"""Explicit synthetic initialization of Smolenova et al. (2025), Eq(4).

The canonical logistic length and checked anchor are our research policy,
not an observed cultivar initialization. See crop-internode-length-state-v1.md.
"""
from copy import deepcopy
from fractions import Fraction
from hashlib import sha256
import json
from math import exp, isclose, isfinite, log, log1p
import re
from sys import float_info

from .crop_internode_length_change import (
    InternodeLengthChangeHold, calculate_internode_length_change, normalize_internode_curve,
)
from .crop_morphology_thermal_clock import MorphologyClockHold, normalize_internode_clock_state


MODEL_VERSION = 'internode-logistic-length-state-research-v1'
STATE_KEYS = {'model_version', 'clock_state', 'curve', 'curve_sha256', 'length', 'anchor'}


class InternodeLengthHold(ValueError):
    pass


def _need(condition, reason):
    if not condition:
        raise InternodeLengthHold(reason)


def _identifier(value):
    _need(type(value) is str and re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9_.:/-]{0,199}', value),
          'INPUT_HOLD: bounded ASCII input ID required')


def _digest(value):
    return sha256(json.dumps(value, sort_keys=True, separators=(',', ':'), allow_nan=False).encode()).hexdigest()


def _quantity(quantity):
    _need(type(quantity) is dict and set(quantity) == {'value', 'unit'}, 'INPUT_HOLD: closed length quantity required')
    _need(quantity['unit'] == 'm', 'UNIT_HOLD: length in metres required')
    _need(type(quantity['value']) in (int, float), 'INPUT_HOLD: numeric length required')
    try:
        value = float(quantity['value'])
    except OverflowError:
        raise InternodeLengthHold('NUMERIC_HOLD: length overflow') from None
    _need(isfinite(value) and value > 0, 'INITIAL_LENGTH_HOLD: finite positive length required')
    return {'value': value, 'unit': 'm'}


def _age(clock):
    exact = clock['age_exact']
    return Fraction(int(exact['numerator']), int(exact['denominator']))


def _length(clock, curve):
    m, k, tm = (curve['values'][key]['value'] for key in ('maximum_length', 'steepness', 'inflection_age'))
    try:
        x = float(Fraction.from_float(k) * (_age(clock) - Fraction.from_float(tm)))
    except OverflowError:
        raise InternodeLengthHold('NUMERIC_HOLD: point exponent overflow') from None
    _need(isfinite(x), 'NUMERIC_HOLD: finite point exponent required')
    if x >= 0:
        length = m / (1 + exp(-x))
    else:
        q = exp(x)
        length = m * q / (1 + q) if q >= float_info.min else exp(log(m) + x - log1p(q))
    _need(isfinite(length) and float_info.min <= length <= m, 'NUMERIC_HOLD: normal bounded length required')
    return {'value': length, 'unit': 'm'}


def _normalized(clock, curve):
    try:
        normalized_clock = normalize_internode_clock_state(state=clock)
        normalized_curve = normalize_internode_curve(curve=curve)
    except (MorphologyClockHold, InternodeLengthChangeHold) as exc:
        raise InternodeLengthHold(str(exc)) from None
    return normalized_clock, normalized_curve['curve'], normalized_curve['curve_sha256']


def _envelope(state, identity):
    return {'model_version': MODEL_VERSION, 'scope': 'software_research_only',
            'claim_scope': 'synthetic_crop_math_only', 'gates': 'not_assessed',
            'input_sha256': _digest({'model_version': MODEL_VERSION, **identity}), 'state': state}


def initialize_internode_length(*, inputs):
    _need(type(inputs) is dict and set(inputs) == {'input_id', 'clock_state', 'curve', 'initial_length'},
          'INPUT_HOLD: closed initialization input required')
    _identifier(inputs['input_id'])
    clock, curve, curve_hash = _normalized(inputs['clock_state'], inputs['curve'])
    requested, canonical = _quantity(inputs['initial_length']), _length(clock, curve)
    _need(isclose(requested['value'], canonical['value'], rel_tol=1e-12, abs_tol=0),
          'INITIAL_LENGTH_HOLD: explicit length does not match canonical curve')
    anchor = {'clock_state': deepcopy(clock), 'curve_sha256': curve_hash,
              'requested_length': requested, 'canonical_length': dict(canonical)}
    state = {'model_version': MODEL_VERSION, 'clock_state': clock, 'curve': curve,
             'curve_sha256': curve_hash, 'length': canonical, 'anchor': anchor}
    return _envelope(state, {'operation': 'initialize', 'input_id': inputs['input_id'], 'state': state})


def normalize_internode_length_state(*, state):
    _need(type(state) is dict and set(state) == STATE_KEYS and state['model_version'] == MODEL_VERSION,
          'STATE_HOLD: closed supported length state required')
    clock, curve, curve_hash = _normalized(state['clock_state'], state['curve'])
    _need(state['curve_sha256'] == curve_hash, 'STATE_HOLD: curve identity mismatch')
    canonical = _length(clock, curve)
    _need(_quantity(state['length']) == canonical, 'STATE_HOLD: current length is not canonical')
    anchor = state['anchor']
    _need(type(anchor) is dict and set(anchor) == {
        'clock_state', 'curve_sha256', 'requested_length', 'canonical_length'}, 'STATE_HOLD: closed initial receipt required')
    initial, _, _ = _normalized(anchor['clock_state'], curve)
    constants = set(clock) - {'at', 'age_exact'}
    _need(all(initial[key] == clock[key] for key in constants), 'STATE_HOLD: clock identity changed')
    _need(initial['at'] <= clock['at'] and _age(initial) <= _age(clock)
          and (initial['at'] != clock['at'] or _age(initial) == _age(clock)), 'STATE_HOLD: initial receipt after current clock')
    original_length = _length(initial, curve)
    requested = _quantity(anchor['requested_length'])
    _need(anchor['curve_sha256'] == curve_hash and _quantity(anchor['canonical_length']) == original_length
          and isclose(requested['value'], original_length['value'], rel_tol=1e-12, abs_tol=0),
          'STATE_HOLD: initial receipt mismatch')
    return {'model_version': MODEL_VERSION, 'clock_state': clock, 'curve': curve,
            'curve_sha256': curve_hash, 'length': canonical, 'anchor': {
                'clock_state': initial, 'curve_sha256': curve_hash,
                'requested_length': requested, 'canonical_length': original_length}}


def advance_internode_length(*, inputs):
    _need(type(inputs) is dict and set(inputs) == {'input_id', 'state', 'segments'},
          'INPUT_HOLD: closed advance input required')
    _identifier(inputs['input_id'])
    state = normalize_internode_length_state(state=inputs['state'])
    try:
        change = calculate_internode_length_change(inputs={
            'input_id': inputs['input_id'], 'clock_state': state['clock_state'],
            'segments': inputs['segments'], 'curve': state['curve']})
    except InternodeLengthChangeHold as exc:
        raise InternodeLengthHold(str(exc)) from None
    canonical = _length(change['checkpoint'], state['curve'])
    result = _envelope({**state, 'clock_state': change['checkpoint'], 'length': canonical}, {
        'operation': 'advance', 'state': state, 'length_change_input_sha256': change['input_sha256']})
    result.update(length_change=change['length_change'], length_change_input_sha256=change['input_sha256'])
    return result
