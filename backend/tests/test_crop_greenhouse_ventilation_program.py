"""Independent event trajectories, real atomic ordering and global hold prefixes."""
from copy import deepcopy
from decimal import Decimal, localcontext
from hashlib import sha256
import importlib.util
import json
from math import fsum
from pathlib import Path

import pytest

from app import crop_greenhouse_ventilation_program as model
from app.crop_growth_rates import ReferenceParameters as Growth
from app.crop_fruit_cohorts import ReferenceFruitCohortParameters as Cohort
from app.crop_fruit_transport import ReferenceFruitTransportParameters as Transport
from app.crop_canopy_exchange import ReferenceParameters as Exchange
from test_crop_climate_joint_boundary import independent_balances, state, state_equal, metrics as stock_metrics

ROOT = Path(__file__).resolve().parents[2]
FIXTURE = ROOT/'fixtures/crop-greenhouse-ventilation-program-reference-cases-v1.json'
DOCUMENT = json.loads(FIXTURE.read_bytes())
SOURCE = {c['case_id']: c for c in json.loads((ROOT/DOCUMENT['source_cases']).read_bytes())['cases']}
CASES = [{**deepcopy(SOURCE[c['source_case_id']]), **c} for c in DOCUMENT['cases']]
BY_ID = {c['case_id']: c for c in CASES}


@pytest.fixture(scope='module')
def profiles():
    return {key: kind((ROOT/'fixtures'/name).read_bytes()) for key, kind, name in (
        ('growth_profile', Growth, 'crop-growth-reference-parameters-v1.json'),
        ('cohort_profile', Cohort, 'crop-fruit-cohort-reference-parameters-v1.json'),
        ('transport_profile', Transport, 'crop-fruit-transport-reference-parameters-v1.json'),
        ('exchange_profile', Exchange, 'crop-canopy-exchange-reference-parameters-v1.json'))}


def run(profiles, case=None, dt=2, **changes):
    c = BY_ID['warm-mid'] if case is None else case
    scale = lambda n: int(n*c['step_seconds']/dt)
    kwargs = {'scenario': c['scenario'], 'ventilation': c['ventilation'],
        'events': [{'step_index': scale(e['step_index']), 'event': e['event']} for e in c['events']],
        'output_steps': [scale(i) for i in c['output_steps']], 'step_seconds': dt,
        'step_count': scale(c['step_count']), **profiles}
    kwargs.update(changes)
    return model.integrate_events(**kwargs)


@pytest.fixture(scope='module')
def results(profiles):
    return {c['case_id']: run(profiles, c) for c in CASES}


@pytest.mark.parametrize('case', CASES, ids=lambda c: c['case_id'])
def test_all_independent_selected_states_ledgers_events_and_raw_balances(profiles, results, case):
    r = results[case['case_id']]
    for actual, expected in zip(r['samples'], case['expected_decimal']['samples'], strict=True):
        assert actual['step_index'] == expected['step_index']
        assert actual['elapsed_seconds'] == float(expected['elapsed_seconds'])
        assert actual['event_count'] == expected['event_count']
        state_equal(state(actual), expected['state'])
        for block in ('integrated_transfers', 'event_totals', 'derived'):
            for key, wanted in expected[block].items():
                assert actual[block][key]['value'] == pytest.approx(float(wanted), rel=5e-12, abs=5e-14)
        assert actual['derived']['canopy_temperature']['value'] == pytest.approx(
            float(expected['derived']['canopy_temperature']), rel=0, abs=2e-10)
        assert len(actual['balance_residuals']) == 10
        for key, q in actual['balance_residuals'].items():
            assert abs(q['value']) <= actual['balance_budgets'][key]['value']
        for key, value in independent_balances(profiles, case, actual).items():
            assert abs(value) <= {'number': 1e-12, 'vapor_and_water_boundaries': 1e-13,
                'crop_capacity': 1e-8}.get(key, 1e-7)
        t = actual['integrated_transfers']; f = case['scenario']['forcing']; time = actual['elapsed_seconds']
        for total, vent, limit in [('air_external_sensible_heat', 'ventilation_sensible_heat', 1e-7),
                ('air_external_vapor', 'ventilation_vapor', 1e-13)]:
            assert abs(fsum((t[total]['value'], -f[total]['value']*time, -t[vent]['value']))) <= limit
        assert abs(fsum((t['ventilation_latent_energy']['value'],
            -profiles['exchange_profile'].values['latent_heat']*t['ventilation_vapor']['value']))) <= 1e-7
    for actual, expected in zip(r['events'], case['expected_decimal']['events'], strict=True):
        assert actual['step_index'] == expected['step_index']
        assert actual['elapsed_seconds'] == float(expected['elapsed_seconds'])
        applied = actual['management']
        state_equal(state(applied['before']['scenario']), expected['before'])
        state_equal(state(applied['after']['scenario']), expected['after'])
        for key, wanted in expected['removed_totals'].items():
            q = applied['removed'][key]
            found = fsum(v['value'] for v in q) if isinstance(q, list) else q['value']
            assert found == pytest.approx(float(wanted), rel=5e-12, abs=5e-14)


def metrics(sample):
    return {**stock_metrics(sample), **{k: Decimal(str(sample['integrated_transfers'][k]['value']
        if isinstance(sample['integrated_transfers'][k], dict) else sample['integrated_transfers'][k]))
        for k in ('ventilation_sensible_heat', 'ventilation_vapor')}}


@pytest.mark.parametrize('name', ['warm-mid', 'reverse-mid', 'dark-mid'])
def test72_independent_halving_ratios_with_fixed_event_time(profiles, results, name):
    c = BY_ID[name]
    with localcontext() as context:
        context.prec = 80
        target = metrics(c['fine_32s_dt0_25_decimal']['samples'][-1])
        rows = [run(profiles, c, dt=8), run(profiles, c, dt=4), results[name]]
        errors = [{k: abs(v-target[k]) for k, v in metrics(r['last_confirmed']).items()} for r in rows]
        for key in target:
            a, b, d = (e[key] for e in errors)
            assert a > b > d > 0 and a/b > 8 and b/d > 8, (name, key, a, b, d)
        assert all(r['events'][0]['elapsed_seconds'] == 16 for r in rows)


def test_oracle_replays_fixture_bytes_and_all_pins():
    path = ROOT/'research/crop-greenhouse-ventilation-program-reference.py'
    spec = importlib.util.spec_from_file_location('vent_program_reference', path)
    oracle = importlib.util.module_from_spec(spec); spec.loader.exec_module(oracle)
    assert DOCUMENT['generator_sha256'] == sha256(path.read_bytes()).hexdigest()
    for name, digest in DOCUMENT['input_sha256'].items():
        assert sha256((ROOT/name).read_bytes()).hexdigest() == digest
    expected = oracle.references()
    assert expected == DOCUMENT
    assert (json.dumps(expected, indent=2, sort_keys=True, allow_nan=False)+'\n').encode() == FIXTURE.read_bytes()


def test_actual_counts_atomic_order_post_event_forcing_and_input_preservation(profiles, monkeypatch):
    calls, vent_calls = [], []
    original, boundary = model.stage.joint.evaluate_rhs, model.stage.vent.calculate_ventilation
    def record(**kwargs):
        r = original(**kwargs); calls.append(r); return r
    def record_boundary(**kwargs):
        r = boundary(**kwargs); vent_calls.append(r); return r
    monkeypatch.setattr(model.stage.joint, 'evaluate_rhs', record)
    monkeypatch.setattr(model.stage.vent, 'calculate_ventilation', record_boundary)
    c = deepcopy(BY_ID['multiple']); before = deepcopy(c)
    r = run(profiles, c)
    n, e = c['step_count'], len(c['events'])
    assert len(calls) == r['numerical']['total_joint_rhs_evaluations'] == 2+6*n+3*e
    assert len(vent_calls) == r['numerical']['ventilation_evaluations'] == 1+5*n+e
    assert r['numerical']['input_validation_rhs_evaluations'] == 1+n
    assert r['numerical']['management_rhs_evaluations'] == 2*e
    assert c == before
    for journal, sample in zip(r['events'], r['samples'], strict=True):
        assert sample['phase'] == 'boundary-after-event'
        assert sample['plant_state'] == journal['management']['after']['scenario']['plant_state']
        assert sample['ventilation'] == journal['ventilation_after']
        assert journal['management']['before']['scenario']['forcing'] == c['scenario']['forcing']
        for key, q in journal['ventilation_after']['forcing_contribution'].items():
            assert journal['combined_forcing_after'][key]['value'] == pytest.approx(
                c['scenario']['forcing'][key]['value']+q['value'], rel=2e-14, abs=0)
    assert r['scenario']['forcing'] == c['scenario']['forcing']


def test_no_events_match_new_short_stage_and_output_selection_preserves_physics(profiles, results):
    c, r = BY_ID['no-events'], results['no-events']
    short = model.stage.integrate(scenario=c['scenario'], ventilation=c['ventilation'], step_seconds=2, step_count=16, **profiles)
    for key in ('plant_state', 'cohort_state', 'climate_state', 'derived', 'ventilation'):
        assert r['last_confirmed'][key] == short['samples'][-1][key]
    assert r['integrated_transfers'] == short['integrated_transfers']
    a = results['warm-mid']; b = run(profiles, output_steps=[0,16])
    assert a['last_confirmed'] == b['last_confirmed'] and a['events'] == b['events']
    assert a['calculation_sha256'] != b['calculation_sha256']


def test_zero_ventilation_full_management_matches_original_driver(profiles):
    c = deepcopy(BY_ID['multiple']); c['ventilation']['forcing']['volume_exchange_per_floor_area']['value'] = 0
    r = run(profiles, c)
    old = model.previous.integrate_events(**{k: c[k] for k in ('scenario','events','output_steps','step_seconds','step_count')}, **profiles)
    for key in ('plant_state','cohort_state','climate_state','derived','event_totals'):
        assert r['last_confirmed'][key] == old['last_confirmed'][key]
    for key, q in old['integrated_transfers'].items():
        assert r['integrated_transfers'][key] == q
    assert [e['management'] for e in r['events']] == [e['management'] for e in old['events']]
    assert r['model_version'] != old['model_version']


@pytest.mark.parametrize('fault', ['weather_extra','weather_missing','weather_unit','scenario_extra','profile',
    'event_duplicate','event_reverse','output_missing','output_duplicate','budget','too_many_events','too_many_outputs'])
def test_closed_bounds_and_domain_inputs_hold_without_confirmed_output(profiles, fault):
    c, changes = deepcopy(BY_ID['warm-mid']), {}
    if fault == 'weather_extra': c['ventilation']['state'] = {}
    if fault == 'weather_missing': del c['ventilation']['forcing']['outdoor_vapor_pressure']
    if fault == 'weather_unit': c['ventilation']['forcing']['outdoor_vapor_pressure']['unit'] = '%'
    if fault == 'scenario_extra': c['scenario']['unexpected'] = 0
    if fault == 'profile': changes['exchange_profile'] = None
    if fault == 'event_duplicate': changes['events'] = c['events']*2
    if fault == 'event_reverse': changes['events'] = list(reversed(BY_ID['multiple']['events']))
    if fault == 'output_missing': changes['output_steps'] = [8,16]
    if fault == 'output_duplicate': changes['output_steps'] = [0,0,16]
    if fault == 'budget': changes['step_seconds'] = True
    if fault == 'too_many_events': changes['events'] = c['events']*129
    if fault == 'too_many_outputs': changes['output_steps'] = list(range(513))
    with pytest.raises(model.VentilationProgramHold) as error:
        run(profiles, c, **changes)
    assert error.value.last_confirmed is None and error.value.samples == error.value.events == []


@pytest.mark.parametrize('where', [0,8,16])
def test_failed_event_global_balance_keeps_same_time_pre_event_and_prefix(profiles, monkeypatch, where):
    c = deepcopy(BY_ID['warm-mid']); c['events'][0]['step_index'] = where
    original = model._balances
    def fail(*args):
        if args[8] == 1:
            raise model.previous.BoundaryHold('BALANCE_HOLD: injected event ledger')
        return original(*args)
    monkeypatch.setattr(model, '_balances', fail)
    with pytest.raises(model.VentilationProgramHold, match='BALANCE_HOLD') as error:
        run(profiles, c)
    assert error.value.failed_phase == 'global-event-balance'
    assert error.value.step_index == where and error.value.last_confirmed['event_count'] == 0
    assert error.value.last_confirmed['phase'] == ('initial' if where == 0 else 'step-end')
    assert error.value.events == [] and all(s['step_index'] < where for s in error.value.samples)


def test_post_event_boundary_failure_never_commits_management(profiles, monkeypatch):
    applied = False
    original, evaluate = model.previous.management.apply_management, model.stage._evaluate
    def event(**kwargs):
        nonlocal applied
        value = original(**kwargs); applied = True; return value
    def fail(*args):
        if applied: raise model.stage.vent.VentilationHold('NUMERIC_HOLD: post-event boundary')
        return evaluate(*args)
    monkeypatch.setattr(model.previous.management, 'apply_management', event)
    monkeypatch.setattr(model.stage, '_evaluate', fail)
    with pytest.raises(model.VentilationProgramHold) as error: run(profiles)
    assert error.value.failed_phase == 'event-after-ventilation'
    assert error.value.last_confirmed['step_index'] == 8 and error.value.last_confirmed['event_count'] == 0
    assert error.value.events == [] and len(error.value.samples) == 1


def test_real_temperature_hold_keeps_selected_initial_prefix(profiles):
    c = deepcopy(BY_ID['warm-mid']); c['scenario']['forcing']['canopy_external_heat']['value'] = 1e7
    with pytest.raises(model.VentilationProgramHold, match='TEMPERATURE_HOLD') as error: run(profiles, c)
    assert error.value.failed_phase == 'interval' and error.value.inner_failed_stage == 'k2'
    assert error.value.last_confirmed_elapsed_seconds == 0 and len(error.value.samples) == 1


def test_maximum512_outputs128_events_and_new_identity(profiles, results):
    prior = json.loads((ROOT/'fixtures/crop-climate-joint-management-reference-cases-v1.json').read_bytes())
    zero = prior['cases'][0]['event']; events = []
    for index in range(128):
        e = deepcopy(zero); e['input_id'] = 'vent-max-'+str(index)
        events.append({'step_index': index, 'event': e})
    r = run(profiles, events=events, output_steps=[*range(511),512], step_seconds=.0625, step_count=512)
    assert len(r['samples']) == 512 and len(r['events']) == 128
    assert r['last_confirmed']['event_count'] == 128 and r['last_confirmed']['elapsed_seconds'] == 32
    assert r['numerical']['total_joint_rhs_evaluations'] == 3458
    assert all(q['value'] == 0 for q in r['event_totals'].values())
    a = results['warm-mid']
    assert a == run(profiles)
    assert a['code_sha256'] == sha256((ROOT/'backend/app/crop_greenhouse_ventilation_program.py').read_bytes()).hexdigest()
    assert a['stage_code_sha256'] == model.stage.CODE_SHA256 and a['driver_code_sha256'] == model.previous.CODE_SHA256
    assert a['ledger_schema_version'] == 'joint-ventilation-ledgers-v1'
    assert a['claim_scope'] == 'synthetic_joint_ventilation_management_program_only' and a['G0_G4'] == 'not_assessed'
