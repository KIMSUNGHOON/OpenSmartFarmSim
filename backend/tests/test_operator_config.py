"""Protected operator input boundaries; actual SCRAM/TLS proof is separate."""

from dataclasses import asdict
import http.client
import json
import os
from pathlib import Path
import signal
import socket
import ssl
import subprocess
import sys
import time
from types import SimpleNamespace

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from app.operator_config import OperatorConfigHold, load_api_runtime, api_service
from app.api_runtime import ApiRuntimeConfig
import app.operator_config as operator_config
from login_database import login_database, login_scope
from psycopg import sql
from test_api_runtime import policy, dependencies, TOKEN
from test_api_serve import tls_files


@pytest.fixture
def private_config(tmp_path):
    directory = tmp_path/'operator'
    directory.mkdir(mode=0o700)
    def private(name, value):
        path = directory/name
        path.write_bytes(value)
        path.chmod(0o600)
        return str(path)
    legacy_policy = asdict(policy())
    assert legacy_policy.pop('crop_cycle_calculation_result_storage') is False
    doc = {'config_version':'operator-api-config-v1', 'policy':legacy_policy,
        'dsn_file':private('authority.dsn', b'dbname=private-test-db user=private-test-user'),
        'artifact_root':str(tmp_path/'artifacts'),
        'certificate':private('certificate.pem', b'synthetic-certificate'),
        'private_key':private('private.pem', b'synthetic-private-key'),
        'thermal_gate_key_file':private('thermal.key', b'synthetic-thermal-key-'+b't'*32),
        'market_hold_key_file':private('market.key', b'synthetic-market-key-'+b'm'*32),
        'authored_run_gate_key_file':None, 'content_access':None,
        'host':'127.0.0.1', 'port':8443, 'dependencies_factory':'trusted_operator:dependencies'}
    path=directory/'operator.json'
    path.write_text(json.dumps(doc)); path.chmod(0o600)
    return path, doc


def store(path, doc):
    path.write_text(json.dumps(doc))


def isolated_assembly(monkeypatch):
    calls=[]
    def factory(*, config):
        assert type(config) is ApiRuntimeConfig
        calls.append(config)
        return dependencies()
    monkeypatch.setattr('app.operator_config.ApiRuntime', lambda config, deps: ('assembled',config,deps))
    monkeypatch.setattr('app.operator_config.importlib.import_module',
                        lambda *_: SimpleNamespace(dependencies=factory))
    return calls


def test_reads_explicit_private_config_and_hides_secrets(monkeypatch, private_config):
    path, doc=private_config
    calls=isolated_assembly(monkeypatch)
    result=load_api_runtime(path)
    assert result[0]=='assembled' and len(calls)==1
    config=calls[0]
    assert config.policy==policy() and config.port==8443
    assert config.artifact_root==Path(doc['artifact_root'])
    assert config.thermal_gate_key==Path(doc['thermal_gate_key_file']).read_bytes()
    assert config.authored_run_gate_key is None and config.content_access is None
    assert 'private-test' not in repr(config) and 'synthetic-' not in repr(config)


@pytest.mark.parametrize('crop_option', [None, False, True])
def test_existing_policy_and_explicit_crop_option(monkeypatch, private_config, crop_option):
    path, doc = private_config
    if crop_option is None:
        del doc['policy']['crop_result_storage']
    else:
        doc['policy']['crop_result_storage'] = crop_option
    store(path, doc)
    calls = isolated_assembly(monkeypatch)
    load_api_runtime(path)
    assert calls[0].policy.crop_result_storage is (crop_option is True)


@pytest.mark.parametrize('coupled_option', ['omit', False, True])
def test_coupled_storage_default_policy_loads_existing_api(monkeypatch, private_config, coupled_option):
    path, doc = private_config
    if coupled_option == 'omit':
        del doc['policy']['crop_coupled_result_storage']
    else:
        doc['policy']['crop_coupled_result_storage'] = coupled_option
    store(path, doc)
    calls = isolated_assembly(monkeypatch)
    load_api_runtime(path)
    assert len(calls) == 1 and calls[0].policy.crop_coupled_result_storage is (coupled_option is True)


@pytest.mark.parametrize('coupled_option', [0, 1, 'false', None])
def test_coupled_storage_api_option_is_closed_before_factory(monkeypatch, private_config, coupled_option):
    path, doc = private_config
    doc['policy']['crop_coupled_result_storage'] = coupled_option
    store(path, doc)
    monkeypatch.setattr(operator_config.importlib, 'import_module',
        lambda *_: pytest.fail('non-boolean coupled API option imported dependencies'))
    with pytest.raises(OperatorConfigHold, match='^operator_config_rejected$'):
        load_api_runtime(path)


@pytest.mark.parametrize('crop_option', [0, 1, 'false', None])
def test_crop_option_requires_explicit_boolean(monkeypatch, private_config, crop_option):
    path, doc = private_config
    doc['policy']['crop_result_storage'] = crop_option
    store(path, doc)
    monkeypatch.setattr('app.operator_config.importlib.import_module',
        lambda *_: pytest.fail('invalid crop option imported factory'))
    with pytest.raises(OperatorConfigHold, match='^operator_config_rejected$'):
        load_api_runtime(path)


@pytest.mark.parametrize('fault', ['extra','missing','version','policy_extra','policy_missing',
    'policy_bool','content_extra','content_bool','host','port_bool','relative','traversal','factory'])
def test_closed_schema_rejects_before_factory(monkeypatch, private_config, fault):
    path, doc=private_config
    if fault=='extra': doc['private-test-marker']='untrusted'
    elif fault=='missing': del doc['content_access']
    elif fault=='version': doc['config_version']='unknown-v2'
    elif fault=='policy_extra': doc['policy']['password']='private-test-marker'
    elif fault=='policy_missing': del doc['policy']['connection_limit']
    elif fault=='policy_bool': doc['policy']['market_calculation']=1
    elif fault=='content_extra': doc['content_access']={'owner_uid':0,'reader_gid':0,'unknown':0}
    elif fault=='content_bool': doc['content_access']={'owner_uid':True,'reader_gid':0}
    elif fault=='host': doc['host']='0.0.0.0'
    elif fault=='port_bool': doc['port']=True
    elif fault=='relative': doc['dsn_file']='relative.dsn'
    elif fault=='traversal': doc['artifact_root']='/private/../artifacts'
    elif fault=='factory': doc['dependencies_factory']='module:factory;private-test-marker'
    store(path,doc)
    monkeypatch.setattr('app.operator_config.importlib.import_module', lambda *_:pytest.fail('rejected config imported factory'))
    with pytest.raises(OperatorConfigHold,match='^operator_config_rejected$') as error:
        load_api_runtime(path)
    assert 'private-test-marker' not in str(error.value)


@pytest.mark.parametrize('raw', [b'{"config_version":"a","config_version":"b"}', b'{"port":NaN}',
                               b'[]', b'\xff', b'x'*65537])
def test_invalid_json_or_size_is_closed(monkeypatch,private_config,raw):
    path,_=private_config
    path.write_bytes(raw)
    monkeypatch.setattr('app.operator_config.importlib.import_module', lambda *_:pytest.fail('invalid JSON imported factory'))
    with pytest.raises(OperatorConfigHold,match='^operator_config_rejected$'): load_api_runtime(path)


@pytest.mark.parametrize('fault',['file_mode','parent_mode','file_symlink','parent_symlink','hard_link','fifo','short_key'])
def test_actual_private_metadata_and_paths_are_required(monkeypatch,private_config,tmp_path,fault):
    path,doc=private_config
    if fault=='file_mode': path.chmod(0o644)
    elif fault=='parent_mode': path.parent.chmod(0o750)
    elif fault=='file_symlink':
        target=path.with_suffix('.actual'); path.rename(target); path.symlink_to(target)
    elif fault=='parent_symlink':
        target=tmp_path/'actual'; path.parent.rename(target); path.parent.symlink_to(target,target_is_directory=True)
    elif fault=='hard_link': os.link(path,path.with_suffix('.copy'))
    elif fault=='fifo':
        path.unlink(); os.mkfifo(path,0o600)
    elif fault=='short_key': Path(doc['market_hold_key_file']).write_bytes(b'short')
    monkeypatch.setattr('app.operator_config.importlib.import_module',lambda *_:pytest.fail('bad private input imported factory'))
    with pytest.raises(OperatorConfigHold,match='^operator_config_rejected$'): load_api_runtime(path)


def test_missing_environment_has_fixed_error(monkeypatch):
    monkeypatch.delenv('OSSF_API_CONFIG',raising=False)
    with pytest.raises(OperatorConfigHold,match='^operator_config_rejected$'): api_service()


@pytest.mark.parametrize('target', ['file', 'parent'])
def test_wrong_observed_owner_is_rejected_before_factory(monkeypatch, private_config, target):
    path, _ = private_config
    expected = (path if target == 'file' else path.parent).stat().st_ino
    original = os.fstat
    def wrong_owner(descriptor):
        info = original(descriptor)
        if info.st_ino == expected:
            fields = {name: getattr(info, name) for name in dir(info) if name.startswith('st_')}
            fields['st_uid'] = os.geteuid() + 1
            return SimpleNamespace(**fields)
        return info
    monkeypatch.setattr(operator_config.os, 'fstat', wrong_owner)
    monkeypatch.setattr(operator_config.importlib, 'import_module',
                        lambda *_: pytest.fail('wrong owner imported dependencies'))
    with pytest.raises(OperatorConfigHold, match='^operator_config_rejected$'):
        load_api_runtime(path)


@pytest.mark.parametrize('attribute', ['system.posix_acl_access', 'system.posix_acl_default'])
def test_posix_acl_inspection_refuses_additional_access(monkeypatch, private_config, attribute):
    path, _ = private_config
    monkeypatch.setattr(operator_config.os, 'listxattr', lambda _descriptor: [attribute])
    monkeypatch.setattr(operator_config.importlib, 'import_module',
                        lambda *_: pytest.fail('ACL input imported dependencies'))
    with pytest.raises(OperatorConfigHold, match='^operator_config_rejected$'):
        load_api_runtime(path)


@pytest.mark.parametrize('mutation', ['permissions', 'append', 'same_size', 'unlink'])
def test_real_change_during_read_refuses_input_and_closes_descriptors(monkeypatch, private_config, mutation):
    path, _ = private_config
    inode = path.stat().st_ino
    original = os.read
    before = set(Path('/proc/self/fd').iterdir())
    def changed_read(descriptor, size):
        raw = original(descriptor, size)
        if os.fstat(descriptor).st_ino == inode:
            if mutation == 'permissions': path.chmod(0o644)
            elif mutation == 'append':
                with path.open('ab') as stream: stream.write(b' ')
            elif mutation == 'same_size': path.write_bytes(b' ' * len(raw))
            else: path.unlink()
        return raw
    monkeypatch.setattr(operator_config.os, 'read', changed_read)
    monkeypatch.setattr(operator_config.importlib, 'import_module',
                        lambda *_: pytest.fail('changed input imported dependencies'))
    with pytest.raises(OperatorConfigHold, match='^operator_config_rejected$'):
        load_api_runtime(path)
    assert set(Path('/proc/self/fd').iterdir()) == before


@pytest.mark.parametrize('fault', ['wrong_type', 'missing_verifier', 'exception', 'exit'])
def test_dependency_failure_has_fixed_error_and_no_descriptor_leak(monkeypatch, private_config, fault):
    path, _ = private_config
    calls = []
    def factory(*, config):
        calls.append(config)
        if fault == 'wrong_type': return object()
        if fault == 'missing_verifier': return dependencies(release_verifier=None)
        if fault == 'exception': raise RuntimeError('private-test dependency credential')
        raise SystemExit('private-test dependency credential')
    monkeypatch.setattr(operator_config.importlib, 'import_module',
                        lambda *_: SimpleNamespace(dependencies=factory))
    before = set(Path('/proc/self/fd').iterdir())
    with pytest.raises(OperatorConfigHold, match='^operator_config_rejected$'):
        load_api_runtime(path)
    assert len(calls) == 1 and set(Path('/proc/self/fd').iterdir()) == before


def configure_login(private_config, login_scope, tls_files, *, port=0):
    path, doc = private_config
    base, actual_policy, dsns = login_scope
    certificate, key, _ = tls_files
    base.artifact_root.mkdir(mode=0o700)
    legacy_policy = asdict(actual_policy)
    assert legacy_policy.pop('crop_cycle_calculation_result_storage') is False
    doc.update(policy=legacy_policy, artifact_root=str(base.artifact_root),
               certificate=str(certificate), private_key=str(key), port=port)
    Path(doc['dsn_file']).write_text(dsns['authority'])
    store(path, doc)
    return path, doc


@pytest.mark.parametrize('login_scope', [{'market_calculation': True, 'break_even_calculation': True,
                                        'market_source_storage': True}], indirect=True)
@pytest.mark.parametrize('fault', ['identity', 'grant', 'provider', 'provider_binding', 'tls'])
def test_actual_scram_assembly_refuses_current_identity_grants_provider_and_tls(
        monkeypatch, private_config, login_scope, tls_files, fault):
    path, doc = configure_login(private_config, login_scope, tls_files)
    base, actual_policy, dsns = login_scope
    if fault == 'identity': Path(doc['dsn_file']).write_text(dsns['request'])
    elif fault == 'grant':
        with base.connect() as conn:
            conn.execute(sql.SQL('GRANT SELECT ON {}.jobs TO {}').format(
                sql.Identifier(actual_policy.schema), sql.Identifier(actual_policy.roles['worker'])))
    elif fault == 'tls': Path(doc['private_key']).write_bytes(b'synthetic invalid private PEM')
    calls = []
    def source_factory(*, principal_provider):
        calls.append(principal_provider)
        if fault == 'provider': return object()
        if fault == 'provider_binding':
            from app.market_source_store import MarketSourceStore
            return MarketSourceStore(dsns['authority'], actual_policy.schema,
                runtime_identity=(actual_policy, 'authority'), principal_provider=lambda: None)
        return dependencies().market_source_factory(principal_provider=principal_provider)
    monkeypatch.setitem(sys.modules, 'trusted_operator', SimpleNamespace(
        dependencies=lambda *, config: dependencies(market_source_factory=source_factory)))
    with pytest.raises(OperatorConfigHold, match='^operator_config_rejected$'):
        load_api_runtime(path)
    assert len(calls) == (0 if fault in {'identity', 'grant'} else 1)


@pytest.mark.parametrize('login_scope', [{'market_calculation': True, 'break_even_calculation': True}], indirect=True)
def test_real_operator_entry_starts_tls_bearer_and_refuses_post_start_grant_drift(
        private_config, login_scope, tls_files):
    with socket.socket() as probe:
        probe.bind(('127.0.0.1', 0)); port = probe.getsockname()[1]
    path, doc = configure_login(private_config, login_scope, tls_files, port=port)
    base, actual_policy, _ = login_scope
    directory = path.parent
    # This explicitly synthetic dependency module is installed only in the disposable test directory.
    (directory/'trusted_operator.py').write_text('''from test_api_runtime import dependencies
from app.api_runtime import ApiRuntimeConfig
from app.cli_contracts import _canonical
from app.http_identity import current_principal
from app.research_registry import ResearchRegistry
from hashlib import sha256
from test_research_registry import document
def source_factory(*, principal_provider):
    assert principal_provider is current_principal
    assert current_principal() is None
    return dependencies().market_source_factory(principal_provider=principal_provider)
def dependencies_factory(*, config):
    assert type(config) is ApiRuntimeConfig
    value = document()
    value['registrations'][0]['tenant_id'] = 'tenant-1'
    raw = _canonical(value)
    return dependencies(market_source_factory=source_factory,
        research_registry=ResearchRegistry(raw, sha256(raw).hexdigest()))
''')
    doc['dependencies_factory'] = 'trusted_operator:dependencies_factory'
    store(path, doc)
    backend = Path(__file__).resolve().parents[1]
    environment = {'PATH': os.defpath, 'LANG': 'C.UTF-8', 'OSSF_API_CONFIG': str(path),
        'PYTHONPATH': os.pathsep.join(map(str, (backend, backend/'tests', directory)))}
    process = subprocess.Popen([sys.executable, '-m', 'app.api_serve', '--factory',
        'app.operator_config:api_service'], cwd=backend, env=environment,
        stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    context = ssl.create_default_context(cafile=doc['certificate'])
    def call(route='/openapi.json', *, method='GET', body=None, authenticated=True):
        conn = http.client.HTTPSConnection('127.0.0.1', port, timeout=45, context=context)
        try:
            headers = {'Authorization': 'Bearer '+TOKEN.decode()} if authenticated else {}
            if body is not None: headers['Content-Type'] = 'application/json'
            conn.request(method, route, json.dumps(body) if body is not None else None, headers)
            response = conn.getresponse()
            return response.status, json.loads(response.read())
        finally: conn.close()
    try:
        deadline = time.monotonic()+120
        while True:
            assert process.poll() is None, 'synthetic operator API exited before TLS readiness'
            try: response = call(authenticated=False); break
            except OSError: pass
            assert time.monotonic()<deadline, 'synthetic operator API not ready'
            time.sleep(0.05)
        assert response[0] == 401
        assert call()[1] == json.loads((backend.parent/'contracts/openapi-v1.json').read_bytes())
        from test_api_location_research import BODY
        accepted = call('/v1/locations', method='POST', body=BODY)
        assert accepted[0] == 202
        route = '/v1/jobs/'+accepted[1]['research_job']['job_id']
        assert call(route)[1] == accepted[1]['research_job']
        with base.connect() as conn:
            conn.execute(sql.SQL('GRANT SELECT ON {}.jobs TO {}').format(
                sql.Identifier(actual_policy.schema), sql.Identifier(actual_policy.roles['worker'])))
        assert call(route)[0] == 503
    finally:
        process.terminate()
        try: stdout, stderr = process.communicate(timeout=10)
        except subprocess.TimeoutExpired: process.kill(); stdout, stderr = process.communicate(timeout=5)
    assert process.returncode == -signal.SIGTERM and stdout == b''
    assert all(value not in stderr for value in (TOKEN, str(path).encode(), b'passfile',
        Path(doc['thermal_gate_key_file']).read_bytes(), Path(doc['market_hold_key_file']).read_bytes()))


@pytest.mark.parametrize('startup_option', ['omit', False, True])
def test_startup_option_preserves_old_operator_and_explicit_selection(monkeypatch, private_config, startup_option):
    path, doc = private_config
    if startup_option == 'omit':
        doc['policy'].pop('crop_startup_result_storage', None)
    else:
        doc['policy']['crop_startup_result_storage'] = startup_option
    store(path, doc)
    calls = isolated_assembly(monkeypatch)
    load_api_runtime(path)
    assert len(calls)==1 and calls[0].policy.crop_startup_result_storage is (startup_option is True)


@pytest.mark.parametrize('startup_option', [0, 1, 'false', None])
def test_startup_option_is_boolean_before_dependency_import(monkeypatch, private_config, startup_option):
    path, doc = private_config
    doc['policy']['crop_startup_result_storage'] = startup_option
    store(path, doc)
    monkeypatch.setattr(operator_config.importlib, 'import_module',
        lambda *_: pytest.fail('invalid startup flag imported dependencies'))
    with pytest.raises(OperatorConfigHold, match='^operator_config_rejected$'):
        load_api_runtime(path)


@pytest.mark.parametrize('cycle_option', ['omit', False, True])
def test_cycle_storage_option_preserves_existing_operator_config(monkeypatch, private_config, cycle_option):
    path, doc = private_config
    if cycle_option == 'omit':
        doc['policy'].pop('crop_cycle_result_storage', None)
    else:
        doc['policy']['crop_cycle_result_storage'] = cycle_option
    store(path, doc)
    calls = isolated_assembly(monkeypatch)
    load_api_runtime(path)
    assert len(calls) == 1
    assert calls[0].policy.crop_cycle_result_storage is (cycle_option is True)
    assert calls[0].policy.crop_startup_result_storage is False


@pytest.mark.parametrize('cycle_option', [0, 1, 'false', None, [], {}])
def test_cycle_storage_invalid_type_rejected_before_dependency_import(monkeypatch, private_config, cycle_option):
    path, doc = private_config
    doc['policy']['crop_cycle_result_storage'] = cycle_option
    store(path, doc)
    monkeypatch.setattr(operator_config.importlib, 'import_module',
        lambda *_: pytest.fail('invalid cycle flag imported dependencies'))
    with pytest.raises(OperatorConfigHold, match='^operator_config_rejected$'):
        load_api_runtime(path)
