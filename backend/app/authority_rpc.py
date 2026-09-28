"""Scoped synthetic authority dispatcher. Production isolation remains closed."""

from dataclasses import asdict
from pathlib import Path
import os
import re
import select
import signal
import socket
import time
from uuid import UUID

from .cli_ipc import MAX_REQUEST, receive, request, require_peer, send
from .cli_worker import CliWorker, WorkResult
from .runtime_roles import RuntimeRolePolicy, RuntimeLoginPolicy, RolePolicyHold, audit_runtime_roles


STATES = frozenset({"succeeded", "hold", "failed", "canceled", "queued", "unclosed"})
CODE = re.compile(r"[a-z][a-z0-9_]{0,79}\Z")
RESULT_FIELDS = frozenset(WorkResult.__dataclass_fields__)


def _uuid(value, *, nullable=False):
    if nullable and value is None:
        return None
    if type(value) is not str or str(UUID(value)) != value:
        raise ValueError("canonical authority result UUID required")
    return UUID(value)


def _result(value):
    if value is None:
        return None
    if (type(value) is not dict or set(value) != RESULT_FIELDS or
            type(value["attempt"]) is not int or not 1 <= value["attempt"] <= 2147483647 or
            type(value["state"]) is not str or value["state"] not in STATES or
            type(value["reason_code"]) is not str or not CODE.fullmatch(value["reason_code"])):
        raise ValueError("invalid authority result")
    return WorkResult(_uuid(value["job_id"]), value["attempt"], value["state"],
        value["reason_code"], _uuid(value["capture_id"], nullable=True),
        _uuid(value["decision_id"], nullable=True))


class AuthorityDispatchError(ValueError):
    """No automatic retry: an accepted job may have completed without a reply."""


class AuthorityClient:
    """General worker holds only a socket endpoint, expected UID and tenant."""

    def __init__(self, socket_path, *, authority_uid, tenant_id, wait_seconds=660):
        self.socket_path = Path(socket_path)
        if (not self.socket_path.is_absolute() or type(authority_uid) is not int or
                authority_uid < 0 or type(tenant_id) is not str or not 1 <= len(tenant_id) <= 200 or
                type(wait_seconds) is not int or not 1 <= wait_seconds <= 660):
            raise ValueError("fixed authority peer, tenant and bounded wait required")
        self.authority_uid, self.tenant_id = authority_uid, tenant_id
        self.wait_seconds = wait_seconds

    def run_once(self):
        with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as conn:
            try:
                conn.settimeout(5)
                conn.connect(str(self.socket_path))
                require_peer(conn, self.authority_uid)
                send(conn, {"version": 1, "op": "run_next"}, MAX_REQUEST)
                deadline = time.monotonic() + self.wait_seconds
                # Wait for the first byte separately; a frame still has a five-second bound.
                while True:
                    remaining = deadline - time.monotonic()
                    if remaining <= 0:
                        raise TimeoutError("authority dispatch wait exceeded")
                    if select.select([conn], [], [], remaining)[0]:
                        break
                reply = receive(conn, MAX_REQUEST, deadline=deadline)
                if (set(reply) != {"version", "ok", "tenant_id", "result"} or
                        type(reply["version"]) is not int or reply["version"] != 1 or
                        reply["ok"] is not True or reply["tenant_id"] != self.tenant_id):
                    raise ValueError("authority scope or reply differs")
                return _result(reply["result"])
            except Exception:
                raise AuthorityDispatchError("authority dispatch unresolved; do not automatically retry") from None


class AuthorityServer:
    """Own the existing validated pipeline; accept no caller-supplied job data."""

    def __init__(self, engine, *, socket_path, worker_uid, tenant_id, role_policy):
        self.socket_path = Path(socket_path)
        parent = self.socket_path.parent
        if (not isinstance(engine, CliWorker) or engine.supervisor_client is None or
                engine.attestation_store is None or
                not isinstance(role_policy, RuntimeRolePolicy) or
                role_policy.schema != engine.store.schema or
                type(tenant_id) is not str or not 1 <= len(tenant_id) <= 200 or
                engine.supervisor_client.tenant_id != tenant_id or
                type(worker_uid) is not int or worker_uid < 0 or
                not self.socket_path.is_absolute() or not parent.is_dir() or
                parent.is_symlink() or parent.stat().st_uid != os.getuid() or
                parent.stat().st_mode & 0o022):
            raise ValueError("protected authority endpoint and fixed supervised scope required")
        self.engine, self.role_policy = engine, role_policy
        self.worker_uid, self.tenant_id = worker_uid, tenant_id

    def _audit(self):
        with self.engine.store.connect() as conn:
            if isinstance(self.role_policy, RuntimeLoginPolicy):
                from .runtime_login import verify_runtime_identity
                verify_runtime_identity(conn, self.role_policy, "authority")
            if conn.execute("SELECT current_user AS name").fetchone()["name"] != self.role_policy.roles["authority"]:
                raise RolePolicyHold("authority_database_identity_required")
            audit_runtime_roles(conn, self.role_policy)

    def serve(self, *, max_sessions=None):
        if max_sessions is not None and (type(max_sessions) is not int or max_sessions < 1):
            raise ValueError("invalid authority session bound")
        self._audit()

        def terminate(_signal, _frame):
            raise SystemExit(0)

        previous = signal.signal(signal.SIGTERM, terminate)
        try:
            with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as listener:
                listener.bind(str(self.socket_path))
                identity = self.socket_path.stat().st_ino
                self.socket_path.chmod(0o660)
                try:
                    listener.listen(1)
                    count = 0
                    while max_sessions is None or count < max_sessions:
                        conn, _ = listener.accept()
                        with conn:
                            self._session(conn)
                        count += 1
                finally:
                    if self.socket_path.exists() and self.socket_path.stat().st_ino == identity:
                        self.socket_path.unlink()
        finally:
            signal.signal(signal.SIGTERM, previous)

    def _session(self, conn):
        try:
            require_peer(conn, self.worker_uid)
            request(receive(conn, MAX_REQUEST), "run_next")
            self._audit()
            # A lost dispatcher connection does not cancel an accepted durable job.
            result = self.engine.run_once()
            wire = None
            if result is not None:
                wire = {key: str(value) if isinstance(value, UUID) else value
                        for key, value in asdict(result).items()}
                _result(wire)
            send(conn, {"version": 1, "ok": True, "tenant_id": self.tenant_id,
                        "result": wire}, MAX_REQUEST)
        except Exception:
            try:
                send(conn, {"version": 1, "ok": False, "code": "authority_rejected"}, MAX_REQUEST)
            except Exception:
                pass
