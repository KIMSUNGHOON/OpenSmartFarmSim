# Stored repeated-material artifact v1

**Status: IMPLEMENTED — bounded local software acceptance.** The increment is the two additive modules `backend/app/crop_supply_material_repeat_artifact_producer.py`, `backend/app/crop_supply_material_repeat_artifact_reader.py` and one focused test file `backend/tests/test_crop_supply_material_repeat_artifact.py`. Old artifact families, numerical modules, source fixtures and inputs remain preserved. The [local software record](../research/supply-material-repeat-artifact-20261107.md) distinguishes actual split finite-guard execution, the default monolithic fixture command and hosted CI. Strict client, lawful delivery and same-selection realistic 3D remain required product work; no SDK/UI, Farm, whole-season or G0–G4/R2 acceptance follows.

The historical design checkpoint is phased numerical JOIN `a6ecc592…`, repeat code `8bc372… / ad42ce… / 5eecc2…`, QA63 and numerical-contract snapshot `3eaabd…`. The numerical generation checkpoint underlying this proposal is repeat code `7c51dabd… / 100433a7… / 5eecc2cf…`, QA `63aa0b92…`, [numerical contract](supply-material-repeat-numerical-v1.md) snapshot `e8012aba…` and phased JOIN `a72eb5b2…`. These are distinct immutable software-replay references; neither JOIN is a passed monolithic numerical test or approval of this artifact.

Numerical-parent local software acceptance is recorded at checkpoint `0e5927819d3a343da2449cd4bfa7ec0c28a5dc96` ([acceptance evidence](../research/supply-material-repeat-numerical-20261107.md)). The actual local owner decision is `bounded-numerical-software-5f6752bbe4d341c0`, with operator-held receipt SHA256 `34837dc011c41730e54df581dfcba4831fb6efd8b2c800988e296ce6a1e458e6`. The historical numerical generation contract remains `e8012abac1ad455224751b3e6f774af930c4a9b4fe22b350f7052617704353d8`; the current accepted-status contract is `53667b0ae19ef8b50f8f691902473ae59fda68b86235c98e8917662c33d0c9de` and differs only at status line3. Artifact local acceptance is limited to the actual source-bound cases and preservation recorded in the linked artifact report. Its generation contract `ff6061dc…` and generation QA `91b157a3…` remain immutable history; a later status-only contract and append-only live QA do not relabel or regenerate the artifact. Default monolithic/hosted whole-suite and wider product acceptance remain separate. G0–G4 are not assessed; R2 is not approved.

## 1. Python ABI and authority boundary

The following names/signatures are fixed for the first TDD slice:

```text
producer.produce_repeat_material_artifact(directory, access, *, handle) -> str
reader.read_repeat_material_manifest(directory, access, root_sha256) -> bytes
reader.read_repeat_material_frame(directory, access, root_sha256, *, index) -> bytes
reader.RepeatArtifactHold(ValueError)
```

`directory` is an absolute, operator-fixed owned artifact directory, and `access` is an exact existing `ContentAccess`. The producer requires an exact genuine current `crop_supply_material_repeat_owner.Handle`, its original token and actual workspace; it rejects a legacy Handle, proxy, reconstructed tuple, supplied callback/program or merely equal raw bytes. Returned root is a lowercase SHA256 of the actual published canonical root bytes. Reader returns the original canonical manifest/frame bytes after complete validation, including a final fence before exposing the buffer. `root_sha256` must be a canonical digest and `index` a strict integer, never bool, in the actual frame range. There is no arbitrary source selector or path inside a request.

Use the corrected source-session-v2 same-real-class acquisition and direct captured OS cleanup policy, with fresh code/function/rights/file checks, rather than old mutable `self.close` context cleanup. Normal and partial-error acquisition, controlled puts, late failure and cleanup must not invoke a rejected function/property/code replacement. This inherits the parent boundary; it does not authorize changing its code. Producer requires writer permission before the first effect. Output directory must be physically distinct from every selected input archive, including ancestor/descendant and symlink aliases. Every source input stays immutable.

A reader performs stored source/quantity/proof validation only. No live RHS/stage evaluation, numerical candidate/point generation, new authoritative adoption, schedule consumption, growth curve evaluation, source collection, DB access, CLI/process launch or CAS write is permitted. The parent’s original saved-stage algebra, exact rational bookkeeping and stored clock composition are permitted with actual source-bound observations. Their calls are distinguished from live numerical generation. Nothing here claims current Farm/account/registry authority from static files.

## 2. Exact notation and bounded wire primitives

Every object below has **exactly** the listed keys. All keys are required; no unknown fields or implicit defaults/coercions. Union tags select exactly one variant. Arrays preserve the specified source order. JSON rejects duplicate keys, nonfinite values and non-UTF-8; canonical bytes use the existing original JSON encoder (`sort_keys=True`, compact separators, `ensure_ascii=False`, finite original binary64 values). Reading and canonical re-encoding must give the same bytes for new JSON documents. Original source/NOTICE bytes retain their original formats unchanged.

- `H`: exactly 64 lowercase hexadecimal characters; SHA256 is over actual complete bytes, never a logical alias.
- `I[a,b]`: `type(value) is int`, inclusive bounds; `B`: exact bool; `Null`: literal JSON null.
- `Ref`: closed `{sha256:H, bytes:I[1,2097152]}`. `OriginalRef` has the same two keys with bytes up to 16777216, solely for original-group blobs already permitted by the unchanged original reader. Original root, NOTICE, all new documents and other groups use `Ref`.
- `Exact[u]`: closed `{numerator:string,denominator:string,unit:u}`. Integer strings are canonical reduced rational numerator/strictly positive denominator, at most 4096 characters each; no plus, leading zeros, negative zero or unreduced fraction. The unit is exact, nonempty and at most 64 characters. A parameter `u` is bound to the original validated source unit, not client-selected conversion.
- `Quantity[u]`: closed `{value:finite binary64,unit:u}`. Geometry/carbon/represented ages are nonnegative; floor area is positive. Preserve the source binary64 value; no decimal rounding, floor/density conversion or scaling.
- `At`: closed `{time_origin_utc:aware RFC3339 string,elapsed_seconds_exact:Exact['s']}`. Copy the original origin string, validate with the existing original UTC parser, and compare exact elapsed fractions. No datetime rounding or new observation/publication timestamp is inserted.
- `Rights`: closed `{use:B,display:B,redistribute:B}`. It equals the AND of **all** selected original/plan/material/repeat source grants, including every consumed successor declaration; require use and display true for this replay artifact. A false redistribution bit stays false.
- `SourceObject(P)`: a dependent closed type: the complete JSON subobject at the **fixed path P listed below** in an independently schema-, source- and hash-validated immutable parent record. It must be canonically byte-equal, including every nested key, type, order of arrays and unit. The expectation comes from the selected source closure, never from the frame being checked. This is not arbitrary JSON or permission to omit the parent validator. No caller-specified JSON pointer is accepted.

Limits are 2097152 bytes per new replay document; 67108864 total physical bytes, including the root and distinct referenced blobs; at most 4096 physical CAS files, 512 projected frames and 32768 total sampled state scalars. Existing parent numerical call/work/publication limits, original source bounds and writer temporary-file reservation rules remain unchanged. These are hard bounds, not measured fit. Exceeding a bound holds; it never drops a source record or frame. No new arbitrary deadline or relaxed numerical cap is introduced. Each controlled parent operation retains its original deadline; a focused test phase remains under the root’s existing finite guard.

Producer orchestration policy `completed-parent-verified-transfer-v1` captures one absolute maximum600-second artifact deadline at API entry; it covers acquisition, validation, transport, all cleanup and the final check before return. This explicit artifact envelope uses the existing finite-phase ceiling and does not replace or extend any numerical deadline. One genuine parent validation/build operation, including every normal context-exit fence and cleanup, must complete under its unchanged single maximum60-second meter before publication. A failed or expired validation cannot create the private verified transfer bundle or enter transport; no per-event, per-frame, per-batch or retry meter renewal is allowed. Only after all parent contexts close successfully may the producer retain the complete call-local immutable raw input read set and derived output buffers. It then reacquires the same five real source directories with unchanged access policies, read/write flags and locks. That is a new artifact-only transfer session, not a continued numerical session or a claim that the old owner factory/check executes during transfer. Before and after every controlled put and around root publication, current real-FD file/directory identities and full selected input bytes, code/loaded dispatch, actual source/output policies, effective rights and genuine input Handle/workspace bindings must agree with the successful validation. The bundle alone is never authority; points/frames remain derived output buffers rather than nonexistent source files. Transfer executes no numerical evaluator, proof replay, candidate/point generation, adoption or parent lifetime charge. Existing preflight, root-last and allowed-orphan rules remain. After closing every transfer/output FD, check the same artifact deadline and fixed code/Handle/workspace/policy bindings again before returning the root. Reader validation keeps its existing single parent60-second operation; no reader deadline or public ABI/payload change is introduced here.

## 3. Root, source and selected physical closure

`Root` has these exact keys:

| Key | Type/value |
|---|---|
| schema_version | `supply-material-repeat-artifact-v1` |
| scope | `software_research_only` |
| G0_G4 | `not_assessed` |
| R2 | `not_approved` |
| time_kind | `synthetic_model_clock_not_observation` |
| claim_scope | `stored_synthetic_repeat_material_window_only` |
| code_sha256 | exact fixed component map described below |
| source | `Source` |
| blob_groups | `Groups` |
| transitions | chronological `Transition[]`, 1..256 entries |
| frames | ordered `FrameDescriptor[]`, 2..512 entries |
| effective_rights | `Rights` |
| window | `Window` |
| terminal | `Terminal` |
| notice | `Ref`, identical to original root `root_inputs.license_notice` |

`code_sha256` is a closed map with exactly the finite key set K: the current pinned `crop_supply_material_artifact_reader.SOURCE_PATHS`, union the three repeat numerical module paths, `backend/app/job_store.py` and the two new artifact module paths. Values are actual file SHA256s; duplicate paths collapse once. K is fixed by this version and its pinned source tuple, not by a request or artifact. Loaded function/code identities must match those files at every required fence. Code hashes identify the actual new producer/reader and source validators; never claim the unchanged old bulk artifact producer executed. New file hashes are established by actual implementation, not invented in this proposal.

`Raw3` is closed `{cursor:Ref,current:Ref,basis:Ref}`. `LegacySelection` is closed `{definition:Ref,cursor:Ref}`. `Source` is closed:

```text
{owner_version:'supply-material-repeat-owner-research-v1', definition:Ref,
 anchor:Raw3, final:Raw3, original_root:Ref, original_frame_index:I[0,511],
 base:LegacySelection, forcing:LegacySelection, material:LegacySelection}
```

`anchor` is the actual repeat source-anchor cursor/current/basis; it is context, not an emitted crop frame. `final` is the producer Handle’s exact raw3. All cursors use the same source.definition. The original/base/forcing/material links must be those reached through that definition’s actual bridge, with full original source closure and unchanged profiles/NOTICE. Their raw records keep the original schemas/versions. No Farm, floor, timestamp, policy or source root is relabelled.

`Groups` has exactly seven keys: `original,base,forcing,material,repeat,points,frames`. Values are unique digest-sorted arrays of descriptors. `original` uses `OriginalRef[]`; the other six use `Ref[]`. The four source groups and repeat are nonempty. `points` contains the complete canonical public receipt of every selected repeat material adoption; `frames` contains every actual projected frame blob. Both are nonempty because this version requires at least one committed repeat material adoption. Source-only anchors, pending pages and uncommitted/orphan successors produce no frame.

Every advertised digest has real bytes under the existing digest filename. Source groups contain the exact records visited by the unchanged original/base/forcing/material validation and repeat ancestry validation, including physical witnesses, origins, material-before/after frame records and required pending evidence. No unrelated siblings or uncommitted orphans are added. Reader proves exact equality of selected and used descriptor sets in each group. A digest may occur in two groups only when the validated graph actually uses the **same physical bytes** in both roles; count total bytes/files once. Duplicate descriptors inside a group, a missing reference or unequal lengths hold.

The points group has actual full receipt bytes under their full public receipt SHA. A physical witness digest, full public receipt digest, inner calculation digest and candidate calculation digest remain distinct identities; none is a file alias for another. The frame group contains actual canonical projected-frame bytes, unlike a digest computed for an unpersisted response. Manifest is not listed in its own closure. Root SHA and projected frame SHA have no self-reference: neither payload contains its own SHA or artifact-root SHA.

`Window` is closed `{first_at:At,last_at:At,covers_whole_season:false,selection:'committed_repeat_material_and_confirmed_remainder'}`; endpoints equal first/last selected frames. `Terminal` is closed `{status:'completed'|'confirmed_prefix',hold:Null,scope:'declared_synthetic_forcing_plan_only'}`; completed requires actual final `declared_end`, otherwise confirmed_prefix. It does not convert a partial window into a whole-season claim.

## 4. Exact transitions and descriptor variants

Each transition has the following common exact keys: `index:I[0,255], kind, previous_cursor_sha256:H, cursor:Ref, history_page:Ref, before_current:Ref, after_current:Ref, before_basis:Ref, after_basis:Ref, frame_indices`. Its cursor’s previous/page/current/basis fields must match those physical records; consecutive transitions join byte-exactly, starting at anchor and ending at final. The finite variants add only the fields below:

| kind | frame_indices | Additional key(s) and predicate |
|---|---|---|
| `interval` | exactly `[i]` | none; before/after basis equal; copied after-current phase is `original_grid_endpoint`, `forcing_before` or `declared_end` |
| `forcing_switch` | exactly `[i]` | none; same basis; after phase `forcing_after`; actual predecessor’s phase is `forcing_before` at identical At |
| `material_adoption` | exactly `[i,i+1]` | `point:PointEvidence`; phases material_before then material_after at the exact same At; active before/after bases may differ and both are validated |

`PointEvidence` is closed `{witness:Ref,receipt:Ref,calculation_sha256:H,candidate_calculation_sha256:H,before_frame:Ref,after_frame:Ref}`. Witness is the actual history `point_witness_sha256`; receipt’s actual full SHA is history `point_sha256`. The other hashes bind the exact receipt’s `calculation_sha256` and candidate’s calculation identity according to the parent schema. Both original six-key stored material frame records must match the receipt and page, not a re-generated numerical state. A receipt reconstructed from its witness must be whole-byte equal to the points blob, with zero live RHS; selected-stock equality is insufficient.

`FrameDescriptor` is closed `{index:I[0,511],transition_index:I[0,255],phase:Phase,at:At,active_basis_sha256:H,frame:Ref,state_scalars:I[1,32768]}`. `Phase` is exactly `material_before|material_after|original_grid_endpoint|forcing_before|forcing_after|declared_end`. Values match its actual frame blob. Indices are contiguous and exactly covered by transition.frame_indices; frame count equals two per material adoption plus one per other transition. No lifetime frame-counter substitution. Identity is `(history_page.sha256, side)` where side is before/after for adoption and after otherwise; index is its preserved history order, not a time sort.

## 5. Exact projected frame and binding variants

`Frame` has these exact keys:

```text
{schema_version:'supply-material-repeat-replay-frame-v1',
 scope:'software_research_only',G0_G4:'not_assessed',R2:'not_approved',
 time_kind:'synthetic_model_clock_not_observation',
 claim_scope:'stored_synthetic_repeat_material_window_only',
 index:I[0,511],phase:Phase,at:At,binding:Binding,snapshot:Snapshot,
 model_floor_area:Quantity['m2_floor'],state_layout:SourceObject(ActiveSeed.state_layout),
 leaves:LeafRow[],internodes:InternodeRow[],accounts:Accounts}
```

`ActiveSeed` is `active_basis.numeric_basis.seed`, with that basis obtained through this frame’s verified transition and binding. `Snapshot` is closed `{at:At,state:finite-binary64[],derived:SourceObject(SnapshotSource.derived)}`. Entire snapshot is canonical byte-equal to the selected material-frame state/derived/at or actual confirmed numeric.last_confirmed. Preserve finite state coordinates, including signed climate coordinates; only the named organ metric coordinates have nonnegative constraints.

`Binding` has common exact keys `kind,transition_index:I[0,255],history_page_sha256:H,transition_cursor_sha256:H,active_basis_sha256:H,context_cursor_sha256:H,checkpoint_cursor_sha256,source`. Variants are:

| kind / phase | checkpoint_cursor_sha256 | source exact keys | Required source/basis |
|---|---|---|---|
| `dense_material_before` / material_before | Null | `{receipt:Ref,witness:Ref,material_frame:Ref}` | page.before_basis; source points to actual before_frame; receipt.point_data.before_dense supplies state/derived. context is page.previous_cursor; it is **not** a dense-time checkpoint. |
| `adopted_material_after` / material_after | transition cursor H | `{current:Ref,receipt:Ref,witness:Ref,material_frame:Ref}` | page.after_basis and after-current; actual after_frame equals receipt.point_data after state/derived and confirmed current. context remains page.previous_cursor. |
| `confirmed_current` / other four phases | transition cursor H | `{current:Ref}` | page.after_basis and after-current numeric.last_confirmed; context is page.previous_cursor. |

No source-variant field is optional. A dense checkpoint H, confirmed null checkpoint, before state in after basis, wrong cursor/page or wrong material-frame digest holds even if its own content hash was recomputed.

`Accounts` is closed `{event_sequence:parent-validated nonnegative exact int,schedule:SourceObject(ScheduleSource),global_ledgers:LedgerMap,local_ledgers:LedgerMap,point_totals_exact:ExactMap,lifetime_transfers_exact:ExactMap,transfer_origins:Origins}`. `Origins` is closed `{physical:H,geometry:H}`, with real selected origin records. `LedgerMap` is a dependent closed map: exact key inventory and units of the selected source ledger and ActiveSeed; each row is closed `{residual_exact:Exact[u],budget_exact:Exact[u]}`, budget nonnegative and abs(residual) <= budget. `ExactMap` is a dependent closed map with the exact key inventory/units of its validated source and `Exact[u]` rows. No arbitrary ledger name or changed unit is admitted.

The following paths are normative and complete; `P` is that adoption’s full receipt.point_data, `N` is after-current.numeric:

| Value | dense_material_before | adopted_material_after / confirmed_current |
|---|---|---|
| SnapshotSource | `{at:P.at,state:P.before_dense.state,derived:P.before_dense.derived}` | N.last_confirmed |
| event_sequence | P.before_dense.event_sequence | N.event_sequence |
| ScheduleSource | P.source_schedule with **only** age_exact replaced by P.before_dense.shoot_age_exact | N.schedule |
| global_ledgers | P.before_dense.pending_global_ledgers | N.global_ledgers |
| local_ledgers | P.before_dense.local_ledgers | N.branch_ledgers |
| point_totals_exact | P.before_dense.point_totals_exact | N.point_totals_exact |
| lifetime_transfers_exact | P.before_dense.pending_lifetime_transfers_exact | N.lifetime_transfers_exact |
| transfer_origins | P.before_dense.transfer_origins | N.transfer_origins |

Each copied field is SourceObject equality to this table, after the independent parent’s closed schema and ledger/books validation. In particular, dense-before has the pre-event schedule and accounts; it cannot acquire the later consumed sequence or post-point totals. Original source arrays remain available byte-exactly in closure.

## 6. Organ rows, metric coordinates and diagnostic union

`LeafRow` and `InternodeRow` have the same exact keys: `id,parent_internode_id,source_index,geometry,carbon,represented_age,clock_exact,birth,geometry_origin,metadata,geometry_diagnostics`. ID and parent use the existing original bounded `_id` grammar. source_index is strict integer 0..511. Leaves are the exact ordered ActiveSeed.organs.leaves, matching ActiveSeed.program.leaves; internodes are exact ordered ActiveSeed.organs.internodes. Each parent is the declared parent ID or original null, and every nonnull parent is a present internode. Preserve zero-sized and explicitly unbound organs. No guessed attachment is inserted.

`birth`, `geometry_origin`, `metadata` are dependent closed SourceObjects at ActiveSeed.organs.[leaves|internodes][source_index].baseline, ActiveSeed.geometry_baselines.[leaves|internodes][source_index], and the whole corresponding organ row. They must be copied exactly. `model_floor_area` is ActiveSeed.program.model_floor_area, positive and unchanged. `clock_exact` is Exact['degC_day'] from the existing versioned original stored birth-relative clock arithmetic using this frame’s At, baseline and selected lifetime indoor_air_temperature_time; no new temperature or growth coefficient. All original clock inputs are retained in the source closure.

Let n be the active leaf count, m the active stem/root-compartment count, h the active internode count, and z=106+3n+m. Exact state length is z+2h. Original layout’s ordered leaf/compartment/internode IDs must agree with ActiveSeed. For leaf i, area/state[106+n+i] uses m2, carbon/state[106+2n+i] uses mg_CH2O/m2_floor, represented age/state[106+i] uses degC_day. For internode i, length/state[z+h+i] uses m, represented age/state[z+i] uses degC_day, and carbon/state[106+3n+j] uses mg_CH2O/m2_floor where j is that exact ID’s index in program.stem_root_compartments. These values are copied as Quantity. **Never use final-basis offsets for an earlier frame.**

`geometry_diagnostics` is the following exact two-variant union, with u=m2 for leaves, m for internodes:

```text
{kind:'stored_confirmed',canonical_status:'stored',
 potential_exact:Exact[u],realized_exact:Exact[u],deficit_exact:Exact[u],
 lifetime_potential_exact:Exact[u],lifetime_realized_exact:Exact[u],
 lifetime_deficit_exact:Exact[u],canonical_gap_exact:Exact[u],
 canonical_potential_difference_exact:Exact[u]}

{kind:'dense_stored_transfers',canonical_status:'not_stored_at_dense_boundary',
 potential_exact:Exact[u],realized_exact:Exact[u],deficit_exact:Exact[u],
 lifetime_potential_exact:Exact[u],lifetime_realized_exact:Exact[u],
 lifetime_deficit_exact:Exact[u],canonical_gap_exact:Null,
 canonical_potential_difference_exact:Null}
```

Confirmed frames copy the actual N.geometry_diagnostics leaf_i/internode_i eight fields. Dense-before copies potential and realized from P.before_dense.pending_branch_transfers_exact[kind_i_potential/realized], and lifetime potential/realized from pending_lifetime_transfers_exact with those same keys. Its two deficit fields are **only** their versioned exact rational differences, with potential >= realized >= 0. Confirmed deficit fields also equal their actual potential-minus-realized; canonical gaps can be signed. No growth/area/length curve is evaluated to populate the dense nulls, and no prior confirmed diagnostics are presented as current. Wrong tag/status, nonnull dense canonical field, null confirmed field, missing/extra diagnostic key or wrong geometry unit holds.

## 7. Ordering, source fences and publication/read behavior

Walk the real acyclic repeat ancestry chronologically. Anchor emits zero frames. Every committed repeat page is included; each material page adds its same-At before/after pair in that order, an interval adds its confirmed frame, and a forcing switch adds forcing_after once. Do not deduplicate by UTC, sort phases lexically, interpolate geometry or append an unconfirmed right endpoint. Same-At forcing_before/after must be actual adjacent confirmed records with the same active basis and unchanged stock vector, geometry, schedule and required source books; forcing-derived values may change. Material adoption checks use their own before/after bases and exact source receipt, not forcing continuity rules.

Use original strict validators and saved algebra to verify the complete chain, canonical full receipt reconstruction, exact origins/once-only events/books and ordered per-basis inventory.

Stored-only proof policy (`saved-source-curve-observations-v1`): the artifact reader uses versioned reader-local adaptations of the original stored-chain and point validators. It preserves their closed schemas, source/history/basis/once-only links, full saved-stage RK4/root/point arithmetic, transfer integration, physical/local/global ledgers, construction/funding/heat, exact clocks, rights and byte/hash checks. The adapted validators do not claim that the unchanged whole numerical `_restore`, point `verify`, or leaf initializer executed. The genuine producer's completed parent validation still executes its original numerical validators and retains the original 60-second limit; publication and all other limits remain unchanged.

Exactly two kinds of retained values are curve observations rather than independently re-evaluated curve equations: (1) confirmed `canonical_gap_exact` and `canonical_potential_difference_exact` in each original numeric geometry diagnostic; (2) the canonical area in an actual new leaf's initialization receipt already contained in the selected complete material point. For (1), require the original closed eight-field diagnostic shape/units, independently recompute its first six transfer/deficit fields, and retain the final two fields byte-exactly from the selected source current. For (2), validate the complete initialization envelope, the original closed curve declaration, parameter units/finite-positive bounds and normalized declaration/hash, leaf identity, exact zero age, finite positive bounded area, requested-to-canonical `isclose` rule (`rel_tol=1e-12`, `abs_tol=0`), and original receipt hash; use that observation in the unchanged seed compatibility, point funding/heat/core and point-books arithmetic. Require complete reconstructed point bytes and all full-receipt/inner/candidate/witness identities to match their actual physical records. These checks do not independently prove curve(age)=geometry or curve(0)=the saved initial area, and do not rerun the original curve normalizer's internally evaluated growth-rate representability test. The genuine producer's original parent validation still performs those curve/normalizer checks; their source declarations and code identities remain retained. No additional observation is inferred, no curve is evaluated, and no source observation alone grants authority. Dense-boundary canonical nulls and every existing wire schema/tag remain unchanged.
 Existing old reader one-basis checks remain unchanged for its old family. Re-read selected blob hashes/metadata and fixed code identities, file policies and actual effective rights at required entry/final fences. A final rights/code/source/storage mismatch suppresses output bytes/root. Artifact reader authority is its operator-fixed access and selected immutable closure; no current DB or Farm revocation guarantee is invented.

Producer validates and preflights the entire selected output closure before controlled writes, then checks current source/rights/code and output access before each controlled put and before/after root publication. Publish the root last. If late failure follows an earlier successful immutable put, already-written blobs or an unpublished root may remain as explicit orphans; no cross-directory atomicity or rollback is claimed. Return no root on that failure. Partial initialization/unwind closes its actual FDs by the corrected captured OS policy, never a rejected callback. Successful reader is read-only and returns no stale buffer after its final fence.

The current reference’s grants are use=true/display=true/redistribute=false. Private artifact tests do not grant public export. Existing all-three-rights public exporter must continue holding. A later separately authored own public revision, or a genuinely authorized protected display route with proved current checks, is a separate review/implementation decision. No input/NOTICE is changed, no availability is backdated and no ex-post synthetic replay becomes ex-ante farm evidence.

## 8. Focused TDD and acceptance before the next layer

The first missing-API test prepares genuine trusted original material and a newly issued current repeat Handle using real existing producer/public APIs, verifies the actual parent baseline and then lazily imports this artifact API. A fixture/parent failure is not feature RED. Current actual JOIN is evidence for the design, not a fake Handle or reusable runtime token.

The focused test file must establish: full/split deterministic actual artifact roots and every selected raw3/source/NOTICE byte; physical witness/full public receipt/inner/candidate separation; real persisted projected blobs; matching-basis dimensions/IDs/parents/coordinate units and exact copied accounts/clocks; both actual material pairs, interval/remainder and forcing pair; dense null checkpoint/diagnostic tags versus real confirmed diagnostics. Actual measured document/total bytes/frame/scalar counts must fit unchanged bounds.

Independent standalone stored read must exercise all frame variants with raw equality and observed zero live RHS/new candidate/new point/adoption/CAS writes/DB/process/outbound/curve evaluation, allowing the precise saved algebra. Meaningful rehashed wrong-basis/phase/order/parent/unit/dimension/source/unknown-key/tag/null faults and code/rights/storage/late-publication/capacity/cleanup faults must hold without stale output; immutable input/FD checks and allowed orphan semantics remain explicit. A blanket always-hold implementation does not satisfy positive production/read acceptance. All newly authored test outputs are synthetic software evidence only.

The V1 broad 3D direction remains a dependency map, not an extra implementation allowance. After this artifact-only increment, freeze and test the strict SDK/common metric geometry decoder, lawful delivery and same selected realistic renderer/table/graph in a separate small slice. Full Farm custody, schema4 cost binding, production current query and end-user deployment remain required. No SDK/browser/gates or whole-goal completion follows from this private ABI candidate.
