from copy import deepcopy
from decimal import Decimal, localcontext
from fractions import Fraction
from hashlib import sha256
from math import ulp
import json

import pytest

from app import crop_organ_fractional_candidate as model
from test_crop_organ_next_threshold import crossings, contexts, roots, stored, profiles, TOLERANCE, frac

stock = model.stock


def calculate(ctx,cp,**kw):
    return model.calculate_fractional_shoot_candidate(ctx,stock.checkpoint_bytes(ctx,cp),expected_sha256=cp.sha256,
        time_tolerance_seconds_exact=kw.get('tolerance',TOLERANCE))


@pytest.mark.parametrize('case',range(4))
def test_actual_all_components_exact_time_independent_dense_arithmetic_and_prefix_composition(crossings,case):
    ctx,cp,_=crossings[case];before=stock.context_bytes(ctx);raw=stock.checkpoint_bytes(ctx,cp);result=calculate(ctx,cp)
    certificate=result['source_root_certificate'];rows=certificate['stages'];selected=certificate['numerical_root_interval']['upper_elapsed_seconds_exact']
    assert result['at']['elapsed_seconds_exact']==selected and result['source_prefix']==cp.value
    assert result['integrator_checkpoint']is None and result['new_internodes']=='not_created'and result['schedule_adoption']=='not_performed'
    assert result['redistribution_authorized']is False and result['G0_G4']=='not_assessed'
    assert result['state_layout']==ctx.manifest['state_layout']and len(result['dense_candidate']['state'])==106+3*len(ctx.program['leaves'])+len(ctx.program['stem_root_compartments'])
    assert [r['substeps']for r in result['refinements']]==[1,2,4]and result['rhs_evaluations']==37
    duration=frac(result['partial_interval_seconds_exact']);dt=frac(certificate['step_seconds_exact']);theta=duration/dt
    with localcontext()as precision:
        precision.prec=200;D=lambda x:Decimal(x.numerator)/Decimal(x.denominator);z=D(theta)
        weights=[z-3*z*z/2+2*z*z*z/3,z*z-2*z*z*z/3,z*z-2*z*z*z/3,-z*z/2+2*z*z*z/3]
        for i,value in enumerate(result['dense_candidate']['state']):
            expected=Decimal.from_float(rows[0]['state'][i])+D(dt)*sum((w*Decimal.from_float(r['rates'][i])for w,r in zip(weights,rows,strict=True)),Decimal(0))
            assert abs(Decimal.from_float(value)-expected)<=Decimal.from_float(ulp(value))/2
        for i,q in enumerate(certificate['stage_flux_order']):
            value=result['dense_candidate']['partial_interval_transfers'][q['name']]['value'];expected=D(dt)*sum((w*Decimal.from_float(r['flux'][i])for w,r in zip(weights,rows,strict=True)),Decimal(0))
            assert abs(Decimal.from_float(value)-expected)<=Decimal.from_float(ulp(value))/2
    for packet in [result['dense_candidate'],*result['refinements']]:
        assert len(packet['local_ledgers'])==8+2*len(ctx.program['leaves'])+len(ctx.program['stem_root_compartments'])
        for name,row in packet['local_ledgers'].items():
            assert abs(frac(row['residual_exact']))<=frac(row['budget_exact'])
            global_row=packet['global_ledgers'][name];source=result['source_global_ledgers'][name]
            assert frac(global_row['residual_exact'])==frac(source['residual_exact'])+frac(row['residual_exact'])
            assert frac(global_row['budget_exact'])==frac(source['budget_exact'])+frac(row['budget_exact'])
            assert abs(frac(global_row['residual_exact']))<=frac(global_row['budget_exact'])
        for name,value in packet['partial_interval_transfers'].items():
            assert frac(packet['pending_lifetime_transfers_exact'][name])==Fraction.from_float(cp.value['integrated_transfers'][name]['value'])+Fraction.from_float(value['value'])
    assert frac(result['dense_candidate']['shoot_threshold_residual_exact'])>=0
    weights=(Fraction(1,6),Fraction(1,3),Fraction(1,3),Fraction(1,6));comparison=result['full_step_dense_comparison']
    for i,value in enumerate(comparison['state_differences_exact']):
        full=float(Fraction.from_float(rows[0]['state'][i])+dt*sum((w*Fraction.from_float(row['rates'][i])for w,row in zip(weights,rows,strict=True)),Fraction(0)))
        assert frac(value)==Fraction.from_float(full)-Fraction.from_float(certificate['unadopted_endpoint']['last_confirmed']['state'][i])
        assert value['unit']==result['state_coordinates'][i]['unit']
    assert result['calculation_sha256']==sha256(stock._canonical({k:v for k,v in result.items()if k!='calculation_sha256'})).hexdigest()
    assert stock.context_bytes(ctx)==before and stock.checkpoint_bytes(ctx,cp)==raw


def test_current_only_37_rhs_no_legacy_vector_ledger_or_old_replay(crossings,monkeypatch):
    ctx,cp,_=crossings[0];calls=[];evaluate=stock.short._evaluate
    def counted(*a,**k):calls.append(1);return evaluate(*a,**k)
    monkeypatch.setattr(stock.short,'_evaluate',counted)
    def forbidden(*a,**k):raise AssertionError('no old vector ledger/replay/initialization')
    for owner,name in [(model.old,'_ledgers'),(model.old,'_refine'),(stock,'advance_chunk'),(stock,'adopt_births'),(stock,'prepare_context'),(stock,'_seal'),
        (stock.leaf,'_jump'),(stock.stem,'_jump'),(stock.short.old.leaf_area,'initialize_leaf_area'),(stock.short.old.leaf_area,'normalize_leaf_area_state')]:monkeypatch.setattr(owner,name,forbidden)
    result=calculate(ctx,cp);assert len(calls)==result['rhs_evaluations']==37


@pytest.mark.parametrize('case',range(6))
@pytest.mark.parametrize('kind',['leaf','internode'])
def test_no_crossing_does_not_invent_an_event_candidate(contexts,case,kind):
    ctx,_=contexts[case,kind];cp=stock.start(ctx)
    with pytest.raises(model.FractionalCandidateHold,match='THRESHOLD_HOLD'):calculate(ctx,cp)


@pytest.mark.parametrize('stage',[6,7,8,12,20,37])
def test_domain_failure_in_dense_or_refinements_returns_no_candidate(crossings,monkeypatch,stage):
    ctx,cp,_=crossings[0];raw=stock.checkpoint_bytes(ctx,cp);before=stock.context_bytes(ctx);calls=[];evaluate=stock.short._evaluate
    def failed(*a,**k):
        calls.append(1)
        if len(calls)==stage:raise ValueError('DOMAIN_HOLD: explicit fractional stage failure')
        return evaluate(*a,**k)
    monkeypatch.setattr(stock.short,'_evaluate',failed)
    with pytest.raises(model.FractionalCandidateHold,match='DOMAIN_HOLD'):calculate(ctx,cp)
    assert len(calls)==stage and stock.checkpoint_bytes(ctx,cp)==raw and stock.context_bytes(ctx)==before


@pytest.mark.parametrize('kind',['code','capacity','hash','typed','context'])
def test_source_identity_and_bounds_hold(crossings,contexts,monkeypatch,kind):
    ctx,cp,_=crossings[0];raw=stock.checkpoint_bytes(ctx,cp);digest=cp.sha256
    if kind=='code':monkeypatch.setattr(model,'CODE_SHA256','0'*64)
    elif kind=='capacity':monkeypatch.setattr(model,'MAX_BYTES',100)
    elif kind=='hash':digest='0'*64
    elif kind=='typed':raw=cp
    else:ctx=contexts[0,'leaf'][0]
    with pytest.raises(model.FractionalCandidateHold):model.calculate_fractional_shoot_candidate(ctx,raw,expected_sha256=digest,time_tolerance_seconds_exact=TOLERANCE)


def test_exact_time_refinement_has_fourth_order_on_nonlinear_analytic_ode(monkeypatch):
    monkeypatch.setattr(stock.short,'_evaluate',lambda p,y,profiles:(tuple(v*v for v in y),{}))
    monkeypatch.setattr(stock.short,'_flux',lambda p,y,rhs:tuple(v*v for v in y))
    monkeypatch.setattr(stock.short,'_flux_units',lambda p:{'integral':'1'})
    monkeypatch.setattr(model,'_packet',lambda *a:{'state':list(a[6]),'transfers':list(a[7])})
    errors=[]
    with localcontext()as precision:
        precision.prec=100
        for count in (1,2,4,8):
            out=model._refine(None,{},None,{'last_confirmed':{'state':[1.]}},None,None,{},Fraction(1,4),count)
            errors.append(abs(Decimal.from_float(out['state'][0])-Decimal(4)/3))
        assert all(10<a/b<20 for a,b in zip(errors,errors[1:]))


@pytest.mark.parametrize('n,m',[(1,2),(128,256)])
def test_local_ledger_coordinates_across_inventory_shapes(contexts,n,m):
    ctx,_=contexts[0,'leaf'];p=ctx.program;p['leaves']=[deepcopy(p['leaves'][0])for _ in range(n)];p['stem_root_compartments']=[deepcopy(p['stem_root_compartments'][0])for _ in range(m)]
    state=[0.]*(106+3*n+m);state[0]=1.;state[103]=1.;state[104]=20.;state[105]=.001
    state[106:106+n]=[100.]*n;state[106+n:106+2*n]=[.1]*n;state[106+2*n:]=[1.]*(n+m)
    view={'air_capacity':{'value':1.},'canopy_capacity':{'value':1.}}
    transfers=(0.,)*len(stock.short._flux_units(p));result=model._local(p,state,state,transfers,view,view,Fraction(0),1.,1)
    assert len(result)==8+2*n+m and all(frac(q['residual_exact'])==0 for q in result.values())
    changed=state[:];changed[-1]+=.01
    with pytest.raises(model.FractionalCandidateHold,match='BALANCE_HOLD'):model._local(p,state,changed,transfers,view,view,Fraction(0),1.,1)


@pytest.mark.parametrize('kind',['certificate_hash','stage_hash'])
def test_corrupted_source_certificate_is_not_used(crossings,monkeypatch,kind):
    ctx,cp,_=crossings[0];original=model.interval.probe_next_shoot_threshold
    def changed(*a,**k):
        value=original(*a,**k);value['stages'][0]['rates'][0]+=.1
        if kind=='stage_hash':value['calculation_sha256']=sha256(stock._canonical({k:v for k,v in value.items()if k!='calculation_sha256'})).hexdigest()
        return value
    monkeypatch.setattr(model.interval,'probe_next_shoot_threshold',changed)
    with pytest.raises(model.FractionalCandidateHold,match='HASH_HOLD'):calculate(ctx,cp)


def test_false_local_ledger_cannot_bypass_exact_global_composition(crossings,monkeypatch):
    ctx,cp,_=crossings[0];original=model._local
    def changed(*a,**k):
        value=original(*a,**k);value['carbohydrate']['residual_exact']=model.Q(Fraction(1),model.MASS);return value
    monkeypatch.setattr(model,'_local',changed)
    with pytest.raises(model.FractionalCandidateHold,match='GLOBAL_COMPOSITION_HOLD'):calculate(ctx,cp)


def test_original_exact_global_prefix_must_fit_original_budget(crossings):
    ctx,cp,_=crossings[0];p,seed,_=stock._context(ctx);v=cp.value;original=model._source_global(ctx,p,seed,v)
    key=next(k for k,row in original.items()if frac(row['residual_exact'])!=0);v['global_balance_budgets'][key]['value']=0.
    with pytest.raises(model.FractionalCandidateHold,match='GLOBAL_PREFIX_HOLD'):model._source_global(ctx,p,seed,v)


def test_profile_changed_at_final_refinement_withholds_all_packets(crossings,monkeypatch):
    from types import MappingProxyType
    ctx,cp,_=crossings[0];profile=ctx._root._profiles[0];original=profile.values;evaluate=stock.short._evaluate;calls=[]
    def changed(*a,**k):
        value=evaluate(*a,**k);calls.append(1)
        if len(calls)==37:
            values=dict(original);key=next(iter(values));values[key]+=.001;object.__setattr__(profile,'values',MappingProxyType(values))
        return value
    monkeypatch.setattr(stock.short,'_evaluate',changed)
    try:
        with pytest.raises(model.FractionalCandidateHold,match='PROFILE_HOLD'):calculate(ctx,cp)
    finally:object.__setattr__(profile,'values',original)


def test_original_rights_changed_after_refinements_prevent_return(crossings,monkeypatch):
    ctx,cp,_=crossings[0];original=stock.leaf.binding.bind_initial_stem_carbon;calls=[]
    def changed(*a,**k):
        value=original(*a,**k);calls.append(1)
        if len(calls)>=5:value['source_rights']['stem']['display']=False
        return value
    monkeypatch.setattr(stock.leaf.binding,'bind_initial_stem_carbon',changed)
    with pytest.raises(model.FractionalCandidateHold,match='SOURCE_HOLD'):calculate(ctx,cp)


def test_legacy_pure_math_code_change_at_last_rhs_is_held(crossings,monkeypatch):
    ctx,cp,_=crossings[0];evaluate=stock.short._evaluate;calls=[]
    def changed(*a,**k):
        value=evaluate(*a,**k);calls.append(1)
        if len(calls)==37:monkeypatch.setattr(model.old,'CODE_SHA256','0'*64)
        return value
    monkeypatch.setattr(stock.short,'_evaluate',changed)
    with pytest.raises(model.FractionalCandidateHold):calculate(ctx,cp)


def test_runtime_error_is_not_reclassified_as_hold(crossings,monkeypatch):
    ctx,cp,_=crossings[0]
    def unexpected(*a,**k):raise RuntimeError('operator interruption')
    monkeypatch.setattr(stock.short,'_evaluate',unexpected)
    with pytest.raises(RuntimeError,match='operator interruption'):calculate(ctx,cp)
