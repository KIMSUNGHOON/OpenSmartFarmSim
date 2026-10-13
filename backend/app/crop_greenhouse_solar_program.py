"""Atomic solar event grid; crop-greenhouse-solar-program-v1.md."""
from copy import deepcopy
from hashlib import sha256
from pathlib import Path

from . import crop_climate_joint_boundary as previous
from . import crop_greenhouse_solar_integration as stage

VERSION = 'joint-solar-ventilation-management-program-research-v1'
CODE_SHA256 = sha256(Path(__file__).read_bytes()).hexdigest()
EVENT_UNITS = previous.EVENT_UNITS
DIAGNOSTICS = ('ventilation', 'solar_heat_composition', 'solar_par', 'solar_nir')


class SolarProgramHold(previous.BoundaryHold):
    """Keep only confirmed program boundaries after an unavailable calculation."""


def _balances(seed, current, totals, events, first, last, index, dt, event_count, profiles):
    residuals, budgets = previous._balances(seed, current, totals, events, first, last,
        index+event_count, profiles)
    values = tuple(totals[k]['value'] for k in stage.FLUX_UNITS)
    a, b = stage.vent_joint._partitions(values[:25], seed, index, dt,
        profiles['exchange_profile'].values['latent_heat'])
    c, d = stage._partitions(values, index)
    return {**residuals, **a, **c}, {**budgets, **b, **d}


def _diagnostic(index, dt, current, result):
    sample = stage._sample(index, dt, current, stage.core._state(current), result)
    return {k: sample[k] for k in DIAGNOSTICS}


def _snapshot(index, dt, current, rhs, totals, events, count, residuals, budgets, phase, diagnostic):
    return {**previous._snapshot(index, dt, current, rhs, totals, events, count,
        residuals, budgets, phase), **diagnostic}


def integrate_events(*, scenario, solar, ventilation, events, output_steps, step_seconds, step_count,
        growth_profile, cohort_profile, transport_profile, exchange_profile):
    profiles = dict(growth_profile=growth_profile, cohort_profile=cohort_profile,
        transport_profile=transport_profile, exchange_profile=exchange_profile)
    confirmed, samples, journal, index, phase = None, [], [], 0, 'input'
    errors = (previous.BoundaryHold, previous.management.JointManagementHold,
        stage.core.JointIntegrationHold, stage.joint.JointClimateHold,
        OverflowError, ValueError, ZeroDivisionError)
    try:
        dt, schedule, outputs = previous._prepare(events, output_steps, step_seconds, step_count)
        previous._need(type(scenario) is dict and all(row['event']['origin'] == scenario.get('origin')
            for row in schedule), 'INPUT_HOLD: mixed event origins')
        phase = 'initial'
        initial = stage.solar_rhs.evaluate_rhs(scenario=scenario, solar=solar, ventilation=ventilation, **profiles)
        seed = current = initial['scenario']
        sun, weather, first = initial['solar'], initial['ventilation'], initial['joint_rhs']
        rhs, diagnostic = first, _diagnostic(0, dt, current, initial)
        totals, event_totals = previous._zero(stage.FLUX_UNITS), previous._zero(EVENT_UNITS)
        event_count, coupled_calls = 0, 1
        residuals, budgets = _balances(seed, current, totals, event_totals, first, rhs, 0, dt, 0, profiles)
        confirmed = _snapshot(0, dt, current, rhs, totals, event_totals, 0,
            residuals, budgets, 'initial', diagnostic)
        pending, requested = {row['step_index']: row['event'] for row in schedule}, set(outputs)
        for index in range(step_count+1):
            if index:
                phase = 'interval'
                part = stage.integrate(scenario=current, solar=sun, ventilation=weather,
                    step_seconds=dt, step_count=1, **profiles)
                end = part['samples'][-1]
                candidate = {**current, **{k: end[k] for k in ('plant_state', 'cohort_state', 'climate_state')}}
                phase = 'global-step-balance'
                increments = previous._add(totals, part['integrated_transfers'], stage.FLUX_UNITS)
                next_rhs = {'derived': end['derived']}
                residuals, budgets = _balances(seed, candidate, increments, event_totals,
                    first, next_rhs, index, dt, event_count, profiles)
                current, totals, rhs = candidate, increments, next_rhs
                coupled_calls += part['numerical']['coupled_rhs_evaluations']
                diagnostic = {k: end[k] for k in DIAGNOSTICS}
                confirmed = _snapshot(index, dt, current, rhs, totals, event_totals, event_count,
                    residuals, budgets, 'step-end', diagnostic)
            if index in pending:
                phase = 'event-before-solar'
                before = stage.solar_rhs.evaluate_rhs(scenario=current, solar=sun,
                    ventilation=weather, **profiles)
                before_diagnostic = _diagnostic(index, dt, current, before)
                phase = 'event'
                applied = previous.management.apply_management(scenario=before['joint_rhs']['scenario'],
                    event=pending[index], **profiles)
                increment = {}
                for key, unit in EVENT_UNITS.items():
                    quantity = applied['removed'][key]
                    increment[key] = previous._q(previous._sum(q['value'] for q in quantity), unit) if isinstance(quantity, list) else quantity
                candidate = {**applied['after']['scenario'], 'forcing': seed['forcing']}
                phase = 'event-after-solar'
                after = stage.solar_rhs.evaluate_rhs(scenario=candidate, solar=sun,
                    ventilation=weather, **profiles)
                next_rhs = after['joint_rhs']
                next_diagnostic = _diagnostic(index, dt, candidate, after)
                phase = 'global-event-balance'
                increments = previous._add(event_totals, increment, EVENT_UNITS)
                residuals, budgets = _balances(seed, candidate, totals, increments,
                    first, next_rhs, index, dt, event_count+1, profiles)
                current, event_totals, rhs = candidate, increments, next_rhs
                event_count += 1
                coupled_calls += 2
                diagnostic = next_diagnostic
                confirmed = _snapshot(index, dt, current, rhs, totals, event_totals, event_count,
                    residuals, budgets, 'boundary-after-event', diagnostic)
                journal.append({'step_index': index, 'elapsed_seconds': index*dt, 'management': applied,
                    'combined_forcing_before': before['joint_rhs']['scenario']['forcing'],
                    'combined_forcing_after': after['joint_rhs']['scenario']['forcing'],
                    'solar_before': before_diagnostic,
                    'solar_after': diagnostic})
            if index in requested:
                samples.append(confirmed)
    except errors as exc:
        known = errors[:4]
        reason = str(exc) if isinstance(exc, known) else 'NUMERIC_HOLD: program arithmetic failed'
        held = SolarProgramHold(f'{reason}: global_step={index}; phase={phase}')
        held.step_index, held.failed_phase, held.last_confirmed = index, phase, deepcopy(confirmed)
        held.last_confirmed_elapsed_seconds = None if confirmed is None else confirmed['elapsed_seconds']
        held.samples, held.events = deepcopy(samples), deepcopy(journal)
        held.inner_failed_stage = getattr(exc, 'failed_stage', None)
        raise held from exc
    numerical = {'method': 'single-step-current-solar-ventilation-rk4-events-v1',
        'step_seconds': dt, 'step_count': step_count, 'duration_seconds': dt*step_count,
        'coupled_rhs_evaluations': coupled_calls, 'PAR_evaluations': coupled_calls,
        'NIR_evaluations': coupled_calls, 'ventilation_evaluations': coupled_calls,
        'management_rhs_evaluations': 2*event_count, 'total_joint_rhs_evaluations': coupled_calls+2*event_count,
        'extra_validation_RHS_evaluations': 0,
        'forcing_sampling': stage.POLICY['sampling'],
        'event_forcing': 'compose_before_validate_removal_restore_source_compose_after',
        'roundoff_rule': '64-ulp-per-step-and-event-global-ledger-v1',
        'time_coordinate': 'elapsed_step_grid_no_UTC_checkpoint',
        'quantity_rule': 'cohort-decimal-rational-removal-v1'}
    bound = {'model_version': VERSION, 'code_sha256': CODE_SHA256,
        'stage_code_sha256': stage.CODE_SHA256, 'driver_code_sha256': previous.CODE_SHA256,
        'management_code_sha256': previous.management.CODE_SHA256,
        'component_code_sha256': part['component_code_sha256'],
        'input_sha256': previous._hash({'scenario': seed, 'solar': sun, 'ventilation': weather,
            'events': schedule, 'output_steps': outputs, 'numerical': numerical}),
        'initial_rhs_calculation_sha256': initial['calculation_sha256'],
        'policy_sha256': previous._hash({'solar_RHS': initial['policy_sha256'], 'integration': stage.POLICY,
            'events': numerical['quantity_rule'], 'event_forcing': numerical['event_forcing']}),
        'source_sha256': initial['source_sha256'], 'notice_sha256': initial['notice_sha256'],
        'profile_sha256': first['profile_sha256'], 'numerical': numerical}
    payload = {'samples': samples, 'events': journal, 'last_confirmed': confirmed,
        'integrated_transfers': totals, 'event_totals': event_totals}
    return {**bound, **payload, 'calculation_sha256': previous._hash(bound),
        'result_sha256': previous._hash(payload), 'status': 'completed', 'scenario': seed,
        'solar': sun, 'ventilation': weather, 'scheduled_events': schedule, 'output_steps': outputs,
        'state_schema_version': stage.joint.STATE_SCHEMA, 'ledger_schema_version': 'joint-solar-ventilation-ledgers-v1',
        'clock_contract': 'elapsed-grid-current-solar-ventilation-rk4-events-v1',
        'physical_clock_contract': stage.joint.CLOCK_CONTRACT, 'scope': 'software_research_only',
        'claim_scope': 'synthetic_joint_solar_ventilation_management_program_only', 'G0_G4': 'not_assessed'}
