"""Shared solar/ventilation RK4; crop-greenhouse-solar-integration-v1.md."""
from hashlib import sha256
from math import isfinite, ulp
from pathlib import Path

from . import crop_climate_joint_integration as core
from . import crop_climate_joint_rhs as joint
from . import crop_greenhouse_solar_joint as solar_rhs
from . import crop_greenhouse_ventilation_joint as vent_joint

VERSION = 'joint-crop-climate-solar-ventilation-rk4-research-v1'
CODE_SHA256 = sha256(Path(__file__).read_bytes()).hexdigest()
PAR_FIELDS = ('outdoor', 'above_canopy', 'cover_reflected', 'cover_absorbed',
    'construction_intercepted', 'canopy_absorbed', 'floor_absorbed',
    'unresolved_reflected', 'upward_transmitted')
NIR_FIELDS = ('outdoor', 'available_virtual', 'canopy_absorbed', 'floor_absorbed',
    'upward_virtual', 'construction_unallocated')
FLUX_UNITS = {**vent_joint.FLUX_UNITS, 'canopy_non_solar_heat': core.ENERGY,
    **dict.fromkeys(('solar_par_'+k for k in PAR_FIELDS), core.ENERGY),
    **dict.fromkeys(('solar_nir_'+k for k in NIR_FIELDS), core.ENERGY)}
POLICY = {'composition': 'current_shared_solar_ventilation_RHS_once_per_trial',
    'sampling': 'solar_outdoor_and_other_forcing_constant_current_shared_state',
    'initial': 'complete_composition_validates_and_supplies_k1',
    'unallocated': 'no_floor_cover_reflection_construction_heat_credit'}


class SolarIntegrationHold(core.JointIntegrationHold):
    """An unavailable shared trial preserves only its last confirmed endpoint."""


def _need(condition, reason):
    if not condition:
        raise SolarIntegrationHold(reason)


def _held(exc, index, phase, last):
    reason = str(exc) if isinstance(exc, (joint.JointClimateHold, core.JointIntegrationHold)) else (
        'NUMERIC_HOLD: arithmetic failed')
    held = SolarIntegrationHold(f'{reason}: step={index}; stage={phase}')
    held.step_index, held.failed_stage, held.last_confirmed_sample = index, phase, last
    held.last_confirmed_elapsed_seconds = None if last is None else last['elapsed_seconds']
    return held


def _values(result):
    r, par, nir, outdoor = result['joint_rhs'], result['PAR_joint']['radiation'], result['NIR'], result['outdoor']
    rates, flux, _ = core._from_result(r, r['scenario'])
    vent = tuple(outdoor['forcing_contribution'][k]['value'] for k in
        ('air_external_sensible_heat', 'air_external_vapor')) + (
        outdoor['local_transfers']['latent_energy']['air']['value'],)
    optical = {'outdoor': par['diagnostics']['outdoor_PAR'],
        'above_canopy': par['diagnostics']['above_canopy_PAR'], **par['exterior_PAR_partition']}
    near = {'outdoor': nir['diagnostics']['outdoor_nir'],
        'available_virtual': nir['diagnostics']['available_virtual_nir'],
        'canopy_absorbed': nir['heat_components']['canopy_absorbed_nir'],
        'floor_absorbed': nir['heat_components']['floor_absorbed_nir'],
        'upward_virtual': nir['heat_components']['upward_virtual_nir'],
        'construction_unallocated': nir['heat_components']['construction_unallocated_nir']}
    extra = (result['scenario']['forcing']['canopy_non_solar_heat']['value'],) + tuple(
        optical[k]['value'] for k in PAR_FIELDS) + tuple(near[k]['value'] for k in NIR_FIELDS)
    return rates, flux+vent+extra, result


def _evaluate(base, solar, weather, state, profiles):
    return _values(solar_rhs.evaluate_rhs(scenario=core._scenario(base, state), solar=solar,
        ventilation=weather, **profiles))


def _sample(index, dt, base, state, result):
    par, nir = result['PAR_joint']['radiation'], result['NIR']
    return {**vent_joint._sample(index, dt, base, state, result['joint_rhs'], result['outdoor']),
        'solar_heat_composition': result['heat_composition'],
        'solar_par': {'input_sha256': par['input_sha256'], 'crop_forcing': par['crop_forcing'],
            'heat_composition': result['PAR_joint']['heat_composition'], 'diagnostics': par['diagnostics'],
            'interior_partition': par['interior_partition'], 'exterior_PAR_partition': par['exterior_PAR_partition']},
        'solar_nir': {k: nir[k] for k in ('input_sha256', 'optics', 'reflection_denominators',
            'heat_components', 'diagnostics', 'partition_residuals', 'partition_budgets')}}


def _partitions(totals, index):
    t = dict(zip(FLUX_UNITS, totals, strict=True))
    rows = {
        'canopy_solar_heat_partition': (t['canopy_external_heat'], -t['canopy_non_solar_heat'],
            -t['solar_par_canopy_absorbed'], -t['solar_nir_canopy_absorbed']),
        'interior_PAR_partition': (t['solar_par_above_canopy'], *(-t['solar_par_'+k] for k in
            ('canopy_absorbed', 'floor_absorbed', 'unresolved_reflected', 'upward_transmitted'))),
        'exterior_PAR_partition': (t['solar_par_outdoor'], *(-t['solar_par_'+k] for k in
            ('above_canopy', 'cover_reflected', 'cover_absorbed', 'construction_intercepted'))),
        'virtual_NIR_partition': (t['solar_nir_available_virtual'], *(-t['solar_nir_'+k] for k in
            ('canopy_absorbed', 'floor_absorbed', 'upward_virtual'))),
        'exterior_virtual_NIR_partition': (t['solar_nir_outdoor'], -t['solar_nir_available_virtual'],
            -t['solar_nir_construction_unallocated'])}
    residuals, budgets = {}, {}
    for name, terms in rows.items():
        value = core._sum(terms)
        budget = 64*(index+1)*ulp(core._sum(map(abs, terms)))
        _need(isfinite(budget) and abs(value) <= budget, 'BALANCE_HOLD: unresolved '+name)
        residuals[name], budgets[name] = core._q(value, core.ENERGY), core._q(budget, core.ENERGY)
    return residuals, budgets


def integrate(*, scenario, solar, ventilation, step_seconds, step_count,
        growth_profile, cohort_profile, transport_profile, exchange_profile):
    """Advance108 states/41 ledgers with current PAR, NIR and ventilation each trial."""
    _need(type(step_seconds) in (int, float), 'BUDGET_HOLD: numeric step required')
    try:
        dt = float(step_seconds)
    except OverflowError as exc:
        raise SolarIntegrationHold('BUDGET_HOLD: unrepresentable step') from exc
    _need(isfinite(dt) and dt > 0 and type(step_count) is int and 1 <= step_count <= 4096,
        'BUDGET_HOLD: positive step and1..4096 integer steps required')
    _need(isfinite(dt*step_count) and 0 < dt*step_count <= 600, 'BUDGET_HOLD:600s research horizon')
    profiles = dict(growth_profile=growth_profile, cohort_profile=cohort_profile,
        transport_profile=transport_profile, exchange_profile=exchange_profile)
    errors = (joint.JointClimateHold, core.JointIntegrationHold, OverflowError, ValueError, ZeroDivisionError)
    try:
        first = solar_rhs.evaluate_rhs(scenario=scenario, solar=solar, ventilation=ventilation, **profiles)
        base, solar, weather = first['scenario'], first['solar'], first['ventilation']
        initial = state = core._state(base)
        current = _values(first)
        cumulative = (0.0,)*len(FLUX_UNITS)
        samples = [_sample(0, dt, base, state, first)]
        latent = exchange_profile.values['latent_heat']
        reference = base['parameters']['reference_temperature']['value']
        def balances(candidate, totals, following, index):
            a, b = core._balances(initial, candidate, totals[:22], first['joint_rhs'],
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
            k1, j1, _ = current
            k2, j2, _ = _evaluate(base, solar, weather, core._advance(state, k1, dt/2), profiles)
            phase = 'k3'
            k3, j3, _ = _evaluate(base, solar, weather, core._advance(state, k2, dt/2), profiles)
            phase = 'k4'
            k4, j4, _ = _evaluate(base, solar, weather, core._advance(state, k3, dt), profiles)
            phase = 'endpoint'
            candidate = core._advance(state, core._weighted(k1, k2, k3, k4), dt)
            totals = core._advance(cumulative, core._weighted(j1, j2, j3, j4), dt)
            following = _evaluate(base, solar, weather, candidate, profiles)
            phase = 'endpoint_balance'
            residuals, budgets = balances(candidate, totals, following, index)
        except errors as exc:
            raise _held(exc, index, phase, samples[-1]) from exc
        state, cumulative, current = candidate, totals, following
        samples.append(_sample(index, dt, base, state, current[2]))
    numerical = {'method': 'shared-stage-fixed-rk4-v1', 'step_seconds': dt, 'step_count': step_count,
        'duration_seconds': dt*step_count, 'coupled_rhs_evaluations': 4*step_count+1,
        'PAR_evaluations': 4*step_count+1, 'NIR_evaluations': 4*step_count+1,
        'ventilation_evaluations': 4*step_count+1, 'total_joint_rhs_evaluations': 4*step_count+1,
        'extra_validation_RHS_evaluations': 0, 'forcing_sampling': POLICY['sampling'],
        'roundoff_rule': '64-ulp-per-step-ledger-v1', 'time_coordinate': 'elapsed_seconds_no_UTC_checkpoint'}
    components = {**joint.COMPONENT_CODE_SHA256, 'crop_climate_joint_rhs': joint.CODE_SHA256,
        'crop_climate_joint_integration': core.CODE_SHA256, 'crop_greenhouse_ventilation_joint': vent_joint.CODE_SHA256,
        **{m.__name__.rsplit('.', 1)[-1]: m.CODE_SHA256 for m in
            (solar_rhs, solar_rhs.vent, solar_rhs.par, solar_rhs.par.radiation, solar_rhs.nir)}}
    bound = {'model_version': VERSION, 'code_sha256': CODE_SHA256,
        'input_sha256': first['input_sha256'], 'component_code_sha256': components,
        'profile_sha256': first['joint_rhs']['profile_sha256'],
        'policy_sha256': core._hash({'solar_RHS': first['policy_sha256'], 'integration': POLICY}),
        'numerical': numerical}
    transfers = {k: core._q(v, FLUX_UNITS[k]) for k, v in zip(FLUX_UNITS, cumulative, strict=True)}
    return {**bound, 'calculation_sha256': core._hash(bound),
        'source_sha256': first['source_sha256'], 'notice_sha256': first['notice_sha256'],
        'initial_solar_calculation_sha256': first['calculation_sha256'],
        'state_schema_version': joint.STATE_SCHEMA, 'clock_contract': joint.CLOCK_CONTRACT,
        'ledger_schema_version': 'joint-solar-ventilation-ledgers-v1', 'scenario': base,
        'solar': solar, 'ventilation': weather, 'samples': samples, 'integrated_transfers': transfers,
        'canopy_water_boundary': core._q(-transfers['canopy_to_air_vapor']['value'], core.WATER),
        'balance_residuals': residuals, 'balance_budgets': budgets,
        'scope': 'software_research_only', 'claim_scope': 'synthetic_joint_solar_ventilation_integration_only',
        'G0_G4': 'not_assessed'}
