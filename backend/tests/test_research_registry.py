"""Pinned registration facts; fixture metadata establishes no source adoption."""

from dataclasses import FrozenInstanceError
from hashlib import sha256
import json
from pathlib import Path
import sys

import pytest
from psycopg import sql

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from app.api import create_app
from app.cli_contracts import DecisionContract, ProposalHold, _canonical
from app.cli_worker import CliWorker
from app.orchestration import LocationRequest, LocationResearchService
from app.research_registry import ResearchRegistry
from test_api_location_research import (BODY, assembly, login_database, login_scope,
    post, rows, UnusedMarketHoldStore, UnusedThermalRunStore, UnusedMarketResultStore)
from test_cli_contracts import proposal
from test_cli_worker import _fake_cli
from test_job_evidence import cli_store
from test_api_job_status import get


def document():
    return {"registry_version": "research-registry-v1", "registrations": [
        {"tenant_id": "tenant-a", "point": {"latitude": BODY["latitude"], "longitude": BODY["longitude"]},
         "period_start_utc": BODY["period_start_utc"], "period_end_utc": BODY["period_end_utc"],
         "goal_id": BODY["goal_id"], "provider_ids": ["synthetic-provider-v1"]}]}


def registry(value=None):
    raw = _canonical(document() if value is None else value)
    return ResearchRegistry(raw, sha256(raw).hexdigest())


def queued_input(catalog):
    value = {"input_version": "research_input_v1", "tenant_id": "tenant-a",
        "point": {"latitude": BODY["latitude"], "longitude": BODY["longitude"]},
        "period_start_utc": BODY["period_start_utc"], "period_end_utc": BODY["period_end_utc"],
        "goal_id": BODY["goal_id"], "provider_ids": ["synthetic-provider-v1"],
        "candidate_ids": ["synthetic-provider-v1", "research-registry-sha256:"+catalog.sha256],
        "evidence_refs": [], "decision_context_id": None, "decision_at_utc": None,
        "claim_mode": None, "decision_time_kind": None}
    return value


def job_for(value):
    raw = _canonical(value)
    return {"stage": "research", "tenant_id": value["tenant_id"],
            "input_bytes": raw, "input_sha256": sha256(raw).hexdigest()}


def test_admission_and_cli_authority_use_same_persisted_registry_identity(assembly):
    _, store, base, _, principal, _ = assembly
    catalog = registry()
    contract = DecisionContract(catalog.authority_snapshot)
    store.decision_validator = contract
    app = create_app(store, UnusedMarketHoldStore(), UnusedThermalRunStore(),
                     UnusedMarketResultStore(), principal_provider=lambda: principal,
                     location_research_service=LocationResearchService(store, catalog.scope_for_location))
    accepted = post(app)
    assert accepted[0] == 202 and post(app) == accepted
    job = rows(base)[0]
    value, authority = contract.input_context(job)
    assert value == queued_input(catalog)
    assert authority.allow_proceed is False and authority.evidence == {} and authority.approved_claims == {}
    assert authority.missing_evidence == ("research_source_evidence", "signed_decision_context")
    output = proposal(job)
    output["missing_evidence"] = list(authority.missing_evidence)
    plan = contract.plan(job, _canonical(output))
    assert plan.disposition == "hold" and plan.code == "validated_hold"
    output.update(proposed_status="proceed", selected_ids=["synthetic-provider-v1"])
    with pytest.raises(ProposalHold, match="^gate_hold$"):
        contract.plan(job, _canonical(output))
    assert post(app, {**BODY, "longitude": 128.0})[0] == 422
    principal["tenant_id"] = "tenant-b"
    assert post(app)[0] == 422
    assert len(rows(base)) == 1
    with base.connect() as conn:
        assert conn.execute(sql.SQL("SELECT count(*) FROM {}.ai_decisions").format(
            sql.Identifier(base.schema))).fetchone()["count"] == 0


def test_registered_facts_are_frozen_and_return_no_foreign_scope():
    catalog = registry()
    body = LocationRequest.model_validate(BODY)
    scope = catalog.scope_for_location("tenant-a", body)
    assert scope.registry_sha256 == catalog.sha256
    with pytest.raises(FrozenInstanceError):
        catalog._sha256 = "a" * 64
    with pytest.raises(TypeError):
        catalog._scopes["new"] = scope
    with pytest.raises(FrozenInstanceError):
        scope.provider_ids = ("unregistered-provider",)
    assert catalog.scope_for_location("tenant-b", body) is None
    assert catalog.scope_for_location("tenant-a", BODY) is None


def test_registered_region_to_process_hold_and_http_status(assembly, tmp_path):
    _, store, base, _, principal, _ = assembly
    catalog = registry()
    contract = DecisionContract(catalog.authority_snapshot)
    store.decision_validator = contract
    store.evidence_policy = cli_store(store).evidence_policy
    principal["scopes"].update({"auditor", "artifact"})
    app = create_app(store, UnusedMarketHoldStore(), UnusedThermalRunStore(),
                     UnusedMarketResultStore(), principal_provider=lambda: principal,
                     location_research_service=LocationResearchService(store, catalog.scope_for_location))
    status, accepted = post(app)
    assert status == 202
    original = rows(base)[0]["input_bytes"]
    home = tmp_path / "synthetic-cli-home"
    home.mkdir(mode=0o700)
    worker = CliWorker(store, contract, cli_path=_fake_cli(tmp_path), codex_home=home,
        child_env={"CODEX_API_KEY": "synthetic-test-key"}, timeout_seconds=5,
        lease_seconds=15, synthetic_smoke=True)
    result = worker.run_once()
    assert result.state == "hold" and result.reason_code == "validated_hold"
    assert result.capture_id is not None and result.decision_id is not None
    report = json.loads(store.read_hold_report("tenant-a", result.job_id))
    assert report["missing_evidence"] == ["research_source_evidence", "signed_decision_context"]
    status, observed = get(app, "/v1/jobs/"+accepted["research_job"]["job_id"])
    assert status == 200 and observed["state"] == "hold" and observed["attempt_count"] == 1
    assert observed["reason_code"] == "ai_validated_hold"
    status, replay = post(app)
    assert status == 202 and replay["research_job"]["job_id"] == accepted["research_job"]["job_id"]
    assert len(rows(base)) == 1 and rows(base)[0]["input_bytes"] == original
    assert worker.run_once() is None


@pytest.mark.parametrize("change", [
    {"provider_ids": ["unregistered-provider"]},
    {"candidate_ids": ["synthetic-provider-v1", "research-registry-sha256:"+"a"*64]},
    {"candidate_ids": ["synthetic-provider-v1"]},
    {"goal_id": "foreign-goal"}, {"tenant_id": "tenant-b"},
    {"point": {"latitude": 37.0, "longitude": 127.0}},
    {"period_end_utc": "2026-01-03T00:00:00Z"},
    {"evidence_refs": [{"id": "forged-source", "sha256": "a"*64}]},
    {"decision_context_id": "unverified-context", "decision_at_utc": "2026-01-01T00:00:00Z",
     "claim_mode": "ex_post_replay", "decision_time_kind": "actual"},
])
def test_changed_request_or_unapproved_context_cannot_gain_authority(change):
    catalog = registry()
    value = {**queued_input(catalog), **change}
    assert catalog.authority_snapshot(job_for(value), value) is None


def test_cli_authority_rechecks_raw_bytes_and_exact_parsed_value():
    catalog = registry()
    value = queued_input(catalog)
    job = job_for(value)
    assert catalog.authority_snapshot({**job, "input_sha256": "a"*64}, value) is None
    assert catalog.authority_snapshot({**job, "stage": "assessment"}, value) is None
    assert catalog.authority_snapshot(job, {**value, "goal_id": "foreign-goal"}) is None
    changed = document()
    changed["registrations"][0]["provider_ids"].append("new-provider")
    assert registry(changed).authority_snapshot(job, value) is None


@pytest.mark.parametrize("change", [
    {"tenant_id": True}, {"tenant_id": "bad tenant"}, {"point": {"latitude": True, "longitude": 127.0}},
    {"point": {"latitude": 91.0, "longitude": 127.0}},
    {"point": {"latitude": 37.5, "longitude": 127.0, "station_id": "foreign"}},
    {"period_start_utc": "2026-02-30T00:00:00Z"},
    {"period_end_utc": BODY["period_start_utc"]}, {"G0": True},
    {"provider_ids": []}, {"provider_ids": ["same", "same"]}, {"provider_ids": [True]},
    {"provider_ids": [["unhashable"]]}, {"provider_ids": ["research-registry-sha256:"+"a"*64]},
])
def test_invalid_catalog_entries_reject_with_fixed_private_error(change):
    value = document()
    value["registrations"][0].update(change)
    with pytest.raises(ValueError, match="^research registry rejected$"):
        registry(value)


@pytest.mark.parametrize("fault", ["pin", "canonical", "duplicates", "unknown", "empty", "many", "key", "size", "utf8"])
def test_catalog_envelope_and_raw_identity_are_bounded(fault):
    value = document()
    if fault == "duplicates":
        value["registrations"] *= 2
    elif fault == "unknown":
        value["private-source-key"] = "private-credential"
    elif fault == "empty":
        value["registrations"] = []
    elif fault == "many":
        value["registrations"] *= 65
    raw = _canonical(value)
    if fault == "canonical":
        raw = json.dumps(value, indent=2).encode()
    elif fault == "key":
        raw = b'{"registry_version":"private-credential","registry_version":"research-registry-v1"}'
    elif fault == "size":
        raw = b" " * 65537
    elif fault == "utf8":
        raw = b"\xffprivate-credential"
    expected = "a" * 64 if fault == "pin" else sha256(raw).hexdigest()
    with pytest.raises(ValueError, match="^research registry rejected$"):
        ResearchRegistry(raw, expected)
