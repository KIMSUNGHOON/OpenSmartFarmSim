from copy import deepcopy
from fractions import Fraction
from hashlib import sha256
import json

import pytest

from app import crop_organ_current_shoot_clock as model
from test_crop_organ_funded_continuation import roots, prepared, next_inputs
from test_crop_stem_root_initial_binding import stored, profiles

stock = model.stock


def derive(ctx, cp):
    raw = stock.checkpoint_bytes(ctx, cp)
    return model.derive_current_shoot_clock(ctx, raw, expected_sha256=sha256(raw).hexdigest())


def F(q):
    return Fraction(int(q['numerator']), int(q['denominator']))


@pytest.fixture(scope='module')
def contexts(roots):
    return {(case, kind): prepared(roots[case], kind, 1) for case in range(6) for kind in ('leaf', 'internode')}


@pytest.mark.parametrize('case', range(6))
@pytest.mark.parametrize('kind', ['leaf', 'internode'])
@pytest.mark.parametrize('extra', [0, 1, 3])
def test_actual_current_cp_initial_source_ages_ids_signed_integral_and_immutable_bytes(contexts, case, kind, extra):
    ctx, kw = contexts[case, kind]; cp = stock.start(ctx)
    if extra: cp = stock.advance_chunk(ctx, cp, extra)['checkpoint']
    raw = stock.checkpoint_bytes(ctx, cp); before = stock.context_bytes(ctx)
    result = derive(ctx, cp); source = stock._source(ctx); state = source['stem_selection']['source_state']; t = state['timeline_state']
    elapsed = F(cp.value['at_elapsed_seconds_exact']); integral = cp.value['integrated_transfers']['indoor_air_temperature_time']['value']
    base = Fraction.from_float(float(t['base_temperature']['value'])); change = (Fraction.from_float(integral)-base*elapsed)/86400
    assert F(result['shoot']['age_exact']) == F(t['age_exact'])+change
    assert result['development_origin_utc'] == t['started_at'] and result['simulation_origin_utc'] == t['at']
    assert F(result['development_elapsed_seconds_exact']) == F(result['simulation_start_development_elapsed_seconds_exact'])+elapsed
    assert result['shoot']['shoot_id'] == t['shoot_id'] and result['shoot']['age_basis'] == 'since_shoot_development_origin'
    for actual, original in zip(result['initial_internodes'], state['internodes'], strict=True):
        clock = original['length_state']['clock_state']
        assert actual['internode_id'] == clock['internode_id'] and actual['source_clock'] == clock
        assert F(actual['age_exact']) == F(clock['age_exact'])+change
    declared = result['declared_internodes']; assert len(declared) == (kind == 'internode')
    for actual in declared:
        record = ctx.point_history[0]; age = (Fraction.from_float(integral)-Fraction.from_float(record['air_temperature_integral'])-base*(elapsed-F(record['inputs']['at_elapsed_seconds_exact'])))/86400
        assert F(actual['age_exact']) == age and actual['age_basis'] == 'since_declared_material_point'
        assert actual['event_id'] == record['inputs']['events'][0]['event_id']
        assert actual['physiological_emergence'] == 'not_established'
    ids = [r['internode_id'] for r in result['initial_internodes']+declared]
    assert ids == [r['compartment_id'] for r in ctx.program['stem_root_compartments'] if r['kind'] == 'internode']
    assert result['unclocked_root_system_ids'] == ['explicit-root']
    assert result['checkpoint_sha256'] == cp.sha256 and result['step_index'] == cp.value['step_index']
    assert result['redistribution_authorized'] is False and result['G0_G4'] == 'not_assessed'
    assert result['new_growth_steps'] == 0 and result['checkpoint_validation_stage_evaluations'] == 1
    assert result['calculation_sha256'] == sha256(stock._canonical({k: v for k, v in result.items() if k != 'calculation_sha256'})).hexdigest()
    assert stock.context_bytes(ctx) == before and stock.checkpoint_bytes(ctx, cp) == raw and derive(ctx, cp) == result


@pytest.mark.parametrize('first,second', [('leaf','internode'), ('internode','leaf'), ('internode','internode')])
@pytest.mark.parametrize('gap', [0, 1])
def test_two_points_preserve_order_and_material_clock_bases(contexts, first, second, gap):
    ctx, kw = contexts[0, first]; cp = stock.start(ctx)
    if gap: cp = stock.advance_chunk(ctx, cp, gap)['checkpoint']
    v = next_inputs(ctx, cp, second, kw)
    ctx2 = stock.adopt_births(context=ctx, raw_checkpoint=stock.checkpoint_bytes(ctx, cp), expected_sha256=cp.sha256, kind=second, inputs=v)
    after = stock.start(ctx2); a = derive(ctx, cp); b = derive(ctx2, after)
    assert a['shoot'] == b['shoot'] and a['initial_internodes'] == b['initial_internodes']
    assert b['declared_internodes'][:len(a['declared_internodes'])] == a['declared_internodes']
    if second == 'internode': assert F(b['declared_internodes'][-1]['age_exact']) == 0
    final = stock.advance_chunk(ctx2, after, 1)['checkpoint']; result = derive(ctx2, final)
    for r in result['declared_internodes']: assert F(r['age_exact']) > 0


def test_only_current_validation_rhs_and_no_history_point_or_area_replay(contexts, monkeypatch):
    ctx, kw = contexts[2, 'internode']; cp = stock.advance_chunk(ctx, stock.start(ctx), 2)['checkpoint']; raw = stock.checkpoint_bytes(ctx, cp)
    evaluate = stock.short._evaluate; calls = []
    def counted(*a, **k): calls.append(1); return evaluate(*a, **k)
    monkeypatch.setattr(stock.short, '_evaluate', counted)
    def forbidden(*a, **k): raise AssertionError('no old replay/initialization allowed')
    for owner, name in [(stock, 'advance_chunk'), (stock, 'adopt_births'), (stock, 'prepare_context'), (stock.leaf, '_jump'), (stock.stem, '_jump'),
                        (stock.short.old.leaf_area, 'initialize_leaf_area'), (stock.short.old.leaf_area, 'normalize_leaf_area_state')]:
        monkeypatch.setattr(owner, name, forbidden)
    model.derive_current_shoot_clock(ctx, raw, expected_sha256=cp.sha256)
    assert len(calls) == 1


@pytest.mark.parametrize('initial,integral,seconds,base,expected', [
    (10, -86400., 1, 5., Fraction(10)-1-Fraction(5,86400)),
    (1, 0., 8640, 5., Fraction(1,2)), (0, 0., 0, 5., Fraction(0)),
    (0, 5., 1, 5., Fraction(0)), (0, 6., 1, 5., Fraction(1,86400))])
def test_signed_no_clip_exact_arithmetic(initial, integral, seconds, base, expected):
    assert F(model._age(Fraction(initial), integral, Fraction(seconds), base)) == expected


@pytest.mark.parametrize('initial,integral,seconds,base', [(0, 4., 1, 5.), (0, -1., 0, 5.), (1, 0., 86401, 5.)])
def test_negative_age_is_hold_instead_of_clamp(initial, integral, seconds, base):
    with pytest.raises(model.CurrentShootClockHold, match='AGE_HOLD'): model._age(Fraction(initial), integral, Fraction(seconds), base)


@pytest.mark.parametrize('edit', [lambda q: q.update(unit='K_s'), lambda q: q.update(value=float('nan')), lambda q: q.update(value=1), lambda q: q.update(extra=True)])
def test_closed_finite_air_integral_units(edit):
    q = {'value': 0., 'unit': 'degC_s'}; edit(q)
    with pytest.raises(model.CurrentShootClockHold, match='UNIT_HOLD'): model._integral(q)


@pytest.mark.parametrize('change', ['hash', 'bytes', 'typed', 'oversize', 'context'])
def test_untrusted_checkpoint_identity_bytes_and_cap_are_held(contexts, change):
    ctx, _ = contexts[0, 'leaf']; cp = stock.start(ctx); raw = stock.checkpoint_bytes(ctx, cp); digest = cp.sha256
    if change == 'hash': digest = '0'*64
    elif change == 'bytes': raw += b'\n'
    elif change == 'typed': raw = cp
    elif change == 'oversize': raw = b'x'*(stock.MAX_CHECKPOINT_BYTES+1); digest = sha256(raw).hexdigest()
    else: ctx = contexts[1, 'leaf'][0]
    with pytest.raises(model.CurrentShootClockHold): model.derive_current_shoot_clock(ctx, raw, expected_sha256=digest)


@pytest.mark.parametrize('field', ['unit', 'time', 'order', 'identity', 'integral'])
def test_modified_cp_cannot_be_accepted_with_an_old_hash(contexts, field):
    ctx, _ = contexts[0, 'internode']; cp = stock.start(ctx); q = cp.value
    if field == 'unit': q['integrated_transfers']['indoor_air_temperature_time']['unit'] = 'K_s'
    elif field == 'time': q['at_elapsed_seconds_exact']['numerator'] = '2'
    elif field == 'order': q['event_sequence'] += 1
    elif field == 'identity': q['context_sha256'] = '0'*64
    else: q['integrated_transfers']['indoor_air_temperature_time']['value'] += 1.
    with pytest.raises(model.CurrentShootClockHold): model.derive_current_shoot_clock(ctx, stock._canonical(q), expected_sha256=cp.sha256)


def test_result_cap_does_not_issue_partial_clock(contexts, monkeypatch):
    ctx, _ = contexts[0, 'internode']; cp = stock.start(ctx); monkeypatch.setattr(model, 'MAX_BYTES', 100)
    with pytest.raises(model.CurrentShootClockHold, match='CAPACITY_HOLD'): derive(ctx, cp)


def test_late_current_source_change_withholds_result(contexts, monkeypatch):
    ctx, _ = contexts[0, 'leaf']; cp = stock.start(ctx); source = stock._source; calls = []
    def changed(*a, **k):
        value = source(*a, **k); calls.append(1)
        if len(calls) >= 4: value['source_rights']['crop']['display'] = False
        return value
    monkeypatch.setattr(stock, '_source', changed)
    with pytest.raises(model.CurrentShootClockHold, match='SOURCE_HOLD'): derive(ctx, cp)


def test_extra_real_below_base_checkpoint_is_signed_negative_hold(stored, profiles, tmp_path):
    from pathlib import Path
    from test_crop_leaf_carbon_stock_artifact import encoded, ACCESS
    from app.crop_rational_morphology_artifact_producer import produce_rational_morphology_artifact
    root_path = Path(__file__).resolve().parents[2]
    source = json.loads((root_path/'web/public/morphology-rational-replay/input.json').read_bytes())
    source['initial_state']['timeline_state']['base_temperature']['value'] = 20.
    for node in source['initial_state']['internodes']:
        length = node['length_state']
        length['clock_state']['base_temperature']['value'] = 20.
        length['anchor']['clock_state']['base_temperature']['value'] = 20.
    stem_directory = tmp_path/'higher-stem-base'
    stem_root = produce_rational_morphology_artifact(stem_directory, ACCESS, program_raw=encoded(source))
    root = stock.parent.prepare_context(program=stored[0][0].program, step_seconds=.125, step_count=2, **profiles)
    row = (root, stored[0][1], stem_directory, stored[0][3], stem_root, -1)
    ctx, _ = prepared(row, 'internode', 0); cp = stock.advance_chunk(ctx, stock.start(ctx), 1)['checkpoint']
    assert cp is not None and cp.value['integrated_transfers']['indoor_air_temperature_time']['value'] < 20.*.125
    raw = stock.checkpoint_bytes(ctx, cp)
    with pytest.raises(model.CurrentShootClockHold, match='AGE_HOLD'): derive(ctx, cp)
    assert stock.checkpoint_bytes(ctx, cp) == raw


@pytest.mark.parametrize('name', ['model', 'prior'])
def test_extra_code_identity_change_is_held(contexts, monkeypatch, name):
    ctx, _ = contexts[0, 'internode']; cp = stock.start(ctx)
    monkeypatch.setattr(model if name == 'model' else model.prior, 'CODE_SHA256', '0'*64)
    with pytest.raises(model.CurrentShootClockHold, match='CODE_HOLD'): derive(ctx, cp)


def test_extra_profile_changed_during_current_validation_withholds_clock(contexts, monkeypatch):
    from types import MappingProxyType
    ctx, _ = contexts[0, 'internode']; cp = stock.start(ctx); raw = stock.checkpoint_bytes(ctx, cp)
    evaluate = stock.short._evaluate; profile = ctx._root._profiles[0]; original = profile.values
    def changed(*a, **k):
        value = evaluate(*a, **k); values = dict(original); key = next(iter(values)); values[key] += .001
        object.__setattr__(profile, 'values', MappingProxyType(values)); return value
    monkeypatch.setattr(stock.short, '_evaluate', changed)
    try:
        with pytest.raises(model.CurrentShootClockHold, match='PROFILE_HOLD'):
            model.derive_current_shoot_clock(ctx, raw, expected_sha256=cp.sha256)
    finally: object.__setattr__(profile, 'values', original)


def test_extra_actual_store_read_changed_at_final_fence_is_held(contexts, monkeypatch):
    ctx, _ = contexts[0, 'internode']; cp = stock.start(ctx); raw = stock.checkpoint_bytes(ctx, cp)
    store = stock.leaf.binding.MorphologyBlobStore; original = store.get; calls = []
    digest = stock._source(ctx)['stem_selection']['program_sha256']
    def changed(self, key, **k):
        value = original(self, key, **k)
        if key == digest:
            calls.append(1)
            if len(calls) >= 9: return value+b' '
        return value
    monkeypatch.setattr(store, 'get', changed)
    with pytest.raises(model.CurrentShootClockHold): model.derive_current_shoot_clock(ctx, raw, expected_sha256=cp.sha256)
    assert len(calls) >= 9


@pytest.mark.parametrize('field', ['display', 'use'])
def test_extra_current_original_rights_cannot_be_replaced_by_claim(contexts, monkeypatch, field):
    ctx, _ = contexts[0, 'leaf']; cp = stock.start(ctx); raw = stock.checkpoint_bytes(ctx, cp)
    original = stock.leaf.binding.bind_initial_stem_carbon
    def changed(*a, **k):
        value = original(*a, **k); value['source_rights']['stem'][field] = False; return value
    monkeypatch.setattr(stock.leaf.binding, 'bind_initial_stem_carbon', changed)
    with pytest.raises(model.CurrentShootClockHold, match='SOURCE_HOLD'): model.derive_current_shoot_clock(ctx, raw, expected_sha256=cp.sha256)


@pytest.mark.parametrize('field', ['air', 'time', 'sequence'])
def test_extra_rehashed_cp_still_needs_derived_state_and_time_consistency(contexts, field):
    ctx, _ = contexts[0, 'internode']; cp = stock.start(ctx); payload = cp.value
    if field == 'air': payload['integrated_transfers']['indoor_air_temperature_time']['value'] += 1.
    elif field == 'time': payload['at_elapsed_seconds_exact']['numerator'] = '3'
    else: payload['event_sequence'] += 1
    raw = stock._canonical(payload)
    with pytest.raises(model.CurrentShootClockHold): model.derive_current_shoot_clock(ctx, raw, expected_sha256=sha256(raw).hexdigest())


def test_extra_unexpected_runtime_error_is_not_reclassified_as_hold(contexts, monkeypatch):
    ctx, _ = contexts[0, 'leaf']; cp = stock.start(ctx); raw = stock.checkpoint_bytes(ctx, cp)
    def unexpected(*a, **k): raise RuntimeError('operator interruption')
    monkeypatch.setattr(stock.short, '_evaluate', unexpected)
    with pytest.raises(RuntimeError, match='operator interruption'): model.derive_current_shoot_clock(ctx, raw, expected_sha256=cp.sha256)


def test_extra_returned_mutable_copy_cannot_change_original_clock_or_cp(contexts):
    ctx, _ = contexts[0, 'internode']; cp = stock.start(ctx); original = derive(ctx, cp); changed = deepcopy(original)
    changed['declared_internodes'][0]['age_exact']['numerator'] = '99'
    changed['shoot']['age_exact']['numerator'] = '99'
    assert derive(ctx, cp) == original
