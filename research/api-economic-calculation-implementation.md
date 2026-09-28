# Economic calculation HTTP evidence

Status: implementation candidate; full CLI/farm/browser/G1/G4 remain held.
The active root Codex CLI turn_context at 2026-09-28T18:31:28.225Z records
gpt-6-sol / xhigh in thread 01a0e064-b01b-7a22-8ef8-dd4afe0eb7dc. No recursive
CLI, extra model call or subagent is used. Its reviewable implementation output
is [the service](../backend/app/api_economic_calculation.py),
[HTTP contract](../contracts/api-economic-calculation-v1.md) and
[real-store tests](../backend/tests/test_api_economic_calculation.py).
The [authenticated assembly test](../backend/tests/test_api_economic_calculation_runtime.py)
uses the full existing production login profile.
The existing versioned engine/codecs/stores produce every numeric value.

The optional actual-source ApiRuntime service admits bounded immutable worker
input with current scopes, exact authority binding and whole-ledger replay at
commit. No result is published during admission. Namespaced client keys use the
existing unique intent constraint and return the current actual JobStatus.
Completed-job lookup verifies canonical immutable input, publication/attempt/
manifest/receipt pins and the actual fully recalculated result before using the
existing safe EconomicResultRead projection. Final scope/pointer checks cover
replay and failed preparation. The original implementation/environment digests
are validated as historical metadata, not independent release evidence.
Unknown/null and engine calculation/Assessment holds are retained.

Initial test collection required the repository's usual backend path setup
(1 error in 0.22 s); after that correction, RED reached the deliberately missing
service module (1 error in 30.33 s). The first connected-path run reached
completed read but failed a test-only field assertion: the existing public field
is economic_result_id, not result_id (1 failed in 155.04 s). The assertion was
corrected; production response naming was retained.

The focused run passed **42** in **710.71 s (11:50)** with one assembly-fixture
failure: its narrow calculation login profile omitted ApiRuntime's required
break_even_calculation flag. The runtime case was moved to a separate fixture
module with the existing full production profile; the production gate was kept.
The corrected fresh Bearer/actual-store case passed **1 in 108.89 s (1:48)**,
including completed result lookup, missing authentication and rejection after
actual PostgreSQL grant drift. Thus **43 unique cases** were checked: 8 new
calculation HTTP boundaries, 1 new authenticated assembly case and 34 existing
OpenAPI/economic read/signed replay cases. This is two terminal test runs, not a
single aggregate 43-case run. No broad task checkbox, CLI record,
approved source/release or G1/G4 decision is promoted. Parent worker CI receipt
is appended to [its implementation record](economic-calculation-worker-implementation.md)
with this functional change. No broader local backend or distinct-UID suite is
rerun; hosted CI retains the required full suite and UID/content/cleanup gates.
The parent full backend run took 40:29, close to its 45-minute job limit.
The timeout is extended to 60 minutes for these additional real-store replay
and authenticated boundary cases; test commands and acceptance gates are intact.

Review confirmed current input/result pins, immutable retry behavior, exact
receipt/publication agreement, no result publication during admission, and
scope/source-identity checks after replay. All **120 local Markdown targets** in
changed/new documents resolve and whitespace checks passed. Hosted CI for this
follow-up has not yet run.

Remaining work includes protected worker deployment, economic/break-even and
research/collection/review/Assessment orchestration, browser/3D, actual exact CLI
execution and independent isolation/custody/release, and actual G0/G2/G3/G4
evidence. Synthetic source records, keys and software tests cannot establish
farm performance, future margin or crop ranking. New service code joins the
closed implementation digest and needs a fresh independent release.
