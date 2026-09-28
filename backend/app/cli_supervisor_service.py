"""Foreground Linux IPC supervisor candidate; deployment isolation is separate."""

import base64
from dataclasses import asdict
from datetime import datetime
from hashlib import sha256
import os
from pathlib import Path
import signal
import socket
import stat
import threading
import time
from uuid import UUID

from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
import psycopg
from psycopg import sql
from psycopg.conninfo import conninfo_to_dict
from psycopg.rows import dict_row

from .cli_attestation_issuer import ExecutionAttestationIssuer
from .cli_ipc import MAX_REQUEST, MAX_RESPONSE, receive, request, require_peer, send
from .cli_supervisor import CliProcessSupervisor


def _key(path):
    fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW)
    try:
        info = os.fstat(fd)
        if (not stat.S_ISREG(info.st_mode) or info.st_uid != os.getuid() or
                info.st_mode & 0o077 or info.st_size != 32):
            raise ValueError("private supervisor key file required")
        raw = os.read(fd, 33)
        if len(raw) != 32:
            raise ValueError("private supervisor key changed")
        return Ed25519PrivateKey.from_private_bytes(raw)
    finally:
        os.close(fd)


def _uuid(value):
    if type(value) is not str or str(UUID(value)) != value:
        raise ValueError("canonical IPC UUID required")
    return UUID(value)


def _wire(observation):
    return {key: (base64.b64encode(value).decode("ascii") if type(value) is bytes
                  else value.isoformat().replace("+00:00", "Z")
                  if isinstance(value, datetime) else value)
            for key, value in asdict(observation).items()}


class _SupervisorReads:
    """Bound database waits; this is not a substitute for deployed DB grants."""

    def __init__(self, store):
        if not store._dsn:
            raise ValueError("explicit supervisor database DSN required")
        self._store = store

    def __getattr__(self, name):
        return getattr(self._store, name)

    def connect(self):
        if self._store.runtime_identity is not None:
            from .runtime_login import connect_runtime
            policy, kind = self._store.runtime_identity
            if kind != "supervisor":
                raise ValueError("supervisor database identity required")
            return connect_runtime(self._store._dsn, policy, kind)
        configured = conninfo_to_dict(self._store._dsn).get("options", "")
        return psycopg.connect(self._store._dsn, row_factory=dict_row,
            connect_timeout=3, options=configured + " -c statement_timeout=2000 -c default_transaction_read_only=on")


class SupervisorServer:
    """One configured tenant/worker UID, one active connection, one attempt."""

    def __init__(self, store, *, socket_path, worker_uid, tenant_id, key_file, key_id,
                 cli_path, codex_home, executable_sha256, environment_sha256,
                 child_env=None, timeout_seconds=600):
        self.socket_path = Path(socket_path)
        parent = self.socket_path.parent
        if (not self.socket_path.is_absolute() or not parent.is_dir() or
                parent.is_symlink() or parent.stat().st_uid != os.getuid() or
                parent.stat().st_mode & 0o022 or
                type(worker_uid) is not int or worker_uid < 0 or
                type(tenant_id) is not str or not 1 <= len(tenant_id) <= 200):
            raise ValueError("protected socket directory and fixed worker scope required")
        self.store, self.worker_uid, self.tenant_id = _SupervisorReads(store), worker_uid, tenant_id
        self.private_key, self.key_id = _key(key_file), key_id
        self.cli_path, self.codex_home = Path(cli_path), Path(codex_home)
        self.child_env, self.timeout_seconds = child_env, timeout_seconds
        self.executable_sha256, self.environment_sha256 = executable_sha256, environment_sha256
        if store.runtime_identity is not None:
            from .runtime_roles import audit_runtime_roles
            with self.store.connect() as conn:
                audit_runtime_roles(conn, store.runtime_identity[0])
        # Validate trusted settings before listening or accepting requests.
        self._issuer()

    def _issuer(self):
        observer = CliProcessSupervisor(self.cli_path, self.codex_home,
            child_env=self.child_env, timeout_seconds=self.timeout_seconds)
        return ExecutionAttestationIssuer(self.store, observer, self.private_key,
            self.key_id, executable_sha256=self.executable_sha256,
            environment_sha256=self.environment_sha256)

    def serve(self, *, max_sessions=None):
        if max_sessions is not None and (type(max_sessions) is not int or max_sessions < 1):
            raise ValueError("invalid supervisor session bound")
        def terminate(_signal, _frame):
            raise SystemExit(0)

        previous = signal.signal(signal.SIGTERM, terminate)
        try:
            self._listen(max_sessions)
        finally:
            signal.signal(signal.SIGTERM, previous)

    def _listen(self, max_sessions):
        with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as listener:
            # Never unlink an operator-owned or live socket at startup.
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

    def _session(self, conn):
        issuer = self._issuer()
        observer = issuer.observer
        stop = threading.Event()
        lock = threading.Lock()
        monitor = None
        reservation = None
        invalid = []
        started = False
        version = None
        issue_request = None
        deadline = time.monotonic() + self.timeout_seconds + 30

        def watch():
            next_live_check = 0
            while not stop.wait(0.05):
                try:
                    with lock:
                        now = time.monotonic()
                        if now >= deadline:
                            invalid.append("supervisor_attempt_fenced")
                            observer.close()
                            conn.shutdown(socket.SHUT_RDWR)
                            return
                        observer.poll()
                    if now >= next_live_check:
                        if not issuer.scope_live(allow_closed=True):
                            invalid.append("supervisor_attempt_fenced")
                            conn.shutdown(socket.SHUT_RDWR)
                            return
                        next_live_check = now + 0.5
                except Exception:
                    invalid.append("supervisor_observation_failed")
                    try:
                        conn.shutdown(socket.SHUT_RDWR)
                    except OSError:
                        pass
                    return

        try:
            require_peer(conn, self.worker_uid)
            while True:
                value = receive(conn, MAX_REQUEST, deadline=deadline)
                op = value.get("op")
                with lock:
                    if invalid:
                        raise ValueError("supervisor attempt fenced")
                    if op == "version":
                        request(value, op)
                        if version is not None or started:
                            raise ValueError("version handshake already complete")
                        if sha256(self.cli_path.read_bytes()).hexdigest() != self.executable_sha256:
                            raise ValueError("supervisor executable changed")
                        version = observer._version()
                        data = {"cli_version": version, "tenant_id": self.tenant_id,
                                "executable_sha256": self.executable_sha256,
                                "environment_sha256": self.environment_sha256}
                    elif op == "start":
                        request(value, op, ("job_id", "attempt"))
                        if started or version is None or type(value["attempt"]) is not int or value["attempt"] < 1:
                            raise ValueError("version handshake and valid new attempt required")
                        job_id, attempt = _uuid(value["job_id"]), value["attempt"]
                        reservation = self.store.connect()
                        reservation.autocommit = True
                        identity = f"{self.store.schema}/{self.tenant_id}/{job_id}/{attempt}"
                        lock_id = int.from_bytes(sha256(identity.encode()).digest()[:8], "big", signed=True)
                        reserved = reservation.execute("SELECT pg_try_advisory_lock(%s) AS held", (lock_id,)).fetchone()
                        previous = reservation.execute(sql.SQL("""
                            SELECT 1 FROM {} WHERE tenant_id=%s AND job_id=%s AND attempt=%s
                        """).format(self.store._table("attempt_cli_launches")),
                            (self.tenant_id, job_id, attempt)).fetchone()
                        if not reserved["held"] or previous is not None:
                            raise ValueError("attempt already reserved or launched")
                        launch = issuer.start(self.tenant_id, job_id, attempt)
                        if launch.cli_version != version:
                            raise ValueError("supervisor binary version changed")
                        started = True
                        monitor = threading.Thread(target=watch, daemon=True)
                        monitor.start()
                        data = _wire(launch)
                    elif op == "poll":
                        request(value, op)
                        if not started:
                            raise ValueError("supervisor attempt not started")
                        result = observer.poll()
                        data = _wire(result) if result is not None else None
                    elif op == "issue":
                        request(value, op, ("capture_id", "decision_id", "request_id"))
                        ids = tuple(_uuid(value[name]) for name in
                                    ("capture_id", "decision_id", "request_id"))
                        if not started or (issue_request is not None and ids != issue_request):
                            raise ValueError("issuance request identity changed")
                        raw, signature = issuer.issue(*ids[:2])
                        issue_request = ids
                        data = {"raw": base64.b64encode(raw).decode("ascii"),
                                "signature": base64.b64encode(signature).decode("ascii")}
                    elif op == "stop":
                        request(value, op)
                        stop.set()
                        observer.close()
                        send(conn, {"ok": True, "data": None}, MAX_RESPONSE)
                        return
                    else:
                        raise ValueError("unsupported supervisor operation")
                    send(conn, {"ok": True, "data": data}, MAX_RESPONSE)
        except Exception:
            # Never expose raw output, database details, paths, or key material.
            try:
                send(conn, {"ok": False, "code": "supervisor_rejected"}, MAX_RESPONSE)
            except (OSError, ValueError):
                pass
        finally:
            stop.set()
            if monitor is not None:
                monitor.join(timeout=5)
            with lock:
                observer.close()
            if reservation is not None:
                reservation.close()
