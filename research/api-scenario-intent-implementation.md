# HTTP thermal scenario intent implementation evidence

Status: software contract candidate, not independent domain, source or G1/G4
acceptance. The root Codex CLI session's turn_context at
2026-09-28T15:07:54.754Z records gpt-6-sol / xhigh (thread
01a0e064-b01b-7a22-8ef8-dd4afe0eb7dc). No recursive CLI, additional model or new
subagent was launched. No agricultural/economic coefficient or arithmetic is
changed by this slice.

## Boundary

[Registration/lookup contract](../contracts/api-scenario-intent-v1.md) exposes
the existing [actual v6 Store](../backend/app/thermal_scenario_store.py).
The API injects the authenticated tenant into the strict intent, returns only a
five-field version acknowledgement and preserves registered_intent. Actual
source/context/hold references and current scopes are rechecked by the Store.
Conflicts use a specific ThermalScenarioHold subtype without changing immutable
storage. IDs with slash/colon use bounded lookup query arguments. HTTP Run
submission still performs full publisher admission; registration grants no gate.

The three JSON submission routes use one bounded duplicate/nonfinite-rejecting
helper. Existing location/Run admission ordering and statuses remain unchanged.
The OpenAPI request inlines the generated unavailable-market schema because a
schema-local $defs reference would otherwise target the OpenAPI document root.
The closed code digest includes the two new modules; a fresh independent release
is required. No existing fixture/schema/source/release data is rewritten.

## Verification

Actual RED: authenticated SCRAM fixture POST returned 404 before the route
existed. Initial registration/lookup, immutable retry/conflict/new version,
tenant/scope/reference/transport/error tests passed **23 in 32.87 s**.
The first OpenAPI reference-resolution test found the misplaced nested $defs
reference; it was replaced by the inline generated market schema. Existing
OpenAPI reference and per-operation scope checks cover that correction.

Expanded scenario/Store/Run/location/OpenAPI regressions passed **132 in
160.34 s**. After collection, three further cases were added and passed
**3 in 13.16 s**: write-scope revocation inside the actual registration transaction
rolls the insert back with HTTP 403; slash/colon IDs retain identity through the
query route; an HTTP registration's actual returned hash binds to HTTP queue,
targeted worker completion and verified public Run lookup. The final three were
not part of the earlier 132. Worker/review signatures remain synthetic.

Locked OpenAPI export/check and **109 local link targets, none missing** passed.
Final review covered required request fields/authenticated tenant injection,
scopes before reads, actual immutable record/source checks and in-transaction
rollback, compatible conflict subtype, fixed errors/private-field omission,
query identity, source/model profiles and admission's distinct gate checks.
The generated OpenAPI diff adds only the two scenario operations and summary
schema; existing operation IDs/response schemas and JSON submission behavior
are preserved. Broader API/runtime/UID/Compose hosted acceptance follows the
implementation commit and must match its exact head. No optional broad rerun
was done after the three final tests; the implementation code did not change.

## Holds

Fixtures use controller-owned synthetic keys/captures and actual SCRAM stores.
They prove software registration/queue/publication contracts only. Actual product
CLI, independent release/authority/custody, protected deployment, complete farm/
economic Scenario, workflow assessment, 3D/browser/full G1/G4 and actual G0/G2/G3
evidence remain unaccepted. No broad checkbox or gate is promoted here.
