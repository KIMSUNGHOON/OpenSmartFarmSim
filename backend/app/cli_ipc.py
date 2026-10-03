"""Bounded, strict JSON frames for the local Linux supervisor connection."""

import json
import socket
import struct
import time


MAX_REQUEST = 4096
MAX_RESPONSE = 16 * 1024 * 1024
IO_SECONDS = 5


def _pairs(items):
    result = {}
    for key, value in items:
        if key in result:
            raise ValueError("duplicate IPC JSON key")
        result[key] = value
    return result


def receive(conn, limit, *, deadline=None):
    deadline = min(deadline or float("inf"), time.monotonic() + IO_SECONDS)

    def read(size):
        parts = bytearray()
        while len(parts) < size:
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                raise TimeoutError("IPC frame deadline exceeded")
            conn.settimeout(remaining)
            data = conn.recv(min(size - len(parts), 65536))
            if not data:
                raise EOFError("IPC connection closed")
            parts.extend(data)
        return bytes(parts)

    size = struct.unpack("!I", read(4))[0]
    if not 1 <= size <= limit:
        raise ValueError("IPC frame exceeds bound")
    value = json.loads(read(size).decode("utf-8"), object_pairs_hook=_pairs,
                       parse_constant=lambda _: (_ for _ in ()).throw(ValueError()))
    if type(value) is not dict:
        raise ValueError("IPC object required")
    return value


def send(conn, value, limit):
    raw = json.dumps(value, sort_keys=True, separators=(",", ":"),
                     ensure_ascii=False, allow_nan=False).encode("utf-8")
    if not 1 <= len(raw) <= limit:
        raise ValueError("IPC frame exceeds bound")
    conn.settimeout(IO_SECONDS)
    conn.sendall(struct.pack("!I", len(raw)) + raw)


def require_peer(conn, expected_uid):
    if type(expected_uid) is not int or expected_uid < 0:
        raise ValueError("configured IPC peer UID required")
    _, uid, _ = struct.unpack("3i", conn.getsockopt(
        socket.SOL_SOCKET, socket.SO_PEERCRED, struct.calcsize("3i")))
    if uid != expected_uid:
        raise ValueError("unapproved IPC peer")


def request(value, op, fields=()):
    if (set(value) != {"version", "op", *fields} or
            type(value["version"]) is not int or value["version"] != 1 or
            value["op"] != op):
        raise ValueError("unsupported IPC request")

