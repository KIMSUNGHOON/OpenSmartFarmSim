"""Saved source workflow recovery uses stored tenant links, not browser memory."""

import asyncio
from hashlib import sha256
import json
from urllib.parse import urlencode, urlsplit
from uuid import uuid4

from app.api import create_app
from app.cli_contracts import DecisionContract
from app.cli_worker import CliWorker
from app.owned_fixture_collection import CollectionService, CollectionWorker
from app.owned_collection_review import OwnedCollectionReviewService
from app.owned_source_history import COLLECTION_KEY, READ_SCOPES
from test_api_job_status import UnusedMarketHoldStore, UnusedMarketResultStore
from test_cli_worker import _fake_cli
from test_http_identity import request
from test_owned_collection_review import review_setup
from test_owned_fixture_collection import collection_setup, login_scope, login_database
from test_owned_research import research_setup


def get(app, path):
    url = urlsplit(path)
    return asyncio.run(request(app, path=url.path, query=url.query.encode(), method='GET'))[:2]


def app_for(service, collection=None, review=None):
    return create_app(service.store, UnusedMarketHoldStore(), service.runs,
        UnusedMarketResultStore(), principal_provider=service.store.principal_provider,
        location_research_service=service, collection_service=collection,
        owned_collection_review_service=review)


def test_source_history_restores_owned_jobs_and_current_authority(research_setup, monkeypatch):
    service, body, principal, _ = research_setup
    root = service.submit('tenant-a', body)[2]
    app = app_for(service)
    status, page = get(app, '/v1/source-history')
    assert status == 200 and len(page['items']) == 1
    item = page['items'][0]
    assert item['job']['job_id'] == str(root['job_id'])
    assert item['point'] == {'latitude': 37.5, 'longitude': 127.0}
    assert item['current_authority'] == 'available'
    assert 'input_bytes' not in json.dumps(page) and 'decision_context_id' not in json.dumps(page)
    status, detail = get(app, '/v1/source-history/' + str(root['job_id']))
    assert status == 200 and detail == {'research': item, 'collection': None, 'review': None}
    assert get(app, '/v1/source-history/' + str(uuid4()))[0] == 404
    assert get(app, '/v1/source-history?before_job_id=' + str(root['job_id']))[0] == 422
    for scope in READ_SCOPES:
        principal['scopes'].remove(scope)
        assert get(app, '/v1/source-history')[0] == 403
        principal['scopes'].add(scope)
    principal['tenant_id'] = 'other-tenant'
    assert get(app, '/v1/source-history')[1] == {'items': [], 'next_cursor': None}
    assert get(app, '/v1/source-history/' + str(root['job_id']))[0] == 404
    principal['tenant_id'] = 'tenant-a'
    monkeypatch.setattr(service.runs, 'get_decision_context', lambda *_: None)
    assert get(app, '/v1/source-history')[1]['items'][0]['current_authority'] == 'hold'
    assert get(app, '/v1/source-history/' + str(root['job_id']))[1]['research']['current_authority'] == 'hold'


def test_source_history_restores_linked_collection_review_and_pages(research_setup, tmp_path):
    service, body, _, _ = research_setup
    first = service.submit('tenant-a', body)[2]
    second = service.submit('tenant-a', body.model_copy(update={
        'idempotency_key': 'owned-research-history-second'}))[2]
    app = app_for(service)
    status, page = get(app, '/v1/source-history?limit=1')
    assert status == 200 and page['next_cursor'] is not None
    cursor = page['next_cursor']
    assert cursor['job_id'] == page['items'][0]['job']['job_id']
    status, older = get(app, '/v1/source-history?' + urlencode({
        'limit': 1, 'before_created_at': cursor['created_at'], 'before_job_id': cursor['job_id']}))
    assert status == 200 and older['items'][0]['job']['job_id'] == str(first['job_id'])
    assert {page['items'][0]['job']['job_id'], older['items'][0]['job']['job_id']} == {
        str(first['job_id']), str(second['job_id'])}

    contract = DecisionContract(service.authority_snapshot)
    service.store.decision_validator = contract
    program = _fake_cli(tmp_path)
    program.write_text(program.read_text().replace('candidate-a', service.registry.provider_id))
    home = tmp_path / 'source-history-cli-home'
    home.mkdir(mode=0o700)
    worker = CliWorker(service.store, contract, cli_path=program, codex_home=home,
        child_env={'CODEX_API_KEY': 'synthetic-test-key'}, timeout_seconds=10,
        lease_seconds=300, synthetic_smoke=True)
    assert worker.run_once().state == 'succeeded'
    collection = CollectionService(service.store, service.registry)
    collected = collection.submit('tenant-a', str(first['job_id']), 'history-collection')
    assert CollectionWorker(collection, tenant_id='tenant-a').run_once(str(collected['job_id'])).state == 'succeeded'
    review = OwnedCollectionReviewService(collection, service.runs)
    reviewed = review.submit('tenant-a', str(collected['job_id']), 'history-review')
    linked = app_for(service, collection, review)
    status, detail = get(linked, '/v1/source-history/' + str(first['job_id']))
    assert status == 200 and detail['collection']['job_id'] == str(collected['job_id'])
    assert detail['review']['job_id'] == str(reviewed['job_id'])
    assert detail['research']['job']['job_id'] == str(first['job_id'])
    assert 'input_bytes' not in json.dumps(detail) and 'raw_utf8' not in json.dumps(detail)
    assert get(linked, '/v1/source-history/' + str(second['job_id']))[1]['collection'] is None
    with service.store.connect() as conn:
        stored = service.store._locked_job(conn, 'tenant-a', collected['job_id'])
        forged = json.loads(service.store._verified_input(stored))
    forged['research_input_sha256'] = 'a' * 64
    service.store.submit('tenant-a', 'collection', forged,
        COLLECTION_KEY + sha256(b'wrong-history-parent').hexdigest())
    assert get(linked, '/v1/source-history/' + str(first['job_id']))[0] == 422


def test_source_history_requires_owned_research_runtime(research_setup):
    service, _, _, _ = research_setup
    app = create_app(service.store, UnusedMarketHoldStore(), service.runs,
        UnusedMarketResultStore(), principal_provider=service.store.principal_provider)
    assert get(app, '/v1/source-history')[0] == 503
