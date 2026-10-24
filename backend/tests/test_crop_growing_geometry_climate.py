from copy import deepcopy
from hashlib import sha256
import json
from math import fsum,ulp
from pathlib import Path

import pytest

from app import crop_growing_geometry_climate as model
from app.crop_growth_rates import ReferenceParameters as Growth
from app.crop_fruit_cohorts import ReferenceFruitCohortParameters as Cohort
from app.crop_fruit_transport import ReferenceFruitTransportParameters as Transport
from app.crop_canopy_exchange import ReferenceParameters as Exchange

ROOT=Path(__file__).resolve().parents[2]
OLD=json.loads((ROOT/'fixtures/crop-climate-joint-rhs-reference-cases-v1.json').read_bytes())['cases']
REFERENCE=json.loads((ROOT/'fixtures/crop-growing-geometry-climate-reference-v1.json').read_bytes())['cases']


@pytest.fixture(scope='module')
def profiles():
    return {name:kind((ROOT/'fixtures'/file).read_bytes())for name,kind,file in (
        ('growth_profile',Growth,'crop-growth-reference-parameters-v1.json'),
        ('cohort_profile',Cohort,'crop-fruit-cohort-reference-parameters-v1.json'),
        ('transport_profile',Transport,'crop-fruit-transport-reference-parameters-v1.json'),
        ('exchange_profile',Exchange,'crop-canopy-exchange-reference-parameters-v1.json'))}


def q(value,unit):return {'value':value,'unit':unit}


def program(index=0):
    s=deepcopy(OLD[index]['scenario']);s['forcing']['outgoing_capacity_temperature']=q(float(OLD[index]['expected_decimal']['derived']['canopy_temperature']),'degC')
    leaves=[]
    for i,(maximum,steepness,age,base)in enumerate([(0.5,.02,100,5),(.75,.015,120,7),(1.41,.01,140,9)]):
        leaves.append({'leaf_id':f'own-leaf-{i}','thermal_age':q(age,'degC_day'),
            'base_temperature':q(base,'degC'),'initial_area':q(maximum/2,'m2'),
            'curve':{'profile_id':f'own-curve-{i}','origin':'synthetic','values':{
                'maximum_area':q(maximum,'m2'),'steepness':q(steepness,'1/degC_day'),'inflection_age':q(age,'degC_day')}}})
    return {'input_id':s['input_id'],'origin':'synthetic','scenario':s,'leaves':leaves,
        'normalization':'zero_lower_asymptote_sigmoid_v1','thermal_age_policy':'dynamic_indoor_air_no_clip_v1',
        'capacity_policy':'declared_outflow_plus_area_capacity_derivative_v1',
        'model_floor_area':q(1,'m2_floor'),'capacity_outflow':q(.0001,'J/m2_floor/K/s')}


def integrate(p,profiles,dt=2,count=16):return model.integrate(program=p,step_seconds=dt,step_count=count,**profiles)


def test_same_air_clock_area_chain_rule_and_selected_gross_policy(profiles):
    p=program();saved=deepcopy(p);result=model.evaluate_rhs(program=p,**profiles)
    ta=p['scenario']['climate_state']['air_temperature']['value'];expected=[]
    for leaf,age_rate,area_rate in zip(p['leaves'],result['leaf_age_rates'],result['leaf_area_rates'],strict=True):
        curve=leaf['curve']['values'];rate=(ta-leaf['base_temperature']['value'])/86400
        assert age_rate['value']==rate
        expected.append(curve['maximum_area']['value']*curve['steepness']['value']/4*rate)
        assert area_rate['value']==pytest.approx(expected[-1],rel=1e-12,abs=0)
    joint=result['joint'];transport=joint['capacity_transport']
    assert joint['derived']['leaf_area_index_rate']['value']==pytest.approx(fsum(expected),rel=1e-12,abs=0)
    assert transport['capacity_rates']['outgoing']['value']==.0001
    assert abs(transport['balance_residuals']['capacity_rate']['value'])<=transport['balance_budgets']['capacity_rate']['value']
    assert p==saved and model.evaluate_rhs(program=p,**profiles)==result


def test_full_short_interval_advances_leaf_geometry_and_climate_together(profiles,monkeypatch):
    calls=[];original=model.joint.evaluate_rhs
    def traced(**kwargs):calls.append(deepcopy(kwargs['scenario']));return original(**kwargs)
    monkeypatch.setattr(model.joint,'evaluate_rhs',traced)
    p=program();saved=deepcopy(p);r=integrate(p,profiles)
    assert len(calls)==r['numerical']['rhs_evaluations']==65
    assert len(r['samples'])==17 and r['samples'][-1]['elapsed_seconds']==32
    start,end=r['samples'][0]['state'],r['samples'][-1]['state'];n=3
    assert all(b>a for a,b in zip(start[108:108+n],end[108:108+n],strict=True))
    assert all(b>a for a,b in zip(start[108+n:],end[108+n:],strict=True))
    assert end[106]!=start[106]and r['samples'][-1]['derived']['leaf_area_index']['value']>r['samples'][0]['derived']['leaf_area_index']['value']
    for name,row in r['balance_residuals'].items():assert abs(row['value'])<=r['balance_budgets'][name]['value']
    assert r['G0_G4']=='not_assessed'and r['scope']=='software_research_only'and p==saved


@pytest.mark.parametrize('key',['normalization','thermal_age_policy','capacity_policy','capacity_outflow'])
def test_no_implicit_policy_or_outflow(key,profiles):
    p=program();p.pop(key)
    with pytest.raises(model.GrowingGeometryHold):model.evaluate_rhs(program=p,**profiles)


@pytest.mark.parametrize('change',[
    lambda p:p.update(origin='observed'),lambda p:p.update(extra=1),
    lambda p:p.update(thermal_age_policy='canopy_temperature'),
    lambda p:p.update(capacity_policy='default_zero_outflow'),
    lambda p:p['leaves'][0]['initial_area'].update(value=.1),
    lambda p:p['leaves'][0]['base_temperature'].update(value=19),
    lambda p:p['leaves'][0]['thermal_age'].update(value=-1),
    lambda p:p['leaves'][0]['thermal_age'].update(value=True),
    lambda p:p['leaves'][0]['initial_area'].update(unit='cm2'),
    lambda p:p['leaves'][0].update(age_exact={'numerator':'1','denominator':'1','unit':'degC_day'}),
    lambda p:p['leaves'].append(deepcopy(p['leaves'][0])),
    lambda p:p['leaves'].clear(),lambda p:p['model_floor_area'].update(value=0),
    lambda p:p['capacity_outflow'].update(value=-1),
    lambda p:p['capacity_outflow'].update(value=1e100),
    lambda p:p['scenario']['forcing'].pop('incoming_capacity_temperature'),
    lambda p:p['scenario']['forcing'].pop('outgoing_capacity_temperature')])
def test_scope_initial_area_clock_units_and_unrepresentable_gross_holds(change,profiles):
    p=program();change(p)
    with pytest.raises(model.GrowingGeometryHold):model.evaluate_rhs(program=p,**profiles)


def test_base_equal_air_is_exact_zero_not_cooling_clipped(profiles):
    p=program()
    for leaf in p['leaves']:leaf['base_temperature']['value']=18
    r=model.evaluate_rhs(program=p,**profiles)
    assert all(row['value']==0 for row in r['leaf_age_rates']+r['leaf_area_rates'])
    assert r['joint']['capacity_transport']['capacity_rates']['geometry']['value']==0
    assert r['joint']['capacity_transport']['capacity_rates']['incoming']['value']==.0001


@pytest.mark.parametrize('dt,count',[(0,1),(-1,1),(True,1),(1,0),(1,True),(1,4097),(601,1),(1e-20,1),(1,4096)])
def test_time_output_budget_and_lost_increment_holds(dt,count,profiles):
    with pytest.raises(model.GrowingGeometryHold):integrate(program(),profiles,dt,count)


def test_failed_trial_retains_last_confirmed_sample_without_success(profiles):
    p=program();p['scenario']['forcing']['canopy_external_heat']['value']=1e7
    with pytest.raises(model.GrowingGeometryHold)as caught:integrate(p,profiles,8,4)
    error=caught.value
    assert error.step_index==1 and error.failed_stage=='k2'
    assert error.last_confirmed_sample['elapsed_seconds']==0


def test_initial_requested_area_is_recorded_and_only_initially_canonicalized(profiles):
    p=program();p['leaves'][0]['initial_area']['value']*=1+2e-13
    r=integrate(p,profiles,2,2)
    assert r['initial_area_receipts'][0]['requested_area']!=r['initial_area_receipts'][0]['canonical_area']
    assert r['samples'][0]['state'][111]==.25
    assert len(r['samples'][-1]['curve_invariant_changes'])==3


def test_result_hash_and_caller_input_are_detached(profiles):
    p=program();saved=deepcopy(p);r=integrate(p,profiles,2,2);before=deepcopy(r)
    def digest(x):return sha256(json.dumps(x,sort_keys=True,separators=(',',':'),ensure_ascii=False,allow_nan=False).encode()).hexdigest()
    assert r['raw_input_sha256']==digest(saved)
    assert r['calculation_sha256']==digest({k:v for k,v in r.items()if k!='calculation_sha256'})
    p['leaves'][0]['initial_area']['value']=0;assert r==before
    r['program']['leaves'][1]['initial_area']['value']=0
    assert p['leaves'][1]==saved['leaves'][1]and integrate(saved,profiles,2,2)==before


@pytest.mark.parametrize('case',REFERENCE,ids=lambda c:c['case_id'])
def test_independent_full_state_transfers_and_curve_companion(case,profiles):
    r=integrate(case['program'],profiles,case['step_seconds'],case['step_count']);e=case['expected'];last=r['samples'][-1]
    pairs=list(zip(last['state'],e['state'],strict=True))
    pairs.extend((r['integrated_transfers'][name]['value'],v)for name,v in e['integrated_transfers'].items())
    pairs.extend([(last['derived']['canopy_temperature']['value'],e['derived']['canopy_temperature']),
                  (last['derived']['leaf_area_index']['value'],e['derived']['leaf_area_index'])])
    for observed,value in pairs:
        target=float(value)
        if target==0:assert observed==0
        else:assert abs(observed-target)<=max(32*ulp(target),5e-12*abs(target))
    n=len(case['program']['leaves'])
    for i,(observed,value)in enumerate(zip(last['curve_invariant_changes'],e['curve_invariant_changes'],strict=True)):
        scale=max(abs(r['samples'][0]['state'][108+n+i]),abs(last['state'][108+n+i]))
        assert abs(observed['value']-float(value))<=64*(case['step_count']+1)*ulp(scale)


@pytest.mark.parametrize('case',REFERENCE[:3],ids=lambda c:c['case_id'])
def test_timestep_refinement_or_explicit_roundoff_floor(case,profiles):
    reference=case['fine_32s_dt0_25'];runs=[integrate(case['program'],profiles,dt,int(32/dt))for dt in (8,4,2)]
    actual=[]
    for r in runs:
        y=r['samples'][-1]['state'];d=r['samples'][-1]['derived'];t=r['integrated_transfers']
        actual.append([d['canopy_temperature']['value'],y[106],y[107],y[3],y[4],y[0],fsum(y[5:55]),
            t['sensible']['value'],t['latent']['value'],t['vapor']['value'],*y[108:]])
    fine=[float(reference['derived']['canopy_temperature']),float(reference['state'][106]),float(reference['state'][107]),
        float(reference['state'][3]),float(reference['state'][4]),float(reference['state'][0]),
        float(reference['derived']['fruit_carbohydrate_total']),
        *[float(reference['integrated_transfers'][name])for name in ('sensible','latent','vapor')],
        *map(float,reference['state'][108:])]
    ratios=0
    for column,target in enumerate(fine):
        errors=[abs(row[column]-target)for row in actual]
        for coarse,finer in zip(errors,errors[1:],strict=False):
            if finer<=128*ulp(target):continue
            assert coarse>8*finer,(case['case_id'],column,errors)
            ratios+=1
    assert ratios>=8


@pytest.mark.parametrize('count',[1,3,512])
def test_explicit_leaf_inventory_bound_and_order(count,profiles):
    p=program();original=p['leaves'][0];p['leaves']=[]
    for i in range(count):
        leaf=deepcopy(original);leaf['leaf_id']=f'bounded-{i}';p['leaves'].append(leaf)
    p['model_floor_area']['value']=count*.25/1.33
    r=model.evaluate_rhs(program=p,**profiles)
    assert len(r['state'])==108+2*count and len(r['leaf_area_rates'])==count
    assert [leaf['leaf_id']for leaf in r['program']['leaves']]==[f'bounded-{i}'for i in range(count)]


def test_excessive_inventory_is_rejected(profiles):
    p=program();p['leaves']=[{**deepcopy(p['leaves'][0]),'leaf_id':f'excess-{i}'}for i in range(513)]
    with pytest.raises(model.GrowingGeometryHold,match='CAPACITY_HOLD'):model.evaluate_rhs(program=p,**profiles)


def test_sample_capacity_is_checked_before_joint_calculation(profiles,monkeypatch):
    def forbidden(**kwargs):raise AssertionError('oversized samples must not start joint calculation')
    monkeypatch.setattr(model.joint,'evaluate_rhs',forbidden)
    with pytest.raises(model.GrowingGeometryHold,match='CAPACITY_HOLD: sample scalar'):integrate(program(),profiles,.01,4096)


def test_input_byte_budget_is_checked_before_joint_calculation(profiles,monkeypatch):
    def forbidden(**kwargs):raise AssertionError('oversized input must not start joint calculation')
    monkeypatch.setattr(model.joint,'evaluate_rhs',forbidden)
    p=program();p['input_id']='x'*(2*1024**2)
    with pytest.raises(model.GrowingGeometryHold,match='CAPACITY_HOLD: 2MiB'):model.evaluate_rhs(program=p,**profiles)
