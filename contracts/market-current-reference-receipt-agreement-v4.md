# Current raw dependency receipt agreement — v4 proposal

Status: **standalone receipt primitive locally accepted by48 actual SCRAM checks;
pure-getter equivalence and verifier integration remain proposed**.
[Primitive implementation/evidence](../research/market-current-reference-receipt-primitive-20261019.md).
[Measured v3 rejection and private v4 feasibility](../research/market-current-reference-row-integration-evaluation-20261019.md).
The accepted v2 verifier and standalone v3 primitive remain unchanged.

## Implemented primitive interface

`market_reference_receipts.verify_receipts(owner, tenant, source_keys,
candidate_keys, pin_keys, consume) -> None` borrows the exact owned bundle's
supported connection. It returns no public result. Its trusted internal callback
must return `None` and must not publish intermediate data. The private reader
returns32-byte receipts or explicit `None` for requested absent keys, with no
lookup SQL; it rejects unknown keys and cannot be reused after close/failure.
Fresh pre/post SQL receipts, field/type/nullability and physical relation OID
descriptors, current binding/code/lifetime checks and final enclosing audit are
required. This fingerprints dependencies; it does not validate raw domain data,
approve rights, prove getter equivalence or cache permissions. Unsupported
primitive inputs reject; future baseline eligibility fallback is not implemented.

## Development order

1. Accepted: closed exact-key SQL receipt primitive with48 real DB checks.
2. Specify and prove eligible pure-data/default-getter semantics and complete
   mutable dependencies; unsupported callbacks, schemas or repositories use v2.
3. Bind an expectation only after a full original trace passes between matching
   fresh receipt snapshots in the same registration lifetime. Initial full farm
   validation is still required. It is not a cross-request authorization ticket.
4. For eligible repeat data references, check fresh DB-computed receipts rather
   than repeating pure reconstruction. Retain actual current principal/scope,
   raw rights data, dynamic tenant/held/context and derived-candidate validation,
   callback, code/Decimal, cancellation/lease and role boundaries.
5. Prove late-change/denial/equivalence/cleanup and useful paired actual cost
   before adoption. Changed-source original64 and subsequent product gates remain.

## Receipt primitive acceptance

- Parameterized exact tenant/key predicates, explicit absent results, closed
  source/candidate/pin key sets, duplicate/unknown/count/byte rejection or safe
  baseline eligibility fallback. No tenant-wide scan or SQL interception.
  Retain the v3 development bounds: at most128 combined unique keys and1MiB
  conservative uncompressed dependency bytes, including joined job input.
  Reject oversize dependencies before SQL encoding/hashing/materialization;
  compressed storage size or the small returned digest is not a byte bound.
- Compute a versioned fingerprint from actual raw bytes and every metadata
  field used by validation, including joined source-job stage/input/hash and
  candidate presence. Do not trust only a stored payload hash. Raw binary and
  timestamp normalization and PostgreSQL producer/version must be explicit.
  Pin the exact field/schema set; unknown schema changes require baseline
  fallback before use. Expose only fixed-length receipts and requested absence.
- Use the actual supported shared SCRAM/read-only Read Committed connection
  and owned execution lifetime. No raw payload, permission result, decision,
  signature or gate approval is returned. The enclosing final audit remains.
- Test source/job/candidate insertion/deletion/replacement/metadata/raw changes,
  same-key hash drift, absent-to-present, exact tenant scope, actual size caps,
  session/profile/slot/Task/thread/code changes and cleanup.

## Equivalence and publication conditions

The private prototype deliberately replaces some actual source getter calls;
v3's getter-count/order condition does not prove v4. Define eligible default
pure functions by pinned code, model/schema/method identities, immutable input
bytes and Decimal/normalization settings. A method depending on wall-clock,
external state or an unrecorded dependency cannot use this shortcut.

Retain original validation for dynamic getters and derived candidate manifests
unless every consumed dependency is independently covered and proven. Consider
fallback precedence: an existing candidate can make an underlying source row
irrelevant. Unrelated rows must not cause spurious holds; changes in required
dependencies must deny all output. Post-validation receipt drift never becomes
an approval or a cached permission. Corrections require new versions.

The full initial trace must succeed while all required raw dependencies agree
before/after. After that anchor, each current boundary requires new receipts and
fresh authority checks. Close/poison expectations with their registration owner;
copied/nested/wrong execution or changed code/Decimal/context cannot reuse them.
Preserve existing fallback/ordinary paths and document any extra conservative
holds; do not silently narrow supported farms or lower G0–G4.

Acceptance evidence must include normal and adversarial actual DB comparisons,
original values/UTC/proofs, worker normal/hold/cancel/lease, query/HTTP denial,
no unauthorized reads/writes, immutable run/code/parameter versions and full
owned cleanup under existing5root/512MiB per PID/1GiB combined limits.
Only then assess original trace-OFF64, calculating WebGL, WSL capacity and user
activation. Real farm rights/independent G0–G4 evidence remain separate holds.
