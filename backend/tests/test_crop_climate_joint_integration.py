"""Whole coupled trajectories, conservation, feedback, numerical failure boundaries."""
from copy import deepcopy
from decimal import Decimal,localcontext
from hashlib import sha256
import json
from math import fsum
from pathlib import Path

import pytest

from app import crop_climate_joint_integration as model
from app.crop_growth_rates import ReferenceParameters as Growth
from app.crop_fruit_cohorts import ReferenceFruitCohortParameters as Cohort
from app.crop_fruit_transport import ReferenceFruitTransportParameters as Transport
from app.crop_canopy_exchange import ReferenceParameters as Exchange

ROOT=Path(__file__).resolve().parents[2]
STAGES=json.loads((ROOT/'fixtures/crop-climate-joint-rhs-reference-cases-v1.json').read_bytes())['cases']


@pytest.fixture(scope='module')
def profiles():
    return {name:kind((ROOT/'fixtures'/filename).read_bytes()) for name,kind,filename in (
        ('growth_profile',Growth,'crop-growth-reference-parameters-v1.json'),
        ('cohort_profile',Cohort,'crop-fruit-cohort-reference-parameters-v1.json'),
        ('transport_profile',Transport,'crop-fruit-transport-reference-parameters-v1.json'),
        ('exchange_profile',Exchange,'crop-canopy-exchange-reference-parameters-v1.json'))}


def run(profiles,s=None,dt=2,count=16):
    return model.integrate(scenario=STAGES[0]['scenario'] if s is None else s,
        step_seconds=dt,step_count=count,**profiles)


def test_common_stages_recompute_leaf_temperature_and_fluxes_without_mutation(profiles,monkeypatch):
    calls=[];original=model.joint.evaluate_rhs
    def record(**kw):
        result=original(**kw);calls.append(result);return result
    monkeypatch.setattr(model.joint,'evaluate_rhs',record)
    scenario=deepcopy(STAGES[0]['scenario']);before=deepcopy(scenario)
    r=run(profiles,scenario)
    assert len(calls)==65==r['numerical']['rhs_evaluations']
    assert len(r['samples'])==17 and r['samples'][-1]['elapsed_seconds']==32
    assert scenario==before
    assert calls[1]['derived']['canopy_temperature']!=calls[0]['derived']['canopy_temperature']
    assert calls[1]['derived']['leaf_area_index']!=calls[0]['derived']['leaf_area_index']
    for i,sample in enumerate(r['samples']):
        assert sample['derived']==calls[i*4]['derived']
        leaf=sample['plant_state']['leaf']['value'];u=sample['climate_state']['canopy_sensible_energy']['value']
        assert sample['derived']['canopy_temperature']['value']==pytest.approx(
            u/(1200*profiles['growth_profile'].values['sla']*leaf),rel=5e-13)
    for key,q in r['balance_residuals'].items():assert abs(q['value'])<=r['balance_budgets'][key]['value']
    assert len(r['integrated_transfers'])==22
    assert r['canopy_water_boundary']['value']==-r['integrated_transfers']['canopy_to_air_vapor']['value']
    assert r['G0_G4']=='not_assessed' and r['scope']=='software_research_only'


def test_dynamic_temperature_history_uses_changing_canopy(profiles):
    r=run(profiles);a,b=r['samples'][0],r['samples'][-1]
    old=a['plant_state']['temperature_sum']['value']+32*a['derived']['canopy_temperature']['value']/86400
    assert abs(b['plant_state']['temperature_sum']['value']-old)>1e-6


@pytest.mark.parametrize('dt,count',((True,1),('2',1),(None,1),(float('nan'),1),
    (float('inf'),1),(0,1),(-1,1),(10**400,1),(1,True),(1,0),(1,4097),(1,1.0),(601,1),(1,6010)))
def test_explicit_bounded_numerical_inputs(profiles,dt,count):
    with pytest.raises(model.JointIntegrationHold,match='BUDGET_HOLD'):run(profiles,dt=dt,count=count)


def test_initial_domain_failure_has_no_confirmed_sample(profiles):
    s=deepcopy(STAGES[0]['scenario']);s['plant_state']['leaf']['value']=0
    with pytest.raises(model.JointIntegrationHold,match='EMPTY_CANOPY') as held:run(profiles,s)
    assert held.value.step_index==0 and held.value.failed_stage=='initial'
    assert held.value.last_confirmed_sample is None and held.value.last_confirmed_elapsed_seconds is None


def test_trial_domain_failure_preserves_last_confirmed_state(profiles,monkeypatch):
    expected=run(profiles,count=1)['samples'][-1];original=model.joint.evaluate_rhs;calls=0
    def fail(**kw):
        nonlocal calls
        calls+=1
        if calls==7:raise model.joint.JointClimateHold('TEMPERATURE_HOLD: forced trial failure')
        return original(**kw)
    monkeypatch.setattr(model.joint,'evaluate_rhs',fail)
    with pytest.raises(model.JointIntegrationHold,match='TEMPERATURE_HOLD') as held:run(profiles)
    assert held.value.step_index==2 and held.value.failed_stage=='k3'
    assert held.value.last_confirmed_sample==expected
    assert held.value.last_confirmed_elapsed_seconds==2


def references():
    return json.loads((ROOT/'fixtures/crop-climate-joint-integration-reference-cases-v1.json').read_bytes())['cases']


def state(sample):
    return [sample['plant_state'][k]['value'] for k in model.PLANT]+[
        q['value'] for k in model.COHORT for q in sample['cohort_state'][k]]+[
        sample['climate_state'][k]['value'] for k in model.CLIMATE]


@pytest.mark.parametrize('index',range(6))
def test_independent_decimal_all_states_transfers_and_balances(profiles,index):
    case=references()[index];r=run(profiles,case['scenario'],case['step_seconds'],case['step_count'])
    expected=case['expected_decimal'];actual=state(r['samples'][-1])
    assert len(actual)==108
    for i,(x,y) in enumerate(zip(actual,expected['state'],strict=True)):
        assert x==pytest.approx(float(y),rel=5e-12,abs=2e-10 if i in (3,4,106) else 5e-14),(case['case_id'],i)
        if i in (3,4,106):assert abs(x-float(y))<=2e-10
    for key,wanted in expected['derived'].items():
        assert r['samples'][-1]['derived'][key]['value']==pytest.approx(
            float(wanted),rel=5e-12,abs=2e-10 if key=='canopy_temperature' else 5e-14)
        if key=='canopy_temperature':assert abs(r['samples'][-1]['derived'][key]['value']-float(wanted))<=2e-10
    assert set(r['integrated_transfers'])==set(expected['integrated_transfers'])
    for key,wanted in expected['integrated_transfers'].items():
        assert r['integrated_transfers'][key]['value']==pytest.approx(float(wanted),rel=5e-12,abs=5e-14),key
    for key,q in r['balance_residuals'].items():
        limit={'carbohydrate':1e-7,'number':1e-12,'vapor_and_water_boundaries':1e-13,'crop_capacity':1e-8}.get(key,1e-7)
        assert abs(q['value'])<=limit and abs(q['value'])<=r['balance_budgets'][key]['value']


def metrics(y,transfers,tc):
    d=lambda x:Decimal(str(x))
    return {'canopy_temperature':d(tc),'air_temperature':d(y[106]),'air_vapor_mass':d(y[107]),
        'temperature_filtered_24h':d(y[3]),'temperature_sum':d(y[4]),'buffer':d(y[0]),
        'fruit_carbohydrate':sum(map(d,y[5:55])),**{k:d(transfers[k]) for k in (
            'canopy_to_air_sensible','canopy_to_vapor_latent','canopy_to_air_vapor')}}


@pytest.mark.parametrize('index',range(3))
def test_step_halving_against_independent_fine_reference(profiles,index):
    case=references()[index];fine=case['fine_32s_dt0_25_decimal']
    with localcontext() as context:
        context.prec=80
        target=metrics(fine['state'],fine['integrated_transfers'],fine['derived']['canopy_temperature']);errors=[]
        for dt in (8,4,2):
            r=run(profiles,case['scenario'],dt,32//dt)
            actual=metrics(state(r['samples'][-1]),{k:q['value'] for k,q in r['integrated_transfers'].items()},
                r['samples'][-1]['derived']['canopy_temperature']['value'])
            errors.append({k:abs(actual[k]-v) for k,v in target.items()})
        for name in target:
            for coarse,finer in zip(errors,errors[1:]):
                assert coarse[name]>8*finer[name]>0,(case['case_id'],name,str(coarse[name]),str(finer[name]))


@pytest.mark.parametrize('index',(3,4))
def test_reference_shift_preserves_trajectory_and_transforms_material_ledgers(profiles,index):
    cases=references();a=run(profiles,cases[0]['scenario']);b=run(profiles,cases[index]['scenario'])
    delta=cases[index]['scenario']['parameters']['reference_temperature']['value']
    for sa,sb in zip(a['samples'],b['samples'],strict=True):
        for group in ('plant_state','cohort_state'):
            xa,xb=sa[group],sb[group]
            for key in xa:
                pa,pb=(xa[key],xb[key]) if isinstance(xa[key],list) else ([xa[key]],[xb[key]])
                for qa,qb in zip(pa,pb,strict=True):assert qa['value']==pytest.approx(qb['value'],rel=5e-12,abs=2e-10)
        assert sb['climate_state']['canopy_sensible_energy']['value']==pytest.approx(
            sa['climate_state']['canopy_sensible_energy']['value']-delta*sa['derived']['canopy_capacity']['value'],rel=5e-12,abs=1e-9)
        for key in ('canopy_temperature','leaf_area_index'):
            assert sa['derived'][key]['value']==pytest.approx(sb['derived'][key]['value'],rel=5e-12,abs=2e-10)
        for key in ('air_temperature','air_vapor_mass'):
            assert sa['climate_state'][key]['value']==pytest.approx(sb['climate_state'][key]['value'],rel=5e-12,abs=5e-14)
    ta,tb=a['integrated_transfers'],b['integrated_transfers']
    for heat,capacity in (('incoming_capacity_heat','capacity_allocation'),
        ('maintenance_capacity_heat','capacity_maintenance'),('removal_capacity_heat','capacity_removal')):
        assert tb[heat]['value']==pytest.approx(ta[heat]['value']-delta*ta[capacity]['value'],rel=5e-12,abs=1e-9)
    for key in ('canopy_to_air_sensible','canopy_to_vapor_latent','canopy_to_air_vapor'):
        assert ta[key]['value']==pytest.approx(tb[key]['value'],rel=5e-12,abs=5e-14)


@pytest.mark.parametrize('stage,call',(('k2',2),('k3',3),('k4',4),('endpoint',5)))
def test_each_unconfirmed_stage_failure_keeps_original_sample(profiles,monkeypatch,stage,call):
    original=model.joint.evaluate_rhs;calls=0;initial=run(profiles,count=1)['samples'][0]
    def fail(**kw):
        nonlocal calls
        calls+=1
        if calls==call:raise model.joint.JointClimateHold('STATE_HOLD: synthetic stage failure')
        return original(**kw)
    monkeypatch.setattr(model.joint,'evaluate_rhs',fail)
    with pytest.raises(model.JointIntegrationHold) as held:run(profiles)
    assert held.value.failed_stage==stage and held.value.step_index==1
    assert held.value.last_confirmed_sample==initial and held.value.last_confirmed_elapsed_seconds==0


def test_actual_temperature_trial_hold_is_not_a_clamped_success(profiles):
    s=deepcopy(STAGES[0]['scenario']);s['forcing']['canopy_external_heat']['value']=1e7
    with pytest.raises(model.JointIntegrationHold,match='TEMPERATURE_HOLD') as held:run(profiles,s)
    assert held.value.failed_stage=='k2' and held.value.last_confirmed_elapsed_seconds==0


@pytest.mark.parametrize('dt',(5e-324,1e-200))
def test_underflow_or_lost_state_increment_holds(profiles,dt):
    with pytest.raises(model.JointIntegrationHold,match='NUMERIC_HOLD'):run(profiles,dt=dt,count=1)


def test_candidate_balance_failure_does_not_publish_candidate(profiles,monkeypatch):
    original=model._from_result
    def corrupt(r,base):
        rates,flux,result=original(r,base);changed=list(flux);changed[0]+=1
        return rates,tuple(changed),result
    monkeypatch.setattr(model,'_from_result',corrupt)
    with pytest.raises(model.JointIntegrationHold,match='BALANCE_HOLD') as held:run(profiles)
    assert held.value.failed_stage=='endpoint_balance' and held.value.last_confirmed_elapsed_seconds==0


def test_initial_ledger_arithmetic_failure_is_an_explicit_initial_hold(profiles,monkeypatch):
    def overflow(*args):raise OverflowError('synthetic initial stock overflow')
    monkeypatch.setattr(model,'_balances',overflow)
    with pytest.raises(model.JointIntegrationHold,match='NUMERIC_HOLD') as held:run(profiles)
    assert held.value.failed_stage=='initial' and held.value.last_confirmed_sample is None


def test_identity_binds_numerics_source_profiles_and_input(profiles):
    a=run(profiles,dt=2,count=1);b=run(profiles,dt=1,count=2)
    assert a['input_sha256']==b['input_sha256'] and a['calculation_sha256']!=b['calculation_sha256']
    assert a['code_sha256']==sha256((ROOT/'backend/app/crop_climate_joint_integration.py').read_bytes()).hexdigest()
    assert a['rhs_code_sha256']==model.joint.CODE_SHA256
    assert a['component_code_sha256']==dict(model.joint.COMPONENT_CODE_SHA256)
    assert a['numerical']['time_coordinate']=='elapsed_seconds_no_UTC_checkpoint'
    assert a['claim_scope']=='synthetic_joint_crop_climate_short_integration_only'
    s=deepcopy(STAGES[0]['scenario']);s['forcing']['canopy_external_heat']['value']+=1
    changed=run(profiles,s,dt=2,count=1)
    assert changed['input_sha256']!=a['input_sha256'] and changed['calculation_sha256']!=a['calculation_sha256']


@pytest.mark.parametrize('mutation',('event','unit','shape','profile'))
def test_inherited_closed_scenario_and_profile_contract(profiles,mutation):
    s=deepcopy(STAGES[0]['scenario']);p=dict(profiles)
    if mutation=='event':s['events']=[]
    if mutation=='unit':s['climate_state']['air_temperature']['unit']='K'
    if mutation=='shape':s['cohort_state']['fruit_number'].pop()
    if mutation=='profile':p['exchange_profile']=None
    with pytest.raises(model.JointIntegrationHold):run(p,s)


def test_energy_water_number_and_carbon_recomputed_from_raw_stocks_and_ledgers(profiles):
    r=run(profiles);a,b=map(state,(r['samples'][0],r['samples'][-1]));t={k:q['value'] for k,q in r['integrated_transfers'].items()}
    ca=r['samples'][0]['derived']['air_capacity']['value'];latent=profiles['exchange_profile'].values['latent_heat']
    energy=fsum((b[105]-a[105],ca*(b[106]-a[106]),latent*(b[107]-a[107]),
        -t['canopy_external_heat'],-t['air_external_sensible_heat'],-latent*t['air_external_vapor'],
        -t['incoming_capacity_heat'],t['maintenance_capacity_heat'],t['removal_capacity_heat']))
    assert abs(energy)<=1e-7
    carbon=fsum((*b[:3],*b[5:55]))-fsum((*a[:3],*a[5:55]))
    carbon=fsum((carbon,-t['photosynthesis'],*[t[k] for k in tuple(model.FLUX_UNITS)[1:8]]))
    number=fsum((fsum(b[55:105])-fsum(a[55:105]),-t['fruit_number_inflow'],t['terminal_fruit_number']))
    water=fsum((b[107]-a[107],-t['canopy_to_air_vapor'],-t['air_external_vapor']))
    assert abs(carbon)<=1e-7 and abs(number)<=1e-12 and abs(water)<=1e-13
