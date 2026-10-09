"""Exact source/economic HTTP selection over real TLS, Bearer and SCRAM."""

import asyncio
from datetime import datetime, timedelta, timezone
import http.client
import json
from pathlib import Path
import ssl
import sys
import threading
import time
from urllib.parse import urlencode, urlsplit
from uuid import uuid4

import pytest
from jsonschema import Draft202012Validator

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from app.api import create_app
from app.api_openapi import contract_document
from app.api_runtime import ApiRuntime
from app.farm_economic_candidate_selection import (FarmEconomicCandidateService,
    FarmEconomicCandidateHold, READ_SCOPES)
from app.http_identity import BearerGrant, BearerRegistry, current_principal, token_digest
from app.market_source_store import MarketSourceStore
from test_api_job_status import UnusedMarketResultStore
from test_api_runtime import config, dependencies
from test_api_serve import tls_files
from test_farm_economic_candidate_selection import (candidate_selection, authoring, farm_setup,
    login_scope, login_database, counts, new_candidate, PROFILE)
from test_http_identity import request
from test_market_hold_store import context_verifier


PATH = '/v1/source-history/{research_job_id}/collections/{collection_job_id}/economic-candidates'


def paths(root, child, candidate):
    base = PATH.format(research_job_id=root, collection_job_id=child)
    return base, base + '/' + candidate


@pytest.mark.parametrize('login_scope', [PROFILE], indirect=True)
def test_candidate_http_errors_and_cursors_are_closed(candidate_selection, monkeypatch):
    service, root, child, body, principal, _ = candidate_selection
    source, jobs = service.source, service.economic.jobs
    def app_for(with_economic):
        return create_app(jobs, service.economic.candidates._source._holds, source.research.runs,
            UnusedMarketResultStore(), principal_provider=jobs.principal_provider,
            location_research_service=source.research, collection_service=source.collection,
            economic_scenario_service=service.economic if with_economic else None)
    listing, selected = paths(root, child, body['farm']['economic']['candidate_id'])
    def get(app, where):
        target = urlsplit(where)
        return asyncio.run(request(app, path=target.path, query=target.query.encode(), method='GET'))[:2]
    assert get(app_for(False), listing)[0] == get(app_for(False), selected)[0] == 503
    app = app_for(True)
    before = counts(service)
    expected = service.get('tenant-1', root, child, body['farm']['economic']['candidate_id']).model_dump(mode='json')
    assert get(app, selected) == (200, expected)
    assert get(app, listing)[1]['verification'] == 'requires_current_selection'
    assert get(app, PATH.format(research_job_id=uuid4(), collection_job_id=child))[0] == 404
    assert get(app, listing + '/' + '0' * 64)[0] == 404
    for query in ({'limit': 0}, {'limit': 51}, {'before_candidate_id': 'a' * 64},
            {'before_candidate_id': 'a' * 64, 'before_recorded_at': '2026-10-01T00:00:00'},
            {'before_candidate_id': 'a' * 64, 'before_recorded_at': '2026-10-01T00:00:00+09:00'},
            {'before_candidate_id': 'invalid', 'before_recorded_at': '2026-10-01T00:00:00Z'}):
        status, error = get(app, listing + '?' + urlencode(query))
        assert status == 422 and error['error']['code'] == 'invalid_request'
    assert get(app, listing + '/' + 'A' * 64)[0] == 422
    principal['authenticated'] = False
    assert get(app, listing)[0] == get(app, selected)[0] == 401
    principal['authenticated'] = True
    for method, path in (('list', listing), ('get', selected)):
        for error, status in ((PermissionError('private selection detail'), 403),
                (FarmEconomicCandidateHold('private held detail'), 422),
                (RuntimeError('private backend detail'), 503)):
            with monkeypatch.context() as patch:
                def fail(*_args, **_kwargs): raise error
                patch.setattr(FarmEconomicCandidateService, method, fail)
                actual, value = get(app, path)
                assert actual == status and set(value) == {'error'} and 'private' not in json.dumps(value)
    assert counts(service) == before


def test_candidate_openapi_has_closed_pins_and_distinct_verification():
    document = contract_document()
    for path, operation_id, schema_name in ((PATH, 'listSourceEconomicCandidates', 'FarmEconomicCandidatePage'),
            (PATH + '/{candidate_id}', 'getSourceEconomicCandidate', 'FarmEconomicSelection')):
        operation = document['paths'][path]['get']
        assert operation['operationId'] == operation_id
        assert operation['x-ossf-required-scopes'] == list(READ_SCOPES)
        assert operation['responses']['200']['content']['application/json']['schema'] == {
            '$ref': '#/components/schemas/' + schema_name}
        schema = document['components']['schemas'][schema_name]
        Draft202012Validator.check_schema(schema)
        assert schema['additionalProperties'] is False
        assert set(schema['properties']) == set(schema['required'])
    for name, marker in (('FarmEconomicCandidatePage', 'requires_current_selection'),
            ('FarmEconomicSelection', 'requires_registration_recheck')):
        assert document['components']['schemas'][name]['properties']['verification']['const'] == marker
    assert document['components']['schemas']['FarmEconomicCandidatePage']['properties']['items']['maxItems'] == 50
    assert document['components']['schemas']['SourceFarmSelection']['properties']['g1_status']['const'] == 'not_accepted'


@pytest.mark.parametrize('login_scope', [PROFILE], indirect=True)
def test_standard_https_reads_pages_and_current_selection_without_writes(candidate_selection, tls_files, monkeypatch):
    service, root, child, body, _, _ = candidate_selection
    new_candidate(service, body, 'https-r2')
    before = counts(service)
    candidate = body['farm']['economic']['candidate_id']
    expected = service.get('tenant-1', root, child, candidate).model_dump(mode='json')
    source, jobs = service.source, service.economic.jobs
    research, holds = source.research, service.economic.candidates._source._holds
    cert, key, _ = tls_files
    now = datetime.now(timezone.utc)
    allowed = set(READ_SCOPES)
    subjects = [('owner', 'tenant-1', allowed), ('foreign', 'other-tenant', allowed)]
    subjects.extend(('denied-' + scope, 'tenant-1', allowed - {scope}) for scope in READ_SCOPES)
    tokens = {name: ('synthetic-source-economic-' + name + '-' + 'e' * 32).encode()
        for name, _, _ in subjects}
    grants = tuple(BearerGrant(token_digest(tokens[name]), tenant, frozenset(scopes),
        now - timedelta(seconds=1), now + timedelta(minutes=20)) for name, tenant, scopes in subjects)
    source_factory = lambda *, principal_provider: MarketSourceStore(jobs._dsn, jobs.schema,
        principal_provider=principal_provider, runtime_identity=jobs.runtime_identity)
    runtime = ApiRuntime(config(policy=jobs.runtime_identity[0], dsn=jobs._dsn,
        artifact_root=jobs.artifact_root, certificate=cert, private_key=key, port=0),
        dependencies(research_registry=research.catalog, bearer_registry=BearerRegistry(grants),
            owned_fixture_registry=research.registry, owned_research_contexts=dict(research._contexts),
            context_verifier=context_verifier, market_scope_resolver=holds._scope_resolver,
            market_source_factory=source_factory))
    assert runtime.collections.jobs is runtime.research.store is runtime.jobs
    assert runtime.market_candidates._source._holds._context_store is runtime.thermal
    server = runtime.service.server()
    thread = threading.Thread(target=server.run, daemon=True)
    thread.start()
    timings = []
    listing, selected = paths(root, child, candidate)
    try:
        deadline = time.monotonic() + 15
        while not server.started:
            assert thread.is_alive() and time.monotonic() < deadline
            time.sleep(0.01)
        port = server.servers[0].sockets[0].getsockname()[1]
        trust = ssl.create_default_context(cafile=str(cert))
        def call(path, bearer='owner'):
            conn = http.client.HTTPSConnection('127.0.0.1', port, timeout=30, context=trust)
            try:
                headers = {} if bearer is None else {'Authorization': 'Bearer ' + tokens[bearer].decode()}
                started = time.monotonic()
                conn.request('GET', path, headers=headers)
                response = conn.getresponse()
                value = json.loads(response.read())
                timings.append(time.monotonic() - started)
                assert response.getheader('cache-control') == 'no-store'
                return response.status, value
            finally:
                conn.close()
        assert call(listing, None)[0] == 401
        for scope in READ_SCOPES:
            assert call(listing, 'denied-' + scope)[0] == 403
        assert call(listing, 'foreign')[0] == call(selected, 'foreign')[0] == 404
        assert call(PATH.format(research_job_id=uuid4(), collection_job_id=child))[0] == 404
        first_status, first = call(listing + '?limit=1')
        assert first_status == 200 and first['verification'] == 'requires_current_selection'
        cursor = first['next_cursor']
        assert cursor is not None
        next_status, next_page = call(listing + '?' + urlencode({'limit': 1,
            'before_recorded_at': cursor['recorded_at'], 'before_candidate_id': cursor['candidate_id']}))
        assert next_status == 200 and next_page['next_cursor'] is None
        assert {first['items'][0]['economic']['candidate_id'], next_page['items'][0]['economic']['candidate_id']} == {
            item.economic.candidate_id for item in service.list('tenant-1', root, child).items}
        assert call(selected) == call(selected) == (200, expected)
        with monkeypatch.context() as patch:
            patch.setattr(runtime.market_candidates._source._source, 'get_input_rights', lambda *_: None)
            assert call(listing)[0] == 200
            status, held = call(selected)
            assert status == 422 and held['error']['code'] == 'source_economic_hold'
        assert call(selected) == (200, expected)
        assert call(listing + '?limit=51')[0] == 422
        assert len(timings) == 20 and max(timings) < 30
        assert counts(service) == before and current_principal() is None
        print('source_economic_https=' + json.dumps({'responses': len(timings),
            'max_full_response_seconds': round(max(timings), 3), 'client_timeout_seconds': 30,
            'write_scopes': 0, 'cli': 'synthetic_test_executable'}))
    finally:
        server.should_exit = True
        thread.join(timeout=15)
        assert not thread.is_alive()
