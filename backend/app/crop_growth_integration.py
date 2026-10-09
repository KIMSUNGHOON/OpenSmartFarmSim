"""Bounded research integration of pinned crop rates; no approved Run publication."""
from datetime import datetime, timedelta
from fractions import Fraction
from hashlib import sha256
import json
from math import fsum, isfinite, ulp
from pathlib import Path
import platform
import re

from . import crop_growth_rates as rates


INTEGRATOR_VERSION = "crop-rk4-research-v1"
DOMAIN_POLICY = "vanthoor-bounded-photosynthesis-v1"
STATE = tuple(rates.STATE_UNITS)
FLUX = ("photosynthesis", "growth_respiration", "maintenance_leaf", "maintenance_stem_root",
        "maintenance_fruit", "removal_leaf", "removal_stem_root", "removal_fruit")
ORGANS = ("leaf", "stem_root", "fruit")
EVENT_UNITS = {organ: rates.MASS_UNIT for organ in ORGANS}
CODE_HASHES = {"integrator": sha256(Path(__file__).read_bytes()).hexdigest(),
               "rates": sha256(Path(rates.__file__).read_bytes()).hexdigest()}


class CropIntegrationHold(ValueError):
    """Malformed or unbounded program rejected before equation evaluation."""


class _EvaluationHold(Exception):
    def __init__(self, reason, at, phase, state):
        self.reason, self.at, self.phase, self.state = reason, at, phase, list(state)


def _need(condition, reason):
    if not condition:
        raise CropIntegrationHold(reason)


def _utc(value):
    _need(type(value) is str and re.fullmatch(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z", value),
          "TIME_HOLD: canonical whole-second UTC required")
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise CropIntegrationHold("TIME_HOLD: invalid UTC") from exc


def _stamp(at):
    return at.isoformat().replace("+00:00", "Z")


def _hash(document):
    return sha256(json.dumps(document, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()).hexdigest()


def _block(block, units):
    try:
        return rates._block(block, units)
    except rates.CropRateHold as exc:
        raise CropIntegrationHold(str(exc)) from exc


def _prepare(initial_state, segments, events, output_times, profile, solver):
    _need(type(profile) is rates.ReferenceParameters, "PROFILE_HOLD: pinned reference required")
    for records in (segments, events, output_times):
        _need(type(records) is list and len(records) <= 20000, "RESOURCE_HOLD: bounded lists required")
    _need(bool(segments) and len(output_times) >= 2, "INPUT_HOLD: full period and output endpoints required")
    _need(type(solver) is dict and set(solver) == {"method", "max_step_seconds", "max_steps", "roundoff_rule"}
          and solver["method"] == "rk4-fixed-v1" and solver["roundoff_rule"] == "64-ulp-per-operation-v1",
          "SOLVER_HOLD: closed pinned solver required")
    _need(type(solver["max_step_seconds"]) is int and 1 <= solver["max_step_seconds"] <= 86400
          and type(solver["max_steps"]) is int and 1 <= solver["max_steps"] <= 1000000,
          "RESOURCE_HOLD: explicit positive integer budgets required")
    initial, normalized_initial = _block(initial_state, rates.STATE_UNITS)
    normalized_segments = []
    previous_end = None
    for segment in segments:
        _need(type(segment) is dict and set(segment) == {"start", "end", "forcing", "removals"},
              "INPUT_HOLD: closed forcing interval required")
        start, end = _utc(segment["start"]), _utc(segment["end"])
        _need(start < end and (previous_end is None or start == previous_end), "TIME_HOLD: noncontinuous intervals")
        _, forcing = _block(segment["forcing"], rates.FORCING_UNITS)
        _, removal = _block(segment["removals"], rates.REMOVAL_UNITS)
        normalized_segments.append({"start": segment["start"], "end": segment["end"],
                                    "forcing": forcing, "removals": removal})
        previous_end = end
    begin, finish = _utc(segments[0]["start"]), previous_end
    outputs = [_utc(t) for t in output_times]
    _need(outputs[0] == begin and outputs[-1] == finish and all(a < b for a, b in zip(outputs, outputs[1:])),
          "TIME_HOLD: ordered outputs must cover exact period")
    normalized_events = []; event_times = []
    for event in events:
        _need(type(event) is dict and set(event) == {"at", "removals"}, "INPUT_HOLD: closed removal event required")
        at = _utc(event["at"])
        _need(begin <= at <= finish and (not event_times or at > event_times[-1]), "TIME_HOLD: unordered or external event")
        _, removal = _block(event["removals"], EVENT_UNITS)
        normalized_events.append({"at": event["at"], "removals": removal}); event_times.append(at)
    boundaries = sorted(set(outputs + event_times + [_utc(s["end"]) for s in normalized_segments]))
    needed = sum((int((b-a).total_seconds())+solver["max_step_seconds"]-1)//solver["max_step_seconds"]
                 for a, b in zip(boundaries, boundaries[1:]))
    _need(needed <= solver["max_steps"], "RESOURCE_HOLD: planned steps exceed explicit budget")
    normalized = {"initial_state": normalized_initial, "segments": normalized_segments, "events": normalized_events,
                  "output_times": list(output_times), "solver": dict(solver)}
    return initial, normalized, boundaries, needed


def _state_record(y):
    return {k: {"value": value if isfinite(value) else None, "unit": rates.STATE_UNITS[k]}
            for k, value in zip(STATE, y[:6])}


def _guard(y, at, phase):
    if not all(isfinite(v) for v in y):
        raise _EvaluationHold("NUMERIC_HOLD: nonfinite state or accumulation", at, phase, y)
    if any(v < 0 for v in y):
        raise _EvaluationHold("DEPLETED_STATE_HOLD: negative trial state or accumulation", at, phase, y)


def _ledger(y, initial, operations, at):
    try:
        start_total, current_total = fsum(initial[:4]), fsum(y[:4])
        residual = fsum((*y[:4], *[-v for v in initial[:4]], -y[6], *y[7:]))
        scale = max(1.0, abs(start_total), abs(current_total), *map(abs, y[6:]))
        budget = 64 * (operations + 1) * ulp(scale)
    except (OverflowError, ValueError) as exc:
        raise _EvaluationHold("NUMERIC_HOLD: carbon balance overflow", at, "balance", y) from exc
    if not isfinite(residual) or abs(residual) > budget:
        raise _EvaluationHold("BALANCE_HOLD: unresolved accumulated carbon residual", at, "balance", y)
    return residual, budget


def integrate_crop(*, initial_state, segments, events, output_times, profile, solver):
    """Integrate declared research inputs or return a hold with solver diagnostics."""
    initial, program, boundaries, planned = _prepare(initial_state, segments, events, output_times, profile, solver)
    manifest = {"integrator_version": INTEGRATOR_VERSION, "rate_model_version": rates.MODEL_VERSION,
                "domain_policy": DOMAIN_POLICY, "profile_id": profile.profile_id, "profile_sha256": profile.sha256,
                "code_sha256": dict(CODE_HASHES), "solver": program["solver"], "time_rule": "UTC_POSIX_whole_seconds_v1",
                "python_version": platform.python_version(), "convergence": "not_evaluated_for_this_program",
                "temperature_sum_method": "analytic_piecewise_constant_fraction_v1"}
    manifest["input_sha256"] = _hash({"program": program, "integrator_version": INTEGRATOR_VERSION,
                                     "rate_model_version": rates.MODEL_VERSION, "domain_policy": DOMAIN_POLICY,
                                     "profile_sha256": profile.sha256, "code_sha256": CODE_HASHES})
    blocks = [program["initial_state"]] + [b for s in program["segments"] for b in (s["forcing"], s["removals"])]
    blocks += [e["removals"] for e in program["events"]]
    manifest["origins"] = sorted({b["origin"] for b in blocks})
    manifest["input_ids"] = [b["input_id"] for b in blocks]
    y = [initial[k] for k in STATE] + [0.0] * len(FLUX); seed = list(y)
    at = boundaries[0]; active = 0; steps = 0; event_count = 0; last_confirmed = None
    frames = []; journal = []; events_by_time = {_utc(e["at"]): e for e in program["events"]}
    requested = set(program["output_times"])
    temperature_clocks = []
    running_sum = Fraction.from_float(initial["temperature_sum"])
    for segment in program["segments"]:
        begin, finish = _utc(segment["start"]), _utc(segment["end"])
        slope = Fraction.from_float(segment["forcing"]["values"]["canopy_temperature"]["value"]) / Fraction.from_float(profile.values["seconds_per_day"])
        temperature_clocks.append((begin, running_sum, slope))
        running_sum += slope * int((finish-begin).total_seconds())

    def clock_state(vector, time, phase):
        vector = list(vector)
        begin, prefix, slope = temperature_clocks[active]
        try:
            vector[5] = float(prefix + slope * Fraction.from_float((time-begin).total_seconds()))
        except OverflowError as exc:
            raise _EvaluationHold("NUMERIC_HOLD: temperature sum overflow", time, phase, vector) from exc
        return vector

    def rhs(vector, time, phase):
        vector = clock_state(vector, time, phase)
        _guard(vector, time, phase)
        state = {"input_id": program["initial_state"]["input_id"] + ":calculated", "origin": "reference_calculation",
                 "values": {k: {"value": v, "unit": rates.STATE_UNITS[k]} for k, v in zip(STATE, vector[:6])}}
        segment = program["segments"][active]
        try:
            result = rates.calculate_rates(state=state, forcing=segment["forcing"],
                                           removals=segment["removals"], profile=profile)
        except rates.CropRateHold as exc:
            raise _EvaluationHold(str(exc), time, phase, vector) from exc
        return ([result["derivatives"][k]["value"] for k in STATE] +
                [result["photosynthesis"]["value"], result["growth_respiration"]["value"]] +
                [result["maintenance_respiration"][k]["value"] for k in ORGANS] +
                [result["removals"][k]["value"] for k in ORGANS])

    def snapshot(vector, time):
        residual, budget = _ledger(vector, seed, steps + event_count, time)
        return {"at": _stamp(time), "state": _state_record(vector),
                "lai": {"value": profile.values["sla"] * vector[1], "unit": "m2_leaf/m2_floor"},
                "cumulative": {k: {"value": v, "unit": rates.MASS_UNIT} for k, v in zip(FLUX, vector[6:])},
                "carbon_residual": {"value": residual, "unit": rates.MASS_UNIT},
                "carbon_residual_budget": {"value": budget, "unit": rates.MASS_UNIT}}

    try:
        for boundary in boundaries:
            while at < boundary:
                h = min(program["solver"]["max_step_seconds"], int((boundary-at).total_seconds()))
                half = at + timedelta(seconds=h/2); end = at + timedelta(seconds=h)
                k1 = rhs(y, at, "rk4-k1")
                k2 = rhs([v+h*d/2 for v, d in zip(y, k1)], half, "rk4-k2")
                k3 = rhs([v+h*d/2 for v, d in zip(y, k2)], half, "rk4-k3")
                k4 = rhs([v+h*d for v, d in zip(y, k3)], end, "rk4-k4")
                try:
                    candidate = [fsum((v, h*fsum((a, 2*b, 2*c, d))/6)) for v, a, b, c, d in zip(y, k1, k2, k3, k4)]
                except (OverflowError, ValueError) as exc:
                    raise _EvaluationHold("NUMERIC_HOLD: RK4 update failed", end, "step-end-arithmetic", y) from exc
                candidate = clock_state(candidate, end, "step-end")
                rhs(candidate, end, "step-end")
                _ledger(candidate, seed, steps+event_count+1, end)
                y, at = candidate, end; steps += 1
                last_confirmed = {**snapshot(y, at), "phase": "step-end",
                                  "forcing_input_id": program["segments"][active]["forcing"]["input_id"]}
            if active+1 < len(program["segments"]) and at == _utc(program["segments"][active]["end"]):
                active += 1
            candidate = list(y); event = events_by_time.get(at)
            if event:
                removed = event["removals"]["values"]
                if any(removed[k]["value"] > candidate[STATE.index(k)] for k in ORGANS):
                    raise _EvaluationHold("REMOVAL_EXCEEDS_STORAGE_HOLD: explicit event exceeds state", at, "event", candidate)
                for k in ORGANS:
                    candidate[STATE.index(k)] -= removed[k]["value"]
                    candidate[6+FLUX.index("removal_"+k)] += removed[k]["value"]
            rhs(candidate, at, "boundary-after-event" if event else "boundary")
            _ledger(candidate, seed, steps+event_count+bool(event), at)
            if event:
                journal.append({"at": _stamp(at), "input_id": event["removals"]["input_id"],
                                "removals": event["removals"]["values"], "before": _state_record(y), "after": _state_record(candidate)})
                event_count += 1
            y = candidate
            last_confirmed = {**snapshot(y, at), "phase": "boundary-after-event" if event else "boundary",
                              "forcing_input_id": program["segments"][active]["forcing"]["input_id"]}
            if _stamp(at) in requested:
                frames.append(snapshot(y, at))
        result = {"status": "completed", "scope": "software_research_only", "manifest": manifest,
                  "steps": steps, "planned_steps": planned, "samples": frames, "events": journal}
    except _EvaluationHold as exc:
        result = {"status": "hold", "scope": "software_research_only", "manifest": manifest,
                  "steps": steps, "planned_steps": planned, "samples": [], "events": [],
                  "hold": {"reason": exc.reason, "attempted_at": _stamp(exc.at), "phase": exc.phase,
                           "time_meaning": "solver_evaluation_time", "last_confirmed": last_confirmed,
                           "failed_state": _state_record(exc.state)}}
    except (OverflowError, ValueError) as exc:
        result = {"status": "hold", "scope": "software_research_only", "manifest": manifest,
                  "steps": steps, "planned_steps": planned, "samples": [], "events": [],
                  "hold": {"reason": "NUMERIC_HOLD: integration arithmetic failed", "attempted_at": _stamp(at),
                           "phase": "arithmetic", "time_meaning": "solver_evaluation_time",
                           "last_confirmed": last_confirmed, "failed_state": _state_record(y)}}
    result["result_sha256"] = _hash(result)
    return result
