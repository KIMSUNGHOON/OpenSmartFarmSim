# Shared PAR, virtual NIR and ventilation integration — v1

New `joint-crop-climate-solar-ventilation-rk4-research-v1` uses the unchanged
[current-state composition](crop-greenhouse-solar-joint-v1.md) and existing
joint RK4/state/ledger primitives. All old profiles/model/context/result
identities stay immutable. `integrate(scenario, solar, ventilation,
step_seconds, step_count, four profiles)` accepts that composition's closed
inputs, explicit non-solar canopy heat and shared two-band solar assumption.

All108 states advance together. Every initial/trial/endpoint evaluates exactly
one NIR, one ventilation, one PAR and one joint RHS at the same current leaf,
air/vapor and signed canopy energy/capacity. Initial composition both validates
the complete input and supplies k1; no extra validation RHS is needed. Endpoint
RHS supplies the next k1. Each kernel count is `4*n+1`. Other forcing/solar/
outdoor quantities are interval constants; derived absorption and ventilation
are current-stage values. No floor/cover/reflection/construction heat credit,
second crop interception, dynamic weather/CO₂ closure or total greenhouse heat
claim. Virtual NIR model limits remain those of the instantaneous contract.

Step is finite positive int/float excluding bool, count integer1..4096 excluding
bool, interval at most600s. These are research budgets, not stability/accuracy/
capacity guarantees. Elapsed seconds only; no events/UTC/product checkpoint/
storage/API/3D admission. A manual numerical split is not runtime resume proof.

## 41 ledgers and 15 balances

Retain core22 and ventilation3 ledgers. Add signed `canopy_non_solar_heat`,
the nine `solar_par_` ledgers from [PAR integration](crop-greenhouse-radiation-par-integration-v1.md),
and six J/m2_floor NIR ledgers: `solar_nir_outdoor`,
`solar_nir_available_virtual`, `solar_nir_canopy_absorbed`,
`solar_nir_floor_absorbed`, `solar_nir_upward_virtual`,
`solar_nir_construction_unallocated`. Use the identical RK weights as states.
Keep core7/ventilation3 balances and test:

```text
Icanopy_external = Inon_solar + Icanopy_PAR + Icanopy_NIR
Iabove_PAR = Icanopy_PAR + Ifloor_PAR + Iunresolved_PAR + Iupward_PAR
Ioutdoor_PAR = Iabove_PAR + Icover_reflected_PAR + Icover_absorbed_PAR + Iconstruction_PAR
Iavailable_virtual_NIR = Icanopy_NIR + Ifloor_NIR + Iupward_virtual_NIR
Ioutdoor_NIR = Iavailable_virtual_NIR + Iconstruction_unallocated_NIR
```

Partition budgets: `64*(step_index+1)*ulp(sum(abs(terms)))`; core/ventilation
budgets unchanged. They are binary64 roundoff checks, not time-error or field
accuracy allowances. Return original states/derived quantities plus current
boundary input hashes/incident photons/heat/optical partitions, normalized
original inputs and full code/profile/policy/source/notice/numerical identities.
New ledger identity `joint-solar-ventilation-ledgers-v1`. Failure retains only
last confirmed sample/elapsed time and failed step/stage; no candidate success.
`software_research_only`, `synthetic_joint_solar_ventilation_integration_only`,
`G0_G4=not_assessed`.

## Acceptance fixed before tests

- Independent app-free Decimal80 source optics/outdoor/crop/exchange/capacity and
  a separate149-vector RK4; full108 states/41 transfers/3 derived values for
  day/dark/reverse outdoor air/signed other heat/changed leaf/zero ventilation/
  zero NIR. Same-step relative5e-12/absolute5e-14; Tc absolute2e-10K.
- All15 runtime balances; absolute carbon/energy1e-7, number1e-12, vapor1e-13,
  capacity1e-8 in corresponding units. No virtual remainder as physical heat.
- Three smooth32s examples, dt8/4/2 against independent Decimal dt0.25: each
  halving reduces error by>8 for Tc/Tair/vapor/T24/Tsum/buffer/fruit C and
  sensible/latent/vapor/ventilation sensible/vapor transfers. Invariants and
  floating-point floors are not convergence claims; do not lower this bar.
- Actual one-call shared trial capture/current LAI/temperature/air; evolving
  NIR and PAR absorption; frozen initial NIR negative control. Dark exactly
  matches old ventilation; zero NIR exactly matches old PAR physical solution
  under a new identity. Manual event-free split preserves states/transfer sums.
- Immutable input/replay/version/component pins; explicit heat/spectrum/origin/
  schema/unit/profile/domain/numeric/budget holds and last confirmed prefix.
- Focused existing consumers, all five live roots/dynamic descendants, original
  sources/assets/results, FD/owned cleanup and512MiB/PID/combined1GiB unchanged.

Then implement new immutable input/context/checkpoint/store/API/same UTC3D
acceptance. Real optical/facility/cultivar/local/future farm/market data and
G0–G4 remain separate publication dependencies; full completion date unknown.
