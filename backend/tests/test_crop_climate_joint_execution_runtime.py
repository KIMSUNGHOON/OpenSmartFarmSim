"""Explicit API assembly and an independent consumer of the same actual job."""
from contextlib import contextmanager
from dataclasses import asdict, replace
from datetime import timedelta
from hashlib import sha256
import http.client
import json
import os
from pathlib import Path
import signal
import ssl
import sys
import threading
import time
from types import SimpleNamespace
from urllib.parse import urlencode

import pytest

from app import crop_climate_joint_operator_config as loader
from app import crop_climate_joint_execution_worker as execution
from app import http_identity
from app.api_runtime import ApiRuntime
from test_crop_climate_joint_runtime import (joint_config, private_config, store,
    isolated_assembly, tls_files, login_database, original_login_scope, login_scope,
    authoring, farm_setup, setup, profiles, LOGIN, config, dependencies, original,
    calculation, current, fd_inventory, TOKEN, NOW, database_cleanup)
import test_crop_climate_joint_runtime as reader
import test_joint_deterministic_work as consumer
import test_crop_climate_joint_execution_query as progress

POST = '/v1/crop-climate-joint-executions'
SCOPES = frozenset({'simulation_create', 'simulation_execute', 'metadata', 'cancel',
    *reader.READ_SCOPES, *execution.checkpoints.execution.permissions.WRITE_SCOPES})


def save(name, value):
    root = os.environ.get('OSSF_JOINT_EXECUTION_RUNTIME_EVIDENCE')
    if root:
        with (Path(root)/(name+'.json')).open('x') as f:
            os.fchmod(f.fileno(), 0o400)
            json.dump(value, f, sort_keys=True, indent=2); f.flush(); os.fsync(f.fileno())


@pytest.fixture
def execution_config(joint_config):
    path, doc = joint_config
    doc.update(config_version=loader.EXECUTION_VERSION, crop_climate_joint_execution=True)
    doc['policy'].update(crop_climate_joint_result_storage=True, crop_cycle_result_storage=True)
    store(path, doc)
    return path, doc


@pytest.mark.parametrize('enabled', [False, True])
def test_explicit_execution_version_keeps_a_strict_flag(execution_config, monkeypatch, enabled):
    path, doc = execution_config; doc[loader.EXECUTION_FLAG] = enabled; store(path, doc)
    calls = isolated_assembly(monkeypatch)
    assert loader.load_joint_api_runtime(path)[0] == 'assembled'
    assert calls[0].crop_climate_joint_execution is enabled


@pytest.mark.parametrize('flag', [None, 0, 1, 'true', [], {}])
def test_execution_flag_rejects_coercion_before_import(execution_config, monkeypatch, flag):
    path, doc = execution_config; doc[loader.EXECUTION_FLAG] = flag; store(path, doc)
    monkeypatch.setattr(original.importlib, 'import_module', lambda *_: pytest.fail('import before validation'))
    with pytest.raises(original.OperatorConfigHold, match='^operator_config_rejected$'):
        loader.load_joint_api_runtime(path)


@pytest.mark.parametrize('fault', ['missing', 'extra', 'read-version', 'joint-disabled', 'cycle-disabled', 'policy-flag'])
def test_execution_version_is_closed(execution_config, monkeypatch, fault):
    path, doc = execution_config
    if fault == 'missing': del doc[loader.EXECUTION_FLAG]
    elif fault == 'extra': doc['worker'] = {}
    elif fault == 'read-version': doc['config_version'] = loader.VERSION
    elif fault == 'joint-disabled': doc['policy'][loader.FLAG] = False
    elif fault == 'cycle-disabled': doc['policy']['crop_cycle_result_storage'] = False
    elif fault == 'policy-flag': doc['policy'][loader.EXECUTION_FLAG] = True
    store(path, doc)
    monkeypatch.setattr(original.importlib, 'import_module', lambda *_: pytest.fail('import before validation'))
    with pytest.raises(original.OperatorConfigHold, match='^operator_config_rejected$'):
        loader.load_joint_api_runtime(path)


@pytest.mark.parametrize('load', [original.load_api_runtime, calculation.load_calculation_api_runtime])
def test_old_loaders_reject_execution_version(execution_config, load):
    with pytest.raises(original.OperatorConfigHold, match='^operator_config_rejected$'): load(execution_config[0])


def test_reader_version_and_direct_runtime_default_remain_disabled(joint_config, monkeypatch):
    calls = isolated_assembly(monkeypatch); loader.load_joint_api_runtime(joint_config[0])
    assert calls[0].crop_climate_joint_execution is False and config().crop_climate_joint_execution is False
    with pytest.raises(ValueError, match='^API runtime configuration rejected$'):
        config(crop_climate_joint_execution=True)
    for value in (None, 0, 1, 'true'):
        with pytest.raises(ValueError, match='^API runtime configuration rejected$'):
            config(crop_climate_joint_execution=value)


@pytest.mark.parametrize('field', ['config', 'dsn_file', 'thermal_gate_key_file', 'market_hold_key_file',
    'certificate', 'private_key', 'permissions'])
@pytest.mark.parametrize('phase', ['factory', 'assembly'])
def test_execution_files_rechecked_after_each_trusted_boundary(execution_config, monkeypatch, field, phase):
    reader.test_protected_files_are_rechecked_after_factory_and_assembly(execution_config, monkeypatch, phase, field)


@pytest.fixture
def native(setup, execution_config, tls_files, database_cleanup, tmp_path, monkeypatch):
    from app.crop_climate_joint_farm_binding import JointFarmBinding
    from app.crop_cycle_farm_binding import CycleFarmBinding
    from app.crop_cycle_server_custody import CycleServerCustody
    from app.crop_cycle_result_store import CycleCropResultStore
    from app.market_source_store import MarketSourceStore
    from test_crop_cycle_artifact import PROFILES, NOTICE
    from test_crop_cycle_farm_binding import SyntheticInputRights
    server, raw, value = setup; value[4]['scopes'].update(SCOPES)
    jobs = server.binding.jobs; farms = server.binding.farms; research = farms.replay.owned_research
    result_store = execution.results.JointCropClimateResultStore(server, integrity_key=reader.registered.KEY)
    admission = execution.checkpoints.execution.JointCropClimateExecutionService(server.binding, input_resolver=server.input_resolver)
    checkpoints = execution.checkpoints.JointExecutionCheckpointStore(admission, server)
    worker = execution.JointExecutionWorker(checkpoints, result_store, tenant_id='tenant-1')
    legacy_root = tmp_path/'legacy-server'; legacy_root.mkdir(mode=0o700)
    class UnusedResolver:
        version = 'owned-joint-execution-unused-legacy-v1'
        def __call__(self, *a): pytest.fail('legacy inputs resolved')
    def legacy_factory(*, farm_authoring_service):
        bound = CycleFarmBinding(farm_authoring_service, **PROFILES, notice_raw=NOTICE, input_rights=SyntheticInputRights())
        custody = CycleServerCustody(bound, legacy_root, input_resolver=UnusedResolver(), integrity_key=b'owned-unused-custody-'+b's'*32)
        return CycleCropResultStore(custody, integrity_key=b'owned-unused-registry-'+b'd'*32)
    def joint_factory(*, farm_authoring_service):
        bound = JointFarmBinding(farm_authoring_service, server.binding.input_authority, input_rights=value[-1])
        custody = reader.registered.producer.model.JointServerCustody(bound, server.directory,
            input_resolver=server.input_resolver, integrity_key=server.integrity_key)
        return execution.results.JointCropClimateResultStore(custody, integrity_key=result_store.integrity_key)
    def source_factory(*, principal_provider):
        return MarketSourceStore(jobs._dsn, jobs.schema, principal_provider=principal_provider, runtime_identity=jobs.runtime_identity)
    grant = http_identity.BearerGrant(http_identity.token_digest(TOKEN), 'tenant-1', SCOPES,
        NOW-timedelta(seconds=1), NOW+timedelta(hours=1))
    cert, key, _ = tls_files; descriptor = jobs._content_directory(create=True); os.close(descriptor)
    cfg = config(policy=jobs.runtime_identity[0], dsn=jobs._dsn, artifact_root=jobs.artifact_root,
        certificate=cert, private_key=key, port=0, crop_climate_joint_execution=True)
    deps = dependencies(research_registry=research.catalog, owned_fixture_registry=research.registry,
        owned_research_contexts=dict(research._contexts), market_scope_resolver=farms.replay.thermal.holds._scope_resolver,
        market_source_factory=source_factory, bearer_registry=http_identity.BearerRegistry((grant,), clock=lambda:NOW),
        crop_cycle_result_store_factory=legacy_factory, crop_climate_joint_result_store_factory=joint_factory,
        crop_climate_joint_current_query_factory=lambda *, result_store: current.JointCropClimateCurrentQuery(result_store))
    path, doc = execution_config
    doc.update(policy=asdict(cfg.policy), artifact_root=str(cfg.artifact_root), certificate=str(cert), private_key=str(key), port=0)
    for field, data in (('dsn_file',cfg.dsn.encode()), ('thermal_gate_key_file',cfg.thermal_gate_key), ('market_hold_key_file',cfg.market_hold_key)):
        Path(doc[field]).write_bytes(data)
    store(path, doc)
    def factory(*, config):
        assert config == cfg; return deps
    monkeypatch.setitem(sys.modules, 'trusted_operator', SimpleNamespace(dependencies=factory))
    files = {p:sha256(p.read_bytes()).hexdigest() for p in
        (path, cert, key, *(Path(doc[f]) for f in ('dsn_file','thermal_gate_key_file','market_hold_key_file')), *value[2][0].iterdir())}
    initial = fd_inventory()
    with monkeypatch.context() as patch:
        calls = progress.forbid(patch)
        runtime = loader.load_joint_api_runtime(path)
        assert not any(calls.values())
    assert fd_inventory() == initial
    yield SimpleNamespace(runtime=runtime, worker=worker, raw=raw, value=value, config=cfg, deps=deps, path=path, files=files)
    assert {p:sha256(p.read_bytes()).hexdigest() for p in files} == files
    assert not list(legacy_root.iterdir()) and http_identity.current_principal() is None


@contextmanager
def served(runtime, certificate):
    server = runtime.service.server(); inventory = fd_inventory()
    thread = threading.Thread(target=server.run, daemon=True); thread.start(); replies=[]; deadline=time.monotonic()+10
    try:
        while not server.started:
            assert thread.is_alive() and time.monotonic()<deadline; time.sleep(.01)
        port=server.servers[0].sockets[0].getsockname()[1]
        context=ssl.create_default_context(cafile=str(certificate))
        def send(method, path, body=None):
            connection=http.client.HTTPSConnection('127.0.0.1',port,context=context,timeout=60); started=time.monotonic()
            try:
                headers={'Authorization':'Bearer '+TOKEN.decode()}
                if body is not None: headers['Content-Type']='application/json'
                connection.request(method,path,body=body,headers=headers); response=connection.getresponse(); raw=response.read()
                assert response.getheader('Cache-Control')=='no-store'
                replies.append({'status':response.status,'bytes':len(raw),'sha256':sha256(raw).hexdigest(),'seconds':time.monotonic()-started})
                return response.status, raw
            finally: connection.close()
        yield send, replies
    finally:
        server.should_exit=True; thread.join(15); assert not thread.is_alive()
        assert fd_inventory()==inventory


@LOGIN
@pytest.mark.parametrize('setup,expected_status', [(None, 'completed'), ('hold', 'hold')], indirect=['setup'])
def test_native_runtime_http_job_is_automatically_consumed(native, tmp_path, monkeypatch, expected_status):
    c=native; rt=c.runtime
    assert rt.joint_execution_admission.binding is rt.joint_crop_results.server.binding
    assert rt.joint_execution_checkpoints.server is rt.joint_crop_results.server
    assert rt.joint_execution_query.results is rt.joint_crop_results
    assert rt.joint_execution_query.checkpoints is rt.joint_execution_checkpoints
    assert rt.joint_execution_admission.jobs is rt.jobs and rt.jobs.principal_provider is http_identity.current_principal
    captured=[]; original_read=rt.joint_execution_query.read
    def read(*a): raw=original_read(*a); captured.append(raw); return raw
    monkeypatch.setattr(rt.joint_execution_query,'read',read)
    pack, factory=consumer.joint_factory(c.worker,c.value,tmp_path)
    block=tmp_path/'block'; block.touch(mode=0o600)
    try:
        with served(rt,c.config.certificate) as (send,replies):
            status,raw=send('POST',POST,c.raw); assert status==202; job=json.loads(raw)['job_id']
            assert job not in pack.read_text()+factory.read_text()
            path='/v1/jobs/'+job+'/crop-climate-joint-execution'
            with monkeypatch.context() as patch:
                calls=progress.forbid(patch); status,raw=send('GET',path)
                assert status==200 and raw==captured[-1] and json.loads(raw)['checkpoint_status']=='none' and not any(calls.values())
            with consumer.legacy.process_consumer(tmp_path,'joint_operator:build') as (process,events,errors):
                consumer.legacy.wait_for(lambda:(tmp_path/'claimed').exists(),process,timeout=20)
                status,raw=send('GET',path); assert status==200 and json.loads(raw)['job']['state']=='simulating'
                process.send_signal(signal.SIGTERM)
                consumer.legacy.wait_for(lambda:(tmp_path/'stop-observed').exists(),process,timeout=5)
                block.unlink(); process.wait(timeout=150)
            assert process.returncode==0 and errors==['']
            proof=consumer.attempt_proof(tmp_path,1); assert proof['calls']['step']==16
            with monkeypatch.context() as patch:
                calls=progress.forbid(patch); status,raw=send('GET',path)
                assert status==200 and raw==captured[-1] and not any(calls.values())
                value=json.loads(raw); selected=value['result']; assert selected is not None
                assert selected['status']==expected_status and value['job']['state']==('succeeded' if selected['status']=='completed' else 'hold')
                farm=json.loads(c.raw)['farm']
                expected=current.JointCropClimateCurrentQuery(c.worker.results).read('tenant-1',selected['result_id'],farm,view='summary')
                status,stored=send('GET',reader.PATH+selected['result_id']+'?'+urlencode(farm))
                assert status==200 and stored==expected and json.loads(stored)['summary']['status']==selected['status'] and not any(calls.values())
            with c.worker.jobs.connect() as conn:
                assert conn.pgconn.used_password and conn.info.get_parameters()['require_auth']=='scram-sha-256'
            assert [e['event'] for e in events]==['started','attempt','stopped'] and events[1]['job_id']==job
        save('automatic-'+selected['status'],{'actual_scram':True,'verified_TLS':True,'automatic_independent_consumer':True,
            'same_job_and_original_progress_bytes':True,'process_exit':process.returncode,'events':events,'attempt':proof,'read_calls':calls,'replies':replies})
    finally:
        pack.unlink(); (tmp_path/'proof.private.json').unlink()


@LOGIN
def test_native_runtime_running_cancel_is_acknowledged_by_consumer(native, tmp_path):
    c=native; pack,factory=consumer.joint_factory(c.worker,c.value,tmp_path)
    block=tmp_path/'block'; block.touch(mode=0o600)
    try:
        with served(c.runtime,c.config.certificate) as (send,replies):
            status,raw=send('POST',POST,c.raw); assert status==202; job=json.loads(raw)['job_id']
            path='/v1/jobs/'+job+'/crop-climate-joint-execution'
            with consumer.legacy.process_consumer(tmp_path,'joint_operator:build') as (process,events,errors):
                consumer.legacy.wait_for(lambda:(tmp_path/'claimed').exists(),process,timeout=20)
                status,raw=send('POST',path+'/cancel'); value=json.loads(raw)
                assert status==200 and value['cancel_requested'] and value['job']['state']=='simulating'
                process.send_signal(signal.SIGTERM)
                consumer.legacy.wait_for(lambda:(tmp_path/'stop-observed').exists(),process,timeout=5)
                block.unlink(); process.wait(timeout=45)
            assert process.returncode==0 and errors==['']
            proof=consumer.attempt_proof(tmp_path,1); assert proof['state']=='canceled' and not any(proof['calls'].values())
            status,raw=send('GET',path); value=json.loads(raw)
            assert status==200 and value['job']['state']=='canceled' and value['result'] is None and value['checkpoint'] is None
            consumer.reference.no_published_result(c.worker,job)
        save('running-cancel',{'actual_scram':True,'verified_TLS':True,'worker_acknowledged':True,
            'process_exit':process.returncode,'events':events,'attempt':proof,'replies':replies})
    finally:
        pack.unlink(); (tmp_path/'proof.private.json').unlink()


@LOGIN
def test_native_disabled_runtime_leaves_execution_unavailable(native):
    runtime=ApiRuntime(replace(native.config,crop_climate_joint_execution=False),native.deps)
    assert runtime.joint_execution_admission is runtime.joint_execution_checkpoints is runtime.joint_execution_query is None
    with served(runtime,native.config.certificate) as (send,replies):
        assert send('POST',POST,native.raw)[0]==503
        job='11111111-1111-4111-8111-111111111111'; path='/v1/jobs/'+job+'/crop-climate-joint-execution'
        assert send('GET',path)[0]==503 and send('POST',path+'/cancel')[0]==503
    assert not list(native.worker.server.directory.iterdir())
    save('disabled',{'no_execution_objects':True,'actual_scram':True,'verified_TLS':True,'replies':replies})
