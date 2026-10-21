from copy import deepcopy
import json
from pathlib import Path

import pytest

from app.crop_internode_length import calculate_internode_length_point, InternodeLengthHold


REFERENCE = json.loads((Path(__file__).resolve().parents[2] /
    'fixtures/crop-internode-length-point-reference-v1.json').read_bytes())['cases']


@pytest.mark.parametrize('case', REFERENCE, ids=lambda c:c['case_id'])
def test_exact_age_points_against_independent_Decimal800(case):
    p = deepcopy(case['inputs']); before = deepcopy(p)
    result = calculate_internode_length_point(inputs=p)
    assert result['length']['unit'] == 'm'
    assert result['length']['value'] == pytest.approx(float(case['expected_length_m']), rel=1e-12, abs=0)
    assert result['age_exact'] == p['age_exact'] and p == before
    assert result['scope'] == 'software_research_only' and result['gates'] == 'not_assessed'
    assert result['claim_scope'] == 'synthetic_crop_math_only'
    assert result['model_version'] == 'internode-logistic-length-point-research-v1'
    assert len(result['curve_sha256']) == len(result['input_sha256']) == 64
    assert calculate_internode_length_point(inputs=p) == result


@pytest.mark.parametrize('change', ['origin', 'basis', 'extra-time', 'negative', 'zero-denominator',
    'unreduced', 'leading-zero', 'too-long', 'age-unit', 'curve-unit', 'curve-origin', 'bool', 'nonfinite'])
def test_invalid_or_unsupported_point_inputs_hold(change):
    p = deepcopy(REFERENCE[0]['inputs'])
    if change == 'origin':p['origin'] = 'observed'
    elif change == 'basis':p['thermal_age_basis'] = 'since_shoot_development_origin'
    elif change == 'extra-time':p['emerged_at'] = '2026-10-01T00:00:00Z'
    elif change == 'negative':p['age_exact']['numerator'] = '-1'
    elif change == 'zero-denominator':p['age_exact']['denominator'] = '0'
    elif change == 'unreduced':p['age_exact'].update(numerator='2',denominator='2')
    elif change == 'leading-zero':p['age_exact']['numerator'] = '00'
    elif change == 'too-long':p['age_exact']['numerator'] = '1' * 1025
    elif change == 'age-unit':p['age_exact']['unit'] = 's'
    elif change == 'curve-unit':p['curve']['values']['maximum_length']['unit'] = 'cm'
    elif change == 'curve-origin':p['curve']['origin'] = 'observed'
    elif change == 'bool':p['curve']['values']['steepness']['value'] = True
    else:p['curve']['values']['maximum_length']['value'] = float('inf')
    with pytest.raises(InternodeLengthHold):calculate_internode_length_point(inputs=p)


@pytest.mark.parametrize('change', ['exponent-overflow', 'subnormal-length'])
def test_unrepresentable_point_is_not_filled_with_zero(change):
    p = deepcopy(REFERENCE[0]['inputs'])
    if change == 'exponent-overflow':p['age_exact'].update(numerator='1'+'0'*1000,denominator='1')
    else:p['curve']['values']['maximum_length']['value'] = 1e-307
    with pytest.raises(InternodeLengthHold,match='NUMERIC_HOLD'):calculate_internode_length_point(inputs=p)
