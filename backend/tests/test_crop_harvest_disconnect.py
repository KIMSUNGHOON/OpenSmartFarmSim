"""Disconnect control flow; native TLS evidence is recorded separately."""
import asyncio
import json
from urllib.parse import urlencode

import pytest

from test_api_crop_harvest_route import assembly, source, TOKEN, PATH
from test_crop_harvest_current_query import forbid_all_reads_math


async def disconnected_request(case, messages, *, canceled=False):
    sent = []
    pending = iter(messages)

    async def receive():
        if canceled:
            raise asyncio.CancelledError()
        return next(pending)

    async def send(message):
        sent.append(message)

    path = PATH + case.result_id
    await case.app({'type': 'http', 'asgi': {'version': '3.0'}, 'method': 'GET',
        'path': path, 'raw_path': path.encode(), 'root_path': '',
        'query_string': urlencode(case.farm).encode(),
        'headers': [(b'authorization', b'Bearer ' + TOKEN), (b'content-length', b'1')],
        'scheme': 'https', 'http_version': '1.1', 'server': ('test', 443),
        'client': ('test', 1234)}, receive, send)
    start = next(item for item in sent if item['type'] == 'http.response.start')
    raw = b''.join(item.get('body', b'') for item in sent if item['type'] == 'http.response.body')
    return start['status'], json.loads(raw), dict(start['headers'])


@pytest.mark.parametrize('prefix', [[], [{'type': 'http.request', 'body': b'', 'more_body': True}]])
def test_disconnect_before_complete_body_rejects_without_opening_result(source, monkeypatch, prefix):
    case = assembly(source, monkeypatch)
    forbid_all_reads_math(monkeypatch)
    status, value, headers = asyncio.run(disconnected_request(
        case, [*prefix, {'type': 'http.disconnect'}]))
    assert status == 422 and value == {'error': {'code': 'invalid_request', 'message': 'Invalid request'}}
    assert headers[b'cache-control'] == b'no-store'
    assert 'open' not in case.trace and case.trace.count('account') == 1


def test_task_cancellation_during_body_receive_is_not_converted_to_a_response(source, monkeypatch):
    case = assembly(source, monkeypatch)
    forbid_all_reads_math(monkeypatch)
    with pytest.raises(asyncio.CancelledError):
        asyncio.run(disconnected_request(case, [], canceled=True))
    assert 'open' not in case.trace
