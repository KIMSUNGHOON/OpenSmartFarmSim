# Saved-source farm composer layout refinement

Date: 2026-10-01 (Asia/Seoul). Small UI follow-up to the
[source/farm connection](source-farm-web-implementation.md) and its
[same-new-Run financial continuation](source-farm-financial-continuation-implementation.md).
The ongoing development CLI uses `gpt-6.1-sol` / `xhigh` as recorded in
[model migration evidence](cli-model-migration-implementation.md).
No recursive product CLI invocation or agricultural data adoption occurred.

## Changes and review

The selected source and economic summaries sit beside one another on wide
screens and stack below 1,120 px. Coordinates, exact UTC period/decision time,
the hypothetical-time marker and G0/G1 nonacceptance remain visible. Research
and collection UUIDs can be expanded with a native details control.

When using selected saved references, the new farm ID/revision stay editable
and visible. The remaining pinned references are grouped in a collapsed native
details element with their original read-only inputs. The direct-reference
path keeps its editable fields. Four native section links move focus to the
corresponding existing summary; React `useId` provides per-composer targets.
The long explicit physical form still extends below the first viewport.

The existing source browser case checks keyboard opening/closing of both
reference groups, exact microsecond decision time, read-only state and focus
movement from each section link. The existing selection-change, uncertain
registration, retry and account-generation checks remain in the focused run.

Code review covered controlled values, registration and agreement reset,
native form/navigation behavior, focus, mobile grid limits and asset loading.
The presentation change introduces one 7,424-byte local PNG and no new package
or remote asset request. Numeric inputs still start empty and existing current
source/rights checks decide registration. The decorative icon has empty alt text.

## Recovered design asset

The original authorized 12ui branch
`crt-4c79b699439094997489bcfaeb47ccc552c4be68` and its three conversions are
identified in the earlier [design record](source-farm-web-implementation.md#design-provenance-and-limits).
`12ui resume <conversion-id> --output layerdoc --out <path>` recovered each
existing LayerDoc and its extracted assets without a new conversion purchase.
All three recovered LayerDoc hashes exactly match the originals in that record.

The form conversion `cef09221-b24a-4757-97a7-e8eb4d9d1b8a` supplied
[cutout-15](../web/src/assets/cutout-15-b6376be1ea78.png), a document/magnifier
icon copied unchanged from its asset manifest. Asset SHA-256:
`b6376be1ea78d066b3a653b3b269313044284a6c3a72546b16df138081fb3a4b`.
The normalized source-image SHA-256 is
`65804d0d952fd6b01c5446b76c41785bade7d2feb9f4efa19935a7b6a0f8064a`.
Other recovered raster files remain in the local design record. No raster icon
was approximated in CSS. This provenance is an internal design record; the
public deployment asset license audit remains part of G4.

## Final target closes and visual limits

Each final state was captured after the section links were implemented,
against its own unchanged recovered LayerDoc at 1,536 × 1,024. The owning
repository was `web/`; each capture, conversion recovery and plan stage settled
with command exit 0. Draft/pick were skipped because the existing targets were
supplied. Each spend record has zero charged/list/provider cost and no new runs.

| State | Existing DOM overlap | Target overlap | Final public fixture capture |
| --- | --- | --- | --- |
| Source selection | 30.38% | 28.92% | [Source](artifacts/source-farm-refined-source-desktop.png) |
| Economic selection | 34.21% | 27.37% | [Economic](artifacts/source-farm-refined-economic-desktop.png) |
| Explicit farm form | 30.86% | 26.04% | [Form](artifacts/source-farm-refined-form-desktop.png) |

These are element-match percentages, not pixel similarity. All three kits
identify the requested capture but report low overlap below their 60% anchor
threshold. Each live capture was inspected beside the original corresponding
image. The source target contains unsupported researcher/climate/count details;
the economic target contains unsupported source groups and approval labels;
the form target contains unsupported facility/control/crop/owner defaults.
The current real controls and hold markers remain. This increment is a
readability/navigation improvement, **not precision design acceptance**.
The proposed global token edits were reviewed; existing locally hosted Noto
Sans KR and the established navigation/colors are retained for this small change.

Local durable kits: `/tmp/ossf-source-farm-design-20261001/final-close-{source,economic,form}-web/`.
An earlier kit used the monorepo root and failed when resolving `repo/src`;
the subsequent kits use the actual `web/` root. The zero-price dry-run planning
lookup also failed before execution. Neither attempt is acceptance evidence.

## Focused verification and resource cleanup

One local browser process at a time, one Playwright worker, `nice -n 10`:

- After grouping references and summaries, `source-farm.spec.ts`,
  `authored-form.spec.ts` and `authored-workflow.spec.ts`: **14 passed in 21.9 s**.
- After adding native section links, the affected existing keyboard case:
  **1 passed in 3.0 s**. This rerun is included in the same 14 distinct cases.
- Final `npm run build`, including typecheck: passed, 637 transformed modules,
  build 445 ms. Existing large chart/scene chunk advisories remain.
- Actual Chromium visual probe: three states × 1,536/768/320 px = **9 checks**,
  zero page errors and no horizontal overflow. It confirms side-by-side summary
  bounds on desktop, empty floor area/heat capacity, loaded icon, initially
  collapsed references and keyboard facility focus at each width. Expanding
  pinned references at 320 px preserves read-only state without overflow.
- The [desktop facility](artifacts/source-farm-refined-facility-desktop.png)
  and [phone facility](artifacts/source-farm-refined-facility-phone.png) captures
  were inspected. All committed captures contain public fixtures; the
  connection password input was asserted empty before capture.

The visual probe report is under
`/tmp/ossf-source-farm-design-20261001/final-review/report.json`.
Its browser closed, the owned preview process stopped and its session returned
terminal exit 143 after SIGTERM. Baseline PostgreSQL and unrelated user services
remain running. Generated drift in earlier authored-workflow captures was
restored rather than included in this UI change.

The [hosted continuation](source-farm-financial-continuation-implementation.md#hosted-verification-of-the-continuation)
passed at `5dc63f3`, before this UI diff. Hosted checks for this later layout
remain pending. `web-source-farm-authoring` stays unchecked until its final
acceptance evidence exists. Product CLI, independent G1, real-source/field/
future comparison and G4 evidence remain separate holds.

The later [final software UI acceptance](source-farm-web-implementation.md#final-software-ui-acceptance-2026-10-01)
records the exact `93e30a7` web and saved-source new-registration/financial/3D
hosted proof. It supersedes the pending UI checkpoint above without changing
the recorded low visual overlap or opening a product gate. The workflow's
separate financial-browser failure and subsequent latency change are explicit.
