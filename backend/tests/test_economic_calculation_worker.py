"""Real SCRAM and fenced publication; all source records/keys are synthetic."""

import json
import os
from pathlib import Path
import sys

import pytest
from psycopg import sql

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from app.economics import FORMULA_VERSION
from app.market_result_store import MarketResultStore
from test_api_economic_scenario import economic_api, post, login_database, login_scope, PROFILE

pytestmark = pytest.mark.parametrize('login_scope', [PROFILE], indirect=True)


@pytest.fixture
def calculation_setup(economic_api):
    from app.economic_calculation_worker import EconomicCalculationWorker
    app, jobs, candidates, principal, _, request = economic_api
    status, scenario = post(app, {'request': request, 'idempotency_key': 'worker-scenario'})
    assert status == 200
    principal['scopes'].update({'artifact', 'simulation_execute', 'market_result_write', 'cancel'})
    results = MarketResultStore(jobs._dsn, jobs.schema, candidates,
        runtime_identity=jobs.runtime_identity, principal_provider=jobs.principal_provider)
    data = {'input_version': 'economic-calculation-input-v1', 'scenario_id': scenario['scenario_id'],
        'scenario_revision': scenario['scenario_revision'], 'scenario_sha256': scenario['scenario_sha256'],
        'candidate_id': scenario['candidate_id'], 'formula_version': FORMULA_VERSION}
    job = jobs.submit('tenant-1', 'simulation', data, 'economic-calculation')
    os.close(jobs._content_directory(create=True))
    worker = EconomicCalculationWorker(jobs, results, tenant_id='tenant-1')
    return worker, jobs, results, job, data, principal


def result_count(results):
    with results.connect() as conn:
        return conn.execute(sql.SQL('SELECT count(*) AS n FROM {}')
            .format(results._table('market_result_records'))).fetchone()['n']


def test_calculation_and_completion_commit_together_and_replay(calculation_setup):
    worker, jobs, results, job, data, _ = calculation_setup
    outcome = worker.run_once(str(job['job_id']))
    assert outcome.state == 'succeeded' and outcome.economic_result_id
    assert jobs.get_job('tenant-1', job['job_id'])['state'] == 'succeeded'
    receipt = json.loads(jobs.read_artifact('tenant-1', job['job_id']))
    stored = results.get_market_result(data['scenario_id'], data['scenario_revision'])
    assert receipt['economic_result_id'] == stored.economic_result.result_id == outcome.economic_result_id
    assert receipt['assessment_status'] == stored.assessment_status == 'hold'
    assert receipt['claim_scope'] == 'user_assumption_arithmetic_only'
    assert jobs.get_publication('tenant-1', job['job_id'])['decision_id'] is None
    assert jobs.list_decisions('tenant-1', job['job_id']) == []
    assert len(jobs.list_attempt_outcomes('tenant-1', job['job_id'])) == 1
    assert worker.run_once(str(job['job_id'])) is None and result_count(results) == 1


def test_other_model_stage_tenant_and_canceled_jobs_are_not_claimed(calculation_setup):
    worker, jobs, results, job, data, _ = calculation_setup
    neighbors = [jobs.submit('tenant-1', 'simulation', {'input_version': 'thermal-simulation-input-v1'}, 'other-model'),
        jobs.submit('tenant-1', 'collection', data, 'other-stage'),
        jobs.submit('tenant-2', 'simulation', data, 'other-tenant')]
    assert jobs.cancel('tenant-1', job['job_id'])
    for target in [job, *neighbors]:
        assert worker.run_once(str(target['job_id'])) is None
    for neighbor in neighbors:
        tenant = 'tenant-2' if neighbor is neighbors[-1] else 'tenant-1'
        with jobs.connect() as conn:
            row = jobs._locked_job(conn, tenant, neighbor['job_id'])
        assert row['state'] == 'queued' and row['attempt_count'] == 0
    assert result_count(results) == 0


@pytest.mark.parametrize('scope', ['simulation_execute', 'market_result_write', 'decision_context_read'])
def test_missing_execution_scope_does_not_claim(calculation_setup, scope):
    worker, jobs, results, job, _, principal = calculation_setup
    principal['scopes'].remove(scope)
    with pytest.raises(PermissionError, match='economic calculation denied'):
        worker.run_once(str(job['job_id']))
    assert jobs.get_job('tenant-1', job['job_id'])['attempt_count'] == 0
    assert result_count(results) == 0


@pytest.mark.parametrize('field,state', [('scenario_sha256', 'hold'), ('candidate_id', 'hold'), ('formula_version', 'failed')])
def test_wrong_pins_or_formula_cannot_publish(calculation_setup, field, state):
    worker, jobs, results, _, data, _ = calculation_setup
    bad = jobs.submit('tenant-1', 'simulation', {**data, field: 'a'*64}, 'wrong-'+field)
    outcome = worker.run_once(str(bad['job_id']))
    assert outcome.state == state and outcome.economic_result_id is None
    assert jobs.get_publication('tenant-1', bad['job_id']) is None and result_count(results) == 0


@pytest.mark.parametrize('fault,state', [('scope', 'hold'), ('code', 'queued'), ('source', 'queued'), ('publication', 'queued')])
def test_post_insert_failure_rolls_back_result_and_completion(calculation_setup, monkeypatch, fault, state):
    worker, jobs, results, job, _, principal = calculation_setup
    if fault == 'publication':
        def fail(*_, **__): raise RuntimeError('private publication detail')
        monkeypatch.setattr(jobs, '_insert_publication', fail)
    else:
        original = results._checked
        def change(*args):
            value = original(*args)
            if fault == 'scope': principal['scopes'].remove('market_result_write')
            if fault == 'code': monkeypatch.setattr(worker, '_digests', lambda: ('f'*64, 'e'*64))
            if fault == 'source':
                from app.market_source_store import MarketSourceStore
                view = results._candidates._source
                old = view._source
                view._source = MarketSourceStore(old.dsn, old.schema,
                    principal_provider=old._principal_provider, runtime_identity=old.runtime_identity)
            return value
        monkeypatch.setattr(results, '_checked', change)
    outcome = worker.run_once(str(job['job_id']))
    assert outcome.state == state and 'private' not in outcome.reason_code
    assert outcome.economic_result_id is None and result_count(results) == 0
    assert jobs.get_publication('tenant-1', job['job_id']) is None
    assert jobs.get_job('tenant-1', job['job_id'])['state'] == state


def test_cancel_before_commit_is_acknowledged_without_result(calculation_setup, monkeypatch):
    worker, jobs, results, job, _, _ = calculation_setup
    original = worker._calculate
    def cancel(*args):
        value = original(*args)
        assert jobs.cancel('tenant-1', job['job_id'])
        return value
    monkeypatch.setattr(worker, '_calculate', cancel)
    assert worker.run_once(str(job['job_id'])).state == 'canceled'
    assert result_count(results) == 0 and jobs.get_publication('tenant-1', job['job_id']) is None


def test_expired_calculation_is_recovered_by_new_attempt(calculation_setup, monkeypatch):
    worker, jobs, results, job, _, _ = calculation_setup
    original = worker._calculate
    calls = []
    def expire(*args):
        value = original(*args)
        calls.append(True)
        if len(calls) == 1:
            with jobs.connect() as conn:
                conn.execute(sql.SQL("UPDATE {} SET lease_until=clock_timestamp()-interval '1 second' WHERE job_id=%s")
                    .format(jobs._table('jobs')), (job['job_id'],))
        return value
    monkeypatch.setattr(worker, '_calculate', expire)
    assert worker.run_once(str(job['job_id'])).state == 'unclosed'
    assert result_count(results) == 0 and jobs.get_publication('tenant-1', job['job_id']) is None
    recovered = worker.run_once(str(job['job_id']))
    assert recovered.state == 'succeeded' and recovered.attempt == 2 and result_count(results) == 1
    outcomes = jobs.list_attempt_outcomes('tenant-1', job['job_id'])
    assert [row['state'] for row in outcomes] == ['lease_expired', 'succeeded']


def test_real_foreground_process_publishes_scoped_result(calculation_setup, tmp_path):
    from dataclasses import asdict
    import subprocess
    worker, jobs, results, job, _, principal = calculation_setup
    document = {'dsn': jobs._dsn, 'policy': asdict(jobs.runtime_identity[0]),
        'artifact_root': str(jobs.artifact_root), 'principal': principal | {'scopes': sorted(principal['scopes'])},
        'hold_scope': results._candidates._source._holds._scope_resolver()}
    config = tmp_path/'economic-operator.json'
    config.write_text(json.dumps(document))
    config.chmod(0o600)
    factory = tmp_path/'economic_operator.py'
    factory.write_text('''import json
from pathlib import Path
from app.runtime_roles import RuntimeLoginPolicy
from app.job_store import JobStore
from app.market_source_store import MarketSourceStore
from app.market_candidate_store import MarketCandidateStore
from app.market_result_store import MarketResultStore
from app.market_hold_store import MarketHoldStore
from app.thermal_run_store import ThermalRunStore
from app.api_market_source import _MarketSources
from app.economic_calculation_worker import EconomicCalculationWorker
from test_market_hold_store import context_verifier, HOLD_KEY
def build():
    data = json.loads(Path(__file__).with_name('economic-operator.json').read_text())
    policy = RuntimeLoginPolicy(**data['policy'])
    binding = (policy, 'authority')
    provider = lambda: data['principal']
    kwargs = dict(runtime_identity=binding, principal_provider=provider)
    jobs = JobStore(data['dsn'], policy.schema, Path(data['artifact_root']), audit_runtime_grants=True, **kwargs)
    sources = MarketSourceStore(data['dsn'], policy.schema, **kwargs)
    contexts = ThermalRunStore(data['dsn'], policy.schema, gate_key=b'synthetic-gate-key-32-bytes-long!',
        release_verifier=lambda *_: None, context_verifier=context_verifier, **kwargs)
    holds = MarketHoldStore(data['dsn'], policy.schema, context_store=contexts,
        scope_resolver=lambda *_: data['hold_scope'], signing_key=HOLD_KEY, **kwargs)
    candidates = MarketCandidateStore(data['dsn'], policy.schema,
        _MarketSources(sources, holds, principal_provider=provider), **kwargs)
    results = MarketResultStore(data['dsn'], policy.schema, candidates, **kwargs)
    return EconomicCalculationWorker(jobs, results, tenant_id=data['principal']['tenant_id'])
''')
    factory.chmod(0o600)
    env = os.environ | {'PYTHONPATH': os.pathsep.join([str(tmp_path), str(Path(__file__).parent),
                                                     str(Path(__file__).parents[1])])}
    process = subprocess.run([sys.executable, '-m', 'app.economic_work', '--factory',
        'economic_operator:build', '--job-id', str(job['job_id'])], env=env,
        capture_output=True, text=True, timeout=180)
    assert process.returncode == 0, process.stderr
    outcome = json.loads(process.stdout)['result']
    assert outcome['state'] == 'succeeded' and result_count(results) == 1
    assert results.get_economic_result('tenant-1', outcome['economic_result_id']).assessment_status == 'hold'
