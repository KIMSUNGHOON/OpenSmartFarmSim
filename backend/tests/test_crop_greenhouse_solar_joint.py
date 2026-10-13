"""Independent full joint equations and once-only current-state solar/air forcing."""
from copy import deepcopy
from decimal import Decimal, localcontext
from hashlib import sha256
import json
from math import fsum
from pathlib import Path
import runpy

import pytest

from app import crop_greenhouse_solar_joint as model
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
    s['forcing']['canopy_non_solar_heat'] = s['forcing'].pop('canopy_external_heat')
    del s['forcing']['par_above_canopy']
    par = json.loads((ROOT/'fixtures/crop-greenhouse-radiation-par-reference-cases-v1.json').read_bytes())['cases'][0]['scenario']
    nir = json.loads((ROOT/'fixtures/crop-greenhouse-radiation-nir-reference-cases-v1.json').read_bytes())['cases'][0]['scenario']
    values = {**par['values'], **nir['values']}; del values['leaf_area_index']
    solar = {'input_id':'synthetic-shared-solar', 'origin':'synthetic', 'values':values}
    weather = json.loads((ROOT/'fixtures/crop-greenhouse-ventilation-joint-reference-cases-v1.json').read_bytes())['cases'][0]['ventilation']
    return {'scenario':s, 'solar':solar, 'ventilation':weather}


@pytest.fixture(scope='module')
def independent():
    prior = runpy.run_path(str(ROOT/'research/crop-climate-joint-rhs-reference.py'))
    for name, digest in prior['INPUTS'].items():assert sha256((ROOT/name).read_bytes()).hexdigest() == digest
    def parameters(name):
        rows = json.loads((ROOT/'fixtures'/name).read_bytes())['parameters']
        return {k:Decimal(v.get('source_value',str(v['value']))) for k,v in rows.items()}
    oracles = {key:runpy.run_path(str(ROOT/'research'/name))[function] for key,name,function in (
        ('startup','crop-plant-startup-reference.py','calculate'),
        ('plant','crop-integration-reference.py','decimal_rhs'),
        ('thermal','crop-canopy-air-dynamics-reference.py','rhs'),
        ('capacity','crop-canopy-energy-transport-reference.py','transport'))}
    return prior['calculate'], parameters, oracles, {
        band:runpy.run_path(str(ROOT/f'research/crop-greenhouse-radiation-{band}-reference.py'))['reference']
        for band in ('par','nir')}


@pytest.mark.parametrize('case', ['day','dark','reverse-air','signed-other-heat','changed-leaf'])
def test585_independent_full_state_rates_exchange_and_seven_balances(profiles, independent, case):
    c = inputs(); s, sun, weather = c['scenario'], c['solar'], c['ventilation']
    if case == 'dark':sun['values']['outdoor_global_radiation']['value'] = 0
    if case == 'reverse-air':
        weather['forcing']['outdoor_air_temperature']['value'] = 28
        weather['forcing']['outdoor_vapor_pressure']['value'] = 2800
    if case == 'signed-other-heat':s['forcing']['canopy_non_solar_heat']['value'] = -50
    if case == 'changed-leaf':
        s['plant_state']['leaf']['value'] *= 1.15
        s['climate_state']['canopy_sensible_energy']['value'] *= 1.15
    before = deepcopy(c); r = model.evaluate_rhs(**c, **profiles); actual = r['joint_rhs']
    calculate, parameters, oracles, optics = independent
    with localcontext() as ctx:
        ctx.prec = 80
        p = parameters('crop-growth-reference-parameters-v1.json')
        ep = parameters('crop-canopy-exchange-reference-parameters-v1.json')
        lai = p['sla']*Decimal(str(s['plant_state']['leaf']['value']))
        def boundary(band, units):
            values = {k:q for k,q in sun['values'].items() if k in units}
            values['leaf_area_index'] = {'value':lai,'unit':'m2_leaf/m2_floor'}
            return optics[band]({**sun,'values':values})
        par = boundary('par',model.par.radiation.INPUT_UNITS)
        nir = boundary('nir',model.nir.INPUT_UNITS)
        ref = deepcopy(s); other = Decimal(str(ref['forcing'].pop('canopy_non_solar_heat')['value']))
        ref['forcing']['canopy_external_heat'] = {'value':str(other+Decimal(par['canopy_absorbed'])+
            Decimal(nir['heat_components']['canopy_absorbed_nir'])),'unit':'W/m2_floor'}
        ref['forcing']['par_above_canopy'] = {'value':par['par_above_canopy'],'unit':'umol_photons/m2_floor/s'}
        pv = {k:Decimal(str(q['value'])) for k,q in s['parameters'].items()}
        w = {k:Decimal(str(q['value'])) for k,q in weather['forcing'].items()}
        air = Decimal(str(s['climate_state']['air_temperature']['value']))
        vapor = Decimal(str(s['climate_state']['air_vapor_mass']['value']))
        rho_out = w['outdoor_vapor_pressure']/(pv['vapor_gas_constant']*(w['outdoor_air_temperature']+Decimal('273.15')))
        sensible = pv['air_capacity_density']*ep['air_heat_capacity']*w['volume_exchange_per_floor_area']*(w['outdoor_air_temperature']-air)
        water = w['volume_exchange_per_floor_area']*(rho_out-vapor/pv['air_volume_per_floor_area'])
        for key, value in [('air_external_sensible_heat',sensible),('air_external_vapor',water)]:
            ref['forcing'][key]['value'] = str(Decimal(str(s['forcing'][key]['value']))+value)
        expected = calculate(ref,p,parameters('crop-fruit-cohort-reference-parameters-v1.json'),ep,oracles)
    for name, group in {'derived':actual['derived'],'plant_derivatives':actual['derivatives']['plant'],
            'climate_derivatives':actual['derivatives']['climate'],'exchange':actual['exchange']['exchange']}.items():
        for key, text in expected[name].items():assert group[key]['value'] == pytest.approx(float(text),rel=5e-12,abs=5e-14)
    for name,key in [('dC','fruit_carbohydrate'),('dN','fruit_number')]:
        for q,text in zip(actual['derivatives']['cohorts'][key],expected[name],strict=True):
            assert q['value'] == pytest.approx(float(text),rel=5e-12,abs=5e-14)
    assert len(actual['balance_residuals']) == 7
    for key,q in actual['balance_residuals'].items():assert abs(q['value']) <= actual['balance_budgets'][key]['value']
    assert c == before and model.evaluate_rhs(**c,**profiles) == r


def test_actual_once_only_calls_shared_current_state_and_original_input_identity(profiles, monkeypatch):
    seen = {k:[] for k in ['PAR','NIR','vent','joint']}
    for module,name,key in [(model.par.radiation,'calculate_par','PAR'),(model.nir,'calculate_nir','NIR'),
            (model.vent,'calculate_ventilation','vent'),(model.joint,'evaluate_rhs','joint')]:
        original = getattr(module,name)
        def record(*,_original=original,_key=key,**kwargs):
            r = _original(**kwargs);seen[_key].append(r);return r
        monkeypatch.setattr(module,name,record)
    c = inputs(); r = model.evaluate_rhs(**c,**profiles)
    assert {k:len(v) for k,v in seen.items()} == {'PAR':1,'NIR':1,'vent':1,'joint':1}
    for key in ['PAR','NIR']:
        assert seen[key][0]['scenario']['values']['leaf_area_index'] == r['joint_rhs']['derived']['leaf_area_index']
    assert r['joint_rhs']['scenario']['forcing']['par_above_canopy'] == seen['PAR'][0]['crop_forcing']['par_above_canopy']
    assert r['outdoor']['scenario']['state'] == {k:r['joint_rhs']['scenario']['climate_state'][k] for k in model.vent.STATE_UNITS}
    h = r['heat_composition']
    assert h['canopy_external_heat']['value'] == fsum((fsum((h['canopy_non_solar_heat']['value'],
        h['canopy_absorbed_nir']['value'])),h['canopy_absorbed_par']['value']))
    for key,q in r['outdoor']['forcing_contribution'].items():
        assert r['joint_rhs']['scenario']['forcing'][key]['value'] == fsum((c['scenario']['forcing'][key]['value'],q['value']))
    assert r['scenario']['forcing'] == c['scenario']['forcing']
    assert r['solar']['values'] == c['solar']['values'] and r['ventilation'] == c['ventilation']
    assert r['code_sha256'] == sha256(Path(model.__file__).read_bytes()).hexdigest()
    assert r['source_sha256']['NIR'] == model.nir.SOURCE_SHA256
    assert r['notice_sha256']['exchange'] == profiles['exchange_profile'].notice_sha256


def test_NIR_changes_only_current_canopy_heat_and_dark_removes_both_solar_bands(profiles):
    c = inputs(); day = model.evaluate_rhs(**c,**profiles)
    c['solar']['values']['canopy_nir_reflectance']['value'] = 0
    changed = model.evaluate_rhs(**c,**profiles)
    assert changed['joint_rhs']['crop']['photosynthesis'] == day['joint_rhs']['crop']['photosynthesis']
    assert changed['heat_composition']['canopy_absorbed_nir'] != day['heat_composition']['canopy_absorbed_nir']
    for key in ['air_temperature','air_vapor_mass']:
        assert changed['joint_rhs']['derivatives']['climate'][key] == day['joint_rhs']['derivatives']['climate'][key]
    c = inputs();c['solar']['values']['outdoor_global_radiation']['value'] = 0
    dark = model.evaluate_rhs(**c,**profiles)
    assert dark['joint_rhs']['crop']['photosynthesis']['value'] == 0
    delta = day['joint_rhs']['derivatives']['climate']['canopy_sensible_energy']['value']-(
        dark['joint_rhs']['derivatives']['climate']['canopy_sensible_energy']['value'])
    assert delta == pytest.approx(fsum(day['heat_composition'][k]['value'] for k in (
        'canopy_absorbed_par','canopy_absorbed_nir')),rel=5e-13)
    assert day['G0_G4'] == 'not_assessed' and day['claim_scope'] == 'synthetic_current_state_solar_ventilation_rhs_only'
    assert day['calculation_sha256'] != dark['calculation_sha256']


@pytest.mark.parametrize('fault', ['old_PAR','old_total_heat','old_non_PAR','missing_non_solar','solar_type',
    'caller_LAI','actual_NIR_tau','spectrum','solar_origin','weather_origin','weather_type','solar_unit',
    'empty_canopy','cohort_shape','profile','singular','numeric','scenario_extra'])
def test_double_count_mixed_closed_input_domain_and_numeric_holds(profiles,fault):
    c,p = inputs(),dict(profiles);f = c['scenario']['forcing'];sun = c['solar']['values']
    if fault == 'old_PAR':f['par_above_canopy'] = {'value':100,'unit':model.par.radiation.PHOTONS}
    if fault == 'old_total_heat':f['canopy_external_heat'] = {'value':100,'unit':model.nir.HEAT}
    if fault == 'old_non_PAR':f['canopy_non_par_heat'] = {'value':100,'unit':model.nir.HEAT}
    if fault == 'missing_non_solar':del f['canopy_non_solar_heat']
    if fault == 'solar_type':c['solar'] = []
    if fault == 'caller_LAI':sun['leaf_area_index'] = {'value':2,'unit':'m2_leaf/m2_floor'}
    if fault == 'actual_NIR_tau':sun['cover_nir_transmittance'] = {'value':.7,'unit':'1'}
    if fault == 'spectrum':sun['solar_nir_fraction']['value'] = .4
    if fault == 'solar_origin':c['solar']['origin'] = 'reference_calculation'
    if fault == 'weather_origin':c['ventilation']['origin'] = 'reference_calculation'
    if fault == 'weather_type':c['ventilation'] = None
    if fault == 'solar_unit':sun['outdoor_global_radiation']['unit'] = 'W/m2_leaf'
    if fault == 'empty_canopy':c['scenario']['plant_state']['leaf']['value'] = 0
    if fault == 'cohort_shape':c['scenario']['cohort_state']['fruit_number'].pop()
    if fault == 'profile':p['growth_profile'] = None
    if fault == 'singular':
        for key in ['cover_nir_reflectance','floor_nir_reflectance','canopy_nir_reflectance']:sun[key]['value'] = 1
    if fault == 'numeric':sun['nir_extinction_coefficient']['value'] = 1e6
    if fault == 'scenario_extra':c['scenario']['events'] = []
    with pytest.raises(model.SolarJointHold):model.evaluate_rhs(**c,**p)
