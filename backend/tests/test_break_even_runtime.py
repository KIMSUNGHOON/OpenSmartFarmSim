"""Real SCRAM for synthetic, pinned full-path break-even replay."""
from dataclasses import replace
from pathlib import Path
import sys
import psycopg
from psycopg import sql
import pytest
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from app.break_even_store import BreakEvenStore
from app.runtime_roles import RuntimeLoginPolicy, RolePolicyHold, audit_runtime_roles
from app.runtime_login import connect_runtime
from login_database import login_database, login_scope
from test_api_break_even import app_for, get
from test_break_even import trial_plan
from test_market_signed_hold_integration import signed_market_assembly


def test_break_even_profile_rejects_implicit_or_nonboolean_opt_in():
    for value in (None, 1, 'true'):
        with pytest.raises(RolePolicyHold):
            RuntimeLoginPolicy('schema', 'owner', 'roles', 'database', market_calculation=True, break_even_calculation=value)
    with pytest.raises(RolePolicyHold):
        RuntimeLoginPolicy('schema', 'owner', 'roles', 'database', break_even_calculation=True)


@pytest.mark.parametrize('login_scope', [{'market_calculation': True, 'break_even_calculation': True}], indirect=True)
@pytest.mark.parametrize('kind', ['request', 'worker', 'supervisor'])
def test_general_logins_cannot_read_break_even_table(login_scope, kind):
    _, policy, dsns = login_scope
    with connect_runtime(dsns[kind], policy, kind) as conn, pytest.raises(psycopg.errors.InsufficientPrivilege):
        conn.execute(sql.SQL('SELECT * FROM {}.break_even_plan_results LIMIT 0').format(sql.Identifier(policy.schema)))


@pytest.mark.parametrize('login_scope', [{'market_calculation': True, 'break_even_calculation': True}], indirect=True)
def test_bound_break_even_replays_signed_trials_and_safe_http_with_actual_scram(login_scope):
    base, policy, dsns = login_scope
    candidate_factory, source, market_request, principal, scope = signed_market_assembly(
        dsns['authority'], policy.schema, runtime_identity=(policy, 'authority'))
    _, request = trial_plan([20, 26, 32], candidate_repository_factory=lambda _: candidate_factory(),
        case_factory=lambda: (source, market_request))
    def store():
        return BreakEvenStore(dsns['authority'], policy.schema, candidate_factory(),
            principal_provider=lambda: principal, runtime_identity=(policy, 'authority'))
    pinned = store().pin_break_even_plan(request, source.break_even_plan)
    assert store().get_break_even_read('tenant-1', request['plan_id'])[1] == pinned
    assert store().get_break_even_read('tenant-2', request['plan_id']) is None
    app = app_for(store(), principal)
    path = '/v1/break-even-results?plan_id='+request['plan_id']
    assert get(app, path)[1]['zero_values'] == ['26']
    with store().connect() as conn:
        assert conn.pgconn.used_password
        assert audit_runtime_roles(conn, policy)['policy_version'] == 'runtime-break-even-login-policy-v4'
        assert conn.info.user == policy.roles['authority']
        assert not conn.execute('SELECT has_table_privilege(current_user,%s,\'UPDATE\') AS allowed',
            (policy.schema+'.break_even_plan_results',)).fetchone()['allowed']
    with pytest.raises(ValueError):
        BreakEvenStore(dsns['authority'], policy.schema, candidate_factory(), principal_provider=lambda: principal,
            runtime_identity=(replace(policy, break_even_calculation=False), 'authority'))
    wrong = BreakEvenStore(dsns['request'], policy.schema, candidate_factory(), principal_provider=lambda: principal,
        runtime_identity=(policy, 'authority'))
    with pytest.raises(RolePolicyHold, match='^runtime_login_rejected$'): wrong.connect()
    scope['scope_version'] = 'v2'
    assert get(app, path)[0] == 503
    scope['scope_version'] = 'v1'
    with base.connect() as conn:
        conn.execute(sql.SQL('GRANT SELECT ON {}.break_even_plan_results TO {}').format(
            sql.Identifier(policy.schema), sql.Identifier(policy.roles['worker'])))
    with pytest.raises(RolePolicyHold, match='^market_runtime_grants_rejected$'): store().connect()
    assert get(app, path)[0] == 503
