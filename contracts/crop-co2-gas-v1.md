# CO₂ ideal-gas scalar v1

Status: scalar software acceptance completed; [evidence](../research/artifacts/crop-co2-gas-20261021.json).
Authority is the accepted software
development policy P01 in the [source review](../research/crop-co2-stomatal-source-policy-20261021.md)
and [register](../research/crop-co2-stomatal-source-register-20261021.json).

## Boundary and identity

`backend/app/crop_co2_gas.py` supplies two pure internal functions:

```python
density_to_ppm(*, density_mg_m3, temperature_c, pressure_pa, basis,
               water_vapor_pressure_pa=None) -> float
ppm_to_density(*, ppm, temperature_c, pressure_pa, basis,
               water_vapor_pressure_pa=None) -> float
```

Model identity: `greenlight-co2-ideal-gas-explicit-pressure-v1`.
R is8.3144598 Pa*m3/(mol*K), M_CO2 is44.01e-3 kg/mol, temperature offset273.15 K,
from pinned GreenLight C8 SHA-256
`c0fb7a025533f15b80cb6cd60aafdc19be9fe42df6b8183cf97b83fc086138b3`,
pointer `/Crop/co2dens2ppm(temp, dens)`. Retain the
[BSD notice](../LICENSES/GreenLight-BSD-3-Clause-Clear.txt).
The module exposes its model/source/code identities for a later caller's manifest.

Temperature, pressure and basis have no defaults. `basis='wet'` uses total
pressure; `basis='dry'` uses total pressure minus an explicitly supplied water
vapor pressure. Optional vapor pressure, when supplied with either basis, must
be finite and satisfy0≤p_H2O<P_total. A missing vapor value on the wet path
does not assert dry air: it is unnecessary for a total-air denominator.
The functions accept Python int/float scalars, reject bool/strings/Decimal and
nonfinite/unrepresentable numbers, and return density in mg_CO2/m3 or mole ppm
respectively. Names carry the internal units; there is no public JSON endpoint.

## Arithmetic and holds

With `T=T_C+273.15`, `P_b=P_total` for wet or `P_total-p_H2O` for dry:

```text
ppm = density_mg_m3 * R * T / (M_CO2 * P_b)
density_mg_m3 = ppm * M_CO2 * P_b / (R * T)
```

The mg→kg and mole-fraction→ppm factors cancel algebraically in these forms.
The source's101325Pa is reproduced by explicitly passing that pressure. Other
pressures are the named project extension, not an unchanged upstream helper.
No source stomatal etaMgPpm, crop44g/mol sink or modern R is substituted.

Require T_K>0, P_total>0, valid basis and nonnegative concentration. A mole
fraction above1 is physically invalid; no clipping is applied. Zero concentration
returns zero after input validation. Invalid inputs produce `Co2GasHold`.
Overflow/nonfinite results, zero floating-point denominators and nonzero values
that underflow to zero produce a numeric hold. Finite inputs do not guarantee
representable intermediate arithmetic. Near the pure-CO₂ boundary a floating
result above1e6 is held rather than clamped. No accuracy domain is implied for
real gas behavior, sensors or biological forcing.

Neither function evolves an air state, computes crop uptake/resistance,
converts a total mass without volume, or changes saved crop/thermal results.
Net sink, air mass RHS, dynamic coupling, input adoption and same-UTC result
publication are separate children. Existing explicit rS and the P03 unit hold remain.

## Acceptance fixed before execution

- Independently compute CO₂ and total/dry-air **mole counts** in an explicit
  arbitrary test volume using Decimal precision80 and g/mol rather than the
  implementation's cancelled scalar expression. For both directions over
  explicit synthetic T/P/basis cases use relative error≤3e-15, absolute0;
  zero must be exact. Round trips alone do not establish acceptance.
- Verify temperature/pressure and water dilution behavior, zero, numeric/domain
  boundaries, explicit missing basis/pressure, and nonfinite/overflow/underflow
  holds. Match constants/source identity to the reviewed register.
- Focused pytest under the existing WSL guard; unchanged existing crop/profile/
  result sources and healthy5root/previews/originals; no DB, browser or external
  API activity in the scalar tests. Record actual checks and remaining scope.

## Observed acceptance — 2026-10-21 KST

The first reference run errored because the module was absent; it is an absence
check, not a numerical counterexample. After implementation, the entire focused
file passed35 tests in0.17s; the guard's child exit0/wall0.594567s, combined peak
RSS626,315,264bytes, FD4→4, all5root/2,148originals/frozen previews preserved,
owned process/PG/temp/credential residue0. The near-water-only reference uses
Decimal's exact binary-float input conversion so that subtracting nearly equal
pressures tests the supplied scalar rather than a rounded decimal replacement.

Existing crop/stomatal numerical modules and profiles are unchanged. No DB or
browser test, whole-product suite, dynamic mass balance, field accuracy or
deployment is accepted by these35 scalar checks. Next: the separately reviewed
net crop-carbon sink, then air mass RHS and coupled integration.
