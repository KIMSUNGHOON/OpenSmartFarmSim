"""Protected joint runtime assembly and actual SCRAM/TLS saved-result reads."""
from dataclasses import asdict, replace
from datetime import timedelta
from hashlib import sha256
import http.client
import json
import logging
import os
from pathlib import Path
import ssl
import subprocess
import sys
import threading
import time
from types import SimpleNamespace
from urllib.parse import urlencode

import pytest

from app import crop_climate_joint_operator_config as loader
from app import operator_config as original
from app import calculation_operator_config as calculation
from app import crop_climate_joint_current_query as current
from app.api_runtime import ApiRuntime, ApiRuntimeDependencies
from app.crop_result_store import READ_SCOPES
from app.http_identity import BearerGrant, BearerRegistry, current_principal, token_digest
from test_api_runtime import config, dependencies, policy
from test_operator_config import private_config, store, isolated_assembly
from test_api_serve import tls_files
from test_api_crop_cycle_route import TOKEN, NOW
from test_api_crop_climate_joint_route import fd_inventory, PATH
from test_api_crop_climate_joint_replay import database_cleanup
from test_crop_climate_joint_result_store import login_database, original_login_scope, login_scope, authoring, farm_setup, setup
import test_crop_climate_joint_result_store as registered

profiles = registered.profiles
LOGIN = registered.pytestmark


def save(name, value):
    root = os.environ.get('OSSF_JOINT_RUNTIME_EVIDENCE')
    if root:
        with (Path(root)/name).open('x') as f:
            os.fchmod(f.fileno(), 0o400)
            json.dump(value, f, sort_keys=True, indent=2); f.flush(); os.fsync(f.fileno())


@pytest.fixture
def joint_config(private_config):
    path, doc = private_config
    doc['config_version'] = loader.VERSION
    store(path, doc)
    return path, doc


@pytest.mark.parametrize('enabled', [False, True])
def test_explicit_version_and_closed_optional_calculation_coexistence(joint_config, monkeypatch, enabled):
    path, doc = joint_config
    doc['policy'][loader.FLAG] = enabled
    doc['policy']['crop_cycle_result_storage'] = enabled
    doc['policy'][loader.CALCULATION_FLAG] = enabled
    store(path, doc); calls = isolated_assembly(monkeypatch)
    result = loader.load_joint_api_runtime(path)
    assert result[0] == 'assembled' and calls[0].policy.crop_climate_joint_result_storage is enabled
    assert calls[0].policy.crop_cycle_calculation_result_storage is enabled
    assert 'synthetic-' not in repr(calls[0])


@pytest.mark.parametrize('fault', ['missing-flag', 'extra', 'version', 'policy-extra', 'policy-missing',
    'joint-int', 'joint-string', 'joint-null', 'legacy-prerequisite', 'calculation-prerequisite',
    'calculation-int', 'host', 'port', 'factory', 'relative-path'])
def test_closed_configuration_fails_before_dependency_import(joint_config, monkeypatch, fault):
    path, doc = joint_config; p = doc['policy']
    if fault == 'missing-flag': del p[loader.FLAG]
    elif fault == 'extra': doc['unknown'] = True
    elif fault == 'version': doc['config_version'] = 'operator-api-config-v1'
    elif fault == 'policy-extra': p['unknown'] = False
    elif fault == 'policy-missing': del p['owner']
    elif fault == 'joint-int': p[loader.FLAG] = 1
    elif fault == 'joint-string': p[loader.FLAG] = 'true'
    elif fault == 'joint-null': p[loader.FLAG] = None
    elif fault == 'legacy-prerequisite': p[loader.FLAG] = True
    elif fault == 'calculation-prerequisite': p[loader.CALCULATION_FLAG] = True
    elif fault == 'calculation-int': p[loader.CALCULATION_FLAG] = 0
    elif fault == 'host': doc['host'] = '0.0.0.0'
    elif fault == 'port': doc['port'] = True
    elif fault == 'factory': doc['dependencies_factory'] = 'not:a:reference'
    elif fault == 'relative-path': doc['dsn_file'] = 'relative.dsn'
    store(path, doc)
    monkeypatch.setattr(original.importlib, 'import_module', lambda *_: pytest.fail('invalid configuration imported dependencies'))
    before = fd_inventory()
    with pytest.raises(original.OperatorConfigHold, match='^operator_config_rejected$'):
        loader.load_joint_api_runtime(path)
    assert fd_inventory() == before


@pytest.mark.parametrize('raw', [b'{"port":1,"port":2}', b'{"port":NaN}', b'\xff', b' ' * 65537])
def test_invalid_json_size_and_encoding_are_closed(joint_config, monkeypatch, raw):
    path, _ = joint_config; path.write_bytes(raw)
    monkeypatch.setattr(original.importlib, 'import_module', lambda *_: pytest.fail('invalid JSON imported dependencies'))
    with pytest.raises(original.OperatorConfigHold, match='^operator_config_rejected$'):
        loader.load_joint_api_runtime(path)


@pytest.mark.parametrize('phase', ['factory', 'assembly'])
@pytest.mark.parametrize('field', ['config', 'dsn_file', 'thermal_gate_key_file', 'market_hold_key_file',
    'certificate', 'private_key', 'permissions'])
def test_protected_files_are_rechecked_after_factory_and_assembly(joint_config, monkeypatch, phase, field):
    path, doc = joint_config; trace = []
    target = path if field in ('config', 'permissions') else Path(doc[field])
    def mutate():
        if field == 'permissions': target.chmod(0o644)
        else: target.write_bytes(target.read_bytes()+b' ')
    def factory(*, config):
        trace.append('factory')
        if phase == 'factory': mutate()
        return dependencies()
    def assemble(*args):
        trace.append('assembly'); mutate(); return object()
    monkeypatch.setattr(original.importlib, 'import_module', lambda *_: SimpleNamespace(dependencies=factory))
    monkeypatch.setattr(original, 'ApiRuntime', assemble)
    before = fd_inventory()
    with pytest.raises(original.OperatorConfigHold, match='^operator_config_rejected$'):
        loader.load_joint_api_runtime(path)
    assert trace == (['factory'] if phase == 'factory' else ['factory', 'assembly'])
    assert fd_inventory() == before


@pytest.mark.parametrize('fault', ['type', 'exception', 'exit'])
def test_dependency_failures_have_fixed_error(joint_config, monkeypatch, fault):
    def factory(**kwargs):
        if fault == 'type': return object()
        if fault == 'exception': raise RuntimeError('private configuration marker')
        raise SystemExit('private configuration marker')
    monkeypatch.setattr(original.importlib, 'import_module', lambda *_: SimpleNamespace(dependencies=factory))
    with pytest.raises(original.OperatorConfigHold, match='^operator_config_rejected$'):
        loader.load_joint_api_runtime(joint_config[0])


@pytest.mark.parametrize('version', ['legacy', 'calculation'])
@pytest.mark.parametrize('option', ['omitted', False, True])
def test_old_operator_versions_keep_joint_omission_false_compatibility(private_config, monkeypatch, version, option):
    path, doc = private_config
    read = original.load_api_runtime
    if version == 'calculation':
        doc['config_version'] = calculation.VERSION
        doc['policy'][loader.CALCULATION_FLAG] = False
        read = calculation.load_calculation_api_runtime
    if option == 'omitted': del doc['policy'][loader.FLAG]
    else: doc['policy'][loader.FLAG] = option
    store(path, doc); calls = isolated_assembly(monkeypatch)
    if option is True:
        with pytest.raises(original.OperatorConfigHold, match='^operator_config_rejected$'): read(path)
        assert calls == []
    else: assert read(path)[0] == 'assembled' and len(calls) == 1


@pytest.mark.parametrize('read', [original.load_api_runtime, calculation.load_calculation_api_runtime])
def test_old_loaders_reject_new_version(joint_config, monkeypatch, read):
    calls = isolated_assembly(monkeypatch)
    with pytest.raises(original.OperatorConfigHold, match='^operator_config_rejected$'): read(joint_config[0])
    assert calls == []


@pytest.mark.parametrize('flag,store_factory,query_factory,legacy', [
    (False, True, False, False), (False, False, True, False), (False, True, True, False),
    (True, False, False, True), (True, True, False, True), (True, False, True, True),
    (True, True, True, False)])
def test_flag_factory_and_legacy_prerequisite_fail_before_io(monkeypatch, flag, store_factory, query_factory, legacy):
    def forbidden(*a, **kw): pytest.fail('invalid joint assembly performed I/O')
    monkeypatch.setattr('app.api_runtime.JobStore', forbidden)
    p = replace(policy(), crop_climate_joint_result_storage=flag, crop_cycle_result_storage=legacy)
    deps = dependencies(crop_cycle_result_store_factory=forbidden if legacy else None,
        crop_climate_joint_result_store_factory=forbidden if store_factory else None,
        crop_climate_joint_current_query_factory=forbidden if query_factory else None)
    with pytest.raises(ValueError, match='^API runtime assembly rejected$'): ApiRuntime(config(policy=p), deps)


@pytest.mark.parametrize('field', ['crop_climate_joint_result_store_factory', 'crop_climate_joint_current_query_factory'])
def test_new_dependency_fields_require_callables(field):
    with pytest.raises(ValueError, match='^API runtime dependencies rejected$'): dependencies(**{field: True})


def test_environment_entrypoint_uses_new_loader(monkeypatch):
    service = object(); calls = []
    monkeypatch.setenv('OSSF_API_CONFIG', '/private/joint.json')
    monkeypatch.setattr(loader, 'load_joint_api_runtime', lambda path: calls.append(path) or SimpleNamespace(service=service))
    assert loader.api_service() is service and calls == [Path('/private/joint.json')]
    monkeypatch.delenv('OSSF_API_CONFIG')
    with pytest.raises(original.OperatorConfigHold, match='^operator_config_rejected$'): loader.api_service()


@pytest.mark.parametrize('first', ['app.crop_climate_joint_operator_config', 'app.api_runtime'])
def test_fresh_import_does_not_connect_or_load_joint_math(first):
    code = '''import importlib,os,socket,sys,psycopg
def deny(*a,**k):raise AssertionError('import performed I/O')
psycopg.connect=deny;socket.create_connection=deny
fd=len(os.listdir('/proc/self/fd'));importlib.import_module(sys.argv[1])
assert 'app.crop_climate_joint_current_query' not in sys.modules
assert 'app.crop_climate_joint_integration' not in sys.modules
assert len(os.listdir('/proc/self/fd'))==fd
'''
    child = subprocess.run([sys.executable, '-B', '-c', code, first], capture_output=True, timeout=30)
    assert child.returncode == 0, child.stderr.decode()


@pytest.fixture
def native(setup, joint_config, tls_files, database_cleanup, tmp_path, monkeypatch):
    from app.crop_climate_joint_farm_binding import JointFarmBinding
    from app.crop_cycle_farm_binding import CycleFarmBinding
    from app.crop_cycle_server_custody import CycleServerCustody
    from app.crop_cycle_result_store import CycleCropResultStore
    from app.market_source_store import MarketSourceStore
    from test_crop_cycle_artifact import PROFILES, NOTICE
    from test_crop_cycle_farm_binding import SyntheticInputRights
    seed, raw, value, done = registered.ready(setup)
    record = seed.put('tenant-1', raw); farm = json.loads(raw)['farm']
    expected = {view: current.JointCropClimateCurrentQuery(seed).read('tenant-1', record['result_id'], farm, view=view)
                for view in ('summary', 'samples', 'events')}
    farms = seed.server.binding.farms; jobs = seed.jobs; research = farms.replay.owned_research
    old_root = tmp_path/'legacy-server'; old_root.mkdir(mode=0o700)
    class UnusedResolver:
        version = 'owned-joint-runtime-unused-legacy-v1'
        def __call__(self, *a, **kw): pytest.fail('joint runtime resolved legacy inputs')
    def legacy_factory(*, farm_authoring_service):
        binding = CycleFarmBinding(farm_authoring_service, **PROFILES, notice_raw=NOTICE, input_rights=SyntheticInputRights())
        server = CycleServerCustody(binding, old_root, input_resolver=UnusedResolver(), integrity_key=b'owned-joint-runtime-legacy-server-' + b's'*32)
        return CycleCropResultStore(server, integrity_key=b'owned-joint-runtime-legacy-db-' + b'd'*32)
    options = {'server_key': seed.server.integrity_key, 'db_key': seed.integrity_key}
    def joint_factory(*, farm_authoring_service):
        bound = JointFarmBinding(farm_authoring_service, seed.server.binding.input_authority, input_rights=value[-1])
        custody = registered.producer.model.JointServerCustody(bound, seed.server.directory,
            input_resolver=seed.server.input_resolver, integrity_key=options['server_key'])
        return current.storage.JointCropClimateResultStore(custody, integrity_key=options['db_key'])
    def source_factory(*, principal_provider):
        return MarketSourceStore(jobs._dsn, jobs.schema, principal_provider=principal_provider, runtime_identity=jobs.runtime_identity)
    clock = {'now': NOW}
    grant = BearerGrant(token_digest(TOKEN), 'tenant-1', frozenset(READ_SCOPES), NOW-timedelta(seconds=1), NOW+timedelta(hours=1))
    cert, key, _ = tls_files
    descriptor = jobs._content_directory(create=True); os.close(descriptor)
    cfg = config(policy=jobs.runtime_identity[0], dsn=jobs._dsn, artifact_root=jobs.artifact_root,
                 certificate=cert, private_key=key, port=0)
    deps = dependencies(research_registry=research.catalog, owned_fixture_registry=research.registry,
        owned_research_contexts=dict(research._contexts), market_scope_resolver=farms.replay.thermal.holds._scope_resolver,
        market_source_factory=source_factory, bearer_registry=BearerRegistry((grant,), clock=lambda: clock['now']),
        crop_cycle_result_store_factory=legacy_factory, crop_climate_joint_result_store_factory=joint_factory,
        crop_climate_joint_current_query_factory=lambda *, result_store: current.JointCropClimateCurrentQuery(result_store))
    path, doc = joint_config
    doc.update(policy=asdict(cfg.policy), artifact_root=str(cfg.artifact_root), certificate=str(cert), private_key=str(key), port=0)
    Path(doc['dsn_file']).write_text(cfg.dsn)
    Path(doc['thermal_gate_key_file']).write_bytes(cfg.thermal_gate_key)
    Path(doc['market_hold_key_file']).write_bytes(cfg.market_hold_key)
    store(path, doc)
    def factory(*, config):
        assert config == cfg
        return deps
    monkeypatch.setitem(sys.modules, 'trusted_operator', SimpleNamespace(dependencies=factory))
    before = registered.producer.reference.counts(seed.server.binding)
    calls = registered.producer.reference.forbid(monkeypatch)
    def forbidden(*a, **kw): pytest.fail('joint runtime created or registered results')
    for obj, name in ((registered.producer.model.JointServerCustody, 'advance'),
                      (current.storage.JointCropClimateResultStore, 'put'),
                      (CycleServerCustody, 'advance'), (CycleCropResultStore, 'put')):
        monkeypatch.setattr(obj, name, forbidden)
    files = {p: sha256(p.read_bytes()).hexdigest() for p in
        (path, cert, key, *(Path(doc[f]) for f in ('dsn_file', 'thermal_gate_key_file', 'market_hold_key_file')), *value[2][0].iterdir())}
    yield SimpleNamespace(path=path, config=cfg, deps=deps, seed=seed, value=value, record=record, farm=farm,
        expected=expected, calls=calls, done=json.loads(done), old_root=old_root, options=options, clock=clock)
    assert registered.producer.reference.counts(seed.server.binding) == before and registered.count(seed.server.binding) == 1
    assert {p: sha256(p.read_bytes()).hexdigest() for p in files} == files and not list(old_root.iterdir())
    assert all(n == 0 for n in calls.values()) and current_principal() is None


@LOGIN
@pytest.mark.parametrize('setup', [None, 'hold'], indirect=True)
def test_native_verified_tls_runtime_completed_and_hold_original_bytes(native):
    c = native; initial = fd_inventory(); runtime = loader.load_joint_api_runtime(c.path)
    selected = runtime.joint_crop_results; query = runtime.joint_crop_query
    assert type(runtime) is ApiRuntime and type(selected) is current.storage.JointCropClimateResultStore
    assert type(query) is current.JointCropClimateCurrentQuery and query.store is selected
    assert selected.jobs is runtime.jobs and selected.server.binding.farms is runtime.farm_authoring
    assert runtime.jobs.principal_provider is current_principal
    assert len({selected.integrity_key, selected.server.integrity_key, selected.server.binding.input_authority.integrity_key}) == 3
    with runtime.jobs.connect() as conn: assert conn.pgconn.used_password and conn.info.get_parameters()['require_auth'] == 'scram-sha-256'
    assert fd_inventory() == initial
    pytest_log_fds = {str(h().stream.fileno()) for h in logging._handlerList if h() is not None
        and type(h()).__module__ == '_pytest.logging' and getattr(h(), 'baseFilename', None) == os.devnull
        and getattr(h(), 'stream', None) is not None and not h().stream.closed}
    server = runtime.service.server(); inventory = fd_inventory()
    assert inventory == {k:v for k,v in initial.items() if k not in pytest_log_fds}
    thread = threading.Thread(target=server.run, daemon=True); thread.start(); replies = {}; deadline = time.monotonic()+10
    try:
        while not server.started:
            assert thread.is_alive() and time.monotonic() < deadline; time.sleep(.01)
        context = ssl.create_default_context(cafile=str(c.config.certificate))
        port = server.servers[0].sockets[0].getsockname()[1]
        for view, expected in c.expected.items():
            connection = http.client.HTTPSConnection('127.0.0.1', port, context=context, timeout=30); started = time.monotonic()
            try:
                connection.request('GET', PATH+c.record['result_id']+'?'+urlencode(c.farm)+('' if view == 'summary' else '&view='+view),
                                   headers={'Authorization':'Bearer '+TOKEN.decode()})
                response = connection.getresponse(); raw = response.read()
                assert response.status == 200 and raw == expected and response.getheader('Cache-Control') == 'no-store'
                replies[view] = {'bytes':len(raw), 'sha256':sha256(raw).hexdigest(), 'seconds':time.monotonic()-started}
            finally: connection.close()
    finally: server.should_exit = True; thread.join(15); assert not thread.is_alive()
    summary = json.loads(c.expected['summary'])
    assert summary['summary']['status'] == c.done['status'] and summary['reference']['G0_G4'] == 'not_assessed'
    assert summary['summary']['last_confirmed']['time']['at'].endswith('.123456Z')
    assert fd_inventory() == inventory
    save('runtime-'+c.done['status']+'.json', {'actual_scram':True, 'verified_TLS':True, 'same_jobs_farm_current_principal':True,
        'three_distinct_keys':True, 'original_wire_UTC':True, 'replies':replies, 'calls':c.calls, 'FD':[len(inventory),len(fd_inventory())]})


@LOGIN
def test_native_runtime_rejects_foreign_objects_keys_pins_and_changed_grants(native, login_scope, monkeypatch):
    from psycopg import sql
    c = native; before = fd_inventory(); rejected = []
    def deny(deps):
        with pytest.raises(ValueError, match='^API runtime assembly rejected$'): ApiRuntime(c.config, deps)
        assert fd_inventory() == before
    for name, changes in (
        ('store-type', {'crop_climate_joint_result_store_factory':lambda **_: object()}),
        ('foreign-store', {'crop_climate_joint_result_store_factory':lambda **_: c.seed}),
        ('query-type', {'crop_climate_joint_current_query_factory':lambda **_: object()}),
        ('foreign-query', {'crop_climate_joint_current_query_factory':lambda **_: current.JointCropClimateCurrentQuery(c.seed)})):
        deny(replace(c.deps, **changes)); rejected.append(name)
    for key in ('server_key', 'db_key'):
        previous = c.options[key]; c.options[key] = c.seed.server.binding.input_authority.integrity_key
        try: deny(c.deps); rejected.append(key+'-reused-input-key')
        finally: c.options[key] = previous
    with monkeypatch.context() as patch:
        patch.setattr(current, 'CODE_SHA256', '0'*64); deny(c.deps); rejected.append('model-code-pin')
    base, p, _ = login_scope
    def select_grant(verb):
        with base.connect() as conn:
            conn.execute(sql.SQL('SET LOCAL ROLE {}').format(sql.Identifier(p.owner)))
            conn.execute(sql.SQL(verb+' SELECT ON {} '+('TO' if verb == 'GRANT' else 'FROM')+' {}').format(
                sql.Identifier(p.schema, current.storage.schema.TABLE), sql.Identifier(p.roles['authority'])))
    select_grant('REVOKE')
    try: deny(c.deps); rejected.append('changed-runtime-grant')
    finally: select_grant('GRANT')
    rebuilt = ApiRuntime(c.config, c.deps)
    assert rebuilt.joint_crop_results is not c.seed and rebuilt.joint_crop_query.store is rebuilt.joint_crop_results
    assert fd_inventory() == before
    save('runtime-misassembly.json', {'rejected':rejected, 'rebuilt_same_binding':True, 'FD':[len(before),len(fd_inventory())], 'calls':c.calls})


@LOGIN
def test_native_runtime_late_rights_and_account_during_serialization(native, monkeypatch):
    from test_api_crop_climate_joint_route import get
    c = native; runtime = loader.load_joint_api_runtime(c.path); encode = current.public._public_bytes; rejected = []
    for phase in ('rights', 'account'):
        seen = []
        def serialized(model):
            raw = encode(model); seen.append(1)
            if len(seen) == 2:
                if phase == 'rights': c.value[-1].allowed = False
                else: c.clock['now'] = NOW+timedelta(hours=1)
            return raw
        try:
            with monkeypatch.context() as patch:
                patch.setattr(current.public, '_public_bytes', serialized)
                status, value, _ = get(runtime.service.app, c.record['result_id'], c.farm)
            assert len(seen) == 2 and status == (422 if phase == 'rights' else 401) and 'error' in value
            rejected.append({'phase':phase, 'status':status})
        finally: c.value[-1].allowed = True; c.clock['now'] = NOW
    save('runtime-late-denial.json', {'rejected':rejected, 'calls':c.calls})
