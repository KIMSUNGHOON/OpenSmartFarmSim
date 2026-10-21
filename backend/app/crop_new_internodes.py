"""Bind synthetic shoot emergence to explicit canonical internode lengths.

Source and project policies: contracts/crop-shoot-new-internodes-v1.md.
This produces new internodes only, not a complete crop or plant height.
"""
from fractions import Fraction
from hashlib import sha256
import json

from .crop_internode_length import (
    MODEL_VERSION as LENGTH_VERSION, InternodeLengthHold, advance_internode_length, initialize_internode_length,
)
from .crop_shoot_timeline import (
    MODEL_VERSION as TIMELINE_VERSION, ShootTimelineHold, advance_shoot_event_timeline,
)


MODEL_VERSION = 'shoot-new-internodes-research-v1'


class NewInternodeHold(ValueError):
    pass


def _need(condition, reason):
    if not condition:
        raise NewInternodeHold(reason)


def _digest(value):
    return sha256(json.dumps(value, sort_keys=True, separators=(',', ':'), allow_nan=False).encode()).hexdigest()


def _fraction(quantity):
    return Fraction(int(quantity['numerator']), int(quantity['denominator']))


def _clock(internode_id, utc, base):
    return {'origin': 'synthetic', 'age_basis': 'since_internode_emergence',
            'temperature_basis': 'indoor_air_piecewise_constant', 'internode_id': internode_id,
            'emerged_at': utc, 'at': utc, 'base_temperature': dict(base),
            'age_exact': {'numerator': '0', 'denominator': '1', 'unit': 'degC_day'}}


def create_internodes_from_shoot_events(*, inputs):
    _need(type(inputs) is dict and set(inputs) == {
        'input_id', 'timeline_state', 'segments', 'curve', 'initial_length'}, 'INPUT_HOLD: closed new-internode input required')
    try:
        timeline = advance_shoot_event_timeline(inputs={'input_id': inputs['input_id'],
            'state': inputs['timeline_state'], 'segments': inputs['segments']})
    except ShootTimelineHold as exc:
        raise NewInternodeHold(str(exc)) from None
    _need(all(event['utc_whole_second'] is not None for event in timeline['events']),
          'SUBSECOND_EMERGENCE_HOLD: internode clock requires whole-second birth UTC')
    current = timeline['checkpoint']
    try:
        prototype = initialize_internode_length(inputs={
            'input_id': 'synthetic-template-validation',
            'clock_state': _clock('synthetic-template-validation', current['at'], current['base_temperature']),
            'curve': inputs['curve'], 'initial_length': inputs['initial_length']})
    except InternodeLengthHold as exc:
        raise NewInternodeHold(str(exc)) from None
    curve = prototype['state']['curve']
    initial_length = prototype['state']['anchor']['requested_length']
    new_internodes = []
    for event in timeline['events']:
        birth = event['utc_whole_second']
        entity = {key: current[key] for key in ('shoot_id', 'development_origin_id', 'schedule_id', 'started_at')}
        entity.update(sequence=event['sequence'], birth_age_exact=event['thermal_age_exact'])
        internode_id = 'internode:' + _digest(entity)
        try:
            initial = initialize_internode_length(inputs={
                'input_id': _digest({'input_id': inputs['input_id'], 'internode_id': internode_id, 'operation': 'initialize'}),
                'clock_state': _clock(internode_id, birth, current['base_temperature']),
                'curve': curve, 'initial_length': initial_length})
            remaining = [{**segment, 'start_utc': max(birth, segment['start_utc'])}
                         for segment in inputs['segments'] if segment['end_utc'] > birth]
            state, advanced_hash = initial['state'], None
            if remaining:
                advanced = advance_internode_length(inputs={
                    'input_id': _digest({'input_id': inputs['input_id'], 'internode_id': internode_id, 'operation': 'advance'}),
                    'state': state, 'segments': remaining})
                state, advanced_hash = advanced['state'], advanced['input_sha256']
        except InternodeLengthHold as exc:
            raise NewInternodeHold(str(exc)) from None
        _need(_fraction(state['clock_state']['age_exact']) ==
              _fraction(current['age_exact']) - _fraction(event['thermal_age_exact']),
              'CLOCK_HOLD: internode age does not match shoot age since birth')
        new_internodes.append({'sequence': event['sequence'], 'birth_age_exact': dict(event['thermal_age_exact']),
            'length_state': state, 'initialization_input_sha256': initial['input_sha256'],
            'advancement_input_sha256': advanced_hash})
    identity = {'model_version': MODEL_VERSION, 'timeline_version': TIMELINE_VERSION,
                'length_version': LENGTH_VERSION, 'timeline_input_sha256': timeline['input_sha256'],
                'curve_sha256': prototype['state']['curve_sha256'], 'initial_length': initial_length}
    result = {'model_version': MODEL_VERSION, 'scope': 'software_research_only',
              'claim_scope': 'synthetic_crop_math_only', 'gates': 'not_assessed',
              'input_sha256': _digest(identity), 'timeline_input_sha256': timeline['input_sha256'],
              'timeline_checkpoint': current, 'new_internodes': new_internodes}
    _need(len(json.dumps(result, sort_keys=True, separators=(',', ':'), allow_nan=False).encode()) <= 2 * 1024**2,
          'CAPACITY_HOLD: new-internode result exceeds 2MiB')
    return result
