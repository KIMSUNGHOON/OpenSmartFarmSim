"""Closed ASGI control flow and actual SCRAM/verified TLS original reads."""
import asyncio
from copy import deepcopy
from datetime import timedelta
from hashlib import sha256
import http.client
import logging
import json
import os
from pathlib import Path
import ssl
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
from app import api_crop_greenhouse_ventilation_route as route
from app import crop_greenhouse_ventilation_current_query as current
from app.api_openapi import _SchemaOnlyStores, contract_document
from app.crop_result_store import READ_SCOPES
from app.http_identity import current_principal
from app.https_service import HttpsApiService
from app.runtime_roles import RolePolicyHold
from test_api_crop_cycle_route import protect, TOKEN, NOW
from test_api_serve import tls_files
from test_http_identity import request
from test_crop_greenhouse_ventilation_result_store import login_database, original_login_scope, login_scope, farm_setup, setup
from test_farm_authoring_storage import authoring as base_authoring
from test_api_crop_greenhouse_ventilation_replay import database_cleanup
import test_crop_greenhouse_ventilation_result_store as registered

profiles = registered.profiles
PATH = '/v1/crop-greenhouse-ventilation-research-results/'
RESULT = 'joint-ventilation-result-v1:'+'a'*64
FARM = dict(scenario_id='joint-farm', scenario_revision='r1', registration_sha256='2'*64, crop_id='crop-1')
public = current.public


def get(app, result_id=RESULT, farm=FARM, *, query='', body=b'', headers=None):
    return asyncio.run(request(app, path=PATH+result_id, query=(urlencode(farm)+query).encode(), body=body,
        headers=headers if headers is not None else [(b'authorization', b'Bearer '+TOKEN)]))


def save(name, value):
    directory = os.environ.get('OSSF_VENTILATION_ROUTE_EVIDENCE')
    if directory:
        with (Path(directory)/name).open('x') as f:
            os.fchmod(f.fileno(), 0o400); json.dump(value, f, sort_keys=True, indent=2); f.flush(); os.fsync(f.fileno())


def assembly(monkeypatch, *, scopes=READ_SCOPES):
    trace = []; clock = {'now': NOW}; state = {'error': None, 'raw': b'{}', 'tenant': 'tenant-1', 'read': None}
    jobs = SimpleNamespace(principal_provider=current_principal); farms = object()
    store = object.__new__(current.storage.VentilationResultStore)
    store.jobs = jobs; store.server = SimpleNamespace(binding=SimpleNamespace(jobs=jobs, farms=farms))
    monkeypatch.setattr(store, '_binding', lambda: None)
    query = object.__new__(current.VentilationCurrentQuery); query.store = store
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
    route.install_greenhouse_ventilation_routes(app, jobs=jobs, farms=farms, store=store, query=query,
        principal_provider=current_principal, authorized_tenant=authorized, error=api._error, access=api._access)
    return SimpleNamespace(app=protect(app, tenant='tenant-1', scopes=scopes, clock=lambda: clock['now']),
        store=store, query=query, jobs=jobs, farms=farms, state=state, trace=trace, clock=clock)


def test_default_route_and_create_app_forwarding(monkeypatch):
    unused = _SchemaOnlyStores()
    app = protect(api.create_app(unused, unused, unused, unused, principal_provider=current_principal))
    assert get(app)[0] == 503 and get(app, headers=[])[0] == 401
    seen = []
    monkeypatch.setattr(api, 'install_greenhouse_ventilation_routes', lambda *_, **kw: seen.append(kw))
    store, query = object(), object()
    api.create_app(unused, unused, unused, unused, principal_provider=current_principal,
        crop_greenhouse_ventilation_result_store=store, crop_greenhouse_ventilation_current_query=query)
    assert len(seen) == 1 and seen[0]['store'] is store and seen[0]['query'] is query
    assert seen[0]['jobs'] is unused and seen[0]['principal_provider'] is current_principal


@pytest.mark.parametrize('query', ['&extra=x', '&crop_id=other', '&view=samples&view=events',
    '&view=samples&offset=0&offset=1', '&view=summary&offset=0', '&limit=1', '&view=unknown',
    '&view=events&offset=129', '&view=events&limit=9', '&view=samples&offset=513', '&view=samples&limit=65',
    '&view=samples&offset=-1', '&view=samples&offset=01', '&view=samples&offset=+1', '&view=samples&limit=1.0',
    '&view=samples&offset=true', '&view=samples&limit=0', '&view=samples&offset=', '&view=samples&offset=0x10'])
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
    with pytest.raises(ValueError, match='^trusted ventilation research reader required$'):
        route.install_greenhouse_ventilation_routes(FastAPI(), jobs=jobs, farms=farms, store=store, query=query,
            principal_provider=provider, authorized_tenant=lambda *_: None, error=api._error, access=api._access)


@pytest.mark.parametrize('failure,status', [(PermissionError, 403), (current.VentilationCurrentQueryHold, 422),
    (current.server.VentilationCustodyHold, 422), (current.server.farms.VentilationFarmBindingHold, 422),
    (current.server.VentilationCustodyPending, 503), (RolePolicyHold, 503), (RuntimeError, 503)])
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
@pytest.mark.parametrize('failure', [None, current.VentilationCurrentQueryHold, PermissionError, RuntimeError])
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
    assert headers[b'x-ossf-ventilation-query-version'] == current.VERSION.encode()
    assert headers[b'x-ossf-ventilation-query-code-sha256'] == current.CODE_SHA256.encode()
    assert headers[b'x-ossf-ventilation-projection-code-sha256'] == public.CODE_SHA256.encode()


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
    doc = contract_document(); previous = json.loads((Path(__file__).resolve().parents[2]/'contracts/openapi-v1.json').read_bytes())
    assert all(doc['paths'][p] == v for p, v in previous['paths'].items() if p != PATH+'{result_id}')
    op = doc['paths'][PATH+'{result_id}']['get']; params = {p['name']: p['schema'] for p in op['parameters']}
    assert op['operationId'] == 'getGreenhouseVentilationResearchResult' and op['x-ossf-required-scopes'] == list(READ_SCOPES)
    assert op['security'] == [{'ServiceBearer': []}] and params['result_id']['pattern'] == public.RESULT_ID_PATTERN
    assert params['offset']['maximum'] == 512 and params['limit']['anyOf'][0]['maximum'] == 64
    ref = op['responses']['200']['content']['application/json']['schema']['$ref'].rsplit('/', 1)[1]
    assert doc['components']['schemas'][ref]['additionalProperties'] is False
    assert 'VentilationReference' in doc['components']['schemas']
    assert doc['components']['schemas']['HarvestReplay']['properties']['reference']['$ref'] == '#/components/schemas/Reference'
    assert set(op['responses']) == {'200', '401', '403', '404', '422', '503'}
    save('openapi.json', {'paths': len(doc['paths']), 'schemas': len(doc['components']['schemas']),
        'existing_operations_equal': True, 'closed_joint_response': True})


@pytest.mark.parametrize('first', ['app.api', 'app.api_crop_greenhouse_ventilation_route', 'app.operator_config'])
def test_fresh_import_order_and_schema_do_not_connect_or_start_query(first):
    code = '''import importlib,json,os,socket,sys,psycopg
def forbidden(*a,**k):raise AssertionError('schema tried I/O')
psycopg.connect=forbidden;socket.create_connection=forbidden
before=len(os.listdir('/proc/self/fd'));importlib.import_module(sys.argv[1])
from app.api_openapi import contract_document
assert '/v1/crop-greenhouse-ventilation-research-results/{result_id}' in contract_document()['paths']
assert 'app.crop_greenhouse_ventilation_current_query' not in sys.modules
assert 'app.crop_cycle_calculation_context' not in sys.modules
assert len(os.listdir('/proc/self/fd'))==before
print(json.dumps({'first':sys.argv[1],'FD':before,'query_loaded':False,'database_or_socket_connections':0}))
'''
    child = subprocess.run([sys.executable, '-B', '-c', code, first], capture_output=True, timeout=30)
    assert child.returncode == 0, child.stderr.decode()
    save('import-'+first.rsplit('.', 1)[-1]+'.json', json.loads(child.stdout))


@pytest.fixture
def authoring(base_authoring, monkeypatch):
    farms, _, principal = base_authoring; replay = farms.replay; mode = {'preparing': True}
    def provider(): return principal if mode['preparing'] else current_principal()
    monkeypatch.setattr(replay.jobs, 'principal_provider', provider)
    for obj in (replay.thermal.runs, replay.thermal.holds, replay.candidates,
                replay.candidates._source, replay.candidates._source._source):
        monkeypatch.setattr(obj, '_principal_provider', provider)
    farms._http_test_mode = mode
    yield base_authoring
    mode['preparing'] = True


LOGIN = registered.pytestmark


@pytest.fixture
def native(setup, database_cleanup, monkeypatch):
    store, raw, value, done = registered.ready(setup); record = store.put('tenant-1', raw)
    query = current.VentilationCurrentQuery(store); farms = store.server.binding.farms; replay = farms.replay
    calls = registered.producer.reference.forbid(monkeypatch)
    farm = json.loads(raw)['farm']; before = registered.producer.reference.counts(store.server.binding)
    unused = _SchemaOnlyStores()
    app = api.create_app(store.jobs, replay.thermal.holds, replay.thermal.runs, unused,
        principal_provider=store.jobs.principal_provider, thermal_scenario_store=replay.thermal,
        farm_scenario_service=replay, farm_authoring_service=farms,
        crop_greenhouse_ventilation_result_store=store, crop_greenhouse_ventilation_current_query=query)
    yield SimpleNamespace(store=store, query=query, record=record, farm=farm, value=value, done=json.loads(done), calls=calls,
        app=app, mode=farms._http_test_mode, before=before)
    farms._http_test_mode['preparing'] = True
    assert registered.producer.reference.counts(store.server.binding) == before and registered.count(store.server.binding) == 1
    assert all(n == 0 for n in calls.values())


def native_app(case, *, scopes=READ_SCOPES, tenant='tenant-1', clock=None):
    case.mode['preparing'] = False
    return protect(case.app, scopes=scopes, tenant=tenant, clock=clock)


def fd_inventory():
    result = {}
    for path in Path('/proc/self/fd').iterdir():
        try:
            info = path.stat(); result[path.name] = (os.readlink(path), info.st_dev, info.st_ino)
        except FileNotFoundError: pass
    return result


@LOGIN
@pytest.mark.parametrize('setup', [None, 'hold'], indirect=True)
def test_native_scram_verified_https_original_wires_completed_hold(native, tls_files):
    c = native; initial_fds = fd_inventory(); expected = {view: c.query.read('tenant-1', c.record['result_id'], c.farm, view=view)
        for view in ('summary', 'samples', 'events')}
    assert fd_inventory() == initial_fds
    with c.store.jobs.connect() as conn: assert conn.pgconn.used_password and conn.info.get_parameters()['require_auth'] == 'scram-sha-256'
    pytest_log_fds = {str(handler().stream.fileno()) for handler in logging._handlerList
        if handler() is not None and type(handler()).__module__ == '_pytest.logging'
        and getattr(handler(), 'baseFilename', None) == os.devnull
        and getattr(handler(), 'stream', None) is not None and not handler().stream.closed}
    cert, key, _ = tls_files; server = HttpsApiService(native_app(c), cert, key, port=0).server()
    inventory = fd_inventory(); fd = len(inventory)
    assert inventory == {k: v for k, v in initial_fds.items() if k not in pytest_log_fds}
    thread = threading.Thread(target=server.run, daemon=True); thread.start(); replies = {}; deadline = time.monotonic()+10
    try:
        while not server.started:
            assert thread.is_alive() and time.monotonic() < deadline; time.sleep(.01)
        port = server.servers[0].sockets[0].getsockname()[1]; context = ssl.create_default_context(cafile=str(cert))
        for view, original in expected.items():
            connection = http.client.HTTPSConnection('127.0.0.1', port, context=context, timeout=30)
            started = time.monotonic()
            try:
                connection.request('GET', PATH+c.record['result_id']+'?'+urlencode(c.farm)+('' if view == 'summary' else '&view='+view),
                    headers={'Authorization': 'Bearer '+TOKEN.decode()})
                response = connection.getresponse(); raw = response.read(); assert response.status == 200 and raw == original
                assert response.getheader('Cache-Control') == 'no-store' and len(raw) <= public.MAX_RESPONSE_BYTES
                replies[view] = dict(bytes=len(raw), sha256=sha256(raw).hexdigest(), seconds=time.monotonic()-started)
            finally: connection.close()
    finally:
        server.should_exit = True; thread.join(15); assert not thread.is_alive(); c.mode['preparing'] = True
    summary = json.loads(expected['summary']); assert summary['summary']['status'] == c.done['status']
    assert summary['reference']['G0_G4'] == 'not_assessed'
    assert summary['summary']['last_confirmed']['time']['at'].endswith('.123456Z')
    if c.done['status'] == 'hold': assert summary['summary']['checkpoint_sha256'] is None and summary['summary']['hold'] is not None
    save('native-FD-'+c.done['status']+'.json', dict(before=inventory, after=fd_inventory()))
    assert fd_inventory() == inventory and current_principal() is None
    save('native-'+c.done['status']+'.json', dict(replies=replies, actual_scram=True, verified_TLS=True,
        original_response_bytes_equal=True, original_108_states_ledgers_UTC=True, calls=c.calls,
        pytest_devnull_log_handlers_closed_by_TLS_logging_config=len(pytest_log_fds), FD=[fd, len(fd_inventory())]))


@LOGIN
def test_native_request_refusal_missing_account_and_early_disconnect(native, monkeypatch):
    c = native; app = native_app(c); reads = []; original = c.query.read
    def read(*a, **kw): reads.append(1); return original(*a, **kw)
    monkeypatch.setattr(c.query, 'read', read)
    for query in ('&extra=x', '&view=events&offset=129', '&view=samples&limit=65'):
        assert get(app, c.record['result_id'], c.farm, query=query)[0] == 422
    assert get(app, c.record['result_id'], c.farm, body=b'{}')[0] == 422
    assert get(app, c.record['result_id'], c.farm, headers=[])[0] == 401
    assert get(native_app(c, scopes=READ_SCOPES[:-1]), c.record['result_id'], c.farm)[0] == 403
    sent = []
    async def receive(): return {'type': 'http.disconnect'}
    async def send(message): sent.append(message)
    asyncio.run(asgi(app, receive=receive, send=send, result_id=c.record['result_id'], farm=c.farm))
    assert sent[0]['status'] == 422
    assert reads == []
    assert get(native_app(c), 'joint-ventilation-result-v1:'+'0'*64, c.farm)[0] == 404
    assert get(native_app(c, tenant='foreign'), c.record['result_id'], c.farm)[0] in (403, 404)
    assert len(reads) == 2
    save('native-refusals.json', dict(early_invalid_query_calls=0, missing_or_foreign_denied=True, calls=c.calls))


@LOGIN
@pytest.mark.parametrize('phase', ['rights', 'account'])
def test_native_withdrawal_during_serialization_withholds_original_bytes(native, monkeypatch, phase):
    c = native; binding, _, packet, _, _, rights = c.value
    source = binding.farms.replay.candidates._source._source; previous = source.get_input_rights
    clock = {'now': NOW}; app = native_app(c, clock=lambda: clock['now']); encode = public._public_bytes; rejected = []
    changes = [('input-rights', lambda: setattr(rights, 'allowed', False), lambda: setattr(rights, 'allowed', True)),
        ('review', lambda: packet[3].update(status='revoked'), lambda: packet[3].update(status='accepted_for_software_validation')),
        ('farm-source', lambda: setattr(source, 'get_input_rights', lambda *_: None), lambda: setattr(source, 'get_input_rights', previous))]
    if phase == 'account': changes = [('credential', lambda: clock.update(now=NOW+timedelta(hours=1)), lambda: clock.update(now=NOW))]
    for name, withdraw, restore in changes:
        for view in ('summary', 'samples', 'events'):
            observed = []
            def serialized(model):
                raw = encode(model); observed.append(1)
                if len(observed) == 2: withdraw()
                return raw
            try:
                with monkeypatch.context() as patch:
                    patch.setattr(public, '_public_bytes', serialized)
                    status, value, _ = get(app, c.record['result_id'], c.farm, query='' if view == 'summary' else '&view='+view)
                assert status == (401 if phase == 'account' else 422) and 'error' in value and len(observed) == 2
                rejected.append(name+':'+view)
            finally: restore()
    c.mode['preparing'] = True
    save('native-withdrawal-'+phase+'.json', dict(rejected=rejected, serialized_but_withheld=True, calls=c.calls))


@LOGIN
@pytest.mark.parametrize('mode', ['cancel', 'send-failure'])
def test_native_cancel_and_send_failure_release_custody(native, monkeypatch, mode):
    c = native; app = native_app(c); entered = threading.Event(); release = threading.Event(); closed = threading.Event()
    encode = public._public_bytes; original = c.query.read; wires = []; after = []; fd = fd_inventory()
    def serialized(model):
        wire = encode(model); wires.append(wire)
        if len(wires) == 2:
            entered.set(); assert release.wait(10)
        return wire
    def read(*a, **kw):
        try: return original(*a, **kw)
        finally: after.append(current_principal()); closed.set()
    async def exercise():
        async def receive(): return dict(type='http.request', body=b'', more_body=False)
        async def send(_): raise RuntimeError('private transport error')
        task = asyncio.create_task(asgi(app, receive=receive, send=send, result_id=c.record['result_id'], farm=c.farm))
        deadline = time.monotonic()+20
        while not entered.is_set():
            assert time.monotonic() < deadline; await asyncio.sleep(.001)
        if mode == 'cancel': task.cancel()
        else: release.set()
        try:
            with pytest.raises(asyncio.CancelledError if mode == 'cancel' else RuntimeError): await task
        finally: release.set()
        while not closed.is_set():
            assert time.monotonic() < deadline; await asyncio.sleep(.001)
    with monkeypatch.context() as patch:
        patch.setattr(public, '_public_bytes', serialized); patch.setattr(c.query, 'read', read)
        asyncio.run(exercise())
    c.mode['preparing'] = True
    assert closed.is_set() and c.query.read('tenant-1', c.record['result_id'], c.farm) == wires[1]
    assert current_principal() is None and fd_inventory() == fd
    if mode == 'cancel': assert after == [None]
    save('native-'+mode+'.json', dict(worker_closed=True, custody_reopened_same_wire=True,
        current_principal_cleared=True, FD_count=len(fd), calls=c.calls))
