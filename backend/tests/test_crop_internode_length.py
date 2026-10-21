from copy import deepcopy
import json
from math import fsum
from pathlib import Path

import pytest

from app.crop_internode_length import (
    InternodeLengthHold, advance_internode_length, initialize_internode_length,
)

REFERENCE = json.loads((Path(__file__).resolve().parents[2] /
    'fixtures/crop-internode-length-state-reference-v1.json').read_bytes())


def inputs(index=0):
    return deepcopy(REFERENCE['cases'][index]['inputs'])


@pytest.mark.parametrize('case', REFERENCE['cases'], ids=lambda c: c['case_id'])
def test_explicit_initial_length_and_independent_direct_curve(case):
    original = deepcopy(case['inputs'])
    result = initialize_internode_length(inputs=case['inputs'])
    assert result['state']['length']['value'] == pytest.approx(float(case['expected_length_m']), rel=1e-12, abs=0)
    assert result['state']['anchor']['requested_length'] == case['inputs']['initial_length']
    assert result['state']['anchor']['canonical_length'] == result['state']['length']
    assert result['state']['clock_state'] == case['inputs']['clock_state']
    assert result['scope'] == 'software_research_only' and result['claim_scope'] == 'synthetic_crop_math_only'
    assert result['gates'] == 'not_assessed'
    assert result['model_version'] == 'internode-logistic-length-state-research-v1'
    assert case['inputs'] == original
    assert initialize_internode_length(inputs=case['inputs']) == result


def test_accepted_numeric_anchor_difference_does_not_become_offset():
    p = inputs()
    canonical = initialize_internode_length(inputs=p)['state']['length']
    p['initial_length']['value'] *= 1 + 5e-13
    result = initialize_internode_length(inputs=p)
    assert result['state']['length'] == canonical
    assert result['state']['anchor']['requested_length'] == p['initial_length']
    assert result['state']['length'] != p['initial_length']


@pytest.mark.parametrize('case', REFERENCE['cases'], ids=lambda c: c['case_id'])
def test_advance_preserves_initial_receipt_and_immutable_input(case):
    first = initialize_internode_length(inputs=case['inputs'])
    p = {'input_id': 'advance', 'state': first['state'], 'segments': deepcopy(case['segments'])}
    original = deepcopy(p)
    result = advance_internode_length(inputs=p)
    assert result['state']['length']['value'] == pytest.approx(float(case['expected_end_length_m']), rel=1e-12, abs=0)
    assert result['state']['anchor'] == first['state']['anchor']
    assert result['state']['length']['value'] >= first['state']['length']['value']
    assert result['state']['length']['value'] <= first['state']['curve']['values']['maximum_length']['value']
    assert result['length_change']['value'] >= 0
    assert len(result['length_change_input_sha256']) == 64
    assert p == original
    assert advance_internode_length(inputs=p) == result


def test_variable_program_split_uses_canonical_end_length_without_drift():
    case = REFERENCE['cases'][2]
    initial = initialize_internode_length(inputs=case['inputs'])['state']
    p = {'input_id': 'whole', 'state': initial, 'segments': deepcopy(case['segments'])}
    whole = advance_internode_length(inputs=p)
    first = advance_internode_length(inputs={**p, 'input_id': 'part1', 'segments': p['segments'][:1]})
    second = advance_internode_length(inputs={**p, 'input_id': 'part2', 'state': first['state'], 'segments': p['segments'][1:]})
    assert second['state'] == whole['state']
    assert fsum([first['length_change']['value'], second['length_change']['value']]) == pytest.approx(
        whole['length_change']['value'], rel=1e-12, abs=0)
    assert whole['input_sha256'] != second['input_sha256']


def test_exact_age_increment_survives_equal_float_endpoint_lengths():
    case = REFERENCE['cases'][7]
    initial = initialize_internode_length(inputs=case['inputs'])['state']
    result = advance_internode_length(inputs={'input_id': 'tiny', 'state': initial, 'segments': case['segments']})
    assert result['state']['length'] == initial['length']
    assert result['length_change']['value'] > 0
    assert result['state']['clock_state']['age_exact'] != initial['clock_state']['age_exact']


@pytest.mark.parametrize('change', ['zero', 'mismatch', 'missing-length', 'extra', 'bool', 'nan', 'infinity',
    'wrong-unit', 'bad-id', 'old-clock', 'real-origin', 'age-not-reduced'])
def test_initialization_does_not_invent_or_silently_replace_anchor(change):
    p = inputs()
    if change == 'zero': p['initial_length']['value'] = 0
    elif change == 'mismatch': p['initial_length']['value'] *= 1.000001
    elif change == 'missing-length': del p['initial_length']
    elif change == 'extra': p['height'] = 1
    elif change == 'bool': p['initial_length']['value'] = True
    elif change == 'nan': p['initial_length']['value'] = float('nan')
    elif change == 'infinity': p['initial_length']['value'] = float('inf')
    elif change == 'wrong-unit': p['initial_length']['unit'] = 'cm'
    elif change == 'bad-id': p['input_id'] = ''
    elif change == 'old-clock': p['clock_state']['age_basis'] = 'canopy_temperature_sum'
    elif change == 'real-origin': p['curve']['origin'] = 'reference_observation'
    else: p['clock_state']['age_exact'] = {'numerator': '0', 'denominator': '2', 'unit': 'degC_day'}
    with pytest.raises(InternodeLengthHold):
        initialize_internode_length(inputs=p)


@pytest.mark.parametrize('change', ['length', 'curve', 'curve-hash', 'anchor-hash', 'anchor-length',
    'anchor-request', 'clock-identity', 'clock-time', 'anchor-time', 'extra-state', 'state-version'])
def test_resume_rechecks_curve_initial_receipt_and_canonical_state(change):
    initial = initialize_internode_length(inputs=inputs())['state']
    p = {'input_id': 'advance', 'state': initial, 'segments': deepcopy(REFERENCE['cases'][0]['segments'])}
    state = p['state']
    if change == 'length': state['length']['value'] *= 1.000001
    elif change == 'curve': state['curve']['values']['maximum_length']['value'] *= 2
    elif change == 'curve-hash': state['curve_sha256'] = '0' * 64
    elif change == 'anchor-hash': state['anchor']['curve_sha256'] = '0' * 64
    elif change == 'anchor-length': state['anchor']['canonical_length']['value'] *= 2
    elif change == 'anchor-request': state['anchor']['requested_length']['value'] = 0
    elif change == 'clock-identity': state['clock_state']['internode_id'] = 'different'
    elif change == 'clock-time': state['clock_state']['at'] = '2026-09-30T00:00:00Z'
    elif change == 'anchor-time': state['anchor']['clock_state']['at'] = '2026-10-02T00:00:00Z'
    elif change == 'extra-state': state['height'] = 1
    else: state['model_version'] = 'unknown'
    with pytest.raises(InternodeLengthHold):
        advance_internode_length(inputs=p)


def test_failed_advance_leaves_prior_state_available():
    state = initialize_internode_length(inputs=inputs())['state']
    original = deepcopy(state)
    segments = deepcopy(REFERENCE['cases'][0]['segments'])
    segments[0]['air_temperature']['value'] = 0
    with pytest.raises(InternodeLengthHold):
        advance_internode_length(inputs={'input_id': 'hold', 'state': state, 'segments': segments})
    assert state == original
