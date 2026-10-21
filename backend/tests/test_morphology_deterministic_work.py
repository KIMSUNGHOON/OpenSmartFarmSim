"""Morphology consumption is explicit, version-bound, and idle at construction."""
import pytest

from app.crop_morphology_execution_worker import MorphologyExecutionWorker
from app.crop_morphology_execution import INPUT_VERSION
from app.deterministic_work import DeterministicWorkerLoop, LoopHold
from app.job_store import JobStore
from app.runtime_roles import RuntimeLoginPolicy


@pytest.fixture
def worker(tmp_path, monkeypatch):
    policy = RuntimeLoginPolicy('test_jobs', 'test_owner', 'test_runtime', 'postgres')
    jobs = JobStore('dbname=postgres', policy.schema, tmp_path/'unused', runtime_identity=(policy,'authority'),
        audit_runtime_grants=True, principal_provider=lambda: {'authenticated':True,'tenant_id':'tenant-1',
            'scopes': {'metadata','simulation_execute'}})
    value = object.__new__(MorphologyExecutionWorker); value.jobs = jobs; value.tenant_id = 'tenant-1'
    monkeypatch.setattr(value, '_binding', lambda: None)
    monkeypatch.setattr(value, 'run_once', lambda *_: pytest.fail('construction started calculation'))
    return value


def test_explicit_morphology_loop_is_constructed_without_starting_work(worker):
    loop = DeterministicWorkerLoop(worker, input_versions=frozenset({INPUT_VERSION}))
    assert loop.worker is worker and loop.discovery.input_versions == frozenset({INPUT_VERSION})


@pytest.mark.parametrize('versions', [frozenset(), frozenset({'morphology-execution-input-v2'}),
    frozenset({'joint-crop-climate-execution-input-v1'}), frozenset({INPUT_VERSION,'economic-calculation-input-v1'})])
def test_future_other_and_mixed_versions_are_not_implicitly_enabled(worker, versions):
    with pytest.raises(LoopHold): DeterministicWorkerLoop(worker, input_versions=versions)
