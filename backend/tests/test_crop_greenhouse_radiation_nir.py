"""Independent source/cavity NIR values, analytical limits and representability."""
from copy import deepcopy
from hashlib import sha256
import json
from math import fsum
from pathlib import Path
import runpy

import pytest

from app import crop_greenhouse_radiation_nir as model

ROOT = Path(__file__).resolve().parents[2]
FIXTURE = ROOT/'fixtures/crop-greenhouse-radiation-nir-reference-cases-v1.json'
DOCUMENT = json.loads(FIXTURE.read_bytes())
CASES = DOCUMENT['cases']


def run(case=None):
    return model.calculate_nir(scenario=(CASES[0] if case is None else case)['scenario'])


@pytest.mark.parametrize('case', CASES, ids=[c['case_id'] for c in CASES])
def test315_independent_source_and_cavity_scalars_with_partition_budgets(case):
    before = deepcopy(case); r = run(case)
    for group, values in case['expected_decimal'].items():
        assert set(values) == set(r[group])
        for key, text in values.items():
            assert r[group][key]['value'] == pytest.approx(float(text), rel=2e-13, abs=0), (group, key)
    assert len(r['partition_residuals']) == 4
    for key, q in r['partition_residuals'].items():
        assert abs(q['value']) <= r['partition_budgets'][key]['value']
    assert case == before


def test_generator_exact_fixture_replay_and_native_source_custody():
    path = ROOT/'research/crop-greenhouse-radiation-nir-reference.py'
    assert sha256(path.read_bytes()).hexdigest() == DOCUMENT['generator_sha256']
    oracle = runpy.run_path(str(path))['document']()
    assert oracle == DOCUMENT
    assert (json.dumps(oracle, indent=2, sort_keys=True, allow_nan=False)+'\n').encode() == FIXTURE.read_bytes()
    register = json.loads((ROOT/'research/crop-nir-source-register-20261013.json').read_bytes())
    assert register['review_context']['model'] == 'gpt-6.1-sol'
    assert register['review_context']['reasoning_effort'] == 'xhigh'
    assert not register['adopted_farm_data']
    assert register['sources'][0]['raw_sha256'] == model.SOURCE_SHA256
    assert sha256((ROOT/'LICENSES/GreenLight-BSD-3-Clause-Clear.txt').read_bytes()).hexdigest() == model.NOTICE_SHA256


def test_zero_absorption_and_unallocated_energy_limits_are_exact():
    for c in CASES:
        r = run(c); o, h = r['optics'], r['heat_components']
        if c['case_id'] in ('no-leaves', 'zero-extinction', 'lossless-canopy', 'reflective-cover', 'near-reflectors-lossless'):
            assert o['canopy_absorptance']['value'] == h['canopy_absorbed_nir']['value'] == 0
        if c['case_id'] == 'reflective-floor':assert o['floor_absorptance']['value'] == 0
        if c['case_id'] == 'reflective-cover':assert o['upward_reflectance']['value'] == 1
        if c['case_id'] in ('dark', 'no-NIR'):assert all(q['value'] == 0 for q in h.values())
        if c['case_id'] == 'construction-intercepts-all':
            assert h['construction_unallocated_nir']['value'] == r['diagnostics']['outdoor_nir']['value']
            assert all(h[k]['value'] == 0 for k in ('canopy_absorbed_nir', 'floor_absorbed_nir', 'upward_virtual_nir'))
        assert abs(fsum(q['value'] for q in h.values())-r['diagnostics']['outdoor_nir']['value']) <= (
            r['partition_budgets']['virtual_nir_energy']['value'])


def test_zero_canopy_simple_cover_floor_formula_and_sparse_positive_absorption():
    c = deepcopy(CASES[2]); r = run(c)
    cover = c['scenario']['values']['cover_nir_reflectance']['value']
    floor = c['scenario']['values']['floor_nir_reflectance']['value']
    assert r['optics']['floor_absorptance']['value'] == pytest.approx((1-cover)*(1-floor)/(1-cover*floor), rel=2e-13)
    r = run(CASES[12])
    assert r['optics']['canopy_transmittance']['value'] == 1.0
    assert r['optics']['canopy_absorptance']['value'] > 0


def test_radiation_scaling_identity_and_immutable_normalized_inputs():
    c = deepcopy(CASES[0]); before = deepcopy(c); r = run(c)
    assert r == run(c) and c == before
    assert r['code_sha256'] == sha256(Path(model.__file__).read_bytes()).hexdigest()
    c['scenario']['values']['outdoor_global_radiation']['value'] *= 2
    twice = run(c)
    assert twice['optics'] == r['optics']
    for key, q in r['heat_components'].items():assert twice['heat_components'][key]['value'] == 2*q['value']
    assert twice['input_sha256'] != r['input_sha256'] and twice['calculation_sha256'] != r['calculation_sha256']
    assert r['G0_G4'] == 'not_assessed' and r['claim_scope'] == 'synthetic_virtual_solar_NIR_math_only'
    assert r['time_coordinate'] == 'instantaneous_no_state_advance'


@pytest.mark.parametrize('key', list(model.INPUT_UNITS))
@pytest.mark.parametrize('fault', ['missing', 'unit', 'bool', 'string', 'nan', 'negative', 'quantity_extra'])
def test_closed_quantity_units_and_numeric_domain_holds(key, fault):
    c = deepcopy(CASES[0]); q = c['scenario']['values'][key]
    if fault == 'missing':del c['scenario']['values'][key]
    if fault == 'unit':q['unit'] = 'wrong'
    if fault == 'bool':q['value'] = True
    if fault == 'string':q['value'] = '0.5'
    if fault == 'nan':q['value'] = float('nan')
    if fault == 'negative':q['value'] = -1
    if fault == 'quantity_extra':q['guess'] = True
    with pytest.raises(model.RadiationNIRHold):run(c)


@pytest.mark.parametrize('fault', ['extra', 'blank_id', 'long_id', 'origin', 'type', 'actual_tau', 'PAR_fraction'])
def test_ambiguous_physical_cover_or_spectrum_and_closed_scenario_holds(fault):
    c = deepcopy(CASES[0]); s = c['scenario']
    if fault == 'extra':s['profile'] = {}
    if fault == 'blank_id':s['input_id'] = ' '
    if fault == 'long_id':s['input_id'] = 'x'*201
    if fault == 'origin':s['origin'] = 'farm_observation'
    if fault == 'type':c['scenario'] = None
    if fault == 'actual_tau':s['values']['cover_nir_transmittance'] = {'value':.7, 'unit':'1'}
    if fault == 'PAR_fraction':s['values']['solar_par_fraction'] = s['values'].pop('solar_nir_fraction')
    with pytest.raises(model.RadiationNIRHold):run(c)


@pytest.mark.parametrize('key', [k for k,u in model.INPUT_UNITS.items() if u == '1'])
def test_fraction_above_one_holds(key):
    c = deepcopy(CASES[0]); c['scenario']['values'][key]['value'] = 1.01
    with pytest.raises(model.RadiationNIRHold, match='OPTICS_HOLD'):run(c)


@pytest.mark.parametrize('dark', [False, True])
@pytest.mark.parametrize('leaf,rho', [(0,.35),(2,1)])
def test_trapped_lossless_cavity_is_singular_even_in_dark(dark, leaf, rho):
    c = deepcopy(CASES[0]); v = c['scenario']['values']
    for key in ['cover_nir_reflectance','floor_nir_reflectance']:v[key]['value'] = 1
    v['canopy_nir_reflectance']['value'] = rho; v['leaf_area_index']['value'] = leaf
    if dark:v['outdoor_global_radiation']['value'] = 0
    with pytest.raises(model.RadiationNIRHold, match='singular reflection denominator'):run(c)


@pytest.mark.parametrize('fault', ['input_overflow','depth_overflow','attenuation_underflow','radiation_underflow'])
def test_numeric_representability_holds_without_clipping_or_fallback(fault):
    c = deepcopy(CASES[0]); v = c['scenario']['values']
    if fault == 'input_overflow':v['outdoor_global_radiation']['value'] = 10**400
    if fault == 'depth_overflow':
        v['nir_extinction_coefficient']['value'] = 1e308; v['leaf_area_index']['value'] = 1e308
    if fault == 'attenuation_underflow':v['nir_extinction_coefficient']['value'] = 1e6
    if fault == 'radiation_underflow':v['outdoor_global_radiation']['value'] = 5e-324
    with pytest.raises(model.RadiationNIRHold, match='NUMERIC_HOLD'):run(c)
