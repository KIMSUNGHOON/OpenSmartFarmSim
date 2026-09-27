"""Public-key bridge from independent CLI observation to a thermal review."""

from hashlib import sha256
import json
from pathlib import Path

from psycopg import sql

from .cli_worker import CliWorker
from .execution_attestation import HEX, _canonical


class ExecutionVerifier:
    """Fail closed unless signed process bytes match the durable decision chain."""

    def __init__(self, attestation_store, *, executable_sha256, environment_sha256):
        if (type(executable_sha256) is not str or not HEX.fullmatch(executable_sha256) or
                type(environment_sha256) is not str or
                not HEX.fullmatch(environment_sha256)):
            raise ValueError("pinned executable and environment digests required")
        self.store = attestation_store
        self.executable_sha256 = executable_sha256
        self.environment_sha256 = environment_sha256

    @staticmethod
    def _argv_ok(argv):
        return (len(argv) == 21 and
                all(Path(argv[index]).is_absolute() for index in (0, 15, 17, 19)) and
                argv == CliWorker._argv(argv[0], argv[19], argv[15], argv[17]))

    def __call__(self, tenant, job_id, attempt, capture_id, snapshot_id, decision_id):
        try:
            return self._verified(tenant, job_id, attempt, capture_id,
                                  snapshot_id, decision_id)
        except Exception:
            return False

    def _verified(self, tenant, job_id, attempt, capture_id, snapshot_id, decision_id):
        record = self.store.get(tenant, job_id, attempt)
        if (record is None or record.tenant_id != tenant or
                str(record.job_id) != str(job_id) or record.attempt != attempt or
                str(record.capture_id) != str(capture_id) or
                record.executable_sha256 != self.executable_sha256 or
                record.environment_sha256 != self.environment_sha256 or
                not self._argv_ok(record.argv)):
            return False
        table = self.store.job_store._table
        with self.store.job_store.connect() as conn:
            job = conn.execute(sql.SQL("""
                SELECT * FROM {} WHERE tenant_id=%s AND job_id=%s
            """).format(table("jobs")), (tenant, job_id)).fetchone()
            attempt_row = conn.execute(sql.SQL("""
                SELECT * FROM {} WHERE tenant_id=%s AND job_id=%s AND attempt=%s
            """).format(table("job_attempts")), (tenant, job_id, attempt)).fetchone()
            invocation = conn.execute(sql.SQL("""
                SELECT * FROM {} WHERE tenant_id=%s AND job_id=%s AND attempt=%s
            """).format(table("attempt_invocations")),
                (tenant, job_id, attempt)).fetchone()
            launch = conn.execute(sql.SQL("""
                SELECT * FROM {} WHERE tenant_id=%s AND job_id=%s AND attempt=%s
            """).format(table("attempt_cli_launches")),
                (tenant, job_id, attempt)).fetchone()
            decision = conn.execute(sql.SQL("""
                SELECT * FROM {} WHERE tenant_id=%s AND job_id=%s AND attempt=%s
            """).format(table("ai_decisions")), (tenant, job_id, attempt)).fetchone()
            if any(row is None for row in (job, attempt_row, invocation, launch, decision)):
                return False
            if not self.store.job_store._verified_invocation_inputs(conn, job, invocation):
                return False
            capture = self.store.job_store._valid_cli_capture(
                conn, job, attempt, decision["output_sha256"])
            if capture is None:
                return False
        input_value = json.loads(job["input_bytes"])
        return bool(
            job["stage"] == "collection_review" and job["state"] == "succeeded" and
            input_value.get("snapshot_id") == snapshot_id and
            record.input_sha256 == job["input_sha256"] and
            record.prompt_sha256 == invocation["prompt_sha256"] == launch["prompt_sha256"] and
            record.schema_sha256 == invocation["schema_sha256"] == launch["schema_sha256"] and
            record.attempt_id == attempt_row["attempt_id"] == invocation["attempt_id"] and
            record.launch_id == launch["launch_id"] == capture["launch_id"] and
            record.capture_id == capture["capture_id"] == decision["capture_id"] and
            record.process_id == launch["process_id"] and
            record.cli_version == launch["cli_version"] == invocation["cli_version"] and
            invocation["execution_kind"] == "codex_cli" and
            (invocation["model"], invocation["reasoning_effort"]) ==
                ("gpt-6-sol", "xhigh") and
            sha256(_canonical(record.argv)).hexdigest() == launch["args_sha256"] and
            record.jsonl_sha256 == capture["jsonl_sha256"] and
            record.final_output_sha256 == capture["final_output_sha256"] ==
                decision["output_sha256"] and
            record.exit_code == capture["exit_code"] == 0 and
            record.termination_reason == capture["termination_reason"] == "completed" and
            record.usage == capture["usage"] and
            str(decision["decision_id"]) == str(decision_id) and
            job["created_at"] <= record.started_at_utc <= launch["spawned_at"] <=
                record.ended_at_utc <= capture["sealed_at"] <= record.signed_at_utc
        )
