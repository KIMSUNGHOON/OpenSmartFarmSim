"""Fixed explicit leaf births and removals on the original rational time axis."""
from copy import deepcopy

from . import crop_leaf_removal_inventory as base

single = base.single
point = base.point
MODEL_VERSION = 'declared-leaf-lifecycle-research-v1'
STATE_KEYS = {'model_version', 'existing_inventory_state', 'birth_declarations', 'birth_declarations_sha256',
              'removal_declarations', 'removal_declarations_sha256', 'new_leaf_checkpoints'}
PARENT_HOLDS = (base.LeafRemovalInventoryHold, *base.PARENT_HOLDS)


class LeafLifecycleHold(ValueError):
    pass


def _need(condition, reason):
    if not condition:
        raise LeafLifecycleHold(reason)


def _input(inputs, keys):
    point.births._bounded(inputs)
    _need(type(inputs) is dict and set(inputs) == keys, 'INPUT_HOLD: closed fixed leaf lifecycle input required')
    point.leaf._identifier(inputs['input_id'])


def _schedule(source, supplied_births, supplied_removals):
    existing = point._leaves(source)
    _need(type(supplied_births) is list and len(existing) + len(supplied_births) <= 512,
          'CAPACITY_HOLD: 1-512 existing and scheduled leaves required')
    previous = single._seconds(source['at_elapsed_seconds_exact']); source_at = previous
    available = dict(existing); births = []; initials = {}
    for declaration in supplied_births:
        initial = point.population._declared_initialization(declaration, source['time_origin_utc'])
        clock = initial['clock_state']; identifier = clock['leaf_id']; at = single._seconds(clock['emerged_elapsed_seconds_exact'])
        _need(at > source_at and at >= previous, 'TIME_HOLD: ordered future births after the source required')
        _need(identifier not in available, 'INPUT_HOLD: existing and scheduled leaf IDs must be unique')
        previous = at; available[identifier] = initial; initials[identifier] = initial; births.append(deepcopy(declaration))
    _need(type(supplied_removals) is list and len(supplied_removals) <= 512,
          'CAPACITY_HOLD: 0-512 explicit lifecycle removals required')
    removals = []; seen_leaves = set(); seen_events = set()
    for value in supplied_removals:
        _need(type(value) is dict and type(value.get('leaf_id')) is str and value['leaf_id'] in available,
              'INPUT_HOLD: removal must name an existing or scheduled leaf')
        declaration = single._declaration(value, available[value['leaf_id']])
        _need(declaration['leaf_id'] not in seen_leaves and declaration['event_id'] not in seen_events,
              'INPUT_HOLD: unique removal leaf and event IDs required')
        seen_leaves.add(declaration['leaf_id']); seen_events.add(declaration['event_id']); removals.append(declaration)
    existing_removals = [d for d in removals if d['leaf_id'] in existing]
    return births, initials, removals, existing_removals


def _normalize(state):
    point.births._bounded(state)
    _need(type(state) is dict and set(state) == STATE_KEYS and state['model_version'] == MODEL_VERSION,
          'STATE_HOLD: closed supported leaf lifecycle state required')
    existing = base.normalize_leaf_removal_inventory_state(state=state['existing_inventory_state'])
    source = existing['source_population']
    births, initials, removals, existing_removals = _schedule(source, state['birth_declarations'], state['removal_declarations'])
    _need(state['birth_declarations_sha256'] == point._digest(births)
          and state['removal_declarations_sha256'] == point._digest(removals), 'STATE_HOLD: original lifecycle declarations changed')
    _need(existing['removal_declarations'] == existing_removals, 'STATE_HOLD: existing and lifecycle removals differ')
    at_record = existing['at_elapsed_seconds_exact']; at = single._seconds(at_record)
    supplied = state['new_leaf_checkpoints']; by_leaf = {d['leaf_id']: d for d in removals}
    _need(type(supplied) is list and len(supplied) == len(births), 'STATE_HOLD: original scheduled leaf count and order required')
    checkpoints = []
    for declaration, checkpoint in zip(births, supplied):
        _need(type(checkpoint) is dict and set(checkpoint) == {'state', 'removal_receipt'},
              'STATE_HOLD: closed pending or emerged leaf checkpoint required')
        if single._seconds(declaration['emerged_elapsed_seconds_exact']) > at:
            _need(checkpoint['state'] is None and checkpoint['removal_receipt'] is None,
                  'STATE_HOLD: a pending leaf cannot have current or removed state')
            checkpoints.append({'state': None, 'removal_receipt': None})
        else:
            identifier = declaration['leaf_id']
            timeline = single.normalize_leaf_removal_timeline_state(
                state=base._timeline(initials[identifier], by_leaf.get(identifier), checkpoint, at_record))
            checkpoints.append(base._checkpoint(timeline))
    result = {**state, 'existing_inventory_state': existing, 'birth_declarations': births,
              'removal_declarations': removals, 'new_leaf_checkpoints': checkpoints}
    point.births._bounded(result)
    return result


def normalize_leaf_lifecycle_state(*, state):
    try:
        return _normalize(state)
    except PARENT_HOLDS as exc:
        raise LeafLifecycleHold(str(exc)) from None


def _envelope(state, inputs, operation):
    existing = state['existing_inventory_state']; emerged = [r for r in state['new_leaf_checkpoints'] if r['state'] is not None]
    checkpoints = [*existing['leaf_checkpoints'], *emerged]
    active = [r for r in checkpoints if r['removal_receipt'] is None]
    removed = [r for r in checkpoints if r['removal_receipt'] is not None]
    pending = [d['leaf_id'] for d, r in zip(state['birth_declarations'], state['new_leaf_checkpoints']) if r['state'] is None]
    def area(records):
        return point.inventory._sum(r['state']['area_state']['area']['value'] for r in records)
    result = {'model_version': MODEL_VERSION, 'scope': 'software_research_only', 'claim_scope': 'synthetic_crop_math_only',
              'gates': 'not_assessed', 'input_sha256': point._digest({'model_version': MODEL_VERSION, 'operation': operation, 'inputs': inputs}),
              'state': state, 'time_origin_utc': existing['source_population']['time_origin_utc'],
              'at_elapsed_seconds_exact': deepcopy(existing['at_elapsed_seconds_exact']),
              'declared_leaf_count': len(checkpoints) + len(pending), 'tracked_leaf_count': len(checkpoints),
              'active_leaf_count': len(active), 'removed_leaf_count': len(removed),
              'scheduled_birth_count': len(state['birth_declarations']), 'emerged_new_leaf_count': len(emerged),
              'pending_leaf_count': len(pending), 'pending_leaf_ids': pending,
              'active_leaf_ids': [r['state']['clock_state']['leaf_id'] for r in active],
              'removed_leaf_ids': [r['state']['clock_state']['leaf_id'] for r in removed],
              'active_leaf_area': area(active), 'removed_leaf_area': area(removed), 'last_tracked_leaf_area': area(checkpoints)}
    point.births._bounded(result)
    return result


def initialize_leaf_lifecycle(*, inputs):
    try:
        _input(inputs, {'input_id', 'population_state', 'births', 'removals'})
        source = point.population.normalize_leaf_population_state(state=deepcopy(inputs['population_state']))
        births, _, removals, existing_removals = _schedule(source, inputs['births'], inputs['removals'])
        existing = base.initialize_leaf_removal_inventory(inputs={'input_id': inputs['input_id'],
            'population_state': source, 'removals': existing_removals})['state']
        state = {'model_version': MODEL_VERSION, 'existing_inventory_state': existing,
                 'birth_declarations': births, 'birth_declarations_sha256': point._digest(births),
                 'removal_declarations': removals, 'removal_declarations_sha256': point._digest(removals),
                 'new_leaf_checkpoints': [{'state': None, 'removal_receipt': None} for _ in births]}
        return _envelope(state, inputs, 'initialize')
    except PARENT_HOLDS as exc:
        raise LeafLifecycleHold(str(exc)) from None


def advance_leaf_lifecycle(*, inputs):
    try:
        _input(inputs, {'input_id', 'state', 'segments'})
        state = _normalize(inputs['state']); forcing = point.births._forcing(inputs['segments'])
        old = state['existing_inventory_state']; start_record = old['at_elapsed_seconds_exact']; start = single._seconds(start_record)
        _need(forcing[0]['start_elapsed_seconds_exact'] == start_record, 'TIME_HOLD: forcing must continue the lifecycle timeline')
        end = single._seconds(forcing[-1]['end_elapsed_seconds_exact'])
        existing = base.advance_leaf_removal_inventory(inputs={'input_id': inputs['input_id'], 'state': old, 'segments': forcing})['state']
        by_leaf = {d['leaf_id']: d for d in state['removal_declarations']}; checkpoints = []
        for declaration, checkpoint in zip(state['birth_declarations'], state['new_leaf_checkpoints']):
            birth = single._seconds(declaration['emerged_elapsed_seconds_exact'])
            if birth > end:
                checkpoints.append({'state': None, 'removal_receipt': None}); continue
            identifier = declaration['leaf_id']
            initial = point.population._declared_initialization(declaration, old['source_population']['time_origin_utc'])
            if birth > start:
                timeline = single.initialize_leaf_removal_timeline(inputs={'input_id': inputs['input_id'],
                    'leaf_state': initial, 'removal': by_leaf.get(identifier)})['state']
                remaining = [{**s, 'start_elapsed_seconds_exact': point.births._record(max(birth, single._seconds(s['start_elapsed_seconds_exact'])))}
                             for s in forcing if single._seconds(s['end_elapsed_seconds_exact']) > birth]
            else:
                timeline = base._timeline(initial, by_leaf.get(identifier), checkpoint, start_record); remaining = forcing
            if remaining:
                timeline = single.advance_leaf_removal_timeline(inputs={'input_id': inputs['input_id'],
                    'state': timeline, 'segments': remaining})['state']
            checkpoints.append(base._checkpoint(timeline))
        return _envelope({**state, 'existing_inventory_state': existing, 'new_leaf_checkpoints': checkpoints}, inputs, 'advance')
    except PARENT_HOLDS as exc:
        raise LeafLifecycleHold(str(exc)) from None
