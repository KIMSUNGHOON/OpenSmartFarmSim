"""Private validated hold artifacts projected through authenticated tenant reads."""

from dataclasses import replace
import json
import os
from pathlib import Path
import sys
from uuid import uuid4

import pytest
from psycopg import sql

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from app.api import create_app
from app.cli_contracts import DecisionContract, _canonical
from app.cli_worker import CliWorker
from app.orchestration import LocationResearchService
from test_api_location_research import (assembly, login_database, login_scope, post,
    UnusedMarketHoldStore, UnusedThermalRunStore, UnusedMarketResultStore)
from test_api_job_status import get
from test_research_registry import registry, queued_input
from test_cli_contracts import input_for, resolver
from test_cli_worker import _fake_cli
from test_job_evidence import cli_store


def application(store, principal, catalog):
    return create_app(store, UnusedMarketHoldStore(), UnusedThermalRunStore(),
        UnusedMarketResultStore(), principal_provider=lambda: principal,
        location_research_service=LocationResearchService(store, catalog.scope_for_location))


@pytest.fixture
def held_case(assembly, request, tmp_path):
    _, store, base, _, principal, _ = assembly
    settings = getattr(request, "param", {})
    stage = settings.get("stage", "research")
    catalog = registry()
    initial = catalog.authority_snapshot if stage == "research" else resolver
    def authority(job, value):
        snapshot = initial(job, value)
        return replace(snapshot, missing_evidence=settings["missing"]) if "missing" in settings else snapshot
    contract = DecisionContract(authority)
    store.decision_validator, store.evidence_policy = contract, cli_store(store).evidence_policy
    principal["scopes"].update({"artifact", "auditor"})
    app = application(store, principal, catalog)
    if stage == "research":
        status, accepted = post(app)
        assert status == 202
        job_id = accepted["research_job"]["job_id"]
    else:
        job_id = str(store.submit("tenant-a", stage, input_for(stage), uuid4().hex)["job_id"])
    home = tmp_path / "synthetic-home"
    home.mkdir(mode=0o700)
    worker = CliWorker(store, contract, cli_path=_fake_cli(tmp_path), codex_home=home,
        child_env={"CODEX_API_KEY": "synthetic-test-key"}, timeout_seconds=5,
        lease_seconds=15, synthetic_smoke=True)
    assert worker.run_once().state == "hold"
    return app, store, base, principal, catalog, job_id, "/v1/jobs/"+job_id+"/hold-report"


@pytest.mark.parametrize("held_case", [{"stage": stage} for stage in
    ("research", "collection_review", "assessment")], indirect=True)
def test_validated_hold_is_persistent_safe_and_distinct_from_job_status(held_case):
    app, store, _, principal, catalog, job_id, path = held_case
    status, reply = get(app, path)
    assert status == 200 and reply["status"] == "hold" and reply["job_id"] == job_id
    assert set(reply) == {"job_id", "stage", "hold_id", "status", "recorded_at", "reason_code",
                          "missing_evidence", "missing_evidence_count"}
    assert reply["reason_code"] == "evidence_missing"
    expected = (["research_source_evidence", "signed_decision_context"] if reply["stage"] == "research"
                else ["real_source_g0"])
    assert reply["missing_evidence"] == expected and reply["missing_evidence_count"] == len(expected)
    assert get(app, "/v1/jobs/"+job_id)[1]["reason_code"] == "ai_validated_hold"
    assert get(application(store, principal, catalog), path) == (200, reply)
    assert all(private not in json.dumps(reply) for private in
               ("tenant-a", "decision_id", "receipt_id", "attempt_id", "input_sha256",
                "Synthetic evidence", "lease_token", "report_sha256"))
    schema = app.openapi()["paths"]["/v1/jobs/{job_id}/hold-report"]["get"]
    assert schema["responses"]["200"]["content"]["application/json"]["schema"]["$ref"].endswith("/JobHoldStatus")


@pytest.mark.parametrize("held_case", [{"missing": ("research_source_evidence", "synthetic_private_record_A",
    "synthetic_private_record_B", "signed_decision_context")}], indirect=True)
def test_private_missing_identifiers_collapse_to_categories(held_case):
    app, _, _, _, _, _, path = held_case
    status, reply = get(app, path)
    assert status == 200 and reply["missing_evidence_count"] == 4
    assert reply["missing_evidence"] == ["research_source_evidence", "other_evidence", "signed_decision_context"]
    assert "synthetic_private_record" not in json.dumps(reply)


@pytest.mark.parametrize("held_case", [{"missing": ()}], indirect=True)
def test_decision_hold_without_missing_evidence_stays_a_hold(held_case):
    app, _, _, _, _, _, path = held_case
    status, reply = get(app, path)
    assert status == 200 and reply["reason_code"] == "decision_held"
    assert reply["missing_evidence"] == [] and reply["missing_evidence_count"] == 0


@pytest.mark.parametrize("scope", ["metadata", "artifact", "auditor"])
def test_missing_scope_denies_before_artifact_read(held_case, monkeypatch, scope):
    app, store, _, principal, _, _, path = held_case
    principal["scopes"].remove(scope)
    def forbidden(*_):
        raise AssertionError("denied caller read private artifact")
    monkeypatch.setattr(store, "read_hold_report", forbidden)
    assert get(app, path)[0] == 403


def test_authentication_and_tenant_and_missing_or_queued_jobs(held_case):
    app, store, _, principal, _, _, path = held_case
    principal["authenticated"] = False
    assert get(app, path)[0] == 401
    principal["authenticated"] = True
    principal["tenant_id"] = "tenant-b"
    assert get(app, path)[0] == 404
    principal["tenant_id"] = "tenant-a"
    assert get(app, "/v1/jobs/not-a-uuid/hold-report")[0] == 422
    assert get(app, f"/v1/jobs/{uuid4()}/hold-report")[0] == 404
    queued = store.submit("tenant-a", "collection", {"synthetic": True}, "queued-hold-test")
    assert get(app, f"/v1/jobs/{queued['job_id']}/hold-report")[0] == 404


def test_store_scope_denial_and_infrastructure_hold_do_not_invent_ai_report(held_case):
    app, store, _, principal, catalog, _, path = held_case
    original = store.principal_provider
    store.principal_provider = lambda: {**principal, "scopes": {"metadata", "auditor"}}
    assert get(app, path)[0] == 404
    store.principal_provider = original
    job = store.submit("tenant-a", "research", queued_input(catalog), "infrastructure-hold")
    lease = store.claim(60, allowed_stages=("research",), tenant_id="tenant-a")
    assert lease["job_id"] == job["job_id"]
    assert store.fail("tenant-a", job["job_id"], lease["attempt"], lease["lease_token"],
                      "hold", "model_access_missing")
    assert get(app, f"/v1/jobs/{job['job_id']}/hold-report")[0] == 404


def test_store_auditor_scope_is_required_even_when_http_principal_has_it(held_case):
    app, store, _, principal, _, job_id, path = held_case
    store.principal_provider = lambda: {**principal, "scopes": {"metadata", "artifact"}}
    assert store.read_hold_report("tenant-a", job_id) is None
    assert get(app, path)[0] == 404


@pytest.mark.parametrize("change", [{"tenant_id": "foreign-tenant"}, {"job_id": uuid4()},
    {"attempt": 2}, {"hold_id": "bad-uuid"}, {"recorded_at": None}])
def test_inconsistent_report_metadata_returns_private_fixed_error(held_case, monkeypatch, change):
    app, store, _, _, _, job_id, path = held_case
    held = store.get_hold_report("tenant-a", job_id)
    monkeypatch.setattr(store, "get_hold_report", lambda *_: {**held, **change})
    assert get(app, path) == (503, {"error": {"code": "store_unavailable", "message": "Job hold report unavailable"}})


@pytest.mark.parametrize("raw", [
    b'{"schema_version":"hold_v1","reason_code":"evidence_missing","missing_evidence":[],"private":"credential"}',
    b'{"schema_version":"hold_v1","schema_version":"hold_v1"}',
    _canonical({"schema_version": "hold_v1", "reason_code": "private_reason", "missing_evidence": []}),
    _canonical({"schema_version": "hold_v1", "reason_code": "evidence_missing", "missing_evidence": ["a", "a"]}),
    b" " * 16385,
])
def test_corrupt_or_unsupported_report_bytes_are_not_exposed(held_case, monkeypatch, raw):
    app, store, _, _, _, _, path = held_case
    monkeypatch.setattr(store, "read_hold_report", lambda *_: raw)
    status, error = get(app, path)
    assert status == 503 and error["error"]["message"] == "Job hold report unavailable"
    assert "credential" not in json.dumps(error) and "private_reason" not in json.dumps(error)


def test_real_content_hash_change_is_rejected(held_case):
    app, store, base, _, _, job_id, path = held_case
    original = store.read_hold_report("tenant-a", job_id)
    changed = original.replace(b"research_source_evidence", b"research_target_evidence")
    assert changed != original and len(changed) == len(original)
    with base.connect() as conn:
        digest = conn.execute(sql.SQL("SELECT report_sha256 FROM {}.job_hold_reports WHERE job_id=%s").format(
            sql.Identifier(base.schema)), (job_id,)).fetchone()["report_sha256"]
    directory = store._content_directory("tenant-a")
    try:
        os.chmod(digest, 0o600, dir_fd=directory)
        fd = os.open(digest, os.O_WRONLY | os.O_TRUNC, dir_fd=directory)
        with os.fdopen(fd, "wb") as target:
            target.write(changed)
    finally:
        os.close(directory)
    assert get(app, path)[0] == 503
