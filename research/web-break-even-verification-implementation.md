# Web asynchronous break-even verification implementation

Date: 2026-10-02 (Asia/Seoul). Existing exact development CLI: `gpt-6.1-sol`
/ `xhigh`; no recursive Codex CLI. Scope: an internal `economic-break-even`
/ `api-flow` web increment under the
[web verification contract](../contracts/web-break-even-verification-v1.md).

## Behavior

The SDK sends only the actual completed calculation UUID to verification
admission and rejects a parent UUID, other-stage or open Job response. Legacy
and verified result methods share the existing strict closed decoder and
524288-byte bound. Both preserve exact money strings, null cash, plan/context/
calendar/target/unit/grid bindings and Assessment hold; no economics is computed
in the browser.

The existing workspace first reads calculation status. On succeeded, a deliberate
user action requests verification. Separate status and identifiers distinguish
the two Jobs. Unknown admission freezes its parent, editing, plan resubmission
and connection changes; confirmation repeats the same parent request. Navigation
retains the existing in-memory state. Once the child exists, refresh reads it
and only its succeeded verified result. Every refresh clears old amounts before
current checks. The screen issues no synchronous full-replay result request.

## Local software checks

- SDK RED: **6 failed, 4 passed** because the two new methods were absent.
  GREEN: **10 passed**, including wrong-child/stage/open-schema rejection and
  shared exact-money/hold validation for both result paths.
- Chromium RED: the lost-verification case failed because the deliberate
  verification button did not exist (**6.4 s** case). After implementation,
  focused **4 passed in 8.6 s**: lost scenario, plan and verification responses,
  queued child without amounts, malformed completed result clearing old amounts,
  canceled child clearing old amounts, and missing sale/collection records.
- Full web unit selection: **160 passed across 11 files in 1.87 s**.
  Type checking and production build pass. Vite retains its existing warning
  for the lazy Three/ECharts chunks above 500 kB; no dependency or chunk policy
  was changed.
- Full `CI=true` Chromium selection: **51 passed in 1.3 min**, one worker,
  no retries/skips. Existing tracked screenshots rewritten by the suite were
  restored from the initially clean tree; fresh focused captures stay private.
- Added mobile unknown/queued verification captures and overflow assertion:
  **1 passed in 3.0 s** after the full run. The implementation is unchanged.
  Existing completed-grid captures cover 320/768/1440 px at 16/32 px text with
  native keyboard table scrolling. Desktop result and 320 px unknown-admission
  images were visually inspected. Their amounts are synthetic software fixtures.

## Design comparison

The original approved economic LayerDoc was recovered from completed conversion
`c78c3be8-0563-43aa-9412-9837c541b34d` without a purchase; its exact SHA-256 is
`d7fe438a1ee53aaa0ec2894e54382c300bd8d0fb3f60305eed07d16f0df184e7`.
The first close used the repository root and failed plan generation because
that root has no `src`. Changing the durable record's repo was rejected, so a
new free kit used the actual `web` package. Capture/target/plan stages settled
at `/tmp/ossf-ui-break-even-verification-close-web`, with **31.3% DOM overlap**
against the tool's 60% threshold. This is not pixel-fidelity acceptance.

The kit and plan were inspected. Its title/subtitle, connection-to-demand,
action-to-badge and navigation mappings do not preserve this product's meaning.
Unsupported sample quantities/profit/rankings, growth/status art and decorative
dials remain excluded under the existing UI/spec claim boundary. The previously
adopted self-hosted font, forest/ivory palette and readable card/notice styles
already serve the added controls. The upper viewport comparison does not prove
the new lower section; the independent focused captures/checks above cover it.
No paid asset, generated farm output or new CSS system was introduced.

## Remaining evidence

The [actual SCRAM/HTTPS/browser selection](../backend/tests/web_break_even_smoke.py)
completed on PostgreSQL 16.15: **3 passed in 263.31 s, no skips**. Each case
submits an actual calculation from the browser, checks its immutable input and
ordered pins, completes its leased worker, and admits a separate verification.
A separate Python process executes the protected operator using fresh private
store configuration. The actual verification input pins the same calculation;
its independently read projection matches the original server grid projection.
The browser displays exact strings/nulls/hold and makes no synchronous result
request. Actual SQL confirms one calculation and one verification intent.

| Response loss | SDK body EOF observations | Maximum seconds |
| --- | ---: | ---: |
| None | 15 | 10.1071 |
| Plan admission, then receipt recovery | 14 | 6.0410 |
| Verification admission, then same-parent confirmation | 15 | 10.3936 |

The [test-only observer](../web/e2e/observe-api-body.mjs) measures the SDK's own
`reader.read()` through EOF, including the completed verification result.
All **44 observed complete bodies** are `no-store` and finish within the
unchanged **30 s** client limit. Intentionally aborted admission replies and
error bodies the SDK does not consume are not body-EOF observations. Request
counts separately prove one scenario pair/plan write and, after verification
reply loss, two exact-parent POSTs resolving to the one stored child. No page
errors or unexpected console warnings/errors occurred; each intentional reply
loss has exactly one expected network console error. Browser/server/child
process resources close. No real Codex CLI or independent authority runs here.

Tested source SHA-256 values:

| File | SHA-256 |
| --- | --- |
| `web/src/break-even-api.ts` | `860b2d0d71013f5d4492419824bc85322bde7a525099cf8e17ed7ef49ae87c02` |
| `web/src/BreakEvenWorkspace.tsx` | `877e53870aa871cf0c8c07fd2d0de2220a29f3fcd0df4d6889465ca47e37cc4c` |
| `web/src/api.ts` | `b506629e0221d8f287b4b8f94d0bd64ffbea54fdd824ea386575b1f16f863dc9` |

Changed Markdown's **439 local file/anchor links** resolve, the Python browser
harness parses, and the JavaScript harness passes `node --check`. Separate
unstaged and staged diff whitespace gates pass. Hosting checks of earlier
`160118c` cover its API/operator and prior web implementation, not these later
web changes; its backend workflow is still live.

Two-trial synthetic software checks cannot establish actual 256-trial worker/
HTTP/reader capacity, cancellation/retry/rights withdrawal budgets, automatic
workers, protected deployment or reload recovery. Actual product CLI, independent
execution/release/G1, source G0, local G2, future G3a, paired G3b and operating
G4 remain separate evidence requirements. Parent task checkboxes remain unchecked.

## Hosted web and authored follow-up at 6a264c6

For exact commit `6a264c6bd20a7202e03bee139de97463410dfc19`, the
[web workflow](https://github.com/KIMSUNGHOON/OpenSmartFarmSim/actions/runs/36946195030)
completed successfully: **160 unit tests across 11 files** and **51 Chromium
cases**. The [C0 workflow](https://github.com/KIMSUNGHOON/OpenSmartFarmSim/actions/runs/36946195056)
also completed successfully.

The [authored workflow](https://github.com/KIMSUNGHOON/OpenSmartFarmSim/actions/runs/36946195202)
completed all seven PostgreSQL 18.6 selections and their database/password cleanup:

| Selection | Passed | Suite seconds |
| --- | ---: | ---: |
| API | 104 | 355.21 |
| Economics | 13 | 474.89 |
| Assessment | 15 | 689.18 |
| Assessment HTTPS | 1 | 321.20 |
| Financial selection | 3 | 703.95 |
| Authored browser | 4 | 731.73 |
| Financial browser | 1 | 353.03 |

These are **141 executions**, including the existing fake CLI/test authority
paths. The earlier `160118c` broad backend run has since
[completed successfully](api-break-even-verification-implementation.md#terminal-hosted-backend-at-160118c).
The `6a264c6` [broad backend follow-up](https://github.com/KIMSUNGHOON/OpenSmartFarmSim/actions/runs/36946195060)
is still live at this observation; its aggregate is not accepted yet.
These hosted results do not cover the later uncommitted admission performance
candidate or establish the actual 256-trial budget or independent product gates.

The later [terminal 6a264c6 backend record](break-even-calculation-fence-implementation.md#terminal-hosted-backend-at-6a264c6)
resolves that live observation: all six PostgreSQL 18.6 partitions/aggregate
completed with **2,294 passed, 0 skipped**, separate Linux UID **4 passed** and
successful cleanup. The later admission performance candidate is still separate.
