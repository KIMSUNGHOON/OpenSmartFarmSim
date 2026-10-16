"""Protected solar configuration and pre-I/O assembly boundaries."""
from dataclasses import replace
import json
import os
from pathlib import Path
import subprocess
import sys
from types import SimpleNamespace

import pytest
from app import crop_greenhouse_solar_operator_config as loader
from app import operator_config as original
from app.api_runtime import ApiRuntime,ApiRuntimeDependencies
from test_api_runtime import config,dependencies,policy
from test_operator_config import private_config,store,isolated_assembly


def fd_inventory():
    result={}
    for path in Path('/proc/self/fd').iterdir():
        try:
            info=path.stat();result[path.name]=(os.readlink(path),info.st_dev,info.st_ino)
        except FileNotFoundError:pass
    return result


def save(name, value):
    root = os.environ.get('OSSF_SOLAR_RUNTIME_EVIDENCE')
    if root:
        with (Path(root)/name).open('x') as f:
            os.fchmod(f.fileno(), 0o400)
            json.dump(value, f, sort_keys=True, indent=2); f.flush(); os.fsync(f.fileno())


@pytest.fixture
def solar_config(private_config):
    path, doc = private_config
    doc['config_version'] = loader.VERSION
    store(path, doc)
    return path, doc


@pytest.mark.parametrize('enabled', [False, True])
@pytest.mark.parametrize('joint,ventilation', [(False, False), (False, True), (True, False), (True, True)])
def test_explicit_version_and_closed_optional_calculation_coexistence(solar_config, monkeypatch, enabled, joint, ventilation):
    path, doc = solar_config
    doc['policy'][loader.FLAG] = enabled
    doc['policy']['crop_cycle_result_storage'] = enabled or joint or ventilation
    doc['policy'][loader.CALCULATION_FLAG] = enabled
    doc['policy'][original.JOINT_RESULT_FLAG] = joint
    doc['policy'][original.VENTILATION_RESULT_FLAG] = ventilation
    store(path, doc); calls = isolated_assembly(monkeypatch)
    result = loader.load_solar_api_runtime(path)
    assert result[0] == 'assembled' and calls[0].policy.crop_greenhouse_solar_result_storage is enabled
    assert calls[0].policy.crop_cycle_calculation_result_storage is enabled
    assert calls[0].policy.crop_climate_joint_result_storage is joint
    assert calls[0].policy.crop_greenhouse_ventilation_result_storage is ventilation
    assert 'synthetic-' not in repr(calls[0])


@pytest.mark.parametrize('fault', ['missing-flag', 'extra', 'version', 'policy-extra', 'policy-missing',
    'solar-int', 'solar-string', 'solar-null', 'legacy-prerequisite', 'calculation-prerequisite',
    'calculation-int', 'joint-int', 'joint-prerequisite', 'vent-int', 'vent-prerequisite', 'host', 'port', 'factory', 'relative-path'])
def test_closed_configuration_fails_before_dependency_import(solar_config, monkeypatch, fault):
    path, doc = solar_config; p = doc['policy']
    if fault == 'missing-flag': del p[loader.FLAG]
    elif fault == 'extra': doc['unknown'] = True
    elif fault == 'version': doc['config_version'] = 'operator-api-config-v1'
    elif fault == 'policy-extra': p['unknown'] = False
    elif fault == 'policy-missing': del p['owner']
    elif fault == 'solar-int': p[loader.FLAG] = 1
    elif fault == 'solar-string': p[loader.FLAG] = 'true'
    elif fault == 'solar-null': p[loader.FLAG] = None
    elif fault == 'legacy-prerequisite': p[loader.FLAG] = True
    elif fault == 'calculation-prerequisite': p[loader.CALCULATION_FLAG] = True
    elif fault == 'calculation-int': p[loader.CALCULATION_FLAG] = 0
    elif fault == 'joint-int': p[original.JOINT_RESULT_FLAG] = 0
    elif fault == 'joint-prerequisite': p[original.JOINT_RESULT_FLAG] = True
    elif fault == 'vent-int': p[original.VENTILATION_RESULT_FLAG] = 1
    elif fault == 'vent-prerequisite': p[original.VENTILATION_RESULT_FLAG] = True
    elif fault == 'host': doc['host'] = '0.0.0.0'
    elif fault == 'port': doc['port'] = True
    elif fault == 'factory': doc['dependencies_factory'] = 'not:a:reference'
    elif fault == 'relative-path': doc['dsn_file'] = 'relative.dsn'
    store(path, doc)
    monkeypatch.setattr(original.importlib, 'import_module', lambda *_: pytest.fail('invalid configuration imported dependencies'))
    before = fd_inventory()
    with pytest.raises(original.OperatorConfigHold, match='^operator_config_rejected$'):
        loader.load_solar_api_runtime(path)
    assert fd_inventory() == before


@pytest.mark.parametrize('raw', [b'{"port":1,"port":2}', b'{"port":NaN}', b'\xff', b' ' * 65537])
def test_invalid_json_size_and_encoding_are_closed(solar_config, monkeypatch, raw):
    path, _ = solar_config; path.write_bytes(raw)
    monkeypatch.setattr(original.importlib, 'import_module', lambda *_: pytest.fail('invalid JSON imported dependencies'))
    with pytest.raises(original.OperatorConfigHold, match='^operator_config_rejected$'):
        loader.load_solar_api_runtime(path)


@pytest.mark.parametrize('phase', ['factory', 'assembly'])
@pytest.mark.parametrize('field', ['config', 'dsn_file', 'thermal_gate_key_file', 'market_hold_key_file',
    'certificate', 'private_key', 'permissions'])
def test_protected_files_are_rechecked_after_factory_and_assembly(solar_config, monkeypatch, phase, field):
    path, doc = solar_config; trace = []
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
        loader.load_solar_api_runtime(path)
    assert trace == (['factory'] if phase == 'factory' else ['factory', 'assembly'])
    assert fd_inventory() == before


@pytest.mark.parametrize('fault', ['type', 'exception', 'exit'])
def test_dependency_failures_have_fixed_error(solar_config, monkeypatch, fault):
    def factory(**kwargs):
        if fault == 'type': return object()
        if fault == 'exception': raise RuntimeError('private configuration marker')
        raise SystemExit('private configuration marker')
    monkeypatch.setattr(original.importlib, 'import_module', lambda *_: SimpleNamespace(dependencies=factory))
    with pytest.raises(original.OperatorConfigHold, match='^operator_config_rejected$'):
        loader.load_solar_api_runtime(solar_config[0])


@pytest.mark.parametrize('flag,store_factory,query_factory,legacy', [
    (False, True, False, False), (False, False, True, False), (False, True, True, False),
    (True, False, False, True), (True, True, False, True), (True, False, True, True),
    (True, True, True, False)])
def test_flag_factory_and_legacy_prerequisite_fail_before_io(monkeypatch, flag, store_factory, query_factory, legacy):
    def forbidden(*a, **kw): pytest.fail('invalid solar assembly performed I/O')
    monkeypatch.setattr('app.api_runtime.JobStore', forbidden)
    p = replace(policy(), crop_greenhouse_solar_result_storage=flag, crop_cycle_result_storage=legacy)
    deps = dependencies(crop_cycle_result_store_factory=forbidden if legacy else None,
        crop_greenhouse_solar_result_store_factory=forbidden if store_factory else None,
        crop_greenhouse_solar_current_query_factory=forbidden if query_factory else None)
    with pytest.raises(ValueError, match='^API runtime assembly rejected$'): ApiRuntime(config(policy=p), deps)


@pytest.mark.parametrize('field', ['crop_greenhouse_solar_result_store_factory', 'crop_greenhouse_solar_current_query_factory'])
def test_new_dependency_fields_require_callables(field):
    with pytest.raises(ValueError, match='^API runtime dependencies rejected$'): dependencies(**{field: True})


def test_environment_entrypoint_uses_new_loader(monkeypatch):
    service = object(); calls = []
    monkeypatch.setenv('OSSF_API_CONFIG', '/private/solar.json')
    monkeypatch.setattr(loader, 'load_solar_api_runtime', lambda path: calls.append(path) or SimpleNamespace(service=service))
    assert loader.api_service() is service and calls == [Path('/private/solar.json')]
    monkeypatch.delenv('OSSF_API_CONFIG')
    with pytest.raises(original.OperatorConfigHold, match='^operator_config_rejected$'): loader.api_service()


@pytest.mark.parametrize('first', ['app.crop_greenhouse_solar_operator_config', 'app.api_runtime'])
def test_fresh_import_does_not_connect_or_load_solar_math(first):
    code = '''import importlib,os,socket,sys,psycopg
def deny(*a,**k):raise AssertionError('import performed I/O')
psycopg.connect=deny;socket.create_connection=deny
fd=len(os.listdir('/proc/self/fd'));importlib.import_module(sys.argv[1])
assert 'app.crop_greenhouse_solar_current_query' not in sys.modules
assert 'app.crop_climate_joint_integration' not in sys.modules
assert 'app.crop_greenhouse_solar_joint' not in sys.modules
assert len(os.listdir('/proc/self/fd'))==fd
'''
    child = subprocess.run([sys.executable, '-B', '-c', code, first], capture_output=True, timeout=30)
    assert child.returncode == 0, child.stderr.decode()
