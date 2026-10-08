"""Private research runtime configurations fail before service assembly."""
from hashlib import sha256
import importlib.util
import json
from pathlib import Path

import pytest

SCRIPT = Path(__file__).resolve().parents[2]/'research/crop-cycle-registered-runtime.py'


@pytest.fixture
def runtime():
    spec = importlib.util.spec_from_file_location('registered_runtime_config', SCRIPT)
    module = importlib.util.module_from_spec(spec); spec.loader.exec_module(module)
    return module


def private(path, value):
    raw = json.dumps(value, sort_keys=True, separators=(',', ':')).encode()
    if path.exists(): path.chmod(0o600)
    path.write_bytes(raw); path.chmod(0o400)
    return sha256(raw).hexdigest()


@pytest.fixture
def private_config(runtime, tmp_path):
    names = ('dsn','registry','scope','request','proof','thermal','market','input','server')
    paths = {name:str(tmp_path/(name+'.private')) for name in names}
    for path in paths.values(): private(Path(path), {})
    value = {key:None for key in runtime.FIELDS}
    value.update(version=runtime.VERSION, scope='owned_synthetic_only',code_sha256=runtime.CODE_SHA256,
        dsn_file=paths['dsn'],registry_file=paths['registry'],market_scope_file=paths['scope'],request_file=paths['request'],
        request_sha256=sha256(Path(paths['request']).read_bytes()).hexdigest(),
        keys={name:paths[name] for name in ('thermal','market','input','server')},
        input={name:None for name in ('directory','root_sha256','evidence_file','issuer_id','key_id')},
        static_sha256={path:sha256(Path(path).read_bytes()).hexdigest() for path in paths.values()})
    value['input']['evidence_file'] = paths['proof']
    return tmp_path/'runtime.json', value


def test_modified_config_rejects_before_assembly(runtime, private_config, monkeypatch):
    calls = []; monkeypatch.setattr(runtime, '_assemble', lambda *a: calls.append(True))
    path, value = private_config; digest = private(path, value)
    runtime.load_runtime(path,digest); assert calls == [True]; calls.clear()
    value['policy'] = {'changed':True}; private(path, value)
    with pytest.raises(ValueError): runtime.load_runtime(path, digest)
    assert calls == []


@pytest.mark.parametrize('fault', ['old-version', 'unknown-field', 'world-readable', 'missing-field'])
def test_invalid_private_configuration_rejects_before_assembly(runtime, private_config, monkeypatch, fault):
    calls = []; monkeypatch.setattr(runtime, '_assemble', lambda *a: calls.append(True))
    path, value = private_config
    digest = private(path,value); runtime.load_runtime(path,digest); assert calls == [True]; calls.clear()
    if fault == 'old-version': value['version'] = 'old-owned-runtime-v0'
    elif fault == 'unknown-field': value['unexpected'] = 'not accepted'
    elif fault == 'missing-field': value.pop('policy')
    digest = private(path, value)
    if fault == 'world-readable': path.chmod(0o644)
    with pytest.raises(ValueError): runtime.load_runtime(path, digest)
    assert calls == []


def test_fixed_file_tamper_rejects_before_assembly(runtime, private_config, monkeypatch):
    calls = []; monkeypatch.setattr(runtime,'_assemble',lambda *a:calls.append(True))
    path,value = private_config; digest = private(path,value)
    runtime.load_runtime(path,digest); assert calls == [True]; calls.clear()
    private(Path(value['keys']['server']), {'changed':True})
    with pytest.raises(ValueError): runtime.load_runtime(path,digest)
    assert calls == []
