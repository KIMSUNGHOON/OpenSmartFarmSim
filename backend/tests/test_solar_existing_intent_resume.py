"""Existing Solar history cannot be recreated before its current authority check."""
from hashlib import sha256
import fcntl
import json
import os

import pytest

from app import crop_greenhouse_solar_server_custody as model
from app import runtime_connection_scope
from test_crop_greenhouse_solar_server_custody import (
    setup, authoring, profiles, login_database, login_scope, cleanup,
    settle_owned_database_backends, pytestmark, save)


def started(setup):
    server, raw, value = setup
    for _ in range(2): progress = json.loads(server.advance('tenant-1', raw, budget=1))
    assert progress['steps'] == 1
    identity = model._intent_id('tenant-1', json.loads(raw))
    return server, raw, value, server.directory / identity


def snapshot(root):
    return {str(path.relative_to(root)): (path.stat().st_mode, sha256(path.read_bytes()).hexdigest())
            for path in root.rglob('*') if path.is_file()}


def assert_closed(server):
    farms = server.binding.farms
    assert farms._registration_read.get() is None and runtime_connection_scope._CURRENT.get() is None
    source = farms.replay.candidates._source._source
    assert source._scoped_reader.get() is farms.replay.candidates._scoped_reader.get() is None


def forbid_consumption_or_creation(patch):
    calls = []

    def forbidden(*args, **kwargs):
        calls.append(1)
        pytest.fail('unverified resume consumed or created calculation history')

    opening = os.open

    def noncreating(path, flags, *args, **kwargs):
        if flags & (os.O_CREAT | os.O_TRUNC): forbidden()
        return opening(path, flags, *args, **kwargs)

    patch.setattr(os, 'open', noncreating)
    patch.setattr(os, 'mkdir', forbidden)
    patch.setattr(model.files, '_immutable', forbidden)
    patch.setattr(model._Session, '_load', forbidden)
    for name in ('prepare_context', 'start', 'restore_checkpoint', 'advance_chunk'):
        patch.setattr(model.continuation, name, forbidden)
    return calls


def test_existing_resume_entry_never_creates_and_keeps_its_selected_head(setup, monkeypatch):
    server, raw, _, intent = started(setup)
    before = snapshot(server.directory)
    current = type(server.binding).current
    checks = []

    def checking(binding, *args, **kwargs):
        result = current(binding, *args, **kwargs)
        checks.append(1)
        return result

    with monkeypatch.context() as patch:
        calls = forbid_consumption_or_creation(patch)
        patch.setattr(type(server.binding), 'current', checking)
        with server._open('tenant-1', raw, True, _advance_resume=True) as (session, _):
            assert not checks
            assert session._resume_head == (intent / 'artifact' / 'HEAD').read_bytes()
            session._guard()
            assert checks == [1]
    assert not calls and snapshot(server.directory) == before
    assert_closed(server)
    save('existing-resume-noncreating-entry.json', {'checks': len(checks), 'creation_or_consumption': 0})


def test_resume_option_rejects_invalid_modes_before_touching_history(setup):
    server, raw, _ = setup
    before = snapshot(server.directory)
    for mode in (None, 0, 1, 'false', [], {}, object()):
        with pytest.raises(model.SolarCustodyHold):
            with server._open('tenant-1', raw, True, _advance_resume=mode):
                pytest.fail('invalid resume option yielded')
    for write, entry in ((False, True), (True, False)):
        with pytest.raises(model.SolarCustodyHold):
            with server._open('tenant-1', raw, write, entry_guard=entry, _advance_resume=True):
                pytest.fail('invalid entry combination yielded')
    assert snapshot(server.directory) == before
    assert_closed(server)


def test_default_and_new_intent_entries_keep_eager_current_validation(setup, tmp_path, monkeypatch):
    server, raw, _, _ = started(setup)
    current = type(server.binding).current
    checks = []

    def checking(binding, *args, **kwargs):
        result = current(binding, *args, **kwargs)
        checks.append(binding)
        return result

    monkeypatch.setattr(type(server.binding), 'current', checking)
    for write in (True, False):
        checks.clear()
        with server._open('tenant-1', raw, write) as (session, _):
            assert checks == [server.binding] and session._resume_head is None
    root = tmp_path / 'new-custody'
    root.mkdir(mode=0o700)
    fresh = type(server)(server.binding, root, input_resolver=server.input_resolver,
                         integrity_key=server.integrity_key)
    checks.clear()
    with fresh._open('tenant-1', raw, True, _advance_resume=True) as (session, _):
        assert checks == [server.binding] and session._resume_head is None
    assert_closed(server)


def test_selected_resume_never_recreates_lost_history_members(setup, tmp_path, monkeypatch):
    server, raw, _, intent = started(setup)
    original = model._existing_history
    before = snapshot(server.directory)
    members = [server.directory / '.custody-lock', intent / '.intent-lock',
               intent / 'intent.json', intent / 'proofs', intent / 'artifact',
               intent / 'artifact' / 'HEAD']
    for index, member in enumerate(members):
        parked = tmp_path / ('missing-member-' + str(index))

        def lose(root, identity):
            assert original(root, identity) is True
            member.rename(parked)
            return True

        try:
            with monkeypatch.context() as patch:
                patch.setattr(model, '_existing_history', lose)
                calls = forbid_consumption_or_creation(patch)
                with pytest.raises(model.SolarCustodyHold): server.advance('tenant-1', raw, budget=1)
                assert not calls
        finally:
            if parked.exists(): parked.rename(member)
        assert snapshot(server.directory) == before
        assert_closed(server)
    save('existing-resume-lost-members.json', {'fault_vectors': len(members), 'creation_or_consumption': 0})


def test_selected_resume_rechecks_late_physical_economic_review_and_scope_rights(setup, monkeypatch):
    server, raw, value, _ = started(setup)
    original = model._existing_history
    before = snapshot(server.directory)
    source = server.binding.farms.replay.candidates._source._source
    for fault in ('physical', 'economic', 'review', 'scope'):
        prior_status = value[2][3]['status']
        prior_scopes = set(value[4]['scopes'])
        try:
            with monkeypatch.context() as patch:
                def revoke(root, identity):
                    assert original(root, identity) is True
                    if fault == 'physical': value[5].allowed = False
                    elif fault == 'economic': patch.setattr(source, 'get_input_rights', lambda *_: None)
                    elif fault == 'review': value[2][3]['status'] = 'revoked'
                    else: value[4]['scopes'].discard('crop_result_write')
                    return True

                patch.setattr(model, '_existing_history', revoke)
                calls = forbid_consumption_or_creation(patch)
                with pytest.raises((model.SolarCustodyHold, PermissionError)):
                    server.advance('tenant-1', raw, budget=1)
                assert not calls
        finally:
            value[5].allowed = True
            value[2][3]['status'] = prior_status
            value[4]['scopes'].clear(); value[4]['scopes'].update(prior_scopes)
        assert snapshot(server.directory) == before
        assert_closed(server)
    save('existing-resume-current-rights.json', {'fault_vectors': 4, 'creation_or_consumption': 0})


def test_resume_rejects_missing_changed_or_authentic_older_head_after_first_guard(setup, tmp_path, monkeypatch):
    server, raw, _, intent = started(setup)
    head = intent / 'artifact' / 'HEAD'
    original_raw = head.read_bytes()
    digest = model._head(json.loads(original_raw))
    current_proof = json.loads((intent / 'proofs' / (digest + '.json')).read_bytes())['payload']
    parent = current_proof['parent']['head_sha256']
    older = json.loads((intent / 'proofs' / (parent + '.json')).read_bytes())['payload']['head']
    older_raw = model._canonical(older)
    assert older_raw != original_raw
    before = snapshot(server.directory)
    current = type(server.binding).current
    for fault in ('missing', 'changed', 'authentic_older'):
        armed = [True]
        parked = tmp_path / 'head-removed-after-check'

        def change_after_check(binding, *args, **kwargs):
            result = current(binding, *args, **kwargs)
            if binding is server.binding and armed[0]:
                armed[0] = False
                if fault == 'missing': head.rename(parked)
                else:
                    head.chmod(0o600)
                    head.write_bytes(b'{}' if fault == 'changed' else older_raw)
                    head.chmod(0o400)
            return result

        try:
            with monkeypatch.context() as patch:
                patch.setattr(type(server.binding), 'current', change_after_check)
                calls = forbid_consumption_or_creation(patch)
                with pytest.raises(model.SolarCustodyHold): server.advance('tenant-1', raw, budget=1)
                assert not armed[0] and not calls
        finally:
            if parked.exists(): parked.rename(head)
            head.chmod(0o600); head.write_bytes(original_raw); head.chmod(0o400)
        assert snapshot(server.directory) == before
        assert_closed(server)
    save('existing-resume-selected-head.json', {'fault_vectors': 3, 'creation_or_consumption': 0})


def test_resume_preserves_actual_existing_shared_and_exclusive_lock_conflicts(setup, monkeypatch):
    server, raw, _, intent = started(setup)
    before = snapshot(server.directory)
    for lock in (server.directory / '.custody-lock', intent / '.intent-lock'):
        for mode in (fcntl.LOCK_SH, fcntl.LOCK_EX):
            with lock.open('rb') as holder:
                fcntl.flock(holder, mode | fcntl.LOCK_NB)
                with monkeypatch.context() as patch:
                    calls = forbid_consumption_or_creation(patch)
                    with pytest.raises(model.SolarCustodyPending): server.advance('tenant-1', raw, budget=1)
                    assert not calls
            assert snapshot(server.directory) == before
            assert_closed(server)
    save('existing-resume-existing-locks.json', {'fault_vectors': 4, 'creation_or_consumption': 0})
