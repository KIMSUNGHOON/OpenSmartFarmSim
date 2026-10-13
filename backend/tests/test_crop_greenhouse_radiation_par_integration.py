"""Independent trajectories and actual shared solar/air/crop trial composition."""
from copy import deepcopy
from decimal import Decimal, localcontext
from hashlib import sha256
import json
from math import fsum
from pathlib import Path
import runpy

import pytest

from app import crop_greenhouse_radiation_par_integration as model
from app.crop_growth_rates import ReferenceParameters as Growth
from app.crop_fruit_cohorts import ReferenceFruitCohortParameters as Cohort
from app.crop_fruit_transport import ReferenceFruitTransportParameters as Transport
from app.crop_canopy_exchange import ReferenceParameters as Exchange

ROOT = Path(__file__).resolve().parents[2]
DOCUMENT = json.loads((ROOT/'fixtures/crop-greenhouse-radiation-par-integration-reference-cases-v1.json').read_bytes())
CASES = DOCUMENT['cases']


@pytest.fixture(scope='module')
def profiles():
    return {key: kind((ROOT/'fixtures'/name).read_bytes()) for key, kind, name in (
        ('growth_profile', Growth, 'crop-growth-reference-parameters-v1.json'),
        ('cohort_profile', Cohort, 'crop-fruit-cohort-reference-parameters-v1.json'),
        ('transport_profile', Transport, 'crop-fruit-transport-reference-parameters-v1.json'),
        ('exchange_profile', Exchange, 'crop-canopy-exchange-reference-parameters-v1.json'))}


def run(profiles, case=None, dt=2, count=16):
    c = CASES[0] if case is None else case
    return model.integrate(scenario=c['scenario'], solar=c['solar'], ventilation=c['ventilation'],
        step_seconds=dt, step_count=count, **profiles)


@pytest.fixture(scope='module')
def results(profiles):
    return [run(profiles, c) for c in CASES]


def state(s):
    return [q['value'] for q in [*[s['plant_state'][k] for k in model.core.PLANT],
        *s['cohort_state']['fruit_carbohydrate'], *s['cohort_state']['fruit_number'],
        *[s['climate_state'][k] for k in model.core.CLIMATE]]]


@pytest.mark.parametrize('index', range(6), ids=[c['case_id'] for c in CASES])
def test_independent876_scalars_and13_balance_budgets(results, index):
    r, expected = results[index], CASES[index]['expected_decimal']
    assert len(state(r['samples'][-1])) == len(expected['state']) == 108
    for found, wanted in zip(state(r['samples'][-1]), expected['state'], strict=True):
        assert found == pytest.approx(float(wanted), rel=5e-12, abs=5e-14)
    assert len(r['integrated_transfers']) == len(expected['integrated_transfers']) == 35
    for key, text in expected['integrated_transfers'].items():
        assert r['integrated_transfers'][key]['value'] == pytest.approx(float(text), rel=5e-12, abs=5e-14), key
    for key, text in expected['derived'].items():
        assert r['samples'][-1]['derived'][key]['value'] == pytest.approx(float(text), rel=5e-12, abs=5e-14)
    assert r['samples'][-1]['derived']['canopy_temperature']['value'] == pytest.approx(
        float(expected['derived']['canopy_temperature']), rel=0, abs=2e-10)
    assert len(r['balance_residuals']) == 13
    for key, q in r['balance_residuals'].items():
        assert abs(q['value']) <= r['balance_budgets'][key]['value']
        limit = 1e-12 if key == 'number' else 1e-13 if q['unit'] == model.core.WATER else (
            1e-8 if key == 'crop_capacity' else 1e-7)
        assert abs(q['value']) <= limit


def metrics(r):
    y = state(r['samples'][-1]); t = r['integrated_transfers']
    return [r['samples'][-1]['derived']['canopy_temperature']['value'], y[106], y[107], y[3], y[4],
        y[0], fsum(y[5:55]), *[t[k]['value'] for k in ('canopy_to_air_sensible', 'canopy_to_vapor_latent',
            'canopy_to_air_vapor', 'ventilation_sensible_heat', 'ventilation_vapor')]]


def fine_metrics(r):
    y = list(map(Decimal, r['state'])); t = r['integrated_transfers']
    return [Decimal(r['derived']['canopy_temperature']), y[106], y[107], y[3], y[4], y[0], sum(y[5:55]),
        *[Decimal(t[k]) for k in ('canopy_to_air_sensible', 'canopy_to_vapor_latent',
            'canopy_to_air_vapor', 'ventilation_sensible_heat', 'ventilation_vapor')]]


@pytest.mark.parametrize('index', range(3), ids=[c['case_id'] for c in CASES[:3]])
def test_all72_independent_step_halving_ratios_above8(profiles, results, index):
    c = CASES[index]
    with localcontext() as context:
        context.prec = 80
        target = fine_metrics(c['fine_32s_dt0_25_decimal'])
        series = [run(profiles, c, dt=8, count=4), run(profiles, c, dt=4, count=8), results[index]]
        errors = [[abs(Decimal(str(x))-y) for x, y in zip(metrics(r), target, strict=True)] for r in series]
        for column in range(12):
            a, b, d = (row[column] for row in errors)
            assert a > b > d > 0, (index, column, a, b, d)
            assert a/b > 8 and b/d > 8, (index, column, a/b, b/d)


def test_independent_generator_pins_and_exact_same_step_replay():
    path = ROOT/'research/crop-greenhouse-radiation-par-integration-reference.py'
    assert sha256(path.read_bytes()).hexdigest() == DOCUMENT['generator_sha256']
    for name, digest in DOCUMENT['input_sha256'].items():
        assert sha256((ROOT/name).read_bytes()).hexdigest() == digest
    oracle = runpy.run_path(str(path)); c = CASES[0]
    with localcontext() as ctx:
        ctx.prec = 80
        expected = oracle['trajectory'](c['scenario'], c['solar'], c['ventilation'], Decimal(2), 16,
            oracle['environment']())
    assert expected == c['expected_decimal']


def test_actual_shared_trial_current_LAI_temperature_air_and_once_only_composition(profiles, monkeypatch):
    stages, radiation, outdoor = [], [], []
    for module, name, target in ((model.par, 'evaluate_rhs', stages),
            (model.par.radiation, 'calculate_par', radiation),
            (model.vent_joint.vent, 'calculate_ventilation', outdoor)):
        original = getattr(module, name)
        def record(*, _original=original, _target=target, **kwargs):
            r = _original(**kwargs); _target.append(r); return r
        monkeypatch.setattr(module, name, record)
    c = deepcopy(CASES[0]); before = deepcopy(c); r = run(profiles, c)
    assert c == before
    assert len(stages) == len(radiation) == r['numerical']['PAR_evaluations'] == 66
    assert len(stages) == r['numerical']['total_joint_rhs_evaluations']
    assert len(outdoor) == r['numerical']['ventilation_evaluations'] == r['numerical']['coupled_rhs_evaluations'] == 65
    assert r['numerical']['input_validation_PAR_and_RHS_evaluations'] == 1
    for stage, optical, vent in zip(stages[1:], radiation[1:], outdoor, strict=True):
        joint = stage['joint_rhs']
        assert optical['scenario']['values']['leaf_area_index'] == joint['derived']['leaf_area_index']
        assert joint['derived']['leaf_area_index']['value'] == profiles['growth_profile'].values['sla']*(
            joint['scenario']['plant_state']['leaf']['value'])
        assert joint['scenario']['forcing']['par_above_canopy'] == optical['crop_forcing']['par_above_canopy']
        assert joint['scenario']['forcing']['canopy_external_heat'] == stage['heat_composition']['canopy_external_heat']
        assert stage['heat_composition']['canopy_external_heat']['value'] == fsum((
            c['scenario']['forcing']['canopy_non_par_heat']['value'], optical['heat_components']['canopy_absorbed_par']['value']))
        assert vent['scenario']['state'] == {k: joint['scenario']['climate_state'][k] for k in model.vent_joint.vent.STATE_UNITS}
        for key, q in vent['forcing_contribution'].items():
            assert joint['scenario']['forcing'][key]['value'] == fsum((c['scenario']['forcing'][key]['value'], q['value']))
    for index, sample in enumerate(r['samples']):
        assert sample['derived'] == stages[1+4*index]['joint_rhs']['derived']
        assert sample['solar_par']['input_sha256'] == radiation[1+4*index]['input_sha256']
    assert r['samples'][0]['solar_par']['heat_composition'] != r['samples'][-1]['solar_par']['heat_composition']
    assert r['scenario']['forcing'] == before['scenario']['forcing']


def legacy_scenario(r):
    s = deepcopy(r['scenario']); f = s['forcing']; sample = r['samples'][0]['solar_par']
    f.pop('canopy_non_par_heat'); f['canopy_external_heat'] = sample['heat_composition']['canopy_external_heat']
    f['par_above_canopy'] = sample['crop_forcing']['par_above_canopy']
    return s


def test_dark_exact_previous_ventilation_solution_new_identity(profiles, results):
    c, r = CASES[2], results[2]
    old = model.vent_joint.integrate(scenario=legacy_scenario(r), ventilation=c['ventilation'],
        step_seconds=2, step_count=16, **profiles)
    assert [{k: v for k, v in s.items() if k != 'solar_par'} for s in r['samples']] == old['samples']
    for key, q in old['integrated_transfers'].items():
        assert r['integrated_transfers'][key] == q
    assert all(r['integrated_transfers']['solar_par_'+k]['value'] == 0 for k in model.PAR_FIELDS)
    assert r['model_version'] != old['model_version'] and r['calculation_sha256'] != old['calculation_sha256']


def test_freezing_initial_PAR_fails_to_reproduce_current_leaf_trajectory(profiles, results):
    r = results[0]
    frozen = model.vent_joint.integrate(scenario=legacy_scenario(r), ventilation=CASES[0]['ventilation'],
        step_seconds=2, step_count=16, **profiles)
    assert abs(state(frozen['samples'][-1])[105]-state(r['samples'][-1])[105]) > 1e-5


def test_manual_event_free_split_state_and_integrated_partition_ledgers(profiles, results):
    first = run(profiles, count=7); c = deepcopy(CASES[0])
    for key in ('plant_state', 'cohort_state', 'climate_state'):c['scenario'][key] = first['samples'][-1][key]
    rest = run(profiles, c, count=9)
    assert state(rest['samples'][-1]) == state(results[0]['samples'][-1])
    for key, q in results[0]['integrated_transfers'].items():
        found = fsum((first['integrated_transfers'][key]['value'], rest['integrated_transfers'][key]['value']))
        assert found == pytest.approx(q['value'], rel=5e-12, abs=5e-14), key


def test_normalized_input_identity_replay_scope_and_components(profiles, results):
    r = results[0]; c = deepcopy(CASES[0]); before = deepcopy(c)
    assert run(profiles, c) == r and c == before
    assert r['calculation_sha256'] == model.core._hash({k:r[k] for k in ('model_version', 'code_sha256',
        'input_sha256', 'component_code_sha256', 'profile_sha256', 'policy_sha256', 'numerical')})
    c['solar']['values']['outdoor_global_radiation']['value'] += 1
    assert run(profiles, c)['input_sha256'] != r['input_sha256']
    assert run(profiles, dt=4, count=8)['calculation_sha256'] != r['calculation_sha256']
    for name, digest in r['component_code_sha256'].items():
        assert sha256((ROOT/'backend/app'/f'{name}.py').read_bytes()).hexdigest() == digest
    assert sha256(Path(model.__file__).read_bytes()).hexdigest() == r['code_sha256']
    assert r['G0_G4'] == 'not_assessed' and r['scope'] == 'software_research_only'
    assert r['claim_scope'] == 'synthetic_joint_solar_PAR_ventilation_only'


@pytest.mark.parametrize('dt,count', [(True,1), ('2',1), (None,1), (float('nan'),1),
    (float('inf'),1), (0,1), (-1,1), (10**400,1), (1,True), (1,0), (1,4097), (1,1.0), (601,1)])
def test_bounded_numerics_hold(profiles, dt, count):
    with pytest.raises(model.RadiationPARIntegrationHold, match='BUDGET_HOLD'):
        run(profiles, dt=dt, count=count)


@pytest.mark.parametrize('fault', ['legacy_PAR', 'legacy_heat', 'missing_non_PAR', 'caller_LAI',
    'solar_origin', 'weather_origin', 'weather_extra', 'weather_type', 'weather_unit', 'weather_negative',
    'scenario_extra', 'leaf_unit', 'empty_canopy', 'cohort_shape', 'profile', 'optics', 'photon_overflow'])
def test_closed_input_domain_and_initial_holds(profiles, fault):
    c, p = deepcopy(CASES[0]), dict(profiles)
    if fault == 'legacy_PAR': c['scenario']['forcing']['par_above_canopy'] = {'value':100, 'unit':model.par.radiation.PHOTONS}
    if fault == 'legacy_heat': c['scenario']['forcing']['canopy_external_heat'] = {'value':100, 'unit':model.par.radiation.HEAT}
    if fault == 'missing_non_PAR': del c['scenario']['forcing']['canopy_non_par_heat']
    if fault == 'caller_LAI': c['solar']['values']['leaf_area_index'] = {'value':2, 'unit':'m2_leaf/m2_floor'}
    if fault == 'solar_origin': c['solar']['origin'] = 'reference_calculation'
    if fault == 'weather_origin': c['ventilation']['origin'] = 'reference_calculation'
    if fault == 'weather_extra': c['ventilation']['state'] = {}
    if fault == 'weather_type': c['ventilation'] = None
    if fault == 'weather_unit': c['ventilation']['forcing']['outdoor_vapor_pressure']['unit'] = 'kPa'
    if fault == 'weather_negative': c['ventilation']['forcing']['volume_exchange_per_floor_area']['value'] = -1
    if fault == 'scenario_extra': c['scenario']['events'] = []
    if fault == 'leaf_unit': c['scenario']['plant_state']['leaf']['unit'] = 'kg'
    if fault == 'empty_canopy': c['scenario']['plant_state']['leaf']['value'] = 0
    if fault == 'cohort_shape': c['scenario']['cohort_state']['fruit_number'].pop()
    if fault == 'profile': p['exchange_profile'] = None
    if fault == 'optics': c['solar']['values']['cover_par_transmittance']['value'] = 2
    if fault == 'photon_overflow': c['solar']['values']['solar_par_photon_conversion']['value'] = 1e308
    with pytest.raises(model.RadiationPARIntegrationHold) as error:run(p, c)
    assert error.value.step_index == 0 and error.value.failed_stage == 'initial'
    assert error.value.last_confirmed_sample is None


@pytest.mark.parametrize('phase,call', [('k2',3), ('k3',4), ('k4',5), ('endpoint',6), ('k3',8)])
def test_failed_PAR_trial_keeps_last_confirmed_sample(profiles, monkeypatch, phase, call):
    expected = run(profiles, count=1)['samples'][-1 if call > 6 else 0]
    original = model.par.radiation.calculate_par; calls = 0
    def fail(**kwargs):
        nonlocal calls
        calls += 1
        if calls == call: raise model.par.radiation.RadiationPARHold('NUMERIC_HOLD: synthetic trial unavailable')
        return original(**kwargs)
    monkeypatch.setattr(model.par.radiation, 'calculate_par', fail)
    with pytest.raises(model.RadiationPARIntegrationHold, match='NUMERIC_HOLD') as error:run(profiles)
    assert error.value.failed_stage == phase
    assert error.value.last_confirmed_sample == expected
    assert error.value.last_confirmed_elapsed_seconds == expected['elapsed_seconds']


def test_unconfirmed_endpoint_balance_failure_preserves_prefix(profiles, monkeypatch):
    expected = run(profiles, count=1)['samples'][0]; original = model._partitions
    def fail(totals, index):
        if index == 1: raise model.RadiationPARIntegrationHold('BALANCE_HOLD: synthetic partition unavailable')
        return original(totals, index)
    monkeypatch.setattr(model, '_partitions', fail)
    with pytest.raises(model.RadiationPARIntegrationHold, match='BALANCE_HOLD') as error:run(profiles)
    assert error.value.failed_stage == 'endpoint_balance' and error.value.last_confirmed_sample == expected
