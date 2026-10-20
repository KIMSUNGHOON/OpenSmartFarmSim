"""Current SCRAM reads preserve original CO2 wires and reject late changes."""
from contextlib import contextmanager
from copy import deepcopy
from datetime import timedelta
from hashlib import sha256
import ctypes
import gc
import json
import os
from pathlib import Path
import subprocess
import sys

import psycopg
import pytest

from app import crop_greenhouse_co2_current_query as current
import test_crop_greenhouse_co2_result_store as registered
from test_api_crop_greenhouse_co2_replay_store import (authoring, profiles, login_database,
    original_login_scope, login_scope, setup, settle_owned_database_backends)

public = current.public
pytestmark = registered.pytestmark


def save(name, value):
    directory = os.environ.get('OSSF_JOINT_PREFIX_SDK_EVIDENCE')
    if directory:
        with (Path(directory)/('co2-current-query-'+name)).open('x') as output:
            os.fchmod(output.fileno(), 0o400)
            json.dump(value, output, sort_keys=True, indent=2)
            output.flush(); os.fsync(output.fileno())


@pytest.fixture(scope='module', autouse=True)
def cleanup(login_database):
    yield
    with psycopg.connect(login_database['admin']) as conn:
        schemas = conn.execute("SELECT count(*) FROM pg_namespace WHERE nspname LIKE 'login_test_%'").fetchone()[0]
        roles = conn.execute("SELECT count(*) FROM pg_roles WHERE rolname LIKE 'login_%'").fetchone()[0]
    assert schemas == roles == 0
    save('database-cleanup.json', {'schemas': schemas, 'roles': roles})


@pytest.fixture
def ready(setup):
    result, raw, value, done = registered.ready(setup)
    gc.collect(); ctypes.CDLL(None).malloc_trim(0)
    record = result.put('tenant-1', raw)
    return current.Co2CurrentQuery(result), record, raw, value, done


@contextmanager
def readonly(monkeypatch):
    execute = psycopg.Connection.execute; calls = {'SQL_writes': 0}
    def run(conn, query, *args, **kwargs):
        text = query.as_string(conn) if hasattr(query, 'as_string') else query
        if text.split(None, 1)[0].upper() in ('INSERT', 'UPDATE', 'DELETE', 'TRUNCATE', 'CREATE', 'ALTER', 'DROP', 'GRANT', 'REVOKE'):
            calls['SQL_writes'] += 1
            pytest.fail('current query attempted SQL mutation')
        return execute(conn, query, *args, **kwargs)
    with monkeypatch.context() as patch:
        patch.setattr(psycopg.Connection, 'execute', run)
        yield calls
    assert calls['SQL_writes'] == 0


def original_wires(query, record, farm):
    with query.store._read('tenant-1', record['result_id'], farm) as (row, packet, session):
        assert query.store._record(row) == record
        with current.artifact.open_artifact(session.path, packet['artifact']['sha256']) as reader:
            terminal = {**reader.summary, 'manifest': reader._context['manifest'],
                'time_binding': reader._header['binding']}
            pages = {kind: reader.page(kind) for kind in ('samples', 'events')}
            return {view: public._public_bytes(public.project_co2_result(record, terminal,
                source_program=reader._context['program'], view=view,
                page=None if view == 'summary' else pages[view],
                limit=None if view == 'summary' else 64 if view == 'samples' else 8))
                for view in ('summary', 'samples', 'events')}


FRESH_SCRIPT = '''import sys, json, traceback
def failure_location(kind,error,tb):
 chain=[];seen=set()
 while error is not None and id(error) not in seen and len(chain)<8:
  seen.add(id(error));chain.append({'type':type(error).__name__,'locations':[
   {'file':row.filename.rsplit('/',1)[-1],'line':row.lineno,'function':row.name}
   for row in traceback.extract_tb(error.__traceback__)]});error=error.__context__
 print(json.dumps({'exception_chain':chain}),file=sys.stderr)
sys.excepthook=failure_location
''' + registered.producer.FRESH_SETUP + '''
import os
from app import crop_greenhouse_co2_result_store as result_model
from app import crop_greenhouse_co2_current_query as current
result=result_model.Co2ResultStore(custody,integrity_key=b'owned-co2-result-store-key-32-bytes!')
query=current.Co2CurrentQuery(result);farm=p['body']['farm'];before=counts(service)
class Patch:
 def setattr(self,target,name,value):setattr(target,name,value)
calls=measured(Patch());calls['SQL_writes']=0;execute=psycopg.Connection.execute
def read_only(conn,sql,*args,**kwargs):
 text=sql.as_string(conn) if hasattr(sql,'as_string') else sql
 if text.split(None,1)[0].upper() in ('INSERT','UPDATE','DELETE','TRUNCATE','CREATE','ALTER','DROP','GRANT','REVOKE'):
  calls['SQL_writes']+=1;raise AssertionError('fresh current query attempted SQL mutation')
 return execute(conn,sql,*args,**kwargs)
psycopg.Connection.execute=read_only
fd=len(os.listdir('/proc/self/fd'));actual={}
for view in ('summary','samples','events'):
 wire=query.read('tenant-1',p['result_id'],farm,view=view)
 actual[view]=sha256(wire).hexdigest()
 assert json.loads(wire)['recorded_at']==p['recorded_at_public']
assert actual==p['response_sha256']
record=result.get('tenant-1',p['result_id'],farm)
assert record['recorded_at'].isoformat()==p['recorded_at']
assert sha256(record['payload_raw']).hexdigest()==p['payload_sha256']
assert sha256(record['progress_raw']).hexdigest()==p['expected_progress_sha256']
review['status']='revoked';rejected=[]
for view in ('summary','samples','events'):
 try:query.read('tenant-1',p['result_id'],farm,view=view)
 except current.Co2CurrentQueryHold:rejected.append(view)
 else:raise AssertionError('fresh current revoked review returned response')
assert len(rejected)==3 and all(value==0 for value in calls.values())
assert counts(service)==before and len(os.listdir('/proc/self/fd'))==fd
with jobs.connect() as conn:assert conn.pgconn.used_password and conn.info.get_parameters()['require_auth']=='scram-sha-256'
print(json.dumps({'actual_scram':True,'fresh_exec':True,'current_DB_authorization':True,
 'response_sha256':actual,'current_review_revocation_denied':rejected,'calls':calls,
 'FD_before_after':[fd,fd],'counts_unchanged':True,'original_recorded_at_and_bytes':True}))
'''


@pytest.mark.parametrize('setup', [pytest.param(None, id='normal'), pytest.param('hold', id='hold')], indirect=True)
def test_original_normal_hold_and_fresh_current_database(ready, tmp_path, monkeypatch):
    query, record, raw, value, done = ready; binding = query.store.server.binding; farm = value[1]['farm']
    expected = original_wires(query, record, farm); before = registered.producer.reference.counts(binding)
    rows = registered.count(binding); fd = len(os.listdir('/proc/self/fd'))
    calls = registered.producer.reference.forbid(monkeypatch)
    with readonly(monkeypatch) as sql_calls:
        actual = {view: query.read('tenant-1', record['result_id'], farm, view=view) for view in expected}
        assert actual == expected
        summary = json.loads(actual['summary']); progress = json.loads(done)
        assert summary['summary']['last_confirmed']['value'] == progress['last_confirmed']
        assert summary['summary']['last_confirmed']['time'] == progress['times']['last_confirmed']
        assert summary['reference']['failed_boundary'] == progress['times']['hold']
        assert query.store.get('tenant-1', record['result_id'], farm) == record
    hashes = {view: sha256(wire).hexdigest() for view, wire in actual.items()}
    path = registered.producer.fresh_pack(tmp_path, value, done, query.store.server)
    pack = json.loads(path.read_bytes()); pack.update(result_id=record['result_id'],
        payload_sha256=record['payload_sha256'], recorded_at=record['recorded_at'].isoformat(),
        recorded_at_public=summary['recorded_at'], response_sha256=hashes)
    path.write_text(json.dumps(pack)); path.chmod(0o600)
    gc.collect(); ctypes.CDLL(None).malloc_trim(0)
    child = subprocess.Popen([sys.executable, '-B', '-c', FRESH_SCRIPT, str(path)],
        stdin=subprocess.DEVNULL, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
        env=dict(os.environ, PYTHONPATH=registered.producer.FRESH_PYTHONPATH))
    stdout, stderr = child.communicate(timeout=100)
    if child.returncode:
        failure = {'stderr_sha256': sha256(stderr).hexdigest()}
        try: failure.update(json.loads(stderr))
        except (ValueError, TypeError): pass
        save('fresh-failure.json', failure)
    assert child.returncode == 0, 'fresh current query failed; stderr SHA '+sha256(stderr).hexdigest()
    fresh = json.loads(stdout); assert fresh['response_sha256'] == hashes
    assert all(value == 0 for value in fresh['calls'].values())
    assert registered.producer.reference.counts(binding) == before and registered.count(binding) == rows == 1
    assert len(os.listdir('/proc/self/fd')) == fd and all(value == 0 for value in calls.values())
    status = json.loads(done)['status']
    save(status+'.json', {'status': status, 'original_wires_equal': True, 'response_sha256': hashes,
        'original_counts': progress['counts'], 'original_recorded_at': summary['recorded_at'],
        'calls': {**calls, **sql_calls}, 'FD_before_after': [fd, fd], 'counts_unchanged': True,
        'registered_result_rows': rows, 'G0_G4': 'not_assessed'})
    save('fresh-'+status+'.json', {**fresh, 'actual_exit': child.returncode, 'G0_G4': 'not_assessed'})


@pytest.mark.parametrize('phase', ['projection', 'serialization'])
def test_early_and_late_rights_account_and_farm_source_revocation(ready, monkeypatch, phase):
    query, record, _, value, _ = ready; binding, body, packet, _, principal, rights = value; farm = body['farm']
    source = binding.farms.replay.candidates._source._source; get_rights = source.get_input_rights
    changes = [('input-rights', lambda: setattr(rights, 'allowed', False), lambda: setattr(rights, 'allowed', True)),
        ('review', lambda: packet[3].update(status='revoked'), lambda: packet[3].update(status='accepted_for_software_validation')),
        ('read-scope', lambda: principal['scopes'].remove('crop_result_read'), lambda: principal['scopes'].add('crop_result_read')),
        ('account', lambda: principal.update(authenticated=False), lambda: principal.update(authenticated=True)),
        ('farm-source', lambda: setattr(source, 'get_input_rights', lambda *_: None), lambda: setattr(source, 'get_input_rights', get_rights))]
    before = registered.producer.reference.counts(binding); fd = len(os.listdir('/proc/self/fd'))
    calls = registered.producer.reference.forbid(monkeypatch); serialize = public._public_bytes; rejected = []
    with readonly(monkeypatch) as sql_calls:
        for name, withdraw, restore in changes:
            for view in ('summary', 'samples', 'events'):
                withdraw()
                try:
                    with pytest.raises((current.Co2CurrentQueryHold, PermissionError)):
                        query.read('tenant-1', record['result_id'], farm, view=view)
                finally: restore()
                observed = []
                def serialized(value):
                    wire = serialize(value); observed.append(1)
                    if len(observed) == (1 if phase == 'projection' else 2): withdraw()
                    return wire
                try:
                    with monkeypatch.context() as patch:
                        patch.setattr(public, '_public_bytes', serialized)
                        with pytest.raises((current.Co2CurrentQueryHold, PermissionError)):
                            query.read('tenant-1', record['result_id'], farm, view=view)
                    assert len(observed) >= (1 if phase == 'projection' else 2)
                finally: restore()
                rejected.append(name+':'+view)
        assert query.store.get('tenant-1', record['result_id'], farm) == record
    assert registered.producer.reference.counts(binding) == before and all(value == 0 for value in calls.values())
    assert len(os.listdir('/proc/self/fd')) == fd
    save('rights-'+phase+'.json', {'phase': phase, 'early_denied': 15, 'late_denied': 15,
        'rejected': rejected, 'calls': {**calls, **sql_calls}, 'counts_unchanged': True, 'FD_before_after': [fd, fd]})


def test_late_database_record_page_and_selected_HEAD_tampering(ready, monkeypatch):
    query, record, raw, value, _ = ready; farm = value[1]['farm']; store = query.store
    before = registered.producer.reference.counts(store.server.binding); fd = len(os.listdir('/proc/self/fd'))
    calls = registered.producer.reference.forbid(monkeypatch); serialize = public._public_bytes; find = store._find
    rejected = []
    with readonly(monkeypatch) as sql_calls:
        for kind in ('signature', 'column', 'recorded-at', 'missing', 'progress-bytes', 'progress-hash', 'provenance', 'custody-code'):
            flag = []; observed = []
            def serialized(value):
                wire = serialize(value); observed.append(1)
                if len(observed) == 2: flag.append(True)
                return wire
            def lookup(*args, **kwargs):
                row = find(*args, **kwargs)
                if not flag: return row
                if kind == 'missing': return None
                row = deepcopy(row)
                if kind == 'signature': row['integrity_signature'] = '0'*64
                elif kind == 'column': row['steps'] -= 1
                elif kind == 'progress-bytes': row['progress_raw'] += b' '
                elif kind == 'progress-hash': row['progress_sha256'] = '0'*64
                elif kind == 'provenance': row['provenance_sha256'] = '0'*64
                elif kind == 'custody-code': row['custody_code_sha256'] = '0'*64
                else: row['recorded_at'] += timedelta(microseconds=1)
                return row
            with monkeypatch.context() as patch:
                patch.setattr(public, '_public_bytes', serialized); patch.setattr(store, '_find', lookup)
                with pytest.raises(current.Co2CurrentQueryHold): query.read('tenant-1', record['result_id'], farm)
            assert flag; rejected.append(kind)
        _, directory, _ = registered.producer.locations(store.server, raw)
        with current.artifact.open_artifact(directory, json.loads(record['payload_raw'])['artifact']['sha256']) as reader:
            digest = reader._index['samples'][0]['sha256']
        pages = list(directory.rglob(digest+'.json')); assert len(pages) == 1
        for kind, path, view in [('page', pages[0], 'samples'), ('HEAD', directory/'HEAD', 'summary')]:
            saved = path.read_bytes(); mode = path.stat().st_mode & 0o777; observed = []
            def corrupted(value):
                wire = serialize(value); observed.append(1)
                if len(observed) == 2:
                    path.chmod(0o600); path.write_bytes(saved+b' '); path.chmod(mode)
                return wire
            try:
                with monkeypatch.context() as patch:
                    patch.setattr(public, '_public_bytes', corrupted)
                    with pytest.raises(current.Co2CurrentQueryHold): query.read('tenant-1', record['result_id'], farm, view=view)
                assert len(observed) == 2; rejected.append(kind)
            finally:
                path.chmod(0o600); path.write_bytes(saved); path.chmod(mode)
        assert query.store.get('tenant-1', record['result_id'], farm) == record
    assert registered.producer.reference.counts(store.server.binding) == before
    assert all(value == 0 for value in calls.values()) and len(os.listdir('/proc/self/fd')) == fd
    save('tamper.json', {'late_tamper_denied': rejected, 'DB_mutation_is_lookup_fault_injection': True,
        'page_and_HEAD_tamper_actual_owned_files': True, 'calls': {**calls, **sql_calls},
        'counts_unchanged': True, 'FD_before_after': [fd, fd]})


def test_closed_queries_page_end_busy_and_changed_assembly(ready, monkeypatch):
    query, record, raw, value, done = ready; farm = value[1]['farm']; before = registered.producer.reference.counts(query.store.server.binding)
    calls = registered.producer.reference.forbid(monkeypatch); fd = len(os.listdir('/proc/self/fd'))
    bad = [{'view': True}, {'view': 'other'}, {'offset': True}, {'offset': 1}, {'limit': 1},
        {'view': 'samples', 'offset': -1}, {'view': 'samples', 'offset': 513}, {'view': 'events', 'offset': 129},
        {'view': 'samples', 'limit': True}, {'view': 'samples', 'limit': 0}, {'view': 'samples', 'limit': 65}, {'view': 'events', 'limit': 9}]
    with readonly(monkeypatch) as sql_calls:
        for args in bad:
            with pytest.raises(current.Co2CurrentQueryHold): query.read('tenant-1', record['result_id'], farm, **args)
        for changed in (None, {**farm, 'extra': 1}, {**farm, 'registration_sha256': 'bad'}, {**farm, 'crop_id': 'other-crop'}):
            with pytest.raises(current.Co2CurrentQueryHold): query.read('tenant-1', record['result_id'], changed)
        assert query.read('tenant-1', current.storage.VERSION+':'+'0'*64, farm) is None
        with pytest.raises(PermissionError): query.read('foreign', record['result_id'], farm)
        with pytest.raises(current.Co2CurrentQueryHold): query.read('tenant-1', 'joint-solar-result-v1:'+'0'*64, farm)
        assert json.loads(query.read('tenant-1', record['result_id'], farm, view='samples', offset=1, limit=1))['page']['next_offset'] == 2
        end = json.loads(done)['counts']['samples']
        assert json.loads(query.read('tenant-1', record['result_id'], farm, view='samples', offset=end))['page']['records'] == []
        with monkeypatch.context() as patch:
            patch.setattr(query, 'store', object())
            with pytest.raises(current.Co2CurrentQueryHold): query.read('tenant-1', record['result_id'], farm)
        with monkeypatch.context() as patch:
            patch.setattr(current, 'VERSION', 'changed')
            with pytest.raises(current.Co2CurrentQueryHold): query.read('tenant-1', record['result_id'], farm)
        serialize = public._public_bytes; observed = []
        def oversized(value):
            wire = serialize(value); observed.append(1)
            return b'x'*(public.MAX_RESPONSE_BYTES+1) if len(observed) == 2 else wire
        with monkeypatch.context() as patch:
            patch.setattr(public, '_public_bytes', oversized)
            with pytest.raises(current.Co2CurrentQueryHold): query.read('tenant-1', record['result_id'], farm)
        assert len(observed) == 2
        changed = deepcopy(farm); observed = []
        def changed_farm(value):
            wire = serialize(value); observed.append(1)
            if len(observed) == 2: changed['crop_id'] = 'changed-during-serialization'
            return wire
        with monkeypatch.context() as patch:
            patch.setattr(public, '_public_bytes', changed_farm)
            with pytest.raises(current.Co2CurrentQueryHold): query.read('tenant-1', record['result_id'], changed)
        root_fd = current.server.files.job_store._open_directory_nofollow(query.store.server.directory)
        lock = current.server.files._file(root_fd, '.custody-lock', lock=True)
        try:
            with pytest.raises(current.server.Co2CustodyPending): query.read('tenant-1', record['result_id'], farm)
        finally:
            os.close(lock); os.close(root_fd)
    assert registered.producer.reference.counts(query.store.server.binding) == before
    assert all(value == 0 for value in calls.values()) and len(os.listdir('/proc/self/fd')) == fd
    save('edges.json', {'invalid_queries': len(bad), 'invalid_farms': 4, 'missing_is_None': True,
        'foreign_family_tenant_and_changed_assembly_denied': True, 'page_end_and_cursor': True,
        'response_2MiB_and_changed_farm_denied': True, 'busy_propagated': True,
        'calls': {**calls, **sql_calls}, 'counts_unchanged': True, 'FD_before_after': [fd, fd]})
