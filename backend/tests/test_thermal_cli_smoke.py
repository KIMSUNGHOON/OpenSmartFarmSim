"""Optional real CLI bridge; fixture authorities do not establish a G1 gate."""

import json
import os
from pathlib import Path
import sys
from uuid import uuid4

from psycopg import sql

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.cli_worker import CliWorker
from app.job_store import JobStore
from app.thermal_publisher import collection_review_input
from app.thermal_review_contract import ThermalReviewContract
from test_jobs import pg_store
from test_thermal_publisher import setup
from test_thermal_review_contract import authority


if os.environ.get("OSSF_REAL_THERMAL_CLI_SMOKE") == "1":
    def test_real_cli_synthetic_thermal_review(setup):
        publisher, run_store, base, _, snapshot_id, _, _, _ = setup
        with run_store.connect() as conn:
            row = conn.execute(sql.SQL("""
                SELECT decision_context_id FROM {}.decision_contexts
                WHERE tenant_id=%s AND snapshot_id=%s
            """).format(sql.Identifier(run_store.schema)),
                ("tenant-a", snapshot_id)).fetchone()
        context = run_store.get_decision_context(
            "tenant-a", snapshot_id, row["decision_context_id"])
        snapshot = run_store.get_snapshot("tenant-a", snapshot_id)
        contract = ThermalReviewContract(run_store, authority)
        store = JobStore(base._dsn, base.schema, base.artifact_root,
                         decision_validator=contract,
                         evidence_policy=base.evidence_policy,
                         principal_provider=base.principal_provider)
        job = store.submit("tenant-a", "collection_review",
                           collection_review_input(snapshot, context),
                           "real-thermal-review-" + uuid4().hex)
        worker = CliWorker(store, contract,
                           cli_path=Path(os.environ["OSSF_REAL_CLI_PATH"]),
                           codex_home=Path(os.environ["OSSF_REAL_CODEX_HOME"]),
                           timeout_seconds=600, lease_seconds=660,
                           synthetic_smoke=True)
        worked = worker.run_once()
        assert worked is not None and worked.job_id == job["job_id"]
        assert worked.state == "succeeded", (worked.state, worked.reason_code)
        assert worked.capture_id and worked.decision_id
        invocation = store.get_invocation("tenant-a", job["job_id"], worked.attempt)
        assert (invocation["execution_kind"], invocation["model"],
                invocation["reasoning_effort"]) == ("codex_cli", "gpt-6-sol", "xhigh")
        with store.connect() as conn:
            capture = conn.execute(sql.SQL("""
                SELECT jsonl_sha256, final_output_sha256, exit_code,
                       termination_reason, usage FROM {}
                WHERE tenant_id=%s AND job_id=%s AND attempt=%s
            """).format(store._table("attempt_cli_captures")),
                ("tenant-a", job["job_id"], worked.attempt)).fetchone()
        assert capture["jsonl_sha256"] and capture["final_output_sha256"]
        assert capture["exit_code"] == 0 and capture["termination_reason"] == "completed"
        assert capture["usage"]["input_tokens"] > 0

        publisher.job_store = store
        receipt = publisher.publish("tenant-a", job["job_id"], snapshot_id)
        assert run_store.get_run("tenant-a", receipt["run_id"])["report"]["decision_id"] == str(
            worked.decision_id)
        print(json.dumps({
            "job_id": str(job["job_id"]), "capture_id": str(worked.capture_id),
            "decision_id": str(worked.decision_id),
            "jsonl_sha256": capture["jsonl_sha256"],
            "final_output_sha256": capture["final_output_sha256"],
            "usage": capture["usage"], "run_id": receipt["run_id"],
            "trace_sha256": list(receipt["trace_sha256"]),
        }, sort_keys=True))
