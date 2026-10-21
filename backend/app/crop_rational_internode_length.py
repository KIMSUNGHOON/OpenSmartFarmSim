"""Canonical synthetic internode length with exact rational emergence offsets."""
from copy import deepcopy
from fractions import Fraction
from hashlib import sha256
import json
from math import isclose, isfinite
import re

from .crop_internode_length import InternodeLengthHold, POINT_VERSION, calculate_internode_length_point
from .crop_internode_length_change import InternodeLengthChangeHold, normalize_internode_curve
from .crop_morphology_thermal_clock import thermal_age_fraction
from .crop_rational_morphology_clock import (
    MODEL_VERSION as CLOCK_VERSION, RationalMorphologyClockHold,
    advance_rational_internode_thermal_clock, normalize_rational_internode_clock_state,
)


MODEL_VERSION = 'internode-rational-length-state-research-v1'
STATE_KEYS = {'model_version', 'clock_state', 'curve', 'curve_sha256', 'length', 'anchor'}


class RationalInternodeLengthHold(ValueError):
    pass


def _need(condition, reason):
    if not condition:
        raise RationalInternodeLengthHold(reason)


def _identifier(value):
    _need(type(value) is str and re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9_.:/-]{0,199}', value),
          'INPUT_HOLD: bounded ASCII input ID required')


def _digest(value):
    return sha256(json.dumps(value, sort_keys=True, separators=(',', ':'), allow_nan=False).encode()).hexdigest()


def _quantity(q):
    _need(type(q) is dict and set(q) == {'value', 'unit'}, 'INPUT_HOLD: closed length quantity required')
    _need(q['unit'] == 'm', 'UNIT_HOLD: length in metres required')
    _need(type(q['value']) in (int, float), 'INPUT_HOLD: numeric length required')
    try:
        value = float(q['value'])
    except OverflowError:
        raise RationalInternodeLengthHold('NUMERIC_HOLD: length overflow') from None
    _need(isfinite(value) and value > 0, 'INITIAL_LENGTH_HOLD: finite positive length required')
    return {'value': value, 'unit': 'm'}


def _normalized(clock, curve):
    try:
        normalized_clock = normalize_rational_internode_clock_state(state=clock)
        normalized_curve = normalize_internode_curve(curve=curve)
    except (RationalMorphologyClockHold, InternodeLengthChangeHold) as exc:
        raise RationalInternodeLengthHold(str(exc)) from None
    return normalized_clock, normalized_curve['curve'], normalized_curve['curve_sha256']


def _point(clock, curve):
    try:
        return calculate_internode_length_point(inputs={'input_id': 'rational-state-canonical-point',
            'origin': 'synthetic', 'thermal_age_basis': 'since_internode_emergence',
            'age_exact': clock['age_exact'], 'curve': curve})
    except InternodeLengthHold as exc:
        raise RationalInternodeLengthHold(str(exc)) from None


def _seconds(record):
    return Fraction(int(record['numerator']), int(record['denominator']))


def _envelope(state, identity, point, clock_receipt=None):
    result = {'model_version': MODEL_VERSION, 'scope': 'software_research_only',
        'claim_scope': 'synthetic_crop_math_only', 'gates': 'not_assessed',
        'input_sha256': _digest({'model_version': MODEL_VERSION, **identity}), 'state': state,
        'point_model_version': POINT_VERSION, 'point_input_sha256': point['input_sha256'],
        'clock_model_version': CLOCK_VERSION}
    if clock_receipt is not None:
        result['clock_input_sha256'] = clock_receipt['input_sha256']
    return result


def initialize_rational_internode_length(*, inputs):
    _need(type(inputs) is dict and set(inputs) == {'input_id', 'clock_state', 'curve', 'initial_length'},
          'INPUT_HOLD: closed rational initialization required')
    _identifier(inputs['input_id'])
    clock, curve, curve_hash = _normalized(inputs['clock_state'], inputs['curve'])
    requested, point = _quantity(inputs['initial_length']), _point(clock, curve)
    canonical = point['length']
    _need(isclose(requested['value'], canonical['value'], rel_tol=1e-12, abs_tol=0),
          'INITIAL_LENGTH_HOLD: explicit length does not match canonical curve')
    state = {'model_version': MODEL_VERSION, 'clock_state': clock, 'curve': curve,
        'curve_sha256': curve_hash, 'length': canonical, 'anchor': {'clock_state': deepcopy(clock),
            'curve_sha256': curve_hash, 'requested_length': requested, 'canonical_length': dict(canonical)}}
    return _envelope(state, {'operation': 'initialize', 'input_id': inputs['input_id'], 'state': state}, point)


def normalize_rational_internode_length_state(*, state):
    _need(type(state) is dict and set(state) == STATE_KEYS and state['model_version'] == MODEL_VERSION,
          'STATE_HOLD: closed supported rational length state required')
    clock, curve, curve_hash = _normalized(state['clock_state'], state['curve'])
    _need(state['curve_sha256'] == curve_hash, 'STATE_HOLD: curve identity mismatch')
    canonical = _point(clock, curve)['length']
    _need(_quantity(state['length']) == canonical, 'STATE_HOLD: current length is not canonical')
    anchor = state['anchor']
    _need(type(anchor) is dict and set(anchor) == {
        'clock_state', 'curve_sha256', 'requested_length', 'canonical_length'}, 'STATE_HOLD: closed initial receipt required')
    initial, _, _ = _normalized(anchor['clock_state'], curve)
    constants = set(clock) - {'at_elapsed_seconds_exact', 'age_exact'}
    _need(all(initial[key] == clock[key] for key in constants), 'STATE_HOLD: clock identity changed')
    initial_at, current_at = (_seconds(c['at_elapsed_seconds_exact']) for c in (initial, clock))
    initial_age, current_age = (thermal_age_fraction(c['age_exact']) for c in (initial, clock))
    _need(initial_at <= current_at and initial_age <= current_age
          and (initial_at != current_at or initial_age == current_age), 'STATE_HOLD: initial receipt after current clock')
    original = _point(initial, curve)['length']; requested = _quantity(anchor['requested_length'])
    _need(anchor['curve_sha256'] == curve_hash and _quantity(anchor['canonical_length']) == original
          and isclose(requested['value'], original['value'], rel_tol=1e-12, abs_tol=0), 'STATE_HOLD: initial receipt mismatch')
    return {'model_version': MODEL_VERSION, 'clock_state': clock, 'curve': curve,
        'curve_sha256': curve_hash, 'length': canonical, 'anchor': {'clock_state': initial,
            'curve_sha256': curve_hash, 'requested_length': requested, 'canonical_length': original}}


def advance_rational_internode_length(*, inputs):
    _need(type(inputs) is dict and set(inputs) == {'input_id', 'state', 'segments'}, 'INPUT_HOLD: closed rational advance required')
    _identifier(inputs['input_id']); state = normalize_rational_internode_length_state(state=inputs['state'])
    try:
        clock = advance_rational_internode_thermal_clock(inputs={
            'input_id': inputs['input_id'], 'state': state['clock_state'], 'segments': inputs['segments']})
    except RationalMorphologyClockHold as exc:
        raise RationalInternodeLengthHold(str(exc)) from None
    point = _point(clock['checkpoint'], state['curve'])
    return _envelope({**state, 'clock_state': clock['checkpoint'], 'length': point['length']}, {
        'operation': 'advance', 'input_id': inputs['input_id'], 'state': state,
        'clock_input_sha256': clock['input_sha256']}, point, clock)
