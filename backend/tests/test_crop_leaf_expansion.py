from copy import deepcopy
import json
import math
from pathlib import Path

import pytest

from app.crop_leaf_expansion import LeafExpansionHold, calculate_leaf_expansion_rate


REFERENCE = json.loads((Path(__file__).resolve().parents[2] /
    'fixtures/crop-leaf-expansion-rate-reference-v1.json').read_bytes())


def inputs():
    return deepcopy(REFERENCE['cases'][0]['inputs'])


@pytest.mark.parametrize('case', REFERENCE['cases'], ids=lambda c: c['case_id'])
def test_independent_decimal_rate_closed_research_result_and_input_unchanged(case):
    original = deepcopy(case['inputs'])
    actual = calculate_leaf_expansion_rate(inputs=case['inputs'])
    quantity = actual['expansion_per_thermal_age']
    assert quantity['unit'] == 'm2/degC_day' and math.isfinite(quantity['value']) and quantity['value'] > 0
    assert quantity['value'] == pytest.approx(float(case['expected_m2_per_degC_day']), rel=1e-12, abs=0)
    assert actual['model_version'] == 'leaf-logistic-thermal-area-rate-research-v1'
    assert actual['scope'] == 'software_research_only' and actual['claim_scope'] == 'synthetic_crop_math_only'
    assert actual['gates'] == 'not_assessed' and len(actual['input_sha256']) == 64
    assert set(actual) == {'model_version', 'scope', 'claim_scope', 'gates', 'input_sha256', 'expansion_per_thermal_age'}
    assert case['inputs'] == original


def test_inflection_symmetry_linear_area_scaling_and_id_identity():
    p = inputs()
    values = []
    for age in (0, 2, 4, 6, 8):
        p['values']['thermal_age']['value'] = age
        values.append(calculate_leaf_expansion_rate(inputs=p)['expansion_per_thermal_age']['value'])
    assert values[0] == values[4] and values[1] == values[3] and values[0] < values[1] < values[2]
    assert values[2] == pytest.approx(.005, rel=1e-14)
    before = calculate_leaf_expansion_rate(inputs=p)
    assert calculate_leaf_expansion_rate(inputs=p) == before
    p['input_id'] = 'another-owned-probe'
    different_id = calculate_leaf_expansion_rate(inputs=p)
    assert different_id['input_sha256'] != before['input_sha256']
    assert different_id['expansion_per_thermal_age'] == before['expansion_per_thermal_age']
    p['values']['maximum_area']['value'] *= 8
    scaled = calculate_leaf_expansion_rate(inputs=p)
    assert scaled['expansion_per_thermal_age']['value'] == pytest.approx(8 * values[-1], rel=1e-14)


@pytest.mark.parametrize('field,unit', [('thermal_age', 'day'), ('maximum_area', 'cm2'),
    ('steepness', '1'), ('inflection_age', 'degC')])
def test_unit_mismatch_does_not_silently_convert_or_infer_source_table_units(field, unit):
    p = inputs(); p['values'][field]['unit'] = unit
    with pytest.raises(LeafExpansionHold, match='UNIT_HOLD'):
        calculate_leaf_expansion_rate(inputs=p)


@pytest.mark.parametrize('field,bad', [
    ('thermal_age', -1), ('inflection_age', -1), ('maximum_area', 0), ('steepness', 0),
    ('maximum_area', -1), ('steepness', -1), ('thermal_age', True), ('maximum_area', False),
    ('thermal_age', '2'), ('thermal_age', float('nan')), ('maximum_area', float('inf')),
    ('steepness', 10**1000),
])
def test_invalid_numeric_quantities_hold(field, bad):
    p = inputs(); p['values'][field]['value'] = bad
    with pytest.raises(LeafExpansionHold):
        calculate_leaf_expansion_rate(inputs=p)


@pytest.mark.parametrize('change', ['missing', 'extra', 'quantity-extra', 'actual-origin',
    'canopy-clock', 'internode-clock', 'empty-id', 'long-id', 'non-ascii-id', 'missing-id', 'not-object'])
def test_closed_synthetic_leaf_point_does_not_accept_existing_crop_or_internode_age(change):
    p = inputs()
    if change == 'missing': del p['values']['steepness']
    elif change == 'extra': p['area'] = 1
    elif change == 'quantity-extra': p['values']['thermal_age']['source'] = 'unreviewed'
    elif change == 'actual-origin': p['origin'] = 'reference_observation'
    elif change == 'canopy-clock': p['thermal_age_basis'] = 'canopy_temperature_sum'
    elif change == 'internode-clock': p['thermal_age_basis'] = 'since_internode_emergence'
    elif change == 'empty-id': p['input_id'] = ''
    elif change == 'long-id': p['input_id'] = 'a' * 201
    elif change == 'non-ascii-id': p['input_id'] = '무검토'
    elif change == 'missing-id': del p['input_id']
    elif change == 'not-object': p = None
    with pytest.raises(LeafExpansionHold, match='INPUT_HOLD'):
        calculate_leaf_expansion_rate(inputs=p)


@pytest.mark.parametrize('case', ['exponent-overflow', 'rate-overflow', 'positive-underflow'])
def test_unrepresentable_positive_rate_holds_instead_of_clipping_or_zero(case):
    p = inputs(); v = p['values']
    if case == 'exponent-overflow': v['thermal_age']['value'] = 1e308; v['steepness']['value'] = 2
    elif case == 'rate-overflow':
        v['thermal_age']['value'] = v['inflection_age']['value']
        v['maximum_area']['value'] = v['steepness']['value'] = 1e308
    else: v['thermal_age']['value'] = 1e308
    with pytest.raises(LeafExpansionHold, match='NUMERIC_HOLD'):
        calculate_leaf_expansion_rate(inputs=p)
