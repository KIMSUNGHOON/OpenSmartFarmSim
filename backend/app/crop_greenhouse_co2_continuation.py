"""Immutable109-state resume; crop-greenhouse-co2-continuation-v1.md."""
from copy import deepcopy
from dataclasses import dataclass, field
from hashlib import sha256
import json
from math import isfinite
from pathlib import Path

from . import crop_climate_joint_continuation as transport
from . import crop_greenhouse_co2_program as driver

VERSION = "joint-co2-solar-continuation-research-v2"
CHECKPOINT_VERSION = "joint-co2-solar-checkpoint-v2"
CODE_SHA256 = sha256(Path(__file__).read_bytes()).hexdigest()
MAX_CONTEXT_BYTES = 2*1024**2
MAX_CHECKPOINT_BYTES = 65536
MAX_CHUNK_BOUNDARIES = 128
PROFILE_NAMES = transport.PROFILE_NAMES
_canonical, _hash, _digest, _prefix = transport._canonical, transport._hash, transport._digest, transport._prefix
_TOKEN = object()


class ContinuationRejected(ValueError):
    """Invalid context/checkpoint/budget; no numerical interval began."""


def _need(condition, reason):
    if not condition:
        raise ContinuationRejected(reason)


def _identity(profiles):
    rhs = driver.stage.rhs; solar = rhs.solar_rhs
    modules = (driver, driver.stage, driver.management, rhs, rhs.gas, rhs.net, rhs.air,
               solar, solar.par, solar.par.radiation, solar.nir, solar.vent,
               driver.stage.previous, driver.stage.previous.vent_joint)
    return {**transport._identity(profiles), "engine_version": VERSION, "engine_code_sha256": CODE_SHA256,
        "transport_helpers_code_sha256": transport.CODE_SHA256,
        "co2_solar_component_code_sha256": {m.__name__.rsplit('.', 1)[-1]: m.CODE_SHA256 for m in modules},
        "co2_solar_policy_sha256": {m.__name__.rsplit('.', 1)[-1]: _hash(m.POLICY) for m in modules if hasattr(m, 'POLICY')},
        "state_schema": rhs.STATE_SCHEMA, "ledger_schema": "joint-solar-co2-ledgers-v1",
        "event_schema": "joint-co2-solar-event-ledgers-v1", "balance_count": 17,
        "journal_schema": driver.JOURNAL_SCHEMA,
        "source_sha256": {"gas": rhs.gas.SOURCE_SHA256, "net": rhs.net.SOURCE_SHA256,
            "air_mass": rhs.air.SOURCE_SHA256, "PAR": solar.par.radiation.SOURCE_SHA256,
            "NIR": solar.nir.SOURCE_SHA256, "exchange": profiles[-1].source_sha256},
        "notice_sha256": {"PAR": solar.par.radiation.NOTICE_SHA256, "NIR": solar.nir.NOTICE_SHA256,
            "exchange": profiles[-1].notice_sha256}}


@dataclass(frozen=True)
class Context:
    _program: bytes
    _manifest: bytes
    _first: bytes
    root_sha256: str
    _profiles: tuple = field(repr=False)
    _token: object = field(repr=False)

    @property
    def manifest(self): return json.loads(self._manifest)
    @property
    def program(self): return json.loads(self._program)


@dataclass(frozen=True)
class Checkpoint:
    _raw: bytes = field(repr=False)
    sha256: str
    context_sha256: str
    _token: object = field(repr=False)

    @property
    def value(self): return json.loads(self._raw)


def _profiles(context):
    return {k+'_profile': p for k, p in zip(PROFILE_NAMES, context._profiles, strict=True)}


def _context(context):
    _need(type(context) is Context and context._token is _TOKEN, "CONTEXT_HOLD: prepared CO2 context required")
    try:
        _need(all(type(v) is bytes for v in (context._program, context._manifest, context._first))
            and len(context._program)+len(context._manifest)+len(context._first) <= MAX_CONTEXT_BYTES,
            "RESOURCE_HOLD: bounded immutable context bytes required")
        manifest = context.manifest
        _need(_hash(manifest) == context.root_sha256 and manifest["identity"] == _identity(context._profiles)
            and manifest["program_sha256"] == sha256(context._program).hexdigest()
            and manifest["initial_rhs_sha256"] == sha256(context._first).hexdigest(),
            "CONTEXT_HOLD: changed code/profile/environment/program/seed")
        return context.program, json.loads(context._first)
    except (ValueError, TypeError, KeyError, AttributeError) as exc:
        raise ContinuationRejected("CONTEXT_HOLD: invalid immutable context: "+str(exc)) from exc


def prepare_context(*, scenario, forcing_program, events, output_steps, step_seconds, step_count,
                    growth_profile, cohort_profile, transport_profile, exchange_profile):
    profiles = (growth_profile, cohort_profile, transport_profile, exchange_profile)
    kwargs = {k+'_profile': p for k, p in zip(PROFILE_NAMES, profiles, strict=True)}
    try:
        dt, schedule, outputs = driver.previous._prepare(events, output_steps, step_seconds, step_count)
        _need(type(scenario) is dict and all(row["event"]["origin"] == scenario.get("origin") for row in schedule),
              "INPUT_HOLD: mixed event origins")
        forcing = driver._forcing(forcing_program, step_count, scenario.get("origin"))
        first = driver.stage.rhs.evaluate_rhs(scenario=scenario,
            **{k: forcing[0][k] for k in driver.BOUNDARIES}, **kwargs)
        forcing[0] = {"step_index": 0, **{k: first[k] for k in driver.BOUNDARIES}}
        program = {"scenario": first["scenario"], "forcing_program": forcing, "events": schedule,
                   "output_steps": outputs, "step_seconds": dt, "step_count": step_count}
        raw, initial = _canonical(program), _canonical(first)
        manifest = {"identity": _identity(profiles), "program_sha256": sha256(raw).hexdigest(),
            "initial_rhs_sha256": sha256(initial).hexdigest(), "initial_calculation_sha256": first["calculation_sha256"],
            "policy_sha256": _hash({"program": driver.POLICY, "stage": driver.stage.POLICY,
                "management": driver.management.POLICY, "RHS": first["policy_sha256"],
                "solar": first["solar_rhs"]["policy_sha256"]}),
            "numerical": {"step_seconds": dt, "step_count": step_count, "duration_seconds": dt*step_count,
                "method": "single-step-current-co2-solar-rk4-piecewise-events-v1",
                "roundoff_rule": "64-ulp-per-step-and-event-global-ledger-v1"},
            "scope": "software_research_only", "clock_contract": "elapsed-grid-current-co2-solar-events-v1"}
        bound = _canonical(manifest)
        _need(len(raw)+len(initial)+len(bound) <= MAX_CONTEXT_BYTES, "RESOURCE_HOLD: context byte limit")
    except (driver.previous.BoundaryHold, driver.stage.joint.JointClimateHold,
            OverflowError, ValueError, ZeroDivisionError) as exc:
        raise ContinuationRejected(str(exc)) from exc
    return Context(raw, bound, initial, sha256(bound).hexdigest(), profiles, _TOKEN)


def _balances(context, program, first, current, t, e, diagnostic, index, count):
    return driver._balances(program["scenario"], current, t, e, first["solar_rhs"]["joint_rhs"],
        {"derived": diagnostic["derived"]}, index, program["step_seconds"], count, _profiles(context))


def _initial(context, program, first):
    t, e = driver.previous._zero(driver.stage.FLUX_UNITS), driver.previous._zero(driver.EVENT_UNITS)
    diagnostic = driver._diagnostic(program["scenario"], first)
    residuals, budgets = _balances(context, program, first, program["scenario"], t, e, diagnostic, 0, 0)
    return {"version": CHECKPOINT_VERSION, "context_sha256": context.root_sha256, "next_index": 0,
        "forcing_cursor": 1, "output_cursor": 0, "event_cursor": 0,
        "output_prefix_sha256": _hash([]), "event_prefix_sha256": _hash([]),
        "last_confirmed": driver._snapshot(0, program["step_seconds"], diagnostic, program["forcing_program"][0],
            t, e, 0, residuals, budgets, "initial")}


def _seal(context, payload):
    raw = _canonical(payload)
    _need(len(raw) <= MAX_CHECKPOINT_BYTES, "RESOURCE_HOLD: checkpoint byte limit")
    return Checkpoint(raw, sha256(raw).hexdigest(), context.root_sha256, _TOKEN)


def start(context):
    program, first = _context(context)
    return _seal(context, _initial(context, program, first))


def checkpoint_bytes(context, checkpoint):
    _context(context)
    _need(type(checkpoint) is Checkpoint and checkpoint._token is _TOKEN
        and checkpoint.context_sha256 == context.root_sha256 and type(checkpoint._raw) is bytes
        and len(checkpoint._raw) <= MAX_CHECKPOINT_BYTES and sha256(checkpoint._raw).hexdigest() == checkpoint.sha256,
        "CHECKPOINT_HOLD: immutable matching CO2 checkpoint required")
    return checkpoint._raw


def _validate(context, payload, program, first):
    initial = _initial(context, program, first)
    _need(type(payload) is dict and set(payload) == set(initial) and payload["version"] == CHECKPOINT_VERSION
        and payload["context_sha256"] == context.root_sha256, "CHECKPOINT_HOLD: closed matching checkpoint")
    n = payload["next_index"]
    _need(type(n) is int and 0 <= n <= program["step_count"]+1, "CHECKPOINT_HOLD: next index")
    for k in ("output_cursor", "event_cursor", "forcing_cursor"):
        _need(type(payload[k]) is int, "CHECKPOINT_HOLD: integer cursor")
    forcing_count = max(1, sum(row["step_index"] < n for row in program["forcing_program"]))
    _need(payload["output_cursor"] == sum(i < n for i in program["output_steps"])
        and payload["event_cursor"] == sum(row["step_index"] < n for row in program["events"])
        and payload["forcing_cursor"] == forcing_count, "CHECKPOINT_HOLD: cursor/position mismatch")
    for kind in ("output", "event"):
        digest = payload[kind+"_prefix_sha256"]
        _need(_digest(digest), "CHECKPOINT_HOLD: prefix SHA")
        if payload[kind+"_cursor"] == 0:
            _need(digest == _hash([]), "CHECKPOINT_HOLD: empty prefix")
    if n == 0:
        _need(payload == initial, "CHECKPOINT_HOLD: original initial state required")
    last = payload["last_confirmed"]
    _need(type(last) is dict and set(last) == set(initial["last_confirmed"]), "CHECKPOINT_HOLD: closed confirmed snapshot")
    current = {**program["scenario"], **{k: last[k] for k in ("plant_state", "cohort_state", "climate_state")}}
    for key, units in (("integrated_transfers", driver.stage.FLUX_UNITS), ("event_totals", driver.EVENT_UNITS)):
        ledger = last[key]
        _need(type(ledger) is dict and set(ledger) == set(units), "CHECKPOINT_HOLD: closed ledger")
        for k, u in units.items():
            q = ledger[k]
            _need(type(q) is dict and set(q) == {"value", "unit"} and q["unit"] == u
                and type(q["value"]) is float and isfinite(q["value"]), "CHECKPOINT_HOLD: finite float64 ledger")
    try:
        for name, units, arrays in (("plant_state", driver.stage.joint.SCALAR_BLOCKS["plant_state"], False),
            ("cohort_state", driver.stage.joint.ARRAY_BLOCKS["cohort_state"], True),
            ("climate_state", driver.stage.rhs.CLIMATE_UNITS, False)):
            _, normalized = driver.stage.joint._quantities(current[name], units, arrays=arrays)
            _need(_canonical(current[name]) == _canonical(normalized), "CHECKPOINT_HOLD: canonical float64 state required")
        active = program["forcing_program"][forcing_count-1]
        result = driver.stage.rhs.evaluate_rhs(scenario=current,
            **{k: active[k] for k in driver.BOUNDARIES}, **_profiles(context))
        index = max(0, n-1); diagnostic = driver._diagnostic(current, result)
        residuals, budgets = _balances(context, program, first, current,
            last["integrated_transfers"], last["event_totals"], diagnostic, index, payload["event_cursor"])
    except (driver.previous.BoundaryHold, driver.stage.joint.JointClimateHold,
            OverflowError, ValueError, ZeroDivisionError) as exc:
        raise ContinuationRejected("CHECKPOINT_HOLD: invalid current state or global balances: "+str(exc)) from exc
    phase = "initial"
    if n and any(row["step_index"] == index for row in program["events"]): phase = "boundary-after-event"
    elif n and any(row["step_index"] == index for row in program["forcing_program"][1:]): phase = "forcing-boundary"
    elif index: phase = "step-end"
    expected = driver._snapshot(index, program["step_seconds"], diagnostic, active,
        last["integrated_transfers"], last["event_totals"], payload["event_cursor"], residuals, budgets, phase)
    _need(_canonical(last) == _canonical(expected), "CHECKPOINT_HOLD: stale state/forcing/diagnostic/phase/time/balance")
    return result


def restore_checkpoint(context, raw_bytes, *, expected_sha256):
    program, first = _context(context)
    _need(type(raw_bytes) is bytes and 0 < len(raw_bytes) <= MAX_CHECKPOINT_BYTES and _digest(expected_sha256)
        and sha256(raw_bytes).hexdigest() == expected_sha256, "CHECKPOINT_HOLD: trusted expected raw digest required")
    def pairs(rows):
        out = {}
        for k, v in rows:
            _need(k not in out, "CHECKPOINT_HOLD: duplicate JSON key"); out[k] = v
        return out
    def constant(v): raise ContinuationRejected("CHECKPOINT_HOLD: nonfinite JSON constant")
    try:
        payload = json.loads(raw_bytes.decode('utf-8'), object_pairs_hook=pairs, parse_constant=constant)
        _need(_canonical(payload) == raw_bytes, "CHECKPOINT_HOLD: canonical bytes required")
        _validate(context, payload, program, first)
    except (UnicodeError, ValueError, TypeError, KeyError, RecursionError, OverflowError) as exc:
        raise ContinuationRejected("CHECKPOINT_HOLD: invalid external checkpoint: "+str(exc)) from exc
    return _seal(context, payload)


def advance_chunk(context, checkpoint, boundary_budget):
    _need(type(boundary_budget) is int and 1 <= boundary_budget <= MAX_CHUNK_BOUNDARIES,
          "BUDGET_HOLD:1..128 boundaries")
    program, first = _context(context)
    payload = json.loads(checkpoint_bytes(context, checkpoint))
    result = _validate(context, payload, program, first)
    begin = payload["next_index"]
    _need(begin <= program["step_count"], "COMPLETED_HOLD: no boundary remains")
    confirmed = payload["last_confirmed"]
    current = {**program["scenario"], **{k: confirmed[k] for k in ("plant_state", "cohort_state", "climate_state")}}
    t, e, count = confirmed["integrated_transfers"], confirmed["event_totals"], payload["event_cursor"]
    active = program["forcing_program"][payload["forcing_cursor"]-1]
    diagnostic = driver._diagnostic(current, result)
    samples, journal, calls, held = [], [], 0, None
    index, phase = begin, "initial"
    schedule = {row["step_index"]: row["event"] for row in program["events"]}
    changes = {row["step_index"]: row for row in program["forcing_program"][1:]}
    outputs, dt, profiles = set(program["output_steps"]), program["step_seconds"], _profiles(context)
    try:
        for index in range(begin, min(begin+boundary_budget, program["step_count"]+1)):
            if index:
                phase = "interval"
                part = driver.stage.integrate(scenario=current, **{k: active[k] for k in driver.BOUNDARIES},
                    step_seconds=dt, step_count=1, **profiles)
                end = part["samples"][-1]
                candidate = {**current, **{k: end[k] for k in ("plant_state", "cohort_state", "climate_state")}}
                increments = driver.previous._add(t, part["integrated_transfers"], driver.stage.FLUX_UNITS)
                phase = "global-step-balance"
                residuals, budgets = _balances(context, program, first, candidate, increments, e, end, index, count)
                current, t, diagnostic = candidate, increments, end
                calls += part["numerical"]["coupled_rhs_evaluations"]
                confirmed = driver._snapshot(index, dt, diagnostic, active, t, e, count,
                    residuals, budgets, "step-end")
            if index in changes:
                phase = "forcing"
                changed = driver.stage.rhs.evaluate_rhs(scenario=current,
                    **{k: changes[index][k] for k in driver.BOUNDARIES}, **profiles)
                next_diagnostic = driver._diagnostic(current, changed)
                residuals, budgets = _balances(context, program, first, current, t, e, next_diagnostic, index, count)
                active = {"step_index": index, **{k: changed[k] for k in driver.BOUNDARIES}}
                diagnostic = next_diagnostic; calls += 1
                confirmed = driver._snapshot(index, dt, diagnostic, active, t, e, count,
                    residuals, budgets, "forcing-boundary")
            if index in schedule:
                phase = "event"
                applied = driver.management.apply_management(scenario=current,
                    **{k: active[k] for k in driver.BOUNDARIES}, event=schedule[index], **profiles)
                increment = {}
                for key, unit in driver.EVENT_UNITS.items():
                    quantity = applied["removed"][key]
                    increment[key] = driver.previous._q(driver.previous._sum(q["value"] for q in quantity), unit) if isinstance(quantity, list) else quantity
                candidate = applied["after"]["scenario"]
                next_diagnostic = driver._diagnostic(candidate, applied["after_rhs"])
                increments = driver.previous._add(e, increment, driver.EVENT_UNITS)
                phase = "global-event-balance"
                residuals, budgets = _balances(context, program, first, candidate, t, increments, next_diagnostic, index, count+1)
                current, e, diagnostic = candidate, increments, next_diagnostic
                count += 1; calls += 2
                confirmed = driver._snapshot(index, dt, diagnostic, active, t, e, count,
                    residuals, budgets, "boundary-after-event")
                row = {"step_index": index, "elapsed_seconds": index*dt,
                       "forcing_step_index": active["step_index"], "management": driver._journal_management(applied)}
                journal.append(row); payload["event_prefix_sha256"] = _prefix(payload["event_prefix_sha256"], row)
            if index in outputs:
                samples.append(confirmed)
                payload["output_prefix_sha256"] = _prefix(payload["output_prefix_sha256"], confirmed)
            payload.update(next_index=index+1, event_cursor=count,
                forcing_cursor=sum(row["step_index"] <= index for row in program["forcing_program"]),
                output_cursor=payload["output_cursor"]+int(index in outputs), last_confirmed=confirmed)
        next_checkpoint = _seal(context, payload)
    except (driver.previous.BoundaryHold, driver.stage.core.JointIntegrationHold, driver.management.Co2ManagementHold,
            driver.stage.joint.JointClimateHold, OverflowError, ValueError, ZeroDivisionError) as exc:
        held = {"step_index": index, "elapsed_seconds": index*dt, "phase": phase,
                "reason": str(exc), "inner_failed_stage": getattr(exc, "failed_stage", None)}
        next_checkpoint = None
    return {"status": "hold" if held else "completed" if payload["next_index"] == program["step_count"]+1 else "yielded",
        "scope": "software_research_only", "claim_scope": "synthetic_joint_co2_solar_continuation_only", "G0_G4": "not_assessed",
        "manifest": context.manifest, "context_sha256": context.root_sha256,
        "steps": confirmed["step_index"], "planned_steps": program["step_count"],
        "output_start": checkpoint.value["output_cursor"], "event_start": checkpoint.value["event_cursor"],
        "samples": deepcopy(samples), "events": deepcopy(journal), "last_confirmed": deepcopy(confirmed),
        "checkpoint": next_checkpoint, "hold": held, "confirmed_numerical_coupled_evaluations": calls,
        "checkpoint_validation_coupled_evaluations": 1}
