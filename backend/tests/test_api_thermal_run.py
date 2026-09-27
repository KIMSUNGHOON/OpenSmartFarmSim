"""Only an accepted, tenant-scoped synthetic Run reaches the HTTP replay view."""

from copy import deepcopy
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.api import create_app
from app.api_thermal import project_thermal_manifest
from test_api_job_status import get, UnusedMarketResultStore
from test_api_market_hold import UnusedJobStore
from test_jobs import pg_store
from test_thermal_publisher import setup as publisher_setup
from test_thermal_run_store import (accepted_pair, packet, raw_inputs, run_store,
                                    stored_context)


class UnusedMarketHoldStore:
    def get_public_report(self, _tenant, _report_id):
        raise AssertionError("thermal Run must not read a market report")


def test_accepted_run_metadata_and_series_share_one_verified_record(publisher_setup):
    publisher, run_store, _, job, snapshot_id, _, _, _ = publisher_setup
    record = publisher.publish("tenant-a", job["job_id"], snapshot_id)
    traces = run_store.get_run("tenant-a", record["run_id"])["trace_raws"]
    principal = {"authenticated": True, "tenant_id": "tenant-a",
                 "scopes": {"thermal_run_read"}}
    app = create_app(UnusedJobStore(), UnusedMarketHoldStore(), run_store,
                     UnusedMarketResultStore(),
                     principal_provider=lambda: principal)
    path = f"/v1/runs/{record['run_id']}"

    status, summary = get(app, path)
    assert status == 200
    assert summary["run_id"] == record["run_id"]
    assert summary["status"] == "accepted"
    assert summary["synthetic"] is True
    assert summary["temporal_provenance"] == "ex_post_replay"
    assert summary["point_count"] == 120
    assert summary["trace_sha256"] == list(record["trace_sha256"])
    assert all(key not in summary for key in
               ("tenant_id", "report_raw", "release_raw", "gate_signature",
                "source_records", "context_raw"))

    status, series = get(app, path + "/series")
    assert status == 200
    assert series["run_id"] == summary["run_id"]
    assert series["temporal_provenance"] == summary["temporal_provenance"]
    assert len(series["points"]) == summary["point_count"]
    first_trace, second_trace = (json.loads(raw) for raw in traces)
    first = series["points"][0]
    last = series["points"][-1]
    assert first["temperature_k"] == first_trace["steps"][0]["state_end"]["temperature"]["value"]
    assert last["temperature_k"] == second_trace["steps"][-1]["state_end"]["temperature"]["value"]
    assert last["at_utc"].replace("+00:00", "Z") == summary["end_utc"].replace("+00:00", "Z")
    assert all(key not in first for key in ("source_records", "forcing", "heater", "parameters"))

    principal["scopes"].add("thermal_snapshot_read")
    stored = run_store.get_run("tenant-a", record["run_id"])
    snapshot = run_store.get_snapshot("tenant-a", stored["report"]["snapshot_id"])
    project_thermal_manifest(stored, snapshot)
    status, manifest = get(app, path + "/manifest")
    assert status == 200
    assert manifest["run_id"] == summary["run_id"]
    assert manifest["manifest_sha256"] == summary["manifest_sha256"]
    assert manifest["trace_sha256"] == summary["trace_sha256"]
    assert {source["fixture_id"] for source in manifest["used_sources"]} == {
        "synthetic-weather-v1", "synthetic-thermal-parameters-v1"}
    assert manifest["excluded_fixture_ids"] == ["synthetic-economics-v1"]
    assert "NO_REAL_SOURCE_G0" in manifest["source_unresolved_at_creation"]
    assert "NO_ACCEPTED_THERMAL_RUN" in manifest["source_unresolved_at_creation"]
    assert manifest["law_reference"]["available_at_utc"] is None
    assert manifest["law_reference"]["published_at_utc"] is None
    assert manifest["law_reference"]["display_right"] == "allowed_with_conditions"
    assert all(key not in manifest for key in
               ("manifest_raw", "thermal_raw", "weather_raw", "release_raw", "gate_signature"))
    principal["scopes"].remove("thermal_snapshot_read")
    assert get(app, path + "/manifest")[0] == 403

    principal["tenant_id"] = "tenant-b"
    assert get(app, path)[0] == 404
    principal["tenant_id"] = "tenant-a"
    principal["scopes"].clear()
    assert get(app, path)[0] == 403
    principal["authenticated"] = False
    assert get(app, path)[0] == 401
    assert get(app, "/v1/runs/not-a-run")[0] == 422

    schema = app.openapi()
    assert schema["paths"]["/v1/runs/{run_id}"]["get"]["responses"]["200"]
    assert schema["paths"]["/v1/runs/{run_id}/series"]["get"]["responses"]["200"]
    assert schema["paths"]["/v1/runs/{run_id}/manifest"]["get"]["responses"]["200"]


def test_missing_candidate_or_corrupt_run_is_not_displayed(publisher_setup):
    publisher, run_store, _, job, snapshot_id, _, _, _ = publisher_setup
    principal = {"authenticated": True, "tenant_id": "tenant-a",
                 "scopes": {"thermal_run_read"}}
    app = create_app(UnusedJobStore(), UnusedMarketHoldStore(), run_store,
                     UnusedMarketResultStore(),
                     principal_provider=lambda: principal)
    unknown_id = "synthetic-thermal-v1:" + "a" * 64
    assert get(app, f"/v1/runs/{unknown_id}")[0] == 404

    class CorruptStore:
        def get_run(self, _tenant, _run_id):
            raise ValueError("private release key and raw trace path")

        def get_snapshot(self, _tenant, _snapshot_id):
            raise AssertionError("corrupt Run must not read snapshot")

    app = create_app(UnusedJobStore(), UnusedMarketHoldStore(), CorruptStore(),
                     UnusedMarketResultStore(),
                     principal_provider=lambda: principal)
    status, error = get(app, f"/v1/runs/{unknown_id}")
    assert status == 503
    assert error == {"error": {"code": "store_unavailable", "message": "Run unavailable"}}

    record = publisher.publish("tenant-a", job["job_id"], snapshot_id)
    stored = run_store.get_run("tenant-a", record["run_id"])
    altered = deepcopy(stored)
    first = json.loads(altered["trace_raws"][0])
    first["source_records"][0]["rights"]["display"] = "denied"
    altered["trace_raws"] = (json.dumps(first).encode(), altered["trace_raws"][1])

    class DeniedDisplayStore:
        def get_run(self, _tenant, _run_id):
            return altered

        def get_snapshot(self, _tenant, _snapshot_id):
            raise AssertionError("denied Run must not read snapshot")

    app = create_app(UnusedJobStore(), UnusedMarketHoldStore(), DeniedDisplayStore(),
                     UnusedMarketResultStore(),
                     principal_provider=lambda: principal)
    assert get(app, f"/v1/runs/{record['run_id']}")[0] == 503

    wrong_snapshot = deepcopy(run_store.get_snapshot("tenant-a", stored["report"]["snapshot_id"]))
    wrong_snapshot["weather_raw"] = b"changed synthetic weather"

    class WrongSnapshotStore:
        def get_run(self, _tenant, _run_id):
            return stored

        def get_snapshot(self, _tenant, _snapshot_id):
            return wrong_snapshot

    principal["scopes"].add("thermal_snapshot_read")
    app = create_app(UnusedJobStore(), UnusedMarketHoldStore(), WrongSnapshotStore(),
                     UnusedMarketResultStore(),
                     principal_provider=lambda: principal)
    assert get(app, f"/v1/runs/{record['run_id']}/manifest")[0] == 503


def test_store_only_packet_without_full_publisher_release_is_not_public(run_store):
    snapshot_id = run_store.put_snapshot("tenant-a", *raw_inputs())
    context = stored_context(run_store, snapshot_id)
    traces = accepted_pair(snapshot_id, context)
    record = run_store.publish_verified("tenant-a", **packet(snapshot_id, traces, context))
    principal = {"authenticated": True, "tenant_id": "tenant-a",
                 "scopes": {"thermal_run_read", "thermal_snapshot_read"}}
    app = create_app(UnusedJobStore(), UnusedMarketHoldStore(), run_store,
                     UnusedMarketResultStore(),
                     principal_provider=lambda: principal)
    path = f"/v1/runs/{record['run_id']}"
    assert get(app, path)[0] == 503
    assert get(app, path + "/series")[0] == 503
    assert get(app, path + "/manifest")[0] == 503
