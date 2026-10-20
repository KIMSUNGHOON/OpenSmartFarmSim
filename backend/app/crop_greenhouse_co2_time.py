"""Exact CO2/Solar UTC labels; crop-greenhouse-co2-time-v1.md."""
from dataclasses import dataclass, field
from fractions import Fraction
from hashlib import sha256
from pathlib import Path
import json

from . import crop_greenhouse_co2_continuation as continuation
from . import crop_climate_joint_time as clock_helpers

VERSION = "joint-co2-solar-time-binding-research-v1"
TIME_RULE = clock_helpers.TIME_RULE
CODE_SHA256 = sha256(Path(__file__).read_bytes()).hexdigest()
MAX_RESULT_BYTES = 8*1024**2
_TOKEN = object()
TimeBindingRejected = clock_helpers.TimeBindingRejected
_need = clock_helpers._need
_origin, _stamp, _at, _point = clock_helpers._origin, clock_helpers._stamp, clock_helpers._at, clock_helpers._point


def _manifest(context, origin):
    try: program, _ = continuation._context(context)
    except continuation.ContinuationRejected as exc: raise TimeBindingRejected("CONTEXT_HOLD: "+str(exc)) from exc
    start = _origin(origin, program); decimal_step = str(program["step_seconds"])
    step = Fraction(decimal_step)*1_000_000
    _need(step.denominator == 1 and step > 0, "PRECISION_HOLD: exact integer microsecond step required")
    step_us = step.numerator
    return {"version": VERSION, "time_rule": TIME_RULE, "time_code_sha256": CODE_SHA256,
        "calendar_helpers_code_sha256": clock_helpers.CODE_SHA256, "context_sha256": context.root_sha256,
        "origin": origin, "start_utc": _stamp(start, step_us, 0), "end_utc": _stamp(start, step_us, program["step_count"]),
        "step_seconds_decimal": decimal_step, "step_microseconds": step_us, "step_count": program["step_count"],
        "scope": "software_research_only", "G0_G4": "not_assessed"}


@dataclass(frozen=True)
class Binding:
    _manifest: bytes = field(repr=False)
    sha256: str
    _context: continuation.Context = field(repr=False)
    _token: object = field(repr=False)

    @property
    def manifest(self): return json.loads(self._manifest)


def prepare_binding(context, *, origin):
    raw = continuation._canonical(_manifest(context, origin))
    return Binding(raw, sha256(raw).hexdigest(), context, _TOKEN)


def _binding(binding, expected_sha256=None):
    _need(type(binding) is Binding and binding._token is _TOKEN and type(binding._manifest) is bytes
        and len(binding._manifest) <= 16384, "BINDING_HOLD: prepared bounded binding required")
    if expected_sha256 is not None:
        _need(continuation._digest(expected_sha256) and expected_sha256 == binding.sha256, "BINDING_HOLD: trusted binding SHA")
    try:
        manifest = binding.manifest
        _need(sha256(binding._manifest).hexdigest() == binding.sha256
            and continuation._canonical(_manifest(binding._context, manifest["origin"])) == binding._manifest,
            "BINDING_HOLD: changed time/context/origin identity")
    except (ValueError, TypeError, KeyError, AttributeError) as exc:
        raise TimeBindingRejected("BINDING_HOLD: "+str(exc)) from exc
    return manifest, binding._context.program


def at_index(binding, index):
    manifest, _ = _binding(binding)
    return _at(manifest, index)


def _active(program, index):
    return max(row["step_index"] for row in program["forcing_program"] if row["step_index"] <= index)


def _phase(program, index):
    if any(row["step_index"] == index for row in program["events"]): return "boundary-after-event"
    if any(row["step_index"] == index for row in program["forcing_program"][1:]): return "forcing-boundary"
    return "step-end" if index else "initial"


def _frame(record, active, phase, events):
    _need(type(record.get("forcing_step_index")) is int and record["forcing_step_index"] == active
        and type(record.get("event_count")) is int and record["event_count"] == events
        and record.get("phase") == phase, "SOURCE_HOLD: active forcing/event/phase position")


def _checkpoint(binding, checkpoint, manifest, program):
    try: raw = continuation.checkpoint_bytes(binding._context, checkpoint)
    except continuation.ContinuationRejected as exc: raise TimeBindingRejected("SOURCE_HOLD: "+str(exc)) from exc
    value = json.loads(raw)
    _need(type(value) is dict and set(value) == {"version", "context_sha256", "next_index", "forcing_cursor", "output_cursor", "event_cursor",
        "output_prefix_sha256", "event_prefix_sha256", "last_confirmed"}
        and value["version"] == continuation.CHECKPOINT_VERSION and value["context_sha256"] == binding._context.root_sha256,
        "SOURCE_HOLD: closed CO2 checkpoint identity")
    n = value["next_index"]; point = _point(manifest, value["last_confirmed"], program)
    _need(type(n) is int and 0 <= n <= program["step_count"]+1 and point["step_index"] == max(0, n-1),
          "SOURCE_HOLD: checkpoint position")
    for kind, indices in (("output", program["output_steps"]), ("event", [e["step_index"] for e in program["events"]])):
        _need(type(value[kind+"_cursor"]) is int and value[kind+"_cursor"] == sum(i < n for i in indices)
            and continuation._digest(value[kind+"_prefix_sha256"]), "SOURCE_HOLD: checkpoint cursor/prefix")
        if value[kind+"_cursor"] == 0:
            _need(value[kind+"_prefix_sha256"] == continuation._hash([]), "SOURCE_HOLD: empty prefix")
    cursor = max(1, sum(row["step_index"] < n for row in program["forcing_program"]))
    _need(type(value["forcing_cursor"]) is int and value["forcing_cursor"] == cursor, "SOURCE_HOLD: forcing cursor")
    _frame(value["last_confirmed"], program["forcing_program"][cursor-1]["step_index"],
           _phase(program, point["step_index"]) if n else "initial", value["event_cursor"])
    return value, point


def _result(binding, payload):
    payload = {"version": VERSION, "binding_sha256": binding.sha256, "scope": "software_research_only", "G0_G4": "not_assessed", **payload}
    raw = continuation._canonical(payload)
    _need(len(raw)+84 <= MAX_RESULT_BYTES, "RESOURCE_HOLD: bound result byte limit")
    return {**payload, "result_sha256": sha256(raw).hexdigest()}


def bind_checkpoint(binding, checkpoint, *, expected_binding_sha256):
    _need(continuation._digest(expected_binding_sha256), "BINDING_HOLD: trusted binding SHA required")
    manifest, program = _binding(binding, expected_binding_sha256)
    value, point = _checkpoint(binding, checkpoint, manifest, program)
    return _result(binding, {"source_checkpoint_sha256": checkpoint.sha256, "source": value,
                            "time": {**point, "next_index": value["next_index"]}})


def _source(context, chunk):
    _need(type(chunk) is dict, "SOURCE_HOLD: chunk dictionary required")
    pack = dict(chunk); cp = pack.get("checkpoint")
    if cp is not None:
        try: raw = continuation.checkpoint_bytes(context, cp)
        except continuation.ContinuationRejected as exc: raise TimeBindingRejected("SOURCE_HOLD: "+str(exc)) from exc
        pack["checkpoint"] = {"sha256": cp.sha256, "value": json.loads(raw)}
    try: raw = continuation._canonical(pack)
    except (ValueError, TypeError, RecursionError) as exc: raise TimeBindingRejected("SOURCE_HOLD: canonical finite JSON required") from exc
    _need(len(raw) <= MAX_RESULT_BYTES, f"RESOURCE_HOLD: source chunk bytes {len(raw)} exceed {MAX_RESULT_BYTES}")
    return json.loads(raw), sha256(raw).hexdigest()


def source_chunk_sha256(context, chunk):
    """Producer digest only; custody authentication is a later boundary."""
    return _source(context, chunk)[1]


def bind_chunk(binding, before_checkpoint, chunk, *, expected_chunk_sha256, expected_binding_sha256):
    _need(continuation._digest(expected_binding_sha256), "BINDING_HOLD: trusted binding SHA required")
    manifest, program = _binding(binding, expected_binding_sha256)
    before, _ = _checkpoint(binding, before_checkpoint, manifest, program)
    source, digest = _source(binding._context, chunk)
    _need(continuation._digest(expected_chunk_sha256) and digest == expected_chunk_sha256,
          "SOURCE_HOLD: trusted chunk SHA required")
    keys = {"status", "scope", "claim_scope", "G0_G4", "manifest", "context_sha256", "steps", "planned_steps",
            "output_start", "event_start", "samples", "events", "last_confirmed", "checkpoint", "hold",
            "confirmed_numerical_coupled_evaluations", "checkpoint_validation_coupled_evaluations"}
    _need(set(source) == keys and source["status"] in ("yielded", "completed", "hold")
        and source["scope"] == "software_research_only" and source["claim_scope"] == "synthetic_joint_co2_solar_continuation_only"
        and source["G0_G4"] == "not_assessed" and source["context_sha256"] == binding._context.root_sha256
        and continuation._canonical(source["manifest"]) == binding._context._manifest,
        "SOURCE_HOLD: closed matching CO2 source identity")
    begin, count = before["next_index"], program["step_count"]
    _need(begin <= count and type(source["planned_steps"]) is int and source["planned_steps"] == count,
          "SOURCE_HOLD: source period")
    for kind in ("output", "event"):
        _need(type(source[kind+"_start"]) is int and source[kind+"_start"] == before[kind+"_cursor"],
              "SOURCE_HOLD: source/before cursor mismatch")
    held = source["status"] == "hold"; cp = chunk["checkpoint"]; hold = source["hold"]
    event_indices = [row["step_index"] for row in program["events"]]
    forcing_indices = [row["step_index"] for row in program["forcing_program"][1:]]
    if held:
        _need(cp is None and type(hold) is dict and set(hold) == {"step_index", "elapsed_seconds", "phase", "reason", "inner_failed_stage"}
            and hold["phase"] in ("interval", "global-step-balance", "forcing", "event", "global-event-balance")
            and type(hold["reason"]) is str and 0 < len(hold["reason"]) <= 4096
            and (hold["inner_failed_stage"] is None or type(hold["inner_failed_stage"]) is str and 0 < len(hold["inner_failed_stage"]) <= 200),
            "SOURCE_HOLD: explicit failed boundary")
        hold_point = _point(manifest, hold, program); end = hold["step_index"]; after = None
        _need((hold["phase"] != "forcing" or end in forcing_indices)
            and (hold["phase"] not in ("event", "global-event-balance") or end in event_indices)
            and (hold["phase"] not in ("interval", "global-step-balance") or end > 0),
            "SOURCE_HOLD: failure phase/schedule mismatch")
    else:
        _need(hold is None and cp is not None, "SOURCE_HOLD: checkpoint/hold status")
        after, _ = _checkpoint(binding, cp, manifest, program); end = after["next_index"]; hold_point = None
        _need((source["status"] == "completed") == (end == count+1), "SOURCE_HOLD: completion position")
    upper = min(begin+continuation.MAX_CHUNK_BOUNDARIES, count+1)
    _need(type(end) is int and begin <= end <= upper and (held or end > begin) and (not held or end < upper),
          "SOURCE_HOLD: bounded original boundary range")
    times = {}
    for key, kind, indices in (("samples", "output", program["output_steps"]), ("events", "event", event_indices)):
        rows = source[key]
        _need(type(rows) is list and len(rows) <= continuation.MAX_CHUNK_BOUNDARIES, "SOURCE_HOLD: bounded rows")
        points = [_point(manifest, row, program) for row in rows]
        _need([p["step_index"] for p in points] == [i for i in indices if begin <= i < end],
              "SOURCE_HOLD: missing/extra/out-of-order boundary records")
        prefix = before[kind+"_prefix_sha256"]
        for row, point in zip(rows, points, strict=True):
            i = point["step_index"]
            if key == "samples":
                _frame(row, _active(program, i), _phase(program, i), sum(j <= i for j in event_indices))
            else:
                _need(set(row) == {"step_index", "elapsed_seconds", "forcing_step_index", "management"}
                    and type(row["forcing_step_index"]) is int and row["forcing_step_index"] == _active(program, i)
                    and type(row["management"]) is dict, "SOURCE_HOLD: event/active forcing schema")
            prefix = continuation._prefix(prefix, row)
        if after is not None:
            _need(after[kind+"_cursor"] == before[kind+"_cursor"]+len(rows) and after[kind+"_prefix_sha256"] == prefix,
                  "SOURCE_HOLD: changed prefix/cursor")
        times[key] = points
    last = source["last_confirmed"]; point = _point(manifest, last, program)
    same_time = held and hold["phase"] in ("forcing", "event", "global-event-balance")
    expected_last = end if same_time else max(0, end-1)
    _need(point["step_index"] == expected_last and type(source["steps"]) is int and source["steps"] == expected_last,
          "SOURCE_HOLD: last confirmed position")
    active = _active(program, end-1 if held and hold["phase"] == "forcing" else expected_last)
    phase = _phase(program, expected_last)
    if held and hold["phase"] == "forcing": phase = "step-end"
    elif held and hold["phase"] in ("event", "global-event-balance"):
        phase = "forcing-boundary" if end in forcing_indices else "step-end" if end else "initial"
    _frame(last, active, phase, before["event_cursor"]+len(source["events"]))
    if after is not None:
        _need(continuation._canonical(after["last_confirmed"]) == continuation._canonical(last),
              "SOURCE_HOLD: checkpoint/last mismatch")
    steps = expected_last-max(0, begin-1)
    changes = sum(begin <= i <= active for i in forcing_indices)
    _need(type(source["confirmed_numerical_coupled_evaluations"]) is int
        and source["confirmed_numerical_coupled_evaluations"] == 5*steps+2*len(source["events"])+changes
        and type(source["checkpoint_validation_coupled_evaluations"]) is int
        and source["checkpoint_validation_coupled_evaluations"] == 1, "SOURCE_HOLD: confirmed call accounting")
    times.update(last_confirmed=point, hold=hold_point)
    return _result(binding, {"source_chunk_sha256": digest, "before_checkpoint_sha256": before_checkpoint.sha256,
                             "source": source, "times": times})
