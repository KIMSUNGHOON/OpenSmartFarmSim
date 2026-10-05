from copy import deepcopy
from dataclasses import replace
import json
from math import inf, nan
from pathlib import Path

import pytest

from app import crop_cycle_continuation as cycle
from app import crop_plant_startup_integration as original
from app.crop_growth_rates import ReferenceParameters
from app.crop_fruit_cohorts import ReferenceFruitCohortParameters
from app.crop_fruit_transport import ReferenceFruitTransportParameters

ROOT = Path(__file__).resolve().parents[2]
CASES = json.loads((ROOT / 'fixtures/crop-plant-startup-integration-reference-v1.json').read_bytes())['cases']
PROFILES = {
    'growth_profile': ReferenceParameters((ROOT / 'fixtures/crop-growth-reference-parameters-v1.json').read_bytes()),
    'cohort_profile': ReferenceFruitCohortParameters((ROOT / 'fixtures/crop-fruit-cohort-reference-parameters-v1.json').read_bytes()),
    'transport_profile': ReferenceFruitTransportParameters((ROOT / 'fixtures/crop-fruit-transport-reference-parameters-v1.json').read_bytes()),
}


def program(name='empty-entry'):
    return deepcopy(next(c['program'] for c in CASES if c['case_id'] == name))


def context(candidate=None, **profiles):
    return cycle.prepare_context(**(candidate or program()), **(profiles or PROFILES))


def test_initial_checkpoint_has_original_seed_no_confirmed_past_and_binary_roundtrip():
    ctx = context()
    cp = cycle.start(ctx)
    assert cp['phase'] == 'initial-ready' and cp['steps'] == cp['sequence'] == 0
    assert len(cp['y']) == len(cp['seed']) == 121 and cp['y'] == cp['seed']
    assert cp['boundary_cursor'] == cp['output_cursor'] == cp['event_cursor'] == 0
    assert cp['parent_sha256'] is None
    assert cycle.restore_checkpoint(ctx, cycle.checkpoint_bytes(ctx, cp)) == cp
    assert all(type(v) is float for v in cp['y'])
    assert cp['root_sha256'] == ctx.root_sha256


@pytest.mark.parametrize('key', list(PROFILES))
def test_context_requires_exact_fixed_profile(key):
    profiles = dict(PROFILES); profiles[key] = {}
    with pytest.raises(cycle.CycleContinuationRejected, match='PROFILE_HOLD'):
        context(**profiles)


@pytest.mark.parametrize('key,bad', [('solver', {}), ('segments', []), ('events', [{}]), ('output_times', [])])
def test_context_preserves_closed_input_preflight(key, bad):
    p = program(); p[key] = bad
    with pytest.raises(cycle.CycleContinuationRejected):
        context(p)


def test_context_copies_caller_program_and_pins_new_code_root():
    p = program(); before = deepcopy(p); ctx = context(p)
    p['solver']['max_step_seconds'] = 8
    p['initial_state']['input_id'] = 'changed-after-context'
    assert ctx.program == before
    assert ctx.manifest['code_sha256']['continuation'] == cycle.CODE_SHA256
    assert ctx.manifest['physical_code_sha256'] == original.CODE_HASHES
    assert context(p).root_sha256 != ctx.root_sha256


def finish(ctx, quota=7, transition_quota=10000, checkpoint=None):
    cp = checkpoint or cycle.start(ctx)
    samples, events, chunks = [], [], []
    while True:
        result = cycle.advance_chunk(ctx, cp, {'max_steps': quota, 'max_transitions': transition_quota})
        assert result['output_start'] == len(samples)
        assert result['event_start'] == len(events)
        samples.extend(result['samples']); events.extend(result['events']); chunks.append(result)
        if result['status'] != 'yielded':
            return {**result, 'samples': samples, 'events': events}, chunks
        cp = cycle.restore_checkpoint(ctx, cycle.checkpoint_bytes(ctx, result['checkpoint']))


@pytest.fixture(scope='module')
def originals():
    return {c['case_id']:original.integrate_plant_startup(**c['program'], **PROFILES) for c in CASES}


@pytest.mark.parametrize('quota', [1,2,7,64,10000])
@pytest.mark.parametrize('case', CASES, ids=lambda c:c['case_id'])
def test_actual_rhs_program_matches_original_state_cumulatives_ledgers_events(case, quota, originals):
    p = case['program']; before = deepcopy(p)
    expected = originals[case['case_id']]
    actual, chunks = finish(context(p), quota)
    assert actual['status'] == expected['status'] == 'completed'
    for field in ('samples', 'events', 'steps', 'planned_steps', 'scope'):
        assert actual[field] == expected[field]
    assert p == before
    assert actual['checkpoint']['phase'] == 'boundary-committed'
    assert actual['checkpoint']['event_count'] == len(expected['events'])
    for a, b in zip(chunks, chunks[1:]):
        assert b['checkpoint']['parent_sha256'] == a['checkpoint']['checkpoint_sha256']


def test_step_end_at_event_boundary_has_not_committed_event_or_output_twice():
    ctx = context(program('full-removal-reentry')); cp = cycle.start(ctx)
    first = cycle.advance_chunk(ctx, cp, {'max_steps': 10000, 'max_transitions': 1})
    assert first['checkpoint']['phase'] == 'boundary-committed'
    assert len(first['events']) == len(first['samples']) == 1
    cp = first['checkpoint']
    while cp['at'] != ctx.program['events'][1]['at']:
        step = cycle.advance_chunk(ctx, cp, {'max_steps': 1, 'max_transitions': 1})
        cp = cycle.restore_checkpoint(ctx, cycle.checkpoint_bytes(ctx, step['checkpoint']))
    assert cp['phase'] == 'step-end' and cp['event_count'] == cp['output_cursor'] == 1
    removal = cycle.advance_chunk(ctx, cp, {'max_steps': 10000, 'max_transitions': 1})
    assert removal['checkpoint']['phase'] == 'boundary-committed'
    assert len(removal['samples']) == len(removal['events']) == 1
    assert removal['samples'][0]['state'] == removal['events'][0]['after']
    assert all(q['value'] == 0 for k in ('fruit_number','fruit_carbohydrate') for q in removal['samples'][0]['state'][k])
    next_step = cycle.advance_chunk(ctx, removal['checkpoint'], {'max_steps': 1, 'max_transitions': 1})
    assert next_step['events'] == next_step['samples'] == []


@pytest.mark.parametrize('kind', ['entry','pre-onset','carbon-without-number','underflow','t0-event','event','fractional'])
def test_hold_and_confirmed_past_match_original_without_failed_trial_checkpoint(kind):
    p = program('full-removal-reentry' if kind in ('t0-event','event') else 'night-smooth' if kind == 'fractional' else 'empty-entry')
    initial = p['initial_state']['values']
    if kind == 'entry': p['segments'][0]['fruit_entry']['values']['fruit_number_inflow']['value'] = 100
    if kind == 'pre-onset': initial['temperature_sum']['value'] = 0
    if kind == 'carbon-without-number': initial['fruit_carbohydrate'][0]['value'] = 1
    if kind == 'underflow': initial['stem_root']['value'] = 5e-324
    if kind in ('t0-event','event'): p['events'][0 if kind == 't0-event' else 1]['removals']['values']['leaf']['value'] = 1e6
    if kind == 'fractional':
        initial['buffer']['value'] = 1
        p['output_times'] = [p['output_times'][0], p['output_times'][-1]]
        p['solver']['max_step_seconds'] = 3599
    expected = original.integrate_plant_startup(**p, **PROFILES)
    actual, _ = finish(context(p), 1, 1)
    assert actual['status'] == expected['status'] == 'hold' and actual['checkpoint'] is None
    for key in ('samples','events','steps','planned_steps','hold','last_confirmed'):
        assert actual[key] == expected[key]
    if kind == 'fractional':
        assert actual['hold']['phase'] == 'rk4-k2' and actual['hold']['at'].endswith('59.500000Z')


def reseal(cp):
    cp['checkpoint_sha256'] = original._hash({k:v for k,v in cp.items() if k != 'checkpoint_sha256'})
    return cp


@pytest.mark.parametrize('key,value', [
    ('version','other'), ('root_sha256','0'*64), ('calculated_state_id','changed'), ('at','2026-01-01T00:00:03Z'),
    ('steps',True), ('steps',1), ('event_count',1), ('active_segment',1), ('boundary_cursor',99),
    ('output_cursor',0), ('event_cursor',1), ('sequence',0), ('phase','initial-ready'), ('parent_sha256',None),
    ('output_prefix_sha256','bad'), ('event_prefix_sha256','1'*64), ('extra',0),
])
def test_rehashed_bad_identity_position_counters_are_rejected_before_rhs(key, value, monkeypatch):
    ctx = context(); cp = cycle.advance_chunk(ctx,cycle.start(ctx),{'max_steps':1,'max_transitions':1})['checkpoint']
    cp[key] = value; reseal(cp)
    def forbidden(**kwargs): raise AssertionError('rejected checkpoint reached RHS')
    monkeypatch.setattr(original.coupled,'calculate_plant_startup_rates',forbidden)
    with pytest.raises(cycle.CycleContinuationRejected):
        cycle.advance_chunk(ctx,cp,{'max_steps':1,'max_transitions':1})


@pytest.mark.parametrize('kind', ['seed','clock','clock-bool','temperature','balance','length','bool','nan','inf','negative','unsealed'])
def test_changed_state_seed_clock_and_balance_rejected(kind):
    ctx = context(); cp = cycle.advance_chunk(ctx,cycle.start(ctx),{'max_steps':1,'max_transitions':2})['checkpoint']
    if kind == 'seed': cp['seed'][0] += 1
    if kind == 'clock': cp['clock']['prefix']['numerator'] = '9'*1000
    if kind == 'clock-bool': cp['clock']['prefix']['numerator'] = True
    if kind == 'temperature': cp['y'][4] += 1
    if kind == 'balance': cp['y'][0] += 1
    if kind == 'length': cp['y'].pop()
    if kind == 'bool': cp['y'][0] = True
    if kind == 'nan': cp['y'][0] = nan
    if kind == 'inf': cp['y'][0] = inf
    if kind == 'negative': cp['y'][0] = -1.
    if kind == 'unsealed': cp['y'][0] += 1
    if kind not in ('nan','inf','unsealed'): reseal(cp)
    with pytest.raises(cycle.CycleContinuationRejected):
        cycle.checkpoint_bytes(ctx,cp)


@pytest.mark.parametrize('raw', [b'{',b'null',b'{"y":0,"y":1}',b'{"y":NaN}',b'\xff',b' '*65537,
    '{"version":"x"}'.encode('utf-16'),b'['*2000+b']'*2000])
def test_invalid_closed_utf8_checkpoint_bytes(raw):
    with pytest.raises(cycle.CycleContinuationRejected): cycle.restore_checkpoint(context(),raw)


def test_other_json_encoding_of_valid_checkpoint_is_rejected():
    ctx = context(); raw = json.dumps(cycle.start(ctx)).encode('utf-16')
    with pytest.raises(cycle.CycleContinuationRejected): cycle.restore_checkpoint(ctx,raw)


@pytest.mark.parametrize('budget', [None,{}, {'max_steps':0,'max_transitions':1}, {'max_steps':True,'max_transitions':1},
    {'max_steps':10001,'max_transitions':1}, {'max_steps':1,'max_transitions':0}, {'max_steps':1,'max_transitions':1,'extra':1}])
def test_invalid_budget_is_typed_rejection(budget):
    ctx = context()
    with pytest.raises(cycle.CycleContinuationRejected): cycle.advance_chunk(ctx,cycle.start(ctx),budget)


def test_initial_counter_boolean_and_changed_context_root_are_rejected():
    ctx = context(); cp = cycle.start(ctx); cp['steps'] = False; reseal(cp)
    with pytest.raises(cycle.CycleContinuationRejected): cycle.checkpoint_bytes(ctx,cp)
    with pytest.raises(cycle.CycleContinuationRejected): cycle.start(replace(ctx,root_sha256='0'*64))


def test_completed_checkpoint_cannot_repeat_final_output(originals):
    actual, _ = finish(context(),10000)
    ctx = context()
    with pytest.raises(cycle.CycleContinuationRejected,match='already completed'):
        cycle.advance_chunk(ctx,actual['checkpoint'],{'max_steps':1,'max_transitions':1})


def test_original_odd_step_remainders_and_fractional_trials_unchanged(monkeypatch):
    p = program('positive-tail'); p['solver']['max_step_seconds'] = 7
    traces = [[], []]; index = 0; advance = original._advance
    def observe(y, rates, h, at):
        traces[index].append((at.isoformat(),h))
        return advance(y,rates,h,at)
    monkeypatch.setattr(original,'_advance',observe)
    expected = original.integrate_plant_startup(**p, **PROFILES)
    index = 1; actual, _ = finish(context(p),1,1)
    assert actual['status'] == expected['status'] == 'completed'
    assert traces[0] == traces[1] and any(h != 7 for _,h in traces[0])
    assert actual['samples'] == expected['samples'] and actual['events'] == expected['events']


def test_restore_inspects_checkpoint_without_reintegrating_confirmed_past(monkeypatch):
    ctx = context(); result = cycle.advance_chunk(ctx,cycle.start(ctx),{'max_steps':2,'max_transitions':10000})
    raw = cycle.checkpoint_bytes(ctx,result['checkpoint'])
    def forbidden(**kwargs): raise AssertionError('checkpoint reader reintegrated RHS')
    monkeypatch.setattr(original.coupled,'calculate_plant_startup_rates',forbidden)
    assert cycle.restore_checkpoint(ctx,raw) == result['checkpoint']


@pytest.mark.parametrize('key', ['physical_code_sha256','profile_sha256','policy_sha256','allocation_policy_sha256','python_version'])
def test_rehashed_context_cannot_change_pinned_physical_versions(key):
    ctx = context(); manifest = ctx.manifest
    if type(manifest[key]) is dict:
        manifest[key][next(iter(manifest[key]))] = '0'*64
    else:
        manifest[key] = '0'*64
    other = replace(ctx,_manifest=json.dumps(manifest).encode(),
                    root_sha256=original._hash({'program':ctx.program,'manifest':manifest}))
    with pytest.raises(cycle.CycleContinuationRejected): cycle.start(other)


def test_unexpected_process_failure_propagates_without_numeric_hold(monkeypatch):
    def interrupted(**kwargs): raise RuntimeError('external interruption')
    monkeypatch.setattr(original.coupled,'calculate_plant_startup_rates',interrupted)
    ctx = context(); cp = cycle.start(ctx); before = deepcopy(cp)
    with pytest.raises(RuntimeError,match='external interruption'):
        cycle.advance_chunk(ctx,cp,{'max_steps':1,'max_transitions':1})
    assert cp == before
