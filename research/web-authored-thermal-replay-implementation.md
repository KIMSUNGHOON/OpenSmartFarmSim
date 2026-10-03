# Authored thermal browser replay implementation

Date: 2026-09-30 KST. Scope: [web contract](../contracts/web-authored-thermal-replay-v1.md).
This session is the existing Codex CLI `gpt-6-sol` with `xhigh` effort; no
nested CLI was launched. Browser data here are explicit HTTP doubles, not
farm measurements, product CLI output, approved release or G1 evidence.

The browser now chooses fixed or authored thermal replay. The authored SDK
discovers a completed job's Run, reads its summary and 120 points, rejects
wrong IDs, scope, trace shape, time, count, uncomputed fields and invalid
numbers, and hands the same selected point to the existing 3D scene, chart,
summary and table. A kind or job change invalidates a pending response.
The backend-authored read route existed before this work, but standard HTTPS
runtime assembly for its store remains outstanding.

The required 12ui design workflow used the existing
[desktop capture](artifacts/thermal-replay-desktop.png), selected candidate B
in `/tmp/ossf-authored-replay-12ui` and added a compact mode choice above the
job ID in the existing visual language. The kit was unanchored (0% DOM
coverage); no pixel-fidelity acceptance is asserted. Its proposed static
greenhouse and chart raster layers were not shipped: a stored Run must change
the actual WebGL geometry/color and chart at each selected point. Its three
purchase IDs are `crt-ef3f9a41247f1632b2141588068be839ff3c1d2f`,
`bfbb38f7-05ea-4ec1-928b-6b55cc58767c`, and
`f78a9800-d346-45c8-9900-03a984b8a1a6`; the kit reports a combined
stage ceiling of $0.67, not settled spend.
After implementation, `12ui improve` compared the
[captured browser state](artifacts/authored-thermal-replay-desktop.png) with the
chosen unchanged LayerDoc in `/tmp/ossf-authored-replay-close`. It settled with
no additional purchase but was image-input/unanchored (0% DOM coverage), so
there is no measured pixel-fidelity claim. Visual inspection confirmed the
mode choice above the job selector, synthetic notice, existing scene and
summary arrangement. The proposed chart and greenhouse bitmaps remained
excluded because they would conceal changing Run values.

Verification on this slice: `npm run typecheck` and `npm run build` passed;
Vite still reports its existing 500 kB warnings for the lazily loaded scene
and chart chunks. `npm run test` passed 68 tests across 6 files; focused Chromium `playwright test
e2e/replay-authored.spec.ts e2e/replay.spec.ts` passed 6 cases. The authored
case asserted actual WebGL draw calls, a changed canvas image, all six raw
values and the same final UTC point across scene/chart/summary/table. The
malformed scope returned an explicit hold with no scene; changing replay kind
cleared the old display. The existing fixed path also passed its WebGL loss,
keyboard, 320/768/1440px, reduced-motion and 200% text cases. The
[authored browser capture](artifacts/authored-thermal-replay-desktop.png) is a
software-fixture screenshot, not a farm prediction. A normal HTTPS/SCRAM
authored browser smoke, actual product CLI invocation, independent release,
full G1 and production checks were not run or accepted here.
