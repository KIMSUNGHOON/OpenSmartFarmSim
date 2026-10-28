# Supply-limited post-material Context and seed checkpoint, research v1

This additive owner adopts the actual [material point](crop-supply-morphology-point-v1.md).
It owns a new immutable Context and **seed-only** checkpoint. It does not advance
time, repeat material events, publish a farm Run or connect a new UI.

## Actual adoption and ownership

`crop_supply_morphology_context.prepare_context(origin, raw_checkpoint,
expected_sha256=..., time_tolerance_seconds_exact=..., inputs=...)` requires the
genuine accepted supply-law Context and its actual pending-event CP. It executes
the accepted candidate/material operation once and binds the complete original
point bytes, source Context hash and current code closure. Caller inputs and
tolerance must remain unchanged through return. No older typed handle is forged.

The seed retains the actual after-program, ordered organs, C/age/area/length vector,
layout, original/new construction costs, birth baselines, exact lifetime transfers,
point totals and global ledgers. Zero internode length remains exactly zero. The
new leaf, if present, is the only initialized leaf. Original source/profile/rights
and current organ clocks remain authoritative; no coefficients or geometry are
adjusted to make a receipt pass.

Adoption consumes exactly the first pending source event: retain its ID, sequence
and threshold, then add the actual source phyllochron to the next threshold and
increment sequence once. Keep the computed air-integral age without snapping it to
the threshold. This schedule is a synthetic numerical policy, not a measured
physical emergence time. Stateless retries recreate the same owner; this module
does not enforce a persistent farm-level single-writer event log.

## Clocks, original grid and accounting origins

Preserve the original step, count and horizon. At the exact material time, record
the completed grid index, whether it lies on the grid, the next original grid time
and its exact remaining duration. No step is integrated during adoption.

Physical lifetime flows keep their original-root origin. Geometry flows carry the
accepted supply-law branch integrals; new geometry channels start at exact zero.
Seed extension/unmapped classifications remain material baselines, not continuous
transfers or another debit. Units and those two distinct origins are explicit.
The seed CP starts with zero branch transfers and zero branch residual/budget;
its global ledgers equal the actual post-material preview.

Append a dense-before and actual-after sample to the source output hash chain,
binding each sample, phase, event sequence, material-point hash and model version.
Advance output cursor by two and event sequence by one. Preserve the old prefix.

## Cold restore and public operations

`context_bytes`, `point_bytes`, `start` and `checkpoint_bytes` validate the genuine
owner and export immutable canonical bytes. `restore_context(origin, raw_bytes,
expected_sha256=..., point_bytes=...)` requires trusted original descriptor and
point hashes, the actual genuine source owner, current source/code/profile/rights,
closed schemas and direct arithmetic reconciliation of the saved receipts.

Cold Context restore/start/export executes **zero** coupled RHS evaluations,
material operations, funding calls and leaf initializations. Pure receipt
arithmetic, source reads and profile validation still run. Establishing the
original source owner is a separately measured preparation step, not part of this
zero-replay claim. Hashes supplied by an untrusted caller are not farm custody or
independent source approval.

`restore_checkpoint(context, raw_bytes, expected_sha256=...)` accepts exactly the
seed CP derived from that owner. It then evaluates the real newborn stage **once**
at the saved current state, compares the whole saved post-point stage, rechecks
inputs/profiles/source/code and returns an owned CP. It never reruns a past
interval, material operation, funding call or initialization. Unexpected
`RuntimeError` propagates; known validation failures raise `SupplyContextHold`.

## Bounds and next owner

Descriptor plus original point bytes are capped together at2MiB; the seed CP at
512KiB. Preserve original inventory/horizon limits and32768-scalar budget.
Canonical bytes, trusted hashes, genuine type/token, closed derived seed and
current/late fences reject replacement or extra claims without returning partial
state. No DB/network/worker/export/UI mutation is added. G0–G4 remain not_assessed.

The next module must use this actual seed and the zero-length newborn stage to
integrate the fractional remainder and original grid. Prove full/split/cold byte
identity, lifetime/global composition, next-threshold hold and confirmed failure
prefix before implementing successor events. This seed-only validator must not be
presented as an evolved-checkpoint validator or replaced by an older invariant.

Evidence: [focused report](../research/crop-supply-morphology-context-20261028.md).
