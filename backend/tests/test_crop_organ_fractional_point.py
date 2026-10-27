from copy import deepcopy
from decimal import Decimal,localcontext
from fractions import Fraction
from hashlib import sha256
import json

import pytest

from app import crop_organ_fractional_point as model
from test_crop_organ_next_threshold import crossings, contexts, roots, stored, profiles, TOLERANCE, frac

stock=model.stock


@pytest.fixture(scope='module')
def candidates(crossings):
    return [(ctx,cp,model.candidate.calculate_fractional_shoot_candidate(ctx,stock.checkpoint_bytes(ctx,cp),expected_sha256=cp.sha256,time_tolerance_seconds_exact=TOLERANCE))for ctx,cp,_ in crossings]


def inputs(row,with_leaf=True,stem_C=.25,leaf_C=.125,temperature=22.):
    ctx,cp,candidate=row;p=ctx.program;event=model.source_event(candidate)
    v={'schema_version':'individual-organ-fractional-material-point-input-v1','input_id':'own-numerical-source-event','origin':'synthetic','policy':model.POLICY,
        'context_sha256':ctx.root_sha256,'checkpoint_sha256':cp.sha256,'candidate_sha256':candidate['calculation_sha256'],
        'initial_binding_sha256':candidate['source_root_certificate']['initial_binding_sha256'],
        'at_elapsed_seconds_exact':deepcopy(candidate['at']['elapsed_seconds_exact']),'model_floor_area':deepcopy(p['model_floor_area']),
        'source_event_id':event['source_event_id'],'source_threshold_sequence':event['sequence'],'source_threshold_exact':deepcopy(event['threshold_exact']),
        'parent_internode_id':[r['compartment_id']for r in p['stem_root_compartments']if r['kind']=='internode'][-1],
        'internode':{'compartment_id':event['internode_id'],'kind':'internode','initial_carbon':{'value':stem_C,'unit':model.MASS},
            'sink_weight':{'value':1.,'unit':'1'},'carbon_removal':{'value':0.,'unit':model.MASS+'/s'}},
        'leaf':None,'rights':deepcopy(candidate['source_root_certificate']['point_rights'][0]),'reviewer':'native-software-QA-not-agricultural-validation'}
    if with_leaf:
        leaf=deepcopy(p['leaves'][0]);area=model.leaf.arithmetic.resume.short.old.leaf_area._area_at(Fraction(0),leaf['curve'])
        leaf.update(leaf_id=event['leaf_id'],thermal_age={'value':0.,'unit':'degC_day'},initial_area=area,initial_carbon={'value':leaf_C,'unit':model.MASS})
        v['leaf']={'declaration':leaf,'incoming_temperature':{'value':temperature,'unit':'degC'}}
    return v


def apply(row,v):
    ctx,cp,_=row
    return model.apply_fractional_material_point(ctx,stock.checkpoint_bytes(ctx,cp),expected_sha256=cp.sha256,time_tolerance_seconds_exact=TOLERANCE,inputs=v)


@pytest.mark.parametrize('case',range(4))
@pytest.mark.parametrize('with_leaf',[False,True])
def test_actual_candidate_new_identity_material_state_and_unchanged_old_inventory(candidates,case,with_leaf):
    row=candidates[case];ctx,cp,candidate=row;v=inputs(row,with_leaf);before=stock.context_bytes(ctx);cpraw=stock.checkpoint_bytes(ctx,cp);rawv=stock._canonical(v)
    result=apply(row,v);p=ctx.program;old=candidate['dense_candidate']['state'];new=result['after_state'];n=len(p['leaves']);m=len(p['stem_root_compartments']);new_n=n+with_leaf
    assert result['at']==candidate['at']and result['before_candidate_sha256']==candidate['calculation_sha256']and result['inputs']==v
    assert new[1:103]==old[1:103]and new[104:106]==old[104:106]and new[0]<old[0]
    assert new[106:106+n]==old[106:106+n]and new[106+new_n:106+new_n+n]==old[106+n:106+2*n]
    assert new[106+2*new_n:106+2*new_n+n]==old[106+2*n:106+3*n]
    assert new[106+3*new_n:106+3*new_n+m]==old[106+3*n:]
    assert new[-1]==.25 and result['after_program']['stem_root_compartments'][:-1]==p['stem_root_compartments']
    assert result['after_program']['stem_root_compartments'][-1]['compartment_id']==model.source_event(candidate)['internode_id']
    assert result['after_anchors'][:n]==json.loads(ctx._seed)['anchors']and len(result['after_anchors'])==new_n
    assert result['before_candidate']['source_prefix']==cp.value and result['integrator_checkpoint']is None and result['schedule_adoption']=='not_performed'
    assert result['redistribution_authorized']is False and result['G0_G4']=='not_assessed'
    assert result['rhs_evaluations']==38+with_leaf and result['elapsed_seconds_advanced']=={'numerator':'0','denominator':'1','unit':'s'}
    if with_leaf:
        assert new[106+n]==0. and new[106+2*new_n+n]==.125
        assert result['leaf_receipts'][0]['parent_internode_id']==result['source_event']['internode_id']
    else:assert new[103]==old[103]and result['after_derived']['canopy_capacity']==candidate['dense_candidate']['derived']['canopy_capacity']
    for r in result['point_balances'].values():assert abs(frac(r['residual_exact']))<=frac(r['budget_exact'])
    assert result['calculation_sha256']==sha256(stock._canonical({k:v for k,v in result.items()if k!='calculation_sha256'})).hexdigest()
    assert stock.context_bytes(ctx)==before and stock.checkpoint_bytes(ctx,cp)==cpraw and stock._canonical(v)==rawv


@pytest.mark.parametrize('temperature',[10.,22.,34.])
@pytest.mark.parametrize('masses',[(.1,.2),(3.5,2.25)])
def test_decimal120_sequential_costs_once_K_U_and_whole_carbohydrate(candidates,temperature,masses):
    row=candidates[0];v=inputs(row,True,*masses,temperature);out=apply(row,v);before=row[2]['dense_candidate'];after=out['after_state'];n=len(row[0].program['leaves']);nn=n+1
    with localcontext()as precision:
        precision.prec=120;D=Decimal.from_float;S,L=map(D,masses);cS=D(.3);cL=D(.28)
        ds=float((1+cS)*S);dl=float((1+cL)*L);rs=float(cS*S);rl=float(cL*L)
        assert after[0]==float(D(float(D(before['state'][0])-D(ds)))-D(dl))
        for kind,expected in [('internode',(float(S),rs,ds)),('leaf',(float(L),rl,dl))]:
            part=out['flow_components'][kind]
            assert [part[k]['value']for k in ('structural_carbon','growth_respiration','buffer_debit')]==list(expected)
        leaf=out['leaf_receipts'][0]['initialization']['state'];area=D(leaf['area']['value']);params=row[0].program
        K=float(D(params['scenario']['parameters']['leaf_heat_capacity']['value'])*area/D(params['model_floor_area']['value']));E=float(D(K)*(D(temperature)-D(params['scenario']['parameters']['reference_temperature']['value'])))
        assert out['point_flows']['capacity_in']['value']==K and after[103]==float(D(before['state'][103])+D(E))
        whole=lambda y,count:D(y[0])+sum(map(D,y[3:53]),Decimal(0))+sum(map(D,y[106+2*count:]),Decimal(0))
        residual=whole(after,nn)-whole(before['state'],n)+D(rs)+D(rl)
        assert abs(residual)<=Decimal(int(out['point_balances']['whole_carbohydrate']['budget_exact']['numerator']))/Decimal(int(out['point_balances']['whole_carbohydrate']['budget_exact']['denominator']))


def test_canonical_internode_identity_matches_original_later_source_not_fixed_time(candidates,stored):
    from test_crop_stem_root_initial_binding import bind
    event=model.source_event(candidates[0][2]);source=bind(stored[2])['stem_selection']['source_state']
    assert event['internode_id']==source['internodes'][-1]['length_state']['clock_state']['internode_id']
    assert candidates[0][2]['at']['elapsed_seconds_exact']['denominator']!='1'


@pytest.mark.parametrize('change',[
    lambda v:v.update(candidate_sha256='0'*64),lambda v:v.update(initial_binding_sha256='0'*64),
    lambda v:v['at_elapsed_seconds_exact'].update(numerator='1',denominator='1'),lambda v:v.update(source_event_id='invented'),
    lambda v:v.update(source_threshold_sequence=True),lambda v:v['source_threshold_exact'].update(numerator='6'),
    lambda v:v.update(parent_internode_id='explicit-root'),lambda v:v.update(parent_internode_id='placeholder'),
    lambda v:v['internode'].update(compartment_id='invented'),lambda v:v['leaf']['declaration'].update(leaf_id='invented'),
    lambda v:v['rights'].update(display=False),lambda v:v['model_floor_area'].update(value=2.),
    lambda v:v['internode']['initial_carbon'].update(unit='g_DM/plant'),lambda v:v.update(extra=True)])
def test_wrong_identity_time_sequence_parent_rights_basis_and_units_reject(candidates,change):
    row=candidates[0];v=inputs(row);change(v)
    with pytest.raises(model.FractionalPointHold):apply(row,v)


@pytest.mark.parametrize('kind',['stem','leaf'])
def test_insufficient_declared_structural_funding_has_no_partial_effect(candidates,kind):
    row=candidates[0];v=inputs(row);v['internode'if kind=='stem'else'leaf']['initial_carbon'if kind=='stem'else'declaration']=(
        {'value':1e100,'unit':model.MASS}if kind=='stem'else{**v['leaf']['declaration'],'initial_carbon':{'value':1e100,'unit':model.MASS}})
    before=stock.context_bytes(row[0])
    with pytest.raises(model.FractionalPointHold,match='FUNDING_HOLD'):apply(row,v)
    assert stock.context_bytes(row[0])==before


@pytest.mark.parametrize('with_leaf',[False,True])
def test_only_expected_new_leaf_initialized_and_38_or_39_rhs(candidates,monkeypatch,with_leaf):
    row=candidates[0];v=inputs(row,with_leaf);evaluate=stock.short._evaluate;initialize=stock.short.old.leaf_area.initialize_leaf_area;calls=[];new=[]
    def counted(*a,**k):calls.append(1);return evaluate(*a,**k)
    def allowed(*,inputs):
        assert with_leaf and inputs['leaf_id']==v['leaf']['declaration']['leaf_id'];new.append(inputs['leaf_id']);return initialize(inputs=inputs)
    def forbidden(*a,**k):raise AssertionError('no replay, old initialization, geometry or issued CP')
    monkeypatch.setattr(stock.short,'_evaluate',counted);monkeypatch.setattr(stock.short.old.leaf_area,'initialize_leaf_area',allowed)
    for owner,name in [(stock,'prepare_context'),(stock,'advance_chunk'),(stock,'_seal'),(stock.stem,'apply_internode_births'),(stock.leaf,'apply_leaf_births'),
        (stock.short.old.leaf_area,'normalize_leaf_area_state'),(model.source_ids,'create_rational_internodes_from_shoot_events')]:monkeypatch.setattr(owner,name,forbidden)
    out=apply(row,v);assert len(calls)==out['rhs_evaluations']==38+with_leaf and len(new)==with_leaf


def test_stateless_repeat_is_identical_not_a_second_debit_or_adoption(candidates):
    row=candidates[0];v=inputs(row);a=apply(row,v);b=apply(row,v)
    assert a==b and a['after_state'][0]==b['after_state'][0] and a['before_candidate']==row[2]


@pytest.mark.parametrize('collision',['event','organ'])
def test_actual_preexisting_manual_event_or_canonical_organ_cannot_be_charged_again(candidates,collision):
    ctx,_,old_candidate=candidates[0];first=stock.start(ctx);v=inputs(candidates[0]);event=model.source_event(old_candidate)
    declaration=deepcopy(ctx.point_history[0]['inputs']);declaration.update(schema_version='stem-root-funded-internode-point-input-v1',policy='explicit-new-internode-carbon-from-buffer-v1',
        context_sha256=ctx.root_sha256,checkpoint_sha256=first.sha256,at_elapsed_seconds_exact=first.value['at_elapsed_seconds_exact'])
    declaration['events']=[{'event_id':event['internode_event_id']if collision=='event'else'early-manual-node',
        'parent_internode_id':v['parent_internode_id'],'compartment':v['internode']}]
    second=stock.adopt_births(context=ctx,raw_checkpoint=stock.checkpoint_bytes(ctx,first),expected_sha256=first.sha256,kind='internode',inputs=declaration)
    cp=stock.advance_chunk(second,stock.start(second),candidates[0][1].value['step_index'])['checkpoint'];assert cp is not None
    calculation=model.candidate.calculate_fractional_shoot_candidate(second,stock.checkpoint_bytes(second,cp),expected_sha256=cp.sha256,time_tolerance_seconds_exact=TOLERANCE)
    row=(second,cp,calculation);new=inputs(row);before=stock.context_bytes(second)
    with pytest.raises(model.FractionalPointHold,match='EVENT_HOLD'):apply(row,new)
    assert stock.context_bytes(second)==before


@pytest.mark.parametrize('last_stage',[38,39])
def test_profile_mutation_in_point_stage_withholds_whole_result(candidates,monkeypatch,last_stage):
    from types import MappingProxyType
    row=candidates[0];v=inputs(row);profile=row[0]._root._profiles[0];original=profile.values;evaluate=stock.short._evaluate;calls=[]
    def changed(*a,**k):
        result=evaluate(*a,**k);calls.append(1)
        if len(calls)==last_stage:
            values=dict(original);key=next(iter(values));values[key]+=.001;object.__setattr__(profile,'values',MappingProxyType(values))
        return result
    monkeypatch.setattr(stock.short,'_evaluate',changed)
    try:
        with pytest.raises(model.FractionalPointHold):apply(row,v)
    finally:object.__setattr__(profile,'values',original)


def test_rights_change_after_both_points_prevents_return(candidates,monkeypatch):
    row=candidates[0];v=inputs(row);bind=stock.leaf.binding.bind_initial_stem_carbon;calls=[]
    def changed(*a,**k):
        result=bind(*a,**k);calls.append(1)
        if len(calls)>=7:result['source_rights']['stem']['display']=False
        return result
    monkeypatch.setattr(stock.leaf.binding,'bind_initial_stem_carbon',changed)
    with pytest.raises(model.FractionalPointHold,match='SOURCE_HOLD'):apply(row,v)


def test_id_code_identity_change_in_final_rhs_is_held(candidates,monkeypatch):
    row=candidates[0];v=inputs(row);evaluate=stock.short._evaluate;calls=[]
    def changed(*a,**k):
        result=evaluate(*a,**k);calls.append(1)
        if len(calls)==39:monkeypatch.setattr(model,'ID_CODE_SHA256','0'*64)
        return result
    monkeypatch.setattr(stock.short,'_evaluate',changed)
    with pytest.raises(model.FractionalPointHold,match='CODE_HOLD'):apply(row,v)


def test_response_cap_never_issues_partial_material_point(candidates,monkeypatch):
    row=candidates[0];v=inputs(row);monkeypatch.setattr(model,'MAX_BYTES',len(stock._canonical(v))+1)
    with pytest.raises(model.FractionalPointHold,match='CAPACITY_HOLD'):apply(row,v)


def test_runtime_error_is_not_hidden_as_normal_hold(candidates,monkeypatch):
    row=candidates[0];v=inputs(row)
    def unexpected(*a,**k):raise RuntimeError('operator interruption')
    monkeypatch.setattr(stock.short,'_evaluate',unexpected)
    with pytest.raises(RuntimeError,match='operator interruption'):apply(row,v)
