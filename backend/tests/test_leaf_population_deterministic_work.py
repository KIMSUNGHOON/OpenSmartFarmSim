"""LeafPopulation consumption is explicit, version-bound, and idle at construction."""
import pytest
from types import SimpleNamespace
from uuid import UUID

from app.crop_leaf_population_execution_worker import LeafPopulationExecutionWorker, LeafPopulationExecutionOutcome
from app.crop_leaf_population_execution import INPUT_VERSION
from app.deterministic_work import DeterministicWorkerLoop, LoopHold
from app.job_store import JobStore
from app.runtime_roles import RuntimeLoginPolicy


@pytest.fixture
def worker(tmp_path, monkeypatch):
    policy = RuntimeLoginPolicy('test_jobs', 'test_owner', 'test_runtime', 'postgres')
    jobs = JobStore('dbname=postgres', policy.schema, tmp_path/'unused', runtime_identity=(policy,'authority'),
        audit_runtime_grants=True, principal_provider=lambda: {'authenticated':True,'tenant_id':'tenant-1',
            'scopes': {'metadata','simulation_execute'}})
    value = object.__new__(LeafPopulationExecutionWorker); value.jobs = jobs; value.tenant_id = 'tenant-1'
    monkeypatch.setattr(value, '_binding', lambda: None)
    monkeypatch.setattr(value, 'run_once', lambda *_: pytest.fail('construction started calculation'))
    return value


def test_explicit_leaf_population_loop_is_constructed_without_starting_work(worker):
    loop = DeterministicWorkerLoop(worker, input_versions=frozenset({INPUT_VERSION}))
    assert loop.worker is worker and loop.discovery.input_versions == frozenset({INPUT_VERSION})


@pytest.mark.parametrize('versions', [frozenset(), frozenset({'leaf-population-execution-input-v2'}),
    frozenset({'joint-crop-climate-execution-input-v1'}), frozenset({'morphology-execution-input-v1'}),
    frozenset({INPUT_VERSION,'economic-calculation-input-v1'})])
def test_future_other_and_mixed_versions_are_not_implicitly_enabled(worker, versions):
    with pytest.raises(LoopHold): DeterministicWorkerLoop(worker, input_versions=versions)


def test_exact_leaf_outcome_emits_only_safe_attempt_metadata(worker):
    loop = DeterministicWorkerLoop(worker, input_versions=frozenset({INPUT_VERSION}))
    identity = '00000000-0000-4000-8000-000000000017'
    result = LeafPopulationExecutionOutcome(UUID(identity), 1, 'succeeded', 'leaf_population_completed', '1'*64)
    assert loop._event(result, SimpleNamespace(job_id=identity)) == {'version': 1, 'event': 'attempt',
        'job_id': identity, 'attempt': 1, 'state': 'succeeded', 'reason_code': 'leaf_population_completed'}


@pytest.mark.parametrize('fault', ['wrong_type', 'unclosed', 'wrong_job'])
def test_unclosed_other_job_or_other_family_outcome_is_rejected(worker, fault):
    loop = DeterministicWorkerLoop(worker, input_versions=frozenset({INPUT_VERSION}))
    identity = '00000000-0000-4000-8000-000000000017'
    result = LeafPopulationExecutionOutcome(UUID(identity), 1, 'succeeded', 'leaf_population_completed')
    if fault == 'wrong_type':
        from app.crop_morphology_execution_worker import MorphologyExecutionOutcome
        result = MorphologyExecutionOutcome(UUID(identity), 1, 'succeeded', 'morphology_completed')
    elif fault == 'unclosed': result = LeafPopulationExecutionOutcome(UUID(identity), 1, 'unclosed', 'leaf_population_execution_lease_lost')
    else: result = LeafPopulationExecutionOutcome(UUID('00000000-0000-4000-8000-000000000018'), 1, 'succeeded', 'leaf_population_completed')
    with pytest.raises(LoopHold): loop._event(result, SimpleNamespace(job_id=identity))
