"""Shared metadata and publication rules; real DAC UID checks run in hosted CI."""

from hashlib import sha256
import os
from pathlib import Path
import stat
import struct
import sys

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from app.content_access import ContentAccess
from app.job_store import JobStore
from test_jobs import synthetic_principal


def storage(tmp_path):
    return JobStore(None, "unused", tmp_path / "content",
        content_access=ContentAccess(os.geteuid(), os.getegid()), principal_provider=synthetic_principal)


def seeded(tmp_path):
    store = storage(tmp_path)
    payload = b"self-authored synthetic content"
    digest = sha256(payload).hexdigest()
    store._durable_content(payload, digest, "tenant-a")
    directory = store.artifact_root / ".evidence" / sha256(b"tenant-a").hexdigest()
    return store, payload, digest, directory


def test_shared_store_survives_private_umask_and_dedup_never_replaces_inode(tmp_path):
    previous = os.umask(0o077)
    try:
        store, payload, digest, directory = seeded(tmp_path)
    finally:
        os.umask(previous)
    for path in (store.artifact_root, directory.parent, directory):
        info = path.stat()
        assert (info.st_uid, info.st_gid, stat.S_IMODE(info.st_mode)) == (os.geteuid(), os.getegid(), 0o750)
    path = directory / digest
    identity = path.stat().st_ino
    store._durable_content(payload, digest, "tenant-a")
    assert path.stat().st_ino == identity and stat.S_IMODE(path.stat().st_mode) == 0o640
    assert store._read_private_evidence("tenant-a", {"sha256": digest, "size": len(payload)}) == payload
    assert not list(directory.glob(".incoming-*"))


@pytest.mark.parametrize("component", ["root", "evidence", "tenant"])
@pytest.mark.parametrize("mode", [0o770, 0o751, 0o2750])
def test_every_directory_rejects_widened_or_special_permissions_without_repair(tmp_path, component, mode):
    store, payload, digest, directory = seeded(tmp_path)
    target = {"root": store.artifact_root, "evidence": directory.parent, "tenant": directory}[component]
    target.chmod(mode)
    with pytest.raises(ValueError, match="metadata"):
        store._read_private_evidence("tenant-a", {"sha256": digest, "size": len(payload)})
    with pytest.raises(ValueError, match="metadata"):
        store._durable_content(payload, digest, "tenant-a")
    assert stat.S_IMODE(target.stat().st_mode) == mode


@pytest.mark.parametrize("mode", [0o660, 0o644, 0o1640])
def test_bad_final_file_metadata_blocks_reads_and_dedup(tmp_path, mode):
    store, payload, digest, directory = seeded(tmp_path)
    path = directory / digest
    inode = path.stat().st_ino
    path.chmod(mode)
    with pytest.raises(ValueError, match="metadata"):
        store._read_private_evidence("tenant-a", {"sha256": digest, "size": len(payload)})
    with pytest.raises(ValueError, match="existing content-addressed"):
        store._durable_content(payload, digest, "tenant-a")
    assert path.stat().st_ino == inode and not list(directory.glob(".incoming-*"))


@pytest.mark.parametrize("field", ["owner_uid", "reader_gid"])
def test_wrong_expected_identity_cannot_read_existing_store(tmp_path, field):
    store, payload, digest, _ = seeded(tmp_path)
    values = {"owner_uid": os.geteuid(), "reader_gid": os.getegid()}
    values[field] += 1
    store.content_access = ContentAccess(**values)
    with pytest.raises(ValueError, match="metadata"):
        store._read_private_evidence("tenant-a", {"sha256": digest, "size": len(payload)})


def test_nonowner_effective_uid_is_readonly_and_cannot_create(tmp_path, monkeypatch):
    store, payload, digest, directory = seeded(tmp_path)
    before = set(directory.iterdir())
    real_uid = os.geteuid()
    monkeypatch.setattr(os, "geteuid", lambda: real_uid + 1)
    assert store._read_private_evidence("tenant-a", {"sha256": digest, "size": len(payload)}) == payload
    with pytest.raises(ValueError, match="writer identity"):
        store._durable_content(b"new", sha256(b"new").hexdigest(), "tenant-a")
    assert set(directory.iterdir()) == before


def test_reader_group_must_be_in_effective_or_supplementary_groups_before_creation(tmp_path, monkeypatch):
    store = storage(tmp_path)
    group = store.content_access.reader_gid
    monkeypatch.setattr(os, "getegid", lambda: group + 1)
    monkeypatch.setattr(os, "getgroups", lambda: [])
    with pytest.raises(ValueError, match="writer identity"):
        store._durable_content(b"new", sha256(b"new").hexdigest())
    assert not store.artifact_root.exists()


def test_shared_policy_does_not_migrate_a_private_existing_root(tmp_path):
    store = storage(tmp_path)
    store.artifact_root.mkdir(mode=0o700)
    with pytest.raises(ValueError, match="metadata"):
        store._durable_content(b"new", sha256(b"new").hexdigest())
    assert stat.S_IMODE(store.artifact_root.stat().st_mode) == 0o700


def test_public_artifact_read_uses_same_metadata_and_hash_validation(tmp_path):
    store = storage(tmp_path)
    payload = b"synthetic artifact"
    digest = sha256(payload).hexdigest()
    store._durable_content(payload, digest)
    store._publication_row = lambda *_: {"artifact_sha256": digest, "artifact_size": len(payload)}
    assert store.read_artifact("tenant-a", "fixture") == payload
    (store.artifact_root / digest).chmod(0o644)
    with pytest.raises(ValueError, match="metadata"):
        store.read_artifact("tenant-a", "fixture")


def test_metadata_is_synced_before_digest_link(tmp_path, monkeypatch):
    store = storage(tmp_path)
    events = []
    fsync, link = os.fsync, os.link
    def sync(fd):
        info = os.fstat(fd)
        events.append(("sync", info.st_ino, stat.S_IMODE(info.st_mode)))
        return fsync(fd)
    def publish(source, destination, **kwargs):
        fd = os.open(source, os.O_RDONLY, dir_fd=kwargs["src_dir_fd"])
        try:
            info = os.fstat(fd)
            assert ("sync", info.st_ino, 0o640) in events
        finally:
            os.close(fd)
        events.append(("link", destination))
        return link(source, destination, **kwargs)
    monkeypatch.setattr(os, "fsync", sync)
    monkeypatch.setattr(os, "link", publish)
    store._durable_content(b"durable", sha256(b"durable").hexdigest(), "tenant-a")
    assert any(event[0] == "link" for event in events)


def test_fifo_at_digest_name_is_rejected_without_waiting_for_a_writer(tmp_path):
    store, payload, digest, directory = seeded(tmp_path)
    (directory / digest).unlink()
    os.mkfifo(directory / digest, mode=0o640)
    with pytest.raises(ValueError, match="metadata"):
        store._read_private_evidence("tenant-a", {"sha256": digest, "size": len(payload)})
    with pytest.raises(ValueError, match="existing content-addressed"):
        store._durable_content(payload, digest, "tenant-a")


def test_symlink_at_digest_name_is_rejected_and_never_overwritten(tmp_path):
    store, payload, digest, directory = seeded(tmp_path)
    path = directory / digest
    path.unlink()
    target = tmp_path / "outside"
    target.write_bytes(payload)
    path.symlink_to(target)
    with pytest.raises(OSError):
        store._read_private_evidence("tenant-a", {"sha256": digest, "size": len(payload)})
    with pytest.raises(OSError):
        store._durable_content(payload, digest, "tenant-a")
    assert path.is_symlink() and target.read_bytes() == payload
    assert not list(directory.glob(".incoming-*"))


@pytest.mark.parametrize("scope", ["file", "directory", "default"])
def test_named_acl_cannot_widen_access_while_mode_numbers_stay_unchanged(tmp_path, scope):
    store, payload, digest, directory = seeded(tmp_path)
    target = directory / digest if scope == "file" else store.artifact_root
    permission = 4 if scope == "file" else 5
    entries = ((1, 6 if scope == "file" else 7, 0xffffffff), (2, permission, os.geteuid() + 1),
               (4, permission, 0xffffffff), (16, permission, 0xffffffff), (32, 0, 0xffffffff))
    acl = struct.pack("<I", 2) + b"".join(struct.pack("<HHI", *entry) for entry in entries)
    attribute = "system.posix_acl_default" if scope == "default" else "system.posix_acl_access"
    os.setxattr(target, attribute, acl)
    assert stat.S_IMODE(target.stat().st_mode) == (0o640 if scope == "file" else 0o750)
    with pytest.raises(ValueError, match="ACL"):
        store._read_private_evidence("tenant-a", {"sha256": digest, "size": len(payload)})


def test_new_store_rejects_inherited_acl_before_granting_group_read(tmp_path):
    store = storage(tmp_path)
    entries = ((1, 7, 0xffffffff), (2, 5, os.geteuid() + 1), (4, 5, 0xffffffff),
               (16, 5, 0xffffffff), (32, 0, 0xffffffff))
    acl = struct.pack("<I", 2) + b"".join(struct.pack("<HHI", *entry) for entry in entries)
    os.setxattr(tmp_path, "system.posix_acl_default", acl)
    with pytest.raises(ValueError, match="inherited content ACL"):
        store._durable_content(b"new", sha256(b"new").hexdigest())
    assert stat.S_IMODE(store.artifact_root.stat().st_mode) == 0o700
    assert not list(store.artifact_root.iterdir())
