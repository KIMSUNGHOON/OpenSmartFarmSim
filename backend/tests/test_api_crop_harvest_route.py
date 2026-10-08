"""Owned Bearer ASGI control flow using recorded DB values; no live DB/TLS proof."""
import asyncio
from contextlib import contextmanager
from copy import deepcopy
from datetime import timedelta
from hashlib import sha256
import json
import os
from pathlib import Path
import subprocess
import sys
from types import SimpleNamespace
from urllib.parse import urlencode

from fastapi import FastAPI
import pytest

from app import api_crop_harvest_route as route
from app import crop_harvest_current_query as current
from app.api import create_app, _access, _error
from app.api_openapi import _SchemaOnlyStores, contract_document, CONTRACT_PATH
from app.crop_result_store import READ_SCOPES
from app.http_identity import current_principal
from app.runtime_roles import RolePolicyHold
from test_api_crop_cycle_route import protect, TOKEN, NOW
from test_api_crop_harvest_replay import source, REFERENCE_SHA
from test_crop_harvest_current_query import forbid_all_reads_math
from test_crop_harvest import save_native
from test_http_identity import request

PATH = '/v1/crop-harvest-research-results/'


def get(case, result_id=None, *, farm=None, query='', body=b'', headers=None):
    return asyncio.run(request(case.app, path=PATH + (result_id or case.result_id),
        query=(urlencode(case.farm if farm is None else farm) + query).encode(), body=body,
        headers=headers if headers is not None else [(b'authorization', b'Bearer ' + TOKEN)]))


def assembly(source, monkeypatch, *, scopes=READ_SCOPES, tenant=None, clock=None, disabled=False):
    packet = current.registry._decode(source['record']['payload_raw'])
    farm = packet['farm']; trace = []
    state = {'allowed': True, 'exists': True, 'read_error': None, 'current_error': None,
             'tenant_after_read': None}
    jobs = _SchemaOnlyStores(); jobs.principal_provider = current_principal; farms = object()
    parent = object.__new__(current.current.storage.CalculationCycleCropResultStore)
    parent.jobs = jobs; parent.server = SimpleNamespace(binding=SimpleNamespace(farms=farms, jobs=jobs))
    original = object.__new__(current.current.CalculationCurrentCycleQuery); original.store = parent
    store = object.__new__(current.registry.HarvestRegistry); store.query = original
    store.policy = current.registry.schema.HarvestRegistryPolicy(
        'owned_schema', 'owned_owner', 'owned_pub', 'owned_read', 'owned_database')
    store.role = store.policy.reader
    query = object.__new__(current.HarvestCurrentQuery); query.store = store
    monkeypatch.setattr(query, '_binding', lambda: trace.append('binding'))

    @contextmanager
    def open_result(who, result_id, farm_ref, *, start=0, limit=None):
        trace.append('open')
        assert current_principal()['tenant_id'] == who
        try:
            if state['read_error'] is not None: raise state['read_error']
            if not state['allowed']: raise PermissionError('owned private source reason')
            if farm_ref != farm: raise current.HarvestCurrentQueryHold('owned private farm mismatch')
            if result_id != source['record']['result_id'] or not state['exists'] or who != packet['tenant_id']:
                yield None
            else:
                value = deepcopy(source); value['page'] = None
                if limit is not None:
                    total = source['page']['total']
                    if start > total: raise current.HarvestCurrentQueryHold('owned private offset')
                    rows = deepcopy(source['page']['records'][start:start + limit])
                    value['page'] = {'start': start, 'next': start + len(rows), 'total': total, 'records': rows}
                yield value
            trace.append('current')
            if state['current_error'] is not None: raise state['current_error']
            if not state['allowed']: raise PermissionError('owned private withdrawal reason')
        finally:
            trace.append('close')

    monkeypatch.setattr(query, 'open', open_result)
    def bypass(*_, **__): pytest.fail('route bypassed current query')
    for name in ('get', 'summary', 'page'): monkeypatch.setattr(parent, name, bypass)
    for name in ('_find', '_connection', 'put'): monkeypatch.setattr(store, name, bypass)

    def authorized(*required):
        trace.append('account')
        principal = current_principal()
        if principal is None: return None, _error(401, 'unauthenticated', 'Authentication required')
        if any(scope not in principal['scopes'] for scope in required):
            return None, _error(403, 'forbidden', 'Resource access denied')
        return state['tenant_after_read'] or principal['tenant_id'], None

    base = create_app(jobs, jobs, jobs, jobs, principal_provider=current_principal, break_even_store=jobs)
    base.router.routes[:] = [r for r in base.router.routes if getattr(r, 'path', None) != PATH + '{result_id}']
    kwargs = dict(jobs=jobs, farms=farms, query=None if disabled else query,
        principal_provider=current_principal, authorized_tenant=authorized, error=_error, access=_access)
    route.install_harvest_routes(base, **kwargs)
    return SimpleNamespace(app=protect(base, scopes=scopes, tenant=tenant or packet['tenant_id'], clock=clock),
        base=base, kwargs=kwargs, query=query, store=store, parent=parent, trace=trace, state=state,
        farm=farm, result_id=source['record']['result_id'])


@pytest.mark.parametrize('view', ['summary', 'records'])
def test_one_current_context_preserves_recorded_values_and_checks_before_return(source, monkeypatch, view):
    case = assembly(source, monkeypatch); forbid_all_reads_math(monkeypatch)
    expected_source = source if view == 'records' else {**source, 'page': None}
    expected = route.public.project_harvest_result(expected_source, view=view, limit=64 if view == 'records' else None)
    original_bytes = route.public._public_bytes; raw = []
    def encoded(value):
        case.trace.append('bytes'); result = original_bytes(value); raw.append(result); return result
    monkeypatch.setattr(route.public, '_public_bytes', encoded)
    fd = len(os.listdir('/proc/self/fd')); before = deepcopy(source)
    status, value, headers = get(case, query='' if view == 'summary' else '&view=records')
    assert status == 200 and value == expected.model_dump(mode='json')
    assert raw and all(item == original_bytes(expected) for item in raw)
    assert all(len(item) <= route.public.MAX_RESPONSE_BYTES for item in raw)
    assert case.trace.count('open') == case.trace.count('current') == case.trace.count('close') == 1
    assert max(i for i, name in enumerate(case.trace) if name == 'bytes') < case.trace.index('current')
    assert case.trace.index('current') < case.trace.index('close') < len(case.trace) - 1
    assert case.trace[-1] == 'account' and case.trace.count('account') == 2
    assert headers[b'cache-control'] == b'no-store' and headers[b'x-content-type-options'] == b'nosniff'
    assert headers[b'x-ossf-harvest-query-version'] == current.VERSION.encode()
    assert headers[b'x-ossf-harvest-query-code-sha256'] == current.CODE_SHA256.encode()
    assert headers[b'x-ossf-harvest-projection-code-sha256'] == route.public.CODE_SHA256.encode()
    assert source == before and fd == len(os.listdir('/proc/self/fd'))
    save_native('harvest-route-' + view + '.json', {'scope': 'owned_ASGI_recorded_DB_values_not_live_DB_or_TLS',
        'source_receipt_sha256': REFERENCE_SHA, 'status': status, 'response': value,
        'raw_utf8': raw[0].decode(), 'bytes': len(raw[0]), 'sha256': sha256(raw[0]).hexdigest(),
        'trace': case.trace, 'FD_before_after': [fd, fd], 'RHS_regeneration_registration_proof_calls': 0,
        'gates': 'not_assessed'})


@pytest.mark.parametrize('query', ['&extra=1', '&scenario_id=duplicate', '&view=summary&view=records',
    '&view=unknown', '&offset=0', '&limit=1', '&view=records&offset=01', '&view=records&offset=+1',
    '&view=records&offset=-1', '&view=records&offset=1.0', '&view=records&offset=true',
    '&view=records&offset=262145', '&view=records&limit=0', '&view=records&limit=65',
    '&view=records&limit=01', '&view=records&limit=1&limit=2', '&view=records&offset=%201',
    '&view=records&limit='])
def test_invalid_queries_never_open_current_result(source, monkeypatch, query):
    case = assembly(source, monkeypatch)
    status, value, headers = get(case, query=query)
    assert status == 422 and value == {'error': {'code': 'invalid_request', 'message': 'Invalid request'}}
    assert 'open' not in case.trace and headers[b'cache-control'] == b'no-store'


@pytest.mark.parametrize('field', ['scenario_id', 'scenario_revision', 'registration_sha256', 'crop_id'])
@pytest.mark.parametrize('invalid', ['missing', 'empty'])
def test_incomplete_farm_never_opens_result(source, monkeypatch, field, invalid):
    case = assembly(source, monkeypatch); farm = dict(case.farm)
    if invalid == 'missing': farm.pop(field)
    else: farm[field] = ''
    assert get(case, farm=farm)[0] == 422 and 'open' not in case.trace


@pytest.mark.parametrize('result_id', ['crop-cycle-verified-result-v1:' + 'a' * 64,
    'crop-harvest-registered-result-v1:' + 'A' * 64, 'crop-harvest-registered-result-v1:' + 'a' * 63])
def test_invalid_ids_do_not_reach_query(source, monkeypatch, result_id):
    case = assembly(source, monkeypatch)
    assert get(case, result_id)[0] == 422 and 'open' not in case.trace


def test_body_scope_and_credentials_are_checked_before_query(source, monkeypatch):
    case = assembly(source, monkeypatch)
    assert get(case, body=b'{}')[0] == 422 and 'open' not in case.trace
    assert get(case, headers=[])[0] == 401 and 'open' not in case.trace
    case = assembly(source, monkeypatch, scopes=READ_SCOPES[:-1])
    assert get(case)[0] == 403 and 'open' not in case.trace


def test_disabled_query_is_authenticated_unavailable(source, monkeypatch):
    case = assembly(source, monkeypatch, disabled=True)
    assert get(case)[0] == 503 and get(case, headers=[])[0] == 401 and 'open' not in case.trace


@pytest.mark.parametrize('missing', ['exists', 'tenant', 'result'])
def test_missing_or_other_tenant_closes_context_and_returns_not_found(source, monkeypatch, missing):
    case = assembly(source, monkeypatch, tenant='foreign' if missing == 'tenant' else None)
    if missing == 'exists': case.state['exists'] = False
    result_id = 'crop-harvest-registered-result-v1:' + '0' * 64 if missing == 'result' else None
    status, value, _ = get(case, result_id)
    assert status == 404 and value['error']['code'] == 'not_found'
    assert case.trace.count('open') == case.trace.count('current') == case.trace.count('close') == 1


def test_valid_but_mismatched_farm_is_held_without_details(source, monkeypatch):
    case = assembly(source, monkeypatch); farm = {**case.farm, 'crop_id': 'foreign'}
    status, value, _ = get(case, farm=farm)
    assert status == 422 and value['error']['code'] == 'harvest_research_hold'
    assert 'private' not in json.dumps(value) and case.trace.count('close') == 1


@pytest.mark.parametrize('where', ['read_error', 'current_error'])
@pytest.mark.parametrize('error,status,code', [
    (PermissionError, 403, 'forbidden'), (current.HarvestCurrentQueryHold, 422, 'harvest_research_hold'),
    (current.registry.HarvestRegistrationHold, 422, 'harvest_research_hold'),
    (current.registry.replay.HarvestArtifactHold, 422, 'harvest_research_hold'),
    (RuntimeError, 503, 'harvest_research_unavailable'), (RolePolicyHold, 503, 'harvest_research_unavailable')])
def test_read_and_exit_faults_are_closed_and_private(source, monkeypatch, where, error, status, code):
    case = assembly(source, monkeypatch); case.state[where] = error('owned private reason')
    actual, value, headers = get(case)
    assert actual == status and value['error']['code'] == code and 'private' not in json.dumps(value)
    assert case.trace.count('open') == case.trace.count('close') == 1
    assert headers[b'cache-control'] == b'no-store'


@pytest.mark.parametrize('phase', ['project', 'bytes'])
def test_projection_or_serialization_hold_never_publishes(source, monkeypatch, phase):
    case = assembly(source, monkeypatch)
    def held(*_, **__): raise route.public.HarvestProjectionHold('owned private projection')
    monkeypatch.setattr(route.public, 'project_harvest_result' if phase == 'project' else '_public_bytes', held)
    status, value, _ = get(case)
    assert status == 422 and 'private' not in json.dumps(value) and case.trace.count('close') == 1


@pytest.mark.parametrize('withdraw', ['source', 'credential', 'tenant', 'scope'])
def test_changes_during_projection_refuse_prepared_bytes(source, monkeypatch, withdraw):
    clock = {'now': NOW}; case = assembly(source, monkeypatch, clock=lambda: clock['now'])
    project = route.public.project_harvest_result
    def changed(*args, **kwargs):
        value = project(*args, **kwargs)
        if withdraw == 'source': case.state['allowed'] = False
        elif withdraw == 'credential': clock['now'] = NOW + timedelta(hours=1)
        elif withdraw == 'tenant': case.state['tenant_after_read'] = 'foreign'
        else: case.state['current_error'] = PermissionError('owned private scope withdrawal')
        return value
    monkeypatch.setattr(route.public, 'project_harvest_result', changed)
    status, value, _ = get(case)
    assert status == (401 if withdraw == 'credential' else 403) and 'private' not in json.dumps(value)
    assert case.trace.count('current') == case.trace.count('close') == 1
    save_native('harvest-route-withdrawal-' + withdraw + '.json',
        {'scope': 'owned_control_flow_fault_injection_not_live_authority', 'status': status,
         'response': value, 'trace': case.trace, 'stale_bytes_published': False})


@pytest.mark.parametrize('fault', ['query-type', 'registry-type', 'original-query-type', 'parent-store-type',
    'publisher', 'jobs', 'farm', 'binding-jobs', 'principal', 'binding-error',
    'principal-callback', 'authorization-callback', 'error-callback', 'access-callback'])
def test_install_rejects_mixed_configuration(source, monkeypatch, fault):
    case = assembly(source, monkeypatch); kwargs = dict(case.kwargs)
    if fault == 'query-type': kwargs['query'] = SimpleNamespace(**case.query.__dict__)
    elif fault == 'registry-type': case.query.store = SimpleNamespace(**case.store.__dict__)
    elif fault == 'original-query-type': case.store.query = SimpleNamespace(**case.store.query.__dict__)
    elif fault == 'parent-store-type': case.store.query.store = SimpleNamespace(**case.parent.__dict__)
    elif fault == 'publisher': case.store.role = case.store.policy.publisher
    elif fault == 'jobs': kwargs['jobs'] = _SchemaOnlyStores()
    elif fault == 'farm': kwargs['farms'] = object()
    elif fault == 'binding-jobs': case.parent.server.binding.jobs = object()
    elif fault == 'principal': kwargs['principal_provider'] = lambda: None
    elif fault == 'binding-error':
        def invalid(): raise RuntimeError('owned private binding')
        monkeypatch.setattr(case.query, '_binding', invalid)
    else:
        kwargs[{'principal-callback': 'principal_provider', 'authorization-callback': 'authorized_tenant',
                'error-callback': 'error', 'access-callback': 'access'}[fault]] = None
    with pytest.raises(ValueError, match='^trusted harvest reader required$'):
        route.install_harvest_routes(FastAPI(), **kwargs)


def test_offset_split_empty_and_out_of_range_preserve_positions(source, monkeypatch):
    case = assembly(source, monkeypatch); forbid_all_reads_math(monkeypatch); rows = []; responses = []
    for start in (0, 3, 6):
        status, value, _ = get(case, query=f'&view=records&offset={start}&limit=3')
        assert status == 200 and value['page']['offset'] == start and value['page']['total'] == 6
        assert value['page']['next_offset'] == (3 if start == 0 else None)
        rows.extend(value['page']['records']); responses.append(value)
    assert rows == source['page']['records'] and get(case, query='&view=records&offset=7')[0] == 422
    assert case.trace.count('open') == case.trace.count('close') == 4
    save_native('harvest-route-split.json', {'scope': 'owned_ASGI_recorded_DB_values_not_live_DB_or_TLS',
        'full_split_equal': True, 'rows': len(rows), 'responses': responses, 'past_total_status': 422})


def test_openapi_invalidates_cache_preserves_old_contract_and_declares_authenticated_bounds():
    stores = _SchemaOnlyStores(); base = create_app(stores, stores, stores, stores,
        principal_provider=current_principal, break_even_store=stores)
    declared = deepcopy(base.openapi()); static = CONTRACT_PATH.read_bytes()
    assert contract_document() == declared
    base.router.routes[:] = [r for r in base.router.routes if getattr(r, 'path', None) != PATH + '{result_id}']
    base.openapi_schema = None
    before = deepcopy(base.openapi())
    route.install_harvest_routes(base, jobs=stores, farms=None, query=None, principal_provider=current_principal,
        authorized_tenant=lambda *_: None, error=_error, access=_access)
    assert base.openapi_schema is None
    doc = base.openapi(); operation = doc['paths'][PATH + '{result_id}']['get']
    assert set(doc['paths']) - set(before['paths']) == {PATH + '{result_id}'}
    assert all(doc['paths'][k] == v for k, v in before['paths'].items())
    assert all(doc['components']['schemas'][k] == v for k, v in before['components']['schemas'].items())
    assert contract_document() == declared and CONTRACT_PATH.read_bytes() == static
    assert operation['operationId'] == 'getHarvestResearchResult'
    assert operation['security'] == [{'ServiceBearer': []}] and operation['x-ossf-required-scopes'] == list(READ_SCOPES)
    assert doc['components']['securitySchemes']['ServiceBearer']['scheme'] == 'bearer'
    params = {p['name']: p for p in operation['parameters']}
    assert set(params) == {'result_id', 'scenario_id', 'scenario_revision', 'registration_sha256', 'crop_id', 'view', 'offset', 'limit'}
    assert params['result_id']['schema']['pattern'] == route.public.RESULT_ID_PATTERN
    assert params['offset']['schema']['maximum'] == route.public.MAX_ROWS
    assert params['limit']['schema']['anyOf'][0]['maximum'] == 64
    assert all(params[k]['required'] for k in ('result_id', 'scenario_id', 'scenario_revision', 'registration_sha256', 'crop_id'))
    assert set(operation['responses']) == {'200', '401', '403', '404', '422', '503'}
    assert operation['responses']['200']['content']['application/json']['schema']['$ref'].endswith('/HarvestReplay')
    assert doc['components']['schemas']['HarvestReplay']['additionalProperties'] is False
    save_native('harvest-route-openapi.json', {'scope': 'installer_schema_only_not_runtime_app',
        'old_path_count': len(before['paths']), 'old_schema_count': len(before['components']['schemas']),
        'existing_paths_schemas_preserved': True, 'static_contract_sha256': sha256(static).hexdigest(),
        'cache_invalidated': True, 'operation': operation, 'ServiceBearer': doc['components']['securitySchemes']['ServiceBearer']})


def test_fresh_import_has_no_connection_or_descriptor_side_effect():
    code = '''import json,os,socket,sys,psycopg
calls=[]
def forbidden(*a,**k):
 calls.append(True);raise AssertionError('connection during import')
psycopg.connect=forbidden;socket.create_connection=forbidden
before=len(os.listdir('/proc/self/fd'))
import app.api_crop_harvest_route
assert not calls and before==len(os.listdir('/proc/self/fd'))
print(json.dumps({'connection_calls':len(calls),'FD_before_after':[before,before]}))
'''
    child = subprocess.run([sys.executable, '-c', code], capture_output=True, text=True, timeout=30)
    assert child.returncode == 0 and child.stderr == ''
    save_native('harvest-route-import.json', {'original_child_exit_code': child.returncode, **json.loads(child.stdout)})
