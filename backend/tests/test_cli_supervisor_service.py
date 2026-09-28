"""Separate local process + fake CLI + test key; not deployment isolation."""

from contextlib import contextmanager
from dataclasses import replace
from hashlib import sha256
import multiprocessing
import os
from pathlib import Path
import socket
import sys
import tempfile
import time
from uuid import uuid4

from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from cryptography.hazmat.primitives.serialization import Encoding, PrivateFormat, NoEncryption, PublicFormat
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from app.cli_contracts import DecisionContract, SCHEMA_BYTES
from app.cli_ipc import MAX_REQUEST, MAX_RESPONSE, receive, send
from app.cli_supervisor_service import SupervisorServer
from app.cli_worker import MODEL, EFFORT, PROMPT_VERSION, SCHEMA_VERSION
from app.execution_attestation import install_execution_attestation_schema
from app.job_store import JobStore
from test_cli_contracts import input_for, resolver
from test_cli_worker import _worker
from test_job_evidence import cli_store
from test_jobs import pg_store, synthetic_principal


def approved(job, value):
    original = resolver(job, value)
    return replace(original, allow_proceed=True, missing_evidence=(),
                   g3a_candidate_ids=original.candidate_ids, g3b_ok=True)


def _serve(dsn, schema, artifacts, settings, proceed, max_sessions):
    base = JobStore(dsn, schema, Path(artifacts), principal_provider=synthetic_principal)
    trusted = cli_store(base)
    store = JobStore(dsn, schema, Path(artifacts),
        decision_validator=DecisionContract(approved if proceed else resolver),
        evidence_policy=trusted.evidence_policy, principal_provider=synthetic_principal)
    SupervisorServer(store, **settings).serve(max_sessions=max_sessions)


@contextmanager
def running_server(store, worker, tmp_path, *, proceed=False, worker_uid=None, max_sessions=1):
    private = Ed25519PrivateKey.generate()
    key_file = tmp_path / "supervisor-key"
    key_file.write_bytes(private.private_bytes(Encoding.Raw, PrivateFormat.Raw, NoEncryption()))
    key_file.chmod(0o600)
    public = private.public_key().public_bytes(Encoding.Raw, PublicFormat.Raw)
    with store.connect() as conn:
        exists = conn.execute("SELECT to_regclass(%s) AS existing",
                              (store.schema + ".execution_attestations",)).fetchone()
        if exists["existing"] is None:
            install_execution_attestation_schema(conn, store.schema)
    with tempfile.TemporaryDirectory(prefix="ossf-socket-") as directory:
        path = Path(directory) / "supervisor.sock"
        settings = dict(socket_path=path, worker_uid=os.getuid() if worker_uid is None else worker_uid,
            tenant_id="tenant-a", key_file=key_file, key_id="test-supervisor-v1",
            cli_path=worker.cli_path, codex_home=worker.codex_home,
            executable_sha256=sha256(worker.cli_path.read_bytes()).hexdigest(),
            environment_sha256=sha256(b"test-supervisor-environment").hexdigest(),
            child_env=worker.child_env, timeout_seconds=worker.timeout_seconds)
        process = multiprocessing.get_context("spawn").Process(target=_serve,
            args=(store._dsn, store.schema, str(store.artifact_root), settings, proceed, max_sessions))
        process.start()
        try:
            for _ in range(200):
                if path.exists():
                    break
                assert process.is_alive(), "supervisor failed before listening"
                time.sleep(0.02)
            assert path.exists()
            yield path, public, settings, process
        finally:
            process.join(timeout=5)
            if process.is_alive():
                process.terminate()
                process.join(timeout=5)
            assert not process.is_alive()


def exchange(conn, op, **fields):
    send(conn, {"version": 1, "op": op, **fields}, MAX_REQUEST)
    reply = receive(conn, MAX_RESPONSE)
    assert reply["ok"] is True, reply
    return reply["data"]


def frozen_attempt(store, worker, stage="research"):
    job = store.submit("tenant-a", stage, input_for(stage), uuid4().hex)
    lease = store.claim(30, allowed_stages=(stage,))
    tenant, job_id, attempt, token = (lease["tenant_id"], lease["job_id"], lease["attempt"], lease["lease_token"])
    raw = store.read_input(tenant, job_id, attempt, token)
    value, authority = worker.contract.input_context(dict(lease, input_bytes=raw))
    prompt = store.append_evidence(tenant, job_id, attempt, token, kind="prompt",
        payload=worker._prompt(dict(lease, input_bytes=raw), value, authority), rights_ref="server_cli_prompt")
    schema = store.append_evidence(tenant, job_id, attempt, token, kind="output_schema",
        payload=SCHEMA_BYTES, rights_ref="server_cli_schema")
    assert store.register_invocation(tenant, job_id, attempt, token,
        prompt_evidence_id=prompt["evidence_id"], schema_evidence_id=schema["evidence_id"],
        prompt_version=PROMPT_VERSION, schema_version=SCHEMA_VERSION, execution_kind="codex_cli",
        cli_version=worker._version(), model=MODEL, reasoning_effort=EFFORT)
    return job, lease


def connect(path):
    conn = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    conn.connect(str(path))
    return conn


def test_separate_service_version_and_refusal_of_caller_argv(pg_store, tmp_path):
    store, worker = _worker(pg_store, tmp_path)
    with running_server(store, worker, tmp_path) as (path, _, settings, process):
        assert process.pid != os.getpid()
        with connect(path) as conn:
            metadata = exchange(conn, "version")
            assert metadata["cli_version"] == "codex-cli 0.157.1"
            assert metadata["executable_sha256"] == settings["executable_sha256"]
            send(conn, {"version": 1, "op": "start", "job_id": str(uuid4()),
                        "attempt": 1, "argv": ["arbitrary"]}, MAX_REQUEST)
            assert receive(conn, MAX_RESPONSE) == {"ok": False, "code": "supervisor_rejected"}
    assert not (tmp_path / "actual-prompt.sha256").exists()


def test_service_rejects_unapproved_worker_uid(pg_store, tmp_path):
    store, worker = _worker(pg_store, tmp_path)
    with running_server(store, worker, tmp_path, worker_uid=os.getuid() + 1) as (path, _, _, _):
        with connect(path) as conn:
            assert receive(conn, MAX_RESPONSE)["ok"] is False


@pytest.mark.parametrize("cause", ["disconnect", "cancel", "timeout", "terminate"])
def test_service_stops_its_child_without_trusting_worker_poll(pg_store, tmp_path, cause):
    store, worker = _worker(pg_store, tmp_path, mode="timeout", timeout=1 if cause == "timeout" else 5)
    job, lease = frozen_attempt(store, worker)
    with running_server(store, worker, tmp_path) as (path, _, _, process):
        conn = connect(path)
        exchange(conn, "version")
        launch = exchange(conn, "start", job_id=str(job["job_id"]), attempt=lease["attempt"])
        pid = launch["process_id"]
        if cause == "cancel":
            assert store.cancel("tenant-a", job["job_id"])
        if cause == "disconnect":
            conn.close()
        if cause == "terminate":
            process.terminate()
        for _ in range(200):
            if not Path(f"/proc/{pid}").exists():
                break
            time.sleep(0.02)
        assert not Path(f"/proc/{pid}").exists()
        if cause == "timeout":
            assert exchange(conn, "poll")["termination_reason"] == "cli_timeout"
            exchange(conn, "stop")
        conn.close()
        process.join(timeout=5)
        assert process.exitcode == 0
    assert store.get_publication("tenant-a", job["job_id"]) is None


def test_key_file_must_be_private_and_not_a_symlink(tmp_path):
    from app.cli_supervisor_service import _key
    path = tmp_path / "key"
    path.write_bytes(b"k" * 32)
    path.chmod(0o644)
    with pytest.raises(ValueError):
        _key(path)
    path.chmod(0o600)
    alias = tmp_path / "alias"
    alias.symlink_to(path)
    with pytest.raises(OSError):
        _key(alias)


@pytest.mark.parametrize("pin", ["valid", "tenant", "uid", "binary"])
def test_client_authenticates_the_supervisor_metadata(pg_store, tmp_path, pin):
    from app.cli_supervisor_client import SupervisorClient
    store, worker = _worker(pg_store, tmp_path)
    with running_server(store, worker, tmp_path) as (path, _, settings, _):
        client = SupervisorClient(path, supervisor_uid=os.getuid() + (pin == "uid"),
            tenant_id="tenant-b" if pin == "tenant" else "tenant-a",
            executable_sha256="0" * 64 if pin == "binary" else settings["executable_sha256"],
            environment_sha256=settings["environment_sha256"])
        if pin == "valid":
            with client.session() as session:
                assert session.version() == "codex-cli 0.157.1"
        else:
            with pytest.raises(ValueError):
                with client.session() as session:
                    session.version()


def test_two_services_cannot_launch_the_same_live_attempt(pg_store, tmp_path):
    from app.cli_supervisor_client import SupervisorClient
    store, worker = _worker(pg_store, tmp_path, mode="timeout", timeout=5)
    job, lease = frozen_attempt(store, worker)
    with running_server(store, worker, tmp_path) as first:
        with running_server(store, worker, tmp_path) as second:
            def client(data):
                path, _, settings, _ = data
                return SupervisorClient(path, supervisor_uid=os.getuid(), tenant_id="tenant-a",
                    executable_sha256=settings["executable_sha256"],
                    environment_sha256=settings["environment_sha256"])
            with client(first).session() as a:
                a.version()
                observed = a.start(job["job_id"], lease["attempt"])
                with client(second).session() as b:
                    b.version()
                    with pytest.raises(ValueError, match="rejected"):
                        b.start(job["job_id"], lease["attempt"])
                assert Path(f"/proc/{observed.process_id}").exists()
            assert not Path(f"/proc/{observed.process_id}").exists()
