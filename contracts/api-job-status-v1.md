# Job status HTTP slice v1

Status: internal G1 API software candidate. This implements only the previously specified `GET /v1/jobs/{id}` read path; it does not submit, run, or assess a job.

`GET /v1/jobs/{job_id}` accepts a UUID path parameter and derives the tenant from a trusted server principal provider, never from request headers, query parameters, or the URL. An authenticated principal with the `metadata` scope may read only a job that the tenant-scoped `JobStore` also authorizes. The response contains `job_id`, `stage`, `state`, `attempt_count`, `max_attempts`, `created_at`, `updated_at`, and `reason_code` (null when no reason is recorded). `state` uses the durable job vocabulary. `reason_code` is the stored short machine code only; the API does not return the arbitrary reason JSON, input bytes or hash, tenant ID, idempotency key, lease token, CLI prompt/output, or raw evidence. A completed calculation job's `succeeded` state is not an Assessment pass.

Error bodies use `{ "error": { "code": "...", "message": "..." } }`: `401` for missing/invalid authentication, `403` for absent metadata scope, `404` for missing or foreign-tenant jobs, `422` for a malformed UUID, and `503` when the store cannot be read. Error messages do not include database exceptions, IDs, or source data. The OpenAPI 3.1 fragment is generated from typed FastAPI/Pydantic models and checked by the focused API test.

This read path has no product login, submission flow, market hold report association, Run/result/Assessment endpoint, or full end-to-end G1 evidence yet. Those remain in `api-flow` and later tasks.
