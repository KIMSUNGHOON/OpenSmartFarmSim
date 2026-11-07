"""First genuine protected manifest GET; HTTPS-scheme ASGI is not TLS evidence."""
import asyncio
from datetime import datetime, timedelta, timezone
from hashlib import sha256
import os
import secrets
from types import SimpleNamespace

from fastapi import FastAPI

from app.content_access import ContentAccess
from app.http_identity import BearerGrant, BearerRegistry, PrincipalMiddleware, current_principal, token_digest
import test_crop_supply_material_repeat_artifact as artifact_cases
from test_crop_supply_material_repeat_artifact import (
    source, origin, seed_before_repeat, first_parent, first_artifact,
)


PINNED_SOURCES = {
    'backend/app/crop_supply_material_repeat_artifact_producer.py': '10aa0ae2dac7a7b996229a59edeb62d2a5f7dff3418b7ee41079cb6faf9101b8',
    'backend/app/crop_supply_material_repeat_artifact_reader.py': 'f21370bf89967679b7b4da68934c353d5056ed68bc1ccac5ad1c581242b4d881',
    'backend/app/crop_supply_material_repeat_owner.py': '100433a72717d765705dfba7845896f03477e1074578eacd8bbc11c0ba1c1b87',
    'backend/app/crop_supply_material_repeat_point.py': '7c51dabdf6d71987df91ad37ee583b9f22c21fbe5e85486db763356920b19a16',
    'backend/app/crop_supply_material_repeat_proof.py': '5eecc2cf937f5d052069a1d32edaa25b099cda7c24b8703b9530aba4adb216a5',
    'backend/tests/test_crop_supply_material_repeat_artifact.py': '75065a0c9b83a712d2033cb8b141fb4e0388829b39ce30adb449eccc6116fae0',
    'contracts/supply-material-repeat-artifact-v1.md': '1c92bdc8a21ac170e61c69a4a1067128caf901eec297102e2155c9a6b10f6d2c',
}


async def _asgi_manifest_get(app, token):
    path = '/v1/research/material-repeat/manifest'
    received = False
    complete = asyncio.Event()
    start = None
    parts = []
    size = 0

    async def receive():
        nonlocal received
        if not received:
            received = True
            return {'type': 'http.request', 'body': b'', 'more_body': False}
        await complete.wait()
        return {'type': 'http.disconnect'}

    async def send(message):
        nonlocal start, size
        if message['type'] == 'http.response.start':
            assert start is None and not complete.is_set()
            start = {'status': message['status'], 'headers': list(message.get('headers', []))}
        else:
            assert message['type'] == 'http.response.body'
            assert start is not None and not complete.is_set()
            body = message.get('body', b'')
            assert type(body) is bytes
            size += len(body)
            assert size <= 2097152
            parts.append(body)
            if not message.get('more_body', False):
                complete.set()

    await app({'type': 'http', 'asgi': {'version': '3.0'}, 'method': 'GET',
               'path': path, 'raw_path': path.encode('ascii'), 'root_path': '',
               'query_string': b'', 'headers': [(b'host', b'repeat.test'),
                   (b'authorization', b'Bearer ' + token)], 'scheme': 'https',
               'http_version': '1.1', 'server': ('repeat.test', 443),
               'client': ('test-client', 1234), 'state': {}}, receive, send)
    assert start is not None and complete.is_set()
    return SimpleNamespace(status_code=start['status'], content=b''.join(parts),
                           headers={key.decode('latin-1').lower(): value.decode('latin-1')
                                    for key, value in start['headers']})


def test_genuine_first_artifact_manifest_get_returns_exact_protected_bytes(first_artifact):
    packet = first_artifact
    parent = packet['parent']
    directory, access, root, raw = (packet[key] for key in ('directory', 'access', 'root', 'raw'))
    assert type(parent['handle']) is artifact_cases.repeat.Handle
    assert parent['handle'].current['numeric']['schedule']['consumed_sequence'] == 13
    assert parent['handle'].current['effective_rights'] == {'use': True, 'display': True, 'redistribute': False}
    assert directory.is_absolute() and type(access) is ContentAccess
    assert type(root) is str and len(root) == 64 and set(root) <= set('0123456789abcdef')
    assert type(raw) is bytes and 1 <= len(raw) <= 2097152 and sha256(raw).hexdigest() == root
    assert (directory / root).read_bytes() == raw
    manifest = packet['manifest']
    assert artifact_cases.canonical(manifest) == raw
    assert manifest['effective_rights'] == {'use': True, 'display': True, 'redistribute': False}
    assert len(manifest['transitions']) == 1 and manifest['transitions'][0]['kind'] == 'material_adoption'
    assert [frame['phase'] for frame in manifest['frames']] == ['material_before', 'material_after']
    assert manifest['frames'][0]['at'] == manifest['frames'][1]['at']
    for relative, expected in PINNED_SOURCES.items():
        assert sha256((artifact_cases.ROOT / relative).read_bytes()).hexdigest() == expected
    for relative in PINNED_SOURCES:
        if relative.startswith('backend/app/'):
            assert manifest['code_sha256'][relative] == PINNED_SOURCES[relative]
    _, reader = artifact_cases._api()
    # A real public-reader positive is a setup gate before the new API import.
    assert reader.read_repeat_material_manifest(directory, access, root) == raw
    directories = [directory, *artifact_cases._directories(parent)]
    before = artifact_cases._inventory(directories)
    fd_before = len(os.listdir('/proc/self/fd'))
    assert current_principal() is None
    token = secrets.token_urlsafe(32).encode('ascii')
    now = datetime.now(timezone.utc)
    tenant = 'own-repeat-http-test'
    grant = BearerGrant(token_digest(token), tenant, frozenset({'metadata', 'artifact'}),
                        now - timedelta(seconds=1), now + timedelta(minutes=5))
    registry = BearerRegistry((grant,))
    try:
        # The feature-absence RED must reach this line after genuine fixture/read gates.
        from app.api_supply_material_repeat import create_repeat_material_app
        app = create_repeat_material_app(directory=directory, access=access, root_sha256=root,
                                         tenant_id=tenant, registry=registry)
        assert type(app) is PrincipalMiddleware and type(app.app) is FastAPI
        assert app.registry is registry
        response = asyncio.run(_asgi_manifest_get(app, token))
        assert response.status_code == 200
        assert response.content == raw and sha256(response.content).hexdigest() == root
        assert response.headers['content-type'].split(';')[0].strip() == 'application/json'
        assert response.headers['cache-control'] == 'no-store'
        assert response.headers['x-content-type-options'] == 'nosniff'
        assert response.headers['x-frame-options'] == 'DENY'
    finally:
        assert current_principal() is None
        assert len(os.listdir('/proc/self/fd')) == fd_before
        assert artifact_cases._inventory(directories) == before
        for relative, expected in PINNED_SOURCES.items():
            assert sha256((artifact_cases.ROOT / relative).read_bytes()).hexdigest() == expected



def _fixed_delivery(packet, registry):
    from app import api_supply_material_repeat as public
    assert sha256((artifact_cases.ROOT / 'backend/app/api_supply_material_repeat.py').read_bytes()).hexdigest() == '06a3195b2996d7debac60f2f57875ba5d110201dd861578c8e5be7e4f5308ffe'
    assert sha256((artifact_cases.ROOT / 'contracts/supply-material-repeat-protected-delivery-v1.md').read_bytes()).hexdigest() == '90cebe16be7f9df6adffa471474676370675424ff4b56b68eed6a412d0474dcd'
    app = public.create_repeat_material_app(directory=packet['directory'], access=packet['access'],
        root_sha256=packet['root'], tenant_id='own-repeat-http-test', registry=registry)
    assert type(app) is PrincipalMiddleware and type(app.app) is FastAPI and app.registry is registry
    return app


async def _selected_get(app, path, headers):
    async def selected(scope, receive, send):
        assert scope['scheme'] == 'https' and scope['method'] == 'GET'
        forwarded = {**scope, 'path': path, 'raw_path': path.encode('ascii'),
                     'headers': [(b'host', b'repeat.test'), *headers]}
        await app(forwarded, receive, send)
    return await _asgi_manifest_get(selected, b'unused-transport-token')


def test_genuine_material_frame_pair_is_exact_raw_and_preserves_both_basis_sides(first_artifact):
    packet = first_artifact
    descriptors = packet['manifest']['frames']
    assert len(descriptors) == 2
    expected = []
    for index, descriptor in enumerate(descriptors):
        assert descriptor['index'] == index
        raw, value = artifact_cases._blob(packet['directory'], descriptor['frame']['sha256'])
        assert len(raw) == descriptor['frame']['bytes']
        expected.append((raw, value))
    assert [value['phase'] for _, value in expected] == ['material_before', 'material_after']
    assert expected[0][1]['at'] == expected[1][1]['at']
    assert expected[0][1]['binding']['active_basis_sha256'] != expected[1][1]['binding']['active_basis_sha256']
    assert expected[0][1]['binding']['checkpoint_cursor_sha256'] is None
    assert expected[1][1]['binding']['checkpoint_cursor_sha256'] is not None
    for row in [*expected[0][1]['leaves'], *expected[0][1]['internodes']]:
        assert row['geometry_diagnostics']['kind'] == 'dense_stored_transfers'
        assert row['geometry_diagnostics']['canonical_status'] == 'not_stored_at_dense_boundary'
        assert row['geometry_diagnostics']['canonical_gap_exact'] is None
        assert row['geometry_diagnostics']['canonical_potential_difference_exact'] is None
    for row in [*expected[1][1]['leaves'], *expected[1][1]['internodes']]:
        assert row['geometry_diagnostics']['kind'] == 'stored_confirmed'
        assert row['geometry_diagnostics']['canonical_status'] == 'stored'
        assert row['geometry_diagnostics']['canonical_gap_exact'] is not None
        assert row['geometry_diagnostics']['canonical_potential_difference_exact'] is not None
    token = secrets.token_urlsafe(32).encode('ascii')
    now = datetime.now(timezone.utc)
    grant = BearerGrant(token_digest(token), 'own-repeat-http-test', frozenset({'metadata', 'artifact'}),
                        now - timedelta(seconds=1), now + timedelta(minutes=5))
    app = _fixed_delivery(packet, BearerRegistry((grant,)))
    _, reader = artifact_cases._api()
    calls, returned = [], []

    def observe(frame, event, value):
        name = 'manifest' if frame.f_code is reader.read_repeat_material_manifest.__code__ else 'frame'
        if event == 'call':
            calls.append((name, frame.f_locals.get('index')))
        elif event == 'return':
            assert type(value) is bytes
            returned.append((name, sha256(value).hexdigest(), len(value)))

    directories = [packet['directory'], *artifact_cases._directories(packet['parent'])]
    before = artifact_cases._inventory(directories)
    fd_before = len(os.listdir('/proc/self/fd'))
    try:
        with artifact_cases.qa._watch(observe, {
                reader.read_repeat_material_manifest.__code__, reader.read_repeat_material_frame.__code__}):
            for index, (raw, _) in enumerate(expected):
                response = asyncio.run(_selected_get(app, f'/v1/research/material-repeat/frames/{index}',
                    [(b'authorization', b'Bearer ' + token)]))
                assert response.status_code == 200 and response.content == raw
                assert response.headers['content-type'].split(';')[0].strip() == 'application/json'
                assert response.headers['cache-control'] == 'no-store'
                assert calls == [('frame', value) for value in range(index + 1)]
                assert returned == [('frame', descriptors[value]['frame']['sha256'],
                                     descriptors[value]['frame']['bytes']) for value in range(index + 1)]
    finally:
        assert current_principal() is None
        assert len(os.listdir('/proc/self/fd')) == fd_before
        assert artifact_cases._inventory(directories) == before


def test_credential_and_scope_denials_do_not_enter_the_real_artifact_reader(first_artifact):
    import json
    packet = first_artifact
    now = datetime.now(timezone.utc)
    tokens = {name: secrets.token_urlsafe(32).encode('ascii')
              for name in ('good', 'tenant', 'metadata', 'artifact', 'future', 'expired', 'unknown')}
    specs = [
        ('good', 'own-repeat-http-test', {'metadata', 'artifact'}, now - timedelta(seconds=1), now + timedelta(minutes=5)),
        ('tenant', 'another-own-tenant', {'metadata', 'artifact'}, now - timedelta(seconds=1), now + timedelta(minutes=5)),
        ('metadata', 'own-repeat-http-test', {'metadata'}, now - timedelta(seconds=1), now + timedelta(minutes=5)),
        ('artifact', 'own-repeat-http-test', {'artifact'}, now - timedelta(seconds=1), now + timedelta(minutes=5)),
        ('future', 'own-repeat-http-test', {'metadata', 'artifact'}, now + timedelta(minutes=5), now + timedelta(minutes=10)),
        ('expired', 'own-repeat-http-test', {'metadata', 'artifact'}, now - timedelta(minutes=10), now - timedelta(minutes=5)),
    ]
    registry = BearerRegistry(tuple(BearerGrant(token_digest(tokens[name]), tenant, frozenset(scopes), start, end)
                                   for name, tenant, scopes, start, end in specs))
    app = _fixed_delivery(packet, registry)
    _, reader = artifact_cases._api()
    calls, returned = [], []

    def observe(frame, event, value):
        name = 'manifest' if frame.f_code is reader.read_repeat_material_manifest.__code__ else 'frame'
        if event == 'call':
            calls.append(name)
        elif event == 'return':
            assert type(value) is bytes
            returned.append((name, sha256(value).hexdigest(), len(value)))

    def authorization(name):
        return [(b'authorization', b'Bearer ' + tokens[name])]

    cases = [
        ([], 401),
        ([(b'authorization', b'Bearer short')], 401),
        (authorization('unknown'), 401),
        (authorization('good') + authorization('good'), 401),
        (authorization('future'), 401),
        (authorization('expired'), 401),
        (authorization('tenant'), 403),
        (authorization('metadata'), 403),
        (authorization('artifact'), 403),
    ]
    directories = [packet['directory'], *artifact_cases._directories(packet['parent'])]
    before = artifact_cases._inventory(directories)
    fd_before = len(os.listdir('/proc/self/fd'))
    try:
        with artifact_cases.qa._watch(observe, {
                reader.read_repeat_material_manifest.__code__, reader.read_repeat_material_frame.__code__}):
            baseline = asyncio.run(_selected_get(app, '/v1/research/material-repeat/manifest', authorization('good')))
            assert baseline.status_code == 200 and baseline.content == packet['raw']
            assert calls == ['manifest'] and returned == [('manifest', packet['root'], len(packet['raw']))]
            for headers, status in cases:
                response = asyncio.run(_selected_get(app, '/v1/research/material-repeat/manifest', headers))
                expected = ({'error': {'code': 'unauthenticated', 'message': 'Authentication required'}}
                            if status == 401 else {'error': {'code': 'forbidden', 'message': 'Resource access denied'}})
                assert response.status_code == status
                assert json.loads(response.content) == expected
                assert response.headers['cache-control'] == 'no-store'
                if status == 401:
                    assert response.headers['www-authenticate'] == 'Bearer'
                assert calls == ['manifest'] and returned == [('manifest', packet['root'], len(packet['raw']))]
            recovered = asyncio.run(_selected_get(app, '/v1/research/material-repeat/manifest', authorization('good')))
            assert recovered.status_code == 200 and recovered.content == packet['raw']
            assert calls == ['manifest', 'manifest']
            assert returned == [('manifest', packet['root'], len(packet['raw']))] * 2
    finally:
        assert current_principal() is None
        assert len(os.listdir('/proc/self/fd')) == fd_before
        assert artifact_cases._inventory(directories) == before



async def _request_shape(app, token, *, path='/v1/research/material-repeat/manifest',
                         raw_path=None, query=b'', body=b'', method='GET', extra_headers=()):
    async def shaped(scope, receive, send):
        async def shaped_receive():
            message = await receive()
            if message['type'] == 'http.request':
                assert message.get('body', b'') == b'' and not message.get('more_body', False)
                message = {**message, 'body': body}
            return message
        forwarded = {**scope, 'method': method, 'path': path,
            'raw_path': path.encode('ascii') if raw_path is None else raw_path,
            'query_string': query, 'headers': [(b'host', b'repeat.test'),
                (b'authorization', b'Bearer ' + token), *extra_headers]}
        await app(forwarded, shaped_receive, send)
    return await _asgi_manifest_get(shaped, b'unused-transport-token')


def test_request_syntax_rejects_before_read_and_unavailable_admitted_frame_holds_after_real_reconstruction(first_artifact):
    import json
    packet = first_artifact
    frame_raw = [artifact_cases._blob(packet['directory'], descriptor['frame']['sha256'])[0]
                 for descriptor in packet['manifest']['frames']]
    assert len(frame_raw) == 2
    token = secrets.token_urlsafe(32).encode('ascii')
    now = datetime.now(timezone.utc)
    grant = BearerGrant(token_digest(token), 'own-repeat-http-test', frozenset({'metadata', 'artifact'}),
                        now - timedelta(seconds=1), now + timedelta(minutes=5))
    app = _fixed_delivery(packet, BearerRegistry((grant,)))
    _, reader = artifact_cases._api()
    calls, returned, loaded = [], [], []

    def observe(frame, event, value):
        if frame.f_code is reader._load.__code__:
            if event == 'return':
                assert type(value) is tuple and len(value) == 4
                assert value[0] == packet['raw'] and value[1] == frame_raw
                loaded.append(True)
        else:
            name = 'manifest' if frame.f_code is reader.read_repeat_material_manifest.__code__ else 'frame'
            if event == 'call':
                calls.append((name, frame.f_locals.get('index')))
            elif event == 'return' and type(value) is bytes:
                returned.append((name, sha256(value).hexdigest()))

    cases = [
        ({'path': '/v1/research/material-repeat/frames/01'}, 422, 'invalid_request', 'Invalid request'),
        ({'path': '/v1/research/material-repeat/frames/512'}, 422, 'invalid_request', 'Invalid request'),
        ({'path': '/v1/research/material-repeat/frames/1.0'}, 422, 'invalid_request', 'Invalid request'),
        ({'path': '/v1/research/material-repeat/frames/0',
          'raw_path': b'/v1/research/material-repeat/frames/%30'}, 422, 'invalid_request', 'Invalid request'),
        ({'query': b'extra=1'}, 422, 'invalid_request', 'Invalid request'),
        ({'body': b'x'}, 422, 'invalid_request', 'Invalid request'),
        ({'extra_headers': [(b'range', b'bytes=0-1')]}, 422, 'invalid_request', 'Invalid request'),
        ({'method': 'HEAD'}, 405, 'method_not_allowed', 'Method not allowed'),
        ({'method': 'POST'}, 405, 'method_not_allowed', 'Method not allowed'),
        ({'path': '/v1/research/material-repeat/unknown'}, 404, 'not_found', 'Resource not found'),
    ]
    directories = [packet['directory'], *artifact_cases._directories(packet['parent'])]
    before = artifact_cases._inventory(directories)
    fd_before = len(os.listdir('/proc/self/fd'))
    try:
        with artifact_cases.qa._watch(observe, {reader.read_repeat_material_manifest.__code__,
                reader.read_repeat_material_frame.__code__, reader._load.__code__}):
            baseline = asyncio.run(_request_shape(app, token, path='/v1/research/material-repeat/frames/0'))
            assert baseline.status_code == 200 and baseline.content == frame_raw[0]
            assert calls == [('frame', 0)] and returned == [('frame', sha256(frame_raw[0]).hexdigest())]
            assert loaded == [True]
            for options, status, code, message in cases:
                response = asyncio.run(_request_shape(app, token, **options))
                assert response.status_code == status
                assert json.loads(response.content) == {'error': {'code': code, 'message': message}}
                assert response.headers['cache-control'] == 'no-store'
                assert calls == [('frame', 0)] and returned == [('frame', sha256(frame_raw[0]).hexdigest())]
                assert loaded == [True]
            unavailable = asyncio.run(_request_shape(app, token, path='/v1/research/material-repeat/frames/2'))
            assert unavailable.status_code == 422
            assert json.loads(unavailable.content) == {'error': {'code': 'repeat_material_hold',
                                                               'message': 'Repeat material evidence unavailable'}}
            assert calls == [('frame', 0), ('frame', 2)] and loaded == [True, True]
            assert returned == [('frame', sha256(frame_raw[0]).hexdigest())]
            recovered = asyncio.run(_request_shape(app, token, path='/v1/research/material-repeat/frames/1'))
            assert recovered.status_code == 200 and recovered.content == frame_raw[1]
            assert calls == [('frame', 0), ('frame', 2), ('frame', 1)] and loaded == [True, True, True]
            assert returned == [('frame', sha256(frame_raw[0]).hexdigest()), ('frame', sha256(frame_raw[1]).hexdigest())]
    finally:
        assert current_principal() is None
        assert len(os.listdir('/proc/self/fd')) == fd_before
        assert artifact_cases._inventory(directories) == before


import json as _tls_json
import ssl as _tls_ssl
import threading as _tls_threading
import time as _tls_time
from contextlib import contextmanager as _tls_contextmanager

import pytest as _tls_pytest
from test_api_serve import tls_files as _tls_files


def _tls_context(cert=None):
    context = _tls_ssl.SSLContext(_tls_ssl.PROTOCOL_TLS_CLIENT)
    context.minimum_version = _tls_ssl.TLSVersion.TLSv1_2
    context.verify_mode = _tls_ssl.CERT_REQUIRED
    context.check_hostname = True
    if cert is not None:
        context.load_verify_locations(cafile=str(cert))
    assert context.verify_mode == _tls_ssl.CERT_REQUIRED and context.check_hostname
    assert context.keylog_filename is None
    return context


async def _tls_get(port, context, path, token=None, *, incomplete_body=False):
    loop = asyncio.get_running_loop()
    writer = None
    socket = None
    started = loop.time()
    deadline = started + 30.0
    phase = 'connecting'

    def current():
        if loop.time() >= deadline:
            raise TimeoutError('absolute TLS client deadline reached')

    try:
        try:
            async with asyncio.timeout_at(deadline):
                stream, writer = await asyncio.open_connection(
                    '127.0.0.1', port, ssl=context, server_hostname='127.0.0.1', limit=8192)
                socket = writer.get_extra_info('socket')
                current()
                negotiated = writer.get_extra_info('ssl_object')
                assert negotiated is not None and negotiated.version() in {'TLSv1.2', 'TLSv1.3'}
                headers = [b'GET ' + path.encode('ascii') + b' HTTP/1.1',
                           b'Host: 127.0.0.1', b'Connection: close']
                if token is not None:
                    headers.append(b'Authorization: Bearer ' + token)
                if incomplete_body:
                    headers.append(b'Content-Length: 1')
                writer.write(b'\r\n'.join(headers) + b'\r\n\r\n')
                await writer.drain()
                current()
                phase = 'await_headers'
                head = await stream.readuntil(b'\r\n\r\n')
                current()
                phase = 'response_body'
                assert len(head) <= 8192
                lines = head[:-4].split(b'\r\n')
                status = lines[0].split(b' ', 2)
                assert len(status) == 3 and status[0] == b'HTTP/1.1'
                assert len(status[1]) == 3 and status[1].isdigit()
                fields = {}
                for line in lines[1:]:
                    key, separator, value = line.partition(b':')
                    assert separator and key and not key[:1].isspace()
                    name = key.decode('ascii').lower()
                    assert name not in fields
                    fields[name] = value.strip().decode('ascii')
                assert not {'transfer-encoding', 'content-encoding', 'content-disposition', 'location'} & fields.keys()
                declared = fields['content-length']
                assert declared.isascii() and declared.isdecimal() and str(int(declared)) == declared
                length = int(declared)
                assert 1 <= length <= 2097152
                raw = await stream.readexactly(length)
                current()
                phase = 'await_eof'
                extra = await stream.read(1)
                current()
                assert extra == b''
                elapsed = loop.time() - started
                assert elapsed < 30.0
                return SimpleNamespace(status_code=int(status[1]), headers=fields,
                                       content=raw, seconds=elapsed)
        except TimeoutError as error:
            elapsed = loop.time() - started
            assert elapsed >= 30.0, 'not the complete-operation client deadline'
            error._ossf_tls_client_deadline = True
            error._ossf_tls_client_phase = phase
            error._ossf_tls_client_seconds = elapsed
            raise
    finally:
        if writer is not None:
            writer.close()
            try:
                await asyncio.wait_for(writer.wait_closed(), timeout=15.0)
            except TimeoutError:
                writer.transport.abort()
                await asyncio.sleep(0)
                raise AssertionError('TLS client cleanup did not finish') from None
            except (ConnectionResetError, BrokenPipeError):
                pass
            assert socket is not None and socket.fileno() == -1, 'TLS client socket remains open'


@_tls_contextmanager
def _tls_served(server):
    failures = []

    def run():
        try:
            server.run()
        except BaseException as error:
            failures.append(type(error).__name__)

    thread = _tls_threading.Thread(target=run, name='own-repeat-tls', daemon=False)
    thread.start()
    try:
        ready_by = _tls_time.monotonic() + 10.0
        while not server.started:
            assert thread.is_alive() and _tls_time.monotonic() < ready_by, 'owned TLS service did not start'
            _tls_time.sleep(0.01)
        assert not failures and len(server.servers) == 1
        sockets = server.servers[0].sockets
        assert len(sockets) == 1 and sockets[0].getsockname()[0] == '127.0.0.1'
        port = sockets[0].getsockname()[1]
        assert 0 < port < 65536
        yield port
    finally:
        server.should_exit = True
        # An unsuccessful client may leave the unchanged reader60 draining.
        thread.join(60.0 + 15.0)
        assert not thread.is_alive(), 'owned TLS service or reader did not drain'
        assert not failures, 'owned TLS service failed'
        assert all(not listener.sockets for listener in getattr(server, 'servers', ()))


def _tls_forbidden_entries():
    from app.job_store import JobStore
    from app.crop_morphology_artifact_io import MorphologyBlobStore
    from app import crop_supply_material_repeat_owner as owner
    from app import crop_supply_material_repeat_point as point
    from app import crop_leaf_area as leaf_curve
    from app import crop_internode_length as length_curve
    qa = artifact_cases.qa
    return [
        (qa.base.stage.evaluate, (None,) * 5, {}),
        (qa.point.apply_material_point, (None,) * 3, {'inputs': None}),
        (qa.candidate.calculate_threshold_state, (None,) * 3, {}),
        (point.calculate_successor_candidate, (None,) * 3, {}),
        (point.apply_successor_material_point, (None,) * 3, {'inputs': None}),
        (owner.adopt_successor, (None,) * 3,
         {'inputs': None, 'expected_point_sha256': None, 'workspace': None}),
        (MorphologyBlobStore.put, (None, b''), {'maximum': 1}),
        (JobStore.connect, (None,), {}),
        (JobStore._durable_content, (None, b'', '0' * 64), {}),
        (leaf_curve._area_at, (None, None), {}),
        (leaf_curve.calculate_leaf_area_point, (), {'inputs': None}),
        (length_curve._length_at_thermal_age, (None, None), {}),
        (length_curve.calculate_internode_length_point, (), {'inputs': None}),
    ]


class _TlsEntrySeen(BaseException):
    pass


def test_verified_tls_manifest_and_frame_obey_absolute_client30_and_timeout_drains(first_artifact, _tls_files, request):
    packet = first_artifact
    certificate, key, _ = _tls_files
    assert certificate.parent.stat().st_mode & 0o777 == 0o700
    assert key.stat().st_mode & 0o777 == 0o600
    assert packet['manifest']['effective_rights'] == {'use': True, 'display': True, 'redistribute': False}
    descriptor = packet['manifest']['frames'][0]
    expected_frame = (packet['directory'] / descriptor['frame']['sha256']).read_bytes()
    assert len(expected_frame) == descriptor['frame']['bytes']
    assert sha256(expected_frame).hexdigest() == descriptor['frame']['sha256']
    assert descriptor['index'] == 0 and descriptor['phase'] == 'material_before'
    token = secrets.token_urlsafe(32).encode('ascii')
    now = datetime.now(timezone.utc)
    grant = BearerGrant(token_digest(token), 'own-repeat-http-test', frozenset({'metadata', 'artifact'}),
                        now - timedelta(seconds=1), now + timedelta(minutes=5))
    app = _fixed_delivery(packet, BearerRegistry((grant,)))
    trust, untrusted = _tls_context(certificate), _tls_context()
    assert untrusted.get_ca_certs() == []
    _, reader = artifact_cases._api()
    reads = {reader.read_repeat_material_manifest.__code__: 'manifest',
             reader.read_repeat_material_frame.__code__: 'frame'}
    entries = _tls_forbidden_entries()
    forbidden_codes = {function.__code__ for function, _, _ in entries}
    assert len(forbidden_codes) == 13 and not forbidden_codes & reads.keys()
    phase, expected_code = 'control', None
    controls, forbidden, calls, returned = [], [], [], []

    def observe(frame, event, value):
        if frame.f_code in forbidden_codes:
            if event != 'call':
                return
            if phase == 'control':
                assert frame.f_code is expected_code
                controls.append(frame.f_code)
                raise _TlsEntrySeen()
            forbidden.append(frame.f_code.co_name)
            raise AssertionError('TLS stored read entered a forbidden generation/storage boundary')
        name = reads[frame.f_code]
        if event == 'call':
            calls.append((name, frame.f_locals.get('index')))
        elif event == 'return':
            assert type(value) is bytes
            returned.append((name, len(value), sha256(value).hexdigest()))

    def positive_controls():
        nonlocal expected_code
        for function, args, kwargs in entries:
            expected_code = function.__code__
            before = len(controls)
            with _tls_pytest.raises(_TlsEntrySeen):
                function(*args, **kwargs)
            assert len(controls) == before + 1

    def headers(response):
        assert response.headers['content-type'].split(';')[0].strip() == 'application/json'
        assert response.headers['cache-control'] == 'no-store'
        assert response.headers['x-content-type-options'] == 'nosniff'
        assert response.headers['x-frame-options'] == 'DENY'
        assert response.headers['strict-transport-security'] == 'max-age=31536000'

    directories = [packet['directory'], *artifact_cases._directories(packet['parent'])]
    before = artifact_cases._inventory(directories)
    source_pins = {relative: sha256((artifact_cases.ROOT / relative).read_bytes()).hexdigest()
                   for relative in [*PINNED_SOURCES, 'backend/app/api_supply_material_repeat.py',
                                    'backend/app/http_identity.py', 'backend/app/https_service.py',
                                    'backend/app/content_access.py',
                                    'contracts/supply-material-repeat-protected-delivery-v1.md']}
    from app.https_service import HttpsApiService
    import stat as _tls_stat
    _logging_plugin = request.config.pluginmanager.get_plugin('logging-plugin')
    _logging_handler = getattr(_logging_plugin, 'log_file_handler', None)
    _logging_stream = getattr(_logging_handler, 'stream', None)
    _logging_owner = {'state': 'unavailable'}
    if _logging_stream is not None:
        try:
            _logging_fd = _logging_stream.fileno()
            _logging_info = os.fstat(_logging_fd)
        except (OSError, ValueError, AttributeError):
            pass
        else:
            _logging_owner = {'state': 'observed', 'fd': _logging_fd,
                'handler_class': type(_logging_handler).__name__,
                'dev': _logging_info.st_dev, 'ino': _logging_info.st_ino,
                'type': _tls_stat.S_IFMT(_logging_info.st_mode)}
    server = HttpsApiService(app, certificate, key, port=0).server()
    if _logging_owner['state'] == 'observed':
        _logging_owner['same_stream_closed_after_configuration'] = _logging_stream.closed
        _logging_owner['handler_stream_cleared_after_configuration'] = _logging_handler.stream is None
        try:
            _logging_after = os.fstat(_logging_fd)
        except OSError as error:
            _logging_owner['descriptor_errno_after_configuration'] = error.errno
        else:
            _logging_owner['descriptor_after_configuration'] = {
                'dev': _logging_after.st_dev, 'ino': _logging_after.st_ino,
                'type': _tls_stat.S_IFMT(_logging_after.st_mode)}
    print(_tls_json.dumps({'repeat_tls_bootstrap_logging': _logging_owner,
        'measured_FD_scope': 'after_configuration_before_thread_through_join',
        'constructor_global_handler_preservation_claimed': False}, sort_keys=True))
    fd_before = len(os.listdir('/proc/self/fd'))
    manifest_seconds = frame_seconds = timeout_seconds = None
    try:
        with artifact_cases.qa._watch(observe, forbidden_codes | reads.keys()):
            positive_controls()
            phase = 'tls'
            with _tls_served(server) as port:
                with _tls_pytest.raises(_tls_ssl.SSLCertVerificationError):
                    asyncio.run(_tls_get(port, untrusted, '/v1/research/material-repeat/manifest'))
                assert calls == [] and returned == [] and forbidden == []
                denied = asyncio.run(_tls_get(port, trust, '/v1/research/material-repeat/manifest'))
                assert denied.status_code == 401
                assert _tls_json.loads(denied.content) == {'error': {
                    'code': 'unauthenticated', 'message': 'Authentication required'}}
                assert denied.headers['www-authenticate'] == 'Bearer'
                headers(denied)
                assert calls == [] and returned == [] and forbidden == []
                manifest = asyncio.run(_tls_get(port, trust, '/v1/research/material-repeat/manifest', token))
                exact_manifest = manifest.content == packet['raw'] and sha256(manifest.content).hexdigest() == packet['root']
                assert manifest.status_code == 200 and exact_manifest
                headers(manifest)
                manifest_seconds = manifest.seconds
                assert calls == [('manifest', None)]
                assert returned == [('manifest', len(packet['raw']), packet['root'])]
                frame = asyncio.run(_tls_get(port, trust, '/v1/research/material-repeat/frames/0', token))
                exact_frame = frame.content == expected_frame and sha256(frame.content).hexdigest() == descriptor['frame']['sha256']
                assert frame.status_code == 200 and exact_frame
                headers(frame)
                frame_seconds = frame.seconds
                expected_calls = [('manifest', None), ('frame', 0)]
                expected_returns = [('manifest', len(packet['raw']), packet['root']),
                                    ('frame', len(expected_frame), descriptor['frame']['sha256'])]
                assert calls == expected_calls and returned == expected_returns and forbidden == []
                with _tls_pytest.raises(TimeoutError) as caught:
                    asyncio.run(_tls_get(port, trust, '/v1/research/material-repeat/manifest', token,
                                         incomplete_body=True))
                assert getattr(caught.value, '_ossf_tls_client_deadline', False) is True
                assert caught.value._ossf_tls_client_phase == 'await_headers'
                timeout_seconds = caught.value._ossf_tls_client_seconds
                assert timeout_seconds >= 30.0
                assert calls == expected_calls and returned == expected_returns and forbidden == []
            phase = 'control'
            positive_controls()
            assert len(controls) == 26 and forbidden == []
    finally:
        assert current_principal() is None
        assert len(os.listdir('/proc/self/fd')) == fd_before
        assert artifact_cases._inventory(directories) == before
        for relative, expected in source_pins.items():
            assert sha256((artifact_cases.ROOT / relative).read_bytes()).hexdigest() == expected
    print(_tls_json.dumps({'repeat_tls_client30': {
        'manifest_seconds': manifest_seconds, 'frame0_seconds': frame_seconds,
        'incomplete_body_timeout_seconds': timeout_seconds, 'verified_TLS': True,
        'client_attempts': 5, 'real_reader_calls': len(calls), 'reader_normal_returns': len(returned),
        'before_body_controls': len(controls), 'forbidden_entries': len(forbidden),
        'FD_scope': 'after_configuration_before_thread_through_join',
        'FD_before_after': [fd_before, len(os.listdir('/proc/self/fd'))],
        'service_joined': True, 'inventories_and_source_pins_unchanged': True,
        'protected_delivery_accepted': False}}, sort_keys=True))



def test_late_bearer_expiry_during_real_load_and_before_success_start_suppresses_bytes(first_artifact):
    import errno
    import json
    from app import api_supply_material_repeat as public

    packet = first_artifact
    _, reader = artifact_cases._api()
    token = secrets.token_urlsafe(32).encode('ascii')
    valid_at = datetime.now(timezone.utc)
    grant = BearerGrant(token_digest(token), 'own-repeat-http-test', frozenset({'metadata', 'artifact'}),
                        valid_at - timedelta(seconds=1), valid_at + timedelta(minutes=5))
    clock_value = [valid_at]

    def registry_clock():
        return clock_value[0]

    registry = BearerRegistry((grant,), clock=registry_clock)
    app = _fixed_delivery(packet, registry)
    registry_state = public._registry(registry)
    expected_principal = {'authenticated': True, 'tenant_id': grant.tenant_id, 'scopes': grant.scopes}
    records = []
    active = [None]

    def expire(record, boundary):
        assert record['expired_at'] is None
        assert current_principal() == expected_principal
        assert public._registry(registry) == registry_state
        assert public._CLOCK() < record['deadline']
        clock_value[0] = grant.expires_at
        assert current_principal() is None
        assert public._registry(registry) == registry_state
        record['expired_at'] = boundary

    def observe(frame, event, value):
        record = active[0]
        assert record is not None
        if frame.f_code is reader._load.__code__:
            if event == 'call':
                assert record['load_entries'] == 0 and record['public_entries'] == 1
                assert current_principal() == expected_principal
                store = frame.f_locals['store']
                fd = store.__dict__['_fd']
                assert type(fd) is int and os.fstat(fd).st_ino == packet['directory'].stat().st_ino
                caller = frame.f_back
                while caller is not None and not (caller.f_code.co_filename == public.__file__
                        and caller.f_code.co_name == 'checked_read'):
                    caller = caller.f_back
                assert caller is not None
                entered, finished, stopped = (caller.f_locals[key] for key in ('entered', 'finished', 'stopped'))
                assert entered.is_set() and not finished.is_set() and not stopped.is_set()
                record.update(store=store, fd=fd, entered=entered, finished=finished, stopped=stopped,
                              deadline=caller.f_locals['deadline'])
                assert public._CLOCK() < record['deadline']
                record['load_entries'] += 1
                if record['mode'] == 'load_expiry':
                    expire(record, 'real_load_entry')
            elif event == 'return':
                assert type(value) is tuple and len(value) == 4 and value[0] == packet['raw']
                assert record['store'].__dict__['_fd'] == record['fd']
                record['load_returns'] += 1
        elif frame.f_code is reader.read_repeat_material_manifest.__code__:
            if event == 'call':
                assert record['public_entries'] == 0 and current_principal() == expected_principal
                record['public_entries'] += 1
            elif event == 'return':
                assert type(value) is bytes and value == packet['raw']
                assert record['load_returns'] == 1 and record['store'].__dict__['_fd'] is None
                try:
                    os.fstat(record['fd'])
                except OSError as error:
                    assert error.errno == errno.EBADF
                else:
                    raise AssertionError('real reader descriptor is still open')
                assert public._CLOCK() < record['deadline']
                record['raw_returns'] += 1
        elif frame.f_code is public._authorized.__code__ and event == 'return':
            if value is None:
                assert current_principal() == expected_principal
                record['auth_valid'] += 1
            else:
                assert record['expired_at'] is not None and current_principal() is None
                assert value.status_code == 401
                record['auth_expired'] += 1
        elif frame.f_code is public._Release.__call__.__code__ and event == 'call':
            assert record['raw_returns'] == 1 and record['store'].__dict__['_fd'] is None
            assert record['entered'].is_set() and record['finished'].is_set() and not record['stopped'].is_set()
            assert current_principal() == expected_principal
            assert frame.f_locals['self'].request.scope['state'][public._DEADLINE] == record['deadline']
            record['release_entries'] += 1
            if record['mode'] == 'release_expiry':
                expire(record, 'real_release_entry')

    directories = [packet['directory'], *artifact_cases._directories(packet['parent'])]
    before = artifact_cases._inventory(directories)
    fd_before = len(os.listdir('/proc/self/fd'))
    try:
        with artifact_cases.qa._watch(observe, {reader.read_repeat_material_manifest.__code__,
                reader._load.__code__, public._authorized.__code__, public._Release.__call__.__code__}):
            for mode in ('baseline', 'load_expiry', 'release_expiry', 'recovery'):
                clock_value[0] = valid_at
                record = {'mode': mode, 'expired_at': None, 'public_entries': 0, 'load_entries': 0,
                          'load_returns': 0, 'raw_returns': 0, 'release_entries': 0,
                          'auth_valid': 0, 'auth_expired': 0}
                records.append(record)
                active[0] = record
                response = asyncio.run(_asgi_manifest_get(app, token))
                assert record['public_entries'] == record['load_entries'] == record['load_returns'] == record['raw_returns'] == 1
                assert record['entered'].is_set() and record['finished'].is_set() and not record['stopped'].is_set()
                assert record['store'].__dict__['_fd'] is None
                assert response.headers['cache-control'] == 'no-store'
                assert current_principal() is None and public._registry(registry) == registry_state
                if mode in ('baseline', 'recovery'):
                    assert response.status_code == 200 and response.content == packet['raw']
                    assert record['expired_at'] is None and record['auth_expired'] == 0
                    assert record['release_entries'] == 1 and record['auth_valid'] > 0
                else:
                    assert response.status_code == 401 and response.headers['www-authenticate'] == 'Bearer'
                    assert json.loads(response.content) == {'error': {'code': 'unauthenticated',
                                                                       'message': 'Authentication required'}}
                    assert response.content != packet['raw'] and record['auth_expired'] == 1
                    assert record['auth_valid'] > 0
                    assert record['expired_at'] == ('real_load_entry' if mode == 'load_expiry' else 'real_release_entry')
                    assert record['release_entries'] == (0 if mode == 'load_expiry' else 1)
        assert [record['mode'] for record in records] == ['baseline', 'load_expiry', 'release_expiry', 'recovery']
    finally:
        clock_value[0] = valid_at
        assert current_principal() is None and public._registry(registry) == registry_state
        assert len(os.listdir('/proc/self/fd')) == fd_before
        assert artifact_cases._inventory(directories) == before



async def _ownership_no_response_request(app, token, disconnected, observation):
    path = '/v1/research/material-repeat/manifest'
    received = False
    size = 0

    async def receive():
        nonlocal received
        if not received:
            received = True
            observation['body_received'] = True
            return {'type': 'http.request', 'body': b'', 'more_body': False}
        await disconnected.wait()
        observation['disconnects_received'] += 1
        return {'type': 'http.disconnect'}

    async def send(message):
        nonlocal size
        if message['type'] == 'http.response.start':
            observation['sent'].append(('start', message['status']))
        else:
            assert message['type'] == 'http.response.body'
            body = message.get('body', b'')
            assert type(body) is bytes
            size += len(body)
            assert size <= 2097152
            observation['sent'].append(('body', len(body)))

    try:
        await app({'type': 'http', 'asgi': {'version': '3.0'}, 'method': 'GET',
                   'path': path, 'raw_path': path.encode('ascii'), 'root_path': '',
                   'query_string': b'', 'headers': [(b'host', b'repeat.test'),
                       (b'authorization', b'Bearer ' + token)], 'scheme': 'https',
                   'http_version': '1.1', 'server': ('repeat.test', 443),
                   'client': ('test-client', 1234), 'state': {}}, receive, send)
    finally:
        observation['app_exited'] = True
        observation['order'].append('app_exited')


def test_cancel_and_disconnect_own_real_reader_until_cleanup_before_suppression(first_artifact):
    import errno
    import threading
    from app import api_supply_material_repeat as public

    packet = first_artifact
    _, reader = artifact_cases._api()
    token = secrets.token_urlsafe(32).encode('ascii')
    now = datetime.now(timezone.utc)
    grant = BearerGrant(token_digest(token), 'own-repeat-http-test', frozenset({'metadata', 'artifact'}),
                        now - timedelta(seconds=1), now + timedelta(minutes=5))
    registry = BearerRegistry((grant,))
    app = _fixed_delivery(packet, registry)
    registry_state = public._registry(registry)
    expected_principal = {'authenticated': True, 'tenant_id': grant.tenant_id, 'scopes': grant.scopes}
    records = []
    active = [None]

    def closed(record):
        assert record['store'].__dict__['_fd'] is None
        try:
            os.fstat(record['fd'])
        except OSError as error:
            assert error.errno == errno.EBADF
        else:
            raise AssertionError('original reader descriptor is still open')

    def within_original_deadlines(record):
        assert public._CLOCK() < record['deadline']
        assert public._CLOCK() < record['meter'].deadline

    def observe(frame, event, value):
        record = active[0]
        assert record is not None
        if frame.f_code is reader.read_repeat_material_manifest.__code__:
            if event == 'call':
                assert record['public_entries'] == 0 and current_principal() == expected_principal
                record['public_entries'] += 1
            elif event == 'return':
                assert type(value) is bytes and value == packet['raw']
                assert record['load_returns'] == 1 and current_principal() == expected_principal
                closed(record)
                within_original_deadlines(record)
                record['raw_returns'] += 1
                record['order'].append('real_raw_return_after_FD_close')
        elif frame.f_code is reader._load.__code__:
            if event == 'call':
                assert record['load_entries'] == 0 and record['public_entries'] == 1
                assert current_principal() == expected_principal
                store = frame.f_locals['store']
                assert type(store) is reader.MorphologyBlobStore and store._access is packet['access']
                assert store._write is False
                fd = store.__dict__['_fd']
                assert type(fd) is int
                held, named = os.fstat(fd), packet['directory'].stat()
                assert (held.st_dev, held.st_ino) == (named.st_dev, named.st_ino)
                caller = frame.f_back
                while caller is not None and not (caller.f_code.co_filename == public.__file__
                        and caller.f_code.co_name == 'checked_read'):
                    caller = caller.f_back
                assert caller is not None
                entered, finished, stopped = (caller.f_locals[key] for key in ('entered', 'finished', 'stopped'))
                assert entered.is_set() and not finished.is_set() and not stopped.is_set()
                record.update(store=store, fd=fd, meter=frame.f_locals['meter'], entered=entered,
                              finished=finished, stopped=stopped, deadline=caller.f_locals['deadline'])
                within_original_deadlines(record)
                record['load_entries'] += 1
                if record['mode'] in ('cancel', 'disconnect'):
                    record['order'].append('real_worker_held_with_FD')
                    record['held'].set()
                    remaining = min(record['deadline'], record['meter'].deadline) - public._CLOCK()
                    assert remaining > 0 and record['release'].wait(timeout=min(5.0, remaining))
                    within_original_deadlines(record)
                    assert not finished.is_set() and store.__dict__['_fd'] == fd
                    assert os.fstat(fd).st_ino == named.st_ino
                    record['order'].append('real_worker_released_with_FD')
            elif event == 'return':
                assert type(value) is tuple and len(value) == 4 and value[0] == packet['raw']
                assert record['store'].__dict__['_fd'] == record['fd']
                record['load_returns'] += 1
        elif frame.f_code is public._Release.__call__.__code__ and event == 'call':
            assert record['mode'] in ('baseline', 'recovery')
            assert record['raw_returns'] == 1 and record['finished'].is_set()
            record['release_entries'] += 1
        elif frame.f_code is public._Suppressed.__call__.__code__:
            assert record['mode'] == 'disconnect'
            assert record['raw_returns'] == 1 and record['finished'].is_set()
            closed(record)
            within_original_deadlines(record)
            if event == 'call':
                record['suppressed_entries'] += 1
            elif event == 'return':
                record['suppressed_returns'] += 1
                record['order'].append('real_suppressed_return')

    async def wait_for_state(record, predicate):
        stop = min(record['deadline'], record['meter'].deadline, public._CLOCK() + 5.0) if 'deadline' in record else public._CLOCK() + 5.0
        while not predicate():
            assert public._CLOCK() < stop, 'owned observation did not reach its causal boundary'
            await asyncio.sleep(0)

    async def interrupt(record):
        disconnected = asyncio.Event()
        task = asyncio.create_task(_ownership_no_response_request(app, token, disconnected, record))
        try:
            await wait_for_state(record, record['held'].is_set)
            assert record['body_received'] and record['disconnects_received'] == 0
            assert record['entered'].is_set() and not record['finished'].is_set()
            assert record['raw_returns'] == 0 and record['sent'] == []
            assert record['store'].__dict__['_fd'] == record['fd']
            assert os.fstat(record['fd']).st_ino == packet['directory'].stat().st_ino
            within_original_deadlines(record)
            if record['mode'] == 'cancel':
                assert task.cancel()
                await wait_for_state(record, record['stopped'].is_set)
                assert task.cancelling() and not task.done()
                assert record['entered'].is_set() and not record['finished'].is_set()
                assert record['store'].__dict__['_fd'] == record['fd']
                assert os.fstat(record['fd']).st_ino == packet['directory'].stat().st_ino
                assert record['sent'] == [] and not record['app_exited']
                record['order'].append('cancel_stopped_but_request_not_done')
            else:
                assert not task.done() and not record['stopped'].is_set()
                disconnected.set()
                record['order'].append('client_disconnect_available')
            within_original_deadlines(record)
            record['release'].set()
            if record['mode'] == 'cancel':
                try:
                    await task
                except asyncio.CancelledError:
                    record['order'].append('cancel_propagated')
                else:
                    raise AssertionError('actual request cancellation did not propagate')
                assert task.cancelled() and record['stopped'].is_set()
                assert record['disconnects_received'] == 0
                assert record['suppressed_entries'] == record['suppressed_returns'] == 0
                assert record['order'].index('real_raw_return_after_FD_close') < record['order'].index('app_exited') < record['order'].index('cancel_propagated')
            else:
                await task
                assert not task.cancelled() and not record['stopped'].is_set()
                assert record['disconnects_received'] == 1
                assert record['suppressed_entries'] == record['suppressed_returns'] == 1
                assert record['order'].index('real_raw_return_after_FD_close') < record['order'].index('real_suppressed_return') < record['order'].index('app_exited')
            assert record['app_exited'] and record['sent'] == [] and record['release_entries'] == 0
            assert record['entered'].is_set() and record['finished'].is_set()
            closed(record)
            within_original_deadlines(record)
        finally:
            record['release'].set()
            await asyncio.gather(task, return_exceptions=True)

    directories = [packet['directory'], *artifact_cases._directories(packet['parent'])]
    before = artifact_cases._inventory(directories)
    fd_before = len(os.listdir('/proc/self/fd'))
    try:
        with artifact_cases.qa._watch(observe, {reader.read_repeat_material_manifest.__code__, reader._load.__code__,
                public._Release.__call__.__code__, public._Suppressed.__call__.__code__}):
            for mode in ('baseline', 'cancel', 'disconnect', 'recovery'):
                record = {'mode': mode, 'public_entries': 0, 'load_entries': 0, 'load_returns': 0,
                          'raw_returns': 0, 'release_entries': 0, 'suppressed_entries': 0,
                          'suppressed_returns': 0, 'held': threading.Event(), 'release': threading.Event(),
                          'body_received': False, 'disconnects_received': 0, 'app_exited': False,
                          'sent': [], 'order': []}
                records.append(record)
                active[0] = record
                if mode in ('baseline', 'recovery'):
                    response = asyncio.run(_asgi_manifest_get(app, token))
                    assert response.status_code == 200 and response.content == packet['raw']
                    assert record['release_entries'] == 1 and not record['stopped'].is_set()
                    assert record['suppressed_entries'] == record['suppressed_returns'] == 0
                else:
                    asyncio.run(interrupt(record))
                assert record['public_entries'] == record['load_entries'] == record['load_returns'] == record['raw_returns'] == 1
                assert record['entered'].is_set() and record['finished'].is_set()
                closed(record)
                assert current_principal() is None and public._registry(registry) == registry_state
        assert [record['mode'] for record in records] == ['baseline', 'cancel', 'disconnect', 'recovery']
    finally:
        for record in records:
            record['release'].set()
        assert current_principal() is None and public._registry(registry) == registry_state
        assert len(os.listdir('/proc/self/fd')) == fd_before
        assert artifact_cases._inventory(directories) == before



@_tls_pytest.mark.parametrize('fault', ['code', 'policy'], ids=['loaded_code_final_fence', 'app_policy_release'])
def test_final_code_and_app_policy_drift_suppress_valid_reader_bytes(first_artifact, fault):
    import errno
    import json
    from app import api_supply_material_repeat as public

    packet = first_artifact
    _, reader = artifact_cases._api()
    access = ContentAccess(packet['access'].owner_uid, packet['access'].reader_gid)
    original_access = dict(vars(access))
    fixture_access = (id(packet['access']), dict(vars(packet['access'])))
    token = secrets.token_urlsafe(32).encode('ascii')
    now = datetime.now(timezone.utc)
    grant = BearerGrant(token_digest(token), 'own-repeat-http-test', frozenset({'metadata', 'artifact'}),
                        now - timedelta(seconds=1), now + timedelta(minutes=15))
    registry = BearerRegistry((grant,))
    app = _fixed_delivery({**packet, 'access': access}, registry)
    registry_state = public._registry(registry)
    expected_principal = {'authenticated': True, 'tenant_id': grant.tenant_id, 'scopes': grant.scopes}
    policy_snapshot = public._policy(access)
    original_function, original_code = public._authorized, public._authorized.__code__
    expected_dispatch = public._DISPATCH

    def rejected_authorization(tenant):
        raise AssertionError('rejected authorization code body executed')

    replacement_code = rejected_authorization.__code__
    assert original_function.__closure__ is None and original_code.co_freevars == replacement_code.co_freevars == ()
    assert original_code.co_argcount == replacement_code.co_argcount == 1

    class RejectedCodeEntry(BaseException):
        pass

    control_phase = [False]
    controls, rejected_entries, records = [], [], []
    active = [None]

    def closed(record):
        assert record['store'].__dict__['_fd'] is None
        try:
            os.fstat(record['fd'])
        except OSError as error:
            assert error.errno == errno.EBADF
        else:
            raise AssertionError('real reader descriptor is still open')

    def current(record):
        assert current_principal() == expected_principal
        assert public._CLOCK() < record['deadline'] and public._CLOCK() < record['meter'].deadline

    def observe(frame, event, value):
        if frame.f_code is replacement_code:
            if event == 'call':
                if control_phase[0]:
                    controls.append(frame.f_code)
                else:
                    rejected_entries.append(frame.f_code)
                raise RejectedCodeEntry()
            return
        record = active[0]
        assert record is not None
        if frame.f_code is reader.read_repeat_material_manifest.__code__:
            if event == 'call':
                assert record['public_entries'] == 0 and current_principal() == expected_principal
                record['public_entries'] += 1
            elif event == 'return':
                assert type(value) is bytes and value == packet['raw'] and record['load_returns'] == 1
                closed(record)
                current(record)
                record['raw_returns'] += 1
        elif frame.f_code is reader._load.__code__:
            if event == 'call':
                assert record['load_entries'] == 0 and record['public_entries'] == 1
                store = frame.f_locals['store']
                assert type(store) is reader.MorphologyBlobStore and store._access is access and store._write is False
                fd = store.__dict__['_fd']
                assert type(fd) is int and os.fstat(fd).st_ino == packet['directory'].stat().st_ino
                caller = frame.f_back
                while caller is not None and not (caller.f_code.co_filename == public.__file__
                        and caller.f_code.co_name == 'checked_read'):
                    caller = caller.f_back
                assert caller is not None
                record.update(store=store, fd=fd, meter=frame.f_locals['meter'], deadline=caller.f_locals['deadline'],
                    entered=caller.f_locals['entered'], finished=caller.f_locals['finished'], stopped=caller.f_locals['stopped'])
                assert record['entered'].is_set() and not record['finished'].is_set() and not record['stopped'].is_set()
                current(record)
                record['load_entries'] += 1
            elif event == 'return':
                assert type(value) is tuple and len(value) == 4 and value[0] == packet['raw']
                record['load_returns'] += 1
        elif frame.f_code is reader._fence.__code__ and event == 'call':
            if (frame.f_locals['complete'] is True and frame.f_back.f_code is reader._read.__code__):
                assert record['load_returns'] == 1 and frame.f_locals['store'] is record['store']
                assert frame.f_locals['witnessed'][packet['root']][0] == packet['raw']
                record['final_fences'] += 1
                if record['mode'] == 'fault' and fault == 'code' and not record['injected']:
                    current(record)
                    assert record['store'].__dict__['_fd'] == record['fd'] and not record['finished'].is_set()
                    assert original_function.__code__ is original_code and dict(vars(access)) == original_access
                    original_function.__code__ = replacement_code
                    record['injected'] = True
        elif frame.f_code is public._Release.__call__.__code__ and event == 'call':
            assert record['raw_returns'] == 1 and record['finished'].is_set()
            closed(record)
            current(record)
            record['releases'] += 1
            if record['mode'] == 'fault':
                assert fault == 'policy' and not record['injected']
                assert original_function.__code__ is original_code and dict(vars(access)) == original_access
                changed_uid = (access.owner_uid + 1) % (2**32 - 1)
                assert changed_uid != access.owner_uid and 0 <= changed_uid < 2**32 - 1
                object.__setattr__(access, 'owner_uid', changed_uid)
                record['injected'] = True
        elif frame.f_code is public._dispatch.__code__ and event == 'return':
            if record['injected'] and fault == 'code':
                assert record['raw_returns'] == 1 and value != expected_dispatch
                selected = [row for row in value if row[0] == '_authorized']
                assert len(selected) == 1 and selected[0][1] is original_function and selected[0][2] is replacement_code
                record['changed_dispatch'] += 1
            else:
                assert value == expected_dispatch
        elif frame.f_code is public._policy.__code__ and event == 'return':
            assert frame.f_locals['access'] is access
            if record['injected'] and fault == 'policy':
                assert value != policy_snapshot and value[0] == id(access)
                assert record['raw_returns'] == 1 and record['finished'].is_set()
                record['changed_policy'] += 1
            else:
                assert value == policy_snapshot
        elif frame.f_code is public._directory.__code__ and event == 'call' and record['injected']:
            record['directory_after_fault'] += 1

    def restore(record):
        production_closed = False
        if record['injected']:
            try:
                closed(record)
                production_closed = record['entered'].is_set() and record['finished'].is_set()
            except (AssertionError, OSError, KeyError):
                pass
        original_function.__code__ = original_code
        state = object.__getattribute__(access, '__dict__')
        state.clear()
        state.update(original_access)
        if record['injected']:
            assert production_closed, 'production cleanup did not precede fault restoration'
        assert original_function.__code__ is original_code and dict(vars(access)) == original_access

    directories = [packet['directory'], *artifact_cases._directories(packet['parent'])]
    before = artifact_cases._inventory(directories)
    source_paths = set(packet['manifest']['code_sha256']) | set(PINNED_SOURCES) | {
        'backend/app/api_supply_material_repeat.py', 'backend/app/http_identity.py',
        'backend/app/content_access.py', 'contracts/supply-material-repeat-protected-delivery-v1.md'}
    sources_before = {path: sha256((artifact_cases.ROOT / path).read_bytes()).hexdigest() for path in source_paths}
    fd_before = len(os.listdir('/proc/self/fd'))
    try:
        with artifact_cases.qa._watch(observe, {reader.read_repeat_material_manifest.__code__, reader._load.__code__,
                reader._fence.__code__, public._Release.__call__.__code__, public._dispatch.__code__,
                public._policy.__code__, public._directory.__code__, replacement_code}):
            if fault == 'code':
                control_phase[0] = True
                with _tls_pytest.raises(RejectedCodeEntry):
                    rejected_authorization(None)
                control_phase[0] = False
                assert controls == [replacement_code]
            for mode in ('baseline', 'fault', 'recovery'):
                record = {'mode': mode, 'public_entries': 0, 'load_entries': 0, 'load_returns': 0,
                          'raw_returns': 0, 'final_fences': 0, 'releases': 0, 'injected': False,
                          'changed_dispatch': 0, 'changed_policy': 0, 'directory_after_fault': 0}
                records.append(record)
                active[0] = record
                try:
                    response = asyncio.run(_asgi_manifest_get(app, token))
                    assert record['public_entries'] == record['load_entries'] == record['load_returns'] == record['raw_returns'] == 1
                    assert record['final_fences'] == 1 and record['entered'].is_set() and record['finished'].is_set()
                    assert not record['stopped'].is_set()
                    closed(record)
                    assert response.headers['cache-control'] == 'no-store'
                    assert record['directory_after_fault'] == 0 and rejected_entries == []
                    if mode == 'fault':
                        assert record['injected'] and response.status_code == 503
                        assert json.loads(response.content) == {'error': {'code': 'repeat_material_unavailable',
                                                                           'message': 'Repeat material unavailable'}}
                        assert response.content != packet['raw']
                        if fault == 'code':
                            assert record['changed_dispatch'] > 0 and record['changed_policy'] == record['releases'] == 0
                        else:
                            assert record['changed_policy'] > 0 and record['changed_dispatch'] == 0 and record['releases'] == 1
                    else:
                        assert not record['injected'] and response.status_code == 200 and response.content == packet['raw']
                        assert record['changed_dispatch'] == record['changed_policy'] == 0 and record['releases'] == 1
                finally:
                    restore(record)
                assert current_principal() is None and public._registry(registry) == registry_state
            if fault == 'code':
                control_phase[0] = True
                with _tls_pytest.raises(RejectedCodeEntry):
                    rejected_authorization(None)
                control_phase[0] = False
                assert controls == [replacement_code, replacement_code] and rejected_entries == []
        assert [record['mode'] for record in records] == ['baseline', 'fault', 'recovery']
    finally:
        original_function.__code__ = original_code
        state = object.__getattribute__(access, '__dict__')
        state.clear()
        state.update(original_access)
        assert (id(packet['access']), dict(vars(packet['access']))) == fixture_access
        assert current_principal() is None and public._registry(registry) == registry_state
        assert len(os.listdir('/proc/self/fd')) == fd_before
        assert artifact_cases._inventory(directories) == before
        assert {path: sha256((artifact_cases.ROOT / path).read_bytes()).hexdigest() for path in source_paths} == sources_before



@_tls_pytest.mark.parametrize('fault', ['bytes', 'mode', 'directory'],
    ids=['selected_source_bytes', 'selected_source_mode', 'owned_directory_identity'])
def test_final_source_fences_reject_only_owned_copy_mutations(first_artifact, tmp_path, fault):
    import errno
    import json
    import shutil
    import stat
    from app import api_supply_material_repeat as public
    from app import crop_morphology_artifact_io as storage

    packet = first_artifact
    _, reader = artifact_cases._api()
    original_directories = [packet['directory'], *artifact_cases._directories(packet['parent'])]
    originals_before = artifact_cases._inventory(original_directories)
    fixture_access = (id(packet['access']), dict(vars(packet['access'])))
    directory = shutil.copytree(packet['directory'], tmp_path / 'owned-copy')
    assert directory != packet['directory'] and directory.parent == tmp_path
    access = ContentAccess(packet['access'].owner_uid, packet['access'].reader_gid)
    access.require_writer()
    spare, parked = tmp_path / 'owned-empty-replacement', tmp_path / 'owned-parked-copy'
    spare.mkdir(mode=0o750)
    spare.chmod(0o750)
    for path in (directory, spare):
        fd = os.open(path, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
        try:
            access.validate(fd, directory=True)
        finally:
            os.close(fd)
    descriptor = packet['manifest']['blob_groups']['base'][0]
    target_hash = descriptor['sha256']
    target = directory / target_hash
    original_blob = target.read_bytes()
    assert len(original_blob) == descriptor['bytes'] and sha256(original_blob).hexdigest() == target_hash

    def stamp(info):
        return (info.st_dev, info.st_ino, stat.S_IMODE(info.st_mode), info.st_uid, info.st_gid,
                info.st_nlink, info.st_size, info.st_mtime_ns, info.st_ctime_ns)

    def copy_state():
        info = directory.stat(follow_symlinks=False)
        assert stat.S_ISDIR(info.st_mode) and stat.S_IMODE(info.st_mode) == 0o750
        assert (info.st_uid, info.st_gid) == (access.owner_uid, access.reader_gid)
        files = {}
        for path in directory.iterdir():
            before = path.stat(follow_symlinks=False)
            assert stat.S_ISREG(before.st_mode) and before.st_nlink == 1
            assert stat.S_IMODE(before.st_mode) == 0o640
            assert (before.st_uid, before.st_gid) == (access.owner_uid, access.reader_gid)
            raw = path.read_bytes()
            assert sha256(raw).hexdigest() == path.name
            assert stamp(path.stat(follow_symlinks=False)) == stamp(before)
            files[path.name] = (stamp(before), sha256(raw).hexdigest())
        return stamp(info), files

    initial_copy = copy_state()
    token = secrets.token_urlsafe(32).encode('ascii')
    now = datetime.now(timezone.utc)
    grant = BearerGrant(token_digest(token), 'own-repeat-http-test', frozenset({'metadata', 'artifact'}),
                        now - timedelta(seconds=1), now + timedelta(minutes=15))
    registry = BearerRegistry((grant,))
    app = _fixed_delivery({**packet, 'directory': directory, 'access': access}, registry)
    registry_state = public._registry(registry)
    expected_principal = {'authenticated': True, 'tenant_id': grant.tenant_id, 'scopes': grant.scopes}
    expected_directory = public._directory(directory, access)
    records = []
    active = [None]

    def current(record):
        assert current_principal() == expected_principal
        assert public._CLOCK() < record['deadline'] and public._CLOCK() < record['meter'].deadline

    def closed(record):
        assert record['store'].__dict__['_fd'] is None
        for fd in [record['fd'], *record['directory_check_fds']]:
            try:
                os.fstat(fd)
            except OSError as error:
                assert error.errno == errno.EBADF
            else:
                raise AssertionError('actual source validation descriptor remains open')

    def observe(frame, event, value):
        record = active[0]
        assert record is not None
        if frame.f_code is reader.read_repeat_material_manifest.__code__:
            if event == 'call':
                assert record['public_entries'] == 0 and current_principal() == expected_principal
                record['public_entries'] += 1
            elif event == 'return':
                assert type(value) is bytes and value == packet['raw'] and record['load_returns'] == 1
                closed(record)
                current(record)
                record['raw_returns'] += 1
        elif frame.f_code is reader._load.__code__:
            if event == 'call':
                store = frame.f_locals['store']
                assert type(store) is storage.MorphologyBlobStore and store._access is access and store._write is False
                fd = store.__dict__['_fd']
                assert type(fd) is int
                assert (os.fstat(fd).st_dev, os.fstat(fd).st_ino) == initial_copy[0][:2]
                caller = frame.f_back
                while caller is not None and not (caller.f_code.co_filename == public.__file__
                        and caller.f_code.co_name == 'checked_read'):
                    caller = caller.f_back
                assert caller is not None
                record.update(store=store, fd=fd, meter=frame.f_locals['meter'], deadline=caller.f_locals['deadline'],
                    entered=caller.f_locals['entered'], finished=caller.f_locals['finished'], stopped=caller.f_locals['stopped'])
                assert record['entered'].is_set() and not record['finished'].is_set() and not record['stopped'].is_set()
                current(record)
                record['load_entries'] += 1
            elif event == 'return':
                assert type(value) is tuple and len(value) == 4 and value[0] == packet['raw']
                record['load_returns'] += 1
        elif frame.f_code is reader._fence.__code__ and event == 'call':
            if frame.f_locals['complete'] is True and frame.f_back.f_code is reader._read.__code__:
                assert record['load_returns'] == 1 and frame.f_locals['store'] is record['store']
                witness = frame.f_locals['witnessed'][target_hash]
                assert witness[0] == original_blob
                record['witness_meta'] = witness[1]
                record['final_fences'] += 1
                if record['mode'] == 'fault' and fault == 'directory':
                    current(record)
                    assert not record['mutation_started'] and not record['finished'].is_set()
                    assert target.read_bytes() == original_blob and not parked.exists()
                    record['mutation_started'] = True
                    directory.rename(parked)
                    spare.rename(directory)
                    named = directory.stat(follow_symlinks=False)
                    assert (named.st_dev, named.st_ino) != initial_copy[0][:2]
                    assert stat.S_IMODE(named.st_mode) == 0o750
                    assert (named.st_uid, named.st_gid) == (access.owner_uid, access.reader_gid)
                    record['injected'] = True
        elif frame.f_code is storage.MorphologyBlobStore._usage.__code__ and event == 'return':
            caller = frame.f_back
            if (caller.f_code is reader._fence.__code__ and caller.f_locals['complete'] is True
                    and caller.f_back.f_code is reader._read.__code__):
                assert record['final_fences'] == 1 and record['load_returns'] == 1
                assert frame.f_locals['self'] is record['store']
                assert type(value) is tuple and len(value) == 2 and value[1] == len(initial_copy[1])
                record['final_usage_returns'] += 1
                if record['mode'] == 'fault' and fault in ('bytes', 'mode'):
                    current(record)
                    assert not record['mutation_started'] and not record['finished'].is_set()
                    assert reader.base._metadata(target.stat(follow_symlinks=False)) == record['witness_meta']
                    assert target.read_bytes() == original_blob and stat.S_IMODE(target.stat().st_mode) == 0o640
                    record['mutation_started'] = True
                    if fault == 'bytes':
                        fd = os.open(target, os.O_WRONLY | os.O_NOFOLLOW)
                        try:
                            assert os.write(fd, bytes([original_blob[0] ^ 1])) == 1
                        finally:
                            os.close(fd)
                        assert target.stat().st_size == len(original_blob)
                        assert sha256(target.read_bytes()).hexdigest() != target_hash
                    else:
                        target.chmod(0o600)
                        assert stat.S_IMODE(target.stat().st_mode) == 0o600
                    assert reader.base._metadata(target.stat(follow_symlinks=False)) != record['witness_meta']
                    record['injected'] = True
        elif frame.f_code is reader.need.__code__ and event == 'call' and not frame.f_locals['condition']:
            caller = frame.f_back
            if (frame.f_locals['message'] == 'STORAGE_HOLD: selected artifact metadata changed'
                    and caller.f_code is reader._fence.__code__ and caller.f_locals['h'] == target_hash):
                assert record['mode'] == 'fault' and fault in ('bytes', 'mode') and record['injected']
                assert caller.f_locals['meta'] == record['witness_meta'] and caller.f_locals['before'] != record['witness_meta']
                current(record)
                record['metadata_rejections'] += 1
            else:
                record['other_false_predicates'].append(('reader', frame.f_locals['message']))
        elif frame.f_code is storage._need.__code__ and event == 'call' and not frame.f_locals['condition']:
            caller = frame.f_back
            if (frame.f_locals['reason'] == 'STORAGE_HOLD: artifact directory replaced'
                    and caller.f_code is storage.MorphologyBlobStore._guard.__code__):
                assert record['mode'] == 'fault' and fault == 'directory' and record['injected']
                assert caller.f_locals['self'] is record['store']
                held, opened = caller.f_locals['held'], caller.f_locals['opened']
                assert (held.st_dev, held.st_ino) == initial_copy[0][:2]
                assert (held.st_dev, held.st_ino) != (opened.st_dev, opened.st_ino)
                record['directory_check_fds'].append(caller.f_locals['current'])
                current(record)
                record['directory_rejections'] += 1
            else:
                record['other_false_predicates'].append(('store', frame.f_locals['reason']))
        elif frame.f_code is public._directory.__code__ and event == 'return':
            assert frame.f_locals['directory'] == directory and frame.f_locals['access'] is access
            if record['injected'] and fault == 'directory':
                assert value != expected_directory
                record['changed_directory'] += 1
            else:
                assert value == expected_directory
        elif frame.f_code is public._Release.__call__.__code__ and event == 'call':
            assert record['mode'] != 'fault' and record['raw_returns'] == 1 and record['finished'].is_set()
            closed(record)
            record['releases'] += 1

    def repair(record):
        if not record['mutation_started']:
            return
        assert record['entered'].is_set() and record['finished'].is_set()
        closed(record)
        if fault == 'directory':
            if parked.exists():
                if directory.exists():
                    assert not list(directory.iterdir()) and not spare.exists()
                    directory.rename(spare)
                parked.rename(directory)
        else:
            target.write_bytes(original_blob)
            target.chmod(0o640)
        after = copy_state()
        assert after[0][:7] == initial_copy[0][:7] and set(after[1]) == set(initial_copy[1])
        for name, (metadata, digest) in after[1].items():
            original_metadata, original_digest = initial_copy[1][name]
            assert digest == original_digest and metadata[:7] == original_metadata[:7]
            if fault == 'directory' or name != target_hash:
                assert metadata == original_metadata
        record['repaired'] = True

    source_paths = set(packet['manifest']['code_sha256']) | set(PINNED_SOURCES) | {
        'backend/app/api_supply_material_repeat.py', 'contracts/supply-material-repeat-protected-delivery-v1.md'}
    sources_before = {path: sha256((artifact_cases.ROOT / path).read_bytes()).hexdigest() for path in source_paths}
    fd_before = len(os.listdir('/proc/self/fd'))
    try:
        with artifact_cases.qa._watch(observe, {reader.read_repeat_material_manifest.__code__, reader._load.__code__,
                reader._fence.__code__, storage.MorphologyBlobStore._usage.__code__, reader.need.__code__,
                storage._need.__code__, public._directory.__code__, public._Release.__call__.__code__}):
            for mode in ('baseline', 'fault', 'recovery'):
                record = {'mode': mode, 'public_entries': 0, 'load_entries': 0, 'load_returns': 0,
                          'raw_returns': 0, 'final_fences': 0, 'final_usage_returns': 0, 'releases': 0,
                          'mutation_started': False, 'injected': False, 'repaired': False,
                          'metadata_rejections': 0, 'directory_rejections': 0, 'changed_directory': 0,
                          'directory_check_fds': [], 'other_false_predicates': []}
                records.append(record)
                active[0] = record
                try:
                    response = asyncio.run(_asgi_manifest_get(app, token))
                    assert record['public_entries'] == record['load_entries'] == record['load_returns'] == record['final_fences'] == 1
                    assert record['entered'].is_set() and record['finished'].is_set() and not record['stopped'].is_set()
                    closed(record)
                    assert record['other_false_predicates'] == [] and response.headers['cache-control'] == 'no-store'
                    if mode == 'fault':
                        assert record['injected'] and record['raw_returns'] == record['releases'] == 0
                        assert response.content != packet['raw']
                        if fault == 'directory':
                            assert record['directory_rejections'] == 1 and record['changed_directory'] > 0
                            assert record['metadata_rejections'] == record['final_usage_returns'] == 0
                            assert response.status_code == 503
                            expected_error = {'error': {'code': 'repeat_material_unavailable', 'message': 'Repeat material unavailable'}}
                        else:
                            assert record['metadata_rejections'] == record['final_usage_returns'] == 1
                            assert record['directory_rejections'] == record['changed_directory'] == 0
                            assert response.status_code == 422
                            expected_error = {'error': {'code': 'repeat_material_hold', 'message': 'Repeat material evidence unavailable'}}
                        assert json.loads(response.content) == expected_error
                    else:
                        assert response.status_code == 200 and response.content == packet['raw']
                        assert record['raw_returns'] == record['final_usage_returns'] == record['releases'] == 1
                        assert record['metadata_rejections'] == record['directory_rejections'] == record['changed_directory'] == 0
                finally:
                    repair(record)
                assert current_principal() is None and public._registry(registry) == registry_state
            assert records[1]['repaired'] and [record['mode'] for record in records] == ['baseline', 'fault', 'recovery']
    finally:
        for record in records:
            if record['mutation_started'] and not record['repaired']:
                repair(record)
        assert (id(packet['access']), dict(vars(packet['access']))) == fixture_access
        assert current_principal() is None and public._registry(registry) == registry_state
        assert len(os.listdir('/proc/self/fd')) == fd_before
        assert artifact_cases._inventory(original_directories) == originals_before
        assert {path: sha256((artifact_cases.ROOT / path).read_bytes()).hexdigest() for path in source_paths} == sources_before



def test_real_default_utc_expiry_at_load_suppresses_tls_bytes_after_reader_cleanup(first_artifact, _tls_files):
    import errno
    from app import api_supply_material_repeat as public
    from app.https_service import HttpsApiService

    packet = first_artifact
    certificate, key, _ = _tls_files
    assert certificate.parent.stat().st_mode & 0o777 == 0o700
    assert key.stat().st_mode & 0o777 == 0o600
    assert packet['manifest']['effective_rights'] == {'use': True, 'display': True, 'redistribute': False}
    assert type(packet['raw']) is bytes and sha256(packet['raw']).hexdigest() == packet['root']
    assert (packet['directory'] / packet['root']).read_bytes() == packet['raw']
    _, reader = artifact_cases._api()
    trust = _tls_context(certificate)
    entries = _tls_forbidden_entries()
    forbidden_codes = {function.__code__ for function, _, _ in entries}
    observed_codes = {reader.read_repeat_material_manifest.__code__, reader._load.__code__,
                      public._authorized.__code__, public._Release.__call__.__code__}
    assert len(forbidden_codes) == 13 and not forbidden_codes & observed_codes
    phase, expected_code = 'control', None
    controls, forbidden, records = [], [], []
    active = [None]

    def closed(record):
        assert record['store'].__dict__['_fd'] is None
        try:
            os.fstat(record['fd'])
        except OSError as error:
            assert error.errno == errno.EBADF
        else:
            raise AssertionError('real UTC expiry reader descriptor remains open')

    def deadlines(record):
        meter = record['meter']
        assert (meter.started, meter.deadline) == record['reader_times']
        assert meter.deadline == meter.started + 60
        assert public._CLOCK() < record['adapter_deadline']
        assert public._CLOCK() < meter.deadline

    def observe(frame, event, value):
        if frame.f_code in forbidden_codes:
            if event != 'call':
                return
            if phase == 'control':
                assert frame.f_code is expected_code
                controls.append(frame.f_code)
                raise _TlsEntrySeen()
            forbidden.append(frame.f_code.co_name)
            raise AssertionError('real UTC expiry entered forbidden generation/storage')
        record = active[0]
        assert record is not None
        principal = {'authenticated': True, 'tenant_id': record['grant'].tenant_id,
                     'scopes': record['grant'].scopes}
        if frame.f_code is reader.read_repeat_material_manifest.__code__:
            if event == 'call':
                assert record['public_entries'] == 0 and current_principal() == principal
                record['public_entries'] += 1
            elif event == 'return':
                assert type(value) is bytes and value == packet['raw']
                assert record['load_returns'] == 1
                closed(record)
                deadlines(record)
                assert current_principal() == (None if record['mode'] == 'expiry' else principal)
                record['raw_returns'] += 1
                record['order'].append('normal_raw_return_after_FD_close')
        elif frame.f_code is reader._load.__code__:
            if event == 'call':
                assert record['load_entries'] == 0 and record['public_entries'] == 1
                assert current_principal() == principal
                assert public._registry(registry) == registry_state
                store, meter = frame.f_locals['store'], frame.f_locals['meter']
                assert type(store) is reader.MorphologyBlobStore
                assert store._access is packet['access'] and store._write is False
                fd = store.__dict__['_fd']
                assert type(fd) is int
                held, named = os.fstat(fd), packet['directory'].stat()
                assert (held.st_dev, held.st_ino) == (named.st_dev, named.st_ino)
                caller = frame.f_back
                while caller is not None and not (caller.f_code.co_filename == public.__file__
                        and caller.f_code.co_name == 'checked_read'):
                    caller = caller.f_back
                assert caller is not None
                entered, finished, stopped = (caller.f_locals[k] for k in ('entered', 'finished', 'stopped'))
                assert entered.is_set() and not finished.is_set() and not stopped.is_set()
                record.update(store=store, fd=fd, meter=meter, entered=entered, finished=finished,
                              stopped=stopped, adapter_deadline=caller.f_locals['deadline'],
                              reader_times=(meter.started, meter.deadline))
                deadlines(record)
                assert 0 < record['adapter_deadline'] - public._CLOCK() <= 30.0
                record['load_entries'] += 1
                if record['mode'] == 'expiry':
                    utc_before = datetime.now(timezone.utc)
                    remaining = (short_grant.expires_at - utc_before).total_seconds()
                    assert 0 < remaining <= 5.0, 'short grant must still be valid at real load entry'
                    wait = remaining + 0.05
                    assert min(record['adapter_deadline'], meter.deadline) - public._CLOCK() > wait
                    assert registry.valid(short_grant) and current_principal() == principal
                    started_wait = _tls_time.monotonic()
                    _tls_time.sleep(wait)
                    elapsed_wait = _tls_time.monotonic() - started_wait
                    utc_after = datetime.now(timezone.utc)
                    assert elapsed_wait >= wait and utc_after >= short_grant.expires_at
                    deadlines(record)
                    assert not registry.valid(short_grant) and current_principal() is None
                    assert public._registry(registry) == registry_state
                    assert entered.is_set() and not finished.is_set() and not stopped.is_set()
                    assert store.__dict__['_fd'] == fd
                    assert (os.fstat(fd).st_dev, os.fstat(fd).st_ino) == (named.st_dev, named.st_ino)
                    record.update(expired=True, remaining_utc_at_load=remaining,
                                  actual_wait_seconds=elapsed_wait)
                    record['order'].append('real_UTC_expired_while_original_load_entered')
            elif event == 'return':
                assert type(value) is tuple and len(value) == 4 and value[0] == packet['raw']
                assert record['store'].__dict__['_fd'] == record['fd']
                deadlines(record)
                record['load_returns'] += 1
                record['order'].append('normal_original_load_return')
        elif frame.f_code is public._authorized.__code__ and event == 'return':
            if value is None:
                assert current_principal() == principal
                record['valid_authorizations'] += 1
            else:
                assert record['mode'] == 'expiry' and record['expired']
                assert current_principal() is None and not registry.valid(short_grant)
                assert value.status_code == 401
                assert _tls_json.loads(value.body) == {'error': {
                    'code': 'unauthenticated', 'message': 'Authentication required'}}
                assert record['raw_returns'] == 1 and record['load_returns'] == 1
                assert record['entered'].is_set() and record['finished'].is_set()
                assert not record['stopped'].is_set()
                closed(record)
                deadlines(record)
                gate = frame.f_back
                assert gate.f_code.co_filename == public.__file__ and gate.f_code.co_name == 'gate'
                assert gate.f_locals['deadline'] == record['adapter_deadline']
                handle = gate.f_back
                assert handle.f_code.co_filename == public.__file__ and handle.f_code.co_name == 'handle'
                assert handle.f_locals['raw'] == packet['raw'] and handle.f_locals['failure'] is None
                assert handle.f_locals['worker'].done()
                record['expired_authorizations'] += 1
                record['order'].append('actual_postread_authorized_401')
        elif frame.f_code is public._Release.__call__.__code__ and event == 'call':
            assert record['mode'] == 'recovery' and record['raw_returns'] == 1
            assert record['entered'].is_set() and record['finished'].is_set()
            assert not record['stopped'].is_set() and current_principal() == principal
            assert frame.f_locals['self'].request.scope['state'][public._DEADLINE] == record['adapter_deadline']
            closed(record)
            deadlines(record)
            record['release_entries'] += 1

    def positive_controls():
        nonlocal expected_code
        for function, args, kwargs in entries:
            expected_code = function.__code__
            before_control = len(controls)
            with _tls_pytest.raises(_TlsEntrySeen):
                function(*args, **kwargs)
            assert len(controls) == before_control + 1

    directories = [packet['directory'], *artifact_cases._directories(packet['parent'])]
    before = artifact_cases._inventory(directories)
    source_pins = {relative: sha256((artifact_cases.ROOT / relative).read_bytes()).hexdigest()
                   for relative in [*PINNED_SOURCES, 'backend/app/api_supply_material_repeat.py',
                                    'backend/app/http_identity.py', 'backend/app/https_service.py',
                                    'backend/app/content_access.py',
                                    'contracts/supply-material-repeat-protected-delivery-v1.md']}
    short_token, long_token = (secrets.token_urlsafe(32).encode('ascii') for _ in range(2))
    assert short_token != long_token
    now = datetime.now(timezone.utc)
    short_grant = BearerGrant(token_digest(short_token), 'own-repeat-http-test',
        frozenset({'metadata', 'artifact'}), now - timedelta(seconds=1), now + timedelta(seconds=5))
    long_grant = BearerGrant(token_digest(long_token), 'own-repeat-http-test',
        frozenset({'metadata', 'artifact'}), now - timedelta(seconds=1), now + timedelta(minutes=15))
    registry = BearerRegistry((short_grant, long_grant))
    assert any(registry._clock.__code__ is constant for constant in BearerRegistry.__init__.__code__.co_consts)
    app = _fixed_delivery(packet, registry)
    registry_state = public._registry(registry)
    assert registry._grants == (short_grant, long_grant)
    server = HttpsApiService(app, certificate, key, port=0).server()
    fd_before = len(os.listdir('/proc/self/fd'))
    try:
        with artifact_cases.qa._watch(observe, forbidden_codes | observed_codes):
            positive_controls()
            phase = 'tls'
            with _tls_served(server) as port:
                for mode, token, grant in [('expiry', short_token, short_grant),
                                            ('recovery', long_token, long_grant)]:
                    record = {'mode': mode, 'grant': grant, 'expired': False, 'public_entries': 0,
                              'load_entries': 0, 'load_returns': 0, 'raw_returns': 0,
                              'valid_authorizations': 0, 'expired_authorizations': 0,
                              'release_entries': 0, 'order': []}
                    records.append(record)
                    active[0] = record
                    response = asyncio.run(_tls_get(port, trust, '/v1/research/material-repeat/manifest', token))
                    assert 0 < response.seconds < 30.0
                    record['TLS_seconds'] = response.seconds
                    assert record['public_entries'] == record['load_entries'] == record['load_returns'] == record['raw_returns'] == 1
                    assert record['entered'].is_set() and record['finished'].is_set() and not record['stopped'].is_set()
                    closed(record)
                    deadlines(record)
                    assert record['valid_authorizations'] > 0 and public._registry(registry) == registry_state
                    assert response.headers['content-type'].split(';')[0].strip() == 'application/json'
                    assert response.headers['cache-control'] == 'no-store'
                    assert response.headers['x-content-type-options'] == 'nosniff'
                    assert response.headers['x-frame-options'] == 'DENY'
                    assert response.headers['strict-transport-security'] == 'max-age=31536000'
                    if mode == 'expiry':
                        assert response.status_code == 401 and response.headers['www-authenticate'] == 'Bearer'
                        assert _tls_json.loads(response.content) == {'error': {
                            'code': 'unauthenticated', 'message': 'Authentication required'}}
                        assert response.content != packet['raw']
                        assert record['expired'] and record['expired_authorizations'] == 1
                        assert record['release_entries'] == 0
                        assert record['order'] == ['real_UTC_expired_while_original_load_entered',
                            'normal_original_load_return', 'normal_raw_return_after_FD_close',
                            'actual_postread_authorized_401']
                    else:
                        assert response.status_code == 200 and response.content == packet['raw']
                        assert len(response.content) == len(packet['raw']) and sha256(response.content).hexdigest() == packet['root']
                        assert record['expired_authorizations'] == 0 and record['release_entries'] == 1
                        assert not record['expired'] and registry.valid(long_grant)
                    assert datetime.now(timezone.utc) >= short_grant.expires_at
                    assert not registry.valid(short_grant)
            phase = 'control'
            positive_controls()
            assert len(controls) == 26 and forbidden == []
        assert [record['mode'] for record in records] == ['expiry', 'recovery']
    finally:
        assert current_principal() is None
        assert public._registry(registry) == registry_state and registry._grants == (short_grant, long_grant)
        assert not registry.valid(short_grant) and registry.valid(long_grant)
        assert len(os.listdir('/proc/self/fd')) == fd_before
        assert artifact_cases._inventory(directories) == before
        for relative, expected in source_pins.items():
            assert sha256((artifact_cases.ROOT / relative).read_bytes()).hexdigest() == expected
    print(_tls_json.dumps({'repeat_real_default_UTC_load_expiry': {
        'one_pytest_case': True, 'real_reader_normal_returns': sum(r['raw_returns'] for r in records),
        'short_UTC_remaining_at_load': records[0]['remaining_utc_at_load'],
        'actual_expiry_wait_seconds': records[0]['actual_wait_seconds'],
        'fault_TLS_seconds': records[0]['TLS_seconds'], 'recovery_TLS_seconds': records[1]['TLS_seconds'],
        'postread_401_before_Release': records[0]['expired_authorizations'] == 1 and records[0]['release_entries'] == 0,
        'long_token_recovery_200': records[1]['release_entries'] == 1,
        'before_body_controls': len(controls), 'forbidden_entries': len(forbidden),
        'FD_scope': 'after_configuration_before_thread_through_join',
        'FD_before_after': [fd_before, len(os.listdir('/proc/self/fd'))],
        'registry_sources_inventory_unchanged': True, 'service_joined': True,
        'protected_delivery_accepted': False}}, sort_keys=True))
