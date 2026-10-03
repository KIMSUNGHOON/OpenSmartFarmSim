# First internal thermal replay implementation

Date: 2026-09-30 KST. Status: software implementation candidate; full
`web-shell`/`web-replay`, product CLI, independent G1 and production acceptance
remain open. Scope: [viewer contract](../contracts/web-thermal-replay-v1.md).

## Development and data boundary

This work used the existing Codex CLI session, model `gpt-6-sol`, effort
`xhigh`. Its `turn_context` at `2026-09-29T14:47:19.119Z` in rollout
`rollout-2026-09-27T10-04-50-01a0e064-b01b-7a22-8ef8-dd4afe0eb7dc.jsonl`
records that model and effort. No nested CLI was launched. The integration
fixture's worker uses a fake CLI and test-owned signing/release authorities;
it is not an actual product model invocation or independent release proof.

No backend application, physics, money calculation, schema, permissions or
publisher `CODE_FILES` changed. The new explicit smoke is a test harness.
The viewer discovers an owned completed job's Run, then reads its existing
summary, series and manifest. Each of the four GETs retains the existing
bounded request, timeout, Bearer header, no-store and omitted-cookie policy.
The client checks closed DTOs, fixed synthetic/ex-post scope/model/units,
manifest/trace pins, 120 ordered one-minute end points and finite quantities
before displaying anything. This is response coherence checking; the server
owns current authorization, rights, custody and gate decisions.

One selected point supplies the scene, graph, summary and table. Kelvin/°C
and relative-humidity/% conversions affect display only. Supply energy is
per stored one-minute interval, not a cumulative or purchased-energy value.
Color spans this Run's observed numeric range; the heat bar is normalized
to this Run's maximum delivered heat. Neither scale is a crop threshold.
Geometry is an explanatory single-zone house without surveyed dimensions,
crops, lighting, water, ventilation or inferred control commands.

The read result is cleared on input or API changes, and an epoch rejects
late responses. Playback is off initially, advances one stored minute per
screen second, pauses on manual selection/hidden document and is disabled
by reduced motion. WebGL absence/loss retains every HTML value and time
control; restoration recreates the scene at the current selected point.
Renderers dispose resources and observers on teardown. Resize work is
coalesced into one requested frame; there is no permanent animation loop.

## Dependencies and primary sources

The npm registry was checked before installing exact versions with strict
peer checks. `package.json` and `package-lock.json` pin:

| Package | Version | Role / license |
| --- | --- | --- |
| three | 0.186.1 | WebGL2 scene / MIT |
| echarts | 6.1.0 | core modules, SVG line chart / Apache-2.0 |
| @types/three | 0.186.0 | development types / MIT |
| zrender | 6.1.0 | locked chart dependency / BSD-3-Clause |
| tslib | 2.3.0 | locked chart dependency / 0BSD |

Implementation consulted [Three WebGLRenderer](https://threejs.org/docs/pages/WebGLRenderer.html),
[OrbitControls](https://threejs.org/docs/pages/OrbitControls.html),
[ECharts core imports](https://echarts.apache.org/handbook/en/basics/import/)
and [SVG rendering](https://echarts.apache.org/handbook/en/best-practices/canvas-vs-svg/).
Original Three, ECharts LICENSE/NOTICE/d3, zrender, and tslib license/copyright
notices are copied into `web/public/licenses/`; tslib line endings are normalized
to LF without changing the license/copyright text. The installed package and
[upstream 2.3.0 declaration](https://raw.githubusercontent.com/microsoft/tslib/2.3.0/package.json)
confirm 0BSD; an initially mislabeled copied filename was corrected before
commit. Existing self-hosted Noto Sans
KR and its OFL notice remain. No stock/generated 3D artwork is shipped.

The shell lazily loads the 12KB replay UI. Three and ECharts load separately
only after a coherent Run is available; table/text rendering can proceed
while these modules load. The initial shell remains about 303KB minified.
The scene and chart chunks remain about 557KB and 521KB (139KB/177KB gzip).
Vite's 500KB warnings remain visible. The default was not raised, and this is
not a production download/frame-rate/device-budget acceptance. The
[Rolldown documentation](https://rolldown.rs/reference/OutputOptions.codeSplitting)
was consulted; no manual chunk grouping or new bundler configuration was added.

## Verification and fixes

The SDK's initial ten cases failed before implementation. After correcting
a test UTC spelling (`.000Z` versus canonical `Z`), all ten passed. They
reject identity, trace, scope, unit, count, order, nonfinite value, denied
display rights and extra uncomputed crop fields. Full Vitest recorded
**60 passed, 5 files, 308ms**; the final repeat after a fresh locked install
passed **60 in 312ms**. `npm ci --strict-peer-deps` installed 60 packages and
audited 61 with zero vulnerabilities. TypeScript and the Vite build passed; bundle
warnings above remain.

Actual isolated Chromium runs recorded **18 passed in 35.7s** across the full
web suite. The final focused replay run recorded **4 passed in 18.1s** after
adding actual canvas-image change and all-six graph selection checks. It
covers actual WebGL draw calls, shared points after keyboard/time controls,
pause, restored context after loss, 320/768/1440px resize, reduced motion,
200% text, stale reads, connection changes and malformed manifest rejection.
No Chrome DevTools MCP was available; the existing locked Playwright Chromium
was used without a personal profile. Response doubles in this browser suite
are explicitly software fixtures, not gate-approved farm data.

Concrete fixes during inspection:

- Absolute hidden table text lacked a local containing block and extended
  document scroll height far below the actual page. Positioned timestamp
  buttons contain that text; vertical overflow checks cover the regression.
- A populated chart's default grid minimum kept its old SVG width after
  narrowing an already loaded page. `min-width: 0` allows its container to
  shrink. Resize observers defer sizing to one frame to avoid observer loops.
- The input panel folds after loading; it can reopen to change/reread the
  job. All six summary fields and the scrollable table remain available.

The explicit real HTTPS/SCRAM smoke was developed through observed failures:
69.78s (test incorrectly unpacked a job dict), 111.60s (CDP could not reread
an SDK-released response body), 108.94s and 118.47s (resizing exposed chart
overflow), and 107.04s (captured GPU warnings). The harness now compares with
the server projection of the verified immutable Run, supplied through stdin;
network verification still checks four actual authenticated 200/no-store GETs.
Tokens are never put in argv, screenshots or reported network records.

The four warnings were reproduced independently as Chromium/ANGLE's exact
`GPU stall due to ReadPixels` performance diagnostic. The
[Chromium change](https://chromium.googlesource.com/chromium/src/+/3c071403b0115bb92ef085b4fc806930e712065c)
records this same console line in WebGL tests; [ANGLE's pinned source](https://chromium.googlesource.com/angle/angle/+/b4efc051da9dc884087f1ace8185d410d4349d02/src/libANGLE/renderer/vulkan/vk_helpers.cpp)
emits it during CPU pixel readback. Only that exact line is classified and
counted separately in the software-GPU screenshot harness. Other warnings
and all page/console errors still fail. This does not suppress product
warnings or establish hardware performance.

The final actual HTTPS/Bearer/SCRAM/Chromium smoke recorded **1 passed in
104.10s**, with four actual authenticated 200/no-store reads, 120 points,
first/last and a subsequent keyboard-selected point matching the server Run,
and all six summary/table quantities matching the immutable server projection.
Desktop/tablet/phone resizing had no remaining document overflow. Page/console
errors and unexpected warnings were zero; the four classified GPU readback
warnings remain reported. The upstream verifies the test CA; only the isolated
browser context ignores its disposable browser-facing certificate error.
Services and test roles/password files are cleaned up.

These are actual captures of that synthetic server Run, not generated design
images: [scene and summary](artifacts/thermal-replay-scene-summary.png),
[desktop page](artifacts/thermal-replay-desktop.png), and
[mobile page](artifacts/thermal-replay-mobile.png). No token or private farm
record is present. Their input authorities remain test fixtures as described
above; images are renderer evidence, not agricultural validation. The
[sanitized browser report](artifacts/thermal-replay-browser-report.json) records
the four read paths, warning count and capture hashes.

## Design review

The actual original p3/slot c image was inspected, SHA-256
`5d1fe99009a76203d68bec722e425d28479d9e8aa2dab330fd3daff4b20c1ca9`.
Its original conversion `60761b90-a85e-4ac5-8d7a-f590b5fcf8f7` yielded unchanged
LayerDoc SHA-256 `9624dd0191efd94208507f910cb2b64dcf3d08f9cc9c4d8332acbf2552cedee7`
without a purchase. The generated responsive p3 HTML was retained as a layout
reference; its fake data and raster greenhouse are not product assets.

Target-based `12ui improve` kit `/tmp/ossf-ui-thermal-close-v4` completed
capture/plan with no purchase. Its README, token CSS and annotated plan were
reviewed. Initial capture used the repository rather than web source root;
a subsequent capture ran before its asynchronous test setup finished, and
the next one had scrolled to the setup button. The final kit corrected the
source root and explicitly awaited the loaded state and scrolled to the top.
That temporary response-double preview was removed from the workspace.

DOM overlap is **30.4%, below 60%**; this is not pixel-fidelity acceptance.
The scene/input `#f8f6ed` surface and `#e0dbcf` border were adopted while
keeping the readable existing font, heading sizes and shared shell. The plan
misidentifies admission as the scene, scene as chart, timestamp as a label
and numeric values as headings; those semantic replacements were rejected.
Original raster charts, crop/equipment illustration, dial, decorative status
lamp/icons, made-up coordinates and unsupported CO2/light/water/ventilation
numbers remain excluded under the product contract. Replacing real source
values with that art would misstate results. Scene/graph/table regions and
mobile states are inspected independently of the kit's first viewport.

## Remaining acceptance

Focused local checks were used; the full backend suite, a local Docker app
profile launch, actual product CLI and independent custody/release were not
run for this frontend slice. Hosted CI is reported by its exact commit head
in the draft PR; earlier passing runs are not proof for a later head. All
676 checked local relative Markdown links exist. Task counts remain 19
accepted / 20 pending, not a measure of overall product completion.

Full farm input authoring, paired farm Assessment, physical heat-to-purchased
energy/cost evidence, actual product CLI/supervisor/custody/release and whole
G1/G4 remain open. Real-source G0, local G2, future G3a and paired candidate
G3b still need their independent rights/measurements/validation. Existing
task checkboxes are unchanged. A visible synthetic scene cannot establish
crop growth, harvest, future margin or a crop ranking.
