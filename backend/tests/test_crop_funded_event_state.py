from decimal import Decimal, localcontext
from fractions import Fraction
from math import ulp
from types import SimpleNamespace

import pytest

from app import crop_funded_event_state as model
from app.crop_morphology_artifact_io import MorphologyBlobStore
from test_crop_funded_event_time import sources, ACCESS, TOLERANCE, frac
from test_crop_leaf_funded_birth_artifact import profiles


def calculate(sources, *, label='leaf', **changes):
    base, sr, lr = sources[:3]
    return model.calculate_funded_threshold_state(base/label, base/'stem', ACCESS,
        **{'leaf_root_sha256': lr, 'stem_root_sha256': sr, 'stem_start_index': 0,
           'bracket_index': 0, 'time_tolerance_seconds_exact': TOLERANCE, **changes})


@pytest.mark.parametrize('count', [1, 512])
def test_exact_dense_combinations_across_supported_vector_dimensions(count):
    initial = tuple(float(i+1) for i in range(107+3*count))
    rates = tuple(tuple(float((i+j)%7)/8 for i in range(len(initial))) for j in range(4))
    theta = Fraction(13, 29)
    actual = model._combine(initial, rates, model._weights(theta), Fraction(1, 3))
    with localcontext() as context:
        context.prec = 200
        dec = lambda f: Decimal(f.numerator)/Decimal(f.denominator)
        t = dec(theta)
        weights = (t-3*t*t/2+2*t**3/3, t*t-2*t**3/3, t*t-2*t**3/3, -t*t/2+2*t**3/3)
        for i, value in enumerate(actual):
            reference = Decimal.from_float(initial[i])+sum(w*Decimal.from_float(rates[j][i]) for j, w in enumerate(weights))/3
            assert abs(Decimal.from_float(value)-reference) <= Decimal.from_float(ulp(value))/2


@pytest.mark.parametrize('value,prior', [(Fraction(1, 10**400), None), (Fraction(10**400), None),
    (Fraction.from_float(1e300)+1, 1e300)])
def test_underflow_overflow_and_lost_state_increment_reject(value, prior):
    with pytest.raises((model.MorphologyArtifactHold, OverflowError)):
        model._rounded(value, prior)


def test_new_exact_time_rk4_has_fourth_order_convergence_for_nonlinear_analytic_ODE(monkeypatch):
    monkeypatch.setattr(model.dynamics, '_evaluate', lambda p, y, profiles: (tuple(v*v for v in y), {}))
    monkeypatch.setattr(model.dynamics, '_flux', lambda p, y, rhs: tuple(v*v for v in y))
    monkeypatch.setattr(model.dynamics, '_flux_units', lambda p: {'integral': '1'})
    monkeypatch.setattr(model, '_ledgers', lambda *a, **k: {})
    profiles = {'exchange_profile': SimpleNamespace(values={'latent_heat': 1.})}
    with localcontext() as context:
        context.prec = 100
        errors = []
        for count in (1, 2, 4, 8):
            state, transfers, _ = model._refine({}, (1.,), profiles, Fraction(1, 4), count)
            errors.append(abs(Decimal.from_float(state[0])-Decimal(4)/3))
            assert abs(Decimal.from_float(state[0])-1-Decimal.from_float(transfers[0])) < Decimal('1e-14')
        assert all(10 < a/b < 20 for a, b in zip(errors, errors[1:]))


@pytest.mark.parametrize('label', ['leaf', 'root-leaf'])
def test_original_root_or_funded_state_time_prefix_and_independent_dense_values(sources, monkeypatch, label):
    calls = []
    original = model.dynamics._evaluate
    def counted(*a, **k):
        calls.append(1)
        return original(*a, **k)
    monkeypatch.setattr(model.dynamics, '_evaluate', counted)
    collected = []
    collect = model._collect
    def captured(*a, **k):
        value = collect(*a, **k); collected.extend(value)
        return value
    monkeypatch.setattr(model, '_collect', captured)
    leaf_root = sources[2] if label == 'leaf' else sources[3]
    result = calculate(sources, label=label, leaf_root_sha256=leaf_root)
    assert result['selection'] == {'leaf_root_sha256': leaf_root, 'stem_root_sha256': sources[1],
        'stem_start_index': 0, 'bracket_index': 0, 'time_tolerance_seconds_exact': TOLERANCE}
    assert len(calls) == result['rhs_evaluations'] == 41
    certificate = result['source_root_certificate']
    assert result['at']['elapsed_seconds_exact'] == certificate['numerical_root_interval']['upper_elapsed_seconds_exact']
    assert result['integrator_checkpoint'] is None and result['new_internodes'] == 'not_created'
    assert result['G0_G4'] == 'not_assessed'
    manifest = model.event.leaf.read_funded_leaf_manifest(sources[0]/label, ACCESS, leaf_root)
    left = certificate['source_bracket']['left_frame_index']
    with MorphologyBlobStore(sources[0]/label, ACCESS) as store:
        cp = model._parse(store.get(manifest['samples'][left]['checkpoint_sha256'], maximum=model.event.leaf.CHECKPOINT_MAX), model.event.leaf.CHECKPOINT_MAX)
    assert result['source_prefix'] == {k: cp[k] for k in result['source_prefix']}
    assert result['source_event_sequence'] == (2 if label == 'leaf' else 0)
    assert len(result['dense_candidate']['state']) == 107+3*len(result['state_layout']['leaf_ids'])
    assert [row['substeps'] for row in result['refinements']] == [1, 2, 4]
    duration = frac(result['partial_interval_seconds_exact'])
    dt = frac(certificate['source_bracket']['end_at']['elapsed_seconds_exact'])-frac(certificate['source_bracket']['start_at']['elapsed_seconds_exact'])
    with localcontext() as context:
        context.prec = 200
        dec = lambda f: Decimal(f.numerator)/Decimal(f.denominator)
        theta = dec(duration/dt)
        weights = (theta-3*theta**2/2+2*theta**3/3, theta**2-2*theta**3/3,
                   theta**2-2*theta**3/3, -theta**2/2+2*theta**3/3)
        for i, actual in enumerate(result['dense_candidate']['state']):
            expected = Decimal.from_float(collected[0][0][i])+dec(dt)*sum(weights[j]*Decimal.from_float(collected[j][1][i]) for j in range(4))
            assert abs(Decimal.from_float(actual)-expected) <= Decimal.from_float(ulp(actual))/2
        transfers = list(result['dense_candidate']['partial_interval_transfers'].values())
        for i, actual in enumerate(transfers):
            expected = dec(dt)*sum(weights[j]*Decimal.from_float(collected[j][2][i]) for j in range(4))
            assert abs(Decimal.from_float(actual['value'])-expected) <= Decimal.from_float(ulp(actual['value']))/2
    for packet in [result['dense_candidate'], *result['refinements']]:
        assert len(packet['local_ledgers']) == 7+2*len(result['state_layout']['leaf_ids'])
        for ledger in packet['local_ledgers'].values():
            assert abs(frac(ledger['residual_exact'])) <= frac(ledger['budget_exact'])
    # Climate differences are well above roundoff in this declared synthetic case.
    one, two, four = [r['state'] for r in result['refinements']]
    for index in (104, 105, 106):
        a = abs(Fraction.from_float(one[index])-Fraction.from_float(two[index]))
        b = abs(Fraction.from_float(two[index])-Fraction.from_float(four[index]))
        assert a > b > 0 and 8 < a/b < 24


@pytest.mark.parametrize('kind', ['code', 'capacity', 'stage', 'dense-domain', 'ledger', 'refinement-domain', 'late-code', 'late-rights'])
def test_atomic_numeric_domain_ledger_source_and_capacity_failure(sources, monkeypatch, kind):
    if kind == 'code':
        monkeypatch.setattr(model, 'CODE_SHA256', '0'*64)
    elif kind == 'capacity':
        monkeypatch.setattr(model, 'MAX_BYTES', 32)
    elif kind == 'stage':
        original = model._collect
        def changed(*a, **k):
            rows = original(*a, **k); y, rates, flux, rhs = rows[0]
            rows[0] = (y, (rates[0]+1, *rates[1:]), flux, rhs)
            return rows
        monkeypatch.setattr(model, '_collect', changed)
    elif kind in ('dense-domain', 'refinement-domain'):
        original = model.dynamics._evaluate
        calls = []
        def changed(*a, **k):
            calls.append(1)
            if len(calls) == (10 if kind == 'dense-domain' else 12):
                raise ValueError('DOMAIN_HOLD: injected unconfirmed stage')
            return original(*a, **k)
        monkeypatch.setattr(model.dynamics, '_evaluate', changed)
    elif kind == 'ledger':
        original = model._combine
        calls = []
        def changed(*a, **k):
            value = original(*a, **k); calls.append(1)
            return (value[0]+1, *value[1:]) if len(calls) == 2 else value
        monkeypatch.setattr(model, '_combine', changed)
    elif kind == 'late-code':
        original = model._pins
        calls = []
        def changed():
            value = original(); calls.append(1)
            if len(calls) > 1:
                value[next(iter(value))] = '0'*64
            return value
        monkeypatch.setattr(model, '_pins', changed)
    else:
        refine = model._refine
        done = []
        def counted(*a, **k):
            value = refine(*a, **k); done.append(1)
            return value
        monkeypatch.setattr(model, '_refine', counted)
        graph = model.event.leaf._graph
        def changed(store, manifest):
            value = graph(store, manifest)
            if done:
                manifest['source_rights']['display'] = False
            return value
        monkeypatch.setattr(model.event.leaf, '_graph', changed)
    with pytest.raises(model.FundedEventStateHold):
        calculate(sources)


def test_readonly_local_calculation_never_advances_history_adopts_birth_or_writes(sources, monkeypatch):
    import os
    import socket
    import subprocess
    import psycopg
    from app import crop_leaf_funded_birth_point as point
    def forbidden(*a, **k):
        raise AssertionError('no external side effect or checkpoint adoption')
    for owner, name in ((socket, 'socket'), (subprocess, 'Popen'), (psycopg, 'connect'),
                        (MorphologyBlobStore, 'put'), (point, 'apply_births'), (point.resume, 'advance_chunk')):
        monkeypatch.setattr(owner, name, forbidden)
    original = os.open
    def readonly(path, flags, *a, **k):
        if flags & (os.O_WRONLY|os.O_RDWR|os.O_CREAT|os.O_TRUNC|os.O_APPEND):
            return forbidden()
        return original(path, flags, *a, **k)
    monkeypatch.setattr(os, 'open', readonly)
    result = calculate(sources)
    assert result['global_prefix_composition'].startswith('not_adopted')


def test_caller_mutation_cannot_change_captured_selection_or_reported_tolerance(sources, monkeypatch):
    tolerance = dict(TOLERANCE)
    original = model.event.locate_funded_shoot_threshold
    def mutate_caller(*a, **k):
        assert k['time_tolerance_seconds_exact'] is not tolerance
        tolerance['denominator'] = '7'
        return original(*a, **k)
    monkeypatch.setattr(model.event, 'locate_funded_shoot_threshold', mutate_caller)
    result = calculate(sources, time_tolerance_seconds_exact=tolerance)
    assert tolerance['denominator'] == '7'
    assert result['selection']['time_tolerance_seconds_exact'] == TOLERANCE
    assert result['source_root_certificate']['requested_time_tolerance_seconds_exact'] == TOLERANCE
