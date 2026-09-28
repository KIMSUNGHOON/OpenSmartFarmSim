# HTTPS service implementation evidence

On 2026-09-28, existing Codex CLI 0.157.1 session
`01a0e064-b01b-7a22-8ef8-dd4afe0eb7dc` implemented and reviewed
[the HTTPS transport contract](../contracts/api-https-service-v1.md). Its inspected
local context at `2026-09-28T09:56:36.427Z` records `gpt-6-sol` / `xhigh`.
No extra agent, recursive CLI/model call or agricultural/economic coefficient
was used. The test's `python -m app.api_serve` subprocess is our API entrypoint,
not another Codex process. Current-session review is not independent release
or actual runtime model evidence.

Primary sources retrieved that day:

- [Uvicorn settings](https://uvicorn.dev/settings/) documents programmatic
  configuration, TLS, forwarded-header trust, h11, reset_contextvars and limits.
- [Uvicorn deployment](https://uvicorn.dev/deployment/) documents custom SSL
  context factories and warns about trusting forwarded headers.
- [Uvicorn release notes](https://uvicorn.dev/release-notes/) and
  [PyPI 0.54.0](https://pypi.org/project/uvicorn/0.54.0/) support the version choice.
  PyPI's primary JSON metadata reports stable 0.54.0, publication
  `2026-09-25T06:52:35.829563Z`, Python >=3.10 and BSD-3-Clause.
  Installed exact source confirms SSL factory recognition and signal re-raise.

Only base Uvicorn is added. Lock resolution adds Uvicorn 0.54.0, click 8.5.0
and h11 0.16.0; other pins are preserved. `uv sync --locked --group dev` and
`uv lock --check` passed. Optional standard transports/reload packages are not
installed. Licensing/security review for a production release remains separate.

The adapter accepts an already authenticated FastAPI assembly from trusted
operator code. It loads bounded TLS files through inspected Linux descriptors,
requires private parent/key ownership, minimum TLS 1.2 and exact loopback scope,
and disables plaintext/proxy/access-log behavior. Diagnostics/CLI errors are
fixed events. Configured limits bound transport resources; they do not prove
shared limits, request deadlines, operating capacity or managed restart.

The first local suite had **28 passed, one failed in 2.62 s**: defining the
service in the `python -m` entrypoint duplicated class identity when a factory
imported it by module name. Splitting the reusable service into
`https_service.py` corrected the actual child startup. The next run again had
28 passed/one failed in 2.70 s, after all real HTTPS/SQL operations succeeded:
the test expected zero exit, but Uvicorn deliberately re-raises SIGTERM after
shutdown. Its installed source confirmed this; the assertion now requires the
signal exit. No server termination behavior was changed.

Identity, location/status/hold API and thermal publisher/review checks passed
**137 cases in 47.67 s** before two final denial regressions were added. Final
HTTPS tests passed **31 cases in 2.74 s** with
`uv run --locked --group dev pytest tests/test_api_serve.py -q --tb=short`
and disposable local PostgreSQL 16.15 via the existing `OSSF_TEST_PG_DSN`.

The real API child uses a private fixture factory/config, an ephemeral synthetic
EC certificate, synthetic Bearer and actual SCRAM authority connection. A client
trusting only that certificate receives 401 without authorization, then reads
OpenAPI, submits/retries a registered point and reads its queued job; the SQL
database contains exactly one immutable job. Spoofed forwarded protocol/client
headers do not override actual TLS. Untrusted certificate verification and
plaintext requests fail. SIGTERM ends the child without token/path output.
Other tests reject invalid service types/bindings, unsafe/symlinked/empty/large/
encrypted/mismatched TLS files, FIFO and configuration failures; key pathname
replacement after open cannot replace loaded bytes. Fixed diagnostics hide
exception/token text. Other domain readers in the child are explicit unused
test doubles; no full Run/economics/CLI application assembly is claimed.

New transport/entrypoint bytes join the closed thermal digest; lock changes
also require independent release evidence. Existing manifests/releases/records
and SQL schema/grants were preserved. Whitespace and changed-document links
were checked separately; hosted exact-head CI is a later receipt.

Public CA/domain/renewal, operating accounts and full protected factory/config,
revocation, shared limits/deadlines, safe attributed audit, Compose application
wiring and real runtime Codex isolation/execution remain pending. Actual source
and independent release, UI/full G1, field/forecast/comparison and G4 evidence
are not supplied by these synthetic software tests.
