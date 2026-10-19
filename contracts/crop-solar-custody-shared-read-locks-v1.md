# Solar custody shared read locks — v1 candidate

Evidence: [current worker/API diagnosis](../research/crop-solar-audit-scope-v2-worker-api-diagnostic-20261019.md).
The retained worker path is `_confirm` → custody open Pending → bounded retry →
attempt1/queued/solar_execution_busy. The original trace-OFF run is incomplete.
This candidate is implemented and under verification;
[20 focused checks](../research/crop-solar-shared-read-locks-implementation-20261019.md)
have passed. It is not adopted or accepted as a complete component yet.

## Change boundary

Keep the writer's nonblocking exclusive root and intent locks. For Solar
`_open(write=False)` only, acquire nonblocking shared locks on those same existing
files. Keep descriptor security, lock ordering, directory identity, quotas,
signed intent/proof/HEAD ancestry and current source/principal checks.
The common file helper's default lock behavior remains exclusive.

A read session must not create lock files or intent data, prepare a numerical
context, advance a calculation or publish a HEAD/proof. Enforce its mode at the
mutating session methods. The prefix's existing manual read session is read only.
Do not remove locks or substitute an unlocked confirmation. Normal writers and
other callers retain their prior lock behavior.

No changes to equations, inputs, public response shapes, checkpoint comparison,
role/rights validation, chunk/poll/retry/lease/deadline values or resource caps.
This is a filesystem access boundary; it is not an authorization cache.

## Acceptance

1. Meaningful RED/GREEN with separate open file descriptions shows two actual
   read sessions can coexist, including confirmation while a reader is open.
   Their signed original values/UTC match. Include a real separate process lock
   probe; duplicating one descriptor does not prove independent locking.
2. A writer cannot acquire either protected file while a reader holds it, readers
   cannot enter during a writer, and the writer succeeds after all readers close.
   Opening a read session never upgrades its locks or creates a missing lock file.
3. Read-session prepare/advance/publication fail before numerical or filesystem
   changes. Late rights/source/directory/proof changes, exceptions, cancel/expiry
   and malformed modes fail closed with original data and owned FD cleanup.
4. Existing custody, checkpoint, progress query and prefix normal/hold/none/current/
   unconfirmed/real-lock/heartbeat/late-change paths retain their required results.
   Plain queries still perform no calculation or SQL mutation.
5. Preserve current5root/descendants, original2,148 entries, frozen source/assets,
   both UIs,512MiB per PID/1GiB combined and actual DB/process/file cleanup. Run
   fixture modules separately. Then test the original uninstrumented64 normal
   with original actors, two advancing prefixes and all termination/cleanup proofs.

Shared locks allow readers to coexist and remain incompatible with exclusive
locks; independent `open()` calls are distinct lock descriptions. This follows
the [Linux flock manual](https://man7.org/linux/man-pages/man2/flock.2.html) and
[Python3.12 fcntl documentation](https://docs.python.org/3.12/library/fcntl.html).
Validate the actual workspace filesystem rather than infer operational capacity
from those API semantics. Software concurrency checks do not accept G0–G4,
farm predictions, deployment, hold/cancel/calculating WebGL or the whole product.
