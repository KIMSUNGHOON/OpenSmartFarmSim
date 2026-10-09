"""Actual SCRAM farm, current source/review, and a fresh exec without physics."""
from copy import deepcopy
from dataclasses import asdict
from hashlib import sha256
import json
import os
from pathlib import Path
import subprocess
import sys
from time import perf_counter

import psycopg
import pytest

from app import crop_climate_joint_farm_binding as model
from app.crop_result_store import READ_SCOPES,WRITE_SCOPES
from app.thermal_run_store import _canonical
from test_farm_authoring_storage import authoring,request
from test_farm_replay_scenario import farm_setup
from test_crop_cycle_farm_binding import counts
import test_crop_climate_joint_input_evidence as inputs
from login_database import login_database,login_scope

profiles=inputs.profiles
FRESH_PYTHONPATH=os.pathsep.join((str(Path(__file__).resolve().parents[1]),str(Path(__file__).resolve().parent)))
pytestmark=pytest.mark.parametrize('login_scope',[{'market_calculation':True,'market_source_storage':True,
    'thermal_scenario_storage':True,'break_even_calculation':True,'crop_cycle_result_storage':True}],indirect=True)


class SyntheticJointRights:
    policy_version='owned-joint-input-rights-test-v1'
    allowed=True
    def __init__(self):self.calls=[]
    def __call__(self,tenant,declaration,source,use):
        self.calls.append(use)
        return self.allowed is True and tenant=='tenant-1' and declaration['schema_version']==model.RIGHTS_VERSION \
            and declaration['input_source_sha256']==source and use in ('research_calculation','research_display')


def save(name,value):
    directory=os.environ.get('OSSF_JOINT_FARM_EVIDENCE')
    if directory:
        p=Path(directory)/name
        with p.open('x') as f:os.fchmod(f.fileno(),0o400);json.dump(value,f,sort_keys=True,indent=2);f.flush();os.fsync(f.fileno())


@pytest.fixture(scope='module',autouse=True)
def cleanup(login_database):
    yield
    with psycopg.connect(login_database['admin']) as conn:
        schemas=conn.execute("SELECT count(*) FROM pg_namespace WHERE nspname LIKE 'login_test_%'").fetchone()[0]
        roles=conn.execute("SELECT count(*) FROM pg_roles WHERE rolname LIKE 'login_%'").fetchone()[0]
    save('database-cleanup.json',{'schemas':schemas,'roles':roles});assert schemas==roles==0


def build(authoring,directory,profiles,origin=None):
    farms,farm_body,principal=authoring;registered=farms.submit('tenant-1',request(farm_body));principal['scopes'].update(WRITE_SCOPES)
    origin=inputs.reference.origin('2026-10-01T00:00:00.123456Z') if origin is None else origin
    p=inputs.packet(directory,profiles,origin=origin);server=inputs.authority(p[3]);proof=inputs.issue(server,p)
    body={'study_id':'joint-study','revision':'r1','farm':{'scenario_id':farm_body['farm']['scenario_id'],
        'scenario_revision':farm_body['farm']['scenario_revision'],'registration_sha256':registered.scenario_sha256,'crop_id':'crop-1'},
        'input':{'schema_version':inputs.model.SOURCE_VERSION,'program_id':p[2]._context.program['scenario']['input_id'],
            'source_sha256':p[1],'context_sha256':p[2]._context.root_sha256,'time_binding_sha256':p[2].sha256,
            'evidence_sha256':sha256(proof).hexdigest()},
        'rights':{'schema_version':model.RIGHTS_VERSION,'declaration_id':'owned-joint-source','revision':'r1',
            'input_source_sha256':p[1],'available_at':farm_body['farm']['decision_at'],'redistribute':False,
            **{k:True for k in ('ownership_asserted','access','store','transform','use','display')}}}
    rights=SyntheticJointRights();service=model.JointFarmBinding(farms,server,input_rights=rights)
    return service,body,p,proof,principal,rights


def forbid(monkeypatch):
    m=inputs.model;c=m.continuation;calls={k:0 for k in ('prepare_context','start','restore','advance','RHS','step','event','prepare_binding')}
    def blocked(key):
        def fail(*a,**kw):calls[key]+=1;pytest.fail('farm binding invoked '+key)
        return fail
    for target,name,key in ((c,'prepare_context','prepare_context'),(c,'start','start'),(c,'restore_checkpoint','restore'),
        (c,'advance_chunk','advance'),(m.joint,'evaluate_rhs','RHS'),(c.driver.short,'integrate','step'),
        (c.driver.management,'apply_management','event'),(m.clock,'prepare_binding','prepare_binding')):
        monkeypatch.setattr(target,name,blocked(key))
    return calls


@pytest.fixture
def setup(authoring,tmp_path,profiles,monkeypatch):
    value=build(authoring,tmp_path/'inputs',profiles);calls=forbid(monkeypatch)
    yield value
    assert all(n==0 for n in calls.values())


def prepare(value):
    service,body,p,proof,*_=value;return service.prepare('tenant-1',_canonical(body),p[0],proof)


def current(value,expected,*,tenant='tenant-1',write=False,body=None):
    service,original,p,proof,*_=value
    return service.current(tenant,_canonical(original if body is None else body),p[0],proof,expected,write=write)


FRESH_SCRIPT='''from pathlib import Path
import json,sys
from app.runtime_roles import RuntimeLoginPolicy
from app.job_store import JobStore
from app.market_source_store import MarketSourceStore
from app.market_candidate_store import MarketCandidateStore
from app.market_hold_store import MarketHoldStore
from app.thermal_run_store import ThermalRunStore
from app.thermal_scenario_store import ThermalScenarioStore
from app.api_market_source import _MarketSources
from app.research_registry import ResearchRegistry
from app.owned_research import OwnedResearchService
from app.owned_fixture_registry import OwnedFixtureRegistry
from app.farm_replay_scenario import FarmReplayScenarioService
from app.farm_authoring_storage import FarmAuthoringService
from test_market_hold_store import HOLD_KEY,context_verifier
import test_crop_climate_joint_farm_binding as t
p=json.loads(Path(sys.argv[1]).read_bytes());policy=RuntimeLoginPolicy(**p['policy']);identity=(policy,'authority')
principal=p['principal'];principal['scopes']=set(principal['scopes']);provider=lambda:principal
kw={'runtime_identity':identity,'principal_provider':provider};dsn=p['dsn'];schema=policy.schema
jobs=JobStore(dsn,schema,Path(p['artifacts']),audit_runtime_grants=True,**kw)
sources=MarketSourceStore(dsn,schema,**kw)
runs=ThermalRunStore(dsn,schema,gate_key=b'synthetic-gate-key-32-bytes-long!',release_verifier=lambda *_:None,context_verifier=context_verifier,**kw)
holds=MarketHoldStore(dsn,schema,context_store=runs,scope_resolver=lambda *_:dict(p['scope']),signing_key=HOLD_KEY,**kw)
view=_MarketSources(sources,holds,principal_provider=provider);candidates=MarketCandidateStore(dsn,schema,view,**kw)
raw=p['registry_raw'].encode();registry=ResearchRegistry(raw,p['registry_sha256'])
owned=OwnedResearchService(jobs,runs,registry,OwnedFixtureRegistry(Path(p['root'])),{next(iter(registry._scopes)):p['context_id']})
replay=FarmReplayScenarioService(jobs,ThermalScenarioStore(runs,holds),candidates,registry,owned_research=owned)
review=dict(p['review']);authority=t.inputs.authority(review);rights=t.SyntheticJointRights()
service=t.model.JointFarmBinding(FarmAuthoringService(replay),authority,input_rights=rights)
calls={k:0 for k in ('prepare_context','start','restore','advance','RHS','step','event','prepare_binding')}
def blocked(key):
 def fail(*a,**kw):calls[key]+=1;raise AssertionError('fresh invoked '+key)
 return fail
m=t.inputs.model;c=m.continuation
for target,name,key in ((c,'prepare_context','prepare_context'),(c,'start','start'),(c,'restore_checkpoint','restore'),(c,'advance_chunk','advance'),(m.joint,'evaluate_rhs','RHS'),(c.driver.short,'integrate','step'),(c.driver.management,'apply_management','event'),(m.clock,'prepare_binding','prepare_binding')):setattr(target,name,blocked(key))
body=t._canonical(p['body']);proof=Path(p['proof']).read_bytes();expected=Path(p['binding']).read_bytes();before=t.counts(service)
raw=service.current('tenant-1',body,p['directory'],proof,expected);assert raw==expected
with jobs.connect() as conn:assert conn.pgconn.used_password and conn.info.get_parameters()['require_auth']=='scram-sha-256'
review['status']='revoked'
try:service.current('tenant-1',body,p['directory'],proof,expected)
except t.model.JointFarmBindingHold:pass
else:raise AssertionError('fresh review revocation reused binding')
assert t.counts(service)==before and all(n==0 for n in calls.values())
print(json.dumps({'binding_sha256':t.sha256(raw).hexdigest(),'calls':calls,'review_revocation_rejected':True,'counts':before,'actual_scram':True}))
'''


def test_normal_registered_bind_and_actual_fresh_exec(setup,tmp_path,monkeypatch):
    service,body,p,proof,principal,rights=setup;before=counts(service);checks=[];original=service.input_authority.verify
    def verify(*a,**kw):checks.append(1);return original(*a,**kw)
    monkeypatch.setattr(service.input_authority,'verify',verify)
    started=perf_counter();raw=prepare(setup);prepare_seconds=perf_counter()-started;v=json.loads(raw)
    assert len(checks)==2 and rights.calls==['research_calculation','research_display']*2
    assert v['version']==model.VERSION and v['G0_G4']=='not_assessed' and v['request']==body
    assert v['input']['context_sha256']==p[2]._context.root_sha256 and v['input']['time_binding_sha256']==p[2].sha256
    assert v['input']['period']=={'start':p[2].manifest['start_utc'],'end':p[2].manifest['end_utc']}
    assert v['input']['initial_state_sha256']==inputs.model._record(p[2])['initial_state_sha256']
    assert v['registration']['crop']['crop_id']=='crop-1' and v['registration']['crop']['batch_id']
    assert v['registration']['zone_id'] and v['registration']['floor_area']['unit']=='m²'
    assert v['registration']['profile_applicability']=='unvalidated_for_registered_crop'
    checks.clear();rights.calls.clear();started=perf_counter();assert current(setup,raw)==raw;current_seconds=perf_counter()-started
    assert len(checks)==2 and rights.calls==['research_display']*2 and current(setup,raw,write=True)==raw
    replay=service.farms.replay;registry=[]
    for s in replay.registry._scopes.values():registry.append({'tenant_id':s.tenant_id,'point':{'latitude':s.point[0],'longitude':s.point[1]},
        'period_start_utc':s.period_start_utc,'period_end_utc':s.period_end_utc,'goal_id':s.goal_id,'provider_ids':list(s.provider_ids)})
    registry_raw=_canonical({'registry_version':'research-registry-v1','registrations':registry})
    assert sha256(registry_raw).hexdigest()==replay.registry.sha256
    proof_path=tmp_path/'proof.private.json';proof_path.write_bytes(proof);proof_path.chmod(0o400)
    binding_path=tmp_path/'binding.private.json';binding_path.write_bytes(raw);binding_path.chmod(0o400)
    pack={'policy':asdict(service.jobs.runtime_identity[0]),'dsn':service.jobs._dsn,'artifacts':str(service.jobs.artifact_root),
        'principal':{**principal,'scopes':sorted(principal['scopes'])},'scope':replay.thermal.holds._scope_resolver(None,None,None),
        'registry_raw':registry_raw.decode(),'registry_sha256':replay.registry.sha256,'context_id':'context-1','root':str(inputs.reference.reference.ROOT),
        'review':p[3],'body':body,'proof':str(proof_path),'binding':str(binding_path),'directory':str(p[0])}
    config=tmp_path/'fresh.private.json';config.write_text(json.dumps(pack));config.chmod(0o600)
    child=subprocess.Popen([sys.executable,'-B','-c',FRESH_SCRIPT,str(config)],stdin=subprocess.DEVNULL,stdout=subprocess.PIPE,stderr=subprocess.PIPE,
        env=dict(os.environ,PYTHONPATH=FRESH_PYTHONPATH))
    stdout,stderr=child.communicate(timeout=60);assert child.returncode==0,stderr.decode();fresh=json.loads(stdout)
    assert fresh['binding_sha256']==sha256(raw).hexdigest() and fresh['review_revocation_rejected'] and all(n==0 for n in fresh['calls'].values())
    assert counts(service)==before and before[2:]==(0,0)
    save('normal-binding.json',{'binding':v,'binding_bytes':len(raw),'binding_sha256':sha256(raw).hexdigest(),'prepare_seconds':prepare_seconds,
        'current_seconds':current_seconds,'counts_before_after':[before,counts(service)],'proof_checks_per_call':2,'fresh':{**fresh,'PID':child.pid,'actual_exit':child.returncode,'fresh_exec':True}})


def test_current_permissions_reviews_and_sources(setup,monkeypatch):
    service,body,p,proof,principal,rights=setup;raw=prepare(setup);before=counts(service);checked=[]
    principal['scopes'].remove('crop_result_write');assert current(setup,raw)==raw
    with pytest.raises(PermissionError):current(setup,raw,write=True)
    principal['scopes'].add('crop_result_write');checked.append('read-versus-write')
    for scope in READ_SCOPES:
        principal['scopes'].remove(scope)
        with pytest.raises(PermissionError):current(setup,raw)
        principal['scopes'].add(scope);checked.append(scope)
    with pytest.raises(PermissionError):current(setup,raw,tenant='foreign')
    rights.allowed=False
    with pytest.raises(model.JointFarmBindingHold):current(setup,raw)
    rights.allowed=True;p[3]['status']='revoked'
    with pytest.raises(model.JointFarmBindingHold):current(setup,raw)
    p[3]['status']='accepted_for_software_validation'
    with monkeypatch.context() as patch:
        patch.setattr(service.farms.replay.candidates._source._source,'get_input_rights',lambda *_:None)
        with pytest.raises(model.JointFarmBindingHold):current(setup,raw)
    assert counts(service)==before;save('current-rights.json',{'scopes_checked':checked,'foreign_tenant_rejected':True,'source_review_rights_revocations_rejected':True,'counts_unchanged':True})


def test_closed_requests_and_mixed_provenance(setup):
    service,body,p,proof,*_=setup;raw=prepare(setup);before=counts(service);checked=[]
    for kind in ('extra','source','context','time','evidence','program','old-input','old-rights','rights-source','rights-type','redistribute','available','crop','farm','revision','null'):
        v=deepcopy(body)
        if kind=='extra':v['filesystem_path']='/tmp/forbidden'
        elif kind in ('source','context','time','evidence'):v['input'][{'source':'source_sha256','context':'context_sha256','time':'time_binding_sha256','evidence':'evidence_sha256'}[kind]]='0'*64
        elif kind=='program':v['input']['program_id']='different-program'
        elif kind=='old-input':v['input']['schema_version']='crop-cycle-input-packet-v1'
        elif kind=='old-rights':v['rights']['schema_version']='crop-cycle-input-rights-v1'
        elif kind=='rights-source':v['rights']['input_source_sha256']='0'*64
        elif kind=='rights-type':v['rights']['display']=1
        elif kind=='redistribute':v['rights']['redistribute']=True
        elif kind=='available':v['rights']['available_at']='2099-01-01T00:00:00Z'
        elif kind=='crop':v['farm']['crop_id']='other-crop'
        elif kind=='farm':v['farm']['registration_sha256']='0'*64
        elif kind=='revision':v['farm']['scenario_revision']='other-revision'
        else:v['input']=None
        with pytest.raises(model.JointFarmBindingHold):current(setup,raw,body=v)
        checked.append(kind)
    for bad in (b' '+_canonical(body),b'{"x":1,"x":2}',b'{"x":NaN}',b'\xff',b'',b' '*(model.MAX_BINDING_BYTES+1)):
        with pytest.raises(model.JointFarmBindingHold):service.prepare('tenant-1',bad,p[0],proof)
    with pytest.raises(model.JointFarmBindingHold):current(setup,raw+b' ')
    assert counts(service)==before;save('closed-and-mixed.json',{'request_cases':checked,'raw_cases':6,'expected_binding_rejected':True,'counts_unchanged':True})


def test_late_callback_changes_rejected_without_new_rows(setup,monkeypatch):
    service,body,p,proof,principal,rights=setup;raw=prepare(setup);before=counts(service);checked=[]
    for kind in ('rights','review','source','scope','bytes','declaration'):
        with monkeypatch.context() as patch:
            original=SyntheticJointRights.__call__;calls=[]
            def changed(self,tenant,declaration,source,use):
                answer=original(self,tenant,declaration,source,use);calls.append(1)
                if len(calls)==1:
                    if kind=='rights':self.allowed=False
                    elif kind=='review':p[3]['status']='revoked'
                    elif kind=='source':patch.setattr(service.farms.replay.candidates._source._source,'get_input_rights',lambda *_:None)
                    elif kind=='scope':principal['scopes'].remove('crop_result_read')
                    elif kind=='bytes':
                        target=p[0]/'source.json';target.chmod(0o600);target.write_bytes(target.read_bytes()+b' ');target.chmod(0o400)
                    else:declaration['display']=False
                return answer
            patch.setattr(SyntheticJointRights,'__call__',changed)
            old_bytes=(p[0]/'source.json').read_bytes()
            with pytest.raises((model.JointFarmBindingHold,PermissionError)):current(setup,raw,write=True)
            rights.allowed=True;p[3]['status']='accepted_for_software_validation';principal['scopes'].add('crop_result_read')
            if kind=='bytes':
                target=p[0]/'source.json';target.chmod(0o600);target.write_bytes(old_bytes);target.chmod(0o400)
        checked.append(kind)
    assert counts(service)==before;save('late-callbacks.json',{'cases':checked,'counts_unchanged':True})


def test_fixed_runtime_configuration_and_exact_true(setup,monkeypatch):
    service,body,p,proof,_,rights=setup;raw=prepare(setup);checked=[]
    for target,name,value in ((service,'farms',object()),(service,'input_authority',object()),(service,'input_rights',object()),
        (rights,'policy_version','changed'),(service.jobs,'runtime_identity',(service.jobs.runtime_identity[0],'request')),
        (model,'CODE_SHA256','0'*64),(service.input_authority,'key_id','changed')):
        with monkeypatch.context() as patch:
            patch.setattr(target,name,value)
            with pytest.raises(model.JointFarmBindingHold):current(setup,raw)
        checked.append(name)
    for value in (1,'true',None,{},False):
        with monkeypatch.context() as patch:
            patch.setattr(SyntheticJointRights,'__call__',lambda *a:value)
            with pytest.raises(model.JointFarmBindingHold):current(setup,raw)
    with pytest.raises(model.JointFarmBindingHold):current(setup,raw,write=1)
    save('runtime-fixed.json',{'configuration_cases':checked,'non_true_answers_rejected':5,'bool_write_required':True})


def test_authenticated_utc_outside_actual_crop_period(authoring,tmp_path,profiles,monkeypatch):
    value=build(authoring,tmp_path/'outside',profiles,origin=inputs.reference.origin('2026-01-01T00:00:00Z'))
    edge=build(authoring,tmp_path/'microsecond-edge',profiles,origin=inputs.reference.origin('2026-10-24T23:59:28.000001Z'))
    before=counts(value[0]);calls=forbid(monkeypatch)
    with pytest.raises(model.JointFarmBindingHold):prepare(value)
    assert edge[2][2].manifest['end_utc']=='2026-10-25T00:00:00.000001Z'
    with pytest.raises(model.JointFarmBindingHold):prepare(edge)
    assert counts(value[0])==before and all(n==0 for n in calls.values())
    save('outside-period.json',{'authenticated_time_origin':'2026-01-01T00:00:00Z','actual_occupancy_rejected':True,
        'authenticated_end_one_microsecond_outside':edge[2][2].manifest['end_utc'],'counts_unchanged':True})
