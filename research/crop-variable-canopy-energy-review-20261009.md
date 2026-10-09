# Variable canopy capacity and energy transport review — 2026-10-09

## Decision proposed for review

The next small child should define **gross thermal capacity transport and partial leaf removal**, before implementing a joint crop and climate RHS. It can use the accepted crop allocation and loss rates, but must identify their conversion to thermal capacity as an explicit synthetic model choice. It must not identify carbohydrate inventory with leaf water mass or claim a measured canopy energy model.

Use fixed, explicit `capLeaf` and the pinned, fixed `sla` to represent `C = capLeaf * sla * leaf`. Keep allocation, maintenance and removal separate. Require an explicit incoming capacity temperature `Tin`; outgoing capacity leaves at the current canopy temperature. Represent canopy energy relative to an explicit reference temperature as a signed quantity `Uref = C * (Tc - Tref)`. A subsequent joint integrator should advance `Uref` and leaf inventory and derive `Tc` at every stage. The first child can expose the capacity transport/event kernel without introducing that new integration state yet.

This is a proposed **open storage closure for synthetic software experiments**. The reviewed source equations do not establish the physical validity of assigning canopy capacity loss to maintenance carbohydrate respiration. No new physical coefficient or dataset is adopted. Actual cultivar runs, actual farm runs and domestic independent datasets remain **0**; G0–G4 remain `not_assessed`/`hold`. The original completed replay, source `7ff954b` and user preview `24180` remain outside this task.

## Execution and evidence boundary

This note is the output of the background research agent requested by the applied `engineering-suite:research` skill. The parent explicitly reports this agent's invocation as `model=gpt-6.1-sol`, `reasoning_effort=xhigh`, `fork_turns=none`, in the existing native Codex CLI workflow. This is an orchestration attestation, not an independently recovered CLI event record.

| Invocation field | Recorded evidence |
| --- | --- |
| Agent | `/root/canopy_thermal_interface_audit` |
| Requested and parent-attested model / effort | `gpt-6.1-sol` / `xhigh` |
| Own native CLI command / session ID / turn-event ID | `unavailable` / `null` / `null` |
| Own invocation context hash | `null`; no parent's or previous research turn's hash reused |
| Additional or recursive Codex CLI launches | `0` |
| Output | This Markdown file only |
| Implementation edits, model tests, builds, browsers, PostgreSQL or process lifecycle actions | `0` for this task |
| Research operations | Read current source/contracts; retrieve primary documents; compute byte hashes; inspect this file and local links |
| Reviewer / adoption decision | Background research agent / independent parent review pending; no source or coefficient adoption |

The starting checkout was `9fba4465cefdf67e4558764a76a4fbf143c897c3`, with a clean worktree. The fixed LAI child `ec18ea6` was already accepted according to [its implementation evidence](crop-canopy-air-dynamics-implementation-20261009.md). Its reported checks are prior evidence, not checks run by this research agent. The [earlier interface audit](crop-climate-interface-audit-20261009.md) and [current coupling contract](../contracts/crop-climate-coupling-v1.md) define the predecessor boundary.

Read scope: [agent workflow](../AGENTS.md), [README](../README.md), [product scope](../docs/PROJECT_SPEC.md), [architecture](../docs/ARCHITECTURE.md), [research baseline](../docs/RESEARCH_BASELINE.md), the contracts and code linked below. This note does not change the plan, checkboxes, production claim gates or accepted immutable results.

## 1. What the pinned source actually supplies

### Climate capacity and the temperature equation

The pinned GreenLight Chapter 8 definition expresses `capCan = capLeaf * lai` and advances `tCan` by its radiation, sensible and latent terms divided by that capacity. Its `tCan` expression has no explicit capacity derivative or growth, maintenance or pruning sensible transport term. This is a claim about that definition and the cited equation, not an exhaustive claim about every model in the thesis. See [the pinned Chapter 8 source](https://raw.githubusercontent.com/davkat1/GreenLight/7a7b36870135aa38bbe81e65590dcf5473786bdd/greenlight/models/katzin_2021/definition/vanthoor_2011/greenhouse_vanthoor_2011_chapter_8.json), pointers `/State equations/Temperature states/tCan` (Eq. 8.1) and `/Capacities/capCan` (Eq. 8.20), and [Vanthoor's thesis](https://edepot.wur.nl/170301), Chapter 8.

Fresh in-memory thesis text inspection corroborated Eq. 8.1 on [printed page 203, PDF page 207](https://edepot.wur.nl/170301#page=207) and Eq. 8.20 on [printed page 210, PDF page 214](https://edepot.wur.nl/170301#page=214). The relevant crop inventory/LAI equations appear on [printed page 245, PDF page 249](https://edepot.wur.nl/170301#page=249); growth/maintenance respiration appears on [printed page 256, PDF page 260](https://edepot.wur.nl/170301#page=260). The absence claim remains limited to the reviewed temperature/capacity expressions, rather than an exhaustive absence search of all thesis prose.

The reviewed climate equation can be written `C * Tc' = Φ`, with `Φ` the net canopy heat rate. If `C` changes, this does **not** by itself mean `Uref' = Φ`. By the product rule it implies `Uref' = Φ + (Tc - Tref) * C'`. One possible interpretation is that all new capacity arrives at `Tc`, and all lost capacity leaves at `Tc`. That interpretation needs an explicit boundary ledger; it cannot establish a different incoming temperature or the biological mechanism of the transport.

The source's `capLeaf` parameter has capacity per leaf area units; it is not a measured property of this project's cultivar. The source's small positive no-crop LAI is also not an approved empty-canopy policy. This task neither copies the coefficient into a new physical profile nor substitutes a positive epsilon for zero LAI. See the same source at `/Parameters/Table 8.1/capLeaf` and `/Crop/lai`, and [the existing exchange profile](../fixtures/crop-canopy-exchange-reference-parameters-v1.json).

### Crop carbohydrate and leaf area

The pinned crop definition supplies separate leaf allocation, maintenance and pruning flows, `cLeaf' = mcBufLeaf - mcLeafAir - mcLeafHar`, and `lai = sla * cLeaf`. The growth respiration expression charges buffer allocation separately. These are carbohydrate bookkeeping relations; they do not supply leaf water inventory, incoming tissue temperature or an energy term for that material. See [the pinned Chapter 9 definition](https://raw.githubusercontent.com/davkat1/GreenLight/7a7b36870135aa38bbe81e65590dcf5473786bdd/greenlight/models/katzin_2021/definition/vanthoor_2011/crop_vanthoor_2011_chapter_9_simplified.json), `/State variables of the model/cLeaf`, `/State variables of the model/lai`, `/Model flows/Carbohydrate flow to plant organs/mcBufLeaf`, and `/Model flows/Growth and maintenance respiration` (Eqs. 9.4–9.5, 9.43–9.45).

The combined [main definition](https://raw.githubusercontent.com/davkat1/GreenLight/7a7b36870135aa38bbe81e65590dcf5473786bdd/greenlight/models/katzin_2021/definition/vanthoor_2011/main_vanthoor_2011.json) lists greenhouse and crop definitions in `/processing_order`. Combining definitions does not introduce a missing sensible material transport expression. The [standalone crop extension](https://raw.githubusercontent.com/davkat1/GreenLight/7a7b36870135aa38bbe81e65590dcf5473786bdd/greenlight/models/katzin_2021/definition/vanthoor_2011/extension_crop_vanthoor_2011_for_standalone.json) prescribes `tCan` at `/Inputs/tCan`; that input does not answer how a growing dynamic canopy exchanges heat with incoming tissue.

The Chapter 9 source's `mcBufLeaf` metadata contains a positive area exponent in its rate unit. The project uses the documented per-floor-area correction in [the pinned growth profile](../fixtures/crop-growth-reference-parameters-v1.json); do not propagate the source metadata typo into the capacity transport units. The source's smooth automatic pruning expression also must not replace the project's explicit continuous removals and management events. Source similarity is evidence to inspect, not an automatic correctness decision.

### Directly reusable current interfaces

| Current interface | Reuse for the new child | Boundary that must be explicit |
| --- | --- | --- |
| [Crop growth rates](../backend/app/crop_growth_rates.py), [growth contract](../contracts/crop-growth-research-v1.md) | `state.leaf`; `allocation.leaf`; `maintenance_respiration.leaf`; `removals.leaf`; `derivatives.leaf`; `lai` | Leaf is `mg_CH2O/m2_floor`, rates are `mg_CH2O/m2_floor/s`; no leaf-water mass is available |
| [Plant startup rates](../backend/app/crop_plant_startup_rates.py), [startup contract](../contracts/crop-plant-startup-rates-v1.md) | `allocation.leaf`; `vegetative_maintenance.leaf`; `removals.leaf`; `lai`; same leaf derivative | Startup modifies fruit/buffer policy; do not use total growth respiration as another leaf outflow |
| [Current crop continuation](../backend/app/crop_cycle_continuation.py), [continuation contract](../contracts/crop-cycle-continuation-v1.md) | Management removal amount and existing event ordering/carbon ledger | Event leaf removal is an amount, not a rate; crop and canopy energy changes must become atomic in the later joint path |
| [Fixed LAI dynamics](../backend/app/crop_canopy_air_dynamics.py), [coupling contract](../contracts/crop-climate-coupling-v1.md) | `m_v`, vapor equation of state, exchange `H/E/LE`, fixed air capacity, external `Qcan/Qair/Fv`, stage domain checks | Its `LAI` and `Ccan` are fixed; its old temperature state and fixed-capacity energy check cannot simply become a variable-capacity checkpoint |
| [Exchange module](../backend/app/crop_canopy_exchange.py), [exchange contract](../contracts/crop-canopy-exchange-v1.md) | Same-stage `Tc/Tair`, per-floor `LAI`, air vapor pressure; paired `E` and `LE` | Capacity loss does not change the accepted one-latent-debit policy; no implicit canopy water pool exists |

For startup, `requested_allocation.leaf` and `allocation.leaf` currently coincide, but the capacity policy should bind the actual accepted allocation field. Growth respiration is paid by the buffer in the current equations; subtracting it again from leaf capacity would double count a leaf loss that the crop RHS does not contain. Continuous removal and the instantaneous event are separate paths and must not both debit the same removal amount.

## 2. Open storage derivation and choice of energy reference

The first law for a control volume includes energy transported across its material boundary as well as heat and work. For an actual fluid flow, flow work leads to enthalpy transport. This principle motivates the boundary accounting below; it does not make the project's carbohydrate-to-capacity proxy a measured mass flow. [MIT's control-volume first-law derivation](https://web.mit.edu/16.unified/www/SPRING/thermodynamics/notes/node18.html) supports the open-system accounting principle. The following equations are this review's proposed reduced model and derivation.

### Definitions and dimensions

All extensive inventories below are **per floor area**. Temperatures may be represented in degrees Celsius because only differences enter this sensible store; their differences have kelvin units. `Tref` is an arbitrary accounting reference, not another physical state.

| Symbol | Definition | Unit / condition |
| --- | --- | --- |
| `B` | Current leaf carbohydrate inventory | `mg_CH2O/m2_floor`; strictly positive in the proposed admitted mode |
| `s` | Pinned `sla` | `m2_leaf/mg_CH2O`; fixed and positive |
| `cL` | Explicit synthetic `capLeaf` | `J/m2_leaf/K`; fixed and positive |
| `κ = cL*s` | Capacity per carbohydrate inventory in this model | `J/K/mg_CH2O`; phenomenological, not water mass conversion |
| `LAI = s*B`, `C = κ*B` | Current leaf area and canopy sensible capacity | `m2_leaf/m2_floor`, `J/m2_floor/K` |
| `A`, `M`, `R` | Gross leaf allocation, maintenance and continuous removal | Each nonnegative `mg_CH2O/m2_floor/s`; `B' = A-M-R` |
| `g = κ*A` | Incoming capacity rate | `J/m2_floor/K/s` |
| `d_m = κ*M`, `d_r = κ*R`, `d = d_m+d_r` | Outgoing capacity rates | `J/m2_floor/K/s`; keep loss categories identifiable |
| `Tin` | Temperature assigned to incoming capacity | Explicit finite temperature input; no default from air or canopy |
| `Tc`, `Tair` | Current canopy and air temperature | Physical state/derived state, not reference temperature |
| `Uref = C*(Tc-Tref)` | Canopy sensible energy relative to `Tref` | Signed `J/m2_floor`; may be negative |
| `Φ = Qcan-H-LE` | Net canopy heat rate excluding capacity transport | `W/m2_floor = J/m2_floor/s`; positive heats canopy |

Because `κ` is fixed, the crop and capacity inventories obey

```text
B' = A - M - R
C' = g - d_m - d_r = κ * B'
```

The proposed **declared boundary policy** is: incoming capacity arrives at `Tin`; maintenance-associated and removal-associated capacity leave the represented store at current `Tc`. The capacity reservoirs are external to the represented canopy/air/vapor system. This is a synthetic closure for a prescribed `C(B)`. Maintenance does not establish a literal export of leaf tissue; connecting it to this reservoir is part of the assumption requiring future physical review.

```text
Sin  = g   * (Tin - Tref)                  [W/m2_floor]
Sout_m = d_m * (Tc - Tref)                 [W/m2_floor]
Sout_r = d_r * (Tc - Tref)                 [W/m2_floor]
S = Sin - Sout_m - Sout_r

Uref' = Φ + S
```

Expanding `Uref' = C*Tc' + (Tc-Tref)*C'` gives

```text
C*Tc' = Φ + g*(Tin-Tc)
```

Outgoing capacity at the current temperature cancels from the temperature equation. Its energy export **still belongs in the ledger**. Cancelling this term does not permit dropping gross loss records, or replacing `g` by a positive part of net `C'`. If a later policy uses a different outgoing temperature or returns the material's heat to air, both temperature and boundary equations change and need a new explicit contract.

The reduced model omits chemical energy, respiration heat, variable tissue water content, hydraulic transport, mechanical work and a true biomass enthalpy relation. It must not estimate any of those from this note. In particular, `κ*M` is capacity bookkeeping induced by `C=κB`; it is not a respiration calorimetry result, `M` is not water evaporation, and `λ*M` is not an admissible heat flux.

### Arbitrary reference changes must preserve temperature

Let a second reference be `Tref2 = Tref1 + δ`, with identical physical states and forcing. A valid representation transforms as

```text
Uref2 = Uref1 - δ*C
Sin2 = Sin1 - δ*g
Sout_m2 = Sout_m1 - δ*d_m
Sout_r2 = Sout_r1 - δ*d_r
S2 = S1 - δ*C'
Uref2' = Uref1' - δ*C'
Tc = Tref1 + Uref1/C = Tref2 + Uref2/C
```

Thus `Tc'` and every exchange calculation are invariant. Signed energy and signed exported reference energy are necessary: a positive outgoing capacity can carry negative energy relative to a reference above `Tc`. Rejecting negative `Uref` or forcing an exported energy to be nonnegative would make the model depend on the arbitrary reference.

This is exact-arithmetic invariance. Large reference offsets can make reconstruction `Tref+Uref/C` ill-conditioned in finite precision. The implementation must declare its numerical tolerance/conditioning policy and hold on unresolved reconstruction; it must not promise byte equality for every finite offset or silently clamp the reconstructed temperature.

Two superficially similar implementations have different meanings:

1. Updating `C` while imposing `Uref'=Φ` with no material energy boundary gives `C*Tc'=Φ-(Tc-Tref)*C'`. Under variable capacity this depends on the arbitrary reference and is not the proposed open storage policy.
2. Updating `C` with `C*Tc'=Φ` can represent the explicit choice `Tin=Tc` and current-temperature outflow. It then requires `S=(Tc-Tref)*C'` in the energy ledger. It cannot silently stand for the distinct input `Tin` required here.

These are dimensional/product-rule results, not a claim that the original greenhouse model violates a measured plant energy balance. A source equation can omit a transport policy because it uses an approximation; this project's policy must state that approximation before coupling changing inventory to temperature.

## 3. Gross turnover defeats a net-LAI-only adapter

Consider an isolated capacity-policy case with `Φ=0`, equal positive allocation and total loss, and an incoming temperature different from the initial canopy temperature:

```text
g = d = a > 0
C' = 0
LAI' = 0
C*Tc' = a*(Tin-Tc)
```

The canopy temperature changes even though net LAI is constant. An adapter which derives its incoming capacity only from `max(C',0)` produces zero temperature response and misses the transport. The analytic trajectory for constant `a`, `C` and `Tin` is

```text
Tc(t) = Tin + (Tc(0)-Tin) * exp(-a*t/C)
```

This is a symbolic counterexample for the policy kernel, not a numeric crop result. The later independent reference generator should instantiate explicit synthetic inputs and compute all expected numbers deterministically. `Φ=0` here isolates the capacity accounting; it does not claim that an arbitrary accepted canopy exchange state has zero evaporation or heat exchange.

The same issue occurs when allocation and loss only partly cancel. Net `B'` is sufficient to update inventory, but insufficient to recover the incoming energy. Distinguish `A`, `M`, `R` and their ledgers even if the temperature RHS uses only `g` after algebraic cancellation.

## 4. Management events and empty-canopy holds

For a partial leaf removal event, let `r` be the event amount in `mg_CH2O/m2_floor`, `0 <= r < B_before`. The proposed instantaneous event has no added heat and exports removed capacity at the pre-event canopy temperature:

```text
B_after = B_before - r
C_before = κ*B_before
C_after  = κ*B_after
U_after  = U_before * (C_after/C_before)
U_export = U_before - U_after
Tc_after = Tref + U_after/C_after = Tc_before
```

The exported reference energy is equivalently `κ*r*(Tc_before-Tref)` in exact arithmetic. The eventual implementation must pin its operation order and compare alternative expressions using a stated numerical tolerance, rather than assume floating point expressions are byte-identical. `r=0` is the identity. Air temperature and vapor mass remain unchanged; the export is not an additional air heat source or latent debit.

The event conserves the accounting relation `U_before = U_after + U_export`. Under a reference shift, `U_export2 = U_export1 - δ*(C_before-C_after)`; canopy temperature stays invariant. Cases above, below and exactly at `Tref` distinguish positive, negative and zero reference energy export with nonnegative removed capacity. These cases are essential checks against a sign clamp.

The later joint path must validate and commit crop removal, canopy energy change and event ledger atomically, before publishing a post-event point. It must retain the pre-event checkpoint on a failed transition. The current [crop-only event implementation](../backend/app/crop_cycle_continuation.py) is useful for the removal amount and crop ledger, but has no canopy energy state to conserve yet.

The admitted mode requires positive `B`, `LAI` and `C` at every derivative stage, accepted endpoint and post-event state. Initial leaf zero, a trial state reaching zero, complete removal (`r=B_before`) and reentry from an empty canopy must return explicit holds. Complete removal would leave `C=0` and `U=0`, for which `Tc` is undefined. Do not keep a valid temperature by an epsilon capacity, assign air temperature, or invent a new incoming temperature. An eventual empty/reentry state machine needs its own initialization and material/energy policy.

This first child also keeps `sla` and `capLeaf` fixed for the whole calculation. Changing either introduces an additional capacity change that the gross carbohydrate flows do not explain; it needs a separate policy/version. It is not covered by the formula `C'=κB'`.

## 5. Consequences for the later joint state and ledgers

### Advance energy; derive canopy temperature each stage

The parent proposes `Uref` as the new canopy integration state. This review supports that choice:

```text
Given the current stage's B and Uref:
  LAI = s*B
  C = cL*LAI
  Tc = Tref + Uref/C
  evaluate crop rates using this Tc
  evaluate exchange using this Tc, LAI, Tair and m_v
  derive g, d_m, d_r from those same crop rates
  Uref' = Qcan-H-LE + Sin-Sout_m-Sout_r
```

Pin the multiplication order `C=cL*(s*B)` through the derived `LAI`; mathematically `cL*(s*B)` and `(cL*s)*B` are equal but their floating point paths need not be identical. Reject nonfinite or unresolved zero capacity, and apply the existing crop/exchange `10–34 degC` domain to **derived `Tc`**, not to `Uref` or arbitrary `Tref`. `Tin` must be supplied and finite; its admitted physical range and forcing semantics need to be pinned in the contract. There is no default `Tin=Tc` or `Tin=Tair`.

The [current crop continuation](../backend/app/crop_cycle_continuation.py) assumes a nonnegative state vector. A signed energy slot cannot pass through that unchanged guard or the old checkpoint schema. A new typed state and versioned checkpoint are required later. The present kernel need not change the old state or replay anything.

Advancing `Tc` and `B` independently with RK4 and reconstructing `Uref=C*(Tc-Tref)` at endpoints introduces a product of two integrated variables. An endpoint energy residual then includes discretization error, even if both differential equations were algebraically consistent. It should not be tested against a roundoff-only ledger tolerance. By advancing `Uref` directly, canopy energy and its accumulated boundary ledger are linear state combinations; shared stage evaluations and weights preserve that accounting up to floating point error. The reference transformation `Uref2=Uref1-δκB` is also linear in the integrated states when `κ` is fixed. Numerical conditioning and tolerances still need tests.

### Retain the accepted air, vapor and latent boundary

Using the predecessor's fixed air capacity and constants:

```text
Cair = h_air * rhoAirCap * cpAir
e_air = (m_v/h_air) * R_v * (Tair+273.15)
Tair' = (Qair+H)/Cair
m_v' = E+Fv
LE = λ*E
```

No capacity transport term is automatically credited to air. The canopy debit `-LE` and vapor store `+λ*m_v` cancel internally once. Introducing a separate latent debit for capacity loss, maintenance or removal would be an unsupported extra term. The accepted bulk saturation checks remain stage/endpoint holds; reverse `E` remains a mathematical exchange range and does not establish leaf condensation physics. See [the fixed LAI contract](../contracts/crop-climate-coupling-v1.md) and [exchange contract](../contracts/crop-canopy-exchange-v1.md).

For a constant reference, the represented combined reduced energy is

```text
W = Uref + Cair*(Tair-Tref) + λ*m_v
W' = Qcan + Qair + λ*Fv + Sin - Sout_m - Sout_r
```

At an event, `W_before-W_after=U_export`. The previous fixed-capacity combined ledger must therefore acquire the capacity transport/export boundary; it must not require the variable-capacity store to stay constant when that external boundary is nonzero. A reference change shifts `W` by `-δ*(C+Cair)` and the rate boundary by `-δ*C'`, consistently.

The represented water inventory is still only vapor: `m_v'=E+Fv`. Canopy liquid is an external boundary with rate `-E`. `g`, `d_m` and `d_r` carry no water mass in this reduced policy, because no leaf tissue water ratio exists in the accepted inputs. It follows that this is not a full plant water/enthalpy balance. A later measured crop model must address that missing state or boundary before making physical water or energy purchase claims.

### Coupled time remains a separate dependency

The capacity kernel can be implemented without adopting a new time grid. A subsequent joint RHS must consume crop and exchange rates from the same stage and state. A subsequent integrator must define shared forcing sampling, dynamic `Tc` contribution to `T24`/`Tsum`, crop cohort/startup transitions, removal ordering, clock precision and checkpoint identity. The crop-only prescribed-canopy-temperature clock cannot be attached unchanged to a dynamic canopy feedback loop. See [the earlier interface audit](crop-climate-interface-audit-20261009.md) and [the current continuation contract](../contracts/crop-cycle-continuation-v1.md).

## 6. Small first contract and independent acceptance cases

The first implementation can be a deterministic **capacity transport and event policy**, with no farm run, new climate integration, database write, UI or production result. Its public values should include explicit units and source parameter versions. Suggested contract surface:

| Operation | Required inputs | Required outputs / holds |
| --- | --- | --- |
| Continuous transport | Positive leaf inventory; pinned `sla`; explicit fixed `capLeaf`; actual gross `A/M/R`; explicit `Tin/Tref`; current `Uref` or an explicitly converted current `Tc` | `LAI/C/Tc`; gross `g/d_m/d_r`; `C'`; signed `Sin/Sout_m/Sout_r/S`; compatibility check against crop leaf derivative |
| Partial removal | Current leaf and energy, same parameter versions/reference, absolute removal amount | Post-event leaf/capacity/energy; unchanged temperature within declared numerical tolerance; signed exported energy; no mutation on hold |
| Reference conversion | Existing signed energy, current capacity, old/new references | `Unew=Uold-(Tref_new-Tref_old)*C`; no change to physical temperature |

Require closed field/unit sets, finite values, nonnegative gross rates and removal, positive admitted capacity, explicit reference and incoming temperature. A result is a synthetic/reference calculation policy, not approved data. Keep allocation versus maintenance/removal labels, because a generic net derivative cannot reconstruct them.

The next child can fit the parent's proposed core five artifacts: one contract, one pure kernel, focused tests, one independent Decimal reference generator, and one synthetic fixture. The contract must state formulas, domains, signs, operation order, numerical tolerance and hold codes. All numeric inputs/expected outputs should be generated by the deterministic artifact, not supplied as arithmetic claims in this prose.

### Independent symbolic cases to instantiate

| Case | Analytic condition / expected relation | Error exposed |
| --- | --- | --- |
| Fixed capacity | `A=M=R=0`; `S=0` | Regression to accepted fixed-LAI heat accounting |
| Pure growth, no heat/loss | Constant `g>0`; `C=C0+g*t`; `Tc=Tin+(Tc0-Tin)*C0/C` | Missing incoming sensible term or silent equal temperatures |
| Pure loss, no heat/inflow | Constant `d>0`; `C=C0-d*t>0`; `Tc=Tc0`; `U=C*(Tc0-Tref)` | Holding energy fixed while removing capacity |
| Gross turnover | `g=d=a>0`, `C=C0`, `Tc=Tin+(Tc0-Tin)*exp(-a*t/C0)` | Net-LAI-only transport |
| Explicit equal-temperature inflow | Caller explicitly supplies `Tin=Tc`; `C*Tc'=Φ` while `S=(Tc-Tref)*C'` | Dropping capacity energy from the ledger because temperature equation cancels it |
| Reference shift | Apply any admitted finite `δ`; transformed energy/rates reconstruct identical temperature and derivative | Absolute-value energy clamps or reference-dependent equations |
| Partial removal | Above/below/equal-to-reference initial temperatures; `U_before=U_after+U_export`, `Tc_after=Tc_before` | Wrong export sign or heat credit to air |
| Empty boundary | Initial zero leaf, trial zero capacity, complete removal, reentry | Epsilon capacity or arbitrary temperature initialization |
| Malformed inputs | Missing `Tin`, wrong units, nonfinite values, negative gross flows, removal beyond current leaf, unrepresentable capacity | Silent defaults, partial event commits or numeric contamination |

For the kernel, a separate Decimal implementation should evaluate the rate/event algebra from the documented inputs and formulas without importing the production kernel. Differential tests should distinguish formulas with equal net inventory change but different gross turnover. Later integration checks should use analytic trajectories, shared-stage energy/transport ledgers and reference-shift trajectories, plus a convergence check for thermal/crop state accuracy. Decimal alone is not physical validation and a reference implementation that repeats an accidental production branch is not independent evidence.

These cases are recommendations, not executed tests. No new coefficient, numeric thermal result or task acceptance is produced by this research note.

## 7. Physical and implementation holds

| Missing item / unresolved judgment | Current treatment | Required before a stronger claim |
| --- | --- | --- |
| Cultivar-specific leaf heat capacity and water/dry-matter composition | `null` physical adoption; explicit synthetic `capLeaf` only | Rights/QC review and independent measurements supporting the chosen capacity relation |
| Incoming tissue temperature / material origin | Explicit synthetic `Tin`; no air/canopy default | Defined tissue/water/control-volume boundary and evidence for its temperature/enthalpy |
| Capacity consequence of maintenance carbohydrate loss | Declared phenomenological reservoir outflow | Physical assessment of dry matter, water retention, respiration products and metabolic heat |
| True material enthalpy and water transported with growth/removal | Omitted, explicit hold | A consistent tissue mass/enthalpy model and measurements; capacity units alone are insufficient |
| Changing SLA or leaf properties | Fixed versions only | Separate parameter-transition and energy policy |
| Empty canopy and reentry | Explicit hold | Typed empty mode, initialization boundary and accepted transition policy |
| Joint forcing and temperature-history clock | Future contract | Same-stage crop/climate RHS, dynamic history semantics and versioned checkpoints |
| Full greenhouse boundary | External `Qcan/Qair/Fv` remain synthetic prescribed forcing | Separate radiation, ventilation, envelope, actuator and purchase-energy contracts/evidence |
| Actual crop/energy/harvest/purchase/economic validity | `hold`; no independent farm data | The corresponding project evidence and gates, not this algebraic kernel |

A realistic order is: (1) pin and independently review the capacity/event contract; (2) implement the pure policy and independent cases; (3) define a new joint RHS with derived stage `Tc` and explicit signed energy state; (4) define a short shared integrator/clock/event/checkpoint contract; (5) run bounded synthetic conservation and domain cases; (6) separately investigate greenhouse boundaries and actual crop evidence. No production completion date follows from this research. Each stage depends on the previous stage's acceptance; the original replay remains a separate immutable result.

## 8. Source provenance for this review

### New read-only retrievals, not adopted inputs

The following are current-task retrieval observations. Their bytes were hashed in memory; no raw source file, existing source register, fixture or pinned profile was overwritten. Observation time is `null` for these model/teaching documents. First public `available_at` is **unknown (`null`)**; retrieval time is not a substitute. The GreenLight revision is the fixed commit below; its publication/commit time was not independently established in this task. Independent release/data reviewer is pending.

| ID / primary source | Retrieval UTC | Bytes / SHA-256 | Revision, rights, QC and pointers |
| --- | --- | --- | --- |
| S1 [GreenLight Chapter 8](https://raw.githubusercontent.com/davkat1/GreenLight/7a7b36870135aa38bbe81e65590dcf5473786bdd/greenlight/models/katzin_2021/definition/vanthoor_2011/greenhouse_vanthoor_2011_chapter_8.json) | `2026-10-09T14:47:28.942776Z` | `130649`; `c0fb7a025533f15b80cb6cd60aafdc19be9fe42df6b8183cf97b83fc086138b3` | Commit `7a7b36870135aa38bbe81e65590dcf5473786bdd`; code/model license S6; `tCan`, `capCan`, `capLeaf`, `lai` pointers above; matches the previously pinned raw hash |
| S2 [GreenLight simplified Chapter 9](https://raw.githubusercontent.com/davkat1/GreenLight/7a7b36870135aa38bbe81e65590dcf5473786bdd/greenlight/models/katzin_2021/definition/vanthoor_2011/crop_vanthoor_2011_chapter_9_simplified.json) | `2026-10-09T14:47:29.183800Z` | `26741`; `272a589edf0bb40d1a91b34e883f8e94b9adf747a576be4620c50296c03d7033` | Same commit/license; `cLeaf`, `lai`, `mcBufLeaf`, `mcBufAir`, `mcLeafAir`, `mcLeafHar`; rate-area unit typo noted, not adopted |
| S3 [GreenLight combined main](https://raw.githubusercontent.com/davkat1/GreenLight/7a7b36870135aa38bbe81e65590dcf5473786bdd/greenlight/models/katzin_2021/definition/vanthoor_2011/main_vanthoor_2011.json) | `2026-10-09T14:47:29.389508Z` | `1559`; `1eb223ad590c63487420a67f994f30f2d6d260c78c8697e01ae06fcbf68f8b66` | Same commit/license; `/processing_order`; not evidence that every listed control definition was inspected |
| S4 [GreenLight standalone crop extension](https://raw.githubusercontent.com/davkat1/GreenLight/7a7b36870135aa38bbe81e65590dcf5473786bdd/greenlight/models/katzin_2021/definition/vanthoor_2011/extension_crop_vanthoor_2011_for_standalone.json) | `2026-10-09T14:47:29.673008Z` | `3895`; `74bf4f3ebc3100945de834433b210984c7a75c78c58218e5f7d5b4bd1c82ea49` | Same commit/license; `/Inputs/tCan`; prescribed standalone input |
| S5 [GreenLight model readme](https://raw.githubusercontent.com/davkat1/GreenLight/7a7b36870135aa38bbe81e65590dcf5473786bdd/greenlight/models/katzin_2021/definition/vanthoor_2011/readme.txt) | `2026-10-09T14:47:29.931222Z` | `2581`; `9e5ca837f6be1524886550f2c00d0ddab0cf980fd4be778e7e8d3532f4239ad9` | Same commit; describes combined/standalone definitions and source attribution |
| S6 [GreenLight license](https://raw.githubusercontent.com/davkat1/GreenLight/7a7b36870135aa38bbe81e65590dcf5473786bdd/LICENSE.txt) | `2026-10-09T14:49:41.815913Z` | `1716`; `96ce8c1f3d7b5473f473417c2785c63b74148edaddc2b9b6d40a6bbe3b7f4b6a` | BSD 3-Clause Clear: redistribution conditions/notices/disclaimer, no endorsement and no patent grant; applies to covered source, not automatically to external papers/data |
| S7 [MIT control-volume first law](https://web.mit.edu/16.unified/www/SPRING/thermodynamics/notes/node18.html) | `2026-10-09T14:49:41.598742Z` | `57872`; `438a9704182092ced15d8728a73f34c74ccd141308d557765b9737eda9e42117` | Official university teaching page; revision/publication/available-at unknown; linked/paraphrased only; raw display/redistribution rights not established, no raw adoption |
| S8 [Vanthoor thesis](https://edepot.wur.nl/170301) | Initial hash retrieval `2026-10-09T14:50:54.775177Z`; text-inspection retrieval `2026-10-09T15:03:00.974649Z` | `3423075`; `965ecc5573290d0cc59b514e9766b301f9584d212545dec177efa66dd756ac38` on both | Thesis 2011; Chapters 8–9, printed pp. 203/210/245/256 (PDF pp. 207/214/249/260); in-memory `pypdf` extraction plus pinned JSON equation comparison; same bytes as existing thesis pin; fresh retrieval does not establish first availability or unrestricted redistribution; no raw adoption |

GreenLight pointers identify source semantics; the project's dimensional correction, explicit management policy and the proposed energy transport policy remain distinguishable project decisions. The source register's existing reviewer/invocation evidence is not this agent's own invocation evidence. Existing source registers remain unchanged.

### Current local source snapshot

Read-only SHA-256 observations at `2026-10-09T14:50:54.776904Z`:

| Path | SHA-256 |
| --- | --- |
| `backend/app/crop_growth_rates.py` | `d8270e642dc80a747dd7d449094351369abb135a4663c3bf9fcdb1be5cd75858` |
| `backend/app/crop_plant_startup_rates.py` | `9b056740e2def0391226648726a4a4244eba0493c2c8a40b5b0d88260107e756` |
| `backend/app/crop_cycle_continuation.py` | `478f152a2395a451d9add64acf37e23ddc32a15273b14d0419869c1634596899` |
| `backend/app/crop_canopy_air_dynamics.py` | `69dbb671d4a9e0cc611b3d26702c45fa88f9d1cb4e3edd85443270951671d052` |
| `contracts/crop-climate-coupling-v1.md` | `31f31d0780999db50bface1e4a98456c9379d25235a1f946189793ca40c21d93` |
| `fixtures/crop-growth-reference-parameters-v1.json` | `d606d44c5ea6494820d0b182d08536524acdb88508a9f676788523b1248e83ca` |
| `fixtures/crop-canopy-exchange-reference-parameters-v1.json` | `1e032ced2ffdaf8ba713184e89b628cce4173c9e7231f30710afeda8fbf20110` |
| `research/crop-canopy-exchange-source-register-20261009.json` | `4f1f1c17671eb4631fb5c1761e1efd1927a89f987603bd95536d7a349c714bdc` |
| `research/crop-tomato-source-register-20261004.json` | `86aa3c45a0f0107ac02e8d9e0fe2cf25a485cacde292e8a7cd6321472dfa8b19` |

These hashes identify the reviewed snapshot, not a promise that another concurrent agent will never change a contract. No fixture input, raw result or existing register is updated by this task. Read-only inspection found **26 local links, 0 missing**, and **4 pinned parameter/source-register files, 0 changed**. No model tests or simulations were run. Source retrieval/text inspection completed; this note is ready for independent review and source freezing.
