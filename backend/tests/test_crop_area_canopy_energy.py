from copy import deepcopy
from math import fsum, ulp
from hashlib import sha256
from pathlib import Path
import json

import pytest

from app import crop_area_canopy_energy as model
from app import crop_canopy_energy_transport as legacy
from app.crop_growth_rates import ReferenceParameters

ROOT=Path(__file__).resolve().parents[2]
PROFILE=ReferenceParameters((ROOT/'fixtures/crop-growth-reference-parameters-v1.json').read_bytes())
LEGACY=json.loads((ROOT/'fixtures/crop-canopy-energy-transport-reference-cases-v1.json').read_bytes())['transport_cases']
REFERENCE=json.loads((ROOT/'fixtures/crop-area-canopy-energy-reference-v1.json').read_bytes())['cases']


def inputs(inflow=3,outflow=1,tin=14,tout=22,q=0,reference=0):
    numbers={'leaf_area_index':1.25,'leaf_area_index_rate':(inflow-outflow)/1024,
        'leaf_heat_capacity':1024,'capacity_inflow':inflow,'capacity_outflow':outflow,
        'canopy_temperature':22,'incoming_capacity_temperature':tin,'outgoing_capacity_temperature':tout,
        'reference_temperature':reference,'nonmaterial_heat':q}
    return {'input_id':'explicit-area-energy','origin':'synthetic','values':{
        name:{'value':value,'unit':model.UNITS[name]}for name,value in numbers.items()}}


def run(value):return model.calculate_area_energy(inputs=value)


def adapted_legacy(case):
    v=case['forcing']['values'];s=PROFILE.values['sla'];cap=v['leaf_heat_capacity']['value']
    gin=cap*(s*v['leaf_allocation']['value'])
    gout=fsum(cap*(s*v[name]['value'])for name in ('leaf_maintenance','leaf_removal'))
    value=inputs(gin,gout,v['incoming_capacity_temperature']['value'],v['canopy_temperature']['value'],
                 reference=v['reference_temperature']['value'])
    values=value['values'];values['leaf_area_index']['value']=s*v['leaf_carbohydrate']['value']
    values['leaf_heat_capacity']['value']=cap;values['leaf_area_index_rate']['value']=fsum((gin,-gout))/cap
    values['canopy_temperature']['value']=v['canopy_temperature']['value']
    return value


@pytest.mark.parametrize('case',LEGACY,ids=lambda c:c['case_id'])
def test_legacy_represented_transport_same_conditions_without_mass_inversion(case):
    value=adapted_legacy(case);before=deepcopy(value);result=run(value)
    old=legacy.calculate_transport(forcing=case['forcing'],profile=PROFILE)
    for key in ('canopy_capacity','canopy_sensible_energy','leaf_area_index'):
        assert result[key]['value']==pytest.approx(old[key]['value'],rel=3e-13,abs=2e-13)
    assert result['canopy_temperature_rate']['value']==pytest.approx(old['material_temperature_rate']['value'],rel=3e-13,abs=2e-13)
    assert result['energy_flows']['material']['value']==pytest.approx(old['energy_flows']['net']['value'],rel=3e-13,abs=2e-13)
    assert value==before and run(value)==result


def test_net_zero_gross_turnover_carries_heat_and_stays_explicit():
    value=inputs(3,3);result=run(value)
    assert result['capacity_rates']['geometry']['value']==0 and result['capacity_rates']['transport']['value']==0
    assert result['canopy_temperature_rate']['value']<0 and result['energy_flows']['material']['value']<0
    assert result['G0_G4']=='not_assessed' and result['claim_scope']=='synthetic_area_capacity_bookkeeping_only'


@pytest.mark.parametrize('reference',[-10,0,22,30])
def test_reference_shift_changes_signed_stocks_and_flows_but_not_temperature_rate(reference):
    first=run(inputs());shifted=run(inputs(reference=reference));capacity=first['canopy_capacity']['value']
    rate=first['capacity_rates']['geometry']['value']
    assert shifted['canopy_temperature_rate']==first['canopy_temperature_rate']
    assert shifted['canopy_sensible_energy']['value']==pytest.approx(first['canopy_sensible_energy']['value']-reference*capacity,rel=3e-13,abs=2e-13)
    assert shifted['energy_flows']['total']['value']==pytest.approx(first['energy_flows']['total']['value']-reference*rate,rel=3e-13,abs=2e-13)
    for key,q in shifted['balance_residuals'].items():assert abs(q['value'])<=shifted['balance_budgets'][key]['value']


@pytest.mark.parametrize('change',[
    lambda p:p.update(extra=1),lambda p:p.update(origin='reference_observation'),lambda p:p.update(input_id=''),
    lambda p:p['values'].pop('nonmaterial_heat'),lambda p:p['values'].pop('outgoing_capacity_temperature'),
    lambda p:p['values'].update(leaf_heat_capacity_rate={'value':0,'unit':'J/m2_leaf/K/s'}),
    lambda p:p['values']['leaf_area_index'].update(value=0),
    lambda p:p['values']['leaf_heat_capacity'].update(value=0),
    lambda p:p['values']['capacity_inflow'].update(value=-1),
    lambda p:p['values']['capacity_outflow'].update(value=True),
    lambda p:p['values']['leaf_area_index_rate'].update(value=0),
    lambda p:p['values']['leaf_area_index'].update(value=float('nan')),
    lambda p:p['values']['capacity_outflow'].update(value=float('inf')),
    lambda p:p['values']['leaf_area_index_rate'].update(unit='mg_CH2O/m2_floor/s'),
    lambda p:p['values']['incoming_capacity_temperature'].update(value=9),
    lambda p:p['values']['outgoing_capacity_temperature'].update(value=35),
    lambda p:p['values']['reference_temperature'].update(value=1e30)])
def test_closed_scope_no_missing_flow_fallback_and_numeric_domain_holds(change):
    value=inputs();change(value)
    with pytest.raises(model.AreaCanopyEnergyHold):run(value)


def test_huge_balanced_gross_flows_cannot_hide_inconsistent_net_capacity():
    value=inputs(1e100,1e100);value['values']['leaf_area_index_rate']['value']=.001
    with pytest.raises(model.AreaCanopyEnergyHold,match='CAPACITY_BALANCE_HOLD'):run(value)


def test_explicit_outgoing_temperature_and_nonmaterial_heat_are_used():
    first=run(inputs(tout=22));other=run(inputs(tout=30));heated=run(inputs(q=20))
    assert other['canopy_temperature_rate']['value']<first['canopy_temperature_rate']['value']
    assert heated['canopy_temperature_rate']['value']>first['canopy_temperature_rate']['value']


def test_zero_capacity_flows_still_require_temperatures_and_heat():
    value=inputs(0,0);value['values'].pop('incoming_capacity_temperature')
    with pytest.raises(model.AreaCanopyEnergyHold):run(value)


@pytest.mark.parametrize('case',REFERENCE,ids=lambda c:c['case_id'])
def test_independent_energy_inventory_oracle(case):
    value=deepcopy(case['inputs']);saved=deepcopy(value);result=run(value)
    for path,number in case['expected'].items():
        actual=result
        for name in path.split('.'):actual=actual[name]
        expected=float(number);observed=actual['value']
        if expected==0:assert observed==0
        else:assert abs(observed-expected)<=max(32*ulp(expected),3e-13*abs(expected))
    for name,row in result['balance_residuals'].items():assert abs(row['value'])<=result['balance_budgets'][name]['value']
    assert value==saved and run(value)==result


@pytest.mark.parametrize('changes',[
    {'leaf_area_index':1e308},
    {'leaf_area_index':5e-324,'leaf_heat_capacity':.5},
    {'leaf_heat_capacity':.5,'leaf_area_index_rate':5e-324},
    {'leaf_area_index':1e308,'leaf_heat_capacity':1,'reference_temperature':22,'nonmaterial_heat':5e-324},
    {'capacity_inflow':5e-324,'capacity_outflow':5e-324,'reference_temperature':21.5,
     'incoming_capacity_temperature':22,'outgoing_capacity_temperature':22},
    {'leaf_area_index':5e-324,'leaf_heat_capacity':1,'reference_temperature':21.5}])
def test_arithmetic_overflow_underflow_and_lost_temperature_rate_hold(changes):
    value=inputs(0,0)
    for name,number in changes.items():value['values'][name]['value']=number
    with pytest.raises(model.AreaCanopyEnergyHold,match='NUMERIC_HOLD'):run(value)


def test_result_is_detached_and_binds_raw_input_and_calculation():
    value=inputs();before=deepcopy(value);result=run(value);saved=deepcopy(result)
    def digest(document):return sha256(json.dumps(document,sort_keys=True,separators=(',',':'),ensure_ascii=False,allow_nan=False).encode()).hexdigest()
    assert result['raw_input_sha256']==digest(before)
    assert result['calculation_sha256']==digest({k:v for k,v in result.items()if k!='calculation_sha256'})
    value['values']['leaf_area_index']['value']=2
    assert result==saved
    result['inputs']['values']['leaf_area_index']['value']=3
    assert value['values']['leaf_area_index']['value']==2 and run(before)==saved


@pytest.mark.parametrize('identifier',['x'*201,'한글','has spaces'])
def test_identifiers_are_bounded_ascii(identifier):
    value=inputs();value['input_id']=identifier
    with pytest.raises(model.AreaCanopyEnergyHold):run(value)
