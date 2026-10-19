"""Real-SCRAM raw dependency receipts; no verifier shortcut is enabled."""
from hashlib import sha256
import importlib

import psycopg
import pytest
from psycopg import sql

from app import market_reference_bundle as bundles
from test_market_current_reference_bundle import (
    replay_trace, registration, authoring, profiles, login_database,
    original_login_scope, login_scope, query_cleanup, pytestmark)


@pytest.fixture
def harness(replay_trace, monkeypatch, login_scope):
    store, tenant, trace, principal = replay_trace
    key = next(args for name, args, _ in trace if name == 'get_economic_input')
    source_keys, candidate_keys = (('economic_input', *key),), (key,)
    pin_keys = tuple(dict.fromkeys(args for name, args, _ in trace if name in ('get_market_candidate','get_economic_scenario','get_economic_scenario_pin')))
    base, policy, _ = login_scope
    with base.connect() as conn:
        pin_keys = tuple(key for key in pin_keys if conn.execute(
            sql.SQL('SELECT 1 FROM {} WHERE tenant_id=%s AND scenario_id=%s AND revision=%s')
            .format(sql.Identifier(policy.schema,'market_candidate_pins')),(tenant,*key)).fetchone())
    assert pin_keys
    def run(consume, sources=source_keys, candidates=candidate_keys, pins=pin_keys):
        def primitive(owner, selected, slot, _):
            bundle = bundles._Bundle(owner, selected, slot, owner._reference_reader(selected))
            bundle.token = slot.set(bundle)
            try:
                model = importlib.import_module('app.market_reference_receipts')
                return model.verify_receipts(owner, selected, sources, candidates, pins, consume)
            finally:
                bundle.close()
        with monkeypatch.context() as patch:
            patch.setattr(bundles, '_verify_trace', primitive)
            return store.verify_current_reads(tenant, trace)
    return store, tenant, source_keys, candidate_keys, pin_keys, principal, run


def test_exact_present_absent_receipts_no_payload_and_closed_reader(harness, monkeypatch):
    store, tenant, sources, candidates, pins, _, run = harness
    retained, queries, calls = [], [], []
    execute = psycopg.Connection.execute
    def observe(conn, query, params=None, **kwargs):
        text = query.as_string(conn) if hasattr(query, 'as_string') else query
        calls.append(text)
        assert text.split(None, 1)[0].upper() not in {'INSERT', 'UPDATE', 'DELETE', 'CREATE', 'ALTER', 'DROP', 'GRANT', 'REVOKE'}
        cursor = execute(conn, query, params, **kwargs)
        if 'receipt_keys AS MATERIALIZED' in text:
            rows = cursor.fetchall()
            assert all(set(row) == {'category','kind','identity','revision','bytes','ok','receipt'} for row in rows)
            assert all(type(row['receipt']) is bytes and len(row['receipt']) == 32 for row in rows)
            queries.append((params, rows))
            from types import SimpleNamespace
            return SimpleNamespace(fetchall=lambda: rows)
        return cursor
    monkeypatch.setattr(psycopg.Connection, 'execute', observe)
    def consume(reader):
        retained.append(reader)
        assert reader.conn.pgconn.used_password
        assert reader.conn.info.get_parameters()['require_auth'] == 'scram-sha-256'
        before = len(calls)
        digest = reader.source_receipt(reader.conn, tenant, *sources[0])
        assert type(digest) is bytes and len(digest) == 32
        assert reader.candidate_receipt(reader.conn, tenant, *candidates[0]) is None
        assert all(type(reader.pin_receipt(reader.conn, tenant, *key)) is bytes for key in pins)
        assert reader.source_receipt(reader.conn, tenant, *sources[0]) == digest
        assert len(calls) == before
    assert run(consume) is None
    assert len(queries) == 2
    assert retained and not retained[0].active and retained[0].conn is retained[0].receipts is None
    with pytest.raises(ValueError): retained[0].source_receipt(None, tenant, *sources[0])
    assert store._reference_bundle.get() is store._scoped_reader.get() is None


def test_present_candidate_pin_only_and_missing_source(harness, login_scope):
    _, tenant, sources, candidates, pins, _, run = harness
    base, policy, _ = login_scope
    with base.connect() as conn:
        conn.execute(sql.SQL('INSERT INTO {}(tenant_id,input_id,revision,payload_raw,payload_sha256) SELECT tenant_id,record_id,revision,payload_raw,payload_sha256 FROM {} WHERE tenant_id=%s AND kind=%s AND record_id=%s AND revision=%s')
            .format(sql.Identifier(policy.schema,'market_candidate_inputs'),sql.Identifier(policy.schema,'market_source_records')),
            (tenant,*sources[0]))
    def consume(reader):
        assert len(reader.candidate_receipt(reader.conn,tenant,*candidates[0]))==32
        assert all(len(reader.pin_receipt(reader.conn,tenant,*key))==32 for key in pins)
        assert reader.source_receipt(reader.conn,tenant,'economic_input','absent','r1') is None
        assert reader.pin_receipt(reader.conn,tenant,'absent-pin','r1') is None
    assert run(consume,(('economic_input','absent','r1'),),candidates,(*pins,('absent-pin','r1'))) is None
    assert run(lambda reader: None,(),(),pins) is None


def test_timezone_bytea_output_and_unrelated_foreign_rows_do_not_change_receipts(harness, login_scope):
    _, tenant, sources, candidates, _, _, run = harness
    base, policy, _ = login_scope
    def consume(reader):
        reader.conn.execute("SET LOCAL TimeZone='Asia/Seoul'")
        reader.conn.execute("SET LOCAL bytea_output='escape'")
        with base.connect() as conn:
            target=sql.Identifier(policy.schema,'market_source_records')
            conn.execute(sql.SQL('ALTER TABLE {} DISABLE TRIGGER USER').format(target))
            conn.execute(sql.SQL("UPDATE {} SET recorded_at=recorded_at+interval '1 microsecond' WHERE tenant_id=%s AND record_id<>%s")
                .format(target),(tenant,sources[0][1]))
            raw=__import__('json').dumps({'tenant_id':'foreign','input_id':candidates[0][0],'revision':candidates[0][1]}).encode()
            conn.execute(sql.SQL('INSERT INTO {}(tenant_id,input_id,revision,payload_raw,payload_sha256) VALUES(%s,%s,%s,%s,%s)')
                .format(sql.Identifier(policy.schema,'market_candidate_inputs')),('foreign',*candidates[0],raw,sha256(raw).hexdigest()))
    assert run(consume) is None


def _disable(conn, table):
    conn.execute(sql.SQL('ALTER TABLE {} DISABLE TRIGGER USER').format(table))


def _drop_digest_checks(conn, schema, name):
    constraints=conn.execute('''SELECT c.conname FROM pg_catalog.pg_constraint c
        JOIN pg_catalog.pg_class t ON t.oid=c.conrelid JOIN pg_catalog.pg_namespace n ON n.oid=t.relnamespace
        WHERE n.nspname=%s AND t.relname=%s AND c.contype='c' AND pg_get_constraintdef(c.oid) LIKE '%%sha256(%%' ''',(schema,name)).fetchall()
    assert constraints
    for row in constraints:
        conn.execute(sql.SQL('ALTER TABLE {} DROP CONSTRAINT {}').format(sql.Identifier(schema,name),sql.Identifier(row['conname'])))


@pytest.mark.parametrize('change', ['source_raw_same_hash','job_raw_same_hash','source_metadata',
    'source_deleted','source_replaced','candidate_added','candidate_deleted','candidate_raw_same_hash','candidate_metadata','pin_record_raw',
    'pin_scenario_raw','pin_manifest_raw','pin_metadata','pin_deleted','grant','principal'])
def test_required_dependency_changes_deny_outer_result(harness, login_scope, change):
    store, tenant, sources, candidates, pins, principal, run = harness
    base, policy, _ = login_scope
    retained=[]
    raw_table={'source_raw_same_hash':'market_source_records','job_raw_same_hash':'jobs',
        'candidate_raw_same_hash':'market_candidate_inputs','pin_record_raw':'market_candidate_pins',
        'pin_scenario_raw':'market_candidate_pins','pin_manifest_raw':'market_candidate_pins'}.get(change)
    if raw_table:
        # ACCESS EXCLUSIVE test DDL must finish before the reader owns relation locks.
        with base.connect() as conn:_drop_digest_checks(conn,policy.schema,raw_table)
    if change in ('candidate_deleted','candidate_raw_same_hash','candidate_metadata'):
        with base.connect() as conn:
            conn.execute(sql.SQL('INSERT INTO {}(tenant_id,input_id,revision,payload_raw,payload_sha256) SELECT tenant_id,record_id,revision,payload_raw,payload_sha256 FROM {} WHERE tenant_id=%s AND kind=%s AND record_id=%s AND revision=%s')
                .format(sql.Identifier(policy.schema,'market_candidate_inputs'),sql.Identifier(policy.schema,'market_source_records')),(tenant,*sources[0]))
    def consume(reader):
        retained.append(reader)
        if change=='principal': principal['scopes'].discard('market_source_read');return
        with base.connect() as conn:
            source=sql.Identifier(policy.schema,'market_source_records')
            if change=='grant':
                conn.execute(sql.SQL('GRANT UPDATE ON {} TO {}').format(source,sql.Identifier(policy.roles['authority'])));return
            if change.startswith('source') or change=='job_raw_same_hash':
                row=conn.execute(sql.SQL('SELECT * FROM {} WHERE tenant_id=%s AND kind=%s AND record_id=%s AND revision=%s').format(source),(tenant,*sources[0])).fetchone()
                target=sql.Identifier(policy.schema,'jobs') if change.startswith('job') else source
                _disable(conn,target)
                if change=='source_raw_same_hash':
                    conn.execute(sql.SQL('UPDATE {} SET payload_raw=%s WHERE tenant_id=%s AND kind=%s AND record_id=%s AND revision=%s').format(source),(b'{}',tenant,*sources[0]))
                elif change=='job_raw_same_hash':
                    conn.execute(sql.SQL('UPDATE {} SET input_bytes=%s WHERE tenant_id=%s AND job_id=%s').format(target),(b'{}',tenant,row['job_id']))
                elif change=='source_metadata':
                    conn.execute(sql.SQL("UPDATE {} SET recorded_at=recorded_at+interval '1 microsecond' WHERE tenant_id=%s AND kind=%s AND record_id=%s AND revision=%s").format(source),(tenant,*sources[0]))
                elif change=='source_deleted':
                    conn.execute(sql.SQL('DELETE FROM {} WHERE tenant_id=%s AND kind=%s AND record_id=%s AND revision=%s').format(source),(tenant,*sources[0]))
                else:
                    conn.execute(sql.SQL('DELETE FROM {} WHERE tenant_id=%s AND kind=%s AND record_id=%s AND revision=%s').format(source),(tenant,*sources[0]))
                    row['recorded_at']=row['recorded_at'].replace(year=row['recorded_at'].year+1)
                    conn.execute(sql.SQL('INSERT INTO {}({}) VALUES({})').format(source,sql.SQL(',').join(map(sql.Identifier,row)),sql.SQL(',').join(sql.Placeholder() for _ in row)),tuple(row.values()))
            elif change.startswith('candidate'):
                target=sql.Identifier(policy.schema,'market_candidate_inputs');_disable(conn,target)
                if change=='candidate_raw_same_hash':
                    conn.execute(sql.SQL('UPDATE {} SET payload_raw=payload_raw||%s WHERE tenant_id=%s AND input_id=%s AND revision=%s').format(target),(b' ',tenant,*candidates[0]))
                elif change=='candidate_metadata':
                    conn.execute(sql.SQL("UPDATE {} SET recorded_at=recorded_at+interval '1 microsecond' WHERE tenant_id=%s AND input_id=%s AND revision=%s").format(target),(tenant,*candidates[0]))
                elif change=='candidate_deleted':
                    conn.execute(sql.SQL('DELETE FROM {} WHERE tenant_id=%s AND input_id=%s AND revision=%s').format(target),(tenant,*candidates[0]))
                else:
                    conn.execute(sql.SQL('INSERT INTO {}(tenant_id,input_id,revision,payload_raw,payload_sha256) SELECT tenant_id,record_id,revision,payload_raw,payload_sha256 FROM {} WHERE tenant_id=%s AND kind=%s AND record_id=%s AND revision=%s').format(target,source),(tenant,*sources[0]))
            else:
                target=sql.Identifier(policy.schema,'market_candidate_pins');_disable(conn,target)
                if change=='pin_deleted':
                    conn.execute(sql.SQL('DELETE FROM {} WHERE tenant_id=%s AND scenario_id=%s AND revision=%s').format(target),(tenant,*pins[0]))
                elif change=='pin_metadata':
                    conn.execute(sql.SQL("UPDATE {} SET recorded_at=recorded_at+interval '1 microsecond' WHERE tenant_id=%s AND scenario_id=%s AND revision=%s").format(target),(tenant,*pins[0]))
                else:
                    field={'pin_record_raw':'record_raw','pin_scenario_raw':'scenario_raw','pin_manifest_raw':'inputs_manifest_raw'}[change]
                    conn.execute(sql.SQL('UPDATE {} SET {}={}||%s WHERE tenant_id=%s AND scenario_id=%s AND revision=%s')
                        .format(target,sql.Identifier(field),sql.Identifier(field)),(b' ',tenant,*pins[0]))
    with pytest.raises((ValueError,PermissionError)):
        run(consume)
    assert retained and not retained[0].active and retained[0].conn is retained[0].receipts is None
    assert store._reference_bundle.get() is store._scoped_reader.get() is None


@pytest.mark.parametrize('change',['duplicate','unknown_kind','too_many','empty','wrong_shape'])
def test_invalid_key_sets_reject_before_callback(harness, change):
    _,_,sources,candidates,pins,_,run=harness
    chosen={'duplicate':sources*2,'unknown_kind':(('unknown','id','r1'),),
        'too_many':tuple(('economic_input',str(i),'r1') for i in range(129)),
        'empty':(),'wrong_shape':(('economic_input','id'),)}[change]
    calls=[]
    with pytest.raises(ValueError):run(lambda _:calls.append(1),chosen,() if change=='empty' else candidates,() if change=='empty' else pins)
    assert not calls


@pytest.mark.parametrize('change',['nested','copied','thread','task','copied_close','code','version',
    'connection','keys','provider','table_method','exception','unknown_key','nonempty_result','slot','tenant','other_connection'])
def test_lifetime_failure_poisoning_cleanup_and_next_call(harness, monkeypatch, change):
    from contextvars import copy_context
    from concurrent.futures import ThreadPoolExecutor
    import asyncio
    from app import market_reference_receipts as model
    store,tenant,sources,candidates,pins,_,run=harness
    retained=[]
    with monkeypatch.context() as changes:
        def consume(reader):
            retained.append(reader)
            if change=='exception':raise RuntimeError('owned interruption')
            if change=='code':changes.setattr(model,'CODE_SHA256','0'*64);return
            if change=='version':changes.setattr(model,'VERSION','changed');return
            if change=='connection':reader.conn.close();return
            if change=='slot':changes.setattr(model,'_active',type(model._active)('changed',default=None));return
            if change=='keys':reader.keys=((),(),());return
            if change=='provider':changes.setattr(store,'_principal_provider',lambda:{});return
            if change=='table_method':changes.setattr(store,'_table',lambda _:sql.Identifier('changed'));return
            if change=='nonempty_result':return {'not_an_approval':True}
            with pytest.raises(ValueError):
                if change=='nested':model.verify_receipts(store,tenant,sources,candidates,pins,lambda _:None)
                elif change=='copied':copy_context().run(reader.source_receipt,reader.conn,tenant,*sources[0])
                elif change=='copied_close':copy_context().run(reader._close)
                elif change=='tenant':reader.source_receipt(reader.conn,'foreign',*sources[0])
                elif change=='other_connection':reader.source_receipt(object(),tenant,*sources[0])
                elif change=='unknown_key':reader.source_receipt(reader.conn,tenant,'economic_input','unknown','r1')
                elif change=='task':
                    async def copied():reader.source_receipt(reader.conn,tenant,*sources[0])
                    asyncio.run(copied())
                else:
                    context=copy_context()
                    with ThreadPoolExecutor(max_workers=1) as pool:
                        pool.submit(context.run,reader.source_receipt,reader.conn,tenant,*sources[0]).result(timeout=10)
        with pytest.raises((ValueError,RuntimeError,psycopg.Error)):run(consume)
    assert retained and not retained[0].active and retained[0].conn is retained[0].receipts is None
    assert model._active.get() is store._reference_bundle.get() is store._scoped_reader.get() is None
    assert run(lambda _:None) is None


def test_primitive_requires_existing_owned_bundle(harness):
    from app import market_reference_receipts as model
    store,tenant,sources,candidates,pins,_,_=harness
    with pytest.raises(ValueError):model.verify_receipts(store,tenant,sources,candidates,pins,lambda _:None)


@pytest.mark.parametrize('combined',[False,True])
def test_compressible_raw_budget_prevents_digest_encoding_before_callback(harness, login_scope, monkeypatch, combined):
    import json
    from types import SimpleNamespace
    _,tenant,sources,_,pins,_,run=harness
    base,policy,_=login_scope
    raw=json.dumps({'pad':'x'*(65536-len('{"pad":""}'))},separators=(',',':')).encode()
    digest=sha256(raw).hexdigest()
    with base.connect() as conn:
        source,jobs=sql.Identifier(policy.schema,'market_source_records'),sql.Identifier(policy.schema,'jobs')
        selected=conn.execute(sql.SQL("SELECT kind,record_id,revision,job_id FROM {} WHERE tenant_id=%s AND kind='economic_input' ORDER BY record_id LIMIT %s").format(source),(tenant,1 if combined else 9)).fetchall()
        assert len(selected)==(1 if combined else 9)
        for table in (source,jobs):_disable(conn,table)
        for row in selected:
            conn.execute(sql.SQL('UPDATE {} SET payload_raw=%s,payload_sha256=%s WHERE tenant_id=%s AND kind=%s AND record_id=%s AND revision=%s').format(source),(raw,digest,tenant,row['kind'],row['record_id'],row['revision']))
            conn.execute(sql.SQL('UPDATE {} SET input_bytes=%s,input_sha256=%s WHERE tenant_id=%s AND job_id=%s').format(jobs),(raw,digest,tenant,row['job_id']))
        if combined:
            target=sql.Identifier(policy.schema,'market_candidate_pins');_disable(conn,target)
            # Each category fits alone; their combined uncompressed bytes do not.
            original=conn.execute(sql.SQL('SELECT record_raw,scenario_raw,inputs_manifest_raw FROM {} WHERE tenant_id=%s AND scenario_id=%s AND revision=%s').format(target),(tenant,*pins[0])).fetchone()
            assert original is not None
            for field, value in original.items():
                assert len(value)<330000
                value=value+b' '*(330000-len(value))
                conn.execute(sql.SQL('UPDATE {} SET {}=%s,{}=%s WHERE tenant_id=%s AND scenario_id=%s AND revision=%s')
                    .format(target,sql.Identifier(field),sql.Identifier(field.replace('_raw','_sha256'))),(value,sha256(value).hexdigest(),tenant,*pins[0]))
    execute=psycopg.Connection.execute;observed=[];callbacks=[]
    def capture(conn,query,params=None,**kwargs):
        cursor=execute(conn,query,params,**kwargs)
        text=query.as_string(conn) if hasattr(query,'as_string') else query
        if 'receipt_keys AS MATERIALIZED' not in text:return cursor
        values=cursor.fetchall();observed.append(values)
        assert values and all(v['ok'] is False and v['receipt'] is None for v in values)
        if combined:
            totals={i:sum(v['bytes'] for v in values if v['category']==i) for i in range(3)}
            assert all(v<1048576 for v in totals.values()) and sum(totals.values())>1048576
        return SimpleNamespace(fetchall=lambda:values)
    monkeypatch.setattr(psycopg.Connection,'execute',capture)
    chosen=tuple((v['kind'],v['record_id'],v['revision']) for v in selected)
    with pytest.raises(ValueError):run(lambda _:callbacks.append(1),chosen,(),pins if combined else ())
    assert len(observed)==1 and not callbacks


@pytest.mark.parametrize('category',['source','pin'])
def test_absent_to_present_required_dependencies_are_not_reused(harness,login_scope,category):
    _,tenant,sources,_,pins,_,run=harness
    base,policy,_=login_scope
    name='market_source_records' if category=='source' else 'market_candidate_pins'
    target=sql.Identifier(policy.schema,name)
    names=('kind','record_id','revision') if category=='source' else ('scenario_id','revision')
    key=sources[0] if category=='source' else pins[0]
    where=sql.SQL('tenant_id=%s AND ')+sql.SQL(' AND ').join(sql.SQL('{}=%s').format(sql.Identifier(n)) for n in names)
    with base.connect() as conn:
        row=conn.execute(sql.SQL('SELECT * FROM {} WHERE {}').format(target,where),(tenant,*key)).fetchone()
        assert row is not None
        _disable(conn,target)
        conn.execute(sql.SQL('DELETE FROM {} WHERE {}').format(target,where),(tenant,*key))
    def consume(reader):
        getter=reader.source_receipt if category=='source' else reader.pin_receipt
        assert getter(reader.conn,tenant,*key) is None
        with base.connect() as conn:
            conn.execute(sql.SQL('INSERT INTO {}({}) VALUES({})').format(target,sql.SQL(',').join(map(sql.Identifier,row)),sql.SQL(',').join(sql.Placeholder() for _ in row)),tuple(row.values()))
    with pytest.raises(ValueError):run(consume)


def test_source_scope_revocation_stops_before_any_further_receipt_SQL(harness,monkeypatch):
    _,_,_,_,_,principal,run=harness
    execute=psycopg.Connection.execute;reads=[]
    def observing(conn,query,params=None,**kwargs):
        text=query.as_string(conn) if hasattr(query,'as_string') else query
        if 'receipt_keys AS MATERIALIZED' in text:reads.append(1)
        return execute(conn,query,params,**kwargs)
    monkeypatch.setattr(psycopg.Connection,'execute',observing)
    with pytest.raises((ValueError,PermissionError)):
        run(lambda _:principal['scopes'].discard('market_source_read'))
    assert len(reads)==1, 'revoked source scope must stop before the post-read SQL'


def test_unknown_schema_is_rejected_before_consumer(harness,login_scope):
    _,_,_,_,_,_,run=harness
    base,policy,_=login_scope
    with base.connect() as conn:
        conn.execute(sql.SQL('ALTER TABLE {} ADD COLUMN unexpected text').format(sql.Identifier(policy.schema,'market_source_records')))
    calls=[]
    with pytest.raises((ValueError,PermissionError)):run(lambda _:calls.append(1))
    assert not calls
