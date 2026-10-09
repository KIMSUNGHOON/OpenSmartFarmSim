"""Real SCRAM registration, immutable source reads and current rights, without claims."""
from contextlib import contextmanager
from copy import deepcopy
from dataclasses import replace
from hashlib import sha256
import hmac
import json
import os
from pathlib import Path
import subprocess
import sys

from psycopg import sql
import psycopg
import pytest

from app import crop_climate_joint_result_store as store
from app import crop_climate_joint_result_schema as schema
from app.runtime_roles import audit_runtime_roles
from login_database import login_database, login_scope as original_login_scope
from test_farm_authoring_storage import authoring
from test_farm_replay_scenario import farm_setup
from test_crop_climate_joint_server_custody import setup, profiles
import test_crop_climate_joint_server_custody as producer

KEY = b'owned-joint-result-store-key-32-bytes!'
pytestmark = pytest.mark.parametrize('original_login_scope', [{'market_calculation': True,
    'market_source_storage': True, 'thermal_scenario_storage': True, 'break_even_calculation': True,
    'crop_cycle_result_storage': True}], indirect=True)


def save(name, value):
    root = os.environ.get('OSSF_JOINT_RESULT_EVIDENCE')
    if root:
        with (Path(root)/name).open('x') as f:
            os.fchmod(f.fileno(), 0o400); json.dump(value, f, sort_keys=True, indent=2)
            f.flush(); os.fsync(f.fileno())


@pytest.fixture
def login_scope(original_login_scope, request):
    base, policy, dsns = original_login_scope
    current = replace(policy, crop_climate_joint_result_storage=getattr(request, 'param', True))
    with base.connect() as conn:
        conn.execute(sql.SQL('SET LOCAL ROLE {}').format(sql.Identifier(policy.owner)))
        schema.install_joint_crop_climate_result_schema(conn, policy.schema)
        if current.crop_climate_joint_result_storage:
            conn.execute(sql.SQL('GRANT SELECT,INSERT ON {} TO {}').format(
                sql.Identifier(policy.schema, schema.TABLE), sql.Identifier(policy.roles['authority'])))
    with base.connect() as conn: audit_runtime_roles(conn, current)
    return base, current, dsns


@pytest.fixture(scope='module', autouse=True)
def cleanup(login_database):
    yield
    with psycopg.connect(login_database['admin']) as conn:
        schemas = conn.execute("SELECT count(*) FROM pg_namespace WHERE nspname LIKE 'login_test_%'").fetchone()[0]
        roles = conn.execute("SELECT count(*) FROM pg_roles WHERE rolname LIKE 'login_%'").fetchone()[0]
    save('database-cleanup.json', {'schemas': schemas, 'roles': roles}); assert schemas == roles == 0


def count(binding):
    with binding.jobs.connect() as conn:
        return conn.execute(sql.SQL('SELECT count(*) AS n FROM {}').format(
            binding.jobs._table(schema.TABLE))).fetchone()['n']


def ready(setup):
    custody, raw, value = setup
    done = custody.advance('tenant-1', raw, budget=128)
    return store.JointCropClimateResultStore(custody, integrity_key=KEY), raw, value, done


FRESH_SCRIPT = producer.reference.FRESH_SCRIPT.split('calls={')[0] + '''
import test_crop_climate_joint_result_store as u
from pytest import MonkeyPatch
packet=(Path(p['directory']),p['body']['input']['source_sha256'],None,review)
resolver=u.producer.Resolver(packet,Path(p['proof']).read_bytes())
custody=u.producer.model.JointServerCustody(service,p['custody'],input_resolver=resolver,integrity_key=u.producer.KEY)
result=u.store.JointCropClimateResultStore(custody,integrity_key=u.KEY)
raw=t._canonical(p['body']);farm=p['body']['farm'];before=t.counts(service)
with MonkeyPatch.context() as patch:
 calls=t.forbid(patch)
 record=result.get('tenant-1',p['result_id'],farm)
 assert record['payload_sha256']==p['payload_sha256'] and record['recorded_at'].isoformat()==p['recorded_at']
 assert u.sha256(record['payload_raw']).hexdigest()==p['payload_sha256']
 pages={k:result.page('tenant-1',p['result_id'],farm,k) for k in ('samples','events')}
 assert {k:u.sha256(t._canonical(v)).hexdigest() for k,v in pages.items()}==p['page_hashes']
 summary=result.summary('tenant-1',p['result_id'],farm)
 assert u.sha256(t._canonical(summary)).hexdigest()==p['summary_sha256']
 review['status']='revoked'
 try:result.get('tenant-1',p['result_id'],farm)
 except u.producer.model.JointCustodyHold:pass
 else:raise AssertionError('fresh revoked input review allowed')
 assert all(v==0 for v in calls.values())
with jobs.connect() as conn:assert conn.pgconn.used_password and conn.info.get_parameters()['require_auth']=='scram-sha-256'
assert t.counts(service)==before
print(json.dumps({'calls':calls,'actual_scram':True,'review_revocation_rejected':True,'original_bytes_pages_UTC':True,'PID':__import__('os').getpid()}))
'''


def test_original_signed_result_retry_pages_summary_and_fresh_scram(setup, tmp_path, monkeypatch):
    result, raw, value, done = ready(setup); custody = result.server; farm = json.loads(raw)['farm']
    expected = {k: custody.page('tenant-1', raw, done, k) for k in ('samples', 'events')}
    before = producer.reference.counts(custody.binding); fd = len(os.listdir('/proc/self/fd'))
    calls = producer.reference.forbid(monkeypatch)
    first = result.put('tenant-1', raw); packet = json.loads(first['payload_raw'])
    assert packet['policies']['server_progress'] == json.loads(done)
    assert packet['artifact']['status'] == 'completed' and packet['artifact']['steps'] == 16
    assert packet['input']['start_utc'] == '2026-10-01T00:00:00.123456Z'
    assert packet['input']['end_utc'] == '2026-10-01T00:00:32.123456Z'
    assert packet['farm']['crop_id'] == farm['crop_id'] and packet['G0_G4'] == 'not_assessed'
    assert first == result.put('tenant-1', raw) == result.get('tenant-1', first['result_id'], farm)
    for kind in expected:
        assert store._canonical(result.page('tenant-1', first['result_id'], farm, kind)) == store._canonical(expected[kind])
        assert result.page('tenant-1', first['result_id'], farm, kind, expected[kind]['total'])['records'] == []
    summary = result.summary('tenant-1', first['result_id'], farm)
    assert summary['checkpoint'] == json.loads(done)['checkpoint'] and summary['status'] == 'completed'
    assert summary['manifest']['identity'] == packet['binding']['input']['model_identity']
    assert sha256(producer.model._canonical(summary['time_binding'])).hexdigest() == packet['input']['time_binding_sha256']
    row = result._find('tenant-1', result_id=first['result_id'])
    assert all(str(row[k]) == v if k == 'registration_job_id' else row[k] == v for k, v in result._columns(packet).items())
    assert row['integrity_signature'] == hmac.new(KEY, store.DOMAIN + first['payload_raw'], 'sha256').hexdigest()
    path = producer.fresh_pack(tmp_path, value, done, custody); fresh = json.loads(path.read_bytes())
    fresh.update(result_id=first['result_id'], payload_sha256=first['payload_sha256'],
        recorded_at=first['recorded_at'].isoformat(), page_hashes={k: sha256(store._canonical(v)).hexdigest() for k, v in expected.items()},
        summary_sha256=sha256(store._canonical(summary)).hexdigest())
    path.write_text(json.dumps(fresh))
    child = subprocess.run([sys.executable, '-B', '-c', FRESH_SCRIPT, str(path)],
        stdin=subprocess.DEVNULL, capture_output=True, timeout=100,
        env=dict(os.environ, PYTHONPATH=producer.FRESH_PYTHONPATH))
    assert child.returncode == 0, child.stderr.decode(); evidence = json.loads(child.stdout)
    assert not Path('/proc', str(evidence['PID'])).exists()
    assert count(custody.binding) == 1 and producer.reference.counts(custody.binding) == before
    assert all(v == 0 for v in calls.values()) and len(os.listdir('/proc/self/fd')) == fd
    save('normal.json', {'packet': packet, 'payload_bytes': len(first['payload_raw']),
        'payload_sha256': first['payload_sha256'], 'fresh': evidence, 'calls': calls,
        'counts_before_after': [before, producer.reference.counts(custody.binding)],
        'FD_before_after': [fd, len(os.listdir('/proc/self/fd'))], 'rows': 1, 'actual_crop_Runs': 0})


@pytest.mark.parametrize('login_scope', [False], indirect=True)
def test_default_permission_refuses_store(setup):
    custody, _, _ = setup
    with pytest.raises(producer.model.JointCustodyHold): store.JointCropClimateResultStore(custody, integrity_key=KEY)


def test_uncreated_yielded_wrong_key_foreign_and_advisory_pending(setup, login_scope, monkeypatch):
    custody, raw, value = setup
    for key in (producer.KEY, b'x'*31, 'not-bytes'):
        with pytest.raises(producer.model.JointCustodyHold): store.JointCropClimateResultStore(custody, integrity_key=key)
    result = store.JointCropClimateResultStore(custody, integrity_key=KEY)
    with pytest.raises(producer.model.JointCustodyHold): result.put('tenant-1', raw)
    assert json.loads(custody.advance('tenant-1', raw, budget=1))['status'] == 'yielded'
    with pytest.raises(producer.model.JointCustodyHold): result.put('tenant-1', raw)
    custody.advance('tenant-1', raw, budget=128); calls = producer.reference.forbid(monkeypatch)
    farm = json.loads(raw)['farm']; base, _, _ = login_scope
    with base.connect() as conn:
        conn.execute('SELECT pg_advisory_xact_lock(%s)', (store._lock_key('tenant-1', 'joint-study', 'r1'),))
        with pytest.raises(producer.model.JointCustodyPending): result.put('tenant-1', raw)
    with pytest.raises(PermissionError): result.put('foreign', raw)
    assert result.get('tenant-1', store.VERSION+':'+'0'*64, farm) is None
    assert count(custody.binding) == 0
    assert all(v == 0 for v in calls.values())
    save('pending.json', {'uncreated_yielded_key_foreign_busy_rejected': True, 'rows': 0, 'calls': calls})


@pytest.mark.parametrize('phase', ['before-commit', 'after-commit'])
def test_actual_transaction_late_write_rights_and_rollback(setup, monkeypatch, phase):
    result, raw, value, _ = ready(setup); principal = value[4]; connect = result.jobs.connect
    calls = producer.reference.forbid(monkeypatch)
    class Connection:
        inserted = False
        def __init__(self, conn): self.conn = conn
        def __getattr__(self, key): return getattr(self.conn, key)
        def execute(self, query, *args, **kwargs):
            answer = self.conn.execute(query, *args, **kwargs)
            if hasattr(query, 'as_string') and query.as_string(self.conn).startswith('INSERT INTO'):
                self.inserted = True
                if phase == 'before-commit': principal['scopes'].remove('crop_result_write')
            return answer
    @contextmanager
    def connected():
        with connect() as conn:
            observed = Connection(conn); yield observed
        if phase == 'after-commit' and observed.inserted: principal['scopes'].remove('crop_result_write')
    monkeypatch.setattr(result.jobs, 'connect', connected)
    with pytest.raises(PermissionError): result.put('tenant-1', raw)
    assert count(result.server.binding) == (phase == 'after-commit')
    monkeypatch.setattr(result.jobs, 'connect', connect); principal['scopes'].add('crop_result_write')
    assert all(v == 0 for v in calls.values())
    if phase == 'after-commit':
        row = result._find('tenant-1', study_id='joint-study', revision='r1')
        assert result.get('tenant-1', row['result_id'], json.loads(raw)['farm'])['payload_raw'] == row['payload_raw']
    save(phase+'.json', {'rows': int(phase == 'after-commit'), 'late_rights_rejected': True, 'calls': calls})


def test_current_revocations_invalid_pages_and_no_rows_created(setup, monkeypatch):
    result, raw, value, _ = ready(setup); first = result.put('tenant-1', raw)
    binding, body, packet, _, principal, rights = value; farm = body['farm']; calls = producer.reference.forbid(monkeypatch)
    source = binding.farms.replay.candidates._source._source; get_rights = source.get_input_rights
    changes = [('input-rights', lambda: setattr(rights, 'allowed', False), lambda: setattr(rights, 'allowed', True)),
        ('review', lambda: packet[3].update(status='revoked'), lambda: packet[3].update(status='accepted_for_software_validation')),
        ('read-scope', lambda: principal['scopes'].remove('crop_result_read'), lambda: principal['scopes'].add('crop_result_read')),
        ('farm-source', lambda: monkeypatch.setattr(source, 'get_input_rights', lambda *_: None),
            lambda: monkeypatch.setattr(source, 'get_input_rights', get_rights))]
    rejected = []
    for name, withdraw, restore in changes:
        withdraw()
        for read in (lambda: result.get('tenant-1', first['result_id'], farm),
                lambda: result.page('tenant-1', first['result_id'], farm, 'samples'),
                lambda: result.summary('tenant-1', first['result_id'], farm)):
            with pytest.raises((producer.model.JointCustodyHold, PermissionError)): read()
        restore(); rejected.append(name)
    for kind, start, limit in (('unknown', 0, 1), ('samples', True, 1), ('samples', -1, 1),
            ('samples', 0, True), ('samples', 0, 65), ('events', 0, 9)):
        with pytest.raises(producer.model.JointCustodyHold): result.page('tenant-1', first['result_id'], farm, kind, start, limit)
    assert result.get('tenant-1', first['result_id'], farm) == first and count(binding) == 1
    assert all(v == 0 for v in calls.values())
    save('rights.json', {'revocations': rejected, 'denied_reads': 12, 'invalid_pages': 6, 'rows': 1, 'calls': calls})


def test_valid_hmac_cannot_mix_original_binding_progress_columns_or_keys(setup, monkeypatch):
    result, raw, value, _ = ready(setup); first = result.put('tenant-1', raw); farm = value[1]['farm']
    original = result._find('tenant-1', result_id=first['result_id']); calls = producer.reference.forbid(monkeypatch)
    find = result._find; rejected = []
    for kind in ('signature', 'authority', 'column', 'proof', 'evidence', 'context', 'UTC', 'crop', 'code', 'resolver'):
        row = deepcopy(original); packet = json.loads(row['payload_raw'])
        if kind == 'signature': row['integrity_signature'] = '0'*64
        elif kind == 'authority': row['registered_by'] = result.jobs.runtime_identity[0].roles['worker']
        elif kind == 'column': row['steps'] -= 1
        else:
            if kind == 'proof': packet['policies']['server_progress']['proof_sha256'] = '0'*64; packet['artifact']['proof_sha256'] = '0'*64
            elif kind == 'evidence': packet['binding']['input']['evidence_sha256'] = '0'*64
            elif kind == 'context': packet['input']['context_sha256'] = '0'*64
            elif kind == 'UTC': packet['input']['start_utc'] = '2026-10-01T00:00:00.123457Z'
            elif kind == 'crop': packet['farm']['batch_id'] = 'other-batch'
            elif kind == 'code': packet['code']['storage_code_sha256'] = '0'*64
            else: packet['policies']['resolver_version'] = 'other-resolver-v1'
            packet['result_id'] = store.VERSION+':'+sha256(store._canonical({k: v for k, v in packet.items() if k != 'result_id'})).hexdigest()
            row.update(result._columns(packet)); row['payload_raw'] = store._canonical(packet)
            row['payload_sha256'] = sha256(row['payload_raw']).hexdigest(); row['integrity_signature'] = result._signature(row['payload_raw'])
        monkeypatch.setattr(result, '_find', lambda *a, _row=row, **kw: _row)
        with pytest.raises(producer.model.JointCustodyHold): result.get('tenant-1', row['result_id'], farm)
        rejected.append(kind)
    monkeypatch.setattr(result, '_find', find)
    for other in ({**farm, 'crop_id': 'another-crop'}, {**farm, 'scenario_revision': 'r2'}):
        with pytest.raises(producer.model.JointCustodyHold): result.get('tenant-1', first['result_id'], other)
    wrong = store.JointCropClimateResultStore(result.server, integrity_key=b'z'*32)
    with pytest.raises(producer.model.JointCustodyHold): wrong.get('tenant-1', first['result_id'], farm)
    for changed in (first['payload_raw']+b' ', b'{"duplicate":1,"duplicate":2}', b'{}', b'x'*(store.MAX_PACKET_BYTES+1)):
        with pytest.raises(producer.model.JointCustodyHold): store._decode(changed)
    assert result.get('tenant-1', first['result_id'], farm) == first and count(result.server.binding) == 1
    assert all(v == 0 for v in calls.values()); save('tamper.json', {'changed': rejected, 'calls': calls, 'rows': 1})


@pytest.mark.parametrize('setup', ['hold'], indirect=True)
def test_original_hold_keeps_last_checkpoint_events_UTC_and_unpublished_gate(setup, monkeypatch):
    result, raw, value, done = ready(setup); progress = json.loads(done)
    assert progress['status'] == 'hold'; calls = producer.reference.forbid(monkeypatch)
    record = result.put('tenant-1', raw); farm = value[1]['farm']; summary = result.summary('tenant-1', record['result_id'], farm)
    assert summary['hold'] == progress['hold'] and summary['last_confirmed'] == progress['last_confirmed']
    assert summary['checkpoint'] == progress['checkpoint'] is None and summary['G0_G4'] == 'not_assessed'
    assert result.get('tenant-1', record['result_id'], farm) == record
    assert json.loads(record['payload_raw'])['status'] == 'stored_unpublished_research'
    assert all(v == 0 for v in calls.values()); save('hold.json', {'progress': progress, 'calls': calls, 'rows': 1})


def test_revision_conflicts_forced_rollback_old_rows_and_late_read_rights(setup, tmp_path, login_scope, monkeypatch):
    result, raw, value, _ = ready(setup); base, policy, _ = login_scope
    other_body = deepcopy(value[1]); other_body['rights']['revision'] = 'r2'
    other_root = tmp_path/'other-custody'; other_root.mkdir(mode=0o700)
    other_server = producer.model.JointServerCustody(result.server.binding, other_root,
        input_resolver=result.server.input_resolver, integrity_key=producer.KEY)
    other_raw = store._canonical(other_body); other_server.advance('tenant-1', other_raw, budget=128)
    other_store = store.JointCropClimateResultStore(other_server, integrity_key=KEY)
    calls = producer.reference.forbid(monkeypatch)
    from app.crop_cycle_calculation_result_schema import install_calculation_cycle_crop_result_schema
    from test_crop_cycle_result_schema import with_payload, insert as insert_legacy
    from test_crop_cycle_calculation_result_schema import with_payload as verified_payload, insert as insert_verified
    registration = json.loads(result.server.inspect('tenant-1', raw))
    with result.server._open('tenant-1', raw, False) as (session, _): binding = json.loads(session.binding_raw)
    old = with_payload({'tenant_id': 'tenant-1', 'study_id': 'old-schema-only', 'revision': 'r1',
        'result_id': 'crop-cycle-result-v1:'+'1'*64, 'scenario_id': value[1]['farm']['scenario_id'],
        'scenario_revision': value[1]['farm']['scenario_revision'],
        'registration_job_id': binding['registration']['registration_job_id'],
        'registration_sha256': binding['registration']['registration_sha256'],
        'input_root_sha256': '2'*64, 'artifact_sha256': '3'*64, 'artifact_header_sha256': '4'*64,
        'artifact_ref': 'crop-cycle-artifact-v1:'+'3'*64, 'artifact_status': 'completed',
        'steps': 120, 'planned_steps': 120, 'sample_count': 3, 'event_count': 0, 'commit_count': 1,
        'storage_bytes': 1, 'file_count': 1, 'integrity_signature': '5'*64,
        'registered_by': policy.roles['authority']})
    verified = verified_payload({**old, 'result_id': 'crop-cycle-verified-result-v1:'+'1'*64,
        'artifact_ref': 'crop-cycle-verified-artifact-v1:'+'3'*64})
    old_tables = ('crop_cycle_research_results', 'crop_cycle_verified_research_results')
    def old_rows(conn):
        return [conn.execute(sql.SQL('SELECT * FROM {}').format(sql.Identifier(policy.schema, t))).fetchall() for t in old_tables]
    with base.connect() as conn:
        conn.execute(sql.SQL('SET LOCAL ROLE {}').format(sql.Identifier(policy.owner)))
        install_calculation_cycle_crop_result_schema(conn, policy.schema)
        insert_legacy(conn, policy, old); insert_verified(conn, policy, verified); before = old_rows(conn)
    check_row = result._row
    def fail(*a, **kw): raise ValueError('forced post-insert failure')
    monkeypatch.setattr(result, '_row', fail)
    with pytest.raises(producer.model.JointCustodyHold): result.put('tenant-1', raw)
    assert count(result.server.binding) == 0
    monkeypatch.setattr(result, '_row', check_row); first = result.put('tenant-1', raw)
    with pytest.raises(producer.model.JointCustodyConflict): other_store.put('tenant-1', other_raw)
    assert count(result.server.binding) == 1 and result.get('tenant-1', first['result_id'], value[1]['farm']) == first
    original_page = store.artifact.ArtifactReader.page; rights = value[5]
    def late(*args, **kw):
        answer = original_page(*args, **kw); rights.allowed = False; return answer
    monkeypatch.setattr(store.artifact.ArtifactReader, 'page', late)
    with pytest.raises(producer.model.JointCustodyHold): result.page('tenant-1', first['result_id'], value[1]['farm'], 'samples')
    rights.allowed = True; monkeypatch.setattr(store.artifact.ArtifactReader, 'page', original_page)
    assert result.get('tenant-1', first['result_id'], value[1]['farm']) == first
    with base.connect() as conn:
        conn.execute(sql.SQL('SET LOCAL ROLE {}').format(sql.Identifier(policy.owner)))
        assert old_rows(conn) == before
    with base.connect() as conn: assert audit_runtime_roles(conn, policy)['tables'] > 0
    assert all(v == 0 for v in calls.values())
    save('conflict.json', {'same_revision_conflict': True, 'forced_failure_rollback': True,
        'late_page_rights_rejected': True, 'old_schema_only_rows_preserved': [1, 1],
        'historical_signed_migration_tested': False, 'current_grants_audit': True,
        'rows': 1, 'calls': calls, 'original_intent_sha256': registration['intent_sha256']})
