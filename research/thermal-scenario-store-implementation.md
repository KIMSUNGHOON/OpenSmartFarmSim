# Thermal scenario intent / v6 implementation evidence

Status: persistent thermal-component software candidate, not complete product
Scenario, actual CLI execution, source approval or G1/G4 acceptance.

Active Codex CLI thread 01a0e064-b01b-7a22-8ef8-dd4afe0eb7dc made this domain/
interface judgment. Selectively inspected actual turn_context at
2026-09-28T13:44:38.142Z records exact gpt-6-sol/xhigh. Reviewable output is the
[store](../backend/app/thermal_scenario_store.py),
[contract](../contracts/thermal-scenario-store-v1.md),
[schema](../contracts/thermal-scenario-v1.schema.json) and
[tests](../backend/tests/test_thermal_scenario_store.py).
No recursive CLI, additional model call, subagent or external source adoption
was performed. This evidence is not independent gate approval.

The next documented Run submission requires Scenario ID/version, but no thermal
Scenario object was persisted. The implementation records selection intent and
references to existing immutable snapshot/model/context/market-hold objects.
It creates no physical/economic coefficient or output. The zone label represents
the one fixed conceptual fixture zone; all geometry/initial/control values stay
in the original snapshot. Full physical/economic/crop Scenario composition and
HTTP submission remain subsequent work. Registration has explicit
`registered_intent` status and does not open any gate.

The optional exact-bool thermal_scenario_storage flag selects v6 and only adds
authority SELECT/INSERT for the new immutable table. It defaults false and
leaves previous profile permissions/version selection unchanged. No runtime
schema/role/password provisioning or owner fallback is introduced. Fresh tests
install the table before dedicated-owner grants, then use actual SCRAM and
existing full per-connection audit. A future installation needs protected,
explicit operator provisioning; no deployment or upgrade is implied.

## Focused verification

RED: the new module was absent (collection error). First implementation exposed
a context timestamp field mismatch: the signed store uses decision_at_utc while
the hold read uses a datetime; the existing UTC parser now compares those exact
times. Then **19 cases passed**, with one test incorrectly expecting
RolePolicyHold instead of the existing Run-store login wrapper. The new store
now consistently masks connection failures as fixed ThermalScenarioHold.

Local PostgreSQL 16.15 / SCRAM with locked dependencies:

- New scenario registration/reload/revision/immutability, invalid input, actual
  snapshot/context/hold/scope failures, tenant/scopes/grant drift, matching v6
  binding, constructor bypass and write-scope revocation rollback: **22 passed
  in 33.12 s**.
- [Normative schema equality/closed contract](../backend/tests/test_thermal_scenario_contract.py):
  **1 passed in 0.24 s**, without database or credentials.
- OpenAPI exact check passed unchanged; no submission route is advertised yet.

The initial schema-only test placed in the parametrized DB module could not
collect; it was moved to its own database-free module. This is a test layout
correction, not a source/gate failure. Existing profile/market/API regression
passed **110 in 386.73 s** (runtime roles/login, persistent market sources and
API runtime). Final changed-file/schema/link/whitespace review passed:
**106 local links, none broken**. Review inspected default-false profile
compatibility, authority-only table privileges, actual login/grant audit,
bounded canonical input, signed reference identity/time/pins, immutable
conflict/revision behavior, write-scope rollback, safe errors and absence of
new arithmetic or source/gate approval. The HTTP contract remains unchanged.

## Remaining holds

All keys, signatures, review captures, scope resolver and fixture records are
synthetic and controller owned. Actual CLI/independent context/release/custody,
operating configuration, complete farm/economic Scenario, Scenario-to-Run
identity and admission/worker/HTTP orchestration, browser/3D and full G1/G4 are
pending. Actual G0/G2/G3 evidence remains missing. Original immutable fixture,
source/release versions and arithmetic are unchanged. New store/schema and
policy code enter the closed runtime digest and require a fresh independent
release. Broad task checkboxes remain open. Hosted verification follows the
implementation commit and must match its exact head.
