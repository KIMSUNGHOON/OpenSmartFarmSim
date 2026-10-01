"""Every runtime identity must retain the complete closed privilege matrix."""

from psycopg import sql
import pytest

from test_runtime_roles import role_scope, pg_store, installed
from app.runtime_roles import audit_runtime_roles, RolePolicyHold


@pytest.mark.parametrize('kind', ['request', 'worker', 'supervisor', 'authority'])
@pytest.mark.parametrize('fault', ['table', 'column_grant_option', 'schema', 'sequence', 'routine'])
def test_each_role_rejects_unapproved_effective_privileges(role_scope, kind, fault):
    store, policy = role_scope
    installed(role_scope)
    role = sql.Identifier(policy.roles[kind])
    namespace = sql.Identifier(policy.schema)
    with store.connect() as conn:
        if fault == 'table':
            conn.execute(sql.SQL('GRANT UPDATE ON TABLE {}.ai_decisions TO {}')
                .format(namespace, role))
        elif fault == 'column_grant_option':
            conn.execute(sql.SQL('GRANT SELECT(input_bytes) ON TABLE {}.jobs TO {} WITH GRANT OPTION')
                .format(namespace, role))
        elif fault == 'schema':
            conn.execute(sql.SQL('GRANT CREATE ON SCHEMA {} TO {}').format(namespace, role))
        elif fault == 'sequence':
            conn.execute(sql.SQL('CREATE SEQUENCE {}.audit_sequence').format(namespace))
            conn.execute(sql.SQL('ALTER SEQUENCE {}.audit_sequence OWNER TO {}')
                .format(namespace, sql.Identifier(policy.owner)))
            conn.execute(sql.SQL('GRANT USAGE ON SEQUENCE {}.audit_sequence TO {}')
                .format(namespace, role))
        else:
            routine = conn.execute('SELECT proname FROM pg_proc WHERE pronamespace=%s::regnamespace '
                'ORDER BY proname LIMIT 1', (policy.schema,)).fetchone()['proname']
            conn.execute(sql.SQL('GRANT EXECUTE ON FUNCTION {}.{}() TO {}')
                .format(namespace, sql.Identifier(routine), role))
    with store.connect() as conn, pytest.raises(RolePolicyHold):
        audit_runtime_roles(conn, policy)
