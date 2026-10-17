"""Hold/context borrowing must keep actual validation and Decimal results."""
from collections import Counter
from concurrent.futures import ThreadPoolExecutor
from contextvars import ContextVar
from copy import deepcopy
from hashlib import sha256
import hmac
import threading

import psycopg
from psycopg import sql
from app.market_candidate_store import MarketCandidateDenied
from app.market_hold_store import MarketHoldStore, _canonical
from app.thermal_run_store import ThermalRunStore
from app.runtime_roles import RolePolicyHold
from test_market_hold_store import CONTEXT_KEY
import json
import os
from pathlib import Path

import pytest

from app.economics import EconomicLedger
from app.market_scenario import MarketScenarioService
from test_api_economic_scenario import economic_api
from test_market_shared_read_scope import shared
from test_market_candidate_read_scope import audit_cleanup
from test_market_source_store import PROFILE
from login_database import login_database, login_scope

pytestmark = pytest.mark.parametrize('login_scope', [PROFILE], indirect=True)


def test_eligible_scope_reuses_reader_for_current_hold_and_context(shared, monkeypatch):
    _, store, _, pinned = shared
    source, holds = store._source._source, store._source._holds
    contexts = holds._context_store
    connections, checks = [], []
    for owner, label in ((source, 'source'), (store, 'candidate'),
                         (holds, 'holds'), (contexts, 'contexts')):
        original = owner.connect
        def opened(*args, _original=original, _label=label, **kwargs):
            conn = _original(*args, **kwargs)
            connections.append((_label, conn, conn.pgconn.used_password))
            return conn
        monkeypatch.setattr(owner, 'connect', opened)
    for owner, name in ((holds, '_verified'), (holds, '_context'),
                        (contexts, '_decision_context_in_transaction')):
        original = getattr(owner, name)
        def checked(*args, _original=original, _name=name, **kwargs):
            checks.append(_name)
            return _original(*args, **kwargs)
        monkeypatch.setattr(owner, name, checked)
    def read():
        verified = MarketScenarioService(store).validate_pinned(pinned.scenario_id, pinned.revision, 'tenant-1')
        with store.read_scope('tenant-1'):
            ledger = EconomicLedger(store).calculate(verified[1])
        return verified, ledger
    provider = holds._principal_provider
    with monkeypatch.context() as fallback:
        fallback.setattr(holds, '_principal_provider', lambda: provider())
        previous = read()
    previous_connections, previous_checks = list(connections), list(checks)
    connections.clear(); checks.clear()
    current = read()
    assert current == previous and current[1].result_id == previous[1].result_id
    assert checks == previous_checks
    assert all(conn.closed and password for _, conn, password in previous_connections+connections)
    assert store._scoped_reader.get() is source._scoped_reader.get() is None
    before = Counter(label for label, _, _ in previous_connections)
    after = Counter(label for label, _, _ in connections)
    observation = {'same_typed_request_scenario_pin': current[0] == previous[0],
        'same_decimal_ledger_and_result_id': current[1] == previous[1],
        'same_hold_context_validator_sequence': checks == previous_checks,
        'fallback_connections': dict(before), 'eligible_connections': dict(after),
        'all_connections_closed_with_actual_password': True,
        'actual_farm_Runs': 0, 'G0_G4': 'not_assessed'}
    if directory := os.environ.get('OSSF_SHARED_MARKET_EVIDENCE'):
        with (Path(directory)/'held-context-reader-observation.private.json').open('x') as f:
            os.fchmod(f.fileno(),0o400);json.dump(observation,f,sort_keys=True,indent=2)
    assert before['holds'] > 0 and before['contexts'] > 0
    assert after == {'source': 2}, observation


@pytest.fixture
def held(shared):
    jobs, store, principal, pinned = shared
    with jobs.connect() as conn:
        row = conn.execute(sql.SQL('SELECT * FROM {}.market_hold_reports WHERE tenant_id=%s LIMIT 1')
            .format(sql.Identifier(jobs.schema)), ('tenant-1',)).fetchone()
    payload = json.loads(row['payload_raw'])
    return jobs, store, principal, payload


def lookup(store, payload):
    value = store.get_market_hold_report(payload['hold_report_id'])
    assert value is not None and value['hold_report_id']==payload['hold_report_id']
    context = store.get_decision_context('tenant-1', payload['snapshot_id'], payload['decision_context_id'])
    assert context is not None and context['context_sha256'] == payload['context_sha256']
    return value, context


@pytest.mark.parametrize('change', ['holds_provider','contexts_provider','holds_policy','contexts_policy',
    'holds_dsn','contexts_dsn','hold_subclass','context_subclass'])
def test_ineligible_hold_binding_retains_original_reads(held, monkeypatch, change):
    _, store, _, payload = held
    holds = store._source._holds; contexts = holds._context_store
    expected = lookup(store, payload)
    if change.endswith('_provider'):
        owner = holds if change.startswith('holds') else contexts
        provider = owner._principal_provider
        monkeypatch.setattr(owner,'_principal_provider',lambda:provider())
    elif change.endswith('_policy'):
        owner = holds if change.startswith('holds') else contexts
        policy,kind = owner.runtime_identity
        monkeypatch.setattr(owner,'runtime_identity',(deepcopy(policy),kind))
    elif change.endswith('_dsn'):
        owner = holds if change.startswith('holds') else contexts
        monkeypatch.setattr(owner,'dsn',owner.dsn+' ')
    elif change=='hold_subclass':
        class OtherHold(MarketHoldStore):pass
        monkeypatch.setattr(holds,'__class__',OtherHold)
    else:
        class OtherContext(ThermalRunStore):pass
        monkeypatch.setattr(contexts,'__class__',OtherContext)
    connections=[]
    for owner in (holds,contexts):
        original=owner.connect
        def connected(*args,_original=original,**kwargs):
            conn=_original(*args,**kwargs);connections.append((conn,conn.pgconn.used_password));return conn
        monkeypatch.setattr(owner,'connect',connected)
    with store.read_scope('tenant-1'):
        assert lookup(store,payload)==expected
    assert len(connections)==3 and all(conn.closed and password for conn,password in connections)
    assert store._scoped_references.get() is None


@pytest.mark.parametrize('change', ['holds_dsn','contexts_dsn','holds_schema','contexts_schema',
    'holds_policy','contexts_policy','holds_tuple','holds_provider','contexts_provider','holds',
    'contexts','scope_resolver','key','context_verifier','candidate_slot','reference_slot','source_slot'])
def test_active_hold_binding_drift_is_denied_without_fallback(held, monkeypatch, change):
    _,store,_,payload=held
    view=store._source;source=view._source;holds=view._holds;contexts=holds._context_store
    slots=(store._scoped_reader,store._scoped_references,source._scoped_reader)
    before=len(os.listdir('/proc/self/fd'))
    with monkeypatch.context() as mutation:
        for owner in (store,holds,contexts):
            mutation.setattr(owner,'connect',lambda:pytest.fail('changed active references fell back'))
        with pytest.raises(MarketCandidateDenied):
            with store.read_scope('tenant-1'):
                conn=store._scoped_reader.get()[0];lookup(store,payload)
                if change.endswith('_dsn') or change.endswith('_schema'):
                    owner=holds if change.startswith('holds') else contexts
                    attr='dsn' if change.endswith('_dsn') else 'schema'
                    mutation.setattr(owner,attr,getattr(owner,attr)+('_different' if attr=='schema' else ' '))
                elif change.endswith('_policy') or change=='holds_tuple':
                    owner=contexts if change=='contexts_policy' else holds
                    policy,kind=owner.runtime_identity
                    mutation.setattr(owner,'runtime_identity',tuple([policy if change=='holds_tuple' else deepcopy(policy),kind]))
                elif change.endswith('_provider'):
                    owner=holds if change.startswith('holds') else contexts;provider=owner._principal_provider
                    mutation.setattr(owner,'_principal_provider',lambda:provider())
                elif change=='holds':mutation.setattr(view,'_holds',object())
                elif change=='contexts':mutation.setattr(holds,'_context_store',object())
                elif change=='scope_resolver':
                    original=holds._scope_resolver;mutation.setattr(holds,'_scope_resolver',lambda *a:original(*a))
                elif change=='key':mutation.setattr(holds,'_key',b'different-owned-signature-key-32-bytes!')
                elif change=='context_verifier':
                    original=contexts._context_verifier;mutation.setattr(contexts,'_context_verifier',lambda *a:original(*a))
                else:
                    owner,attr={'candidate_slot':(store,'_scoped_reader'),
                        'reference_slot':(store,'_scoped_references'),'source_slot':(source,'_scoped_reader')}[change]
                    mutation.setattr(owner,attr,ContextVar('replaced-held-reader',default=None))
                lookup(store,payload)
    assert conn.closed and all(slot.get() is None for slot in slots)
    assert len(os.listdir('/proc/self/fd'))==before


@pytest.mark.parametrize('change',['market_candidate_read','market_source_read',
    'market_hold_context_read','decision_context_read','authenticated','tenant_id'])
def test_current_reference_rights_are_required(held, monkeypatch, change):
    _,store,principal,payload=held;original=deepcopy(principal)
    holds=store._source._holds;contexts=holds._context_store
    try:
        with pytest.raises(MarketCandidateDenied):
            with store.read_scope('tenant-1'):
                conn=store._scoped_reader.get()[0];lookup(store,payload)
                monkeypatch.setattr(holds,'connect',lambda:pytest.fail('withdrawn hold scope fell back'))
                monkeypatch.setattr(contexts,'connect',lambda:pytest.fail('withdrawn context scope fell back'))
                if change=='authenticated':principal[change]=False
                elif change=='tenant_id':principal[change]='foreign'
                else:principal['scopes'].remove(change)
                store.get_market_hold_report(payload['hold_report_id'])
    finally:principal.clear();principal.update(original)
    assert conn.closed and store._scoped_references.get() is None


@pytest.mark.parametrize('change',['hold_raw','hold_signature','context_raw','context_signature',
    'signed_context_binding','signed_hold_scope'])
def test_committed_reference_corruption_is_reread(held,change):
    jobs,store,_,payload=held;holds=store._source._holds
    with pytest.raises(ValueError,match={'signed_context_binding':'market hold decision context changed','signed_hold_scope':'market hold creation intent changed'}.get(change)):
        with store.read_scope('tenant-1'):
            conn=store._scoped_reader.get()[0];lookup(store,payload)
            with jobs.connect() as owner:
                context=change.startswith('context') or change=='signed_context_binding'
                table=jobs._table('decision_contexts' if context else 'market_hold_reports')
                owner.execute(sql.SQL('ALTER TABLE {} DISABLE TRIGGER USER').format(table))
                column='decision_context_id' if context else 'hold_report_id'
                identity=payload['decision_context_id'] if context else payload['hold_report_id']
                row=owner.execute(sql.SQL('SELECT * FROM {} WHERE tenant_id=%s AND {}=%s').format(table,sql.Identifier(column)),('tenant-1',identity)).fetchone()
                if change.endswith('signature'):
                    field='context_signature' if context else 'signature'
                    owner.execute(sql.SQL('UPDATE {} SET {}=%s WHERE tenant_id=%s AND {}=%s').format(table,sql.Identifier(field),sql.Identifier(column)),('0'*64,'tenant-1',identity))
                else:
                    raw_field='context_raw' if context else 'payload_raw'
                    hash_field='context_sha256' if context else 'payload_sha256'
                    document=json.loads(row[raw_field])
                    if context:document['planning_event_sha256']='f'*64
                    elif change=='signed_hold_scope':document['scope']['candidate_ids']=['foreign-crop']
                    else:document['reasons']=['forged-test-reason']
                    raw=_canonical(document);assignments=[sql.SQL('{}=%s').format(sql.Identifier(raw_field)),sql.SQL('{}=%s').format(sql.Identifier(hash_field))];values=[raw,sha256(raw).hexdigest()]
                    if change=='signed_context_binding':
                        assignments.append(sql.SQL('context_signature=%s'));values.append(hmac.new(CONTEXT_KEY,b'decision-context-v1\0'+raw,sha256).hexdigest())
                    if change=='signed_hold_scope':assignments.append(sql.SQL('signature=%s'));values.append(holds._signature(raw))
                    owner.execute(sql.SQL('UPDATE {} SET {} WHERE tenant_id=%s AND {}=%s').format(table,sql.SQL(',').join(assignments),sql.Identifier(column)),(*values,'tenant-1',identity))
                owner.execute(sql.SQL('ALTER TABLE {} ENABLE TRIGGER USER').format(table))
            store.get_market_hold_report(payload['hold_report_id'])
    assert conn.closed and store._scoped_references.get() is None


@pytest.mark.parametrize('change',['read_write','repeatable_read','autocommit','closed'])
def test_reference_read_rechecks_actual_session(held,monkeypatch,change):
    _,store,_,payload=held
    with pytest.raises((MarketCandidateDenied,RolePolicyHold)):
        with store.read_scope('tenant-1'):
            conn=store._scoped_reader.get()[0];lookup(store,payload)
            for owner in (store._source._holds,store._source._holds._context_store):
                monkeypatch.setattr(owner,'connect',lambda:pytest.fail('changed session fell back'))
            if change=='closed':conn.close()
            else:
                conn.commit()
                if change=='autocommit':conn.autocommit=True
                else:conn.execute('BEGIN ISOLATION LEVEL '+('READ COMMITTED READ WRITE' if change=='read_write' else 'REPEATABLE READ READ ONLY'))
            store.get_market_hold_report(payload['hold_report_id'])
    assert conn.closed and store._scoped_references.get() is None


@pytest.mark.parametrize('change',['extra_grant','effective_role'])
def test_reference_read_rechecks_actual_roles(held,change):
    jobs,store,_,payload=held;policy=store.runtime_identity[0]
    try:
        with pytest.raises(RolePolicyHold):
            with store.read_scope('tenant-1'):
                conn=store._scoped_reader.get()[0];lookup(store,payload)
                with jobs.connect() as owner:
                    if change=='extra_grant':owner.execute(sql.SQL('GRANT SELECT ON {} TO {}').format(jobs._table('market_hold_reports'),sql.Identifier(policy.roles['worker'])))
                    else:
                        owner.execute(sql.SQL('GRANT {} TO {} WITH SET TRUE').format(sql.Identifier(policy.roles['worker']),sql.Identifier(policy.roles['authority'])))
                        assert owner.execute('SELECT set_option FROM pg_auth_members WHERE roleid=%s::regrole AND member=%s::regrole',(policy.roles['worker'],policy.roles['authority'])).fetchone()['set_option']
                if change=='effective_role':
                    conn.commit();conn.execute('BEGIN ISOLATION LEVEL READ COMMITTED READ ONLY')
                    conn.execute(sql.SQL('SET ROLE {}').format(sql.Identifier(policy.roles['worker'])))
                    assert conn.execute('SELECT current_user AS effective').fetchone()['effective']==policy.roles['worker']
                store.get_market_hold_report(payload['hold_report_id'])
    finally:
        with jobs.connect() as owner:
            if change=='extra_grant':owner.execute(sql.SQL('REVOKE SELECT ON {} FROM {}').format(jobs._table('market_hold_reports'),sql.Identifier(policy.roles['worker'])))
            else:owner.execute(sql.SQL('REVOKE {} FROM {}').format(sql.Identifier(policy.roles['worker']),sql.Identifier(policy.roles['authority'])))
    assert conn.closed and store._scoped_references.get() is None


@pytest.mark.parametrize('change',['provider','rights'])
def test_reference_authority_is_rechecked_after_private_read(held,monkeypatch,change):
    _,store,principal,payload=held;holds=store._source._holds;original=holds._market_hold_report;provider=holds._principal_provider;before=deepcopy(principal)
    def late(*args,**kwargs):
        value=original(*args,**kwargs)
        assert kwargs['conn'] is store._scoped_reader.get()[0]
        if change=='provider':monkeypatch.setattr(holds,'_principal_provider',lambda:provider())
        else:principal['scopes'].remove('market_hold_context_read')
        return value
    monkeypatch.setattr(holds,'_market_hold_report',late)
    try:
        with pytest.raises(MarketCandidateDenied):
            with store.read_scope('tenant-1'):
                conn=store._scoped_reader.get()[0]
                store.get_market_hold_report(payload['hold_report_id'])
    finally:principal.clear();principal.update(before)
    assert conn.closed and store._scoped_references.get() is None


def test_unscoped_reads_nested_and_exception_ownership(held,monkeypatch):
    _,store,_,payload=held;holds=store._source._holds;contexts=holds._context_store
    expected=lookup(store,payload)
    with monkeypatch.context() as active:
        active.setattr(holds,'connect',lambda:pytest.fail('eligible hold read opened connection'))
        active.setattr(contexts,'connect',lambda:pytest.fail('eligible context read opened connection'))
        with pytest.raises(LookupError):
            with store.read_scope('tenant-1'):
                conn=store._scoped_reader.get()[0]
                assert lookup(store,payload)==expected
                with pytest.raises(MarketCandidateDenied):
                    with store.read_scope('tenant-1'):pytest.fail('nested scope accepted')
                with pytest.raises(psycopg.errors.ReadOnlySqlTransaction):
                    with conn.transaction():conn.execute('CREATE TEMP TABLE held_scope_write_rejected(n int)')
                assert lookup(store,payload)==expected
                raise LookupError('owned test exception')
    assert conn.closed and store._scoped_references.get() is None
    assert lookup(store,payload)==expected


def test_concurrent_reference_scopes_keep_distinct_owners(held):
    _,store,_,payload=held;barrier=threading.Barrier(2);expected=lookup(store,payload)
    def read(_):
        with store.read_scope('tenant-1'):
            conn=store._scoped_reader.get()[0];barrier.wait(timeout=20)
            assert lookup(store,payload)==expected
            pid=conn.info.backend_pid
        assert conn.closed and store._scoped_references.get() is None
        return pid
    with ThreadPoolExecutor(max_workers=2) as pool:pids=list(pool.map(read,range(2)))
    assert len(set(pids))==2 and store._scoped_references.get() is None


def test_changed_scope_resolver_contents_are_rechecked(held,monkeypatch):
    _,store,_,payload=held;holds=store._source._holds;scope=deepcopy(payload['scope'])
    monkeypatch.setattr(holds,'_scope_resolver',lambda *_:deepcopy(scope))
    with pytest.raises(ValueError,match='market hold evaluation scope changed'):
        with store.read_scope('tenant-1'):
            conn=store._scoped_reader.get()[0];lookup(store,payload)
            scope['candidate_ids']=['different-owned-crop']
            store.get_market_hold_report(payload['hold_report_id'])
    assert conn.closed and store._scoped_references.get() is None
