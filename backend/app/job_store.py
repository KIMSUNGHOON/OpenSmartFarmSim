"""Tenant-scoped PostgreSQL job transitions and content-addressed publication."""

from hashlib import sha256
import json
import os
from pathlib import Path
import re
import secrets
import stat
from uuid import UUID, uuid4

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


class JobIntentConflict(ValueError):
    """An existing tenant/stage intent has different immutable input bytes."""


class JobStore:
    def __init__(self, dsn: str | None, schema: str, artifact_root: Path,
                 *, decision_validator=None, evidence_policy=None,
                 principal_provider=None,
                 allow_synthetic_invocation: bool = False, runtime_identity=None,
                 content_access=None):
        if content_access is not None:
            from .content_access import ContentAccess
            if not isinstance(content_access, ContentAccess):
                raise ValueError("explicit content access policy required")
        if runtime_identity is not None:
            from .runtime_roles import RuntimeLoginPolicy
            if (type(runtime_identity) is not tuple or len(runtime_identity) != 2 or
                    not isinstance(runtime_identity[0], RuntimeLoginPolicy) or
                    runtime_identity[0].schema != schema or type(runtime_identity[1]) is not str or
                    runtime_identity[1] not in runtime_identity[0].roles or
                    type(dsn) is not str):
                raise ValueError("fixed runtime login policy and scope required")
        self._dsn = dsn
        self.schema = schema
        self.artifact_root = Path(artifact_root)
        self.decision_validator = decision_validator
        self.evidence_policy = evidence_policy
        self.principal_provider = principal_provider
        self.allow_synthetic_invocation = allow_synthetic_invocation
        self.runtime_identity = runtime_identity
        self.content_access = content_access

    def connect(self) -> psycopg.Connection:
        if self.runtime_identity is not None:
            from .runtime_login import connect_runtime
            return connect_runtime(self._dsn, *self.runtime_identity)
        if self._dsn is None:
            return connect_app()
        return psycopg.connect(self._dsn, row_factory=dict_row)

    def _table(self, name: str) -> sql.Composed:
        return sql.SQL("{}.{}").format(sql.Identifier(self.schema), sql.Identifier(name))

    def _principal_scopes(self, tenant_id) -> frozenset[str]:
        try:
            principal = self.principal_provider() if self.principal_provider else None
            if (isinstance(principal, dict) and principal.get("authenticated") is True
                    and principal.get("tenant_id") == tenant_id):
                scopes = principal.get("scopes")
                if (isinstance(scopes, (tuple, list, set, frozenset))
                        and all(type(scope) is str for scope in scopes)):
                    return frozenset(scopes)
        except Exception:
            pass
        return frozenset()

    def _has_scope(self, tenant_id, scope="metadata") -> bool:
        return scope in self._principal_scopes(tenant_id)

    def _event(self, conn, tenant_id, job_id, kind, attempt=None, reason=None):
        conn.execute(sql.SQL("""
            INSERT INTO {} (tenant_id, job_id, event_id, attempt, kind, reason)
            VALUES (%s, %s, %s, %s, %s, %s)
        """).format(self._table("job_events")),
                     (tenant_id, job_id, uuid4(), attempt, kind, Jsonb(reason) if reason else None))

    @staticmethod
    def _check_outcome_args(exit_code, termination_reason, usage, jsonl_evidence_id):
        if exit_code is not None and (type(exit_code) is not int or not 0 <= exit_code <= 255):
            raise ValueError("exit_code must be an integer from 0 to 255")
        if termination_reason is not None:
            require_reason_code(termination_reason)
        if usage is not None:
            keys = {"input_tokens", "output_tokens", "total_tokens",
                    "cached_input_tokens", "cache_write_input_tokens",
                    "reasoning_output_tokens"}
            if (type(usage) is not dict or not usage or any(
                    key not in keys or type(value) is not int or not 0 <= value <= 9223372036854775807
                    for key, value in usage.items())):
                raise ValueError("usage must contain only nonnegative integer token counts")
        if jsonl_evidence_id is not None and not isinstance(jsonl_evidence_id, UUID):
            raise ValueError("jsonl_evidence_id must be a UUID")

    def _check_jsonl_reference(self, conn, tenant_id, job_id, attempt, evidence_id):
        if evidence_id is None:
            return
        row = conn.execute(sql.SQL("""
            SELECT kind, late FROM {} WHERE tenant_id = %s AND job_id = %s
                AND attempt = %s AND evidence_id = %s
        """).format(self._table("attempt_evidence")),
            (tenant_id, job_id, attempt, evidence_id)).fetchone()
        if row is None or row["kind"] != "jsonl" or row["late"]:
            raise ValueError("JSONL evidence must be nonlate and belong to this attempt")

    def _outcome(self, conn, tenant_id, job_id, attempt, state, reason=None,
                 *, exit_code=None, termination_reason=None, usage=None, jsonl_evidence_id=None):
        invocation = conn.execute(sql.SQL("""
            SELECT execution_kind FROM {} WHERE tenant_id = %s AND job_id = %s AND attempt = %s
        """).format(self._table("attempt_invocations")), (tenant_id, job_id, attempt)).fetchone()
        if invocation and invocation["execution_kind"] == "codex_cli":
            capture = self._capture(conn, tenant_id, job_id, attempt)
            recovery = (state == "lease_expired" and reason == {"code": "lease_expired"}
                        or state == "canceled" and reason == {"code": "cancel_lease_expired"}
                        or state == "failed" and reason == {"code": "attempts_exhausted"})
            if recovery:
                exit_code, usage = None, None
                jsonl_evidence_id = capture["jsonl_evidence_id"] if capture else None
            elif capture:
                exit_code = capture["exit_code"]
                usage = capture["usage"]
                jsonl_evidence_id = capture["jsonl_evidence_id"]
                termination_reason = capture["termination_reason"]
            else:
                exit_code, usage, termination_reason = None, None, None
        self._check_outcome_args(exit_code, termination_reason, usage, jsonl_evidence_id)
        self._check_jsonl_reference(conn, tenant_id, job_id, attempt, jsonl_evidence_id)
        decision = conn.execute(sql.SQL("""
            SELECT decision_id FROM {} WHERE tenant_id = %s AND job_id = %s AND attempt = %s
        """).format(self._table("ai_decisions")), (tenant_id, job_id, attempt)).fetchone()
        conn.execute(sql.SQL("""
            INSERT INTO {} (tenant_id, job_id, attempt, attempt_id, state, reason, decision_id,
                            exit_code, termination_reason, usage, jsonl_evidence_id)
            SELECT tenant_id, job_id, attempt, attempt_id, %s, %s, %s, %s, %s, %s, %s FROM {}
            WHERE tenant_id = %s AND job_id = %s AND attempt = %s
        """).format(self._table("attempt_outcomes"), self._table("job_attempts")),
            (state, Jsonb(reason) if reason else None,
             decision["decision_id"] if decision else None, exit_code, termination_reason,
             Jsonb(usage) if usage is not None else None, jsonl_evidence_id,
             tenant_id, job_id, attempt))

    def list_attempt_outcomes(self, tenant_id, job_id) -> list[dict]:
        if not self._has_scope(tenant_id):
            return []
        with self.connect() as conn:
            return conn.execute(sql.SQL("""
                SELECT attempt, attempt_id, state, reason, decision_id, exit_code,
                    termination_reason, usage, jsonl_evidence_id, ended_at FROM {}
                WHERE tenant_id = %s AND job_id = %s ORDER BY attempt
            """).format(self._table("attempt_outcomes")), (tenant_id, job_id)).fetchall()

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
                ON CONFLICT ON CONSTRAINT jobs_intent_key
                DO NOTHING
                RETURNING *
            """).format(self._table("jobs")),
                (tenant_id, job_id, stage, digest, input_bytes,
                 idempotency_key, max_attempts)).fetchone()
            if row is None:
                row = conn.execute(sql.SQL("""
                    SELECT * FROM {} WHERE tenant_id = %s AND stage = %s
                        AND idempotency_key = %s
                """).format(self._table("jobs")),
                    (tenant_id, stage, idempotency_key)).fetchone()
            else:
                self._event(conn, tenant_id, job_id, "submitted")
            if row is None or self._verified_input(row) != input_bytes:
                raise JobIntentConflict("idempotency key conflicts with a different input")
        return self._public_job(row)

    def get_job(self, tenant_id: str, job_id) -> dict | None:
        if not self._has_scope(tenant_id):
            return None
        with self.connect() as conn:
            row = conn.execute(sql.SQL("SELECT * FROM {} WHERE tenant_id = %s AND job_id = %s")
                               .format(self._table("jobs")), (tenant_id, job_id)).fetchone()
            return self._public_job(row)

    @staticmethod
    def _allowed_stages(allowed_stages):
        if allowed_stages is None:
            return tuple(ACTIVE_BY_STAGE)
        if (isinstance(allowed_stages, (str, bytes)) or
                not isinstance(allowed_stages, (tuple, list, set, frozenset)) or
                not allowed_stages or any(type(stage) is not str or stage not in ACTIVE_BY_STAGE
                                          for stage in allowed_stages)):
            raise ValueError("allowed_stages must be a nonempty subset of job stages")
        return tuple(sorted(set(allowed_stages)))

    def _recover_expired(self, conn, allowed_stages, tenant_id=None) -> int:
            rows = conn.execute(sql.SQL("""
                SELECT tenant_id, job_id, attempt_count, cancel_requested, max_attempts
                FROM {} WHERE state IN ('researching','collecting','reviewing','simulating','assessing')
                    AND lease_until <= clock_timestamp() AND stage = ANY(%s)
                    AND (%s::text IS NULL OR tenant_id = %s)
                FOR UPDATE SKIP LOCKED
            """).format(self._table("jobs")), (list(allowed_stages), tenant_id, tenant_id)).fetchall()
            for row in rows:
                target = ("canceled" if row["cancel_requested"] else
                          "failed" if row["attempt_count"] >= row["max_attempts"] else "queued")
                reason = {"code": "cancel_lease_expired" if row["cancel_requested"]
                          else "attempts_exhausted" if target == "failed" else "lease_expired"}
                conn.execute(sql.SQL("""
                    UPDATE {} SET state = %s, reason = %s, lease_token = NULL,
                        lease_until = NULL, cancel_requested = false,
                        updated_at = clock_timestamp()
                    WHERE tenant_id = %s AND job_id = %s
                """).format(self._table("jobs")),
                    (target, Jsonb(reason), row["tenant_id"], row["job_id"]))
                self._event(conn, row["tenant_id"], row["job_id"], target,
                            row["attempt_count"], reason)
                self._outcome(conn, row["tenant_id"], row["job_id"], row["attempt_count"],
                              target if target != "queued" else "lease_expired", reason,
                              termination_reason=reason["code"])
            return len(rows)

    def recover_expired(self) -> int:
        with self.connect() as conn:
            return self._recover_expired(conn, self._allowed_stages(None))

    def claim(self, lease_seconds: int, *, allowed_stages=None, tenant_id=None) -> dict | None:
        require_seconds(lease_seconds, "lease_seconds")
        if tenant_id is not None and (type(tenant_id) is not str or not 1 <= len(tenant_id) <= 200):
            raise ValueError("invalid claim tenant scope")
        stages = self._allowed_stages(allowed_stages)
        with self.connect() as conn:
            self._recover_expired(conn, stages, tenant_id)
            while True:
                row = conn.execute(sql.SQL("""
                    SELECT * FROM {} WHERE stage = ANY(%s)
                        AND (%s::text IS NULL OR tenant_id = %s) AND (
                        (state = 'queued' AND next_attempt_at <= clock_timestamp())
                        OR (state IN ('researching','collecting','reviewing','simulating','assessing')
                            AND lease_until <= clock_timestamp() AND NOT cancel_requested
                            AND attempt_count < max_attempts))
                    ORDER BY created_at, job_id
                    FOR UPDATE SKIP LOCKED LIMIT 1
                """).format(self._table("jobs")), (list(stages), tenant_id, tenant_id)).fetchone()
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
                    if row["state"] in ACTIVE_STATES:
                        self._outcome(conn, row["tenant_id"], row["job_id"],
                                      row["attempt_count"], "hold", reason)
                    continue
                break
            attempt = row["attempt_count"] + 1
            attempt_id = uuid4()
            token = secrets.token_urlsafe(32)
            if row["state"] != "queued":
                self._event(conn, row["tenant_id"], row["job_id"], "lease_expired",
                            row["attempt_count"])
                self._outcome(conn, row["tenant_id"], row["job_id"], row["attempt_count"],
                              "lease_expired", {"code": "lease_expired"},
                              termination_reason="lease_expired")
            claimed = conn.execute(sql.SQL("""
                UPDATE {} SET state = %s, attempt_count = %s, lease_token = %s,
                    lease_until = clock_timestamp() + %s * interval '1 second',
                    updated_at = clock_timestamp(), reason = NULL
                WHERE tenant_id = %s AND job_id = %s RETURNING *
            """).format(self._table("jobs")),
                (ACTIVE_BY_STAGE[row["stage"]], attempt, token, lease_seconds,
                 row["tenant_id"], row["job_id"])).fetchone()
            conn.execute(sql.SQL("""
                INSERT INTO {} (tenant_id, job_id, attempt, attempt_id, lease_token_sha256)
                VALUES (%s, %s, %s, %s, %s)
            """).format(self._table("job_attempts")),
                (row["tenant_id"], row["job_id"], attempt, attempt_id,
                 sha256(token.encode()).hexdigest()))
            self._event(conn, row["tenant_id"], row["job_id"], "attempt_started", attempt)
            claimed["attempt"] = attempt
            claimed["attempt_id"] = attempt_id
            return claimed

    def read_input(self, tenant_id, job_id, attempt, token) -> bytes | None:
        """Return canonical bytes only to the current live, uncanceled worker lease."""
        with self.connect() as conn:
            row = self._locked_job(conn, tenant_id, job_id)
            if not self._owns_live_lease(row, attempt, token) or row["cancel_requested"]:
                return None
            return self._verified_input(row)

    def register_invocation(self, tenant_id, job_id, attempt, token, *,
                            prompt_evidence_id, schema_evidence_id,
                            prompt_version, schema_version, execution_kind,
                            cli_version, model, reasoning_effort):
        for label, version in (("prompt_version", prompt_version),
                               ("schema_version", schema_version)):
            if (not isinstance(version, str) or
                    not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_.:-]{0,199}", version)):
                raise ValueError(f"{label} must be a bounded version identifier")
        if execution_kind == "codex_cli":
            if (not isinstance(cli_version, str) or
                    not re.fullmatch(r"codex-cli [0-9]+\.[0-9]+\.[0-9]+", cli_version)
                    or model != "gpt-6-sol" or reasoning_effort != "xhigh"):
                raise ValueError("runtime invocation needs exact CLI model, effort, and version")
        elif execution_kind == "synthetic_fixture":
            if (self.allow_synthetic_invocation is not True or
                    cli_version != "synthetic_fixture" or model is not None or
                    reasoning_effort is not None):
                raise ValueError("synthetic invocation is permitted only in fixture mode")
        else:
            raise ValueError("unknown invocation execution kind")
        if not isinstance(prompt_evidence_id, UUID) or not isinstance(schema_evidence_id, UUID):
            raise ValueError("invocation evidence IDs must be UUIDs")
        with self.connect() as conn:
            job = self._locked_job(conn, tenant_id, job_id)
            if (not self._owns_live_lease(job, attempt, token) or job["cancel_requested"]
                    or job["stage"] not in AI_STAGES
                    or self._has_invocation(conn, tenant_id, job_id, attempt)):
                return None
            self._verified_input(job)
            evidence = conn.execute(sql.SQL("""
                SELECT evidence_id, kind, late, sha256, size, receipt_state FROM {}
                WHERE tenant_id = %s AND job_id = %s AND attempt = %s
                    AND evidence_id IN (%s, %s)
            """).format(self._table("attempt_evidence")),
                (tenant_id, job_id, attempt, prompt_evidence_id, schema_evidence_id)).fetchall()
            by_id = {row["evidence_id"]: row for row in evidence}
            prompt = by_id.get(prompt_evidence_id)
            schema = by_id.get(schema_evidence_id)
            if (prompt is None or prompt["kind"] != "prompt" or prompt["late"]
                    or prompt["receipt_state"] != "retained"
                    or schema is None or schema["kind"] != "output_schema" or schema["late"]
                    or schema["receipt_state"] != "retained"):
                raise ValueError("invocation requires retained current prompt and output schema")
            self._read_private_evidence(tenant_id, prompt)
            self._read_private_evidence(tenant_id, schema)
            claim = conn.execute(sql.SQL("""
                SELECT attempt_id FROM {} WHERE tenant_id = %s AND job_id = %s AND attempt = %s
            """).format(self._table("job_attempts")), (tenant_id, job_id, attempt)).fetchone()
            return conn.execute(sql.SQL("""
                INSERT INTO {} (tenant_id, job_id, attempt, attempt_id, input_sha256,
                    prompt_evidence_id, prompt_version, prompt_sha256,
                    schema_evidence_id, schema_version, schema_sha256,
                    execution_kind, cli_version, model, reasoning_effort)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                RETURNING *
            """).format(self._table("attempt_invocations")),
                (tenant_id, job_id, attempt, claim["attempt_id"], job["input_sha256"],
                 prompt_evidence_id, prompt_version, prompt["sha256"],
                 schema_evidence_id, schema_version, schema["sha256"],
                 execution_kind, cli_version, model, reasoning_effort)).fetchone()

    def _has_invocation(self, conn, tenant_id, job_id, attempt):
        return conn.execute(sql.SQL("""
            SELECT 1 FROM {} WHERE tenant_id = %s AND job_id = %s AND attempt = %s
        """).format(self._table("attempt_invocations")),
            (tenant_id, job_id, attempt)).fetchone() is not None

    def _verified_invocation_inputs(self, conn, job, invocation) -> bool:
        if (invocation is None or invocation["input_sha256"] != job["input_sha256"]
                or invocation["attempt"] != job["attempt_count"]):
            return False
        for evidence_id, kind, digest in (
            (invocation["prompt_evidence_id"], "prompt", invocation["prompt_sha256"]),
            (invocation["schema_evidence_id"], "output_schema", invocation["schema_sha256"]),
        ):
            row = self._evidence_row(conn, job["tenant_id"], job["job_id"], evidence_id)
            if (row is None or row["attempt"] != invocation["attempt"]
                    or row["kind"] != kind or row["late"]
                    or row["receipt_state"] != "retained" or row["sha256"] != digest):
                return False
            try:
                self._read_private_evidence(job["tenant_id"], row)
            except (OSError, ValueError, TypeError):
                return False
        return True

    def get_invocation(self, tenant_id, job_id, attempt):
        if not self._has_scope(tenant_id, "auditor"):
            return None
        with self.connect() as conn:
            return conn.execute(sql.SQL("""
                SELECT * FROM {} WHERE tenant_id = %s AND job_id = %s AND attempt = %s
            """).format(self._table("attempt_invocations")),
                (tenant_id, job_id, attempt)).fetchone()

    def _capture(self, conn, tenant_id, job_id, attempt):
        return conn.execute(sql.SQL("""
            SELECT * FROM {} WHERE tenant_id = %s AND job_id = %s AND attempt = %s
        """).format(self._table("attempt_cli_captures")),
            (tenant_id, job_id, attempt)).fetchone()

    @staticmethod
    def _parse_cli_jsonl(payload):
        if not payload or not payload.endswith(b"\n"):
            raise ValueError("incomplete CLI JSONL")
        events = []
        for line in payload.splitlines():
            if not line or len(line) > 1048576:
                raise ValueError("invalid CLI JSONL line")
            event = json.loads(line.decode("utf-8"), object_pairs_hook=JobStore._unique_pairs)
            if (type(event) is not dict or event.get("type") not in
                    {"thread.started", "turn.started", "item.started", "item.updated",
                     "item.completed", "turn.completed", "turn.failed", "error"}):
                raise ValueError("invalid CLI JSONL event")
            events.append(event)
        if (len(events) < 4 or events[0]["type"] != "thread.started" or
                events[1]["type"] != "turn.started" or
                sum(event["type"] == "thread.started" for event in events) != 1 or
                sum(event["type"] == "turn.started" for event in events) != 1 or
                events[-1]["type"] != "turn.completed" or
                any(event["type"] in ("turn.failed", "error") for event in events) or
                any(event["type"] not in ("item.started", "item.updated", "item.completed")
                    for event in events[2:-1])):
            raise ValueError("CLI JSONL has no sole completed terminal event")
        if any(event.get("error") is not None or event.get("status") == "failed"
               for event in events):
            raise ValueError("CLI event contains an error or failed status")
        item_types = {}
        started_ids = set()
        completed_ids = set()
        allowed_items = {"agent_message", "reasoning", "command_execution",
                         "file_change", "mcp_tool_call", "web_search", "todo_list"}
        for event in events[2:-1]:
            item = event.get("item")
            if type(item) is not dict:
                raise ValueError("CLI item is missing")
            item_id, item_type = item.get("id"), item.get("type")
            if (type(item_id) is not str or not item_id or len(item_id) > 200
                    or item_type not in allowed_items or item.get("status") == "failed"
                    or item.get("error") is not None or item_id in completed_ids
                    or (item_id in item_types and item_types[item_id] != item_type)):
                raise ValueError("CLI item is failed or has an invalid lifecycle")
            if event["type"] == "item.started":
                if item_id in item_types:
                    raise ValueError("CLI item started twice")
                started_ids.add(item_id)
            elif event["type"] == "item.updated" and item_id not in started_ids:
                raise ValueError("CLI item updated before it started")
            item_types[item_id] = item_type
            if event["type"] == "item.completed":
                completed_ids.add(item_id)
        messages = [event["item"].get("text") for event in events
                    if event["type"] == "item.completed"
                    and type(event.get("item")) is dict
                    and event["item"].get("type") == "agent_message"]
        if not messages or type(messages[-1]) is not str:
            raise ValueError("CLI JSONL has no final completed agent message")
        usage = events[-1].get("usage")
        if usage is not None:
            JobStore._check_outcome_args(None, None, usage, None)
        return usage, messages[-1].encode("utf-8")

    @staticmethod
    def _unique_pairs(pairs):
        value = {}
        for key, item in pairs:
            if key in value:
                raise ValueError("duplicate JSON key")
            value[key] = item
        return value

    def record_cli_launch(self, tenant_id, job_id, attempt, token, *,
                          argv, process_id, executable="codex"):
        if (type(argv) not in (list, tuple) or not argv or
                any(type(arg) is not str or not arg or len(arg) > 1000 for arg in argv)
                or type(process_id) is not int or process_id <= 0 or executable != "codex"):
            raise ValueError("invalid CLI launch observation")
        args_digest = sha256(self._canonical_report(list(argv))).hexdigest()
        with self.connect() as conn:
            job = self._locked_job(conn, tenant_id, job_id)
            invocation = conn.execute(sql.SQL("""
                SELECT * FROM {} WHERE tenant_id = %s AND job_id = %s AND attempt = %s
            """).format(self._table("attempt_invocations")),
                (tenant_id, job_id, attempt)).fetchone()
            if (not self._owns_live_lease(job, attempt, token) or job["cancel_requested"]
                    or invocation is None or invocation["execution_kind"] != "codex_cli"):
                return None
        event_bytes = self._canonical_report({"event_version": "cli-launch-v1",
            "attempt_id": str(invocation["attempt_id"]), "executable": executable,
            "cli_version": invocation["cli_version"], "args_sha256": args_digest,
            "process_id": process_id})
        evidence = self.append_evidence(tenant_id, job_id, attempt, token,
            kind="launch_event", payload=event_bytes, rights_ref="server_cli_launch")
        if evidence is None or evidence["late"] or evidence["receipt_state"] != "retained":
            return None
        with self.connect() as conn:
            job = self._locked_job(conn, tenant_id, job_id)
            if not self._owns_live_lease(job, attempt, token) or job["cancel_requested"]:
                return None
            if self._read_private_evidence(tenant_id, evidence) != event_bytes:
                return None
            return conn.execute(sql.SQL("""
                INSERT INTO {} (tenant_id, job_id, attempt, attempt_id, launch_id,
                    launch_evidence_id, executable, cli_version, args_sha256,
                    prompt_sha256, schema_sha256, process_id)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                RETURNING *
            """).format(self._table("attempt_cli_launches")),
                (tenant_id, job_id, attempt, invocation["attempt_id"], uuid4(),
                 evidence["evidence_id"], executable, invocation["cli_version"], args_digest,
                 invocation["prompt_sha256"], invocation["schema_sha256"], process_id)).fetchone()

    def seal_cli_capture(self, tenant_id, job_id, attempt, token, *, launch_id,
                         jsonl_evidence_id, final_output, exit_code,
                         termination_reason="completed", completed=True):
        if type(final_output) is not bytes or len(final_output) > 1048576:
            raise ValueError("invalid captured final output")
        self._check_outcome_args(exit_code, termination_reason, None, jsonl_evidence_id)
        if type(completed) is not bool or not isinstance(launch_id, UUID):
            raise ValueError("invalid capture state")
        with self.connect() as conn:
            job = self._locked_job(conn, tenant_id, job_id)
            launch = conn.execute(sql.SQL("""
                SELECT * FROM {} WHERE tenant_id = %s AND job_id = %s AND attempt = %s
                    AND launch_id = %s
            """).format(self._table("attempt_cli_launches")),
                (tenant_id, job_id, attempt, launch_id)).fetchone()
            if (not self._owns_live_lease(job, attempt, token) or job["cancel_requested"]
                    or launch is None or self._capture(conn, tenant_id, job_id, attempt)):
                return None
            evidence = (self._evidence_row(conn, tenant_id, job_id, jsonl_evidence_id)
                        if jsonl_evidence_id else None)
            if jsonl_evidence_id is not None and evidence is None:
                return None
            if evidence and (evidence["attempt"] != attempt or evidence["kind"] != "jsonl"
                             or evidence["late"]):
                return None
            digest = evidence["sha256"] if evidence and evidence["receipt_state"] == "retained" else None
            usage = None
            if digest:
                try:
                    usage, terminal_output = self._parse_cli_jsonl(
                        self._read_private_evidence(tenant_id, evidence))
                    if terminal_output != final_output:
                        usage = None
                except (OSError, ValueError, TypeError, UnicodeError):
                    pass
            return conn.execute(sql.SQL("""
                INSERT INTO {} (tenant_id, job_id, attempt, attempt_id, launch_id,
                    capture_id, jsonl_evidence_id, jsonl_sha256, final_output_sha256,
                    exit_code, termination_reason, usage, completed)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                RETURNING *
            """).format(self._table("attempt_cli_captures")),
                (tenant_id, job_id, attempt, launch["attempt_id"], launch_id, uuid4(),
                 jsonl_evidence_id, digest,
                 sha256(final_output).hexdigest(), exit_code, termination_reason,
                 Jsonb(usage) if usage is not None else None, completed)).fetchone()

    def _valid_cli_capture(self, conn, job, attempt, final_digest):
        capture = self._capture(conn, job["tenant_id"], job["job_id"], attempt)
        if (capture is None or not capture["completed"] or capture["exit_code"] != 0
                or capture["termination_reason"] != "completed"
                or capture["final_output_sha256"] != final_digest
                or capture["jsonl_evidence_id"] is None or capture["jsonl_sha256"] is None):
            return None
        launch = conn.execute(sql.SQL("""
            SELECT * FROM {} WHERE tenant_id = %s AND job_id = %s AND attempt = %s
                AND launch_id = %s
        """).format(self._table("attempt_cli_launches")),
            (job["tenant_id"], job["job_id"], attempt, capture["launch_id"])).fetchone()
        launch_evidence = (self._evidence_row(conn, job["tenant_id"], job["job_id"],
                                              launch["launch_evidence_id"]) if launch else None)
        if (launch is None or launch_evidence is None or launch_evidence["late"]
                or launch_evidence["kind"] != "launch_event"
                or launch_evidence["receipt_state"] != "retained"):
            return None
        expected_launch = self._canonical_report({"event_version": "cli-launch-v1",
            "attempt_id": str(launch["attempt_id"]), "executable": launch["executable"],
            "cli_version": launch["cli_version"], "args_sha256": launch["args_sha256"],
            "process_id": launch["process_id"]})
        try:
            if self._read_private_evidence(job["tenant_id"], launch_evidence) != expected_launch:
                return None
        except (OSError, ValueError, TypeError):
            return None
        row = self._evidence_row(conn, job["tenant_id"], job["job_id"], capture["jsonl_evidence_id"])
        if (row is None or row["attempt"] != attempt or row["kind"] != "jsonl" or row["late"]
                or row["receipt_state"] != "retained" or row["sha256"] != capture["jsonl_sha256"]):
            return None
        try:
            usage, terminal_output = self._parse_cli_jsonl(
                self._read_private_evidence(job["tenant_id"], row))
        except (OSError, ValueError, TypeError, UnicodeError):
            return None
        return capture if (usage == capture["usage"] and
                           sha256(terminal_output).hexdigest() == final_digest) else None

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
             *, retry_delay_seconds: int = 1, exit_code=None,
             termination_reason=None, usage=None, jsonl_evidence_id=None) -> bool:
        if kind not in FAILURE_KINDS:
            raise ValueError("unknown failure kind")
        require_reason_code(code)
        if code in {"lease_expired", "cancel_lease_expired", "attempts_exhausted",
                    "canceled_by_request", "ai_validated_hold", "input_sha256_mismatch"}:
            raise ValueError("failure code is reserved for a server transition")
        require_seconds(retry_delay_seconds, "retry_delay_seconds", 0, 3600)
        self._check_outcome_args(exit_code, termination_reason, usage, jsonl_evidence_id)
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
            self._outcome(conn, tenant_id, job_id, attempt, state, reason,
                          exit_code=exit_code, termination_reason=termination_reason,
                          usage=usage, jsonl_evidence_id=jsonl_evidence_id)
            return True

    def cancel(self, tenant_id, job_id) -> bool:
        if not self._has_scope(tenant_id, "cancel"):
            return False
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

    def ack_cancel(self, tenant_id, job_id, attempt, token, *, exit_code=None,
                   termination_reason=None, usage=None, jsonl_evidence_id=None) -> bool:
        self._check_outcome_args(exit_code, termination_reason, usage, jsonl_evidence_id)
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
            self._outcome(conn, tenant_id, job_id, attempt, "canceled", reason,
                          exit_code=exit_code, termination_reason=termination_reason,
                          usage=usage, jsonl_evidence_id=jsonl_evidence_id)
            return True

    def _evidence_access(self, conn, tenant_id, job_id, attempt, token):
        job = self._locked_job(conn, tenant_id, job_id)
        if job is None or not isinstance(token, str):
            return None
        claim = conn.execute(sql.SQL("""
            SELECT attempt_id, lease_token_sha256 FROM {}
            WHERE tenant_id = %s AND job_id = %s AND attempt = %s
        """).format(self._table("job_attempts")),
            (tenant_id, job_id, attempt)).fetchone()
        if claim is None or claim["lease_token_sha256"] != sha256(token.encode()).hexdigest():
            return None
        live = self._owns_live_lease(job, attempt, token) and not job["cancel_requested"]
        return job, not live

    @staticmethod
    def _check_evidence_args(kind, payload, rights_ref, withhold_reason, sequence):
        if kind not in {"prompt", "output_schema", "final_output", "jsonl", "launch_event",
                        "tool_event", "validation_report"}:
            raise ValueError("unknown evidence kind")
        if (not isinstance(rights_ref, str)
                or not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_.:-]{0,199}", rights_ref)):
            raise ValueError("rights_ref must identify a bounded rights record")
        if sequence is not None and (type(sequence) is not int or sequence < 0):
            raise ValueError("sequence must be a nonnegative integer")
        if payload is None:
            require_reason_code(withhold_reason)
        elif type(payload) is not bytes:
            raise TypeError("evidence payload must be bytes")
        elif withhold_reason is not None:
            raise ValueError("withheld evidence cannot include raw payload")
        elif len(payload) > (1048576 if kind == "final_output" else 10485760):
            raise ValueError("evidence exceeds kind size limit")

    def append_evidence(self, tenant_id, job_id, attempt, token, *, kind,
                        payload: bytes | None, rights_ref: str,
                        withhold_reason: str | None = None,
                        sequence: int | None = None, classification="restricted",
                        source_id="job_attempt", intended_use="decision_evidence"):
        self._check_evidence_args(kind, payload, rights_ref, withhold_reason, sequence)
        if classification not in ("private", "restricted"):
            raise ValueError("unknown evidence classification")
        with self.connect() as conn:
            if self._evidence_access(conn, tenant_id, job_id, attempt, token) is None:
                return None
        original_digest = sha256(payload).hexdigest() if payload is not None else None
        authority = None
        if payload is not None and self.evidence_policy is not None:
            try:
                proposal = self.evidence_policy(tenant_id, source_id, intended_use,
                                                kind, payload, original_digest)
                required = {"tenant_id", "source_id", "intended_use", "payload_sha256",
                            "rights_proof_id", "rights_version", "policy_version",
                            "classification", "read_scope", "retain_raw", "retain_digest"}
                if (type(proposal) is dict and required <= proposal.keys()
                        and proposal["tenant_id"] == tenant_id
                        and proposal["intended_use"] == intended_use
                        and proposal["payload_sha256"] == original_digest
                        and proposal["classification"] in ("private", "restricted")
                        and proposal["read_scope"] in ("auditor", "none")
                        and type(proposal["retain_raw"]) is bool
                        and type(proposal["retain_digest"]) is bool
                        and (not proposal["retain_raw"] or proposal["retain_digest"])
                        and all(isinstance(proposal[key], str) and
                                re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_.:-]{0,199}", proposal[key])
                                for key in ("source_id", "intended_use", "rights_proof_id",
                                            "rights_version", "policy_version"))):
                    authority = proposal
            except Exception:
                pass
        if authority is None:
            authority = dict(tenant_id=tenant_id, source_id="unverified",
                             intended_use="unverified", payload_sha256=original_digest,
                             rights_proof_id="unverified", rights_version="unverified",
                             policy_version="unconfigured", classification="restricted",
                             read_scope="none", retain_raw=False, retain_digest=False)
        retained = payload is not None and authority["retain_raw"]
        digest = original_digest if retained or (payload is not None and authority["retain_digest"]) else None
        authorized_digest = digest if payload is not None else None
        if retained:
            self._durable_evidence(tenant_id, payload, digest)
        state = "not_received" if payload is None else "retained" if retained else "received_but_withheld"
        reason = withhold_reason if payload is None else None if retained else "policy_denied"
        hash_reason = "digest_not_authorized" if state == "received_but_withheld" and digest is None else None
        with self.connect() as conn:
            access = self._evidence_access(conn, tenant_id, job_id, attempt, token)
            if access is None:
                return None
            _, late = access
            if sequence is None:
                next_row = conn.execute(sql.SQL("""
                    SELECT coalesce(max(sequence) + 1, 0) AS next_sequence FROM {}
                    WHERE tenant_id = %s AND job_id = %s AND attempt = %s AND kind = %s
                """).format(self._table("attempt_evidence")),
                    (tenant_id, job_id, attempt, kind)).fetchone()
                sequence = next_row["next_sequence"]
            authorization_id = uuid4()
            conn.execute(sql.SQL("""
                INSERT INTO {} (authorization_id, tenant_id, source_id, intended_use,
                    payload_sha256, rights_proof_id, rights_version, policy_version,
                    classification, read_scope, retain_raw, retain_digest)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """).format(self._table("evidence_authorizations")),
                (authorization_id, tenant_id, authority["source_id"], authority["intended_use"],
                 authorized_digest, authority["rights_proof_id"],
                 authority["rights_version"], authority["policy_version"],
                 authority["classification"], authority["read_scope"],
                 authority["retain_raw"], authority["retain_digest"]))
            return conn.execute(sql.SQL("""
                INSERT INTO {} (tenant_id, job_id, attempt, evidence_id, kind,
                    sequence, late, classification, rights_ref, policy_version,
                    authorization_id, receipt_state, sha256, size, withhold_reason,
                    hash_withheld_reason)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                RETURNING *
            """).format(self._table("attempt_evidence")),
                (tenant_id, job_id, attempt, uuid4(), kind, sequence, late,
                 authority["classification"], authority["rights_proof_id"],
                 authority["policy_version"], authorization_id, state, digest,
                 len(payload) if retained else None, reason, hash_reason)).fetchone()

    def list_evidence(self, tenant_id, job_id) -> list[dict]:
        scopes = self._principal_scopes(tenant_id)
        if "metadata" not in scopes:
            return []
        with self.connect() as conn:
            rows = conn.execute(sql.SQL("""
                SELECT attempt, evidence_id, kind, sequence, late, classification,
                    rights_ref, policy_version, authorization_id, receipt_state,
                    sha256, size, withhold_reason, hash_withheld_reason, recorded_at
                FROM {} WHERE tenant_id = %s AND job_id = %s
                ORDER BY attempt, recorded_at, evidence_id
            """).format(self._table("attempt_evidence")), (tenant_id, job_id)).fetchall()
        if "auditor" not in scopes:
            for row in rows:
                row.pop("sha256")
        return rows

    def _evidence_row(self, conn, tenant_id, job_id, evidence_id):
        return conn.execute(sql.SQL("""
            SELECT e.* FROM {} e JOIN {} j USING (tenant_id, job_id)
            WHERE e.tenant_id = %s AND e.job_id = %s AND e.evidence_id = %s
        """).format(self._table("attempt_evidence"), self._table("jobs")),
            (tenant_id, job_id, evidence_id)).fetchone()

    def read_evidence(self, tenant_id, job_id, evidence_id, *, access=None):
        if access == "public" or not self._has_scope(tenant_id, "auditor"):
            return None
        with self.connect() as conn:
            row = self._evidence_row(conn, tenant_id, job_id, evidence_id)
            authority = (conn.execute(sql.SQL("SELECT * FROM {} WHERE authorization_id = %s")
                                      .format(self._table("evidence_authorizations")),
                                      (row["authorization_id"],)).fetchone() if row else None)
        if (row is None or row["receipt_state"] != "retained" or authority is None
                or authority["read_scope"] != "auditor"):
            return None
        return self._read_private_evidence(tenant_id, row)

    @staticmethod
    def _validation_context(job, invocation, final_digest, artifact_digest, capture=None):
        return {
            "tenant_id": job["tenant_id"], "job_id": str(job["job_id"]),
            "attempt": invocation["attempt"], "attempt_id": str(invocation["attempt_id"]),
            "stage": job["stage"], "input_sha256": job["input_sha256"],
            "prompt_evidence_id": str(invocation["prompt_evidence_id"]),
            "prompt_version": invocation["prompt_version"],
            "prompt_sha256": invocation["prompt_sha256"],
            "schema_evidence_id": str(invocation["schema_evidence_id"]),
            "schema_version": invocation["schema_version"],
            "schema_sha256": invocation["schema_sha256"],
            "execution_kind": invocation["execution_kind"],
            "cli_version": invocation["cli_version"], "model": invocation["model"],
            "reasoning_effort": invocation["reasoning_effort"],
            "output_sha256": final_digest, "artifact_sha256": artifact_digest,
            "capture_id": str(capture["capture_id"]) if capture else None,
            "capture_sha256": capture["jsonl_sha256"] if capture else None,
        }

    @staticmethod
    def _canonical_report(report):
        return json.dumps(report, sort_keys=True, separators=(",", ":"),
                          ensure_ascii=True).encode("utf-8")

    @staticmethod
    def _parse_report(payload):
        def unique_pairs(pairs):
            value = {}
            for key, item in pairs:
                if key in value:
                    raise ValueError("duplicate report key")
                value[key] = item
            return value
        if len(payload) > 16384:
            raise ValueError("validation report exceeds bound")
        report = json.loads(payload.decode("utf-8"), object_pairs_hook=unique_pairs)
        if type(report) is not dict or JobStore._canonical_report(report) != payload:
            raise ValueError("validation report is not canonical")
        return report

    @staticmethod
    def _parse_hold_report(payload):
        if type(payload) is not bytes or len(payload) > 16384:
            raise ValueError("invalid hold report bytes")
        report = JobStore._parse_report(payload)
        if set(report) != {"schema_version", "reason_code", "missing_evidence"}:
            raise ValueError("hold report has unexpected fields")
        if report["schema_version"] != "hold_v1":
            raise ValueError("unknown hold report version")
        require_reason_code(report["reason_code"])
        identifiers = report["missing_evidence"]
        if (type(identifiers) is not list or len(identifiers) > 50 or
                any(type(item) is not str or
                    not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_.:-]{0,199}", item)
                    for item in identifiers) or len(set(identifiers)) != len(identifiers)):
            raise ValueError("missing evidence requires safe bounded identifiers")
        return report

    def record_decision(self, tenant_id, job_id, attempt, token,
                        final_output: bytes, proposed_artifact: bytes):
        if type(final_output) is not bytes or type(proposed_artifact) is not bytes:
            raise TypeError("final output and proposed artifact must be bytes")
        if len(final_output) > 1048576 or len(proposed_artifact) > 10485760:
            raise ValueError("decision bytes exceed size limit")
        with self.connect() as conn:
            job = self._locked_job(conn, tenant_id, job_id)
            if (not self._owns_live_lease(job, attempt, token) or job["cancel_requested"]
                    or job["stage"] not in AI_STAGES or self.decision_validator is None
                    or not self._has_invocation(conn, tenant_id, job_id, attempt)
                    or self._has_decision(conn, tenant_id, job_id, attempt, None)):
                return None
            invocation = conn.execute(sql.SQL("""
                SELECT * FROM {} WHERE tenant_id = %s AND job_id = %s AND attempt = %s
            """).format(self._table("attempt_invocations")),
                (tenant_id, job_id, attempt)).fetchone()
            if not self._verified_invocation_inputs(conn, job, invocation):
                return None
            if (invocation["execution_kind"] == "codex_cli" and
                    self._valid_cli_capture(conn, job, attempt, sha256(final_output).hexdigest()) is None):
                return None
        final = self.append_evidence(tenant_id, job_id, attempt, token,
            kind="final_output", payload=final_output, rights_ref="server_generated")
        if final is None:
            return None
        if final["receipt_state"] != "retained" or final["late"]:
            report = {"passed": False, "version": "storage-v1", "code": "final_withheld",
                      "disposition": None}
        else:
            stored = self._read_private_evidence(tenant_id, final)
            with self.connect() as conn:
                job = self._locked_job(conn, tenant_id, job_id)
            try:
                result = self.decision_validator(job, stored, proposed_artifact)
                report = {
                    "passed": result.get("passed") is True,
                    "version": result["version"], "code": result["code"],
                    "disposition": result.get("disposition"),
                    "hold_report_sha256": None,
                }
                require_name(report["version"], "validator version")
                require_reason_code(report["code"])
                if (report["disposition"] is None and self.allow_synthetic_invocation
                        and invocation["execution_kind"] == "synthetic_fixture"):
                    report["disposition"] = "proceed"
                if report["disposition"] not in ("proceed", "hold"):
                    raise ValueError("validator must give a disposition")
                if report["disposition"] == "hold":
                    normalized_hold = result.get("hold_report")
                    if type(normalized_hold) is not bytes or normalized_hold != proposed_artifact:
                        raise ValueError("validator did not authorize exact hold report bytes")
                    self._parse_hold_report(normalized_hold)
                    report["hold_report_sha256"] = sha256(normalized_hold).hexdigest()
            except Exception:
                report = {"passed": False, "version": "storage-v1", "code": "validator_error",
                          "disposition": None}
        with self.connect() as conn:
            invocation = conn.execute(sql.SQL("""
                SELECT * FROM {} WHERE tenant_id = %s AND job_id = %s AND attempt = %s
            """).format(self._table("attempt_invocations")),
                (tenant_id, job_id, attempt)).fetchone()
            job = conn.execute(sql.SQL("SELECT * FROM {} WHERE tenant_id = %s AND job_id = %s")
                               .format(self._table("jobs")), (tenant_id, job_id)).fetchone()
        if invocation is None or job is None:
            return None
        with self.connect() as conn:
            if not self._verified_invocation_inputs(conn, job, invocation):
                return None
            capture = (self._valid_cli_capture(conn, job, attempt, final["sha256"])
                       if invocation["execution_kind"] == "codex_cli" else None)
        if invocation["execution_kind"] == "codex_cli" and capture is None:
            return None
        report = {"report_version": "decision-validation-v1", "passed": report["passed"],
                  "validator_version": report["version"], "validator_code": report["code"],
                  "disposition": report["disposition"],
                  "hold_report_sha256": report.get("hold_report_sha256"),
                  **self._validation_context(job, invocation, final["sha256"],
                                             sha256(proposed_artifact).hexdigest(), capture)}
        report_bytes = self._canonical_report(report)
        if len(report_bytes) > 16384:
            raise ValueError("validation report exceeds bound")
        validation = self.append_evidence(tenant_id, job_id, attempt, token,
            kind="validation_report", payload=report_bytes, rights_ref="server_validation")
        if (not report["passed"] or validation is None
                or validation["receipt_state"] != "retained"
                or final["receipt_state"] != "retained" or validation["late"]):
            return None
        with self.connect() as conn:
            job = self._locked_job(conn, tenant_id, job_id)
            if (not self._owns_live_lease(job, attempt, token) or job["cancel_requested"]
                    or not self._has_invocation(conn, tenant_id, job_id, attempt)
                    or self._has_decision(conn, tenant_id, job_id, attempt, None)):
                return None
            current_invocation = conn.execute(sql.SQL("""
                SELECT * FROM {} WHERE tenant_id = %s AND job_id = %s AND attempt = %s
            """).format(self._table("attempt_invocations")),
                (tenant_id, job_id, attempt)).fetchone()
            if not self._verified_invocation_inputs(conn, job, current_invocation):
                return None
            current_capture = (self._valid_cli_capture(conn, job, attempt, final["sha256"])
                               if current_invocation["execution_kind"] == "codex_cli" else None)
            if current_invocation["execution_kind"] == "codex_cli" and current_capture is None:
                return None
            expected_report = {"report_version": "decision-validation-v1", "passed": True,
                               "validator_version": report["validator_version"],
                               "validator_code": report["validator_code"],
                               "disposition": report["disposition"],
                               "hold_report_sha256": (report["artifact_sha256"]
                                                      if report["disposition"] == "hold" else None),
                               **self._validation_context(job, current_invocation,
                                                          final["sha256"], report["artifact_sha256"],
                                                          current_capture)}
            if report != expected_report:
                return None
            self._read_private_evidence(tenant_id, validation)
            receipt_id = uuid4()
            conn.execute(sql.SQL("""
                INSERT INTO {} (tenant_id, job_id, attempt, attempt_id, receipt_id,
                    final_evidence_id, validation_evidence_id, report_sha256,
                    output_sha256, artifact_sha256, input_sha256,
                    prompt_evidence_id, schema_evidence_id, prompt_sha256,
                    schema_sha256, prompt_version, schema_version,
                    execution_kind, cli_version, model, reasoning_effort, stage,
                    validator_version, validator_code, disposition, capture_id,
                    capture_sha256, passed)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
                        %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
                        %s, %s, %s, true)
            """).format(self._table("validation_receipts")),
                (tenant_id, job_id, attempt, current_invocation["attempt_id"], receipt_id,
                 final["evidence_id"], validation["evidence_id"], validation["sha256"],
                 final["sha256"], report["artifact_sha256"], job["input_sha256"],
                 current_invocation["prompt_evidence_id"], current_invocation["schema_evidence_id"],
                 current_invocation["prompt_sha256"], current_invocation["schema_sha256"],
                 current_invocation["prompt_version"], current_invocation["schema_version"],
                 current_invocation["execution_kind"], current_invocation["cli_version"],
                 current_invocation["model"], current_invocation["reasoning_effort"],
                 job["stage"], report["validator_version"], report["validator_code"],
                 report["disposition"], current_capture["capture_id"] if current_capture else None,
                 current_capture["jsonl_sha256"] if current_capture else None))
            decision_id = uuid4()
            inserted = conn.execute(sql.SQL("""
                INSERT INTO {} (tenant_id, job_id, attempt, decision_id, output_sha256,
                    artifact_sha256, final_evidence_id, validation_evidence_id, receipt_id,
                    disposition, capture_id, capture_sha256)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s) RETURNING decision_id
            """).format(self._table("ai_decisions")),
                (tenant_id, job_id, attempt, decision_id, final["sha256"],
                 sha256(proposed_artifact).hexdigest(), final["evidence_id"],
                 validation["evidence_id"], receipt_id, report["disposition"],
                 current_capture["capture_id"] if current_capture else None,
                 current_capture["jsonl_sha256"] if current_capture else None)).fetchone()
            return inserted["decision_id"]

    def list_decisions(self, tenant_id, job_id) -> list[dict]:
        if not self._has_scope(tenant_id, "auditor"):
            return []
        with self.connect() as conn:
            return conn.execute(sql.SQL("""
                SELECT attempt, decision_id, output_sha256, artifact_sha256,
                    final_evidence_id, validation_evidence_id, recorded_at FROM {}
                WHERE tenant_id = %s AND job_id = %s ORDER BY recorded_at, decision_id
            """).format(self._table("ai_decisions")), (tenant_id, job_id)).fetchall()

    def _content_directory(self, tenant_id=None, *, create=False):
        if create and self.content_access is not None:
            self.content_access.require_writer()
        names = [self.artifact_root.name]
        if tenant_id is not None:
            names += [".evidence", sha256(tenant_id.encode()).hexdigest()]
        fd = _open_directory_nofollow(self.artifact_root.parent)
        try:
            for name in names:
                created = False
                if create:
                    try:
                        os.mkdir(name, mode=0o700, dir_fd=fd)
                        created = True
                    except FileExistsError:
                        pass
                    os.fsync(fd)
                child_fd = os.open(name, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW,
                                   dir_fd=fd)
                try:
                    if self.content_access is not None:
                        if created:
                            self.content_access.prepare_new(child_fd, directory=True)
                            os.fsync(child_fd)
                            os.fsync(fd)
                        self.content_access.validate(child_fd, directory=True)
                    else:
                        info = os.fstat(child_fd)
                        if (not stat.S_ISDIR(info.st_mode) or info.st_uid != os.getuid()
                                or info.st_mode & 0o077):
                            raise ValueError("content directory must be private and owned by this process")
                except BaseException:
                    os.close(child_fd)
                    raise
                os.close(fd)
                fd = child_fd
            return fd
        except BaseException:
            os.close(fd)
            raise

    def _read_content(self, directory_fd, digest, size):
        require_digest(digest)
        fd = os.open(digest, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK, dir_fd=directory_fd)
        with os.fdopen(fd, "rb") as stream:
            info = os.fstat(stream.fileno())
            if self.content_access is not None:
                self.content_access.validate(stream.fileno(), directory=False)
            if not stat.S_ISREG(info.st_mode) or info.st_size != size:
                raise ValueError("committed content is corrupt")
            data = stream.read(size + 1)
        if len(data) != size or sha256(data).hexdigest() != digest:
            raise ValueError("committed content is corrupt")
        return data

    def _durable_content(self, payload, expected_sha256, tenant_id=None):
        require_digest(expected_sha256)
        if type(payload) is not bytes or sha256(payload).hexdigest() != expected_sha256:
            raise ValueError("artifact SHA-256 mismatch")
        directory_fd = self._content_directory(tenant_id, create=True)
        try:
            temp_name = ".incoming-" + secrets.token_hex(16)
            fd = os.open(temp_name, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW,
                         0o600, dir_fd=directory_fd)
            try:
                with os.fdopen(fd, "wb") as stream:
                    stream.write(payload)
                    stream.flush()
                    if self.content_access is not None:
                        self.content_access.prepare_new(stream.fileno(), directory=False)
                    os.fsync(stream.fileno())
                try:
                    os.link(temp_name, expected_sha256, src_dir_fd=directory_fd,
                            dst_dir_fd=directory_fd, follow_symlinks=False)
                except FileExistsError:
                    try:
                        self._read_content(directory_fd, expected_sha256, len(payload))
                    except ValueError as error:
                        raise ValueError("existing content-addressed artifact is corrupt") from error
            finally:
                os.unlink(temp_name, dir_fd=directory_fd)
                os.fsync(directory_fd)
        finally:
            os.close(directory_fd)

    def _durable_artifact(self, artifact: bytes, expected_sha256: str) -> None:
        self._durable_content(artifact, expected_sha256)

    def _durable_evidence(self, tenant_id, payload, digest):
        self._durable_content(payload, digest, tenant_id)

    def _read_private_evidence(self, tenant_id, row):
        if row["sha256"] is None:
            return None
        directory_fd = self._content_directory(tenant_id)
        try:
            return self._read_content(directory_fd, row["sha256"], row["size"])
        finally:
            os.close(directory_fd)

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

    def _has_decision(self, conn, tenant_id, job_id, attempt, decision_id):
        return conn.execute(sql.SQL("""
            SELECT * FROM {} WHERE tenant_id = %s AND job_id = %s
                AND attempt = %s AND (%s::uuid IS NULL OR decision_id = %s)
        """).format(self._table("ai_decisions")),
            (tenant_id, job_id, attempt, decision_id, decision_id)).fetchone()

    def _valid_publication_decision(self, conn, job, attempt, decision_id, digest) -> bool:
        if job["stage"] in DETERMINISTIC_STAGES:
            return decision_id is None
        if job["stage"] not in AI_STAGES or decision_id is None:
            return False
        decision = self._has_decision(conn, job["tenant_id"], job["job_id"],
                                      attempt, decision_id)
        return bool(decision and decision["artifact_sha256"] == digest
                    and decision["disposition"] == "proceed")

    def _verify_decision_final(self, conn, job, attempt, decision_id, digest,
                               disposition="proceed"):
        tenant_id, job_id = job["tenant_id"], job["job_id"]
        decision = self._has_decision(conn, tenant_id, job_id, attempt, decision_id)
        if (decision is None or decision["artifact_sha256"] != digest
                or decision["disposition"] != disposition):
            return False
        final = self._evidence_row(conn, tenant_id, job_id, decision["final_evidence_id"])
        report_row = self._evidence_row(conn, tenant_id, job_id,
                                        decision["validation_evidence_id"])
        receipt = conn.execute(sql.SQL("""
            SELECT * FROM {} WHERE tenant_id = %s AND job_id = %s AND attempt = %s
                AND receipt_id = %s
        """).format(self._table("validation_receipts")),
            (tenant_id, job_id, attempt, decision["receipt_id"])).fetchone()
        invocation = conn.execute(sql.SQL("""
            SELECT * FROM {} WHERE tenant_id = %s AND job_id = %s AND attempt = %s
        """).format(self._table("attempt_invocations")),
            (tenant_id, job_id, attempt)).fetchone()
        if (final is None or report_row is None or receipt is None or invocation is None
                or final["kind"] != "final_output" or report_row["kind"] != "validation_report"
                or final["receipt_state"] != "retained"
                or report_row["receipt_state"] != "retained"
                or final["sha256"] != decision["output_sha256"] or final["late"]
                or report_row["sha256"] != receipt["report_sha256"] or report_row["late"]
                or receipt["final_evidence_id"] != final["evidence_id"]
                or receipt["validation_evidence_id"] != report_row["evidence_id"]
                or receipt["output_sha256"] != decision["output_sha256"]
                or receipt["artifact_sha256"] != digest or receipt["passed"] is not True
                or receipt["disposition"] != disposition
                or receipt["capture_id"] != decision["capture_id"]
                or receipt["capture_sha256"] != decision["capture_sha256"]):
            return False
        if not self._verified_invocation_inputs(conn, job, invocation):
            return False
        capture = None
        if invocation["execution_kind"] == "codex_cli":
            capture = self._valid_cli_capture(conn, job, attempt, decision["output_sha256"])
            if (capture is None or capture["capture_id"] != decision["capture_id"]
                    or capture["jsonl_sha256"] != decision["capture_sha256"]):
                return False
        elif decision["capture_id"] is not None or decision["capture_sha256"] is not None:
            return False
        try:
            self._read_private_evidence(tenant_id, final)
            report = self._parse_report(self._read_private_evidence(tenant_id, report_row))
        except (OSError, ValueError, TypeError, UnicodeError):
            return False
        expected = {"report_version": "decision-validation-v1", "passed": True,
                    "validator_version": receipt["validator_version"],
                    "validator_code": receipt["validator_code"],
                    "disposition": disposition,
                    "hold_report_sha256": digest if disposition == "hold" else None,
                    **self._validation_context(job, invocation,
                                               decision["output_sha256"], digest, capture)}
        return (report == expected and receipt["attempt_id"] == invocation["attempt_id"]
                and receipt["input_sha256"] == job["input_sha256"]
                and receipt["prompt_sha256"] == invocation["prompt_sha256"]
                and receipt["schema_sha256"] == invocation["schema_sha256"]
                and receipt["prompt_version"] == invocation["prompt_version"]
                and receipt["schema_version"] == invocation["schema_version"]
                and receipt["stage"] == job["stage"])

    def publish(self, tenant_id, job_id, attempt, token, decision_id,
                artifact: bytes, expected_sha256: str, manifest: dict, *,
                exit_code=None, termination_reason=None, usage=None,
                jsonl_evidence_id=None) -> dict | None:
        require_public_manifest_v1(manifest)
        require_digest(expected_sha256)
        self._check_outcome_args(exit_code, termination_reason, usage, jsonl_evidence_id)
        with self.connect() as conn:
            job = self._locked_job(conn, tenant_id, job_id)
            if not self._owns_live_lease(job, attempt, token) or job["cancel_requested"]:
                return None
            if not self._valid_publication_decision(conn, job, attempt, decision_id,
                                                    expected_sha256):
                return None
            self._check_jsonl_reference(conn, tenant_id, job_id, attempt, jsonl_evidence_id)
            if decision_id is not None and not self._verify_decision_final(
                    conn, job, attempt, decision_id, expected_sha256):
                return None
        self._durable_artifact(artifact, expected_sha256)
        with self.connect() as conn:
            job = self._locked_job(conn, tenant_id, job_id)
            if not self._owns_live_lease(job, attempt, token) or job["cancel_requested"]:
                return None
            if not self._valid_publication_decision(conn, job, attempt, decision_id,
                                                    expected_sha256):
                return None
            if decision_id is not None and not self._verify_decision_final(
                    conn, job, attempt, decision_id, expected_sha256):
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
            self._outcome(conn, tenant_id, job_id, attempt, "succeeded",
                          exit_code=exit_code, termination_reason=termination_reason,
                          usage=usage, jsonl_evidence_id=jsonl_evidence_id)
            return publication

    def finish_validated_hold(self, tenant_id, job_id, attempt, token,
                              decision_id, report_bytes):
        self._parse_hold_report(report_bytes)
        digest = sha256(report_bytes).hexdigest()
        with self.connect() as conn:
            job = self._locked_job(conn, tenant_id, job_id)
            if (not self._owns_live_lease(job, attempt, token) or job["cancel_requested"]
                    or not self._verify_decision_final(conn, job, attempt, decision_id,
                                                       digest, "hold")):
                return None
        self._durable_evidence(tenant_id, report_bytes, digest)
        with self.connect() as conn:
            job = self._locked_job(conn, tenant_id, job_id)
            if (not self._owns_live_lease(job, attempt, token) or job["cancel_requested"]
                    or not self._verify_decision_final(conn, job, attempt, decision_id,
                                                       digest, "hold")):
                return None
            decision = self._has_decision(conn, tenant_id, job_id, attempt, decision_id)
            receipt = conn.execute(sql.SQL("""
                SELECT * FROM {} WHERE tenant_id = %s AND job_id = %s AND attempt = %s
                    AND receipt_id = %s
            """).format(self._table("validation_receipts")),
                (tenant_id, job_id, attempt, decision["receipt_id"])).fetchone()
            auth_id = uuid4()
            conn.execute(sql.SQL("""
                INSERT INTO {} (authorization_id, tenant_id, source_id, intended_use,
                    payload_sha256, rights_proof_id, rights_version, policy_version,
                    classification, read_scope, retain_raw, retain_digest)
                VALUES (%s, %s, 'server_hold_report', 'hold_report', %s,
                    'server_validated', 'hold-v1', 'hold-v1', 'private', 'auditor', true, true)
            """).format(self._table("evidence_authorizations")),
                (auth_id, tenant_id, digest))
            held = conn.execute(sql.SQL("""
                INSERT INTO {} (tenant_id, job_id, attempt, attempt_id, decision_id,
                    receipt_id, hold_id, report_sha256, report_size, authorization_id)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s) RETURNING *
            """).format(self._table("job_hold_reports")),
                (tenant_id, job_id, attempt, receipt["attempt_id"], decision_id,
                 receipt["receipt_id"], uuid4(), digest, len(report_bytes), auth_id)).fetchone()
            reason = {"code": "ai_validated_hold"}
            updated = conn.execute(sql.SQL("""
                UPDATE {} SET state = 'hold', reason = %s, lease_token = NULL,
                    lease_until = NULL, updated_at = clock_timestamp()
                WHERE tenant_id = %s AND job_id = %s AND attempt_count = %s
                    AND lease_token = %s AND lease_until > clock_timestamp()
                    AND NOT cancel_requested
            """).format(self._table("jobs")),
                (Jsonb(reason), tenant_id, job_id, attempt, token))
            if updated.rowcount != 1:
                return None
            self._event(conn, tenant_id, job_id, "hold", attempt, reason)
            self._outcome(conn, tenant_id, job_id, attempt, "hold", reason)
            return held

    def get_hold_report(self, tenant_id, job_id):
        if not self._has_scope(tenant_id, "metadata"):
            return None
        with self.connect() as conn:
            row = conn.execute(sql.SQL("""
                SELECT h.* FROM {} h JOIN {} j USING (tenant_id, job_id)
                WHERE h.tenant_id = %s AND h.job_id = %s AND j.state = 'hold'
                    AND j.reason->>'code' = 'ai_validated_hold'
            """).format(self._table("job_hold_reports"), self._table("jobs")),
                (tenant_id, job_id)).fetchone()
        if row is None:
            return None
        return {key: row[key] for key in ("tenant_id", "job_id", "attempt", "attempt_id",
                                          "decision_id", "receipt_id", "hold_id", "recorded_at")}

    def read_hold_report(self, tenant_id, job_id):
        if not self._has_scope(tenant_id, "artifact"):
            return None
        with self.connect() as conn:
            row = conn.execute(sql.SQL("""
                SELECT h.* FROM {} h JOIN {} j USING (tenant_id, job_id)
                JOIN {} a ON a.authorization_id = h.authorization_id
                WHERE h.tenant_id = %s AND h.job_id = %s AND j.state = 'hold'
                    AND j.reason->>'code' = 'ai_validated_hold' AND a.tenant_id = h.tenant_id
                    AND a.payload_sha256 = h.report_sha256 AND a.retain_raw
                    AND a.read_scope = 'auditor'
            """).format(self._table("job_hold_reports"), self._table("jobs"),
                          self._table("evidence_authorizations")),
                (tenant_id, job_id)).fetchone()
        if row is None:
            return None
        directory_fd = self._content_directory(tenant_id)
        try:
            data = self._read_content(directory_fd, row["report_sha256"], row["report_size"])
        finally:
            os.close(directory_fd)
        self._parse_hold_report(data)
        return data

    def _publication_row(self, tenant_id, job_id) -> dict | None:
        with self.connect() as conn:
            return conn.execute(sql.SQL("""
                SELECT p.* FROM {} AS p JOIN {} AS j
                  ON p.tenant_id = j.tenant_id AND p.job_id = j.job_id
                WHERE p.tenant_id = %s AND p.job_id = %s AND j.state = 'succeeded'
            """).format(self._table("job_publications"), self._table("jobs")),
                (tenant_id, job_id)).fetchone()

    def get_publication(self, tenant_id, job_id) -> dict | None:
        if not self._has_scope(tenant_id):
            return None
        return self._publication_row(tenant_id, job_id)

    def read_artifact(self, tenant_id, job_id) -> bytes | None:
        if not self._has_scope(tenant_id, "artifact"):
            return None
        publication = self._publication_row(tenant_id, job_id)
        if publication is None:
            return None
        digest = publication["artifact_sha256"]
        root_fd = self._content_directory()
        try:
            data = self._read_content(root_fd, digest, publication["artifact_size"])
        finally:
            os.close(root_fd)
        return data
