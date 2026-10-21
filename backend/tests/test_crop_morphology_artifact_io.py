from hashlib import sha256
import os
from pathlib import Path
import subprocess
import sys

import pytest

from app.content_access import ContentAccess
from app.crop_morphology_artifact_io import MorphologyBlobStore, MorphologyArtifactHold
from app.job_store import JobStore


def access():
    return ContentAccess(os.getuid(), os.getgid())


def test_original_bytes_same_digest_retry_metadata_and_fresh_process_read(tmp_path, monkeypatch):
    def forbidden(*args,**kwargs):
        raise AssertionError('DB connection forbidden for file transport')
    monkeypatch.setattr(JobStore, 'connect', forbidden)
    root = tmp_path/'artifact'
    raw = b'{"origin":"synthetic"}'
    with MorphologyBlobStore(root, access(), write=True) as store:
        digest = store.put(raw,maximum=1024)
        assert digest == sha256(raw).hexdigest()
        before = (root/digest).stat()
        assert store.put(raw,maximum=1024) == digest
        assert (root/digest).stat() == before
        assert store.get(digest,maximum=1024) == raw
    code = """import os,sys
from pathlib import Path
from app.content_access import ContentAccess
from app.crop_morphology_artifact_io import MorphologyBlobStore
from app.job_store import JobStore
JobStore.connect=lambda *a,**k: (_ for _ in ()).throw(AssertionError('database forbidden'))
with MorphologyBlobStore(Path(sys.argv[1]),ContentAccess(os.getuid(),os.getgid())) as store:
 assert store.get(sys.argv[2],maximum=1024)==b'{"origin":"synthetic"}'
print('fresh-read-ok')
"""
    done = subprocess.run([sys.executable,'-c',code,str(root),digest],capture_output=True,text=True,timeout=10)
    assert done.returncode == 0,done.stderr
    assert done.stdout.strip() == 'fresh-read-ok'


def test_second_writer_rejected_but_reader_allowed(tmp_path):
    root = tmp_path/'artifact'
    with MorphologyBlobStore(root,access(),write=True) as first:
        digest = first.put(b'{}',maximum=1024)
        with pytest.raises(MorphologyArtifactHold):
            MorphologyBlobStore(root,access(),write=True)
        with MorphologyBlobStore(root,access()) as reader:
            assert reader.get(digest,maximum=1024)==b'{}'
        with pytest.raises(MorphologyArtifactHold):
            reader.put(b'{}',maximum=1024)


@pytest.mark.parametrize('change',['symlink','hardlink','permissions','bytes','oversize','directory-replacement'])
def test_changed_artifact_never_returns_bytes(tmp_path,change):
    root = tmp_path/'artifact'
    with MorphologyBlobStore(root,access(),write=True) as writer:
        digest = writer.put(b'{}',maximum=1024)
    with MorphologyBlobStore(root,access()) as reader:
        path = root/digest
        if change=='symlink':
            other=tmp_path/'other';other.write_bytes(b'{}');path.unlink();path.symlink_to(other)
        elif change=='hardlink':os.link(path,tmp_path/'second-link')
        elif change=='permissions':path.chmod(0o644)
        elif change=='bytes':path.write_bytes(b'[]')
        elif change=='oversize':path.write_bytes(b'x'*1025)
        else:root.rename(tmp_path/'original');root.mkdir(mode=0o750)
        with pytest.raises(MorphologyArtifactHold):
            reader.get(digest,maximum=1024)


def test_symlink_parent_and_non_private_metadata_hold(tmp_path):
    root = tmp_path/'real';root.mkdir(mode=0o750)
    link=tmp_path/'link';link.symlink_to(root,target_is_directory=True)
    with pytest.raises(MorphologyArtifactHold):
        MorphologyBlobStore(link/'child',access(),write=True)
    root.chmod(0o777)
    with pytest.raises(MorphologyArtifactHold):
        MorphologyBlobStore(root,access())


@pytest.mark.parametrize('maximum',[True,0,16*1024**2+1])
def test_bounds_are_explicit(tmp_path,maximum):
    with MorphologyBlobStore(tmp_path/'artifact',access(),write=True) as writer:
        with pytest.raises(MorphologyArtifactHold):writer.put(b'{}',maximum=maximum)


def test_reader_cannot_put_and_bad_digest_does_not_escape_root(tmp_path):
    root=tmp_path/'artifact'
    with MorphologyBlobStore(root,access(),write=True):pass
    with MorphologyBlobStore(root,access()) as reader:
        with pytest.raises(MorphologyArtifactHold):reader.put(b'{}',maximum=1024)
        with pytest.raises(MorphologyArtifactHold):reader.get('../outside',maximum=1024)


def test_handles_close_after_repeated_failure_without_fd_growth(tmp_path):
    root=tmp_path/'artifact'
    with MorphologyBlobStore(root,access(),write=True):pass
    before=len(os.listdir('/proc/self/fd'))
    for _ in range(20):
        with pytest.raises(MorphologyArtifactHold):
            with MorphologyBlobStore(root,access()) as reader:
                reader.get('0'*64,maximum=1024)
    assert len(os.listdir('/proc/self/fd'))==before
