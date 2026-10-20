"""Read-only query currentness owns only one fresh registration pair."""
from contextlib import nullcontext
from contextvars import copy_context
from hashlib import sha256
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT/'backend'), str(ROOT/'backend/tests'), str(ROOT/'research')]

import psycopg
from psycopg import sql
import pytest

from app import crop_greenhouse_solar_execution_query as model
from app import runtime_connection_scope as connections
from app.farm_authoring_storage import FarmAuthoringHold
from app.market_source_store import MarketSourceStore
from test_solar_checkpoint_registration_scope import current_request
from test_crop_greenhouse_solar_execution_query import (
    worker_setup, producer_setup, authoring, profiles, login_database,
    original_login_scope, login_scope, query_cleanup, save)
import test_crop_greenhouse_solar_execution_query as reference

pytestmark = [reference.reference.pytestmark, pytest.mark.usefixtures('query_cleanup')]


@pytest.mark.parametrize('existing', [False, True])
def test_query_current_scopes_one_pair_and_keeps_every_source(worker_setup, monkeypatch, existing):
    worker, job_id, raw, _ = worker_setup
    query = model.SolarExecutionQuery(worker.checkpoints, worker.results)
    farms = worker.server.binding.farms
    value, request_raw, binding_raw = current_request(worker, job_id)
    ref = json.loads(raw)['farm']
    args = ('tenant-1', ref['scenario_id'], ref['scenario_revision'], ref['registration_sha256'])
    read, prepare = farms.read_registration, farms._prepare
    source_read = MarketSourceStore._read_in_transaction
    observed = {'prepare': 0, 'sources': [], 'witnesses': [], 'connections': []}

    def preparing(*a, **kw):
        observed['prepare'] += 1
        return prepare(*a, **kw)

    def reading(*a, **kw):
        result = read(*a, **kw)
        observed['witnesses'].append(farms._registration_read.get())
        frame = connections._CURRENT.get()
        observed['connections'].append(frame.conn if frame is not None else None)
        return result

    def source(self, conn, tenant, kind, identity, revision, **kw):
        observed['sources'].append((tenant, kind, identity, revision, kw.get('pin', False)))
        return source_read(self, conn, tenant, kind, identity, revision, **kw)

    monkeypatch.setattr(farms, '_prepare', preparing)
    monkeypatch.setattr(farms, 'read_registration', reading)
    monkeypatch.setattr(MarketSourceStore, '_read_in_transaction', source)
    with farms.registration_read_scope(*args) if existing else nullcontext():
        owner = farms._registration_read.get()
        with monkeypatch.context() as patch:
            forbidden = reference.reference.producer.reference.forbid(patch)
            query._current('tenant-1', value, request_raw, binding_raw)
            assert all(n == 0 for n in forbidden.values())
        assert len(observed['sources']) == 152
        assert observed['sources'][:76] == observed['sources'][76:]
        assert len(observed['witnesses']) == 2
        save('query-current-pair-' + str(existing).lower(), {
            'registration_reads': 2, 'reconstructions': observed['prepare'],
            'ordered_current_sources': 152, 'existing_owner': existing,
            'new_numerics': 0})
        assert observed['prepare'] == 1
        witness = observed['witnesses'][0]
        assert witness is not None and all(w is witness for w in observed['witnesses'])
        assert farms._registration_read.get() is owner
        assert witness.active is existing
    assert farms._registration_read.get() is connections._CURRENT.get() is connections._REQUEST.get() is None
    assert all(conn is not None and conn.closed for conn in observed['connections'])


@pytest.mark.parametrize('change', [
    'scope', 'source', 'grant', 'research', 'snapshot', 'principal', 'copied_context', 'read_error'])
def test_query_current_rejects_late_changes_and_closes_scope(worker_setup, login_scope, monkeypatch, change):
    worker, job_id, _, fixture = worker_setup
    query = model.SolarExecutionQuery(worker.checkpoints, worker.results)
    farms = worker.server.binding.farms
    value, request_raw, binding_raw = current_request(worker, job_id)
    base, policy, _ = login_scope
    original = farms.read_registration
    calls, retained = [], []

    def reading(*a, **kw):
        if len(calls) == 1:
            if change == 'copied_context': return copy_context().run(original, *a, **kw)
            if change == 'read_error': raise RuntimeError('query registration read diagnostic')
        result = original(*a, **kw)
        calls.append(True)
        if len(calls) == 1:
            retained.append(connections._CURRENT.get().conn)
            if change == 'scope': fixture[4]['scopes'].discard('market_source_read')
            elif change == 'principal': fixture[4]['tenant_id'] = 'different-tenant'
            elif change in ('source', 'grant', 'research', 'snapshot'):
                with base.connect() as conn:
                    table = {'source': 'market_source_records', 'grant': 'market_source_records',
                             'research': 'jobs', 'snapshot': 'thermal_input_snapshots'}[change]
                    target = sql.Identifier(policy.schema, table)
                    if change == 'grant':
                        conn.execute(sql.SQL('GRANT UPDATE ON {} TO {}').format(
                            target, sql.Identifier(policy.roles['authority'])))
                    else:
                        conn.execute(sql.SQL('ALTER TABLE {} DISABLE TRIGGER USER').format(target))
                        bad = b'{}'; digest = sha256(bad).hexdigest()
                        if change == 'source':
                            conn.execute(sql.SQL("UPDATE {} SET payload_raw=%s,payload_sha256=%s "
                                "WHERE tenant_id=%s AND kind='input_rights'").format(target),
                                (bad, digest, 'tenant-1'))
                        elif change == 'research':
                            conn.execute(sql.SQL('UPDATE {} SET input_bytes=%s,input_sha256=%s '
                                'WHERE tenant_id=%s AND job_id=%s').format(target),
                                (bad, digest, 'tenant-1', result['farm'].research_job_id))
                        else:
                            conn.execute(sql.SQL('UPDATE {} SET weather_raw=%s,weather_sha256=%s '
                                'WHERE tenant_id=%s AND snapshot_id=%s').format(target),
                                (bad, digest, 'tenant-1', result['farm'].snapshot_id))
        return result

    monkeypatch.setattr(farms, 'read_registration', reading)
    try:
        with pytest.raises((model.custody.farms.SolarFarmBindingHold, FarmAuthoringHold, PermissionError)):
            query._current('tenant-1', value, request_raw, binding_raw)
        assert calls == [True] and retained and all(conn.closed for conn in retained)
        assert farms._registration_read.get() is connections._CURRENT.get() is connections._REQUEST.get() is None
    finally:
        fixture[4]['tenant_id'] = 'tenant-1'
        fixture[4]['scopes'].add('market_source_read')
    with base.connect() as conn:
        assert conn.execute(sql.SQL('SELECT count(*) AS n FROM {} WHERE tenant_id=%s AND job_id=%s')
            .format(worker.jobs._table('job_publications')), ('tenant-1', job_id)).fetchone()['n'] == 0
        assert conn.execute(sql.SQL('SELECT count(*) AS n FROM {} '
            'WHERE tenant_id=%s AND job_id=%s AND kind=%s').format(worker.jobs._table('job_events')),
            ('tenant-1', job_id, model.checkpoints.EVENT_KIND)).fetchone()['n'] == 0
    save('query-current-late-' + change, {'denied': True, 'closed': True,
         'checkpoint_events': 0, 'result_publications': 0})


def test_query_current_does_not_accept_another_registration_owner(worker_setup):
    worker, job_id, raw, _ = worker_setup
    query = model.SolarExecutionQuery(worker.checkpoints, worker.results)
    value, request_raw, binding_raw = current_request(worker, job_id)
    farms = worker.server.binding.farms
    ref = json.loads(raw)['farm']
    with pytest.raises((model.custody.farms.SolarFarmBindingHold, FarmAuthoringHold)):
        with farms.registration_read_scope('tenant-1', 'different-scenario',
                ref['scenario_revision'], ref['registration_sha256']):
            query._current('tenant-1', value, request_raw, binding_raw)
    assert farms._registration_read.get() is connections._CURRENT.get() is connections._REQUEST.get() is None


@pytest.fixture(autouse=True)
def candidate_scope(monkeypatch):
    from solar_query_scope_candidate import install
    install(monkeypatch)
