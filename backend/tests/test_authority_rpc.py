"""Restricted SQL + separate processes with fake CLI/test key; no G1/G4 claim."""

from contextlib import contextmanager
import copy
import multiprocessing
import os
from pathlib import Path
import select
import socket
import sys
import tempfile
import threading
import time
from uuid import uuid4

import psycopg
from psycopg import sql
from psycopg.conninfo import make_conninfo
from psycopg.rows import dict_row
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from app.authority_rpc import AuthorityClient, AuthorityServer, AuthorityDispatchError
from app.cli_contracts import DecisionContract
from app.cli_ipc import MAX_REQUEST, receive, send
from app.cli_supervisor_client import SupervisorClient
from app.cli_supervisor_service import _SupervisorReads
from app.cli_worker import CliWorker
from app.execution_attestation import ExecutionAttestationStore
from app.job_store import JobStore
from app.runtime_roles import RolePolicyHold, RuntimeLoginPolicy
from test_cli_contracts import resolver
from test_cli_supervisor_service import approved, running_server, connect
from test_cli_worker import _worker
from test_job_evidence import cli_store
from test_jobs import pg_store, synthetic_principal
from test_runtime_roles import role_scope, installed
from test_supervised_cli_worker import decision_input


def engine_for(dsn, schema, artifacts, policy, supervisor, public, settings, proceed,
               *, restricted=True):
    contract = DecisionContract(approved if proceed else resolver)
    base = JobStore(dsn, schema, Path(artifacts), principal_provider=synthetic_principal)
    login = isinstance(policy, RuntimeLoginPolicy)
    store = JobStore(dsn, schema, Path(artifacts), decision_validator=contract,
        evidence_policy=cli_store(base).evidence_policy, principal_provider=synthetic_principal,
        runtime_identity=(policy, "authority") if login else None)
    if restricted and not login:
        def authority_connect():
            conn = psycopg.connect(dsn, row_factory=dict_row)
            conn.execute(sql.SQL("SET SESSION AUTHORIZATION {}").format(
                sql.Identifier(policy.roles["authority"])))
            conn.commit()
            return conn
        store.connect = authority_connect
    client = SupervisorClient(supervisor, supervisor_uid=os.getuid(), tenant_id="tenant-a",
        executable_sha256=settings["executable_sha256"],
        environment_sha256=settings["environment_sha256"])
    return CliWorker(store, contract, supervisor_client=client,
        attestation_store=ExecutionAttestationStore(store, {"test-supervisor-v1": public}),
        timeout_seconds=10, lease_seconds=20, synthetic_smoke=True)


def _serve(dsn, schema, artifacts, policy, supervisor, public, settings, proceed,
           path, worker_uid, max_sessions):
    engine = engine_for(dsn, schema, artifacts, policy, supervisor, public, settings, proceed)
    AuthorityServer(engine, socket_path=path, worker_uid=worker_uid, tenant_id="tenant-a",
                    role_policy=policy).serve(max_sessions=max_sessions)


@contextmanager
def running_authority(store, policy, server=None, *, proceed=False, worker_uid=None,
                      max_sessions=1):
    supervisor, public, settings = (server[0], server[1], server[2]) if server else (
        Path("/tmp/unused-supervisor.sock"), b"p" * 32,
        {"executable_sha256": "a" * 64, "environment_sha256": "b" * 64})
    with tempfile.TemporaryDirectory(prefix="ossf-authority-socket-") as directory:
        path = Path(directory) / "authority.sock"
        process = multiprocessing.get_context("spawn").Process(target=_serve,
            args=(store._dsn, store.schema, str(store.artifact_root), policy, supervisor,
                  public, settings, proceed, path,
                  os.getuid() if worker_uid is None else worker_uid, max_sessions))
        process.start()
        try:
            for _ in range(250):
                if path.exists():
                    break
                assert process.is_alive(), "authority failed before listening"
                time.sleep(0.02)
            assert path.exists()
            client = AuthorityClient(path, authority_uid=os.getuid(), tenant_id="tenant-a", wait_seconds=30)
            yield client, process
        finally:
            process.join(timeout=1)
            if process.is_alive():
                process.terminate()
                process.join(timeout=5)
            assert not process.is_alive()


def supervisor_store(store, policy):
    configured = copy.copy(store)
    configured._dsn = make_conninfo(store._dsn, options="-c role=" + policy.roles["supervisor"])
    return configured


def state(store, tenant, job):
    with store.connect() as conn:
        return conn.execute(sql.SQL("SELECT state FROM {} WHERE tenant_id=%s AND job_id=%s").format(
            store._table("jobs")), (tenant, job["job_id"])).fetchone()["state"]


@pytest.mark.parametrize("stage", ["research", "collection_review", "assessment"])
@pytest.mark.parametrize("proceed", [False, True])
def test_dispatcher_uses_restricted_authority_and_supervisor_processes(role_scope, tmp_path, stage, proceed):
    base, policy = role_scope
    store, local = _worker(base, tmp_path, mode="valid_slow", authority=approved if proceed else resolver)
    job = store.submit("tenant-a", stage, decision_input(stage), uuid4().hex)
    foreign = store.submit("tenant-b", stage, decision_input(stage), uuid4().hex)
    installed(role_scope)
    with running_server(supervisor_store(store, policy), local, tmp_path, proceed=proceed) as server:
        with running_authority(store, policy, server, proceed=proceed) as (client, process):
            assert process.pid != os.getpid() and process.pid != server[3].pid
            assert set(client.__dict__) == {"socket_path", "authority_uid", "tenant_id", "wait_seconds"}
            result = client.run_once()
            assert result.job_id == job["job_id"]
            assert result.state == ("succeeded" if proceed else "hold"), result
            assert result.capture_id is not None and result.decision_id is not None
            record = ExecutionAttestationStore(store, {"test-supervisor-v1": server[1]}).get(
                "tenant-a", result.job_id, result.attempt)
            assert record.capture_id == result.capture_id
            assert store.list_decisions("tenant-a", job["job_id"])[0]["decision_id"] == result.decision_id
            assert not Path(f"/proc/{record.process_id}").exists()
    assert state(store, "tenant-b", foreign) == "queued"


def test_empty_dispatch_never_contacts_supervisor(role_scope):
    store, policy = role_scope
    installed(role_scope)
    with running_authority(store, policy) as (client, _):
        assert client.run_once() is None


@pytest.mark.parametrize("field", ["tenant_id", "job_id", "lease_token", "input", "argv", "artifact"])
def test_dispatch_request_rejects_caller_controlled_data_before_claim(role_scope, field):
    store, policy = role_scope
    job = store.submit("tenant-a", "research", decision_input("research"), uuid4().hex)
    installed(role_scope)
    with running_authority(store, policy) as (client, _):
        with connect(client.socket_path) as conn:
            send(conn, {"version": 1, "op": "run_next", field: "untrusted"}, MAX_REQUEST)
            assert receive(conn, MAX_REQUEST) == {"version": 1, "ok": False, "code": "authority_rejected"}
    assert state(store, "tenant-a", job) == "queued"


def test_dispatch_rejects_unapproved_uid(role_scope):
    store, policy = role_scope
    installed(role_scope)
    with running_authority(store, policy, worker_uid=os.getuid() + 1) as (client, _):
        with pytest.raises(AuthorityDispatchError):
            client.run_once()


@pytest.mark.parametrize("partial", [False, True])
def test_stalled_request_has_absolute_deadline_and_does_not_block_next_dispatch(role_scope, partial):
    store, policy = role_scope
    job = store.submit("tenant-a", "research", decision_input("research"), uuid4().hex)
    installed(role_scope)
    with running_authority(store, policy, max_sessions=2) as (client, _):
        with connect(client.socket_path) as conn:
            conn.settimeout(7)
            started = time.monotonic()
            if partial:
                conn.sendall(b"\0\0")
            assert select.select([conn], [], [], 7)[0]
            assert receive(conn, MAX_REQUEST)["ok"] is False
            assert 4 <= time.monotonic() - started < 7
        assert state(store, "tenant-a", job) == "queued"
        assert store.cancel("tenant-a", job["job_id"])
        assert client.run_once() is None


def test_authority_refuses_administrator_identity_and_wrong_tenant(role_scope, tmp_path):
    store, policy = role_scope
    installed(role_scope)
    settings = {"executable_sha256": "a" * 64, "environment_sha256": "b" * 64}
    engine = engine_for(store._dsn, store.schema, store.artifact_root, policy,
                        Path("/tmp/unused.sock"), b"p" * 32, settings, False, restricted=False)
    server = AuthorityServer(engine, socket_path=tmp_path / "authority.sock", worker_uid=os.getuid(),
                             tenant_id="tenant-a", role_policy=policy)
    with pytest.raises(RolePolicyHold, match="authority_database_identity"):
        server.serve(max_sessions=1)
    assert not server.socket_path.exists()
    with pytest.raises(ValueError, match="fixed supervised scope"):
        AuthorityServer(engine, socket_path=server.socket_path, worker_uid=os.getuid(),
                        tenant_id="tenant-b", role_policy=policy)


def test_authority_reaudits_privilege_drift_before_claim(role_scope):
    store, policy = role_scope
    job = store.submit("tenant-a", "research", decision_input("research"), uuid4().hex)
    installed(role_scope)
    with running_authority(store, policy) as (client, _):
        with store.connect() as conn:
            conn.execute(sql.SQL("GRANT SELECT ON {}.jobs TO {}").format(
                sql.Identifier(policy.schema), sql.Identifier(policy.roles["worker"])))
        with pytest.raises(AuthorityDispatchError):
            client.run_once()
    assert state(store, "tenant-a", job) == "queued"


def test_supervisor_preserves_trusted_role_and_forces_read_bounds(role_scope):
    store, policy = role_scope
    installed(role_scope)
    configured = supervisor_store(store, policy)
    configured._dsn = make_conninfo(configured._dsn,
        options="-c role=" + policy.roles["supervisor"] + " -c statement_timeout=0 -c default_transaction_read_only=off")
    with _SupervisorReads(configured).connect() as conn:
        row = conn.execute("SELECT current_user AS name, current_setting('statement_timeout') AS timeout, "
                           "current_setting('transaction_read_only') AS readonly").fetchone()
        assert row == {"name": policy.roles["supervisor"], "timeout": "2s", "readonly": "on"}
        with pytest.raises(psycopg.errors.ReadOnlySqlTransaction):
            conn.execute(sql.SQL("UPDATE {}.jobs SET state='queued' WHERE false").format(sql.Identifier(policy.schema)))


def launch_pid(store, job):
    for _ in range(250):
        with store.connect() as conn:
            row = conn.execute(sql.SQL("SELECT process_id FROM {} WHERE job_id=%s").format(
                store._table("attempt_cli_launches")), (job["job_id"],)).fetchone()
        if row:
            return row["process_id"]
        time.sleep(0.02)
    pytest.fail("authority did not durably record launch")


@pytest.mark.parametrize("action", ["disconnect", "cancel", "terminate"])
def test_accepted_job_lifetime_is_independent_of_dispatch_socket(role_scope, tmp_path, action):
    base, policy = role_scope
    store, local = _worker(base, tmp_path, mode="valid_slow" if action == "disconnect" else "timeout",
                           authority=approved)
    job = store.submit("tenant-a", "research", decision_input("research"), uuid4().hex)
    installed(role_scope)
    with running_server(supervisor_store(store, policy), local, tmp_path, proceed=True) as server:
        with running_authority(store, policy, server, proceed=True) as (client, process):
            conn = connect(client.socket_path)
            send(conn, {"version": 1, "op": "run_next"}, MAX_REQUEST)
            pid = launch_pid(store, job)
            if action == "disconnect":
                conn.close()
                process.join(timeout=5)
                assert state(store, "tenant-a", job) == "succeeded"
            elif action == "cancel":
                assert store.cancel("tenant-a", job["job_id"])
                reply = receive(conn, MAX_REQUEST)
                assert reply["result"]["state"] == "canceled"
                assert store.get_publication("tenant-a", job["job_id"]) is None
            else:
                process.terminate()
                process.join(timeout=5)
                assert store.get_publication("tenant-a", job["job_id"]) is None
            conn.close()
            for _ in range(100):
                if not Path(f"/proc/{pid}").exists():
                    break
                time.sleep(0.02)
            assert not Path(f"/proc/{pid}").exists()


def test_concurrent_dispatchers_claim_one_job_once(role_scope, tmp_path):
    base, policy = role_scope
    store, local = _worker(base, tmp_path, mode="valid_slow", authority=approved)
    job = store.submit("tenant-a", "research", decision_input("research"), uuid4().hex)
    installed(role_scope)
    with running_server(supervisor_store(store, policy), local, tmp_path, proceed=True) as server:
        with running_authority(store, policy, server, proceed=True) as (first, _):
            with running_authority(store, policy, server, proceed=True) as (second, _):
                results = []
                threads = [threading.Thread(target=lambda c=c: results.append(c.run_once()))
                           for c in (first, second)]
                for thread in threads: thread.start()
                for thread in threads: thread.join(timeout=10)
                assert all(not thread.is_alive() for thread in threads)
                assert len(results) == 2 and results.count(None) == 1
                result = next(value for value in results if value is not None)
                assert result.job_id == job["job_id"] and result.attempt == 1 and result.state == "succeeded"
    with store.connect() as conn:
        count = conn.execute(sql.SQL("SELECT count(*) AS n FROM {} WHERE job_id=%s").format(
            store._table("execution_attestations")), (job["job_id"],)).fetchone()["n"]
    assert count == 1


def test_client_waits_for_execution_longer_than_frame_deadline(role_scope, tmp_path):
    base, policy = role_scope
    store, local = _worker(base, tmp_path, mode="valid_slow", authority=approved)
    local.cli_path.write_text(local.cli_path.read_text().replace("time.sleep(1)", "time.sleep(6)"))
    store.submit("tenant-a", "research", decision_input("research"), uuid4().hex)
    installed(role_scope)
    with running_server(supervisor_store(store, policy), local, tmp_path, proceed=True) as server:
        with running_authority(store, policy, server, proceed=True) as (client, _):
            started = time.monotonic()
            result = client.run_once()
            assert result.state == "succeeded" and time.monotonic() - started >= 6


@pytest.mark.parametrize("fault", ["tenant", "version", "attempt", "extra", "state", "uuid", "reason", "lost"])
def test_client_rejects_altered_or_lost_reply_without_retry(tmp_path, fault):
    with tempfile.TemporaryDirectory(prefix="ossf-authority-peer-") as directory:
        path = Path(directory) / "peer.sock"
        with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as listener:
            listener.bind(str(path)); listener.listen(2)
            calls = []
            def peer():
                conn, _ = listener.accept()
                with conn:
                    calls.append(receive(conn, MAX_REQUEST))
                    if fault == "lost":
                        return
                    result = {"job_id": str(uuid4()), "attempt": 1, "state": "hold",
                        "reason_code": "validated_hold", "capture_id": None, "decision_id": None}
                    reply = {"version": 1, "ok": True, "tenant_id": "tenant-a", "result": result}
                    if fault == "tenant": reply["tenant_id"] = "tenant-b"
                    elif fault == "version": reply["version"] = True
                    elif fault == "attempt": result["attempt"] = True
                    elif fault == "extra": result["lease_token"] = "untrusted"
                    elif fault == "state": result["state"] = "approved"
                    elif fault == "uuid": result["job_id"] = "arbitrary"
                    elif fault == "reason": result["reason_code"] = "raw prompt or secret"
                    send(conn, reply, MAX_REQUEST)
            thread = threading.Thread(target=peer)
            thread.start()
            with pytest.raises(AuthorityDispatchError):
                AuthorityClient(path, authority_uid=os.getuid(), tenant_id="tenant-a").run_once()
            thread.join(timeout=2)
            assert not thread.is_alive() and calls == [{"version": 1, "op": "run_next"}]
            listener.settimeout(0.05)
            with pytest.raises(TimeoutError): listener.accept()
