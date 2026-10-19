"""Actual checkpoint currentness retains fresh rights within one registration scope."""
from contextlib import nullcontext
from contextvars import copy_context
from hashlib import sha256
import json

import psycopg
from psycopg import sql
import pytest

from app.farm_authoring_storage import FarmAuthoringHold
from app.crop_greenhouse_solar_farm_binding import SolarFarmBindingHold
from app.market_source_store import MarketSourceStore
from app import runtime_connection_scope as connections
from test_crop_greenhouse_solar_execution_query import (
    worker_setup, producer_setup, authoring, profiles, login_database,
    original_login_scope, login_scope, query_cleanup, save)
import test_crop_greenhouse_solar_execution_query as reference


pytestmark = [reference.reference.pytestmark, pytest.mark.usefixtures('query_cleanup')]


def current_request(worker, job_id):
    with worker.jobs.connect() as conn:
        row = conn.execute(sql.SQL('SELECT * FROM {} WHERE tenant_id=%s AND job_id=%s')
            .format(worker.jobs._table('jobs')), ('tenant-1', job_id)).fetchone()
    return worker.checkpoints._input('tenant-1', row)


@pytest.mark.parametrize('existing', [False, True])
def test_current_reads_share_scope_without_skipping_sources(worker_setup, monkeypatch, existing):
    worker, job_id, raw, _ = worker_setup
    farms = worker.server.binding.farms
    value, request_raw, binding_raw = current_request(worker, job_id)
    ref = json.loads(raw)['farm']
    args = ('tenant-1', ref['scenario_id'], ref['scenario_revision'], ref['registration_sha256'])
    original, prepare = farms.read_registration, farms._prepare
    source_read = MarketSourceStore._read_in_transaction
    observed = {'prepare': 0, 'sources': [], 'witnesses': [], 'connections': []}

    def preparing(*a, **kw):
        observed['prepare'] += 1
        return prepare(*a, **kw)

    def reading(*a, **kw):
        result = original(*a, **kw)
        observed['witnesses'].append(farms._registration_read.get())
        observed['connections'].append(connections._CURRENT.get().conn
            if connections._CURRENT.get() is not None else None)
        return result

    def source(self, conn, tenant, kind, identity, revision, **kw):
        observed['sources'].append((tenant, kind, identity, revision, kw.get('pin', False)))
        return source_read(self, conn, tenant, kind, identity, revision, **kw)

    monkeypatch.setattr(farms, '_prepare', preparing)
    monkeypatch.setattr(farms, 'read_registration', reading)
    monkeypatch.setattr(MarketSourceStore, '_read_in_transaction', source)
    with farms.registration_read_scope(*args) if existing else nullcontext():
        owner = farms._registration_read.get()
        worker.checkpoints._current('tenant-1', value, request_raw, binding_raw)
        assert observed['prepare'] == 1
        assert len(observed['witnesses']) == 2
        witness = observed['witnesses'][0]
        assert witness is not None and all(w is witness for w in observed['witnesses'])
        assert len(observed['sources']) == 152
        assert observed['sources'][:76] == observed['sources'][76:]
        assert farms._registration_read.get() is owner
        if existing:
            assert witness is owner and owner.active
        else:
            assert not witness.active
    assert farms._registration_read.get() is connections._CURRENT.get() is None
    assert all(conn is not None and conn.closed for conn in observed['connections'])
    save('checkpoint-current-scope-' + str(existing).lower(), {
        'registration_reads': 2, 'reconstructions': 1, 'ordered_source_reads': 152,
        'existing_scope_preserved': existing, 'closed': True, 'new_calculation': False})


@pytest.mark.parametrize('change', ['scope', 'source', 'grant', 'copied_context'])
def test_current_rejects_changes_between_registration_reads(worker_setup, login_scope, monkeypatch, change):
    worker, job_id, _, fixture = worker_setup
    farms = worker.server.binding.farms
    value, request_raw, binding_raw = current_request(worker, job_id)
    base, policy, _ = login_scope
    original = farms.read_registration
    calls, retained = [], []

    def reading(*a, **kw):
        if len(calls) == 1 and change == 'copied_context':
            return copy_context().run(original, *a, **kw)
        result = original(*a, **kw)
        calls.append(1)
        if len(calls) == 1:
            retained.append(connections._CURRENT.get().conn)
            if change == 'scope':
                fixture[4]['scopes'].discard('market_source_read')
            elif change in ('source', 'grant'):
                with base.connect() as conn:
                    table = sql.Identifier(policy.schema, 'market_source_records')
                    if change == 'grant':
                        conn.execute(sql.SQL('GRANT UPDATE ON {} TO {}').format(
                            table, sql.Identifier(policy.roles['authority'])))
                    else:
                        conn.execute(sql.SQL('ALTER TABLE {} DISABLE TRIGGER USER').format(table))
                        raw = b'{}'
                        conn.execute(sql.SQL("UPDATE {} SET payload_raw=%s,payload_sha256=%s "
                            "WHERE tenant_id=%s AND kind='input_rights'").format(table),
                            (raw, sha256(raw).hexdigest(), 'tenant-1'))
        return result

    monkeypatch.setattr(farms, 'read_registration', reading)
    with pytest.raises((SolarFarmBindingHold, FarmAuthoringHold, PermissionError)):
        worker.checkpoints._current('tenant-1', value, request_raw, binding_raw)
    assert calls == [1] and retained and all(conn.closed for conn in retained)
    assert farms._registration_read.get() is connections._CURRENT.get() is connections._REQUEST.get() is None
    with base.connect() as conn:
        assert conn.execute(sql.SQL('SELECT count(*) AS count FROM {} '
            'WHERE tenant_id=%s AND job_id=%s AND kind=%s').format(worker.jobs._table('job_events')),
            ('tenant-1', job_id, reference.model.checkpoints.EVENT_KIND)).fetchone()['count'] == 0
    save('checkpoint-current-denied-' + change, {'change': change, 'denied': True,
        'confirmed_events': 0, 'connections_closed': True, 'new_calculation': False})
