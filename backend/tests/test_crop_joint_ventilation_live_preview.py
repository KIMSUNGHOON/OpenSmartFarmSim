"""Verify the owned preview's opt-in upgrade and rollback on a fresh database."""
from dataclasses import replace
import importlib.util
from pathlib import Path
import signal
import subprocess
import sys
from types import SimpleNamespace

import pytest
from psycopg import sql

from app.crop_greenhouse_ventilation_result_schema import TABLE
from app.runtime_roles import audit_runtime_roles
from test_crop_climate_joint_result_store import (
    login_database, login_scope, original_login_scope, pytestmark as database_marks,
)

spec = importlib.util.spec_from_file_location(
    'ventilation_live_preview', Path(__file__).resolve().parents[2]/'research/crop-joint-ventilation-live-preview.py')
preview = importlib.util.module_from_spec(spec)
spec.loader.exec_module(preview)


def relation(conn, policy):
    return conn.execute('SELECT to_regclass(%s) AS relation', (policy.schema+'.'+TABLE,)).fetchone()['relation']


@database_marks
def test_upgrade_and_rollback_preserve_existing_access(login_scope, login_database):
    base, previous, _ = login_scope
    enabled = replace(previous, crop_greenhouse_ventilation_result_storage=True)
    with base.connect() as conn:
        before = conn.execute(sql.SQL('SELECT count(*) AS n FROM {}').format(base._table('jobs'))).fetchone()['n']
        audit_runtime_roles(conn, previous)
    preview.provision(login_database['admin'], enabled)
    with base.connect() as conn:
        assert relation(conn, enabled) is not None
        audit_runtime_roles(conn, enabled)
        for privilege in ('SELECT', 'INSERT'):
            assert conn.execute('SELECT has_table_privilege(%s,%s,%s) AS allowed',
                (enabled.roles['authority'], enabled.schema+'.'+TABLE, privilege)).fetchone()['allowed']
        assert conn.execute(sql.SQL('SELECT count(*) AS n FROM {}').format(base._table('jobs'))).fetchone()['n'] == before
    preview.provision(login_database['admin'], previous, enabled=False)
    with base.connect() as conn:
        assert relation(conn, previous) is not None
        audit_runtime_roles(conn, previous)
        for privilege in ('SELECT', 'INSERT'):
            assert not conn.execute('SELECT has_table_privilege(%s,%s,%s) AS allowed',
                (previous.roles['authority'], previous.schema+'.'+TABLE, privilege)).fetchone()['allowed']
        oid = conn.execute('SELECT to_regclass(%s)::oid AS oid', (previous.schema+'.'+TABLE,)).fetchone()['oid']
    preview.provision(login_database['admin'], enabled)
    preview.provision(login_database['admin'], enabled)
    with base.connect() as conn:
        audit_runtime_roles(conn, enabled)
        assert conn.execute('SELECT to_regclass(%s)::oid AS oid', (enabled.schema+'.'+TABLE,)).fetchone()['oid'] == oid
        assert conn.execute("SELECT 1 FROM pg_namespace WHERE nspname LIKE 'ossf_preview_check_%'").fetchone() is None
        assert conn.execute(sql.SQL('SELECT count(*) AS n FROM {}').format(base._table('jobs'))).fetchone()['n'] == before


@database_marks
@pytest.mark.parametrize('change', ['column', 'trigger'])
def test_existing_schema_change_rejects_reenable_without_grants(login_scope, login_database, change):
    import psycopg
    base, previous, _ = login_scope
    enabled = replace(previous, crop_greenhouse_ventilation_result_storage=True)
    preview.provision(login_database['admin'], enabled)
    preview.provision(login_database['admin'], previous, enabled=False)
    with psycopg.connect(login_database['admin']) as conn:
        conn.execute(sql.SQL('ALTER TABLE {} ').format(sql.Identifier(previous.schema,TABLE)) +
            (sql.SQL('ADD COLUMN unexpected text') if change == 'column' else
             sql.SQL('DISABLE TRIGGER joint_ventilation_result_immutable')))
    with pytest.raises(ValueError, match='installed ventilation schema mismatch'):
        preview.provision(login_database['admin'], enabled)
    with base.connect() as conn:
        audit_runtime_roles(conn, previous)
        assert conn.execute("SELECT 1 FROM pg_namespace WHERE nspname LIKE 'ossf_preview_check_%'").fetchone() is None
        assert not conn.execute('SELECT has_table_privilege(%s,%s,%s) AS allowed',
            (previous.roles['authority'], previous.schema+'.'+TABLE, 'INSERT')).fetchone()['allowed']


@database_marks
def test_failed_audit_rolls_back_table_and_grants(login_scope, login_database, monkeypatch):
    base, previous, _ = login_scope
    enabled = replace(previous, crop_greenhouse_ventilation_result_storage=True)
    with base.connect() as conn:
        assert relation(conn, previous) is None
    def reject(*_):
        raise ValueError('injected activation audit rejection')
    with monkeypatch.context() as patch:
        patch.setattr('app.runtime_roles.audit_runtime_roles', reject)
        with pytest.raises(ValueError, match='injected activation audit rejection'):
            preview.provision(login_database['admin'], enabled)
    with base.connect() as conn:
        assert relation(conn, previous) is None
        audit_runtime_roles(conn, previous)


@database_marks
def test_policy_mismatch_cannot_install(login_scope, login_database):
    base, previous, _ = login_scope
    with pytest.raises(ValueError, match='storage policy mismatch'):
        preview.provision(login_database['admin'], previous)
    with base.connect() as conn:
        assert relation(conn, previous) is None
        audit_runtime_roles(conn, previous)


@pytest.mark.parametrize('ignore_term', [False, True])
def test_exact_owned_child_shutdown_escalates_and_reaps(ignore_term):
    source = ('import signal,time\n'
              + ('signal.signal(signal.SIGTERM,signal.SIG_IGN)\n' if ignore_term else '')
              + 'print("ready",flush=True)\ntime.sleep(30)\n')
    with subprocess.Popen([sys.executable, '-B', '-c', source], stdout=subprocess.PIPE, text=True) as child:
        try:
            assert child.stdout.readline() == 'ready\n'
            outcome = preview.stop_owned_process(child, timeout=.1)
            assert outcome == {'exit':-signal.SIGKILL if ignore_term else -signal.SIGTERM, 'forced':ignore_term}
            assert child.poll() is not None and not Path('/proc', str(child.pid)).exists()
        finally:
            if child.poll() is None: child.kill(); child.wait(timeout=5)


def test_child_cleanup_error_does_not_skip_other_services(monkeypatch):
    workers, nginx = [object(), object()], object()
    called = []
    def stop(child, *, timeout):
        called.append(child)
        if child is workers[0]: raise OSError('injected owned wait failure')
        return {'exit':0, 'forced':False}
    monkeypatch.setattr(preview, 'stop_owned_process', stop)
    server = SimpleNamespace(should_exit=False)
    joined, closed = [], []
    thread = SimpleNamespace(join=lambda timeout:joined.append(timeout), is_alive=lambda:False)
    logs = [SimpleNamespace(close=lambda:closed.append(True))]
    outcome = preview.stop_owned_services(workers, nginx, server, thread, logs)
    assert called == [*workers, nginx] and joined == [30] and closed == [True]
    assert server.should_exit and not outcome['service_stopped']
    assert outcome['errors'] == ['child_cleanup_failed']
