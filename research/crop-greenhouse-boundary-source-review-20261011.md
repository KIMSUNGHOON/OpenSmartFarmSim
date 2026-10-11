# Greenhouse boundary source review — 2026-10-11

The first implementable child is a **pure ventilation sensible/vapor boundary**, using an explicit nonnegative volume exchange per floor area and the existing joint model's explicit vapor gas constant. It returns signed outward fluxes and the opposite inward forcings. This removes two prescribed boundary terms through a deterministic physical calculation while retaining the current crop/canopy contracts. Radiation, CO₂ storage, stomatal resistance, facility flow estimation, and field applicability remain separate dependencies.

This is a source review and a proposed small calculation boundary. It does not adopt farm observations, supply missing facility coefficients, accept an implementation, or complete the greenhouse/crop coupling parent. Context: [coupling contract](../contracts/crop-climate-coupling-v1.md), [joint RHS](../contracts/crop-climate-joint-rhs-v1.md), [earlier canopy review](crop-canopy-exchange-baseline-20261009.md), and [source register](crop-canopy-exchange-source-register-20261009.json).

Reviewer: delegated agent `/root/greenhouse_boundary_sources`, assigned `gpt-6.1-sol / xhigh`. Actual native CLI invocation/session/turn-event metadata is **unavailable to this delegated agent**; the task assignment is not independent invocation proof. The parent records its actual native CLI context separately. No CLI was launched recursively, and no further agents were spawned. The `engineering-suite:research` workflow supplied this delegated primary-source task.

## Primary-source retrieval and rights

All sources below are pinned to GreenLight commit/product ID `7a7b36870135aa38bbe81e65590dcf5473786bdd`. `observed_at=null`: these are model definitions and a license, not agricultural observations. `published_at=null` and `available_at=null`: first public availability was not reconstructed. A file creation statement or commit timestamp is not accepted as a publication/decision-availability time. The vintage is the full commit ID; no newer revision was substituted.

| Source ID and primary URL | Retrieval UTC; bytes; SHA-256 | Units and QC |
| --- | --- | --- |
| `chapter8`: [greenhouse_vanthoor_2011_chapter_8.json](https://raw.githubusercontent.com/davkat1/GreenLight/7a7b36870135aa38bbe81e65590dcf5473786bdd/greenlight/models/katzin_2021/definition/vanthoor_2011/greenhouse_vanthoor_2011_chapter_8.json) | `2026-10-11T12:29:59.759538+00:00`; 130,649; `c0fb7a025533f15b80cb6cd60aafdc19be9fe42df6b8183cf97b83fc086138b3` | JSON parsed; exact expressions/pointers inspected below; bytes/hash match earlier register. Quantity-specific units; area, vapor conversion, CO₂ conversion, and switch-slope qualifications below. No empirical accuracy domain established. |
| `license`: [LICENSE.txt](https://raw.githubusercontent.com/davkat1/GreenLight/7a7b36870135aa38bbe81e65590dcf5473786bdd/LICENSE.txt) | `2026-10-11T12:29:59.951354+00:00`; 1,716; `96ce8c1f3d7b5473f473417c2785c63b74148edaddc2b9b6d40a6bbe3b7f4b6a` | Units not applicable. Exact notice matches [retained notice](../LICENSES/GreenLight-BSD-3-Clause-Clear.txt). |
| `chapter9`: [crop_vanthoor_2011_chapter_9_simplified.json](https://raw.githubusercontent.com/davkat1/GreenLight/7a7b36870135aa38bbe81e65590dcf5473786bdd/greenlight/models/katzin_2021/definition/vanthoor_2011/crop_vanthoor_2011_chapter_9_simplified.json) | `2026-10-11T12:31:45.848580+00:00`; 26,741; `272a589edf0bb40d1a91b34e883f8e94b9adf747a576be4620c50296c03d7033` | JSON parsed; crop CO₂ sink and PAR interface inspected. Bytes/hash match existing growth profile/source register. CH₂O and CO₂ mass are different quantities. |
| `standalone`: [extension_crop_vanthoor_2011_for_standalone.json](https://raw.githubusercontent.com/davkat1/GreenLight/7a7b36870135aa38bbe81e65590dcf5473786bdd/greenlight/models/katzin_2021/definition/vanthoor_2011/extension_crop_vanthoor_2011_for_standalone.json) | `2026-10-11T12:31:46.040612+00:00`; 3,895; `74bf4f3ebc3100945de834433b210984c7a75c78c58218e5f7d5b4bd1c82ea49` | JSON parsed; incident/absorbed PAR and optical constants inspected. Bytes/hash match existing growth profile/source register. |

Reviewer for each retrieval is the delegated agent identified above; these records are `reference_software_equations_only_not_G0_data`. Raw responses were inspected in memory and were not written as new artifacts because the authorized output is this one note. Hashes identify observed bytes; this does not supply a new immutable adopted-data snapshot.

Rights for all three code files: the pinned license permits use and source/binary redistribution with conditions. Source redistribution retains copyright, conditions, and disclaimer; binary redistribution reproduces them in accompanying documentation/materials. Display/reuse must preserve the relevant notice and must not imply endorsement. The copyright notice identifies David Katzin and Wageningen Research Foundation, 2025. No patent rights are granted; warranty and liability disclaimers apply. The existing retained notice is the appropriate preservation artifact. These permissions do not extend automatically to cited papers, linked datasets, or separately owned images. No such raw content is included here. [Pinned license](https://raw.githubusercontent.com/davkat1/GreenLight/7a7b36870135aa38bbe81e65590dcf5473786bdd/LICENSE.txt).

## Ventilation: exact source and proposed reduced boundary

The following are exact source `definition` strings. Pointers are within `chapter8`; source fluxes are per square meter of greenhouse floor by the accompanying volume-per-floor flow units and state capacities. The source often prints only `m**-2`; the explicit floor label below is the project's area-basis interpretation.

| JSON pointer | Exact expression | Source unit |
| --- | --- | --- |
| `/Heat fluxes/Convection and conduction/sensible(hec, t1, t2)` | `abs(hec) * (t1 - t2)` | `W m**-2` |
| `/Heat fluxes/Convection and conduction/Table 8.4/hAirOut` | `sensible(rhoAirCap * cPAir * (fVentSide + fVentForced), tAir, tOut)` | `W m**-2` |
| `/Vapour fluxes/airMv(f12, vp1, vp2, t1, t2)` | `(18 / 8314) * abs(f12) * (vp1 / (t1 + 273.15) - vp2 / (t2 + 273.15))` | `kg m**-2 s**-1` |
| `/Vapour fluxes/mvAirOut` | `airMv(fVentSide+fVentForced, vpAir, vpOut, tAir, tOut)` | `kg m**-2 s**-1` |
| `/Heat fluxes/Convection and conduction/Table 8.4/hTopOut` | `sensible(rhoAirCap * cPAir * fVentRoof, tTop, tOut)` | `W m**-2` |
| `/Vapour fluxes/mvTopOut` | `airMv(fVentRoof, vpTop, vpOut, tTop, tOut)` | `kg m**-2 s**-1` |

The main compartment source temperature equation subtracts `hAirOut`; its vapor equation subtracts `mvAirOut`. Thus positive outward quantities become negative inward forcings. `abs(f12)` sets the magnitude of air exchange; the transported heat/mass still takes its sign from the temperature/density difference. The source description saying that sensible heat always flows “from 1 to 2” must not override the signed expression when `t1<t2`. The vapor expression compares **vapor density**, not pressure alone, because each pressure is divided by its own absolute temperature. [Chapter 8](https://raw.githubusercontent.com/davkat1/GreenLight/7a7b36870135aa38bbe81e65590dcf5473786bdd/greenlight/models/katzin_2021/definition/vanthoor_2011/greenhouse_vanthoor_2011_chapter_8.json).

For the first child define these explicit inputs: `f≥0 [m3/m2_floor/s]`, `Tair,Tout [degC]`, indoor `m_v≥0 [kg_water/m2_floor]`, `h=V/A>0 [m3/m2_floor]`, `rhoAirCap>0 [kg_air/m3]`, the **same** explicit `Rv>0 [J/kg_water/K]` as the joint model, and `vpOut≥0 [Pa]`. Reuse the accepted exchange profile's `cp [J/kg_air/K]` and `L [J/kg_water]`; do not introduce a second copy or default facility values.

Project reduction, derived from the current mass state and ideal-gas pressure relation:

```text
Tk_in  = Tair + 273.15
Tk_out = Tout + 273.15
rho_v_in  = m_v/h
rho_v_out = vpOut/(Rv*Tk_out)
vp_in    = rho_v_in*Rv*Tk_in       # diagnostic consistency with existing joint state

Hout  = rhoAirCap*cp*f*(Tair-Tout)  [W/m2_floor, signed outward]
MVout = f*(rho_v_in-rho_v_out)     [kg_water/m2_floor/s, signed outward]
Qair_vent = -Hout
Fv_vent   = -MVout
latent_out = L*MVout               [W/m2_floor, separate vapor-energy ledger]
```

This is an **ideal-gas reduced project variant**, rather than an exact reconstruction of GreenLight's vapor closure for every admissible `Rv`. Source `/Parameters/Table 8.1/mWater=18 [kg/kmol]` and `/Parameters/Table 8.1/R=8314 [J/kmol/K]` give `Rv_source=8314/18`. Substitution of `vp_in=(m_v/h)*Rv*Tk_in` into the original `airMv` makes the expressions identical when `Rv=Rv_source`. An explicit `Rv=461.5`, used in existing synthetic joint inputs, differs from that ratio. Retain the explicit value and the declared model identity; do not claim source equality or silently change the joint input to make a test pass. [Chapter 8](https://raw.githubusercontent.com/davkat1/GreenLight/7a7b36870135aa38bbe81e65590dcf5473786bdd/greenlight/models/katzin_2021/definition/vanthoor_2011/greenhouse_vanthoor_2011_chapter_8.json).

Dimensional derivation:

```text
rhoAirCap*cp*f*dT:
 (kg_air/m3)*(J/kg_air/K)*(m3/m2_floor/s)*K = W/m2_floor
vp/(Rv*Tk):
 Pa/[(J/kg_water/K)*K] = (J/m3)/(J/kg_water) = kg_water/m3
f*delta(rho_v):
 (m3/m2_floor/s)*(kg_water/m3) = kg_water/m2_floor/s
L*MVout = W/m2_floor
f/h = 1/s
```

`rhoAirCap` is the source's sensible capacity density, distinct from water-vapor density and from any later dynamic moist/dry-air density. Kelvin conversion is required in gas-law denominators; Celsius temperature differences already equal Kelvin differences. The source's `18/8314` is not a dimensionless correction factor.

The explicit `f` represents one declared well-mixed main-air/outdoor exchange. GreenLight has separate main and top compartments; its roof flow is coupled to `tTop/vpTop`. Adding roof and side rates while using only main-compartment state would be a further reduction. Natural-ventilation formulas additionally require geometry, wind, openings, discharge/wind coefficients, leakage, screen properties, and screen control; the first child does not infer them. The source declares `fVentSide/fVentRoof/fVentForced` in `m**3 m**-2 s**-1`. Air changes per hour would require the independently declared conversion `f=ACH*h/3600`; ACH must not be accepted under the volume-per-floor unit. [Chapter 8, natural/forced ventilation sections](https://raw.githubusercontent.com/davkat1/GreenLight/7a7b36870135aa38bbe81e65590dcf5473786bdd/greenlight/models/katzin_2021/definition/vanthoor_2011/greenhouse_vanthoor_2011_chapter_8.json).

At a later shared-stage integration, use `Qair=Qair_other-Hout` and `Fv=Fv_other-MVout` exactly once. `latent_out` is diagnostic accounting for the energy carried by vapor. It must **not** be added to or subtracted from the air sensible derivative. With the existing reduced store and material transport:

```text
Uref' + Cair*Tair' + L*m_v'
 = Qcan + Qair_other - Hout + L*(Fv_other-MVout) + Qmaterial
```

This bookkeeping excludes vapor/liquid sensible enthalpy, pressure work, and other omitted greenhouse stores, as the existing joint contract does. It is not total farm energy or water conservation. The first pure boundary child supplies instantaneous quantities only; fixed forcings in an existing integrator must not be relabeled as dynamically recomputed ventilation.

## Narrow implementation and independent acceptance proposal

The suggested core remains five new files: pure boundary module, focused tests, its contract, an independent Decimal reference generator, and its synthetic fixture. The existing joint source, profiles, stored results, and running previews need no mutation for this child. A later small adapter/integration acceptance must prove reevaluation from each current joint stage; completion of the pure boundary is not that proof.

All required values must be explicit and unit-checked. Reject bool/string numerics, missing/extra fields, nonfinite values, negative `f/m_v/vpOut`, nonpositive `h/rhoAirCap/Rv`, invalid absolute temperature, and nonrepresentable operations. Do not use `abs` to turn a negative caller flow into a valid input. The existing parent retains its accepted indoor temperature/saturation/domain guards. Outdoor temperature limits and any outdoor saturation/QC policy must be declared in the new contract; the ideal-gas expression alone supplies no empirical outdoor accuracy range. Missing outdoor vapor pressure is a hold, not dry air. A zero flow still needs a valid complete input.

Suggested independent numerical acceptance, to be fixed in that contract before running it:

1. Use Decimal precision 80 without importing the product boundary or obtaining expected values through it. Independently calculate all densities, inward/outward fluxes, latent ledger, and algebraic balances. Reuse pinned input/profile literals while keeping the arithmetic independent. A candidate binary64 comparison is relative `3e-13` for nonzero expected scalars and absolute `5e-14` in each declared output unit for expected zeros; identify these as software arithmetic tolerances, not field accuracy.
2. Cover `f=0`; equal indoor/outdoor temperature and density; hot/dry and cold/moist outside; heat and vapor moving in opposite directions; nonzero mass with varying indoor temperature; zero vapor mass; and explicit zero outdoor pressure. Require signed conservation without clipping or forcing matching signs.
3. Use an equal-**density** case with different temperatures: vapor exchange is zero even though pressures differ. Use equal **pressure** with different temperatures: vapor exchange is generally nonzero. Both catch replacement of the gas-law density difference with a pressure difference or an indoor-temperature denominator for both sides.
4. At `Rv=8314/18`, reconstruct the original `airMv` independently in Decimal and prove equality with the project reduction. At explicit `Rv=461.5`, calculate both variants separately and preserve the documented difference. Do not treat the source variant as the expected value for the new model variant.
5. Check direct relations `Qair_vent+Hout=0`, `Fv_vent+MVout=0`, and `latent_out-L*MVout=0`; check floor-area normalization, no extra `h` division in a flux, and exactly one later whole-area multiplication. Test invalid and overflow/underflow cases with no mutated input. If tiny nonzero fluxes disappear in binary64, follow the existing explicit numerical-hold policy rather than reporting exact physical equilibrium.
6. For the later stage adapter, prove a changed stage `Tair/m_v` changes its ventilation terms; preserve canopy `H/LE/E` and do not insert `L*Fv` into sensible air heat. With canopy terms disabled and constant outside inputs, independent analytic checks are available: `Tair-Tout` and `m_v-h*rho_v_out` each decay as `exp(-f*t/h)` under `Cair=h*rhoAirCap*cp`. This is a derived limiting test, not an instruction to run a new trajectory in this source-review task.

No such acceptance run was performed by this review agent. The proposal supplies a reviewable calculation boundary and tests that can falsify common unit/sign/double-counting errors.

## Solar radiation, PAR interception, and canopy absorbed heat

Source `chapter8`, section `/Heat fluxes/Global, PAR and NIR heat fluxes`, uses **energy** fluxes first:

```text
rParGhSun       = (1-etaGlobAir)*tauCovPar*etaGlobPar*iGlob
rParSunCanDn    = rParGhSun*(1-rhoCanPar)*(1-exp(-k1Par*lai))
rParSunFlrCanUp = rParGhSun*exp(-k1Par*lai)*rhoFlrPar*(1-rhoCanPar)
                  *(1-exp(-k2Par*lai))
rParSunCan      = rParSunCanDn+rParSunFlrCanUp
rNirSunCan      = (1-etaGlobAir)*aCanNir*etaGlobNir*iGlob
parCan          = parJtoUmolSun*rParSunCan
```

Each symbol is also its exact final pointer segment. `iGlob` is outdoor global solar radiation; each `r...` here is `W m**-2`. `parCan` is absorbed `µmol_photons m**-2 s**-1`. `/Parameters/parJtoUmolSun=4.6 [umol_photons/J]` is the source's **solar PAR** conversion; `/Parameters/Table 8.1/etaGlobPar` and `etaGlobNir` are separate energy fractions (both `0.5` in that reference). These are pinned reference parameters, not approved spectra/facility defaults. `etaGlobAir` is the construction absorption fraction, not an air-heat term automatically available to the reduced air store. [Chapter 8](https://raw.githubusercontent.com/davkat1/GreenLight/7a7b36870135aa38bbe81e65590dcf5473786bdd/greenlight/models/katzin_2021/definition/vanthoor_2011/greenhouse_vanthoor_2011_chapter_8.json).

The `chapter8` canopy temperature RHS at `/State equations/Temperature states/tCan` includes `rParSunCan+rNirSunCan`, with additional pipe/longwave exchanges and canopy sensible/latent losses. A source-backed solar-only contribution to a future reduced `Qcan` is therefore `Qcan_solar=rParSunCan+rNirSunCan`, while the remaining exchanges retain their own explicit boundaries. Neither `parCan/4.6` nor `rParSunCan` represents total absorbed solar energy, and `iGlob*4.6` is not above-canopy PAR. Electrical lamps require their own spectrum/conversion and optical path. [Chapter 8](https://raw.githubusercontent.com/davkat1/GreenLight/7a7b36870135aa38bbe81e65590dcf5473786bdd/greenlight/models/katzin_2021/definition/vanthoor_2011/greenhouse_vanthoor_2011_chapter_8.json).

The current [crop rate module](../backend/app/crop_growth_rates.py) already applies the `standalone` `/Auxiliary states/parGhCan` and `/Auxiliary states/parFlrCan` interception to `par_above_canopy`. Its existing optical constants match the source's `k1Par/k2Par/rhoCanPar/rhoFlrPar`. Consequently, a later solar boundary must pass:

```text
joint.par_above_canopy = parJtoUmolSun*rParGhSun
```

Then the crop's absorbed photon flux equals source `parCan` when the same LAI and optical constants are used. Passing `parJtoUmolSun*rParSunCan` into that **above-canopy** field would intercept radiation twice. This equality follows algebraically from the two primary definitions; it does not establish field optical accuracy. [Standalone source](https://raw.githubusercontent.com/davkat1/GreenLight/7a7b36870135aa38bbe81e65590dcf5473786bdd/greenlight/models/katzin_2021/definition/vanthoor_2011/extension_crop_vanthoor_2011_for_standalone.json), [Chapter 8](https://raw.githubusercontent.com/davkat1/GreenLight/7a7b36870135aa38bbe81e65590dcf5473786bdd/greenlight/models/katzin_2021/definition/vanthoor_2011/greenhouse_vanthoor_2011_chapter_8.json).

NIR cannot be replaced by the PAR interception coefficient. Source pointers in the same `chapter8` heat section define `tauHatCovNir=1-rhoCovNir`, `tauHatFlrNir=1-rhoFlrNir`, `tauHatCanNir=exp(-kNir*lai)`, and `rhoHatCanNir=rhoCanNir*(1-tauHatCanNir)`. It combines cover/canopy and then floor with `/Lumped cover layers/functions/tau12(...)`, `rhoUp(...)`, and `rhoDn(...)`; finally `aCanNir=1-tauCovCanFlrNir-rhoCovCanFlrNir`. The virtual nonabsorbing cover/floor construction is part of this source approximation. A later adoption must reproduce its full ordering/reflections and test denominators, coefficient bounds, `LAI=0`, and partition balances; an invented Beer-law NIR factor is not equivalent. [Chapter 8](https://raw.githubusercontent.com/davkat1/GreenLight/7a7b36870135aa38bbe81e65590dcf5473786bdd/greenlight/models/katzin_2021/definition/vanthoor_2011/greenhouse_vanthoor_2011_chapter_8.json).

For reproducibility, the source layer functions use arguments `(tau1,tau2,rho1Up,rho1Dn,rho2Up,rho2Dn)` and the following exact algebra, with whitespace normalized:

```text
tau12 = tau1*tau2/(1-rho1Dn*rho2Up)
rhoUp = rho1Up+tau1**2*rho2Up/(1-rho1Dn*rho2Up)
rhoDn = rho2Dn+tau2**2*rho1Dn/(1-rho1Dn*rho2Up)
```

The NIR heat-section pointers call those functions as follows:

```text
tauCovCanNir = tau12(tauHatCovNir,tauHatCanNir,
                     rhoCovNir,rhoCovNir,rhoHatCanNir,rhoHatCanNir)
rhoCovCanNirUp = rhoUp(tauHatCovNir,tauHatCanNir,
                       rhoCovNir,rhoCovNir,rhoHatCanNir,rhoHatCanNir)
rhoCovCanNirDn = rhoDn(tauHatCovNir,tauHatCanNir,
                       rhoCovNir,rhoCovNir,rhoHatCanNir,rhoHatCanNir)
tauCovCanFlrNir = tau12(tauCovCanNir,tauHatFlrNir,
                        rhoCovCanNirUp,rhoCovCanNirDn,rhoFlrNir,rhoFlrNir)
rhoCovCanFlrNir = rhoUp(tauCovCanNir,tauHatFlrNir,
                       rhoCovCanNirUp,rhoCovCanNirDn,rhoFlrNir,rhoFlrNir)
aCanNir = 1-tauCovCanFlrNir-rhoCovCanFlrNir
aFlrNir = tauCovCanFlrNir
```

These are dimensionless optical expressions. Neither replacing `tauHatCovNir` with actual `tauCovNir` nor multiplying `rNirSunCan` by another canopy/cover transmission is an exact reproduction of the pinned source. Any proposed physical correction requires its own recorded model variant. [Chapter 8](https://raw.githubusercontent.com/davkat1/GreenLight/7a7b36870135aa38bbe81e65590dcf5473786bdd/greenlight/models/katzin_2021/definition/vanthoor_2011/greenhouse_vanthoor_2011_chapter_8.json).

Missing radiation inputs remain holds: valid outdoor radiation and time meaning, spectral fractions/conversion basis, cover/screen/floor optics and positions, construction absorption, applicable LAI/optics, and remaining canopy heat exchanges. A smaller radiation child may first establish solar PAR plus its own energy partition, with NIR still an explicit separately identified heat input; it must not label that partial result total solar heating.

## CO₂: mass state, ppm conversion, and crop sink

Exact `chapter8` source definitions:

| Pointer | Definition and meaning |
| --- | --- |
| `/State equations/CO2 concentration states/co2Air` | `(1/capCo2Air) * (mcBlowAir + mcExtAir + mcPadAir - mcAirCan - mcAirTop - mcAirOut)`; state unit `mg_CO2/m3` |
| `/Capacities/capCo2Air` | `hAir`; unit `m`, equivalently volume per floor area |
| `/CO2 fluxes/airMc(f12, c1, c2)` | `abs(f12) * (c1 - c2)`; `mg_CO2/m2_floor/s` |
| `/CO2 fluxes/mcAirOut` | `airMc(fVentSide + fVentForced, co2Air, co2Out)` |
| `/Crop/co2InPpm` | `co2dens2ppm(tAir, (1e-6 * co2Air))` |
| `/Crop/co2dens2ppm(temp, dens)` | `8.3144598e6* (temp + 273.15) * dens / (101325 * 44.01e-3)`; density argument is `kg_CO2/m3`, output molar ppm; assumes 1 atm |
| `/Parameters/Table 8.1/etaMgPpm` | `0.554`; constant factor `ppm mg**-1 m**3`, used by stomatal `rfCo2` |

The `1e-6` density conversion is **mg to kg**, not ppm scaling. The conversion function contains the `10^6` ppm factor in its numerator. Its explicit pressure assumption and `44.01e-3 kg/mol` basis differ from treating `etaMgPpm` as a universally valid conversion. Both paths coexist in the pinned source; they are not identical for arbitrary temperatures. A new dynamic model should pick and name one conversion policy with explicit pressure or explicitly pinned 1-atm applicability, rather than mixing them between crop and stomatal calculations. [Chapter 8](https://raw.githubusercontent.com/davkat1/GreenLight/7a7b36870135aa38bbe81e65590dcf5473786bdd/greenlight/models/katzin_2021/definition/vanthoor_2011/greenhouse_vanthoor_2011_chapter_8.json).

For a fixed-volume reduction, a possible later state is `m_CO2=h*c_CO2 [mg_CO2/m2_floor]`. Then `c_CO2=m_CO2/h`, outward exchange is `f*(c_in-c_out)`, and the gas-law ppm conversion is derived at each current stage temperature. ppm is a concentration ratio and is not a conserved mass state. Temperature changes can change ppm at fixed volume/mass under the chosen fixed-pressure ideal-gas conversion; the thermodynamic pressure/volume approximation must remain explicit.

`chapter8` alone has `/Crop/mcAirCan=0` under its no-crop assumption. Actual net crop uptake is defined by `chapter9` `/Model flows/Canopy photosynthesis/Net photosynthesis rate/mcAirCan` as:

```text
mCo2/mCh2o * (mcAirBuf-mcBufAir-mcOrgAir)
```

It uses net assimilation after the defined buffer and organ respiration terms, with molar-mass conversion from CH₂O to CO₂. Thus the new air sink must not be gross photosynthesis alone, whole leaf biomass change, or an unconverted CH₂O flux. Source `/Parameters/mCo2` is `44e-3 [mg/umol]`; this is a different pinned convention from the conversion function's `44.01e-3 kg/mol`. A later child must preserve the existing crop parameter convention or explicitly version/review a correction. It also needs initial air CO₂ mass, outdoor CO₂ quantity/basis, injection terms, pressure policy, and common-stage sink/crop forcing; none is supplied by the ventilation child. [Chapter 9](https://raw.githubusercontent.com/davkat1/GreenLight/7a7b36870135aa38bbe81e65590dcf5473786bdd/greenlight/models/katzin_2021/definition/vanthoor_2011/crop_vanthoor_2011_chapter_9_simplified.json).

## Stomatal closure: unresolved switch-slope dimension

In `chapter8`, `/Canopy transpiration/rS` is `rSMin * rfRCan * rfCo2 * rfVp`. `rfRCan=(rCan+cEvap1)/(rCan+cEvap2)` uses total above-canopy **PAR+NIR energy**. `/Canopy transpiration/rCanSun` is `(1-etaGlobAir)*(tauCovPar*etaGlobPar+tauCovNir*etaGlobNir)*iGlob`; `rCan=rCanSun`. This is not absorbed PAR, photon PAR, or full outdoor solar radiation. `rfCo2` uses the source's constant `etaMgPpm*co2Air`; `rfVp` uses canopy saturation minus indoor vapor pressure. Both source factors apply stated caps. [Chapter 8](https://raw.githubusercontent.com/davkat1/GreenLight/7a7b36870135aa38bbe81e65590dcf5473786bdd/greenlight/models/katzin_2021/definition/vanthoor_2011/greenhouse_vanthoor_2011_chapter_8.json).

The exact source relationships, with whitespace normalized, are:

```text
rfCo2 = min(1.5,1+cEvap3*(etaMgPpm*co2Air-200)**2)
rfVp  = min(5.8,1+cEvap4*(satVp(tCan)-vpAir)**2)
cEvap3 = cEvap3Night*(1-sRs)+cEvap3Day*sRs
cEvap4 = cEvap4Night*(1-sRs)+cEvap4Day*sRs
```

Their final pointer segments are under `/Canopy transpiration`; `cEvap3` has `ppm_CO2^-2` and `cEvap4` has `Pa^-2`. These source values/caps are facts about the pinned model, not new field-calibrated defaults. [Chapter 8](https://raw.githubusercontent.com/davkat1/GreenLight/7a7b36870135aa38bbe81e65590dcf5473786bdd/greenlight/models/katzin_2021/definition/vanthoor_2011/greenhouse_vanthoor_2011_chapter_8.json).

The switch is exactly `/Canopy transpiration/sRs = 1 / (1 + exp(sRsSlope * (rCan - rCanSp)))`. Source `/Parameters/Table 8.1/rCanSp` has `W m**-2`, but `sRsSlope` is declared `m W**-2` with literal `-1`. Multiplying the declared units gives `m^-1 W^-1`, not a dimensionless exponential argument. The dimensionally required slope is `m2/W` (inverse radiation flux). This review identifies a metadata conflict; it does not authorize silently relabeling the source parameter or claiming that a numerically unchanged `-1` has been independently validated.

The sign/literal gives an increasing daylight switch as radiation rises; that algebraic fact does not resolve the units. The day/night coefficient blends also need their own exact pointer/literal pinning, stable logistic evaluation, and unit review. Keep the currently explicit positive `rS` for the first ventilation child. A later stomatal child requires a recorded interpretation/correction with a new version, source-faithful coefficient treatment, consistent CO₂ conversion, and independent checks; otherwise hold. [Chapter 8](https://raw.githubusercontent.com/davkat1/GreenLight/7a7b36870135aa38bbe81e65590dcf5473786bdd/greenlight/models/katzin_2021/definition/vanthoor_2011/greenhouse_vanthoor_2011_chapter_8.json).

## Dependency result and preservation evidence

| Small child | Evidence it can add; remaining hold |
| --- | --- |
| Explicit ventilation boundary | Independent instantaneous signed sensible/vapor exchange using current mass/temperature; no facility flow prediction or trajectory claim. |
| Shared-stage ventilation integration | Recompute the accepted boundary at each actual crop/climate stage; independently verify short trajectories, energy/water ledgers, convergence, events and changed model identity. |
| Solar/PAR and canopy absorbed shortwave | Separate incident PAR photons, absorbed PAR energy, and NIR; match crop interception once; pin optical and spectral inputs. Longwave/cover/floor/heater effects retain explicit missing boundaries. |
| Dynamic CO₂ | New conserved mass state and versioned state/continuation policy, conversion/pressure basis, injection/outdoor exchange and net crop sink at the same stage. |
| Stomatal resistance | Resolve `sRsSlope` dimensional conflict and CO₂ conversion consistency before replacing explicit `rS`. |

The whole greenhouse/crop coupling remains incomplete after any single row. Actual cultivar/facility applicability, independently measured climate/resource/crop data, and the corresponding product claim gates remain held under the authoritative documents. This research introduces no broader infrastructure proposal.

Read-only local pins observed at `2026-10-11T12:31:57.211804+00:00`:

| File | SHA-256 |
| --- | --- |
| [joint RHS source](../backend/app/crop_climate_joint_rhs.py) | `207ed32696b59f1ec8ce750db70bd10798c5c7ae8f78206df6038177e81124b8` |
| [crop rate source](../backend/app/crop_growth_rates.py) | `d8270e642dc80a747dd7d449094351369abb135a4663c3bf9fcdb1be5cd75858` |
| [exchange profile](../fixtures/crop-canopy-exchange-reference-parameters-v1.json) | `1e032ced2ffdaf8ba713184e89b628cce4173c9e7231f30710afeda8fbf20110` |
| [growth profile](../fixtures/crop-growth-reference-parameters-v1.json) | `d606d44c5ea6494820d0b182d08536524acdb88508a9f676788523b1248e83ca` |
| [retained license](../LICENSES/GreenLight-BSD-3-Clause-Clear.txt) | `96ce8c1f3d7b5473f473417c2785c63b74148edaddc2b9b6d40a6bbe3b7f4b6a` |
| [joint RHS contract](../contracts/crop-climate-joint-rhs-v1.md) | `3633bb79ed70c641990152da28f2efa3a4532f0df95976c095737f509c61e12f` |
| [coupling contract](../contracts/crop-climate-coupling-v1.md) | `f54f3f6a078eca1ddeda65d37f6a445aefe003895f8051e6a1f98a68f515aac0` |
| [earlier source register](crop-canopy-exchange-source-register-20261009.json) | `4f1f1c17671eb4631fb5c1761e1efd1927a89f987603bd95536d7a349c714bdc` |

This delegated task writes only this note. It performs source retrieval/hash/pointer inspection and local document/source reading. No tests, builds, browser or database operations, model execution, process management, git operations, or commits were performed. Private originals and live previews were not opened or modified. New implementation acceptance and product/field claims are not established by this report.

Final focused document check: 14 local links resolve, and all eight existing source/profile/contract/license pins above remain unchanged. Primary retrieval byte lengths/hashes match their earlier pins. The boundary and independent Decimal acceptance are proposed work; they were not executed here.
