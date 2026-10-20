# Current-stage solar, crop and CO₂ inventory — v1

Status: instantaneous software acceptance completed;
[evidence](../research/artifacts/crop-greenhouse-co2-joint-20261021.json). This follows
[CO₂ gas](crop-co2-gas-v1.md), [net crop exchange](crop-co2-net-exchange-v1.md),
[air mass](crop-co2-air-mass-v1.md) and the existing
[solar/ventilation joint RHS](crop-greenhouse-solar-joint-v1.md).
The [source policy](../research/crop-co2-stomatal-source-policy-20261021.md)
remains authoritative for the explicit numerical conventions and stomatal hold.

## New input/state boundary

`crop_greenhouse_co2_joint.evaluate_rhs(scenario=..., solar=..., ventilation=...,
co2=..., growth_profile=..., cohort_profile=..., transport_profile=..., exchange_profile=...)`
has a new model and state identity. The scenario retains the old joint block
names, but `climate_state` additionally requires `air_co2_mass [mg_CO2/m2_floor]`,
and its solar forcing **excludes** caller-supplied `co2`. The original108-state
model, checkpoints, program and stored result contracts are unchanged.

The new `co2` block has exactly `input_id`, `origin`, `basis`, `parameters`,
`forcing`. ID is nonblank1–200characters; origin matches the scenario, solar and
weather research origin. Basis is explicit `wet` or `dry`. Parameters contain
only `air_pressure [Pa]`; forcing contains only `outdoor_co2_density [mg_CO2/m3]`
and signed `external_co2_flux [mg_CO2/m2_floor/s]`. There is no default pressure,
outdoor concentration, injection, water content or external ppm. Every quantity
has exactly `{value,unit}` and the existing finite scalar/unit policy.

All109 state quantities are trial inputs. Positive CO₂ mass is needed by the
underlying crop's positive-ppm domain; a depleted value is held, not replaced
by a tiny floor. h and Rv are the same positive explicit core parameters.

## One shared trial

```text
c_CO2 = m_CO2 / h
p_H2O = (m_v / h) * Rv * (Ta + 273.15)
crop_ppm = gas.density_to_ppm(c_CO2, Ta, explicit P, basis, current p_H2O)
solar_rhs = existing Solar/NIR/PAR/ventilation/crop RHS(using crop_ppm)
net = net_exchange(solar_rhs.joint_rhs.crop)
air = air_mass(current m_CO2, same h, same actual ventilation f,
               outdoor CO2 density, external CO2 flux, net)
```

Evaluate the gas conversion, Solar RHS, net adapter and air mass RHS once each.
The existing Solar chain calls NIR/PAR/ventilation/joint/actual startup crop once.
Do not substitute an old organ result or recalculate the crop. Derive ppm from
air temperature, not canopy temperature, and derive water pressure from the
current vapor inventory, never outdoor or stale moisture. Pass current vapor
pressure on both gas bases; the ideal mixture requires P>p_H2O and CO₂ plus
water mole fractions≤1. Existing crop/thermal/solar domains remain unchanged.

Return a new109-state derivative structure with the actual air mass derivative,
current gas diagnostics, original Solar component result and heat composition,
net and air results, copied normalized new inputs, source/component/profile/
policy/model/code/input/calculation identities. The normalized new forcing has
no prescribed ppm; the nested old Solar result records the **derived** ppm used.
New IDs are `current-state-solar-crop-co2-joint-rhs-v1` and
`crop-solar-co2-stage-state-v1`. Scope is instantaneous software research only.

Preserve the original seven crop/heat/water/capacity balance residuals and
budgets exactly. Add air CO₂ inventory and a combined carbon-equivalent ledger:

```text
M_air' + F_vent_out - F_external
  + (44/30) * (C_plant' + C_removed + C_terminal) = 0
```

C_plant' sums buffer/leaf/stem and50fruit-carbon derivatives, excluding number
and temperature derivatives. Removal and terminal fruit outflow are external
biomass transfers in this ledger, not air respiration. Use the named C9 mass
equivalence; it is not a claim of a unified physical molar-mass convention with
the C8 gas helper. Budget is the air budget plus converted existing crop budget
plus64 ULP of the largest actual combined balance term or1mg_CO2/m2/s.
Retain [GreenLight notice](../LICENSES/GreenLight-BSD-3-Clause-Clear.txt).

## Acceptance fixed before execution

1. Use all7 existing independent Solar scenarios on both wet/dry bases. Compute
   current gas quantities independently with Decimal80, feed the unrounded ppm
   into the existing **app-free** full Solar derivative oracle, and derive net/
   air flux from its respiration/mass terms. Compare all109 derivatives at
   relative5e-12/absolute5e-14; pure gas diagnostics at relative3e-15/absolute0.
2. Capture actual one-call composition, same current air/vapor/volume/flow and
   actual startup-result handoff. Check all nine ledgers, day/night, pressure/
   inventory response, old Solar equivalence at the derived ppm, stable bound
   input identity/no input mutation and no double heat/water/carbon credit.
   Include nonzero leaf/stem removal explicitly; the original seven scenarios
   contain terminal fruit carbon but zero continuous leaf/stem removal.
3. Reject old supplied ppm, wrong units/shapes/origins/basis, missing/nonpositive
   pressure, impossible gas mixture, depleted/invalid inventory and propagated
   old-model holds. Keep original modules/profiles/checkpoints/results and5roots/
   previews under the existing WSL guard. No time integration, storage/API/3D,
   browser/DB/whole-product or field gate acceptance in this child.

## Observed acceptance — 2026-10-21 KST

Final37 checks passed in0.54s. The14 wet/dry reference points plus a nonzero
removal point compare1,635 state derivatives with the app-free oracle. The final
run includes the removal test added after the initial36-pass run; these counts
are not added. The missing-module initial run is an absence check, not a
numerical counterexample. Actual capture verified all nine specified component
calls occur once, including the real startup crop handoff and shared vapor/flow.

Final guard child0/wall0.859496s, peak combined RSS617,566,208bytes, FD4→4;
all5roots,2,148originals and frozen previews preserved, owned process/PG/temp/
credential residue0. Existing model/profile bytes were unchanged. The exact
native CLI model/effort and selected metadata hash are recorded in the evidence.
There is no time advance, trajectory, checkpoint, new saved3D, field/gate or
deployment acceptance. Next is a separate109-state short integrator/reference.
