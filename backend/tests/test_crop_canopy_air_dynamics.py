"""Independent storage/flux oracles, coupled feedback and strict research holds."""
from copy import deepcopy
import json
from math import fsum, nextafter
from pathlib import Path

import pytest

from app import crop_canopy_air_dynamics as model
from app.crop_canopy_exchange import ReferenceParameters

ROOT = Path(__file__).resolve().parents[2]
CASES = json.loads((ROOT/'fixtures/crop-canopy-air-dynamics-reference-cases-v1.json').read_bytes())['cases']


@pytest.fixture(scope='module')
def profile():
    return ReferenceParameters((ROOT/'fixtures/crop-canopy-exchange-reference-parameters-v1.json').read_bytes())


@pytest.fixture
def scenario():
    return deepcopy(CASES[0]['scenario'])


@pytest.mark.parametrize('case', CASES, ids=lambda c:c['case_id'])
def test_independent_rhs_capacities_pressure_signed_exchange_and_stores(profile, case):
    before = deepcopy(case['scenario'])
    result = model.evaluate_rhs(scenario=case['scenario'],profile=profile)
    found = {'air_pressure':result['air_vapor_pressure']['value'],
        **{k+'_capacity':q['value'] for k,q in result['capacities'].items()},
        **{k:q['value'] for k,q in result['exchange'].items()},
        **{k+'_rate':q['value'] for k,q in result['derivatives'].items()}}
    assert set(found) == set(case['rhs_decimal'])
    for key, expected in case['rhs_decimal'].items():
        assert found[key] == pytest.approx(float(expected), rel=3e-13, abs=0)
    assert case['scenario'] == before
    assert result['scope'] == 'software_research_only'
    assert result['claim_scope'] == 'synthetic_canopy_air_dynamics_only'
    assert result['G0_G4'] == 'not_assessed'
    assert abs(result['balance_residuals']['reduced_energy']['value']) <= 1e-10
    assert abs(result['balance_residuals']['vapor_and_water_boundaries']['value']) <= 1e-19
    rates=result['derivatives'];forces=case['scenario']['forcing'];caps=result['capacities']
    scale=fsum((abs(caps['canopy']['value']*rates['canopy_temperature']['value']),
        abs(caps['air']['value']*rates['air_temperature']['value']),
        abs(profile.values['latent_heat']*rates['air_vapor_mass']['value']),
        abs(forces['canopy_external_heat']['value']),abs(forces['air_external_sensible_heat']['value']),
        abs(profile.values['latent_heat']*forces['air_external_vapor']['value'])))
    assert abs(result['balance_residuals']['reduced_energy']['value']) <= 2e-13*scale


def test_no_latent_in_air_sensible_or_second_aggregate_debit(profile, scenario):
    result = model.evaluate_rhs(scenario=scenario,profile=profile)
    e,h,le = (result['exchange'][key]['value'] for key in ('water_vapor','sensible_heat','latent_heat'))
    dc,da,dm = (q['value'] for q in result['derivatives'].values())
    cc,ca = (q['value'] for q in result['capacities'].values())
    assert ca*da == pytest.approx(h,rel=2e-14)
    assert cc*dc == pytest.approx(-h-le,rel=2e-14)
    assert dm == e and result['canopy_water_boundary']['value'] == -e
    assert abs(fsum((cc*dc,ca*da,profile.values['latent_heat']*dm))) < 1e-10
    assert abs(fsum((cc*dc,ca*da+le,profile.values['latent_heat']*dm))) > 1


def test_vapor_mass_pressure_changes_with_air_temperature_and_geometry(profile, scenario):
    first = model.evaluate_rhs(scenario=scenario,profile=profile)
    scenario['state']['air_temperature']['value'] = 28
    hot = model.evaluate_rhs(scenario=scenario,profile=profile)
    assert hot['air_vapor_pressure']['value']/first['air_vapor_pressure']['value'] == pytest.approx(301.15/291.15)
    assert hot['exchange']['water_vapor']['value'] < first['exchange']['water_vapor']['value']
    scenario['parameters']['air_volume_per_floor_area']['value'] *= 2
    taller = model.evaluate_rhs(scenario=scenario,profile=profile)
    assert taller['air_vapor_pressure']['value'] == hot['air_vapor_pressure']['value']/2
    assert taller['capacities']['air']['value'] == hot['capacities']['air']['value']*2
    assert taller['capacities']['canopy'] == hot['capacities']['canopy']


def test_reverse_vapor_exchange_retains_mathematical_scope(profile):
    result = model.evaluate_rhs(scenario=CASES[1]['scenario'],profile=profile)
    assert all(q['value'] < 0 for q in result['exchange'].values())
    assert result['derivatives']['canopy_temperature']['value'] > 0
    assert result['derivatives']['air_temperature']['value'] < 0
    assert result['canopy_water_boundary']['value'] > 0


@pytest.mark.parametrize('block,units', (('state',model.STATE_UNITS),('parameters',model.PARAMETER_UNITS),
    ('forcing',model.FORCING_UNITS)))
def test_closed_quantities_exact_units_numeric_finiteness(profile,scenario,block,units):
    for key,unit in units.items():
        original=deepcopy(scenario[block][key])
        for bad in (True,None,'1',float('nan'),float('inf'),-float('inf'),10**400):
            scenario[block][key]={'value':bad,'unit':unit}
            with pytest.raises(model.CanopyAirHold):model.evaluate_rhs(scenario=scenario,profile=profile)
        scenario[block][key]={'value':1,'unit':'wrong'}
        with pytest.raises(model.CanopyAirHold,match='UNIT_HOLD'):model.evaluate_rhs(scenario=scenario,profile=profile)
        scenario[block][key]={**original,'extra':1}
        with pytest.raises(model.CanopyAirHold):model.evaluate_rhs(scenario=scenario,profile=profile)
        scenario[block][key]=original
    scenario[block]['extra']={'value':1,'unit':'1'}
    with pytest.raises(model.CanopyAirHold):model.evaluate_rhs(scenario=scenario,profile=profile)


@pytest.mark.parametrize('field', model.PARAMETER_UNITS)
def test_parameters_no_missing_zero_or_negative_fallback(profile,scenario,field):
    for value in (0,-1):
        scenario['parameters'][field]['value']=value
        with pytest.raises(model.CanopyAirHold):model.evaluate_rhs(scenario=scenario,profile=profile)
    del scenario['parameters'][field]
    with pytest.raises(model.CanopyAirHold):model.evaluate_rhs(scenario=scenario,profile=profile)


@pytest.mark.parametrize('field', ('canopy_temperature','air_temperature'))
def test_synthetic_temperature_domain_includes_endpoints(profile,scenario,field):
    scenario['state']['air_vapor_mass']['value']=0
    for value in (10,34):
        scenario['state'][field]['value']=value
        model.evaluate_rhs(scenario=scenario,profile=profile)
    for value in (nextafter(10,-float('inf')),nextafter(34,float('inf'))):
        scenario['state'][field]['value']=value
        with pytest.raises(model.CanopyAirHold,match='STATE_HOLD'):model.evaluate_rhs(scenario=scenario,profile=profile)


def test_negative_mass_bulk_saturation_and_empty_canopy_hold(profile,scenario):
    scenario['state']['air_vapor_mass']['value']=-1
    with pytest.raises(model.CanopyAirHold,match='negative vapor'):model.evaluate_rhs(scenario=scenario,profile=profile)
    scenario['state']['air_vapor_mass']['value']=1
    with pytest.raises(model.CanopyAirHold,match='BULK_SATURATION'):model.evaluate_rhs(scenario=scenario,profile=profile)
    scenario['parameters']['leaf_area_index']['value']=0
    with pytest.raises(model.CanopyAirHold,match='EMPTY_CANOPY'):model.evaluate_rhs(scenario=scenario,profile=profile)


@pytest.mark.parametrize('mutation', ('missing','extra','origin','id','profile'))
def test_closed_research_identity(profile,scenario,mutation):
    if mutation=='missing':del scenario['forcing']
    elif mutation=='extra':scenario['C_eff']={'value':1e6,'unit':'J/K'}
    elif mutation=='origin':scenario['origin']='approved_farm'
    elif mutation=='id':scenario['input_id']=' '
    else:profile=None
    with pytest.raises(model.CanopyAirHold):model.evaluate_rhs(scenario=scenario,profile=profile)


@pytest.mark.parametrize('case', CASES, ids=lambda c:c['case_id'])
def test_independent_60_second_trajectory_and_each_storage_ledger(profile,case):
    before=deepcopy(case['scenario'])
    result=model.integrate(scenario=case['scenario'],profile=profile,step_seconds=1,step_count=60)
    expected=case['trajectory_60s_dt1_decimal']
    assert len(result['samples'])==61
    assert result['samples'][0]['state']==before['state']
    assert [row['elapsed_seconds'] for row in result['samples']]==list(range(61))
    for key,value in expected['state'].items():
        assert result['samples'][-1]['state'][key]['value']==pytest.approx(float(value),rel=0,
            abs=2e-14 if key=='air_vapor_mass' else 2e-11)
    for source,target in (('water_vapor','canopy_to_air_vapor'),('sensible_heat','canopy_to_air_sensible'),
        ('latent_heat','canopy_to_vapor_latent')):
        assert result['integrated_transfers'][target]['value']==pytest.approx(
            float(expected['transfers'][source]),rel=3e-13,abs=1e-14)
    for key,q in result['balance_residuals'].items():
        assert abs(q['value']) <= (1e-13 if key=='vapor_and_water_boundaries' else 1e-7)
    assert result['numerical']['rhs_evaluations']==241
    assert result['samples'][-1]['state']['canopy_temperature']!=before['state']['canopy_temperature']
    assert result['samples'][-1]['state']['air_temperature']!=before['state']['air_temperature']
    assert case['scenario']==before
    assert result['G0_G4']=='not_assessed'


@pytest.mark.parametrize('case', (CASES[0],CASES[1],CASES[3]),ids=lambda c:c['case_id'])
def test_step_halving_against_independent_decimal_finer_solution(profile,case):
    reference=case['trajectory_60s_dt0_25_decimal']['state']
    errors={key:[] for key in model.STATE_UNITS}
    transfer_names={'water_vapor':'canopy_to_air_vapor','sensible_heat':'canopy_to_air_sensible',
        'latent_heat':'canopy_to_vapor_latent'}
    errors.update({key:[] for key in transfer_names})
    for dt in (4,2,1):
        result=model.integrate(scenario=case['scenario'],profile=profile,step_seconds=dt,step_count=60//dt)
        for key,value in reference.items():
            errors[key].append(abs(result['samples'][-1]['state'][key]['value']-float(value)))
        for key,target in transfer_names.items():
            expected=float(case['trajectory_60s_dt0_25_decimal']['transfers'][key])
            errors[key].append(abs(result['integrated_transfers'][target]['value']-expected))
    for values in errors.values():
        assert values[0]>8*values[1] and values[1]>8*values[2]


def test_common_stage_exchange_is_recomputed_from_evolving_joint_state(profile,scenario,monkeypatch):
    original=model.calculate_exchange
    stages=[]
    def observed(**kw):
        stages.append(deepcopy(kw['forcing']['values']))
        return original(**kw)
    monkeypatch.setattr(model,'calculate_exchange',observed)
    result=model.integrate(scenario=scenario,profile=profile,step_seconds=1,step_count=4)
    assert len(stages)==result['numerical']['rhs_evaluations']==17
    assert stages[-1]['canopy_temperature']['value']==result['samples'][-1]['state']['canopy_temperature']['value']
    assert stages[-1]['air_temperature']['value']==result['samples'][-1]['state']['air_temperature']['value']
    assert stages[-1]['air_vapor_pressure']!=stages[0]['air_vapor_pressure']
    assert stages[-1]['canopy_temperature']!=stages[0]['canopy_temperature']
    final=deepcopy(scenario);final['state']=result['samples'][-1]['state']
    assert model.evaluate_rhs(scenario=final,profile=profile)['exchange']!=model.evaluate_rhs(scenario=scenario,profile=profile)['exchange']


def test_exact_stationary_state_with_explicit_balanced_boundaries(profile,scenario):
    scenario['state']['air_temperature']['value']=scenario['state']['canopy_temperature']['value']
    rhs=model.evaluate_rhs(scenario=scenario,profile=profile)
    scenario['forcing']['canopy_external_heat']['value']=rhs['exchange']['latent_heat']['value']
    scenario['forcing']['air_external_vapor']['value']=-rhs['exchange']['water_vapor']['value']
    assert all(q['value']==0 for q in model.evaluate_rhs(scenario=scenario,profile=profile)['derivatives'].values())
    result=model.integrate(scenario=scenario,profile=profile,step_seconds=1,step_count=60)
    assert all(row['state']==scenario['state'] for row in result['samples'])
    assert abs(result['balance_residuals']['reduced_energy']['value'])<1e-7


@pytest.mark.parametrize('field,value,reason', (('canopy_external_heat',-1e8,'temperature'),
    ('air_external_sensible_heat',1e8,'temperature'),('air_external_vapor',1,'BULK_SATURATION'),
    ('air_external_vapor',-1,'negative vapor')))
def test_trial_failure_preserves_last_confirmed_state_without_returning_partial_success(profile,scenario,field,value,reason):
    scenario['forcing'][field]['value']=value
    before=deepcopy(scenario)
    with pytest.raises(model.CanopyAirHold,match=reason) as held:
        model.integrate(scenario=scenario,profile=profile,step_seconds=1,step_count=10)
    assert held.value.step_index==1 and held.value.failed_stage=='k2'
    assert held.value.last_confirmed_elapsed_seconds==0
    assert held.value.last_confirmed_state==scenario['state']
    assert scenario==before


@pytest.mark.parametrize('dt,count', ((0,1),(-1,1),(True,1),('1',1),(float('nan'),1),
    (float('inf'),1),(601,1),(1,0),(1,4097),(1,True),(1,1.0),(1e308,4096)))
def test_explicit_numerical_budget_no_fallback(profile,scenario,dt,count):
    with pytest.raises(model.CanopyAirHold):
        model.integrate(scenario=scenario,profile=profile,step_seconds=dt,step_count=count)


def test_numerical_stagnation_holds_instead_of_publishing_identical_states(profile,scenario):
    with pytest.raises(model.CanopyAirHold,match='rounding'):
        model.integrate(scenario=scenario,profile=profile,step_seconds=1e-20,step_count=1)


@pytest.mark.parametrize('changes', ({'leaf_heat_capacity':1e308}, {'air_volume_per_floor_area':1e308},
    {'leaf_heat_capacity':5e-324,'leaf_area_index':5e-324},
    {'air_volume_per_floor_area':5e-324}, {'vapor_gas_constant':5e-324}))
def test_capacity_pressure_and_derivative_extremes_fail_closed(profile,scenario,changes):
    for key,value in changes.items():scenario['parameters'][key]['value']=value
    with pytest.raises(model.CanopyAirHold):model.evaluate_rhs(scenario=scenario,profile=profile)


def test_canonical_replay_and_new_numerics_have_distinct_identity(profile,scenario):
    original=model.integrate(scenario=scenario,profile=profile,step_seconds=1,step_count=2)
    reordered=dict(reversed(list(scenario.items())))
    for key in ('parameters','forcing','state'):reordered[key]=dict(reversed(list(reordered[key].items())))
    assert model.integrate(scenario=reordered,profile=profile,step_seconds=1,step_count=2)==original
    other=model.integrate(scenario=scenario,profile=profile,step_seconds=.5,step_count=4)
    assert other['input_sha256']==original['input_sha256']
    assert other['calculation_sha256']!=original['calculation_sha256']
