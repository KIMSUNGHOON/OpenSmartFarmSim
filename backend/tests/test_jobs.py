"""PostgreSQL contracts for the durable job store; only synthetic metadata is used."""

from concurrent.futures import ThreadPoolExecutor
from hashlib import sha256
import json
import os
from pathlib import Path
import sys
from uuid import UUID, uuid4

import psycopg
from psycopg import sql
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.db import install_schema
from app.job_store import JobStore
from app import jobs
from app.jobs import canonical_input_bytes, canonical_input_sha256


@pytest.fixture
def pg_store(tmp_path):
    dsn = os.environ.get("OSSF_TEST_PG_DSN")
    if not dsn:
        pytest.skip("OSSF_TEST_PG_DSN is unset")
    schema = "jobs_test_" + uuid4().hex
    with psycopg.connect(dsn, autocommit=True) as conn:
        conn.execute(sql.SQL("CREATE SCHEMA {}").format(sql.Identifier(schema)))
    try:
        with psycopg.connect(dsn) as conn:
            install_schema(conn, schema)
        yield JobStore(
            dsn, schema, tmp_path / "artifacts",
            decision_validator=synthetic_validator,
            evidence_policy=synthetic_evidence_policy,
            principal_provider=synthetic_principal,
            allow_synthetic_invocation=True,
        )
    finally:
        with psycopg.connect(dsn, autocommit=True) as conn:
            conn.execute(sql.SQL("DROP SCHEMA {} CASCADE").format(sql.Identifier(schema)))


MAX_INPUT_BYTES = 64 * 1024


def synthetic_decision_bytes(job):
    return json.dumps({
        "schema_version": "decision_v1", "stage": job["stage"],
        "input_sha256": job["input_sha256"], "fixture": "synthetic",
    }, sort_keys=True, separators=(",", ":")).encode()


def synthetic_validator(job, final_output, proposed_artifact):
    try:
        value = json.loads(final_output)
    except (ValueError, UnicodeDecodeError):
        return {"passed": False, "version": "synthetic-storage-v1", "code": "invalid_json"}
    passed = (value == json.loads(synthetic_decision_bytes(job))
              and isinstance(proposed_artifact, bytes))
    return {"passed": passed, "version": "synthetic-storage-v1",
            "code": "synthetic_pass" if passed else "synthetic_mismatch"}


def synthetic_evidence_policy(tenant_id, source_id, intended_use, kind, payload, digest):
    fixture_bytes = (intended_use == "decision_evidence" and
                     (b"synthetic" in payload or
                     (kind == "final_output" and payload == b"invalid JSON") or
                     (kind == "validation_report" and b'"report_version":"decision-validation-v1"' in payload)))
    return dict(tenant_id=tenant_id,
                source_id="synthetic_self_authored" if fixture_bytes else "unverified",
                intended_use=intended_use,
                payload_sha256=digest,
                rights_proof_id="synthetic_self_authored" if fixture_bytes else "synthetic_denial",
                rights_version="fixture-v1", policy_version="synthetic-storage-v1",
                classification="private" if fixture_bytes else "restricted",
                read_scope="auditor" if fixture_bytes else "none",
                retain_raw=fixture_bytes, retain_digest=True)


synthetic_evidence_policy.policy_version = "synthetic-storage-v1"


def synthetic_principal():
    return {"authenticated": True, "tenant_id": "tenant-a",
            "scopes": ("metadata", "auditor", "artifact", "cancel")}


def test_isolated_runtime_role_cannot_insert_authoritative_audit_rows(pg_store):
    role = "ossf_test_runtime_" + uuid4().hex
    created = False
    try:
        with pg_store.connect() as conn:
            current_user = conn.execute("SELECT current_user AS name").fetchone()["name"]
            try:
                conn.execute(sql.SQL("CREATE ROLE {} NOLOGIN").format(sql.Identifier(role)))
                conn.execute(sql.SQL("GRANT {} TO {}").format(
                    sql.Identifier(role), sql.Identifier(current_user)))
            except psycopg.errors.InsufficientPrivilege:
                pytest.skip("test server does not permit isolated role creation")
            created = True
            conn.execute(sql.SQL("GRANT USAGE ON SCHEMA {} TO {}").format(
                sql.Identifier(pg_store.schema), sql.Identifier(role)))
            for table in ("evidence_authorizations", "attempt_evidence",
                          "validation_receipts", "ai_decisions"):
                conn.execute(sql.SQL("GRANT SELECT ON {}.{} TO {}").format(
                    sql.Identifier(pg_store.schema), sql.Identifier(table), sql.Identifier(role)))
        for table in ("evidence_authorizations", "attempt_evidence",
                      "validation_receipts", "ai_decisions"):
            with pg_store.connect() as conn:
                conn.execute(sql.SQL("SET LOCAL ROLE {}").format(sql.Identifier(role)))
                with pytest.raises(psycopg.errors.InsufficientPrivilege):
                    conn.execute(sql.SQL("INSERT INTO {}.{} SELECT * FROM {}.{} WHERE false").format(
                        sql.Identifier(pg_store.schema), sql.Identifier(table),
                        sql.Identifier(pg_store.schema), sql.Identifier(table)))
    finally:
        if created:
            with pg_store.connect() as conn:
                conn.execute(sql.SQL("DROP OWNED BY {}").format(sql.Identifier(role)))
                conn.execute(sql.SQL("DROP ROLE {}").format(sql.Identifier(role)))


def validated_decision(store, job, lease, payload):
    prepare_synthetic_invocation(store, job, lease)
    return store.record_decision(job["tenant_id"], job["job_id"], lease["attempt"],
                                 lease["lease_token"], synthetic_decision_bytes(job), payload)


def prepare_synthetic_invocation(store, job, lease):
    tenant, job_id, attempt, token = (job["tenant_id"], job["job_id"],
                                      lease["attempt"], lease["lease_token"])
    if store.get_invocation(tenant, job_id, attempt) is not None:
        return
    if store.read_input(tenant, job_id, attempt, token) is None:
        return
    prompt = store.append_evidence(tenant, job_id, attempt, token, kind="prompt",
        payload=b"synthetic instruction v1", rights_ref="self_authored_fixture")
    schema = store.append_evidence(tenant, job_id, attempt, token, kind="output_schema",
        payload=b'{"fixture":"synthetic"}', rights_ref="self_authored_fixture")
    assert prompt is not None and schema is not None
    assert store.register_invocation(tenant, job_id, attempt, token,
        prompt_evidence_id=prompt["evidence_id"], schema_evidence_id=schema["evidence_id"],
        prompt_version="synthetic-v1", schema_version="synthetic-v1",
        execution_kind="synthetic_fixture", cli_version="synthetic_fixture",
        model=None, reasoning_effort=None)


def test_canonical_input_serializes_once_and_rejects_non_json(monkeypatch):
    calls = 0
    original = jobs.json.dumps

    def counted(*args, **kwargs):
        nonlocal calls
        calls += 1
        return original(*args, **kwargs)

    monkeypatch.setattr(jobs.json, "dumps", counted)
    assert canonical_input_bytes({"b": "합성", "a": [1]}) == '{"a":[1],"b":"합성"}'.encode("utf-8")
    assert calls == 1
    for value in ([1], {"source_bytes": b"synthetic bytes"}, {"count": float("nan")},
                  {1: "synthetic"}):
        with pytest.raises(ValueError):
            canonical_input_bytes(value)
    with pytest.raises(ValueError, match="input exceeds"):
        canonical_input_bytes({"fixture": "가" * MAX_INPUT_BYTES})
    for value in ({"api_key": "synthetic-placeholder"},
                  {"nested": [{"password": "synthetic-placeholder"}]},
                  {"source": {"raw_data": "synthetic source"}},
                  {"source_raw_data": "synthetic source"},
                  {"provider_response": "synthetic source"}):
        with pytest.raises(ValueError, match="input field"):
            canonical_input_bytes(value)


def test_canonical_input_rechecks_nested_field_names_and_changed_raw_digest():
    value = {"nested": [{"raw_sha256": "a" * 64, "source_url": "synthetic"}]}
    assert canonical_input_bytes(value) == (
        b'{"nested":[{"raw_sha256":"' + b'a' * 64 + b'","source_url":"synthetic"}]}')
    value["nested"][0]["raw_sha256"] = "A" * 64
    with pytest.raises(ValueError, match="input field"):
        canonical_input_bytes(value)
    for key in ("prefix-PASS.word-suffix", "source_raw_content", "an_API_KEY_reference",
                "xBearerTokenY", "safe_authorization_note", "prior_CREDENTIAL_record"):
        with pytest.raises(ValueError, match="input field"):
            canonical_input_bytes({"nested": [{key: "synthetic"}]})
    assert canonical_input_bytes({"supply": "synthetic", "scope_version": "r1"}) == (
        b'{"scope_version":"r1","supply":"synthetic"}')


def submit(store, tenant="tenant-a", stage="research", input_value=None, key="key-a", **kwargs):
    return store.submit(tenant, stage, input_value or {"fixture": "synthetic"}, key, **kwargs)


def test_intent_key_dedup_concurrent_and_terminal(pg_store):
    with ThreadPoolExecutor(max_workers=8) as pool:
        results = list(pool.map(lambda _: submit(pg_store), range(16)))
    job_id = results[0]["job_id"]
    assert {row["job_id"] for row in results} == {job_id}
    assert UUID(str(job_id))
    assert submit(pg_store)["job_id"] == job_id
    assert submit(pg_store, tenant="tenant-b")["job_id"] != job_id
    assert submit(pg_store, stage="simulation")["job_id"] != job_id
    with pytest.raises(ValueError, match="idempotency"):
        submit(pg_store, input_value={"fixture": "other"})
    assert submit(pg_store, input_value={"fixture": "other"}, key="other-input")["job_id"] != job_id
    assert submit(pg_store, key="other")["job_id"] != job_id
    assert canonical_input_sha256({"a": 1, "b": 2}) == canonical_input_sha256({"b": 2, "a": 1})
    assert results[0]["input_sha256"] == canonical_input_sha256({"fixture": "synthetic"})
    assert pg_store.get_job("tenant-b", job_id) is None
    with pytest.raises(ValueError):
        submit(pg_store, key="")

    lease = pg_store.claim(60)
    assert lease["job_id"] == job_id
    assert "lease_token" not in submit(pg_store)
    assert "lease_token" not in pg_store.get_job("tenant-a", job_id)
    pg_store.fail("tenant-a", job_id, lease["attempt"], lease["lease_token"], "fatal", "invalid_fixture")
    assert submit(pg_store)["state"] == "failed"
    with pg_store.connect() as conn, pytest.raises(psycopg.Error):
        conn.execute(sql.SQL("UPDATE {}.jobs SET state = 'queued' WHERE tenant_id = %s AND job_id = %s")
                     .format(sql.Identifier(pg_store.schema)), ("tenant-a", job_id))


def test_input_bytes_are_canonical_private_and_immutable(pg_store):
    value = {"z": [1.0, "합성"], "a": {"b": 2}}
    expected = '{"a":{"b":2},"z":[1.0,"합성"]}'.encode("utf-8")
    job = submit(pg_store, input_value=value)
    assert job["input_sha256"] == sha256(expected).hexdigest()
    assert "input_bytes" not in job
    assert "input_bytes" not in pg_store.get_job("tenant-a", job["job_id"])
    with pg_store.connect() as conn:
        stored = conn.execute(sql.SQL("""
            SELECT input_bytes, pg_typeof(input_bytes)::text AS input_type FROM {}.jobs
            WHERE tenant_id = %s AND job_id = %s
        """).format(sql.Identifier(pg_store.schema)),
            ("tenant-a", job["job_id"])).fetchone()
    assert stored["input_bytes"] == expected
    assert stored["input_type"] == "bytea"
    for column, replacement in (("input_bytes", b"changed"),
                                ("input_sha256", "0" * 64)):
        with pg_store.connect() as conn, pytest.raises(psycopg.Error):
            conn.execute(sql.SQL("UPDATE {}.jobs SET {} = %s WHERE tenant_id = %s AND job_id = %s")
                         .format(sql.Identifier(pg_store.schema), sql.Identifier(column)),
                         (replacement, "tenant-a", job["job_id"]))


def test_submission_rejects_oversize_secrets_and_raw_source_fields(pg_store):
    with pytest.raises(ValueError, match="input exceeds"):
        submit(pg_store, input_value={"fixture": "가" * MAX_INPUT_BYTES})
    for value in ({"api_key": "synthetic-placeholder"},
                  {"nested": [{"password": "synthetic-placeholder"}]},
                  {"source": {"raw_data": "synthetic source"}},
                  {"provider_response": "synthetic source"}):
        with pytest.raises(ValueError, match="input field"):
            submit(pg_store, input_value=value)
    assert pg_store.claim(60) is None


def test_worker_input_read_requires_live_current_lease(pg_store):
    job = submit(pg_store)
    assert pg_store.read_input("tenant-a", job["job_id"], 1, "wrong") is None
    lease = pg_store.claim(60)
    expected = b'{"fixture":"synthetic"}'
    assert lease["input_bytes"] == expected
    assert pg_store.read_input("tenant-a", job["job_id"], 1, lease["lease_token"]) == expected
    assert pg_store.read_input("tenant-b", job["job_id"], 1, lease["lease_token"]) is None
    assert pg_store.read_input("tenant-a", job["job_id"], 2, lease["lease_token"]) is None
    assert pg_store.read_input("tenant-a", job["job_id"], 1, "wrong") is None
    assert pg_store.cancel("tenant-a", job["job_id"])
    assert pg_store.read_input("tenant-a", job["job_id"], 1, lease["lease_token"]) is None


def test_collection_review_claim_and_database_stage_state_pair(pg_store):
    review = submit(pg_store, stage="collection_review")
    with pytest.raises(ValueError, match="unknown job stage"):
        submit(pg_store, stage="review", key="legacy-review")
    lease = pg_store.claim(60)
    assert lease["job_id"] == review["job_id"]
    assert lease["stage"] == "collection_review"
    assert lease["state"] == "reviewing"
    assert pg_store.get_job("tenant-a", review["job_id"])["state"] == "reviewing"

    collection = submit(pg_store, stage="collection", key="collect")
    collected = pg_store.claim(60)
    assert collected["job_id"] == collection["job_id"]
    assert collected["state"] == "collecting"

    for stage, state in (("collection_review", "collecting"),
                         ("collection", "reviewing")):
        with pg_store.connect() as conn, pytest.raises(psycopg.errors.CheckViolation):
            conn.execute(sql.SQL("""
                INSERT INTO {}.jobs (tenant_id, job_id, stage, input_sha256, input_bytes,
                                     idempotency_key, state, max_attempts,
                                     lease_token, lease_until)
                VALUES (%s, %s, %s, %s, %s, %s, %s, 1, 'synthetic-token',
                        clock_timestamp() + interval '1 minute')
            """).format(sql.Identifier(pg_store.schema)),
                ("tenant-a", uuid4(), stage, sha256(b"{}").hexdigest(),
                 b"{}", str(uuid4()), state))


def test_max_attempts_rejects_more_than_two_retries(pg_store):
    allowed = submit(pg_store, max_attempts=3)
    assert allowed["max_attempts"] == 3
    with pytest.raises(ValueError):
        submit(pg_store, key="four", max_attempts=4)
    with pg_store.connect() as conn, pytest.raises(psycopg.errors.CheckViolation):
        conn.execute(sql.SQL("""
            INSERT INTO {}.jobs (tenant_id, job_id, stage, input_sha256, input_bytes,
                                 idempotency_key, state, max_attempts)
            VALUES (%s, %s, 'research', %s, %s, %s, 'queued', 4)
        """).format(sql.Identifier(pg_store.schema)),
            ("tenant-a", uuid4(), sha256(b"{}").hexdigest(), b"{}", "direct-four"))


def test_claim_skips_locked_oldest_job(pg_store):
    first = submit(pg_store, key="first")
    second = submit(pg_store, key="second")
    with pg_store.connect() as lock_conn:
        locked = lock_conn.execute(sql.SQL("""
            SELECT job_id FROM {}.jobs ORDER BY created_at, job_id
            FOR UPDATE LIMIT 1
        """).format(sql.Identifier(pg_store.schema))).fetchone()
        assert locked["job_id"] == first["job_id"]
        lease = pg_store.claim(60)
        assert lease["job_id"] == second["job_id"]
    lease = pg_store.claim(60)
    assert lease["job_id"] == first["job_id"]


def test_one_claim_renew_fence_and_reclaim(pg_store):
    job = submit(pg_store, max_attempts=2)
    with ThreadPoolExecutor(max_workers=2) as pool:
        leases = list(pool.map(lambda _: pg_store.claim(60), range(2)))
    assert sum(lease is not None for lease in leases) == 1
    first = next(lease for lease in leases if lease)
    assert first["attempt"] == 1
    assert pg_store.renew("tenant-a", job["job_id"], 1, first["lease_token"], 60)
    assert not pg_store.renew("tenant-b", job["job_id"], 1, first["lease_token"], 60)
    assert not pg_store.renew("tenant-a", job["job_id"], 1, "wrong", 60)
    with pg_store.connect() as conn:
        conn.execute(sql.SQL("UPDATE {}.jobs SET lease_until = clock_timestamp() - interval '1 second' WHERE job_id = %s")
                     .format(sql.Identifier(pg_store.schema)), (job["job_id"],))
    second = pg_store.claim(60)
    assert second["job_id"] == job["job_id"] and second["attempt"] == 2
    assert second["lease_token"] != first["lease_token"]
    assert not pg_store.renew("tenant-a", job["job_id"], 1, first["lease_token"], 60)
    assert not pg_store.fail("tenant-a", job["job_id"], 1, first["lease_token"], "fatal", "stale")
    with pg_store.connect() as conn:
        conn.execute(sql.SQL("UPDATE {}.jobs SET lease_until = clock_timestamp() - interval '1 second' WHERE job_id = %s")
                     .format(sql.Identifier(pg_store.schema)), (job["job_id"],))
    pg_store.recover_expired()
    assert pg_store.get_job("tenant-a", job["job_id"])["reason"]["code"] == "attempts_exhausted"
    assert pg_store.claim(60) is None


def test_retry_hold_fatal_and_cancel(pg_store):
    transient = submit(pg_store, key="transient", max_attempts=2)
    lease = pg_store.claim(60)
    assert pg_store.fail("tenant-a", transient["job_id"], 1, lease["lease_token"], "transient", "provider_503", retry_delay_seconds=30)
    assert pg_store.claim(60) is None
    with pg_store.connect() as conn:
        conn.execute(sql.SQL("UPDATE {}.jobs SET next_attempt_at = clock_timestamp() - interval '1 second' WHERE job_id = %s")
                     .format(sql.Identifier(pg_store.schema)), (transient["job_id"],))
    lease = pg_store.claim(60)
    assert lease["attempt"] == 2
    assert pg_store.fail("tenant-a", transient["job_id"], 2, lease["lease_token"], "transient", "provider_503")
    assert pg_store.get_job("tenant-a", transient["job_id"])["state"] == "failed"

    hold = submit(pg_store, key="hold")
    lease = pg_store.claim(60)
    assert pg_store.fail("tenant-a", hold["job_id"], 1, lease["lease_token"], "hold", "rights_missing")
    assert pg_store.get_job("tenant-a", hold["job_id"])["state"] == "hold"
    queued = submit(pg_store, key="queued")
    assert not pg_store.cancel("tenant-b", queued["job_id"])
    assert pg_store.cancel("tenant-a", queued["job_id"])
    assert pg_store.get_job("tenant-a", queued["job_id"])["state"] == "canceled"

    active = submit(pg_store, key="active")
    lease = pg_store.claim(60)
    assert lease["job_id"] == active["job_id"]
    assert pg_store.cancel("tenant-a", active["job_id"])
    assert pg_store.get_job("tenant-a", active["job_id"])["cancel_requested"]
    assert pg_store.ack_cancel("tenant-a", active["job_id"], lease["attempt"], lease["lease_token"])
    assert pg_store.get_job("tenant-a", active["job_id"])["state"] == "canceled"


def test_append_only_audit_rows_enforced_by_database(pg_store):
    job = submit(pg_store)
    lease = pg_store.claim(60)
    decision = validated_decision(pg_store, job, lease, b"synthetic audit artifact")
    assert UUID(str(decision))
    for table in ("job_attempts", "job_events", "attempt_evidence",
                  "attempt_invocations", "ai_decisions"):
        with pg_store.connect() as conn, pytest.raises(psycopg.Error):
            conn.execute(sql.SQL("DELETE FROM {}.{}").format(sql.Identifier(pg_store.schema), sql.Identifier(table)))
    assert pg_store.list_decisions("tenant-b", job["job_id"]) == []
    assert pg_store.record_decision("tenant-b", job["job_id"], 1, lease["lease_token"],
                                    synthetic_decision_bytes(job), b"synthetic audit artifact") is None
    with pg_store.connect() as conn, pytest.raises(psycopg.errors.CheckViolation,
                                                   match="decision needs retained current final output and validation report"):
        conn.execute(sql.SQL("""
            INSERT INTO {}.ai_decisions
                (tenant_id, job_id, attempt, decision_id, output_sha256,
                 artifact_sha256, final_evidence_id, validation_evidence_id)
            VALUES (%s, %s, 1, %s, %s, %s, %s, %s)
        """).format(sql.Identifier(pg_store.schema)),
            ("tenant-b", job["job_id"], uuid4(), sha256(synthetic_decision_bytes(job)).hexdigest(),
             sha256(b"synthetic audit artifact").hexdigest(), uuid4(), uuid4()))
