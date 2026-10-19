"""Pure current verification keeps actual source reads and defers no public result."""
import pytest
from concurrent.futures import ThreadPoolExecutor
from contextvars import copy_context
from psycopg import sql

from app import market_candidate_store as candidates
from app.farm_registration_read_scope import _fingerprint
from app.market_source_store import MarketSourceStore
from test_farm_registration_read_scope import (
    registration, authoring, profiles, login_database, original_login_scope,
    login_scope, query_cleanup, pytestmark)


def test_pure_bundle_preserves_every_read_and_has_fewer_reference_audits(registration, monkeypatch):
    farms, args, _ = registration
    store = farms.replay.candidates
    with farms.registration_read_scope(*args):
        farms.read_registration(*args)
        trace = tuple(farms._registration_read.get().lookups)
    audit = candidates.audit_runtime_roles
    read = MarketSourceStore._read_in_transaction
    observed = {'audits': 0, 'reads': []}
    def auditing(*a, **kw):
        observed['audits'] += 1; return audit(*a, **kw)
    def reading(self, conn, tenant, kind, identity, revision, **kw):
        observed['reads'].append((tenant, kind, identity, revision, kw.get('pin', False)))
        return read(self, conn, tenant, kind, identity, revision, **kw)
    monkeypatch.setattr(candidates, 'audit_runtime_roles', auditing)
    monkeypatch.setattr(MarketSourceStore, '_read_in_transaction', reading)
    with store.read_scope(args[0]):
        for name, values, digest in trace:
            assert _fingerprint(getattr(store, name)(*values)) == digest
    baseline = {'audits': observed['audits'], 'reads': list(observed['reads'])}
    observed.update(audits=0, reads=[])
    assert store.verify_current_reads(args[0], trace) is None
    assert observed['reads'] == baseline['reads']
    assert observed['audits'] < baseline['audits']
    assert store._reference_bundle.get() is store._scoped_reader.get() is store._scoped_references.get() is None


@pytest.fixture
def replay_trace(registration):
    farms, args, principal = registration
    with farms.registration_read_scope(*args):
        farms.read_registration(*args)
        trace = tuple(farms._registration_read.get().lookups)
    return farms.replay.candidates, args[0], trace, principal


@pytest.mark.parametrize('change', ['grant', 'principal', 'source', 'connection', 'pointer'])
def test_late_changes_reject_entire_verification_without_a_return(replay_trace, login_scope, monkeypatch, change):
    store, tenant, trace, principal = replay_trace
    base, policy, _ = login_scope
    holds = store._source._holds
    original = holds._market_hold_report
    observed = []
    def changing(*a, **kw):
        result = original(*a, **kw)
        if not observed:
            observed.append(store._scoped_reader.get()[0])
            if change == 'principal': principal['scopes'].discard('market_hold_context_read')
            elif change == 'connection': observed[0].close()
            elif change == 'pointer': monkeypatch.setattr(holds, '_key', b'changed-fixture-key-32-bytes!!!!!!')
            else:
                with base.connect() as conn:
                    table = sql.Identifier(policy.schema, 'market_source_records')
                    if change == 'grant':
                        conn.execute(sql.SQL('GRANT UPDATE ON {} TO {}').format(table, sql.Identifier(policy.roles['authority'])))
                    else:
                        conn.execute(sql.SQL('ALTER TABLE {} DISABLE TRIGGER USER').format(table))
                        conn.execute(sql.SQL("UPDATE {} SET payload_raw=%s,payload_sha256=%s WHERE tenant_id=%s AND kind='input_rights'").format(table),
                            (b'{}', __import__('hashlib').sha256(b'{}').hexdigest(), tenant))
        return result
    monkeypatch.setattr(holds, '_market_hold_report', changing)
    with pytest.raises((ValueError, PermissionError)):
        store.verify_current_reads(tenant, trace)
    assert observed and all(conn.closed for conn in observed)
    assert store._reference_bundle.get() is store._scoped_reader.get() is store._scoped_references.get() is None


@pytest.mark.parametrize('change', ['nested', 'copied_context', 'same_execution_copy', 'copied_close', 'exception'])
def test_bundle_lifetime_cannot_escape_or_reenter(replay_trace, monkeypatch, change):
    store, tenant, trace, _ = replay_trace
    holds = store._source._holds
    original = holds._market_hold_report
    observed = []
    def interrupted(*a, **kw):
        result = original(*a, **kw)
        witness = store._reference_bundle.get()
        observed.append((witness, store._scoped_reader.get()[0]))
        if change == 'nested':
            with pytest.raises(ValueError): store.verify_current_reads(tenant, trace)
        elif change == 'copied_context':
            context = copy_context()
            with ThreadPoolExecutor(max_workers=1) as pool:
                future = pool.submit(context.run, witness.guard, store, tenant)
                with pytest.raises(ValueError): future.result(timeout=10)
        elif change == 'same_execution_copy':
            with pytest.raises(ValueError): copy_context().run(witness.guard, store, tenant)
        elif change == 'copied_close':
            with pytest.raises(ValueError): copy_context().run(witness.close)
        else: raise ValueError('owned fixture interruption')
        return result
    monkeypatch.setattr(holds, '_market_hold_report', interrupted)
    with pytest.raises(ValueError): store.verify_current_reads(tenant, trace)
    assert observed and all(conn.closed and not witness.active for witness, conn in observed)
    assert store._reference_bundle.get() is store._scoped_reader.get() is store._scoped_references.get() is None
    for witness, _ in observed:
        with pytest.raises(ValueError): witness.guard(store, tenant)
    monkeypatch.setattr(holds, '_market_hold_report', original)
    assert store.verify_current_reads(tenant, trace) is None


def test_ineligible_shared_held_binding_uses_original_current_reads(replay_trace, monkeypatch):
    store, tenant, trace, _ = replay_trace
    holds = store._source._holds
    provider = holds._principal_provider
    monkeypatch.setattr(holds, '_principal_provider', lambda: provider())
    assert store.verify_current_reads(tenant, trace) is None
    assert store._reference_bundle.get() is store._scoped_reader.get() is store._scoped_references.get() is None
