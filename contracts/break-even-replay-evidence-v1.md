# Break-even replay evidence v1

Status: internal preparation for asynchronous full-grid verification.

`BreakEvenStore.capture_break_even_replay(tenant_id, plan_id, check=...)` reads
an existing stored request, plan and result through the current tenant's actual
store. It runs the unchanged BreakEvenService over fresh candidate, ledger,
rights, settlement and market/context lookups, compares the canonical result
with the immutable stored bytes, and requires an observation for every trial.
An engine hold that returns before all trials cannot produce this evidence;
existing synchronous reads retain their hold/null behavior.

The closed repository adapter records only lookup method, bounded identifier
arguments and the canonical hash of the observed return value. Repeated reads
still call the underlying current provider; only the evidence entries are
deduplicated. A reference changing between repeated reads, missing/invalid data,
an unsupported reference shape or a size violation aborts capture. Any failed
lookup or recheck invalidates that adapter permanently; a retry needs a new
full replay. Canonicalization uses the existing market serializer, including
date/time semantics and economic decimal strings.

Every unique dependency is read again from its current provider with checkpoints.
Tenant access, store/principal/policy/DSN/schema binding, stored byte hashes and
the actual runtime implementation/environment digests are checked. The caller
may supply its existing full store-chain/scope/lease/cancellation guard. These
callbacks are not cached. Candidate coverage must equal the stored trial set;
the sole plan dependency must match the actual stored plan digest.

The frozen, closed `break-even-replay-evidence-v1` record contains tenant/plan
identifiers, request/plan/result/code/environment hashes, 2–256 trial count and
sorted unique lookup descriptors. It contains no numeric source records,
credentials, generated prose or approval fields. Identifier arguments have a
200-character bound; at most 16,384 descriptors and 1 MiB of canonical evidence
are allowed. These are memory/serialization limits, not throughput proof.
The new module is included in the runtime code digest inventory.

## Publication boundary

This function does not store or sign the record, submit/finish a verification
job, emit a receipt, or expose a new HTTP result reader. No reader accepts an
arbitrary supplied inventory as authority. Hash matching alone cannot prove
inventory completeness or grant current access. Sequential rechecks are not an
atomic snapshot of all external state or an indefinite rights authorization.

The subsequent asynchronous implementation must bind the exact server-produced
record to the immutable calculation parent and verification input, leased
attempt, fenced publication and bounded receipt. Result reading must validate
that completion and the current full store-chain/scope/dependency/code bindings.
The existing synchronous completion read continues to replay the full engine.
Admission, status, retry/cancel, rights withdrawal and actual 256-trial load
evidence under the unchanged 30-second web request limit remain required.

Assessment remains hold and the current G0–G4 requirements are unchanged.
Synthetic fixture checks establish software behavior only. Actual product CLI,
independent execution/release/G1 and production capacity are separate evidence.

See [implementation evidence](../research/break-even-replay-evidence-implementation.md)
and [existing completed-job read](api-job-break-even-result-v1.md).

The subsequent [internal verification service/worker](break-even-verification-v1.md)
now binds this server-produced record to the immutable parent/input and leased
publication. The [internal completed-evidence reader](break-even-verified-result-v1.md)
rechecks current dependencies through actual stores. HTTP/web/operator assembly
and actual 256-trial read/load evidence remain pending.
