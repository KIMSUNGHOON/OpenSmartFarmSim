"""One declared existing leaf, exact forcing, and a frozen removal checkpoint."""
from copy import deepcopy

from . import crop_declared_leaf_removal as point
from .crop_morphology_thermal_clock import MorphologyClockHold, thermal_age_fraction
from .crop_rational_morphology_clock import _seconds

MODEL_VERSION = 'declared-leaf-removal-timeline-research-v1'
STATE_KEYS = {'model_version', 'initial_leaf_state', 'initial_leaf_state_sha256', 'removal_declaration',
              'removal_declaration_sha256', 'at_elapsed_seconds_exact', 'leaf_state', 'removal_receipt'}
PARENT_HOLDS = (*point.PARENT_HOLDS, point.LeafRemovalHold, MorphologyClockHold)


class LeafRemovalTimelineHold(ValueError):
    pass


def _need(condition, reason):
    if not condition:
        raise LeafRemovalTimelineHold(reason)


def _declaration(value, initial):
    if value is None:
        return None
    _need(type(value) is dict, 'INPUT_HOLD: explicit removal declaration or null required')
    clock = initial['clock_state']
    declaration = point._event(value, {'time_origin_utc': clock['time_origin_utc'],
                                      'at_elapsed_seconds_exact': value.get('at_elapsed_seconds_exact')})
    _need(declaration['leaf_id'] == clock['leaf_id']
          and _seconds(declaration['at_elapsed_seconds_exact']) >= _seconds(clock['at_elapsed_seconds_exact']),
          'TIME_HOLD: same existing leaf and non-retrospective removal required')
    return declaration


def _receipt(declaration, current):
    return {'declaration_sha256': point._digest(declaration), 'last_leaf_state_sha256': point._digest(current),
            'at_elapsed_seconds_exact': deepcopy(declaration['at_elapsed_seconds_exact']),
            'area': deepcopy(current['area_state']['area'])}


def _input(inputs, keys):
    point.births._bounded(inputs)
    _need(type(inputs) is dict and set(inputs) == keys, 'INPUT_HOLD: closed single-leaf removal timeline input required')
    point.leaf._identifier(inputs['input_id'])


def _normalize(state):
    point.births._bounded(state)
    _need(type(state) is dict and set(state) == STATE_KEYS and state['model_version'] == MODEL_VERSION,
          'STATE_HOLD: supported closed removal timeline required')
    initial = point.leaf.normalize_rational_leaf_area_state(state=deepcopy(state['initial_leaf_state']))
    current = point.leaf.normalize_rational_leaf_area_state(state=deepcopy(state['leaf_state']))
    _need(state['initial_leaf_state_sha256'] == point._digest(initial), 'STATE_HOLD: initial leaf source changed')
    declaration = _declaration(state['removal_declaration'], initial)
    expected_hash = None if declaration is None else point._digest(declaration)
    _need(state['removal_declaration_sha256'] == expected_hash, 'STATE_HOLD: removal declaration changed')
    at = _seconds(state['at_elapsed_seconds_exact']); last = _seconds(current['clock_state']['at_elapsed_seconds_exact'])
    initial_at = _seconds(initial['clock_state']['at_elapsed_seconds_exact'])
    _need(initial_at <= last <= at
          and thermal_age_fraction(current['clock_state']['age_exact']) >= thermal_age_fraction(initial['clock_state']['age_exact']),
          'STATE_HOLD: timeline or leaf age moved before the initial source')
    _need(current['clock_anchor'] == initial['clock_anchor']
          and current['area_state']['anchor'] == initial['area_state']['anchor']
          and current['area_state']['curve'] == initial['area_state']['curve'],
          'STATE_HOLD: original leaf anchor or curve changed')
    _need(last != initial_at or current == initial, 'STATE_HOLD: leaf changed without elapsed time')
    target = None if declaration is None else _seconds(declaration['at_elapsed_seconds_exact'])
    receipt = state['removal_receipt']
    if target is not None and target <= at:
        _need(last == target and point._digest(receipt) == point._digest(_receipt(declaration, current)),
              'STATE_HOLD: removal checkpoint or receipt changed')
    else:
        _need(receipt is None and last == at, 'STATE_HOLD: active leaf must match the global timeline')
    return {**state, 'initial_leaf_state': initial, 'leaf_state': current,
            'removal_declaration': declaration, 'removal_receipt': deepcopy(receipt),
            'at_elapsed_seconds_exact': deepcopy(state['at_elapsed_seconds_exact'])}


def normalize_leaf_removal_timeline_state(*, state):
    try:
        return _normalize(state)
    except PARENT_HOLDS as exc:
        raise LeafRemovalTimelineHold(str(exc)) from None


def _envelope(state, inputs, operation):
    removed = state['removal_receipt'] is not None; area = state['leaf_state']['area_state']['area']
    result = {'model_version': MODEL_VERSION, 'scope': 'software_research_only',
              'claim_scope': 'synthetic_crop_math_only', 'gates': 'not_assessed',
              'input_sha256': point._digest({'model_version': MODEL_VERSION, 'operation': operation, 'inputs': inputs}),
              'state': state, 'status': 'removed' if removed else 'active',
              'active_leaf_count': int(not removed), 'removed_leaf_count': int(removed),
              'last_leaf_area': deepcopy(area), 'active_leaf_area': {'value': 0.0, 'unit': 'm2'} if removed else deepcopy(area),
              'removed_leaf_area': deepcopy(area) if removed else {'value': 0.0, 'unit': 'm2'}}
    point.births._bounded(result)
    return result


def initialize_leaf_removal_timeline(*, inputs):
    try:
        _input(inputs, {'input_id', 'leaf_state', 'removal'})
        initial = point.leaf.normalize_rational_leaf_area_state(state=deepcopy(inputs['leaf_state']))
        declaration = _declaration(inputs['removal'], initial)
        immediate = declaration is not None and declaration['at_elapsed_seconds_exact'] == initial['clock_state']['at_elapsed_seconds_exact']
        state = {'model_version': MODEL_VERSION, 'initial_leaf_state': initial, 'initial_leaf_state_sha256': point._digest(initial),
                 'removal_declaration': declaration, 'removal_declaration_sha256': None if declaration is None else point._digest(declaration),
                 'at_elapsed_seconds_exact': deepcopy(initial['clock_state']['at_elapsed_seconds_exact']),
                 'leaf_state': deepcopy(initial), 'removal_receipt': _receipt(declaration, initial) if immediate else None}
        return _envelope(state, inputs, 'initialize')
    except PARENT_HOLDS as exc:
        raise LeafRemovalTimelineHold(str(exc)) from None


def advance_leaf_removal_timeline(*, inputs):
    try:
        _input(inputs, {'input_id', 'state', 'segments'})
        state = _normalize(inputs['state']); forcing = point.births._forcing(inputs['segments'])
        at = _seconds(state['at_elapsed_seconds_exact'])
        _need(_seconds(forcing[0]['start_elapsed_seconds_exact']) == at, 'TIME_HOLD: forcing must continue the global timeline')
        end = _seconds(forcing[-1]['end_elapsed_seconds_exact']); current = state['leaf_state']; receipt = state['removal_receipt']
        if receipt is None:
            declaration = state['removal_declaration']
            target = None if declaration is None else _seconds(declaration['at_elapsed_seconds_exact'])
            stop = end if target is None else min(end, target)
            prefix = [{**segment, 'end_elapsed_seconds_exact': point.births._record(min(stop, _seconds(segment['end_elapsed_seconds_exact'])))}
                      for segment in forcing if _seconds(segment['start_elapsed_seconds_exact']) < stop]
            current = point.leaf.advance_rational_leaf_area(inputs={'input_id': inputs['input_id'], 'state': current, 'segments': prefix})['state']
            if target is not None and target <= end:
                receipt = _receipt(declaration, current)
        result = {**state, 'at_elapsed_seconds_exact': deepcopy(forcing[-1]['end_elapsed_seconds_exact']),
                  'leaf_state': current, 'removal_receipt': receipt}
        return _envelope(result, inputs, 'advance')
    except PARENT_HOLDS as exc:
        raise LeafRemovalTimelineHold(str(exc)) from None
