from copy import deepcopy
from hashlib import sha256
import json
from math import fsum,ulp
from pathlib import Path

import pytest

from app import crop_explicit_lai_climate_rhs as model
from app import crop_climate_joint_rhs as legacy
from app.crop_growth_rates import ReferenceParameters as Growth
from app.crop_fruit_cohorts import ReferenceFruitCohortParameters as Cohort
from app.crop_fruit_transport import ReferenceFruitTransportParameters as Transport
from app.crop_canopy_exchange import ReferenceParameters as Exchange

ROOT=Path(__file__).resolve().parents[2]
OLD=json.loads((ROOT/'fixtures/crop-climate-joint-rhs-reference-cases-v1.json').read_bytes())['cases']
REFERENCE=json.loads((ROOT/'fixtures/crop-explicit-lai-climate-reference-v1.json').read_bytes())['cases']


@pytest.fixture(scope='module')
def profiles():
    return {name:kind((ROOT/'fixtures'/file).read_bytes())for name,kind,file in (
        ('growth_profile',Growth,'crop-growth-reference-parameters-v1.json'),
        ('cohort_profile',Cohort,'crop-fruit-cohort-reference-parameters-v1.json'),
        ('transport_profile',Transport,'crop-fruit-transport-reference-parameters-v1.json'),
        ('exchange_profile',Exchange,'crop-canopy-exchange-reference-parameters-v1.json'))}


def adapted(case):
    scenario=deepcopy(case['scenario']);expected=case['expected_decimal']
    rates=expected['capacity_rates'];gin=float(rates['allocation'])
    gout=fsum(float(rates[key])for key in ('maintenance','removal'))
    def q(v,u):return {'value':v,'unit':u}
    scenario['geometry']={'model_floor_area':q(1,'m2_floor'),
        'leaf_area_index':q(float(expected['derived']['leaf_area_index']),'m2_leaf/m2_floor'),
        'leaf_area_index_rate':q(fsum((gin,-gout))/scenario['parameters']['leaf_heat_capacity']['value'],'m2_leaf/m2_floor/s')}
    scenario['capacity_transport']={name:q(value,'J/m2_floor/K/s')for name,value in (
        ('capacity_inflow',gin),('capacity_outflow',gout))}
    scenario['forcing']['outgoing_capacity_temperature']=q(float(expected['derived']['canopy_temperature']),'degC')
    return scenario


def run(s,p):return model.evaluate_rhs(scenario=s,**p)


@pytest.mark.parametrize('case',OLD,ids=lambda c:c['case_id'])
def test_original_joint_same_explicit_conditions(case,profiles):
    scenario=adapted(case);saved=deepcopy(scenario);new=run(scenario,profiles)
    old=legacy.evaluate_rhs(scenario=case['scenario'],**profiles)
    for group in ('derived',):
        for name,row in old[group].items():assert new[group][name]['value']==pytest.approx(row['value'],rel=5e-12,abs=2e-13)
    for name in ('plant','climate'):
        for key,row in old['derivatives'][name].items():assert new['derivatives'][name][key]['value']==pytest.approx(row['value'],rel=5e-12,abs=5e-14)
    for name in ('fruit_carbohydrate','fruit_number'):
        for actual,expected in zip(new['derivatives']['cohorts'][name],old['derivatives']['cohorts'][name],strict=True):
            assert actual['value']==pytest.approx(expected['value'],rel=5e-12,abs=5e-14)
    for name,row in old['exchange']['exchange'].items():assert new['exchange']['exchange'][name]['value']==pytest.approx(row['value'],rel=5e-12,abs=5e-14)
    assert new['scope']=='software_research_only'and new['G0_G4']=='not_assessed'
    assert new['time_coordinate']=='derivatives_per_second_no_time_advance'
    assert scenario==saved and run(scenario,profiles)==new


def test_each_component_receives_same_temperature_and_area_once(profiles,monkeypatch):
    seen={}
    for module,name,key in ((model.carbon,'calculate_plant_rates','carbon'),
        (model.exchange,'calculate_exchange','exchange'),(model.area,'calculate_area_energy','area')):
        original=getattr(module,name)
        def traced(*,_original=original,_key=key,**kw):
            seen.setdefault(_key,[]).append(deepcopy({k:v for k,v in kw.items()if 'profile'not in k}))
            return _original(**kw)
        monkeypatch.setattr(module,name,traced)
    s=adapted(OLD[0]);result=run(s,profiles)
    assert {key:len(v)for key,v in seen.items()}=={'carbon':1,'exchange':1,'area':1}
    tc=result['derived']['canopy_temperature'];lai=result['derived']['leaf_area_index']
    assert seen['carbon'][0]['forcing']['values']['canopy_temperature']==tc
    for key in ('area','exchange'):
        values=seen[key][0]['inputs'if key=='area'else'forcing']['values']
        assert values['canopy_temperature']==tc and values['leaf_area_index']==lai
    assert seen['area'][0]['inputs']['values']['nonmaterial_heat']['value']==fsum((
        s['forcing']['canopy_external_heat']['value'],-result['exchange']['exchange']['sensible_heat']['value'],
        -result['exchange']['exchange']['latent_heat']['value']))


def test_explicit_area_and_gross_transport_drive_distinct_feedback(profiles):
    s=adapted(OLD[0]);first=run(s,profiles)
    s['geometry']['leaf_area_index']['value']*=2
    s['climate_state']['canopy_sensible_energy']['value']*=2
    s['geometry']['leaf_area_index_rate']['value']=2/s['parameters']['leaf_heat_capacity']['value']
    s['capacity_transport']['capacity_inflow']['value']=3
    s['capacity_transport']['capacity_outflow']['value']=1
    changed=run(s,profiles)
    assert changed['derived']['canopy_temperature']==first['derived']['canopy_temperature']
    assert changed['crop']['photosynthesis']!=first['crop']['photosynthesis']
    assert changed['exchange']['exchange']!=first['exchange']['exchange']
    s['capacity_transport']['capacity_inflow']['value']+=1
    s['capacity_transport']['capacity_outflow']['value']+=1
    turnover=run(s,profiles)
    assert turnover['crop']==changed['crop']and turnover['exchange']==changed['exchange']
    assert turnover['derived']['canopy_temperature_rate']!=changed['derived']['canopy_temperature_rate']


@pytest.mark.parametrize('block',['plant_state','cohort_state','relative_growth_rate','climate_state',
    'parameters','forcing','removals','fruit_entry','geometry','capacity_transport'])
def test_closed_quantity_blocks(block,profiles):
    for mutation in ('extra','missing','unit','bool'):
        s=adapted(OLD[0]);key=next(iter(s[block]))
        if mutation=='extra':s[block]['extra']={'value':1,'unit':'1'}
        elif mutation=='missing':s[block].pop(key)
        else:
            row=s[block][key];row=row[0]if isinstance(row,list)else row
            row['unit'if mutation=='unit'else'value']='wrong'if mutation=='unit'else True
        with pytest.raises(model.ExplicitLaiClimateHold):run(s,profiles)


@pytest.mark.parametrize('block,key,value',[
    ('geometry','model_floor_area',0),('geometry','leaf_area_index',0),
    ('geometry','leaf_area_index_rate',1),('capacity_transport','capacity_inflow',-1),
    ('parameters','leaf_heat_capacity',0),('parameters','air_volume_per_floor_area',0),
    ('parameters','reference_temperature',1e30),('forcing','outgoing_capacity_temperature',35),
    ('climate_state','air_vapor_mass',1),('climate_state','air_vapor_mass',-1),
    ('climate_state','air_temperature',9),('plant_state','leaf',0),
    ('geometry','leaf_area_index',1e308),('forcing','co2',float('nan'))])
def test_domain_capacity_balance_and_arithmetic_holds(block,key,value,profiles):
    s=adapted(OLD[0]);s[block][key]['value']=value
    with pytest.raises(model.ExplicitLaiClimateHold):run(s,profiles)


def test_no_latent_or_material_heat_credit_to_air_and_zero_vapor_depletion(profiles):
    s=adapted(OLD[0]);result=run(s,profiles)
    h=result['exchange']['exchange']['sensible_heat']['value']
    assert result['derived']['air_capacity']['value']*result['derivatives']['climate']['air_temperature']['value']==pytest.approx(
        s['forcing']['air_external_sensible_heat']['value']+h,rel=3e-13)
    s['climate_state']['air_vapor_mass']['value']=0;s['forcing']['air_external_vapor']['value']=-1
    with pytest.raises(model.ExplicitLaiClimateHold,match='DEPLETED_STATE_HOLD'):run(s,profiles)


def test_inputs_outputs_and_full_calculation_hash_are_detached(profiles):
    s=adapted(OLD[0]);saved=deepcopy(s);result=run(s,profiles);original=deepcopy(result)
    def digest(x):return sha256(json.dumps(x,sort_keys=True,separators=(',',':'),ensure_ascii=False,allow_nan=False).encode()).hexdigest()
    assert result['raw_input_sha256']==digest(saved)
    assert result['calculation_sha256']==digest({k:v for k,v in result.items()if k!='calculation_sha256'})
    s['geometry']['model_floor_area']['value']=2;assert result==original
    result['scenario']['plant_state']['buffer']['value']=0
    assert s['plant_state']==saved['plant_state']and run(saved,profiles)==original


@pytest.mark.parametrize('case',REFERENCE,ids=lambda c:c['case_id'])
def test_independent_carbon_exchange_capacity_and_heat_reference(case,profiles):
    s=deepcopy(case['scenario']);saved=deepcopy(s);result=run(s,profiles)
    for path,number in case['expected'].items():
        found=result
        for name in path.split('.'):found=found[int(name)]if isinstance(found,list)else found[name]
        actual=found['value'];target=float(number);scale=float(case['cancellation_scales'].get(path,0))
        if target==scale==0:assert actual==0,path
        else:assert abs(actual-target)<=max(32*ulp(target),5e-12*abs(target),64*ulp(scale)),path
    for name,row in result['balance_residuals'].items():assert abs(row['value'])<=result['balance_budgets'][name]['value'],name
    assert s==saved and run(s,profiles)==result


@pytest.mark.parametrize('profile',['growth_profile','cohort_profile','transport_profile','exchange_profile'])
def test_exact_profile_types(profile,profiles):
    with pytest.raises(model.ExplicitLaiClimateHold,match='PROFILE_HOLD'):run(adapted(OLD[0]),{**profiles,profile:object()})


@pytest.mark.parametrize('change',[
    lambda s:s.update(origin='reference_calculation'),lambda s:s.update(input_id='x'*201),
    lambda s:s.update(input_id='한글'),lambda s:s.update(extra=1),
    lambda s:s['forcing'].pop('incoming_capacity_temperature'),
    lambda s:s['forcing'].pop('outgoing_capacity_temperature'),
    lambda s:s['cohort_state']['fruit_number'].pop(),
    lambda s:s['relative_growth_rate']['fruit_relative_growth_rate'].append({'value':0,'unit':'1/s'}),
    lambda s:s['capacity_transport'].update(capacity_inflow={'value':1e100,'unit':'J/m2_floor/K/s'},
        capacity_outflow={'value':1e100,'unit':'J/m2_floor/K/s'}),
    lambda s:s['climate_state']['canopy_sensible_energy'].update(value=1e308)])
def test_scope_arrays_missing_temperatures_and_large_gross_net_hold(change,profiles):
    s=adapted(OLD[0]);change(s)
    with pytest.raises(model.ExplicitLaiClimateHold):run(s,profiles)


def test_basis_declaration_binds_hash_without_rescaling_per_floor_quantities(profiles):
    s=adapted(OLD[0]);first=run(s,profiles);s['geometry']['model_floor_area']['value']=2;other=run(s,profiles)
    assert other['input_sha256']!=first['input_sha256']and other['calculation_sha256']!=first['calculation_sha256']
    assert other['derived']==first['derived']and other['derivatives']==first['derivatives']
