"""Actual SCRAM progress reads, original times, current rights and no calculation."""
from contextlib import contextmanager
from copy import deepcopy
from hashlib import sha256
import json
import os
from pathlib import Path
from uuid import uuid4

import psycopg
import pytest
from psycopg import sql

from app import crop_greenhouse_co2_execution_query as model
from test_crop_greenhouse_co2_execution_worker import (
    setup as worker_setup, producer_setup, authoring, profiles,
    login_database, original_login_scope, login_scope)
import test_crop_greenhouse_co2_execution_worker as reference
from test_deterministic_job_discovery import persisted_digest as jobs_digest
from test_crop_solar_custody_file_locks import exclusive_locks


def persisted_digest(jobs):
    with jobs.connect() as conn:
        rows=conn.execute(sql.SQL('SELECT * FROM {} ORDER BY tenant_id,result_id')
            .format(jobs._table(model.storage.schema.TABLE))).fetchall()
    return sha256((jobs_digest(jobs)+repr(rows)).encode()).hexdigest()


def save(name, value):
    root = os.environ.get('OSSF_CO2_EXECUTION_QUERY_EVIDENCE')
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
    return model.Co2ExecutionQuery(worker.checkpoints, worker.results), worker, job_id, raw, value


def readonly(value):
    value[4]['scopes'].difference_update({'simulation_create', 'simulation_execute', 'crop_result_write'})


def forbid(patch):
    calls = reference.producer.reference.forbid(patch)
    calls['SQL_write_attempts']=0
    execute=psycopg.Connection.execute
    def readonly_sql(conn,statement,*args,**kwargs):
        text=statement.as_string(conn) if hasattr(statement,'as_string') else statement
        if text.split(None,1)[0].upper() in ('INSERT','UPDATE','DELETE','TRUNCATE','CREATE','ALTER','DROP','GRANT','REVOKE'):
            calls['SQL_write_attempts']+=1
            pytest.fail('progress query attempted SQL mutation')
        return execute(conn,statement,*args,**kwargs)
    patch.setattr(psycopg.Connection,'execute',readonly_sql)
    def block(key):
        calls[key] = 0
        def fail(*a, **kw):
            calls[key] += 1; pytest.fail('progress query invoked ' + key)
        return fail
    for cls, name in ((model.checkpoints.Co2ExecutionCheckpointStore, 'confirm'),
            (model.custody.Co2ServerCustody, 'advance'),
            (model.storage.Co2ResultStore, 'put'),
            (model.storage.Co2ResultStore, '_put_in_transaction')):
        patch.setattr(cls, name, block(name))
    for name in ('submit', 'claim', 'renew', 'fail', 'cancel', 'ack_cancel', '_event', '_outcome', '_insert_publication', '_durable_artifact'):
        patch.setattr(model.checkpoints.execution.JobStore, name, block('jobs.' + name))
    return calls


def read(query, job_id):
    raw = query.read('tenant-1', job_id)
    assert raw == model.storage._canonical(json.loads(raw)) and len(raw) <= model.MAX_RESPONSE_BYTES
    result = json.loads(raw); assert model.ExecutionRead.model_validate(result).model_dump(mode='json') == result
    assert set(result) == {'version', 'scope', 'G0_G4', 'rights_or_gate_approval', 'job', 'cancel_requested', 'observed_at', 'checkpoint_status', 'checkpoint', 'result'}
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
    value[4]['scopes'].update({'simulation_execute', 'crop_result_write'})
    worker.checkpoints.confirm('tenant-1', job_id, attempt=lease['attempt'], lease_token=lease['lease_token'])
    readonly(value); after_confirmation = persisted_digest(worker.jobs)
    intent, _, _ = reference.producer.locations(worker.server, raw)
    with exclusive_locks(worker.server.directory/'.custody-lock', intent/'.intent-lock'):
        with monkeypatch.context() as patch:
            calls = forbid(patch); busy = read(query, job_id)
    for result in (mismatch, busy):
        assert result['checkpoint_status'] == 'unavailable' and result['checkpoint'] is result['result'] is None
    assert persisted_digest(worker.jobs) == after_confirmation != before
    assert read(query, job_id)['checkpoint_status'] == 'current'
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
        assert response['result'] == {'result_id': outcome.result_id, 'farm': expected_farm, 'status': progress['status'], 'provenance_sha256':progress['provenance_sha256'], 'rights_or_gate_approval':False}
        assert response['checkpoint']['computed_through_utc'] == progress['times']['last_confirmed']['at']
        assert response['checkpoint']['artifact_sha256'] == progress['artifact_sha256']
        assert all(n == 0 for n in calls.values())
    assert persisted_digest(worker.jobs) == before
    evidence = {'response': response, 'calls': calls, 'query_database_unchanged': True,
        'publication_count': len(reference.rows(worker, job_id, 'job_publications'))}
    assert evidence['publication_count'] == (1 if outcome.state == 'succeeded' else 0)
    evidence['independent_fresh_reader']='separate required native query-fresh cases'
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
        with pytest.raises(model.Co2ExecutionQueryHold): query.read('tenant-1', job_id)
    rights.allowed = True
    assert persisted_digest(worker.jobs) == before and all(n == 0 for n in calls.values())
    save('rights', {'read_scopes_without_create_execute_write': True, 'scope_rejections': 2,
        'late_source_rights_rejected': True, 'calls': calls, 'query_database_unchanged': True})


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
        with pytest.raises(model.Co2ExecutionQueryHold): query.read('tenant-1', job_id)
    assert persisted_digest(worker.jobs) == before and all(n == 0 for n in calls.values())
    save('corrupt-' + fault, {'appended_owned_fault_only': True, 'existing_immutable_records_unchanged': True, 'calls': calls, 'query_database_unchanged': True})


@reference.pytestmark
@pytest.mark.usefixtures('query_cleanup')
def test_binding_bad_ids_and_dependency_drift_are_rejected(setup, monkeypatch):
    query, worker, job_id, _, value = setup; readonly(value)
    before = persisted_digest(worker.jobs); original = query.results
    with monkeypatch.context() as patch:
        calls = forbid(patch)
        for bad in (None, uuid4(), 'bad', str(uuid4()).upper()):
            with pytest.raises(ValueError, match='^co2 execution query request rejected$'): query.read('tenant-1', bad)
        with pytest.raises(model.Co2ExecutionQueryHold): model.Co2ExecutionQuery(object(), worker.results)
        query.results = object()
        try:
            with pytest.raises(model.Co2ExecutionQueryHold): query.read('tenant-1', job_id)
        finally: query.results = original
        assert not any(calls.values())
    assert persisted_digest(worker.jobs) == before
    save('binding', {'invalid_ids': 4, 'fixed_dependencies': True, 'query_database_unchanged': True, 'calls': calls})


@reference.pytestmark
@pytest.mark.usefixtures('query_cleanup')
def test_rights_job_change_during_read_is_pending_without_partial_response(setup, monkeypatch):
    query, worker, job_id, _, value = setup; readonly(value)
    terminal = query._terminal; actor = []; owner_execute=psycopg.Connection.execute
    with monkeypatch.context() as patch:
        calls = forbid(patch)
        def drift(*a, **kw):
            result = terminal(*a, **kw)
            with worker.jobs.connect() as conn:
                owner_execute(conn,sql.SQL("UPDATE {} SET state='canceled',reason=%s::jsonb,updated_at=clock_timestamp() WHERE tenant_id=%s AND job_id=%s")
                    .format(worker.jobs._table('jobs')), (json.dumps({'code':'canceled_by_request'}), 'tenant-1', job_id))
            actor.append('cancel'); return result
        patch.setattr(query, '_terminal', drift)
        with pytest.raises(model.Co2ExecutionQueryPending): query.read('tenant-1', job_id)
    assert actor == ['cancel'] and all(n == 0 for n in calls.values())
    save('job-drift', {'separate_actor_cancel': 1, 'pending_no_partial_response': True, 'query_calls': calls})


@reference.pytestmark
@pytest.mark.usefixtures('query_cleanup')
def test_source_rights_revoked_during_serialization_rejects_response(setup, monkeypatch):
    query, worker, job_id, _, value = setup
    readonly(value); rights = value[5]
    original = model.ExecutionRead.model_validate
    before = persisted_digest(worker.jobs)
    with monkeypatch.context() as patch:
        calls = forbid(patch)
        def revoke(cls, *args, **kwargs):
            result = original(*args, **kwargs)
            rights.allowed = False
            return result
        patch.setattr(model.ExecutionRead, 'model_validate', classmethod(revoke))
        with pytest.raises(model.Co2ExecutionQueryHold):
            query.read('tenant-1', job_id)
    rights.allowed = True
    assert persisted_digest(worker.jobs) == before and all(n == 0 for n in calls.values())
    save('serialization-rights', {'late_source_revocation_rejected': True, 'calls': calls, 'query_database_unchanged': True})


@reference.pytestmark
@pytest.mark.usefixtures('query_cleanup')
def test_terminal_bundle_faults_reject_without_mutation(setup, monkeypatch):
    query, worker, job_id, _, value = setup
    assert worker.run_once(job_id).state == 'succeeded'
    readonly(value); original = query._bundle
    before = persisted_digest(worker.jobs); rejected = []
    for fault in ('link-provenance', 'link-approval', 'publication', 'outcome', 'terminal'):
        with monkeypatch.context() as patch:
            calls = forbid(patch)
            def altered(*args, **kwargs):
                bundle = deepcopy(original(*args, **kwargs))
                if fault == 'link-provenance': bundle[2][0]['reason']['provenance_sha256'] = '0' * 64
                elif fault == 'link-approval': bundle[2][0]['reason']['rights_or_gate_approval'] = True
                elif fault == 'publication': bundle[3][0]['artifact_sha256'] = '0' * 64
                elif fault == 'outcome': bundle[4][0]['termination_reason'] = 'unexpected'
                else: bundle[5][0]['reason'] = {'code': 'unexpected'}
                return bundle
            patch.setattr(query, '_bundle', altered)
            with pytest.raises(model.Co2ExecutionQueryHold):
                query.read('tenant-1', job_id)
            assert all(n == 0 for n in calls.values())
        rejected.append(fault)
    assert persisted_digest(worker.jobs) == before
    save('terminal-faults', {'returned_bundle_fault_injections': rejected, 'query_database_unchanged': True, 'calls': calls})


@reference.pytestmark
@pytest.mark.usefixtures('query_cleanup')
@pytest.mark.parametrize('keep_competing_lock', [False, True])
def test_checkpoint_lock_is_released_during_followup_checks(setup, monkeypatch, keep_competing_lock):
    query, worker, job_id, raw, value = setup
    lease = confirm(worker, job_id)
    worker.server.advance('tenant-1', raw, budget=2)
    first = worker.checkpoints.confirm('tenant-1', job_id,
        attempt=lease['attempt'], lease_token=lease['lease_token'])
    readonly(value); before = persisted_digest(worker.jobs)
    terminal = query._terminal; owners = []
    intent, _, _ = reference.producer.locations(worker.server, raw)
    def competing_open(*args, **kwargs):
        result = terminal(*args, **kwargs)
        other = exclusive_locks(worker.server.directory/'.custody-lock', intent/'.intent-lock')
        other.__enter__();owners.append(other)
        if not keep_competing_lock:
            other.__exit__(None, None, None);owners.clear()
        return result
    try:
        with monkeypatch.context() as patch:
            calls = forbid(patch);patch.setattr(query, '_terminal', competing_open)
            if keep_competing_lock:
                with pytest.raises(model.Co2ExecutionQueryPending):read(query, job_id)
            else:
                result = read(query, job_id)
                assert result['checkpoint_status'] == 'current'
                assert result['checkpoint']['head_sha256'] == first['checkpoint']['head_sha256']
                assert result['checkpoint']['computed_through_utc'] == first['checkpoint']['computed_through_utc']
            assert all(n == 0 for n in calls.values())
    finally:
        for other in reversed(owners):other.__exit__(None, None, None)
    assert persisted_digest(worker.jobs) == before
    save('lock-'+str(keep_competing_lock), {'competing_lock_retained': keep_competing_lock,
        'unlocked_followup_checked': True, 'calls': calls, 'query_database_unchanged': True})


@reference.pytestmark
@pytest.mark.usefixtures('query_cleanup')
@pytest.mark.parametrize('change', ['signed_advance', 'corrupt'])
def test_checkpoint_changed_after_snapshot_never_returns_partial_response(setup, monkeypatch, change):
    query, worker, job_id, raw, value = setup
    lease = confirm(worker, job_id)
    worker.server.advance('tenant-1', raw, budget=2)
    worker.checkpoints.confirm('tenant-1', job_id,
        attempt=lease['attempt'], lease_token=lease['lease_token'])
    _, artifact, _ = reference.producer.locations(worker.server, raw)
    path = artifact/'HEAD';first = path.read_bytes();mode = path.stat().st_mode & 0o777
    worker.server.advance('tenant-1', raw, budget=2)
    following = path.read_bytes()
    assert following != first
    def publish(data):
        path.chmod(0o600);path.write_bytes(data);path.chmod(mode)
    publish(first)
    terminal = query._terminal
    def moved(*args, **kwargs):
        result = terminal(*args, **kwargs)
        publish(following if change == 'signed_advance' else b'{"untrusted":true}')
        return result
    readonly(value);before = persisted_digest(worker.jobs)
    try:
        with monkeypatch.context() as patch:
            calls = forbid(patch);patch.setattr(query, '_terminal', moved)
            expected = model.Co2ExecutionQueryPending if change == 'signed_advance' else model.Co2ExecutionQueryHold
            with pytest.raises(expected):read(query, job_id)
            assert all(n == 0 for n in calls.values())
    finally:publish(following)
    assert persisted_digest(worker.jobs) == before
    save('head-'+change, {'owned_HEAD_fault': change, 'partial_response_rejected': True,
        'calls': calls, 'query_database_unchanged': True})


@reference.pytestmark
@pytest.mark.usefixtures('query_cleanup')
def test_checkpoint_directory_identity_survives_the_unlocked_interval(setup, monkeypatch):
    import shutil
    query, worker, job_id, raw, value = setup
    lease = confirm(worker, job_id)
    worker.server.advance('tenant-1', raw, budget=2)
    worker.checkpoints.confirm('tenant-1', job_id,
        attempt=lease['attempt'], lease_token=lease['lease_token'])
    intent, _, _ = reference.producer.locations(worker.server, raw)
    moved = worker.server.directory.parent/'progress-reader-original-intent'
    terminal = query._terminal; swapped = []
    def replace_directory(*args, **kwargs):
        result = terminal(*args, **kwargs)
        intent.rename(moved);shutil.copytree(moved, intent);swapped.append(True)
        return result
    readonly(value);before = persisted_digest(worker.jobs)
    try:
        with monkeypatch.context() as patch:
            calls = forbid(patch);patch.setattr(query, '_terminal', replace_directory)
            with pytest.raises(model.Co2ExecutionQueryHold):read(query, job_id)
            assert swapped == [True] and all(n == 0 for n in calls.values())
    finally:
        if moved.exists():
            shutil.rmtree(intent);moved.rename(intent)
    assert persisted_digest(worker.jobs) == before
    save('directory', {'owned_directory_swap_denied': True, 'calls': calls,
        'query_database_unchanged': True})
