"""Synthetic definite area increment, without an assumed initial leaf area.

contracts/crop-leaf-area-change-v1.md defines the independent integration
policy. The exact-age parser and stable algebra come from our own kernels.
"""
from fractions import Fraction
from hashlib import sha256
import json
from math import exp, expm1, isfinite, log, log1p
import re
from sys import float_info

from .crop_leaf_expansion import MODEL_VERSION as RATE_VERSION, LeafExpansionHold, calculate_leaf_expansion_rate
from .crop_morphology_thermal_clock import MorphologyClockHold, thermal_age_fraction


MODEL_VERSION = 'leaf-logistic-area-change-research-v1'


class LeafAreaChangeHold(ValueError):
    pass


def _need(condition, reason):
    if not condition:
        raise LeafAreaChangeHold(reason)


def _digest(value):
    return sha256(json.dumps(value, sort_keys=True, separators=(',', ':'), allow_nan=False).encode()).hexdigest()


def _sigmoid(x):
    if x >= 0:
        return 1 / (1 + exp(-x))
    q = exp(x)
    return q / (1 + q)


def _softplus(x):
    return max(x, 0) + log1p(exp(-abs(x)))


def normalize_leaf_area_curve(*, curve):
    _need(type(curve) is dict and set(curve) == {'profile_id', 'origin', 'values'},
          'INPUT_HOLD: closed curve required')
    supplied = curve['values']
    _need(type(supplied) is dict and set(supplied) == {'maximum_area', 'steepness', 'inflection_age'},
          'INPUT_HOLD: three explicit curve parameters required')
    try:
        calculate_leaf_expansion_rate(inputs={'input_id': curve['profile_id'], 'origin': curve['origin'],
            'thermal_age_basis': 'since_leaf_emergence',
            'values': {**supplied, 'thermal_age': supplied['inflection_age']}})
    except LeafExpansionHold as exc:
        raise LeafAreaChangeHold(str(exc)) from None
    normalized = {**curve, 'values': {name: {'value': float(q['value']), 'unit': q['unit']}
                                      for name, q in supplied.items()}}
    return {'curve': normalized, 'curve_sha256': _digest({'rate_model_version': RATE_VERSION, 'curve': normalized})}


def calculate_leaf_area_change(*, inputs):
    _need(type(inputs) is dict and set(inputs) == {'input_id', 'start_age_exact', 'end_age_exact', 'curve'},
          'INPUT_HOLD: closed area-change input required')
    _need(type(inputs['input_id']) is str and re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9_.:/-]{0,199}', inputs['input_id']),
          'INPUT_HOLD: bounded ASCII input ID required')
    normalized = normalize_leaf_area_curve(curve=inputs['curve'])
    try:
        start, end = (thermal_age_fraction(inputs[k]) for k in ('start_age_exact', 'end_age_exact'))
    except MorphologyClockHold as exc:
        raise LeafAreaChangeHold(str(exc)) from None
    _need(end >= start, 'TIME_HOLD: nondecreasing explicit thermal age required')
    values = normalized['curve']['values']
    maximum, k, midpoint = (values[name]['value'] for name in ('maximum_area', 'steepness', 'inflection_age'))
    change = 0.0
    if end > start:
        exact_k, exact_midpoint = Fraction.from_float(k), Fraction.from_float(midpoint)
        try:
            x0, x1 = (float(exact_k * (age-exact_midpoint)) for age in (start, end))
        except OverflowError:
            raise LeafAreaChangeHold('NUMERIC_HOLD: point exponent overflow') from None
        _need(isfinite(x0) and isfinite(x1), 'NUMERIC_HOLD: finite point exponents required')
        delta = exact_k * (end-start)
        try:
            d = float(delta)
        except OverflowError:
            d = float('inf')
        factor = -expm1(-d)
        right, left = _sigmoid(x1), _sigmoid(-x0)
        if min(right, left, factor) >= float_info.min:
            change = maximum * right * left * factor
        else:
            log_factor = log(factor) if factor > 0 else log(delta.numerator)-log(delta.denominator)
            try:
                change = exp(log(maximum)-_softplus(-x1)-_softplus(x0)+log_factor)
            except OverflowError:
                raise LeafAreaChangeHold('NUMERIC_HOLD: area change overflow') from None
        _need(isfinite(change) and float_info.min <= change <= maximum,
              'NUMERIC_HOLD: normal bounded positive area change required')
    identity = {'model_version': MODEL_VERSION, 'input_id': inputs['input_id'],
        'curve_sha256': normalized['curve_sha256'],
        **{k: dict(inputs[k]) for k in ('start_age_exact','end_age_exact')}}
    return {'model_version': MODEL_VERSION, 'scope': 'software_research_only',
        'claim_scope': 'synthetic_crop_math_only', 'gates': 'not_assessed',
        'input_sha256': _digest(identity), 'curve_sha256': normalized['curve_sha256'],
        **{k: dict(inputs[k]) for k in ('start_age_exact','end_age_exact')},
        'area_change': {'value': change, 'unit': 'm2'}}
