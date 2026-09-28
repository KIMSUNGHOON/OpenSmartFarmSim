# Immutable user-assumption market sources v1

Status: typed persistence software candidate. This is the first unavailable-market
path's user-owned assumptions, not adoption of external agricultural/market data,
an approved MarketSnapshot, a forecast or independent source review.

## Admission and replay

`MarketSourceStore.adopt_job(tenant, kind, job_id)` requires current authenticated
tenant and `market_source_write`. The caller supplies a kind and actual job ID,
never payload bytes, hashes, pins, reviewer or approval flags. In one audited
authority connection the store reads that tenant's actual immutable job input.
Only `collection`/`simulation` stages qualify; completion is not required because
the evidence is immutable submitted input, not successful collection or execution.

The bytes must match the job's hash, the exact existing strict typed model's
canonical JSON, the current tenant and bounded IDs. The 64 KiB job limit applies.
Unknown fields/kinds, external origin and noncanonical dates/decimals are rejected
with fixed private errors. Economic scenarios require both market contexts to be
`unavailable`. Existing models restrict numeric inputs and joint/settlement
assumptions to user/assumed; this store does not expand those contracts.
Canonical typed wire includes explicit default fields. References must use the
actual stored wire hash; an earlier JSON representation omitting defaults is a
different byte version. Admission never silently normalizes an existing job.

Seven kinds are supported:

| Kind | Existing type | Version key |
| --- | --- | --- |
| economic_scenario | EconomicScenario | scenario_id, scenario_revision |
| economic_input | OwnedEconomicRecord | input_id, revision |
| joint_shock | JointShock | shock_id, revision |
| input_rights | InputRights | input_id, revision |
| settlement_applicability | Applicability | binding_id, revision |
| settlement_evidence | OwnedSettlementRecord | settlement_ref, revision |
| prior_batch_cost | PriorBatchCostRecord | cost_ref, fixed `single` |

The final existing type has no revision field. Corrections require a new cost_ref;
the reader never selects a mutable latest record. Other corrections use a new
explicit revision. Tenant/kind/ID/revision is unique. Identical bytes are idempotent,
including another qualifying job with identical bytes; the first job binding is
preserved. Conflicting bytes roll back. Owner-installed foreign key/hash checks
and UPDATE/DELETE triggers protect the table. No automatic migration is run.

Stored metadata includes canonical bytes/hash, actual job ID, store version,
`admission_kind=contract_valid_user_assumption`, actual authority login and DB
recording time. The admission marker describes software validation only; it is
not agricultural QC or an independent reviewer. Typed payloads preserve their
explicit units, source references, availability/effective dates, rights and
evidence references. Original raw hashes remain references, not restricted data.
The job validator permits only the exact `raw_sha256` key with a lowercase 64-digit
hex string; other raw/secret names, aliases and invalid values remain rejected.

Every getter requires `market_source_read`, scopes the DB query to the current
tenant, verifies model/identity/hash/actor/version and the original job bytes
again, and returns a fresh Python projection with typed dates. Baseline scenario
pins and shock pins are generated from verified rows; caller-supplied pins are
unsupported. The baseline pin's immutable input reference is the actual job UUID,
and both hashes equal the exact stored scenario/job bytes.

Storage does not assert that availability, rights, effective scope, settlement
links, numbers or a joint shock are usable in a particular calculation.
`MarketScenarioService`/`EconomicLedger` still validate those together for the
specific decision; results remain `conditional_user_assumption` and Assessment
`hold`. The assembled signed hold/DecisionContext remains a separate authority.

## Authenticated profile and assembly

Keyword-only `RuntimeLoginPolicy.market_source_storage=False` requires exact bool.
True requires market_calculation=True and opts into audit version
`runtime-market-source-login-policy-v5`. It adds only market_source_records to
the immutable authority SELECT/INSERT matrix. General request/worker/supervisor
roles have no rights. NOLOGIN v1 and login v2/v3/v4 defaults retain their matrices
and versions; no existing role is automatically upgraded. The store requires an
explicit matching v5 authority binding, with no unbound fixture/owner fallback.
Every connection validates real SCRAM identity and the full effective grant audit.

An operator may supply a factory returning this store through the existing
[API assembly](api-runtime-assembly-v1.md) source interface. That assembly also
requires break_even_calculation=True and current_principal; read principals need
market_source_read as well as existing candidate/result/grid scopes. Source write
is a server admission operation. Subsequent [HTTP intake](api-market-user-source-v1.md)
binds all seven types to actual immutable intent bytes in one transaction. Protected
configuration, owner provisioning and actual source submission orchestration
remain separate work.

No source URL/product, observation/publication/retrieval time, vintage, independent
QC/reviewer or third-party rights is inferred. External source G0, actual CLI,
independent release/custody, G1/G4 and browser operation remain unproven. Synthetic
DB/TLS/grant tests never substitute for them. New code changes the closed thermal
code digest and needs a fresh independent release; old records remain unchanged.
