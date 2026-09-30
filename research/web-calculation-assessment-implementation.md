# Calculation assessment web connection

Date: 2026-10-01 (Asia/Seoul). Current development policy is Codex CLI
`gpt-6.1-sol`/`xhigh`; this is software implementation evidence, not a product
model execution or agricultural acceptance record.

## Implemented path

The [web contract](../contracts/web-calculation-assessment-v1.md) connects the
existing verified thermal/economic assessment join to navigation item
**06 계산 평가**. The client sends exactly two parent job IDs and one stable key,
accepts only HTTP 202 and the supported assessment states, and refuses a
positive recommendation-shaped or unrelated response. The server remains
responsible for parent integrity, current rights/scopes and exact farm/context
binding. Separate authored thermal Run receipts are not yet supported here.

The workspace freezes uncertain admission, protects its retry key across view
navigation, and prevents connection changes or replacement writes while that
admission is unresolved. Bounded 4xx refusal allows an explicit new input.
Confirmed job IDs can be reopened by GET after reload. A later read failure
keeps the known ID for GET retry and clears unconfirmed current status/report;
it does not cause another POST. Account reconnection clears old display state,
and asynchronous results are guarded by a connection generation.

Public hold reports use existing bounded evidence categories and never expose
raw CLI prose or private farm inputs. The view shows no ranking, crop growth,
purchased energy or future margin result. Parent IDs are an internal operator
input; the general regional orchestration and automatic parent selection remain
required future work. Unknown admission reload recovery is still pending.

## Verification to date

- `npm run typecheck`: passed.
- Complete web Vitest selection, one concurrent worker: **93 passed in 1.44 s**.
  This includes exact assessment request/retry bytes, server identifier grammar,
  response stage/state/ID checks, forbidden extra-field projection and bounded
  HTTP/network errors.
- Focused actual Chromium fixture suite: **6 passed in 5.8 s**. It covers
  keyboard admission/hold, a lost response and stable retry across navigation,
  4xx reset, refusing positive status, saved GET lookup after reload and account
  reconnection, GET failure without another POST, one admission on double-click,
  wrong report stage, and phone overflow. Browser console/page errors in the
  capture case were empty. An initial double-click test expected the pre-submit
  button name; it was corrected to the actual retry label before the final run.
- Existing source shell, economics and authored farm workflows: **14 passed
  in 20.6 s**, including narrow/large-text layout, account reconnect, pending
  financial locks and 3D navigation. Incidental regenerated historical authored
  screenshots were restored; this change adds only the new assessment captures.
- Production web build: passed. The existing ECharts/Three.js lazy chunks still
  trigger Vite's >500 kB chunk advisory; it is not a browser console error or
  measured assessment performance claim.
- Desktop 1440 px and phone 390 px screenshots were inspected:
  [desktop](artifacts/calculation-assessment-desktop.png),
  [phone](artifacts/calculation-assessment-phone.png). They contain synthetic IDs
  and hold data only. The existing approved panel/form/status styles are reused;
  no CSS or new font was added. The attempted 12ui draft had already terminated
  for exhausted free allowance and insufficient prepaid wallet, so no new
  generated design or alignment kit is claimed.
- The explicit actual HTTPS/PostgreSQL 16.15/SCRAM browser test in
  [web_assessment_smoke.py](../backend/tests/web_assessment_smoke.py) and
  [its browser script](../web/e2e/real-assessment-smoke.mjs) passed:
  **1 passed in 157.73 s**, with one browser POST, five HTTPS responses,
  six persisted hold categories and zero browser errors. The browser uses the
  real API/DB and its unchanged 30-second request timeout; the CLI executable
  and authority fixtures are synthetic. No recommendation publication exists.
  The hosted authored API workflow now explicitly runs this test; PostgreSQL
  18/hosted proof for this change remains pending.

## Remaining acceptance

Browser fixture responses and fake CLI proposals establish software contracts.
Actual product CLI/supervisor custody, independent release, complete regional
farm/economic orchestration and G1 remain unaccepted. G0 rights/quality and
local, future and paired comparison evidence remain required for G2/G3a/G3b;
G4 still requires deployment proof. The broader task checkboxes remain unchanged.
