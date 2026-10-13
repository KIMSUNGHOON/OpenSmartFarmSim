# Shared solar and ventilation integration acceptance — 2026-10-13

Accepted [new integration](../contracts/crop-greenhouse-solar-integration-v1.md),
[code](../backend/app/crop_greenhouse_solar_integration.py) and
[machine evidence](artifacts/crop-greenhouse-solar-integration-implementation-20261013.json).
Every shared RK trial evaluates current PAR, source virtual NIR, ventilation
and the original crop/climate RHS once. Native CLI `gpt-6.1-sol`/`xhigh` context
at2026-10-13T12:47:41.178Z, raw SHA
`2b1f0bbefe746fb83ac8393798a38e196573bff23d75624646494174b0fa8b74`,
and actual design/output hashes are recorded; no recursive CLI or new physical
coefficient/closure. Existing profiles/models/results remain unchanged.
Actual farm Runs0/G0–G4 `not_assessed`; new solar calculation is not deployed.

## Numerical acceptance

Original5936:0: **56 new tests**,26.19s pytest/26.763s guard.
Original72352:0: **617 focused tests,0 skipped**,56.14s pytest/56.736s guard;
includes prior crop/joint/PAR/NIR/ventilation and integration consumers.

- Independent app-free Decimal80 source/crop/outdoor/exchange/capacity equations
  and separate149-vector RK4 compare **1,064 scalars** (seven ×108 states,
  41 integrated transfers,3 derived values). Same-step relative5e-12/absolute
  5e-14 and canopy temperature absolute2e-10K pass.
- Day cool/dry, day warm/moist, dark, signed non-solar heat, changed leaf,
  zero ventilation and zero NIR. Three smooth32s dt8/4/2 trajectories versus
  independent Decimal dt0.25 pass **72 error-reduction ratios>8**. This does
  not establish full-season accuracy or stability.
- All **15 balances** pass fixed runtime roundoff and absolute limits.
  Non-solar/PAR/NIR canopy heat and virtual optical partitions are distinct;
  floor/cover/reflection/construction receive no additional thermal credit.
- Actual call capture:16steps→**65 calls each** to PAR/NIR/ventilation/core RHS.
  Initial complete composition validates the input and supplies k1; no extra
  validation RHS. Current LAI/air/energy and paired RK weights are shared.
- Freezing initial NIR gives a different trajectory. Dark exactly reproduces
  old ventilation; zero NIR exactly reproduces old PAR physical states/ledgers
  under new identities. Manual event-free split is exact for final states and
  within the fixed tolerance for cumulative transfers; it is not product resume
  proof. Closed units/origins/spectrum/heat/profile/budget/numeric holds,
  last confirmed prefix, immutability/replay/component pins pass.

The first independent fixture generation shared a nested NIR input across
cases; its last zero-NIR case changed earlier cases. Original29101:1 correctly
refused inconsistent spectra:8failed/33passed/15errors. This was a fixture
generator alias bug; the initial generator/raw fixture/failure remain private
evidence. Case inputs now copy independently. Original84924:0 regenerated the
correct fixture in22.793s; full exact generator replay and cross-case mutation
regression pass. No acceptance tolerance or model equation changed to pass.

Focused acceptance preserved **five required live roots/dynamic descendants**,
2,148 original entries, both frozen UI source/asset sets, HTTP5173, FD4→4 and
owned process/PG/passfile0. Peak136,159,232bytes/PID and897,609,728bytes combined,
215 nominal0.25s samples;512MiB/PID/combined1GiB unchanged. No edits occurred
during focused guards.

## WSL reboot recovery

Before implementation the boot ID had changed and all five old root identities
were gone. The preflight stopped before any test child; old roots/custody were
retained and explicitly replaced after recovery, never silently omitted.
Restored the original full growth/harvest from its preserved manifest to
legacy `run-v23`; restored the original retained joint DB/API/worker to
`serve-v25`, then retained ventilation namespace/API/worker to `serve-v6`.
Frozen code/models, original inputs/results and keys were preserved.

Local authentication retained the same token digests while renewing issue/
expiry times; versioned runtime/TLS configurations preserve the prior bytes.
Ventilation runtime changed only authentication and the reviewed original
runtime hash; API config changed only certificate/key paths. New local service
authentication expires2026-10-14T12:53:06.657217Z (21:53KST next day).
Private credentials/guides stay outside the repository. Reboot automatic
startup/G4 was not implemented or accepted.

Original95242:0 checked authenticated original growth/harvest summaries before
legacy cutover. Original96535:0 checked actual SCRAM/HTTPS original inputs3/
stored samples9 and frozen snapshot files, read calculations/writes0; retained
ventilation normal/hold **six HTTP bodies are byte-identical** to pre-restart
results. Both original user ports200, FD4→4/owned cleanup0, five new roots live.
Its combined peak989,528,064bytes stayed under1GiB.

## Visible result and next acceptance

Both localhost5173/5174 development feeds report this acceptance and explicitly
hold new solar3D deployment. Existing scene remains the accepted ventilation
model. Status publication is data-only; current browser DOM/WebGL was not rerun.
Original39613:0 verified both actual HTTP feeds200/`no-store`/exact source bytes,
reported2026-10-13 22:14:42KST, SHA-256
`b45601a722e8fe91d64a9956e617c878ff87415f48ecb7ce6d1a6aadfe6bb413`.
Both served HTML entries equal their current frozen files;2,173 frozen ventilation
source files/five roots/old assets/FD4→4/owned cleanup0 passed. Combined peak
837,160,960bytes; no new browser acceptance or completion estimate is implied.

Next reuse original atomic management equations in a **new solar management/
selected-output program**, preserving source other forcing and recomputing
post-event PAR/NIR/ventilation. Then new immutable context/checkpoint/UTC→input
evidence/farm/custody binding→store/API/automatic worker→same UTC3D with
normal/hold/cancel, current rights and original model/UI preservation. Old
management/checkpoint types are not silently reused for41 ledgers. These are
remaining dependencies of the existing PAR runtime task, not new operating
foundation scope.

Actual optical/facility/cultivar/local/future farm and market/economic data
remain external publication dependencies. Synthetic software development is
independent; production, future margin and ranking claims require corresponding
gates. Full CI/current browser/independent farm validation were not run. Latest
[remote CI](https://github.com/KIMSUNGHOON/OpenSmartFarmSim/actions/runs/37995386493)
still shows the older2026-10-09 `f06fb67` failure, not this revision's proof.
No push. Overall completion date/remaining hours unknown; automatic goal remains
usage-limited while delegated manual work progresses.
