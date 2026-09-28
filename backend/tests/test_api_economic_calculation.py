"""HTTP to real fenced arithmetic and replay; synthetic records/keys only."""

import asyncio
from hashlib import sha256
from copy import deepcopy
import json
from pathlib import Path
import sys

import pytest
from psycopg import sql

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from app.api import create_app
from app.jobs import canonical_input_bytes
from test_economic_calculation_worker import (calculation_setup, economic_api,
    login_database, login_scope, PROFILE, result_count)
from test_http_identity import request

pytestmark = pytest.mark.parametrize('login_scope', [PROFILE], indirect=True)


@pytest.fixture
def calculation_api(calculation_setup):
    from app.api_economic_calculation import EconomicCalculationService
    worker, jobs, results, _, data, principal = calculation_setup
    service = EconomicCalculationService(jobs, results)
    view = results._candidates._source
    app = create_app(jobs, view._holds, view._holds._context_store, results,
        principal_provider=jobs.principal_provider, economic_calculation_service=service)
    return app, service, worker, data | {'idempotency_key': 'http-calculation'}, principal


def post(app, body, *, raw=None, media=b'application/json'):
    return asyncio.run(request(app, path='/v1/economic-results', method='POST',
        headers=[(b'content-type', media), (b'x-tenant-id', b'foreign')],
        body=json.dumps(body).encode() if raw is None else raw))[:2]


def get(app, job_id):
    return asyncio.run(request(app, path=f'/v1/jobs/{job_id}/economic-result'))[:2]


def counts(service):
    with service.jobs.connect() as conn:
        return tuple(conn.execute(sql.SQL('SELECT count(*) AS n FROM {}')
            .format(service.jobs._table(name))).fetchone()['n']
            for name in ('jobs', 'job_publications', 'market_result_records'))


def test_admission_worker_completion_and_read_are_connected(calculation_api):
    app, service, worker, body, principal = calculation_api
    before = counts(service)
    status, accepted = post(app, body)
    assert status == 202 and accepted['state'] == 'queued' and accepted['attempt_count'] == 0
    assert counts(service) == (before[0]+1, before[1], before[2])
    assert post(app, body) == (202, accepted)
    job_id = accepted['job_id']
    assert get(app, job_id)[0] == 404
    outcome = worker.run_once(job_id)
    assert outcome.state == 'succeeded'
    assert post(app, body)[1]['state'] == 'succeeded'
    principal['scopes'].difference_update({'simulation_execute', 'market_result_write', 'market_candidate_write'})
    status, result = get(app, job_id)
    assert status == 200 and result['economic_result_id'] == outcome.economic_result_id
    assert result['assessment_status'] == 'hold' and result['input_origin'] == 'user'
    assert result['evidence_level'] == 'assumed'
    direct = asyncio.run(request(app, path='/v1/economic-results/'+outcome.economic_result_id))
    assert direct[0:2] == (status, result)
    assert 'tenant_id' not in result and 'receipt_version' not in result and 'candidate_id' not in result
    principal['tenant_id'] = 'tenant-2'
    assert get(app, job_id)[0] == 404
    principal['authenticated'] = False
    assert get(app, job_id)[0] == 401


def test_invalid_requests_and_scope_denial_create_nothing(calculation_api):
    from app.economic_calculation_worker import CALCULATION_SCOPES
    app, service, _, body, principal = calculation_api
    before = counts(service)
    for scope in CALCULATION_SCOPES:
        principal['scopes'].remove(scope)
        assert post(app, body)[0] == 403
        principal['scopes'].add(scope)
    for changes in ({'tenant_id': 'foreign'}, {'formula_version': 'other'},
            {'input_version': 'other'}, {'scenario_id': 1}, {'candidate_id': 'a'*64},
            {'scenario_sha256': 'b'*64}, {'idempotency_key': ''}, {'idempotency_key': '한글'}):
        assert post(app, body | changes)[0] == 422
    assert post(app, body, raw=b' '*4097)[0] == 413
    assert post(app, body, media=b'text/plain')[0] == 415
    assert counts(service) == before
    view = service.results._candidates._source
    unconfigured = create_app(service.jobs, view._holds, view._holds._context_store,
        service.results, principal_provider=service.jobs.principal_provider)
    assert post(unconfigured, body)[0] == 503
    assert get(unconfigured, '00000000-0000-4000-8000-000000000001')[0] == 503


def test_conflicting_existing_intent_is_not_replaced(calculation_api):
    app, service, _, body, _ = calculation_api
    key = 'economic-calculation-v1:'+sha256(body['idempotency_key'].encode('ascii')).hexdigest()
    service.jobs.submit('tenant-1', 'simulation', {'input_version': 'other'}, key)
    before = counts(service)
    assert post(app, body)[0] == 409 and counts(service) == before


@pytest.mark.parametrize('fault,status', [('scope', 403), ('rebind', 503), ('private', 503)])
def test_admission_commit_failure_rolls_back(calculation_api, monkeypatch, fault, status):
    from app.market_source_store import MarketSourceStore
    app, service, _, body, principal = calculation_api
    before = counts(service)
    original = service.jobs._event
    def change(*args, **kwargs):
        original(*args, **kwargs)
        if fault == 'scope': principal['scopes'].remove('simulation_execute')
        if fault == 'rebind':
            view = service.results._candidates._source
            old = view._source
            view._source = MarketSourceStore(old.dsn, old.schema,
                principal_provider=old._principal_provider, runtime_identity=old.runtime_identity)
        if fault == 'private': raise RuntimeError('private server detail')
    monkeypatch.setattr(service.jobs, '_event', change)
    code, response = post(app, body)
    assert code == status and 'private' not in str(response) and counts(service) == before


def test_completed_receipt_and_publication_must_match_actual_records(calculation_api, monkeypatch):
    app, service, worker, body, _ = calculation_api
    status, accepted = post(app, body)
    assert status == 202 and worker.run_once(accepted['job_id']).state == 'succeeded'
    from uuid import UUID
    job_id = UUID(accepted['job_id'])
    receipt = json.loads(service.jobs.read_artifact('tenant-1', job_id))
    publication = service.jobs.get_publication('tenant-1', job_id)
    for field, value in [('candidate_id', 'a'*64), ('result_sha256', 'b'*64),
            ('assessment_status', 'pass'), ('code_sha256', 'invalid'), ('extra', 'private')]:
        raw = canonical_input_bytes(receipt | {field: value})
        changed = deepcopy(publication)
        changed.update(artifact_size=len(raw), artifact_sha256=sha256(raw).hexdigest())
        changed['manifest']['artifact_sha256'] = sha256(raw).hexdigest()
        monkeypatch.setattr(service.jobs, 'read_artifact', lambda *_: raw)
        monkeypatch.setattr(service.jobs, 'get_publication', lambda *_: changed)
        status, response = get(app, accepted['job_id'])
        assert status == 503 and 'private' not in str(response)
    raw = canonical_input_bytes(receipt)
    for field, value in [('attempt', 999), ('artifact_sha256', 'f'*64),
            ('decision_id', 'forged'), ('manifest', {})]:
        changed = publication | {field: value}
        assert get(app, accepted['job_id'])[0] == 503
    changed = publication
    assert get(app, accepted['job_id'])[0] == 200


def test_read_rechecks_revocation_after_replay(calculation_api, monkeypatch):
    from app.api_economic_calculation import ECONOMIC_JOB_READ_SCOPES
    app, service, worker, body, principal = calculation_api
    _, accepted = post(app, body)
    assert worker.run_once(accepted['job_id']).state == 'succeeded'
    for scope in ECONOMIC_JOB_READ_SCOPES:
        principal['scopes'].remove(scope)
        assert get(app, accepted['job_id'])[0] == 403
        principal['scopes'].add(scope)
    original = service.results.get_market_result
    def revoke(*args):
        result = original(*args)
        principal['scopes'].remove('market_source_read')
        return result
    monkeypatch.setattr(service.results, 'get_market_result', revoke)
    assert get(app, accepted['job_id'])[0] == 403
    principal['scopes'].add('market_source_read')
    from app.market_source_store import MarketSourceStore
    view = service.results._candidates._source
    old = view._source
    def rebind(*args):
        result = original(*args)
        view._source = MarketSourceStore(old.dsn, old.schema,
            principal_provider=old._principal_provider, runtime_identity=old.runtime_identity)
        return result
    monkeypatch.setattr(service.results, 'get_market_result', rebind)
    assert get(app, accepted['job_id'])[0] == 503
