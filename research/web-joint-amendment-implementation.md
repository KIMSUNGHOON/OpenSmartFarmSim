# Saved economic assumption to joint revision — software candidate

Date: 2026-09-29. This extends the [economic workspace contract](../contracts/web-economic-workspace-v1.md)
and its [prior evidence](web-economic-workspace-implementation.md). Existing
whole-task checkboxes and G0–G4 holds remain unchanged.

## Actual development context and decision

The existing Codex CLI session's latest turn context was inspected at
`2026-09-29T09:59:01.741Z`: model `gpt-6-sol`, effort `xhigh`, thread
`01a0e064-b01b-7a22-8ef8-dd4afe0eb7dc`. This is development context, not a
product-runtime invocation receipt. No recursive CLI or subagent was launched.

Inspection of `MarketScenarioService._prepare`, `JointShock`, `InputRights`,
`EconomicNumber`, source intake and the immutable candidate store established
that an existing numeric edit can already produce a new derived ledger. No new
backend endpoint, model, money calculation, coefficient or data adapter is
required. A baseline fork would duplicate that established contract.

The browser first reads the actual saved number and complete selected shock,
checks source receipt hashes, and offers matching existing edit slots. It requires
explicit selection and ownership/use/display confirmation; redistribution is
denied. The nine EconomicNumber fields are UTF-8 sorted-key JSON hashed; owned
scope fields, tenant and source metadata are not included. A server-produced
Unicode/microsecond/high-precision Decimal hash is a unit-test golden value.
Money remains a string throughout; time ordering preserves six fractional digits.

The new rights body and cloned joint body have pinned keys. Only the selected
numeric edit and the joint/edited-driver revisions, rights and later knowledge
times change. Existing hypotheses, other changes, contract caps and settlement
bindings remain unchanged. The server continues to validate all references,
rights, timing, conservation, units and settlement applicability.

`settlement_path_sha256` includes sale-linked collections/costs/deductions.
Changing one of those can invalidate existing settlement evidence. The browser
preserves that evidence and the server rejects an unsupported path; no new
settlement evidence is invented. The actual positive integration uses the
self-authored production cost's payment, whose sale_id is null. General
settlement and baseline/event authoring remain required.

Rights `200`, then joint `200`, then an exact joint read/selection are distinct
phases. A lost write response retains that body's bytes/key and locks selection,
editing and auth. Acknowledged phases are not reposted. A failed read after the
two acknowledgements retries only the read. Calculation remains a separate user
action. State is retained across navigation in memory, not browser reload.

## Verification

- Focused builder suite first failed because the implementation did not exist,
  then passed after implementation. It covers explicit selection/rights,
  ID/unit/revision mismatch, period containment and microsecond future leakage,
  immutable originals, precise hashing and preserved settlement references.
- Strict TypeScript and Vite production build passed. **45 unit cases passed**: the previous 35, eight
  builder cases and two HTTP boundary cases for closed nested edits and rights
  receipt identity/stage. A null rights body initially raised a raw TypeError;
  a RED→GREEN object guard now rejects it as ApiError before HTTP dispatch.
- **11 Playwright cases passed in 14.9s after the Korean control labels**, including all six previous browser
  cases and rights/shock/read response loss, explicit application and future
  input rejection. Bodies/keys, acknowledged-phase retention, auth/selection
  locks, navigation retention, no automatic calculation, exact revision pinning,
  no invented amounts, keyboard operation and 320/768/1440px at 100%/200% root
  text were checked. Mocks exercise software contracts, not farm data.
- **Actual TLS/SCRAM/PostgreSQL revised-input integration passed in 148.82s**
  (`tests/web_economic_smoke.py -k True`, one passed/one deselected). It checks the new
  EconomicNumber rights hash and the actual derived production payment value
  and revision, preserved original joint/settlement references, real worker
  completion/replay, browser DTO display and one calculation job on retry.
  After the Korean selection labels, a final combined field-drift and revised
  TLS check passed **2 tests in 147.93s**, with the registration-only case
  deselected. The new `55.0000000001`/new revision is present in the actual derived cost
  payment; the original joint retains `60`/`r2`. The exact browser-generated
  rights hash equals the server EconomicNumber hash. The pre-existing huge
  decimal registration-only TLS case was not rerun in this focused check; its
  prior evidence remains in the preceding record. Scenario/calculation
  acknowledgements initially took approximately 20.7s/28.6s, and the final
  pair took 20.6s/26.9s; no timeout was increased.
  Operating latency/capacity proof is still needed.

## Design close

12ui reused the unchanged approved economics LayerDoc SHA-256
`d7fe438a1ee53aaa0ec2894e54382c300bd8d0fb3f60305eed07d16f0df184e7` at
`/tmp/ossf-ui-economics-target/derived.layerdoc.json`. The original design image
SHA is `faf808bc9a97251530509bb10078e84c08b9912bbe8d5da654101a32ccd80113`;
conversion `c78c3be8-0563-43aa-9412-9837c541b34d`. The local close kit
`/tmp/ossf-ui-joint-amend-close` completed all stages and bought nothing.

Its DOM overlap is **29.1%**, below the 60% anchor threshold; this is not a pixel
fidelity claim. The kit README and annotated plan were inspected. Matching
text suggestions map the page title to a subtitle and the unknown-result notice
to price/profit/ranking; those would remove real semantics and were rejected.
The proposed 14px heading/navigation tokens would reduce readability. Existing
self-hosted Noto Sans KR and forest/ivory styling remain; the new preview uses
the approved card background `#f6f8eb`, border `#e0e5d4` and 12px radius. Select
and checkbox receive the existing font/focus styling.

The kit has no extracted raster files. The same excluded groups from the prior
close remain: invented price/profit/ranking plots, a decorative simulation dial,
a success lamp/growing plant without gate evidence, unavailable navigation/play/
settings/shield controls, and icons tied to missing cost/cash/chart/pen actions.
They are not recreated in CSS and no fresh conversion was bought. The product
claim gates and UI design truth take precedence over those unavailable assets.
User-facing edit labels use Korean demand/supply/macro, event and amount names;
user-owned row IDs remain visible to disambiguate selection. Six functional screenshots under `/tmp/ossf-joint-amendment-screens` were captured
at the top of the page; desktop 1440px and 320px/200% were visually inspected.

## Remaining scope

The browser response-order issue in hosted Web run `36554674000` was fixed in
`3c5cc88` by waiting for the actual queued status response before keyboard
refresh. That commit's [Web run 36555028673](https://github.com/KIMSUNGHOON/OpenSmartFarmSim/actions/runs/36555028673)
and [Compose run 36555028764](https://github.com/KIMSUNGHOON/OpenSmartFarmSim/actions/runs/36555028764)
passed. Its [backend run 36555028693](https://github.com/KIMSUNGHOON/OpenSmartFarmSim/actions/runs/36555028693)
was still in progress when inspected; it is not recorded as passed.
Monthly cash display now has separate [implementation evidence](web-economic-cash-implementation.md).

General farm/facility and ledger/event inputs, settlement authoring,
break-even screens, actual runtime CLI research/review/assessment, 3D/replay,
whole synthetic G1, independent source rights/measurements/future/comparison
validation and G4 operating/cost/capacity proof remain required. No whole task
was checked off. These self-authored synthetic records prove software behavior
only, not harvest, purchased energy, future profit, ranking or data approval.

## Review and scope of checks

A five-axis review inspected the changed client boundaries, pinned phase state,
rights/hash semantics, preserved versions and backend test assertions against
existing source/scenario contracts. No new dependency or backend arithmetic,
query, credential policy, gate decision or source adoption was introduced.
The bounded source reads and body limit remain unchanged. The local check is
focused; the entire backend suite and operating load were not rerun locally.
Local Markdown links and `git diff --check` passed. Backend hosted CI is reported
by its actual state, without substituting the narrow TLS case for a full pass.

## Hosted CI failure and synchronized browser regression

For head `faf96bea5d8d72b3351bd81fe325406d95d0864f`, [Compose CI
36554673971](https://github.com/KIMSUNGHOON/OpenSmartFarmSim/actions/runs/36554673971)
passed in 31s. [Web CI
36554674000](https://github.com/KIMSUNGHOON/OpenSmartFarmSim/actions/runs/36554674000)
passed install/type/unit/build/audit but failed two pre-existing economic browser
cases: the second keyboard refresh ran before the first queued-status read
finished, so the still-disabled button ignored it. The five new amendment
browser cases passed. A 200ms delayed, snapshotted job reply reproduced the same
missing-result failure locally. The test now waits for the actual queued JSON
response and re-enabled refresh control before transitioning its mock to
succeeded. The delayed response remains as a regression condition. **All 11
browser cases passed in 12.7s** after the fix. Product code, timeouts and retries
are unchanged. [Backend CI
36554674042](https://github.com/KIMSUNGHOON/OpenSmartFarmSim/actions/runs/36554674042)
was revalidated in_progress; no full-suite pass was claimed or run restarted.
