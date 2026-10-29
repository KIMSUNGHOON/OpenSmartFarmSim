from copy import deepcopy
from fractions import Fraction
import json

import pytest

from test_crop_supply_morphology_newborn_point import current,profiles,prepared,pending,calculated,adopted,trajectory,post_pending,post_calculated,point_inputs


@pytest.fixture(scope='module')
def successor(request):
    from app import crop_supply_morphology_successor_context as model
    row=request.getfixturevalue('post_pending');before=request.getfixturevalue('post_calculated');origin,raw,digest,_=row
    inputs=point_inputs(row,before)
    context=model.prepare_context(origin,raw,expected_sha256=digest,time_tolerance_seconds_exact={'numerator':'1','denominator':'1000','unit':'s'},inputs=inputs)
    return context,row,before


def test_genuine_context_and_seed_cp_consume_actual_event_once(successor):
    from app import crop_supply_morphology_successor_context as model
    context,row,before=successor;cp=model.start(context);seed=context.value['seed'];point=json.loads(model.point_bytes(context))
    assert type(context)is model.Context and type(cp)is model.Checkpoint
    assert seed['program']==point['after_program']and cp.value['last_confirmed']['state']==point['after_state']
    assert cp.value['schedule']['consumed_sequence']==before['source_prefix']['schedule']['next_sequence']
    assert cp.value['schedule']['next_sequence']==before['source_prefix']['schedule']['next_sequence']+1
    assert cp.value['schedule']['age_exact']==before['dense_candidate']['shoot_age_exact']
    assert cp.value['output_cursor']==before['source_prefix']['output_cursor']+2 and cp.value['event_sequence']==before['source_prefix']['event_sequence']+1
    assert model.X(seed['original_grid_position']['remaining_to_next_grid_seconds_exact'])==Fraction(304)-model.X(point['at']['elapsed_seconds_exact'])
    assert cp.value['global_ledgers']==point['post_point_global_ledgers_preview']
    assert all(model.X(v['residual_exact'])==model.X(v['budget_exact'])==0 for v in cp.value['branch_ledgers'].values())
    assert cp.value['G0_G4']=='not_assessed'and cp.value['phase']=='fractional_after_compatible_material_point'


def test_explicit_geometry_origins_and_all_lifetime_channels_survive_adoption(successor):
    from app import crop_supply_morphology_successor_context as model
    context,_,_=successor;seed=context.value['seed'];point=json.loads(model.point_bytes(context))
    assert seed['geometry_baselines']==point['after_geometry_baselines']
    assert seed['birth_bases']==point['after_birth_baselines']
    assert seed['lifetime_transfers_exact']==point['post_point_lifetime_transfers_exact_preview']
    assert set(seed['lifetime_transfers_exact'])==set(model.resume.books.flux_units(seed['program'],seed['organs']))
    h=len(seed['organs']['internodes']);offset=seed['state_layout']['original_prefix_length']+h
    assert seed['geometry_baselines']['internodes'][-2]['origin_geometry']['value']==0.
    assert seed['initial_sample']['state'][offset+h-2]>0.
    assert seed['geometry_baselines']['internodes'][-1]['origin']=='current_material_seed'


def test_caller_tolerance_changed_after_capture_is_rejected(successor,monkeypatch):
    from app import crop_supply_morphology_successor_context as model
    _,row,before=successor;origin,raw,digest,_=row;inputs=point_inputs(row,before)
    tolerance={'numerator':'1','denominator':'1000','unit':'s'};apply=model.point.apply_fractional_material_point
    def changed(*args,**kwargs):
        result=apply(*args,**kwargs);tolerance['denominator']='100';return result
    monkeypatch.setattr(model.point,'apply_fractional_material_point',changed)
    with pytest.raises(model.SupplyContextHold,match='INPUT_HOLD'):
        model.prepare_context(origin,raw,expected_sha256=digest,time_tolerance_seconds_exact=tolerance,inputs=inputs)


def test_original_point_schema_rejects_rehashed_extra_claims(successor):
    from app import crop_supply_morphology_successor_context as model
    context,row,_=successor;result=json.loads(model.point_bytes(context));result['invented_yield']=1.
    result['calculation_sha256']=model._hash({k:v for k,v in result.items()if k!='calculation_sha256'})
    with pytest.raises(ValueError):model.proofs.validate(row[0],result)


def test_caller_rights_changed_just_after_point_capture_cannot_be_successor(successor,monkeypatch):
    from app import crop_supply_morphology_successor_context as model
    context,row,before=successor;origin,raw,digest,_=row;inputs=point_inputs(row,before);apply=model.point.apply_fractional_material_point
    def changed(*args,**kwargs):
        result=apply(*args,**kwargs);inputs['rights']['use']=False;return result
    monkeypatch.setattr(model.point,'apply_fractional_material_point',changed)
    with pytest.raises(model.SupplyContextHold,match='INPUT_HOLD'):
        model.prepare_context(origin,raw,expected_sha256=digest,time_tolerance_seconds_exact={'numerator':'1','denominator':'1000','unit':'s'},inputs=inputs)


def test_cold_context_start_and_export_do_not_replay_and_cp_restore_only_checks_one_current_rhs(successor,monkeypatch):
    from app import crop_supply_morphology_successor_context as model
    context,row,_=successor;raw=model.context_bytes(context);proof=model.point_bytes(context);cp=model.start(context);cpraw=model.checkpoint_bytes(context,cp)
    calls=[];evaluate=model.point.core.stage.evaluate
    def counted(*args,**kw):calls.append(1);return evaluate(*args,**kw)
    def forbidden(*args,**kw):raise AssertionError('no old RHS, material funding/point, leaf init or grid advance on restore')
    for owner,name in [(model.point,'apply_fractional_material_point'),(model.point.core,'apply'),(model.point.core.arithmetic,'_fund'),(model.point.core.arithmetic,'_new_leaf'),
        (model.point.core.arithmetic.resume.short.old.leaf_area,'initialize_leaf_area'),(model.point.candidate,'calculate_next_event_candidate'),
        (model.source.stock.short,'_evaluate'),(model.resume,'restore_checkpoint'),(model.resume,'advance_chunk'),(model.resume,'_rhs'),(model.source,'adopt_first'),(model.source,'adopt_successor')]:monkeypatch.setattr(owner,name,forbidden)
    monkeypatch.setattr(model.point.core.stage,'evaluate',counted)
    cold=model.restore_context(row[0],raw,expected_sha256=context.root_sha256,point_bytes=proof)
    assert model.context_bytes(cold)==raw and model.point_bytes(cold)==proof and model.checkpoint_bytes(cold,model.start(cold))==cpraw and calls==[]
    restored=model.restore_checkpoint(cold,cpraw,expected_sha256=cp.sha256)
    assert model.checkpoint_bytes(cold,restored)==cpraw and len(calls)==1


@pytest.mark.parametrize('field',['state','schedule','prefix','cursor','global','branch','life','point','json_type','extra'])
def test_self_rehashed_seed_cp_changes_are_rejected_before_current_rhs(successor,monkeypatch,field):
    from app import crop_supply_morphology_successor_context as model
    context,_,_=successor;cp=model.start(context);p=cp.value
    if field=='state':p['last_confirmed']['state'][0]+=1.
    elif field=='schedule':p['schedule']['next_sequence']+=1
    elif field=='prefix':p['output_prefix_sha256']='0'*64
    elif field=='cursor':p['output_cursor']+=1
    elif field=='global':next(iter(p['global_ledgers'].values()))['residual_exact']['numerator']='123'
    elif field=='branch':next(iter(p['branch_ledgers'].values()))['budget_exact']['numerator']='1'
    elif field=='life':next(iter(p['lifetime_transfers_exact'].values()))['numerator']='1'
    elif field=='point':next(iter(p['point_totals_exact'].values()))['numerator']='1'
    elif field=='json_type':p['branch_steps']=False
    else:p['extra']=1
    def forbidden(*args,**kwargs):raise AssertionError('altered seed cannot run current RHS')
    monkeypatch.setattr(model.point.core.stage,'evaluate',forbidden);raw=model._canonical(p)
    with pytest.raises(model.SupplyContextHold):model.restore_checkpoint(context,raw,expected_sha256=model._hash(p))


@pytest.mark.parametrize('field',['schedule','state','cost','baseline','geometry','prefix','origin','json_type','extra'])
def test_self_rehashed_owner_cannot_replace_the_actual_point_derived_seed(successor,field):
    from app import crop_supply_morphology_successor_context as model
    context,row,_=successor;value=context.value
    if field=='schedule':value['seed']['schedule']['consumed_sequence']+=1
    elif field=='state':value['seed']['initial_sample']['state'][0]+=1.
    elif field=='cost':value['seed']['costs']['internodes'][-1]*=2
    elif field=='baseline':value['seed']['birth_bases']['stem_root'][-1]['base_temperature']['value']+=1.
    elif field=='geometry':value['seed']['geometry_baselines']['internodes'][-2]['origin_geometry']['value']+=1.
    elif field=='prefix':value['seed']['output_prefix_sha256']='0'*64
    elif field=='origin':value['origin_context_sha256']='0'*64
    elif field=='json_type':value['seed']['original_numerical']['step_count']=float(value['seed']['original_numerical']['step_count'])
    else:value['extra']=1
    raw=model._canonical(value)
    with pytest.raises(model.SupplyContextHold):model.restore_context(row[0],raw,expected_sha256=model._hash(value),point_bytes=model.point_bytes(context))


@pytest.mark.parametrize('field',['funding','state','baseline','geometry','parent','budget','stage_extra','candidate_extra','json_type','initialization'])
def test_rehashed_material_proof_must_still_match_original_direct_equations(successor,field):
    from app import crop_supply_morphology_successor_context as model
    context,row,_=successor;p=json.loads(model.point_bytes(context))
    if field=='funding':p['flow_components']['internode']['buffer_debit']['value']+=1.
    elif field=='state':p['after_state'][0]+=1.
    elif field=='baseline':p['new_birth_baselines']['stem_root'][-1]['base_temperature']['value']+=1.
    elif field=='geometry':p['after_geometry_baselines']['internodes'][-2]['origin_geometry']['value']+=1.
    elif field=='json_type':p['after_geometry_baselines']['internodes'][-1]['origin_geometry']['value']=False
    elif field=='parent':p['after_organs']['internodes'][-1]['parent_internode_id']='other-parent'
    elif field=='budget':next(iter(p['post_point_global_ledgers_preview'].values()))['budget_exact']['numerator']='123'
    elif field=='stage_extra':p['after_stage']['extra']=1
    elif field=='candidate_extra':
        p['before_candidate']['extra']=1;p['before_candidate']['calculation_sha256']=model._hash({k:v for k,v in p['before_candidate'].items()if k!='calculation_sha256'})
        p['inputs']['candidate_sha256']=p['before_candidate_sha256']=p['before_candidate']['calculation_sha256'];p['input_sha256']=model._hash(p['inputs'])
    else:p['leaf_receipts'][0]['initialization']['state']['anchor']['requested_area']['value']*=2
    p['calculation_sha256']=model._hash({k:v for k,v in p.items()if k!='calculation_sha256'})
    with pytest.raises(ValueError):model.proofs.validate(row[0],p)


@pytest.mark.parametrize('kind',['context','point','checkpoint'])
def test_bounded_bytes_and_trusted_hash_are_required(successor,kind):
    from app import crop_supply_morphology_successor_context as model
    context,row,_=successor;raw=model.context_bytes(context);proof=model.point_bytes(context);cp=model.start(context)
    with pytest.raises(model.SupplyContextHold):
        if kind=='context':model.restore_context(row[0],raw+b' ',expected_sha256=context.root_sha256,point_bytes=proof)
        elif kind=='point':model.restore_context(row[0],raw,expected_sha256=context.root_sha256,point_bytes=proof+b' ')
        else:model.restore_checkpoint(context,model.checkpoint_bytes(context,cp),expected_sha256='0'*64)


@pytest.mark.parametrize('failure',['profile','source','code','runtime'])
def test_current_validation_late_failure_never_returns_a_checkpoint(successor,monkeypatch,failure):
    from pathlib import Path
    from stat import S_IMODE
    from app import crop_supply_morphology_successor_context as model
    context,row,_=successor;cp=model.start(context);raw=model.checkpoint_bytes(context,cp);evaluate=model.point.core.stage.evaluate
    profile=row[0]._origin._source._source._root._profiles[0];original=profile.filtered_temperature_bounds;directory=Path(row[0]._origin._source._source._directories[0]);mode=S_IMODE(directory.stat().st_mode)
    def changed(*args,**kwargs):
        if failure=='runtime':raise RuntimeError('unexpected new current RHS')
        out=evaluate(*args,**kwargs)
        if failure=='profile':object.__setattr__(profile,'filtered_temperature_bounds',(1.,2.))
        elif failure=='source':directory.chmod(0)
        elif failure=='code':monkeypatch.setattr(model,'CODE_SHA256','0'*64)
        return out
    monkeypatch.setattr(model.point.core.stage,'evaluate',changed)
    try:
        with pytest.raises(RuntimeError if failure=='runtime'else model.SupplyContextHold):model.restore_checkpoint(context,raw,expected_sha256=cp.sha256)
    finally:object.__setattr__(profile,'filtered_temperature_bounds',original);directory.chmod(mode)


def test_new_owner_is_not_an_old_handle_and_cannot_reconsume_through_old_entry(successor):
    from app import crop_supply_morphology_successor_context as model
    context,row,before=successor;origin,raw,digest,_=row
    with pytest.raises(ValueError):model.resume._context(context)
    with pytest.raises(model.SupplyContextHold):model.prepare_context(context,raw,expected_sha256=digest,time_tolerance_seconds_exact={'numerator':'1','denominator':'1000','unit':'s'},inputs=point_inputs(row,before))
    assert model.start(context).value['schedule']['consumed_sequence']==before['source_prefix']['schedule']['next_sequence']


@pytest.mark.parametrize('with_leaf,length',[(False,0.),(False,.01),(True,.01)])
def test_actual_other_seed_shapes_prepare_restore_and_keep_original_remainder(post_pending,post_calculated,with_leaf,length):
    from app import crop_supply_morphology_successor_context as model
    origin,raw,digest,_=post_pending;inputs=point_inputs(post_pending,post_calculated,with_leaf=with_leaf,length=length)
    context=model.prepare_context(origin,raw,expected_sha256=digest,time_tolerance_seconds_exact={'numerator':'1','denominator':'1000','unit':'s'},inputs=inputs)
    blob=model.context_bytes(context);proof=model.point_bytes(context);cold=model.restore_context(origin,blob,expected_sha256=context.root_sha256,point_bytes=proof)
    cp=model.start(cold);raw_cp=model.checkpoint_bytes(cold,cp);reopened=model.restore_checkpoint(cold,raw_cp,expected_sha256=cp.sha256)
    assert model.checkpoint_bytes(cold,reopened)==raw_cp and len(cp.value['global_ledgers'])==(84 if with_leaf else 79)
    assert cp.value['last_confirmed']['state'][-1]==length and cp.value['schedule']['next_sequence']==post_calculated['source_prefix']['schedule']['next_sequence']+1
