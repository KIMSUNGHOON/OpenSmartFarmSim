"""Only an accepted, tenant-scoped synthetic Run reaches the HTTP replay view."""

from copy import deepcopy
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.api import create_app
from test_api_job_status import get
from test_api_market_hold import UnusedJobStore
from test_thermal_run_store import (accepted_pair, packet, raw_inputs, run_store,
                                    stored_context)


class UnusedMarketHoldStore:
    def get_public_report(self, _tenant, _report_id):
        raise AssertionError("thermal Run must not read a market report")


def test_accepted_run_metadata_and_series_share_one_verified_record(run_store):
    snapshot_id = run_store.put_snapshot("tenant-a", *raw_inputs())
    context = stored_context(run_store, snapshot_id)
    traces = accepted_pair(snapshot_id, context)
    record = run_store.publish_verified("tenant-a", **packet(snapshot_id, traces, context))
    principal = {"authenticated": True, "tenant_id": "tenant-a",
                 "scopes": {"thermal_run_read"}}
    app = create_app(UnusedJobStore(), UnusedMarketHoldStore(), run_store,
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


def test_missing_candidate_or_corrupt_run_is_not_displayed(run_store):
    principal = {"authenticated": True, "tenant_id": "tenant-a",
                 "scopes": {"thermal_run_read"}}
    app = create_app(UnusedJobStore(), UnusedMarketHoldStore(), run_store,
                     principal_provider=lambda: principal)
    unknown_id = "synthetic-thermal-v1:" + "a" * 64
    assert get(app, f"/v1/runs/{unknown_id}")[0] == 404

    class CorruptStore:
        def get_run(self, _tenant, _run_id):
            raise ValueError("private release key and raw trace path")

    app = create_app(UnusedJobStore(), UnusedMarketHoldStore(), CorruptStore(),
                     principal_provider=lambda: principal)
    status, error = get(app, f"/v1/runs/{unknown_id}")
    assert status == 503
    assert error == {"error": {"code": "store_unavailable", "message": "Run unavailable"}}

    snapshot_id = run_store.put_snapshot("tenant-a", *raw_inputs())
    context = stored_context(run_store, snapshot_id)
    traces = accepted_pair(snapshot_id, context)
    record = run_store.publish_verified("tenant-a", **packet(snapshot_id, traces, context))
    stored = run_store.get_run("tenant-a", record["run_id"])
    altered = deepcopy(stored)
    first = json.loads(altered["trace_raws"][0])
    first["source_records"][0]["rights"]["display"] = "denied"
    altered["trace_raws"] = (json.dumps(first).encode(), altered["trace_raws"][1])

    class DeniedDisplayStore:
        def get_run(self, _tenant, _run_id):
            return altered

    app = create_app(UnusedJobStore(), UnusedMarketHoldStore(), DeniedDisplayStore(),
                     principal_provider=lambda: principal)
    assert get(app, f"/v1/runs/{record['run_id']}")[0] == 503
