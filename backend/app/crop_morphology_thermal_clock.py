"""Synthetic constant-air-temperature extension of Smolenova et al. (2025).

DOI 10.1093/insilicoplants/diaf022, sections 2.1.3/2.3; article CC BY 4.0.
UTC intervals, rational carry and below-base holds are this research policy:
contracts/crop-morphology-thermal-clock-v1.md. No author code is reused.
"""
from datetime import datetime
from fractions import Fraction
from hashlib import sha256
import json
from math import isfinite
import re


MODEL_VERSION = 'internode-air-thermal-clock-research-v1'
STATE_KEYS = {'origin', 'age_basis', 'temperature_basis', 'internode_id',
              'emerged_at', 'at', 'base_temperature', 'age_exact'}


class MorphologyClockHold(ValueError):
    pass


def _need(condition, reason):
    if not condition:
        raise MorphologyClockHold(reason)


def _identifier(value):
    return type(value) is str and re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9_.:/-]{0,199}', value)


def _utc(value):
    _need(type(value) is str and re.fullmatch(
        r'[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}Z', value),
        'TIME_HOLD: whole-second UTC required')
    try:
        return datetime.fromisoformat(value)
    except ValueError:
        raise MorphologyClockHold('TIME_HOLD: invalid UTC date') from None


def _temperature(quantity):
    _need(type(quantity) is dict and set(quantity) == {'value', 'unit'},
        'INPUT_HOLD: closed temperature quantity required')
    _need(quantity['unit'] == 'degC', 'UNIT_HOLD: Celsius required')
    _need(type(quantity['value']) in (int, float), 'INPUT_HOLD: numeric temperature required')
    try:
        value = float(quantity['value'])
    except OverflowError:
        raise MorphologyClockHold('NUMERIC_HOLD: temperature overflow') from None
    _need(isfinite(value), 'NUMERIC_HOLD: finite temperature required')
    return value


def _age(record):
    _need(type(record) is dict and set(record) == {'numerator', 'denominator', 'unit'},
        'INPUT_HOLD: exact age quantity required')
    _need(record['unit'] == 'degC_day', 'UNIT_HOLD: degree-day age required')
    for key in ('numerator', 'denominator'):
        value = record[key]
        _need(type(value) is str, 'INPUT_HOLD: decimal integer string required')
        _need(1 <= len(value) <= 1024, 'CAPACITY_HOLD: exact age digit limit')
        _need(re.fullmatch(r'0|[1-9][0-9]*', value), 'INPUT_HOLD: canonical nonnegative integer required')
    _need(record['denominator'] != '0', 'INPUT_HOLD: positive denominator required')
    age = Fraction(int(record['numerator']), int(record['denominator']))
    _need(str(age.numerator) == record['numerator'] and str(age.denominator) == record['denominator'],
        'INPUT_HOLD: reduced exact age required')
    return age


def normalize_internode_clock_state(*, state):
    _need(type(state) is dict and set(state) == STATE_KEYS, 'INPUT_HOLD: closed clock state required')
    _need(state['origin'] == 'synthetic' and state['age_basis'] == 'since_internode_emergence'
        and state['temperature_basis'] == 'indoor_air_piecewise_constant',
        'INPUT_HOLD: explicit synthetic internode air-temperature clock required')
    _need(_identifier(state['internode_id']), 'INPUT_HOLD: bounded internode ID required')
    emerged, at = _utc(state['emerged_at']), _utc(state['at'])
    _need(emerged <= at, 'TIME_HOLD: emergence after checkpoint')
    age = _age(state['age_exact'])
    _need(at != emerged or age == 0, 'INPUT_HOLD: nonzero age at emergence')
    base = _temperature(state['base_temperature'])
    return {**state, 'base_temperature': {'value': base, 'unit': 'degC'},
            'age_exact': dict(state['age_exact'])}


def advance_internode_thermal_clock(*, inputs):
    _need(type(inputs) is dict and set(inputs) == {'input_id', 'state', 'segments'},
        'INPUT_HOLD: closed clock input required')
    _need(_identifier(inputs['input_id']), 'INPUT_HOLD: bounded input ID required')
    state = normalize_internode_clock_state(state=inputs['state'])
    age, at = _age(state['age_exact']), _utc(state['at'])
    base = state['base_temperature']['value']
    segments = inputs['segments']
    _need(type(segments) is list and 1 <= len(segments) <= 512, 'CAPACITY_HOLD: segment count')
    normalized_segments = []
    for segment in segments:
        _need(type(segment) is dict and set(segment) == {'start_utc', 'end_utc', 'air_temperature'},
            'INPUT_HOLD: closed constant-temperature segment required')
        start, end = _utc(segment['start_utc']), _utc(segment['end_utc'])
        _need(start == at and end > start, 'TIME_HOLD: contiguous forward interval required')
        temperature = _temperature(segment['air_temperature'])
        _need(temperature >= base, 'TEMPERATURE_DOMAIN_HOLD: air temperature below explicit base')
        duration = end - start
        seconds = duration.days * 86400 + duration.seconds
        age += (Fraction.from_float(temperature) - Fraction.from_float(base)) * seconds / 86400
        at = end
        normalized_segments.append({**segment, 'air_temperature': {'value': temperature, 'unit': 'degC'}})
    exact = {'numerator': str(age.numerator), 'denominator': str(age.denominator), 'unit': 'degC_day'}
    _need(max(len(exact['numerator']), len(exact['denominator'])) <= 1024, 'CAPACITY_HOLD: checkpoint age digits')
    try:
        value = float(age)
    except OverflowError:
        raise MorphologyClockHold('NUMERIC_HOLD: age overflow') from None
    _need(isfinite(value) and (age == 0 or value > 0), 'NUMERIC_HOLD: positive age not representable')
    identity = json.dumps({'model_version': MODEL_VERSION, 'inputs': {
        'input_id': inputs['input_id'], 'state': state, 'segments': normalized_segments}},
        sort_keys=True, separators=(',', ':'), allow_nan=False).encode()
    checkpoint = {**state, 'at': segments[-1]['end_utc'], 'age_exact': exact}
    return {'model_version': MODEL_VERSION, 'scope': 'software_research_only',
            'claim_scope': 'synthetic_crop_math_only', 'gates': 'not_assessed',
            'input_sha256': sha256(identity).hexdigest(), 'checkpoint': checkpoint,
            'thermal_age': {'value': value, 'unit': 'degC_day'}}
