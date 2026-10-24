from copy import deepcopy
from decimal import Decimal, localcontext
from fractions import Fraction
from hashlib import sha256
import json

import pytest

from app import crop_leaf_removal_inventory as model
from app import crop_rational_leaf_area as leaf
from app import crop_leaf_population as population
from test_crop_leaf_population import REFERENCE, example, advance as source_advance, states, clipped, fraction
from test_crop_rational_leaf_area import seconds


def source(index=0):
    return source_advance(example(index))['state']


def declared(snapshot, offsets):
    at = fraction(snapshot['at_elapsed_seconds_exact'])
    return [{'schema_version': 'declared-whole-leaf-removal-event-v1', 'origin': 'synthetic',
             'action': 'remove_whole_leaf', 'event_id': 'remove-' + str(i),
             'leaf_id': item['clock_state']['leaf_id'], 'time_origin_utc': snapshot['time_origin_utc'],
             'at_elapsed_seconds_exact': seconds(at + offset)}
            for i, (item, offset) in enumerate(zip(states({'state': snapshot}), offsets)) if offset is not None]


def initialize(snapshot, removals):
    return model.initialize_leaf_removal_inventory(inputs={'input_id': 'inventory-init',
        'population_state': snapshot, 'removals': removals})


def advance(state, segments):
    return model.advance_leaf_removal_inventory(inputs={'input_id': 'inventory-step', 'state': state, 'segments': segments})


def forcing(snapshot):
    at = fraction(snapshot['at_elapsed_seconds_exact'])
    return [{'start_elapsed_seconds_exact': seconds(at + start), 'end_elapsed_seconds_exact': seconds(at + end),
             'air_temperature': {'value': temperature, 'unit': 'degC'}}
            for start, end, temperature in [(0, 11, 22), (11, 23, 18), (23, 41, 27)]]


def expected(current, segments, stop):
    clock = current['clock_state']; age = fraction(clock['age_exact'])
    base = Fraction.from_float(float(clock['base_temperature']['value']))
    for segment in clipped(segments, fraction(clock['at_elapsed_seconds_exact']), stop):
        duration = fraction(segment['end_elapsed_seconds_exact']) - fraction(segment['start_elapsed_seconds_exact'])
        age += (Fraction.from_float(float(segment['air_temperature']['value'])) - base) * duration / 86400
    with localcontext() as context:
        context.prec = 100
        a = Decimal(age.numerator) / Decimal(age.denominator)
        values = current['area_state']['curve']['values']
        maximum, k, midpoint = [Decimal.from_float(float(values[key]['value']))
                               for key in ['maximum_area', 'steepness', 'inflection_age']]
        area = maximum / (1 + (-k * (a - midpoint)).exp())
    return age, area


@pytest.mark.parametrize('index', range(len(REFERENCE['cases'])))
def test_existing_initial_and_already_born_leaves_keep_independent_ages_areas_and_source(index):
    snapshot = source(index); original = deepcopy(snapshot); segments = forcing(snapshot)
    offsets = [Fraction(0), Fraction(1, 3), Fraction(11), Fraction(23), Fraction(41), Fraction(42)]
    removals = declared(snapshot, offsets); initial = initialize(snapshot, removals)
    before = deepcopy(initial); result = advance(initial['state'], segments); current = result['state']
    end = fraction(segments[-1]['end_elapsed_seconds_exact']); start = fraction(snapshot['at_elapsed_seconds_exact'])
    live = []; removed = []; live_ids = []; removed_ids = []
    for item, record, offset in zip(states({'state': snapshot}), current['leaf_checkpoints'], offsets):
        stop = min(end, start + offset); age, area = expected(item, segments, stop)
        assert fraction(record['state']['clock_state']['age_exact']) == age
        assert record['state']['clock_state']['at_elapsed_seconds_exact'] == seconds(stop)
        assert record['state']['area_state']['area']['value'] == pytest.approx(float(area), rel=1e-12)
        identifier = item['clock_state']['leaf_id']
        if start + offset <= end:
            removed.append(area); removed_ids.append(identifier)
            assert record['removal_receipt']['area'] == record['state']['area_state']['area']
        else:
            live.append(area); live_ids.append(identifier); assert record['removal_receipt'] is None
    assert result['active_leaf_count'] == len(live) and result['removed_leaf_count'] == len(removed)
    assert result['tracked_leaf_count'] == len(live) + len(removed)
    assert result['active_leaf_ids'] == live_ids and result['removed_leaf_ids'] == removed_ids
    assert result['active_leaf_area']['value'] == pytest.approx(float(sum(live)), rel=1e-12)
    assert result['removed_leaf_area']['value'] == pytest.approx(float(sum(removed)), rel=1e-12)
    assert result['last_tracked_leaf_area']['value'] == pytest.approx(float(sum(live + removed)), rel=1e-12)
    assert current['source_population'] == snapshot == original and initial == before
    assert model.normalize_leaf_removal_inventory_state(state=current) == current
    assert (result['scope'], result['claim_scope'], result['gates']) == ('software_research_only', 'synthetic_crop_math_only', 'not_assessed')


@pytest.mark.parametrize('index', range(len(REFERENCE['cases'])))
def test_explicit_empty_removal_list_matches_original_population_advance_without_births(index):
    snapshot = source(index); segments = forcing(snapshot)
    original = population.advance_leaf_population(inputs={'input_id': 'original', 'state': snapshot,
                                                          'segments': segments, 'births': []})
    result = advance(initialize(snapshot, [])['state'], segments)
    assert [record['state'] for record in result['state']['leaf_checkpoints']] == states(original)
    assert result['active_leaf_area'] == original['tracked_leaf_area']
    assert result['removed_leaf_area'] == {'value': 0.0, 'unit': 'm2'}


def test_all_removed_at_source_keep_last_states_while_global_time_advances_without_leaf_calls(monkeypatch):
    snapshot = source(); initial = initialize(snapshot, declared(snapshot, [0] * 512))
    frozen = deepcopy(initial['state']['leaf_checkpoints'])
    def forbidden(*args, **kwargs):
        raise AssertionError('a removed leaf cannot advance')
    monkeypatch.setattr(leaf, 'advance_rational_leaf_area', forbidden)
    result = advance(initial['state'], forcing(snapshot))
    assert result['state']['leaf_checkpoints'] == frozen and result['active_leaf_ids'] == []
    assert result['active_leaf_area'] == {'value': 0.0, 'unit': 'm2'}
    assert result['state']['at_elapsed_seconds_exact'] == forcing(snapshot)[-1]['end_elapsed_seconds_exact']


@pytest.mark.parametrize('offsets', [[None] * 6, [0] * 6, [11] * 6,
                                  [Fraction(1, 3), 11, 11, 23, 41, 42]])
def test_all_integer_and_selected_fractional_partition_resumptions_match_whole_state(offsets):
    snapshot = source(); start = fraction(snapshot['at_elapsed_seconds_exact']); segments = forcing(snapshot)
    initial = initialize(snapshot, declared(snapshot, offsets))['state']; whole = advance(initial, segments)
    cuts = [Fraction(i) for i in range(1, 41)] + [Fraction(1, 3), Fraction(37, 5), Fraction(137, 5), Fraction(122, 3)]
    for offset in cuts:
        left = advance(initial, clipped(segments, start, start + offset))
        right = advance(left['state'], clipped(segments, start + offset, start + 41))
        assert right['state'] == whole['state']
        assert right['active_leaf_area'] == whole['active_leaf_area'] and right['removed_leaf_area'] == whole['removed_leaf_area']


def digest(value):
    return sha256(json.dumps(value, sort_keys=True, separators=(',', ':'), allow_nan=False).encode()).hexdigest()


def test_unhashable_leaf_identity_is_a_domain_hold_without_mutating_source():
    snapshot = source(); original = deepcopy(snapshot); removals = declared(snapshot, [0])
    removals[0]['leaf_id'] = []
    with pytest.raises(model.LeafRemovalInventoryHold): initialize(snapshot, removals)
    assert snapshot == original


@pytest.mark.parametrize('fault', ['none', 'tuple', 'unknown', 'duplicate-leaf', 'duplicate-event', 'past',
                                  'wrong-origin', 'extra', 'wrong-unit', 'not-reduced', 'boolean', 'nan', 'too-many'])
def test_invalid_declarations_hold_atomically(fault):
    snapshot = source(); original = deepcopy(snapshot); removals = declared(snapshot, [0, 11])
    if fault == 'none': removals = None
    elif fault == 'tuple': removals = tuple(removals)
    elif fault == 'unknown': removals[0]['leaf_id'] = 'not-yet-born'
    elif fault == 'duplicate-leaf': removals[1]['leaf_id'] = removals[0]['leaf_id']
    elif fault == 'duplicate-event': removals[1]['event_id'] = removals[0]['event_id']
    elif fault == 'past': removals[0]['at_elapsed_seconds_exact'] = seconds(1)
    elif fault == 'wrong-origin': removals[0]['time_origin_utc'] = '2026-10-02T00:00:00Z'
    elif fault == 'extra': removals[0]['suggested'] = True
    elif fault == 'wrong-unit': removals[0]['at_elapsed_seconds_exact']['unit'] = 'day'
    elif fault == 'not-reduced': removals[0]['at_elapsed_seconds_exact'].update(numerator='2', denominator='2')
    elif fault == 'boolean': removals[0]['at_elapsed_seconds_exact']['numerator'] = True
    elif fault == 'nan': removals[0]['at_elapsed_seconds_exact']['numerator'] = float('nan')
    elif fault == 'too-many': removals *= 257
    before = deepcopy(removals)
    with pytest.raises(model.LeafRemovalInventoryHold): initialize(snapshot, removals)
    assert snapshot == original
    if fault != 'nan': assert removals == before


@pytest.mark.parametrize('fault', ['source-sha', 'source-history', 'source-attachment', 'declarations-sha',
                                  'declaration-removed', 'missing', 'extra', 'reordered', 'wrong-clock',
                                  'early-global', 'unadvanced-global', 'live-receipt', 'missing-receipt',
                                  'last-state-sha', 'receipt-area', 'extra-receipt-key', 'extra-checkpoint-key', 'extra-state-key'])
def test_changed_source_history_current_clocks_and_last_removal_receipts_hold(fault):
    snapshot = source(); state = advance(initialize(snapshot, declared(snapshot, [0, 11]))['state'], forcing(snapshot))['state']
    if fault == 'source-sha': state['source_population_sha256'] = '0' * 64
    elif fault == 'source-history':
        state['source_population']['birth_inventory'].clear()
        state['source_population_sha256'] = digest(state['source_population'])
    elif fault == 'source-attachment': state['source_population']['initial_inventory_state']['leaves'][0]['attachment_internode_id'] = 'other'
    elif fault == 'declarations-sha': state['removal_declarations_sha256'] = '0' * 64
    elif fault == 'declaration-removed': state['removal_declarations'].pop()
    elif fault == 'missing': state['leaf_checkpoints'].pop()
    elif fault == 'extra': state['leaf_checkpoints'].append(deepcopy(state['leaf_checkpoints'][0]))
    elif fault == 'reordered': state['leaf_checkpoints'].reverse()
    elif fault == 'wrong-clock': state['leaf_checkpoints'][0]['state']['clock_state']['leaf_id'] = 'other'
    elif fault == 'early-global': state['at_elapsed_seconds_exact'] = seconds(0)
    elif fault == 'unadvanced-global': state['at_elapsed_seconds_exact'] = seconds(86500)
    elif fault == 'live-receipt': state['leaf_checkpoints'][-1]['removal_receipt'] = deepcopy(state['leaf_checkpoints'][0]['removal_receipt'])
    elif fault == 'missing-receipt': state['leaf_checkpoints'][0]['removal_receipt'] = None
    elif fault == 'last-state-sha': state['leaf_checkpoints'][0]['removal_receipt']['last_leaf_state_sha256'] = '0' * 64
    elif fault == 'receipt-area': state['leaf_checkpoints'][0]['removal_receipt']['area']['value'] *= 2
    elif fault == 'extra-receipt-key': state['leaf_checkpoints'][0]['removal_receipt']['other'] = True
    elif fault == 'extra-checkpoint-key': state['leaf_checkpoints'][0]['prediction'] = True
    elif fault == 'extra-state-key': state['external'] = True
    before = deepcopy(state)
    with pytest.raises(model.LeafRemovalInventoryHold): model.normalize_leaf_removal_inventory_state(state=state)
    assert state == before


@pytest.mark.parametrize('all_removed', [True, False])
@pytest.mark.parametrize('fault', ['gap', 'unit', 'nan', 'boolean', 'empty', '513', 'extra', 'below-base'])
def test_forcing_is_validated_even_when_no_active_leaves_remain(all_removed, fault):
    snapshot = source(); state = initialize(snapshot, declared(snapshot, [0] * 512) if all_removed else [])['state']
    segments = forcing(snapshot)
    if fault == 'gap': segments[1]['start_elapsed_seconds_exact'] = seconds(86412)
    elif fault == 'unit': segments[0]['air_temperature']['unit'] = 'K'
    elif fault == 'nan': segments[0]['air_temperature']['value'] = float('nan')
    elif fault == 'boolean': segments[0]['air_temperature']['value'] = True
    elif fault == 'empty': segments = []
    elif fault == '513': segments *= 171
    elif fault == 'extra': segments[0]['source'] = 'unreviewed'
    elif fault == 'below-base': segments[0]['air_temperature']['value'] = 0
    before = deepcopy(state)
    if all_removed and fault == 'below-base':
        assert advance(state, segments)['state']['leaf_checkpoints'] == state['leaf_checkpoints']
    else:
        with pytest.raises(model.LeafRemovalInventoryHold): advance(state, segments)
    assert state == before


def test_pending_last_leaf_removal_in_next_window_and_simultaneous_boundary_do_not_create_births(monkeypatch):
    snapshot = source(); at = fraction(snapshot['at_elapsed_seconds_exact']); segments = forcing(snapshot)
    initial = initialize(snapshot, declared(snapshot, [11, 11, 11, 23, 41, 42]))['state']
    def forbidden(*args, **kwargs):
        raise AssertionError('new births and old population advancement are outside this operation')
    monkeypatch.setattr(population, 'advance_leaf_population', forbidden)
    monkeypatch.setattr(model.point.births, 'create_declared_leaves', forbidden)
    left = advance(initial, segments)
    assert left['active_leaf_count'] == 1
    next_segment = {'start_elapsed_seconds_exact': seconds(at + 41), 'end_elapsed_seconds_exact': seconds(at + 43),
                    'air_temperature': {'value': 23, 'unit': 'degC'}}
    right = advance(left['state'], [next_segment]); whole = advance(initial, [*segments, next_segment])
    assert right['state'] == whole['state'] and right['active_leaf_count'] == 0
    assert right['state']['leaf_checkpoints'][-1]['state']['clock_state']['at_elapsed_seconds_exact'] == seconds(at + 42)


def test_input_output_are_independent_and_ordered_declarations_are_retained():
    snapshot = source(); removals = list(reversed(declared(snapshot, [11, 11, 23])))
    inputs = {'input_id': 'alias', 'population_state': snapshot, 'removals': removals}; before = deepcopy(inputs)
    result = model.initialize_leaf_removal_inventory(inputs=inputs)
    assert result['state']['removal_declarations'] == removals
    normalized = model.normalize_leaf_removal_inventory_state(state=result['state'])
    normalized['leaf_checkpoints'][0]['state']['clock_anchor']['leaf_id'] = 'changed'
    assert result['state']['leaf_checkpoints'][0]['state']['clock_anchor']['leaf_id'] != 'changed'
    result['state']['source_population']['birth_inventory'].clear()
    result['state']['removal_declarations'][0]['event_id'] = 'changed'
    assert inputs == before


@pytest.mark.parametrize('operation', ['initialize', 'advance', 'normalize'])
@pytest.mark.parametrize('fault', ['non-json', 'cycle', '2MiB'])
def test_non_json_cycles_and_payload_byte_limit_hold(operation, fault):
    snapshot = source(); state = initialize(snapshot, [])['state']
    value = {'input_id': 'bounded', 'population_state': snapshot, 'removals': []} if operation == 'initialize' else (
        {'input_id': 'bounded', 'state': state, 'segments': forcing(snapshot)} if operation == 'advance' else state)
    if fault == 'non-json': value['unsupported'] = object()
    elif fault == 'cycle': value['unsupported'] = value
    else: value['unsupported'] = 'x' * (2 * 1024**2)
    with pytest.raises(model.LeafRemovalInventoryHold):
        if operation == 'initialize': model.initialize_leaf_removal_inventory(inputs=value)
        elif operation == 'advance': model.advance_leaf_removal_inventory(inputs=value)
        else: model.normalize_leaf_removal_inventory_state(state=value)


def test_512_forcing_segments_and_next_513_rejection():
    snapshot = source(); at = fraction(snapshot['at_elapsed_seconds_exact']); initial = initialize(snapshot, [])['state']
    segments = [{'start_elapsed_seconds_exact': seconds(at + i), 'end_elapsed_seconds_exact': seconds(at + i + 1),
                 'air_temperature': {'value': 22, 'unit': 'degC'}} for i in range(513)]
    result = advance(initial, segments[:512])
    assert result['state']['at_elapsed_seconds_exact'] == seconds(at + 512)
    with pytest.raises(model.LeafRemovalInventoryHold): advance(initial, segments)


def large_source(count):
    inputs = deepcopy(REFERENCE['cases'][0]['initialization']); template = inputs['initial_inventory']['leaves'][0]
    records = []
    for i in range(count):
        item = deepcopy(template); item['initialization']['clock_state']['leaf_id'] = 'leaf-' + str(i); records.append(item)
    inputs['initial_inventory']['leaves'] = records
    return population.initialize_leaf_population(inputs=inputs)['state']


@pytest.mark.parametrize('count', [1, 256, 512])
def test_bounded_existing_leaf_counts_are_accepted_and_advanced(count):
    snapshot = large_source(count); initial = initialize(snapshot, [])
    result = advance(initial['state'], forcing(snapshot))
    assert result['tracked_leaf_count'] == result['active_leaf_count'] == count
    assert result['state']['source_population'] == snapshot
    assert len(json.dumps(result, separators=(',', ':')).encode()) <= 2 * 1024**2
    assert result['active_leaf_area']['value'] == pytest.approx(
        count * result['state']['leaf_checkpoints'][0]['state']['area_state']['area']['value'], rel=1e-12)


def test_513_source_count_and_512_removal_output_byte_limit_hold_atomically():
    snapshot = large_source(512); before = deepcopy(snapshot)
    with pytest.raises(model.LeafRemovalInventoryHold, match='2MiB'):
        initialize(snapshot, declared(snapshot, [0] * 512))
    assert snapshot == before
    snapshot['initial_inventory_state']['leaves'].append(deepcopy(snapshot['initial_inventory_state']['leaves'][0]))
    with pytest.raises(model.LeafRemovalInventoryHold, match='512'): initialize(snapshot, [])


def test_256_immediate_removals_keep_all_ids_and_accept_empty_active_inventory():
    snapshot = large_source(256); initial = initialize(snapshot, declared(snapshot, [0] * 256))
    result = advance(initial['state'], forcing(snapshot))
    assert result['active_leaf_count'] == 0 and result['removed_leaf_count'] == 256
    assert len(set(result['removed_leaf_ids'])) == 256 and result['active_leaf_ids'] == []
    assert result['state']['leaf_checkpoints'] == initial['state']['leaf_checkpoints']


def test_normalization_cannot_expand_an_accepted_raw_payload_past_output_byte_limit():
    original = initialize(large_source(512), [])['state']
    def convert(value, padding, integers):
        if isinstance(value, dict): return {k: convert(v, padding, integers) for k, v in value.items()}
        if isinstance(value, list): return [convert(v, padding, integers) for v in value]
        if isinstance(value, str) and value.startswith('leaf-') and value[5:].isdigit():
            return 'X' * padding + ('Y' * 64 if value == 'leaf-0' else '') + value
        if integers and type(value) is float and value.is_integer(): return int(value)
        return value
    found = None
    for padding in range(32):
        canonical = convert(original, padding, False)
        canonical['source_population_sha256'] = digest(canonical['source_population'])
        raw = convert(canonical, 0, True)
        raw_bytes = len(json.dumps(raw, sort_keys=True, separators=(',', ':')).encode())
        canonical_bytes = len(json.dumps(canonical, sort_keys=True, separators=(',', ':')).encode())
        if raw_bytes <= 2 * 1024**2 < canonical_bytes:
            found = raw; break
    assert found is not None, 'the test must exercise the input/output size boundary'
    with pytest.raises(model.LeafRemovalInventoryHold, match='2MiB'):
        model.normalize_leaf_removal_inventory_state(state=found)
