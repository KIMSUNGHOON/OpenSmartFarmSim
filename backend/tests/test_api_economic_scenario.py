"""Atomic scenario registration over actual SCRAM; synthetic sources/keys only."""

import asyncio
from copy import deepcopy
import json
from pathlib import Path
import sys

import pytest
from psycopg import sql

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from app.api import create_app
from app.job_store import JobStore
from app.jobs import canonical_input_bytes
from app.market_source_store import MarketSourceStore
from app.market_candidate_store import MarketCandidateStore
from app.market_hold_store import MarketHoldStore
from app.thermal_run_store import ThermalRunStore
from app.market_scenario import MarketScenarioRequest, _json
from app.api_economic_scenario import EconomicScenarioRequest, ECONOMIC_SCENARIO_SCOPES
from test_market_source_store import PROFILE, record_items, submit, login_database, login_scope
from test_market_signed_hold_integration import signed_market_assembly
from test_market_hold_store import HOLD_KEY, context_verifier
from test_api_job_status import UnusedMarketResultStore
from test_http_identity import request

pytestmark = pytest.mark.parametrize('login_scope', [PROFILE], indirect=True)


@pytest.fixture
def economic_api(login_scope):
    from app.api_economic_scenario import EconomicScenarioService
    from app.api_market_source import _MarketSources
    base, policy, dsns = login_scope
    _, values, req, principal, scope = signed_market_assembly(
        dsns['authority'], policy.schema, runtime_identity=(policy, 'authority'))
    req = MarketScenarioRequest.model_validate_json(_json(req)).model_dump(mode='json')
    principal['scopes'].update({'metadata', 'market_source_read', 'market_source_write',
                               'decision_context_read'})
    provider = lambda: principal
    jobs = JobStore(dsns['authority'], policy.schema, base.artifact_root,
        runtime_identity=(policy, 'authority'), principal_provider=provider, audit_runtime_grants=True)
    sources = MarketSourceStore(dsns['authority'], policy.schema,
        runtime_identity=(policy, 'authority'), principal_provider=provider)
    for kind, model in record_items(values):
        sources.adopt_job('tenant-1', kind, str(submit(base, model)['job_id']))
    req['shock']['sha256'] = sources.get_joint_shock_pin('joint-1', 'r1')['sha256']
    contexts = ThermalRunStore(dsns['authority'], policy.schema,
        gate_key=b'synthetic-gate-key-32-bytes-long!', release_verifier=lambda *_: None,
        context_verifier=context_verifier, runtime_identity=(policy, 'authority'), principal_provider=provider)
    holds = MarketHoldStore(dsns['authority'], policy.schema, context_store=contexts,
        scope_resolver=lambda *_: dict(scope), signing_key=HOLD_KEY,
        runtime_identity=(policy, 'authority'), principal_provider=provider)
    view = _MarketSources(sources, holds, principal_provider=provider)
    candidates = MarketCandidateStore(dsns['authority'], policy.schema, view,
        runtime_identity=(policy, 'authority'), principal_provider=provider)
    service = EconomicScenarioService(jobs, candidates)
    app = create_app(jobs, holds, contexts, UnusedMarketResultStore(),
        principal_provider=provider, economic_scenario_service=service)
    return app, jobs, candidates, principal, service, req


def post(app, body, *, raw=None):
    return asyncio.run(request(app, path='/v1/economic-scenarios', method='POST',
        headers=[(b'content-type', b'application/json'), (b'x-tenant-id', b'foreign')],
        body=json.dumps(body).encode() if raw is None else raw))[:2]


def counts(jobs):
    with jobs.connect() as conn:
        return tuple(conn.execute(sql.SQL('SELECT count(*) AS n FROM {}')
            .format(jobs._table(name))).fetchone()['n']
            for name in ('jobs', 'market_candidate_pins', 'market_candidate_inputs'))


def test_registration_is_atomic_replayable_and_idempotent(economic_api):
    app, jobs, candidates, _, service, req = economic_api
    before = counts(jobs)
    body = {'request': req, 'idempotency_key': 'economic-http'}
    status, response = post(app, body)
    assert status == 200 and response['registration_status'] == 'pinned_user_assumption'
    assert response['intent_job']['state'] == 'queued' and response['intent_job']['attempt_count'] == 0
    assert counts(jobs)[0:2] == (before[0]+1, 1) and counts(jobs)[2] > 0
    assert post(app, body) == (200, response)
    assert 'tenant_id' not in response and 'economic_result' not in response
    with jobs.connect() as conn:
        row = conn.execute(sql.SQL('SELECT * FROM {} WHERE job_id=%s')
            .format(jobs._table('jobs')), (response['intent_job']['job_id'],)).fetchone()
    assert row['input_bytes'] == canonical_input_bytes(req)
    fresh = MarketCandidateStore(candidates.dsn, candidates.schema, candidates._source,
        runtime_identity=candidates.runtime_identity, principal_provider=candidates._principal_provider)
    stored = fresh.get_market_candidate(response['scenario_id'], response['scenario_revision'])
    assert stored['candidate_id'] == response['candidate_id']
    assert stored['economic_scenario_sha256'] == response['scenario_sha256']
    from app.market_scenario import MarketScenarioService
    result = MarketScenarioService(fresh).calculate_pinned(
        response['scenario_id'], response['scenario_revision'], 'tenant-1')
    assert result.assessment_status == 'hold'


@pytest.mark.parametrize('scope', ECONOMIC_SCENARIO_SCOPES)
def test_each_scope_is_required_before_any_admission(economic_api, scope):
    app, jobs, _, principal, _, req = economic_api
    before = counts(jobs)
    principal['scopes'].remove(scope)
    assert post(app, {'request': req, 'idempotency_key': 'denied'})[0] == 403
    assert counts(jobs) == before


@pytest.mark.parametrize('fault', ['tenant', 'baseline_hash', 'shock_hash', 'market_context'])
def test_unbound_request_never_creates_intent_or_candidate(economic_api, fault):
    app, jobs, _, _, _, template = economic_api
    before = counts(jobs)
    req = deepcopy(template)
    if fault == 'tenant': req['tenant_id'] = 'foreign'
    if fault == 'baseline_hash': req['baseline']['sha256'] = 'a'*64
    if fault == 'shock_hash': req['shock']['sha256'] = 'b'*64
    if fault == 'market_context': req['market_context']['hold_report_id'] = 'market-hold-v1:'+'c'*64
    assert post(app, {'request': req, 'idempotency_key': 'unbound'})[0] == 422
    assert counts(jobs) == before


@pytest.mark.parametrize('scope', ['market_candidate_write', 'decision_context_read'])
def test_revocation_after_candidate_insert_rolls_back_all_objects(economic_api, monkeypatch, scope):
    app, jobs, candidates, principal, _, req = economic_api
    before = counts(jobs)
    original = candidates._checked_candidate
    def revoke(*args):
        result = original(*args)
        principal['scopes'].remove(scope)
        return result
    monkeypatch.setattr(candidates, '_checked_candidate', revoke)
    assert post(app, {'request': req, 'idempotency_key': 'revoked'})[0] == 403
    assert counts(jobs) == before


@pytest.mark.parametrize('phase', ['lookup', 'insert'])
def test_same_policy_source_rebinding_rolls_back(economic_api, monkeypatch, phase):
    app, jobs, candidates, _, _, req = economic_api
    before = counts(jobs)
    view = candidates._source
    original = candidates._checked_candidate if phase == 'insert' else view._source.get_joint_shock
    def rebind(*args):
        result = original(*args)
        old = view._source
        view._source = MarketSourceStore(old.dsn, old.schema,
            principal_provider=old._principal_provider, runtime_identity=old.runtime_identity)
        return result
    if phase == 'insert': monkeypatch.setattr(candidates, '_checked_candidate', rebind)
    else: monkeypatch.setattr(view._source, 'get_joint_shock', rebind)
    assert post(app, {'request': req, 'idempotency_key': 'rebound'})[0] == 503
    assert counts(jobs) == before


def test_changed_preparation_at_commit_rolls_back(economic_api, monkeypatch):
    app, jobs, _, _, service, req = economic_api
    before = counts(jobs)
    original = service._prepare
    calls = []
    def change(*args):
        prepared = original(*args)
        calls.append(True)
        if len(calls) > 1: prepared[2]['rights_manifest_sha256'] = 'd'*64
        return prepared
    monkeypatch.setattr(service, '_prepare', change)
    assert post(app, {'request': req, 'idempotency_key': 'changed'})[0] == 503
    assert len(calls) == 2 and counts(jobs) == before


def test_numeric_collision_rolls_back_job_and_candidate(economic_api):
    from hashlib import sha256
    app, jobs, candidates, _, service, req = economic_api
    _, _, _, numbers = service._prepare('tenant-1', MarketScenarioRequest.model_validate_json(_json(req)))
    item = deepcopy(numbers[0])
    item['value'] = '999'
    from app.economic_contracts import OwnedEconomicRecord
    raw = canonical_input_bytes(OwnedEconomicRecord.model_validate(item).model_dump(mode='json'))
    with jobs.connect() as conn:
        conn.execute(sql.SQL('INSERT INTO {} (tenant_id,input_id,revision,payload_raw,payload_sha256) VALUES (%s,%s,%s,%s,%s)')
            .format(jobs._table('market_candidate_inputs')), ('tenant-1', item['input_id'], item['revision'], raw, sha256(raw).hexdigest()))
    before = counts(jobs)
    assert post(app, {'request': req, 'idempotency_key': 'numeric-conflict'})[0] == 409
    assert counts(jobs) == before


@pytest.mark.parametrize('fault', ['insert', 'lookup'])
def test_private_failure_and_body_bound_leave_no_admission(economic_api, monkeypatch, fault):
    app, jobs, candidates, _, _, req = economic_api
    before = counts(jobs)
    body = {'request': req, 'idempotency_key': 'private-failure'}
    assert post(app, body, raw=b' '*4097)[0] == 413
    def fail(*_): raise RuntimeError('private server/source detail')
    if fault == 'insert': monkeypatch.setattr(candidates, '_pin_in_transaction', fail)
    else: monkeypatch.setattr(candidates._source._source, 'get_joint_shock', fail)
    status, response = post(app, body)
    assert status == 503 and 'private' not in str(response) and counts(jobs) == before
