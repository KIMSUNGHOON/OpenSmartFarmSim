"""ASGI control flow for verified results; custody authority is tested separately."""
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
from fastapi.exceptions import RequestValidationError
import pytest

from app import api
from app import api_crop_cycle_calculation_route as route
from app import crop_cycle_calculation_current_query as current
from app import crop_cycle_calculation_result_store as storage
from app.api import create_app, _access, _error
from app.api_openapi import _SchemaOnlyStores, contract_document
from app.crop_cycle_calculation_farm_binding import CalculationFarmBindingHold
from app.crop_cycle_calculation_server_custody import CalculationCustodyHold
from app.crop_result_store import READ_SCOPES
from app.farm_authoring_storage import FarmAuthoringHold
from app.http_identity import current_principal
from app.runtime_roles import RolePolicyHold
from app.thermal_run_store import _canonical
from test_api_crop_cycle_route import protect, TOKEN, NOW
from test_api_crop_cycle_calculation_replay import saved, program, forbid_computation
from test_http_identity import request

PATH = '/v1/crop-cycle-calculation-research-results/'
FARM = {'scenario_id': 'own-projection-farm', 'scenario_revision': 'r1',
        'registration_sha256': '2' * 64, 'crop_id': 'crop-1'}


def get(app, result_id, farm=FARM, *, query='', body=b'', headers=None):
    return asyncio.run(request(app, path=PATH + result_id,
        query=(urlencode(farm) + query).encode(), body=body,
        headers=headers if headers is not None else [(b'authorization', b'Bearer ' + TOKEN)]))


def test_default_authenticated_calculation_route_is_unavailable():
    unused = _SchemaOnlyStores()
    app = protect(create_app(unused, unused, unused, unused, principal_provider=current_principal))
    result_id = 'crop-cycle-verified-result-v1:' + 'a' * 64
    status, body, _ = get(app, result_id)
    assert status == 503 and body['error']['code'] == 'crop_research_unavailable'
    assert get(app, result_id, headers=[])[0] == 401


@pytest.fixture(scope='module')
def calculation_case(tmp_path_factory):
    return saved(tmp_path_factory.mktemp('calculation-route'), program('full-removal-reentry'))


def assembly(case, monkeypatch, *, scopes=READ_SCOPES, tenant='own-projection-tenant', clock=None):
    record, terminal, pages = case
    packet = json.loads(record['payload_raw']); farm = packet['binding']['request']['farm']
    trace = []
    state = {'allowed': True, 'exists': True, 'read_error': None, 'current_error': None,
             'tenant_after_read': None}
    jobs = SimpleNamespace(principal_provider=current_principal); farms = object()
    store = object.__new__(storage.CalculationCycleCropResultStore)
    store.jobs = jobs; store.server = SimpleNamespace(binding=SimpleNamespace(farms=farms, jobs=jobs))
    monkeypatch.setattr(store, '_binding', lambda: trace.append('store-binding'))
    query = object.__new__(current.CalculationCurrentCycleQuery); query.store = store
    monkeypatch.setattr(query, '_binding', lambda: trace.append('query-binding'))
    @contextmanager
    def open_result(who, result_id, farm_ref, *, kind=None, start=0, limit=None):
        trace.append('open')
        assert current_principal()['tenant_id'] == who
        try:
            if state['read_error'] is not None: raise state['read_error']
            if not state['allowed']: raise PermissionError('private source reason')
            if farm_ref != farm: raise CalculationFarmBindingHold('private farm mismatch')
            if result_id != record['result_id'] or not state['exists'] or who != packet['tenant_id']:
                yield None
            else:
                page = None
                if kind is not None:
                    original = deepcopy(pages[kind]); total = original['total']
                    if start > total: raise current.CalculationCurrentCycleQueryHold('private offset beyond total')
                    rows = original['records'][start:start + limit]
                    page = {'kind': kind, 'start': start, 'next': start + len(rows), 'total': total, 'records': rows}
                yield {'record': deepcopy(record), 'terminal': deepcopy(terminal), 'page': page}
            trace.append('current')
            if state['current_error'] is not None: raise state['current_error']
            if not state['allowed']: raise PermissionError('private withdrawal reason')
        finally:
            trace.append('close')
    monkeypatch.setattr(query, 'open', open_result)
    for name in ('get', 'page', 'summary'):
        monkeypatch.setattr(store, name, lambda *_: pytest.fail('route bypassed current query'))
    def authorized(*required):
        principal = current_principal()
        if principal is None: return None, _error(401, 'unauthenticated', 'Authentication required')
        if any(scope not in principal['scopes'] for scope in required):
            return None, _error(403, 'forbidden', 'Resource access denied')
        return state['tenant_after_read'] or principal['tenant_id'], None
    app = FastAPI()
    @app.exception_handler(RequestValidationError)
    async def invalid(*_): return _error(422, 'invalid_request', 'Invalid request')
    route.install_calculation_cycle_routes(app, jobs=jobs, farms=farms, store=store, query=query,
        principal_provider=current_principal, authorized_tenant=authorized, error=_error, access=_access)
    return protect(app, scopes=scopes, tenant=tenant, clock=clock), store, query, farm, trace, state


@pytest.mark.parametrize('view', ['summary', 'samples', 'events'])
def test_one_current_context_preserves_original_bytes_and_checks_after_projection(calculation_case, monkeypatch, view):
    app, _, _, farm, trace, _ = assembly(calculation_case, monkeypatch)
    forbid_computation(monkeypatch)
    before = len(os.listdir('/proc/self/fd')); original_bytes = route.public._public_bytes
    def encoded(value): trace.append('bytes'); return original_bytes(value)
    monkeypatch.setattr(route.public, '_public_bytes', encoded)
    status, value, headers = get(app, calculation_case[0]['result_id'], farm,
                                 query='' if view == 'summary' else '&view=' + view)
    assert status == 200 and value['schema_version'] == 'crop-cycle-calculation-replay-v1'
    assert value['result_id'] == calculation_case[0]['result_id']
    assert trace.count('open') == trace.count('current') == trace.count('close') == 1
    assert max(i for i, name in enumerate(trace) if name == 'bytes') < trace.index('current') < trace.index('close')
    assert headers[b'cache-control'] == b'no-store'
    assert headers[b'x-ossf-crop-query-version'] == current.VERSION.encode()
    assert headers[b'x-ossf-crop-query-code-sha256'] == current.CODE_SHA256.encode()
    assert value['reference']['gates'] == 'not_assessed'
    assert value['reference']['input_validation'] == json.loads(calculation_case[0]['payload_raw'])['binding']['input']['input_validation']
    if view == 'summary':
        assert _canonical(value['summary']['manifest']) == _canonical(calculation_case[1]['manifest'])
        assert value['page'] is None
    else:
        expected = calculation_case[2][view]['records']
        if view == 'events': expected = [{k: row[k] for k in ('at', 'before', 'after', 'removed')} for row in expected]
        assert _canonical(value['page']['records']) == _canonical(expected) and value['summary'] is None
        assert value['page']['limit'] == (64 if view == 'samples' else 8)
    raw = _canonical(value)
    assert len(raw) <= 2 * 1024 * 1024 and len(os.listdir('/proc/self/fd')) == before
    for field in (b'"tenant_id":', b'"checkpoint":', b'"input_id":', b'"rights":', b'"integrity_key":'):
        assert field not in raw
    save_reference('normal-' + view + '.json', {'status': status, 'view': view,
        'response_bytes': len(raw), 'response_sha256': sha256(raw).hexdigest(),
        'one_context_and_post_bytes_current_check': True, 'same_original_values_UTC_validation': True,
        'parser_context_QC_RHS_forbidden': True, 'fd_before': before, 'fd_after': len(os.listdir('/proc/self/fd'))})


@pytest.mark.parametrize('query', ['&tenant_id=foreign', '&root=/tmp/private', '&view=summary&offset=0', '&limit=8',
    '&view=events&limit=9', '&view=samples&limit=65', '&view=samples&offset=131073', '&view=samples&offset=-1',
    '&view=samples&offset=01', '&view=samples&limit=+1', '&view=events&limit=1.0', '&view=samples&offset=true',
    '&view=samples&offset=0&offset=1', '&view=samples&view=events', '&view=unknown', '&crop_id=foreign'])
def test_closed_request_is_denied_before_query(calculation_case, monkeypatch, query):
    app, _, _, farm, trace, _ = assembly(calculation_case, monkeypatch)
    assert get(app, calculation_case[0]['result_id'], farm, query=query)[0] == 422 and 'open' not in trace


@pytest.mark.parametrize('fault', ['body', 'missing-field', 'old-id', 'authentication', 'scope'])
def test_invalid_request_and_missing_authority_do_not_open(calculation_case, monkeypatch, fault):
    app, _, _, farm, trace, _ = assembly(calculation_case, monkeypatch,
        scopes=READ_SCOPES[:-1] if fault == 'scope' else READ_SCOPES)
    selected = dict(farm); result_id = calculation_case[0]['result_id']
    if fault == 'missing-field': del selected['crop_id']
    if fault == 'old-id': result_id = 'crop-cycle-result-v1:' + 'a' * 64
    status = get(app, result_id, selected, body=b'{}' if fault == 'body' else b'',
                 headers=[] if fault == 'authentication' else None)[0]
    assert status == (401 if fault == 'authentication' else 403 if fault == 'scope' else 422)
    assert 'open' not in trace


@pytest.mark.parametrize('missing', ['exists', 'tenant', 'result-id'])
def test_missing_or_foreign_result_closes_without_payload(calculation_case, monkeypatch, missing):
    app, _, _, farm, trace, state = assembly(calculation_case, monkeypatch,
        tenant='foreign' if missing == 'tenant' else 'own-projection-tenant')
    if missing == 'exists': state['exists'] = False
    result_id = 'crop-cycle-verified-result-v1:' + 'a' * 64 if missing == 'result-id' else calculation_case[0]['result_id']
    assert get(app, result_id, farm)[0] == 404
    assert trace.count('open') == trace.count('current') == trace.count('close') == 1


@pytest.mark.parametrize('position', ['read_error', 'current_error'])
@pytest.mark.parametrize('error,status', [(PermissionError('private'), 403),
    (CalculationCustodyHold('private'), 422), (CalculationFarmBindingHold('private'), 422),
    (current.CalculationCurrentCycleQueryHold('private'), 422), (FarmAuthoringHold('private'), 422),
    (RolePolicyHold('private'), 503), (RuntimeError('private'), 503)])
def test_read_and_final_errors_close_and_hide_reasons(calculation_case, monkeypatch, position, error, status):
    app, _, _, farm, trace, state = assembly(calculation_case, monkeypatch); state[position] = error
    actual, value, _ = get(app, calculation_case[0]['result_id'], farm)
    assert actual == status and 'private' not in json.dumps(value)
    assert trace.count('open') == trace.count('close') == 1


@pytest.mark.parametrize('withdraw', ['source', 'credential', 'tenant'])
def test_withdrawal_during_projection_refuses_stale_bytes(calculation_case, monkeypatch, withdraw):
    clock = {'now': NOW}
    app, _, _, farm, trace, state = assembly(calculation_case, monkeypatch, clock=lambda: clock['now'])
    project = route.public.project_calculation_cycle_result
    def changed(*args, **kwargs):
        value = project(*args, **kwargs)
        if withdraw == 'source': state['allowed'] = False
        elif withdraw == 'credential': clock['now'] = NOW + timedelta(hours=1)
        else: state['tenant_after_read'] = 'foreign'
        return value
    monkeypatch.setattr(route.public, 'project_calculation_cycle_result', changed)
    assert get(app, calculation_case[0]['result_id'], farm)[0] == (401 if withdraw == 'credential' else 403)
    assert trace.count('current') == trace.count('close') == 1


@pytest.mark.parametrize('fault', ['store-type', 'query-type', 'missing-store', 'missing-query',
                                 'query-store', 'jobs', 'farm', 'binding-jobs', 'principal'])
def test_install_rejects_mixed_authority(calculation_case, monkeypatch, fault):
    _, store, query, _, _, _ = assembly(calculation_case, monkeypatch)
    jobs = store.jobs; farms = store.server.binding.farms; principal = current_principal
    if fault == 'store-type': store = SimpleNamespace(**store.__dict__)
    elif fault == 'query-type': query = SimpleNamespace(**query.__dict__)
    elif fault == 'missing-store': store = None
    elif fault == 'missing-query': query = None
    elif fault == 'query-store': query.store = object()
    elif fault == 'jobs': jobs = SimpleNamespace(principal_provider=principal)
    elif fault == 'farm': farms = object()
    elif fault == 'binding-jobs': store.server.binding.jobs = object()
    else: principal = lambda: None
    with pytest.raises(ValueError, match='^trusted calculation cycle reader required$'):
        route.install_calculation_cycle_routes(FastAPI(), jobs=jobs, farms=farms, store=store, query=query,
            principal_provider=principal, authorized_tenant=lambda *_: None, error=_error, access=_access)


@pytest.mark.parametrize('kind,limit', [('samples', 1), ('events', 2)])
def test_offsets_limits_and_empty_end_preserve_positions(calculation_case, monkeypatch, kind, limit):
    app, _, _, farm, trace, _ = assembly(calculation_case, monkeypatch)
    total = calculation_case[2][kind]['total']
    status, value, _ = get(app, calculation_case[0]['result_id'], farm, query=f'&view={kind}&offset=1&limit={limit}')
    assert status == 200 and value['page']['offset'] == 1 and len(value['page']['records']) == limit
    assert value['page']['next_offset'] == (1 + limit if 1 + limit < total else None)
    status, value, _ = get(app, calculation_case[0]['result_id'], farm, query=f'&view={kind}&offset={total}&limit={limit}')
    assert status == 200 and value['page']['records'] == [] and value['page']['next_offset'] is None
    assert get(app, calculation_case[0]['result_id'], farm, query=f'&view={kind}&offset={total + 1}')[0] == 422
    assert trace.count('open') == trace.count('close') == 3


@pytest.mark.parametrize('kind', ['past', 'empty'])
def test_actual_numerical_hold_preserves_only_confirmed_past(tmp_path, monkeypatch, kind):
    p = program('full-removal-reentry' if kind == 'past' else 'empty-entry')
    if kind == 'past': p['events'][1]['removals']['values']['leaf']['value'] = 1e6
    else: p['initial_state']['values']['temperature_sum']['value'] = 0
    case = saved(tmp_path, p); app, _, _, farm, trace, _ = assembly(case, monkeypatch)
    forbid_computation(monkeypatch)
    status, value, _ = get(app, case[0]['result_id'], farm)
    assert status == 200 and value['reference']['status'] == 'hold'
    assert _canonical(value['summary']['hold']['last_confirmed']) == _canonical(case[1]['last_confirmed'])
    for view in ('samples', 'events'):
        status, value, _ = get(app, case[0]['result_id'], farm, query='&view=' + view)
        assert status == 200 and value['page']['total'] == case[2][view]['total']
    assert trace.count('open') == trace.count('close') == 3
    save_reference('hold-' + kind + '.json', {'original_steps': case[1]['steps'],
        'original_sample_count': case[2]['samples']['total'], 'original_event_count': case[2]['events']['total'],
        'same_confirmed_past_UTC': True, 'parser_context_QC_RHS_forbidden': True})


def test_create_app_forwards_explicit_new_readers(monkeypatch):
    jobs = _SchemaOnlyStores(); store = object(); query = object(); seen = []
    monkeypatch.setattr(api, 'install_calculation_cycle_routes', lambda *args, **kwargs: seen.append(kwargs))
    create_app(jobs, jobs, jobs, jobs, principal_provider=current_principal,
        crop_cycle_calculation_result_store=store, crop_cycle_calculation_current_query=query)
    assert len(seen) == 1 and seen[0]['store'] is store and seen[0]['query'] is query
    assert seen[0]['jobs'] is jobs and seen[0]['principal_provider'] is current_principal


def test_openapi_declares_closed_new_provenance_and_existing_paging():
    doc = contract_document(); operation = doc['paths'][PATH + '{result_id}']['get']
    assert operation['operationId'] == 'getCalculationCycleCropResearchResult'
    assert operation['x-ossf-required-scopes'] == list(READ_SCOPES)
    params = {p['name']: p for p in operation['parameters']}
    assert params['result_id']['schema']['pattern'] == route.public.RESULT_ID_PATTERN
    assert params['offset']['schema']['maximum'] == 131072
    schemas = doc['components']['schemas']
    for name in ('CalculationCycleCropReplay', 'CalculationCycleCropReference', 'CalculationInputValidation',
                 'CalculationManifestValidation', 'InputEvidenceDependencies'):
        assert schemas[name]['additionalProperties'] is False
    assert schemas['CalculationCycleCropReference']['properties']['gates']['const'] == 'not_assessed'
    assert schemas['CycleSamplePage']['properties']['records']['maxItems'] == 64
    assert schemas['CycleEventPage']['properties']['records']['maxItems'] == 8


def save_reference(name, value):
    root = os.environ.get('OSSF_CALCULATION_ROUTE_EVIDENCE')
    if root:
        with (Path(root)/name).open('x') as handle:
            os.fchmod(handle.fileno(), 0o400); json.dump(value, handle, sort_keys=True, indent=2)
            handle.write('\n'); handle.flush(); os.fsync(handle.fileno())


@pytest.mark.parametrize('first', ['app.api', 'app.api_crop_cycle_calculation_route', 'app.calculation_operator_config'])
def test_fresh_python_keeps_new_calculation_modules_unloaded(first):
    code = '''import importlib,json,os,sys
before=len(os.listdir('/proc/self/fd'))
importlib.import_module(sys.argv[1])
from app.api_openapi import contract_document
assert '/v1/crop-cycle-calculation-research-results/{result_id}' in contract_document()['paths']
forbidden=['app.crop_cycle_calculation_context','app.crop_cycle_calculation_result_store','app.crop_cycle_calculation_current_query']
assert all(name not in sys.modules for name in forbidden)
assert before==len(os.listdir('/proc/self/fd'))
print(json.dumps({'first':sys.argv[1],'fd_before':before,'fd_after':len(os.listdir('/proc/self/fd')),'new_calculation_store_query_modules_loaded':False}))
'''
    child = subprocess.run([sys.executable, '-c', code, first], capture_output=True, text=True, timeout=30)
    assert child.returncode == 0 and child.stderr == ''
    save_reference('import-' + first.rsplit('.', 1)[-1] + '.json', {'exit_code': 0, **json.loads(child.stdout)})
