"""Synthetic service credentials; ASGI scheme tests are not TLS deployment proof."""

import asyncio
from contextvars import copy_context
from dataclasses import FrozenInstanceError, replace
from datetime import datetime, timezone, timedelta
import json
from pathlib import Path
import sys

import pytest
from starlette.concurrency import run_in_threadpool
from starlette.responses import JSONResponse

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from app.api import create_app
from app.cli_contracts import _canonical
from app.http_identity import (BearerGrant, BearerRegistry, PrincipalMiddleware,
                              current_principal, token_digest)
from app.orchestration import LocationResearchService
from app.research_registry import ResearchRegistry
from test_api_location_research import (assembly, login_database, login_scope, BODY,
    UnusedMarketHoldStore, UnusedThermalRunStore, UnusedMarketResultStore, rows)
from test_research_registry import document


NOW = datetime(2026, 1, 1, tzinfo=timezone.utc)
TOKEN_A, TOKEN_B = b"synthetic-service-a-"+b"a"*32, b"synthetic-service-b-"+b"b"*32


def grant(raw=TOKEN_A, tenant="tenant-a", **changes):
    return replace(BearerGrant(token_digest(raw), tenant,
        frozenset({"metadata", "location_create"}), NOW, NOW+timedelta(hours=1)), **changes)


async def request(app, *, headers=None, scheme="https", path="/", method="GET", body=b"", wait=None):
    sent = []
    received = False
    async def receive():
        nonlocal received
        if not received:
            received = True
            if wait is not None:
                await wait()
            return {"type": "http.request", "body": body, "more_body": False}
        return {"type": "http.disconnect"}
    async def send(message):
        sent.append(message)
    await app({"type": "http", "asgi": {"version": "3.0"}, "method": method,
        "path": path, "raw_path": path.encode(), "root_path": "", "query_string": b"token=spoofed",
        "headers": headers if headers is not None else [(b"authorization", b"Bearer "+TOKEN_A)],
        "scheme": scheme, "http_version": "1.1", "server": ("test", 443), "client": ("test", 1234),
        "state": {"principal": {"authenticated": True, "tenant_id": "foreign-tenant"}}}, receive, send)
    start = next(item for item in sent if item["type"] == "http.response.start")
    raw = b"".join(item.get("body", b"") for item in sent if item["type"] == "http.response.body")
    return start["status"], json.loads(raw), dict(start["headers"])


def test_principal_is_fresh_scoped_and_header_is_removed():
    async def app(scope, receive, send):
        principal = current_principal()
        assert principal == await run_in_threadpool(current_principal)
        principal["tenant_id"] = "spoofed-tenant"
        principal["scopes"] = frozenset({"auditor"})
        assert current_principal()["tenant_id"] == "tenant-a"
        assert "auditor" not in current_principal()["scopes"]
        assert all(key.lower() != b"authorization" for key, _ in scope["headers"])
        assert "token_sha256" not in current_principal()
        await JSONResponse({"ok": True})(scope, receive, send)
    registry = BearerRegistry((grant(),), clock=lambda: NOW)
    protected = PrincipalMiddleware(app, registry)
    assert current_principal() is None
    status, reply, headers = asyncio.run(request(protected, headers=[
        (b"AUTHORIZATION", b"bEaReR "+TOKEN_A), (b"x-tenant-id", b"tenant-b"), (b"cookie", b"tenant=tenant-b")]))
    assert status == 200 and reply == {"ok": True} and current_principal() is None
    assert headers[b"cache-control"] == b"no-store" and headers[b"x-content-type-options"] == b"nosniff"
    assert headers[b"x-frame-options"] == b"DENY" and b"default-src 'none'" in headers[b"content-security-policy"]
    assert b"strict-transport-security" in headers
    assert TOKEN_A.decode() not in repr(registry) and token_digest(TOKEN_A) not in repr(grant())
    with pytest.raises(FrozenInstanceError):
        registry._grants = ()


@pytest.mark.parametrize("headers", [[], [(b"authorization", b"Bearer "+b"unknown"*8)],
    [(b"authorization", b"Bearer "+TOKEN_A), (b"Authorization", b"Bearer "+TOKEN_A)],
    [(b"authorization", b"Basic "+TOKEN_A)], [(b"authorization", b"Bearer  "+TOKEN_A)],
    [(b"authorization", b"Bearer "+TOKEN_A+b" ")], [(b"authorization", b"Bearer short")],
    [(b"authorization", b"Bearer "+b"a"*129)], [(b"authorization", b"Bearer \xff"+b"a"*40)],
    [(b"cookie", b"Authorization=Bearer "+TOKEN_A), (b"x-tenant-id", b"tenant-a")]])
def test_malformed_or_spoofed_credentials_never_reach_application(headers):
    async def forbidden(*_):
        raise AssertionError("untrusted credential reached application")
    app = PrincipalMiddleware(forbidden, BearerRegistry((grant(),), clock=lambda: NOW))
    status, error, response_headers = asyncio.run(request(app, headers=headers))
    assert status == 401 and error == {"error": {"code": "unauthenticated", "message": "Authentication required"}}
    assert response_headers[b"www-authenticate"] == b"Bearer" and current_principal() is None


@pytest.mark.parametrize("now", [NOW-timedelta(microseconds=1), NOW+timedelta(hours=1),
                                   NOW.replace(tzinfo=None), "synthetic private clock error"])
def test_not_yet_valid_expired_or_invalid_clock_denies(now):
    async def forbidden(*_):
        raise AssertionError("invalid clock reached application")
    app = PrincipalMiddleware(forbidden, BearerRegistry((grant(),), clock=lambda: now))
    assert asyncio.run(request(app))[0] == 401 and current_principal() is None


def test_plain_http_and_forwarded_header_do_not_assert_tls():
    async def forbidden(*_):
        raise AssertionError("plaintext credential reached application")
    app = PrincipalMiddleware(forbidden, BearerRegistry((grant(),), clock=lambda: NOW))
    status, _, headers = asyncio.run(request(app, scheme="http", headers=[
        (b"authorization", b"Bearer "+TOKEN_A), (b"x-forwarded-proto", b"https")]))
    assert status == 401 and b"strict-transport-security" not in headers


def test_copied_child_task_and_context_lose_identity_after_request():
    async def exercise():
        release = asyncio.Event()
        copied = []
        children = []
        async def app(scope, receive, send):
            copied.append(copy_context())
            async def child():
                await release.wait()
                return current_principal()
            children.append(asyncio.create_task(child()))
            await JSONResponse({"ok": True})(scope, receive, send)
        middleware = PrincipalMiddleware(app, BearerRegistry((grant(),), clock=lambda: NOW))
        assert (await request(middleware))[0] == 200
        release.set()
        assert await children[0] is None and copied[0].run(current_principal) is None
        assert current_principal() is None
    asyncio.run(exercise())


@pytest.mark.parametrize("mode", ["raise", "cancel", "send_failure"])
def test_cleanup_closes_identity_on_all_exit_paths(mode):
    copied = []
    async def app(scope, receive, send):
        copied.append(copy_context())
        assert current_principal() is not None
        if mode == "raise":
            raise RuntimeError("synthetic private exception")
        if mode == "cancel":
            raise asyncio.CancelledError()
        await send({"type": "http.response.start", "status": 200, "headers": []})
    async def failed_send(_):
        raise RuntimeError("synthetic private send exception")
    middleware = PrincipalMiddleware(app, BearerRegistry((grant(),), clock=lambda: NOW))
    async def run():
        if mode == "send_failure":
            await middleware({"type": "http", "scheme": "https", "headers": [(b"authorization", b"Bearer "+TOKEN_A)]},
                None, failed_send)
        else:
            await request(middleware)
    with pytest.raises((RuntimeError, asyncio.CancelledError)):
        asyncio.run(run())
    assert copied[0].run(current_principal) is None and current_principal() is None


def test_credential_expiry_is_rechecked_during_request():
    clock = [NOW]
    async def app(scope, receive, send):
        assert current_principal() is not None
        clock[0] += timedelta(hours=1)
        assert current_principal() is None and await run_in_threadpool(current_principal) is None
        await JSONResponse({"ok": True})(scope, receive, send)
    assert asyncio.run(request(PrincipalMiddleware(app, BearerRegistry((grant(),), clock=lambda: clock[0]))))[0] == 200


@pytest.mark.parametrize("changes", [{"token_sha256": "private-invalid-hash"}, {"tenant_id": "bad tenant"},
    {"scopes": {"metadata"}}, {"scopes": frozenset({"*"})}, {"not_before": NOW.replace(tzinfo=None)},
    {"expires_at": NOW}, {"expires_at": NOW+timedelta(days=2)}])
def test_invalid_operator_grants_fail_with_fixed_error(changes):
    with pytest.raises(ValueError, match="^service grant rejected$"):
        grant(**changes)


def test_duplicate_registry_grants_reject():
    with pytest.raises(ValueError, match="^service registry rejected$"):
        BearerRegistry((grant(), grant()))


def test_clock_exception_fails_closed_without_private_message():
    def broken_clock():
        raise RuntimeError("synthetic private clock detail")
    async def forbidden(*_):
        raise AssertionError("failed clock reached application")
    status, body, _ = asyncio.run(request(PrincipalMiddleware(forbidden,
        BearerRegistry((grant(),), clock=broken_clock))))
    assert status == 401 and "private" not in json.dumps(body)


@pytest.mark.parametrize("kind", ["lifespan", "websocket"])
def test_non_http_calls_have_no_request_identity(kind):
    entered, sent = [], []
    async def app(scope, receive, send):
        entered.append(scope["type"])
        assert current_principal() is None
    async def send(message):
        sent.append(message)
    middleware = PrincipalMiddleware(app, BearerRegistry((grant(),), clock=lambda: NOW))
    asyncio.run(middleware({"type": kind, "headers": [(b"authorization", b"Bearer "+TOKEN_A)]}, None, send))
    assert entered == (["lifespan"] if kind == "lifespan" else [])
    assert sent == ([] if kind == "lifespan" else [{"type": "websocket.close", "code": 1008}])
    assert current_principal() is None


def test_real_postgres_concurrent_authenticated_requests_remain_tenant_scoped(assembly):
    _, store, base, _, _, _ = assembly
    value = document()
    value["registrations"].append({**value["registrations"][0], "tenant_id": "tenant-b"})
    raw = _canonical(value)
    from hashlib import sha256
    catalog = ResearchRegistry(raw, sha256(raw).hexdigest())
    store.principal_provider = current_principal
    app = create_app(store, UnusedMarketHoldStore(), UnusedThermalRunStore(), UnusedMarketResultStore(),
        principal_provider=current_principal, location_research_service=LocationResearchService(store, catalog.scope_for_location))
    protected = PrincipalMiddleware(app, BearerRegistry((grant(), grant(TOKEN_B, "tenant-b")), clock=lambda: NOW))
    async def run():
        entered = 0
        gate = asyncio.Event()
        async def interleave():
            nonlocal entered
            entered += 1
            if entered == 2:
                gate.set()
            await gate.wait()
            await asyncio.sleep(0)
        async def submit(raw_token):
            return await request(protected, headers=[(b"authorization", b"Bearer "+raw_token),
                (b"content-type", b"application/json"), (b"x-tenant-id", b"foreign-tenant")],
                path="/v1/locations", method="POST", body=json.dumps(BODY).encode(), wait=interleave)
        first, second = await asyncio.wait_for(asyncio.gather(submit(TOKEN_A), submit(TOKEN_B)), timeout=10)
        assert first[0] == second[0] == 202
        a, b = first[1]["research_job"]["job_id"], second[1]["research_job"]["job_id"]
        assert a != b and first[1]["location_id"] != second[1]["location_id"]
        assert (await request(protected, path="/v1/jobs/"+a))[0] == 200
        assert (await request(protected, path="/v1/jobs/"+b))[0] == 404
        restricted = PrincipalMiddleware(app, BearerRegistry((grant(scopes=frozenset({"metadata"})),), clock=lambda: NOW))
        assert (await request(restricted, path="/v1/locations", method="POST", body=json.dumps(BODY).encode()))[0] == 403
        assert current_principal() is None
    asyncio.run(run())
    assert {row["tenant_id"] for row in rows(base)} == {"tenant-a", "tenant-b"}
