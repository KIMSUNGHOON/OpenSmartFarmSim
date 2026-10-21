"""Exact synthetic organ clock with rational seconds since an explicit UTC origin."""
from fractions import Fraction
from hashlib import sha256
import json
from math import isfinite
import re

from .crop_morphology_thermal_clock import MorphologyClockHold, parse_whole_second_utc, thermal_age_fraction


MODEL_VERSION = 'internode-rational-air-thermal-clock-research-v1'
STATE_KEYS = {'origin', 'age_basis', 'temperature_basis', 'internode_id', 'time_origin_utc',
              'emerged_elapsed_seconds_exact', 'at_elapsed_seconds_exact', 'base_temperature', 'age_exact'}


class RationalMorphologyClockHold(ValueError):
    pass


def _need(condition, reason):
    if not condition:
        raise RationalMorphologyClockHold(reason)


def _identifier(value):
    _need(type(value) is str and re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9_.:/-]{0,199}', value),
          'INPUT_HOLD: bounded ASCII identifier required')


def _seconds(record):
    _need(type(record) is dict and set(record) == {'numerator', 'denominator', 'unit'}, 'TIME_HOLD: closed exact seconds required')
    _need(record['unit'] == 's', 'UNIT_HOLD: elapsed seconds required')
    for key in ('numerator', 'denominator'):
        _need(type(record[key]) is str and 1 <= len(record[key]) <= 1024, 'CAPACITY_HOLD: bounded integer string required')
        _need(re.fullmatch(r'0|[1-9][0-9]*', record[key]), 'TIME_HOLD: canonical nonnegative integer required')
    _need(record['denominator'] != '0', 'TIME_HOLD: positive denominator required')
    value = Fraction(int(record['numerator']), int(record['denominator']))
    _need(str(value.numerator) == record['numerator'] and str(value.denominator) == record['denominator'],
          'TIME_HOLD: reduced exact seconds required')
    return value


def _temperature(q):
    _need(type(q) is dict and set(q) == {'value', 'unit'}, 'INPUT_HOLD: closed temperature required')
    _need(q['unit'] == 'degC', 'UNIT_HOLD: Celsius required')
    _need(type(q['value']) in (int, float), 'INPUT_HOLD: numeric temperature required')
    try:
        value = float(q['value'])
    except OverflowError:
        raise RationalMorphologyClockHold('NUMERIC_HOLD: temperature overflow') from None
    _need(isfinite(value), 'NUMERIC_HOLD: finite temperature required')
    return value


def _age_record(age):
    n, d = str(age.numerator), str(age.denominator)
    _need(len(n) <= 1024 and len(d) <= 1024, 'CAPACITY_HOLD: resulting exact age digit limit')
    return {'numerator': n, 'denominator': d, 'unit': 'degC_day'}


def normalize_rational_internode_clock_state(*, state):
    _need(type(state) is dict and set(state) == STATE_KEYS, 'INPUT_HOLD: closed rational organ clock required')
    _need(state['origin'] == 'synthetic' and state['age_basis'] == 'since_internode_emergence'
          and state['temperature_basis'] == 'indoor_air_piecewise_constant', 'INPUT_HOLD: explicit synthetic air clock required')
    _identifier(state['internode_id'])
    birth, at = (_seconds(state[k]) for k in ('emerged_elapsed_seconds_exact', 'at_elapsed_seconds_exact'))
    try:
        parse_whole_second_utc(state['time_origin_utc'])
        age = thermal_age_fraction(state['age_exact'])
    except MorphologyClockHold as exc:
        raise RationalMorphologyClockHold(str(exc)) from None
    _need(at >= birth and (at != birth or age == 0), 'TIME_HOLD: birth/checkpoint age mismatch')
    base = _temperature(state['base_temperature'])
    return {**state, 'emerged_elapsed_seconds_exact': dict(state['emerged_elapsed_seconds_exact']),
            'at_elapsed_seconds_exact': dict(state['at_elapsed_seconds_exact']),
            'age_exact': dict(state['age_exact']), 'base_temperature': {'value': base, 'unit': 'degC'}}


def advance_rational_internode_thermal_clock(*, inputs):
    _need(type(inputs) is dict and set(inputs) == {'input_id', 'state', 'segments'}, 'INPUT_HOLD: closed rational clock input required')
    _identifier(inputs['input_id']); state = normalize_rational_internode_clock_state(state=inputs['state'])
    segments = inputs['segments']
    _need(type(segments) is list and 1 <= len(segments) <= 512, 'CAPACITY_HOLD: bounded nonempty forcing required')
    at = _seconds(state['at_elapsed_seconds_exact']); age = thermal_age_fraction(state['age_exact'])
    base = Fraction.from_float(state['base_temperature']['value']); normalized = []
    for segment in segments:
        _need(type(segment) is dict and set(segment) == {
            'start_elapsed_seconds_exact', 'end_elapsed_seconds_exact', 'air_temperature'}, 'INPUT_HOLD: closed rational segment required')
        start, end = (_seconds(segment[k]) for k in ('start_elapsed_seconds_exact', 'end_elapsed_seconds_exact'))
        _need(start == at and end > start, 'TIME_HOLD: contiguous forward rational forcing required')
        temperature = _temperature(segment['air_temperature']); difference = Fraction.from_float(temperature) - base
        _need(difference >= 0, 'THERMAL_DOMAIN_HOLD: air below base is unsupported')
        age += difference * (end - start) / 86400
        _age_record(age)
        at = end
        normalized.append({'start_elapsed_seconds_exact': dict(segment['start_elapsed_seconds_exact']),
            'end_elapsed_seconds_exact': dict(segment['end_elapsed_seconds_exact']),
            'air_temperature': {'value': temperature, 'unit': 'degC'}})
    identity = {'model_version': MODEL_VERSION, 'inputs': {
        'input_id': inputs['input_id'], 'state': state, 'segments': normalized}}
    raw = json.dumps(identity, sort_keys=True, separators=(',', ':'), allow_nan=False).encode()
    return {'model_version': MODEL_VERSION, 'scope': 'software_research_only', 'claim_scope': 'synthetic_crop_math_only',
            'gates': 'not_assessed', 'input_sha256': sha256(raw).hexdigest(), 'checkpoint': {**state,
                'at_elapsed_seconds_exact': dict(normalized[-1]['end_elapsed_seconds_exact']), 'age_exact': _age_record(age)}}
