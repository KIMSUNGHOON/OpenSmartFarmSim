"""Owned SCRAM and complete HTTPS bodies; no measured farm or forecast claim."""
from copy import deepcopy
from dataclasses import asdict, replace
from datetime import datetime, timedelta, timezone
from hashlib import sha256
import http.client
import json
import os
from pathlib import Path
import ssl
import threading
import time
from types import SimpleNamespace
from urllib.parse import urlencode
import sys

import psycopg
from psycopg import sql
import pytest

from app import calculation_operator_config as loader
from app import api_crop_cycle_calculation_replay as public
from app import crop_cycle_calculation_context as engine
from app import crop_cycle_calculation_result_store as storage
from app import crop_cycle_calculation_current_query as current
from app import crop_cycle_calculation_server_custody as custody
from app.crop_cycle_calculation_farm_binding import CalculationFarmBinding
from app.crop_cycle_calculation_result_evidence import CalculationResultEvidenceAuthority
from app.crop_cycle_farm_binding import CycleFarmBinding
from app.crop_cycle_result_store import CycleCropResultStore
from app.crop_cycle_server_custody import CycleServerCustody
from app.crop_result_store import READ_SCOPES, WRITE_SCOPES
from app.http_identity import BearerGrant, BearerRegistry, current_principal, token_digest
from app.market_source_store import MarketSourceStore
from app.thermal_run_store import _canonical
from test_api_runtime import config, dependencies
from test_api_serve import tls_files
from test_operator_config import private_config, store as store_config
from test_calculation_operator_config import calculation_config, calculation_assembly as construction_case
from test_crop_cycle_calculation_result_store_farms import login_scope, original_login_scope
from test_crop_cycle_artifact import PROFILES, NOTICE
from test_crop_cycle_farm_binding import SyntheticInputRights
from test_crop_cycle_input_evidence import authority
from test_crop_startup_result_store import shifted
from test_farm_authoring_storage import authoring, request as farm_request
from test_farm_replay_scenario import farm_setup
from login_database import login_database

SERVER_KEY = b'owned-calculation-https-server-' + b's' * 32
DB_KEY = b'owned-calculation-https-db-' + b'd' * 32
RESULT_KEY = b'owned-calculation-https-evidence-' + b'r' * 32
FLAG = 'crop_cycle_calculation_result_storage'
pytestmark = pytest.mark.parametrize('original_login_scope', [{'market_calculation': True,
    'market_source_storage': True, 'thermal_scenario_storage': True, 'break_even_calculation': True,
    'crop_cycle_result_storage': True}], indirect=True)


def save_reference(name, value):
    root = os.environ.get('OSSF_CALCULATION_TLS_EVIDENCE')
    if root:
        with (Path(root)/name).open('x') as handle:
            os.fchmod(handle.fileno(), 0o400); json.dump(value, handle, sort_keys=True, indent=2)
            handle.write('\n'); handle.flush(); os.fsync(handle.fileno())


@pytest.fixture(scope='module', autouse=True)
def audit_cleanup(login_database, tmp_path_factory):
    yield
    with psycopg.connect(login_database['admin']) as conn:
        schemas = conn.execute("SELECT count(*) FROM pg_namespace WHERE nspname ~ '^login_test_'").fetchone()[0]
        roles = conn.execute("SELECT count(*) FROM pg_roles WHERE rolname ~ '^login_(owner_|[0-9a-f]{32}_)'").fetchone()[0]
        directory = Path(conn.execute('SHOW data_directory').fetchone()[0])
    passfiles = list(tmp_path_factory.getbasetemp().rglob('*.pgpass'))
    methods = [line.split()[-1] for line in (directory/'pg_hba.conf').read_text().splitlines()
               if line.strip().startswith('host')]
    assert schemas == roles == len(passfiles) == 0 and methods and set(methods) == {'scram-sha-256'}
    save_reference('database-cleanup.json', {'schemas_after': schemas, 'roles_after': roles,
        'passfiles_after': len(passfiles), 'actual_host_auth_methods': methods})


class Inputs:
    version = 'owned-https-verified-inputs-v1'
    def __init__(self): self.values = {}; self.opened = []
    def __call__(self, root, *, authority):
        directory, proof = self.values[root]
        context = engine.open_calculation_context(directory, root, proof, authority=authority)
        self.opened.append(context)
        return context


class Evidence:
    version = 'owned-https-verified-results-v1'
    def __init__(self): self.values = {}
    def __call__(self, tenant, packet):
        assert tenant == 'tenant-1'
        return dict(self.values[packet['result_id']])


@pytest.fixture
def http_case(authoring, private_config, tmp_path, request, monkeypatch):
    farms, farm_body, principal = authoring
    registered = farms.submit('tenant-1', farm_request(farm_body)); principal['scopes'].update(WRITE_SCOPES)
    farm = {'scenario_id': farm_body['farm']['scenario_id'], 'scenario_revision': farm_body['farm']['scenario_revision'],
            'registration_sha256': registered.scenario_sha256, 'crop_id': 'crop-1'}
    jobs = farms.replay.jobs; research = farms.replay.owned_research
    input_authority = authority(); rights = SyntheticInputRights(); inputs = Inputs(); evidence = Evidence()
    binding = CalculationFarmBinding(farms, input_authority, input_rights=rights)
    root = tmp_path/'verified-server'; legacy_root = tmp_path/'legacy-server'
    root.mkdir(mode=0o700); legacy_root.mkdir(mode=0o700)
    server = custody.CalculationServerCustody(binding, root, input_resolver=inputs, integrity_key=SERVER_KEY)
    results = storage.CalculationCycleCropResultStore(server, integrity_key=DB_KEY)
    result_authority = CalculationResultEvidenceAuthority(input_authority, integrity_key=RESULT_KEY,
        issuer_id='owned-https-verified-results', key_id='result-v1')
    records = {}; expected = {}; terminals = {}; source_paths = []
    for name in ('managed', 'past', 'empty'):
        p = shifted('empty-entry' if name == 'empty' else 'full-removal-reentry')
        if name == 'past': p['events'][1]['removals']['values']['leaf']['value'] = 1e6
        elif name == 'empty': p['initial_state']['values']['temperature_sum']['value'] = 0
        expected[name] = engine.physical.integrate_plant_startup(**deepcopy(p), **PROFILES)
        anchors = p.pop('output_times'); directory = tmp_path/('inputs-' + name)
        packet = engine.inputs.write_input_packet(directory, **p, anchors=anchors, outputs=anchors,
            **PROFILES, program_id='owned-https-' + name)
        for path in directory.iterdir(): path.chmod(0o400)
        proof = input_authority.issue(directory, packet['root_sha256'])
        inputs.values[packet['root_sha256']] = (directory, proof); source_paths.append(directory)
        body = {'study_id': 'owned-https-' + name, 'revision': 'r1', 'farm': farm,
            'input': {'schema_version': engine.inputs.VERSION, 'root_sha256': packet['root_sha256'],
                      'program_id': 'owned-https-' + name},
            'rights': {'schema_version': 'crop-cycle-input-rights-v1', 'declaration_id': 'owned-https-' + name,
                'revision': 'r1', 'input_root_sha256': packet['root_sha256'],
                'available_at': farm_body['farm']['decision_at'], 'redistribute': False,
                **{key: True for key in ('ownership_asserted', 'access', 'store', 'transform', 'use', 'display')}}}
        started = time.monotonic()
        progress = json.loads(server.advance('tenant-1', _canonical(body),
            budget={'max_steps': 10000, 'max_transitions': 128}))
        record = results.put('tenant-1', _canonical(body)); records[name] = record
        result_directory = root/custody._intent_id('tenant-1', body)/'artifact'
        result_proof = result_authority.issue(result_directory, progress['artifact_sha256'],
            directory, packet['root_sha256'], proof)
        terminals[name] = json.loads(result_proof)['payload']['summary']
        evidence.values[record['result_id']] = {'input_directory': directory, 'input_evidence_raw': proof,
                                               'result_evidence_raw': result_proof}
        assert progress['status'] == expected[name]['status'] and progress['steps'] == expected[name]['steps']
        save_reference('prepared-' + name + '.json', {'seconds': time.monotonic() - started,
            'steps': progress['steps'], 'status': progress['status'], 'counts': progress['counts'],
            'input_evidence_sha256': sha256(proof).hexdigest(), 'result_evidence_sha256': sha256(result_proof).hexdigest()})
    assert all(context.reader.closed for context in inputs.opened)
    descriptor = jobs._content_directory(create=True); os.close(descriptor)
    certificate, private_key, _ = request.getfixturevalue('tls_files')
    cfg = config(policy=jobs.runtime_identity[0], dsn=jobs._dsn, artifact_root=jobs.artifact_root,
                 certificate=certificate, private_key=private_key, port=0)
    now = datetime.now(timezone.utc)
    tokens = {name: ('owned-verified-https-' + name + '-' + 't' * 32).encode()
              for name in ('owner', 'foreign', 'denied')}
    grants = tuple(BearerGrant(token_digest(tokens[name]), tenant, frozenset(scopes),
        now - timedelta(seconds=1), now + timedelta(hours=1)) for name, tenant, scopes in
        (('owner', 'tenant-1', READ_SCOPES), ('foreign', 'foreign', READ_SCOPES),
         ('denied', 'tenant-1', READ_SCOPES[:-1])))
    def source_factory(*, principal_provider):
        return MarketSourceStore(jobs._dsn, jobs.schema, principal_provider=principal_provider,
                                 runtime_identity=jobs.runtime_identity)
    def crop_factory(*, farm_authoring_service):
        bound = CalculationFarmBinding(farm_authoring_service, input_authority, input_rights=rights)
        selected = custody.CalculationServerCustody(bound, root, input_resolver=inputs, integrity_key=SERVER_KEY)
        return storage.CalculationCycleCropResultStore(selected, integrity_key=DB_KEY)
    def query_factory(*, result_store):
        return current.CalculationCurrentCycleQuery(result_store, result_authority, evidence_resolver=evidence)
    class UnusedLegacy:
        version = 'owned-https-unused-legacy-v1'
        def __call__(self, *args, **kwargs): pytest.fail('new HTTP route used legacy calculation')
    def legacy_factory(*, farm_authoring_service):
        bound = CycleFarmBinding(farm_authoring_service, **PROFILES, notice_raw=NOTICE, input_rights=rights)
        selected = CycleServerCustody(bound, legacy_root, input_resolver=UnusedLegacy(), integrity_key=SERVER_KEY)
        return CycleCropResultStore(selected, integrity_key=DB_KEY)
    deps = dependencies(research_registry=research.catalog, bearer_registry=BearerRegistry(grants),
        owned_fixture_registry=research.registry, owned_research_contexts=dict(research._contexts),
        market_scope_resolver=farms.replay.thermal.holds._scope_resolver, market_source_factory=source_factory,
        crop_cycle_result_store_factory=legacy_factory, crop_cycle_calculation_result_store_factory=crop_factory,
        crop_cycle_calculation_current_query_factory=query_factory)
    path, doc = private_config
    doc.update(config_version='operator-calculation-api-config-v1', policy=asdict(cfg.policy),
        artifact_root=str(cfg.artifact_root), certificate=str(certificate), private_key=str(private_key), port=0)
    Path(doc['dsn_file']).write_text(cfg.dsn)
    Path(doc['thermal_gate_key_file']).write_bytes(cfg.thermal_gate_key)
    Path(doc['market_hold_key_file']).write_bytes(cfg.market_hold_key); store_config(path, doc)
    off_cfg = replace(cfg, policy=replace(cfg.policy, crop_cycle_calculation_result_storage=False))
    def off_source_factory(*, principal_provider):
        return MarketSourceStore(off_cfg.dsn, off_cfg.policy.schema, principal_provider=principal_provider,
                                 runtime_identity=(off_cfg.policy, 'authority'))
    off_deps = replace(deps, crop_cycle_calculation_result_store_factory=None,
                       crop_cycle_calculation_current_query_factory=None,
                       market_source_factory=off_source_factory)
    def factory(*, config):
        expected_cfg = cfg if config.policy.crop_cycle_calculation_result_storage else off_cfg
        assert config == expected_cfg
        return deps if config.policy.crop_cycle_calculation_result_storage else off_deps
    monkeypatch.setitem(sys.modules, 'trusted_operator', SimpleNamespace(dependencies=factory))
    def forbidden(*args, **kwargs): pytest.fail('HTTPS parsed/calculated/issued/published crop output')
    for module, name in ((engine.inputs, 'open_input_packet'), (engine.legacy, 'prepare_context'),
            (engine, 'open_calculation_context'), (engine, 'advance_chunk'), (engine.short._Evaluator, 'rhs'),
            (storage.artifact, 'open_artifact'), (storage.artifact, '_validate_delta'),
            (custody._Journal, '__init__'), (custody.CalculationServerCustody, 'advance'),
            (storage.CalculationCycleCropResultStore, 'put'), (engine.evidence.InputEvidenceAuthority, 'issue'),
            (CalculationResultEvidenceAuthority, 'issue')):
        monkeypatch.setattr(module, name, forbidden)
    yield SimpleNamespace(path=path, doc=doc, cfg=cfg, jobs=jobs, records=records, expected=expected,
        terminals=terminals, rights=rights, evidence=evidence, root=root, source_paths=source_paths, tokens=tokens,
        off_cfg=off_cfg, off_deps=off_deps)
    assert all(context.reader.closed for context in inputs.opened)


def custody_fds(paths):
    count = 0
    for path in Path('/proc/self/fd').iterdir():
        try: target = os.readlink(path)
        except FileNotFoundError: continue
        count += any(target == str(root) or target.startswith(str(root) + '/') for root in paths)
    return count


def fd_inventory():
    result = {}
    for path in Path('/proc/self/fd').iterdir():
        try:
            info = path.stat()
            result[path.name] = (os.readlink(path), info.st_dev, info.st_ino)
        except FileNotFoundError:
            continue
    return result


@pytest.mark.parametrize('source_policy', ['original', 'selected'])
def test_disabled_operator_source_policy_must_match_selected_runtime(
        construction_case, login_database, monkeypatch, source_policy):
    case = construction_case
    cfg = replace(case.config, policy=replace(case.config.policy, crop_cycle_calculation_result_storage=False))
    deps = replace(case.dependencies, crop_cycle_calculation_result_store_factory=None,
                   crop_cycle_calculation_current_query_factory=None)
    if source_policy == 'selected':
        def source_factory(*, principal_provider):
            return MarketSourceStore(cfg.dsn, cfg.policy.schema, principal_provider=principal_provider,
                                     runtime_identity=(cfg.policy, 'authority'))
        deps = replace(deps, market_source_factory=source_factory)
    def factory(*, config):
        assert config == cfg
        return deps
    monkeypatch.setitem(sys.modules, 'trusted_operator', SimpleNamespace(dependencies=factory))
    case.document['policy'] = asdict(cfg.policy); store_config(case.path, case.document)
    table = case.jobs._table(storage.schema.TABLE); role = sql.Identifier(cfg.policy.roles['authority'])
    with psycopg.connect(login_database['admin']) as conn:
        conn.execute(sql.SQL('REVOKE SELECT,INSERT ON {} FROM {}').format(table, role))
    try:
        if source_policy == 'original':
            with pytest.raises(loader.original.OperatorConfigHold, match='^operator_config_rejected$'):
                loader.load_calculation_api_runtime(case.path)
        else:
            selected = loader.load_calculation_api_runtime(case.path)
            assert selected.calculation_cycle_crop_results is selected.calculation_cycle_crop_query is None
        save_reference('disabled-source-policy-' + source_policy + '.json', {
            'actual_scram_assembly': True, 'new_storage_grants_removed': True,
            'source_policy': source_policy, 'accepted': source_policy == 'selected'})
    finally:
        with psycopg.connect(login_database['admin']) as conn:
            conn.execute(sql.SQL('GRANT SELECT,INSERT ON {} TO {}').format(table, role))


def test_actual_protected_loader_scram_https_original_pages_holds_restart_and_withdrawal(
        http_case, login_database, monkeypatch):
    case = http_case; jobs = case.jobs; paths = [case.root, *case.source_paths]
    observed = []; joined = 0; trust = ssl.create_default_context(cafile=str(case.cfg.certificate))
    def counts():
        with jobs.connect() as conn:
            return {name: conn.execute(sql.SQL('SELECT count(*) AS n FROM {}').format(jobs._table(name))).fetchone()['n']
                for name in ('jobs', 'job_events', storage.schema.TABLE, 'thermal_g1_runs')}
    def inventory():
        files = [case.path, case.cfg.certificate, case.cfg.private_key,
                 *(Path(case.doc[key]) for key in ('dsn_file', 'thermal_gate_key_file', 'market_hold_key_file'))]
        files.extend(path for root in paths for path in root.rglob('*') if path.is_file())
        return {str(path): (sha256(path.read_bytes()).hexdigest(), path.stat().st_mode, path.stat().st_ino) for path in files}
    baseline = counts(); files_before = inventory()
    def target(name='managed', view='summary', **pages):
        return '/v1/crop-cycle-calculation-research-results/' + case.records[name]['result_id'] + '?' + urlencode(
            {**case.doc_farm, 'view': view, **pages})
    case.doc_farm = json.loads(case.records['managed']['payload_raw'])['binding']['request']['farm']
    monkeypatch.setenv('OSSF_API_CONFIG', str(case.path))
    first_selected = loader.load_calculation_api_runtime(case.path)
    first_https = first_selected.service.server()
    fd_before = len(os.listdir('/proc/self/fd')); fds_before = fd_inventory()
    for restart in range(2):
        selected = first_selected if restart == 0 else loader.load_calculation_api_runtime(case.path)
        assert selected.calculation_cycle_crop_results.jobs is selected.jobs
        assert selected.calculation_cycle_crop_query.store is selected.calculation_cycle_crop_results
        https = first_https if restart == 0 else loader.api_service().server()
        thread = threading.Thread(target=https.run, daemon=True); thread.start()
        try:
            deadline = time.monotonic() + 15
            while not https.started:
                assert thread.is_alive() and time.monotonic() < deadline; time.sleep(.01)
            port = https.servers[0].sockets[0].getsockname()[1]
            def call(where=None, bearer='owner'):
                connection = http.client.HTTPSConnection('127.0.0.1', port, timeout=30, context=trust)
                try:
                    start = time.monotonic()
                    connection.request('GET', where or target(), headers={} if bearer is None else
                        {'Authorization': 'Bearer ' + case.tokens[bearer].decode()})
                    response = connection.getresponse(); raw = response.read(); seconds = time.monotonic() - start
                    assert seconds < 30 and len(raw) <= public.MAX_RESPONSE_BYTES
                    assert response.getheader('cache-control') == 'no-store' and custody_fds(paths) == 0
                    value = json.loads(raw)
                    assert all(marker not in raw for marker in (b'"tenant_id":', b'"checkpoint":', b'"integrity_key":', b'"input_id":'))
                    if response.status == 200:
                        assert response.getheader('x-ossf-crop-query-version') == current.VERSION
                        assert response.getheader('x-ossf-crop-query-code-sha256') == current.CODE_SHA256
                    observed.append({'status': response.status, 'seconds': seconds, 'bytes': len(raw),
                                     'body_sha256': sha256(raw).hexdigest()})
                    return response.status, value
                finally: connection.close()
            status, value = call(); assert status == 200
            assert value['schema_version'] == public.VERSION and value['result_id'] == case.records['managed']['result_id']
            assert value['summary']['manifest'] == case.terminals['managed']['manifest']
            if restart == 0:
                assert call(bearer=None)[0] == 401 and call(bearer='denied')[0] == 403 and call(bearer='foreign')[0] == 404
                for kind, limit in (('samples', 2), ('events', 1)):
                    rows = []; offset = 0
                    while True:
                        status, value = call(target(view=kind, offset=offset, limit=limit)); assert status == 200
                        rows.extend(value['page']['records'])
                        if value['page']['next_offset'] is None: break
                        offset = value['page']['next_offset']
                    original = case.expected['managed'][kind]
                    if kind == 'events': original = [{k: row[k] for k in ('at', 'before', 'after', 'removed')} for row in original]
                    assert _canonical(rows) == _canonical(original)
                    assert call(target(view=kind, offset=len(rows), limit=limit))[1]['page']['records'] == []
                for name in ('past', 'empty'):
                    status, value = call(target(name)); assert status == 200 and value['reference']['status'] == 'hold'
                    assert _canonical(value['summary']['hold']['last_confirmed']) == _canonical(case.terminals[name]['last_confirmed'])
                    for kind in ('samples', 'events'):
                        status, value = call(target(name, kind)); assert status == 200
                        expected = case.expected[name][kind]
                        if kind == 'events': expected = [{k: row[k] for k in ('at', 'before', 'after', 'removed')} for row in expected]
                        assert _canonical(value['page']['records']) == _canonical(expected)
                case.rights.allowed = False
                try: assert call()[0] == 422
                finally: case.rights.allowed = True
                with monkeypatch.context() as patch:
                    encode = public._public_bytes
                    def withdraw(projected):
                        raw = encode(projected); case.rights.allowed = False; return raw
                    patch.setattr(public, '_public_bytes', withdraw)
                    try: assert call()[0] == 422
                    finally: case.rights.allowed = True
                with monkeypatch.context() as patch:
                    patch.setattr(selected.farm_scenarios.candidates._source._source, 'get_input_rights', lambda *_: None)
                    assert call()[0] == 422
                table = jobs._table(storage.schema.TABLE); worker = sql.Identifier(case.cfg.policy.roles['worker'])
                with psycopg.connect(login_database['admin']) as conn:
                    conn.execute(sql.SQL('GRANT SELECT ON {} TO {}').format(table, worker))
                try:
                    status, value = call(); assert status == 503 and value['error']['code'] == 'crop_research_unavailable'
                finally:
                    with psycopg.connect(login_database['admin']) as conn:
                        conn.execute(sql.SQL('REVOKE SELECT ON {} FROM {}').format(table, worker))
                entry = case.evidence.values[case.records['managed']['result_id']]; proof = entry['result_evidence_raw']
                tampered = json.loads(proof); tampered['payload']['summary']['steps'] += 1
                issuer = selected.calculation_cycle_crop_query.authority
                tampered['hmac_sha256'] = issuer._signature(tampered['payload'])
                entry['result_evidence_raw'] = _canonical(tampered)
                try: assert call()[0] == 422
                finally: entry['result_evidence_raw'] = proof
            assert call()[0] == 200
        finally:
            https.should_exit = True; thread.join(timeout=15); assert not thread.is_alive(); joined += 1
    save_reference('active-https.json', {'responses': deepcopy(observed), 'joined_servers': joined,
        'original_values_UTC_and_manifest': True, 'past_and_empty_hold': True,
        'withdrawals_valid_HMAC_tamper_and_live_grant_error_denied': True})
    # Disable the feature with the corresponding authority grants removed, then restore both.
    table = jobs._table(storage.schema.TABLE); role = sql.Identifier(case.cfg.policy.roles['authority'])
    off_path = case.path.with_name('disabled.json'); off_doc = deepcopy(case.doc); off_doc['policy'] = asdict(case.off_cfg.policy)
    off_path.write_text(json.dumps(off_doc)); off_path.chmod(0o600)
    with psycopg.connect(login_database['admin']) as conn:
        conn.execute(sql.SQL('REVOKE SELECT,INSERT ON {} FROM {}').format(table, role))
    try:
        off = loader.load_calculation_api_runtime(off_path); https = off.service.server()
        thread = threading.Thread(target=https.run, daemon=True); thread.start()
        try:
            deadline = time.monotonic() + 15
            while not https.started:
                assert thread.is_alive() and time.monotonic() < deadline; time.sleep(.01)
            port = https.servers[0].sockets[0].getsockname()[1]
            assert call()[0] == 503
        finally:
            https.should_exit = True; thread.join(timeout=15); assert not thread.is_alive(); joined += 1
    finally:
        with psycopg.connect(login_database['admin']) as conn:
            conn.execute(sql.SQL('GRANT SELECT,INSERT ON {} TO {}').format(table, role))
        off_path.unlink()
    assert counts() == baseline and baseline[storage.schema.TABLE] == 3 and baseline['thermal_g1_runs'] == 0
    assert inventory() == files_before and custody_fds(paths) == 0 and current_principal() is None
    assert len(os.listdir('/proc/self/fd')) == fd_before
    assert fd_inventory() == fds_before
    with jobs.connect() as conn:
        assert conn.pgconn.used_password and conn.info.get_parameters()['require_auth'] == 'scram-sha-256'
    save_reference('actual-https.json', {'scope': 'synthetic_registered_software_path_only', 'actual_scram': True,
        'protected_loader_and_env_service': True, 'responses': observed, 'joined_servers': joined,
        'maximum_full_body_seconds': max(value['seconds'] for value in observed),
        'maximum_full_body_bytes': max(value['bytes'] for value in observed),
        'original_values_UTC_and_manifest': True, 'past_and_empty_hold': True,
        'current_withdrawals_and_valid_HMAC_tamper_denied': True, 'live_grant_error_503': True,
        'disabled_policy_and_removed_grants_503': True, 'math_QC_proof_issue_publication_forbidden': True,
        'counts_before': baseline, 'counts_after': counts(), 'input_config_custody_files_unchanged': True,
        'fd_before': fd_before, 'fd_after': len(os.listdir('/proc/self/fd')),
        'same_descriptor_targets_devices_and_inodes': fd_inventory() == fds_before})
