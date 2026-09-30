"""Authored Run table is an opt-in authority-only SQL boundary."""

from pathlib import Path
import sys

from psycopg import errors, sql
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.runtime_login import connect_runtime
from app.runtime_roles import RuntimeLoginPolicy, RolePolicyHold, audit_runtime_roles
from login_database import login_database, login_scope


def test_run_profile_requires_release_custody():
    with pytest.raises(RolePolicyHold):
        RuntimeLoginPolicy('project', 'owner', 'prefix', 'database',
            authored_run_storage=True)


@pytest.mark.parametrize('login_scope', [{
    'authored_release_storage': True, 'authored_run_storage': True,
}], indirect=True)
def test_authored_run_table_has_only_authority_login(login_scope):
    base, policy, dsns = login_scope
    with base.connect() as conn:
        audit = audit_runtime_roles(conn, policy)
        assert audit['policy_version'] == 'runtime-authored-run-login-policy-v8'
    with connect_runtime(dsns['authority'], policy, 'authority') as conn:
        conn.execute(sql.SQL('SELECT * FROM {} LIMIT 0').format(
            base._table('authored_thermal_runs')))
    for kind in ('request', 'worker', 'supervisor'):
        with connect_runtime(dsns[kind], policy, kind) as conn, pytest.raises(
                errors.InsufficientPrivilege):
            conn.execute(sql.SQL('SELECT * FROM {} LIMIT 0').format(
                base._table('authored_thermal_runs')))
