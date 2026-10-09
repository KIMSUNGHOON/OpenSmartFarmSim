"""Manual native SCRAM -> HTTPS -> bounded WebGL proof; own synthetic inputs only."""
from copy import deepcopy
from datetime import datetime, timedelta, timezone
from hashlib import sha256
import importlib.util
import json
import os
from pathlib import Path
import select
import subprocess
import sys
import threading
import time

import pytest
from psycopg import sql

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from app import api_crop_cycle_replay as public
from app import crop_cycle_result_store as storage
from app import crop_cycle_server_custody as custody
from app import crop_cycle_input_stream as inputs
from app import crop_cycle_stream_execution as engine
from app.crop_cycle_farm_binding import CycleFarmBinding
from app.api_runtime import ApiRuntime
from app.http_identity import BearerGrant, BearerRegistry, current_principal, token_digest
from app.market_source_store import MarketSourceStore
from app.thermal_run_store import _canonical
from test_crop_cycle_server_custody_farms import server_setup, KEY, BUDGET
from test_crop_cycle_result_store_farms import DB_KEY
from test_crop_cycle_artifact import PROFILES, NOTICE
from test_crop_startup_result_store import shifted
from test_api_crop_cycle_tls import OwnInputs, custody_fds
from test_farm_authoring_storage import authoring
from test_farm_replay_scenario import farm_setup
from login_database import login_database, login_scope
from test_api_runtime import config, dependencies
from test_api_serve import tls_files
from test_market_hold_store import context_verifier
from web_shell_smoke import frontend, WEB

POLICY = {'market_calculation': True, 'market_source_storage': True,
          'thermal_scenario_storage': True, 'break_even_calculation': True,
          'crop_cycle_result_storage': True}


@pytest.mark.parametrize('login_scope', [POLICY], indirect=True)
def test_fresh_25h_scram_tls_original_pages_webgl_rights_holds_and_cleanup(server_setup, request, tmp_path, monkeypatch):
    root = Path(__file__).resolve().parents[2]
    frozen = json.loads((root / 'research/artifacts/crop-cycle-api-runtime-long-reference-20261006.json').read_bytes())
    for name, digest in frozen['frozen_current49_sha256'].items():
        assert sha256((root / name).read_bytes()).hexdigest() == digest, name
    recorded_path = root / 'web/e2e/cycle-crop-recorded-responses.json'
    assert sha256(recorded_path.read_bytes()).hexdigest() == '43fad7bf11f43a2fd92ed04323a024848b1e8d086add391e0a714016a3e3c990'
    recorded = json.loads(recorded_path.read_bytes())['long']
    baseline_samples = [row for response in recorded[1:5] for row in response['page']['records']]
    baseline_events = [row for response in recorded[6:9] for row in response['page']['records']]
    assert len(baseline_samples) == 27 and len(baseline_events) == 5
    initial, raw, rights, _, _ = server_setup
    original_body = json.loads(raw)
    spec = importlib.util.spec_from_file_location('cycle_web_long_reference', root / 'research/crop-cycle-stream-execution-reference.py')
    reference = importlib.util.module_from_spec(spec); spec.loader.exec_module(reference)
    candidate = reference.long_program()
    def stamp(value):
        return (datetime.fromisoformat(value.replace('Z', '+00:00')) + timedelta(days=273)).isoformat().replace('+00:00', 'Z')
    for segment in candidate['segments']:
        for key in ('start', 'end'): segment[key] = stamp(segment[key])
    for event in candidate['events']: event['at'] = stamp(event['at'])
    candidate['output_times'] = [stamp(t) for t in candidate['output_times']]
    programs = {'long': candidate}
    past = shifted('positive-tail'); past['events'] = []; past['solver']['max_step_seconds'] = 1
    past['segments'][0]['removals']['values']['leaf']['value'] = 1e9
    programs['past'] = past
    empty = shifted('positive-tail'); empty['initial_state']['values']['buffer']['value'] = 0
    empty['segments'][0]['forcing']['values']['par_above_canopy']['value'] = 0
    programs['empty'] = empty
    programs['empty_completed'] = shifted()
    programs = {name: programs[name] for name in ('past', 'empty', 'empty_completed', 'long')}
    bodies, paths = {}, {}
    for name, program in programs.items():
        program = deepcopy(program); anchors = program.pop('output_times')
        program_id = 'own-http-long-cycle' if name == 'long' else 'own-web-cycle-' + name
        directory = tmp_path / (name + '-input')
        packet = inputs.write_input_packet(directory, **program, anchors=anchors,
            outputs=[] if name == 'empty_completed' else anchors, **PROFILES, program_id=program_id)
        body = deepcopy(original_body)
        body['revision'] = 'web-' + name
        body['input'].update(root_sha256=packet['root_sha256'], program_id=program_id)
        body['rights']['input_root_sha256'] = packet['root_sha256']
        bodies[name] = _canonical(body); paths[packet['root_sha256']] = directory
    assert json.loads(bodies['long'])['input']['root_sha256'] == recorded[0]['reference']['input_root_sha256']
    owned_root = tmp_path / 'web-custody'; owned_root.mkdir(mode=0o700)
    resolver = OwnInputs(paths)
    service = custody.CycleServerCustody(initial.binding, owned_root, input_resolver=resolver, integrity_key=KEY)
    store = storage.CycleCropResultStore(service, integrity_key=DB_KEY)
    results, execution = {}, {}
    progress_path = Path('/tmp/ossf-cycle-web-native-progress-20261006.json')
    started = time.monotonic()
    for name, intent in bodies.items():
        tick = time.monotonic(); advances = 0
        while True:
            progress = json.loads(service.advance('tenant-1', intent, budget=BUDGET)); advances += 1
            progress_path.write_text(json.dumps({'phase': 'calculation', 'program': name,
                'advances': advances, 'status': progress['status'], 'steps': progress['steps'],
                'elapsed_seconds': time.monotonic() - started, 'gates': 'not_assessed'}) + '\n')
            if progress['status'] != 'yielded': break
        record = store.put('tenant-1', intent)
        farm = json.loads(intent)['farm']
        summary = json.loads(public._read_cycle_response(store, 'tenant-1', record['result_id'], farm, 'summary', None, None))
        if name == 'long':
            assert progress['status'] == 'completed' and progress['steps'] == 11400
            assert summary['reference']['sample_count'] == 27 and summary['reference']['event_count'] == 5
            samples, events = baseline_samples, baseline_events
        else:
            samples = json.loads(public._read_cycle_response(store, 'tenant-1', record['result_id'], farm, 'samples', 0, 7))['page']['records']
            events = json.loads(public._read_cycle_response(store, 'tenant-1', record['result_id'], farm, 'events', 0, 2))['page']['records']
        results[name] = {'summary': summary, 'samples': samples, 'events': events}
        execution[name] = {'seconds': time.monotonic() - tick, 'advances': advances, 'steps': progress['steps'], 'status': progress['status']}
    assert len(results['past']['samples']) == 1 and results['past']['summary']['summary']['hold']['at'].endswith('.500000Z')
    assert results['empty']['samples'] == [] and results['empty']['summary']['summary']['status'] == 'hold'
    assert results['empty_completed']['samples'] == [] and results['empty_completed']['summary']['summary']['status'] == 'completed'
    jobs = store.jobs; replay = service.binding.farms.replay; research = replay.owned_research
    def rows():
        with jobs.connect() as conn:
            return conn.execute(sql.SQL('SELECT count(*) AS n FROM {}').format(jobs._table(storage.schema.TABLE))).fetchone()['n']
    before = rows(); assert before == 4
    def forbidden(*args, **kwargs): pytest.fail('browser GET executed crop equations')
    monkeypatch.setattr(engine, 'advance_chunk', forbidden)
    monkeypatch.setattr(engine.short._Evaluator, 'rhs', forbidden)
    cert, key, _ = request.getfixturevalue('tls_files')
    now = datetime.now(timezone.utc)
    tokens = {name: ('own-cycle-web-' + name + '-' + 'w' * 32).encode() for name in ('owner', 'denied')}
    grants = tuple(BearerGrant(token_digest(tokens[name]), 'tenant-1', frozenset(scopes), now - timedelta(seconds=1),
        now + timedelta(hours=1)) for name, scopes in [('owner', set(public.READ_SCOPES)),
        ('denied', set(public.READ_SCOPES) - {'crop_result_read'})])
    def sources(*, principal_provider):
        return MarketSourceStore(jobs._dsn, jobs.schema, principal_provider=principal_provider, runtime_identity=jobs.runtime_identity)
    def crops(*, farm_authoring_service):
        binding = CycleFarmBinding(farm_authoring_service, **PROFILES, notice_raw=NOTICE, input_rights=rights)
        server = custody.CycleServerCustody(binding, owned_root, input_resolver=resolver, integrity_key=KEY)
        return storage.CycleCropResultStore(server, integrity_key=DB_KEY)
    descriptor = jobs._content_directory(create=True); os.close(descriptor)
    runtime = ApiRuntime(config(policy=jobs.runtime_identity[0], dsn=jobs._dsn, artifact_root=jobs.artifact_root,
        certificate=cert, private_key=key, port=0), dependencies(research_registry=research.catalog,
        bearer_registry=BearerRegistry(grants), owned_fixture_registry=research.registry,
        owned_research_contexts=dict(research._contexts), context_verifier=context_verifier,
        market_scope_resolver=replay.thermal.holds._scope_resolver,
        market_source_factory=sources, crop_cycle_result_store_factory=crops))
    https = runtime.service.server(); thread = threading.Thread(target=https.run, daemon=True)
    browser = None; thread.start()
    try:
        deadline = time.monotonic() + 15
        while not https.started:
            assert thread.is_alive() and time.monotonic() < deadline; time.sleep(.01)
        port = https.servers[0].sockets[0].getsockname()[1]
        with frontend(f'https://127.0.0.1:{port}', cert, key) as (web_port, _):
            environment = {name: os.environ[name] for name in ('PATH', 'HOME', 'LANG', 'PLAYWRIGHT_BROWSERS_PATH') if name in os.environ}
            browser = subprocess.Popen(['node', 'e2e/real-cycle-crop-replay-smoke.mjs', f'https://127.0.0.1:{web_port}', str(tmp_path / 'screens')],
                cwd=WEB, env=environment, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            def send(value): browser.stdin.write(json.dumps(value) + '\n'); browser.stdin.flush()
            def receive(timeout, stage):
                assert select.select([browser.stdout], [], [], timeout)[0], 'browser protocol deadline: ' + stage
                line = browser.stdout.readline()
                if not line:
                    _, errors = browser.communicate(timeout=5)
                    pytest.fail('cycle browser failed at ' + stage + ': ' + errors[-4000:])
                value = json.loads(line)
                progress_path.write_text(json.dumps({'phase': 'browser', 'stage': value['stage'], 'elapsed_seconds': time.monotonic()-started}) + '\n')
                assert value['stage'] == stage
                return value
            send({'tokens': {k: v.decode() for k, v in tokens.items()}, 'results': results})
            receive(480, 'geometry_verified')
            rights.allowed = False; send({'stage': 'rights_revoked'})
            receive(45, 'rights_hold_verified')
            rights.allowed = True; send({'stage': 'rights_restored'})
            report = receive(120, 'verified')
            _, error = browser.communicate(timeout=15); assert browser.returncode == 0, error[-4000:]
            assert report['original_samples_verified'] == 27 and report['original_events_verified'] == 5
            assert report['max_active_reads'] == 1 and report['lifecycle']['unmount_zero']
            assert report['errors'] == [] and [item['status'] for item in report['network']].count(422) == 1
            assert [item['status'] for item in report['network']].count(403) == 1
            successful = [item for item in report['network'] if item['status'] == 200]
            assert all(item['outcome'] == 'complete' and item['seconds'] < 30 and item['bytes'] <= public.MAX_RESPONSE_BYTES
                and item['cache'] == 'no-store' for item in successful)
            assert rows() == before and custody_fds([owned_root, *paths.values()]) == 0 and current_principal() is None
            with jobs.connect() as conn: assert conn.pgconn.used_password
            evidence = {'scope': 'fresh_registered_synthetic_25h_SCRAM_TLS_WebGL_software_only',
                'actual_tls_scram': True, 'frozen49_verified': True,
                'numeric_baseline': 'immutable_prior_HTTP_rows_verified_by_independent_control_flow_sharing_frozen_rates',
                'baseline_input_root_sha256': recorded[0]['reference']['input_root_sha256'],
                'fresh_independent_control_flow': False, 'execution': execution, 'results': results, 'browser': report,
                'rows_before': before, 'rows_after': rows(), 'rhs_during_browser': 0,
                'custody_fds_after': 0, 'screens': str(tmp_path / 'screens'), 'frontend_stopped': True,
                'gates': 'not_assessed', 'actual_crop_runs': 0, 'domestic_independent_datasets': 0}
    finally:
        rights.allowed = True
        if browser is not None and browser.poll() is None: browser.kill(); browser.communicate(timeout=5)
        https.should_exit = True; thread.join(15); assert not thread.is_alive()
    evidence['https_server_joined'] = True
    Path('/tmp/ossf-cycle-crop-web-https-evidence-20261006.json').write_text(json.dumps(evidence, ensure_ascii=False, indent=2) + '\n')
    print('cycle_crop_browser_verified=' + json.dumps({'sample_count': 27, 'event_count': 5,
        'responses': len(report['network']), 'rights_and_account_denied': True, 'lifecycle_zero': True}))
