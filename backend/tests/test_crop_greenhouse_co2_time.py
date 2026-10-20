"""Exact UTC labels without any current or historical physical calculation."""
from copy import deepcopy
from dataclasses import replace
from datetime import datetime, timezone
from hashlib import sha256
from importlib import import_module
import calendar
import json
import os
from pathlib import Path
import subprocess
import sys

import pytest
from app import crop_greenhouse_co2_continuation as c
import test_crop_greenhouse_co2_continuation as reference

profiles=reference.profiles


@pytest.fixture(scope='module')
def model():return import_module('app.crop_greenhouse_co2_time')


def origin(stamp='2026-10-01T00:00:00Z'):
    return dict(input_id='synthetic-co2-time-origin',origin='synthetic',start_at=stamp,precision='microsecond')


def bind(model,binding,before,chunk):
    return model.bind_chunk(binding,before,chunk,expected_binding_sha256=binding.sha256,
        expected_chunk_sha256=model.source_chunk_sha256(binding._context,chunk))


def forbid_numerics(monkeypatch):
    def forbidden(*args,**kwargs):pytest.fail('UTC binding invoked numerics/advance/restore')
    rhs=c.driver.stage.rhs;solar=rhs.solar_rhs
    for target,name in ((rhs,'evaluate_rhs'),(c.driver.stage.joint,'evaluate_rhs'),(c.driver.stage,'integrate'),
        (solar,'evaluate_rhs'),(solar.vent,'calculate_ventilation'),(solar.par.radiation,'calculate_par'),
        (solar.nir,'calculate_nir'),(rhs.gas,'density_to_ppm'),(rhs.net,'calculate_exchange'),(rhs.air,'evaluate_rhs'),
        (c.driver.management,'apply_management'),(c,'advance_chunk'),(c,'restore_checkpoint')):
        monkeypatch.setattr(target,name,forbidden)


@pytest.mark.parametrize('case',reference.CASES,ids=lambda x:x['case_id'])
@pytest.mark.parametrize('budget',(1,7,128))
def test_all_programs_keep_exact_source_prefixes_with_zero_numerics(model,profiles,monkeypatch,case,budget):
    ctx=reference.context(c,profiles,case);cp=c.start(ctx);pairs=[]
    while cp.value['next_index']<=ctx.program['step_count']:
        chunk=c.advance_chunk(ctx,cp,budget);assert chunk['status']!='hold',chunk['hold']
        pairs.append((cp,chunk));cp=chunk['checkpoint']
    snapshots=[model._source(ctx,r)[0] for _,r in pairs];saved=(ctx._program,ctx._manifest,ctx._first);raw=c.checkpoint_bytes(ctx,cp)
    forbid_numerics(monkeypatch);binding=model.prepare_binding(ctx,origin=origin())
    for (before,chunk),source in zip(pairs,snapshots,strict=True):
        r=bind(model,binding,before,chunk);assert r['source']==source
        for key in ('samples','events'):
            assert r['times'][key]==[{'step_index':v['step_index'],'at':model.at_index(binding,v['step_index'])} for v in source[key]]
        assert r['times']['last_confirmed']['at']==model.at_index(binding,source['last_confirmed']['step_index'])
        assert r['times']['hold'] is None and r['G0_G4']=='not_assessed'
        assert c._hash({k:v for k,v in r.items() if k!='result_sha256'})==r['result_sha256']
    assert (ctx._program,ctx._manifest,ctx._first)==saved and c.checkpoint_bytes(ctx,cp)==raw


def test_utc_kst_fractional_source_and_t0_identity(model,profiles,monkeypatch):
    ctx=reference.context(c,profiles);before=c.start(ctx);chunk=c.advance_chunk(ctx,before,1)
    forbid_numerics(monkeypatch)
    a=model.prepare_binding(ctx,origin=origin());b=model.prepare_binding(ctx,origin=origin('2026-10-01T09:00:00+09:00'))
    assert [model.at_index(a,i) for i in (0,4,8,16)]==[model.at_index(b,i) for i in (0,4,8,16)] and a.sha256!=b.sha256
    ready=model.bind_checkpoint(a,before,expected_binding_sha256=a.sha256)
    committed=model.bind_checkpoint(a,chunk['checkpoint'],expected_binding_sha256=a.sha256)
    assert ready['time']['at']==committed['time']['at']=='2026-10-01T00:00:00.000000Z'
    assert ready['source_checkpoint_sha256']!=committed['source_checkpoint_sha256']
    assert (ready['time']['next_index'],committed['time']['next_index'])==(0,1)


@pytest.mark.parametrize('stamp,dt,count',[
    ('1969-12-31T23:59:59.900001Z',.1,3),('2000-02-28T23:59:59.900001Z',.1,3),
    ('2027-12-31T23:59:59.500000Z',.0625,16),('2026-10-01T09:00:00+09:00',2,16),
    ('2026-10-01T00:00:00.000001Z',.000001,3)])
def test_independent_integer_calendar_arithmetic(model,profiles,monkeypatch,stamp,dt,count):
    case=deepcopy(reference.CASES[0]);case.update(step_seconds=dt,step_count=count,events=[],output_steps=[0,count]);case['forcing_program']=case['forcing_program'][:1]
    ctx=reference.context(c,profiles,case);forbid_numerics(monkeypatch);b=model.prepare_binding(ctx,origin=origin(stamp))
    start=datetime.fromisoformat(stamp.replace('Z','+00:00'));offset=int(start.utcoffset().total_seconds())
    micros=(calendar.timegm(start.timetuple())-offset)*1000000+start.microsecond
    for i in range(count+1):
        seconds,us=divmod(micros+i*round(dt*1000000),1000000);point=datetime.fromtimestamp(seconds,timezone.utc)
        expected=f'{point.year:04d}-{point.month:02d}-{point.day:02d}T{point.hour:02d}:{point.minute:02d}:{point.second:02d}.{us:06d}Z'
        assert model.at_index(b,i)==expected


def test_real_fractional_output_keeps_binary64_elapsed(model,profiles,monkeypatch):
    case=deepcopy(reference.CASES[0]);case.update(step_seconds=.1,step_count=3,output_steps=[0,3]);case['forcing_program']=case['forcing_program'][:1]
    ctx=reference.context(c,profiles,case);before=c.start(ctx);chunk=c.advance_chunk(ctx,before,128)
    forbid_numerics(monkeypatch);b=model.prepare_binding(ctx,origin=origin());r=bind(model,b,before,chunk)
    assert r['source']['samples'][-1]['elapsed_seconds']==.30000000000000004
    assert r['times']['samples'][-1]['at']=='2026-10-01T00:00:00.300000Z'


@pytest.mark.parametrize('stamp',('2026-10-01T00:00:00','2026-10-01T00:00:00-00:00','2026-10-01T00:00:00.0000001Z',
    '2026-10-01T00:00:60Z','2026-02-30T00:00:00Z','2026-10-01T00:00:00+24:00','9999-12-31T23:59:59Z'))
def test_invalid_offset_precision_calendar_and_range(model,profiles,stamp):
    with pytest.raises(model.TimeBindingRejected):model.prepare_binding(reference.context(c,profiles),origin=origin(stamp))


@pytest.mark.parametrize('fault',('origin','precision','extra','id','submicro','fraction','index-bool','index-high'))
def test_invalid_origin_step_and_index(model,profiles,fault):
    case=deepcopy(reference.CASES[0]);o=origin()
    if fault=='origin':o['origin']='reference_calculation'
    elif fault=='precision':o['precision']='millisecond'
    elif fault=='extra':o['extra']=1
    elif fault=='id':o['input_id']=' bad '
    elif fault=='submicro':case['step_seconds']=1e-7
    elif fault=='fraction':case['step_seconds']=1/3
    ctx=reference.context(c,profiles,case)
    with pytest.raises(model.TimeBindingRejected):
        b=model.prepare_binding(ctx,origin=o)
        if fault in ('index-bool','index-high'):model.at_index(b,True if fault=='index-bool' else 17)


@pytest.mark.parametrize('phase,index',[(p,i) for p in ('event','global-event-balance') for i in (0,8,16)]+[('forcing',4),('forcing',8),('forcing',16),('interval',1),('global-step-balance',1)])
def test_real_and_injected_hold_times_keep_correct_active_forcing(model,profiles,monkeypatch,phase,index):
    case=deepcopy(reference.reference.BY_ID['weather-multiple'])
    if phase=='event':next(e for e in case['events'] if e['step_index']==index)['event']['values']['leaf']['value']=1e15
    elif phase=='forcing':next(r for r in case['forcing_program'] if r['step_index']==index)['solar']['values']['outdoor_global_radiation']['value']=-1
    elif phase=='interval':case['forcing_program'][0]['co2']['forcing']['external_co2_flux']['value']=-10000
    elif phase=='global-step-balance':
        old=c.driver.stage.integrate
        def corrupt(**kw):
            r=old(**kw);r['integrated_transfers']['photosynthesis']['value']+=1;return r
        monkeypatch.setattr(c.driver.stage,'integrate',corrupt)
    else:
        old=c.driver.management.apply_management;target=next(e for e in case['events'] if e['step_index']==index)['event']['input_id']
        def corrupt(**kw):
            r=old(**kw)
            if kw['event']['input_id']==target:r['removed']['canopy_sensible_energy']['value']+=1
            return r
        monkeypatch.setattr(c.driver.management,'apply_management',corrupt)
    ctx=reference.context(c,profiles,case);before=c.start(ctx)
    if index:before=c.advance_chunk(ctx,before,index)['checkpoint']
    raw=c.checkpoint_bytes(ctx,before);chunk=c.advance_chunk(ctx,before,1)
    assert chunk['status']=='hold' and chunk['hold']['phase']==phase
    forbid_numerics(monkeypatch);b=model.prepare_binding(ctx,origin=origin());r=bind(model,b,before,chunk)
    last=index if phase in ('forcing','event','global-event-balance') else index-1
    assert r['times']['hold']=={'step_index':index,'at':model.at_index(b,index)}
    assert r['times']['last_confirmed']=={'step_index':last,'at':model.at_index(b,last)}
    assert r['source']['checkpoint'] is None and r['times']['samples']==r['times']['events']==[]
    active=max(row['step_index'] for row in case['forcing_program'] if row['step_index']<index) if phase=='forcing' else max(row['step_index'] for row in case['forcing_program'] if row['step_index']<=last)
    assert r['source']['last_confirmed']['forcing_step_index']==active and c.checkpoint_bytes(ctx,before)==raw


@pytest.mark.parametrize('mutation',('extra','claim','manifest','context','output','event','planned','samples-order','elapsed-bool',
    'sample-unit','sample-active','event-active','last-active','last-phase','calls','validation','legacy-counters','hold','checkpoint','forcing-cursor'))
def test_rehashed_source_schema_cursors_order_calls_and_active_forcing_reject(model,profiles,mutation):
    ctx=reference.context(c,profiles);before=c.start(ctx);chunk=c.advance_chunk(ctx,before,9)
    if mutation=='extra':chunk['extra']=1
    elif mutation=='claim':chunk['claim_scope']='synthetic_joint_solar_ventilation_continuation_only'
    elif mutation=='manifest':chunk['manifest']['numerical']['step_count']+=1
    elif mutation=='context':chunk['context_sha256']='0'*64
    elif mutation=='output':chunk['output_start']+=1
    elif mutation=='event':chunk['event_start']+=1
    elif mutation=='planned':chunk['planned_steps']=False
    elif mutation=='samples-order':chunk['samples'].reverse()
    elif mutation=='elapsed-bool':chunk['samples'][0]['elapsed_seconds']=False
    elif mutation=='sample-unit':chunk['samples'][0]['climate_state']['air_co2_mass']['unit']='mg_CH2O/m2_floor'
    elif mutation=='sample-active':chunk['samples'][1]['forcing_step_index']=0
    elif mutation=='event-active':chunk['events'][-1]['forcing_step_index']=0
    elif mutation=='last-active':chunk['last_confirmed']['forcing_step_index']=0
    elif mutation=='last-phase':chunk['last_confirmed']['phase']='step-end'
    elif mutation=='calls':chunk['confirmed_numerical_coupled_evaluations']+=1
    elif mutation=='validation':chunk['checkpoint_validation_coupled_evaluations']=True
    elif mutation=='legacy-counters':chunk['confirmed_numerical_joint_rhs_evaluations']=100
    elif mutation=='hold':chunk['hold']={'reason':'fake'}
    elif mutation=='checkpoint':chunk['checkpoint']=None
    else:
        cp=chunk['checkpoint'];v=cp.value;v['forcing_cursor']-=1;raw=c._canonical(v)
        chunk['checkpoint']=replace(cp,_raw=raw,sha256=sha256(raw).hexdigest())
    b=model.prepare_binding(ctx,origin=origin())
    with pytest.raises(model.TimeBindingRejected):bind(model,b,before,chunk)


@pytest.mark.parametrize('bad',(None,False,'','0'*64,'x'*64))
def test_trusted_digests_are_mandatory(model,profiles,bad):
    ctx=reference.context(c,profiles);before=c.start(ctx);chunk=c.advance_chunk(ctx,before,1);b=model.prepare_binding(ctx,origin=origin())
    digest=model.source_chunk_sha256(ctx,chunk)
    with pytest.raises(model.TimeBindingRejected):model.bind_chunk(b,before,chunk,expected_chunk_sha256=bad,expected_binding_sha256=b.sha256)
    with pytest.raises(model.TimeBindingRejected):model.bind_chunk(b,before,chunk,expected_chunk_sha256=digest,expected_binding_sha256=bad)
    with pytest.raises(model.TimeBindingRejected):model.bind_checkpoint(b,before,expected_binding_sha256=bad)


def test_original_digest_copy_identity_and_byte_limits(model,profiles,monkeypatch):
    ctx=reference.context(c,profiles);before=c.start(ctx);chunk=c.advance_chunk(ctx,before,1);b=model.prepare_binding(ctx,origin=origin());digest=model.source_chunk_sha256(ctx,chunk)
    r=bind(model,b,before,chunk);r['source']['samples'][0]['climate_state']['air_co2_mass']['value']=0
    b.manifest['origin']['start_at']='changed'
    assert model.source_chunk_sha256(ctx,chunk)==digest and model.at_index(b,0)=='2026-10-01T00:00:00.000000Z'
    changed=dict(chunk);changed['samples']=deepcopy(chunk['samples']);changed['samples'][0]['plant_state']['leaf']['value']+=1
    with pytest.raises(model.TimeBindingRejected):model.bind_chunk(b,before,changed,expected_chunk_sha256=digest,expected_binding_sha256=b.sha256)
    monkeypatch.setattr(model,'MAX_RESULT_BYTES',100)
    with pytest.raises(model.TimeBindingRejected):bind(model,b,before,chunk)
    with pytest.raises(model.TimeBindingRejected):model.bind_checkpoint(b,before,expected_binding_sha256=b.sha256)


@pytest.mark.parametrize('which',('calendar','model'))
def test_time_code_identities_are_bound(model,profiles,monkeypatch,which):
    b=model.prepare_binding(reference.context(c,profiles),origin=origin())
    monkeypatch.setattr(model.clock_helpers if which=='calendar' else model,'CODE_SHA256','0'*64)
    with pytest.raises(model.TimeBindingRejected):model.at_index(b,0)


@pytest.mark.parametrize('bad',(None,False,[],{'checkpoint':None,'value':float('nan')},{'checkpoint':None,'value':float('inf')}))
def test_invalid_source_or_nonfinite_json(model,profiles,bad):
    with pytest.raises(model.TimeBindingRejected):model.source_chunk_sha256(reference.context(c,profiles),bad)


def test_fresh_python_binding_uses_zero_further_numerical_calls(model,profiles,tmp_path):
    ctx=reference.context(c,profiles);before=c.advance_chunk(ctx,c.start(ctx),9)['checkpoint'];chunk=c.advance_chunk(ctx,before,8)
    b=model.prepare_binding(ctx,origin=origin());expected=bind(model,b,before,chunk)
    path=tmp_path/'transport.json';path.write_text(json.dumps({'before':before.value,'before_sha':before.sha256,
        'source':model._source(ctx,chunk)[0],'origin':origin(),'binding_sha':b.sha256,'source_sha':expected['source_chunk_sha256']}))
    script='''import json,sys
from pathlib import Path
import test_crop_greenhouse_co2_time as t
from app import crop_greenhouse_co2_time as m
p=json.loads(Path(sys.argv[1]).read_bytes());c=t.c;ctx=t.reference.context(c,t.profiles.__wrapped__());s=p['source']
before=c.restore_checkpoint(ctx,c._canonical(p['before']),expected_sha256=p['before_sha'])
s['checkpoint']=c.restore_checkpoint(ctx,c._canonical(s['checkpoint']['value']),expected_sha256=s['checkpoint']['sha256'])
def forbidden(*args,**kw):raise AssertionError('time binding invoked numerics')
r=c.driver.stage.rhs;solar=r.solar_rhs
for target,name in ((r,'evaluate_rhs'),(c.driver.stage.joint,'evaluate_rhs'),(c.driver.stage,'integrate'),(solar,'evaluate_rhs'),(solar.vent,'calculate_ventilation'),(solar.par.radiation,'calculate_par'),(solar.nir,'calculate_nir'),(r.gas,'density_to_ppm'),(r.net,'calculate_exchange'),(r.air,'evaluate_rhs'),(c.driver.management,'apply_management'),(c,'advance_chunk'),(c,'restore_checkpoint')):setattr(target,name,forbidden)
b=m.prepare_binding(ctx,origin=p['origin']);out=m.bind_chunk(b,before,s,expected_chunk_sha256=p['source_sha'],expected_binding_sha256=p['binding_sha'])
print(json.dumps({'result':out['result_sha256'],'binding':b.sha256,'binding_numerical_calls':0}))
'''
    completed=subprocess.run([sys.executable,'-B','-c',script,str(path)],check=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE,timeout=30,env=dict(os.environ,PYTHONPATH=reference.FRESH_PYTHONPATH))
    assert json.loads(completed.stdout)=={'result':expected['result_sha256'],'binding':b.sha256,'binding_numerical_calls':0}


@pytest.mark.parametrize('which',('context','binding','checkpoint'))
def test_legacy_types_are_incompatible(model,profiles,which):
    import test_crop_greenhouse_solar_continuation as old
    from app import crop_greenhouse_solar_time as old_time
    ctx=reference.context(c,profiles);b=model.prepare_binding(ctx,origin=origin());legacy=old.context(profiles)
    with pytest.raises(model.TimeBindingRejected):
        if which=='context':model.prepare_binding(legacy,origin=origin())
        elif which=='binding':model.at_index(old_time.prepare_binding(legacy,origin=origin()),0)
        else:model.bind_checkpoint(b,old.model.start(legacy),expected_binding_sha256=b.sha256)


def test_maximum128_samples_events_forcing_under_original_byte_limit(model,profiles,monkeypatch):
    case=deepcopy(reference.CASES[0]);case.update(step_seconds=.0625,step_count=128,output_steps=list(range(129)),events=[])
    initial=case['forcing_program'][0];case['forcing_program']=[{**deepcopy(initial),'step_index':i} for i in range(129)]
    source=reference.reference.BY_ID['multiple']['events'][0]['event']
    for i in range(128):
        e=deepcopy(source);e['input_id']='co2-time-max-'+str(i);e['values']['leaf']['value']=e['values']['stem_root']['value']=0
        for q in e['values']['fruit_fraction']:q['value']=0
        case['events'].append({'step_index':i,'event':e})
    ctx=reference.context(c,profiles,case);before=c.start(ctx);chunk=c.advance_chunk(ctx,before,128);assert chunk['status']=='yielded'
    saved=model._source(ctx,chunk)[0];forbid_numerics(monkeypatch);b=model.prepare_binding(ctx,origin=origin());out=bind(model,b,before,chunk)
    assert len(out['times']['samples'])==len(out['times']['events'])==128 and out['source']==saved
    assert len(c._canonical(out))<=8*1024**2
    print(json.dumps({'co2_time_maximum_bytes':{'source':len(c._canonical(saved)),
        'bound_result':len(c._canonical(out)),'samples':128,'events':128,'forcing_activations':128}}))


@pytest.mark.parametrize('fault',('missing-inner','invalid-inner','phase','reason','extra','calls'))
def test_rehashed_hold_details_and_forcing_position_are_closed(model,profiles,fault):
    case=deepcopy(reference.reference.BY_ID['weather-multiple']);case['forcing_program'][0]['co2']['forcing']['external_co2_flux']['value']=-10000
    ctx=reference.context(c,profiles,case);before=c.start(ctx);chunk=c.advance_chunk(ctx,before,128);assert chunk['status']=='hold'
    if fault=='missing-inner':del chunk['hold']['inner_failed_stage']
    elif fault=='invalid-inner':chunk['hold']['inner_failed_stage']=False
    elif fault=='phase':chunk['hold']['phase']='forcing'
    elif fault=='reason':chunk['hold']['reason']=''
    elif fault=='extra':chunk['hold']['extra']=1
    else:chunk['confirmed_numerical_coupled_evaluations']+=1
    b=model.prepare_binding(ctx,origin=origin())
    with pytest.raises(model.TimeBindingRejected):bind(model,b,before,chunk)


@pytest.mark.parametrize('raw',(b'1',b'null',b'[]'))
def test_wrong_checkpoint_json_type_rejects_without_numerics(model,profiles,monkeypatch,raw):
    ctx=reference.context(c,profiles);cp=c.start(ctx);changed=replace(cp,_raw=raw,sha256=sha256(raw).hexdigest())
    forbid_numerics(monkeypatch);b=model.prepare_binding(ctx,origin=origin())
    with pytest.raises(model.TimeBindingRejected):model.bind_checkpoint(b,changed,expected_binding_sha256=b.sha256)
