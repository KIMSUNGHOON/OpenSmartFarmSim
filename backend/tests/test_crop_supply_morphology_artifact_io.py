"""A later identical replacement must not bypass an earlier immutable read."""
import os
from pathlib import Path

import pytest

from app.content_access import ContentAccess
from app.crop_morphology_artifact_io import MorphologyBlobStore


def test_reader_rejects_identical_bytes_replaced_after_projection(tmp_path, monkeypatch):
    from app import crop_supply_morphology_artifact_reader as reader
    access = ContentAccess(owner_uid=os.getuid(), reader_gid=os.getgid())
    directory = tmp_path / 'artifact'
    with MorphologyBlobStore(directory, access, write=True) as store:
        digest = store.put(b'{"original":true}', maximum=reader.MAX)
        observed = {}
        reader._read(store, digest, observed)
        replacement = tmp_path / 'replacement'
        replacement.write_bytes(b'{"original":true}')
        replacement.chmod(0o640)
        replacement.replace(directory / digest)
        monkeypatch.setattr(reader, '_pins', lambda: {'test': 'fixed-current-code'})
        with pytest.raises(ValueError, match='STORAGE_HOLD'):
            reader._fence(store, {'code_sha256': reader._pins()}, observed)


def test_unchanged_immutable_read_preserves_bytes_and_policy(tmp_path, monkeypatch):
    from app import crop_supply_morphology_artifact_reader as reader
    access = ContentAccess(owner_uid=os.getuid(), reader_gid=os.getgid())
    with MorphologyBlobStore(tmp_path / 'artifact', access, write=True) as store:
        original = b'{"original":true}'
        digest = store.put(original, maximum=reader.MAX)
        observed = {}
        assert reader._read(store, digest, observed) == original
        monkeypatch.setattr(reader, '_pins', lambda: {'test': 'fixed-current-code'})
        reader._fence(store, {'code_sha256': reader._pins()}, observed)
        assert store.get(digest, maximum=reader.MAX) == original


@pytest.mark.parametrize('loaded', ['reader', 'projection'])
def test_changed_files_cannot_describe_an_older_loaded_reader_as_current(monkeypatch, loaded):
    from app import crop_supply_morphology_artifact_reader as reader
    target = Path(reader.__file__ if loaded == 'reader' else reader.projection.__file__).resolve()
    original = Path.read_bytes
    def changed(path):
        raw = original(path)
        return raw + b'changed-after-import' if path == target else raw
    monkeypatch.setattr(Path, 'read_bytes', changed)
    with pytest.raises(ValueError, match='CODE_HOLD'):
        reader._pins()
