# Completed economic job monthly cash — software candidate

Date: 2026-09-29. This extends the [economic workspace](../contracts/web-economic-workspace-v1.md)
and [saved numeric revision](web-joint-amendment-implementation.md), using the
[cash page contract](../contracts/api-economic-cash-flow-v1.md). Existing whole-task
checkboxes and G0–G4 holds remain unchanged.

## Development context and implementation decision

The existing CLI turn context at `2026-09-29T10:45:23.108Z` reports exact model
`gpt-6-sol`, effort `xhigh`, thread `01a0e064-b01b-7a22-8ef8-dd4afe0eb7dc`.
This is development context, not a product-runtime invocation receipt. No
recursive CLI or subagent was launched.

Inspection of the versioned EconomicLedger established that monthly opening,
net, closing, minimum, minimum instant and shortage already derive from pinned
cash events and explicit opening cash using Decimal and the Asia/Seoul calendar.
There was no public HTTP series. A separate completed-job page keeps the old
economic-result DTO unchanged; no new farm arithmetic, inferred period, source,
authority, DB grant, migration, model or dependency was added.

The economic service shares its existing publication/receipt, immutable input,
current read scopes, source/result binding and full ledger replay checks between
summary and cash projections. Its final guard also runs when a projection
rejects. The new projection module is included in CODE_FILES so runtime code
digests cover the new read contract. The worker and formulas are unchanged.

Each request selects 1–24 months, default 12, after an exact existing month
cursor. This bounds response rows, not the computation: each page still
revalidates the whole completed result. No live/latest scenario is substituted.
An unavailable series remains null, with a null count and no cursor. A final
existing cursor returns an empty terminal page; an unknown cursor is rejected.

The browser requests 12 rows explicitly after verifying its completed result.
Both result IDs, scenario/revision, decision/formula, market hold and claim
labels must match. Money stays a decimal string; formatting adds separators
and a currency label. The table names KST month grouping and UTC minimum times,
supports manual next/first-page reads and native keyboard horizontal scrolling.
Connection reset, new calculation, result refresh and failed cash reads clear
prior cash rows. Unknown cash is “미확인”, never an invented zero.

## Verification

- Strict TypeScript, Vite production build and **46 web unit cases passed**.
  The cash client rejects mismatched result/hold IDs, timezone/cursor,
  numeric money, bad/duplicate months and extra fields; long signed decimal
  strings, declared zero and a KST month-boundary UTC instant remain exact.
- The initial combined backend check had **1 failed, 12 passed, 7 deselected**.
  Its helper appended the query to ASGI `path`, producing 404; the helper now
  supplies `query_string`. This was a test transport error, not a route change.
  That run passed the missing-service/different-model/OpenAPI cash case and
  the existing economic admission/completion case; it was not a green suite.
- After the query fix, final guard and code-digest addition, focused local
  PostgreSQL checks passed **11 cases in 159.74s, 9 deselected**: ten projection
  cases and actual admission/worker/completion/monthly HTTP. Read-only scopes,
  revocation during rejected projection, foreign tenant, unauthenticated read,
  unfinished job, invalid/terminal cursor, query bounds, exact identity and
  absence of tenant/raw inputs were checked. Projection fixtures alone are
  synthetic contract examples, not adopted farm records.
- The initial browser suite had **10 passed, 1 failed** because the wide table
  expanded the result grid on a 320px display. `minmax(0,1fr)` bounds that grid
  while preserving real table scrolling. Final **11 Playwright cases passed
  in 16.9s**: manual reads, unavailable/null presentation, exact large signed
  amounts, 13-month pagination and native ArrowRight scrolling at 320/768/1440px
  with 16px/32px root text, alongside existing retry paths. Internal table
  descendants may overflow their scroll region; the region and document may not.
- After adding focused section screenshots, the single relevant browser case
  passed **1 case in 5.7s**. Whole-page and cash-section captures are retained
  under `/tmp/ossf-cash-screens`; desktop and 320px/200% cash views were inspected.
- **Actual TLS/SCRAM/PostgreSQL/Chromium revised-input integration passed in
  169.00s** (`tests/web_economic_smoke.py -k True`, one passed/one deselected).
  It registered explicit rights and the revised joint shock, verified the actual
  derived payment and preserved original, ran the real economic worker/replay,
  then read the new HTTP page. Every displayed month, five amount strings and
  UTC minimum instant matched the server projection. The calculation retry
  retained one stored job. Only synthetic records/keys were used; no CLI ran.
  The registration-only parameter was not rerun. Scenario/calculation admission
  took approximately 21.0s/28.6s; no request deadline was increased. Operating
  latency, capacity and costs still require evidence.

## Design close and review

12ui reused original economics image SHA-256
`faf808bc9a97251530509bb10078e84c08b9912bbe8d5da654101a32ccd80113`, conversion
`c78c3be8-0563-43aa-9412-9837c541b34d`, and its unchanged LayerDoc SHA-256
`d7fe438a1ee53aaa0ec2894e54382c300bd8d0fb3f60305eed07d16f0df184e7`.
The kit `/tmp/ossf-ui-cash-close` completed all stages and bought nothing.
Its README, annotated plan and token CSS were inspected. DOM overlap was
29.1%, below the 60% anchor threshold; no pixel fidelity acceptance is claimed.

The new table retains the approved forest/ivory palette, `#f6f8eb` surface,
`#e0e5d4` border and 12px radius. Existing self-hosted Noto Sans KR remains.
The plan's title-to-subtitle and conditional-warning-to-percent mappings
would remove real semantics; they were rejected. Its 14px heading/navigation
token would reduce readability. The kit has no extracted raster files. The
previously excluded fake plots, decorative dial, unsupported success lamp/
growth imagery, unavailable navigation and icons are not reconstructed in CSS
or bought again. Functional content and product claim gates take precedence.
The actual monthly section was reviewed separately below the captured viewport.

Code review confirmed shared completion proof, current read authorization,
fixed public errors, bounded closed DTOs, exact strings and no added dependency.
Per-page full replay and broad-period computation remain performance limitations;
pagination is not operating capacity evidence.

## Remaining scope

General farm/facility and baseline/event/settlement inputs, break-even plan and
pinned trial scenario UI, actual runtime CLI research/review/assessment,
3D/replay, whole synthetic G1, independent source rights/measurements/future/
candidate-comparison evidence, and G4 operating/cost/capacity proof remain.
These synthetic checks do not prove harvest, purchased energy, future margin,
ranking, data approval or deployment. No whole task was checked off.
