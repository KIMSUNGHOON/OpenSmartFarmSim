"""Bind exact synthetic shoot births to rational-time canonical internode states."""
from fractions import Fraction
from hashlib import sha256
import json
from math import isfinite

from .crop_morphology_thermal_clock import MorphologyClockHold, parse_whole_second_utc
from .crop_rational_internode_length import (
    MODEL_VERSION as LENGTH_VERSION, RationalInternodeLengthHold,
    advance_rational_internode_length, initialize_rational_internode_length,
)
from .crop_shoot_timeline import MODEL_VERSION as TIMELINE_VERSION, ShootTimelineHold, advance_shoot_event_timeline


MODEL_VERSION = 'shoot-rational-new-internodes-research-v1'
AIR_ADAPTER_VERSION = 'whole-second-utc-to-rational-air-segments-research-v1'


class RationalNewInternodeHold(ValueError):
    pass


def _need(condition, reason):
    if not condition:
        raise RationalNewInternodeHold(reason)


def _digest(value):
    return sha256(json.dumps(value, sort_keys=True, separators=(',', ':'), allow_nan=False).encode()).hexdigest()


def _fraction(record):
    return Fraction(int(record['numerator']), int(record['denominator']))


def _seconds_record(value):
    return {'numerator': str(value.numerator), 'denominator': str(value.denominator), 'unit': 's'}


def rational_air_segments_from_utc(*, time_origin_utc, segments):
    _need(type(segments) is list and 1 <= len(segments) <= 512, 'CAPACITY_HOLD: bounded nonempty UTC forcing required')
    try:
        origin = parse_whole_second_utc(time_origin_utc)
        previous = None; normalized = []
        for segment in segments:
            _need(type(segment) is dict and set(segment) == {'start_utc', 'end_utc', 'air_temperature'},
                  'INPUT_HOLD: closed UTC AIR segment required')
            start, end = (parse_whole_second_utc(segment[key]) for key in ('start_utc', 'end_utc'))
            _need(origin <= start < end and (previous is None or start == previous), 'TIME_HOLD: forward contiguous UTC forcing required')
            q = segment['air_temperature']
            _need(type(q) is dict and set(q) == {'value', 'unit'}, 'INPUT_HOLD: closed AIR temperature required')
            _need(q['unit'] == 'degC', 'UNIT_HOLD: AIR Celsius required')
            _need(type(q['value']) in (int, float), 'INPUT_HOLD: numeric AIR temperature required')
            try:
                temperature = float(q['value'])
            except OverflowError:
                raise RationalNewInternodeHold('NUMERIC_HOLD: AIR temperature overflow') from None
            _need(isfinite(temperature), 'NUMERIC_HOLD: finite AIR temperature required')
            offsets = [instant - origin for instant in (start, end)]
            normalized.append({'start_elapsed_seconds_exact': _seconds_record(Fraction(offsets[0].days * 86400 + offsets[0].seconds)),
                'end_elapsed_seconds_exact': _seconds_record(Fraction(offsets[1].days * 86400 + offsets[1].seconds)),
                'air_temperature': {'value': temperature, 'unit': 'degC'}})
            previous = end
    except MorphologyClockHold as exc:
        raise RationalNewInternodeHold(str(exc)) from None
    return normalized


def _clock(internode_id, origin, birth, base):
    return {'origin': 'synthetic', 'age_basis': 'since_internode_emergence',
        'temperature_basis': 'indoor_air_piecewise_constant', 'internode_id': internode_id,
        'time_origin_utc': origin, 'emerged_elapsed_seconds_exact': dict(birth),
        'at_elapsed_seconds_exact': dict(birth), 'base_temperature': dict(base),
        'age_exact': {'numerator': '0', 'denominator': '1', 'unit': 'degC_day'}}


def create_rational_internodes_from_shoot_events(*, inputs):
    _need(type(inputs) is dict and set(inputs) == {'input_id', 'timeline_state', 'segments', 'curve', 'initial_length'},
          'INPUT_HOLD: closed rational new-internode input required')
    try:
        timeline = advance_shoot_event_timeline(inputs={'input_id': inputs['input_id'],
            'state': inputs['timeline_state'], 'segments': inputs['segments']})
    except ShootTimelineHold as exc:
        raise RationalNewInternodeHold(str(exc)) from None
    current = timeline['checkpoint']; origin = current['started_at']
    forcing = rational_air_segments_from_utc(time_origin_utc=origin, segments=inputs['segments'])
    try:
        prototype = initialize_rational_internode_length(inputs={'input_id': 'synthetic-template-validation',
            'clock_state': _clock('synthetic-template-validation', origin, _seconds_record(Fraction(0)), current['base_temperature']),
            'curve': inputs['curve'], 'initial_length': inputs['initial_length']})
    except RationalInternodeLengthHold as exc:
        raise RationalNewInternodeHold(str(exc)) from None
    curve = prototype['state']['curve']; initial_length = prototype['state']['anchor']['requested_length']
    nodes = []
    for event in timeline['events']:
        birth = event['elapsed_seconds_exact']; birth_value = _fraction(birth)
        entity = {key: current[key] for key in ('shoot_id', 'development_origin_id', 'schedule_id', 'started_at')}
        entity.update(sequence=event['sequence'], birth_age_exact=event['thermal_age_exact'])
        internode_id = 'internode:' + _digest(entity)
        try:
            initial = initialize_rational_internode_length(inputs={
                'input_id': _digest({'input_id': inputs['input_id'], 'internode_id': internode_id, 'operation': 'initialize'}),
                'clock_state': _clock(internode_id, origin, birth, current['base_temperature']),
                'curve': curve, 'initial_length': initial_length})
            remaining = [{**segment, 'start_elapsed_seconds_exact': _seconds_record(max(
                birth_value, _fraction(segment['start_elapsed_seconds_exact'])))} for segment in forcing
                if _fraction(segment['end_elapsed_seconds_exact']) > birth_value]
            state, advanced_hash = initial['state'], None
            if remaining:
                advanced = advance_rational_internode_length(inputs={
                    'input_id': _digest({'input_id': inputs['input_id'], 'internode_id': internode_id, 'operation': 'advance'}),
                    'state': state, 'segments': remaining})
                state, advanced_hash = advanced['state'], advanced['input_sha256']
        except RationalInternodeLengthHold as exc:
            raise RationalNewInternodeHold(str(exc)) from None
        _need(_fraction(state['clock_state']['age_exact']) ==
              _fraction(current['age_exact']) - _fraction(event['thermal_age_exact']), 'CLOCK_HOLD: organ and shoot ages disagree')
        nodes.append({'sequence': event['sequence'], 'birth_age_exact': dict(event['thermal_age_exact']),
            'length_state': state, 'initialization_input_sha256': initial['input_sha256'], 'advancement_input_sha256': advanced_hash})
    identity = {'model_version': MODEL_VERSION, 'timeline_version': TIMELINE_VERSION, 'length_version': LENGTH_VERSION,
        'air_adapter_version': AIR_ADAPTER_VERSION, 'timeline_input_sha256': timeline['input_sha256'],
        'curve_sha256': prototype['state']['curve_sha256'], 'initial_length': initial_length}
    result = {'model_version': MODEL_VERSION, 'scope': 'software_research_only', 'claim_scope': 'synthetic_crop_math_only',
        'gates': 'not_assessed', 'input_sha256': _digest(identity), 'timeline_input_sha256': timeline['input_sha256'],
        'time_origin_utc': origin, 'air_adapter_version': AIR_ADAPTER_VERSION,
        'timeline_checkpoint': current, 'new_internodes': nodes}
    _need(len(json.dumps(result, sort_keys=True, separators=(',', ':'), allow_nan=False).encode()) <= 2 * 1024**2,
          'CAPACITY_HOLD: rational new-internode result exceeds 2MiB')
    return result
