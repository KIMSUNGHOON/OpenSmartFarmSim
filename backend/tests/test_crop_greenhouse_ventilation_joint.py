"""Whole independent trajectories, convergence and real current-stage composition."""
from copy import deepcopy
from decimal import Decimal, localcontext
from hashlib import sha256
import importlib.util
import json
from math import fsum
from pathlib import Path

import pytest

from app import crop_greenhouse_ventilation_joint as model
from app.crop_growth_rates import ReferenceParameters as Growth
from app.crop_fruit_cohorts import ReferenceFruitCohortParameters as Cohort
from app.crop_fruit_transport import ReferenceFruitTransportParameters as Transport
from app.crop_canopy_exchange import ReferenceParameters as Exchange

ROOT = Path(__file__).resolve().parents[2]
FIXTURE = ROOT/'fixtures/crop-greenhouse-ventilation-joint-reference-cases-v1.json'
DOCUMENT = json.loads(FIXTURE.read_bytes())
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
    return model.integrate(scenario=c['scenario'], ventilation=c['ventilation'],
        step_seconds=dt, step_count=count, **profiles)


@pytest.fixture(scope='module')
def results(profiles):
    return [run(profiles, c) for c in CASES]


def state(sample):
    return [q['value'] for q in [*[sample['plant_state'][k] for k in model.core.PLANT],
        *sample['cohort_state']['fruit_carbohydrate'], *sample['cohort_state']['fruit_number'],
        *[sample['climate_state'][k] for k in model.core.CLIMATE]]]


@pytest.mark.parametrize('index', range(6), ids=[c['case_id'] for c in CASES])
def test_independent_full_state_ledgers_derived_and_all_balance_budgets(results, index):
    r, expected = results[index], CASES[index]['expected_decimal']
    actual = state(r['samples'][-1])
    assert len(actual) == len(expected['state']) == 108
    for found, wanted in zip(actual, expected['state'], strict=True):
        assert found == pytest.approx(float(wanted), rel=5e-12, abs=5e-14)
    assert set(r['integrated_transfers']) == set(expected['integrated_transfers'])
    assert len(r['integrated_transfers']) == 25
    for key, text in expected['integrated_transfers'].items():
        assert r['integrated_transfers'][key]['value'] == pytest.approx(float(text), rel=5e-12, abs=5e-14), key
    for key, text in expected['derived'].items():
        assert r['samples'][-1]['derived'][key]['value'] == pytest.approx(float(text), rel=5e-12, abs=5e-14)
    assert r['samples'][-1]['derived']['canopy_temperature']['value'] == pytest.approx(
        float(expected['derived']['canopy_temperature']), rel=0, abs=2e-10)
    assert len(r['balance_residuals']) == 10
    for key, q in r['balance_residuals'].items():
        assert abs(q['value']) <= r['balance_budgets'][key]['value']
        limit = 1e-12 if key == 'number' else 1e-13 if q['unit'] == model.core.WATER else (
            1e-8 if key == 'crop_capacity' else 1e-7)
        assert abs(q['value']) <= limit


def metrics(r):
    y = state(r['samples'][-1])
    t = r['integrated_transfers']
    return [r['samples'][-1]['derived']['canopy_temperature']['value'], y[106], y[107], y[3], y[4],
        y[0], fsum(y[5:55]), *[t[k]['value'] for k in ('canopy_to_air_sensible', 'canopy_to_vapor_latent',
            'canopy_to_air_vapor', 'ventilation_sensible_heat', 'ventilation_vapor')]]


def fine_metrics(r):
    y = list(map(Decimal, r['state']))
    t = r['integrated_transfers']
    return [Decimal(r['derived']['canopy_temperature']), y[106], y[107], y[3], y[4], y[0], sum(y[5:55]),
        *[Decimal(t[k]) for k in ('canopy_to_air_sensible', 'canopy_to_vapor_latent',
            'canopy_to_air_vapor', 'ventilation_sensible_heat', 'ventilation_vapor')]]


@pytest.mark.parametrize('index', range(3), ids=[c['case_id'] for c in CASES[:3]])
def test_independent_fine_reference_and_all72_halving_ratios_above8(profiles, results, index):
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


def test_independent_generator_replays_exact_fixture_and_source_pins():
    path = ROOT/'research/crop-greenhouse-ventilation-joint-reference.py'
    spec = importlib.util.spec_from_file_location('ventilation_joint_reference', path)
    oracle = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(oracle)
    assert DOCUMENT['generator_sha256'] == sha256(path.read_bytes()).hexdigest()
    for name, digest in DOCUMENT['input_sha256'].items():
        assert sha256((ROOT/name).read_bytes()).hexdigest() == digest
    document = oracle.references()
    assert document == DOCUMENT
    assert (json.dumps(document, indent=2, sort_keys=True, allow_nan=False)+'\n').encode() == FIXTURE.read_bytes()


def test_actual_stage_pairing_evolving_flux_and_once_only_composition(profiles, monkeypatch):
    calls, boundaries = [], []
    original, boundary = model.joint.evaluate_rhs, model.vent.calculate_ventilation
    def capture_joint(**kwargs):
        value = original(**kwargs); calls.append(value); return value
    def capture_boundary(**kwargs):
        value = boundary(**kwargs); boundaries.append(value); return value
    monkeypatch.setattr(model.joint, 'evaluate_rhs', capture_joint)
    monkeypatch.setattr(model.vent, 'calculate_ventilation', capture_boundary)
    case = deepcopy(CASES[0]); before = deepcopy(case)
    r = run(profiles, case)
    assert case == before
    assert len(calls) == r['numerical']['total_joint_rhs_evaluations'] == 66
    assert len(boundaries) == r['numerical']['ventilation_evaluations'] == r['numerical']['coupled_rhs_evaluations'] == 65
    assert r['numerical']['input_validation_rhs_evaluations'] == 1
    for result, flux in zip(calls[1:], boundaries, strict=True):
        assert flux['scenario']['state'] == {k: result['scenario']['climate_state'][k] for k in model.vent.STATE_UNITS}
        assert flux['scenario']['parameters'] == {k: result['scenario']['parameters'][k] for k in model.vent.PARAMETER_UNITS}
        for key, q in flux['forcing_contribution'].items():
            assert result['scenario']['forcing'][key]['value'] == pytest.approx(
                case['scenario']['forcing'][key]['value']+q['value'], rel=2e-14, abs=0)
    for index, sample in enumerate(r['samples']):
        assert sample['derived'] == calls[1+index*4]['derived']
        assert sample['ventilation']['input_sha256'] == boundaries[index*4]['input_sha256']
    assert r['samples'][0]['ventilation']['forcing_contribution'] != r['samples'][-1]['ventilation']['forcing_contribution']
    assert r['scenario']['forcing'] == before['scenario']['forcing']


def test_zero_ventilation_exact_physical_equivalence_with_new_identity(profiles, results):
    c, r = CASES[3], results[3]
    previous = model.core.integrate(scenario=c['scenario'], step_seconds=2, step_count=16, **profiles)
    assert [{k: v for k, v in s.items() if k != 'ventilation'} for s in r['samples']] == previous['samples']
    for key, q in previous['integrated_transfers'].items():
        assert r['integrated_transfers'][key] == q
    assert all(r['integrated_transfers'][k]['value'] == 0 for k in tuple(model.FLUX_UNITS)[22:])
    assert r['model_version'] != previous['model_version']
    assert r['calculation_sha256'] != previous['calculation_sha256']


def test_freezing_initial_flux_gives_different_trajectory(profiles, results):
    c = deepcopy(CASES[0])
    for key, q in results[0]['samples'][0]['ventilation']['forcing_contribution'].items():
        c['scenario']['forcing'][key]['value'] += q['value']
    frozen = model.core.integrate(scenario=c['scenario'], step_seconds=2, step_count=16, **profiles)
    assert abs(state(frozen['samples'][-1])[106]-state(results[0]['samples'][-1])[106]) > 1e-4
    assert abs(state(frozen['samples'][-1])[107]-state(results[0]['samples'][-1])[107]) > 1e-8


def test_reference_temperature_changes_preserve_physical_solution(results):
    a = results[0]
    for b in results[4:]:
        for key in ('canopy_temperature', 'leaf_area_index', 'canopy_capacity'):
            assert b['samples'][-1]['derived'][key]['value'] == pytest.approx(
                a['samples'][-1]['derived'][key]['value'], rel=5e-12, abs=5e-14)
        for index, (x, y) in enumerate(zip(state(a['samples'][-1]), state(b['samples'][-1]), strict=True)):
            if index != 105:
                assert x == pytest.approx(y, rel=5e-12, abs=5e-14)
    assert CASES[4]['scenario']['climate_state']['canopy_sensible_energy']['value'] < 0
    assert CASES[5]['scenario']['climate_state']['canopy_sensible_energy']['value'] == 0


def test_returned_raw_stocks_combined_and_ventilation_ledgers_balance(results, profiles):
    latent = profiles['exchange_profile'].values['latent_heat']
    for r in results:
        a, b = state(r['samples'][0]), state(r['samples'][-1])
        t = {k: q['value'] for k, q in r['integrated_transfers'].items()}
        ca = r['samples'][0]['derived']['air_capacity']['value']
        energy = fsum((b[105]-a[105], ca*(b[106]-a[106]), latent*(b[107]-a[107]),
            -t['canopy_external_heat'], -t['air_external_sensible_heat'], -latent*t['air_external_vapor'],
            -t['incoming_capacity_heat'], t['maintenance_capacity_heat'], t['removal_capacity_heat']))
        assert abs(energy) <= 1e-7
        carbon = fsum((*b[:3], *b[5:55]))-fsum((*a[:3], *a[5:55]))
        assert abs(fsum((carbon, -t['photosynthesis'], *[t[k] for k in tuple(model.FLUX_UNITS)[1:8]]))) <= 1e-7
        assert abs(fsum((b[107]-a[107], -t['canopy_to_air_vapor'], -t['air_external_vapor']))) <= 1e-13
        assert abs(fsum((fsum(b[55:105])-fsum(a[55:105]), -t['fruit_number_inflow'], t['terminal_fruit_number']))) <= 1e-12
        for key, base_key, total, unit in (
                ('ventilation_sensible_heat', 'air_external_sensible_heat', t['air_external_sensible_heat'], model.core.ENERGY),
                ('ventilation_vapor', 'air_external_vapor', t['air_external_vapor'], model.core.WATER)):
            residual = fsum((total, -r['scenario']['forcing'][base_key]['value']*32, -t[key]))
            assert abs(residual) <= (1e-13 if unit == model.core.WATER else 1e-7)
        assert abs(fsum((t['ventilation_latent_energy'], -latent*t['ventilation_vapor']))) <= 1e-7


@pytest.mark.parametrize('dt,count', [(True,1), ('2',1), (None,1), (float('nan'),1),
    (float('inf'),1), (0,1), (-1,1), (10**400,1), (1,True), (1,0), (1,4097), (1,1.0), (601,1)])
def test_explicit_bounded_numerics_hold(profiles, dt, count):
    with pytest.raises(model.JointVentilationHold, match='BUDGET_HOLD'):
        run(profiles, dt=dt, count=count)


@pytest.mark.parametrize('fault', ['weather_extra', 'weather_missing', 'weather_type', 'weather_unit',
    'weather_negative', 'scenario_extra', 'scenario_unit', 'cohort_shape', 'empty_canopy', 'profile'])
def test_closed_inherited_domains_and_current_input_initial_holds(profiles, fault):
    c, p = deepcopy(CASES[0]), dict(profiles)
    if fault == 'weather_extra': c['ventilation']['state'] = {}
    if fault == 'weather_missing': del c['ventilation']['forcing']['outdoor_vapor_pressure']
    if fault == 'weather_type': c['ventilation'] = None
    if fault == 'weather_unit': c['ventilation']['forcing']['volume_exchange_per_floor_area']['unit'] = '1/h'
    if fault == 'weather_negative': c['ventilation']['forcing']['volume_exchange_per_floor_area']['value'] = -1
    if fault == 'scenario_extra': c['scenario']['events'] = []
    if fault == 'scenario_unit': c['scenario']['climate_state']['air_temperature']['unit'] = 'K'
    if fault == 'cohort_shape': c['scenario']['cohort_state']['fruit_number'].pop()
    if fault == 'empty_canopy': c['scenario']['plant_state']['leaf']['value'] = 0
    if fault == 'profile': p['exchange_profile'] = None
    with pytest.raises(model.JointVentilationHold) as error:
        run(p, c)
    assert error.value.step_index == 0 and error.value.failed_stage == 'initial'
    assert error.value.last_confirmed_sample is None


@pytest.mark.parametrize('phase,call', [('k2',2), ('k3',3), ('k4',4), ('endpoint',5), ('k3',7)])
def test_unconfirmed_boundary_stage_failure_keeps_last_complete_sample(profiles, monkeypatch, phase, call):
    expected = run(profiles, count=1)['samples'][-1 if call > 5 else 0]
    original = model.vent.calculate_ventilation
    calls = 0
    def fail(**kwargs):
        nonlocal calls
        calls += 1
        if calls == call:
            raise model.vent.VentilationHold('NUMERIC_HOLD: synthetic boundary trial unavailable')
        return original(**kwargs)
    monkeypatch.setattr(model.vent, 'calculate_ventilation', fail)
    with pytest.raises(model.JointVentilationHold, match='NUMERIC_HOLD') as error:
        run(profiles)
    assert error.value.failed_stage == phase
    assert error.value.step_index == (2 if call > 5 else 1)
    assert error.value.last_confirmed_sample == expected


@pytest.mark.parametrize('column', [16,22,23,24])
def test_corrupt_combined_or_ventilation_ledger_is_not_accepted(profiles, monkeypatch, column):
    original = model._evaluate
    def corrupt(*args):
        rates, flux, result, boundary = original(*args)
        values = list(flux); values[column] += 1
        return rates, tuple(values), result, boundary
    monkeypatch.setattr(model, '_evaluate', corrupt)
    with pytest.raises(model.JointVentilationHold, match='BALANCE_HOLD') as error:
        run(profiles)
    assert error.value.failed_stage == 'endpoint_balance'
    assert error.value.last_confirmed_elapsed_seconds == 0


def test_actual_temperature_trial_is_a_hold_and_keeps_initial_sample(profiles):
    c = deepcopy(CASES[0]); c['scenario']['forcing']['canopy_external_heat']['value'] = 1e7
    with pytest.raises(model.JointVentilationHold, match='TEMPERATURE_HOLD') as error:
        run(profiles, c)
    assert error.value.failed_stage == 'k2' and error.value.last_confirmed_elapsed_seconds == 0


@pytest.mark.parametrize('dt', [5e-324, 1e-200])
def test_lost_or_underflowed_increment_holds(profiles, dt):
    with pytest.raises(model.JointVentilationHold, match='NUMERIC_HOLD'):
        run(profiles, dt=dt, count=1)


def test_new_identity_binds_weather_numerics_components_profiles_and_retains_claim_holds(profiles, results):
    a = results[0]
    b = run(profiles, dt=1, count=32)
    assert a['input_sha256'] == b['input_sha256'] and a['calculation_sha256'] != b['calculation_sha256']
    c = deepcopy(CASES[0]); c['ventilation']['forcing']['outdoor_air_temperature']['value'] += .1
    changed = run(profiles, c)
    assert changed['input_sha256'] != a['input_sha256'] and changed['calculation_sha256'] != a['calculation_sha256']
    assert a['code_sha256'] == sha256((ROOT/'backend/app/crop_greenhouse_ventilation_joint.py').read_bytes()).hexdigest()
    for key, digest in a['component_code_sha256'].items():
        assert sha256((ROOT/'backend/app'/str(key+'.py')).read_bytes()).hexdigest() == digest
    assert a['model_version'] == model.VERSION
    assert a['ledger_schema_version'] == 'joint-ventilation-ledgers-v1'
    assert a['state_schema_version'] == model.joint.STATE_SCHEMA
    assert a['claim_scope'] == 'synthetic_joint_crop_climate_prescribed_ventilation_only'
    assert a['scope'] == 'software_research_only' and a['G0_G4'] == 'not_assessed'
