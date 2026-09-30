# Authored farm input HTTP v1

Status: proposed authenticated intake for the existing
[immutable authoring service](farm-authoring-storage-v1.md). It registers an
explicit user-owned farm input version; it neither simulates nor releases a
Run. See the [product gates](../docs/PROJECT_SPEC.md).

`POST /v1/farm-authored-inputs` accepts exactly one
`FarmAuthoringRequest` (`schema_version=farm-authoring-request-v1`) as bounded
duplicate-free JSON, at most 65,536 bytes. The server supplies the tenant from
the Bearer principal and requires the service's `WRITE_SCOPES`. It returns the
existing `FarmAuthoringSummary`: scenario and revision, exact stored input,
farm, numeric and rights SHA-256s, `registered_unpublished_inputs`, and the
immutable intent job status. It does not echo the farm fields, private rights
declaration or source records. Repeating the same scenario/revision and bytes
returns the same result; conflicting bytes return 409. Malformed transport or
schema returns 413/415/422; unavailable references/rights hold at 422;
missing authorization returns 401/403; failed storage returns 503.

`GET /v1/farm-authored-inputs?scenario_id=...&scenario_revision=...` requires
the service's `READ_SCOPES` and returns the same summary only after current
registration, selected research/thermal/economic sources and rights are
rechecked. A missing or foreign version returns 404; a revoked or incoherent
version returns 422/503 without raw input. Both routes use the existing
no-store HTTPS error envelope, closed schemas and server-side source/tenant
authority. The UI must not infer that an intent job is a completed CLI review,
independent release or simulation Run.

The standard `ApiRuntime` may assemble an exact `FarmAuthoringService` only
when its own `FarmReplayScenarioService` includes owned research. The API
rejects a different job/farm binding. Existing runtimes without this service
keep the routes unavailable. Verification covers OpenAPI, scope/owner,
idempotency/conflict, invalid body and current-source hold, then actual
HTTPS/SCRAM intake with synthetic private fixtures. Product CLI and G1 remain
separate acceptance gates.
