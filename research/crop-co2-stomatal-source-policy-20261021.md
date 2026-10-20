# CO₂ mass, concentration and stomatal source review — 2026-10-21 KST

Decision record: `co2-source-review-20261021-v1`. This completes source and
development-boundary review only. The [machine register](crop-co2-stomatal-source-register-20261021.json)
contains the retrieved versions, hashes, exact JSON pointers, units, rights and
reviewer. Existing numerical profiles, saved results and running previews were
preserved. Claim and development authority remains [PROJECT_SPEC §5.3](../docs/PROJECT_SPEC.md#53-개발-착수와-결과-게시).

## Decisions and remaining holds

| Decision | Disposition | Consequence |
| --- | --- | --- |
| P01: explicit ideal-gas concentration conversion | Accepted for a new software research kernel, using the pinned C8 numerical R/M conventions and explicit temperature, pressure and wet/dry basis | Start scalar conversion independently of catalogue/U1 capacity and dynamic stomatal closure. This is a pressure-explicit project extension of C8's fixed-pressure helper. |
| P02: crop carbon to air CO₂ | Source relationship and existing rate-field mapping reviewed; implementation pending | Net assimilation subtracts growth and maintenance respiration. Harvest/removal is not an air flux. Preserve the source's distinct molar-mass conventions until a separately reviewed version chooses otherwise. |
| P03: implicit stomatal resistance | Hold | The source's slope unit is inconsistent; no author correction was found. Preserve the existing explicit positive resistance interface. |
| P04: observations, applicable cultivar/facility parameters and publication claims | Not adopted | Literature/code review supplies no domestic independent measurement, approved Run, or production/economic validation. See the [independent data status](crop-independent-data-status.json). |

P01 accepts a numerical development policy, not agricultural validity, a sensor
calibration, a field coefficient set or a source-data release. P03 does not block
P01 or the separate net-carbon/mass-balance development children.

## Actual review execution

The parent inspected its current native CLI `turn_context`: timestamp
`2026-10-20T17:04:07.957Z`, model `gpt-6.1-sol`, effort `xhigh`, this workspace;
event-line SHA-256 `93294e4dddecc13266a8a355d8b45a0ec1b2df52e9307c28e28a1f8aaa76beb4`.
The session creation header says `source=vscode`, `cli_version=0.157.1`;
this is creation metadata, not a current installed-binary version measurement.
No recursive CLI was launched. The `research` skill required background source
research; `/root/co2_stomatal_units_sources` was assigned the exact model/effort
and returned a private draft, SHA-256
`f202719a2c0898bb52d959cf87f5256e1e02d3c74bc1f7f25a827db025deb5b7`.
The parent read it and checked the underlying source bytes. Assignment itself
is not independent invocation proof. Public outputs of this review are this
document and its register; raw prompts, session transcript and literature PDFs
are not public outputs.

## 1. State, capacity and exchange

Pinned [GreenLight C8][c8], `/State equations/CO2 concentration states/co2Air`,
uses concentration in `mg_CO2/m3` and divides net floor-area flux by
`/Capacities/capCo2Air = hAir [m]`. Its `/CO2 fluxes/airMc(f12, c1, c2)` is
`abs(f12) * (c1 - c2)` in `mg_CO2/m2_floor/s`; `mcAirOut` applies it to the
specified side/forced ventilation. A negative signed concentration difference
therefore represents inward CO₂ in this exchange formulation. This is a
well-mixed exchange approximation; it is not a general directed advection law.

Project algebra: with fixed floor area A and volume V, `h=V/A`, `m/A=h*c`.
Mass per floor area is conserved by `d(h*c)/dt = sources - sinks`, whereas ppm
is an intensive ratio. `dc/dt=(sources-sinks)/h` requires fixed h; varying volume
needs the additional storage derivative and a separate model version. Air
temperature/pressure changes alter a concentration's ppm interpretation without
creating CO₂ mass. This reduced trace-gas balance does not solve total-air
compressibility, pressure-driven displacement or a complete dry-air mass balance.

C8 alone sets `/Crop/mcAirCan=0` for a no-crop variant. That zero must not be
silently carried into a crop-coupled calculation. [C8][c8].

## 2. Temperature, pressure and wet/dry basis

The exact C8 helper at `/Crop/co2dens2ppm(temp, dens)` is

```text
8.3144598e6 * (temp + 273.15) * dens / (101325 * 44.01e-3)
```

Its density input is **kg_CO2/m3**; the call at `/Crop/co2InPpm` multiplies
`co2Air` by `1e-6` to convert mg to kg. The helper already contains the ppm
factor. Pressure is fixed at 101325 Pa. The [author's older helper][lc]
corroborates those conventions. No retrieved C8 declaration specifies wet/dry
measurement basis. [C8][c8].

P01's explicit project convention follows ideal-gas amount accounting:

```text
T_K = T_C + 273.15
rho_kg_m3 = c_mg_m3 * 1e-6
x_CO2_wet = (rho_kg_m3 / M_CO2) / (P_total / (R * T_K))
ppm_wet = x_CO2_wet * 1e6
ppm_dry = ppm_wet / (1 - p_H2O / P_total)
```

The last expression is project algebra for a water-excluded denominator under
the same ideal-mixture assumption; it is not a declaration about the original
model's sensor basis. The [LI-COR primary manual][li] distinguishes water-vapor
dilution correction and dry-air concentration conventions and states the
ideal-gas number-density relationship. Its chamber-specific flux estimation is
not adopted here. The equations embedded as SVG images were not visually
inspected, so this review does not claim an exact transcription of those images.

Use `R=8.3144598 Pa*m3/(mol*K)` and `M_CO2=44.01e-3 kg/mol` only as the
named C8 numerical convention. The [NIST 2022 CODATA table][nist] gives a
different exact modern R; a conversion module must not silently substitute it.
Temperature in K, positive explicit pressure, finite nonnegative density and
an explicit concentration basis are required. Dry basis additionally requires
`0 <= p_H2O < P_total`; no humidity or 1-atm fallback is supplied. The numerical
domain of an ideal-gas scalar is not an empirically validated greenhouse domain.
Unknown sensor pressure/basis remains an input-adoption hold.

The first scalar does not need volume to convert **density** to ppm. Converting
total mass requires an explicit V in m3, and converting floor-area storage
requires explicit h in m3/m2_floor. These quantities must not be conflated.

## 3. Net crop sink and molar-mass conventions

[C9][c9], `/Model flows/Canopy photosynthesis/Net photosynthesis rate/mcAirCan`,
defines `mCo2/mCh2o * (mcAirBuf - mcBufAir - mcOrgAir)`.
The source has `mCo2=44e-3 mg/umol` and `mCh2o=30e-3 mg/umol`; the former
differs from C8's 44.01 g/mol converter convention. No existing profile is
modified to hide that difference. Source-reproduction identities and any future
single-molar-mass physical variant must remain distinct.

The current [rate implementation](../backend/app/crop_growth_rates.py) maps:

| Source term | Existing field | Unit |
| --- | --- | --- |
| `mcAirBuf` | `photosynthesis` | mg_CH2O/m2_floor/s |
| `mcBufAir` | `growth_respiration` | mg_CH2O/m2_floor/s |
| `mcOrgAir` | sum of `maintenance_respiration` | mg_CH2O/m2_floor/s |

The existing `photosynthesis` already applies the source photosynthetic
compensation term. Calling it gross fixation and subtracting that term again
would double-count respiration. Growth and maintenance respiration still need
their own subtraction. `removals`, fruit harvest and biomass redistribution do
not constitute CO₂ returned to greenhouse air. A signed net sink can be negative
at night and must not be clipped to zero. The next adapter must verify that its
source rate identity/profile is the reviewed one rather than accepting arbitrary
prose or incompatible model fields. [C9][c9]; [existing profile](../fixtures/crop-growth-reference-parameters-v1.json).

## 4. Stomatal unit conflict stays open

C8 `/Canopy transpiration` defines:

```text
rS = rSMin * rfRCan * rfCo2 * rfVp
rfRCan = (rCan + cEvap1) / (rCan + cEvap2)
rfCo2 = min(1.5, 1 + cEvap3 * (etaMgPpm * co2Air - 200)**2)
rfVp = min(5.8, 1 + cEvap4 * (satVp(tCan) - vpAir)**2)
sRs = 1 / (1 + exp(sRsSlope * (rCan - rCanSp)))
```

The register transcribes the day/night blends and exact parameter units/literals.
`rCan` is incident PAR+NIR energy above the canopy after the stated optical and
construction factors; it is not absorbed PAR, photon flux or outdoor radiation
alone. The old implementation also adds lamp terms absent from this pinned
solar definition. `satVp` uses denominator 238.3, which must remain distinct from
the project's older 237.3 policy. [C8][c8]; [legacy auxiliary equations][la].

`sRsSlope=-1` is declared `m W**-2`; the exponent requires an inverse radiation
flux dimension, m2/W. The [original thesis][v], printed p218 Eq8.51 and p232
Table8.1 (PDF pages222/236), and [legacy parameters][lp] line103 both repeat the
inconsistent unit. These are provenance corroboration, not a corrected-unit
source or independent field validation. PDF text was inspected; page pixels
were not. A later variant could normalize radiation explicitly by 1 W/m2 to
preserve source numeric behavior, but that would be a versioned project
interpretation. **P03 does not adopt that correction.**

Stomata use constant `etaMgPpm=0.554`, while photosynthesis uses the temperature
dependent helper. Replacing both with one conversion changes the numerical
model. A legacy comment suggesting replacement is not an implemented correction.
C9 also uses a fixed air/stomatal CO₂ ratio, not a conductance calculated from
this rS. Implementing rS alone would not validate mechanistic carbon conductance
or water-stress response. [C8][c8]; [C9][c9]; [legacy auxiliary equations][la].

## 5. Next small implementation children

1. **`co2-gas-conversion-kernel` — next:** a versioned pure scalar and contract,
   with named source R/M, explicit units/T/P/basis and no crop-model mutation.
   Compare against independent high-precision mole-count accounting, including
   wet/dry conversion, temperature/pressure changes, zero concentration,
   incompatible/nonfinite inputs and representability limits. Record numeric
   tolerances before running. An inverse round trip alone is insufficient.
2. **`co2-net-crop-sink-kernel`:** reviewed existing CH2O rate outputs to signed
   CO₂ flux; prove independent stoichiometry, nighttime source, removal exclusion,
   no second compensation subtraction and unchanged crop outputs/profile.
3. **`co2-air-mass-balance-kernel`:** explicit geometry and signed exchange,
   sources/sinks; prove no-flux mass conservation, analytic well-mixed exchange
   and air/crop transfer cancellation before short coupled integration.
4. **Stomatal decision then scalar, coupling, immutable results and same-UTC 3D:**
   P03 and scalar references are prerequisites for implicit rS substitution.
   They are not prerequisites for the first three children. The existing
   catalogue20/U1 performance hold remains a separate required product task.

Model development and independent farm access continue in parallel. Later
trajectory, resource purchase, economic and product claims retain their
existing authoritative acceptance requirements.

## Verification completed / not performed

The parent rehashed retrieved sources, parsed C8/C9 and matched the formula and
parameter pointers in the register; matched the retained BSD notice; inspected
the selected current rate fields and native CLI metadata. The bounded primary
metrology fetch exited0 in1.893104s, peak combined RSS596,652,032bytes,
FD4→4; all5 protected roots,2,148 originals and both frozen previews were
preserved, with no owned process/PG/temp/credential residue. This verifies
retrieval/reading and preservation, not a crop calculation.

No physiological kernel, product suite, browser/DB integration or deployment
was accepted by this research. Source publication times and historical public
availability remain unknown where the register says null. Source code and a
public PDF do not provide independent farm data or a validated prediction.

[c8]: https://raw.githubusercontent.com/davkat1/GreenLight/7a7b36870135aa38bbe81e65590dcf5473786bdd/greenlight/models/katzin_2021/definition/vanthoor_2011/greenhouse_vanthoor_2011_chapter_8.json
[c9]: https://raw.githubusercontent.com/davkat1/GreenLight/7a7b36870135aa38bbe81e65590dcf5473786bdd/greenlight/models/katzin_2021/definition/vanthoor_2011/crop_vanthoor_2011_chapter_9_simplified.json
[lc]: https://raw.githubusercontent.com/davkat1/GreenLight/4ec6018e0aad2775ad11085d34f3886a7b7dd052/Code/serviceFunctions/co2dens2ppm.m
[lp]: https://raw.githubusercontent.com/davkat1/GreenLight/4ec6018e0aad2775ad11085d34f3886a7b7dd052/Code/createGreenLightModel/setGlParams.m
[la]: https://raw.githubusercontent.com/davkat1/GreenLight/4ec6018e0aad2775ad11085d34f3886a7b7dd052/Code/createGreenLightModel/setGlAux.m
[v]: https://edepot.wur.nl/170301
[li]: https://www.licor.com/support/LI-8250/topics/deriving-the-flux-equation-co2.html
[nist]: https://physics.nist.gov/cuu/Constants/Table/allascii.txt
