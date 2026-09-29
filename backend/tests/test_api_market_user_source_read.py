"""Owned immutable source reads over actual SCRAM; no external data gate."""

import asyncio
import json
import os
from datetime import datetime, timezone, timedelta
from urllib.parse import urlencode

import pytest
from jsonschema import Draft202012Validator

from test_api_market_user_source import source_api, post, counts
from test_market_source_store import PROFILE, login_database, login_scope
from test_http_identity import request
from test_api_serve import tls_files

pytestmark = pytest.mark.parametrize('login_scope', [{**PROFILE, 'break_even_calculation': True}], indirect=True)


def get(app, path='/v1/market-user-sources', **query):
    return asyncio.run(request(app, path=path, query=urlencode(query).encode()))[:2]


@pytest.mark.parametrize('kind', ['economic_scenario', 'economic_input', 'joint_shock',
    'input_rights', 'settlement_applicability', 'settlement_evidence', 'prior_batch_cost'])
def test_typed_record_roundtrip_needs_no_write_and_preserves_nulls_strings_and_pin(source_api, kind):
    app, jobs, _, principal, _, values = source_api
    status, registered = post(app, {'kind': kind, 'input': values[kind], 'idempotency_key': 'read'})
    assert status == 200
    principal['scopes'].remove('market_source_write')
    status, result = get(app, '/v1/market-user-sources/record', kind=kind,
        record_id=registered['record_id'], revision=registered['revision'])
    assert status == 200
    assert result['input'] == values[kind]
    assert result['payload_sha256'] == registered['payload_sha256']
    assert result['recorded_at'] == registered['recorded_at']
    assert result['admission_kind'] == 'contract_valid_user_assumption'
    assert 'tenant_id' not in json.dumps(result) and 'intent_job' not in result
    assert counts(jobs) == (1, 1)


def test_catalog_empty_and_byte_ordered_cursor_without_duplicates(source_api):
    app, jobs, _, _, _, values = source_api
    assert get(app, kind='economic_input') == (200, {
        'kind': 'economic_input', 'items': [], 'next_cursor': None})
    pairs = [('가정/# ?%', 'r2'), ('same', 'r2'), ('same', 'r10'), ('B', 'r1'), ('a', 'r1')]
    for index, (record_id, revision) in enumerate(pairs):
        payload = values['economic_input'] | {'input_id': record_id, 'revision': revision}
        assert post(app, {'kind': 'economic_input', 'input': payload,
            'idempotency_key': 'page-'+str(index)})[0] == 200
    query = {'kind': 'economic_input', 'limit': 2}
    found = []
    while True:
        status, page = get(app, **query)
        assert status == 200 and len(page['items']) <= 2
        assert all('input' not in item and 'tenant_id' not in item for item in page['items'])
        found += [(item['record_id'], item['revision']) for item in page['items']]
        if page['next_cursor'] is None:
            break
        cursor = page['next_cursor']
        assert (cursor['record_id'], cursor['revision']) == found[-1]
        query |= {'after_record_id': cursor['record_id'], 'after_revision': cursor['revision']}
    assert found == sorted(pairs, key=lambda pair: tuple(part.encode() for part in pair))
    assert len(found) == len(set(found)) and counts(jobs) == (5, 5)
    assert get(app, kind='joint_shock')[1]['items'] == []
    status, record = get(app, '/v1/market-user-sources/record', kind='economic_input',
        record_id=pairs[0][0], revision=pairs[0][1])
    assert status == 200 and record['input']['input_id'] == pairs[0][0]


def test_foreign_and_missing_record_are_indistinguishable(source_api):
    app, _, _, principal, _, values = source_api
    _, record = post(app, {'kind': 'economic_input', 'input': values['economic_input'], 'idempotency_key': 'own'})
    query = {'kind': record['kind'], 'record_id': record['record_id'], 'revision': record['revision']}
    missing = get(app, '/v1/market-user-sources/record', **(query | {'revision': 'absent'}))
    principal['tenant_id'] = 'tenant-2'
    assert get(app, '/v1/market-user-sources/record', **query) == missing
    assert missing[0] == 404 and 'input' not in missing[1]
    assert get(app, kind='economic_input')[1]['items'] == []


@pytest.mark.parametrize('query', [{'kind': 'unknown'}, {'kind': 'economic_input', 'limit': 0},
    {'kind': 'economic_input', 'limit': 51}, {'kind': 'economic_input', 'limit': '1.5'},
    {'kind': 'economic_input', 'after_record_id': 'x'},
    {'kind': 'economic_input', 'after_revision': 'r1'},
    {'kind': 'economic_input', 'after_record_id': 'x'*201, 'after_revision': 'r1'},
    {'kind': 'economic_input', 'after_record_id': ' x', 'after_revision': 'r1'}])
def test_bad_catalog_queries_do_not_read_or_write(source_api, monkeypatch, query):
    app, jobs, sources, _, _, _ = source_api
    def unexpected():
        pytest.fail('invalid query reached storage')
    monkeypatch.setattr(sources, 'connect', unexpected)
    status, result = get(app, **query)
    assert status == 422 and result == {'error': {'code': 'invalid_request', 'message': 'Invalid request'}}
    assert counts(jobs) == (0, 0)


@pytest.mark.parametrize('path', ['/v1/market-user-sources', '/v1/market-user-sources/record'])
@pytest.mark.parametrize('scope', ['market_source_read', 'metadata'])
def test_read_scopes_required_before_lookup_and_rechecked_after_it(source_api, monkeypatch, path, scope):
    app, jobs, sources, principal, _, values = source_api
    _, record = post(app, {'kind': 'economic_input', 'input': values['economic_input'], 'idempotency_key': 'scope'})
    query = {'kind': 'economic_input'}
    if path.endswith('/record'):
        query |= {'record_id': record['record_id'], 'revision': record['revision']}
    principal['scopes'].remove(scope)
    original = sources.connect
    def unexpected():
        pytest.fail('missing scope reached storage')
    monkeypatch.setattr(sources, 'connect', unexpected)
    assert get(app, path, **query)[0] == 403
    principal['scopes'].add(scope)
    monkeypatch.setattr(sources, 'connect', original)
    verify = sources._verified
    def revoke(*args):
        result = verify(*args)
        principal['scopes'].remove(scope)
        return result
    monkeypatch.setattr(sources, '_verified', revoke)
    status, result = get(app, path, **query)
    assert status == 403 and 'input' not in result and counts(jobs) == (1, 1)


@pytest.mark.parametrize('fault', ['original_job', 'payload_hash', 'version', 'admitting_role', 'binding', 'failure'])
def test_corruption_rebinding_and_failures_publish_no_record_or_partial_page(source_api, monkeypatch, fault):
    app, jobs, sources, _, service, values = source_api
    _, record = post(app, {'kind': 'economic_input', 'input': values['economic_input'], 'idempotency_key': 'fault'})
    select = sources._select
    verify = sources._verified
    if fault == 'original_job':
        monkeypatch.setattr(sources, '_job_input', lambda *args: b'{}')
    elif fault in ('payload_hash', 'version', 'admitting_role'):
        field = {'payload_hash': 'payload_sha256', 'version': 'store_version', 'admitting_role': 'admitted_by'}[fault]
        def corrupt(*args):
            row = select(*args)
            return row | {field: '0'*64 if fault == 'payload_hash' else 'private-rejected-value'}
        monkeypatch.setattr(sources, '_select', corrupt)
    elif fault == 'binding':
        from app.market_source_store import MarketSourceStore
        def rebind(*args):
            result = verify(*args)
            service.sources = MarketSourceStore(sources.dsn, sources.schema,
                principal_provider=sources._principal_provider, runtime_identity=sources.runtime_identity)
            return result
        monkeypatch.setattr(sources, '_verified', rebind)
    else:
        def fail(*args):
            raise RuntimeError('private credentials and record contents')
        monkeypatch.setattr(sources, '_verified', fail)
    status, result = get(app, '/v1/market-user-sources/record', kind='economic_input',
        record_id=record['record_id'], revision=record['revision'])
    assert status == 503 and result == {'error': {'code': 'source_unavailable',
        'message': 'User source lookup unavailable'}}
    # _select faults apply to exact lookups; catalog tests verify every lookahead too.
    if fault not in ('payload_hash', 'version', 'admitting_role'):
        service.sources = sources
        assert get(app, kind='economic_input') == (status, result)
    assert 'private' not in json.dumps(result) and counts(jobs) == (1, 1)


def test_corrupt_catalog_lookahead_rejects_whole_page(source_api, monkeypatch):
    app, _, sources, _, _, values = source_api
    for record_id in ('a', 'b'):
        assert post(app, {'kind': 'economic_input', 'input': values['economic_input'] | {'input_id': record_id},
            'idempotency_key': record_id})[0] == 200
    original = sources._verified
    def corrupt(conn, row):
        if row['record_id'] == 'b':
            raise ValueError('private corrupt lookahead')
        return original(conn, row)
    monkeypatch.setattr(sources, '_verified', corrupt)
    status, result = get(app, kind='economic_input', limit=1)
    assert status == 503 and 'items' not in result and 'private' not in json.dumps(result)


def test_openapi_seven_closed_owner_redacted_shapes_match_actual_records(source_api):
    app, _, _, _, _, values = source_api
    schema = app.openapi()
    operation = schema['paths']['/v1/market-user-sources/record']['get']
    assert operation['x-ossf-required-scopes'] == ['market_source_read', 'metadata']
    response_schema = operation['responses']['200']['content']['application/json']['schema']
    assert len(response_schema['oneOf']) == 7
    validator = Draft202012Validator(response_schema | {'components': schema['components']})
    for kind, payload in values.items():
        _, registered = post(app, {'kind': kind, 'input': payload, 'idempotency_key': 'schema-'+kind})
        status, record = get(app, '/v1/market-user-sources/record', kind=kind,
            record_id=registered['record_id'], revision=registered['revision'])
        assert status == 200
        validator.validate(record)
        assert list(validator.iter_errors(record | {'input': record['input'] | {'tenant_id': 'tenant-1'}}))
        missing = record['input'].copy()
        missing.pop(next(iter(missing)))
        assert list(validator.iter_errors(record | {'input': missing}))


def test_fresh_runtime_bearer_reads_without_write_cache_or_tenant_override(source_api, tls_files):
    from app.api_runtime import ApiRuntime
    from app.http_identity import BearerRegistry, BearerGrant, token_digest, current_principal
    from app.api_market_source import SOURCE_READ_SCOPES
    from app.market_source_store import MarketSourceStore
    from test_api_runtime import config, dependencies
    app, jobs, _, _, _, values = source_api
    _, record = post(app, {'kind': 'economic_input', 'input': values['economic_input'], 'idempotency_key': 'runtime'})
    os.close(jobs._content_directory(create=True))
    token = b'synthetic-source-read-token-'+b'r'*32
    now = datetime.now(timezone.utc)
    registry = BearerRegistry((BearerGrant(token_digest(token), 'tenant-1', frozenset(SOURCE_READ_SCOPES),
        now-timedelta(seconds=1), now+timedelta(minutes=5)),))
    cert, key, _ = tls_files
    factory = lambda *, principal_provider: MarketSourceStore(jobs._dsn, jobs.schema,
        principal_provider=principal_provider, runtime_identity=jobs.runtime_identity)
    runtime = ApiRuntime(config(policy=jobs.runtime_identity[0], dsn=jobs._dsn, artifact_root=jobs.artifact_root,
        certificate=cert, private_key=key), dependencies(bearer_registry=registry, market_source_factory=factory))
    query = urlencode({'kind': record['kind'], 'record_id': record['record_id'], 'revision': record['revision']}).encode()
    status, result, headers = asyncio.run(request(runtime.service.app,
        path='/v1/market-user-sources/record', query=query,
        headers=[(b'authorization', b'Bearer '+token), (b'x-tenant-id', b'foreign-tenant')]))
    assert status == 200 and result['input'] == values['economic_input']
    assert headers[b'cache-control'] == b'no-store' and current_principal() is None
    assert asyncio.run(request(runtime.service.app, path='/v1/market-user-sources/record', query=query, headers=[]))[0] == 401


@pytest.mark.parametrize('fault', ['owner', 'revision'])
def test_returned_row_must_match_requested_owner_and_version(source_api, monkeypatch, fault):
    app, _, sources, principal, _, values = source_api
    body = {'kind': 'economic_input', 'input': values['economic_input'], 'idempotency_key': 'identity'}
    _, record = post(app, body)
    principal['tenant_id'] = 'tenant-2' if fault == 'owner' else 'tenant-1'
    other = body['input'] | {'value': '999'}
    if fault == 'revision':
        other['revision'] = 'other-revision'
    assert post(app, body | {'input': other, 'idempotency_key': 'other-row'})[0] == 200
    principal['tenant_id'] = 'tenant-1'
    select = sources._select
    monkeypatch.setattr(sources, '_select', lambda conn, tenant, kind, identity, revision:
        select(conn, 'tenant-2' if fault == 'owner' else tenant, kind, identity,
            'other-revision' if fault == 'revision' else revision))
    status, result = get(app, '/v1/market-user-sources/record', kind=record['kind'],
        record_id=record['record_id'], revision=record['revision'])
    assert status == 503 and 'input' not in result


def test_exact_decimal_string_and_identical_new_intent_preserve_one_catalog_entry(source_api):
    app, jobs, _, _, _, values = source_api
    body = {'kind': 'economic_input', 'input': values['economic_input'] | {
        'value': '9007199254740993.0000000001'}, 'idempotency_key': 'precise'}
    _, first = post(app, body)
    _, later = post(app, body | {'idempotency_key': 'same-record-new-intent'})
    assert later['intent_job']['job_id'] != first['intent_job']['job_id']
    assert later['recorded_at'] == first['recorded_at']
    status, page = get(app, kind='economic_input')
    assert status == 200 and len(page['items']) == 1 and counts(jobs) == (2, 1)
    status, result = get(app, '/v1/market-user-sources/record', kind='economic_input',
        record_id=first['record_id'], revision=first['revision'])
    assert status == 200 and result['input']['value'] == '9007199254740993.0000000001'


def test_large_legal_source_response_has_space_for_metadata(source_api):
    app, _, _, _, _, values = source_api
    payload = json.loads(json.dumps(values['joint_shock']))
    payload['shock_id'] = '가'*200
    payload['revision'] = '나'*200
    body = {'kind': 'joint_shock', 'input': payload, 'idempotency_key': 'large-read'}
    serialize = lambda: json.dumps(body, ensure_ascii=False, separators=(',', ':')).encode()
    payload['drivers'][0]['hypothesis'] = 'x'*(65000-len(serialize())+len(payload['drivers'][0]['hypothesis'].encode()))
    raw = serialize()
    assert len(raw) == 65000
    status, record = post(app, body, raw=raw)
    assert status == 200
    status, result = get(app, '/v1/market-user-sources/record', kind='joint_shock',
        record_id=record['record_id'], revision=record['revision'])
    assert status == 200 and result['input'] == payload
    size = len(json.dumps(result, ensure_ascii=False, separators=(',', ':')).encode())
    assert 65536 < size <= 131072


def test_unconfigured_source_service_does_not_offer_fake_inputs(source_api):
    from app.api import create_app
    from test_api_job_status import UnusedThermalRunStore, UnusedMarketResultStore
    from test_api_thermal_run import UnusedMarketHoldStore
    _, jobs, _, principal, _, _ = source_api
    app = create_app(jobs, UnusedMarketHoldStore(), UnusedThermalRunStore(), UnusedMarketResultStore(),
        principal_provider=jobs.principal_provider)
    queries = [('/v1/market-user-sources', {'kind': 'economic_input'}),
        ('/v1/market-user-sources/record', {'kind': 'economic_input', 'record_id': 'missing', 'revision': 'r1'})]
    for path, query in queries:
        assert get(app, path, **query) == (503, {'error': {'code': 'source_unavailable',
            'message': 'User source lookup unavailable'}})
    principal['authenticated'] = False
    for path, query in queries:
        assert get(app, path, **query)[0] == 401
    assert counts(jobs) == (0, 0)
