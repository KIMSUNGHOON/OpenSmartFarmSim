"""Protected calculation config; actual crop HTTP transport is a later child."""
from dataclasses import asdict
from hashlib import sha256
import json
import os
from pathlib import Path
import subprocess
import sys
from time import perf_counter
from types import SimpleNamespace

import psycopg
from psycopg import sql
import pytest

from app import calculation_operator_config as loader
from app import operator_config as original
from test_operator_config import private_config,store,isolated_assembly
from test_api_runtime import config, dependencies
from test_api_serve import tls_files
from test_crop_cycle_calculation_result_store_farms import login_scope, original_login_scope
from test_farm_authoring_storage import authoring
from test_farm_replay_scenario import farm_setup
from login_database import assert_host_scram, login_database

VERSION='operator-calculation-api-config-v1'
FLAG='crop_cycle_calculation_result_storage'


@pytest.fixture
def calculation_config(private_config):
    path,doc=private_config;doc['config_version']=VERSION;doc['policy'][FLAG]=False
    store(path,doc);return path,doc


@pytest.mark.parametrize('enabled',[False,True])
def test_explicit_new_policy_preserves_protected_config_and_original_loader(calculation_config,monkeypatch,enabled):
    path,doc=calculation_config;doc['policy'][FLAG]=enabled
    if enabled:doc['policy']['crop_cycle_result_storage']=True
    store(path,doc);raw=path.read_bytes();before=len(os.listdir('/proc/self/fd'));calls=isolated_assembly(monkeypatch)
    assembled=loader.load_calculation_api_runtime(path)
    assert assembled[0]=='assembled' and len(calls)==1 and asdict(calls[0].policy)==doc['policy']
    assert calls[0].policy.crop_cycle_calculation_result_storage is enabled
    assert 'synthetic-' not in repr(calls[0]) and 'private-test' not in repr(calls[0])
    with pytest.raises(original.OperatorConfigHold,match='^operator_config_rejected$'):original.load_api_runtime(path)
    assert path.read_bytes()==raw and len(os.listdir('/proc/self/fd'))==before


def deny_import(monkeypatch):
    monkeypatch.setattr(original.importlib, 'import_module',
                        lambda *_: pytest.fail('rejected calculation config imported dependencies'))


@pytest.mark.parametrize('fault', [
    'extra', 'missing', 'legacy-version', 'policy-extra', 'policy-missing', 'policy-type',
    'missing-flag', 'zero-flag', 'one-flag', 'string-flag', 'null-flag',
    'old-false', 'old-missing', 'old-one', 'content-extra', 'content-bool',
    'host', 'port-bool', 'relative', 'traversal', 'factory', 'empty-dsn'])
def test_closed_new_schema_and_prerequisite_refuse_before_import(
        calculation_config, monkeypatch, fault):
    path, doc = calculation_config
    if fault == 'extra': doc['private-marker'] = 'untrusted'
    elif fault == 'missing': del doc['content_access']
    elif fault == 'legacy-version': doc['config_version'] = 'operator-api-config-v1'
    elif fault == 'policy-extra': doc['policy']['password'] = 'private-marker'
    elif fault == 'policy-missing': del doc['policy']['connection_limit']
    elif fault == 'policy-type': doc['policy'] = []
    elif fault == 'missing-flag': del doc['policy'][FLAG]
    elif fault.endswith('-flag'):
        doc['policy'][FLAG] = {'zero-flag': 0, 'one-flag': 1,
                              'string-flag': 'false', 'null-flag': None}[fault]
    elif fault.startswith('old-'):
        doc['policy'][FLAG] = True
        if fault == 'old-missing': doc['policy'].pop('crop_cycle_result_storage')
        else: doc['policy']['crop_cycle_result_storage'] = 1 if fault == 'old-one' else False
    elif fault == 'content-extra': doc['content_access'] = {'owner_uid': 0, 'reader_gid': 0, 'extra': 0}
    elif fault == 'content-bool': doc['content_access'] = {'owner_uid': True, 'reader_gid': 0}
    elif fault == 'host': doc['host'] = '0.0.0.0'
    elif fault == 'port-bool': doc['port'] = True
    elif fault == 'relative': doc['dsn_file'] = 'relative.dsn'
    elif fault == 'traversal': doc['artifact_root'] = '/private/../artifacts'
    elif fault == 'factory': doc['dependencies_factory'] = 'module:factory;private-marker'
    elif fault == 'empty-dsn': Path(doc['dsn_file']).write_bytes(b'   ')
    store(path, doc)
    deny_import(monkeypatch)
    before = len(os.listdir('/proc/self/fd'))
    with pytest.raises(original.OperatorConfigHold, match='^operator_config_rejected$') as error:
        loader.load_calculation_api_runtime(path)
    assert 'private-marker' not in str(error.value)
    assert len(os.listdir('/proc/self/fd')) == before


@pytest.mark.parametrize('raw', [b'{"port":1,"port":2}', b'{"port":NaN}',
                               b'[]', b'\xff', b'x' * 65537])
def test_invalid_json_and_size_refuse_before_import(calculation_config, monkeypatch, raw):
    path, _ = calculation_config
    path.write_bytes(raw)
    deny_import(monkeypatch)
    with pytest.raises(original.OperatorConfigHold, match='^operator_config_rejected$'):
        loader.load_calculation_api_runtime(path)


@pytest.mark.parametrize('fault', ['file-mode', 'parent-mode', 'file-symlink', 'parent-symlink',
                                 'hardlink', 'fifo', 'short-key', 'missing-key'])
def test_actual_protected_files_refuse_unsafe_inputs(calculation_config, monkeypatch, tmp_path, fault):
    path, doc = calculation_config
    if fault == 'file-mode': path.chmod(0o644)
    elif fault == 'parent-mode': path.parent.chmod(0o750)
    elif fault == 'file-symlink':
        target = path.with_suffix('.actual'); path.rename(target); path.symlink_to(target)
    elif fault == 'parent-symlink':
        target = tmp_path/'actual'; path.parent.rename(target); path.parent.symlink_to(target, target_is_directory=True)
    elif fault == 'hardlink': os.link(path, path.with_suffix('.copy'))
    elif fault == 'fifo': path.unlink(); os.mkfifo(path, 0o600)
    elif fault == 'short-key': Path(doc['market_hold_key_file']).write_bytes(b'short')
    else: Path(doc['thermal_gate_key_file']).unlink()
    deny_import(monkeypatch)
    before = len(os.listdir('/proc/self/fd'))
    with pytest.raises(original.OperatorConfigHold, match='^operator_config_rejected$'):
        loader.load_calculation_api_runtime(path)
    assert len(os.listdir('/proc/self/fd')) == before


@pytest.mark.parametrize('attribute', ['system.posix_acl_access', 'system.posix_acl_default'])
def test_shared_acl_inspection_is_used(calculation_config, monkeypatch, attribute):
    path, _ = calculation_config
    monkeypatch.setattr(original.os, 'listxattr', lambda _descriptor: [attribute])
    deny_import(monkeypatch)
    with pytest.raises(original.OperatorConfigHold, match='^operator_config_rejected$'):
        loader.load_calculation_api_runtime(path)


@pytest.mark.parametrize('mutation', ['permissions', 'append', 'same-size', 'unlink'])
def test_actual_change_during_read_refuses_and_closes(calculation_config, monkeypatch, mutation):
    path, _ = calculation_config
    inode = path.stat().st_ino
    read = os.read
    def changing_read(descriptor, size):
        raw = read(descriptor, size)
        if os.fstat(descriptor).st_ino == inode:
            if mutation == 'permissions': path.chmod(0o644)
            elif mutation == 'append':
                with path.open('ab') as stream: stream.write(b' ')
            elif mutation == 'same-size': path.write_bytes(b' ' * len(raw))
            else: path.unlink()
        return raw
    monkeypatch.setattr(original.os, 'read', changing_read)
    deny_import(monkeypatch)
    before = len(os.listdir('/proc/self/fd'))
    with pytest.raises(original.OperatorConfigHold, match='^operator_config_rejected$'):
        loader.load_calculation_api_runtime(path)
    assert len(os.listdir('/proc/self/fd')) == before


@pytest.mark.parametrize('fault', ['wrong-type', 'exception', 'exit'])
def test_dependency_errors_remain_fixed_and_close_descriptors(calculation_config, monkeypatch, fault):
    path, _ = calculation_config
    calls = []
    def factory(*, config):
        calls.append(config)
        if fault == 'wrong-type': return object()
        if fault == 'exception': raise RuntimeError('private-test dependency credential')
        raise SystemExit('private-test dependency credential')
    monkeypatch.setattr(original.importlib, 'import_module', lambda *_: SimpleNamespace(dependencies=factory))
    before = len(os.listdir('/proc/self/fd'))
    with pytest.raises(original.OperatorConfigHold, match='^operator_config_rejected$'):
        loader.load_calculation_api_runtime(path)
    assert len(calls) == 1 and len(os.listdir('/proc/self/fd')) == before


def test_optional_protected_authored_key_and_content_access(calculation_config, monkeypatch):
    path, doc = calculation_config
    key = path.parent/'authored.key'; key.write_bytes(b'owned-authored-key-' + b'a' * 32); key.chmod(0o600)
    doc['authored_run_gate_key_file'] = str(key)
    doc['content_access'] = {'owner_uid': os.geteuid(), 'reader_gid': os.getegid()}
    doc['policy'].pop('crop_result_storage')
    store(path, doc)
    calls = isolated_assembly(monkeypatch)
    loader.load_calculation_api_runtime(path)
    assert calls[0].authored_run_gate_key == key.read_bytes()
    assert asdict(calls[0].content_access) == doc['content_access']
    assert calls[0].policy.crop_result_storage is False


def test_environment_entrypoint_returns_loaded_service(calculation_config, monkeypatch):
    path, _ = calculation_config
    seen = []
    service = object()
    def load(selected): seen.append(selected); return SimpleNamespace(service=service)
    monkeypatch.setattr(loader, 'load_calculation_api_runtime', load)
    monkeypatch.setenv('OSSF_API_CONFIG', str(path))
    assert loader.api_service() is service and seen == [path]


@pytest.mark.parametrize('value', [None, 'relative.json', '/private/../config.json'])
def test_environment_errors_refuse_without_loading(monkeypatch, value):
    if value is None: monkeypatch.delenv('OSSF_API_CONFIG', raising=False)
    else: monkeypatch.setenv('OSSF_API_CONFIG', value)
    monkeypatch.setattr(loader, 'load_calculation_api_runtime', lambda *_: pytest.fail('invalid env loaded config'))
    with pytest.raises(original.OperatorConfigHold, match='^operator_config_rejected$'):
        loader.api_service()


@pytest.mark.parametrize('enabled', [False, True])
def test_legacy_version_keeps_rejecting_new_field(calculation_config, monkeypatch, enabled):
    path, doc = calculation_config
    doc['config_version'] = 'operator-api-config-v1'; doc['policy'][FLAG] = enabled
    store(path, doc); deny_import(monkeypatch)
    with pytest.raises(original.OperatorConfigHold, match='^operator_config_rejected$'):
        original.load_api_runtime(path)


def save_reference(name, value):
    root = os.environ.get('OSSF_CALCULATION_LOADER_EVIDENCE')
    if root:
        with (Path(root)/name).open('x') as handle:
            os.fchmod(handle.fileno(), 0o400); json.dump(value, handle, sort_keys=True, indent=2)
            handle.write('\n'); handle.flush(); os.fsync(handle.fileno())


@pytest.mark.parametrize('first', ['app.calculation_operator_config', 'app.operator_config', 'app.api_runtime'])
def test_fresh_python_import_orders_keep_calculation_modules_unloaded(first):
    code = '''import importlib,json,os,secrets,sys
before=len(os.listdir('/proc/self/fd'))
for name in [sys.argv[1],'app.calculation_operator_config','app.operator_config','app.api_runtime','app.api_crop_cycle_calculation_replay']:importlib.import_module(name)
forbidden=['app.crop_cycle_calculation_context','app.crop_cycle_calculation_result_store','app.crop_cycle_calculation_current_query']
assert all(name not in sys.modules for name in forbidden)
assert before==len(os.listdir('/proc/self/fd'))
print(json.dumps({'first':sys.argv[1],'fd_before':before,'fd_after':len(os.listdir('/proc/self/fd')),'new_calculation_store_query_modules_loaded':False}))
'''
    child = subprocess.run([sys.executable, '-c', code, first], text=True, capture_output=True, timeout=30)
    assert child.returncode == 0 and child.stderr == ''
    save_reference('import-' + first.rsplit('.', 1)[-1] + '.json', {'exit_code': 0, **json.loads(child.stdout)})


@pytest.fixture(scope='module')
def audit_database(login_database, tmp_path_factory):
    yield
    with psycopg.connect(login_database['admin']) as conn:
        schemas = conn.execute("SELECT count(*) FROM pg_namespace WHERE nspname ~ '^login_test_'").fetchone()[0]
        roles = conn.execute("SELECT count(*) FROM pg_roles WHERE rolname ~ '^login_(owner_|[0-9a-f]{32}_)'").fetchone()[0]
        methods = assert_host_scram(conn)
    passfiles = list(tmp_path_factory.getbasetemp().rglob('*.pgpass'))
    assert schemas == roles == len(passfiles) == 0
    save_reference('database-cleanup.json', {'schemas_after': schemas, 'roles_after': roles,
        'passfiles_after': len(passfiles), 'actual_host_auth_methods': methods})


@pytest.fixture
def calculation_assembly(authoring, tls_files, calculation_config, tmp_path, monkeypatch):
    from app import crop_cycle_calculation_context as engine
    from app import crop_cycle_calculation_result_store as storage
    from app import crop_cycle_calculation_current_query as query
    from app import crop_cycle_result_store as old_store
    from app import crop_cycle_server_custody as old_server
    from app.crop_cycle_calculation_farm_binding import CalculationFarmBinding
    from app.crop_cycle_farm_binding import CycleFarmBinding
    from app.crop_cycle_calculation_result_evidence import CalculationResultEvidenceAuthority
    from app.market_source_store import MarketSourceStore
    from test_crop_cycle_artifact import program, PROFILES, NOTICE
    from test_crop_cycle_farm_binding import SyntheticInputRights
    from test_crop_cycle_input_evidence import authority
    farms, _, _ = authoring
    jobs = farms.replay.jobs; research = farms.replay.owned_research
    issuer = authority(); rights = SyntheticInputRights(); input_root = tmp_path/'inputs'
    packet = program('empty-entry'); anchors = packet.pop('output_times')
    receipt = engine.inputs.write_input_packet(input_root, **packet, anchors=anchors,
        outputs=anchors, **PROFILES, program_id='owned-loader-input')
    for path in input_root.iterdir(): path.chmod(0o400)
    input_proof = issuer.issue(input_root, receipt['root_sha256'])
    new_root = tmp_path/'calculation-server'; old_root = tmp_path/'legacy-server'
    new_root.mkdir(mode=0o700); old_root.mkdir(mode=0o700)
    server_key = b'owned-loader-server-' + b's' * 32
    db_key = b'owned-loader-db-' + b'd' * 32
    result_key = b'owned-loader-result-' + b'r' * 32
    class Resolver:
        version = 'owned-loader-unused-resolver-v1'
        def __call__(self, *args, **kwargs): pytest.fail('loader assembly resolved crop inputs/results')
    def crop_factory(*, farm_authoring_service):
        bound = CalculationFarmBinding(farm_authoring_service, issuer, input_rights=rights)
        server = storage.server.CalculationServerCustody(bound, new_root,
            input_resolver=Resolver(), integrity_key=server_key)
        return storage.CalculationCycleCropResultStore(server, integrity_key=db_key)
    def query_factory(*, result_store):
        result_authority = CalculationResultEvidenceAuthority(issuer, integrity_key=result_key,
            issuer_id='owned-loader-result-authority', key_id='result-v1')
        return query.CalculationCurrentCycleQuery(result_store, result_authority, evidence_resolver=Resolver())
    def legacy_factory(*, farm_authoring_service):
        bound = CycleFarmBinding(farm_authoring_service, **PROFILES, notice_raw=NOTICE, input_rights=rights)
        server = old_server.CycleServerCustody(bound, old_root, input_resolver=Resolver(), integrity_key=server_key)
        return old_store.CycleCropResultStore(server, integrity_key=db_key)
    def source_factory(*, principal_provider):
        return MarketSourceStore(jobs._dsn, jobs.schema, principal_provider=principal_provider,
                                 runtime_identity=jobs.runtime_identity)
    descriptor = jobs._content_directory(create=True); os.close(descriptor)
    cert, key, _ = tls_files
    cfg = config(policy=jobs.runtime_identity[0], dsn=jobs._dsn, artifact_root=jobs.artifact_root,
                 certificate=cert, private_key=key, port=0)
    deps = dependencies(research_registry=research.catalog, owned_fixture_registry=research.registry,
        owned_research_contexts=dict(research._contexts),
        market_scope_resolver=farms.replay.thermal.holds._scope_resolver,
        market_source_factory=source_factory, crop_cycle_result_store_factory=legacy_factory,
        crop_cycle_calculation_result_store_factory=crop_factory,
        crop_cycle_calculation_current_query_factory=query_factory)
    path, doc = calculation_config
    doc.update(policy=asdict(cfg.policy), artifact_root=str(cfg.artifact_root),
               certificate=str(cert), private_key=str(key), port=0)
    Path(doc['dsn_file']).write_text(cfg.dsn)
    Path(doc['thermal_gate_key_file']).write_bytes(cfg.thermal_gate_key)
    Path(doc['market_hold_key_file']).write_bytes(cfg.market_hold_key)
    store(path, doc)
    def factory(*, config):
        assert config == cfg
        return deps
    monkeypatch.setitem(sys.modules, 'trusted_operator', SimpleNamespace(dependencies=factory))
    def forbidden(*args, **kwargs): pytest.fail('loader assembly parsed/calculated/published crop output')
    for module, name in ((engine.inputs, 'open_input_packet'), (engine.legacy, 'prepare_context'),
            (engine, 'open_calculation_context'), (engine, 'advance_chunk'), (engine.short._Evaluator, 'rhs'),
            (engine.evidence.InputEvidenceAuthority, 'issue'), (CalculationResultEvidenceAuthority, 'issue'),
            (storage.artifact, 'open_artifact'), (storage.artifact, '_validate_delta'),
            (storage.server.CalculationServerCustody, 'advance'), (storage.CalculationCycleCropResultStore, 'put'),
            (old_server.CycleServerCustody, 'advance'), (old_store.CycleCropResultStore, 'put')):
        monkeypatch.setattr(module, name, forbidden)
    return SimpleNamespace(path=path, document=doc, config=cfg, dependencies=deps, jobs=jobs,
        input_root=input_root, input_proof=input_proof, new_root=new_root, old_root=old_root,
        storage_type=storage.CalculationCycleCropResultStore, query_type=query.CalculationCurrentCycleQuery)


@pytest.mark.parametrize('original_login_scope', [{'market_calculation': True, 'market_source_storage': True,
    'thermal_scenario_storage': True, 'break_even_calculation': True, 'crop_cycle_result_storage': True}], indirect=True)
def test_actual_scram_protected_loader_assembly_reconstruction_and_no_computation(
        calculation_assembly, audit_database, monkeypatch):
    from app.http_identity import current_principal
    case = calculation_assembly
    def counts():
        with case.jobs.connect() as conn:
            return {name: conn.execute(sql.SQL('SELECT count(*) AS n FROM {}').format(
                case.jobs._table(name))).fetchone()['n'] for name in
                ('jobs', 'job_events', 'crop_cycle_research_results', 'crop_cycle_verified_research_results')}
    def unchanged_files():
        paths = {case.path, case.config.certificate, case.config.private_key,
                 *(Path(case.document[field]) for field in
                   ('dsn_file', 'thermal_gate_key_file', 'market_hold_key_file')),
                 *case.input_root.iterdir()}
        return {str(path): (sha256(path.read_bytes()).hexdigest(), path.stat().st_mode, path.stat().st_ino)
                for path in paths}
    before = counts(); files_before = unchanged_files(); fd_before = len(os.listdir('/proc/self/fd'))
    started = perf_counter(); selected = loader.load_calculation_api_runtime(case.path)
    elapsed = perf_counter() - started
    current = selected.calculation_cycle_crop_results; selected_query = selected.calculation_cycle_crop_query
    assert type(selected) is original.ApiRuntime and type(current) is case.storage_type
    assert type(selected_query) is case.query_type and selected_query.store is current
    assert current.jobs is selected.jobs and current.server.binding.jobs is selected.jobs
    assert current.server.binding.farms is selected.farm_authoring and selected.jobs.principal_provider is current_principal
    assert len({current.integrity_key, current.server.integrity_key, current.server.binding.input_authority.integrity_key,
                selected_query.authority.integrity_key}) == 4
    with selected.jobs.connect() as conn:
        assert conn.pgconn.used_password and conn.info.get_parameters()['require_auth'] == 'scram-sha-256'
    rebuilt = loader.load_calculation_api_runtime(case.path)
    assert rebuilt.calculation_cycle_crop_results is not current
    assert rebuilt.calculation_cycle_crop_results.jobs is rebuilt.jobs
    assert rebuilt.calculation_cycle_crop_query.store is rebuilt.calculation_cycle_crop_results
    monkeypatch.setenv('OSSF_API_CONFIG', str(case.path))
    assert type(loader.api_service()) is type(selected.service)
    assert counts() == before and before['crop_cycle_research_results'] == before['crop_cycle_verified_research_results'] == 0
    assert unchanged_files() == files_before and len(os.listdir('/proc/self/fd')) == fd_before
    assert not list(case.new_root.iterdir()) and not list(case.old_root.iterdir())
    save_reference('scram-assembly.json', {'actual_scram': True, 'normal_assembly_seconds': elapsed,
        'same_jobs_farm_current_principal': True, 'four_independent_keys': True,
        'reconstructed_same_bindings': True, 'environment_entrypoint_assembled_service': True,
        'counts_before': before, 'counts_after': counts(), 'private_files_and_inputs_unchanged': True,
        'parser_context_QC_RHS_advance_publication_forbidden': True,
        'input_proof_sha256': sha256(case.input_proof).hexdigest(),
        'fd_before': fd_before, 'fd_after': len(os.listdir('/proc/self/fd'))})
