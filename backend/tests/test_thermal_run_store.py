"""PostgreSQL publication checks for two synthetic thermal G1 trace bytes."""

from concurrent.futures import ThreadPoolExecutor
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


def verify_test_release(raw, signature):
    if not hmac.compare_digest(signature, hmac.new(
        RELEASE_KEY, b"thermal-g1-release-v1\0" + raw, sha256).hexdigest()):
        return None
    return {"authority_id": "test-authority", "reviewer": "test-independent-reviewer",
            "review_evidence_raw": REVIEW_RAW}


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()


def raw_inputs():
    return tuple((ROOT / "fixtures" / name).read_bytes() for name in (
        "manifest-v2.json", "synthetic-weather-v1.json", "synthetic-thermal-parameters-v1.json"
    ))


def accepted_pair(snapshot_id):
    candidate = calculate_fixture(*raw_inputs(), decision_id=str(uuid4()),
                                  decision_at_utc="2026-09-28T00:00:00Z",
                                  input_snapshot_id=snapshot_id)
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


def packet(snapshot_id, traces):
    release = canonical({"release_version": "thermal-g1-release-v1", "scope": "synthetic_only",
        "authority_id": "test-authority", "reviewer": "test-independent-reviewer",
        "review_evidence_sha256": sha256(REVIEW_RAW).hexdigest()})
    hashes = [sha256(raw).hexdigest() for raw in traces]
    report = canonical({
        "gate_version": "thermal-g1-publisher-v1", "status": "pass",
        "tenant_id": "tenant-a",
        "run_id": json.loads(traces[0])["run_id"], "snapshot_id": snapshot_id,
        "decision_id": json.loads(traces[0])["decision_id"],
        "review_job_id": str(uuid4()), "review_capture_id": str(uuid4()),
        "decision_at_utc": "2026-09-28T00:00:00Z",
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
                              principal_provider=lambda: {"authenticated": True,
                                  "tenant_id": "tenant-a", "scopes": (
                                      "thermal_snapshot_write", "thermal_snapshot_read",
                                      "thermal_run_publish", "thermal_run_read")})
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


def test_malformed_principal_scopes_are_not_authorization(run_store):
    malformed = ThermalRunStore(run_store.dsn, run_store.schema, gate_key=GATE_KEY,
        release_verifier=verify_test_release, principal_provider=lambda: {
            "authenticated": True, "tenant_id": "tenant-a",
            "scopes": "thermal_snapshot_write"})
    with pytest.raises(ThermalStoreHold, match="ACCESS_HOLD"):
        malformed.put_snapshot("tenant-a", *raw_inputs())


def test_two_traces_publish_atomically_and_replay_identically(run_store):
    snapshot_id = run_store.put_snapshot("tenant-a", *raw_inputs())
    traces = accepted_pair(snapshot_id)
    value = packet(snapshot_id, traces)
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
    accepted = accepted_pair(snapshot_id)
    for traces in ((accepted[0],),
                   (canonical({**json.loads(accepted[0]), "run_status": "candidate"}), accepted[1]),
                   (accepted[0], canonical({**json.loads(accepted[1]), "initial_state":
                    json.loads(calculate_fixture(*raw_inputs(),
                        decision_id=json.loads(accepted[0])["decision_id"],
                        decision_at_utc="2026-09-28T00:00:00Z",
                        input_snapshot_id=snapshot_id)[1])["initial_state"]}))):
        with pytest.raises(ThermalStoreHold):
            run_store.publish_verified("tenant-a", **packet(snapshot_id, traces))
    with run_store.connect() as conn:
        count = conn.execute(sql.SQL("SELECT count(*) FROM {}.thermal_g1_runs")
                             .format(sql.Identifier(run_store.schema))).fetchone()["count"]
    assert count == 0


def test_store_without_independent_release_verifier_holds(run_store):
    snapshot_id = run_store.put_snapshot("tenant-a", *raw_inputs())
    run_store._release_verifier = None
    with pytest.raises(ThermalStoreHold, match="SIGNATURE_HOLD"):
        run_store.publish_verified("tenant-a", **packet(snapshot_id, accepted_pair(snapshot_id)))


def test_signed_packet_cannot_replay_into_other_tenant_same_snapshot(run_store):
    other = ThermalRunStore(run_store.dsn, run_store.schema, gate_key=GATE_KEY,
        release_verifier=verify_test_release, principal_provider=lambda: {
            "authenticated": True, "tenant_id": "tenant-b",
            "scopes": ("thermal_snapshot_write", "thermal_run_publish")})
    snapshot_id = other.put_snapshot("tenant-b", *raw_inputs())
    signed_for_a = packet(snapshot_id, accepted_pair(snapshot_id))
    with pytest.raises(ThermalStoreHold, match="REPORT_HOLD"):
        other.publish_verified("tenant-b", **signed_for_a)


@pytest.mark.parametrize("missing", ["status", "carry"])
def test_postgres_rejects_missing_json_fields_even_on_direct_insert(run_store, missing):
    snapshot_id = run_store.put_snapshot("tenant-a", *raw_inputs())
    first, second = (json.loads(raw) for raw in accepted_pair(snapshot_id))
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
    value = packet(snapshot_id, (first_raw, second_raw))
    report = json.loads(value["report_raw"])
    with run_store.connect() as conn, pytest.raises(psycopg.errors.CheckViolation):
        conn.execute(sql.SQL("""INSERT INTO {}.thermal_g1_runs
            (tenant_id,run_id,snapshot_id,manifest_sha256,trace0_raw,trace0_sha256,
             trace1_raw,trace1_sha256,release_raw,release_sha256,release_signature,
             report_raw,report_sha256,gate_signature)
             VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)""")
            .format(sql.Identifier(run_store.schema)),
            ("tenant-a", report["run_id"], snapshot_id, report["manifest_sha256"],
             first_raw, first_sha, second_raw, sha256(second_raw).hexdigest(),
             value["release_raw"], sha256(value["release_raw"]).hexdigest(),
             value["release_signature"], value["report_raw"],
             sha256(value["report_raw"]).hexdigest(), value["gate_signature"]))


def test_duplicate_concurrent_publish_is_one_row(run_store):
    snapshot_id = run_store.put_snapshot("tenant-a", *raw_inputs())
    value = packet(snapshot_id, accepted_pair(snapshot_id))
    with ThreadPoolExecutor(max_workers=4) as pool:
        results = list(pool.map(lambda _: run_store.publish_verified("tenant-a", **value), range(4)))
    assert len({row["run_id"] for row in results}) == 1
    with run_store.connect() as conn:
        count = conn.execute(sql.SQL("SELECT count(*) FROM {}.thermal_g1_runs")
                             .format(sql.Identifier(run_store.schema))).fetchone()["count"]
    assert count == 1
