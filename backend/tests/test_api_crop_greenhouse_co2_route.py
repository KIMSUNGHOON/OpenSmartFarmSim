"""Closed ASGI control flow; native SCRAM/TLS cases are in the companion test."""
import asyncio
from datetime import timedelta
from hashlib import sha256
import json
import os
from pathlib import Path
import subprocess
import sys
import threading
import time
from types import SimpleNamespace
from urllib.parse import urlencode

from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
import pytest

from app import api
from app import api_crop_greenhouse_co2_route as route
from app import crop_greenhouse_co2_current_query as current
from app.api_openapi import _SchemaOnlyStores, contract_document
from app.crop_result_store import READ_SCOPES
from app.http_identity import current_principal
from app.runtime_roles import RolePolicyHold
from test_api_crop_cycle_route import protect, TOKEN, NOW
from test_http_identity import request

PATH = '/v1/crop-greenhouse-co2-research-results/'
RESULT = 'joint-co2-solar-result-v1:'+'a'*64
FARM = dict(scenario_id='joint-farm', scenario_revision='r1', registration_sha256='2'*64, crop_id='crop-1')
public = current.public


def get(app, result_id=RESULT, farm=FARM, *, query='', body=b'', headers=None):
    return asyncio.run(request(app, path=PATH+result_id, query=(urlencode(farm)+query).encode(), body=body,
        headers=headers if headers is not None else [(b'authorization', b'Bearer '+TOKEN)]))


def save(name, value):
    directory = os.environ.get('OSSF_CO2_HTTP_EVIDENCE')
    if directory:
        with (Path(directory)/name).open('x') as f:
            os.fchmod(f.fileno(), 0o400); json.dump(value, f, sort_keys=True, indent=2); f.flush(); os.fsync(f.fileno())


def assembly(monkeypatch, *, scopes=READ_SCOPES):
    trace = []; clock = {'now': NOW}; state = {'error': None, 'raw': b'{}', 'tenant': 'tenant-1', 'read': None}
    jobs = SimpleNamespace(principal_provider=current_principal); farms = object()
    store = object.__new__(current.storage.Co2ResultStore)
    store.jobs = jobs; store.server = SimpleNamespace(binding=SimpleNamespace(jobs=jobs, farms=farms))
    monkeypatch.setattr(store, '_binding', lambda: None)
    query = object.__new__(current.Co2CurrentQuery); query.store = store
    monkeypatch.setattr(query, '_binding', lambda: None)
    def read(tenant, result_id, farm, **kwargs):
        trace.append((tenant, result_id, farm, kwargs)); assert current_principal()['tenant_id'] == 'tenant-1'
        if state['read'] is not None: return state['read']()
        if state['error'] is not None: raise state['error']
        return state['raw']
    monkeypatch.setattr(query, 'read', read)
    def authorized(*required):
        p = current_principal()
        if p is None: return None, api._error(401, 'unauthenticated', 'Authentication required')
        if any(s not in p['scopes'] for s in required): return None, api._error(403, 'forbidden', 'Resource access denied')
        return state['tenant'], None
    app = FastAPI()
    @app.exception_handler(RequestValidationError)
    async def invalid(*_): return api._error(422, 'invalid_request', 'Invalid request')
    route.install_greenhouse_co2_routes(app, jobs=jobs, farms=farms, store=store, query=query,
        principal_provider=current_principal, authorized_tenant=authorized, error=api._error, access=api._access)
    return SimpleNamespace(app=protect(app, tenant='tenant-1', scopes=scopes, clock=lambda: clock['now']),
        store=store, query=query, jobs=jobs, farms=farms, state=state, trace=trace, clock=clock)


def test_default_route_and_create_app_forwarding(monkeypatch):
    unused = _SchemaOnlyStores()
    app = protect(api.create_app(unused, unused, unused, unused, principal_provider=current_principal))
    assert get(app)[0] == 503 and get(app, headers=[])[0] == 401
    seen = []
    monkeypatch.setattr(api, 'install_greenhouse_co2_routes', lambda *_, **kw: seen.append(kw))
    store, query = object(), object()
    api.create_app(unused, unused, unused, unused, principal_provider=current_principal,
        crop_greenhouse_co2_result_store=store, crop_greenhouse_co2_current_query=query)
    assert len(seen) == 1 and seen[0]['store'] is store and seen[0]['query'] is query
    assert seen[0]['jobs'] is unused and seen[0]['principal_provider'] is current_principal


@pytest.mark.parametrize('query', ['&extra=x', '&crop_id=other', '&view=samples&view=events',
    '&view=samples&offset=0&offset=1', '&view=summary&offset=0', '&limit=1', '&view=unknown',
    '&view=events&offset=129', '&view=events&limit=9', '&view=samples&offset=513', '&view=samples&limit=65',
    '&view=samples&offset=-1', '&view=samples&offset=01', '&view=samples&offset=+1', '&view=samples&limit=1.0',
    '&view=samples&offset=true', '&view=samples&limit=0', '&view=samples&offset=', '&view=samples&offset=0x10', '&source_program=x', '&basis=dry', '&co2_basis=wet'])
def test_bad_query_never_reads(monkeypatch, query):
    case = assembly(monkeypatch)
    assert get(case.app, query=query)[0] == 422 and case.trace == []


@pytest.mark.parametrize('fault', ['body', 'missing-field', 'wrong-id', 'authentication', 'scope'])
def test_bad_input_or_authority_never_reads(monkeypatch, fault):
    case = assembly(monkeypatch, scopes=READ_SCOPES[:-1] if fault == 'scope' else READ_SCOPES)
    farm = dict(FARM)
    if fault == 'missing-field': del farm['crop_id']
    status = get(case.app, 'crop-cycle-verified-result-v1:'+'a'*64 if fault == 'wrong-id' else RESULT, farm,
        body=b'{}' if fault == 'body' else b'', headers=[] if fault == 'authentication' else None)[0]
    assert status == (401 if fault == 'authentication' else 403 if fault == 'scope' else 422) and case.trace == []


@pytest.mark.parametrize('fault', ['store', 'query', 'no-store', 'no-query', 'query-store', 'jobs', 'farms',
    'binding-jobs', 'principal', 'store-binding', 'query-binding'])
def test_mixed_assembly_is_rejected(monkeypatch, fault):
    c = assembly(monkeypatch); store, query, jobs, farms, provider = c.store, c.query, c.jobs, c.farms, current_principal
    if fault == 'store': store = object()
    elif fault == 'query': query = object()
    elif fault == 'no-store': store = None
    elif fault == 'no-query': query = None
    elif fault == 'query-store': query.store = object()
    elif fault == 'jobs': jobs = object()
    elif fault == 'farms': farms = object()
    elif fault == 'binding-jobs': store.server.binding.jobs = object()
    elif fault == 'principal': provider = lambda: None
    else:
        def held(): raise RuntimeError('private binding detail')
        monkeypatch.setattr(store if fault == 'store-binding' else query, '_binding', held)
    with pytest.raises(ValueError, match='^trusted co2 research reader required$'):
        route.install_greenhouse_co2_routes(FastAPI(), jobs=jobs, farms=farms, store=store, query=query,
            principal_provider=provider, authorized_tenant=lambda *_: None, error=api._error, access=api._access)


@pytest.mark.parametrize('failure,status', [(PermissionError, 403), (current.Co2CurrentQueryHold, 422),
    (current.server.Co2CustodyHold, 422), (current.server.farms.Co2FarmBindingHold, 422),
    (current.server.Co2CustodyPending, 503), (RolePolicyHold, 503), (RuntimeError, 503)])
def test_failures_hide_private_reasons(monkeypatch, failure, status):
    c = assembly(monkeypatch); c.state['error'] = failure('private detail')
    actual, value, headers = get(c.app)
    assert actual == status and 'private' not in json.dumps(value) and len(c.trace) == 1
    assert headers[b'cache-control'] == b'no-store' and current_principal() is None


@pytest.mark.parametrize('raw,status', [(None, 404), ('{}', 503), (b'', 503), (b'x'*(2*1024**2+1), 503)])
def test_missing_and_bounded_bytes(monkeypatch, raw, status):
    c = assembly(monkeypatch); c.state['raw'] = raw
    assert get(c.app)[0] == status and len(c.trace) == 1


@pytest.mark.parametrize('withdraw', ['credential', 'tenant'])
@pytest.mark.parametrize('failure', [None, current.Co2CurrentQueryHold, PermissionError, RuntimeError])
def test_account_is_checked_after_thread(monkeypatch, withdraw, failure):
    c = assembly(monkeypatch)
    def changed():
        if withdraw == 'credential': c.clock['now'] += timedelta(hours=1)
        else: c.state['tenant'] = 'foreign'
        if failure is not None: raise failure('private query failure')
        return b'{}'
    c.state['read'] = changed
    assert get(c.app)[0] == (401 if withdraw == 'credential' else 403) and len(c.trace) == 1


@pytest.mark.parametrize('view', ['summary', 'samples', 'events'])
def test_same_query_once_and_headers(monkeypatch, view):
    c = assembly(monkeypatch)
    status, _, headers = get(c.app, query='' if view == 'summary' else '&view='+view)
    assert status == 200 and c.trace == [('tenant-1', RESULT, FARM, dict(view=view, offset=0, limit=None))]
    assert headers[b'x-ossf-co2-query-version'] == current.VERSION.encode()
    assert headers[b'x-ossf-co2-query-code-sha256'] == current.CODE_SHA256.encode()
    assert headers[b'x-ossf-co2-projection-code-sha256'] == public.CODE_SHA256.encode()


async def asgi(app, *, receive, send, result_id=RESULT, farm=FARM):
    await app(dict(type='http', asgi={'version': '3.0'}, method='GET', path=PATH+result_id,
        raw_path=(PATH+result_id).encode(), root_path='', query_string=urlencode(farm).encode(),
        headers=[(b'authorization', b'Bearer '+TOKEN)], scheme='https', http_version='1.1',
        server=('test', 443), client=('test', 1234)), receive, send)


def test_early_disconnect_before_query(monkeypatch):
    c = assembly(monkeypatch); sent = []
    async def receive(): return {'type': 'http.disconnect'}
    async def send(message): sent.append(message)
    asyncio.run(asgi(c.app, receive=receive, send=send))
    assert sent[0]['status'] == 422 and c.trace == [] and current_principal() is None


@pytest.mark.parametrize('mode', ['cancel', 'send-failure'])
def test_cancel_or_send_failure_clears_identity_and_worker(monkeypatch, mode):
    c = assembly(monkeypatch); entered = threading.Event(); release = threading.Event(); closed = threading.Event(); after = []
    def blocked():
        try:
            entered.set(); assert release.wait(5); after.append(current_principal()); return b'{}'
        finally: closed.set()
    c.state['read'] = blocked
    async def exercise():
        async def receive(): return dict(type='http.request', body=b'', more_body=False)
        async def send(_): raise RuntimeError('private transport error')
        task = asyncio.create_task(asgi(c.app, receive=receive, send=send))
        deadline = time.monotonic()+5
        while not entered.is_set():
            assert time.monotonic() < deadline; await asyncio.sleep(.001)
        if mode == 'cancel': task.cancel()
        else: release.set()
        try:
            with pytest.raises(asyncio.CancelledError if mode == 'cancel' else RuntimeError): await task
        finally: release.set()
        while not closed.is_set():
            assert time.monotonic() < deadline; await asyncio.sleep(.001)
    asyncio.run(exercise())
    assert closed.is_set() and len(c.trace) == 1 and current_principal() is None
    if mode == 'cancel': assert after == [None]


def test_openapi_preserves_existing_operations_and_closed_joint_shapes():
    root = Path(__file__).resolve().parents[2]
    doc = contract_document(); previous = json.loads((root/'research/artifacts/co2-route-openapi-baseline-20261021.json').read_bytes())
    canonical = lambda value: json.dumps(value, sort_keys=True, separators=(',', ':'), ensure_ascii=False).encode()
    assert all(sha256(canonical(doc['paths'][p])).hexdigest() == digest for p, digest in previous['paths'].items())
    assert set(doc['paths']) == set(previous['paths']) | {PATH+'{result_id}',
        '/v1/crop-greenhouse-co2-executions', '/v1/jobs/{job_id}/crop-greenhouse-co2-execution',
        '/v1/jobs/{job_id}/crop-greenhouse-co2-execution/cancel'}
    assert all(sha256(canonical(doc['components']['schemas'][p])).hexdigest() == digest for p, digest in previous['schemas'].items())
    assert sha256(canonical({k: v for k, v in doc['components'].items() if k != 'schemas'})).hexdigest() == previous['other_components_sha256']
    assert sha256(canonical({k: v for k, v in doc.items() if k not in ('paths', 'components')})).hexdigest() == previous['root_fields_sha256']
    op = doc['paths'][PATH+'{result_id}']['get']; params = {p['name']: p['schema'] for p in op['parameters']}
    assert op['operationId'] == 'getGreenhouseCo2ResearchResult' and op['x-ossf-required-scopes'] == list(READ_SCOPES)
    assert op['security'] == [{'ServiceBearer': []}] and params['result_id']['pattern'] == public.RESULT_ID_PATTERN
    assert params['offset']['maximum'] == 512 and params['limit']['anyOf'][0]['maximum'] == 64
    ref = op['responses']['200']['content']['application/json']['schema']['$ref'].rsplit('/', 1)[1]
    assert doc['components']['schemas'][ref]['additionalProperties'] is False
    assert 'Co2Reference' in doc['components']['schemas']
    assert doc['components']['schemas']['HarvestReplay']['properties']['reference']['$ref'] == '#/components/schemas/Reference'
    assert set(op['responses']) == {'200', '401', '403', '404', '422', '503'}
    save('openapi.json', {'paths': len(doc['paths']), 'schemas': len(doc['components']['schemas']),
        'existing_operations_equal': True, 'existing_schema_count_preserved': len(previous['schemas']),
        'closed_joint_response': True})


@pytest.mark.parametrize('first', ['app.api', 'app.api_crop_greenhouse_co2_route', 'app.operator_config'])
def test_fresh_import_order_and_schema_do_not_connect_or_start_query(first):
    code = '''import importlib,json,os,socket,sys,psycopg
def forbidden(*a,**k):raise AssertionError('schema tried I/O')
psycopg.connect=forbidden;socket.create_connection=forbidden
before=len(os.listdir('/proc/self/fd'));importlib.import_module(sys.argv[1])
from app.api_openapi import contract_document
assert '/v1/crop-greenhouse-co2-research-results/{result_id}' in contract_document()['paths']
assert 'app.crop_greenhouse_co2_current_query' not in sys.modules
assert 'app.crop_cycle_calculation_context' not in sys.modules
assert len(os.listdir('/proc/self/fd'))==before
print(json.dumps({'first':sys.argv[1],'FD':before,'query_loaded':False,'database_or_socket_connections':0}))
'''
    child = subprocess.run([sys.executable, '-B', '-c', code, first], capture_output=True, timeout=30)
    assert child.returncode == 0, child.stderr.decode()
    save('import-'+first.rsplit('.', 1)[-1]+'.json', json.loads(child.stdout))
