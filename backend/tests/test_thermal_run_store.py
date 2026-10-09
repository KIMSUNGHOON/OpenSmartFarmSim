"""PostgreSQL publication checks for two synthetic thermal G1 trace bytes."""

from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta, timezone
from hashlib import sha256
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

from app.thermal import calculate_fixture
from app.thermal_run_store import ThermalRunStore, ThermalStoreHold, install_thermal_run_schema


ROOT = Path(__file__).resolve().parents[2]
GATE_KEY = b"synthetic-test-gate-key-32-bytes!!"
RELEASE_KEY = b"synthetic-test-release-key-32-bytes"
REVIEW_RAW = b'{"mock_review":"not_a_real_authority"}'
CONTEXT_KEY = b"synthetic-test-context-key-32-bytes!"


def verify_test_release(raw, signature):
    if not hmac.compare_digest(signature, hmac.new(
        RELEASE_KEY, b"thermal-g1-release-v1\0" + raw, sha256).hexdigest()):
        return None
    return {"authority_id": "test-authority", "reviewer": "test-independent-reviewer",
            "review_evidence_raw": REVIEW_RAW,
            "issued_at_utc": json.loads(raw)["issued_at_utc"]}


def verify_test_context(raw, signature):
    if not hmac.compare_digest(signature, hmac.new(
        CONTEXT_KEY, b"decision-context-v1\0" + raw, sha256).hexdigest()):
        return None
    context = json.loads(raw)
    return {key: context[key] for key in
            ("authority_id", "planning_event_sha256", "decision_at_utc",
             "decision_time_kind")}


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()


def raw_inputs():
    return tuple((ROOT / "fixtures" / name).read_bytes() for name in (
        "manifest-v2.json", "synthetic-weather-v1.json", "synthetic-thermal-parameters-v1.json"
    ))


def signed_context(tenant, snapshot_id, *, context_id=None, mode="ex_ante", kind="hypothetical"):
    document = {"context_version": "decision-context-v1", "tenant_id": tenant,
        "snapshot_id": snapshot_id, "decision_context_id": context_id or str(uuid4()),
        "decision_at_utc": "2026-09-27T09:04:30Z", "claim_mode": mode,
        "decision_time_kind": kind, "authority_id": "test-context-authority",
        "issued_at_utc": datetime.now(timezone.utc).isoformat(timespec="microseconds").replace("+00:00", "Z")}
    document["planning_event_sha256"] = sha256(canonical({
        "tenant_id": tenant, "snapshot_id": snapshot_id,
        "decision_context_id": document["decision_context_id"],
        "decision_at_utc": document["decision_at_utc"],
        "decision_time_kind": kind, "mock": True})).hexdigest()
    raw = canonical(document)
    signature = hmac.new(CONTEXT_KEY, b"decision-context-v1\0" + raw,
                         sha256).hexdigest()
    return document, raw, signature


def stored_context(run_store, snapshot_id, *, tenant="tenant-a", mode="ex_post_replay"):
    document, raw, signature = signed_context(tenant, snapshot_id, mode=mode)
    assert run_store.put_decision_context(tenant, raw, signature) == document["decision_context_id"]
    context = run_store.get_decision_context(tenant, snapshot_id, document["decision_context_id"])
    assert context["context_sha256"] == sha256(raw).hexdigest()
    return context


def review_at_for(context):
    return (context["recorded_at"].astimezone(timezone.utc) + timedelta(seconds=1)).isoformat(
        timespec="microseconds").replace("+00:00", "Z")


def accepted_pair(snapshot_id, context):
    candidate = calculate_fixture(*raw_inputs(), decision_id=str(uuid4()),
                                  decision_at_utc=context["decision_at_utc"],
                                  input_snapshot_id=snapshot_id,
                                  decision_context_id=context["decision_context_id"],
                                  claim_mode=context["claim_mode"],
                                  decision_time_kind=context["decision_time_kind"],
                                  review_at_utc=review_at_for(context))
    first, second = (json.loads(raw) for raw in candidate)
    first["run_status"] = "accepted"
    first_raw = canonical(first)
    digest = sha256(first_raw).hexdigest()
    second["run_status"] = "accepted"
    for field in ("temperature", "humidity_ratio"):
        carry = second["initial_state"][field]
        carry["previous_trace_sha256"] = digest
        carry["basis_ref"] = f"trace-sha256:{digest}#{carry['previous_state_pointer']}"
    return first_raw, canonical(second)


def packet(snapshot_id, traces, context):
    issued_at = context["recorded_at"].astimezone(timezone.utc).isoformat(
        timespec="microseconds").replace("+00:00", "Z")
    release = canonical({"release_version": "thermal-g1-release-v1", "scope": "synthetic_only",
        "authority_id": "test-authority", "reviewer": "test-independent-reviewer",
        "reviewed_at_utc": issued_at, "issued_at_utc": issued_at,
        "review_evidence_sha256": sha256(REVIEW_RAW).hexdigest(),
        "snapshot_id": snapshot_id, "context_sha256": context["context_sha256"],
        **{key: context[key] for key in
           ("decision_context_id", "decision_at_utc", "claim_mode", "decision_time_kind")}})
    hashes = [sha256(raw).hexdigest() for raw in traces]
    report = canonical({
        "gate_version": "thermal-g1-publisher-v1", "status": "pass",
        "tenant_id": "tenant-a",
        "run_id": json.loads(traces[0])["run_id"], "snapshot_id": snapshot_id,
        "decision_id": json.loads(traces[0])["decision_id"],
        "decision_context_id": context["decision_context_id"],
        "context_sha256": context["context_sha256"],
        "claim_mode": context["claim_mode"],
        "decision_time_kind": context["decision_time_kind"],
        "review_job_id": str(uuid4()), "review_capture_id": str(uuid4()),
        "decision_at_utc": context["decision_at_utc"],
        "review_at_utc": review_at_for(context),
        "manifest_sha256": sha256(raw_inputs()[0]).hexdigest(),
        "code_sha256": "a" * 64, "environment_sha256": "b" * 64,
        "release_sha256": sha256(release).hexdigest(), "trace_sha256": hashes,
    })
    gate_signature = (hmac.new(GATE_KEY, b"thermal-g1-gate-v1\0" + report + b"\0" +
                              hashes[0].encode() + hashes[1].encode(), sha256).hexdigest()
                      if len(hashes) == 2 else "0" * 64)
    release_signature = hmac.new(RELEASE_KEY, b"thermal-g1-release-v1\0" + release,
                                 sha256).hexdigest()
    return dict(report_raw=report, gate_signature=gate_signature, release_raw=release,
                release_signature=release_signature, trace_raws=traces)


@pytest.fixture
def run_store():
    dsn = os.environ.get("OSSF_TEST_PG_DSN")
    if not dsn:
        pytest.skip("OSSF_TEST_PG_DSN is unset")
    schema = "thermal_g1_test_" + uuid4().hex
    with psycopg.connect(dsn, autocommit=True) as conn:
        conn.execute(sql.SQL("CREATE SCHEMA {}").format(sql.Identifier(schema)))
    try:
        with psycopg.connect(dsn) as conn:
            install_thermal_run_schema(conn, schema)
        yield ThermalRunStore(dsn, schema, gate_key=GATE_KEY,
                              release_verifier=verify_test_release,
                              context_verifier=verify_test_context,
                              principal_provider=lambda: {"authenticated": True,
                                  "tenant_id": "tenant-a", "scopes": (
                                      "thermal_snapshot_write", "thermal_snapshot_read",
                                      "thermal_run_publish", "thermal_run_read",
                                      "decision_context_write", "decision_context_read")})
    finally:
        with psycopg.connect(dsn, autocommit=True) as conn:
            conn.execute(sql.SQL("DROP SCHEMA {} CASCADE").format(sql.Identifier(schema)))


def test_snapshot_bytes_are_immutable_and_tenant_scoped(run_store):
    snapshot_id = run_store.put_snapshot("tenant-a", *raw_inputs())
    snapshot = run_store.get_snapshot("tenant-a", snapshot_id)
    assert (snapshot["manifest_raw"], snapshot["weather_raw"], snapshot["thermal_raw"]) == raw_inputs()
    assert run_store.get_snapshot("tenant-b", snapshot_id) is None
    with run_store.connect() as conn, pytest.raises(psycopg.Error):
        conn.execute(sql.SQL("UPDATE {}.thermal_input_snapshots SET weather_raw = %s WHERE snapshot_id = %s")
                     .format(sql.Identifier(run_store.schema)), (b"tampered", snapshot_id))


def test_signed_decision_context_is_immutable_tenant_and_snapshot_scoped(run_store):
    snapshot_id = run_store.put_snapshot("tenant-a", *raw_inputs())
    context = stored_context(run_store, snapshot_id)
    identifier = context["decision_context_id"]
    assert run_store.get_decision_context("tenant-b", snapshot_id, identifier) is None
    assert run_store.get_decision_context("tenant-a", "other-snapshot", identifier) is None
    with run_store.connect() as conn, pytest.raises(psycopg.Error):
        conn.execute(sql.SQL("UPDATE {}.decision_contexts SET snapshot_id=%s WHERE decision_context_id=%s")
                     .format(sql.Identifier(run_store.schema)), ("other-snapshot", identifier))
    missing = ThermalRunStore(run_store.dsn, run_store.schema, gate_key=GATE_KEY,
        release_verifier=verify_test_release, principal_provider=lambda: {
            "authenticated": True, "tenant_id": "tenant-a",
            "scopes": ("decision_context_write", "decision_context_read")})
    _, raw, signature = signed_context("tenant-a", snapshot_id)
    with pytest.raises(ThermalStoreHold, match="SIGNATURE_HOLD"):
        missing.put_decision_context("tenant-a", raw, signature)
    with pytest.raises(ThermalStoreHold, match="SIGNATURE_HOLD"):
        run_store.put_decision_context("tenant-a", raw, "wrong-signature")


def test_malformed_principal_scopes_are_not_authorization(run_store):
    malformed = ThermalRunStore(run_store.dsn, run_store.schema, gate_key=GATE_KEY,
        release_verifier=verify_test_release, principal_provider=lambda: {
            "authenticated": True, "tenant_id": "tenant-a",
            "scopes": "thermal_snapshot_write"})
    with pytest.raises(ThermalStoreHold, match="ACCESS_HOLD"):
        malformed.put_snapshot("tenant-a", *raw_inputs())


def test_two_traces_publish_atomically_and_replay_identically(run_store):
    snapshot_id = run_store.put_snapshot("tenant-a", *raw_inputs())
    context = stored_context(run_store, snapshot_id)
    traces = accepted_pair(snapshot_id, context)
    value = packet(snapshot_id, traces, context)
    record = run_store.publish_verified("tenant-a", **value)
    assert record["run_id"] == json.loads(traces[0])["run_id"]
    assert run_store.get_run("tenant-a", record["run_id"])["trace_raws"] == traces
    assert run_store.get_run("tenant-b", record["run_id"]) is None
    assert run_store.publish_verified("tenant-a", **value)["run_id"] == record["run_id"]
    with run_store.connect() as conn, pytest.raises(psycopg.Error):
        conn.execute(sql.SQL("DELETE FROM {}.thermal_g1_runs WHERE run_id = %s")
                     .format(sql.Identifier(run_store.schema)), (record["run_id"],))


def test_candidate_partial_and_stale_carry_never_publish(run_store):
    snapshot_id = run_store.put_snapshot("tenant-a", *raw_inputs())
    context = stored_context(run_store, snapshot_id)
    accepted = accepted_pair(snapshot_id, context)
    stale = json.loads(accepted[1])
    for field in ("temperature", "humidity_ratio"):
        carry = stale["initial_state"][field]
        carry["previous_trace_sha256"] = "f" * 64
        carry["basis_ref"] = f"trace-sha256:{'f' * 64}#{carry['previous_state_pointer']}"
    for traces in ((accepted[0],),
                   (canonical({**json.loads(accepted[0]), "run_status": "candidate"}), accepted[1]),
                   (accepted[0], canonical(stale))):
        with pytest.raises(ThermalStoreHold):
            run_store.publish_verified("tenant-a", **packet(snapshot_id, traces, context))
    with run_store.connect() as conn:
        count = conn.execute(sql.SQL("SELECT count(*) FROM {}.thermal_g1_runs")
                             .format(sql.Identifier(run_store.schema))).fetchone()["count"]
    assert count == 0


def test_store_without_independent_release_verifier_holds(run_store):
    snapshot_id = run_store.put_snapshot("tenant-a", *raw_inputs())
    context = stored_context(run_store, snapshot_id)
    run_store._release_verifier = None
    with pytest.raises(ThermalStoreHold, match="SIGNATURE_HOLD"):
        run_store.publish_verified("tenant-a", **packet(snapshot_id, accepted_pair(snapshot_id, context), context))


def test_signed_packet_cannot_swap_context_or_review_clock(run_store):
    snapshot_id = run_store.put_snapshot("tenant-a", *raw_inputs())
    context = stored_context(run_store, snapshot_id)
    value = packet(snapshot_id, accepted_pair(snapshot_id, context), context)
    later_review = (datetime.fromisoformat(review_at_for(context).replace("Z", "+00:00")) +
                    timedelta(seconds=1)).isoformat().replace("+00:00", "Z")
    for key, replacement in (("decision_context_id", "other-context"),
                             ("review_at_utc", later_review),
                             ("claim_mode", "ex_ante")):
        altered = json.loads(value["report_raw"])
        altered[key] = replacement
        report_raw = canonical(altered)
        hashes = altered["trace_sha256"]
        signature = hmac.new(GATE_KEY, b"thermal-g1-gate-v1\0" + report_raw + b"\0" +
                             hashes[0].encode() + hashes[1].encode(), sha256).hexdigest()
        with pytest.raises(ThermalStoreHold):
            run_store.publish_verified("tenant-a", **{**value, "report_raw": report_raw,
                                                       "gate_signature": signature})
    with run_store.connect() as conn:
        count = conn.execute(sql.SQL("SELECT count(*) FROM {}.thermal_g1_runs")
                             .format(sql.Identifier(run_store.schema))).fetchone()["count"]
    assert count == 0


def test_store_also_holds_ex_ante_without_durable_proof_packet(run_store):
    snapshot_id = run_store.put_snapshot("tenant-a", *raw_inputs())
    context = stored_context(run_store, snapshot_id, mode="ex_ante")
    value = packet(snapshot_id, accepted_pair(snapshot_id, context), context)
    with pytest.raises(ThermalStoreHold, match="REPORT_HOLD: ex-ante"):
        run_store.publish_verified("tenant-a", **value)


def test_read_rechecks_context_authority(run_store):
    snapshot_id = run_store.put_snapshot("tenant-a", *raw_inputs())
    context = stored_context(run_store, snapshot_id)
    value = packet(snapshot_id, accepted_pair(snapshot_id, context), context)
    receipt = run_store.publish_verified("tenant-a", **value)
    run_store._context_verifier = None
    with pytest.raises(ThermalStoreHold, match="SIGNATURE_HOLD"):
        run_store.get_run("tenant-a", receipt["run_id"])


def test_signed_packet_cannot_replay_into_other_tenant_same_snapshot(run_store):
    other = ThermalRunStore(run_store.dsn, run_store.schema, gate_key=GATE_KEY,
        release_verifier=verify_test_release, context_verifier=verify_test_context,
        principal_provider=lambda: {
            "authenticated": True, "tenant_id": "tenant-b",
            "scopes": ("thermal_snapshot_write", "thermal_run_publish",
                       "decision_context_write", "decision_context_read")})
    snapshot_id = other.put_snapshot("tenant-b", *raw_inputs())
    context = stored_context(other, snapshot_id, tenant="tenant-b")
    signed_for_a = packet(snapshot_id, accepted_pair(snapshot_id, context), context)
    with pytest.raises(ThermalStoreHold, match="REPORT_HOLD"):
        other.publish_verified("tenant-b", **signed_for_a)


@pytest.mark.parametrize("missing", ["status", "carry"])
def test_postgres_rejects_missing_json_fields_even_on_direct_insert(run_store, missing):
    snapshot_id = run_store.put_snapshot("tenant-a", *raw_inputs())
    context = stored_context(run_store, snapshot_id)
    first, second = (json.loads(raw) for raw in accepted_pair(snapshot_id, context))
    if missing == "status":
        del first["run_status"]
    first_raw = canonical(first)
    first_sha = sha256(first_raw).hexdigest()
    for field in ("temperature", "humidity_ratio"):
        carry = second["initial_state"][field]
        carry["previous_trace_sha256"] = first_sha
        carry["basis_ref"] = f"trace-sha256:{first_sha}#{carry['previous_state_pointer']}"
    if missing == "carry":
        del second["initial_state"]["temperature"]["previous_trace_sha256"]
    second_raw = canonical(second)
    value = packet(snapshot_id, (first_raw, second_raw), context)
    report = json.loads(value["report_raw"])
    with run_store.connect() as conn, pytest.raises(psycopg.errors.CheckViolation):
        conn.execute(sql.SQL("""INSERT INTO {}.thermal_g1_runs
            (tenant_id,run_id,snapshot_id,decision_context_id,manifest_sha256,trace0_raw,trace0_sha256,
             trace1_raw,trace1_sha256,release_raw,release_sha256,release_signature,
             report_raw,report_sha256,gate_signature)
             VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)""")
            .format(sql.Identifier(run_store.schema)),
            ("tenant-a", report["run_id"], snapshot_id, context["decision_context_id"],
             report["manifest_sha256"],
             first_raw, first_sha, second_raw, sha256(second_raw).hexdigest(),
             value["release_raw"], sha256(value["release_raw"]).hexdigest(),
             value["release_signature"], value["report_raw"],
             sha256(value["report_raw"]).hexdigest(), value["gate_signature"]))


def test_duplicate_concurrent_publish_is_one_row(run_store):
    snapshot_id = run_store.put_snapshot("tenant-a", *raw_inputs())
    context = stored_context(run_store, snapshot_id)
    value = packet(snapshot_id, accepted_pair(snapshot_id, context), context)
    with ThreadPoolExecutor(max_workers=4) as pool:
        results = list(pool.map(lambda _: run_store.publish_verified("tenant-a", **value), range(4)))
    assert len({row["run_id"] for row in results}) == 1
    with run_store.connect() as conn:
        count = conn.execute(sql.SQL("SELECT count(*) FROM {}.thermal_g1_runs")
                             .format(sql.Identifier(run_store.schema))).fetchone()["count"]
    assert count == 1
