# Saved source and economic selection in the farm composer

Date: 2026-10-01 (Asia/Seoul). UI increment under the
[web connection contract](../contracts/web-source-farm-authoring-v1.md), following
the [accepted transport](source-farm-client-implementation.md). The development
CLI remains the exact `gpt-6.1-sol` / `xhigh` session recorded in
[model migration evidence](cli-model-migration-implementation.md). No real CLI
was recursively launched and no agricultural coefficients or data were adopted.

## Behavior and review

The existing 04 farm workspace opens a bounded composer with three steps:
saved source, economic version, explicit farm inputs. The first step reads the
authenticated research history, re-reads the selected completed research and
loads its collection/review activity. Only a completed collection of that
research can request current source references. Review records retain their
actual status and are not selectable as collections. A currently held or
unfinished research is not a source selection.

The second step lists economic metadata for the exact source context. Each
chosen candidate is re-read through the existing current selection client.
The source UUIDs, snapshot/context, decision time, market hold, economic pin and
evaluation dates become read-only form values. No farm ID/revision, facility or
crop value, numeric provenance, or rights agreement is supplied. The existing
direct-reference input remains an explicit alternative.

Changing either selection clears the old references, submission preview and
rights agreement. Explicit physical values remain a draft and must be reviewed
again. Direct edits to reference fields also cancel the rights agreement.
An uncertain registration locks both reference modes, selection changes, form
inputs and the workspace's return to saved-farm lookup. Its retry sends the
same request bytes. API/account changes unmount the old selection; generation
checks discard late responses. Tokens and the physical draft are not stored.

Pagination uses the transport's exact UTC microsecond/digest cursor. Empty
history, absent economic versions, permission failure and current selection
holds remain visible states; none manufacture a new source or economic input.
Software-only, ex-post replay, G0/G1 nonacceptance and assessment hold remain
explicit. The server rechecks registration; a browser selection issues no gate.

## Focused browser and build evidence

Node 22.22.3, npm 11.16.0, existing locked dependencies, Chromium, one worker and
`nice -n 10`. The focused run of `source-farm.spec.ts`, `authored-form.spec.ts`
and `authored-workflow.spec.ts` passed **14 tests in 22.0 seconds**. After the
direct-reference agreement reset, the affected source/form subset passed
**8 tests in 12.2 seconds**; these reruns are not additional distinct tests.

The seven new source cases check exact source/pin registration and identical
uncertain retry; reference/rights/preview changes; empty records and current
hold; foreign context and revoked source; 21 economic records across an exact
microsecond page boundary; a late old-account response and fresh reconnect;
keyboard activation and no horizontal overflow at 320/768/1024/1440 pixels.
The last case recorded zero page errors and captured all three states.
Existing direct form registration and saved-farm/job/Run recovery remain covered.
These browser cases use mocked HTTP responses, not HTTPS/database proof.

Type checking and the production build passed: 637 modules, 451 ms Vite build.
The existing >500 kB chart/3D chunk advisory remains and its limit was not raised.
Dist output and local browser/design kits are not committed.
The direct form case was subsequently extended to change its economic revision,
cancel the agreement/preview, restore the exact revision and reconfirm; its
focused rerun passed **1 test in 3.0 seconds**.

## Design provenance and limits

The previously started 12ui branch completed rather than being repurchased:
`crt-4c79b699439094997489bcfaeb47ccc552c4be68`, concept SHA-256
`5aed43c6724fb7f1124e81e33b3c5f8d50735b3a895cbf4459256948bd450c18`.
Hosted completion: 2026-10-01T05:16:16.107Z; prototype completion:
2026-10-01T05:17:15.235Z. It generated three inspected screens, four HTML exports
and a clickable prototype with a passed runtime gate. Warnings remain for
3/7 holding destinations and two skipped shell transplants.

The generated source-card, economic-list and pinned-input hierarchy informed
the existing React interface. The existing seven navigation routes, forest/
ivory colors and locally hosted Noto Sans KR remain. Invented researcher names,
crop/farm details, climate values, IDs and verification-complete labels were
rejected. Source/economic numbers are read only from the validated responses;
farm values start empty. The source target depicts unsupported evidence details
and the authoring target depicts unsupported prefilled farm facts, so those
content regions cannot be copied as assertions.

Original viewport conversions were derived to unchanged LayerDocs without a
new purchase:

| State | Conversion | Source LayerDoc SHA-256 |
| --- | --- | --- |
| Source | `b92a09ef-4005-4e07-99fd-c8aabecc9df7` | `b60cef3f8f62bcb848c2a4d43adf2b7ca07d82af7952e7bb231bc301800bd046` |
| Economic | `3a81a7f6-2c1e-4e1b-bde8-4bd350793971` | `186db5a59e089efbc0ed9f5ae22e622913109d372b063af4ad51e6b0f12f26e5` |
| Form | `cef09221-b24a-4757-97a7-e8eb4d9d1b8a` | `9a5e66beb7fec3bb6bb031d4833c0f2e7fdad2e2f86ab98e54cd7c5666844164` |

All three required target closes ran against the implemented local React app
with an isolated public synthetic fetch fixture, original unchanged LayerDocs,
1536×1024 captures and a ready-state bootstrap. Each capture/convert/plan stage
settled, with **no new purchase**. This is rendered design evidence, not another
real API test.

| Kit under `/tmp/ossf-source-farm-design-20261001/` | DOM overlap | Target overlap | Result |
| --- | --- | --- | --- |
| `close-source` | 30.4% | 28.9% | emitted-low-overlap |
| `close-economic` | 34.2% | 26.3% | emitted-low-overlap |
| `close-form` | 27.4% | 20.8% | emitted-low-overlap |

The READMEs and plans were inspected. These are below the kit's 60% anchor
threshold, so this increment does not claim design precision. Suggested changes
map synthetic status to field-data status, real UUIDs to unrelated explanatory
text and the input lead to a collection panel; those semantic mappings are
rejected. Added evidence/crop/equipment panels assert data not supplied by the
API. Missing map/loading, sprout/greenhouse and document/equipment rasters are
recorded by the LayerDoc-only kits; their extraction and any visual adoption
remain held. They were neither shipped nor replaced with CSS approximations.
Their unsupported regions are not added merely to increase the overlap score.
Existing local fonts and shared navigation tokens are retained rather than
importing an unreviewed global token patch for all seven routes.

The actual [source](artifacts/source-farm-selection-desktop.png),
[economic](artifacts/source-farm-economic-desktop.png) and
[form](artifacts/source-farm-authoring-desktop.png) full-page captures preserve
the public fixture's true UI. The lower facility, forcing/crop and rights
regions were separately captured and visually inspected; the added header and
source summary keep some controls below the first viewport, a remaining layout
refinement. All three phone states were recaptured at 320 px with no overflow
and zero page errors. Neither a top viewport nor these health checks establish
the missing visual precision. The kits remain local audit evidence.

The source dry run printed a zero-price plan then exited with the CLI's unrelated
run-directory lookup error. The actual source command and both subsequent
commands exited 0 with settled kits; no paid conversion was retried.

## Actual HTTPS/SCRAM new farm to 3D

The existing full authored software harness now exercises both direct references
and saved-source selection. It completes the exact queued research with the
fixture CLI and its owned collection with the actual collection worker before
the browser reads their authenticated history. The browser chooses the exact
collection/economic version, keeps physical inputs empty until it explicitly
enters the public fixture document, registers the farm, submits review and Run
jobs, and opens the actual posted immutable Run in Chromium/WebGL.

With PostgreSQL 16.15/SCRAM, the actual standard HTTPS runtime, locked Node/
Chromium and `nice -n 10`, `tests/test_authored_full_software_path.py` passed
**2 tests, 0 skipped, in 334.99 seconds**. This includes the changed direct
input path and the new saved-source path. The latter observed **14 successful
API responses**: six source/economic reads, farm registration 200, two job
admissions 202 and their status/summary/series reads. The direct path observed
eight responses. Both checked `no-store`, request methods, the UI registration
hash against the actual immutable server record, same-job/same-Run projection,
120 points, first/last keyboard times across 3D/chart/summary/HTML, responsive
320/768/1440 captures and zero console errors. Each reported four occurrences
of the narrowly accepted GPU screenshot readback warning.

Local evidence: `/tmp/pytest-of-sunghoonk/pytest-46/`, cases
`test_owned_farm_review_release0` (direct) and `...release1` (saved source).
Screens live in each `full-path-screens` directory. No private token or raw
restricted source is copied into this report. Headers are not a full-body
latency measurement; the client's existing 30-second full-body deadline remains.

Initial investigation exposed a too-short harness wait for current selection
and a CDP response-body reread after the SDK released it. The final harness
waits for the selected form within the existing transport deadline and compares
the displayed registration hash to the independently read server record. A
later attempt was disturbed by editing a live Vite module; the final two-case
run used fixed UI code. These failed attempts are not accepted evidence.
Product timeouts, rights/schema checks and release requirements were not relaxed.

## Hosted CI and resource checkpoint

The earlier full backend run
[36810716327](https://github.com/KIMSUNGHOON/OpenSmartFarmSim/actions/runs/36810716327)
on commit `7f698e695d2ea5ba346d55f371fb916ed6a5c606` ended **cancelled** at
2026-10-01T05:59:53Z. Its check annotation explicitly states that the job exceeded
**2h30m0s**. The backend test step was canceled, the distinct-UID step was skipped
and database/password cleanup passed. This is incomplete full-suite evidence,
not a test pass or a reason to raise the timeout. The separately recorded authored
smoke, web and C0 runs on that exact commit remain separate results.

New local source/browser commits have no hosted result yet. Before batching the
next push, the full backend CI needs bounded partitions preserving every test
and the UID check. No new production gate is granted by the two focused local
browser chains. The owned local fixture stack and design preview were stopped;
the existing PostgreSQL baseline and unrelated user processes were preserved.

## Remaining contract acceptance

`web-source-farm-authoring` remains unchecked. Extending this new farm/Run in
the same actual HTTPS/SCRAM test through economics/assessment and back to the
same 3D is still required. The target closes completed but visual refinement
and missing asset adoption are not accepted. A fixture CLI and test execution/release signatures
prove software behavior only. Actual product CLI, independent execution custody
and release/full G1, real-source G0, field G2, forecasting/comparison G3 and
deployment G4 remain separate holds.

## Later same-Run financial continuation

The [subsequent local proof](source-farm-financial-continuation-implementation.md)
extends the saved-source case through the newly registered Run's economic
calculation, all monthly cash cells, six assessment holds, reload/reconnect and
the same 3D Run. It passed one focused actual HTTPS/SCRAM browser case in
442.43 s; 27 financial response bodies completed within the unchanged 30-second
limit. This supersedes the missing local financial-continuation checkpoint
above. Visual refinement, new hosted verification and actual product CLI/
independent G1/G4 acceptance remain separate.

## Final software UI acceptance (2026-10-01)

The source-path task's later UI revision is exact commit
`93e30a7676b335a45d2fbc2b466c715bce583647`. The
[authored PostgreSQL workflow 36843547162](https://github.com/KIMSUNGHOON/OpenSmartFarmSim/actions/runs/36843547162)
has terminal results. Its **authored-browser suite passed 4 cases in 851.68 s**,
including the saved-source **new registration** path, new authored Run, server
money and cash, six assessment holds, reload/reconnection and the same 3D Run.
This is the final layout/registration-lock revision, rather than the earlier
pre-layout evidence. Both initial paths reported 120 points, zero console/page
errors and four recognized GPU capture warnings. The source path completed
14 initial API responses and 27 actual client reader EOF financial bodies;
the latter's maximum was **26.3284 s** within the unchanged 30-second limit.
Its financial continuation made two admissions, displayed one complete cash
month and recovered the same assessment and Run.

[Web workflow 36843547345](https://github.com/KIMSUNGHOON/OpenSmartFarmSim/actions/runs/36843547345)
passed **154 unit tests, 50 Chromium cases**, typecheck/build and zero audit
findings on that exact commit.
[C0 workflow 36843547161](https://github.com/KIMSUNGHOON/OpenSmartFarmSim/actions/runs/36843547161)
also passed. The local client/selection/combination/recovery/keyboard/registration
proofs, [layout refinement](source-farm-layout-refinement-implementation.md),
adopted icon and three target-close runs complete the source-path software
acceptance. Low visual overlap remains a recorded limitation; pixel/design
precision is not claimed. Missing farm values stay empty and no crop, tariff,
harvest, profit or gate approval is taken from a generated design.

The same authored workflow **failed overall** because its separate
financial-browser suite stopped on an unresolved assessment admission. The
other six suites and all seven cleanup steps completed successfully. Its failed
case is not included as passing acceptance, and the six-part full backend run
is still separate. [Fresh grant audit batching and body diagnostics](runtime-role-audit-batching-implementation.md#all-role-query-batching-follow-up-2026-10-01)
address the measured latency risk and have separate local evidence; hosted
verification of that subsequent backend change remains pending.

`web-source-farm-authoring` is now checked for this explicit software scope.
The CLI/execution/release fixtures do not provide product model invocation,
independent custody/release/full G1, actual source/field/future comparison or
G4 evidence. Those holds remain. Hard reload of an unacknowledged page-memory
registration still requires the existing server history and does not constitute
durable unknown-intent recovery.
