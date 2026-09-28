"""User assumptions survive fresh readers; synthetic records confer no data gate."""

from dataclasses import replace
from concurrent.futures import ThreadPoolExecutor
from datetime import timedelta
from hashlib import sha256
from pathlib import Path
import sys

import psycopg
from psycopg import sql
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from app.economic_contracts import (EconomicScenario, OwnedEconomicRecord,
    OwnedSettlementRecord, PriorBatchCostRecord)
from app.jobs import canonical_input_bytes
from app.market_scenario import JointShock, InputRights, Applicability, MarketScenarioService
from app.market_source_store import MarketSourceStore
from app.market_candidate_store import MarketCandidateStore
from app.market_result_store import MarketResultStore
from app.break_even_store import BreakEvenStore
from app.runtime_roles import RuntimeLoginPolicy, RolePolicyHold, audit_runtime_roles
from app.runtime_login import connect_runtime
from login_database import login_database, login_scope
from test_economics import base, opening_lot, TrustedTestRepository
from test_market_scenario import case
from test_break_even import trial_plan
from test_market_signed_hold_integration import signed_market_assembly
from test_api_break_even import app_for, get


PROFILE = {'market_calculation': True, 'market_source_storage': True}
MODELS = {'economic_scenario': EconomicScenario, 'economic_input': OwnedEconomicRecord,
    'joint_shock': JointShock, 'input_rights': InputRights,
    'settlement_applicability': Applicability, 'settlement_evidence': OwnedSettlementRecord,
    'prior_batch_cost': PriorBatchCostRecord}


def record_items(source):
    groups = {'economic_scenario': source.scenarios, 'economic_input': source.records,
        'joint_shock': source.shocks, 'input_rights': source.rights,
        'settlement_applicability': source.bindings, 'settlement_evidence': source.settlements,
        'prior_batch_cost': source.prior_costs}
    for kind, values in groups.items():
        for value in values.values():
            yield kind, MODELS[kind].model_validate(value)


def submit(base_store, model, *, stage='simulation', tenant='tenant-1'):
    data = model.model_dump(mode='json') if hasattr(model, 'model_dump') else model
    raw = canonical_input_bytes(data)
    return base_store.submit(tenant, stage, data, 'source-'+sha256(raw).hexdigest())


def store_for(login_scope, principal):
    _, policy, dsns = login_scope
    return MarketSourceStore(dsns['authority'], policy.schema,
        principal_provider=lambda: principal, runtime_identity=(policy, 'authority'))


@pytest.fixture
def source_setup(login_scope):
    principal = {'authenticated': True, 'tenant_id': 'tenant-1',
                 'scopes': {'market_source_read', 'market_source_write'}}
    return store_for(login_scope, principal), principal


@pytest.mark.parametrize('login_scope', [PROFILE], indirect=True)
def test_all_seven_typed_families_and_server_pins_survive_fresh_reader(login_scope, source_setup):
    base_store, policy, dsns = login_scope
    store, principal = source_setup
    source, _ = case()
    prior = TrustedTestRepository(EconomicScenario.model_validate(base(opening_inventory=(opening_lot(),))))
    source.prior_costs = prior.prior_costs
    jobs = {}
    originals = {}
    for kind, model in record_items(source):
        job = submit(base_store, model, stage='collection' if kind == 'economic_scenario' else 'simulation')
        adopted = store.adopt_job('tenant-1', kind, str(job['job_id']))
        assert adopted == model.model_dump(mode='python')
        assert store.adopt_job('tenant-1', kind, str(job['job_id'])) == adopted
        jobs[kind] = job
        originals[kind] = adopted
    fresh = store_for(login_scope, principal)
    scenario = fresh.get_economic_scenario('scenario-1', 'r1')
    pin = fresh.get_economic_scenario_pin('scenario-1', 'r1')
    assert scenario == originals['economic_scenario']
    assert pin['immutable_job_input_ref'] == str(jobs['economic_scenario']['job_id'])
    assert pin['payload_sha256'] == pin['immutable_job_input_sha256'] == jobs['economic_scenario']['input_sha256']
    shock = fresh.get_joint_shock('joint-1', 'r1')
    shock_pin = fresh.get_joint_shock_pin('joint-1', 'r1')
    assert shock == originals['joint_shock'] and shock_pin['sha256'] == jobs['joint_shock']['input_sha256']
    assert fresh.get_prior_batch_cost('prior-batch-cost') == originals['prior_batch_cost']
    number = originals['economic_input']
    assert fresh.get_economic_input(number['input_id'], number['revision']) == number
    rights = originals['input_rights']
    assert fresh.get_input_rights(rights['input_id'], rights['revision']) == rights
    binding = originals['settlement_applicability']
    assert fresh.get_settlement_applicability(binding['binding_id'], binding['revision']) == binding
    evidence = originals['settlement_evidence']
    assert fresh.get_settlement_evidence(evidence['settlement_ref'], evidence['revision']) == evidence
    with fresh.connect() as conn:
        assert conn.pgconn.used_password and conn.info.user == policy.roles['authority']
        assert audit_runtime_roles(conn, policy)['policy_version'] == 'runtime-market-source-login-policy-v5'
        for privilege in ('SELECT', 'INSERT', 'UPDATE', 'DELETE', 'TRUNCATE'):
            assert conn.execute('SELECT has_table_privilege(current_user,%s,%s) AS allowed',
                (policy.schema+'.market_source_records', privilege)).fetchone()['allowed'] == (privilege in {'SELECT', 'INSERT'})


@pytest.mark.parametrize('login_scope', [PROFILE], indirect=True)
def test_conflicting_version_rejected_and_correction_uses_new_revision(login_scope, source_setup):
    base_store, _, _ = login_scope
    store, _ = source_setup
    source, _ = case()
    model = OwnedEconomicRecord.model_validate(next(iter(source.records.values())))
    job = submit(base_store, model)
    store.adopt_job('tenant-1', 'economic_input', str(job['job_id']))
    changed = model.model_copy(update={'value': '999'})
    bad = submit(base_store, changed)
    with pytest.raises(ValueError, match='^market source version conflict$'):
        store.adopt_job('tenant-1', 'economic_input', str(bad['job_id']))
    newer = changed.model_copy(update={'revision': 'r-new'})
    store.adopt_job('tenant-1', 'economic_input', str(submit(base_store, newer)['job_id']))
    assert store.get_economic_input(model.input_id, model.revision)['value'] == model.value
    assert store.get_economic_input(model.input_id, 'r-new')['value'] == '999'


@pytest.mark.parametrize('login_scope', [PROFILE], indirect=True)
@pytest.mark.parametrize('fault', ['wrong_tenant', 'no_write', 'unknown_kind', 'wrong_stage',
    'wrong_shape', 'external_origin', 'noncanonical', 'missing_job'])
def test_admission_rejects_unbound_or_invalid_inputs(login_scope, source_setup, fault):
    base_store, policy, _ = login_scope
    store, principal = source_setup
    source, _ = case()
    model = OwnedEconomicRecord.model_validate(next(iter(source.records.values())))
    value = model.model_dump(mode='json')
    kind = 'economic_input'
    if fault == 'wrong_tenant': value['tenant_id'] = 'tenant-2'
    if fault == 'no_write': principal['scopes'].remove('market_source_write')
    if fault == 'unknown_kind': kind = 'arbitrary_approval'
    if fault == 'wrong_shape': value['approved_g0'] = True
    if fault == 'external_origin': value['origin'] = 'observed'
    if fault == 'noncanonical': value['available_at'] = value['available_at'].replace('Z', '+00:00')
    job = submit(base_store, value, stage='research' if fault == 'wrong_stage' else 'simulation')
    job_id = str(job['job_id']) if fault != 'missing_job' else '00000000-0000-0000-0000-000000000000'
    with pytest.raises(ValueError, match='^market source (admission denied|input rejected)$'):
        store.adopt_job('tenant-1', kind, job_id)
    with base_store.connect() as conn:
        assert conn.execute(sql.SQL('SELECT count(*) AS n FROM {}.market_source_records').format(
            sql.Identifier(policy.schema))).fetchone()['n'] == 0


@pytest.mark.parametrize('login_scope', [PROFILE], indirect=True)
def test_reads_require_current_tenant_and_scope_and_return_independent_values(login_scope, source_setup):
    base_store, _, _ = login_scope
    store, principal = source_setup
    scenario = EconomicScenario.model_validate(case()[0].scenarios[('scenario-1', 'r1')])
    store.adopt_job('tenant-1', 'economic_scenario', str(submit(base_store, scenario)['job_id']))
    value = store.get_economic_scenario('scenario-1', 'r1')
    value['harvests'][0]['quantity']['value'] = '999'
    assert store.get_economic_scenario('scenario-1', 'r1')['harvests'][0]['quantity']['value'] != '999'
    assert store.get_economic_scenario('absent', 'r1') is None
    principal['tenant_id'] = 'tenant-2'
    assert store.get_economic_scenario('scenario-1', 'r1') is None
    principal['tenant_id'] = 'tenant-1'
    principal['scopes'].remove('market_source_read')
    assert store.get_economic_scenario_pin('scenario-1', 'r1') is None
    assert not store.tenant_is_authenticated('tenant-1')


@pytest.mark.parametrize('login_scope', [PROFILE], indirect=True)
@pytest.mark.parametrize('kind', ['request', 'worker', 'supervisor'])
def test_general_logins_cannot_read_sources(login_scope, kind):
    _, policy, dsns = login_scope
    with connect_runtime(dsns[kind], policy, kind) as conn, pytest.raises(psycopg.errors.InsufficientPrivilege):
        conn.execute(sql.SQL('SELECT * FROM {}.market_source_records LIMIT 0').format(sql.Identifier(policy.schema)))


def test_storage_profile_and_binding_are_explicit():
    for flag in (None, 1, 'true'):
        with pytest.raises(RolePolicyHold):
            RuntimeLoginPolicy('schema', 'owner', 'roles', 'database', market_calculation=True, market_source_storage=flag)
    with pytest.raises(RolePolicyHold):
        RuntimeLoginPolicy('schema', 'owner', 'roles', 'database', market_source_storage=True)
    p = RuntimeLoginPolicy('schema', 'owner', 'roles', 'database', market_calculation=True)
    for binding in (None, (p, 'authority'), (replace(p, market_source_storage=True), 'worker')):
        with pytest.raises(ValueError, match='^market source binding rejected$'):
            MarketSourceStore('private dsn', 'schema', principal_provider=lambda: None, runtime_identity=binding)


def test_job_input_allows_only_an_exact_nonsecret_raw_digest_reference():
    assert canonical_input_bytes({'raw_sha256': 'a'*64}) == b'{"raw_sha256":"'+b'a'*64+b'"}'
    for key, value in [('raw_sha256', 'private source bytes'), ('raw_sha256', 'A'*64),
            ('raw_sha256', {'secret': 'value'}), ('rawSha256', 'a'*64),
            ('raw_source', 'a'*64), ('password', 'a'*64), ('raw_data', 'a'*64)]:
        with pytest.raises(ValueError): canonical_input_bytes({key: value})


@pytest.mark.parametrize('login_scope', [PROFILE], indirect=True)
def test_concurrent_adoption_is_idempotent_and_owner_updates_are_blocked(login_scope, source_setup):
    base_store, policy, _ = login_scope
    store, _ = source_setup
    scenario = EconomicScenario.model_validate(case()[0].scenarios[('scenario-1', 'r1')])
    job = submit(base_store, scenario)
    with ThreadPoolExecutor(max_workers=3) as pool:
        results = list(pool.map(lambda _: store.adopt_job('tenant-1', 'economic_scenario', str(job['job_id'])), range(3)))
    assert results[0] == results[1] == results[2]
    table = sql.SQL('{}.market_source_records').format(sql.Identifier(policy.schema))
    with base_store.connect() as conn:
        assert conn.execute(sql.SQL('SELECT count(*) AS n FROM {}').format(table)).fetchone()['n'] == 1
    for operation in ('UPDATE {} SET revision=revision', 'DELETE FROM {}'):
        with base_store.connect() as conn, pytest.raises(psycopg.errors.RaiseException):
            conn.execute(sql.SQL(operation).format(table))


@pytest.mark.parametrize('login_scope', [PROFILE], indirect=True)
def test_wrong_login_downgrade_and_grant_drift_fail_before_source_reads(login_scope, source_setup):
    base_store, policy, dsns = login_scope
    store, principal = source_setup
    wrong = MarketSourceStore(dsns['request'], policy.schema, principal_provider=lambda: principal,
        runtime_identity=(policy, 'authority'))
    with pytest.raises(RolePolicyHold, match='^runtime_login_rejected$'):
        wrong.get_economic_scenario('scenario-1', 'r1')
    with store.connect() as conn, pytest.raises(RolePolicyHold):
        audit_runtime_roles(conn, replace(policy, market_source_storage=False))
    with base_store.connect() as conn:
        conn.execute(sql.SQL('GRANT SELECT ON {}.market_source_records TO {}').format(
            sql.Identifier(policy.schema), sql.Identifier(policy.roles['worker'])))
    with pytest.raises(RolePolicyHold, match='^market_runtime_grants_rejected$'):
        store.get_economic_scenario('scenario-1', 'r1')


@pytest.mark.parametrize('login_scope', [PROFILE], indirect=True)
def test_original_job_corruption_is_detected_on_replay(login_scope, source_setup):
    base_store, policy, _ = login_scope
    store, _ = source_setup
    scenario = EconomicScenario.model_validate(case()[0].scenarios[('scenario-1', 'r1')])
    job = submit(base_store, scenario)
    store.adopt_job('tenant-1', 'economic_scenario', str(job['job_id']))
    with base_store.connect() as conn:
        # Privileged corruption fixture, not a deployed operation or admission path.
        table = sql.SQL('{}.jobs').format(sql.Identifier(policy.schema))
        conn.execute(sql.SQL('ALTER TABLE {} DISABLE TRIGGER ALL').format(table))
        conn.execute(sql.SQL('UPDATE {} SET input_bytes=%s,input_sha256=%s WHERE job_id=%s').format(table),
            (b'{}', sha256(b'{}').hexdigest(), job['job_id']))
        conn.execute(sql.SQL('ALTER TABLE {} ENABLE TRIGGER ALL').format(table))
    with pytest.raises(ValueError, match='^market source input rejected$'):
        store.get_economic_scenario_pin('scenario-1', 'r1')


@pytest.mark.parametrize('login_scope', [PROFILE], indirect=True)
@pytest.mark.parametrize('fault', ['future_available', 'use_denied'])
def test_storage_admission_does_not_bypass_decision_time_or_rights(login_scope, fault):
    base_store, policy, dsns = login_scope
    original, source, request, principal, _ = signed_market_assembly(dsns['authority'], policy.schema,
        runtime_identity=(policy, 'authority'))
    principal['scopes'].update({'market_source_read', 'market_source_write'})
    shock = source.shocks[('joint-1', 'r1')]
    store = store_for(login_scope, principal)
    if fault == 'use_denied':
        raw = JointShock.model_validate(shock).model_dump(mode='json')
        raw['rights']['use'] = 'denied'
        with pytest.raises(ValueError, match='^market source input rejected$'):
            store.adopt_job('tenant-1', 'joint_shock', str(submit(base_store, raw)['job_id']))
        assert store.get_joint_shock('joint-1', 'r1') is None
        return
    if fault == 'future_available': shock['available_at'] += timedelta(days=1)
    for kind, model in record_items(source):
        store.adopt_job('tenant-1', kind, str(submit(base_store, model)['job_id']))
    request['shock']['sha256'] = store.get_joint_shock_pin('joint-1', 'r1')['sha256']
    signed = original()._source
    class Sources:
        def get_market_hold_report(self, report_id): return signed.get_market_hold_report(report_id)
        def get_decision_context(self, *args): return signed.get_decision_context(*args)
        def __getattr__(self, name): return getattr(store, name)
    candidates = MarketCandidateStore(dsns['authority'], policy.schema, Sources(),
        principal_provider=lambda: principal, runtime_identity=(policy, 'authority'))
    with pytest.raises(ValueError, match='available|rights|use'):
        MarketScenarioService(candidates).build_candidate(request, 'tenant-1')


@pytest.mark.parametrize('login_scope', [{**PROFILE, 'break_even_calculation': True}], indirect=True)
def test_signed_economic_and_grid_replay_after_original_memory_records_are_removed(login_scope):
    base_store, policy, dsns = login_scope
    original_factory, source, template, principal, _ = signed_market_assembly(dsns['authority'], policy.schema,
        runtime_identity=(policy, 'authority'))
    principal['scopes'].update({'market_source_read', 'market_source_write'})
    store = store_for(login_scope, principal)
    baseline = EconomicScenario.model_validate(source.scenarios[('scenario-1', 'r1')])
    job = submit(base_store, baseline)
    source.pins[('scenario-1', 'r1')]['immutable_job_input_ref'] = str(job['job_id'])
    source.scenario_pin['immutable_job_input_ref'] = str(job['job_id'])
    signed_holds = original_factory()._source
    source.get_market_hold_report = signed_holds.get_market_hold_report
    source.get_decision_context = signed_holds.get_decision_context
    _, plan_request = trial_plan([20, 26, 32], case_factory=lambda: (source, template))
    plan = source.break_even_plan
    requests = [value['request'] for value in source.candidates.values()]
    for kind, model in record_items(source):
        if kind == 'economic_scenario' and model.scenario_id != baseline.scenario_id:
            continue
        store.adopt_job('tenant-1', kind, str(submit(base_store, model)['job_id']))
    for name in ('scenarios', 'records', 'shocks', 'rights', 'bindings', 'settlements', 'prior_costs', 'pins', 'shock_pins', 'candidates'):
        getattr(source, name).clear()

    class HeldSources:
        def __init__(self): self._source = store_for(login_scope, principal)
        def get_market_hold_report(self, report_id): return signed_holds.get_market_hold_report(report_id)
        def get_decision_context(self, *args): return signed_holds.get_decision_context(*args)
        def __getattr__(self, name): return getattr(self._source, name)

    def candidates():
        return MarketCandidateStore(dsns['authority'], policy.schema, HeldSources(),
            principal_provider=lambda: principal, runtime_identity=(policy, 'authority'))
    for index, request in enumerate(requests):
        # The adopted typed wire includes explicit optional defaults. Its actual
        # immutable hash, rather than the earlier in-memory fixture hash, is used.
        request['shock']['sha256'] = store.get_joint_shock_pin(
            request['shock']['shock_id'], request['shock']['revision'])['sha256']
        candidate = MarketScenarioService(candidates()).build_candidate(request, 'tenant-1')
        assert candidate.status == 'pinned'
        plan['trials'][index].update(scenario_id=candidate.scenario_id,
            revision=candidate.revision, scenario_sha256=candidate.economic_scenario_sha256)
    results = MarketResultStore(dsns['authority'], policy.schema, candidates(),
        principal_provider=lambda: principal, runtime_identity=(policy, 'authority'))
    first = plan['trials'][0]
    economic = results.pin_market_result(first['scenario_id'], first['revision'])
    assert results.get_economic_result('tenant-1', economic.economic_result.result_id) == economic
    assert economic.assessment_status == 'hold' and economic.calculation_status == 'conditional_user_assumption'
    def grid_store():
        return BreakEvenStore(dsns['authority'], policy.schema, candidates(),
            principal_provider=lambda: principal, runtime_identity=(policy, 'authority'))
    pinned = grid_store().pin_break_even_plan(plan_request, plan)
    assert grid_store().get_break_even_read('tenant-1', plan_request['plan_id'])[1] == pinned
    status, public = get(app_for(grid_store(), principal), '/v1/break-even-results?plan_id='+plan_request['plan_id'])
    assert status == 200 and public['zero_values'] == ['26'] and public['assessment_status'] == 'hold'
    principal['scopes'].remove('market_source_read')
    assert get(app_for(grid_store(), principal), '/v1/break-even-results?plan_id='+plan_request['plan_id'])[0] == 404
