# Foreground HTTPS API service v1

`python -m app.api_serve --factory operator_module:create_service` starts an
operator-controlled `HttpsApiService`. The factory follows the existing
foreground service pattern and returns an exact service object with an exact
`PrincipalMiddleware` around a FastAPI app. Operator code/config is trusted;
HTTP clients and AI proposals cannot choose modules, TLS files or grants.
Assembly must bind the same identity provider to the API and request stores.

The adapter uses locked Uvicorn 0.54.0 with Python asyncio/ASGI3/h11, one worker,
required lifespan, no reload, no proxy headers, no WebSocket transport, no
access logs and no Server header. Uvicorn diagnostic messages are replaced by
a fixed service event, including exception details. CLI configuration and
service errors use fixed JSON codes. Factory code is responsible for its own
safe logging. No process, credential or database-role isolation is implied.
Service and entrypoint use separate modules so `python -m` preserves exact
factory type identity. Uvicorn performs shutdown and re-raises the original
termination signal; SIGTERM is a signal exit, not a successful zero exit.

Listen addresses are exactly `127.0.0.1` or `::1`; default port is 8443, with
0 allowed for an ephemeral test socket. Plaintext mode is absent. TLS minimum
is 1.2 using OpenSSL defaults. Operator certificate/key paths are absolute;
their immediate directory must be owned by the current UID and private.
Directory/file symlinks, nonregular/empty/oversized files, foreign ownership,
group/other access to the key and group/other write to the certificate are
rejected. Linux nofollow directory/file descriptors stay open while OpenSSL
loads via `/proc/self/fd`, preventing a pathname replacement between inspection
and loading. Encrypted keys fail without interactive password prompting.
The loaded context is retained in memory; TLS bytes/paths do not enter repr or
application responses. Certificate issuance, expiry management, hostname
policy and renewal remain operator/deployment responsibilities.

Transport has a 64 connection/task concurrency cap, backlog 128, 8192-byte
incomplete h11 event cap, 5-second keepalive, 10-second graceful shutdown and
10,000-request process lifetime. These bound individual server resources;
shared rate limits, request body/read deadlines, capacity/SLO validation and
managed restart remain separate operating work. Accepted requests keep the
existing authentication, tenant, schema and gate checks.

Synthetic ephemeral certificates verify real TLS and HTTP software transport,
not public CA trust, production certificates/accounts, independent model or
release evidence, G1 or G4. Public/proxy binding, protected full application
factory/config provisioning and Compose service wiring remain pending.
