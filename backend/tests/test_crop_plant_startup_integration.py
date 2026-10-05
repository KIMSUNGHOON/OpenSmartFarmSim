from copy import deepcopy
from hashlib import sha256
import json
from math import exp, fsum, ulp
from pathlib import Path

import pytest

from app.crop_growth_rates import ReferenceParameters
from app.crop_fruit_cohorts import ReferenceFruitCohortParameters
from app.crop_fruit_transport import ReferenceFruitTransportParameters
from app.crop_plant_cohort_integration import integrate_plant_cohorts
from app import crop_plant_startup_integration as model

ROOT = Path(__file__).resolve().parents[2]
REFERENCE = json.loads((ROOT/'fixtures/crop-plant-startup-integration-reference-v1.json').read_bytes())
PROFILES = {
    'growth_profile': ReferenceParameters((ROOT/'fixtures/crop-growth-reference-parameters-v1.json').read_bytes()),
    'cohort_profile': ReferenceFruitCohortParameters((ROOT/'fixtures/crop-fruit-cohort-reference-parameters-v1.json').read_bytes()),
    'transport_profile': ReferenceFruitTransportParameters((ROOT/'fixtures/crop-fruit-transport-reference-parameters-v1.json').read_bytes()),
}


def program(pattern='empty-entry'):
    return deepcopy(next(c['program'] for c in REFERENCE['cases'] if c['case_id']==pattern))


def run(candidate, **profiles):
    return model.integrate_plant_startup(**candidate, **(profiles or PROFILES))


def close(actual, reference):
    expected = float(reference)
    assert abs(actual-expected)<=max(64*ulp(expected), 5e-11*abs(expected))


@pytest.mark.parametrize('case', REFERENCE['cases'], ids=lambda c:c['case_id'])
def test_matched_independent_decimal_state_cumulative_and_four_ledgers(case):
    candidate=case['program'];before=deepcopy(candidate);result=run(candidate)
    assert result['status']=='completed' and result['scope']=='software_research_only'
    assert len(result['samples'])==len(case['expected'])
    for actual, expected in zip(result['samples'], case['expected'], strict=True):
        assert actual['at']==expected['at']
        for group in ('state','cumulative'):
            for key, value in expected[group].items():
                if type(value) is list:
                    assert len(actual[group][key])==50
                    for q, v in zip(actual[group][key], value, strict=True): close(q['value'], v)
                else:close(actual[group][key]['value'], value)
        close(actual['lai']['value'], expected['lai'])
        close(actual['fruit_carbohydrate_total']['value'], expected['fruit_carbohydrate_total'])
        for field in ('carbon','number'):
            assert abs(actual[field+'_residual']['value'])<=actual[field+'_residual_budget']['value']
        for field in ('requested','growth_respiration'):
            d=actual['startup_diagnostics']
            assert abs(d[field+'_residual']['value'])<=d[field+'_budget']['value']
        for field in model.STARTUP_FLUX:
            assert actual['cumulative'][field]['unit']=='mg_CH2O/m2_floor'
    assert candidate==before
    manifest=result['manifest']
    assert manifest['program_version']=='crop-plant-startup-program-v1'
    assert manifest['integrator_version']=='crop-plant-startup-rk4-research-v1'
    assert manifest['rate_model_version']=='explicit-entry-empty-sink-plant-rates-research-v1'
    assert manifest['convergence']=='not_evaluated_for_this_program'
    assert not any(k in result for k in ('fresh_kg','harvest','rank','prediction','seed'))


@pytest.mark.parametrize('pattern', ['positive-tail','night-smooth'])
def test_overlapping_program_preserves_original_v1_states_and_old_flux(pattern):
    candidate=program(pattern);new=run(candidate);old=integrate_plant_cohorts(**candidate, **PROFILES)
    assert new['status']==old['status']=='completed' and new['events']==old['events']
    for a,b in zip(new['samples'],old['samples'],strict=True):
        assert a['state']==b['state'] and a['lai']==b['lai']
        assert {k:v for k,v in a['cumulative'].items() if k not in model.STARTUP_FLUX}==b['cumulative']
        assert a['cumulative']['deferred_fruit_carbohydrate']['value']==0
    assert new['result_sha256']!=old['result_sha256']


def test_empty_no_entry_stays_empty_and_retains_requested_carbon():
    result=run(program('empty-no-entry'))
    for sample in result['samples']:
        assert all(q['value']==0 for k in ('fruit_number','fruit_carbohydrate') for q in sample['state'][k])
        c=sample['cumulative']
        assert c['requested_fruit_carbohydrate']==c['deferred_fruit_carbohydrate']
        assert c['realized_fruit_carbohydrate']['value']==c['fruit_growth_respiration']['value']==0
    assert result['samples'][-1]['cumulative']['deferred_fruit_carbohydrate']['value']>0


def test_full_removal_is_atomic_for_number_carbon_and_can_restart_without_seed():
    candidate=program('full-removal-reentry');result=run(candidate)
    assert result['status']=='completed' and len(result['events'])==3
    middle=result['events'][1]
    assert all(q['value']==0 for k in ('fruit_number','fruit_carbohydrate') for q in middle['after'][k])
    assert result['samples'][1]['state']==middle['after']
    assert result['samples'][-1]['state']['fruit_number'][0]['value']>0
    assert result['samples'][-1]['cumulative']['event_number']['value']>0


@pytest.mark.parametrize('pattern', ['empty-entry','first-only','night-smooth'])
def test_independent_number_solution_includes_first_entry_and_deep_tail(pattern):
    case=next(c for c in REFERENCE['cases'] if c['case_id']==pattern);result=run(case['program'])
    for sample, expected in zip(result['samples'],case['analytic_number'],strict=True):
        values=[q['value'] for q in sample['state']['fruit_number']]
        reference=list(map(float,expected['fruit_number']))
        scale=fsum(reference)
        if scale==0:assert values==reference
        else:assert fsum(abs(a-b) for a,b in zip(values,reference,strict=True))<=scale*1e-9
        if sample['at']!=case['program']['output_times'][0]:assert all(v>0 for v in values)


@pytest.mark.parametrize('pattern', ['empty-entry','full-removal-reentry','night-smooth'])
def test_refinement_measures_transition_error_and_smooth_error_separately(pattern):
    case=next(c for c in REFERENCE['cases'] if c['case_id']==pattern)
    candidate=deepcopy(case['program']);reference=case['refined_expected'][-1]
    errors=[]
    for step in ((120,60,30) if pattern=='night-smooth' else (8,4,2,1)):
        candidate['solver']['max_step_seconds']=step;result=run(candidate)
        assert result['status']=='completed'
        final=result['samples'][-1]
        errors.append(max(abs(final[group][key]['value']-float(value)) for group in ('state','cumulative')
                          for key,value in reference[group].items() if type(value) is not list))
    assert all(a>b>0 for a,b in zip(errors,errors[1:]))
    if pattern=='night-smooth':assert all(a>8*b for a,b in zip(errors,errors[1:]))


def test_replay_normalized_input_policy_code_profile_hashes_and_snapshot(monkeypatch):
    candidate=program();before=deepcopy(candidate);result=run(candidate)
    assert result==run(deepcopy(candidate)) and candidate==before
    payload={k:v for k,v in result.items() if k!='result_sha256'}
    assert result['result_sha256']==sha256(json.dumps(payload,sort_keys=True,separators=(',',':'),allow_nan=False).encode()).hexdigest()
    for key,p in PROFILES.items():assert result['manifest']['profile_sha256'][key]==p.sha256
    assert result['manifest']['policy_sha256']==REFERENCE['input_sha256']['research/crop-fruit-startup-source-register.json']
    assert result['manifest']['code_sha256']==model.CODE_HASHES
    changed=deepcopy(candidate);changed['initial_state']['input_id']='different-input';other=run(changed)
    assert result['samples']==other['samples'] and result['manifest']['input_sha256']!=other['manifest']['input_sha256']
    original=model.coupled.calculate_plant_startup_rates
    def mutate_caller(**kwargs):
        candidate['solver']['max_step_seconds']=8
        candidate['segments'][0]['fruit_entry']['values']['fruit_number_inflow']['value']=100
        return original(**kwargs)
    monkeypatch.setattr(model.coupled,'calculate_plant_startup_rates',mutate_caller)
    assert run(candidate)==result


@pytest.mark.parametrize('field', ['requested_carbohydrate_inflow','realized_growth_respiration'])
def test_inconsistent_startup_flux_cannot_pass_accumulated_diagnostics(monkeypatch,field):
    original=model.coupled.calculate_plant_startup_rates
    def corrupt(**kwargs):
        result=original(**kwargs);result['fruit_startup'][field]['value']+=1
        return result
    monkeypatch.setattr(model.coupled,'calculate_plant_startup_rates',corrupt)
    result=run(program())
    assert result['status']=='hold' and 'BALANCE_HOLD' in result['hold']['reason']
    assert len(result['samples'])==1 and result['last_confirmed']['at']==program()['output_times'][0]


@pytest.mark.parametrize('kind', ['weighted-underflow','accumulated-respiration-underflow','overflow'])
def test_unrepresentable_startup_accumulations_hold_without_rounding_to_zero(monkeypatch,kind):
    original=model.coupled.calculate_plant_startup_rates
    def numeric_fault(**kwargs):
        result=original(**kwargs);s=result['fruit_startup']
        at_start=kwargs['state']['values']['temperature_sum']['value']==500
        value=1e308 if kind=='overflow' else 5e-324 if at_start or kind=='accumulated-respiration-underflow' else 0
        s['requested_carbohydrate_inflow']['value']=value
        s['effective_carbohydrate_inflow']['value']=value if kind=='accumulated-respiration-underflow' else 0
        s['deferred_carbohydrate_inflow']['value']=0 if kind=='accumulated-respiration-underflow' else value
        s['realized_growth_respiration']['value']=0
        return result
    monkeypatch.setattr(model.coupled,'calculate_plant_startup_rates',numeric_fault)
    result=run(program())
    assert result['status']=='hold' and 'NUMERIC_HOLD' in result['hold']['reason']
    assert len(result['samples'])==1 and result['last_confirmed']['at']==program()['output_times'][0]


@pytest.mark.parametrize('key,bad', [('segments',[]),('segments',[{}]),('events',[{}]),('output_times',[]),('solver',{})])
def test_closed_program_preflight(key,bad):
    candidate=program();candidate[key]=bad
    with pytest.raises(model.PlantStartupIntegrationHold):run(candidate)


@pytest.mark.parametrize('key,value', [('max_steps',0),('max_steps',True),('max_steps',10001),('max_steps',1),
    ('max_step_seconds',0),('max_step_seconds',True),('max_step_seconds',3601),('method','euler'),('roundoff_rule','clip')])
def test_solver_and_planned_budgets_preflight(key,value):
    candidate=program();candidate['solver'][key]=value
    with pytest.raises(model.PlantStartupIntegrationHold):run(candidate)


@pytest.mark.parametrize('key,limit', [('segments',128),('events',128),('output_times',512)])
def test_resource_lists_preflight(key,limit):
    candidate=program('full-removal-reentry');candidate[key]=[candidate[key][0]]*(limit+1)
    with pytest.raises(model.PlantStartupIntegrationHold,match='RESOURCE_HOLD'):run(candidate)


@pytest.mark.parametrize('kind', ['array','unit','RGR','overlap','timezone','duplicate-event','long-period'])
def test_closed_units_arrays_and_utc_boundaries_are_validated_by_new_interface(kind):
    candidate=program('full-removal-reentry')
    if kind=='array':candidate['initial_state']['values']['fruit_number'].pop()
    if kind=='unit':candidate['initial_state']['values']['buffer']['unit']='kg'
    if kind=='RGR':candidate['segments'][0]['relative_growth_rate']['values']['fruit_relative_growth_rate'][0]['value']=True
    if kind=='overlap':candidate['segments'][1]['start']=candidate['segments'][0]['start']
    if kind=='timezone':candidate['output_times'][0]='2026-01-01T09:00:00+09:00'
    if kind=='duplicate-event':candidate['events'].append(deepcopy(candidate['events'][-1]))
    if kind=='long-period':
        candidate['segments']=[candidate['segments'][0]];candidate['segments'][0]['end']='2026-01-02T00:00:01Z'
        candidate['events']=[];candidate['output_times']=[candidate['segments'][0]['start'],candidate['segments'][0]['end']]
    with pytest.raises(model.PlantStartupIntegrationHold):run(candidate)


@pytest.mark.parametrize('key', list(PROFILES))
def test_exact_profiles_required(key):
    profiles=dict(PROFILES);profiles[key]={}
    with pytest.raises(model.PlantStartupIntegrationHold,match='PROFILE_HOLD'):run(program(),**profiles)


@pytest.mark.parametrize('kind,reason', [('entry','FRUIT_ENTRY_BUDGET_HOLD'),('pre-onset','FRUIT_COHORT_DOMAIN_HOLD'),
    ('carbon-without-number','FRUIT_COHORT_STATE_HOLD'),('underflow','NUMERIC_HOLD')])
def test_runtime_domains_hold_before_any_unconfirmed_samples(kind,reason):
    candidate=program();values=candidate['initial_state']['values']
    if kind=='entry':candidate['segments'][0]['fruit_entry']['values']['fruit_number_inflow']['value']=100
    if kind=='pre-onset':values['temperature_sum']['value']=0
    if kind=='carbon-without-number':values['fruit_carbohydrate'][0]['value']=1
    if kind=='underflow':values['stem_root']['value']=5e-324
    result=run(candidate)
    assert result['status']=='hold' and reason in result['hold']['reason']
    assert not result['samples'] and not result['events'] and result['last_confirmed'] is None


def test_event_failure_and_negative_trial_preserve_only_confirmed_past():
    candidate=program('full-removal-reentry');candidate['events'][1]['removals']['values']['leaf']['value']=1e6
    result=run(candidate)
    assert result['status']=='hold' and result['hold']['phase']=='event' and len(result['samples'])==1
    assert result['last_confirmed']['at']==candidate['events'][1]['at'] and len(result['events'])==1
    candidate=program('night-smooth');candidate['initial_state']['values']['buffer']['value']=1
    candidate['output_times']=[candidate['output_times'][0],candidate['output_times'][-1]]
    candidate['solver']['max_step_seconds']=3600;result=run(candidate)
    assert result['status']=='hold' and result['hold']['phase']=='rk4-k2' and len(result['samples'])==1
    assert 'DEPLETED_STATE_HOLD' in result['hold']['reason']


def test_temperature_filter_and_fraction_clock_are_separate_from_startup_policy():
    candidate=program();candidate['initial_state']['values']['temperature_filtered_24h']['value']=21
    result=run(candidate)
    assert result['status']=='completed'
    for sample,t in zip(result['samples'],(0,60,120),strict=True):
        assert abs(sample['state']['temperature_filtered_24h']['value']-(20+exp(-t/86400)))<=64*ulp(21)
        assert sample['state']['temperature_sum']['value']==float(500+20*t/86400)


def test_independent_inputs_and_generator_pins():
    for path,digest in REFERENCE['input_sha256'].items():assert sha256((ROOT/path).read_bytes()).hexdigest()==digest
    assert sha256((ROOT/'research/crop-plant-startup-integration-reference.py').read_bytes()).hexdigest()==REFERENCE['generator_sha256']
