"""Fresh application process and Unix RPC; fixtures make no farm/G1/G4 claims."""

from contextlib import contextmanager
import json
import os
from pathlib import Path
import socket
import subprocess
import sys
import threading
from uuid import uuid4

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from app.cli_ipc import MAX_REQUEST, receive, send


def run(path, *, authority_uid=None, tenant="tenant-a", extra=()):
    return subprocess.run([sys.executable, "-B", "-m", "app.cli_dispatch", "--socket", str(path),
        "--authority-uid", str(os.getuid() if authority_uid is None else authority_uid),
        "--tenant", tenant, "--wait-seconds", "2", *extra],
        cwd=Path(__file__).resolve().parents[1],
        env={"HOME": str(path.parent), "PATH": "/usr/bin:/bin", "LANG": "C.UTF-8"},
        capture_output=True, timeout=5)


@contextmanager
def server(path, reply):
    calls = []
    failures = []
    with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as listener:
        listener.bind(str(path)); listener.listen(2); listener.settimeout(5)
        def serve():
            try:
                conn, _ = listener.accept()
                calls.append("connected")
                with conn:
                    try:
                        value = receive(conn, MAX_REQUEST)
                    except EOFError:
                        return
                    assert value == {"version": 1, "op": "run_next"}
                    calls.append("requested")
                    if reply is not None:
                        send(conn, reply, MAX_REQUEST)
            except BaseException as error:
                failures.append(type(error).__name__)
        worker = threading.Thread(target=serve)
        worker.start()
        try:
            yield calls
        finally:
            worker.join(timeout=5)
            assert not worker.is_alive() and not failures


def response(state):
    result = None if state is None else {
        "job_id": str(uuid4()), "attempt": 1, "state": state, "reason_code": "validated_hold",
        "capture_id": str(uuid4()), "decision_id": str(uuid4())}
    return {"version": 1, "ok": True, "tenant_id": "tenant-a", "result": result}


@pytest.mark.parametrize("state", [None, "succeeded", "hold", "failed", "canceled", "queued", "unclosed"])
def test_fresh_dispatch_process_returns_only_validated_result_and_one_request(tmp_path, state):
    path = tmp_path / "rpc"
    reply = response(state)
    with server(path, reply) as calls:
        completed = run(path)
    assert completed.returncode == 0 and completed.stderr == b""
    assert json.loads(completed.stdout) == reply
    assert calls == ["connected", "requested"]


@pytest.mark.parametrize("fault", ["lost_reply", "tenant", "malformed", "peer"])
def test_unresolved_reply_emits_fixed_error_and_never_retries(tmp_path, fault):
    path = tmp_path / "rpc"
    reply = response("hold")
    if fault == "lost_reply": reply = None
    elif fault == "tenant": reply["tenant_id"] = "tenant-b"
    elif fault == "malformed": reply["result"]["reason_code"] = "private fixture text"
    with server(path, reply) as calls:
        completed = run(path, authority_uid=os.getuid() + 1 if fault == "peer" else None)
    assert completed.returncode == 3 and completed.stdout == b""
    assert json.loads(completed.stderr) == {"version": 1, "ok": False, "code": "authority_dispatch_unresolved"}
    assert calls == (["connected"] if fault == "peer" else ["connected", "requested"])


@pytest.mark.parametrize("extra", [('--wait-seconds', '0'), ('--wait-seconds', '661'),
                                   ('--authority-uid', '-1'), ('--unexpected', 'fixture-secret'),
                                   ('--wait-seconds', 'fixture-secret')])
def test_configuration_errors_do_not_echo_arguments_or_connect(tmp_path, extra):
    completed = run(tmp_path / "absent", extra=extra)
    assert completed.returncode == 2 and completed.stdout == b""
    assert json.loads(completed.stderr) == {"version": 1, "ok": False, "code": "dispatcher_configuration_rejected"}
    assert b"fixture-secret" not in completed.stderr


def test_unavailable_endpoint_emits_no_path_or_driver_details(tmp_path):
    completed = run(tmp_path / "private-endpoint")
    assert completed.returncode == 3 and completed.stdout == b""
    assert b"private-endpoint" not in completed.stderr
