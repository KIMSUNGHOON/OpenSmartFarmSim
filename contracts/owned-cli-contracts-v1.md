# Shared owned CLI contracts v1

Status: software assembly candidate. Actual isolated product CLI, independent
operator custody/review/release, full browser flow and G1/G4 remain pending.

`OwnedCliContractRouter(research, reviews, assessments, review_authority)` accepts
the exact implemented OwnedResearchService, OwnedCollectionReviewService and
CalculationAssessmentService classes. All three must use the same JobStore and
ThermalRunStore; research and collection must also use the same OwnedFixtureRegistry.
Each service's existing protected runtime binding is checked during construction.
The review authority is an explicit trusted operator callback, not a request,
model output or automatic approval supplied by this assembly.

| Stage | Input version | Existing validator |
| --- | --- | --- |
| research | research_input_v1 | DecisionContract with actual owned research authority |
| collection_review | owned-collection-review-input-v1 | OwnedCollectionReviewContract with actual service and explicit review authority |
| assessment | calculation-assessment-input-v1 | CalculationAssessmentContract; explicit hold |

The copied read-only registration contains only these three pairs. Other input
versions retain the router's `decision_contract_unregistered` hold; there is no
legacy or generic fallback. Callers requiring other versions can still configure
the existing general CliContractRouter explicitly.

Construction captures service identities, their existing binding pointers, and
delegate/resolver/parser identities. Every input-context, binding-field, plan and
final-validation operation checks this binding before and after delegation. A
changed or mixed binding raises `owned_cli_binding_hold`; final validation
returns a failed bounded report with that code. Valid operations retain the
selected delegate's validator version, artifact and missing evidence. Current
principal/scope checks and immutable input/source/context replay remain those
of the actual services; construction adds no permissions or gate evidence.

The protected authority factory installs this exact router object on both
`jobs.decision_validator` and `CliWorker.contract`, with the existing evidence
policy. It must provide its own principal, executable/supervisor, credential and
attestation configuration. This module opens no socket, invokes no model,
provisions no identity or signing key, and does not alter CliWorker's production
isolation restriction. The authenticated API runtime does not install a worker
or convert HTTP request identity into authority identity.

The implementation is included in the existing code digest. Previously issued
code-bound release evidence does not authorize changed code. Tests use actual
SCRAM services, existing synthetic captures/keys and a self-authored fake CLI.
They establish service routing and software holds, not real model execution,
independent release, source G0, field accuracy or crop recommendations.

See [implementation evidence](../research/owned-cli-contracts-implementation.md),
[general routing](cli-contract-router-v1.md), [owned research](owned-research-v1.md),
[collection review](owned-collection-review-v1.md) and
[held calculation assessment](calculation-assessment-v1.md).
