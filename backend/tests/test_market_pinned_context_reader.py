"""Current farm references use the established owned reader, never a data cache."""
from collections import Counter
from copy import deepcopy
import json
import os
from pathlib import Path

import pytest
from psycopg import sql

from app.market_scenario import MarketScenarioService
from test_api_economic_scenario import economic_api
from test_market_shared_read_scope import shared
from test_market_source_store import PROFILE
from login_database import login_database, login_scope

pytestmark = pytest.mark.parametrize('login_scope', [PROFILE], indirect=True)


def reference_ids(store, pinned):
    request, _, _ = MarketScenarioService(store).validate_pinned(
        pinned.scenario_id, pinned.revision, 'tenant-1')
    report = store.get_market_hold_report(request.market_context.hold_report_id)
    return report['snapshot_id'], report['decision_context_id'], report['hold_report_id']


def test_current_context_pin_and_checks_match_with_fewer_owned_connections(shared, monkeypatch):
    _, store, _, pinned = shared
    snapshot, context_id, hold_id = reference_ids(store, pinned)
    holds = store._source._holds
    contexts = holds._context_store
    connections, checks = [], []
    for owner, label in ((store._source._source, 'source'), (store, 'candidate'),
                         (holds, 'holds'), (contexts, 'contexts')):
        original = owner.connect
        def connect(*args, _original=original, _label=label, **kwargs):
            conn = _original(*args, **kwargs)
            connections.append((_label, conn, conn.pgconn.used_password))
            return conn
        monkeypatch.setattr(owner, 'connect', connect)
    for owner, name in ((holds, '_verified'), (contexts, '_decision_context_in_transaction')):
        original = getattr(owner, name)
        def checked(*args, _original=original, _name=name, **kwargs):
            checks.append(_name)
            return _original(*args, **kwargs)
        monkeypatch.setattr(owner, name, checked)
    service = MarketScenarioService(store)
    baseline = (contexts.get_decision_context('tenant-1', snapshot, context_id),
        holds.get_market_hold_report(hold_id),
        service.validate_pinned(pinned.scenario_id, pinned.revision, 'tenant-1'))
    previous, previous_checks = list(connections), list(checks)
    connections.clear(); checks.clear()
    actual = service.validate_pinned_context(pinned.scenario_id, pinned.revision,
        'tenant-1', snapshot, context_id, hold_id)
    assert actual == baseline and checks == previous_checks
    assert Counter(label for label, _, _ in connections) == {'source': 1}
    assert len(previous) > len(connections)
    assert all(conn.closed and password for _, conn, password in previous+connections)
    assert store._scoped_reader.get() is store._source._source._scoped_reader.get() is None
    if directory := os.environ.get('OSSF_SHARED_MARKET_EVIDENCE'):
        evidence = {'original_connections':dict(Counter(label for label, _, _ in previous)),
            'current_connections':dict(Counter(label for label, _, _ in connections)),
            'identical_context_hold_typed_pin':actual == baseline,
            'identical_current_validator_sequence':checks == previous_checks,
            'all_actual_SCRAM_connections_owned_and_closed':True}
        with (Path(directory)/'pinned-context-reader.private.json').open('x') as handle:
            os.fchmod(handle.fileno(), 0o400);json.dump(evidence, handle, sort_keys=True)


@pytest.mark.parametrize('scope', ['decision_context_read', 'market_hold_context_read',
                                    'market_candidate_read', 'market_source_read'])
def test_a_later_call_observes_current_scope_revocation(shared, scope):
    _, store, principal, pinned = shared
    args = reference_ids(store, pinned)
    service = MarketScenarioService(store)
    before = service.validate_pinned_context(pinned.scenario_id, pinned.revision, 'tenant-1', *args)
    original = deepcopy(principal['scopes'])
    try:
        principal['scopes'].remove(scope)
        with pytest.raises((ValueError, PermissionError)):
            service.validate_pinned_context(pinned.scenario_id, pinned.revision, 'tenant-1', *args)
    finally:
        principal['scopes'] = original
    assert service.validate_pinned_context(pinned.scenario_id, pinned.revision, 'tenant-1', *args) == before
    assert store._scoped_reader.get() is store._source._source._scoped_reader.get() is None


def test_ineligible_hold_provider_retains_independent_reads(shared, monkeypatch):
    _, store, _, pinned = shared
    args = reference_ids(store, pinned)
    service = MarketScenarioService(store)
    expected = service.validate_pinned_context(pinned.scenario_id, pinned.revision, 'tenant-1', *args)
    holds = store._source._holds
    provider = holds._principal_provider
    monkeypatch.setattr(holds, '_principal_provider', lambda: provider())
    connections = []
    for owner in (holds, holds._context_store):
        original = owner.connect
        def connect(*args, _original=original, **kwargs):
            conn = _original(*args, **kwargs)
            connections.append((conn, conn.pgconn.used_password));return conn
        monkeypatch.setattr(owner, 'connect', connect)
    assert service.validate_pinned_context(pinned.scenario_id, pinned.revision, 'tenant-1', *args) == expected
    assert connections and all(conn.closed and password for conn, password in connections)
    assert store._scoped_reader.get() is store._scoped_references.get() is None


@pytest.mark.parametrize('change', ['hold_signature', 'context_signature'])
def test_committed_corruption_between_reference_and_pin_is_not_cached(shared, monkeypatch, change):
    jobs, store, _, pinned = shared
    snapshot, context_id, hold_id = reference_ids(store, pinned)
    service = MarketScenarioService(store)
    original = service._validate_pinned
    def changed(*args):
        table_name = 'market_hold_reports' if change == 'hold_signature' else 'decision_contexts'
        field = 'signature' if change == 'hold_signature' else 'context_signature'
        column = 'hold_report_id' if change == 'hold_signature' else 'decision_context_id'
        identity = hold_id if change == 'hold_signature' else context_id
        table = jobs._table(table_name)
        with jobs.connect() as owner:
            owner.execute(sql.SQL('ALTER TABLE {} DISABLE TRIGGER USER').format(table))
            owner.execute(sql.SQL('UPDATE {} SET {}=%s WHERE tenant_id=%s AND {}=%s')
                .format(table, sql.Identifier(field), sql.Identifier(column)),
                ('0'*64, 'tenant-1', identity))
            owner.execute(sql.SQL('ALTER TABLE {} ENABLE TRIGGER USER').format(table))
        return original(*args)
    monkeypatch.setattr(service, '_validate_pinned', changed)
    with pytest.raises(ValueError):
        service.validate_pinned_context(pinned.scenario_id, pinned.revision,
            'tenant-1', snapshot, context_id, hold_id)
    assert store._scoped_reader.get() is store._scoped_references.get() is None


@pytest.mark.parametrize('change', ['provider', 'key', 'transaction'])
def test_active_reference_binding_changes_fail_without_new_connections(shared, monkeypatch, change):
    _, store, _, pinned = shared
    args = reference_ids(store, pinned)
    service = MarketScenarioService(store)
    holds = store._source._holds
    original = service._validate_pinned
    owned = []
    def changed(*values):
        conn = store._scoped_reader.get()[0];owned.append(conn)
        for owner in (store, holds, holds._context_store):
            monkeypatch.setattr(owner, 'connect', lambda: pytest.fail('active binding used fallback'))
        if change == 'provider':
            provider = holds._principal_provider
            monkeypatch.setattr(holds, '_principal_provider', lambda: provider())
        elif change == 'key':
            monkeypatch.setattr(holds, '_key', b'different-owned-test-signature-key!')
        else:
            conn.commit();conn.execute('BEGIN ISOLATION LEVEL READ COMMITTED READ WRITE')
        return original(*values)
    monkeypatch.setattr(service, '_validate_pinned', changed)
    with pytest.raises(ValueError):
        service.validate_pinned_context(pinned.scenario_id, pinned.revision, 'tenant-1', *args)
    assert owned and all(conn.closed for conn in owned)
    assert store._scoped_reader.get() is store._scoped_references.get() is None
