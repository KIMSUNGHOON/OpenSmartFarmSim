"""Independent whole-stage reference and actual current-state PAR composition."""
from copy import deepcopy
from decimal import Decimal, localcontext
from hashlib import sha256
import json
from pathlib import Path
import runpy

import pytest

from app import crop_greenhouse_radiation_par_joint as model
from app.crop_growth_rates import ReferenceParameters as Growth
from app.crop_fruit_cohorts import ReferenceFruitCohortParameters as Cohort
from app.crop_fruit_transport import ReferenceFruitTransportParameters as Transport
from app.crop_canopy_exchange import ReferenceParameters as Exchange

ROOT = Path(__file__).resolve().parents[2]


@pytest.fixture(scope='module')
def profiles():
    return {key: kind((ROOT/'fixtures'/name).read_bytes()) for key, kind, name in (
        ('growth_profile', Growth, 'crop-growth-reference-parameters-v1.json'),
        ('cohort_profile', Cohort, 'crop-fruit-cohort-reference-parameters-v1.json'),
        ('transport_profile', Transport, 'crop-fruit-transport-reference-parameters-v1.json'),
        ('exchange_profile', Exchange, 'crop-canopy-exchange-reference-parameters-v1.json'))}


def inputs():
    s = json.loads((ROOT/'fixtures/crop-climate-joint-rhs-reference-cases-v1.json').read_bytes())['cases'][0]['scenario']
    s['forcing']['canopy_non_par_heat'] = s['forcing'].pop('canopy_external_heat')
    del s['forcing']['par_above_canopy']
    solar = json.loads((ROOT/'fixtures/crop-greenhouse-radiation-par-reference-cases-v1.json').read_bytes())['cases'][0]['scenario']
    del solar['values']['leaf_area_index']
    return s, solar


def run(s, solar, profiles):
    return model.evaluate_rhs(scenario=s, solar=solar, **profiles)


@pytest.fixture(scope='module')
def independent():
    old = runpy.run_path(str(ROOT/'research/crop-climate-joint-rhs-reference.py'))
    for name, digest in old['INPUTS'].items():
        assert sha256((ROOT/name).read_bytes()).hexdigest() == digest
    def parameters(name):
        rows = json.loads((ROOT/'fixtures'/name).read_bytes())['parameters']
        return {k: Decimal(v.get('source_value', str(v['value']))) for k, v in rows.items()}
    oracles = {key: runpy.run_path(str(ROOT/'research'/name))[function] for key, name, function in (
        ('startup', 'crop-plant-startup-reference.py', 'calculate'),
        ('plant', 'crop-integration-reference.py', 'decimal_rhs'),
        ('thermal', 'crop-canopy-air-dynamics-reference.py', 'rhs'),
        ('capacity', 'crop-canopy-energy-transport-reference.py', 'transport'))}
    return old['calculate'], parameters, oracles, runpy.run_path(
        str(ROOT/'research/crop-greenhouse-radiation-par-reference.py'))['reference']


@pytest.mark.parametrize('case', ['day', 'dark', 'negative-other-heat', 'changed-leaf'])
def test_independent_full_crop_climate_stage_and_all_seven_balances(profiles, independent, case):
    s, solar = inputs()
    if case == 'dark': solar['values']['outdoor_global_radiation']['value'] = 0
    if case == 'negative-other-heat': s['forcing']['canopy_non_par_heat']['value'] = -50
    if case == 'changed-leaf':
        s['plant_state']['leaf']['value'] *= 1.15
        s['climate_state']['canopy_sensible_energy']['value'] *= 1.15
    before = deepcopy((s, solar)); r = run(s, solar, profiles); actual = r['joint_rhs']
    calculate, parameters, oracles, par_reference = independent
    with localcontext() as ctx:
        ctx.prec = 80
        p = parameters('crop-growth-reference-parameters-v1.json')
        ref_solar = deepcopy(solar)
        ref_solar['values']['leaf_area_index'] = {'value': str(p['sla']*Decimal(str(s['plant_state']['leaf']['value']))),
                                                'unit': 'm2_leaf/m2_floor'}
        par = par_reference(ref_solar)
        ref = deepcopy(s)
        non_par = ref['forcing'].pop('canopy_non_par_heat')
        ref['forcing']['canopy_external_heat'] = {'value': str(Decimal(str(non_par['value']))+
            Decimal(par['canopy_absorbed'])), 'unit': 'W/m2_floor'}
        ref['forcing']['par_above_canopy'] = {'value': par['par_above_canopy'], 'unit': 'umol_photons/m2_floor/s'}
        expected = calculate(ref, p, parameters('crop-fruit-cohort-reference-parameters-v1.json'),
            parameters('crop-canopy-exchange-reference-parameters-v1.json'), oracles)
    groups = {'derived': actual['derived'], 'plant_derivatives': actual['derivatives']['plant'],
        'climate_derivatives': actual['derivatives']['climate'], 'exchange': actual['exchange']['exchange']}
    for name, group in groups.items():
        for key, text in expected[name].items():
            assert group[key]['value'] == pytest.approx(float(text), rel=5e-12, abs=5e-14), (name, key)
    for name, key in (('dC', 'fruit_carbohydrate'), ('dN', 'fruit_number')):
        for q, text in zip(actual['derivatives']['cohorts'][key], expected[name], strict=True):
            assert q['value'] == pytest.approx(float(text), rel=5e-12, abs=5e-14)
    for key, q in actual['balance_residuals'].items():
        assert abs(q['value']) <= actual['balance_budgets'][key]['value']
    assert len(actual['balance_residuals']) == 7
    assert (s, solar) == before
    assert run(s, solar, profiles) == r
    assert r['G0_G4'] == 'not_assessed'
    assert r['claim_scope'] == 'synthetic_current_state_PAR_joint_rhs_only'


def test_one_current_trial_and_light_changes_canopy_heat_and_crop_without_air_credit(profiles, monkeypatch):
    s, solar = inputs(); seen = {'PAR': [], 'joint': []}
    for module, name, label in ((model.radiation, 'calculate_par', 'PAR'), (model.joint, 'evaluate_rhs', 'joint')):
        original = getattr(module, name)
        def record(*, _original=original, _label=label, **kw):
            seen[_label].append(deepcopy(kw['scenario'])); return _original(**kw)
        monkeypatch.setattr(module, name, record)
    day = run(s, solar, profiles)
    assert {k: len(v) for k, v in seen.items()} == {'PAR': 1, 'joint': 1}
    assert seen['PAR'][0]['values']['leaf_area_index'] == day['joint_rhs']['derived']['leaf_area_index']
    assert seen['joint'][0]['forcing']['par_above_canopy'] == day['radiation']['crop_forcing']['par_above_canopy']
    solar['values']['outdoor_global_radiation']['value'] = 0
    dark = run(s, solar, profiles)
    heat_delta = day['joint_rhs']['derivatives']['climate']['canopy_sensible_energy']['value']-(
        dark['joint_rhs']['derivatives']['climate']['canopy_sensible_energy']['value'])
    assert heat_delta == pytest.approx(day['heat_composition']['canopy_absorbed_par']['value'], rel=5e-13)
    for key in ('air_temperature', 'air_vapor_mass'):
        assert day['joint_rhs']['derivatives']['climate'][key] == dark['joint_rhs']['derivatives']['climate'][key]
    assert day['joint_rhs']['crop']['photosynthesis']['value'] > 0
    assert dark['joint_rhs']['crop']['photosynthesis']['value'] == 0
    solar['values']['outdoor_global_radiation']['value'] = 600
    s['plant_state']['leaf']['value'] *= 1.15
    s['climate_state']['canopy_sensible_energy']['value'] *= 1.15
    changed = run(s, solar, profiles)
    assert changed['radiation']['crop_forcing'] == day['radiation']['crop_forcing']
    assert changed['heat_composition']['canopy_absorbed_par'] != day['heat_composition']['canopy_absorbed_par']
    assert changed['calculation_sha256'] != day['calculation_sha256']
    assert day['code_sha256'] == sha256((ROOT/'backend/app/crop_greenhouse_radiation_par_joint.py').read_bytes()).hexdigest()


@pytest.mark.parametrize('fault', ['old_PAR', 'old_heat', 'missing_non_PAR', 'unit', 'nonfinite',
    'caller_LAI', 'missing_solar', 'mixed_origin', 'empty_leaf', 'leaf_unit', 'profile', 'solar_type',
    'scenario_extra', 'optics', 'photon_overflow'])
def test_ambiguous_double_count_and_closed_input_holds(profiles, fault):
    s, solar = inputs(); profiles = dict(profiles)
    if fault == 'old_PAR': s['forcing']['par_above_canopy'] = {'value': 1000, 'unit': model.radiation.PHOTONS}
    if fault == 'old_heat': s['forcing']['canopy_external_heat'] = {'value': 100, 'unit': model.radiation.HEAT}
    if fault == 'missing_non_PAR': del s['forcing']['canopy_non_par_heat']
    if fault == 'unit': s['forcing']['canopy_non_par_heat']['unit'] = model.radiation.PHOTONS
    if fault == 'nonfinite': s['forcing']['canopy_non_par_heat']['value'] = float('nan')
    if fault == 'caller_LAI': solar['values']['leaf_area_index'] = {'value': 2, 'unit': 'm2_leaf/m2_floor'}
    if fault == 'missing_solar': del solar['values']['solar_par_fraction']
    if fault == 'mixed_origin': solar['origin'] = 'reference_calculation'
    if fault == 'empty_leaf': s['plant_state']['leaf']['value'] = 0
    if fault == 'leaf_unit': s['plant_state']['leaf']['unit'] = 'kg'
    if fault == 'profile': profiles['growth_profile'] = object()
    if fault == 'solar_type': solar = []
    if fault == 'scenario_extra': s['old_model'] = True
    if fault == 'optics': solar['values']['cover_par_transmittance']['value'] = 2
    if fault == 'photon_overflow': solar['values']['solar_par_photon_conversion']['value'] = 1e308
    with pytest.raises(model.RadiationPARJointHold):
        run(s, solar, profiles)
