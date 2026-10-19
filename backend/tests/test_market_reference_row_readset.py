"""Owned real-SCRAM primitive checks; product verifier integration is separate."""
from contextvars import copy_context
from concurrent.futures import ThreadPoolExecutor
from hashlib import sha256
from types import SimpleNamespace
import asyncio
import json

import psycopg
from psycopg import sql
import pytest

from app import market_reference_row_readset as model
from test_market_current_reference_bundle import (
    replay_trace, registration, authoring, profiles, login_database,
    original_login_scope, login_scope, query_cleanup, pytestmark)


@pytest.fixture
def harness(replay_trace, monkeypatch):
    store, tenant, trace, principal = replay_trace
    key = next(args for name, args, _ in trace if name == 'get_economic_input')
    source_keys, candidate_keys = (('economic_input', *key),), (key,)
    def run(consume, sources=source_keys, candidates=candidate_keys):
        def primitive(owner, selected, slot, _):
            bundle = model.bundles._Bundle(owner, selected, slot, owner._reference_reader(selected))
            bundle.token = slot.set(bundle)
            try:
                return model.verify_rows(owner, selected, sources, candidates, consume)
            finally:
                bundle.close()
        with monkeypatch.context() as patch:
            patch.setattr(model.bundles, '_verify_trace', primitive)
            return store.verify_current_reads(tenant, trace)
    return store, tenant, source_keys, candidate_keys, principal, run


def test_actual_exact_present_absent_rows_and_closed_reader(harness, monkeypatch):
    store, tenant, sources, candidates, _, run = harness
    queries, retained, calls = [], [], []
    execute = psycopg.Connection.execute
    def observe(conn, query, params=None, **kwargs):
        calls.append(1)
        text = query.as_string(conn) if hasattr(query, 'as_string') else query
        assert text.split(None, 1)[0].upper() not in {'INSERT', 'UPDATE', 'DELETE', 'CREATE', 'ALTER', 'DROP', 'GRANT', 'REVOKE'}
        if 'WITH m AS MATERIALIZED' in text:
            queries.append((params, text))
        return execute(conn, query, params, **kwargs)
    monkeypatch.setattr(psycopg.Connection, 'execute', observe)
    def consume(reader):
        assert reader.conn.pgconn.used_password
        assert reader.conn.info.get_parameters()['require_auth'] == 'scram-sha-256'
        before = len(calls)
        row = reader.source_row(reader.conn, tenant, *sources[0])
        assert row['tenant_id'] == tenant and row['payload_raw'] == row['source_job_input_bytes']
        assert sha256(row['payload_raw']).hexdigest() == row['payload_sha256'] == row['source_job_input_sha256']
        assert reader.candidate_row(reader.conn, tenant, *candidates[0]) is None
        row.clear()
        assert reader.source_row(reader.conn, tenant, *sources[0])['tenant_id'] == tenant
        assert len(calls) == before
        retained.append(reader)
    assert run(consume) is None
    assert len(queries) == 4
    assert queries[0][0] == ([sources[0][0]], [sources[0][1]], [sources[0][2]], tenant, model.MAX_BYTES)
    assert queries[1][0] == ([candidates[0][0]], [candidates[0][1]], tenant, model.MAX_BYTES)
    assert all('JOIN unnest(' in text for _, text in queries)
    reader = retained[0]
    assert not reader.active and reader.rows is reader.conn is reader.reader is None
    with pytest.raises(ValueError): reader.source_row(None, tenant, *sources[0])
    assert model._active.get() is store._reference_bundle.get() is store._scoped_reader.get() is None


@pytest.mark.parametrize('change', ['source_metadata', 'source_job', 'candidate_appears', 'grant',
                                   'principal', 'source_deleted', 'source_replaced', 'candidate_deleted'])
def test_late_current_changes_reject_the_outer_verifier(harness, login_scope, change):
    store, tenant, sources, candidates, principal, run = harness
    base, policy, _ = login_scope
    retained, returned = [], []
    if change == 'candidate_deleted':
        with base.connect() as conn:
            source, candidate = sql.Identifier(policy.schema, 'market_source_records'), sql.Identifier(policy.schema, 'market_candidate_inputs')
            conn.execute(sql.SQL('INSERT INTO {}(tenant_id,input_id,revision,payload_raw,payload_sha256) SELECT tenant_id,record_id,revision,payload_raw,payload_sha256 FROM {} WHERE tenant_id=%s AND kind=%s AND record_id=%s AND revision=%s')
                         .format(candidate, source), (tenant, *sources[0]))
    def consume(reader):
        retained.append(reader)
        row = reader.source_row(reader.conn, tenant, *sources[0])
        if change == 'principal':
            principal['scopes'].discard('market_source_read')
            return
        with base.connect() as conn:
            source = sql.Identifier(policy.schema, 'market_source_records')
            if change == 'grant':
                conn.execute(sql.SQL('GRANT UPDATE ON {} TO {}').format(source, sql.Identifier(policy.roles['authority'])))
            elif change == 'source_metadata':
                conn.execute(sql.SQL('ALTER TABLE {} DISABLE TRIGGER USER').format(source))
                conn.execute(sql.SQL('UPDATE {} SET recorded_at=recorded_at+interval \'1 microsecond\' WHERE tenant_id=%s AND kind=%s AND record_id=%s AND revision=%s')
                             .format(source), (tenant, *sources[0]))
            elif change == 'source_job':
                target = sql.Identifier(policy.schema, 'jobs')
                conn.execute(sql.SQL('ALTER TABLE {} DISABLE TRIGGER USER').format(target))
                raw = b'{}'
                conn.execute(sql.SQL('UPDATE {} SET input_bytes=%s,input_sha256=%s WHERE tenant_id=%s AND job_id=%s')
                             .format(target), (raw, sha256(raw).hexdigest(), tenant, row['job_id']))
            elif change == 'source_deleted':
                conn.execute(sql.SQL('ALTER TABLE {} DISABLE TRIGGER USER').format(source))
                conn.execute(sql.SQL('DELETE FROM {} WHERE tenant_id=%s AND kind=%s AND record_id=%s AND revision=%s')
                             .format(source), (tenant, *sources[0]))
            elif change == 'source_replaced':
                conn.execute(sql.SQL('ALTER TABLE {} DISABLE TRIGGER USER').format(source))
                conn.execute(sql.SQL('DELETE FROM {} WHERE tenant_id=%s AND kind=%s AND record_id=%s AND revision=%s')
                             .format(source), (tenant, *sources[0]))
                conn.execute(sql.SQL('INSERT INTO {}(tenant_id,kind,record_id,revision,job_id,payload_raw,payload_sha256,store_version,admission_kind,admitted_by,recorded_at) VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,clock_timestamp())')
                             .format(source), tuple(row[k] for k in ('tenant_id','kind','record_id','revision','job_id','payload_raw','payload_sha256','store_version','admission_kind','admitted_by')))
            elif change == 'candidate_deleted':
                target = sql.Identifier(policy.schema, 'market_candidate_inputs')
                assert reader.candidate_row(reader.conn, tenant, *candidates[0]) is not None
                conn.execute(sql.SQL('ALTER TABLE {} DISABLE TRIGGER USER').format(target))
                conn.execute(sql.SQL('DELETE FROM {} WHERE tenant_id=%s AND input_id=%s AND revision=%s')
                             .format(target), (tenant, *candidates[0]))
            else:
                target = sql.Identifier(policy.schema, 'market_candidate_inputs')
                conn.execute(sql.SQL('INSERT INTO {}(tenant_id,input_id,revision,payload_raw,payload_sha256) VALUES(%s,%s,%s,%s,%s)')
                             .format(target), (tenant, *candidates[0], row['payload_raw'], row['payload_sha256']))
    with pytest.raises((ValueError, PermissionError)):
        returned.append(run(consume))
    assert not returned and retained and not retained[0].active and retained[0].rows is None
    assert model._active.get() is store._reference_bundle.get() is store._scoped_reader.get() is None


@pytest.mark.parametrize('change', ['unknown_key', 'nested', 'copied', 'thread', 'exception', 'code',
                                   'keys', 'connection', 'tenant', 'slot', 'task', 'copied_close',
                                   'other_connection', 'provider', 'table_method', 'nonempty_result'])
def test_failed_lifetimes_cannot_return_or_authorize_next_operation(harness, monkeypatch, change):
    store, tenant, sources, candidates, _, run = harness
    retained = []
    with monkeypatch.context() as changes:
        def consume(reader):
            retained.append(reader)
            if change == 'exception': raise RuntimeError('owned interruption')
            if change == 'connection': reader.conn.close(); return
            if change == 'keys': reader.keys = ((), ()); return
            if change == 'code': changes.setattr(model, 'CODE_SHA256', '0'*64); return
            if change == 'slot': changes.setattr(model, '_active', type(model._active)('changed', default=None)); return
            if change == 'provider': changes.setattr(store, '_principal_provider', lambda: {}); return
            if change == 'table_method': changes.setattr(store, '_table', lambda name: sql.Identifier('changed', name)); return
            if change == 'nonempty_result': return {'not_a_public_result': True}
            with pytest.raises(ValueError):
                if change == 'unknown_key': reader.source_row(reader.conn, tenant, 'economic_input', 'unknown', 'r1')
                elif change == 'nested': model.verify_rows(store, tenant, sources, candidates, lambda _: None)
                elif change == 'copied': copy_context().run(reader.source_row, reader.conn, tenant, *sources[0])
                elif change == 'copied_close': copy_context().run(reader._close)
                elif change == 'tenant': reader.source_row(reader.conn, 'foreign', *sources[0])
                elif change == 'other_connection': reader.source_row(object(), tenant, *sources[0])
                elif change == 'task':
                    async def copied(): reader.source_row(reader.conn, tenant, *sources[0])
                    asyncio.run(copied())
                else:
                    context = copy_context()
                    with ThreadPoolExecutor(max_workers=1) as pool:
                        pool.submit(context.run, reader.source_row, reader.conn, tenant, *sources[0]).result(timeout=10)
        with pytest.raises((ValueError, RuntimeError, psycopg.Error)):
            run(consume)
    assert retained and not retained[0].active and retained[0].rows is None
    assert model._active.get() is store._reference_bundle.get() is store._scoped_reader.get() is None
    assert run(lambda reader: None) is None


@pytest.mark.parametrize('bad', ['duplicate', 'unknown_kind', 'too_many', 'wrong_shape', 'empty'])
def test_invalid_closed_key_sets_reject_before_query_or_callback(harness, monkeypatch, bad):
    _, _, sources, candidates, _, run = harness
    chosen = {'duplicate': sources*2, 'unknown_kind': (('unknown', 'id', 'r1'),),
              'too_many': tuple(('economic_input', str(i), 'r1') for i in range(model.MAX_KEYS+1)),
              'wrong_shape': (('economic_input', 'id'),), 'empty': ()}[bad]
    calls = []
    with pytest.raises(ValueError): run(lambda reader: calls.append(1), chosen, () if bad == 'empty' else candidates)
    assert not calls and model._active.get() is None


def test_primitive_cannot_start_outside_the_owned_pure_bundle(harness):
    store, tenant, sources, candidates, _, _ = harness
    with pytest.raises(ValueError): model.verify_rows(store, tenant, sources, candidates, lambda reader: None)
    assert model._active.get() is None


def test_absent_source_is_distinct_from_an_unrequested_key(harness):
    _, tenant, _, _, _, run = harness
    missing = ('economic_input', 'absent-owned-primitive-key', 'r1')
    def consume(reader):
        assert reader.source_row(reader.conn, tenant, *missing) is None
    assert run(consume, (missing,), ()) is None


def test_invalid_source_job_is_rejected_before_consumer(harness, login_scope):
    _, tenant, sources, candidates, _, run = harness
    base, policy, _ = login_scope
    with base.connect() as conn:
        jobs, source = sql.Identifier(policy.schema, 'jobs'), sql.Identifier(policy.schema, 'market_source_records')
        conn.execute(sql.SQL('ALTER TABLE {} DISABLE TRIGGER USER').format(jobs))
        conn.execute(sql.SQL('UPDATE {} SET stage=\'research\' WHERE tenant_id=%s AND job_id=(SELECT job_id FROM {} WHERE tenant_id=%s AND kind=%s AND record_id=%s AND revision=%s)')
                     .format(jobs, source), (tenant, tenant, *sources[0]))
    calls = []
    with pytest.raises(ValueError): run(lambda reader: calls.append(1), sources, candidates)
    assert not calls and model._active.get() is None


def test_SQL_budget_suppresses_oversized_raw_values_before_client_fetch(harness, login_scope, monkeypatch):
    _, tenant, _, _, _, run = harness
    base, policy, _ = login_scope
    raw = json.dumps({'pad': 'x'*(65536-len('{"pad":""}'))}, separators=(',', ':')).encode()
    assert len(raw) == 65536
    digest = sha256(raw).hexdigest()
    with base.connect() as conn:
        source, jobs = sql.Identifier(policy.schema, 'market_source_records'), sql.Identifier(policy.schema, 'jobs')
        keys = conn.execute(sql.SQL('SELECT kind,record_id,revision,job_id FROM {} WHERE tenant_id=%s AND kind=\'economic_input\' ORDER BY record_id LIMIT 9')
                            .format(source), (tenant,)).fetchall()
        assert len(keys) == 9
        for table in (source, jobs): conn.execute(sql.SQL('ALTER TABLE {} DISABLE TRIGGER USER').format(table))
        for row in keys:
            conn.execute(sql.SQL('UPDATE {} SET payload_raw=%s,payload_sha256=%s WHERE tenant_id=%s AND kind=%s AND record_id=%s AND revision=%s')
                         .format(source), (raw, digest, tenant, row['kind'], row['record_id'], row['revision']))
            conn.execute(sql.SQL('UPDATE {} SET input_bytes=%s,input_sha256=%s WHERE tenant_id=%s AND job_id=%s')
                         .format(jobs), (raw, digest, tenant, row['job_id']))
    execute = psycopg.Connection.execute
    observed, calls = [], []
    def limited(conn, query, params=None, **kwargs):
        cursor = execute(conn, query, params, **kwargs)
        text = query.as_string(conn) if hasattr(query, 'as_string') else query
        if 'WITH m AS MATERIALIZED' not in text: return cursor
        rows = cursor.fetchall()
        observed.append(all(row['ok'] is False and row['payload_raw'] is None
                            and row['source_job_input_bytes'] is None for row in rows))
        return SimpleNamespace(fetchall=lambda: rows)
    monkeypatch.setattr(psycopg.Connection, 'execute', limited)
    with pytest.raises(ValueError):
        run(lambda reader: calls.append(1), tuple((r['kind'], r['record_id'], r['revision']) for r in keys), ())
    assert observed == [True] and not calls and model._active.get() is None
