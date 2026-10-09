"""Actual IPC/process plumbing with synthetic decisions, a fake CLI, and test key."""

from pathlib import Path
import os
import sys
from uuid import uuid4

import pytest
from psycopg import sql

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from app.cli_supervisor_client import SupervisorClient, SupervisorSession
from app.cli_worker import CliWorker
from app.execution_attestation import ExecutionAttestationStore
from app.execution_verifier import ExecutionVerifier
from test_cli_contracts import input_for
from test_cli_supervisor_service import approved, running_server
from test_cli_worker import _worker
from test_jobs import pg_store


def decision_input(stage):
    value = input_for(stage)
    value.update(decision_context_id="ipc-test-context-a",
        decision_at_utc="2026-01-03T00:00:00Z", claim_mode="ex_post_replay",
        decision_time_kind="hypothetical")
    return value


def supervised(store, local, server):
    path, public, settings, _ = server
    attestations = ExecutionAttestationStore(store, {"test-supervisor-v1": public})
    client = SupervisorClient(path, supervisor_uid=os.getuid(), tenant_id="tenant-a",
        executable_sha256=settings["executable_sha256"],
        environment_sha256=settings["environment_sha256"])
    worker = CliWorker(store, local.contract, supervisor_client=client,
        attestation_store=attestations, timeout_seconds=local.timeout_seconds,
        lease_seconds=local.lease_seconds, synthetic_smoke=True)
    return worker, attestations


@pytest.mark.parametrize("stage", ["research", "collection_review", "assessment"])
@pytest.mark.parametrize("proceed", [False, True])
def test_worker_delegates_all_ai_stages_and_verifies_before_closure(pg_store, tmp_path, stage, proceed):
    from test_cli_contracts import resolver
    store, local = _worker(pg_store, tmp_path, mode="valid_slow",
                          authority=approved if proceed else resolver)
    job = store.submit("tenant-a", stage, decision_input(stage), uuid4().hex)
    with running_server(store, local, tmp_path, proceed=proceed) as server:
        worker, attestations = supervised(store, local, server)
        assert worker.cli_path is None and worker.codex_home is None and worker.child_env == {}
        result = worker.run_once()
        assert result.state == ("succeeded" if proceed else "hold"), result
        record = attestations.get("tenant-a", job["job_id"], result.attempt)
        assert record is not None and record.capture_id == result.capture_id
        assert record.usage == {"input_tokens": 1, "output_tokens": 1}
        assert not Path(f"/proc/{record.process_id}").exists()
        assert attestations.get("tenant-b", job["job_id"], result.attempt) is None
        assert not ExecutionVerifier(attestations,
            executable_sha256=worker.supervisor_client.executable_sha256,
            environment_sha256=worker.supervisor_client.environment_sha256).verify_pending(
                "tenant-a", job["job_id"], result.attempt, result.capture_id, result.decision_id)
        if stage == "collection_review" and proceed:
            assert ExecutionVerifier(attestations,
                executable_sha256=worker.supervisor_client.executable_sha256,
                environment_sha256=worker.supervisor_client.environment_sha256)(
                    "tenant-a", job["job_id"], result.attempt, result.capture_id,
                    "snapshot-a", result.decision_id)


@pytest.mark.parametrize("fault", ["missing", "signature", "jsonl"])
def test_worker_cannot_publish_without_matching_signed_observation(pg_store, tmp_path, monkeypatch, fault):
    store, local = _worker(pg_store, tmp_path, mode="valid_slow", authority=approved)
    job = store.submit("tenant-a", "collection_review", decision_input("collection_review"), uuid4().hex)
    original_issue = SupervisorSession.issue
    original_append = store.append_evidence

    def issue(self, capture_id, decision_id):
        if fault == "missing":
            raise ValueError("test lost supervisor reply")
        raw, signature = original_issue(self, capture_id, decision_id)
        return raw, b"\0" * 64 if fault == "signature" else signature

    def append(*args, **kwargs):
        if kwargs.get("kind") == "jsonl" and kwargs.get("payload"):
            kwargs["payload"] = b" " + kwargs["payload"]
        return original_append(*args, **kwargs)

    monkeypatch.setattr(SupervisorSession, "issue", issue)
    if fault == "jsonl":
        monkeypatch.setattr(store, "append_evidence", append)
    with running_server(store, local, tmp_path, proceed=True) as server:
        worker, attestations = supervised(store, local, server)
        result = worker.run_once()
        assert result.state == "hold" and result.reason_code == "execution_attestation_unverified", result
        assert attestations.get("tenant-a", job["job_id"], result.attempt) is None
    assert store.get_publication("tenant-a", job["job_id"]) is None
    assert store.get_hold_report("tenant-a", job["job_id"]) is None


def test_cached_issuance_rechecks_cancellation_and_worker_refuses_closure(pg_store, tmp_path, monkeypatch):
    store, local = _worker(pg_store, tmp_path, mode="valid_slow", authority=approved)
    job = store.submit("tenant-a", "research", decision_input("research"), uuid4().hex)
    original = SupervisorSession.issue

    def issue(self, capture_id, decision_id):
        first = original(self, capture_id, decision_id)
        assert original(self, capture_id, decision_id) == first
        assert store.cancel("tenant-a", job["job_id"])
        with pytest.raises((ValueError, EOFError, OSError)):
            original(self, capture_id, decision_id)
        return first

    monkeypatch.setattr(SupervisorSession, "issue", issue)
    with running_server(store, local, tmp_path, proceed=True) as server:
        worker, _ = supervised(store, local, server)
        result = worker.run_once()
        assert result.state == "canceled", result
    assert store.get_publication("tenant-a", job["job_id"]) is None


@pytest.mark.parametrize("expired", [False, True])
def test_tenant_scoped_worker_does_not_claim_or_recover_another_tenant(pg_store, tmp_path, expired):
    store, local = _worker(pg_store, tmp_path, mode="valid_slow")
    foreign = store.submit("tenant-b", "research", decision_input("research"), uuid4().hex)
    if expired:
        assert store.claim(30, allowed_stages=("research",), tenant_id="tenant-b")
        with store.connect() as conn:
            conn.execute(sql.SQL("UPDATE {} SET lease_until=clock_timestamp()-interval '1 second' WHERE job_id=%s")
                .format(store._table("jobs")), (foreign["job_id"],))
    own = store.submit("tenant-a", "research", decision_input("research"), uuid4().hex)
    with running_server(store, local, tmp_path) as server:
        worker, _ = supervised(store, local, server)
        result = worker.run_once()
        assert result.job_id == own["job_id"] and result.state == "hold"
    with store.connect() as conn:
        row = conn.execute(sql.SQL("SELECT state, attempt_count FROM {} WHERE job_id=%s")
                           .format(store._table("jobs")), (foreign["job_id"],)).fetchone()
    assert row == {"state": "researching" if expired else "queued", "attempt_count": int(expired)}
