"""Same-session SCRAM reads, original wires, late withdrawals and tampering."""
from copy import deepcopy
from datetime import timedelta
from hashlib import sha256
import json
import os
from pathlib import Path
import subprocess
import sys
from time import monotonic

import pytest

from app import crop_climate_joint_current_query as current
import test_crop_climate_joint_result_store as registered
from test_crop_climate_joint_result_store import login_database, original_login_scope, login_scope, authoring, farm_setup, setup
from test_api_crop_climate_joint_replay import database_cleanup

profiles = registered.profiles
public = current.public


def save(name, value):
    directory = os.environ.get('OSSF_JOINT_CURRENT_QUERY_EVIDENCE')
    if directory:
        with (Path(directory)/name).open('x') as f:
            os.fchmod(f.fileno(), 0o400); json.dump(value, f, sort_keys=True, indent=2); f.flush(); os.fsync(f.fileno())


@pytest.fixture
def ready(setup, database_cleanup):
    result, raw, value, done = registered.ready(setup)
    record = result.put('tenant-1', raw)
    return current.JointCropClimateCurrentQuery(result), record, raw, value, done


@pytest.mark.parametrize('store', [None, False, object(), current.storage.JointCropClimateResultStore.__new__(current.storage.JointCropClimateResultStore)])
def test_exact_initialized_store_required(store):
    with pytest.raises(current.JointCurrentQueryHold): current.JointCropClimateCurrentQuery(store)


FRESH_SCRIPT = registered.producer.reference.FRESH_SCRIPT.split('calls={')[0] + '''
import test_crop_climate_joint_result_store as u
from app import crop_climate_joint_current_query as q
from pytest import MonkeyPatch
packet=(Path(p['directory']),p['body']['input']['source_sha256'],None,review)
resolver=u.producer.Resolver(packet,Path(p['proof']).read_bytes())
custody=u.producer.model.JointServerCustody(service,p['custody'],input_resolver=resolver,integrity_key=u.producer.KEY)
store=u.store.JointCropClimateResultStore(custody,integrity_key=u.KEY);query=q.JointCropClimateCurrentQuery(store)
before=t.counts(service)
with MonkeyPatch.context() as patch:
 calls=t.forbid(patch)
 responses={k:u.sha256(query.read('tenant-1',p['result_id'],p['body']['farm'],view=k)).hexdigest() for k in ('summary','samples','events')}
 assert responses==p['responses']
 review['status']='revoked'
 try:query.read('tenant-1',p['result_id'],p['body']['farm'])
 except q.JointCurrentQueryHold:pass
 else:raise AssertionError('fresh revoked source allowed')
 assert all(n==0 for n in calls.values()) and t.counts(service)==before
with jobs.connect() as conn:assert conn.pgconn.used_password and conn.info.get_parameters()['require_auth']=='scram-sha-256'
print(json.dumps({'PID':__import__('os').getpid(),'actual_scram':True,'response_sha256':responses,'calls':calls,'revoked_review_denied':True,'counts_unchanged':True}))
'''


def original_wires(query, record, farm):
    terminal = query.store.summary('tenant-1', record['result_id'], farm)
    pages = {k: query.store.page('tenant-1', record['result_id'], farm, k) for k in ('samples', 'events')}
    return {k: public._public_bytes(public.project_joint_result(record, terminal, view=k,
        page=None if k == 'summary' else pages[k], limit=None if k == 'summary' else 64 if k == 'samples' else 8))
        for k in ('summary', 'samples', 'events')}


LOGIN = pytest.mark.parametrize('original_login_scope', [{'market_calculation': True, 'market_source_storage': True,
    'thermal_scenario_storage': True, 'break_even_calculation': True, 'crop_cycle_result_storage': True}], indirect=True)


@LOGIN
def test_normal_original_wires_same_session_and_fresh_scram(ready, tmp_path, monkeypatch):
    query, record, raw, value, done = ready; farm = value[1]['farm']; before = registered.producer.reference.counts(query.store.server.binding)
    calls = registered.producer.reference.forbid(monkeypatch); expected = original_wires(query, record, farm)
    fd = len(os.listdir('/proc/self/fd')); timings = {}; responses = {}
    for view in expected:
        start = monotonic(); wire = query.read('tenant-1', record['result_id'], farm, view=view)
        timings[view] = monotonic()-start; assert wire == expected[view]
        responses[view] = {'bytes': len(wire), 'sha256': sha256(wire).hexdigest()}
        assert json.loads(wire)['reference']['G0_G4'] == 'not_assessed'
    path = registered.producer.fresh_pack(tmp_path, value, done, query.store.server); packed = json.loads(path.read_bytes())
    packed.update(result_id=record['result_id'], responses={k: v['sha256'] for k, v in responses.items()}); path.write_text(json.dumps(packed))
    child = subprocess.run([sys.executable, '-B', '-c', FRESH_SCRIPT, str(path)], stdin=subprocess.DEVNULL,
        capture_output=True, timeout=70, env=dict(os.environ, PYTHONPATH=registered.producer.FRESH_PYTHONPATH))
    assert child.returncode == 0, child.stderr.decode(); fresh = json.loads(child.stdout)
    assert not Path('/proc', str(fresh['PID'])).exists()
    assert query.store.get('tenant-1', record['result_id'], farm) == record
    assert registered.producer.reference.counts(query.store.server.binding) == before and registered.count(query.store.server.binding) == 1
    assert all(n == 0 for n in calls.values()) and len(os.listdir('/proc/self/fd')) == fd
    save('normal.json', {'responses': responses, 'query_seconds': timings, 'fresh': fresh,
        'original_wires_equal': True, 'calls': calls, 'counts_unchanged': True, 'FD_before_after': [fd, fd], 'G0_G4': 'not_assessed'})


@LOGIN
@pytest.mark.parametrize('setup', ['hold'], indirect=True)
def test_hold_preserves_original_last_confirmed_failure_boundary_and_pages(ready, monkeypatch):
    query, record, _, value, done = ready; farm = value[1]['farm']; calls = registered.producer.reference.forbid(monkeypatch)
    expected = original_wires(query, record, farm); before = registered.producer.reference.counts(query.store.server.binding)
    actual = {k: query.read('tenant-1', record['result_id'], farm, view=k) for k in expected}; assert actual == expected
    summary = json.loads(actual['summary']); progress = json.loads(done)
    assert summary['summary']['last_confirmed']['value'] == progress['last_confirmed'] and summary['summary']['checkpoint_sha256'] is None
    assert summary['summary']['hold']['time'] == progress['times']['hold']
    for view in ('samples', 'events'):
        assert all(r['time']['step_index'] < progress['hold']['step_index'] for r in json.loads(actual[view])['page']['records'])
    assert registered.producer.reference.counts(query.store.server.binding) == before and all(n == 0 for n in calls.values())
    save('hold.json', {'original_wires_equal': True, 'original_last_confirmed_and_failure_prefix': True,
        'response_sha256': {k: sha256(v).hexdigest() for k, v in actual.items()}, 'calls': calls, 'counts_unchanged': True})


@LOGIN
@pytest.mark.parametrize('phase', ['projection', 'serialization'])
def test_current_and_late_revocations_withhold_every_view(ready, monkeypatch, phase):
    query, record, _, value, _ = ready; binding, body, packet, _, principal, rights = value; farm = body['farm']
    source = binding.farms.replay.candidates._source._source; get_rights = source.get_input_rights
    changes = [('input-rights', lambda: setattr(rights, 'allowed', False), lambda: setattr(rights, 'allowed', True)),
        ('review', lambda: packet[3].update(status='revoked'), lambda: packet[3].update(status='accepted_for_software_validation')),
        ('read-scope', lambda: principal['scopes'].remove('crop_result_read'), lambda: principal['scopes'].add('crop_result_read')),
        ('farm-source', lambda: setattr(source, 'get_input_rights', lambda *_: None), lambda: setattr(source, 'get_input_rights', get_rights))]
    calls = registered.producer.reference.forbid(monkeypatch); before = registered.producer.reference.counts(binding); original = public._public_bytes; rejected = []
    for name, withdraw, restore in changes:
        for view in ('summary', 'samples', 'events'):
            withdraw()
            try:
                with pytest.raises((current.JointCurrentQueryHold, PermissionError)): query.read('tenant-1', record['result_id'], farm, view=view)
            finally: restore()
            observed = []
            def serialized(model):
                wire = original(model); observed.append(len(wire))
                if len(observed) == (1 if phase == 'projection' else 2): withdraw()
                return wire
            try:
                with monkeypatch.context() as patch:
                    patch.setattr(public, '_public_bytes', serialized)
                    with pytest.raises((current.JointCurrentQueryHold, PermissionError)): query.read('tenant-1', record['result_id'], farm, view=view)
                assert len(observed) >= (1 if phase == 'projection' else 2)
            finally: restore()
            rejected.append(name+':'+view)
    assert query.store.get('tenant-1', record['result_id'], farm) == record
    assert registered.producer.reference.counts(binding) == before and all(n == 0 for n in calls.values())
    save('rights-'+phase+'.json', {'early_denied': 12, 'late_denied': 12, 'rejected': rejected,
        'phase': phase, 'calls': calls, 'counts_unchanged': True})


@LOGIN
def test_after_serialization_DB_record_signature_columns_and_original_page_tamper(ready, monkeypatch):
    query, record, raw, value, _ = ready; farm = value[1]['farm']; store = query.store
    calls = registered.producer.reference.forbid(monkeypatch); before = registered.producer.reference.counts(store.server.binding)
    original = public._public_bytes; find = store._find; rejected = []
    for kind in ('signature', 'column', 'recorded-at', 'missing'):
        flag = []; serialization = []
        def serialized(model):
            wire = original(model); serialization.append(1)
            if len(serialization) == 2: flag.append(True)
            return wire
        def lookup(*args, **kw):
            row = find(*args, **kw)
            if not flag: return row
            if kind == 'missing': return None
            row = deepcopy(row)
            if kind == 'signature': row['integrity_signature'] = '0'*64
            elif kind == 'column': row['steps'] -= 1
            else: row['recorded_at'] += timedelta(microseconds=1)
            return row
        with monkeypatch.context() as patch:
            patch.setattr(public, '_public_bytes', serialized); patch.setattr(store, '_find', lookup)
            with pytest.raises(current.JointCurrentQueryHold): query.read('tenant-1', record['result_id'], farm)
        assert flag; rejected.append(kind)
    _, directory, _ = registered.producer.locations(store.server, raw)
    with current.artifact.open_artifact(directory, json.loads(record['payload_raw'])['artifact']['sha256']) as reader:
        digest = reader._index['samples'][0]['sha256']
    blobs = list(directory.rglob(digest+'.json'))
    assert len(blobs) == 1; blob = blobs[0]; saved = blob.read_bytes(); mode = blob.stat().st_mode & 0o777; observed = []
    def tampered(model):
        wire = original(model); observed.append(1)
        if len(observed) == 2:
            blob.chmod(0o600); blob.write_bytes(saved+b' '); blob.chmod(mode)
        return wire
    try:
        with monkeypatch.context() as patch:
            patch.setattr(public, '_public_bytes', tampered)
            with pytest.raises(current.JointCurrentQueryHold): query.read('tenant-1', record['result_id'], farm, view='samples')
        assert len(observed) == 2; rejected.append('original-page-after-serialization')
    finally:
        blob.chmod(0o600); blob.write_bytes(saved); blob.chmod(mode)
    assert registered.producer.reference.counts(store.server.binding) == before and all(n == 0 for n in calls.values())
    save('tamper.json', {'late_tamper_rejected': rejected, 'DB_mutations_are_lookup_fault_injection': True,
        'page_tamper_is_actual_owned_file': True, 'calls': calls, 'counts_unchanged': True})


@LOGIN
def test_bounds_missing_foreign_farm_and_changed_assembly(ready, monkeypatch):
    query, record, _, value, _ = ready; farm = value[1]['farm']; calls = registered.producer.reference.forbid(monkeypatch)
    bad = [{'view': True}, {'view': 'other'}, {'offset': True}, {'offset': 1}, {'limit': 1},
        {'view': 'samples', 'offset': -1}, {'view': 'samples', 'offset': 513}, {'view': 'events', 'offset': 129},
        {'view': 'samples', 'limit': True}, {'view': 'samples', 'limit': 0}, {'view': 'samples', 'limit': 65}, {'view': 'events', 'limit': 9}]
    for args in bad:
        with pytest.raises(current.JointCurrentQueryHold): query.read('tenant-1', record['result_id'], farm, **args)
    for changed in (None, {**farm, 'extra': 1}, {**farm, 'registration_sha256': 'bad'}, {**farm, 'crop_id': 'other-crop'}):
        with pytest.raises(current.JointCurrentQueryHold): query.read('tenant-1', record['result_id'], changed)
    assert query.read('tenant-1', current.storage.VERSION+':'+'0'*64, farm) is None
    with pytest.raises(PermissionError): query.read('foreign', record['result_id'], farm)
    first = query.read('tenant-1', record['result_id'], farm, view='samples', offset=1, limit=1)
    assert json.loads(first)['page']['next_offset'] == 2
    assert json.loads(query.read('tenant-1', record['result_id'], farm, view='samples', offset=3))['page']['records'] == []
    with monkeypatch.context() as patch:
        patch.setattr(query, 'store', object())
        with pytest.raises(current.JointCurrentQueryHold): query.read('tenant-1', record['result_id'], farm)
    original = public._public_bytes; observed = []
    def oversized(model):
        wire = original(model); observed.append(1)
        return b'x'*(public.MAX_RESPONSE_BYTES+1) if len(observed) == 2 else wire
    with monkeypatch.context() as patch:
        patch.setattr(public, '_public_bytes', oversized)
        with pytest.raises(current.JointCurrentQueryHold): query.read('tenant-1', record['result_id'], farm)
    assert len(observed) == 2 and all(n == 0 for n in calls.values())
    save('edges.json', {'invalid_queries': len(bad), 'invalid_or_foreign_farms': 4, 'missing_is_None': True,
        'foreign_tenant_and_changed_store_denied': True, 'page_end_and_cursor': True, 'serialized_2MiB_enforced': True, 'calls': calls})
