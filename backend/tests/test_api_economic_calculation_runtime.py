"""Actual production assembly profile and authenticated economic route checks."""

import asyncio
import json

import pytest
from psycopg import sql

from test_api_economic_calculation import calculation_api, calculation_setup
from test_economic_calculation_worker import economic_api, login_database, login_scope, PROFILE
from test_api_serve import tls_files
from test_http_identity import request

pytestmark = pytest.mark.parametrize('login_scope',
    [{**PROFILE, 'break_even_calculation': True}], indirect=True)


def test_fresh_bearer_runtime_and_database_grant_drift(calculation_api, tls_files, login_scope):
    from datetime import datetime, timezone, timedelta
    from app.api_runtime import ApiRuntime
    from app.http_identity import BearerRegistry, BearerGrant, token_digest, current_principal
    from app.economic_calculation_worker import CALCULATION_SCOPES
    from app.market_source_store import MarketSourceStore
    from test_api_runtime import config, dependencies
    _, service, worker, body, _ = calculation_api
    jobs = service.jobs
    token = b'synthetic-economic-calculation-token-'+b'c'*32
    now = datetime.now(timezone.utc)
    registry = BearerRegistry((BearerGrant(token_digest(token), 'tenant-1', frozenset(CALCULATION_SCOPES),
        now-timedelta(seconds=1), now+timedelta(minutes=30)),))
    cert, key, _ = tls_files
    factory = lambda *, principal_provider: MarketSourceStore(jobs._dsn, jobs.schema,
        principal_provider=principal_provider, runtime_identity=jobs.runtime_identity)
    runtime = ApiRuntime(config(policy=jobs.runtime_identity[0], dsn=jobs._dsn,
        artifact_root=jobs.artifact_root, certificate=cert, private_key=key),
        dependencies(bearer_registry=registry, market_source_factory=factory,
            market_scope_resolver=service.results._candidates._source._holds._scope_resolver))
    def call(path, method='GET', payload=b''):
        return asyncio.run(request(runtime.service.app, path=path, method=method, body=payload,
            headers=[(b'authorization', b'Bearer '+token), (b'content-type', b'application/json'),
                (b'x-tenant-id', b'foreign')]))
    status, accepted, headers = call('/v1/economic-results', 'POST', json.dumps(body).encode())
    assert status == 202 and headers[b'cache-control'] == b'no-store' and current_principal() is None
    assert worker.run_once(accepted['job_id']).state == 'succeeded'
    path = '/v1/jobs/'+accepted['job_id']+'/economic-result'
    status, result, headers = call(path)
    assert status == 200 and result['assessment_status'] == 'hold'
    assert headers[b'cache-control'] == b'no-store' and current_principal() is None
    assert asyncio.run(request(runtime.service.app, path=path))[0] == 401
    base, policy, _ = login_scope
    with base.connect() as conn:
        conn.execute(sql.SQL('GRANT SELECT ON {}.jobs TO {}')
            .format(sql.Identifier(policy.schema), sql.Identifier(policy.roles['worker'])))
    assert call(path)[0] == 503
