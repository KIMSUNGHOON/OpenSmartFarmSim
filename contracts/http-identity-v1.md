# Request identity and service bearer authentication v1

The [HTTP identity adapter](../backend/app/http_identity.py) binds one
server-approved service credential to `current_principal()` for the API and
every request-facing store. Privileged assembly installs that same provider on
all of them, then wraps the ASGI app in `PrincipalMiddleware(app, registry)`.
This is service access authentication; browser login/session provisioning and
production identity integration remain separate work.

`BearerGrant` is frozen: a domain-separated token SHA-256, tenant ID, bounded
frozenset of scope identifiers, UTC `not_before` and `expires_at`. Lifetime is
positive and at most 24 hours. `BearerRegistry` takes 1–256 unique grants from
protected operator configuration, never from client headers/body/model output.
The operator generates unpredictable tokens from at least 32 random bytes and
keeps raw tokens and their hashes out of logs/prompts/public manifests. Tokens
have 32–128 ASCII URL-safe characters. No password or JWT verification, token
issuance, public registration, refresh or cookie flow is implied. Replacing the
registry retires credentials for new requests; already accepted operations may
finish. Durable revocation/rotation and audit are G4 work.

Only HTTPS ASGI requests and exactly one bounded `Authorization: Bearer <token>`
header may authenticate. Expired, future, unknown or malformed credentials and
clock failures return the fixed existing `401` envelope plus Bearer challenge.
Token hashes are compared with constant-time comparison. Query parameters,
cookies, caller tenant/scope headers and supplied ASGI state grant no identity.
The raw authorization header is removed before invoking the application.
The adapter trusts the ASGI server's scheme; actual TLS/proxy peer restriction
and header stripping must be proved by deployment, not client assertions.

The provider returns a fresh principal dictionary with frozen scopes; no raw
token/hash is part of it. Request-local `ContextVar` binding propagates through
the existing AnyIO thread pool. Every invocation starts unbound and resets in
`finally`; its shared lifetime is closed even when a copied child task outlives
the request. The provider also refuses expired/currently invalid grants. A
previously authorized accepted operation may finish after credential expiry;
expiry does not rewrite or delete durable jobs. Lifespan runs unbound; WebSocket
access is denied. Workers outside requests need their own trusted service
principal, never a retained HTTP identity.

Responses disable caching and add nosniff, frame denial and strict API-only CSP;
HTTPS responses also carry HSTS. CORS is not added. The strict API CSP does not
permit interactive Swagger assets; OpenAPI JSON remains available to authorized
callers. Middleware does not log credentials or request bodies. It grants no
SQL role, source right, data approval or G0–G4 permission.

[Loopback HTTPS startup](api-https-service-v1.md) has a separate transport adapter.
Public HTTPS deployment, protected credential loading/rotation, shared limits,
safe access logging, request attribution, actual operating accounts, browser
sessions and G4 remain pending. This contract does not establish a deployment.
