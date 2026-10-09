from copy import deepcopy
from dataclasses import FrozenInstanceError
from hashlib import sha256
import json
from math import fsum
from pathlib import Path

import pytest

from app.crop_fruit_cohorts import (
    FruitCohortHold, ReferenceFruitCohortParameters, calculate_cohort_rates, calculate_demand_rates,
)
from app.crop_fruit_transport import ReferenceFruitTransportParameters


ROOT = Path(__file__).resolve().parents[2]
RAW = (ROOT / 'fixtures/crop-fruit-cohort-reference-parameters-v1.json').read_bytes()
TRANSPORT = ReferenceFruitTransportParameters((ROOT / 'fixtures/crop-fruit-transport-reference-parameters-v1.json').read_bytes())
REFERENCE = json.loads((ROOT / 'fixtures/crop-fruit-cohort-reference-cases-v1.json').read_bytes())


def inputs():
    return deepcopy(next(c for c in REFERENCE['cases'] if c['case_id'] == 'synthetic-20C-multiple-varying-RGR'))


def run(case):
    return calculate_cohort_rates(state=case['state'], inflow=case['inflow'],
        profile=ReferenceFruitCohortParameters(RAW), transport_profile=TRANSPORT)


@pytest.mark.parametrize('case', REFERENCE['cases'], ids=lambda c: c['case_id'])
def test_independent_gompertz_transport_allocation_respiration_and_balances(case):
    result = run(case); expected = case['expected']; demand = result['demand']
    separately = calculate_demand_rates(state=case['state'], profile=ReferenceFruitCohortParameters(RAW))
    assert demand == separately
    assert result['model_version'] == 'explicit-entry-fruit-cohort-rates-research-v1'
    assert result['scope'] == demand['scope'] == 'software_research_only'
    assert result['profile_sha256'] == demand['profile_sha256'] == REFERENCE['profile_sha256']
    assert result['transport_profile_sha256'] == TRANSPORT.sha256
    for name, unit in (('development_rate','1/s'), ('fruit_growth_period','day'), ('peak_age','day'), ('steepness','1/day')):
        assert demand[name]['value'] == pytest.approx(float(expected[name]),rel=5e-12,abs=5e-14)
        assert demand[name]['unit'] == unit
    arrays = ((demand['stage_age'],'stage_age','day'),
              (demand['potential_growth'],'potential_growth','mg_CH2O/fruit_equivalent/day'),
              (demand['weighted_demand'],'weighted_demand','mg_CH2O/m2_floor/day'),
              (result['allocation'],'allocation','mg_CH2O/m2_floor/s'),
              (result['maintenance'],'maintenance','mg_CH2O/m2_floor/s'),
              (result['derivatives']['fruit_number'],'dN','fruits_equivalent/m2_floor/s'),
              (result['derivatives']['fruit_carbohydrate'],'dC','mg_CH2O/m2_floor/s'))
    for actual, key, unit in arrays:
        assert len(actual) == 50
        for q,target in zip(actual,expected[key],strict=True):
            assert q['value'] == pytest.approx(float(target),rel=5e-12,abs=5e-14)
            assert q['unit'] == unit
    for name in ('fruit_growth_respiration','fruit_buffer_debit'):
        assert result[name]['value'] == pytest.approx(float(expected[name]),rel=5e-12,abs=5e-14)
        assert result[name]['unit'] == 'mg_CH2O/m2_floor/s'
    terminal = result['terminal_outflow']
    for group,key,unit in (('fruit_number','terminal_number','fruits_equivalent/m2_floor/s'),
                           ('fruit_carbohydrate','terminal_carbohydrate','mg_CH2O/m2_floor/s')):
        assert terminal[group]['value'] == pytest.approx(float(expected[key]),rel=5e-12,abs=5e-14)
        assert terminal[group]['unit'] == unit
    F=case['inflow']['values']['fruit_carbohydrate_inflow']['value']
    S=case['inflow']['values']['fruit_number_inflow']['value']
    carbon_terms=[*(q['value'] for q in result['derivatives']['fruit_carbohydrate']),
                  terminal['fruit_carbohydrate']['value'], *(q['value'] for q in result['maintenance'])]
    residuals={'number':fsum([*(q['value'] for q in result['derivatives']['fruit_number']),terminal['fruit_number']['value'],-S]),
               'carbohydrate':fsum([*carbon_terms,-F]),
               'buffer_carbohydrate':fsum([*carbon_terms,result['fruit_growth_respiration']['value'],-result['fruit_buffer_debit']['value']])}
    for group,residual in residuals.items():
        assert result['balance_residual'][group]['value'] == residual
        assert abs(residual) <= result['balance_budget'][group]['value']
    assert result['fruit_buffer_debit']['value'] == pytest.approx(F*1.27)
    assert not any(k in result for k in ('harvest','fresh_kg','prediction'))


def test_profile_and_inputs_immutable_hashes_bound_and_replay_identical():
    profile=ReferenceFruitCohortParameters(RAW)
    assert profile.sha256 == sha256(RAW).hexdigest()
    with pytest.raises(FrozenInstanceError): profile.stages=1
    with pytest.raises(TypeError): profile.values['GMax']=1
    case=inputs(); before=deepcopy(case); result=run(case)
    assert case == before and result == run(deepcopy(case))
    for block in ('state','inflow'):
        changed=deepcopy(case); changed[block]['input_id']='another-version'
        other=run(changed)
        assert other['input_sha256'] != result['input_sha256']
        assert other['derivatives'] == result['derivatives']
    changed=deepcopy(case); changed['state']['values']['fruit_relative_growth_rate'][1]['value']*=2
    other=run(changed)
    assert other['input_sha256'] != result['input_sha256'] and other['maintenance'] != result['maintenance']


@pytest.mark.parametrize('raw',[None,'bytes',b'{}',RAW+b' ',RAW.replace(b'10000.0',b'10001.0')])
def test_unreviewed_profile_held(raw):
    with pytest.raises(FruitCohortHold,match='PROFILE_HOLD'): ReferenceFruitCohortParameters(raw)


@pytest.mark.parametrize('field',['fruit_number','fruit_carbohydrate','fruit_relative_growth_rate','temperature_filtered_24h','temperature_sum'])
@pytest.mark.parametrize('bad',[float('nan'),float('inf'),-1,True,'1',None])
def test_invalid_state_quantities_held(field,bad):
    case=inputs(); block=case['state']['values'][field]
    q=block[0] if type(block) is list else block; q['value']=bad
    with pytest.raises(FruitCohortHold,match='INPUT_HOLD'): run(case)


@pytest.mark.parametrize('field',['fruit_number','fruit_carbohydrate','fruit_relative_growth_rate'])
@pytest.mark.parametrize('size',[0,49,51])
def test_exact_compartment_arrays_required(field,size):
    case=inputs(); q=case['state']['values'][field][0]
    case['state']['values'][field]=[q]*size
    with pytest.raises(FruitCohortHold,match='INPUT_HOLD'): run(case)


@pytest.mark.parametrize('temperature',[16.99,23.01])
def test_outside_shared_domain_held(temperature):
    case=inputs(); case['state']['values']['temperature_filtered_24h']['value']=temperature
    with pytest.raises(FruitCohortHold,match='FRUIT_COHORT_DOMAIN_HOLD'): run(case)


def test_onset_wrong_unit_mass_without_number_and_closed_input_held():
    case=inputs(); case['state']['values']['temperature_sum']['value']=0
    with pytest.raises(FruitCohortHold,match='FRUIT_COHORT_DOMAIN_HOLD'): run(case)
    case=inputs(); case['state']['values']['fruit_relative_growth_rate'][0]['unit']='day'
    with pytest.raises(FruitCohortHold,match='UNIT_HOLD'): run(case)
    case=inputs(); case['state']['values']['fruit_number'][0]['value']=0
    with pytest.raises(FruitCohortHold,match='FRUIT_COHORT_STATE_HOLD'): run(case)
    case=inputs(); case['inflow']['values']['unknown']={}
    with pytest.raises(FruitCohortHold,match='INPUT_HOLD'): run(case)
    case=inputs(); case['state']['values']['unknown']={}
    with pytest.raises(FruitCohortHold,match='INPUT_HOLD'): run(case)
    case=inputs(); case['state']['origin']='approved'
    with pytest.raises(FruitCohortHold,match='INPUT_HOLD'): run(case)
    case=inputs(); case['state']['input_id']=' '
    with pytest.raises(FruitCohortHold,match='INPUT_HOLD'): run(case)


def test_zero_tail_positive_remaining_entry_budget_and_zero_entry_mass_hold():
    case=inputs()
    for name in ('fruit_number','fruit_carbohydrate'):
        for q in case['state']['values'][name]: q['value']=0
    with pytest.raises(FruitCohortHold,match='EMPTY_FRUIT_SINK_HOLD'): run(case)
    case=inputs(); case['inflow']['values']['fruit_number_inflow']['value']=1
    with pytest.raises(FruitCohortHold,match='FRUIT_ENTRY_BUDGET_HOLD'): run(case)
    case=inputs(); case['inflow']['values']['fruit_entry_carbohydrate']['value']=0
    with pytest.raises(FruitCohortHold,match='FRUIT_ENTRY_STATE_HOLD'): run(case)


def test_unreviewed_transport_or_cohort_profile_held():
    case=inputs(); profile=ReferenceFruitCohortParameters(RAW)
    with pytest.raises(FruitCohortHold,match='PROFILE_HOLD'):
        calculate_cohort_rates(state=case['state'],inflow=case['inflow'],profile=profile,transport_profile={})
    with pytest.raises(FruitCohortHold,match='PROFILE_HOLD'):
        calculate_demand_rates(state=case['state'],profile={})


def test_numeric_overflow_and_positive_maintenance_underflow_held():
    case=inputs(); case['state']['values']['fruit_relative_growth_rate'][1]['value']=1e308
    with pytest.raises(FruitCohortHold,match='NUMERIC_HOLD'): run(case)
    case=inputs()
    for q in case['state']['values']['fruit_number']: q['value']=1e308
    with pytest.raises(FruitCohortHold,match='NUMERIC_HOLD'): run(case)
    case=inputs()
    for q in case['state']['values']['fruit_carbohydrate']: q['value']=1e-315
    for q in case['state']['values']['fruit_number']: q['value']=1
    for q in case['state']['values']['fruit_relative_growth_rate']: q['value']=1e-315
    with pytest.raises(FruitCohortHold,match='NUMERIC_HOLD'): run(case)


@pytest.mark.parametrize('bad',[None,[],{}, {'origin':'synthetic'}])
@pytest.mark.parametrize('block',['state','inflow'])
def test_closed_input_blocks_required(block,bad):
    case=inputs(); case[block]=bad
    with pytest.raises(FruitCohortHold,match='INPUT_HOLD'): run(case)


@pytest.mark.parametrize('block',['state','inflow'])
def test_missing_extra_metadata_and_non_object_values_held(block):
    for field in ('input_id','origin','values'):
        case=inputs(); del case[block][field]
        with pytest.raises(FruitCohortHold,match='INPUT_HOLD'): run(case)
    case=inputs(); case[block]['extra']=0
    with pytest.raises(FruitCohortHold,match='INPUT_HOLD'): run(case)
    case=inputs(); case[block]['values']=[]
    with pytest.raises(FruitCohortHold,match='INPUT_HOLD'): run(case)


def test_growth_respiration_underflow_and_buffer_debit_overflow_held():
    case=deepcopy(next(c for c in REFERENCE['cases'] if c['case_id']=='synthetic-20C-zero-zero-RGR'))
    case['inflow']['values']['fruit_carbohydrate_inflow']['value']=5e-324
    case['inflow']['values']['fruit_number_inflow']['value']=5e-324
    case['inflow']['values']['fruit_entry_carbohydrate']['value']=1
    with pytest.raises(FruitCohortHold,match='NUMERIC_HOLD: invalid growth respiration'): run(case)
    case['inflow']['values']['fruit_carbohydrate_inflow']['value']=1.7e308
    case['inflow']['values']['fruit_number_inflow']['value']=1.7e308
    with pytest.raises(FruitCohortHold,match='NUMERIC_HOLD: aggregate overflow'): run(case)
