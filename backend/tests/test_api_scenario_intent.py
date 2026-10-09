"""Actual scenario registration/read contracts; source keys/captures are synthetic."""

import asyncio
import json
from pathlib import Path
import sys
from urllib.parse import urlencode

import pytest
from psycopg import sql

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from app.api import create_app
from test_thermal_scenario_store import scenario_setup, simulation_setup, login_database, login_scope
from test_api_job_status import UnusedMarketResultStore
from test_api_thermal_run import UnusedMarketHoldStore
from test_http_identity import request
from test_api_run_submission import submission, bound_execution, post as run_post

pytestmark = pytest.mark.parametrize('login_scope', [{'thermal_scenario_storage': True,
    'market_calculation': True, 'break_even_calculation': True}], indirect=True)


@pytest.fixture
def scenario_api(scenario_setup):
    store, runs, holds, value, principal, base = scenario_setup
    from app.job_store import JobStore
    jobs = JobStore(runs.dsn, runs.schema, base.artifact_root,
        runtime_identity=runs.runtime_identity, principal_provider=runs._principal_provider,
        audit_runtime_grants=True)
    app = create_app(jobs, holds, runs, UnusedMarketResultStore(),
        principal_provider=lambda: principal, thermal_scenario_store=store)
    return app, {key: item for key, item in value.items() if key != 'tenant_id'}, scenario_setup


def post(app, body, *, raw=None, media=b'application/json'):
    return asyncio.run(request(app, path='/v1/scenarios', method='POST',
        headers=[(b'content-type', media), (b'x-tenant-id', b'foreign-tenant')],
        body=json.dumps(body).encode() if raw is None else raw))[:2]


def read(app, body, **changes):
    query = urlencode({key: (body | changes)[key] for key in ('scenario_id', 'scenario_revision')}).encode()
    return asyncio.run(request(app, path='/v1/scenarios', query=query,
        headers=[(b'x-tenant-id', b'foreign-tenant')]))[:2]


def count(setup):
    _, runs, _, _, _, base = setup
    with base.connect() as conn:
        return conn.execute(sql.SQL('SELECT count(*) AS n FROM {}.thermal_scenarios')
            .format(sql.Identifier(runs.schema))).fetchone()['n']


def test_registered_version_is_replayable_and_safe_to_bind(scenario_api):
    app, body, setup = scenario_api
    status, registered = post(app, body)
    assert status == 200 and registered['status'] == 'registered_intent'
    actual = setup[0].get('tenant-a', body['scenario_id'], body['scenario_revision'])
    assert registered['scenario_sha256'] == actual['scenario_sha256']
    assert registered['scenario_id'] == body['scenario_id']
    assert registered['scenario_revision'] == body['scenario_revision']
    assert set(registered) == {'scenario_id', 'scenario_revision', 'scenario_sha256', 'status', 'recorded_at'}
    assert post(app, body) == (200, registered) and read(app, body) == (200, registered)
    assert count(setup) == 1 and 'pins' not in registered and 'tenant_id' not in registered
    assert post(app, body | {'zone_id': 'changed'})[0] == 409 and count(setup) == 1
    status, revised = post(app, body | {'scenario_revision': 'r2', 'zone_id': 'changed'})
    assert status == 200 and revised['scenario_sha256'] != registered['scenario_sha256']
    assert read(app, body) == (200, registered) and count(setup) == 2


@pytest.mark.parametrize('change', [{'tenant_id': 'foreign-tenant'}, {'coefficients': {'heat': 4}},
    {'model_version': 'invented'}, {'origin': 'provider'}, {'scenario_revision': ''},
    {'market_context': {'kind': 'available', 'snapshot_id': 'fake-g0'}}])
def test_closed_request_never_inserts_bad_intent(scenario_api, change):
    app, body, setup = scenario_api
    assert post(app, body | change)[0] == 422 and count(setup) == 0


@pytest.mark.parametrize('scope', ['thermal_scenario_write', 'thermal_scenario_read',
    'thermal_snapshot_read', 'decision_context_read', 'market_hold_context_read'])
def test_registration_requires_each_current_scope(scenario_api, scope):
    app, body, setup = scenario_api
    setup[4]['scopes'].remove(scope)
    assert post(app, body)[0] == 403 and count(setup) == 0


@pytest.mark.parametrize('scope', ['thermal_scenario_read', 'thermal_snapshot_read',
    'decision_context_read', 'market_hold_context_read'])
def test_reads_require_each_reference_scope(scenario_api, scope):
    app, body, setup = scenario_api
    assert post(app, body)[0] == 200
    setup[4]['scopes'].remove(scope)
    assert read(app, body)[0] == 403


def test_wrong_tenant_or_unknown_version_is_not_found(scenario_api):
    app, body, setup = scenario_api
    assert post(app, body)[0] == 200
    assert read(app, body, scenario_revision='unknown')[0] == 404
    setup[4]['tenant_id'] = 'foreign-tenant'
    assert read(app, body)[0] == 404


def test_actual_missing_reference_and_store_errors_are_fixed(scenario_api, monkeypatch):
    app, body, setup = scenario_api
    status, result = post(app, body | {'decision_context_id': 'unknown'})
    assert status == 422 and count(setup) == 0 and 'unknown' not in json.dumps(result)
    def fail(*_):
        raise RuntimeError('private credential and source data')
    monkeypatch.setattr(setup[0], 'put', fail)
    status, result = post(app, body)
    assert status == 503 and 'private' not in json.dumps(result)


def test_scope_revoked_inside_registration_rolls_back(scenario_api, monkeypatch):
    app, body, setup = scenario_api
    store, _, _, _, principal, _ = setup
    original = store._record
    def revoke(row):
        value = original(row)
        principal['scopes'].remove('thermal_scenario_write')
        return value
    monkeypatch.setattr(store, '_record', revoke)
    assert post(app, body)[0] == 403 and count(setup) == 0


def test_query_ids_preserve_slash_and_colon_without_path_reinterpretation(scenario_api):
    app, body, _ = scenario_api
    body = body | {'scenario_id': 'scope/fixture:scenario', 'scenario_revision': 'versions/r:2'}
    status, registered = post(app, body)
    assert status == 200 and read(app, body) == (200, registered)


def test_http_registered_hash_binds_to_http_execution_and_result(submission):
    app, run_body, _, setup = submission
    worker, store, _, _, _, _, _, _ = setup
    original = store.get('tenant-a', run_body['scenario_id'], run_body['scenario_revision'])['scenario']
    body = original.model_dump(mode='json', exclude={'tenant_id'}) | {'scenario_id': 'http-linked-scenario'}
    status, registered = post(app, body)
    assert status == 200
    run_body |= {key: registered[key] for key in ('scenario_id', 'scenario_revision', 'scenario_sha256')}
    status, queued = run_post(app, run_body)
    assert status == 202
    result = worker.run_once(queued['job_id'])
    assert result.state == 'succeeded'
    status, summary, _ = asyncio.run(request(app, path=f"/v1/jobs/{queued['job_id']}/run", headers=[]))
    assert status == 200 and summary['run_id'] == result.run_id
    assert read(app, body) == (200, registered)


@pytest.mark.parametrize('raw,media,status', [(b'{}', b'text/plain', 415),
    (b' '*4097, b'application/json', 413), (b'{"x":1,"x":2}', b'application/json', 422),
    (b'{"x":NaN}', b'application/json', 422), (b'\xff', b'application/json', 422)])
def test_bounded_transport_does_not_insert(scenario_api, raw, media, status):
    app, body, setup = scenario_api
    assert post(app, body, raw=raw, media=media)[0] == status and count(setup) == 0
