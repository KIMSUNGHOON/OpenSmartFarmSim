# Break-even asynchronous verification v1

Status: internal service/worker candidate. Internal current-dependency reading
now has a [separate contract](break-even-verified-result-v1.md). HTTP/web/operator
integration and actual maximum-grid load remain subsequent implementation.

## Admission

`BreakEvenVerificationService.submit(tenant, calculation_job_id)` accepts only
the canonical UUID of an actual completed break-even calculation. The existing
completion verifier checks canonical input, attempt/publication/receipt and
stored request/plan/result hashes without running market/ledger arithmetic.
Its closed metadata record explicitly requires replay and contains no result
numbers. Existing public result reading still performs full replay.

Admission requires the existing completed-result scopes plus simulation_execute;
break_even_write is unnecessary. The actual audited stores share their original
tenant/principal/schema/DSN/policy bindings. The immutable
`break-even-verification-input-v1` pins calculation UUID/attempt/input/receipt,
plan/request/result, trial count, scan/formula and current code/environment.
The server idempotency key binds parent UUID and current code/environment. Same
intent reuses the same Job; different immutable input under that key conflicts.
Preparation and the final admission guard compare current parent bytes and
bindings. Admission is an intent to verify, not a completed verification.

## Leased replay and publication

`BreakEvenVerificationWorker.run_once(job_id)` targets only that tenant's queued
or expired/recoverable simulation of this input model. It verifies canonical
leased input and the pinned current implementation, then revalidates the parent
and runs the full existing replay/reference-capture path. Every planned trial
must be observed. Current scopes, full provider pointers, implementation and
lease/cancellation are checked around engine trials and dependency rechecks.
No CLI, new coefficient, source adoption or arithmetic formula is introduced.

Full grid replay happens outside the final job-row lock. The final transaction
renews the lease using that same connection, revalidates bounded parent
completion and current binding, and fences succeeded state, publication/event
and attempt outcome together. It does not rerun a large grid while holding the
verification job lock. Private content can be orphaned after a failed commit;
it has no authorized completed receipt/publication.

The immutable replay evidence is stored through the existing tenant-private
content-addressed evidence directory, limited to 1 MiB. A canonical receipt of
at most 4 KiB binds its hash/size, parent and input hashes, result/code/environment,
trial count and versions. The receipt contains no raw reference list or tenant
ID. Generic job metadata/cancellation remain the existing protected operations.
Evidence is historical full-grid software replay; Assessment remains hold.

## Completed reader and acceptance boundary

There is no new HTTP admission endpoint in this service/worker slice.
An arbitrary manifest, receipt or evidence inventory supplied by a caller
cannot authorize a result. The [internal completed-evidence reader](break-even-verified-result-v1.md)
resolves the actual verification Job/input/publication/receipt and tenant-private
bytes, and rechecks parent/current rights/provider/code/dependency bindings.
Historical completion grants no indefinite source rights or G0–G4 approval.

Actual 256-trial SCRAM worker/admission/result-read load, unchanged 30-second web
deadline, retry/cancel/withdrawal under that load, protected operator deployment,
HTTP/web integration and independent product CLI/G1/G4 are still required.
Synthetic fixture tests establish software contracts only.
