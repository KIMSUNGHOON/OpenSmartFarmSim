from fractions import Fraction

from test_crop_supply_morphology_context import current,profiles,prepared,pending,calculated,adopted


def test_actual_zero_length_newborn_advances_original_remainder(request):
    from app import crop_supply_morphology_newborn_resume as model
    context,_,_=request.getfixturevalue('adopted');initial=model.start(context);seed=context.value['seed']
    assert initial.value['last_confirmed']==seed['initial_sample']
    assert initial.value['output_prefix_sha256']==seed['output_prefix_sha256']
    assert initial.value['last_confirmed']['state'][-1]==0.
    out=model.advance_chunk(context,initial,1)
    assert out['status']=='yielded',out['hold']
    cp=out['checkpoint'].value
    assert cp['at']['elapsed_seconds_exact']==model.Q(Fraction(264),'s')
    assert model.X(out['intervals'][0]['step_seconds_exact'])==Fraction(264)-model.X(initial.value['at']['elapsed_seconds_exact'])
    assert cp['last_confirmed']['state'][-1]>0. and cp['schedule']['next_sequence']==seed['schedule']['next_sequence']
    assert cp['point_totals_exact']==seed['point_totals_exact']and cp['G0_G4']=='not_assessed'
    assert out['current_validation_RHS_evaluations']==1 and out['new_RHS_evaluations']==4
    assert all(abs(model.X(v['residual_exact']))<=model.X(v['budget_exact'])for v in cp['global_ledgers'].values())


import json
from copy import deepcopy
import pytest


@pytest.fixture(scope='module')
def trajectory(adopted):
    from app import crop_supply_morphology_newborn_resume as model
    context=adopted[0];out=model.advance_chunk(context,model.start(context),128)
    assert out['status']=='hold'and out['pending_event']is not None,out['hold']
    return out


def test_full_split_and_cold_checkpoints_match_without_consuming_next_event(adopted,trajectory):
    from app import crop_supply_morphology_newborn_resume as model
    context=adopted[0];seed=model.start(context);cp=seed;seen=[]
    for _ in trajectory['samples']:
        out=model.advance_chunk(context,cp,1);assert out['status']=='yielded',out['hold'];cp=out['checkpoint'];seen+=out['samples']
        raw=model.checkpoint_bytes(context,cp);cold=model.owner.restore_context(context._origin,model.owner.context_bytes(context),expected_sha256=context.root_sha256,point_bytes=model.owner.point_bytes(context))
        cp=model.restore_checkpoint(cold,raw,expected_sha256=cp.sha256)
    assert seen==trajectory['samples']and cp.value==trajectory['last_confirmed']
    assert model.checkpoint_bytes(context,cp)==model._canonical(trajectory['last_confirmed'])
    again=model.advance_chunk(context,cp,1)
    assert again['samples']==[]and again['last_confirmed']==cp.value and again['pending_event']==trajectory['pending_event']
    assert cp.value['schedule']['next_sequence']==seed.value['schedule']['next_sequence']
    assert cp.value['point_totals_exact']==seed.value['point_totals_exact']and cp.value['output_cursor']==seed.value['output_cursor']+len(seen)


def test_all_four_stage_states_and_cumulative_channels_reconcile_exactly(adopted,trajectory):
    from app import crop_supply_morphology_newborn_resume as model
    initial=model.start(adopted[0]);values=[v['name']for v in trajectory['intervals'][0]['flux_order']];totals=[0.]*len(values)
    F=Fraction.from_float;weights=[Fraction(1,6),Fraction(1,3),Fraction(1,3),Fraction(1,6)];state=initial.value['last_confirmed']['state']
    for trace in trajectory['intervals']:
        h=model.X(trace['step_seconds_exact']);rows=trace['stages'];assert rows[0]['state']==state
        for i,offset in [(1,h/2),(2,h/2),(3,h)]:assert rows[i]['state']==[float(F(a)+offset*F(b))for a,b in zip(state,rows[i-1]['rates'],strict=True)]
        state=[float(F(a)+h*sum((w*F(r['rates'][i])for w,r in zip(weights,rows,strict=True)),Fraction(0)))for i,a in enumerate(state)]
        totals=[float(F(a)+h*sum((w*F(r['flux'][i])for w,r in zip(weights,rows,strict=True)),Fraction(0)))for i,a in enumerate(totals)]
        assert state==trace['endpoint']['state']
    cp=trajectory['last_confirmed'];assert state==cp['last_confirmed']['state']
    assert totals==[cp['branch_integrated_transfers'][k]['value']for k in values]
    for name,t in zip(values,totals,strict=True):assert model.X(cp['lifetime_transfers_exact'][name])==model.X(initial.value['lifetime_transfers_exact'][name])+F(t)
    for name,row in cp['global_ledgers'].items():
        for field in ['residual_exact','budget_exact']:assert model.X(row[field])==model.X(initial.value['global_ledgers'][name][field])+model.X(cp['branch_ledgers'][name][field])


def test_next_threshold_returns_monotone_unadopted_bracket_and_original_prefix(adopted,trajectory):
    from app import crop_supply_morphology_newborn_resume as model
    cp=trajectory['last_confirmed'];pending=trajectory['pending_event']
    assert trajectory['checkpoint']is None and pending['schedule_consumed']is False and pending['candidate_or_checkpoint_issued']is False
    assert pending['left_at']==cp['at']and model.X(pending['left_age_exact'])<model.X(pending['threshold_exact'])<=model.X(pending['right_age_exact'])
    assert model.X(pending['interval']['shoot_clock_certificate']['minimum_derivative_per_unit_theta_exact'])>=0
    assert trajectory['past_intervals_reintegrated']==0 and cp['last_confirmed']['state'][-1]>0.


def test_cold_and_current_validation_have_no_old_rhs_material_or_initialization(adopted,trajectory,monkeypatch):
    from app import crop_supply_morphology_newborn_resume as model
    context=adopted[0];seed=model.start(context);raw=model.checkpoint_bytes(context,seed);fullraw=model._canonical(trajectory['last_confirmed']);calls=[];evaluate=model.owner.point.core.stage.evaluate
    def counted(*args,**kw):calls.append(1);return evaluate(*args,**kw)
    def forbidden(*args,**kw):raise AssertionError('no old RHS/CP/material/candidate/fund/init on newborn resume')
    for module,name in [(model.resume,'advance_chunk'),(model.resume,'restore_checkpoint'),(model.resume,'_rhs'),(model.source,'advance_chunk'),(model.source,'restore_checkpoint'),
        (model.owner,'prepare_context'),(model.owner,'restore_checkpoint'),(model.owner.point,'apply_fractional_material_point'),(model.owner.point.core,'apply'),
        (model.owner.point.candidate,'calculate_next_event_candidate'),(model.owner.point.core.arithmetic,'_fund'),(model.owner.point.core.arithmetic,'_new_leaf'),
        (model.source.stock.short,'_evaluate'),(model.source.stock.short.old.leaf_area,'initialize_leaf_area')]:monkeypatch.setattr(module,name,forbidden)
    monkeypatch.setattr(model.owner.point.core.stage,'evaluate',counted)
    assert model.checkpoint_bytes(context,model.start(context))==raw and calls==[]
    restored=model.restore_checkpoint(context,fullraw,expected_sha256=model._hash(trajectory['last_confirmed']));assert calls==[1]
    assert model.checkpoint_bytes(context,restored)==fullraw and calls==[1]
    out=model.advance_chunk(context,seed,1);assert out['status']=='yielded'and len(calls)==6


@pytest.mark.parametrize('field',['state','schedule','life','point','global','branch','prefix','cursor','phase','seed','unit','extra'])
def test_rehashed_checkpoint_corruption_cannot_restore(adopted,trajectory,field):
    from app import crop_supply_morphology_newborn_resume as model
    p=deepcopy(trajectory['last_confirmed'])
    if field=='state':p['last_confirmed']['state'][0]+=1.
    elif field=='schedule':p['schedule']['next_sequence']+=1
    elif field=='life':next(iter(p['lifetime_transfers_exact'].values()))['numerator']='123'
    elif field=='point':next(iter(p['point_totals_exact'].values()))['numerator']='123'
    elif field=='global':next(iter(p['global_ledgers'].values()))['budget_exact']['numerator']='123'
    elif field=='branch':next(iter(p['branch_ledgers'].values()))['budget_exact']['numerator']='123'
    elif field=='prefix':p['output_prefix_sha256']='0'*64
    elif field=='cursor':p['output_cursor']+=1
    elif field=='phase':p['phase']='invented'
    elif field=='seed':p['seed_checkpoint_sha256']='0'*64
    elif field=='unit':next(iter(p['branch_integrated_transfers'].values()))['unit']='invented'
    else:p['extra']=1
    with pytest.raises(ValueError):model.restore_checkpoint(adopted[0],model._canonical(p),expected_sha256=model._hash(p))


@pytest.mark.parametrize('budget',[0,-1,129,True,1.5])
def test_original_step_budget_is_bounded(adopted,budget):
    from app import crop_supply_morphology_newborn_resume as model
    context=adopted[0]
    with pytest.raises(model.SupplyNewbornHold):model.advance_chunk(context,model.start(context),budget)


def test_actual_stage_domain_failure_keeps_last_confirmed_original_endpoint(adopted,monkeypatch):
    from app import crop_supply_morphology_newborn_resume as model
    context=adopted[0];initial=model.start(context);expected=model.advance_chunk(context,initial,1)['checkpoint'].value;evaluate=model.owner.point.core.stage.evaluate;calls=[]
    def failing(*args,**kw):
        calls.append(1)
        if len(calls)==7:raise ValueError('own injected supported-domain failure')
        return evaluate(*args,**kw)
    monkeypatch.setattr(model.owner.point.core.stage,'evaluate',failing)
    out=model.advance_chunk(context,initial,3)
    assert out['status']=='hold'and out['checkpoint']is None and out['pending_event']is None
    assert out['last_confirmed']==expected and len(out['samples'])==len(out['intervals'])==1
    restored=model.restore_checkpoint(context,model._canonical(expected),expected_sha256=model._hash(expected));assert restored.value==expected


@pytest.mark.parametrize('failure',['profile','source','code','caller','stage_input'])
def test_late_changed_authority_discards_unpublishable_prefix(adopted,monkeypatch,failure):
    from pathlib import Path
    from stat import S_IMODE
    from app import crop_supply_morphology_newborn_resume as model
    context=adopted[0];cp=model.start(context);evaluate=model.owner.point.core.stage.evaluate;calls=[]
    profile=context._origin._source._source._root._profiles[0];original=profile.filtered_temperature_bounds;directory=Path(context._origin._source._source._directories[0]);mode=S_IMODE(directory.stat().st_mode)
    def changed(*args,**kw):
        out=evaluate(*args,**kw);calls.append(1)
        if len(calls)==6:
            if failure=='profile':object.__setattr__(profile,'filtered_temperature_bounds',(1.,2.))
            elif failure=='source':directory.chmod(0)
            elif failure=='code':monkeypatch.setattr(model,'CODE_SHA256','0'*64)
            elif failure=='caller':object.__setattr__(cp,'_raw',cp._raw+b' ')
            else:args[2]['internodes'][-1]['parent_internode_id']='invented-parent'
        return out
    monkeypatch.setattr(model.owner.point.core.stage,'evaluate',changed)
    try:
        out=model.advance_chunk(context,cp,3)
        assert out['status']=='hold'and out['last_confirmed']is None and out['samples']==out['intervals']==[]and out['pending_event']is None and out['checkpoint']is None
    finally:object.__setattr__(profile,'filtered_temperature_bounds',original);directory.chmod(mode)


def test_unexpected_runtime_error_propagates(adopted,monkeypatch):
    from app import crop_supply_morphology_newborn_resume as model
    context=adopted[0];cp=model.start(context)
    def fail(*args,**kw):raise RuntimeError('own unexpected newborn stage')
    monkeypatch.setattr(model.owner.point.core.stage,'evaluate',fail)
    with pytest.raises(RuntimeError):model.advance_chunk(context,cp,1)


def test_seed_only_and_old_checkpoints_are_not_evolved_newborn_handles(adopted):
    from app import crop_supply_morphology_newborn_resume as model
    context=adopted[0];old=model.owner.start(context)
    with pytest.raises(ValueError):model.advance_chunk(context,old,1)
    with pytest.raises(ValueError):model.owner.checkpoint_bytes(context,model.start(context))


@pytest.mark.parametrize('kind',['oversize','hash','noncanonical'])
def test_raw_checkpoint_bounds_and_original_hash(adopted,kind):
    from app import crop_supply_morphology_newborn_resume as model
    context=adopted[0];cp=model.start(context);raw=model.checkpoint_bytes(context,cp);digest=cp.sha256
    if kind=='oversize':raw=b' '*(model.MAX_CP+1)
    elif kind=='hash':digest='0'*64
    else:raw+=b' '
    with pytest.raises(ValueError):model.restore_checkpoint(context,raw,expected_sha256=digest)
