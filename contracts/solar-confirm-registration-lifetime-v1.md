# Solar confirmation registration lifetime — v1 candidate

Status: proposed from the [actual consumer observation](../research/solar-checkpoint-consumer-review-20261020.md).
No production implementation or cost acceptance yet. Extends the existing
[registration read scope](farm-registration-read-scope-v1.md) and
[connection lifetime](farm-registration-connection-lifetime-v1.md).

## Boundary

One `SolarExecutionCheckpointStore.confirm` may own one existing registration
read scope after its original early lease and verified input, before its first
`_current`. Close that scope before the surrounding jobs transaction commits.
The currently separate first-current and custody-session scopes perform two
reconstructions in the observed operation; the candidate aims to perform one.

The existing `_session` may explicitly ask the read-only server `_open` to join
that exact active registration owner. This must be a private, strict option,
disabled by default. Match the owner, tenant/scenario/revision/hash, active slot
and execution ownership. A missing, foreign, closed, poisoned or mismatched
owner rejects. Preserve ordinary/public entry and nested-scope behavior.

Do not extend the scope across worker quanta, requests, attempts or tenants.
Reuse only the reconstruction allowed by `RegistrationRead`; every original
current source lookup, owned research and thermal snapshot check, principal,
role, code and session check still executes. Existing per-read transactions and
row-lock release boundaries remain; do not create a long source transaction.

## Preserved consumers

Keep the original first guarded progress, fresh middle `_snapshot` load and
proof, signed descendant validation, both unlocked leases, late `_current`,
fresh final guarded progress equality and locked lease/input/history fence.
Keep full file/JSON/hash/time validation in every storage load. The metadata
packet remains the same closed25 fields and cannot resume numerical state or
approve rights. Public progress bytes and their size limit remain unchanged.

No JSON ownership cache or stored authority result is introduced. Preserve
hold/error precedence and rollback when scope entry, body or exit fails.

## Next acceptance step

1. Compare the original and private candidate on the same actual
   before/advance/confirm workload. Record registration owners/reconstructions,
   ordered source lookups, current boundaries, transaction/session behavior,
   original checkpoint bytes/counts/UTC and fresh load order. No product change
   follows from a reconstruction count alone.
2. Require both ABBA pairs faster and mean at least2% for the whole workload.
   A failure rejects this candidate; do not repeat unchanged timing to select a
   favorable result. Preserve the original independent actor/input/budget.
3. Before product adoption, cover original versus candidate late source,
   research/snapshot/registration, physical/economic right, principal/grant and
   session changes; wrong owner/context/Task/thread and copied context; lease,
   cancellation, same-HEAD tampering, error/exit rollback and cleanup. Reconcile
   any changed SQL/audit count with the existing scoped reconstruction path.
4. Compare private and final product source; run affected checkpoint, public
   custody, worker, query and HTTP checks. The existing independent normal64 →
   hold → HTTP cancel → calculating WebGL → WSL activation remains separate.

Design judgment: this native Codex CLI `gpt-6.1-sol` / `xhigh` session; invocation
context and source/output hashes are recorded in the linked observation.
