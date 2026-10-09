"""HTTP admission against authenticated PG; catalog/principal are synthetic fixtures."""

import asyncio
from concurrent.futures import ThreadPoolExecutor
from dataclasses import replace
from hashlib import sha256
import json
from pathlib import Path
import sys

import pytest
from psycopg import sql

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from app.api import create_app
from app.cli_contracts import parse_stage_input
from app.job_store import JobStore
from app.orchestration import LocationRequest, LocationResearchService, ResearchScope
from login_database import login_database, login_scope
from test_api_job_status import (get, UnusedMarketHoldStore, UnusedMarketResultStore,
                                 UnusedThermalRunStore)


BODY = {"latitude": 37.5, "longitude": 127.0,
        "period_start_utc": "2026-01-01T00:00:00.123456Z",
        "period_end_utc": "2026-01-02T00:00:00Z",
        "goal_id": "historical-thermal-replay", "idempotency_key": "region-intent"}
CATALOG_HASH = sha256(b"synthetic-test-catalog-v1").hexdigest()


def post(app, value=BODY, *, raw=None, media=b"application/json", chunk_size=None):
    raw = json.dumps(value).encode() if raw is None else raw
    async def call():
        sent = []
        chunks = [raw] if chunk_size is None else [raw[i:i+chunk_size] for i in range(0, len(raw), chunk_size)]
        async def receive():
            if not chunks:
                return {"type": "http.disconnect"}
            return {"type": "http.request", "body": chunks.pop(0), "more_body": bool(chunks)}
        async def send(message):
            sent.append(message)
        await app({"type": "http", "asgi": {"version": "3.0"}, "method": "POST",
                   "path": "/v1/locations", "raw_path": b"/v1/locations", "root_path": "",
                   "query_string": b"", "headers": [(b"content-type", media)],
                   "http_version": "1.1", "scheme": "http", "server": ("test", 80),
                   "client": ("test", 1234)}, receive, send)
        status = next(item["status"] for item in sent if item["type"] == "http.response.start")
        payload = json.loads(b"".join(item.get("body", b"") for item in sent
                                      if item["type"] == "http.response.body"))
        return status, payload
    return asyncio.run(call())


@pytest.fixture
def assembly(login_scope):
    base, policy, dsns = login_scope
    principal = {"authenticated": True, "tenant_id": "tenant-a", "scopes": {"location_create", "metadata"}}
    controls = {"registry": CATALOG_HASH, "fault": None, "calls": 0}
    def resolve(tenant, body):
        controls["calls"] += 1
        scope = ResearchScope(tenant, (body.latitude, body.longitude), body.period_start_utc,
                              body.period_end_utc, body.goal_id, controls["registry"],
                              ("synthetic-provider-v1",))
        fault = controls["fault"]
        if fault == "unsupported":
            return None
        if fault == "exception":
            raise RuntimeError("private source credential and provider response")
        if fault == "tenant":
            return replace(scope, tenant_id="foreign-tenant")
        if fault == "point":
            return replace(scope, point=(0.0, 0.0))
        if fault == "providers":
            return replace(scope, provider_ids=("synthetic-provider-v1",)*2)
        if fault == "hash":
            return replace(scope, registry_sha256="not-a-raw-hash")
        return scope
    store = JobStore(dsns["authority"], policy.schema, base.artifact_root,
                     runtime_identity=(policy, "authority"), principal_provider=lambda: principal)
    service = LocationResearchService(store, resolve)
    app = create_app(store, UnusedMarketHoldStore(), UnusedThermalRunStore(),
                     UnusedMarketResultStore(), principal_provider=lambda: principal,
                     location_research_service=service)
    return app, store, base, policy, principal, controls


def rows(base):
    with base.connect() as conn:
        return conn.execute(sql.SQL("SELECT * FROM {}.jobs ORDER BY created_at").format(
            sql.Identifier(base.schema))).fetchall()


def test_location_registers_exact_immutable_research_input_and_public_status(assembly):
    app, store, base, _, _, _ = assembly
    status, reply = post(app, chunk_size=64)
    assert status == 202 and reply["spatial_support"] == "pending_research"
    assert reply["location_id"].startswith("location-v1-")
    assert reply["point"] == {"latitude": 37.5, "longitude": 127.0}
    job = rows(base)[0]
    value = parse_stage_input(job["input_bytes"], job)
    assert value["point"] == reply["point"]
    assert value["provider_ids"] == ["synthetic-provider-v1"]
    assert value["candidate_ids"] == ["synthetic-provider-v1", "research-registry-sha256:"+CATALOG_HASH]
    assert value["evidence_refs"] == []
    assert all(value[name] is None for name in ("decision_context_id", "decision_at_utc", "claim_mode", "decision_time_kind"))
    assert value["period_start_utc"] == BODY["period_start_utc"]
    assert job["stage"] == "research" and job["state"] == "queued" and job["attempt_count"] == 0
    assert job["input_sha256"] == sha256(job["input_bytes"]).hexdigest()
    assert get(app, "/v1/jobs/"+reply["research_job"]["job_id"]) == (200, reply["research_job"])
    assert all(private not in json.dumps(reply) for private in
               ("tenant-a", "input_bytes", "idempotency_key", "registry_sha256", "lease_token"))
    schema = app.openapi()["paths"]["/v1/locations"]["post"]
    request = schema["requestBody"]["content"]["application/json"]["schema"]
    assert request["additionalProperties"] is False and set(request["required"]) == set(BODY)
    assert "202" in schema["responses"] and "409" in schema["responses"]


def test_replay_and_changed_input_or_catalog_preserve_original(assembly):
    app, _, base, _, _, controls = assembly
    accepted = post(app)
    assert accepted[0] == 202 and post(app) == accepted
    assert post(app, {**BODY, "longitude": 128.0})[0] == 409
    controls["registry"] = sha256(b"synthetic-catalog-new-version").hexdigest()
    status, error = post(app)
    assert status == 409 and error["error"]["code"] == "intent_conflict"
    saved = rows(base)
    assert len(saved) == 1 and CATALOG_HASH in saved[0]["input_bytes"].decode()


def test_concurrent_http_replay_registers_one_job(assembly):
    app, _, base, _, _, _ = assembly
    with ThreadPoolExecutor(max_workers=2) as pool:
        results = list(pool.map(lambda _: post(app), range(2)))
    assert results[0][0] == 202 and results[0] == results[1]
    assert len(rows(base)) == 1


def test_same_key_isolated_between_tenants(assembly):
    app, _, base, _, principal, _ = assembly
    status, first = post(app)
    assert status == 202
    principal["tenant_id"] = "tenant-b"
    status, second = post(app)
    assert status == 202 and second["location_id"] != first["location_id"]
    assert second["research_job"]["job_id"] != first["research_job"]["job_id"]
    assert get(app, "/v1/jobs/"+first["research_job"]["job_id"])[0] == 404
    assert len(rows(base)) == 2


@pytest.mark.parametrize("fault,status", [("authentication", 401), ("scope", 403), ("store_scope", 403)])
def test_denial_precedes_lookup_and_write(assembly, fault, status):
    app, store, base, _, principal, controls = assembly
    if fault == "authentication":
        principal["authenticated"] = False
    elif fault == "scope":
        principal["scopes"] = {"metadata"}
    else:
        store.principal_provider = lambda: {**principal, "scopes": {"metadata"}}
    assert post(app)[0] == status
    assert controls["calls"] == 0 and rows(base) == []


@pytest.mark.parametrize("change", [
    {"latitude": True}, {"latitude": 91.0}, {"longitude": float("nan")},
    {"longitude": float("inf")}, {"latitude": "37.5"}, {"tenant_id": "foreign-tenant"},
    {"decision_at_utc": "2026-01-01T00:00:00Z"}, {"model": "other"}, {"G0": True},
    {"period_start_utc": "2026-02-30T00:00:00Z"},
    {"period_end_utc": BODY["period_start_utc"]},
    {"period_start_utc": "2026-01-01T00:00:00.1234567Z"}, {"idempotency_key": "bad key"},
    {"goal_id": None},
])
def test_invalid_requests_never_reach_scope_lookup_or_write(assembly, change):
    app, _, base, _, _, controls = assembly
    status, error = post(app, {**BODY, **change})
    assert status == 422 and set(error) == {"error"}
    assert controls["calls"] == 0 and rows(base) == []


@pytest.mark.parametrize("raw,media,status", [
    (b'{"latitude":0,"latitude":37.5}', b"application/json", 422),
    (b'\xffprivate-credential', b"application/json", 422),
    (b'{}', b"application/json", 422),
    (b'[]', b"application/json", 422),
    (b' ' * 4097, b"application/json", 413),
    (b'{}', b"text/plain", 415),
])
def test_bounded_closed_json_errors_hide_raw_input(assembly, raw, media, status):
    app, _, base, _, _, controls = assembly
    code, error = post(app, raw=raw, media=media, chunk_size=64)
    assert code == status and "private-credential" not in json.dumps(error)
    assert controls["calls"] == 0 and rows(base) == []


@pytest.mark.parametrize("fault,status", [("unsupported", 422), ("tenant", 503),
    ("point", 503), ("providers", 503), ("hash", 503), ("exception", 503)])
def test_unapproved_or_broken_scope_never_queues(assembly, fault, status):
    app, _, base, _, _, controls = assembly
    controls["fault"] = fault
    code, error = post(app)
    assert code == status and "private" not in json.dumps(error)
    assert rows(base) == []


def test_unconfigured_admission_remains_unavailable(assembly):
    _, store, base, _, principal, controls = assembly
    app = create_app(store, UnusedMarketHoldStore(), UnusedThermalRunStore(),
                     UnusedMarketResultStore(), principal_provider=lambda: principal)
    assert post(app)[0] == 503
    assert rows(base) == [] and controls["calls"] == 0
    with pytest.raises(ValueError, match="authenticated research authority"):
        LocationResearchService(base, lambda *_: None)


def test_actual_grant_drift_blocks_submission(assembly):
    app, _, base, policy, _, controls = assembly
    with base.connect() as conn:
        conn.execute(sql.SQL("GRANT SELECT ON {}.jobs TO {}").format(
            sql.Identifier(policy.schema), sql.Identifier(policy.roles["worker"])))
    assert post(app)[0] == 503
    assert controls["calls"] == 0 and rows(base) == []
