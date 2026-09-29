"""Explicit real TLS/browser/PG integration; synthetic fake CLI, no G1/G4 proof."""

from contextlib import contextmanager
from hashlib import sha256
import http.client
import json
import os
from pathlib import Path
import select
import socket
import ssl
import subprocess
import sys
import threading
import time
from uuid import UUID

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from app.api_runtime import ApiRuntime
from app.cli_contracts import DecisionContract, _canonical
from app.cli_worker import CliWorker
from app.job_store import JobStore
from app.research_registry import ResearchRegistry
from login_database import login_database, login_scope
from test_api_runtime import TOKEN, config, dependencies
from test_api_serve import tls_files
from test_api_location_research import rows
from test_cli_worker import _fake_cli
from test_job_evidence import cli_store
from test_jobs import synthetic_principal


WEB = Path(__file__).resolve().parents[2]/'web'


@contextmanager
def frontend(origin, cert, key, *, trusted=True):
    with socket.socket() as probe:
        probe.bind(('127.0.0.1', 0)); port = probe.getsockname()[1]
    env = {name: os.environ[name] for name in ('PATH', 'HOME', 'LANG', 'PLAYWRIGHT_BROWSERS_PATH')
           if name in os.environ}
    env.update(OSSF_WEB_API_ORIGIN=origin, OSSF_WEB_TLS_CERT=str(cert), OSSF_WEB_TLS_KEY=str(key))
    if trusted: env['OSSF_WEB_API_CA'] = str(cert)
    child = subprocess.Popen(['node', 'node_modules/vite/bin/vite.js', '--port', str(port)],
        cwd=WEB, env=env, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    try:
        context = ssl.create_default_context(cafile=str(cert))
        deadline = time.monotonic()+20
        while time.monotonic() < deadline and child.poll() is None:
            client = http.client.HTTPSConnection('127.0.0.1', port, timeout=1, context=context)
            try:
                client.request('GET', '/')
                response = client.getresponse()
                if response.status == 200:
                    response.read(); break
            except (OSError, http.client.HTTPException):
                time.sleep(.1)
            finally: client.close()
        else: pytest.fail('synthetic frontend did not become ready')
        yield port, context
    finally:
        child.terminate()
        try: child.wait(timeout=5)
        except subprocess.TimeoutExpired: child.kill(); child.wait(timeout=5)


@pytest.mark.parametrize('login_scope', [{'market_calculation': True, 'break_even_calculation': True}], indirect=True)
def test_browser_real_https_admission_persisted_hold_and_verified_upstream(login_scope, tls_files, tmp_path):
    base, policy, dsns = login_scope
    cert, key, _ = tls_files
    base.artifact_root.mkdir(mode=0o700)
    raw = _canonical({'registry_version': 'research-registry-v1', 'registrations': [{
        'tenant_id': 'tenant-1', 'point': {'latitude': 37.5, 'longitude': 127.0},
        'period_start_utc': '2026-10-15T08:00:00.000Z',
        'period_end_utc': '2026-10-15T10:00:00.000Z', 'goal_id': 'historical-thermal-replay',
        'provider_ids': ['synthetic-provider-v1']}]})
    catalog = ResearchRegistry(raw, sha256(raw).hexdigest())
    runtime = ApiRuntime(config(policy=policy, dsn=dsns['authority'], artifact_root=base.artifact_root,
        certificate=cert, private_key=key, port=0), dependencies(research_registry=catalog))
    server = runtime.service.server()
    thread = threading.Thread(target=server.run, daemon=True)
    thread.start()
    browser = None
    try:
        deadline = time.monotonic()+10
        while not server.started and thread.is_alive() and time.monotonic() < deadline: time.sleep(.05)
        assert server.started
        api_port = server.servers[0].sockets[0].getsockname()[1]
        origin = f'https://127.0.0.1:{api_port}'
        with frontend(origin, cert, key) as (port, _):
            env = {name: os.environ[name] for name in ('PATH', 'HOME', 'LANG', 'PLAYWRIGHT_BROWSERS_PATH')
                   if name in os.environ}
            browser = subprocess.Popen(['node', 'e2e/real-api-smoke.mjs', f'https://127.0.0.1:{port}'],
                cwd=WEB, env=env, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            assert select.select([browser.stdout], [], [], 30)[0], 'synthetic browser admission timed out'
            line = browser.stdout.readline()
            if not line:
                _, errors = browser.communicate(timeout=5)
                pytest.fail('synthetic browser exited before admission: '+errors[:2000])
            queued = json.loads(line)
            assert queued['stage'] == 'queued' and UUID(queued['job_id'])
            contract = DecisionContract(catalog.authority_snapshot)
            principal = lambda: {**synthetic_principal(), 'tenant_id': 'tenant-1'}
            jobs = JobStore(dsns['authority'], policy.schema, base.artifact_root,
                principal_provider=principal, runtime_identity=(policy, 'authority'),
                decision_validator=contract, evidence_policy=cli_store(base).evidence_policy,
                audit_runtime_grants=True)
            home = tmp_path/'fake-cli-home'; home.mkdir(mode=0o700)
            worker = CliWorker(jobs, contract, cli_path=_fake_cli(tmp_path), codex_home=home,
                child_env={'CODEX_API_KEY': 'synthetic-test-key'}, timeout_seconds=5,
                lease_seconds=15, synthetic_smoke=True)
            outcome = worker.run_once()
            assert outcome.state == 'hold' and str(outcome.job_id) == queued['job_id']
            browser.stdin.write('hold-ready\n'); browser.stdin.flush()
            output, errors = browser.communicate(timeout=30)
            assert browser.returncode == 0, errors[-2000:]
            assert json.loads(output)['stage'] == 'verified'
            assert len(rows(base)) == 1 and rows(base)[0]['state'] == 'hold'
            assert worker.run_once() is None
        with frontend(origin, cert, key, trusted=False) as (port, context):
            client = http.client.HTTPSConnection('127.0.0.1', port, timeout=5, context=context)
            try:
                client.request('GET', '/v1/jobs/'+queued['job_id'], headers={'Authorization': 'Bearer '+TOKEN.decode()})
                response = client.getresponse()
                assert response.status == 502 and queued['job_id'].encode() not in response.read()
            finally: client.close()
    finally:
        if browser is not None and browser.poll() is None:
            browser.kill(); browser.communicate(timeout=5)
        server.should_exit = True; thread.join(timeout=15)
        assert not thread.is_alive()
