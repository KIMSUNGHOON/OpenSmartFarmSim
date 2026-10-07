"""Explicit calculation runtime selection; actual HTTP transport is separate."""
from dataclasses import replace
import json
import os
from pathlib import Path
import subprocess
import sys
from hashlib import sha256
from time import perf_counter

import psycopg
from psycopg import sql

import pytest

from app import api_runtime as runtime
from test_api_runtime import config,dependencies,policy
from test_api_serve import tls_files
from test_crop_cycle_calculation_result_store_farms import login_scope,original_login_scope
from test_farm_authoring_storage import authoring
from test_farm_replay_scenario import farm_setup
from login_database import login_database


def test_calculation_flag_without_factories_is_denied_before_connections(monkeypatch):
    calls=[]
    monkeypatch.setattr(runtime,'JobStore',lambda *a,**kw:calls.append('connection'))
    with pytest.raises(ValueError,match='^API runtime assembly rejected$'):
        runtime.ApiRuntime(config(policy=replace(policy(),crop_cycle_calculation_result_storage=True)),dependencies())
    assert calls==[]


@pytest.mark.parametrize('enabled,old_enabled,store,query',[
    (True,True,False,False),(True,True,True,False),(True,True,False,True),
    (False,False,True,False),(False,False,False,True),(False,False,True,True),(True,False,True,True)])
def test_calculation_factory_and_flag_mixing_is_denied_before_calls(monkeypatch,enabled,old_enabled,store,query):
    calls=[]
    def factory(**kwargs):calls.append('factory')
    monkeypatch.setattr(runtime,'JobStore',lambda *a,**kw:calls.append('connection'))
    selected=replace(policy(),crop_cycle_result_storage=old_enabled,crop_cycle_calculation_result_storage=enabled)
    deps=dependencies(crop_cycle_result_store_factory=factory if old_enabled else None,
        crop_cycle_calculation_result_store_factory=factory if store else None,
        crop_cycle_calculation_current_query_factory=factory if query else None)
    with pytest.raises(ValueError,match='^API runtime assembly rejected$'):runtime.ApiRuntime(config(policy=selected),deps)
    assert calls==[]


@pytest.mark.parametrize('name',['crop_cycle_calculation_result_store_factory','crop_cycle_calculation_current_query_factory'])
@pytest.mark.parametrize('value',[True,0,'private factory path'])
def test_calculation_noncallable_factories_are_closed(name,value):
    with pytest.raises(ValueError,match='^API runtime dependencies rejected$'):dependencies(**{name:value})


def test_calculation_factories_are_optional_and_hidden():
    deps=dependencies();factory=lambda **kwargs:None
    for name in ('crop_cycle_calculation_result_store_factory','crop_cycle_calculation_current_query_factory'):
        assert getattr(deps,name) is None
        selected=replace(deps,**{name:factory});assert getattr(selected,name) is factory and name not in repr(selected)
    assert policy().crop_cycle_calculation_result_storage is False


def save_reference(name,value):
    root=os.environ.get('OSSF_CALCULATION_FACTORY_EVIDENCE')
    if root:
        with (Path(root)/name).open('x') as f:
            os.fchmod(f.fileno(),0o400);json.dump(value,f,sort_keys=True,indent=2);f.write('\n')
            f.flush();os.fsync(f.fileno())


@pytest.mark.parametrize('first',['app.api_runtime','app.operator_config','app.api_crop_cycle_calculation_replay'])
def test_runtime_fresh_import_orders_preserve_lazy_calculation_loading(first):
    code='''import importlib,json,os,sys
before=len(os.listdir('/proc/self/fd'))
for name in [sys.argv[1],'app.api_runtime','app.operator_config','app.api_crop_cycle_calculation_replay']:importlib.import_module(name)
forbidden=['app.crop_cycle_calculation_context','app.crop_cycle_calculation_result_store','app.crop_cycle_calculation_current_query']
assert all(name not in sys.modules for name in forbidden)
assert before==len(os.listdir('/proc/self/fd'))
print(json.dumps({'first':sys.argv[1],'fd_before':before,'fd_after':len(os.listdir('/proc/self/fd')),'new_calculation_store_query_modules_loaded':False}))
'''
    child=subprocess.run([sys.executable,'-c',code,first],text=True,capture_output=True,timeout=30)
    assert child.returncode==0 and child.stderr==''
    save_reference('import-'+first.rsplit('.',1)[-1]+'.json',{'exit_code':child.returncode,**json.loads(child.stdout)})


@pytest.fixture(scope='module')
def audit_database(login_database,tmp_path_factory):
    yield
    with psycopg.connect(login_database['admin']) as conn:
        schemas=conn.execute("SELECT count(*) FROM pg_namespace WHERE nspname ~ '^login_test_'").fetchone()[0]
        roles=conn.execute("SELECT count(*) FROM pg_roles WHERE rolname ~ '^login_(owner_|[0-9a-f]{32}_)'").fetchone()[0]
        directory=Path(conn.execute('SHOW data_directory').fetchone()[0])
    passfiles=list(tmp_path_factory.getbasetemp().rglob('*.pgpass'))
    assert schemas==roles==len(passfiles)==0
    methods=[line.split()[-1] for line in (directory/'pg_hba.conf').read_text().splitlines()
        if line.strip().startswith('host')]
    assert methods and set(methods)=={'scram-sha-256'}
    save_reference('database-cleanup.json',{'schemas_after':schemas,'roles_after':roles,
        'passfiles_after':len(passfiles),'actual_host_auth_methods':methods})


@pytest.mark.parametrize('original_login_scope',[{'market_calculation':True,'market_source_storage':True,
    'thermal_scenario_storage':True,'break_even_calculation':True,'crop_cycle_result_storage':True}],indirect=True)
def test_actual_scram_calculation_factories_same_farm_reconstruction_mixing_and_no_computation(
        authoring,tls_files,tmp_path,monkeypatch,audit_database):
    from app import crop_cycle_calculation_context as engine
    from app import crop_cycle_calculation_result_store as storage
    from app import crop_cycle_calculation_current_query as query
    from app import crop_cycle_result_store as old_store
    from app import crop_cycle_server_custody as old_server
    from app.crop_cycle_calculation_farm_binding import CalculationFarmBinding
    from app.crop_cycle_farm_binding import CycleFarmBinding
    from app.crop_cycle_calculation_result_evidence import CalculationResultEvidenceAuthority
    from app.farm_authoring_storage import FarmAuthoringService
    from app.http_identity import current_principal
    from app.market_source_store import MarketSourceStore
    from test_crop_cycle_artifact import program,PROFILES,NOTICE
    from test_crop_cycle_farm_binding import SyntheticInputRights
    from test_crop_cycle_input_evidence import authority
    farms,_,_=authoring;jobs=farms.replay.jobs;research=farms.replay.owned_research
    issuer=authority();rights=SyntheticInputRights();root=tmp_path/'inputs'
    p=program('empty-entry');anchors=p.pop('output_times')
    receipt=engine.inputs.write_input_packet(root,**p,anchors=anchors,outputs=anchors,**PROFILES,program_id='owned-runtime-input')
    for path in root.iterdir():path.chmod(0o400)
    input_proof=issuer.issue(root,receipt['root_sha256'])
    new_root=tmp_path/'calculation-server';old_root=tmp_path/'legacy-server'
    new_root.mkdir(mode=0o700);old_root.mkdir(mode=0o700)
    server_key=b'owned-runtime-server-'+b's'*32;db_key=b'owned-runtime-db-'+b'd'*32
    result_key=b'owned-runtime-result-'+b'r'*32
    class Resolver:
        version='owned-runtime-unused-resolver-v1'
        def __call__(self,*args,**kwargs):pytest.fail('assembly resolved crop inputs/results')
    def make_store(selected_farms):
        bound=CalculationFarmBinding(selected_farms,issuer,input_rights=rights)
        server=storage.server.CalculationServerCustody(bound,new_root,input_resolver=Resolver(),integrity_key=server_key)
        return storage.CalculationCycleCropResultStore(server,integrity_key=db_key)
    def crop_factory(*,farm_authoring_service):return make_store(farm_authoring_service)
    def make_query(store,key=result_key):
        result_authority=CalculationResultEvidenceAuthority(issuer,integrity_key=key,
            issuer_id='owned-runtime-result-authority',key_id='result-v1')
        return query.CalculationCurrentCycleQuery(store,result_authority,evidence_resolver=Resolver())
    def query_factory(*,result_store):return make_query(result_store)
    def legacy_factory(*,farm_authoring_service):
        bound=CycleFarmBinding(farm_authoring_service,**PROFILES,notice_raw=NOTICE,input_rights=rights)
        server=old_server.CycleServerCustody(bound,old_root,input_resolver=Resolver(),integrity_key=server_key)
        return old_store.CycleCropResultStore(server,integrity_key=db_key)
    def source_factory(*,principal_provider):
        return MarketSourceStore(jobs._dsn,jobs.schema,principal_provider=principal_provider,runtime_identity=jobs.runtime_identity)
    def counts():
        with jobs.connect() as conn:
            return {name:conn.execute(sql.SQL('SELECT count(*) AS n FROM {}').format(jobs._table(name))).fetchone()['n']
                for name in ('jobs','job_events','crop_cycle_research_results','crop_cycle_verified_research_results')}
    def inputs_state():
        return {p.name:(sha256(p.read_bytes()).hexdigest(),p.stat().st_mode,p.stat().st_ino) for p in root.iterdir()}
    descriptor=jobs._content_directory(create=True);os.close(descriptor)
    before=counts();original_inputs=inputs_state();fd_before=len(os.listdir('/proc/self/fd'))
    cert,key,_=tls_files
    cfg=config(policy=jobs.runtime_identity[0],dsn=jobs._dsn,artifact_root=jobs.artifact_root,certificate=cert,private_key=key,port=0)
    deps=dependencies(research_registry=research.catalog,owned_fixture_registry=research.registry,
        owned_research_contexts=dict(research._contexts),market_scope_resolver=farms.replay.thermal.holds._scope_resolver,
        market_source_factory=source_factory,crop_cycle_result_store_factory=legacy_factory,
        crop_cycle_calculation_result_store_factory=crop_factory,crop_cycle_calculation_current_query_factory=query_factory)
    def forbidden(*args,**kwargs):pytest.fail('runtime assembly parsed/calculated/published crop output')
    for module,name in ((engine.inputs,'open_input_packet'),(engine.legacy,'prepare_context'),
            (engine,'open_calculation_context'),(engine,'advance_chunk'),(engine.short._Evaluator,'rhs'),
            (engine.evidence.InputEvidenceAuthority,'issue'),(CalculationResultEvidenceAuthority,'issue'),
            (storage.artifact,'open_artifact'),(storage.artifact,'_validate_delta'),
            (storage.server.CalculationServerCustody,'advance'),(storage.CalculationCycleCropResultStore,'put'),
            (old_server.CycleServerCustody,'advance'),(old_store.CycleCropResultStore,'put')):
        monkeypatch.setattr(module,name,forbidden)
    create_app=runtime.create_app;forwarded=[]
    def capture_app(*args,**kwargs):
        forwarded.append(kwargs);return create_app(*args,**kwargs)
    monkeypatch.setattr(runtime,'create_app',capture_app)
    started=perf_counter();selected=runtime.ApiRuntime(cfg,deps);normal_seconds=perf_counter()-started
    current=selected.calculation_cycle_crop_results
    assert forwarded[-1].get('crop_cycle_calculation_result_store') is current
    assert forwarded[-1].get('crop_cycle_calculation_current_query') is selected.calculation_cycle_crop_query
    assert current.jobs is selected.jobs and current.server.binding.jobs is selected.jobs
    assert current.server.binding.farms is selected.farm_authoring
    assert selected.jobs.principal_provider is current_principal and selected.calculation_cycle_crop_query.store is current
    assert len({current.integrity_key,current.server.integrity_key,issuer.integrity_key,
        selected.calculation_cycle_crop_query.authority.integrity_key})==4
    with selected.jobs.connect() as conn:
        assert conn.pgconn.used_password and conn.info.get_parameters()['require_auth']=='scram-sha-256'
    rebuilt=runtime.ApiRuntime(cfg,deps)
    assert rebuilt.calculation_cycle_crop_results is not current and rebuilt.calculation_cycle_crop_results.jobs is rebuilt.jobs
    assert rebuilt.calculation_cycle_crop_query.store is rebuilt.calculation_cycle_crop_results
    def other_farm(*,farm_authoring_service):return make_store(FarmAuthoringService(farm_authoring_service.replay))
    def changed_store(*,farm_authoring_service):
        value=make_store(farm_authoring_service);value.integrity_key+=b'-changed';return value
    def changed_query(*,result_store):
        value=make_query(result_store);value.evidence_resolver.version='changed-resolver-v1';return value
    cases=[('legacy-store',lambda **_:selected.cycle_crop_results,query_factory),
        ('untyped-store',lambda **_:object(),query_factory),('foreign-jobs',lambda **_:make_store(farms),query_factory),
        ('other-farm',other_farm,query_factory),('store-binding',changed_store,query_factory),
        ('untyped-query',crop_factory,lambda **_:object()),
        ('other-store-query',crop_factory,lambda *,result_store:make_query(storage.CalculationCycleCropResultStore(result_store.server,integrity_key=db_key))),
        ('query-binding',crop_factory,changed_query),('reused-evidence-key',crop_factory,lambda *,result_store:make_query(result_store,db_key))]
    denied=[]
    for name,store_factory,current_query_factory in cases:
        with pytest.raises(ValueError,match='^API runtime assembly rejected$'):
            runtime.ApiRuntime(cfg,replace(deps,crop_cycle_calculation_result_store_factory=store_factory,
                crop_cycle_calculation_current_query_factory=current_query_factory))
        denied.append(name)
        assert len(os.listdir('/proc/self/fd'))==fd_before and counts()==before
    assert inputs_state()==original_inputs and not list(new_root.iterdir()) and not list(old_root.iterdir())
    assert before['crop_cycle_research_results']==before['crop_cycle_verified_research_results']==0
    save_reference('scram-assembly.json',{'actual_scram':True,'normal_assembly_seconds':normal_seconds,
        'same_jobs_farm_current_principal':True,'four_independent_keys':True,'reconstructed_same_bindings':True,
        'denied_actual_cases':denied,'counts_before':before,'counts_after':counts(),
        'parser_context_QC_RHS_advance_publication_forbidden':True,'inputs_unchanged':True,
        'input_proof_sha256':sha256(input_proof).hexdigest(),'fd_before':fd_before,'fd_after':len(os.listdir('/proc/self/fd'))})
