"""Real-process and PostgreSQL worker tests with self-authored synthetic inputs."""

from hashlib import sha256
import json
import os
from pathlib import Path
import sys
import time
from uuid import uuid4
from dataclasses import replace
from concurrent.futures import ThreadPoolExecutor

import pytest
from psycopg import sql

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.cli_contracts import DecisionContract
from app.cli_worker import CliWorker
from app.job_store import JobStore
from test_cli_contracts import input_for, resolver
from test_job_evidence import cli_store
from test_jobs import pg_store


def _fake_cli(tmp_path, mode="valid"):
    path = tmp_path / ("codex-" + uuid4().hex)
    script = """#!/usr/bin/env python3
import json
import os
import pathlib
import subprocess
import sys
import time
if '--version' in sys.argv:
    if 'CODEX_API_KEY' in os.environ:
        sys.exit(7)
    print('codex-cli 0.157.1')
    sys.exit(0)
args = sys.argv
target = pathlib.Path(args[args.index('--output-last-message') + 1])
prompt = sys.stdin.buffer.read()
context = json.loads(prompt.split(b'\\n')[-2])
if MODE == 'timeout':
    time.sleep(30)
if MODE == 'leader_exit_child':
    child = subprocess.Popen([sys.executable, '-c',
        'import signal,time; signal.signal(signal.SIGTERM, signal.SIG_IGN); time.sleep(30)'])
    pathlib.Path(PID_MARKER).write_text(str(child.pid))
    time.sleep(0.1)
value = {'schema_version': 'decision_v1', 'stage': context['stage'],
         'input_sha256': context['input_sha256'],
         'proposed_status': 'proceed' if context['server_allows_proceed'] else 'hold',
         'selected_ids': ['candidate-a'] if context['server_allows_proceed'] else [],
         'rejected_ids': [], 'claims': [],
         'missing_evidence': context['server_missing_evidence'],
         'reason': 'Synthetic evidence is insufficient.',
         'decision_context_id': context['input']['decision_context_id'],
         'decision_at_utc': context['input']['decision_at_utc'],
         'claim_mode': context['input']['claim_mode'],
         'decision_time_kind': context['input']['decision_time_kind']}
final = json.dumps(value, sort_keys=True, separators=(',', ':'))
if MODE != 'missing_final':
    target.write_text(final)
print(json.dumps({'type': 'thread.started'}))
print(json.dumps({'type': 'turn.started'}))
if MODE == 'tool':
    print(json.dumps({'type': 'item.completed', 'item': {'id': 'tool-1',
        'type': 'command_execution', 'command': 'forbidden'}}))
print(json.dumps({'type': 'item.completed', 'item': {'id': 'message-1',
    'type': 'agent_message', 'text': final if MODE != 'mismatch' else '{}'}}))
print(json.dumps({'type': 'turn.completed', 'usage': {'input_tokens': 1,
    'output_tokens': 1}}))
"""
    path.write_text(script.replace("PID_MARKER", repr(str(tmp_path / "grandchild.pid")))
                         .replace("MODE", repr(mode)))
    path.chmod(0o700)
    return path


def _worker(pg_store, tmp_path, mode="valid", *, timeout=10, authority=resolver):
    contract = DecisionContract(authority)
    trusted = cli_store(pg_store)
    trusted = JobStore(trusted._dsn, trusted.schema, trusted.artifact_root,
                       decision_validator=contract,
                       evidence_policy=trusted.evidence_policy,
                       principal_provider=trusted.principal_provider)
    home = tmp_path / "codex-home"
    home.mkdir(mode=0o700)
    return trusted, CliWorker(trusted, contract, cli_path=_fake_cli(tmp_path, mode),
                              codex_home=home, child_env={"CODEX_API_KEY": "synthetic-test-key"},
                              timeout_seconds=timeout,
                              lease_seconds=timeout + 10, synthetic_smoke=True)


def _submit(store, stage):
    return store.submit("tenant-a", stage, input_for(stage), uuid4().hex)


def test_worker_claims_only_ai_stages_and_records_real_process_hold(pg_store, tmp_path):
    store, worker = _worker(pg_store, tmp_path)
    store.submit("tenant-a", "collection", {"fixture": "synthetic"}, uuid4().hex)
    job = _submit(store, "research")
    argv = worker._argv(worker.cli_path, tmp_path, tmp_path / "schema", tmp_path / "final")
    assert argv[argv.index("-m") + 1] == "gpt-6-sol"
    assert argv[argv.index("-c") + 1] == 'model_reasoning_effort="xhigh"'
    assert argv[argv.index("--sandbox") + 1] == "read-only"
    assert "--ignore-user-config" in argv and "--json" in argv
    result = worker.run_once()
    assert result.state == "hold" and result.reason_code == "validated_hold"
    assert result.job_id == job["job_id"] and result.capture_id and result.decision_id
    assert store.get_job("tenant-a", job["job_id"])["state"] == "hold"
    assert json.loads(store.read_hold_report("tenant-a", job["job_id"])) == {
        "schema_version": "hold_v1", "reason_code": "evidence_missing",
        "missing_evidence": ["real_source_g0"]}
    assert store.get_hold_report("tenant-b", job["job_id"]) is None
    assert len(store.list_decisions("tenant-a", job["job_id"])) == 1
    assert store.claim(60, allowed_stages=("research", "collection_review", "assessment")) is None


def test_server_authorized_research_proceed_publishes_safe_projection(pg_store, tmp_path):
    def approved(job, value):
        return replace(resolver(job, value), allow_proceed=True, missing_evidence=())

    store, worker = _worker(pg_store, tmp_path, authority=approved)
    value = input_for("research")
    value.update(decision_context_id="decision-context-v1:" + "c" * 64,
                 decision_at_utc="2026-01-03T00:00:00Z",
                 claim_mode="ex_ante", decision_time_kind="hypothetical")
    job = store.submit("tenant-a", "research", value, uuid4().hex)
    result = worker.run_once()
    assert result.state == "succeeded" and result.capture_id and result.decision_id
    publication = store.get_publication("tenant-a", job["job_id"])
    assert publication is not None
    assert publication["manifest"]["stage"] == "research"


@pytest.mark.parametrize("mode,code", [("tool", "unapproved_tool_event"),
                                        ("mismatch", "final_jsonl_mismatch")])
def test_worker_rejects_tool_or_final_mismatch_without_decision(pg_store, tmp_path, mode, code):
    store, worker = _worker(pg_store, tmp_path, mode)
    job = _submit(store, "collection_review")
    result = worker.run_once()
    assert result.state == "hold" and result.reason_code == code
    assert store.list_decisions("tenant-a", job["job_id"]) == []
    assert store.get_hold_report("tenant-a", job["job_id"]) is None
    assert store.list_attempt_outcomes("tenant-a", job["job_id"])[0]["decision_id"] is None


def test_worker_timeout_has_no_fake_decision_and_retries_with_new_attempt(pg_store, tmp_path):
    store, worker = _worker(pg_store, tmp_path, "timeout", timeout=1)
    job = _submit(store, "assessment")
    result = worker.run_once()
    assert result.reason_code == "cli_timeout"
    assert result.state == "queued"
    assert store.list_decisions("tenant-a", job["job_id"]) == []
    outcomes = store.list_attempt_outcomes("tenant-a", job["job_id"])
    assert outcomes[0]["decision_id"] is None
    time.sleep(1.1)
    new = store.claim(60, allowed_stages=("assessment",))
    assert new["attempt_id"] != outcomes[0]["attempt_id"]


def test_unknown_input_version_fails_before_cli_launch(pg_store, tmp_path):
    store, worker = _worker(pg_store, tmp_path)
    job = store.submit("tenant-a", "collection_review",
                       {"input_version": "thermal-g1-collection-review-input-v1",
                        "snapshot_id": "synthetic-fixture"}, uuid4().hex)
    result = worker.run_once()
    assert result.state == "hold" and result.reason_code == "unknown_input_version"
    assert store.get_invocation("tenant-a", job["job_id"], 1) is None


def test_missing_final_has_no_invented_capture_hash(pg_store, tmp_path):
    store, worker = _worker(pg_store, tmp_path, "missing_final")
    job = _submit(store, "research")
    result = worker.run_once()
    assert result.state == "failed" and result.reason_code == "final_missing"
    assert store.list_decisions("tenant-a", job["job_id"]) == []
    with store.connect() as conn:
        capture = conn.execute(sql.SQL("SELECT final_output_sha256 FROM {} WHERE job_id = %s")
                               .format(store._table("attempt_cli_captures")),
                               (job["job_id"],)).fetchone()
    assert capture is None


def test_leader_exit_does_not_leave_credential_holding_child(pg_store, tmp_path):
    store, worker = _worker(pg_store, tmp_path, "leader_exit_child")
    _submit(store, "research")
    result = worker.run_once()
    assert result.state == "hold"
    pid = int((tmp_path / "grandchild.pid").read_text())
    status = Path(f"/proc/{pid}/stat")
    assert not status.exists() or status.read_text().split()[2] == "Z"


def test_watchdog_kills_process_while_launch_store_call_stalls(pg_store, tmp_path):
    store, worker = _worker(pg_store, tmp_path, "timeout", timeout=1)
    _submit(store, "research")
    original = store.record_cli_launch
    def slow_launch(*args, **kwargs):
        time.sleep(2)
        return original(*args, **kwargs)
    store.record_cli_launch = slow_launch
    result = worker.run_once()
    assert result.reason_code == "cli_timeout"
    assert result.state == "queued"


def test_running_cancellation_fences_and_kills_cli(pg_store, tmp_path):
    store, worker = _worker(pg_store, tmp_path, "timeout", timeout=10)
    job = _submit(store, "research")
    with ThreadPoolExecutor(max_workers=1) as pool:
        future = pool.submit(worker.run_once)
        for _ in range(100):
            if store.get_invocation("tenant-a", job["job_id"], 1):
                break
            time.sleep(0.05)
        assert store.cancel("tenant-a", job["job_id"])
        result = future.result(timeout=12)
    assert result.state == "canceled"
    assert store.list_decisions("tenant-a", job["job_id"]) == []


def test_exhausted_timeout_reports_terminal_store_state(pg_store, tmp_path):
    store, worker = _worker(pg_store, tmp_path, "timeout", timeout=1)
    job = store.submit("tenant-a", "research", input_for("research"), uuid4().hex,
                       max_attempts=1)
    result = worker.run_once()
    assert result.state == "failed" and result.reason_code == "cli_timeout"
    assert store.get_job("tenant-a", job["job_id"])["state"] == "failed"


def test_credential_sources_are_exclusive_and_symlinks_fail_closed(pg_store, tmp_path):
    store, worker = _worker(pg_store, tmp_path)
    source_home = tmp_path / "source-home"
    source_home.mkdir(mode=0o700)
    credential = source_home / "auth.json"
    credential.write_bytes(b"synthetic credential")
    credential.chmod(0o600)
    with pytest.raises(ValueError, match="one Codex credential"):
        CliWorker(store, worker.contract, cli_path=worker.cli_path,
                  codex_home=source_home,
                  child_env={"CODEX_API_KEY": "synthetic-test-key"},
                  synthetic_smoke=True)
    credential.unlink()
    credential.symlink_to(tmp_path / "nonexistent")
    worker = CliWorker(store, worker.contract, cli_path=worker.cli_path,
                       codex_home=source_home, synthetic_smoke=True,
                       timeout_seconds=10, lease_seconds=20)
    job = _submit(store, "research")
    result = worker.run_once()
    assert result.state == "failed" and result.reason_code == "credential_unavailable"
    assert store.get_invocation("tenant-a", job["job_id"], 1) is not None
    assert store.list_decisions("tenant-a", job["job_id"]) == []


def test_unexpected_store_error_closes_attempt_without_decision(pg_store, tmp_path):
    store, worker = _worker(pg_store, tmp_path)
    job = _submit(store, "research")
    original = store.append_evidence
    seen = False
    def flaky(*args, **kwargs):
        nonlocal seen
        if not seen:
            seen = True
            raise RuntimeError("synthetic database error")
        return original(*args, **kwargs)
    store.append_evidence = flaky
    result = worker.run_once()
    assert result.state == "failed" and result.reason_code == "worker_runtime_error"
    assert store.list_decisions("tenant-a", job["job_id"]) == []


def test_production_constructor_rejects_unattested_launcher(pg_store, tmp_path):
    store, worker = _worker(pg_store, tmp_path)
    with pytest.raises(ValueError, match="isolation"):
        CliWorker(store, worker.contract, cli_path=worker.cli_path,
                  codex_home=worker.codex_home)


if os.environ.get("OSSF_REAL_CLI_SMOKE") == "1":
    def test_real_cli_three_stage_synthetic_hold(pg_store, tmp_path):
        cli = Path(os.environ["OSSF_REAL_CLI_PATH"])
        home = Path(os.environ["OSSF_REAL_CODEX_HOME"])
        contract = DecisionContract(resolver)
        base = cli_store(pg_store)
        store = JobStore(base._dsn, base.schema, base.artifact_root,
                         decision_validator=contract, evidence_policy=base.evidence_policy,
                         principal_provider=base.principal_provider)
        worker = CliWorker(store, contract, cli_path=cli, codex_home=home,
                           timeout_seconds=600, lease_seconds=660, synthetic_smoke=True)
        jobs = [_submit(store, stage) for stage in
                ("research", "collection_review", "assessment")]
        for job in jobs:
            result = worker.run_once()
            assert result.job_id == job["job_id"]
            assert result.state == "hold" and result.reason_code == "validated_hold"
            assert result.capture_id and result.decision_id
            assert store.read_hold_report("tenant-a", job["job_id"])
            invocation = store.get_invocation("tenant-a", job["job_id"], result.attempt)
            assert invocation["execution_kind"] == "codex_cli"
            assert (invocation["model"], invocation["reasoning_effort"]) == ("gpt-6-sol", "xhigh")
            with store.connect() as conn:
                capture = conn.execute(sql.SQL("""
                    SELECT capture_id, jsonl_sha256, final_output_sha256, exit_code,
                           termination_reason, usage FROM {}
                    WHERE tenant_id = %s AND job_id = %s AND attempt = %s
                """).format(store._table("attempt_cli_captures")),
                    ("tenant-a", job["job_id"], result.attempt)).fetchone()
            assert capture["capture_id"] == result.capture_id
            assert capture["exit_code"] == 0 and capture["termination_reason"] == "completed"
            assert capture["jsonl_sha256"] and capture["final_output_sha256"]
            assert capture["usage"]["input_tokens"] > 0
            print(json.dumps({"stage": job["stage"], "job_id": str(job["job_id"]),
                              "attempt": result.attempt, "capture_id": str(result.capture_id),
                              "decision_id": str(result.decision_id),
                              "jsonl_sha256": capture["jsonl_sha256"],
                              "final_output_sha256": capture["final_output_sha256"],
                              "usage": capture["usage"]}, sort_keys=True))
