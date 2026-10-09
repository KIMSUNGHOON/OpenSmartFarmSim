from copy import deepcopy
from hashlib import sha256
import json
from math import fsum
from pathlib import Path

import pytest

from app.crop_growth_rates import ReferenceParameters
from app.crop_fruit_cohorts import ReferenceFruitCohortParameters
from app.crop_fruit_transport import ReferenceFruitTransportParameters
from app.crop_plant_cohort_rates import PlantCohortHold, calculate_plant_cohort_rates


ROOT = Path(__file__).resolve().parents[2]
REFERENCE = json.loads((ROOT/'fixtures/crop-plant-cohort-reference-cases-v1.json').read_bytes())
PROFILES = {
    'growth_profile':ReferenceParameters((ROOT/'fixtures/crop-growth-reference-parameters-v1.json').read_bytes()),
    'cohort_profile':ReferenceFruitCohortParameters((ROOT/'fixtures/crop-fruit-cohort-reference-parameters-v1.json').read_bytes()),
    'transport_profile':ReferenceFruitTransportParameters((ROOT/'fixtures/crop-fruit-transport-reference-parameters-v1.json').read_bytes()),
}
BLOCKS = ('state','cohort_state','forcing','removals','fruit_entry')


def case_input():
    return deepcopy(REFERENCE['cases'][2])


def run(case, **profiles):
    return calculate_plant_cohort_rates(**{k:case[k] for k in BLOCKS},**(profiles or PROFILES))


@pytest.mark.parametrize('case',REFERENCE['cases'],ids=lambda c:c['case_id'])
def test_independent_whole_plant_rates_and_number_carbon_budgets(case):
    result = run(case); expected = case['expected']; cohort = result['cohorts']
    assert result['scope'] == cohort['scope'] == 'software_research_only'
    assert result['model_version'] == 'vanthoor-greenlight-explicit-entry-plant-rates-research-v1'
    for k in ('photosynthesis','growth_respiration','lai','fruit_carbohydrate_total','fruit_maintenance'):
        assert result[k]['value'] == pytest.approx(float(expected[k]),rel=5e-12,abs=5e-14)
    assert result['fruit_carbohydrate_total']['unit'] == 'mg_CH2O/m2_floor'
    assert result['fruit_maintenance']['unit'] == 'mg_CH2O/m2_floor/s'
    for k,value in expected['plant_derivatives'].items():
        assert result['derivatives'][k]['value'] == pytest.approx(float(value),rel=5e-12,abs=5e-14)
    for field,key in (('fruit_carbohydrate','dC'),('fruit_number','dN')):
        for actual,reference in zip(cohort['derivatives'][field],expected[key],strict=True):
            assert actual['value'] == pytest.approx(float(reference),rel=5e-12,abs=5e-14)
    assert result['allocation']['fruit']['value'] == pytest.approx(float(expected['fruit_allocation']))
    assert cohort['fruit_buffer_debit']['value'] == pytest.approx(float(expected['fruit_buffer_debit']))
    assert fsum(q['value'] for q in cohort['maintenance']) == result['fruit_maintenance']['value']
    assert result['fruit_maintenance']['value'] != pytest.approx(float(expected['old_single_fruit_maintenance']))
    assert 'fruit' not in result['derivatives']
    assert not any(k in result for k in ('fresh_kg','harvest','prediction','rank'))
    for key in ('carbohydrate','number'):
        assert abs(result['balance_residual'][key]['value']) <= result['balance_budget'][key]['value']


def test_replay_input_binding_and_profiles_without_mutation():
    case=case_input(); before=deepcopy(case); result=run(case)
    assert case == before and result == run(deepcopy(case))
    for key,p in PROFILES.items():
        assert result['profile_sha256'][key] == p.sha256
    for block in BLOCKS:
        modified=deepcopy(case); modified[block]['input_id']+='-next'
        other=run(modified)
        assert other['input_sha256'] != result['input_sha256']
        assert other['derivatives'] == result['derivatives']
    assert result['research_assumptions'] == ['leaf_stem_fixed_RGR_from_reference_profile_not_measured']


@pytest.mark.parametrize('block',BLOCKS)
@pytest.mark.parametrize('bad',[None,[],{}, {'values':{}}])
def test_closed_blocks_required(block,bad):
    case=case_input(); case[block]=bad
    with pytest.raises(PlantCohortHold,match='INPUT_HOLD'): run(case)


@pytest.mark.parametrize('block',BLOCKS)
def test_bounded_ids_and_known_origin_required(block):
    case=case_input(); case[block]['input_id']='x'*257
    with pytest.raises(PlantCohortHold,match='INPUT_HOLD'): run(case)
    case=case_input(); case[block]['origin']='approved'
    with pytest.raises(PlantCohortHold,match='INPUT_HOLD'): run(case)


@pytest.mark.parametrize('name',['temperature_filtered_24h','temperature_sum'])
def test_conflicting_shared_temperature_held(name):
    case=case_input(); case['state']['values'][name]['value']+=0.1
    with pytest.raises(PlantCohortHold,match='STATE_MISMATCH_HOLD'): run(case)


@pytest.mark.parametrize('block,key',[('state','fruit'),('removals','fruit'),('fruit_entry','fruit_carbohydrate_inflow')])
def test_independent_fruit_total_removal_and_carbon_supply_not_accepted(block,key):
    case=case_input(); case[block]['values'][key]={'value':0,'unit':'mg_CH2O/m2_floor'}
    with pytest.raises(PlantCohortHold,match='INPUT_HOLD'): run(case)


@pytest.mark.parametrize('key',list(PROFILES))
def test_unpinned_profile_held(key):
    profiles=dict(PROFILES); profiles[key]={}
    with pytest.raises(PlantCohortHold,match='PROFILE_HOLD'): run(case_input(),**profiles)


def test_empty_tail_entry_budget_and_positive_carbon_without_number_held():
    case=case_input()
    for k in ('fruit_number','fruit_carbohydrate'):
        for q in case['cohort_state']['values'][k]: q['value']=0
    with pytest.raises(PlantCohortHold,match='EMPTY_FRUIT_SINK_HOLD'): run(case)
    case=case_input(); case['fruit_entry']['values']['fruit_number_inflow']['value']=100
    with pytest.raises(PlantCohortHold,match='FRUIT_ENTRY_BUDGET_HOLD'): run(case)
    case=case_input(); case['cohort_state']['values']['fruit_number'][0]['value']=0
    with pytest.raises(PlantCohortHold,match='FRUIT_COHORT_STATE_HOLD'): run(case)


def test_total_carbon_overflow_and_existing_photosynthesis_domain_held():
    case=case_input()
    for q in case['cohort_state']['values']['fruit_carbohydrate']: q['value']=1e308
    for q in case['cohort_state']['values']['fruit_number']: q['value']=1
    with pytest.raises(PlantCohortHold,match='NUMERIC_HOLD'): run(case)
    case=case_input(); case['state']['values']['leaf']['value']=0
    with pytest.raises(PlantCohortHold,match='COMPENSATION_POINT_HOLD'): run(case)


def test_reference_inputs_and_oracle_are_pinned():
    for path,digest in REFERENCE['input_sha256'].items():
        assert sha256((ROOT/path).read_bytes()).hexdigest()==digest
    assert sha256((ROOT/'research/crop-plant-cohort-reference.py').read_bytes()).hexdigest()==REFERENCE['generator_sha256']
