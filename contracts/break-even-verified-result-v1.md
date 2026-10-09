# Completed break-even verification result v1

Status: internal service candidate. Its
[HTTP/protected operator assembly](api-break-even-verification-v1.md) has focused
SCRAM/HTTPS software checks. Web and actual maximum-grid load acceptance remain
subsequent work.

## Authority and result

`BreakEvenVerifiedResultService.read_job_result(tenant, verification_job_uuid)`
requires the existing completed-result read scopes. Simulation execution and
source/candidate/plan writes are unnecessary. Tenant comes from the server's
current principal; actual audited Job/BreakEven/Candidate/Source/Hold/Context
stores retain one principal/policy/schema/DSN and their original provider chain.

Only that tenant's actual succeeded simulation with the closed
`break-even-verification-input-v1` model can supply results. Other models, queued
jobs and missing UUIDs return no result. Canonical immutable input must match the
current code/environment. Actual publication, attempt, input/artifact hashes,
receipt size and manifest are checked; a CLI decision cannot stand in for this
deterministic publication. The exact receipt fields and versions must match input.

The reader resolves the receipt's hash/size through the existing tenant-private
evidence directory, hashes the actual bytes and validates the closed canonical
replay-evidence model. Its tenant/parent/plan/request/result/code/environment/trial
count must match the actual completed input. The current parent calculation's
metadata is revalidated before and after dependency reading. The actual immutable
result row must match all hashes/statuses and the complete planned trial count;
the evidence must cover exactly that plan's candidate references.

No caller-provided receipt, inventory or manifest argument exists. Private bytes
without that actual immutable completed input/publication cannot authorize a
result. Authorized deterministic workers and immutable publications are the
server's custody boundary; the receipt is not an independent G1/G4 certificate.

The result is the existing conditional user-grid projection, Decimal-derived
strings/null, user/assumed origin, unavailable-market context and Assessment hold.
The reader performs no market shock, ledger or break-even arithmetic. Existing
synchronous readers retain their full-replay behavior.

## Fresh dependency reading

The closed 13-method replay inventory is rechecked against actual current store
values. Candidate/scenario/numeric/source lookups share one freshly authenticated,
audited market connection for this call, while retaining the stores' existing
canonical row, job-input, manifest and tenant validators. Source fallback retains
the existing resolution order. Every descriptor is read afresh; no row or access
decision is cached across calls, and matching descriptors are not replaced by
caller-supplied values. Existing signed hold/current-scope and context verifiers
continue their own authenticated lookups. Plan lookup also retains its store.

Current principal/scope/full provider bindings are checked around each reference.
The shared connection repeats the complete role audit before return; illegal
grants or revocation fail closed. Current implementation/environment are checked
before/after the full read. A changed/missing reference, changed parent, changed
code or unavailable evidence yields no numeric result. Sequential checks are not
an atomic view of all external state or indefinite rights authorization.

The existing 1 MiB private evidence/result, 4 KiB receipt, 64 KiB input and
16,384-descriptor limits remain. They bound serialized data, not a throughput
guarantee. The unchanged 30-second web limit and actual 256-trial SCRAM admission,
completion/read, cancel/retry/withdrawal load still need separate evidence.
Actual product CLI, independent release/G1 and G0/G2/G3a/G3b/G4 remain held.
