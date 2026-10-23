"""Caller-declared whole-leaf removals at one immutable population checkpoint."""
from copy import deepcopy
from hashlib import sha256

from . import crop_leaf_population as population
from . import crop_leaf_inventory as inventory
from . import crop_declared_leaf_births as births
from . import crop_rational_leaf_area as leaf
from .crop_rational_morphology_clock import RationalMorphologyClockHold, _seconds

MODEL_VERSION = 'declared-leaf-removal-point-research-v1'
STATE_KEYS = {'model_version', 'population_snapshot', 'population_snapshot_sha256', 'removals', 'removals_sha256'}
EVENT_KEYS = {'schema_version', 'origin', 'action', 'event_id', 'leaf_id', 'time_origin_utc', 'at_elapsed_seconds_exact'}
PARENT_HOLDS = (population.LeafPopulationHold, inventory.LeafInventoryHold, births.DeclaredLeafBirthHold,
                leaf.RationalLeafAreaHold, RationalMorphologyClockHold)


class LeafRemovalHold(ValueError):
    pass


def _need(condition, reason):
    if not condition:
        raise LeafRemovalHold(reason)


def _digest(value):
    return sha256(births._bounded(value)).hexdigest()


def _leaves(snapshot):
    return {item['state']['clock_state']['leaf_id']: item['state']
            for item in [*snapshot['initial_inventory_state']['leaves'], *snapshot['new_leaves']]}


def _event(value, snapshot):
    _need(type(value) is dict and set(value) == EVENT_KEYS, 'INPUT_HOLD: closed removal declaration required')
    _need(value['schema_version'] == 'declared-whole-leaf-removal-event-v1' and value['origin'] == 'synthetic'
          and value['action'] == 'remove_whole_leaf', 'INPUT_HOLD: explicit synthetic whole-leaf removal required')
    leaf._identifier(value['event_id']); leaf._identifier(value['leaf_id'])
    _seconds(value['at_elapsed_seconds_exact'])
    _need(value['time_origin_utc'] == snapshot['time_origin_utc']
          and value['at_elapsed_seconds_exact'] == snapshot['at_elapsed_seconds_exact'],
          'TIME_HOLD: removal must match the original exact checkpoint')
    return deepcopy(value)


def _input(inputs, keys):
    births._bounded(inputs)
    _need(type(inputs) is dict and set(inputs) == keys, 'INPUT_HOLD: closed leaf removal input required')
    leaf._identifier(inputs['input_id'])


def _normalize(state):
    births._bounded(state)
    _need(type(state) is dict and set(state) == STATE_KEYS and state['model_version'] == MODEL_VERSION,
          'STATE_HOLD: supported closed leaf removal state required')
    snapshot = population.normalize_leaf_population_state(state=deepcopy(state['population_snapshot']))
    _need(state['population_snapshot_sha256'] == _digest(snapshot), 'STATE_HOLD: population snapshot changed')
    records = state['removals']
    _need(type(records) is list and len(records) <= 512, 'CAPACITY_HOLD: bounded removal history required')
    _need(state['removals_sha256'] == _digest(records), 'STATE_HOLD: removal history changed')
    available = _leaves(snapshot); removed = set(); events = set(); normalized = []
    for record in records:
        _need(type(record) is dict and set(record) == {'declaration', 'declaration_sha256', 'last_leaf_state_sha256'},
              'STATE_HOLD: closed removal receipt required')
        declaration = _event(record['declaration'], snapshot); identifier = declaration['leaf_id']
        _need(identifier in available and identifier not in removed and declaration['event_id'] not in events,
              'STATE_HOLD: removal history has missing or repeated identity')
        _need(record['declaration_sha256'] == _digest(declaration)
              and record['last_leaf_state_sha256'] == _digest(available[identifier]),
              'STATE_HOLD: removal declaration or last leaf state changed')
        removed.add(identifier); events.add(declaration['event_id']); normalized.append(deepcopy(record))
    return {**state, 'population_snapshot': snapshot, 'removals': normalized}


def normalize_leaf_removal_state(*, state):
    try:
        return _normalize(state)
    except PARENT_HOLDS as exc:
        raise LeafRemovalHold(str(exc)) from None


def _envelope(state, inputs, operation, new_count):
    available = _leaves(state['population_snapshot'])
    removed = {record['declaration']['leaf_id'] for record in state['removals']}
    areas = {identifier: value['area_state']['area']['value'] for identifier, value in available.items()}
    result = {'model_version': MODEL_VERSION, 'scope': 'software_research_only', 'claim_scope': 'synthetic_crop_math_only',
              'gates': 'not_assessed', 'input_sha256': _digest({'model_version': MODEL_VERSION, 'operation': operation, 'inputs': inputs}),
              'state': state, 'snapshot_leaf_count': len(areas), 'active_leaf_count': len(areas) - len(removed),
              'removed_leaf_count': len(removed), 'new_removed_leaf_count': new_count,
              'active_leaf_ids': [identifier for identifier in areas if identifier not in removed],
              'snapshot_leaf_area': inventory._sum(areas.values()),
              'active_leaf_area': inventory._sum(area for identifier, area in areas.items() if identifier not in removed),
              'removed_leaf_area': inventory._sum(area for identifier, area in areas.items() if identifier in removed)}
    births._bounded(result)
    return result


def initialize_leaf_removal(*, inputs):
    try:
        _input(inputs, {'input_id', 'population_state'})
        snapshot = population.normalize_leaf_population_state(state=deepcopy(inputs['population_state']))
        state = {'model_version': MODEL_VERSION, 'population_snapshot': snapshot,
                 'population_snapshot_sha256': _digest(snapshot), 'removals': [], 'removals_sha256': _digest([])}
        return _envelope(state, inputs, 'initialize', 0)
    except PARENT_HOLDS as exc:
        raise LeafRemovalHold(str(exc)) from None


def apply_leaf_removals(*, inputs):
    try:
        _input(inputs, {'input_id', 'state', 'events'})
        state = _normalize(inputs['state']); supplied = inputs['events']
        _need(type(supplied) is list and len(state['removals']) + len(supplied) <= 512,
              'CAPACITY_HOLD: bounded removal batch required')
        available = _leaves(state['population_snapshot']); records = state['removals']
        removed = {record['declaration']['leaf_id'] for record in records}
        events = {record['declaration']['event_id'] for record in records}
        for value in supplied:
            declaration = _event(value, state['population_snapshot']); identifier = declaration['leaf_id']
            _need(identifier in available and identifier not in removed and declaration['event_id'] not in events,
                  'INPUT_HOLD: missing or already removed leaf/event identity')
            records.append({'declaration': declaration, 'declaration_sha256': _digest(declaration),
                            'last_leaf_state_sha256': _digest(available[identifier])})
            removed.add(identifier); events.add(declaration['event_id'])
        current = {**state, 'removals': records, 'removals_sha256': _digest(records)}
        return _envelope(current, inputs, 'remove', len(supplied))
    except PARENT_HOLDS as exc:
        raise LeafRemovalHold(str(exc)) from None
