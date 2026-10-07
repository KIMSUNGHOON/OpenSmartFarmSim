"""Authentication audits use server rules even when its files are remote."""
from pathlib import Path
from unittest.mock import patch

import psycopg
import pytest

from login_database import assert_host_scram, login_database, login_scope


class RulesConnection:
    def __init__(self, rows): self.rows = rows
    def execute(self, query): return self
    def fetchall(self): return self.rows


def test_local_admin_trust_does_not_replace_host_scram():
    assert assert_host_scram(RulesConnection([
        ('local', 'trust', None), ('host', 'scram-sha-256', None),
        ('hostssl', 'scram-sha-256', None)])) == ['scram-sha-256', 'scram-sha-256']


@pytest.mark.parametrize('rows', [[], [('local', 'trust', None)],
    [('host', 'trust', None)], [('hostssl', 'md5', None)],
    [('host', 'scram-sha-256', None), (None, None, 'invalid rule')]])
def test_missing_non_scram_or_invalid_rules_cannot_pass(rows):
    with pytest.raises(AssertionError): assert_host_scram(RulesConnection(rows))


@pytest.fixture(scope='module')
def runtime_teardown_audits(login_database, tmp_path_factory):
    yield
    from test_calculation_operator_config import audit_database as loader_audit
    from test_crop_cycle_calculation_runtime import audit_database as runtime_audit
    from test_api_crop_cycle_calculation_tls import audit_cleanup as tls_audit
    with patch.object(Path, 'read_text', side_effect=AssertionError('host config file read')):
        for audit in (loader_audit, runtime_audit, tls_audit):
            cleanup = audit.__wrapped__(login_database, tmp_path_factory)
            next(cleanup)
            with pytest.raises(StopIteration): next(cleanup)


def test_actual_scram_and_server_audit_need_no_host_config_file(
        login_database, login_scope, monkeypatch, runtime_teardown_audits):
    _, _, dsns = login_scope
    with psycopg.connect(dsns['authority'], require_auth='scram-sha-256') as conn:
        assert conn.pgconn.used_password
    with psycopg.connect(login_database['admin']) as conn:
        with monkeypatch.context() as no_host_file:
            no_host_file.setattr(Path, 'read_text', lambda *a, **k: pytest.fail('host config file read'))
            assert set(assert_host_scram(conn)) == {'scram-sha-256'}
