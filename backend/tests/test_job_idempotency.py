"""A client idempotency key identifies one intent within a tenant and stage."""

from concurrent.futures import ThreadPoolExecutor
from hashlib import sha256
from uuid import uuid4

import pytest
from psycopg import sql

from test_jobs import pg_store
from app.db import upgrade_job_intent_key


def test_same_key_same_input_replays_one_job(pg_store):
    first = pg_store.submit("tenant-a", "research", {"fixture": "one"}, "intent-1")
    replay = pg_store.submit("tenant-a", "research", {"fixture": "one"}, "intent-1")
    assert replay["job_id"] == first["job_id"]


def test_same_key_changed_input_is_rejected_without_creating_job(pg_store):
    first = pg_store.submit("tenant-a", "research", {"fixture": "one"}, "intent-1")
    with pytest.raises(ValueError, match="idempotency"):
        pg_store.submit("tenant-a", "research", {"fixture": "two"}, "intent-1")
    with pg_store.connect() as conn:
        rows = conn.execute(sql.SQL(
            "SELECT job_id FROM {}.jobs "
            "WHERE tenant_id = %s AND stage = %s AND idempotency_key = %s"
        ).format(sql.Identifier(pg_store.schema)),
            ("tenant-a", "research", "intent-1"),
        ).fetchall()
    assert [row["job_id"] for row in rows] == [first["job_id"]]


def test_concurrent_changed_inputs_cannot_share_one_key(pg_store):
    def submit(value):
        try:
            return pg_store.submit("tenant-a", "research", {"fixture": value}, "intent-1")
        except ValueError as error:
            return error

    with ThreadPoolExecutor(max_workers=2) as pool:
        outcomes = list(pool.map(submit, ("one", "two")))
    assert sum(isinstance(item, dict) for item in outcomes) == 1
    assert sum(isinstance(item, ValueError) for item in outcomes) == 1


def test_key_scope_is_separate_for_stage_and_tenant(pg_store):
    first = pg_store.submit("tenant-a", "research", {"fixture": "one"}, "intent-1")
    other_stage = pg_store.submit("tenant-a", "collection", {"fixture": "two"}, "intent-1")
    other_tenant = pg_store.submit("tenant-b", "research", {"fixture": "three"}, "intent-1")
    assert len({first["job_id"], other_stage["job_id"], other_tenant["job_id"]}) == 3


def _restore_legacy_constraint(pg_store):
    with pg_store.connect() as conn:
        conn.execute(sql.SQL("ALTER TABLE {}.jobs DROP CONSTRAINT jobs_intent_key")
                     .format(sql.Identifier(pg_store.schema)))
        conn.execute(sql.SQL("""
            ALTER TABLE {}.jobs ADD CONSTRAINT jobs_legacy_tuple
                UNIQUE (tenant_id, stage, input_sha256, idempotency_key)
        """).format(sql.Identifier(pg_store.schema)))


def test_upgrade_existing_table_before_new_submit(pg_store):
    first = pg_store.submit("tenant-a", "research", {"fixture": "one"}, "intent-1")
    _restore_legacy_constraint(pg_store)
    with pg_store.connect() as conn:
        upgrade_job_intent_key(conn, pg_store.schema)
        upgrade_job_intent_key(conn, pg_store.schema)
    assert pg_store.submit("tenant-a", "research", {"fixture": "one"},
                           "intent-1")["job_id"] == first["job_id"]
    with pytest.raises(ValueError, match="idempotency"):
        pg_store.submit("tenant-a", "research", {"fixture": "two"}, "intent-1")


def test_upgrade_refuses_historical_conflicts_without_mutating_jobs(pg_store):
    first = pg_store.submit("tenant-a", "research", {"fixture": "one"}, "intent-1")
    _restore_legacy_constraint(pg_store)
    other_bytes = b'{"fixture":"two"}'
    with pg_store.connect() as conn:
        conn.execute(sql.SQL("""
            INSERT INTO {}.jobs (tenant_id, job_id, stage, input_sha256,
                input_bytes, idempotency_key, state, max_attempts)
            VALUES (%s, %s, 'research', %s, %s, 'intent-1', 'queued', 3)
        """).format(sql.Identifier(pg_store.schema)),
            ("tenant-a", uuid4(), sha256(other_bytes).hexdigest(), other_bytes))
    with pg_store.connect() as conn, pytest.raises(ValueError, match="reconciliation"):
        upgrade_job_intent_key(conn, pg_store.schema)
    with pg_store.connect() as conn:
        rows = conn.execute(sql.SQL("""
            SELECT job_id FROM {}.jobs WHERE tenant_id = 'tenant-a'
                AND stage = 'research' AND idempotency_key = 'intent-1'
        """).format(sql.Identifier(pg_store.schema))).fetchall()
    assert len(rows) == 2
    assert first["job_id"] in {row["job_id"] for row in rows}
