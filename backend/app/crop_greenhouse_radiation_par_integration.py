"""Shared solar PAR/ventilation RK4; crop-greenhouse-radiation-par-integration-v1.md."""
from hashlib import sha256
from math import isfinite, ulp
from pathlib import Path

from . import crop_climate_joint_integration as core
from . import crop_climate_joint_rhs as joint
from . import crop_greenhouse_radiation_par_joint as par
from . import crop_greenhouse_ventilation_joint as vent_joint

VERSION = 'joint-crop-climate-solar-par-ventilation-rk4-research-v1'
CODE_SHA256 = sha256(Path(__file__).read_bytes()).hexdigest()
PAR_FIELDS = ('outdoor', 'above_canopy', 'cover_reflected', 'cover_absorbed',
    'construction_intercepted', 'canopy_absorbed', 'floor_absorbed',
    'unresolved_reflected', 'upward_transmitted')
FLUX_UNITS = {**vent_joint.FLUX_UNITS, 'canopy_non_par_heat': core.ENERGY,
    **dict.fromkeys(('solar_par_'+k for k in PAR_FIELDS), core.ENERGY)}
POLICY = {'forcing': 'explicit_non_PAR_plus_current_PAR_and_current_ventilation_once',
    'radiation_heat_credit': 'canopy_absorbed_PAR_only',
    'sampling': 'solar_outdoor_and_other_forcing_constant_current_shared_state',
    'validation_PAR_and_RHS_evaluations': 1}


class RadiationPARIntegrationHold(core.JointIntegrationHold):
    """An unavailable shared trial preserves only the last confirmed endpoint."""


def _need(condition, reason):
    if not condition:
        raise RadiationPARIntegrationHold(reason)


def _held(exc, index, phase, last):
    reason = str(exc) if isinstance(exc, (joint.JointClimateHold, core.JointIntegrationHold,
        vent_joint.vent.VentilationHold)) else 'NUMERIC_HOLD: arithmetic failed'
    held = RadiationPARIntegrationHold(f'{reason}: step={index}; stage={phase}')
    held.step_index, held.failed_stage, held.last_confirmed_sample = index, phase, last
    held.last_confirmed_elapsed_seconds = None if last is None else last['elapsed_seconds']
    return held


def _evaluate(base, solar, weather, state, profiles):
    current = core._scenario(base, state)
    boundary = vent_joint.vent.calculate_ventilation(scenario={
        **weather, 'state': {k: current['climate_state'][k] for k in vent_joint.vent.STATE_UNITS},
        'parameters': {k: current['parameters'][k] for k in vent_joint.vent.PARAMETER_UNITS}},
        profile=profiles['exchange_profile'])
    forcing = dict(current['forcing'])
    for key, q in boundary['forcing_contribution'].items():
        forcing[key] = core._q(core._sum((forcing[key]['value'], q['value'])), q['unit'])
    result = par.evaluate_rhs(scenario={**current, 'forcing': forcing}, solar=solar, **profiles)
    r, radiation = result['joint_rhs'], result['radiation']
    rates, flux, _ = core._from_result(r, r['scenario'])
    vent_flux = tuple(boundary['forcing_contribution'][k]['value'] for k in
        ('air_external_sensible_heat', 'air_external_vapor')) + (
        boundary['local_transfers']['latent_energy']['air']['value'],)
    optical = {'outdoor': radiation['diagnostics']['outdoor_PAR'],
        'above_canopy': radiation['diagnostics']['above_canopy_PAR'], **radiation['exterior_PAR_partition']}
    par_flux = (base['forcing']['canopy_non_par_heat']['value'],) + tuple(
        optical[k]['value'] for k in PAR_FIELDS)
    return rates, flux+vent_flux+par_flux, result, boundary


def _sample(index, dt, base, state, result, boundary):
    r = result['radiation']
    return {**vent_joint._sample(index, dt, base, state, result['joint_rhs'], boundary),
        'solar_par': {'input_sha256': r['input_sha256'], 'crop_forcing': r['crop_forcing'],
            'heat_composition': result['heat_composition'], 'diagnostics': r['diagnostics'],
            'interior_partition': r['interior_partition'], 'exterior_PAR_partition': r['exterior_PAR_partition']}}


def _partitions(totals, index):
    t = dict(zip(FLUX_UNITS, totals, strict=True))
    rows = {
        'canopy_PAR_heat_partition': (t['canopy_external_heat'], -t['canopy_non_par_heat'],
            -t['solar_par_canopy_absorbed']),
        'interior_PAR_partition': (t['solar_par_above_canopy'], *(-t['solar_par_'+k] for k in
            ('canopy_absorbed', 'floor_absorbed', 'unresolved_reflected', 'upward_transmitted'))),
        'exterior_PAR_partition': (t['solar_par_outdoor'], *(-t['solar_par_'+k] for k in
            ('above_canopy', 'cover_reflected', 'cover_absorbed', 'construction_intercepted')))}
    residuals, budgets = {}, {}
    for name, terms in rows.items():
        value = core._sum(terms)
        budget = 64*(index+1)*ulp(core._sum(map(abs, terms)))
        _need(isfinite(budget) and abs(value) <= budget, 'BALANCE_HOLD: unresolved '+name)
        residuals[name], budgets[name] = core._q(value, core.ENERGY), core._q(budget, core.ENERGY)
    return residuals, budgets


def integrate(*, scenario, solar, ventilation, step_seconds, step_count,
        growth_profile, cohort_profile, transport_profile, exchange_profile):
    """Advance108 states and35 ledgers with current PAR and ventilation each trial."""
    _need(type(step_seconds) in (int, float), 'BUDGET_HOLD: numeric step required')
    try:
        dt = float(step_seconds)
    except OverflowError as exc:
        raise RadiationPARIntegrationHold('BUDGET_HOLD: unrepresentable step') from exc
    _need(isfinite(dt) and dt > 0 and type(step_count) is int and 1 <= step_count <= 4096,
        'BUDGET_HOLD: positive step and1..4096 integer steps required')
    _need(isfinite(dt*step_count) and 0 < dt*step_count <= 600, 'BUDGET_HOLD:600s research horizon')
    profiles = dict(growth_profile=growth_profile, cohort_profile=cohort_profile,
        transport_profile=transport_profile, exchange_profile=exchange_profile)
    errors = (joint.JointClimateHold, core.JointIntegrationHold,
        vent_joint.vent.VentilationHold, OverflowError, ValueError, ZeroDivisionError)
    try:
        _need(type(ventilation) is dict and set(ventilation) == {'input_id', 'origin', 'forcing'},
            'INPUT_HOLD: closed outdoor ventilation input required')
        validation = par.evaluate_rhs(scenario=scenario, solar=solar, **profiles)
        base, solar = validation['scenario'], validation['solar']
        _need(ventilation['origin'] == base['origin'], 'INPUT_HOLD: mixed research origins')
        initial = state = core._state(base)
        current = _evaluate(base, solar, ventilation, state, profiles)
        first = current[2]['joint_rhs']
        weather = {k: current[3]['scenario'][k] for k in ('input_id', 'origin', 'forcing')}
        cumulative = (0.0,)*len(FLUX_UNITS)
        samples = [_sample(0, dt, base, state, current[2], current[3])]
        latent = exchange_profile.values['latent_heat']
        reference = base['parameters']['reference_temperature']['value']
        def balances(candidate, totals, following, index):
            a, b = core._balances(initial, candidate, totals[:22], first,
                following[2]['joint_rhs'], index, latent, reference)
            c, d = vent_joint._partitions(totals[:25], base, index, dt, latent)
            e, f = _partitions(totals, index)
            return {**a, **c, **e}, {**b, **d, **f}
        residuals, budgets = balances(state, cumulative, current, 0)
    except errors as exc:
        raise _held(exc, 0, 'initial', None) from exc
    for index in range(1, step_count+1):
        phase = 'k2'
        try:
            k1, j1, _, _ = current
            k2, j2, _, _ = _evaluate(base, solar, weather, core._advance(state, k1, dt/2), profiles)
            phase = 'k3'
            k3, j3, _, _ = _evaluate(base, solar, weather, core._advance(state, k2, dt/2), profiles)
            phase = 'k4'
            k4, j4, _, _ = _evaluate(base, solar, weather, core._advance(state, k3, dt), profiles)
            phase = 'endpoint'
            candidate = core._advance(state, core._weighted(k1, k2, k3, k4), dt)
            totals = core._advance(cumulative, core._weighted(j1, j2, j3, j4), dt)
            following = _evaluate(base, solar, weather, candidate, profiles)
            phase = 'endpoint_balance'
            residuals, budgets = balances(candidate, totals, following, index)
        except errors as exc:
            raise _held(exc, index, phase, samples[-1]) from exc
        state, cumulative, current = candidate, totals, following
        samples.append(_sample(index, dt, base, state, current[2], current[3]))
    numerical = {'method': 'shared-stage-fixed-rk4-v1', 'step_seconds': dt, 'step_count': step_count,
        'duration_seconds': dt*step_count, 'coupled_rhs_evaluations': 4*step_count+1,
        'ventilation_evaluations': 4*step_count+1, 'PAR_evaluations': 4*step_count+2,
        'input_validation_PAR_and_RHS_evaluations': 1, 'total_joint_rhs_evaluations': 4*step_count+2,
        'forcing_sampling': POLICY['sampling'], 'roundoff_rule': '64-ulp-per-step-ledger-v1',
        'time_coordinate': 'elapsed_seconds_no_UTC_checkpoint'}
    components = {**joint.COMPONENT_CODE_SHA256, 'crop_climate_joint_rhs': joint.CODE_SHA256,
        'crop_climate_joint_integration': core.CODE_SHA256,
        'crop_greenhouse_ventilation': vent_joint.vent.CODE_SHA256,
        'crop_greenhouse_ventilation_joint': vent_joint.CODE_SHA256,
        'crop_greenhouse_radiation_par': par.radiation.CODE_SHA256,
        'crop_greenhouse_radiation_par_joint': par.CODE_SHA256}
    bound = {'model_version': VERSION, 'code_sha256': CODE_SHA256,
        'input_sha256': core._hash({'scenario': base, 'solar': solar, 'ventilation': weather}),
        'component_code_sha256': components, 'profile_sha256': first['profile_sha256'],
        'policy_sha256': core._hash({'joint': first['policy_sha256'], 'PAR': current[2]['policy_sha256'],
            'radiation': current[2]['radiation']['policy_sha256'],
            'ventilation': current[3]['policy_sha256'], 'integration': POLICY}), 'numerical': numerical}
    transfers = {k: core._q(v, FLUX_UNITS[k]) for k, v in zip(FLUX_UNITS, cumulative, strict=True)}
    return {**bound, 'calculation_sha256': core._hash(bound),
        'source_sha256': {'PAR': par.radiation.SOURCE_SHA256, 'exchange': exchange_profile.source_sha256},
        'notice_sha256': {'PAR': par.radiation.NOTICE_SHA256, 'exchange': exchange_profile.notice_sha256},
        'initial_PAR_joint_input_sha256': validation['input_sha256'],
        'state_schema_version': joint.STATE_SCHEMA, 'clock_contract': joint.CLOCK_CONTRACT,
        'ledger_schema_version': 'joint-solar-par-ventilation-ledgers-v1',
        'scenario': base, 'solar': solar, 'ventilation': weather, 'samples': samples,
        'integrated_transfers': transfers,
        'canopy_water_boundary': core._q(-transfers['canopy_to_air_vapor']['value'], core.WATER),
        'balance_residuals': residuals, 'balance_budgets': budgets,
        'scope': 'software_research_only', 'claim_scope': 'synthetic_joint_solar_PAR_ventilation_only',
        'G0_G4': 'not_assessed'}
