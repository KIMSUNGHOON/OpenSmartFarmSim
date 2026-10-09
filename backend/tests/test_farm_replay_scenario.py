"""Joined registration over actual SCRAM; no CLI, source or farm claim."""

import asyncio
from hashlib import sha256
import json
from pathlib import Path
import sys
from urllib.parse import urlsplit

import pytest
from psycopg import sql

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from app.farm_replay_scenario import (FarmReplayScenarioService, FarmReplayScenarioRequest,
    FarmReplayScenarioHold, READ_SCOPES, WRITE_SCOPES)
from app.api_economic_scenario import EconomicScenarioRequest
from app.jobs import canonical_input_bytes
from app.orchestration import LocationResearchService, LocationRequest
from app.research_registry import ResearchRegistry
from app.thermal_scenario_store import ThermalScenarioStore
from app.owned_fixture_registry import OwnedFixtureRegistry
from app.owned_research import OwnedResearchService, ADMISSION_SCOPES as OWNED_SCOPES
from app.api import create_app
from test_http_identity import request as http_request
from test_api_job_status import UnusedMarketResultStore
from test_api_economic_scenario import economic_api
from test_thermal_publisher import input_raws
from login_database import login_database, login_scope

pytestmark = pytest.mark.parametrize('login_scope', [{'market_calculation':True,
    'market_source_storage':True, 'thermal_scenario_storage':True, 'break_even_calculation':True}], indirect=True)


@pytest.fixture
def farm_setup(login_scope, monkeypatch):
    import test_market_signed_hold_integration as seed
    monkeypatch.setattr(seed, 'SNAPSHOT_RAWS', input_raws())
    _, jobs, candidates, principal, economic, request = economic_api.__wrapped__(login_scope)
    principal['scopes'].update(set(WRITE_SCOPES) | {'location_create', 'thermal_scenario_write'})
    holds = candidates._source._holds
    runs = holds._context_store
    weather = json.loads(input_raws()[1])
    location = dict(latitude=35.0, longitude=127.0, period_start_utc=weather['start_utc'],
        period_end_utc=weather['end_utc'], goal_id='historical-thermal-replay', idempotency_key='farm-location')
    registration = {'tenant_id':'tenant-1', 'point':{'latitude':35.0,'longitude':127.0},
        **{key:location[key] for key in ('period_start_utc','period_end_utc','goal_id')},
        'provider_ids':[OwnedFixtureRegistry(Path(__file__).resolve().parents[2]).provider_id]}
    raw = canonical_input_bytes({'registry_version':'research-registry-v1','registrations':[registration]})
    registry = ResearchRegistry(raw, sha256(raw).hexdigest())
    _, _, research = LocationResearchService(jobs, registry.scope_for_location).submit(
        'tenant-1', LocationRequest.model_validate(location))
    hold = holds.get_market_hold_report(request['market_context']['hold_report_id'])
    thermal = ThermalScenarioStore(runs, holds)
    selected = thermal.put('tenant-1', {'schema_version':'thermal-scenario-v1','scenario_id':'thermal-one',
        'scenario_revision':'r1','tenant_id':'tenant-1','snapshot_id':hold['snapshot_id'],
        'decision_context_id':hold['decision_context_id'],'market_context':request['market_context'],
        'zone_id':'fixture-zone','goal_id':'historical-thermal-replay','model_version':'thermal-v1',
        'parameter_set_version':'synthetic-thermal-parameters-v1','origin':'user','evidence_level':'assumed'})
    registered = economic.submit('tenant-1', EconomicScenarioRequest.model_validate_json(
        canonical_input_bytes({'request':request,'idempotency_key':'farm-economics'})))
    body = {'schema_version':'farm-replay-scenario-v1','scenario_id':'farm-one','scenario_revision':'r1',
        'research_job_id':str(research['job_id']),
        'thermal':{'scenario_id':'thermal-one','revision':'r1','sha256':selected['scenario_sha256']},
        'economic':{'scenario_id':registered.scenario_id,'revision':registered.scenario_revision,
            'sha256':registered.scenario_sha256,'candidate_id':registered.candidate_id},
        'decision_at':request['decision_at'],'market_context':request['market_context'],
        'goal_id':'historical-thermal-replay','origin':'user','evidence_level':'assumed'}
    service = FarmReplayScenarioService(jobs, thermal, candidates, registry)
    return service, body, principal


def model(body):
    return FarmReplayScenarioRequest.model_validate_json(canonical_input_bytes(body))


def count(service):
    with service.jobs.connect() as conn:
        return conn.execute(sql.SQL('SELECT count(*) AS n FROM {}').format(service.jobs._table('jobs'))).fetchone()['n']


def test_joined_version_survives_fresh_service_and_identical_retry(farm_setup):
    service, body, _ = farm_setup
    before = count(service)
    first = service.submit('tenant-1', model(body))
    assert first.registration_status == 'registered_intent' and first.intent_job.state == 'queued'
    assert first.intent_job.attempt_count == 0 and count(service) == before+1
    assert service.submit('tenant-1', model(body)) == first
    fresh = FarmReplayScenarioService(service.jobs, service.thermal, service.candidates, service.registry)
    assert fresh.get('tenant-1', 'farm-one', 'r1') == first
    with service.jobs.connect() as conn:
        row = service.jobs._locked_job(conn, 'tenant-1', first.intent_job.job_id)
    raw = row['input_bytes']
    value = json.loads(raw)
    assert sha256(raw).hexdigest() == first.scenario_sha256
    assert value['request'] == body and value['tenant_id'] == 'tenant-1'
    assert value['bindings']['point'] == {'latitude':35.0,'longitude':127.0}
    assert value['bindings']['spatial_support'] == 'pending_research'
    assert value['bindings']['thermal_pins'] and value['bindings']['economic_candidate_id']
    assert service.jobs.get_publication('tenant-1', first.intent_job.job_id) is None
    from app.job_store import JobIntentConflict
    with pytest.raises(JobIntentConflict):
        service.submit('tenant-1', model(body | {'origin':'user', 'research_job_id':body['research_job_id'],
            'thermal':body['thermal'] | {'sha256':'a'*64}}))
    assert service.get('tenant-other', 'farm-one', 'r1') is None


def test_clock_market_hash_and_root_scope_mismatches_never_admit(farm_setup):
    service, body, _ = farm_setup
    before = count(service)
    changes = [{'decision_at':'2026-09-27T00:00:00Z'},
        {'thermal':body['thermal'] | {'sha256':'a'*64}},
        {'economic':body['economic'] | {'candidate_id':'b'*64}},
        {'market_context':{'kind':'unavailable','hold_report_id':'market-hold-v1:'+'c'*64}}]
    for change in changes:
        with pytest.raises(FarmReplayScenarioHold): service.submit('tenant-1', model(body | change))
    assert count(service) == before
    with service.jobs.connect() as conn:
        original = service.jobs._locked_job(conn, 'tenant-1', body['research_job_id'])
    forged = json.loads(original['input_bytes'])
    forged['point']['latitude'] = 36.0
    job = service.jobs.submit('tenant-1', 'research', forged, 'unregistered-root')
    with pytest.raises(FarmReplayScenarioHold):
        service.submit('tenant-1', model(body | {'research_job_id':str(job['job_id'])}))


def test_current_scopes_rights_and_late_revocation_fail_closed(farm_setup, monkeypatch):
    service, body, principal = farm_setup
    service.submit('tenant-1', model(body))
    for scope in READ_SCOPES:
        principal['scopes'].remove(scope)
        with pytest.raises(PermissionError): service.get('tenant-1', 'farm-one', 'r1')
        principal['scopes'].add(scope)
    original = service._references
    calls = 0
    def revoke(*args):
        nonlocal calls
        result = original(*args)
        calls += 1
        if calls == 2: principal['scopes'].remove('farm_scenario_write')
        return result
    before = count(service)
    monkeypatch.setattr(service, '_references', revoke)
    with pytest.raises(PermissionError): service.submit('tenant-1', model(body | {'scenario_revision':'r2'}))
    principal['scopes'].add('farm_scenario_write')
    assert count(service) == before
    monkeypatch.setattr(service, '_references', original)
    monkeypatch.setattr(service.candidates._source._source, 'get_input_rights', lambda *_:None)
    with pytest.raises(FarmReplayScenarioHold): service.get('tenant-1', 'farm-one', 'r1')


def test_signed_owned_research_context_is_bound_to_the_joint_selection(farm_setup, monkeypatch):
    service, body, principal = farm_setup
    principal['scopes'].update(OWNED_SCOPES)
    owned = OwnedResearchService(service.jobs, service.thermal.runs, service.registry,
        OwnedFixtureRegistry(Path(__file__).resolve().parents[2]),
        {next(iter(service.registry._scopes)):'context-1'})
    with service.jobs.connect() as conn:
        root = service.jobs._locked_job(conn, 'tenant-1', body['research_job_id'])
    value = json.loads(root['input_bytes'])
    location = LocationRequest.model_validate({**value['point'],
        **{key:value[key] for key in ('period_start_utc','period_end_utc','goal_id')},'idempotency_key':'owned-root'})
    _, _, actual = owned.submit('tenant-1', location)
    body = body | {'research_job_id':str(actual['job_id'])}
    linked = FarmReplayScenarioService(service.jobs, service.thermal, service.candidates, service.registry, owned)
    accepted = linked.submit('tenant-1', model(body))
    assert accepted.registration_status == 'registered_intent'
    assert linked.get('tenant-1', 'farm-one', 'r1') == accepted
    monkeypatch.setattr(owned, 'authority_snapshot', lambda *_:None)
    with pytest.raises(FarmReplayScenarioHold): linked.get('tenant-1', 'farm-one', 'r1')


def application(service):
    return create_app(service.jobs, service.thermal.holds, service.thermal.runs, UnusedMarketResultStore(),
        principal_provider=service.jobs.principal_provider, thermal_scenario_store=service.thermal,
        farm_scenario_service=service)


def call(app, body=None, *, raw=None, path='/v1/farm-scenarios', media=b'application/json'):
    target = urlsplit(path)
    return asyncio.run(http_request(app,path=target.path,query=target.query.encode(),
        method='POST' if body is not None or raw is not None else 'GET',
        headers=[(b'content-type',media),(b'x-tenant-id',b'foreign')],
        body=json.dumps(body).encode() if raw is None else raw))[:2]


def test_http_contract_scopes_transport_conflict_and_current_read(farm_setup):
    service, body, principal = farm_setup
    app = application(service)
    before = count(service)
    for scope in WRITE_SCOPES:
        principal['scopes'].remove(scope)
        assert call(app,raw=b'{')[0] == 403
        principal['scopes'].add(scope)
    principal['authenticated'] = False
    assert call(app,raw=b'{')[0] == 401
    principal['authenticated'] = True
    for change in ({'tenant_id':'foreign'}, {'decision_at':'2026-09-28T00:00:00'},
                   {'physical_parameters':{}}, {'market_context':{'kind':'available','snapshot_id':'fake-g0'}}):
        assert call(app,body | change)[0] == 422
    assert call(app,raw=b'{"scenario_id":"a","scenario_id":"b"}')[0] == 422
    assert call(app,raw=b'{"unexpected":NaN}')[0] == 422
    assert call(app,raw=b' '*4097)[0] == 413
    assert call(app,body,media=b'text/plain')[0] == 415
    assert count(service) == before
    status, accepted = call(app,body)
    assert status == 200 and set(accepted) == {'scenario_id','scenario_revision','scenario_sha256',
        'registration_status','intent_job'}
    assert call(app,body) == (200,accepted)
    assert call(app,body | {'thermal':body['thermal'] | {'sha256':'b'*64}})[0] == 409
    assert call(app,path='/v1/farm-scenarios?scenario_id=farm-one&scenario_revision=r1') == (200,accepted)
    assert call(app,path='/v1/farm-scenarios?scenario_id=missing&scenario_revision=r1')[0] == 404
    assert call(app,path='/v1/farm-scenarios?scenario_id=&scenario_revision=r1')[0] == 422
    assert count(service) == before+1
    schema = app.openapi()['paths']['/v1/farm-scenarios']
    request = schema['post']['requestBody']['content']['application/json']['schema']
    assert request['additionalProperties'] is False and '$defs' not in request
    assert request['properties']['thermal']['additionalProperties'] is False
    assert schema['get']['x-ossf-required-scopes'] == list(READ_SCOPES)
    unconfigured = create_app(service.jobs, service.thermal.holds, service.thermal.runs, UnusedMarketResultStore(),
        principal_provider=service.jobs.principal_provider)
    assert call(unconfigured,body)[0] == 503
