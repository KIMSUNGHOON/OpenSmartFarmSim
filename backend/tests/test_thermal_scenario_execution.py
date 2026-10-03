"""Scenario-bound durable jobs use real records; captures and keys are synthetic."""

import json
import asyncio
from datetime import datetime, timezone, timedelta
from pathlib import Path
import sys

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from app.api import create_app
from app.thermal_simulation_worker import ThermalSimulationWorker
from test_api_job_status import get, UnusedMarketResultStore
from test_api_thermal_run import UnusedMarketHoldStore
from test_thermal_scenario_store import scenario_setup
from test_thermal_simulation_worker import simulation_setup, run_count
from login_database import login_database, login_scope
from test_api_serve import tls_files

pytestmark = pytest.mark.parametrize('login_scope', [{'thermal_scenario_storage': True,
    'market_calculation': True, 'break_even_calculation': True}], indirect=True)


@pytest.fixture
def bound_execution(scenario_setup, simulation_setup):
    store, runs, _, value, principal, _ = scenario_setup
    _, publisher, _, jobs, _, original_input, _, _ = simulation_setup
    record = store.put('tenant-a', value)
    data = {**original_input, 'input_version': 'thermal-simulation-input-v2',
        'scenario_id': value['scenario_id'], 'scenario_revision': value['scenario_revision'],
        'scenario_sha256': record['scenario_sha256']}
    job = jobs.submit('tenant-a', 'simulation', data, 'bound-scenario')
    worker = ThermalSimulationWorker(publisher, tenant_id='tenant-a', scenario_store=store)
    return worker, store, runs, jobs, job, data, principal, publisher


def application(setup):
    _, store, runs, jobs, _, _, principal, _ = setup
    return create_app(jobs, UnusedMarketHoldStore(), runs, UnusedMarketResultStore(),
        principal_provider=lambda: principal, thermal_scenario_store=store)


def test_versioned_scenario_execution_and_http_discovery_share_pins(bound_execution):
    worker, store, runs, jobs, job, data, _, _ = bound_execution
    result = worker.run_once(str(job['job_id']))
    assert result.state == 'succeeded'
    receipt = json.loads(jobs.read_artifact('tenant-a', job['job_id']))
    scenario = store.get('tenant-a', data['scenario_id'], data['scenario_revision'])
    assert receipt['receipt_version'] == 'thermal-simulation-result-v2'
    assert receipt['scenario_sha256'] == scenario['scenario_sha256']
    assert receipt['scenario_pins'] == scenario['pins']
    assert receipt['scenario_id'] == data['scenario_id'] and receipt['scenario_revision'] == data['scenario_revision']
    app = application(bound_execution)
    status, summary = get(app, f"/v1/jobs/{job['job_id']}/run")
    assert status == 200 and summary['run_id'] == result.run_id
    assert summary == get(app, f'/v1/runs/{result.run_id}')[1]
    assert 'scenario_pins' not in summary and run_count(runs) == 1
    assert worker.run_once(str(job['job_id'])) is None


@pytest.mark.parametrize('change', [{'scenario_id': 'unknown'}, {'scenario_revision': 'unknown'},
    {'scenario_sha256': '0'*64}, {'snapshot_id': 'thermal-snapshot-v1:'+('0'*64)}])
def test_unmatched_scenario_cannot_publish(bound_execution, change):
    worker, _, runs, jobs, _, data, _, _ = bound_execution
    job = jobs.submit('tenant-a', 'simulation', data | change, 'wrong-bound-scenario')
    result = worker.run_once(str(job['job_id']))
    assert result.state == 'hold' and result.reason_code == 'thermal_scenario_hold'
    assert jobs.get_publication('tenant-a', job['job_id']) is None and run_count(runs) == 0


def test_missing_store_holds_v2_instead_of_dropping_scenario_pins(bound_execution):
    _, _, runs, jobs, job, _, _, publisher = bound_execution
    result = ThermalSimulationWorker(publisher, tenant_id='tenant-a').run_once(str(job['job_id']))
    assert result.state == 'hold' and result.reason_code == 'thermal_scenario_hold'
    assert jobs.get_publication('tenant-a', job['job_id']) is None and run_count(runs) == 0


@pytest.mark.parametrize('point', ['prepare', 'insert'])
def test_scope_revocation_before_completion_rolls_back_run(bound_execution, monkeypatch, point):
    worker, _, runs, jobs, job, _, principal, publisher = bound_execution
    owner = publisher if point == 'prepare' else runs
    name = 'prepare' if point == 'prepare' else '_publish_verified_in_transaction'
    original = getattr(owner, name)
    def revoke(*args, **kwargs):
        result = original(*args, **kwargs)
        principal['scopes'].remove('thermal_scenario_read')
        return result
    monkeypatch.setattr(owner, name, revoke)
    result = worker.run_once(str(job['job_id']))
    assert result.state == 'hold' and result.reason_code == 'thermal_scenario_hold'
    assert jobs.get_publication('tenant-a', job['job_id']) is None and run_count(runs) == 0


@pytest.mark.parametrize('scope', ['thermal_scenario_read', 'thermal_snapshot_read',
    'decision_context_read', 'market_hold_context_read'])
def test_bound_result_requires_reference_scopes(bound_execution, scope):
    worker, _, _, _, job, _, principal, _ = bound_execution
    assert worker.run_once(str(job['job_id'])).state == 'succeeded'
    principal['scopes'].remove(scope)
    assert get(application(bound_execution), f"/v1/jobs/{job['job_id']}/run")[0] == 403


def test_current_scenario_failure_hides_stored_completion(bound_execution, monkeypatch):
    worker, store, _, _, job, _, _, _ = bound_execution
    assert worker.run_once(str(job['job_id'])).state == 'succeeded'
    monkeypatch.setattr(store, 'get', lambda *_: None)
    assert get(application(bound_execution), f"/v1/jobs/{job['job_id']}/run")[0] == 503


def test_valid_scenario_for_another_signed_context_cannot_use_this_review(bound_execution):
    from test_thermal_run_store import signed_context
    worker, store, runs, jobs, _, data, principal, _ = bound_execution
    record = store.get('tenant-a', data['scenario_id'], data['scenario_revision'])
    principal['scopes'].add('decision_context_write')
    _, raw, signature = signed_context('tenant-a', data['snapshot_id'], context_id='second-context', mode='ex_post_replay')
    runs.put_decision_context('tenant-a', raw, signature)
    original_resolver = store.holds._scope_resolver
    original_scope = original_resolver('tenant-a', data['snapshot_id'], record['scenario'].decision_context_id)
    store.holds._scope_resolver = lambda tenant, snapshot, context: (
        original_scope | {'decision_context_id': context} if context == 'second-context'
        else original_resolver(tenant, snapshot, context))
    hold = store.holds.issue_not_evaluated('tenant-a', data['snapshot_id'], 'second-context')
    value = record['scenario'].model_dump(mode='json') | {'scenario_id': 'second-scenario',
        'decision_context_id': 'second-context',
        'market_context': {'kind': 'unavailable', 'hold_report_id': hold['hold_report_id']}}
    other = store.put('tenant-a', value)
    job = jobs.submit('tenant-a', 'simulation', data | {'scenario_id': 'second-scenario',
        'scenario_sha256': other['scenario_sha256']}, 'other-context-review')
    result = worker.run_once(str(job['job_id']))
    assert result.state == 'hold' and result.reason_code == 'thermal_scenario_hold'
    assert jobs.get_publication('tenant-a', job['job_id']) is None and run_count(runs) == 0


def test_fresh_v6_api_runtime_reads_bound_job_under_bearer_identity(bound_execution, tls_files):
    from app.api_runtime import ApiRuntime
    from app.http_identity import BearerGrant, BearerRegistry, token_digest, current_principal
    from app.thermal_scenario_execution import SCENARIO_SCOPES
    from test_api_runtime import config, dependencies
    from test_http_identity import request
    worker, store, runs, jobs, job, _, _, _ = bound_execution
    result = worker.run_once(str(job['job_id']))
    assert result.state == 'succeeded'
    token = b'synthetic-bound-job-token-'+b'b'*32
    now = datetime.now(timezone.utc)
    scopes = frozenset(SCENARIO_SCOPES+('metadata', 'artifact', 'thermal_run_read'))
    registry = BearerRegistry((BearerGrant(token_digest(token), 'tenant-a', scopes,
        now-timedelta(seconds=1), now+timedelta(minutes=5)),))
    cert, key, _ = tls_files
    runtime = ApiRuntime(config(policy=jobs.runtime_identity[0], dsn=jobs._dsn,
        artifact_root=jobs.artifact_root, certificate=cert, private_key=key,
        thermal_gate_key=runs._gate_key, market_hold_key=store.holds._key),
        dependencies(bearer_registry=registry, context_verifier=runs._context_verifier,
            release_verifier=runs._release_verifier, market_scope_resolver=store.holds._scope_resolver))
    assert runtime.thermal_scenarios.runs is runtime.thermal
    assert runtime.thermal_scenarios.holds is runtime.market_holds
    path = f"/v1/jobs/{job['job_id']}/run"
    status, summary, headers = asyncio.run(request(runtime.service.app, path=path,
        headers=[(b'authorization', b'Bearer '+token), (b'x-tenant-id', b'tenant-b')]))
    assert status == 200 and summary['run_id'] == result.run_id
    assert headers[b'cache-control'] == b'no-store' and current_principal() is None


@pytest.mark.parametrize('change', [{'coefficients': {'heat': 9}}, {'scenario_sha256': 'A'*64},
                                   {'approved_g1': True}])
def test_v2_input_remains_closed_and_reference_only(bound_execution, change):
    worker, _, runs, jobs, _, data, _, _ = bound_execution
    job = jobs.submit('tenant-a', 'simulation', data | change, 'invalid-bound-shape')
    result = worker.run_once(str(job['job_id']))
    assert result.state == 'failed' and result.reason_code == 'simulation_input_rejected'
    assert jobs.get_publication('tenant-a', job['job_id']) is None and run_count(runs) == 0


def test_receipt_pin_changes_are_not_hidden_by_matching_artifact_digest(bound_execution, monkeypatch):
    from hashlib import sha256
    from app.jobs import canonical_input_bytes
    worker, _, _, jobs, job, _, _, _ = bound_execution
    assert worker.run_once(str(job['job_id'])).state == 'succeeded'
    receipt = json.loads(jobs.read_artifact('tenant-a', job['job_id']))
    receipt['scenario_pins']['context_sha256'] = '0'*64
    raw = canonical_input_bytes(receipt)
    publication = jobs.get_publication('tenant-a', job['job_id'])
    publication.update(artifact_sha256=sha256(raw).hexdigest(), artifact_size=len(raw))
    publication['manifest']['artifact_sha256'] = publication['artifact_sha256']
    monkeypatch.setattr(jobs, 'get_publication', lambda *_: publication)
    monkeypatch.setattr(jobs, 'read_artifact', lambda *_: raw)
    assert get(application(bound_execution), f"/v1/jobs/{job['job_id']}/run")[0] == 503


def test_untyped_scenario_store_cannot_enter_worker_configuration(bound_execution):
    _, _, _, _, _, _, _, publisher = bound_execution
    with pytest.raises(ValueError, match='simulation worker binding rejected'):
        ThermalSimulationWorker(publisher, tenant_id='tenant-a', scenario_store=object())
