from copy import deepcopy
from hashlib import sha256
import json

import pytest

from app import crop_leaf_funded_birth_continuation as model
from test_crop_leaf_funded_birth_point import setup_point
from test_crop_growing_geometry_climate import profiles


def prepared(profiles, case=0, cut=2, count=1):
    kw = setup_point(profiles, case, cut, count)
    if count > 2:
        for event in kw['inputs']['events']:
            event['leaf']['initial_carbon']['value'] = .001
            event['leaf']['carbon_removal']['value'] = 0.
    context = model.prepare_context(parent_context=kw['context'], raw_parent_checkpoint=kw['raw_checkpoint'],
                                    expected_parent_sha256=kw['expected_sha256'], inputs=kw['inputs'])
    return context, kw


@pytest.mark.parametrize('case', range(6))
@pytest.mark.parametrize('cut', [0, 2, 4])
def test_adopted_context_binds_original_program_clock_stocks_and_ledgers(profiles, case, cut):
    context, kw = prepared(profiles, case, cut)
    p, seed, m = model._context(context)
    point = model.point.apply_births(**kw)
    assert p == point['after_program'] and seed['last_confirmed'] == point['after_sample']
    assert seed['before_checkpoint'] == point['before_checkpoint']
    assert m['numerical']['event_global_step_index'] == cut
    assert len(seed['birth_bases']) == 4 and seed['birth_bases'][-1]['step_index'] == cut
    assert seed['anchors'][:3] == json.loads(kw['context']._seed)['evaluation']['curve_residuals']
    assert seed['anchors'][-1] == {'value': 0., 'unit': 'm2'}
    for name, row in point['before_checkpoint']['integrated_transfers'].items():
        assert seed['base_transfers'][name] == row
    assert [seed['base_transfers']['leaf_3_'+k]['value'] for k in ('inflow', 'maintenance', 'removal')] == [0.]*3
    raw = model.context_bytes(context)
    restored = model.restore_context(root_context=kw['context'], raw_bytes=raw, expected_sha256=sha256(raw).hexdigest())
    assert model.context_bytes(restored) == raw and restored.root_sha256 == context.root_sha256


def test_frozen_context_restore_calls_no_ode_or_point(profiles, monkeypatch):
    context, kw = prepared(profiles)
    raw = model.context_bytes(context)
    def forbidden(*a, **k): raise AssertionError('no replay during frozen context restore')
    monkeypatch.setattr(model.short, '_evaluate', forbidden)
    monkeypatch.setattr(model.short, '_prepare', forbidden)
    monkeypatch.setattr(model.point, 'apply_births', forbidden)
    restored = model.restore_context(root_context=kw['context'], raw_bytes=raw, expected_sha256=sha256(raw).hexdigest())
    assert model.context_bytes(restored) == raw


def test_program_and_history_properties_are_isolated_copies(profiles):
    context, _ = prepared(profiles)
    original = model.context_bytes(context)
    p = context.program; p['leaves'][0]['initial_carbon']['value'] = 999.
    h = context.point_history; h[0]['inputs']['events'][0]['event_id'] = 'different'
    assert model.context_bytes(context) == original


@pytest.mark.parametrize('case', range(6))
def test_point_snapshot_closes_segment_and_root_ledgers(profiles, case):
    context, _ = prepared(profiles, case)
    p, seed, _ = model._context(context); sample = seed['last_confirmed']; y = sample['state']
    zero = (0.,)*len(model.short._flux_units(p))
    residuals, budgets = model._segment_balances(context, p, seed, y, zero, sample, 0)
    total = model._lifetime(p, seed, zero)
    gr, gb = model._global_balances(context, p, seed, y, total, sample, budgets, sample['step_index'])
    assert all(abs(row['value']) <= budgets[name]['value'] for name, row in residuals.items())
    assert all(abs(row['value']) <= gb[name]['value'] for name, row in gr.items())


@pytest.mark.parametrize('case', range(6))
def test_real_next_steps_preserve_global_time_and_all_ledgers(profiles, case):
    context, _ = prepared(profiles, case)
    cp = model.start(context)
    before = cp.value
    result = model.advance_chunk(context, cp, 2)
    assert result['status'] == 'completed', result.get('hold')
    assert result['step_index'] == 4 and result['confirmed_new_steps'] == 2
    assert result['checkpoint_validation_stage_evaluations'] == 1 and result['attempted_new_stage_evaluations'] == 8
    assert [s['elapsed_seconds'] for s in result['samples']] == [.375, .5]
    assert result['samples'][-1]['state'][110] > 0.
    assert result['samples'][-1]['state'][114] > before['last_confirmed']['state'][114]
    assert result['point_totals'] == before['point_totals']
    assert all(abs(row['value']) <= result['global_balance_budgets'][name]['value']
               for name, row in result['global_balance_residuals'].items())
    raw = model.checkpoint_bytes(context, result['checkpoint'])
    restored = model.restore_checkpoint(context, raw, expected_sha256=sha256(raw).hexdigest())
    assert model.checkpoint_bytes(context, restored) == raw
    with pytest.raises(model.FundedContinuationHold, match='COMPLETED_HOLD'):
        model.advance_chunk(context, restored, 1)


def next_inputs(context, cp):
    v = deepcopy(context.point_history[0]['inputs'])
    v.update(context_sha256=context.root_sha256, checkpoint_sha256=cp.sha256,
             at_elapsed_seconds_exact=cp.value['at_elapsed_seconds_exact'])
    v['events'][0]['event_id'] = 'second-event'
    v['events'][0]['leaf']['leaf_id'] = 'second-new-leaf'
    return v


def test_second_funded_birth_keeps_history_old_state_and_lifetime_totals(profiles):
    context, _ = prepared(profiles, cut=0)
    middle = model.advance_chunk(context, model.start(context), 2)['checkpoint']
    v = next_inputs(context, middle)
    second = model.adopt_births(context=context, raw_checkpoint=model.checkpoint_bytes(context, middle),
                                expected_sha256=middle.sha256, inputs=v)
    cp = model.start(second)
    old, new = middle.value, cp.value
    assert len(second.point_history) == 2 and len(second.program['leaves']) == 5
    assert old['step_index'] == new['step_index'] == 2
    assert old['at_elapsed_seconds_exact'] == new['at_elapsed_seconds_exact']
    assert new['output_cursor'] == old['output_cursor']+1 and new['phase'] == 'after_birth'
    for name, row in old['integrated_transfers'].items(): assert new['integrated_transfers'][name] == row
    assert new['point_totals']['growth_respiration']['value'] == 2*old['point_totals']['growth_respiration']['value']
    result = model.advance_chunk(second, cp, 2)
    assert result['status'] == 'completed', result.get('hold')
    assert result['samples'][-1]['state'][110] > result['samples'][-1]['state'][111] > 0.
    v = next_inputs(second, result['checkpoint'])
    with pytest.raises(model.FundedContinuationHold, match='EVENT_HOLD'):
        model.adopt_births(context=second, raw_checkpoint=model.checkpoint_bytes(second, result['checkpoint']),
                           expected_sha256=result['checkpoint'].sha256, inputs=v)


@pytest.fixture(scope='module')
def base_context(profiles):
    return prepared(profiles)[0]


def raw(value): return json.dumps(value, sort_keys=True, separators=(',', ':'), ensure_ascii=False, allow_nan=False).encode()


@pytest.mark.parametrize('change', [
    lambda v: v.update(extra=1), lambda v: v.pop('phase'), lambda v: v.update(step_index=True),
    lambda v: v.update(step_index=3), lambda v: v.update(segment_step_index=-1),
    lambda v: v.update(output_cursor=1), lambda v: v.update(output_prefix_sha256='x'*64),
    lambda v: v.update(event_sequence=False), lambda v: v.update(context_sha256='0'*64),
    lambda v: v['at_elapsed_seconds_exact'].update(unit='min'),
    lambda v: v['last_confirmed']['state'].__setitem__(0, True),
    lambda v: v['last_confirmed']['state'].__setitem__(0, v['last_confirmed']['state'][0]+1.),
    lambda v: v['last_confirmed']['state'].pop(),
    lambda v: v['last_confirmed']['derived']['leaf_carbohydrate'].update(value=1.),
    lambda v: v['integrated_transfers']['photosynthesis'].update(value=999.),
    lambda v: v['segment_integrated_transfers']['photosynthesis'].update(unit='mg_CH2O'),
    lambda v: v['segment_integrated_transfers']['photosynthesis'].update(value=True),
    lambda v: v['point_totals']['growth_respiration'].update(value=0.),
    lambda v: v['global_balance_budgets']['carbohydrate'].update(value=999.)
])
def test_changed_checkpoint_metadata_state_units_and_ledgers_are_rejected(base_context, change):
    value = model.start(base_context).value
    change(value); encoded = raw(value)
    with pytest.raises(model.FundedContinuationHold):
        model.restore_checkpoint(base_context, encoded, expected_sha256=sha256(encoded).hexdigest())


@pytest.mark.parametrize('where', ['manifest', 'seed', 'history'])
def test_even_trusted_snapshot_requires_closed_captured_fields(base_context, where):
    value = json.loads(model.context_bytes(base_context))
    (value[where][0] if where == 'history' else value[where])['extra'] = 1
    for name in ('program', 'seed', 'history'): value['manifest'][name+'_sha256'] = sha256(raw(value[name])).hexdigest()
    encoded = raw(value)
    with pytest.raises(model.FundedContinuationHold):
        model.restore_context(root_context=base_context._root, raw_bytes=encoded, expected_sha256=sha256(encoded).hexdigest())


@pytest.mark.parametrize('budget', [0, -1, True, 129, 1.5])
def test_step_budget_is_bounded_integer(base_context, budget):
    with pytest.raises(model.FundedContinuationHold, match='BUDGET_HOLD'):
        model.advance_chunk(base_context, model.start(base_context), budget)


def test_trial_failure_keeps_last_confirmed_prefix_and_no_checkpoint(base_context, monkeypatch):
    cp = model.start(base_context); evaluate = model.short._evaluate; calls = []
    def fail_after_one_step(p, y, profiles):
        calls.append(1)
        if len(calls) == 6: raise model.short.StockDynamicsHold('injected next k2')
        return evaluate(p, y, profiles)
    monkeypatch.setattr(model.short, '_evaluate', fail_after_one_step)
    result = model.advance_chunk(base_context, cp, 2)
    assert result['status'] == 'hold' and result['checkpoint'] is None
    assert result['step_index'] == 3 and result['confirmed_new_steps'] == 1 and len(result['samples']) == 1
    assert result['hold']['step_index'] == 4 and result['hold']['stage'] == 'k2'
    assert result['last_confirmed'] == result['samples'][-1] and result['output_cursor'] == cp.value['output_cursor']+1


@pytest.fixture(scope='module')
def full_cases(profiles):
    result = []
    for case in range(6):
        context, _ = prepared(profiles, case, cut=0)
        out = model.advance_chunk(context, model.start(context), 4)
        assert out['status'] == 'completed'
        result.append((context, out))
    return result


def compositions(n):
    if n == 0: return [()]
    return [(a, *rest) for a in range(1, n+1) for rest in compositions(n-a)]


@pytest.mark.parametrize('case', range(6))
@pytest.mark.parametrize('grouping', compositions(4))
def test_all_four_step_splits_preserve_samples_ledgers_and_final_bytes(full_cases, case, grouping):
    context, whole = full_cases[case]; cp = model.start(context); samples = []
    for count in grouping:
        out = model.advance_chunk(context, cp, count); assert out['status'] != 'hold'
        samples.extend(out['samples']); encoded = model.checkpoint_bytes(context, out['checkpoint'])
        cp = model.restore_checkpoint(context, encoded, expected_sha256=sha256(encoded).hexdigest())
    assert samples == whole['samples']
    assert model.checkpoint_bytes(context, cp) == model.checkpoint_bytes(context, whole['checkpoint'])


@pytest.mark.parametrize('case', range(6))
@pytest.mark.parametrize('first,second', [((1, 1), (1, 1)), ((1, 1), (2,)), ((2,), (1, 1)), ((2,), (2,))])
def test_two_event_plan_is_independent_of_interval_chunking(full_cases, case, first, second):
    root = full_cases[case][0]
    def calculate(groups1, groups2):
        cp = model.start(root)
        for count in groups1: cp = model.advance_chunk(root, cp, count)['checkpoint']
        next_context = model.adopt_births(context=root, raw_checkpoint=model.checkpoint_bytes(root, cp),
                                         expected_sha256=cp.sha256, inputs=next_inputs(root, cp))
        cp = model.start(next_context)
        for count in groups2:
            out = model.advance_chunk(next_context, cp, count)
            assert out['status'] != 'hold', out['hold']
            cp = out['checkpoint']
        return model.context_bytes(next_context), model.checkpoint_bytes(next_context, cp)
    assert calculate(first, second) == calculate((2,), (2,))


def test_same_time_two_points_keep_distinct_phase_and_unique_history(profiles):
    context, _ = prepared(profiles, cut=0); cp = model.start(context)
    second = model.adopt_births(context=context, raw_checkpoint=model.checkpoint_bytes(context, cp),
                               expected_sha256=cp.sha256, inputs=next_inputs(context, cp))
    new = model.start(second)
    assert new.value['step_index'] == cp.value['step_index'] == 0
    assert new.value['event_sequence'] == 2 and new.value['output_cursor'] == cp.value['output_cursor']+1
    assert new.value['output_prefix_sha256'] != cp.value['output_prefix_sha256']


@pytest.mark.parametrize('target', ['engine', 'point', 'root_profile'])
def test_source_and_profile_fences(base_context, monkeypatch, target):
    if target == 'engine': monkeypatch.setattr(model, 'CODE_SHA256', '0'*64)
    elif target == 'point': monkeypatch.setattr(model.point, 'CODE_SHA256', '0'*64)
    else:
        from dataclasses import replace
        from types import SimpleNamespace
        altered = replace(base_context._root, _profiles=(SimpleNamespace(sha256='0'*64), *base_context._root._profiles[1:]))
        base_context = replace(base_context, _root=altered)
    with pytest.raises(model.FundedContinuationHold): model.start(base_context)


def test_512_leaves_and_scalar_limits(profiles):
    context, kw = prepared(profiles, cut=2, count=509)
    assert len(context.program['leaves']) == 512
    cp = model.start(context)
    assert len(model.checkpoint_bytes(context, cp)) <= model.MAX_CHECKPOINT_BYTES
    out = model.advance_chunk(context, cp, 2)
    assert out['status'] == 'completed', out['hold']
    encoded = model.context_bytes(context)
    assert len(encoded) <= model.MAX_BYTES
    restored = model.restore_context(root_context=kw['context'], raw_bytes=encoded, expected_sha256=sha256(encoded).hexdigest())
    assert model.context_bytes(restored) == encoded


@pytest.mark.parametrize('which', ['point_unit', 'budget', 'clock'])
def test_frozen_history_units_and_clock_are_checked(base_context, which):
    value = json.loads(model.context_bytes(base_context)); record = value['history'][0]
    if which == 'point_unit': record['point_flows']['growth_respiration']['unit'] = 'mg_CH2O'
    elif which == 'budget': record['balances']['whole_carbon']['budget']['value'] = -1.
    else: record['inputs']['at_elapsed_seconds_exact']['unit'] = 'day'
    value['manifest']['history_sha256'] = sha256(raw(value['history'])).hexdigest()
    encoded = raw(value)
    with pytest.raises(model.FundedContinuationHold):
        model.restore_context(root_context=base_context._root, raw_bytes=encoded, expected_sha256=sha256(encoded).hexdigest())


@pytest.mark.parametrize('encoded', [b'{}', b'\xff', b'{"x":1,"x":2}', b'{"x":NaN}'])
def test_external_checkpoint_json_is_strict(base_context, encoded):
    with pytest.raises(model.FundedContinuationHold):
        model.restore_checkpoint(base_context, encoded, expected_sha256=sha256(encoded).hexdigest())


def test_source_change_at_new_endpoint_keeps_original_prefix(base_context, monkeypatch):
    cp = model.start(base_context); evaluate = model.short._evaluate; calls = []
    def changed(p, y, profiles):
        result = evaluate(p, y, profiles); calls.append(1)
        if len(calls) == 5: monkeypatch.setattr(model, 'CODE_SHA256', '0'*64)
        return result
    monkeypatch.setattr(model.short, '_evaluate', changed)
    out = model.advance_chunk(base_context, cp, 1)
    assert out['status'] == 'hold' and out['checkpoint'] is None and out['confirmed_new_steps'] == 0
    assert out['output_prefix_sha256'] == cp.value['output_prefix_sha256']
    assert 'CODE_HOLD' in out['hold']['reason']


def test_minimum_original_one_leaf_advances_two_leaf_state(profiles):
    from test_crop_leaf_carbon_stock_dynamics import program
    p = program(); share = p['leaves'][0]['initial_area']['value']/sum(leaf['initial_area']['value'] for leaf in p['leaves'])
    p['scenario']['climate_state']['canopy_sensible_energy']['value'] *= share; p['leaves'] = p['leaves'][:1]
    root = model.parent.prepare_context(program=p, step_seconds=.125, step_count=4, **profiles); cp = model.parent.start(root)
    v = setup_point(profiles, cut=0)['inputs']; v.update(context_sha256=root.root_sha256, checkpoint_sha256=cp.sha256)
    context = model.prepare_context(parent_context=root, raw_parent_checkpoint=model.parent.checkpoint_bytes(root, cp),
                                     expected_parent_sha256=cp.sha256, inputs=v)
    out = model.advance_chunk(context, model.start(context), 4)
    assert out['status'] == 'completed' and len(out['last_confirmed']['state']) == 113


def test_remaining_scalar_budget_rejects_oversized_new_topology(profiles):
    kw = setup_point(profiles, cut=0)
    root = model.parent.prepare_context(program=kw['context'].program, step_seconds=.125, step_count=250, **profiles)
    cp = model.parent.start(root); kw['inputs'].update(context_sha256=root.root_sha256, checkpoint_sha256=cp.sha256)
    with pytest.raises(model.FundedContinuationHold, match='CAPACITY_HOLD'):
        model.prepare_context(parent_context=root, raw_parent_checkpoint=model.parent.checkpoint_bytes(root, cp),
                              expected_parent_sha256=cp.sha256, inputs=kw['inputs'])


@pytest.mark.parametrize('target', ['MAX_BYTES', 'MAX_CHECKPOINT_BYTES'])
def test_byte_budgets_remain_enforced(base_context, monkeypatch, target):
    monkeypatch.setattr(model, target, 32)
    with pytest.raises(model.FundedContinuationHold, match='CAPACITY_HOLD'): model.start(base_context)


@pytest.mark.parametrize('which', ['leaf_unit', 'curve_unit', 'incoming_temperature'])
def test_frozen_leaf_declarations_reject_unit_substitution_without_recalculation(base_context, which):
    value = json.loads(model.context_bytes(base_context)); record = value['history'][0]
    leaf = record['new_leaves'][0]; declared = record['inputs']['events'][0]['leaf']
    if which == 'leaf_unit': leaf['initial_carbon']['unit'] = declared['initial_carbon']['unit'] = 'mg_CH2O'
    elif which == 'curve_unit': leaf['curve']['values']['maximum_area']['unit'] = declared['curve']['values']['maximum_area']['unit'] = 'cm2'
    else: record['inputs']['events'][0]['incoming_temperature']['unit'] = 'K'
    value['program']['leaves'][-1] = leaf
    for name in ('program', 'seed', 'history'): value['manifest'][name+'_sha256'] = sha256(raw(value[name])).hexdigest()
    encoded = raw(value)
    with pytest.raises(model.FundedContinuationHold):
        model.restore_context(root_context=base_context._root, raw_bytes=encoded, expected_sha256=sha256(encoded).hexdigest())
