"""Current-stage ventilation RK4; crop-greenhouse-ventilation-joint-v1.md."""
from hashlib import sha256
from math import isfinite, ulp
from pathlib import Path

from . import crop_climate_joint_integration as core
from . import crop_climate_joint_rhs as joint
from . import crop_greenhouse_ventilation as vent

VERSION = 'joint-crop-climate-prescribed-ventilation-rk4-research-v1'
CODE_SHA256 = sha256(Path(__file__).read_bytes()).hexdigest()
FLUX_UNITS = {**core.FLUX_UNITS, 'ventilation_sensible_heat': core.ENERGY,
    'ventilation_vapor': core.WATER, 'ventilation_latent_energy': core.ENERGY}
POLICY = {'forcing_composition': 'other_prescribed_plus_current_stage_ventilation_once',
    'latent_energy': 'separate_vapor_ledger_no_sensible_credit',
    'weather_sampling': 'explicit_constant_interval', 'validation_rhs_evaluations': 1}


class JointVentilationHold(core.JointIntegrationHold):
    """No successful trajectory is returned past an unavailable shared stage."""


def _need(condition, reason):
    if not condition:
        raise JointVentilationHold(reason)


def _held(exc, index, phase, last):
    reason = str(exc) if isinstance(exc, (joint.JointClimateHold, core.JointIntegrationHold,
        vent.VentilationHold)) else 'NUMERIC_HOLD: arithmetic failed'
    held = JointVentilationHold(f'{reason}: step={index}; stage={phase}')
    held.step_index, held.failed_stage, held.last_confirmed_sample = index, phase, last
    held.last_confirmed_elapsed_seconds = None if last is None else last['elapsed_seconds']
    return held


def _evaluate(base, weather, state, profiles):
    current = core._scenario(base, state)
    boundary = vent.calculate_ventilation(scenario={
        'input_id': weather['input_id'], 'origin': weather['origin'], 'forcing': weather['forcing'],
        'state': {k: current['climate_state'][k] for k in vent.STATE_UNITS},
        'parameters': {k: current['parameters'][k] for k in vent.PARAMETER_UNITS}},
        profile=profiles['exchange_profile'])
    forcing = dict(current['forcing'])
    for key, quantity in boundary['forcing_contribution'].items():
        forcing[key] = core._q(core._sum((forcing[key]['value'], quantity['value'])), quantity['unit'])
    result = joint.evaluate_rhs(scenario={**current, 'forcing': forcing}, **profiles)
    rates, flux, _ = core._from_result(result, result['scenario'])
    extra = (boundary['forcing_contribution']['air_external_sensible_heat']['value'],
        boundary['forcing_contribution']['air_external_vapor']['value'],
        boundary['local_transfers']['latent_energy']['air']['value'])
    return rates, flux+extra, result, boundary


def _sample(index, dt, base, state, result, boundary):
    return {**core._sample(index, dt, base, state, result),
        'ventilation': {'input_sha256': boundary['input_sha256'], 'derived': boundary['derived'],
            'forcing_contribution': boundary['forcing_contribution'],
            'latent_energy': boundary['local_transfers']['latent_energy']['air']}}


def _partitions(totals, base, index, dt, latent):
    t = dict(zip(FLUX_UNITS, totals, strict=True))
    rows = {
        'ventilation_sensible_partition': ((t['air_external_sensible_heat'],
            -base['forcing']['air_external_sensible_heat']['value']*(index*dt),
            -t['ventilation_sensible_heat']), core.ENERGY),
        'ventilation_vapor_partition': ((t['air_external_vapor'],
            -base['forcing']['air_external_vapor']['value']*(index*dt),
            -t['ventilation_vapor']), core.WATER),
        'ventilation_latent_partition': ((t['ventilation_latent_energy'],
            -latent*t['ventilation_vapor']), core.ENERGY)}
    residuals, budgets = {}, {}
    for name, (terms, unit) in rows.items():
        value = core._sum(terms)
        budget = 64*(index+1)*ulp(core._sum(map(abs, terms)))
        _need(isfinite(budget) and abs(value) <= budget, 'BALANCE_HOLD: unresolved '+name)
        residuals[name], budgets[name] = core._q(value, unit), core._q(budget, unit)
    return residuals, budgets


def integrate(*, scenario, ventilation, step_seconds, step_count,
        growth_profile, cohort_profile, transport_profile, exchange_profile):
    """Advance shared states and25 ledgers with ventilation reevaluated per trial."""
    _need(type(step_seconds) in (int, float), 'BUDGET_HOLD: numeric step required')
    try:
        dt = float(step_seconds)
    except OverflowError as exc:
        raise JointVentilationHold('BUDGET_HOLD: unrepresentable step') from exc
    _need(isfinite(dt) and dt > 0 and type(step_count) is int and 1 <= step_count <= 4096,
        'BUDGET_HOLD: positive step and1..4096 integer steps required')
    _need(isfinite(dt*step_count) and 0 < dt*step_count <= 600, 'BUDGET_HOLD:600s research horizon')
    profiles = dict(growth_profile=growth_profile, cohort_profile=cohort_profile,
        transport_profile=transport_profile, exchange_profile=exchange_profile)
    errors = (joint.JointClimateHold, core.JointIntegrationHold, vent.VentilationHold,
        OverflowError, ValueError, ZeroDivisionError)
    try:
        _need(type(ventilation) is dict and set(ventilation) == {'input_id', 'origin', 'forcing'},
            'INPUT_HOLD: closed outdoor ventilation input required')
        validation = joint.evaluate_rhs(scenario=scenario, **profiles)
        base = validation['scenario']
        initial = state = core._state(base)
        current = _evaluate(base, ventilation, state, profiles)
        first = current[2]
        weather = {k: current[3]['scenario'][k] for k in ('input_id', 'origin', 'forcing')}
        cumulative = (0.0,)*len(FLUX_UNITS)
        samples = [_sample(0, dt, base, state, first, current[3])]
        latent = exchange_profile.values['latent_heat']
        reference = base['parameters']['reference_temperature']['value']
        residuals, budgets = core._balances(initial, state, cumulative[:22], first, first, 0, latent, reference)
        extra_residuals, extra_budgets = _partitions(cumulative, base, 0, dt, latent)
    except errors as exc:
        raise _held(exc, 0, 'initial', None) from exc
    for index in range(1, step_count+1):
        phase = 'k2'
        try:
            k1, j1, _, _ = current
            k2, j2, _, _ = _evaluate(base, weather, core._advance(state, k1, dt/2), profiles)
            phase = 'k3'
            k3, j3, _, _ = _evaluate(base, weather, core._advance(state, k2, dt/2), profiles)
            phase = 'k4'
            k4, j4, _, _ = _evaluate(base, weather, core._advance(state, k3, dt), profiles)
            phase = 'endpoint'
            candidate = core._advance(state, core._weighted(k1, k2, k3, k4), dt)
            totals = core._advance(cumulative, core._weighted(j1, j2, j3, j4), dt)
            following = _evaluate(base, weather, candidate, profiles)
            phase = 'endpoint_balance'
            residuals, budgets = core._balances(initial, candidate, totals[:22],
                first, following[2], index, latent, reference)
            extra_residuals, extra_budgets = _partitions(totals, base, index, dt, latent)
        except errors as exc:
            raise _held(exc, index, phase, samples[-1]) from exc
        state, cumulative, current = candidate, totals, following
        samples.append(_sample(index, dt, base, state, current[2], current[3]))
    numerical = {'method': 'shared-stage-fixed-rk4-v1', 'step_seconds': dt, 'step_count': step_count,
        'duration_seconds': dt*step_count, 'coupled_rhs_evaluations': 4*step_count+1,
        'ventilation_evaluations': 4*step_count+1, 'input_validation_rhs_evaluations': 1,
        'total_joint_rhs_evaluations': 4*step_count+2,
        'forcing_sampling': 'other_and_outdoor_constant_ventilation_current_stage',
        'roundoff_rule': '64-ulp-per-step-ledger-v1', 'time_coordinate': 'elapsed_seconds_no_UTC_checkpoint'}
    components = {**joint.COMPONENT_CODE_SHA256, 'crop_climate_joint_rhs': joint.CODE_SHA256,
        'crop_climate_joint_integration': core.CODE_SHA256, 'crop_greenhouse_ventilation': vent.CODE_SHA256}
    input_hash = core._hash({'scenario': base, 'ventilation': weather})
    bound = {'model_version': VERSION, 'code_sha256': CODE_SHA256, 'input_sha256': input_hash,
        'component_code_sha256': components, 'profile_sha256': first['profile_sha256'],
        'policy_sha256': core._hash({'joint': first['policy_sha256'],
            'ventilation': current[3]['policy_sha256'], 'integration': POLICY}), 'numerical': numerical}
    transfers = {k: core._q(v, FLUX_UNITS[k]) for k, v in zip(FLUX_UNITS, cumulative, strict=True)}
    return {**bound, 'calculation_sha256': core._hash(bound),
        'source_sha256': exchange_profile.source_sha256, 'notice_sha256': exchange_profile.notice_sha256,
        'initial_joint_input_sha256': validation['input_sha256'],
        'state_schema_version': joint.STATE_SCHEMA, 'clock_contract': joint.CLOCK_CONTRACT,
        'ledger_schema_version': 'joint-ventilation-ledgers-v1', 'scenario': base, 'ventilation': weather,
        'samples': samples, 'integrated_transfers': transfers,
        'canopy_water_boundary': core._q(-transfers['canopy_to_air_vapor']['value'], core.WATER),
        'balance_residuals': {**residuals, **extra_residuals}, 'balance_budgets': {**budgets, **extra_budgets},
        'scope': 'software_research_only',
        'claim_scope': 'synthetic_joint_crop_climate_prescribed_ventilation_only', 'G0_G4': 'not_assessed'}
