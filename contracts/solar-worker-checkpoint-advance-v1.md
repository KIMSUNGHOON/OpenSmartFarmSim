# Solar worker advancement before checkpoint confirmation — v1

Status: locally accepted with [82 focused checks and actual product comparison](../research/solar-worker-checkpoint-advance-implementation-20261020.md),
2026-10-20 KST. Independent64, deployment and scientific gates remain unaccepted. Extends [existing intent resume](solar-existing-intent-resume-v1.md)
and [current guard ownership](solar-current-physical-farm-view-v1.md).

`SolarExecutionWorker.run_once` discards the return from its advancement call.
Its next consumed result comes from the independently verified `_confirm`.
The private advancement acknowledgement must make no progress, rights or
checkpoint claim. It returns `None`; a server-confirmed checkpoint remains the
only input to the worker's progress/terminal decision and database publication.

Public `advance`, `inspect`, `page` and their returned bytes retain their original
progress construction and pre/post guards. Default/internal adoption and result
readers retain their existing modes. No request field, wire version, source/model
coefficient, actor program or simulation input changes.

A server-private `_advance_for_checkpoint` may use the same current guarded write
entry and original advancement body. An exact-bool private return option may
omit only the unused progress construction; its default keeps the public path.
It cannot skip initial selected-HEAD validation, authentic existing history,
prepare/current checks, numeric start/restore/chunk checks, reservations, private
page/commit/proof writes, any before/after proof/HEAD publication guard or cleanup.
Terminal retries remain nonnumerical and must validate existing authentic data.

The worker must next execute the original `_confirm` before it consumes a
checkpoint or publishes a DB result. Keep the current request/binding and rights,
fresh guarded progress before/after its snapshot, signed descendant checks,
unlocked early leases, final locked lease/input/history fence and atomic DB
publication. A changed/withdrawn source, tampered HEAD, cancellation or expired
lease between private acknowledgement and confirmation must not publish an
unverified checkpoint/result. No permission/result is carried across the calls.

Acceptance before adoption:

- RED then real SCRAM checks: private return is `None`, no progress construction
  in that write call, default/public raw response unchanged, strict private option
  and budget, current denial before numeric/file consumption, original late proof/
  HEAD rejection, terminal retry without numerics, original confirmed values/UTC.
- Test the actual worker call and the unchanged independent `_confirm`, including
  post-ack rights/input/HEAD changes, no fabricated progress, cancel/lease/hold and
  atomic result behavior. Timing/fault spies may target the active private call;
  preserve their original assertions and the original independent actor hashes.
- Compare original before/advance/confirm quanta ABBA, each pair faster and mean
  at least2%, and reconcile only the unused response's SQL/current-check delta.
  Retain every remaining full physical/economic right and original numeric/UTC.
- Compare private and final product source; run affected public/default, worker,
  current/late-rights, query/HTTP/lock checks. Resource limits/protected files and
  services/cleanup remain required. Software acceptance does not pass original64,
  hold/cancel/calculating-WebGL/WSL deployment or G0–G4.
