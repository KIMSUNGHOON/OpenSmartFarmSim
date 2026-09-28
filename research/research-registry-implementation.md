# Pinned research registry implementation evidence

On 2026-09-28, the existing Codex CLI 0.157.1 session
`01a0e064-b01b-7a22-8ef8-dd4afe0eb7dc` implemented and reviewed
[research-registry-v1](../contracts/research-registry-v1.md). Its latest inspected
turn context at `2026-09-28T08:45:15.992Z` records `gpt-6-sol` and `xhigh`.
No extra agent or nested CLI/model process, external source research, actual
runtime model invocation, farm record or agricultural/economic coefficient was
used. This is current-session software evidence, not independent gate evidence.

The preceding admission boundary supplied an injectable scope lookup. The new
immutable registry supplies concrete shared facts to admission and initial
research validation: canonical byte/hash identity, exact registered tenant/
point/period/goal/provider scope and reserved catalog references. The CLI
resolver rechecks raw immutable job input and grants no evidence, claim or
proceed permission. It requires structured hold while source evidence and signed
planning context are missing. Lookup performs no collection/signing/model call.
No SQL schema, grants or dependency/lock changes were needed.

The first registry suite passed **34 cases in 2.24 s** against disposable local
PostgreSQL 16.15 and real SCRAM authority credentials. Adding a real child-process
fixture connected `POST /v1/locations` through the existing worker to persisted
hold and GET status. The combined registry/admission/CLI/worker/publisher/review
run had **108 passed, one failed** in 36.85 s: the new test incorrectly expected
the hold artifact's `evidence_missing` reason in job status. The established job
status is `ai_validated_hold`. The assertion was corrected; production behavior
was preserved. The final registry suite passed **35 cases in 2.95 s** using
`uv run --locked --group dev pytest tests/test_research_registry.py -q --tb=short`.

Cases cover private fixed constructor errors, canonical/raw bounds, reserved/
duplicate provider IDs and registrations, frozen state, rehashed input tampering,
changed catalog, tenant/scope/context separation and refusal of a proceed claim.
The process fixture uses a fake CLI, synthetic private credential and evidence
policy under one OS UID. It verifies software transport and immutable retry, not
actual Codex execution, provider G0 or independent runtime custody. Whitespace
and changed-document local links were checked separately.

The registry module enters the thermal publisher code digest, requiring new
independent release evidence. Existing manifests, releases, jobs and decisions
were not rewritten. Protected operator pin/file assembly, source/vintage/right
evidence, later signed planning, per-job containment, actual CLI invocation and
the full UI/G1 path remain missing; field, forecast/ranking and G4 are not opened.
