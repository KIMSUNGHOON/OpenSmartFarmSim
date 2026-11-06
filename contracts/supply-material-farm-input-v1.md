# Owned material inputs and initial seed custody for an exact Farm v1

Status: accepted — [163 focused checks and actual owned SCRAM/seed proof](../research/farm-owned-input-and-seed-20261106.md). Acceptance covers immutable owned material Farm inputs and genuine initial seed custody; completed material simulation, cost association and product views remain pending.

The [accepted material/cost scope kernel](supply-material-resource-cost-scope-binding-v1.md) remains a research intermediate. This step establishes newly admitted owned inputs and their genuinely consumed initial carbon/stem/individual Context for an exact current Farm registration. Existing numerical code, old fixtures/results, `FarmInputs.economic`, schema3 economic selection and the separate schema4 cost path remain unchanged.

## Modules and exact interface

```python
# app.crop_supply_material_farm_inputs
MaterialFarmInputService(farms)
    .submit(tenant, request_raw: bytes) -> JobStatus
    .current(tenant, job_id: str, expected_input_sha256: str) -> VerifiedMaterialFarmInput
MaterialFarmInputHold(ValueError)
_request(raw: bytes) -> dict
_utc_fraction(aware_datetime) -> Fraction

# app.crop_supply_material_farm_seed
MaterialFarmSeedProducer(service, directory, access)
    .produce(tenant, job_id: str, expected_input_sha256: str) -> VerifiedMaterialFarmSeed
MaterialFarmSeedHold(ValueError)
```

`farms` is exactly the existing `FarmAuthoringService`; `service` is exactly `MaterialFarmInputService`; `access` is exactly `ContentAccess`. The authority JobStore is `farms.replay.jobs` with the existing audited authority/runtime crop-result profile. The constructor fixes the server directory, access, authority and implementation identities. No public request selects a tenant, path, provider, callback, root, profile file or code implementation. Job UUIDs are canonical lowercase strings; SHAs are lowercase64hex. Permission failures retain `PermissionError`; immutable intent conflicts retain `JobIntentConflict`. Invalid/unavailable/current-binding failures use the respective fixed Hold class without partial success.

Verified input exposes read-only `input_bytes` (the actual immutable bytes), `request` (a fresh JSON copy), and `witness` (a fresh detached resolved-row JSON copy below). Verified seed exposes read-only `context` (the genuine original `crop_stem_root_stock_continuation.Context`), `initial_binding_bytes` (the original canonical binder proof), `carbon_root_sha256`, `stem_root_sha256`, and `witness` (a fresh seed-witness JSON copy below). Verified types are immutable and issued only by their exact server services with private construction/token checks. Copied JSON or a hash is not a capability. No verified object is accepted in place of current owned-row resolution.

## Closed canonical request

All fields are required; no implicit defaults. `_request` rejects duplicate keys, nonfinite/nonstandard JSON, unknown fields, malformed UTF-8 and wrong types. Canonical JSON is UTF-8, sorted keys, separators `(',', ':')`, `ensure_ascii=False`, `allow_nan=False`; input must equal its canonical encoding. Preserve original nested numeric types/values. New names use the existing Farm identifier syntax and200-character cap; source model identifiers retain their original validators. JSON depth is at most64 and nodes at most32768. Request bytes and the ENTIRE stored input including its server witness must each fit the unchanged `jobs.MAX_INPUT_BYTES=65536`; reject overflow. Do not hide raw source in encoded strings, relax blocked input keys, raise the cap or spill to a client directory.

| Object | Exact keys / values |
|---|---|
| request | `schema_version='supply-material-farm-input-request-v1'`, `study_id`, `revision`, `farm`, `source`, `rights`, `provenance` |
| farm | `scenario_id`, `scenario_revision`, `registration_sha256`, `crop_id`, `zone_id` |
| source | `carbon_stock_inputs`, `stem_program`, `stem_start_index`, `individual_program`, `numerical`, `tracking_basis`, `profile_sha256` |
| numerical | `step_seconds`, `step_count`; original supported numeric types, finite positive step, original integer count/horizon/scalar caps |
| tracking_basis | `kind='one_tracked_shoot_on_declared_model_floor_research_v1'`, `shoot_id`, `model_floor_area`, `tracked_shoot_count={'value':1,'unit':'tracked_shoot'}` |
| profile_sha256 | `growth_profile`, `cohort_profile`, `transport_profile`, `exchange_profile`; the existing four exact research-profile SHAs |
| rights | `schema_version='supply-material-farm-input-rights-v1'`, `declaration_id`, `revision`, `ownership_asserted`, `access`, `store`, `transform`, `use`, `display`, `redistribute`, `available_at`, `reviewer` |
| provenance | `origin='own_declared_synthetic_assumptions'`, `product_id`, `source_ref`, `revision`, `observed_at=null`, `published_at=null`, `available_at`, `retrieved_at`, `qc='software_contract_only_not_farm_measurements'`, `reviewer` |

All six ownership/access/store/transform/use/display grants are explicitly true and top redistribution is false. `provenance.product_id` equals `study_id`, its revision equals request revision, and both reviewer fields agree. These are self-authored synthetic declarations, not independent rights/data/gate approval.

`carbon_stock_inputs` is the entire original closed `leaf-carbon-stock-artifact-input-v1` document. `stem_program` is the entire original closed `morphology-software-program-v2`. `individual_program` is the entire original explicit stem/root program accepted by `crop_stem_root_stock_continuation.prepare_context`; it has no newly inserted schema key. Preserve its original policies, scenario, leaves, model floor, capacity outflow and explicit `stem_root_compartments`. `stem_start_index` is an explicit bool-excluding integer, -1 for the newly produced stem's original state or an actual declared output sample index. This is not a public artifact reference.

Admission performs pure closed structure/unit/domain/identity checks, using the original reader schemas where pure. In particular it does not call individual `_prepare`, Context constructors, area initialization, RHS, advancement or original producer functions: they calculate. Check the individual program's closed original fields/units/policies, explicit compartment IDs/kinds, and unchanged non-stem request components against the carbon input without inventing an aggregate allocation. The original numerical initialization and original exact initial-inventory/balance checks occur only in the authorized producer; a structurally admitted unsupported numerical state can still hold there.

The server loads the exact four original profile bytes/classes and license notice, validates their fixed SHA identities and retains their existing scope. It accepts no new coefficients, cultivar profile, tariff, source unit or scaling. Source component SHAs use the original canonical codecs; the outer immutable input uses the existing JobStore codec.

## Farm, basis and time mapping

Resolve the exact Farm through `registration_read_scope` and `read_registration(tenant, scenario_id, scenario_revision, registration_sha256)`. The actual registration row/input SHA, original Farm/rights/source/context/compiled-input witnesses remain current before and after each boundary. `crop_id` must exist and `zone_id` equal the registered single-zone facility. Shared tenant or batch labels do not establish this link.

The first supported mapping is `same_registered_single_zone_floor_v1`: exact rational equality of original Farm `facility.floor_area` decimal (`m²`) and original carbon/individual/tracking `model_floor_area` binary64 (`m2_floor`). Preserve all original representations. Require the existing initial binder's equal footprint and ordered complete inventory; no conversion or rescaling of counters, carbon, geometry or costs. The declared one tracked shoot is not validated density or a whole-Farm plant population. Copy actual cultivable/crop areas without using them to scale. Registered species/variety does not select a coefficient or prove applicability.

The former Farm fixture100m² and seed fixture1m2_floor are incompatible. The positive must explicitly author a NEW consistent Farm and NEW compatible owned inputs; for example an independently declared Farm floor/cultivable/crop area1 and original model floor1. Preserve both old fixtures unchanged. Never alter source quantities to manufacture a positive. Actual whole-request/intent/witness64KiB sizing is required evidence, not assumed from component sizes.

The carbon model origin and actually selected stem time must agree exactly under the original binder. Preserve original UTC strings and integer-origin plus reduced Fraction seconds; `_utc_fraction` uses integer UTC days/seconds/microseconds, never `timestamp()`, `total_seconds()` or float. Do not round submicrosecond elapsed times into datetime. Require each complete declared source/individual support and selected seed time inside both selected crop occupancy and the Farm evaluation calendar. Farm dates cover Asia/Seoul midnight at period_start through midnight after period_end; crop occupancy is half-open. Check positive support with `start<=left<right<=end`; a selected instantaneous seed satisfies `start<=at<end`. Do not substitute harvest/sales windows or move a source epoch.

Farm thermal initial/forcing units (`K`, `kg_v/kg_da`, `kg_da/s`, `W`, etc.) do not supply material initial state/forcing (`degC`, `mg_CH2O/m2_floor`, `kg_water/m2_floor`, `W/m2_floor`, `ppm`, photon flux). The material program contains explicit supplemental owned assumptions in its original units. Do not coerce the Farm thermal compiler, infer air density/volume-per-floor/plant count, or derive carbon from geometry. The original binder preserves its one-shoot and no per-plant conversion/unvalidated density limits.

All availability/grant/retrieval times are mandatory aware ISO `YYYY-MM-DDTHH:MM:SS[.1–6 digits](Z|±HH:MM)`. Preserve original text; compare exact UTC microseconds. At the first intent the server captures one actual aware UTC `server_review_at` and requires:

- every original nested carbon/stem rights `declared_at_utc <= rights.available_at`;
- `rights.available_at <= provenance.available_at <= provenance.retrieved_at <= server_review_at`;
- all current grants and required source timestamps are present/usable. Original observed/publication remain null; do not infer timestamps.

At every current/produce/commit fence require these times AND the stored review time no later than a fresh actual server `current_at`. Future grants or a backwards clock hold. Retry/current checks never advance the stored review or declared dates. The original Farm authority's historical `ex_post_replay` remains unchanged: newly recorded material inputs are explicitly `supplemental_ex_post_synthetic_material_assumptions`, with `ex_ante_validity='not_established'`. Keep the original Farm decision/context, model epoch, declared availability/retrieval/grant times and actual DB recording distinct. Even a declared date before the Farm decision is not proof of actual prior availability. Do not backdate a new row or rewrite the Farm registration/market vintage.

## Noncircular persisted and resolved witnesses

The stored collection input has exactly `input_version='supply-material-owned-input-v1'`, server-copied `tenant_id`, original `request`, `content_witness`, `content_witness_sha256`. The latter hashes only the canonical subobject. The input contains no field with its own full input SHA.

The closed content witness has exactly:

| Key | Exact shape |
|---|---|
| schema_version | `supply-material-farm-input-content-witness-v1` |
| farm | original exact five-field pin |
| registration | `registration_job_id`, `registration_sha256`, `farm_sha256`, `rights_sha256`, `source_binding_sha256`, `numeric_input_sha256`, `crop_sha256`, `facility_sha256`, `decision_at`, `decision_context_id`, `context_sha256`, `snapshot_id`, `calendar_utc`, `occupancy_utc` |
| components | `carbon_stock_inputs`, `stem_program`, `individual_program`, `numerical`, `tracking_basis_sha256` |
| normalization | `mapping_version='same_registered_single_zone_floor_v1'`, original `farm_floor_area`, original `model_floor_area`, original `tracking_basis` |
| time_scope | `model_origin_utc`, `carbon_duration_seconds_exact`, `individual_duration_seconds_exact`, `stem_program_start_utc`, `stem_program_end_utc`, `selected_stem_at_utc`, `declared_dates`, `assumption_mode`, `declared_availability_vs_farm_decision`, `ex_ante_validity` |
| rights_policy | `version='supply-material-farm-input-rights-v1'`, `effective_rights={'use':true,'display':true,'redistribute':false}` |
| implementation | `authority_version='supply-material-owned-input-v1'`, current `code_sha256` map, fixed `profile_sha256` map, `notice_sha256` |
| server_review_at | the first actual server review time |

Registration job/SHA refers to the ALREADY EXISTING Farm row. Hash original Farm/rights/crop/facility/source-binding canonical JSON and original compiled thermal bytes without substituting new representations. Calendar/occupancy objects have exactly `start`,`end`, aware UTC strings. `context_sha256` is the original Farm binding context hash. Each of the three components has exactly `format_id`,`sha256`,`bytes`; format IDs respectively `leaf-carbon-stock-artifact-input-v1`, `morphology-software-program-v2`, `stem-root-stock-program-interface-v1`. The last is this wrapper's interface tag, not a claim that the original individual program has a schema_version. `numerical` is the original two-field object. Exact seconds have reduced integer string `numerator`,`denominator`, `unit='s'`. `declared_dates` has exactly `rights_available_at`,`provenance_available_at`,`provenance_retrieved_at`,`carbon_rights_declared_at_utc`,`stem_rights_declared_at_utc`. The assumption mode is the supplemental ex-post literal above; declared relation is `before_or_at` or `after`; ex-ante remains not_established.

No new input job UUID/full input SHA/created_at, execution attempt, future computed root/Context or publication facts enter this pre-insert witness. Only existing input-component descriptors are permitted. Never precompute a seed to populate metadata admission.

After insertion `current()` resolves the actual verified row and returns a detached witness with exactly `schema_version='supply-material-farm-input-resolved-witness-v1'`, `tenant_id`, `owned_input`, `content_witness_sha256`, original `content_witness`. `owned_input` has exactly `job_id`,`input_version`,`input_sha256`,`created_at`,`stage`,`state`, copied from the actual row, with stage collection and supported unclaimed input-registry state queued. A canceled/failed/claimed/otherwise changed input holds; it is not automatic collection work. This detached object can contain the whole input SHA because it is not stored inside that input. `created_at` is the actual first DB value, not review/response/model time. Retain both it and the original Farm decision; compare those actual facts independently of declared availability. The declaration may be invalidated by existing current principal/Farm/rights policy or explicit input cancellation; no external/restricted-data adoption is supported.

Use the existing atomic JobStore intent uniqueness with a domain-separated key from study_id/revision. Same request retry preserves first UUID/input bytes/SHA/created_at/review. Retain the first content witness and revalidate current authorities. A changed client request conflicts; changed code/policy/source cannot rewrite a prior version. Capture a fixed current check in commit_guard and recheck after return. Failed precommit binding rolls back uncommitted input/event rows; a genuinely committed intent is preserved if a later response check fails.

## Read, write and execution authority

Use the actual existing constants, without guessed scope names:

```text
READ_SCOPES = crop_result_store.READ_SCOPES
  = (farm_scenario_read, metadata, artifact, thermal_snapshot_read,
     decision_context_read, market_hold_context_read, market_source_read,
     market_candidate_read, crop_result_read)
WRITE_SCOPES = crop_result_store.WRITE_SCOPES
  = READ_SCOPES + (crop_result_write,)
PRODUCE_SCOPES = WRITE_SCOPES + (simulation_create,)
```

`submit` requires WRITE_SCOPES; `current` requires READ_SCOPES and performs reads only. `produce` requires PRODUCE_SCOPES before any numerical call or writable store/directory creation, not merely successful read resolution. Future current-result read requires READ_SCOPES without write/execute. JobStore.submit itself does not authorize this service; check every scope/current tenant/principal/runtime binding explicitly. A read-only principal missing write OR execute must cause zero numerical/CAS side effects.

Capture exact objects/provider/runtime/profile/directory/access, code/schema/profile/scopes/clock and own function identities in an immutable private program. Invoke captured guard/pointer/capture/parser implementations, passing captured encoders/identities throughout. Fresh inspection must detect class/instance replacement without invoking forged live hooks. Current principal VALUES/scopes, Farm, input, rights/source and time usability are re-read. No mutable callback/write selector can bypass the fixed production guard.

Guard before AND after each controlled numerical initialization/advance and each CAS put/root/export operation; compare the actual original resolved witness and input/component identities. Guard immediately before return. Fixed commit callbacks must remain fixed under late metadata-event mutation. Existing file inode/access/usage/hash guards remain necessary. These are operation fences, not a cross-store atomic snapshot or instantaneous revocation guarantee.

## Genuine seed production and original formats

`directory` is a separate existing absolute nonsymlink server workspace, fixed at construction and protected by ContentAccess. Derive only `<directory>/<actual_input_sha256>/carbon` and `/stem`; no request path or alternate root is accepted. Do not create writable children until full production authorization succeeds. Existing per-blob/store caps and lock/ownership policies remain unchanged.

The new owned producer owns the small original source artifact serialization/write loops, calling frozen original numerical Context/start/advance/checkpoint functions and original compute-free reader validators. Put the production guard around each controlled call and put. Do not copy equations, monkeypatch global store classes, introduce arbitrary writer callbacks or pretend the old bulk producers offer internal tenant/current hooks. A future alternative staging scheme requires a separate review. Preserve original canonical source root formats, flags, original input/program/profile bytes and numerical outputs.

The carbon/stem roots' original `code_sha256` maps describe original schema/dependency compatibility; they do NOT attest that an uncalled old bulk producer performed this execution. Record the actual NEW producer/version/code identities in the owned seed witness. A same-input oracle against the original bulk producers must show identical original numerical artifact bytes, alongside independent consumed-input/custody checks. Old-byte equivalence alone is not Farm authority.

Prepare the genuine individual Context from the actual stored individual program/numerical/profile inputs. Construct only the original initial-binding declaration's generated source anchors from the newly produced roots/selected state/Context; copy its tracking basis, original rights and reviewer from the stored request. Call the unchanged `bind_initial_stem_carbon`. Verify actual component/program/profile/initial-state/epoch/floor/ordered inventory/root/Context/proof linkage before issuing the seed. A genuine unrelated public/other-job root or Context cannot acquire this witness.

The fixed private validation seam is `producer._link(verified_input, *, context, carbon_root_sha256, stem_root_sha256, initial_binding_bytes) -> dict`: it returns only the closed seed `source` descriptor below, never a verified-seed token or publication. It uses the input's server-derived carbon/stem directories, re-resolves that actual input and performs the fixed production/current guards. Compare actual original manifest input/program/profile/selected-state and Context request/program/seed/binder identities against that exact owned packet. Capture this method's implementation identity like the other private methods. Tests can place a genuinely produced independent source in the fixed test store and call this seam to prove a semantic component/owned-input mismatch, without replacing a captured producer function or introducing a public configurable root/provider. Identical canonical inputs may have identical numerical roots; byte equivalence alone never establishes the producer's causal owned execution or issues its private verified-seed object. Only the complete guarded `produce` path issues that object.

The seed witness has exactly `schema_version='supply-material-farm-seed-witness-v1'`, `tenant_id`, `farm`, `owned_input`, `content_witness_sha256`, `resolved_witness_sha256`, `source`, `producer`, `effective_rights`, `scope='synthetic_farm_bound_initial_inputs_only'`, `profile_applicability='unvalidated_for_registered_crop'`, `ex_ante_validity='not_established'`, `recording_vs_farm_decision`, `G0_G4='not_assessed'`, `R2='not_approved'`.

`owned_input` is the original six-field actual-row descriptor. `resolved_witness_sha256` hashes the canonical detached witness. `recording_vs_farm_decision` is before_or_at/after from actual DB time and Farm decision. `source` has exactly `carbon_root_sha256`,`stem_root_sha256`,`stem_start_index`,`selected_stem_state_sha256`,`individual_context_sha256`,`individual_request_sha256`,`individual_program_sha256`,`individual_seed_sha256`,`initial_binding_sha256`. `producer` has exactly `version='supply-material-farm-seed-v1'`,`code_sha256` (actual new producer/dependency map), `original_dependency_sha256` (exact `carbon_stock` and `stem` original manifest maps). Effective rights are use/display true and redistribute false, intersected with every original source grant; never elevate redistribution. Canonical seed witness/proof outputs each stay within2MiB and original lower caps.

This seed object is not a succeeded simulation or DB publication. A late check can leave protected unreferenced CAS files written before the failure; suppress the result and record/clean owned temporary resources without claiming SQL rollback deleted files or all failures made zero writes. Never remove old accepted blobs. No input/result API or automatic worker is installed by this step.

## Actual acceptance and required continuation

Independent tests must establish an actual current Farm and newly authored compatible synthetic source inputs before the feature's module-missing RED. Actual SCRAM GREEN must prove immutable intent/current first-row facts, hard64KiB request+whole-input sizing, genuine new carbon/stem/individual seed and original binder linkage, same-input original-byte oracle, and semantic rejection of a genuinely unrelated public/other-job root/Context. Positive publication must not be faked. Exercise exact scopes, read/no-side-effect behavior, current tenant/rights/input cancellation, future/naive/reversed times, altered raw/hash/unit/basis, code/profile/directory/function identity, late numeric/CAS/commit drift, concurrent retry/conflict/rollback and cleanup. Counts come from actual collection and terminal evidence. Focused inherited authority/initial-binder regressions follow the actual touched call sites; no guessed or historical fresh count.

Completion of this input/initial-seed prerequisite does not complete full material custody. The static material parameter/event-parent plan must next be frozen; runtime Context/cursor/pending/candidate/event anchors must come from the genuine execution, with static declaration SHA and compiled original-point-input SHA retained. Genuine full forcing/material lineage then needs the original complete closure/root, existing simulation lease/CAS terminal publication and fresh current no-replay query. Publication ID/time must come from real committed records; precommit rollback and postcommit response suppression remain distinct.

Separately associate original schema4 cost input/job/trace/first publication and independent resource-period declarations to the SAME exact Farm/version/context; do not alter legacy FarmInputs.economic or prorate original amounts. Both links remain prerequisites for combined admission/current query, protected HTTP/runtime, strict SDK, same-selection3D/table/graph and actual browser acceptance. No Farm crop validity, resource purchase, margin/ranking, independent domestic data, G0–G4 or R2 approval follows. Whole product goal remains incomplete.
