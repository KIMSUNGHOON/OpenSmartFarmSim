"""Atomic crop/cohort/capacity events and composition with the shared integrator."""
from copy import deepcopy
from decimal import Decimal,localcontext
from hashlib import sha256
import json
from math import fsum
from pathlib import Path

import pytest

from app import crop_climate_joint_management as model
from app import crop_climate_joint_integration as short
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


def event(leaf=1000,stem=500,fraction=.25):
    return {'input_id':'synthetic-joint-removal','origin':'synthetic','values':{
        'leaf':{'value':leaf,'unit':model.MASS},'stem_root':{'value':stem,'unit':model.MASS},
        'fruit_fraction':[{'value':fraction,'unit':'1'} for _ in range(50)]}}


def run(profiles,s=None,e=None):return model.apply_management(
    scenario=STAGES[0]['scenario'] if s is None else s,event=event() if e is None else e,**profiles)


def test_atomic_shared_removal_preserves_temperature_air_and_clock(profiles):
    s=deepcopy(STAGES[0]['scenario']);e=event();before_s,before_e=deepcopy(s),deepcopy(e)
    r=run(profiles,s,e);after=r['after']['scenario']
    assert s==before_s and e==before_e
    assert after['plant_state']['leaf']['value']==s['plant_state']['leaf']['value']-1000
    assert after['plant_state']['stem_root']['value']==s['plant_state']['stem_root']['value']-500
    for key in ('buffer','temperature_filtered_24h','temperature_sum'):assert after['plant_state'][key]==s['plant_state'][key]
    for key in ('air_temperature','air_vapor_mass'):assert after['climate_state'][key]==s['climate_state'][key]
    assert r['after']['derived']['canopy_temperature']['value']==pytest.approx(r['before']['derived']['canopy_temperature']['value'],abs=2e-13,rel=0)
    assert r['after']['derived']['leaf_area_index']['value']<r['before']['derived']['leaf_area_index']['value']
    for key in ('fruit_carbohydrate','fruit_number'):
        for a,b in zip(s['cohort_state'][key],after['cohort_state'][key],strict=True):
            assert b['value']==float(Decimal(str(a['value']))*Decimal('.75'))
    for key,q in r['balance_residuals'].items():assert abs(q['value'])<=r['balance_budgets'][key]['value']
    assert r['scope']=='software_research_only' and r['G0_G4']=='not_assessed'


@pytest.mark.parametrize('leaf',(50000,50001))
def test_full_or_excess_leaf_holds_without_partial_crop_update(profiles,leaf):
    s=deepcopy(STAGES[0]['scenario']);before=deepcopy(s)
    with pytest.raises(model.JointManagementHold) as held:run(profiles,s,event(leaf=leaf))
    assert s==before and held.value.last_confirmed['scenario']==s


def test_zero_event_is_an_identity(profiles):
    r=run(profiles,e=event(0,0,0))
    assert r['before']==r['after'] and all(q['value']==0 for q in r['removed_totals'].values())


def test_equal_decimal_retained_cohort_numbers_do_not_create_spurious_transport(profiles):
    case=references()['programs'][3];r=run(profiles,case['scenario'],case['event'])
    numbers=r['after']['scenario']['cohort_state']['fruit_number']
    assert numbers[1]['value']==numbers[2]['value']==.15
    rhs=model.joint.evaluate_rhs(scenario=r['after']['scenario'],**profiles)
    assert rhs['derivatives']['cohorts']['fruit_number'][2]['value']==0
    assert r['quantity_rule']=='cohort-decimal-rational-removal-v1'


def test_fraction_lost_to_rounding_holds(profiles):
    with pytest.raises(model.JointManagementHold,match='NUMERIC_HOLD') as held:run(profiles,e=event(fraction=1e-200))
    assert held.value.failed_phase=='event_removal' and held.value.last_confirmed is not None


def references():return json.loads((ROOT/'fixtures/crop-climate-joint-management-reference-cases-v1.json').read_bytes())
def state(s):return list(short._state(s))


@pytest.mark.parametrize('index',range(9))
def test_independent_decimal_event_states_removed_quantities_and_inventories(profiles,index):
    case=references()['cases'][index];r=run(profiles,case['scenario'],case['event']);expected=case['expected_decimal']
    for x,y in zip(state(r['after']['scenario']),expected['state'],strict=True):assert x==pytest.approx(float(y),rel=5e-12,abs=5e-14)
    for k,y in expected['removed'].items():
        found=r['removed'][k]
        pairs=zip(found,y,strict=True) if isinstance(y,list) else [(found,y)]
        for q,wanted in pairs:assert q['value']==pytest.approx(float(wanted),rel=5e-12,abs=5e-14),(case['case_id'],k)
    for k,y in expected['totals'].items():assert r['removed_totals'][k]['value']==pytest.approx(float(y),rel=5e-12,abs=5e-14)
    for k,y in expected['derived'].items():
        assert r['after']['derived'][k]['value']==pytest.approx(float(y),rel=5e-12,abs=5e-14)
        if k=='canopy_temperature':assert abs(r['after']['derived'][k]['value']-float(y))<=2e-13
    for k,q in r['balance_residuals'].items():
        limit={'carbohydrate':1e-7,'number':1e-12,'canopy_sensible':1e-8,'crop_capacity':1e-8,'temperature':2e-13}[k]
        assert abs(q['value'])<=limit and abs(q['value'])<=r['balance_budgets'][k]['value']


def compose(profiles,case,dt=2):
    """Explicit test caller; production continuation/order is a separate task."""
    current=deepcopy(case['scenario']);transfers=dict.fromkeys(short.FLUX_UNITS,0.0)
    totals={};at=case['event_at_seconds'];previous=0
    for boundary in sorted({at,32}):
        if boundary>previous:
            interval=short.integrate(scenario=current,step_seconds=dt,step_count=(boundary-previous)//dt,**profiles)
            sample=interval['samples'][-1]
            current={**current,**{k:sample[k] for k in ('plant_state','cohort_state','climate_state')}}
            for k,q in interval['integrated_transfers'].items():transfers[k]=fsum((transfers[k],q['value']))
        if boundary==at:
            before_event=state(current);r=run(profiles,current,case['event']);current=r['after']['scenario'];after_event=state(current)
            for k,q in r['removed'].items():totals[k]=fsum(v['value'] for v in q) if isinstance(q,list) else q['value']
        previous=boundary
    rhs=model.joint.evaluate_rhs(scenario=current,**profiles)
    return {'state':state(current),'integrated_transfers':transfers,'event_totals':totals,
        'before_event_state':before_event,'after_event_state':after_event,
        'derived':{k:rhs['derived'][k]['value'] for k in ('canopy_temperature','leaf_area_index','canopy_capacity')}}


def global_balances(profiles,case,r):
    a,b=state(case['scenario']),r['state'];t,e=r['integrated_transfers'],r['event_totals']
    p={k:q['value'] for k,q in case['scenario']['parameters'].items()};ep=profiles['exchange_profile'].values
    ca=p['air_volume_per_floor_area']*p['air_capacity_density']*ep['air_heat_capacity']
    carbon=lambda y:fsum((*y[:3],*y[5:55]))
    out={
        'carbohydrate':fsum((carbon(b)-carbon(a),-t['photosynthesis'],*[t[k] for k in tuple(short.FLUX_UNITS)[1:8]],e['leaf'],e['stem_root'],e['fruit_carbohydrate'])),
        'number':fsum((fsum(b[55:105])-fsum(a[55:105]),-t['fruit_number_inflow'],t['terminal_fruit_number'],e['fruit_number'])),
        'canopy_sensible':fsum((b[105]-a[105],-t['canopy_external_heat'],t['canopy_to_air_sensible'],t['canopy_to_vapor_latent'],-t['incoming_capacity_heat'],t['maintenance_capacity_heat'],t['removal_capacity_heat'],e['canopy_sensible_energy'])),
        'air_sensible':fsum((ca*(b[106]-a[106]),-t['air_external_sensible_heat'],-t['canopy_to_air_sensible'])),
        'vapor_and_water_boundaries':fsum((b[107]-a[107],-t['canopy_to_air_vapor'],-t['air_external_vapor'])),
        'crop_capacity':fsum((p['leaf_heat_capacity']*profiles['growth_profile'].values['sla']*(b[1]-a[1]),-t['capacity_allocation'],t['capacity_maintenance'],t['capacity_removal'],e['canopy_capacity']))}
    out['reduced_energy']=fsum((b[105]-a[105],ca*(b[106]-a[106]),ep['latent_heat']*(b[107]-a[107]),
        -t['canopy_external_heat'],-t['air_external_sensible_heat'],-ep['latent_heat']*t['air_external_vapor'],
        -t['incoming_capacity_heat'],t['maintenance_capacity_heat'],t['removal_capacity_heat'],e['canopy_sensible_energy']))
    return out


@pytest.mark.parametrize('index',range(5))
def test_independent_bounded_composition_initial_mid_final_events_and_global_ledgers(profiles,index):
    case=references()['programs'][index];r=compose(profiles,case);expected=case['expected_decimal']
    for k in ('state','before_event_state','after_event_state'):
        for i,(x,y) in enumerate(zip(r[k],expected[k],strict=True)):
            assert x==pytest.approx(float(y),rel=5e-12,abs=2e-10 if i in (3,4,106) else 5e-14),(case['case_id'],k,i)
            if i in (3,4,106):assert abs(x-float(y))<=2e-10
    for k in ('integrated_transfers','event_totals','derived'):
        assert set(r[k])==set(expected[k])
        for key,y in expected[k].items():assert r[k][key]==pytest.approx(float(y),rel=5e-12,abs=5e-14),(case['case_id'],k,key)
    assert abs(r['derived']['canopy_temperature']-float(expected['derived']['canopy_temperature']))<=2e-10
    for k,v in global_balances(profiles,case,r).items():
        limit={'carbohydrate':1e-7,'number':1e-12,'vapor_and_water_boundaries':1e-13,'crop_capacity':1e-8}.get(k,1e-7)
        assert abs(v)<=limit,(case['case_id'],k,v)


def metrics(r):
    d=lambda x:Decimal(str(x));y=r['state'];t=r['integrated_transfers']
    return {'canopy_temperature':d(r['derived']['canopy_temperature']),'air_temperature':d(y[106]),
        'air_vapor_mass':d(y[107]),'temperature_filtered_24h':d(y[3]),'temperature_sum':d(y[4]),
        'buffer':d(y[0]),'fruit_carbohydrate':sum(map(d,y[5:55])),**{k:d(t[k]) for k in (
            'canopy_to_air_sensible','canopy_to_vapor_latent','canopy_to_air_vapor')}}


@pytest.mark.parametrize('index',range(3))
def test_composed_step_halving_with_the_same_event_time(profiles,index):
    case=references()['programs'][index]
    with localcontext() as context:
        context.prec=80;target=metrics(case['fine_32s_dt0_25_decimal']);errors=[]
        for dt in (8,4,2):
            actual=metrics(compose(profiles,case,dt));errors.append({k:abs(actual[k]-v) for k,v in target.items()})
        for key in target:
            for coarse,fine in zip(errors,errors[1:]):
                assert coarse[key]>8*fine[key]>0,(case['case_id'],key,str(coarse[key]),str(fine[key]))


@pytest.mark.parametrize('field',('leaf','stem_root','fruit_fraction'))
@pytest.mark.parametrize('bad',(True,None,'1',float('nan'),float('inf'),10**400,-1))
def test_closed_numeric_fields(profiles,field,bad):
    e=event();row=e['values'][field][0] if field=='fruit_fraction' else e['values'][field];row['value']=bad
    with pytest.raises(model.JointManagementHold):run(profiles,e=e)


@pytest.mark.parametrize('field',('leaf','stem_root','fruit_fraction'))
@pytest.mark.parametrize('failure',('unit','extra','missing'))
def test_closed_quantity_units_and_fields(profiles,field,failure):
    e=event();row=e['values'][field][0] if field=='fruit_fraction' else e['values'][field]
    if failure=='unit':row['unit']='wrong'
    if failure=='extra':row['extra']=1
    if failure=='missing':del e['values'][field]
    with pytest.raises(model.JointManagementHold):run(profiles,e=e)


@pytest.mark.parametrize('mutation',('short','long','tuple','high','value_extra','metadata_extra','id','origin'))
def test_closed_event_shape_and_provenance(profiles,mutation):
    e=event();fractions=e['values']['fruit_fraction']
    if mutation=='short':fractions.pop()
    if mutation=='long':fractions.append(fractions[0])
    if mutation=='tuple':e['values']['fruit_fraction']=tuple(fractions)
    if mutation=='high':fractions[0]['value']=1.1
    if mutation=='value_extra':e['values']['other']={'value':0,'unit':'1'}
    if mutation=='metadata_extra':e['at']=0
    if mutation=='id':e['input_id']=' '
    if mutation=='origin':e['origin']='farm_observation'
    with pytest.raises(model.JointManagementHold):run(profiles,e=e)


def test_actual_post_removal_crop_domain_failure_keeps_pre_event_state(profiles):
    s=deepcopy(STAGES[0]['scenario']);before=deepcopy(s)
    with pytest.raises(model.JointManagementHold) as held:run(profiles,s,event(49999,0,0))
    assert held.value.failed_phase=='candidate' and held.value.last_confirmed['scenario']==s
    assert s==before


@pytest.mark.parametrize('name',('growth_profile','cohort_profile','transport_profile','exchange_profile'))
def test_wrong_profile_holds_before_any_confirmed_event_state(profiles,name):
    with pytest.raises(model.JointManagementHold) as held:run({**profiles,name:None})
    assert held.value.failed_phase=='initial' and held.value.last_confirmed is None


def test_candidate_failure_is_atomic_and_does_not_mutate_event(profiles,monkeypatch):
    original=model.joint.evaluate_rhs;calls=0;s=deepcopy(STAGES[0]['scenario']);e=event();saved_s,saved_e=deepcopy(s),deepcopy(e)
    def fail(**kw):
        nonlocal calls
        calls+=1
        if calls==2:raise model.joint.JointClimateHold('STATE_HOLD: synthetic candidate failure')
        return original(**kw)
    monkeypatch.setattr(model.joint,'evaluate_rhs',fail)
    with pytest.raises(model.JointManagementHold) as held:run(profiles,s,e)
    assert held.value.failed_phase=='candidate' and held.value.last_confirmed['scenario']==saved_s
    assert s==saved_s and e==saved_e


def test_event_energy_is_signed_under_reference_shift_and_zero(profiles):
    rows=[run(profiles,STAGES[i]['scenario']) for i in (0,5,6)]
    for i,r in enumerate(rows[1:]):
        ref=STAGES[(5,6)[i]]['scenario']['parameters']['reference_temperature']['value']
        first=rows[0]
        assert r['removed']['canopy_sensible_energy']['value']==pytest.approx(
            first['removed']['canopy_sensible_energy']['value']-ref*r['removed']['canopy_capacity']['value'],rel=5e-12,abs=1e-9)
        assert r['after']['derived']['canopy_temperature']['value']==pytest.approx(first['after']['derived']['canopy_temperature']['value'],abs=2e-13,rel=0)
    assert rows[1]['removed']['canopy_sensible_energy']['value']<0
    assert rows[2]['removed']['canopy_sensible_energy']['value']==0


def test_identity_source_and_shared_public_kernel_calls(profiles,monkeypatch):
    calls=[];original=model.joint.inventory.calculate_leaf_removal
    def record(**kw):calls.append(deepcopy(kw['event']));return original(**kw)
    monkeypatch.setattr(model.joint.inventory,'calculate_leaf_removal',record)
    a=run(profiles);b=run(profiles,e=event(2000))
    assert len(calls)==2 and calls[0]['values']['leaf_removed']['value']==1000
    assert a['calculation_sha256']!=b['calculation_sha256'] and a['event_sha256']!=b['event_sha256']
    assert a['code_sha256']==sha256((ROOT/'backend/app/crop_climate_joint_management.py').read_bytes()).hexdigest()
    assert a['rhs_code_sha256']==model.joint.CODE_SHA256
    assert a['component_code_sha256']==dict(model.joint.COMPONENT_CODE_SHA256)
    assert a['time_coordinate']=='instantaneous_no_clock'
    assert a['claim_scope']=='synthetic_joint_crop_climate_management_only'
