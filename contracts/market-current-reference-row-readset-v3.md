# Closed current reference row readset — v3 proposal

Status: **primitive implemented and locally accepted by34 actual SCRAM checks;
verifier integration and full v3 adoption remain proposed**.
[Primitive evidence](../research/market-current-reference-row-readset-primitive-20261019.md).
[Current-source evidence and fixture-only comparison](../research/crop-solar-current-read-candidate-evaluation-20261019.md).
The accepted [v1 verifier](market-current-reference-bundle-v1.md) and
[v2 audit lifetime](market-current-reference-audit-scope-v2.md) remain the product baseline.

## Implemented primitive interface

`market_reference_row_readset.verify_rows(owner, tenant, source_keys,
candidate_keys, consume) -> None` requires an existing owned `_Bundle` and its
physical shared SCRAM/Read Committed/read-only connection. Source keys are
unique `(kind, record_id, revision)` tuples, candidate keys unique
`(input_id, revision)` tuples. The combined limit is128 keys and1MiB of
conservative retained row accounting. Each SQL batch also suppresses raw fields
above its1MiB limit; the combined size is checked before `consume`.

The private reader returns copied rows or explicit `None` for requested absent
keys, and rejects unknown keys. `consume` must return `None`. It is a trusted
internal consumer; it must not publish intermediate rows. Lookup checks add no
SQL. Full existing physical identity/isolation checks surround capture/recheck.
The primitive clears its row/connection references and tokens; the enclosing
source scope owns the physical connection and final role audit. Its successful
exit is still required before accepting the outer verifier. No existing runtime
caller uses this primitive yet.

## Boundary

One pure `verify_current_reads` operation may use a closed, bounded row readset
for its explicitly recorded source and candidate-input keys. Retain the initial
full validation, all logical getters and duplicates in order, their canonical
digests, every current principal/scope/right and source validator, and all current
Solar/farm boundaries. Ordinary getters and ineligible bindings retain v2.

Unlike v2's individual physical SQL per lookup, this proposal would read the
exact current rows in a bounded batch before the logical loop, then re-read and
compare those same raw rows after it. This is an explicit change in physical
read timing and needs new concurrency evidence. It must not be presented as
already preserving every v2 interleaving.

No production SQL interception or tenant-wide scan. Build parameterized exact
key queries from the closed trace. Include original source-job stage/input/hash
and missing candidate-input results; validate identity, cardinality, duplicates,
size and unknown keys. Failed/missing/changed or unprovable dependencies hold or
use the original audited path. Do not reuse values across verifier calls or cache
permissions, role results or gate approval.

## Ownership and release

The readset is private to the exact connection/store/tenant/policy/principal,
code, slot and execution Task/thread. Nested, copied, retained, expired, poisoned
or switched owners cannot supply rows. Preserve existing read-only Read Committed
and physical SCRAM/session checks. Opening/closing the actual source scope still
performs its fresh role audits. All original current getters/rights validators
execute; no value, signature, publication or selector escapes before post-read
comparison and final actual audit. Exception cleanup clears all rows/tokens.

Start with the readset primitive and real DB tests before wiring it into the
pure verifier. The first reconstruction, normal getters, custody/worker/query,
equations, original actors64/chunk1/poll/retry360 and resource caps are unchanged.

## Acceptance

1. Real SCRAM verifies exact present and absent keys, source/job raw hashes,
   no unintended tenant/ID reads, unknown-key/duplicate/size rejection, no SQL
   mutation, and no returned value before the final checks.
2. Permanent rights/principal/role and raw source/job/candidate changes during
   the interval reject all output. Changes outside the required readset do not
   spuriously authorize or mix data. Current source/rights validators still run.
3. Same-key metadata mutation, replacement/deletion, late grant, callback/binding
   change, identity/isolation/slot/code changes, nesting/copied context/Task/thread,
   exceptions and next-operation fresh reads are tested, with full cleanup.
4. Actual advance preserves current12/registration24/reconstruction1, logical
   source1,824/order, original values/UTC/proofs and role boundaries. Report actual
   SQL/batch/row/byte counts separately. The fixture's85/11 stored rows are not
   the74/34 required keys and are not production query predicates.
5. Same-fixture paired useful improvement and focused denial/worker/query/HTTP
   regressions, review and5root/512MiB per PID/1GiB combined/owned cleanup precede
   local adoption. If semantics or benefit cannot be proved, retain v2.
6. Changed-source original trace-OFF native64 and full normal/DB cleanup proofs,
   hold/cancel/calculating WebGL, WSL capacity and user activation are separate.
   Actual farm rights/independent G0–G4 evidence and full completion remain open.
