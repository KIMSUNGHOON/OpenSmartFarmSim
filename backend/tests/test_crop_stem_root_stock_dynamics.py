from copy import deepcopy
from decimal import Decimal
from hashlib import sha256
import json
from math import fsum, ulp
from pathlib import Path
from types import MappingProxyType

import pytest

from app import crop_stem_root_stock_dynamics as model
from test_crop_growing_geometry_climate import profiles, q

ROOT = Path(__file__).resolve().parents[2]
REFERENCE = json.loads((ROOT/'fixtures/crop-stem-root-stock-dynamics-reference-v1.json').read_bytes())


def program(case=0): return deepcopy(REFERENCE['cases'][case]['program'])


def run(p, profiles, dt=.125, count=2):
    return model.integrate(program=p, step_seconds=dt, step_count=count, **profiles)


@pytest.mark.parametrize('case', range(6))
@pytest.mark.parametrize('weights', [(1.,2.,3.,4.), (0.,0.,0.,0.), (0.,1.,0.,3.)])
def test_explicit_organ_state_and_integrated_ledgers_without_aggregate_slot(profiles, case, weights):
    p = program(case)
    for row,w in zip(p['stem_root_compartments'],weights,strict=True): row['sink_weight']['value'] = w
    before = deepcopy(p); r = run(p, profiles); first,last = r['samples'][0],r['samples'][-1]
    n,m = len(p['leaves']),len(p['stem_root_compartments']); offset = 106+3*n
    assert len(first['state']) == len(last['state']) == 106+3*n+m
    assert 'leaf' not in r['state_layout']['plant'] and 'stem_root' not in r['state_layout']['plant']
    assert r['state_layout']['leaf_blocks'] == ['thermal_age','area','carbon']
    assert len(r['samples']) == 3 and r['numerical']['rhs_evaluations'] == 9 and last['elapsed_seconds'] == .25
    assert len(r['integrated_transfers']) == 21+3*n+3*m
    assert [x['compartment_id'] for x in r['state_layout']['stem_root_compartments']] == [x['compartment_id'] for x in p['stem_root_compartments']]
    d = Decimal.from_float
    for i in range(m):
        a,b = first['state'][offset+i],last['state'][offset+i]
        g,maint,rem = [r['integrated_transfers'][f'stem_root_{i}_{k}']['value'] for k in ('inflow','maintenance','removal')]
        assert abs(d(b)-d(a)-d(g)+d(maint)+d(rem)) <= d(r['balance_budgets'][f'stem_root_carbon_{i}']['value'])
    assert last['derived']['stem_root_carbohydrate']['value'] == fsum(last['state'][offset:])
    assert last['derived']['leaf_carbohydrate']['value'] == fsum(last['state'][106+2*n:offset])
    for name,value in r['balance_residuals'].items(): assert abs(value['value']) <= r['balance_budgets'][name]['value'],name
    assert 'stem_root_carbon' in r['balance_residuals'] and p == before
    assert r['G0_G4'] == 'not_assessed' and r['claim_scope'] == 'synthetic_stem_root_stock_short_integration_only'


@pytest.mark.parametrize('case', REFERENCE['cases'], ids=lambda c:c['case_id'])
def test_app_free_Decimal110_entire_ODE_RK4_state_transfers_and_diagnostics(profiles, case):
    r = run(case['program'], profiles, case['step_seconds'], case['step_count']); last = r['samples'][-1]; expected = case['expected']
    pairs = list(zip(last['state'], expected['state'], strict=True))
    pairs += [(r['integrated_transfers'][k]['value'],v) for k,v in expected['integrated_transfers'].items()]
    pairs += [(last['derived'][k]['value'],expected['derived'][k]) for k in ('canopy_temperature','leaf_area_index','leaf_carbohydrate','stem_root_carbohydrate')]
    for actual,value in pairs:
        target = float(value)
        if target == 0: assert actual == 0
        else: assert abs(actual-target) <= max(32*ulp(target),5e-12*abs(target))
    n = len(case['program']['leaves'])
    for i,(actual,target) in enumerate(zip(last['curve_invariant_changes'],expected['curve_invariant_changes'],strict=True)):
        scale = max(abs(r['samples'][0]['state'][106+n+i]),abs(last['state'][106+n+i]))
        assert abs(actual['value']-float(target)) <= 64*(case['step_count']+1)*ulp(scale)


@pytest.mark.parametrize('change', [
    lambda p:p.pop('stem_root_stock_policy'), lambda p:p.update(stem_root_stock_policy='default'),
    lambda p:p['scenario']['plant_state'].update(stem_root=q(1,'mg_CH2O/m2_floor')),
    lambda p:p['scenario']['removals'].update(stem_root=q(0,'mg_CH2O/m2_floor/s')),
    lambda p:p.update(stem_root_compartments=[]), lambda p:p.update(stem_root_compartments=tuple(p['stem_root_compartments'])),
    lambda p:p['stem_root_compartments'][0].pop('initial_carbon'), lambda p:p['stem_root_compartments'][0]['initial_carbon'].update(unit='mg_C'),
    lambda p:p['stem_root_compartments'][0]['initial_carbon'].update(value=-1),
    lambda p:p['stem_root_compartments'][0]['carbon_removal'].update(value=-1),
    lambda p:p['stem_root_compartments'][0]['sink_weight'].update(value=True),
    lambda p:p['stem_root_compartments'][0].update(kind='internode'),
    lambda p:p['stem_root_compartments'][1].update(compartment_id=p['stem_root_compartments'][0]['compartment_id']),
    lambda p:p['stem_root_compartments'][0].update(extra=1)])
def test_explicit_closed_inventory_units_and_no_duplicate_aggregate(profiles, change):
    p = program(); change(p)
    with pytest.raises(model.StemRootDynamicsHold): run(p, profiles, count=1)


@pytest.mark.parametrize('dt,count', [(0,1),(-1,1),(True,1),(1,0),(1,True),(1,4097),(601,1),(1e-20,1),(1,4096)])
def test_numerical_horizon_sample_and_increment_limits(profiles, dt, count):
    with pytest.raises(model.StemRootDynamicsHold): run(program(), profiles, dt, count)


def test_same_stage_source_once_and_only_initial_normalization(profiles, monkeypatch):
    calls=[]; prepared=[]; fn=model.stock.evaluate_rhs; prepare=model.old._prepare
    def counted(**kw): calls.append(deepcopy(kw['stem_root_stocks'])); return fn(**kw)
    def once(v): prepared.append(1); return prepare(v)
    def forbidden(*a,**kw): raise AssertionError('old whole RHS/integration forbidden')
    monkeypatch.setattr(model.stock,'evaluate_rhs',counted);monkeypatch.setattr(model.old,'_prepare',once)
    for module in (model.old,model.leaf):
        monkeypatch.setattr(module,'_evaluate',forbidden);monkeypatch.setattr(module,'integrate',forbidden)
    r=run(program(),profiles)
    assert len(calls)==9 and len(prepared)==1
    assert len({tuple(x['carbon']['value'] for x in c['compartments']) for c in calls})>1
    assert calls[-1]['compartments'][0]['carbon']['value']==r['samples'][-1]['state'][115]


def test_individual_depletion_and_failed_trial_preserve_confirmed_prefix(profiles):
    p=program();p['stem_root_compartments'][0]['initial_carbon']['value']=.0001
    p['stem_root_compartments'][0]['carbon_removal']['value']=1.
    with pytest.raises(model.StemRootDynamicsHold)as caught:run(p,profiles,1,4)
    assert caught.value.failed_stage=='k2'and caught.value.last_confirmed_sample['state'][115]==.0001
    p=program();p['scenario']['forcing']['canopy_external_heat']['value']=1e7
    with pytest.raises(model.StemRootDynamicsHold)as caught:run(p,profiles,8,4)
    assert caught.value.step_index==1 and caught.value.failed_stage=='k2'and caught.value.last_confirmed_elapsed_seconds==0.


def test_failure_after_one_confirmed_step_preserves_exact_all_ledgers(profiles,monkeypatch):
    p=program();baseline=run(p,profiles,count=1);fn=model._evaluate;calls=[]
    def failed(p,y,profiles):
        calls.append(1)
        if len(calls)==7:raise model.StemRootDynamicsHold('NUMERIC_HOLD: owned k3 failure')
        return fn(p,y,profiles)
    monkeypatch.setattr(model,'_evaluate',failed)
    with pytest.raises(model.StemRootDynamicsHold)as caught:run(p,profiles,count=4)
    e=caught.value;assert e.step_index==2 and e.failed_stage=='k3'
    assert e.last_confirmed_sample==baseline['samples'][-1] and e.last_confirmed_integrated_transfers==baseline['integrated_transfers']
    assert e.last_confirmed_balance_residuals==baseline['balance_residuals']and e.last_confirmed_balance_budgets==baseline['balance_budgets']


def test_reference_and_hashes_are_current(profiles):
    for name,h in REFERENCE['input_sha256'].items():assert sha256((ROOT/name).read_bytes()).hexdigest()==h
    assert sha256((ROOT/'research/crop-stem-root-stock-dynamics-reference.py').read_bytes()).hexdigest()==REFERENCE['generator_sha256']
    r=run(program(),profiles,count=1)
    raw=json.dumps({k:v for k,v in r.items()if k!='calculation_sha256'},sort_keys=True,separators=(',',':'),ensure_ascii=False,allow_nan=False).encode()
    assert r['calculation_sha256']==sha256(raw).hexdigest()and run(program(),profiles,count=1)==r


def test_refinement_or_measured_roundoff_floor_against_independent_fine_32s(profiles):
    case=REFERENCE['cases'][0];ref=case['fine_32s_dt0_25'];observed=[]
    for dt in (8,4,2):
        r=run(case['program'],profiles,dt,int(32/dt));y=r['samples'][-1]['state'];d=r['samples'][-1]['derived'];t=r['integrated_transfers']
        observed.append([d['canopy_temperature']['value'],y[104],y[105],y[1],y[2],y[0],fsum(y[3:53]),
                         *(t[k]['value']for k in ('sensible','latent','vapor')),*y[106:]])
    y=list(map(float,ref['state']));target=[float(ref['derived']['canopy_temperature']),y[104],y[105],y[1],y[2],y[0],fsum(y[3:53]),
        *(float(ref['integrated_transfers'][k])for k in ('sensible','latent','vapor')),*y[106:]];ratios=0
    for column,value in enumerate(target):
        errors=[abs(row[column]-value)for row in observed]
        for coarse,finer in zip(errors,errors[1:],strict=False):
            if finer<=128*ulp(value):continue
            assert coarse>8*finer,(column,errors);ratios+=1
    assert ratios>=8


def test_initial_area_receipt_and_actual_current_area_are_not_resnapped(profiles):
    p=program();p['leaves'][0]['initial_area']['value']*=1+2e-13;r=run(p,profiles,count=1)
    receipt=r['initial_area_receipts'][0];assert receipt['requested_area']!=receipt['canonical_area']
    assert r['samples'][0]['state'][109]==receipt['canonical_area']['value']
    _,normalized,state,_=model._prepare(p);state=list(state);state[109]+=1e-8
    _,e=model._evaluate(normalized,tuple(state),profiles)
    assert model._view(e)['joint']['derived']['leaf_area_index']['value']==fsum(state[109:112])/normalized['model_floor_area']['value']
    assert e['curve_residuals'][0]['value']>0 and state[115]==p['stem_root_compartments'][0]['initial_carbon']['value']


@pytest.mark.parametrize('kind',['own_code','stock_source_code','legacy_helper_code','profile_values'])
def test_current_code_and_pinned_profile_fences(profiles,monkeypatch,kind):
    p=program();params=profiles
    if kind=='own_code':monkeypatch.setattr(model,'CODE_SHA256','0'*64)
    elif kind=='stock_source_code':monkeypatch.setitem(model.COMPONENT_CODE_SHA256,model.stock.__name__,'0'*64)
    elif kind=='legacy_helper_code':monkeypatch.setitem(model.COMPONENT_CODE_SHA256,model.old.__name__,'0'*64)
    else:
        original=profiles['growth_profile'];wrong=type(original)(original.raw_bytes)
        object.__setattr__(wrong,'values',MappingProxyType({**wrong.values,'cStemM':wrong.values['cStemM']*2}))
        params={**profiles,'growth_profile':wrong}
    with pytest.raises(model.StemRootDynamicsHold):run(p,params,count=1)


@pytest.mark.parametrize('count',[1,256,512,513])
def test_actual_compartment_minimum_output_and_count_boundaries(profiles,count):
    p=program();total=fsum(r['initial_carbon']['value']for r in p['stem_root_compartments']);template=deepcopy(p['stem_root_compartments'][0]);rows=[]
    for i in range(count):
        row=deepcopy(template);row.update(compartment_id=f'c{i}',kind='root_system'if i==0 else'internode')
        row['initial_carbon']['value']=total/count;row['carbon_removal']['value']=0.;row['sink_weight']['value']=1.;rows.append(row)
    p['stem_root_compartments']=rows
    if count>=512:
        with pytest.raises(model.StemRootDynamicsHold,match='CAPACITY_HOLD'):run(p,profiles,count=1)
    else:
        r=run(p,profiles,count=1)
        assert len(r['samples'][-1]['state'])==106+9+count and len(r['integrated_transfers'])==30+3*count


def test_output_capacity_hold_keeps_completed_prefix(profiles,monkeypatch):
    p=program();baseline=run(p,profiles,count=1);limit=len(model._canonical(p))+50
    assert limit<len(model._canonical(baseline));monkeypatch.setattr(model,'MAX_BYTES',limit)
    with pytest.raises(model.StemRootDynamicsHold,match='CAPACITY_HOLD')as caught:run(p,profiles,count=1)
    assert caught.value.failed_stage=='output'and caught.value.last_confirmed_sample==baseline['samples'][-1]
    assert caught.value.last_confirmed_integrated_transfers==baseline['integrated_transfers']


def test_leaf_clock_uses_current_indoor_air_with_zero_and_negative_domain(profiles):
    p=program()
    for row in p['leaves']:row['base_temperature']['value']=18
    r=model.evaluate_rhs(program=p,**profiles);assert all(q['value']==0 for q in r['leaf_age_rates']+r['leaf_area_rates'])
    p['leaves'][0]['base_temperature']['value']=19
    with pytest.raises(model.StemRootDynamicsHold,match='TEMPERATURE_DOMAIN_HOLD'):model.evaluate_rhs(program=p,**profiles)
