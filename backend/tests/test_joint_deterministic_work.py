"""Joint queue consumption: isolated boundaries and actual SCRAM processes."""
from contextlib import ExitStack
from dataclasses import replace
from hashlib import sha256
import json
import os
from pathlib import Path
import signal
from textwrap import indent
from threading import Event
from uuid import UUID, uuid4

import psycopg
import pytest

from app.deterministic_work import DeterministicWorkerLoop, LoopHold
from app.deterministic_job_discovery import DiscoveryPage, DiscoveredJob
from app.crop_climate_joint_execution_worker import JointExecutionWorker, JointExecutionOutcome
from app.economic_calculation_worker import EconomicCalculationOutcome
from app.job_store import JobStore
from app.runtime_roles import RuntimeLoginPolicy
from test_crop_climate_joint_execution_worker import (
    setup as joint_setup, producer_setup, authoring, farm_setup, profiles,
    login_database, original_login_scope, login_scope)
import test_crop_climate_joint_execution_worker as reference
import test_deterministic_work as legacy

VERSION = reference.model.checkpoints.execution.INPUT_VERSION


def save(name, value):
    root = os.environ.get('OSSF_JOINT_CONSUMER_EVIDENCE')
    if root:
        with (Path(root) / (name + '.json')).open('x') as f:
            os.fchmod(f.fileno(), 0o400); json.dump(value, f, sort_keys=True, indent=2)
            f.flush(); os.fsync(f.fileno())


@pytest.fixture(scope='module')
def joint_cleanup(login_database):
    yield
    with psycopg.connect(login_database['admin']) as conn:
        schemas = conn.execute("SELECT count(*) FROM pg_namespace WHERE nspname LIKE 'login_test_%'").fetchone()[0]
        roles = conn.execute("SELECT count(*) FROM pg_roles WHERE rolname LIKE 'login_%'").fetchone()[0]
    assert schemas == roles == 0
    save('database-cleanup', {'schemas': schemas, 'roles': roles})


@pytest.fixture
def isolated_joint(tmp_path, monkeypatch):
    policy = RuntimeLoginPolicy('test_jobs', 'test_owner', 'test_runtime', 'postgres')
    jobs = JobStore('dbname=postgres', policy.schema, tmp_path / 'unused',
        runtime_identity=(policy, 'authority'), audit_runtime_grants=True,
        principal_provider=lambda: {'authenticated': True, 'tenant_id': 'tenant-a',
            'scopes': {'metadata', 'simulation_execute'}})
    worker = object.__new__(JointExecutionWorker)
    worker.jobs, worker.tenant_id = jobs, 'tenant-a'
    monkeypatch.setattr(worker, '_binding', lambda: None)
    return DeterministicWorkerLoop(worker, input_versions=frozenset({VERSION})), worker


@pytest.mark.parametrize('state', ['queued', 'succeeded', 'failed', 'hold', 'canceled'])
def test_joint_closed_outcome_is_bounded_metadata(isolated_joint, monkeypatch, state):
    loop, worker = isolated_joint; identity = str(uuid4()); stop = Event()
    monkeypatch.setattr(loop.discovery, 'page', lambda **_: DiscoveryPage((DiscoveredJob(identity, VERSION),), 1, None))
    def run_once(job):
        assert job == identity; stop.set()
        return JointExecutionOutcome(UUID(job), 1, state, 'joint_execution_busy', 'private-result-marker')
    monkeypatch.setattr(worker, 'run_once', run_once)
    events = []; loop.run(stop, emit=events.append)
    assert events == [{'version': 1, 'event': 'attempt', 'job_id': identity,
        'attempt': 1, 'state': state, 'reason_code': 'joint_execution_busy'}]
    assert 'private-result-marker' not in json.dumps(events)


@pytest.mark.parametrize('fault', ['economic_outcome', 'unclosed', 'attempt_bool', 'job', 'reason'])
def test_joint_invalid_outcome_stops_before_emission(isolated_joint, monkeypatch, fault):
    loop, worker = isolated_joint; identity = str(uuid4())
    value = JointExecutionOutcome(UUID(identity), 1, 'succeeded', 'completed')
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


@pytest.mark.parametrize('version', ['economic-calculation-input-v1', 'joint-crop-climate-execution-input-v2'])
def test_joint_worker_rejects_unconfigured_versions(isolated_joint, version):
    _, worker = isolated_joint
    with pytest.raises(LoopHold, match='^deterministic_binding_rejected$'):
        DeterministicWorkerLoop(worker, input_versions=frozenset({version}))


def joint_factory(worker, value, tmp_path):
    path = reference.producer.fresh_pack(tmp_path, value, b'not-yet-created', worker.server)
    prefix = reference.FRESH_WORKER.split('with MonkeyPatch.context()')[0]
    prefix = prefix.replace("Path(sys.argv[1])", "Path(__file__).with_name('fresh.private.json')")
    prefix = prefix.replace("chunk_budget=8 if p['phase']=='producer' else 128", 'chunk_budget=128')
    suffix = '''
from app.deterministic_work import DeterministicWorkerLoop
import time
directory=Path(__file__).parent
patch=MonkeyPatch();calls=u.producer.measured(patch)
loop=DeterministicWorkerLoop(worker,input_versions=frozenset({u.model.checkpoints.execution.INPUT_VERSION}),page_size=50)
stop_flag=None
run=loop.run
def observed_run(stop,*,emit):
 nonlocal stop_flag
 stop_flag=stop
 return run(stop,emit=emit)
loop.run=observed_run
before=worker._before
def controlled(lease):
 if (directory/'block').exists():
  (directory/'claimed').touch(mode=0o600)
  while (directory/'block').exists():
   if stop_flag.is_set():(directory/'stop-observed').touch(mode=0o600)
   time.sleep(.02)
 return before(lease)
worker._before=controlled
run_once=worker.run_once
def observed_attempt(job_id):
 outcome=run_once(job_id)
 if outcome is not None:
  proof={'state':outcome.state,'attempt':outcome.attempt,'calls':dict(calls),'actual_scram':False}
  with jobs.connect() as conn:
   proof['actual_scram']=bool(conn.pgconn.used_password and conn.info.get_parameters()['require_auth']=='scram-sha-256')
  proof_path=directory/('attempt-'+str(outcome.attempt)+'.private.json')
  pending_path=proof_path.with_suffix('.tmp')
  with pending_path.open('x') as f:
   __import__('os').fchmod(f.fileno(),0o600);json.dump(proof,f);f.flush();__import__('os').fsync(f.fileno())
  __import__('os').replace(pending_path,proof_path)
 return outcome
worker.run_once=observed_attempt
return loop
'''
    factory = tmp_path / 'joint_operator.py'
    factory.write_text('def build():\n' + indent(prefix + suffix, '    ')); factory.chmod(0o600)
    return path, factory


def attempt_proof(tmp_path, attempt):
    value = json.loads((tmp_path / ('attempt-' + str(attempt) + '.private.json')).read_bytes())
    assert value['actual_scram']
    return value


def terminal(worker, job_id, state, raw, value):
    job = worker.jobs.get_job('tenant-1', job_id); assert job['state'] == state
    outcomes = reference.rows(worker, job_id, 'attempt_outcomes')
    assert len(outcomes) == job['attempt_count']
    if state == 'canceled':
        reference.no_published_result(worker, job_id)
        return {'state': state, 'registry': 0, 'publication': 0}
    links = [e for e in reference.rows(worker, job_id, 'job_events') if e['kind'] == reference.model.RESULT_EVENT_KIND]
    assert len(links) == reference.count(worker.server.binding) == 1
    record = worker.results.get('tenant-1', links[0]['reason']['result_id'], value[1]['farm'])
    progress = json.loads(worker.server.inspect('tenant-1', raw))
    packet = json.loads(record['payload_raw'])
    assert packet['policies']['server_progress'] == progress and progress['status'] == 'completed'
    assert progress['steps'] == 16 and progress['times']['last_confirmed']['at'] == '2026-10-01T00:00:32.123456Z'
    publications = reference.rows(worker, job_id, 'job_publications')
    assert len(publications) == 1 and publications[0]['manifest'] == links[0]['reason']
    assert links[0]['reason']['artifact_sha256'] == sha256(record['payload_raw']).hexdigest()
    assert packet['G0_G4'] == 'not_assessed'
    return {'state': state, 'registry': 1, 'publication': 1, 'original_progress': progress,
        'payload_sha256': record['payload_sha256'], 'result_link': links[0]['reason']}


@reference.pytestmark
@pytest.mark.usefixtures('joint_cleanup')
@pytest.mark.parametrize('cancel', [False, True])
def test_scram_joint_automatic_signal_finishes_current_and_skips_following(joint_setup, tmp_path, cancel):
    worker, job_id, raw, value = joint_setup
    body = json.loads(raw); body['revision'] = 'following'
    following = worker.checkpoints.admission.submit('tenant-1', reference.model.results._canonical(body))
    value[4]['scopes'].remove('simulation_create')
    path, factory = joint_factory(worker, value, tmp_path)
    assert job_id not in path.read_text() + factory.read_text()
    block = tmp_path / 'block'; block.touch(mode=0o600)
    try:
        with legacy.process_consumer(tmp_path, 'joint_operator:build') as (process, events, errors):
            legacy.wait_for(lambda: (tmp_path / 'claimed').exists(), process, timeout=20)
            assert worker.jobs.get_job('tenant-1', job_id)['state'] == 'simulating'
            if cancel: assert worker.jobs.cancel('tenant-1', job_id)
            process.send_signal(signal.SIGTERM)
            legacy.wait_for(lambda: (tmp_path / 'stop-observed').exists(), process, timeout=5)
            block.unlink(); process.wait(timeout=150)
        state = 'canceled' if cancel else 'succeeded'
        assert process.returncode == 0 and errors == ['']
        assert [e['event'] for e in events] == ['started', 'attempt', 'stopped']
        assert events[1]['job_id'] == job_id and events[1]['state'] == state
        assert set(events[1]) == {'version', 'event', 'job_id', 'attempt', 'state', 'reason_code'}
        pending = worker.jobs.get_job('tenant-1', following['job_id'])
        assert pending['state'] == 'queued' and pending['attempt_count'] == 0
        proof = attempt_proof(tmp_path, 1)
        assert proof['calls']['step'] == (0 if cancel else 16)
        result = terminal(worker, job_id, state, raw, value)
        save('signal-' + state, {'events': events, 'attempt': proof, 'result': result,
            'no_target_UUID_in_factory_or_configuration': True, 'following_attempts': 0, 'actual_process_exit': process.returncode})
    finally:
        path.unlink(); (tmp_path / 'proof.private.json').unlink()


@reference.pytestmark
@pytest.mark.usefixtures('joint_cleanup')
def test_scram_joint_busy_retry_is_discovered_again_without_direct_dispatch(joint_setup, tmp_path):
    worker, job_id, raw, value = joint_setup
    value[4]['scopes'].remove('simulation_create')
    path, _ = joint_factory(worker, value, tmp_path)
    try:
        with ExitStack() as lock:
            lock.enter_context(worker.server._open('tenant-1', raw, True))
            with legacy.process_consumer(tmp_path, 'joint_operator:build') as (process, events, errors):
                legacy.wait_for(lambda: (tmp_path / 'attempt-1.private.json').exists(), process, timeout=20)
                first = attempt_proof(tmp_path, 1)
                assert first['state'] == 'queued' and all(n == 0 for n in first['calls'].values())
                assert worker.jobs.get_job('tenant-1', job_id)['state'] == 'queued'
                reference.no_published_result(worker, job_id)
                lock.close()
                legacy.wait_for(lambda: worker.jobs.get_job('tenant-1', job_id)['state'] == 'succeeded', process, timeout=160)
        assert process.returncode == 0 and errors == ['']
        assert [(e['attempt'], e['state']) for e in events if e['event'] == 'attempt'] == [(1, 'queued'), (2, 'succeeded')]
        second = attempt_proof(tmp_path, 2)
        assert second['calls']['step'] == 16
        result = terminal(worker, job_id, 'succeeded', raw, value)
        save('retry', {'events': events, 'attempts': [first, second], 'result': result,
            'actual_file_lock_and_persisted_retry': True, 'actual_process_exit': process.returncode})
    finally:
        path.unlink(); (tmp_path / 'proof.private.json').unlink()


@reference.pytestmark
@pytest.mark.usefixtures('joint_cleanup')
def test_scram_joint_unclosed_lease_stops_with_fixed_error_and_no_next_job(joint_setup, tmp_path):
    worker, job_id, raw, value = joint_setup
    body = json.loads(raw); body['revision'] = 'following'
    following = worker.checkpoints.admission.submit('tenant-1', reference.model.results._canonical(body))
    path, _ = joint_factory(worker, value, tmp_path)
    block = tmp_path / 'block'; block.touch(mode=0o600)
    try:
        with legacy.process_consumer(tmp_path, 'joint_operator:build') as (process, events, errors):
            legacy.wait_for(lambda: (tmp_path / 'claimed').exists(), process, timeout=20)
            reference.expire(worker, job_id); block.unlink(); process.wait(timeout=20)
        assert process.returncode == 3
        assert [e['event'] for e in events] == ['started']
        assert json.loads(errors[0]) == {'version': 1, 'ok': False, 'code': 'deterministic_execution_unresolved'}
        proof = attempt_proof(tmp_path, 1)
        assert proof['state'] == 'unclosed' and all(n == 0 for n in proof['calls'].values())
        reference.no_published_result(worker, job_id)
        assert reference.rows(worker, job_id, 'attempt_outcomes') == []
        pending = worker.jobs.get_job('tenant-1', following['job_id'])
        assert pending['state'] == 'queued' and pending['attempt_count'] == 0
        save('unclosed', {'events': events, 'error': json.loads(errors[0]), 'attempt': proof,
            'following_attempts': 0, 'partial_result': False, 'actual_process_exit': process.returncode})
    finally:
        path.unlink(); (tmp_path / 'proof.private.json').unlink()
