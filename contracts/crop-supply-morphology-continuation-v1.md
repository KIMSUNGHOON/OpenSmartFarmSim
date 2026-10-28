# Supply-limited shared-stage continuation, research v1

This additive implementation follows [the accepted law](crop-supply-limited-morphology-v1.md)
and [the bound stage](crop-supply-morphology-bound-stage-v1.md).
It is an internal synthetic calculation contract, not a production endpoint or farm forecast.

## Objects and operations

`backend/app/crop_supply_morphology_resume.py` owns genuine frozen `Context` and
`Checkpoint` types. `prepare_context(source_context, raw_checkpoint,
expected_sha256=..., inputs=...)` binds the actual accepted repeat source, its
selected checkpoint and explicit construction parameters. It validates the old
current RHS once and computes the new bound stage once. No past interval, material
point, birth or leaf initialization is replayed. Existing state, clocks, identities,
geometry, D0, point receipts and historical scope remain immutable.

`context_bytes` and `proof_bytes` export canonical descriptors and the exact parent
checkpoint, parameter input and initial bound result. `restore_context` requires
those bounded original bytes and a trusted descriptor SHA. It checks the actual
source, current code/profile/access and algebraic bindings without a coupled RHS.
`start` issues the actual new branch checkpoint with zero new transfers and no time
advance. These hashes require trusted server custody; a self hash is not independent
farm evidence. This module does not supply that custody or a persistent store.

`checkpoint_bytes` checks shape, accounts and current fences without a coupled RHS.
`restore_checkpoint` additionally validates the saved sample using one **new current**
RHS, without old biology. `advance_chunk(context, checkpoint, step_budget)` accepts
an integer 1–128 and checks one new current RHS before advancing. Each interval
then computes k2/k3/k4 and the endpoint with four new RHS calls; k1 is reused.
Unexpected `RuntimeError` propagates. Known input/domain/account failures hold.

## Integration and books

The original grid/horizon and exact first fractional remainder are preserved.
The actual full extended state and all physical/construction channels use the same
RK4 stages, rational step and weights. A chunk boundary does not reset cumulative
transfers. Whole, split and cold-restored execution must produce identical samples,
traces, confirmed checkpoint bytes and first pending bracket.

`crop_supply_morphology_books.py` carries original C, fruit-number, sensible energy,
vapor, capacity and reduced-energy accounts plus individual C and thermal ages.
New geometry accounts check `delta X = integral(realized)`,
`integral(extension + unmapped) = integral(actual structural allocation)` and
`integral(extension) = (k/F)*integral(realized)` for every represented organ.
They exclude appended lengths/ages from physical carbon sums and map internodes to
the actual stock IDs. Root has no invented length/clock; initially unbound leaf
parents remain unbound. No new material point or growth-respiration charge occurs.

Physical global residuals equal the accepted source residual plus the new local
residual exactly, with the original plus local rounding budgets. New internode-age
accounts also retain their initial represented-minus-clock residual and budget.
Budgets cover explicitly tested floating arithmetic, not crop-model error.
Integrated potential, realized and nonnegative deficit are separate from canonical
curve-minus-integral diagnostics. A historical curve gap is not overwritten or
hidden in an ULP allowance. No clamp, epsilon area or fabricated removal is added.

## First pending event and numerical diagnostics

Every proposed production interval checks the exact RK4 dense shoot-age polynomial:
its derivative minimum on [0,1] must be nonnegative and its right threshold
classification must match the accumulated air integral. Unresolved monotonicity or
rounding holds. This certifies that polynomial, not physical emergence time.

At the first due threshold the result is `hold`, with no new checkpoint object,
no candidate/material point, and no schedule consumption. It includes only the
last valid confirmed prefix and an explicitly **unrefined**, unadopted new-law
endpoint bracket. The crossing endpoint is not a confirmed sample. Repeating from
the confirmed checkpoint produces the same bracket. Old-trajectory candidates are
not accepted as a substitute. Candidate refinement, compatible seed funding and
repeated event adoption are separate tasks.

`compare_interval_refinements(context, raw_checkpoint, expected_sha256=...)` performs
read-only 1/2/4 subdivisions to the same next original endpoint: one new current and
28 new stage/endpoint RHS calls. It returns actual state/flow/account differences,
not adopted checkpoints or a certified ODE/agronomic error bound. Any crossing
right candidates remain explicitly unadopted.

## Limits, failures and visibility

Complete descriptor/proof and public-result bounds are 2 MiB, checkpoints 512 KiB,
parameter inputs 128 KiB; the original 600-second and 32,768-scalar bounds also apply.
A normal numerical/domain failure preserves only the last confirmed prefix. A
current or late source/profile/code/access loss withholds all new samples and
prefixes. Caller inputs, sources and old stored results remain unchanged.

The accepted evidence is [the focused report](../research/crop-supply-morphology-continuation-20261028.md).
There is no new API, worker, database result, export or 3D UI in this slice.
All outputs are `software_research_only`, G0–G4 `not_assessed`; no actual cultivar,
local measurement, harvest, energy purchase, margin or ranking is claimed.
