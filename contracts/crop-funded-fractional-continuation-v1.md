# Fractional material event and original-grid continuation, v1

This research engine adopts the [declared fractional material point](crop-funded-fractional-birth-point-v1.md)
into its own immutable context/checkpoint, checks branch and lifetime conservation, and advances
the remainder to the next original grid coordinate followed by original grid intervals.
It does not fabricate an old fixed-grid context/token, change original data/coefficients/caps,
validate biological emergence, bind actual stem attachments or approve G0–G4/R2 claims.

## Source and event adoption

`prepare_context(point_context, inputs)` uses a genuine prepared point context and recomputes
the point with the accepted material arithmetic. Capture the original source snapshot/root
sample/left checkpoint/birth bases and grid, original global transfers plus the checked dense
partial interval, current program/anchors, explicit point records and after-point seed.
Existing source leaves retain their original ages/C/A/anchors and birth times/integral bases;
new leaves use explicitly declared C, zero age and their own exact birth time/air-integral bases.
Both the source lifetime and the new branch baseline remain distinct. Previously scheduled
future points in a stored source graph are not implicitly replayed into this new branch.

Source-prefix flows are added once to dense partial flows. Future segment flows are accumulated
separately and added once to the captured branch prefix, then to the lifetime prefix.
New leaf-specific continuous flow fields start at zero. Original source point totals and new
branch point totals stay separate from continuous flows. They are combined only for lifetime
conservation; structural C is internal buffer transfer, while growth respiration is a C outflow.
Only explicit sensible/capacity input enters the reduced thermal model.

`start(context)` deterministically yields the after-point checkpoint. The first fractional
before/after snapshots extend the original output prefix and advance its cursor by two.
`adopt_births(context, checkpoint, inputs)` uses a distinct input schema,
`fractional-continuation-birth-input-v1`, with current context/CP SHA, exact current time,
original floor and explicit events. It verifies the current CP and returns a new context.
Start that context to obtain its after-point CP. It advances the cursor by one without advancing
time; continuous transfer prefixes remain unchanged. Already used source/new event and leaf IDs
are rejected. Repeating the same operation against the same immutable before-state is a
deterministic retry; repeating it against its new after-state cannot debit again.

## Exact clock, storage and numerical method

Own context and checkpoint schemas separate exact elapsed seconds, original grid index,
segment/branch integration counts, event sequence, phase, cursor and prefix. No integer index
stands in for the initial fraction. `advance_chunk(context, cp, step_budget)` accepts1..128
confirmed original-grid endpoints. First step duration is the exact remaining fraction to the
next original grid time; subsequent steps use original dt. Chunk boundaries do not subdivide
those numerical intervals. Completed horizons reject further advances.

Use the [already defined rational-time classical RK4](crop-funded-event-state-v1.md): shared
stage RHS for every state and transfer, exact rational time/coefficient combinations and one
binary64 rounding per combination. Preserve the original root grid/horizon/forcing. The point
does not normalize existing areas, reset old physiological ages, or reconstruct past ODE steps.
The model remains the explicit short research domain; full-cycle forcing/calibration remains open.

`context_bytes/restore_context` take immutable canonical bytes and an **externally trusted**
expected SHA. Restore checks closed version/code/profiles/current original source/schema/point
history and frozen values without ODE or point/leaf reinitialization. It does not recreate an
old material-point handle/token. `checkpoint_bytes/restore_checkpoint` bind the own context,
state shape/units/exact coordinate and rebuilt current sample/transfers/ledgers; CP restoration
evaluates only the current RHS once. This is not a history re-integration or farm custody claim.
Expected SHA must come from trusted storage/run evidence; a self-hash or Python field rewrite
does not confer provenance. Future production admission still needs current farm/source review.

## Conservation, failure and limits

Check branch and root lifetime whole carbohydrate/fruit number/canopy and air sensible heat/
vapor/capacity/reduced energy and every leaf age/C. Exact rational sums use represented values
and exact duration; publish reproducible float diagnostics only after the exact residual passes.
Keep the original64-ULP-per-step rule and explicit point balance budgets, plus source-prefix/
partial-interval budgets for lifetime checks and the original64-ULP aggregation allowance.
Rebuild these diagnostics from frozen context and current state on restore, not from prose.
These are roundoff budgets, not physical/discretization error certificates.

Context≤2MiB, CP≤1MiB,1..512 leaves, remaining sample scalar budget32768 and original≤600s/
4096 grid-step domain remain. Lower component serialization caps remain; the documented
[same512-leaf request hold](../research/crop-funded-fractional-birth-point-20261026.md) is not resolved here.
Late source/code/grant changes hold. A failed RK stage/domain/ledger returns no new checkpoint,
only the last confirmed prefix/samples and explicit failing stage/target; unconfirmed point/
endpoint values are never committed. No old grid apply/prepare/advance, DB/CLI/network or writes.

Acceptance: actual fractional remainder and multiple original endpoints, exact source prefix/
old C/A/ages/anchors and new birth bases, independently checked RK4/flows/global and branch
ledgers, canonical trusted restore with0past/0context RHS and1current CP RHS, same-time/mid/end
points/ID reuse/partial failures, byte-identical CPs across chunk groupings, closed schemas and
source/rights/caps/resource evidence. Maximum metadata hold remains explicit. Independent local
measurements, source-bound morphology, immutable combined replay/SDK/realistic3D, whole crop
cycle/resources/economics/autonomous comparison and scientific/production gates remain open.
