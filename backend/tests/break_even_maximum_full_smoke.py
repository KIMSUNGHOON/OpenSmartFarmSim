"""Explicit TLS/operator capacity checks; synthetic software evidence only."""

from dataclasses import asdict
import asyncio
import cProfile
from datetime import datetime, timedelta, timezone
from hashlib import sha256
import http.client
import json
import os
from pathlib import Path
import socket
import ssl
import subprocess
import sys
import threading
import time

import pytest
from cryptography import x509
from cryptography.hazmat.primitives import hashes, serialization

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.api_runtime import ApiRuntime
from app.api_break_even_verification import VERIFICATION_SCOPES
from app.break_even_plan_submission import PLAN_SUBMISSION_SCOPES
from app.http_identity import BearerRegistry, BearerGrant, token_digest, current_principal
from app.market_source_store import MarketSourceStore
from test_api_break_even_plan import build_plan_api, login_database, login_scope, PROFILE
from test_api_runtime import config, dependencies
from test_api_serve import tls_files
from test_http_identity import request
from break_even_admission_profile import profile_summary

def _refresh_operator_tls(tls_files, now):
    cert, private, key = tls_files
    previous = x509.load_pem_x509_certificate(cert.read_bytes())
    builder = (x509.CertificateBuilder().subject_name(previous.subject)
        .issuer_name(previous.issuer).public_key(key.public_key())
        .serial_number(x509.random_serial_number())
        .not_valid_before(now - timedelta(minutes=1))
        .not_valid_after(now + timedelta(hours=12)))
    for extension in previous.extensions:
        builder = builder.add_extension(extension.value, extension.critical)
    certificate = builder.sign(key, hashes.SHA256())
    cert.write_bytes(certificate.public_bytes(serialization.Encoding.PEM))
    return cert, private, key


def test_tls_material_survives_expired_setup_and_both_operator_watchdogs(tls_files):
    cert, private, _ = tls_files
    original = x509.load_pem_x509_certificate(cert.read_bytes())
    private_digest = sha256(private.read_bytes()).digest()
    after_setup = original.not_valid_after_utc + timedelta(minutes=10)
    refreshed, _, _ = _refresh_operator_tls(tls_files, after_setup)
    current = x509.load_pem_x509_certificate(refreshed.read_bytes())
    assert original.not_valid_after_utc < after_setup
    assert current.not_valid_before_utc <= after_setup
    assert current.not_valid_after_utc > after_setup + timedelta(seconds=2 * 7200 + 600)
    assert current.subject == original.subject and current.issuer == original.issuer
    assert list(current.extensions) == list(original.extensions)
    assert current.public_key().public_numbers() == original.public_key().public_numbers()
    assert sha256(private.read_bytes()).digest() == private_digest
    assert private.stat().st_mode & 0o777 == 0o600


def _operator_configuration(service, principal, tmp_path):
    directory = tmp_path / 'maximum_operator_private'
    directory.mkdir(mode=0o700)
    document = {'dsn': service.jobs._dsn, 'policy': asdict(service.jobs.runtime_identity[0]),
        'artifacts': str(service.jobs.artifact_root),
        'principal': principal | {'scopes': sorted(principal['scopes'])},
        'hold_scope': service.store._source._source._holds._scope_resolver()}
    path = directory / 'maximum_operator.json'
    path.write_text(json.dumps(document))
    path.chmod(0o600)
    factory = directory / 'maximum_operator.py'
    factory.write_text('''from pathlib import Path
from break_even_operator_factory import build as create
from app.break_even_calculation_worker import BreakEvenCalculationWorker
def verification():
    return create(Path(__file__).with_suffix('.json'))
def calculation():
    worker = verification()
    return BreakEvenCalculationWorker(worker.jobs, worker.store, tenant_id=worker.tenant_id)
''')
    factory.chmod(0o600)
    return directory


def _run_operator(directory, mode, identity, trial_count):
    module = 'app.break_even_work' if mode == 'calculation' else 'app.break_even_verify_work'
    env = os.environ | {'PYTHONPATH': os.pathsep.join([str(directory),
        str(Path(__file__).parent), str(Path(__file__).parents[1])])}
    started = time.perf_counter()
    # A resource watchdog for this explicit check, not a production worker SLA.
    watchdog = 300 if trial_count == 2 else 7200
    process = subprocess.run([sys.executable, '-m', module, '--factory',
        'maximum_operator:' + mode, '--job-id', identity], env=env,
        capture_output=True, text=True, timeout=watchdog)
    elapsed = time.perf_counter() - started
    assert process.returncode == 0, 'protected operator did not finish successfully'
    result = json.loads(process.stdout)
    assert result['ok'] and result['result']['state'] == 'succeeded'
    assert result['result']['job_id'] == identity
    print('maximum_full_operator=' + json.dumps({'mode': mode,
        'trial_count': trial_count, 'seconds': elapsed,
        'watchdog_seconds': watchdog, 'scope': 'synthetic_software_only'}), flush=True)
    return result['result']


def _exercise_path(login_scope, tls_files, tmp_path, values):
    count = len(values)
    began = time.perf_counter()
    def progress(stage, completed):
        print('maximum_full_setup=' + json.dumps({'stage': stage, 'count': completed,
            'trial_count': count, 'elapsed_seconds': time.perf_counter() - began}), flush=True)
    _, service, body, principal = build_plan_api(login_scope, values, progress=progress)
    private = _operator_configuration(service, principal, tmp_path)
    current_scope = service.store._source._source._holds._scope_resolver()
    token = b'synthetic-maximum-grid-token-' + b'm' * 32
    now = datetime.now(timezone.utc)
    registry = BearerRegistry((BearerGrant(token_digest(token), 'tenant-1',
        frozenset(PLAN_SUBMISSION_SCOPES) | frozenset(VERIFICATION_SCOPES),
        now - timedelta(seconds=1), now + timedelta(hours=12)),))
    cert, key, _ = _refresh_operator_tls(tls_files, now)
    jobs = service.jobs
    factory = lambda *, principal_provider: MarketSourceStore(jobs._dsn, jobs.schema,
        principal_provider=principal_provider, runtime_identity=jobs.runtime_identity)
    runtime = ApiRuntime(config(policy=jobs.runtime_identity[0], dsn=jobs._dsn,
        artifact_root=jobs.artifact_root, certificate=cert, private_key=key),
        dependencies(bearer_registry=registry, market_source_factory=factory,
            market_scope_resolver=lambda *_: dict(current_scope)))
    sock = socket.socket()
    sock.bind(('127.0.0.1', 0))
    sock.listen(128)
    port = sock.getsockname()[1]
    server = runtime.service.server()
    thread = threading.Thread(target=server.run, kwargs={'sockets': [sock]}, daemon=True)
    observations = []
    def call(label, path, method='GET', data=None, *, authenticated=True):
        headers = {'X-Tenant-ID': 'foreign'}
        if authenticated:
            headers['Authorization'] = 'Bearer ' + token.decode()
        if data is not None:
            headers['Content-Type'] = 'application/json'
        connection = http.client.HTTPSConnection('127.0.0.1', port,
            context=ssl.create_default_context(cafile=str(cert)), timeout=30)
        started = time.perf_counter()
        try:
            connection.request(method, path, body=json.dumps(data) if data is not None else None,
                headers=headers)
            response = connection.getresponse()
            raw = response.read()
            elapsed = time.perf_counter() - started
            assert response.getheader('Cache-Control') == 'no-store'
            assert len(raw) <= 524288 and elapsed < 30
            observations.append({'label': label, 'status': response.status,
                'body_bytes': len(raw), 'body_eof_seconds': elapsed})
            print('maximum_full_response=' + json.dumps(observations[-1]), flush=True)
            return response.status, json.loads(raw)
        finally:
            connection.close()
    thread.start()
    try:
        deadline = time.monotonic() + 10
        while not server.started:
            assert thread.is_alive() and time.monotonic() < deadline, 'HTTPS server did not start'
            time.sleep(0.02)
        try:
            status, accepted = call('plan', '/v1/break-even-plans', 'POST', body)
        except TimeoutError:
            if count == 256:
                server.should_exit = True
                thread.join(timeout=45)
                assert not thread.is_alive(), 'owned HTTPS server did not stop before diagnosis'
                profile = cProfile.Profile()
                started = time.perf_counter()
                status, diagnostic, _ = profile.runcall(asyncio.run,
                    request(runtime.service.app, path='/v1/break-even-plans', method='POST',
                        headers=[(b'content-type', b'application/json'),
                            (b'authorization', b'Bearer ' + token)],
                        body=json.dumps(body).encode()))
                elapsed = time.perf_counter() - started
                assert status == 202 and diagnostic['trial_count'] == count
                measured = profile_summary(profile, elapsed, status=status, trial_count=count)
                measured['phase'] = 'diagnostic_asgi_retry_after_original_tls_timeout'
                print('maximum_full_slow_diagnostic=' + json.dumps(measured), flush=True)
            raise
        assert status == 202 and accepted['trial_count'] == count
        assert accepted['intent_job']['state'] == 'queued'
        assert service.store.get_break_even_read('tenant-1', accepted['plan_id']) is None
        parent = accepted['intent_job']['job_id']
        status, repeated = call('plan_reuse', '/v1/break-even-plans', 'POST', body)
        assert status == 202 and repeated == accepted
        status, pending = call('calculation_queued', f'/v1/jobs/{parent}')
        assert status == 200 and pending['state'] == 'queued'
        calculated = _run_operator(private, 'calculation', parent, count)
        assert calculated['plan_id'] == accepted['plan_id']
        status, completed = call('calculation_complete', f'/v1/jobs/{parent}')
        assert status == 200 and completed['state'] == 'succeeded'
        verification_body = {'calculation_job_id': parent}
        status, child = call('verification', '/v1/break-even-verifications', 'POST', verification_body)
        assert status == 202 and child['state'] == 'queued'
        identity = child['job_id']
        path = f'/v1/jobs/{identity}/break-even-verified-result'
        assert call('verification_pending', path)[0] == 404
        verified = _run_operator(private, 'verification', identity, count)
        assert verified['calculation_job_id'] == parent
        status, value = call('verified_result', path)
        assert status == 200 and len(value['trials']) == count
        assert value['plan_id'] == accepted['plan_id']
        assert value['scope'] == 'conditional_user_grid_only'
        assert value['assessment_status'] == 'hold' and value['input_origin'] == 'user'
        status, reused = call('verification_reuse', '/v1/break-even-verifications', 'POST', verification_body)
        assert status == 202 and reused['job_id'] == identity
        assert call('unauthenticated', path, authenticated=False)[0] == 401
        current_scope['scope_version'] = 'withdrawn-during-explicit-capacity-check'
        status, withheld = call('current_hold_scope_changed', path)
        assert status == 503 and 'trials' not in withheld
        assert current_principal() is None
        print('maximum_full_path=' + json.dumps({'trial_count': count,
            'responses': len(observations),
            'max_body_eof_seconds': max(item['body_eof_seconds'] for item in observations),
            'client_timeout_seconds': 30, 'reader': 'actual_http_client_to_eof',
            'operators': 'separate_python_processes', 'scope': 'synthetic_software_only'}), flush=True)
    finally:
        server.should_exit = True
        thread.join(timeout=45)
        sock.close()
        assert not thread.is_alive(), 'owned HTTPS server did not stop'


@pytest.mark.parametrize('login_scope', [{**PROFILE, 'break_even_calculation': True}], indirect=True)
def test_two_trial_tls_operator_harness(login_scope, tls_files, tmp_path):
    _exercise_path(login_scope, tls_files, tmp_path, [20, 32])


@pytest.mark.parametrize('login_scope', [{**PROFILE, 'break_even_calculation': True}], indirect=True)
def test_actual_256_trial_tls_calculation_verification_and_current_read(login_scope, tls_files, tmp_path):
    _exercise_path(login_scope, tls_files, tmp_path, list(range(20, 276)))
