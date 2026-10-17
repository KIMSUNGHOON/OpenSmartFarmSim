"""A shared reader preserves real SCRAM identity, current values, and ownership."""
from contextlib import contextmanager
from contextvars import ContextVar
from copy import deepcopy
import json
import os
from pathlib import Path

import psycopg
from psycopg import sql
import pytest

from app.api_market_source import _MarketSources
from app.economics import EconomicLedger
from app.market_candidate_store import MarketCandidateDenied
from app.market_scenario import MarketScenarioService
from app.market_source_store import MarketSourceStore
from app.runtime_roles import RolePolicyHold
from test_api_economic_scenario import economic_api
from test_market_source_store import PROFILE
from test_market_candidate_read_scope import audit_cleanup
from login_database import login_database, login_scope

pytestmark = pytest.mark.parametrize('login_scope', [PROFILE], indirect=True)


@pytest.fixture
def shared(economic_api, login_scope):
    _, _, store, principal, _, request = economic_api
    pinned = MarketScenarioService(store).build_candidate(request, 'tenant-1')
    return login_scope[0], store, principal, pinned


def test_one_source_owned_reader_preserves_full_validation_and_decimal_result(shared, monkeypatch):
    _, store, _, pinned = shared
    view, source = store._source, store._source._source
    connections, checks = [], []
    for owner, label in ((source, 'source'), (store, 'candidate')):
        original = owner.connect
        def traced(*args, _original=original, _label=label, **kwargs):
            conn = _original(*args, **kwargs)
            connections.append((_label, conn, conn.pgconn.used_password))
            return conn
        monkeypatch.setattr(owner, 'connect', traced)
    for owner, name in ((store, '_candidate_in_transaction'), (store, '_input_in_transaction'),
                        (source, '_read_in_transaction')):
        original = getattr(owner, name)
        def traced(*args, _original=original, _name=name, **kwargs):
            checks.append(_name)
            return _original(*args, **kwargs)
        monkeypatch.setattr(owner, name, traced)
    def read():
        result = MarketScenarioService(store).validate_pinned(pinned.scenario_id, pinned.revision, 'tenant-1')
        with store.read_scope('tenant-1'):
            ledger = EconomicLedger(store).calculate(result[1])
        return result, ledger
    with monkeypatch.context() as fallback:
        original = view._principal_provider
        fallback.setattr(view, '_principal_provider', lambda: original())
        previous = read()
    old_connections, old_checks = list(connections), list(checks)
    connections.clear(); checks.clear()
    current = read()
    assert current == previous and current[1].result_id == previous[1].result_id
    assert checks == old_checks
    assert [label for label, _, _ in old_connections] == ['source', 'candidate']*2
    assert [label for label, _, _ in connections] == ['source']*2
    assert all(conn.closed and password for _, conn, password in old_connections+connections)
    with store.read_scope('tenant-1'):
        conn = store._scoped_reader.get()[0]
        assert conn is source._scoped_reader.get()[0]
        identity = conn.execute('SELECT session_user AS authenticated, current_user AS effective, current_database() AS database').fetchone()
        policy, kind = store.runtime_identity
        assert identity == {'authenticated': policy.roles[kind], 'effective': policy.roles[kind], 'database': policy.database}
        assert conn.execute('SHOW transaction_read_only').fetchone()['transaction_read_only'] == 'on'
        assert conn.execute('SHOW transaction_isolation').fetchone()['transaction_isolation'] == 'read committed'
    assert conn.closed and store._scoped_reader.get() is source._scoped_reader.get() is None
    if root := os.environ.get('OSSF_SHARED_MARKET_EVIDENCE'):
        with (Path(root)/'shared-reader-observation.private.json').open('x') as f:
            os.fchmod(f.fileno(), 0o400)
            json.dump({'same_typed_request_scenario_pin': current[0] == previous[0],
                       'same_decimal_ledger_and_result_id': current[1] == previous[1],
                       'same_check_sequence': checks == old_checks,
                       'legacy_candidate_connections': 2, 'legacy_source_connections': 2,
                       'shared_candidate_connections': 0, 'shared_source_connections': 2,
                       'actual_scram_password': True, 'all_connections_closed': True,
                       'actual_crop_Runs': 0, 'G0_G4': 'not_assessed'}, f, sort_keys=True)


@pytest.mark.parametrize('change', ['provider', 'dsn', 'policy_object', 'wrapper_type', 'legacy_candidate'])
def test_ineligible_profile_keeps_two_separately_owned_connections(shared, monkeypatch, change):
    _, store, _, pinned = shared
    view, source = store._source, store._source._source
    if change == 'provider':
        original = view._principal_provider
        monkeypatch.setattr(view, '_principal_provider', lambda: original())
    elif change == 'dsn': monkeypatch.setattr(store, 'dsn', store.dsn+' ')
    elif change == 'policy_object':
        policy, kind = store.runtime_identity
        monkeypatch.setattr(store, 'runtime_identity', (deepcopy(policy), kind))
    elif change == 'wrapper_type':
        class OtherView(_MarketSources):
            pass
        monkeypatch.setattr(store, '_source', OtherView(source, view._holds, principal_provider=view._principal_provider))
    else: monkeypatch.setattr(store, 'runtime_identity', None)
    with store.read_scope('tenant-1'):
        candidate_conn = store._scoped_reader.get()[0]
        source_conn = source._scoped_reader.get()[0]
        assert candidate_conn is not source_conn
        assert candidate_conn.pgconn.used_password and source_conn.pgconn.used_password
        assert store.get_market_candidate(pinned.scenario_id, pinned.revision)
    assert candidate_conn.closed and source_conn.closed
    assert store._scoped_reader.get() is source._scoped_reader.get() is None


@pytest.mark.parametrize('change', ['candidate_dsn', 'source_dsn', 'both_dsn', 'source_schema', 'both_schema',
    'candidate_policy', 'both_policy', 'wrapper_provider', 'source_provider', 'candidate_provider',
    'wrapper', 'source', 'holds', 'candidate_slot', 'source_slot'])
def test_shared_binding_drift_is_denied_without_fallback_or_context_leaks(shared, monkeypatch, change):
    _, store, _, pinned = shared
    view, source = store._source, store._source._source
    candidate_slot, source_slot = store._scoped_reader, source._scoped_reader
    monkeypatch.setattr(store, 'connect', lambda: pytest.fail('changed shared reader silently fell back'))
    descriptors = len(os.listdir('/proc/self/fd'))
    with monkeypatch.context() as mutation:
        with pytest.raises(MarketCandidateDenied):
            with store.read_scope('tenant-1'):
                conn = store._scoped_reader.get()[0]
                assert store.get_market_candidate(pinned.scenario_id, pinned.revision)
                if change in ('candidate_dsn', 'both_dsn'): mutation.setattr(store, 'dsn', store.dsn+' ')
                if change in ('source_dsn', 'both_dsn'): mutation.setattr(source, 'dsn', source.dsn+' ')
                if change in ('source_schema', 'both_schema'): mutation.setattr(source, 'schema', 'foreign_schema')
                if change == 'both_schema': mutation.setattr(store, 'schema', 'foreign_schema')
                if change in ('candidate_policy', 'both_policy'):
                    policy, kind = store.runtime_identity
                    binding = (deepcopy(policy), kind)
                    mutation.setattr(store, 'runtime_identity', binding)
                    if change == 'both_policy': mutation.setattr(source, 'runtime_identity', binding)
                if change in ('wrapper_provider', 'source_provider', 'candidate_provider'):
                    owner = {'wrapper_provider': view, 'source_provider': source, 'candidate_provider': store}[change]
                    provider = owner._principal_provider
                    mutation.setattr(owner, '_principal_provider', lambda: provider())
                if change == 'wrapper':
                    mutation.setattr(store, '_source', _MarketSources(source, view._holds, principal_provider=view._principal_provider))
                if change == 'source':
                    mutation.setattr(view, '_source', MarketSourceStore(source.dsn, source.schema,
                        runtime_identity=source.runtime_identity, principal_provider=source._principal_provider))
                if change == 'holds': mutation.setattr(view, '_holds', object())
                if change == 'candidate_slot': mutation.setattr(store, '_scoped_reader', ContextVar('replacement-candidate', default=None))
                if change == 'source_slot': mutation.setattr(source, '_scoped_reader', ContextVar('replacement-source', default=None))
    assert conn.closed and candidate_slot.get() is source_slot.get() is None
    assert store._scoped_reader is candidate_slot and source._scoped_reader is source_slot
    assert len(os.listdir('/proc/self/fd')) == descriptors


@pytest.mark.parametrize('change', ['read_write', 'repeatable_read', 'autocommit', 'row_factory'])
def test_shared_session_change_is_denied_and_owner_closes(shared, change):
    _, store, _, _ = shared
    source = store._source._source
    with pytest.raises((MarketCandidateDenied, RolePolicyHold)):
        with store.read_scope('tenant-1'):
            conn = store._scoped_reader.get()[0]
            if change == 'row_factory': conn.row_factory = psycopg.rows.tuple_row
            else:
                conn.commit()
                if change == 'autocommit': conn.autocommit = True
                elif change == 'read_write': conn.execute('BEGIN ISOLATION LEVEL READ COMMITTED READ WRITE')
                else: conn.execute('BEGIN ISOLATION LEVEL REPEATABLE READ READ ONLY')
    assert conn.closed and store._scoped_reader.get() is source._scoped_reader.get() is None


@pytest.mark.parametrize('change', ['closed', 'wrong_type', 'wrong_tenant'])
def test_bad_offered_connection_cannot_trigger_legacy_fallback(shared, monkeypatch, change):
    _, store, _, _ = shared
    source = store._source._source
    scope = source.read_scope
    @contextmanager
    def bad_scope(tenant):
        with scope(tenant) as conn:
            if change == 'closed': conn.close()
            if change == 'wrong_tenant': source._scoped_reader.set((conn, 'foreign'))
            yield object() if change == 'wrong_type' else conn
    monkeypatch.setattr(source, 'read_scope', bad_scope)
    monkeypatch.setattr(store, 'connect', lambda: pytest.fail('invalid offered connection silently fell back'))
    with pytest.raises(MarketCandidateDenied):
        with store.read_scope('tenant-1'): pytest.fail('invalid offered connection entered')
    assert store._scoped_reader.get() is source._scoped_reader.get() is None


def test_effective_sql_role_change_is_rejected(shared):
    jobs, store, _, _ = shared
    source = store._source._source
    policy = store.runtime_identity[0]
    try:
        with pytest.raises(RolePolicyHold):
            with store.read_scope('tenant-1'):
                conn = store._scoped_reader.get()[0]
                with jobs.connect() as owner:
                    owner.execute(sql.SQL('GRANT {} TO {} WITH SET TRUE').format(sql.Identifier(policy.roles['worker']),
                        sql.Identifier(policy.roles['authority'])))
                    membership = owner.execute('SELECT set_option FROM pg_auth_members WHERE roleid=%s::regrole AND member=%s::regrole',
                        (policy.roles['worker'], policy.roles['authority'])).fetchone()
                    assert membership['set_option'] is True
                conn.commit()
                conn.execute('BEGIN ISOLATION LEVEL READ COMMITTED READ ONLY')
                conn.execute(sql.SQL('SET ROLE {}').format(sql.Identifier(policy.roles['worker'])))
                assert conn.execute('SELECT current_user AS effective').fetchone()['effective'] == policy.roles['worker']
    finally:
        with jobs.connect() as owner:
            owner.execute(sql.SQL('REVOKE {} FROM {}').format(sql.Identifier(policy.roles['worker']),
                sql.Identifier(policy.roles['authority'])))
    assert conn.closed and store._scoped_reader.get() is source._scoped_reader.get() is None
