"""Existing leaf checkpoints with independent declared removal boundaries."""
from copy import deepcopy

from . import crop_leaf_removal_timeline as single

point = single.point
MODEL_VERSION = 'declared-leaf-removal-inventory-research-v1'
STATE_KEYS = {'model_version', 'source_population', 'source_population_sha256', 'removal_declarations',
              'removal_declarations_sha256', 'at_elapsed_seconds_exact', 'leaf_checkpoints'}
PARENT_HOLDS = (single.LeafRemovalTimelineHold, *single.PARENT_HOLDS)


class LeafRemovalInventoryHold(ValueError):
    pass


def _need(condition, reason):
    if not condition:
        raise LeafRemovalInventoryHold(reason)


def _input(inputs, keys):
    point.births._bounded(inputs)
    _need(type(inputs) is dict and set(inputs) == keys, 'INPUT_HOLD: closed existing-leaf removal inventory required')
    point.leaf._identifier(inputs['input_id'])


def _declarations(supplied, source):
    _need(type(supplied) is list and len(supplied) <= 512, 'CAPACITY_HOLD: 0-512 explicit removal declarations required')
    available = point._leaves(source); identifiers = set(); events = set(); records = []
    for value in supplied:
        _need(type(value) is dict and type(value.get('leaf_id')) is str and value['leaf_id'] in available,
              'INPUT_HOLD: removal must name an existing source leaf')
        declaration = single._declaration(value, available[value['leaf_id']])
        _need(declaration['leaf_id'] not in identifiers and declaration['event_id'] not in events,
              'INPUT_HOLD: unique removal leaf and event IDs required')
        identifiers.add(declaration['leaf_id']); events.add(declaration['event_id']); records.append(declaration)
    return records


def _timeline(initial, declaration, checkpoint, at):
    return {'model_version': single.MODEL_VERSION, 'initial_leaf_state': initial,
            'initial_leaf_state_sha256': point._digest(initial), 'removal_declaration': declaration,
            'removal_declaration_sha256': None if declaration is None else point._digest(declaration),
            'at_elapsed_seconds_exact': at, 'leaf_state': checkpoint['state'],
            'removal_receipt': checkpoint['removal_receipt']}


def _checkpoint(timeline):
    return {'state': timeline['leaf_state'], 'removal_receipt': timeline['removal_receipt']}


def _normalize(state):
    point.births._bounded(state)
    _need(type(state) is dict and set(state) == STATE_KEYS and state['model_version'] == MODEL_VERSION,
          'STATE_HOLD: closed supported removal inventory required')
    source = point.population.normalize_leaf_population_state(state=deepcopy(state['source_population']))
    _need(state['source_population_sha256'] == point._digest(source), 'STATE_HOLD: original population source changed')
    declarations = _declarations(state['removal_declarations'], source)
    _need(state['removal_declarations_sha256'] == point._digest(declarations), 'STATE_HOLD: removal declarations changed')
    at = single._seconds(state['at_elapsed_seconds_exact'])
    _need(at >= single._seconds(source['at_elapsed_seconds_exact']), 'TIME_HOLD: timeline moved before its source')
    available = point._leaves(source); by_leaf = {d['leaf_id']: d for d in declarations}
    supplied = state['leaf_checkpoints']
    _need(type(supplied) is list and len(supplied) == len(available), 'STATE_HOLD: original leaf count and order required')
    records = []
    for (identifier, initial), checkpoint in zip(available.items(), supplied):
        _need(type(checkpoint) is dict and set(checkpoint) == {'state', 'removal_receipt'},
              'STATE_HOLD: closed current or removed leaf checkpoint required')
        timeline = single.normalize_leaf_removal_timeline_state(
            state=_timeline(initial, by_leaf.get(identifier), checkpoint, state['at_elapsed_seconds_exact']))
        records.append(_checkpoint(timeline))
    result = {**state, 'source_population': source, 'removal_declarations': declarations,
              'at_elapsed_seconds_exact': deepcopy(state['at_elapsed_seconds_exact']), 'leaf_checkpoints': records}
    point.births._bounded(result)
    return result


def normalize_leaf_removal_inventory_state(*, state):
    try:
        return _normalize(state)
    except PARENT_HOLDS as exc:
        raise LeafRemovalInventoryHold(str(exc)) from None


def _envelope(state, inputs, operation):
    active = [r for r in state['leaf_checkpoints'] if r['removal_receipt'] is None]
    removed = [r for r in state['leaf_checkpoints'] if r['removal_receipt'] is not None]
    def area(records):
        return point.inventory._sum(r['state']['area_state']['area']['value'] for r in records)
    result = {'model_version': MODEL_VERSION, 'scope': 'software_research_only',
              'claim_scope': 'synthetic_crop_math_only', 'gates': 'not_assessed',
              'input_sha256': point._digest({'model_version': MODEL_VERSION, 'operation': operation, 'inputs': inputs}),
              'state': state, 'tracked_leaf_count': len(active) + len(removed),
              'active_leaf_count': len(active), 'removed_leaf_count': len(removed),
              'active_leaf_ids': [r['state']['clock_state']['leaf_id'] for r in active],
              'removed_leaf_ids': [r['state']['clock_state']['leaf_id'] for r in removed],
              'active_leaf_area': area(active), 'removed_leaf_area': area(removed),
              'last_tracked_leaf_area': area(state['leaf_checkpoints'])}
    point.births._bounded(result)
    return result


def initialize_leaf_removal_inventory(*, inputs):
    try:
        _input(inputs, {'input_id', 'population_state', 'removals'})
        source = point.population.normalize_leaf_population_state(state=deepcopy(inputs['population_state']))
        declarations = _declarations(inputs['removals'], source); by_leaf = {d['leaf_id']: d for d in declarations}
        records = []
        for identifier, initial in point._leaves(source).items():
            timeline = single.initialize_leaf_removal_timeline(inputs={'input_id': inputs['input_id'],
                'leaf_state': initial, 'removal': by_leaf.get(identifier)})['state']
            records.append(_checkpoint(timeline))
        state = {'model_version': MODEL_VERSION, 'source_population': source, 'source_population_sha256': point._digest(source),
                 'removal_declarations': declarations, 'removal_declarations_sha256': point._digest(declarations),
                 'at_elapsed_seconds_exact': deepcopy(source['at_elapsed_seconds_exact']), 'leaf_checkpoints': records}
        return _envelope(state, inputs, 'initialize')
    except PARENT_HOLDS as exc:
        raise LeafRemovalInventoryHold(str(exc)) from None


def advance_leaf_removal_inventory(*, inputs):
    try:
        _input(inputs, {'input_id', 'state', 'segments'})
        state = _normalize(inputs['state']); forcing = point.births._forcing(inputs['segments'])
        _need(forcing[0]['start_elapsed_seconds_exact'] == state['at_elapsed_seconds_exact'],
              'TIME_HOLD: forcing must continue the inventory timeline')
        available = point._leaves(state['source_population']); by_leaf = {d['leaf_id']: d for d in state['removal_declarations']}
        records = []
        for (identifier, initial), checkpoint in zip(available.items(), state['leaf_checkpoints']):
            advanced = single.advance_leaf_removal_timeline(inputs={'input_id': inputs['input_id'],
                'state': _timeline(initial, by_leaf.get(identifier), checkpoint, state['at_elapsed_seconds_exact']),
                'segments': forcing})['state']
            records.append(_checkpoint(advanced))
        current = {**state, 'at_elapsed_seconds_exact': deepcopy(forcing[-1]['end_elapsed_seconds_exact']), 'leaf_checkpoints': records}
        return _envelope(current, inputs, 'advance')
    except PARENT_HOLDS as exc:
        raise LeafRemovalInventoryHold(str(exc)) from None
