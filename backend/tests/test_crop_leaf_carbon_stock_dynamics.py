from copy import deepcopy
from hashlib import sha256
import json
from math import fsum
from math import ulp
from pathlib import Path

import pytest

from app import crop_leaf_carbon_stock_dynamics as model
from app import crop_growing_geometry_climate as old
from test_crop_growing_geometry_climate import profiles,REFERENCE,q


def program(case=0,weights=(1.,2.,4.),shares=(.25,.25,.5)):
    p=deepcopy(REFERENCE[case]['program']);carbon=p['scenario']['plant_state'].pop('leaf')['value'];removal=p['scenario']['removals'].pop('leaf')['value']
    p['leaf_stock_policy']='leaf-stocks-uniform-maintenance-explicit-removal-v1'
    for leaf,w,share in zip(p['leaves'],weights,shares,strict=True):
        leaf.update(initial_carbon=q(carbon*share,'mg_CH2O/m2_floor'),sink_weight=q(w,'1'),carbon_removal=q(removal*share,'mg_CH2O/m2_floor/s'))
    return p


def run(p,profiles,dt=.125,count=8):return model.integrate(program=p,step_seconds=dt,step_count=count,**profiles)


@pytest.mark.parametrize('case',range(6))
@pytest.mark.parametrize('weights,shares',[((1.,2.,4.),(.25,.25,.5)),((0.,0.,0.),(.25,.25,.5)),((0.,1.,2.),(0.,.5,.5))])
def test_explicit_individual_state_and_all_ledgers_advance_without_aggregate_slot(profiles,case,weights,shares):
    p=program(case,weights,shares);before=deepcopy(p);r=run(p,profiles);first,last=r['samples'][0],r['samples'][-1];n=len(p['leaves'])
    assert len(first['state'])==len(last['state'])==107+3*n and 'leaf'not in r['state_layout']['plant']
    assert r['state_layout']['leaf_blocks']==['thermal_age','area','carbon']and r['numerical']['rhs_evaluations']==33
    assert len(r['samples'])==9 and last['elapsed_seconds']==1.
    assert [x['value']for x in(first['derived']['leaf_carbohydrate'],last['derived']['leaf_carbohydrate'])]==[
        fsum(first['state'][107+2*n:]),fsum(last['state'][107+2*n:])]
    for i in range(n):
        assert last['state'][107+i]>first['state'][107+i]and last['state'][107+n+i]>first['state'][107+n+i]
        assert 'leaf_carbon_'+str(i)in r['balance_residuals']
    assert len(r['integrated_transfers'])==21+3*n
    for name,v in r['balance_residuals'].items():assert abs(v['value'])<=r['balance_budgets'][name]['value'],name
    assert r['G0_G4']=='not_assessed'and r['claim_scope']=='synthetic_leaf_carbon_stock_short_integration_only'
    assert p==before and run(p,profiles)==r


def test_source_once_per_stage_no_old_rhs_or_integrator_and_only_initial_area_normalization(profiles,monkeypatch):
    p=program();calls=[];fn=model.stock.evaluate_rhs;prepare=old._prepare;prepared=[]
    def counted(**kw):calls.append(deepcopy(kw['leaf_stocks']));return fn(**kw)
    def once(v):prepared.append(1);return prepare(v)
    def forbidden(*a,**kw):raise AssertionError('no old whole geometry calculation')
    monkeypatch.setattr(model.stock,'evaluate_rhs',counted);monkeypatch.setattr(old,'_prepare',once)
    monkeypatch.setattr(old,'_evaluate',forbidden);monkeypatch.setattr(old,'integrate',forbidden)
    r=run(p,profiles,count=2);assert len(calls)==9 and len(prepared)==1
    assert len({tuple(x['carbon']['value']for x in c['leaves'])for c in calls})>1
    assert calls[-1]['leaves'][0]['carbon']['value']==r['samples'][-1]['state'][113]


def test_initial_receipt_and_no_later_resnap_or_initial_carbon_inference(profiles):
    p=program();p['leaves'][0]['initial_area']['value']*=1+2e-13;r=run(p,profiles,count=2)
    receipt=r['initial_area_receipts'][0];assert receipt['requested_area']!=receipt['canonical_area']
    assert r['samples'][0]['state'][110]==receipt['canonical_area']['value']
    assert r['samples'][0]['state'][113]==p['leaves'][0]['initial_carbon']['value']
    assert len(r['samples'][-1]['curve_invariant_changes'])==3


@pytest.mark.parametrize('change',[
    lambda p:p.pop('leaf_stock_policy'),lambda p:p.update(leaf_stock_policy='default'),lambda p:p.update(origin='observed'),
    lambda p:p['scenario']['plant_state'].update(leaf=q(1,'mg_CH2O/m2_floor')),
    lambda p:p['scenario']['removals'].update(leaf=q(0,'mg_CH2O/m2_floor/s')),
    lambda p:p['leaves'][0].pop('initial_carbon'),lambda p:p['leaves'][0]['initial_carbon'].update(unit='mg_CH2O'),
    lambda p:p['leaves'][0]['initial_carbon'].update(value=-1),lambda p:p['leaves'][0]['sink_weight'].update(value=True),
    lambda p:p['leaves'][0]['carbon_removal'].update(value=-1),lambda p:p['leaves'][0].update(extra=1),
    lambda p:p['leaves'].append(deepcopy(p['leaves'][0])),lambda p:p.update(leaves=[]),
    lambda p:p['leaves'][0]['initial_area'].update(value=.01),lambda p:p['model_floor_area'].update(value=0)])
def test_closed_explicit_state_policy_units_and_basis(profiles,change):
    p=program();change(p)
    with pytest.raises(model.StockDynamicsHold):run(p,profiles,count=1)


@pytest.mark.parametrize('dt,count',[(0,1),(-1,1),(True,1),(1,0),(1,True),(1,4097),(601,1),(1e-20,1),(1,4096)])
def test_step_horizon_capacity_and_lost_increment_holds(profiles,dt,count):
    with pytest.raises(model.StockDynamicsHold):run(program(),profiles,dt,count)


def test_trial_and_stock_depletion_keep_last_confirmed_prefix(profiles):
    p=program();p['scenario']['forcing']['canopy_external_heat']['value']=1e7
    with pytest.raises(model.StockDynamicsHold)as caught:run(p,profiles,8,4)
    assert caught.value.step_index==1 and caught.value.failed_stage=='k2'and caught.value.last_confirmed_sample['elapsed_seconds']==0
    p=program();p['leaves'][0]['initial_carbon']['value']=.0001;p['leaves'][0]['carbon_removal']['value']=1
    with pytest.raises(model.StockDynamicsHold)as caught:run(p,profiles,1,4)
    assert caught.value.last_confirmed_sample['state'][113]==.0001


def test_requested_state_and_result_are_detached_and_hash_bound(profiles):
    p=program();r=run(p,profiles,count=2);saved=deepcopy(r)
    def digest(v):return sha256(json.dumps(v,sort_keys=True,separators=(',',':'),ensure_ascii=False,allow_nan=False).encode()).hexdigest()
    assert r['calculation_sha256']==digest({k:v for k,v in r.items()if k!='calculation_sha256'})
    p['leaves'][0]['initial_carbon']['value']=0;assert r==saved
    r['program']['leaves'][1]['initial_carbon']['value']=0;assert p['leaves'][1]['initial_carbon']['value']>0


REFERENCE_STOCK=json.loads((Path(__file__).resolve().parents[2]/'fixtures/crop-leaf-carbon-stock-dynamics-reference-v1.json').read_bytes())


@pytest.mark.parametrize('case',REFERENCE_STOCK['cases'],ids=lambda c:c['case_id'])
def test_app_free_Decimal110_full_RK4_state_transfers_and_curve_reference(case,profiles):
    r=run(case['program'],profiles,case['step_seconds'],case['step_count']);last=r['samples'][-1];expected=case['expected']
    pairs=list(zip(last['state'],expected['state'],strict=True))
    pairs += [(r['integrated_transfers'][k]['value'],v)for k,v in expected['integrated_transfers'].items()]
    pairs += [(last['derived'][k]['value'],expected['derived'][k])for k in('canopy_temperature','leaf_area_index','leaf_carbohydrate')]
    for actual,value in pairs:
        target=float(value)
        if target==0:assert actual==0
        else:assert abs(actual-target)<=max(32*ulp(target),5e-12*abs(target))
    n=len(case['program']['leaves'])
    for i,(actual,target)in enumerate(zip(last['curve_invariant_changes'],expected['curve_invariant_changes'],strict=True)):
        scale=max(abs(r['samples'][0]['state'][107+n+i]),abs(last['state'][107+n+i]))
        assert abs(actual['value']-float(target))<=64*(case['step_count']+1)*ulp(scale)


def test_refinement_or_measured_roundoff_floor_against_independent_fine_32s(profiles):
    case=REFERENCE_STOCK['cases'][0];ref=case['fine_32s_dt0_25'];observed=[]
    for dt in(8,4,2):
        r=run(case['program'],profiles,dt,int(32/dt));y=r['samples'][-1]['state'];d=r['samples'][-1]['derived'];t=r['integrated_transfers']
        observed.append([d['canopy_temperature']['value'],y[105],y[106],y[2],y[3],y[0],fsum(y[4:54]),
            *(t[k]['value']for k in('sensible','latent','vapor')),*y[107:]])
    y=list(map(float,ref['state']));target=[float(ref['derived']['canopy_temperature']),y[105],y[106],y[2],y[3],y[0],fsum(y[4:54]),
        *(float(ref['integrated_transfers'][k])for k in('sensible','latent','vapor')),*y[107:]]
    ratios=0
    for column,value in enumerate(target):
        errors=[abs(row[column]-value)for row in observed]
        for coarse,finer in zip(errors,errors[1:],strict=False):
            if finer<=128*ulp(value):continue
            assert coarse>8*finer,(column,errors);ratios+=1
    assert ratios>=8


def test_512_individual_stocks_and_output_boundary(profiles):
    p=program();C=fsum(x['initial_carbon']['value']for x in p['leaves']);leaf=deepcopy(p['leaves'][0]);p['leaves']=[]
    for i in range(512):p['leaves'].append({**deepcopy(leaf),'leaf_id':f'bounded-{i}',
        'initial_carbon':q(C/512,'mg_CH2O/m2_floor'),'sink_weight':q(1.,'1'),'carbon_removal':q(0.,'mg_CH2O/m2_floor/s')})
    p['model_floor_area']['value']=512*.25/1.33;r=run(p,profiles,count=1)
    assert len(r['samples'][-1]['state'])==1643 and len(r['integrated_transfers'])==1557
    p['leaves'].append({**deepcopy(leaf),'leaf_id':'overflow'})
    with pytest.raises(model.StockDynamicsHold,match='CAPACITY_HOLD'):run(p,profiles,count=1)


def test_failure_after_confirmed_step_preserves_exact_state_and_transfer_prefix(profiles,monkeypatch):
    p=program();baseline=run(p,profiles,count=1);fn=model._evaluate;calls=[]
    def failed(p,y,profiles):
        calls.append(1)
        if len(calls)==7:raise model.StockDynamicsHold('NUMERIC_HOLD: owned k3 failure')
        return fn(p,y,profiles)
    monkeypatch.setattr(model,'_evaluate',failed)
    with pytest.raises(model.StockDynamicsHold)as caught:run(p,profiles,count=4)
    error=caught.value;assert error.step_index==2 and error.failed_stage=='k3'
    assert error.last_confirmed_sample==baseline['samples'][-1]
    assert error.last_confirmed_integrated_transfers==baseline['integrated_transfers']
    assert error.last_confirmed_balance_residuals==baseline['balance_residuals']and error.last_confirmed_balance_budgets==baseline['balance_budgets']


def test_same_indoor_air_clock_zero_and_negative_domain_are_not_canopy_clock(profiles):
    p=program()
    for leaf in p['leaves']:leaf['base_temperature']['value']=18
    r=model.evaluate_rhs(program=p,**profiles);assert all(q['value']==0 for q in r['leaf_age_rates']+r['leaf_area_rates'])
    p['leaves'][0]['base_temperature']['value']=19
    with pytest.raises(model.StockDynamicsHold,match='TEMPERATURE_DOMAIN_HOLD'):model.evaluate_rhs(program=p,**profiles)


def test_reference_fixture_generator_and_input_hashes_are_current():
    root=Path(__file__).resolve().parents[2]
    for name,h in REFERENCE_STOCK['input_sha256'].items():assert sha256((root/name).read_bytes()).hexdigest()==h
    assert sha256((root/'research/crop-leaf-carbon-stock-dynamics-reference.py').read_bytes()).hexdigest()==REFERENCE_STOCK['generator_sha256']


def test_current_companion_area_is_authoritative_with_nonzero_curve_residual(profiles):
    _,p,y,_=model._prepare(program());n=len(p['leaves']);current=list(y);current[107+n]+=1e-8;before=current.copy()
    _,evaluation=model._evaluate(p,tuple(current),profiles)
    derived=evaluation['stock_rhs']['source_stage']['source_joint']['derived']
    assert derived['leaf_area_index']['value']==fsum(current[107+n:107+2*n])/p['model_floor_area']['value']
    assert abs(evaluation['curve_residuals'][0]['value']-1e-8)<1e-15 and current==before
