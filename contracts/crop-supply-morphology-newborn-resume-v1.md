# Supply-limited newborn original-grid continuation, research v1

This additive solver starts from the actual [post-material Context](crop-supply-morphology-context-v1.md).
It uses that genuine Context directly and issues its own evolving Checkpoint type.
The original seed-only validator and all previously accepted sources remain unchanged.

## Actual seed and numerical path

`crop_supply_morphology_newborn_resume.start(context)` requires the genuine accepted
post-material owner. It binds the original owner seed-CP hash, actual point/source,
current code closure, program, ordered organs, original/new construction costs,
C/age/area/length vector, birth baselines, rights and numerical grid/horizon.
Start keeps the actual post-material sample, event sequence, consumed/next schedule,
point totals and output cursor/prefix. It does not append a duplicate seed sample.
Branch transfers and branch residuals/budgets are zero; global ledgers match the seed.

`advance_chunk(context, checkpoint, step_budget)` permits1..128 original endpoints.
The first interval spans the exact material time to the next original grid time;
subsequent intervals follow the original step and horizon. It uses the real
zero-length newborn stage, the accepted shared-stage RK4 weights and exact-fraction
combination followed by binary64 rounding. k1 reuses the validated current/previous
endpoint RHS; k2/k3/k4 and the actual endpoint add four RHS evaluations per attempted
interval. Continuous transfer channels use those same stage states and weights.
Zero internode length is not replaced by an epsilon. C, geometry and climate evolve
in the same state; old biology/trajectory/material operations are never replayed.

Every advance separately validates the current RHS once. A readonly export/start
runs no coupled RHS, and CP restoration runs exactly one actual current RHS. Original
source-owner construction is separate measured preparation. No leaf is initialized
or material funding executed by this solver.

## Local, lifetime and global accounting

Keep physical lifetime flows relative to the original root and geometry lifetime
flows relative to the accepted supply-law branch, with newly born geometry channels
starting at zero. Material seed construction remains in its birth/point baselines.
Add only the new continuous branch integrals; point totals and event sequence stay
unchanged. Compute branch carbon/stock/age/capacity/heat/vapor equations and explicit
roundoff budgets using the accepted rules.

Reconstruct physical global equations from the original root and actual birth
baselines. Geometry equations use the actual original supply-law geometry and its
physical inflow origin for existing organs, or the material seed for new organs.
Global residuals and budgets must equal accepted seed values plus the new branch.
Record nonnegative branch/lifetime potential deficits and canonical diagnostics;
these are numerical diagnostics, not cultivar calibration or error guarantees.
Current ages are reconstructed from immutable birth baselines, exact lifetime air
integral and the current vector; immutable Context metadata is not rewritten.

Each confirmed grid sample extends the source prefix using its hash, previous
prefix, original seed-CP hash, Context, step, phase and solver version. Full, split
and cold runs must produce identical CP bytes. No extra schedule consumption or
material point is hidden in a grid step.

## Next event, restore and failures

A certified monotone dense shoot polynomial identifies an unresolved next-threshold
bracket. Return only the last confirmed prefix plus the unadopted bracket; issue no
checkpoint for its right endpoint, consume no schedule item and add no organ.
Refined new-owner candidates and repeated material adoption are the next task.

`checkpoint_bytes` and `restore_checkpoint(..., expected_sha256=...)` require closed
actual state/time/unit/clock/flow/account/prefix fields, genuine ownership/current
code/source/profile/rights and canonical bounded bytes. Restoration checks the
saved current derived state with the actual newborn RHS once, without re-integrating
past intervals. Trusted original CP hashes remain required; self-hashes are not
independent source approval or farm custody evidence.

The original2MiB public-result and512KiB CP limits, bounded inventory/horizon and
32768-scalar budget remain. Known numerical/domain/balance failures preserve the
confirmed prefix when its authorities are still valid. Changed source/profile/code,
stage input or caller CP invalidates the response and clears its unpublishable
samples/prefix. Unexpected RuntimeError propagates. No DB/network/worker/export/UI
side effect is added. This is synthetic software research; G0–G4 remain not_assessed.

Evidence: [focused report](../research/crop-supply-morphology-newborn-resume-20261028.md).
