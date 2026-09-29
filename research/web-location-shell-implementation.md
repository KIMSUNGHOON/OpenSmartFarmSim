# Location web shell implementation evidence

Status: verified software candidate for initial admission/status/hold only.
Date: 2026-09-29. [Contract](../contracts/web-location-shell-v1.md) and
[execution](../web/README.md) retain the remaining whole-task acceptance.

## Development and design

Judgments were made in the already-running Codex CLI session
`01a0e064-b01b-7a22-8ef8-dd4afe0eb7dc`, whose actual turn context at
`2026-09-29T08:02:20.872Z` records `gpt-6-sol`, `xhigh`. No recursive CLI or
product model invocation was launched for this change.

The approved 12ui p1/p2 responsive exports supply the shell and cards. Their
unchanged LayerDoc hashes are respectively
`495981212d8caa5ed072188a2e54a246bab09be21d21707a467721e0bc9aaa62`
and `4370380b0c8c9eb8520b35246f00ecee3abf88e42f151e2195db518150f40c14`.
Required target-based close kits completed with no purchases. DOM overlap was
34% for input and 29.7% for work, below the 60% anchor threshold; this is not
pixel-fidelity proof. Some matches are wrong (work h1 matched a sidebar button).
Only valid shared typography, surfaces, sidebar and card changes were applied.
The original decorative dial, fabricated completion/log/count/annual fields,
unused routes and crop/energy/forecast claims remain excluded by UI_DESIGN.
No generated raster or corpus reference asset is shipped.

Actual Chromium screenshots were viewed against their original approved
images. Keyboard submission/refresh, narrow layout and text enlargement were
checked in the implemented app. A native combined date/time control and auto
minimum grid track overflowed at 320px/200%; zero-minimum tracks and separate
UTC date/time controls preserve the period while fitting the narrow screen.

## Sources and dependency rights

Official sources consulted on 2026-09-29:

- [Vite server options](https://vite.dev/config/server-options): own TLS files,
  strict port, proxy and filesystem bounds.
- [Playwright release notes](https://playwright.dev/docs/release-notes) and
  [CI instructions](https://playwright.dev/docs/ci): exact installed Test
  `1.63.0` / Chromium `153.0.8010.12`; isolated contexts and browser installation.
- [Fontsource installation](https://fontsource.org/fonts/noto-sans-kr/install):
  self-hosted variable package `5.3.0`; actual package metadata records Google
  Inc., OFL-1.1 and source `https://github.com/google/fonts`. Unmodified notice
  SHA-256 is `18aabf190848725e2576eefb5c29ba06aac1029d02132252a7f312eac2e50cf3`,
  equal to the packaged public/build notice. No remote Google font call is used.
- [npm 11.16.0 release](https://github.com/npm/cli/releases/tag/v11.16.0): exact
  locally observed and CI-pinned tool. Node is `22.22.3`; added Node types are
  `22.20.4`. Dependencies are fixed by the reviewed package-lock integrity pins.

These are software sources and font rights, not agricultural or market G0
inputs. No farm/provider record was adopted.

## Focused verification

- Vitest: **23 passed**, including timezone-bearing real server times, invalid
  calendar rejection, exact HTTP status, streamed UTF-8 byte bound, auth/error
  redaction, DTO identity and exact repeat intent.
- Playwright mock boundary suite: **3 passed in 3.4s**. Keyboard queue/hold,
  lost response with the same body/key, and input/work at 320/768/1440 pixels
  with normal and doubled root text size passed. No broad WCAG certification
  or performance gate follows from these checks.
- Explicit `tests/web_shell_smoke.py`: **1 passed in 8.05s**, with actual SCRAM
  PostgreSQL roles, protected ApiRuntime, API and browser-facing TLS, verified
  upstream CA and isolated Chromium. Actual admission→fake process hold→manual
  read displayed two server-owned missing categories; repeated intent retained
  one stored held job, and no additional worker job remained. An untrusted
  upstream yielded 502 and no protected job result. Browser console/page-error
  checks on the successful flow were clean. No actual Codex model was invoked.
- The real connection exposed offset `+09:00` in PostgreSQL job timestamps.
  The original UTC-only client rejected it; a failing regression preceded the
  fix. Offset/microsecond strings now survive validation and KST display without
  being mislabeled UTC. Mock-only tests had not exposed this defect.
- Strict TypeScript and Vite build passed. npm audit reported **0
  vulnerabilities**. Playwright runner emitted only its NO_COLOR/FORCE_COLOR
  process-environment warning; this was not a browser console warning.
- Locked reinstall added 49 packages and audited 50 with no vulnerabilities;
  unit/type/build checks passed after it. The built OFL notice matches the
  original package. Static preview in Chromium loaded the declared font,
  requested no remote resources and used 12 font chunks / 207,492 encoded
  bytes across the two screens. All built font chunks total 3,519,780 bytes;
  the cold two-screen observation is not a performance acceptance threshold.
  Final screenshots were viewed after date/time separation. Review also
  increased the keyboard focus outline contrast inside the dark sidebar.

Hosted web CI is newly configured and must be observed at the exact pushed
head. This change did not run the full backend suite, public TLS/production
hosting, actual-model flow, whole farm/calendar/economic orchestration, map/3D,
independent reviewer/custody/release, provider G0, G2, G3a, G3b or G4. All
corresponding task checkboxes and gates remain unchanged.

## Hosted receipt for the web-shell head

Head `ec8107bdc57404cc5f3633637efc20678fdaf9c0`:
[web CI 36542677609](https://github.com/KIMSUNGHOON/OpenSmartFarmSim/actions/runs/36542677609)
completed successfully at `2026-09-29T08:26:47Z` (45 seconds). Its hosted log
confirms 23 unit tests, typecheck/build, 3 Chromium browser tests, and npm audit
with zero vulnerabilities. The browser suite uses mocked responses; the actual
TLS/SCRAM smoke above remains local evidence, not a hosted test.
[Compose 36542677509](https://github.com/KIMSUNGHOON/OpenSmartFarmSim/actions/runs/36542677509)
also succeeded for that exact head. Backend run `36542677529` was still live
when this receipt was recorded. These receipts confer no actual-model or gate
acceptance.

## Hosted receipt for stored-source read head

Exact head `a4cd8c3c78ed62715017834c493b5ffc5d8269c6`:
[web CI 36545970275](https://github.com/KIMSUNGHOON/OpenSmartFarmSim/actions/runs/36545970275)
passed at `2026-09-29T08:57:48Z` (44 seconds), including unit/type/build, audit
and Chromium checks.
[Compose 36545970349](https://github.com/KIMSUNGHOON/OpenSmartFarmSim/actions/runs/36545970349)
passed at `2026-09-29T08:57:40Z` (33 seconds), including database readiness,
persistence and cleanup. Backend run `36545970279` remains in progress at this
receipt. These are receipts for the prior committed source-read head, not the
new economic workspace or a gate acceptance.
