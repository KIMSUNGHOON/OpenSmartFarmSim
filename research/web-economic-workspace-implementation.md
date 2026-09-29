# Economic workspace implementation evidence

Date: 2026-09-29. Candidate for the
[economic web contract](../contracts/web-economic-workspace-v1.md); all existing
whole-task and data/model gates remain unaccepted.

## Development and scope

Work continued in the existing Codex CLI session
`01a0e064-b01b-7a22-8ef8-dd4afe0eb7dc`. The actual turn context at
`2026-09-29T09:21:23.011Z` records `gpt-6-sol`, `xhigh`. No recursive CLI or
product model execution was launched. The preceding status-only turn did not
change implementation state; this turn resumed the failing economic browser
integration rather than reducing the active goal to a read-only viewer.

The screen can discover exact stored versions, edit and register a numeric
assumption, register a selected baseline/joint-shock candidate, submit a
calculation, and read the actual completed public economic result. Original
server models, hash/rights/context checks and Decimal arithmetic stay at their
existing boundaries. An edited scalar is not silently inserted into a baseline:
new baseline and rights authoring remains required and is explicitly labelled.
The result display uses server strings/nulls and retains economic hold.

The API client shares the existing validators/transport with the location shell.
Source root fields derive from the existing three canonical server models,
with a default backend test checking the artifact for drift. Baseline and shock
read methods project only the safe selection fields; unused nested ledger data
is never posted as a replacement, calculated, or rendered. The new methods do
not approve data or broaden the operator's existing grants/runtime assembly.

## Bugs observed and corrected

- Actual numeric registration returned **422**. A minimal invocation of the
  original Store validator rejected `2026-09-29T08:00:00.000Z` and accepted
  `2026-09-29T08:00:00Z`; the form now supplies canonical whole-second UTC while
  keeping the user's date/time. The smoke checks both actual request and stored
  value `9007199254740993.0000000001` without JavaScript number conversion.
- After a successful numeric save, a lost calculation reply disabled its retry
  button because the prior numeric intent still existed. The browser regression
  was RED; the lock now reflects whether a calculation flow is pinned, so its
  pending phase can be replayed while the previous acknowledgement is retained.
- The populated form overflowed at 320px with 200% root text. Explicit
  zero-minimum form tracks and wrapping long identifiers/revisions resolved the
  observed overflow. The keyboard/resize test was RED before the fix.
- Initial real-flow checks allowed 45 seconds for two separate HTTP admissions;
  that was too short for the observed replay path. The test now waits for queued
  or a real error within a bounded phase. The browser's per-request timeout is
  unchanged. An initial test also incorrectly passed a public job projection to
  the private immutable-input verifier; it now reads the actual stored job row.
  These earlier failed runs are not acceptance passes.

## Verification

- Strict TypeScript, Vite build, and **35 Vitest cases** passed after the final
  source/result changes. The economic client checks exact decimal strings,
  typed/closed source data, cursor identity, expected admission status, null
  amounts, candidate identity, decision time and market-hold identity. Existing
  location tests remain unchanged and passed with the shared transport.
- **6 Playwright browser cases passed in 7.4s**: existing location/status/hold
  cases plus lost numeric, scenario and calculation responses. They verify
  immutable retry bodies/keys, frozen editing/authentication, preserved state
  across navigation, acknowledged-phase retention, no amounts before actual
  completion, negative/long decimal rendering, null display, keyboard controls,
  and 320/768/1440px at 100%/200% root text. Final screenshots
  were captured with the page at its top to avoid fixed/sticky elements being
  displaced in full-page captures; the focused calculation case passed in 3.4s. The mock baseline/shock fixtures
  deliberately exercise only the client projection; unused fields are not
  canonical server fixtures. They supply no source adoption or gate evidence.
  An initial keyboard helper advanced before the preceding read finished;
  explicit enabled/selection waits resolved that test synchronization failure.
- Actual TLS/API/SCRAM/PG/Chromium combined smoke plus source-field drift:
  **3 passed in 136.03s**, including the original location fake-CLI hold and
  upstream certificate rejection. Economic source/result data and keys are
  self-authored synthetic fixtures; no product model was invoked.
- After binding the result to the pinned decision/hold, awaiting the real retry
  response, and asserting one stored calculation job, the final economic smoke
  **passed in 143.21s**. It checks the stored exact scalar/canonical timestamp,
  actual scenario and calculation admissions, actual Decimal worker completion
  and result projection, UI totals/hold, completed duplicate admission, and no
  duplicate worker claim. The observed admissions took approximately **20.1s**
  and **27.6s**. These are local observations, not an accepted performance SLA.
  There is little margin against the current 30s request deadline; optimization
  and realistic capacity/latency proof remain an operating requirement.
- Changed Markdown paths resolved: **250 local targets, none missing**.
  `git diff --check` passed. No new dependencies, model assumptions, provider
  records, credentials, DB migrations, grant changes or backend arithmetic edits
  are included. The full backend suite was not rerun locally; the existing
  hosted workflow must be inspected at the new pushed head.

## Design close

The required 12ui target-based close used the unchanged original economic-state
LayerDoc SHA-256
`d7fe438a1ee53aaa0ec2894e54382c300bd8d0fb3f60305eed07d16f0df184e7`
from conversion `c78c3be8-0563-43aa-9412-9837c541b34d`. Its original economic
screen PNG SHA-256 is
`faf808bc9a97251530509bb10078e84c08b9912bbe8d5da654101a32ccd80113`.
All close stages settled
with **no purchases**. DOM overlap **29.1%** is below the 60% anchor threshold;
this is not pixel-fidelity or full design acceptance. The selector matches
include an incorrect title-to-subtitle mapping and a null-result message mapped
to price/cost/ranking. Those patches were rejected.

Only the valid currency-card surface/border/radius and existing forest/ivory
shell/card hierarchy were applied, with the existing self-hosted Noto Sans KR
family and legible A-style title. Desktop results stack to retain long exact
server strings; smaller screens stack the input and result regions. Actual
Chromium screenshots of populated mock data were compared with the original
economic screen, including narrow/enlarged text. These screenshots are software
fixtures, not farm predictions. Kits/screenshots stay outside the repository.

The target's missing raster plot depicts unsupported unit-price/profit ranges
and crop rankings, so it is excluded under PROJECT_SPEC/UI_DESIGN/AGENTS. The
decorative dial is explicitly excluded by UI_DESIGN. Status lamp and growing
plant art imply evidence/growth that the current path lacks; nav/play/gear/shield
icons concern absent routes, and chart/cost/cash/pen imagery accompanies controls
or series not yet implemented. They are excluded rather than reconstructed as
CSS or bought again. No generated raster, corpus reference, or extra icon asset
is shipped. Remaining monthly/3D/complete-input states need their own functional
implementation and matching design close.

## Remaining acceptance

Registration of the edited number does not update a selected existing baseline.
Baseline/rights/settlement authoring, full farm inputs, monthly/date and
break-even UI, market-hold details, real CLI three-stage execution/assessment,
independent release/reviewer evidence, 3D/replay and whole synthetic G1 remain
required. Real provider rights/QC/vintages and field/future/paired/operating
evidence for G0/G2/G3a/G3b/G4 are absent. Task checkboxes and the active goal
remain unchanged.
