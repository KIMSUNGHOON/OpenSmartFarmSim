from copy import deepcopy
import json
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


@pytest.mark.parametrize('case', CASES, ids=lambda c:c['case_id'])
def test_actual_rhs_program_matches_original_state_cumulatives_ledgers_events(case):
    p = case['program']; before = deepcopy(p)
    expected = original.integrate_plant_startup(**p, **PROFILES)
    actual, chunks = finish(context(p))
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
