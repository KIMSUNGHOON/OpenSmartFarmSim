"""HTTPS service identity shared by ASGI requests and request-facing stores."""

from contextvars import ContextVar
from dataclasses import dataclass, field
from datetime import datetime, timezone, timedelta
from hashlib import sha256
import hmac
import re

from starlette.responses import JSONResponse

from .cli_contracts import _id


TOKEN = re.compile(rb"[A-Za-z0-9_-]{32,128}\Z")
HEX = re.compile(r"[0-9a-f]{64}\Z")
SCOPE = re.compile(r"[a-z][a-z0-9_]{0,63}\Z")
DOMAIN = b"OpenSmartFarmSim/api-bearer-v1\0"
_PRINCIPAL = ContextVar("ossf_http_principal", default=None)
HEADERS = {b"cache-control": b"no-store", b"x-content-type-options": b"nosniff",
    b"x-frame-options": b"DENY", b"content-security-policy": b"default-src 'none'; frame-ancestors 'none'"}


def _utc(value):
    return type(value) is datetime and value.utcoffset() == timedelta(0)


def token_digest(raw):
    if type(raw) is not bytes or TOKEN.fullmatch(raw) is None:
        raise ValueError("service credential rejected")
    return sha256(DOMAIN+raw).hexdigest()


@dataclass(frozen=True)
class BearerGrant:
    token_sha256: str = field(repr=False)
    tenant_id: str
    scopes: frozenset[str]
    not_before: datetime
    expires_at: datetime

    def __post_init__(self):
        if (type(self.token_sha256) is not str or HEX.fullmatch(self.token_sha256) is None or
                not _id(self.tenant_id) or type(self.scopes) is not frozenset or len(self.scopes) > 20 or
                any(type(item) is not str or SCOPE.fullmatch(item) is None for item in self.scopes) or
                not _utc(self.not_before) or not _utc(self.expires_at) or
                not timedelta(0) < self.expires_at-self.not_before <= timedelta(days=1)):
            raise ValueError("service grant rejected")


@dataclass(frozen=True, init=False)
class BearerRegistry:
    _grants: tuple[BearerGrant, ...] = field(repr=False)
    _clock: object = field(repr=False)

    def __init__(self, grants, *, clock=None):
        if (type(grants) is not tuple or not 1 <= len(grants) <= 256 or
                any(type(item) is not BearerGrant for item in grants) or
                len({item.token_sha256 for item in grants}) != len(grants) or
                (clock is not None and not callable(clock))):
            raise ValueError("service registry rejected")
        object.__setattr__(self, "_grants", grants)
        object.__setattr__(self, "_clock", clock if clock is not None else (lambda: datetime.now(timezone.utc)))

    def valid(self, grant):
        try:
            now = self._clock()
            return _utc(now) and grant.not_before <= now < grant.expires_at
        except Exception:
            return False

    def authenticate(self, header):
        if type(header) is not bytes or len(header) > 135:
            return None
        scheme, separator, raw = header.partition(b" ")
        if scheme.lower() != b"bearer" or not separator or TOKEN.fullmatch(raw) is None:
            return None
        digest = token_digest(raw)
        match = None
        for grant in self._grants:
            if hmac.compare_digest(digest, grant.token_sha256):
                match = grant
        return match if match is not None and self.valid(match) else None


@dataclass
class _RequestIdentity:
    grant: BearerGrant
    registry: BearerRegistry
    active: bool = True


def current_principal():
    identity = _PRINCIPAL.get()
    if identity is None or not identity.active or not identity.registry.valid(identity.grant):
        return None
    return {"authenticated": True, "tenant_id": identity.grant.tenant_id, "scopes": identity.grant.scopes}


class PrincipalMiddleware:
    def __init__(self, app, registry):
        if not callable(app) or type(registry) is not BearerRegistry:
            raise ValueError("protected service application required")
        self.app, self.registry = app, registry

    async def __call__(self, scope, receive, send):
        token = _PRINCIPAL.set(None)
        identity = None
        try:
            if scope["type"] == "lifespan":
                await self.app(scope, receive, send)
                return
            if scope["type"] == "websocket":
                await send({"type": "websocket.close", "code": 1008})
                return
            async def protected_send(message):
                if message["type"] == "http.response.start":
                    additions = dict(HEADERS)
                    if scope.get("scheme") == "https":
                        additions[b"strict-transport-security"] = b"max-age=31536000"
                    headers = [(key, value) for key, value in message.get("headers", []) if key.lower() not in additions]
                    message = {**message, "headers": headers+list(additions.items())}
                await send(message)
            headers = [value for key, value in scope.get("headers", []) if key.lower() == b"authorization"]
            grant = self.registry.authenticate(headers[0]) if scope.get("scheme") == "https" and len(headers) == 1 else None
            if grant is None:
                response = JSONResponse({"error": {"code": "unauthenticated", "message": "Authentication required"}},
                    status_code=401, headers={"WWW-Authenticate": "Bearer"})
                await response(scope, receive, protected_send)
                return
            identity = _RequestIdentity(grant, self.registry)
            _PRINCIPAL.set(identity)
            cleaned = {**scope, "headers": [(key, value) for key, value in scope.get("headers", [])
                                            if key.lower() != b"authorization"]}
            await self.app(cleaned, receive, protected_send)
        finally:
            if identity is not None:
                identity.active = False
            _PRINCIPAL.reset(token)
