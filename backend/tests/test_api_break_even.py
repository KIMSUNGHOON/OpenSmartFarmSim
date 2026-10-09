"""Conditional grid display with synthetic source records."""
import asyncio
from dataclasses import replace
from decimal import Decimal
import json
from pathlib import Path
import sys
from urllib.parse import urlsplit
import pytest
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from app.api import create_app
from app.api_break_even import project_break_even_result
from app.break_even import BreakEvenRequest, BreakEvenService
from test_api_job_status import UnusedMarketResultStore, UnusedThermalRunStore
from test_api_market_hold import UnusedJobStore
from test_api_thermal_run import UnusedMarketHoldStore
from test_break_even import trial_plan, saved_break_even


def get(app, url):
    parts = urlsplit(url)
    async def call():
        sent = []
        async def receive(): return {'type': 'http.request', 'body': b'', 'more_body': False}
        async def send(message): sent.append(message)
        await app({'type': 'http', 'asgi': {'version': '3.0'}, 'method': 'GET',
            'path': parts.path, 'raw_path': parts.path.encode(), 'root_path': '',
            'query_string': parts.query.encode(), 'headers': [], 'scheme': 'https',
            'http_version': '1.1', 'server': ('test', 443), 'client': ('test', 1234)}, receive, send)
        start = next(item for item in sent if item['type'] == 'http.response.start')
        return start['status'], json.loads(b''.join(item.get('body', b'') for item in sent if item['type'] == 'http.response.body'))
    return asyncio.run(call())


def app_for(store, principal):
    return create_app(UnusedJobStore(), UnusedMarketHoldStore(), UnusedThermalRunStore(),
        UnusedMarketResultStore(), principal_provider=lambda: principal, break_even_store=store)


@pytest.mark.parametrize('target', ['oi', 'operating_cash', 'cumulative_equity_cash'])
@pytest.mark.parametrize('variable,values', [('KRW/kg', [20, 26, 32]), ('kg', [2, 3, 4])])
def test_projection_preserves_target_units_values_and_conditional_scope(target, variable, values):
    repo, raw = trial_plan(values, target=target, variable=variable)
    request = BreakEvenRequest.model_validate(raw)
    result = BreakEvenService(repo).scan(request, 'tenant-1')
    public = project_break_even_result(request, result).model_dump(mode='json')
    assert public['target'] == target and public['variable_unit'] == variable
    assert public['assessment_status'] == 'hold' and public['scope'] == 'conditional_user_grid_only'
    assert public['market_hold_report_id'] == request.market_context.hold_report_id
    assert public['input_origin'] == 'user' and public['evidence_level'] == 'assumed'
    assert public['zero_values'] == [format(value, 'f') for value in result.zero_values]
    assert [item['target_value_krw'] for item in public['trials']] == [format(item.target_value, 'f') for item in result.trials]
    assert not {'tenant_id', 'sale_id', 'batch_id', 'request_sha256'} & public.keys()
    assert all('scenario_id' not in item for item in public['trials'])


@pytest.mark.parametrize('values,status', [([20, 25, 30], 'bracket_only'), ([30, 31, 32], 'no_zero_on_grid')])
def test_projection_preserves_grid_brackets_and_no_grid_zero(values, status):
    repo, raw = trial_plan(values)
    request = BreakEvenRequest.model_validate(raw)
    result = BreakEvenService(repo).scan(request, 'tenant-1')
    public = project_break_even_result(request, result)
    assert public.status == status and public.zero_values == []
    assert public.brackets == [[format(v, 'f') for v in pair] for pair in result.brackets]


def test_projection_preserves_unknowns_withholds_details_and_rejects_bad_claims():
    repo, raw = trial_plan([20, 26, 32])
    request = BreakEvenRequest.model_validate(raw)
    result = BreakEvenService(repo).scan(request, 'tenant-1')
    held = replace(result, status='hold', zero_values=(), brackets=(), trials=(), hold_reasons=('TARGET_UNRESOLVED', 'private sale details'))
    public = project_break_even_result(request, held)
    assert public.trials == [] and public.hold_reason_codes == ['TARGET_UNRESOLVED', 'DETAIL_WITHHELD']
    unknown = replace(result, trials=(replace(result.trials[0], minimum_cash_balance=None, cash_shortage=Decimal('0')), *result.trials[1:]))
    public = project_break_even_result(request, unknown)
    assert public.trials[0].minimum_cash_balance_krw is None and public.trials[0].cash_shortage_krw == '0'
    for changed in (replace(result, assessment_status='pass'), replace(result, target='future_margin'),
                    replace(result, minimum=Decimal('NaN')), replace(result, trials=(replace(result.trials[0], target_value=1.0),))):
        with pytest.raises(ValueError): project_break_even_result(request, changed)


def test_http_replays_pinned_result_and_checks_each_tenant(saved_break_even):
    factory, source, raw, principal = saved_break_even
    pinned = factory().pin_break_even_plan(raw, source.break_even_plan)
    app = app_for(factory(), principal)
    path = '/v1/break-even-results?plan_id='+raw['plan_id']
    status, body = get(app, path)
    assert status == 200 and body['status'] == pinned.status and body['zero_values'] == ['26']
    assert body['assessment_status'] == 'hold' and body['variable_unit'] == 'KRW/kg'
    assert factory().get_break_even_read('foreign-tenant', raw['plan_id']) is None
    principal['tenant_id'] = 'tenant-2'
    assert get(app, path)[0] == 404
    principal['tenant_id'] = 'tenant-1'
    principal['scopes'].remove('break_even_read')
    assert get(app, path)[0] == 403
    principal['scopes'].add('break_even_read')
    principal['authenticated'] = False
    assert get(app, path)[0] == 401
    principal['authenticated'] = True
    assert get(app, '/v1/break-even-results?plan_id=missing')[0] == 404
    assert get(app, '/v1/break-even-results')[0] == 422
    assert get(app, '/v1/break-even-results?plan_id='+ 'x'*201)[0] == 422
    source.rights.clear()
    assert get(app, path) == (503, {'error': {'code': 'store_unavailable', 'message': 'Break-even result unavailable'}})


def test_http_generic_errors_and_request_identity():
    principal = {'authenticated': True, 'tenant_id': 'tenant-1', 'scopes': {'break_even_read'}}
    repo, raw = trial_plan([20, 26, 32])
    request = BreakEvenRequest.model_validate(raw)
    result = BreakEvenService(repo).scan(request, 'tenant-1')
    class WrongStore:
        def get_break_even_read(self, *_): return request, result
    assert get(app_for(WrongStore(), principal), '/v1/break-even-results?plan_id=wrong')[0] == 503
    assert get(app_for(None, principal), '/v1/break-even-results?plan_id=missing')[0] == 503
    with pytest.raises(ValueError): app_for(object(), principal)


def test_nonmonotone_grid_status_is_preserved():
    repo, raw = trial_plan([20, 26, 32], target='operating_cash', collection_overrides={1:'0'})
    request = BreakEvenRequest.model_validate(raw)
    result = BreakEvenService(repo).scan(request, 'tenant-1')
    assert project_break_even_result(request, result).status == 'nonmonotone_on_grid'


def test_query_accepts_an_existing_unicode_slash_plan_identifier(saved_break_even):
    from urllib.parse import quote
    from app.break_even import canonical_request_sha256
    factory, source, raw, principal = saved_break_even
    raw = {**raw, 'plan_id': '내부/가격 계획'}
    plan = {**source.break_even_plan, 'plan_id': raw['plan_id'], 'request_sha256': canonical_request_sha256(raw)}
    factory().pin_break_even_plan(raw, plan)
    status, public = get(app_for(factory(), principal), '/v1/break-even-results?plan_id='+quote(raw['plan_id'], safe=''))
    assert status == 200 and public['plan_id'] == raw['plan_id']
