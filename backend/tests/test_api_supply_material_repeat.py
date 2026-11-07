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
