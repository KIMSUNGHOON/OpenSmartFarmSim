# Crop cycle replay: bounded market source read scope

Status: development candidate, 2026-10-06. The actual Codex CLI session uses
`gpt-6.1-sol / xhigh`; no recursive CLI is invoked. This is a narrow dependency
of [cycle runtime acceptance](api-crop-cycle-pages-v1.md), justified by the
[actual read profile](../research/artifacts/crop-cycle-api-read-profile-20261006.json).
The foundation remains fixed at `d19f7c0`.

## Change and boundary

Only `MarketScenarioService.validate_pinned` opens the optional trusted
repository read scope. `MarketCandidateStore` and `_MarketSources` forward it
to the actual `MarketSourceStore`; fixture repositories without the capability
retain their current path. Four existing modules and one focused test file
form this slice. Candidate/hold connections and write transactions retain
their existing paths. No dependency, database schema or calculation changes.

The source store owns a fresh verified SCRAM connection for that call only.
It selects `READ COMMITTED READ ONLY`, keeps the connection in an instance
ContextVar, and rejects nesting. Every existing typed getter still checks
the current tenant/scope and fetches the row plus immutable originating job;
rights, availability, pins and economic arithmetic are recomputed as before.
There is no row cache or result cache. Separate contexts do not share a connection.
Normal exit repeats the current tenant/source scope check and effective grant
audit before returning. Failure resets the ContextVar, rolls back and closes
the connection. A scoped getter cannot follow a changed principal to another
tenant. Caller supplied connections are not accepted.

[Psycopg connection contexts](https://www.psycopg.org/psycopg3/docs/basic/transactions.html)
close connections after commit or rollback; the installed dependency remains
the locked version. [PostgreSQL 16 Read Committed](https://www.postgresql.org/docs/16/transaction-iso.html)
uses a fresh snapshot for each statement, preserving observation of committed
corrections during validation. Repeatable Read is not selected.

## Acceptance

1. Scoped and unscoped validation returns identical typed request, derived
   scenario and full pin; Decimal ledger results and IDs agree. The number
   of source row/job validations agrees while source connection creation
   falls to one per validation.
2. Actual SCRAM tests cover scope/tenant withdrawal during the block,
   original job corruption after an earlier read, denied rights on replay,
   grant drift at entry and normal exit, nesting, exceptional cleanup and
   concurrent reads. Current grant failures remain holds.
3. Read-only enforcement rejects writes through the owned connection.
   Completed blocks leave closed connections and no retained ContextVar.
   Ordinary getters after a block still open their own audited connection.
4. Existing market source/scenario and crop runtime focused regressions pass.
   This slice alone does not accept the runtime API. The original registered
   25-hour/11,400-step case must still deliver all original 27 samples and
   5 events within the unchanged 30-second/2-MiB response budget, without
   RHS execution, and pass restart/cleanup checks.

No actual crop input or G0–G4 permission is adopted by this slice. Independent
farm data acquisition continues separately from software development.
