"""Actual leased calculation, signed original values, and atomic DB completion."""
from contextlib import contextmanager
from hashlib import sha256
import json
import os
from pathlib import Path
import threading
import time
from uuid import uuid4

import psycopg
import pytest
from psycopg import sql

from app import crop_greenhouse_solar_execution_worker as model
from test_crop_greenhouse_solar_result_store import (
    authoring, profiles, login_database, original_login_scope, login_scope,
    KEY, pytestmark, count)
from test_crop_greenhouse_solar_server_custody import setup as producer_setup
import test_crop_greenhouse_solar_server_custody as producer


def save(name, value):
    root = os.environ.get('OSSF_SOLAR_WORKER_EVIDENCE')
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
    admission = model.checkpoints.execution.SolarExecutionService(server.binding, input_resolver=server.input_resolver)
    checkpoint_store = model.checkpoints.SolarExecutionCheckpointStore(admission, server)
    result_store = model.results.SolarResultStore(server, integrity_key=KEY)
    worker = model.SolarExecutionWorker(checkpoint_store, result_store, tenant_id='tenant-1', chunk_budget=8)
    job = admission.submit('tenant-1', raw)
    return worker, str(job['job_id']), raw, value


def link_provenance(progress, value):
    source=json.loads((value[2][0]/'source.json').read_bytes())
    return progress['provenance_sha256']==sha256(producer.model._canonical(source['provenance'])).hexdigest()


@pytest.mark.parametrize('fault', ['provenance', 'approval'])
def test_current_checkpoint_history_rejects_wrong_provenance_or_approval(setup, monkeypatch, fault):
    from copy import deepcopy
    from types import SimpleNamespace
    worker, job_id, raw, _ = setup
    lease=worker.jobs.claim(600,allowed_stages=('simulation',),tenant_id='tenant-1',job_id=job_id)
    worker.server.advance('tenant-1',raw,budget=1)
    worker._confirm(lease)
    execute=psycopg.Connection.execute;observed=[]
    def injected(conn,query,*args,**kwargs):
        result=execute(conn,query,*args,**kwargs)
        text=query.as_string(conn) if hasattr(query,'as_string') else query
        if text.startswith('SELECT event_id, attempt, reason, recorded_at FROM '):
            rows=deepcopy(result.fetchall());assert rows
            if fault=='provenance':rows[0]['reason']['provenance_sha256']='0'*64
            else:rows[0]['reason']['rights_or_gate_approval']=True
            observed.append(1)
            return SimpleNamespace(fetchall=lambda:rows)
        return result
    with monkeypatch.context() as patch:
        calls=producer.reference.forbid(patch)
        patch.setattr(psycopg.Connection,'execute',injected)
        with pytest.raises(model.checkpoints.SolarCheckpointHold):worker._confirm(lease)
        assert all(v==0 for v in calls.values())
    assert observed and len([r for r in rows(worker,job_id,'job_events') if r['kind']==model.checkpoints.EVENT_KIND])==1
    save('history-'+fault,{'wrong_reference_denied':True,'actual_DB_mutation':False,'calls':calls})


def rows(worker, job_id, table):
    with worker.jobs.connect() as conn:
        return conn.execute(sql.SQL('SELECT * FROM {} WHERE tenant_id=%s AND job_id=%s')
            .format(worker.jobs._table(table)), ('tenant-1', job_id)).fetchall()


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
    original_advance = producer.model.SolarServerCustody._advance_for_checkpoint
    original_confirm = model.SolarExecutionWorker._confirm
    original_before = model.SolarExecutionWorker._before
    def timed_advance(instance, *a, **kw):
        start = time.monotonic(); result = original_advance(instance, *a, **kw); end = time.monotonic()
        assert result is None
        chunks.append({'start':start-origin, 'end':end-origin, 'seconds':end-start,
                       'budget':kw['budget']})
        return result
    def timed_confirm(instance, *a, **kw):
        result = original_confirm(instance, *a, **kw)
        if chunks and 'steps' not in chunks[-1]: chunks[-1]['steps'] = result['checkpoint']['steps']
        return result
    def timed_before(instance, *a, **kw):
        start = time.monotonic(); result = original_before(instance, *a, **kw); end = time.monotonic()
        renewals.append({'start':start-origin, 'end':end-origin, 'seconds':end-start})
        return result
    with monkeypatch.context() as patch:
        calls = producer.measured(patch)
        patch.setattr(producer.model.SolarServerCustody, '_advance_for_checkpoint', timed_advance)
        patch.setattr(model.SolarExecutionWorker, '_confirm', timed_confirm)
        patch.setattr(model.SolarExecutionWorker, '_before', timed_before)
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
    assert progress['G0_G4'] == 'not_assessed' and progress['rights_or_gate_approval'] is False
    assert link_provenance(progress, value)
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
    assert link['provenance_sha256']==progress['provenance_sha256'] and link['rights_or_gate_approval'] is False
    assert len(publications) == (1 if state == 'succeeded' else 0)
    if publications: assert publications[0]['manifest'] == link
    events = [r for r in rows(worker, job_id, 'job_events') if r['kind'] == model.checkpoints.EVENT_KIND]
    events.sort(key=lambda r: r['reason']['publication_sequence'])
    assert [r['reason']['publication_sequence'] for r in events] == [1, 2, 3]
    assert events[-1]['reason']['head_sha256'] == progress['head_sha256']
    assert events[-1]['reason']['provenance_sha256']==progress['provenance_sha256'] and events[-1]['reason']['rights_or_gate_approval'] is False
    summary = worker.results.summary('tenant-1', outcome.result_id, value[1]['farm'])
    after = producer.reference.counts(binding)
    assert after[0] == before[0] and after[2:] == before[2:] == (0, 0)
    assert after[1] - before[1] == len(rows(worker, job_id, 'job_events')) - 1
    save('normal-' + status, {'progress': progress, 'calls': calls, 'read_calls': read_calls,
        'independent_fresh_reader': 'separate sequential-process test', 'result_link': link,
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
        original = producer.model.SolarServerCustody._advance_for_checkpoint
        def cancel(server, *a, **kw):
            result = original(server, *a, **kw)
            assert worker.jobs.cancel('tenant-1', job_id)
            return result
        monkeypatch.setattr(producer.model.SolarServerCustody, '_advance_for_checkpoint', cancel)
    else:
        worker.server.advance('tenant-1', raw, budget=128)
        original = model.SolarExecutionWorker._finish
        def cancel(instance, *a, **kw):
            assert worker.jobs.cancel('tenant-1', job_id)
            return original(instance, *a, **kw)
        monkeypatch.setattr(model.SolarExecutionWorker, '_finish', cancel)
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
        measured = producer.model.SolarServerCustody._advance_for_checkpoint
        def lost(server, *a, **kw):
            result = measured(server, *a, **kw); expire(worker, job_id); return result
        patch.setattr(producer.model.SolarServerCustody, '_advance_for_checkpoint', lost)
        first = worker.run_once(job_id)
    assert first.state == 'unclosed' and first.result_id is None
    progress = json.loads(worker.server.inspect('tenant-1', raw))
    no_published_result(worker, job_id)
    assert not any(r['kind'] == model.checkpoints.EVENT_KIND for r in rows(worker, job_id, 'job_events'))
    adopted = []; confirm = model.checkpoints.SolarExecutionCheckpointStore.confirm
    with monkeypatch.context() as patch:
        remaining = producer.measured(patch)
        def accept(store, *a, **kw):
            record = confirm(store, *a, **kw)
            adopted.append((record['checkpoint']['head_sha256'], dict(remaining)))
            return record
        patch.setattr(model.checkpoints.SolarExecutionCheckpointStore, 'confirm', accept)
        final = worker.run_once(job_id)
    assert final.state == 'succeeded' and final.attempt == 2
    assert adopted[0][0] == progress['head_sha256'] and all(n == 0 for n in adopted[0][1].values())
    assert calls['step'] + remaining['step'] == 16 and remaining['start'] == 0
    assert [r['state'] for r in sorted(rows(worker, job_id, 'attempt_outcomes'), key=lambda r:r['attempt'])] == ['lease_expired', 'succeeded']
    save('expiry', {'private_prefix': progress, 'first_calls': calls, 'remaining_calls': remaining,
        'first_adoption_calls_zero': adopted[0][1], 'final_state': final.state, 'final_attempt': final.attempt})



@pytest.mark.parametrize('fault', ['event', 'final_update'])
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
            original = model.results.SolarResultStore._put_in_transaction
            @contextmanager
            def fail(instance, *a, **kw):
                with original(instance, *a, **kw) as record: yield record
                hit.append(True); raise RuntimeError('owned post-hook rollback fault')
            patch.setattr(model.results.SolarResultStore, '_put_in_transaction', fail)
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



def test_admission_idempotency_closed_input_and_late_rollback(setup, monkeypatch):
    from app.job_store import JobIntentConflict
    from copy import deepcopy
    worker, job_id, raw, value = setup
    admission = worker.checkpoints.admission
    execution = model.checkpoints.execution
    with monkeypatch.context() as patch:
        calls = producer.reference.forbid(patch)
        assert str(admission.submit('tenant-1', raw)['job_id']) == job_id
        changed = json.loads(raw); changed['rights']['declaration_id'] = 'changed-owned-declaration'
        with pytest.raises(JobIntentConflict):
            admission.submit('tenant-1', execution.documents._canonical(changed))
        changed = json.loads(raw); changed['unexpected'] = True
        for invalid in (b'{', b' '* (execution.MAX_INPUT_BYTES+1), execution.documents._canonical(changed)):
            with pytest.raises(execution.SolarExecutionHold):
                admission.submit('tenant-1', invalid)
        before = {name:len(rows(worker, job_id, name)) for name in ('jobs','job_events','job_attempts')}
        with worker.jobs.connect() as conn:
            all_before = tuple(conn.execute(sql.SQL('SELECT count(*) AS n FROM {}').format(
                worker.jobs._table(name))).fetchone()['n'] for name in ('jobs','job_events','job_attempts'))
        original = worker.jobs._event; inserted = []
        def event(conn, tenant, job, kind, *a, **kw):
            original(conn, tenant, job, kind, *a, **kw)
            if kind == 'submitted':
                inserted.append(str(job)); value[-1].allowed = False
        patch.setattr(worker.jobs, '_event', event)
        changed = deepcopy(json.loads(raw)); changed['revision'] = 'r2'
        try:
            with pytest.raises((PermissionError, execution.SolarExecutionHold)):
                admission.submit('tenant-1', execution.documents._canonical(changed))
        finally:
            value[-1].allowed = True
        with worker.jobs.connect() as conn:
            all_after = tuple(conn.execute(sql.SQL('SELECT count(*) AS n FROM {}').format(
                worker.jobs._table(name))).fetchone()['n'] for name in ('jobs','job_events','job_attempts'))
        assert len(inserted) == 1 and all_before == all_after
        assert before == {name:len(rows(worker, job_id, name)) for name in before}
        assert all(n == 0 for n in calls.values())
    save('admission', {'idempotent':True,'same_revision_conflict':True,
        'closed_input':True,'late_rights_insert_rollback':True,'calls':calls})


def test_checkpoint_duplicate_current_rights_and_original_time_without_numerics(setup, monkeypatch):
    worker, job_id, raw, value = setup
    lease = worker.jobs.claim(600, allowed_stages=('simulation',), tenant_id='tenant-1', job_id=job_id)
    progress = json.loads(worker.server.advance('tenant-1', raw, budget=1))
    def confirm(store):
        return store.confirm('tenant-1', job_id, attempt=lease['attempt'], lease_token=lease['lease_token'])
    with monkeypatch.context() as patch:
        calls = producer.reference.forbid(patch)
        first = confirm(worker.checkpoints)
        assert first == confirm(worker.checkpoints)
        fresh = model.checkpoints.SolarExecutionCheckpointStore(worker.checkpoints.admission, worker.server)
        assert first == confirm(fresh)
        assert worker.jobs.renew('tenant-1', job_id, lease['attempt'], lease['lease_token'], 600)
        assert first == confirm(fresh)
        assert first['checkpoint']['head_sha256'] == progress['head_sha256']
        assert first['checkpoint']['computed_through_utc'] == progress['times']['last_confirmed']['at']
        value[-1].allowed = False
        try:
            with pytest.raises((PermissionError, model.checkpoints.SolarCheckpointHold)):
                confirm(fresh)
        finally:
            value[-1].allowed = True
        assert first == confirm(fresh)
        assert all(n == 0 for n in calls.values())
    events = [r for r in rows(worker, job_id, 'job_events') if r['kind'] == model.checkpoints.EVENT_KIND]
    assert len(events) == 1 and count(worker.server.binding) == 0
    assert rows(worker, job_id, 'job_publications') == []
    save('checkpoint', {'same_original_event':True,'same_original_UTC':True,
        'late_rights_denied':True,'publications':0,'calls':calls})


@pytest.mark.parametrize('point', [
    'before', 'confirm_before', 'confirm_after', 'finish_before', 'finish_after', 'result_after'])
def test_cancel_commits_during_evidence_validation(setup, monkeypatch, point):
    worker, job_id, raw, _ = setup
    lease = worker.jobs.claim(600, allowed_stages=('simulation',), tenant_id='tenant-1', job_id=job_id)
    if point != 'before':
        worker.server.advance('tenant-1', raw, budget=128)
    confirmed = worker._confirm(lease) if point.startswith('finish') or point == 'result_after' else None
    original_events = len(rows(worker, job_id, 'job_events'))
    owner = model.results.SolarResultStore if point == 'result_after' else model.checkpoints.SolarExecutionCheckpointStore
    original = owner._current
    entered, release = threading.Event(), threading.Event()
    current_calls, outcomes, errors = [], [], []
    pause_at = 2 if point.endswith('after') else 1

    def validating(instance, *args, **kwargs):
        result = original(instance, *args, **kwargs)
        current_calls.append(True)
        if len(current_calls) == pause_at:
            entered.set()
            assert release.wait(30), 'concurrency fixture was not released'
        return result

    def execute():
        try:
            if point == 'before': outcomes.append(worker._before(lease))
            elif point.startswith('confirm'): outcomes.append(worker._confirm(lease))
            else: outcomes.append(worker._finish(lease, confirmed))
        except BaseException as exc:
            errors.append(exc)

    monkeypatch.setattr(owner, '_current', validating)
    thread = threading.Thread(target=execute)
    thread.start()
    try:
        assert entered.wait(30), 'worker did not reach validation'
        started = time.monotonic()
        assert worker.checkpoints.admission.cancel('tenant-1', job_id)
        cancel_seconds = time.monotonic() - started
        assert cancel_seconds < 5
        assert not release.is_set() and thread.is_alive()
        assert worker.jobs.get_job('tenant-1', job_id)['cancel_requested']
    finally:
        release.set()
        thread.join(30)
        assert not thread.is_alive()
    assert not outcomes and len(errors) == 1
    assert isinstance(errors[0], model.checkpoints.SolarCheckpointLeaseLost)
    assert worker._lost(lease).state == 'canceled'
    no_published_result(worker, job_id)
    events = rows(worker, job_id, 'job_events')
    assert len(events) == original_events + 2
    assert [r['kind'] for r in events].count('cancel_requested') == 1
    assert rows(worker, job_id, 'attempt_outcomes')[0]['state'] == 'canceled'
    save('cancel-validation-' + point, {'point': point, 'accepted_during_validation': True,
        'cancel_seconds': cancel_seconds, 'worker_acknowledged': True,
        'partial_checkpoint_and_results_rolled_back': True,
        'fixture_barrier': True, 'native_browser_acceptance': False})


@pytest.mark.parametrize('point,change', [('confirm', 'input'), ('finish', 'expire')])
def test_unlocked_validation_rejects_changed_input_or_expired_lease(setup, monkeypatch, point, change):
    worker, job_id, raw, _ = setup
    lease = worker.jobs.claim(600, allowed_stages=('simulation',), tenant_id='tenant-1', job_id=job_id)
    worker.server.advance('tenant-1', raw, budget=128)
    confirmed = worker._confirm(lease) if point == 'finish' else None
    original_events = len(rows(worker, job_id, 'job_events'))
    original = model.checkpoints.SolarExecutionCheckpointStore._current
    calls = []

    def changed(instance, *args, **kwargs):
        result = original(instance, *args, **kwargs)
        calls.append(True)
        if len(calls) == 2:
            if change == 'expire': expire(worker, job_id)
            else:
                value = json.loads(rows(worker, job_id, 'jobs')[0]['input_bytes'])
                value['input_resolver_version'] += '-changed'
                new_raw = model.checkpoints.execution.canonical_input_bytes(value)
                with worker.jobs.connect() as conn:
                    conn.execute(sql.SQL('UPDATE {} SET input_bytes=%s,input_sha256=%s WHERE job_id=%s')
                        .format(worker.jobs._table('jobs')), (new_raw, sha256(new_raw).hexdigest(), job_id))
        return result

    monkeypatch.setattr(model.checkpoints.SolarExecutionCheckpointStore, '_current', changed)
    with pytest.raises(model.checkpoints.SolarCheckpointHold):
        if point == 'confirm': worker._confirm(lease)
        else: worker._finish(lease, confirmed)
    assert len(calls) == 2
    no_published_result(worker, job_id)
    assert len(rows(worker, job_id, 'job_events')) == original_events
    assert not rows(worker, job_id, 'attempt_outcomes')
    save('late-validation-' + change, {'point': point, 'change': change,
        'all_checkpoint_and_result_writes_rolled_back': True})


@pytest.mark.parametrize('active', [False, True])
def test_scoped_cancel_preserves_identity_permissions_and_revoked_rights(setup, monkeypatch, active):
    worker, job_id, raw, value = setup
    admission, principal, rights = worker.checkpoints.admission, value[4], value[-1]
    lease = worker.jobs.claim(600, allowed_stages=('simulation',), tenant_id='tenant-1', job_id=job_id) if active else None
    legacy = worker.jobs.submit('tenant-1', 'simulation', {'input_version': 'other-model'}, uuid4().hex)
    assert not admission.cancel('tenant-1', str(legacy['job_id']))
    assert not admission.cancel('tenant-other', job_id)
    principal['scopes'].remove('cancel')
    assert not admission.cancel('tenant-1', job_id)
    principal['scopes'].add('cancel')
    original_scopes = set(principal['scopes'])
    principal['scopes'].difference_update({'simulation_create', 'simulation_execute'})
    rights.allowed = False
    try:
        with monkeypatch.context() as patch:
            calls = producer.reference.forbid(patch)
            assert admission.cancel('tenant-1', job_id)
            if active:
                assert admission.cancel('tenant-1', job_id)
                assert worker._lost(lease).state == 'canceled'
            assert not admission.cancel('tenant-1', job_id)
            assert all(n == 0 for n in calls.values())
    finally:
        principal['scopes'].update(original_scopes); rights.allowed = True
    events = rows(worker, job_id, 'job_events')
    assert [r['kind'] for r in events].count('canceled') == 1
    assert [r['kind'] for r in events].count('cancel_requested') == int(active)
    no_published_result(worker, job_id)
    save('scoped-cancel-' + str(active), {'active': active, 'rights_revoked_cancellation': True,
        'other_model_tenant_scope_and_terminal_denied': True, 'numerical_calls': calls})


@pytest.mark.parametrize('change', ['none', 'cancel', 'expire', 'input'])
def test_before_validation_releases_read_connection_and_fences_changes(setup, monkeypatch, change):
    worker, job_id, raw, _ = setup
    lease = worker.jobs.claim(600, allowed_stages=('simulation',), tenant_id='tenant-1', job_id=job_id)
    connect, current, read_lease = worker.jobs.connect, worker.checkpoints._current, worker.checkpoints._lease
    opened, observed, changed_reads = [], [], []

    def tracked_connect():
        opened[:] = [conn for conn in opened if not conn.closed]
        conn = connect()
        opened.append(conn)
        return conn

    def validating(*args, **kwargs):
        observed.append(all(conn.closed for conn in opened))
        assert observed[-1], 'unlocked lease read connection remained open during source validation'
        result = current(*args, **kwargs)
        if change == 'cancel':
            assert worker.jobs.cancel('tenant-1', job_id)
        elif change == 'expire':
            expire(worker, job_id)
        elif change == 'input':
            changed_reads.append(True)
        return result

    def final_read(*args, **kwargs):
        row = read_lease(*args, **kwargs)
        if changed_reads:
            assert kwargs.get('lock', True)
            row = dict(row)
            value = json.loads(row['input_bytes'])
            value['input_resolver_version'] += '-changed'
            row['input_bytes'] = model.checkpoints.execution.canonical_input_bytes(value)
            row['input_sha256'] = sha256(row['input_bytes']).hexdigest()
        return row

    with monkeypatch.context() as patch:
        calls = producer.reference.forbid(patch)
        patch.setattr(worker.jobs, 'connect', tracked_connect)
        patch.setattr(worker.checkpoints, '_current', validating)
        patch.setattr(worker.checkpoints, '_lease', final_read)
        if change == 'none':
            assert worker._before(lease) == raw
        else:
            with pytest.raises(model.checkpoints.SolarCheckpointHold):
                worker._before(lease)
        assert all(n == 0 for n in calls.values())
    assert observed == [True] and all(conn.closed for conn in opened)
    no_published_result(worker, job_id)
    assert not any(r['kind'] == model.checkpoints.EVENT_KIND for r in rows(worker, job_id, 'job_events'))
    save('before-connection-' + change, {'read_connection_closed_before_current_check':True,
        'late_change':change, 'late_change_denied':change != 'none',
        'numerical_and_CLI_calls':calls, 'checkpoint_and_result_rows':0,
        'test_control_SQL':change in ('cancel','expire'),
        'final_input_read_fault_injection':change == 'input', 'actual_DB_input_mutation':False})
