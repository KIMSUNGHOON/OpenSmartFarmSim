from copy import deepcopy
from fractions import Fraction
from hashlib import sha256
import json

import pytest

from test_crop_supply_morphology_rhs import current,profiles,parameters


@pytest.fixture(scope='module')
def prepared(current):
    from app import crop_supply_morphology_resume as model
    source,cp,raw=current
    return model.prepare_context(source,raw,expected_sha256=cp.sha256,inputs=parameters(source,cp))


def test_actual_fractional_branch_advances_and_split_restore_is_identical(prepared):
    from app import crop_supply_morphology_resume as model
    context=prepared
    initial=model.start(context);before=model.context_bytes(context)
    whole=model.advance_chunk(context,initial,2)
    one=model.advance_chunk(context,initial,1)
    assert whole['status']==one['status']=='yielded'
    assert one['checkpoint'].value['at']['elapsed_seconds_exact']==model.Q(Fraction(224),'s')
    restored=model.restore_checkpoint(context,model.checkpoint_bytes(context,one['checkpoint']),expected_sha256=one['checkpoint'].sha256)
    split=model.advance_chunk(context,restored,1)
    assert model.checkpoint_bytes(context,whole['checkpoint'])==model.checkpoint_bytes(context,split['checkpoint'])
    final=whole['checkpoint'].value
    assert final['at']['elapsed_seconds_exact']==model.Q(Fraction(232),'s')
    assert whole['samples']==one['samples']+split['samples']
    assert final['last_confirmed']['state']!=initial.value['last_confirmed']['state']
    assert all(abs(model.X(v['residual_exact']))<=model.X(v['budget_exact'])for v in final['global_ledgers'].values())
    assert all(model.X(v['deficit_exact'])>=0 for v in final['geometry_diagnostics'].values())
    assert model.context_bytes(context)==before and final['G0_G4']=='not_assessed'


def test_start_context_restore_and_current_cp_validation_never_replay_old_rhs(prepared,monkeypatch):
    from app import crop_supply_morphology_resume as model
    ctx=prepared;cp=model.start(ctx);raw=model.context_bytes(ctx);proofs=model.proof_bytes(ctx);cpraw=model.checkpoint_bytes(ctx,cp)
    calls=[];evaluate=model.bound.stage.evaluate
    def counted(*args,**kw):calls.append(1);return evaluate(*args,**kw)
    def forbidden(*args,**kw):raise AssertionError('no old biology, material operation or initialization')
    for owner,name in [(model.source.stock.short,'_evaluate'),(model.bound,'evaluate_bound_rhs'),(model.source,'advance_chunk'),
        (model.source,'restore_checkpoint'),(model.source,'start'),(model.source,'adopt_first'),(model.source,'adopt_successor'),
        (model.source.stock.short.old.leaf_area,'initialize_leaf_area')]:monkeypatch.setattr(owner,name,forbidden)
    monkeypatch.setattr(model.bound.stage,'evaluate',counted)
    cold=model.restore_context(ctx._source,raw,expected_sha256=ctx.root_sha256,proof_bytes=proofs)
    assert model.checkpoint_bytes(cold,model.start(cold))==cpraw and calls==[]
    restored=model.restore_checkpoint(cold,cpraw,expected_sha256=cp.sha256);assert calls==[1]
    result=model.advance_chunk(cold,restored,1)
    assert result['status']=='yielded'and len(calls)==6
    assert result['current_validation_RHS_evaluations']==1 and result['new_RHS_evaluations']==4


def test_shared_rk4_states_and_all_transfer_channels_match_independent_fraction_arithmetic(prepared):
    from app import crop_supply_morphology_resume as model
    out=model.advance_chunk(prepared,model.start(prepared),1);trace=out['intervals'][0];rows=trace['stages'];h=model.X(trace['step_seconds_exact'])
    F=Fraction.from_float;weights=(Fraction(1,6),Fraction(1,3),Fraction(1,3),Fraction(1,6))
    for i,value in enumerate(trace['endpoint']['state']):
        assert value==float(F(rows[0]['state'][i])+h*sum((w*F(row['rates'][i])for w,row in zip(weights,rows,strict=True)),Fraction(0)))
    transfers=out['checkpoint'].value['branch_integrated_transfers']
    for i,descriptor in enumerate(trace['flux_order']):
        assert transfers[descriptor['name']]['value']==float(h*sum((w*F(row['flux'][i])for w,row in zip(weights,rows,strict=True)),Fraction(0)))
        assert transfers[descriptor['name']]['unit']==descriptor['unit']
    assert out['checkpoint'].value['point_totals_exact']==json.loads(prepared._parent)['point_totals_exact']


def test_new_law_first_due_threshold_returns_only_confirmed_prefix_and_unadopted_bracket(prepared):
    from app import crop_supply_morphology_resume as model
    cp=model.start(prepared);out=model.advance_chunk(prepared,cp,128)
    assert out['status']=='hold'and out['pending_event']is not None,out['hold']
    assert out['checkpoint']is None and out['pending_event']['candidate_or_checkpoint_issued']is False
    pending=out['pending_event'];confirmed=out['last_confirmed']
    assert pending['left_at']==confirmed['at']
    assert model.X(pending['left_age_exact'])<model.X(pending['threshold_exact'])<=model.X(pending['right_age_exact'])
    assert confirmed['schedule']['next_sequence']==cp.value['schedule']['next_sequence']
    assert confirmed['point_totals_exact']==cp.value['point_totals_exact']
    assert len(out['samples'])==len(out['intervals'])==confirmed['branch_steps']
    restored=model.restore_checkpoint(prepared,model._canonical(confirmed),expected_sha256=model._hash(confirmed))
    again=model.advance_chunk(prepared,restored,1)
    assert again['samples']==[]and again['last_confirmed']==confirmed and again['pending_event']==pending


def test_same_time_one_two_four_diagnostic_keeps_source_cp_and_reports_actual_convergence(prepared):
    from app import crop_supply_morphology_resume as model
    cp=model.start(prepared);raw=model.checkpoint_bytes(prepared,cp)
    out=model.compare_interval_refinements(prepared,raw,expected_sha256=cp.sha256)
    assert [x['subdivisions']for x in out['rows']]==[1,2,4]
    assert all(x['at']==out['rows'][0]['at']for x in out['rows'])and out['checkpoint_issued']is False
    assert out['current_validation_RHS_evaluations']==1 and out['new_RHS_evaluations']==28
    assert len(out['state_differences'])==len(cp.value['last_confirmed']['state'])
    for index in [103,104,105]:
        row=out['state_differences'][index]
        assert model.X(row['two_to_four_exact'])<model.X(row['one_to_two_exact'])
    assert model.checkpoint_bytes(prepared,cp)==raw


@pytest.mark.parametrize('field',['state','flow','schedule','phase','global','prefix','extra'])
def test_self_rehashed_cp_corruption_does_not_replace_actual_new_current_authority(prepared,field):
    from app import crop_supply_morphology_resume as model
    cp=model.start(prepared);p=cp.value
    if field=='state':p['last_confirmed']['state'][0]+=1.
    elif field=='flow':next(iter(p['branch_integrated_transfers'].values()))['value']+=1.
    elif field=='schedule':p['schedule']['next_sequence']+=1
    elif field=='phase':p['phase']='other'
    elif field=='global':next(iter(p['global_ledgers'].values()))['budget_exact']['numerator']='0'
    elif field=='prefix':p['output_prefix_sha256']='0'*64
    else:p['extra']=1
    raw=model._canonical(p)
    with pytest.raises(model.SupplyResumeHold):model.restore_checkpoint(prepared,raw,expected_sha256=sha256(raw).hexdigest())


@pytest.mark.parametrize('budget',[0,True,-1,129,1.5])
def test_invalid_step_budget_cannot_change_seed(prepared,budget):
    from app import crop_supply_morphology_resume as model
    cp=model.start(prepared);raw=model.checkpoint_bytes(prepared,cp)
    with pytest.raises(model.SupplyResumeHold):model.advance_chunk(prepared,cp,budget)
    assert model.checkpoint_bytes(prepared,cp)==raw


@pytest.mark.parametrize('when',['k2','endpoint','late_profile','runtime'])
def test_failed_unconfirmed_stage_or_late_profile_never_emits_new_cp(prepared,monkeypatch,when):
    from app import crop_supply_morphology_resume as model
    cp=model.start(prepared);run=model.bound.stage.evaluate;calls=[]
    profile=prepared._source._source._root._profiles[0];original=profile.filtered_temperature_bounds
    def changed(*args,**kw):
        calls.append(1)
        if when=='k2'and len(calls)==2:raise ValueError('DOMAIN_HOLD: deliberate unsupported intermediate')
        out=run(*args,**kw)
        if when=='endpoint'and len(calls)==5:raise ValueError('DOMAIN_HOLD: deliberate endpoint')
        if when=='late_profile'and len(calls)==5:object.__setattr__(profile,'filtered_temperature_bounds',(1.,2.))
        if when=='runtime'and len(calls)==2:raise RuntimeError('unexpected stage failure')
        return out
    monkeypatch.setattr(model.bound.stage,'evaluate',changed)
    try:
        if when=='runtime':
            with pytest.raises(RuntimeError):model.advance_chunk(prepared,cp,2)
        else:
            out=model.advance_chunk(prepared,cp,2)
            assert out['status']=='hold'and out['checkpoint']is None and out['samples']==[]
            assert out['last_confirmed']is None if when=='late_profile'else out['last_confirmed']==cp.value
    finally:object.__setattr__(profile,'filtered_temperature_bounds',original)


def test_exact_dense_clock_certificate_has_nonnegative_derivative_and_same_right_classification(prepared):
    from app import crop_supply_morphology_resume as model
    out=model.advance_chunk(prepared,model.start(prepared),128)
    traces=[*out['intervals'],out['pending_event']['interval']]
    for trace in traces:
        cert=trace['shoot_clock_certificate'];coefficients=list(map(model.X,cert['shoot_age_coefficients_exact']));h=model.X(trace['step_seconds_exact'])
        a,b,c,d=(Fraction.from_float(row['state'][104])for row in trace['stages']);base=Fraction.from_float(model._context(prepared)['shoot_base_temperature'])
        assert coefficients[1:]==[h*(a-base)/86400,h*(-3*a/2+b+c-d/2)/86400,h*(2*a/3-2*b/3-2*c/3+2*d/3)/86400]
        _,c1,c2,c3=coefficients;values=[c1,c1+2*c2+3*c3]
        if c3>0:
            vertex=-c2/(3*c3)
            if 0<vertex<1:values.append(c1+2*c2*vertex+3*c3*vertex*vertex)
        assert min(values)==model.X(cert['minimum_derivative_per_unit_theta_exact'])>=0
        assert sum(coefficients,Fraction(0))==model.X(cert['dense_right_age_exact'])


def test_unresolved_dense_clock_monotonicity_or_rounding_is_not_skipped(prepared,monkeypatch):
    from app import crop_supply_morphology_resume as model
    cp=model.start(prepared);step=model._step
    def changed(*args,**kw):
        state,totals,rhs,trace=step(*args,**kw)
        trace['stages'][0]['state'][104]=-100.
        return state,totals,rhs,trace
    monkeypatch.setattr(model,'_step',changed)
    out=model.advance_chunk(prepared,cp,2)
    assert out['status']=='hold'and out['checkpoint']is None and out['samples']==[]
    assert out['last_confirmed']==cp.value and 'SCHEDULE_'in out['hold']


@pytest.mark.parametrize('proof_key',['parent_checkpoint','inputs','initial_bound'])
def test_context_proofs_are_bounded_immutable_and_source_bound(prepared,proof_key):
    from app import crop_supply_morphology_resume as model
    raw=model.context_bytes(prepared);proofs=model.proof_bytes(prepared);changed=dict(proofs);changed[proof_key]+=b' '
    with pytest.raises(model.SupplyResumeHold):model.restore_context(prepared._source,raw,expected_sha256=prepared.root_sha256,proof_bytes=changed)
    assert model.context_bytes(prepared)==raw


def test_late_actual_source_access_loss_withholds_all_new_samples(prepared,monkeypatch):
    from pathlib import Path
    from stat import S_IMODE
    from app import crop_supply_morphology_resume as model
    cp=model.start(prepared);directory=Path(prepared._source._source._directories[0]);mode=S_IMODE(directory.stat().st_mode)
    run=model.bound.stage.evaluate;calls=[]
    def revoked(*args,**kw):
        out=run(*args,**kw);calls.append(1)
        if len(calls)==5:directory.chmod(0)
        return out
    monkeypatch.setattr(model.bound.stage,'evaluate',revoked)
    try:
        out=model.advance_chunk(prepared,cp,2)
        assert out['status']=='hold'and out['samples']==[]and out['last_confirmed']is None and out['checkpoint']is None
    finally:directory.chmod(mode)


@pytest.mark.parametrize('failure',['domain','late_profile'])
def test_failure_after_one_confirmed_interval_keeps_only_currently_valid_prefix(prepared,monkeypatch,failure):
    from app import crop_supply_morphology_resume as model
    cp=model.start(prepared);first=model.advance_chunk(prepared,cp,1)
    run=model.bound.stage.evaluate;calls=[]
    profile=prepared._source._source._root._profiles[0];original=profile.filtered_temperature_bounds
    def changed(*args,**kw):
        calls.append(1)
        if len(calls)==6 and failure=='domain':raise ValueError('DOMAIN_HOLD: second interval unsupported')
        out=run(*args,**kw)
        if len(calls)==9 and failure=='late_profile':object.__setattr__(profile,'filtered_temperature_bounds',(1.,2.))
        return out
    monkeypatch.setattr(model.bound.stage,'evaluate',changed)
    try:
        out=model.advance_chunk(prepared,cp,2)
        assert out['status']=='hold'and out['checkpoint']is None
        if failure=='domain':
            assert out['last_confirmed']==first['checkpoint'].value and out['samples']==first['samples']and out['intervals']==first['intervals']
        else:assert out['last_confirmed']is None and out['samples']==out['intervals']==[]
    finally:object.__setattr__(profile,'filtered_temperature_bounds',original)


def test_current_new_solver_code_pin_is_checked_before_emitting_bytes(prepared,monkeypatch):
    from app import crop_supply_morphology_resume as model
    cp=model.start(prepared)
    monkeypatch.setattr(model,'CODE_SHA256','0'*64)
    with pytest.raises(model.SupplyResumeHold,match='CODE_HOLD'):model.checkpoint_bytes(prepared,cp)


@pytest.mark.parametrize('kind',['context','checkpoint'])
def test_oversized_new_raw_bytes_hold_before_parsing_or_rhs(prepared,monkeypatch,kind):
    from app import crop_supply_morphology_resume as model
    def forbidden(*args,**kw):raise AssertionError('oversized raw data cannot run RHS')
    monkeypatch.setattr(model.bound.stage,'evaluate',forbidden)
    raw=b' '*(model.MAX_BYTES+1 if kind=='context'else model.MAX_CP+1)
    with pytest.raises(model.SupplyResumeHold,match='CAPACITY_HOLD'if kind=='context'else'HASH_HOLD'):
        if kind=='context':model.restore_context(prepared._source,raw,expected_sha256=sha256(raw).hexdigest(),proof_bytes=model.proof_bytes(prepared))
        else:model.restore_checkpoint(prepared,raw,expected_sha256=sha256(raw).hexdigest())
