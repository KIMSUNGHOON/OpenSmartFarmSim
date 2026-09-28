"""Explicit root-only service smoke. Fake CLI/test key; not G1/G4 or custody proof."""

from contextlib import contextmanager
from dataclasses import asdict
from datetime import datetime
from hashlib import sha256
import json
import os
from pathlib import Path
import pwd
import select
import signal
import subprocess
import sys
import tempfile
import time
from uuid import uuid4

from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from cryptography.hazmat.primitives.serialization import Encoding, PrivateFormat, NoEncryption, PublicFormat
from psycopg.conninfo import conninfo_to_dict, make_conninfo
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.authority_rpc import AuthorityClient, AuthorityServer, AuthorityDispatchError
from app.cli_ipc import MAX_REQUEST, receive
from app.content_access import ContentAccess
from app.execution_attestation import ExecutionAttestationStore
# Preload the connector before UID drop; the Python installation is controller-owned.
from app.runtime_login import connect_runtime
from login_database import login_database, login_scope
from test_authority_rpc import engine_for, state
from test_cli_contracts import resolver
from test_cli_supervisor_service import approved, connect
from test_cli_worker import _worker
from test_supervised_cli_worker import decision_input


AUTHORITY, SUPERVISOR, WORKER, ROGUE = 11001, 11002, 11003, 11004
CONTENT_GROUP, SUPERVISOR_GROUP, DISPATCH_GROUP = 11010, 11011, 11012


class ProbeFailure(AssertionError):
    """Only internal probe codes and validated WorkResult states/reasons."""


def directory(path, uid, gid, mode):
    path.mkdir(mode=mode)
    path.chmod(mode)
    os.chown(path, uid, gid)
    return path


def private_file(path, data, uid, gid):
    path.write_bytes(data)
    path.chmod(0o600)
    os.chown(path, uid, gid)
    return path


def denied(path, flags=os.O_RDONLY):
    with pytest.raises(PermissionError):
        fd = os.open(path, flags | os.O_NOFOLLOW)
        os.close(fd)


def reap(handle, seconds):
    deadline = time.monotonic() + seconds
    while handle[0] is not None:
        pid, status = os.waitpid(handle[0], os.WNOHANG)
        if pid:
            handle[0] = None  # Never signal a PID after it has been reaped.
            return os.waitstatus_to_exitcode(status)
        if time.monotonic() >= deadline:
            return None
        time.sleep(0.02)


@contextmanager
def child(uid, gid, groups, action, *, home):
    read_fd, write_fd = os.pipe()
    pid = os.fork()
    if pid == 0:
        os.close(read_fd)
        try:
            os.environ.clear()
            os.environ.update(HOME=str(home), PATH="/usr/bin:/bin", LANG="C.UTF-8")
            os.setgroups(groups)
            os.setgid(gid)
            os.setuid(uid)
            assert os.getresuid() == (uid,) * 3 and os.getresgid() == (gid,) * 3
            assert sorted(os.getgroups()) == sorted(groups)
            action()
            os.write(write_fd, b"ok")
            os._exit(0)
        except BaseException as error:
            # Never include driver messages, passwords, paths, prompts or raw CLI output.
            detail = f"{type(error).__name__}:{getattr(error, 'errno', None)}"
            if isinstance(error, ProbeFailure):
                detail += ":" + str(error)
            os.write(write_fd, detail.encode("ascii")[:128])
            os._exit(1)
    os.close(write_fd)
    handle = [pid, read_fd]
    try:
        yield handle
    finally:
        if handle[0] is not None and reap(handle, 0) is None:
            os.kill(handle[0], signal.SIGTERM)
            if reap(handle, 5) is None:
                os.kill(handle[0], signal.SIGKILL)
                os.waitpid(handle[0], 0)
                handle[0] = None
        os.close(read_fd)


def finished(handle, *, executed=False):
    assert select.select([handle[1]], [], [], 15)[0], "UID service deadline"
    response = os.read(handle[1], 128)
    assert response == (b"" if executed else b"ok"), "UID service failed: " + response.decode("ascii")
    assert reap(handle, 2) == 0


def listening(path, handle):
    deadline = time.monotonic() + 10
    while not path.exists():
        if reap(handle, 0) is not None:
            response = os.read(handle[1], 128)
            raise AssertionError("service startup failed: " + response.decode("ascii"))
        assert time.monotonic() < deadline, "service startup deadline"
        time.sleep(0.02)
    time.sleep(0.02)


@pytest.mark.parametrize("stage", ["research", "collection_review", "assessment"])
def test_distinct_uid_services_and_authenticated_roles(login_scope, stage):
    assert os.geteuid() == 0, "explicit hosted root controller required"
    for uid in (AUTHORITY, SUPERVISOR, WORKER, ROGUE):
        with pytest.raises(KeyError):
            pwd.getpwuid(uid)
    base, policy, dsns = login_scope
    proceed = stage != "assessment"
    with tempfile.TemporaryDirectory(prefix="ossf-services-uid-") as temporary:
        root = Path(temporary)
        root.chmod(0o755)  # FD traversal requires read/search on synthetic ancestors.
        sup_home = directory(root / "supervisor", 0, 0, 0o700)
        authority_home = directory(root / "authority", AUTHORITY, DISPATCH_GROUP, 0o700)
        worker_home = directory(root / "worker", WORKER, DISPATCH_GROUP, 0o700)
        rogue_home = directory(root / "rogue", ROGUE, DISPATCH_GROUP, 0o700)
        content = directory(root / "content", AUTHORITY, CONTENT_GROUP, 0o750)
        sup_socket_dir = directory(root / "s", SUPERVISOR, SUPERVISOR_GROUP, 0o750)
        auth_socket_dir = directory(root / "a", AUTHORITY, DISPATCH_GROUP, 0o750)
        for kind, home, uid, gid in (("authority", authority_home, AUTHORITY, DISPATCH_GROUP),
                                   ("supervisor", sup_home, SUPERVISOR, SUPERVISOR_GROUP)):
            source = Path(conninfo_to_dict(dsns[kind])["passfile"])
            target = private_file(home / "db.pgpass", source.read_bytes(), uid, gid)
            dsns[kind] = make_conninfo(dsns[kind], passfile=str(target))
        store, local = _worker(base, sup_home, mode="valid_slow", authority=approved if proceed else resolver)
        store.artifact_root = content / "artifacts"
        store.content_access = ContentAccess(AUTHORITY, CONTENT_GROUP)
        # The fake executable uses only public system Python and records its actual exec identity.
        marker = sup_home / "cli-identity.json"
        script = local.cli_path.read_text().replace("#!/usr/bin/env python3", "#!/usr/bin/python3", 1)
        script = script.replace("args = sys.argv", f"pathlib.Path({str(marker)!r}).write_text(json.dumps("
            "{'uid': list(os.getresuid()), 'gid': list(os.getresgid()), 'groups': os.getgroups()}))\nargs = sys.argv", 1)
        local.cli_path.write_text(script)
        private = Ed25519PrivateKey.generate()
        key = private_file(sup_home / "key", private.private_bytes(Encoding.Raw, PrivateFormat.Raw, NoEncryption()),
                           SUPERVISOR, SUPERVISOR_GROUP)
        public = private.public_key().public_bytes(Encoding.Raw, PublicFormat.Raw)
        for path in [sup_home, *sup_home.rglob("*")]:
            os.chown(path, SUPERVISOR, SUPERVISOR_GROUP)
        settings = dict(socket_path=sup_socket_dir / "rpc", worker_uid=AUTHORITY, tenant_id="tenant-a",
            key_file=key, key_id="test-supervisor-v1", cli_path=local.cli_path, codex_home=local.codex_home,
            executable_sha256=sha256(local.cli_path.read_bytes()).hexdigest(),
            environment_sha256=sha256(b"synthetic-uid-test-environment").hexdigest(),
            child_env=local.child_env, timeout_seconds=10)
        configuration = private_file(sup_home / "service-fixture.json", json.dumps(dict(
            policy=asdict(policy), dsn=dsns["supervisor"], artifact_root=str(store.artifact_root),
            content_access=asdict(store.content_access), proceed=proceed,
            settings={name: str(value) if isinstance(value, Path) else value
                      for name, value in settings.items()})).encode(), SUPERVISOR, SUPERVISOR_GROUP)
        application = Path(sys.executable).parents[2] / "code" / "backend"
        job = store.submit("tenant-a", stage, decision_input(stage), uuid4().hex)
        foreign = store.submit("tenant-b", stage, decision_input(stage), uuid4().hex)

        def supervisor():
            denied(authority_home / "db.pgpass")
            os.chdir(application)
            os.execve(sys.executable, [sys.executable, "-B", "-m", "app.cli_supervise",
                "--factory", "uid_supervisor_factory:create", "--max-sessions", "2"],
                {"HOME": str(sup_home), "PATH": "/usr/bin:/bin", "LANG": "C.UTF-8",
                 "PYTHONPATH": str(application / "tests"),
                 "OSSF_SUPERVISOR_FIXTURE_CONFIG": str(configuration)})

        def authority():
            datetime.strptime("2026-01-03T00:00:00Z", "%Y-%m-%dT%H:%M:%SZ")
            denied(key)
            engine = engine_for(dsns["authority"], store.schema, store.artifact_root, policy,
                settings["socket_path"], public, settings, proceed,
                content_access=store.content_access, supervisor_uid=SUPERVISOR)
            AuthorityServer(engine, socket_path=auth_socket_dir / "rpc", worker_uid=WORKER,
                            tenant_id="tenant-a", role_policy=policy).serve(max_sessions=2)

        def wrong_supervisor_peer():
            with connect(settings["socket_path"]) as conn:
                assert receive(conn, MAX_REQUEST) == {"ok": False, "code": "supervisor_rejected"}

        def wrong_authority_peer():
            with pytest.raises(AuthorityDispatchError):
                AuthorityClient(auth_socket_dir / "rpc", authority_uid=AUTHORITY,
                                tenant_id="tenant-a", wait_seconds=15).run_once()

        def dispatch():
            for secret in (key, sup_home / "db.pgpass", authority_home / "db.pgpass"):
                denied(secret)
            with pytest.raises(PermissionError):
                with connect(settings["socket_path"]):
                    pass
            # Exec replaces the fork's controller memory; only endpoint/scope arguments remain.
            completed = subprocess.run([sys.executable, "-B", "-m", "app.cli_dispatch",
                "--socket", str(auth_socket_dir / "rpc"), "--authority-uid", str(AUTHORITY),
                "--tenant", "tenant-a", "--wait-seconds", "15"], cwd=application,
                env={"HOME": str(worker_home), "PATH": "/usr/bin:/bin", "LANG": "C.UTF-8"},
                capture_output=True, timeout=20)
            if completed.returncode != 0 or completed.stderr:
                raise ProbeFailure("dispatcher_process_failed")
            reply = json.loads(completed.stdout)
            assert set(reply) == {"version", "ok", "tenant_id", "result"}
            assert reply["version"] == 1 and reply["ok"] is True and reply["tenant_id"] == "tenant-a"
            result = reply["result"]
            if result is None or result["job_id"] != str(job["job_id"]):
                raise ProbeFailure("dispatch_result_scope")
            if result["state"] != ("succeeded" if proceed else "hold"):
                raise ProbeFailure("dispatch_state_" + result["state"] + "_" + result["reason_code"])
            if result["capture_id"] is None or result["decision_id"] is None:
                raise ProbeFailure("dispatch_unrecorded_" + result["reason_code"])
            evidence = store.artifact_root / ".evidence" / sha256(b"tenant-a").hexdigest()
            denied(evidence)

        with child(SUPERVISOR, SUPERVISOR_GROUP, [CONTENT_GROUP], supervisor, home=sup_home) as sup:
            listening(settings["socket_path"], sup)
            with child(WORKER, DISPATCH_GROUP, [SUPERVISOR_GROUP], wrong_supervisor_peer, home=worker_home) as wrong:
                finished(wrong)
            with child(AUTHORITY, DISPATCH_GROUP, [CONTENT_GROUP, SUPERVISOR_GROUP], authority,
                       home=authority_home) as auth:
                listening(auth_socket_dir / "rpc", auth)
                with child(ROGUE, DISPATCH_GROUP, [], wrong_authority_peer, home=rogue_home) as wrong:
                    finished(wrong)
                with child(WORKER, DISPATCH_GROUP, [], dispatch, home=worker_home) as worker:
                    finished(worker)
                finished(auth)
            finished(sup, executed=True)
        identity = json.loads(marker.read_text())
        assert identity == {"uid": [SUPERVISOR] * 3, "gid": [SUPERVISOR_GROUP] * 3, "groups": [CONTENT_GROUP]}
        record = ExecutionAttestationStore(store, {"test-supervisor-v1": public}).get("tenant-a", job["job_id"], 1)
        assert record is not None and record.capture_id is not None and record.usage == {"input_tokens": 1, "output_tokens": 1}
        assert not Path(f"/proc/{record.process_id}").exists()
        assert state(store, "tenant-b", foreign) == "queued"
        assert store.get_job("tenant-a", job["job_id"])["state"] == ("succeeded" if proceed else "hold")
        decisions = store.list_decisions("tenant-a", job["job_id"])
        assert len(decisions) == 1 and decisions[0]["output_sha256"] == record.final_output_sha256
        if proceed:
            assert store.get_publication("tenant-a", job["job_id"])["decision_id"] == decisions[0]["decision_id"]
        else:
            assert store.get_hold_report("tenant-a", job["job_id"]) is not None
        assert not settings["socket_path"].exists() and not (auth_socket_dir / "rpc").exists()
        print(f"Distinct UID service smoke passed: {stage}; separate SCRAM users, peer UIDs, "
              "fresh supervisor and dispatcher exec, signed persistence and private-file denials. "
              "Fake CLI/test key; no G1/G4 acceptance.")
