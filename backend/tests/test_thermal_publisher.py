"""Synthetic publisher contract tests; signed fixtures are test doubles, not G1 evidence."""

from hashlib import sha256
from datetime import timezone
import hmac
import json
import os
from pathlib import Path
import sys
from uuid import uuid4

import psycopg
from psycopg import sql
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.thermal_publisher import (ThermalG1Publisher, ThermalPublishHold,
                                   collection_review_input, collection_review_proposal,
                                   runtime_digests, _check_physics, _check_trace_sources,
                                   _source_checks)
from app.thermal import calculate_fixture
from app.thermal_run_store import ThermalRunStore, install_thermal_run_schema
from test_job_evidence import cli_store, prepare_cli_capture
from test_jobs import pg_store, synthetic_decision_bytes
from test_thermal_run_store import stored_context, verify_test_context


ROOT = Path(__file__).resolve().parents[2]
GATE_KEY = b"synthetic-test-gate-key-32-bytes!!"
RELEASE_KEY = b"synthetic-test-release-key-32-bytes"


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()


def input_raws():
    return tuple((ROOT / "fixtures" / name).read_bytes() for name in (
        "manifest-v2.json", "synthetic-weather-v1.json", "synthetic-thermal-parameters-v1.json"))


@pytest.fixture
def setup(pg_store, request, *, schema_installed=False):
    if not schema_installed:
        with pg_store.connect() as conn:
            install_thermal_run_schema(conn, pg_store.schema)
    job_store = cli_store(pg_store)
    evidence_holder = {"raw": None}
    def verify_test_release(raw, signature):
        if not hmac.compare_digest(signature, hmac.new(
            RELEASE_KEY, b"thermal-g1-release-v1\0" + raw, sha256).hexdigest()):
            return None
        return {"authority_id": "test-authority", "reviewer": "independent synthetic reviewer",
                "review_evidence_raw": evidence_holder["raw"],
                "issued_at_utc": json.loads(raw)["issued_at_utc"]}
    run_store = ThermalRunStore(pg_store._dsn, pg_store.schema, gate_key=GATE_KEY,
        release_verifier=verify_test_release, principal_provider=lambda: {
            "authenticated": True, "tenant_id": "tenant-a", "scopes": (
                "thermal_snapshot_write", "thermal_snapshot_read", "thermal_run_publish",
                "thermal_run_read", "decision_context_write", "decision_context_read")},
        context_verifier=verify_test_context)
    snapshot_id = run_store.put_snapshot("tenant-a", *input_raws())
    snapshot = run_store.get_snapshot("tenant-a", snapshot_id)
    context = stored_context(run_store, snapshot_id,
                             mode=getattr(request, "param", "ex_post_replay"))
    reviewed_at = context["recorded_at"].astimezone(timezone.utc).isoformat(
        timespec="microseconds").replace("+00:00", "Z")
    job = job_store.submit("tenant-a", "collection_review",
        collection_review_input(snapshot, context), "thermal-review-" + uuid4().hex)
    lease = job_store.claim(60, allowed_stages=("collection_review",))
    prepare_cli_capture(job_store, job, lease)
    proposal = collection_review_proposal(snapshot, context)
    decision = job_store.record_decision("tenant-a", job["job_id"], lease["attempt"],
        lease["lease_token"], synthetic_decision_bytes(job), canonical(proposal))
    assert decision is not None
    publication = job_store.publish("tenant-a", job["job_id"], lease["attempt"],
        lease["lease_token"], decision, canonical(proposal), sha256(canonical(proposal)).hexdigest(),
        {"schema_version": "1"})
    assert publication is not None
    code_sha, environment_sha = runtime_digests(ROOT)
    evidence = {
        "review_version": "thermal-g1-review-evidence-v1",
        "authority_id": "test-authority", "reviewer": "independent synthetic reviewer",
        "reviewed_at_utc": reviewed_at,
        "issued_at_utc": reviewed_at,
        "review_method": "codex_cli_gpt-6-sol_xhigh",
        "manifest_sha256": snapshot["manifest_sha256"],
        "weather_sha256": snapshot["weather_sha256"],
        "thermal_sha256": snapshot["thermal_sha256"],
        "code_sha256": code_sha, "environment_sha256": environment_sha,
        "cleared_holds": ["NO_ENGINE_OPERATION_ORDER_REVIEW", "NO_SERVER_INPUT_LINKAGE_REVIEW"],
        "operation_order": {"status": "pass", "version": "thermal-euler-v1"},
        "input_linkage": {"status": "pass", "version": "thermal-g1-publisher-v1"},
        "source_rights_qc": {"status": "pass", "scope": "synthetic_only"},
        "snapshot_id": snapshot_id, "context_sha256": context["context_sha256"],
        **{key: context[key] for key in
           ("decision_context_id", "decision_at_utc", "claim_mode", "decision_time_kind")},
    }
    evidence_holder["raw"] = canonical(evidence)
    release = {
        "release_version": "thermal-g1-release-v1", "scope": "synthetic_only",
        "manifest_sha256": snapshot["manifest_sha256"],
        "weather_sha256": snapshot["weather_sha256"],
        "thermal_sha256": snapshot["thermal_sha256"],
        "code_sha256": code_sha, "environment_sha256": environment_sha,
        "authority_id": "test-authority", "reviewer": "independent synthetic reviewer",
        "reviewed_at_utc": reviewed_at,
        "issued_at_utc": reviewed_at,
        "review_evidence_sha256": sha256(evidence_holder["raw"]).hexdigest(),
        "cleared_holds": ["NO_ENGINE_OPERATION_ORDER_REVIEW", "NO_SERVER_INPUT_LINKAGE_REVIEW"],
        "source_verdict": "synthetic_qc_rights_and_links_checked",
        "snapshot_id": snapshot_id, "context_sha256": context["context_sha256"],
        **{key: context[key] for key in
           ("decision_context_id", "decision_at_utc", "claim_mode", "decision_time_kind")},
    }

    def resolver(_tenant, _snapshot_id):
        raw = canonical(release)
        signature = hmac.new(RELEASE_KEY, b"thermal-g1-release-v1\0" + raw,
                             sha256).hexdigest()
        return raw, signature

    publisher = ThermalG1Publisher(run_store, job_store, resolver,
                                   root=ROOT, gate_key=GATE_KEY,
                                   release_verifier=verify_test_release,
                                   execution_verifier=lambda *_: True)
    return publisher, run_store, job_store, job, snapshot_id, release, resolver, evidence_holder


def test_real_db_review_link_promotes_two_recarried_bytes_atomically(setup):
    publisher, runs, _, job, snapshot_id, _, _, _ = setup
    receipt = publisher.publish("tenant-a", job["job_id"], snapshot_id)
    stored = runs.get_run("tenant-a", receipt["run_id"])
    first, second = (json.loads(raw) for raw in stored["trace_raws"])
    assert first["run_status"] == second["run_status"] == "accepted"
    assert second["initial_state"]["temperature"]["previous_trace_sha256"] == sha256(stored["trace_raws"][0]).hexdigest()
    assert stored["report"]["decision_id"] == first["decision_id"]
    assert first["decision_context_id"] == second["decision_context_id"] == stored["report"]["decision_context_id"]
    assert first["decision_at_utc"] == "2026-09-27T09:04:30Z"
    assert first["review_at_utc"] == stored["report"]["review_at_utc"]
    assert first["decision_at_utc"] != first["review_at_utc"]
    assert first["claim_mode"] == second["claim_mode"] == "ex_post_replay"
    assert publisher.publish("tenant-a", job["job_id"], snapshot_id) == receipt
    with runs.connect() as conn:
        count = conn.execute(sql.SQL("SELECT count(*) FROM {}.thermal_g1_runs")
            .format(sql.Identifier(runs.schema))).fetchone()["count"]
    assert count == 1


def test_preparing_verified_packet_does_not_publish_a_run(setup):
    publisher, runs, _, job, snapshot_id, _, _, _ = setup
    packet = publisher.prepare('tenant-a', job['job_id'], snapshot_id)
    report = json.loads(packet['report_raw'])
    assert runs.get_run('tenant-a', report['run_id']) is None
    receipt = runs.publish_verified('tenant-a', **packet)
    assert receipt == publisher.publish('tenant-a', job['job_id'], snapshot_id)


def test_no_release_or_self_author_review_holds_without_run(setup):
    publisher, runs, _, job, snapshot_id, release, resolver, _ = setup
    publisher.release_resolver = lambda *_: None
    with pytest.raises(ThermalPublishHold, match="RELEASE_HOLD"):
        publisher.publish("tenant-a", job["job_id"], snapshot_id)
    release["reviewer"] = "OpenSmartFarmSim fixture authors"
    publisher.release_resolver = resolver
    with pytest.raises(ThermalPublishHold, match="RELEASE_HOLD"):
        publisher.publish("tenant-a", job["job_id"], snapshot_id)
    assert runs.get_run("tenant-a", "none") is None


def test_no_independent_release_verifier_holds_even_with_signed_bytes(setup):
    publisher, runs, _, job, snapshot_id, _, _, _ = setup
    publisher.release_verifier = None
    with pytest.raises(ThermalPublishHold, match="RELEASE_HOLD"):
        publisher.publish("tenant-a", job["job_id"], snapshot_id)
    assert runs.get_run("tenant-a", "none") is None


def test_signed_release_cannot_clear_holds_when_review_evidence_bytes_change(setup):
    publisher, runs, _, job, snapshot_id, _, _, evidence_holder = setup
    evidence_holder["raw"] = canonical({"fake": "review"})
    with pytest.raises(ThermalPublishHold, match="RELEASE_HOLD"):
        publisher.publish("tenant-a", job["job_id"], snapshot_id)
    assert runs.get_run("tenant-a", "none") is None


def test_release_review_cannot_predate_signed_context(setup):
    publisher, runs, _, job, snapshot_id, release, _, evidence_holder = setup
    early = "2026-09-27T09:05:00Z"
    release["reviewed_at_utc"] = early
    evidence = json.loads(evidence_holder["raw"])
    evidence["reviewed_at_utc"] = early
    evidence_holder["raw"] = canonical(evidence)
    release["review_evidence_sha256"] = sha256(evidence_holder["raw"]).hexdigest()
    with pytest.raises(ThermalPublishHold, match="RELEASE_HOLD"):
        publisher.publish("tenant-a", job["job_id"], snapshot_id)
    assert runs.get_run("tenant-a", "none") is None


def test_no_real_worker_proof_holds_even_with_cli_shaped_db_capture(setup):
    publisher, runs, _, job, snapshot_id, _, _, _ = setup
    publisher.execution_verifier = None
    with pytest.raises(ThermalPublishHold, match="REVIEW_HOLD"):
        publisher.publish("tenant-a", job["job_id"], snapshot_id)
    assert runs.get_run("tenant-a", "none") is None


def test_missing_or_swapped_context_holds_before_publication(setup, monkeypatch):
    publisher, runs, _, job, snapshot_id, _, _, _ = setup
    original = runs.get_decision_context
    monkeypatch.setattr(runs, "get_decision_context", lambda *_: None)
    with pytest.raises(ThermalPublishHold, match="CONTEXT_HOLD"):
        publisher.publish("tenant-a", job["job_id"], snapshot_id)
    def swapped(tenant, snapshot, context_id):
        value = original(tenant, snapshot, context_id)
        return {**value, "decision_at_utc": "2026-09-27T08:00:00Z"}
    monkeypatch.setattr(runs, "get_decision_context", swapped)
    with pytest.raises(ThermalPublishHold, match="REVIEW_HOLD"):
        publisher.publish("tenant-a", job["job_id"], snapshot_id)
    assert runs.get_run("tenant-a", "none") is None


def test_server_source_checker_keeps_ex_ante_D_separate_from_R():
    raw = input_raws()
    manifest, weather, thermal = map(json.loads, raw)
    from datetime import datetime, timezone
    D = datetime(2026, 9, 27, 8, tzinfo=timezone.utc)
    R = datetime(2026, 9, 27, 10, tzinfo=timezone.utc)
    hashes = tuple(sha256(value).hexdigest() for value in raw)
    with pytest.raises(ThermalPublishHold, match="SOURCE_HOLD"):
        _source_checks(manifest, weather, thermal, hashes, D, R, "ex_ante")
    _source_checks(manifest, weather, thermal, hashes, D, R, "ex_post_replay")


@pytest.mark.parametrize("setup", ["ex_ante"], indirect=True)
def test_ex_ante_requires_independent_archived_vintage_and_rights_proof(setup):
    publisher, runs, _, job, snapshot_id, _, _, _ = setup
    with pytest.raises(ThermalPublishHold, match="SOURCE_HOLD: no durable D-time"):
        publisher.publish("tenant-a", job["job_id"], snapshot_id)
    assert runs.get_run("tenant-a", "none") is None


def test_snapshot_recorded_after_decision_is_not_retroactive_review(setup, monkeypatch):
    from datetime import timedelta
    publisher, runs, _, job, snapshot_id, _, _, _ = setup
    original = runs.get_snapshot
    def later(tenant, identifier):
        row = original(tenant, identifier)
        return {**row, "recorded_at": row["recorded_at"] + timedelta(days=1)}
    monkeypatch.setattr(runs, "get_snapshot", later)
    with pytest.raises(ThermalPublishHold, match="REVIEW_HOLD"):
        publisher.publish("tenant-a", job["job_id"], snapshot_id)


def test_release_pin_change_or_wrong_job_holds(setup):
    publisher, runs, _, job, snapshot_id, release, _, _ = setup
    release["code_sha256"] = "f" * 64
    with pytest.raises(ThermalPublishHold, match="RELEASE_HOLD"):
        publisher.publish("tenant-a", job["job_id"], snapshot_id)
    with pytest.raises(ThermalPublishHold, match="REVIEW_HOLD"):
        publisher.publish("tenant-a", uuid4(), snapshot_id)
    with runs.connect() as conn:
        count = conn.execute(sql.SQL("SELECT count(*) FROM {}.thermal_g1_runs")
            .format(sql.Identifier(runs.schema))).fetchone()["count"]
    assert count == 0


def test_source_checker_rejects_tampered_rights_and_source_ids_without_publication(setup, monkeypatch):
    publisher, runs, _, job, snapshot_id, _, _, _ = setup
    original = publisher._checked_snapshot
    def bad_snapshot(tenant, identifier, decision_at, review_at, claim_mode):
        manifest, weather, thermal = original(tenant, identifier, decision_at,
                                              review_at, claim_mode)
        manifest["files"][0]["rights"]["display"] = "denied"
        return manifest, weather, thermal
    monkeypatch.setattr(publisher, "_checked_snapshot", bad_snapshot)
    with pytest.raises(ThermalPublishHold, match="SOURCE_HOLD"):
        publisher.publish("tenant-a", job["job_id"], snapshot_id)
    assert runs.get_run("tenant-a", "none") is None


def test_independent_checker_rejects_cross_hour_ids_and_changed_energy():
    manifest_raw, weather_raw, thermal_raw = input_raws()
    manifest, weather, thermal = map(json.loads, (manifest_raw, weather_raw, thermal_raw))
    traces = [json.loads(raw) for raw in calculate_fixture(
        manifest_raw, weather_raw, thermal_raw, decision_id="synthetic-test-decision",
        decision_at_utc="2026-09-27T09:04:30Z", input_snapshot_id="synthetic-test-snapshot",
        decision_context_id="synthetic-test-context", claim_mode="ex_post_replay",
        decision_time_kind="hypothetical", review_at_utc="2026-09-27T09:06:00Z")]
    rows = {row["fixture_id"]: row for row in manifest["files"]}
    identity = {"decision_id": "synthetic-test-decision",
                "decision_at_utc": "2026-09-27T09:04:30Z",
                "review_at_utc": "2026-09-27T09:06:00Z",
                "decision_context_id": "synthetic-test-context",
                "claim_mode": "ex_post_replay", "decision_time_kind": "hypothetical",
                "input_snapshot_id": "synthetic-test-snapshot",
                "manifest_sha256": sha256(manifest_raw).hexdigest()}
    from datetime import datetime, timezone
    review_at = datetime(2026, 9, 27, 9, 6, tzinfo=timezone.utc)
    _check_trace_sources(traces, weather, thermal, rows, review_at, identity)
    _check_physics(traces, weather, thermal)
    traces[1]["forcing"]["solar_gain"]["input_record_ids"][0] = (
        "synthetic-weather-v1:/intervals/0/values/solar_interval_energy")
    with pytest.raises(ThermalPublishHold, match="SOURCE_HOLD"):
        _check_trace_sources(traces, weather, thermal, rows, review_at, identity)
    traces[1]["forcing"]["solar_gain"]["input_record_ids"][0] = (
        "synthetic-weather-v1:/intervals/1/values/solar_interval_energy")
    traces[0]["steps"][0]["heat_terms"]["heater"]["value"] += 1
    with pytest.raises(ThermalPublishHold, match="PHYSICS_HOLD"):
        _check_physics(traces, weather, thermal)
    traces[0]["steps"][0]["heat_terms"]["heater"]["value"] -= 1
    traces[0]["parameters"]["effective_heat_capacity"]["value"] += 1
    with pytest.raises(ThermalPublishHold, match="SOURCE_HOLD"):
        _check_physics(traces, weather, thermal)
    traces[0]["parameters"]["effective_heat_capacity"]["value"] -= 1
    traces[0]["initial_state"]["temperature"]["basis_ref"] = "unrelated-source"
    with pytest.raises(ThermalPublishHold, match="SOURCE_HOLD"):
        _check_trace_sources(traces, weather, thermal, rows, review_at, identity)
    traces[0]["initial_state"]["temperature"]["basis_ref"] = "thermal-assumption-v1"
    traces[1]["source_records"][0]["normalization_rule_ref"] = "invented-rule"
    with pytest.raises(ThermalPublishHold, match="SOURCE_HOLD"):
        _check_trace_sources(traces, weather, thermal, rows, review_at, identity)
    traces[1]["source_records"][0]["normalization_rule_ref"] = "synthetic-identity-si-v1"
    traces[0]["run_id"] = "forged-run"
    with pytest.raises(ThermalPublishHold, match="SOURCE_HOLD"):
        _check_trace_sources(traces, weather, thermal, rows, review_at, identity)
    traces[0]["initial_state"]["humidity_ratio"]["value"] = 0.1
    with pytest.raises(ThermalPublishHold, match="PHYSICS_HOLD"):
        _check_physics(traces, weather, thermal)
