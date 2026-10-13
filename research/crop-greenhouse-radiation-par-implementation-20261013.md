# Solar PAR calculation acceptance — 2026-10-13

**Accepted:** instantaneous prescribed solar PAR calculation and its unchanged
crop-consumer interface. [Contract](../contracts/crop-greenhouse-radiation-par-v1.md),
[primary review](crop-par-primary-source-review-20261013.md),
[machine evidence and actual example](artifacts/crop-greenhouse-radiation-par-implementation-20261013.json).
Actual farm Runs0; G0–G4 `not_assessed`. This module is not deployed to the UI.

## What can be inspected

- [Versioned calculator](../backend/app/crop_greenhouse_radiation_par.py) and
  [independent Decimal80 reference](crop-greenhouse-radiation-par-reference.py).
- [Ten original synthetic cases](../fixtures/crop-greenhouse-radiation-par-reference-cases-v1.json):
  150 partition/photon scalars plus10 original-form electron-transport comparisons.
- For the explicit synthetic600W/m² case, the actual calculator returns
  incident869.4µmol photons/m²/s and canopy absorbed PAR153.65189801683186W/m².
  Interior residual is7.105427357601002e−15W/m²; exterior PAR residual is0.
  These values are software checks, not measured crop production or total solar heat.

## Passed checks

Original exec30432:0: **88 new tests**; original56298:0: **275 total focused tests**
(88 new +187 existing growth/joint-RHS/ventilation tests), 0 skipped.
The second test process took0.71s; guarded wall1.167682149s.
Independent precision80 partition/photon values, limiting cases, source/profile/
code/input identity, repeatability, immutability, closed units and schema,
numeric/domain holds and the actual existing crop's electron transport passed.
The double-interception negative control differs as required.

The guard included **all five required live roots and dynamic descendants**.
Peak121,208,832bytes/PID; combined689,283,072bytes, nominal0.25s sampling.
Both frozen source/asset sets and2,148 original source entries stayed unchanged;
required roots remained live,5173 returned200, FD4→4, no owned process/PG/passfile
remained. The calculator and tests have no DB, API or user-service write path.
This does not repeat the earlier entire database/HTTPS/browser acceptance.

## Next acceptance and external dependencies

1. A new instantaneous joint adapter derives LAI from the **current leaf state**,
   replaces the prescribed incident PAR field, and sums canopy absorbed PAR with
   an explicitly named non-PAR heat component. Reject ambiguous total-solar input.
   Prove one call at the same trial, unchanged air/vapor terms, crop/heat effects,
   numeric/identity holds and existing joint balance budgets.
2. Reevaluate that boundary at every RK trial; compare independent trajectories,
   interval reduction, new context/checkpoint identity and original results.
3. Complete the distinct NIR optics/heat contract before total solar claims.
   New stored/API/UTC3D coupling needs its own acceptance; current user UI remains
   the already accepted ventilation version.

Regional weather/time semantics, solar spectra, lumped cover/floor optics and
independent local/cultivar/future-farm validation are still missing. Development
continues with explicit synthetic inputs while those records are acquired.
No full CI or field validation ran; overall product completion remains undated.
