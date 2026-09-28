"""Fresh authority application command, actual SCRAM, fake CLI/key; no gate acceptance."""

from contextlib import contextmanager
import copy
from dataclasses import asdict
import json
import os
from pathlib import Path
import signal
import subprocess
import sys
import tempfile
import time
from uuid import uuid4

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from app.authority_rpc import AuthorityClient
from app.content_access import ContentAccess
from login_database import login_database, login_scope
from test_cli_contracts import resolver
from test_cli_supervisor_service import approved, running_server
from test_cli_worker import _worker
from test_supervised_cli_worker import decision_input


def command(tmp_path, config=None):
    (tmp_path / "authority_probe.py").write_text('''
def wrong():
    return None
def broken():
    raise RuntimeError("private fixture detail")
''')
    return dict(cwd=Path(__file__).resolve().parents[1], stdout=subprocess.PIPE, stderr=subprocess.PIPE,
        env={"HOME": str(tmp_path), "PATH": "/usr/bin:/bin", "LANG": "C.UTF-8",
             "PYTHONPATH": os.pathsep.join((str(tmp_path), str(Path(__file__).resolve().parent))),
             "OSSF_AUTHORITY_FIXTURE_CONFIG": str(config or tmp_path / "absent-config")})


def argv(extra=()):
    return [sys.executable, "-B", "-m", "app.cli_authority",
            "--factory", "uid_authority_factory:create", *extra]


@contextmanager
def running(options, extra=()):
    process = subprocess.Popen(argv(extra), **options)
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


def listening(process, path):
    deadline = time.monotonic() + 10
    while not path.exists():
        assert process.poll() is None and time.monotonic() < deadline
        time.sleep(0.02)


@pytest.mark.parametrize("stage", ["research", "collection_review", "assessment"])
def test_fresh_authority_command_dispatches_with_authenticated_profiles(login_scope, tmp_path, stage):
    base, policy, dsns = login_scope
    proceed = stage != "assessment"
    store, local = _worker(base, tmp_path, mode="valid_slow", authority=approved if proceed else resolver)
    store.content_access = ContentAccess(os.getuid(), os.getgid())
    job = store.submit("tenant-a", stage, decision_input(stage), uuid4().hex)
    supervisor = copy.copy(store)
    supervisor._dsn, supervisor.runtime_identity = dsns["supervisor"], (policy, "supervisor")
    with running_server(supervisor, local, tmp_path, proceed=proceed) as (endpoint, public, settings, _process):
        with tempfile.TemporaryDirectory(prefix="ossf-authority-command-") as directory:
            path = Path(directory) / "rpc"
            config = tmp_path / "authority-config.json"
            config.write_text(json.dumps(dict(policy=asdict(policy), dsn=dsns["authority"],
                artifact_root=str(store.artifact_root), content_access=asdict(store.content_access),
                proceed=proceed, key_id="test-supervisor-v1", public_key=public.hex(),
                supervisor=dict(socket_path=str(endpoint), supervisor_uid=os.getuid(), tenant_id="tenant-a",
                    executable_sha256=settings["executable_sha256"], environment_sha256=settings["environment_sha256"]),
                settings=dict(socket_path=str(path), worker_uid=os.getuid(), tenant_id="tenant-a"))))
            config.chmod(0o600)
            with running(command(tmp_path, config), ("--max-sessions", "1")) as process:
                listening(process, path)
                result = AuthorityClient(path, authority_uid=os.getuid(), tenant_id="tenant-a",
                                         wait_seconds=15).run_once()
                assert result.job_id == job["job_id"] and result.state == ("succeeded" if proceed else "hold")
                assert result.capture_id is not None and result.decision_id is not None
                stdout, stderr = process.communicate(timeout=5)
                assert process.returncode == 0 and stdout == stderr == b""
            assert not path.exists()
    assert store.get_job("tenant-a", job["job_id"])["state"] == result.state


@pytest.mark.parametrize("mode", ["sigterm", "wrong_profile", "existing_path"])
def test_authenticated_idle_service_cleanup_and_fixed_admission_errors(login_scope, tmp_path, mode):
    base, policy, dsns = login_scope
    with tempfile.TemporaryDirectory(prefix="ossf-authority-idle-") as directory:
        path = Path(directory) / "rpc"
        if mode == "existing_path":
            path.write_bytes(b"preserved fixture bytes")
        config = tmp_path / "authority-config.json"
        config.write_text(json.dumps(dict(policy=asdict(policy),
            dsn=dsns["supervisor" if mode == "wrong_profile" else "authority"],
            artifact_root=str(base.artifact_root), content_access=dict(owner_uid=os.getuid(), reader_gid=os.getgid()),
            proceed=False, key_id="test-supervisor-v1", public_key=(b"p" * 32).hex(),
            supervisor=dict(socket_path=str(Path(directory) / "absent-supervisor"), supervisor_uid=os.getuid(),
                tenant_id="tenant-a", executable_sha256="a" * 64, environment_sha256="b" * 64),
            settings=dict(socket_path=str(path), worker_uid=os.getuid(), tenant_id="tenant-a"))))
        config.chmod(0o600)
        with running(command(tmp_path, config)) as process:
            if mode == "sigterm":
                listening(process, path)
                process.send_signal(signal.SIGTERM)
            stdout, stderr = process.communicate(timeout=5)
            assert stdout == b""
            if mode == "sigterm":
                assert process.returncode == 0 and stderr == b""
            else:
                assert process.returncode == 3
                assert json.loads(stderr) == {"version": 1, "ok": False, "code": "authority_service_failed"}
        if mode == "existing_path":
            assert path.read_bytes() == b"preserved fixture bytes"
        else:
            assert not path.exists()


@pytest.mark.parametrize("extra", [("--factory", "fixture-secret"), ("--factory", "absent_factory:create"),
    ("--factory", "authority_probe:wrong"), ("--factory", "authority_probe:broken"),
    ("--max-sessions", "0"), ("--max-sessions", "fixture-secret"), ("--unknown", "fixture-secret")])
def test_startup_rejections_do_not_echo_arguments_or_factory_exceptions(tmp_path, extra):
    completed = subprocess.run(argv(extra), **command(tmp_path), timeout=5)
    assert completed.returncode == 2 and completed.stdout == b""
    assert json.loads(completed.stderr) == {"version": 1, "ok": False, "code": "authority_startup_rejected"}
