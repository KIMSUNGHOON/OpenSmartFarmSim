# Pure current reference verification — v1

The [actual current call paths](../research/runtime-role-audit-phases-evaluation-20261019.md)
identified312 reference audits within528 audits per Solar advance. The previous
four-SQL candidate was not adopted. This slice groups one internal verification
operation while retaining actual reads and authorization at its boundaries.

`MarketCandidateStore.verify_current_reads(tenant, trace)` verifies a closed,
bounded sequence of getter names, string arguments and expected canonical
SHA256 digests. It returns no data, connection, permission result or ticket.
Every getter and duplicate still executes in order, including actual held-report
and decision-context validators. No values or authorization results are cached.

The method owns the existing read-only Read Committed scope. A private lifetime
exists only during this pure loop. Eligible held-reference getters still check
the current tenant/scopes, bindings, identity, read-only/isolation and actual
source documents before/after each read. Full role audits run before and after
the loop; all existing scope entry/exit audits remain. Ordinary getters and
ordinary read scopes retain their original full per-getter audits. Ineligible
shared bindings retain the original getter path.

No intermediate value, signature or publication is returned outside the verifier.
Failure invalidates the lifetime and releases all slots/connections. Nested or
copied lifetimes, wrong execution owner, identity/pointer/connection changes,
late role/principal/source changes and malformed traces fail closed. A transient
extra privilege is never used for a SQL write: the operation remains read only.

The farm registration reader uses this verifier only for its repeated current
trace; initial full validation and all12 Solar current boundaries remain.
Pin changed store/verifier code in the binding dependencies. Do not change
equations, worker, inputs, chunk/poll/retry/deadlines or resource caps.

Acceptance: identical actual ordered reads/duplicates, values/UTC/proofs and
all existing source/principal checks; fewer reference role audits; no SQL
mutation or intermediate public result; late changes/nesting/copied context/
exception cleanup and next-operation revalidation. Compare the same actual
advance in paired order and retain only a useful measured improvement. Then
verify original native64 normal, independent hold/cancel, calculating WebGL,
WSL capacity and user activation separately. Preserve current5root/descendants,
original files and512MiB/PID/1GiB combined. G0–G4 and real farm rights/validation
remain separate gates.
