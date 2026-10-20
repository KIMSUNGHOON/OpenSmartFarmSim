"""Exact piecewise-program continuation, fresh restore and rejected checkpoints."""
from copy import deepcopy
from dataclasses import replace
from hashlib import sha256
from importlib import import_module
import json
import os
from pathlib import Path
import subprocess
import sys

import pytest
import test_crop_greenhouse_co2_program as reference

ROOT=Path(__file__).resolve().parents[2]
CASES=reference.CASES;profiles=reference.profiles
FRESH_PYTHONPATH=os.pathsep.join((str(ROOT/'backend'),str(ROOT/'backend/tests')))


@pytest.fixture(scope='module')
def model():return import_module('app.crop_greenhouse_co2_continuation')


def context(model,profiles,case=None):
    c=reference.BY_ID['weather-multiple'] if case is None else case
    return model.prepare_context(**{k:c[k] for k in ('scenario','forcing_program','events','output_steps','step_seconds','step_count')},**profiles)


def collect(model,ctx,budget,restore=True):
    cp=model.start(ctx);samples=[];events=[];chunks=[];out=model._hash([]);ev=model._hash([])
    while True:
        if restore:cp=model.restore_checkpoint(ctx,model.checkpoint_bytes(ctx,cp),expected_sha256=cp.sha256)
        r=model.advance_chunk(ctx,cp,budget);assert r['status'] in ('yielded','completed'),r['hold']
        assert r['output_start']==len(samples) and r['event_start']==len(events)
        for s in r['samples']:out=model._prefix(out,s)
        for e in r['events']:ev=model._prefix(ev,e)
        samples.extend(r['samples']);events.extend(r['events']);chunks.append(r);cp=r['checkpoint']
        assert cp.value['output_prefix_sha256']==out and cp.value['event_prefix_sha256']==ev
        assert len(chunks)<=ctx.program['step_count']+1
        if r['status']=='completed':return dict(samples=samples,events=events,last_confirmed=r['last_confirmed'],checkpoint=cp,chunks=chunks)


@pytest.fixture(scope='module')
def baselines(model,profiles):
    rows={}
    for c in CASES:
        ctx=context(model,profiles,c);one=collect(model,ctx,128);expected=reference.run(model.driver,profiles,c)
        for k in ('samples','events','last_confirmed'):assert one[k]==expected[k]
        rows[c['case_id']]=(ctx,one)
    return rows


@pytest.mark.parametrize('case',CASES,ids=lambda c:c['case_id'])
@pytest.mark.parametrize('budget',(1,2,3,7,128))
def test_all_programs_and_chunk_groupings_are_exact(model,profiles,baselines,case,budget):
    ctx,one=baselines[case['case_id']];r=collect(model,ctx,budget)
    for k in ('samples','events','last_confirmed','checkpoint'):assert r[k]==one[k]
    assert model.checkpoint_bytes(ctx,r['checkpoint'])==model.checkpoint_bytes(ctx,one['checkpoint'])
    assert sum(c['confirmed_numerical_coupled_evaluations'] for c in r['chunks'])==5*16+2*len(case['events'])+len(case['forcing_program'])-1


def test_mixed_budgets_immutability_retry_and_initial_cursors(model,profiles,baselines):
    case=deepcopy(reference.BY_ID['weather-multiple']);saved=deepcopy(case);ctx=context(model,profiles,case);cp=model.start(ctx)
    assert cp.value['next_index']==0 and cp.value['forcing_cursor']==1 and cp.value['event_cursor']==cp.value['output_cursor']==0
    raw=model.checkpoint_bytes(ctx,cp);a=model.advance_chunk(ctx,cp,1);assert a==model.advance_chunk(ctx,cp,1)
    assert model.checkpoint_bytes(ctx,cp)==raw and case==saved
    copy=ctx.program;copy['scenario']['plant_state']['leaf']['value']=0
    value=cp.value;value['forcing_cursor']=999
    assert ctx.program['scenario']==saved['scenario'] and cp.value['forcing_cursor']==1
    samples=[];events=[]
    for n in (1,3,4,1,7,1):
        r=model.advance_chunk(ctx,cp,n);assert r['status']!='hold',r['hold']
        samples.extend(r['samples']);events.extend(r['events']);cp=r['checkpoint']
    _,one=baselines['weather-multiple']
    assert r['status']=='completed' and cp==one['checkpoint'] and samples==one['samples'] and events==one['events']


@pytest.mark.parametrize('name',['weather-mid','weather-multiple','weather-no-events'])
@pytest.mark.parametrize('dt',(8,4,2))
def test_accepted_convergence_grids_remain_exact(model,profiles,name,dt):
    c=deepcopy(reference.BY_ID[name]);scale=lambda i:int(i*c['step_seconds']/dt)
    for row in c['events']+c['forcing_program']:row['step_index']=scale(row['step_index'])
    c['output_steps']=[scale(i) for i in c['output_steps']];c['step_count']=scale(c['step_count']);c['step_seconds']=dt
    r=collect(model,context(model,profiles,c),3);old=reference.run(model.driver,profiles,c,dt=dt)
    for k in ('samples','events','last_confirmed'):assert r[k]==old[k]


@pytest.mark.parametrize('boundary',(0,1,4,5,8,9,16,17))
def test_fresh_python_restore_runs_only_remaining_work(model,profiles,baselines,tmp_path,boundary):
    ctx,one=baselines['weather-multiple'];cp=model.start(ctx)
    if boundary:cp=model.advance_chunk(ctx,cp,boundary)['checkpoint']
    original=model.checkpoint_bytes(ctx,cp);raw_path=tmp_path/'checkpoint.json';raw_path.write_bytes(original)
    pack=tmp_path/'resume.json';pack.write_text(json.dumps({'case':reference.BY_ID['weather-multiple'],'digest':cp.sha256,'path':str(raw_path)}))
    script='''import json,sys
from pathlib import Path
import test_crop_greenhouse_co2_continuation as t
from app import crop_greenhouse_co2_continuation as m
p=json.loads(Path(sys.argv[1]).read_bytes());ctx=t.context(m,t.profiles.__wrapped__(),p['case'])
calls={'RHS':0,'step':0,'event':0};old_rhs=m.driver.stage.rhs.evaluate_rhs;old_step=m.driver.stage.integrate;old_event=m.driver.management.apply_management
def rhs(**kw):calls['RHS']+=1;return old_rhs(**kw)
def step(**kw):calls['step']+=1;return old_step(**kw)
def event(**kw):calls['event']+=1;return old_event(**kw)
m.driver.stage.rhs.evaluate_rhs=rhs;m.driver.stage.integrate=step;m.driver.management.apply_management=event
cp=m.restore_checkpoint(ctx,Path(p['path']).read_bytes(),expected_sha256=p['digest']);samples=[];events=[];chunks=0
while cp.value['next_index']<=ctx.program['step_count']:
 r=m.advance_chunk(ctx,cp,3);assert r['status']!='hold',r['hold'];cp=r['checkpoint'];chunks+=1;samples.extend(r['samples']);events.extend(r['events'])
print(json.dumps({'checkpoint':cp.sha256,'samples':m._hash(samples),'events':m._hash(events),'calls':calls,'chunks':chunks}))
'''
    completed=subprocess.run([sys.executable,'-B','-c',script,str(pack)],check=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE,timeout=30,env=dict(os.environ,PYTHONPATH=FRESH_PYTHONPATH))
    found=json.loads(completed.stdout);samples=[s for s in one['samples'] if s['step_index']>=boundary];events=[e for e in one['events'] if e['step_index']>=boundary]
    remaining_steps=16-max(0,boundary-1);changes=sum(row['step_index']>=boundary for row in ctx.program['forcing_program'][1:])
    assert found['checkpoint']==one['checkpoint'].sha256 and found['samples']==model._hash(samples) and found['events']==model._hash(events)
    assert found['calls']['step']==remaining_steps and found['calls']['event']==len(events)
    assert found['calls']['RHS']==1+found['chunks']+5*remaining_steps+2*len(events)+changes
    assert model.checkpoint_bytes(ctx,cp)==original


def test_restore_checks_only_current_endpoint(model,profiles,monkeypatch):
    ctx=context(model,profiles);cp=model.advance_chunk(ctx,model.start(ctx),9)['checkpoint'];calls=[];old=model.driver.stage.rhs.evaluate_rhs
    def record(**kw):calls.append(deepcopy(kw['scenario']));return old(**kw)
    def forbidden(**kw):pytest.fail('restore replayed a step/event')
    monkeypatch.setattr(model.driver.stage.rhs,'evaluate_rhs',record);monkeypatch.setattr(model.driver.stage,'integrate',forbidden);monkeypatch.setattr(model.driver.management,'apply_management',forbidden)
    assert model.restore_checkpoint(ctx,model.checkpoint_bytes(ctx,cp),expected_sha256=cp.sha256)==cp
    assert len(calls)==1 and calls[0]['climate_state']==cp.value['last_confirmed']['climate_state']


@pytest.mark.parametrize('bad',(None,True,0,-1,129,1.0,'1'))
def test_invalid_budgets(model,profiles,bad):
    ctx=context(model,profiles)
    with pytest.raises(model.ContinuationRejected):model.advance_chunk(ctx,model.start(ctx),bad)


@pytest.mark.parametrize('kind',('engine','driver','stage','management','RHS','components','policy','source','notice','profile','environment'))
def test_code_source_profile_policy_environment_identity(model,profiles,monkeypatch,kind):
    ctx=context(model,profiles)
    if kind=='engine':monkeypatch.setattr(model,'CODE_SHA256','0'*64)
    elif kind=='driver':monkeypatch.setattr(model.driver,'CODE_SHA256','0'*64)
    elif kind=='stage':monkeypatch.setattr(model.driver.stage,'CODE_SHA256','0'*64)
    elif kind=='management':monkeypatch.setattr(model.driver.management,'CODE_SHA256','0'*64)
    elif kind=='RHS':monkeypatch.setattr(model.driver.stage.rhs,'CODE_SHA256','0'*64)
    elif kind=='components':monkeypatch.setattr(model.driver.stage.joint,'COMPONENT_CODE_SHA256',{})
    elif kind=='policy':monkeypatch.setattr(model.driver.stage.joint.crop.startup,'POLICY_SHA256','0'*64)
    elif kind=='source':monkeypatch.setattr(model.driver.stage.rhs.gas,'SOURCE_SHA256','0'*64)
    elif kind=='notice':monkeypatch.setattr(model.driver.stage.rhs.solar_rhs.nir,'NOTICE_SHA256','0'*64)
    elif kind=='profile':ctx=replace(ctx,_profiles=(None,*ctx._profiles[1:]))
    else:monkeypatch.setattr(model.transport.platform,'python_version',lambda:'changed')
    with pytest.raises(model.ContinuationRejected,match='CONTEXT_HOLD'):model.start(ctx)


@pytest.mark.parametrize('mutation',('extra','version','context','index-bool','index-high','output','event','forcing','forcing-bool','active','phase','elapsed','ppm','co2-unit','co2-domain','state-int','ledger-bool','ledger-unit','balance','prefix'))
def test_checkpoint_structure_current_state_ledgers_and_forcing(model,profiles,mutation):
    ctx=context(model,profiles);cp=model.advance_chunk(ctx,model.start(ctx),8)['checkpoint'];v=cp.value;s=v['last_confirmed']
    if mutation=='extra':v['extra']=1
    elif mutation=='version':v['version']='old108'
    elif mutation=='context':v['context_sha256']='0'*64
    elif mutation=='index-bool':v['next_index']=True
    elif mutation=='index-high':v['next_index']=18
    elif mutation=='output':v['output_cursor']+=1
    elif mutation=='event':v['event_cursor']+=1
    elif mutation=='forcing':v['forcing_cursor']+=1
    elif mutation=='forcing-bool':v['forcing_cursor']=True
    elif mutation=='active':s['forcing_step_index']=0
    elif mutation=='phase':s['phase']='forcing-boundary'
    elif mutation=='elapsed':s['elapsed_seconds']+=1
    elif mutation=='ppm':s['derived']['crop_co2_ppm']['value']+=1
    elif mutation=='co2-unit':s['climate_state']['air_co2_mass']['unit']='mg_CH2O/m2_floor'
    elif mutation=='co2-domain':s['climate_state']['air_co2_mass']['value']=-1.0
    elif mutation=='state-int':s['climate_state']['air_co2_mass']['value']=int(s['climate_state']['air_co2_mass']['value'])
    elif mutation=='ledger-bool':s['event_totals']['leaf']['value']=True
    elif mutation=='ledger-unit':s['integrated_transfers']['co2_crop_to_air']['unit']='mg_CH2O/m2_floor'
    elif mutation=='balance':s['integrated_transfers']['co2_external_to_air']['value']+=1
    else:v['output_prefix_sha256']='bad'
    raw=model._canonical(v)
    with pytest.raises(model.ContinuationRejected):model.restore_checkpoint(ctx,raw,expected_sha256=sha256(raw).hexdigest())


@pytest.mark.parametrize('raw',(b'{}',b'\xff',b'[]',b'{"x":1,"x":2}',b'{"x":NaN}',b'{"x":Infinity}',b' '*65537))
def test_external_json_rejected(model,profiles,raw):
    ctx=context(model,profiles)
    with pytest.raises(model.ContinuationRejected):model.restore_checkpoint(ctx,raw,expected_sha256=sha256(raw).hexdigest())


def test_digest_context_frozen_bytes_and_completed_limits(model,profiles,baselines,monkeypatch):
    ctx,one=baselines['weather-multiple'];cp=model.start(ctx);raw=model.checkpoint_bytes(ctx,cp)
    for digest in (None,False,'','x'*64,'0'*64):
        with pytest.raises(model.ContinuationRejected):model.restore_checkpoint(ctx,raw,expected_sha256=digest)
    v=cp.value;v['output_prefix_sha256']='0'*64;altered=model._canonical(v)
    with pytest.raises(model.ContinuationRejected):model.restore_checkpoint(ctx,altered,expected_sha256=cp.sha256)
    with pytest.raises(model.ContinuationRejected):model.checkpoint_bytes(ctx,replace(cp,_raw=b'{}'))
    changed=deepcopy(reference.BY_ID['weather-multiple']);changed['forcing_program'][1]['co2']['forcing']['external_co2_flux']['value']+=1
    other=context(model,profiles,changed)
    with pytest.raises(model.ContinuationRejected):model.restore_checkpoint(other,raw,expected_sha256=cp.sha256)
    with pytest.raises(model.ContinuationRejected):model.advance_chunk(other,cp,1)
    with pytest.raises(model.ContinuationRejected,match='COMPLETED_HOLD'):model.advance_chunk(ctx,one['checkpoint'],1)
    pretty=json.dumps(cp.value,indent=2).encode()
    with pytest.raises(model.ContinuationRejected):model.restore_checkpoint(ctx,pretty,expected_sha256=sha256(pretty).hexdigest())
    monkeypatch.setattr(model,'MAX_CHECKPOINT_BYTES',1)
    with pytest.raises(model.ContinuationRejected):model.start(ctx)
    monkeypatch.setattr(model,'MAX_CONTEXT_BYTES',1)
    with pytest.raises(model.ContinuationRejected):context(model,profiles)


@pytest.mark.parametrize('failure',('forcing','event','depletion','step-balance','event-balance'))
def test_real_and_injected_holds_match_original_prefix(model,profiles,monkeypatch,failure):
    c=deepcopy(reference.BY_ID['weather-multiple'])
    if failure=='forcing':c['forcing_program'][2]['solar']['values']['outdoor_global_radiation']['value']=-1
    elif failure=='event':c['events'][1]['event']['values']['leaf']['value']=1e15
    elif failure=='depletion':c['forcing_program'][0]['co2']['forcing']['external_co2_flux']['value']=-10000
    elif failure=='step-balance':
        old=model.driver.stage.integrate
        def corrupt(**kw):
            r=old(**kw);r['integrated_transfers']['photosynthesis']['value']+=1;return r
        monkeypatch.setattr(model.driver.stage,'integrate',corrupt)
    else:
        old=model.driver.management.apply_management
        def corrupt(**kw):
            r=old(**kw);r['removed']['canopy_sensible_energy']['value']+=1;return r
        monkeypatch.setattr(model.driver.management,'apply_management',corrupt)
    ctx=context(model,profiles,c);cp=model.start(ctx);raw=model.checkpoint_bytes(ctx,cp);r=model.advance_chunk(ctx,cp,128)
    with pytest.raises(model.driver.ProgramHold) as held:reference.run(model.driver,profiles,c)
    assert r['status']=='hold' and r['checkpoint'] is None and r['hold']['phase']==held.value.failed_phase
    assert r['last_confirmed']==held.value.last_confirmed and r['samples']==held.value.samples and r['events']==held.value.events
    assert model.checkpoint_bytes(ctx,cp)==raw


def test_late_hold_and_crash_preserve_incoming_checkpoint(model,profiles,monkeypatch):
    c=deepcopy(reference.BY_ID['weather-multiple']);c['events'][-1]['event']['values']['leaf']['value']=1e15
    ctx=context(model,profiles,c);cp=model.advance_chunk(ctx,model.start(ctx),16)['checkpoint'];raw=model.checkpoint_bytes(ctx,cp)
    r=model.advance_chunk(ctx,cp,1);assert r['status']=='hold' and r['last_confirmed']['phase']=='forcing-boundary' and r['last_confirmed']['forcing_step_index']==16
    assert r['samples']==r['events']==[] and model.checkpoint_bytes(ctx,cp)==raw
    def crash(**kw):raise KeyboardInterrupt('synthetic cancellation')
    monkeypatch.setattr(model.driver.stage,'integrate',crash)
    with pytest.raises(KeyboardInterrupt):model.advance_chunk(ctx,cp,1)
    assert model.checkpoint_bytes(ctx,cp)==raw


def test_maximum_forcing_outputs_events_and_byte_limits(model,profiles):
    c=deepcopy(reference.BY_ID['no-events']);c.update(step_seconds=.0625,step_count=512,output_steps=[*range(511),512],events=[])
    force=c['forcing_program'][0];c['forcing_program']=[{**deepcopy(force),'step_index':i} for i in c['output_steps']]
    source=reference.BY_ID['multiple']['events'][0]['event']
    for i in range(128):
        e=deepcopy(source);e['input_id']='co2-max-cont-'+str(i);e['values']['leaf']['value']=e['values']['stem_root']['value']=0
        for q in e['values']['fruit_fraction']:q['value']=0
        c['events'].append({'step_index':i,'event':e})
    ctx=context(model,profiles,c);r=collect(model,ctx,128)
    assert len(r['samples'])==512 and len(r['events'])==128 and len(r['chunks'])==5
    assert r['checkpoint'].value['forcing_cursor']==512 and r['checkpoint'].value['output_cursor']==512 and r['checkpoint'].value['event_cursor']==128
    assert len(ctx._program)+len(ctx._manifest)+len(ctx._first)<=2*1024**2
    assert all(len(model.checkpoint_bytes(ctx,c['checkpoint']))<=65536 for c in r['chunks'])
