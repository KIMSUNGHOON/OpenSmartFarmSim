"""Actual writer/read validation races, stale snapshots and fail-closed cleanup."""
from concurrent.futures import ThreadPoolExecutor
from contextlib import contextmanager
import json
import os
import threading

import pytest

import test_crop_greenhouse_solar_shared_read_locks as reference
from test_crop_greenhouse_solar_shared_read_locks import (
    started, worker_setup, producer_setup, authoring, profiles, login_database,
    original_login_scope, login_scope, query_cleanup)
from test_crop_solar_custody_file_locks import exclusive_locks, probe

custody = reference.custody
pytestmark = reference.pytestmark


def paths(server, raw):
    intent = server.directory/custody._intent_id('tenant-1', json.loads(raw))
    return server.directory/'.custody-lock', intent/'.intent-lock', intent/'artifact'


@contextmanager
def validating_reader(server, raw, monkeypatch):
    state = threading.local(); entered = threading.Event(); resume = threading.Event()
    reader_ident = []
    original_load, original_current = custody._Session._load, type(server.binding).current
    def load(session, *args, **kwargs):
        value = original_load(session, *args, **kwargs)
        if reader_ident and threading.get_ident() == reader_ident[0]: state.loaded = True
        return value
    def current(binding, *args, **kwargs):
        if getattr(state, 'loaded', False) and not getattr(state, 'blocked', False):
            state.blocked = True; entered.set()
            assert resume.wait(30), 'owned read validation was not released'
        return original_current(binding, *args, **kwargs)
    def reader():
        reader_ident.append(threading.get_ident())
        return server.inspect('tenant-1', raw)
    with monkeypatch.context() as patch:
        patch.setattr(custody._Session, '_load', load)
        patch.setattr(type(server.binding), 'current', current)
        with ThreadPoolExecutor(max_workers=1) as pool:
            future = pool.submit(reader)
            try:
                assert entered.wait(40), 'actual read did not reach post-capture current validation'
                yield resume, future
            finally: resume.set()


def test_writer_advances_during_current_validation_and_stale_read_is_pending(started, monkeypatch):
    worker, _, raw, expected, _ = started; server = worker.server
    with validating_reader(server, raw, monkeypatch) as (resume, future):
        advanced = json.loads(server.advance('tenant-1', raw, budget=1))
        resume.set()
        with pytest.raises(custody.SolarCustodyPending): future.result(timeout=40)
    assert advanced['steps'] == expected['steps']+1 == 2
    assert advanced['times']['last_confirmed']['at'] == '2026-10-01T00:00:04.123456Z'
    assert json.loads(server.inspect('tenant-1', raw)) == advanced


@pytest.mark.parametrize('lock', [0, 1], ids=['root', 'intent'])
def test_reacquisition_fails_closed_and_releases_partial_locks(started, monkeypatch, lock):
    worker, _, raw, expected, _ = started; server = worker.server
    locks = paths(server, raw)[:2]; before = len(os.listdir('/proc/self/fd'))
    with validating_reader(server, raw, monkeypatch) as (resume, future):
        with exclusive_locks(locks[lock]):
            resume.set()
            with pytest.raises(custody.SolarCustodyPending): future.result(timeout=40)
    assert all(probe(path, 'exclusive') == 0 for path in locks)
    assert json.loads(server.inspect('tenant-1', raw)) == expected
    assert len(os.listdir('/proc/self/fd')) == before


@pytest.mark.parametrize('lock', [0, 1], ids=['root', 'intent'])
def test_replaced_named_lock_rejects_same_live_old_descriptor(started, monkeypatch, lock):
    worker, _, raw, expected, _ = started; server = worker.server
    path = paths(server, raw)[lock]; original = server.directory.parent/'reader-original-lock'
    with validating_reader(server, raw, monkeypatch) as (resume, future):
        path.rename(original)
        try:
            path.touch(mode=0o600)
            resume.set()
            with pytest.raises(custody.SolarCustodyHold): future.result(timeout=40)
        finally:
            path.unlink(); original.rename(path)
    assert json.loads(server.inspect('tenant-1', raw)) == expected
    assert all(probe(path, 'exclusive') == 0 for path in paths(server, raw)[:2])


def test_failed_publication_with_same_HEAD_does_not_return_old_storage_counts(started, monkeypatch):
    worker, _, raw, expected, _ = started; server = worker.server
    artifact = paths(server, raw)[2]; head = (artifact/'HEAD').read_bytes()
    before = {p.name: p.stat().st_size for p in artifact.iterdir()}
    def fail(*args, **kwargs): raise RuntimeError('owned pre-HEAD publication failure')
    with validating_reader(server, raw, monkeypatch) as (resume, future):
        monkeypatch.setattr(custody._Session, '_publish', fail)
        with pytest.raises(custody.SolarCustodyHold): server.advance('tenant-1', raw, budget=1)
        assert (artifact/'HEAD').read_bytes() == head
        assert {p.name: p.stat().st_size for p in artifact.iterdir()} != before
        resume.set()
        with pytest.raises(custody.SolarCustodyPending): future.result(timeout=40)
    recovered = json.loads(server.inspect('tenant-1', raw))
    assert recovered['head_sha256'] == expected['head_sha256'] and recovered['steps'] == 1
    assert recovered['times'] == expected['times']
    assert (recovered['storage_bytes'], recovered['file_count']) != (expected['storage_bytes'], expected['file_count'])


def test_rights_failure_returns_no_snapshot_and_releases_both_locks(started, monkeypatch):
    worker, _, raw, _, _ = started; server = worker.server
    rights = worker.server.binding.input_rights
    with validating_reader(server, raw, monkeypatch) as (resume, future):
        rights.allowed = False
        try:
            resume.set()
            with pytest.raises((custody.SolarCustodyHold, PermissionError)): future.result(timeout=40)
        finally: rights.allowed = True
    assert all(probe(path, 'exclusive') == 0 for path in paths(server, raw)[:2])
