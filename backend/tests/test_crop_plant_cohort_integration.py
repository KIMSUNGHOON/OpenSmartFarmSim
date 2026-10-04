from copy import deepcopy
from hashlib import sha256
import json
from math import exp, fsum
from pathlib import Path

import pytest

from app.crop_growth_rates import ReferenceParameters
from app.crop_fruit_cohorts import ReferenceFruitCohortParameters
from app.crop_fruit_transport import ReferenceFruitTransportParameters
from app.crop_plant_cohort_integration import PlantCohortIntegrationHold, integrate_plant_cohorts


ROOT = Path(__file__).resolve().parents[2]
REFERENCE = json.loads((ROOT/'fixtures/crop-plant-cohort-integration-reference-v1.json').read_bytes())
PROFILES = {
    'growth_profile':ReferenceParameters((ROOT/'fixtures/crop-growth-reference-parameters-v1.json').read_bytes()),
    'cohort_profile':ReferenceFruitCohortParameters((ROOT/'fixtures/crop-fruit-cohort-reference-parameters-v1.json').read_bytes()),
    'transport_profile':ReferenceFruitTransportParameters((ROOT/'fixtures/crop-fruit-transport-reference-parameters-v1.json').read_bytes()),
}


def program(index=0):
    return deepcopy(REFERENCE['cases'][index]['program'])


def run(candidate,**profiles):
    return integrate_plant_cohorts(**candidate,**(profiles or PROFILES))


@pytest.mark.parametrize('case',REFERENCE['cases'],ids=lambda c:c['case_id'])
def test_refined_independent_full_state_cumulative_and_analytic_number(case):
    result=run(case['program'])
    assert result['status']=='completed' and result['scope']=='software_research_only'
    assert len(result['samples'])==len(case['expected'])
    for actual,reference in zip(result['samples'],case['expected'],strict=True):
        assert actual['at']==reference['at']
        for group in ('state','cumulative'):
            for key,target in reference[group].items():
                quantities=actual[group][key]
                if isinstance(target,list):
                    assert len(quantities)==len(target)==50
                    for quantity,value in zip(quantities,target,strict=True):
                        assert quantity['value']==pytest.approx(float(value),rel=5e-9,abs=5e-9)
                else:assert quantities['value']==pytest.approx(float(target),rel=5e-9,abs=5e-9)
        assert actual['lai']['value']==pytest.approx(float(reference['lai']),rel=5e-9,abs=5e-9)
        assert actual['fruit_carbohydrate_total']['value']==fsum(q['value'] for q in actual['state']['fruit_carbohydrate'])
        for key in ('carbon','number'):
            assert abs(actual[key+'_residual']['value'])<=actual[key+'_residual_budget']['value']
    for actual,reference in zip(result['samples'],case.get('analytic_number',[])):
        for q,value in zip(actual['state']['fruit_number'],reference['fruit_number'],strict=True):
            assert q['value']==pytest.approx(float(value),rel=1e-12,abs=2e-14)
    assert result['manifest']['time_rule']=='UTC_POSIX_whole_seconds_v1'
    assert not any(k in result for k in ('fresh_kg','harvest','rank','prediction'))


def test_management_removes_matching_number_and_carbon_including_endpoint_events():
    candidate=program();result=run(candidate)
    assert [j['at'] for j in result['events']]==[e['at'] for e in candidate['events']]
    for journal,event in zip(result['events'],candidate['events'],strict=True):
        for k in ('leaf','stem_root'):
            assert journal['before'][k]['value']-journal['after'][k]['value']==pytest.approx(event['removals']['values'][k]['value'])
        for k in ('fruit_number','fruit_carbohydrate'):
            for before,after,f in zip(journal['before'][k],journal['after'][k],event['removals']['values']['fruit_fraction'],strict=True):
                assert after['value']==pytest.approx(before['value']*(1-f['value']))
        if event['at'] in candidate['output_times']:
            sample=next(s for s in result['samples'] if s['at']==event['at'])
            assert sample['state']==journal['after']
    assert result['samples'][0]['cumulative']['event_number']['value']==pytest.approx(.02)


def test_step_refinement_decreases_error_against_independent_night_reference():
    candidate=program(1);expected=REFERENCE['cases'][1]['expected'][-1]
    errors=[]
    for step in (120,60,30):
        candidate['solver']['max_step_seconds']=step;result=run(candidate)
        assert result['status']=='completed'
        final=result['samples'][-1]
        errors.append(max(abs(final[group][key]['value']-float(value))
            for group in ('state','cumulative') for key,value in expected[group].items() if not isinstance(value,list)))
    assert errors[0]>8*errors[1]>64*errors[2]>0


def test_temperature_filter_analytic_limit_and_exact_fraction_clock():
    candidate=program();candidate['initial_state']['values']['temperature_filtered_24h']['value']=21
    result=run(candidate);assert result['status']=='completed'
    for sample,t in zip(result['samples'],(0,60,120,180,240,300),strict=True):
        assert sample['state']['temperature_filtered_24h']['value']==pytest.approx(20+exp(-t/86400),abs=2e-13)
        assert sample['state']['temperature_sum']['value']==float(500+20*t/86400)


def test_immutable_inputs_profiles_same_manifest_result_and_input_binding():
    candidate=program();before=deepcopy(candidate);result=run(candidate)
    assert candidate==before and result==run(deepcopy(candidate))
    payload={k:v for k,v in result.items() if k!='result_sha256'}
    assert result['result_sha256']==sha256(json.dumps(payload,sort_keys=True,separators=(',',':'),allow_nan=False).encode()).hexdigest()
    changed=deepcopy(candidate);changed['initial_state']['input_id']='x'*256
    other=run(changed);assert other['status']=='completed'
    assert other['samples']==result['samples'] and other['manifest']['input_sha256']!=result['manifest']['input_sha256']
    assert all(result['manifest']['profile_sha256'][key]==p.sha256 for key,p in PROFILES.items())


def test_running_calculation_uses_snapshot_when_caller_changes_solver(monkeypatch):
    from app import crop_plant_cohort_rates
    candidate=program();expected=run(deepcopy(candidate))
    original=crop_plant_cohort_rates.calculate_plant_cohort_rates
    def caller_update(**kwargs):
        candidate['solver']['max_step_seconds']=1
        return original(**kwargs)
    monkeypatch.setattr(crop_plant_cohort_rates,'calculate_plant_cohort_rates',caller_update)
    actual=run(candidate)
    assert candidate['solver']['max_step_seconds']==1
    assert actual==expected


@pytest.mark.parametrize('key,bad',[('segments',[]),('segments',[{}]),('events',[{}]),('output_times',[]),('output_times',['bad']),('solver',{})])
def test_invalid_closed_time_program_held_before_execution(key,bad):
    candidate=program();candidate[key]=bad
    with pytest.raises(PlantCohortIntegrationHold):run(candidate)


@pytest.mark.parametrize('key,value',[('max_steps',0),('max_steps',10001),('max_steps',True),('max_steps',1),
    ('max_step_seconds',0),('max_step_seconds',3601),('max_step_seconds',True),('method','euler'),('roundoff_rule','clip')])
def test_solver_and_planned_step_budgets_checked(key,value):
    candidate=program();candidate['solver'][key]=value
    with pytest.raises(PlantCohortIntegrationHold):run(candidate)


@pytest.mark.parametrize('key,limit',[('segments',128),('events',128),('output_times',512)])
def test_bounded_arrays_preflight(key,limit):
    candidate=program();candidate[key]=[candidate[key][0]]*(limit+1)
    with pytest.raises(PlantCohortIntegrationHold,match='RESOURCE_HOLD'):run(candidate)


@pytest.mark.parametrize('key',list(PROFILES))
def test_unpinned_profiles_preflight(key):
    profiles=dict(PROFILES);profiles[key]={}
    with pytest.raises(PlantCohortIntegrationHold,match='PROFILE_HOLD'):run(program(),**profiles)


@pytest.mark.parametrize('key,value',[('origin','approved'),('input_id',' '),('input_id','x'*257)])
def test_initial_provenance_preflight(key,value):
    candidate=program();candidate['initial_state'][key]=value
    with pytest.raises(PlantCohortIntegrationHold,match='INPUT_HOLD'):run(candidate)


@pytest.mark.parametrize('bad',[float('nan'),float('inf'),-1,True,'1',None])
def test_invalid_quantities_preflight(bad):
    candidate=program();candidate['segments'][0]['relative_growth_rate']['values']['fruit_relative_growth_rate'][0]['value']=bad
    with pytest.raises(PlantCohortIntegrationHold,match='INPUT_HOLD'):run(candidate)


def test_units_compartment_lengths_and_fraction_bounds_preflight():
    candidate=program();candidate['initial_state']['values']['fruit_number'].pop()
    with pytest.raises(PlantCohortIntegrationHold,match='INPUT_HOLD'):run(candidate)
    candidate=program();candidate['initial_state']['values']['buffer']['unit']='kg'
    with pytest.raises(PlantCohortIntegrationHold,match='UNIT_HOLD'):run(candidate)
    candidate=program();candidate['events'][0]['removals']['values']['fruit_fraction'][0]['value']=1.01
    with pytest.raises(PlantCohortIntegrationHold,match='INPUT_HOLD'):run(candidate)


def test_overlap_timezone_duplicate_external_events_and_day_limit_preflight():
    for kind in ('overlap','timezone','duplicate','external','long'):
        candidate=program()
        if kind=='overlap':candidate['segments'][1]['start']=candidate['segments'][0]['start']
        elif kind=='timezone':candidate['output_times'][0]='2026-01-01T09:00:00+09:00'
        elif kind=='duplicate':candidate['events'].append(deepcopy(candidate['events'][-1]))
        elif kind=='external':candidate['events'][-1]['at']='2026-01-02T00:00:00Z'
        else:
            candidate['segments']=[candidate['segments'][0]];candidate['segments'][0]['end']='2026-01-02T00:00:01Z'
            candidate['events']=[];candidate['output_times']=[candidate['segments'][0]['start'],candidate['segments'][0]['end']]
        with pytest.raises(PlantCohortIntegrationHold,match='TIME_HOLD|RESOURCE_HOLD'):run(candidate)


def test_over_removal_returns_hold_with_only_confirmed_samples():
    candidate=program();candidate['events'][1]['removals']['values']['leaf']['value']=1e6
    result=run(candidate)
    assert result['status']=='hold' and 'REMOVAL_EXCEEDS_STORAGE_HOLD' in result['hold']['reason']
    assert result['hold']['at']==candidate['events'][1]['at'] and result['hold']['phase']=='event'
    assert len(result['samples'])==3 and len(result['events'])==1
    assert result['last_confirmed']['at']==candidate['events'][1]['at']


def test_negative_trial_is_held_without_clipping_or_future_samples():
    candidate=program(1);candidate['initial_state']['values']['buffer']['value']=1
    candidate['output_times']=[candidate['output_times'][0],candidate['output_times'][-1]]
    candidate['solver']['max_step_seconds']=3600
    result=run(candidate)
    assert result['status']=='hold' and result['hold']['phase']=='rk4-k2'
    assert 'DEPLETED_STATE_HOLD' in result['hold']['reason']
    assert len(result['samples'])==1 and result['last_confirmed']['at']==candidate['output_times'][0]


def test_empty_tail_entry_budget_and_positive_outflow_underflow_are_runtime_holds():
    for kind in ('empty','entry','underflow'):
        candidate=program()
        if kind=='empty':
            for name in ('fruit_number','fruit_carbohydrate'):
                for q in candidate['initial_state']['values'][name]:q['value']=0
        elif kind=='entry':candidate['segments'][0]['fruit_entry']['values']['fruit_number_inflow']['value']=100
        else:
            candidate['events']=[]
            for q in candidate['initial_state']['values']['fruit_carbohydrate']:q['value']=5e-324
        result=run(candidate)
        assert result['status']=='hold' and not result['samples'] and not result['events']
        assert result['last_confirmed'] is None


def test_positive_stem_maintenance_underflow_is_not_silently_accepted():
    candidate=program();candidate['events']=[]
    candidate['initial_state']['values']['stem_root']['value']=5e-324
    result=run(candidate)
    assert result['status']=='hold'
    assert result['hold']['reason']=='NUMERIC_HOLD: positive vegetative maintenance underflow'
    assert not result['samples'] and result['last_confirmed'] is None


def test_independent_reference_files_and_generator_hashes():
    for name,wanted in REFERENCE['input_sha256'].items():assert sha256((ROOT/name).read_bytes()).hexdigest()==wanted
    assert sha256((ROOT/'research/crop-plant-cohort-integration-reference.py').read_bytes()).hexdigest()==REFERENCE['generator_sha256']
