# Request identity implementation evidence

On 2026-09-28, existing Codex CLI 0.157.1 session
`01a0e064-b01b-7a22-8ef8-dd4afe0eb7dc` implemented and reviewed the
[service identity contract](../contracts/http-identity-v1.md). Its inspected
local turn context at `2026-09-28T09:45:41.657Z` records `gpt-6-sol` / `xhigh`.
No additional agent or recursive CLI/model call was used. This is software
design evidence from the current session, not independent release approval or
an actual product runtime model invocation.

The adapter uses existing locked Starlette/AnyIO dependencies and Python 3.12.
[Starlette's middleware documentation](https://starlette.dev/middleware/)
explains pure ASGI wrapping and ContextVar limitations of BaseHTTPMiddleware.
[Python 3.12 contextvars](https://docs.python.org/3.12/library/contextvars.html)
documents request/task-local binding and token reset; the
[AnyIO worker-thread documentation](https://anyio.readthedocs.io/en/stable/threads.html)
documents context copying into worker threads. These primary sources support
the chosen adapter; actual lifetime and isolation behavior is tested locally.

Frozen operator grants use domain-separated hashes, exact tenant/scopes and
bounded UTC windows. Only one bounded HTTPS Bearer header can authenticate;
fixed errors conceal token/clock details. Client tenant/scope/cookie/query/state
values supply no identity. The raw authorization header is removed downstream.
The API and request-facing stores use one ContextVar provider, including the
existing thread pool. A shared closed flag prevents copied child contexts from
retaining identity after response, exception, cancellation or send failure.
Grant expiry is rechecked by the provider. No SQL role or data/gate permission
is inferred from successful authentication.

The initial isolated suite passed **30 cases in 1.89 s** against local
PostgreSQL 16.15 using `uv run --locked --group dev pytest` and the existing
`OSSF_TEST_PG_DSN`. It includes overlapping authenticated POST requests to real
SCRAM-protected storage: equal idempotency keys create distinct tenant jobs and
cross-tenant status reads return 404. Later additions cover scope denial,
clock exceptions, lifespan and WebSocket behavior. The final identity suite has
**33 cases**. The combined identity, location/status/hold/market/thermal/economic
HTTP, research registry, thermal review and publisher run passed **151 cases in
56.15 s**, with no skips. Whitespace and changed-document local links were
checked separately. Hosted exact-head CI is a separate later receipt.

Tokens, clocks, scopes and accounts in these tests are synthetic. An ASGI
`scheme=https` fixture is not actual TLS/proxy/deployment proof. No actual farm
data, source credentials, research, crop coefficient, economics or model output
was used. Dependencies, locks, SQL schema/grants and existing immutable
manifests/releases/records were preserved. Identity code joins the closed
thermal code digest and therefore requires new independent release evidence.

Protected credential/config loading, real HTTP server startup, trusted TLS
termination, revocation/rotation, safe access logging, request attribution,
shared limits, operating accounts and browser sessions remain pending.
The module is a composable service adapter; it does not constitute a deployed
authentication system or complete api-flow/G1/G4.

Exact identity commit `6713a12b74e34883ef5829399813b6c81ef850ac` passed
[backend CI](https://github.com/KIMSUNGHOON/OpenSmartFarmSim/actions/runs/36405879698):
**1480 ordinary tests, 2 warnings** in 330.32 s, **four distinct-UID cases** in
18.91 s and content DAC. Its
[Compose CI](https://github.com/KIMSUNGHOON/OpenSmartFarmSim/actions/runs/36405879887)
also passed. Terminal exact-head states were rechecked on 2026-09-28. Those
receipts precede the later HTTPS transport and dependency changes.
