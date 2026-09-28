# Implemented API OpenAPI contract v1

[openapi-v1.json](openapi-v1.json) is the deterministic OpenAPI 3.1.0 snapshot
of the seventeen implemented operations. It is an internal software candidate.
Future ingestion/break-even/assessment submissions and region listings are
specified in ARCHITECTURE but are not advertised as available operations.

Generate/check with locked dependencies from `backend`:

```sh
uv run --locked --group dev python -m app.api_openapi --write
uv run --locked --group dev python -m app.api_openapi --check
```

Generation constructs the real API routes with schema-only dependencies that
refuse reads. It requires no credential, database connection, collection or
model call. The committed pretty/sorted JSON bytes must match regeneration;
tests catch drift in methods, schemas, operation IDs, statuses and auth metadata.
Changes require reviewing the generated diff and client compatibility before
updating the snapshot. This document does not authorize a deployed application.

All documented operations require HTTP Bearer over HTTPS. `ServiceBearer`
describes an opaque service credential, not JWT, OAuth or token issuance.
`x-ossf-required-scopes` lists the AND requirements from the same immutable local
tuple used by the runtime route check. We use empty arrays for the HTTP Bearer
security requirement and the vendor field for server scope names. OpenAPI 3.1
also permits role names in non-OAuth arrays; this contract chooses the explicit
vendor field. Actual credential verification remains in PrincipalMiddleware and
each store still enforces tenant/right access independently.

Operation IDs are stable: registerLocation, registerMarketUserSource, registerEconomicScenario, registerThermalScenario, getThermalScenario,
submitThermalRun, submitEconomicCalculation, getJob, getJobHold, getJobRun, getJobEconomicResult, getMarketHold,
getRun, getRunSeries, getRunManifest, getEconomicResult, getBreakEvenResult. `LocationPoint` is a
closed latitude/longitude object with coordinate bounds, matching the actual
response. Registration's request is closed JSON with a 4096-byte maximum
(`x-ossf-max-body-bytes`). Duplicate JSON keys and period ordering are runtime
checks beyond JSON Schema. All documented error responses use ErrorEnvelope.

Example body (synthetic software-contract coordinates; no approved source scope):

```json
{"latitude":37.5,"longitude":127.0,"period_start_utc":"2026-01-01T00:00:00Z","period_end_utc":"2026-01-02T00:00:00Z","goal_id":"historical-thermal-replay","idempotency_key":"one-region-intent"}
```

Only a matching approved operator registry admits it. A `202` is queued
research, not an actual model execution, data adoption or recommendation.
Authentication failure is `401` with Bearer challenge and this fixed body:

```json
{"error":{"code":"unauthenticated","message":"Authentication required"}}
```

Schema examples, synthetic Run constants and conditional/hold economic fields
grant no G0–G4 evidence. Full authenticated operator assembly, remaining
submissions, actual runtime CLI, independently approved sources/releases,
browser/G1 and public G4 remain separate work.

The [conditional break-even read](api-break-even-read-v1.md) uses a bounded
`plan_id` query to support existing Unicode/slash IDs and preserves finite-grid
status, decimal values and assessment hold. Existing operation IDs stay fixed.

The [thermal job Run read](api-job-run-v1.md) binds a completed simulation's
publication and bounded receipt to the actual input and verified Run. It returns
the existing public ThermalRunSummary, with no new response fields.

Its x-ossf-conditional-scopes declares the additional four reference scopes for
scenario-bound result v2. Existing operation IDs, response schemas and v1 scope
requirements are unchanged.

The [thermal submission](api-run-submission-v1.md) operation advertises a closed
4096-byte v2 request and explicit AND scopes. Its 202 is existing JobStatus;
the operator must configure the actual admission publisher or it returns 503.

[Scenario registration/lookup](api-scenario-intent-v1.md) return only a fixed
version acknowledgement, preserving the registered_intent boundary. GET uses
bounded query IDs to preserve the existing slash/colon identifier grammar.

[User-assumption intake](api-market-user-source-v1.md) adds seven closed request
alternatives and a 65536-byte limit. Its acknowledgement keeps the intent queued
and grants no source approval, calculation completion or forecast claim.

[Conditional scenario registration](api-economic-scenario-v1.md) joins the actual
intent and existing candidate/numeric pins in one transaction. Registration stays
distinct from subsequent calculation, CLI execution and gate acceptance.
