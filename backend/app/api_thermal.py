"""Bounded, display-safe projection of an already verified synthetic thermal Run."""

from datetime import datetime, timedelta, timezone
from hashlib import sha256
import json
from math import isfinite
import re

from .api_contracts import (ThermalLawReference, ThermalManifestSource, ThermalRunManifest,
                            ThermalRunSeries, ThermalRunSummary, ThermalSeriesPoint)


RUN_ID_PATTERN = r"^synthetic-thermal-v1:[0-9a-f]{64}$"
_RUN_ID = re.compile(RUN_ID_PATTERN)
_STEP = timedelta(seconds=60)
_HOUR = timedelta(hours=1)
_DIGEST = re.compile(r"[0-9a-f]{64}\Z")
_USED = {"synthetic-weather-v1", "synthetic-thermal-parameters-v1"}


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
    if type(stored.get("release_raw")) is not bytes:
        raise ValueError("thermal display release missing")
    release = json.loads(stored["release_raw"])
    if (type(release) is not dict or
            any(release.get(key) != report.get(key) for key in
                ("snapshot_id", "manifest_sha256", "code_sha256", "environment_sha256")) or
            release.get("cleared_holds") !=
                ["NO_ENGINE_OPERATION_ORDER_REVIEW", "NO_SERVER_INPUT_LINKAGE_REVIEW"] or
            release.get("source_verdict") != "synthetic_qc_rights_and_links_checked" or
            any(type(release.get(key)) is not str or
                not _DIGEST.fullmatch(release[key])
                for key in ("weather_sha256", "thermal_sha256"))):
        raise ValueError("thermal display publisher release incomplete")
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


def project_thermal_manifest(stored, snapshot):
    """Show the original hold inventory and only source records used by this Run."""
    summary, _ = project_thermal_run(stored)
    report = stored["report"]
    if (type(snapshot) is not dict or
            snapshot.get("snapshot_id") != report.get("snapshot_id") or
            type(snapshot.get("manifest_raw")) is not bytes or
            type(snapshot.get("weather_raw")) is not bytes or
            type(snapshot.get("thermal_raw")) is not bytes or
            sha256(snapshot["manifest_raw"]).hexdigest() != report["manifest_sha256"] or
            not isinstance(stored.get("release_raw"), bytes)):
        raise ValueError("thermal display snapshot binding invalid")
    manifest = json.loads(snapshot["manifest_raw"])
    thermal = json.loads(snapshot["thermal_raw"])
    release = json.loads(stored["release_raw"])
    if (release.get("snapshot_id") != snapshot["snapshot_id"] or
            release.get("manifest_sha256") != report["manifest_sha256"] or
            release.get("weather_sha256") != sha256(snapshot["weather_raw"]).hexdigest() or
            release.get("thermal_sha256") != sha256(snapshot["thermal_raw"]).hexdigest() or
            type(manifest.get("files")) is not list or len(manifest["files"]) != 3 or
            type(manifest.get("unresolved")) is not list or
            not all(type(item) is str for item in manifest["unresolved"]) or
            type(thermal.get("law_source")) is not dict or
            thermal.get("fixture_id") != "synthetic-thermal-parameters-v1"):
        raise ValueError("thermal display manifest shape invalid")
    rows = {row["fixture_id"]: row for row in manifest["files"]}
    if (len(rows) != 3 or set(rows) != _USED | {"synthetic-economics-v1"} or
            any(type(row) is not dict or row.get("synthetic") is not True or
                type(row.get("rights")) is not dict or
                row["rights"].get("display") != "allowed"
                for row in manifest["files"]) or
            rows["synthetic-weather-v1"]["sha256"] !=
                sha256(snapshot["weather_raw"]).hexdigest() or
            rows["synthetic-thermal-parameters-v1"]["sha256"] !=
                sha256(snapshot["thermal_raw"]).hexdigest()):
        raise ValueError("thermal display source inventory invalid")
    for raw in stored["trace_raws"]:
        trace = json.loads(raw)
        seen = set()
        for source in trace["source_records"]:
            fixture_id = source["id"].split(":", 1)[0]
            if (fixture_id not in _USED or
                    source.get("raw_sha256") != rows[fixture_id]["sha256"] or
                    source.get("product_id") != rows[fixture_id]["product_id"]):
                raise ValueError("thermal display source does not bind manifest")
            seen.add(fixture_id)
        if seen != _USED:
            raise ValueError("thermal display source missing from trace")
    used_sources = []
    for fixture_id in sorted(_USED):
        row = rows[fixture_id]
        used_sources.append(ThermalManifestSource(
            fixture_id=fixture_id, product_id=row["product_id"],
            source_locator=row["source_locator"], raw_sha256=row["sha256"],
            vintage_id=row["vintage_id"], revision_id=row["revision_id"],
            available_at_utc=_utc(row["available_at_utc"]),
            retrieved_at_utc=_utc(row["retrieved_at_utc"]),
            observed_start_utc=(_utc(row["observed_start_utc"])
                                   if row["observed_start_utc"] is not None else None),
            observed_end_utc=(_utc(row["observed_end_utc"])
                                 if row["observed_end_utc"] is not None else None),
            qc_status=row["qc"]["status"], review_status=row["review"]["status"],
            display_right=row["rights"]["display"], synthetic=True,
        ))
    law = thermal["law_source"]
    rights = law["rights"]
    if (type(rights) is not dict or
            rights.get("display") != "allowed_with_conditions" or
            rights.get("status") !=
                "nws_public_domain_disclaimer_independent_cli_reviewed_conditional" or
            type(rights.get("conditions")) is not str or not rights["conditions"] or
            type(law.get("raw_pdf_sha256")) is not str or
            not _DIGEST.fullmatch(law["raw_pdf_sha256"]) or
            law.get("published_at_utc") is not None or
            law.get("available_at_utc") is not None):
        raise ValueError("thermal display law rights or vintage invalid")
    law_reference = ThermalLawReference(
        product_id=law["product_id"], source_url=law["url"],
        raw_pdf_sha256=law["raw_pdf_sha256"], published_at_utc=None,
        available_at_utc=None, retrieved_at_utc=_utc(law["retrieved_at_utc"]),
        publication_time_status=law["publication_time_status"],
        version_status=law["version_status"], rights_status=rights["status"],
        display_right=rights["display"], display_conditions=rights["conditions"],
    )
    return ThermalRunManifest(
        run_id=summary.run_id, synthetic=True,
        temporal_provenance=summary.temporal_provenance,
        snapshot_id=snapshot["snapshot_id"],
        manifest_sha256=summary.manifest_sha256,
        code_sha256=report["code_sha256"],
        environment_sha256=report["environment_sha256"],
        release_sha256=report["release_sha256"],
        trace_sha256=summary.trace_sha256,
        source_unresolved_at_creation=manifest["unresolved"],
        used_sources=used_sources,
        excluded_fixture_ids=["synthetic-economics-v1"],
        law_reference=law_reference,
    )
