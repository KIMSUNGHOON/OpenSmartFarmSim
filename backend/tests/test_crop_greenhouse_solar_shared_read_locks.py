"""Real read/confirmation coexistence while custody writers remain excluded."""
from concurrent.futures import ThreadPoolExecutor
from hashlib import sha256
import json
import os
import threading

import pytest

from test_crop_solar_custody_file_locks import probe

from app import crop_greenhouse_solar_server_custody as custody
from test_crop_greenhouse_solar_execution_query import (
    worker_setup, producer_setup, authoring, profiles, login_database,
    original_login_scope, login_scope, query_cleanup)
import test_crop_greenhouse_solar_execution_query as reference

pytestmark = [reference.reference.pytestmark, pytest.mark.usefixtures('query_cleanup')]


@pytest.fixture
def started(worker_setup):
    worker, job_id, raw, _ = worker_setup
    server = worker.server
    initial = json.loads(server.advance('tenant-1', raw, budget=1))
    expected = json.loads(server.advance('tenant-1', raw, budget=1))
    assert initial['steps'] == 0 and expected['steps'] == 1
    lease = worker.jobs.claim(600, tenant_id='tenant-1', allowed_stages=('simulation',), job_id=job_id)
    assert lease
    return worker, job_id, raw, expected, lease


def test_checkpoint_confirmation_coexists_with_an_actual_read_session(started):
    worker, job_id, raw, expected, lease = started
    server = worker.server
    error = None
    with server._open('tenant-1', raw, False) as (reader, _):
        before = reader.progress()
        with ThreadPoolExecutor(max_workers=1) as pool:
            try: confirmed = pool.submit(worker._confirm, lease).result(timeout=40)
            except Exception as caught: error = caught
        if error is None:
            assert confirmed['checkpoint']['steps'] == expected['steps']
            assert confirmed['checkpoint']['head_sha256'] == expected['head_sha256']
            assert confirmed['checkpoint']['proof_sha256'] == expected['proof_sha256']
            assert confirmed['checkpoint']['computed_through_utc'] == expected['times']['last_confirmed']['at']
        assert reader.progress() == before
    if error is not None: raise error



def tree(path):
    return {str(p.relative_to(path)):(p.lstat().st_dev, p.lstat().st_ino, p.lstat().st_mode,
        sha256(p.read_bytes()).hexdigest() if p.is_file() else None) for p in path.rglob('*')}


@pytest.mark.parametrize('write', [False, True])
def test_actual_sessions_keep_writer_exclusion_and_release(started, write):
    worker, _, raw, expected, _ = started
    server = worker.server
    identity = custody._intent_id('tenant-1', json.loads(raw))
    locks = (server.directory/'.custody-lock', server.directory/identity/'.intent-lock')
    with server._open('tenant-1', raw, write):
        for path in locks:
            assert probe(path, 'exclusive') == 2
            assert probe(path, 'shared') == (2 if write else 0)
        def incompatible():
            with server._open('tenant-1', raw, not write): pass
        with ThreadPoolExecutor(max_workers=1) as pool:
            with pytest.raises(custody.SolarCustodyPending): pool.submit(incompatible).result(timeout=40)
    for path in locks: assert probe(path, 'exclusive') == 0
    with server._open('tenant-1', raw, True) as (writer, _):
        assert json.loads(writer.progress())['head_sha256'] == expected['head_sha256']


def test_progress_query_and_duplicate_confirmation_coexist(started, monkeypatch):
    worker, job_id, raw, expected, lease = started
    confirmed = worker._confirm(lease)
    query = reference.model.SolarExecutionQuery(worker.checkpoints, worker.results)
    original = custody._Session.progress
    caller = threading.get_ident();observed = [];errors = []
    def while_reading(session):
        if threading.get_ident() == caller and not observed:
            observed.append(True)
            with ThreadPoolExecutor(max_workers=1) as pool:
                try: observed.append(pool.submit(worker._confirm, lease).result(timeout=40))
                except Exception as error: errors.append(error)
        return original(session)
    monkeypatch.setattr(custody._Session, 'progress', while_reading)
    value = reference.read(query, job_id)
    if errors: raise errors[0]
    assert observed[1] == confirmed
    assert value['checkpoint_status'] == 'current'
    assert value['checkpoint']['head_sha256'] == expected['head_sha256']


def test_read_session_cannot_prepare_advance_or_publish(started, monkeypatch):
    worker, _, raw, _, _ = started
    before = tree(worker.server.directory);calls = []
    def forbidden(*args, **kwargs):
        calls.append(True)
        raise AssertionError('read session entered numerical/publication work')
    with worker.server._open('tenant-1', raw, False) as (reader, prepare):
        with monkeypatch.context() as patch:
            patch.setattr(custody.continuation, 'prepare_context', forbidden)
            patch.setattr(custody.continuation, 'advance_chunk', forbidden)
            for operation in (prepare, lambda:reader.advance(1, forbidden),
                              lambda:reader._publish(None, forbidden, {})):
                with pytest.raises(custody.SolarCustodyHold): operation()
        assert not calls
    assert tree(worker.server.directory) == before


@pytest.mark.parametrize('name', ['.custody-lock', '.intent-lock'])
def test_read_session_cannot_recreate_a_missing_lock(started, name):
    worker, _, raw, _, _ = started
    server = worker.server
    identity = custody._intent_id('tenant-1', json.loads(raw))
    path = server.directory/name if name == '.custody-lock' else server.directory/identity/name
    path.unlink();before = tree(server.directory)
    with pytest.raises(custody.SolarCustodyHold):
        with server._open('tenant-1', raw, False): pass
    assert not path.exists() and tree(server.directory) == before
