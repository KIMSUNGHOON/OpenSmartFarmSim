"""Piecewise outdoor forcing and atomic events; crop-greenhouse-co2-program-v1.md."""
from copy import deepcopy
from hashlib import sha256
from math import isfinite, ulp
from pathlib import Path

from . import crop_climate_joint_boundary as previous
from . import crop_greenhouse_co2_integration as stage
from . import crop_greenhouse_co2_management as management

VERSION = "joint-co2-solar-forcing-management-program-research-v1"
CODE_SHA256 = sha256(Path(__file__).read_bytes()).hexdigest()
EVENT_UNITS = previous.EVENT_UNITS
BOUNDARIES = ("solar", "ventilation", "co2")
POLICY = {"forcing": "piecewise_constant_old_interval_then_new_boundary",
          "events": "new_forcing_then_atomic_removal_then_selected_output",
          "scenario": "fixed_geometry_profiles_and_uncomposed_internal_sources",
          "carbon": "44_over_30_event_carbohydrate_removed_once_not_emission"}


class ProgramHold(previous.BoundaryHold):
    """Keep only confirmed boundaries and the committed journal after failure."""


def _forcing(rows, count, origin):
    previous._need(type(rows) is list and 1 <= len(rows) <= 512, "BUDGET_HOLD:1..512 forcing rows required")
    last = -1
    for row in rows:
        previous._need(type(row) is dict and set(row) == {"step_index", *BOUNDARIES},
                       "INPUT_HOLD: closed forcing row required")
        i = row["step_index"]
        previous._need(type(i) is int and last < i <= count and (last != -1 or i == 0),
                       "TIME_HOLD: forcing indices start at0 and strictly increase in grid")
        previous._need(all(type(row[k]) is dict for k in BOUNDARIES), "INPUT_HOLD: forcing blocks required")
        previous._need(all(row[k].get("origin") == origin for k in BOUNDARIES), "INPUT_HOLD: mixed forcing origins")
        last = i
    return deepcopy(rows)


def _balances(seed, current, totals, events, first, last, index, dt, event_count, profiles):
    operations = index + event_count
    a, b = previous._balances(seed, current, totals, events, first, last, operations, profiles)
    values = tuple(totals[k]["value"] for k in stage.FLUX_UNITS)
    c, d = stage.previous.vent_joint._partitions(values[:25], seed, index, dt,
        profiles["exchange_profile"].values["latent_heat"])
    e, f = stage.previous._partitions(values[:41], index)
    carbon = lambda s: previous._sum([s["plant_state"][k]["value"] for k in ("buffer", "leaf", "stem_root")]
        + [q["value"] for q in s["cohort_state"]["fruit_carbohydrate"]])
    m0, m1 = (s["climate_state"]["air_co2_mass"]["value"] for s in (seed, current))
    c0, c1 = carbon(seed), carbon(current)
    t = {k: q["value"] for k, q in totals.items()}
    ratio = stage.rhs.net.CO2_MOLAR_MASS / stage.rhs.net.CH2O_MOLAR_MASS
    removed = previous._sum(events[k]["value"] for k in ("leaf", "stem_root", "fruit_carbohydrate"))
    mass_terms = (m1-m0, *(-t[k] for k in stage.CO2_FIELDS))
    combined = (m1-m0, ratio*(c1-c0), ratio*removed, *(ratio*t[k] for k in
        ("removal_leaf", "removal_stem_root", "terminal_fruit_carbohydrate")),
        -t["co2_ventilation_to_air"], -t["co2_external_to_air"])
    mass_budget = 64*(index+1)*ulp(max(abs(m0), abs(m1), previous._sum(map(abs, mass_terms))))
    combined_budget = previous._sum((mass_budget, ratio*b["carbohydrate"]["value"],
        64*(operations+1)*ulp(max(abs(previous._sum((m0, ratio*c0))),
            abs(previous._sum((m1, ratio*c1))), previous._sum(map(abs, combined))))))
    g, h = {}, {}
    for key, terms, budget in (("air_co2", mass_terms, mass_budget),
                              ("crop_air_carbon_equivalent", combined, combined_budget)):
        value = previous._sum(terms)
        previous._need(isfinite(budget) and abs(value) <= budget, "BALANCE_HOLD: unresolved global " + key)
        g[key], h[key] = previous._q(value, stage.CO2_UNIT), previous._q(budget, stage.CO2_UNIT)
    return {**a, **c, **e, **g}, {**b, **d, **f, **h}


def _diagnostic(current, rhs):
    state = stage.core._state(current) + (current["climate_state"]["air_co2_mass"]["value"],)
    return stage._sample(0, 1, current, state, rhs)


def _snapshot(index, dt, diagnostic, active, totals, events, count, residuals, budgets, phase):
    return {**diagnostic, "step_index": index, "elapsed_seconds": index*dt,
        "forcing_step_index": active["step_index"], "integrated_transfers": totals,
        "event_totals": events, "event_count": count, "balance_residuals": residuals,
        "balance_budgets": budgets, "phase": phase}


def integrate_events(*, scenario, forcing_program, events, output_steps, step_seconds, step_count,
                     growth_profile, cohort_profile, transport_profile, exchange_profile):
    """Confirm each old-forcing interval, new boundary and removal before output."""
    profiles = dict(growth_profile=growth_profile, cohort_profile=cohort_profile,
                    transport_profile=transport_profile, exchange_profile=exchange_profile)
    confirmed, samples, journal, index, phase = None, [], [], 0, "input"
    errors = (previous.BoundaryHold, management.Co2ManagementHold, stage.core.JointIntegrationHold,
              stage.joint.JointClimateHold, OverflowError, ValueError, ZeroDivisionError)
    try:
        dt, schedule, outputs = previous._prepare(events, output_steps, step_seconds, step_count)
        previous._need(type(scenario) is dict and all(row["event"]["origin"] == scenario.get("origin")
            for row in schedule), "INPUT_HOLD: mixed event origins")
        forcing = _forcing(forcing_program, step_count, scenario.get("origin"))
        phase = "initial"
        initial = stage.rhs.evaluate_rhs(scenario=scenario, **{k: forcing[0][k] for k in BOUNDARIES}, **profiles)
        seed = current = initial["scenario"]; first = initial["solar_rhs"]["joint_rhs"]
        active = {"step_index": 0, **{k: initial[k] for k in BOUNDARIES}}; normalized = [active]
        diagnostic = _diagnostic(current, initial)
        totals, event_totals = previous._zero(stage.FLUX_UNITS), previous._zero(EVENT_UNITS)
        event_count, calls = 0, 1
        def balance(candidate, t, e, diag, i, n):
            return _balances(seed, candidate, t, e, first, {"derived": diag["derived"]}, i, dt, n, profiles)
        residuals, budgets = balance(current, totals, event_totals, diagnostic, 0, 0)
        confirmed = _snapshot(0, dt, diagnostic, active, totals, event_totals, 0, residuals, budgets, "initial")
        changes = {row["step_index"]: row for row in forcing[1:]}
        pending, requested = {row["step_index"]: row["event"] for row in schedule}, set(outputs)
        for index in range(step_count+1):
            if index:
                phase = "interval"
                part = stage.integrate(scenario=current, **{k: active[k] for k in BOUNDARIES},
                    step_seconds=dt, step_count=1, **profiles)
                end = part["samples"][-1]
                candidate = {**current, **{k: end[k] for k in ("plant_state", "cohort_state", "climate_state")}}
                increments = previous._add(totals, part["integrated_transfers"], stage.FLUX_UNITS)
                phase = "global-step-balance"
                residuals, budgets = balance(candidate, increments, event_totals, end, index, event_count)
                current, totals, diagnostic = candidate, increments, end
                calls += part["numerical"]["coupled_rhs_evaluations"]
                confirmed = _snapshot(index, dt, diagnostic, active, totals, event_totals,
                    event_count, residuals, budgets, "step-end")
            if index in changes:
                phase = "forcing"
                changed = stage.rhs.evaluate_rhs(scenario=current,
                    **{k: changes[index][k] for k in BOUNDARIES}, **profiles)
                next_diagnostic = _diagnostic(current, changed)
                residuals, budgets = balance(current, totals, event_totals, next_diagnostic, index, event_count)
                active = {"step_index": index, **{k: changed[k] for k in BOUNDARIES}}
                normalized.append(active); diagnostic = next_diagnostic; calls += 1
                confirmed = _snapshot(index, dt, diagnostic, active, totals, event_totals,
                    event_count, residuals, budgets, "forcing-boundary")
            if index in pending:
                phase = "event"
                applied = management.apply_management(scenario=current,
                    **{k: active[k] for k in BOUNDARIES}, event=pending[index], **profiles)
                increment = {}
                for key, unit in EVENT_UNITS.items():
                    quantity = applied["removed"][key]
                    increment[key] = previous._q(previous._sum(q["value"] for q in quantity), unit) if isinstance(quantity, list) else quantity
                candidate = applied["after"]["scenario"]
                next_diagnostic = _diagnostic(candidate, applied["after_rhs"])
                increments = previous._add(event_totals, increment, EVENT_UNITS)
                phase = "global-event-balance"
                residuals, budgets = balance(candidate, totals, increments, next_diagnostic, index, event_count+1)
                current, event_totals, diagnostic = candidate, increments, next_diagnostic
                event_count += 1; calls += 2
                confirmed = _snapshot(index, dt, diagnostic, active, totals, event_totals,
                    event_count, residuals, budgets, "boundary-after-event")
                journal.append({"step_index": index, "elapsed_seconds": index*dt,
                    "forcing_step_index": active["step_index"], "management": applied})
            if index in requested:
                samples.append(confirmed)
    except errors as exc:
        reason = str(exc) if isinstance(exc, errors[:4]) else "NUMERIC_HOLD: program arithmetic failed"
        held = ProgramHold(f"{reason}: global_step={index}; phase={phase}")
        held.step_index, held.failed_phase, held.last_confirmed = index, phase, deepcopy(confirmed)
        held.last_confirmed_elapsed_seconds = None if confirmed is None else confirmed["elapsed_seconds"]
        held.samples, held.events = deepcopy(samples), deepcopy(journal)
        held.inner_failed_stage = getattr(exc, "failed_stage", None)
        raise held from exc
    numerical = {"method": "single-step-current-co2-solar-rk4-piecewise-events-v1",
        "step_seconds": dt, "step_count": step_count, "duration_seconds": dt*step_count,
        "state_count": 109, "ledger_count": 44, "event_count": event_count,
        "forcing_rows": len(normalized), "coupled_rhs_evaluations": calls,
        "management_rhs_evaluations": 2*event_count, "forcing_change_rhs_evaluations": len(normalized)-1,
        "extra_validation_RHS_evaluations": 0, "roundoff_rule": "64-ulp-per-step-and-event-global-ledger-v1",
        "time_coordinate": "elapsed_step_grid_no_UTC_checkpoint", "quantity_rule": management.POLICY["quantity_rule"]}
    bound = {"model_version": VERSION, "code_sha256": CODE_SHA256, "stage_code_sha256": stage.CODE_SHA256,
        "management_code_sha256": management.CODE_SHA256, "driver_code_sha256": previous.CODE_SHA256,
        "component_code_sha256": part["component_code_sha256"], "profile_sha256": initial["profile_sha256"],
        "input_sha256": previous._hash({"scenario": seed, "forcing_program": normalized,
            "events": schedule, "output_steps": outputs, "numerical": numerical}),
        "initial_rhs_calculation_sha256": initial["calculation_sha256"], "numerical": numerical,
        "policy_sha256": previous._hash({"program": POLICY, "stage": stage.POLICY, "management": management.POLICY,
            "initial_RHS": initial["policy_sha256"], "solar": initial["solar_rhs"]["policy_sha256"]})}
    payload = {"samples": samples, "events": journal, "last_confirmed": confirmed,
               "integrated_transfers": totals, "event_totals": event_totals}
    return {**bound, **payload, "calculation_sha256": previous._hash(bound),
        "result_sha256": previous._hash(payload), "status": "completed", "scenario": seed,
        "forcing_program": normalized, "scheduled_events": schedule, "output_steps": outputs,
        "source_sha256": {**initial["source_sha256"], "solar": initial["solar_rhs"]["source_sha256"]},
        "notice_sha256": initial["solar_rhs"]["notice_sha256"], "state_schema_version": stage.rhs.STATE_SCHEMA,
        "ledger_schema_version": "joint-solar-co2-ledgers-v1", "event_schema_version": "joint-co2-solar-event-ledgers-v1",
        "scope": "software_research_only", "claim_scope": "synthetic_joint_co2_solar_forcing_management_only",
        "G0_G4": "not_assessed"}
