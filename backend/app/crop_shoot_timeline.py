"""Synthetic exact event timing from constant indoor-air segments.

Our subdaily extension of Smolenova et al. (2025), article CC BY 4.0;
contracts/crop-shoot-air-event-timeline-v1.md records its research boundary.
"""
from copy import deepcopy
from datetime import timedelta
from fractions import Fraction
from hashlib import sha256
import json

from .crop_morphology_thermal_clock import (
    AIR_SEGMENT_VERSION, MorphologyClockHold, integrate_constant_air_segments, parse_whole_second_utc,
)
from .crop_phytomer_emergence import (
    MODEL_VERSION as EMERGENCE_VERSION, PhytomerEmergenceHold, advance_phytomer_emergence,
)


MODEL_VERSION = 'shoot-air-phytomer-timeline-research-v1'
STATE_KEYS = {'origin', 'age_basis', 'shoot_id', 'development_origin_id', 'schedule_id',
              'started_at', 'at', 'base_temperature', 'age_exact', 'next_threshold_exact',
              'phyllochron_exact', 'next_sequence'}


class ShootTimelineHold(ValueError):
    pass


def _need(condition, reason):
    if not condition:
        raise ShootTimelineHold(reason)


def _fraction(quantity):
    return Fraction(int(quantity['numerator']), int(quantity['denominator']))


def advance_shoot_event_timeline(*, inputs):
    _need(type(inputs) is dict and set(inputs) == {'input_id', 'state', 'segments'},
          'INPUT_HOLD: closed shoot timeline input required')
    state = inputs['state']
    _need(type(state) is dict and set(state) == STATE_KEYS, 'INPUT_HOLD: closed shoot timeline state required')
    _need(state['origin'] == 'synthetic' and state['age_basis'] == 'since_shoot_development_origin',
          'INPUT_HOLD: explicit synthetic shoot development clock required')
    try:
        origin, at = parse_whole_second_utc(state['started_at']), parse_whole_second_utc(state['at'])
        _need(origin <= at, 'TIME_HOLD: development origin after checkpoint')
        program = integrate_constant_air_segments(checkpoint_utc=state['at'], age_exact=state['age_exact'],
            base_temperature=state['base_temperature'], segments=inputs['segments'])
        _need(origin != at or program['intervals'][0]['age_start'] == 0, 'INPUT_HOLD: nonzero age at development origin')
        emergence = advance_phytomer_emergence(inputs={'input_id': inputs['input_id'], 'state': {
            **{key: state[key] for key in ('origin', 'age_basis', 'shoot_id', 'development_origin_id',
                                          'schedule_id', 'next_threshold_exact', 'phyllochron_exact', 'next_sequence')},
            'at_age_exact': state['age_exact']}, 'end_age_exact': program['age_exact']})
    except (MorphologyClockHold, PhytomerEmergenceHold) as exc:
        raise ShootTimelineHold(str(exc)) from None
    events, position = [], 0
    for event in emergence['events']:
        threshold = _fraction(event['thermal_age_exact'])
        while threshold > program['intervals'][position]['age_end']:
            position += 1
        interval = program['intervals'][position]
        _need(interval['age_start'] < threshold and interval['temperature_difference'] > 0,
              'TIME_HOLD: event does not belong to a warming interval')
        elapsed = parse_whole_second_utc(interval['start_utc']) - origin
        seconds = Fraction(elapsed.days * 86400 + elapsed.seconds) + (
            threshold - interval['age_start']) * 86400 / interval['temperature_difference']
        exact = {'numerator': str(seconds.numerator), 'denominator': str(seconds.denominator), 'unit': 's'}
        _need(max(len(exact['numerator']), len(exact['denominator'])) <= 1024,
              'CAPACITY_HOLD: exact event time digits')
        utc = None
        if seconds.denominator == 1:
            utc = (origin + timedelta(seconds=seconds.numerator)).isoformat().replace('+00:00', 'Z')
        events.append({**event, 'elapsed_seconds_exact': exact, 'utc_whole_second': utc})
    normalized = {**deepcopy(state), 'base_temperature': program['base_temperature']}
    phase = emergence['checkpoint']
    checkpoint = {**normalized, 'at': program['at'], 'age_exact': program['age_exact'],
                  'next_threshold_exact': phase['next_threshold_exact'], 'next_sequence': phase['next_sequence']}
    identity = json.dumps({'model_version': MODEL_VERSION, 'air_segment_version': AIR_SEGMENT_VERSION,
        'emergence_version': EMERGENCE_VERSION, 'inputs': {'input_id': inputs['input_id'],
        'state': normalized, 'segments': program['normalized_segments']}},
        sort_keys=True, separators=(',', ':'), allow_nan=False).encode()
    return {'model_version': MODEL_VERSION, 'scope': 'software_research_only',
            'claim_scope': 'synthetic_crop_math_only', 'gates': 'not_assessed',
            'input_sha256': sha256(identity).hexdigest(), 'time_origin_utc': state['started_at'],
            'events': events, 'checkpoint': checkpoint}
