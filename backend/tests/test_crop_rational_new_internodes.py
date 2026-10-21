from copy import deepcopy
from fractions import Fraction
import json
from pathlib import Path

import pytest

from app.crop_rational_new_internodes import (
    create_rational_internodes_from_shoot_events, rational_air_segments_from_utc, RationalNewInternodeHold,
)
from app.crop_new_internodes import create_internodes_from_shoot_events, NewInternodeHold
from app.crop_rational_internode_length import advance_rational_internode_length
from test_crop_rational_internode_length import exact, reference


ROOT = Path(__file__).resolve().parents[2]
REFERENCE = json.loads((ROOT / 'fixtures/crop-new-internodes-reference-v1.json').read_bytes())
TIMELINE = json.loads((ROOT / 'fixtures/crop-shoot-timeline-reference-v1.json').read_bytes())


def inputs():
    return deepcopy(REFERENCE['cases'][0]['inputs'])


def fractional():
    p = inputs(); case = TIMELINE['cases'][3]['inputs']
    p['timeline_state'] = deepcopy(case['state']); p['segments'] = deepcopy(case['segments'])
    return p


@pytest.mark.parametrize('case', REFERENCE['cases'], ids=lambda c: c['case_id'])
def test_independent_whole_second_programs_and_old_entity_ids(case):
    p = deepcopy(case['inputs']); before = deepcopy(p)
    result = create_rational_internodes_from_shoot_events(inputs=p)
    old = create_internodes_from_shoot_events(inputs=p)
    assert result['timeline_checkpoint'] == old['timeline_checkpoint'] == case['timeline_checkpoint']
    assert len(result['new_internodes']) == len(case['new_internodes'])
    for actual, legacy, expected in zip(result['new_internodes'], old['new_internodes'], case['new_internodes'], strict=True):
        clock = actual['length_state']['clock_state']; old_clock = legacy['length_state']['clock_state']
        assert clock['internode_id'] == old_clock['internode_id']
        assert actual['birth_age_exact'] == expected['birth_age_exact']
        assert clock['age_exact'] == expected['end_age_exact'] == old_clock['age_exact']
        assert actual['length_state']['length'] == legacy['length_state']['length']
        assert actual['length_state']['length']['value'] == pytest.approx(float(expected['end_length_m']), rel=1e-12, abs=0)
        assert clock['time_origin_utc'] == p['timeline_state']['started_at']
    assert p == before and create_rational_internodes_from_shoot_events(inputs=p) == result


def test_fractional_births_are_exact_and_old_adapter_still_holds():
    p = fractional(); before = deepcopy(p)
    result = create_rational_internodes_from_shoot_events(inputs=p)
    assert len(result['new_internodes']) == 3
    for index, node in enumerate(result['new_internodes']):
        clock = node['length_state']['clock_state']; age = Fraction(2 - index, 86400)
        assert clock['emerged_elapsed_seconds_exact'] == exact(index + 1, 3)
        assert clock['at_elapsed_seconds_exact'] == exact(1)
        assert clock['age_exact'] == exact(age, unit='degC_day')
        assert 'emerged_at' not in clock and 'utc_whole_second' not in clock
        assert node['length_state']['length']['value'] == pytest.approx(float(reference(age, p['curve'])), rel=1e-12, abs=0)
        assert (node['advancement_input_sha256'] is None) == (index == 2)
    assert result['model_version'] == 'shoot-rational-new-internodes-research-v1'
    assert result['claim_scope'] == 'synthetic_crop_math_only' and result['gates'] == 'not_assessed'
    assert len(result['input_sha256']) == len(result['timeline_input_sha256']) == 64
    assert p == before
    with pytest.raises(NewInternodeHold, match='SUBSECOND_EMERGENCE_HOLD'):
        create_internodes_from_shoot_events(inputs=p)


def test_fractional_nodes_split_resume_keep_ids_and_states():
    p = fractional(); p['segments'][0]['end_utc'] = '2026-10-01T00:00:03Z'
    whole = create_rational_internodes_from_shoot_events(inputs=p)
    first_segment = {**p['segments'][0], 'end_utc': '2026-10-01T00:00:01Z'}
    second_segment = {**p['segments'][0], 'start_utc': first_segment['end_utc']}
    first = create_rational_internodes_from_shoot_events(inputs={**p, 'input_id': 'first', 'segments': [first_segment]})
    second = create_rational_internodes_from_shoot_events(inputs={**p, 'input_id': 'second',
        'timeline_state': first['timeline_checkpoint'], 'segments': [second_segment]})
    forcing = rational_air_segments_from_utc(time_origin_utc=p['timeline_state']['started_at'], segments=[second_segment])
    resumed = [advance_rational_internode_length(inputs={'input_id': 'resume', 'state': n['length_state'],
        'segments': forcing})['state'] for n in first['new_internodes']]
    assert len(whole['new_internodes']) == 9
    assert resumed + [n['length_state'] for n in second['new_internodes']] == [n['length_state'] for n in whole['new_internodes']]
    assert second['timeline_checkpoint'] == whole['timeline_checkpoint']


def test_variable_and_flat_air_clips_only_remainder_after_birth():
    p = fractional(); p['segments'] = [p['segments'][0],
        {'start_utc': '2026-10-01T00:00:01Z', 'end_utc': '2026-10-01T00:00:02Z', 'air_temperature': {'value': 0, 'unit': 'degC'}},
        {'start_utc': '2026-10-01T00:00:02Z', 'end_utc': '2026-10-01T00:00:03Z', 'air_temperature': {'value': 6, 'unit': 'degC'}}]
    result = create_rational_internodes_from_shoot_events(inputs=p)
    births = [Fraction(1, 3), Fraction(2, 3), Fraction(1)] + [Fraction(2) + Fraction(i, 6) for i in range(1, 7)]
    ages = [Fraction(8 - i, 86400) for i in range(9)]
    assert len(result['new_internodes']) == len(births)
    for node, birth, age in zip(result['new_internodes'], births, ages, strict=True):
        assert node['length_state']['clock_state']['emerged_elapsed_seconds_exact'] == exact(birth)
        assert node['length_state']['clock_state']['age_exact'] == exact(age, unit='degC_day')
        assert node['length_state']['length']['value'] == pytest.approx(float(reference(age, p['curve'])), rel=1e-12, abs=0)


@pytest.mark.parametrize('change', ['missing-initial', 'zero', 'wrong-initial', 'curve-origin', 'below-base', 'extra'])
def test_unverified_inputs_do_not_create_partial_nodes(change):
    p = fractional()
    if change == 'missing-initial': del p['initial_length']
    elif change == 'zero': p['initial_length']['value'] = 0
    elif change == 'wrong-initial': p['initial_length']['value'] *= 2
    elif change == 'curve-origin': p['curve']['origin'] = 'observed'
    elif change == 'below-base': p['segments'][0]['air_temperature']['value'] = -1
    else: p['unexpected'] = 0
    before = deepcopy(p)
    with pytest.raises(RationalNewInternodeHold): create_rational_internodes_from_shoot_events(inputs=p)
    assert p == before


@pytest.mark.parametrize('change', ['origin', 'before-origin', 'gap', 'backwards', 'extra', 'unit', 'bool', 'inf', 'empty', 'overcapacity'])
def test_utc_to_rational_air_format_boundary(change):
    p = fractional(); origin = p['timeline_state']['started_at']; segments = p['segments']
    if change == 'origin': origin = '2026-10-01T00:00:00.5Z'
    elif change == 'before-origin': origin = '2026-10-01T00:00:01Z'
    elif change == 'gap': segments.append({**segments[0], 'start_utc': '2026-10-01T00:00:02Z', 'end_utc': '2026-10-01T00:00:03Z'})
    elif change == 'backwards': segments[0]['end_utc'] = origin
    elif change == 'extra': segments[0]['x'] = 0
    elif change == 'unit': segments[0]['air_temperature']['unit'] = 'K'
    elif change == 'bool': segments[0]['air_temperature']['value'] = True
    elif change == 'inf': segments[0]['air_temperature']['value'] = float('inf')
    elif change == 'empty': segments = []
    else: segments *= 513
    with pytest.raises(RationalNewInternodeHold): rational_air_segments_from_utc(time_origin_utc=origin, segments=segments)


def test_utc_adapter_preserves_leap_day_seconds_and_copies_input():
    segments = [{'start_utc': '2028-02-29T23:59:59Z', 'end_utc': '2028-03-01T00:00:01Z',
                 'air_temperature': {'value': 5, 'unit': 'degC'}}]; before = deepcopy(segments)
    result = rational_air_segments_from_utc(time_origin_utc='2028-02-29T00:00:00Z', segments=segments)
    assert result == [{'start_elapsed_seconds_exact': exact(86399), 'end_elapsed_seconds_exact': exact(86401),
                      'air_temperature': {'value': 5.0, 'unit': 'degC'}}]
    result[0]['air_temperature']['value'] = 7
    assert segments == before


def test_large_exact_birth_receipts_respect_result_budget():
    p = inputs(); denominator = 675 * 2**2390
    start = Fraction(denominator * 10**300 + 1, denominator)
    step = (Fraction.from_float(1e300) - Fraction.from_float(-1e-300)) / 86400
    p['timeline_state'].update(at='2026-10-01T01:00:00Z', base_temperature={'value': -1e-300, 'unit': 'degC'},
        age_exact=exact(start, unit='degC_day'), next_threshold_exact=exact(start + step, unit='degC_day'),
        phyllochron_exact=exact(step, unit='degC_day'))
    p['segments'] = [{'start_utc': '2026-10-01T01:00:00Z', 'end_utc': '2026-10-01T01:08:32Z',
                      'air_temperature': {'value': 1e300, 'unit': 'degC'}}]
    p['curve']['profile_id'] = 'synthetic-' + 'x' * 190
    p['curve']['values'].update(maximum_length={'value': 1e308, 'unit': 'm'},
        steepness={'value': 1e-300, 'unit': '1/degC_day'}, inflection_age={'value': 0, 'unit': 'degC_day'})
    p['initial_length'] = {'value': 5e307, 'unit': 'm'}
    with pytest.raises(RationalNewInternodeHold, match='CAPACITY_HOLD: rational new-internode result exceeds 2MiB'):
        create_rational_internodes_from_shoot_events(inputs=p)
