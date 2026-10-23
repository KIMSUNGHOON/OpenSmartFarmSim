from copy import deepcopy
from decimal import Decimal
from fractions import Fraction
from hashlib import sha256
import json

import pytest

from app.crop_declared_leaf_removal import (
    LeafRemovalHold, initialize_leaf_removal, apply_leaf_removals, normalize_leaf_removal_state,
)
from app import crop_leaf_population as population
from test_crop_leaf_population import REFERENCE, advance, example, states, clipped, fraction
from test_crop_rational_leaf_area import seconds


def digest(value):
    return sha256(json.dumps(value, sort_keys=True, separators=(',', ':'), allow_nan=False).encode()).hexdigest()


def initialized(index=0):
    population = advance(example(index))['state']
    return initialize_leaf_removal(inputs={'input_id': 'removal-init', 'population_state': population})


def leaves(state):
    return states({'state': state['population_snapshot']})


def event(state, identifier, identity='remove-1'):
    snapshot = state['population_snapshot']
    return {'schema_version': 'declared-whole-leaf-removal-event-v1', 'origin': 'synthetic',
            'action': 'remove_whole_leaf', 'event_id': identity, 'leaf_id': identifier,
            'time_origin_utc': snapshot['time_origin_utc'],
            'at_elapsed_seconds_exact': deepcopy(snapshot['at_elapsed_seconds_exact'])}


def apply(state, events):
    return apply_leaf_removals(inputs={'input_id': 'removal-step', 'state': state, 'events': events})


@pytest.mark.parametrize('index', range(len(REFERENCE['cases'])))
def test_independent_reference_initial_new_leaf_areas_and_retained_snapshot(index):
    result = initialized(index); state = result['state']; before = deepcopy(state)
    expected = REFERENCE['cases'][index]['expected']; selected = [expected[0], expected[-1]]
    ids = [row['leaf_id'] for row in selected]
    records = [event(state, identifier, 'remove-' + str(i)) for i, identifier in enumerate(ids)]
    result = apply(state, records)
    removed = sum((Decimal(row['area_m2']) for row in selected), Decimal(0))
    active = sum((Decimal(row['area_m2']) for row in expected if row['leaf_id'] not in ids), Decimal(0))
    assert result['removed_leaf_area'] == {'value': pytest.approx(float(removed), rel=1e-12), 'unit': 'm2'}
    assert result['active_leaf_area'] == {'value': pytest.approx(float(active), rel=1e-12), 'unit': 'm2'}
    assert result['snapshot_leaf_count'] == len(expected)
    assert result['active_leaf_count'] == len(expected) - 2
    assert result['removed_leaf_count'] == result['new_removed_leaf_count'] == 2
    assert result['active_leaf_ids'] == [row['leaf_id'] for row in expected if row['leaf_id'] not in ids]
    assert result['state']['population_snapshot'] == before['population_snapshot']
    assert state == before and normalize_leaf_removal_state(state=result['state']) == result['state']
    assert (result['scope'], result['claim_scope'], result['gates']) == (
        'software_research_only', 'synthetic_crop_math_only', 'not_assessed')


def test_every_leaf_can_be_removed_without_erasing_anchors_or_last_state():
    original = initialized()['state']; inputs = deepcopy(original)
    records = [event(original, leaf['clock_state']['leaf_id'], 'remove-' + str(i)) for i, leaf in enumerate(leaves(original))]
    result = apply(original, records)
    assert result['active_leaf_count'] == 0 and result['active_leaf_ids'] == []
    assert result['active_leaf_area'] == {'value': 0.0, 'unit': 'm2'}
    assert result['removed_leaf_area'] == result['snapshot_leaf_area']
    assert result['state']['population_snapshot'] == inputs['population_snapshot']
    for receipt, leaf in zip(result['state']['removals'], leaves(original)):
        assert receipt['last_leaf_state_sha256'] == digest(leaf)
        assert receipt['declaration_sha256'] == digest(receipt['declaration'])
    assert original == inputs


def test_same_time_split_history_and_noop_match_batch_state():
    initial = initialized()['state']
    records = [event(initial, leaf['clock_state']['leaf_id'], 'remove-' + str(i)) for i, leaf in enumerate(leaves(initial))]
    whole = apply(initial, records)
    current = initial
    for record in records:
        current = apply(current, [record])['state']
    assert current == whole['state']
    empty = apply(current, [])
    assert empty['state'] == current and empty['new_removed_leaf_count'] == 0


@pytest.mark.parametrize('fault', ['missing', 'duplicate-leaf', 'duplicate-event', 'future', 'other-origin', 'extra', 'unit'])
def test_unsupported_or_duplicate_events_hold_atomically(fault):
    state = initialized()['state']; before = deepcopy(state)
    record = event(state, leaves(state)[0]['clock_state']['leaf_id']); records = [record]
    if fault == 'missing': record['leaf_id'] = 'never-emerged'
    elif fault == 'duplicate-leaf': records.append({**record, 'event_id': 'other'})
    elif fault == 'duplicate-event': records.append({**record, 'leaf_id': leaves(state)[1]['clock_state']['leaf_id']})
    elif fault == 'future': record['at_elapsed_seconds_exact'] = seconds(86401)
    elif fault == 'other-origin': record['time_origin_utc'] = '2026-10-02T00:00:00Z'
    elif fault == 'extra': record['prediction'] = True
    elif fault == 'unit': record['at_elapsed_seconds_exact']['unit'] = 'day'
    with pytest.raises(LeafRemovalHold): apply(state, records)
    assert state == before


def test_reapplying_removed_leaf_with_new_event_id_is_rejected():
    state = initialized()['state']; record = event(state, leaves(state)[0]['clock_state']['leaf_id'])
    removed = apply(state, [record])['state']
    with pytest.raises(LeafRemovalHold): apply(removed, [{**record, 'event_id': 'another'}])


@pytest.mark.parametrize('cut', [Fraction(1, 3), Fraction(37, 5), Fraction(86399, 7)])
def test_fractional_checkpoint_and_its_original_clock_are_never_rounded(cut):
    p = example(); p['segments'] = clipped(p['segments'], Fraction(0), cut)
    p['births'] = [record for record in p['births'] if fraction(record['emerged_elapsed_seconds_exact']) <= cut]
    snapshot = advance(p)['state']
    state = initialize_leaf_removal(inputs={'input_id': 'fractional', 'population_state': snapshot})['state']
    declaration = event(state, leaves(state)[0]['clock_state']['leaf_id'])
    result = apply(state, [declaration])
    assert result['state']['removals'][0]['declaration']['at_elapsed_seconds_exact'] == seconds(cut)
    assert result['state']['population_snapshot'] == snapshot


def test_new_leaf_at_its_exact_birth_checkpoint_and_before_birth():
    p = example(); first = p['births'][0]; cut = fraction(first['emerged_elapsed_seconds_exact'])
    early = advance({**p, 'segments': clipped(p['segments'], Fraction(0), cut / 2), 'births': []})['state']
    early = initialize_leaf_removal(inputs={'input_id': 'early', 'population_state': early})['state']
    with pytest.raises(LeafRemovalHold): apply(early, [event(early, first['leaf_id'])])
    now = advance({**p, 'segments': clipped(p['segments'], Fraction(0), cut), 'births': [first]})['state']
    state = initialize_leaf_removal(inputs={'input_id': 'at-birth', 'population_state': now})['state']
    result = apply(state, [event(state, first['leaf_id'])])
    assert result['removed_leaf_count'] == 1
    assert leaves(state)[-1]['clock_state']['age_exact'] == {'numerator': '0', 'denominator': '1', 'unit': 'degC_day'}


@pytest.mark.parametrize('fault', ['model', 'snapshot-hash', 'snapshot-leaf', 'birth-inventory', 'history-delete',
                                  'history-order', 'history-hash', 'declaration-hash', 'last-state',
                                  'rehash-action', 'rehash-leaf', 'rehash-time', 'receipt-extra', 'state-extra'])
def test_history_snapshot_and_receipt_changes_are_rejected(fault):
    state = initialized()['state']
    records = [event(state, leaf['clock_state']['leaf_id'], 'remove-' + str(i)) for i, leaf in enumerate(leaves(state)[:2])]
    state = apply(state, records)['state']
    if fault == 'model': state['model_version'] = population.MODEL_VERSION
    elif fault == 'snapshot-hash': state['population_snapshot_sha256'] = '0' * 64
    elif fault == 'snapshot-leaf': state['population_snapshot']['initial_inventory_state']['leaves'].pop()
    elif fault == 'birth-inventory': state['population_snapshot']['birth_inventory'].pop()
    elif fault == 'history-delete': state['removals'].pop()
    elif fault == 'history-order': state['removals'].reverse()
    elif fault == 'history-hash': state['removals_sha256'] = '0' * 64
    elif fault == 'declaration-hash': state['removals'][0]['declaration_sha256'] = '0' * 64
    elif fault == 'last-state': state['removals'][0]['last_leaf_state_sha256'] = '0' * 64
    elif fault == 'receipt-extra': state['removals'][0]['area_to_mass'] = 1
    elif fault == 'state-extra': state['active_leaf_count'] = 999
    else:
        declaration = state['removals'][0]['declaration']
        if fault == 'rehash-action': declaration['action'] = 'natural_senescence'
        elif fault == 'rehash-leaf': declaration['leaf_id'] = 'missing'
        else: declaration['at_elapsed_seconds_exact'] = seconds(1)
        state['removals'][0]['declaration_sha256'] = digest(declaration)
    if fault not in ['history-delete', 'history-order', 'history-hash']:
        state['removals_sha256'] = digest(state['removals'])
    with pytest.raises(LeafRemovalHold): normalize_leaf_removal_state(state=state)


@pytest.mark.parametrize('value', ['', 'x' * 201, '잎-1', True, None])
@pytest.mark.parametrize('key', ['event_id', 'leaf_id'])
def test_bounded_explicit_identity_required(key, value):
    state = initialized()['state']; declaration = event(state, leaves(state)[0]['clock_state']['leaf_id'])
    declaration[key] = value
    with pytest.raises(LeafRemovalHold): apply(state, [declaration])


@pytest.mark.parametrize('fault', ['action', 'origin', 'schema', 'missing', 'not-record', 'unreduced', 'zero-denominator', 'integer-time'])
def test_closed_declaration_and_exact_time_domain(fault):
    state = initialized()['state']; declaration = event(state, leaves(state)[0]['clock_state']['leaf_id'])
    if fault == 'action': declaration['action'] = 'remove_half_leaf'
    elif fault == 'origin': declaration['origin'] = 'observed'
    elif fault == 'schema': declaration['schema_version'] = 'leaf-birth-event-v1'
    elif fault == 'missing': declaration.pop('action')
    elif fault == 'not-record': declaration = []
    elif fault == 'integer-time': declaration['at_elapsed_seconds_exact'] = 86400
    else: declaration['at_elapsed_seconds_exact'] = {'numerator': '172800', 'denominator': '0' if fault == 'zero-denominator' else '2', 'unit': 's'}
    with pytest.raises(LeafRemovalHold): apply(state, [declaration])


@pytest.mark.parametrize('fault', ['init-extra', 'apply-extra', 'input-id', 'not-events', 'not-state', 'nan', 'non-json', 'cycle', 'oversized'])
def test_input_schema_json_and_size_fences(fault):
    state = initialized()['state']; inputs = {'input_id': 'fence', 'state': state, 'events': []}
    if fault == 'init-extra':
        with pytest.raises(LeafRemovalHold): initialize_leaf_removal(inputs={'input_id': 'fence', 'population_state': state['population_snapshot'], 'tenant_id': 'invented'})
        return
    if fault == 'apply-extra': inputs['forcing'] = []
    elif fault == 'input-id': inputs['input_id'] = True
    elif fault == 'not-events': inputs['events'] = {}
    elif fault == 'not-state': inputs['state'] = None
    elif fault == 'nan': inputs['unexpected'] = float('nan')
    elif fault == 'non-json': inputs['unexpected'] = {1, 2}
    elif fault == 'cycle': inputs['unexpected'] = inputs
    elif fault == 'oversized': inputs['unexpected'] = 'x' * (2 * 1024 ** 2)
    with pytest.raises(LeafRemovalHold): apply_leaf_removals(inputs=inputs)


def test_output_mutation_never_changes_input_events_or_snapshot():
    state = initialized()['state']; record = event(state, leaves(state)[0]['clock_state']['leaf_id'])
    before = deepcopy((state, record)); result = apply(state, [record])
    result['state']['population_snapshot']['initial_inventory_state']['leaves'].clear()
    result['state']['removals'][0]['declaration']['at_elapsed_seconds_exact']['numerator'] = '999'
    assert (state, record) == before


def test_512_small_initial_leaves_all_removed_and_513_parent_hold():
    initialization = example()['initialization']; prototype = initialization['initial_inventory']['leaves'][0]
    initialization['initial_inventory']['leaves'] = []
    for i in range(512):
        record = deepcopy(prototype); record['attachment_internode_id'] = 'internode-' + str(i)
        record['initialization']['clock_state']['leaf_id'] = 'leaf-' + str(i)
        initialization['initial_inventory']['leaves'].append(record)
    snapshot = population.initialize_leaf_population(inputs=initialization)['state']
    state = initialize_leaf_removal(inputs={'input_id': 'capacity', 'population_state': snapshot})['state']
    result = apply(state, [event(state, 'leaf-' + str(i), 'remove-' + str(i)) for i in range(512)])
    assert result['active_leaf_count'] == 0 and result['removed_leaf_count'] == 512
    record = deepcopy(prototype); record['initialization']['clock_state']['leaf_id'] = 'overflow'
    initialization['initial_inventory']['leaves'].append(record)
    with pytest.raises(population.LeafPopulationHold): population.initialize_leaf_population(inputs=initialization)
    with pytest.raises(LeafRemovalHold): apply(state, [event(state, 'leaf-0')] * 513)


def test_removal_and_normalization_never_advance_any_clock_or_population(monkeypatch):
    state = initialized()['state']
    def forbidden(*args, **kwargs):
        raise AssertionError('point removal cannot advance growth or forcing')
    for module, name in [(population, 'advance_leaf_population'), (population.inventory, 'advance_leaf_inventory'),
                         (population.leaf, 'advance_rational_leaf_area'), (population.leaf, 'advance_leaf_thermal_clock'),
                         (population.births, 'create_declared_leaves')]:
        monkeypatch.setattr(module, name, forbidden)
    result = apply(state, [event(state, leaves(state)[0]['clock_state']['leaf_id'])])
    assert normalize_leaf_removal_state(state=result['state']) == result['state']
