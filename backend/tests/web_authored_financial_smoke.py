"""Actual saved Run -> new money worker -> fake CLI hold -> recovery -> browser 3D."""

from copy import copy
from datetime import datetime, timedelta, timezone
import json
import os
from pathlib import Path
import select
import signal
import subprocess
import sys
import threading
import time
from uuid import UUID

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from app.api_runtime import ApiRuntime
from app.authored_financial_selection import AuthoredFinancialSelectionService
from app.authored_economic_execution import AUTHORED_ECONOMIC_SCOPES
from app.calculation_assessment import ADMISSION_SCOPES
from app.economic_calculation_worker import CALCULATION_SCOPES
from app.farm_authoring_storage import FarmAuthoringService
from app.farm_authored_release_store import AuthoredReleaseStore
from app.farm_authored_review import FarmAuthoredReviewService
from app.farm_authored_run import AuthoredRunPreparer
from app.farm_authored_run_store import AuthoredRunStore
from app.http_identity import BearerGrant, BearerRegistry, token_digest
from app.market_source_store import MarketSourceStore
from app.owned_fixture_registry import OwnedFixtureRegistry
from test_api_runtime import config, dependencies
from test_api_serve import tls_files
from test_authored_calculation_assessment import (authored_pair, authored_economic, authoring,
    farm_setup, login_database, login_scope, PROFILE, assessment_cli)
from test_authored_economic_execution import money_worker
from web_shell_smoke import WEB, frontend


ROOT = Path(__file__).resolve().parents[2]
pytestmark = pytest.mark.parametrize('login_scope', [PROFILE], indirect=True)


def test_saved_authored_run_admits_money_and_assessment_recovers_and_replays(authored_pair, tls_files, tmp_path):
    service, _, intent, _, economic, _ = authored_pair
    jobs = service.jobs
    selected = AuthoredFinancialSelectionService(economic).read('tenant-1', UUID(intent['run_job_id']))
    expected = {'input': selected.calculation_input.model_dump(mode='json'), 'run_id': selected.thermal_run.run_id,
        'amounts': economic.read_job_result('tenant-1', UUID(intent['economic_job_id'])).model_dump(mode='json')['amounts'],
        'cash': economic.read_job_cash_flow('tenant-1', UUID(intent['economic_job_id'])).model_dump(mode='json')}
    expected_path = tmp_path / 'synthetic-browser-expected.json'
    expected_path.write_text(json.dumps(expected))
    token = b'synthetic-authored-financial-browser-' + b'a' * 32
    now = datetime.now(timezone.utc)
    scopes = frozenset((*ADMISSION_SCOPES, *AUTHORED_ECONOMIC_SCOPES, *CALCULATION_SCOPES, 'auditor'))
    grant = BearerGrant(token_digest(token), 'tenant-1', scopes,
        now - timedelta(seconds=1), now + timedelta(minutes=25))
    farm = service.farm_scenario_service
    original = service.authored_run_store.preparer

    def authored_factory(*, job_store, farm_scenario_service, gate_key):
        author = FarmAuthoringService(farm_scenario_service)
        completion = copy(original.release_store.verifier.completion)
        completion.review = FarmAuthoredReviewService(author)
        completion.jobs, completion.runs = job_store, farm_scenario_service.thermal.runs
        verifier = copy(original.release_store.verifier)
        verifier.completion = completion
        return AuthoredRunStore(AuthoredRunPreparer(author, AuthoredReleaseStore(verifier)), gate_key)

    source_factory = lambda *, principal_provider: MarketSourceStore(jobs._dsn, jobs.schema,
        principal_provider=principal_provider, runtime_identity=jobs.runtime_identity)
    cert, key, _ = tls_files
    runtime = ApiRuntime(config(policy=jobs.runtime_identity[0], dsn=jobs._dsn, artifact_root=jobs.artifact_root,
        certificate=cert, private_key=key, port=0, authored_run_gate_key=service.authored_run_store.gate_key,
        thermal_gate_key=service.runs._gate_key, market_hold_key=service.scenario_store.holds._key),
        dependencies(research_registry=farm.registry, bearer_registry=BearerRegistry((grant,)),
            market_source_factory=source_factory, market_scope_resolver=service.scenario_store.holds._scope_resolver,
            owned_fixture_registry=OwnedFixtureRegistry(ROOT),
            owned_research_contexts={next(iter(farm.registry._scopes)): 'context-1'},
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
            env = {name: os.environ[name] for name in ('PATH', 'HOME', 'LANG', 'PLAYWRIGHT_BROWSERS_PATH') if name in os.environ}
            browser = subprocess.Popen(['node', 'e2e/real-authored-financial-smoke.mjs',
                f'https://127.0.0.1:{web_port}', intent['run_job_id'], '300', str(expected_path)],
                cwd=WEB, env=env, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                text=True, start_new_session=True)

            def event():
                assert select.select([browser.stdout], [], [], 240)[0], 'browser phase observation timed out'
                line = browser.stdout.readline()
                if not line:
                    _, error = browser.communicate(timeout=5)
                    pytest.fail('browser exited: ' + error.replace(token.decode(), '<redacted>')[-2500:])
                return json.loads(line)

            queued = event()
            assert queued['event'] == 'economic-queued'
            money_id = UUID(queued['job_id'])
            assert str(money_id) != intent['economic_job_id']
            assert jobs.get_job('tenant-1', money_id)['state'] == 'queued'
            begun = time.monotonic()
            outcome = money_worker(economic).run_once(str(money_id))
            assert outcome.state == 'succeeded'
            print('authored_money_browser_worker_seconds=' + str(round(time.monotonic() - begun, 3)))
            browser.stdin.write('economic-ready\n'); browser.stdin.flush()
            queued = event()
            assert queued['event'] == 'assessment-queued' and queued['economic_job_id'] == str(money_id)
            assessment_id = UUID(queued['job_id'])
            cli, _ = assessment_cli(service, tmp_path)
            lease = jobs.claim(300, tenant_id='tenant-1', job_id=str(assessment_id), allowed_stages=('assessment',))
            begun = time.monotonic()
            outcome = cli._run_claimed(lease)
            assert outcome.state == 'hold' and outcome.decision_id
            print('authored_assessment_browser_worker_seconds=' + str(round(time.monotonic() - begun, 3)))
            browser.stdin.write('assessment-ready\n'); browser.stdin.flush()
            verified = event()
            assert verified['event'] == 'verified' and verified['post_count'] == 2
            assert verified['hold_count'] == 6 and verified['point_count'] == 120 and verified['console_errors'] == 0
            assert verified['client_timeout_seconds'] == 30 and verified['max_response_header_seconds'] < 30
            _, error = browser.communicate(timeout=15)
            assert browser.returncode == 0, error.replace(token.decode(), '<redacted>')[-2500:]
            assert jobs.get_publication('tenant-1', assessment_id) is None
            print('authored_financial_browser_https=' + json.dumps(verified))
    finally:
        if browser is not None and browser.poll() is None:
            os.killpg(browser.pid, signal.SIGTERM)
            try:
                browser.communicate(timeout=5)
            except subprocess.TimeoutExpired:
                os.killpg(browser.pid, signal.SIGKILL)
                browser.communicate(timeout=5)
        server.should_exit = True
        thread.join(timeout=15)
        assert not thread.is_alive()
