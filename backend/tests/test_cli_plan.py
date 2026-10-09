"""Fresh foreground planning command; test keys and one shared OS identity."""

from contextlib import contextmanager
from dataclasses import asdict
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import time

from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from cryptography.hazmat.primitives.serialization import Encoding, PrivateFormat, PublicFormat, NoEncryption
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from app.planning_events import DecisionContextVerifier
from app.planning_rpc import PlanningClient
from app.thermal_run_store import ThermalRunStore
from login_database import login_scope
from test_planning_roles import scope, login_database
from test_thermal_run_store import raw_inputs


def options(tmp_path, config=None):
    (tmp_path / "planning_probe.py").write_text('''
def wrong():
    return None
def broken():
    raise RuntimeError("private fixture detail")
''')
    return dict(cwd=Path(__file__).resolve().parents[1], stdout=subprocess.PIPE, stderr=subprocess.PIPE,
        env={"HOME": str(tmp_path), "PATH": "/usr/bin:/bin", "LANG": "C.UTF-8",
             "PYTHONPATH": os.pathsep.join((str(tmp_path), str(Path(__file__).resolve().parent))),
             "OSSF_PLANNING_FIXTURE_CONFIG": str(config or tmp_path / "absent")})


def argv(extra=()):
    return [sys.executable, "-B", "-m", "app.cli_plan", "--factory", "uid_planning_factory:create", *extra]


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


def listening(process, path):
    deadline = time.monotonic() + 10
    while not path.exists():
        assert process.poll() is None and time.monotonic() < deadline
        time.sleep(0.02)
    time.sleep(0.02)


def configuration(scope, tmp_path, path, *, wrong_login=False):
    _, policy, stores, dsns = scope
    key = Ed25519PrivateKey.generate()
    private = tmp_path / "planning-key"
    private.write_bytes(key.private_bytes(Encoding.Raw, PrivateFormat.Raw, NoEncryption()))
    private.chmod(0o600)
    config = tmp_path / "planning-config.json"
    config.write_text(json.dumps(dict(policy=asdict(policy), dsn=dsns["supervisor" if wrong_login else "authority"],
        private_key_file=str(private), key_id="test-planning-v1",
        snapshot={"tenant_id": "tenant-a", "snapshot_id": "snapshot-a"},
        settings=dict(socket_path=str(path), caller_uid=os.getuid(), tenant_id="tenant-a"))))
    config.chmod(0o600)
    public = key.public_key().public_bytes(Encoding.Raw, PublicFormat.Raw)
    verifier = DecisionContextVerifier({"test-planning-v1": public}, stores["supervisor"].read_event)
    return config, verifier


def test_fresh_planning_command_issues_with_real_writer_and_reader(scope, tmp_path):
    with tempfile.TemporaryDirectory(prefix="ossf-plan-command-") as directory:
        path = Path(directory) / "rpc"
        config, verifier = configuration(scope, tmp_path, path)
        with running(options(tmp_path, config), ("--max-sessions", "1")) as process:
            listening(process, path)
            client = PlanningClient(path, planning_uid=os.getuid(), tenant_id="tenant-a", verifier=verifier)
            raw, signature = client.issue("snapshot-a", claim_mode="ex_post_replay", decision_time_kind="actual")
            assert verifier(raw, signature) is not None
            stdout, stderr = process.communicate(timeout=10)
            assert process.returncode == 0 and stdout == stderr == b"" and not path.exists()


def test_idle_foreground_sigterm_cleans_up_socket(scope, tmp_path):
    with tempfile.TemporaryDirectory(prefix="ossf-plan-term-") as directory:
        path = Path(directory) / "rpc"
        config, _ = configuration(scope, tmp_path, path)
        with running(options(tmp_path, config)) as process:
            listening(process, path)
            process.terminate()
            stdout, stderr = process.communicate(timeout=10)
            assert process.returncode == 0 and stdout == stderr == b"" and not path.exists()


@pytest.mark.parametrize("fault", ["wrong_login", "existing_socket"])
def test_service_admission_failures_are_fixed_and_preserve_existing_path(scope, tmp_path, fault):
    with tempfile.TemporaryDirectory(prefix="ossf-plan-admission-") as directory:
        path = Path(directory) / "rpc"
        config, _ = configuration(scope, tmp_path, path, wrong_login=fault == "wrong_login")
        if fault == "existing_socket": path.write_bytes(b"operator-owned existing path")
        result = subprocess.run(argv(("--max-sessions", "1")), **options(tmp_path, config), timeout=10)
        assert result.returncode == 3 and result.stdout == b""
        assert json.loads(result.stderr) == {"version": 1, "ok": False, "code": "planning_service_failed"}
        if fault == "existing_socket": assert path.read_bytes() == b"operator-owned existing path"
        else: assert not path.exists()


@pytest.mark.parametrize("extra", [(), ("--factory", "bad factory"), ("--factory", "planning_probe:wrong"),
    ("--factory", "planning_probe:broken"), ("--max-sessions", "0"), ("--max-sessions", "invalid")])
def test_startup_rejects_without_private_exception_details(tmp_path, extra):
    result = subprocess.run(argv(extra), **options(tmp_path), timeout=10)
    assert result.returncode == 2 and result.stdout == b""
    assert json.loads(result.stderr) == {"version": 1, "ok": False, "code": "planning_startup_rejected"}


def test_static_help_does_not_construct_absent_factory(tmp_path):
    result = subprocess.run(argv(("--help",)), **options(tmp_path), timeout=10)
    assert result.returncode == 0 and result.stderr == b"" and b"ossf-plan" in result.stdout


def test_fresh_client_command_persists_context_and_review_with_authenticated_profiles(scope, login_scope, tmp_path):
    base, job_policy, job_dsns = login_scope
    principal = lambda: {"authenticated": True, "tenant_id": "tenant-a", "scopes": ("thermal_snapshot_write",)}
    snapshots = ThermalRunStore(base._dsn, base.schema, gate_key=b"unused-synthetic-controller-key-32!",
                                release_verifier=lambda *_: None, principal_provider=principal)
    snapshot = snapshots.put_snapshot("tenant-a", *raw_inputs())
    with tempfile.TemporaryDirectory(prefix="ossf-plan-client-") as directory:
        path = Path(directory) / "rpc"
        config, verifier = configuration(scope, tmp_path, path)
        value = json.loads(config.read_bytes())
        value["snapshot"]["snapshot_id"] = snapshot
        config.write_text(json.dumps(value))
        public = verifier.public_keys["test-planning-v1"].public_bytes(Encoding.Raw, PublicFormat.Raw)
        client_config = tmp_path / "client-config.json"
        client_config.write_text(json.dumps(dict(uid=os.getuid(), tenant_id="tenant-a",
            planning_policy=asdict(scope[1]), job_policy=asdict(job_policy), reader_dsn=scope[3]["supervisor"],
            job_dsn=job_dsns["authority"], key_id="test-planning-v1", public_key=public.hex(),
            planning_uid=os.getuid(), socket_path=str(path), snapshot_id=snapshot,
            artifact_root=str(tmp_path / "artifacts"), denied_paths=[])))
        client_config.chmod(0o600)
        with running(options(tmp_path, config), ("--max-sessions", "2")) as process:
            listening(process, path)
            command = options(tmp_path)
            command["env"]["OSSF_PLANNING_CLIENT_FIXTURE_CONFIG"] = str(client_config)
            result = subprocess.run([sys.executable, "-B", "-m", "uid_planning_client"], **command, timeout=20)
            assert result.returncode == 0 and result.stdout == result.stderr == b""
            stdout, stderr = process.communicate(timeout=10)
            assert process.returncode == 0 and stdout == stderr == b"" and not path.exists()
