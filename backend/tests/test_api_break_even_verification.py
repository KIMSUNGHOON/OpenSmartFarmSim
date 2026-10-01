"""Actual SCRAM HTTP/worker connection with synthetic assumptions and test keys."""

import asyncio
from dataclasses import asdict
from datetime import datetime, timedelta, timezone
import http.client
import json
import os
from pathlib import Path
import ssl
import socket
import subprocess
import sys
import time
import threading
from types import SimpleNamespace
from uuid import uuid4

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.api import create_app
from app.api_break_even_verification import VERIFICATION_SCOPES
from app.break_even_verification_worker import BreakEvenVerificationWorker
from app.break_even_verified_result import BreakEvenVerifiedResultService
from test_break_even_verification import (verification_setup, result_api, complete,
    calculation_setup, plan_api, login_database, login_scope, PROFILE)
from test_api_job_status import UnusedMarketResultStore
from test_http_identity import request
from test_api_serve import tls_files

pytestmark = pytest.mark.parametrize('login_scope', [{**PROFILE, 'break_even_calculation': True}], indirect=True)


@pytest.fixture
def verification_api(verification_setup):
    service, parent, principal = verification_setup
    view = service.store._source._source
    reader = BreakEvenVerifiedResultService(service.jobs, service.store)
    app = create_app(service.jobs, view._holds, view._holds._context_store, UnusedMarketResultStore(),
        principal_provider=service.jobs.principal_provider, break_even_store=service.store,
        break_even_verification_service=service, break_even_verified_result_service=reader)
    return app, service, reader, parent, principal


def post(app, parent, *, raw=None, content_type=b'application/json'):
    body = json.dumps({'calculation_job_id': parent}).encode() if raw is None else raw
    return asyncio.run(request(app, method='POST', path='/v1/break-even-verifications',
        headers=[(b'content-type', content_type)], body=body))[:2]


def get(app, identity):
    return asyncio.run(request(app, path=f'/v1/jobs/{identity}/break-even-verified-result'))[:2]


def test_http_admission_reuse_completion_and_read_only_projection(verification_api, monkeypatch):
    from app.break_even import BreakEvenService
    app, service, _, parent, principal = verification_api
    principal['scopes'].discard('break_even_write')
    status, accepted = post(app, parent)
    assert status == 202 and accepted['state'] == 'queued'
    identity = accepted['job_id']
    assert post(app, parent) == (202, accepted)
    assert get(app, identity)[0] == 404
    worker = BreakEvenVerificationWorker(service.jobs, service.store, tenant_id='tenant-1')
    assert worker.run_once(identity).state == 'succeeded'
    principal['scopes'].discard('simulation_execute')
    def forbidden(*_, **__): raise RuntimeError('private arithmetic path')
    monkeypatch.setattr(BreakEvenService, 'scan', forbidden)
    status, value = get(app, identity)
    assert status == 200 and len(value['trials']) == 2 and value['assessment_status'] == 'hold'
    assert value['scope'] == 'conditional_user_grid_only' and value['input_origin'] == 'user'
    assert post(app, parent)[0] == 403


def test_transport_unknown_parent_and_scope_rejection(verification_api):
    app, _, _, parent, principal = verification_api
    for body in (b'{', b'[]', b'{"calculation_job_id":"invalid"}',
            b'{"calculation_job_id":"'+parent.encode()+b'","tenant_id":"foreign"}',
            b'{"calculation_job_id":"'+parent.encode()+b'","calculation_job_id":"'+parent.encode()+b'"}',
            b'{"calculation_job_id":NaN}', b'\xff'):
        assert post(app, parent, raw=body)[0] == 422
    assert post(app, parent, raw=b' '*4097)[0] == 413
    assert post(app, parent, content_type=b'text/plain')[0] == 415
    assert post(app, str(uuid4()))[0] == 422
    assert get(app, 'invalid')[0] == 422 and get(app, str(uuid4()))[0] == 404
    for scope in VERIFICATION_SCOPES:
        principal['scopes'].remove(scope)
        assert post(app, parent)[0] == 403
        principal['scopes'].add(scope)
    principal['authenticated'] = False
    assert post(app, parent)[0] == 401 and get(app, str(uuid4()))[0] == 401


def test_unconfigured_wrong_binding_and_private_errors_are_bounded(verification_api, monkeypatch):
    app, service, reader, parent, _ = verification_api
    view = service.store._source._source
    args = (service.jobs, view._holds, view._holds._context_store, UnusedMarketResultStore())
    kwargs = dict(principal_provider=service.jobs.principal_provider, break_even_store=service.store)
    unconfigured = create_app(*args, **kwargs)
    assert post(unconfigured, parent)[0] == 503 and get(unconfigured, str(uuid4()))[0] == 503
    with pytest.raises(ValueError):
        create_app(*args, **kwargs, break_even_verification_service=SimpleNamespace(jobs=service.jobs, store=service.store))
    def unavailable(*_, **__): raise RuntimeError('private source detail')
    monkeypatch.setattr(service, 'submit', unavailable)
    monkeypatch.setattr(reader, 'read_job_result', unavailable)
    for status, value in (post(app, parent), get(app, str(uuid4()))):
        assert status == 503 and 'private' not in str(value)


def run_operator(service, principal, identity, tmp_path):
    document = {'dsn': service.jobs._dsn, 'policy': asdict(service.jobs.runtime_identity[0]),
        'artifacts': str(service.jobs.artifact_root), 'principal': principal | {'scopes': sorted(principal['scopes'])},
        'hold_scope': service.store._source._source._holds._scope_resolver()}
    config = tmp_path/'verification_operator.json'
    config.write_text(json.dumps(document)); config.chmod(0o600)
    factory = tmp_path/'verification_operator.py'
    factory.write_text('from pathlib import Path\nfrom break_even_operator_factory import build as create\n'
        'def build(): return create(Path(__file__).with_suffix(".json"))\n')
    factory.chmod(0o600)
    env = os.environ | {'PYTHONPATH': os.pathsep.join([str(tmp_path), str(Path(__file__).parent),
        str(Path(__file__).parents[1])])}
    process = subprocess.run([sys.executable, '-m', 'app.break_even_verify_work', '--factory',
        'verification_operator:build', '--job-id', identity], env=env, capture_output=True, text=True, timeout=300)
    assert process.returncode == 0, process.stderr
    result = json.loads(process.stdout)
    assert result['ok'] and result['result']['state'] == 'succeeded'
    assert result['result']['calculation_job_id']


def test_standard_https_admits_separate_operator_and_reads_persisted_result(verification_api, tls_files, tmp_path):
    from app.api_runtime import ApiRuntime
    from app.http_identity import BearerRegistry, BearerGrant, token_digest, current_principal
    from app.market_source_store import MarketSourceStore
    from test_api_runtime import config, dependencies
    _, service, _, parent, principal = verification_api
    token = b'synthetic-grid-verification-token-'+b'v'*32
    now = datetime.now(timezone.utc)
    registry = BearerRegistry((BearerGrant(token_digest(token), 'tenant-1', frozenset(VERIFICATION_SCOPES),
        now-timedelta(seconds=1), now+timedelta(minutes=30)),))
    cert, key, _ = tls_files
    jobs = service.jobs
    factory = lambda *, principal_provider: MarketSourceStore(jobs._dsn, jobs.schema,
        principal_provider=principal_provider, runtime_identity=jobs.runtime_identity)
    runtime = ApiRuntime(config(policy=jobs.runtime_identity[0], dsn=jobs._dsn,
        artifact_root=jobs.artifact_root, certificate=cert, private_key=key),
        dependencies(bearer_registry=registry, market_source_factory=factory,
            market_scope_resolver=service.store._source._source._holds._scope_resolver))
    sock = socket.socket()
    sock.bind(('127.0.0.1', 0)); sock.listen(128)
    port = sock.getsockname()[1]
    server = runtime.service.server()
    thread = threading.Thread(target=server.run, kwargs={'sockets': [sock]}, daemon=True)
    durations = []
    def call(path, method='GET', body=None, authenticated=True):
        headers = {'X-Tenant-ID': 'foreign'}
        if authenticated: headers['Authorization'] = 'Bearer '+token.decode()
        if body is not None: headers['Content-Type'] = 'application/json'
        connection = http.client.HTTPSConnection('127.0.0.1', port,
            context=ssl.create_default_context(cafile=str(cert)), timeout=30)
        start = time.perf_counter()
        try:
            connection.request(method, path, body=body, headers=headers)
            response = connection.getresponse(); raw = response.read()
            assert response.getheader('Cache-Control') == 'no-store'
            durations.append(time.perf_counter()-start)
            assert durations[-1] < 30
            return response.status, json.loads(raw)
        finally: connection.close()
    thread.start()
    try:
        deadline = time.monotonic()+10
        while not server.started:
            assert thread.is_alive() and time.monotonic() < deadline, 'HTTPS server did not start'
            time.sleep(0.02)
        body = json.dumps({'calculation_job_id': parent})
        status, accepted = call('/v1/break-even-verifications', 'POST', body)
        assert status == 202
        identity = accepted['job_id']; path=f'/v1/jobs/{identity}/break-even-verified-result'
        assert call(path)[0] == 404
        run_operator(service, principal, identity, tmp_path)
        status, value = call(path)
        assert status == 200 and len(value['trials']) == 2 and value['assessment_status'] == 'hold'
        assert call('/v1/break-even-verifications', 'POST', body)[1]['job_id'] == identity
        assert call(path, authenticated=False)[0] == 401
        assert current_principal() is None
        print('break_even_verification_https='+json.dumps({'responses': len(durations),
            'max_body_seconds': max(durations), 'client_timeout_seconds': 30,
            'trial_count': 2, 'operator': 'separate_python_process', 'assessment_status': 'hold'}))
    finally:
        server.should_exit = True
        thread.join(timeout=15)
        sock.close()
        assert not thread.is_alive()
