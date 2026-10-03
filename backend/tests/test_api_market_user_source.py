"""Actual atomic user-source intake; fixtures grant no external data/economic gate."""

import asyncio
from hashlib import sha256
import json
import os
from pathlib import Path
import sys

import pytest
from psycopg import sql

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from app.api import create_app
from app.job_store import JobStore
from app.jobs import canonical_input_bytes
from app.market_source_store import MarketSourceStore
from test_market_source_store import record_items, PROFILE, login_database, login_scope
from test_market_scenario import case
from test_economics import base, opening_lot, TrustedTestRepository
from app.economic_contracts import EconomicScenario
from test_api_job_status import UnusedThermalRunStore, UnusedMarketResultStore
from test_api_thermal_run import UnusedMarketHoldStore
from test_http_identity import request
from test_api_serve import tls_files
from test_api_economic_scenario import economic_api

pytestmark = pytest.mark.parametrize('login_scope', [{**PROFILE, 'break_even_calculation': True}], indirect=True)


@pytest.fixture
def source_api(login_scope):
    from app.api_market_source import MarketUserSourceService
    base_store, policy, dsns = login_scope
    principal = {'authenticated': True, 'tenant_id': 'tenant-1',
        'scopes': {'market_source_read', 'market_source_write', 'metadata'}}
    provider = lambda: principal
    jobs = JobStore(dsns['authority'], policy.schema, base_store.artifact_root,
        runtime_identity=(policy, 'authority'), principal_provider=provider, audit_runtime_grants=True)
    sources = MarketSourceStore(dsns['authority'], policy.schema,
        principal_provider=provider, runtime_identity=(policy, 'authority'))
    service = MarketUserSourceService(jobs, sources)
    app = create_app(jobs, UnusedMarketHoldStore(), UnusedThermalRunStore(), UnusedMarketResultStore(),
        principal_provider=provider, market_user_source_service=service)
    source, _ = case()
    prior = TrustedTestRepository(EconomicScenario.model_validate(base(opening_inventory=(opening_lot(),))))
    source.prior_costs = prior.prior_costs
    values = {kind: model.model_dump(mode='json', exclude={'tenant_id'}) for kind, model in record_items(source)}
    return app, jobs, sources, principal, service, values


def post(app, body, *, raw=None):
    return asyncio.run(request(app, path='/v1/market-user-sources', method='POST',
        headers=[(b'content-type', b'application/json'), (b'x-tenant-id', b'foreign-tenant')],
        body=json.dumps(body).encode() if raw is None else raw))[:2]


def counts(jobs):
    with jobs.connect() as conn:
        return tuple(conn.execute(sql.SQL('SELECT count(*) AS n FROM {}')
            .format(jobs._table(name))).fetchone()['n'] for name in ('jobs', 'market_source_records'))


@pytest.mark.parametrize('kind', ['economic_scenario', 'economic_input', 'joint_shock',
    'input_rights', 'settlement_applicability', 'settlement_evidence', 'prior_batch_cost'])
def test_all_typed_sources_bind_actual_job_and_preserve_first_admission(source_api, kind):
    app, jobs, sources, _, _, values = source_api
    body = {'kind': kind, 'input': values[kind], 'idempotency_key': 'source-http'}
    status, registered = post(app, body)
    assert status == 200 and registered['admission_kind'] == 'contract_valid_user_assumption'
    assert registered['kind'] == kind and registered['intent_job']['state'] == 'queued'
    assert counts(jobs) == (1, 1) and post(app, body) == (200, registered)
    assert 'tenant_id' not in registered and 'input' not in registered
    with jobs.connect() as conn:
        row = conn.execute(sql.SQL('SELECT * FROM {}').format(jobs._table('market_source_records'))).fetchone()
        job = conn.execute(sql.SQL('SELECT * FROM {}').format(jobs._table('jobs'))).fetchone()
    assert row['payload_raw'] == job['input_bytes'] == canonical_input_bytes(values[kind] | {'tenant_id': 'tenant-1'})
    assert row['payload_sha256'] == registered['payload_sha256'] == sha256(row['payload_raw']).hexdigest()
    assert row['job_id'] == job['job_id'] and row['tenant_id'] == 'tenant-1'
    with jobs.connect() as conn:
        assert sources._verified(conn, row).model_dump(mode='json')['tenant_id'] == 'tenant-1'


@pytest.mark.parametrize('change', [{'tenant_id': 'foreign-tenant'}, {'origin': 'observed'},
    {'approved_g0': True}, {'value': 123}, {'value': 'NaN'}])
def test_invalid_numeric_source_never_creates_job_or_row(source_api, change):
    app, jobs, _, _, _, values = source_api
    body = {'kind': 'economic_input', 'input': values['economic_input'] | change, 'idempotency_key': 'bad-source'}
    assert post(app, body)[0] == 422 and counts(jobs) == (0, 0)


@pytest.mark.parametrize('scope', ['market_source_read', 'market_source_write', 'metadata'])
def test_intake_requires_each_scope_before_write(source_api, scope):
    app, jobs, _, principal, _, values = source_api
    principal['scopes'].remove(scope)
    assert post(app, {'kind': 'economic_input', 'input': values['economic_input'],
        'idempotency_key': 'scope'})[0] == 403 and counts(jobs) == (0, 0)


def test_source_scope_revoked_after_insert_rolls_back_both_objects(source_api, monkeypatch):
    app, jobs, sources, principal, _, values = source_api
    original = sources._verified
    def revoke(*args):
        value = original(*args)
        principal['scopes'].remove('market_source_write')
        return value
    monkeypatch.setattr(sources, '_verified', revoke)
    assert post(app, {'kind': 'economic_input', 'input': values['economic_input'],
        'idempotency_key': 'rollback'})[0] == 403 and counts(jobs) == (0, 0)


def test_source_version_conflict_rolls_back_new_intent_and_fixed_failure_hides_details(source_api, monkeypatch):
    app, jobs, sources, _, _, values = source_api
    body = {'kind': 'economic_input', 'input': values['economic_input'], 'idempotency_key': 'original'}
    assert post(app, body)[0] == 200
    assert post(app, body | {'input': values['economic_input'] | {'value': '999'},
        'idempotency_key': 'changed'})[0] == 409 and counts(jobs) == (1, 1)
    def fail(*_, **__):
        raise RuntimeError('private credentials and raw source')
    monkeypatch.setattr(sources, '_adopt_in_transaction', fail)
    status, result = post(app, body | {'idempotency_key': 'failure'})
    assert status == 503 and 'private' not in json.dumps(result) and counts(jobs) == (1, 1)


def test_store_rebinding_during_intake_rolls_back(source_api, monkeypatch):
    app, jobs, sources, _, service, values = source_api
    other = MarketSourceStore(sources.dsn, sources.schema,
        principal_provider=sources._principal_provider, runtime_identity=sources.runtime_identity)
    original = sources._verified
    def rebind(*args):
        value = original(*args)
        service.sources = other
        return value
    monkeypatch.setattr(sources, '_verified', rebind)
    assert post(app, {'kind': 'economic_input', 'input': values['economic_input'],
        'idempotency_key': 'rebind'})[0] == 503 and counts(jobs) == (0, 0)


def test_larger_input_transport_and_exact_overflow_do_not_change_payload(source_api):
    app, jobs, _, _, _, values = source_api
    body = {'kind': 'economic_input', 'input': values['economic_input'], 'idempotency_key': 'large'}
    raw = b' '*5000+json.dumps(body).encode()
    assert post(app, body, raw=raw)[0] == 200 and counts(jobs) == (1, 1)
    raw = json.dumps(body).encode()
    assert post(app, body, raw=raw+b' '*(65537-len(raw)))[0] == 413 and counts(jobs) == (1, 1)


def test_fresh_bearer_runtime_assembles_actual_source_intake(source_api, tls_files):
    from datetime import datetime, timezone, timedelta
    from app.api_runtime import ApiRuntime
    from app.http_identity import BearerRegistry, BearerGrant, token_digest, current_principal
    from app.api_market_source import SOURCE_SCOPES
    from test_api_runtime import config, dependencies
    _, jobs, sources, _, _, values = source_api
    os.close(jobs._content_directory(create=True))
    token = b'synthetic-user-source-token-'+b'u'*32
    now = datetime.now(timezone.utc)
    registry = BearerRegistry((BearerGrant(token_digest(token), 'tenant-1', frozenset(SOURCE_SCOPES),
        now-timedelta(seconds=1), now+timedelta(minutes=5)),))
    cert, key, _ = tls_files
    factory = lambda *, principal_provider: MarketSourceStore(jobs._dsn, jobs.schema,
        principal_provider=principal_provider, runtime_identity=jobs.runtime_identity)
    runtime = ApiRuntime(config(policy=jobs.runtime_identity[0], dsn=jobs._dsn,
        artifact_root=jobs.artifact_root, certificate=cert, private_key=key),
        dependencies(bearer_registry=registry, market_source_factory=factory))
    body = {'kind': 'economic_input', 'input': values['economic_input'], 'idempotency_key': 'bearer'}
    status, registered, headers = asyncio.run(request(runtime.service.app,
        path='/v1/market-user-sources', method='POST', body=json.dumps(body).encode(),
        headers=[(b'authorization', b'Bearer '+token), (b'content-type', b'application/json'),
            (b'x-tenant-id', b'foreign-tenant')]))
    assert status == 200 and registered['admission_kind'] == 'contract_valid_user_assumption'
    assert headers[b'cache-control'] == b'no-store' and current_principal() is None
    assert counts(jobs) == (1, 1)


def test_fresh_bearer_runtime_registers_actual_conditional_scenario(economic_api, tls_files):
    from datetime import datetime, timezone, timedelta
    from app.api_runtime import ApiRuntime
    from app.http_identity import BearerRegistry, BearerGrant, token_digest, current_principal
    from app.api_economic_scenario import ECONOMIC_SCENARIO_SCOPES
    from test_api_runtime import config, dependencies
    _, jobs, candidates, _, _, req = economic_api
    os.close(jobs._content_directory(create=True))
    token = b'synthetic-economic-scenario-token-'+b'e'*32
    now = datetime.now(timezone.utc)
    registry = BearerRegistry((BearerGrant(token_digest(token), 'tenant-1', frozenset(ECONOMIC_SCENARIO_SCOPES),
        now-timedelta(seconds=1), now+timedelta(minutes=5)),))
    cert, key, _ = tls_files
    factory = lambda *, principal_provider: MarketSourceStore(jobs._dsn, jobs.schema,
        principal_provider=principal_provider, runtime_identity=jobs.runtime_identity)
    runtime = ApiRuntime(config(policy=jobs.runtime_identity[0], dsn=jobs._dsn,
        artifact_root=jobs.artifact_root, certificate=cert, private_key=key),
        dependencies(bearer_registry=registry, market_source_factory=factory,
            market_scope_resolver=candidates._source._holds._scope_resolver))
    body = {'request': req, 'idempotency_key': 'economic-bearer'}
    status, registered, headers = asyncio.run(request(runtime.service.app,
        path='/v1/economic-scenarios', method='POST', body=json.dumps(body).encode(),
        headers=[(b'authorization', b'Bearer '+token), (b'content-type', b'application/json'),
            (b'x-tenant-id', b'foreign-tenant')]))
    assert status == 200 and registered['registration_status'] == 'pinned_user_assumption'
    assert registered['intent_job']['state'] == 'queued'
    assert headers[b'cache-control'] == b'no-store' and current_principal() is None
    assert candidates.get_market_candidate(registered['scenario_id'], registered['scenario_revision'])['candidate_id'] == registered['candidate_id']
