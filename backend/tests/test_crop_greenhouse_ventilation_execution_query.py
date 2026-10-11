"""Actual SCRAM progress reads, original times, current rights and no calculation."""
from contextlib import contextmanager
from copy import deepcopy
from hashlib import sha256
import json
import os
from pathlib import Path
import subprocess
import sys
from uuid import uuid4

import psycopg
import pytest
from psycopg import sql

from app import crop_greenhouse_ventilation_execution_query as model
from test_crop_greenhouse_ventilation_execution_worker import (
    setup as worker_setup, producer_setup, authoring, farm_setup, profiles,
    login_database, original_login_scope, login_scope)
import test_crop_greenhouse_ventilation_execution_worker as reference
from test_deterministic_job_discovery import persisted_digest


def save(name, value):
    root = os.environ.get('OSSF_VENTILATION_EXECUTION_QUERY_EVIDENCE')
    if root:
        with (Path(root) / (name + '.json')).open('x') as f:
            os.fchmod(f.fileno(), 0o400); json.dump(value, f, sort_keys=True, indent=2)
            f.flush(); os.fsync(f.fileno())


@pytest.fixture(scope='module')
def query_cleanup(login_database):
    yield
    with psycopg.connect(login_database['admin']) as conn:
        schemas = conn.execute("SELECT count(*) FROM pg_namespace WHERE nspname LIKE 'login_test_%'").fetchone()[0]
        roles = conn.execute("SELECT count(*) FROM pg_roles WHERE rolname LIKE 'login_%'").fetchone()[0]
    assert schemas == roles == 0
    save('database-cleanup', {'schemas': schemas, 'roles': roles})


@pytest.fixture
def setup(worker_setup):
    worker, job_id, raw, value = worker_setup
    return model.VentilationExecutionQuery(worker.checkpoints, worker.results), worker, job_id, raw, value


def readonly(value):
    value[4]['scopes'].difference_update({'simulation_create', 'simulation_execute', 'crop_result_write'})


def forbid(patch):
    calls = reference.producer.reference.forbid(patch)
    def block(key):
        calls[key] = 0
        def fail(*a, **kw):
            calls[key] += 1; pytest.fail('progress query invoked ' + key)
        return fail
    for cls, name in ((model.checkpoints.VentilationExecutionCheckpointStore, 'confirm'),
            (model.custody.VentilationServerCustody, 'advance'),
            (model.storage.VentilationResultStore, 'put'),
            (model.storage.VentilationResultStore, '_put_in_transaction')):
        patch.setattr(cls, name, block(name))
    for name in ('submit', 'claim', 'renew', 'fail', 'cancel', 'ack_cancel', '_event', '_outcome', '_insert_publication', '_durable_artifact'):
        patch.setattr(model.checkpoints.execution.JobStore, name, block('jobs.' + name))
    return calls


def read(query, job_id):
    raw = query.read('tenant-1', job_id)
    assert raw == model.storage._canonical(json.loads(raw)) and len(raw) <= model.MAX_RESPONSE_BYTES
    result = json.loads(raw); assert model.ExecutionRead.model_validate(result).model_dump(mode='json') == result
    assert set(result) == {'version', 'scope', 'G0_G4', 'job', 'cancel_requested', 'observed_at', 'checkpoint_status', 'checkpoint', 'result'}
    assert not any(k in raw.decode() for k in ('lease_token', 'lease_until', 'principal', 'dsn', 'input_bytes', 'proofs/'))
    return result


def confirm(worker, job_id):
    lease = worker.jobs.claim(600, tenant_id='tenant-1', allowed_stages=('simulation',), job_id=job_id)
    assert lease
    return lease


@reference.pytestmark
@pytest.mark.usefixtures('query_cleanup')
def test_none_unstarted_cancelled_and_missing_have_no_calculation(setup, original_login_scope, monkeypatch):
    query, worker, job_id, _, value = setup
    base = original_login_scope[0]; unrelated = []
    for tenant, stage, version in (('foreign', 'simulation', model.checkpoints.execution.INPUT_VERSION),
            ('tenant-1', 'collection', model.checkpoints.execution.INPUT_VERSION),
            ('tenant-1', 'simulation', 'economic-calculation-input-v1')):
        unrelated.append(str(base.submit(tenant, stage, {'input_version': version}, uuid4().hex)['job_id']))
    readonly(value); before = persisted_digest(worker.jobs)
    original_entries = sorted(p.name for p in worker.server.directory.iterdir())
    with monkeypatch.context() as patch:
        calls = forbid(patch); first = read(query, job_id)
        assert first['job']['state'] == 'queued' and first['checkpoint_status'] == 'none'
        assert first['checkpoint'] is first['result'] is None
        assert query.read('tenant-1', str(uuid4())) is None
        assert all(query.read('tenant-1', other) is None for other in unrelated)
        assert all(n == 0 for n in calls.values())
    assert persisted_digest(worker.jobs) == before
    assert worker.jobs.cancel('tenant-1', job_id)
    with monkeypatch.context() as patch:
        calls = forbid(patch); canceled = read(query, job_id)
        assert canceled['job']['state'] == 'canceled' and canceled['checkpoint_status'] == 'none'
    assert sorted(p.name for p in worker.server.directory.iterdir()) == original_entries
    save('none', {'queued': first, 'canceled': canceled, 'calls': calls, 'query_database_unchanged': True, 'intent_not_created': True})


@pytest.mark.parametrize('fault', ['extra', 'version', 'status', 'steps', 'result'])
def test_projection_closed_schema_and_inconsistent_progress_rejected(fault):
    at = '2026-10-01T00:00:02.123456Z'
    payload = {'version': model.VERSION, 'scope': model.custody.SCOPE, 'G0_G4': 'not_assessed',
        'job': {'job_id':str(uuid4()), 'stage':'simulation', 'state':'simulating', 'attempt_count':1,
            'max_attempts':3, 'created_at':at, 'updated_at':at, 'reason_code':None},
        'cancel_requested':False, 'observed_at':at, 'checkpoint_status':'current', 'result':None,
        'checkpoint':{'head_sha256':'a'*64, 'proof_sha256':'b'*64, 'artifact_sha256':None,
            'status':'yielded', 'steps':1, 'planned_steps':16, 'counts':{'samples':2,'events':0},
            'computed_through_utc':at, 'checkpoint_recorded_at':at, 'publication_sequence':1}}
    model.ExecutionRead.model_validate(payload)
    if fault == 'extra': payload['private'] = True
    elif fault == 'version': payload['version'] += '-future'
    elif fault == 'status': payload['checkpoint_status'] = 'unavailable'
    elif fault == 'steps': payload['checkpoint']['steps'] = -1
    else: payload['result'] = {'result_id':'joint-ventilation-result-v1:'+'c'*64,
        'status':'completed','farm':{'scenario_id':'farm','scenario_revision':'r1','registration_sha256':'d'*64,'crop_id':'crop',
            'batch_id':'batch','zone_id':'zone'}}
    with pytest.raises(ValueError): model.ExecutionRead.model_validate(payload)


@reference.pytestmark
@pytest.mark.usefixtures('query_cleanup')
def test_checkpoint_original_counts_utc_first_time_survives_heartbeat_and_new_attempt(setup, monkeypatch):
    query, worker, job_id, raw, value = setup; lease = confirm(worker, job_id)
    readonly(value)
    with monkeypatch.context() as patch:
        calls = forbid(patch); claimed = read(query, job_id)
        assert claimed['job']['state'] == 'simulating' and claimed['checkpoint_status'] == 'none'
    value[4]['scopes'].update({'simulation_execute', 'crop_result_write'})
    progress = json.loads(worker.server.advance('tenant-1', raw, budget=2))
    first = worker.checkpoints.confirm('tenant-1', job_id, attempt=lease['attempt'], lease_token=lease['lease_token'])
    readonly(value)
    with monkeypatch.context() as patch:
        calls = forbid(patch); initial = read(query, job_id)
        assert initial['checkpoint_status'] == 'current'
        cp = initial['checkpoint']
        assert cp['counts'] == progress['counts'] and cp['head_sha256'] == progress['head_sha256']
        assert cp['computed_through_utc'] == progress['times']['last_confirmed']['at']
        assert cp['checkpoint_recorded_at'] == model._utc(first['recorded_at'])
    assert worker.jobs.renew('tenant-1', job_id, lease['attempt'], lease['lease_token'], 600)
    value[4]['scopes'].update({'simulation_execute', 'crop_result_write'})
    reference.expire(worker, job_id); new = confirm(worker, job_id)
    duplicate = worker.checkpoints.confirm('tenant-1', job_id, attempt=new['attempt'], lease_token=new['lease_token'])
    assert duplicate == first and first['attempt'] == 1 and new['attempt'] == 2
    readonly(value); before = persisted_digest(worker.jobs)
    with monkeypatch.context() as patch:
        calls = forbid(patch); after = read(query, job_id)
        assert after['checkpoint'] == cp and after['job']['attempt_count'] == 2
        assert after['job']['updated_at'] != initial['job']['updated_at'] and all(n == 0 for n in calls.values())
    assert persisted_digest(worker.jobs) == before
    save('checkpoint', {'claimed': claimed, 'first': initial, 'retried': after, 'original_confirmation_attempt': first['attempt'], 'calls': calls, 'query_database_unchanged': True})


@reference.pytestmark
@pytest.mark.usefixtures('query_cleanup')
def test_checkpoint_unconfirmed_descendant_and_real_lock_are_unavailable(setup, monkeypatch):
    query, worker, job_id, raw, value = setup; lease = confirm(worker, job_id)
    worker.server.advance('tenant-1', raw, budget=2)
    worker.checkpoints.confirm('tenant-1', job_id, attempt=lease['attempt'], lease_token=lease['lease_token'])
    worker.server.advance('tenant-1', raw, budget=2)
    readonly(value); before = persisted_digest(worker.jobs)
    with monkeypatch.context() as patch:
        calls = forbid(patch); mismatch = read(query, job_id)
    with worker.server._open('tenant-1', raw, False):
        with monkeypatch.context() as patch:
            calls = forbid(patch); busy = read(query, job_id)
    for result in (mismatch, busy):
        assert result['checkpoint_status'] == 'unavailable' and result['checkpoint'] is result['result'] is None
    assert persisted_digest(worker.jobs) == before
    save('unavailable', {'unconfirmed': mismatch, 'busy': busy, 'calls': calls, 'query_database_unchanged': True})


@reference.pytestmark
@pytest.mark.usefixtures('query_cleanup')
@pytest.mark.parametrize('producer_setup', ['normal', 'hold'], indirect=True)
def test_terminal_original_result_success_or_numerical_hold_and_fresh_reader(setup, producer_setup, tmp_path, monkeypatch):
    query, worker, job_id, raw, value = setup
    worker.server.advance('tenant-1', raw, budget=128)
    outcome = worker.run_once(job_id)
    progress = json.loads(worker.server.inspect('tenant-1', raw))
    assert outcome.state == ('succeeded' if progress['status'] == 'completed' else 'hold')
    readonly(value); before = persisted_digest(worker.jobs)
    with monkeypatch.context() as patch:
        calls = forbid(patch); response = read(query, job_id)
        assert response['checkpoint_status'] == 'current' and response['job']['state'] == outcome.state
        with worker.jobs.connect() as conn:
            row = conn.execute(sql.SQL('SELECT * FROM {} WHERE tenant_id=%s AND result_id=%s')
                .format(worker.jobs._table(model.storage.schema.TABLE)), ('tenant-1', outcome.result_id)).fetchone()
        packet = worker.results._row(row, 'tenant-1', value[1]['farm'])
        expected_farm = {k: packet['farm'][k] for k in model.public.Farm.model_fields}
        assert response['result'] == {'result_id': outcome.result_id, 'farm': expected_farm, 'status': progress['status']}
        assert response['checkpoint']['computed_through_utc'] == progress['times']['last_confirmed']['at']
        assert response['checkpoint']['artifact_sha256'] == progress['artifact_sha256']
        assert all(n == 0 for n in calls.values())
    assert persisted_digest(worker.jobs) == before
    evidence = {'response': response, 'calls': calls, 'query_database_unchanged': True,
        'publication_count': len(reference.rows(worker, job_id, 'job_publications'))}
    assert evidence['publication_count'] == (1 if outcome.state == 'succeeded' else 0)
    if outcome.state == 'succeeded':
        path = reference.producer.fresh_pack(tmp_path, value, worker.server.inspect('tenant-1', raw), worker.server)
        packet = json.loads(path.read_bytes()); packet.update(job_id=job_id, phase='consumer', expected=response); path.write_text(json.dumps(packet))
        script = reference.FRESH_WORKER.split('with MonkeyPatch.context()')[0] + '''
import test_crop_greenhouse_ventilation_execution_query as q
query=q.model.VentilationExecutionQuery(worker.checkpoints,worker.results)
with MonkeyPatch.context() as patch:
 calls=q.forbid(patch);response=json.loads(query.read('tenant-1',p['job_id']))
 response.pop('observed_at');expected=p['expected'];expected.pop('observed_at');assert response==expected
 assert all(n==0 for n in calls.values())
with jobs.connect() as conn:assert conn.pgconn.used_password and conn.info.get_parameters()['require_auth']=='scram-sha-256'
print(json.dumps({'same_original_DTO_except_observation_time':True,'calls':calls,'actual_scram':True}))
'''
        try:
            child = subprocess.run([sys.executable, '-B', '-c', script, str(path)], capture_output=True,
                stdin=subprocess.DEVNULL, timeout=120, env=dict(os.environ, PYTHONPATH=reference.producer.FRESH_PYTHONPATH))
            assert child.returncode == 0, child.stderr.decode(); evidence['fresh'] = json.loads(child.stdout)
        finally: path.unlink(); (tmp_path / 'proof.private.json').unlink()
        original = query._bundle; rejected = []
        for fault in ('publication-bool', 'worker-pin'):
            with monkeypatch.context() as patch:
                calls = forbid(patch)
                def view(*a, _fault=fault, **kw):
                    bundle = deepcopy(original(*a, **kw))
                    if _fault == 'publication-bool': bundle[3][0]['manifest']['attempt'] = True
                    else: bundle[2][0]['reason']['worker_code_sha256'] = 'a' * 64
                    return bundle
                patch.setattr(query, '_bundle', view)
                with pytest.raises(model.VentilationExecutionQueryHold): query.read('tenant-1', job_id)
                assert all(n == 0 for n in calls.values())
                rejected.append(fault)
        evidence['read_view_faults_rejected'] = rejected
        assert persisted_digest(worker.jobs) == before
    save('terminal-' + progress['status'], evidence)


@reference.pytestmark
@pytest.mark.usefixtures('query_cleanup')
def test_rights_readonly_scopes_and_late_revocation_fail_closed(setup, monkeypatch):
    query, worker, job_id, _, value = setup; readonly(value); principal, rights = value[4:]
    for scope in ('metadata', 'crop_result_read'):
        principal['scopes'].remove(scope)
        with pytest.raises(PermissionError): query.read('tenant-1', job_id)
        principal['scopes'].add(scope)
    before = persisted_digest(worker.jobs); terminal = query._terminal
    with monkeypatch.context() as patch:
        calls = forbid(patch)
        def revoke(*a, **kw):
            result = terminal(*a, **kw); rights.allowed = False; return result
        patch.setattr(query, '_terminal', revoke)
        with pytest.raises(model.VentilationExecutionQueryHold): query.read('tenant-1', job_id)
    rights.allowed = True
    assert persisted_digest(worker.jobs) == before and all(n == 0 for n in calls.values())
    save('rights', {'read_scopes_without_create_execute_write': True, 'scope_rejections': 2, 'late_source_rights_rejected': True, 'calls': calls})


@reference.pytestmark
@pytest.mark.usefixtures('query_cleanup')
@pytest.mark.parametrize('fault', ['extra', 'duplicate', 'wrong-input'])
def test_corrupt_appended_checkpoint_event_rejects_without_mutation(setup, monkeypatch, fault):
    query, worker, job_id, raw, value = setup; lease = confirm(worker, job_id)
    worker.server.advance('tenant-1', raw, budget=2)
    first = worker.checkpoints.confirm('tenant-1', job_id, attempt=1, lease_token=lease['lease_token'])
    forged = deepcopy(first['checkpoint'])
    if fault == 'extra': forged['private-marker'] = True
    if fault == 'wrong-input': forged['input_sha256'] = 'a' * 64
    with worker.jobs.connect() as conn:
        worker.jobs._event(conn, 'tenant-1', job_id, model.checkpoints.EVENT_KIND, 1, forged)
    readonly(value); before = persisted_digest(worker.jobs)
    with monkeypatch.context() as patch:
        calls = forbid(patch)
        with pytest.raises(model.VentilationExecutionQueryHold): query.read('tenant-1', job_id)
    assert persisted_digest(worker.jobs) == before and all(n == 0 for n in calls.values())
    save('corrupt-' + fault, {'appended_owned_fault_only': True, 'existing_immutable_records_unchanged': True, 'calls': calls, 'query_database_unchanged': True})


@reference.pytestmark
@pytest.mark.usefixtures('query_cleanup')
def test_binding_bad_ids_and_dependency_drift_are_rejected(setup):
    query, worker, job_id, _, value = setup; readonly(value)
    for bad in (None, uuid4(), 'bad', str(uuid4()).upper()):
        with pytest.raises(ValueError, match='^ventilation execution query request rejected$'): query.read('tenant-1', bad)
    with pytest.raises(model.VentilationExecutionQueryHold): model.VentilationExecutionQuery(object(), worker.results)
    before = persisted_digest(worker.jobs); original = query.results; query.results = object()
    with pytest.raises(model.VentilationExecutionQueryHold): query.read('tenant-1', job_id)
    query.results = original; assert persisted_digest(worker.jobs) == before
    save('binding', {'invalid_ids': 4, 'fixed_dependencies': True, 'query_database_unchanged': True})


@reference.pytestmark
@pytest.mark.usefixtures('query_cleanup')
def test_rights_job_change_during_read_is_pending_without_partial_response(setup, monkeypatch):
    query, worker, job_id, _, value = setup; readonly(value)
    terminal = query._terminal; actor = []
    with monkeypatch.context() as patch:
        calls = forbid(patch)
        def drift(*a, **kw):
            result = terminal(*a, **kw)
            with worker.jobs.connect() as conn:
                conn.execute(sql.SQL("UPDATE {} SET state='canceled',reason=%s::jsonb,updated_at=clock_timestamp() WHERE tenant_id=%s AND job_id=%s")
                    .format(worker.jobs._table('jobs')), (json.dumps({'code':'canceled_by_request'}), 'tenant-1', job_id))
            actor.append('cancel'); return result
        patch.setattr(query, '_terminal', drift)
        with pytest.raises(model.VentilationExecutionQueryPending): query.read('tenant-1', job_id)
    assert actor == ['cancel'] and all(n == 0 for n in calls.values())
    save('job-drift', {'separate_actor_cancel': 1, 'pending_no_partial_response': True, 'query_calls': calls})
