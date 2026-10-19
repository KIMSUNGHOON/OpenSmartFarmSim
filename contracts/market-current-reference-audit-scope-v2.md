# Pure current reference audit scope — v2 candidate

This is the next implementation boundary after the
[v1 component and native failure](../research/market-current-reference-bundle-implementation-20261019.md)
and [actual remaining cost](../research/crop-solar-reference-bundle-remaining-cost-20261019.md).
It is not implemented or accepted yet. The v1 implementation remains the baseline.

## Small change

Keep `verify_current_reads(tenant, trace)` a closed, bounded operation returning
only `None`. For compatible stores, use the existing source store's audited,
read-only Read Committed scope to own the verification operation. Its actual
entry/exit role audits must cover all actual reads and the full cleanup path.
Combine only the additional candidate/reference entry/exit audits inside that
same operation. Do not add an authorization cache or a general audit-disable flag.

Before selecting this path, verify the actual shared connection, identical
runtime policy/role/schema/DSN, source/candidate/held stores and principal provider,
empty original slots, and supported exact bindings. Preserve current identity,
scope, pointer, read-only/isolation and source checks before/after each held read.
Retain the full ordered trace and duplicates, actual getters and canonical digests.
The first reconstruction, each of the12 Solar current boundaries, normal getters
and ordinary read scopes retain their existing validation contracts.

No connection, permission result, intermediate value or lifetime escapes the
verifier. The source scope's final actual role audit must succeed before return.
Any failure poisons the operation and cleans every owned token/connection.
Ineligible bindings take the original audited path. Nested or copied contexts,
wrong Task/thread, changed slot/provider/policy/connection and late principal,
grant or source changes must fail closed. Do not change source-store role policy,
worker/query, equations, schema, original actors, input, chunk/poll/retry/deadlines
or resource caps.

## Acceptance

1. Meaningful DB tests cover an actual final grant drift (including during source
   scope exit), current principal/source/connection changes, copied/nested
   lifetimes, cleanup exceptions and full revalidation by the next operation.
2. Ordinary and incompatible read paths preserve their existing audits and
   results. No source read or duplicate is skipped; no SQL mutation occurs.
3. One actual advance retains current12/registration24/reconstruction1,
   source1,824/order and original values/UTC/checkpoint/proofs. Candidate/reference
   audit calls decrease only in the compatible pure operation.
4. A paired actual advance shows useful improvement under the unchanged
  5root/512MiB per PID/1GiB combined guard; otherwise retain the v1 baseline.
   Include real exits, source/originals/UI/FD and owned DB/process/file cleanup.
5. Original uninstrumented native64 normal and its complete proofs are a separate
   gate after adoption. Then independent hold/cancel, calculating WebGL, WSL
   capacity and user activation. No real farm prediction or G0–G4 approval follows
   from these software checks.

Use the observed audit boundaries to review the implementation, not a predicted
speedup. Native completion and completion dates remain unproven until measured.
