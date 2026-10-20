"""Observe actual checkpoint consumers; explicit SCRAM diagnostic, not a benchmark."""
from hashlib import sha256
import json
from pathlib import Path
import sys

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT / 'backend'), str(ROOT / 'backend/tests')]
from app import crop_greenhouse_solar_execution_checkpoint as checkpoints
from test_crop_greenhouse_solar_execution_query import (
    worker_setup, producer_setup, authoring, profiles, login_database,
    original_login_scope, login_scope, query_cleanup, save)
import test_crop_greenhouse_solar_execution_worker as reference

pytestmark = [reference.pytestmark, pytest.mark.usefixtures('query_cleanup')]
custody = checkpoints.custody
storage = custody.storage


def checkpoint_rows(worker, job_id):
    return [row for row in reference.rows(worker, job_id, 'job_events')
            if row['kind'] == checkpoints.EVENT_KIND]


def page_path(worker, raw):
    _, artifact, _ = reference.producer.locations(worker.server, raw)
    head = json.loads((artifact / 'HEAD').read_bytes())
    digest = head['latest_commit_sha256']
    while digest:
        commit = json.loads((artifact / (digest + '.json')).read_bytes())
        for descriptors in commit['pages'].values():
            if descriptors:
                return artifact, artifact / (descriptors[0]['sha256'] + '.json')
        digest = commit['parent_commit_sha256']
    raise AssertionError('diagnostic requires an actual stored page')


def test_actual_confirm_consumers_and_same_head_late_tampering(worker_setup, monkeypatch):
    worker, job_id, raw, fixture = worker_setup
    lease = worker.jobs.claim(600, allowed_stages=('simulation',),
                              tenant_id='tenant-1', job_id=job_id)
    assert lease
    worker.server._advance_for_checkpoint('tenant-1', raw, budget=1)
    worker.server._advance_for_checkpoint('tenant-1', raw, budget=1)
    expected = json.loads(worker.server.inspect('tenant-1', raw))
    trace, reads, snapshots, transports, reconstructions = [], [], [], [], []
    farms = worker.server.binding.farms
    original_prepare = farms._prepare
    original_load = custody._Session._load
    original_storage_load = storage._Files._load
    original_progress = custody._Session.progress
    original_snapshot = checkpoints.SolarExecutionCheckpointStore._snapshot
    original_current = checkpoints.SolarExecutionCheckpointStore._current
    original_lease = checkpoints.SolarExecutionCheckpointStore._lease
    original_history = checkpoints.SolarExecutionCheckpointStore._history
    original_descendant = checkpoints.SolarExecutionCheckpointStore._descendant

    def loading(session):
        trace.append('session.load')
        value = original_load(session)
        data = value[2]
        assert type(data) is tuple and len(data) == 8
        assert set(data[7]) == {'samples', 'events'}
        reads.append({'tuple_slots': len(data), 'commit_count': len(data[2]),
            'checkpoint_value_present': data[3] is not None and 'value' in data[3],
            'counts': data[7].copy(), 'head_sha256': value[1]})
        return value

    def storage_loading(handle, head):
        trace.append('storage.load')
        return original_storage_load(handle, head)

    def progress(session):
        trace.append('progress.begin')
        value = original_progress(session)
        transports.append(value)
        trace.append('progress.end')
        return value

    def snapshot(store, *args):
        trace.append('snapshot.begin')
        value = original_snapshot(store, *args)
        snapshots.append(value)
        trace.append('snapshot.end')
        return value

    def current(store, *args):
        trace.append('current.begin')
        value = original_current(store, *args)
        trace.append('current.end')
        return value

    def leasing(store, *args, **kwargs):
        trace.append('lease.locked' if kwargs.get('lock', True) else 'lease.unlocked')
        return original_lease(store, *args, **kwargs)

    def history(store, *args):
        trace.append('history')
        return original_history(store, *args)

    def descendant(store, *args):
        trace.append('descendant')
        return original_descendant(store, *args)

    def prepare(*args, **kwargs):
        owner = farms._registration_read.get()
        assert owner is not None and owner.active
        reconstructions.append(owner)
        return original_prepare(*args, **kwargs)

    with monkeypatch.context() as patch:
        forbidden = reference.producer.reference.forbid(patch)
        patch.setattr(custody._Session, '_load', loading)
        patch.setattr(storage._Files, '_load', storage_loading)
        patch.setattr(custody._Session, 'progress', progress)
        patch.setattr(farms, '_prepare', prepare)
        for name, method in (('_snapshot', snapshot), ('_current', current),
                             ('_lease', leasing), ('_history', history),
                             ('_descendant', descendant)):
            patch.setattr(checkpoints.SolarExecutionCheckpointStore, name, method)
        result = worker._confirm(lease)
        assert all(value == 0 for value in forbidden.values())
    assert trace == [
        'lease.unlocked', 'current.begin', 'current.end',
        'progress.begin', 'session.load', 'storage.load', 'progress.end', 'history',
        'snapshot.begin', 'session.load', 'storage.load', 'snapshot.end', 'descendant',
        'lease.unlocked', 'current.begin', 'current.end',
        'progress.begin', 'session.load', 'storage.load', 'progress.end',
        'lease.locked', 'history']
    assert len(reads) == 3 and reads[0] == reads[1] == reads[2]
    assert len(transports) == 2 and transports[0] == transports[1]
    assert len(reconstructions) == 2 and reconstructions[0] is not reconstructions[1]
    assert all(not owner.active for owner in reconstructions)
    packet, _ = snapshots[0]
    assert result['checkpoint'] == packet and set(packet) == checkpoints._FIELDS
    assert not {'value', 'checkpoint', 'last_confirmed', 'times', 'hold'} & set(packet)
    assert packet['rights_or_gate_approval'] is False and packet['G0_G4'] == 'not_assessed'
    assert packet['steps'] == expected['steps'] == 1
    assert packet['counts'] == expected['counts']
    assert packet['computed_through_utc'] == expected['times']['last_confirmed']['at']
    failures = []
    for phase in ('snapshot', 'final_progress'):
        worker.server._advance_for_checkpoint('tenant-1', raw, budget=1)
        artifact, path = page_path(worker, raw)
        head_before = (artifact / 'HEAD').read_bytes()
        original_page = path.read_bytes()
        events_before = checkpoint_rows(worker, job_id)
        injected, progress_calls = [], []

        def tamper():
            assert not injected
            path.chmod(0o600)
            path.write_bytes(original_page + b' ')
            path.chmod(0o400)
            injected.append(True)
            assert (artifact / 'HEAD').read_bytes() == head_before

        def late_snapshot(store, *args):
            if phase == 'snapshot': tamper()
            return original_snapshot(store, *args)

        def late_progress(session):
            progress_calls.append(True)
            if phase == 'final_progress' and len(progress_calls) == 2: tamper()
            return original_progress(session)

        try:
            with monkeypatch.context() as patch:
                forbidden = reference.producer.reference.forbid(patch)
                patch.setattr(checkpoints.SolarExecutionCheckpointStore, '_snapshot', late_snapshot)
                patch.setattr(custody._Session, 'progress', late_progress)
                with pytest.raises(checkpoints.SolarCheckpointHold):
                    worker._confirm(lease)
                assert injected and all(value == 0 for value in forbidden.values())
            assert checkpoint_rows(worker, job_id) == events_before
            assert (artifact / 'HEAD').read_bytes() == head_before
            failures.append({'phase': phase, 'same_HEAD': True, 'held': True,
                'checkpoint_events_unchanged': True, 'new_numerics': 0})
        finally:
            path.chmod(0o600)
            path.write_bytes(original_page)
            path.chmod(0o400)
        restored = worker._confirm(lease)
        assert len(checkpoint_rows(worker, job_id)) == len(events_before) + 1
        assert restored['checkpoint']['head_sha256'] == sha256(head_before).hexdigest()
    assert reference.rows(worker, job_id, 'job_publications') == []
    save('checkpoint-consumer-observation', {'scope': 'synthetic_software_diagnostic_only',
        'trace': trace, 'fresh_loads': reads, 'transport_bytes': len(transports[0]),
        'packet_bytes': len(custody._canonical(packet)), 'packet_fields': sorted(packet),
        'confirm_registration_reconstructions': len(reconstructions),
        'separate_registration_owners': True, 'registration_owners_closed': True,
        'numerical_checkpoint_absent_from_packet': True, 'rights_or_gate_approval': False,
        'original_computed_through_utc': packet['computed_through_utc'],
        'same_HEAD_tampering': failures, 'restored_after_each': True,
        'production_changed': False, 'normal64_accepted': False})
