from copy import deepcopy
import json
from pathlib import Path

import pytest

from app.crop_internode_length import advance_internode_length
from app.crop_new_internodes import NewInternodeHold, create_internodes_from_shoot_events

ROOT = Path(__file__).resolve().parents[2]
REFERENCE = json.loads((ROOT / 'fixtures/crop-new-internodes-reference-v1.json').read_bytes())
TIMELINE = json.loads((ROOT / 'fixtures/crop-shoot-timeline-reference-v1.json').read_bytes())


def inputs(index=0):
    return deepcopy(REFERENCE['cases'][index]['inputs'])


@pytest.mark.parametrize('case', REFERENCE['cases'], ids=lambda c: c['case_id'])
def test_independent_manual_birth_ages_and_direct_decimal_end_lengths(case):
    original = deepcopy(case['inputs'])
    out = create_internodes_from_shoot_events(inputs=case['inputs'])
    assert out['timeline_checkpoint'] == case['timeline_checkpoint']
    assert len(out['new_internodes']) == len(case['new_internodes'])
    for actual, expected in zip(out['new_internodes'], case['new_internodes'], strict=True):
        assert actual['sequence'] == expected['sequence']
        assert actual['birth_age_exact'] == expected['birth_age_exact']
        clock = actual['length_state']['clock_state']
        assert clock['emerged_at'] == expected['birth_utc']
        assert clock['at'] == out['timeline_checkpoint']['at']
        assert clock['age_exact'] == expected['end_age_exact']
        assert actual['length_state']['length']['value'] == pytest.approx(float(expected['end_length_m']), rel=1e-12, abs=0)
        assert len(actual['initialization_input_sha256']) == 64
    assert len({n['length_state']['clock_state']['internode_id'] for n in out['new_internodes']}) == len(out['new_internodes'])
    assert out['model_version'] == 'shoot-new-internodes-research-v1'
    assert out['scope'] == 'software_research_only' and out['claim_scope'] == 'synthetic_crop_math_only'
    assert out['gates'] == 'not_assessed' and 'height' not in out
    assert original == case['inputs']
    assert create_internodes_from_shoot_events(inputs=case['inputs']) == out


def test_endpoint_birth_has_only_initial_state_without_invented_interval():
    out = create_internodes_from_shoot_events(inputs=inputs())
    final = out['new_internodes'][-1]
    assert final['advancement_input_sha256'] is None
    assert final['length_state']['clock_state']['at'] == final['length_state']['clock_state']['emerged_at']
    assert final['length_state']['clock_state']['age_exact'] == {'numerator':'0','denominator':'1','unit':'degC_day'}


def test_split_keeps_ids_and_births_and_existing_node_can_resume_without_reset():
    p = inputs()
    whole = create_internodes_from_shoot_events(inputs=p)
    first_segment = deepcopy(p['segments'][0])
    first_segment['end_utc'] = '2026-10-01T08:00:00Z'
    second_segment = deepcopy(p['segments'][0])
    second_segment['start_utc'] = first_segment['end_utc']
    first = create_internodes_from_shoot_events(inputs={**p, 'input_id': 'part1', 'segments': [first_segment]})
    second = create_internodes_from_shoot_events(inputs={**p, 'input_id': 'part2',
        'timeline_state': first['timeline_checkpoint'], 'segments': [second_segment]})
    old = first['new_internodes'][0]
    advanced = advance_internode_length(inputs={'input_id':'resume-existing', 'state':old['length_state'], 'segments':[second_segment]})
    assert advanced['state'] == whole['new_internodes'][0]['length_state']
    assert advanced['state']['anchor'] == old['length_state']['anchor']
    assert [n['length_state'] for n in second['new_internodes']] == [n['length_state'] for n in whole['new_internodes'][1:]]
    assert second['timeline_checkpoint'] == whole['timeline_checkpoint']


def test_fractional_birth_cannot_be_silently_rounded():
    p = inputs()
    p['timeline_state'] = deepcopy(TIMELINE['cases'][3]['inputs']['state'])
    p['segments'] = deepcopy(TIMELINE['cases'][3]['inputs']['segments'])
    original = deepcopy(p)
    with pytest.raises(NewInternodeHold, match='SUBSECOND_EMERGENCE_HOLD'):
        create_internodes_from_shoot_events(inputs=p)
    assert p == original


@pytest.mark.parametrize('change', ['missing-initial', 'extra', 'initial-zero', 'initial-mismatch', 'curve-origin',
    'curve-unit', 'below-base', 'wrong-clock'])
def test_unverified_profile_or_clock_never_creates_organs(change):
    p = inputs(4)
    if change == 'missing-initial': del p['initial_length']
    elif change == 'extra': p['initial_node_count'] = 0
    elif change == 'initial-zero': p['initial_length']['value'] = 0
    elif change == 'initial-mismatch': p['initial_length']['value'] *= 2
    elif change == 'curve-origin': p['curve']['origin'] = 'reference_observation'
    elif change == 'curve-unit': p['curve']['values']['steepness']['unit'] = '1/day'
    elif change == 'below-base': p['segments'][0]['air_temperature']['value'] = 4
    else: p['timeline_state']['age_basis'] = 'since_internode_emergence'
    original = deepcopy(p)
    with pytest.raises(NewInternodeHold):
        create_internodes_from_shoot_events(inputs=p)
    assert p == original


def test_large_exact_birth_receipts_cannot_exceed_packet_budget():
    from fractions import Fraction

    def quantity(value):
        return {'numerator': str(value.numerator), 'denominator': str(value.denominator), 'unit': 'degC_day'}

    p = inputs()
    denominator = 675 * 2**2390
    start = Fraction(denominator * 10**300 + 1, denominator)
    step = (Fraction.from_float(1e300) - Fraction.from_float(-1e-300)) / 86400
    p['timeline_state'].update(at='2026-10-01T01:00:00Z', base_temperature={'value':-1e-300,'unit':'degC'},
        age_exact=quantity(start), next_threshold_exact=quantity(start + step), phyllochron_exact=quantity(step))
    p['segments'] = [{'start_utc':'2026-10-01T01:00:00Z','end_utc':'2026-10-01T01:08:32Z',
                      'air_temperature':{'value':1e300,'unit':'degC'}}]
    p['curve']['profile_id'] = 'synthetic-' + 'x' * 190
    p['curve']['values'].update(maximum_length={'value':1e308,'unit':'m'},
        steepness={'value':1e-300,'unit':'1/degC_day'}, inflection_age={'value':0,'unit':'degC_day'})
    p['initial_length'] = {'value':5e307,'unit':'m'}
    with pytest.raises(NewInternodeHold, match='CAPACITY_HOLD: new-internode result exceeds 2MiB'):
        create_internodes_from_shoot_events(inputs=p)
