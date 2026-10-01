# Break-even verification HTTP and protected operator implementation

Date: 2026-10-02 (Asia/Seoul). Development CLI: `gpt-6.1-sol` / `xhigh` in
the existing session; no recursive Codex CLI was launched. Scope: an internal
`economic-break-even` / `api-flow` increment under the
[HTTP/operator contract](../contracts/api-break-even-verification-v1.md).

## Changes

The [HTTP module](../backend/app/api_break_even_verification.py) admits only an
actual completed calculation UUID through a closed 4 KiB JSON request. Current
tenant and required read/execution scopes come from the authenticated server
principal. The existing service resolves immutable input and server intent;
repeated submission reuses the same verification Job. Completed reading uses
the actual private replay evidence and fresh parent/source/rights bindings.
Read-only access needs no execution or source/candidate/plan writes. Exceptions
return fixed bounded errors without internal details.

[ApiRuntime](../backend/app/api_runtime.py) assembles both exact services through
its existing actual MarketSourceStore chain and Bearer request identity. The
versioned [OpenAPI](../contracts/openapi-v1.json) records operation IDs, scopes,
request bound and errors. Existing synchronous result replay remains available.

The [operator command](../backend/app/break_even_verify_work.py) validates an
ASCII factory reference and canonical Job UUID before importing the factory.
It requires the exact worker type, runs one targeted leased attempt and emits
only bounded Job/attempt/state/reason/calculation-parent metadata. Fixed startup
and unresolved-execution errors are distinct. Both new runtime modules are in
the current code manifest. No dependency, schema, grant, arithmetic formula,
CLI model invocation or request deadline changed.

## Focused evidence

- Operator error/type/outcome and OpenAPI/authentication contract selection:
  **69 passed in 36.23 s**. Invalid configuration precedes factory import;
  private exception text stays out of operator output. These unit boundaries
  alone do not prove an actual worker completion.
- [Actual SCRAM HTTP selection](../backend/tests/test_api_break_even_verification.py):
  **4 passed in 219.75 s**, no skips, on PostgreSQL 16.15. It verifies submission,
  immutable reuse, pending/completed reading, every required submission scope,
  read-only projection with scan arithmetic disabled, malformed/oversized/media
  inputs, unknown parent/Job, unavailable assembly and bounded private errors.
- One of those four cases starts the standard Bearer HTTPS runtime with the
  actual source factory and current-principal provider. A **separate Python
  process** builds fresh authenticated stores from temporary private files,
  executes the operator and publishes the actual persisted verification. HTTPS
  checks admission, pending 404, completed two-trial result, repeat admission
  and unauthenticated 401; the caller's foreign tenant header supplies no identity.
  All **5 complete response bodies** reach EOF under the unchanged **30 s**
  client timeout; the observed maximum is **0.503335387998959 s**. Every response
  is `Cache-Control: no-store`; request principal context is cleared and the
  server thread/socket close. No Codex CLI child runs in this test.

The first local invocation was interrupted before an accepted case after
**53.23 s**, when inspection found that the HTTPS test called nonexistent
service start/close methods. It is not passing evidence. The test was corrected
to use the actual Uvicorn server and its explicitly owned loopback socket;
the successful four-case invocation above follows that correction. Runtime
worker policy and client timeout were unchanged.

The tested current code SHA-256 is
`bcfe32a0b8da31ee9e30148fc793c1cdef51bb27b490e0b77959162b64d7663b`;
locked backend environment SHA-256 is
`e73e9ec049e80bfa4ad96afc33bfa25f5fddab60d60771284d6292178241beb3`.
Temporary SCRAM credentials, tenant-private evidence and test keys are not
included in this record or repository.

The official default CI collector succeeds with **2,290 cases across 141
files**, excluding only the existing delegated authored full software pair.
Complete inventory SHA-256 is
`ac2822d13de6ab215a5902fef6490305425fe14397e258d333b1d3a35d073598`.
Changed Python files parse (**9 files**), OpenAPI JSON parses, and changed
Markdown's **410 local file/anchor links** resolve. The unstaged and separately
executed staged diff whitespace checks pass.

## Surrounding CI and remaining work

The earlier `1e4210b` full hosted backend is now terminal success:
**2,265 passed, 0 skipped**, plus the separate Linux UID selection's **4 passed**
and all database/password cleanup steps. Its
[verification record](break-even-verification-implementation.md#terminal-hosted-backend-at-1e4210b)
also records that revision's authored/web/C0 checks. It excludes the later
completed-dependency reader and this HTTP/operator increment; those changes
require their own hosted run.

This selection uses synthetic two-trial assumptions and test authority keys.
Assessment remains `hold` with `conditional_user_grid_only`. SDK/browser
integration, automatic processing and protected deployment assembly, actual
256-trial SCRAM calculation/verification/HTTP reads under the unchanged 30 s
deadline, cancel/retry/source-rights withdrawal under that load, actual product
CLI and independent execution/release/G1/G4 remain outstanding. G0/G2/G3a/G3b
require their own evidence. The parent task checkboxes remain unchecked.

## Hosted checks at 160118c

The published revision `160118c7e085e4a665bae04a22f6f85437f1785b`
has terminal successful [authored checks](https://github.com/KIMSUNGHOON/OpenSmartFarmSim/actions/runs/36937726965):
seven suites, **141 test executions**, no skipped tests. API: **104 passed in
498.07 s**; economics: **13 in 589.62 s**; assessment: **15 in 887.46 s**;
assessment HTTPS: **1 in 332.54 s**; financial selection: **3 in 718.33 s**;
authored browser: **4 in 578.27 s**; financial browser: **1 in 458.32 s**.
All seven jobs and their database/password cleanup steps succeeded.
The assessment HTTPS case completed 10 bodies with maximum **22.318 s**.
The financial browser completed **29 actual SDK reader-EOF bodies**, maximum
**22.36579999999999 s**, below its unchanged 30-second client budget, with
zero console errors. These synthetic test executables and authority keys do
not establish product CLI or independent release evidence.

The same revision's [web checks](https://github.com/KIMSUNGHOON/OpenSmartFarmSim/actions/runs/36937726951)
also succeeded: **154 unit tests across 11 files** and **50 Chromium cases**
using one worker. [C0 checks](https://github.com/KIMSUNGHOON/OpenSmartFarmSim/actions/runs/36937726991)
succeeded. These results precede the later SDK/web asynchronous verification
commit and calculation publication-fence follow-up.

The full [backend workflow](https://github.com/KIMSUNGHOON/OpenSmartFarmSim/actions/runs/36937726974)
is still live at this observation: partitions 0–2 succeeded, 3–4 are running,
and 5 is queued. The workflow's top-level `queued` status is not a terminal
result. Its counts/inventory and complete cleanup acceptance will be recorded
only after all partitions and the aggregate check finish. A new push is held
to preserve this running workflow.
