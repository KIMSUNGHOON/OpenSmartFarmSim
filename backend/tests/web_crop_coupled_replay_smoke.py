"""Own synthetic SCRAM custody -> normal HTTPS/Bearer -> actual 50 C/N WebGL."""
from copy import deepcopy
from datetime import datetime, timedelta, timezone
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
from app.api_runtime import ApiRuntime
from app.crop_coupled_result_store import CoupledCropResultStore, READ_SCOPES
from app.http_identity import BearerGrant, BearerRegistry, token_digest
from app.market_source_store import MarketSourceStore
from test_api_runtime import config, dependencies
from test_api_serve import tls_files
from test_api_crop_coupled_replay import CROP_POLICY, project
from test_crop_coupled_result_store import (coupled_setup, authoring, farm_setup, login_scope,
    login_database, PROFILES, NOTICE, KEY, put, count, update_rights)
from test_market_hold_store import context_verifier
from web_shell_smoke import frontend, WEB


@pytest.mark.parametrize('login_scope', [CROP_POLICY], indirect=True)
def test_saved_coupled_crop_https_webgl_past_empty_hold_rights_account_cleanup(coupled_setup, tls_files, tmp_path, monkeypatch):
    store, body, _, rights = coupled_setup
    record = put(store, body); expected = project(record)
    past_body = deepcopy(body); past_body['revision'] = 'web-fractional-hold'
    past_body['program']['events'] = []; past_body['program']['solver']['max_step_seconds'] = 1
    past_body['program']['segments'][0]['removals']['values']['leaf']['value'] = 1e9
    update_rights(past_body); past = project(put(store, past_body))
    empty_body = deepcopy(body); empty_body['revision'] = 'web-empty-hold'
    empty_body['program']['initial_state']['values']['buffer']['value'] = 0
    empty_body['program']['segments'][0]['forcing']['values']['par_above_canopy']['value'] = 0
    update_rights(empty_body); empty = project(put(store, empty_body))
    assert expected['status'] == 'completed' and len(expected['samples']) == 6
    assert past['status'] == 'hold' and len(past['samples']) == 1 and past['hold']['at'].endswith('.500000Z')
    assert empty['status'] == 'hold' and empty['samples'] == []
    jobs = store.jobs; replay = store.farms.replay; research = replay.owned_research
    cert, key, _ = tls_files; now = datetime.now(timezone.utc)
    tokens = {name: ('synthetic-coupled-web-' + name + '-' + 'w' * 32).encode() for name in ('owner', 'denied')}
    grants = tuple(BearerGrant(token_digest(tokens[name]), 'tenant-1', frozenset(scopes),
        now - timedelta(seconds=1), now + timedelta(minutes=15)) for name, scopes in
        [('owner', set(READ_SCOPES)), ('denied', set(READ_SCOPES) - {'crop_result_read'})])

    def source_factory(*, principal_provider):
        return MarketSourceStore(jobs._dsn, jobs.schema, principal_provider=principal_provider, runtime_identity=jobs.runtime_identity)

    def crop_factory(*, farm_authoring_service):
        return CoupledCropResultStore(farm_authoring_service, **PROFILES, notice_raw=NOTICE, program_rights=rights, integrity_key=KEY)

    descriptor = jobs._content_directory(create=True); os.close(descriptor)
    runtime = ApiRuntime(config(policy=jobs.runtime_identity[0], dsn=jobs._dsn,
        artifact_root=jobs.artifact_root, certificate=cert, private_key=key, port=0),
        dependencies(research_registry=research.catalog, bearer_registry=BearerRegistry(grants),
            owned_fixture_registry=research.registry, owned_research_contexts=dict(research._contexts),
            context_verifier=context_verifier, market_scope_resolver=replay.thermal.holds._scope_resolver,
            market_source_factory=source_factory, crop_coupled_result_store_factory=crop_factory))
    before = count(store)
    monkeypatch.setattr('app.crop_coupled_artifact.integration.integrate_plant_cohorts', lambda **_: pytest.fail('browser GET reintegrated'))
    monkeypatch.setattr('app.crop_coupled_result_store.calculate_coupled_artifact', lambda *a, **k: pytest.fail('browser GET calculated'))
    server = runtime.service.server(); thread = threading.Thread(target=server.run, daemon=True); browser = None; thread.start()
    try:
        deadline = time.monotonic() + 15
        while not server.started:
            assert thread.is_alive() and time.monotonic() < deadline; time.sleep(.01)
        port = server.servers[0].sockets[0].getsockname()[1]
        with frontend(f'https://127.0.0.1:{port}', cert, key) as (web_port, _):
            env = {name: os.environ[name] for name in ('PATH', 'HOME', 'LANG', 'PLAYWRIGHT_BROWSERS_PATH') if name in os.environ}
            browser = subprocess.Popen(['node', 'e2e/real-coupled-crop-replay-smoke.mjs', f'https://127.0.0.1:{web_port}', str(tmp_path / 'screens')],
                cwd=WEB, env=env, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            browser.stdin.write(json.dumps({'tokens': {k: v.decode() for k, v in tokens.items()}, 'result': expected, 'past': past, 'empty': empty}) + '\n'); browser.stdin.flush()
            assert select.select([browser.stdout], [], [], 120)[0], 'coupled browser did not verify geometry'
            first = browser.stdout.readline()
            if not first:
                _, errors = browser.communicate(timeout=5); pytest.fail('coupled browser failed before geometry: ' + errors[-2500:])
            assert json.loads(first) == {'stage': 'geometry_verified', 'sample_count': 6}
            rights.allowed = False; browser.stdin.write(json.dumps({'stage': 'rights_revoked'}) + '\n'); browser.stdin.flush()
            assert select.select([browser.stdout], [], [], 45)[0], 'coupled browser did not verify rights hold'
            denied = browser.stdout.readline()
            if not denied:
                _, errors = browser.communicate(timeout=5); pytest.fail('coupled browser failed before rights hold: ' + errors[-2500:])
            assert json.loads(denied)['stage'] == 'rights_hold_verified'
            rights.allowed = True; browser.stdin.write(json.dumps({'stage': 'rights_restored'}) + '\n'); browser.stdin.flush()
            output, error = browser.communicate(timeout=90); assert browser.returncode == 0, error[-3000:]
            report = json.loads(output); assert report['stage'] == 'verified'
            assert [item['status'] for item in report['network']] == [200, 200, 200, 200, 422, 403, 200]
            assert len(report['consumed']) == 5
            assert all(item['cache'] == 'no-store' and item['body_seconds'] < 30 for item in report['consumed'])
            assert count(store) == before
            with jobs.connect() as conn:
                assert conn.pgconn.used_password
            evidence = {'scope': 'synthetic_crop_math_only', 'actual_tls_scram': True, 'result': expected, 'past': past,
                'empty': empty, 'browser': report, 'rows_before': before, 'rows_after': count(store), 'get_reintegration': False,
                'screens': str(tmp_path / 'screens'), 'frontend_stopped': True}
    finally:
        rights.allowed = True
        if browser is not None and browser.poll() is None: browser.kill(); browser.communicate(timeout=5)
        server.should_exit = True; thread.join(timeout=15); assert not thread.is_alive()
    evidence['https_server_joined'] = True
    Path('/tmp/ossf-coupled-crop-web-https-evidence-20261005.json').write_text(json.dumps(evidence, ensure_ascii=False, indent=2) + '\n')
    print('coupled_crop_browser_verified=' + json.dumps({'result_id': expected['result_id'], 'sample_count': 6, 'network_statuses': [x['status'] for x in report['network']]}))
