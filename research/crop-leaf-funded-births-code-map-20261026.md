# Funded leaf appearance: current-code map at 394695a1

Read-only source-code/specification evidence for the parent researcher. No agricultural/model-selection/architecture recommendation, data/coefficients adoption, or gate decision is made here. No external source was browsed, Codex subprocess launched, tests/builds/services run, application code edited, or commit/push performed. The parent’s actual native CLI/model proof is not this background agent’s proof; the parent must record its own invocation/output for substantive judgments.

Snapshot: `394695a1c670a9edf07b26dbe91c46628346238e`. Parent independently verified all60 source hashes before edits on2026-10-26 KST. Parent research/design uses the native gpt-6.1-sol/xhigh session; see [decision](crop-leaf-funded-births-design-20261026.md). References are repository-relative `file:line` references; ranges denote inspected implementation. Full-file hashes at the end bind the evidence capture. Navigation-only search hits are not evidence.

## 1. Scope and current acceptance

README states the first target is one Korean location, greenhouse zone, cherry-tomato cultivar/cycle and the development order is crop calculation → immutable result/same-time growth 3D → production/resources/economics (`README.md:758–769`). Gates are separate (`docs/PROJECT_SPEC.md:752–764`). The documented stack remains small deterministic Python modules and standard-library RK4 (`docs/TECH_STACK.md:58–66`). Source/immutable-version and same-time replay contracts are separate from runtime judgment (`docs/ARCHITECTURE.md:39–41`, `182–195`; `AGENTS.md:14–21`).

Current task records already accept individual-stock RHS, Ci/a/A integration/continuation, immutable storage, export, strict SDK and 3D software/preview in their synthetic software scopes (`tasks/todo.md:144–156`; `tasks/plan.md:25–34`; `docs/RESEARCH_BASELINE.md:3–11`). Actual visible-window/R2 and main-app whole-bundle resource holds remain separate. The historical 2026-10-24 observation that individual Ci was missing is not a current missing feature.

`leaf-carbon-funded-births` remains unchecked and names initial C source/buffer debit/growth respiration, capacity/incoming sensible heat, original clocks/attachment, empty/simultaneous/duplicate births/removals (`tasks/todo.md:157`). The dependency plan labels this parallel research, not a new prerequisite for accepted current-state storage/replay (`tasks/plan.md:28–34`). These are repository status statements, not independently rerun acceptance evidence.

## 2. Current Ci/a/A program, state and units

Owner: `backend/app/crop_leaf_carbon_stock_dynamics.py`. Public calls are `evaluate_rhs(*,program,**profiles)` and `integrate(*,program,step_seconds,step_count,**profiles)` (`:143–194`). `_prepare` accepts only top-level fields below (`:43–64`):

```text
input_id, origin, normalization, thermal_age_policy, capacity_policy,
leaf_stock_policy, scenario, leaves, model_floor_area, capacity_outflow
```

Explicit policies are `zero_lower_asymptote_sigmoid_v1`, `dynamic_indoor_air_no_clip_v1`, `declared_outflow_plus_area_capacity_derivative_v1`, `leaf-stocks-uniform-maintenance-explicit-removal-v1` (`backend/app/crop_growing_geometry_climate.py:18–22`; stock dynamics `:17–19`, `46–47`; independent reader declaration `backend/app/crop_leaf_carbon_stock_artifact_reader.py:36–39`).

Fixed 1–512 leaves each have exactly `leaf_id,curve,thermal_age,base_temperature,initial_area,initial_carbon,sink_weight,carbon_removal`. Initial C is `mg_CH2O/m2_floor`, weight `1`, removal `mg_CH2O/m2_floor/s` (`stock dynamics:19`, `48–63`). These are same-footprint stocks, not absolute per-leaf mg. Scenario input excludes aggregate `plant_state.leaf` and `removals.leaf`; preparation makes temporary aggregate adapters from explicit rows and removes them from normalized program (`:49–62`). Original IDs/order are retained; duplicates are rejected by inherited preparation (`backend/app/crop_growing_geometry_climate.py:54–69`).

The vector layout follows `_prepare/_project/_evaluate/_layout` (`stock dynamics:63–95`, `129–133`):

| Index | State | Unit |
| --- | --- | --- |
| 0 | buffer | mg_CH2O/m2_floor |
| 1 | stem_root | mg_CH2O/m2_floor |
| 2 | temperature_filtered_24h | degC |
| 3 | temperature_sum | degC_day |
| 4–53 | fruit_carbohydrate[50] | mg_CH2O/m2_floor |
| 54–103 | fruit_number[50] | fruits_equivalent/m2_floor |
| 104 | canopy_sensible_energy | J/m2_floor |
| 105 | air_temperature | degC |
| 106 | air_vapor_mass | kg_water/m2_floor |
| 107+i (0≤i<n) | thermal_age[i] | degC_day |
| 107+n+i | area[i] | m2 |
| 107+2n+i | carbon[i] | mg_CH2O/m2_floor |

Aggregate leaf C is a once-rounded exact sum of current Ci, projected temporarily for the inherited pure helpers, never an independently integrated state (`stock dynamics:67–69`; `backend/app/crop_leaf_carbon_stock_rhs.py:37`, `67–69`). N in the fruit block means fruit number, not nitrogen.

At each stage, stock dynamics `:75–95` does the following:

- Requires `a_i≥0`, `0<A_i≤Amax_i`, and current indoor air≥leaf base temperature; below-base air holds without clipping.
- Computes `a_i'=(Ta−Tbase_i)/86400` and `A_i'=F_i'(a_i)*a_i'`. The rate reads curve/age, not C supply (`:79–82`; rate units/calculation `backend/app/crop_leaf_expansion.py:13–15`, `27–70`).
- Forms `LAI=sum(current A_i)/floor`, `Ldot=sum(A_i')/floor`, `g_in=g_out+k*Ldot` (`:83–88`).
- Calls individual-stock RHS once with current Ci, original IDs, explicit weights/removal rates (`:89–95`).

Bounds: 2 MiB input/output; positive dt, 1–4096 steps, ≤600 s; `(N+1)*(107+3n+2n+8)≤32768`; shared-stage fixed RK4 with `4N+1` successful evaluations. Failure records failed step/stage and last confirmed sample/transfers/residuals/budgets (`stock dynamics:21`, `153–194`). No topology-changing operation appears in these public calls/closed fields.

## 3. Buffer, growth cost, allocation, stock and continuous ledgers

The actual downstream implementation is stock RHS → partition joint RHS → explicit-LAI joint RHS → `crop_explicit_lai_carbon_cohorts` (`backend/app/crop_leaf_carbon_stock_rhs.py:10`, `69–76`; `backend/app/crop_leaf_partition_climate_rhs.py:8–9`, `55–70`; `backend/app/crop_explicit_lai_climate_rhs.py:9`, `109–116`).

`crop_explicit_lai_carbon_cohorts._non_optical` calculates requested allocations from current buffer and pinned profile factors; leaf/stem maintenance is linear in represented organ C (`backend/app/crop_explicit_lai_carbon_cohorts.py:41–58`). Requested growth respiration sums profile cost×requested allocation. Buffer base derivative is photosynthesis minus requested structural allocation and requested growth respiration, followed by existing fruit-startup refund; realized total growth cost retains leaf/stem profile terms and realized fruit cost (`:101–112`). Pinned `ReferenceParameters` rejects unreviewed profile bytes by fixed SHA (`backend/app/crop_growth_rates.py:16–25`, `37–55`). No coefficient is chosen or reproduced here.

Leaf partition policy `explicit-relative-leaf-sinks-and-empty-deferral-v1` interprets explicit weights as relative priorities. It still requires a 1–512-row list. “Empty” means total sink weight zero; this is not a zero-leaf canopy. Positive weights share the requested leaf growth. At total weight zero it realizes no leaf growth and refunds deferred structural leaf growth plus avoided `cLeafG` respiration to the buffer derivative (`backend/app/crop_leaf_carbon_partition.py:13–16`, `67–105`). It does not advance stock or create a leaf. Partition joint RHS changes buffer/aggregate-leaf derivative and total growth respiration, preserves source result/hashes and checks whole-C/leaf balances (`backend/app/crop_leaf_partition_climate_rhs.py:68–99`).

Individual-stock RHS requires complete unique ordered 1–512 leaf IDs and positive aggregate Ci. Rows contain explicit current C, weight and continuous removal; individual zero Ci is allowed (`backend/app/crop_leaf_carbon_stock_rhs.py:48–69`). It allocates original total maintenance as `M_i=M*C_i/(exact sum Ci)` under the explicit common mass-specific policy, then `Ci'=g_i−M_i−R_i`; outward final derivative at Ci=0 holds (`:76–85`). Actual rounded per-leaf sums, aggregate discrepancies, and whole-C/leaf budgets are returned (`:86–116`).

The inherited 21 integrated quantities, in order, are photosynthesis, growth_respiration, maintenance_leaf, maintenance_stem, maintenance_fruit, removal_leaf, removal_stem, terminal_carbon, entry_number, terminal_number, sensible, latent, incoming_heat, outgoing_heat, canopy_external, air_external, vapor, external_vapor, capacity_in, capacity_out, indoor_air_temperature_time (`backend/app/crop_growing_geometry_climate.py:127–149`). Stock dynamics appends each leaf’s inflow/maintenance/removal in ID order (`stock dynamics:109–110`). Integrated units: C `mg_CH2O/m2_floor`, fruit number `fruits_equivalent/m2_floor`, heat `J/m2_floor`, vapor `kg_water/m2_floor`, capacity `J/m2_floor/K`, air-temperature-time `degC_s` (`geometry climate:127–132`). Per-leaf balance is `ΔCi−∫gi+∫Mi+∫Ri=0`, with current 64(N+1)ulp item-scale budget (`stock dynamics:116–126`). There is no seed-C transfer or birth-respiration event term in these fixed-topology ledgers.

## 4. Immutable current continuation and canonical area rule

`backend/app/crop_leaf_carbon_stock_continuation.py` supplies prepare/start/checkpoint-bytes/restore/advance (`:105–260`). Preparation normalizes/evaluates once, preserving original request, normalized program and seed state/evaluation/initial receipts as canonical immutable bytes. Identity binds engine/short/components, four profiles, policies, schema `individual-leaf-carbon-area-vector-v1`, Python/platform/float environment, grid/layout/flux units (`:46–53`, `105–126`). Context bound is 2 MiB, checkpoint 512 KiB (`:17–18`).

Checkpoint fields are version, context SHA, step_index, output_cursor=index+1, sample-prefix SHA, last_confirmed, integrated_transfers, balance_residuals/budgets (`:139–146`). No UTC origin, exact emergence, attachment, event queue, topology phase/cursor, birth ID/history or SourceRecord field appears. Restore requires trusted external raw SHA, canonical JSON, no duplicate keys/nonfinite constants (`:194–211`). It demands seed vector length and the exact current flux key set, evaluates current RHS and seed-relative balances (`:161–187`): adding entries cannot turn an old checkpoint into a supported new topology.

Advance accepts 1–128 steps, validates current endpoint once, then four new stages per step; numerical/domain failure returns hold with failed step/time/stage/reason, last confirmed state/transfers, and no next checkpoint (`:214–260`).

Initial inherited preparation requires nonnegative age/positive requested A, computes canonical F(age), checks requested/canonical with rel_tol=1e-12/abs_tol=0, uses canonical A initially, and retains both values as receipts (`backend/app/crop_growing_geometry_climate.py:60–71`). Thereafter current A and `D=A−F(a)`, `D−D0` are retained; current restore uses original D0 and never calls initial preparation (`stock dynamics:75–82`, `111`, `116–126`; continuation:180–185, `226–246`).

The stable canonical function implements `F(a)=Amax/(1+exp(−k(a−midpoint)))` and requires a positive normal represented result (`backend/app/crop_leaf_area.py:73–86`). Age 0 therefore has positive F(0) when supported; `zero_lower_asymptote_sigmoid_v1` is not an area-zero-at-emergence rule. Requested area 0 is rejected (`:43–52`, `105–118`). These routines supply no seed-C-versus-area equation.

## 5. Separate existing birth, exact-clock, population and attachment paths

- `create_declared_leaves`: closed input `input_id/origin/time_origin_utc/segments/births`; each birth is `leaf_id/attachment_internode_id/emerged_elapsed_seconds_exact/base_temperature/curve/normalization/initial_area`. It permits 0–512 births, ordered times with ties, unique IDs, in `(start,end]` (`backend/app/crop_declared_leaf_births.py:13–14`, `39–74`). It creates age exactly 0 at the declared exact emergence, validates F(0), advances only post-birth forcing, and preserves original attachment plus initialization/advance input SHA (`:69–95`). At an end-boundary birth there is no advance. EVENT_KEYS has no carbon/source/debit/respiration/capacity/energy/event_id fields.
- Exact elapsed seconds use reduced nonnegative numerator/denominator integer strings, unit `s`, positive denominator, each string≤1024 digits (`backend/app/crop_rational_morphology_clock.py:30–40`). Leaf clock fields include origin, age/temperature bases, leaf ID, whole-second UTC origin, emergence/current exact seconds, base temperature, exact age. At birth/checkpoint equality age must be 0 (`backend/app/crop_rational_leaf_area.py:17–20`, `46–60`). Piecewise-constant exact-air advancement uses Fraction(binary64 temperature−base)×exact duration/86400 on contiguous segments, holds below base (`:63–87`). This is distinct from current dynamic-air RK4 age integration.
- Initial inventory requires 1–512 leaves with attachment/full rational initialization and preserves initial ordered ID/attachment anchors (`backend/app/crop_leaf_inventory.py:78–88`, `101–123`). Population combines this and declared new leaves, retaining immutable declaration hashes/birth inventory; it checks duplicates/order/anchors and total count≤512 (`backend/app/crop_leaf_population.py:11–12`, `39–70`, `103–122`). Tracked inventory area is not automatically whole physical canopy (`contracts/crop-declared-leaf-inventory-v1.md:18–22`).
- Area lifecycle fixes future birth/removal declarations/hashes, validates all IDs, permits removal of an existing or scheduled leaf, and requires unique removal leaf/event IDs (`backend/app/crop_leaf_lifecycle.py:29–52`). Pending slots are `{state:None,removal_receipt:None}` (`:55–84`). Advance initializes reached births at exact emergence then advances only the suffix through removal timeline (`:133–159`). Single-leaf removal initialization permits immediate removal and receipt at its initial instant (`backend/app/crop_leaf_removal_timeline.py:23–39`, `100–110`), so same-instant birth/removal exists in this area-only path. It does not define current-Ci funding or energy-event ordering.
- `build_leaf_birth_inputs_from_stored_shoot` reads original stored stem program/endpoint states, checks timeline endpoint and original parent identity, classifies original sequences and emits vegetative births with original exact emergence/attachment (`backend/app/crop_stored_shoot_leaf_birth_inputs.py:63–139`). Stable IDs hash model version/stem program/policy/sequence/attachment (`:101–119`). Uniform profile contains only base temperature/curve/normalization/initial_area (`:49–60`); no funded C or incoming heat profile.
- `bind_leaf_population_to_stored_stem` checks identical UTC origin/current elapsed coordinate, attachment existence in the actual stored frame, and parent emergence≤leaf emergence≤current. It returns original population/root/result hashes and leaf IDs/time/area (`backend/app/crop_leaf_stem_binding.py:25–49`). It validates population, not stock continuation.

## 6. Capacity/sensible ledgers and older removal continuation

Continuous independent-area heat accounting already has `Ccap=k*LAI`, net geometric capacity rate equal to gross `g_in−g_out`, incoming/outgoing sensible powers `g_in*(Tin−Tref)`/`g_out*(Tout−Tref)`, `U=Ccap*(Tc−Tref)`, and chain-rule checks (`backend/app/crop_area_canopy_energy.py:47–84`). Its required units are at `:14–17`; numeric constants are capacity `J/m2_floor/K`, capacity rate `.../s`, energy `J/m2_floor`, power `W/m2_floor` (`backend/app/crop_canopy_energy_transport.py:15–20`). Current Ci dynamics supplies the area-based gross rates and retains explicit incoming/outgoing temperature forcing (`stock dynamics:83–88`; explicit-LAI joint RHS:22–30, `123–128`).

The existing finite-removal path is older and separate:

- `crop_growing_geometry_leaf_removal_point` imports `crop_growing_geometry_continuation`, not stock continuation (`backend/app/crop_growing_geometry_leaf_removal_point.py:10–17`). Its current indices are older `108+2n`, aggregate leaf C at1/U at105/ages from108 (`:69–71`, `99–120`). It does not directly accept current stock Context/vector.
- `apply_removals` validates trusted parent CP/context/exact grid coordinate. It requires zero continuous leaf removal and capacity_outflow, a complete positive assumed absolute `mg_CH2O` per-leaf distribution matching aggregate/floor, and at least one remaining leaf (`:61–86`). Closed events carry event_id/leaf_id/carbohydrate/capacity/sensible_energy/outgoing_temperature and must be unique/current (`:89–98`).
- It checks `Tout=Tc_before`, `capacity=k*current A/floor`, `Eout=capacity*(Tout−Tref)`, subtracts event C/floor and signed E once, checks remaining C/capacity/energy, retains surviving current a/A/original indices, original D0/receipts/prior21 transfers, and returns separate point outflows (`:99–139`). Birth/incoming material, empty canopy and non-well-mixed removal are unsupported (`contracts/growing-geometry-leaf-removal-point-v1.md:30–45`).
- Post-removal context executes the point from trusted parent CP, selects survivors in original order, evaluates current post-event RHS, preserves D0/receipts/old transfers/event outflows and starts segment21 transfers at0 (`backend/app/crop_growing_geometry_post_removal_context.py:149–190`). Phase is `after_removal_before_next_step`; original global index/exact time and remaining horizon are retained.
- Next-interval global balances count prior flux, point C/capacity/sensible outflow and new segment flux once each, including canopy/reduced-energy/capacity budgets (`backend/app/crop_growing_geometry_removal_next_interval.py:54–105`). Scope remains first removal/positive remaining canopy/zero continuous leaf-C and capacity outflow; births/empty canopy/multiple events unsupported (`contracts/growing-geometry-removal-next-interval-v1.md:3–6`, `20–35`).
- Earlier `crop_leaf_carbon_removal` connects rational area lifecycle to aggregate SLA-consistent management with explicit absolute masses and area≈sla*carbon checks (`backend/app/crop_leaf_carbon_removal.py:76–129`). Independent-area point explicitly does not invoke it (`contracts/growing-geometry-leaf-removal-point-v1.md:3–6`). Neither is a current Ci funded-birth operator.

Positive-canopy restrictions exist at several boundaries: fixed list≥1, aggregate Ci>0, joint LAI>0, area-energy LAI>0 (`stock dynamics:48`; stock RHS:58,68; `backend/app/crop_explicit_lai_climate_rhs.py:91–96`; area energy:47–48). Zero-weight partition is therefore not an already implemented empty-canopy continuation.

## 7. Existing provenance, availability, stored-time and 3D boundaries

`SourceRecord` stores provider/product/version/source URL/site, revision, observed/published/available/retrieved/valid times, variable unit/time semantics/provider QC, project checks/rights, raw SHA, synthetic author/method, source reviewer/evidence (`backend/app/provenance.py:35–40`, `84–149`). It checks UTC/time coherence, duplicates, synthetic metadata and content-addressed identity (`:151–191`).

Appearance input authority validates original canonical SourceRecord against exact program SHA/product/version/revision/reviewer/evidence. It requires declaration≤observed≤published≤available≤retrieved≤decision, exact unit-variable paths, structural QC and explicit rights/redistribution denial where declared (`backend/app/crop_leaf_appearance_input_evidence.py:62–102`). Its contract calls this structural evidence, not numeric/gate approval (`contracts/crop-leaf-appearance-input-evidence-v1.md:11–25`). Population input evidence is a separate generated-declaration review, not a replacement for original appearance-policy evidence (`contracts/crop-leaf-population-input-evidence-v1.md:11–25`; appearance contract:3–5).

Appearance farm binding checks actual completed/signed parent job/root, original input evidence and current rights; source and rights available_at≤registration decision, occupancy/calendar bounds, repeated current parent/rights checks (`backend/app/crop_leaf_appearance_farm_binding.py:155–185`; `contracts/crop-leaf-appearance-farm-binding-v1.md:11–29`). This infrastructure does not already bind a stock funding event.

Current stock artifact input contains only schema/input_id/origin/rights/time_origin_utc/step_seconds/step_count/program; its own-input rights preserve explicit use/display/redistribute. There is no SourceRecord/available_at field (`backend/app/crop_leaf_carbon_stock_artifact_reader.py:118–159`). The contract says this UTC origin is a synthetic display basis, not observation/farm time or available_at (`contracts/crop-leaf-carbon-stock-artifact-v1.md:6–11`). Producer preserves original request/program/seed/context/4 profiles/notice and CP bytes, exact dt×index descriptors and CP chain, then publishes completed root last (`backend/app/crop_leaf_carbon_stock_artifact_producer.py:11–45`). Reader identifies saved A as geometry authority and stem/pose/attachment as separate authored asset (`stock artifact reader:40–52`).

Current 3D scaffold has three fixed IDs and authored height/yaw; stock renderer captures Ci without deriving geometry from it (`web/src/growingGeometryPlant.ts:8–12`, `30–38`). Accepted stored-3D contract excludes new births/intermediate states and distinguishes authored attachment/pose from stored A/Ci/a (`contracts/leaf-carbon-stock-stored-3d-v1.md:3–11`).

## 8. Missing current fields/operators versus unresolved questions

The inspected current stock dynamics/continuation closed interfaces lack:

| Current absence | Separate existing fact |
| --- | --- |
| Funding source/debit/seed-respiration event fields and atomic birth transition | Continuous buffer/`cLeafG*G` accounting exists; initial_carbon is an initial declaration. |
| Birth identity/history/exact emergence/attachment/topology phase and variable vector transition | Exact birth/population/lifecycle/attachment modules exist separately; current CP shape is immutable. |
| Incoming birth-capacity/sensible point ledger and current-Ci global event continuation | Continuous gross area-capacity flow exists; older removal ledgers target aggregate layout. |
| Empty-canopy Ci initialization/continuation | Positive list/aggregate Ci/LAI/capacity boundaries block it. |
| Ci SourceRecord/available_at/current farm-parent funded-input binding | General provenance/appearance bindings exist; current stock epoch is synthetic display time. |
| Funded-birth artifact/SDK/new-ID renderer path | Accepted current artifacts use fixed list; renderer uses authored original3 IDs. |

Unresolved questions for the parent’s required native CLI judgment and deterministic review: evidence/source/units for seed C; validity/application of growth cost for a birth event; funding/depletion and simultaneous-event policy; exact source clock versus fixed dynamic-air grid; declared-population/common-footprint/attachment evidence; incoming temperature/sensible closure and empty-canopy domain; provenance/rights/current-review sufficiency. This map chooses none of those policies and offers no coefficients or generated crop results.

## 9. Performed verification and limitations

Performed mechanical reads/searches, file/line mapping, source SHA256 capture, and one private draft write (directory0700/file0600). No equation execution, tests, builds, services, external retrieval, data adoption, gate check, application/repository mutation or recursive CLI invocation. The first file-write command used unavailable `python` and failed before making a file; the successful write used `/usr/bin/python3`. Existing repository acceptance is reported as documented evidence only. Parent may adopt the single draft after its guarded phase; this agent wrote no repository research file.

## Source capture SHA256

Captured UTC: 2026-10-25T23:14:39.274093+00:00

Raw full-file SHA256 values below apply even when the read covered selected relevant sections. No source bytes/private credentials are embedded. Navigation-only search hits are excluded from this evidence manifest.

| Source | SHA256 |
| --- | --- |
| `AGENTS.md` | `9110c45e16c0fa2b9e3cc768d3d6f20763ba1cf25305e0b9afdf95bf661a1399` |
| `README.md` | `04b92013cefc7e7b5f92657c4a43b77071a569bcff9b2c161b2f5663a0e9f99b` |
| `docs/PROJECT_SPEC.md` | `2c64340ea2684c80360bc2e7fc0898d34a65ba127e7843ea56545de13c919a12` |
| `docs/ARCHITECTURE.md` | `68ba2181cff228d9cd4850f131d0039b6a7230feae4aed4651ca23081792851f` |
| `docs/TECH_STACK.md` | `ed7a6fdf9b2f7bd2459e551d44cbdd5d5a39afa63a7a0ba087f946770d05628d` |
| `docs/RESEARCH_BASELINE.md` | `a1042af891d14f7aa65855d1f1c84b8db995ecbe5d3680f9ee19242072dee1c3` |
| `docs/IMPLEMENTATION_SLICE.md` | `87cb97d646af4d76e12d0b3c2599b00c8adc5cb0f7a3dfd3bf32c0e6e69b11b8` |
| `docs/IMPLEMENTATION_READINESS.md` | `8d5eddb4f3a894637f277bc2110e8be0619eb4b27ded93cd160663c9d881aeb3` |
| `tasks/todo.md` | `3ccfb93adab75cadc9f837cc8b2e68c75270d92fbbe97f4da4e0bdd03ecb75ce` |
| `tasks/plan.md` | `dd86037346f1e43f8f4cd0e226365835d3d684e0c745e73c8e6ff9d2e509047a` |
| `backend/app/crop_leaf_carbon_stock_dynamics.py` | `0e2a51a23b95b10cfc15d46f5668266f2b7981a769d966a167f9a4a9cafdf80d` |
| `backend/app/crop_leaf_carbon_stock_rhs.py` | `1da1cfef06860893b9ef4f661b15e5d7b4bc099a8d6563c4a9c6bd23156ab4be` |
| `backend/app/crop_leaf_carbon_stock_continuation.py` | `62b7ba4c8dbcf56297fde3e2c8ef78e55efe283eab85b9f26640f917236e8f0d` |
| `backend/app/crop_leaf_carbon_partition.py` | `6b80b6611ac1f972158fe00fea92c9b0b99af3d94f942ec2710b6fea26c81266` |
| `backend/app/crop_leaf_partition_climate_rhs.py` | `a708f13ed9290f4353e61310959aeab8f2f4bf0c3c4f02d5f9d0181fc3aebab3` |
| `backend/app/crop_growing_geometry_climate.py` | `5cf58d1dea92e59e1059d5e5cd359a81b8dde950fed2ac575911a4be90788a0a` |
| `backend/app/crop_explicit_lai_climate_rhs.py` | `92298f609d5225955ed153e5c2c194a012697ed38ca4b6d032dc552475f713f0` |
| `backend/app/crop_explicit_lai_carbon_cohorts.py` | `5c3e305f317205b36bac037aaf8a4a0c2342d5ed44a1169a0cffdd0905873541` |
| `backend/app/crop_growth_rates.py` | `d8270e642dc80a747dd7d449094351369abb135a4663c3bf9fcdb1be5cd75858` |
| `backend/app/crop_area_canopy_energy.py` | `8a6c7b8fb772d550bcda63d13185f180ad082c9f5e6e05937cce20bb3edebba8` |
| `backend/app/crop_canopy_energy_transport.py` | `389f8c68c5259d20d3bb5d61e191791c6df112eb8b24c7cd1d5020e7da4e579c` |
| `backend/app/crop_leaf_area.py` | `a8e1182a5630df592ae98cf0fe79c840207bd478a30391280f837f092232c5a6` |
| `backend/app/crop_leaf_expansion.py` | `7dfbc855b619d01139ae0dab84b7097cbc33a5b8d4e472ae143c442d124d53a6` |
| `backend/app/crop_declared_leaf_births.py` | `44068d74541b873bd5459a2893b87c357797639805e1eaa346f1f35880ca2c5f` |
| `backend/app/crop_leaf_inventory.py` | `f38f064e70c869a76a0a00b916548904b72b9aa92f105d17c1afd22bd3ad576d` |
| `backend/app/crop_leaf_population.py` | `b37bbee59c20778f38506d157644d87c91cd8fe2cf1ca54e9842bb8c10eabd09` |
| `backend/app/crop_rational_leaf_area.py` | `2eea8499a9caae569580f66b0f89ac8711a06d5cf7993be047d013850ba434a0` |
| `backend/app/crop_rational_morphology_clock.py` | `7926dc9a9a51e452e79ca74e31fd88d7d5b34120c5fc4b8a8107b1c4f0a85ea3` |
| `backend/app/crop_leaf_lifecycle.py` | `75496cc682ee4e6108215c66103d061897859e07836c14c4fb4a0e80ffbf581b` |
| `backend/app/crop_leaf_removal_timeline.py` | `a37f6f003cc67a76f0b02fc7c50192f62b20f4cc83a734169cb685211b01c916` |
| `backend/app/crop_stored_shoot_leaf_birth_inputs.py` | `d8e59fdf99156694d424dad4f392fd880fac9b059984f1d9144ee0f61417a5f4` |
| `backend/app/crop_leaf_stem_binding.py` | `2b57a8b009fceb83a2d23c3356d9e0792576111a50445f8b7a071ae9cf759673` |
| `backend/app/crop_growing_geometry_leaf_removal_point.py` | `a792ce523f05117a2d3d4f903641480f386e58afd66b1d47bbe9dbba89ed4634` |
| `backend/app/crop_growing_geometry_post_removal_context.py` | `89e36ffa5ce9f92c8c936bbdbd4456617f773ef7500fb8cb0f2891efa0860e8d` |
| `backend/app/crop_growing_geometry_removal_next_interval.py` | `7a3aa794eba8089ae89d70750981b066d44f83807d9879e5b22e856deeb42c15` |
| `backend/app/crop_leaf_carbon_removal.py` | `fcfb4da564f30728d51be65428b97f72588bb2e9d5d3a6c1c8f8f85eaa2c250a` |
| `backend/app/provenance.py` | `8b616d1ca21233b39f9b69e8dbec475e0483bc8d8b38baa18c99c4bfdcd93b0f` |
| `backend/app/crop_leaf_appearance_input_evidence.py` | `c4486ac90a300f3ac9302d460b94fa92e9f2369e8c7cfd562b749ed76459f0c5` |
| `backend/app/crop_leaf_appearance_farm_binding.py` | `cd931d4aa6b7e2681bd556e6e3ba44ec1dab46e51cd51d9658108cc5031e93ef` |
| `backend/app/crop_leaf_carbon_stock_artifact_reader.py` | `37d6cc94f20d85a1d5e37ae0ff3f4466c3ab3b563768543f2d40e204cb2f0225` |
| `backend/app/crop_leaf_carbon_stock_artifact_producer.py` | `98f5997eefd0857402a782cf39d0e1db729b38b4678f71d25115c4000cc8f679` |
| `web/src/growingGeometryPlant.ts` | `4c3287ba5b99204f8800002d73572b647028d60da9ef7bc9ef5ac1e1f1ced5ee` |
| `contracts/crop-leaf-carbon-stock-dynamics-v1.md` | `393ad3339f0194eb03d8008b702dea8f145681a34d0388b754f34399713d4be5` |
| `contracts/crop-leaf-carbon-stock-rhs-v1.md` | `88553f8f39712dee9c7a080aeb3444188cf6543b8ff4cb521c56bf85f72c2ed9` |
| `contracts/crop-leaf-carbon-stock-continuation-v1.md` | `6dc7a59627b03dfcef9c4a22c436172a33e6b7cfdf0f50da949b4e925e8f9b3f` |
| `contracts/crop-declared-leaf-births-v1.md` | `95b317d0f685fb376e826ebf01ff92e76a0b5ee2da2311eec791ce431cf5c929` |
| `contracts/crop-declared-leaf-inventory-v1.md` | `f2626cdd4d058a44dec2d2a50dffbc497188fa9481a0385c2fe9243461686aa6` |
| `contracts/crop-stored-shoot-leaf-birth-inputs-v1.md` | `ff95835d9f1478031161615c40becd90f5b4ee02d9c26ef6d52af737c063339a` |
| `contracts/crop-leaf-stem-binding-v1.md` | `dd67d6359146f70fdf7e349f392f895f499033c5d5193796caf64c1acccae0fe` |
| `contracts/growing-geometry-leaf-removal-point-v1.md` | `d59bdbd39b96ab8ff5cef159b836d8ed317727a8b46309ed644f59d57e119801` |
| `contracts/growing-geometry-post-removal-context-v1.md` | `58912fe4e03df581c6c316b487713881d44888525d10f2f080bb645587cce48d` |
| `contracts/growing-geometry-removal-next-interval-v1.md` | `11ed173c53862d9bf1d68fd855bcc8f1397c936a0993b78f0efc4f4b40bdd29e` |
| `contracts/crop-leaf-appearance-input-evidence-v1.md` | `06d9be282c879f901c99da537af1afd742d8772218c7fa1783dc34bfae2007e4` |
| `contracts/crop-leaf-population-input-evidence-v1.md` | `5975116d16e93c14e40a25a0c436147ead97916edda0d47563684c0231834f6f` |
| `contracts/crop-leaf-appearance-farm-binding-v1.md` | `fc6c6eb98e32397a9dfcdd8a1555d9e9badec2f4032b2b2442a6299ce6850716` |
| `contracts/crop-leaf-carbon-stock-artifact-v1.md` | `b385c1fa3c47b8bcc9b781f638a04b18109d9062e673a1f77c7cf6b6d73e24f5` |
| `contracts/leaf-carbon-stock-stored-3d-v1.md` | `41fbd3b0081c1b72864d3be21522569309348315198107f910cd04ab2f1124cb` |
| `contracts/leaf-carbon-stock-sdk-v1.md` | `5d8239cf77bb8f6927cbf89afdaaddd516975a57215ee0b608d0be9c6d77d6db` |
| `contracts/leaf-carbon-stock-export-v1.md` | `67fc4c9c1d9c2b77f275d20eda65b759bf820ed82ed69164da091944b4e06df2` |
