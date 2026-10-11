"""Same-grid ventilation resume and trusted checkpoint transport."""
from copy import deepcopy
from dataclasses import replace
from hashlib import sha256
import json
import os
from pathlib import Path
import subprocess
import sys

import pytest

from app import crop_greenhouse_ventilation_continuation as model
import test_crop_greenhouse_ventilation_program as reference
import test_crop_climate_joint_boundary as legacy_reference

ROOT=Path(__file__).resolve().parents[2]
FRESH_PYTHONPATH=os.pathsep.join((str(Path(__file__).resolve().parents[1]),str(Path(__file__).resolve().parent)))
CASES=reference.CASES
profiles=reference.profiles


def context(profiles,case=None):
    case=CASES[6] if case is None else case
    return model.prepare_context(scenario=case['scenario'],ventilation=case['ventilation'],events=case['events'],output_steps=case['output_steps'],
        step_seconds=case['step_seconds'],step_count=case['step_count'],**profiles)


def collect(ctx,budget,restore=False):
    cp=model.start(ctx);samples=[];events=[];chunks=[]
    while True:
        if restore:cp=model.restore_checkpoint(ctx,model.checkpoint_bytes(ctx,cp),expected_sha256=cp.sha256)
        r=model.advance_chunk(ctx,cp,budget);assert r['status']!='hold',r['hold']
        samples.extend(r['samples']);events.extend(r['events']);chunks.append(r);cp=r['checkpoint']
        if r['status']=='completed':return {'samples':samples,'events':events,'last_confirmed':r['last_confirmed'],'checkpoint':cp,'chunks':chunks}


def test_smoke_chunked_initial_mid_final_events_match_original_driver_exactly(profiles):
    ctx=context(profiles);r=collect(ctx,3,True);old=reference.run(profiles,CASES[6])
    for k in ('samples','events','last_confirmed'):assert r[k]==old[k]
    assert r['checkpoint'].value['next_index']==17 and [x['step_index'] for x in r['events']]==[0,8,16]


def test_smoke_all_chunk_groupings_have_identical_checkpoint_bytes(profiles):
    ctx=context(profiles);a=collect(ctx,1);b=collect(ctx,128)
    assert model.checkpoint_bytes(ctx,a['checkpoint'])==model.checkpoint_bytes(ctx,b['checkpoint'])


def test_mixed_chunk_budgets_preserve_the_same_final_bytes_and_prefix(profiles):
    ctx=context(profiles);cp=model.start(ctx);samples=[];events=[]
    for budget in (1,7,1,2,1,5):
        cp=model.restore_checkpoint(ctx,model.checkpoint_bytes(ctx,cp),expected_sha256=cp.sha256)
        r=model.advance_chunk(ctx,cp,budget);samples.extend(r['samples']);events.extend(r['events']);cp=r['checkpoint']
    whole=collect(ctx,128)
    assert r['status']=='completed' and cp==whole['checkpoint'] and samples==whole['samples'] and events==whole['events']


@pytest.mark.parametrize('index',(1,2,3))
@pytest.mark.parametrize('dt',(8,4,2))
def test_previously_accepted_step_halving_grids_are_preserved_exactly(profiles,index,dt):
    case=deepcopy(CASES[index]);scale=lambda i:int(i*case['step_seconds']/dt)
    case['events']=[{**row,'step_index':scale(row['step_index'])} for row in case['events']]
    case['output_steps']=[scale(i) for i in case['output_steps']];case['step_count']=scale(case['step_count']);case['step_seconds']=dt
    r=collect(context(profiles,case),3,True);old=reference.run(profiles,case,dt)
    for k in ('samples','events','last_confirmed'):assert r[k]==old[k]


def test_smoke_initial_ready_t0_commit_are_distinct(profiles):
    ctx=context(profiles);cp=model.start(ctx);r=model.advance_chunk(ctx,cp,1)
    assert cp.value['next_index']==0 and cp.value['event_cursor']==cp.value['output_cursor']==0
    assert r['checkpoint'].value['next_index']==1 and r['checkpoint'].value['event_cursor']==r['checkpoint'].value['output_cursor']==1
    assert r['last_confirmed']['elapsed_seconds']==0 and r['last_confirmed']['phase']=='boundary-after-event'


def test_smoke_properties_and_inputs_are_immutable_copies(profiles):
    case=deepcopy(CASES[6]);saved=deepcopy(case);ctx=context(profiles,case);cp=model.start(ctx)
    case['scenario']['plant_state']['leaf']['value']=0
    program=ctx.program;program['scenario']['plant_state']['leaf']['value']=0
    value=cp.value;value['next_index']=999
    assert ctx.program['scenario']==saved['scenario'] and cp.value['next_index']==0


@pytest.mark.parametrize('index',range(10))
@pytest.mark.parametrize('budget',(1,2,3,7,128))
def test_every_original_program_and_chunk_grouping_is_exact(profiles,index,budget):
    case=CASES[index];ctx=context(profiles,case);result=collect(ctx,budget,True);expected=reference.run(profiles,case)
    for k in ('samples','events','last_confirmed'):assert result[k]==expected[k]
    one=collect(ctx,128)
    assert result['checkpoint'].sha256==one['checkpoint'].sha256
    assert model.checkpoint_bytes(ctx,result['checkpoint'])==model.checkpoint_bytes(ctx,one['checkpoint'])
    outputs=events=0
    for chunk in result['chunks']:
        assert chunk['output_start']==outputs and chunk['event_start']==events
        outputs+=len(chunk['samples']);events+=len(chunk['events'])
        assert len(chunk['samples'])<=budget and len(chunk['events'])<=budget
        assert chunk['scope']=='software_research_only' and chunk['G0_G4']=='not_assessed'


@pytest.mark.parametrize('boundary',(0,1,8,9,17))
def test_fresh_python_restore_preserves_pending_and_committed_event_positions(profiles,tmp_path,boundary):
    ctx=context(profiles);cp=model.start(ctx)
    if boundary:cp=model.advance_chunk(ctx,cp,boundary)['checkpoint']
    original_raw=model.checkpoint_bytes(ctx,cp);target=collect(ctx,128)
    pack=tmp_path/'resume.json';raw_path=tmp_path/'checkpoint.json';raw_path.write_bytes(original_raw)
    pack.write_text(json.dumps({'case':CASES[6],'digest':cp.sha256,'checkpoint':str(raw_path)}))
    script='''import json,sys
from pathlib import Path
import test_crop_greenhouse_ventilation_continuation as t
from app import crop_greenhouse_ventilation_continuation as m
p=json.loads(Path(sys.argv[1]).read_bytes());ctx=t.context(t.profiles.__wrapped__(),p['case'])
calls={'RHS':0,'step':0,'event':0};old_rhs=m.driver.stage.joint.evaluate_rhs;old_step=m.driver.stage.integrate;old_event=m.driver.previous.management.apply_management
def rhs(**kw):calls['RHS']+=1;return old_rhs(**kw)
def step(**kw):calls['step']+=1;return old_step(**kw)
def event(**kw):calls['event']+=1;return old_event(**kw)
m.driver.stage.joint.evaluate_rhs=rhs;m.driver.stage.integrate=step;m.driver.previous.management.apply_management=event
cp=m.restore_checkpoint(ctx,Path(p['checkpoint']).read_bytes(),expected_sha256=p['digest']);samples=[];events=[];chunks=0
while cp.value['next_index']<=ctx.program['step_count']:
 r=m.advance_chunk(ctx,cp,3);assert r['status']!='hold',r['hold'];cp=r['checkpoint'];chunks+=1;samples.extend(r['samples']);events.extend(r['events'])
print(json.dumps({'checkpoint_sha256':cp.sha256,'samples_sha256':m._hash(samples),'events_sha256':m._hash(events),'calls':calls,'chunks':chunks}))
'''
    completed=subprocess.run([sys.executable,'-B','-c',script,str(pack)],check=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE,timeout=20,
        env=dict(os.environ,PYTHONPATH=FRESH_PYTHONPATH))
    found=json.loads(completed.stdout);remaining_samples=[s for s in target['samples'] if s['step_index']>=boundary]
    remaining_events=[e for e in target['events'] if e['step_index']>=boundary]
    assert found['checkpoint_sha256']==target['checkpoint'].sha256
    assert found['samples_sha256']==model._hash(remaining_samples) and found['events_sha256']==model._hash(remaining_events)
    remaining_steps=16-max(0,boundary-1)
    assert found['calls']['step']==remaining_steps and found['calls']['event']==len(remaining_events)
    assert found['calls']['RHS']==1+found['chunks']+6*remaining_steps+3*len(remaining_events)
    assert model.checkpoint_bytes(ctx,cp)==original_raw


def test_same_checkpoint_retry_is_deterministic_and_does_not_mutate_inputs(profiles):
    ctx=context(profiles);cp=model.start(ctx);raw=model.checkpoint_bytes(ctx,cp)
    a=model.advance_chunk(ctx,cp,9);b=model.advance_chunk(ctx,cp,9)
    assert a==b and model.checkpoint_bytes(ctx,cp)==raw
    a['last_confirmed']['plant_state']['leaf']['value']=0
    a['manifest']['identity']['engine_version']='changed'
    assert model.advance_chunk(ctx,cp,9)==b


def test_restoring_checks_only_the_current_endpoint_not_the_prefix(profiles,monkeypatch):
    ctx=context(profiles);cp=model.advance_chunk(ctx,model.start(ctx),9)['checkpoint'];calls=[]
    rhs=model.driver.stage.joint.evaluate_rhs
    def record(**kw):calls.append(deepcopy(kw['scenario']));return rhs(**kw)
    def forbidden(**kw):pytest.fail('restore replayed a numerical step or management event')
    monkeypatch.setattr(model.driver.stage.joint,'evaluate_rhs',record)
    monkeypatch.setattr(model.driver.stage,'integrate',forbidden);monkeypatch.setattr(model.driver.previous.management,'apply_management',forbidden)
    restored=model.restore_checkpoint(ctx,model.checkpoint_bytes(ctx,cp),expected_sha256=cp.sha256)
    assert restored==cp and len(calls)==1
    assert calls[0]['plant_state']==cp.value['last_confirmed']['plant_state']
    assert calls[0]['plant_state']!=ctx.program['scenario']['plant_state']


@pytest.mark.parametrize('bad',(None,True,0,-1,129,1.0,'1',10**400))
def test_invalid_boundary_budgets_reject_before_current_rhs(profiles,monkeypatch,bad):
    ctx=context(profiles);cp=model.start(ctx)
    def forbidden(**kw):pytest.fail('invalid budget reached RHS')
    monkeypatch.setattr(model.driver.stage.joint,'evaluate_rhs',forbidden)
    with pytest.raises(model.ContinuationRejected,match='BUDGET_HOLD'):model.advance_chunk(ctx,cp,bad)


@pytest.mark.parametrize('field',('_program','_manifest','_first','root_sha256','_profiles','_token'))
def test_changed_context_fields_reject(profiles,field):
    ctx=context(profiles)
    value={'_program':b'{}','_manifest':b'{}','_first':b'{}','root_sha256':'0'*64,'_profiles':(None,)*4,'_token':None}[field]
    with pytest.raises(model.ContinuationRejected,match='CONTEXT_HOLD'):model.start(replace(ctx,**{field:value}))


@pytest.mark.parametrize('kind',('engine','driver','short','management','RHS','component','policy','environment'))
def test_current_code_policy_or_environment_change_rejects_context(profiles,monkeypatch,kind):
    ctx=context(profiles)
    if kind=='engine':monkeypatch.setattr(model,'CODE_SHA256','0'*64)
    elif kind=='driver':monkeypatch.setattr(model.driver,'CODE_SHA256','0'*64)
    elif kind=='short':monkeypatch.setattr(model.driver.stage,'CODE_SHA256','0'*64)
    elif kind=='management':monkeypatch.setattr(model.driver.previous.management,'CODE_SHA256','0'*64)
    elif kind=='RHS':monkeypatch.setattr(model.driver.stage.joint,'CODE_SHA256','0'*64)
    elif kind=='component':monkeypatch.setattr(model.driver.stage.joint,'COMPONENT_CODE_SHA256',{})
    elif kind=='policy':monkeypatch.setattr(model.driver.stage.joint.crop.startup,'POLICY_SHA256','0'*64)
    elif kind=='environment':monkeypatch.setattr(model.transport.platform,'python_version',lambda:'changed')
    with pytest.raises(model.ContinuationRejected,match='CONTEXT_HOLD'):model.start(ctx)


def test_changed_program_cannot_restore_or_advance_another_context_checkpoint(profiles):
    a=context(profiles);case=deepcopy(CASES[6]);case['scenario']['forcing']['canopy_external_heat']['value']+=1;b=context(profiles,case)
    cp=model.start(a);raw=model.checkpoint_bytes(a,cp)
    with pytest.raises(model.ContinuationRejected,match='CHECKPOINT_HOLD'):model.restore_checkpoint(b,raw,expected_sha256=cp.sha256)
    with pytest.raises(model.ContinuationRejected,match='CHECKPOINT_HOLD'):model.advance_chunk(b,cp,1)


@pytest.mark.parametrize('bad',(None,False,'','0'*64,'x'*64))
def test_trusted_expected_digest_is_required_before_rhs(profiles,monkeypatch,bad):
    ctx=context(profiles);raw=model.checkpoint_bytes(ctx,model.start(ctx))
    def forbidden(**kw):pytest.fail('invalid expected digest reached RHS')
    monkeypatch.setattr(model.driver.stage.joint,'evaluate_rhs',forbidden)
    with pytest.raises(model.ContinuationRejected):model.restore_checkpoint(ctx,raw,expected_sha256=bad)


def test_changed_and_rehashed_transport_is_rejected_against_trusted_digest(profiles):
    ctx=context(profiles);cp=model.advance_chunk(ctx,model.start(ctx),9)['checkpoint'];changed=cp.value
    changed['output_prefix_sha256']='0'*64;raw=model._canonical(changed);assert sha256(raw).hexdigest()!=cp.sha256
    with pytest.raises(model.ContinuationRejected,match='trusted expected'):model.restore_checkpoint(ctx,raw,expected_sha256=cp.sha256)


@pytest.mark.parametrize('mutation',('extra','missing','version','context','index-bool','index-low','index-high','output','event','cursor-bool',
    'prefix','empty-prefix','phase','elapsed','derived','unit','ledger-bool','ledger-nan','ledger-extra','state-domain','balance','state-extra','initial-seed',
    'state-unit','state-quantity-extra','state-bool','state-int','cohort-unit','cohort-extra','cohort-size','climate-unit'))
def test_structural_current_domain_and_global_ledger_validation(profiles,mutation):
    ctx=context(profiles);cp=model.start(ctx) if mutation in ('empty-prefix','initial-seed') else model.advance_chunk(ctx,model.start(ctx),8)['checkpoint']
    value=cp.value;last=value['last_confirmed']
    if mutation=='extra':value['extra']=1
    elif mutation=='missing':del value['event_cursor']
    elif mutation=='version':value['version']='changed'
    elif mutation=='context':value['context_sha256']='0'*64
    elif mutation=='index-bool':value['next_index']=True
    elif mutation=='index-low':value['next_index']=-1
    elif mutation=='index-high':value['next_index']=18
    elif mutation=='output':value['output_cursor']+=1
    elif mutation=='event':value['event_cursor']+=1
    elif mutation=='cursor-bool':value['event_cursor']=True
    elif mutation=='prefix':value['output_prefix_sha256']='bad'
    elif mutation=='empty-prefix':value['event_prefix_sha256']='0'*64
    elif mutation=='phase':last['phase']='boundary-after-event'
    elif mutation=='elapsed':last['elapsed_seconds']+=1
    elif mutation=='derived':last['derived']['canopy_temperature']['value']+=1
    elif mutation=='unit':last['integrated_transfers']['photosynthesis']['unit']='g'
    elif mutation=='ledger-bool':last['event_totals']['leaf']['value']=True
    elif mutation=='ledger-nan':last['event_totals']['leaf']['value']=float('nan')
    elif mutation=='ledger-extra':last['event_totals']['extra']={'value':0.0,'unit':'1'}
    elif mutation=='state-domain':last['plant_state']['leaf']['value']=0
    elif mutation=='balance':last['integrated_transfers']['photosynthesis']['value']+=1
    elif mutation=='state-extra':last['plant_state']['extra']={'value':0.0,'unit':'1'}
    elif mutation=='initial-seed':last['plant_state']['leaf']['value']+=1
    elif mutation=='state-unit':last['plant_state']['leaf']['unit']='g'
    elif mutation=='state-quantity-extra':last['plant_state']['leaf']['extra']=1
    elif mutation=='state-bool':last['plant_state']['leaf']['value']=True
    elif mutation=='state-int':last['plant_state']['leaf']['value']=int(last['plant_state']['leaf']['value'])
    elif mutation=='cohort-unit':next(iter(last['cohort_state'].values()))[0]['unit']='g'
    elif mutation=='cohort-extra':last['cohort_state']['extra']=[]
    elif mutation=='cohort-size':next(iter(last['cohort_state'].values())).pop()
    elif mutation=='climate-unit':last['climate_state']['air_temperature']['unit']='K'
    raw=json.dumps(value,sort_keys=True,separators=(',',':')).encode()
    with pytest.raises(model.ContinuationRejected):model.restore_checkpoint(ctx,raw,expected_sha256=sha256(raw).hexdigest())


@pytest.mark.parametrize('raw',(b'{}',b'\xff',b'[]',b'{"x":1,"x":2}',b'{"x":NaN}',b'{"x":Infinity}',b' '*65537))
def test_invalid_external_json_rejects(profiles,raw):
    ctx=context(profiles)
    with pytest.raises(model.ContinuationRejected):model.restore_checkpoint(ctx,raw,expected_sha256=sha256(raw).hexdigest())


def test_noncanonical_bytes_and_mutated_frozen_checkpoint_reject(profiles):
    ctx=context(profiles);cp=model.start(ctx);raw=json.dumps(cp.value,indent=2).encode()
    with pytest.raises(model.ContinuationRejected,match='canonical'):model.restore_checkpoint(ctx,raw,expected_sha256=sha256(raw).hexdigest())
    with pytest.raises(model.ContinuationRejected):model.checkpoint_bytes(ctx,replace(cp,_raw=b'{}'))


def test_context_checkpoint_and_completed_limits(profiles,monkeypatch):
    ctx=context(profiles);final=collect(ctx,128)['checkpoint']
    with pytest.raises(model.ContinuationRejected,match='COMPLETED_HOLD'):model.advance_chunk(ctx,final,1)
    monkeypatch.setattr(model,'MAX_CHECKPOINT_BYTES',1)
    with pytest.raises(model.ContinuationRejected,match='RESOURCE_HOLD'):model.start(ctx)
    monkeypatch.setattr(model,'MAX_CONTEXT_BYTES',1)
    with pytest.raises(model.ContinuationRejected,match='RESOURCE_HOLD'):context(profiles)


@pytest.mark.parametrize('bad',('profile','event','output','step'))
def test_prepare_reuses_original_closed_input_validation(profiles,bad):
    case=deepcopy(CASES[6]);p=dict(profiles)
    if bad=='profile':p['exchange_profile']=None
    elif bad=='event':case['events'][0]['event']['values']['leaf']['unit']='g'
    elif bad=='output':case['output_steps']=[0,1,1,16]
    elif bad=='step':case['step_seconds']=True
    with pytest.raises(model.ContinuationRejected):context(p,case)


def test_late_real_event_hold_preserves_previous_checkpoint_and_global_prefix(profiles):
    case=deepcopy(CASES[6]);case['events'][-1]['event']['values']['leaf']['value']=50000
    ctx=context(profiles,case);a=model.advance_chunk(ctx,model.start(ctx),8);b=model.advance_chunk(ctx,a['checkpoint'],8)
    cp=b['checkpoint'];raw=model.checkpoint_bytes(ctx,cp);r=model.advance_chunk(ctx,cp,1)
    assert r['status']=='hold' and r['checkpoint'] is None and r['hold']['phase']=='event' and r['hold']['step_index']==16
    assert r['last_confirmed']['step_index']==16 and r['last_confirmed']['event_count']==2 and r['last_confirmed']['phase']=='step-end'
    assert r['samples']==r['events']==[] and model.checkpoint_bytes(ctx,cp)==raw
    with pytest.raises(model.driver.VentilationProgramHold) as held:reference.run(profiles,case)
    assert a['samples']+b['samples']==held.value.samples and a['events']+b['events']==held.value.events
    assert r['last_confirmed']==held.value.last_confirmed and r==model.advance_chunk(ctx,cp,1)


@pytest.mark.parametrize('target',('step','event'))
def test_global_balance_trial_failure_matches_original_confirmed_prefix(profiles,monkeypatch,target):
    ctx=context(profiles);cp=model.start(ctx)
    if target=='step':
        old=model.driver.stage.integrate
        def corrupt(**kw):
            r=old(**kw);r['integrated_transfers']['photosynthesis']['value']+=1;return r
        monkeypatch.setattr(model.driver.stage,'integrate',corrupt)
    else:
        old=model.driver.previous.management.apply_management
        def corrupt(**kw):
            r=old(**kw);r['removed']['canopy_sensible_energy']['value']+=1;return r
        monkeypatch.setattr(model.driver.previous.management,'apply_management',corrupt)
    r=model.advance_chunk(ctx,cp,128)
    assert r['status']=='hold' and r['checkpoint'] is None and r['hold']['phase']=='global-'+target+'-balance'
    with pytest.raises(model.driver.VentilationProgramHold) as held:reference.run(profiles,CASES[6])
    assert r['last_confirmed']==held.value.last_confirmed and r['samples']==held.value.samples and r['events']==held.value.events


@pytest.mark.parametrize('failure',('temperature','underflow'))
def test_actual_stage_domain_or_numeric_hold_is_not_success(profiles,failure):
    case=deepcopy(CASES[0])
    if failure=='temperature':case['scenario']['forcing']['canopy_external_heat']['value']=1e7
    else:case['step_seconds']=1e-200
    ctx=context(profiles,case);r=model.advance_chunk(ctx,model.start(ctx),128)
    assert r['status']=='hold' and r['checkpoint'] is None and r['hold']['phase']=='interval'
    assert r['last_confirmed']['step_index']==0 and len(r['samples'])==1 and r['events']==[]


def test_crash_or_cancel_exception_is_not_a_normal_yield(profiles,monkeypatch):
    ctx=context(profiles);cp=model.advance_chunk(ctx,model.start(ctx),1)['checkpoint']
    def crash(**kw):raise KeyboardInterrupt('synthetic cancellation')
    monkeypatch.setattr(model.driver.stage,'integrate',crash)
    with pytest.raises(KeyboardInterrupt):model.advance_chunk(ctx,cp,1)
    assert cp.value['next_index']==1


def test_maximum_program_chunk_and_checkpoint_cost_bounds(profiles):
    case=deepcopy(CASES[0]);case.update(step_seconds=.0625,step_count=512,output_steps=[*range(511),512],events=[])
    zero=deepcopy(legacy_reference.PREVIOUS['cases'][0]['event'])
    for i in range(128):
        e=deepcopy(zero);e['input_id']=f'synthetic-max-event-{i}';case['events'].append({'step_index':i,'event':e})
    ctx=context(profiles,case);r=collect(ctx,128,True)
    assert len(r['samples'])==512 and len(r['events'])==128 and len(r['chunks'])==5
    assert max(len(c['samples']) for c in r['chunks'])==128 and max(len(c['events']) for c in r['chunks'])==128
    assert all(len(model.checkpoint_bytes(ctx,c['checkpoint']))<=65536 for c in r['chunks'])
    assert len(ctx._program)+len(ctx._manifest)+len(ctx._first)<=model.MAX_CONTEXT_BYTES
    assert r['checkpoint'].value['output_cursor']==512 and r['checkpoint'].value['event_cursor']==128


def test_restore_checks_current_ventilation_once_without_historical_work(profiles,monkeypatch):
    ctx=context(profiles);cp=model.advance_chunk(ctx,model.start(ctx),9)['checkpoint'];calls=[]
    original=model.driver.stage.vent.calculate_ventilation
    def record(**kw):calls.append(deepcopy(kw['scenario']));return original(**kw)
    def forbidden(**kw):pytest.fail('restore integrated a past step or repeated management')
    monkeypatch.setattr(model.driver.stage.vent,'calculate_ventilation',record)
    monkeypatch.setattr(model.driver.stage,'integrate',forbidden)
    monkeypatch.setattr(model.driver.previous.management,'apply_management',forbidden)
    assert model.restore_checkpoint(ctx,model.checkpoint_bytes(ctx,cp),expected_sha256=cp.sha256)==cp
    assert len(calls)==1
    assert calls[0]['state']['air_temperature']==cp.value['last_confirmed']['climate_state']['air_temperature']


@pytest.mark.parametrize('kind',('old-context','old-checkpoint','old-transport'))
def test_original22_ledger_types_and_transport_are_not_new_checkpoints(profiles,kind):
    import test_crop_climate_joint_continuation as old
    ctx=context(profiles);legacy=old.context(profiles);cp=old.model.start(legacy)
    with pytest.raises(model.ContinuationRejected):
        if kind=='old-context':model.start(legacy)
        elif kind=='old-checkpoint':model.advance_chunk(ctx,cp,1)
        else:model.restore_checkpoint(ctx,old.model.checkpoint_bytes(legacy,cp),expected_sha256=cp.sha256)


@pytest.mark.parametrize('kind',('transport-helper','base-driver','base-integration','vent-code','vent-policy','stage-policy'))
def test_additional_ventilation_dependencies_are_pinned(profiles,monkeypatch,kind):
    ctx=context(profiles)
    modules={'transport-helper':model.transport,'base-driver':model.driver.previous,
        'base-integration':model.driver.stage.core,'vent-code':model.driver.stage.vent}
    if kind in modules:monkeypatch.setattr(modules[kind],'CODE_SHA256','0'*64)
    elif kind=='vent-policy':monkeypatch.setattr(model.driver.stage.vent,'POLICY',{})
    else:monkeypatch.setattr(model.driver.stage,'POLICY',{})
    with pytest.raises(model.ContinuationRejected,match='CONTEXT_HOLD'):model.start(ctx)


@pytest.mark.parametrize('kind',('outdoor','flow','input-id','other-forcing'))
def test_changed_source_weather_and_other_forcing_cannot_share_checkpoints(profiles,kind):
    ctx=context(profiles);cp=model.start(ctx);case=deepcopy(CASES[6])
    if kind=='outdoor':case['ventilation']['forcing']['outdoor_air_temperature']['value']+=1
    elif kind=='flow':case['ventilation']['forcing']['volume_exchange_per_floor_area']['value']*=2
    elif kind=='input-id':case['ventilation']['input_id']='different-synthetic-ventilation'
    else:case['scenario']['forcing']['air_external_sensible_heat']['value']+=1
    other=context(profiles,case);assert ctx.root_sha256!=other.root_sha256
    with pytest.raises(model.ContinuationRejected):model.restore_checkpoint(other,model.checkpoint_bytes(ctx,cp),expected_sha256=cp.sha256)


@pytest.mark.parametrize('kind',('ledger-missing','ledger-unit','vent-heat','vent-latent','vent-vapor','diagnostic-input','diagnostic-forcing','diagnostic-derived'))
def test_new25_ledger_partitions_and_current_ventilation_diagnostic_reject_tampering(profiles,kind):
    ctx=context(profiles);cp=model.advance_chunk(ctx,model.start(ctx),8)['checkpoint'];v=cp.value
    last=v['last_confirmed'];ledger=last['integrated_transfers'];diagnostic=last['ventilation']
    if kind=='ledger-missing':del ledger['ventilation_sensible_heat']
    elif kind=='ledger-unit':ledger['ventilation_vapor']['unit']='kg_water'
    elif kind=='vent-heat':ledger['ventilation_sensible_heat']['value']+=1
    elif kind=='vent-latent':ledger['ventilation_latent_energy']['value']+=1
    elif kind=='vent-vapor':ledger['ventilation_vapor']['value']+=.01
    elif kind=='diagnostic-input':diagnostic['input_sha256']='0'*64
    elif kind=='diagnostic-forcing':next(iter(diagnostic['forcing_contribution'].values()))['value']+=1
    else:next(iter(diagnostic['derived'].values()))['value']+=1
    raw=model._canonical(v)
    with pytest.raises(model.ContinuationRejected):model.restore_checkpoint(ctx,raw,expected_sha256=sha256(raw).hexdigest())


def test_failed_post_management_ventilation_keeps_same_time_pre_event_state(profiles,monkeypatch):
    ctx=context(profiles);cp=model.start(ctx);original=model.driver.stage._evaluate
    seed=ctx.program['scenario']['plant_state']['leaf']['value']
    def fail(base,*args,**kwargs):
        if base['plant_state']['leaf']['value']<seed:raise model.driver.stage.vent.VentilationHold('synthetic post-event diagnostic failure')
        return original(base,*args,**kwargs)
    monkeypatch.setattr(model.driver.stage,'_evaluate',fail)
    r=model.advance_chunk(ctx,cp,128)
    assert r['status']=='hold' and r['checkpoint'] is None and r['hold']['phase']=='event-after-ventilation'
    assert r['samples']==r['events']==[] and r['last_confirmed']==cp.value['last_confirmed']
    with pytest.raises(model.driver.VentilationProgramHold) as held:reference.run(profiles,CASES[6])
    assert held.value.last_confirmed==r['last_confirmed'] and held.value.samples==r['samples'] and held.value.events==r['events']


def test_actual_confirmed_joint_and_ventilation_call_counts(profiles,monkeypatch):
    ctx=context(profiles);cp=model.start(ctx);counts={'joint':0,'vent':0}
    rhs=model.driver.stage.joint.evaluate_rhs;vent=model.driver.stage.vent.calculate_ventilation
    def joint(**kw):counts['joint']+=1;return rhs(**kw)
    def boundary(**kw):counts['vent']+=1;return vent(**kw)
    monkeypatch.setattr(model.driver.stage.joint,'evaluate_rhs',joint)
    monkeypatch.setattr(model.driver.stage.vent,'calculate_ventilation',boundary)
    chunks=[]
    while True:
        r=model.advance_chunk(ctx,cp,3);assert r['status']!='hold';chunks.append(r);cp=r['checkpoint']
        if r['status']=='completed':break
    n,e=ctx.program['step_count'],len(ctx.program['events'])
    assert counts=={'joint':len(chunks)+6*n+3*e,'vent':len(chunks)+5*n+e}
    assert sum(r['confirmed_numerical_joint_rhs_evaluations'] for r in chunks)==6*n+3*e
    assert sum(r['confirmed_numerical_ventilation_evaluations'] for r in chunks)==5*n+e
    assert all(r['checkpoint_validation_joint_rhs_evaluations']==r['checkpoint_validation_ventilation_evaluations']==1 for r in chunks)
