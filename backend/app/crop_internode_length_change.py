"""Definite integral of Smolenova et al. (2025), Eq(4), article CC BY 4.0.

Independent equation implementation; no author repository code is reused.
Numeric and research boundaries: contracts/crop-internode-length-change-v1.md.
"""
from fractions import Fraction
from hashlib import sha256
import json
from math import exp, expm1, isfinite, log, log1p
from sys import float_info

from .crop_internode_elongation import (
    MODEL_VERSION as RATE_VERSION, InternodeElongationHold, calculate_internode_elongation,
)
from .crop_morphology_thermal_clock import (
    MODEL_VERSION as CLOCK_VERSION, MorphologyClockHold, advance_internode_thermal_clock,
)


MODEL_VERSION = 'internode-logistic-length-change-research-v1'


class InternodeLengthChangeHold(ValueError):
    pass


def _need(condition, reason):
    if not condition:
        raise InternodeLengthChangeHold(reason)


def _digest(value):
    return sha256(json.dumps(value, sort_keys=True, separators=(',', ':'),
                             allow_nan=False).encode()).hexdigest()


def _exact_age(state):
    age = state['age_exact']
    return Fraction(int(age['numerator']), int(age['denominator']))


def _sigmoid(x):
    if x >= 0:
        return 1 / (1 + exp(-x))
    q = exp(x)
    return q / (1 + q)


def _softplus(x):
    return max(x, 0) + log1p(exp(-abs(x)))


def calculate_internode_length_change(*, inputs):
    _need(type(inputs) is dict and set(inputs) == {
        'input_id', 'clock_state', 'segments', 'curve'}, 'INPUT_HOLD: closed length-change input required')
    curve = inputs['curve']
    _need(type(curve) is dict and set(curve) == {'profile_id', 'origin', 'values'},
          'INPUT_HOLD: closed curve required')
    supplied = curve['values']
    _need(type(supplied) is dict and set(supplied) == {
        'maximum_length', 'steepness', 'inflection_age'}, 'INPUT_HOLD: three curve parameters required')
    try:
        calculate_internode_elongation(inputs={
            'input_id': curve['profile_id'], 'origin': curve['origin'],
            'thermal_age_basis': 'since_internode_emergence',
            'values': {**supplied, 'thermal_age': supplied['inflection_age']}})
        clock = advance_internode_thermal_clock(inputs={
            'input_id': inputs['input_id'], 'state': inputs['clock_state'], 'segments': inputs['segments']})
    except (InternodeElongationHold, MorphologyClockHold) as exc:
        raise InternodeLengthChangeHold(str(exc)) from None
    values = {name: {'value': float(quantity['value']), 'unit': quantity['unit']}
              for name, quantity in supplied.items()}
    maximum, k, tm = (values[name]['value'] for name in ('maximum_length', 'steepness', 'inflection_age'))
    start, end = _exact_age(inputs['clock_state']), _exact_age(clock['checkpoint'])
    change = 0.0
    if end > start:
        exact_k, exact_tm = Fraction.from_float(k), Fraction.from_float(tm)
        try:
            x0, x1 = (float(exact_k * (age - exact_tm)) for age in (start, end))
        except OverflowError:
            raise InternodeLengthChangeHold('NUMERIC_HOLD: point exponent overflow') from None
        _need(isfinite(x0) and isfinite(x1), 'NUMERIC_HOLD: finite point exponents required')
        delta = exact_k * (end - start)
        try:
            d = float(delta)
        except OverflowError:
            d = float('inf')
        factor = -expm1(-d)
        right, left = _sigmoid(x1), _sigmoid(-x0)
        if min(right, left, factor) >= float_info.min:
            change = maximum * right * left * factor
        else:
            log_factor = log(factor) if factor > 0 else log(delta.numerator) - log(delta.denominator)
            try:
                change = exp(log(maximum) - _softplus(-x1) - _softplus(x0) + log_factor)
            except OverflowError:
                raise InternodeLengthChangeHold('NUMERIC_HOLD: length change overflow') from None
        _need(isfinite(change) and float_info.min <= change <= maximum,
              'NUMERIC_HOLD: normal bounded positive length change required')
    curve_hash = _digest({'rate_model_version': RATE_VERSION,
                         'curve': {**curve, 'values': values}})
    identity = {'model_version': MODEL_VERSION, 'clock_model_version': CLOCK_VERSION,
                'clock_input_sha256': clock['input_sha256'], 'curve_sha256': curve_hash}
    return {'model_version': MODEL_VERSION, 'scope': 'software_research_only',
            'claim_scope': 'synthetic_crop_math_only', 'gates': 'not_assessed',
            'input_sha256': _digest(identity), 'curve_sha256': curve_hash,
            'clock_input_sha256': clock['input_sha256'], 'checkpoint': clock['checkpoint'],
            'thermal_age': clock['thermal_age'], 'length_change': {'value': change, 'unit': 'm'}}
