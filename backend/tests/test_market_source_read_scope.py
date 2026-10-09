"""Actual scoped source reads retain current authority and immutable job checks."""

from concurrent.futures import ThreadPoolExecutor
from contextlib import nullcontext
from copy import deepcopy
from hashlib import sha256
import threading

import psycopg
from psycopg import sql
import pytest

from app.economic_contracts import OwnedEconomicRecord
from app.economics import EconomicLedger
from app.market_scenario import MarketScenarioService
from app.market_source_store import MarketSourceDenied
from app.market_source_store import MarketSourceStore
from app.market_candidate_store import MarketCandidateStore, MarketCandidateDenied
from app.runtime_roles import RolePolicyHold
from test_api_economic_scenario import economic_api
from test_market_source_store import PROFILE, source_setup, submit, case
from login_database import login_database, login_scope

pytestmark = pytest.mark.parametrize('login_scope', [PROFILE], indirect=True)


@pytest.mark.parametrize('tenant', [None, '', 'foreign'])
def test_unauthenticated_read_scope_fails_before_connection(tenant, monkeypatch, login_scope):
    _, selected, _ = login_scope
    source = MarketSourceStore('unconnected', selected.schema, principal_provider=lambda: None,
        runtime_identity=(selected, 'authority'))
    candidate = MarketCandidateStore('unconnected', selected.schema, source,
        principal_provider=lambda: None, runtime_identity=(selected, 'authority'))
    monkeypatch.setattr(source, 'connect', lambda: pytest.fail('denied scope opened a connection'))
    for store, error in ((source, MarketSourceDenied), (candidate, MarketCandidateDenied)):
        with pytest.raises(error):
            with store.read_scope(tenant):
                pytest.fail('denied scope entered')


@pytest.fixture
def scoped_record(login_scope, source_setup):
    jobs, _, _ = login_scope
    store, principal = source_setup
    model = OwnedEconomicRecord.model_validate(next(iter(case()[0].records.values())))
    job = submit(jobs, model)
    store.adopt_job('tenant-1', 'economic_input', str(job['job_id']))
    return store, principal, model, job


def test_source_scope_reuses_one_verified_connection_and_closes_it(scoped_record, monkeypatch):
    store, _, model, _ = scoped_record
    connections = []
    connect = store.connect
    def traced():
        conn = connect()
        connections.append(conn)
        return conn
    monkeypatch.setattr(store, 'connect', traced)
    with store.read_scope('tenant-1'):
        assert store.get_economic_input(model.input_id, model.revision) == model.model_dump(mode='python')
        assert store.get_economic_input(model.input_id, model.revision) == model.model_dump(mode='python')
        assert len(connections) == 1 and connections[0].pgconn.used_password
        assert connections[0].execute('SHOW transaction_read_only').fetchone()['transaction_read_only'] == 'on'
        assert connections[0].execute('SHOW transaction_isolation').fetchone()['transaction_isolation'] == 'read committed'
    assert connections[0].closed
    assert store.get_economic_input(model.input_id, model.revision)
    assert len(connections) == 2 and all(conn.closed for conn in connections)


@pytest.mark.parametrize('change', ['scope', 'tenant', 'authenticated'])
def test_source_scope_rejects_current_principal_change_and_resets(scoped_record, change):
    store, principal, model, _ = scoped_record
    original = deepcopy(principal)
    try:
        with pytest.raises(MarketSourceDenied):
            with store.read_scope('tenant-1'):
                assert store.get_economic_input(model.input_id, model.revision)
                if change == 'scope': principal['scopes'].remove('market_source_read')
                elif change == 'tenant': principal['tenant_id'] = 'foreign'
                else: principal['authenticated'] = False
                assert store.get_economic_input(model.input_id, model.revision) is None
    finally:
        principal.clear(); principal.update(original)
    with store.read_scope('tenant-1'):
        assert store.get_economic_input(model.input_id, model.revision)


def test_scope_observes_committed_original_job_corruption(scoped_record, login_scope):
    store, _, model, job = scoped_record
    jobs, _, _ = login_scope
    with pytest.raises(ValueError, match='^market source input rejected$'):
        with store.read_scope('tenant-1'):
            assert store.get_economic_input(model.input_id, model.revision)
            with jobs.connect() as owner:
                table = jobs._table('jobs')
                owner.execute(sql.SQL('ALTER TABLE {} DISABLE TRIGGER ALL').format(table))
                owner.execute(sql.SQL('UPDATE {} SET input_bytes=%s,input_sha256=%s WHERE job_id=%s').format(table),
                    (b'{}', sha256(b'{}').hexdigest(), job['job_id']))
                owner.execute(sql.SQL('ALTER TABLE {} ENABLE TRIGGER ALL').format(table))
            store.get_economic_input(model.input_id, model.revision)


@pytest.mark.parametrize('when', ['entry', 'exit'])
def test_scope_rejects_grant_drift_at_entry_or_exit(scoped_record, login_scope, when):
    store, _, model, _ = scoped_record
    jobs, policy, _ = login_scope
    def change(operation):
        with jobs.connect() as owner:
            owner.execute(sql.SQL(operation+' SELECT ON {}.market_source_records '+
                ('TO' if operation == 'GRANT' else 'FROM')+' {}').format(
                sql.Identifier(policy.schema), sql.Identifier(policy.roles['worker'])))
    try:
        if when == 'entry': change('GRANT')
        with pytest.raises(RolePolicyHold):
            with store.read_scope('tenant-1'):
                assert store.get_economic_input(model.input_id, model.revision)
                change('GRANT')
    finally:
        change('REVOKE')
    with store.read_scope('tenant-1'):
        assert store.get_economic_input(model.input_id, model.revision)


def test_nested_or_failed_scope_cannot_retain_connection(scoped_record, monkeypatch):
    store, _, model, _ = scoped_record
    connections = []
    connect = store.connect
    def traced():
        conn = connect(); connections.append(conn); return conn
    monkeypatch.setattr(store, 'connect', traced)
    with pytest.raises(RuntimeError, match='own controlled interruption'):
        with store.read_scope('tenant-1'):
            with pytest.raises(MarketSourceDenied):
                with store.read_scope('tenant-1'):
                    pytest.fail('nested scope entered')
            assert store.get_economic_input(model.input_id, model.revision)
            raise RuntimeError('own controlled interruption')
    assert len(connections) == 1 and connections[0].closed
    with store.read_scope('tenant-1'):
        assert store.get_economic_input(model.input_id, model.revision)
    assert len(connections) == 2 and all(conn.closed for conn in connections)


def test_scope_connection_is_read_only(scoped_record):
    store, _, model, _ = scoped_record
    with pytest.raises(psycopg.errors.ReadOnlySqlTransaction):
        with store.read_scope('tenant-1'):
            with store._read_context('tenant-1') as conn:
                conn.execute(sql.SQL('INSERT INTO {} SELECT * FROM {} WHERE false').format(
                    store._table('market_source_records'), store._table('market_source_records')))
    assert store.get_economic_input(model.input_id, model.revision)


def test_concurrent_scopes_on_same_store_do_not_share_connections(scoped_record):
    store, _, model, _ = scoped_record
    barrier = threading.Barrier(2)
    def read(_):
        with store.read_scope('tenant-1'):
            with store._read_context('tenant-1') as conn:
                pid = conn.info.backend_pid
            barrier.wait(timeout=10)
            assert store.get_economic_input(model.input_id, model.revision) == model.model_dump(mode='python')
            return pid
    with ThreadPoolExecutor(max_workers=2) as pool:
        pids = list(pool.map(read, range(2)))
    assert len(set(pids)) == 2
    with store.read_scope('tenant-1'):
        assert store.get_economic_input(model.input_id, model.revision)


def test_scoped_pinned_validation_preserves_all_source_checks_and_decimal_ledger(economic_api, monkeypatch):
    _, _, candidates, _, _, request = economic_api
    service = MarketScenarioService(candidates)
    pinned = service.build_candidate(request, 'tenant-1')
    source = candidates._source._source
    calls = {'connections': 0, 'verified_reads': 0}
    connect, verify = source.connect, source._read_in_transaction
    def traced_connect():
        calls['connections'] += 1; return connect()
    def traced_verify(*args, **kwargs):
        calls['verified_reads'] += 1; return verify(*args, **kwargs)
    monkeypatch.setattr(source, 'connect', traced_connect)
    monkeypatch.setattr(source, '_read_in_transaction', traced_verify)
    with monkeypatch.context() as patch:
        patch.setattr(source, 'read_scope', lambda _: nullcontext())
        previous = service.validate_pinned(pinned.scenario_id, pinned.revision, 'tenant-1')
    previous_calls = dict(calls)
    calls.update(connections=0, verified_reads=0)
    current = service.validate_pinned(pinned.scenario_id, pinned.revision, 'tenant-1')
    assert current == previous
    assert calls['connections'] == 1 and previous_calls['connections'] > 20
    assert calls['verified_reads'] == previous_calls['verified_reads'] > 20
    ledger = EconomicLedger(candidates)
    assert ledger.calculate(current[1]) == ledger.calculate(previous[1])
    rights = source.get_input_rights
    monkeypatch.setattr(source, 'get_input_rights', lambda *_: None)
    with pytest.raises(ValueError):
        service.validate_pinned(pinned.scenario_id, pinned.revision, 'tenant-1')
    monkeypatch.setattr(source, 'get_input_rights', rights)
    assert service.validate_pinned(pinned.scenario_id, pinned.revision, 'tenant-1') == previous
