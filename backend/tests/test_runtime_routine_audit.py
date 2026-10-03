"""Current effective routine privileges remain denied after batching the read."""

import pytest
from psycopg import sql
from pathlib import Path
import sys

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from app.runtime_roles import audit_runtime_roles,RolePolicyHold
from test_runtime_roles import role_scope,pg_store,installed


@pytest.mark.parametrize('kind',['request','worker','supervisor','authority'])
@pytest.mark.parametrize('edge',[0,-1])
def test_current_grant_to_first_or_last_routine_is_rejected_then_revocation_restores(role_scope,kind,edge):
    store,policy=role_scope
    installed(role_scope)
    with store.connect() as conn:
        routines=conn.execute('SELECT proname FROM pg_proc WHERE pronamespace=%s::regnamespace ORDER BY oid',
            (policy.schema,)).fetchall()
        assert len(routines)>1
        routine=sql.Identifier(policy.schema,routines[edge]['proname'])
        role=sql.Identifier(policy.roles[kind])
        conn.execute(sql.SQL('GRANT EXECUTE ON FUNCTION {}() TO {}').format(routine,role))
    with store.connect() as conn,pytest.raises(RolePolicyHold,match='runtime_routine_privilege'):
        audit_runtime_roles(conn,policy)
    with store.connect() as conn:
        conn.execute(sql.SQL('REVOKE EXECUTE ON FUNCTION {}() FROM {}').format(routine,role))
        assert audit_runtime_roles(conn,policy)['routines']==len(routines)
