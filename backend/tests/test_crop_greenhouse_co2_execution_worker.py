"""Actual Co2 worker calculation, retained originals and atomic terminal storage.

Automatic discovery and independent crash/restart are a subsequent child.
"""
from hashlib import sha256
import json
import os
from pathlib import Path
import time

import psycopg
import pytest
from psycopg import sql
from app import crop_greenhouse_co2_execution_worker as model
from test_crop_greenhouse_co2_result_store import (
    authoring, profiles, login_database, original_login_scope, login_scope, KEY, pytestmark, count)
from test_crop_greenhouse_co2_server_custody import setup as producer_setup, settle_owned_database_backends
import test_crop_greenhouse_co2_server_custody as producer


def save(name, value):
    root = os.environ.get('OSSF_CO2_WORKER_EVIDENCE')
    if root:
        if name != 'database-cleanup':
            value = dict(value, actual_scram=True, scope='worker_core_only',
                         independent_fresh_reader=False, actual_SIGKILL=False)
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
    admission = model.checkpoints.execution.Co2ExecutionService(server.binding, input_resolver=server.input_resolver)
    checkpoint_store = model.checkpoints.Co2ExecutionCheckpointStore(admission, server)
    result_store = model.results.Co2ResultStore(server, integrity_key=KEY)
    worker = model.Co2ExecutionWorker(checkpoint_store, result_store, tenant_id='tenant-1', chunk_budget=8)
    with worker.jobs.connect() as conn:
        assert conn.pgconn.used_password
        assert conn.info.get_parameters()['require_auth'] == 'scram-sha-256'
    job = admission.submit('tenant-1', raw)
    return worker, str(job['job_id']), raw, value


def link_provenance(progress, value):
    source=json.loads((value[2][0]/'source.json').read_bytes())
    return progress['provenance_sha256']==sha256(producer.model._canonical(source['provenance'])).hexdigest()


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
    original_advance = producer.model.Co2ServerCustody._advance_for_checkpoint
    original_confirm = model.Co2ExecutionWorker._confirm
    original_before = model.Co2ExecutionWorker._before
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
        patch.setattr(producer.model.Co2ServerCustody, '_advance_for_checkpoint', timed_advance)
        patch.setattr(model.Co2ExecutionWorker, '_confirm', timed_confirm)
        patch.setattr(model.Co2ExecutionWorker, '_before', timed_before)
        outcome = worker.run_once(job_id)
    worker_seconds = time.monotonic() - origin
    renewal_gaps = [b['end']-a['end'] for a,b in zip(renewals,renewals[1:])]
    tail = worker_seconds - renewals[-1]['end']
    assert len(chunks) > 1 and all(0 < p['seconds'] < worker.lease_seconds for p in chunks)
    assert all(0 < t < worker.lease_seconds for t in (*renewal_gaps, tail))
    status = expected['status']; state = 'succeeded' if status == 'completed' else 'hold'
    assert outcome.state == state and outcome.attempt == 1 and outcome.result_id
    assert calls['step'] == 16 and calls['start'] == 1 and calls['restore'] >= 1
    assert calls['CLI'] == 0
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
        'result_link': link,
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
        original = producer.model.Co2ServerCustody._advance_for_checkpoint
        def cancel(server, *a, **kw):
            result = original(server, *a, **kw)
            assert worker.jobs.cancel('tenant-1', job_id)
            return result
        monkeypatch.setattr(producer.model.Co2ServerCustody, '_advance_for_checkpoint', cancel)
    else:
        worker.server.advance('tenant-1', raw, budget=128)
        original = model.Co2ExecutionWorker._finish
        def cancel(instance, *a, **kw):
            assert worker.jobs.cancel('tenant-1', job_id)
            return original(instance, *a, **kw)
        monkeypatch.setattr(model.Co2ExecutionWorker, '_finish', cancel)
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
        measured = producer.model.Co2ServerCustody._advance_for_checkpoint
        def lost(server, *a, **kw):
            result = measured(server, *a, **kw); expire(worker, job_id); return result
        patch.setattr(producer.model.Co2ServerCustody, '_advance_for_checkpoint', lost)
        first = worker.run_once(job_id)
    assert first.state == 'unclosed' and first.result_id is None
    progress = json.loads(worker.server.inspect('tenant-1', raw))
    no_published_result(worker, job_id)
    assert not any(r['kind'] == model.checkpoints.EVENT_KIND for r in rows(worker, job_id, 'job_events'))
    adopted = []; confirm = model.checkpoints.Co2ExecutionCheckpointStore.confirm
    with monkeypatch.context() as patch:
        remaining = producer.measured(patch)
        def accept(store, *a, **kw):
            record = confirm(store, *a, **kw)
            adopted.append((record['checkpoint']['head_sha256'], dict(remaining)))
            return record
        patch.setattr(model.checkpoints.Co2ExecutionCheckpointStore, 'confirm', accept)
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
        if fault == 'event':
            original = type(worker.jobs)._event
            def fail(instance, conn, tenant, job, *args, **kw):
                result = original(instance, conn, tenant, job, *args, **kw)
                if args[0] == 'succeeded':
                    hit.append(True); raise RuntimeError('owned publication rollback fault')
                return result
            patch.setattr(type(worker.jobs), '_event', fail)
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


def test_execution_scope_loss_after_terminal_update_rolls_back_all_results(setup,monkeypatch):
    worker,job,raw,value=setup;worker.server.advance('tenant-1',raw,budget=128)
    execute=psycopg.Connection.execute;updated=[];principal=value[4]
    def revoke(conn,statement,params=None,*args,**kwargs):
        cursor=execute(conn,statement,params,*args,**kwargs)
        text=statement.as_string(conn) if hasattr(statement,'as_string') else statement
        if 'SET state=%s, reason=%s,' in text and params and params[0]=='succeeded':
            assert cursor.rowcount==1;updated.append(1);principal['scopes'].remove('simulation_execute')
        return cursor
    try:
        with monkeypatch.context() as patch:
            calls=producer.reference.forbid(patch)
            patch.setattr(psycopg.Connection,'execute',revoke)
            outcome=worker.run_once(job)
            assert not any(calls.values())
    finally:principal['scopes'].add('simulation_execute')
    assert updated==[1] and outcome.state=='hold' and outcome.result_id is None
    no_published_result(worker,job)
    assert [r['state'] for r in rows(worker,job,'attempt_outcomes')]==['hold']
    save('late-after-update-scope',{'after_successful_terminal_UPDATE':True,
        'result_publication_link_terminal_rolled_back':True,'closure_state':outcome.state,'calls':calls})
