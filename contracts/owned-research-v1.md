# Owned research planning connection v1

Status: internal software candidate; actual CLI, independent planning/custody/
release, source adoption, full browser/G1/G4 acceptance remain pending.

OwnedResearchService is a protected operator option for the existing location
request/response and research_input_v1. It requires the actual audited authority
JobStore, matching ThermalRunStore/context verifier, immutable ResearchRegistry,
fixed OwnedFixtureRegistry and a copied read-only scope-to-context-ID map. Keys
must belong to the registry's exact tenant/point/period/goal scopes. Requests
cannot supply a context ID, date, signature, source URL, source approval or path.

The registered provider tuple must contain only the fixed owned provider. Before
admission, original manifest/bytes and declared author rights are checked; the
derived thermal snapshot ID selects an already stored, verified signed context.
Existing unit/clock/thermal preflight checks and the bundle's exact period must
match the registered scope. The job pins the provider/catalog identity, original
bundle SHA and context SHA in candidate_ids, plus the four signed context fields.
These fingerprints are references; they cannot be selected as provider requests.

Admission requires location_create, metadata and decision_context_read before
HTTP body parsing. Verification requires the two read scopes. Complete source/
context/binding checks are repeated before commit; scope drift, changed inputs,
binding drift or backend failure leaves no intent. Location IDs, idempotency
behavior and public LocationAccepted/JobStatus shapes are retained.

The trusted authority resolver reparses actual stored input and reconstructs
the exact prepared metadata. Context must have been recorded before job creation.
It permits only the registered owned-fixture collection plan, with no approved
scientific claims, no G3a candidates and no G3b approval. Research proceed means
validated procedural provider selection; downstream collection still records
G0/G1 not_accepted and Assessment hold. No data or model gate is approved here.

ApiRuntimeDependencies optionally accepts owned_research_contexts together with
owned_fixture_registry. Runtime exposes the constructed research service and
binds it to the same actual stores/current_principal. Without the mapping it
retains the original LocationResearchService and initial registry's hold.
OpenAPI's owned-research conditional scopes describe the additional two read
requirements. Clients receive no context/bundle/snapshot IDs in the response.

Worker assembly installs DecisionContract(service.authority_snapshot) as the
registered research contract in the shared CLI router. Actual exact-model
execution and independently protected operator dependencies remain required.
Tests use fake executables/controller-owned keys; this option does not establish
independent planning, original author custody, G0, G1 or agricultural validity.
