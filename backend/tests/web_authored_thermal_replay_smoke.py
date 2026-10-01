"""Explicit stored authored Run -> standard HTTPS -> actual browser 3D smoke."""

from datetime import datetime, timedelta, timezone
import json
import os
from pathlib import Path
import subprocess
import sys
import threading
import time

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.api_authored_thermal import AUTHORED_READ_SCOPES, project_authored_run
from app.api_runtime import ApiRuntime
from app.farm_authoring_storage import FarmAuthoringService
from app.farm_authored_review import FarmAuthoredReviewService
from app.farm_authored_run_store import AuthoredRunStore
from app.http_identity import BearerGrant, BearerRegistry, token_digest
from app.market_source_store import MarketSourceStore
from app.owned_fixture_registry import OwnedFixtureRegistry
from test_api_authored_runtime import PROFILE
from test_api_runtime import config, dependencies
from test_api_serve import tls_files
from test_farm_authored_simulation_worker import _admit
from login_database import login_database, login_scope
from web_shell_smoke import frontend, WEB


ROOT = Path(__file__).resolve().parents[2]
pytestmark = pytest.mark.parametrize('login_scope', PROFILE, indirect=True)


def test_authored_run_replays_through_real_https_and_webgl(login_scope, tls_files, tmp_path):
    jobs, _, packet, preparer, original_store, job, worker = _admit(login_scope, tmp_path)
    assert worker.run_once(str(job['job_id'])).state == 'succeeded'
    _, series = project_authored_run(original_store.get_run('tenant-a', packet.run_id))
    cert, key, _ = tls_files
    now = datetime.now(timezone.utc)
    token = b'synthetic-authored-browser-' + b'a' * 32
    grant = BearerGrant(token_digest(token), 'tenant-a', frozenset(AUTHORED_READ_SCOPES),
        now - timedelta(seconds=1), now + timedelta(minutes=20))
    registry = dependencies().research_registry
    contexts = {next(iter(registry._scopes)): 'context-1'}
    source_factory = lambda *, principal_provider: MarketSourceStore(
        jobs._dsn, jobs.schema, principal_provider=principal_provider,
        runtime_identity=jobs.runtime_identity)

    def authored_factory(*, job_store, farm_scenario_service, gate_key):
        preparer.authoring = FarmAuthoringService(farm_scenario_service)
        preparer.release_store.jobs = job_store
        preparer.release_store.verifier.completion.review = FarmAuthoredReviewService(preparer.authoring)
        preparer.release_store.verifier.completion.jobs = job_store
        preparer.release_store.verifier.completion.runs = farm_scenario_service.thermal.runs
        return AuthoredRunStore(preparer, gate_key)

    runtime = ApiRuntime(config(policy=jobs.runtime_identity[0], dsn=jobs._dsn,
        artifact_root=jobs.artifact_root, certificate=cert, private_key=key,
        port=0, authored_run_gate_key=original_store.gate_key),
        dependencies(research_registry=registry, bearer_registry=BearerRegistry((grant,)),
            market_source_factory=source_factory, owned_fixture_registry=OwnedFixtureRegistry(ROOT),
            owned_research_contexts=contexts,
            authored_run_store_factory=authored_factory))
    server = runtime.service.server()
    thread = threading.Thread(target=server.run, daemon=True)
    thread.start()
    browser = None
    try:
        deadline = time.monotonic() + 15
        while not server.started:
            assert thread.is_alive() and time.monotonic() < deadline
            time.sleep(0.01)
        port = server.servers[0].sockets[0].getsockname()[1]
        with frontend(f'https://127.0.0.1:{port}', cert, key) as (web_port, _):
            env = {name: os.environ[name] for name in
                ('PATH', 'HOME', 'LANG', 'PLAYWRIGHT_BROWSERS_PATH') if name in os.environ}
            browser = subprocess.Popen(['node', 'e2e/real-thermal-replay-smoke.mjs',
                f'https://127.0.0.1:{web_port}', str(tmp_path / 'screens')],
                cwd=WEB, env=env, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                stderr=subprocess.PIPE, text=True)
            browser.stdin.write(json.dumps({'kind': 'authored', 'token': token.decode(),
                'job_id': str(job['job_id']), 'run_id': packet.run_id,
                'series': series.model_dump(mode='json')}) + '\n')
            browser.stdin.flush()
            output, error = browser.communicate(timeout=90)
            assert browser.returncode == 0, error[-2500:]
            report = json.loads(output)
            assert report['stage'] == 'verified' and report['points'] == 120
            assert len(report['network']) == 3
            assert all(item['status'] == 200 for item in report['network'])
            print('authored_replay_browser=' + json.dumps(report))
            print('authored_replay_screens=' + str(tmp_path / 'screens'))
    finally:
        if browser is not None and browser.poll() is None:
            browser.kill()
            browser.communicate(timeout=5)
        server.should_exit = True
        thread.join(timeout=15)
        assert not thread.is_alive()
