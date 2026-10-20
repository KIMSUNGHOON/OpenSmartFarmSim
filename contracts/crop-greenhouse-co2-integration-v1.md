# Short CO₂/crop/solar integration v1

Status: short research integration accepted;
[evidence](../research/artifacts/crop-greenhouse-co2-integration-20261021.json). This advances the accepted
[109-state current-stage RHS](crop-greenhouse-co2-joint-v1.md). It reuses the
unchanged [Solar integration](crop-greenhouse-solar-integration-v1.md) state,
ledger, sample and partition primitives without invoking its old prescribed-ppm
solver. Old108-state profiles/checkpoints/programs/results remain unchanged.

`integrate(scenario, solar, ventilation, co2, step_seconds, step_count, four profiles)`
takes the new RHS's closed inputs. All external forcing, radiation/weather,
pressure and basis are constant within this event-free research interval.
CO₂ mass, air temperature/vapor and crop states advance together; each actual
RK trial derives ppm from its own current mass/h/T/P/vapor. No initial ppm is
frozen or supplied by the caller. Every trial executes the actual Solar/startup/
net/air chain once; initial and endpoint RHS results supply the next k1.
Counts are4*n+1 per component, no extra validation RHS. Endpoints are validated
before becoming confirmed samples; any initial or intermediate failure returns
no success and exposes only the last confirmed sample/time and failed step/stage.

## State, transfers and accounting

State order is the old108-state order followed by `air_co2_mass` at index108.
Advance the old41 Solar ledgers and three signed CO₂ ledgers with the same RK4
weights: `co2_ventilation_to_air`, `co2_external_to_air`, `co2_crop_to_air`.
Their integrated unit is mg_CO2/m2_floor; these are model mass transfers, not
purchased gas or fuel. Return44 named transfers and current gas/solar/crop
diagnostics in each confirmed sample. State and ledger identities are new.

Retain the old15 balances and add:

```text
M1-M0 - I_vent_to_air - I_external - I_crop_to_air = 0
M1-M0 + (44/30)*(C1-C0 + I_removed + I_terminal)
      - I_vent_to_air - I_external = 0
```

The source C9 carbon-equivalent convention is retained; it does not unify the
C8 gas helper's44.01g/mol choice. Removal and terminal carbon are external plant
transfers, not respiration. CO₂ inventory roundoff budget is64*(n+1)*ULP of the
largest initial/final inventory or sum of absolute balance terms. Combined
budget adds the converted old carbohydrate budget and64*(n+1)*ULP of its total
initial/final air+plant inventory/terms. These are numerical budgets, not field
accuracy or time-error allowances. Existing heat/water/optical budgets remain.

Step is explicit finite positive int/float excluding bool; count is integer
1..4096 excluding bool; duration≤600s. These match the existing research
boundary and are not stability/capacity promises. No event, full cycle, UTC,
checkpoint/resume/store/API/3D admission or field/gate promotion occurs here.
Retain the [GreenLight notice](../LICENSES/GreenLight-BSD-3-Clause-Clear.txt).

## Acceptance fixed before execution

- Eight explicit synthetic32s cases from the existing Solar scenarios cover
  day/dark, both CO₂ exchange directions, signed external gas, nonzero removal,
  wet/dry, zero ventilation/NIR. Compare all109 final states,44 integrated
  transfers, canopy temperature/LAI/capacity and final ppm with an app-free
  Decimal80 **153-vector** RK4: relative5e-12/absolute5e-14; Tc additionally
  absolute2e-10K. Verify generator/input hashes and exact fixture replay.
- All17 balances pass original runtime budgets. Absolute residual limits:
  carbon/CO₂/energy1e-7, number1e-12, water1e-13, capacity1e-8 in stated units.
- First three smooth32s examples: dt8/4/2 against independent Decimal dt0.25.
  Each halving reduces error by>8 for the existing12 thermal/crop/transfer
  metrics plus CO₂ mass, ppm, integrated crop→air and ventilation→air. All96
  ratios must pass. Constant/invariant external injection is excluded from
  convergence claims; the bar will not be lowered to accommodate a failure.
- Capture actual evolving trial mass/T/vapor/ppm and4*n+1 calls, endpoint
  samples, immutable inputs/identity, event-free numerical split and real
  intermediate depletion/last confirmed prefix. Reject bad budgets before RHS
  and preserve source domain/units/profile/basis holds.
- Focused tests under existing WSL guard; original models/profiles/results,
  5healthy roots and frozen previews, FD/owned cleanup/caps unchanged. Whole
  product CI, browser/DB, storage/3D and independent farm validation remain later.

## Observed acceptance — 2026-10-21 KST

Final25 checks passed in25.82s. Eight32s examples matched1,256 independent final
state/transfer/derived scalars; all17 balances and96 step-halving ratios passed
the predeclared limits. The generator replay matched the fixture exactly.
Actual capture verified65 evolving current-stage evaluations for16 steps,
endpoint sample correspondence and immutable replay. Actual strong extraction
and later depletion held only the last confirmed prefix; numerical split
matched the full physical endpoint. This is not runtime checkpoint proof.

Guard child0/wall26.241616s, combined peak RSS665,407,488bytes, FD4→4;
5healthy roots,2,148originals and frozen previews preserved, owned process/PG/
temp/credential residue0. Independent fixture generation also exited0 under the
same guard in22.386720s. Initial missing-module failure was an absence check,
not a numerical counterexample. No existing source/profile/result changed.
No management events, full cycle, UTC/custody/Run, browser/DB/whole CI or new
saved3D/field/deployment claim was accepted. Next: atomic managed state change,
then forcing/program/continuation/storage and same-UTC3D in separate children.
