"""UTC representation must leave the physical clock and original values intact."""
from copy import deepcopy
from dataclasses import replace
from hashlib import sha256
import calendar
import json
import subprocess
import sys
import time

import pytest

from app import crop_climate_joint_time as model
import test_crop_climate_joint_continuation as reference

profiles=reference.profiles


def origin(stamp='2026-10-01T00:00:00Z'):
    return {'input_id':'synthetic-time-origin-v1','origin':'synthetic','start_at':stamp,'precision':'microsecond'}


def test_smoke_same_utc_and_kst_instants(profiles):
    ctx=reference.context(profiles)
    a=model.prepare_binding(ctx,origin=origin());b=model.prepare_binding(ctx,origin=origin('2026-10-01T09:00:00+09:00'))
    assert [model.at_index(a,i) for i in (0,8,16)]==[model.at_index(b,i) for i in (0,8,16)]
    assert model.at_index(a,16)=='2026-10-01T00:00:32.000000Z' and a.sha256!=b.sha256


def test_smoke_fractional_grid_preserves_original_physical_elapsed(profiles):
    case=deepcopy(reference.CASES[0]);case.update(step_seconds=.1,step_count=3,output_steps=[0,3])
    ctx=reference.context(profiles,case);binding=model.prepare_binding(ctx,origin=origin('1969-12-31T23:59:59.900001Z'))
    assert model.at_index(binding,3)=='1970-01-01T00:00:00.200001Z'
    assert ctx.program['step_seconds']*3==.30000000000000004


def test_actual_fractional_output_keeps_binary_elapsed_and_exact_utc(profiles,monkeypatch):
    case=deepcopy(reference.CASES[0]);case.update(step_seconds=.1,step_count=3,output_steps=[0,3])
    ctx=reference.context(profiles,case);before=reference.model.start(ctx);chunk=reference.model.advance_chunk(ctx,before,128)
    forbid_numerics(monkeypatch);binding=model.prepare_binding(ctx,origin=origin());r=bind(binding,before,chunk)
    assert r['source']['samples'][-1]['elapsed_seconds']==.30000000000000004
    assert r['times']['samples'][-1]['at']=='2026-10-01T00:00:00.300000Z'


def bind(binding,before,chunk):
    return model.bind_chunk(binding,before,chunk,expected_binding_sha256=binding.sha256,
        expected_chunk_sha256=model.source_chunk_sha256(binding._context,chunk))


def forbid_numerics(monkeypatch):
    def forbidden(*a,**kw):pytest.fail('UTC binding invoked physical calculations or restore')
    for target,name in ((reference.model.driver.joint,'evaluate_rhs'),(reference.model.driver.short,'integrate'),
        (reference.model.driver.management,'apply_management'),(reference.model,'advance_chunk'),(reference.model,'restore_checkpoint')):
        monkeypatch.setattr(target,name,forbidden)


@pytest.mark.parametrize('index',range(9))
@pytest.mark.parametrize('budget',(1,7,128))
def test_all_accepted_programs_preserve_every_source_and_prefix_with_no_numerics(profiles,monkeypatch,index,budget):
    ctx=reference.context(profiles,reference.CASES[index]);cp=reference.model.start(ctx);pairs=[]
    while cp.value['next_index']<=ctx.program['step_count']:
        chunk=reference.model.advance_chunk(ctx,cp,budget);pairs.append((cp,chunk));cp=chunk['checkpoint']
    saved_context=(ctx._manifest,ctx._program,ctx._first);raw_cp=reference.model.checkpoint_bytes(ctx,cp)
    snapshots=[model._source(ctx,chunk)[0] for _,chunk in pairs]
    forbid_numerics(monkeypatch);binding=model.prepare_binding(ctx,origin=origin())
    for (before,chunk),source in zip(pairs,snapshots,strict=True):
        r=bind(binding,before,chunk);assert r['source']==source
        for key in ('samples','events'):
            assert [p['at'] for p in r['times'][key]]==[model.at_index(binding,row['step_index']) for row in source[key]]
        assert r['times']['last_confirmed']['at']==model.at_index(binding,source['last_confirmed']['step_index'])
        assert r['times']['hold'] is None and r['scope']=='software_research_only' and r['G0_G4']=='not_assessed'
        payload={k:v for k,v in r.items() if k!='result_sha256'}
        assert reference.model._hash(payload)==r['result_sha256']
    assert (ctx._manifest,ctx._program,ctx._first)==saved_context and reference.model.checkpoint_bytes(ctx,cp)==raw_cp


def test_t0_ready_and_committed_have_same_time_but_distinct_original_identity(profiles,monkeypatch):
    ctx=reference.context(profiles);before=reference.model.start(ctx);chunk=reference.model.advance_chunk(ctx,before,1)
    forbid_numerics(monkeypatch);binding=model.prepare_binding(ctx,origin=origin())
    a=model.bind_checkpoint(binding,before,expected_binding_sha256=binding.sha256)
    b=model.bind_checkpoint(binding,chunk['checkpoint'],expected_binding_sha256=binding.sha256)
    assert a['time']['at']==b['time']['at'] and (a['time']['next_index'],b['time']['next_index'])==(0,1)
    assert a['source_checkpoint_sha256']!=b['source_checkpoint_sha256']
    r=bind(binding,before,chunk)
    assert r['times']['samples']==r['times']['events']==[{'step_index':0,'at':a['time']['at']}]


def test_real_failed_management_has_time_without_a_fabricated_event_or_output(profiles,monkeypatch):
    case=deepcopy(reference.CASES[6]);case['events'][-1]['event']['values']['leaf']['value']=50000
    ctx=reference.context(profiles,case);before=reference.model.advance_chunk(ctx,reference.model.start(ctx),16)['checkpoint']
    raw=reference.model.checkpoint_bytes(ctx,before);chunk=reference.model.advance_chunk(ctx,before,1)
    assert chunk['status']=='hold' and chunk['last_confirmed']['phase']=='step-end'
    forbid_numerics(monkeypatch);binding=model.prepare_binding(ctx,origin=origin());r=bind(binding,before,chunk)
    assert r['times']['samples']==r['times']['events']==[]
    assert r['times']['hold']==r['times']['last_confirmed']=={'step_index':16,'at':'2026-10-01T00:00:32.000000Z'}
    assert r['source']['checkpoint'] is None and reference.model.checkpoint_bytes(ctx,before)==raw


def test_actual_interval_hold_keeps_failed_and_confirmed_times_separate(profiles,monkeypatch):
    case=deepcopy(reference.CASES[0]);case['scenario']['forcing']['canopy_external_heat']['value']=1e7
    ctx=reference.context(profiles,case);before=reference.model.start(ctx);chunk=reference.model.advance_chunk(ctx,before,128)
    forbid_numerics(monkeypatch);binding=model.prepare_binding(ctx,origin=origin());r=bind(binding,before,chunk)
    assert r['times']['hold']['at']=='2026-10-01T00:00:02.000000Z'
    assert r['times']['last_confirmed']['at']=='2026-10-01T00:00:00.000000Z'
    assert len(r['times']['samples'])==1 and not r['times']['events']


@pytest.mark.parametrize('target',('step','event'))
def test_global_balance_hold_preserves_only_original_confirmed_prefix(profiles,monkeypatch,target):
    ctx=reference.context(profiles);before=reference.model.start(ctx)
    if target=='step':
        old=reference.model.driver.short.integrate
        def corrupt(**kw):
            r=old(**kw);r['integrated_transfers']['photosynthesis']['value']+=1;return r
        monkeypatch.setattr(reference.model.driver.short,'integrate',corrupt)
    else:
        old=reference.model.driver.management.apply_management
        def corrupt(**kw):
            r=old(**kw);r['removed']['canopy_sensible_energy']['value']+=1;return r
        monkeypatch.setattr(reference.model.driver.management,'apply_management',corrupt)
    chunk=reference.model.advance_chunk(ctx,before,128);assert chunk['hold']['phase']=='global-'+target+'-balance'
    forbid_numerics(monkeypatch);binding=model.prepare_binding(ctx,origin=origin());r=bind(binding,before,chunk)
    assert r['source']['checkpoint'] is None and r['times']['hold']['step_index']==chunk['hold']['step_index']
    assert r['source']['samples']==chunk['samples'] and r['source']['events']==chunk['events']


@pytest.mark.parametrize('stamp',('2026-10-01','2026-10-01T00:00:00','2026-10-01T00:00:00-00:00',
    '2026-10-01T00:00:00 Asia/Seoul','2026-10-01t00:00:00z','2026-10-01T00:00:00.0000001Z',
    '2026-10-01T00:00:00+00:60','2026-10-01T00:00:00+24:00','2026-10-01T24:00:00Z',
    '2016-12-31T23:59:60Z','2026-02-29T00:00:00Z','0000-01-01T00:00:00Z',None,True,10**100))
def test_unsupported_or_ambiguous_origins_are_rejected(profiles,stamp):
    with pytest.raises(model.TimeBindingRejected,match='ORIGIN_HOLD'):model.prepare_binding(reference.context(profiles),origin=origin(stamp))


@pytest.mark.parametrize('mutation',('extra','missing','id','id-space','id-long','origin','precision','shape'))
def test_closed_origin_and_scope(profiles,mutation):
    v=origin()
    if mutation=='extra':v['extra']=1
    elif mutation=='missing':del v['start_at']
    elif mutation=='id':v['input_id']=False
    elif mutation=='id-space':v['input_id']=' '
    elif mutation=='id-long':v['input_id']='x'*201
    elif mutation=='origin':v['origin']='reference_calculation'
    elif mutation=='precision':v['precision']='second'
    else:v=[]
    with pytest.raises(model.TimeBindingRejected,match='ORIGIN_HOLD'):model.prepare_binding(reference.context(profiles),origin=v)


@pytest.mark.parametrize('dt',(1e-7,1e-200,1/3))
def test_unrepresentable_grid_is_held_without_rounding_or_changing_context(profiles,dt):
    case=deepcopy(reference.CASES[0]);case['step_seconds']=dt;ctx=reference.context(profiles,case);raw=ctx._program
    with pytest.raises(model.TimeBindingRejected,match='PRECISION_HOLD'):model.prepare_binding(ctx,origin=origin())
    assert ctx._program==raw and ctx.program['step_seconds']==dt


@pytest.mark.parametrize('stamp',('9999-12-31T23:59:40Z','0001-01-01T00:00:00+00:01'))
def test_utc_origin_and_end_range_overflow_reject(profiles,stamp):
    with pytest.raises(model.TimeBindingRejected):model.prepare_binding(reference.context(profiles),origin=origin(stamp))


@pytest.mark.parametrize('start,end',(('0001-01-01T00:00:00Z','0001-01-01T00:00:32.000000Z'),
    ('9999-12-31T23:59:27.999999Z','9999-12-31T23:59:59.999999Z')))
def test_exact_supported_year_range_endpoints(profiles,start,end):
    binding=model.prepare_binding(reference.context(profiles),origin=origin(start))
    assert model.at_index(binding,16)==end


@pytest.mark.parametrize('start',('1969-12-31T23:59:59.999999Z','2000-02-28T23:59:59.999999Z',
    '2100-02-28T23:59:59.999999Z','2026-12-31T23:59:59.999999Z'))
@pytest.mark.parametrize('dt',(.000001,.0625,.1,2.0))
def test_integer_epoch_oracle_checks_rollovers_without_float_timestamp(profiles,start,dt):
    case=deepcopy(reference.CASES[0]);case['step_seconds']=dt;binding=model.prepare_binding(reference.context(profiles,case),origin=origin(start))
    whole,fraction=start[:-1].split('.');start_us=calendar.timegm(time.strptime(whole,'%Y-%m-%dT%H:%M:%S'))*1_000_000+int(fraction)
    step_us={.000001:1,.0625:62500,.1:100000,2.0:2000000}[dt]
    for i in range(17):
        seconds,micros=divmod(start_us+i*step_us,1_000_000)
        expected=time.strftime('%Y-%m-%dT%H:%M:%S',time.gmtime(seconds))+f'.{micros:06d}Z'
        assert model.at_index(binding,i)==expected


@pytest.mark.parametrize('index',(True,False,-1,17,1.,'1',None,10**100))
def test_only_original_integer_indices(profiles,index):
    binding=model.prepare_binding(reference.context(profiles),origin=origin())
    with pytest.raises(model.TimeBindingRejected,match='INDEX_HOLD'):model.at_index(binding,index)


@pytest.mark.parametrize('field',('_manifest','sha256','_context','_token'))
def test_changed_internal_binding_identity_rejects(profiles,field):
    binding=model.prepare_binding(reference.context(profiles),origin=origin())
    changed=replace(binding,**{field:{'_manifest':b'{}','sha256':'0'*64,'_context':None,'_token':None}[field]})
    with pytest.raises(model.TimeBindingRejected):model.at_index(changed,0)


@pytest.mark.parametrize('kind',('time-code','time-rule','continuation-code','rhs','policy'))
def test_changed_current_time_or_model_code_and_policy_reject(profiles,monkeypatch,kind):
    binding=model.prepare_binding(reference.context(profiles),origin=origin())
    if kind=='time-code':monkeypatch.setattr(model,'CODE_SHA256','0'*64)
    elif kind=='time-rule':monkeypatch.setattr(model,'TIME_RULE','changed')
    elif kind=='continuation-code':monkeypatch.setattr(reference.model,'CODE_SHA256','0'*64)
    elif kind=='rhs':monkeypatch.setattr(reference.model.driver.joint,'CODE_SHA256','0'*64)
    else:monkeypatch.setattr(reference.model.driver.joint.crop.startup,'POLICY_SHA256','0'*64)
    with pytest.raises(model.TimeBindingRejected):model.at_index(binding,0)


def test_origin_context_and_before_checkpoint_mixing_rejects(profiles):
    ctx=reference.context(profiles);before=reference.model.start(ctx);chunk=reference.model.advance_chunk(ctx,before,9)
    a=model.prepare_binding(ctx,origin=origin());b=model.prepare_binding(ctx,origin=origin('2026-10-02T00:00:00Z'))
    digest=model.source_chunk_sha256(ctx,chunk)
    with pytest.raises(model.TimeBindingRejected,match='binding SHA'):
        model.bind_chunk(b,before,chunk,expected_chunk_sha256=digest,expected_binding_sha256=a.sha256)
    with pytest.raises(model.TimeBindingRejected):bind(a,chunk['checkpoint'],chunk)
    other=reference.context(profiles,reference.CASES[0]);other_binding=model.prepare_binding(other,origin=origin())
    with pytest.raises(model.TimeBindingRejected):bind(other_binding,before,chunk)


@pytest.mark.parametrize('mutation',('extra','missing','scope','manifest','status','start','planned','samples-order',
    'sample-elapsed','sample-bool','sample-state','event-elapsed','last','calls','validation-calls','hold','checkpoint'))
def test_shape_time_prefix_and_position_errors_reject_even_with_a_new_transport_digest(profiles,mutation):
    ctx=reference.context(profiles);before=reference.model.start(ctx);chunk=reference.model.advance_chunk(ctx,before,9)
    if mutation=='extra':chunk['extra']=1
    elif mutation=='missing':del chunk['steps']
    elif mutation=='scope':chunk['scope']='crop_prediction'
    elif mutation=='manifest':chunk['manifest']['numerical']['step_seconds']=3.
    elif mutation=='status':chunk['status']='completed'
    elif mutation=='start':chunk['output_start']=True
    elif mutation=='planned':chunk['planned_steps']=False
    elif mutation=='samples-order':chunk['samples'].reverse()
    elif mutation=='sample-elapsed':chunk['samples'][0]['elapsed_seconds']=.000001
    elif mutation=='sample-bool':chunk['samples'][0]['step_index']=False
    elif mutation=='sample-state':chunk['samples'][0]['plant_state']['leaf']['value']+=1
    elif mutation=='event-elapsed':chunk['events'][0]['elapsed_seconds']=1.
    elif mutation=='last':chunk['last_confirmed']['plant_state']['leaf']['value']+=1
    elif mutation=='calls':chunk['confirmed_numerical_rhs_evaluations']+=1
    elif mutation=='validation-calls':chunk['checkpoint_validation_rhs_evaluations']=True
    elif mutation=='hold':chunk['hold']={'reason':'fake'}
    else:chunk['checkpoint']=None
    binding=model.prepare_binding(ctx,origin=origin())
    with pytest.raises(model.TimeBindingRejected):bind(binding,before,chunk)


@pytest.mark.parametrize('bad',(None,False,'','0'*64,'x'*64))
def test_original_trusted_digests_are_mandatory(profiles,bad):
    ctx=reference.context(profiles);before=reference.model.start(ctx);chunk=reference.model.advance_chunk(ctx,before,1)
    binding=model.prepare_binding(ctx,origin=origin());digest=model.source_chunk_sha256(ctx,chunk)
    with pytest.raises(model.TimeBindingRejected):model.bind_chunk(binding,before,chunk,expected_chunk_sha256=bad,expected_binding_sha256=binding.sha256)
    with pytest.raises(model.TimeBindingRejected):model.bind_chunk(binding,before,chunk,expected_chunk_sha256=digest,expected_binding_sha256=bad)
    with pytest.raises(model.TimeBindingRejected):model.bind_checkpoint(binding,before,expected_binding_sha256=bad)


def test_changed_and_rehashed_source_cannot_use_original_trusted_digest(profiles):
    ctx=reference.context(profiles);before=reference.model.start(ctx);chunk=reference.model.advance_chunk(ctx,before,1)
    binding=model.prepare_binding(ctx,origin=origin());digest=model.source_chunk_sha256(ctx,chunk)
    chunk['samples'][0]['plant_state']['leaf']['value']+=1
    assert model.source_chunk_sha256(ctx,chunk)!=digest
    with pytest.raises(model.TimeBindingRejected,match='trusted chunk SHA'):
        model.bind_chunk(binding,before,chunk,expected_chunk_sha256=digest,expected_binding_sha256=binding.sha256)


@pytest.mark.parametrize('bad',(None,True,[],{'checkpoint':None,'value':float('nan')},{'checkpoint':None,'value':float('inf')}))
def test_invalid_source_shape_or_nonfinite_values_are_rejected(profiles,bad):
    with pytest.raises(model.TimeBindingRejected):
        model.source_chunk_sha256(reference.context(profiles),bad)


def test_outputs_and_manifest_are_copies_and_byte_limits_are_enforced(profiles,monkeypatch):
    ctx=reference.context(profiles);before=reference.model.start(ctx);chunk=reference.model.advance_chunk(ctx,before,1)
    binding=model.prepare_binding(ctx,origin=origin());saved=model.source_chunk_sha256(ctx,chunk);r=bind(binding,before,chunk)
    r['source']['samples'][0]['plant_state']['leaf']['value']=0;binding.manifest['origin']['start_at']='changed'
    assert model.source_chunk_sha256(ctx,chunk)==saved and model.at_index(binding,0)=='2026-10-01T00:00:00.000000Z'
    monkeypatch.setattr(model,'MAX_RESULT_BYTES',100)
    with pytest.raises(model.TimeBindingRejected,match='RESOURCE_HOLD'):bind(binding,before,chunk)
    with pytest.raises(model.TimeBindingRejected,match='RESOURCE_HOLD'):model.bind_checkpoint(binding,before,expected_binding_sha256=binding.sha256)


def test_maximum_first_chunk_preserves_all_128_samples_and_events(profiles,monkeypatch):
    case=deepcopy(reference.CASES[0]);case.update(step_seconds=.0625,step_count=128,output_steps=list(range(129)),events=[])
    event=deepcopy(reference.reference.PREVIOUS['cases'][0]['event'])
    for i in range(128):
        e=deepcopy(event);e['input_id']=f'synthetic-time-max-{i}';case['events'].append({'step_index':i,'event':e})
    ctx=reference.context(profiles,case);before=reference.model.start(ctx);chunk=reference.model.advance_chunk(ctx,before,128)
    saved=model._source(ctx,chunk)[0];forbid_numerics(monkeypatch);binding=model.prepare_binding(ctx,origin=origin());r=bind(binding,before,chunk)
    assert len(r['times']['samples'])==len(r['times']['events'])==128 and r['source']==saved
    assert len(reference.model._canonical(r))<=model.MAX_RESULT_BYTES


def test_fresh_python_binds_original_transport_without_replaying_prefix(profiles,tmp_path):
    ctx=reference.context(profiles);before=reference.model.advance_chunk(ctx,reference.model.start(ctx),9)['checkpoint']
    chunk=reference.model.advance_chunk(ctx,before,8);binding=model.prepare_binding(ctx,origin=origin());expected=bind(binding,before,chunk)
    p=tmp_path/'transport.json';p.write_text(json.dumps({'before':before.value,'before_sha256':before.sha256,
        'source':model._source(ctx,chunk)[0],'origin':origin(),'binding_sha256':binding.sha256,'source_sha256':expected['source_chunk_sha256']}))
    script='''import json,sys
from pathlib import Path
import test_crop_climate_joint_time as t
from app import crop_climate_joint_time as m
p=json.loads(Path(sys.argv[1]).read_bytes());ctx=t.reference.context(t.profiles.__wrapped__());s=p['source'];c=t.reference.model
before=c.restore_checkpoint(ctx,c._canonical(p['before']),expected_sha256=p['before_sha256'])
s['checkpoint']=c.restore_checkpoint(ctx,c._canonical(s['checkpoint']['value']),expected_sha256=s['checkpoint']['sha256'])
def forbidden(*a,**kw):raise AssertionError('UTC binding invoked numerics')
c.driver.joint.evaluate_rhs=c.driver.short.integrate=c.driver.management.apply_management=c.restore_checkpoint=c.advance_chunk=forbidden
b=m.prepare_binding(ctx,origin=p['origin']);r=m.bind_chunk(b,before,s,expected_chunk_sha256=p['source_sha256'],expected_binding_sha256=p['binding_sha256'])
print(json.dumps({'result_sha256':r['result_sha256'],'binding_sha256':b.sha256,'binding_numerical_calls':0}))
'''
    r=subprocess.run([sys.executable,'-B','-c',script,str(p)],check=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE,timeout=20)
    assert json.loads(r.stdout)=={'result_sha256':expected['result_sha256'],'binding_sha256':binding.sha256,'binding_numerical_calls':0}
