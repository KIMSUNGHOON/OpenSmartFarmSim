from copy import deepcopy
import json
import math
from pathlib import Path

import pytest

from app.crop_internode_elongation import (
    InternodeElongationHold, calculate_internode_elongation,
)


REFERENCE = json.loads((Path(__file__).resolve().parents[2] /
    'fixtures/crop-internode-elongation-reference-v1.json').read_bytes())


def inputs():
    return deepcopy(REFERENCE['cases'][0]['inputs'])


@pytest.mark.parametrize('case', REFERENCE['cases'], ids=lambda c: c['case_id'])
def test_independent_decimal_equation_and_research_scope(case):
    original = deepcopy(case['inputs'])
    actual = calculate_internode_elongation(inputs=case['inputs'])
    quantity = actual['elongation_per_thermal_age']
    assert quantity['unit'] == 'm/degC_day'
    assert math.isfinite(quantity['value']) and quantity['value'] > 0
    assert quantity['value'] == pytest.approx(float(case['expected_m_per_degC_day']), rel=1e-12, abs=0)
    assert actual['model_version'] == 'internode-logistic-thermal-rate-research-v1'
    assert actual['scope'] == 'software_research_only'
    assert actual['claim_scope'] == 'synthetic_crop_math_only'
    assert actual['gates'] == 'not_assessed'
    assert len(actual['input_sha256']) == 64
    assert set(actual) == {'model_version', 'scope', 'claim_scope', 'gates',
                           'input_sha256', 'elongation_per_thermal_age'}
    assert case['inputs'] == original


def test_inflection_maximum_symmetry_and_provenance_identity():
    p = inputs()
    results = []
    for age in (0, 20, 40, 60, 80):
        p['values']['thermal_age']['value'] = age
        results.append(calculate_internode_elongation(inputs=p))
    values = [r['elongation_per_thermal_age']['value'] for r in results]
    assert values[0] == values[4] and values[1] == values[3]
    assert values[0] < values[1] < values[2]
    assert values[2] == pytest.approx(.0015, rel=1e-14)
    assert calculate_internode_elongation(inputs=p) == results[-1]
    p['input_id'] = 'another-arithmetic-probe'
    revised = calculate_internode_elongation(inputs=p)
    assert revised['elongation_per_thermal_age'] == results[-1]['elongation_per_thermal_age']
    assert revised['input_sha256'] != results[-1]['input_sha256']


@pytest.mark.parametrize('field,unit', [('thermal_age', 'day'), ('maximum_length', 'cm'),
    ('steepness', '1'), ('inflection_age', 'degC')])
def test_rejects_wrong_units_including_source_table_dimensionless_steepness(field, unit):
    p = inputs()
    p['values'][field]['unit'] = unit
    with pytest.raises(InternodeElongationHold, match='UNIT_HOLD'):
        calculate_internode_elongation(inputs=p)


@pytest.mark.parametrize('field,bad', [
    ('thermal_age', -1), ('inflection_age', -1), ('maximum_length', 0), ('steepness', 0),
    ('maximum_length', -1), ('steepness', -1), ('thermal_age', True), ('thermal_age', '2'),
    ('thermal_age', float('nan')), ('maximum_length', float('inf')),
    ('steepness', 10**1000),
])
def test_rejects_invalid_quantity_values(field, bad):
    p = inputs()
    p['values'][field]['value'] = bad
    with pytest.raises(InternodeElongationHold):
        calculate_internode_elongation(inputs=p)


@pytest.mark.parametrize('change', ['missing', 'extra', 'quantity-extra', 'actual-origin',
    'old-clock', 'empty-id', 'long-id', 'non-ascii-id', 'missing-id', 'not-object'])
def test_rejects_incomplete_or_unsupported_input_contract(change):
    p = inputs()
    if change == 'missing': del p['values']['steepness']
    elif change == 'extra': p['height'] = 1
    elif change == 'quantity-extra': p['values']['thermal_age']['source'] = 'unreviewed'
    elif change == 'actual-origin': p['origin'] = 'reference_observation'
    elif change == 'old-clock': p['thermal_age_basis'] = 'canopy_temperature_sum'
    elif change == 'empty-id': p['input_id'] = ''
    elif change == 'long-id': p['input_id'] = 'a' * 201
    elif change == 'non-ascii-id': p['input_id'] = '무검토'
    elif change == 'missing-id': del p['input_id']
    elif change == 'not-object': p = None
    with pytest.raises(InternodeElongationHold, match='INPUT_HOLD'):
        calculate_internode_elongation(inputs=p)


@pytest.mark.parametrize('case', ['exponent-overflow', 'rate-overflow', 'positive-underflow'])
def test_numeric_failures_are_holds_not_zero_or_clipped_rates(case):
    p = inputs()
    v = p['values']
    if case == 'exponent-overflow':
        v['thermal_age']['value'] = 1e308
        v['steepness']['value'] = 2
    elif case == 'rate-overflow':
        v['thermal_age']['value'] = v['inflection_age']['value']
        v['maximum_length']['value'] = v['steepness']['value'] = 1e308
    else:
        v['thermal_age']['value'] = 1e308
    with pytest.raises(InternodeElongationHold, match='NUMERIC_HOLD'):
        calculate_internode_elongation(inputs=p)
