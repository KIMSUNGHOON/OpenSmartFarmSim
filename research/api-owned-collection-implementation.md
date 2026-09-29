# Owned ingestion/review API implementation

Status: software candidate; actual product CLI/G1/G4 acceptance is pending.

## Decision and scope

Connect completed-research collection and completed-collection review services
to authenticated HTTP and protected runtime assembly. Requests contain only the
actual parent UUID and bounded idempotency key; server evidence owns coordinates,
dates, sources and signed decision context. Existing JobStatus preserves
collection completion, queued review and gate holds.

This architecture judgment was made in running Codex CLI session
01a0e064-b01b-7a22-8ef8-dd4afe0eb7dc. Selected turn_context metadata checked
read-only at 2026-09-29T05:34:25.058Z records gpt-6-sol and xhigh. Session output
is retained development evidence. No recursive CLI, extra model call or sub-agent
was used. Fake executable/context/bearer fixtures below are software evidence.

## Implementation

- Closed FrozenContract models reuse existing canonical UUID/identifier grammars;
  bounded JSON and duplicate-key checks precede admission.
- POST /v1/ingestions and /v1/collection-reviews use exact existing services,
  server-bound tenant, current principal and existing scope tuples.
- JobStatus contains no original bytes, source/tenant/proof IDs or snapshot.
  Actual collection records preserve G0/G1 not_accepted and Assessment hold.
- Optional typed OwnedFixtureRegistry on ApiRuntimeDependencies assembles both
  services with actual authority stores/current_principal. The default is
  unconfigured; runtime exposes the two protected services.
- Review prepare errors are bounded CollectionReviewHold; JobIntentConflict is
  preserved as 409; other failures are fixed 503. Existing atomic preparation,
  commit guards and snapshot-before-job chronology are retained.
- Regenerated OpenAPI contains twenty-one operations with stable IDs, request/
  error shapes and matching AND scopes. The new module joins implementation
  digest coverage and requires current independent release evidence.
- No lock/dependency, SQL schema/grant, equation, gate or automatic source change.

## Verification

RED: focused collection produced one missing-module error in 0.63s.
The initial actual SCRAM/HTTP collection-to-review path passed in 14.93s.
It admits immutable collection intent, executes the actual deterministic
collector, retries completed status and admits candidate-bound review. Both
endpoints reuse the original job on identical retry and suppress private fields;
fixture G0/Assessment statuses remain unchanged.

Final focused verification used the locked development environment and local
PostgreSQL DSN with test_api_owned_collection.py, test_api_openapi.py,
test_api_runtime.py, test_owned_fixture_collection.py,
test_owned_collection_review.py, test_cli_contract_router.py and
test_api_job_status.py: **119 passed in 288.50s (4:48)**, no warnings.
This includes thirteen new HTTP cases, two new OpenAPI scope cases and one
optional-dependency rejection case; the earlier single positive test overlaps.

Checks covered actual collector completion and review admission, idempotency,
closed/malformed/oversized/duplicate-key bodies, media types, every required
scope, foreign tenant/missing parent/context, 409 intent conflict and snapshot
rollback, final scope/binding/private failures, absent services and mismatched
principal/assembly, actual Bearer runtime assembly and existing regressions.
The Bearer check is ASGI authentication/assembly evidence; live TLS deployment
and independently owned operator configuration remain pending.

Review checked request/store/principal identity, current permissions, original
parent/source/context verification, exact legacy JobStatus projection, bounded
fixed errors, commit atomicity, OpenAPI compatibility and implementation digest
coverage. No production issue remained from review. OpenAPI --check passed;
uv lock --check resolved 31 packages. All 164 local Markdown targets in changed/
new documents resolve. The staged whitespace gate is required before commit.
No local full suite, distinct-UID, browser, actual provider or real model smoke
was run. Full hosted checks are required at the functional head. No broad task/
gate checkbox was promoted.

## Remaining acceptance

Initial ResearchRegistry still requires source/context evidence. Exact-model
product research/review/assessment, independently protected factories and
planning/isolation/custody/release, adopted snapshots, complete farm/economic
orchestration, browser/3D and G0–G4 evidence remain needed. This API option has
owned-fixture software scope; a real provider adapter remains separate work.

## Hosted receipt for the collection HTTP head

The [backend run 36527887920](https://github.com/KIMSUNGHOON/OpenSmartFarmSim/actions/runs/36527887920) succeeded at exact head `b2af211bee0034c3d07f3a3fb33c6c436a3d2475`, with **1924 passed, 2 existing malformed-G0 serializer warnings in 6755.74s (1:52:35)**. Separate actual-UID service/planning smoke recorded **4 passed in 18.62s**; DAC checking and database/password/runtime cleanup passed. The job ran `2026-09-29T05:48:11Z`–`07:41:37Z`. [Compose run 36527887950](https://github.com/KIMSUNGHOON/OpenSmartFarmSim/actions/runs/36527887950) also succeeded at that head. This covers collection HTTP software only, not later shared-contract, assessment or web changes, actual Codex, full G1 or G4.
