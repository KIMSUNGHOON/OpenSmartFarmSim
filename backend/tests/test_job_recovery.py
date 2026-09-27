"""Recovery and atomic publication against separate PostgreSQL connections."""

from hashlib import sha256
import os
from concurrent.futures import ThreadPoolExecutor
from threading import Barrier
from uuid import uuid4

import psycopg
from psycopg import sql
import pytest

from test_jobs import INPUT, pg_store, submit


def test_stale_decision_audited_but_cannot_publish(pg_store):
    job = submit(pg_store, max_attempts=2)
    first = pg_store.claim(60)
    old_decision = pg_store.record_decision("tenant-a", job["job_id"], 1, first["lease_token"], INPUT)
    with pg_store.connect() as conn:
        conn.execute(sql.SQL("UPDATE {}.jobs SET lease_until = clock_timestamp() - interval '1 second' WHERE job_id = %s")
                     .format(sql.Identifier(pg_store.schema)), (job["job_id"],))
    restarted = type(pg_store)(os.environ["OSSF_TEST_PG_DSN"], pg_store.schema, pg_store.artifact_root)
    second = restarted.claim(60)
    assert second["attempt"] == 2
    assert second["input_bytes"] == b'{"fixture":"synthetic"}'
    assert restarted.read_input("tenant-a", job["job_id"], 1, first["lease_token"]) is None
    assert restarted.read_input("tenant-a", job["job_id"], 2, second["lease_token"]) == second["input_bytes"]
    late_decision = restarted.record_decision("tenant-a", job["job_id"], 1, first["lease_token"], INPUT)
    assert late_decision is None
    assert {item["decision_id"] for item in restarted.list_decisions("tenant-a", job["job_id"])} == {old_decision}
    payload = b"complete synthetic artifact"
    digest = sha256(payload).hexdigest()
    assert restarted.publish("tenant-a", job["job_id"], 1, first["lease_token"], old_decision, payload, digest, {"schema_version": "1"}) is None
    assert restarted.publish("tenant-a", job["job_id"], 1, first["lease_token"], late_decision, payload, digest, {"schema_version": "1"}) is None
    assert not pg_store.artifact_root.exists()
    decision = restarted.record_decision("tenant-a", job["job_id"], 2, second["lease_token"], INPUT)
    publication = restarted.publish("tenant-a", job["job_id"], 2, second["lease_token"], decision, payload, digest, {"schema_version": "1"})
    assert publication["decision_id"] == decision
    assert restarted.get_publication("tenant-b", job["job_id"]) is None
    assert restarted.get_publication("tenant-a", job["job_id"])["artifact_sha256"] == digest
    assert restarted.read_artifact("tenant-a", job["job_id"]) == payload
    assert restarted.read_artifact("tenant-b", job["job_id"]) is None
    assert restarted.publish("tenant-a", job["job_id"], 2, second["lease_token"], decision, payload, digest, {"schema_version": "1"}) is None
    assert restarted.record_decision("tenant-a", job["job_id"], 2, second["lease_token"], INPUT) is None
    assert restarted.read_input("tenant-a", job["job_id"], 2, second["lease_token"]) is None
    with restarted.connect() as conn, pytest.raises(psycopg.errors.UniqueViolation):
        conn.execute(sql.SQL("""
            INSERT INTO {}.job_publications
                (tenant_id, job_id, publication_id, attempt, decision_id,
                 artifact_sha256, artifact_size, manifest)
            SELECT tenant_id, job_id, %s, attempt, decision_id,
                   artifact_sha256, artifact_size, manifest
            FROM {}.job_publications WHERE tenant_id = %s AND job_id = %s
        """).format(sql.Identifier(pg_store.schema), sql.Identifier(pg_store.schema)),
            (uuid4(), "tenant-a", job["job_id"]))
    for table in ("job_publications", "ai_decisions"):
        with restarted.connect() as conn, pytest.raises(psycopg.Error):
            conn.execute(sql.SQL("UPDATE {}.{} SET job_id = job_id").format(sql.Identifier(pg_store.schema), sql.Identifier(table)))


@pytest.mark.parametrize("stage", ("collection", "simulation"))
def test_deterministic_stage_publishes_without_fabricated_ai_decision(pg_store, stage):
    job = submit(pg_store, stage=stage)
    lease = pg_store.claim(60)
    assert lease["stage"] == stage
    assert pg_store.record_decision("tenant-a", job["job_id"], 1,
                                    lease["lease_token"], INPUT) is None
    assert pg_store.list_decisions("tenant-a", job["job_id"]) == []
    payload = (stage + " synthetic output").encode()
    digest = sha256(payload).hexdigest()
    publication = pg_store.publish("tenant-a", job["job_id"], 1,
                                   lease["lease_token"], None, payload,
                                   digest, {"schema_version": "1"})
    assert publication is not None
    assert publication["decision_id"] is None
    assert publication["manifest"]["stage"] == stage
    assert publication["manifest"].get("decision_id") is None
    restarted = type(pg_store)(os.environ["OSSF_TEST_PG_DSN"], pg_store.schema,
                               pg_store.artifact_root)
    assert restarted.get_publication("tenant-a", job["job_id"])["artifact_sha256"] == digest
    assert restarted.read_artifact("tenant-a", job["job_id"]) == payload


def test_ai_stage_cannot_publish_without_real_decision(pg_store):
    job = submit(pg_store)
    lease = pg_store.claim(60)
    payload = b"unreviewed synthetic output"
    digest = sha256(payload).hexdigest()
    assert pg_store.publish("tenant-a", job["job_id"], 1, lease["lease_token"],
                            None, payload, digest, {"schema_version": "1"}) is None
    assert not pg_store.artifact_root.exists()
    assert pg_store.get_publication("tenant-a", job["job_id"]) is None


@pytest.mark.parametrize("stage, has_decision", (("research", False),
                                                ("collection", True)))
def test_database_rejects_publication_decision_for_wrong_stage(pg_store, stage,
                                                               has_decision):
    job = submit(pg_store, stage=stage)
    lease = pg_store.claim(60)
    decision_id = uuid4() if has_decision else None
    with pytest.raises(psycopg.errors.CheckViolation):
        with pg_store.connect() as conn:
            if decision_id is not None:
                conn.execute(sql.SQL("""
                    INSERT INTO {}.ai_decisions
                        (tenant_id, job_id, attempt, decision_id, output_sha256)
                    VALUES (%s, %s, 1, %s, %s)
                """).format(sql.Identifier(pg_store.schema)),
                    ("tenant-a", job["job_id"], decision_id, INPUT))
            conn.execute(sql.SQL("""
                UPDATE {}.jobs SET state = 'succeeded', lease_token = NULL,
                    lease_until = NULL WHERE tenant_id = %s AND job_id = %s
            """).format(sql.Identifier(pg_store.schema)),
                ("tenant-a", job["job_id"]))
            conn.execute(sql.SQL("""
                INSERT INTO {}.job_publications
                    (tenant_id, job_id, publication_id, attempt, decision_id,
                     artifact_sha256, artifact_size, manifest)
                VALUES (%s, %s, %s, 1, %s, %s, 0, '{{}}'::jsonb)
            """).format(sql.Identifier(pg_store.schema)),
                ("tenant-a", job["job_id"], uuid4(), decision_id,
                 sha256(b"").hexdigest()))
    assert pg_store.get_job("tenant-a", job["job_id"])["state"] != "succeeded"
    assert pg_store.get_publication("tenant-a", job["job_id"]) is None


def test_public_manifest_rejects_caller_fields_before_writing_and_uses_server_metadata(pg_store):
    job = submit(pg_store)
    lease = pg_store.claim(60)
    decision = pg_store.record_decision("tenant-a", job["job_id"], 1,
                                        lease["lease_token"], INPUT)
    payload = b"synthetic public manifest artifact"
    digest = sha256(payload).hexdigest()
    invalid_manifests = (
        {"schema_version": "2"},
        {"schema_version": 1},
        {"schema_version": "1", "raw_data": "synthetic restricted data"},
        {"schema_version": "1", "api_key": "synthetic placeholder"},
        {"schema_version": "1", "job_id": "caller-controlled"},
        {"schema_version": "1", "publication_id": "caller-controlled"},
        {"schema_version": "1", "artifact_sha256": "caller-controlled"},
    )
    for manifest in invalid_manifests:
        with pytest.raises(ValueError, match="manifest"):
            pg_store.publish("tenant-a", job["job_id"], 1, lease["lease_token"],
                             decision, payload, digest, manifest)
        assert not pg_store.artifact_root.exists()
        assert pg_store.get_publication("tenant-a", job["job_id"]) is None
        assert pg_store.get_job("tenant-a", job["job_id"])["state"] == "researching"

    publication = pg_store.publish("tenant-a", job["job_id"], 1,
                                   lease["lease_token"], decision, payload,
                                   digest, {"schema_version": "1"})
    assert publication is not None
    assert pg_store.get_publication("tenant-a", job["job_id"])["manifest"] == {
        "schema_version": "1",
        "job_id": str(job["job_id"]),
        "stage": "research",
        "input_sha256": job["input_sha256"],
        "attempt": 1,
        "decision_id": str(decision),
        "artifact_sha256": digest,
    }


def test_succeeded_job_requires_publication_at_commit(pg_store):
    direct_job_id = uuid4()
    with pytest.raises(psycopg.errors.CheckViolation):
        with pg_store.connect() as conn:
            conn.execute(sql.SQL("""
                INSERT INTO {}.jobs (tenant_id, job_id, stage, input_sha256,
                                     input_bytes, idempotency_key, state, max_attempts)
                VALUES (%s, %s, 'research', %s, %s, %s, 'succeeded', 1)
            """).format(sql.Identifier(pg_store.schema)),
                ("tenant-a", direct_job_id, sha256(b"{}").hexdigest(), b"{}",
                 "direct-succeeded"))
    assert pg_store.get_job("tenant-a", direct_job_id) is None

    job = submit(pg_store)
    with pytest.raises(psycopg.errors.CheckViolation):
        with pg_store.connect() as conn:
            conn.execute(sql.SQL("""
                UPDATE {}.jobs SET state = 'succeeded'
                WHERE tenant_id = %s AND job_id = %s
            """).format(sql.Identifier(pg_store.schema)),
                ("tenant-a", job["job_id"]))
    assert pg_store.get_job("tenant-a", job["job_id"])["state"] == "queued"
    assert pg_store.get_publication("tenant-a", job["job_id"]) is None


def test_publication_requires_succeeded_job_at_commit(pg_store):
    job = submit(pg_store)
    lease = pg_store.claim(60)
    decision = pg_store.record_decision("tenant-a", job["job_id"], 1,
                                        lease["lease_token"], INPUT)
    with pytest.raises(psycopg.errors.CheckViolation):
        with pg_store.connect() as conn:
            conn.execute(sql.SQL("""
                INSERT INTO {}.job_publications
                    (tenant_id, job_id, publication_id, attempt, decision_id,
                     artifact_sha256, artifact_size, manifest)
                VALUES (%s, %s, %s, 1, %s, %s, 0, '{{}}'::jsonb)
            """).format(sql.Identifier(pg_store.schema)),
                ("tenant-a", job["job_id"], uuid4(), decision,
                 sha256(b"").hexdigest()))
    assert pg_store.get_job("tenant-a", job["job_id"])["state"] == "researching"
    assert pg_store.get_publication("tenant-a", job["job_id"]) is None


def test_expired_and_cancel_requested_attempts_cannot_record_decision(pg_store):
    job = submit(pg_store)
    lease = pg_store.claim(60)
    with pg_store.connect() as conn:
        conn.execute(sql.SQL("""
            UPDATE {}.jobs SET lease_until = clock_timestamp() - interval '1 second'
            WHERE tenant_id = %s AND job_id = %s
        """).format(sql.Identifier(pg_store.schema)), ("tenant-a", job["job_id"]))
    assert pg_store.read_input("tenant-a", job["job_id"], 1, lease["lease_token"]) is None
    assert pg_store.record_decision("tenant-a", job["job_id"], 1, lease["lease_token"], INPUT) is None
    assert pg_store.list_decisions("tenant-a", job["job_id"]) == []
    second = pg_store.claim(60)
    assert pg_store.cancel("tenant-a", job["job_id"])
    assert pg_store.record_decision("tenant-a", job["job_id"], 2, second["lease_token"], INPUT) is None
    assert pg_store.list_decisions("tenant-a", job["job_id"]) == []


def test_corrupt_input_fails_closed_before_worker_read_or_claim(pg_store):
    job = submit(pg_store)
    lease = pg_store.claim(60)
    with pg_store.connect() as conn:
        conn.execute(sql.SQL("ALTER TABLE {}.jobs DROP CONSTRAINT jobs_input_digest_matches")
                     .format(sql.Identifier(pg_store.schema)))
        conn.execute(sql.SQL("ALTER TABLE {}.jobs DISABLE TRIGGER guard_change")
                     .format(sql.Identifier(pg_store.schema)))
    try:
        with pg_store.connect() as conn:
            conn.execute(sql.SQL("""
                UPDATE {}.jobs SET input_bytes = %s WHERE tenant_id = %s AND job_id = %s
            """).format(sql.Identifier(pg_store.schema)),
                (b'{"fixture":"altered"}', "tenant-a", job["job_id"]))
    finally:
        with pg_store.connect() as conn:
            conn.execute(sql.SQL("ALTER TABLE {}.jobs ENABLE TRIGGER guard_change")
                         .format(sql.Identifier(pg_store.schema)))
    with pytest.raises(ValueError, match="input SHA-256 mismatch"):
        pg_store.read_input("tenant-a", job["job_id"], 1, lease["lease_token"])
    with pg_store.connect() as conn:
        conn.execute(sql.SQL("""
            UPDATE {}.jobs SET lease_until = clock_timestamp() - interval '1 second'
            WHERE tenant_id = %s AND job_id = %s
        """).format(sql.Identifier(pg_store.schema)), ("tenant-a", job["job_id"]))
    assert pg_store.claim(60) is None
    held = pg_store.get_job("tenant-a", job["job_id"])
    assert held["state"] == "hold"
    assert held["reason"] == {"code": "input_sha256_mismatch"}
    assert held["attempt_count"] == 1


def test_corrupt_oldest_job_is_held_and_next_job_can_be_claimed(pg_store):
    corrupted = submit(pg_store, key="corrupt-first")
    healthy = submit(pg_store, key="healthy-second")
    with pg_store.connect() as conn:
        conn.execute(sql.SQL("ALTER TABLE {}.jobs DROP CONSTRAINT IF EXISTS jobs_input_digest_matches")
                     .format(sql.Identifier(pg_store.schema)))
        conn.execute(sql.SQL("ALTER TABLE {}.jobs DISABLE TRIGGER guard_change")
                     .format(sql.Identifier(pg_store.schema)))
    try:
        with pg_store.connect() as conn:
            conn.execute(sql.SQL("""
                UPDATE {}.jobs SET input_bytes = %s
                WHERE tenant_id = %s AND job_id = %s
            """).format(sql.Identifier(pg_store.schema)),
                (b'{"fixture":"corrupt"}', "tenant-a", corrupted["job_id"]))
    finally:
        with pg_store.connect() as conn:
            conn.execute(sql.SQL("ALTER TABLE {}.jobs ENABLE TRIGGER guard_change")
                         .format(sql.Identifier(pg_store.schema)))
    lease = pg_store.claim(60)
    assert lease["job_id"] == healthy["job_id"]
    held = pg_store.get_job("tenant-a", corrupted["job_id"])
    assert held["state"] == "hold"
    assert held["reason"]["code"] == "input_sha256_mismatch"
    with pg_store.connect() as conn:
        events = conn.execute(sql.SQL("""
            SELECT kind, reason FROM {}.job_events
            WHERE tenant_id = %s AND job_id = %s AND kind = 'hold'
        """).format(sql.Identifier(pg_store.schema)),
            ("tenant-a", corrupted["job_id"])).fetchall()
    assert events == [{"kind": "hold", "reason": {"code": "input_sha256_mismatch"}}]
    assert pg_store.claim(60) is None


def test_database_rejects_mismatched_input_bytes_at_insert(pg_store):
    with pytest.raises(psycopg.errors.CheckViolation) as error:
        with pg_store.connect() as conn:
            conn.execute(sql.SQL("""
                INSERT INTO {}.jobs
                    (tenant_id, job_id, stage, input_sha256, input_bytes,
                     idempotency_key, state, max_attempts)
                VALUES (%s, %s, 'research', %s, %s, %s, 'queued', 1)
            """).format(sql.Identifier(pg_store.schema)),
                ("tenant-a", uuid4(), sha256(b'{}').hexdigest(),
                 b'{"fixture":"mismatch"}', "bad-direct-insert"))
    assert error.value.diag.constraint_name == "jobs_input_digest_matches"


def test_database_rejects_mismatched_input_bytes_at_update(pg_store):
    job = submit(pg_store)
    with pg_store.connect() as conn:
        conn.execute(sql.SQL("ALTER TABLE {}.jobs DISABLE TRIGGER guard_change")
                     .format(sql.Identifier(pg_store.schema)))
    try:
        with pytest.raises(psycopg.errors.CheckViolation) as error:
            with pg_store.connect() as conn:
                conn.execute(sql.SQL("""
                    UPDATE {}.jobs SET input_bytes = %s
                    WHERE tenant_id = %s AND job_id = %s
                """).format(sql.Identifier(pg_store.schema)),
                    (b'{"fixture":"mismatch"}', "tenant-a", job["job_id"]))
        assert error.value.diag.constraint_name == "jobs_input_digest_matches"
    finally:
        with pg_store.connect() as conn:
            conn.execute(sql.SQL("ALTER TABLE {}.jobs ENABLE TRIGGER guard_change")
                         .format(sql.Identifier(pg_store.schema)))


def test_first_artifact_root_creation_syncs_parent_directory(pg_store, monkeypatch):
    job = submit(pg_store)
    lease = pg_store.claim(60)
    decision = pg_store.record_decision("tenant-a", job["job_id"], 1,
                                        lease["lease_token"], INPUT)
    payload = b"synthetic fsync artifact"
    digest = sha256(payload).hexdigest()
    parent = pg_store.artifact_root.parent
    real_fsync = os.fsync
    synced_parent = False

    def observe_fsync(fd):
        nonlocal synced_parent
        if os.path.realpath(f"/proc/self/fd/{fd}") == str(parent):
            synced_parent = True
        return real_fsync(fd)

    monkeypatch.setattr(os, "fsync", observe_fsync)
    assert pg_store.publish("tenant-a", job["job_id"], 1, lease["lease_token"],
                            decision, payload, digest, {"schema_version": "1"})
    assert synced_parent


@pytest.mark.parametrize("parent_kind", ("missing", "symlink"))
def test_artifact_root_requires_existing_real_parent(pg_store, parent_kind):
    job = submit(pg_store)
    lease = pg_store.claim(60)
    decision = pg_store.record_decision("tenant-a", job["job_id"], 1,
                                        lease["lease_token"], INPUT)
    parent = pg_store.artifact_root.parent / "alternate-parent"
    if parent_kind == "symlink":
        parent.symlink_to(pg_store.artifact_root.parent, target_is_directory=True)
    pg_store.artifact_root = parent / "artifacts"
    payload = b"synthetic parent check"
    digest = sha256(payload).hexdigest()
    with pytest.raises(OSError):
        pg_store.publish("tenant-a", job["job_id"], 1, lease["lease_token"],
                         decision, payload, digest, {"schema_version": "1"})
    assert pg_store.get_job("tenant-a", job["job_id"])["state"] == "researching"
    assert pg_store.get_publication("tenant-a", job["job_id"]) is None


def test_rollback_leaves_no_visible_run_and_cancel_wins(pg_store, monkeypatch):
    job = submit(pg_store)
    lease = pg_store.claim(60)
    decision = pg_store.record_decision("tenant-a", job["job_id"], 1, lease["lease_token"], INPUT)
    payload = b"complete synthetic artifact"
    digest = sha256(payload).hexdigest()
    original = pg_store._insert_publication

    def abort_after_insert(*args, **kwargs):
        original(*args, **kwargs)
        raise RuntimeError("synthetic crash before transaction commit")

    monkeypatch.setattr(pg_store, "_insert_publication", abort_after_insert)
    with pytest.raises(RuntimeError):
        pg_store.publish("tenant-a", job["job_id"], 1, lease["lease_token"], decision, payload, digest, {"schema_version": "1"})
    assert (pg_store.artifact_root / digest).read_bytes() == payload
    assert pg_store.get_publication("tenant-a", job["job_id"]) is None
    assert pg_store.get_job("tenant-a", job["job_id"])["state"] == "researching"
    monkeypatch.setattr(pg_store, "_insert_publication", original)
    assert pg_store.cancel("tenant-a", job["job_id"])
    assert pg_store.publish("tenant-a", job["job_id"], 1, lease["lease_token"], decision, payload, digest, {"schema_version": "1"}) is None
    assert pg_store.ack_cancel("tenant-a", job["job_id"], 1, lease["lease_token"])
    assert pg_store.get_publication("tenant-a", job["job_id"]) is None


def test_expired_cancel_recovered_after_restart(pg_store):
    job = submit(pg_store)
    lease = pg_store.claim(60)
    assert pg_store.cancel("tenant-a", job["job_id"])
    with pg_store.connect() as conn:
        conn.execute(sql.SQL("UPDATE {}.jobs SET lease_until = clock_timestamp() - interval '1 second' WHERE job_id = %s")
                     .format(sql.Identifier(pg_store.schema)), (job["job_id"],))
    restarted = type(pg_store)(os.environ["OSSF_TEST_PG_DSN"], pg_store.schema, pg_store.artifact_root)
    restarted.recover_expired()
    assert restarted.get_job("tenant-a", job["job_id"])["state"] == "canceled"
    assert not restarted.ack_cancel("tenant-a", job["job_id"], 1, lease["lease_token"])


def test_cancel_and_publication_race_serializes_on_job_row(pg_store):
    job = submit(pg_store)
    lease = pg_store.claim(60)
    decision = pg_store.record_decision("tenant-a", job["job_id"], 1, lease["lease_token"], INPUT)
    payload = b"race artifact"
    digest = sha256(payload).hexdigest()
    barrier = Barrier(2)

    def cancel():
        barrier.wait()
        return pg_store.cancel("tenant-a", job["job_id"])

    def publish():
        barrier.wait()
        return pg_store.publish("tenant-a", job["job_id"], 1, lease["lease_token"],
                                decision, payload, digest, {"schema_version": "1"})

    with ThreadPoolExecutor(max_workers=2) as pool:
        canceled = pool.submit(cancel)
        published = pool.submit(publish)
        cancel_result, publication = canceled.result(), published.result()
    if publication is None:
        assert cancel_result
        assert pg_store.ack_cancel("tenant-a", job["job_id"], 1, lease["lease_token"])
        assert pg_store.get_publication("tenant-a", job["job_id"]) is None
    else:
        assert not cancel_result
        assert pg_store.get_publication("tenant-a", job["job_id"])["publication_id"] == publication["publication_id"]


def test_content_address_is_never_replaced(pg_store):
    job = submit(pg_store)
    lease = pg_store.claim(60)
    decision = pg_store.record_decision("tenant-a", job["job_id"], 1, lease["lease_token"], INPUT)
    payload = b"verified complete artifact"
    digest = sha256(payload).hexdigest()
    pg_store.artifact_root.mkdir(mode=0o700)
    existing = pg_store.artifact_root / digest
    existing.write_bytes(b"corrupt existing bytes")
    with pytest.raises(ValueError, match="corrupt"):
        pg_store.publish("tenant-a", job["job_id"], 1, lease["lease_token"],
                         decision, payload, digest, {"schema_version": "1"})
    assert existing.read_bytes() == b"corrupt existing bytes"
    assert pg_store.get_publication("tenant-a", job["job_id"]) is None
    assert pg_store.read_artifact("tenant-a", job["job_id"]) is None


def test_invalid_publication_identity_leaves_artifact_directory_unchanged(pg_store):
    job = submit(pg_store)
    lease = pg_store.claim(60)
    decision = pg_store.record_decision("tenant-a", job["job_id"], 1,
                                        lease["lease_token"], INPUT)
    payload = b"rejected synthetic artifact"
    digest = sha256(payload).hexdigest()
    invalid = (("tenant-b", 1, lease["lease_token"], decision),
               ("tenant-a", 1, "wrong-token", decision),
               ("tenant-a", 2, lease["lease_token"], decision),
               ("tenant-a", 1, lease["lease_token"], uuid4()))
    for tenant, attempt, token, decision_id in invalid:
        before = set(pg_store.artifact_root.iterdir()) if pg_store.artifact_root.exists() else set()
        assert pg_store.publish(tenant, job["job_id"], attempt, token, decision_id,
                                payload, digest, {"schema_version": "1"}) is None
        after = set(pg_store.artifact_root.iterdir()) if pg_store.artifact_root.exists() else set()
        assert after == before
    assert pg_store.get_publication("tenant-a", job["job_id"]) is None


def test_lease_expiry_during_artifact_write_leaves_unpublished_orphan(pg_store, monkeypatch):
    job = submit(pg_store)
    lease = pg_store.claim(60)
    decision = pg_store.record_decision("tenant-a", job["job_id"], 1,
                                        lease["lease_token"], INPUT)
    payload = b"artifact written before lease expiry"
    digest = sha256(payload).hexdigest()
    original = pg_store._durable_artifact

    def expire_while_writing(artifact, expected_sha256):
        original(artifact, expected_sha256)
        with pg_store.connect() as conn:
            conn.execute("SET LOCAL lock_timeout = '500ms'")
            conn.execute(sql.SQL("""
                UPDATE {}.jobs SET lease_until = clock_timestamp() - interval '1 second'
                WHERE tenant_id = %s AND job_id = %s
            """).format(sql.Identifier(pg_store.schema)),
                ("tenant-a", job["job_id"]))

    monkeypatch.setattr(pg_store, "_durable_artifact", expire_while_writing)
    assert pg_store.publish("tenant-a", job["job_id"], 1, lease["lease_token"],
                            decision, payload, digest, {"schema_version": "1"}) is None
    assert (pg_store.artifact_root / digest).read_bytes() == payload
    assert pg_store.get_publication("tenant-a", job["job_id"]) is None


def test_succeeded_job_cannot_mutate_and_publication_remains_readable(pg_store):
    job = submit(pg_store)
    lease = pg_store.claim(60)
    decision = pg_store.record_decision("tenant-a", job["job_id"], 1,
                                        lease["lease_token"], INPUT)
    payload = b"accepted synthetic artifact"
    digest = sha256(payload).hexdigest()
    publication = pg_store.publish("tenant-a", job["job_id"], 1,
                                    lease["lease_token"], decision, payload,
                                    digest, {"schema_version": "1"})
    assert publication is not None
    for state in ("queued", "failed"):
        with pg_store.connect() as conn, pytest.raises(psycopg.Error):
            conn.execute(sql.SQL("""
                UPDATE {}.jobs SET state = %s WHERE tenant_id = %s AND job_id = %s
            """).format(sql.Identifier(pg_store.schema)),
                (state, "tenant-a", job["job_id"]))
        assert pg_store.get_job("tenant-a", job["job_id"])["state"] == "succeeded"
        assert pg_store.get_publication("tenant-a", job["job_id"])["publication_id"] == publication["publication_id"]
        assert pg_store.read_artifact("tenant-a", job["job_id"]) == payload
