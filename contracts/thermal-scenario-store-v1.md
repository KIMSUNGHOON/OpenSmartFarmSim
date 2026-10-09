# Thermal scenario intent storage v1 / explicit login v6

Status: internal software candidate. This stores the thermal component of a
future product Scenario; it does not implement the complete farm/economic plan,
Run submission or G1/G4 acceptance by itself. Subsequent
[HTTP thermal admission](api-run-submission-v1.md) binds it to an actual queued
v2 job after publisher evidence checks; complete farm/economic plans are pending.
The [HTTP registration/lookup](api-scenario-intent-v1.md) returns only the actual
version/hash/status/first timestamp under current write/reference scopes.

[ThermalScenario](../backend/app/thermal_scenario_store.py) and its
[closed schema](thermal-scenario-v1.schema.json) identify a tenant/scenario/revision,
actual immutable thermal snapshot and signed DecisionContext, an existing
`unavailable` MarketContext, one conceptual zone label, historical thermal replay
goal and the fixed thermal-v1/synthetic-thermal-parameters-v1 model profile.
All fields are required. Selection intent is `origin=user`, `evidence_level=assumed`;
these labels do not relabel the separately authored source records. IDs are
bounded to 200 characters. No coefficient, tariff, crop output, money, geometry
override, default-zero input or gate decision is accepted. The zone ID labels
the single fixture zone; it changes no physical parameter. Its actual facility,
initial conditions and control values remain in the pinned snapshot. This first
contract supports only the existing synthetic thermal profile and ex-post replay.
Later physical scenarios and economic/crop links need explicit contracts/versions.

`ThermalScenarioStore(runs, holds)` requires exact existing store classes, same
DSN/schema/authority policy/principal callable, and holds bound to that Run store.
The optional exact-boolean `thermal_scenario_storage=True` selects login v6.
All previous flags remain independent and default false; with this flag false,
the previous v1–v5 table permissions and version selection remain unchanged.
The added `thermal_scenarios` table grants only authority SELECT/INSERT; request,
general worker and supervisor receive no access. Existing SCRAM login and full
effective-grant audit execute for every connection. There is no owner fallback.

Before fresh v6 roles, a protected provisioner installs the new table with
`install_thermal_scenario_schema` after existing snapshot/context/hold tables.
Runtime never provisions roles, migrates objects or installs passwords. No
in-place grants upgrade command is supplied; existing installations remain
unchanged until an operator explicitly provisions and audits the new profile.
The table has tenant/snapshot/context foreign keys, a content-hash check,
bounded canonical payload (4096 bytes) and exact four-hash pin bytes (1024).
Updates/deletes are rejected by its immutable trigger.

`put(tenant, value)` revalidates even constructed/copied models and current write
scope. Existing snapshot integrity, signed context and signed Market hold are
read under their existing scopes. Tenant/snapshot/context/mode/decision time must
match; hold scope is rechecked by MarketHoldStore. The fixture profile is checked
structurally. The source manifest/weather/thermal and context hashes are pinned.
Registration does not assert source rights/QC or authorize calculation: the
publisher's full source/execution/release/physics gates remain required later.

Identical tenant/scenario/revision retries preserve the first timestamp and
bytes. Conflicting bytes are rejected; correction creates a new revision or ID.
Write scope/binding is rechecked before commit and failure rolls insertion back.
`get(tenant, id, revision)` checks read scope, fixed identity/hash/actor and all
current references/pins again. Wrong tenant, denied scenario read, invalid ID or
unknown record returns None. Other failures have fixed ThermalScenarioHold
messages; no credential, raw exception or source byte is exposed.

The result is `status=registered_intent`, a frozen scenario, its SHA-256, four
input pins and DB registration time. It is neither accepted Run nor G0 approval,
farm accuracy, predicted crop/margin, ranking or operating evidence. Missing
physical/economic/crop evidence remains a hold; future workflow must join these
components and repeat relevant gates. No model invocation is made by this store.
