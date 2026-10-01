"""Actual-source server plan admission; synthetic records/keys only."""

import asyncio
from copy import deepcopy
from hashlib import sha256
import json
import os
from pathlib import Path
import sys

import pytest
from psycopg import sql

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from app.api import create_app
from app.break_even import BreakEvenRequest, BreakEvenService
from app.break_even_store import BreakEvenStore, _ProposedPlanRepository
from app.economic_contracts import EconomicScenario
from app.job_store import JobStore
from app.jobs import canonical_input_bytes
from app.market_candidate_store import MarketCandidateStore
from app.market_scenario import MarketScenarioService
from app.market_source_store import MarketSourceStore
from app.market_hold_store import MarketHoldStore
from app.thermal_run_store import ThermalRunStore
from app.api_market_source import _MarketSources
from test_market_source_store import PROFILE, record_items, submit, login_database, login_scope
from test_market_signed_hold_integration import signed_market_assembly
from test_market_hold_store import HOLD_KEY, context_verifier
from test_break_even import trial_plan
from test_api_job_status import UnusedMarketResultStore
from test_http_identity import request
from test_api_serve import tls_files

pytestmark = pytest.mark.parametrize('login_scope', [{**PROFILE, 'break_even_calculation': True}], indirect=True)


@pytest.fixture
def plan_api(login_scope):
    return build_plan_api(login_scope, [20, 32])


def build_plan_api(login_scope, values, *, progress=None):
    from app.break_even_plan_submission import BreakEvenPlanSubmissionService
    base, policy, dsns = login_scope
    original, source, template, principal, scope = signed_market_assembly(
        dsns['authority'], policy.schema, runtime_identity=(policy, 'authority'))
    principal['scopes'].update({'metadata', 'artifact', 'simulation_execute', 'market_source_read',
                               'market_source_write', 'decision_context_read'})
    baseline = EconomicScenario.model_validate(source.scenarios[('scenario-1', 'r1')])
    job = submit(base, baseline)
    source.pins[('scenario-1', 'r1')]['immutable_job_input_ref'] = str(job['job_id'])
    source.scenario_pin['immutable_job_input_ref'] = str(job['job_id'])
    signed = original()._source
    source.get_market_hold_report = signed.get_market_hold_report
    source.get_decision_context = signed.get_decision_context
    _, raw_request = trial_plan(values, case_factory=lambda: (source, template))
    if progress is not None:progress('generated', len(values))
    requests = [value['request'] for value in source.candidates.values()]
    provider = lambda: principal
    kwargs = dict(runtime_identity=(policy, 'authority'), principal_provider=provider)
    jobs = JobStore(dsns['authority'], policy.schema, base.artifact_root, audit_runtime_grants=True, **kwargs)
    os.close(jobs._content_directory(create=True))
    sources = MarketSourceStore(dsns['authority'], policy.schema, **kwargs)
    source_count = 0
    for kind, model in record_items(source):
        if kind == 'economic_scenario' and model.scenario_id != baseline.scenario_id: continue
        sources.adopt_job('tenant-1', kind, str(submit(base, model)['job_id']))
        source_count += 1
        if progress is not None and source_count % 64 == 0:progress('sources', source_count)
    if progress is not None:progress('sources_complete', source_count)
    for name in ('scenarios', 'records', 'shocks', 'rights', 'bindings', 'settlements', 'prior_costs',
                 'pins', 'shock_pins', 'candidates'):
        getattr(source, name).clear()
    contexts = ThermalRunStore(dsns['authority'], policy.schema,
        gate_key=b'synthetic-gate-key-32-bytes-long!', release_verifier=lambda *_: None,
        context_verifier=context_verifier, **kwargs)
    holds = MarketHoldStore(dsns['authority'], policy.schema, context_store=contexts,
        scope_resolver=lambda *_: dict(scope), signing_key=HOLD_KEY, **kwargs)
    candidates = MarketCandidateStore(dsns['authority'], policy.schema,
        _MarketSources(sources, holds, principal_provider=provider), **kwargs)
    pins = []
    for req in requests:
        req['shock']['sha256'] = sources.get_joint_shock_pin(req['shock']['shock_id'], req['shock']['revision'])['sha256']
        candidate = MarketScenarioService(candidates).build_candidate(req, 'tenant-1')
        pins.append({'scenario_id': candidate.scenario_id, 'revision': candidate.revision,
                     'scenario_sha256': candidate.economic_scenario_sha256})
        if progress is not None and len(pins) % 16 == 0:progress('candidates', len(pins))
    store = BreakEvenStore(dsns['authority'], policy.schema, candidates, **kwargs)
    service = BreakEvenPlanSubmissionService(jobs, store)
    app = create_app(jobs, holds, contexts, UnusedMarketResultStore(), principal_provider=provider,
        break_even_store=store, break_even_plan_service=service)
    body = {'request': BreakEvenRequest.model_validate(raw_request).model_dump(mode='json'), 'trials': pins}
    return app, service, body, principal


def post(app, body, *, raw=None):
    return asyncio.run(request(app, path='/v1/break-even-plans', method='POST',
        headers=[(b'content-type', b'application/json'), (b'x-tenant-id', b'foreign')],
        body=json.dumps(body).encode() if raw is None else raw))[:2]


def counts(service):
    with service.jobs.connect() as conn:
        return tuple(conn.execute(sql.SQL('SELECT count(*) AS n FROM {}')
            .format(service.jobs._table(name))).fetchone()['n']
            for name in ('jobs', 'job_publications', 'break_even_plan_results'))


def test_server_plan_is_durable_replayable_and_idempotent(plan_api):
    from app.break_even_plan_submission import BreakEvenPlanInput
    app, service, body, _ = plan_api
    before = counts(service)
    status, accepted = post(app, body)
    assert status == 202 and accepted['registration_status'] == 'pinned_user_grid_intent'
    assert accepted['trial_count'] == 2 and accepted['intent_job']['state'] == 'queued'
    assert counts(service) == (before[0]+1, before[1], before[2])
    assert post(app, body) == (status, accepted)
    with service.jobs.connect() as conn:
        row = conn.execute(sql.SQL('SELECT * FROM {} WHERE job_id=%s')
            .format(service.jobs._table('jobs')), (accepted['intent_job']['job_id'],)).fetchone()
    raw = service.jobs._verified_input(row)
    value = BreakEvenPlanInput.model_validate_json(raw)
    assert raw == canonical_input_bytes(value.model_dump(mode='json'))
    assert value.plan.tenant_id == 'tenant-1' and [ref.value for ref in value.plan.trials] == ['20', '32']
    assert sha256(canonical_input_bytes(value.plan.model_dump(mode='json'))).hexdigest() == accepted['plan_sha256']
    result = BreakEvenService(_ProposedPlanRepository(service.store._source, value.plan)).scan(value.request, 'tenant-1')
    assert result.status == 'bracket_only' and result.assessment_status == 'hold'
    assert service.store.get_break_even_read('tenant-1', accepted['plan_id']) is None
    assert 'tenant_id' not in accepted and 'trials' not in accepted and 'result' not in accepted


def test_scope_shape_and_pin_rejection_create_no_intent(plan_api):
    from app.break_even_plan_submission import PLAN_SUBMISSION_SCOPES
    app, service, body, principal = plan_api
    before = counts(service)
    for scope in PLAN_SUBMISSION_SCOPES:
        principal['scopes'].remove(scope)
        assert post(app, body)[0] == 403
        principal['scopes'].add(scope)
    for changes in ({'tenant_id': 'foreign'}, {'plan': {}}, {'idempotency_key': 'ignored'}, {'trials': []}):
        assert post(app, body | changes)[0] == 422
    changed = deepcopy(body)
    changed['request']['plan_id'] = 'a'*201
    assert post(app, changed)[0] == 422
    for fault in ('hash', 'repeat', 'order', 'range'):
        changed = deepcopy(body)
        if fault == 'hash': changed['trials'][0]['scenario_sha256'] = 'a'*64
        if fault == 'repeat': changed['trials'][1] = changed['trials'][0]
        if fault == 'order': changed['trials'].reverse()
        if fault == 'range': changed['request']['step'] = '0'
        assert post(app, changed)[0] == 422
    assert post(app, body, raw=b' '*65537)[0] == 413
    principal['tenant_id'] = 'tenant-2'
    assert post(app, body)[0] == 422
    principal['tenant_id'] = 'tenant-1'
    assert counts(service) == before


def test_plan_id_conflict_does_not_replace_immutable_intent(plan_api):
    app, service, body, _ = plan_api
    assert post(app, body)[0] == 202
    changed = deepcopy(body)
    changed['request']['target'] = 'operating_cash'
    before = counts(service)
    assert post(app, changed)[0] == 409 and counts(service) == before


@pytest.mark.parametrize('fault,status', [('scope', 403), ('source', 503), ('private', 503)])
def test_final_admission_guard_rolls_back(plan_api, monkeypatch, fault, status):
    app, service, body, principal = plan_api
    before = counts(service)
    original = service.jobs._event
    def change(*args, **kwargs):
        original(*args, **kwargs)
        if fault == 'scope': principal['scopes'].remove('break_even_write')
        if fault == 'source':
            view = service.store._source._source
            old = view._source
            view._source = MarketSourceStore(old.dsn, old.schema,
                runtime_identity=old.runtime_identity, principal_provider=old._principal_provider)
        if fault == 'private': raise RuntimeError('private plan detail')
    monkeypatch.setattr(service.jobs, '_event', change)
    code, response = post(app, body)
    assert code == status and 'private' not in str(response) and counts(service) == before


def test_source_rebinding_during_preparation_creates_no_intent(plan_api, monkeypatch):
    app, service, body, _ = plan_api
    before = counts(service)
    view = service.store._source._source
    old = view._source
    original = old.get_joint_shock
    def rebind(*args):
        value = original(*args)
        view._source = MarketSourceStore(old.dsn, old.schema,
            runtime_identity=old.runtime_identity, principal_provider=old._principal_provider)
        return value
    monkeypatch.setattr(old, 'get_joint_shock', rebind)
    assert post(app, body)[0] == 503 and counts(service) == before


def test_fresh_bearer_runtime_admits_actual_plan(plan_api, tls_files):
    from datetime import datetime, timezone, timedelta
    from app.api_runtime import ApiRuntime
    from app.http_identity import BearerRegistry, BearerGrant, token_digest, current_principal
    from app.break_even_plan_submission import PLAN_SUBMISSION_SCOPES
    from test_api_runtime import config, dependencies
    _, service, body, _ = plan_api
    jobs = service.jobs
    token = b'synthetic-break-even-plan-token-'+b'p'*32
    now = datetime.now(timezone.utc)
    registry = BearerRegistry((BearerGrant(token_digest(token), 'tenant-1', frozenset(PLAN_SUBMISSION_SCOPES),
        now-timedelta(seconds=1), now+timedelta(minutes=30)),))
    cert, key, _ = tls_files
    factory = lambda *, principal_provider: MarketSourceStore(jobs._dsn, jobs.schema,
        principal_provider=principal_provider, runtime_identity=jobs.runtime_identity)
    runtime = ApiRuntime(config(policy=jobs.runtime_identity[0], dsn=jobs._dsn,
        artifact_root=jobs.artifact_root, certificate=cert, private_key=key),
        dependencies(bearer_registry=registry, market_source_factory=factory,
            market_scope_resolver=service.store._source._source._holds._scope_resolver))
    status, accepted, headers = asyncio.run(request(runtime.service.app,
        path='/v1/break-even-plans', method='POST', body=json.dumps(body).encode(),
        headers=[(b'authorization', b'Bearer '+token), (b'content-type', b'application/json'),
                 (b'x-tenant-id', b'foreign')]))
    assert status == 202 and accepted['intent_job']['state'] == 'queued'
    assert accepted['trial_count'] == 2 and headers[b'cache-control'] == b'no-store'
    assert current_principal() is None
