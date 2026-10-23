"""Native leaf queries reuse reconstruction while retaining current source reads."""
from contextlib import nullcontext
from contextvars import copy_context
from hashlib import sha256

import psycopg
from psycopg import sql
import pytest

from app import runtime_connection_scope as connections
from app.crop_leaf_population_execution_query import LeafPopulationExecutionQueryHold
from app.market_source_store import MarketSourceStore
from test_crop_leaf_population_execution_query_native import (
    completed, execution_setup, setup, login_scope, login_database, final_cleanup,
    readonly, schema_hash, snapshot)
import test_crop_leaf_population_execution_query_native as reference


pytestmark = reference.pytestmark


@pytest.mark.parametrize('existing', [False, True])
def test_completed_query_reconstructs_once_and_keeps_every_current_source(
        completed, login_scope, monkeypatch, existing):
    service, reader, values, _, job, outcome = completed
    farms = service.authority.farm_binding.parent_authority.farm_binding.farms
    ref = values[1]['farm']
    args = ('tenant-1', ref['scenario_id'], ref['scenario_revision'], ref['registration_sha256'])
    before = schema_hash(login_scope[0])
    parent = snapshot(service.authority.farm_binding.parent_authority.directory)
    leaf = snapshot(service.authority.directory)
    prepare, read = farms._prepare, farms.read_registration
    source_read = MarketSourceStore._read_in_transaction
    observed = {'prepare': 0, 'sources': [], 'traces': [], 'witnesses': [], 'connections': []}

    def preparing(*a, **kw):
        observed['prepare'] += 1
        return prepare(*a, **kw)

    def reading(*a, **kw):
        start = len(observed['sources'])
        value = read(*a, **kw)
        observed['traces'].append(observed['sources'][start:])
        observed['witnesses'].append(farms._registration_read.get())
        frame = connections._CURRENT.get()
        observed['connections'].append(None if frame is None else frame.conn)
        return value

    def source(self, conn, tenant, kind, identity, revision, **kw):
        observed['sources'].append((tenant, kind, identity, revision, kw.get('pin', False)))
        return source_read(self, conn, tenant, kind, identity, revision, **kw)

    monkeypatch.setattr(farms, '_prepare', preparing)
    monkeypatch.setattr(farms, 'read_registration', reading)
    monkeypatch.setattr(MarketSourceStore, '_read_in_transaction', source)
    with monkeypatch.context() as patch:
        growth, writes, sql_writes = readonly(patch)
        with farms.registration_read_scope(*args) if existing else nullcontext():
            owner = farms._registration_read.get()
            value = reader.read('tenant-1', str(job['job_id']))
            assert observed['prepare'] == 1
            assert len(observed['traces']) == 64
            assert len(observed['traces'][0]) == 76
            assert all(trace == observed['traces'][0] for trace in observed['traces'])
            assert len(observed['sources']) == 64 * 76
            witness = observed['witnesses'][0]
            assert witness is not None and all(w is witness for w in observed['witnesses'])
            assert farms._registration_read.get() is owner and witness.active is existing
            assert value['job']['state'] == 'succeeded'
            assert value['result']['result_sha256'] == outcome.result_sha256
            assert value['result']['parent_result_sha256'] == values[1]['parent']['result_sha256']
            assert value['manifest'] is value['frame'] is value['replay'] is None
        assert not any(growth.values()) and not any(writes.values()) and not sql_writes
    assert farms._registration_read.get() is connections._CURRENT.get() is connections._REQUEST.get() is None
    assert all(conn is not None and conn.closed for conn in observed['connections'])
    assert schema_hash(login_scope[0]) == before
    assert snapshot(service.authority.farm_binding.parent_authority.directory) == parent
    assert snapshot(service.authority.directory) == leaf


def test_completed_query_rejects_late_changes_and_restores_current_reads(completed, login_scope, monkeypatch):
    service, reader, values, _, job, outcome = completed
    farms = service.authority.farm_binding.parent_authority.farm_binding.farms
    base, policy, _ = login_scope
    principal = values[7]
    before = schema_hash(base)
    parent = snapshot(service.authority.farm_binding.parent_authority.directory)
    leaf = snapshot(service.authority.directory)
    read, execute = farms.read_registration, psycopg.Cursor.execute

    # Only explicit administrator fault statements use this captured SQL method.
    # The actual query remains under readonly() throughout each fault and recovery.
    def admin(statement, params=()):
        with base.connect() as conn, conn.cursor() as cursor:
            return execute(cursor, statement, params).fetchall() if statement.as_string(conn).startswith('SELECT') \
                else execute(cursor, statement, params).rowcount

    def sql_fault(change, registered):
        target = sql.Identifier(policy.schema, 'market_source_records')
        if change == 'grant':
            role = sql.Identifier(policy.roles['authority'])
            assert admin(sql.SQL('SELECT has_table_privilege(%s,%s,%s) AS allowed'),
                (policy.roles['authority'], target.as_string(), 'UPDATE')) == [{'allowed': False}]
            admin(sql.SQL('GRANT UPDATE ON {} TO {}').format(target, role))
            return lambda: admin(sql.SQL('REVOKE UPDATE ON {} FROM {}').format(target, role))
        farm = registered['farm']
        source_id, source_revision = next(args for name, args, _ in farms._registration_read.get().lookups
            if name == 'get_input_rights')
        specs = {
            'source': ('market_source_records', 'payload_raw', 'payload_sha256',
                "tenant_id=%s AND kind='input_rights' AND record_id=%s AND revision=%s",
                ('tenant-1', source_id, source_revision)),
            'research': ('jobs', 'input_bytes', 'input_sha256', 'tenant_id=%s AND job_id=%s',
                ('tenant-1', farm.research_job_id)),
            'registration': ('jobs', 'input_bytes', 'input_sha256',
                "tenant_id=%s AND stage='collection' AND idempotency_key=%s",
                ('tenant-1', farms._key(farm.scenario_id, farm.scenario_revision))),
            'snapshot': ('thermal_input_snapshots', 'weather_raw', 'weather_sha256',
                'tenant_id=%s AND snapshot_id=%s', ('tenant-1', farm.snapshot_id))}
        table, raw, digest, where, params = specs[change]
        target = sql.Identifier(policy.schema, table)
        columns = sql.SQL(',').join(map(sql.Identifier, (raw, digest)))
        rows = admin(sql.SQL('SELECT {} FROM {} WHERE {}').format(columns, target, sql.SQL(where)), params)
        assert len(rows) == 1
        update = sql.SQL('UPDATE {} SET {}=%s,{}=%s WHERE {}').format(
            target, sql.Identifier(raw), sql.Identifier(digest), sql.SQL(where))

        def replace(data):
            with base.connect() as conn, conn.cursor() as cursor:
                execute(cursor, sql.SQL('ALTER TABLE {} DISABLE TRIGGER USER').format(target))
                assert execute(cursor, update, (*data, *params)).rowcount == 1
                execute(cursor, sql.SQL('ALTER TABLE {} ENABLE TRIGGER USER').format(target))
        replace((b'{}', sha256(b'{}').hexdigest()))
        return lambda: replace((rows[0][raw], rows[0][digest]))

    with monkeypatch.context() as fence:
        growth, writes, sql_writes = readonly(fence)
        assert reader.read('tenant-1', str(job['job_id']))['result']['result_sha256'] == outcome.result_sha256
        for change in ('source', 'grant', 'research', 'registration', 'snapshot', 'principal', 'scope',
                       'leaf_rights', 'parent_rights', 'copied_context', 'read_error'):
            reads, applied, retained, undo = [], [], [], []
            tenant, scopes = principal['tenant_id'], set(principal['scopes'])

            def reading(*a, **kw):
                if len(reads) == 1 and change in ('copied_context', 'read_error'):
                    applied.append(change)
                    if change == 'copied_context':
                        return copy_context().run(read, *a, **kw)
                    raise RuntimeError('leaf query registration read diagnostic')
                registered = read(*a, **kw)
                reads.append(True)
                if len(reads) == 1:
                    witness, frame = farms._registration_read.get(), connections._CURRENT.get()
                    assert witness is not None and frame is not None and frame.conn is not None
                    retained.append((witness, frame.conn))
                    if change == 'principal': principal['tenant_id'] = 'different-tenant'
                    elif change == 'scope': principal['scopes'].discard('market_source_read')
                    elif change == 'leaf_rights': values[8].allowed = False
                    elif change == 'parent_rights': values[9].allowed = False
                    elif change not in ('copied_context', 'read_error'):
                        undo.append(sql_fault(change, registered))
                    if change not in ('copied_context', 'read_error'): applied.append(change)
                return registered

            try:
                with monkeypatch.context() as patch:
                    patch.setattr(farms, 'read_registration', reading)
                    with pytest.raises((LeafPopulationExecutionQueryHold, PermissionError)):
                        reader.read('tenant-1', str(job['job_id']))
                # Leaf rights follow the complete parent audit; parent rights are checked after its first read.
                expected_reads = 16 if change == 'leaf_rights' else 1
                assert applied == [change] and reads == [True] * expected_reads, change
                assert retained and all(not witness.active and conn.closed for witness, conn in retained), change
                assert farms._registration_read.get() is connections._CURRENT.get() is connections._REQUEST.get() is None
            finally:
                principal['tenant_id'], principal['scopes'] = tenant, scopes
                values[8].allowed = values[9].allowed = True
                for restore in reversed(undo): restore()
            restored = reader.read('tenant-1', str(job['job_id']))
            assert restored['result']['result_sha256'] == outcome.result_sha256, change
            assert schema_hash(base) == before, change
            assert snapshot(service.authority.farm_binding.parent_authority.directory) == parent, change
            assert snapshot(service.authority.directory) == leaf, change
        assert not any(growth.values()) and not any(writes.values()) and not sql_writes


def test_completed_query_rejects_another_registration_scope(completed, login_scope, monkeypatch):
    service, reader, values, _, job, outcome = completed
    farms = service.authority.farm_binding.parent_authority.farm_binding.farms
    ref = values[1]['farm']
    args = ('tenant-1', ref['scenario_id'], ref['scenario_revision'], ref['registration_sha256'])
    before = schema_hash(login_scope[0])
    with monkeypatch.context() as patch:
        growth, writes, sql_writes = readonly(patch)
        for index in (1, 2, 3):
            wrong = list(args)
            wrong[index] = 'foreign-registration' if index != 3 else '0' * 64
            with farms.registration_read_scope(*wrong):
                witness, frame = farms._registration_read.get(), connections._CURRENT.get()
                with pytest.raises((LeafPopulationExecutionQueryHold, PermissionError)):
                    reader.read('tenant-1', str(job['job_id']))
                assert farms._registration_read.get() is witness and witness.failed
            assert not witness.active and frame.closed
            assert farms._registration_read.get() is connections._CURRENT.get() is connections._REQUEST.get() is None
        assert reader.read('tenant-1', str(job['job_id']))['result']['result_sha256'] == outcome.result_sha256
        assert not any(growth.values()) and not any(writes.values()) and not sql_writes
    assert schema_hash(login_scope[0]) == before
