# Prescribed solar PAR boundary — v1

Child of [crop/climate coupling](crop-climate-coupling-v1.md).
[Primary evidence](../research/crop-par-primary-source-review-20261013.md) fixes
the equations, rights and limitations. This first child calculates instantaneous
solar PAR only. NIR, lamps, longwave radiation, facility optics estimation and
time integration require later acceptance.

## Inputs and identity

`calculate_par(scenario=..., profile=...)` takes the existing pinned
`crop_growth_rates.ReferenceParameters`, retaining its `k1Par`, `k2Par`,
`rhoCanPar`, `rhoFlrPar`. No old profile or calculation is changed.
The closed scenario contains `input_id` (nonblank string, 1–200 characters),
`origin` (`synthetic` or `reference_calculation`), and `values`.
Each quantity is exactly `{value, unit}`; finite int/float, excluding bool.

| Required value | Exact unit | Domain |
| --- | --- | --- |
| `outdoor_global_radiation` | `W/m2_floor` | ≥0; prescribed floor-normalized forcing, not an automatic weather conversion |
| `leaf_area_index` | `m2_leaf/m2_floor` | ≥0; current crop LAI when composed |
| `solar_par_fraction` | `1` | [0,1] |
| `solar_par_photon_conversion` | `umol_photons/J_PAR` | >0, solar spectrum only |
| `cover_par_transmittance` | `1` | [0,1] |
| `cover_par_reflectance` | `1` | [0,1], plus transmittance ≤1 |
| `construction_interception_fraction` | `1` | [0,1] |

The cover coefficients are already lumped, downward incident coefficients.
No additional screen, slope, cover area multiplier or facility default is inferred.
The two spectral inputs are explicit: source values 0.5 and4.6 are research
references, not locally approved spectra. Non-PAR global energy is excluded.
Use/display/redistribution rights and temporal/QC eligibility are not established
by the pure function's research origin. Actual farm inputs await deterministic
adoption and binding through G0 and later claim gates.

`model_version=prescribed-solar-par-boundary-research-v1`; output retains
normalized inputs, input/code/policy/profile/source/notice hashes,
`time_coordinate=instantaneous_no_state_advance`,
`claim_scope=synthetic_prescribed_solar_par_math_only`,
`scope=software_research_only`, `G0_G4=not_assessed`.

## Calculation and partition

For global radiation `G`, spectral fraction `f`, cover `tau,rho`, construction
fraction `s`, photon conversion `c`, and pinned crop optics:

```text
Pout = G*f
P = Pout*tau*(1-s)                    # above canopy, W/m2_floor
t1 = exp(-k1Par*LAI); t2 = exp(-k2Par*LAI)
a1 = 1-t1; a2 = 1-t2
Pdown = P*(1-rhoCanPar)*a1
Pfloor = P*t1*(1-rhoFlrPar)
Pup = P*t1*rhoFlrPar*(1-rhoCanPar)*a2
Pcan = Pdown+Pup
unresolved_reflected = P*rhoCanPar*a1 + P*t1*rhoFlrPar*rhoCanPar*a2
upward_transmitted = P*t1*rhoFlrPar*t2
par_above_canopy = c*P
par_absorbed_canopy = c*Pcan
```

Interior balance: `P=Pcan+Pfloor+unresolved_reflected+upward_transmitted`.
Exterior PAR partition adds `Pout*rho`, `Pout*(1-tau-rho)` and `Pout*tau*s`
to the four interior terms. These extra categories are **project bookkeeping**,
not added GreenLight heat equations. Canopy reflections and light reaching the
cover from inside stop at this accounting boundary; further bounces, cover
reabsorption and outdoor escape are unresolved. Do not call the remainder
outdoor reflection, floor heating, or air heating. The source's PAR approximation
and this partition are distinct from its multilayer NIR model.

The crop receives **`par_above_canopy`**, never `par_absorbed_canopy`.
The unchanged crop formula applies interception once. `heat_components` reports
PAR absorbed by canopy/floor only; neither is total solar heat. A later joint
adapter must combine canopy PAR with a separately identified non-PAR heat input
and preserve other heat terms. It must not add photon flux to watts, or add both
PAR and a total-solar term containing the same PAR.

## Acceptance fixed before execution

Raise `RadiationPARHold` for schema/unit/profile/domain violations, nonfinite
arithmetic, nonzero product or attenuation/interception rounded to zero, or a
partition residual beyond32 binary64 ULPs of the largest partition magnitude.
No fallback, clamp, hidden spectrum or local-facility applicability is supplied.
Analytical zero factors return exact zero after complete input/optical validation.

Independent Decimal precision80 reference imports no application code. Verify
all scalar partitions and both photon coordinates, dark/zero LAI/opaque/reflective
cover/full construction interception, linear radiation scaling, residuals,
closed-schema/units/identities/immutability and numerical holds. An independent
original-form electron transport calculation must agree with the **actual existing
crop consumer** using incident photons, and detect double interception using
absorbed photons. This is an instantaneous composition test; RK stages, new
checkpoint/model binding, stored results/API/3D and user deployment remain later
slices. Existing five live roots, sources and user UI are protected during checks.
