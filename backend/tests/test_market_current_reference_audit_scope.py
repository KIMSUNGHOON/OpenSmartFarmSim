"""One pure verification is enclosed by actual source entry/exit role audits."""
import asyncio
from contextlib import contextmanager
from contextvars import ContextVar
import pytest
from psycopg import sql

from app import market_candidate_store as candidates
from app import market_runtime, market_source_store
from app.runtime_login import connect_runtime
from test_market_current_reference_bundle import (
    replay_trace, registration, authoring, profiles, login_database,
    original_login_scope, login_scope, query_cleanup, pytestmark)


def test_shared_pure_verification_uses_source_audits_without_inner_duplicates(replay_trace, monkeypatch):
    store, tenant, trace, _ = replay_trace
    calls = {'candidate': 0, 'source_entry': 0, 'source_exit': 0}
    for module, label in ((candidates, 'candidate'), (market_runtime, 'source_entry'),
                          (market_source_store, 'source_exit')):
        original = module.audit_runtime_roles
        def audit(*args, _original=original, _label=label, **kwargs):
            calls[_label] += 1
            return _original(*args, **kwargs)
        monkeypatch.setattr(module, 'audit_runtime_roles', audit)
    assert store.verify_current_reads(tenant, trace) is None
    assert calls == {'candidate': 0, 'source_entry': 1, 'source_exit': 1}
    assert store._reference_bundle.get() is store._scoped_reader.get() is store._scoped_references.get() is None
    assert store._source._source._scoped_reader.get() is None


@pytest.mark.parametrize('change', ['grant_before', 'candidate_scope_after', 'held_scope_after',
    'provider_after', 'slot_after', 'held_key_after', 'exception_after',
    'source_scope_after', 'source_connect_after', 'view_scope_after'])
def test_source_exit_drift_or_exception_blocks_return_and_cleans_owned_slots(
        replay_trace, login_scope, monkeypatch, change):
    store, tenant, trace, principal = replay_trace
    base, policy, _ = login_scope
    source, holds = store._source._source, store._source._holds
    slots = (store._reference_bundle, store._scoped_reader, store._scoped_references, source._scoped_reader)
    original = market_source_store.audit_runtime_roles
    observed = []
    def at_exit(conn, *args, **kwargs):
        observed.append(conn)
        if change == 'grant_before':
            with base.connect() as admin:
                admin.execute(sql.SQL('GRANT UPDATE ON {} TO {}').format(
                    sql.Identifier(policy.schema, 'market_source_records'),
                    sql.Identifier(policy.roles['authority'])))
        result = original(conn, *args, **kwargs)
        if change == 'candidate_scope_after': principal['scopes'].discard('market_candidate_read')
        elif change == 'held_scope_after': principal['scopes'].discard('market_hold_context_read')
        elif change == 'provider_after':
            provider = source._principal_provider
            monkeypatch.setattr(source, '_principal_provider', lambda: provider())
        elif change == 'slot_after': monkeypatch.setattr(source, '_scoped_reader', ContextVar('changed_source_slot', default=None))
        elif change == 'held_key_after': monkeypatch.setattr(holds, '_key', b'changed-fixture-key-32-bytes!!!!!!')
        elif change == 'exception_after': raise ValueError('owned source exit interruption')
        elif change == 'source_scope_after':
            scope = source.read_scope
            monkeypatch.setattr(source, 'read_scope', lambda tenant: scope(tenant))
        elif change == 'source_connect_after':
            connect = source.connect
            monkeypatch.setattr(source, 'connect', lambda: connect())
        elif change == 'view_scope_after':
            scope = store._source.read_scope
            monkeypatch.setattr(store._source, 'read_scope', lambda tenant: scope(tenant))
        return result
    monkeypatch.setattr(market_source_store, 'audit_runtime_roles', at_exit)
    with pytest.raises((ValueError, PermissionError)):
        store.verify_current_reads(tenant, trace)
    assert len(observed) == 1 and observed[0].closed
    assert all(slot.get() is None for slot in slots)


@pytest.mark.parametrize('change', ['candidate_provider', 'view_provider', 'held_provider'])
def test_incompatible_bindings_keep_original_getters_and_audits(replay_trace, monkeypatch, change):
    store, tenant, trace, _ = replay_trace
    target = {'candidate_provider':store, 'view_provider':store._source,
              'held_provider':store._source._holds}[change]
    provider = target._principal_provider
    monkeypatch.setattr(target, '_principal_provider', lambda: provider())
    observed = {'candidate':0, 'source_entry':0, 'source_exit':0}
    for module, label in ((candidates, 'candidate'), (market_runtime, 'source_entry'),
                          (market_source_store, 'source_exit')):
        original = module.audit_runtime_roles
        def audit(*args, _original=original, _label=label, **kwargs):
            observed[_label] += 1
            return _original(*args, **kwargs)
        monkeypatch.setattr(module, 'audit_runtime_roles', audit)
    with store.read_scope(tenant):
        for name, args, digest in trace:
            assert candidates.market_reference_bundle.fingerprint(getattr(store, name)(*args)) == digest
    baseline = dict(observed)
    observed.update(candidate=0, source_entry=0, source_exit=0)
    assert store.verify_current_reads(tenant, trace) is None
    assert observed == baseline
    assert store._reference_bundle.get() is store._scoped_reader.get() is store._scoped_references.get() is None


def test_next_operation_reaudits_actual_grants_before_reading_sources(replay_trace, login_scope, monkeypatch):
    store, tenant, trace, _ = replay_trace
    base, policy, _ = login_scope
    observed = []
    original = market_source_store.MarketSourceStore._read_in_transaction
    def reading(self, conn, *args, **kwargs):
        observed.append(conn)
        return original(self, conn, *args, **kwargs)
    monkeypatch.setattr(market_source_store.MarketSourceStore, '_read_in_transaction', reading)
    assert store.verify_current_reads(tenant, trace) is None
    first = len(observed); assert first and all(conn.closed for conn in observed)
    table, role = sql.Identifier(policy.schema, 'market_source_records'), sql.Identifier(policy.roles['authority'])
    with base.connect() as conn: conn.execute(sql.SQL('GRANT UPDATE ON {} TO {}').format(table, role))
    try:
        with pytest.raises(ValueError): store.verify_current_reads(tenant, trace)
        assert len(observed) == first
    finally:
        with base.connect() as conn: conn.execute(sql.SQL('REVOKE UPDATE ON {} FROM {}').format(table, role))
    assert store.verify_current_reads(tenant, trace) is None
    assert len(observed) == first*2 and all(conn.closed for conn in observed)


def test_different_task_poisons_lifetime_and_next_operation_is_fresh(replay_trace, monkeypatch):
    store, tenant, trace, _ = replay_trace
    holds = store._source._holds
    original = holds._market_hold_report
    observed = []
    def crossing_task(*args, **kwargs):
        result = original(*args, **kwargs)
        witness = store._reference_bundle.get()
        observed.append((witness, store._scoped_reader.get()[0]))
        async def copied():
            with pytest.raises(ValueError): witness.guard(store, tenant)
        asyncio.run(copied())
        return result
    monkeypatch.setattr(holds, '_market_hold_report', crossing_task)
    with pytest.raises(ValueError): store.verify_current_reads(tenant, trace)
    assert observed and all(not witness.active and conn.closed for witness, conn in observed)
    monkeypatch.setattr(holds, '_market_hold_report', original)
    assert store.verify_current_reads(tenant, trace) is None


def test_verification_cannot_take_over_an_existing_ordinary_scope(replay_trace):
    store, tenant, trace, _ = replay_trace
    with store.read_scope(tenant):
        current = store._scoped_reader.get()
        with pytest.raises(ValueError): store.verify_current_reads(tenant, trace)
        assert store._scoped_reader.get() is current and not current[0].closed
    assert current[0].closed
    assert store.verify_current_reads(tenant, trace) is None


@pytest.mark.parametrize('target', ['source', 'view'])
def test_replaced_scope_cannot_omit_final_role_audit(replay_trace, login_scope, monkeypatch, target):
    store, tenant, trace, _ = replay_trace
    base, policy, _ = login_scope
    source, view, holds = store._source._source, store._source, store._source._holds
    source_scope = source.read_scope
    @contextmanager
    def incomplete_scope(tenant):
        original = source_scope(tenant)
        conn = original.__enter__()
        try: yield conn
        finally: original.gen.close()
    monkeypatch.setattr(source if target == 'source' else view, 'read_scope', incomplete_scope)
    original = holds._market_hold_report
    observed = []
    def grant_during_read(*args, **kwargs):
        value = original(*args, **kwargs)
        if not observed:
            observed.append(True)
            with base.connect() as conn:
                conn.execute(sql.SQL('GRANT UPDATE ON {} TO {}').format(
                    sql.Identifier(policy.schema, 'market_source_records'),
                    sql.Identifier(policy.roles['authority'])))
        return value
    monkeypatch.setattr(holds, '_market_hold_report', grant_during_read)
    with pytest.raises(ValueError): store.verify_current_reads(tenant, trace)
    assert observed
    assert store._reference_bundle.get() is store._scoped_reader.get() is store._scoped_references.get() is None
    assert source._scoped_reader.get() is None


def test_replaced_connector_cannot_defer_first_role_audit_until_after_reads(replay_trace, login_scope, monkeypatch):
    store, tenant, trace, _ = replay_trace
    base, policy, _ = login_scope
    source = store._source._source
    with base.connect() as conn:
        conn.execute(sql.SQL('GRANT UPDATE ON {} TO {}').format(
            sql.Identifier(policy.schema, 'market_source_records'),
            sql.Identifier(policy.roles['authority'])))
    monkeypatch.setattr(source, 'connect', lambda: connect_runtime(source.dsn, *source.runtime_identity))
    original = market_source_store.MarketSourceStore._read_in_transaction
    reads = []
    def reading(self, conn, *args, **kwargs):
        reads.append(True)
        return original(self, conn, *args, **kwargs)
    monkeypatch.setattr(market_source_store.MarketSourceStore, '_read_in_transaction', reading)
    with pytest.raises(ValueError): store.verify_current_reads(tenant, trace)
    assert not reads
    assert store._reference_bundle.get() is store._scoped_reader.get() is store._scoped_references.get() is None
    assert source._scoped_reader.get() is None
