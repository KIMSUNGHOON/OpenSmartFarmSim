# Authored Run economics and assessment web implementation

Date: 2026-10-01 (Asia/Seoul). Software candidate under
[the web contract](../contracts/web-authored-economic-assessment-v1.md), building
on [current server selection/history](authored-financial-selection-implementation.md).
Development judgment uses the ongoing exact `gpt-6.1-sol` / `xhigh` CLI session
recorded in [the model migration](cli-model-migration-implementation.md).
No real CLI was launched recursively. Agricultural validation and G1–G4
acceptance are outside this change.

## Implemented path

The owner selects a saved authored Run on **07 작성 Run 경제·평가**, or opens it
from the existing authored workspace. Current server selection fixes the Run,
farm revision, registration hash and economic input V3. The browser sends this
closed input without manually entered candidate or parent identifiers. Status,
money and monthly cash use the actual stored economic job; the three-field
assessment intent pins that exact economic parent and thermal job. Its current
hold report exposes the six existing evidence categories. The same thermal
parent opens the existing authored 3D viewer with its existing automatic load
option. Existing authored workspace 3D controls retain their manual load mode.

Index links remain metadata. Choosing a record rechecks current selection,
actual status, completed money and, for assessment, its actual economic parent
and current hold report. Reload/reconnect clears owner state and recovers through
these server links. When records exist, the owner must choose a current record
and explicitly prepare a new calculation. Refreshing history revokes that
preparation. Empty history permits the first calculation.

An unresolved POST retains one exact body/key, including after navigation,
and locks connection/reset, parent switching and other financial workspaces.
Retry sends only that body. A malformed positive response remains unresolved;
a bounded 4xx refusal allows a new intent. Generation fences discard old async
results. Read failures/current refusal clear amounts, cash and hold content.
Failed assessment admission retains the known economic job reference for
recovery while hiding old amounts. A hard reload does not retain an unacknowledged
intent; persisted links must be checked before an explicit new request.

Money is the server's Decimal string or null, formatted without numeric
conversion. Missing values remain `미확인`. The shared closed economic result
decoder retains the existing conditional/user/assumed/hold bounds; generic
economic result checks still require their exact candidate and market hold.
New job reads require their exact ID, stage and state. Financial history preserves
PostgreSQL microsecond ordering rather than comparing only JavaScript milliseconds.
No coefficient, tariff, purchased energy or numerical model changed.

## Focused verification

Local checks run sequentially at `nice -n 10`, with isolated browser processes,
loopback HTTPS and disposable PostgreSQL resources.

- TypeScript check passed.
- All web units: **122 passed, 10 files, 1.70 s**. The new financial boundary
  selection has 29 cases for exact V3 input, current job identity, parent/revision/
  registration/scope, closed response, full timestamp precision, ordering/cursor,
  exact money/null and the existing cash identity. Synthetic values include a
  Decimal above JavaScript's exact integer range.
- Focused Chromium: **19 passed in 23.7 s** — seven new financial cases and six
  each of existing assessment/authored workflow. It covers keyboard selection,
  existing-record preparation, exact POSTs, response loss/retry, bounded refusal,
  malformed positive admission, current refusal, reload recovery without POST,
  account change, cash pages, six holds and the same actual WebGL parent. No
  page overflow at 390 px or at 320 px with text enlarged to 200%.
- Production build passed. Existing lazy chart/scene chunks still produce the
  Vite warning for chunks above 500 kB; this is not a production performance
  measurement or a new bundle-size acceptance.
- Final actual HTTPS/SCRAM financial browser: **1 passed in 467.18 s** on
  PostgreSQL 16.15. The browser admitted a new economic job distinct from the
  completed fixture parent, verified all nine server money/null fields and the
  actual monthly cash row, admitted its exact thermal/economic assessment pair,
  read six holds, reloaded and recovered through GET, then rendered the same
  120-point authored Run in WebGL. Two POSTs, **29 HTTPS response headers**,
  maximum header latency **23.239 s**, unchanged full-body client timeout 30 s,
  zero unexpected console errors/warnings and two separately counted exact GPU
  ReadPixels driver warnings. Money worker **30.059 s**, assessment worker
  **71.197 s** against its 300 s lease. The assessment published no Run.

Initial fixture aliasing, selectors matching both newly available Run buttons
and missing initial 3D loading were corrected before the final checks above.
An early actual setup was interrupted to enforce existing-history preparation;
it has no acceptance result. A complete actual attempt reached new money and
assessment workers, recovery and 3D, then failed its console assertion: the
harness recorded two warnings only as generic kinds. The final harness uses
the existing 3D smoke's exact GPU ReadPixels warning regex, separately counts
only that known driver message and continues to fail all other warnings/errors.
That failed attempt is not acceptance. It ran in **482.12 s**, with workers
31.159 s (money) and 71.242 s (assessment). A corrected functional run passed
in 480.21 s, but its `requestfinished` observer collected only three responses.
The final observer uses response headers and explicitly requires every relevant
API path, without reading response bodies again through DevTools. The final
467.18 s run above verifies this correction. Header latency is not full-body
latency: full-body reads are bounded and independently checked through the
client's unchanged deadline and exact decoded UI values, not a network timing
measurement. These repeated runs are not additional distinct-test counts.

## Design evidence and limits

The 12ui branch used the existing forest/ivory dashboard as its starting image,
three ordered states, page concurrency one and HTML export. The initial download
ended with HTTP 503; resuming the same settled work collected all three images
and four HTML pages. The generated prototype failed one canonical-shell runtime
consistency gate. It is retained as failed and is not an accepted application.

The generated state structure informed saved selection, fixed inputs, conditional
money/cash and six hold categories. Its invented crop names, tariffs, annual
income and claims of all required inputs being checked were rejected under the
project claim gates. Existing components, semantic HTML and the existing
self-hosted Noto Sans KR font implement the functional flow; no generated image,
corpus image, icon or font was added to the product.

Each state's original LayerDoc was derived free from its settled viewport
conversion. Attempts to derive from the composed HTML IDs were refused; the
correct viewport IDs were then used. A first close with repository root failed
because that root has no `src`; repeating with the web root settled all three
target-based closes without purchasing another conversion. Captures use the
actual app on an isolated loopback Vite instance with explicit synthetic fixture
responses and automatic setup for the three states, not a private account.

| State | Original viewport conversion | Unchanged LayerDoc SHA-256 | DOM coverage |
| --- | --- | --- | --- |
| Saved Run | `ac1da83a-a09a-4389-8d81-cb2a1310db78` | `755a1d8115b8bca01e62c779d19ca2752592b342fec71260fe479a32e2972a2e` | 26.7% |
| Economics | `3e2d781f-6f9e-4559-9401-4f6ce4bae500` | `c1ab47b61e8145af3c6d9d61aff1b37e558145b1afce72dd4d0bb2ca33def5ae` | 16.4% |
| Assessment | `4ab51161-0459-4694-b7ff-451ac75cedc9` | `daa6ab7b876623cbc4081646aa9dc7e46b20d7e6a29469b8db0cf7f011fe6031` | 15.4% |

Actual CLI result: `emitted-low-overlap`, below the stated 60% threshold,
with capture identity matched. This is not precise design fidelity or safe
mapping for the whole page. The annotated plans/tokens were inspected; replacing
real controls with unsupported generated claims, copying approval check marks,
changing shared navigation and adding unavailable raster assets was rejected.
The existing palette, font, readable panel hierarchy and responsive stacking
remain. Generated layouts are separate states at 1536×1024; the implementation
keeps their required controls in one continuous workflow. These intentional
content/layout differences are recorded rather than hidden by buying new targets.
The prototype, exports, original targets and all close kits remain under
`/tmp/ossf-authored-financial-design-20261001`.

[Desktop capture](artifacts/authored-financial-desktop.png) and
[phone capture](artifacts/authored-financial-phone.png) were visually inspected
for selection hierarchy, preserved values, visible conditional/hold bounds,
readable controls and wrapped identifiers. They are synthetic software displays.
The cash table is independently checked by the browser cases and economic-state
close; an assessment refresh clears previously fetched cash content.

## Review and remaining holds

Review covers correctness (exact parents, current reads, retries, timestamps and
money), readability (one feature-owned client and workspace), architecture
(existing selection, result, cash, assessment and replay contracts), security
(closed projections, owner-state clearing, private-safe errors and no stored
token), and performance (bounded 20-link pages and the unchanged 30 s request
limit). No dependency, server formula, role, source policy or table changed.
The hosted workflow retains all previous selections and adds an explicit separate
financial browser selection with the same pinned dependencies and 25 min limit.
Workflow YAML and embedded Bash parse, changed local links resolve, and
`git diff --check` passes. Test-owned browser/server/disposable database cleanup
was checked; baseline PostgreSQL and user processes were preserved.

The full backend suite and local PostgreSQL 18 are not rerun for this web change.
Hosted final-head results remain pending. Synthetic CLI executables, test keys
and release fixtures prove software only. Actual product `gpt-6.1-sol` / `xhigh`,
independent release/custody, general region/source/farm orchestration, original
source rights and G0/G1/G2/G3a/G3b/G4 acceptance remain held. Future crop growth,
harvest, purchased energy, future margin and crop ranking are not enabled.
