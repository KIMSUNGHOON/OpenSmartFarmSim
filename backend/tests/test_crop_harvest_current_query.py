"""Registered reads against actual owned SCRAM authority, including fresh exec."""
from copy import deepcopy
from dataclasses import asdict
from datetime import datetime, timezone
from hashlib import sha256
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
from time import perf_counter

import pytest
from psycopg import sql

from app import crop_harvest_current_query as query
from app.crop_cycle_calculation_result_evidence import CalculationResultEvidenceAuthority
from test_crop_harvest import (mass_profile, allocation_profile, server_setup, bound_setup,
    counts, login_scope, original_login_scope, authoring, farm_setup, login_database,
    native_cleanup, forbid_calculation, save_native)
from test_crop_harvest_registry import harvest_scope
from test_crop_cycle_calculation_server_custody_farms import BUDGET
from test_crop_cycle_calculation_result_store_farms import DB_KEY

registry = query.registry
RESULT_KEY = b'owned-harvest-read-result-proof-key-001'
HARVEST_KEY = b'owned-harvest-current-query-key-000001'
FACTORY_VERSION = 'owned-harvest-actual-db-read-factory-v1'
_RUNTIME = None


def request_values():
    return registry.VERSION+':'+'1'*64, {'scenario_id':'owned-farm','scenario_revision':'1',
        'registration_sha256':'2'*64,'crop_id':'owned-crop'}


@pytest.mark.parametrize('case',['id-type','id-prefix','id-hash','farm-type','farm-extra','farm-missing',
    'farm-path','farm-hash','start-bool','start-negative','start-summary','limit-bool','limit-zero','limit-large'])
def test_invalid_identifier_farm_or_page_is_rejected(case):
    result,farm = request_values();start=0;limit=None
    if case=='id-type':result=None
    elif case=='id-prefix':result='foreign:'+'1'*64
    elif case=='id-hash':result=registry.VERSION+':'+'g'*64
    elif case=='farm-type':farm=[]
    elif case=='farm-extra':farm['approved']=True
    elif case=='farm-missing':del farm['crop_id']
    elif case=='farm-path':farm['scenario_id']='../escape'
    elif case=='farm-hash':farm['registration_sha256']='unknown'
    elif case=='start-bool':start=True
    elif case=='start-negative':start=-1
    elif case=='start-summary':start=1
    elif case=='limit-bool':limit=True
    elif case=='limit-zero':limit=0
    else:limit=65
    with pytest.raises(query.HarvestCurrentQueryHold):query._request(result,farm,start,limit)


def test_summary_and_bounded_page_requests_preserve_arguments():
    result,farm=request_values();original=deepcopy(farm)
    for start,limit in ((0,None),(0,1),(0,64),(17,3)):
        query._request(result,farm,start,limit)
    assert farm==original


@pytest.mark.parametrize('store',[None,{},object()])
def test_implicit_query_configuration_is_rejected_without_DB(store):
    with pytest.raises(query.HarvestCurrentQueryHold):query.HarvestCurrentQuery(store)


@pytest.mark.parametrize('name',['VERSION','CODE_SHA256','DEPENDENCY_SHA256','MAX_RESULT_BYTES'])
def test_changed_query_policy_or_code_is_rejected(monkeypatch,name):
    monkeypatch.setattr(query,name,{} if name=='DEPENDENCY_SHA256' else 1 if name=='MAX_RESULT_BYTES' else 'changed')
    with pytest.raises(query.HarvestCurrentQueryHold):query._pins()


def test_internal_response_limit_counts_metadata_and_all_other_fields():
    record={'result_id':'owned','payload_raw':b'{}','payload_sha256':'1'*64,
        'recorded_at':datetime(2026,10,1,tzinfo=timezone.utc)}
    value={'record':record,'summary':{},'page':None,'identity':{}}
    query._bounded(value)
    with pytest.raises(query.HarvestCurrentQueryHold):
        query._bounded({**value,'summary':{'text':'x'*query.MAX_RESULT_BYTES}})


def runtime_module():
    global _RUNTIME
    if _RUNTIME is not None:return _RUNTIME
    path=Path(__file__).resolve().parents[2]/'research/crop-cycle-registered-runtime.py'
    spec=importlib.util.spec_from_file_location('owned_harvest_actual_db_runtime',path)
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    module.Rights=FreshRights
    _RUNTIME=module
    return module


class FreshRights:
    policy_version='owned-harvest-separate-display-calculation-rights-v1'
    def __init__(self,path):self.path=path
    def __call__(self,tenant,declaration,root,intended_use):
        value=json.loads(runtime_module_bytes(self.path))
        assert tenant=='tenant-1' and type(declaration) is dict and query.current.inputs._digest(root)
        assert set(value)=={'research_calculation','research_display'} and all(type(v) is bool for v in value.values())
        assert intended_use in value
        return value[intended_use]


def runtime_module_bytes(path):
    return runtime_module().private_bytes(path)


class FreshEvidence:
    version='owned-harvest-protected-result-evidence-v1'
    def __init__(self,directory,input_path,result_path):
        self.directory=Path(directory);self.input_path=input_path;self.result_path=result_path
    def __call__(self,tenant,packet):
        assert tenant=='tenant-1'
        return {'input_directory':self.directory,'input_evidence_raw':runtime_module_bytes(self.input_path),
            'result_evidence_raw':runtime_module_bytes(self.result_path)}


def replace_control(path,value):
    path=Path(path);path.chmod(0o600)
    with path.open('wb') as stream:
        stream.write(registry._canonical(value));stream.flush();os.fchmod(stream.fileno(),0o400);os.fsync(stream.fileno())


def forbid_all_reads_math(monkeypatch):
    forbid_calculation(monkeypatch)
    def forbidden(*a,**k):raise AssertionError('registered read recalculated or published')
    for module,name in ((registry.harvest,'_read_allocations'),(registry.harvest,'_mass_row'),
            (registry.harvest,'_allocation_row'),(registry.HarvestRegistry,'put'),
            (CalculationResultEvidenceAuthority,'issue')):
        monkeypatch.setattr(module,name,forbidden)


def load_fresh_query(path,digest):
    runtime=runtime_module();raw=runtime.private_bytes(path);bundle=json.loads(raw)
    assert sha256(raw).hexdigest()==digest and registry._canonical(bundle)==raw
    assert set(bundle)=={'version','scope','factory_sha256','rights_version','runtime_config','runtime_sha256',
        'files','static_sha256','policy','harvest_directory','result_id','farm'}
    assert bundle['version']==FACTORY_VERSION and bundle['scope']=='owned_synthetic_only'
    assert bundle['factory_sha256']==sha256(Path(__file__).read_bytes()).hexdigest()
    assert bundle['rights_version']==FreshRights.policy_version
    assert set(bundle['files'])=={'parent_key','result_key','harvest_key','reader_dsn','input_evidence','result_evidence'}
    assert set(bundle['static_sha256'])==set(bundle['files'].values())
    assert all(sha256(runtime.private_bytes(p)).hexdigest()==h for p,h in bundle['static_sha256'].items())
    server,raw=runtime.load_runtime(bundle['runtime_config'],bundle['runtime_sha256'])
    config=json.loads(runtime.private_bytes(bundle['runtime_config']));files=bundle['files']
    store=query.current.storage.CalculationCycleCropResultStore(server,integrity_key=runtime.private_bytes(files['parent_key']))
    issuer=CalculationResultEvidenceAuthority(server.binding.input_authority,integrity_key=runtime.private_bytes(files['result_key']),
        issuer_id='owned-harvest-read',key_id='result-v1')
    evidence=FreshEvidence(config['input']['directory'],files['input_evidence'],files['result_evidence'])
    current=query.current.CalculationCurrentCycleQuery(store,issuer,evidence_resolver=evidence)
    policy=registry.schema.HarvestRegistryPolicy(**bundle['policy'])
    reader=registry.HarvestRegistry(current,policy,Path(bundle['harvest_directory']),
        dsn=runtime.private_bytes(files['reader_dsn']).decode(),integrity_key=runtime.private_bytes(files['harvest_key']))
    return query.HarvestCurrentQuery(reader),bundle


def fresh_child(path,digest,denied=False):
    before=len(os.listdir('/proc/self/fd'))
    with pytest.MonkeyPatch.context() as patch:
        forbid_all_reads_math(patch);service,bundle=load_fresh_query(path,digest)
        if denied:
            with pytest.raises(query.HarvestCurrentQueryHold):service.read('tenant-1',bundle['result_id'],bundle['farm'],limit=64)
            value={'display_right_withdrawal_denied':True}
        else:
            full=service.read('tenant-1',bundle['result_id'],bundle['farm'],limit=64)
            split=[service.read('tenant-1',bundle['result_id'],bundle['farm'],start=start,limit=3)['page'] for start in (0,3)]
            assert [r for p in split for r in p['records']]==full['page']['records']
            with service.store._connection() as conn:assert conn.pgconn.used_password
            value={'result_id':full['record']['result_id'],'payload_sha256':full['record']['payload_sha256'],
                'rows_sha256':sha256(registry._canonical(full['page']['records'])).hexdigest(),
                'row_chain_sha256':full['summary']['row_chain_sha256'],
                'summary_sha256':sha256(registry._canonical(full['summary'])).hexdigest(),
                'row_count':len(full['page']['records']),'actual_reader_SCRAM':True,'full_split_equal':True}
        assert len(os.listdir('/proc/self/fd'))==before
        value.update(pid=os.getpid(),FD_before_after=[before,before],RHS_calls=0,harvest_regeneration_calls=0,
            registration_calls=0,new_proof_calls=0,scope='owned_fresh_exec_actual_same_DB',gates='not_assessed')
        print(json.dumps(value,sort_keys=True),flush=True)


@pytest.mark.parametrize('original_login_scope',[{'market_calculation':True,'market_source_storage':True,
    'thermal_scenario_storage':True,'break_even_calculation':True,'crop_cycle_result_storage':True}],indirect=True)
def test_actual_reader_display_only_tampering_and_fresh_same_DB(server_setup,native_cleanup,harvest_scope,monkeypatch,tmp_path):
    original,request_raw,_,_,expected=server_setup
    runtime=runtime_module();config_path,config_sha=runtime.export_runtime(original,request_raw,tmp_path/'protected-runtime')
    config=json.loads(runtime.private_bytes(config_path));rights_path=config['rights_file'];principal_path=config['principal_file']
    rights={'research_calculation':True,'research_display':True};replace_control(rights_path,rights)
    server,request_raw=runtime.load_runtime(config_path,config_sha)
    timings={};started=perf_counter();progress=json.loads(server.advance('tenant-1',request_raw,budget=BUDGET))
    timings['calculate']=perf_counter()-started;assert progress['status']=='completed' and progress['steps']==120
    parent_store=query.current.storage.CalculationCycleCropResultStore(server,integrity_key=DB_KEY)
    parent=parent_store.put('tenant-1',request_raw);parent_packet=json.loads(parent['payload_raw']);farm=json.loads(request_raw)['farm']
    input_directory=Path(config['input']['directory'])
    for path in input_directory.iterdir():path.chmod(0o400)
    issuer=CalculationResultEvidenceAuthority(server.binding.input_authority,integrity_key=RESULT_KEY,
        issuer_id='owned-harvest-read',key_id='result-v1')
    result_directory=server.directory/registry.current.server._intent_id('tenant-1',json.loads(request_raw))/'artifact'
    result_raw=issuer.issue(result_directory,progress['artifact_sha256'],input_directory,
        parent_packet['input_root_sha256'],runtime.private_bytes(config['input']['evidence_file']))
    protected=tmp_path/'protected-query';protected.mkdir(mode=0o700)
    private_raws={'parent_key':DB_KEY,'result_key':RESULT_KEY,'harvest_key':HARVEST_KEY,
        'reader_dsn':harvest_scope[1][harvest_scope[0].reader].encode(),
        'input_evidence':runtime.private_bytes(config['input']['evidence_file']),'result_evidence':result_raw}
    paths={}
    for name,raw in private_raws.items():
        path=protected/(name+'.private');runtime.write_private(path,raw);paths[name]=str(path)
    evidence=FreshEvidence(input_directory,paths['input_evidence'],paths['result_evidence'])
    current=query.current.CalculationCurrentCycleQuery(parent_store,issuer,evidence_resolver=evidence)
    original_parent=current.read('tenant-1',parent['result_id'],farm)
    policy,dsns,directory=harvest_scope
    profile=mass_profile(registry.harvest._source(original_parent));profile['segments'][0]['end_at']=expected['samples'][-1]['at']
    mass_raw=registry._canonical(profile)
    allocation_raw=registry._canonical(allocation_profile(registry.harvest._mass_parameters(mass_raw),last_sample=2,last_event=3))
    publisher=registry.HarvestRegistry(current,policy,directory,dsn=dsns[policy.publisher],integrity_key=HARVEST_KEY)
    registered=publisher.put('tenant-1',parent['result_id'],farm,mass_raw,allocation_raw);packet=json.loads(registered['payload_raw'])
    reader=registry.HarvestRegistry(current,policy,directory,dsn=dsns[policy.reader],integrity_key=HARVEST_KEY)
    service=query.HarvestCurrentQuery(reader)
    with pytest.raises(query.HarvestCurrentQueryHold):query.HarvestCurrentQuery(publisher)
    bundle={'version':FACTORY_VERSION,'scope':'owned_synthetic_only','factory_sha256':sha256(Path(__file__).read_bytes()).hexdigest(),
        'rights_version':FreshRights.policy_version,'runtime_config':str(config_path),'runtime_sha256':config_sha,
        'files':paths,'static_sha256':{p:sha256(runtime.private_bytes(p)).hexdigest() for p in paths.values()},
        'policy':asdict(policy),'harvest_directory':str(directory),'result_id':registered['result_id'],'farm':farm}
    bundle_path=protected/'query.json';bundle_raw=registry._canonical(bundle);runtime.write_private(bundle_path,bundle_raw)
    bundle_sha=sha256(bundle_raw).hexdigest()
    db_before=counts(server.binding);fd_before=len(os.listdir('/proc/self/fd'))
    def inventory():
        return {str(p):(sha256(p.read_bytes()).hexdigest(),p.stat().st_mode&0o777,p.stat().st_ino)
            for d in (server.directory,input_directory,directory) for p in d.rglob('*') if p.is_file()}
    files_before=inventory();forbid_all_reads_math(monkeypatch)
    principal=json.loads(runtime.private_bytes(principal_path));principal['scopes'].remove('crop_result_write')
    replace_control(principal_path,principal);rights['research_calculation']=False;replace_control(rights_path,rights)
    def read(name,**kw):
        started=perf_counter();value=service.read('tenant-1',registered['result_id'],farm,**kw)
        timings[name]=perf_counter()-started;return value
    full=read('display_only_full',limit=64);summary=read('summary')
    split=[read('split_'+str(start),start=start,limit=3)['page'] for start in (0,3)]
    assert full['record']==summary['record']==registered and summary['page'] is None
    assert [r for p in split for r in p['records']]==full['page']['records'] and full['page']['total']==6
    assert full['summary']==summary['summary'] and full['identity']['rights_or_gate_approval'] is False
    artifact_dir=directory/packet['artifact']['key'];root=json.loads((artifact_dir/(packet['artifact']['sha256']+'.json')).read_bytes())
    rows=[r for p in root['pages'] for r in json.loads((artifact_dir/(p['sha256']+'.json')).read_bytes())]
    assert rows==full['page']['records'] and root['summary']==full['summary']
    assert root['source']==packet['source'] and root['parameter_raw_utf8'].encode()==mass_raw
    assert root['allocation_raw_utf8'].encode()==allocation_raw
    assert service.read('tenant-1',registry.VERSION+':'+'0'*64,farm) is None
    rejects=[]
    for case in ('read-scope','account','display-right','foreign-farm','range','signature','artifact-HEAD','artifact-root','artifact-page'):
        try:
            if case in ('read-scope','account'):
                changed=deepcopy(principal)
                if case=='read-scope':changed['scopes'].remove('crop_result_read')
                else:changed['tenant_id']='foreign'
                replace_control(principal_path,changed)
                with pytest.raises(PermissionError):service.read('tenant-1',registered['result_id'],farm,limit=64)
            elif case=='display-right':
                replace_control(rights_path,{**rights,'research_display':False})
                with pytest.raises(query.HarvestCurrentQueryHold):service.read('tenant-1',registered['result_id'],farm,limit=64)
            elif case in ('foreign-farm','range'):
                with pytest.raises(query.HarvestCurrentQueryHold):
                    service.read('tenant-1',registered['result_id'],{**farm,'crop_id':'foreign'} if case=='foreign-farm' else farm,
                        start=7 if case=='range' else 0,limit=64)
            elif case=='signature':
                found=reader._find;forged=found('tenant-1',registered['result_id']);forged['integrity_signature']='0'*64
                with monkeypatch.context() as patch:
                    patch.setattr(reader,'_find',lambda *a:forged)
                    with pytest.raises(query.HarvestCurrentQueryHold):service.read('tenant-1',registered['result_id'],farm,limit=64)
            else:
                target=artifact_dir/('HEAD' if case=='artifact-HEAD' else packet['artifact']['sha256']+'.json'
                    if case=='artifact-root' else root['pages'][0]['sha256']+'.json')
                raw=target.read_bytes()
                try:
                    target.chmod(0o600);target.write_bytes(raw+b' ');target.chmod(0o400)
                    with pytest.raises(query.HarvestCurrentQueryHold):service.read('tenant-1',registered['result_id'],farm,limit=64)
                finally:target.chmod(0o600);target.write_bytes(raw);target.chmod(0o400)
            rejects.append(case)
        finally:replace_control(principal_path,principal);replace_control(rights_path,rights)
        assert len(os.listdir('/proc/self/fd'))==fd_before
    postyield=[]
    for case in ('display-right','registered-row','page'):
        page_path=artifact_dir/(root['pages'][0]['sha256']+'.json');saved=page_path.read_bytes()
        try:
            with monkeypatch.context() as patch:
                with pytest.raises(query.HarvestCurrentQueryHold):
                    with service.open('tenant-1',registered['result_id'],farm,limit=64) as value:
                        assert value['page']['records']==rows
                        if case=='display-right':replace_control(rights_path,{**rights,'research_display':False})
                        elif case=='registered-row':patch.setattr(reader,'_find',lambda *a:None)
                        else:page_path.chmod(0o600);page_path.write_bytes(saved+b' ');page_path.chmod(0o400)
            postyield.append(case)
        finally:
            replace_control(rights_path,rights);page_path.chmod(0o600);page_path.write_bytes(saved);page_path.chmod(0o400)
        assert len(os.listdir('/proc/self/fd'))==fd_before
    children=[]
    for denied in (False,True):
        replace_control(rights_path,{**rights,'research_display':not denied})
        code='from test_crop_harvest_current_query import fresh_child; import sys; fresh_child(sys.argv[1],sys.argv[2],sys.argv[3]=="denied")'
        argv=[sys.executable,'-c',code,str(bundle_path),bundle_sha,'denied' if denied else 'normal']
        started=perf_counter()
        child=subprocess.Popen(argv,cwd=Path(__file__).parents[1],stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True)
        try:stdout,stderr=child.communicate(timeout=120)
        except BaseException:
            child.kill();child.communicate();raise
        assert child.returncode==0,(child.returncode,stderr[-3000:])
        result=json.loads(stdout);assert result['pid']==child.pid and result['pid']!=os.getpid()
        assert result['FD_before_after'][0]==result['FD_before_after'][1]
        assert result['RHS_calls']==result['harvest_regeneration_calls']==result['registration_calls']==result['new_proof_calls']==0
        if denied:assert result['display_right_withdrawal_denied']
        else:
            assert result['result_id']==registered['result_id'] and result['payload_sha256']==registered['payload_sha256']
            assert result['rows_sha256']==sha256(registry._canonical(rows)).hexdigest()
            assert result['summary_sha256']==sha256(registry._canonical(full['summary'])).hexdigest()
            assert result['actual_reader_SCRAM'] and result['full_split_equal'] and result['row_count']==6
        children.append({'pid':child.pid,'actual_exit':child.returncode,'wall_seconds':perf_counter()-started,
            'stdout_sha256':sha256(stdout.encode()).hexdigest(),'stderr_sha256':sha256(stderr.encode()).hexdigest(),'result':result})
    replace_control(rights_path,rights)
    assert current.read('tenant-1',parent['result_id'],farm)==original_parent
    with reader._connection() as conn:
        actual_rows=conn.execute(sql.SQL('SELECT count(*) AS n FROM {}').format(sql.Identifier(policy.schema,registry.schema.TABLE))).fetchone()['n']
        assert conn.pgconn.used_password and actual_rows==1
    assert inventory()==files_before and counts(server.binding)==db_before and len(os.listdir('/proc/self/fd'))==fd_before
    artifact_files={p.name:{'sha256':sha256(p.read_bytes()).hexdigest(),'mode':p.stat().st_mode&0o777,
        'bytes':p.stat().st_size,'canonical_utf8':p.read_text()} for p in artifact_dir.iterdir()}
    saved_row=reader._find('tenant-1',registered['result_id'])
    private_paths=list(protected.iterdir())+list(Path(config_path).parent.iterdir())
    for path in private_paths:path.unlink()
    assert not list(protected.iterdir()) and not list(Path(config_path).parent.iterdir())
    save_native('harvest-current-query-verified.json',{'actual_reader_SCRAM':True,'schema_policy':asdict(policy),
        'farm':farm,'source':packet['source'],'registered_record':{'result_id':registered['result_id'],
        'payload_raw_utf8':registered['payload_raw'].decode(),'payload_sha256':registered['payload_sha256'],
        'recorded_at':registered['recorded_at'].isoformat()},'stored_signature':saved_row['integrity_signature'],
        'registered_by':saved_row['registered_by'],'rows':rows,'artifact_files':artifact_files,
        'summary':full['summary'],'identity':full['identity'],'timings_seconds':timings,
        'row_count':6,'registered_rows':actual_rows,'summary_full_split_equal':True,'display_only_read_without_write_scope':True,
        'rejected_cases':rejects,'postyield_rejected':postyield,'fresh_actual_DB_children':children,
        'RHS_calls':0,'harvest_regeneration_calls':0,'registration_calls_during_read':0,'new_proof_calls':0,
        'FD_before_after':[fd_before,fd_before],'original_parent_query_preserved':True,
        'input_custody_harvest_SHA_mode_inode_preserved':True,'DB_counts_preserved':list(db_before),
        'protected_files_removed':len(private_paths),'protected_files_after':0,
        'actual_coefficients_adopted':0,'actual_crop_Runs':0,'gates':'not_assessed'})
