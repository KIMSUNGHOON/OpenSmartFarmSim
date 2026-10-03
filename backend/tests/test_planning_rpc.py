"""Real local planning RPC with test keys/shared OS UID, not deployment custody."""

from contextlib import contextmanager
from datetime import datetime, timezone
from hashlib import sha256
import json
import multiprocessing
import os
from pathlib import Path
import socket
import struct
import sys
import tempfile
import threading
import time

from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from cryptography.hazmat.primitives.serialization import Encoding, PrivateFormat, PublicFormat, NoEncryption
from psycopg import sql
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from app.cli_ipc import MAX_REQUEST, receive, send
from app.planning_events import PlanningAuthority, PlanningEventStore, DecisionContextVerifier
from app.planning_rpc import PlanningClient, PlanningServer, PlanningRpcError, MAX_REPLY
from app.thermal_publisher import collection_review_input
from test_planning_roles import scope, login_database
from test_thermal_run_store import run_store, raw_inputs
from test_jobs import pg_store


def _serve(dsn, policy, key_raw, snapshot, path, caller_uid, max_sessions, lose_reply):
    store = PlanningEventStore(dsn, policy.schema, runtime_identity=(policy, "authority"),
        principal_provider=lambda: {"authenticated": True, "tenant_id": "tenant-a",
                                    "scopes": ("planning_event_issue",)})
    authority = PlanningAuthority(store, "test-planning-v1", Ed25519PrivateKey.from_private_bytes(key_raw))
    if lose_reply:
        import app.planning_rpc as rpc
        original = rpc.send
        def drop_success(conn, value, limit):
            if value.get("ok") is True:
                conn.shutdown(socket.SHUT_RDWR)
                raise ConnectionError("injected loss after commit")
            original(conn, value, limit)
        rpc.send = drop_success
    PlanningServer(authority, lambda tenant, sid: snapshot if sid == snapshot["snapshot_id"] else None,
        socket_path=path, caller_uid=caller_uid, tenant_id="tenant-a").serve(max_sessions=max_sessions)


@contextmanager
def running(scope, snapshot, *, caller_uid=None, max_sessions=1, lose_reply=False):
    _admin, policy, stores, dsns = scope
    key = Ed25519PrivateKey.generate()
    public = key.public_key().public_bytes(Encoding.Raw, PublicFormat.Raw)
    verifier = DecisionContextVerifier({"test-planning-v1": public}, stores["supervisor"].read_event)
    with tempfile.TemporaryDirectory(prefix="ossf-plan-rpc-") as directory:
        path = Path(directory) / "planning.sock"
        process = multiprocessing.get_context("spawn").Process(target=_serve,
            args=(dsns["authority"], policy,
                  key.private_bytes(Encoding.Raw, PrivateFormat.Raw, NoEncryption()), snapshot, path,
                  os.getuid() if caller_uid is None else caller_uid, max_sessions, lose_reply))
        process.start()
        try:
            deadline = time.monotonic() + 8
            while not path.exists() and time.monotonic() < deadline:
                assert process.is_alive(), "planning service failed before listening"
                time.sleep(0.02)
            assert path.exists()
            client = PlanningClient(path, planning_uid=os.getuid(), tenant_id="tenant-a", verifier=verifier)
            yield client, process, path
        finally:
            process.join(timeout=1)
            if process.is_alive():
                process.terminate()
                process.join(timeout=5)
            if process.is_alive():
                process.kill()
                process.join(timeout=5)
            assert not process.is_alive(), "planning child not reaped"


def row_count(scope):
    admin, policy, *_ = scope
    with admin.connect() as conn:
        return conn.execute(sql.SQL("SELECT count(*) AS n FROM {}.planning_events").format(
            sql.Identifier(policy.schema))).fetchone()["n"]


def test_remote_planning_context_binds_snapshot_and_durable_collection_job(scope, run_store, pg_store):
    snapshot_id = run_store.put_snapshot("tenant-a", *raw_inputs())
    snapshot = run_store.get_snapshot("tenant-a", snapshot_id)
    with running(scope, snapshot) as (client, process, path):
        assert process.pid != os.getpid()
        raw, signature = client.issue(snapshot_id, claim_mode="ex_post_replay", decision_time_kind="actual")
        run_store._context_verifier = client.verifier
        context_id = run_store.put_decision_context("tenant-a", raw, signature)
        context = run_store.get_decision_context("tenant-a", snapshot_id, context_id)
        value = collection_review_input(snapshot, context)
        job = pg_store.submit("tenant-a", "collection_review", value, "planning-review-intent-a")
        assert pg_store.submit("tenant-a", "collection_review", value, "planning-review-intent-a") == job
        assert job["state"] == "queued" and value["context_sha256"] == sha256(raw).hexdigest()
        process.join(timeout=5)
        assert process.exitcode == 0 and not path.exists()
    assert row_count(scope) == 1


def test_hypothetical_request_retains_explicit_historical_time(scope):
    snapshot = {"tenant_id": "tenant-a", "snapshot_id": "snapshot-a"}
    with running(scope, snapshot) as (client, process, _path):
        raw, _ = client.issue("snapshot-a", claim_mode="ex_ante", decision_time_kind="hypothetical",
            hypothetical_at=datetime(2000, 1, 1, tzinfo=timezone.utc))
        assert json.loads(raw)["decision_at_utc"] == "2000-01-01T00:00:00.000000Z"
        process.join(timeout=5)
        assert process.exitcode == 0


@pytest.mark.parametrize("fault", ["unknown_snapshot", "caller_uid", "service_uid", "foreign_snapshot"])
def test_scope_or_peer_rejection_does_not_issue_an_event(scope, fault):
    snapshot = {"tenant_id": "tenant-b" if fault == "foreign_snapshot" else "tenant-a", "snapshot_id": "snapshot-a"}
    with running(scope, snapshot, caller_uid=os.getuid()+1 if fault == "caller_uid" else None) as (client, process, _):
        if fault == "service_uid": client.planning_uid += 1
        with pytest.raises(PlanningRpcError, match="^planning_issue_unresolved$"):
            client.issue("missing" if fault == "unknown_snapshot" else "snapshot-a",
                         claim_mode="ex_post_replay", decision_time_kind="actual")
        process.join(timeout=5)
        assert process.exitcode == 0
    assert row_count(scope) == 0


@pytest.mark.parametrize("fault", ["extra", "tenant", "actual_time", "mode", "kind", "naive_time",
                                  "missing", "boolean_version", "oversize", "duplicate"])
def test_invalid_wire_requests_return_only_fixed_error_and_no_event(scope, fault):
    snapshot = {"tenant_id": "tenant-a", "snapshot_id": "snapshot-a"}
    value = dict(version=1, op="issue", snapshot_id="snapshot-a", claim_mode="ex_post_replay",
                 decision_time_kind="actual", hypothetical_at_utc=None)
    if fault == "extra": value["authority_id"] = "untrusted"
    elif fault == "tenant": value["tenant_id"] = "tenant-b"
    elif fault == "actual_time": value["hypothetical_at_utc"] = "2000-01-01T00:00:00Z"
    elif fault == "mode": value["claim_mode"] = []
    elif fault == "kind": value["decision_time_kind"] = False
    elif fault == "naive_time": value.update(decision_time_kind="hypothetical", hypothetical_at_utc="2000-01-01")
    elif fault == "missing": del value["snapshot_id"]
    elif fault == "boolean_version": value["version"] = True
    with running(scope, snapshot) as (_client, process, path), socket.socket(socket.AF_UNIX) as conn:
        conn.connect(str(path))
        if fault == "oversize": conn.sendall(struct.pack("!I", MAX_REQUEST+1))
        elif fault == "duplicate":
            raw = json.dumps(value).encode()[:-1] + b',"snapshot_id":"snapshot-b"}'
            conn.sendall(struct.pack("!I", len(raw)) + raw)
        else: send(conn, value, MAX_REQUEST)
        assert receive(conn, MAX_REPLY) == {"version": 1, "ok": False, "code": "planning_issue_rejected"}
        process.join(timeout=5)
        assert process.exitcode == 0
    assert row_count(scope) == 0


def test_lost_success_reply_leaves_one_committed_event_and_never_retries(scope):
    snapshot = {"tenant_id": "tenant-a", "snapshot_id": "snapshot-a"}
    with running(scope, snapshot, lose_reply=True) as (client, process, path):
        with pytest.raises(PlanningRpcError, match="^planning_issue_unresolved$"):
            client.issue("snapshot-a", claim_mode="ex_post_replay", decision_time_kind="actual")
        process.join(timeout=5)
        assert process.exitcode == 0 and not path.exists()
        admin, policy, *_ = scope
        with admin.connect() as conn:
            row = conn.execute(sql.SQL("SELECT * FROM {}.planning_events").format(sql.Identifier(policy.schema))).fetchone()
        assert client.verifier(row["context_raw"], row["context_signature"]) is not None
    assert row_count(scope) == 1


def test_idle_sigterm_removes_only_owned_socket(scope):
    snapshot = {"tenant_id": "tenant-a", "snapshot_id": "snapshot-a"}
    with running(scope, snapshot, max_sessions=None) as (_client, process, path):
        assert path.stat().st_mode & 0o777 == 0o660
        process.terminate()
        process.join(timeout=5)
        assert process.exitcode == 0 and not path.exists()
    assert row_count(scope) == 0


@pytest.mark.parametrize("fault", ["snapshot", "mode", "kind", "hypothetical_time", "signature", "version", "extra"])
def test_client_rejects_swapped_valid_context_or_malformed_reply(scope, fault):
    _admin, _policy, stores, _ = scope
    key = Ed25519PrivateKey.generate()
    authority = PlanningAuthority(stores["authority"], "test-planning-v1", key)
    public = key.public_key().public_bytes(Encoding.Raw, PublicFormat.Raw)
    verifier = DecisionContextVerifier({"test-planning-v1": public}, stores["supervisor"].read_event)
    kind = "hypothetical" if fault in ("kind", "hypothetical_time") else "actual"
    raw, signature = authority.issue("tenant-a", "snapshot-b" if fault == "snapshot" else "snapshot-a",
        claim_mode="ex_ante" if fault == "mode" else "ex_post_replay", decision_time_kind=kind,
        hypothetical_at=datetime(2001, 1, 1, tzinfo=timezone.utc) if kind == "hypothetical" else None)
    reply = dict(version=True if fault == "version" else 1, ok=True, tenant_id="tenant-a",
                 context_raw=raw.decode(), context_signature="0"*128 if fault == "signature" else signature)
    if fault == "extra": reply["secret"] = "untrusted-fixture"
    with tempfile.TemporaryDirectory(prefix="ossf-plan-reply-") as directory:
        path = Path(directory) / "peer.sock"
        with socket.socket(socket.AF_UNIX) as listener:
            listener.bind(str(path))
            listener.listen(1)
            def peer():
                conn, _ = listener.accept()
                with conn:
                    receive(conn, MAX_REQUEST)
                    send(conn, reply, MAX_REPLY)
            thread = threading.Thread(target=peer, daemon=True)
            thread.start()
            client = PlanningClient(path, planning_uid=os.getuid(), tenant_id="tenant-a", verifier=verifier)
            with pytest.raises(PlanningRpcError, match="^planning_issue_unresolved$"):
                client.issue("snapshot-a", claim_mode="ex_post_replay",
                    decision_time_kind="hypothetical" if fault == "hypothetical_time" else "actual",
                    hypothetical_at=datetime(2000, 1, 1, tzinfo=timezone.utc) if fault == "hypothetical_time" else None)
            thread.join(timeout=5)
            assert not thread.is_alive()


def test_owner_smoke_authority_and_existing_socket_are_rejected_without_replacement(scope, tmp_path):
    admin, _policy, stores, _ = scope
    key = Ed25519PrivateKey.generate()
    owner = PlanningAuthority(admin, "test-planning-v1", key, synthetic_smoke=True)
    with pytest.raises(ValueError, match="protected planning endpoint"):
        PlanningServer(owner, lambda *_: None, socket_path=tmp_path / "peer.sock", caller_uid=os.getuid(), tenant_id="tenant-a")
    authority = PlanningAuthority(stores["authority"], "test-planning-v1", key)
    path = tmp_path / "occupied.sock"
    path.write_bytes(b"existing operator file")
    server = PlanningServer(authority, lambda *_: None, socket_path=path, caller_uid=os.getuid(), tenant_id="tenant-a")
    with pytest.raises(OSError): server.serve(max_sessions=1)
    assert path.read_bytes() == b"existing operator file"


def test_client_rejects_owner_backed_smoke_verifier(scope, tmp_path):
    admin, *_ = scope
    key = Ed25519PrivateKey.generate()
    public = key.public_key().public_bytes(Encoding.Raw, PublicFormat.Raw)
    verifier = DecisionContextVerifier({"test-planning-v1": public}, admin.read_event, synthetic_smoke=True)
    with pytest.raises(ValueError, match="fixed planning peer"):
        PlanningClient(tmp_path / "peer.sock", planning_uid=os.getuid(), tenant_id="tenant-a", verifier=verifier)


def test_serving_process_rejects_writer_grant_drift_before_issuance(scope):
    admin, policy, *_ = scope
    snapshot = {"tenant_id": "tenant-a", "snapshot_id": "snapshot-a"}
    with running(scope, snapshot) as (client, process, _path):
        with admin.connect() as conn:
            conn.execute(sql.SQL("GRANT INSERT(recorded_at) ON TABLE {}.planning_events TO {}").format(
                sql.Identifier(policy.schema), sql.Identifier(policy.roles["authority"])))
        with pytest.raises(PlanningRpcError, match="^planning_issue_unresolved$"):
            client.issue("snapshot-a", claim_mode="ex_post_replay", decision_time_kind="actual")
        process.join(timeout=5)
        assert process.exitcode == 0
    assert row_count(scope) == 0
