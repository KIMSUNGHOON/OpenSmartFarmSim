"""Tenant-scoped PostgreSQL job transitions and content-addressed publication."""

from hashlib import sha256
import os
from pathlib import Path
import secrets
import stat
from uuid import uuid4

import psycopg
from psycopg import sql
from psycopg.rows import dict_row
from psycopg.types.json import Jsonb

from app.db import connect_app
from app.jobs import (
    ACTIVE_BY_STAGE, ACTIVE_STATES, AI_STAGES, DETERMINISTIC_STAGES,
    FAILURE_KINDS, TERMINAL_STATES,
    canonical_input_bytes, require_digest, require_name, require_reason_code,
    require_public_manifest_v1, require_seconds,
)


def _open_directory_nofollow(path: Path) -> int:
    flags = os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW
    if path.is_absolute():
        fd = os.open(path.anchor, flags)
        components = path.parts[1:]
    else:
        fd = os.open(".", flags)
        components = path.parts
    try:
        for component in components:
            next_fd = os.open(component, flags, dir_fd=fd)
            os.close(fd)
            fd = next_fd
        return fd
    except BaseException:
        os.close(fd)
        raise


class JobStore:
    def __init__(self, dsn: str | None, schema: str, artifact_root: Path):
        self._dsn = dsn
        self.schema = schema
        self.artifact_root = Path(artifact_root)

    def connect(self) -> psycopg.Connection:
        if self._dsn is None:
            return connect_app()
        return psycopg.connect(self._dsn, row_factory=dict_row)

    def _table(self, name: str) -> sql.Composed:
        return sql.SQL("{}.{}").format(sql.Identifier(self.schema), sql.Identifier(name))

    def _event(self, conn, tenant_id, job_id, kind, attempt=None, reason=None):
        conn.execute(sql.SQL("""
            INSERT INTO {} (tenant_id, job_id, event_id, attempt, kind, reason)
            VALUES (%s, %s, %s, %s, %s, %s)
        """).format(self._table("job_events")),
                     (tenant_id, job_id, uuid4(), attempt, kind, Jsonb(reason) if reason else None))

    @staticmethod
    def _public_job(row):
        if row is None:
            return None
        return {key: value for key, value in row.items()
                if key not in ("lease_token", "input_bytes")}

    @staticmethod
    def _verified_input(row) -> bytes:
        data = row["input_bytes"]
        if not isinstance(data, bytes) or sha256(data).hexdigest() != row["input_sha256"]:
            raise ValueError("input SHA-256 mismatch")
        return data

    def submit(self, tenant_id: str, stage: str, input_value: object,
               idempotency_key: str, *, max_attempts: int = 3) -> dict:
        require_name(tenant_id, "tenant_id")
        require_name(idempotency_key, "idempotency_key")
        if stage not in ACTIVE_BY_STAGE:
            raise ValueError("unknown job stage")
        require_seconds(max_attempts, "max_attempts", 1, 3)
        input_bytes = canonical_input_bytes(input_value)
        digest = sha256(input_bytes).hexdigest()
        job_id = uuid4()
        with self.connect() as conn:
            row = conn.execute(sql.SQL("""
                INSERT INTO {} (tenant_id, job_id, stage, input_sha256, input_bytes,
                                idempotency_key, state, max_attempts)
                VALUES (%s, %s, %s, %s, %s, %s, 'queued', %s)
                ON CONFLICT (tenant_id, stage, input_sha256, idempotency_key)
                DO NOTHING
                RETURNING *
            """).format(self._table("jobs")),
                (tenant_id, job_id, stage, digest, input_bytes,
                 idempotency_key, max_attempts)).fetchone()
            if row is None:
                row = conn.execute(sql.SQL("""
                    SELECT * FROM {} WHERE tenant_id = %s AND stage = %s
                        AND input_sha256 = %s AND idempotency_key = %s
                """).format(self._table("jobs")),
                    (tenant_id, stage, digest, idempotency_key)).fetchone()
            else:
                self._event(conn, tenant_id, job_id, "submitted")
            self._verified_input(row)
        return self._public_job(row)

    def get_job(self, tenant_id: str, job_id) -> dict | None:
        with self.connect() as conn:
            row = conn.execute(sql.SQL("SELECT * FROM {} WHERE tenant_id = %s AND job_id = %s")
                               .format(self._table("jobs")), (tenant_id, job_id)).fetchone()
            return self._public_job(row)

    def recover_expired(self) -> int:
        with self.connect() as conn:
            rows = conn.execute(sql.SQL("""
                SELECT tenant_id, job_id, attempt_count, cancel_requested
                FROM {} WHERE state IN ('researching','collecting','reviewing','simulating','assessing')
                    AND lease_until <= clock_timestamp()
                    AND (cancel_requested OR attempt_count >= max_attempts)
                FOR UPDATE SKIP LOCKED
            """).format(self._table("jobs"))).fetchall()
            for row in rows:
                target = "canceled" if row["cancel_requested"] else "failed"
                reason = {"code": "cancel_lease_expired" if row["cancel_requested"]
                          else "attempts_exhausted"}
                conn.execute(sql.SQL("""
                    UPDATE {} SET state = %s, reason = %s, lease_token = NULL,
                        lease_until = NULL, cancel_requested = false,
                        updated_at = clock_timestamp()
                    WHERE tenant_id = %s AND job_id = %s
                """).format(self._table("jobs")),
                    (target, Jsonb(reason), row["tenant_id"], row["job_id"]))
                self._event(conn, row["tenant_id"], row["job_id"], target,
                            row["attempt_count"], reason)
            return len(rows)

    def claim(self, lease_seconds: int) -> dict | None:
        require_seconds(lease_seconds, "lease_seconds")
        self.recover_expired()
        with self.connect() as conn:
            while True:
                row = conn.execute(sql.SQL("""
                    SELECT * FROM {} WHERE
                        (state = 'queued' AND next_attempt_at <= clock_timestamp())
                        OR (state IN ('researching','collecting','reviewing','simulating','assessing')
                            AND lease_until <= clock_timestamp() AND NOT cancel_requested
                            AND attempt_count < max_attempts)
                    ORDER BY created_at, job_id
                    FOR UPDATE SKIP LOCKED LIMIT 1
                """).format(self._table("jobs"))).fetchone()
                if row is None:
                    return None
                try:
                    self._verified_input(row)
                except ValueError:
                    reason = {"code": "input_sha256_mismatch"}
                    conn.execute(sql.SQL("""
                        UPDATE {} SET state = 'hold', reason = %s,
                            lease_token = NULL, lease_until = NULL,
                            cancel_requested = false, updated_at = clock_timestamp()
                        WHERE tenant_id = %s AND job_id = %s
                    """).format(self._table("jobs")),
                        (Jsonb(reason), row["tenant_id"], row["job_id"]))
                    self._event(conn, row["tenant_id"], row["job_id"], "hold",
                                row["attempt_count"] or None, reason)
                    continue
                break
            attempt = row["attempt_count"] + 1
            token = secrets.token_urlsafe(32)
            if row["state"] != "queued":
                self._event(conn, row["tenant_id"], row["job_id"], "lease_expired",
                            row["attempt_count"])
            claimed = conn.execute(sql.SQL("""
                UPDATE {} SET state = %s, attempt_count = %s, lease_token = %s,
                    lease_until = clock_timestamp() + %s * interval '1 second',
                    updated_at = clock_timestamp(), reason = NULL
                WHERE tenant_id = %s AND job_id = %s RETURNING *
            """).format(self._table("jobs")),
                (ACTIVE_BY_STAGE[row["stage"]], attempt, token, lease_seconds,
                 row["tenant_id"], row["job_id"])).fetchone()
            conn.execute(sql.SQL("""
                INSERT INTO {} (tenant_id, job_id, attempt, lease_token)
                VALUES (%s, %s, %s, %s)
            """).format(self._table("job_attempts")),
                (row["tenant_id"], row["job_id"], attempt, token))
            self._event(conn, row["tenant_id"], row["job_id"], "attempt_started", attempt)
            claimed["attempt"] = attempt
            return claimed

    def read_input(self, tenant_id, job_id, attempt, token) -> bytes | None:
        """Return canonical bytes only to the current live, uncanceled worker lease."""
        with self.connect() as conn:
            row = self._locked_job(conn, tenant_id, job_id)
            if not self._owns_live_lease(row, attempt, token) or row["cancel_requested"]:
                return None
            return self._verified_input(row)

    def _locked_job(self, conn, tenant_id, job_id):
        return conn.execute(sql.SQL("""
            SELECT *, lease_until > clock_timestamp() AS lease_live
            FROM {} WHERE tenant_id = %s AND job_id = %s FOR UPDATE
        """).format(self._table("jobs")), (tenant_id, job_id)).fetchone()

    @staticmethod
    def _owns_live_lease(row, attempt, token):
        return bool(row and row["state"] in ACTIVE_STATES and row["lease_live"]
                    and row["attempt_count"] == attempt and row["lease_token"] == token)

    def renew(self, tenant_id, job_id, attempt, token, lease_seconds: int) -> bool:
        require_seconds(lease_seconds, "lease_seconds")
        with self.connect() as conn:
            row = self._locked_job(conn, tenant_id, job_id)
            if not self._owns_live_lease(row, attempt, token) or row["cancel_requested"]:
                return False
            updated = conn.execute(sql.SQL("""
                UPDATE {} SET lease_until = clock_timestamp() + %s * interval '1 second',
                    updated_at = clock_timestamp()
                WHERE tenant_id = %s AND job_id = %s AND attempt_count = %s
                    AND lease_token = %s AND lease_until > clock_timestamp()
            """).format(self._table("jobs")),
                (lease_seconds, tenant_id, job_id, attempt, token))
            if updated.rowcount != 1:
                return False
            self._event(conn, tenant_id, job_id, "lease_renewed", attempt)
            return True

    def fail(self, tenant_id, job_id, attempt, token, kind, code,
             *, retry_delay_seconds: int = 1) -> bool:
        if kind not in FAILURE_KINDS:
            raise ValueError("unknown failure kind")
        require_reason_code(code)
        require_seconds(retry_delay_seconds, "retry_delay_seconds", 0, 3600)
        with self.connect() as conn:
            row = self._locked_job(conn, tenant_id, job_id)
            if not self._owns_live_lease(row, attempt, token):
                return False
            if row["cancel_requested"]:
                state, reason = "canceled", {"code": "canceled_by_request"}
            elif kind == "hold":
                state, reason = "hold", {"code": code, "kind": kind}
            elif kind == "fatal":
                state, reason = "failed", {"code": code, "kind": kind}
            elif attempt >= row["max_attempts"]:
                state, reason = "failed", {"code": "attempts_exhausted", "last_error": code}
            else:
                state, reason = "queued", {"code": code, "kind": kind}
            updated = conn.execute(sql.SQL("""
                UPDATE {} SET state = %s, reason = %s, lease_token = NULL,
                    lease_until = NULL, cancel_requested = false,
                    next_attempt_at = clock_timestamp() + %s * interval '1 second',
                    updated_at = clock_timestamp()
                WHERE tenant_id = %s AND job_id = %s AND attempt_count = %s
                    AND lease_token = %s AND lease_until > clock_timestamp()
            """).format(self._table("jobs")),
                (state, Jsonb(reason), retry_delay_seconds if state == "queued" else 0,
                 tenant_id, job_id, attempt, token))
            if updated.rowcount != 1:
                return False
            self._event(conn, tenant_id, job_id, state, attempt, reason)
            return True

    def cancel(self, tenant_id, job_id) -> bool:
        with self.connect() as conn:
            row = self._locked_job(conn, tenant_id, job_id)
            if row is None or row["state"] in TERMINAL_STATES:
                return False
            if row["state"] == "queued":
                conn.execute(sql.SQL("""
                    UPDATE {} SET state = 'canceled', reason = %s,
                        updated_at = clock_timestamp()
                    WHERE tenant_id = %s AND job_id = %s
                """).format(self._table("jobs")),
                    (Jsonb({"code": "canceled_by_request"}), tenant_id, job_id))
                self._event(conn, tenant_id, job_id, "canceled")
            elif not row["cancel_requested"]:
                conn.execute(sql.SQL("""
                    UPDATE {} SET cancel_requested = true, updated_at = clock_timestamp()
                    WHERE tenant_id = %s AND job_id = %s
                """).format(self._table("jobs")), (tenant_id, job_id))
                self._event(conn, tenant_id, job_id, "cancel_requested", row["attempt_count"])
            return True

    def ack_cancel(self, tenant_id, job_id, attempt, token) -> bool:
        with self.connect() as conn:
            row = self._locked_job(conn, tenant_id, job_id)
            if not self._owns_live_lease(row, attempt, token) or not row["cancel_requested"]:
                return False
            reason = {"code": "canceled_by_request"}
            updated = conn.execute(sql.SQL("""
                UPDATE {} SET state = 'canceled', reason = %s,
                    cancel_requested = false, lease_token = NULL, lease_until = NULL,
                    updated_at = clock_timestamp()
                WHERE tenant_id = %s AND job_id = %s AND attempt_count = %s
                    AND lease_token = %s AND lease_until > clock_timestamp()
            """).format(self._table("jobs")),
                (Jsonb(reason), tenant_id, job_id, attempt, token))
            if updated.rowcount != 1:
                return False
            self._event(conn, tenant_id, job_id, "canceled", attempt, reason)
            return True

    def record_decision(self, tenant_id, job_id, attempt, token, output_sha256: str):
        require_digest(output_sha256)
        with self.connect() as conn:
            row = self._locked_job(conn, tenant_id, job_id)
            if (not self._owns_live_lease(row, attempt, token) or row["cancel_requested"]
                    or row["stage"] not in AI_STAGES):
                return None
            decision_id = uuid4()
            inserted = conn.execute(sql.SQL("""
                INSERT INTO {} (tenant_id, job_id, attempt, decision_id, output_sha256)
                SELECT tenant_id, job_id, %s, %s, %s FROM {}
                WHERE tenant_id = %s AND job_id = %s AND attempt_count = %s
                    AND lease_token = %s AND lease_until > clock_timestamp()
                    AND NOT cancel_requested
                    AND state IN ('researching','reviewing','assessing')
                RETURNING decision_id
            """).format(self._table("ai_decisions"), self._table("jobs")),
                (attempt, decision_id, output_sha256, tenant_id, job_id,
                 attempt, token)).fetchone()
            return inserted["decision_id"] if inserted else None

    def list_decisions(self, tenant_id, job_id) -> list[dict]:
        with self.connect() as conn:
            return conn.execute(sql.SQL("""
                SELECT attempt, decision_id, output_sha256, recorded_at FROM {}
                WHERE tenant_id = %s AND job_id = %s ORDER BY recorded_at, decision_id
            """).format(self._table("ai_decisions")), (tenant_id, job_id)).fetchall()

    def _durable_artifact(self, artifact: bytes, expected_sha256: str) -> None:
        require_digest(expected_sha256)
        if not isinstance(artifact, bytes) or sha256(artifact).hexdigest() != expected_sha256:
            raise ValueError("artifact SHA-256 mismatch")
        root = self.artifact_root
        directory_flags = os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW
        parent_fd = _open_directory_nofollow(root.parent)
        try:
            try:
                os.mkdir(root.name, mode=0o700, dir_fd=parent_fd)
            except FileExistsError:
                pass
            os.fsync(parent_fd)
            root_fd = os.open(root.name, directory_flags, dir_fd=parent_fd)
            try:
                info = os.fstat(root_fd)
                if (not stat.S_ISDIR(info.st_mode) or info.st_uid != os.getuid()
                        or info.st_mode & 0o077):
                    raise ValueError("artifact directory must be private and owned by this process")
                temp_name = ".incoming-" + secrets.token_hex(16)
                fd = os.open(temp_name, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW,
                             0o600, dir_fd=root_fd)
                try:
                    with os.fdopen(fd, "wb") as stream:
                        stream.write(artifact)
                        stream.flush()
                        os.fsync(stream.fileno())
                    try:
                        os.link(temp_name, expected_sha256, src_dir_fd=root_fd,
                                dst_dir_fd=root_fd, follow_symlinks=False)
                    except FileExistsError:
                        existing_fd = os.open(expected_sha256, os.O_RDONLY | os.O_NOFOLLOW,
                                              dir_fd=root_fd)
                        with os.fdopen(existing_fd, "rb") as stream:
                            if sha256(stream.read()).hexdigest() != expected_sha256:
                                raise ValueError("existing content-addressed artifact is corrupt")
                finally:
                    os.unlink(temp_name, dir_fd=root_fd)
                    os.fsync(root_fd)
            finally:
                os.close(root_fd)
        finally:
            os.close(parent_fd)

    def _insert_publication(self, conn, tenant_id, job_id, attempt, decision_id,
                            digest, size, manifest):
        publication_id = uuid4()
        row = conn.execute(sql.SQL("""
            INSERT INTO {} (tenant_id, job_id, publication_id, attempt, decision_id,
                            artifact_sha256, artifact_size, manifest)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s) RETURNING *
        """).format(self._table("job_publications")),
            (tenant_id, job_id, publication_id, attempt, decision_id, digest,
             size, Jsonb(manifest))).fetchone()
        return row

    def _has_decision(self, conn, tenant_id, job_id, attempt, decision_id) -> bool:
        return conn.execute(sql.SQL("""
            SELECT 1 FROM {} WHERE tenant_id = %s AND job_id = %s
                AND attempt = %s AND decision_id = %s
        """).format(self._table("ai_decisions")),
            (tenant_id, job_id, attempt, decision_id)).fetchone() is not None

    def _valid_publication_decision(self, conn, job, attempt, decision_id) -> bool:
        if job["stage"] in DETERMINISTIC_STAGES:
            return decision_id is None
        return (job["stage"] in AI_STAGES and decision_id is not None
                and self._has_decision(conn, job["tenant_id"], job["job_id"],
                                       attempt, decision_id))

    def publish(self, tenant_id, job_id, attempt, token, decision_id,
                artifact: bytes, expected_sha256: str, manifest: dict) -> dict | None:
        require_public_manifest_v1(manifest)
        with self.connect() as conn:
            job = self._locked_job(conn, tenant_id, job_id)
            if not self._owns_live_lease(job, attempt, token) or job["cancel_requested"]:
                return None
            if not self._valid_publication_decision(conn, job, attempt, decision_id):
                return None
        self._durable_artifact(artifact, expected_sha256)
        with self.connect() as conn:
            job = self._locked_job(conn, tenant_id, job_id)
            if not self._owns_live_lease(job, attempt, token) or job["cancel_requested"]:
                return None
            if not self._valid_publication_decision(conn, job, attempt, decision_id):
                return None
            complete_manifest = {
                "schema_version": "1",
                "job_id": str(job["job_id"]),
                "stage": job["stage"],
                "input_sha256": job["input_sha256"],
                "attempt": job["attempt_count"],
                "artifact_sha256": expected_sha256,
            }
            if decision_id is not None:
                complete_manifest["decision_id"] = str(decision_id)
            updated = conn.execute(sql.SQL("""
                UPDATE {} SET state = 'succeeded', reason = NULL,
                    lease_token = NULL, lease_until = NULL,
                    updated_at = clock_timestamp()
                WHERE tenant_id = %s AND job_id = %s AND attempt_count = %s
                    AND lease_token = %s AND lease_until > clock_timestamp()
                    AND NOT cancel_requested
            """).format(self._table("jobs")), (tenant_id, job_id, attempt, token))
            if updated.rowcount != 1:
                return None
            publication = self._insert_publication(conn, tenant_id, job_id, attempt,
                                                   decision_id, expected_sha256,
                                                   len(artifact), complete_manifest)
            self._event(conn, tenant_id, job_id, "succeeded", attempt)
            return publication

    def get_publication(self, tenant_id, job_id) -> dict | None:
        with self.connect() as conn:
            return conn.execute(sql.SQL("""
                SELECT p.* FROM {} AS p JOIN {} AS j
                  ON p.tenant_id = j.tenant_id AND p.job_id = j.job_id
                WHERE p.tenant_id = %s AND p.job_id = %s AND j.state = 'succeeded'
            """).format(self._table("job_publications"), self._table("jobs")),
                (tenant_id, job_id)).fetchone()

    def read_artifact(self, tenant_id, job_id) -> bytes | None:
        publication = self.get_publication(tenant_id, job_id)
        if publication is None:
            return None
        digest = publication["artifact_sha256"]
        root_fd = _open_directory_nofollow(self.artifact_root)
        try:
            fd = os.open(digest, os.O_RDONLY | os.O_NOFOLLOW, dir_fd=root_fd)
            with os.fdopen(fd, "rb") as stream:
                data = stream.read()
        finally:
            os.close(root_fd)
        if len(data) != publication["artifact_size"] or sha256(data).hexdigest() != digest:
            raise ValueError("committed artifact is corrupt")
        return data
