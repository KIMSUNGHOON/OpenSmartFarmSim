"""Explicit synthetic canonical area and checked initial receipt.

The declared normalization is a research policy, not a measured initial
leaf area or the author's initialization. See crop-leaf-area-state-v1.md.
"""
from fractions import Fraction
from hashlib import sha256
import json
from math import exp, isclose, isfinite, log, log1p
import re
from sys import float_info

from .crop_leaf_area_change import LeafAreaChangeHold, calculate_leaf_area_change, normalize_leaf_area_curve
from .crop_morphology_thermal_clock import MorphologyClockHold, thermal_age_fraction


MODEL_VERSION = 'leaf-logistic-canonical-area-state-research-v1'
POINT_VERSION = 'leaf-logistic-canonical-area-point-research-v1'
NORMALIZATION = 'zero_lower_asymptote_sigmoid_v1'
POINT_KEYS = {'input_id','origin','thermal_age_basis','normalization','age_exact','curve'}
STATE_KEYS = {'model_version','origin','thermal_age_basis','normalization','leaf_id','curve',
              'curve_sha256','age_exact','area','anchor'}


class LeafAreaHold(ValueError):
    pass


def _need(condition, reason):
    if not condition:
        raise LeafAreaHold(reason)


def _identifier(value):
    _need(type(value) is str and re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9_.:/-]{0,199}', value),
          'INPUT_HOLD: bounded ASCII identifier required')


def _digest(value):
    return sha256(json.dumps(value, sort_keys=True, separators=(',', ':'), allow_nan=False).encode()).hexdigest()


def _quantity(quantity):
    _need(type(quantity) is dict and set(quantity) == {'value','unit'}, 'INPUT_HOLD: closed area quantity required')
    _need(quantity['unit'] == 'm2', 'UNIT_HOLD: area in square metres required')
    _need(type(quantity['value']) in (int,float), 'INPUT_HOLD: numeric area required')
    try:
        value = float(quantity['value'])
    except OverflowError:
        raise LeafAreaHold('NUMERIC_HOLD: area overflow') from None
    _need(isfinite(value) and value > 0, 'AREA_HOLD: finite positive area required')
    return {'value': value, 'unit': 'm2'}


def _age(value):
    try:
        return thermal_age_fraction(value)
    except MorphologyClockHold as exc:
        raise LeafAreaHold(str(exc)) from None


def _parameters(inputs):
    _identifier(inputs['input_id'])
    _need(inputs['origin'] == 'synthetic' and inputs['thermal_age_basis'] == 'since_leaf_emergence'
          and inputs['normalization'] == NORMALIZATION, 'INPUT_HOLD: explicit synthetic leaf normalization required')
    try:
        curve = normalize_leaf_area_curve(curve=inputs['curve'])
    except LeafAreaChangeHold as exc:
        raise LeafAreaHold(str(exc)) from None
    return curve['curve'], curve['curve_sha256'], _age(inputs['age_exact'])


def _area_at(age, curve):
    maximum, k, midpoint = (curve['values'][key]['value'] for key in ('maximum_area','steepness','inflection_age'))
    try:
        x = float(Fraction.from_float(k) * (age-Fraction.from_float(midpoint)))
    except OverflowError:
        raise LeafAreaHold('NUMERIC_HOLD: point exponent overflow') from None
    _need(isfinite(x), 'NUMERIC_HOLD: finite point exponent required')
    if x >= 0:
        area = maximum / (1+exp(-x))
    else:
        q = exp(x)
        area = maximum*q/(1+q) if q >= float_info.min else exp(log(maximum)+x-log1p(q))
    _need(isfinite(area) and float_info.min <= area <= maximum, 'NUMERIC_HOLD: normal bounded area required')
    return {'value': area, 'unit': 'm2'}


def calculate_leaf_area_point(*, inputs):
    _need(type(inputs) is dict and set(inputs) == POINT_KEYS, 'INPUT_HOLD: closed leaf area point required')
    curve, curve_hash, age = _parameters(inputs)
    return {'model_version': POINT_VERSION, 'scope': 'software_research_only',
        'claim_scope': 'synthetic_crop_math_only', 'gates': 'not_assessed',
        'input_sha256': _digest({'model_version': POINT_VERSION, 'inputs': {**inputs,'curve':curve}}),
        'curve_sha256': curve_hash, 'normalization': NORMALIZATION,
        'age_exact': dict(inputs['age_exact']), 'area': _area_at(age,curve)}


def _envelope(state, identity):
    return {'model_version': MODEL_VERSION, 'scope': 'software_research_only',
        'claim_scope': 'synthetic_crop_math_only', 'gates': 'not_assessed',
        'input_sha256': _digest({'model_version': MODEL_VERSION, **identity}), 'state': state}


def initialize_leaf_area(*, inputs):
    _need(type(inputs) is dict and set(inputs) == POINT_KEYS | {'leaf_id','initial_area'},
          'INPUT_HOLD: explicit closed leaf initialization required')
    _identifier(inputs['leaf_id'])
    curve, curve_hash, age = _parameters(inputs)
    requested, canonical = _quantity(inputs['initial_area']), _area_at(age,curve)
    _need(isclose(requested['value'], canonical['value'], rel_tol=1e-12, abs_tol=0),
          'INITIAL_AREA_HOLD: explicit area does not match declared canonical curve')
    anchor = {'leaf_id': inputs['leaf_id'], 'age_exact': dict(inputs['age_exact']), 'curve_sha256': curve_hash,
              'requested_area': requested, 'canonical_area': dict(canonical)}
    state = {'model_version': MODEL_VERSION, 'origin': 'synthetic', 'thermal_age_basis': 'since_leaf_emergence',
        'normalization': NORMALIZATION, 'leaf_id': inputs['leaf_id'], 'curve': curve, 'curve_sha256': curve_hash,
        'age_exact': dict(inputs['age_exact']), 'area': canonical, 'anchor': anchor}
    return _envelope(state, {'operation':'initialize','input_id':inputs['input_id'],'state':state})


def normalize_leaf_area_state(*, state):
    _need(type(state) is dict and set(state) == STATE_KEYS and state['model_version'] == MODEL_VERSION,
          'STATE_HOLD: closed supported area state required')
    _identifier(state['leaf_id'])
    curve, curve_hash, age = _parameters({**state,'input_id':state['leaf_id']})
    _need(state['curve_sha256'] == curve_hash, 'STATE_HOLD: curve identity mismatch')
    canonical = _area_at(age,curve)
    _need(_quantity(state['area']) == canonical, 'STATE_HOLD: current area is not canonical')
    anchor = state['anchor']
    _need(type(anchor) is dict and set(anchor) == {'leaf_id','age_exact','curve_sha256','requested_area','canonical_area'},
          'STATE_HOLD: closed initial area receipt required')
    initial_age = _age(anchor['age_exact'])
    _need(anchor['leaf_id'] == state['leaf_id'] and initial_age <= age and anchor['curve_sha256'] == curve_hash,
          'STATE_HOLD: initial receipt identity or age mismatch')
    initial_area, requested = _area_at(initial_age,curve), _quantity(anchor['requested_area'])
    _need(_quantity(anchor['canonical_area']) == initial_area
          and isclose(requested['value'],initial_area['value'],rel_tol=1e-12,abs_tol=0),
          'STATE_HOLD: initial area receipt mismatch')
    return {'model_version':MODEL_VERSION,'origin':'synthetic','thermal_age_basis':'since_leaf_emergence',
        'normalization':NORMALIZATION,'leaf_id':state['leaf_id'],'curve':curve,'curve_sha256':curve_hash,
        'age_exact':dict(state['age_exact']),'area':canonical,'anchor':{
            'leaf_id':state['leaf_id'],'age_exact':dict(anchor['age_exact']),'curve_sha256':curve_hash,
            'requested_area':requested,'canonical_area':initial_area}}


def advance_leaf_area(*, inputs):
    _need(type(inputs) is dict and set(inputs) == {'input_id','state','end_age_exact'},
          'INPUT_HOLD: closed leaf area advance required')
    _identifier(inputs['input_id'])
    state = normalize_leaf_area_state(state=inputs['state'])
    try:
        change = calculate_leaf_area_change(inputs={'input_id':inputs['input_id'], 'curve':state['curve'],
            'start_age_exact':state['age_exact'], 'end_age_exact':inputs['end_age_exact']})
    except LeafAreaChangeHold as exc:
        raise LeafAreaHold(str(exc)) from None
    canonical = _area_at(_age(change['end_age_exact']),state['curve'])
    result = _envelope({**state,'age_exact':dict(change['end_age_exact']),'area':canonical},
        {'operation':'advance','state':state,'area_change_input_sha256':change['input_sha256']})
    result.update(area_change=change['area_change'],area_change_input_sha256=change['input_sha256'])
    return result
