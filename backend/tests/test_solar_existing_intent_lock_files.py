"""Noncreating Solar locks preserve the original file security requirements."""
import os

import pytest

from app import crop_greenhouse_solar_server_custody as model
from test_solar_existing_intent_resume import (
    setup, authoring, profiles, login_database, login_scope, cleanup,
    settle_owned_database_backends, pytestmark, started, snapshot,
    forbid_consumption_or_creation, assert_closed)
from test_crop_greenhouse_solar_server_custody import save


def test_resume_rejects_symlink_hardlink_nonempty_and_wrong_mode_lock_files(setup, tmp_path, monkeypatch):
    server, raw, _, intent = started(setup)
    before = snapshot(server.directory)
    vectors = 0
    for index, lock in enumerate((server.directory / '.custody-lock', intent / '.intent-lock')):
        for fault in ('symlink', 'hardlink', 'nonempty', 'mode'):
            parked = tmp_path / ('original-lock-' + str(index))
            link = tmp_path / ('extra-link-' + str(index))
            try:
                if fault == 'symlink': lock.rename(parked); lock.symlink_to(parked)
                elif fault == 'hardlink':
                    os.link(lock, link)
                elif fault == 'nonempty': lock.write_bytes(b'x')
                else: lock.chmod(0o400)
                with monkeypatch.context() as patch:
                    calls = forbid_consumption_or_creation(patch)
                    with pytest.raises((model.SolarCustodyHold, PermissionError)) as denied:
                        server.advance('tenant-1', raw, budget=1)
                    if isinstance(denied.value, PermissionError):
                        assert fault == 'mode' and lock == server.directory / '.custody-lock'
                    assert not calls
            finally:
                if parked.exists(): lock.unlink(); parked.rename(lock)
                if link.exists(): link.unlink()
                lock.chmod(0o600); lock.write_bytes(b'')
            assert snapshot(server.directory) == before
            assert_closed(server)
            vectors += 1
    save('existing-resume-lock-file-security.json', {'fault_vectors': vectors, 'creation_or_consumption': 0})
