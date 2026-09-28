"""HTTP submission uses actual immutable records; CLI captures/keys are synthetic."""

import asyncio
import json
from pathlib import Path
import sys
from uuid import UUID

import pytest
from psycopg import sql

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from app.api import create_app
from test_thermal_scenario_execution import (bound_execution, scenario_setup, simulation_setup,
    login_database, login_scope, application, run_count)
from test_api_job_status import get, UnusedMarketResultStore
from test_api_thermal_run import UnusedMarketHoldStore
from test_http_identity import request
from test_api_serve import tls_files

pytestmark = pytest.mark.parametrize('login_scope', [{'thermal_scenario_storage': True,
    'market_calculation': True, 'break_even_calculation': True}], indirect=True)


@pytest.fixture
def submission(bound_execution):
    from app.thermal_run_submission import ThermalRunSubmissionService
    _, store, runs, jobs, _, data, principal, publisher = bound_execution
    principal['scopes'].add('thermal_run_submit')
    service = ThermalRunSubmissionService(publisher, store)
    app = create_app(jobs, UnusedMarketHoldStore(), runs, UnusedMarketResultStore(),
        principal_provider=lambda: principal, thermal_scenario_store=store,
        thermal_run_submission_service=service)
    body = data | {'model_version': 'thermal-v1',
        'parameter_set_version': 'synthetic-thermal-parameters-v1', 'idempotency_key': 'http-run'}
    return app, body, service, bound_execution


def post(app, body, *, raw=None, media=b'application/json'):
    return asyncio.run(request(app, path='/v1/runs', method='POST',
        headers=[(b'content-type', media), (b'x-tenant-id', b'foreign-tenant')],
        body=json.dumps(body).encode() if raw is None else raw))[:2]


def submitted_count(jobs):
    with jobs.connect() as conn:
        return conn.execute(sql.SQL("SELECT count(*) AS n FROM {} WHERE idempotency_key='http-run'")
            .format(jobs._table('jobs'))).fetchone()['n']


def test_http_submission_worker_and_run_discovery_share_actual_input(submission):
    app, body, _, setup = submission
    worker, _, runs, jobs, _, data, _, _ = setup
    status, queued = post(app, body)
    assert status == 202 and queued['stage'] == 'simulation' and queued['state'] == 'queued'
    job_id = UUID(queued['job_id'])
    assert jobs.get_job('foreign-tenant', job_id) is None
    assert submitted_count(jobs) == 1 and run_count(runs) == 0
    assert post(app, body) == (202, queued)
    lease = jobs.get_job('tenant-a', job_id)
    with jobs.connect() as conn:
        raw = conn.execute(sql.SQL('SELECT input_bytes FROM {} WHERE job_id=%s')
            .format(jobs._table('jobs')), (job_id,)).fetchone()['input_bytes']
    assert json.loads(raw) == data and lease['attempt_count'] == 0
    result = worker.run_once(str(job_id))
    assert result.state == 'succeeded'
    assert get(app, f'/v1/jobs/{job_id}/run')[1]['run_id'] == result.run_id
    assert post(app, body)[1]['state'] == 'succeeded' and run_count(runs) == 1


@pytest.mark.parametrize('change', [{'coefficients': {'heat': 4}}, {'tenant_id': 'foreign'},
    {'model_version': 'invented'}, {'scenario_sha256': 'A'*64}])
def test_closed_request_rejected_without_job(submission, change):
    app, body, _, setup = submission
    assert post(app, body | change)[0] == 422
    assert submitted_count(setup[3]) == 0


@pytest.mark.parametrize('change', [{'scenario_id': 'missing'}, {'scenario_sha256': '0'*64},
    {'review_job_id': '00000000-0000-0000-0000-000000000000'}])
def test_unverified_binding_never_queues(submission, change):
    app, body, _, setup = submission
    assert post(app, body | change)[0] == 422
    assert submitted_count(setup[3]) == 0 and run_count(setup[2]) == 0


@pytest.mark.parametrize('scope', ['thermal_run_submit', 'metadata', 'artifact',
    'thermal_scenario_read', 'thermal_snapshot_read', 'decision_context_read', 'market_hold_context_read'])
def test_missing_admission_scope_denied(submission, scope):
    app, body, _, setup = submission
    setup[6]['scopes'].remove(scope)
    assert post(app, body)[0] == 403 and submitted_count(setup[3]) == 0


def test_scope_revoked_during_insert_rolls_back_job_and_event(submission, monkeypatch):
    app, body, _, setup = submission
    jobs, principal = setup[3], setup[6]
    original = jobs._event
    def revoke(*args, **kwargs):
        original(*args, **kwargs)
        principal['scopes'].remove('thermal_run_submit')
    monkeypatch.setattr(jobs, '_event', revoke)
    assert post(app, body)[0] == 403 and submitted_count(jobs) == 0


def test_store_rebinding_during_insert_rolls_back_job(submission, monkeypatch):
    from app.job_store import JobStore
    app, body, service, setup = submission
    jobs = setup[3]
    other = JobStore(jobs._dsn, jobs.schema, jobs.artifact_root,
        runtime_identity=jobs.runtime_identity, principal_provider=jobs.principal_provider,
        audit_runtime_grants=True)
    original = jobs._event
    def rebind(*args, **kwargs):
        original(*args, **kwargs)
        service.jobs = other
    monkeypatch.setattr(jobs, '_event', rebind)
    assert post(app, body)[0] == 503 and submitted_count(jobs) == 0


def test_changed_intent_conflicts_and_private_failures_are_fixed(submission, monkeypatch):
    app, body, _, setup = submission
    assert post(app, body)[0] == 202
    store, publisher = setup[1], setup[7]
    original = store.get('tenant-a', body['scenario_id'], body['scenario_revision'])['scenario']
    newer = store.put('tenant-a', original.model_dump(mode='json') | {'scenario_revision': 'r2'})
    changed = body | {'scenario_revision': 'r2', 'scenario_sha256': newer['scenario_sha256']}
    assert post(app, changed)[0] == 409 and submitted_count(setup[3]) == 1
    def fail(*_):
        raise RuntimeError('private credential and raw provider data')
    monkeypatch.setattr(publisher, 'validate_submission', fail)
    status, result = post(app, body)
    assert status == 503 and 'private' not in json.dumps(result)


@pytest.mark.parametrize('raw,media,status', [(b'{}', b'text/plain', 415),
    (b' '*4097, b'application/json', 413), (b'{"x":1,"x":2}', b'application/json', 422),
    (b'{"x":NaN}', b'application/json', 422), (b'\xff', b'application/json', 422)])
def test_transport_failures_do_not_queue(submission, raw, media, status):
    app, body, _, setup = submission
    assert post(app, body, raw=raw, media=media)[0] == status
    assert submitted_count(setup[3]) == 0


def test_unconfigured_submission_is_fixed_unavailable(bound_execution):
    bound_execution[6]['scopes'].add('thermal_run_submit')
    assert post(application(bound_execution), {}) == (503,
        {'error': {'code': 'simulation_unavailable', 'message': 'Simulation submission unavailable'}})


@pytest.mark.parametrize('fault', ['release', 'execution'])
def test_independent_release_and_execution_are_required_before_queue(submission, fault):
    app, body, _, setup = submission
    publisher = setup[7]
    if fault == 'release':
        publisher.release_resolver = lambda *_: None
    else:
        publisher.execution_verifier = lambda *_: False
    assert post(app, body)[0] == 422 and submitted_count(setup[3]) == 0


def test_admission_checks_evidence_without_calculating_or_publishing(submission, monkeypatch):
    import app.thermal_publisher as module
    app, body, _, setup = submission
    def forbid(*_, **__):
        raise AssertionError('admission calculated or published')
    monkeypatch.setattr(module, 'calculate_fixture', forbid)
    monkeypatch.setattr(setup[2], 'publish_verified', forbid)
    assert post(app, body)[0] == 202 and run_count(setup[2]) == 0


def test_fresh_runtime_bearer_submission_uses_bound_stores_and_worker(submission, tls_files):
    from datetime import datetime, timezone, timedelta
    from app.api_runtime import ApiRuntime
    from app.http_identity import BearerRegistry, BearerGrant, current_principal, token_digest
    from app.thermal_publisher import ThermalG1Publisher
    from app.thermal_run_submission import SUBMISSION_SCOPES
    from test_api_runtime import config, dependencies
    _, body, _, setup = submission
    worker, store, runs, jobs, _, _, _, publisher = setup
    token = b'synthetic-submission-bearer-'+b't'*32
    now = datetime.now(timezone.utc)
    scopes = frozenset(SUBMISSION_SCOPES + ('thermal_run_read',))
    registry = BearerRegistry((BearerGrant(token_digest(token), 'tenant-a', scopes,
        now-timedelta(seconds=1), now+timedelta(minutes=5)),))
    calls = []
    def factory(*, run_store, job_store):
        calls.append((run_store, job_store))
        return ThermalG1Publisher(run_store, job_store, publisher.release_resolver,
            root=publisher.root, gate_key=publisher._gate_key,
            release_verifier=publisher.release_verifier, execution_verifier=publisher.execution_verifier)
    cert, key, _ = tls_files
    runtime = ApiRuntime(config(policy=jobs.runtime_identity[0], dsn=jobs._dsn,
        artifact_root=jobs.artifact_root, certificate=cert, private_key=key,
        thermal_gate_key=runs._gate_key, market_hold_key=store.holds._key),
        dependencies(bearer_registry=registry, context_verifier=runs._context_verifier,
            release_verifier=runs._release_verifier, market_scope_resolver=store.holds._scope_resolver,
            thermal_publisher_factory=factory))
    assert calls == [(runtime.thermal, runtime.jobs)]
    status, queued, headers = asyncio.run(request(runtime.service.app, path='/v1/runs', method='POST',
        body=json.dumps(body).encode(), headers=[(b'authorization', b'Bearer '+token),
            (b'content-type', b'application/json'), (b'x-tenant-id', b'foreign-tenant')]))
    assert status == 202 and headers[b'cache-control'] == b'no-store' and current_principal() is None
    result = worker.run_once(queued['job_id'])
    assert result.state == 'succeeded'
    status, summary, _ = asyncio.run(request(runtime.service.app,
        path=f"/v1/jobs/{queued['job_id']}/run", headers=[(b'authorization', b'Bearer '+token)]))
    assert status == 200 and summary['run_id'] == result.run_id and current_principal() is None
