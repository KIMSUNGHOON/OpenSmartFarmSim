"""Sign an observed CLI completion only after its durable decision is verified.

Deployment must instantiate this issuer inside a separately controlled
supervisor process. This module alone does not establish that process boundary.
"""

from datetime import datetime, timezone
from hashlib import sha256
from uuid import uuid4

from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from psycopg import sql

from .cli_contracts import DecisionContract, SCHEMA_BYTES, STAGES
from .cli_supervisor import CliProcessSupervisor
from .cli_worker import CliWorker
from .execution_attestation import (DOMAIN, HEX, KEY_ID, ExecutionAttestation,
                                    encode_attestation)
from .jobs import ACTIVE_BY_STAGE


class ExecutionAttestationIssuer:
    """Own the private key and the process observer in the supervisor service."""

    def __init__(self, job_store, observer: CliProcessSupervisor,
                 private_key: Ed25519PrivateKey, key_id: str, *,
                 executable_sha256: str, environment_sha256: str):
        if (not isinstance(observer, CliProcessSupervisor) or
                observer._process is not None or
                not isinstance(getattr(job_store, "decision_validator", None), DecisionContract) or
                not isinstance(private_key, Ed25519PrivateKey) or
                type(key_id) is not str or not KEY_ID.fullmatch(key_id) or
                type(executable_sha256) is not str or not HEX.fullmatch(executable_sha256) or
                type(environment_sha256) is not str or
                not HEX.fullmatch(environment_sha256)):
            raise ValueError("trusted supervisor key and pinned execution identity required")
        self.job_store = job_store
        self.observer = observer
        self.private_key = private_key
        self.key_id = key_id
        self.executable_sha256 = executable_sha256
        self.environment_sha256 = environment_sha256
        self._scope = None
        self._issued = None

    def start(self, tenant, job_id, attempt):
        """Read the frozen invocation; the caller cannot supply process input bytes."""
        if self._scope is not None or self.observer._process is not None:
            raise ValueError("supervisor attempt already started")
        table = self.job_store._table
        with self.job_store.connect() as conn:
            job = conn.execute(sql.SQL("""
                SELECT *, lease_until > clock_timestamp() AS lease_live
                FROM {} WHERE tenant_id=%s AND job_id=%s
            """).format(table("jobs")), (tenant, job_id)).fetchone()
            attempt_row = conn.execute(sql.SQL("""
                SELECT * FROM {} WHERE tenant_id=%s AND job_id=%s AND attempt=%s
            """).format(table("job_attempts")), (tenant, job_id, attempt)).fetchone()
            invocation = conn.execute(sql.SQL("""
                SELECT * FROM {} WHERE tenant_id=%s AND job_id=%s AND attempt=%s
            """).format(table("attempt_invocations")),
                (tenant, job_id, attempt)).fetchone()
            if (job is None or attempt_row is None or invocation is None or
                    job["stage"] not in STAGES or
                    job["state"] != ACTIVE_BY_STAGE[job["stage"]] or
                    job["attempt_count"] != attempt or not job["lease_live"] or
                    job["cancel_requested"] or
                    attempt_row["attempt_id"] != invocation["attempt_id"] or
                    invocation["execution_kind"] != "codex_cli" or
                    (invocation["model"], invocation["reasoning_effort"]) !=
                        ("gpt-6-sol", "xhigh") or
                    sha256(job["input_bytes"]).hexdigest() != job["input_sha256"] or
                    not self.job_store._verified_invocation_inputs(conn, job, invocation)):
                raise ValueError("trusted live invocation required")
            prompt_row = self.job_store._evidence_row(
                conn, tenant, job_id, invocation["prompt_evidence_id"])
            schema_row = self.job_store._evidence_row(
                conn, tenant, job_id, invocation["schema_evidence_id"])
            prompt = self.job_store._read_private_evidence(tenant, prompt_row)
            schema = self.job_store._read_private_evidence(tenant, schema_row)
            value, authority = self.job_store.decision_validator.input_context(job)
            if prompt != CliWorker._prompt(job, value, authority) or schema != SCHEMA_BYTES:
                raise ValueError("frozen invocation bytes differ from server contract")
        if sha256(self.observer.cli_path.read_bytes()).hexdigest() != self.executable_sha256:
            raise ValueError("pinned supervisor executable differs")
        launch = self.observer.start(prompt)
        if (launch.executable_sha256 != self.executable_sha256 or
                launch.cli_version != invocation["cli_version"] or
                launch.prompt_sha256 != invocation["prompt_sha256"] or
                launch.schema_sha256 != invocation["schema_sha256"]):
            self.observer.close()
            raise ValueError("process observation differs from frozen invocation")
        self._scope = (tenant, job_id, attempt, attempt_row["attempt_id"],
                       job["input_sha256"], job["stage"])
        return launch

    def issue(self, capture_id, decision_id):
        if self._scope is None:
            raise ValueError("supervisor process observation required")
        if self._issued is not None:
            pinned_capture, pinned_decision, raw, signature = self._issued
            if (capture_id, decision_id) != (pinned_capture, pinned_decision):
                raise ValueError("supervisor attestation identity is immutable")
            if not self.scope_live(allow_closed=True):
                raise ValueError("supervisor attempt is no longer live")
            return raw, signature
        (tenant, job_id, attempt, observed_attempt_id,
         observed_input_sha, observed_stage) = self._scope
        observed_launch = self.observer._launch
        observed_result = self.observer._result
        if (observed_launch is None or observed_result is None or
                observed_result.termination_reason != "completed" or
                observed_result.exit_code != 0 or observed_result.usage is None or
                observed_result.jsonl is None or observed_result.final_output is None or
                observed_launch.executable_sha256 != self.executable_sha256 or
                list(observed_launch.argv) != CliWorker._argv(
                    observed_launch.argv[0], observed_launch.argv[19],
                    observed_launch.argv[15], observed_launch.argv[17])):
            raise ValueError("successful independent process observation required")

        table = self.job_store._table
        with self.job_store.connect() as conn:
            job = conn.execute(sql.SQL("""
                SELECT *, lease_until > clock_timestamp() AS lease_live
                FROM {} WHERE tenant_id=%s AND job_id=%s
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
            """).format(table("ai_decisions")),
                (tenant, job_id, attempt)).fetchone()
            if any(row is None for row in (job, attempt_row, invocation, launch,
                                            decision)):
                raise ValueError("durable CLI capture and validated decision missing")
            capture = self.job_store._valid_cli_capture(
                conn, job, attempt, decision["output_sha256"])
            if (capture is None or
                    not self.job_store._verified_invocation_inputs(conn, job, invocation) or
                    not self.job_store._verify_decision_final(
                        conn, job, attempt, decision_id, decision["artifact_sha256"],
                        decision["disposition"])):
                raise ValueError("durable CLI evidence failed validation")
            jsonl_row = self.job_store._evidence_row(
                conn, tenant, job_id, capture["jsonl_evidence_id"])
            final_row = self.job_store._evidence_row(
                conn, tenant, job_id, decision["final_evidence_id"])
            if jsonl_row is None or final_row is None:
                raise ValueError("durable CLI raw bytes unavailable")
            stored_jsonl = self.job_store._read_private_evidence(tenant, jsonl_row)
            stored_final = self.job_store._read_private_evidence(tenant, final_row)

        signed_at = datetime.now(timezone.utc)
        active = (job["stage"] in STAGES and
                  job["state"] == ACTIVE_BY_STAGE[job["stage"]] and job["lease_live"])
        closed = ((job["state"], decision["disposition"]) in
                  {("succeeded", "proceed"), ("hold", "hold")})
        if not all((
            job["stage"] == observed_stage,
            job["stage"] in STAGES, active or closed, not job["cancel_requested"],
            decision["disposition"] in {"proceed", "hold"},
            job["attempt_count"] == attempt,
            job["input_sha256"] == invocation["input_sha256"],
            job["input_sha256"] == observed_input_sha,
            sha256(job["input_bytes"]).hexdigest() == observed_input_sha,
            attempt_row["attempt_id"] == invocation["attempt_id"] ==
                launch["attempt_id"] == capture["attempt_id"],
            attempt_row["attempt_id"] == observed_attempt_id,
            invocation["execution_kind"] == "codex_cli",
            invocation["model"] == "gpt-6-sol",
            invocation["reasoning_effort"] == "xhigh",
            observed_launch.cli_version == invocation["cli_version"] == launch["cli_version"],
            observed_launch.prompt_sha256 == invocation["prompt_sha256"] ==
                launch["prompt_sha256"],
            observed_launch.schema_sha256 == invocation["schema_sha256"] ==
                launch["schema_sha256"],
            sha256(self.job_store._canonical_report(list(observed_launch.argv))).hexdigest() ==
                launch["args_sha256"],
            observed_launch.process_id == launch["process_id"],
            capture["launch_id"] == launch["launch_id"],
            capture["capture_id"] == capture_id == decision["capture_id"],
            decision["decision_id"] == decision_id,
            capture["exit_code"] == 0, capture["termination_reason"] == "completed",
            observed_result.jsonl_sha256 == capture["jsonl_sha256"],
            observed_result.final_output_sha256 == capture["final_output_sha256"] ==
                decision["output_sha256"],
            observed_result.usage == capture["usage"],
            observed_result.started_at_utc == observed_launch.started_at_utc,
            stored_jsonl == observed_result.jsonl,
            stored_final == observed_result.final_output,
            job["created_at"] <= observed_launch.started_at_utc <=
                launch["spawned_at"] <= observed_result.ended_at_utc <=
                capture["sealed_at"] <= signed_at,
        )):
            raise ValueError("process observation differs from durable CLI evidence")

        record = ExecutionAttestation(
            record_version="cli-execution-attestation-v1", key_id=self.key_id,
            tenant_id=tenant, job_id=job_id, attempt=attempt,
            attempt_id=attempt_row["attempt_id"], nonce=uuid4(),
            input_sha256=job["input_sha256"],
            prompt_sha256=observed_launch.prompt_sha256,
            schema_sha256=observed_launch.schema_sha256,
            cli_version=observed_launch.cli_version,
            executable_sha256=observed_launch.executable_sha256,
            argv=list(observed_launch.argv),
            environment_sha256=self.environment_sha256,
            launch_id=launch["launch_id"], capture_id=capture["capture_id"],
            jsonl_sha256=observed_result.jsonl_sha256,
            final_output_sha256=observed_result.final_output_sha256,
            process_id=observed_launch.process_id,
            process_start_token=observed_launch.process_start_token,
            started_at_utc=observed_launch.started_at_utc,
            ended_at_utc=observed_result.ended_at_utc,
            signed_at_utc=signed_at, exit_code=0,
            termination_reason="completed", usage=dict(observed_result.usage))
        raw = encode_attestation(record)
        signature = self.private_key.sign(DOMAIN + raw)
        self._issued = (capture_id, decision_id, raw, signature)
        return raw, signature

    def scope_live(self, *, allow_closed=False):
        if self._scope is None:
            return False
        tenant, job_id, attempt, _, input_sha, stage = self._scope
        with self.job_store.connect() as conn:
            job = conn.execute(sql.SQL("""
                SELECT *, lease_until > clock_timestamp() AS lease_live
                FROM {} WHERE tenant_id=%s AND job_id=%s
            """).format(self.job_store._table("jobs")), (tenant, job_id)).fetchone()
        return (job is not None and job["attempt_count"] == attempt and
                job["input_sha256"] == input_sha and job["stage"] == stage and
                not job["cancel_requested"] and (
                    (job["state"] == ACTIVE_BY_STAGE[stage] and job["lease_live"]) or
                    (allow_closed and job["state"] in {"succeeded", "hold"})))
