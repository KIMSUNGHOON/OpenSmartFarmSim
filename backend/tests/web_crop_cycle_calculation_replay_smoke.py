"""Manual registered synthetic calculation -> protected HTTPS -> same-UTC WebGL."""
from copy import deepcopy
from dataclasses import asdict
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
from types import SimpleNamespace
from urllib.parse import parse_qs

import pytest
from psycopg import sql

from app import api_crop_cycle_calculation_replay as public
from app import calculation_operator_config as loader
from app import crop_cycle_calculation_context as engine
from app import crop_cycle_calculation_current_query as current
from app import crop_cycle_calculation_result_store as storage
from app import crop_cycle_calculation_server_custody as custody
from app.crop_cycle_calculation_farm_binding import CalculationFarmBinding
from app.crop_cycle_calculation_result_evidence import CalculationResultEvidenceAuthority
from app.crop_result_store import READ_SCOPES, WRITE_SCOPES
from app.http_identity import BearerGrant, BearerRegistry, current_principal, token_digest
from app.market_source_store import MarketSourceStore
from app.thermal_run_store import _canonical
from test_api_crop_cycle_calculation_tls import (Inputs, Evidence, SERVER_KEY, DB_KEY, RESULT_KEY,
    audit_cleanup, custody_fds, fd_inventory, login_scope, original_login_scope,
    CycleFarmBinding, CycleServerCustody, CycleCropResultStore)
from test_crop_cycle_artifact import PROFILES, NOTICE
from test_crop_cycle_farm_binding import SyntheticInputRights
from test_crop_cycle_input_evidence import authority
from test_crop_startup_result_store import shifted
from test_farm_authoring_storage import authoring, request as farm_request
from test_farm_replay_scenario import farm_setup
from login_database import login_database
from test_operator_config import private_config, store as store_config
from test_api_runtime import config, dependencies
from test_api_serve import tls_files
from web_shell_smoke import frontend, WEB

pytestmark = pytest.mark.parametrize('original_login_scope', [{'market_calculation': True,
    'market_source_storage': True, 'thermal_scenario_storage': True, 'break_even_calculation': True,
    'crop_cycle_result_storage': True}], indirect=True)


def save(name, value):
    directory = Path(os.environ['OSSF_CALCULATION_NATIVE_EVIDENCE'])
    with (directory/name).open('x') as handle:
        os.fchmod(handle.fileno(), 0o400); json.dump(value, handle, indent=2, sort_keys=True)
        handle.write('\n'); handle.flush(); os.fsync(handle.fileno())


class HTTPObservation:
    def __init__(self, app):
        self.app = app; self.active = self.peak = 0; self.responses = []

    async def __call__(self, scope, receive, send):
        if scope['type'] != 'http' or not scope['path'].startswith('/v1/crop-cycle-calculation-research-results/'):
            return await self.app(scope, receive, send)
        self.active += 1; self.peak = max(self.peak, self.active)
        started = time.monotonic(); query = parse_qs(scope['query_string'].decode('ascii'))
        row = {'method': scope['method'], 'view': query.get('view', ['summary'])[0],
            'offset': query.get('offset', [None])[0], 'status': None, 'bytes': 0, 'complete': False}
        async def observed_send(message):
            if message['type'] == 'http.response.start': row['status'] = message['status']
            if message['type'] == 'http.response.body':
                row['bytes'] += len(message.get('body', b''))
                row['complete'] = not message.get('more_body', False)
            await send(message)
        try:
            return await self.app(scope, receive, observed_send)
        finally:
            row['seconds'] = time.monotonic()-started; self.responses.append(row); self.active -= 1


def test_registered_verified_25h_protected_TLS_original_values_webgl_and_cleanup(
        authoring, private_config, tls_files, tmp_path, monkeypatch):
    workspace = Path(__file__).resolve().parents[2]
    frozen = json.loads((workspace/'research/artifacts/web-crop-cycle-calculation-view-reference-20261008.json').read_text())
    for name, value in {**frozen['preserved_source_sha256'], **frozen['source_sha256']}.items():
        assert sha256((workspace/name).read_bytes()).hexdigest() == value, name
    fixture_path = workspace/'web/e2e/calculation-cycle-crop-recorded-responses.json'
    assert sha256(fixture_path.read_bytes()).hexdigest() == 'a2d3e197b352bc51ab1dd66f520f38912032bb9a9e705733eb89919e47f4a80b'
    recorded = json.loads(fixture_path.read_text())['long']
    def stamp(value):
        return (datetime.fromisoformat(value.replace('Z', '+00:00'))+timedelta(days=273)).isoformat().replace('+00:00', 'Z')
    baseline = {kind: [deepcopy(row) for response in recorded if response.get('page')
        and response['page']['kind'] == kind for row in response['page']['records']] for kind in ('samples', 'events')}
    for rows in baseline.values():
        for row in rows: row['at'] = stamp(row['at'])
    assert len(baseline['samples']) == 27 and len(baseline['events']) == 5
    spec = importlib.util.spec_from_file_location('owned_verified_native_reference', workspace/'research/crop-cycle-stream-execution-reference.py')
    reference = importlib.util.module_from_spec(spec); spec.loader.exec_module(reference)
    long = reference.long_program()
    for segment in long['segments']:
        for key in ('start', 'end'): segment[key] = stamp(segment[key])
    for event in long['events']: event['at'] = stamp(event['at'])
    long['output_times'] = [stamp(value) for value in long['output_times']]
    past = shifted('positive-tail'); past['events'] = []; past['solver']['max_step_seconds'] = 1
    past['segments'][0]['removals']['values']['leaf']['value'] = 1e9
    empty = shifted('empty-entry'); empty['initial_state']['values']['temperature_sum']['value'] = 0
    programs = {'past': past, 'empty': empty, 'empty_completed': shifted('night-smooth'), 'long': long}
    farms, farm_body, principal = authoring
    registered = farms.submit('tenant-1', farm_request(farm_body)); principal['scopes'].update(WRITE_SCOPES)
    farm = {'scenario_id': farm_body['farm']['scenario_id'], 'scenario_revision': farm_body['farm']['scenario_revision'],
        'registration_sha256': registered.scenario_sha256, 'crop_id': 'crop-1'}
    jobs = farms.replay.jobs; research = farms.replay.owned_research
    input_authority = authority(); rights = SyntheticInputRights(); inputs = Inputs(); evidence = Evidence()
    owned_root = tmp_path/'verified-native'; owned_root.mkdir(mode=0o700)
    legacy_root = tmp_path/'unused-legacy'; legacy_root.mkdir(mode=0o700)
    binding = CalculationFarmBinding(farms, input_authority, input_rights=rights)
    server = custody.CalculationServerCustody(binding, owned_root, input_resolver=inputs, integrity_key=SERVER_KEY)
    store = storage.CalculationCycleCropResultStore(server, integrity_key=DB_KEY)
    issuer = CalculationResultEvidenceAuthority(input_authority, integrity_key=RESULT_KEY,
        issuer_id='owned-native-verified-results', key_id='result-v1')
    prepared_query = current.CalculationCurrentCycleQuery(store, issuer, evidence_resolver=evidence)
    results = {}; records = {}; execution = {}; source_paths = []
    for name, p in programs.items():
        expected = baseline if name == 'long' else engine.physical.integrate_plant_startup(**deepcopy(p), **PROFILES)
        if name == 'empty_completed': expected['samples'] = []
        expected_events = [{key: row[key] for key in ('at', 'before', 'after', 'removed')} for row in expected['events']]
        anchors = p.pop('output_times'); directory = tmp_path/('input-'+name); program_id = 'owned-native-verified-'+name
        packet = engine.inputs.write_input_packet(directory, **p, anchors=anchors,
            outputs=[] if name == 'empty_completed' else anchors, **PROFILES, program_id=program_id)
        for path in directory.iterdir(): path.chmod(0o400)
        proof = input_authority.issue(directory, packet['root_sha256'])
        inputs.values[packet['root_sha256']] = (directory, proof); source_paths.append(directory)
        intent = {'study_id': program_id, 'revision': 'r1', 'farm': farm,
            'input': {'schema_version': engine.inputs.VERSION, 'root_sha256': packet['root_sha256'], 'program_id': program_id},
            'rights': {'schema_version': 'crop-cycle-input-rights-v1', 'declaration_id': program_id, 'revision': 'r1',
                'input_root_sha256': packet['root_sha256'], 'available_at': farm_body['farm']['decision_at'], 'redistribute': False,
                **{key: True for key in ('ownership_asserted', 'access', 'store', 'transform', 'use', 'display')}}}
        started = time.monotonic(); advances = 0
        while True:
            progress = json.loads(server.advance('tenant-1', _canonical(intent), budget={'max_steps': 10000, 'max_transitions': 128})); advances += 1
            save(name+'-advance-'+str(advances)+'.json', {'steps': progress['steps'], 'status': progress['status'],
                'counts': progress['counts'], 'seconds': time.monotonic()-started, 'scope': 'owned_synthetic_registered_calculation'})
            if progress['status'] != 'yielded': break
        record = store.put('tenant-1', _canonical(intent)); records[name] = record
        result_root = owned_root/custody._intent_id('tenant-1', intent)/'artifact'
        result_proof = issuer.issue(result_root, progress['artifact_sha256'], directory, packet['root_sha256'], proof)
        evidence.values[record['result_id']] = {'input_directory': directory, 'input_evidence_raw': proof, 'result_evidence_raw': result_proof}
        prepared = prepared_query.read('tenant-1', record['result_id'], farm)
        assert prepared['record'] == record
        terminal = prepared['terminal']
        summary = public.project_calculation_cycle_result(record, terminal).model_dump(mode='json')
        results[name] = {'summary': summary, 'samples': expected['samples'], 'events': expected_events}
        assert summary['reference']['sample_count'] == len(expected['samples']) and summary['reference']['event_count'] == len(expected_events)
        if name == 'long': assert progress['status'] == 'completed' and progress['steps'] == 11400
        elif name == 'past': assert len(expected['samples']) == 1 and summary['summary']['hold']['at'].endswith('.500000Z')
        elif name == 'empty': assert progress['status'] == 'hold' and expected['samples'] == []
        else: assert progress['status'] == 'completed' and progress['steps'] == 120 and expected['samples'] == []
        execution[name] = {'seconds': time.monotonic()-started, 'advances': advances, 'steps': progress['steps'],
            'status': progress['status'], 'input_root_sha256': packet['root_sha256'], 'input_evidence_sha256': sha256(proof).hexdigest(),
            'result_evidence_sha256': sha256(result_proof).hexdigest(), 'result_id': record['result_id']}
        save('prepared-'+name+'.json', execution[name])
    descriptor = jobs._content_directory(create=True); os.close(descriptor)
    now = datetime.now(timezone.utc); tokens = {name: ('owned-native-calculation-'+name+'-'+'n'*32).encode() for name in ('owner', 'denied')}
    grants = tuple(BearerGrant(token_digest(tokens[name]), 'tenant-1', frozenset(scopes), now-timedelta(seconds=1),
        now+timedelta(hours=1)) for name, scopes in [('owner', READ_SCOPES), ('denied', READ_SCOPES[:-1])])
    def sources(*, principal_provider):
        return MarketSourceStore(jobs._dsn, jobs.schema, principal_provider=principal_provider, runtime_identity=jobs.runtime_identity)
    def crops(*, farm_authoring_service):
        bound = CalculationFarmBinding(farm_authoring_service, input_authority, input_rights=rights)
        selected = custody.CalculationServerCustody(bound, owned_root, input_resolver=inputs, integrity_key=SERVER_KEY)
        return storage.CalculationCycleCropResultStore(selected, integrity_key=DB_KEY)
    def queries(*, result_store): return current.CalculationCurrentCycleQuery(result_store, issuer, evidence_resolver=evidence)
    class UnusedLegacy:
        version = 'owned-native-unused-legacy-v1'
        def __call__(self, *args, **kwargs): pytest.fail('verified browser used original calculation resolver')
    def legacy(*, farm_authoring_service):
        bound = CycleFarmBinding(farm_authoring_service, **PROFILES, notice_raw=NOTICE, input_rights=rights)
        return CycleCropResultStore(CycleServerCustody(bound, legacy_root, input_resolver=UnusedLegacy(), integrity_key=SERVER_KEY), integrity_key=DB_KEY)
    certificate, private_key, _ = tls_files
    cfg = config(policy=jobs.runtime_identity[0], dsn=jobs._dsn, artifact_root=jobs.artifact_root,
        certificate=certificate, private_key=private_key, port=0)
    deps = dependencies(research_registry=research.catalog, bearer_registry=BearerRegistry(grants), owned_fixture_registry=research.registry,
        owned_research_contexts=dict(research._contexts), market_scope_resolver=farms.replay.thermal.holds._scope_resolver,
        market_source_factory=sources, crop_cycle_result_store_factory=legacy,
        crop_cycle_calculation_result_store_factory=crops, crop_cycle_calculation_current_query_factory=queries)
    path, doc = private_config
    doc.update(config_version='operator-calculation-api-config-v1', policy=asdict(cfg.policy), artifact_root=str(cfg.artifact_root),
        certificate=str(certificate), private_key=str(private_key), port=0)
    Path(doc['dsn_file']).write_text(cfg.dsn); Path(doc['thermal_gate_key_file']).write_bytes(cfg.thermal_gate_key)
    Path(doc['market_hold_key_file']).write_bytes(cfg.market_hold_key); store_config(path, doc)
    def factory(*, config): assert config == cfg; return deps
    monkeypatch.setitem(sys.modules, 'trusted_operator', SimpleNamespace(dependencies=factory))
    def forbidden(*args, **kwargs): pytest.fail('browser GET parsed/calculated/QC/issued/published crop output')
    for module, name in ((engine.inputs, 'open_input_packet'), (engine.legacy, 'prepare_context'), (engine, 'open_calculation_context'),
            (engine, 'advance_chunk'), (engine.short._Evaluator, 'rhs'), (storage.artifact, 'open_artifact'),
            (storage.artifact._Files, '_load_prefix'), (storage.artifact, '_validate_delta'), (custody._Journal, '__init__'),
            (custody.CalculationServerCustody, 'advance'), (storage.CalculationCycleCropResultStore, 'put'),
            (engine.evidence.InputEvidenceAuthority, 'issue'), (CalculationResultEvidenceAuthority, 'issue')):
        monkeypatch.setattr(module, name, forbidden)
    selected = loader.load_calculation_api_runtime(path)
    assert selected.calculation_cycle_crop_results.jobs is selected.jobs
    assert selected.calculation_cycle_crop_query.store is selected.calculation_cycle_crop_results
    https = selected.service.server(); observed = HTTPObservation(https.config.app); https.config.app = observed
    paths = [owned_root, *source_paths]
    def counts():
        with jobs.connect() as conn:
            return {name: conn.execute(sql.SQL('SELECT count(*) AS n FROM {}').format(jobs._table(name))).fetchone()['n']
                for name in ('jobs', 'job_events', storage.schema.TABLE, 'thermal_g1_runs')}
    def files():
        selected_paths = [path, cfg.certificate, cfg.private_key, *(Path(doc[key]) for key in ('dsn_file', 'thermal_gate_key_file', 'market_hold_key_file'))]
        selected_paths.extend(file for directory in paths for file in directory.rglob('*') if file.is_file())
        return {str(file): (sha256(file.read_bytes()).hexdigest(), file.stat().st_mode, file.stat().st_ino) for file in selected_paths}
    before = counts(); files_before = files(); fds_before = fd_inventory()
    assert before[storage.schema.TABLE] == 4 and before['thermal_g1_runs'] == 0
    thread = threading.Thread(target=https.run, daemon=True); browser = None; thread.start()
    entry = evidence.values[records['long']['result_id']]; original_proof = entry['result_evidence_raw']
    try:
        deadline = time.monotonic()+15
        while not https.started: assert thread.is_alive() and time.monotonic() < deadline; time.sleep(.01)
        port = https.servers[0].sockets[0].getsockname()[1]
        with frontend(f'https://127.0.0.1:{port}', certificate, private_key) as (web_port, _):
            env = {name: os.environ[name] for name in ('PATH', 'HOME', 'LANG', 'PLAYWRIGHT_BROWSERS_PATH', 'TMPDIR') if name in os.environ}
            screens = Path(os.environ['OSSF_CALCULATION_NATIVE_EVIDENCE'])/'screens'
            browser = subprocess.Popen(['node', 'e2e/real-cycle-crop-replay-smoke.mjs', f'https://127.0.0.1:{web_port}', str(screens)],
                cwd=WEB, env=env, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            def send(value): browser.stdin.write(json.dumps(value)+'\n'); browser.stdin.flush()
            def receive(stage, timeout):
                assert select.select([browser.stdout], [], [], timeout)[0], 'native browser protocol deadline: '+stage
                line = browser.stdout.readline()
                if not line:
                    _, error = browser.communicate(timeout=5); pytest.fail('native browser ended at '+stage+': '+error[-4000:])
                value = json.loads(line); assert value['stage'] == stage
                save('browser-stage-'+stage+'.json', {'stage': stage, 'observed_at_utc': datetime.now(timezone.utc).isoformat()})
                return value
            send({'format': 'calculation-cycle', 'tokens': {k: v.decode() for k, v in tokens.items()}, 'results': results})
            receive('geometry_verified', 480); rights.allowed = False; send({'stage': 'rights_revoked'})
            receive('rights_hold_verified', 45); rights.allowed = True; send({'stage': 'rights_restored'})
            receive('tamper_ready', 120)
            tampered = json.loads(original_proof); tampered['payload']['summary']['steps'] += 1
            tampered['hmac_sha256'] = issuer._signature(tampered['payload']); entry['result_evidence_raw'] = _canonical(tampered)
            send({'stage': 'result_tampered'}); receive('tamper_hold_verified', 45)
            entry['result_evidence_raw'] = original_proof; send({'stage': 'result_restored'}); report = receive('verified', 120)
            _, error = browser.communicate(timeout=15); assert browser.returncode == 0, error[-4000:]
            assert report['original_samples_verified'] == 27 and report['original_events_verified'] == 5
            assert report['max_active_reads'] == 1 and report['lifecycle']['unmount_zero'] and report['errors'] == []
            assert report['actual_WebGL_loss_restore'] and report['reduced_motion_keyboard'] and report['result_tamper_protocol']
            successful = [row for row in report['network'] if row['status'] == 200]
            assert all(row['outcome'] == 'complete' and row['seconds'] < 30 and row['bytes'] <= public.MAX_RESPONSE_BYTES
                and row['cache'] == 'no-store' for row in successful)
            assert [row['status'] for row in report['network']].count(422) == 2 and [row['status'] for row in report['network']].count(403) == 1
            assert observed.peak == 1 and observed.active == 0 and len(observed.responses) == len(report['network'])
            assert all(row['complete'] and row['seconds'] < 30 and row['bytes'] <= public.MAX_RESPONSE_BYTES for row in observed.responses)
            assert counts() == before and files() == files_before and custody_fds(paths) == 0 and current_principal() is None
            with jobs.connect() as conn: assert conn.pgconn.used_password and conn.info.get_parameters()['require_auth'] == 'scram-sha-256'
    finally:
        rights.allowed = True; entry['result_evidence_raw'] = original_proof
        if browser is not None and browser.poll() is None: browser.kill(); browser.communicate(timeout=5)
        https.should_exit = True; thread.join(15); assert not thread.is_alive()
    assert all(context.reader.closed for context in inputs.opened)
    assert fd_inventory() == fds_before and counts() == before and files() == files_before
    save('native-verified.json', {'scope': 'registered_owned_synthetic_25h_protected_TLS_WebGL_not_farm_validation',
        'execution': execution, 'numeric_baseline_fixture_sha256': sha256(fixture_path.read_bytes()).hexdigest(),
        'UTC_shift_days': 273, 'baseline_numeric_values_unchanged': True, 'public_results': results, 'browser': report,
        'server_ASGI_max_active': observed.peak, 'server_ASGI_active_after': observed.active, 'server_HTTP_responses': observed.responses,
        'rows_before': before, 'rows_after': counts(), 'read_math_parser_QC_issue_publication_calls': 0,
        'input_config_custody_files_unchanged': True, 'custody_fds_after': 0, 'FD_targets_devices_inodes_identical': True,
        'HTTPS_joined': True, 'frontend_stopped': True, 'actual_SCRAM': True, 'protected_loader': True,
        'gates': 'not_assessed', 'actual_measured_crop_Runs': 0, 'domestic_independent_datasets': 0})
