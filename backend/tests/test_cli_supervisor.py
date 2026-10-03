"""A supervisor candidate must observe the child process and its actual bytes."""

from hashlib import sha256
import json
import multiprocessing
import os
from pathlib import Path
import sys
import time

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.cli_contracts import SCHEMA_BYTES
from app.cli_supervisor import CliProcessSupervisor
from test_cli_worker import _fake_cli


def _prompt():
    context = {
        "stage": "collection_review", "input_sha256": "a" * 64,
        "server_allows_proceed": False, "server_missing_evidence": ["test_hold"],
        "input": {"decision_context_id": "context-a",
                  "decision_at_utc": "2026-01-03T00:00:00Z",
                  "claim_mode": "ex_post_replay",
                  "decision_time_kind": "hypothetical"},
    }
    return b"fixed test instruction\n" + json.dumps(context, sort_keys=True,
        separators=(",", ":")).encode() + b"\n"


def _observe_in_child(binary, home, output):
    with CliProcessSupervisor(Path(binary), Path(home),
                              child_env={"CODEX_API_KEY": "test-only"},
                              timeout_seconds=5) as supervisor:
        launch = supervisor.start(_prompt())
        result = None
        for _ in range(100):
            result = supervisor.poll()
            if result is not None:
                break
            time.sleep(0.02)
        output.put((os.getpid(), launch, result))


def test_supervisor_observes_exact_child_input_output_and_wait(tmp_path):
    home = tmp_path / "private-home"
    home.mkdir(mode=0o700)
    binary = _fake_cli(tmp_path)
    prompt = _prompt()
    with CliProcessSupervisor(binary, home,
                              child_env={"CODEX_API_KEY": "test-only"},
                              timeout_seconds=5) as supervisor:
        launch = supervisor.start(prompt)
        assert launch.process_id > 0
        assert launch.process_start_token.isdecimal()
        assert launch.executable_sha256 == sha256(binary.read_bytes()).hexdigest()
        assert launch.prompt_sha256 == sha256(prompt).hexdigest()
        assert launch.schema_sha256 == sha256(SCHEMA_BYTES).hexdigest()
        assert launch.argv[launch.argv.index("-m") + 1] == "gpt-6.1-sol"
        assert launch.argv[launch.argv.index("-c") + 1] == 'model_reasoning_effort="xhigh"'
        assert launch.argv[launch.argv.index("--sandbox") + 1] == "read-only"
        for _ in range(100):
            result = supervisor.poll()
            if result is not None:
                break
            time.sleep(0.02)
        assert result is not None and result.exit_code == 0
        assert result.termination_reason == "completed"
        assert result.jsonl_sha256 == sha256(result.jsonl).hexdigest()
        assert result.final_output_sha256 == sha256(result.final_output).hexdigest()
        assert result.usage == {"input_tokens": 1, "output_tokens": 1}
        assert result.started_at_utc <= result.ended_at_utc
        assert supervisor.poll() == result
    assert (tmp_path / "actual-prompt.sha256").read_text() == launch.prompt_sha256
    assert (tmp_path / "actual-schema.sha256").read_text() == launch.schema_sha256


def test_supervisor_closes_timeout_without_success_observation(tmp_path):
    home = tmp_path / "private-home"
    home.mkdir(mode=0o700)
    binary = _fake_cli(tmp_path, "timeout")
    with CliProcessSupervisor(binary, home,
                              child_env={"CODEX_API_KEY": "test-only"},
                              timeout_seconds=1) as supervisor:
        supervisor.start(_prompt())
        result = None
        for _ in range(100):
            result = supervisor.poll()
            if result is not None:
                break
            time.sleep(0.02)
        assert result is not None and result.termination_reason == "cli_timeout"
        assert result.exit_code != 0
        assert result.final_output is None


def test_finished_child_is_not_misclassified_when_observer_polls_late(tmp_path):
    home = tmp_path / "private-home"
    home.mkdir(mode=0o700)
    with CliProcessSupervisor(_fake_cli(tmp_path), home,
                              child_env={"CODEX_API_KEY": "test-only"},
                              timeout_seconds=1) as supervisor:
        supervisor.start(_prompt())
        time.sleep(1.1)
        result = supervisor.poll()
        assert result is not None and result.exit_code == 0
        assert result.termination_reason == "completed"


def test_observation_core_runs_in_a_separate_process(tmp_path):
    home = tmp_path / "private-home"
    home.mkdir(mode=0o700)
    binary = _fake_cli(tmp_path)
    context = multiprocessing.get_context("spawn")
    output = context.Queue()
    observer = context.Process(target=_observe_in_child,
                               args=(str(binary), str(home), output))
    observer.start()
    observer.join(timeout=10)
    if observer.is_alive():
        observer.terminate()
        observer.join(timeout=2)
    assert observer.exitcode == 0
    observer_pid, launch, result = output.get(timeout=2)
    assert observer_pid != os.getpid() != launch.process_id
    assert launch.process_id != observer_pid
    assert result is not None and result.termination_reason == "completed"


def test_supervisor_exit_reaps_unfinished_child(tmp_path):
    home = tmp_path / "private-home"
    home.mkdir(mode=0o700)
    with CliProcessSupervisor(_fake_cli(tmp_path, "timeout"), home,
                              child_env={"CODEX_API_KEY": "test-only"},
                              timeout_seconds=5) as supervisor:
        launch = supervisor.start(_prompt())
        assert supervisor.poll() is None
    with pytest.raises(ProcessLookupError):
        os.kill(launch.process_id, 0)
