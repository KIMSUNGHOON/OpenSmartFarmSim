"""PostgreSQL contracts for the durable job store; only synthetic metadata is used."""

from concurrent.futures import ThreadPoolExecutor
from hashlib import sha256
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
        yield JobStore(dsn, schema, tmp_path / "artifacts")
    finally:
        with psycopg.connect(dsn, autocommit=True) as conn:
            conn.execute(sql.SQL("DROP SCHEMA {} CASCADE").format(sql.Identifier(schema)))


INPUT = sha256(b"synthetic input").hexdigest()
MAX_INPUT_BYTES = 64 * 1024


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


def submit(store, tenant="tenant-a", stage="research", input_value=None, key="key-a", **kwargs):
    return store.submit(tenant, stage, input_value or {"fixture": "synthetic"}, key, **kwargs)


def test_exact_tuple_dedup_concurrent_and_terminal(pg_store):
    with ThreadPoolExecutor(max_workers=8) as pool:
        results = list(pool.map(lambda _: submit(pg_store), range(16)))
    job_id = results[0]["job_id"]
    assert {row["job_id"] for row in results} == {job_id}
    assert UUID(str(job_id))
    assert submit(pg_store)["job_id"] == job_id
    assert submit(pg_store, tenant="tenant-b")["job_id"] != job_id
    assert submit(pg_store, stage="simulation")["job_id"] != job_id
    assert submit(pg_store, input_value={"fixture": "other"})["job_id"] != job_id
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
    decision = pg_store.record_decision("tenant-a", job["job_id"], 1, lease["lease_token"], INPUT)
    assert UUID(str(decision))
    for table in ("job_attempts", "job_events", "ai_decisions"):
        with pg_store.connect() as conn, pytest.raises(psycopg.Error):
            conn.execute(sql.SQL("DELETE FROM {}.{}").format(sql.Identifier(pg_store.schema), sql.Identifier(table)))
    assert pg_store.list_decisions("tenant-b", job["job_id"]) == []
    assert pg_store.record_decision("tenant-b", job["job_id"], 1, lease["lease_token"], INPUT) is None
    with pg_store.connect() as conn, pytest.raises(psycopg.errors.ForeignKeyViolation):
        conn.execute(sql.SQL("""
            INSERT INTO {}.ai_decisions (tenant_id, job_id, attempt, decision_id, output_sha256)
            VALUES (%s, %s, 1, %s, %s)
        """).format(sql.Identifier(pg_store.schema)),
            ("tenant-b", job["job_id"], uuid4(), INPUT))
