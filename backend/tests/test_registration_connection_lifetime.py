"""Actual SCRAM registration reads retain transaction and authority boundaries."""
import asyncio
from contextvars import copy_context

import psycopg
from psycopg import sql
from psycopg.rows import tuple_row
import pytest

from app import runtime_connection_scope as connections
from app.farm_authoring_storage import FarmAuthoringHold

from test_farm_registration_read_scope import registration
from test_crop_greenhouse_solar_execution_query import (
    authoring, profiles, login_database, original_login_scope, login_scope, query_cleanup)
import test_crop_greenhouse_solar_execution_query as reference


pytestmark = [reference.reference.pytestmark, pytest.mark.usefixtures('query_cleanup')]


def test_registration_reuses_physical_connection_and_closes_it(registration, monkeypatch):
    farms, args, _ = registration
    execute = psycopg.Connection.execute
    audited = set()

    def executing(conn, query, params=None, **kwargs):
        # Observe actual connections without substituting SQL results.
        audited.add(conn)
        return execute(conn, query, params, **kwargs)

    monkeypatch.setattr(psycopg.Connection, 'execute', executing)
    with farms.registration_read_scope(*args):
        first = farms.read_registration(*args)
        assert farms.read_registration(*args) == first
        assert len({conn.info.backend_pid for conn in audited if not conn.closed}) == 1
        assert len(audited) == 1
    assert audited and all(conn.closed for conn in audited)
    audited.clear()
    with farms.registration_read_scope(*args):
        assert farms.read_registration(*args) == first
        assert len(audited) == 1
        with farms.replay.jobs.connect() as direct:
            assert direct not in audited or len(audited) == 2
            assert len({conn.info.backend_pid for conn in audited if not conn.closed}) == 2
    assert all(conn.closed for conn in audited)


def test_closed_frame_cannot_be_reused_or_retain_authority(registration):
    farms, args, _ = registration
    with farms.registration_read_scope(*args):
        farms.read_registration(*args)
        frame = connections._CURRENT.get()
        conn = frame.conn
    assert conn.closed and frame.conn is frame.owner is frame.witness is frame.profile is None
    with pytest.raises(connections.ConnectionScopeHold):
        frame.check()


@pytest.mark.parametrize('change', ['timeout', 'search_path', 'role', 'timezone', 'datestyle', 'row_factory',
                                   'adapter', 'transaction', 'autocommit', 'read_only'])
def test_changed_session_or_client_cannot_be_reused(registration, change):
    farms, args, _ = registration
    with farms.registration_read_scope(*args):
        farms.read_registration(*args)
        conn = connections._CURRENT.get().conn
        if change in ('timeout', 'search_path', 'role', 'timezone', 'datestyle'):
            statement = {'timeout': 'SET statement_timeout=0',
                'search_path': 'SET search_path=pg_catalog',
                'timezone': sql.SQL('SET TIMEZONE={}').format(sql.Literal(
                    'UTC' if connections._CURRENT.get().session['timezone'] not in ('UTC', 'Etc/UTC') else 'Asia/Seoul')),
                'datestyle': "SET DateStyle='ISO, DMY'",
                'role': sql.SQL('SET ROLE {}').format(sql.Identifier(conn.info.user))}[change]
            conn.execute(statement); conn.commit()
            if change == 'timezone':
                assert connections._session(conn)['timezone'] != connections._CURRENT.get().session['timezone']
                conn.commit()
        elif change == 'row_factory':
            conn.row_factory = tuple_row
        elif change == 'adapter':
            from psycopg.types.string import TextLoader
            class ChangedLoader(TextLoader):
                pass
            conn.adapters.register_loader(25, ChangedLoader)
        elif change == 'transaction':
            conn.execute('SELECT 1')
        elif change == 'autocommit':
            conn.autocommit = True
        else:
            conn.read_only = True
        with pytest.raises((FarmAuthoringHold, PermissionError)):
            farms.read_registration(*args)
    assert conn.closed and connections._CURRENT.get() is connections._REQUEST.get() is None


@pytest.mark.parametrize('change', ['revoke', 'nologin', 'membership'])
def test_prepared_audits_recheck_actual_live_role_changes(registration, login_scope, change):
    farms, args, _ = registration
    base, policy, _ = login_scope
    with farms.registration_read_scope(*args):
        for _ in range(3):
            farms.read_registration(*args)
        conn = connections._CURRENT.get().conn
        assert conn.execute('SELECT count(*) AS count FROM pg_prepared_statements').fetchone()['count'] > 0
        conn.commit()
        with base.connect() as admin:
            if change == 'revoke':
                admin.execute(sql.SQL('REVOKE SELECT ON {} FROM {}').format(
                    sql.Identifier(policy.schema, 'market_source_records'), sql.Identifier(policy.roles['authority'])))
            elif change == 'nologin':
                admin.execute(sql.SQL('ALTER ROLE {} NOLOGIN').format(sql.Identifier(policy.roles['authority'])))
            else:
                admin.execute(sql.SQL('GRANT {} TO {}').format(
                    sql.Identifier(policy.roles['request']), sql.Identifier(policy.roles['authority'])))
        with pytest.raises((FarmAuthoringHold, PermissionError)):
            farms.read_registration(*args)
    assert conn.closed


def test_busy_lease_is_separate_and_row_lock_ends_before_reuse(registration, login_scope):
    farms, args, _ = registration
    base, _, _ = login_scope
    jobs, runs = farms.replay.jobs, farms.replay.thermal.runs
    with farms.registration_read_scope(*args):
        value = farms.read_registration(*args)
        root = value['farm'].research_job_id
        statement = sql.SQL('SELECT job_id FROM {} WHERE tenant_id=%s AND job_id=%s FOR UPDATE NOWAIT').format(jobs._table('jobs'))
        with connections.read_connection(jobs) as first:
            assert jobs._locked_job(first, args[0], root) is not None
            with connections.read_connection(runs) as second:
                assert second is not first and second.info.backend_pid != first.info.backend_pid
            assert second.closed
            with pytest.raises(psycopg.errors.LockNotAvailable):
                with base.connect() as admin:
                    admin.execute(statement, (args[0], root)).fetchone()
        assert not first.closed
        with base.connect() as admin:
            assert admin.execute(statement, (args[0], root)).fetchone() is not None
        assert farms.read_registration(*args) == value
    assert first.closed


def test_body_failure_rolls_back_and_closes_owned_connection(registration):
    farms, args, _ = registration
    with pytest.raises(RuntimeError, match='lease interruption'):
        with farms.registration_read_scope(*args):
            farms.read_registration(*args)
            with connections.read_connection(farms.replay.jobs) as conn:
                conn.execute('SELECT 1')
                raise RuntimeError('lease interruption')
    assert conn.closed and connections._CURRENT.get() is connections._REQUEST.get() is None


def test_copied_same_thread_context_cannot_borrow_connection(registration):
    farms, args, _ = registration
    with farms.registration_read_scope(*args):
        farms.read_registration(*args)
        conn = connections._CURRENT.get().conn
        with pytest.raises(FarmAuthoringHold):
            copy_context().run(farms.read_registration, *args)
    assert conn.closed and connections._CURRENT.get() is None


def test_task_cancellation_closes_owned_connection(registration):
    farms, args, _ = registration
    retained = []
    async def cancel():
        with pytest.raises(asyncio.CancelledError):
            with farms.registration_read_scope(*args):
                farms.read_registration(*args)
                retained.append(connections._CURRENT.get().conn)
                raise asyncio.CancelledError()
        assert connections._CURRENT.get() is connections._REQUEST.get() is None
    asyncio.run(cancel())
    assert retained and all(conn.closed for conn in retained)


def test_initial_connect_wrapper_retains_original_path(registration, monkeypatch):
    farms, args, _ = registration
    source = farms.replay.candidates._source._source
    original = source.connect
    monkeypatch.setattr(source, 'connect', lambda: original())
    with farms.registration_read_scope(*args):
        assert connections._CURRENT.get() is None
        assert farms.read_registration(*args)['scenario_sha256'] == args[3]


@pytest.mark.parametrize('change', ['dsn', 'provider', 'policy'])
def test_changed_store_binding_cannot_borrow_existing_connection(registration, monkeypatch, change):
    from dataclasses import replace
    farms, args, _ = registration
    source = farms.replay.candidates._source._source
    with farms.registration_read_scope(*args):
        farms.read_registration(*args)
        conn = connections._CURRENT.get().conn
        if change == 'dsn':
            monkeypatch.setattr(source, 'dsn', source.dsn + ' application_name=changed')
        elif change == 'provider':
            provider = source._principal_provider
            monkeypatch.setattr(source, '_principal_provider', lambda: provider())
        else:
            monkeypatch.setattr(source, 'runtime_identity', (replace(source.runtime_identity[0]), 'authority'))
        with pytest.raises((FarmAuthoringHold, PermissionError)):
            farms.read_registration(*args)
    assert conn.closed


@pytest.mark.parametrize('change', ['guard', 'function_code'])
def test_changed_connection_code_cannot_be_used(registration, monkeypatch, change):
    farms, args, _ = registration
    with farms.registration_read_scope(*args):
        farms.read_registration(*args)
        conn = connections._CURRENT.get().conn
        if change == 'guard':
            monkeypatch.setattr(connections._Frame, 'check', lambda self: None)
        else:
            def changed(*args, **kwargs):
                pytest.fail('changed connection factory executed')
            monkeypatch.setattr(connections.factory_connection, '__code__', changed.__code__)
        with pytest.raises((FarmAuthoringHold, PermissionError)):
            farms.read_registration(*args)
    assert conn.closed


def test_child_task_cannot_borrow_parent_connection(registration):
    farms, args, _ = registration
    retained = []
    async def child():
        farms.read_registration(*args)
    async def parent():
        with farms.registration_read_scope(*args):
            farms.read_registration(*args)
            retained.append(connections._CURRENT.get().conn)
            with pytest.raises(FarmAuthoringHold):
                await asyncio.create_task(child())
        assert connections._CURRENT.get() is connections._REQUEST.get() is None
    asyncio.run(parent())
    assert retained and all(conn.closed for conn in retained)


def test_rollback_failure_preserves_cancellation_and_closes_connection(registration, monkeypatch):
    farms, args, _ = registration
    rollback = psycopg.Connection.rollback
    target = []
    def failing(conn):
        if target and conn is target[0]:
            raise RuntimeError('fixture rollback failure')
        return rollback(conn)
    monkeypatch.setattr(psycopg.Connection, 'rollback', failing)
    with pytest.raises(asyncio.CancelledError):
        with farms.registration_read_scope(*args):
            farms.read_registration(*args)
            with connections.read_connection(farms.replay.jobs) as conn:
                target.append(conn)
                conn.execute('SELECT 1')
                raise asyncio.CancelledError()
    assert target[0].closed and connections._CURRENT.get() is connections._REQUEST.get() is None


def test_commit_failure_closes_connection_without_a_successful_return(registration, monkeypatch):
    farms, args, _ = registration
    commit = psycopg.Connection.commit
    target = []
    def failing(conn):
        if target and conn is target[0]:
            raise RuntimeError('fixture commit failure')
        return commit(conn)
    monkeypatch.setattr(psycopg.Connection, 'commit', failing)
    with pytest.raises(RuntimeError, match='fixture commit failure'):
        with farms.registration_read_scope(*args):
            farms.read_registration(*args)
            with connections.read_connection(farms.replay.jobs) as conn:
                conn.execute('SELECT 1')
                target.append(conn)
    assert target[0].closed and connections._CURRENT.get() is connections._REQUEST.get() is None
