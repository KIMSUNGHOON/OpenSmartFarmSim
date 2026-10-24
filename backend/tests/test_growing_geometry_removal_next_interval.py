from copy import deepcopy
from dataclasses import replace
from decimal import Decimal,localcontext
from fractions import Fraction
from hashlib import sha256
import importlib.util
import json
from math import ulp
from pathlib import Path

import pytest

from app import crop_growing_geometry_removal_next_interval as model
from app import crop_growing_geometry_post_removal_context as post
from app import crop_growing_geometry_continuation as parent
from test_growing_geometry_leaf_removal_point import profiles,samples,CASES,declaration
from test_growing_geometry_post_removal_context import capture


@pytest.fixture(scope='module')
def contexts(samples):
    return {(case,position,indices):capture(ctx,points[position],indices)
        for case,(ctx,points)in enumerate(samples)for position in range(3)for indices in ((0,),(0,2))}


def collect(ctx,budget):
    cp=model.start(ctx);data=[cp.value['last_confirmed']];chunks=[]
    while cp.value['segment_step_index']<ctx.manifest['numerical']['remaining_steps']:
        cp=model.restore_checkpoint(ctx,model.checkpoint_bytes(ctx,cp),expected_sha256=cp.sha256)
        chunk=model.advance_chunk(ctx,cp,budget);assert chunk['status']!='hold',chunk['hold']
        data.extend(chunk['samples']);chunks.append(chunk);cp=chunk['checkpoint']
    return cp,data,chunks


@pytest.mark.parametrize('case',range(6))
@pytest.mark.parametrize('position',[0,1])
@pytest.mark.parametrize('indices',[(0,),(0,2)])
def test_actual_interval_and_independent_source_balances(contexts,case,position,indices):
    ctx=contexts[case,position,indices];final,data,chunks=collect(ctx,128);payload=final.value
    assert payload['global_step_index']==16
    assert payload['at_elapsed_seconds_exact']=={'numerator':'2','denominator':'1','unit':'s'}
    assert len(data)==ctx.manifest['numerical']['remaining_steps']+1
    assert payload['original_interval_transfers']==json.loads(ctx._seed)['original_interval_transfers']
    assert payload['point_outflows']==json.loads(ctx._seed)['point_outflows']
    n=len(ctx.active_program['leaves']);initial=data[0]['state'];y=data[-1]['state']
    assert all(y[108+i]>initial[108+i]for i in range(n))
    assert all(y[108+n+i]>initial[108+n+i]for i in range(n))
    assert y[:108]!=initial[:108]
    assert all(chunk['attempted_new_stage_evaluations']==4*chunk['confirmed_new_steps']for chunk in chunks)
    assert all(chunk['checkpoint_validation_stage_evaluations']==1 for chunk in chunks)
    with localcontext()as c:
        c.prec=120;d=Decimal.from_float;start=json.loads(ctx._parent._seed)['state']
        a=payload['original_interval_transfers'];b=payload['segment_integrated_transfers'];e=payload['point_outflows']
        transfer=lambda key:d(a[key]['value'])+d(b[key]['value'])
        carbon=sum((d(y[i])-d(start[i])for i in [0,1,2,*range(5,55)]),Decimal(0))-transfer('photosynthesis')
        carbon+=sum((transfer(k)for k in ['growth_respiration','maintenance_leaf','maintenance_stem','maintenance_fruit','removal_leaf','removal_stem','terminal_carbon']),Decimal(0))
        carbon+=d(e['carbohydrate']['value'])
        vapor=d(y[107])-d(start[107])-transfer('vapor')-transfer('external_vapor')
        heat=d(y[105])-d(start[105])-transfer('canopy_external')+transfer('sensible')+transfer('latent')-transfer('incoming_heat')+transfer('outgoing_heat')+d(e['sensible_energy']['value'])
        for key,reference in [('carbohydrate',carbon),('vapor',vapor),('canopy_sensible',heat)]:
            assert abs(reference)<=d(payload['global_balance_budgets'][key]['value'])
            assert abs(d(payload['global_balance_residuals'][key]['value'])-reference)<=d(payload['global_balance_budgets'][key]['value'])
    for i,chunk in enumerate(chunks):assert chunk['scope']=='software_research_only'and chunk['G0_G4']=='not_assessed'


@pytest.mark.parametrize('case',range(6))
@pytest.mark.parametrize('position',[0,1])
@pytest.mark.parametrize('indices',[(0,),(0,2)])
def test_all_single_cuts_and_multiple_budgets_match_bytes(contexts,case,position,indices):
    ctx=contexts[case,position,indices];whole,data,_=collect(ctx,128);count=ctx.manifest['numerical']['remaining_steps']
    for cut in range(1,count):
        start=model.start(ctx);first=model.advance_chunk(ctx,start,cut)
        cp=model.restore_checkpoint(ctx,first['checkpoint']._raw,expected_sha256=first['checkpoint'].sha256)
        last=model.advance_chunk(ctx,cp,128)
        assert [start.value['last_confirmed'],*first['samples'],*last['samples']]==data
        assert last['checkpoint']._raw==whole._raw
    for budget in (1,3):
        final,partitioned,_=collect(ctx,budget);assert final._raw==whole._raw and partitioned==data


def test_start_and_completed_roundtrip_and_no_remaining_step(contexts):
    ctx=contexts[0,2,(0,)];cp=model.start(ctx)
    assert cp.value['segment_step_index']==0
    assert model.restore_checkpoint(ctx,cp._raw,expected_sha256=cp.sha256)._raw==cp._raw
    with pytest.raises(model.RemovalIntervalHold,match='COMPLETED_HOLD'):model.advance_chunk(ctx,cp,1)


def test_restore_and_advance_never_reinitialize_replay_or_reapply_event(contexts,monkeypatch):
    ctx=contexts[0,1,(0,)];cp=model.advance_chunk(ctx,model.start(ctx),3)['checkpoint']
    def forbidden(*a,**k):raise AssertionError('no original initialization, point replay or past advancement')
    for owner,name in [(post,'prepare_context'),(post.point,'apply_removals'),(parent,'prepare_context'),(parent,'start'),
        (parent,'advance_chunk'),(parent.short,'_prepare'),(parent.short,'integrate')]:monkeypatch.setattr(owner,name,forbidden)
    restored=model.restore_checkpoint(ctx,cp._raw,expected_sha256=cp.sha256)
    assert model.advance_chunk(ctx,restored,128)['status']=='completed'


@pytest.mark.parametrize('mutation',[
    lambda x:x.update(segment_step_index=1),lambda x:x.update(global_step_index=0),
    lambda x:x['at_elapsed_seconds_exact'].update(numerator='1'),
    lambda x:x['last_confirmed']['state'].__setitem__(-1,.1),
    lambda x:x['last_confirmed']['derived']['leaf_area_index'].update(value=10),
    lambda x:x['original_interval_transfers']['photosynthesis'].update(value=0),
    lambda x:x['point_outflows']['carbohydrate'].update(value=0),
    lambda x:x['point_outflows']['capacity'].update(value=0),
    lambda x:x['segment_integrated_transfers']['photosynthesis'].update(unit='mg_CH2O'),
    lambda x:x['segment_integrated_transfers']['photosynthesis'].update(value=0),
    lambda x:x['global_balance_residuals']['carbohydrate'].update(value=999),
    lambda x:x['global_balance_budgets']['carbohydrate'].update(value=999),
    lambda x:x['active_original_curve_invariant'][0].update(value=1),
    lambda x:x['engine_identity'].update(code_sha256='0'*64),
    lambda x:x.update(output_prefix_sha256='broken'),lambda x:x.update(extra=1),
])
def test_rehashed_checkpoint_changes_are_rejected(contexts,mutation):
    ctx=contexts[0,1,(0,)];cp=model.advance_chunk(ctx,model.start(ctx),3)['checkpoint'];value=cp.value;mutation(value)
    raw=parent._canonical(value)
    with pytest.raises(model.RemovalIntervalHold):model.restore_checkpoint(ctx,raw,expected_sha256=sha256(raw).hexdigest())


@pytest.mark.parametrize('budget',[0,129,True,1.0,None])
def test_bad_budget_rejected_without_input_changes(contexts,budget):
    ctx=contexts[0,1,(0,)];cp=model.start(ctx);old=cp._raw
    with pytest.raises(model.RemovalIntervalHold,match='BUDGET_HOLD'):model.advance_chunk(ctx,cp,budget)
    assert cp._raw==old


@pytest.mark.parametrize('stage',['k2','k3','k4','endpoint'])
def test_stage_hold_keeps_exact_last_confirmed_prefix(contexts,monkeypatch,stage):
    ctx=contexts[0,1,(0,)];cp=model.start(ctx);expected=model.advance_chunk(ctx,cp,1)['checkpoint']
    original=parent.short._evaluate;calls=0;failure={'k2':6,'k3':7,'k4':8,'endpoint':9}[stage]
    def injected(*a,**k):
        nonlocal calls
        calls+=1
        if calls==failure:raise parent.short.GrowingGeometryHold('INJECTED_DOMAIN_HOLD')
        return original(*a,**k)
    monkeypatch.setattr(parent.short,'_evaluate',injected)
    result=model.advance_chunk(ctx,cp,3)
    assert result['status']=='hold'and result['hold']['stage']==stage
    assert result['confirmed_new_steps']==1 and len(result['samples'])==1
    assert result['checkpoint']is None and result['confirmed_checkpoint']._raw==expected._raw
    assert result['last_confirmed']==expected.value['last_confirmed']


def test_old_models_and_different_contexts_are_rejected(contexts):
    one=contexts[0,1,(0,)];other=contexts[1,1,(0,)];cp=model.start(other)
    with pytest.raises(model.RemovalIntervalHold):model.checkpoint_bytes(one,cp)
    snapshot=post.snapshot(one)
    with pytest.raises(model.RemovalIntervalHold):model.restore_checkpoint(one,snapshot._raw,expected_sha256=snapshot.sha256)
    with pytest.raises(post.PostRemovalContextHold):post.restore_checkpoint(one,model.start(one)._raw,expected_sha256=model.start(one).sha256)


def test_start_binds_original_receipts_without_rhs_or_large_copies(contexts,monkeypatch):
    ctx=contexts[0,1,(0,)];seed=json.loads(ctx._seed)
    def forbidden(*a,**k):raise AssertionError('start cannot evaluate RHS')
    monkeypatch.setattr(parent.short,'_evaluate',forbidden);cp=model.start(ctx)
    for name in ('original_curve_invariant','original_initial_area_receipts','removed_last_states'):
        assert cp.value[name+'_sha256']==sha256(parent._canonical(seed[name])).hexdigest()
    assert cp.value['event_snapshot_sha256']==post.snapshot(ctx).sha256


@pytest.mark.parametrize('field',['carbohydrate','capacity','sensible_energy'])
@pytest.mark.parametrize('factor',[0,2])
def test_global_balance_detects_missing_or_double_event(contexts,field,factor):
    ctx=contexts[0,1,(0,)];p,seed,m=post._context(ctx);cp=model.start(ctx);changed=deepcopy(seed)
    changed['point_outflows'][field]['value']*=factor
    with pytest.raises(model.RemovalIntervalHold,match='GLOBAL_BALANCE_HOLD'):
        model._global_balances(ctx,p,changed,m,tuple(seed['last_confirmed']['state']),(0.0,)*21,
            model._first(seed),cp.value['balance_budgets'],m['numerical']['event_global_step_index'])


@pytest.mark.parametrize('fault',['code','post_code','parent_code','token','raw_hash','CP_size','response_size'])
def test_engine_and_size_boundaries(contexts,monkeypatch,fault):
    ctx=contexts[0,1,(0,)];cp=model.start(ctx)
    if fault=='code':monkeypatch.setattr(model,'CODE_SHA256','0'*64)
    if fault=='post_code':monkeypatch.setattr(post,'CODE_SHA256','0'*64)
    if fault=='parent_code':monkeypatch.setattr(parent,'CODE_SHA256','0'*64)
    if fault=='token':cp=replace(cp,_token=object())
    if fault=='raw_hash':cp=replace(cp,_raw=cp._raw+b' ')
    if fault=='CP_size':monkeypatch.setattr(model,'MAX_CHECKPOINT_BYTES',128)
    if fault=='response_size':monkeypatch.setattr(model,'MAX_RESPONSE_BYTES',128)
    with pytest.raises(model.RemovalIntervalHold):model.advance_chunk(ctx,cp,1)


def test_512_original_leaves_advance_within_the_same_byte_limits(profiles):
    p=deepcopy(CASES[0]['program']);p['capacity_outflow']['value']=0
    p['leaves']=[{**deepcopy(p['leaves'][0]),'leaf_id':f'own-{i}'}for i in range(512)];p['model_floor_area']['value']=512
    k=p['scenario']['parameters']['leaf_heat_capacity']['value'];ref=p['scenario']['parameters']['reference_temperature']['value']
    p['scenario']['climate_state']['canopy_sensible_energy']['value']=k*.25*(20-ref)
    old=parent.prepare_context(program=p,step_seconds=.125,step_count=1,**profiles);cp=parent.start(old)
    ctx=post.prepare_context(parent_context=old,raw_parent_checkpoint=cp._raw,expected_parent_sha256=cp.sha256,inputs=declaration(old,cp))
    start=model.start(ctx);result=model.advance_chunk(ctx,start,1);assert result['status']=='completed',result['hold']
    assert len(result['last_confirmed']['state'])==108+2*511
    assert len(result['checkpoint']._raw)<=256*1024
    assert all(x>y for x,y in zip(result['last_confirmed']['state'][108:],start.value['last_confirmed']['state'][108:],strict=True))


@pytest.mark.parametrize('indices',[(0,),(0,2)])
def test_independent_decimal_rk4_driver(contexts,indices):
    path=Path(__file__).resolve().parents[2]/'research/growing-geometry-removal-rk4-reference.py'
    spec=importlib.util.spec_from_file_location('removal_rk_reference',path);reference=importlib.util.module_from_spec(spec);spec.loader.exec_module(reference)
    ctx=contexts[0,1,indices];p,seed,m=post._context(ctx)
    def rhs(y):
        rates,value=parent.short._evaluate(p,y,parent._profiles(ctx._parent))
        return rates,parent.short._flux(p,y,value)
    expected=reference.integrate(state=seed['last_confirmed']['state'],dt=m['numerical']['step_seconds'],steps=m['numerical']['remaining_steps'],rhs=rhs)
    final,actual,_=collect(ctx,128)
    for predicted,observed in zip(expected,actual,strict=True):
        for a,b in zip(observed['state'],predicted['state'],strict=True):
            assert a==0 if b==0 else abs(a-b)<=max(64*ulp(b),3e-13*abs(b))
    for name,value in zip(parent.short.FLUX_UNITS,expected[-1]['transfers'],strict=True):
        actual=final.value['segment_integrated_transfers'][name]['value']
        assert actual==0 if value==0 else abs(actual-value)<=max(64*ulp(value),3e-13*abs(value))


@pytest.mark.parametrize('stage',['endpoint_balance','endpoint_global_balance','checkpoint'])
def test_balance_or_checkpoint_failure_keeps_last_confirmed(contexts,monkeypatch,stage):
    ctx=contexts[0,1,(0,)];cp=model.start(ctx);expected=model.advance_chunk(ctx,cp,1)['checkpoint']
    name={'endpoint_balance':'_segment_balances','endpoint_global_balance':'_global_balances','checkpoint':'_seal'}[stage]
    old=getattr(model,name);event=ctx.manifest['numerical']['event_global_step_index']
    def injected(*a,**k):
        failing=(a[6]==2 if stage=='endpoint_balance'else a[8]==event+2 if stage=='endpoint_global_balance'else a[1]['segment_step_index']==2)
        if failing:raise model.RemovalIntervalHold('INJECTED_PUBLICATION_BOUNDARY_HOLD')
        return old(*a,**k)
    monkeypatch.setattr(model,name,injected);result=model.advance_chunk(ctx,cp,3)
    assert result['status']=='hold'and result['hold']['stage']==stage
    assert result['checkpoint']is None and result['confirmed_checkpoint']._raw==expected._raw
    assert result['last_confirmed']==expected.value['last_confirmed']and len(result['samples'])==1
