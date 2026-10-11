# Joint current-stage ventilation integration — v1

Predecessors: [pure ventilation](crop-greenhouse-ventilation-v1.md) and
[joint short integration](crop-climate-joint-short-integration-v1.md).
Core5: `backend/app/crop_greenhouse_ventilation_joint.py`,
`backend/tests/test_crop_greenhouse_ventilation_joint.py`, this contract,
`research/crop-greenhouse-ventilation-joint-reference.py`, and
`fixtures/crop-greenhouse-ventilation-joint-reference-cases-v1.json`.

## Boundary and immutable identity

`integrate(scenario=..., ventilation=..., step_seconds=..., step_count=...,
growth_profile=..., cohort_profile=..., transport_profile=..., exchange_profile=...)`
advances the existing108 crop/cohort/climate states jointly, without events.
The new model is `joint-crop-climate-prescribed-ventilation-rk4-research-v1`.
It reuses the old integration module's version-coupled state/RK/ledger helpers and
the existing joint RHS. Their code hashes join the new code, pure ventilation,
profiles, policy, input and numerical identities. Old code/profiles/results/checkpoints
are preserved. This result is not an old continuation/checkpoint or farm Run.

`scenario` is the existing closed joint input. Its air heat/vapor forcing means
**other prescribed boundary contributions**, excluding this ventilation exchange.
`ventilation` has exactly `input_id`, `origin`, `forcing`; the latter contains the
pure ventilation contract's outdoor temperature, outdoor vapor pressure and volume
exchange per floor area with exact units. No separate indoor state/parameters can
be supplied. They come from the current shared trial and the same parent h/rho/Rv.
Outdoor forcings, other forcings and RGR50 are explicit constants for this interval;
the ventilation flux varies with the current indoor state. No control/weather or
facility-flow estimator is introduced. Pure-boundary and existing joint domain/hold
rules remain in force; field/outdoor saturation/QC eligibility remains unassessed.

An initial unforced joint evaluation validates/normalizes the original closed input.
It advances no state. Each coupled evaluation then computes ventilation exactly once
from that current trial and evaluates the joint RHS exactly once with
`Qtotal=Qother+Qvent`, `Ftotal=Fother+Fvent`. Base forcings are never replaced with
the previously combined forcing. L·Fvent is recorded separately and never added to
air sensible heat. RK4 stages and endpoint share current leaf/U/Tair/m_v; endpoint
evaluation is reused for the next k1. Accepted counts are `4*n+1` coupled RHS and
ventilation evaluations plus one input-validation RHS, `4*n+2` total joint calls.

Numerical bounds remain finite positive binary64 dt, integer1–4096steps, horizon≤600s.
All108 states and25 ledgers use the same RK4 stages/weights. Existing increment,
domain and64-ulp-per-step roundoff guards are reused. Holds preserve step/stage and
the last fully accepted sample; no failed trial or endpoint is published as success.

##25 integrated ledgers and10 balances

The original22 ledgers now contain the actual **combined current-stage** Q/Fv.
Append `ventilation_sensible_heat [J/m2_floor]`,
`ventilation_vapor [kg_water/m2_floor]`, and `ventilation_latent_energy [J/m2_floor]`.
The original seven global balances use the total Q/Fv. Add three independent
partitions, with `t=index*dt` and signed integrals:

```text
I_air_external_sensible_heat - Qother*t - I_ventilation_sensible_heat = 0
I_air_external_vapor - Fother*t - I_ventilation_vapor = 0
I_ventilation_latent_energy - L*I_ventilation_vapor = 0
```

Their roundoff budget is `64*(index+1)*ulp(sum(abs(terms)))` in each balance's unit.
These reduced stores/partitions exclude the omitted enthalpy/work and other
greenhouse stores listed in the predecessor contracts. They are not farm conservation
or purchased energy/water demand. Each sample preserves original state/derived fields
plus current ventilation input hash, densities, Q/Fv and latent diagnostic. Output
binds `ledger_schema_version=joint-ventilation-ledgers-v1`, the unchanged state/clock
contract, new model identity, source/notice hashes, `software_research_only`,
`synthetic_joint_crop_climate_prescribed_ventilation_only`, `G0_G4=not_assessed`.

## Acceptance fixed before execution

1. Independent Decimal80 generator imports no application code. Reuse pinned
   independent crop/canopy/capacity equations, add its own signed ventilation
   algebra at each stage, and advance a133-vector. Six32s cases cover cool/dry,
   warm/moist, dark/reverse thermal flow, zero ventilation and signed/zero Uref
   via reference-temperature changes. Whole108 states,25 integrals and3derived
   values match at relative5e-12/absolute5e-14; canopy temperature absolute2e-10 K.
2. For the first three positive-tail cases, compare32s dt8/4/2 with independent
   Decimal dt0.25. Tc/Tair/m_v/T24/Tsum/buffer/total fruit carbohydrate, H/LE/E and
   ventilation Q/Fv errors must each fall by >8 per halving. Do not report a
   zero/invariant or roundoff floor as convergence; retain a hold if criteria fail.
3. Each of the seven stock/flux balances meets existing runtime budgets plus
   absolute limits: energy/carbohydrate1e-7, number1e-12, water1e-13 and capacity1e-8
   in their declared units. Three partition budgets also pass. Recompute balances
   from returned raw stocks/ledgers, rather than relying on residual labels alone.
4. Capture real stage calls: matched current indoor states/parameters, Q/Fv added
   once, exact counts, endpoint/sample pairing, evolving flux and input immutability.
   Prove zero-flow physical equivalence to old integration and a different trajectory
   from freezing the initial nonzero ventilation flux. Confirm reference invariance.
5. Test identities, bounded/closed inputs, inherited domain/profile/unit holds,
   all unconfirmed stage failures, real temperature failure, numeric lost increments,
   and corrupted combined/ventilation ledger rejection with last confirmed state.
6. Preserve old calculation files, frozen services/assets, original entries, FD and
   exact owned-process cleanup; bound WSL to512MiB single/1GiB with protected services.

This core has no management events, UTC, continuation, immutable writer, API or UI
deployment. Those are follow-up contracts under the existing greenhouse parent.
Radiation/PAR/NIR, CO₂/stomatal/facility flow, water/nutrients, purchased energy and
economics remain separate required work; independent cultivar/farm data and G0–G4
claim evidence are not supplied by these synthetic trajectories.
