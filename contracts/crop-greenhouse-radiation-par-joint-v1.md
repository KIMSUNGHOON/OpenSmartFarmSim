# Current-state solar PAR joint RHS — v1

An instantaneous adapter after the [pure PAR boundary](crop-greenhouse-radiation-par-v1.md),
using the unchanged [joint RHS](crop-climate-joint-rhs-v1.md).
This is a new calculation identity, not a replacement for old saved models.

`evaluate_rhs(scenario=..., solar=..., growth_profile=..., cohort_profile=...,
transport_profile=..., exchange_profile=...)` takes the same closed joint
scenario except for its forcing block:

- Remove `par_above_canopy` and `canopy_external_heat` entirely.
- Require `canopy_non_par_heat` in `W/m2_floor`, finite signed int/float excluding bool.
- Preserve the other existing forcing quantities and units.

Legacy incident-PAR/total-canopy-heat keys, extra keys, missing non-PAR heat and
nonfinite values are holds. `canopy_non_par_heat` explicitly excludes this
boundary's solar PAR; its provenance is the caller's declared research input.
The function cannot detect semantically mislabeled numbers. Future server
admission must bind the actual component definitions and evidence. NIR, pipe,
longwave and other omitted heat may be included in this explicit complement;
it is not a derived or approved total solar estimate.

`solar` has `input_id`, `origin`, `values`, exactly as the pure PAR contract
**except `leaf_area_index` is forbidden**. Its origin must match the scenario.
The adapter derives LAI from pinned SLA×current leaf inventory, evaluates PAR
once, and evaluates the existing joint RHS once with:

```text
par_above_canopy = solar PAR incident photons
canopy_external_heat = canopy_non_par_heat + canopy_absorbed_PAR
```

No floor absorption or unresolved reflected energy is credited to canopy/air;
air sensible/vapor forcing stays unchanged. Existing crop, canopy exchange,
material-capacity and seven joint balance checks remain authoritative.
Leaf inventory must be positive under the existing joint model's empty-canopy hold.

Output `model_version=current-state-solar-par-joint-rhs-research-v1` retains
normalized original scenario/solar inputs, component code and calculation hashes,
policy hash, input/calculation identity, original joint result and PAR result,
and the non-PAR/PAR/combined canopy heat terms. It has
`claim_scope=synthetic_current_state_PAR_joint_rhs_only`,
`G0_G4=not_assessed`, no time advance, storage, API, UI or deployment.
No original module/profile or stored context identity changes.

Acceptance: independent Decimal solar transfer plus the existing independent
whole-stage oracle; actual same-state LAI/temperature/crop/heat rates and seven
balance budgets; changing leaf state updates the boundary while preserving its
incident coordinate; dark/non-PAR signed cases; one boundary and one RHS call;
schema/unit/mixed-origin/double-count/empty-canopy/numeric holds; immutable inputs,
identity/replay and protected live roots/source/assets. Every RK trial, trajectories,
NIR optics, new context/checkpoint/storage/UTC3D remain later acceptance.
