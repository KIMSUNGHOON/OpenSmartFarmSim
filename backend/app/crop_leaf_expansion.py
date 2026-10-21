"""Independent synthetic logistic area-rate calculation.

Source definitions, dimensional interpretation and unresolved initial area:
contracts/crop-leaf-expansion-rate-v1.md. No author code or crop coefficients
are reused. This point rate does not supply an area or a leaf geometry.
"""
from hashlib import sha256
import json
from math import exp, isfinite, log, log1p
import re


MODEL_VERSION = 'leaf-logistic-thermal-area-rate-research-v1'
UNITS = {'thermal_age': 'degC_day', 'maximum_area': 'm2',
         'steepness': '1/degC_day', 'inflection_age': 'degC_day'}


class LeafExpansionHold(ValueError):
    pass


def _need(condition, reason):
    if not condition:
        raise LeafExpansionHold(reason)


def calculate_leaf_expansion_rate(*, inputs):
    _need(type(inputs) is dict and set(inputs) == {
        'input_id', 'origin', 'thermal_age_basis', 'values'}, 'INPUT_HOLD: closed input required')
    _need(type(inputs['input_id']) is str and re.fullmatch(
        r'[A-Za-z0-9][A-Za-z0-9_.:/-]{0,199}', inputs['input_id']) is not None,
        'INPUT_HOLD: bounded ASCII input ID required')
    _need(inputs['origin'] == 'synthetic' and inputs['thermal_age_basis'] == 'since_leaf_emergence',
        'INPUT_HOLD: explicit synthetic leaf thermal age required')
    supplied = inputs['values']
    _need(type(supplied) is dict and set(supplied) == set(UNITS),
        'INPUT_HOLD: explicit quantities required')
    values = {}
    for name, unit in UNITS.items():
        quantity = supplied[name]
        _need(type(quantity) is dict and set(quantity) == {'value', 'unit'},
            'INPUT_HOLD: closed quantity required')
        _need(quantity['unit'] == unit, 'UNIT_HOLD: ' + name)
        _need(type(quantity['value']) in (int, float), 'INPUT_HOLD: numeric value required')
        try:
            value = float(quantity['value'])
        except OverflowError:
            raise LeafExpansionHold('NUMERIC_HOLD: input overflow') from None
        _need(isfinite(value) and value >= 0, 'INPUT_HOLD: finite nonnegative quantity required')
        _need(name not in ('steepness', 'maximum_area') or value > 0,
            'INPUT_HOLD: positive curve parameters required')
        values[name] = value
    z = values['steepness'] * (values['thermal_age'] - values['inflection_age'])
    _need(isfinite(z), 'NUMERIC_HOLD: exponent overflow')
    magnitude = abs(z)
    log_rate = (log(values['steepness']) + log(values['maximum_area']) - magnitude
                - 2 * log1p(exp(-magnitude)))
    try:
        rate = exp(log_rate)
    except OverflowError:
        raise LeafExpansionHold('NUMERIC_HOLD: rate overflow') from None
    _need(isfinite(rate) and rate > 0, 'NUMERIC_HOLD: positive rate not representable')
    normalized = {**inputs, 'values': {
        name: {'value': value, 'unit': UNITS[name]} for name, value in values.items()}}
    identity = json.dumps({'model_version': MODEL_VERSION, 'inputs': normalized},
        sort_keys=True, separators=(',', ':'), allow_nan=False).encode()
    return {'model_version': MODEL_VERSION, 'scope': 'software_research_only',
            'claim_scope': 'synthetic_crop_math_only', 'gates': 'not_assessed',
            'input_sha256': sha256(identity).hexdigest(),
            'expansion_per_thermal_age': {'value': rate, 'unit': 'm2/degC_day'}}
