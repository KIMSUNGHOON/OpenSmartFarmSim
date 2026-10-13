"""Independent solar partition and actual crop consumer checks."""
from copy import deepcopy
from hashlib import sha256
import importlib.util
import json
from math import fsum
from pathlib import Path

import pytest

from app import crop_greenhouse_radiation_par as model
from app import crop_growth_rates as crop

ROOT = Path(__file__).resolve().parents[2]
FIXTURE = ROOT/'fixtures/crop-greenhouse-radiation-par-reference-cases-v1.json'
DOCUMENT = json.loads(FIXTURE.read_bytes())
CASES = DOCUMENT['cases']


@pytest.fixture(scope='module')
def profile():
    return crop.ReferenceParameters((ROOT/'fixtures/crop-growth-reference-parameters-v1.json').read_bytes())


def run(scenario, profile):
    return model.calculate_par(scenario=scenario, profile=profile)


@pytest.mark.parametrize('case', CASES, ids=lambda c: c['case_id'])
def test_independent_decimal_partitions_and_photon_coordinates(case, profile):
    original = deepcopy(case['scenario'])
    result = run(original, profile)
    assert original == case['scenario']
    assert run(original, profile) == result
    actual = {k: q['value'] for group in ('diagnostics', 'interior_partition',
        'exterior_PAR_partition', 'crop_forcing', 'absorbed_photons') for k, q in result[group].items()}
    actual['interior_sum'] = fsum(q['value'] for q in result['interior_partition'].values())
    actual['exterior_PAR_sum'] = fsum(q['value'] for q in result['exterior_PAR_partition'].values())
    assert set(actual) == set(case['expected_decimal'])-{'electron_transport_at_20C'}
    for name, value in actual.items():
        expected = float(case['expected_decimal'][name])
        assert value == pytest.approx(expected, rel=2e-13, abs=0), name
        if expected == 0:
            assert value == 0
    for name, residual in result['partition_residuals'].items():
        assert abs(residual['value']) <= result['partition_budgets'][name]['value']
    assert result['heat_components']['canopy_absorbed_par'] == result['interior_partition']['canopy_absorbed']
    assert result['heat_components']['floor_absorbed_par'] == result['interior_partition']['floor_absorbed']
    assert all(q['unit'] == model.HEAT for q in result['exterior_PAR_partition'].values())
    assert result['crop_forcing']['par_above_canopy']['unit'] == crop.FORCING_UNITS['par_above_canopy']
    assert result['claim_scope'] == 'synthetic_prescribed_solar_par_math_only'
    assert result['G0_G4'] == 'not_assessed'
    assert result['time_coordinate'] == 'instantaneous_no_state_advance'


def test_independent_generator_reproduces_pinned_fixture_bytes():
    path = ROOT/'research/crop-greenhouse-radiation-par-reference.py'
    spec = importlib.util.spec_from_file_location('independent_par_reference', path)
    reference = importlib.util.module_from_spec(spec); spec.loader.exec_module(reference)
    assert reference.document() == DOCUMENT
    assert (json.dumps(reference.document(), indent=2, sort_keys=True, allow_nan=False)+'\n').encode() == FIXTURE.read_bytes()
    assert DOCUMENT['generator_sha256'] == sha256(path.read_bytes()).hexdigest()


@pytest.mark.parametrize('case', CASES, ids=lambda c: c['case_id'])
def test_actual_crop_receives_incident_photons_once_against_independent_electron_transport(case, profile):
    scenario = case['scenario']; result = run(scenario, profile)
    inputs = deepcopy(json.loads((ROOT/'fixtures/crop-growth-reference-cases-v1.json').read_bytes())['cases'][0])
    inputs['state']['values']['leaf']['value'] = scenario['values']['leaf_area_index']['value']/profile.values['sla']
    inputs['forcing']['values']['canopy_temperature']['value'] = 20
    inputs['forcing']['values']['par_above_canopy'] = result['crop_forcing']['par_above_canopy']
    actual = crop.calculate_rates(**{k: inputs[k] for k in ('state', 'forcing', 'removals')}, profile=profile)
    expected = float(case['expected_decimal']['electron_transport_at_20C'])
    assert actual['diagnostics']['electron_transport'] == pytest.approx(expected, rel=5e-12, abs=0)
    if expected == 0:
        assert actual['photosynthesis']['value'] == 0
    if case['case_id'] == 'nominal':
        inputs['forcing']['values']['par_above_canopy'] = result['absorbed_photons']['par_absorbed_canopy']
        intercepted_twice = crop.calculate_rates(**{k: inputs[k] for k in ('state', 'forcing', 'removals')}, profile=profile)
        assert intercepted_twice['diagnostics']['electron_transport'] < expected*0.99


def test_linear_scaling_and_hashes_bind_explicit_input(profile):
    s = deepcopy(CASES[0]['scenario']); first = run(s, profile)
    s['values']['outdoor_global_radiation']['value'] *= 2
    second = run(s, profile)
    for group in ('diagnostics', 'interior_partition', 'exterior_PAR_partition', 'crop_forcing', 'absorbed_photons'):
        for name, q in first[group].items():
            assert second[group][name]['value'] == pytest.approx(2*q['value'], rel=2e-14, abs=0)
    assert first['input_sha256'] != second['input_sha256']
    assert first['code_sha256'] == sha256((ROOT/'backend/app/crop_greenhouse_radiation_par.py').read_bytes()).hexdigest()
    assert first['profile_sha256'] == DOCUMENT['profile_sha256']
    assert first['notice_sha256'] == sha256((ROOT/'LICENSES/GreenLight-BSD-3-Clause-Clear.txt').read_bytes()).hexdigest()
    s = deepcopy(CASES[0]['scenario']); s['input_id'] += '-revision'
    assert run(s, profile)['input_sha256'] != first['input_sha256']


@pytest.mark.parametrize('name', model.INPUT_UNITS)
@pytest.mark.parametrize('bad', [True, '1', None, float('nan'), float('inf'), -1, 10**400])
def test_invalid_values_hold(profile, name, bad):
    s = deepcopy(CASES[0]['scenario']); s['values'][name]['value'] = bad
    with pytest.raises(model.RadiationPARHold):
        run(s, profile)


@pytest.mark.parametrize('fault', ['missing', 'extra', 'unit', 'quantity_extra', 'quantity_type',
    'block_type', 'scenario_type', 'origin', 'id', 'id_long', 'profile', 'cover_sum',
    'fraction', 'conversion_zero', 'product_underflow', 'photon_overflow', 'attenuation_underflow'])
def test_closed_schema_optical_and_numeric_holds(profile, fault):
    s = deepcopy(CASES[0]['scenario'])
    if fault == 'missing': del s['values']['leaf_area_index']
    if fault == 'extra': s['NIR'] = 0
    if fault == 'unit': s['values']['outdoor_global_radiation']['unit'] = 'umol_photons/m2_floor/s'
    if fault == 'quantity_extra': s['values']['leaf_area_index']['default'] = 2
    if fault == 'quantity_type': s['values']['leaf_area_index'] = 2
    if fault == 'block_type': s['values'] = []
    if fault == 'scenario_type': s = []
    if fault == 'origin': s['origin'] = 'farm_observation'
    if fault == 'id': s['input_id'] = ' '
    if fault == 'id_long': s['input_id'] = 'a'*201
    if fault == 'profile': profile = object()
    if fault == 'cover_sum': s['values']['cover_par_reflectance']['value'] = 0.9
    if fault == 'fraction': s['values']['solar_par_fraction']['value'] = 1.1
    if fault == 'conversion_zero': s['values']['solar_par_photon_conversion']['value'] = 0
    if fault == 'product_underflow':
        s['values']['outdoor_global_radiation']['value'] = 1e-300
        s['values']['solar_par_fraction']['value'] = 1e-300
    if fault == 'photon_overflow':
        s['values']['solar_par_photon_conversion']['value'] = 1e308
    if fault == 'attenuation_underflow': s['values']['leaf_area_index']['value'] = 2000
    with pytest.raises(model.RadiationPARHold):
        run(s, profile)
