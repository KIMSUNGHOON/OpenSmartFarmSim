"""Independent solar/event trajectories, actual composition and atomic holds."""
from copy import deepcopy
from decimal import Decimal, localcontext
from hashlib import sha256
import json
from math import fsum
from pathlib import Path
import runpy

import pytest

from app import crop_greenhouse_solar_program as model
from app import crop_greenhouse_ventilation_program as old_vent
from test_crop_greenhouse_solar_integration import profiles
from test_crop_climate_joint_boundary import independent_balances, state, state_equal, metrics as stock_metrics

ROOT = Path(__file__).resolve().parents[2]
FIXTURE = ROOT/'fixtures/crop-greenhouse-solar-program-reference-cases-v1.json'
DOCUMENT = json.loads(FIXTURE.read_bytes())
CASES = DOCUMENT['cases']
BY_ID = {c['case_id']: c for c in CASES}


def run(profiles, case=None, dt=2, **changes):
    c = BY_ID['warm-mid'] if case is None else case
    scale = lambda n: int(n*c['step_seconds']/dt)
    kwargs = {k: c[k] for k in ('scenario', 'solar', 'ventilation')}
    kwargs.update(events=[{'step_index': scale(e['step_index']), 'event': e['event']} for e in c['events']],
        output_steps=[scale(i) for i in c['output_steps']], step_seconds=dt,
        step_count=scale(c['step_count']), **profiles)
    kwargs.update(changes)
    return model.integrate_events(**kwargs)


@pytest.fixture(scope='module')
def results(profiles):
    return {c['case_id']: run(profiles, c) for c in CASES}


def radiation_balances(t):
    q = {k: v['value'] for k, v in t.items()}
    return [fsum((q['canopy_external_heat'], -q['canopy_non_solar_heat'],
            -q['solar_par_canopy_absorbed'], -q['solar_nir_canopy_absorbed'])),
        fsum((q['solar_par_above_canopy'], *(-q['solar_par_'+k] for k in
            ('canopy_absorbed','floor_absorbed','unresolved_reflected','upward_transmitted')))),
        fsum((q['solar_par_outdoor'], *(-q['solar_par_'+k] for k in
            ('above_canopy','cover_reflected','cover_absorbed','construction_intercepted')))),
        fsum((q['solar_nir_available_virtual'], *(-q['solar_nir_'+k] for k in
            ('canopy_absorbed','floor_absorbed','upward_virtual')))),
        fsum((q['solar_nir_outdoor'], -q['solar_nir_available_virtual'], -q['solar_nir_construction_unallocated']))]


@pytest.mark.parametrize('case', CASES, ids=lambda c: c['case_id'])
def test_independent5214_selected_scalars_journals_and15_raw_balances(results, profiles, case):
    r = results[case['case_id']]
    for actual, expected in zip(r['samples'], case['expected_decimal']['samples'], strict=True):
        assert actual['step_index'] == expected['step_index']
        assert actual['elapsed_seconds'] == float(expected['elapsed_seconds'])
        assert actual['event_count'] == expected['event_count']
        state_equal(state(actual), expected['state'])
        for block in ('integrated_transfers', 'event_totals', 'derived'):
            for key, wanted in expected[block].items():
                assert actual[block][key]['value'] == pytest.approx(float(wanted), rel=5e-12, abs=5e-14), key
        assert actual['derived']['canopy_temperature']['value'] == pytest.approx(
            float(expected['derived']['canopy_temperature']), rel=0, abs=2e-10)
        assert len(actual['balance_residuals']) == 15
        for key, q in actual['balance_residuals'].items():
            assert abs(q['value']) <= actual['balance_budgets'][key]['value']
        for key, value in independent_balances(profiles, case, actual).items():
            assert abs(value) <= {'number': 1e-12, 'vapor_and_water_boundaries': 1e-13,
                'crop_capacity': 1e-8}.get(key, 1e-7), key
        assert max(map(abs, radiation_balances(actual['integrated_transfers']))) <= 1e-7
        t, f, elapsed = actual['integrated_transfers'], case['scenario']['forcing'], actual['elapsed_seconds']
        for total, vent, limit in [('air_external_sensible_heat','ventilation_sensible_heat',1e-7),
                ('air_external_vapor','ventilation_vapor',1e-13)]:
            assert abs(fsum((t[total]['value'], -f[total]['value']*elapsed, -t[vent]['value']))) <= limit
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
        for k in ('ventilation_sensible_heat','ventilation_vapor')}}


@pytest.mark.parametrize('name', ['warm-mid','reverse-mid','dark-mid'])
def test72_fixed_event_time_independent_step_halving_ratios(profiles, results, name):
    c = BY_ID[name]
    with localcontext() as context:
        context.prec = 80
        target = metrics(c['fine_32s_dt0_25_decimal']['samples'][-1])
        rows = [run(profiles, c, dt=8), run(profiles, c, dt=4), results[name]]
        errors = [{k: abs(v-target[k]) for k,v in metrics(r['last_confirmed']).items()} for r in rows]
        for key in target:
            a, b, d = (e[key] for e in errors)
            assert a > b > d > 0 and a/b > 8 and b/d > 8, (name,key,a,b,d)
        assert all(r['events'][0]['elapsed_seconds'] == 16 for r in rows)


def test_oracle_pins_exact_bytes_and_independent_case_inputs():
    path = ROOT/'research/crop-greenhouse-solar-program-reference.py'
    assert DOCUMENT['generator_sha256'] == sha256(path.read_bytes()).hexdigest()
    for name, digest in DOCUMENT['input_sha256'].items():
        assert sha256((ROOT/name).read_bytes()).hexdigest() == digest
    expected = runpy.run_path(str(path))['references']()
    assert expected == DOCUMENT
    assert (json.dumps(expected, indent=2, sort_keys=True, allow_nan=False)+'\n').encode() == FIXTURE.read_bytes()
    original = deepcopy(expected['cases'][0]['solar'])
    expected['cases'][-1]['solar']['values']['solar_nir_fraction']['value'] = .25
    assert expected['cases'][0]['solar'] == original


def test_actual_calls_order_source_inputs_and_post_event_optics(profiles, monkeypatch):
    originals = {k: v for k,v in (
        ('solar',model.stage.solar_rhs.evaluate_rhs), ('core',model.stage.joint.evaluate_rhs),
        ('PAR',model.stage.solar_rhs.par.radiation.calculate_par),
        ('NIR',model.stage.solar_rhs.nir.calculate_nir), ('vent',model.stage.solar_rhs.vent.calculate_ventilation),
        ('event',model.previous.management.apply_management))}
    calls = {k: [] for k in originals}; trace = []
    def record(name):
        def wrapped(**kwargs):
            if name == 'event': trace.append('event-start')
            result = originals[name](**kwargs)
            calls[name].append((deepcopy(kwargs['scenario']),result))
            trace.append(name)
            return result
        return wrapped
    for module, name, key in [(model.stage.solar_rhs,'evaluate_rhs','solar'),
            (model.stage.joint,'evaluate_rhs','core'), (model.stage.solar_rhs.par.radiation,'calculate_par','PAR'),
            (model.stage.solar_rhs.nir,'calculate_nir','NIR'),
            (model.stage.solar_rhs.vent,'calculate_ventilation','vent'),
            (model.previous.management,'apply_management','event')]:
        monkeypatch.setattr(module, name, record(key))
    c = deepcopy(BY_ID['multiple']); saved = deepcopy(c)
    r = run(profiles, c); n, e = c['step_count'], len(c['events'])
    assert c == saved and r['scenario']['forcing'] == c['scenario']['forcing']
    for name in ('solar','PAR','NIR','vent'):
        assert len(calls[name]) == 1+5*n+2*e
    assert len(calls['core']) == r['numerical']['total_joint_rhs_evaluations'] == 1+5*n+4*e
    assert r['numerical']['coupled_rhs_evaluations'] == 1+5*n+2*e
    assert r['numerical']['management_rhs_evaluations'] == 2*e
    assert r['numerical']['extra_validation_RHS_evaluations'] == 0
    assert all(s['forcing'] == c['scenario']['forcing'] for s,_ in calls['solar'])
    for index, entry in enumerate(trace):
        if entry == 'event-start':
            assert trace[index-1:index+5] == ['solar','event-start','core','core','event','NIR']
    for journal, sample in zip(r['events'], r['samples'], strict=True):
        applied = journal['management']; before, after = journal['solar_before'], journal['solar_after']
        assert sample['phase'] == 'boundary-after-event'
        assert sample['plant_state'] == applied['after']['scenario']['plant_state']
        assert all(sample[k] == after[k] for k in model.DIAGNOSTICS)
        assert applied['before']['scenario']['forcing'] == applied['after']['scenario']['forcing'] == journal['combined_forcing_before']
        assert applied['before']['derived']['leaf_area_index']['value'] > applied['after']['derived']['leaf_area_index']['value']
        assert before['solar_heat_composition']['canopy_absorbed_par']['value'] > after['solar_heat_composition']['canopy_absorbed_par']['value']
        assert before['solar_nir']['heat_components']['canopy_absorbed_nir']['value'] > after['solar_nir']['heat_components']['canopy_absorbed_nir']['value']
        assert before['solar_par']['crop_forcing'] == after['solar_par']['crop_forcing']
        assert before['ventilation'] == after['ventilation']
        assert applied['before']['derived']['canopy_temperature']['value'] == pytest.approx(
            applied['after']['derived']['canopy_temperature']['value'], rel=0, abs=2e-13)
        for key,q in after['ventilation']['forcing_contribution'].items():
            assert journal['combined_forcing_after'][key]['value'] == fsum((c['scenario']['forcing'][key]['value'],q['value']))
        assert journal['combined_forcing_after']['canopy_external_heat'] == after['solar_heat_composition']['canopy_external_heat']


def test_no_events_short_kernel_and_selection_invariance(profiles, results):
    c, r = BY_ID['no-events'], results['no-events']
    short = model.stage.integrate(**{k:c[k] for k in ('scenario','solar','ventilation','step_seconds','step_count')}, **profiles)
    for key in ('plant_state','cohort_state','climate_state','derived',*model.DIAGNOSTICS):
        assert r['last_confirmed'][key] == short['samples'][-1][key]
    assert r['integrated_transfers'] == short['integrated_transfers']
    a, b = results['warm-mid'], run(profiles, output_steps=[0,16])
    assert a['last_confirmed'] == b['last_confirmed'] and a['events'] == b['events']
    assert a['calculation_sha256'] != b['calculation_sha256']


def test_darkness_matches_accepted_ventilation_program(profiles, results):
    c = BY_ID['dark-mid']; s = deepcopy(c['scenario'])
    s['forcing']['canopy_external_heat'] = s['forcing'].pop('canopy_non_solar_heat')
    s['forcing']['par_above_canopy'] = {'value':0,'unit':model.stage.solar_rhs.par.radiation.PHOTONS}
    old = old_vent.integrate_events(scenario=s, **{k:c[k] for k in
        ('ventilation','events','output_steps','step_seconds','step_count')}, **profiles)
    r = results['dark-mid']
    for a,b in zip(r['samples'],old['samples'],strict=True):
        for key in ('plant_state','cohort_state','climate_state','derived','event_totals'):
            assert a[key] == b[key]
        for key,q in b['integrated_transfers'].items(): assert a['integrated_transfers'][key] == q


@pytest.mark.parametrize('fault', ['solar_extra','solar_unit','old_forcing','spectrum','mixed_event',
    'weather_missing','profile','duplicate','reverse','output_missing','output_duplicate','budget',
    'too_many_events','too_many_outputs'])
def test_closed_inputs_hold_before_confirmation(profiles, fault):
    c, changes = deepcopy(BY_ID['warm-mid']), {}
    if fault == 'solar_extra': c['solar']['values']['leaf_area_index'] = {'value':1,'unit':'m2_leaf/m2_floor'}
    if fault == 'solar_unit': c['solar']['values']['outdoor_global_radiation']['unit'] = 'J'
    if fault == 'old_forcing': c['scenario']['forcing']['canopy_external_heat'] = {'value':1,'unit':'W/m2_floor'}
    if fault == 'spectrum': c['solar']['values']['solar_nir_fraction']['value'] = .1
    if fault == 'mixed_event': c['events'][0]['event']['origin'] = 'research'
    if fault == 'weather_missing': del c['ventilation']['forcing']['outdoor_vapor_pressure']
    if fault == 'profile': changes['growth_profile'] = None
    if fault == 'duplicate': changes['events'] = c['events']*2
    if fault == 'reverse': changes['events'] = list(reversed(BY_ID['multiple']['events']))
    if fault == 'output_missing': changes['output_steps'] = [8,16]
    if fault == 'output_duplicate': changes['output_steps'] = [0,0,16]
    if fault == 'budget': changes['step_seconds'] = True
    if fault == 'too_many_events': changes['events'] = c['events']*129
    if fault == 'too_many_outputs': changes['output_steps'] = list(range(513))
    with pytest.raises(model.SolarProgramHold) as error: run(profiles,c,**changes)
    assert error.value.last_confirmed is None and error.value.samples == error.value.events == []


@pytest.mark.parametrize('where',[0,8,16])
@pytest.mark.parametrize('failure',['event','after','balance'])
def test_failed_event_keeps_same_time_pre_event_and_no_output_or_journal(profiles, monkeypatch, where, failure):
    c = deepcopy(BY_ID['warm-mid']); c['events'][0]['step_index'] = where
    if failure == 'event': c['events'][0]['event']['values']['leaf']['value'] = 1e15
    if failure == 'after':
        original, apply = model.stage.solar_rhs.evaluate_rhs, model.previous.management.apply_management
        applied = False
        def event(**kwargs):
            nonlocal applied
            result = apply(**kwargs); applied = True; return result
        def fail(**kwargs):
            if applied: raise model.stage.solar_rhs.SolarJointHold('NUMERIC_HOLD: post-event optics')
            return original(**kwargs)
        monkeypatch.setattr(model.previous.management,'apply_management',event)
        monkeypatch.setattr(model.stage.solar_rhs,'evaluate_rhs',fail)
    if failure == 'balance':
        original = model._balances
        def fail(*args):
            if args[8] == 1: raise model.previous.BoundaryHold('BALANCE_HOLD: event ledger')
            return original(*args)
        monkeypatch.setattr(model,'_balances',fail)
    with pytest.raises(model.SolarProgramHold) as error: run(profiles,c)
    held = error.value
    assert held.failed_phase == {'event':'event','after':'event-after-solar','balance':'global-event-balance'}[failure]
    assert held.step_index == where and held.last_confirmed['event_count'] == 0
    assert held.last_confirmed['phase'] == ('initial' if where == 0 else 'step-end')
    assert held.last_confirmed['elapsed_seconds'] == where*2
    assert held.events == [] and all(s['step_index'] < where for s in held.samples)


def test_real_interval_hold_preserves_initial_prefix(profiles):
    c = deepcopy(BY_ID['warm-mid']); c['scenario']['forcing']['canopy_non_solar_heat']['value'] = 1e7
    with pytest.raises(model.SolarProgramHold,match='TEMPERATURE_HOLD') as error: run(profiles,c)
    assert error.value.failed_phase == 'interval' and error.value.inner_failed_stage == 'k2'
    assert error.value.last_confirmed_elapsed_seconds == 0 and len(error.value.samples) == 1


@pytest.mark.parametrize('failure',['before','step-balance','second-event'])
def test_later_failure_preserves_prior_event_journal_and_detached_prefix(profiles, monkeypatch, results, failure):
    c = deepcopy(BY_ID['multiple'])
    if failure == 'step-balance':
        original = model._balances
        def fail(*args):
            if args[6] == 8 and args[8] == 1:
                raise model.previous.BoundaryHold('BALANCE_HOLD: interval global ledger')
            return original(*args)
        monkeypatch.setattr(model,'_balances',fail)
    elif failure == 'before':
        original = model.stage.solar_rhs.evaluate_rhs
        def fail(**kwargs):
            leaf = kwargs['scenario']['plant_state']['leaf']['value']
            if kwargs['scenario']['forcing'] == c['scenario']['forcing'] and leaf == results['multiple']['events'][1]['management']['before']['scenario']['plant_state']['leaf']['value']:
                # Initial evaluation and interval endpoint are valid; fail the repeat before the second event.
                fail.count += 1
                if fail.count == 2: raise model.stage.solar_rhs.SolarJointHold('NUMERIC_HOLD: pre-event optics')
            return original(**kwargs)
        fail.count = 0
        monkeypatch.setattr(model.stage.solar_rhs,'evaluate_rhs',fail)
    else:
        c['events'][1]['event']['values']['leaf']['value'] = 1e15
    with pytest.raises(model.SolarProgramHold) as error: run(profiles,c)
    held = error.value
    assert held.step_index == 8 and held.last_confirmed['event_count'] == 1
    assert held.failed_phase == {'before':'event-before-solar','step-balance':'global-step-balance','second-event':'event'}[failure]
    assert held.last_confirmed['step_index'] == (7 if failure == 'step-balance' else 8)
    assert len(held.events) == len(held.samples) == 1
    assert held.events[0] == results['multiple']['events'][0]
    saved = deepcopy(held.events[0]); held.samples[0]['plant_state']['leaf']['value'] = -1
    assert held.events[0] == saved


def test_maximum_outputs_events_and_new_identity(profiles, results):
    events = []
    for index in range(128):
        e = deepcopy(BY_ID['warm-mid']['events'][0]['event']);e['input_id'] = 'solar-max-'+str(index)
        e['values']['leaf']['value'] = e['values']['stem_root']['value'] = 0
        for q in e['values']['fruit_fraction']: q['value'] = 0
        events.append({'step_index':index,'event':e})
    r = run(profiles,events=events,output_steps=[*range(511),512],step_seconds=.0625,step_count=512)
    assert len(r['samples']) == 512 and len(r['events']) == 128
    assert r['last_confirmed']['event_count'] == 128 and r['last_confirmed']['elapsed_seconds'] == 32
    assert r['numerical']['total_joint_rhs_evaluations'] == 3073
    assert all(q['value'] == 0 for q in r['event_totals'].values())
    a = results['warm-mid']; assert a == run(profiles)
    assert a['code_sha256'] == sha256((ROOT/'backend/app/crop_greenhouse_solar_program.py').read_bytes()).hexdigest()
    assert a['stage_code_sha256'] == model.stage.CODE_SHA256
    assert a['ledger_schema_version'] == 'joint-solar-ventilation-ledgers-v1'
    assert a['claim_scope'] == 'synthetic_joint_solar_ventilation_management_program_only'
    assert a['G0_G4'] == 'not_assessed'
