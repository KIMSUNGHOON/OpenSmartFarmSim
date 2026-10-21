"""Synthetic thermal-threshold enumeration, based on Smolenova et al. (2025).

Article DOI 10.1093/insilicoplants/diaf022, sections 2.1.3/2.3, CC BY 4.0.
Explicit phase, exact events and endpoint policy are our research extension:
contracts/crop-phytomer-thermal-events-v1.md. No author code is reused.
"""
from fractions import Fraction
from hashlib import sha256
import json
import re


MODEL_VERSION = 'phytomer-thermal-events-research-v1'
STATE_KEYS = {'origin', 'age_basis', 'shoot_id', 'development_origin_id', 'schedule_id',
              'at_age_exact', 'next_threshold_exact', 'phyllochron_exact', 'next_sequence'}


class PhytomerEmergenceHold(ValueError):
    pass


def _need(condition, reason):
    if not condition:
        raise PhytomerEmergenceHold(reason)


def _identifier(value):
    _need(type(value) is str and re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9_.:/-]{0,199}', value),
          'INPUT_HOLD: bounded ASCII identifier required')


def _quantity(value):
    record = {'numerator': str(value.numerator), 'denominator': str(value.denominator), 'unit': 'degC_day'}
    _need(max(len(record['numerator']), len(record['denominator'])) <= 1024,
          'CAPACITY_HOLD: exact quantity digits')
    return record


def _rational(record):
    _need(type(record) is dict and set(record) == {'numerator', 'denominator', 'unit'},
          'INPUT_HOLD: closed exact thermal quantity required')
    _need(record['unit'] == 'degC_day', 'UNIT_HOLD: degree-day quantity required')
    for key in ('numerator', 'denominator'):
        text = record[key]
        _need(type(text) is str, 'INPUT_HOLD: integer string required')
        _need(1 <= len(text) <= 1024, 'CAPACITY_HOLD: exact quantity digits')
        _need(re.fullmatch(r'0|[1-9][0-9]*', text), 'INPUT_HOLD: canonical nonnegative integer required')
    _need(record['denominator'] != '0', 'INPUT_HOLD: positive denominator required')
    value = Fraction(int(record['numerator']), int(record['denominator']))
    _need(_quantity(value) == record, 'INPUT_HOLD: reduced exact quantity required')
    return value


def advance_phytomer_emergence(*, inputs):
    _need(type(inputs) is dict and set(inputs) == {'input_id', 'state', 'end_age_exact'},
          'INPUT_HOLD: closed emergence input required')
    _identifier(inputs['input_id'])
    state = inputs['state']
    _need(type(state) is dict and set(state) == STATE_KEYS, 'INPUT_HOLD: closed emergence state required')
    _need(state['origin'] == 'synthetic' and state['age_basis'] == 'since_shoot_development_origin',
          'INPUT_HOLD: explicit synthetic shoot development clock required')
    for key in ('shoot_id', 'development_origin_id', 'schedule_id'):
        _identifier(state[key])
    sequence = state['next_sequence']
    _need(type(sequence) is int and 0 <= sequence <= 2**31 - 1, 'INPUT_HOLD: bounded nonnegative sequence required')
    start, threshold, period, end = (_rational(record) for record in (
        state['at_age_exact'], state['next_threshold_exact'], state['phyllochron_exact'], inputs['end_age_exact']))
    _need(period > 0, 'INPUT_HOLD: positive phyllochron required')
    _need(threshold > start, 'PHASE_HOLD: next threshold must follow current age')
    _need(end >= start, 'PHASE_HOLD: development age cannot move backward')
    count = (end - threshold) // period + 1 if end >= threshold else 0
    _need(count <= 512 and sequence + count <= 2**31 - 1, 'CAPACITY_HOLD: event or sequence limit')
    next_threshold = _quantity(threshold + count * period)
    events = [{'sequence': sequence + index, 'thermal_age_exact': _quantity(threshold + index * period)}
              for index in range(count)]
    normalized_state = {**state, 'at_age_exact': _quantity(start),
                        'next_threshold_exact': _quantity(threshold), 'phyllochron_exact': _quantity(period)}
    identity = json.dumps({'model_version': MODEL_VERSION, 'inputs': {
        'input_id': inputs['input_id'], 'state': normalized_state, 'end_age_exact': _quantity(end)}},
        sort_keys=True, separators=(',', ':'), allow_nan=False).encode()
    return {'model_version': MODEL_VERSION, 'scope': 'software_research_only',
            'claim_scope': 'synthetic_crop_math_only', 'gates': 'not_assessed',
            'input_sha256': sha256(identity).hexdigest(), 'events': events,
            'checkpoint': {**normalized_state, 'at_age_exact': _quantity(end),
                           'next_threshold_exact': next_threshold, 'next_sequence': sequence + count}}
