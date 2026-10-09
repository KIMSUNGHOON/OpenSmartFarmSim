from copy import deepcopy
from hashlib import sha256
import json
from math import fsum, ulp
from pathlib import Path

import pytest

from app.crop_growth_rates import ReferenceParameters
from app.crop_fruit_cohorts import ReferenceFruitCohortParameters
from app.crop_fruit_transport import ReferenceFruitTransportParameters
from app.crop_plant_cohort_rates import calculate_plant_cohort_rates
from app import crop_plant_startup_rates as model

ROOT = Path(__file__).resolve().parents[2]
REFERENCE = json.loads((ROOT/'fixtures/crop-plant-startup-reference-cases-v1.json').read_bytes())
PROFILES = {
    'growth_profile': ReferenceParameters((ROOT/'fixtures/crop-growth-reference-parameters-v1.json').read_bytes()),
    'cohort_profile': ReferenceFruitCohortParameters((ROOT/'fixtures/crop-fruit-cohort-reference-parameters-v1.json').read_bytes()),
    'transport_profile': ReferenceFruitTransportParameters((ROOT/'fixtures/crop-fruit-transport-reference-parameters-v1.json').read_bytes()),
}
BLOCKS = ('state', 'cohort_state', 'forcing', 'removals', 'fruit_entry')


def case_input(pattern='empty-entry'):
    return deepcopy(next(c for c in REFERENCE['cases'] if c['case_id']==f'synthetic-startup-20C-{pattern}'))


def run(case, **profiles):
    return model.calculate_plant_startup_rates(**{k:case[k] for k in BLOCKS}, **(profiles or PROFILES))


def close(actual, reference):
    expected = float(reference)
    assert abs(actual-expected) <= max(24*ulp(expected), 5e-12*abs(expected))


@pytest.mark.parametrize('case', REFERENCE['cases'], ids=lambda c:c['case_id'])
def test_independent_whole_plant_rates_and_conservation(case):
    before = deepcopy(case); result = run(case); expected = case['expected']; cohorts = result['cohorts']
    assert result['scope'] == 'software_research_only'
    assert result['model_version'] == 'explicit-entry-empty-sink-plant-rates-research-v1'
    for field in ('photosynthesis', 'growth_respiration', 'lai', 'fruit_carbohydrate_total', 'fruit_maintenance'):
        close(result[field]['value'], expected[field])
    for field, value in expected['plant_derivatives'].items(): close(result['derivatives'][field]['value'], value)
    for field, key in (('fruit_carbohydrate', 'dC'), ('fruit_number', 'dN')):
        for actual, reference in zip(cohorts['derivatives'][field], expected[key], strict=True):
            close(actual['value'], reference)
    for field in ('allocation', 'maintenance'):
        for actual, reference in zip(cohorts[field], expected[field], strict=True): close(actual['value'], reference)
    close(result['requested_allocation']['fruit']['value'], expected['requested_fruit_allocation'])
    close(result['allocation']['fruit']['value'], expected['fruit_allocation'])
    close(result['fruit_startup']['deferred_carbohydrate_inflow']['value'], expected['deferred_fruit_allocation'])
    close(result['fruit_startup']['buffer_derivative_adjustment']['value'], expected['buffer_adjustment'])
    close(cohorts['fruit_growth_respiration']['value'], expected['fruit_growth_respiration'])
    close(cohorts['fruit_buffer_debit']['value'], expected['fruit_buffer_debit'])
    close(cohorts['terminal_outflow']['fruit_carbohydrate']['value'], expected['terminal_carbohydrate'])
    close(cohorts['terminal_outflow']['fruit_number']['value'], expected['terminal_number'])
    carbon_terms = [*(result['derivatives'][k]['value'] for k in ('buffer', 'leaf', 'stem_root')),
        *(q['value'] for q in cohorts['derivatives']['fruit_carbohydrate']),
        result['growth_respiration']['value'], *(q['value'] for q in result['vegetative_maintenance'].values()),
        result['fruit_maintenance']['value'], *(q['value'] for q in result['removals'].values()),
        cohorts['terminal_outflow']['fruit_carbohydrate']['value'], -result['photosynthesis']['value']]
    assert result['balance_residual']['carbohydrate']['value'] == fsum(carbon_terms)
    for field in ('carbohydrate', 'number'):
        assert abs(result['balance_residual'][field]['value']) <= result['balance_budget'][field]['value']
    assert result['research_assumptions'] == ['leaf_stem_fixed_RGR_from_reference_profile_not_measured']
    assert result['fruit_carbohydrate_total']['unit'] == 'mg_CH2O/m2_floor'
    assert result['allocation']['fruit']['unit'] == result['growth_respiration']['unit'] == 'mg_CH2O/m2_floor/s'
    assert 'fruit' not in result['derivatives']
    assert not any(k in result for k in ('fresh_kg', 'harvest', 'prediction', 'rank', 'seed', 'automatic_set'))
    assert case == before and result == run(deepcopy(case))


@pytest.mark.parametrize('case', REFERENCE['cases'][:6], ids=lambda c:c['case_id'])
def test_positive_tail_preserves_original_v1_numerical_results(case):
    result = run(case)
    old = calculate_plant_cohort_rates(**{k:case[k] for k in BLOCKS}, **PROFILES)
    for key in ('derivatives', 'cohorts', 'allocation', 'growth_respiration', 'fruit_maintenance',
                'vegetative_maintenance', 'removals', 'photosynthesis', 'lai'):
        assert result[key] == old[key]
    assert result['fruit_startup']['deferred_carbohydrate_inflow']['value'] == 0
    assert result['input_sha256'] != old['input_sha256']


def test_empty_no_entry_first_entry_and_balanced_entry_do_not_invent_seed():
    none = run(case_input('empty-no-entry'))
    assert all(q['value']==0 for qs in none['cohorts']['derivatives'].values() for q in qs)
    assert none['allocation']['fruit']['value']==0 and none['fruit_startup']['deferred_carbohydrate_inflow']['value']>0
    case = case_input(); first = run(case)
    assert first['cohorts']['derivatives']['fruit_number'][0]['value']==case['fruit_entry']['values']['fruit_number_inflow']['value']
    assert all(q['value']==0 for q in first['cohorts']['derivatives']['fruit_carbohydrate'][1:])
    case['fruit_entry']['values']['fruit_number_inflow']['value'] = 1
    case['fruit_entry']['values']['fruit_entry_carbohydrate']['value'] = first['requested_allocation']['fruit']['value']
    balanced = run(case)
    assert balanced['fruit_startup']['deferred_carbohydrate_inflow']['value']==0
    old = calculate_plant_cohort_rates(**{k:case[k] for k in BLOCKS}, **PROFILES)
    assert balanced['derivatives']==old['derivatives'] and balanced['cohorts']==old['cohorts']


@pytest.mark.parametrize('defect', ['buffer-only', 'respiration-only'])
def test_partial_correction_cannot_pass_whole_plant_balance(monkeypatch, defect):
    original = model.startup.calculate_startup_rates
    def damaged(**kwargs):
        result = original(**kwargs)
        if defect=='respiration-only': result['buffer_derivative_adjustment']['value'] = 0
        else:
            result['realized_growth_respiration']['value'] = (
                result['requested_carbohydrate_inflow']['value']*PROFILES['cohort_profile'].values['fruit_growth_respiration'])
        return result
    monkeypatch.setattr(model.startup, 'calculate_startup_rates', damaged)
    with pytest.raises(model.PlantStartupHold, match='BALANCE_HOLD'): run(case_input())


def test_normalized_hash_binds_all_provenance_and_pinned_components():
    case = case_input(); result = run(case)
    for key, profile in PROFILES.items(): assert result['profile_sha256'][key]==profile.sha256
    assert result['policy_sha256']==REFERENCE['input_sha256']['research/crop-fruit-startup-source-register.json']
    for block in BLOCKS:
        for key, value in (('input_id', 'another-research-input'), ('origin', 'reference_calculation')):
            modified = deepcopy(case); modified[block][key] = value; other = run(modified)
            assert other['input_sha256'] != result['input_sha256'] and other['derivatives']==result['derivatives']
    modified = deepcopy(case)
    modified['cohort_state']['values']['fruit_number'][0]['value'] = 0.0
    assert run(modified)['input_sha256'] == result['input_sha256']


@pytest.mark.parametrize('block', BLOCKS)
@pytest.mark.parametrize('bad', [None, [], {}, {'values':{}}])
def test_closed_inputs_required(block, bad):
    case = case_input(); case[block] = bad
    with pytest.raises(model.PlantStartupHold, match='INPUT_HOLD'): run(case)


@pytest.mark.parametrize('block', BLOCKS)
def test_provenance_and_units_cannot_be_bypassed(block):
    case = case_input(); case[block]['input_id'] = 'x'*257
    with pytest.raises(model.PlantStartupHold, match='INPUT_HOLD'): run(case)
    case = case_input(); case[block]['origin'] = 'approved'
    with pytest.raises(model.PlantStartupHold, match='INPUT_HOLD'): run(case)
    case = case_input(); q = next(iter(case[block]['values'].values()))
    if type(q) is list: q = q[0]
    q['unit'] = 'kg'
    with pytest.raises(model.PlantStartupHold, match='UNIT_HOLD'): run(case)


@pytest.mark.parametrize('name', ['temperature_filtered_24h', 'temperature_sum'])
def test_conflicting_shared_temperature_held(name):
    case = case_input(); case['state']['values'][name]['value'] += .1
    with pytest.raises(model.PlantStartupHold, match='STATE_MISMATCH_HOLD'): run(case)


@pytest.mark.parametrize('key', list(PROFILES))
def test_unpinned_profile_held(key):
    profiles = dict(PROFILES); profiles[key] = {}
    with pytest.raises(model.PlantStartupHold, match='PROFILE_HOLD'): run(case_input(), **profiles)


@pytest.mark.parametrize('kind, reason', [
    ('pre-onset', 'FRUIT_COHORT_DOMAIN_HOLD'), ('low-temperature', 'FRUIT_COHORT_DOMAIN_HOLD'),
    ('high-temperature', 'FRUIT_COHORT_DOMAIN_HOLD'), ('carbon-without-number', 'FRUIT_COHORT_STATE_HOLD'),
    ('missing-RGR', 'INPUT_HOLD'), ('short-RGR', 'INPUT_HOLD'), ('invalid-RGR', 'INPUT_HOLD'),
    ('missing-entry', 'INPUT_HOLD'), ('zero-entry-mass', 'FRUIT_ENTRY_STATE_HOLD'),
    ('entry-budget', 'FRUIT_ENTRY_BUDGET_HOLD'), ('entry-underflow', 'NUMERIC_HOLD'),
    ('total-overflow', 'NUMERIC_HOLD'), ('maintenance-overflow', 'NUMERIC_HOLD'),
    ('small-demand-underflow', 'NUMERIC_HOLD'), ('leaf-domain', 'COMPENSATION_POINT_HOLD'),
])
def test_existing_and_startup_domains_remain_held(kind, reason):
    case = case_input(); c = case['cohort_state']['values']; e = case['fruit_entry']['values']
    if kind=='pre-onset': c['temperature_sum']['value'] = 0
    if kind=='low-temperature': c['temperature_filtered_24h']['value'] = 16.9
    if kind=='high-temperature': c['temperature_filtered_24h']['value'] = 23.1
    if kind=='carbon-without-number': c['fruit_carbohydrate'][0]['value'] = 1
    if kind=='missing-RGR': del c['fruit_relative_growth_rate']
    if kind=='short-RGR': c['fruit_relative_growth_rate'].pop()
    if kind=='invalid-RGR': c['fruit_relative_growth_rate'][49]['value'] = True
    if kind=='missing-entry': del e['fruit_entry_carbohydrate']
    if kind=='zero-entry-mass': e['fruit_entry_carbohydrate']['value'] = 0
    if kind=='entry-budget': e['fruit_number_inflow']['value'] = 100
    if kind=='entry-underflow':
        for q in e.values(): q['value'] = 1e-300
    if kind=='total-overflow':
        for q in c['fruit_carbohydrate']: q['value'] = 1e308
        for q in c['fruit_number']: q['value'] = 1
    if kind=='maintenance-overflow':
        c['fruit_relative_growth_rate'][49]['value'] = 1e308
    if kind=='small-demand-underflow': c['fruit_number'][49]['value'] = 5e-324
    if kind=='leaf-domain': case['state']['values']['leaf']['value'] = 0
    with pytest.raises(model.PlantStartupHold, match=reason): run(case)


def test_reference_source_and_generator_pins():
    for path, digest in REFERENCE['input_sha256'].items(): assert sha256((ROOT/path).read_bytes()).hexdigest()==digest
    assert sha256((ROOT/'research/crop-plant-startup-reference.py').read_bytes()).hexdigest()==REFERENCE['generator_sha256']
