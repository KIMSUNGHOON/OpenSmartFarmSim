# Atomic CO₂/Solar managed state transition v1

Status: research software accepted by35 focused tests on2026-10-21 KST. This follows the
[109-state RHS](crop-greenhouse-co2-joint-v1.md),
[short integrator](crop-greenhouse-co2-integration-v1.md) and unchanged
[crop/capacity removal policy](crop-climate-joint-management-v1.md).

`apply_management(scenario, solar, ventilation, co2, event, four profiles)`
evaluates the actual CO₂/Solar RHS before and after a copied candidate. Reuse
the old event parser, explicit organ subtraction, decimal-rational cohort
fractions, leaf-capacity removal and inventory-ledger primitives. Do not call
the old management function or use its fixed-ppm/fixed-PAR RHS as the new
physical post-event result. Event origin must match the scenario.

## State and atomicity

The event has input_id/origin/values, explicit `leaf`, `stem_root` removals in
mg_CH2O/m2_floor and exactly50 `fruit_fraction [1]` values in0..1. The reviewed
decimal-rational fraction policy and numeric loss/underflow holds remain.
The new model is `joint-co2-solar-management-research-v1`; state schema remains
`crop-solar-co2-stage-state-v1`. There is no time/UTC advance, automatic harvest
or source of CO₂. Raw crop carbohydrate removal is not fresh harvested kg.

Buffer/T24/Tsum and bulk air temperature, water vapor and CO₂ mass are unchanged.
Same fixed geometry/pressure/basis then gives exactly unchanged ppm. Leaf
removal changes leaf area/canopy heat capacity and signed reference sensible
energy together, preserving canopy temperature within2e-13K. Actual post-event
Solar PAR/NIR and crop rates use the reduced leaf area. A changed photosynthetic
rate is a new instantaneous derivative, not gas accumulated during an event.
No stem/fruit heat or tissue water state is represented or silently set to zero.

Only after both RHS/domain checks and all event ledgers pass is the candidate
returned. Failure includes its phase and a snapshot of the confirmed pre-event
state, with no partial candidate publication/input mutation. An invalid initial
state has no confirmed snapshot. Full leaf removal/empty canopy remains held.

## Accounting and output

Retain the five carbohydrate/number/canopy energy/capacity/temperature ledgers.
Add four exact-zero bulk-air CO₂/vapor/temperature/ppm invariants and the
source C9 carbon-equivalent inventory:

```text
M_air_before + (44/30)*C_plant_before
  - M_air_after - (44/30)*C_plant_after - (44/30)*C_removed = 0
```

These10 ledgers preserve the named44g/mol/30g/mol source convention; the
converted removed carbohydrate is not gas emission or a carbon-footprint
estimate. Old stock budgets are64 ULP of their recorded inventory/terms;
canopy temperature uses2e-13K; conserved bulk-air quantities use exact0.
The combined stock budget uses the same64-ULP inventory policy in mg_CO2/m2.
Retain the [GreenLight notice](../LICENSES/GreenLight-BSD-3-Clause-Clear.txt).

Return normalized event/removal amounts/totals, before/after snapshots of all
four input blocks/current derived quantities and calculation identities,
`after_rhs` for a later caller's next-stage reuse, ten residuals/budgets,
source/component/profile/policy/model/event/input/calculation identities.
The stored snapshots are not checkpoint/resume admission. The full after RHS
is an in-memory research result, not an approved storage/HTTP packet.

## Acceptance fixed before execution

- Adapt all9 existing independent removal cases to the new Solar/CO₂ boundary
  on wet/dry bases. Compare109 post-event states, removed quantities, totals,
  canopy temperature/LAI/capacity and independently computed ppm with the pinned
  Decimal references. Relative5e-12/absolute5e-14, Tc absolute2e-13K; exact bulk
  air invariants and ten runtime budgets. Check profile/reference source hashes.
- Actual two new RHS evaluations, reduced-LAI absorption, actual post-event
  crop result and no invocation of the old management function. Zero event
  identity/replay/input immutability; full fruit removal, signed/zero Uref,
  incompatible origin/schema/quantity/fractions/profile and depleted/over-removal
  retain pre-event state. Numeric loss is held, not silently discarded.
- A manual16s integration→event→16s integration matches an app-free Decimal
  composition for all109 final states/44 transfers and combined carbon. This
  verifies numerical composition, not automatic scheduling/custody/resume.
- Focused WSL guard with original modules/profiles/results,5healthy roots,
  frozen previews, FD/owned cleanup/caps preserved. No browser/DB/whole CI,
  actual farm, price, ranking, gate or deployment acceptance.

## Observed acceptance

[Machine evidence](../research/artifacts/crop-greenhouse-co2-management-20261021.json)
records35 passing tests in1.58s. Nine independent removal cases on each wet/dry
basis verify109 post-event states, removal/capacity and gas quantities, with ten
event balances. Actual reduced-LAI Solar absorption and two actual new RHS calls
pass. Thirteen invalid input/removal cases preserve the confirmed state; initial
profile failure has no confirmed snapshot. Manual16s→event→16s composition
matches the app-free Decimal80 reference in all109 final states and44 transfers.

The first RED was a missing module. The first full run passed20 tests before a
test incorrectly requested a generator metadata field absent from the original
fixture. The corrected test pins the unchanged generator bytes explicitly;
neither production arithmetic nor the original oracle was changed to pass it.
The final guard preserves five healthy roots,2,148 original entries, frozen
previews, FD4→4 and zero owned process/PG/temp/credential residue. No runtime
checkpoint, automatic program, full crop cycle, saved109-state3D or gate is
accepted by this result. Next: a forcing/event program, then continuation/storage.
