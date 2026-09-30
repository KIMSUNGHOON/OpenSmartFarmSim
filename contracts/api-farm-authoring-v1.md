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

`GET /v1/farm-authored-inputs/catalog` lists the authenticated tenant's
**historical registration metadata** in descending `(created_at, job_id)`
order. `limit` is 1–50 (default 20); `before_created_at` and `before_job_id`
must be supplied together as the previous page's `next_cursor`. The response
contains only `FarmAuthoringSummary` items and the next cursor. The server
checks the immutable job input hash, authoring version, tenant, identity key,
and stored farm/numeric/rights digests before projection. It never returns
the farm body, source records, rights declaration, credentials or CLI output.
The same `READ_SCOPES` apply. A revoked source may leave its registration
metadata visible to its owner: the catalog does **not** certify current use
rights, independent release, a completed Run or G1. Opening an item always
calls the existing single-version GET, which rechecks the current references
and either returns the exact stored hash or holds. A foreign tenant sees no
items. A malformed cursor returns 422; unavailable storage returns 503.

`GET /v1/farm-authored-inputs/activity` accepts `scenario_id`,
`scenario_revision`, and the exact `registration_sha256`. `limit` is 1–50
(default 20). It returns historical authored review/simulation job entries newest first,
with the same `(created_at, job_id)` cursor pair as the catalog. Each entry
contains a public `JobStatus`; a simulation entry also contains the public
status of its bound review job. The server checks the owned immutable
registration, each job's input digest and typed registration/version binding,
and each simulation's review link. It omits prompts, source bytes, lease
tokens, reason details, rights declarations and private artifacts. A missing
registration is 404; a mismatched hash, malformed cursor or broken stored
binding holds. The catalog's `READ_SCOPES` apply.

Activity is **historical metadata**. Its entries do not prove current source
rights, a signed release or a published Run. Resuming a job in the UI must
recheck the selected registration and live job status; `POST` admission and
Run reads continue to use their independent current-evidence checks. Loss of
current rights therefore blocks use even when an old completed job remains
visible. Large-tenant query latency is unmeasured and remains a G4 hold.

The standard `ApiRuntime` may assemble an exact `FarmAuthoringService` only
when its own `FarmReplayScenarioService` includes owned research. The API
rejects a different job/farm binding. Existing runtimes without this service
keep the routes unavailable. Verification covers OpenAPI, scope/owner,
idempotency/conflict, invalid body and current-source hold, then actual
HTTPS/SCRAM intake with synthetic private fixtures. Product CLI and G1 remain
separate acceptance gates.
