# Solar/ventilation atomic management acceptance — 2026-10-13

Accepted [contract](../contracts/crop-greenhouse-solar-program-v1.md),
[program](../backend/app/crop_greenhouse_solar_program.py) and
[machine evidence](artifacts/crop-greenhouse-solar-program-implementation-20261013.json).
The new program reuses the unchanged shared solar RK and original atomic
removal equations. Source non-solar/other air forcing stays immutable; each
event composes PAR/NIR/ventilation before removal, validates atomic removal,
restores source forcing, and composes the new boundary before confirming output.
The journal distinguishes held pre-event forcing in management's own checks
from the actual new coupled forcing. No instantaneous optical/ventilation energy
is credited to removal.

Native parent CLI `gpt-6.1-sol`/`xhigh` turn context at
2026-10-13T14:01:12.240Z and actual design/acceptance output hashes are recorded
in the machine evidence. No recursive CLI, new physical coefficient, source
adoption or field-data approval occurred. Existing source equations, profiles,
models, result identities and frozen live service code remain unchanged.

## Verification

Original1249:0: **698 focused tests passed,0 skipped**, including **46 new program
tests**;133.14s pytest/133.764s guard. Original99087:0 generated the independent
reference in25.455s under the same resource/protection guard.

- App-free Decimal80 solar149-vector RK plus independently pinned cohort
  retention/capacity-energy removal: **11 programs,33 selected samples,5,214
  selected scalar comparisons** (108 states+41 transfers+6 event totals+3 derived
  values each), plus **12 event journals** with before/after states/removals.
  Cases include no events, warm/reverse/dark, event0/interior/end, multiple
  events, signed/zero reference energy, zero ventilation and zero NIR.
- Same-step rel5e-12/abs5e-14, existing temperature/history abs2e-10K and all
  **15 balance budgets** pass. Independent raw stock and radiation/ventilation
  balances also pass fixed absolute bounds: energy/carbohydrate1e-7,
  number1e-12,water1e-13,capacity1e-8. Removed sensible energy retains its sign.
- Three fixed16s-event programs, dt8/4/2 against independent dt0.25, pass
  **72 error-reduction ratios>8**. Independent exact fixture replay and input
  isolation pass; no tolerance was widened.
- Actual calls for16steps/3events: **87 each** composed solar/PAR/NIR/ventilation,
  **93 total core RHS**, including6 separate atomic-management validations.
  The sequence is compose-before→atomic validation/removal→compose-after.
  Captured source forcing stays original for every coupled evaluation.
  Leaf removal changes absorbed PAR/NIR immediately; incident crop photons
  and same-time air/ventilation state retain their intended values.
- No-events exactly matches the accepted shared short RK; dark physical
  states/first25 ledgers match the accepted ventilation program. Selecting
  different outputs changes identity without changing physics/event totals.
  The maximum128events/512outputs passes, including actual call counts.
- Invalid units/spectra/mixed origins/profiles/order/bounds hold before initial
  confirmation. Real temperature and injected interval/global-step/pre-event/
  removal/post-event/global-event failures retain only the confirmed prefix.
  Same-time pre-event endpoints, earlier journal entries and detached snapshots
  survive; uncommitted events and requested outputs are absent.

The first43-test run, original20440:1, had **41passed/2failed** due to test-schema
errors: LAI was read from an absent optical diagnostic and the dark comparison
used an incorrect photon unit spelling. Tests now use the existing derived LAI,
absorbed PAR and declared photon unit. Original3142:0 passed both corrections;
the final698-test run includes them. Private original logs/pins remain preserved.
No implementation equation or numerical criterion changed to resolve those errors.

All runs preserved five required live roots/dynamic descendants,2,148 original
entries, both frozen UI source/asset sets, HTTP5173, FD4→4 and owned processes/
PG/passfiles0. Final peak **136,159,232bytes/PID /969,732,096bytes combined**,
507 nominal0.25s samples, below512MiB/PID and combined1GiB. No source/config
edits occurred during running guards. Full CI and browser DOM/WebGL were not
rerun. This is elapsed-grid synthetic software acceptance, not product resume,
full-season crop accuracy or greenhouse thermal closure.

## Visible result, dependencies and next acceptance

The two existing localhost UI feeds report this accepted calculation stage.
Their displayed simulation remains the previously accepted ventilation model;
**new solar management is not deployed**. Status publication is data-only;
Original6549:0 verified both HTTP feeds200/`no-store`/byte-identical at2026-10-13 23:26:19KST, SHA `a3b7b7191aee4a42b2f07bd6b27fef331fb92ba92359fd0a33bbd32e08efd79f`. Both served HTML entries and2,173 frozen ventilation source files match their originals; five roots/FD4→4/owned cleanup0 pass. Current DOM/WebGL was not rerun.

Next: **new immutable solar context/checkpoint and UTC mapping**. Acceptance:
bind exact model/component/profile/input/numerical identities and41/6 ledgers;
preserve elapsed-grid event/output cursors and original UTC; split at arbitrary
allowed boundaries and restore in a fresh process with identical confirmed
states/journals/totals; count0 replayed past steps/events; reject mixed old25-ledger
contexts, changed inputs/profiles/policies/units, altered or reordered snapshots
and invalid UTC grids. Failed advance must retain the original checkpoint/prefix.
Preserve old contexts/results and five live roots/resources.

Then input evidence/farm/custody→new storage→API/automatic worker→same UTC3D and
normal/hold/cancel/reconnect/restart user acceptance. Existing independent farm
data acquisition remains parallel; no contact or restricted dataset was acquired
this turn. Actual farm Runs0/G0–G4 `not_assessed`. Local optics/facility/spectrum,
named cultivar/season, independent local/future farm and market evidence remain
external holds. Production, purchased energy, future margin and ranking remain
unpublished. Full product completion date and remaining focused hours stay unknown
until those dependencies and subsequent acceptance work are resolved.
