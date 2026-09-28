"""Worker-side IPC client. It receives observations and has no signing key."""

import base64
from dataclasses import fields
from datetime import datetime, timedelta
from hashlib import sha256
from pathlib import Path
import re
import socket
from uuid import uuid4

from .cli_contracts import SCHEMA_BYTES
from .cli_ipc import MAX_REQUEST, MAX_RESPONSE, receive, require_peer, send
from .cli_supervisor import LaunchObservation, ProcessObservation
from .cli_worker import CliWorker, MAX_FINAL, MAX_JSONL
from .execution_attestation import HEX, USAGE_KEYS


def _time(value):
    if type(value) is not str or not value.endswith("Z"):
        raise ValueError("UTC IPC observation required")
    parsed = datetime.fromisoformat(value)
    if parsed.utcoffset() != timedelta(0):
        raise ValueError("UTC IPC observation required")
    return parsed


def _bytes(value, limit):
    if value is None:
        return None
    if type(value) is not str or len(value) > ((limit + 2) // 3) * 4:
        raise ValueError("bounded IPC output required")
    raw = base64.b64decode(value, validate=True)
    if len(raw) > limit:
        raise ValueError("bounded IPC output required")
    return raw


class SupervisorClient:
    def __init__(self, socket_path, *, supervisor_uid, tenant_id,
                 executable_sha256, environment_sha256):
        self.socket_path = Path(socket_path)
        if (not self.socket_path.is_absolute() or
                type(supervisor_uid) is not int or supervisor_uid < 0 or
                type(tenant_id) is not str or not 1 <= len(tenant_id) <= 200 or
                type(executable_sha256) is not str or not HEX.fullmatch(executable_sha256) or
                type(environment_sha256) is not str or not HEX.fullmatch(environment_sha256)):
            raise ValueError("trusted supervisor peer and scope pins required")
        self.supervisor_uid, self.tenant_id = supervisor_uid, tenant_id
        self.executable_sha256, self.environment_sha256 = executable_sha256, environment_sha256

    def session(self):
        return SupervisorSession(self)


class SupervisorSession:
    def __init__(self, client):
        self.client = client
        self.conn = None
        self.launch = None
        self._version = None
        self._issue_identity = None

    def __enter__(self):
        self.conn = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        try:
            self.conn.settimeout(5)
            self.conn.connect(str(self.client.socket_path))
            require_peer(self.conn, self.client.supervisor_uid)
        except BaseException:
            self.close()
            raise
        return self

    def __exit__(self, _type, _value, _traceback):
        if self.conn is not None:
            try:
                self._call("stop")
            except Exception:
                pass
        self.close()

    def close(self):
        if self.conn is not None:
            self.conn.close()
            self.conn = None

    def _call(self, op, **fields):
        try:
            send(self.conn, {"version": 1, "op": op, **fields}, MAX_REQUEST)
            reply = receive(self.conn, MAX_RESPONSE)
            if set(reply) != {"ok", "data"} or reply["ok"] is not True:
                raise ValueError("supervisor request rejected")
            return reply["data"]
        except BaseException:
            # Partial frames cannot be retried on an unsynchronized stream.
            self.close()
            raise

    def version(self):
        value = self._call("version")
        expected = {"cli_version", "tenant_id", "executable_sha256", "environment_sha256"}
        if (type(value) is not dict or set(value) != expected or
                value["tenant_id"] != self.client.tenant_id or
                value["executable_sha256"] != self.client.executable_sha256 or
                value["environment_sha256"] != self.client.environment_sha256 or
                type(value["cli_version"]) is not str or
                not re.fullmatch(r"codex-cli [0-9]+\.[0-9]+\.[0-9]+", value["cli_version"])):
            raise ValueError("supervisor metadata differs from pinned identity")
        self._version = value["cli_version"]
        return self._version

    def start(self, job_id, attempt):
        value = self._call("start", job_id=str(job_id), attempt=attempt)
        if type(value) is not dict or set(value) != {field.name for field in fields(LaunchObservation)}:
            raise ValueError("invalid supervisor launch response")
        argv = value["argv"]
        if (type(argv) is not list or len(argv) != 21 or
                any(type(arg) is not str or not arg or len(arg) > 1000 for arg in argv) or
                any(not Path(argv[index]).is_absolute() for index in (0, 15, 17, 19)) or
                argv != CliWorker._argv(argv[0], argv[19], argv[15], argv[17]) or
                value["cli_version"] != self._version or
                value["executable_sha256"] != self.client.executable_sha256 or
                value["schema_sha256"] != sha256(SCHEMA_BYTES).hexdigest() or
                type(value["prompt_sha256"]) is not str or not HEX.fullmatch(value["prompt_sha256"]) or
                type(value["process_id"]) is not int or value["process_id"] <= 0 or
                type(value["process_start_token"]) is not str or
                not value["process_start_token"].isdecimal()):
            raise ValueError("supervisor launch differs from pinned contract")
        value["argv"] = tuple(argv)
        value["started_at_utc"] = _time(value["started_at_utc"])
        self.launch = LaunchObservation(**value)
        return self.launch

    def poll(self):
        value = self._call("poll")
        if value is None:
            return None
        if type(value) is not dict or set(value) != {field.name for field in fields(ProcessObservation)}:
            raise ValueError("invalid supervisor output response")
        for name, limit in (("jsonl", MAX_JSONL), ("final_output", MAX_FINAL)):
            value[name] = _bytes(value[name], limit)
            digest = sha256(value[name]).hexdigest() if value[name] else None
            if value[name + "_sha256"] != digest:
                raise ValueError("supervisor output digest differs")
        for name in ("started_at_utc", "ended_at_utc"):
            value[name] = _time(value[name])
        usage = value["usage"]
        if (self.launch is None or value["started_at_utc"] != self.launch.started_at_utc or
                value["ended_at_utc"] < value["started_at_utc"] or
                (value["exit_code"] is not None and (type(value["exit_code"]) is not int or
                                                     not 0 <= value["exit_code"] <= 255)) or
                value["termination_reason"] not in {"completed", "cli_timeout", "capture_overflow",
                    "cli_error", "final_missing", "invalid_cli_output"} or
                (usage is not None and (type(usage) is not dict or
                    not {"input_tokens", "output_tokens"} <= set(usage) or not set(usage) <= USAGE_KEYS or
                    any(type(count) is not int or count < 0 for count in usage.values())))):
            raise ValueError("invalid supervisor completion")
        return ProcessObservation(**value)

    def issue(self, capture_id, decision_id):
        if self._issue_identity is None:
            self._issue_identity = (capture_id, decision_id, uuid4())
        if self._issue_identity[:2] != (capture_id, decision_id):
            raise ValueError("issuance identity is immutable")
        value = self._call("issue", capture_id=str(capture_id), decision_id=str(decision_id),
                           request_id=str(self._issue_identity[2]))
        if type(value) is not dict or set(value) != {"raw", "signature"}:
            raise ValueError("invalid supervisor attestation response")
        raw, signature = _bytes(value["raw"], 16384), _bytes(value["signature"], 64)
        if raw is None or not raw or signature is None or len(signature) != 64:
            raise ValueError("invalid supervisor attestation bytes")
        return raw, signature
