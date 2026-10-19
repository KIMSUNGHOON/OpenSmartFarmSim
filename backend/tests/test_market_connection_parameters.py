"""Current shared-reader parameters are checked once per call, with no retained value."""
import psycopg
import pytest

from app.market_candidate_store import MarketCandidateDenied
from app.runtime_roles import RolePolicyHold
from test_market_shared_read_scope import (
    shared, economic_api, login_database, login_scope, audit_cleanup, pytestmark)


def test_each_validation_reads_fresh_parameters_and_still_checks_scram(shared, monkeypatch):
    _, store, _, _ = shared
    source = store._source._source
    original = psycopg.ConnectionInfo.get_parameters
    observed, active = [], [False, False]

    def parameters(info):
        values = original(info)
        if active[0]:
            observed.append(1)
            if active[1]:
                values['host'] = 'wrong-fixture-host'
        return values

    monkeypatch.setattr(psycopg.ConnectionInfo, 'get_parameters', parameters)
    with source.read_scope('tenant-1'):
        conn = source._scoped_reader.get()[0]
        active[0] = True
        try:
            first = store._shared_reader('tenant-1', conn)
            # Binding fields and SCRAM each inspect the current connection.
            assert first is not None and len(observed) == 2
            assert store._shared_reader('tenant-1', conn) == first
            assert len(observed) == 4
            active[1] = True
            with pytest.raises(MarketCandidateDenied):
                store._shared_reader('tenant-1', conn)
        finally:
            active[0] = False
    assert conn.closed and source._scoped_reader.get() is store._scoped_reader.get() is None


@pytest.mark.parametrize('field', ['host', 'hostaddr', 'port', 'dbname', 'user', 'require_auth'])
def test_every_configured_field_and_authentication_mismatch_is_denied(shared, monkeypatch, field):
    _, store, _, _ = shared
    source = store._source._source
    if field == 'hostaddr':
        for owner in (store, source):
            monkeypatch.setattr(owner, 'dsn', owner.dsn + ' hostaddr=127.0.0.1')
    original = psycopg.ConnectionInfo.get_parameters
    active, calls = [False], []

    def parameters(info):
        values = original(info)
        if active[0]:
            calls.append(1)
            assert field in values
            values[field] = 'wrong-fixture-value'
        return values

    monkeypatch.setattr(psycopg.ConnectionInfo, 'get_parameters', parameters)
    with source.read_scope('tenant-1'):
        conn = source._scoped_reader.get()[0]
        assert store._shared_reader('tenant-1', conn) is not None
        active[0] = True
        try:
            with pytest.raises((MarketCandidateDenied, RolePolicyHold)):
                store._shared_reader('tenant-1', conn)
        finally:
            active[0] = False
    assert calls and conn.closed and source._scoped_reader.get() is store._scoped_reader.get() is None


@pytest.mark.parametrize('fault', ['missing_host', 'exception'])
def test_missing_parameters_or_observation_failure_cannot_authorize(shared, monkeypatch, fault):
    _, store, _, _ = shared
    source = store._source._source
    original = psycopg.ConnectionInfo.get_parameters
    active = [False]

    def parameters(info):
        values = original(info)
        if active[0]:
            if fault == 'exception':
                raise psycopg.InterfaceError('fixture parameter observation unavailable')
            del values['host']
        return values

    monkeypatch.setattr(psycopg.ConnectionInfo, 'get_parameters', parameters)
    with source.read_scope('tenant-1'):
        conn = source._scoped_reader.get()[0]
        active[0] = True
        try:
            with pytest.raises((MarketCandidateDenied, psycopg.InterfaceError)):
                store._shared_reader('tenant-1', conn)
        finally:
            active[0] = False
    assert conn.closed and source._scoped_reader.get() is store._scoped_reader.get() is None
