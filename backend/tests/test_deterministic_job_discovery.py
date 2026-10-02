"""Discovery bounds; real SCRAM acceptance is separate from isolated checks."""

from contextlib import contextmanager
from concurrent.futures import ThreadPoolExecutor
from dataclasses import FrozenInstanceError
from datetime import datetime, timedelta, timezone
from hashlib import sha256
from pathlib import Path
import sys
from uuid import uuid4

from psycopg import sql
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from app.deterministic_job_discovery import (
    DeterministicJobDiscovery, DiscoveryCursor, DiscoveryHold,
)
from app.job_store import JobStore
from app.jobs import canonical_input_bytes
from app.runtime_roles import RuntimeLoginPolicy
from login_database import login_database, login_scope
from test_economic_calculation_worker import calculation_setup, economic_api, PROFILE

VERSION = 'break-even-calculation-input-v1'
NOW = datetime(2026, 10, 2, tzinfo=timezone.utc)


@pytest.fixture
def isolated_jobs(tmp_path):
    principal = {'authenticated': True, 'tenant_id': 'tenant-a',
                 'scopes': {'metadata', 'simulation_execute'}}
    policy = RuntimeLoginPolicy('test_jobs', 'test_owner', 'test_runtime', 'postgres')
    jobs = JobStore('dbname=postgres', policy.schema, tmp_path / 'unused',
                    runtime_identity=(policy, 'authority'), audit_runtime_grants=True,
                    principal_provider=lambda: principal)
    return jobs, principal


def row(version, *, raw=None):
    raw = canonical_input_bytes({'input_version': version}) if raw is None else raw
    return {'job_id': uuid4(), 'created_at': NOW, 'input_bytes': raw,
            'input_sha256': sha256(raw).hexdigest()}


def isolated_page(monkeypatch, jobs, rows, *, after_read=None, audit=None):
    """Only replace I/O boundaries; never count this as authentication proof."""
    class Connection:
        def execute(self, query, params=None):
            if params is not None:
                if after_read is not None:
                    after_read()
                return self
        def fetchall(self):
            return rows
    @contextmanager
    def connect():
        yield Connection()
    monkeypatch.setattr(jobs, 'connect', connect)
    monkeypatch.setattr('app.deterministic_job_discovery.audit_runtime_roles',
                        audit or (lambda *_: None))


def test_unrelated_full_page_advances_without_exposing_input(monkeypatch, isolated_jobs):
    jobs, _ = isolated_jobs
    older = [row('thermal-simulation-input-v1'), row('future-input-v1')]
    isolated_page(monkeypatch, jobs, older)
    discovery = DeterministicJobDiscovery(jobs, tenant_id='tenant-a', input_versions=frozenset({VERSION}))
    page = discovery.page(limit=2)
    assert page.jobs == () and page.scanned_count == 2
    assert page.next_cursor == DiscoveryCursor(NOW, str(older[-1]['job_id']))
    assert 'input_bytes' not in repr(page) and 'sha256' not in repr(page)
    with pytest.raises(FrozenInstanceError):
        page.scanned_count = 0


def test_selected_version_only_and_short_page_ends_pass(monkeypatch, isolated_jobs):
    jobs, _ = isolated_jobs
    selected = row(VERSION)
    isolated_page(monkeypatch, jobs, [row('unrelated-v1'), selected])
    page = DeterministicJobDiscovery(jobs, tenant_id='tenant-a', input_versions=frozenset({VERSION})).page()
    assert [(job.job_id, job.input_version) for job in page.jobs] == [(str(selected['job_id']), VERSION)]
    assert page.scanned_count == 2 and page.next_cursor is None
    with pytest.raises(FrozenInstanceError):
        page.jobs[0].job_id = str(uuid4())


@pytest.mark.parametrize('limit', [True, False, 0, 51, 1.0, '25', None])
def test_invalid_limits_never_open_connection(monkeypatch, isolated_jobs, limit):
    jobs, _ = isolated_jobs
    monkeypatch.setattr(jobs, 'connect', lambda: pytest.fail('invalid request connected'))
    discovery = DeterministicJobDiscovery(jobs, tenant_id='tenant-a', input_versions=frozenset({VERSION}))
    with pytest.raises(DiscoveryHold, match='^discovery_page_rejected$'):
        discovery.page(limit=limit)


@pytest.mark.parametrize('versions', [set([VERSION]), (VERSION,), frozenset(),
                                    frozenset({'unknown-v1'}), frozenset({1})])
def test_version_selection_is_explicit_and_immutable(isolated_jobs, versions):
    jobs, _ = isolated_jobs
    with pytest.raises(DiscoveryHold, match='^discovery_binding_rejected$'):
        DeterministicJobDiscovery(jobs, tenant_id='tenant-a', input_versions=versions)


@pytest.mark.parametrize('fault', ['login', 'audit', 'provider', 'tenant'])
def test_construction_requires_audited_authority_and_fixed_tenant(isolated_jobs, fault):
    jobs, _ = isolated_jobs
    tenant = 'tenant-a'
    if fault == 'login': jobs.runtime_identity = (jobs.runtime_identity[0], 'request')
    elif fault == 'audit': jobs.audit_runtime_grants = False
    elif fault == 'provider': jobs.principal_provider = None
    elif fault == 'tenant': tenant = ''
    with pytest.raises(DiscoveryHold, match='^discovery_binding_rejected$'):
        DeterministicJobDiscovery(jobs, tenant_id=tenant, input_versions=frozenset({VERSION}))


def test_cursor_is_typed_and_empty_page_ends_pass(monkeypatch, isolated_jobs):
    jobs, _ = isolated_jobs
    isolated_page(monkeypatch, jobs, [])
    discovery = DeterministicJobDiscovery(jobs, tenant_id='tenant-a', input_versions=frozenset({VERSION}))
    with pytest.raises(DiscoveryHold, match='^discovery_page_rejected$'):
        discovery.page(cursor={'created_at': NOW, 'job_id': str(uuid4())})
    page = discovery.page()
    assert page.jobs == () and page.scanned_count == 0 and page.next_cursor is None


@pytest.mark.parametrize('created_at,job_id', [
    (NOW.replace(tzinfo=None), str(uuid4())),
    (NOW.astimezone(timezone(timedelta(hours=9))), str(uuid4())),
    ('2026-10-02', str(uuid4())), (NOW, uuid4()), (NOW, 'not-a-uuid'),
    (NOW, str(uuid4()).upper()),
])
def test_cursor_requires_utc_and_canonical_uuid(created_at, job_id):
    with pytest.raises(DiscoveryHold, match='^discovery_page_rejected$'):
        DiscoveryCursor(created_at, job_id)


@pytest.mark.parametrize('fault', ['hash', 'noncanonical', 'array', 'oversize', 'secret'])
def test_invalid_immutable_input_rejects_entire_page(monkeypatch, isolated_jobs, fault):
    jobs, _ = isolated_jobs
    invalid = row(VERSION)
    raw = {'noncanonical': b'{ "input_version": "unknown-v1" }',
           'array': b'[]', 'oversize': b'"' + b'x' * 65536 + b'"',
           'secret': b'{"password":"private-test-marker"}'}
    if fault == 'hash':
        invalid['input_sha256'] = '0' * 64
    else:
        invalid = row('unused', raw=raw[fault])
    isolated_page(monkeypatch, jobs, [row(VERSION), invalid])
    with pytest.raises(DiscoveryHold, match='^discovery_input_rejected$') as error:
        DeterministicJobDiscovery(jobs, tenant_id='tenant-a', input_versions=frozenset({VERSION})).page()
    assert 'private-test-marker' not in str(error.value)


@pytest.mark.parametrize('fault', ['scope', 'tenant', 'provider', 'dsn', 'schema', 'login', 'audit'])
def test_current_access_and_binding_drift_expose_no_partial_records(monkeypatch, isolated_jobs, fault):
    jobs, principal = isolated_jobs
    discovery = DeterministicJobDiscovery(jobs, tenant_id='tenant-a', input_versions=frozenset({VERSION}))
    def drift():
        if fault == 'scope': principal['scopes'].remove('simulation_execute')
        elif fault == 'tenant': principal['tenant_id'] = 'tenant-b'
        elif fault == 'provider': jobs.principal_provider = lambda: principal
        elif fault == 'dsn': jobs._dsn = 'dbname=changed'
        elif fault == 'schema': jobs.schema = 'changed_schema'
        elif fault == 'login': jobs.runtime_identity = (jobs.runtime_identity[0], 'worker')
        elif fault == 'audit': jobs.audit_runtime_grants = False
    isolated_page(monkeypatch, jobs, [row(VERSION)], after_read=drift)
    with pytest.raises(DiscoveryHold):
        discovery.page()


def test_scope_missing_before_read_never_connects(monkeypatch, isolated_jobs):
    jobs, principal = isolated_jobs
    principal['scopes'].remove('metadata')
    monkeypatch.setattr(jobs, 'connect', lambda: pytest.fail('unauthorized connection'))
    with pytest.raises(DiscoveryHold, match='^discovery_access_rejected$'):
        DeterministicJobDiscovery(jobs, tenant_id='tenant-a', input_versions=frozenset({VERSION})).page()


def test_post_read_audit_errors_have_fixed_public_reason(monkeypatch, isolated_jobs):
    jobs, _ = isolated_jobs
    def audit(*_):
        raise ValueError('private-test-marker')
    isolated_page(monkeypatch, jobs, [row(VERSION)], audit=audit)
    with pytest.raises(DiscoveryHold, match='^discovery_read_rejected$') as error:
        DeterministicJobDiscovery(jobs, tenant_id='tenant-a', input_versions=frozenset({VERSION})).page()
    assert 'private-test-marker' not in str(error.value)


def test_binding_drift_from_final_principal_call_is_rejected(monkeypatch, isolated_jobs):
    jobs, principal = isolated_jobs
    calls = 0
    def provider():
        nonlocal calls
        calls += 1
        if calls == 2:
            jobs._dsn = 'dbname=changed'
        return principal
    jobs.principal_provider = provider
    isolated_page(monkeypatch, jobs, [row(VERSION)])
    with pytest.raises(DiscoveryHold, match='^discovery_binding_rejected$'):
        DeterministicJobDiscovery(jobs, tenant_id='tenant-a', input_versions=frozenset({VERSION})).page()


def test_database_timestamp_is_normalized_to_utc(monkeypatch, isolated_jobs):
    jobs, _ = isolated_jobs
    selected = row(VERSION)
    selected['created_at'] = NOW.astimezone(timezone(timedelta(hours=9)))
    isolated_page(monkeypatch, jobs, [selected])
    page = DeterministicJobDiscovery(jobs, tenant_id='tenant-a', input_versions=frozenset({VERSION})).page(limit=1)
    assert page.next_cursor == DiscoveryCursor(NOW, str(selected['job_id']))


def test_final_grant_audit_follows_principal_refresh(monkeypatch, isolated_jobs):
    jobs, principal = isolated_jobs
    calls = 0
    grants_changed = False
    def provider():
        nonlocal calls, grants_changed
        calls += 1
        grants_changed = calls == 2
        return principal
    def audit(*_):
        if grants_changed:
            raise ValueError('changed grant')
    jobs.principal_provider = provider
    isolated_page(monkeypatch, jobs, [row(VERSION)], audit=audit)
    with pytest.raises(DiscoveryHold, match='^discovery_read_rejected$'):
        DeterministicJobDiscovery(jobs, tenant_id='tenant-a', input_versions=frozenset({VERSION})).page()


@pytest.fixture
def scram_discovery(login_scope):
    base, policy, dsns = login_scope
    principal = {'authenticated': True, 'tenant_id': 'tenant-a',
                 'scopes': {'metadata', 'simulation_execute'}}
    jobs = JobStore(dsns['authority'], policy.schema, base.artifact_root,
                    runtime_identity=(policy, 'authority'), audit_runtime_grants=True,
                    principal_provider=lambda: principal)
    with jobs.connect() as conn:
        assert conn.pgconn.used_password and conn.info.user == policy.roles['authority']
    discovery = DeterministicJobDiscovery(jobs, tenant_id='tenant-a', input_versions=frozenset({VERSION}))
    return base, jobs, principal, discovery


def queue(base, version=VERSION, *, tenant='tenant-a', stage='simulation', max_attempts=3):
    return base.submit(tenant, stage, {'input_version': version}, uuid4().hex, max_attempts=max_attempts)


def persisted_digest(base):
    with base.connect() as conn:
        records = [conn.execute(sql.SQL('SELECT * FROM {} ORDER BY tenant_id, job_id')
                    .format(base._table(table))).fetchall()
                   for table in ('jobs', 'job_events', 'job_attempts', 'attempt_outcomes', 'job_publications')]
    return sha256(repr([sorted(map(repr, rows)) for rows in records]).encode()).hexdigest()


def discovered_pass(discovery):
    cursor, matches = None, []
    for _ in range(10):
        page = discovery.page(cursor=cursor)
        matches.extend(page.jobs)
        if page.next_cursor is None:
            return tuple(matches)
        cursor = page.next_cursor
    pytest.fail('fixture unexpectedly exceeded 250 scanned rows')


def test_scram_mixed_queue_pagination_is_read_only(scram_discovery):
    base, jobs, _, discovery = scram_discovery
    for _ in range(3):
        queue(base, 'thermal-simulation-input-v1')
    selected = [queue(base), queue(base)]
    queue(base, tenant='tenant-b')
    queue(base, stage='collection')
    future = queue(base)
    live = queue(base)
    terminal = queue(base)
    assert base.cancel('tenant-a', terminal['job_id'])
    lease = jobs.claim(60, tenant_id='tenant-a', allowed_stages=('simulation',), job_id=str(live['job_id']))
    assert lease is not None
    with base.connect() as conn:
        conn.execute(sql.SQL("UPDATE {} SET next_attempt_at=clock_timestamp()+interval '2 hours' WHERE job_id=%s")
                     .format(base._table('jobs')), (future['job_id'],))
    before = persisted_digest(base)
    first = discovery.page(limit=2)
    second = discovery.page(cursor=first.next_cursor, limit=2)
    third = discovery.page(cursor=second.next_cursor, limit=2)
    assert first.jobs == () and first.scanned_count == 2 and first.next_cursor is not None
    assert [job.job_id for job in second.jobs + third.jobs] == [str(job['job_id']) for job in selected]
    assert second.scanned_count == 2 and third.scanned_count == 1 and third.next_cursor is None
    assert persisted_digest(base) == before
    with base.connect() as conn:
        conn.execute(sql.SQL("UPDATE {} SET next_attempt_at=clock_timestamp()-interval '1 second' WHERE job_id=%s")
                     .format(base._table('jobs')), (future['job_id'],))
    assert str(future['job_id']) in {job.job_id for job in discovery.page().jobs}


def test_scram_current_scope_binding_and_grant_drift_are_closed(scram_discovery):
    base, jobs, principal, discovery = scram_discovery
    queue(base)
    assert len(discovery.page().jobs) == 1
    principal['scopes'].remove('metadata')
    with pytest.raises(DiscoveryHold, match='^discovery_access_rejected$'): discovery.page()
    principal['scopes'].add('metadata')
    principal['tenant_id'] = 'tenant-b'
    with pytest.raises(DiscoveryHold, match='^discovery_access_rejected$'): discovery.page()
    principal['tenant_id'] = 'tenant-a'
    provider = jobs.principal_provider
    jobs.principal_provider = lambda: principal
    with pytest.raises(DiscoveryHold, match='^discovery_binding_rejected$'): discovery.page()
    jobs.principal_provider = provider
    policy, kind = jobs.runtime_identity
    jobs.runtime_identity = (policy, 'worker')
    with pytest.raises(DiscoveryHold, match='^discovery_binding_rejected$'): discovery.page()
    jobs.runtime_identity = (policy, kind)
    calls = 0
    def changing_provider():
        nonlocal calls
        calls += 1
        if calls == 2:
            with base.connect() as conn:
                conn.execute(sql.SQL('GRANT SELECT ON {} TO {}').format(
                    base._table('jobs'), sql.Identifier(policy.roles['worker'])))
        return principal
    jobs.principal_provider = changing_provider
    discovery = DeterministicJobDiscovery(jobs, tenant_id='tenant-a', input_versions=frozenset({VERSION}))
    with pytest.raises(DiscoveryHold, match='^discovery_read_rejected$'):
        discovery.page()
    with pytest.raises(DiscoveryHold, match='^discovery_read_rejected$'):
        discovery.page()


@pytest.mark.parametrize('fault', ['hash', 'canonical'])
def test_scram_persisted_corruption_rejects_page(scram_discovery, fault):
    base, _, _, discovery = scram_discovery
    queue(base)
    raw = canonical_input_bytes({'input_version': VERSION}) if fault == 'hash' else b'{ "input_version": "unknown-v1" }'
    with base.connect() as conn:
        if fault == 'hash':
            constraints = conn.execute("""SELECT conname FROM pg_constraint
                WHERE conrelid=%s::regclass AND pg_get_constraintdef(oid) LIKE '%%sha256(input_bytes)%%'""",
                (f'{base.schema}.jobs',)).fetchall()
            assert len(constraints) == 1
            # Administrator fault injection is limited to this disposable test schema.
            conn.execute(sql.SQL('ALTER TABLE {} DROP CONSTRAINT {}').format(
                base._table('jobs'), sql.Identifier(constraints[0]['conname'])))
        conn.execute(sql.SQL("""INSERT INTO {} (tenant_id, job_id, stage, input_bytes,
            input_sha256, idempotency_key, state, max_attempts)
            VALUES ('tenant-a', %s, 'simulation', %s, %s, %s, 'queued', 3)""").format(base._table('jobs')),
            (uuid4(), raw, '0' * 64 if fault == 'hash' else sha256(raw).hexdigest(), uuid4().hex))
    before = persisted_digest(base)
    with pytest.raises(DiscoveryHold, match='^discovery_input_rejected$'):
        discovery.page()
    assert persisted_digest(base) == before


@pytest.mark.parametrize('login_scope', [PROFILE], indirect=True)
def test_scram_discovery_delegates_recovery_and_competing_worker_publication(calculation_setup):
    worker, jobs, results, initial, data, _ = calculation_setup
    version = 'economic-calculation-input-v1'
    discovery = DeterministicJobDiscovery(jobs, tenant_id='tenant-1', input_versions=frozenset({version}))
    first, second = discovered_pass(discovery), discovered_pass(discovery)
    target = str(initial['job_id'])
    assert [job.job_id for job in first] == [target] == [job.job_id for job in second]
    with ThreadPoolExecutor(max_workers=2) as pool:
        outcomes = list(pool.map(worker.run_once, [target, target]))
    completed = [value for value in outcomes if value is not None]
    assert len(completed) == 1 and completed[0].state == 'succeeded'
    assert jobs.get_publication('tenant-1', initial['job_id']) is not None
    assert len(jobs.list_attempt_outcomes('tenant-1', initial['job_id'])) == 1
    assert discovered_pass(discovery) == ()
    with results.connect() as conn:
        assert conn.execute(sql.SQL('SELECT count(*) AS n FROM {}')
                            .format(results._table('market_result_records'))).fetchone()['n'] == 1
    for canceled in (True, False):
        pending = jobs.submit('tenant-1', 'simulation', data, uuid4().hex, max_attempts=1)
        target = str(pending['job_id'])
        lease = jobs.claim(60, tenant_id='tenant-1', allowed_stages=('simulation',), job_id=target)
        assert lease is not None and discovered_pass(discovery) == ()
        if canceled: assert jobs.cancel('tenant-1', pending['job_id'])
        with jobs.connect() as conn:
            conn.execute(sql.SQL("UPDATE {} SET lease_until=clock_timestamp()-interval '1 second' WHERE job_id=%s")
                         .format(jobs._table('jobs')), (pending['job_id'],))
        before = persisted_digest(jobs)
        assert [job.job_id for job in discovered_pass(discovery)] == [target]
        assert persisted_digest(jobs) == before
        assert worker.run_once(target) is None
        closed = jobs.get_job('tenant-1', pending['job_id'])
        assert closed['state'] == ('canceled' if canceled else 'failed') and closed['attempt_count'] == 1
        assert closed['reason']['code'] == ('cancel_lease_expired' if canceled else 'attempts_exhausted')
        assert len(jobs.list_attempt_outcomes('tenant-1', pending['job_id'])) == 1
        assert jobs.get_publication('tenant-1', pending['job_id']) is None and discovered_pass(discovery) == ()
