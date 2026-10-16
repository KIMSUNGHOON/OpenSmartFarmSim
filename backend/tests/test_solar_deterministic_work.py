"""Closed Solar discovery/outcome boundaries; actual workers have separate tests."""
from dataclasses import replace
import json
from threading import Event
from uuid import UUID,uuid4
import pytest
from app.deterministic_work import DeterministicWorkerLoop,LoopHold
from app.deterministic_job_discovery import DiscoveryPage,DiscoveredJob
from app.crop_greenhouse_solar_execution_worker import SolarExecutionWorker,SolarExecutionOutcome
from app.crop_greenhouse_solar_execution import INPUT_VERSION as VERSION
from app.economic_calculation_worker import EconomicCalculationOutcome
from app.job_store import JobStore
from app.runtime_roles import RuntimeLoginPolicy


@pytest.fixture
def isolated_solar(tmp_path, monkeypatch):
    policy = RuntimeLoginPolicy('test_jobs', 'test_owner', 'test_runtime', 'postgres')
    jobs = JobStore('dbname=postgres', policy.schema, tmp_path / 'unused',
        runtime_identity=(policy, 'authority'), audit_runtime_grants=True,
        principal_provider=lambda: {'authenticated': True, 'tenant_id': 'tenant-a',
            'scopes': {'metadata', 'simulation_execute'}})
    worker = object.__new__(SolarExecutionWorker)
    worker.jobs, worker.tenant_id = jobs, 'tenant-a'
    monkeypatch.setattr(worker, '_binding', lambda: None)
    return DeterministicWorkerLoop(worker, input_versions=frozenset({VERSION})), worker


@pytest.mark.parametrize('state', ['queued', 'succeeded', 'failed', 'hold', 'canceled'])
def test_solar_closed_outcome_is_bounded_metadata(isolated_solar, monkeypatch, state):
    loop, worker = isolated_solar; identity = str(uuid4()); stop = Event()
    monkeypatch.setattr(loop.discovery, 'page', lambda **_: DiscoveryPage((DiscoveredJob(identity, VERSION),), 1, None))
    def run_once(job):
        assert job == identity; stop.set()
        return SolarExecutionOutcome(UUID(job), 1, state, 'solar_execution_busy', 'private-result-marker')
    monkeypatch.setattr(worker, 'run_once', run_once)
    events = []; loop.run(stop, emit=events.append)
    assert events == [{'version': 1, 'event': 'attempt', 'job_id': identity,
        'attempt': 1, 'state': state, 'reason_code': 'solar_execution_busy'}]
    assert 'private-result-marker' not in json.dumps(events)


@pytest.mark.parametrize('fault', ['economic_outcome', 'unclosed', 'attempt_bool', 'job', 'reason'])
def test_solar_invalid_outcome_stops_before_emission(isolated_solar, monkeypatch, fault):
    loop, worker = isolated_solar; identity = str(uuid4())
    value = SolarExecutionOutcome(UUID(identity), 1, 'succeeded', 'completed')
    if fault == 'economic_outcome': value = EconomicCalculationOutcome(UUID(identity), 1, 'succeeded', 'completed', None)
    elif fault == 'unclosed': value = replace(value, state='unclosed')
    elif fault == 'attempt_bool': value = replace(value, attempt=True)
    elif fault == 'job': value = replace(value, job_id=uuid4())
    else: value = replace(value, reason_code='private marker!')
    monkeypatch.setattr(loop.discovery, 'page', lambda **_: DiscoveryPage((DiscoveredJob(identity, VERSION),), 1, None))
    monkeypatch.setattr(worker, 'run_once', lambda *_: value)
    events = []
    with pytest.raises(LoopHold, match='^deterministic_outcome_rejected$'): loop.run(Event(), emit=events.append)
    assert events == []


@pytest.mark.parametrize('version', ['economic-calculation-input-v1', 'joint-crop-climate-execution-input-v1',
    'joint-ventilation-execution-input-v1', 'joint-solar-execution-input-v2'])
def test_solar_worker_rejects_unconfigured_versions(isolated_solar, version):
    _, worker = isolated_solar
    with pytest.raises(LoopHold, match='^deterministic_binding_rejected$'):
        DeterministicWorkerLoop(worker, input_versions=frozenset({version}))
