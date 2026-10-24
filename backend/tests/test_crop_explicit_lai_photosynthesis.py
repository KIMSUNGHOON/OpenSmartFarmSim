from copy import deepcopy
from hashlib import sha256
import json
from pathlib import Path

import pytest

from app import crop_explicit_lai_photosynthesis as model
from app import crop_growth_rates as original

ROOT = Path(__file__).resolve().parents[2]
PROFILE_RAW = (ROOT/'fixtures/crop-growth-reference-parameters-v1.json').read_bytes()
PROFILE = original.ReferenceParameters(PROFILE_RAW)
OLD = json.loads((ROOT/'fixtures/crop-growth-reference-cases-v1.json').read_bytes())['cases']
REFERENCE = json.loads((ROOT/'fixtures/crop-explicit-lai-photosynthesis-reference-v1.json').read_bytes())


def inputs(case=0, lai=None):
    case = OLD[case]
    return {'input_id': 'explicit-optical-probe', 'origin': 'synthetic', 'values': {
        'buffer': deepcopy(case['state']['values']['buffer']),
        'leaf_area_index': {'value': PROFILE.values['sla'] * case['state']['values']['leaf']['value'] if lai is None else lai,
                            'unit': 'm2_leaf/m2_floor'}, **deepcopy(case['forcing']['values'])}}


def calculate(value, profile=PROFILE):
    return model.calculate_photosynthesis(inputs=value, profile=profile)


@pytest.mark.parametrize('case', REFERENCE['cases'], ids=lambda row: row['case_id'])
def test_independent_decimal_matrix_and_explicit_domain_holds(case):
    value = deepcopy(case['inputs']); before = deepcopy(value)
    if case['status'] != 'supported':
        with pytest.raises(model.ExplicitLaiPhotosynthesisHold, match='COMPENSATION_POINT_HOLD'): calculate(value)
    else:
        expected = case['expected_decimal']; result = calculate(value)
        assert result['photosynthesis']['value'] == pytest.approx(float(expected['photosynthesis']), rel=5e-12, abs=0)
        for key in ('compensation_point_ppm', 'electron_transport'):
            if expected[key] is None: assert result['diagnostics'][key] is None
            else: assert result['diagnostics'][key] == pytest.approx(float(expected[key]), rel=5e-12, abs=0)
    assert value == before


@pytest.mark.parametrize('index', range(4))
def test_legacy_photo_and_diagnostics_identical_without_changing_original_model(index):
    case = deepcopy(OLD[index]); before = deepcopy(case)
    expected = original.calculate_rates(state=case['state'], forcing=case['forcing'], removals=case['removals'], profile=PROFILE)
    value = inputs(index); saved = deepcopy(value); result = calculate(value)
    assert result['photosynthesis'] == expected['photosynthesis']
    assert result['lai'] == expected['lai'] and result['diagnostics'] == expected['diagnostics']
    assert value == saved and case == before and calculate(value) == result
    assert result['G0_G4'] == 'not_assessed' and result['claim_scope'] == 'synthetic_explicit_lai_photosynthesis_math_only'
    assert result['component_code_sha256'] == sha256(Path(original.__file__).read_bytes()).hexdigest()


@pytest.mark.parametrize('change', [
    lambda p: p.update(extra=True), lambda p: p.update(origin='reference_observation'),
    lambda p: p.update(input_id=''), lambda p: p.update(input_id='a'*201),
    lambda p: p['values'].pop('leaf_area_index'), lambda p: p['values'].update(leaf={'value': 1, 'unit': original.MASS_UNIT}),
    lambda p: p['values']['leaf_area_index'].update(value=True),
    lambda p: p['values']['leaf_area_index'].update(value='1'),
    lambda p: p['values']['leaf_area_index'].update(value=-1),
    lambda p: p['values']['leaf_area_index'].update(value=float('nan')),
    lambda p: p['values']['leaf_area_index'].update(value=float('inf')),
    lambda p: p['values']['leaf_area_index'].update(unit='m2'),
    lambda p: p['values']['buffer'].update(unit='mg_DM/m2_floor'),
    lambda p: p['values']['co2'].update(value=0),
    lambda p: p['values']['canopy_temperature'].update(value=35),
    lambda p: p['values']['canopy_temperature'].update(value=9),
    lambda p: p['values']['par_above_canopy'].update(value=-1)])
def test_no_implicit_mass_or_unit_domain_scope_fallback(change):
    value = inputs(); change(value)
    with pytest.raises(model.ExplicitLaiPhotosynthesisHold): calculate(value)


@pytest.mark.parametrize('temperature,co2,lai,accepted', [
    (10,400,.49,False),(10,400,.51,True),(17,400,.149,False),(17,400,.151,True),
    (23,400,.02,False),(23,400,.023,True),(34,400,.1,False),(34,400,.11,True),
    (17,40,.14,False),(17,40,.3,True),(17,40,.72,False),
    (20,400,0,True),(17,400,0,False),(23,400,0,False)])
def test_existing_source_compensation_domain_and_low_co2_upper_bound(temperature, co2, lai, accepted):
    value = inputs(lai=lai)
    for key, number in [('canopy_temperature',temperature),('co2',co2),('par_above_canopy',200)]:
        value['values'][key]['value'] = number
    if accepted: assert calculate(value)['photosynthesis']['value'] >= 0
    else:
        with pytest.raises(model.ExplicitLaiPhotosynthesisHold, match='COMPENSATION_POINT_HOLD'): calculate(value)


def test_dark_does_not_invent_gamma_but_other_input_domains_still_hold():
    value = inputs(lai=0); value['values']['canopy_temperature']['value'] = 17; value['values']['par_above_canopy']['value'] = 0
    result = calculate(value)
    assert result['photosynthesis']['value'] == 0 and result['diagnostics']['compensation_point_ppm'] is None
    value['values']['canopy_temperature']['value'] = 100
    with pytest.raises(model.ExplicitLaiPhotosynthesisHold): calculate(value)


def test_lai_and_buffer_are_independent_explicit_inputs_and_output_is_not_aliased():
    value = inputs(); a = calculate(value); value['values']['leaf_area_index']['value'] *= 2; b = calculate(value)
    assert a['input_sha256'] != b['input_sha256'] and a['photosynthesis'] != b['photosynthesis']
    assert a['inputs']['values']['buffer'] == b['inputs']['values']['buffer']
    value['values']['buffer']['value'] = 0; c = calculate(value)
    assert c['photosynthesis'] != b['photosynthesis'] and c['lai'] == b['lai']
    c['inputs']['values']['buffer']['value'] = 777
    assert value['values']['buffer']['value'] == 0


@pytest.mark.parametrize('profile', [None, object()])
def test_only_exact_pinned_original_profile_type(profile):
    with pytest.raises(model.ExplicitLaiPhotosynthesisHold, match='PROFILE_HOLD'): calculate(inputs(), profile)


def test_raw_input_identity_keeps_original_bytes_while_normalized_numbers_are_equal():
    value = inputs(lai=1); first = calculate(value)
    value['values']['leaf_area_index']['value'] = 1.0; second = calculate(value)
    assert first['input_sha256'] == second['input_sha256']
    assert first['raw_input_sha256'] != second['raw_input_sha256']
