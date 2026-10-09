from copy import deepcopy
from hashlib import sha256
import json
from math import fsum, ulp
from pathlib import Path

import pytest

from app.crop_fruit_allocation import UNITS, calculate_allocation_rates
from app.crop_fruit_cohorts import ReferenceFruitCohortParameters
from app.crop_fruit_startup import FruitStartupHold, POLICY_SHA256, calculate_startup_rates

ROOT = Path(__file__).resolve().parents[2]
REFERENCE = json.loads((ROOT/'research/artifacts/crop-fruit-startup-policy-reference-20261005.json').read_bytes())
PROFILE = ReferenceFruitCohortParameters((ROOT/'fixtures/crop-fruit-cohort-reference-parameters-v1.json').read_bytes())


def inputs(case=None):
    case = case or REFERENCE['cases'][0]
    values = {name:{'value':float(case[key]) if case[key] is not None else None,'unit':UNITS[name]}
        for name,key in (('fruit_carbohydrate_inflow','requested_F'),
                        ('fruit_number_inflow','S'),('fruit_entry_carbohydrate','W1'))}
    values['fruit_potential_demand'] = [{'value':float(w),'unit':UNITS['fruit_potential_demand']} for w in case['weights']]
    return {'input_id':case['case_id'],'origin':'synthetic','values':values}


@pytest.mark.parametrize('case', REFERENCE['cases'], ids=lambda c:c['case_id'])
def test_independent_decimal_startup_conservation_or_hold(case):
    state=inputs(case); before=deepcopy(state)
    if case['expected_hold']:
        with pytest.raises(FruitStartupHold,match=case['expected_hold']):
            calculate_startup_rates(state=state,profile=PROFILE)
        assert state==before
        return
    result=calculate_startup_rates(state=state,profile=PROFILE)
    assert result['scope']=='software_research_only' and result['policy_id']==REFERENCE['policy_id']
    for name,key in (('effective_carbohydrate_inflow','effective_F'),('deferred_carbohydrate_inflow','deferred_F'),
                     ('buffer_derivative_adjustment','buffer_derivative_adjustment'),
                     ('realized_growth_respiration','realized_growth_respiration')):
        expected=float(case[key]); q=result[name]
        assert q['unit']==UNITS['fruit_carbohydrate_inflow']
        assert abs(q['value']-expected)<=16*ulp(expected)
    for name,key,unit in (('carbohydrate_inflow','allocation',UNITS['fruit_carbohydrate_inflow']),
                          ('number_inflow','number_inflow',UNITS['fruit_number_inflow'])):
        assert len(result[name])==50
        for q,value in zip(result[name],case[key],strict=True):
            assert q['unit']==unit and abs(q['value']-float(value))<=16*ulp(float(value))
    actual=result['effective_carbohydrate_inflow']['value']; deferred=result['deferred_carbohydrate_inflow']['value']
    requested=float(case['requested_F']); cg=.27
    for name,residual in (
        ('request',fsum((actual,deferred,-requested))),
        ('whole_plant',fsum((-requested,-requested*cg,result['buffer_derivative_adjustment']['value'],
                            *(q['value'] for q in result['carbohydrate_inflow']),
                            result['realized_growth_respiration']['value'])))):
        assert result['balance_residual'][name]['value']==residual
        assert abs(residual)<=result['balance_budget'][name]['value']
    if deferred==0:
        old=calculate_allocation_rates(state=state)
        assert result['carbohydrate_inflow']==old['carbohydrate_inflow']
        assert result['number_inflow']==old['number_inflow']
    assert state==before and result==calculate_startup_rates(state=deepcopy(state),profile=PROFILE)
    assert not any(k in result for k in ('fresh_kg','harvest','prediction','initial_seed','automatic_set'))


def test_policy_and_profile_pins_and_requested_provenance_hash():
    assert POLICY_SHA256==sha256((ROOT/'research/crop-fruit-startup-source-register.json').read_bytes()).hexdigest()
    state=inputs(REFERENCE['cases'][3]); first=calculate_startup_rates(state=state,profile=PROFILE)
    assert first['profile_sha256']==PROFILE.sha256
    for key,value in (('input_id','other-input'),('origin','reference_calculation')):
        changed=deepcopy(state);changed[key]=value
        assert calculate_startup_rates(state=changed,profile=PROFILE)['input_sha256']!=first['input_sha256']
    state['values']['fruit_carbohydrate_inflow']['value']*=2
    second=calculate_startup_rates(state=state,profile=PROFILE)
    assert first['carbohydrate_inflow']==second['carbohydrate_inflow']
    assert first['input_sha256']!=second['input_sha256']
    assert first['deferred_carbohydrate_inflow']!=second['deferred_carbohydrate_inflow']


@pytest.mark.parametrize('name',list(UNITS))
@pytest.mark.parametrize('bad',[float('nan'),float('inf'),-1,True,None,'1'])
def test_invalid_quantities_held_even_if_demand_unused(name,bad):
    state=inputs(REFERENCE['cases'][5]);q=state['values'][name]
    if name=='fruit_potential_demand':q=q[0]
    q['value']=bad
    with pytest.raises(FruitStartupHold,match='INPUT_HOLD'):
        calculate_startup_rates(state=state,profile=PROFILE)


@pytest.mark.parametrize('mutation',['state','values','id','origin','quantity','units','length','array'])
def test_closed_shapes_units_and_provenance(mutation):
    state=inputs()
    if mutation=='state':state['extra']=0
    if mutation=='values':del state['values']['fruit_number_inflow']
    if mutation=='id':state['input_id']='x'*257
    if mutation=='origin':state['origin']='approved'
    if mutation=='quantity':state['values']['fruit_entry_carbohydrate']['extra']=0
    if mutation=='units':state['values']['fruit_entry_carbohydrate']['unit']='kg'
    if mutation=='length':state['values']['fruit_potential_demand'].pop()
    if mutation=='array':state['values']['fruit_potential_demand']=tuple(state['values']['fruit_potential_demand'])
    with pytest.raises(FruitStartupHold):calculate_startup_rates(state=state,profile=PROFILE)


@pytest.mark.parametrize('kind',['entry-overflow','entry-underflow','demand-overflow','respiration-underflow',
                                'retention-overflow','tail-underflow'])
def test_unrepresentable_positive_results_are_held(kind):
    state=inputs(REFERENCE['cases'][3]);v=state['values']
    if kind=='entry-overflow':v['fruit_number_inflow']['value']=v['fruit_entry_carbohydrate']['value']=1e308
    if kind=='entry-underflow':v['fruit_number_inflow']['value']=v['fruit_entry_carbohydrate']['value']=1e-300
    if kind=='demand-overflow':
        for q in v['fruit_potential_demand'][1:]:q['value']=1e308
    if kind=='respiration-underflow':
        v['fruit_number_inflow']['value']=v['fruit_carbohydrate_inflow']['value']=5e-324
    if kind=='retention-overflow':v['fruit_carbohydrate_inflow']['value']=1.7e308
    if kind=='tail-underflow':
        v['fruit_potential_demand'][1]['value']=1e-300
        v['fruit_potential_demand'][2]['value']=1e300
    with pytest.raises(FruitStartupHold,match='NUMERIC_HOLD'):
        calculate_startup_rates(state=state,profile=PROFILE)


@pytest.mark.parametrize('profile',[None,{},'unreviewed'])
def test_exact_reviewed_profile_required(profile):
    with pytest.raises(FruitStartupHold,match='PROFILE_HOLD'):
        calculate_startup_rates(state=inputs(),profile=profile)
