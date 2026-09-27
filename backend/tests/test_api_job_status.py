"""The first HTTP read path stays tenant-scoped and omits private job fields."""

import asyncio
import json
from pathlib import Path
import sys
from uuid import uuid4

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.api import create_app
from app.api_contracts import public_job_status
from test_jobs import pg_store


class UnusedMarketHoldStore:
    def get_public_report(self, _tenant, _report_id):
        raise AssertionError("job status must not read a market report")


class UnusedThermalRunStore:
    def get_run(self, _tenant, _run_id):
        raise AssertionError("job status must not read a thermal Run")

    def get_snapshot(self, _tenant, _snapshot_id):
        raise AssertionError("job status must not read a thermal snapshot")


def get(app, path):
    async def call():
        sent = []
        received = False

        async def receive():
            nonlocal received
            if not received:
                received = True
                return {"type": "http.request", "body": b"", "more_body": False}
            return {"type": "http.disconnect"}

        async def send(message):
            sent.append(message)

        await app({"type": "http", "asgi": {"version": "3.0"}, "method": "GET",
                   "path": path, "raw_path": path.encode(), "root_path": "",
                   "query_string": b"", "headers": [], "http_version": "1.1",
                   "scheme": "http", "server": ("test", 80), "client": ("test", 1234)},
                  receive, send)
        status = next(item["status"] for item in sent if item["type"] == "http.response.start")
        body = b"".join(item.get("body", b"") for item in sent
                        if item["type"] == "http.response.body")
        return status, json.loads(body)

    return asyncio.run(call())


def test_job_http_status_scope_and_public_projection(pg_store):
    principal = {"authenticated": True, "tenant_id": "tenant-a", "scopes": {"metadata"}}
    app = create_app(pg_store, UnusedMarketHoldStore(), UnusedThermalRunStore(),
                     principal_provider=lambda: principal)
    job = pg_store.submit("tenant-a", "research", {"fixture": "synthetic"},
                          "api-" + uuid4().hex)
    path = f"/v1/jobs/{job['job_id']}"

    status, payload = get(app, path)
    assert status == 200
    assert set(payload) == {"job_id", "stage", "state", "attempt_count", "max_attempts",
                            "created_at", "updated_at", "reason_code"}
    assert payload["job_id"] == str(job["job_id"])
    assert payload["stage"] == "research" and payload["state"] == "queued"
    assert payload["reason_code"] is None
    assert not any(secret in json.dumps(payload) for secret in
                   ("tenant-a", "idempotency_key", "input_bytes", "input_sha256",
                    "lease_token", "fixture"))

    assert pg_store.cancel("tenant-a", job["job_id"])
    status, payload = get(app, path)
    assert status == 200 and payload["state"] == "canceled"
    assert payload["reason_code"] == "canceled_by_request"

    principal["tenant_id"] = "tenant-b"
    assert get(app, path) == (404, {"error": {"code": "not_found", "message": "Job not found"}})
    principal["tenant_id"] = "tenant-a"
    principal["scopes"] = set()
    assert get(app, path)[0] == 403
    principal["authenticated"] = False
    assert get(app, path)[0] == 401
    assert get(app, "/v1/jobs/not-a-uuid")[0] == 422

    schema = app.openapi()
    assert schema["openapi"].startswith("3.1")
    assert schema["paths"]["/v1/jobs/{job_id}"]["get"]["responses"]["200"]


def test_job_http_store_failure_is_generic_and_reason_details_are_removed(pg_store):
    principal = {"authenticated": True, "tenant_id": "tenant-a", "scopes": {"metadata"}}

    class BrokenStore:
        def get_job(self, _tenant, _job_id):
            raise RuntimeError("private database location and credential")

    app = create_app(BrokenStore(), UnusedMarketHoldStore(), UnusedThermalRunStore(),
                     principal_provider=lambda: principal)
    status, payload = get(app, f"/v1/jobs/{uuid4()}")
    assert status == 503
    assert payload == {"error": {"code": "store_unavailable",
                                 "message": "Job status unavailable"}}

    job = pg_store.submit("tenant-a", "research", {"fixture": "synthetic"},
                          "api-" + uuid4().hex)
    class ForeignStore:
        def get_job(self, _tenant, _job_id):
            return {**job, "tenant_id": "tenant-b"}

    app = create_app(ForeignStore(), UnusedMarketHoldStore(), UnusedThermalRunStore(),
                     principal_provider=lambda: principal)
    assert get(app, f"/v1/jobs/{job['job_id']}")[0] == 404

    projected = public_job_status({**job, "reason": {"code": "temporary_failure",
                                                    "last_error": "sensitive provider response"}})
    assert projected.reason_code == "temporary_failure"
    assert "sensitive provider response" not in projected.model_dump_json()
