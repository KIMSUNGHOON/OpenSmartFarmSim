from copy import deepcopy
import json
from pathlib import Path

import pytest

from app.crop_shoot_timeline import ShootTimelineHold, advance_shoot_event_timeline

REFERENCE = json.loads((Path(__file__).resolve().parents[2] /
    'fixtures/crop-shoot-timeline-reference-v1.json').read_bytes())


def inputs(index=0):
    return deepcopy(REFERENCE['cases'][index]['inputs'])


@pytest.mark.parametrize('case', REFERENCE['cases'], ids=lambda c: c['case_id'])
def test_independent_hand_derived_exact_event_times(case):
    original = deepcopy(case['inputs'])
    out = advance_shoot_event_timeline(inputs=case['inputs'])
    assert out['events'] == case['events']
    assert out['checkpoint'] == case['checkpoint']
    assert out['time_origin_utc'] == case['inputs']['state']['started_at']
    assert out['scope'] == 'software_research_only' and out['claim_scope'] == 'synthetic_crop_math_only'
    assert out['gates'] == 'not_assessed' and out['model_version'] == 'shoot-air-phytomer-timeline-research-v1'
    assert case['inputs'] == original
    assert advance_shoot_event_timeline(inputs=case['inputs']) == out


@pytest.mark.parametrize('index', [1,2])
def test_boundary_and_flat_segment_split_preserve_event_times_and_final_clock(index):
    p = inputs(index)
    whole = advance_shoot_event_timeline(inputs=p)
    first = advance_shoot_event_timeline(inputs={**p, 'input_id': 'first', 'segments': p['segments'][:1]})
    second = advance_shoot_event_timeline(inputs={**p, 'input_id': 'second', 'state': first['checkpoint'], 'segments': p['segments'][1:]})
    assert first['events'] + second['events'] == whole['events']
    assert second['checkpoint'] == whole['checkpoint']
    assert first['time_origin_utc'] == second['time_origin_utc'] == whole['time_origin_utc']
    assert first['input_sha256'] != whole['input_sha256']


def test_subsecond_events_retain_rational_time_instead_of_rounded_utc():
    out = advance_shoot_event_timeline(inputs=inputs(3))
    assert [e['utc_whole_second'] for e in out['events']] == [None, None, '2026-10-01T00:00:01Z']
    assert out['events'][0]['elapsed_seconds_exact'] == {'numerator':'1','denominator':'3','unit':'s'}


@pytest.mark.parametrize('change', ['extra', 'missing-segments', 'empty-segments', 'origin', 'basis', 'missing-phase',
    'start-after-at', 'nonzero-at-origin', 'bad-origin-utc', 'bad-id', 'bad-shoot', 'wrong-base-unit', 'below-base',
    'gap', 'overlap', 'reverse', 'bad-air-unit', 'bad-air-value'])
def test_unverified_clock_phase_and_air_program_hold_without_mutation(change):
    p = inputs()
    s = p['state']
    if change == 'extra': p['height'] = 1
    elif change == 'missing-segments': del p['segments']
    elif change == 'empty-segments': p['segments'] = []
    elif change == 'origin': s['origin'] = 'reference_observation'
    elif change == 'basis': s['age_basis'] = 'since_internode_emergence'
    elif change == 'missing-phase': del s['next_threshold_exact']
    elif change == 'start-after-at': s['started_at'] = '2026-10-02T00:00:00Z'
    elif change == 'nonzero-at-origin': s['age_exact']['numerator'] = '1'
    elif change == 'bad-origin-utc': s['started_at'] = '2026-10-01T00:00:00+00:00'
    elif change == 'bad-id': p['input_id'] = ''
    elif change == 'bad-shoot': s['shoot_id'] = True
    elif change == 'wrong-base-unit': s['base_temperature']['unit'] = 'K'
    elif change == 'below-base': p['segments'][0]['air_temperature']['value'] = 4
    elif change == 'gap': p['segments'][0]['start_utc'] = '2026-10-01T00:00:01Z'
    elif change == 'overlap': p['segments'][0]['start_utc'] = '2026-09-30T23:59:59Z'
    elif change == 'reverse': p['segments'][0]['end_utc'] = p['segments'][0]['start_utc']
    elif change == 'bad-air-unit': p['segments'][0]['air_temperature']['unit'] = 'K'
    else: p['segments'][0]['air_temperature']['value'] = float('inf')
    original = deepcopy(p)
    with pytest.raises(ShootTimelineHold):
        advance_shoot_event_timeline(inputs=p)
    assert p == original
