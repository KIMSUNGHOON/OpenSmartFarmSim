"""Actual SCRAM acceptance of signed HEADs; readers perform no numerical work."""
from copy import deepcopy
from concurrent.futures import ThreadPoolExecutor
from hashlib import sha256
import json
import os
from pathlib import Path
import selectors
import subprocess
import sys
from threading import Event

import psycopg
import pytest
from psycopg import sql
from psycopg.types.json import Jsonb

from app import crop_climate_joint_execution_checkpoint as model
from app import crop_climate_joint_result_store as results
from test_crop_climate_joint_server_custody import authoring, farm_setup, profiles, login_database, login_scope
from test_crop_climate_joint_server_custody import setup as producer_setup
import test_crop_climate_joint_server_custody as producer

pytestmark = producer.pytestmark


def save(name, value):
    root = os.environ.get('OSSF_JOINT_CHECKPOINT_EVIDENCE')
    if root:
        with (Path(root) / (name + '.json')).open('x') as f:
            os.fchmod(f.fileno(), 0o400)
            json.dump(value, f, sort_keys=True, indent=2)
            f.flush(); os.fsync(f.fileno())


@pytest.fixture(scope='module', autouse=True)
def cleanup(login_database):
    yield
    with psycopg.connect(login_database['admin']) as conn:
        schemas = conn.execute("SELECT count(*) FROM pg_namespace WHERE nspname LIKE 'login_test_%'").fetchone()[0]
        roles = conn.execute("SELECT count(*) FROM pg_roles WHERE rolname LIKE 'login_%'").fetchone()[0]
    save('database-cleanup', {'schemas': schemas, 'roles': roles})
    assert schemas == roles == 0


@pytest.fixture
def setup(producer_setup):
    server, raw, value = producer_setup
    principal = value[4]
    principal['scopes'].update({'simulation_create', 'simulation_execute'})
    admission = model.execution.JointCropClimateExecutionService(server.binding, input_resolver=server.input_resolver)
    job = admission.submit('tenant-1', raw)
    lease = admission.jobs.claim(180, allowed_stages=('simulation',), tenant_id='tenant-1', job_id=str(job['job_id']))
    progress = server.advance('tenant-1', raw, budget=1)
    store = model.JointExecutionCheckpointStore(admission, server)
    return store, lease, raw, value, progress


def confirm(store, lease):
    return store.confirm('tenant-1', str(lease['job_id']), attempt=lease['attempt'], lease_token=lease['lease_token'])


def events(store, lease):
    with store.jobs.connect() as conn:
        return conn.execute(sql.SQL('SELECT * FROM {} WHERE tenant_id=%s AND job_id=%s AND kind=%s')
            .format(store.jobs._table('job_events')), ('tenant-1', lease['job_id'], model.EVENT_KIND)).fetchall()


def forbid(patch):
    calls = producer.reference.forbid(patch)
    def blocked(key):
        calls[key] = 0
        def fail(*args, **kwargs):
            calls[key] += 1
            pytest.fail('checkpoint acceptance invoked ' + key)
        return fail
    patch.setattr(producer.model.JointServerCustody, 'advance', blocked('custody_advance'))
    patch.setattr(results.JointCropClimateResultStore, 'put', blocked('result_put'))
    return calls


def test_normal_original_head_duplicate_and_heartbeat_time(setup, monkeypatch):
    store, lease, raw, _, progress = setup
    before = store.jobs.get_job('tenant-1', lease['job_id'])
    with monkeypatch.context() as patch:
        calls = forbid(patch)
        first = confirm(store, lease)
        assert confirm(store, lease) == first
        fresh = model.JointExecutionCheckpointStore(store.admission, store.server)
        assert confirm(fresh, lease) == first
        assert store.jobs.get_job('tenant-1', lease['job_id'])['updated_at'] == before['updated_at']
        assert store.jobs.renew('tenant-1', lease['job_id'], lease['attempt'], lease['lease_token'], 180)
        assert confirm(store, lease) == first and len(events(store, lease)) == 1
        job = store.jobs.get_job('tenant-1', lease['job_id'])
        assert job['state'] == 'simulating' and job['updated_at'] > first['recorded_at']
        assert store.server.inspect('tenant-1', raw) == progress
        assert all(n == 0 for n in calls.values())
    p = first['checkpoint']; v = json.loads(progress)
    assert p['publication_sequence'] == 1 and p['head_sha256'] == v['head_sha256']
    assert p['proof_sha256'] == v['proof_sha256'] and p['counts'] == v['counts']
    assert p['farm_binding_sha256'] == v['binding_sha256'] and p['status'] == 'yielded'
    assert p['computed_through_utc'] == v['times']['last_confirmed']['at']
    with store.jobs.connect() as conn:
        row = store.jobs._locked_job(conn, 'tenant-1', lease['job_id'])
        binding = json.loads(row['input_bytes'])['farm_binding']
    assert binding['registration']['floor_area']['unit'] == 'm²'
    assert sha256(model.execution.documents._canonical(binding)).hexdigest() == p['farm_binding_sha256']
    assert p['G0_G4'] == 'not_assessed' and first['recorded_at'].utcoffset().total_seconds() == 0
    assert len(model.custody._canonical(p)) <= model.MAX_BYTES
    with store.jobs.connect() as conn:
        assert conn.pgconn.used_password and conn.info.get_parameters()['require_auth'] == 'scram-sha-256'
    save('normal', {'checkpoint': p, 'event_recorded_at': first['recorded_at'].isoformat(),
        'same_event_after_retry_and_heartbeat': True, 'actual_scram': True, 'calls': calls})


@pytest.mark.parametrize('producer_setup', ['normal', 'hold'], indirect=True)
def test_sequence_original_counts_utc_and_terminal_without_result(setup, monkeypatch, producer_setup):
    store, lease, raw, _, initial = setup
    with monkeypatch.context() as patch:
        calls = forbid(patch)
        first = confirm(store, lease)
        assert all(v == 0 for v in calls.values())
    final = store.server.advance('tenant-1', raw, budget=128)
    original = json.loads(final)
    with monkeypatch.context() as patch:
        calls = forbid(patch)
        second = confirm(store, lease)
        assert confirm(store, lease) == second and all(v == 0 for v in calls.values())
    a, b = first['checkpoint'], second['checkpoint']
    assert a['publication_sequence'] == 1 and b['publication_sequence'] == 2
    assert b['custody_sequence'] > a['custody_sequence'] and b['steps'] == 16
    assert b['head_sha256'] == original['head_sha256'] and b['proof_sha256'] == original['proof_sha256']
    assert b['counts'] == original['counts'] and b['computed_through_utc'] == original['times']['last_confirmed']['at']
    assert b['artifact_sha256'] == original['artifact_sha256'] and b['status'] in ('completed', 'hold')
    assert second['recorded_at'] > first['recorded_at'] and len(events(store, lease)) == 2
    if b['status'] == 'hold':
        rows = store.server.page('tenant-1', raw, final, 'samples')['records']
        assert all(r['value']['step_index'] < original['hold']['step_index'] for r in rows)
        assert b['counts'] == {'samples': 2, 'events': 2}
    else:
        assert b['counts'] == {'samples': 3, 'events': 3}
    with store.jobs.connect() as conn:
        assert conn.execute(sql.SQL('SELECT count(*) AS n FROM {} WHERE job_id=%s')
            .format(store.jobs._table('job_publications')), (lease['job_id'],)).fetchone()['n'] == 0
    assert store.jobs.get_job('tenant-1', lease['job_id'])['state'] == 'simulating'
    save('sequence-' + b['status'], {'first': a, 'last': b, 'calls': calls,
        'terminal_does_not_complete_job_or_register_result': True, 'failed_trial_not_published': True})


def expire(store, lease):
    with store.jobs.connect() as conn:
        conn.execute(sql.SQL("UPDATE {} SET lease_until=clock_timestamp()-interval '1 second' WHERE job_id=%s")
            .format(store.jobs._table('jobs')), (lease['job_id'],))


def test_lease_fence_retry_preserves_original_event_and_cancel(setup, monkeypatch):
    store, lease, raw, value, _ = setup
    with monkeypatch.context() as patch:
        calls = forbid(patch)
        for field, bad in (('attempt', True), ('attempt', 0), ('attempt', 4),
                           ('lease_token', ''), ('job_id', 'invalid')):
            args = {'attempt': lease['attempt'], 'lease_token': lease['lease_token'], 'job_id': str(lease['job_id'])}
            args[field] = bad
            with pytest.raises(model.JointCheckpointHold): store.confirm('tenant-1', **args)
        for attempt, token in ((2, lease['lease_token']), (lease['attempt'], 'wrong')):
            with pytest.raises(model.JointCheckpointLeaseLost):
                store.confirm('tenant-1', str(lease['job_id']), attempt=attempt, lease_token=token)
        first = confirm(store, lease)
        expire(store, lease)
        with pytest.raises(model.JointCheckpointLeaseLost): confirm(store, lease)
        second_lease = store.jobs.claim(180, allowed_stages=('simulation',), tenant_id='tenant-1', job_id=str(lease['job_id']))
        assert second_lease['attempt'] == 2 and confirm(store, second_lease) == first
        with pytest.raises(model.JointCheckpointLeaseLost): confirm(store, lease)
        assert all(v == 0 for v in calls.values())
    store.server.advance('tenant-1', raw, budget=4)
    with monkeypatch.context() as patch:
        calls = forbid(patch)
        new = confirm(store, second_lease)
        assert new['attempt'] == 2 and new['checkpoint']['publication_sequence'] == 2
        value[4]['scopes'].add('cancel')
        store.jobs.cancel('tenant-1', lease['job_id'])
        with pytest.raises(model.JointCheckpointLeaseLost): confirm(store, second_lease)
        assert len(events(store, lease)) == 2 and all(v == 0 for v in calls.values())
    save('lease', {'invalid_arguments': 5, 'stale_wrong_expired_canceled_rejected': True,
        'new_attempt_same_head_preserves_first_event_time': True, 'new_head_sequence': 2, 'calls': calls})


@pytest.mark.parametrize('change', ['rights', 'scope', 'resolver', 'expired', 'cancel'])
def test_late_change_rolls_back_checkpoint_event(setup, monkeypatch, change):
    store, lease, _, value, _ = setup
    principal, rights = value[4:]; version = store.admission.input_resolver.version
    original_current, original_lease = store._current, store._lease
    seen = []
    def current(*args):
        seen.append('current')
        if len(seen) == 2:
            if change == 'rights': rights.allowed = False
            elif change == 'scope': principal['scopes'].remove('simulation_execute')
            elif change == 'resolver': store.admission.input_resolver.version = 'changed-at-checkpoint-v1'
        return original_current(*args)
    lease_calls = []
    def locked(conn, *args):
        lease_calls.append(1)
        if len(lease_calls) == 3:
            assert conn.execute(sql.SQL('SELECT count(*) AS n FROM {} WHERE job_id=%s AND kind=%s')
                .format(store.jobs._table('job_events')), (lease['job_id'], model.EVENT_KIND)).fetchone()['n'] == 1
            if change == 'expired':
                conn.execute(sql.SQL("UPDATE {} SET lease_until=clock_timestamp()-interval '1 second' WHERE job_id=%s")
                    .format(store.jobs._table('jobs')), (lease['job_id'],))
            elif change == 'cancel':
                conn.execute(sql.SQL('UPDATE {} SET cancel_requested=true WHERE job_id=%s')
                    .format(store.jobs._table('jobs')), (lease['job_id'],))
        return original_lease(conn, *args)
    with monkeypatch.context() as patch:
        calls = forbid(patch)
        patch.setattr(store, '_current', current); patch.setattr(store, '_lease', locked)
        with pytest.raises((model.JointCheckpointHold, PermissionError)): confirm(store, lease)
        assert len(seen) == 2 and events(store, lease) == [] and all(v == 0 for v in calls.values())
    rights.allowed = True; principal['scopes'].add('simulation_execute'); store.admission.input_resolver.version = version
    assert confirm(store, lease)['checkpoint']['publication_sequence'] == 1
    save('late-' + change, {'after_insert_rejected': True, 'checkpoint_event_rolled_back': True,
        'original_lease_transaction_recovered': True, 'calls': calls})


def test_access_current_rights_reviews_source_and_signed_head(setup, monkeypatch):
    store, lease, raw, value, _ = setup
    principal, rights = value[4:]; principal['scopes'].remove('simulation_create')
    with monkeypatch.context() as patch:
        calls = forbid(patch)
        scopes = ('simulation_execute', *producer.reference.WRITE_SCOPES)
        for scope in scopes:
            principal['scopes'].remove(scope)
            with pytest.raises(PermissionError): confirm(store, lease)
            principal['scopes'].add(scope)
        with pytest.raises(PermissionError):
            store.confirm('foreign', str(lease['job_id']), attempt=lease['attempt'], lease_token=lease['lease_token'])
        rights.allowed = False
        with pytest.raises(model.JointCheckpointHold): confirm(store, lease)
        rights.allowed = True
        review = value[2][3]; status = review['status']; review['status'] = 'revoked'
        with pytest.raises(model.JointCheckpointHold): confirm(store, lease)
        review['status'] = status
        _, artifact, proofs = producer.locations(store.server, raw)
        head = artifact / 'HEAD'
        proof = proofs / (sha256(head.read_bytes()).hexdigest() + '.json')
        for path in (value[2][0] / 'source.json', head, proof):
            original = path.read_bytes(); mode = path.stat().st_mode & 0o777
            try:
                path.chmod(0o600); path.write_bytes(original + b' '); path.chmod(mode)
                with pytest.raises(model.JointCheckpointHold): confirm(store, lease)
            finally:
                path.chmod(0o600); path.write_bytes(original); path.chmod(mode)
        assert events(store, lease) == []
        assert confirm(store, lease)['checkpoint']['publication_sequence'] == 1
        assert all(v == 0 for v in calls.values())
    save('access', {'required_scopes': len(scopes), 'create_scope_not_required': True,
        'foreign_rights_review_source_signed_head_rejected': True, 'calls': calls})


def test_input_mixing_closed_envelope_and_forged_history(setup, monkeypatch):
    store, lease, _, _, _ = setup
    with store.jobs.connect() as conn:
        row = store.jobs._locked_job(conn, 'tenant-1', lease['job_id'])
    original = store.jobs._verified_input; value = json.loads(row['input_bytes']); changed = []
    bad = deepcopy(value); bad['unexpected'] = True; changed.append(bad)
    bad = deepcopy(value); bad['farm_binding_sha256'] = '0' * 64; changed.append(bad)
    bad = deepcopy(value); bad['farm_binding']['tenant_id'] = 'foreign'; changed.append(bad)
    bad = deepcopy(value); bad['request']['revision'] += '-other'; changed.append(bad)
    bad = deepcopy(value); bad['input_resolver_version'] = 'untrusted-v1'; changed.append(bad)
    bad = deepcopy(value); bad['input_version'] = 'unsupported-v1'; changed.append(bad)
    with monkeypatch.context() as patch:
        calls = forbid(patch)
        for bad in changed:
            patch.setattr(store.jobs, '_verified_input', lambda _, b=bad: model.execution.canonical_input_bytes(b))
            with pytest.raises(model.JointCheckpointHold): confirm(store, lease)
        patch.setattr(store.jobs, '_verified_input', original)
        first = confirm(store, lease)
        forged = deepcopy(first['checkpoint']); forged['counts']['samples'] = True
        with store.jobs.connect() as conn:
            conn.execute(sql.SQL('INSERT INTO {} (tenant_id,job_id,event_id,attempt,kind,reason) '
                'VALUES (%s,%s,gen_random_uuid(),%s,%s,%s)').format(store.jobs._table('job_events')),
                ('tenant-1', lease['job_id'], lease['attempt'], model.EVENT_KIND, Jsonb(forged)))
        with pytest.raises(model.JointCheckpointHold): confirm(store, lease)
        assert len(events(store, lease)) == 2 and all(v == 0 for v in calls.values())
    save('input', {'closed_mixed_envelopes_rejected': len(changed),
        'injected_invalid_boolean_duplicate_history_blocks_adoption': True, 'new_accepted_event_after_forgery': 0, 'calls': calls})


def test_concurrent_confirm_is_one_original_event(setup, monkeypatch):
    store, lease, _, _, _ = setup
    with monkeypatch.context() as patch:
        calls = forbid(patch)
        original = store.jobs._locked_job; checks = []
        def timed_out(*args):
            if str(args[2]) == str(lease['job_id']):
                checks.append(1)
                if len(checks) == 2: raise model.QueryCanceled()
            return original(*args)
        with monkeypatch.context() as nested:
            nested.setattr(store.jobs, '_locked_job', timed_out)
            with pytest.raises(model.custody.JointCustodyPending): confirm(store, lease)
        assert events(store, lease) == []
        entered, release = Event(), Event()
        original_current = store._current
        def current(*args):
            if not entered.is_set():
                entered.set()
                assert release.wait(15), 'concurrent probe did not release owner'
            return original_current(*args)
        patch.setattr(store, '_current', current)
        with ThreadPoolExecutor(max_workers=2) as pool:
            first = pool.submit(confirm, store, lease)
            try:
                assert entered.wait(15), 'first confirmation did not acquire job lock'
                duplicate = pool.submit(confirm, store, lease)
                with pytest.raises(model.custody.JointCustodyPending): duplicate.result(timeout=12)
            finally: release.set()
            accepted = first.result(timeout=55)
        assert confirm(store, lease) == accepted and len(events(store, lease)) == 1
        assert all(v == 0 for v in calls.values())
    save('concurrent', {'overlapping_requests': 2, 'events': 1, 'busy_returns_typed_pending': True,
        'actual_scram_row_lock_statement_timeout': True, 'pending_inside_file_session_rolled_back': True,
        'retry_identical_event_and_timestamp': True, 'calls': calls})


FRESH_SCRIPT = producer.reference.FRESH_SCRIPT.split('calls={')[0] + '''
import test_crop_climate_joint_server_custody as u
import test_crop_climate_joint_execution_checkpoint as k
from pytest import MonkeyPatch
packet=(Path(p['directory']),p['body']['input']['source_sha256'],None,review)
resolver=u.Resolver(packet,Path(p['proof']).read_bytes())
server=u.model.JointServerCustody(service,p['custody'],input_resolver=resolver,integrity_key=u.KEY)
admission=k.model.execution.JointCropClimateExecutionService(service,input_resolver=resolver)
store=k.model.JointExecutionCheckpointStore(admission,server)
raw=t._canonical(p['body'])
if p['mode']=='crash':
 progress=server.advance('tenant-1',raw,budget=128)
 print(json.dumps({'progress_sha256':u.sha256(progress).hexdigest(),'checkpoint':json.loads(progress)['checkpoint']}),flush=True)
 sys.stdin.readline()
else:
 principal['scopes'].discard('simulation_create')
 with MonkeyPatch.context() as patch:
  calls=k.forbid(patch)
  item=store.confirm('tenant-1',p['job_id'],attempt=p['attempt'],lease_token=p['lease_token'])
  review['status']='revoked'
  try:store.confirm('tenant-1',p['job_id'],attempt=p['attempt'],lease_token=p['lease_token'])
  except k.model.JointCheckpointHold:pass
  else:raise AssertionError('fresh revocation allowed')
  assert all(v==0 for v in calls.values())
 with jobs.connect() as conn:assert conn.pgconn.used_password and conn.info.get_parameters()['require_auth']=='scram-sha-256'
 print(json.dumps({'event_id':item['event_id'],'checkpoint':item['checkpoint'],'recorded_at':item['recorded_at'].isoformat(),
   'calls':calls,'actual_scram':True,'review_revocation_rejected':True}),flush=True)
'''


def test_fresh_crash_after_head_before_event_adopt_without_reintegration(setup, tmp_path, monkeypatch):
    store, lease, raw, value, progress = setup
    _, artifact, _ = producer.locations(store.server, raw)
    head_path = artifact / 'HEAD'; old_head = head_path.read_bytes()
    path = producer.fresh_pack(tmp_path, value, progress, store.server)
    pack = json.loads(path.read_bytes()); pack['mode'] = 'crash'
    path.write_text(json.dumps(pack)); env = dict(os.environ, PYTHONPATH=producer.FRESH_PYTHONPATH)
    child = subprocess.Popen([sys.executable, '-B', '-c', FRESH_SCRIPT, str(path)],
        stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, env=env)
    try:
        with selectors.DefaultSelector() as selector:
            selector.register(child.stdout, selectors.EVENT_READ)
            assert selector.select(45), 'fresh producer did not publish HEAD'
        line = child.stdout.readline(); assert line, 'fresh producer exited before HEAD'
        produced = json.loads(line); child.kill(); child.communicate(timeout=10)
        assert child.returncode == -9 and events(store, lease) == []
        expire(store, lease)
        current = store.jobs.claim(180, allowed_stages=('simulation',), tenant_id='tenant-1', job_id=str(lease['job_id']))
        assert current['attempt'] == 2
        with monkeypatch.context() as patch:
            calls = forbid(patch)
            original = store.server.inspect('tenant-1', raw)
            assert sha256(original).hexdigest() == produced['progress_sha256']
            assert json.loads(original)['checkpoint'] == produced['checkpoint']
            first = confirm(store, current)
            assert confirm(store, current) == first and all(v == 0 for v in calls.values())
        pack.update(mode='read', job_id=str(current['job_id']), attempt=current['attempt'], lease_token=current['lease_token'])
        path.write_text(json.dumps(pack))
        fresh = subprocess.Popen([sys.executable, '-B', '-c', FRESH_SCRIPT, str(path)],
            stdin=subprocess.DEVNULL, stdout=subprocess.PIPE, stderr=subprocess.PIPE, env=env)
        try:
            stdout, stderr = fresh.communicate(timeout=55)
            assert fresh.returncode == 0, 'fresh reader failed; stderr sha256=' + sha256(stderr).hexdigest()
            read = json.loads(stdout)
        finally:
            if fresh.poll() is None: fresh.kill(); fresh.communicate(timeout=10)
        assert read['event_id'] == first['event_id'] and read['recorded_at'] == first['recorded_at'].isoformat()
        assert read['checkpoint'] == first['checkpoint'] and len(events(store, lease)) == 1
        latest_head = head_path.read_bytes()
        with monkeypatch.context() as patch:
            calls_after = forbid(patch)
            try:
                head_path.chmod(0o600); head_path.write_bytes(old_head); head_path.chmod(0o400)
                with pytest.raises(model.JointCheckpointHold): confirm(store, current)
            finally:
                head_path.chmod(0o600); head_path.write_bytes(latest_head); head_path.chmod(0o400)
            assert confirm(store, current) == first and all(v == 0 for v in calls_after.values())
        save('fresh', {'killed_producer_exit': child.returncode, 'fresh_reader_exit': fresh.returncode,
            'original_progress_sha256': produced['progress_sha256'], 'adopted_checkpoint': first['checkpoint'],
            'no_reintegration_calls': calls, 'fresh': read, 'attempt': 2, 'same_event_and_time': True,
            'signed_old_head_rejected_without_new_event': True, 'restored_head_calls': calls_after})
    finally:
        if child.poll() is None: child.kill(); child.communicate(timeout=10)
        path.unlink(missing_ok=True)
