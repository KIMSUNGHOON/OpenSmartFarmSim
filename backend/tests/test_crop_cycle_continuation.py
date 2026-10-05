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
