# Solar PAR and ventilation shared integration — v1

New `joint-crop-climate-solar-par-ventilation-rk4-research-v1`; old
[ventilation](crop-greenhouse-ventilation-joint-v1.md) and saved identities stay immutable.
`integrate(scenario, solar, ventilation, step_seconds, step_count, four profiles)`
uses the [current-state PAR adapter](crop-greenhouse-radiation-par-joint-v1.md)
scenario/solar and the existing closed outdoor ventilation input. All three
origins must match. There are no optional legacy light or total-canopy-heat inputs.

## Shared calculation

The existing bounded fixed RK4 advances all 108 states together. At each trial,
current air temperature/vapor supply ventilation, current leaf supplies PAR LAI,
and current signed canopy energy/capacity supplies the crop/exchange temperature.
Add ventilation to the explicit other air forcing once; the PAR adapter supplies
incident photons and absorbed PAR plus explicit non-PAR canopy heat once.
Floor/unresolved/cover radiation supplies no canopy or air heat. No NIR closure,
total solar, LED spectrum, geometry conversion, purchased energy or weather
sampling is inferred. Other forcing, solar and outdoor inputs are interval constants.

Initial PAR/RHS validation normalizes the base input once before state extraction.
Then coupled initial/trials/endpoints evaluate ventilation, PAR and joint RHS once
each: `4*n+1` coupled evaluations; including validation PAR/RHS total `4*n+2`.
Endpoint RHS becomes next k1. Step positive finite number excluding bool; integer
count 1..4096 excluding bool; interval at most 600s. These are research budgets,
not accuracy/stability guarantees. Elapsed seconds only; no UTC/checkpoint/event
or product Run admission.

Use the unchanged 22 core and 3 ventilation ledgers, plus 10 J/m2_floor ledgers:
`canopy_non_par_heat`, `solar_par_outdoor`, `solar_par_above_canopy`,
`solar_par_cover_reflected`, `solar_par_cover_absorbed`,
`solar_par_construction_intercepted`, `solar_par_canopy_absorbed`,
`solar_par_floor_absorbed`, `solar_par_unresolved_reflected`,
`solar_par_upward_transmitted`. Same RK weights as the states; retain signed
non-PAR heat. Check the seven core/three ventilation balances plus:

```text
Icanopy_external = Inon_PAR + Icanopy_PAR
Iabove_PAR = Icanopy_PAR + Ifloor_PAR + Iunresolved_PAR + Iupward_PAR
Ioutdoor_PAR = Iabove_PAR + Icover_reflected + Icover_absorbed + Iconstruction
```

New partition residual budget is `64*(step_index+1)*ulp(sum(abs(terms)))`.
Existing core/ventilation budgets apply unchanged. Failure includes step/stage,
last confirmed sample/elapsed time; no trial or candidate is published as success.
Sample retains current boundary input hashes, incident photons, heat components,
and PAR partitions together with the original 108 states/derived/ventilation.
Return normalized original inputs, full component/profile/policy/source/notice
hashes, numerical policy and new input/calculation/ledger identity.
`software_research_only`, `synthetic_joint_solar_PAR_ventilation_only`,
`G0_G4=not_assessed`; all examples are synthetic software evidence.

## Acceptance fixed before tests

- Independent app-free Decimal80 full 108 states, 35 ledgers, 3 derived quantities
  for day, dark, signed non-PAR heat, changed leaf and zero ventilation; same-step
  relative 5e-12/absolute 5e-14 and canopy temperature absolute 2e-10 K.
- All 13 runtime balance budgets; absolute carbon/energy 1e-7, number 1e-12,
  vapor 1e-13, capacity 1e-8 in corresponding ledger units.
- Three smooth positive-tail cases: 32s dt8/4/2 against independent Decimal dt0.25;
  each halving reduces error by >8 for Tc/Tair/vapor/T24/Tsum/buffer/fruit C and
  sensible/latent/vapor/ventilation heat/vapor ledgers. Invariants and roundoff
  floors are not convergence claims. Do not relax this bar after observing results.
- Actual per-trial call counts/current state/once-only composition; evolved leaf
  changes absorption; freezing initial PAR is a negative control. Dark PAR yields
  exact equivalence with old ventilation math under a new identity.
- Manual event-free split retains physical state and ledgers within the stated
  numerical tolerance; this does not accept resumable product checkpoints.
- Closed quantities/profiles/origins, explicit heat exclusion, budget/domain/numeric
  failures and last confirmed prefix; immutable inputs/deterministic identity.
- Existing consumer tests, five protected live roots, original sources/assets,
  FD/owned cleanup and512MiB/PID/combined1GiB under the existing resource guard.

Next: independent NIR layer boundary, new immutable context/checkpoint/store/API
and same UTC3D. Real facility/cultivar/optical/local future farm evidence and
G0–G4 acceptance remain separate dependencies; overall completion date unknown.
