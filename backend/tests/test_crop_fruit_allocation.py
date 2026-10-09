from copy import deepcopy
from hashlib import sha256
import json
from math import fsum, ulp
from pathlib import Path

import pytest

from app.crop_fruit_allocation import (
    FruitAllocationHold, POLICY_SHA256, calculate_allocation_rates,
)


ROOT = Path(__file__).resolve().parents[2]
REFERENCE = json.loads((ROOT / 'research/artifacts/crop-fruit-allocation-policy-reference-20261005.json').read_bytes())
UNITS = {'fruit_carbohydrate_inflow': 'mg_CH2O/m2_floor/s',
         'fruit_number_inflow': 'fruits_equivalent/m2_floor/s',
         'fruit_entry_carbohydrate': 'mg_CH2O/fruit_equivalent',
         'fruit_potential_demand': 'mg_CH2O/m2_floor/day'}


def inputs(case=None):
    case = case or next(c for c in REFERENCE['cases'] if c['case_id'] == 'synthetic-mixed')
    values = {field: {'value': float(case[key]), 'unit': UNITS[field]} for field, key in (
        ('fruit_carbohydrate_inflow', 'F'), ('fruit_number_inflow', 'S'),
        ('fruit_entry_carbohydrate', 'W1'))}
    values['fruit_potential_demand'] = [{'value': float(v), 'unit': UNITS['fruit_potential_demand']}
                                      for v in case['demand']]
    return {'input_id': case['case_id'], 'origin': 'synthetic', 'values': values}


@pytest.mark.parametrize('case', REFERENCE['cases'], ids=lambda c: c['case_id'])
def test_independent_decimal_policy_reference_and_holds(case):
    state = inputs(case)
    if case['expected_hold']:
        with pytest.raises(FruitAllocationHold, match=case['expected_hold']):
            calculate_allocation_rates(state=state)
        return
    result = calculate_allocation_rates(state=state)
    assert result['model_version'] == 'explicit-entry-fruit-allocation-rates-v1'
    assert result['policy_id'] == REFERENCE['policy_id']
    assert result['scope'] == 'software_research_only'
    assert result['policy_sha256'] == REFERENCE['source_register_sha256'] == POLICY_SHA256
    assert len(result['carbohydrate_inflow']) == len(result['number_inflow']) == 50
    for group, key, unit in (('carbohydrate_inflow', 'expected_allocation', 'mg_CH2O/m2_floor/s'),
                            ('number_inflow', 'expected_number_inflow', 'fruits_equivalent/m2_floor/s')):
        for actual, expected in zip(result[group], case[key], strict=True):
            assert actual['value'] == pytest.approx(float(expected), rel=5e-12, abs=5e-14)
            assert actual['unit'] == unit
        target = float(case['F'] if group == 'carbohydrate_inflow' else case['S'])
        residual = fsum([*(q['value'] for q in result[group]), -target])
        assert abs(residual) <= 102 * ulp(target)
        assert result['balance_residual'][group] == {'value': residual, 'unit': unit}
        assert result['balance_budget'][group]['unit'] == unit
        assert abs(residual) <= result['balance_budget'][group]['value']
    assert not any(name in result for name in ('harvest', 'fresh_kg', 'prediction'))


def test_policy_source_hash_input_binding_replay_and_no_mutation():
    assert POLICY_SHA256 == sha256((ROOT / 'research/crop-fruit-allocation-source-register.json').read_bytes()).hexdigest()
    state = inputs(); original = deepcopy(state)
    result = calculate_allocation_rates(state=state)
    assert state == original and result == calculate_allocation_rates(state=deepcopy(state))
    for name, replacement in (('input_id', 'other-version'), ('origin', 'reference_calculation')):
        changed = deepcopy(state); changed[name] = replacement
        other = calculate_allocation_rates(state=changed)
        assert other['input_sha256'] != result['input_sha256']
        assert other['carbohydrate_inflow'] == result['carbohydrate_inflow']
    changed = deepcopy(state); changed['values']['fruit_potential_demand'][1]['value'] *= 2
    assert calculate_allocation_rates(state=changed)['input_sha256'] != result['input_sha256']
    for field in ('fruit_carbohydrate_inflow', 'fruit_number_inflow', 'fruit_entry_carbohydrate'):
        changed = deepcopy(state); changed['values'][field]['value'] *= 2
        assert calculate_allocation_rates(state=changed)['input_sha256'] != result['input_sha256']


@pytest.mark.parametrize('factor', [0, 0.001, 2, 1e100])
def test_carbon_and_number_scaling_without_entry_mass_change(factor):
    state = inputs(); initial = calculate_allocation_rates(state=state)
    for name in ('fruit_carbohydrate_inflow', 'fruit_number_inflow'):
        state['values'][name]['value'] *= factor
    other = calculate_allocation_rates(state=state)
    for group in ('carbohydrate_inflow', 'number_inflow'):
        for before, after in zip(initial[group], other[group], strict=True):
            assert after['value'] == pytest.approx(before['value'] * factor)


@pytest.mark.parametrize('field', list(UNITS))
@pytest.mark.parametrize('bad', [float('nan'), float('inf'), -1, True, '1', None])
def test_nonfinite_negative_or_non_numeric_value_held(field, bad):
    state = inputs()
    quantity = state['values'][field][0] if field == 'fruit_potential_demand' else state['values'][field]
    quantity['value'] = bad
    with pytest.raises(FruitAllocationHold, match='INPUT_HOLD'):
        calculate_allocation_rates(state=state)


@pytest.mark.parametrize('field', list(UNITS))
def test_units_and_closed_quantity_shape_required(field):
    state = inputs()
    quantity = state['values'][field][0] if field == 'fruit_potential_demand' else state['values'][field]
    quantity['unit'] = 'unknown'
    with pytest.raises(FruitAllocationHold, match='UNIT_HOLD'):
        calculate_allocation_rates(state=state)
    quantity['unit'] = UNITS[field]; quantity['extra'] = 0
    with pytest.raises(FruitAllocationHold, match='INPUT_HOLD'):
        calculate_allocation_rates(state=state)


@pytest.mark.parametrize('size', [0, 49, 51])
def test_exact_fifty_compartments_required(size):
    state = inputs(); state['values']['fruit_potential_demand'] = [
        {'value': 1, 'unit': UNITS['fruit_potential_demand']}] * size
    with pytest.raises(FruitAllocationHold, match='INPUT_HOLD'):
        calculate_allocation_rates(state=state)


@pytest.mark.parametrize('bad', [None, {}, 1, (1,) * 50, [1] * 50])
def test_malformed_array_held(bad):
    state = inputs(); state['values']['fruit_potential_demand'] = bad
    with pytest.raises(FruitAllocationHold, match='INPUT_HOLD'):
        calculate_allocation_rates(state=state)


@pytest.mark.parametrize('bad', [None, [], {}, {'origin': 'synthetic'}])
def test_closed_state_required(bad):
    with pytest.raises(FruitAllocationHold, match='INPUT_HOLD'):
        calculate_allocation_rates(state=bad)


@pytest.mark.parametrize('bad', [None, [], 1])
def test_closed_values_object_required(bad):
    state = inputs(); state['values'] = bad
    with pytest.raises(FruitAllocationHold, match='INPUT_HOLD'):
        calculate_allocation_rates(state=state)


def test_extra_state_block_held():
    state = inputs(); state['management'] = {}
    with pytest.raises(FruitAllocationHold, match='INPUT_HOLD'):
        calculate_allocation_rates(state=state)


@pytest.mark.parametrize('field', ['input_id', 'origin', 'values', *UNITS])
def test_missing_or_extra_state_field_held(field):
    state = inputs()
    del (state['values'] if field in UNITS else state)[field]
    with pytest.raises(FruitAllocationHold, match='INPUT_HOLD'):
        calculate_allocation_rates(state=state)
    state = inputs(); state['values']['extra'] = {}
    with pytest.raises(FruitAllocationHold, match='INPUT_HOLD'):
        calculate_allocation_rates(state=state)


@pytest.mark.parametrize('value', ['', '  ', 1, None, 'x' * 257])
def test_bounded_explicit_id_required(value):
    state = inputs(); state['input_id'] = value
    with pytest.raises(FruitAllocationHold, match='INPUT_HOLD'):
        calculate_allocation_rates(state=state)


@pytest.mark.parametrize('bad', ['approved', '', [], {}])
def test_origin_does_not_grant_approval(bad):
    state = inputs(); state['origin'] = bad
    with pytest.raises(FruitAllocationHold, match='INPUT_HOLD'):
        calculate_allocation_rates(state=state)


def test_entry_and_weight_aggregate_overflow_or_underflow_held():
    state = inputs(); state['values']['fruit_number_inflow']['value'] = 1e308
    state['values']['fruit_entry_carbohydrate']['value'] = 1e308
    with pytest.raises(FruitAllocationHold, match='NUMERIC_HOLD'):
        calculate_allocation_rates(state=state)
    state = inputs(); state['values']['fruit_number_inflow']['value'] = 1e-320
    state['values']['fruit_entry_carbohydrate']['value'] = 1e-320
    with pytest.raises(FruitAllocationHold, match='NUMERIC_HOLD'):
        calculate_allocation_rates(state=state)
    state = inputs()
    for q in state['values']['fruit_potential_demand'][1:]: q['value'] = 1e308
    with pytest.raises(FruitAllocationHold, match='NUMERIC_HOLD'):
        calculate_allocation_rates(state=state)
    state = inputs(); state['values']['fruit_carbohydrate_inflow']['value'] = 10 ** 10000
    with pytest.raises(FruitAllocationHold, match='NUMERIC_HOLD'):
        calculate_allocation_rates(state=state)


def test_positive_tail_allocation_underflow_held():
    state = inputs(); state['values']['fruit_number_inflow']['value'] = 0
    state['values']['fruit_carbohydrate_inflow']['value'] = 1e-320
    state['values']['fruit_potential_demand'][1]['value'] = 1e-10
    with pytest.raises(FruitAllocationHold, match='NUMERIC_HOLD'):
        calculate_allocation_rates(state=state)
