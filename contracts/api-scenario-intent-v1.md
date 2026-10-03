# Thermal scenario registration and lookup v1

Status: internal software candidate. This exposes the existing immutable thermal
selection intent, not a complete farm/economic Scenario, approved input or G1/G4.

## Registration

`POST /v1/scenarios` / registerThermalScenario accepts closed strict JSON up to
4096 bytes. The fields are exactly
[ThermalScenario](thermal-scenario-store-v1.md)'s fields except tenant_id:
schema_version, scenario_id, scenario_revision, snapshot_id,
decision_context_id, market_context, zone_id, goal_id, model_version,
parameter_set_version, origin and evidence_level. All are required. Tenant comes
from the authenticated principal, never a body, query or header override.
The supported literals/profile and unavailable MarketContext are unchanged.
The API injects that tenant before the actual Store's canonical validation/write.

The AND scopes are thermal_scenario_write, thermal_scenario_read,
thermal_snapshot_read, decision_context_read and market_hold_context_read.
They are checked before any store access. Actual signed references, fixed input
hashes/profile and current scopes/bindings are then rechecked by the v6 Store,
including inside its transaction and immediately before commit. The snapshot's
authorship is not relabeled by the selection intent's user/assumed labels.

`200` acknowledges registration with exactly scenario_id, scenario_revision,
scenario_sha256, status=registered_intent and the actual first recorded_at.
It returns no raw input, reference pins, tenant, review/context/decision IDs,
crop output, calculated Run or approval. The hash may be supplied to
[thermal Run admission](api-run-submission-v1.md), which performs its own full
publisher gates before queueing; a registered intent alone cannot authorize it.

Tenant/scenario/revision is the existing immutable intent key. Identical retry
returns the same hash and first timestamp; changed bytes for that key return
fixed `409 scenario_conflict`. Corrections create a new revision. The conflict
exception remains a ThermalScenarioHold subtype for existing Store callers.
No extra idempotency table, overwrite, migration, coefficient or default input
is introduced.

## Lookup and errors

`GET /v1/scenarios?scenario_id=...&scenario_revision=...` / getThermalScenario
returns the same five-field acknowledgement. Query IDs preserve the existing
bounded ASCII identifier grammar, including slash/colon; they are not path
segments. Its AND scopes are the four registration scopes except write.
Every lookup uses the actual tenant/version row and revalidates current signed
references and pins, rather than trusting a previously returned hash.
Unknown/other-tenant versions are fixed 404. Denied access is 401/403.

Invalid request/duplicate JSON/nonfinite numbers are fixed 422; body/media bounds
are 413/415. Missing registration references are fixed 422 scenario_hold.
Current scope denial during registration returns 403 and the Store rolls back
the insert. Unexpected registration or lookup errors are fixed 503. Missing
configured v6 store is fixed 503 scenario_unavailable after authorization.
No error exposes input values, raw source, private identifiers or exception text.

The existing location and Run submissions now share the same bounded JSON
transport helper. Their early auth/configuration checks, schemas, accepted
states and fixed error codes remain unchanged. OpenAPI inlines the single
unavailable-market schema so nested request references resolve correctly.

## Limits

Existing ApiRuntime with explicit v6 already assembles the actual Scenario
store; this adds no default authority, key, publisher factory or CLI execution.
Software tests use real SCRAM and immutable records with synthetic signed
references/captures. Actual CLI/independent release/custody, protected deployment,
full farm/economic scenarios, collection/assessment, browser/full G1/G4 and
G0/G2/G3 evidence remain unaccepted. Changed code requires a fresh independent
release; existing source/fixture/release evidence is not rewritten.
