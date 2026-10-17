"""Bounded current privilege audits on actual owned PostgreSQL roles."""
import psycopg
from psycopg import sql
import pytest

from app import runtime_roles as model
from test_crop_greenhouse_solar_result_store import (
    login_database, original_login_scope, login_scope, pytestmark as selected_policy)

pytestmark = [selected_policy, pytest.mark.usefixtures('matrix_cleanup')]


@pytest.fixture(scope='module')
def matrix_cleanup(login_database):
    yield
    with psycopg.connect(login_database['admin']) as conn:
        assert conn.execute("SELECT count(*) FROM pg_namespace WHERE nspname LIKE 'login_test_%'").fetchone()[0] == 0
        assert conn.execute("SELECT count(*) FROM pg_roles WHERE rolname LIKE 'login_%'").fetchone()[0] == 0


def matrix_kind(query):
    if not isinstance(query, str) or 'has_table_privilege' not in query:
        return None
    return 'column' if 'has_any_column_privilege' in query else 'table'


@pytest.mark.parametrize('login_scope', [True, False], indirect=True)
def test_success_returns_no_privilege_matrix_rows(login_scope):
    base, policy, _ = login_scope
    observed = []

    class Observe:
        def __init__(self, conn): self.conn = conn
        def __getattr__(self, name): return getattr(self.conn, name)
        def execute(self, query, params=None):
            result = self.conn.execute(query, params)
            kind = matrix_kind(query)
            if kind: observed.append((kind, result.rowcount))
            return result

    with base.connect() as conn:
        result = model.audit_runtime_roles(Observe(conn), policy)
    assert result['roles'] == policy.roles and result['tables'] >= 26
    assert observed == [('table', 0), ('column', 0)]


@pytest.mark.parametrize('fault,reason', [
    ('missing_table', 'runtime_table_grant_matrix'),
    ('unexpected_update', 'runtime_table_grant_matrix'),
    ('table_grant_option', 'runtime_table_grant_matrix'),
    ('worker_column', 'runtime_column_grant_matrix'),
    ('column_grant_option', 'runtime_column_grant_matrix'),
    ('supervisor_read', 'runtime_table_grant_matrix'),
    ('extra_table', 'runtime_table_grant_matrix'),
])
def test_current_privilege_drift_still_holds(login_scope, fault, reason):
    base, policy, _ = login_scope
    target = sql.Identifier(policy.schema, 'jobs')
    role = sql.Identifier(policy.roles['authority'])
    with base.connect() as conn:
        if fault == 'missing_table': command = 'REVOKE SELECT ON {} FROM {}'
        elif fault == 'unexpected_update':
            command = 'GRANT UPDATE ON {} TO {}'
            target = sql.Identifier(policy.schema, 'ai_decisions')
        elif fault == 'table_grant_option': command = 'GRANT INSERT ON {} TO {} WITH GRANT OPTION'
        elif fault == 'worker_column':
            command = 'GRANT SELECT(input_bytes) ON {} TO {}'
            role = sql.Identifier(policy.roles['worker'])
        elif fault == 'column_grant_option': command = 'GRANT INSERT(input_bytes) ON {} TO {} WITH GRANT OPTION'
        elif fault == 'supervisor_read':
            command = 'REVOKE SELECT ON {} FROM {}'
            role = sql.Identifier(policy.roles['supervisor'])
        else:
            target = sql.Identifier(policy.schema, 'extra_matrix_table')
            conn.execute(sql.SQL('SET LOCAL ROLE {}').format(sql.Identifier(policy.owner)))
            conn.execute(sql.SQL('CREATE TABLE {} (value text)').format(target))
            command = 'GRANT SELECT ON {} TO {}'
        conn.execute(sql.SQL(command).format(target, role))
    with base.connect() as conn, pytest.raises(model.RolePolicyHold, match='^' + reason + '$'):
        model.audit_runtime_roles(conn, policy)


@pytest.mark.parametrize('fault', ['revoke_before_column', 'drop_before_table', 'drop_before_column'])
def test_changes_between_current_matrix_statements_fail_closed(login_scope, fault):
    base, policy, _ = login_scope
    extra = sql.Identifier(policy.schema, 'disappearing_matrix_table')
    if fault.startswith('drop_'):
        with base.connect() as conn:
            conn.execute(sql.SQL('SET LOCAL ROLE {}').format(sql.Identifier(policy.owner)))
            conn.execute(sql.SQL('CREATE TABLE {} (value text)').format(extra))

    class Change:
        changed = False
        def __init__(self, conn): self.conn = conn
        def __getattr__(self, name): return getattr(self.conn, name)
        def execute(self, query, params=None):
            kind = matrix_kind(query)
            trigger = 'table' if fault == 'drop_before_table' else 'column'
            if not self.changed and kind == trigger:
                self.changed = True
                if fault.startswith('drop_'):
                    self.conn.execute(sql.SQL('DROP TABLE {}').format(extra))
                else:
                    target = sql.Identifier(policy.schema, 'jobs')
                    role = sql.Identifier(policy.roles['authority'])
                    self.conn.execute(sql.SQL('REVOKE SELECT ON {} FROM {}').format(target, role))
                    self.conn.execute(sql.SQL('GRANT SELECT(input_bytes) ON {} TO {}').format(target, role))
            return self.conn.execute(query, params)

    reason = 'runtime_table_grant_matrix' if fault == 'drop_before_table' else 'runtime_column_grant_matrix'
    with base.connect() as conn:
        changed = Change(conn)
        with pytest.raises(model.RolePolicyHold, match='^' + reason + '$'):
            model.audit_runtime_roles(changed, policy)
        assert changed.changed
