"""Real current-source reads with request-local deterministic reconstruction."""
from hashlib import sha256
from contextvars import copy_context
from concurrent.futures import ThreadPoolExecutor
from decimal import localcontext

import pytest
import psycopg
from psycopg import sql

from app.farm_authoring_storage import FarmAuthoringHold, FarmAuthoringRequest
from app.economics import EconomicLedger
from app.market_source_store import MarketSourceStore
from app.thermal_run_store import _canonical
from test_crop_greenhouse_solar_execution_query import (
    authoring, profiles, login_database,
    original_login_scope, login_scope, query_cleanup)
import test_crop_greenhouse_solar_execution_query as reference

pytestmark = [reference.reference.pytestmark, pytest.mark.usefixtures('query_cleanup')]


@pytest.fixture
def registration(authoring):
    farms, body, principal = authoring
    registered = farms.submit('tenant-1', FarmAuthoringRequest.model_validate_json(_canonical(body)))
    return farms, ('tenant-1', registered.scenario_id, registered.scenario_revision,
                   registered.scenario_sha256), principal


def test_scoped_reads_reconstruct_once_but_repeat_all_actual_source_reads(registration, monkeypatch):
    farms, args, _ = registration
    expected = farms.read_registration(*args)
    prepare, calculate, source_read = farms._prepare, EconomicLedger.calculate, MarketSourceStore._read_in_transaction
    calls = {'prepare': 0, 'calculate': 0, 'source': []}
    def preparing(*a, **kw):
        calls['prepare'] += 1; return prepare(*a, **kw)
    def calculating(*a, **kw):
        calls['calculate'] += 1; return calculate(*a, **kw)
    def reading(self, conn, tenant, kind, identity, revision, **kw):
        calls['source'].append((tenant, kind, identity, revision, kw.get('pin', False)))
        return source_read(self, conn, tenant, kind, identity, revision, **kw)
    monkeypatch.setattr(farms, '_prepare', preparing)
    monkeypatch.setattr(EconomicLedger, 'calculate', calculating)
    monkeypatch.setattr(MarketSourceStore, '_read_in_transaction', reading)
    execute = psycopg.Connection.execute
    def readonly(conn, statement, *a, **kw):
        text = statement.as_string(conn) if hasattr(statement, 'as_string') else statement
        assert text.split(None, 1)[0].upper() not in {
            'INSERT', 'UPDATE', 'DELETE', 'TRUNCATE', 'CREATE', 'ALTER', 'DROP', 'GRANT', 'REVOKE'}
        return execute(conn, statement, *a, **kw)
    monkeypatch.setattr(psycopg.Connection, 'execute', readonly)
    with farms.registration_read_scope(*args):
        first = farms.read_registration(*args)
        trace = list(calls['source']); assert trace
        first['binding'].clear()
        second = farms.read_registration(*args)
        assert second == expected and calls['source'] == trace + trace
        assert calls['prepare'] == calls['calculate'] == 1
    with farms.registration_read_scope(*args):
        assert farms.read_registration(*args) == expected
    assert calls['prepare'] == calls['calculate'] == 2
    assert farms.read_registration(*args) == expected and calls['prepare'] == 3


@pytest.mark.parametrize('change', ['scope', 'input', 'grant', 'research', 'snapshot'])
def test_current_mutable_authority_is_not_reused(registration, login_scope, change):
    farms, args, principal = registration
    base, policy, _ = login_scope
    with farms.registration_read_scope(*args):
        first = farms.read_registration(*args)
        if change == 'scope':
            principal['scopes'].remove('market_source_read')
        else:
            with base.connect() as conn:
                if change == 'grant':
                    conn.execute(sql.SQL('GRANT UPDATE ON {} TO {}').format(
                        sql.Identifier(policy.schema, 'market_source_records'),
                        sql.Identifier(policy.roles['authority'])))
                else:
                    table = {'input': 'market_source_records', 'research': 'jobs',
                             'snapshot': 'thermal_input_snapshots'}[change]
                    target = sql.Identifier(policy.schema, table)
                    conn.execute(sql.SQL('ALTER TABLE {} DISABLE TRIGGER USER').format(target))
                    raw = b'{}'; digest = sha256(raw).hexdigest()
                    if change == 'input':
                        conn.execute(sql.SQL("UPDATE {} SET payload_raw=%s,payload_sha256=%s "
                            "WHERE tenant_id=%s AND kind='input_rights'").format(target), (raw, digest, args[0]))
                    elif change == 'research':
                        conn.execute(sql.SQL('UPDATE {} SET input_bytes=%s,input_sha256=%s '
                            'WHERE tenant_id=%s AND job_id=%s').format(target),
                            (raw, digest, args[0], first['farm'].research_job_id))
                    else:
                        conn.execute(sql.SQL('UPDATE {} SET weather_raw=%s,weather_sha256=%s '
                            'WHERE tenant_id=%s AND snapshot_id=%s').format(target),
                            (raw, digest, args[0], first['farm'].snapshot_id))
        with pytest.raises((FarmAuthoringHold, PermissionError)):
            farms.read_registration(*args)


def test_scope_closes_on_error_and_retained_witness_cannot_authorize(registration):
    farms, args, _ = registration
    with pytest.raises(RuntimeError, match='fixture interruption'):
        with farms.registration_read_scope(*args):
            expected = farms.read_registration(*args)
            retained = farms._registration_read.get()
            raise RuntimeError('fixture interruption')
    assert farms._registration_read.get() is None
    with pytest.raises(ValueError): retained.read(*args)
    with farms.registration_read_scope(*args):
        assert farms.read_registration(*args) == expected


def test_wrong_identity_and_nested_scope_cannot_reuse_registration(registration):
    farms, args, _ = registration
    for index in range(4):
        with farms.registration_read_scope(*args):
            farms.read_registration(*args)
            with pytest.raises(FarmAuthoringHold):
                with farms.registration_read_scope(*args):
                    pytest.fail('nested scope was entered')
            wrong = list(args); wrong[index] = '0' * 64 if index == 3 else 'foreign-version'
            with pytest.raises(FarmAuthoringHold): farms.read_registration(*wrong)


def test_copied_context_cannot_cross_execution_owner(registration):
    farms, args, _ = registration
    with farms.registration_read_scope(*args):
        farms.read_registration(*args)
        context = copy_context()
        with ThreadPoolExecutor(max_workers=1) as pool:
            future = pool.submit(context.run, farms.read_registration, *args)
            with pytest.raises(FarmAuthoringHold): future.result(timeout=10)


def test_late_source_scope_revocation_is_checked_before_return(registration, monkeypatch):
    farms, args, principal = registration
    original = MarketSourceStore._read_in_transaction
    active = [False]
    def reading(self, *a, **kw):
        result = original(self, *a, **kw)
        if active[0]:
            principal['scopes'].discard('market_source_read')
        return result
    monkeypatch.setattr(MarketSourceStore, '_read_in_transaction', reading)
    with farms.registration_read_scope(*args):
        farms.read_registration(*args)
        active[0] = True
        with pytest.raises((FarmAuthoringHold, PermissionError)):
            farms.read_registration(*args)


@pytest.mark.parametrize('change', ['source_pointer', 'numeric_code'])
def test_changed_authority_or_reconstruction_code_cannot_reuse(registration, monkeypatch, change):
    farms, args, _ = registration
    with farms.registration_read_scope(*args):
        farms.read_registration(*args)
        if change == 'source_pointer':
            holds = farms.replay.thermal.holds
            original = holds._scope_resolver
            monkeypatch.setattr(holds, '_scope_resolver', lambda *a: original(*a))
        else:
            def fail(*a, **kw): pytest.fail('changed numeric reconstruction was executed')
            monkeypatch.setattr(EconomicLedger, '_calculate_verified', fail)
        with pytest.raises((FarmAuthoringHold, PermissionError)):
            farms.read_registration(*args)


def test_changed_decimal_context_cannot_reuse_reconstruction(registration):
    farms, args, _ = registration
    with farms.registration_read_scope(*args):
        farms.read_registration(*args)
        with localcontext() as context:
            context.prec += 1
            with pytest.raises(FarmAuthoringHold): farms.read_registration(*args)
