from copy import deepcopy
from decimal import Decimal
from fractions import Fraction
from hashlib import sha256
import json

import pytest

from app import crop_leaf_lifecycle as model
from app import crop_leaf_population as population
from app import crop_rational_leaf_area as leaf
from test_crop_leaf_population import REFERENCE, example, advance as original_advance, states, clipped, fraction
from test_crop_leaf_removal_inventory import expected
from test_crop_rational_leaf_area import seconds


def source(case):
    return population.initialize_leaf_population(inputs=case['initialization'])['state']


def event(identifier, at, identity):
    return {'schema_version': 'declared-whole-leaf-removal-event-v1', 'origin': 'synthetic',
            'action': 'remove_whole_leaf', 'event_id': identity, 'leaf_id': identifier,
            'time_origin_utc': '2026-10-01T00:00:00Z', 'at_elapsed_seconds_exact': seconds(at)}


def initialize(snapshot, births, removals):
    return model.initialize_leaf_lifecycle(inputs={'input_id': 'lifecycle-init', 'population_state': snapshot,
                                                  'births': births, 'removals': removals})


def advance(state, segments):
    return model.advance_leaf_lifecycle(inputs={'input_id': 'lifecycle-step', 'state': state, 'segments': segments})


def current_leaves(result):
    state = result['state']
    return [r['state'] for r in [*state['existing_inventory_state']['leaf_checkpoints'],
                                *state['new_leaf_checkpoints']] if r['state'] is not None]


@pytest.mark.parametrize('index', range(len(REFERENCE['cases'])))
def test_no_removal_matches_original_existing_and_new_leaves_and_independent_reference(index):
    case = example(index); snapshot = source(case); before = deepcopy(case)
    initial = initialize(snapshot, case['births'], []); result = advance(initial['state'], case['segments'])
    assert current_leaves(result) == states(original_advance(case))
    assert result['tracked_leaf_count'] == result['active_leaf_count'] == len(case['expected'])
    assert result['scheduled_birth_count'] == result['emerged_new_leaf_count'] == len(case['births'])
    assert result['pending_leaf_count'] == 0 and result['pending_leaf_ids'] == []
    assert result['active_leaf_area']['value'] == pytest.approx(float(case['expected_sum_m2']), rel=1e-12)
    for current, row in zip(current_leaves(result), case['expected']):
        assert current['clock_state']['age_exact'] == row['age_exact']
        assert current['area_state']['area']['value'] == pytest.approx(float(row['area_m2']), rel=1e-12)
    assert result['state']['existing_inventory_state']['source_population'] == snapshot
    assert model.normalize_leaf_lifecycle_state(state=result['state']) == result['state'] and case == before
    assert (result['scope'], result['claim_scope'], result['gates']) == ('software_research_only', 'synthetic_crop_math_only', 'not_assessed')


def small_case():
    case = example(); template = deepcopy(case['births'][0]); births = []
    for i, at in enumerate([Fraction(1, 3), Fraction(11), Fraction(41), Fraction(42)]):
        births.append({**deepcopy(template), 'leaf_id': 'future-' + str(i), 'emerged_elapsed_seconds_exact': seconds(at)})
    segments = [{'start_elapsed_seconds_exact': seconds(start), 'end_elapsed_seconds_exact': seconds(end),
                 'air_temperature': {'value': temperature, 'unit': 'degC'}}
                for start, end, temperature in [(0, 11, 22), (11, 23, 18), (23, 41, 27)]]
    return source(case), births, segments


def removals_for(snapshot, births, all_initial=True):
    records = [event(item['clock_state']['leaf_id'], Fraction(0), 'existing-' + str(i))
               for i, item in enumerate(states({'state': snapshot}))] if all_initial else []
    records.extend(event(b['leaf_id'], at, 'new-' + str(i)) for i, (b, at) in enumerate(
        zip(births, [Fraction(1, 3), Fraction(23), Fraction(41), Fraction(43)])))
    return records


def test_empty_active_then_births_and_same_instant_removal_preserve_independent_states_and_sums():
    snapshot, births, segments = small_case(); removals = removals_for(snapshot, births)
    initial = initialize(snapshot, births, removals); result = advance(initial['state'], segments)
    assert initial['active_leaf_count'] == 0 and initial['pending_leaf_count'] == 4
    assert result['active_leaf_count'] == 0 and result['pending_leaf_count'] == 1
    assert result['pending_leaf_ids'] == ['future-3'] and result['tracked_leaf_count'] == 6
    assert result['removed_leaf_count'] == 6 and result['emerged_new_leaf_count'] == 3
    total = Decimal(0)
    for current in states({'state': snapshot}): total += Decimal.from_float(current['area_state']['area']['value'])
    for declaration, record, stop in zip(births, result['state']['new_leaf_checkpoints'], [Fraction(1, 3), Fraction(23), Fraction(41)]):
        initialized = population._declared_initialization(declaration, snapshot['time_origin_utc'])
        age, area = expected(initialized, segments, stop); current = record['state']
        assert fraction(current['clock_state']['age_exact']) == age
        assert current['area_state']['area']['value'] == pytest.approx(float(area), rel=1e-12)
        assert current['clock_state']['at_elapsed_seconds_exact'] == seconds(stop)
        assert record['removal_receipt']['area'] == current['area_state']['area']; total += area
    assert result['removed_leaf_area']['value'] == pytest.approx(float(total), rel=1e-12)
    assert result['active_leaf_area'] == {'value': 0.0, 'unit': 'm2'}
    assert result['state']['new_leaf_checkpoints'][-1] == {'state': None, 'removal_receipt': None}


@pytest.mark.parametrize('with_removals', [False, True])
def test_all_integer_and_fractional_splits_keep_same_birth_removal_state(with_removals):
    snapshot, births, segments = small_case(); initial = initialize(snapshot, births, removals_for(snapshot, births) if with_removals else [])['state']
    whole = advance(initial, segments)
    cuts = [Fraction(i) for i in range(1, 41)] + [Fraction(1, 3), Fraction(37, 5), Fraction(137, 5), Fraction(122, 3)]
    for cut in cuts:
        left = advance(initial, clipped(segments, Fraction(0), cut))
        right = advance(left['state'], clipped(segments, cut, Fraction(41)))
        assert right['state'] == whole['state']
        assert right['active_leaf_area'] == whole['active_leaf_area'] and right['removed_leaf_area'] == whole['removed_leaf_area']


def test_birth_after_previous_window_and_last_removal_do_not_recreate_retired_ids():
    snapshot, births, segments = small_case(); initial = initialize(snapshot, births, removals_for(snapshot, births))['state']
    left = advance(initial, segments)
    tail = {'start_elapsed_seconds_exact': seconds(41), 'end_elapsed_seconds_exact': seconds(44),
            'air_temperature': {'value': 22, 'unit': 'degC'}}
    right = advance(left['state'], [tail]); whole = advance(initial, [*segments, tail])
    assert right['state'] == whole['state'] and right['pending_leaf_count'] == right['active_leaf_count'] == 0
    assert right['emerged_new_leaf_count'] == 4 and right['removed_leaf_count'] == 7
    assert right['state']['new_leaf_checkpoints'][-1]['state']['clock_state']['at_elapsed_seconds_exact'] == seconds(43)


@pytest.mark.parametrize('remove_at_birth', [False, True])
def test_birth_at_end_has_no_new_leaf_advance_and_right_window_does_not_duplicate_birth(remove_at_birth, monkeypatch):
    snapshot, births, segments = small_case(); births = [births[2]]
    removals = [event('future-2', Fraction(41), 'same-instant')] if remove_at_birth else []
    initial = initialize(snapshot, births, removals)['state']; calls = []; original = leaf.advance_rational_leaf_area
    def observed(**kw):
        calls.append(kw['inputs']['state']['clock_state']['leaf_id']); return original(**kw)
    monkeypatch.setattr(leaf, 'advance_rational_leaf_area', observed)
    left = advance(initial, segments)
    assert 'future-2' not in calls and left['emerged_new_leaf_count'] == 1
    record = left['state']['new_leaf_checkpoints'][0]
    assert fraction(record['state']['clock_state']['age_exact']) == 0
    right = advance(left['state'], [{'start_elapsed_seconds_exact': seconds(41), 'end_elapsed_seconds_exact': seconds(44),
                                    'air_temperature': {'value': 22, 'unit': 'degC'}}])
    assert calls.count('future-2') == (0 if remove_at_birth else 1)
    assert right['emerged_new_leaf_count'] == 1
    if remove_at_birth: assert right['state']['new_leaf_checkpoints'][0] == record


@pytest.mark.parametrize('fault', ['none', 'tuple', 'duplicate-existing', 'duplicate-new', 'unordered', 'at-source',
                                  'negative', 'unit', 'initial-area', 'extra', 'boolean-ID', 'nan', '513'])
def test_invalid_birth_schedule_holds_without_mutation(fault):
    snapshot, births, _ = small_case(); original = deepcopy(snapshot)
    if fault == 'none': births = None
    elif fault == 'tuple': births = tuple(births)
    elif fault == 'duplicate-existing': births[0]['leaf_id'] = states({'state': snapshot})[0]['clock_state']['leaf_id']
    elif fault == 'duplicate-new': births[1]['leaf_id'] = births[0]['leaf_id']
    elif fault == 'unordered': births.reverse()
    elif fault == 'at-source': births[0]['emerged_elapsed_seconds_exact'] = seconds(0)
    elif fault == 'negative': births[0]['emerged_elapsed_seconds_exact'] = seconds(-1)
    elif fault == 'unit': births[0]['emerged_elapsed_seconds_exact']['unit'] = 'day'
    elif fault == 'initial-area': births[0]['initial_area']['value'] *= 2
    elif fault == 'extra': births[0]['automatic'] = True
    elif fault == 'boolean-ID': births[0]['leaf_id'] = True
    elif fault == 'nan': births[0]['base_temperature']['value'] = float('nan')
    elif fault == '513': births *= 129
    with pytest.raises(model.LeafLifecycleHold): initialize(snapshot, births, [])
    assert snapshot == original


@pytest.mark.parametrize('fault', ['none', 'tuple', 'unknown', 'unhashable-ID', 'duplicate-leaf', 'duplicate-event',
                                  'before-birth', 'negative', 'wrong-origin', 'extra', 'unit', 'noncanonical', '513'])
def test_invalid_removals_include_future_birth_and_event_identity_checks(fault):
    snapshot, births, _ = small_case(); removals = removals_for(snapshot, births)
    if fault == 'none': removals = None
    elif fault == 'tuple': removals = tuple(removals)
    elif fault == 'unknown': removals[0]['leaf_id'] = 'undeclared-future-leaf'
    elif fault == 'unhashable-ID': removals[0]['leaf_id'] = []
    elif fault == 'duplicate-leaf': removals[1]['leaf_id'] = removals[0]['leaf_id']
    elif fault == 'duplicate-event': removals[-1]['event_id'] = removals[0]['event_id']
    elif fault == 'before-birth': removals[3]['at_elapsed_seconds_exact'] = seconds(0)
    elif fault == 'negative': removals[0]['at_elapsed_seconds_exact'] = seconds(-1)
    elif fault == 'wrong-origin': removals[0]['time_origin_utc'] = '2026-10-02T00:00:00Z'
    elif fault == 'extra': removals[0]['reason'] = 'unreviewed'
    elif fault == 'unit': removals[0]['at_elapsed_seconds_exact']['unit'] = 'day'
    elif fault == 'noncanonical': removals[0]['at_elapsed_seconds_exact'].update(numerator='2', denominator='2')
    elif fault == '513': removals *= 74
    before = deepcopy(removals)
    with pytest.raises(model.LeafLifecycleHold): initialize(snapshot, births, removals)
    assert removals == before


@pytest.mark.parametrize('fault', ['birth-hash', 'removal-hash', 'missing-birth', 'birth-order', 'missing-checkpoint',
                                  'extra-checkpoint', 'checkpoint-order', 'pending-state', 'pending-receipt', 'missing-born',
                                  'receipt-sha', 'receipt-area', 'last-clock', 'changed-anchor', 'extra-checkpoint-key',
                                  'extra-state-key', 'base-removal-mismatch', 'time-backwards'])
def test_pending_births_immutable_history_and_removed_checkpoints_reject_mutation(fault):
    snapshot, births, segments = small_case()
    state = advance(initialize(snapshot, births, removals_for(snapshot, births))['state'], segments)['state']
    if fault == 'birth-hash': state['birth_declarations_sha256'] = '0' * 64
    elif fault == 'removal-hash': state['removal_declarations_sha256'] = '0' * 64
    elif fault == 'missing-birth': state['birth_declarations'].pop()
    elif fault == 'birth-order': state['birth_declarations'].reverse()
    elif fault == 'missing-checkpoint': state['new_leaf_checkpoints'].pop()
    elif fault == 'extra-checkpoint': state['new_leaf_checkpoints'].append(deepcopy(state['new_leaf_checkpoints'][0]))
    elif fault == 'checkpoint-order': state['new_leaf_checkpoints'][:2] = reversed(state['new_leaf_checkpoints'][:2])
    elif fault == 'pending-state': state['new_leaf_checkpoints'][-1]['state'] = deepcopy(state['new_leaf_checkpoints'][0]['state'])
    elif fault == 'pending-receipt': state['new_leaf_checkpoints'][-1]['removal_receipt'] = deepcopy(state['new_leaf_checkpoints'][0]['removal_receipt'])
    elif fault == 'missing-born': state['new_leaf_checkpoints'][0]['state'] = None
    elif fault == 'receipt-sha': state['new_leaf_checkpoints'][0]['removal_receipt']['last_leaf_state_sha256'] = '0' * 64
    elif fault == 'receipt-area': state['new_leaf_checkpoints'][0]['removal_receipt']['area']['value'] *= 2
    elif fault == 'last-clock': state['new_leaf_checkpoints'][0]['state']['clock_state']['at_elapsed_seconds_exact'] = seconds(41)
    elif fault == 'changed-anchor': state['new_leaf_checkpoints'][0]['state']['clock_anchor']['leaf_id'] = 'other'
    elif fault == 'extra-checkpoint-key': state['new_leaf_checkpoints'][0]['was_pending'] = True
    elif fault == 'extra-state-key': state['time'] = 41
    elif fault == 'base-removal-mismatch':
        state['removal_declarations'][0]['event_id'] = 'other-event'
        state['removal_declarations_sha256'] = sha256(json.dumps(state['removal_declarations'], sort_keys=True, separators=(',', ':')).encode()).hexdigest()
    elif fault == 'time-backwards': state['existing_inventory_state']['at_elapsed_seconds_exact'] = seconds(0)
    before = deepcopy(state)
    with pytest.raises(model.LeafLifecycleHold): model.normalize_leaf_lifecycle_state(state=state)
    assert state == before


@pytest.mark.parametrize('remove_at_birth', [False, True])
@pytest.mark.parametrize('post_birth_temperature', [0, 22])
def test_below_base_before_birth_does_not_age_pending_leaf_and_after_removal_does_not_advance(remove_at_birth, post_birth_temperature):
    snapshot, births, segments = small_case(); births = [births[1]]
    removals = removals_for(snapshot, [], all_initial=True)
    if remove_at_birth: removals.append(event('future-1', Fraction(11), 'at-emergence'))
    initial = initialize(snapshot, births, removals)['state']
    segments = [deepcopy(segments[0]), {'start_elapsed_seconds_exact': seconds(11), 'end_elapsed_seconds_exact': seconds(23),
                                       'air_temperature': {'value': post_birth_temperature, 'unit': 'degC'}}]
    segments[0]['air_temperature']['value'] = 0
    if post_birth_temperature == 0 and not remove_at_birth:
        with pytest.raises(model.LeafLifecycleHold, match='THERMAL_DOMAIN'): advance(initial, segments)
    else:
        result = advance(initial, segments); current = result['state']['new_leaf_checkpoints'][0]['state']
        assert fraction(current['clock_state']['age_exact']) == (0 if remove_at_birth else Fraction(12 * 12, 86400))
        assert result['at_elapsed_seconds_exact'] == seconds(23)


@pytest.mark.parametrize('fault', ['gap', 'unit', 'nan', 'boolean', 'empty', '513', 'extra', 'start'])
def test_whole_forcing_is_checked_with_only_pending_or_removed_leaves(fault):
    snapshot, births, segments = small_case(); births = [births[-1]]
    initial = initialize(snapshot, births, removals_for(snapshot, [], all_initial=True))['state']
    if fault == 'gap': segments[1]['start_elapsed_seconds_exact'] = seconds(12)
    elif fault == 'unit': segments[0]['air_temperature']['unit'] = 'K'
    elif fault == 'nan': segments[0]['air_temperature']['value'] = float('nan')
    elif fault == 'boolean': segments[0]['air_temperature']['value'] = True
    elif fault == 'empty': segments = []
    elif fault == '513': segments *= 171
    elif fault == 'extra': segments[0]['source'] = 'unreviewed'
    elif fault == 'start': segments[0]['start_elapsed_seconds_exact'] = seconds(1)
    with pytest.raises(model.LeafLifecycleHold): advance(initial, segments)


@pytest.mark.parametrize('operation', ['initialize', 'advance', 'normalize'])
@pytest.mark.parametrize('fault', ['non-json', 'cycle', '2MiB'])
def test_non_json_cycles_and_total_input_byte_limits_hold(operation, fault):
    snapshot, births, segments = small_case(); state = initialize(snapshot, births, [])['state']
    value = {'input_id': 'bounded', 'population_state': snapshot, 'births': births, 'removals': []} if operation == 'initialize' else (
        {'input_id': 'bounded', 'state': state, 'segments': segments} if operation == 'advance' else state)
    value['extra'] = object() if fault == 'non-json' else value if fault == 'cycle' else 'x' * (2 * 1024**2)
    with pytest.raises(model.LeafLifecycleHold):
        if operation == 'initialize': model.initialize_leaf_lifecycle(inputs=value)
        elif operation == 'advance': model.advance_leaf_lifecycle(inputs=value)
        else: model.normalize_leaf_lifecycle_state(state=value)


def test_pending_and_retired_ids_still_consume_capacity_and_512_total_can_emerge_at_end():
    snapshot, births, segments = small_case(); template = births[0]
    births = [{**deepcopy(template), 'leaf_id': 'future-' + str(i), 'emerged_elapsed_seconds_exact': seconds(41)} for i in range(509)]
    initial = initialize(snapshot, births, [])
    assert initial['declared_leaf_count'] == 512 and initial['pending_leaf_count'] == 509 and initial['tracked_leaf_count'] == 3
    result = advance(initial['state'], segments)
    assert result['declared_leaf_count'] == result['tracked_leaf_count'] == result['active_leaf_count'] == 512
    assert result['emerged_new_leaf_count'] == 509 and result['pending_leaf_count'] == 0
    assert model.normalize_leaf_lifecycle_state(state=result['state']) == result['state']
    births.append({**deepcopy(template), 'leaf_id': 'future-extra', 'emerged_elapsed_seconds_exact': seconds(41)})
    with pytest.raises(model.LeafLifecycleHold, match='512'):
        initialize(snapshot, births, removals_for(snapshot, [], all_initial=True))


def test_512_forcing_segments_accept_and_same_time_simultaneous_births_remove_without_growth():
    snapshot, births, _ = small_case(); births = births[:2]
    births[0]['emerged_elapsed_seconds_exact'] = births[1]['emerged_elapsed_seconds_exact'] = seconds(11)
    removals = [event(b['leaf_id'], Fraction(11), 'instant-' + str(i)) for i, b in enumerate(births)]
    initial = initialize(snapshot, births, removals)['state']
    segments = [{'start_elapsed_seconds_exact': seconds(i), 'end_elapsed_seconds_exact': seconds(i + 1),
                 'air_temperature': {'value': 22, 'unit': 'degC'}} for i in range(512)]
    result = advance(initial, segments)
    assert result['at_elapsed_seconds_exact'] == seconds(512) and result['removed_leaf_count'] == 2
    for record in result['state']['new_leaf_checkpoints']:
        assert record['state']['clock_state']['at_elapsed_seconds_exact'] == seconds(11)
        assert fraction(record['state']['clock_state']['age_exact']) == 0


def test_already_born_source_history_and_inputs_outputs_remain_separate():
    case = example(); snapshot = original_advance(case)['state']; declaration = deepcopy(case['births'][0])
    declaration.update(leaf_id='later-new', emerged_elapsed_seconds_exact=seconds(86401))
    inputs = {'input_id': 'already-born', 'population_state': snapshot, 'births': [declaration], 'removals': []}; before = deepcopy(inputs)
    initial = model.initialize_leaf_lifecycle(inputs=inputs)
    result = advance(initial['state'], [{'start_elapsed_seconds_exact': seconds(86400), 'end_elapsed_seconds_exact': seconds(86402),
                                        'air_temperature': {'value': 22, 'unit': 'degC'}}])
    assert result['tracked_leaf_count'] == len(case['expected']) + 1
    assert result['state']['existing_inventory_state']['source_population']['birth_inventory'] == snapshot['birth_inventory']
    normalized = model.normalize_leaf_lifecycle_state(state=result['state'])
    normalized['new_leaf_checkpoints'][0]['state']['clock_anchor']['leaf_id'] = 'changed'
    assert result['state']['new_leaf_checkpoints'][0]['state']['clock_anchor']['leaf_id'] == 'later-new'
    result['state']['birth_declarations'][0]['leaf_id'] = 'changed'
    result['state']['existing_inventory_state']['source_population']['birth_inventory'].clear()
    assert inputs == before
