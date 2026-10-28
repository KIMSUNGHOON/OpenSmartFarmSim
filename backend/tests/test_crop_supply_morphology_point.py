from copy import deepcopy
from fractions import Fraction

import pytest

from test_crop_supply_morphology_candidate import current,profiles,prepared,pending,calculated


def test_zero_length_stage_uses_actual_state_without_clamping_or_changing_positive_case(prepared):
    from app import crop_supply_morphology_birth_stage as stage
    from app import crop_supply_morphology_resume as resume
    data=resume._context(prepared);args=(data['program'],data['initial']['state'],data['initial']['organs'],data['costs'],data['profiles'])
    positive=resume.bound.stage.evaluate(*args)
    assert stage.evaluate(*args)==positive
    y=list(args[1]);size=data['initial']['state_layout']['original_prefix_length'];h=len(args[2]['internodes']);y[size+h]=0.
    assert stage.evaluate(args[0],y,*args[2:])==positive and y[size+h]==0.
    y[size+h]=-1.
    with pytest.raises(ValueError):stage.evaluate(args[0],y,*args[2:])


def point_inputs(pending,calculated,with_leaf=True,length=0.,cost=1e-6,temperature=22.):
    from app import crop_supply_morphology_point as model
    ctx,raw,digest,_=pending;data=model.resume._context(ctx);p=data['program'];event=model.core.source_event(data,calculated)
    value={'schema_version':'supply-morphology-material-point-input-v1','input_id':'own-supply-point-QA','origin':'synthetic','policy':model.POLICY,
        'parameter_source':'own_declared_synthetic_assumptions','parameter_revision':'own-QA-seed-construction-v1',
        'context_sha256':ctx.root_sha256,'checkpoint_sha256':digest,'candidate_sha256':calculated['calculation_sha256'],
        'initial_binding_sha256':data['source_data']['source_snapshot']['manifest']['initial_binding_sha256'],
        'at_elapsed_seconds_exact':deepcopy(calculated['at']['elapsed_seconds_exact']),'model_floor_area':deepcopy(p['model_floor_area']),
        'source_event_id':event['source_event_id'],'source_threshold_sequence':event['sequence'],'source_threshold_exact':deepcopy(event['threshold_exact']),
        'parent_internode_id':[v['compartment_id']for v in p['stem_root_compartments']if v['kind']=='internode'][-1],
        'internode':{'declaration':{'compartment_id':event['internode_id'],'kind':'internode','initial_carbon':{'value':.25,'unit':model.core.MASS},'sink_weight':{'value':1.,'unit':'1'},'carbon_removal':{'value':0.,'unit':model.core.MASS+'/s'}},
            'initial_length':{'value':length,'unit':'m'},'construction_cost':{'value':cost,'unit':'mg_CH2O/m_internode'}},
        'leaf':None,'rights':deepcopy(data['source_data']['point']['inputs']['rights']),'reviewer':'native-software-QA-not-cultivar-validation'}
    if with_leaf:
        declaration=deepcopy(p['leaves'][0]);declaration.update(leaf_id=event['leaf_id'],thermal_age={'value':0.,'unit':'degC_day'},initial_area=model.core.arithmetic.resume.short.old.leaf_area._area_at(Fraction(0),declaration['curve']),
            initial_carbon={'value':.125,'unit':model.core.MASS},sink_weight={'value':1.,'unit':'1'})
        value['leaf']={'declaration':declaration,'incoming_temperature':{'value':temperature,'unit':'degC'},'construction_cost':{'value':cost,'unit':'mg_CH2O/m2_leaf'}}
    return value


def run_point(pending,calculated,**kwargs):
    from app import crop_supply_morphology_point as model
    ctx,raw,digest,_=pending
    return model.apply_fractional_material_point(ctx,raw,expected_sha256=digest,time_tolerance_seconds_exact={'numerator':'1','denominator':'1000','unit':'s'},inputs=point_inputs(pending,calculated,**kwargs))


def test_actual_new_law_material_point_keeps_existing_geometry_and_charges_seed_once(pending,calculated):
    from app import crop_supply_morphology_point as model
    ctx,raw,digest,_=pending;before=calculated['dense_candidate'];out=run_point(pending,calculated)
    p=model.resume._context(ctx)['program'];n=len(p['leaves']);m=len(p['stem_root_compartments']);h=len(model.resume._context(ctx)['initial']['organs']['internodes']);size=106+3*n+m
    nn,nm,nh=n+1,m+1,h+1;newsize=106+3*nn+nm;y=before['state'];z=out['after_state']
    assert len(z)==newsize+2*nh and z[1:103]==y[1:103]and z[104:106]==y[104:106]
    assert z[106:106+n]==y[106:106+n]and z[106+nn:106+nn+n]==y[106+n:106+2*n]
    assert z[106+2*nn:106+2*nn+n]==y[106+2*n:106+3*n]and z[106+3*nn:106+3*nn+m]==y[106+3*n:size]
    assert z[newsize:newsize+h]==y[size:size+h]and z[newsize+nh:newsize+nh+h]==y[size+h:]
    assert z[newsize+nh+h]==0. and z[newsize+h]==0. and out['after_rates'][newsize+nh+h]>0
    assert out['after_state'][newsize-1]==.25 and out['after_state'][106+2*nn+n]==.125
    assert out['before_candidate']==calculated and out['schedule_adoption']=='not_performed'and out['integrator_checkpoint']is None
    assert out['current_validation_RHS_evaluations']==1 and out['candidate_new_RHS_evaluations']==33 and out['point_stage_RHS_evaluations']==2
    assert all(abs(model.X(v['residual_exact']))<=model.X(v['budget_exact'])for v in out['point_balances'].values())
    assert len(out['post_point_global_ledgers_preview'])==74 and out['G0_G4']=='not_assessed'


@pytest.fixture(scope='module',params=[(False,0.),(False,.01),(True,0.),(True,.01)])
def points(pending,calculated,request):
    from app import crop_supply_morphology_point as model
    with_leaf,length=request.param;value=point_inputs(pending,calculated,with_leaf=with_leaf,length=length)
    ctx,raw,digest,_=pending
    out=model.apply_fractional_material_point(ctx,raw,expected_sha256=digest,time_tolerance_seconds_exact={'numerator':'1','denominator':'1000','unit':'s'},inputs=value)
    return value,out


def test_decimal200_funding_and_heat_are_charged_once_at_zero_elapsed_time(points,pending):
    from decimal import Decimal,localcontext
    from app import crop_supply_morphology_point as model
    value,out=points;before=out['before_candidate']['dense_candidate'];p=out['after_program'];components=out['flow_components']
    with localcontext()as precision:
        precision.prec=200;D=Decimal.from_float;buffer=before['state'][0]
        for kind in ['internode','leaf']if value['leaf']is not None else['internode']:
            mass=value['internode']['declaration']['initial_carbon']['value']if kind=='internode'else value['leaf']['declaration']['initial_carbon']['value']
            cost=out['growth_costs']['cStemG'if kind=='internode'else'cLeafG'];resp=float(D(mass)*D(cost));debit=float(D(mass)*(1+D(cost)))
            assert components[kind]['structural_carbon']['value']==mass and components[kind]['growth_respiration']['value']==resp and components[kind]['buffer_debit']['value']==debit
            buffer=float(D(buffer)-D(debit))
        assert out['after_state'][0]==buffer
        if value['leaf']is not None:
            area=out['leaf_receipts'][0]['initialization']['state']['area']['value'];params=p['scenario']['parameters'];capacity=float(D(params['leaf_heat_capacity']['value'])*D(area)/D(p['model_floor_area']['value']))
            heat=float(D(capacity)*(D(value['leaf']['incoming_temperature']['value'])-D(params['reference_temperature']['value'])))
            assert out['point_flows_exact']['capacity_in']==model.Q(Fraction.from_float(capacity),model.core.numeric.CAPACITY)
            assert out['after_state'][103]==float(D(before['state'][103])+D(heat))
        else:assert out['after_state'][103]==before['state'][103]
    assert out['elapsed_seconds_advanced']==model.Q(Fraction(0),'s')and out['integrator_checkpoint']is None and out['global_prefix_adoption']=='not_performed'
    for row in out['seed_compatibility'].values():
        assert model.X(row['compatibility_budget_exact'])==0 and model.X(row['available_minus_required_exact'])>=0
    assert len(out['post_point_global_ledgers_preview'])==(74 if value['leaf']is not None else 69)
    assert all(abs(model.X(v['residual_exact']))<=model.X(v['budget_exact'])for v in out['post_point_global_ledgers_preview'].values())
    for kind in ['leaves','internodes']:
        for row in out['after_organs'][kind]:
            assert abs(model.X(row['represented_minus_clock_exact']))<=model.X(row['age_roundoff_budget_exact'])


def test_stateless_retry_keeps_actual_context_cp_and_original_geometry(points,pending):
    from app import crop_supply_morphology_point as model
    value,out=points;ctx,raw,digest,_=pending;snapshot=model.resume.context_bytes(ctx)
    retry=model.apply_fractional_material_point(ctx,raw,expected_sha256=digest,time_tolerance_seconds_exact={'numerator':'1','denominator':'1000','unit':'s'},inputs=value)
    assert retry==out and model.resume.context_bytes(ctx)==snapshot and model.resume._canonical(out['before_candidate']['source_prefix'])==raw
    assert out['calculation_sha256']==model.resume._hash({k:v for k,v in out.items()if k!='calculation_sha256'})
    assert out['point_stage_RHS_evaluations']==(2 if value['leaf']is not None else 1)
    before=out['before_candidate']['dense_candidate'];h=len(model.resume._context(ctx)['initial']['organs']['internodes']);size=out['after_state_layout']['original_prefix_length']
    for i,row in enumerate(out['after_organs']['internodes'][:-1]):
        assert row['compartment_id']==model.resume._context(ctx)['initial']['organs']['internodes'][i]['compartment_id']
    assert out['after_state'][size+h+1:size+2*h+1]==before['state'][-h:]


@pytest.mark.parametrize('kind',['rights','origin','parameter_source','floor','context','checkpoint'])
def test_invalid_scope_or_source_is_rejected_before_candidate_rhs(pending,calculated,monkeypatch,kind):
    from app import crop_supply_morphology_point as model
    ctx,raw,digest,_=pending;v=point_inputs(pending,calculated)
    if kind=='rights':v['rights']['use']=False
    elif kind=='origin':v['origin']='observed'
    elif kind=='parameter_source':v['parameter_source']='generated_prose'
    elif kind=='floor':v['model_floor_area']['value']*=2
    else:v[kind+'_sha256']='0'*64
    def forbidden(*args,**kwargs):raise AssertionError('invalid input cannot calculate candidate')
    monkeypatch.setattr(model.candidate,'calculate_next_event_candidate',forbidden)
    with pytest.raises(model.SupplyPointHold):model.apply_fractional_material_point(ctx,raw,expected_sha256=digest,time_tolerance_seconds_exact={'numerator':'1','denominator':'1000','unit':'s'},inputs=v)


@pytest.mark.parametrize('kind',['candidate','binding','time','sequence','parent','leaf_id'])
def test_wrong_actual_event_or_candidate_cannot_allocate_a_seed(pending,calculated,kind):
    from app import crop_supply_morphology_point as model
    ctx,raw,digest,_=pending;v=point_inputs(pending,calculated)
    if kind=='candidate':v['candidate_sha256']='0'*64
    elif kind=='binding':v['initial_binding_sha256']='0'*64
    elif kind=='time':v['at_elapsed_seconds_exact']=model.Q(Fraction(1),'s')
    elif kind=='sequence':v['source_threshold_sequence']=True
    elif kind=='parent':v['parent_internode_id']=next(r['compartment_id']for r in model.resume._context(ctx)['program']['stem_root_compartments']if r['kind']=='root_system')
    else:v['leaf']['declaration']['leaf_id']=model.resume._context(ctx)['program']['leaves'][0]['leaf_id']
    with pytest.raises(model.SupplyPointHold):model.apply_fractional_material_point(ctx,raw,expected_sha256=digest,time_tolerance_seconds_exact={'numerator':'1','denominator':'1000','unit':'s'},inputs=v)


@pytest.mark.parametrize('kind',['stem_incompatible','leaf_incompatible','negative_length','wrong_unit','insufficient_funding'])
def test_unfunded_or_incompatible_seed_holds_without_fitting_geometry_or_cost(pending,calculated,kind):
    from app import crop_supply_morphology_point as model
    ctx,raw,digest,_=pending;v=point_inputs(pending,calculated)
    if kind=='stem_incompatible':v['internode']['initial_length']['value']=.01;v['internode']['construction_cost']['value']=1e12
    elif kind=='leaf_incompatible':v['leaf']['construction_cost']['value']=1e12
    elif kind=='negative_length':v['internode']['initial_length']['value']=-.01
    elif kind=='wrong_unit':v['internode']['construction_cost']['unit']='mg_CH2O/m2_leaf'
    else:v['internode']['declaration']['initial_carbon']['value']=1e100
    snapshot=deepcopy(v)
    with pytest.raises(model.SupplyPointHold):model.apply_fractional_material_point(ctx,raw,expected_sha256=digest,time_tolerance_seconds_exact={'numerator':'1','denominator':'1000','unit':'s'},inputs=v)
    assert v==snapshot and model.resume._hash(model.resume._parse(raw,digest,model.resume.MAX_CP))==digest


def test_exact_seed_compatibility_boundary_has_no_epsilon_or_second_charge():
    from math import nextafter
    from app import crop_supply_morphology_point as model
    r=model.core.compatibility(.25,8.,.125,4.,'m')
    assert model.X(r['available_minus_required_exact'])==model.X(r['compatibility_budget_exact'])==0
    assert model.X(r['seed_extension_exact'])==Fraction(1,4)and model.X(r['seed_unmapped_exact'])==0
    with pytest.raises(ValueError):model.core.compatibility(.25,8.,nextafter(.125,1.),4.,'m')


def test_point_never_calls_old_rhs_or_jumps_and_only_new_leaf_is_initialized(pending,calculated,monkeypatch):
    from app import crop_supply_morphology_point as model
    v=point_inputs(pending,calculated);ctx,raw,digest,_=pending;initialized=[];calls=[]
    initialize=model.core.arithmetic.resume.short.old.leaf_area.initialize_leaf_area;evaluate=model.core.stage.evaluate
    def allowed(*,inputs):
        assert inputs['leaf_id']==v['leaf']['declaration']['leaf_id'];initialized.append(1);return initialize(inputs=inputs)
    def counted(*args,**kw):calls.append(1);return evaluate(*args,**kw)
    def forbidden(*args,**kw):raise AssertionError('no old RHS, old point or CP adoption')
    for owner,name in [(model.source.stock.short,'_evaluate'),(model.core.stem,'_jump'),(model.core.leaf,'_jump'),(model.source,'advance_chunk'),(model.source,'adopt_first'),(model.source,'adopt_successor'),(model.resume,'advance_chunk'),(model.resume,'_seal')]:monkeypatch.setattr(owner,name,forbidden)
    monkeypatch.setattr(model.core.arithmetic.resume.short.old.leaf_area,'initialize_leaf_area',allowed)
    monkeypatch.setattr(model.core.stage,'evaluate',counted)
    out=model.apply_fractional_material_point(ctx,raw,expected_sha256=digest,time_tolerance_seconds_exact={'numerator':'1','denominator':'1000','unit':'s'},inputs=v)
    assert len(initialized)==1 and len(calls)==2 and out['point_stage_RHS_evaluations']==2


@pytest.mark.parametrize('failure',['input','tolerance','profile','code','source','runtime'])
def test_late_changes_and_unexpected_failure_never_return_a_point(pending,calculated,monkeypatch,failure):
    from pathlib import Path
    from stat import S_IMODE
    from app import crop_supply_morphology_point as model
    ctx,raw,digest,_=pending;v=point_inputs(pending,calculated);tolerance={'numerator':'1','denominator':'1000','unit':'s'};run=model.core.stage.evaluate;calls=[]
    profile=ctx._source._source._root._profiles[0];original=profile.filtered_temperature_bounds;directory=Path(ctx._source._source._directories[0]);mode=S_IMODE(directory.stat().st_mode)
    def changed(*args,**kwargs):
        if failure=='runtime':raise RuntimeError('unexpected point stage')
        out=run(*args,**kwargs);calls.append(1)
        if len(calls)==2:
            if failure=='input':v['internode']['construction_cost']['value']=2e-6
            elif failure=='tolerance':tolerance['denominator']='1000000'
            elif failure=='profile':object.__setattr__(profile,'filtered_temperature_bounds',(1.,2.))
            elif failure=='code':monkeypatch.setattr(model,'CODE_SHA256','0'*64)
            elif failure=='source':directory.chmod(0)
        return out
    monkeypatch.setattr(model.core.stage,'evaluate',changed)
    try:
        with pytest.raises(RuntimeError if failure=='runtime'else model.SupplyPointHold):model.apply_fractional_material_point(ctx,raw,expected_sha256=digest,time_tolerance_seconds_exact=tolerance,inputs=v)
    finally:object.__setattr__(profile,'filtered_temperature_bounds',original);directory.chmod(mode)


def test_output_byte_bound_never_publishes_a_partial_point(pending,calculated,monkeypatch):
    from app import crop_supply_morphology_point as model
    ctx,raw,digest,_=pending;v=point_inputs(pending,calculated);monkeypatch.setattr(model,'MAX_BYTES',1)
    with pytest.raises(model.SupplyPointHold,match='CAPACITY_HOLD'):model.apply_fractional_material_point(ctx,raw,expected_sha256=digest,time_tolerance_seconds_exact={'numerator':'1','denominator':'1000','unit':'s'},inputs=v)
