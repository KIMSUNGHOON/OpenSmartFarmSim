"""Authenticated leaf-population HTTP transport controls; stubs are not DB/TLS proof."""
import asyncio
from copy import deepcopy
from datetime import datetime, timedelta, timezone
import importlib
import json
from types import SimpleNamespace

from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from starlette.responses import JSONResponse
import pytest

from app import crop_leaf_population_execution as execution
from app import crop_leaf_population_execution_query as queries
from app.http_identity import BearerGrant, BearerRegistry, PrincipalMiddleware, current_principal, token_digest

TOKEN = b'owned-leaf-population-HTTP-control-'+b'a'*32
NOW = datetime(2026, 10, 23, 4, tzinfo=timezone.utc)
JOB = '11111111-1111-4111-8111-111111111111'
POST = '/v1/crop-leaf-population-executions'
PATH = '/v1/jobs/'+JOB+'/crop-leaf-population-execution'
BODY = {'study_id': 'study', 'revision': 'r1',
    'parent': {'job_id': '22222222-2222-4222-8222-222222222222', 'result_sha256': 'c'*64, 'numerical_root_sha256': 'd'*64}, 'farm': {'scenario_id': 'farm', 'scenario_revision': 'r1',
    'registration_sha256': 'a'*64, 'crop_id': 'crop-1'}, 'input': {'schema_version': execution.signed.farms.evidence.SOURCE_VERSION,
    'program_id': 'program', **{k: 'b'*64 for k in ('program_sha256', 'source_sha256', 'evidence_sha256')}},
    'rights': {'schema_version': execution.signed.farms.RIGHTS_VERSION, 'declaration_id': 'owned', 'revision': 'r1',
        'input_source_sha256': 'b'*64, 'available_at': '2026-10-21T18:49:47.384461Z', 'redistribute': False,
        **{k: True for k in ('ownership_asserted', 'access', 'store', 'transform', 'use', 'display')}}}


def error(status, code, message):
    return JSONResponse({'error': {'code': code, 'message': message}}, status_code=status, headers={'Cache-Control': 'no-store'})


def access(scopes):
    return {'security': [{'bearerAuth': []}], 'x-ossf-required-scopes': list(scopes)}


async def request(app, *, path=PATH, method='GET', body=b'', query=b'', headers=None, disconnect=False, send_failure=False):
    sent = []; received = False
    async def receive():
        nonlocal received
        if disconnect: return {'type': 'http.disconnect'}
        if not received:
            received = True; return {'type': 'http.request', 'body': body, 'more_body': False}
        return {'type': 'http.disconnect'}
    async def send(value):
        if send_failure and value['type'] == 'http.response.body': raise ConnectionError('owned transport failure')
        sent.append(value)
    await app({'type': 'http', 'asgi': {'version': '3.0'}, 'method': method, 'path': path, 'raw_path': path.encode(),
        'root_path': '', 'query_string': query, 'headers': headers if headers is not None else [(b'authorization', b'Bearer '+TOKEN)],
        'scheme': 'https', 'http_version': '1.1', 'server': ('test', 443), 'client': ('test', 1234)}, receive, send)
    start = next(v for v in sent if v['type'] == 'http.response.start')
    return start['status'], json.loads(b''.join(v.get('body', b'') for v in sent if v['type'] == 'http.response.body')), dict(start['headers'])


def authorized(*scopes):
    p = current_principal()
    if p is None: return None, error(401, 'unauthenticated', 'Authentication required')
    if not set(scopes) <= p['scopes']: return None, error(403, 'forbidden', 'Resource access denied')
    return p['tenant_id'], None


def protect(app, scopes, clock=lambda: NOW):
    grant = BearerGrant(token_digest(TOKEN), 'tenant-1', frozenset(scopes), NOW, NOW+timedelta(hours=1))
    return PrincipalMiddleware(app, BearerRegistry((grant,), clock=clock))


@pytest.fixture
def route(): return importlib.import_module('app.api_crop_leaf_population_execution')


def assembly(route, monkeypatch, *, scopes=None):
    jobs = SimpleNamespace(principal_provider=current_principal)
    admission = object.__new__(execution.LeafPopulationExecutionService); admission.jobs = jobs
    query = object.__new__(queries.LeafPopulationExecutionQuery); query.jobs = jobs; query.service = admission
    monkeypatch.setattr(admission, '_binding', lambda: None); monkeypatch.setattr(query, '_binding', lambda: None)
    state = {'calls': [], 'error': None, 'hook': None}; row = {'job_id': JOB, 'stage': 'simulation', 'state': 'queued',
        'attempt_count': 0, 'max_attempts': 3, 'created_at': NOW, 'updated_at': NOW, 'reason': None}
    def submit(tenant, raw):
        state['calls'].append(('submit', tenant, json.loads(raw)))
        if state['hook']: state['hook']()
        if state['error']: raise state['error']
        return row
    monkeypatch.setattr(admission, 'submit', submit)
    def read(tenant, job_id, **kw):
        state['calls'].append(('read', tenant, job_id, kw))
        if state['hook']: state['hook']()
        if state['error']: raise state['error']
        return {'schema_version': 'leaf-population-execution-read-v1', **execution.signed.FLAGS,
            'observed_at': NOW.isoformat().replace('+00:00', 'Z'), 'job': {
                **{k: v for k, v in row.items() if k != 'reason'}, 'reason_code': None},
            'cancel_requested': False, 'result': None, 'manifest': None, 'frame': None, 'replay': None}
    monkeypatch.setattr(query, 'read', read)
    state['services'] = jobs, admission, query
    app = FastAPI()
    @app.exception_handler(RequestValidationError)
    async def invalid(*_): return error(422, 'invalid_request', 'Invalid request')
    route.install_leaf_population_execution_routes(app, jobs=jobs, admission=admission, query=query,
        principal_provider=current_principal, authorized_tenant=authorized, error=error, access=access)
    return protect(app, scopes if scopes is not None else set(route.SUBMIT_SCOPES+route.READ_SCOPES+route.CANCEL_SCOPES)), state


def call(app, path=POST, body=None, **kw):
    return asyncio.run(request(app, path=path, method='POST', body=execution.signed.reader._canonical(BODY) if body is None else body,
        headers=[(b'authorization', b'Bearer '+TOKEN), (b'content-type', b'application/json')], **kw))


def test_valid_admission_is_queued_and_never_calculates(route, monkeypatch):
    app, state = assembly(route, monkeypatch); status, body, headers = call(app)
    assert status == 202 and body['state'] == 'queued' and len(state['calls']) == 1
    assert state['calls'][0][1] == 'tenant-1' and headers[b'cache-control'] == b'no-store'


@pytest.mark.parametrize('fault', ['extra', 'missing', 'rights', 'redistribute', 'source', 'duplicate', 'nan', 'utf8', 'size', 'query', 'parent_missing', 'parent_job', 'parent_extra'])
def test_bad_request_never_dispatches(route, monkeypatch, fault):
    app, state = assembly(route, monkeypatch); body = deepcopy(BODY); query = b''; expected = 422
    if fault == 'extra': body['tenant_id'] = 'foreign'
    elif fault == 'missing': del body['farm']
    elif fault == 'rights': body['rights']['use'] = 1
    elif fault == 'redistribute': body['rights']['redistribute'] = True
    elif fault == 'source': body['rights']['input_source_sha256'] = 'c'*64
    if fault == 'parent_missing': del body['parent']
    elif fault == 'parent_job': body['parent']['job_id'] = 'not-a-UUID'
    elif fault == 'parent_extra': body['parent']['path'] = '/private/source'
    raw = execution.signed.reader._canonical(body)
    if fault == 'duplicate': raw = raw[:-1]+b',"study_id":"other"}'
    elif fault == 'nan': raw = b'{"study_id":NaN}'
    elif fault == 'utf8': raw = b'\xff'
    elif fault == 'size': raw = b'x'*65537; expected = 413
    elif fault == 'query': query = b'tenant_id=foreign'
    assert call(app, body=raw, query=query)[0] == expected and state['calls'] == []


def test_missing_auth_scope_and_disabled_have_no_dispatch(route, monkeypatch):
    app, state = assembly(route, monkeypatch, scopes=set())
    assert call(app)[0] == 403 and state['calls'] == []
    assert asyncio.run(request(app, headers=[]))[0] == 401
    bare = FastAPI(); route.install_leaf_population_execution_routes(bare, jobs=object(), admission=None, query=None,
        principal_provider=current_principal, authorized_tenant=authorized, error=error, access=access)
    disabled = protect(bare, set(route.SUBMIT_SCOPES+route.READ_SCOPES+route.CANCEL_SCOPES))
    assert call(disabled)[0] == 503 and asyncio.run(request(disabled))[0] == 503


@pytest.mark.parametrize('suffix,view,index', [('', 'status', None), ('/manifest', 'manifest', None),
    ('/frames/11', 'frame', 11), ('/replay', 'replay', None)])
def test_read_selects_only_the_requested_current_view(route, monkeypatch, suffix, view, index):
    app, state = assembly(route, monkeypatch)
    status, body, headers = asyncio.run(request(app, path=PATH+suffix))
    assert status == 200 and body['job']['job_id'] == JOB and body['result'] is None
    assert state['calls'] == [('read', 'tenant-1', JOB, {'view': view, 'index': index})]
    assert headers[b'cache-control'] == b'no-store'


@pytest.mark.parametrize('suffix,query,body', [('/frames/-1', b'', b''), ('/frames/true', b'', b''),
    ('/frames/01', b'', b''), ('', b'tenant_id=foreign', b''), ('', b'', b'{}')])
def test_bad_get_has_no_dispatch(route, monkeypatch, suffix, query, body):
    app, state = assembly(route, monkeypatch)
    assert asyncio.run(request(app, path=PATH+suffix, query=query, body=body))[0] == 422
    assert state['calls'] == []


def test_openapi_request_has_no_unresolved_local_definitions(route, monkeypatch):
    app, _ = assembly(route, monkeypatch)
    schema = app.app.openapi()['paths'][POST]['post']['requestBody']['content']['application/json']['schema']
    assert '$ref' not in json.dumps(schema) and schema['additionalProperties'] is False


@pytest.mark.parametrize('failure,status', [(PermissionError,403), (execution.JobIntentConflict,409),
    (queries.LeafPopulationExecutionQueryHold,422), (queries.LeafPopulationExecutionQueryPending,503), (RuntimeError,503)])
def test_private_failures_map_to_fixed_public_errors(route, monkeypatch, failure, status):
    app, state = assembly(route, monkeypatch); state['error'] = failure('private source or credential detail')
    observed, value, headers = call(app)
    assert observed == status and 'private' not in json.dumps(value)
    assert headers[b'cache-control'] == b'no-store'


@pytest.mark.parametrize('fault', [None, 'jobs', 'query_service', 'query_jobs', 'provider', 'farm', 'partial'])
def test_only_one_shared_jobs_provider_farm_and_query_graph_is_installed(route, monkeypatch, fault):
    _, state = assembly(route, monkeypatch); jobs, admission, reader = state['services']; farms = object()
    admission.authority = SimpleNamespace(farm_binding=SimpleNamespace(farms=SimpleNamespace(farms=farms)))
    provider = current_principal
    if fault == 'jobs': admission.jobs = object()
    elif fault == 'query_service': reader.service = object()
    elif fault == 'query_jobs': reader.jobs = object()
    elif fault == 'provider': provider = lambda: current_principal()
    elif fault == 'farm': farms = object()
    elif fault == 'partial': reader = None
    def install():
        route.install_leaf_population_execution_routes(FastAPI(), jobs=jobs, admission=admission, query=reader,
            farms=farms, principal_provider=provider, authorized_tenant=authorized, error=error, access=access)
    if fault is None: install()
    else:
        with pytest.raises(ValueError): install()
    assert state['calls'] == []


def test_disconnected_input_never_dispatches_and_releases_identity(route, monkeypatch):
    app, state = assembly(route, monkeypatch)
    async def exercise():
        status, _, _ = await request(app, path=POST, method='POST', disconnect=True,
            headers=[(b'authorization', b'Bearer '+TOKEN), (b'content-type', b'application/json')])
        assert status == 422 and current_principal() is None
    asyncio.run(exercise()); assert state['calls'] == []


def test_failed_response_send_releases_identity(route, monkeypatch):
    app, state = assembly(route, monkeypatch)
    async def exercise():
        with pytest.raises(ConnectionError): await request(app, send_failure=True)
        assert current_principal() is None
    asyncio.run(exercise()); assert len(state['calls']) == 1
