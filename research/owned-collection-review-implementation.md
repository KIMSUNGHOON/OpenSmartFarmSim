# Owned collection to review implementation evidence

Status: software connection candidate; G0/G1/G4 remain unaccepted.
The active root Codex CLI turn_context at 2026-09-29T03:51:28.970Z records
`gpt-6-sol` / `xhigh` in thread 01a0e064-b01b-7a22-8ef8-dd4afe0eb7dc.
This existing exact CLI session performs design and review. No recursive CLI,
additional model invocation or subagent was used. Reviewable output is the
[contract](../contracts/owned-collection-review-v1.md),
[collection read verifier](../backend/app/owned_fixture_collection.py),
[review service/contract](../backend/app/owned_collection_review.py),
[snapshot transaction helper](../backend/app/thermal_run_store.py),
[publisher connection](../backend/app/thermal_publisher.py) and
[actual-store tests](../backend/tests/test_owned_collection_review.py).

## Connection and decisions

The actual completed collection input, publication and canonical record are
reverified against its research final/report/invocation/capture and the fixed
owned registry. Source bytes/QC/metadata and the exact original context remain
bound. Retrieval must fall between job creation and publication; historical
code/environment hashes are well-formed metadata, not independent release proof.
Current read scope and authority/provider/content bindings are checked after
the reads, including failures.

A protected review service requires an actual signed tenant/snapshot context
matching the original decision ID/time/mode/kind. It creates no signature or
planning event. Original manifest/weather/thermal bytes form an existing thermal
snapshot candidate; collection job/attempt/input/record hashes extend the closed
review input. No raw data, price, tariff, coefficient or claim approval enters
the intent. Missing or mismatched context/source/access prevents admission.

Snapshot insertion and review intent admission share one actual JobStore
transaction. A new optional protected admission_prepare callback pins the
snapshot before inserting the job row, preserving the publisher's existing
snapshot-before-job chronology. Existing admission_action retains its later
position for callers whose source records reference the admitted job. The
snapshot helper reuses the existing byte/hash/conflict checks. Final source/
context/scope checks roll back both candidate snapshot and intent on failure.

The new review contract rechecks the actual collection and snapshot before
interpreting a proposal. The trusted authority resolver still decides allowed
claims and hold. Proceed emits the existing thermal proposal; hold preserves
the existing server report. Publisher supports the new input only with the
exact installed service bound to its actual JobStore and Run store. It repeats
verification and retains all existing capture, independent execution/release,
source/clock and physical checks. Legacy input behavior is retained. The new
module joins the selected implementation digest; fresh independent release
evidence remains required after this change.

## Focused evidence

RED was the missing connection module: **1 collection error in 0.23 s**.
The initial atomic candidate/intention case passed **1 in 9.97 s**, one case
deselected. After adding the preparation callback and explicit chronology check,
the connected admission and fake CLI cases passed **2 in 20.94 s**.
The final focused suite passed **94 in 127.84 s (2:07)**: 10 new connection
cases plus 84 existing collection, thermal review/store/publisher and durable
job/recovery cases. A final review added an explicit job-input hash check to the
reusable verifier and a direct forged-hash assertion; the four affected atomic,
CLI proceed/hold and forged-binding cases then passed **4 in 39.46 s**, six cases
deselected. All 94 unique cases passed across the focused runs. The command was:

```text
uv run --locked --group dev pytest -q
  tests/test_owned_collection_review.py tests/test_owned_fixture_collection.py
  tests/test_thermal_review_contract.py tests/test_thermal_run_store.py
  tests/test_thermal_publisher.py tests/test_jobs.py tests/test_job_recovery.py
```

Tests use actual local PostgreSQL 16.15, SCRAM roles, immutable private evidence,
job publication, snapshots and context rows. Context signatures use controller-
owned HMAC fixture keys, not independent planning custody. Research and review
execute fake Python CLI programs, not Codex. Connected proceed and server hold,
idempotency, complete source binding, original bytes, snapshot-before-job time,
missing/changed context, scope drift, insert/final-check rollback, collection
artifact corruption and a forged review hash were checked. Publisher rejects
missing connection configuration and still holds on absent independently
observed CLI execution. No Run or G0 adoption is manufactured.

Review checked source/proof/context identity, original bytes, record bounds,
current scopes/authority bindings after reads, atomicity and chronology, private
error suppression and unchanged mathematical/gate behavior. No dependencies,
locks, DB schema/grants or equations changed. No broader local backend,
distinct-UID, browser or actual provider/model smoke was run. The previous
functional head's successful hosted receipt is recorded in
[collection evidence](owned-fixture-collection-implementation.md).

The preceding full hosted suite took 1:53:16 with four UID cases and cleanup;
the 120-minute job limit had under six minutes of headroom. This increment adds
ten actual source/contract cases and repeated proof checks. The limit extends
to 150 minutes for that measured workload. Full ordinary/UID commands, content
access checks and cleanup are retained. All **152 local Markdown targets** in changed/new documents resolve and the
locked dependency check passed. A separate staged whitespace gate is required
before commit. Hosted CI for this functional head remains subsequent evidence.

## Remaining acceptance

Initial ResearchRegistry remains held. Running operator factories still need
stage-aware routing for the shared CLI queue and complete API/orchestration
assembly. Actual exact CLI execution, independent planning/isolation/custody/
release, adopted snapshots, full browser flow and G0–G4 remain required. No
broad task/gate checkbox was promoted. Fake executions and candidate snapshots
do not establish agricultural validity, energy purchases, future margins or
crop rankings.
