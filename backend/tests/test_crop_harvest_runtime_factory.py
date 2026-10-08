"""Private reader configuration and owned separate-process runtime restoration."""
from copy import deepcopy
from dataclasses import asdict
from hashlib import sha256
import json
import os
from pathlib import Path
import subprocess
import sys
from time import perf_counter
from types import SimpleNamespace

from psycopg.conninfo import make_conninfo
import pytest

from app import crop_harvest_runtime_factory as factory
from test_crop_harvest import save_native
from test_crop_harvest_runtime import (authoring, harvest_scope, login_scope, original_login_scope,
    farm_setup, tls_files, login_database, audit_database)


def private_write(path, raw):
    with path.open('xb') as f:
        os.fchmod(f.fileno(),0o600); f.write(raw); f.flush(); os.fsync(f.fileno())
    return path


def json_raw(value):
    return (json.dumps(value,sort_keys=True,indent=2,ensure_ascii=False,allow_nan=False)+'\n').encode()


@pytest.fixture
def private_case(tmp_path):
    directory=tmp_path/'operator'; directory.mkdir(mode=0o700)
    root=tmp_path/'harvest'; root.mkdir(mode=0o700)
    policy={'schema':'owned_scope','owner':'owned_owner','publisher':'owned_pub','reader':'owned_read','database':'owned_database'}
    passfile=private_write(directory/'reader.pgpass',b'127.0.0.1:5432:owned_database:owned_read:owned-test-only\n')
    dsn=make_conninfo(host='127.0.0.1',port=5432,dbname=policy['database'],user=policy['reader'],passfile=str(passfile))
    dsn_path=private_write(directory/'reader.dsn',dsn.encode())
    key=private_write(directory/'harvest.key',b'owned-private-harvest-key-'+b'h'*32)
    value={'config_version':factory.VERSION,'policy':policy,'directory':str(root),
        'reader_dsn_file':str(dsn_path),'integrity_key_file':str(key)}
    path=private_write(directory/'reader.json',json_raw(value))
    try:
        yield SimpleNamespace(path=path,value=value,root=root,directory=directory,dsn_path=dsn_path,key=key,passfile=passfile)
    finally:
        passfile.unlink(missing_ok=True)


def reject(case):
    with pytest.raises(factory.HarvestRuntimeConfigHold,match='^harvest_reader_config_rejected$'):
        factory.load_harvest_current_query_factory(case.path)


def test_loader_has_no_connection_and_factory_is_explicit_hidden_and_keyword_only(private_case,monkeypatch):
    import psycopg
    calls=[]
    monkeypatch.setattr(psycopg,'connect',lambda *a,**k:calls.append(True))
    fd=len(os.listdir('/proc/self/fd')); value=factory.load_harvest_current_query_factory(private_case.path)
    assert value.version==factory.VERSION and value.config_sha256==sha256(private_case.path.read_bytes()).hexdigest()
    assert not calls and len(os.listdir('/proc/self/fd'))==fd
    assert 'owned-private-harvest-key' not in repr(value) and 'reader.dsn' not in repr(value)
    with pytest.raises(TypeError):value(object())
    with pytest.raises(factory.HarvestRuntimeConfigHold,match='^harvest_reader_config_rejected$'):
        value(calculation_current_query=object())
    assert not calls and len(os.listdir('/proc/self/fd'))==fd


@pytest.mark.parametrize('fault',['unknown','missing','version','policy-extra','policy-missing','policy-role',
    'relative-root','relative-dsn','relative-key','traversal','short-key','long-key','empty-dsn',
    'publisher-dsn','database-dsn','socket-dsn','inline-password','missing-passfile','aliased-files'])
def test_closed_config_and_private_inputs_refuse(private_case,fault):
    c=private_case; value=deepcopy(c.value)
    if fault=='unknown':value['private-marker']='owned'
    elif fault=='missing':value.pop('directory')
    elif fault=='version':value['config_version']='legacy'
    elif fault=='policy-extra':value['policy']['extra']='owned'
    elif fault=='policy-missing':value['policy'].pop('reader')
    elif fault=='policy-role':value['policy']['reader']=value['policy']['publisher']
    elif fault.startswith('relative-'):
        value[{'relative-root':'directory','relative-dsn':'reader_dsn_file','relative-key':'integrity_key_file'}[fault]]='relative'
    elif fault=='traversal':value['directory']=str(c.root/'..'/'harvest')
    elif fault=='short-key':c.key.write_bytes(b'short')
    elif fault=='long-key':c.key.write_bytes(b'x'*4097)
    elif fault=='empty-dsn':c.dsn_path.write_bytes(b'')
    elif fault=='aliased-files':value['integrity_key_file']=str(c.dsn_path)
    else:
        changes={'publisher-dsn':{'user':value['policy']['publisher']},'database-dsn':{'dbname':'foreign'},
            'socket-dsn':{'host':'/owned/socket'},'inline-password':{'password':'owned-test-only'},
            'missing-passfile':{'passfile':''}}[fault]
        c.dsn_path.write_text(make_conninfo(c.dsn_path.read_text(),**changes))
    c.path.write_bytes(json_raw(value)); reject(c)


@pytest.mark.parametrize('raw',[b'{"config_version":1,"config_version":2}',b'{}',b'[]',b'{',b'NaN',b'x'*65537])
def test_malformed_duplicate_or_oversize_config_refuses(private_case,raw):
    private_case.path.write_bytes(raw); reject(private_case)


@pytest.mark.parametrize('fault',['config-mode','key-mode','dsn-mode','passfile-mode','parent-mode','root-mode',
    'symlink','hardlink','acl-probe'])
def test_unsafe_files_and_directory_refuse_and_close(private_case,monkeypatch,fault):
    c=private_case;fd=len(os.listdir('/proc/self/fd'))
    if fault.endswith('-mode'):
        target={'config-mode':c.path,'key-mode':c.key,'dsn-mode':c.dsn_path,'passfile-mode':c.passfile,
            'parent-mode':c.directory,'root-mode':c.root}[fault]
        target.chmod(0o755 if fault in ('parent-mode','root-mode') else 0o644)
    elif fault=='symlink':
        target=c.path.with_suffix('.saved');c.path.rename(target);c.path.symlink_to(target)
    elif fault=='hardlink':os.link(c.path,c.path.with_suffix('.linked'))
    else:
        def denied(_):raise ValueError('owned ACL probe')
        monkeypatch.setattr(factory.private,'_no_acl',denied)
    reject(c);assert len(os.listdir('/proc/self/fd'))==fd


@pytest.mark.parametrize('fault',['config','dsn','key','passfile','root','code','fields'])
def test_captured_configuration_and_root_are_rechecked_before_construction(private_case,monkeypatch,fault):
    c=private_case; make=factory.load_harvest_current_query_factory(c.path)
    if fault in ('config','dsn','key','passfile'):
        target={'config':c.path,'dsn':c.dsn_path,'key':c.key,'passfile':c.passfile}[fault]
        target.write_bytes(target.read_bytes()+b' ')
    elif fault=='root':c.root.rename(c.root.with_name('original-root'));c.root.mkdir(mode=0o700)
    elif fault=='code':monkeypatch.setattr(factory,'CODE_SHA256','0'*64)
    else:monkeypatch.setattr(factory,'FIELDS',factory.FIELDS|{'unknown'})
    with pytest.raises(factory.HarvestRuntimeConfigHold,match='^harvest_reader_config_rejected$'):
        make(calculation_current_query=object())


def test_configuration_change_during_construction_refuses_prepared_reader(private_case,monkeypatch):
    from app import crop_harvest_current_query as current
    c=private_case; make=factory.load_harvest_current_query_factory(c.path); trace=[]; parent=object()
    def registry(query,*args,**kwargs):
        assert query is parent;trace.append('registry');c.key.write_bytes(c.key.read_bytes()+b'changed');return object()
    monkeypatch.setattr(current.registry,'HarvestRegistry',registry)
    monkeypatch.setattr(current,'HarvestCurrentQuery',lambda store:trace.append('query') or object())
    with pytest.raises(factory.HarvestRuntimeConfigHold,match='^harvest_reader_config_rejected$'):
        make(calculation_current_query=parent)
    assert trace==['registry','query']


def test_fresh_import_has_no_connection_or_descriptor_side_effect():
    code='''import json,os,psycopg,socket,sys
calls=[]
def denied(*a,**k):calls.append(True);raise AssertionError('connection during import')
psycopg.connect=denied;socket.create_connection=denied
before=len(os.listdir('/proc/self/fd'))
import app.crop_harvest_runtime_factory
assert not calls and before==len(os.listdir('/proc/self/fd'))
assert 'app.crop_harvest_current_query' not in sys.modules
print(json.dumps({'connection_calls':0,'FD_before_after':[before,before],'harvest_query_loaded':False}))
'''
    child=subprocess.run([sys.executable,'-c',code],capture_output=True,text=True,timeout=30)
    assert child.returncode==0 and child.stderr==''
    save_native('harvest-protected-import.json',{'original_child_exit_code':child.returncode,**json.loads(child.stdout)})


def owned_dependencies(*, config):
    """Actual import target for a private owned test bundle; never a product default."""
    from app.api_runtime import ApiRuntimeDependencies
    from app import crop_cycle_calculation_result_store as storage
    from app import crop_cycle_calculation_current_query as current
    from app import crop_cycle_result_store as legacy
    from app.crop_cycle_calculation_farm_binding import CalculationFarmBinding
    from app.crop_cycle_farm_binding import CycleFarmBinding
    from app.crop_cycle_calculation_result_evidence import CalculationResultEvidenceAuthority
    from app.market_source_store import MarketSourceStore
    from app.owned_fixture_registry import OwnedFixtureRegistry
    from app.research_registry import ResearchRegistry
    from test_api_runtime import dependencies
    from test_crop_cycle_artifact import PROFILES, NOTICE
    from test_crop_cycle_farm_binding import SyntheticInputRights
    from test_crop_cycle_input_evidence import authority
    private=factory.private; path=private._path(os.environ['OSSF_OWNED_HARVEST_RESTORE_BUNDLE'])
    raw=private._private_bytes(path,maximum=65536);bundle=json.loads(raw)
    assert sha256(raw).hexdigest()==os.environ['OSSF_OWNED_HARVEST_RESTORE_SHA256']
    assert bundle['version']=='owned-harvest-protected-restore-v1' and bundle['scope']=='owned_synthetic_zero_crop_outputs'
    assert bundle['factory_module_sha256']==sha256(Path(__file__).read_bytes()).hexdigest()
    assert bundle['reader_factory_code_sha256']==factory.CODE_SHA256
    for file,digest in bundle['static_sha256'].items():
        assert sha256(private._private_bytes(file,maximum=65536)).hexdigest()==digest
    key=lambda name:private._private_bytes(bundle['keys'][name],minimum=32,maximum=4096)
    issuer=authority(key=key('input'),issuer='owned-protected-input',key_id='input-v1')
    rights=SyntheticInputRights()
    class UnusedResolver:
        version='owned-protected-unused-resolver-v1'
        def __call__(self,*_,**__):raise AssertionError('protected assembly resolved crop data')
    def crop_factory(*,farm_authoring_service):
        bound=CalculationFarmBinding(farm_authoring_service,issuer,input_rights=rights)
        server=storage.server.CalculationServerCustody(bound,Path(bundle['crop_root']),
            input_resolver=UnusedResolver(),integrity_key=key('server'))
        return storage.CalculationCycleCropResultStore(server,integrity_key=key('parent'))
    def query_factory(*,result_store):
        evidence=CalculationResultEvidenceAuthority(issuer,integrity_key=key('result'),
            issuer_id='owned-protected-result',key_id='result-v1')
        return current.CalculationCurrentCycleQuery(result_store,evidence,evidence_resolver=UnusedResolver())
    def legacy_factory(*,farm_authoring_service):
        bound=CycleFarmBinding(farm_authoring_service,**PROFILES,notice_raw=NOTICE,input_rights=rights)
        server=legacy.server.CycleServerCustody(bound,Path(bundle['legacy_root']),
            input_resolver=UnusedResolver(),integrity_key=key('server'))
        return legacy.CycleCropResultStore(server,integrity_key=key('parent'))
    def sources(*,principal_provider):
        return MarketSourceStore(config.dsn,config.policy.schema,principal_provider=principal_provider,
            runtime_identity=(config.policy,'authority'))
    catalog=ResearchRegistry(private._private_bytes(bundle['catalog_file'],maximum=65536),bundle['catalog_sha256'])
    contexts={next(iter(catalog._scopes)):bundle['owned_context_id']}
    selected=dependencies(research_registry=catalog,owned_fixture_registry=OwnedFixtureRegistry(Path(bundle['owned_fixture_root'])),
        owned_research_contexts=contexts,market_scope_resolver=lambda *_:json.loads(private._private_bytes(bundle['market_scope_file'],maximum=65536)),
        market_source_factory=sources,crop_cycle_result_store_factory=legacy_factory,
        crop_cycle_calculation_result_store_factory=crop_factory,crop_cycle_calculation_current_query_factory=query_factory,
        crop_harvest_current_query_factory=factory.load_harvest_current_query_factory(bundle['reader_config']))
    assert type(selected) is ApiRuntimeDependencies
    return selected


def runtime_counts(runtime):
    from psycopg import sql
    from app.crop_harvest_registry_schema import TABLE
    with runtime.jobs.connect() as conn:
        counts={name:conn.execute(sql.SQL('SELECT count(*) AS n FROM {}').format(runtime.jobs._table(name))).fetchone()['n']
            for name in ('jobs','job_events','crop_cycle_research_results','crop_cycle_verified_research_results')}
        endpoint=[conn.info.host,conn.info.port,conn.info.dbname]
    store=runtime.harvest_crop_results
    with store._connection() as conn:
        assert conn.pgconn.used_password and conn.info.get_parameters()['require_auth']=='scram-sha-256'
        assert endpoint==[conn.info.host,conn.info.port,conn.info.dbname]
        counts['harvest_rows']=conn.execute(sql.SQL('SELECT count(*) AS n FROM {}').format(
            sql.Identifier(store.policy.schema,TABLE))).fetchone()['n']
    return counts,sha256(json_raw(endpoint)).hexdigest()


def owned_child(path,expected,denied=False):
    from app import calculation_operator_config as loader
    from app import crop_harvest_current_query as current
    from app.http_identity import current_principal
    from test_crop_harvest_current_query import forbid_all_reads_math
    assert sha256(factory.private._private_bytes(path,maximum=65536)).hexdigest()==expected
    fd=len(os.listdir('/proc/self/fd'));before=os.getpid()
    with pytest.MonkeyPatch.context() as patch:
        forbid_all_reads_math(patch)
        def forbidden(*_,**__):raise AssertionError('protected restore parsed or calculated crop data')
        for module,name in ((current.current.inputs,'open_input_packet'),
                (current.current.storage.artifact,'open_artifact'),
                (current.current.server.CalculationServerCustody,'advance'),
                (current.current.storage.CalculationCycleCropResultStore,'put')):
            patch.setattr(module,name,forbidden)
        if denied:
            with pytest.raises(factory.private.OperatorConfigHold,match='^operator_config_rejected$'):
                loader.load_calculation_api_runtime(path)
            result={'denied':True,'error':'operator_config_rejected'}
        else:
            selected=loader.load_calculation_api_runtime(path);query=selected.harvest_crop_query
            assert query.store is selected.harvest_crop_results and query.store.query is selected.calculation_cycle_crop_query
            assert query.store.role==query.store.policy.reader and query.store.query.store.jobs is selected.jobs
            assert query.store.query.store.server.binding.farms is selected.farm_authoring
            assert selected.jobs.principal_provider is current_principal
            counts,endpoint=runtime_counts(selected)
            assert counts['crop_cycle_research_results']==counts['crop_cycle_verified_research_results']==counts['harvest_rows']==0
            result={'same_parent_jobs_farm_principal_reader':True,'counts':counts,'authenticated_endpoint_sha256':endpoint,
                'catalog_sha256':selected.research.catalog.sha256,'row_count':0,'RHS_generation_proof_registration_calls':0}
    assert len(os.listdir('/proc/self/fd'))==fd
    return {'pid':before,'FD_before_after':[fd,fd],'protected_config_sha256':expected,
        'reader_factory_code_sha256':factory.CODE_SHA256,'result':result,'gates':'not_assessed'}


@pytest.mark.parametrize('original_login_scope',[{'market_calculation':True,'market_source_storage':True,
    'thermal_scenario_storage':True,'break_even_calculation':True,'crop_cycle_result_storage':True}],indirect=True)
def test_actual_protected_operator_fresh_python_same_DB_and_private_denial(
        authoring,harvest_scope,tls_files,tmp_path,monkeypatch,audit_database,login_database):
    from psycopg import sql
    import psycopg
    from app import calculation_operator_config as loader
    from app.http_identity import current_principal
    from app.thermal_run_store import _canonical
    from test_api_runtime import config
    farms,request,_=authoring;jobs=farms.replay.jobs;research=farms.replay.owned_research
    scope,dsns,harvest_root=harvest_scope;directory=tmp_path/'protected';directory.mkdir(mode=0o700)
    files=[]
    def write(name,raw):
        p=private_write(directory/name,raw);files.append(p);return p
    keys={name:str(write(name+'.key',('owned-protected-'+name+'-').encode()+bytes([65+i])*32))
        for i,name in enumerate(('input','server','parent','result'))}
    harvest_key=write('harvest.key',b'owned-protected-harvest-'+b'h'*32)
    reader_dsn=write('reader.dsn',dsns[scope.reader].encode())
    reader_doc={'config_version':factory.VERSION,'policy':asdict(scope),'directory':str(harvest_root),
        'reader_dsn_file':str(reader_dsn),'integrity_key_file':str(harvest_key)}
    reader_config=write('reader.json',json_raw(reader_doc))
    registrations=[{'tenant_id':s.tenant_id,'point':{'latitude':s.point[0],'longitude':s.point[1]},
        'period_start_utc':s.period_start_utc,'period_end_utc':s.period_end_utc,'goal_id':s.goal_id,
        'provider_ids':list(s.provider_ids)} for s in research.catalog._scopes.values()]
    catalog_raw=_canonical({'registry_version':'research-registry-v1','registrations':registrations})
    assert sha256(catalog_raw).hexdigest()==research.catalog.sha256 and len(research._contexts)==1
    catalog=write('catalog.json',catalog_raw)
    farm=request['farm'];holds=farms.replay.thermal.holds
    market_scope=write('market-scope.json',_canonical(holds._scope_resolver('tenant-1',farm['snapshot_id'],farm['decision_context_id'])))
    crop_root=tmp_path/'crop';legacy_root=tmp_path/'legacy'
    for path in (crop_root,legacy_root):path.mkdir(mode=0o700)
    cert,tls_key,_=tls_files
    descriptor=jobs._content_directory(create=True);os.close(descriptor)
    cfg=config(policy=jobs.runtime_identity[0],dsn=jobs._dsn,artifact_root=jobs.artifact_root,
        certificate=cert,private_key=tls_key,port=0)
    doc={'config_version':loader.VERSION,'policy':asdict(cfg.policy),
        'dsn_file':str(write('authority.dsn',cfg.dsn.encode())),'artifact_root':str(cfg.artifact_root),
        'certificate':str(cert),'private_key':str(tls_key),
        'thermal_gate_key_file':str(write('thermal.key',cfg.thermal_gate_key)),
        'market_hold_key_file':str(write('market.key',cfg.market_hold_key)),
        'authored_run_gate_key_file':None,'content_access':None,'host':cfg.host,'port':cfg.port,
        'dependencies_factory':'test_crop_harvest_runtime_factory:owned_dependencies'}
    config_path=write('api.json',json_raw(doc));config_sha=sha256(config_path.read_bytes()).hexdigest()
    bundle={'version':'owned-harvest-protected-restore-v1','scope':'owned_synthetic_zero_crop_outputs',
        'factory_module_sha256':sha256(Path(__file__).read_bytes()).hexdigest(),'reader_factory_code_sha256':factory.CODE_SHA256,
        'keys':keys,'crop_root':str(crop_root),'legacy_root':str(legacy_root),'reader_config':str(reader_config),
        'catalog_file':str(catalog),'catalog_sha256':research.catalog.sha256,'owned_fixture_root':str(research.registry._root),
        'owned_context_id':next(iter(research._contexts.values())),'market_scope_file':str(market_scope),
        'static_sha256':{str(p):sha256(p.read_bytes()).hexdigest() for p in files}}
    bundle_path=write('bundle.json',json_raw(bundle));bundle_sha=sha256(bundle_path.read_bytes()).hexdigest()
    monkeypatch.setenv('OSSF_OWNED_HARVEST_RESTORE_BUNDLE',str(bundle_path))
    monkeypatch.setenv('OSSF_OWNED_HARVEST_RESTORE_SHA256',bundle_sha)
    protected={p:(sha256(p.read_bytes()).hexdigest(),p.stat().st_mode,p.stat().st_ino) for p in files+[cert,tls_key]}
    fd=len(os.listdir('/proc/self/fd'));responses=[]
    def run(denied=False):
        code='import json,sys;from test_crop_harvest_runtime_factory import owned_child;print(json.dumps(owned_child(sys.argv[1],sys.argv[2],sys.argv[3]=="denied"),sort_keys=True))'
        argv=[sys.executable,'-c',code,str(config_path),config_sha,'denied' if denied else 'normal']
        started=perf_counter();child=subprocess.run(argv,capture_output=True,text=True,timeout=30)
        assert child.returncode==0 and child.stderr==''
        value=json.loads(child.stdout);assert value['pid']!=os.getpid()
        responses.append({'original_child_exit_code':child.returncode,'argv_sha256':sha256(json_raw(argv)).hexdigest(),
            'seconds':perf_counter()-started,'stdout_sha256':sha256(child.stdout.encode()).hexdigest(),'response':value})
        return value
    def counts():
        with jobs.connect() as conn:
            result={name:conn.execute(sql.SQL('SELECT count(*) AS n FROM {}').format(jobs._table(name))).fetchone()['n']
                for name in ('jobs','job_events','crop_cycle_research_results','crop_cycle_verified_research_results')}
        with psycopg.connect(dsns[scope.reader]) as conn:
            result['harvest_rows']=conn.execute(sql.SQL('SELECT count(*) FROM {}').format(sql.Identifier(scope.schema,'harvest_registered_results'))).fetchone()[0]
        return result
    before=counts()
    try:
        first=run();second=run();assert first['pid']!=second['pid']
        assert first['result']==second['result'] and first['result']['counts']==before
        assert first['result']['catalog_sha256']==research.catalog.sha256
        endpoint=sha256(json_raw([login_database['host'],login_database['port'],login_database['database']])).hexdigest()
        assert first['result']['authenticated_endpoint_sha256']==endpoint
        harvest_key.chmod(0o644)
        try:assert run(denied=True)['result']['denied'] is True
        finally:harvest_key.chmod(0o600)
        assert protected=={p:(sha256(p.read_bytes()).hexdigest(),p.stat().st_mode,p.stat().st_ino) for p in protected}
        assert counts()==before and fd==len(os.listdir('/proc/self/fd'))
        assert not any(list(p.iterdir()) for p in (crop_root,legacy_root,harvest_root))
        save_native('harvest-protected-fresh.json',{'scope':'owned_actual_operator_import_and_fresh_ApiRuntime_zero_rows_no_HTTP_or_product_CLI',
            'actual_same_DB_SCRAM':True,'responses':responses,'counts_before':before,'counts_after':counts(),
            'protected_config_sha256':config_sha,'bundle_sha256':bundle_sha,'catalog_sha256':research.catalog.sha256,
            'protected_files_unchanged':True,'protected_file_count':len(protected),'FD_before_after':[fd,fd],
            'new_crop_or_harvest_rows':0,'actual_HTTP_TLS_tests':0,'gates':'not_assessed'})
    finally:
        for p in files:p.unlink(missing_ok=True)
        assert not any(p.exists() for p in files)
        save_native('harvest-protected-private-cleanup.json',{'protected_files_after':0,'removed_file_count':len(files)})
