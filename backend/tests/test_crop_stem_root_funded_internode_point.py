from copy import deepcopy
from decimal import Decimal,localcontext
from fractions import Fraction
from hashlib import sha256
import json

import pytest

from app import crop_stem_root_funded_internode_point as model
from test_crop_stem_root_initial_binding import stored,profiles,declaration,bind
from test_crop_leaf_carbon_stock_artifact import ACCESS,encoded


def setup(row,cut=0,count=2):
    ctx,cd,sd,cr,sr,index=row;cp=model.resume.start(ctx)
    if cut:cp=model.resume.advance_chunk(ctx,cp,cut)['checkpoint']
    raw=model.resume.checkpoint_bytes(ctx,cp);initial=bind(row);at=Fraction.from_float(ctx.manifest['numerical']['step_seconds'])*cut
    parent=[r for r in ctx.program['stem_root_compartments']if r['kind']=='internode'][-1]['compartment_id']
    events=[{'event_id':'declared-new-event-'+str(i),'parent_internode_id':parent,'compartment':{
        'compartment_id':'declared-new-internode-'+str(i),'kind':'internode',
        'initial_carbon':{'value':.25*(i+1),'unit':'mg_CH2O/m2_floor'},'sink_weight':{'value':1.,'unit':'1'},
        'carbon_removal':{'value':0.,'unit':'mg_CH2O/m2_floor/s'}}}for i in range(count)]
    inputs={'schema_version':'stem-root-funded-internode-point-input-v1','input_id':'declared-internode-point','origin':'synthetic',
        'policy':'explicit-new-internode-carbon-from-buffer-v1','context_sha256':ctx.root_sha256,'checkpoint_sha256':cp.sha256,
        'initial_binding_sha256':sha256(encoded(initial)).hexdigest(),'at_elapsed_seconds_exact':{
            'numerator':str(at.numerator),'denominator':str(at.denominator),'unit':'s'},'model_floor_area':ctx.program['model_floor_area'],
        'events':events,'rights':deepcopy(initial['source_rights']['declaration']),'reviewer':'native-software-QA-not-agricultural-validation'}
    return {'context':ctx,'raw_checkpoint':raw,'expected_sha256':cp.sha256,'crop_directory':cd,'stem_directory':sd,'access':ACCESS,
        'crop_root_sha256':cr,'stem_root_sha256':sr,'stem_start_index':index,'binding_declaration':declaration(row),'inputs':inputs}


@pytest.mark.parametrize('case',range(6))
@pytest.mark.parametrize('cut',[0,1])
def test_new_stock_point_preserves_original_current_state_and_all_past_ledgers(stored,case,cut):
    kw=setup(stored[case],cut);before=json.loads(kw['raw_checkpoint']);old=before['last_confirmed']['state'];inputs=deepcopy(kw['inputs'])
    result=model.apply_internode_births(**kw);after=result['after_sample']['state']
    assert after[1:len(old)]==old[1:] and after[len(old):]==[.25,.5] and after[0]<old[0]
    assert result['before_checkpoint']==before and result['after_sample']['elapsed_seconds']==before['last_confirmed']['elapsed_seconds']
    assert result['after_sample']['curve_invariant_changes']==before['last_confirmed']['curve_invariant_changes']
    assert result['after_program']['leaves']==json.loads(kw['context']._program)['leaves']
    assert result['after_program']['stem_root_compartments'][:-2]==json.loads(kw['context']._program)['stem_root_compartments']
    assert result['after_sample']['derived']['canopy_capacity']==before['last_confirmed']['derived']['canopy_capacity']
    assert result['checkpoint']is None and result['elapsed_steps_advanced']==0 and result['checkpoint_validation_stage_evaluations']==1 and result['after_stage_evaluations']==1
    assert result['G0_G4']=='not_assessed'and result['time_kind']=='synthetic_model_clock_not_observation'
    assert result['redistribution_authorized']is False and result['timing_status']=='declared_at_validated_checkpoint_not_threshold_detection'
    assert kw['inputs']==inputs and model.apply_internode_births(**kw)==result
    assert all(abs(v['residual']['value'])<=v['budget']['value']for v in result['balances'].values())


@pytest.mark.parametrize('masses',[(1.,),(.1,.2),(3.5,2.25,.125)])
def test_independent_decimal_original_stem_cost_and_point_balances(stored,masses):
    kw=setup(stored[0],1,len(masses))
    for event,C in zip(kw['inputs']['events'],masses,strict=True):event['compartment']['initial_carbon']['value']=C
    result=model.apply_internode_births(**kw);before=result['before_checkpoint']['last_confirmed']['state'];after=result['after_sample']['state'];n=len(kw['context'].program['leaves'])
    with localcontext()as c:
        c.prec=110;D=Decimal.from_float;total=sum(map(D,masses),Decimal(0));cost=D(.3)
        assert result['growth_cost']['value']==.3 and result['growth_cost']['parameter']=='cStemG'
        for key,expected in [('structural_carbon',float(total)),('growth_respiration',float(cost*total)),('buffer_debit',float((1+cost)*total))]:
            assert result['point_flows'][key]['value']==expected
        assert after[0]==float(D(before[0])-D(float((1+cost)*total)))
        whole=lambda y:D(y[0])+sum(map(D,y[3:53]),Decimal(0))+sum(map(D,y[106+2*n:]),Decimal(0))
        residual=whole(after)-whole(before)+D(float(cost*total))
        assert abs(residual)<=D(result['balances']['whole_carbon']['budget']['value'])


@pytest.mark.parametrize('change',[
    lambda v:v.update(origin='observed'),lambda v:v.update(extra=1),lambda v:v.update(policy='free_growth'),
    lambda v:v.update(initial_binding_sha256='0'*64),lambda v:v.update(checkpoint_sha256='0'*64),lambda v:v.update(context_sha256='0'*64),
    lambda v:v['at_elapsed_seconds_exact'].update(numerator='2'),lambda v:v['model_floor_area'].update(value=2),
    lambda v:v.update(events=[]),lambda v:v.update(events={}),lambda v:v['events'][0].update(parent_internode_id='invented'),
    lambda v:v['events'][0].update(parent_internode_id='explicit-root'),lambda v:v['events'][0].update(parent_internode_id='declared-new-internode-1'),
    lambda v:v['events'][0]['compartment'].update(kind='root_system'),lambda v:v['events'][0]['compartment'].update(compartment_id='explicit-root'),
    lambda v:v['events'][0]['compartment']['initial_carbon'].update(value=0.),lambda v:v['events'][0]['compartment']['initial_carbon'].update(value=True),
    lambda v:v['events'][0]['compartment']['initial_carbon'].update(value=100000.),lambda v:v['events'][0]['compartment']['initial_carbon'].update(unit='g_DM/plant'),
    lambda v:v['events'][0]['compartment']['sink_weight'].update(value=-1.),lambda v:v['events'][0]['compartment']['carbon_removal'].update(value=-1.),
    lambda v:v['events'][1].update(event_id='declared-new-event-0'),lambda v:v['events'][1]['compartment'].update(compartment_id='declared-new-internode-0'),
    lambda v:v['rights'].update(use=False),lambda v:v['rights'].update(redistribute=1),lambda v:v.update(reviewer='')])
def test_invalid_declaration_parent_time_carbon_and_rights_are_held_without_input_mutation(stored,change):
    kw=setup(stored[0]);change(kw['inputs']);before=deepcopy(kw['inputs']);raw=kw['raw_checkpoint']
    with pytest.raises(model.InternodeBirthHold):model.apply_internode_births(**kw)
    assert kw['inputs']==before and kw['raw_checkpoint']==raw


def test_exactly_two_current_RHS_calls_without_reprepare_replay_or_external_side_effect(stored,monkeypatch):
    import os,socket,subprocess,psycopg
    kw=setup(stored[1],1);calls=[];evaluate=model.short._evaluate
    def counted(p,y,profiles):calls.append(tuple(y));return evaluate(p,y,profiles)
    def forbidden(*a,**k):raise AssertionError('no past replay/initialization/external side effect')
    monkeypatch.setattr(model.short,'_evaluate',counted)
    for owner,name in [(model.resume,'prepare_context'),(model.resume,'advance_chunk'),(model.resume,'start'),
        (model.short,'_prepare'),(model.short,'integrate'),(model.arithmetic.resume,'prepare_context'),
        (model.arithmetic.resume,'advance_chunk'),(model.short.old.leaf_area,'initialize_leaf_area'),
        (socket,'socket'),(subprocess,'Popen'),(psycopg,'connect'),(model.binding.MorphologyBlobStore,'put')]:monkeypatch.setattr(owner,name,forbidden)
    original=os.open
    def readonly(path,flags,*a,**k):
        if flags&(os.O_WRONLY|os.O_RDWR|os.O_CREAT|os.O_TRUNC|os.O_APPEND):return forbidden()
        return original(path,flags,*a,**k)
    monkeypatch.setattr(os,'open',readonly)
    r=model.apply_internode_births(**kw)
    assert len(calls)==2 and list(calls[0])==json.loads(kw['raw_checkpoint'])['last_confirmed']['state'] and list(calls[1])==r['after_sample']['state']


@pytest.mark.parametrize('kind',['own_code','late_dependency','late_source','late_profile','after_domain','after_unexpected'])
def test_code_current_source_and_profile_fences_and_atomic_after_failure(stored,monkeypatch,kind):
    from types import MappingProxyType
    kw=setup(stored[0]);before=kw['raw_checkpoint'];evaluate=model.short._evaluate;ran=[]
    profile=kw['context']._profiles[0];original_values=profile.values
    if kind=='own_code':monkeypatch.setattr(model,'CODE_SHA256','0'*64)
    if kind=='late_dependency':
        pins=model._pins
        def changed():
            r=pins()
            if ran:r['backend/app/crop_stem_root_funded_internode_point.py']='0'*64
            return r
        monkeypatch.setattr(model,'_pins',changed)
    if kind=='late_source':
        bind=model.binding.bind_initial_stem_carbon
        def withdrawn(*a,**k):
            r=bind(*a,**k)
            if ran:r['source_rights']['stem']['display']=False
            return r
        monkeypatch.setattr(model.binding,'bind_initial_stem_carbon',withdrawn)
    def after(p,y,profiles):
        result=evaluate(p,y,profiles)
        if len(y)>len(json.loads(before)['last_confirmed']['state']):
            ran.append(1)
            if kind=='late_profile':object.__setattr__(profile,'values',MappingProxyType({**dict(original_values),'cStemG':.4}))
            if kind=='after_domain':raise ValueError('after domain failure')
            if kind=='after_unexpected':raise RuntimeError('unexpected operator failure')
        return result
    monkeypatch.setattr(model.short,'_evaluate',after)
    try:
        with pytest.raises(RuntimeError if kind=='after_unexpected'else model.InternodeBirthHold):model.apply_internode_births(**kw)
        assert kw['raw_checkpoint']==before
    finally:object.__setattr__(profile,'values',original_values)


@pytest.mark.parametrize('case',[0,1])
def test_result_copies_input_rights_and_checkpoint_raw_digest(stored,case):
    kw=setup(stored[case]);kw['inputs']['rights']['redistribute']=True
    r=model.apply_internode_births(**kw);assert r['redistribution_authorized']is False
    r['after_program']['stem_root_compartments'][0]['initial_carbon']['value']=0
    r['before_checkpoint']['last_confirmed']['state'][0]=0
    again=model.apply_internode_births(**kw);assert again['before_checkpoint']==json.loads(kw['raw_checkpoint'])
    kw['expected_sha256']='0'*64
    with pytest.raises(model.InternodeBirthHold,match='CHECKPOINT_HOLD'):model.apply_internode_births(**kw)


@pytest.mark.parametrize('count',[252,508,509])
def test_resulting_inventory_capacity_preserves_original_lower_output_hold(stored,count):
    kw=setup(stored[0],count=count)
    for event in kw['inputs']['events']:event['compartment']['initial_carbon']['value']=.001
    if count==252:
        r=model.apply_internode_births(**kw);assert len(r['after_program']['stem_root_compartments'])==256
        assert len(r['after_sample']['state'])==106+9+256
    else:
        with pytest.raises(model.InternodeBirthHold,match='CAPACITY_HOLD'):model.apply_internode_births(**kw)


def test_material_core_accepts_validated_changed_inventory_without_old_context_token_fabrication(stored):
    kw=setup(stored[0],cut=1,count=1);first=model.apply_internode_births(**kw)
    events=deepcopy(kw['inputs']['events']);events[0].update(event_id='second-point',parent_internode_id='declared-new-internode-0')
    events[0]['compartment']['compartment_id']='second-internode'
    before=deepcopy(first['after_sample']['state']);program=deepcopy(first['after_program'])
    second=model._jump(program,before,model.resume._profiles(kw['context']),events)
    assert second['state'][1:len(before)]==before[1:] and second['state'][-1]==.25
    assert second['receipts'][0]['parent_internode_id']=='declared-new-internode-0'
    assert second['state'][0]<before[0]and second['program']['stem_root_compartments'][:-1]==program['stem_root_compartments']
    assert all(abs(v['residual']['value'])<=v['budget']['value']for v in second['balances'].values())
    assert first['after_sample']['state']==before and first['after_program']==program
