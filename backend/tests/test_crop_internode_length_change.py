from copy import deepcopy
import json
from math import fsum
from pathlib import Path

import pytest

from app.crop_internode_length_change import InternodeLengthChangeHold, calculate_internode_length_change


REFERENCE = json.loads((Path(__file__).resolve().parents[2] /
    'fixtures/crop-internode-length-change-reference-v1.json').read_bytes())


def inputs(index=0):
    return deepcopy(REFERENCE['cases'][index]['inputs'])


@pytest.mark.parametrize('case', REFERENCE['cases'], ids=lambda c: c['case_id'])
def test_independent_direct_antiderivative_difference(case):
    original = deepcopy(case['inputs'])
    result = calculate_internode_length_change(inputs=case['inputs'])
    assert result['length_change']['unit'] == 'm'
    assert result['length_change']['value'] == pytest.approx(float(case['expected_change_m']), rel=1e-12, abs=0)
    assert result['length_change']['value'] >= 0
    assert result['length_change']['value'] <= case['inputs']['curve']['values']['maximum_length']['value']
    assert result['scope'] == 'software_research_only' and result['gates'] == 'not_assessed'
    assert result['claim_scope'] == 'synthetic_crop_math_only'
    assert result['model_version'] == 'internode-logistic-length-change-research-v1'
    assert case['inputs'] == original
    assert calculate_internode_length_change(inputs=case['inputs']) == result
    assert 'length' not in result and 'height' not in result


def test_variable_program_split_preserves_exact_age_and_integral():
    p = inputs(2)
    whole = calculate_internode_length_change(inputs=p)
    first = calculate_internode_length_change(inputs={**p, 'segments': p['segments'][:1]})
    second = calculate_internode_length_change(inputs={**p, 'clock_state': first['checkpoint'], 'segments': p['segments'][1:]})
    assert second['checkpoint'] == whole['checkpoint']
    assert fsum((first['length_change']['value'], second['length_change']['value'])) == pytest.approx(
        whole['length_change']['value'], rel=1e-12, abs=0)
    assert first['curve_sha256'] == second['curve_sha256'] == whole['curve_sha256']
    assert second['input_sha256'] != whole['input_sha256']


def test_exact_age_change_can_matter_when_float_age_is_unchanged():
    p = inputs(8)
    result = calculate_internode_length_change(inputs=p)
    assert result['thermal_age']['value'] == 1
    assert result['length_change']['value'] > 0
    assert result['checkpoint']['age_exact'] != p['clock_state']['age_exact']


@pytest.mark.parametrize('change', ['curve-extra', 'missing-parameter', 'parameter-unit', 'origin',
    'invalid-profile-id', 'initial-length', 'below-base', 'old-clock'])
def test_rejects_unsupported_contract_and_preserves_delegate_holds(change):
    p = inputs()
    if change == 'curve-extra': p['curve']['fit'] = 'unreviewed'
    elif change == 'missing-parameter': del p['curve']['values']['steepness']
    elif change == 'parameter-unit': p['curve']['values']['steepness']['unit'] = '1/day'
    elif change == 'origin': p['curve']['origin'] = 'reference_observation'
    elif change == 'invalid-profile-id': p['curve']['profile_id'] = ''
    elif change == 'initial-length': p['length'] = {'value': 0, 'unit': 'm'}
    elif change == 'below-base': p['segments'][0]['air_temperature']['value'] = 4
    elif change == 'old-clock': p['clock_state']['age_basis'] = 'canopy_temperature_sum'
    with pytest.raises(InternodeLengthChangeHold):
        calculate_internode_length_change(inputs=p)


@pytest.mark.parametrize('change', ['subnormal-change', 'point-exponent-overflow', 'curve-rate-overflow'])
def test_unresolved_numerics_are_not_clipped(change):
    p = inputs(5)
    v = p['curve']['values']
    if change == 'subnormal-change': v['maximum_length']['value'] = 1e-300
    elif change == 'point-exponent-overflow':
        v['steepness']['value'] = 1e308
        v['inflection_age']['value'] = 0
    else: v['maximum_length']['value'] = v['steepness']['value'] = 1e308
    with pytest.raises(InternodeLengthChangeHold, match='NUMERIC_HOLD'):
        calculate_internode_length_change(inputs=p)
