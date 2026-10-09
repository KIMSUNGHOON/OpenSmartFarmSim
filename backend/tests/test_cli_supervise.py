"""Fresh foreground command and real socket lifecycle; fake CLI/key, no gate claim."""

from contextlib import contextmanager
from hashlib import sha256
import json
import os
from pathlib import Path
import signal
import socket
import subprocess
import sys
import time

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from app.cli_ipc import MAX_REQUEST, receive, send
from test_cli_worker import _fake_cli


@pytest.fixture
def command(tmp_path):
    (tmp_path / "factory_probe.py").write_text('''
import json, os
from pathlib import Path
from app.cli_contracts import DecisionContract
from app.cli_supervisor_service import SupervisorServer
from app.job_store import JobStore
def create():
    value = json.loads(Path(os.environ["OSSF_FACTORY_FIXTURE"]).read_bytes())
    store = JobStore("dbname=unused", "unused", Path(value.pop("artifacts")),
                     decision_validator=DecisionContract(lambda job, value: None))
    return SupervisorServer(store, **value)
def wrong():
    return None
def broken():
    raise RuntimeError("private fixture detail")
''')
    home = tmp_path / "home"
    home.mkdir(mode=0o700)
    key = tmp_path / "key"
    key.write_bytes(b"x" * 32)
    key.chmod(0o600)
    cli = _fake_cli(tmp_path)
    settings = dict(artifacts=str(tmp_path / "artifacts"), socket_path=str(tmp_path / "rpc"),
        worker_uid=os.getuid(), tenant_id="tenant-a", key_file=str(key), key_id="test-v1",
        cli_path=str(cli), codex_home=str(home), executable_sha256=sha256(cli.read_bytes()).hexdigest(),
        environment_sha256="e" * 64, child_env={"CODEX_API_KEY": "synthetic-test-key"})
    config = tmp_path / "config.json"
    config.write_text(json.dumps(settings))
    config.chmod(0o600)
    return dict(cwd=Path(__file__).resolve().parents[1], stdout=subprocess.PIPE, stderr=subprocess.PIPE,
        env={"HOME": str(home), "PATH": "/usr/bin:/bin", "LANG": "C.UTF-8",
             "PYTHONPATH": str(tmp_path), "OSSF_FACTORY_FIXTURE": str(config)})


def argv(extra=()):
    return [sys.executable, "-B", "-m", "app.cli_supervise", "--factory", "factory_probe:create", *extra]


@contextmanager
def running(command, extra=()):
    process = subprocess.Popen(argv(extra), **command)
    try:
        yield process
    finally:
        if process.poll() is None:
            process.terminate()
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait(timeout=5)


@pytest.mark.parametrize("stop", ["session", "sigterm"])
def test_fresh_command_serves_then_removes_its_socket(command, tmp_path, stop):
    path = tmp_path / "rpc"
    with running(command, ("--max-sessions", "1") if stop == "session" else ()) as process:
        deadline = time.monotonic() + 5
        while not path.exists():
            assert process.poll() is None and time.monotonic() < deadline
            time.sleep(0.02)
        if stop == "session":
            with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as connection:
                connection.connect(str(path))
                send(connection, {"version": 1, "op": "version"}, MAX_REQUEST)
                reply = receive(connection, MAX_REQUEST)
                assert reply["ok"] is True and reply["data"]["tenant_id"] == "tenant-a"
                assert reply["data"]["cli_version"] == "codex-cli 0.157.1"
                send(connection, {"version": 1, "op": "stop"}, MAX_REQUEST)
                assert receive(connection, MAX_REQUEST) == {"ok": True, "data": None}
        else:
            process.send_signal(signal.SIGTERM)
        stdout, stderr = process.communicate(timeout=5)
        assert process.returncode == 0 and stdout == stderr == b""
    assert not path.exists()


@pytest.mark.parametrize("extra", [("--factory", "fixture-secret"), ("--factory", "absent_factory:create"),
    ("--factory", "factory_probe:wrong"), ("--factory", "factory_probe:broken"),
    ("--max-sessions", "0"), ("--max-sessions", "fixture-secret"), ("--unknown", "fixture-secret")])
def test_startup_rejections_never_echo_arguments_or_factory_details(command, extra):
    completed = subprocess.run(argv(extra), **command, timeout=5)
    assert completed.returncode == 2 and completed.stdout == b""
    assert json.loads(completed.stderr) == {"version": 1, "ok": False, "code": "supervisor_startup_rejected"}


def test_existing_socket_path_is_preserved_and_serve_error_is_fixed(command, tmp_path):
    path = tmp_path / "rpc"
    path.write_bytes(b"preserved fixture bytes")
    completed = subprocess.run(argv(), **command, timeout=5)
    assert completed.returncode == 3 and completed.stdout == b""
    assert json.loads(completed.stderr) == {"version": 1, "ok": False, "code": "supervisor_service_failed"}
    assert path.read_bytes() == b"preserved fixture bytes"
