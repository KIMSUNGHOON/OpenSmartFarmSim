"""Real SCRAM/transactions, synthetic review captures and keys; no real G1 proof."""

from hashlib import sha256
from dataclasses import asdict
import json
import os
from pathlib import Path
import subprocess
import sys

import pytest
from psycopg import sql

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from app.thermal_simulation_worker import ThermalSimulationWorker, SimulationInput
from app.runtime_roles import RolePolicyHold
from login_database import login_database, login_scope
from test_thermal_publisher import setup as publisher_fixture


@pytest.fixture
def simulation_setup(login_scope, request):
    base, policy, dsns = login_scope
    publisher, runs, jobs, review, snapshot_id, release, resolver, evidence = publisher_fixture.__wrapped__(
        base, request, schema_installed=True)
    principal = {'authenticated': True, 'tenant_id': 'tenant-a', 'scopes': {
        'metadata', 'artifact', 'cancel', 'simulation_execute', 'thermal_snapshot_read',
        'thermal_run_read', 'thermal_run_publish', 'decision_context_read'}}
    provider = lambda: principal
    jobs.runtime_identity = runs.runtime_identity = (policy, 'authority')
    jobs._dsn = runs.dsn = dsns['authority']
    jobs.audit_runtime_grants = True
    jobs.principal_provider = runs._principal_provider = provider
    input_data = dict(input_version='thermal-simulation-input-v1', snapshot_id=snapshot_id,
                      review_job_id=str(review['job_id']))
    job = jobs.submit('tenant-a', 'simulation', input_data, 'thermal-target')
    worker = ThermalSimulationWorker(publisher, tenant_id='tenant-a')
    return worker, publisher, runs, jobs, job, input_data, principal, base


def run_count(runs):
    with runs.connect() as conn:
        return conn.execute(sql.SQL('SELECT count(*) AS n FROM {}').format(runs._table('thermal_g1_runs'))).fetchone()['n']


def test_real_job_completion_and_run_are_atomic_and_replayable(simulation_setup):
    worker, _, runs, jobs, job, _, _, _ = simulation_setup
    neighboring = jobs.submit('tenant-a', 'simulation', {'fixture': 'different-model'}, 'neighbor')
    result = worker.run_once(str(job['job_id']))
    assert result.state == 'succeeded' and result.run_id
    assert jobs.get_job('tenant-a', job['job_id'])['state'] == 'succeeded'
    artifact = json.loads(jobs.read_artifact('tenant-a', job['job_id']))
    run = runs.get_run('tenant-a', result.run_id)
    assert artifact['run_id'] == run['run_id'] and artifact['snapshot_id'] == run['report']['snapshot_id']
    assert artifact['report_sha256'] == sha256(run['report_raw']).hexdigest()
    assert artifact['trace_sha256'] == [sha256(raw).hexdigest() for raw in run['trace_raws']]
    assert artifact['claim_scope'] == 'synthetic_thermal_replay_only'
    publication = jobs.get_publication('tenant-a', job['job_id'])
    assert publication['decision_id'] is None
    outcomes = jobs.list_attempt_outcomes('tenant-a', job['job_id'])
    assert len(outcomes) == 1 and outcomes[0]['state'] == 'succeeded' and outcomes[0]['decision_id'] is None
    assert jobs.list_decisions('tenant-a', job['job_id']) == []
    assert worker.run_once(str(job['job_id'])) is None and run_count(runs) == 1
    assert jobs.get_job('tenant-a', neighboring['job_id'])['state'] == 'queued'


@pytest.mark.parametrize('fault', ['release', 'execution', 'wrong_review', 'wrong_snapshot'])
def test_missing_evidence_holds_without_job_artifact_or_run(simulation_setup, fault):
    worker, publisher, runs, jobs, job, data, _, _ = simulation_setup
    if fault == 'release': publisher.release_resolver = lambda *_: None
    if fault == 'execution': publisher.execution_verifier = lambda *_: False
    if fault == 'wrong_review':
        data = {**data, 'review_job_id': '00000000-0000-0000-0000-000000000000'}
        job = jobs.submit('tenant-a', 'simulation', data, 'wrong-review')
    if fault == 'wrong_snapshot':
        data = {**data, 'snapshot_id': 'thermal-snapshot-v1:'+('0'*64)}
        job = jobs.submit('tenant-a', 'simulation', data, 'wrong-snapshot')
    result = worker.run_once(str(job['job_id']))
    assert result.state == 'hold' and result.run_id is None
    assert result.reason_code.startswith('thermal_')
    assert jobs.get_publication('tenant-a', job['job_id']) is None and run_count(runs) == 0


def test_invalid_input_is_fatal_and_cannot_publish(simulation_setup):
    worker, _, runs, jobs, _, _, _, _ = simulation_setup
    bad = jobs.submit('tenant-a', 'simulation', {'approved': True}, 'invalid')
    result = worker.run_once(str(bad['job_id']))
    assert result.state == 'failed' and result.reason_code == 'simulation_input_rejected'
    assert run_count(runs) == 0


def test_cancel_after_prepare_cannot_publish(simulation_setup, monkeypatch):
    worker, publisher, runs, jobs, job, _, _, _ = simulation_setup
    original = publisher.prepare
    def prepare(*args):
        packet = original(*args)
        assert jobs.cancel('tenant-a', job['job_id'])
        return packet
    monkeypatch.setattr(publisher, 'prepare', prepare)
    result = worker.run_once(str(job['job_id']))
    assert result.state == 'canceled' and run_count(runs) == 0
    assert jobs.get_publication('tenant-a', job['job_id']) is None


def test_expiry_after_run_insert_rolls_back_run_and_job_publication(simulation_setup, monkeypatch):
    _, publisher, runs, jobs, job, _, _, _ = simulation_setup
    worker = ThermalSimulationWorker(publisher, tenant_id='tenant-a', lease_seconds=2)
    original = runs._publish_verified_in_transaction
    def slow(conn, *args, **kwargs):
        receipt = original(conn, *args, **kwargs)
        conn.execute('SELECT pg_sleep(2.1)')
        return receipt
    monkeypatch.setattr(runs, '_publish_verified_in_transaction', slow)
    result = worker.run_once(str(job['job_id']))
    assert result.state == 'unclosed' and result.reason_code == 'simulation_lease_lost'
    assert run_count(runs) == 0 and jobs.get_publication('tenant-a', job['job_id']) is None
    assert jobs.get_job('tenant-a', job['job_id'])['state'] == 'simulating'


def test_crash_after_run_insert_recovers_in_a_new_attempt(simulation_setup, monkeypatch):
    worker, publisher, runs, jobs, job, _, _, base = simulation_setup
    original = runs._publish_verified_in_transaction
    def crash(conn, *args, **kwargs):
        original(conn, *args, **kwargs)
        raise SystemExit('synthetic-worker-stop')
    monkeypatch.setattr(runs, '_publish_verified_in_transaction', crash)
    with pytest.raises(SystemExit): worker.run_once(str(job['job_id']))
    assert run_count(runs) == 0 and jobs.get_publication('tenant-a', job['job_id']) is None
    with base.connect() as conn:
        conn.execute(sql.SQL("UPDATE {} SET lease_until=clock_timestamp()-interval '1 second' WHERE job_id=%s")
            .format(jobs._table('jobs')), (job['job_id'],))
    monkeypatch.setattr(runs, '_publish_verified_in_transaction', original)
    fresh = ThermalSimulationWorker(publisher, tenant_id='tenant-a')
    result = fresh.run_once(str(job['job_id']))
    assert result.state == 'succeeded' and result.attempt == 2 and run_count(runs) == 1
    assert [row['state'] for row in jobs.list_attempt_outcomes('tenant-a', job['job_id'])] == ['lease_expired', 'succeeded']


def test_publication_failure_rolls_back_run_and_requeues(simulation_setup, monkeypatch):
    worker, _, runs, jobs, job, _, _, _ = simulation_setup
    def fail(*_args, **_kwargs): raise ValueError('synthetic-private-failure')
    monkeypatch.setattr(jobs, '_insert_publication', fail)
    result = worker.run_once(str(job['job_id']))
    assert result.state == 'queued' and result.reason_code == 'simulation_runtime_failure'
    assert run_count(runs) == 0 and jobs.get_publication('tenant-a', job['job_id']) is None


def test_scope_and_login_grant_drift_cannot_claim_or_publish(simulation_setup):
    worker, _, runs, jobs, job, _, principal, base = simulation_setup
    principal['scopes'].remove('simulation_execute')
    with pytest.raises(ValueError, match='simulation execution denied'): worker.run_once(str(job['job_id']))
    assert jobs.get_job('tenant-a', job['job_id'])['state'] == 'queued' and run_count(runs) == 0
    principal['scopes'].add('simulation_execute')
    policy = jobs.runtime_identity[0]
    with base.connect() as conn:
        conn.execute(sql.SQL('GRANT SELECT ON {}.thermal_g1_runs TO {}').format(
            sql.Identifier(policy.schema), sql.Identifier(policy.roles['worker'])))
    with pytest.raises(RolePolicyHold): worker.run_once(str(job['job_id']))


@pytest.mark.parametrize('fault', ['unbound', 'wrong_dsn', 'different_principal', 'no_audit'])
def test_constructor_requires_matching_authenticated_stores(simulation_setup, fault):
    _, publisher, runs, jobs, _, _, _, _ = simulation_setup
    if fault == 'unbound': jobs.runtime_identity = None
    if fault == 'wrong_dsn': runs.dsn = 'private-other-dsn'
    if fault == 'different_principal': runs._principal_provider = lambda: None
    if fault == 'no_audit': jobs.audit_runtime_grants = False
    with pytest.raises(ValueError, match='simulation worker binding rejected'):
        ThermalSimulationWorker(publisher, tenant_id='tenant-a')


def test_explicit_target_and_current_binding_are_required_after_startup(simulation_setup):
    worker, _, runs, jobs, job, _, _, _ = simulation_setup
    for value in (None, 1, 'wrong-job', 'AAAAAAAA-AAAA-4AAA-8AAA-AAAAAAAAAAAA'):
        with pytest.raises(ValueError, match='simulation job ID rejected'): worker.run_once(value)
    assert jobs.get_job('tenant-a', job['job_id'])['state'] == 'queued' and run_count(runs) == 0
    jobs.runtime_identity = None
    with pytest.raises(ValueError, match='simulation worker binding rejected'):
        worker.run_once(str(job['job_id']))


@pytest.mark.parametrize('change', [{'input_version': 'other'}, {'snapshot_id': 'thermal-snapshot-v1:'+('A'*64)},
    {'review_job_id': 'not-a-job'}, {'coefficients': {}}, {'approved_g1': True}])
def test_input_is_closed_and_reference_only(change):
    value = dict(input_version='thermal-simulation-input-v1', snapshot_id='thermal-snapshot-v1:'+('a'*64),
        review_job_id='00000000-0000-0000-0000-000000000000')
    with pytest.raises(ValueError): SimulationInput.model_validate(value | change)


@pytest.mark.parametrize('crash', [False, True])
def test_actual_python_process_executes_and_recovers_without_a_model_call(simulation_setup, tmp_path, crash):
    worker, publisher, runs, jobs, job, _, principal, _ = simulation_setup
    release_raw, _ = publisher.release_resolver('tenant-a', 'unused')
    verified = publisher.release_verifier(release_raw, publisher.release_resolver('tenant-a', 'unused')[1])
    data = {'policy': asdict(jobs.runtime_identity[0]), 'dsn': jobs._dsn,
        'artifact_root': str(jobs.artifact_root), 'root': str(publisher.root),
        'release': json.loads(release_raw), 'evidence_hex': verified['review_evidence_raw'].hex(),
        'scopes': sorted(principal['scopes']), 'crash': crash}
    config = tmp_path / 'private-synthetic-config.json'
    config.write_text(json.dumps(data)); config.chmod(0o600)
    factory = tmp_path / 'synthetic_sim_process.py'
    factory.write_text('''import os, json, hmac
from pathlib import Path
from hashlib import sha256
from app.job_store import JobStore
from app.runtime_roles import RuntimeLoginPolicy
from app.thermal_publisher import ThermalG1Publisher
from app.thermal_run_store import ThermalRunStore
from app.thermal_simulation_worker import ThermalSimulationWorker
from test_job_evidence import cli_store
from test_thermal_run_store import verify_test_context
from test_thermal_publisher import canonical, GATE_KEY, RELEASE_KEY
def build():
    data=json.loads(Path(os.environ['OSSF_SIMULATION_TEST_CONFIG']).read_text())
    principal={'authenticated':True,'tenant_id':'tenant-a','scopes':set(data['scopes'])}
    provider=lambda:principal
    binding=(RuntimeLoginPolicy(**data['policy']),'authority')
    jobs=cli_store(JobStore(data['dsn'],binding[0].schema,Path(data['artifact_root']),principal_provider=provider))
    jobs.runtime_identity=binding; jobs.audit_runtime_grants=True
    def verifier(raw,signature):
        if not hmac.compare_digest(signature,hmac.new(RELEASE_KEY,b'thermal-g1-release-v1\\0'+raw,sha256).hexdigest()): return None
        return {'authority_id':data['release']['authority_id'],'reviewer':data['release']['reviewer'],
            'issued_at_utc':data['release']['issued_at_utc'],'review_evidence_raw':bytes.fromhex(data['evidence_hex'])}
    runs=ThermalRunStore(data['dsn'],binding[0].schema,gate_key=GATE_KEY,release_verifier=verifier,
        context_verifier=verify_test_context,principal_provider=provider,runtime_identity=binding)
    def release(*_):
        raw=canonical(data['release'])
        return raw,hmac.new(RELEASE_KEY,b'thermal-g1-release-v1\\0'+raw,sha256).hexdigest()
    publisher=ThermalG1Publisher(runs,jobs,release,root=Path(data['root']),gate_key=GATE_KEY,
        release_verifier=verifier,execution_verifier=lambda *_:True)
    if data['crash']:
        original=runs._publish_verified_in_transaction
        def abrupt(conn,*args,**kwargs):
            original(conn,*args,**kwargs)
            os._exit(71)
        runs._publish_verified_in_transaction=abrupt
    return ThermalSimulationWorker(publisher,tenant_id='tenant-a')
''')
    factory.chmod(0o600)
    backend = Path(__file__).resolve().parents[1]
    env = {'PATH': '/usr/bin:/bin', 'LANG': 'C.UTF-8', 'OSSF_SIMULATION_TEST_CONFIG': str(config),
        'PYTHONPATH': os.pathsep.join((str(tmp_path), str(backend), str(backend/'tests')))}
    argv = [sys.executable, '-m', 'app.simulation_work', '--factory',
        'synthetic_sim_process:build', '--job-id', str(job['job_id'])]
    result = subprocess.run(argv, cwd=backend, env=env, capture_output=True, text=True, timeout=30)
    if crash:
        assert result.returncode == 71 and result.stdout == ''
        assert run_count(runs) == 0 and jobs.get_publication('tenant-a', job['job_id']) is None
        assert jobs.get_job('tenant-a', job['job_id'])['state'] == 'simulating'
        with jobs.connect() as conn:
            conn.execute(sql.SQL("UPDATE {} SET lease_until=clock_timestamp()-interval '1 second' WHERE job_id=%s")
                .format(jobs._table('jobs')), (job['job_id'],))
        data['crash'] = False
        config.write_text(json.dumps(data))
        result = subprocess.run(argv, cwd=backend, env=env, capture_output=True, text=True, timeout=30)
    assert result.returncode == 0, result.stderr
    output = json.loads(result.stdout)
    assert output['result']['state'] == 'succeeded' and output['result']['job_id'] == str(job['job_id'])
    assert output['result']['attempt'] == (2 if crash else 1)
    assert jobs.get_job('tenant-a', job['job_id'])['state'] == 'succeeded'
    assert runs.get_run('tenant-a', output['result']['run_id']) is not None
    assert data['dsn'] not in result.stdout+result.stderr and str(config) not in result.stdout+result.stderr
