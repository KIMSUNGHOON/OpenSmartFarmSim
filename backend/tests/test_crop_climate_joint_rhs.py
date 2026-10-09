"""Independent whole-stage values, actual shared inputs, identities and holds."""
from copy import deepcopy
from hashlib import sha256
import json
from math import fsum
from pathlib import Path

import pytest

from app import crop_climate_joint_rhs as model
from app.crop_growth_rates import ReferenceParameters as Growth
from app.crop_fruit_cohorts import ReferenceFruitCohortParameters as Cohort
from app.crop_fruit_transport import ReferenceFruitTransportParameters as Transport
from app.crop_canopy_exchange import ReferenceParameters as Exchange

ROOT=Path(__file__).resolve().parents[2]
CASES=json.loads((ROOT/'fixtures/crop-climate-joint-rhs-reference-cases-v1.json').read_bytes())['cases']


@pytest.fixture(scope='module')
def profiles():
    return {name:kind((ROOT/'fixtures'/filename).read_bytes()) for name,kind,filename in (
        ('growth_profile',Growth,'crop-growth-reference-parameters-v1.json'),
        ('cohort_profile',Cohort,'crop-fruit-cohort-reference-parameters-v1.json'),
        ('transport_profile',Transport,'crop-fruit-transport-reference-parameters-v1.json'),
        ('exchange_profile',Exchange,'crop-canopy-exchange-reference-parameters-v1.json'))}


def run(s,profiles):return model.evaluate_rhs(scenario=s,**profiles)
def numbers(block):return {k:q['value'] for k,q in block.items()}
def comparable(r):
    return {'derived':numbers(r['derived']),'climate_derivatives':numbers(r['derivatives']['climate']),
        'plant_derivatives':numbers(r['derivatives']['plant']),
        'dC':[q['value'] for q in r['derivatives']['cohorts']['fruit_carbohydrate']],
        'dN':[q['value'] for q in r['derivatives']['cohorts']['fruit_number']],
        'exchange':numbers(r['exchange']['exchange']),
        'capacity_rates':numbers(r['capacity_transport']['capacity_rates']),
        'material_energy':numbers(r['capacity_transport']['energy_flows']),
        'crop_diagnostics':{'photosynthesis':r['crop']['photosynthesis']['value'],
            'growth_respiration':r['crop']['growth_respiration']['value'],
            'fruit_allocation':r['crop']['allocation']['fruit']['value'],
            'deferred_fruit_allocation':r['crop']['fruit_startup']['deferred_carbohydrate_inflow']['value']}}


@pytest.mark.parametrize('case',CASES,ids=lambda c:c['case_id'])
def test_independent_decimal_crop_cohorts_exchange_capacity_and_joint_climate(profiles,case):
    before=deepcopy(case['scenario']);r=run(case['scenario'],profiles);actual=comparable(r)
    assert set(actual)==set(case['expected_decimal'])
    for group,expected in case['expected_decimal'].items():
        pairs=zip(actual[group],expected,strict=True) if isinstance(expected,list) else (
            (actual[group][k],v) for k,v in expected.items())
        for found,wanted in pairs:assert found==pytest.approx(float(wanted),rel=5e-12,abs=5e-14),group
    assert r['derived']['canopy_temperature']['value']==pytest.approx(
        float(case['expected_decimal']['derived']['canopy_temperature']),rel=0,abs=2e-13)
    for key,q in r['balance_residuals'].items():assert abs(q['value'])<=r['balance_budgets'][key]['value']
    assert case['scenario']==before
    assert r['scope']=='software_research_only' and r['claim_scope']=='synthetic_joint_crop_climate_rhs_only'
    assert r['G0_G4']=='not_assessed' and r['time_coordinate']=='derivatives_per_second_no_time_advance'
    assert r['state_schema_version']=='crop-climate-stage-state-v1'
    assert r['clock_contract']=='dynamic-canopy-temperature-history-rhs-v1'
    assert r['code_sha256']==sha256((ROOT/'backend/app/crop_climate_joint_rhs.py').read_bytes()).hexdigest()


def test_shared_trial_calls_each_kernel_once_with_current_temperature_lai_and_gross_flows(profiles,monkeypatch):
    observed={}
    for module,name,key in ((model.crop,'calculate_plant_startup_rates','crop'),
        (model.exchange,'calculate_exchange','exchange'),(model.inventory,'calculate_transport','capacity')):
        original=getattr(module,name)
        def record(*, _original=original,_key=key,**kw):
            observed.setdefault(_key,[]).append(deepcopy({k:v for k,v in kw.items() if 'profile' not in k}))
            return _original(**kw)
        monkeypatch.setattr(module,name,record)
    r=run(CASES[0]['scenario'],profiles)
    assert {k:len(v) for k,v in observed.items()}=={'crop':1,'exchange':1,'capacity':1}
    tc=r['derived']['canopy_temperature'];lai=r['derived']['leaf_area_index']
    assert observed['crop'][0]['forcing']['values']['canopy_temperature']==tc
    assert observed['exchange'][0]['forcing']['values']['canopy_temperature']==tc
    assert observed['exchange'][0]['forcing']['values']['leaf_area_index']==lai
    material=observed['capacity'][0]['forcing']['values']
    assert material['canopy_temperature']==tc
    assert material['leaf_allocation']==r['crop']['allocation']['leaf']
    assert material['leaf_maintenance']==r['crop']['vegetative_maintenance']['leaf']
    assert material['leaf_removal']==r['crop']['removals']['leaf']


def test_leaf_and_signed_energy_feed_back_into_exchange_crop_and_dynamic_temperature_history(profiles):
    s=deepcopy(CASES[0]['scenario']);first=run(s,profiles)
    s['plant_state']['leaf']['value']*=1.1;changed=run(s,profiles)
    assert changed['derived']['leaf_area_index']['value']>first['derived']['leaf_area_index']['value']
    assert changed['derived']['canopy_temperature']['value']<first['derived']['canopy_temperature']['value']
    assert changed['exchange']['exchange']!=first['exchange']['exchange']
    assert changed['crop']['photosynthesis']!=first['crop']['photosynthesis']
    assert changed['derivatives']['plant']['temperature_filtered_24h']!=first['derivatives']['plant']['temperature_filtered_24h']
    assert changed['derivatives']['plant']['temperature_sum']!=first['derivatives']['plant']['temperature_sum']
    s['climate_state']['canopy_sensible_energy']['value']*=1.1;hot=run(s,profiles)
    assert hot['derived']['canopy_temperature']['value']>changed['derived']['canopy_temperature']['value']
    assert hot['crop']['photosynthesis']!=changed['crop']['photosynthesis']


def test_reference_shift_preserves_physical_rates_with_negative_and_zero_energy(profiles):
    first=run(CASES[0]['scenario'],profiles)
    for index in (5,6):
        r=run(CASES[index]['scenario'],profiles);delta=CASES[index]['scenario']['parameters']['reference_temperature']['value']
        for key in ('canopy_temperature','leaf_area_index','air_vapor_pressure','canopy_temperature_rate'):
            assert r['derived'][key]['value']==pytest.approx(first['derived'][key]['value'],rel=5e-12,abs=2e-13)
        assert r['crop']==first['crop'] and r['exchange']==first['exchange']
        assert r['derivatives']['climate']['air_temperature']==first['derivatives']['climate']['air_temperature']
        assert r['derivatives']['climate']['air_vapor_mass']==first['derivatives']['climate']['air_vapor_mass']
        assert r['derivatives']['climate']['canopy_sensible_energy']['value']==pytest.approx(
            first['derivatives']['climate']['canopy_sensible_energy']['value']-
            delta*first['capacity_transport']['capacity_rates']['net']['value'],rel=5e-12)
    assert CASES[5]['scenario']['climate_state']['canopy_sensible_energy']['value']<0
    assert CASES[6]['scenario']['climate_state']['canopy_sensible_energy']['value']==0


def test_gross_turnover_does_not_disappear_when_net_leaf_change_is_zero(profiles):
    s=deepcopy(CASES[9]['scenario']);cold=run(s,profiles)
    assert abs(cold['derivatives']['plant']['leaf']['value'])<5e-14
    assert cold['capacity_transport']['capacity_rates']['allocation']['value']>0
    s['forcing']['incoming_capacity_temperature']=deepcopy(cold['derived']['canopy_temperature'])
    same=run(s,profiles)
    assert same['crop']==cold['crop']
    assert same['exchange']==cold['exchange']
    assert same['derivatives']['climate']['canopy_sensible_energy']!=cold['derivatives']['climate']['canopy_sensible_energy']


def test_air_sensible_excludes_latent_and_material_heat_and_canopy_water_is_external(profiles):
    r=run(CASES[0]['scenario'],profiles);s=CASES[0]['scenario'];h=r['exchange']['exchange']['sensible_heat']['value']
    actual=r['derived']['air_capacity']['value']*r['derivatives']['climate']['air_temperature']['value']
    assert actual==pytest.approx(h+s['forcing']['air_external_sensible_heat']['value'],rel=3e-13)
    assert r['canopy_water_boundary']['value']==-r['exchange']['exchange']['water_vapor']['value']
    assert r['derived']['canopy_temperature_rate']['value']!=0
    assert r['derivatives']['plant']['temperature_sum']['value']==pytest.approx(
        r['derived']['canopy_temperature']['value']/profiles['growth_profile'].values['seconds_per_day'],rel=3e-13)


@pytest.mark.parametrize('block',tuple(model.SCALAR_BLOCKS)+tuple(model.ARRAY_BLOCKS))
def test_closed_blocks_units_numbers_and_array_shapes(profiles,block):
    original=CASES[0]['scenario'];arrays=block in model.ARRAY_BLOCKS
    for key in original[block]:
        for bad in (True,None,'1',float('nan'),float('inf'),10**400):
            s=deepcopy(original);row=s[block][key][0] if arrays else s[block][key];row['value']=bad
            with pytest.raises(model.JointClimateHold):run(s,profiles)
        s=deepcopy(original);row=s[block][key][0] if arrays else s[block][key];row['unit']='wrong'
        with pytest.raises(model.JointClimateHold,match='UNIT_HOLD'):run(s,profiles)
        s=deepcopy(original);row=s[block][key][0] if arrays else s[block][key];row['extra']=1
        with pytest.raises(model.JointClimateHold):run(s,profiles)
        s=deepcopy(original);del s[block][key]
        with pytest.raises(model.JointClimateHold):run(s,profiles)
        if arrays:
            for shape in ([],original[block][key][:-1],original[block][key]+[original[block][key][0]],tuple(original[block][key])):
                s=deepcopy(original);s[block][key]=shape
                with pytest.raises(model.JointClimateHold):run(s,profiles)
    s=deepcopy(original);s[block]['extra']={'value':1,'unit':'1'}
    with pytest.raises(model.JointClimateHold):run(s,profiles)


@pytest.mark.parametrize('name',('growth_profile','cohort_profile','transport_profile','exchange_profile'))
def test_wrong_profile_types_hold(profiles,name):
    with pytest.raises(model.JointClimateHold,match='PROFILE_HOLD'):run(CASES[0]['scenario'],{**profiles,name:None})


@pytest.mark.parametrize('block,key,value,reason',(
    ('plant_state','leaf',0,'EMPTY_CANOPY'),('plant_state','leaf',-1,'STATE_HOLD'),
    ('plant_state','temperature_filtered_24h',16,'HOLD'),('plant_state','temperature_sum',0,'HOLD'),
    ('climate_state','canopy_sensible_energy',1e6,'TEMPERATURE_HOLD'),('climate_state','air_temperature',35,'TEMPERATURE_HOLD'),
    ('climate_state','air_vapor_mass',-1,'STATE_HOLD'),('climate_state','air_vapor_mass',1,'BULK_SATURATION'),
    ('forcing','incoming_capacity_temperature',35,'TEMPERATURE_HOLD'),('forcing','co2',-1,'HOLD'),
    ('forcing','par_above_canopy',-1,'HOLD'),('removals','leaf',-1,'HOLD'),
    ('fruit_entry','fruit_number_inflow',-1,'HOLD'),('parameters','leaf_heat_capacity',0,'INPUT_HOLD'),
    ('parameters','vapor_gas_constant',0,'INPUT_HOLD')))
def test_current_domains_and_no_fallback_hold_without_mutation(profiles,block,key,value,reason):
    s=deepcopy(CASES[0]['scenario']);s[block][key]['value']=value;before=deepcopy(s)
    with pytest.raises(model.JointClimateHold,match=reason):run(s,profiles)
    assert s==before


@pytest.mark.parametrize('block,key,value',(('plant_state','leaf',5e-324),
    ('parameters','leaf_heat_capacity',1e308),('parameters','air_volume_per_floor_area',5e-324),
    ('parameters','vapor_gas_constant',5e-324),('parameters','reference_temperature',1e308),
    ('climate_state','canopy_sensible_energy',5e-324)))
def test_unrepresentable_capacity_pressure_energy_or_reference_holds(profiles,block,key,value):
    s=deepcopy(CASES[0]['scenario']);s[block][key]['value']=value
    if key=='leaf_heat_capacity':s['plant_state']['leaf']['value']=1e8
    with pytest.raises(model.JointClimateHold,match='NUMERIC_HOLD'):run(s,profiles)


def test_cohort_and_rgr_domain_holds(profiles):
    s=deepcopy(CASES[0]['scenario']);s['relative_growth_rate']['fruit_relative_growth_rate'][0]['value']=-1
    with pytest.raises(model.JointClimateHold):run(s,profiles)
    s=deepcopy(CASES[0]['scenario']);s['cohort_state']['fruit_number'][0]['value']=0
    s['cohort_state']['fruit_carbohydrate'][0]['value']=1
    with pytest.raises(model.JointClimateHold):run(s,profiles)


def test_closed_metadata_and_no_external_canopy_temperature_lai_or_events(profiles):
    for field in ('canopy_temperature','leaf_area_index','event'):
        s=deepcopy(CASES[0]['scenario']);s[field]={'value':20,'unit':'degC'}
        with pytest.raises(model.JointClimateHold):run(s,profiles)
    for key,value in (('input_id',' '),('input_id','x'*201),('origin','reference_observation'),('origin',True)):
        s=deepcopy(CASES[0]['scenario']);s[key]=value
        with pytest.raises(model.JointClimateHold):run(s,profiles)


def test_canonical_identity_binds_all_profiles_code_input_and_new_state_contract(profiles):
    s=deepcopy(CASES[0]['scenario']);first=run(s,profiles)
    reordered=dict(reversed(list(s.items())))
    for key in (*model.SCALAR_BLOCKS,*model.ARRAY_BLOCKS):reordered[key]=dict(reversed(list(s[key].items())))
    assert run(reordered,profiles)==first
    for key,digest in first['component_code_sha256'].items():
        assert sha256((ROOT/('backend/app/'+key+'.py')).read_bytes()).hexdigest()==digest
    assert len(first['component_code_sha256'])==9
    s['forcing']['incoming_capacity_temperature']['value']+=1
    other=run(s,profiles)
    assert other['input_sha256']!=first['input_sha256'] and other['calculation_sha256']!=first['calculation_sha256']
    assert other['profile_sha256']==first['profile_sha256']
