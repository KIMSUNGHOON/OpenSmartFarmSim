from copy import deepcopy
from hashlib import sha256
from math import fsum, ulp
import json
from pathlib import Path

import pytest

from app import crop_explicit_lai_carbon_cohorts as model
from app import crop_plant_startup_rates as legacy
from test_crop_plant_startup_rates import PROFILES, BLOCKS, REFERENCE

ROOT=Path(__file__).resolve().parents[2]
EXPLICIT=json.loads((ROOT/'fixtures/crop-explicit-lai-carbon-reference-v1.json').read_bytes())


def geometry(case, value=None):
    return {'input_id': 'explicit-carbon-geometry', 'origin': 'synthetic', 'values': {
        'leaf_area_index': {'value': PROFILES['growth_profile'].values['sla']*case['state']['values']['leaf']['value'] if value is None else value,
                            'unit': 'm2_leaf/m2_floor'}}}


def run(case, area=None):
    return model.calculate_plant_rates(**{key: case[key] for key in BLOCKS},
                                       geometry=geometry(case) if area is None else area, **PROFILES)


def close(actual, expected):
    value = float(expected)
    assert abs(actual-value) <= max(24*ulp(value), 5e-12*abs(value))


def assert_expected(result, expected):
    for name in ('photosynthesis','growth_respiration','fruit_carbohydrate_total','fruit_maintenance','lai'):
        close(result[name]['value'], expected[name])
    for name, value in expected['plant_derivatives'].items(): close(result['derivatives'][name]['value'], value)
    for name, key in [('fruit_carbohydrate','dC'),('fruit_number','dN')]:
        for actual,value in zip(result['cohorts']['derivatives'][name],expected[key],strict=True):close(actual['value'],value)
    for name in ('allocation','maintenance'):
        for actual,value in zip(result['cohorts'][name],expected[name],strict=True):close(actual['value'],value)
    for name,key in [('requested_carbohydrate_inflow','requested_fruit_allocation'),
                     ('effective_carbohydrate_inflow','fruit_allocation'),('deferred_carbohydrate_inflow','deferred_fruit_allocation'),
                     ('buffer_derivative_adjustment','buffer_adjustment')]:close(result['fruit_startup'][name]['value'],expected[key])
    for name,key in [('fruit_carbohydrate','terminal_carbohydrate'),('fruit_number','terminal_number')]:
        close(result['cohorts']['terminal_outflow'][name]['value'],expected[key])
    close(result['cohorts']['fruit_growth_respiration']['value'],expected['fruit_growth_respiration'])
    close(result['cohorts']['fruit_buffer_debit']['value'],expected['fruit_buffer_debit'])
    carbon=fsum([*(result['derivatives'][k]['value']for k in ('buffer','leaf','stem_root')),
        *(q['value']for q in result['cohorts']['derivatives']['fruit_carbohydrate']),result['growth_respiration']['value'],
        *(q['value']for q in result['vegetative_maintenance'].values()),result['fruit_maintenance']['value'],
        *(q['value']for q in result['removals'].values()),result['cohorts']['terminal_outflow']['fruit_carbohydrate']['value'],
        -result['photosynthesis']['value']])
    number=fsum([*(q['value']for q in result['cohorts']['derivatives']['fruit_number']),
        result['cohorts']['terminal_outflow']['fruit_number']['value'],
        -result['inputs']['fruit_entry']['values']['fruit_number_inflow']['value']])
    assert result['balance_residual']['carbohydrate']['value']==carbon
    assert result['balance_residual']['number']['value']==number
    for name, q in result['balance_residual'].items(): assert abs(q['value']) <= result['balance_budget'][name]['value']


@pytest.mark.parametrize('case', REFERENCE['cases'], ids=lambda c:c['case_id'])
def test_same_lai_matches_existing_independent_whole_plant_reference_and_preserves_input(case):
    before=deepcopy(case); result=run(case)
    assert_expected(result,case['expected'])
    expected=legacy.calculate_plant_startup_rates(**{key:case[key] for key in BLOCKS},**PROFILES)
    for key in ('photosynthesis','lai','requested_allocation','allocation','vegetative_maintenance','removals','cohorts','fruit_startup'):
        assert result[key] == expected[key]
    for name,q in expected['derivatives'].items():close(result['derivatives'][name]['value'],q['value'])
    assert case==before and run(case)==result
    payload={key:case[key]for key in BLOCKS};payload['geometry']=geometry(case)
    assert result['raw_input_sha256']==sha256(json.dumps(payload,sort_keys=True,separators=(',',':'),ensure_ascii=False,allow_nan=False).encode()).hexdigest()
    assert result['G0_G4']=='not_assessed' and result['claim_scope']=='synthetic_explicit_lai_carbon_cohort_math_only'
    assert result['research_assumptions']==['leaf_stem_fixed_RGR_from_reference_profile_not_measured']


@pytest.mark.parametrize('row',EXPLICIT['cases'],ids=lambda c:c['case_id'])
def test_independent_explicit_lai_reference_and_legacy_domain_difference(row):
    case=deepcopy(next(c for c in REFERENCE['cases']if c['case_id']==row['source_case_id']))
    if row['leaf_carbohydrate_override']is not None:case['state']['values']['leaf']['value']=row['leaf_carbohydrate_override']
    before=deepcopy(case)
    if row['status']!='supported':
        with pytest.raises(model.ExplicitLaiCarbonHold,match='COMPENSATION_POINT_HOLD'):run(case,row['geometry'])
    else:assert_expected(run(case,row['geometry']),row['expected'])
    assert case==before


@pytest.mark.parametrize('change', [
    lambda c,g:g.update(extra=True), lambda c,g:g.update(origin='reference_observation'),
    lambda c,g:g['values']['leaf_area_index'].update(unit='m2'),
    lambda c,g:g['values']['leaf_area_index'].update(value=float('nan')),
    lambda c,g:g['values']['leaf_area_index'].update(value=True),
    lambda c,g:c['state']['values']['leaf'].update(value=-1),
    lambda c,g:c['state']['values']['leaf'].update(value=0),
    lambda c,g:c['state']['values']['temperature_sum'].update(value=0),
    lambda c,g:c['cohort_state']['values']['temperature_sum'].update(value=999),
    lambda c,g:c['cohort_state']['values']['temperature_filtered_24h'].update(value=25),
    lambda c,g:c['cohort_state']['values']['fruit_number'].pop(),
    lambda c,g:c['fruit_entry']['values']['fruit_number_inflow'].update(value=1e100),
    lambda c,g:c['forcing'].update(origin='reference_calculation'),
    lambda c,g:c['state'].update(input_id='a'*201)])
def test_closed_shared_scope_units_domain_and_entry_budget_hold(change):
    case=deepcopy(REFERENCE['cases'][0]); area=geometry(case); change(case,area)
    with pytest.raises(model.ExplicitLaiCarbonHold):run(case,area)


def test_single_photosynthesis_startup_cohort_and_no_legacy_rhs(monkeypatch):
    case=deepcopy(REFERENCE['cases'][0]); counts=dict.fromkeys(('optical','helper','startup','cohorts'),0)
    def forbidden(**kwargs):raise AssertionError('legacy complete RHS must not run')
    monkeypatch.setattr(model.source,'calculate_rates',forbidden)
    monkeypatch.setattr(legacy,'calculate_plant_startup_rates',forbidden)
    for module,name,counter in [(model.optical,'calculate_photosynthesis','optical'),
        (model.source,'_photosynthesis','helper'),(model.startup,'calculate_startup_rates','startup'),
        (model.fruit,'calculate_cohort_rates','cohorts')]:
        original=getattr(module,name)
        def traced(*args,_original=original,_counter=counter,**kwargs):
            counts[_counter]+=1;return _original(*args,**kwargs)
        monkeypatch.setattr(module,name,traced)
    result=run(case)
    assert counts==dict.fromkeys(counts,1) and result['photosynthesis']['value']>=0


def test_unsupported_legacy_sla_canopy_does_not_reject_supported_explicit_geometry():
    case=deepcopy(next(c for c in REFERENCE['cases'] if c['forcing']['values']['canopy_temperature']['value']==17))
    case['state']['values']['leaf']['value']=1
    with pytest.raises(legacy.PlantStartupHold,match='COMPENSATION_POINT_HOLD'):
        legacy.calculate_plant_startup_rates(**{key:case[key]for key in BLOCKS},**PROFILES)
    result=run(case,geometry(case,1))
    assert result['lai']['value']==1 and result['photosynthesis']['value']>0


def test_explicit_compensation_hold_is_not_replaced_by_legacy_lai():
    case=deepcopy(next(c for c in REFERENCE['cases'] if c['forcing']['values']['canopy_temperature']['value']==17))
    with pytest.raises(model.ExplicitLaiCarbonHold,match='COMPENSATION_POINT_HOLD'):run(case,geometry(case,.001))


def test_final_depleted_buffer_has_no_outward_derivative():
    case=deepcopy(REFERENCE['cases'][0]);case['state']['values']['buffer']['value']=0
    case['forcing']['values']['par_above_canopy']['value']=0
    for q in case['fruit_entry']['values'].values():q['value']=0
    with pytest.raises(model.ExplicitLaiCarbonHold,match='DEPLETED_STATE_HOLD'):run(case)


@pytest.mark.parametrize('field',['buffer_derivative_adjustment','realized_growth_respiration'])
def test_partial_startup_policy_correction_cannot_bypass_whole_carbon_balance(monkeypatch,field):
    case=deepcopy(REFERENCE['cases'][0]);old=model.startup.calculate_startup_rates
    def damaged(**kwargs):
        result=old(**kwargs);result[field]['value']+=.125;return result
    monkeypatch.setattr(model.startup,'calculate_startup_rates',damaged)
    with pytest.raises(model.ExplicitLaiCarbonHold,match='BALANCE_HOLD'):run(case)


def test_result_and_normalized_inputs_do_not_alias_the_callers_state():
    case=deepcopy(REFERENCE['cases'][0]);before=deepcopy(case);result=run(case)
    result['inputs']['state']['values']['leaf']['value']=777
    result['cohorts']['derivatives']['fruit_carbohydrate'][0]['value']=777
    assert case==before and run(case)['inputs']['state']['values']['leaf']['value']!=777
