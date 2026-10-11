"""Explicit prefix assembly and unpaused independent worker over verified TLS."""
from dataclasses import replace
from copy import deepcopy
from hashlib import sha256
import json
import os
from pathlib import Path
import subprocess
import sys
import time
from types import SimpleNamespace
from urllib.parse import urlencode

import pytest

from app import crop_greenhouse_ventilation_operator_config as loader
from app import api_crop_greenhouse_ventilation_prefix as public
from app.api_runtime import ApiRuntime
import test_crop_greenhouse_ventilation_execution_runtime as execution_reference
from test_crop_greenhouse_ventilation_execution_runtime import (
    native, execution_config, ventilation_config, private_config, store, isolated_assembly,
    tls_files, login_database, original_login_scope, login_scope, authoring, farm_setup,
    setup as original_setup, profiles, LOGIN, config, dependencies, original, calculation, current,
    fd_inventory, TOKEN, NOW, database_cleanup, served, POST, SCOPES,
    consumer, progress, http_identity)


@pytest.fixture
def setup(authoring, tmp_path, profiles, request, monkeypatch):
    inputs = execution_reference.worker_reference.producer.reference.inputs
    case = deepcopy(inputs.reference.reference.CASES[6])
    case.update(step_count=64, output_steps=list(range(0, 65, 8)))
    for event in case['events']:
        event['step_index'] *= 4
    if getattr(request, 'param', None) == 'hold':
        case['events'][-1]['event']['values']['leaf']['value'] = 50000
    packet = inputs.packet
    with monkeypatch.context() as patch:
        patch.setattr(inputs, 'packet', lambda directory, profiles, origin=None:
            packet(directory, profiles, case, origin))
        return original_setup.__wrapped__(authoring, tmp_path, profiles,
            SimpleNamespace(param=None), monkeypatch)


def save(name, value):
    root = os.environ.get('OSSF_VENTILATION_PREFIX_RUNTIME_EVIDENCE')
    if root:
        with (Path(root)/(name+'.json')).open('x') as f:
            os.fchmod(f.fileno(), 0o400)
            json.dump(value, f, sort_keys=True, indent=2); f.flush(); os.fsync(f.fileno())


@pytest.fixture
def prefix_config(execution_config):
    path, doc = execution_config
    doc.update(config_version=loader.PREFIX_VERSION, crop_greenhouse_ventilation_prefix=True)
    store(path, doc)
    return path, doc


@pytest.mark.parametrize('enabled', [False, True])
def test_prefix_operator_version_is_explicit(prefix_config, monkeypatch, enabled):
    path, doc = prefix_config; doc[loader.PREFIX_FLAG] = enabled; store(path, doc)
    calls = isolated_assembly(monkeypatch)
    assert loader.load_ventilation_api_runtime(path)[0] == 'assembled'
    assert calls[0].crop_greenhouse_ventilation_prefix is enabled
    assert calls[0].crop_greenhouse_ventilation_execution is True


@pytest.mark.parametrize('fault', ['missing', 'extra', 'null', 'int-zero', 'int-one',
    'string', 'list', 'dict', 'execution-disabled', 'joint-disabled', 'cycle-disabled',
    'policy-flag', 'execution-version', 'reader-version'])
def test_closed_prefix_config_rejected_before_factory(prefix_config, monkeypatch, fault):
    path, doc = prefix_config
    invalid = {'null': None, 'int-zero': 0, 'int-one': 1, 'string': 'true', 'list': [], 'dict': {}}
    if fault in invalid: doc[loader.PREFIX_FLAG] = invalid[fault]
    elif fault == 'missing': del doc[loader.PREFIX_FLAG]
    elif fault == 'extra': doc['unknown'] = True
    elif fault == 'execution-disabled': doc[loader.EXECUTION_FLAG] = False
    elif fault == 'joint-disabled': doc['policy'][loader.FLAG] = False
    elif fault == 'cycle-disabled': doc['policy']['crop_cycle_result_storage'] = False
    elif fault == 'policy-flag': doc['policy'][loader.PREFIX_FLAG] = True
    elif fault == 'execution-version': doc['config_version'] = loader.EXECUTION_VERSION
    else: doc['config_version'] = loader.VERSION
    store(path, doc)
    monkeypatch.setattr(original.importlib, 'import_module', lambda *_: pytest.fail('invalid config imported factory'))
    with pytest.raises(original.OperatorConfigHold, match='^operator_config_rejected$'):
        loader.load_ventilation_api_runtime(path)


@pytest.mark.parametrize('load', [original.load_api_runtime, calculation.load_calculation_api_runtime])
def test_older_operator_loaders_reject_prefix_version(prefix_config, load):
    with pytest.raises(original.OperatorConfigHold, match='^operator_config_rejected$'):
        load(prefix_config[0])


@pytest.mark.parametrize('fixture', ['ventilation_config', 'execution_config'])
def test_existing_versions_keep_prefix_disabled(fixture, request, monkeypatch):
    path, _ = request.getfixturevalue(fixture); calls = isolated_assembly(monkeypatch)
    assert loader.load_ventilation_api_runtime(path)[0] == 'assembled'
    assert calls[0].crop_greenhouse_ventilation_prefix is False


@pytest.mark.parametrize('value', [None, 0, 1, 'true', [], {}, True])
def test_direct_config_rejects_prefix_coercion_and_missing_execution(value):
    with pytest.raises(ValueError, match='^API runtime configuration rejected$'):
        config(crop_greenhouse_ventilation_prefix=value)


@pytest.mark.parametrize('field', ['config', 'dsn_file', 'thermal_gate_key_file',
    'market_hold_key_file', 'certificate', 'private_key', 'permissions'])
@pytest.mark.parametrize('phase', ['factory', 'assembly'])
def test_prefix_private_files_rechecked(prefix_config, monkeypatch, field, phase):
    import test_crop_greenhouse_ventilation_runtime as reader
    reader.test_protected_files_are_rechecked_after_factory_and_assembly(prefix_config, monkeypatch, phase, field)


def test_default_schema_never_imports_or_installs_prefix():
    script = '''import sys,os,json,socket,psycopg
before=len(os.listdir('/proc/self/fd'))
def denied(*a,**kw):raise AssertionError('unexpected connection')
socket.create_connection=denied;psycopg.connect=denied
from app.api_openapi import contract_document,CONTRACT_PATH
doc=contract_document();baseline=json.loads(CONTRACT_PATH.read_bytes())
assert doc['paths']==baseline['paths'] and doc['components']['schemas']==baseline['components']['schemas']
assert not any('/prefix' in p for p in doc['paths'])
assert all('app.'+m not in sys.modules for m in ('crop_greenhouse_ventilation_prefix','api_crop_greenhouse_ventilation_prefix','api_crop_greenhouse_ventilation_prefix_routes'))
assert len(os.listdir('/proc/self/fd'))==before
print(json.dumps({'paths':len(doc['paths']),'schemas':len(doc['components']['schemas']),'prefix_imports':0,'connections':0,'FD_unchanged':True}))
'''
    child = subprocess.run([sys.executable, '-B', '-c', script], capture_output=True, timeout=30)
    assert child.returncode == 0, child.stderr.decode()
    save('default-schema', json.loads(child.stdout))


@pytest.fixture
def prefix_native(native, tmp_path, monkeypatch):
    c = native; cfg = replace(c.config, crop_greenhouse_ventilation_prefix=True)
    doc = json.loads(c.path.read_bytes()); doc.update(config_version=loader.PREFIX_VERSION, crop_greenhouse_ventilation_prefix=True)
    path = tmp_path/'prefix-operator.private.json'; path.touch(mode=0o600); store(path, doc)
    def factory(*, config):
        assert config == cfg; return c.deps
    monkeypatch.setattr(sys.modules['trusted_operator'], 'dependencies', factory)
    before = fd_inventory()
    with monkeypatch.context() as patch:
        calls = progress.forbid(patch); runtime = loader.load_ventilation_api_runtime(path)
        assert not any(calls.values())
    assert fd_inventory() == before
    q = runtime.ventilation_prefix_query
    assert q.query is runtime.ventilation_execution_query and q.jobs is runtime.jobs
    assert q.server is runtime.ventilation_crop_results.server
    assert q.server.binding.farms is runtime.farm_authoring
    assert runtime.ventilation_execution_query.results is runtime.ventilation_crop_results
    assert runtime.jobs.principal_provider is http_identity.current_principal
    c.prefix_runtime = runtime
    return c


def unpaused_consumer(c, tmp_path):
    pack, factory = execution_reference.ventilation_factory(c.worker, c.value, tmp_path)
    raw = factory.read_text(); assert raw.count('chunk_budget=128') == 1
    raw = raw.replace('chunk_budget=128', 'chunk_budget=8')
    diagnostic = '''close=worker._close
def observed_close(lease,kind,reason):
 import traceback
 path=directory/('close-'+str(lease['attempt'])+'.private.json')
 with path.open('x') as f:
  __import__('os').fchmod(f.fileno(),0o600)
  json.dump({'kind':kind,'reason':reason,'traceback':traceback.format_exc(limit=8)},f)
 return close(lease,kind,reason)
worker._close=observed_close
'''
    from textwrap import indent
    factory.write_text(raw.replace('    return loop\n', indent(diagnostic, '    ')+'    return loop\n'))
    assert not (tmp_path/'block').exists()
    return pack, factory


def proofs(tmp_path):
    values = [json.loads(p.read_bytes()) for p in sorted(tmp_path.glob('attempt-*.private.json'))]
    assert values and all(p['actual_scram'] for p in values)
    return values


@LOGIN
@pytest.mark.parametrize('setup,expected', [(None, 'completed'), ('hold', 'hold')], indirect=['setup'])
def test_actual_unpaused_worker_prefix_to_original_terminal(prefix_native, tmp_path, monkeypatch, expected):
    c = prefix_native; rt = c.prefix_runtime; captured = []
    serialize = public._public_bytes
    def record(model):
        raw = serialize(model); captured.append(raw); return raw
    monkeypatch.setattr(public, '_public_bytes', record)
    pack, factory = unpaused_consumer(c, tmp_path)
    observations = []; accepted = []; paired_pages = []; transient = 0
    try:
        with served(rt, c.config.certificate) as (send, replies):
            status, raw = send('POST', POST, c.raw); assert status == 202; job = json.loads(raw)['job_id']
            path = '/v1/jobs/'+job+'/crop-greenhouse-ventilation-execution'; prefix = path+'/prefix'
            with monkeypatch.context() as patch:
                calls = progress.forbid(patch); status, raw = send('GET', prefix)
                assert status == 200 and raw == captured[-1] and json.loads(raw)['prefix_status'] == 'none'
                assert not any(calls.values())
            with consumer.legacy.process_consumer(tmp_path, 'joint_operator:build') as (process, events, errors):
                deadline = time.monotonic()+240
                with monkeypatch.context() as patch:
                    calls = progress.forbid(patch)
                    while True:
                        assert time.monotonic() < deadline and process.poll() is None
                        status, raw = send('GET', prefix)
                        assert status in (200, 503), raw
                        if status == 503:
                            transient += 1; observations.append({'status': 503}); time.sleep(.1); continue
                        assert raw == captured[-1]
                        value = json.loads(raw)
                        observations.append({'status': status, 'prefix_status': value['prefix_status'],
                            'state': value['job']['state'], 'reference': value.get('reference'), 'summary': value['summary']})
                        if value['prefix_status'] == 'closed': break
                        if value['prefix_status'] == 'accepted':
                            assert value['job']['state'] in ('queued', 'simulating')
                            accepted.append(value)
                            if not all(value['summary']['counts'].values()):
                                time.sleep(.1)
                                continue
                            selector = value['reference']['selector']
                            pages = {}
                            for kind in ('events', 'samples'):
                                status, page = send('GET', prefix+'/'+kind+'?'+urlencode(selector))
                                assert status in (200, 409, 503), page
                                if status == 200:
                                    assert page == captured[-1]
                                    rows = json.loads(page); assert rows['reference']['selector'] == selector
                                    pages[kind] = rows['page']['records']
                                    observations.append({'status': 200, 'page': kind,
                                        'count': len(pages[kind]), 'selector': selector})
                                else: observations.append({'status': status, 'page': kind})
                            if set(pages) == {'events', 'samples'}:
                                assert pages['events'] and pages['samples']
                                paired_pages.append({'selector': selector, 'pages': pages})
                        time.sleep(.1)
                    assert not any(calls.values())
                consumer.legacy.wait_for(lambda: bool(list(tmp_path.glob('attempt-*.private.json'))), process, timeout=30)
            assert process.returncode == 0 and errors == ['']
            attempts = proofs(tmp_path)
            save('observed-'+expected, {'observations': observations, 'events': events, 'attempts': attempts})
            assert attempts[-1]['state'] == ('succeeded' if expected == 'completed' else 'hold')
            assert accepted and paired_pages, 'no public running selector with both original pages'
            with monkeypatch.context() as patch:
                calls = progress.forbid(patch); status, raw = send('GET', path); assert status == 200
                outcome = json.loads(raw); selected = outcome['result']; assert selected['status'] == expected
                farm = json.loads(c.raw)['farm']
                expected_raw = current.VentilationCurrentQuery(c.worker.results).read('tenant-1', selected['result_id'], farm, view='summary')
                status, raw = send('GET', '/v1/crop-greenhouse-ventilation-research-results/'+selected['result_id']+'?'+urlencode(farm))
                assert status == 200 and raw == expected_raw and not any(calls.values())
                for kind, limit in (('events', 8), ('samples', 64)):
                    terminal = json.loads(current.VentilationCurrentQuery(c.worker.results).read(
                        'tenant-1', selected['result_id'], farm, view=kind, offset=0, limit=limit))
                    original_rows = terminal['page']['records']
                    for pair in paired_pages:
                        rows = pair['pages'][kind]
                        assert rows == original_rows[:len(rows)]
                assert not any(calls.values())
            assert events[-1]['event'] == 'stopped'
        save('automatic-'+expected, {'actual_scram': True, 'verified_TLS': True, 'automatic_independent_worker': True,
            'test_pause': False, 'chunk_budget': 8, 'running_accepted_count': len(accepted), 'transient_503_count': transient,
            'same_selector_events_samples_200': len(paired_pages), 'original_running_rows_equal_terminal': True,
            'fixture_step_count': 64, 'fixture_simulated_seconds': 128,
            'observations': observations, 'original_terminal_bytes': True, 'read_calls': calls,
            'process_exit': process.returncode, 'attempts': attempts, 'events': events, 'replies': replies})
    finally:
        pack.unlink(); (tmp_path/'proof.private.json').unlink()


@LOGIN
def test_actual_unpaused_cancel_closes_prefix(prefix_native, tmp_path, monkeypatch):
    c = prefix_native; pack, factory = unpaused_consumer(c, tmp_path)
    try:
        with served(c.prefix_runtime, c.config.certificate) as (send, replies):
            status, raw = send('POST', POST, c.raw); assert status == 202; job = json.loads(raw)['job_id']
            path = '/v1/jobs/'+job+'/crop-greenhouse-ventilation-execution'
            with consumer.legacy.process_consumer(tmp_path, 'joint_operator:build') as (process, events, errors):
                consumer.legacy.wait_for(lambda: c.worker.jobs.get_job('tenant-1', job)['state'] == 'simulating', process, timeout=30)
                status, raw = send('POST', path+'/cancel'); assert status == 200 and json.loads(raw)['cancel_requested']
                consumer.legacy.wait_for(lambda: bool(list(tmp_path.glob('attempt-*.private.json'))), process, timeout=60)
            assert process.returncode == 0 and errors == [''] and proofs(tmp_path)[-1]['state'] == 'canceled'
            with monkeypatch.context() as patch:
                calls = progress.forbid(patch); status, raw = send('GET', path+'/prefix'); value = json.loads(raw)
                assert status == 200 and value['prefix_status'] == 'closed' and value['reference'] is None
                assert value['summary'] is None and value['page'] is None and not any(calls.values())
            execution_reference.worker_reference.no_published_result(c.worker, job)
        save('cancel', {'actual_scram': True, 'verified_TLS': True, 'test_pause': False, 'worker_acknowledged': True,
            'process_exit': process.returncode, 'attempts': proofs(tmp_path), 'read_calls': calls, 'replies': replies})
    finally:
        pack.unlink(); (tmp_path/'proof.private.json').unlink()


@LOGIN
def test_disabled_runtime_skips_prefix_installer(native, monkeypatch):
    import app.api_crop_greenhouse_ventilation_prefix_routes as route
    monkeypatch.setattr(route, 'install_ventilation_prefix_routes', lambda *a, **kw: pytest.fail('disabled prefix installed'))
    for enabled in (False, True):
        rt = ApiRuntime(replace(native.config, crop_greenhouse_ventilation_execution=enabled), native.deps)
        assert rt.ventilation_prefix_query is None
        with served(rt, native.config.certificate) as (send, replies):
            path = '/v1/jobs/11111111-1111-4111-8111-111111111111/crop-greenhouse-ventilation-execution/prefix'
            assert all(send('GET', path+suffix)[0] == 404 for suffix in ('', '/samples', '/events'))
    save('disabled', {'installer_calls': 0, 'routes_absent': True, 'actual_scram': True, 'verified_TLS': True})
