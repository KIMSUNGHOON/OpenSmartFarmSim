# Prescribed main-air ventilation — v1

This child of [crop/climate coupling](crop-climate-coupling-v1.md) is an instantaneous
research calculation. Core files: `backend/app/crop_greenhouse_ventilation.py`,
`backend/tests/test_crop_greenhouse_ventilation.py`, this contract,
`research/crop-greenhouse-ventilation-reference.py`, and
`fixtures/crop-greenhouse-ventilation-reference-cases-v1.json`.

## Evidence and model identity

[Primary-source review](../research/crop-greenhouse-boundary-source-review-20261011.md)
records pinned GreenLight Chapter 8 equations, retrievals, hashes, rights, and limitations.
Reuse the immutable [canopy profile](../fixtures/crop-canopy-exchange-reference-parameters-v1.json)
and [retained BSD notice](../LICENSES/GreenLight-BSD-3-Clause-Clear.txt).
The model identity is `prescribed-main-air-ventilation-research-v1`.
Its mass coordinate and explicit `Rv` are a declared ideal-gas project reduction.
Source vapor equivalence requires `Rv=8314/18`; the existing joint input `461.5`
is preserved. Neither source coefficients nor observed farm data are adopted anew.

## Closed inputs and dimensions

`calculate_ventilation(scenario=..., profile=...)` takes the exact pinned exchange
profile and a closed scenario with `input_id`, `origin`, `state`, `parameters`, `forcing`.
Origin is `synthetic` or `reference_calculation`; ID is a nonblank string of1–200characters.
Every quantity is exactly `{value, unit}` with a finite int/float value; bool is invalid.

| Block | Required quantity | Exact unit and domain |
| --- | --- | --- |
| state | `air_temperature` | `degC`, strictly positive Kelvin after conversion |
| state | `air_vapor_mass` | `kg_water/m2_floor`, ≥0 |
| parameters | `air_volume_per_floor_area` | `m3/m2_floor`, >0 |
| parameters | `air_capacity_density` | `kg_air/m3`, >0 |
| parameters | `vapor_gas_constant` | `J/kg_water/K`, >0, same explicit value as parent when composed |
| forcing | `outdoor_air_temperature` | `degC`, strictly positive Kelvin after conversion |
| forcing | `outdoor_vapor_pressure` | `Pa`, ≥0 |
| forcing | `volume_exchange_per_floor_area` | `m3/m2_floor/s`, ≥0 |

The prescribed flow represents a declared well-mixed main-air/outdoor exchange.
Roof/top compartment flow, wind/window control, ACH conversion, geometry, and
facility coefficient estimation are separate models. `rhoAirCap` is sensible capacity
density, distinct from vapor concentration. Profile `cp=1000 J/kg_air/K` and
`L=2450000 J/kg_water` retain their research identities.

The pure boundary's temperature domain is mathematical positive Kelvin only;
it establishes no empirical accuracy range or outdoor saturation/QC eligibility.
It neither calculates saturation pressure nor clamps supersaturation. Existing joint
temperature/saturation/leaf guards still apply when testing composition.
Source QC and an outdoor applicability policy remain required for field inputs.
Missing vapor pressure is a hold rather than a dry-air default.

## Signed forcing and accounting

For `h=V/A`, `f=volume_exchange_per_floor_area`:

```text
rho_v_in  = m_v/h                          [kg_water/m3]
rho_v_out = vpOut/[Rv*(Tout+273.15)]         [kg_water/m3]
Qair      = rhoAirCap*cp*f*(Tout-Tair)       [W/m2_floor, positive into air]
Fv        = f*(rho_v_out-rho_v_in)           [kg_water/m2_floor/s, positive into air]
Lv        = L*Fv                            [W/m2_floor]
reduced_energy_to_air = Qair+Lv             [W/m2_floor]
```

Only `Qair` contributes to `air_external_sensible_heat`; only `Fv` contributes to
`air_external_vapor`. `Lv` is a separate vapor-energy ledger and is never credited
to the sensible air temperature derivative. Each local transfer returns air/outdoor
opposites and a zero local residual. This pairing is bookkeeping, not independent
proof of greenhouse or whole-farm conservation; vapor/liquid sensible enthalpy,
pressure work and other stores are outside this reduced boundary.

The output preserves normalized input plus input/code/policy/profile/source/notice
SHA-256, derived densities, forcing contributions, local transfers/residuals,
`time_coordinate=instantaneous_no_state_advance`, `scope=software_research_only`,
`claim_scope=synthetic_prescribed_ventilation_math_only`, `G0_G4=not_assessed`.
It has no database, API, state advance, irrigation, purchased energy, money, or UI write.

## Holds and numerical acceptance fixed before execution

Raise `VentilationHold` for closed-schema/type/unit/domain/profile violations.
Reject unrepresentable inputs, nonfinite products/quotients/sums, nonzero products
or quotients rounded to zero, and Kelvin-conversion stagnation. Analytical zero
factors produce exact zero after complete input and density validation. No clamp,
coefficient replacement, negative-flow `abs`, or fallback occurs.

Independent generator imports no application code, uses Decimal precision80 and
the pinned profile values, and generates six self-authored cases: cool/dry, warm/moist,
zero exchange, dry equilibrium, isothermal humidity difference, source `Rv`.
Compare all36 reference scalars with relative tolerance `2e-14`, absolute0;
expected zeros are exact. Generator replay must reproduce fixture bytes exactly.
Test source-form equivalence at `8314/18`, explicit461.5 variant, linear flow scaling,
signed heat/vapor, opposite local transfers, input immutability, identities, and holds.

A focused composition test passes these contributions to the existing joint RHS
at the same explicit trial and verifies `ΔTair'=Qair/Cair`, `Δm_v'=Fv`, unchanged
crop/canopy rates and accepted seven balance budgets. It proves an instantaneous
algebraic interface only. Runtime integrator reevaluation at every current stage,
new immutable model/context identity, independent trajectories/convergence and
stored API/3D deployment are subsequent acceptance work. Existing joint/source
profiles, stored results and user services remain immutable during this child.
