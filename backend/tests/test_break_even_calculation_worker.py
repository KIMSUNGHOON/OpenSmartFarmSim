"""Actual leases and atomic rows; all source records and keys are synthetic."""

import json
from pathlib import Path
import sys
from uuid import uuid4

import pytest
from psycopg import sql

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from test_api_break_even_plan import plan_api, post, login_database, login_scope, PROFILE

pytestmark = pytest.mark.parametrize('login_scope', [{**PROFILE, 'break_even_calculation': True}], indirect=True)


@pytest.fixture
def calculation_setup(plan_api):
    from app.break_even_calculation_worker import BreakEvenCalculationWorker
    app, service, body, principal = plan_api
    status, accepted = post(app, body)
    assert status == 202
    principal['scopes'].add('cancel')
    worker = BreakEvenCalculationWorker(service.jobs, service.store, tenant_id='tenant-1')
    return worker, accepted['intent_job']['job_id'], principal


def result_count(worker):
    with worker.jobs.connect() as conn:
        return conn.execute(sql.SQL('SELECT count(*) AS n FROM {}')
            .format(worker.store._table())).fetchone()['n']


def test_calculation_result_and_job_commit_together(calculation_setup, monkeypatch):
    from uuid import UUID
    worker, job_id, _ = calculation_setup
    def unexpected_close(*_, **__):
        raise sys.exc_info()[1]
    monkeypatch.setattr(worker, '_close', unexpected_close)
    outcome = worker.run_once(job_id)
    assert outcome.state == 'succeeded' and outcome.plan_id
    receipt = json.loads(worker.jobs.read_artifact('tenant-1', UUID(job_id)))
    assert receipt['assessment_status'] == 'hold' and receipt['calculation_status'] == 'bracket_only'
    assert receipt['claim_scope'] == 'conditional_user_grid_only'
    assert worker.store.get_break_even_read('tenant-1', outcome.plan_id)[1].status == 'bracket_only'
    assert worker.jobs.get_publication('tenant-1', UUID(job_id))['decision_id'] is None
    assert worker.jobs.list_decisions('tenant-1', UUID(job_id)) == []
    assert len(worker.jobs.list_attempt_outcomes('tenant-1', UUID(job_id))) == 1
    assert worker.run_once(job_id) is None and result_count(worker) == 1
    with worker.jobs.connect() as conn:
        n = conn.execute(sql.SQL("SELECT count(*) AS n FROM {} WHERE job_id=%s AND kind='lease_renewed'")
            .format(worker.jobs._table('job_events')), (job_id,)).fetchone()['n']
    assert n > 0


def test_other_jobs_and_missing_scope_are_not_claimed(calculation_setup):
    from uuid import UUID
    worker, job_id, principal = calculation_setup
    principal['scopes'].remove('break_even_write')
    with pytest.raises(PermissionError): worker.run_once(job_id)
    assert worker.jobs.get_job('tenant-1', UUID(job_id))['attempt_count'] == 0
    principal['scopes'].add('break_even_write')
    for tenant, stage, version in [('tenant-1', 'simulation', 'economic-calculation-input-v1'),
            ('tenant-1', 'collection', 'break-even-calculation-input-v1'),
            ('tenant-2', 'simulation', 'break-even-calculation-input-v1')]:
        other = worker.jobs.submit(tenant, stage, {'input_version': version}, str(uuid4()))
        assert worker.run_once(str(other['job_id'])) is None
    assert worker.jobs.cancel('tenant-1', UUID(job_id))
    assert worker.run_once(job_id) is None and result_count(worker) == 0


def test_forged_plan_is_held_without_result(calculation_setup):
    from uuid import UUID
    worker, job_id, _ = calculation_setup
    with worker.jobs.connect() as conn:
        raw = worker.jobs._verified_input(worker.jobs._locked_job(conn, 'tenant-1', UUID(job_id)))
    value = json.loads(raw)
    value['plan']['fixed_inputs_sha256'] = 'a'*64
    job = worker.jobs.submit('tenant-1', 'simulation', value, 'forged-plan')
    outcome = worker.run_once(str(job['job_id']))
    assert outcome.state == 'hold' and outcome.plan_id is None and result_count(worker) == 0
    assert worker.jobs.get_publication('tenant-1', job['job_id']) is None


@pytest.mark.parametrize('fault,state', [('scope', 'hold'), ('code', 'queued'), ('publication', 'queued')])
def test_post_insert_fault_rolls_back_result_and_completion(calculation_setup, monkeypatch, fault, state):
    from uuid import UUID
    worker, job_id, principal = calculation_setup
    if fault == 'publication':
        def fail(*_, **__): raise RuntimeError('private publication detail')
        monkeypatch.setattr(worker.jobs, '_insert_publication', fail)
    else:
        original = worker.store._checked
        def change(row):
            value = original(row)
            if fault == 'scope': principal['scopes'].remove('break_even_write')
            else: monkeypatch.setattr(worker, '_digests', lambda: ('a'*64, 'b'*64))
            return value
        monkeypatch.setattr(worker.store, '_checked', change)
    outcome = worker.run_once(job_id)
    assert outcome.state == state and outcome.plan_id is None and 'private' not in outcome.reason_code
    assert result_count(worker) == 0 and worker.jobs.get_publication('tenant-1', UUID(job_id)) is None


def test_cancel_before_first_trial_does_not_publish(calculation_setup, monkeypatch):
    from uuid import UUID
    worker, job_id, _ = calculation_setup
    original = worker.jobs.read_input
    def cancel(*args):
        raw = original(*args)
        assert worker.jobs.cancel('tenant-1', UUID(job_id))
        return raw
    monkeypatch.setattr(worker.jobs, 'read_input', cancel)
    assert worker.run_once(job_id).state == 'canceled'
    assert result_count(worker) == 0 and worker.jobs.get_publication('tenant-1', UUID(job_id)) is None


def test_expired_attempt_recovers_and_completes(calculation_setup, monkeypatch):
    worker, job_id, _ = calculation_setup
    original = worker.jobs.read_input
    first = []
    def expire(*args):
        raw = original(*args)
        if not first:
            first.append(True)
            with worker.jobs.connect() as conn:
                conn.execute(sql.SQL("UPDATE {} SET lease_until=clock_timestamp()-interval '1 second' WHERE job_id=%s")
                    .format(worker.jobs._table('jobs')), (job_id,))
        return raw
    monkeypatch.setattr(worker.jobs, 'read_input', expire)
    assert worker.run_once(job_id).state == 'unclosed' and result_count(worker) == 0
    outcome = worker.run_once(job_id)
    assert outcome.state == 'succeeded' and outcome.attempt == 2 and result_count(worker) == 1


def test_actual_foreground_process_completes_existing_plan(calculation_setup, tmp_path):
    from dataclasses import asdict
    import os
    import subprocess
    worker, job_id, principal = calculation_setup
    document = {'dsn': worker.jobs._dsn, 'policy': asdict(worker.jobs.runtime_identity[0]),
        'artifacts': str(worker.jobs.artifact_root),
        'principal': principal | {'scopes': sorted(principal['scopes'])},
        'hold_scope': worker.store._source._source._holds._scope_resolver()}
    config = tmp_path/'break_even_operator.json'
    config.write_text(json.dumps(document))
    config.chmod(0o600)
    factory = tmp_path/'break_even_operator.py'
    factory.write_text('''import json
from pathlib import Path
from app.runtime_roles import RuntimeLoginPolicy
from app.job_store import JobStore
from app.market_source_store import MarketSourceStore
from app.market_candidate_store import MarketCandidateStore
from app.market_hold_store import MarketHoldStore
from app.thermal_run_store import ThermalRunStore
from app.break_even_store import BreakEvenStore
from app.api_market_source import _MarketSources
from app.break_even_calculation_worker import BreakEvenCalculationWorker
from test_market_hold_store import context_verifier, HOLD_KEY
def build():
    data=json.loads(Path(__file__).with_name('break_even_operator.json').read_text())
    policy=RuntimeLoginPolicy(**data['policy'])
    provider=lambda: data['principal']
    kwargs=dict(runtime_identity=(policy,'authority'),principal_provider=provider)
    jobs=JobStore(data['dsn'],policy.schema,Path(data['artifacts']),audit_runtime_grants=True,**kwargs)
    sources=MarketSourceStore(data['dsn'],policy.schema,**kwargs)
    contexts=ThermalRunStore(data['dsn'],policy.schema,gate_key=b'synthetic-gate-key-32-bytes-long!',
        release_verifier=lambda *_:None,context_verifier=context_verifier,**kwargs)
    holds=MarketHoldStore(data['dsn'],policy.schema,context_store=contexts,
        scope_resolver=lambda *_:data['hold_scope'],signing_key=HOLD_KEY,**kwargs)
    candidates=MarketCandidateStore(data['dsn'],policy.schema,
        _MarketSources(sources,holds,principal_provider=provider),**kwargs)
    store=BreakEvenStore(data['dsn'],policy.schema,candidates,**kwargs)
    return BreakEvenCalculationWorker(jobs,store,tenant_id=data['principal']['tenant_id'])
''')
    factory.chmod(0o600)
    env = os.environ | {'PYTHONPATH': os.pathsep.join([str(tmp_path), str(Path(__file__).parent),
                                                     str(Path(__file__).parents[1])])}
    process = subprocess.run([sys.executable, '-m', 'app.break_even_work', '--factory',
        'break_even_operator:build', '--job-id', job_id], env=env, capture_output=True, text=True, timeout=300)
    assert process.returncode == 0, process.stderr
    outcome = json.loads(process.stdout)['result']
    assert outcome['state'] == 'succeeded' and outcome['plan_id'] and result_count(worker) == 1
    assert worker.store.get_break_even_read('tenant-1', outcome['plan_id'])[1].assessment_status == 'hold'
