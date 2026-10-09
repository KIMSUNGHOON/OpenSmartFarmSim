# Owned ingestion and collection review HTTP v1

Status: internal software connection candidate. Actual CLI, independent release,
source adoption, browser/G1 and production G4 acceptance remain pending.

## Requests and responses

| POST path | Closed JSON request | Required AND scopes |
| --- | --- | --- |
| /v1/ingestions | research_job_id (canonical UUID), idempotency_key | metadata, artifact, collection_execute |
| /v1/collection-reviews | collection_job_id (canonical UUID), idempotency_key | metadata, artifact, collection_read, collection_review_create, thermal_snapshot_read, thermal_snapshot_write, decision_context_read |

Both requests use strict frozen models, forbid additional fields, limit bodies
to 4096 bytes and keys to the existing ASCII identifier grammar/200 characters.
Tenant, URLs, original bytes, signatures, dates, source approvals, coefficients
and results are obtained from protected dependencies and actual stored evidence.

Examples describe software fixture requests; the illustrative UUIDs must be
replaced by actual same-tenant completed parent jobs.

```json
{"research_job_id":"00000000-0000-4000-8000-000000000001","idempotency_key":"owned-ingestion-one"}
```

```json
{"collection_job_id":"00000000-0000-4000-8000-000000000002","idempotency_key":"owned-review-one"}
```

Responses are 202 with existing JobStatus. They expose no tenant, source record,
snapshot, proof or private path. Identical retries reuse the actual job and its
current state; completed collection can return succeeded. The immutable record
preserves Assessment hold and G0/G1 not_accepted. Review admission stages a
candidate, not an adopted snapshot.

## Assembly and admission

The API requires exact CollectionService and OwnedCollectionReviewService
objects bound to its actual JobStore/ThermalRunStore and the same request
principal provider. Review requires the matching collection service.
ApiRuntimeDependencies optionally accepts an exact protected OwnedFixtureRegistry;
ApiRuntime assembles both services with existing SCRAM authority stores and
current_principal. Without this dependency, authenticated/scoped calls return 503.

Collection admission revalidates completed research, selection, stored output,
validator/capture/invocation evidence and the fixed original bundle. Its parent
owns coordinates/period; HTTP cannot override them. Review revalidates completed
collection/original bytes and a preexisting signed context, then stores snapshot
candidate and queued intent in the same transaction. Existing commit guards
recheck current scopes and bindings, preserving snapshot-before-job chronology.

Namespaced idempotency keys are preserved. Different input for the same intent
returns 409; review now preserves JobIntentConflict instead of wrapping it.
CollectionReviewHold is the typed bounded prepare error for unavailable stored
inputs. Other admission failures remain fixed 503. Snapshot/job insertion rolls
back on conflict, scope drift, binding drift or backend failure.

Errors: 401 unauthenticated; 403 scope denied; 409 intent conflict; 413 body too
large; 415 unsupported media; 422 malformed request or unavailable parent/context;
503 missing service or admission unavailable. OpenAPI operation IDs are
submitOwnedIngestion and submitOwnedCollectionReview; scope tuples match runtime.

Actual exact-model CLI, independent planning/isolation/custody/release, source
adoption, complete orchestration and UI/3D remain necessary. The initial
ResearchRegistry hold and all G0–G4 gates are preserved.
