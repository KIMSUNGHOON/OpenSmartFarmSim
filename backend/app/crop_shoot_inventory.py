"""Advance an explicit synthetic tracked axis; no observed plant-height claim.

Input, continuity and numeric boundaries:
contracts/crop-shoot-internode-inventory-v1.md.
"""
from hashlib import sha256
import json
from math import fsum, isfinite

from .crop_internode_length import (
    MODEL_VERSION as LENGTH_VERSION, InternodeLengthHold, advance_internode_length,
    normalize_internode_length_state,
)
from .crop_internode_length_change import normalize_internode_curve
from .crop_morphology_thermal_clock import MorphologyClockHold, thermal_age_fraction
from .crop_new_internodes import (
    MODEL_VERSION as NEW_VERSION, NewInternodeHold, create_internodes_from_shoot_events,
)


MODEL_VERSION = 'shoot-internode-inventory-research-v1'


class ShootInventoryHold(ValueError):
    pass


def _need(condition, reason):
    if not condition:
        raise ShootInventoryHold(reason)


def _digest(value):
    return sha256(json.dumps(value, sort_keys=True, separators=(',', ':'), allow_nan=False).encode()).hexdigest()


def advance_shoot_internode_inventory(*, inputs):
    _need(type(inputs) is dict and set(inputs) == {'input_id', 'state', 'segments'}, 'INPUT_HOLD: closed inventory input required')
    state = inputs['state']
    _need(type(state) is dict and set(state) == {
        'timeline_state', 'inventory_start_sequence', 'internodes', 'emergence_profile'}, 'INPUT_HOLD: closed inventory state required')
    first, nodes, profile = state['inventory_start_sequence'], state['internodes'], state['emergence_profile']
    _need(type(first) is int and 0 <= first <= 2**31 - 1, 'INPUT_HOLD: explicit bounded inventory start required')
    _need(type(nodes) is list and len(nodes) <= 512, 'CAPACITY_HOLD: tracked inventory count')
    _need(type(profile) is dict and set(profile) == {'curve', 'initial_length'}, 'INPUT_HOLD: closed emergence profile required')
    try:
        new = create_internodes_from_shoot_events(inputs={'input_id': inputs['input_id'],
            'timeline_state': state['timeline_state'], 'segments': inputs['segments'], **profile})
    except NewInternodeHold as exc:
        raise ShootInventoryHold(str(exc)) from None
    start, end = state['timeline_state'], new['timeline_checkpoint']
    _need(first + len(nodes) == start['next_sequence'], 'INVENTORY_HOLD: contiguous explicit inventory required')
    _need(len(nodes) + len(new['new_internodes']) <= 512, 'CAPACITY_HOLD: total tracked inventory count')
    start_age, end_age = thermal_age_fraction(start['age_exact']), thermal_age_fraction(end['age_exact'])
    normalized_nodes, advanced_nodes, receipts, ids = [], [], [], set()
    prior_age, prior_utc = None, None
    for index, node in enumerate(nodes):
        _need(type(node) is dict and set(node) == {'sequence', 'birth_age_exact', 'length_state'},
              'INPUT_HOLD: closed tracked internode required')
        sequence = node['sequence']
        _need(type(sequence) is int and sequence == first + index, 'INVENTORY_HOLD: ordered contiguous sequence required')
        try:
            length_state = normalize_internode_length_state(state=node['length_state'])
            birth_age = thermal_age_fraction(node['birth_age_exact'])
        except (InternodeLengthHold, MorphologyClockHold) as exc:
            raise ShootInventoryHold(str(exc)) from None
        clock = length_state['clock_state']
        _need(clock['at'] == start['at'] and clock['base_temperature'] == end['base_temperature']
              and start['started_at'] <= clock['emerged_at'], 'CLOCK_HOLD: inventory clock does not match shoot')
        _need(birth_age <= start_age and thermal_age_fraction(clock['age_exact']) == start_age - birth_age,
              'CLOCK_HOLD: inventory age does not match shoot age since birth')
        _need(prior_age is None or (prior_age <= birth_age and prior_utc <= clock['emerged_at']),
              'INVENTORY_HOLD: birth order mismatch')
        _need(clock['internode_id'] not in ids, 'INVENTORY_HOLD: duplicate internode ID')
        ids.add(clock['internode_id'])
        prior_age, prior_utc = birth_age, clock['emerged_at']
        normalized = {'sequence': sequence, 'birth_age_exact': dict(node['birth_age_exact']), 'length_state': length_state}
        normalized_nodes.append(normalized)
        try:
            advanced = advance_internode_length(inputs={'input_id': _digest({
                'input_id': inputs['input_id'], 'sequence': sequence}), 'state': length_state, 'segments': inputs['segments']})
        except InternodeLengthHold as exc:
            raise ShootInventoryHold(str(exc)) from None
        _need(thermal_age_fraction(advanced['state']['clock_state']['age_exact']) == end_age - birth_age,
              'CLOCK_HOLD: advanced age does not match shoot')
        advanced_nodes.append({**normalized, 'length_state': advanced['state']})
        receipts.append({'sequence': sequence, 'kind': 'advanced', 'input_sha256': advanced['input_sha256']})
    for node in new['new_internodes']:
        internode_id = node['length_state']['clock_state']['internode_id']
        _need(internode_id not in ids, 'INVENTORY_HOLD: duplicate new internode ID')
        ids.add(internode_id)
        advanced_nodes.append({key: node[key] for key in ('sequence', 'birth_age_exact', 'length_state')})
        receipts.append({'sequence': node['sequence'], 'kind': 'new',
                         'initialization_input_sha256': node['initialization_input_sha256'],
                         'advancement_input_sha256': node['advancement_input_sha256']})
    try:
        total = fsum(node['length_state']['length']['value'] for node in advanced_nodes)
    except OverflowError:
        raise ShootInventoryHold('NUMERIC_HOLD: tracked axis length overflow') from None
    _need(isfinite(total), 'NUMERIC_HOLD: finite tracked axis length required')
    normalized_profile = {'curve': normalize_internode_curve(curve=profile['curve'])['curve'],
                          'initial_length': {'value': float(profile['initial_length']['value']), 'unit': 'm'}}
    normalized = {**state, 'timeline_state': {**start, 'base_temperature': dict(end['base_temperature'])},
                  'internodes': normalized_nodes, 'emergence_profile': normalized_profile}
    identity = {'model_version': MODEL_VERSION, 'length_version': LENGTH_VERSION,
                'new_internode_version': NEW_VERSION, 'state': normalized,
                'new_internode_input_sha256': new['input_sha256']}
    result = {'model_version': MODEL_VERSION, 'scope': 'software_research_only',
              'claim_scope': 'synthetic_crop_math_only', 'gates': 'not_assessed',
              'input_sha256': _digest(identity), 'state': {**normalized,
                  'timeline_state': end, 'internodes': advanced_nodes},
              'step_receipts': receipts, 'tracked_axis_length': {'value': total, 'unit': 'm'}}
    _need(len(json.dumps(result, sort_keys=True, separators=(',', ':'), allow_nan=False).encode()) <= 2 * 1024**2,
          'CAPACITY_HOLD: tracked inventory result exceeds 2MiB')
    return result
