from copy import deepcopy
from fractions import Fraction

from test_crop_supply_morphology_newborn_candidate import current,profiles,prepared,pending,calculated,adopted,trajectory,post_pending,post_calculated


def point_inputs(row,candidate,with_leaf=True,length=0.,cost=1e-6,temperature=22.):
    from app import crop_supply_morphology_newborn_point as model
    context,_,digest,_=row;data=model.resume._context(context);p=data['program'];event=model.core.source_event(data,candidate)
    v={'schema_version':'supply-morphology-newborn-material-point-input-v1','input_id':'own-newborn-successor-point-QA','origin':'synthetic','policy':model.POLICY,
       'parameter_source':'own_declared_synthetic_assumptions','parameter_revision':'own-QA-compatible-successor-seed-v1','reviewer':'native-software-QA-not-cultivar-validation',
       'context_sha256':context.root_sha256,'checkpoint_sha256':digest,'candidate_sha256':candidate['calculation_sha256'],
       'initial_binding_sha256':data['origin_data']['source_data']['source_snapshot']['manifest']['initial_binding_sha256'],'at_elapsed_seconds_exact':deepcopy(candidate['at']['elapsed_seconds_exact']),
       'model_floor_area':deepcopy(p['model_floor_area']),'source_event_id':event['source_event_id'],'source_threshold_sequence':event['sequence'],'source_threshold_exact':event['threshold_exact'],
       'parent_internode_id':data['organs']['internodes'][-1]['compartment_id'],'internode':{'declaration':{'compartment_id':event['internode_id'],'kind':'internode','initial_carbon':{'value':.25,'unit':model.core.MASS},'sink_weight':{'value':1.,'unit':'1'},'carbon_removal':{'value':0.,'unit':model.core.MASS+'/s'}},'initial_length':{'value':length,'unit':'m'},'construction_cost':{'value':cost,'unit':'mg_CH2O/m_internode'}},
       'leaf':None,'rights':deepcopy(data['point']['inputs']['rights'])}
    if with_leaf:
        declaration=deepcopy(p['leaves'][0]);declaration.update(leaf_id=event['leaf_id'],thermal_age={'value':0.,'unit':'degC_day'},initial_area=model.core.arithmetic.resume.short.old.leaf_area._area_at(Fraction(0),declaration['curve']),initial_carbon={'value':.125,'unit':model.core.MASS},sink_weight={'value':1.,'unit':'1'})
        v['leaf']={'declaration':declaration,'incoming_temperature':{'value':temperature,'unit':'degC'},'construction_cost':{'value':cost,'unit':'mg_CH2O/m2_leaf'}}
    return v


def test_actual_successor_funds_once_keeps_old_newborn_and_geometry_origins(request):
    from app import crop_supply_morphology_newborn_point as model
    row=request.getfixturevalue('post_pending');before=request.getfixturevalue('post_calculated');context,raw,digest,_=row;v=point_inputs(row,before)
    out=request.getfixturevalue('funded')
    data=model.resume._context(context);p=data['program'];n=len(p['leaves']);m=len(p['stem_root_compartments']);h=len(data['organs']['internodes']);size=106+3*n+m;nn=n+1;nh=h+1;newsize=106+3*nn+m+1;y=before['dense_candidate']['state'];z=out['after_state']
    assert out['source_event']['sequence']==before['source_prefix']['schedule']['next_sequence']>data['point']['source_event']['sequence']
    assert z[newsize+nh+h]==0. and z[newsize+h]==0. and out['after_rates'][newsize+nh+h]>0
    assert z[newsize:newsize+h]==y[size:size+h]and z[newsize+nh:newsize+nh+h]==y[size+h:]
    assert len(out['post_point_global_ledgers_preview'])==84 and out['point_order']==['internode','leaf']
    assert out['after_geometry_baselines']['internodes'][-2]['origin_geometry']['value']==0. and z[newsize+nh+h-1]>0.
    assert out['after_geometry_baselines']['internodes'][-1]['origin_geometry']['value']==0.
    assert out['after_birth_baselines']['leaf'][:-1]==data['seed']['birth_bases']['leaf']
    assert out['schedule_adoption']=='not_performed'and out['integrator_checkpoint']is None and out['G0_G4']=='not_assessed'


import json
import pytest


@pytest.fixture(scope='module')
def funded(post_pending,post_calculated):
    from app import crop_supply_morphology_newborn_point as model
    ctx,raw,digest,_=post_pending
    return model.apply_fractional_material_point(ctx,raw,expected_sha256=digest,time_tolerance_seconds_exact={'numerator':'1','denominator':'1000','unit':'s'},inputs=point_inputs(post_pending,post_calculated))


@pytest.fixture(scope='module')
def point_cases(post_pending,post_calculated,funded):
    from app import crop_supply_morphology_newborn_point as model
    ctx,raw,digest,_=post_pending;rows=[]
    for with_leaf,length in [(False,0.),(False,.01),(True,0.),(True,.01)]:
        v=point_inputs(post_pending,post_calculated,with_leaf=with_leaf,length=length)
        out=funded if with_leaf and length==0. else model.apply_fractional_material_point(ctx,raw,expected_sha256=digest,time_tolerance_seconds_exact={'numerator':'1','denominator':'1000','unit':'s'},inputs=v)
        rows.append((v,out))
    return rows


@pytest.mark.parametrize('index',range(4))
def test_exact_funding_heat_existing_coordinates_and_compatibility(point_cases,index):
    from decimal import Decimal,localcontext
    from app import crop_supply_morphology_newborn_point as model
    v,out=point_cases[index];before=out['before_candidate']['dense_candidate'];y=before['state'];z=out['after_state'];old_n=len(out['after_program']['leaves'])-(v['leaf']is not None);new_n=len(out['after_program']['leaves']);new_m=len(out['after_program']['stem_root_compartments']);old_m=new_m-1;new_h=len(out['after_organs']['internodes']);old_h=new_h-1;size=106+3*old_n+old_m;new_size=106+3*new_n+new_m
    with localcontext()as precision:
        precision.prec=200;D=Decimal.from_float;buffer=y[0]
        for kind,costkey in [('internode','cStemG'),*([('leaf','cLeafG')]if v['leaf']is not None else[])]:
            part=out['flow_components'][kind];mass=part['structural_carbon']['value'];cost=out['growth_costs'][costkey]
            assert part['growth_respiration']['value']==float(D(mass)*D(cost))and part['buffer_debit']['value']==float(D(mass)*(1+D(cost)))
            buffer=float(D(buffer)-D(part['buffer_debit']['value']))
        assert z[0]==buffer
        if v['leaf']is not None:
            area=v['leaf']['declaration']['initial_area']['value'];params=out['after_program']['scenario']['parameters'];capacity=float(D(params['leaf_heat_capacity']['value'])*D(area)/D(v['model_floor_area']['value']));heat=float(D(capacity)*(D(v['leaf']['incoming_temperature']['value'])-D(params['reference_temperature']['value'])))
            assert out['flow_components']['leaf']['capacity_in']['value']==capacity and out['flow_components']['leaf']['sensible_in']['value']==heat and z[103]==float(D(y[103])+D(heat))
        else:assert z[103]==y[103]and out['after_derived']['canopy_capacity']==before['derived']['canopy_capacity']
    assert z[1:103]==y[1:103]and z[104:106]==y[104:106]
    for a,b,count in [(106,106,old_n),(106+old_n,106+new_n,old_n),(106+2*old_n,106+2*new_n,old_n),(106+3*old_n,106+3*new_n,old_m),(size,new_size,old_h),(size+old_h,new_size+new_h,old_h)]:assert z[b:b+count]==y[a:a+count]
    for row in out['seed_compatibility'].values():
        assert model.X(row['available_minus_required_exact'])==model.X(row['available_carbon_exact'])-model.X(row['construction_required_exact'])>=0 and model.X(row['compatibility_budget_exact'])==0
    assert z[-1]==v['internode']['initial_length']['value']and len(out['post_point_global_ledgers_preview'])==(84 if v['leaf']is not None else 79)


@pytest.mark.parametrize('index',range(4))
def test_actual_geometry_origins_global_equations_and_unified_lifetime(point_cases,index):
    from app import crop_supply_morphology_newborn_point as model
    v,out=point_cases[index];before=out['before_candidate']['dense_candidate'];p=out['after_program'];z=out['after_state'];n=len(p['leaves']);h=len(out['after_organs']['internodes']);size=out['after_state_layout']['original_prefix_length'];life=out['post_point_lifetime_transfers_exact_preview'];F=model.F;X=model.X;floor=F(p['model_floor_area']['value']);indices={r['compartment_id']:i for i,r in enumerate(p['stem_root_compartments'])}
    for name,q in life.items():assert X(q)==(X(before['pending_lifetime_transfers_exact'][name])if name in before['pending_lifetime_transfers_exact']else 0)
    for kind,key,offset,rows,idkey in [('leaf','leaves',106+n,out['after_organs']['leaves'],'leaf_id'),('internode','internodes',size+h,out['after_organs']['internodes'],'compartment_id')]:
        for i,(node,origin)in enumerate(zip(rows,out['after_geometry_baselines'][key],strict=True)):
            assert node[idkey]==origin[idkey];prefix=f'{kind}_{i}';stock_index=i if kind=='leaf'else indices[node[idkey]];inflow=f'{"leaf"if kind=="leaf"else"stem_root"}_{stock_index}_inflow';cost=F(out['after_costs'][key][i])
            equations={'geometry':F(z[offset+i])-F(origin['origin_geometry']['value'])-X(life[prefix+'_realized']),'partition':X(life[prefix+'_extension'])+X(life[prefix+'_unmapped'])-X(life[inflow])+X(origin['origin_lifetime_inflow_exact']),'construction':X(life[prefix+'_extension'])-cost*X(life[prefix+'_realized'])/floor}
            for suffix,residual in equations.items():assert residual==X(out['post_point_global_ledgers_preview'][prefix+'_'+suffix]['residual_exact'])
    assert all(abs(X(r['residual_exact']))<=X(r['budget_exact'])for r in out['point_balances'].values())
    assert all(abs(X(r['residual_exact']))<=X(r['budget_exact'])for r in out['post_point_global_ledgers_preview'].values())


def test_stateless_retry_has_identical_bytes_and_preserves_caller_sources(post_pending,post_calculated,funded):
    from app import crop_supply_morphology_newborn_point as model
    ctx,raw,digest,_=post_pending;v=point_inputs(post_pending,post_calculated);original=model.resume._canonical(v)
    out=model.apply_fractional_material_point(ctx,raw,expected_sha256=digest,time_tolerance_seconds_exact={'numerator':'1','denominator':'1000','unit':'s'},inputs=v)
    assert model.resume._canonical(out)==model.resume._canonical(funded)and model.resume._canonical(v)==original


def test_actual_candidate_and_material_calls_do_not_use_old_entry_or_reinitialize_existing_leaf(post_pending,post_calculated,funded,monkeypatch):
    from app import crop_supply_morphology_newborn_point as model
    ctx,raw,digest,_=post_pending;v=point_inputs(post_pending,post_calculated);calls={'stage':0,'fund':0,'initialize':[]};stage=model.core.stage.evaluate;fund=model.core.arithmetic._fund;leaf_area=model.core.arithmetic.resume.short.old.leaf_area;initialize=leaf_area.initialize_leaf_area
    def count_stage(*a,**k):calls['stage']+=1;return stage(*a,**k)
    def count_fund(*a,**k):calls['fund']+=1;return fund(*a,**k)
    def count_init(*a,**k):
        out=initialize(*a,**k);calls['initialize'].append(out['state']['leaf_id']);return out
    def forbidden(*a,**k):raise AssertionError('no old public point/biology, CP adoption or integration')
    for module,name in [(model.resume.resume,'_rhs'),(model.source.stock.short,'_evaluate'),(model.resume,'advance_chunk'),(model.resume,'restore_checkpoint'),(model.resume,'start'),(model.resume,'_seal'),(model.resume.owner,'prepare_context'),(model.resume.owner,'restore_checkpoint'),(model.resume.owner.point,'apply_fractional_material_point'),(model.source,'adopt_first'),(model.source,'adopt_successor'),(model.core.material.candidate,'calculate_next_event_candidate')]:monkeypatch.setattr(module,name,forbidden)
    monkeypatch.setattr(model.core.stage,'evaluate',count_stage);monkeypatch.setattr(model.core.arithmetic,'_fund',count_fund);monkeypatch.setattr(leaf_area,'initialize_leaf_area',count_init)
    out=model.apply_fractional_material_point(ctx,raw,expected_sha256=digest,time_tolerance_seconds_exact={'numerator':'1','denominator':'1000','unit':'s'},inputs=v)
    assert out==funded and calls=={'stage':36,'fund':2,'initialize':[out['source_event']['leaf_id']]}


@pytest.mark.parametrize('failure',['schema','context','checkpoint','rights','extra','floor_unit'])
def test_invalid_authority_and_schema_hold_before_rhs(post_pending,post_calculated,monkeypatch,failure):
    from app import crop_supply_morphology_newborn_point as model
    ctx,raw,digest,_=post_pending;v=point_inputs(post_pending,post_calculated)
    if failure=='schema':v['schema_version']='old'
    elif failure=='context':v['context_sha256']='0'*64
    elif failure=='checkpoint':v['checkpoint_sha256']='0'*64
    elif failure=='rights':v['rights']['use']=False
    elif failure=='extra':v['invented']=1
    else:v['model_floor_area']['unit']='m2'
    def forbidden(*a,**k):raise AssertionError('invalid source cannot run actual RHS')
    monkeypatch.setattr(model.core.stage,'evaluate',forbidden)
    with pytest.raises(model.SupplyPointHold):model.apply_fractional_material_point(ctx,raw,expected_sha256=digest,time_tolerance_seconds_exact={'numerator':'1','denominator':'1000','unit':'s'},inputs=v)


@pytest.mark.parametrize('failure',['candidate','event','time'])
def test_actual_next_candidate_identity_and_time_are_required(post_pending,post_calculated,failure):
    from app import crop_supply_morphology_newborn_point as model
    ctx,raw,digest,_=post_pending;v=point_inputs(post_pending,post_calculated)
    if failure=='candidate':v['candidate_sha256']='0'*64
    elif failure=='event':v['source_event_id']='shoot-event:old-first-event'
    else:v['at_elapsed_seconds_exact']={'numerator':'296','denominator':'1','unit':'s'}
    with pytest.raises(model.SupplyPointHold):model.apply_fractional_material_point(ctx,raw,expected_sha256=digest,time_tolerance_seconds_exact={'numerator':'1','denominator':'1000','unit':'s'},inputs=v)


@pytest.mark.parametrize('kind',['internode','leaf'])
def test_incompatible_declared_seed_is_not_corrected_or_funded(post_pending,post_calculated,monkeypatch,kind):
    from app import crop_supply_morphology_newborn_point as model
    ctx,raw,digest,_=post_pending;v=point_inputs(post_pending,post_calculated,length=.01 if kind=='internode'else 0.);v[kind]['construction_cost']['value']=1e12;original=model.resume._canonical(v)
    def forbidden(*a,**k):raise AssertionError('incompatible seed cannot be funded')
    monkeypatch.setattr(model.core.arithmetic,'_fund',forbidden)
    with pytest.raises(model.SupplyPointHold,match='SEED_COMPATIBILITY_HOLD'):model.apply_fractional_material_point(ctx,raw,expected_sha256=digest,time_tolerance_seconds_exact={'numerator':'1','denominator':'1000','unit':'s'},inputs=v)
    assert model.resume._canonical(v)==original


def test_insufficient_actual_buffer_returns_no_partial_point(post_pending,post_calculated):
    from app import crop_supply_morphology_newborn_point as model
    ctx,raw,digest,_=post_pending;v=point_inputs(post_pending,post_calculated,with_leaf=False);v['internode']['declaration']['initial_carbon']['value']=1e12;original=model.resume._canonical(v)
    with pytest.raises(model.SupplyPointHold):model.apply_fractional_material_point(ctx,raw,expected_sha256=digest,time_tolerance_seconds_exact={'numerator':'1','denominator':'1000','unit':'s'},inputs=v)
    assert model.resume._canonical(v)==original


@pytest.mark.parametrize('failure',['profile','source','code','inputs','tolerance','runtime'])
def test_late_failure_returns_no_material_output(post_pending,post_calculated,monkeypatch,failure):
    from pathlib import Path
    from stat import S_IMODE
    from app import crop_supply_morphology_newborn_point as model
    ctx,raw,digest,_=post_pending;v=point_inputs(post_pending,post_calculated);tol={'numerator':'1','denominator':'1000','unit':'s'};evaluate=model.core.stage.evaluate;calls=[];profile=ctx._origin._source._source._root._profiles[0];original=profile.filtered_temperature_bounds;directory=Path(ctx._origin._source._source._directories[0]);mode=S_IMODE(directory.stat().st_mode)
    def changed(*a,**k):
        calls.append(1)
        if len(calls)==35 and failure=='runtime':raise RuntimeError('own unexpected material stage')
        out=evaluate(*a,**k)
        if len(calls)==36:
            if failure=='profile':object.__setattr__(profile,'filtered_temperature_bounds',(1.,2.))
            elif failure=='source':directory.chmod(0)
            elif failure=='code':monkeypatch.setattr(model,'CODE_SHA256','0'*64)
            elif failure=='inputs':v['rights']['display']=False
            elif failure=='tolerance':tol['denominator']='1000000'
        return out
    monkeypatch.setattr(model.core.stage,'evaluate',changed)
    try:
        with pytest.raises(RuntimeError if failure=='runtime'else model.SupplyPointHold):model.apply_fractional_material_point(ctx,raw,expected_sha256=digest,time_tolerance_seconds_exact=tol,inputs=v)
    finally:object.__setattr__(profile,'filtered_temperature_bounds',original);directory.chmod(mode)


@pytest.mark.parametrize('failure',['input_cap','checkpoint_hash','output_cap'])
def test_bounded_material_packets_and_trusted_checkpoint_hash(post_pending,post_calculated,monkeypatch,failure):
    from app import crop_supply_morphology_newborn_point as model
    ctx,raw,digest,_=post_pending;v=point_inputs(post_pending,post_calculated)
    if failure=='input_cap':v['reviewer']='x'*(model.MAX_INPUT_BYTES+1)
    elif failure=='checkpoint_hash':raw+=b' '
    else:monkeypatch.setattr(model,'MAX_BYTES',1)
    with pytest.raises(model.SupplyPointHold):model.apply_fractional_material_point(ctx,raw,expected_sha256=digest,time_tolerance_seconds_exact={'numerator':'1','denominator':'1000','unit':'s'},inputs=v)
