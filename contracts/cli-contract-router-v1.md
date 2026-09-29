# CLI contract routing v1

Status: software connection candidate; actual product CLI and G1/G4 acceptance remain pending.

The protected operator assembly installs the same CliContractRouter object on
JobStore.decision_validator and CliWorker.contract. Its copied, read-only route
map registers exact (stage, input_version) pairs to existing DecisionContract
instances. Configuration must cover research, collection_review and assessment;
invalid keys, versions, stages, contract objects or nested routers are rejected.
Registration contains at most sixteen pairs. A request cannot register a route.

Before selection the router verifies actual input bytes and their stored SHA-256,
then applies the existing bounded JSON parser, including duplicate-key rejection.
It chooses one registered contract without fallback. Unknown pairs raise
decision_contract_unregistered; the existing worker closes the durable attempt
as hold before creating a CLI invocation. The selected contract performs its
existing tenant, source, context, rights, QC and gate checks.

input_context, binding_fields, plan and final validation all select from the
same immutable registration. The selected contract's exact plan, artifact,
hold report, validator version and validator code are preserved. No wrapper
success or generated authority snapshot is substituted.

The current mixed-queue assembly registers the three common v1 inputs plus
thermal-g1-collection-review-input-v1 and owned-collection-review-input-v1.
The owned input retains its completed collection and snapshot verification;
the legacy thermal contract retains its signed snapshot/context verification.
The module is included in the existing implementation digest, so changed code
requires fresh independent release evidence.

Tests use a real SCRAM PostgreSQL queue and fake executable/context keys. They
check durable routing, publications, holds, retained validator reports and no
invocation for an unknown version. Actual exact-model CLI, independent operator
assembly/planning/isolation/custody/release, source adoption, full API/browser
flow and G0–G4 evidence remain necessary. Initial ResearchRegistry still holds.
