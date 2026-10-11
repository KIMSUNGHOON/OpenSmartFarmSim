"""Atomic event-grid ventilation; crop-greenhouse-ventilation-program-v1.md."""
from copy import deepcopy
from hashlib import sha256
from pathlib import Path

from . import crop_climate_joint_boundary as previous
from . import crop_greenhouse_ventilation_joint as stage

VERSION = 'joint-ventilation-management-program-research-v1'
CODE_SHA256 = sha256(Path(__file__).read_bytes()).hexdigest()
EVENT_UNITS = previous.EVENT_UNITS


class VentilationProgramHold(previous.BoundaryHold):
    """No successful program past an unavailable step/event/global balance."""


def _balances(seed, current, totals, events, first, last, index, dt, event_count, profiles):
    residuals, budgets = previous._balances(seed, current, totals, events, first, last, index+event_count, profiles)
    extra, limits = stage._partitions(tuple(totals[k]['value'] for k in stage.FLUX_UNITS),
        seed, index, dt, profiles['exchange_profile'].values['latent_heat'])
    return {**residuals, **extra}, {**budgets, **limits}


def _diagnostic(boundary):
    return {'input_sha256': boundary['input_sha256'], 'derived': boundary['derived'],
        'forcing_contribution': boundary['forcing_contribution'],
        'latent_energy': boundary['local_transfers']['latent_energy']['air']}


def _snapshot(index, dt, current, rhs, totals, events, count, residuals, budgets, phase, diagnostic):
    return {**previous._snapshot(index, dt, current, rhs, totals, events, count, residuals, budgets, phase),
        'ventilation': diagnostic}


def integrate_events(*, scenario, ventilation, events, output_steps, step_seconds, step_count,
        growth_profile, cohort_profile, transport_profile, exchange_profile):
    profiles = dict(growth_profile=growth_profile, cohort_profile=cohort_profile,
        transport_profile=transport_profile, exchange_profile=exchange_profile)
    confirmed, samples, journal, index, phase = None, [], [], 0, 'input'
    try:
        dt, schedule, outputs = previous._prepare(events, output_steps, step_seconds, step_count)
        previous._need(type(ventilation) is dict and set(ventilation) == {'input_id', 'origin', 'forcing'},
            'INPUT_HOLD: closed ventilation input required')
        phase = 'initial'
        validation = stage.joint.evaluate_rhs(scenario=scenario, **profiles)
        seed = current = validation['scenario']
        _, _, rhs, boundary = stage._evaluate(seed, ventilation, stage.core._state(seed), profiles)
        first = rhs
        weather = {k: boundary['scenario'][k] for k in ('input_id', 'origin', 'forcing')}
        diagnostic = _diagnostic(boundary)
        totals, event_totals = previous._zero(stage.FLUX_UNITS), previous._zero(EVENT_UNITS)
        event_count, calls, ventilation_calls = 0, 2, 1
        residuals, budgets = _balances(seed, current, totals, event_totals, first, rhs, 0, dt, 0, profiles)
        confirmed = _snapshot(0, dt, current, rhs, totals, event_totals, 0, residuals, budgets, 'initial', diagnostic)
        pending, requested = {row['step_index']: row['event'] for row in schedule}, set(outputs)
        for index in range(step_count+1):
            if index:
                phase = 'interval'
                part = stage.integrate(scenario=current, ventilation=weather, step_seconds=dt, step_count=1, **profiles)
                end = part['samples'][-1]
                candidate = {**current, **{k: end[k] for k in ('plant_state', 'cohort_state', 'climate_state')}}
                phase = 'global-step-balance'
                increments = previous._add(totals, part['integrated_transfers'], stage.FLUX_UNITS)
                next_rhs = {'derived': end['derived']}
                residuals, budgets = _balances(seed, candidate, increments, event_totals,
                    first, next_rhs, index, dt, event_count, profiles)
                current, totals, rhs, diagnostic = candidate, increments, next_rhs, end['ventilation']
                calls += part['numerical']['total_joint_rhs_evaluations']
                ventilation_calls += part['numerical']['ventilation_evaluations']
                confirmed = _snapshot(index, dt, current, rhs, totals, event_totals, event_count,
                    residuals, budgets, 'step-end', diagnostic)
            if index in pending:
                phase = 'event'
                applied = previous.management.apply_management(scenario=current, event=pending[index], **profiles)
                increment = {}
                for key, unit in EVENT_UNITS.items():
                    quantity = applied['removed'][key]
                    increment[key] = previous._q(previous._sum(q['value'] for q in quantity), unit) if isinstance(quantity, list) else quantity
                phase = 'event-after-ventilation'
                candidate = applied['after']['scenario']
                _, _, next_rhs, boundary = stage._evaluate(candidate, weather, stage.core._state(candidate), profiles)
                phase = 'global-event-balance'
                increments = previous._add(event_totals, increment, EVENT_UNITS)
                residuals, budgets = _balances(seed, candidate, totals, increments,
                    first, next_rhs, index, dt, event_count+1, profiles)
                current, event_totals, rhs = candidate, increments, next_rhs
                event_count += 1
                calls += 3
                ventilation_calls += 1
                diagnostic = _diagnostic(boundary)
                confirmed = _snapshot(index, dt, current, rhs, totals, event_totals, event_count,
                    residuals, budgets, 'boundary-after-event', diagnostic)
                journal.append({'step_index': index, 'elapsed_seconds': index*dt, 'management': applied,
                    'combined_forcing_after': rhs['scenario']['forcing'], 'ventilation_after': diagnostic})
            if index in requested:
                samples.append(confirmed)
    except (previous.BoundaryHold, stage.core.JointIntegrationHold, previous.management.JointManagementHold,
            stage.joint.JointClimateHold, stage.vent.VentilationHold, OverflowError, ValueError, ZeroDivisionError) as exc:
        known = (previous.BoundaryHold, stage.core.JointIntegrationHold, previous.management.JointManagementHold,
            stage.joint.JointClimateHold, stage.vent.VentilationHold)
        reason = str(exc) if isinstance(exc, known) else 'NUMERIC_HOLD: program arithmetic failed'
        held = VentilationProgramHold(f'{reason}: global_step={index}; phase={phase}')
        held.step_index, held.failed_phase, held.last_confirmed = index, phase, deepcopy(confirmed)
        held.last_confirmed_elapsed_seconds = None if confirmed is None else confirmed['elapsed_seconds']
        held.samples, held.events = deepcopy(samples), deepcopy(journal)
        held.inner_failed_stage = getattr(exc, 'failed_stage', None)
        raise held from exc
    numerical = {'method': 'single-step-current-ventilation-rk4-events-v1', 'step_seconds': dt,
        'step_count': step_count, 'duration_seconds': dt*step_count, 'total_joint_rhs_evaluations': calls,
        'ventilation_evaluations': ventilation_calls, 'coupled_rhs_evaluations': ventilation_calls,
        'input_validation_rhs_evaluations': 1+step_count, 'management_rhs_evaluations': 2*event_count,
        'forcing_sampling': 'other_and_outdoor_constant_ventilation_current_stage',
        'roundoff_rule': '64-ulp-per-step-and-event-global-ledger-v1',
        'time_coordinate': 'elapsed_step_grid_no_UTC_checkpoint', 'quantity_rule': 'cohort-decimal-rational-removal-v1'}
    bound = {'model_version': VERSION, 'code_sha256': CODE_SHA256,
        'stage_code_sha256': stage.CODE_SHA256, 'driver_code_sha256': previous.CODE_SHA256,
        'management_code_sha256': previous.management.CODE_SHA256,
        'component_code_sha256': {**stage.joint.COMPONENT_CODE_SHA256,
            'crop_climate_joint_rhs': stage.joint.CODE_SHA256, 'crop_climate_joint_integration': stage.core.CODE_SHA256,
            'crop_greenhouse_ventilation': stage.vent.CODE_SHA256},
        'input_sha256': previous._hash({'scenario': seed, 'ventilation': weather, 'events': schedule,
            'output_steps': outputs, 'numerical': numerical}),
        'initial_rhs_calculation_sha256': first['calculation_sha256'],
        'policy_sha256': previous._hash({'crop': first['policy_sha256'], 'ventilation': boundary['policy_sha256'],
            'events': numerical['quantity_rule'], 'sampling': numerical['forcing_sampling']}),
        'source_sha256': exchange_profile.source_sha256, 'notice_sha256': exchange_profile.notice_sha256,
        'profile_sha256': first['profile_sha256'], 'numerical': numerical}
    payload = {'samples': samples, 'events': journal, 'last_confirmed': confirmed,
        'integrated_transfers': totals, 'event_totals': event_totals}
    return {**bound, **payload, 'calculation_sha256': previous._hash(bound),
        'result_sha256': previous._hash(payload), 'status': 'completed', 'scenario': seed,
        'ventilation': weather, 'scheduled_events': schedule, 'output_steps': outputs,
        'state_schema_version': stage.joint.STATE_SCHEMA, 'ledger_schema_version': 'joint-ventilation-ledgers-v1',
        'clock_contract': 'elapsed-grid-current-ventilation-rk4-events-v1',
        'physical_clock_contract': stage.joint.CLOCK_CONTRACT, 'scope': 'software_research_only',
        'claim_scope': 'synthetic_joint_ventilation_management_program_only', 'G0_G4': 'not_assessed'}
