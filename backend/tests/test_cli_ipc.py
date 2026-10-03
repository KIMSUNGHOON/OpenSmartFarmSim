import os
from pathlib import Path
import socket
import struct
import sys
import time

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from app.cli_ipc import receive, require_peer, request, send


def test_frame_roundtrip_and_peer_credentials():
    a, b = socket.socketpair()
    with a, b:
        send(a, {"version": 1, "op": "start", "label": "온실"}, 4096)
        assert receive(b, 4096)["label"] == "온실"
        require_peer(b, os.getuid())
        with pytest.raises(ValueError, match="peer"):
            require_peer(b, os.getuid() + 1)


@pytest.mark.parametrize("raw", [b'{"op":"poll","op":"stop"}',
                                     b'{"value":NaN}', b'[]', b'\xff'])
def test_frame_rejects_ambiguous_or_invalid_json(raw):
    a, b = socket.socketpair()
    with a, b:
        a.sendall(struct.pack("!I", len(raw)) + raw)
        with pytest.raises((ValueError, UnicodeError)):
            receive(b, 4096)


def test_frame_size_rejected_before_receiving_body():
    a, b = socket.socketpair()
    with a, b:
        a.sendall(struct.pack("!I", 4097))
        with pytest.raises(ValueError, match="bound"):
            receive(b, 4096)


def test_partial_frame_cannot_reset_absolute_deadline():
    a, b = socket.socketpair()
    with a, b:
        a.sendall(struct.pack("!I", 20) + b'{')
        with pytest.raises(TimeoutError):
            receive(b, 4096, deadline=time.monotonic() + 0.02)


@pytest.mark.parametrize("extra", [{"argv": ["anything"]}, {"tenant_id": "tenant-b"},
                                        {"version": True}])
def test_request_rejects_caller_control_of_execution(extra):
    with pytest.raises(ValueError):
        request({"version": 1, "op": "poll"} | extra, "poll")
