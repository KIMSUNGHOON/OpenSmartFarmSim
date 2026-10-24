from copy import deepcopy
from decimal import Decimal, localcontext
from fractions import Fraction
from hashlib import sha256
import json

import pytest

from app import crop_leaf_removal_timeline as model
from app import crop_rational_leaf_area as leaf
from test_crop_rational_leaf_area import REFERENCE, seconds


def rational(record):
    return Fraction(int(record['numerator']), int(record['denominator']))


def declaration(state, at):
    clock = state['clock_state']
    return {'schema_version': 'declared-whole-leaf-removal-event-v1', 'origin': 'synthetic',
            'action': 'remove_whole_leaf', 'event_id': 'explicit-removal', 'leaf_id': clock['leaf_id'],
            'time_origin_utc': clock['time_origin_utc'], 'at_elapsed_seconds_exact': seconds(at)}


def initialized(case, at):
    initial = leaf.initialize_rational_leaf_area(inputs=deepcopy(case['initialization']))['state']
    removal = None if at is None else declaration(initial, at)
    return model.initialize_leaf_removal_timeline(inputs={'input_id': 'timeline-init', 'leaf_state': initial, 'removal': removal})


def advance(state, segments):
    return model.advance_leaf_removal_timeline(inputs={'input_id': 'timeline-step', 'state': state, 'segments': segments})


def clipped(segments, start, end):
    return [{**s, 'start_elapsed_seconds_exact': seconds(max(start, rational(s['start_elapsed_seconds_exact']))),
             'end_elapsed_seconds_exact': seconds(min(end, rational(s['end_elapsed_seconds_exact'])))}
            for s in segments if rational(s['end_elapsed_seconds_exact']) > start and rational(s['start_elapsed_seconds_exact']) < end]


def short_forcing():
    return [{'start_elapsed_seconds_exact': seconds(start), 'end_elapsed_seconds_exact': seconds(end),
             'air_temperature': {'value': temperature, 'unit': 'degC'}}
            for start, end, temperature in [(0, 11, 22), (11, 23, 18), (23, 41, 27)]]


def digest(value):
    return sha256(json.dumps(value, sort_keys=True, separators=(',', ':'), allow_nan=False).encode()).hexdigest()


@pytest.mark.parametrize('case', REFERENCE['cases'], ids=lambda value: value['case_id'])
def test_removal_at_forcing_end_preserves_independent_exact_age_and_area(case):
    end = rational(case['expected_at_seconds_exact']); initial = initialized(case, end)
    before = deepcopy(initial); result = advance(initial['state'], case['segments']); state = result['state']
    assert state['leaf_state']['clock_state']['age_exact'] == case['expected_age_exact']
    assert state['leaf_state']['area_state']['area'] == {'unit': 'm2', 'value': pytest.approx(float(case['expected_area_m2']), rel=1e-12)}
    assert state['leaf_state']['clock_state']['at_elapsed_seconds_exact'] == state['at_elapsed_seconds_exact'] == seconds(end)
    assert result['status'] == 'removed' and result['active_leaf_count'] == 0 and result['removed_leaf_count'] == 1
    assert result['active_leaf_area'] == {'value': 0.0, 'unit': 'm2'}
    assert result['removed_leaf_area'] == result['last_leaf_area'] == state['removal_receipt']['area']
    assert initial == before and model.normalize_leaf_removal_timeline_state(state=state) == state


@pytest.mark.parametrize('case', REFERENCE['cases'], ids=lambda value: value['case_id'])
def test_immediate_removal_initialization_and_later_forcing_do_not_advance_leaf(case, monkeypatch):
    start = rational(case['initialization']['clock_state']['at_elapsed_seconds_exact']); initial = initialized(case, start)
    frozen = deepcopy(initial['state']['leaf_state']); receipt = deepcopy(initial['state']['removal_receipt'])
    def forbidden(*args, **kwargs):
        raise AssertionError('removed leaf cannot advance')
    monkeypatch.setattr(leaf, 'advance_rational_leaf_area', forbidden)
    result = advance(initial['state'], case['segments'])
    assert result['state']['leaf_state'] == frozen and result['state']['removal_receipt'] == receipt
    assert result['state']['at_elapsed_seconds_exact'] == case['expected_at_seconds_exact']
    assert result['removed_leaf_area']['value'] == pytest.approx(float(case['expected_initial_area_m2']), rel=1e-12)


@pytest.mark.parametrize('case', REFERENCE['cases'], ids=lambda value: value['case_id'])
def test_explicit_no_removal_uses_original_reference_without_invented_event(case):
    initial = initialized(case, None); result = advance(initial['state'], case['segments'])
    assert result['status'] == 'active' and result['active_leaf_count'] == 1 and result['removed_leaf_count'] == 0
    assert result['state']['removal_receipt'] is None and result['state']['removal_declaration'] is None
    assert result['active_leaf_area']['value'] == pytest.approx(float(case['expected_area_m2']), rel=1e-12)
    assert result['removed_leaf_area'] == {'value': 0.0, 'unit': 'm2'}
    assert result['state']['leaf_state']['clock_state']['age_exact'] == case['expected_age_exact']


@pytest.mark.parametrize('stop', [Fraction(1, 3), Fraction(37, 5), Fraction(43200), Fraction(86400)])
def test_independent_fractional_cut_and_decimal_sigmoid_with_no_post_removal_age(stop):
    case = deepcopy(REFERENCE['cases'][0]); initial = initialized(case, stop)
    result = advance(initial['state'], case['segments']); current = result['state']['leaf_state']
    age = Fraction(12) * stop / 86400
    assert rational(current['clock_state']['age_exact']) == age
    values = case['initialization']['curve']['values']
    with localcontext() as context:
        context.prec = 90
        a = Decimal(age.numerator) / Decimal(age.denominator)
        maximum, steepness, inflection = [Decimal.from_float(float(values[key]['value'])) for key in ['maximum_area', 'steepness', 'inflection_age']]
        expected = maximum / (Decimal(1) + (-steepness * (a - inflection)).exp())
    assert current['area_state']['area']['value'] == pytest.approx(float(expected), rel=1e-12)
    assert current['clock_state']['at_elapsed_seconds_exact'] == seconds(stop)
    assert result['state']['at_elapsed_seconds_exact'] == seconds(86400)


@pytest.mark.parametrize('stop', [Fraction(0), Fraction(1, 3), Fraction(11), Fraction(17, 3),
                                Fraction(23), Fraction(137, 5), Fraction(41), Fraction(42)])
def test_every_integer_internal_cut_and_fractional_cuts_match_whole_state(stop):
    forcing = short_forcing(); initial = initialized(REFERENCE['cases'][0], stop)['state']
    whole = advance(initial, forcing)
    limit = min(stop, Fraction(41)); age = Fraction(0)
    for segment in clipped(forcing, Fraction(0), limit):
        age += (Fraction(segment['air_temperature']['value']) - 10) * (
            rational(segment['end_elapsed_seconds_exact']) - rational(segment['start_elapsed_seconds_exact'])) / 86400
    assert rational(whole['state']['leaf_state']['clock_state']['age_exact']) == age
    cuts = [*(Fraction(i) for i in range(1, 41)), Fraction(1, 3), Fraction(17, 3), Fraction(37, 5), Fraction(137, 5)]
    for cut in cuts:
        left = advance(initial, clipped(forcing, Fraction(0), cut))
        right = advance(left['state'], clipped(forcing, cut, Fraction(41)))
        assert right['state'] == whole['state'], (stop, cut)
        assert right['active_leaf_area'] == whole['active_leaf_area']
        assert right['removed_leaf_area'] == whole['removed_leaf_area']


def test_future_declaration_is_applied_in_next_window_without_resubmission():
    initial = initialized(REFERENCE['cases'][0], Fraction(42))['state']; forcing = short_forcing()
    extension = {'start_elapsed_seconds_exact': seconds(41), 'end_elapsed_seconds_exact': seconds(43),
                 'air_temperature': {'value': 30, 'unit': 'degC'}}
    first = advance(initial, forcing); assert first['status'] == 'active'
    second = advance(first['state'], [extension]); whole = advance(initial, [*forcing, extension])
    assert second['state'] == whole['state'] and second['status'] == 'removed'
    assert second['state']['leaf_state']['clock_state']['at_elapsed_seconds_exact'] == seconds(42)
    assert second['state']['at_elapsed_seconds_exact'] == seconds(43)


def test_only_active_prefix_reaches_leaf_advance_and_later_forcing_is_not_growth(monkeypatch):
    initial = initialized(REFERENCE['cases'][0], Fraction(11))['state']; forcing = short_forcing()
    for segment in forcing[1:]: segment['air_temperature']['value'] = -50
    original = leaf.advance_rational_leaf_area; calls = []
    def observe(**kwargs):
        calls.append(deepcopy(kwargs['inputs']['segments']))
        return original(**kwargs)
    monkeypatch.setattr(leaf, 'advance_rational_leaf_area', observe)
    removed = advance(initial, forcing)
    assert len(calls) == 1 and calls[0] == forcing[:1]
    assert removed['state']['leaf_state']['clock_state']['at_elapsed_seconds_exact'] == seconds(11)
    extra = [{'start_elapsed_seconds_exact': seconds(41), 'end_elapsed_seconds_exact': seconds(100),
              'air_temperature': {'value': -60, 'unit': 'degC'}}]
    continued = advance(removed['state'], extra)
    assert len(calls) == 1 and continued['state']['leaf_state'] == removed['state']['leaf_state']
    assert continued['state']['removal_receipt'] == removed['state']['removal_receipt']
    assert continued['state']['at_elapsed_seconds_exact'] == seconds(100)


@pytest.mark.parametrize('removed', [False, True])
@pytest.mark.parametrize('fault', ['gap', 'overlap', 'zero', 'unit', 'temperature-bool', 'temperature-nan',
                                 'extra', 'missing', 'empty', '513', 'wrong-start'])
def test_whole_forcing_schema_is_checked_even_after_removal(removed, fault):
    state = initialized(REFERENCE['cases'][0], Fraction(0) if removed else None)['state']; forcing = short_forcing()
    if fault == 'gap': forcing[1]['start_elapsed_seconds_exact'] = seconds(12)
    elif fault == 'overlap': forcing[1]['start_elapsed_seconds_exact'] = seconds(10)
    elif fault == 'zero': forcing[0]['end_elapsed_seconds_exact'] = seconds(0)
    elif fault == 'unit': forcing[-1]['air_temperature']['unit'] = 'K'
    elif fault == 'temperature-bool': forcing[-1]['air_temperature']['value'] = True
    elif fault == 'temperature-nan': forcing[-1]['air_temperature']['value'] = float('nan')
    elif fault == 'extra': forcing[-1]['PAR'] = 100
    elif fault == 'missing': forcing[-1].pop('air_temperature')
    elif fault == 'empty': forcing = []
    elif fault == '513': forcing *= 171
    elif fault == 'wrong-start': forcing[0]['start_elapsed_seconds_exact'] = seconds(1)
    original = deepcopy(state)
    with pytest.raises(model.LeafRemovalTimelineHold): advance(state, forcing)
    assert state == original


def test_below_base_is_rejected_while_leaf_is_active():
    state = initialized(REFERENCE['cases'][0], Fraction(11))['state']; forcing = short_forcing()
    forcing[0]['air_temperature']['value'] = 9
    with pytest.raises(model.LeafRemovalTimelineHold, match='THERMAL_DOMAIN_HOLD'): advance(state, forcing)


@pytest.mark.parametrize('fault', ['model', 'initial-hash', 'declaration-hash', 'changed-declaration', 'global-before-last',
                                 'missing-receipt', 'receipt-hash', 'receipt-extra', 'receipt-area', 'current-after-removal',
                                 'source-extra', 'state-extra'])
def test_source_declaration_checkpoint_and_receipt_fences(fault):
    initial = initialized(REFERENCE['cases'][0], Fraction(11))['state']; state = advance(initial, short_forcing())['state']
    if fault == 'model': state['model_version'] = 'declared-leaf-removal-point-research-v1'
    elif fault == 'initial-hash': state['initial_leaf_state_sha256'] = '0' * 64
    elif fault == 'declaration-hash': state['removal_declaration_sha256'] = '0' * 64
    elif fault == 'changed-declaration': state['removal_declaration']['event_id'] = 'different'
    elif fault == 'global-before-last': state['at_elapsed_seconds_exact'] = seconds(10)
    elif fault == 'missing-receipt': state['removal_receipt'] = None
    elif fault == 'receipt-hash': state['removal_receipt']['last_leaf_state_sha256'] = '0' * 64
    elif fault == 'receipt-extra': state['removal_receipt']['prediction'] = True
    elif fault == 'receipt-area': state['removal_receipt']['area']['value'] = 0.0
    elif fault == 'current-after-removal':
        state['leaf_state'] = leaf.advance_rational_leaf_area(inputs={'input_id': 'forged-after-removal',
            'state': state['leaf_state'], 'segments': [{'start_elapsed_seconds_exact': seconds(11),
            'end_elapsed_seconds_exact': seconds(12), 'air_temperature': {'value': 22, 'unit': 'degC'}}]})['state']
        state['removal_receipt']['last_leaf_state_sha256'] = digest(state['leaf_state'])
        state['removal_receipt']['area'] = deepcopy(state['leaf_state']['area_state']['area'])
    elif fault == 'source-extra': state['initial_leaf_state']['pruning'] = 'unreviewed'
    elif fault == 'state-extra': state['active_leaf_count'] = 99
    with pytest.raises(model.LeafRemovalTimelineHold): model.normalize_leaf_removal_timeline_state(state=state)


@pytest.mark.parametrize('fault', ['wrong-leaf', 'wrong-origin', 'past', 'wrong-action', 'not-event', 'missing-event', 'unreduced'])
def test_initial_removal_must_be_same_existing_leaf_and_exact_nonpast_scope(fault):
    initial = leaf.initialize_rational_leaf_area(inputs=deepcopy(REFERENCE['cases'][0]['initialization']))['state']
    source = leaf.advance_rational_leaf_area(inputs={'input_id': 'warm-source', 'state': initial,
        'segments': [{'start_elapsed_seconds_exact': seconds(0), 'end_elapsed_seconds_exact': seconds(100),
                      'air_temperature': {'value': 30, 'unit': 'degC'}}]})['state']
    removal = declaration(source, Fraction(101))
    if fault == 'wrong-leaf': removal['leaf_id'] = 'other'
    elif fault == 'wrong-origin': removal['time_origin_utc'] = '2026-10-02T00:00:00Z'
    elif fault == 'past': removal['at_elapsed_seconds_exact'] = seconds(99)
    elif fault == 'wrong-action': removal['action'] = 'predict_senescence'
    elif fault == 'not-event': removal = False
    elif fault == 'missing-event': removal.pop('leaf_id')
    elif fault == 'unreduced': removal['at_elapsed_seconds_exact'] = {'numerator': '202', 'denominator': '2', 'unit': 's'}
    with pytest.raises(model.LeafRemovalTimelineHold):
        model.initialize_leaf_removal_timeline(inputs={'input_id': 'invalid', 'leaf_state': source, 'removal': removal})


@pytest.mark.parametrize('kind', ['age-reversal', 'instant-growth'])
def test_normalizer_rejects_valid_leaf_state_from_an_incompatible_initial_history(kind):
    initial = leaf.initialize_rational_leaf_area(inputs=deepcopy(REFERENCE['cases'][0]['initialization']))['state']
    def forced(end, temperature):
        return leaf.advance_rational_leaf_area(inputs={'input_id': 'alternative', 'state': initial,
            'segments': [{'start_elapsed_seconds_exact': seconds(0), 'end_elapsed_seconds_exact': seconds(end),
                          'air_temperature': {'value': temperature, 'unit': 'degC'}}]})['state']
    source = forced(100, 30)
    state = model.initialize_leaf_removal_timeline(inputs={'input_id': 'source', 'leaf_state': source, 'removal': None})['state']
    end, temperature = (200, 15) if kind == 'age-reversal' else (100, 40)
    state['leaf_state'] = forced(end, temperature); state['at_elapsed_seconds_exact'] = seconds(end)
    with pytest.raises(model.LeafRemovalTimelineHold): model.normalize_leaf_removal_timeline_state(state=state)


def test_input_output_aliases_and_512_segments():
    case = REFERENCE['cases'][0]; initial = initialized(case, Fraction(777, 2))['state']; before = deepcopy(initial)
    forcing = [{'start_elapsed_seconds_exact': seconds(i), 'end_elapsed_seconds_exact': seconds(i + 1),
                'air_temperature': {'value': 22, 'unit': 'degC'}} for i in range(512)]; original = deepcopy(forcing)
    result = advance(initial, forcing)
    assert result['state']['leaf_state']['clock_state']['at_elapsed_seconds_exact'] == seconds(Fraction(777, 2))
    assert result['state']['at_elapsed_seconds_exact'] == seconds(512)
    result['state']['initial_leaf_state']['clock_state']['base_temperature']['value'] = 0
    result['state']['removal_declaration']['event_id'] = 'mutated-output'
    assert initial == before and forcing == original


@pytest.mark.parametrize('fault', ['init-extra', 'advance-extra', 'input-id', 'not-state', 'non-json', 'cycle', 'oversized'])
def test_closed_input_and_bounded_json(fault):
    state = initialized(REFERENCE['cases'][0], None)['state']; inputs = {'input_id': 'bound', 'state': state, 'segments': short_forcing()}
    if fault == 'init-extra':
        with pytest.raises(model.LeafRemovalTimelineHold):
            model.initialize_leaf_removal_timeline(inputs={'input_id': 'bad', 'leaf_state': state['leaf_state'], 'removal': None, 'yield': 1})
        return
    if fault == 'advance-extra': inputs['new_leaf'] = []
    elif fault == 'input-id': inputs['input_id'] = True
    elif fault == 'not-state': inputs['state'] = None
    elif fault == 'non-json': inputs['unexpected'] = {1, 2}
    elif fault == 'cycle': inputs['unexpected'] = inputs
    elif fault == 'oversized': inputs['unexpected'] = 'x' * (2 * 1024 ** 2)
    with pytest.raises(model.LeafRemovalTimelineHold): model.advance_leaf_removal_timeline(inputs=inputs)
