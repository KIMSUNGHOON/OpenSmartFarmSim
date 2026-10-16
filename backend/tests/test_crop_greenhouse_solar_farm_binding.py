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

from app import crop_greenhouse_solar_farm_binding as model
from app.crop_result_store import READ_SCOPES,WRITE_SCOPES
from app.thermal_run_store import _canonical
from app.api_economic_scenario import EconomicScenarioRequest,EconomicScenarioService
from app.api_market_source import _MarketSources
from app.economic_contracts import EconomicScenario,OwnedEconomicRecord,OwnedSettlementRecord,PriorBatchCostRecord
from app.farm_authoring_storage import FarmAuthoringService,FarmAuthoringRequest,WRITE_SCOPES as FARM_WRITE_SCOPES
from app.farm_replay_scenario import FarmReplayScenarioService,WRITE_SCOPES as REPLAY_WRITE_SCOPES
from app.job_store import JobStore
from app.market_candidate_store import MarketCandidateStore
from app.market_hold_store import MarketHoldStore
from app.market_scenario import MarketScenarioService,MarketScenarioRequest,JointShock,InputRights,Applicability,_json
from app.market_source_store import MarketSourceStore
from app.orchestration import LocationRequest
from app.owned_fixture_registry import OwnedFixtureRegistry
from app.owned_research import OwnedResearchService,ADMISSION_SCOPES as OWNED_SCOPES
from app.research_registry import ResearchRegistry
from app.thermal_run_store import ThermalRunStore
from app.thermal_scenario_store import ThermalScenarioStore
from psycopg import sql
from test_farm_inputs import example
from test_market_hold_store import HOLD_KEY,context_verifier
import test_market_signed_hold_integration as seed
from test_thermal_publisher import input_raws
import test_crop_greenhouse_solar_input_evidence as inputs
from login_database import login_database,login_scope

profiles=inputs.profiles
FRESH_PYTHONPATH=os.pathsep.join((str(Path(__file__).resolve().parents[1]),str(Path(__file__).resolve().parent)))
pytestmark=pytest.mark.parametrize('login_scope',[{'market_calculation':True,'market_source_storage':True,
    'thermal_scenario_storage':True,'break_even_calculation':True,'crop_cycle_result_storage':True}],indirect=True)


@pytest.fixture
def authoring(login_scope,monkeypatch):
    # Build registered inputs through production services; an HTTP app is unnecessary here.
    root=Path(__file__).resolve().parents[2]
    base,policy,dsns=login_scope;identity=(policy,'authority')
    monkeypatch.setattr(seed,'SNAPSHOT_RAWS',input_raws())
    _,values,req,principal,scope=seed.signed_market_assembly(dsns['authority'],policy.schema,runtime_identity=identity)
    req=MarketScenarioRequest.model_validate_json(_json(req)).model_dump(mode='json')
    principal['scopes'].update({'metadata','market_source_read','market_source_write','decision_context_read',
        'location_create','thermal_scenario_write'}|set(FARM_WRITE_SCOPES)|set(REPLAY_WRITE_SCOPES)|set(OWNED_SCOPES))
    provider=lambda:principal;kw={'runtime_identity':identity,'principal_provider':provider}
    jobs=JobStore(dsns['authority'],policy.schema,base.artifact_root,audit_runtime_grants=True,**kw)
    sources=MarketSourceStore(dsns['authority'],policy.schema,**kw)
    groups={'economic_scenario':(values.scenarios,EconomicScenario),'economic_input':(values.records,OwnedEconomicRecord),
        'joint_shock':(values.shocks,JointShock),'input_rights':(values.rights,InputRights),
        'settlement_applicability':(values.bindings,Applicability),'settlement_evidence':(values.settlements,OwnedSettlementRecord),
        'prior_batch_cost':(values.prior_costs,PriorBatchCostRecord)}
    for kind,(items,cls) in groups.items():
        for value in items.values():
            data=cls.model_validate(value).model_dump(mode='json');raw=_canonical(data)
            row=base.submit('tenant-1','simulation',data,'source-'+sha256(raw).hexdigest())
            sources.adopt_job('tenant-1',kind,str(row['job_id']))
    req['shock']['sha256']=sources.get_joint_shock_pin('joint-1','r1')['sha256']
    runs=ThermalRunStore(dsns['authority'],policy.schema,gate_key=b'synthetic-gate-key-32-bytes-long!',
        release_verifier=lambda *_:None,context_verifier=context_verifier,**kw)
    holds=MarketHoldStore(dsns['authority'],policy.schema,context_store=runs,
        scope_resolver=lambda *_:dict(scope),signing_key=HOLD_KEY,**kw)
    candidates=MarketCandidateStore(dsns['authority'],policy.schema,_MarketSources(sources,holds,principal_provider=provider),**kw)
    economic_service=EconomicScenarioService(jobs,candidates)
    registered=economic_service.submit('tenant-1',EconomicScenarioRequest.model_validate_json(
        _canonical({'request':req,'idempotency_key':'farm-economics'})))
    weather=json.loads(input_raws()[1]);location={'latitude':35.0,'longitude':127.0,
        'period_start_utc':weather['start_utc'],'period_end_utc':weather['end_utc'],
        'goal_id':'historical-thermal-replay','idempotency_key':'authored-farm-research'}
    registration={'tenant_id':'tenant-1','point':{'latitude':35.0,'longitude':127.0},
        **{k:location[k] for k in ('period_start_utc','period_end_utc','goal_id')},
        'provider_ids':[OwnedFixtureRegistry(root).provider_id]}
    registry_raw=_canonical({'registry_version':'research-registry-v1','registrations':[registration]})
    registry=ResearchRegistry(registry_raw,sha256(registry_raw).hexdigest())
    owned=OwnedResearchService(jobs,runs,registry,OwnedFixtureRegistry(root),{next(iter(registry._scopes)):'context-1'})
    _,_,research=owned.submit('tenant-1',LocationRequest.model_validate(location))
    hold=holds.get_market_hold_report(req['market_context']['hold_report_id']);thermal=ThermalScenarioStore(runs,holds)
    selected=thermal.put('tenant-1',{'schema_version':'thermal-scenario-v1','scenario_id':'thermal-one','scenario_revision':'r1',
        'tenant_id':'tenant-1','snapshot_id':hold['snapshot_id'],'decision_context_id':hold['decision_context_id'],
        'market_context':req['market_context'],'zone_id':'fixture-zone','goal_id':'historical-thermal-replay',
        'model_version':'thermal-v1','parameter_set_version':'synthetic-thermal-parameters-v1','origin':'user','evidence_level':'assumed'})
    replay=FarmReplayScenarioService(jobs,thermal,candidates,registry,owned_research=owned)
    _,economic,candidate=MarketScenarioService(candidates).validate_pinned(registered.scenario_id,registered.scenario_revision,'tenant-1')
    document=example();document.update(research_job_id=str(research['job_id']),market_context=req['market_context'],
        snapshot_id=hold['snapshot_id'],decision_context_id='context-1',decision_at=economic.decision_at.isoformat().replace('+00:00','Z'),
        period_start=economic.period_start.isoformat(),period_end=economic.period_end.isoformat(),
        economic={'scenario_id':economic.scenario_id,'revision':economic.scenario_revision,
            'sha256':candidate['economic_scenario_sha256'],'candidate_id':candidate['candidate_id']})
    crop=document['crops'][0];crop['batch_id']=economic.harvests[0].batch_id
    crop['grades']=sorted({r.grade for r in economic.packouts}|{r.grade for r in economic.sales})
    crop['channels']=sorted({r.channel for r in economic.packouts}|{r.channel for r in economic.sales})
    rights={'schema_version':'farm-assumption-rights-v1','scenario_id':document['scenario_id'],
        'scenario_revision':document['scenario_revision'],'declaration_id':'self-authored-farm-1','revision':'r1',
        'origin':'user','evidence_level':'assumed','available_at':document['decision_at'],
        'scope_start':document['period_start'],'scope_end':document['period_end'],'redistribute':False,
        **{k:True for k in ('ownership_asserted','access','store','transform','use','display')}}
    return FarmAuthoringService(replay),{'schema_version':'farm-authoring-request-v1','farm':document,'rights':rights},principal


def request(body):return FarmAuthoringRequest.model_validate_json(_canonical(body))


def counts(service):
    with service.jobs.connect() as conn:
        return tuple(conn.execute(sql.SQL('SELECT count(*) AS n FROM {}').format(service.jobs._table(table))).fetchone()['n']
            for table in ('jobs','job_events','crop_cycle_research_results','thermal_g1_runs'))


class SyntheticSolarRights:
    policy_version='owned-solar-input-rights-test-v1'
    allowed=True
    def __init__(self):self.calls=[]
    def __call__(self,tenant,declaration,source,use):
        self.calls.append(use)
        return self.allowed is True and tenant=='tenant-1' and declaration['schema_version']==model.RIGHTS_VERSION \
            and declaration['input_source_sha256']==source and use in ('research_calculation','research_display')


def save(name,value):
    directory=os.environ.get('OSSF_SOLAR_FARM_EVIDENCE')
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


def build(authoring,directory,profiles,origin=None,available_at=None):
    farms,farm_body,principal=authoring;registered=farms.submit('tenant-1',request(farm_body));principal['scopes'].update(WRITE_SCOPES)
    origin=inputs.reference.origin('2026-10-01T00:00:00.123456Z') if origin is None else origin
    p=inputs.packet(directory,profiles,origin=origin)
    source=json.loads((p[0]/'source.json').read_bytes())
    source['provenance'].update(observed_at='2026-09-26T00:00:00Z',published_at='2026-09-27T00:00:00Z',
        available_at='2026-09-27T00:00:00Z' if available_at is None else available_at)
    p=inputs.rewrite_owned_packet(p,source);server=inputs.authority(p[3]);proof=inputs.issue(server,p)
    body={'study_id':'joint-study','revision':'r1','farm':{'scenario_id':farm_body['farm']['scenario_id'],
        'scenario_revision':farm_body['farm']['scenario_revision'],'registration_sha256':registered.scenario_sha256,'crop_id':'crop-1'},
        'input':{'schema_version':inputs.model.SOURCE_VERSION,'program_id':p[2]._context.program['scenario']['input_id'],
            'source_sha256':p[1],'context_sha256':p[2]._context.root_sha256,'time_binding_sha256':p[2].sha256,
            'evidence_sha256':sha256(proof).hexdigest()},
        'rights':{'schema_version':model.RIGHTS_VERSION,'declaration_id':'owned-joint-source','revision':'r1',
            'input_source_sha256':p[1],'available_at':farm_body['farm']['decision_at'],'redistribute':False,
            **{k:True for k in ('ownership_asserted','access','store','transform','use','display')}}}
    rights=SyntheticSolarRights();service=model.SolarFarmBinding(farms,server,input_rights=rights)
    return service,body,p,proof,principal,rights


def forbid(monkeypatch):
    from app import cli_worker
    m=inputs.model;c=m.continuation;calls={k:0 for k in ('prepare_context','start','restore','advance','RHS','step','event','prepare_binding','ventilation','solar','PAR','NIR','CLI')}
    def blocked(key):
        def fail(*a,**kw):calls[key]+=1;pytest.fail('farm binding invoked '+key)
        return fail
    for target,name,key in ((c,'prepare_context','prepare_context'),(c,'start','start'),(c,'restore_checkpoint','restore'),
        (c,'advance_chunk','advance'),(m.joint,'evaluate_rhs','RHS'),(c.driver.stage,'integrate','step'),
        (c.driver.previous.management,'apply_management','event'),(m.clock,'prepare_binding','prepare_binding'),(c.driver.stage.solar_rhs.vent,'calculate_ventilation','ventilation'),(c.driver.stage.solar_rhs,'evaluate_rhs','solar'),(c.driver.stage.solar_rhs.par.radiation,'calculate_par','PAR'),(c.driver.stage.solar_rhs.nir,'calculate_nir','NIR'),(cli_worker.CliWorker,'run_once','CLI')):
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
from copy import deepcopy
from hashlib import sha256
import hmac
from psycopg import sql
from app import crop_greenhouse_solar_farm_binding as model
from app.crop_greenhouse_solar_input_evidence import SolarInputEvidenceAuthority
from app.thermal_run_store import _canonical
HOLD_KEY=b'synthetic-market-hold-key-32bytes!!'
def context_verifier(raw,signature):
 expected=hmac.new(b'synthetic-market-context-key-32bytes',b'decision-context-v1\\0'+raw,sha256).hexdigest()
 if not hmac.compare_digest(signature,expected):return None
 value=json.loads(raw)
 return {k:value[k] for k in ('authority_id','planning_event_sha256','decision_at_utc','decision_time_kind')}
class SyntheticSolarRights:
 policy_version='owned-solar-input-rights-test-v1'
 def __call__(self,tenant,declaration,source,use):
  return tenant=='tenant-1' and declaration['schema_version']==model.RIGHTS_VERSION and declaration['input_source_sha256']==source and use in ('research_calculation','research_display')
def counts(service):
 with service.jobs.connect() as conn:
  return tuple(conn.execute(sql.SQL('SELECT count(*) AS n FROM {}').format(service.jobs._table(table))).fetchone()['n'] for table in ('jobs','job_events','crop_cycle_research_results','thermal_g1_runs'))
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
review=dict(p['review']);authority=SolarInputEvidenceAuthority(integrity_key=p['evidence_key'].encode(),issuer_id='owned-test',key_id='owned-key-v1',review_resolver=lambda _:deepcopy(review));rights=SyntheticSolarRights()
service=model.SolarFarmBinding(FarmAuthoringService(replay),authority,input_rights=rights)
calls={k:0 for k in ('prepare_context','start','restore','advance','RHS','step','event','prepare_binding','ventilation','solar','PAR','NIR','CLI')}
def blocked(key):
 def fail(*a,**kw):calls[key]+=1;raise AssertionError('fresh invoked '+key)
 return fail
from app import cli_worker
m=model.evidence;c=m.continuation
for target,name,key in ((c,'prepare_context','prepare_context'),(c,'start','start'),(c,'restore_checkpoint','restore'),(c,'advance_chunk','advance'),(m.joint,'evaluate_rhs','RHS'),(c.driver.stage,'integrate','step'),(c.driver.previous.management,'apply_management','event'),(m.clock,'prepare_binding','prepare_binding'),(c.driver.stage.solar_rhs.vent,'calculate_ventilation','ventilation'),(c.driver.stage.solar_rhs,'evaluate_rhs','solar'),(c.driver.stage.solar_rhs.par.radiation,'calculate_par','PAR'),(c.driver.stage.solar_rhs.nir,'calculate_nir','NIR'),(cli_worker.CliWorker,'run_once','CLI')):setattr(target,name,blocked(key))
body=_canonical(p['body']);proof=Path(p['proof']).read_bytes();expected=Path(p['binding']).read_bytes();before=counts(service)
raw=service.current('tenant-1',body,p['directory'],proof,expected);assert raw==expected
with jobs.connect() as conn:assert conn.pgconn.used_password and conn.info.get_parameters()['require_auth']=='scram-sha-256'
review['status']='revoked'
try:service.current('tenant-1',body,p['directory'],proof,expected)
except model.SolarFarmBindingHold:pass
else:raise AssertionError('fresh review revocation reused binding')
assert counts(service)==before and all(n==0 for n in calls.values())
print(json.dumps({'binding_sha256':sha256(raw).hexdigest(),'calls':calls,'review_revocation_rejected':True,'counts':before,'actual_scram':True}))
'''


def test_normal_registered_bind_and_actual_fresh_exec(setup,tmp_path,monkeypatch):
    service,body,p,proof,principal,rights=setup;before=counts(service);checks=[];original=service.input_authority.verify
    def verify(*a,**kw):checks.append(1);return original(*a,**kw)
    monkeypatch.setattr(service.input_authority,'verify',verify)
    started=perf_counter();raw=prepare(setup);prepare_seconds=perf_counter()-started;v=json.loads(raw)
    assert len(checks)==2 and rights.calls==['research_calculation','research_display']*2
    assert v['version']==model.VERSION and v['G0_G4']=='not_assessed' and v['request']==body
    assert v['scope']=='synthetic_joint_solar_math_only'
    assert v['input']['model_identity']['ledger_schema']=='joint-solar-ventilation-ledgers-v1'
    assert v['input']['input_evidence_version']==inputs.model.VERSION
    assert v['input']['context_sha256']==p[2]._context.root_sha256 and v['input']['time_binding_sha256']==p[2].sha256
    assert v['input']['period']=={'start':p[2].manifest['start_utc'],'end':p[2].manifest['end_utc']}
    metadata=json.loads((p[0]/'source.json').read_bytes())['provenance']
    assert v['input']['initial_state_sha256']==inputs.model._record(p[2],metadata)['initial_state_sha256']
    assert v['input']['provenance']==metadata and v['input']['provenance_sha256']==sha256(_canonical(metadata)).hexdigest()
    assert v['rights_or_gate_approval'] is False
    assert model.documents._time(metadata['available_at'])<=model.documents._time(v['registration']['decision_at'])
    assert model.documents._time(metadata['retrieved_at'])>model.documents._time(v['registration']['decision_at'])
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
        'evidence_key':inputs.KEY.decode(),'review':p[3],'body':body,'proof':str(proof_path),'binding':str(binding_path),'directory':str(p[0])}
    config=tmp_path/'fresh.private.json';config.write_text(json.dumps(pack));config.chmod(0o600)
    import gc,ctypes
    gc.collect();ctypes.CDLL(None).malloc_trim(0)
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
    with pytest.raises(model.SolarFarmBindingHold):current(setup,raw)
    rights.allowed=True;p[3]['status']='revoked'
    with pytest.raises(model.SolarFarmBindingHold):current(setup,raw)
    p[3]['status']='accepted_for_software_validation'
    with monkeypatch.context() as patch:
        patch.setattr(service.farms.replay.candidates._source._source,'get_input_rights',lambda *_:None)
        with pytest.raises(model.SolarFarmBindingHold):current(setup,raw)
    assert counts(service)==before;save('current-rights.json',{'scopes_checked':checked,'foreign_tenant_rejected':True,'source_review_rights_revocations_rejected':True,'counts_unchanged':True})


def test_closed_requests_and_mixed_provenance(setup):
    service,body,p,proof,*_=setup;raw=prepare(setup);before=counts(service);checked=[]
    for kind in ('extra','source','context','time','evidence','program','old-input','old-rights','old-joint-input','old-joint-rights','old-ventilation-input','old-ventilation-rights','approval','rights-source','rights-type','redistribute','available','crop','farm','revision','null'):
        v=deepcopy(body)
        if kind=='extra':v['filesystem_path']='/tmp/forbidden'
        elif kind in ('source','context','time','evidence'):v['input'][{'source':'source_sha256','context':'context_sha256','time':'time_binding_sha256','evidence':'evidence_sha256'}[kind]]='0'*64
        elif kind=='program':v['input']['program_id']='different-program'
        elif kind=='old-input':v['input']['schema_version']='crop-cycle-input-packet-v1'
        elif kind=='old-rights':v['rights']['schema_version']='crop-cycle-input-rights-v1'
        elif kind=='old-joint-input':v['input']['schema_version']='joint-crop-climate-input-source-v1'
        elif kind=='old-joint-rights':v['rights']['schema_version']='joint-crop-climate-input-rights-v1'
        elif kind=='old-ventilation-input':v['input']['schema_version']='joint-ventilation-input-source-v1'
        elif kind=='old-ventilation-rights':v['rights']['schema_version']='joint-ventilation-input-rights-v1'
        elif kind=='approval':v['rights_or_gate_approval']=True
        elif kind=='rights-source':v['rights']['input_source_sha256']='0'*64
        elif kind=='rights-type':v['rights']['display']=1
        elif kind=='redistribute':v['rights']['redistribute']=True
        elif kind=='available':v['rights']['available_at']='2099-01-01T00:00:00Z'
        elif kind=='crop':v['farm']['crop_id']='other-crop'
        elif kind=='farm':v['farm']['registration_sha256']='0'*64
        elif kind=='revision':v['farm']['scenario_revision']='other-revision'
        else:v['input']=None
        with pytest.raises(model.SolarFarmBindingHold):current(setup,raw,body=v)
        checked.append(kind)
    for bad in (b' '+_canonical(body),b'{"x":1,"x":2}',b'{"x":NaN}',b'\xff',b'',b' '*(model.MAX_BINDING_BYTES+1)):
        with pytest.raises(model.SolarFarmBindingHold):service.prepare('tenant-1',bad,p[0],proof)
    with pytest.raises(model.SolarFarmBindingHold):current(setup,raw+b' ')
    assert counts(service)==before;save('closed-and-mixed.json',{'request_cases':checked,'raw_cases':6,'expected_binding_rejected':True,'counts_unchanged':True})


def test_late_callback_changes_rejected_without_new_rows(setup,monkeypatch):
    service,body,p,proof,principal,rights=setup;raw=prepare(setup);before=counts(service);checked=[]
    for kind in ('rights','review','source','scope','bytes','declaration'):
        with monkeypatch.context() as patch:
            original=SyntheticSolarRights.__call__;calls=[]
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
            patch.setattr(SyntheticSolarRights,'__call__',changed)
            old_bytes=(p[0]/'source.json').read_bytes()
            with pytest.raises((model.SolarFarmBindingHold,PermissionError)):current(setup,raw,write=True)
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
            with pytest.raises(model.SolarFarmBindingHold):current(setup,raw)
        checked.append(name)
    for value in (1,'true',None,{},False):
        with monkeypatch.context() as patch:
            patch.setattr(SyntheticSolarRights,'__call__',lambda *a:value)
            with pytest.raises(model.SolarFarmBindingHold):current(setup,raw)
    with pytest.raises(model.SolarFarmBindingHold):current(setup,raw,write=1)
    import test_crop_greenhouse_ventilation_input_evidence as legacy
    with pytest.raises(model.SolarFarmBindingHold):
        model.SolarFarmBinding(service.farms,legacy.authority(p[3]),input_rights=rights)
    save('runtime-fixed.json',{'configuration_cases':checked,'non_true_answers_rejected':5,'bool_write_required':True})


def test_authenticated_utc_outside_actual_crop_period(authoring,tmp_path,profiles,monkeypatch):
    value=build(authoring,tmp_path/'outside',profiles,origin=inputs.reference.origin('2026-01-01T00:00:00Z'))
    edge=build(authoring,tmp_path/'microsecond-edge',profiles,origin=inputs.reference.origin('2026-10-24T23:59:28.000001Z'))
    before=counts(value[0]);calls=forbid(monkeypatch)
    with pytest.raises(model.SolarFarmBindingHold):prepare(value)
    assert edge[2][2].manifest['end_utc']=='2026-10-25T00:00:00.000001Z'
    with pytest.raises(model.SolarFarmBindingHold):prepare(edge)
    assert counts(value[0])==before and all(n==0 for n in calls.values())
    save('outside-period.json',{'authenticated_time_origin':'2026-01-01T00:00:00Z','actual_occupancy_rejected':True,
        'authenticated_end_one_microsecond_outside':edge[2][2].manifest['end_utc'],'counts_unchanged':True})



def test_source_availability_at_decision_and_one_microsecond_after(authoring,tmp_path,profiles,monkeypatch):
    values=[build(authoring,tmp_path/name,profiles,available_at=stamp) for name,stamp in (
        ('before','2026-09-27T23:59:59.999999Z'),('exact','2026-09-28T00:00:00Z'),
        ('after','2026-09-28T00:00:00.000001Z'))]
    before=counts(values[0][0]);calls=forbid(monkeypatch)
    for value in values[:2]:
        raw=prepare(value);assert current(value,raw)==raw
        assert json.loads(raw)['input']['provenance']['available_at']==json.loads(
            (value[2][0]/'source.json').read_bytes())['provenance']['available_at']
    with pytest.raises(model.SolarFarmBindingHold):prepare(values[2])
    assert counts(values[0][0])==before and all(n==0 for n in calls.values())
    save('availability.json',{'decision_at':authoring[1]['farm']['decision_at'],'before_and_exact_accepted':True,
        'source_one_microsecond_after_decision_rejected':True,'late_retrieval_not_confused_with_availability':True,
        'counts_unchanged':True,'calls':calls})


def test_actual_database_registration_and_grant_changes_are_current(setup,login_scope):
    service,body,*_=setup;raw=prepare(setup);before=counts(service);base,policy,_=login_scope
    row=service.farms._find('tenant-1',body['farm']['scenario_id'],body['farm']['scenario_revision'])
    with pytest.raises(psycopg.errors.RaiseException,match='job identity is immutable'):
        with base.connect() as conn:
            conn.execute(sql.SQL('UPDATE {} SET input_bytes=%s WHERE job_id=%s').format(service.jobs._table('jobs')),
                (row['input_bytes']+b' ',row['job_id']))
    with pytest.raises(psycopg.errors.CheckViolation,match='jobs_input_digest_matches'):
        with base.connect() as conn:
            conn.execute("SET LOCAL session_replication_role='replica'")
            conn.execute(sql.SQL('UPDATE {} SET input_bytes=%s WHERE job_id=%s').format(service.jobs._table('jobs')),
                (row['input_bytes']+b' ',row['job_id']))
    with base.connect() as conn:
        conn.execute("SET LOCAL session_replication_role='replica'")
        conn.execute(sql.SQL('UPDATE {} SET input_bytes=%s,input_sha256=%s WHERE job_id=%s').format(service.jobs._table('jobs')),
            (row['input_bytes']+b' ',sha256(row['input_bytes']+b' ').hexdigest(),row['job_id']))
    try:
        with pytest.raises(model.SolarFarmBindingHold):current(setup,raw)
    finally:
        with base.connect() as conn:
            conn.execute("SET LOCAL session_replication_role='replica'")
            conn.execute(sql.SQL('UPDATE {} SET input_bytes=%s,input_sha256=%s WHERE job_id=%s').format(service.jobs._table('jobs')),
                (row['input_bytes'],row['input_sha256'],row['job_id']))
    assert current(setup,raw)==raw
    target=service.jobs._table('jobs');role=sql.Identifier(policy.roles['authority'])
    with base.connect() as conn:conn.execute(sql.SQL('GRANT DELETE ON {} TO {}').format(target,role))
    try:
        with pytest.raises(model.SolarFarmBindingHold):current(setup,raw)
    finally:
        with base.connect() as conn:conn.execute(sql.SQL('REVOKE DELETE ON {} FROM {}').format(target,role))
    assert current(setup,raw)==raw and counts(service)==before
    save('actual-database-current.json',{'immutable_trigger_rejected_update':True,
        'digest_constraint_rejected_bytes_only_change':True,
        'rehashed_corruption_injected_only_by_scratch_fixture_admin':True,'stored_registration_tamper_rejected':True,
        'actual_unexpected_grant_rejected':True,'restored_binding_bytes_identical':True,'counts_unchanged':True})
