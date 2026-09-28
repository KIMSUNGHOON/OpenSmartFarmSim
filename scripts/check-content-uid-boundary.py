#!/usr/bin/env python3
"""Root-controlled disposable DAC probe, not a full service/G1/G4 acceptance."""

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

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "backend"))
from app.content_access import ContentAccess
from app.job_store import JobStore


AUTHORITY, SUPERVISOR, WORKER, READ_GROUP = 11001, 11002, 11003, 11010
PAYLOAD = b"self-authored UID storage fixture"
DIGEST = sha256(PAYLOAD).hexdigest()

PROBE = r'''
import errno, hashlib, json, os, sys
path, operation, uid, gid, groups = sys.argv[1:]
uid, gid, groups = int(uid), int(gid), json.loads(groups)
assert os.getresuid() == (uid, uid, uid) and os.getresgid() == (gid, gid, gid)
assert sorted(os.getgroups()) == sorted(groups)
try:
    flags = os.O_RDONLY if operation == 'read' else os.O_WRONLY
    if operation == 'create':
        path += '/probe'
        flags |= os.O_CREAT | os.O_EXCL
    fd = os.open(path, flags | os.O_NOFOLLOW, 0o600)
    try:
        data = os.read(fd, 256) if operation == 'read' else None
    finally:
        os.close(fd)
    result = {'allowed': True}
    if operation == 'read' and len(path.split('/')[-1]) == 64:
        result['digest'] = hashlib.sha256(data).hexdigest()
except OSError as error:
    assert error.errno in (errno.EACCES, errno.EPERM)
    result = {'allowed': False}
print(json.dumps(result))
'''


def drop(uid, groups):
    os.setgroups(groups)
    os.setgid(uid)
    os.setuid(uid)


def probe(path, operation, uid, groups, expected):
    run = subprocess.run(["/usr/bin/python3", "-I", "-c", PROBE, str(path), operation,
        str(uid), str(uid), json.dumps(groups)],
        preexec_fn=lambda: drop(uid, groups), env={"PATH": "/usr/bin:/bin", "LANG": "C.UTF-8"},
        capture_output=True, timeout=5)
    if run.returncode != 0:
        raise ValueError("UID probe failed")
    result = json.loads(run.stdout)
    assert result["allowed"] is expected
    if expected and path.name == DIGEST and operation == "read":
        assert result["digest"] == DIGEST


def publish(root):
    read_fd, write_fd = os.pipe()
    pid = os.fork()
    if pid == 0:
        os.close(read_fd)
        try:
            os.environ.clear()
            drop(AUTHORITY, [READ_GROUP])
            assert os.getresuid() == (AUTHORITY,) * 3 and os.getresgid() == (AUTHORITY,) * 3
            assert os.getgroups() == [READ_GROUP]
            store = JobStore(None, "unused", root / "artifacts",
                content_access=ContentAccess(AUTHORITY, READ_GROUP))
            store._durable_content(PAYLOAD, DIGEST, "tenant-a")
            store._durable_content(PAYLOAD, DIGEST)
            os.write(write_fd, b"ok")
            os._exit(0)
        except BaseException:
            os._exit(1)
    os.close(write_fd)
    try:
        assert select.select([read_fd], [], [], 10)[0]
        assert os.read(read_fd, 3) == b"ok"
        for _ in range(100):
            done, status = os.waitpid(pid, os.WNOHANG)
            if done:
                pid = None
                assert os.waitstatus_to_exitcode(status) == 0
                return
            select.select([], [], [], 0.02)
        raise TimeoutError("writer exit deadline")
    finally:
        os.close(read_fd)
        if pid is not None:
            try: os.kill(pid, signal.SIGKILL)
            except ProcessLookupError: pass
            os.waitpid(pid, 0)


def main():
    if os.geteuid() != 0:
        raise SystemExit("root required for disposable UID smoke")
    for uid in (AUTHORITY, SUPERVISOR, WORKER):
        try: pwd.getpwuid(uid)
        except KeyError: continue
        raise ValueError("disposable probe UID is already assigned")
    with tempfile.TemporaryDirectory(prefix="ossf-content-uid-") as directory:
        root = Path(directory)
        root.chmod(0o711)
        content = root / "content"
        content.mkdir(mode=0o710)
        os.chown(content, AUTHORITY, READ_GROUP)
        publish(content)
        artifacts = content / "artifacts"
        evidence = artifacts / ".evidence" / sha256(b"tenant-a").hexdigest()
        for path in (artifacts / DIGEST, evidence / DIGEST):
            probe(path, "read", SUPERVISOR, [READ_GROUP], True)
            probe(path, "write", SUPERVISOR, [READ_GROUP], False)
            probe(path, "read", WORKER, [], False)
            probe(path, "write", WORKER, [], False)
        probe(evidence, "create", SUPERVISOR, [READ_GROUP], False)
        probe(evidence, "create", WORKER, [], False)
        for uid, name in ((AUTHORITY, "db-password"), (SUPERVISOR, "signing-key")):
            secret = root / name
            secret.mkdir(mode=0o700)
            os.chown(secret, uid, uid)
            file = secret / "private"
            file.write_bytes(os.urandom(32))
            file.chmod(0o600)
            os.chown(file, uid, uid)
            probe(file, "read", WORKER, [], False)
            probe(file, "read", uid, [READ_GROUP], True)
            other = SUPERVISOR if uid == AUTHORITY else AUTHORITY
            probe(file, "read", other, [READ_GROUP], False)
        # A privileged provisioner may corrupt metadata; the reader still checks the opened file.
        os.chown(evidence / DIGEST, WORKER, READ_GROUP)
        store = JobStore(None, "unused", artifacts, content_access=ContentAccess(AUTHORITY, READ_GROUP))
        try:
            store._read_private_evidence("tenant-a", {"sha256": DIGEST, "size": len(PAYLOAD)})
        except ValueError:
            pass
        else:
            raise ValueError("changed file owner was accepted")
    print("Content UID DAC smoke passed: authority writer, supervisor read-only, worker denied; private credentials/key denied. Software filesystem scope only.")


if __name__ == "__main__":
    main()
