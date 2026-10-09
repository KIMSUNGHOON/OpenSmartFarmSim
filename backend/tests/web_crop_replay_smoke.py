"""Explicit actual SCRAM storage -> trusted HTTPS -> calculated crop geometry."""
from copy import deepcopy
from datetime import datetime, timedelta, timezone
from hashlib import sha256
import json
import os
from pathlib import Path
import select
import subprocess
import sys
import threading
import time

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from app.api_crop_replay import project_crop_result
from app.api_runtime import ApiRuntime
from app.crop_result_store import CropResultStore, READ_SCOPES
from app.http_identity import BearerGrant, BearerRegistry, token_digest
from app.market_source_store import MarketSourceStore
from test_api_runtime import config, dependencies
from test_api_serve import tls_files
from test_api_crop_replay import CROP_POLICY
from test_crop_result_store import (crop_setup, authoring, farm_setup, login_scope,
    login_database, PROFILE, NOTICE, KEY, raw, put, count)
from test_market_hold_store import context_verifier
from web_shell_smoke import frontend, WEB


@pytest.mark.parametrize('login_scope', [CROP_POLICY], indirect=True)
def test_saved_crop_research_actual_https_webgl_current_rights_and_account(crop_setup, tls_files, tmp_path, monkeypatch):
    store, body, _, rights = crop_setup
    record = put(store, body)
    expected = project_crop_result(record).model_dump(mode='json')
    held_body = deepcopy(body)
    held_body['revision'] = 'web-numeric-hold'
    held_body['program']['initial_state']['values']['buffer']['value'] = 0
    held_body['program']['segments'][0]['forcing']['values']['par_above_canopy']['value'] = 0
    held_body['rights']['program_sha256'] = sha256(raw(held_body['program'])).hexdigest()
    held = project_crop_result(put(store, held_body)).model_dump(mode='json')
    assert held['status'] == 'hold' and held['hold']['reason_code'] == 'DEPLETED_STATE_HOLD'
    jobs = store.jobs
    replay = store.farms.replay
    research = replay.owned_research
    holds = replay.thermal.holds
    cert, key, _ = tls_files
    now = datetime.now(timezone.utc)
    tokens = {name: ('synthetic-crop-web-' + name + '-' + 'w' * 32).encode() for name in ('owner', 'denied')}
    grants = tuple(BearerGrant(token_digest(tokens[name]), 'tenant-1', frozenset(scopes),
        now - timedelta(seconds=1), now + timedelta(minutes=15)) for name, scopes in
        [('owner', set(READ_SCOPES)), ('denied', set(READ_SCOPES) - {'crop_result_read'})])

    def source_factory(*, principal_provider):
        return MarketSourceStore(jobs._dsn, jobs.schema, principal_provider=principal_provider,
            runtime_identity=jobs.runtime_identity)

    def crop_factory(*, farm_authoring_service):
        return CropResultStore(farm_authoring_service, PROFILE, NOTICE, program_rights=rights, integrity_key=KEY)

    descriptor = jobs._content_directory(create=True)
    os.close(descriptor)
    runtime = ApiRuntime(config(policy=jobs.runtime_identity[0], dsn=jobs._dsn,
        artifact_root=jobs.artifact_root, certificate=cert, private_key=key, port=0),
        dependencies(research_registry=research.catalog, bearer_registry=BearerRegistry(grants),
            owned_fixture_registry=research.registry, owned_research_contexts=dict(research._contexts),
            context_verifier=context_verifier, market_scope_resolver=holds._scope_resolver,
            market_source_factory=source_factory, crop_result_store_factory=crop_factory))
    before = count(store)
    monkeypatch.setattr('app.crop_result_store.integrate_crop', lambda **_: pytest.fail('browser GET reintegrated'))
    server = runtime.service.server()
    thread = threading.Thread(target=server.run, daemon=True)
    browser = None
    thread.start()
    try:
        deadline = time.monotonic() + 15
        while not server.started:
            assert thread.is_alive() and time.monotonic() < deadline
            time.sleep(.01)
        port = server.servers[0].sockets[0].getsockname()[1]
        with frontend(f'https://127.0.0.1:{port}', cert, key) as (web_port, _):
            env = {name: os.environ[name] for name in ('PATH', 'HOME', 'LANG', 'PLAYWRIGHT_BROWSERS_PATH') if name in os.environ}
            browser = subprocess.Popen(['node', 'e2e/real-crop-replay-smoke.mjs',
                f'https://127.0.0.1:{web_port}', str(tmp_path / 'screens')], cwd=WEB, env=env,
                stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            browser.stdin.write(json.dumps({'tokens': {k: v.decode() for k, v in tokens.items()},
                'result': expected, 'held': held}) + '\n')
            browser.stdin.flush()
            assert select.select([browser.stdout], [], [], 90)[0], 'crop browser did not verify saved geometry'
            first = browser.stdout.readline()
            if not first:
                _, errors = browser.communicate(timeout=5)
                pytest.fail('crop browser failed before geometry: ' + errors[-2500:])
            initial = json.loads(first)
            assert initial['stage'] == 'geometry_verified' and initial['sample_count'] == 6
            rights.allowed = False
            browser.stdin.write(json.dumps({'stage': 'rights_revoked'}) + '\n')
            browser.stdin.flush()
            assert select.select([browser.stdout], [], [], 45)[0], 'crop browser did not verify rights hold'
            denied = browser.stdout.readline()
            if not denied:
                _, errors = browser.communicate(timeout=5)
                pytest.fail('crop browser failed before rights hold: ' + errors[-2500:])
            assert json.loads(denied)['stage'] == 'rights_hold_verified'
            rights.allowed = True
            browser.stdin.write(json.dumps({'stage': 'rights_restored'}) + '\n')
            browser.stdin.flush()
            output, error = browser.communicate(timeout=90)
            assert browser.returncode == 0, error[-3000:]
            report = json.loads(output)
            assert report['stage'] == 'verified'
            assert [item['status'] for item in report['network']] == [200, 200, 200, 422, 403, 200]
            assert len(report['consumed']) == 4
            assert all(item['cache'] == 'no-store' and item['body_seconds'] < 30 for item in report['consumed'])
            assert count(store) == before
            with jobs.connect() as conn:
                assert conn.pgconn.used_password
            evidence = {'scope': 'synthetic_crop_math_only', 'actual_tls_scram': True,
                'result': expected, 'held': held, 'browser': report,
                'rows_before': before, 'rows_after': count(store), 'get_reintegration': False,
                'screens': str(tmp_path / 'screens'), 'frontend_stopped': True}
    finally:
        rights.allowed = True
        if browser is not None and browser.poll() is None:
            browser.kill()
            browser.communicate(timeout=5)
        server.should_exit = True
        thread.join(timeout=15)
        assert not thread.is_alive()
    evidence['https_server_joined'] = True
    Path('/tmp/ossf-crop-web-https-evidence-20261004.json').write_text(json.dumps(evidence, ensure_ascii=False, indent=2) + '\n')
    print('crop_replay_browser=' + json.dumps(report))
    print('crop_replay_screens=' + str(tmp_path / 'screens'))
