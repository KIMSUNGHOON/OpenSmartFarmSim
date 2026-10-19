# Current Solar physical farm view — v1

Status: locally accepted with [64 focused checks and actual product comparison](../research/solar-current-guard-ownership-20261020.md), 2026-10-20 KST.
Independent64, deployment and scientific gates remain unaccepted.
Precedents: [binding v1](crop-greenhouse-solar-farm-binding-v1.md),
[registration v1](farm-authoring-storage-v1.md),
[observed dependency/cost](../research/solar-current-validation-boundary-review-20261019.md).

## Decision and existing interface

Keep `SolarFarmBinding._registration` over current `FarmAuthoringService.read_registration`.
It remains a projection of a fully revalidated v1 registration. Do not add an
independent physical-only reader or a new request/binding version in this slice.
The full farm hash includes economic intent/constraints and crop sales metadata;
the source binding commits to current research, snapshot, context, market hold,
candidate and rights. An opaque hash or an earlier receipt does not authorize a
current read. Current economic rights revocation continues to block v1 physical
calculation/publication/display. Economic assessment also remains gated separately.

| Fact consumed by Solar binding | Authority and current check |
| --- | --- |
| Tenant; scenario/revision; registration job/hash | Authenticated scopes, exact farm assembly, current hash-verified owned job and registration |
| Region/research goal; snapshot/context/market/candidate commitment | Full registration/research authority and current references; never an assumed coordinate or old approval |
| Crop/batch/species/variety and profile status | Current declared cultivation; `unvalidated_for_registered_crop` remains; labels do not validate a cultivar |
| Zone/floor area; full farm hash | Validated owned assumptions/rights; canonical whole-farm bytes, including declared economic metadata |
| Occupancy/evaluation period and decision time | Current farm/calendar checks; original microsecond UTC; KST day end; both source/declaration availability cutoffs |
| Source/program/context/time/initial state/provenance/model pins | Complete current signed input verification, files/profile/software pins and source review; original binding/input hashes |
| Calculation/display rights and resolver policy | Current exact-True rights, declaration consistency, pre/post scope and pointer checks; no permission cache |

No public data shape, current v1 hold, scientific coefficient, G0–G4 gate or
numeric calculation is changed by this contract. The separately versioned
physical-only capability considered in the review is deferred: it cannot replace
the original v1 actor/input or turn the original failed64 into a passing subset.

## Implemented ownership of a current check

The full v1 verifier may run fewer times only where the same closed operation
retains its mandatory current check before numeric consumption or metadata read.
No successful verification is carried into another operation.

1. `_open.prepare` returns a private numerical proposal. Keep its leading current
   guard, all source/evidence checks, exact original context construction and
   record comparison. The immediate `_Session.advance` caller retains its full
   guard after `prepare()` and before start/restore/advance. Trial removing only
   the redundant inner post-prepare guard; a wrapper that revokes rights after
   prepare returns must still fail before numerical continuation.
2. `_open` keeps eager validation by default. A private, exact-bool read-only
   entry option may defer the initial session guard for explicitly audited
   consumers that first run `session.progress()` before loading/returning data.
   Write entry cannot defer. This is custody read-only mode, not a claim that the enclosing DB transaction is read-only. `inspect`, `page`, and checkpoint `_session` are the
   only trial callers. Checkpoint may compare the private signed binding bytes
   first; its first progress read remains fully guarded before history/write.
   Other `_open` callers retain the original default, including direct internal
   binding readers and result/query sessions.
3. Retain read-lock snapshot/release/reacquisition checks; every publisher guard
   before proof/HEAD and after HEAD; calculation pre/post guards; progress
   pre/post guards; current registration/economic checks; current lease/input/
   cancellation fences and final atomic publication checks.

## Acceptance before adoption

- Compare the exact default-authority product quantum ABBA with unchanged
  program/actor, budget, counts, values and UTC. Both pairs must improve and
  mean local wall reduction must reach2%; this is not the independent360 gate.
- Verify default eager entry, strict read-only option/invalid modes, unchanged
  direct binding consumers, full guard before first load/return, prepare return
  revocation before continuation and all unchanged publication fences.
- Real SCRAM/current/late source/review/scope/grant changes, read/write lock
  races, lease/cancel/rollback, normal/hold original rows/UTC, zero numerical or
  SQL writes on read, independent fresh read and complete owned cleanup.
- Actual final product comparison is separate from a private candidate. Preserve
  the original64/chunk1/poll/retry360/RSS, two advancing prefixes, actor exit0/0,
  values/UTC and cleanup gate. Do not change fixture/input/actor assertions or
  substitute a physical-only run. Old failures remain recorded.
- Independent normal then hold/HTTPcancel/calculating WebGL/WSL user activation
  still precede deployment. The existing UIs and real-farm/evidence holds stay.
