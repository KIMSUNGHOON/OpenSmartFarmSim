# Fixed-volume main-air CO₂ mass RHS v1

Status: scalar RHS accepted; [evidence](../research/artifacts/crop-co2-air-mass-20261021.json).
This child follows the accepted
[gas conversion](crop-co2-gas-v1.md) and [net crop exchange](crop-co2-net-exchange-v1.md),
using the reviewed [C8 mass capacity/exchange equations](../research/crop-co2-stomatal-source-policy-20261021.md#1-state-capacity-and-exchange).
The existing [prescribed ventilation](crop-greenhouse-ventilation-v1.md) defines
the same explicit nonnegative exchange-volume-per-floor-area convention.
It does not estimate flow from windows, wind, geography or facility defaults.

## Closed internal inputs

`crop_co2_air_mass.evaluate_rhs(state=..., parameters=..., forcing=..., crop_exchange=...)`
takes three closed quantity dictionaries. Quantities are exactly `{value,unit}`,
finite Python int/float excluding bool:

| Block | Field | Unit/domain |
| --- | --- | --- |
| state | `air_co2_mass` | mg_CO2/m2_floor, ≥0 |
| parameters | `air_volume_per_floor_area` | m3/m2_floor, >0, explicit fixed h=V/A |
| forcing | `outdoor_co2_density` | mg_CO2/m3, ≥0 |
| forcing | `volume_exchange_per_floor_area` | m3/m2_floor/s, ≥0 |
| forcing | `external_co2_flux` | mg_CO2/m2_floor/s, signed and explicit |

`crop_exchange` is an already computed result of the current net-exchange model,
with its exact model/code/scope identity, canonical input hash and a finite,
unit-correct, opposite uptake/air pair. `None` explicitly requests the no-crop
reference boundary. There is no omitted-crop default. Internal declared identity
checks do not establish authenticity, source rights or approved model inputs.

## Mass coordinate, signs and domain

```text
c_air = m_air / h
F_vent_to_air = f * (c_out - c_air)
m_air' = F_vent_to_air + F_external + F_crop_to_air
c_air' = m_air' / h                      [fixed h only]
F_vent_to_outdoor = -F_vent_to_air
F_crop_uptake = -F_crop_to_air
m_air' + F_vent_to_outdoor + F_crop_uptake - F_external = 0
```

Storage is CO₂ mass per floor area, not ppm or CH₂O biomass. Total mass is A*m;
the stated geometry is h=V/A. Positive ventilation transfer enters air; its sign
comes from the density difference, not a negative exchange magnitude. Positive
crop uptake removes CO₂ from air and nighttime respiration adds it. External
flux may represent an explicitly supplied boundary, without identifying it as
fuel combustion, purchased gas, energy consumption or a control law.

Reject invalid fields/units/domain and unrepresentable quotient/product/sum;
reject an outward derivative at an exactly depleted air inventory. Do not clip
mass or derivative. A positive inventory with a negative derivative needs a
later positivity-preserving time integrator. Temperature/pressure only enter a
later same-stage density→ppm conversion; changing a gas reporting convention
does not create mass. Variable volume/total-air pressure conservation, upper
compartments, dynamic crop feedback, stomatal substitution and production
integration/storage/API/3D remain separate work.

## Output and predeclared verification

Version `fixed-volume-main-air-co2-rhs-v1` returns copied normalized inputs,
source/model/code and crop-input identity, an input hash, density, mass/density
derivatives, signed external/ventilation/crop transfers and their inventory
residual/budget. Source C8 SHA is
`c0fb7a025533f15b80cb6cd60aafdc19be9fe42df6b8183cf97b83fc086138b3`;
retain the [BSD notice](../LICENSES/GreenLight-BSD-3-Clause-Clear.txt).

- Independently reconstruct total mass/volume/volume flow at explicit area17m2
  using Decimal80, then divide the total flux by area. Scalar relative error≤3e-15,
  absolute0; expected zeros are exact. Mass-budget policy is32 ULP of the largest
  magnitude among the actual balance terms or1mg/m2/s, separately labeled a
  numerical allowance, not an empirical acceptance threshold.
- Verify no-flow conservation, inward/outward ventilation, equal densities,
  external injection/extraction and the actual current joint crop→net result's
  opposite transfer, without recalculating that crop. A test-only RK4 harness
  compares the constant-ventilation no-crop analytic exponential at two step
  sizes, with convergence ratio14–18. This accepts the RHS through a numerical
  reference, not a product integrator or dynamic coupled simulation.
- Reject missing quantities, mass/density/volume-flow unit confusion, invalid
  types/domain/overflow, depleted outward transfer and incompatible crop pairs.
  Preserve original modules/profiles/results,5roots and previews under the
  existing WSL guard. No field, DB/browser, deployment or claim acceptance.

## Observed acceptance

Final30 checks passed in0.18s, including8 independent total-mass/volume cases,
the test-only analytic exponential/convergence comparison and actual daytime
and nighttime joint crop→net→air transfers. The earlier29-pass run lacked the
nighttime composition case and is not added to the final count. The initial
missing-module error is an absence check, not a numerical counterexample.

Final guard child0/wall0.592407s, peak combined RSS634,712,064bytes, FD4→4;
5healthy roots,2,148originals and frozen previews preserved; owned process/PG/
temp/credential residue0. Existing modules/profiles were unchanged. No product
integrator, dynamic CO₂ feedback, saved result/3D, browser/DB or whole-product
CI was run by this child. Next is a new same-stage CO₂/solar/crop/climate
composition, keeping old models/checkpoints/results unchanged.
