from copy import deepcopy
from decimal import Decimal,localcontext
from fractions import Fraction
from hashlib import sha256
import json

import pytest

from app import crop_stem_root_funded_leaf_point as model
from test_crop_stem_root_funded_internode_point import setup as stem_setup
from test_crop_stem_root_initial_binding import stored,profiles
from test_crop_leaf_carbon_stock_artifact import ACCESS,encoded,inputs as crop_inputs


def setup(row,cut=0,count=2,temperature=22.):
    kw=stem_setup(row,cut,count=1);p=kw['context'].program;events=[]
    parent=[r['compartment_id']for r in p['stem_root_compartments']if r['kind']=='internode'][-1]
    for i in range(count):
        leaf=deepcopy(p['leaves'][i%len(p['leaves'])]);area=model.arithmetic.resume.short.old.leaf_area._area_at(Fraction(0),leaf['curve'])
        leaf.update(leaf_id='declared-new-leaf-'+str(i),thermal_age={'value':0.,'unit':'degC_day'},initial_area=area,
                    initial_carbon={'value':.25*(i+1),'unit':'mg_CH2O/m2_floor'})
        events.append({'event_id':'declared-leaf-event-'+str(i),'parent_internode_id':parent,
                       'incoming_temperature':{'value':temperature,'unit':'degC'},'leaf':leaf})
    kw['inputs'].update(schema_version='stem-root-funded-leaf-point-input-v1',policy='explicit-new-leaf-carbon-from-buffer-v1',events=events)
    return kw


@pytest.mark.parametrize('case',range(6))
@pytest.mark.parametrize('cut',[0,1])
def test_new_leaf_layout_preserves_original_stem_root_leaf_and_non_target_current_values(stored,case,cut):
    kw=setup(stored[case],cut);before=json.loads(kw['raw_checkpoint']);old=before['last_confirmed']['state'];n=len(kw['context'].program['leaves']);inputs=deepcopy(kw['inputs'])
    r=model.apply_leaf_births(**kw);after=r['after_sample']['state'];count=2
    assert after[1:103]==old[1:103]and after[104:106]==old[104:106]and after[0]<old[0]
    assert after[106:106+n]==old[106:106+n]and after[106+n:106+n+count]==[0.,0.]
    assert after[106+n+count:106+2*n+count]==old[106+n:106+2*n]
    assert after[106+2*(n+count):106+2*(n+count)+n]==old[106+2*n:106+3*n]
    assert after[106+3*(n+count):]==old[106+3*n:]
    assert r['after_program']['stem_root_compartments']==json.loads(kw['context']._program)['stem_root_compartments']
    assert r['after_program']['leaves'][:n]==json.loads(kw['context']._program)['leaves']
    assert r['before_checkpoint']==before and kw['inputs']==inputs and model.apply_leaf_births(**kw)==r
    assert r['after_sample']['curve_invariant_changes'][:n]==before['last_confirmed']['curve_invariant_changes']
    assert r['after_sample']['curve_invariant_changes'][n:]==[{'value':0.,'unit':'m2'}]*count
    assert r['checkpoint']is None and r['elapsed_steps_advanced']==0 and r['checkpoint_validation_stage_evaluations']==1 and r['after_stage_evaluations']==1
    assert r['redistribution_authorized']is False and r['G0_G4']=='not_assessed'and r['time_kind']=='synthetic_model_clock_not_observation'
    assert all(abs(v['residual']['value'])<=v['budget']['value']for v in r['balances'].values())


@pytest.mark.parametrize('case',range(6))
def test_port_matches_actual_original_leaf_point_without_fabricated_context_or_checkpoint(stored,profiles,case):
    kw=setup(stored[case],count=2);r=model.apply_leaf_births(**kw);old=model.arithmetic
    ctx=old.resume.prepare_context(program=crop_inputs(case)['program'],step_seconds=.125,step_count=1,**profiles)
    cp=old.resume.start(ctx);old_raw=old.resume.checkpoint_bytes(ctx,cp)
    events=[{('attachment_internode_id'if k=='parent_internode_id'else k):v for k,v in e.items()}for e in kw['inputs']['events']]
    inputs={k:deepcopy(v)for k,v in kw['inputs'].items()if k in old.FIELDS}
    inputs.update(schema_version='leaf-funded-birth-point-input-v1',policy=old.POLICY,context_sha256=ctx.root_sha256,checkpoint_sha256=cp.sha256,events=events)
    previous=old.apply_births(context=ctx,raw_checkpoint=old_raw,expected_sha256=cp.sha256,inputs=inputs)
    y=r['after_sample']['state'];n=len(r['after_program']['leaves']);exact=sum((Fraction.from_float(v)for v in y[106+3*n:]),Fraction(0))
    projected=[y[0],float(exact),*y[1:106+3*n]]
    assert projected==previous['after_sample']['state']and r['point_flows']==previous['point_flows']
    assert [v['initialization']for v in r['birth_receipts']]==[v['initialization']for v in previous['birth_receipts']]


@pytest.mark.parametrize('temperature',[10.,22.,34.])
@pytest.mark.parametrize('masses',[(1.,),(.1,.2),(3.5,2.25,.125)])
def test_independent_decimal_cLeafG_capacity_U103_and_whole_C(stored,temperature,masses):
    kw=setup(stored[0],1,len(masses),temperature)
    for event,C in zip(kw['inputs']['events'],masses,strict=True):event['leaf']['initial_carbon']['value']=C
    r=model.apply_leaf_births(**kw);old=r['before_checkpoint']['last_confirmed']['state'];new=r['after_sample']['state'];p=r['after_program'];n0=len(kw['context'].program['leaves']);n1=len(p['leaves'])
    with localcontext()as ctx:
        ctx.prec=110;D=Decimal.from_float;S=sum(map(D,masses),Decimal(0));c=D(.28)
        assert r['growth_cost']['parameter']=='cLeafG'and r['growth_cost']['value']==.28
        for name,expected in [('structural_carbon',float(S)),('growth_respiration',float(c*S)),('buffer_debit',float((1+c)*S))]:assert r['point_flows'][name]['value']==expected
        assert new[0]==float(D(old[0])-D(float((1+c)*S)))
        k=D(p['scenario']['parameters']['leaf_heat_capacity']['value']);floor=D(p['model_floor_area']['value']);ref=D(p['scenario']['parameters']['reference_temperature']['value']);caps=[];energies=[]
        for receipt in r['birth_receipts']:
            area=D(receipt['initialization']['state']['area']['value']);cap=float(k*area/floor);energy=float(D(cap)*(D(temperature)-ref))
            assert receipt['capacity_in']['value']==cap and receipt['sensible_in']['value']==energy;caps.append(D(cap));energies.append(D(energy))
        assert r['point_flows']['capacity_in']['value']==float(sum(caps,Decimal(0)))and r['point_flows']['sensible_in']['value']==float(sum(energies,Decimal(0)))
        assert new[103]==float(D(old[103])+D(float(sum(energies,Decimal(0)))))
        whole=lambda y,n:D(y[0])+sum(map(D,y[3:53]),Decimal(0))+sum(map(D,y[106+2*n:]),Decimal(0))
        assert abs(whole(new,n1)-whole(old,n0)+D(float(c*S)))<=D(r['balances']['whole_carbon']['budget']['value'])


@pytest.mark.parametrize('change',[
    lambda v:v.update(origin='observed'),lambda v:v.update(extra=1),lambda v:v.update(policy='free_leaf'),
    lambda v:v.update(initial_binding_sha256='0'*64),lambda v:v.update(checkpoint_sha256='0'*64),lambda v:v.update(context_sha256='0'*64),
    lambda v:v['at_elapsed_seconds_exact'].update(numerator='2'),lambda v:v['model_floor_area'].update(value=2),
    lambda v:v.update(events=[]),lambda v:v.update(events={}),lambda v:v['events'][0].update(parent_internode_id='invented'),
    lambda v:v['events'][0].update(parent_internode_id='explicit-root'),lambda v:v['events'][0].update(extra=1),
    lambda v:v['events'][0]['leaf'].update(leaf_id='own-leaf-0'),
    lambda v:v['events'][1]['leaf'].update(leaf_id='declared-new-leaf-0'),lambda v:v['events'][1].update(event_id='declared-leaf-event-0'),
    lambda v:v['events'][0]['leaf']['thermal_age'].update(value=1.),lambda v:v['events'][0]['leaf']['initial_area'].update(value=0.),
    lambda v:v['events'][0]['leaf']['initial_carbon'].update(value=0.),lambda v:v['events'][0]['leaf']['initial_carbon'].update(value=True),
    lambda v:v['events'][0]['leaf']['initial_carbon'].update(value=100000.),lambda v:v['events'][0]['leaf']['initial_carbon'].update(unit='g_DM/plant'),
    lambda v:v['events'][0]['incoming_temperature'].update(value=9.),lambda v:v['events'][0].pop('incoming_temperature'),
    lambda v:v['rights'].update(use=False),lambda v:v['rights'].update(redistribute=1),lambda v:v.update(reviewer='')])
def test_invalid_declarations_and_parent_time_rights_are_held_without_mutation(stored,change):
    kw=setup(stored[0]);change(kw['inputs']);before=deepcopy(kw['inputs']);raw=kw['raw_checkpoint']
    with pytest.raises(model.LeafBirthHold):model.apply_leaf_births(**kw)
    assert kw['inputs']==before and kw['raw_checkpoint']==raw


def test_two_current_RHS_calls_initialize_only_declared_new_leaves_and_have_no_external_side_effect(stored,monkeypatch):
    import os,socket,subprocess,psycopg
    from app import job_store
    kw=setup(stored[1],1);calls=[];initializations=[];evaluate=model.short._evaluate;initialize=model.short.old.leaf_area.initialize_leaf_area
    names={e['leaf']['leaf_id']for e in kw['inputs']['events']}
    def counted(p,y,profiles):calls.append(tuple(y));return evaluate(p,y,profiles)
    def new_only(*,inputs):
        assert inputs['leaf_id']in names;initializations.append(inputs['leaf_id']);return initialize(inputs=inputs)
    def forbidden(*a,**k):raise AssertionError('no old preparation/replay/external side effect')
    monkeypatch.setattr(model.short,'_evaluate',counted);monkeypatch.setattr(model.short.old.leaf_area,'initialize_leaf_area',new_only)
    for owner,name in [(model.resume,'prepare_context'),(model.resume,'advance_chunk'),(model.resume,'start'),(model.short,'_prepare'),
        (model.short,'integrate'),(model.arithmetic.resume,'prepare_context'),(model.arithmetic.resume,'advance_chunk'),
        (model.short.old.leaf_area,'normalize_leaf_area_state'),(socket,'socket'),(subprocess,'Popen'),(psycopg,'connect'),
        (job_store,'connect_app'),(model.binding.MorphologyBlobStore,'put')]:monkeypatch.setattr(owner,name,forbidden)
    original=os.open
    def readonly(path,flags,*a,**k):
        if flags&(os.O_WRONLY|os.O_RDWR|os.O_CREAT|os.O_TRUNC|os.O_APPEND):return forbidden()
        return original(path,flags,*a,**k)
    monkeypatch.setattr(os,'open',readonly)
    r=model.apply_leaf_births(**kw)
    assert len(calls)==2 and list(calls[0])==json.loads(kw['raw_checkpoint'])['last_confirmed']['state']and list(calls[1])==r['after_sample']['state']
    assert len(initializations)==2 and set(initializations)==names


@pytest.mark.parametrize('kind',['own_code','late_dependency','late_source','late_profile','after_domain','after_unexpected'])
def test_code_source_profile_fences_and_atomic_failure(stored,monkeypatch,kind):
    from types import MappingProxyType
    kw=setup(stored[0]);before=kw['raw_checkpoint'];evaluate=model.short._evaluate;ran=[];profile=kw['context']._profiles[0];original_values=profile.values
    if kind=='own_code':monkeypatch.setattr(model,'CODE_SHA256','0'*64)
    if kind=='late_dependency':
        pins=model._pins
        def changed():
            v=pins()
            if ran:v['backend/app/crop_stem_root_funded_leaf_point.py']='0'*64
            return v
        monkeypatch.setattr(model,'_pins',changed)
    if kind=='late_source':
        bind=model.binding.bind_initial_stem_carbon
        def withdrawn(*a,**k):
            v=bind(*a,**k)
            if ran:v['source_rights']['stem']['display']=False
            return v
        monkeypatch.setattr(model.binding,'bind_initial_stem_carbon',withdrawn)
    def after(p,y,profiles):
        result=evaluate(p,y,profiles)
        if len(p['leaves'])>len(kw['context'].program['leaves']):
            ran.append(1)
            if kind=='late_profile':object.__setattr__(profile,'values',MappingProxyType({**dict(original_values),'cLeafG':.4}))
            if kind=='after_domain':raise ValueError('after domain failure')
            if kind=='after_unexpected':raise RuntimeError('unexpected operator failure')
        return result
    monkeypatch.setattr(model.short,'_evaluate',after)
    try:
        with pytest.raises(RuntimeError if kind=='after_unexpected'else model.LeafBirthHold):model.apply_leaf_births(**kw)
        assert kw['raw_checkpoint']==before
    finally:object.__setattr__(profile,'values',original_values)


@pytest.mark.parametrize('case',[0,1])
def test_result_copies_false_rights_and_external_checkpoint_digest(stored,case):
    kw=setup(stored[case]);kw['inputs']['rights']['redistribute']=True
    r=model.apply_leaf_births(**kw);assert r['redistribution_authorized']is False
    r['after_program']['stem_root_compartments'][0]['initial_carbon']['value']=0
    r['after_anchors'][0]['value']=999;r['before_checkpoint']['last_confirmed']['state'][0]=0
    again=model.apply_leaf_births(**kw);assert again['before_checkpoint']==json.loads(kw['raw_checkpoint'])
    kw['expected_sha256']='0'*64
    with pytest.raises(model.LeafBirthHold,match='CHECKPOINT_HOLD'):model.apply_leaf_births(**kw)


def test_new_initial_area_request_tolerance_receipt_preserves_old_D0(stored):
    kw=setup(stored[0],1,count=1);area=kw['inputs']['events'][0]['leaf']['initial_area']['value'];requested=area*(1+5e-13)
    kw['inputs']['events'][0]['leaf']['initial_area']['value']=requested;r=model.apply_leaf_births(**kw)
    receipt=r['birth_receipts'][0]['initialization']['state'];assert receipt['area']['value']==area and receipt['anchor']['requested_area']['value']==requested
    n=len(kw['context'].program['leaves']);assert r['after_sample']['curve_invariant_changes'][:n]==json.loads(kw['raw_checkpoint'])['last_confirmed']['curve_invariant_changes']
    kw['inputs']['events'][0]['leaf']['initial_area']['value']=area*1.00001
    with pytest.raises(model.LeafBirthHold,match='INITIAL_AREA_HOLD'):model.apply_leaf_births(**kw)


@pytest.mark.parametrize('order',['stem_then_leaf','leaf_then_stem'])
def test_material_cores_compose_on_changed_inventory_without_old_token_fabrication(stored,order):
    kw=setup(stored[0],1,count=1);stem_kw=stem_setup(stored[0],1,count=1)
    p=json.loads(kw['context']._program);y=json.loads(kw['raw_checkpoint'])['last_confirmed']['state'];profiles=model.resume._profiles(kw['context']);anchors=json.loads(kw['context']._seed)['evaluation']['curve_residuals']
    if order=='stem_then_leaf':
        first=model.stem._jump(p,y,profiles,stem_kw['inputs']['events']);events=deepcopy(kw['inputs']['events']);events[0]['parent_internode_id']='declared-new-internode-0'
        second=model._jump(first['program'],first['state'],profiles,events,anchors)
        n=len(second['program']['leaves']);assert second['state'][106+3*n:]==first['state'][106+3*len(p['leaves']):]
    else:
        first=model._jump(p,y,profiles,kw['inputs']['events'],anchors)
        second=model.stem._jump(first['program'],first['state'],profiles,stem_kw['inputs']['events'])
        assert second['state'][1:len(first['state'])]==first['state'][1:]
    assert len(second['program']['leaves'])==len(p['leaves'])+1 and len(second['program']['stem_root_compartments'])==len(p['stem_root_compartments'])+1
    assert all(abs(v['residual']['value'])<=v['budget']['value']for v in second['balances'].values())


@pytest.mark.parametrize('count',[125,509,510])
def test_leaf_inventory_capacity_and_original_lower_byte_cap(stored,count):
    kw=setup(stored[0],count=count)
    for event in kw['inputs']['events']:event['leaf']['initial_carbon']['value']=.001
    if count==125:
        r=model.apply_leaf_births(**kw);assert len(r['after_program']['leaves'])==128
        assert r['after_sample']['state'][106+3*128:]==json.loads(kw['raw_checkpoint'])['last_confirmed']['state'][115:]
    else:
        with pytest.raises(model.LeafBirthHold,match='CAPACITY_HOLD'):model.apply_leaf_births(**kw)
