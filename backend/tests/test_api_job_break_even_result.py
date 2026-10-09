"""Actual completed plans and authenticated safe projections; synthetic records."""

import asyncio
from copy import deepcopy
from hashlib import sha256
import json
from pathlib import Path
import sys
from urllib.parse import urlencode
from uuid import UUID, uuid4

import pytest
from psycopg import sql

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from app.api import create_app
from app.api_job_break_even_result import BreakEvenJobResultService, BREAK_EVEN_JOB_READ_SCOPES
from app.jobs import canonical_input_bytes
from test_break_even_calculation_worker import calculation_setup
from test_api_break_even_plan import plan_api, login_database, login_scope, PROFILE
from test_api_job_status import UnusedMarketResultStore
from test_http_identity import request
from test_api_serve import tls_files

pytestmark = pytest.mark.parametrize('login_scope', [{**PROFILE, 'break_even_calculation': True}], indirect=True)


@pytest.fixture
def result_api(calculation_setup):
    worker, job_id, principal = calculation_setup
    service = BreakEvenJobResultService(worker.jobs, worker.store)
    view = worker.store._source._source
    app = create_app(worker.jobs, view._holds, view._holds._context_store, UnusedMarketResultStore(),
        principal_provider=worker.jobs.principal_provider, break_even_store=worker.store,
        break_even_job_result_service=service)
    return app, service, worker, job_id, principal


def get(app, job_id):
    return asyncio.run(request(app, path=f'/v1/jobs/{job_id}/break-even-result'))[:2]


def complete(worker, job_id):
    outcome = worker.run_once(job_id)
    assert outcome.state == 'succeeded' and outcome.plan_id
    return outcome


def test_queued_completion_read_only_scopes_and_safe_projection(result_api):
    app, service, worker, job_id, principal = result_api
    assert get(app, job_id)[0] == 404 and get(app, 'invalid')[0] == 422
    assert get(app, str(uuid4()))[0] == 404
    other = worker.jobs.submit('tenant-1', 'simulation', {'input_version': 'other'}, 'other-model')
    assert get(app, str(other['job_id']))[0] == 404
    outcome = complete(worker, job_id)
    principal['scopes'].difference_update({'simulation_execute', 'break_even_write', 'market_candidate_write'})
    status, value = get(app, job_id)
    assert status == 200 and value['plan_id'] == outcome.plan_id
    assert value['status'] == 'bracket_only' and value['assessment_status'] == 'hold'
    assert value['input_origin'] == 'user' and value['evidence_level'] == 'assumed'
    assert value['scope'] == 'conditional_user_grid_only'
    direct = asyncio.run(request(app, path='/v1/break-even-results',
        query=urlencode({'plan_id': outcome.plan_id}).encode()))[:2]
    assert direct == (status, value)
    assert not {'tenant_id', 'receipt_version', 'plan_sha256', 'result_sha256', 'decision_id'} & value.keys()
    principal['tenant_id'] = 'tenant-2'
    assert get(app, job_id)[0] == 404
    principal['authenticated'] = False
    assert get(app, job_id)[0] == 401


def test_completed_receipt_publication_and_plan_must_match(result_api, monkeypatch):
    app, service, worker, job_id, _ = result_api
    outcome = complete(worker, job_id)
    identity = UUID(job_id)
    receipt = json.loads(worker.jobs.read_artifact('tenant-1', identity))
    publication = worker.jobs.get_publication('tenant-1', identity)
    for field, value in [('plan_id', 'wrong'), ('request_sha256', 'a'*64),
            ('plan_sha256', 'b'*64), ('result_sha256', 'c'*64), ('assessment_status', 'pass'),
            ('code_sha256', 'invalid'), ('extra', 'private')]:
        raw = canonical_input_bytes(receipt | {field: value})
        changed = deepcopy(publication)
        changed.update(artifact_size=len(raw), artifact_sha256=sha256(raw).hexdigest())
        changed['manifest']['artifact_sha256'] = sha256(raw).hexdigest()
        monkeypatch.setattr(worker.jobs, 'read_artifact', lambda *_: raw)
        monkeypatch.setattr(worker.jobs, 'get_publication', lambda *_: changed)
        status, value = get(app, job_id)
        assert status == 503 and 'private' not in str(value)
    raw = canonical_input_bytes(receipt)
    for field, value in [('attempt', 999), ('artifact_sha256', 'f'*64),
            ('decision_id', 'forged'), ('manifest', {}), ('artifact_size', 4097)]:
        changed = publication | {field: value}
        assert get(app, job_id)[0] == 503
    changed = publication
    with monkeypatch.context() as patch:
        patch.setattr(worker.jobs, 'get_publication', lambda *_: None)
        assert get(app, job_id)[0] == 503
    original = service.store.get_break_even_plan
    monkeypatch.setattr(service.store, 'get_break_even_plan',
        lambda *_: original(outcome.plan_id) | {'fixed_inputs_sha256': 'd'*64})
    assert get(app, job_id)[0] == 503
    monkeypatch.setattr(service.store, 'get_break_even_plan', original)
    with monkeypatch.context() as patch:
        patch.setattr(service.store, 'get_break_even_read', lambda *_: None)
        assert get(app, job_id)[0] == 503


def test_scopes_and_binding_are_rechecked_after_replay(result_api, monkeypatch):
    from app.market_source_store import MarketSourceStore
    app, service, worker, job_id, principal = result_api
    complete(worker, job_id)
    for scope in BREAK_EVEN_JOB_READ_SCOPES:
        principal['scopes'].remove(scope)
        assert get(app, job_id)[0] == 403
        principal['scopes'].add(scope)
    original = service.store.get_break_even_read
    def revoke(*args):
        result = original(*args)
        principal['scopes'].remove('market_source_read')
        return result
    monkeypatch.setattr(service.store, 'get_break_even_read', revoke)
    assert get(app, job_id)[0] == 403
    principal['scopes'].add('market_source_read')
    def private_failure(*_):
        principal['scopes'].remove('market_source_read')
        raise RuntimeError('private source detail')
    monkeypatch.setattr(service.store, 'get_break_even_read', private_failure)
    assert get(app, job_id)[0] == 403
    principal['scopes'].add('market_source_read')
    view, old = service.store._source._source, service.store._source._source._source
    def rebind(*args):
        result = original(*args)
        view._source = MarketSourceStore(old.dsn, old.schema,
            principal_provider=old._principal_provider, runtime_identity=old.runtime_identity)
        return result
    monkeypatch.setattr(service.store, 'get_break_even_read', rebind)
    status, value = get(app, job_id)
    assert status == 503 and 'private' not in str(value)


def test_unconfigured_service_and_other_completed_models_withhold_result(result_api):
    configured, service, worker, job_id, _ = result_api
    view = service.store._source._source
    app = create_app(worker.jobs, view._holds, view._holds._context_store, UnusedMarketResultStore(),
        principal_provider=worker.jobs.principal_provider, break_even_store=worker.store)
    assert get(app, job_id)[0] == 503
    for stage, version in [('simulation', 'other'), ('collection', 'break-even-calculation-input-v1')]:
        job = worker.jobs.submit('tenant-1', stage, {'input_version': version}, 'other-'+stage)
        lease = worker.jobs.claim(300, tenant_id='tenant-1', allowed_stages=(stage,), job_id=str(job['job_id']))
        digest = sha256(b'{}').hexdigest()
        assert worker.jobs.publish('tenant-1', job['job_id'], lease['attempt'], lease['lease_token'],
            None, b'{}', digest, {'schema_version': '1'})
        assert get(configured, str(job['job_id']))[0] == 404


def test_fresh_bearer_runtime_read_and_grant_drift(result_api, tls_files, login_scope):
    from datetime import datetime, timezone, timedelta
    from app.api_runtime import ApiRuntime
    from app.http_identity import BearerRegistry, BearerGrant, token_digest, current_principal
    from app.market_source_store import MarketSourceStore
    from test_api_runtime import config, dependencies
    _, service, worker, job_id, _ = result_api
    complete(worker, job_id)
    jobs = worker.jobs
    token = b'synthetic-break-even-read-token-'+b'r'*32
    now = datetime.now(timezone.utc)
    registry = BearerRegistry((BearerGrant(token_digest(token), 'tenant-1', frozenset(BREAK_EVEN_JOB_READ_SCOPES),
        now-timedelta(seconds=1), now+timedelta(minutes=30)),))
    cert, key, _ = tls_files
    factory = lambda *, principal_provider: MarketSourceStore(jobs._dsn, jobs.schema,
        principal_provider=principal_provider, runtime_identity=jobs.runtime_identity)
    runtime = ApiRuntime(config(policy=jobs.runtime_identity[0], dsn=jobs._dsn,
        artifact_root=jobs.artifact_root, certificate=cert, private_key=key),
        dependencies(bearer_registry=registry, market_source_factory=factory,
            market_scope_resolver=service.store._source._source._holds._scope_resolver))
    path = '/v1/jobs/'+job_id+'/break-even-result'
    def call():
        return asyncio.run(request(runtime.service.app, path=path,
            headers=[(b'authorization', b'Bearer '+token), (b'x-tenant-id', b'foreign')]))
    status, result, headers = call()
    assert status == 200 and result['assessment_status'] == 'hold'
    assert headers[b'cache-control'] == b'no-store' and current_principal() is None
    assert asyncio.run(request(runtime.service.app, path=path))[0] == 401
    base, policy, _ = login_scope
    with base.connect() as conn:
        conn.execute(sql.SQL('GRANT SELECT ON {}.jobs TO {}')
            .format(sql.Identifier(policy.schema), sql.Identifier(policy.roles['worker'])))
    assert call()[0] == 503
