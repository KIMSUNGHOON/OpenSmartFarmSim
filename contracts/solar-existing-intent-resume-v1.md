# Existing Solar intent resume — v1

Status: locally accepted with [72 focused checks and final product comparison](../research/solar-existing-intent-resume-implementation-20261020.md),
2026-10-20 KST. Independent64/deployment/scientific gates remain unaccepted.
Extends [current guard ownership](solar-current-physical-farm-view-v1.md)
for the private noncreating path used by `SolarServerCustody.advance`.
The subsequent [worker checkpoint advancement](solar-worker-checkpoint-advance-v1.md)
extends the same guarded entry to `_advance_for_checkpoint`; it returns no progress claim.
The existing `entry_guard=False` option remains strictly read-only.

## Boundary

The original write entry can create empty locks/directories and can recreate
`intent.json` if it disappears after verification. Deferring its current check
without changing those operations is not accepted. A complete existing history
may instead use an explicitly selected, noncreating entry:

1. Preserve original principal/scope, component pins, request and registration
   scope checks. Select only an existing root lock, intent directory/lock,
   signed intent, proofs/artifact directories and HEAD. The probe grants no
   authority and does not cache a source, role, permission or gate result.
2. Open existing locks with no `O_CREAT`/`O_TRUNC`, enforce original mode/owner/
   ACL/empty-file checks and exclusive nonblocking lock semantics. Open existing
   directories without mkdir. After selection, a lost/replaced member cannot
   trigger creation, repair or a fresh intent preparation.
3. Verify original signed intent/canonical bytes and exact request/binding pins.
   Read its bounded HEAD as a private expected value. Entry returns no public
   result and runs no context preparation, continuation or artifact writer.
4. The immediate `_Session.advance` starts with the original full current guard,
   including physical and economic sources/rights, then requires the selected
   HEAD still to exist with the same bytes before any `_load`, start/restore,
   continuation, creation or publication. A changed, missing or authentic older
   HEAD is a hold. Authentic history validation remains in the original loader.
5. Preserve every later source/prepare, calculation, proof/HEAD publication and
   progress guard whenever progress is produced, lease/cancellation/input fence and cleanup.
   The subsequent private worker write acknowledgement produces no progress; its
   independent checkpoint confirmation retains the original guarded reads. The first frame
   reconstruction moves to the first advance guard; only the following warm
   verification at that closed entry boundary is removed.

The private `_advance_resume` option is exact bool and valid only with write
entry and the existing eager `entry_guard` setting. Its product callers are public
`advance` and the separately accepted private `_advance_for_checkpoint`. Default `_open`, new/incomplete intent entry and worker adoption retain
their eager checks and original setup behavior. Result/checkpoint/read callers
retain their existing modes. A missing member before selection uses the original
eager path; a member lost after selection fails closed.

## Acceptance

- Source/caller and real fault-injection evidence: original entry may recreate a
  deleted intent, while its next guard still prevents revoked numerical work.
- RED then focused checks for noncreating selected entry, strict options,
  default/new eager behavior, loss of each member, physical/economic/review/scope
  revocation, missing/changed/authentic older HEAD and actual shared/exclusive
  lock conflicts. Preserve history bytes, scopes, FD/connection closure and
  protected user services/resource caps.
- Reconcile cold reconstruction relocation, every remaining current check and
  the exact SQL difference in the original product quantum; original numeric
  results/counts/UTC. Private ABBA must improve both pairs and mean at least2%.
  Repeat the comparison using final product source before local adoption.
- Run affected current/late-rights, worker/query/HTTP and lock regressions.
  Software acceptance does not satisfy the original independent64/chunk1/
  poll/retry360/RSS gate, hold/cancel/calculating-WebGL/user-activation gates or
  real-farm G0–G4. Existing failures and evidence remain historical records.
