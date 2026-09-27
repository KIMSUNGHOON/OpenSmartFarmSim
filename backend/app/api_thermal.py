"""Bounded, display-safe projection of an already verified synthetic thermal Run."""

from datetime import datetime, timedelta, timezone
import json
from math import isfinite
import re

from .api_contracts import ThermalRunSeries, ThermalRunSummary, ThermalSeriesPoint


RUN_ID_PATTERN = r"^synthetic-thermal-v1:[0-9a-f]{64}$"
_RUN_ID = re.compile(RUN_ID_PATTERN)
_STEP = timedelta(seconds=60)
_HOUR = timedelta(hours=1)


def _utc(value):
    if type(value) is not str or not value.endswith("Z"):
        raise ValueError("thermal display time invalid")
    try:
        parsed = datetime.fromisoformat(value[:-1] + "+00:00")
    except ValueError as exc:
        raise ValueError("thermal display time invalid") from exc
    if parsed.tzinfo != timezone.utc:
        raise ValueError("thermal display time invalid")
    return parsed


def _number(record, unit, *, minimum=None, maximum=None):
    if (type(record) is not dict or record.get("unit") != unit or
            type(record.get("value")) not in (int, float) or
            not isfinite(record["value"]) or
            (minimum is not None and record["value"] < minimum) or
            (maximum is not None and record["value"] > maximum)):
        raise ValueError("thermal display value invalid")
    return float(record["value"])


def project_thermal_run(stored):
    """Select display values only after the run store has verified signed bytes."""
    if (type(stored) is not dict or type(stored.get("run_id")) is not str or
            not _RUN_ID.fullmatch(stored["run_id"]) or
            type(stored.get("report")) is not dict or
            type(stored.get("trace_raws")) not in (tuple, list) or
            len(stored["trace_raws"]) != 2):
        raise ValueError("thermal display Run invalid")
    report = stored["report"]
    if (report.get("run_id") != stored["run_id"] or
            report.get("claim_mode") != "ex_post_replay" or
            report.get("status") != "pass" or
            type(report.get("trace_sha256")) is not list or
            len(report["trace_sha256"]) != 2):
        raise ValueError("thermal display gate invalid")
    traces = [json.loads(raw) for raw in stored["trace_raws"]]
    points = []
    previous_end = None
    for index, trace in enumerate(traces):
        if (type(trace) is not dict or trace.get("run_id") != stored["run_id"] or
                trace.get("run_status") != "accepted" or
                trace.get("trace_sequence_index") != index or
                trace.get("model_origin") != "project_aggregate_v1" or
                trace.get("claim_scope") != "synthetic_g1_contract_trace" or
                trace.get("claim_mode") != "ex_post_replay" or
                trace.get("model_version") != "thermal-v1" or
                trace.get("parameter_set_version") != "synthetic-thermal-parameters-v1" or
                trace.get("engine_version") != "thermal-euler-v1" or
                trace.get("unit_registry_version") != "thermal-si-nws-v1" or
                trace.get("manifest_sha256") != report.get("manifest_sha256") or
                type(trace.get("source_records")) is not list or
                not trace["source_records"] or
                any(type(source) is not dict or source.get("synthetic") is not True or
                    type(source.get("rights")) is not dict or
                    source["rights"].get("display") != "allowed"
                    for source in trace["source_records"])):
            raise ValueError("thermal display source or trace scope invalid")
        interval = trace["interval"]
        start, end = _utc(interval["start_utc"]), _utc(interval["end_utc"])
        if end - start != _HOUR or (previous_end is not None and start != previous_end):
            raise ValueError("thermal display interval invalid")
        previous_end = end
        steps = trace["steps"]
        if type(steps) is not list or len(steps) != 60:
            raise ValueError("thermal display step count invalid")
        cursor = start
        for step in steps:
            at_start, at_end = _utc(step["start_utc"]), _utc(step["end_utc"])
            if at_start != cursor or at_end - at_start != _STEP:
                raise ValueError("thermal display step time invalid")
            cursor = at_end
            points.append(ThermalSeriesPoint(
                at_utc=at_end,
                temperature_k=_number(step["state_end"]["temperature"], "K", minimum=0),
                humidity_ratio_kg_v_per_kg_da=_number(
                    step["state_end"]["humidity_ratio"], "kg_v/kg_da", minimum=0),
                relative_humidity_fraction=_number(step["relative_humidity_end"], "1",
                                                   minimum=0, maximum=1),
                heat_demand_w_th=_number(step["heat_demand"], "W_th", minimum=0),
                heat_delivered_w_th=_number(step["heat_delivered"], "W_th", minimum=0),
                delivered_heat_energy_kwh_th=_number(
                    step["delivered_heat_energy"], "kWh_th", minimum=0),
            ))
        if cursor != end:
            raise ValueError("thermal display interval steps differ")
    summary = ThermalRunSummary(
        run_id=stored["run_id"], status="accepted", synthetic=True,
        temporal_provenance="ex_post_replay",
        decision_at_utc=_utc(report["decision_at_utc"]),
        review_at_utc=_utc(report["review_at_utc"]),
        start_utc=_utc(traces[0]["interval"]["start_utc"]),
        end_utc=previous_end, model_version="thermal-v1",
        parameter_set_version="synthetic-thermal-parameters-v1",
        engine_version="thermal-euler-v1", unit_registry_version="thermal-si-nws-v1",
        manifest_sha256=report["manifest_sha256"], trace_sha256=report["trace_sha256"],
        point_count=len(points),
    )
    return summary, ThermalRunSeries(run_id=stored["run_id"],
                                     temporal_provenance="ex_post_replay", points=points)
