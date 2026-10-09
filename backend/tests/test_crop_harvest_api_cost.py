"""Actual loopback TLS transport tests; full preserved-DB cost is separate native evidence."""
import asyncio
from datetime import datetime, timedelta, timezone
from hashlib import sha256
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
from types import SimpleNamespace

from fastapi import FastAPI
from fastapi.responses import Response, StreamingResponse
import pytest

from app.http_identity import BearerGrant, BearerRegistry, PrincipalMiddleware, token_digest
from app.https_service import HttpsApiService
from test_api_crop_cycle_calculation_tls import fd_inventory

ROOT = Path(__file__).resolve().parents[2]
PATH = ROOT / 'research/crop-harvest-api-cost.py'
SPEC = importlib.util.spec_from_file_location('owned_harvest_api_cost_test', PATH)
cost = importlib.util.module_from_spec(SPEC); SPEC.loader.exec_module(cost)
TARGET = '/v1/crop-harvest-research-results/owned?view=summary'
TOKEN = b'owned-harvest-cost-token-' + b'x' * 32


def write(path, raw):
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o400)
    with os.fdopen(fd, 'wb') as stream: stream.write(raw)


@pytest.fixture
def transport(tmp_path):
    cert, key = cost.certificate(SimpleNamespace(write=write), tmp_path)
    app = FastAPI(); behavior = {'body': b'{"scope":"transport-test-only"}', 'delay': 0, 'trickle': False}
    @app.get('/v1/crop-harvest-research-results/owned')
    async def get():
        await asyncio.sleep(behavior['delay'])
        if behavior['trickle']:
            async def parts():
                for _ in range(6):
                    yield b'x'; await asyncio.sleep(.1)
            return StreamingResponse(parts(), headers={'Cache-Control': 'no-store'})
        return Response(behavior['body'], media_type='application/json', headers={'Cache-Control': 'no-store'})
    now = datetime.now(timezone.utc)
    grant = BearerGrant(token_digest(TOKEN), 'tenant-1', frozenset({'artifact_read'}),
                        now - timedelta(seconds=1), now + timedelta(minutes=5))
    service = HttpsApiService(PrincipalMiddleware(app, BearerRegistry((grant,))), cert, key, port=0)
    api = service.server()  # Configure the standard logger before the FD comparison.
    before = fd_inventory()
    # This fixture intentionally measures transport only; it is not the protected harvest route.
    yield SimpleNamespace(server=lambda: api), cert, behavior
    assert fd_inventory() == before


def test_actual_TLS_wire_and_independent_ASGI_emission_match(transport):
    service, cert, behavior = transport
    with cost.serving(service) as (observed, port):
        response = cost.request(port, cert, TARGET, TOKEN)
        emission = observed.take(0, TARGET)
        assert response['status'] == emission['status'] == 200
        assert response['raw'] == behavior['body']
        assert response['headers']['cache-control'] == 'no-store'
        assert emission['complete'] and emission['bytes'] == len(response['raw'])
        assert emission['sha256'] == sha256(response['raw']).hexdigest()
        assert observed.active == 0 and observed.peak == 1
        assert TOKEN.decode() not in json.dumps(emission)
    assert cost.MAX_SECONDS == 30 and cost.MAX_BYTES == 2 * 1024**2


@pytest.mark.parametrize('fault', ['slow-header', 'trickle-body', 'oversize', 'wrong-CA'])
def test_actual_transport_stops_on_deadline_size_or_certificate(transport, tmp_path, monkeypatch, fault):
    service, cert, behavior = transport
    if fault in ('slow-header', 'trickle-body'):
        monkeypatch.setattr(cost, 'MAX_SECONDS', .25)
        behavior['delay'] = .4 if fault == 'slow-header' else 0
        behavior['trickle'] = fault == 'trickle-body'
    elif fault == 'oversize': behavior['body'] = b'x' * (cost.MAX_BYTES + 100)
    else:
        other = tmp_path / 'other'; other.mkdir(mode=0o700)
        cert, _ = cost.certificate(SimpleNamespace(write=write), other)
    with cost.serving(service) as (observed, port):
        with pytest.raises(cost.ReadHold, match='^harvest_api_read_hold$') as caught:
            cost.request(port, cert, TARGET, TOKEN)
        report = caught.value.report
        assert report['reason'] == ('request_timeout' if fault in ('slow-header', 'trickle-body')
                                    else 'response_bytes' if fault == 'oversize' else 'transport_failed')
        assert set(report) == {'reason', 'seconds', 'bytes'}
        if fault == 'trickle-body': assert 0 < report['bytes'] < 6
        if fault == 'oversize': assert report['bytes'] == 2 * 1024**2 + 1


def test_original_exception_still_closes_owned_HTTPS(transport):
    service, cert, _ = transport
    with pytest.raises(RuntimeError, match='owned caller failed'):
        with cost.serving(service) as (observed, port):
            cost.request(port, cert, TARGET, TOKEN); observed.take(0, TARGET)
            raise RuntimeError('owned caller failed')


def test_failed_ASGI_send_is_incomplete_and_releases_observer():
    async def app(scope, receive, send):
        await send({'type': 'http.response.start', 'status': 200})
        await send({'type': 'http.response.body', 'body': b'owned', 'more_body': False})
    async def send(message):
        if message['type'] == 'http.response.body': raise OSError('owned send failed')
    observed = cost.Observation(app)
    with pytest.raises(OSError):
        asyncio.run(observed({'type': 'http', 'path': TARGET.partition('?')[0],
                              'query_string': b'view=summary'}, None, send))
    value = observed.take(0, TARGET)
    assert not value['complete'] and observed.active == 0
    with pytest.raises(ValueError, match='harvest_api_cost_rejected'): observed.take(0, TARGET + '&changed=1')


def child(script, *args):
    value = subprocess.run([sys.executable, '-c', script, str(PATH), *map(str, args)],
                           capture_output=True, timeout=20)
    assert value.returncode == 0, value.stderr


def test_fresh_import_is_stdlib_only_and_has_no_network_or_FD_effect():
    child('''import importlib.util,os,socket,sys
def denied(*a,**k):raise AssertionError('network during import')
socket.create_connection=denied
before=len(os.listdir('/proc/self/fd'))
spec=importlib.util.spec_from_file_location('owned_cost',sys.argv[1]);v=importlib.util.module_from_spec(spec);spec.loader.exec_module(v)
assert before==len(os.listdir('/proc/self/fd'))
assert not any(n=='app' or n.startswith('app.') for n in sys.modules)
''')


def test_loader_selects_exact_backend_paths_without_network(tmp_path):
    (tmp_path / 'app').mkdir()
    child('''import importlib.util,socket,sys
from pathlib import Path
from hashlib import sha256
def denied(*a,**k):raise AssertionError('network during load')
socket.create_connection=denied
spec=importlib.util.spec_from_file_location('owned_cost',sys.argv[1]);v=importlib.util.module_from_spec(spec);spec.loader.exec_module(v)
root=Path(sys.argv[2]);p=root/'research/crop-harvest-storage-preservation.py'
sys.path.insert(0,sys.argv[3])
storage=v.load_storage(root,sha256(p.read_bytes()).hexdigest())
assert storage.CODE_SHA256==sha256(p.read_bytes()).hexdigest()
assert all(Path(m.__file__).resolve().is_relative_to(root/'backend/app') for n,m in sys.modules.items() if n.startswith('app.') and getattr(m,'__file__',None))
assert all(Path(p).resolve()==root/'backend/app' for p in sys.modules['app'].__path__)
assert all(Path(p).is_relative_to(root) for p in storage.DEPENDENCIES)
''', ROOT, tmp_path)


@pytest.mark.parametrize('fault', ['code-SHA', 'foreign-app-path'])
def test_loader_rejects_wrong_code_or_already_imported_backend(fault, tmp_path):
    child('''import importlib.util,sys,types
from pathlib import Path
from hashlib import sha256
spec=importlib.util.spec_from_file_location('owned_cost',sys.argv[1]);v=importlib.util.module_from_spec(spec);spec.loader.exec_module(v)
root=Path(sys.argv[2]);digest=sha256((root/'research/crop-harvest-storage-preservation.py').read_bytes()).hexdigest()
if sys.argv[3]=='code-SHA':digest='0'*64
else:
 m=types.ModuleType('app');m.__file__=sys.argv[4]+'/app.py';sys.modules['app']=m
try:v.load_storage(root,digest)
except ValueError:pass
else:raise AssertionError('foreign backend/code accepted')
assert 'owned_harvest_cost_storage' not in sys.modules
''', ROOT, fault, tmp_path)
