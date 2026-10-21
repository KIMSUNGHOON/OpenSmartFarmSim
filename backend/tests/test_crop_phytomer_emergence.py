from copy import deepcopy
import json
from pathlib import Path

import pytest

from app.crop_phytomer_emergence import PhytomerEmergenceHold, advance_phytomer_emergence

REFERENCE = json.loads((Path(__file__).resolve().parents[2] /
    'fixtures/crop-phytomer-events-reference-v1.json').read_bytes())


def inputs(index=0):
    return deepcopy(REFERENCE['cases'][index]['inputs'])


def quantity(n, d=1):
    from fractions import Fraction
    q = Fraction(n, d)
    return {'numerator': str(q.numerator), 'denominator': str(q.denominator), 'unit': 'degC_day'}


@pytest.mark.parametrize('case', REFERENCE['cases'], ids=lambda c: c['case_id'])
def test_independent_integer_grid_enumeration(case):
    original = deepcopy(case['inputs'])
    out = advance_phytomer_emergence(inputs=case['inputs'])
    assert out['events'] == case['events']
    assert out['checkpoint'] == case['checkpoint']
    assert out['model_version'] == 'phytomer-thermal-events-research-v1'
    assert out['scope'] == 'software_research_only' and out['claim_scope'] == 'synthetic_crop_math_only'
    assert out['gates'] == 'not_assessed'
    assert case['inputs'] == original
    assert advance_phytomer_emergence(inputs=case['inputs']) == out
    assert 'utc' not in out and 'leaves' not in out


@pytest.mark.parametrize('split', [quantity(7, 6), quantity(4, 3)])
def test_exact_threshold_and_between_threshold_splits_preserve_all_events(split):
    p = inputs(5)
    whole = advance_phytomer_emergence(inputs=p)
    first = advance_phytomer_emergence(inputs={**p, 'input_id': 'part1', 'end_age_exact': split})
    second = advance_phytomer_emergence(inputs={**p, 'input_id': 'part2', 'state': first['checkpoint']})
    assert first['events'] + second['events'] == whole['events']
    assert second['checkpoint'] == whole['checkpoint']
    assert first['input_sha256'] != whole['input_sha256']
    stopped = advance_phytomer_emergence(inputs={**p, 'state': first['checkpoint'], 'end_age_exact': split})
    assert stopped['events'] == [] and stopped['checkpoint'] == first['checkpoint']


@pytest.mark.parametrize('change', ['extra-input', 'missing-end', 'extra-state', 'missing-phase', 'origin', 'basis',
    'bad-id', 'bad-shoot', 'unit', 'float-age', 'unreduced', 'zero-denominator', 'leading-zero', 'too-many-digits',
    'backward', 'stale-threshold', 'zero-step', 'negative-step', 'bool-sequence', 'negative-sequence'])
def test_invalid_phase_and_unverified_contracts_hold_without_partial_output(change):
    p = inputs()
    s = p['state']
    if change == 'extra-input': p['utc'] = '2026-10-21T00:00:00Z'
    elif change == 'missing-end': del p['end_age_exact']
    elif change == 'extra-state': s['leaf_count'] = 0
    elif change == 'missing-phase': del s['next_threshold_exact']
    elif change == 'origin': s['origin'] = 'reference_observation'
    elif change == 'basis': s['age_basis'] = 'since_internode_emergence'
    elif change == 'bad-id': p['input_id'] = ''
    elif change == 'bad-shoot': s['shoot_id'] = 'a' * 201
    elif change == 'unit': s['phyllochron_exact']['unit'] = 'day'
    elif change == 'float-age': p['end_age_exact'] = {'value': 15.0, 'unit': 'degC_day'}
    elif change == 'unreduced': s['phyllochron_exact'] = {'numerator': '20', 'denominator': '2', 'unit': 'degC_day'}
    elif change == 'zero-denominator': p['end_age_exact']['denominator'] = '0'
    elif change == 'leading-zero': p['end_age_exact']['numerator'] = '015'
    elif change == 'too-many-digits': p['end_age_exact']['numerator'] = '1' * 1025
    elif change == 'backward': s['at_age_exact'] = quantity(14); p['end_age_exact'] = quantity(13)
    elif change == 'stale-threshold': s['next_threshold_exact'] = quantity(0)
    elif change == 'zero-step': s['phyllochron_exact'] = quantity(0)
    elif change == 'negative-step': s['phyllochron_exact']['numerator'] = '-1'
    elif change == 'bool-sequence': s['next_sequence'] = True
    else: s['next_sequence'] = -1
    original = deepcopy(p)
    with pytest.raises(PhytomerEmergenceHold):
        advance_phytomer_emergence(inputs=p)
    assert p == original


@pytest.mark.parametrize('count', [512, 513])
def test_event_capacity_is_all_or_hold(count):
    p = inputs()
    p['state']['next_threshold_exact'] = quantity(1)
    p['state']['phyllochron_exact'] = quantity(1)
    p['end_age_exact'] = quantity(count)
    if count == 513:
        with pytest.raises(PhytomerEmergenceHold, match='CAPACITY_HOLD'):
            advance_phytomer_emergence(inputs=p)
    else:
        out = advance_phytomer_emergence(inputs=p)
        assert len(out['events']) == 512 and out['checkpoint']['next_threshold_exact'] == quantity(513)


def test_sequence_cannot_overflow_next_checkpoint():
    p = inputs(1)
    p['state']['next_sequence'] = 2**31 - 1
    with pytest.raises(PhytomerEmergenceHold, match='CAPACITY_HOLD'):
        advance_phytomer_emergence(inputs=p)


def test_exact_checkpoint_digit_overflow_does_not_truncate_events():
    p = inputs(1)
    p['state']['phyllochron_exact'] = quantity(1, 2**3390)
    p['state']['next_threshold_exact'] = quantity(1, 5**1450)
    p['end_age_exact'] = deepcopy(p['state']['next_threshold_exact'])
    with pytest.raises(PhytomerEmergenceHold, match='CAPACITY_HOLD'):
        advance_phytomer_emergence(inputs=p)
