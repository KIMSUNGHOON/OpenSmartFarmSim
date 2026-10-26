from decimal import Decimal, localcontext
from fractions import Fraction
import json
from pathlib import Path

import pytest

from app import crop_funded_event_time as model
from app.crop_rational_morphology_artifact_producer import produce_rational_morphology_artifact
from app.crop_leaf_funded_birth_artifact_producer import produce_funded_leaf_artifact
from app.crop_morphology_artifact_io import MorphologyBlobStore, MorphologyArtifactHold
from test_crop_leaf_funded_birth_artifact import calculated_inputs, profiles
from test_crop_leaf_carbon_stock_artifact import ACCESS, encoded
from test_crop_funded_shoot_clock import snapshot

ROOT = Path(__file__).resolve().parents[2]
F = Fraction
TOLERANCE = model._rational(F(1, 10**6), 's')


@pytest.fixture(scope='module')
def sources(tmp_path_factory, profiles):
    base = tmp_path_factory.mktemp('funded-event-time')
    program = json.loads((ROOT/'web/public/morphology-rational-replay/input.json').read_bytes())
    program['output_times'] = ['2026-10-01T07:00:00Z']
    program['segments'][0]['end_utc'] = program['output_times'][-1]
    sr = produce_rational_morphology_artifact(base/'stem', ACCESS, program_raw=encoded(program))
    inputs, _ = calculated_inputs(profiles, steps=(0, 16), dt=8, count=32)
    inputs['time_origin_utc'] = program['output_times'][-1]
    lr = produce_funded_leaf_artifact(base/'leaf', ACCESS, inputs_raw=encoded(inputs), **profiles)
    root_inputs, _ = calculated_inputs(profiles, steps=(32,), dt=8, count=32)
    root_inputs['time_origin_utc'] = program['output_times'][-1]
    root_lr = produce_funded_leaf_artifact(base/'root-leaf', ACCESS, inputs_raw=encoded(root_inputs), **profiles)
    return base, sr, lr, root_lr


def locate(sources, *, label='leaf', **changes):
    base, sr, lr = sources[:3]
    return model.locate_funded_shoot_threshold(base/label, base/'stem', ACCESS,
        **{'leaf_root_sha256': lr, 'stem_root_sha256': sr, 'stem_start_index': 0,
           'bracket_index': 0, 'time_tolerance_seconds_exact': TOLERANCE, **changes})


def frac(q):
    return F(int(q['numerator']), int(q['denominator']))


def test_dense_weights_satisfy_third_order_conditions_exactly():
    for theta in (F(0), F(1, 7), F(1, 2), F(1)):
        b = (theta-3*theta**2/2+2*theta**3/3, theta**2-2*theta**3/3,
             theta**2-2*theta**3/3, -theta**2/2+2*theta**3/3)
        c = (F(0), F(1, 2), F(1, 2), F(1))
        assert sum(b) == theta
        assert sum(x*y for x, y in zip(b, c)) == theta**2/2
        assert sum(x*y*y for x, y in zip(b, c)) == theta**3/3
        assert b[2]/4+b[3]/2 == theta**3/6
        p = model._thermal_polynomial((F(0), F(1, 4), F(1, 4), F(1)), F(1), F(0), F(0), F(0))
        assert model._value(p, theta) == theta**3/(3*86400)


def test_nonlinear_analytic_local_root_error_decreases_with_step_refinement():
    errors = []
    with localcontext() as context:
        context.prec = 100
        for h in (F(1, 2), F(1, 4), F(1, 8), F(1, 16)):
            target = Decimal(37)/100*Decimal(h.numerator)/Decimal(h.denominator)
            threshold = F(target.exp()-1)/86400
            stages = (F(1), 1+h/2, 1+h/2+h*h/4, 1+h+h*h/2+h**3/4)
            p = model._thermal_polynomial(stages, h, F(0), F(0), threshold)
            lo, hi, _ = model._root_interval(p, h, F(1, 10**15))
            midpoint = (lo+hi)*h/2
            errors.append(abs(Decimal(midpoint.numerator)/Decimal(midpoint.denominator)-target))
        assert all(8 < a/b < 24 for a, b in zip(errors, errors[1:]))


@pytest.mark.parametrize('coefficients', [(F(-1), F(1), F(0), F(0)),
                                         (F(-1, 2), F(1), F(0), F(0))])
def test_exact_linear_and_endpoint_roots_remain_enclosed(coefficients):
    lo, hi, _ = model._root_interval(coefficients, F(8), F(1, 10**6))
    assert model._value(coefficients, lo) < 0 <= model._value(coefficients, hi)
    assert (hi-lo)*8 <= F(1, 10**6)


@pytest.mark.parametrize('p', [(F(-1), F(0), F(0), F(0)), (F(-1), F(4), F(-8), F(5)),
                              (F(0), F(1), F(0), F(0)), (F(-2), F(1), F(0), F(0))])
def test_no_root_or_nonmonotone_cubic_holds(p):
    with pytest.raises(MorphologyArtifactHold):
        model._root_interval(p, F(8), F(1, 10**6))


def test_positive_stage_air_above_base_does_not_certify_monotone_dense_age():
    p = model._thermal_polynomial(tuple(map(F, (6, 6, 6, 100))), F(8), F(5), F(0), F(1, 1000))
    assert model._minimum_derivative(p) < 0
    with pytest.raises(MorphologyArtifactHold, match='MONOTONICITY_HOLD'):
        model._root_interval(p, F(8), F(1, 10**6))


def test_precision_and_invalid_tolerance_are_bounded():
    p = (F(-1, 3), F(1), F(0), F(0))
    for tolerance in (F(0), F(-1), F(9), 0.1, F(1, 2**200)):
        with pytest.raises(MorphologyArtifactHold):
            model._root_interval(p, F(8), tolerance)


def test_root_population_before_first_funding_point_replays_same_stages_and_transfers(sources):
    result = locate(sources, label='root-leaf', leaf_root_sha256=sources[3])
    assert result['rhs_evaluations'] == 5
    assert result['endpoint_sample_and_all_transfers'] == 'exact_original_binary64_replay'
    assert result['source_bracket']['right_frame_index'] == result['source_bracket']['left_frame_index']+1
    manifest = model.leaf.read_funded_leaf_manifest(sources[0]/'root-leaf', ACCESS, sources[3])
    assert manifest['samples'][result['source_bracket']['left_frame_index']]['event_sequence'] == 0
    assert frac(result['numerical_root_interval']['width_seconds_exact']) <= frac(TOLERANCE)


def test_cubic_right_endpoint_rounding_cannot_be_repaired_by_inventing_a_crossing():
    p = (F(-1), F(1)-F(1, 2**60), F(0), F(0))
    with pytest.raises(MorphologyArtifactHold, match='ROOT_HOLD'):
        model._root_interval(p, F(8), F(1, 10**6))


def test_original_stored_crossing_all_state_transfers_and_independent_decimal_root(sources, monkeypatch):
    original = model.dynamics._evaluate
    calls = []
    def counted(*a, **k):
        calls.append(1)
        return original(*a, **k)
    monkeypatch.setattr(model.dynamics, '_evaluate', counted)
    before = {name: snapshot(sources[0]/name) for name in ('leaf', 'stem')}
    result = locate(sources)
    assert len(calls) == result['rhs_evaluations'] == 5
    assert result['past_intervals_reintegrated'] == 0 and {name: snapshot(sources[0]/name) for name in ('leaf', 'stem')} == before
    assert result['G0_G4'] == 'not_assessed' and result['integrator_checkpoint'] is None
    assert result['event_state'] == result['new_internodes'] == 'not_created'
    root = result['numerical_root_interval']
    assert frac(root['width_seconds_exact']) <= frac(TOLERANCE)
    assert frac(root['lower_thermal_residual_exact']) < 0 <= frac(root['upper_thermal_residual_exact'])
    bracket = result['source_bracket']
    start = frac(bracket['start_at']['elapsed_seconds_exact'])
    end = frac(bracket['end_at']['elapsed_seconds_exact'])
    lo, hi = (frac(root[k]) for k in ('lower_elapsed_seconds_exact', 'upper_elapsed_seconds_exact'))
    assert start <= lo < hi <= end and len(result['stage_sha256']) == 4
    with localcontext() as context:
        context.prec = 200
        dec = lambda v: Decimal(v.numerator)/Decimal(v.denominator)
        coefficients = [dec(frac(q)) for q in result['polynomial_coefficients']]
        def residual(t):
            theta = (t-dec(start))/dec(end-start)
            return sum(c*theta**i for i, c in enumerate(coefficients))
        assert residual(dec(lo)) < 0 <= residual(dec(hi))
        for t, key in ((lo, 'lower_thermal_residual_exact'), (hi, 'upper_thermal_residual_exact')):
            assert abs(residual(dec(t))-dec(frac(root[key]))) < Decimal('1e-180')
        left, right = dec(start), dec(end)
        for _ in range(200):
            mid = (left+right)/2
            if residual(mid) < 0:
                left = mid
            else:
                right = mid
        assert dec(lo) <= (left+right)/2 <= dec(hi)


@pytest.mark.parametrize('change', [{'bracket_index': True}, {'bracket_index': -1}, {'bracket_index': 1},
    {'time_tolerance_seconds_exact': {'numerator': '1', 'denominator': '0', 'unit': 's'}},
    {'time_tolerance_seconds_exact': {'numerator': '1', 'denominator': '1', 'unit': 'h'}}])
def test_invalid_original_bracket_or_time_input_holds(sources, change):
    with pytest.raises(model.FundedEventTimeHold):
        locate(sources, **change)


@pytest.mark.parametrize('kind', ['code', 'capacity', 'rhs', 'transfer', 'rights', 'late-code', 'late-source', 'late-leaf-blob'])
def test_code_capacity_replay_and_late_rights_source_fences(sources, monkeypatch, kind):
    if kind == 'code':
        monkeypatch.setattr(model, 'CODE_SHA256', '0'*64)
    elif kind == 'capacity':
        monkeypatch.setattr(model, 'MAX_BYTES', 32)
    elif kind == 'rhs':
        original = model.dynamics._advance
        def changed(y, k, dt):
            value = original(y, k, dt)
            return (value[0]+1, *value[1:])
        monkeypatch.setattr(model.dynamics, '_advance', changed)
    elif kind == 'rights':
        original = model.leaf._graph
        def changed(store, manifest):
            result = original(store, manifest)
            manifest['source_rights']['transform'] = False
            return result
        monkeypatch.setattr(model.leaf, '_graph', changed)
    elif kind == 'transfer':
        original = model.dynamics._flux
        def changed(*a, **k):
            value = original(*a, **k)
            return (value[0]+1, *value[1:])
        monkeypatch.setattr(model.dynamics, '_flux', changed)
    elif kind == 'late-code':
        original = model._pins
        calls = []
        def changed():
            value = original(); calls.append(1)
            if len(calls) > 1:
                value[next(iter(value))] = '0'*64
            return value
        monkeypatch.setattr(model, '_pins', changed)
    elif kind == 'late-source':
        original = model.epochs.project_funded_shoot_from_stored_state
        calls = []
        def changed(*a, **k):
            value = original(*a, **k); calls.append(1)
            if len(calls) > 1:
                value['stem_source_state_sha256'] = '0'*64
            return value
        monkeypatch.setattr(model.epochs, 'project_funded_shoot_from_stored_state', changed)
    else:
        stages = model._stages
        done = []
        def completed(*a, **k):
            value = stages(*a, **k); done.append(1)
            return value
        monkeypatch.setattr(model, '_stages', completed)
        original = MorphologyBlobStore.get
        def changed(self, digest, **k):
            value = original(self, digest, **k)
            return value+b' ' if done and digest == sources[2] else value
        monkeypatch.setattr(MorphologyBlobStore, 'get', changed)
    with pytest.raises(model.FundedEventTimeHold):
        locate(sources)


def test_calculation_never_writes_or_uses_db_cli_network_or_birth_point(sources, monkeypatch):
    import os
    import socket
    import subprocess
    import psycopg
    from app import crop_leaf_funded_birth_point as point
    def forbidden(*a, **k):
        raise AssertionError('no external effect or birth adoption')
    for owner, name in ((socket, 'socket'), (subprocess, 'Popen'), (psycopg, 'connect'),
                        (MorphologyBlobStore, 'put'), (point, 'apply_births')):
        monkeypatch.setattr(owner, name, forbidden)
    original = os.open
    def readonly(path, flags, *a, **k):
        if flags & (os.O_WRONLY|os.O_RDWR|os.O_CREAT|os.O_TRUNC|os.O_APPEND):
            return forbidden()
        return original(path, flags, *a, **k)
    monkeypatch.setattr(os, 'open', readonly)
    first = locate(sources)
    second = locate(sources)
    assert first == second
    first['stage_sha256'][0] = '0'*64
    assert second['stage_sha256'][0] != '0'*64
