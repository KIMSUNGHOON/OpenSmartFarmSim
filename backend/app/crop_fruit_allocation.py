"""Instantaneous explicit-entry allocation; policy/source record is hash-pinned."""

from hashlib import sha256
import json
from math import fsum, isfinite, ulp


MODEL_VERSION = 'explicit-entry-fruit-allocation-rates-v1'
POLICY_ID = 'explicit-entry-fruit-allocation-research-v1'
POLICY_SHA256 = 'edbc67cfe59a61a1573ef5b1f189c548c47a74b996d4ef6221adc663c1cc306a'
STAGES = 50
UNITS = {'fruit_carbohydrate_inflow': 'mg_CH2O/m2_floor/s',
         'fruit_number_inflow': 'fruits_equivalent/m2_floor/s',
         'fruit_entry_carbohydrate': 'mg_CH2O/fruit_equivalent',
         'fruit_potential_demand': 'mg_CH2O/m2_floor/day'}


class FruitAllocationHold(ValueError):
    """An input or numeric domain for which no allocation is supplied."""


def _need(condition, reason):
    if not condition:
        raise FruitAllocationHold(reason)


def _number(quantity, unit):
    _need(type(quantity) is dict and set(quantity) == {'value', 'unit'},
          'INPUT_HOLD: closed quantity required')
    _need(quantity['unit'] == unit, 'UNIT_HOLD: unexpected quantity unit')
    _need(type(quantity['value']) in (int, float), 'INPUT_HOLD: numeric value required')
    try:
        value = float(quantity['value'])
    except OverflowError as exc:
        raise FruitAllocationHold('NUMERIC_HOLD: unrepresentable input') from exc
    _need(isfinite(value) and value >= 0, 'INPUT_HOLD: finite nonnegative value required')
    return value


def _quantity(value, unit):
    return {'value': value, 'unit': unit}


def calculate_allocation_rates(*, state):
    """Return conserved instantaneous inflows; no set prediction or state advance."""
    _need(type(state) is dict and set(state) == {'input_id', 'origin', 'values'},
          'INPUT_HOLD: closed state block required')
    _need(type(state['input_id']) is str and 0 < len(state['input_id']) <= 256
          and bool(state['input_id'].strip()) and type(state['origin']) is str
          and state['origin'] in ('synthetic', 'reference_calculation', 'reference_observation'),
          'INPUT_HOLD: explicit bounded provenance required')
    _need(type(state['values']) is dict and set(state['values']) == set(UNITS),
          'INPUT_HOLD: missing or unexpected quantity')
    values, normalized = {}, {}
    for field, unit in UNITS.items():
        raw = state['values'][field]
        if field == 'fruit_potential_demand':
            _need(type(raw) is list and len(raw) == STAGES, 'INPUT_HOLD: exact demand array required')
            values[field] = [_number(q, unit) for q in raw]
            normalized[field] = [_quantity(v, unit) for v in values[field]]
        else:
            values[field] = _number(raw, unit)
            normalized[field] = _quantity(values[field], unit)
    carbon = values['fruit_carbohydrate_inflow']
    number = values['fruit_number_inflow']
    entry_mass = values['fruit_entry_carbohydrate']
    demand = values['fruit_potential_demand']
    _need(number == 0 or entry_mass > 0, 'FRUIT_ENTRY_STATE_HOLD: positive set requires entry mass')
    entry = number * entry_mass
    _need(isfinite(entry) and (number == 0 or entry > 0),
          'NUMERIC_HOLD: nonfinite or positive entry underflow')
    remaining = carbon - entry
    _need(remaining >= 0, 'FRUIT_ENTRY_BUDGET_HOLD: entry exceeds total carbon inflow')
    try:
        if remaining > 0:
            denominator = fsum(demand[1:])
            _need(denominator > 0, 'EMPTY_FRUIT_SINK_HOLD: remaining inflow without tail demand')
            tail = [remaining * (w / denominator) for w in demand[1:]]
            _need(all(isfinite(a) and (w == 0 or a > 0) for w, a in zip(demand[1:], tail, strict=True)),
                  'NUMERIC_HOLD: nonfinite or positive tail underflow')
        else:
            tail = [0.0] * (STAGES - 1)
        inflows = {'carbohydrate_inflow': [entry, *tail],
                   'number_inflow': [number, *([0.0] * (STAGES - 1))]}
        residuals, budgets, output = {}, {}, {}
        for group, target, unit in (('carbohydrate_inflow', carbon, UNITS['fruit_carbohydrate_inflow']),
                                    ('number_inflow', number, UNITS['fruit_number_inflow'])):
            residual = fsum([*inflows[group], -target])
            budget = 2 * (STAGES + 1) * ulp(target)
            _need(isfinite(residual) and abs(residual) <= budget,
                  'BALANCE_HOLD: unresolved inflow residual')
            residuals[group], budgets[group] = _quantity(residual, unit), _quantity(budget, unit)
            output[group] = [_quantity(v, unit) for v in inflows[group]]
    except OverflowError as exc:
        raise FruitAllocationHold('NUMERIC_HOLD: aggregate overflow') from exc
    bound = {'model_version': MODEL_VERSION, 'policy_sha256': POLICY_SHA256,
             'state': {'input_id': state['input_id'], 'origin': state['origin'], 'values': normalized}}
    digest = sha256(json.dumps(bound, sort_keys=True, separators=(',', ':'), allow_nan=False).encode()).hexdigest()
    return {'model_version': MODEL_VERSION, 'policy_id': POLICY_ID, 'policy_sha256': POLICY_SHA256,
            'scope': 'software_research_only', 'input_sha256': digest, **output,
            'balance_residual': residuals, 'balance_budget': budgets}
