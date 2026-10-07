"""Real SCRAM candidate reads retain current rows, authority and exact results."""
from concurrent.futures import ThreadPoolExecutor
from contextlib import nullcontext
from copy import deepcopy
from hashlib import sha256
import json
import os
from pathlib import Path
import threading
from time import perf_counter

import pytest
import psycopg
from psycopg import sql

from app.economics import EconomicLedger
from app.market_candidate_store import MarketCandidateDenied, _canonical
from app.market_scenario import MarketScenarioService
from app.runtime_roles import RolePolicyHold
from test_api_economic_scenario import economic_api
from test_market_source_store import PROFILE
from login_database import login_database, login_scope, assert_host_scram

pytestmark = pytest.mark.parametrize('login_scope', [PROFILE], indirect=True)


def evidence(name, value):
    if directory := os.environ.get('OSSF_CANDIDATE_SCOPE_EVIDENCE'):
        with (Path(directory)/name).open('x') as handle:
            os.fchmod(handle.fileno(),0o400)
            json.dump(value,handle,sort_keys=True,indent=2);handle.write('\n')
            handle.flush();os.fsync(handle.fileno())


@pytest.fixture(scope='module', autouse=True)
def audit_cleanup(login_database, tmp_path_factory):
    yield
    with psycopg.connect(login_database['admin']) as conn:
        schemas = conn.execute("SELECT count(*) FROM pg_namespace WHERE nspname LIKE 'login_test_%'").fetchone()[0]
        roles = conn.execute("SELECT count(*) FROM pg_roles WHERE rolname LIKE 'login_%'").fetchone()[0]
        methods = assert_host_scram(conn)
    passfiles = list(tmp_path_factory.getbasetemp().rglob('*.pgpass'))
    assert schemas == roles == len(passfiles) == 0
    evidence('database-cleanup.json', {'schemas_after':schemas,'roles_after':roles,
        'passfiles_after':len(passfiles),'server_host_auth_methods':methods})


@pytest.fixture
def candidate(economic_api, login_scope):
    _, _, store, principal, _, request = economic_api
    pinned = MarketScenarioService(store).build_candidate(request, 'tenant-1')
    return login_scope[0], store, principal, pinned


def test_validation_reuses_candidate_connection_without_caching_rows(candidate, monkeypatch):
    _, store, _, pinned = candidate
    source = store._source._source
    connections = []; source_connections = []; checks = []; password_auth = []
    original_connect, original_source_connect = store.connect, source.connect
    def connect():
        conn = original_connect(); connections.append(conn)
        password_auth.append(conn.pgconn.used_password); return conn
    def source_connect():
        conn = original_source_connect(); source_connections.append(conn); return conn
    monkeypatch.setattr(store, 'connect', connect)
    monkeypatch.setattr(source, 'connect', source_connect)
    for owner, name in ((store, '_candidate_in_transaction'), (store, '_input_in_transaction'),
                        (source, '_read_in_transaction')):
        original = getattr(owner, name)
        def traced(*args, _original=original, _name=name, **kwargs):
            checks.append(_name); return _original(*args, **kwargs)
        monkeypatch.setattr(owner, name, traced)
    service = MarketScenarioService(store)
    with monkeypatch.context() as previous:
        previous.setattr(store, 'read_scope', store._source.read_scope)
        start = perf_counter()
        baseline = service.validate_pinned(pinned.scenario_id, pinned.revision, 'tenant-1')
        baseline_seconds = perf_counter()-start
    baseline_connections = len(connections); baseline_source_connections = len(source_connections)
    baseline_checks = list(checks)
    connections.clear(); source_connections.clear(); checks.clear(); password_auth.clear()
    start = perf_counter()
    current = service.validate_pinned(pinned.scenario_id, pinned.revision, 'tenant-1')
    current_seconds = perf_counter()-start
    observation = {'baseline_candidate_connections':baseline_connections,
        'current_candidate_connections':len(connections),
        'baseline_source_connections':baseline_source_connections,
        'current_source_connections':len(source_connections),
        'baseline_seconds':baseline_seconds, 'current_seconds':current_seconds,
        'same_typed_request_scenario_pin':current == baseline,
        'same_candidate_input_source_checks':checks == baseline_checks,
        'current_candidate_password_auth':list(password_auth),
        'checks':{name:checks.count(name) for name in set(checks)}}
    evidence('candidate-read-observation.json', observation)
    assert current == baseline and checks == baseline_checks
    assert baseline_connections > 10 and len(connections) == 1
    assert baseline_source_connections == len(source_connections) == 1
    assert password_auth == [True]
    assert all(conn.closed for conn in connections+source_connections)
    with store.read_scope('tenant-1'):
        actual = EconomicLedger(store).calculate(current[1])
    with store._source.read_scope('tenant-1'):
        expected = EconomicLedger(store).calculate(baseline[1])
    assert actual == expected and actual.result_id == expected.result_id


@pytest.mark.parametrize('change', ['scope','tenant','authenticated'])
def test_denied_scope_opens_no_candidate_connection(candidate, monkeypatch, change):
    _, store, principal, _ = candidate
    if change == 'scope': principal['scopes'].remove('market_candidate_read')
    elif change == 'tenant': principal['tenant_id'] = 'foreign'
    else: principal['authenticated'] = False
    monkeypatch.setattr(store,'connect',lambda:pytest.fail('denied scope connected'))
    with pytest.raises(MarketCandidateDenied):
        with store.read_scope('tenant-1'):pytest.fail('denied scope entered')


@pytest.mark.parametrize('change', ['scope','tenant','authenticated'])
def test_current_principal_withdrawal_cannot_reuse_scope(candidate, change):
    _, store, principal, pinned = candidate
    original = deepcopy(principal)
    try:
        with pytest.raises(MarketCandidateDenied):
            with store.read_scope('tenant-1'):
                assert store.get_market_candidate(pinned.scenario_id,pinned.revision)
                if change == 'scope':principal['scopes'].remove('market_candidate_read')
                elif change == 'tenant':principal['tenant_id']='foreign'
                else:principal['authenticated']=False
                assert store.get_market_candidate(pinned.scenario_id,pinned.revision) is None
    finally:
        principal.clear();principal.update(original)
    assert store._scoped_reader.get() is None
    assert store.get_market_candidate(pinned.scenario_id,pinned.revision)


def test_nested_and_exceptional_scope_closes_connection_and_resets(candidate, monkeypatch):
    _, store, _, pinned = candidate
    connections=[];connect=store.connect;descriptors=len(os.listdir('/proc/self/fd'))
    def traced():
        conn=connect();connections.append(conn);return conn
    monkeypatch.setattr(store,'connect',traced)
    with pytest.raises(RuntimeError,match='controlled interruption'):
        with store.read_scope('tenant-1'):
            with pytest.raises(MarketCandidateDenied):
                with store.read_scope('tenant-1'):pytest.fail('nested scope entered')
            assert store.get_market_candidate(pinned.scenario_id,pinned.revision)
            raise RuntimeError('controlled interruption')
    assert len(connections)==1 and connections[0].closed and store._scoped_reader.get() is None
    with store.read_scope('tenant-1'):
        assert store.get_market_candidate(pinned.scenario_id,pinned.revision)
    assert len(connections)==2 and all(conn.closed for conn in connections)
    assert store.get_market_candidate(pinned.scenario_id,pinned.revision)
    assert len(connections)==3 and all(conn.closed for conn in connections)
    assert len(os.listdir('/proc/self/fd'))==descriptors


def test_candidate_connection_is_read_committed_and_read_only(candidate):
    _,store,_,_=candidate
    with pytest.raises(psycopg.errors.ReadOnlySqlTransaction):
        with store.read_scope('tenant-1'):
            with store._read_context('tenant-1') as conn:
                assert conn.execute('SHOW transaction_read_only').fetchone()['transaction_read_only']=='on'
                assert conn.execute('SHOW transaction_isolation').fetchone()['transaction_isolation']=='read committed'
                conn.execute(sql.SQL('INSERT INTO {} SELECT * FROM {} WHERE false').format(
                    store._table('market_candidate_inputs'),store._table('market_candidate_inputs')))
    assert conn.closed and store._scoped_reader.get() is None


def test_scope_observes_committed_candidate_input_corruption(candidate):
    jobs,store,_,pinned=candidate
    with pytest.raises(ValueError,match='market candidate input manifest hash differs'):
        with store.read_scope('tenant-1'):
            assert store.get_market_candidate(pinned.scenario_id,pinned.revision)
            with jobs.connect() as owner:
                table=store._table('market_candidate_inputs')
                row=owner.execute(sql.SQL('SELECT * FROM {} LIMIT 1').format(table)).fetchone()
                changed=json.loads(row['payload_raw']);changed['value']='777'
                raw=_canonical(changed)
                owner.execute(sql.SQL('ALTER TABLE {} DISABLE TRIGGER ALL').format(table))
                owner.execute(sql.SQL('UPDATE {} SET payload_raw=%s,payload_sha256=%s WHERE tenant_id=%s AND input_id=%s AND revision=%s').format(table),
                    (raw,sha256(raw).hexdigest(),row['tenant_id'],row['input_id'],row['revision']))
                owner.execute(sql.SQL('ALTER TABLE {} ENABLE TRIGGER ALL').format(table))
            store.get_market_candidate(pinned.scenario_id,pinned.revision)
    assert store._scoped_reader.get() is None


def test_rights_withdrawal_still_blocks_validation(candidate,monkeypatch):
    _,store,_,pinned=candidate
    service=MarketScenarioService(store)
    original=service.validate_pinned(pinned.scenario_id,pinned.revision,'tenant-1')
    with monkeypatch.context() as patch:
        patch.setattr(store._source._source,'get_input_rights',lambda *_:None)
        with pytest.raises(ValueError):service.validate_pinned(pinned.scenario_id,pinned.revision,'tenant-1')
    assert store._scoped_reader.get() is None
    assert service.validate_pinned(pinned.scenario_id,pinned.revision,'tenant-1')==original


@pytest.mark.parametrize('when',['entry','exit'])
def test_candidate_scope_audits_current_grants_without_source_scope(candidate,when,monkeypatch):
    jobs,store,_,pinned=candidate
    policy=store.runtime_identity[0]
    monkeypatch.setattr(store._source,'read_scope',lambda _:nullcontext())
    def change(operation):
        with jobs.connect() as owner:
            owner.execute(sql.SQL(operation+' SELECT ON {} '+('TO' if operation=='GRANT' else 'FROM')+' {}').format(
                store._table('market_candidate_pins'),sql.Identifier(policy.roles['worker'])))
    try:
        if when=='entry':change('GRANT')
        with pytest.raises(RolePolicyHold):
            with store.read_scope('tenant-1'):
                assert store.get_market_candidate(pinned.scenario_id,pinned.revision)
                change('GRANT')
    finally:change('REVOKE')
    assert store._scoped_reader.get() is None
    with store.read_scope('tenant-1'):
        assert store.get_market_candidate(pinned.scenario_id,pinned.revision)


def test_concurrent_candidate_scopes_own_distinct_connections(candidate):
    _,store,_,pinned=candidate
    barrier=threading.Barrier(2)
    def read(_):
        with store.read_scope('tenant-1'):
            with store._read_context('tenant-1') as conn:pid=conn.info.backend_pid
            barrier.wait(timeout=10)
            assert store.get_market_candidate(pinned.scenario_id,pinned.revision)
        assert conn.closed and store._scoped_reader.get() is None
        return pid
    with ThreadPoolExecutor(max_workers=2) as pool:pids=list(pool.map(read,range(2)))
    assert len(set(pids))==2 and store._scoped_reader.get() is None


def test_closed_candidate_connection_is_not_reused(candidate):
    _,store,_,pinned=candidate
    with pytest.raises(MarketCandidateDenied):
        with store.read_scope('tenant-1'):
            with store._read_context('tenant-1') as conn:conn.close()
            store.get_market_candidate(pinned.scenario_id,pinned.revision)
    assert store._scoped_reader.get() is None
