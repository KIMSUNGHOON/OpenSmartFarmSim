from copy import deepcopy
from dataclasses import replace
from hashlib import sha256
import json
from math import fsum

import pytest

from app import crop_leaf_carbon_stock_continuation as model
from app import crop_leaf_carbon_stock_dynamics as short
from test_crop_leaf_carbon_stock_dynamics import REFERENCE_STOCK,q
from test_crop_growing_geometry_climate import profiles


def raw(v):return json.dumps(v,sort_keys=True,separators=(',',':'),ensure_ascii=False,allow_nan=False).encode()


@pytest.fixture(scope='module')
def cases(profiles):
    rows=[]
    for item in REFERENCE_STOCK['cases']:
        p=item['program'];ctx=model.prepare_context(program=p,step_seconds=.125,step_count=4,**profiles)
        initial=model.start(ctx);whole=model.advance_chunk(ctx,initial,4)
        rows.append((ctx,initial,whole,short.integrate(program=p,step_seconds=.125,step_count=4,**profiles)))
    return rows


def compositions(n):
    if n==0:return [()]
    return [(a,*rest)for a in range(1,n+1)for rest in compositions(n-a)]


@pytest.mark.parametrize('case',range(6))
@pytest.mark.parametrize('grouping',compositions(4))
def test_every_fourstep_grouping_preserves_exact_samples_flows_and_final_bytes(cases,case,grouping):
    ctx,initial,whole,reference=cases[case];cp=model.start(ctx);samples=[initial.value['last_confirmed']]
    for count in grouping:
        out=model.advance_chunk(ctx,cp,count);assert out['status']in('yielded','completed')
        assert out['attempted_new_stage_evaluations']==4*count and out['checkpoint_validation_stage_evaluations']==1
        samples.extend(out['samples']);cp=out['checkpoint'];payload=model.checkpoint_bytes(ctx,cp)
        cp=model.restore_checkpoint(ctx,payload,expected_sha256=sha256(payload).hexdigest())
    assert samples==reference['samples']and out['status']=='completed'
    for name in('integrated_transfers','balance_residuals','balance_budgets'):assert out[name]==reference[name]
    assert model.checkpoint_bytes(ctx,cp)==model.checkpoint_bytes(ctx,whole['checkpoint'])


@pytest.fixture(scope='module')
def long_case(profiles):
    p=REFERENCE_STOCK['cases'][0]['program'];ctx=model.prepare_context(program=p,step_seconds=2,step_count=16,**profiles)
    first=model.start(ctx);whole=model.advance_chunk(ctx,first,16)
    return ctx,first,whole,short.integrate(program=p,step_seconds=2,step_count=16,**profiles)


@pytest.mark.parametrize('cut',range(1,16))
def test_every_single_cut_of_representative_32seconds_is_bit_equal(long_case,cut):
    ctx,first,whole,reference=long_case;a=model.advance_chunk(ctx,first,cut);blob=model.checkpoint_bytes(ctx,a['checkpoint'])
    restored=model.restore_checkpoint(ctx,blob,expected_sha256=sha256(blob).hexdigest());b=model.advance_chunk(ctx,restored,16-cut)
    assert [first.value['last_confirmed'],*a['samples'],*b['samples']]==reference['samples']
    assert b['integrated_transfers']==reference['integrated_transfers']and b['balance_residuals']==reference['balance_residuals']
    assert model.checkpoint_bytes(ctx,b['checkpoint'])==model.checkpoint_bytes(ctx,whole['checkpoint'])


@pytest.mark.parametrize('case',range(6))
def test_initial_middle_completed_restore_and_completed_advance_rejection(cases,case):
    ctx,first,whole,_=cases[case];middle=model.advance_chunk(ctx,first,2)['checkpoint']
    for cp in(first,middle,whole['checkpoint']):
        blob=model.checkpoint_bytes(ctx,cp);r=model.restore_checkpoint(ctx,blob,expected_sha256=cp.sha256)
        assert r.value==cp.value and r.sha256==cp.sha256 and model.checkpoint_bytes(ctx,r)==blob
    with pytest.raises(model.ContinuationRejected,match='COMPLETED_HOLD'):model.advance_chunk(ctx,whole['checkpoint'],1)


def test_start_uses_seed_and_restore_reuses_current_state_without_reinitialization(cases,monkeypatch):
    ctx,first,_,_=cases[0];middle=model.advance_chunk(ctx,first,2)['checkpoint'];blob=model.checkpoint_bytes(ctx,middle)
    calls=[];evaluate=short._evaluate
    def forbidden(*a,**k):raise AssertionError('no initial canonicalization or old replay')
    def counted(p,y,profiles):calls.append(tuple(y));return evaluate(p,y,profiles)
    monkeypatch.setattr(short,'_prepare',forbidden);monkeypatch.setattr(short.old,'_prepare',forbidden)
    monkeypatch.setattr(short,'integrate',forbidden);monkeypatch.setattr(short,'_evaluate',counted)
    assert model.start(ctx).value==first.value and calls==[]
    cp=model.restore_checkpoint(ctx,blob,expected_sha256=middle.sha256);assert len(calls)==1 and list(calls[0])==middle.value['last_confirmed']['state']
    out=model.advance_chunk(ctx,cp,1);assert len(calls)==6 and out['confirmed_new_steps']==1
    assert out['last_confirmed']['state'][113]!=first.value['last_confirmed']['state'][113]


@pytest.mark.parametrize('change',[
    lambda v:v.update(extra=1),lambda v:v.pop('version'),lambda v:v.update(version='growing-geometry-companion-checkpoint-v1'),
    lambda v:v.update(context_sha256='0'*64),lambda v:v.update(step_index=True),lambda v:v.update(step_index=-1),
    lambda v:v.update(step_index=5),lambda v:v.update(output_cursor=2),lambda v:v.update(output_prefix_sha256='not-a-digest'),
    lambda v:v['last_confirmed'].update(extra=1),lambda v:v['last_confirmed'].update(elapsed_seconds=99.),
    lambda v:v['last_confirmed']['state'].pop(),lambda v:v['last_confirmed']['state'].__setitem__(0,True),
    lambda v:v['last_confirmed']['state'].__setitem__(113,-1.),lambda v:v['last_confirmed']['state'].__setitem__(110,0.),
    lambda v:v['last_confirmed']['derived']['leaf_carbohydrate'].update(value=0.),
    lambda v:v['last_confirmed']['curve_residuals'][0].update(value=1.),
    lambda v:v['last_confirmed']['curve_invariant_changes'][0].update(value=1.),
    lambda v:v['integrated_transfers'].pop('leaf_0_inflow'),lambda v:v['integrated_transfers']['leaf_0_inflow'].update(value=True),
    lambda v:v['integrated_transfers']['leaf_0_inflow'].update(unit='mg_CH2O'),
    lambda v:v['integrated_transfers']['leaf_0_inflow'].update(value=1.),
    lambda v:v['balance_residuals']['leaf_carbon_0'].update(value=1.),lambda v:v['balance_budgets']['leaf_carbon_0'].update(value=1.)])
def test_rehashed_but_malformed_or_inconsistent_checkpoint_is_rejected(cases,change):
    ctx,cp,_,_=cases[0];value=cp.value;change(value);blob=raw(value)
    with pytest.raises(model.ContinuationRejected):model.restore_checkpoint(ctx,blob,expected_sha256=sha256(blob).hexdigest())


@pytest.mark.parametrize('bad',[b'',b'\xff',b'{}',b'null',b'{"value":NaN}',b'{"value":Infinity}'])
def test_external_invalid_json_utf8_constants_or_empty_checkpoint(cases,bad):
    ctx=cases[0][0]
    with pytest.raises(model.ContinuationRejected):model.restore_checkpoint(ctx,bad,expected_sha256=sha256(bad).hexdigest())


def test_expected_digest_canonical_bytes_and_duplicate_keys(cases):
    ctx,cp,_,_=cases[0];blob=model.checkpoint_bytes(ctx,cp)
    with pytest.raises(model.ContinuationRejected):model.restore_checkpoint(ctx,blob,expected_sha256='0'*64)
    for bad in(blob+b'\n',json.dumps(cp.value,indent=2).encode(),blob[:-1]+b',"step_index":0}'):
        with pytest.raises(model.ContinuationRejected):model.restore_checkpoint(ctx,bad,expected_sha256=sha256(bad).hexdigest())


@pytest.mark.parametrize('part',['_request','_program','_seed','_manifest','root_sha256','_profiles','_token'])
def test_mutated_context_bytes_profile_or_token_rejected(cases,part):
    ctx=cases[0][0]
    value=(object(),)*4 if part=='_profiles'else object()if part=='_token'else'0'*64 if part=='root_sha256'else b'{}'
    with pytest.raises(model.ContinuationRejected):model.start(replace(ctx,**{part:value}))


@pytest.mark.parametrize('kind',['engine','short','environment'])
def test_actual_code_and_environment_fence(cases,kind,monkeypatch):
    if kind=='engine':monkeypatch.setattr(model,'CODE_SHA256','0'*64)
    elif kind=='short':monkeypatch.setattr(short,'CODE_SHA256','0'*64)
    else:monkeypatch.setattr(model.platform,'machine',lambda:'changed-machine')
    with pytest.raises(model.ContinuationRejected):model.start(cases[0][0])


@pytest.mark.parametrize('budget',[0,-1,True,129,1.,None])
def test_step_budget_rejected_without_advancing(cases,budget):
    ctx,cp,_,_=cases[0]
    with pytest.raises(model.ContinuationRejected):model.advance_chunk(ctx,cp,budget)


@pytest.mark.parametrize('phase',['k2','k3','k4','endpoint','endpoint_balance','checkpoint'])
def test_failed_step_never_publishes_partial_state_or_transfers(cases,phase,monkeypatch):
    ctx,cp,_,_=cases[0];baseline=model.advance_chunk(ctx,cp,1);current=baseline['checkpoint'];calls=[]
    if phase in('k2','k3','k4','endpoint'):
        fn=short._evaluate;target={'k2':2,'k3':3,'k4':4,'endpoint':5}[phase]
        def failed(p,y,profiles):
            calls.append(1)
            if len(calls)==target:raise short.StockDynamicsHold('NUMERIC_HOLD: owned stage fault')
            return fn(p,y,profiles)
        monkeypatch.setattr(short,'_evaluate',failed)
    elif phase=='endpoint_balance':
        fn=short._balances
        def failed(*a):
            if a[6]==2:raise short.StockDynamicsHold('BALANCE_HOLD: owned endpoint fault')
            return fn(*a)
        monkeypatch.setattr(short,'_balances',failed)
    else:
        fn=model._seal
        def failed(context,payload):
            if payload['step_index']==2:raise model.ContinuationRejected('CAPACITY_HOLD: owned seal fault')
            return fn(context,payload)
        monkeypatch.setattr(model,'_seal',failed)
    out=model.advance_chunk(ctx,current,3)
    assert out['status']=='hold'and out['hold']['step_index']==2 and out['hold']['stage']==phase
    assert out['samples']==[]and out['checkpoint']is None and out['last_confirmed']==baseline['last_confirmed']
    for name in('integrated_transfers','balance_residuals','balance_budgets'):assert out[name]==baseline[name]


@pytest.mark.parametrize('kind',[KeyboardInterrupt,RuntimeError])
def test_cancel_or_external_error_is_not_converted_to_success_or_numerical_hold(cases,kind,monkeypatch):
    ctx,cp,_,_=cases[0]
    def failed(*a,**k):raise kind('owned external interruption')
    monkeypatch.setattr(short,'_evaluate',failed)
    with pytest.raises(kind):model.advance_chunk(ctx,cp,1)


def test_public_copies_and_frozen_handles(cases):
    ctx,cp,_,_=cases[0];original_request=ctx.program;original_payload=cp.value
    p=ctx.program;p['leaves'][0]['initial_carbon']['value']=0
    value=cp.value;value['last_confirmed']['state'][113]=0
    assert ctx.program==original_request and cp.value==original_payload
    with pytest.raises(AttributeError):ctx.root_sha256='0'*64
    with pytest.raises(model.ContinuationRejected):model.checkpoint_bytes(ctx,object())


@pytest.mark.parametrize('count',[1,512])
def test_inventory_boundary_roundtrip_and_dynamic_perleaf_transfer_order(profiles,count):
    p=deepcopy(REFERENCE_STOCK['cases'][0]['program']);C=fsum(x['initial_carbon']['value']for x in p['leaves']);leaf=deepcopy(p['leaves'][0])
    p['leaves']=[{**deepcopy(leaf),'leaf_id':f'bounded-{i}','initial_carbon':q(C/count,'mg_CH2O/m2_floor'),
        'sink_weight':q(float(i%7)if count>1 else 1.,'1'),'carbon_removal':q(0.,'mg_CH2O/m2_floor/s')}for i in range(count)]
    p['model_floor_area']['value']=count*.25/1.33
    ctx=model.prepare_context(program=p,step_seconds=.125,step_count=1,**profiles);cp=model.start(ctx)
    for step in(0,1):
        blob=model.checkpoint_bytes(ctx,cp);assert len(blob)<=model.MAX_CHECKPOINT_BYTES
        cp=model.restore_checkpoint(ctx,blob,expected_sha256=sha256(blob).hexdigest())
        assert len(cp.value['last_confirmed']['state'])==107+3*count and len(cp.value['integrated_transfers'])==21+3*count
        if step==0:cp=model.advance_chunk(ctx,cp,1)['checkpoint'];assert cp is not None


@pytest.mark.parametrize('dt,count',[(0,1),(-1,1),(True,1),(1,0),(1,True),(1,4097),(601,1),(.125,252)])
def test_prepare_step_horizon_and_sample_capacity_limits(profiles,dt,count):
    with pytest.raises(model.ContinuationRejected):model.prepare_context(program=REFERENCE_STOCK['cases'][0]['program'],step_seconds=dt,step_count=count,**profiles)


def test_exact_scalar_boundary_context_checkpoint_size_and_required_profiles(profiles,cases,monkeypatch):
    p=REFERENCE_STOCK['cases'][0]['program'];ctx=model.prepare_context(program=p,step_seconds=.125,step_count=251,**profiles)
    assert ctx.manifest['numerical']['step_count']==251
    for altered in({k:v for k,v in profiles.items()if k!='growth_profile'},{**profiles,'extra':object()}):
        with pytest.raises(model.ContinuationRejected):model.prepare_context(program=p,step_seconds=.125,step_count=1,**altered)
    monkeypatch.setattr(model,'MAX_CONTEXT_BYTES',100)
    with pytest.raises(model.ContinuationRejected):model.start(cases[0][0])
    monkeypatch.setattr(model,'MAX_CONTEXT_BYTES',2*1024**2);monkeypatch.setattr(model,'MAX_CHECKPOINT_BYTES',100)
    with pytest.raises(model.ContinuationRejected,match='CAPACITY_HOLD'):model.start(cases[0][0])


def test_component_fence_failure_during_seal_has_continuation_error_type(cases,monkeypatch):
    calls=[];fn=short._fence
    def changed():
        calls.append(1)
        if len(calls)==2:raise short.StockDynamicsHold('CODE_HOLD: owned late component change')
        return fn()
    monkeypatch.setattr(short,'_fence',changed)
    with pytest.raises(model.ContinuationRejected,match='CODE_HOLD'):model.start(cases[0][0])
