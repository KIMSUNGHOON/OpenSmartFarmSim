"""Actual leased calculation, signed original values, and atomic DB completion."""
from contextlib import contextmanager
from hashlib import sha256
import json
import os
from pathlib import Path
import selectors
import signal
import subprocess
import sys
import time
from uuid import uuid4

import psycopg
import pytest
from psycopg import sql

from app import crop_climate_joint_execution_worker as model
from test_crop_climate_joint_result_store import (
    authoring, farm_setup, profiles, login_database, original_login_scope, login_scope,
    KEY, pytestmark, count)
from test_crop_climate_joint_server_custody import setup as producer_setup
import test_crop_climate_joint_server_custody as producer
import test_crop_climate_joint_result_store as registry


def save(name, value):
    root = os.environ.get('OSSF_JOINT_WORKER_EVIDENCE')
    if root:
        with (Path(root) / (name + '.json')).open('x') as f:
            os.fchmod(f.fileno(), 0o400); json.dump(value, f, sort_keys=True, indent=2)
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
    value[4]['scopes'].update({'simulation_create', 'simulation_execute', 'cancel'})
    admission = model.checkpoints.execution.JointCropClimateExecutionService(server.binding, input_resolver=server.input_resolver)
    checkpoint_store = model.checkpoints.JointExecutionCheckpointStore(admission, server)
    result_store = model.results.JointCropClimateResultStore(server, integrity_key=KEY)
    worker = model.JointExecutionWorker(checkpoint_store, result_store, tenant_id='tenant-1', chunk_budget=8)
    job = admission.submit('tenant-1', raw)
    return worker, str(job['job_id']), raw, value


def rows(worker, job_id, table):
    with worker.jobs.connect() as conn:
        return conn.execute(sql.SQL('SELECT * FROM {} WHERE tenant_id=%s AND job_id=%s')
            .format(worker.jobs._table(table)), ('tenant-1', job_id)).fetchall()


FRESH_READ = registry.FRESH_SCRIPT.split("print(json.dumps(")[0] + '''
from app import crop_climate_joint_execution_worker as w
with jobs.connect() as conn:
 job=jobs._locked_job(conn,'tenant-1',p['job_id'])
 publication=conn.execute(u.sql.SQL('SELECT * FROM {} WHERE job_id=%s').format(jobs._table('job_publications')),(p['job_id'],)).fetchone()
 links=conn.execute(u.sql.SQL('SELECT reason FROM {} WHERE job_id=%s AND kind=%s').format(jobs._table('job_events')),(p['job_id'],w.RESULT_EVENT_KIND)).fetchall()
 assert job['state']==p['state'] and len(links)==1
 link=links[0]['reason'];assert link['result_id']==record['result_id'] and link['artifact_sha256']==record['payload_sha256'] and link['artifact_size']==len(record['payload_raw'])
 if p['state']=='succeeded':assert publication['manifest']==link
 else:assert publication is None and link['status']=='hold'
 assert conn.pgconn.used_password and conn.info.get_parameters()['require_auth']=='scram-sha-256'
print(json.dumps({'actual_scram':True,'read_calls':calls,'same_result_and_publication':True,'PID':__import__('os').getpid()}))
'''


@pytest.mark.parametrize('producer_setup', ['normal', 'hold'], indirect=True)
def test_queued_actual_calculation_original_values_and_atomic_completion(setup, producer_setup, tmp_path, monkeypatch):
    worker, job_id, raw, value = setup
    server, binding = worker.server, worker.server.binding
    before = producer.reference.counts(binding)
    c = producer.model.continuation; ctx = value[2][2]._context
    expected = c.advance_chunk(ctx, c.start(ctx), 128)
    value[4]['scopes'].remove('simulation_create')
    chunks, renewals = [], []
    origin = time.monotonic()
    original_advance = producer.model.JointServerCustody.advance
    original_before = model.JointExecutionWorker._before
    def timed_advance(instance, *a, **kw):
        start = time.monotonic(); result = original_advance(instance, *a, **kw); end = time.monotonic()
        chunks.append({'start':start-origin, 'end':end-origin, 'seconds':end-start,
                       'budget':kw['budget'], 'steps':json.loads(result)['steps']})
        return result
    def timed_before(instance, *a, **kw):
        start = time.monotonic(); result = original_before(instance, *a, **kw); end = time.monotonic()
        renewals.append({'start':start-origin, 'end':end-origin, 'seconds':end-start})
        return result
    with monkeypatch.context() as patch:
        calls = producer.measured(patch)
        patch.setattr(producer.model.JointServerCustody, 'advance', timed_advance)
        patch.setattr(model.JointExecutionWorker, '_before', timed_before)
        outcome = worker.run_once(job_id)
    worker_seconds = time.monotonic() - origin
    renewal_gaps = [b['end']-a['end'] for a,b in zip(renewals,renewals[1:])]
    tail = worker_seconds - renewals[-1]['end']
    assert len(chunks) > 1 and all(0 < p['seconds'] < worker.lease_seconds for p in chunks)
    assert all(0 < t < worker.lease_seconds for t in (*renewal_gaps, tail))
    status = expected['status']; state = 'succeeded' if status == 'completed' else 'hold'
    assert outcome.state == state and outcome.attempt == 1 and outcome.result_id
    assert calls['step'] == 16 and calls['start'] == 1 and calls['restore'] == 2
    final = server.inspect('tenant-1', raw); progress = json.loads(final)
    if status == 'hold':
        assert progress['checkpoint'] is None and expected['checkpoint'] is None
        assert progress['hold'] == expected['hold']
    else:
        assert progress['checkpoint']['sha256'] == expected['checkpoint'].sha256
    assert progress['last_confirmed'] == expected['last_confirmed']
    original_pages = {k: server.page('tenant-1', raw, final, k) for k in ('samples', 'events')}
    for kind, page in original_pages.items():
        assert [r['value'] for r in page['records']] == expected[kind]
        assert [r['time']['at'] for r in page['records']] == [producer.model.clock.at_index(value[2][2], r['step_index']) for r in expected[kind]]
    assert progress['G0_G4'] == 'not_assessed'
    with monkeypatch.context() as patch:
        read_calls = producer.reference.forbid(patch)
        record = worker.results.get('tenant-1', outcome.result_id, value[1]['farm'])
        packet = json.loads(record['payload_raw'])
        assert packet['policies']['server_progress'] == progress
        assert worker.run_once(job_id) is None
        assert all(n == 0 for n in read_calls.values())
    publications = rows(worker, job_id, 'job_publications'); outcomes = rows(worker, job_id, 'attempt_outcomes')
    assert len(outcomes) == count(binding) == 1
    links = [r for r in rows(worker, job_id, 'job_events') if r['kind'] == model.RESULT_EVENT_KIND]
    assert len(links) == 1; link = links[0]['reason']
    assert link['artifact_sha256'] == record['payload_sha256'] and link['artifact_size'] == len(record['payload_raw'])
    assert link['root_sha256'] == progress['artifact_sha256'] and link['result_id'] == outcome.result_id
    assert link['status'] == status and outcomes[0]['state'] == state
    assert len(publications) == (1 if state == 'succeeded' else 0)
    if publications: assert publications[0]['manifest'] == link
    events = [r for r in rows(worker, job_id, 'job_events') if r['kind'] == model.checkpoints.EVENT_KIND]
    events.sort(key=lambda r: r['reason']['publication_sequence'])
    assert [r['reason']['publication_sequence'] for r in events] == [1, 2, 3]
    assert events[-1]['reason']['head_sha256'] == progress['head_sha256']
    summary = worker.results.summary('tenant-1', outcome.result_id, value[1]['farm'])
    path = producer.fresh_pack(tmp_path, value, final, server); fresh = json.loads(path.read_bytes())
    fresh.update(result_id=outcome.result_id, job_id=job_id, state=state,
        payload_sha256=record['payload_sha256'], recorded_at=record['recorded_at'].isoformat(),
        page_hashes={k: sha256(model.results._canonical(v)).hexdigest() for k, v in original_pages.items()},
        summary_sha256=sha256(model.results._canonical(summary)).hexdigest())
    path.write_text(json.dumps(fresh))
    try:
        child = subprocess.run([sys.executable, '-B', '-c', FRESH_READ, str(path)],
            stdin=subprocess.DEVNULL, capture_output=True, timeout=100,
            env=dict(os.environ, PYTHONPATH=producer.FRESH_PYTHONPATH))
        assert child.returncode == 0, child.stderr.decode()
        evidence = json.loads(child.stdout)
    finally:
        path.unlink(); (tmp_path / 'proof.private.json').unlink()
    assert not Path('/proc', str(evidence['PID'])).exists()
    after = producer.reference.counts(binding)
    assert after[0] == before[0] and after[2:] == before[2:] == (0, 0)
    assert after[1] - before[1] == len(rows(worker, job_id, 'job_events')) - 1
    save('normal-' + status, {'progress': progress, 'calls': calls, 'read_calls': read_calls,
        'fresh': evidence, 'result_link': link,
        'publication_packet_bytes': len(record['payload_raw']), 'checkpoints': [e['reason'] for e in events],
        'same_original_checkpoint_rows_all_states_utc': True,
        'timings': {'clock':'monotonic', 'worker_seconds':worker_seconds,
            'lease_seconds':worker.lease_seconds, 'chunk_budget':worker.chunk_budget,
            'chunks':chunks, 'validation_and_renewals':renewals, 'renewal_gaps_seconds':renewal_gaps,
            'last_renewal_to_completion_seconds':tail},
        'counts': {'registry':1, 'publication':len(publications), 'outcome':1, 'result_links':1}})


def no_published_result(worker, job_id):
    assert count(worker.server.binding) == 0
    assert rows(worker, job_id, 'job_publications') == []
    assert not any(r['kind'] == 'succeeded' for r in rows(worker, job_id, 'job_events'))
    assert not any(r['kind'] == model.RESULT_EVENT_KIND for r in rows(worker, job_id, 'job_events'))


def expire(worker, job_id):
    with worker.jobs.connect() as conn:
        conn.execute(sql.SQL("UPDATE {} SET lease_until=clock_timestamp()-interval '1 second' WHERE job_id=%s")
            .format(worker.jobs._table('jobs')), (job_id,))


@pytest.mark.parametrize('point', ['chunk', 'terminal'])
def test_chunk_cancel_acknowledged_without_checkpoint_or_result(setup, monkeypatch, point):
    worker, job_id, raw, _ = setup
    if point == 'chunk':
        original = producer.model.JointServerCustody.advance
        def cancel(server, *a, **kw):
            result = original(server, *a, **kw)
            assert worker.jobs.cancel('tenant-1', job_id)
            return result
        monkeypatch.setattr(producer.model.JointServerCustody, 'advance', cancel)
    else:
        worker.server.advance('tenant-1', raw, budget=128)
        original = model.JointExecutionWorker._finish
        def cancel(instance, *a, **kw):
            assert worker.jobs.cancel('tenant-1', job_id)
            return original(instance, *a, **kw)
        monkeypatch.setattr(model.JointExecutionWorker, '_finish', cancel)
    outcome = worker.run_once(job_id)
    assert outcome.state == 'canceled' and outcome.result_id is None
    assert worker.jobs.get_job('tenant-1', job_id)['state'] == 'canceled'
    no_published_result(worker, job_id)
    events = [r for r in rows(worker, job_id, 'job_events') if r['kind'] == model.checkpoints.EVENT_KIND]
    assert len(events) == (0 if point == 'chunk' else 1)
    assert rows(worker, job_id, 'attempt_outcomes')[0]['state'] == 'canceled'
    private = json.loads(worker.server.inspect('tenant-1', raw))
    save('cancel-' + point, {'state': outcome.state, 'private_status': private['status'],
        'confirmed_checkpoints': len(events), 'private_HEAD_not_result': True})


def test_chunk_expiry_and_new_attempt_adopts_prefix_before_remaining_calculation(setup, monkeypatch):
    worker, job_id, raw, _ = setup
    with monkeypatch.context() as patch:
        calls = producer.measured(patch)
        measured = producer.model.JointServerCustody.advance
        def lost(server, *a, **kw):
            result = measured(server, *a, **kw); expire(worker, job_id); return result
        patch.setattr(producer.model.JointServerCustody, 'advance', lost)
        first = worker.run_once(job_id)
    assert first.state == 'unclosed' and first.result_id is None
    progress = json.loads(worker.server.inspect('tenant-1', raw))
    no_published_result(worker, job_id)
    assert not any(r['kind'] == model.checkpoints.EVENT_KIND for r in rows(worker, job_id, 'job_events'))
    adopted = []; confirm = model.checkpoints.JointExecutionCheckpointStore.confirm
    with monkeypatch.context() as patch:
        remaining = producer.measured(patch)
        def accept(store, *a, **kw):
            record = confirm(store, *a, **kw)
            adopted.append((record['checkpoint']['head_sha256'], dict(remaining)))
            return record
        patch.setattr(model.checkpoints.JointExecutionCheckpointStore, 'confirm', accept)
        final = worker.run_once(job_id)
    assert final.state == 'succeeded' and final.attempt == 2
    assert adopted[0][0] == progress['head_sha256'] and all(n == 0 for n in adopted[0][1].values())
    assert calls['step'] + remaining['step'] == 16 and remaining['start'] == 0
    assert [r['state'] for r in sorted(rows(worker, job_id, 'attempt_outcomes'), key=lambda r:r['attempt'])] == ['lease_expired', 'succeeded']
    save('expiry', {'private_prefix': progress, 'first_calls': calls, 'remaining_calls': remaining,
        'first_adoption_calls_zero': adopted[0][1], 'final_state': final.state, 'final_attempt': final.attempt})


@pytest.mark.parametrize('fault', ['publication', 'event', 'outcome', 'hook_exit', 'final_update'])
def test_publication_rollback_leaves_no_partial_result(setup, monkeypatch, fault):
    worker, job_id, raw, _ = setup
    worker.server.advance('tenant-1', raw, budget=128)
    hit = []
    with monkeypatch.context() as patch:
        calls = producer.reference.forbid(patch)
        if fault in ('publication', 'event', 'outcome'):
            name = {'publication':'_insert_publication', 'event':'_event', 'outcome':'_outcome'}[fault]
            original = getattr(type(worker.jobs), name)
            def fail(instance, conn, tenant, job, *args, **kw):
                result = original(instance, conn, tenant, job, *args, **kw)
                terminal = fault == 'publication' or (args[0] if fault == 'event' else args[1]) == 'succeeded'
                if terminal: hit.append(True); raise RuntimeError('owned publication rollback fault')
                return result
            patch.setattr(type(worker.jobs), name, fail)
        elif fault == 'hook_exit':
            original = model.results.JointCropClimateResultStore._put_in_transaction
            @contextmanager
            def fail(instance, *a, **kw):
                with original(instance, *a, **kw) as record: yield record
                hit.append(True); raise RuntimeError('owned post-hook rollback fault')
            patch.setattr(model.results.JointCropClimateResultStore, '_put_in_transaction', fail)
        else:
            original = psycopg.Connection.execute
            def fail(conn, query, params=None, *a, **kw):
                text = query.as_string(conn) if hasattr(query, 'as_string') else str(query)
                if 'SET state=%s, reason=%s,' in text and params and params[0] == 'succeeded':
                    hit.append(True); raise RuntimeError('owned final update rollback fault')
                return original(conn, query, params, *a, **kw)
            patch.setattr(psycopg.Connection, 'execute', fail)
        outcome = worker.run_once(job_id)
        assert all(n == 0 for n in calls.values())
    assert hit == [True] and outcome.state == 'queued' and outcome.result_id is None
    no_published_result(worker, job_id)
    assert len(rows(worker, job_id, 'attempt_outcomes')) == 1
    assert rows(worker, job_id, 'attempt_outcomes')[0]['state'] == 'queued'
    assert sum(r['kind'] == model.checkpoints.EVENT_KIND for r in rows(worker, job_id, 'job_events')) == 1
    save('rollback-' + fault, {'state': outcome.state, 'partial_registry_publication_terminal_events': 0,
        'original_confirmed_prefix_retained': True, 'calls': calls})


@pytest.mark.parametrize('change', ['scope', 'rights', 'resolver'])
def test_late_rights_after_completion_records_roll_back_every_result(setup, monkeypatch, change):
    worker, job_id, raw, value = setup
    worker.server.advance('tenant-1', raw, budget=128)
    principal, rights = value[4:]; original = type(worker.jobs)._outcome
    version = worker.server.input_resolver.version; hit = []
    with monkeypatch.context() as patch:
        calls = producer.reference.forbid(patch)
        def revoke(instance, conn, tenant, job, attempt, state, *a, **kw):
            result = original(instance, conn, tenant, job, attempt, state, *a, **kw)
            if state == 'succeeded':
                hit.append(True)
                if change == 'scope': principal['scopes'].remove('simulation_execute')
                elif change == 'rights': rights.allowed = False
                else: worker.server.input_resolver.version = version + '-changed'
            return result
        patch.setattr(type(worker.jobs), '_outcome', revoke)
        outcome = worker.run_once(job_id)
        assert all(n == 0 for n in calls.values())
    assert hit == [True] and outcome.state == 'hold' and outcome.result_id is None
    principal['scopes'].add('simulation_execute'); rights.allowed = True
    worker.server.input_resolver.version = version
    no_published_result(worker, job_id)
    assert rows(worker, job_id, 'attempt_outcomes')[0]['state'] == 'hold'
    save('late-' + change, {'state': outcome.state, 'all_result_writes_rolled_back': True, 'calls': calls})


def test_terminal_adoption_keeps_original_record_time_without_numerics(setup, monkeypatch):
    worker, job_id, raw, value = setup
    progress = worker.server.advance('tenant-1', raw, budget=128)
    existing = worker.results.put('tenant-1', raw)
    with monkeypatch.context() as patch:
        calls = producer.reference.forbid(patch)
        outcome = worker.run_once(job_id)
        assert outcome.state == 'succeeded' and outcome.result_id == existing['result_id']
        assert worker.results.get('tenant-1', outcome.result_id, value[1]['farm']) == existing
        assert worker.server.inspect('tenant-1', raw) == progress
        assert all(n == 0 for n in calls.values())
    assert count(worker.server.binding) == 1 and len(rows(worker, job_id, 'job_publications')) == 1
    save('adoption', {'same_original_bytes_id_recorded_at': True, 'calls': calls, 'state': outcome.state})


def test_pending_custody_is_retryable_without_numerics_or_result(setup, monkeypatch):
    worker, job_id, raw, _ = setup
    with worker.server._open('tenant-1', raw, True):
        with monkeypatch.context() as patch:
            calls = producer.reference.forbid(patch)
            outcome = worker.run_once(job_id)
            assert outcome.state == 'queued' and outcome.reason_code == 'joint_execution_busy'
            assert outcome.result_id is None and all(n == 0 for n in calls.values())
    no_published_result(worker, job_id)
    assert not any(r['kind'] == model.checkpoints.EVENT_KIND for r in rows(worker, job_id, 'job_events'))
    save('pending', {'state':outcome.state, 'calls':calls, 'checkpoint_count':0})


def test_final_lease_fence_rolls_back_result_publication_and_outcome(setup, monkeypatch):
    worker, job_id, raw, _ = setup
    worker.server.advance('tenant-1', raw, budget=128)
    original = type(worker.jobs)._outcome; hit = []
    with monkeypatch.context() as patch:
        calls = producer.reference.forbid(patch)
        def expire_in_transaction(instance, conn, tenant, job, attempt, state, *a, **kw):
            original(instance, conn, tenant, job, attempt, state, *a, **kw)
            if state == 'succeeded':
                hit.append(True)
                conn.execute(sql.SQL("UPDATE {} SET lease_until=clock_timestamp()-interval '1 second' WHERE job_id=%s")
                    .format(worker.jobs._table('jobs')), (job,))
        patch.setattr(type(worker.jobs), '_outcome', expire_in_transaction)
        outcome = worker.run_once(job_id)
        assert all(n == 0 for n in calls.values())
    assert hit == [True] and outcome.state == 'unclosed' and outcome.result_id is None
    no_published_result(worker, job_id)
    assert rows(worker, job_id, 'attempt_outcomes') == []
    assert worker.jobs.get_job('tenant-1', job_id)['state'] == 'simulating'
    save('final-fence', {'expired_lease_injected_in_completion_transaction':True,
        'all_result_writes_and_injection_rolled_back':True, 'outcome':outcome.state, 'calls':calls})


@pytest.mark.parametrize('case', ['extra', 'digest', 'version', 'stage', 'cancel', 'denied'])
def test_wrong_input_and_unclaimable_jobs_perform_no_work(setup, monkeypatch, case):
    worker, job_id, _, value = setup
    if case in ('extra', 'digest', 'version', 'stage'):
        with worker.jobs.connect() as conn:
            row = worker.jobs._locked_job(conn, 'tenant-1', job_id)
        packet = json.loads(row['input_bytes'])
        if case == 'extra': packet['unexpected'] = True
        if case == 'version': packet['input_version'] = 'unrelated-input-v1'
        raw = model.checkpoints.execution.canonical_input_bytes(packet)
        job_id = str(uuid4())
        def insert():
            with worker.jobs.connect() as conn:
                conn.execute(sql.SQL('INSERT INTO {} '
                '(tenant_id,job_id,stage,state,input_bytes,input_sha256,idempotency_key,max_attempts) '
                'VALUES (%s,%s,%s,%s,%s,%s,%s,%s)').format(worker.jobs._table('jobs')),
                ('tenant-1', job_id, 'collection' if case == 'stage' else 'simulation',
                 'queued', raw, '0'*64 if case == 'digest' else sha256(raw).hexdigest(),
                 'owned-malformed-job-' + case, 3))
        if case == 'digest':
            with pytest.raises(psycopg.errors.CheckViolation): insert()
        else: insert()
    elif case == 'cancel': assert worker.jobs.cancel('tenant-1', job_id)
    else: value[4]['scopes'].remove('simulation_execute')
    with monkeypatch.context() as patch:
        calls = producer.reference.forbid(patch)
        if case == 'denied':
            with pytest.raises(PermissionError): worker.run_once(job_id)
        else:
            outcome = worker.run_once(job_id)
            if case == 'extra': assert outcome.state == 'hold' and outcome.result_id is None
            else: assert outcome is None
        assert all(n == 0 for n in calls.values())
    no_published_result(worker, job_id)
    job = worker.jobs.get_job('tenant-1', job_id)
    if case == 'digest':
        assert job is None and list(worker.server.directory.iterdir()) == []
        save('input-digest', {'state':'rejected_before_queue', 'attempts':0, 'calls':calls})
        return
    assert job['attempt_count'] == (1 if case == 'extra' else 0)
    assert job['state'] == ('hold' if case == 'extra' else 'canceled' if case == 'cancel' else 'queued')
    assert list(worker.server.directory.iterdir()) == []
    save('input-' + case, {'state':job['state'], 'attempts':job['attempt_count'], 'calls':calls})


def test_binding_parameters_tenant_and_job_id_reject_before_claim(setup, monkeypatch):
    worker, job_id, _, _ = setup
    with monkeypatch.context() as patch:
        calls = producer.reference.forbid(patch)
        for field, values in (('lease_seconds', (True, 0, 86401)), ('chunk_budget', (False, 0, 129))):
            for value in values:
                with pytest.raises(ValueError):
                    model.JointExecutionWorker(worker.checkpoints, worker.results, tenant_id='tenant-1', **{field:value})
        with pytest.raises(model.checkpoints.JointCheckpointHold):
            model.JointExecutionWorker(object(), worker.results, tenant_id='tenant-1')
        foreign = model.JointExecutionWorker(worker.checkpoints, worker.results, tenant_id='foreign')
        with pytest.raises(PermissionError): foreign.run_once(job_id)
        for bad in (None, uuid4(), job_id.replace('-', ''), 'not-a-uuid'):
            with pytest.raises(ValueError): worker.run_once(bad)
        assert worker.run_once(str(uuid4())) is None
        for field, changed in (('tenant_id','foreign'), ('chunk_budget',1), ('lease_seconds',1), ('results',object())):
            original = getattr(worker,field); setattr(worker,field,changed)
            with pytest.raises(model.checkpoints.JointCheckpointHold): worker.run_once(job_id)
            setattr(worker,field,original)
        assert all(n == 0 for n in calls.values())
    assert worker.jobs.get_job('tenant-1', job_id)['attempt_count'] == 0
    no_published_result(worker, job_id)
    save('binding', {'claim_attempts':0, 'calls':calls, 'fixed_authority_and_bounds':True})


FRESH_WORKER = producer.reference.FRESH_SCRIPT.split('calls={')[0] + '''
import test_crop_climate_joint_execution_worker as u
from pytest import MonkeyPatch
packet=(Path(p['directory']),p['body']['input']['source_sha256'],None,review)
resolver=u.producer.Resolver(packet,Path(p['proof']).read_bytes())
server=u.producer.model.JointServerCustody(service,p['custody'],input_resolver=resolver,integrity_key=u.producer.KEY)
admission=u.model.checkpoints.execution.JointCropClimateExecutionService(service,input_resolver=resolver)
checkpoint_store=u.model.checkpoints.JointExecutionCheckpointStore(admission,server)
result_store=u.model.results.JointCropClimateResultStore(server,integrity_key=u.KEY)
worker=u.model.JointExecutionWorker(checkpoint_store,result_store,tenant_id='tenant-1',chunk_budget=8 if p['phase']=='producer' else 128)
with MonkeyPatch.context() as patch:
 calls=u.producer.measured(patch);adopted=[]
 if p['phase']=='producer':
  def stop(instance,lease):
   progress=server.inspect('tenant-1',t._canonical(p['body']))
   print(json.dumps({'progress':json.loads(progress),'calls':calls,'PID':__import__('os').getpid()}),flush=True)
   sys.stdin.readline();raise AssertionError('owned producer should have been killed')
  patch.setattr(u.model.JointExecutionWorker,'_confirm',stop)
 else:
  original=u.model.checkpoints.JointExecutionCheckpointStore.confirm
  def confirm(instance,*a,**kw):
   result=original(instance,*a,**kw)
   if not adopted:adopted.append({'checkpoint':result['checkpoint'],'calls':dict(calls)})
   return result
  patch.setattr(u.model.checkpoints.JointExecutionCheckpointStore,'confirm',confirm)
 outcome=worker.run_once(p['job_id'])
 progress=json.loads(server.inspect('tenant-1',t._canonical(p['body'])))
 assert outcome.state=='succeeded' and outcome.attempt==2
 assert adopted[0]['checkpoint']['head_sha256']==p['prefix_head_sha256'] and all(v==0 for v in adopted[0]['calls'].values())
 assert calls['start']==0 and calls['restore']==1 and calls['step']==16-p['prefix_steps']
 with jobs.connect() as conn:assert conn.pgconn.used_password and conn.info.get_parameters()['require_auth']=='scram-sha-256'
 print(json.dumps({'state':outcome.state,'attempt':outcome.attempt,'result_id':outcome.result_id,'progress':progress,'calls':calls,'adopted':adopted,'actual_scram':True,'PID':__import__('os').getpid()}))
'''


def test_crash_after_head_before_db_and_fresh_worker_adopts_original_prefix(setup, tmp_path):
    worker, job_id, raw, value = setup
    value[4]['scopes'].remove('simulation_create')
    path = producer.fresh_pack(tmp_path, value, b'not-yet-created', worker.server)
    packet = json.loads(path.read_bytes()); packet.update(job_id=job_id, phase='producer')
    path.write_text(json.dumps(packet)); child = None; pidfd = None
    try:
        child = subprocess.Popen([sys.executable, '-B', '-c', FRESH_WORKER, str(path)],
            stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
            env=dict(os.environ, PYTHONPATH=producer.FRESH_PYTHONPATH))
        pidfd = os.pidfd_open(child.pid)
        with selectors.DefaultSelector() as selector:
            selector.register(child.stdout, selectors.EVENT_READ)
            ready = selector.select(60)
        assert ready and child.poll() is None
        first = json.loads(child.stdout.readline())
        assert first['PID'] == child.pid and first['progress']['status'] == 'yielded' and first['progress']['steps'] > 0
        signal.pidfd_send_signal(pidfd, signal.SIGKILL)
        _, stderr = child.communicate(timeout=10)
        assert child.returncode == -9, stderr.decode()
        assert not Path('/proc', str(child.pid)).exists()
        no_published_result(worker, job_id)
        assert not any(r['kind'] == model.checkpoints.EVENT_KIND for r in rows(worker, job_id, 'job_events'))
        assert json.loads(worker.server.inspect('tenant-1', raw)) == first['progress']
        expire(worker, job_id)
        packet.update(phase='consumer', prefix_steps=first['progress']['steps'], prefix_head_sha256=first['progress']['head_sha256'])
        path.write_text(json.dumps(packet))
        fresh = subprocess.run([sys.executable, '-B', '-c', FRESH_WORKER, str(path)],
            stdin=subprocess.DEVNULL, capture_output=True, timeout=100,
            env=dict(os.environ, PYTHONPATH=producer.FRESH_PYTHONPATH))
        assert fresh.returncode == 0, fresh.stderr.decode()
        second = json.loads(fresh.stdout)
        assert not Path('/proc', str(second['PID'])).exists()
        assert first['calls']['step'] + second['calls']['step'] == 16
        assert count(worker.server.binding) == len(rows(worker, job_id, 'job_publications')) == 1
        assert worker.jobs.get_job('tenant-1', job_id)['state'] == 'succeeded'
        save('crash', {'producer':first, 'producer_actual_exit':child.returncode, 'fresh':second,
            'fresh_actual_exit':fresh.returncode, 'no_prefix_reintegration':True})
    finally:
        if child is not None and child.poll() is None:
            signal.pidfd_send_signal(pidfd, signal.SIGKILL); child.communicate(timeout=10)
        if pidfd is not None: os.close(pidfd)
        path.unlink(); (tmp_path/'proof.private.json').unlink()
