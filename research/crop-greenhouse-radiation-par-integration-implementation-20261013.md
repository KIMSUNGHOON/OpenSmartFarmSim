# Shared PAR and ventilation integration acceptance — 2026-10-13

**Accepted numerical slice:** current leaf/LAI→solar PAR→crop/absorbed canopy
heat and current air/vapor→ventilation at every shared RK trial.
[Contract](../contracts/crop-greenhouse-radiation-par-integration-v1.md),
[implementation](../backend/app/crop_greenhouse_radiation_par_integration.py),
[tests](../backend/tests/test_crop_greenhouse_radiation_par_integration.py),
[machine evidence](artifacts/crop-greenhouse-radiation-par-integration-implementation-20261013.json).
Native Codex CLI `gpt-6.1-sol` / `xhigh` context and actual design/accepted output
hashes are recorded; no recursive CLI was run. Previously reviewed
[primary source/rights](crop-par-primary-source-review-20261013.md) and pinned
parameters are reused; no new coefficient or NIR assumption was introduced.

## What passed

Original81116:0: **51 new tests**,3.74s pytest/4.348s guard.
Original16500:0: **441 focused tests,0 skipped**,30.41s pytest/30.937s guard,
including the prior PAR/RHS/growth/joint and ventilation/integration consumers.
The old calculation modules/profiles remain unchanged.

- Independent app-free Decimal80143-vector RK4: **876 scalars** (six cases ×
 108 states/35 ledgers/3 derived values), same-step relative5e-12/absolute5e-14;
 canopy temperature absolute2e-10K. Cases: cool/dry day, warm/moist day, dark,
 signed non-PAR heat, changed leaf and zero ventilation.
- Three smooth32s cases at dt8/4/2 against Decimal dt0.25: **72 error ratios>8**
 under the criteria fixed before testing. This establishes these synthetic
 numerical examples only, not a whole-season accuracy or stability guarantee.
- All **13 balances** pass unchanged core/ventilation and explicit integrated
 canopy PAR/non-PAR, interior PAR and exterior PAR partition budgets. Floor,
 unresolved reflection and cover energy receive no canopy/air heat credit.
- Actual call capture:16 steps→65 ventilation/coupled trial evaluations and
 66 PAR/joint calls including one separately counted initial validation.
 Current leaf, air and signed canopy energy determine the same trial's fluxes;
 freezing initial PAR gives a different trajectory. Dark is exactly equivalent
 to the old ventilation calculation under a new identity.
- Event-free manual split has identical final state and matching integrated
 ledgers; immutable inputs/repeatable identity, closed units/origins/profiles,
 ambiguous old PAR/heat inputs, domain/budget/numeric holds and last confirmed
 sample on trial/endpoint-balance failure all pass. Product checkpoint/resume
 acceptance is still a separate task.

Original74107:0 generated the independent fixture under the protected guard
in21.717s; pinned generator/equations and exact same-step regeneration are tested.
Focused acceptance preserved **five required roots/dynamic descendants**,
2,148 original source entries and both frozen UI source/asset sets, HTTP5173,
FD4→4 and owned processes/PG/passfiles0. Peak136,171,520bytes/PID and
868,384,768bytes combined; nominal0.25s sampling and512MiB/PID/combined1GiB
limits unchanged. Source/config edits did not occur during focused guards.

## Observed service expiry and recovery

The first reference guard refused to start because three legacy roots and the
dependent ventilation root had stopped; **no test child was spawned**. The
legacy controller recorded clean exit0 after86,347s with `credential_expiry`,
originals/counts preserved. The ventilation monitor recorded
`protected_process_lost`, worker stopped/API stopped/old route restored and
namespace/results retained. The original joint API/worker stayed live.

Versioned recovery restored the original full stored growth/harvest and original
5173 assets/progress entry, renewed the legacy local credential lifetime, and
started the retained ventilation namespace/source/authentication on5174 again.
Required roots were explicitly replaced with the verified new identities;
missing roots were never silently excluded from a successful guard.
Original26440:0 reconciled original authenticated growth/harvest summaries at
the restored candidate before cutover. Original23666:0 verified **six retained
normal/hold HTTP responses byte-for-byte** against their pre-restart originals,
200/`no-store`, new writes0, five roots live, FD4→4 and cleanup0. Its combined
peak was901,763,072bytes. Private credentials/guides stay outside the repository.
Current recovery: legacy `run-v22`, ventilation `serve-v5`; original joint unchanged.
Ventilation authentication expiry is unchanged at2026-10-13 22:43KST.

## User-visible result and next acceptance

The reviewed development record is published to both
**http://localhost:5173/** and **http://localhost:5174/#ventilation-execution**.
The running scene still reads the accepted ventilation calculation. **PAR is
not deployed to3D** and is not portrayed as a production prediction. Status
publication is a data-only change; current DOM/WebGL was not rerun here.
Original28017:0 verified both HTTP feeds200/`no-store` and exact source bytes,
reported2026-10-13 19:07:22KST, SHA-256
`592bb6908c7c1769fd1b16f71ccb52f78cfbffdc300afc886edfc60af1619524`.
All five roots and2,173 frozen ventilation source files were preserved;
FD4→4/cleanup0, combined peak802,471,936bytes. Estimates remain unknown.

Next: **NIR cover/canopy/floor layer boundary**. Fix the source layer order,
multiple-reflection denominators and explicit optical inputs; test independent
partitions/limiting cases/holds and absence of double-counted heat; then connect
new immutable context/checkpoint→storage/API→same UTC3D with normal/hold/cancel,
current rights and original ventilation/UI preservation. No arbitrary animation
or invented total solar closure substitutes for those calculations.

Real region/cultivar/weather/optics and independent local/future farm and market
records remain external dependencies. Synthetic development continues separately;
actual farm Runs0/G0–G4 `not_assessed`, production/margin/ranking claims held.
The remaining implementation and data acceptance have no substantiated completion
date. Full CI/current PAR browser/local farm validation were not run. The latest
[remote CI](https://github.com/KIMSUNGHOON/OpenSmartFarmSim/actions/runs/37995386493)
is an older2026-10-09 `f06fb67` failure, not evidence for this revision. Existing
automatic goal state remains `usageLimited`; this is delegated manual progress.
