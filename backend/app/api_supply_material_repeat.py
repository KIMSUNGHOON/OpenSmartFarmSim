"""Explicit fixed-resource protected reads of the stored repeat artifact."""
from __future__ import annotations

import asyncio
from hashlib import sha256
import os
from pathlib import Path
import re
import stat
import threading
from time import monotonic
from types import FunctionType

import anyio
from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from starlette.concurrency import run_in_threadpool
from starlette.exceptions import HTTPException
from starlette.requests import ClientDisconnect
from starlette.responses import JSONResponse, Response

from . import content_access, http_identity
from . import crop_supply_material_repeat_artifact_reader as reader
from .cli_contracts import _id
from .content_access import ContentAccess
from .http_identity import BearerRegistry, PrincipalMiddleware


MANIFEST_PATH = '/v1/research/material-repeat/manifest'
FRAME_PATH = '/v1/research/material-repeat/frames/{index}'
MAX_BYTES = 2097152
ADAPTER_SECONDS = 30.0
CODE_SHA256 = sha256(Path(__file__).read_bytes()).hexdigest()
_AUTH_FILE = Path(http_identity.__file__)
_AUTH_SHA256 = sha256(_AUTH_FILE.read_bytes()).hexdigest()
_STAT, _XATTRS, _CLOCK = os.stat, os.listxattr, monotonic
_PATH_TYPE = type(Path())
_DEADLINE = '_ossf_repeat_adapter_deadline'
_READ_MANIFEST = reader.read_repeat_material_manifest
_READ_FRAME = reader.read_repeat_material_frame
_HOLD = reader.RepeatArtifactHold
_CURRENT = http_identity.current_principal


def _dispatch():
    result = []
    for name, value in sorted(globals().items()):
        if getattr(value, '__module__', None) != __name__:
            continue
        if isinstance(value, FunctionType):
            result.append((name, value, value.__code__))
        elif isinstance(value, type):
            result.append((name, value))
            for key, method in sorted(value.__dict__.items()):
                if isinstance(method, FunctionType):
                    result.append((name, key, method, method.__code__))
    return tuple(result)


def _interfaces():
    functions = (reader.read_repeat_material_manifest, reader.read_repeat_material_frame,
                 http_identity.current_principal, http_identity.BearerRegistry.authenticate,
                 http_identity.BearerRegistry.valid, http_identity.BearerRegistry.__init__,
                 http_identity.BearerGrant.__post_init__,
                 http_identity.PrincipalMiddleware.__init__, http_identity.PrincipalMiddleware.__call__,
                 content_access.ContentAccess.__init__, content_access.ContentAccess.validate)
    return (reader.RepeatArtifactHold, http_identity.BearerRegistry, http_identity.BearerGrant,
            http_identity.PrincipalMiddleware, content_access.ContentAccess,
            *[(fn, fn.__code__) for fn in functions])


def _code():
    if (MANIFEST_PATH != '/v1/research/material-repeat/manifest'
            or FRAME_PATH != '/v1/research/material-repeat/frames/{index}'
            or _DEADLINE != '_ossf_repeat_adapter_deadline'
            or _READ_MANIFEST is not reader.read_repeat_material_manifest
            or _READ_FRAME is not reader.read_repeat_material_frame
            or _CURRENT is not http_identity.current_principal
            or _HOLD is not reader.RepeatArtifactHold
            or PrincipalMiddleware is not http_identity.PrincipalMiddleware
            or BearerRegistry is not http_identity.BearerRegistry
            or ContentAccess is not content_access.ContentAccess
            or _STAT is not os.stat or _XATTRS is not os.listxattr or _CLOCK is not monotonic
            or MAX_BYTES != 2097152 or type(MAX_BYTES) is not int
            or ADAPTER_SECONDS != 30.0 or type(ADAPTER_SECONDS) is not float
            or _dispatch() != _DISPATCH or _interfaces() != _INTERFACES
            or sha256(Path(__file__).read_bytes()).hexdigest() != CODE_SHA256
            or sha256(_AUTH_FILE.read_bytes()).hexdigest() != _AUTH_SHA256):
        raise ValueError('fixed delivery code required')


def _error(status, code, message):
    headers = {'WWW-Authenticate': 'Bearer'} if status == 401 else None
    return JSONResponse({'error': {'code': code, 'message': message}},
                        status_code=status, headers=headers)


def _unavailable():
    return _error(503, 'repeat_material_unavailable', 'Repeat material unavailable')


def _authorized(tenant):
    principal = _CURRENT()
    if (type(principal) is not dict or principal.get('authenticated') is not True
            or type(principal.get('tenant_id')) is not str
            or type(principal.get('scopes')) is not frozenset):
        return _error(401, 'unauthenticated', 'Authentication required')
    if principal['tenant_id'] != tenant or not {'metadata', 'artifact'} <= principal['scopes']:
        return _error(403, 'forbidden', 'Resource access denied')
    return None


def _policy(access):
    if type(access) is not ContentAccess:
        raise ValueError('concrete file policy required')
    state = dict(object.__getattribute__(access, '__dict__'))
    if (set(state) != {'owner_uid', 'reader_gid'} or any(type(value) is not int
            or not 0 <= value < 2**32 - 1 for value in state.values())):
        raise ValueError('unchanged file policy required')
    return id(access), tuple(sorted(state.items()))


def _registry(registry):
    state = dict(object.__getattribute__(registry, '__dict__'))
    if set(state) != {'_grants', '_clock'} or type(state['_grants']) is not tuple:
        raise ValueError('unchanged registry required')
    grants = state['_grants']
    if any(type(grant) is not http_identity.BearerGrant for grant in grants):
        raise ValueError('concrete grants required')
    clock = state['_clock']
    return (id(registry), id(grants),
            tuple((id(grant), tuple(sorted(vars(grant).items()))) for grant in grants),
            clock, getattr(clock, '__code__', None))


def _directory(directory, access):
    info = _STAT(directory, follow_symlinks=False)
    if (not stat.S_ISDIR(info.st_mode) or stat.S_IMODE(info.st_mode) != 0o750
            or info.st_uid != access.owner_uid or info.st_gid != access.reader_gid
            or {'system.posix_acl_access', 'system.posix_acl_default'}
            & set(_XATTRS(directory, follow_symlinks=False))):
        raise ValueError('owned artifact directory required')
    return info.st_dev, info.st_ino, info.st_mode, info.st_uid, info.st_gid


class _Suppressed(Response):
    async def __call__(self, scope, receive, send):
        return None


class _Release(Response):
    def __init__(self, raw, request, gate):
        super().__init__(raw, media_type='application/json', headers={'Cache-Control': 'no-store'})
        self.request, self.gate = request, gate

    async def __call__(self, scope, receive, send):
        if await self.request.is_disconnected():
            return
        denied = self.gate()
        if denied is not None:
            await denied(scope, receive, send)
            return
        task = asyncio.current_task()
        if task is not None and task.cancelling():
            raise asyncio.CancelledError()
        await send({'type': 'http.response.start', 'status': 200, 'headers': self.raw_headers})
        await send({'type': 'http.response.body', 'body': self.body})


class _AdapterBoundary:
    def __init__(self, app, gate):
        self.app, self.gate = app, gate

    async def __call__(self, scope, receive, send):
        if scope['type'] != 'http':
            await self.app(scope, receive, send)
            return
        deadline = _CLOCK() + ADAPTER_SECONDS
        scope = {**scope, 'state': {**scope.get('state', {}), _DEADLINE: deadline}}
        denied = self.gate(deadline)
        if denied is not None:
            await denied(scope, receive, send)
            return
        await self.app(scope, receive, send)


class _ReadDenied(Exception):
    def __init__(self, response):
        self.response = response


class _ReadStopped(Exception):
    pass


def create_repeat_material_app(*, directory: Path, access: ContentAccess,
                              root_sha256: str, tenant_id: str,
                              registry: BearerRegistry) -> PrincipalMiddleware:
    try:
        _code()
        if (type(directory) is not _PATH_TYPE or not directory.is_absolute()
                or '..' in directory.parts or type(root_sha256) is not str
                or re.fullmatch('[0-9a-f]{64}', root_sha256) is None
                or not _id(tenant_id) or type(registry) is not BearerRegistry):
            raise ValueError()
        policy = _policy(access)
        physical = _directory(directory, access)
        registry_state = _registry(registry)
    except Exception:
        raise ValueError('fixed protected repeat resource required') from None
    app = FastAPI(docs_url=None, redoc_url=None, openapi_url=None, redirect_slashes=False)
    protected = PrincipalMiddleware(app, registry)

    def gate(deadline):
        try:
            _code()
            denied = _authorized(tenant_id)
            if denied is not None:
                return denied
            if (protected.app is not app or protected.registry is not registry or _registry(registry) != registry_state
                    or _policy(access) != policy or _directory(directory, access) != physical
                    or _CLOCK() >= deadline):
                return _unavailable()
        except Exception:
            return _unavailable()
        return None

    app.add_middleware(_AdapterBoundary, gate=gate)

    @app.exception_handler(RequestValidationError)
    async def invalid_request(_request, _error_detail):
        return _error(422, 'invalid_request', 'Invalid request')

    @app.exception_handler(HTTPException)
    async def http_error(_request, error):
        if error.status_code == 404:
            return _error(404, 'not_found', 'Resource not found')
        if error.status_code == 405:
            return _error(405, 'method_not_allowed', 'Method not allowed')
        return _unavailable()

    async def handle(request, index):
        deadline = request.scope['state'][_DEADLINE]
        denied = gate(deadline)
        if denied is not None:
            return denied
        try:
            expected_path = MANIFEST_PATH
            if index is not None:
                if (type(index) is not str or re.fullmatch('0|[1-9][0-9]{0,2}', index) is None
                        or int(index) > 511):
                    raise ValueError()
                expected_path = FRAME_PATH.replace('{index}', index)
            if (request.scope.get('raw_path') != expected_path.encode('ascii')
                    or request.scope.get('query_string') or 'range' in request.headers):
                raise ValueError()
            async with asyncio.timeout_at(deadline):
                async for chunk in request.stream():
                    if chunk:
                        raise ValueError()
        except ClientDisconnect:
            return _Suppressed()
        except TimeoutError:
            return _unavailable()
        except ValueError:
            return _error(422, 'invalid_request', 'Invalid request')
        if await request.is_disconnected():
            return _Suppressed()
        stopped, entered, finished = threading.Event(), threading.Event(), threading.Event()

        def checked_read():
            entered.set()
            try:
                if stopped.is_set():
                    raise _ReadStopped()
                rejected = gate(deadline)
                if rejected is not None:
                    raise _ReadDenied(rejected)
                if stopped.is_set():
                    raise _ReadStopped()
                if index is None:
                    return _READ_MANIFEST(directory, access, root_sha256)
                return _READ_FRAME(directory, access, root_sha256, index=int(index))
            finally:
                finished.set()

        worker = asyncio.create_task(run_in_threadpool(checked_read))
        failure = None
        raw = None
        try:
            raw = await asyncio.shield(worker)
        except asyncio.CancelledError:
            stopped.set()
            # Keep the real validator owned until its normal FD cleanup finishes.
            with anyio.CancelScope(shield=True):
                while not worker.done() or (entered.is_set() and not finished.is_set()):
                    try:
                        if worker.done():
                            await asyncio.sleep(0.01)
                        else:
                            await asyncio.shield(worker)
                    except asyncio.CancelledError:
                        continue
                    except BaseException:
                        if entered.is_set() and not finished.is_set():
                            continue
                        break
                if worker.done():
                    try:
                        worker.result()
                    except BaseException:
                        pass
            raise
        except _ReadStopped:
            return _Suppressed()
        except _ReadDenied as error:
            failure = error.response
        except _HOLD:
            failure = _error(422, 'repeat_material_hold', 'Repeat material evidence unavailable')
        except PermissionError:
            failure = _error(403, 'forbidden', 'Resource access denied')
        except Exception:
            failure = _unavailable()
        denied = gate(deadline)
        if denied is not None:
            return denied
        if await request.is_disconnected():
            return _Suppressed()
        if failure is not None:
            return failure
        if type(raw) is not bytes or not 1 <= len(raw) <= MAX_BYTES:
            return _unavailable()
        return _Release(raw, request, lambda: gate(deadline))

    @app.get(MANIFEST_PATH, operation_id='getRepeatMaterialManifest', response_model=None)
    async def manifest(request: Request):
        return await handle(request, None)

    @app.get(FRAME_PATH, operation_id='getRepeatMaterialFrame', response_model=None)
    async def frame(request: Request, index: str):
        return await handle(request, index)

    return protected


_DISPATCH = _dispatch()
_INTERFACES = _interfaces()
