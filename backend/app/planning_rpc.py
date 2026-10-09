"""Bounded local planning issuance; callers hold no signing key or writer login."""

from datetime import datetime, timezone
import os
from pathlib import Path
import signal
import socket

from .cli_ipc import MAX_REQUEST, receive, request, require_peer, send
from .planning_events import PlanningAuthority, PlanningEventStore, DecisionContextVerifier
from .thermal_run_store import _context, _time


MAX_REPLY = 65536
FIELDS = ("snapshot_id", "claim_mode", "decision_time_kind", "hypothetical_at_utc")


class PlanningRpcError(ValueError):
    """An event may have committed; do not automatically retry issuance."""


def _id(value):
    return type(value) is str and 1 <= len(value) <= 200 and all(
        ord(char) >= 32 and ord(char) != 127 for char in value)


def _input(value):
    request(value, "issue", FIELDS)
    if (not _id(value["snapshot_id"]) or type(value["claim_mode"]) is not str or
            value["claim_mode"] not in ("ex_ante", "ex_post_replay") or
            type(value["decision_time_kind"]) is not str or
            value["decision_time_kind"] not in ("actual", "hypothetical")):
        raise ValueError("planning request rejected")
    hypothetical = value["hypothetical_at_utc"]
    if value["decision_time_kind"] == "actual":
        if hypothetical is not None:
            raise ValueError("actual timestamp cannot be assigned")
        return None
    return _time(hypothetical)


class PlanningClient:
    def __init__(self, socket_path, *, planning_uid, tenant_id, verifier):
        self.socket_path = Path(socket_path)
        reader = getattr(getattr(verifier, "event_reader", None), "__self__", None)
        if (not self.socket_path.is_absolute() or type(planning_uid) is not int or
                planning_uid < 0 or not _id(tenant_id) or type(verifier) is not DecisionContextVerifier or
                type(reader) is not PlanningEventStore or reader.runtime_identity is None or
                reader.runtime_identity[1] != "supervisor" or
                getattr(verifier.event_reader, "__func__", None) is not PlanningEventStore.read_event):
            raise ValueError("fixed planning peer, tenant and public verifier required")
        self.planning_uid, self.tenant_id, self.verifier = planning_uid, tenant_id, verifier

    def issue(self, snapshot_id, *, claim_mode, decision_time_kind, hypothetical_at=None):
        try:
            hypothetical = None
            if hypothetical_at is not None:
                if not isinstance(hypothetical_at, datetime) or hypothetical_at.utcoffset() is None:
                    raise ValueError("aware hypothetical instant required")
                hypothetical = hypothetical_at.astimezone(timezone.utc).isoformat(
                    timespec="microseconds").replace("+00:00", "Z")
            value = dict(version=1, op="issue", snapshot_id=snapshot_id, claim_mode=claim_mode,
                         decision_time_kind=decision_time_kind, hypothetical_at_utc=hypothetical)
            expected_time = _input(value)
            with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as conn:
                conn.settimeout(5)
                conn.connect(str(self.socket_path))
                require_peer(conn, self.planning_uid)
                send(conn, value, MAX_REQUEST)
                reply = receive(conn, MAX_REPLY)
            if (set(reply) != {"version", "ok", "tenant_id", "context_raw", "context_signature"} or
                    type(reply["version"]) is not int or reply["version"] != 1 or reply["ok"] is not True or
                    reply["tenant_id"] != self.tenant_id or type(reply["context_raw"]) is not str):
                raise ValueError("planning reply rejected")
            raw, signature = reply["context_raw"].encode("utf-8"), reply["context_signature"]
            context = _context(raw, signature, self.verifier)
            if (context["tenant_id"] != self.tenant_id or context["snapshot_id"] != snapshot_id or
                    context["claim_mode"] != claim_mode or context["decision_time_kind"] != decision_time_kind or
                    (expected_time is not None and _time(context["decision_at_utc"]) != expected_time)):
                raise ValueError("planning reply scope differs")
            return raw, signature
        except Exception:
            raise PlanningRpcError("planning_issue_unresolved") from None


class PlanningServer:
    def __init__(self, authority, snapshot_resolver, *, socket_path, caller_uid, tenant_id):
        self.socket_path = Path(socket_path)
        parent = self.socket_path.parent
        if (type(authority) is not PlanningAuthority or authority.store.runtime_identity is None or
                authority.store.runtime_identity[1] != "authority" or not callable(snapshot_resolver) or
                type(caller_uid) is not int or caller_uid < 0 or not _id(tenant_id) or
                not self.socket_path.is_absolute() or not parent.is_dir() or parent.is_symlink() or
                parent.stat().st_uid != os.getuid() or parent.stat().st_mode & 0o022):
            raise ValueError("protected planning endpoint and writer scope required")
        self.authority, self.snapshot_resolver = authority, snapshot_resolver
        self.caller_uid, self.tenant_id = caller_uid, tenant_id

    def serve(self, *, max_sessions=None):
        if max_sessions is not None and (type(max_sessions) is not int or max_sessions < 1):
            raise ValueError("positive planning session bound required")
        if not self.authority.store._scope(self.tenant_id, "planning_event_issue"):
            raise ValueError("planning tenant issue scope required")
        with self.authority.store.connect():
            pass

        def terminate(_signal, _frame):
            raise SystemExit(0)

        previous = signal.signal(signal.SIGTERM, terminate)
        try:
            with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as listener:
                listener.bind(str(self.socket_path))
                identity = self.socket_path.lstat()
                try:
                    self.socket_path.chmod(0o660)
                    listener.listen(1)
                    count = 0
                    while max_sessions is None or count < max_sessions:
                        conn, _ = listener.accept()
                        with conn:
                            self._session(conn)
                        count += 1
                finally:
                    try:
                        current = self.socket_path.lstat()
                        if (current.st_dev, current.st_ino) == (identity.st_dev, identity.st_ino):
                            self.socket_path.unlink()
                    except FileNotFoundError:
                        pass
        finally:
            signal.signal(signal.SIGTERM, previous)

    def _session(self, conn):
        try:
            require_peer(conn, self.caller_uid)
            value = receive(conn, MAX_REQUEST)
            hypothetical = _input(value)
            snapshot = self.snapshot_resolver(self.tenant_id, value["snapshot_id"])
            if (type(snapshot) is not dict or snapshot.get("tenant_id") != self.tenant_id or
                    snapshot.get("snapshot_id") != value["snapshot_id"]):
                raise ValueError("matching snapshot required")
            raw, signature = self.authority.issue(self.tenant_id, value["snapshot_id"],
                claim_mode=value["claim_mode"], decision_time_kind=value["decision_time_kind"],
                hypothetical_at=hypothetical)
            send(conn, dict(version=1, ok=True, tenant_id=self.tenant_id,
                context_raw=raw.decode("utf-8"), context_signature=signature), MAX_REPLY)
        except Exception:
            try:
                send(conn, dict(version=1, ok=False, code="planning_issue_rejected"), MAX_REPLY)
            except Exception:
                pass
