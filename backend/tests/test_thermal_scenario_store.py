"""Immutable execution intents with actual SCRAM and synthetic signed references."""

import json
from pathlib import Path
import sys

import pytest
from psycopg import sql

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from app.thermal_scenario_store import ThermalScenario, ThermalScenarioStore, ThermalScenarioHold
from app.market_hold_store import MarketHoldStore
from app.runtime_roles import RolePolicyHold, audit_runtime_roles
from test_thermal_simulation_worker import simulation_setup
from login_database import login_database, login_scope

pytestmark = pytest.mark.parametrize('login_scope', [{'thermal_scenario_storage': True}], indirect=True)


@pytest.fixture
def scenario_setup(simulation_setup):
    _, _, runs, jobs, _, data, principal, base = simulation_setup
    principal['scopes'].update({'thermal_scenario_write', 'thermal_scenario_read', 'market_hold_issue',
                              'market_hold_context_read'})
    with jobs.connect() as conn:
        raw = conn.execute(sql.SQL('SELECT input_bytes FROM {} WHERE tenant_id=%s AND job_id=%s')
            .format(jobs._table('jobs')), ('tenant-a', data['review_job_id'])).fetchone()['input_bytes']
    context_id = json.loads(raw)['decision_context_id']
    scope = {'scope_version': 'synthetic-scope-v1', 'tenant_id': 'tenant-a',
        'snapshot_id': data['snapshot_id'], 'decision_context_id': context_id, 'candidate_ids': ['fixture-candidate'],
        'sales_start_utc': '2026-09-28T00:00:00Z', 'sales_end_utc': '2026-09-29T00:00:00Z'}
    holds = MarketHoldStore(jobs._dsn, jobs.schema, context_store=runs, scope_resolver=lambda *_: dict(scope),
        principal_provider=jobs.principal_provider, signing_key=b'synthetic-scenario-hold-key-32bytes',
        runtime_identity=jobs.runtime_identity)
    report = holds.issue_not_evaluated('tenant-a', data['snapshot_id'], context_id)
    value = {'schema_version': 'thermal-scenario-v1', 'scenario_id': 'scenario-1', 'scenario_revision': 'r1',
        'tenant_id': 'tenant-a', 'snapshot_id': data['snapshot_id'], 'decision_context_id': context_id,
        'market_context': {'kind': 'unavailable', 'hold_report_id': report['hold_report_id']},
        'zone_id': 'fixture-zone', 'goal_id': 'historical-thermal-replay', 'model_version': 'thermal-v1',
        'parameter_set_version': 'synthetic-thermal-parameters-v1', 'origin': 'user', 'evidence_level': 'assumed'}
    store = ThermalScenarioStore(runs, holds)
    return store, runs, holds, value, principal, base


def test_scenario_survives_fresh_store_and_is_immutable(scenario_setup):
    store, runs, holds, value, _, base = scenario_setup
    first = store.put('tenant-a', value)
    assert store.put('tenant-a', value) == first
    fresh = ThermalScenarioStore(runs, holds)
    assert fresh.get('tenant-a', 'scenario-1', 'r1') == first
    assert first['scenario'].model_dump(mode='json') == value
    assert set(first['pins']) == {'manifest_sha256', 'weather_sha256', 'thermal_sha256', 'context_sha256'}
    with pytest.raises(ThermalScenarioHold, match='conflicting immutable scenario'):
        store.put('tenant-a', value | {'zone_id': 'different-label'})
    revised = store.put('tenant-a', value | {'scenario_revision': 'r2', 'zone_id': 'different-label'})
    assert revised['scenario_sha256'] != first['scenario_sha256']
    assert fresh.get('tenant-a', 'scenario-1', 'r1') == first
    with base.connect() as conn:
        with pytest.raises(Exception, match='thermal scenario is immutable'):
            conn.execute(sql.SQL('DELETE FROM {}.thermal_scenarios').format(sql.Identifier(store.schema)))


@pytest.mark.parametrize('change', [{'model_version': 'invented-model'}, {'coefficients': {'heat': 999}},
    {'origin': 'provider'}, {'evidence_level': 'measured'}, {'goal_id': 'crop-ranking'},
    {'scenario_revision': ''}, {'scenario_id': 'x'*201}, {'snapshot_id': 'unfixed'},
    {'market_context': {'kind': 'available', 'snapshot_id': 'fake-g0'}}])
def test_contract_rejects_unsupported_or_unpinned_inputs(scenario_setup, change):
    store, _, _, value, _, _ = scenario_setup
    with pytest.raises(ThermalScenarioHold): store.put('tenant-a', value | change)


@pytest.mark.parametrize('fault', ['snapshot', 'context', 'hold', 'hold_scope'])
def test_actual_reference_failures_prevent_admission_or_read(scenario_setup, monkeypatch, fault):
    store, runs, holds, value, _, _ = scenario_setup
    store.put('tenant-a', value)
    if fault == 'snapshot': monkeypatch.setattr(runs, 'get_snapshot', lambda *_: None)
    if fault == 'context': monkeypatch.setattr(runs, 'get_decision_context', lambda *_: None)
    if fault == 'hold': monkeypatch.setattr(holds, 'get_market_hold_report', lambda *_: None)
    if fault == 'hold_scope': holds._scope_resolver = lambda *_: {}
    with pytest.raises(ThermalScenarioHold): store.get('tenant-a', 'scenario-1', 'r1')
    with pytest.raises(ThermalScenarioHold): store.put('tenant-a', value | {'scenario_revision': 'r2'})


def test_tenant_scope_and_runtime_grant_drift_are_enforced(scenario_setup):
    store, _, _, value, principal, base = scenario_setup
    store.put('tenant-a', value)
    assert store.get('tenant-b', 'scenario-1', 'r1') is None
    with pytest.raises(ThermalScenarioHold): store.put('tenant-b', value)
    principal['scopes'].remove('thermal_scenario_read')
    assert store.get('tenant-a', 'scenario-1', 'r1') is None
    principal['scopes'].add('thermal_scenario_read')
    principal['scopes'].remove('thermal_scenario_write')
    with pytest.raises(ThermalScenarioHold): store.put('tenant-a', value)
    principal['scopes'].add('thermal_scenario_write')
    policy = store.runtime_identity[0]
    with base.connect() as conn:
        conn.execute(sql.SQL('GRANT SELECT ON {}.thermal_scenarios TO {}').format(
            sql.Identifier(policy.schema), sql.Identifier(policy.roles['worker'])))
    with pytest.raises(ThermalScenarioHold, match='thermal scenario login rejected'):
        store.get('tenant-a', 'scenario-1', 'r1')


@pytest.mark.parametrize('fault', ['profile', 'unbound', 'dsn', 'principal'])
def test_matching_opt_in_store_bindings_are_required(scenario_setup, fault):
    _, runs, holds, _, _, _ = scenario_setup
    if fault == 'profile':
        from dataclasses import replace
        runs.runtime_identity = holds.runtime_identity = (replace(runs.runtime_identity[0], thermal_scenario_storage=False), 'authority')
    if fault == 'unbound': runs.runtime_identity = None
    if fault == 'dsn': holds.dsn = 'private-other-database'
    if fault == 'principal': holds._principal_provider = lambda: None
    with pytest.raises(ThermalScenarioHold): ThermalScenarioStore(runs, holds)


def test_v6_is_explicit_and_has_no_general_role_access(scenario_setup):
    store, _, _, _, _, base = scenario_setup
    policy = store.runtime_identity[0]
    with base.connect() as conn:
        assert audit_runtime_roles(conn, policy)['policy_version'] == 'runtime-thermal-scenario-login-policy-v6'
        for kind in ('request', 'worker', 'supervisor'):
            assert not conn.execute('SELECT has_table_privilege(%s,%s,%s) AS ok',
                (policy.roles[kind], policy.schema+'.thermal_scenarios', 'SELECT')).fetchone()['ok']
    with pytest.raises(RolePolicyHold):
        from dataclasses import replace
        replace(policy, thermal_scenario_storage=1)


def test_construct_bypass_and_poststartup_binding_drift_are_rejected(scenario_setup):
    store, runs, _, value, _, _ = scenario_setup
    forged = ThermalScenario.model_construct(**(value | {'model_version': 'fake'}))
    with pytest.raises(ThermalScenarioHold): store.put('tenant-a', forged)
    runs.dsn = 'private changed dsn'
    with pytest.raises(ThermalScenarioHold, match='thermal scenario binding rejected'):
        store.get('tenant-a', 'scenario-1', 'r1')


def test_write_scope_revoked_before_commit_rolls_back_registration(scenario_setup, monkeypatch):
    store, _, _, value, principal, _ = scenario_setup
    original = store._record
    def revoke(row):
        result = original(row)
        principal['scopes'].remove('thermal_scenario_write')
        return result
    monkeypatch.setattr(store, '_record', revoke)
    with pytest.raises(ThermalScenarioHold, match='thermal scenario registration denied'):
        store.put('tenant-a', value)
    assert store.get('tenant-a', 'scenario-1', 'r1') is None
