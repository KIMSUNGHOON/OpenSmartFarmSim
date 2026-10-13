# Current-state PAR joint acceptance — 2026-10-13

**Accepted:** current leaf→LAI→incident crop PAR and absorbed canopy PAR heat,
evaluated once at one shared trial. [Contract](../contracts/crop-greenhouse-radiation-par-joint-v1.md),
[code](../backend/app/crop_greenhouse_radiation_par_joint.py),
[machine evidence](artifacts/crop-greenhouse-radiation-par-joint-implementation-20261013.json).
This follows the [pure PAR calculation](crop-greenhouse-radiation-par-implementation-20261013.md).
No time integration or user deployment is accepted here. Actual farm Runs0;
G0–G4 remain `not_assessed`.

## Verification

Original9145:0:20 new adapter tests. Original60798:0: **295 focused tests**
(20 adapter +88 PAR +187 existing growth/joint/ventilation consumers), 0 skipped.
Pytest0.95s; guarded wall1.449749143s. Four independently composed Decimal80
whole-stage cases compare **468 scalars** across current derived quantities,
plant/100 cohort/climate rates and exchange, plus all seven joint balances.
Cases cover day, dark, signed non-PAR heat and changed leaf inventory.

Actual kernel calls confirm one PAR calculation and one joint RHS at the same
LAI. Light changes photosynthesis and canopy heat; air sensible/vapor derivatives
receive no PAR/floor/reflection credit. Changing current leaf updates canopy
absorption while retaining the incident-photon coordinate. Repeatability,
input immutability and new calculation identity passed. Old prescribed PAR/heat
keys, absent non-PAR heat, caller-supplied LAI, mixed origins, invalid units,
optics/profile/empty-leaf and photon-overflow inputs produce explicit holds.

The example's explicit150W/m² non-PAR component and current leaf state yield
133.77137357765395W/m² absorbed canopy PAR, combined283.77137357765395W/m².
This is a synthetic instantaneous example, not an approved total solar or
farm production calculation. The function cannot verify a caller's claim that
an arbitrarily labeled number actually excludes PAR; future server evidence
must bind those component meanings before admission.

The guard preserves all **five live roots and descendants**, both frozen source/
asset sets,2,148 original source entries and5173 HTTP200. Peak121,208,832bytes/PID;
combined691,826,688bytes, nominal0.25s sampling; FD4→4; owned process/PG/passfile0.
No source changed during either guard. No database or API write path was added.
Full CI, browser/whole database repetition and independent farm validation did
not run for this additive numerical slice.

Both5173/5174 development feeds publish the same reviewed17:58:49KST record,
SHA-256 `934f2f9fc80204bc143763155ebff679c7c04bc72bfb2dd66de822f2ab44bc53`.
Original70395:0 verified schema, byte equality, HTTP200/`no-store` and preserved
five roots/sources; combined641,232,896bytes. The record distinguishes deployed
ventilation from undeployed PAR and leaves the new work estimate unknown.
This was a data-only update; browser DOM was not rerun. Nineteen local document
links and `git diff --check` also passed.

## Next stage and publication holds

Next implement current-state PAR reevaluation at **each RK trial**, with a new
model identity. Acceptance requires independent full-state and transfer trajectories,
step reduction, explicit PAR/non-PAR integrated heat partitions, dark/changed-leaf/
hold behavior and preservation of existing results and resource limits. Then
complete the separate NIR multilayer boundary and new immutable input/context/
checkpoint→storage/API→same UTC3D acceptance. The current user service continues
to execute its accepted ventilation version; it does not load these new modules.

Real region/weather timing, cultivar/solar/optics and independent local/future
farm/economic data remain external dependencies. These do not block explicit
synthetic model development; they do block corresponding field predictions
and recommendations. Overall completion date remains unknown until those
records and validation scope are secured. The existing goal remains usage-limited;
the user's delegated manual continuation does not change its automatic state.
