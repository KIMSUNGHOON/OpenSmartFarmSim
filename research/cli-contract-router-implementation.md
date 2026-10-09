# Shared CLI contract routing implementation

## Hosted receipt

Functional head f8cd4305efaeaf4dd47355a89462a532917ec928 was checked directly.
[Backend run 36526712504](https://github.com/KIMSUNGHOON/OpenSmartFarmSim/actions/runs/36526712504)
completed successfully: **1,908 ordinary cases**, two existing malformed G0
Pydantic serializer warnings, **3,313.24s (0:55:13)**; **four distinct-UID
service cases in 13.08s**. Content UID/DAC and database/password cleanup steps
also succeeded. The backend job ran from 2026-09-29T05:33:22Z to
2026-09-29T06:29:15Z. Compose run 36526712529 previously completed successfully
at the same exact head. The full backend log was inspected at
/tmp/ossf-cli-router-backend-ci.log. Later functional heads need their own CI;
actual CLI/independent authority, full browser/G1/G4 remain pending.

Status: software candidate, not product CLI/G1/G4 acceptance.

## Decision and scope

The worker claims research, collection_review and assessment from one queue,
but previously installed one contract. The completed owned-collection review
connection adds a second specialized review input. A protected route registry
now selects existing contracts by exact durable stage and input version.
It preserves their source/context/gate checks and immutable validator evidence.
There is no unknown-version fallback or request-defined authority registration.

This architecture judgment was made in the already-running Codex CLI session
01a0e064-b01b-7a22-8ef8-dd4afe0eb7dc. Selected turn_context metadata was checked
read-only at 2026-09-29T05:22:25.941Z and records model gpt-6-sol, effort xhigh.
This session's implementation and retained output are development evidence.
No recursive CLI, additional model call or sub-agent was used. Fake executable
tests below are software evidence, not an actual product model invocation.

## Implementation

- CliContractRouter subclasses the existing contract interface and copies a
  bounded read-only map covering the three AI stages.
- Stored input hash, bounded JSON and duplicate keys are checked before routing.
  Unknown stage/version pairs cannot enter a different parser or authority.
- Each registered contract owns parsing, authority, plan, publication bytes,
  validator version and hold bytes. The worker and JobStore install one router.
- runtime_digest includes the new module; existing release gates require current
  independently approved implementation evidence.
- No dependency, lock, SQL schema/grant, mathematical equation, worker isolation
  requirement, source approval or gate decision changed.

## Verification

RED: the focused test collected one missing-module error in 0.12s.
Initial bounded/configuration/three-stage checks: 14 passed in 0.36s.
The mixed actual SCRAM queue check passed in 21.35s. Its first run failed on a
test reading validator_version from the public decision listing; it was corrected
to read the actual retained validation_evidence_id report through auditor access.
Production behavior was unchanged by that test correction.

The mixed worker processes research hold, owned review proceed, legacy review
proceed and assessment hold in their actual durable queue order. Actual retained
reports preserve each validator version; hold creates no publication; review
artifacts equal the existing thermal proposal. An unregistered research input
closes hold without invocation. Collection G0 remains not_accepted. All inputs,
resolvers, executable outputs and keys in this check are synthetic.

Final focused verification used the repository's locked development environment
and local PostgreSQL DSN with these files: test_cli_contract_router.py,
test_cli_contracts.py, test_cli_worker.py, test_thermal_review_contract.py,
test_owned_collection_review.py, test_thermal_publisher.py and
test_thermal_run_store.py. Result: **78 passed in 109.24s (1:49)**, no warnings.
This includes all fifteen new cases and sixty-three existing cases; the earlier
fourteen unit cases and single mixed-queue case overlap this total.

Review checked exact pair selection, retained hash and duplicate-key boundaries,
closed registration, server authority identity and gate delegation, original
artifact/hold/report/version preservation, metadata-only unknown-input closure,
implementation digest coverage and bounded configuration. No production issue
remained from that review. The locked dependency check resolved 31 packages.
All 152 local Markdown targets in changed/new documents resolve; the staged whitespace gate is required before
commit. No additional local full backend, distinct-UID, browser, real provider
or actual model smoke was run. Full hosted verification is required for the
functional commit; a prior head's result is not this result.

## Remaining acceptance

Protected operating factories still need complete API/orchestration assembly
and evidence-backed research/assessment dependencies. The initial registry's
missing-source/context hold is retained. Exact product CLI execution, independent
planning/isolation/custody/release, adopted sources/snapshots, browser/3D and
G0–G4 acceptance remain necessary. No broad task checkbox was promoted.
