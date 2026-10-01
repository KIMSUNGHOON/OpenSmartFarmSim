"""Source reference HTTP contract with actual TLS/Bearer/SCRAM and fixture CLI."""

import asyncio
from datetime import datetime, timedelta, timezone
import http.client
import json
from pathlib import Path
import ssl
import sys
import threading
import time
from uuid import uuid4

import pytest
from jsonschema import Draft202012Validator

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from app.api import create_app
from app.api_openapi import contract_document
from app.api_runtime import ApiRuntime
from app.http_identity import BearerGrant, BearerRegistry, current_principal, token_digest
from app.market_source_store import MarketSourceStore
from app.source_farm_selection import READ_SCOPES, SourceFarmSelectionHold, SourceFarmSelectionService
from test_api_job_status import UnusedMarketHoldStore, UnusedMarketResultStore
from test_api_runtime import config, dependencies
from test_api_serve import tls_files
from test_http_identity import request
from test_source_farm_selection import (source_setup, research_setup, review_setup, collection_setup,
    login_scope, login_database, pin_existing_snapshot, storage_counts)
from test_thermal_run_store import verify_test_context


PATH = '/v1/source-history/{research_job_id}/collections/{collection_job_id}/farm-input-references'


def selected_path(root, child):
    return PATH.format(research_job_id=root['job_id'], collection_job_id=child['job_id'])


def test_reference_http_errors_are_closed_and_current(source_setup, monkeypatch):
    selection, root, child, principal, _, _ = source_setup
    research, collection = selection.research, selection.collection
    def app_for(with_collection):
        return create_app(research.store, UnusedMarketHoldStore(), research.runs,
            UnusedMarketResultStore(), principal_provider=research.store.principal_provider,
            location_research_service=research, collection_service=collection if with_collection else None)
    path = selected_path(root, child)
    def get(app, where=path):
        return asyncio.run(request(app, path=where, method='GET'))[:2]
    assert get(app_for(False))[0] == 503
    app = app_for(True)
    assert get(app)[0] == 422
    pin_existing_snapshot(selection)
    status, value = get(app)
    assert status == 200 and value == selection.get('tenant-a', root['job_id'], child['job_id']).model_dump(mode='json')
    assert get(app, PATH.format(research_job_id=uuid4(), collection_job_id=child['job_id']))[0] == 404
    assert get(app, PATH.format(research_job_id='invalid', collection_job_id=child['job_id']))[0] == 422
    for scope in READ_SCOPES:
        principal['scopes'].remove(scope)
        assert get(app)[0] == 403
        principal['scopes'].add(scope)
    for error, expected in ((PermissionError('private read detail'), 403),
            (SourceFarmSelectionHold('private held detail'), 422), (RuntimeError('private backend detail'), 503)):
        with monkeypatch.context() as patch:
            def fail(*_args): raise error
            patch.setattr(SourceFarmSelectionService, 'get', fail)
            status, failure = get(app)
            assert status == expected and set(failure) == {'error'} and 'private' not in json.dumps(failure)


def test_reference_schema_keeps_closed_pins_and_fixed_hold():
    document = contract_document()
    operation = document['paths'][PATH]['get']
    assert operation['operationId'] == 'getSourceFarmReferences'
    assert operation['x-ossf-required-scopes'] == list(READ_SCOPES)
    assert operation['responses']['200']['content']['application/json']['schema'] == {
        '$ref': '#/components/schemas/SourceFarmSelection'}
    schema = document['components']['schemas']['SourceFarmSelection']
    Draft202012Validator.check_schema(schema)
    assert schema['additionalProperties'] is False
    assert set(schema['properties']) == set(schema['required'])
    assert schema['properties']['requires_registration_recheck']['const'] is True
    assert schema['properties']['g1_status']['const'] == 'not_accepted'
    assert schema['properties']['assessment_status']['const'] == 'hold'


@pytest.mark.parametrize('login_scope', [{'market_calculation': True, 'break_even_calculation': True,
    'market_source_storage': True}], indirect=True)
def test_standard_https_reads_exact_existing_pins_without_write_scopes(source_setup, tls_files, monkeypatch):
    selection, root, child, _, _, _ = source_setup
    pin_existing_snapshot(selection)
    before = storage_counts(selection)
    expected = selection.get('tenant-a', root['job_id'], child['job_id']).model_dump(mode='json')
    research, jobs = selection.research, selection.research.store
    cert, key, _ = tls_files
    now = datetime.now(timezone.utc)
    allowed = set(READ_SCOPES)
    subjects = [('owner', 'tenant-a', allowed), ('foreign', 'other-tenant', allowed)]
    subjects.extend(('denied-' + scope, 'tenant-a', allowed - {scope}) for scope in READ_SCOPES)
    tokens = {name: ('synthetic-source-farm-' + name + '-' + 's' * 32).encode() for name, _, _ in subjects}
    grants = tuple(BearerGrant(token_digest(tokens[name]), tenant, frozenset(scopes),
        now - timedelta(seconds=1), now + timedelta(minutes=20)) for name, tenant, scopes in subjects)
    source_factory = lambda *, principal_provider: MarketSourceStore(jobs._dsn, jobs.schema,
        principal_provider=principal_provider, runtime_identity=jobs.runtime_identity)
    runtime = ApiRuntime(config(policy=jobs.runtime_identity[0], dsn=jobs._dsn,
        artifact_root=jobs.artifact_root, certificate=cert, private_key=key, port=0),
        dependencies(research_registry=research.catalog, bearer_registry=BearerRegistry(grants),
            owned_fixture_registry=research.registry, owned_research_contexts=dict(research._contexts),
            context_verifier=verify_test_context, market_source_factory=source_factory))
    assert runtime.collections.jobs is runtime.research.store is runtime.jobs
    assert runtime.collections.registry is runtime.research.registry
    server = runtime.service.server()
    thread = threading.Thread(target=server.run, daemon=True)
    thread.start()
    timings = []
    try:
        deadline = time.monotonic() + 15
        while not server.started:
            assert thread.is_alive() and time.monotonic() < deadline
            time.sleep(0.01)
        port = server.servers[0].sockets[0].getsockname()[1]
        trust = ssl.create_default_context(cafile=str(cert))
        def call(bearer='owner', path=selected_path(root, child)):
            conn = http.client.HTTPSConnection('127.0.0.1', port, timeout=30, context=trust)
            try:
                headers = {} if bearer is None else {'Authorization': 'Bearer ' + tokens[bearer].decode()}
                started = time.monotonic()
                conn.request('GET', path, headers=headers)
                response = conn.getresponse()
                data = json.loads(response.read())
                timings.append(time.monotonic() - started)
                assert response.getheader('cache-control') == 'no-store'
                return response.status, data
            finally:
                conn.close()
        assert call(None)[0] == 401
        for scope in READ_SCOPES:
            assert call('denied-' + scope)[0] == 403
        assert call('foreign')[0] == 404
        assert call(path=PATH.format(research_job_id=uuid4(), collection_job_id=child['job_id']))[0] == 404
        assert call() == call() == (200, expected)
        with monkeypatch.context() as patch:
            patch.setattr(runtime.thermal, 'get_decision_context', lambda *_: None)
            assert call()[0] == 422
        assert call() == (200, expected)
        assert len(timings) == 12 and max(timings) < 30
        assert storage_counts(selection) == before and current_principal() is None
        print('source_farm_https=' + json.dumps({'responses': len(timings),
            'max_full_response_seconds': round(max(timings), 3), 'client_timeout_seconds': 30,
            'write_scopes': 0, 'cli': 'synthetic_test_executable'}))
    finally:
        server.should_exit = True
        thread.join(timeout=15)
        assert not thread.is_alive()
