# Current-stage ventilation with atomic management — v1

Core5: `backend/app/crop_greenhouse_ventilation_program.py`, its tests,
this contract, `research/crop-greenhouse-ventilation-program-reference.py`, and
`fixtures/crop-greenhouse-ventilation-program-reference-cases-v1.json`.
Predecessors: [ventilation RK4](crop-greenhouse-ventilation-joint-v1.md),
[original event driver](crop-climate-joint-boundary-driver-v1.md),
[atomic management](crop-climate-joint-management-v1.md).

## Input and execution

`integrate_events(scenario, ventilation, events, output_steps, step_seconds,
step_count, four_profiles)` uses keyword arguments, the existing closed joint
scenario and the current-stage ventilation input. Other/outdoor forcings and RGR
remain explicit constants. Each interval recomputes Q/Fv at its current shared
stages. Reuse original event normalization, limits and source quantity-removal
policy: dt>0,1–4096steps,≤600s,≤128 unique ordered boundary events and2–512 ordered
outputs including0/final. No interpolation, weather/control estimator or new
management coefficients are added.

Order: initial validation/current ventilation →boundary0 management →selected
output; then one accepted RK step →global balances →same-boundary atomic management
→global balances/current ventilation →journal →selected output. Reuse original
management and global stock-balance kernels; do not duplicate crop/event equations.
Keep source scenario forcings as **other** contributions throughout, including after
management; never feed a previously combined forcing back into the next interval.

Snapshots contain108states, current derived values/ventilation diagnostic,
25continuous ledgers,6event totals,10balances/budgets and phase. Seven global
stock balances include original event removals once; the three ventilation partitions
use actual elapsed time and constant other Q/Fv. Removed canopy heat is signed.
Event application changes represented leaf/capacity/energy while preserving the
accepted instantaneous canopy temperature. No instantaneous air-temperature/vapor
jump or latent-to-sensible credit is introduced.

Management journal retains its original before/after validation diagnostics, which
use the source other forcings. `combined_forcing_after` and `ventilation_after` record
the actual new post-event boundary. Original management validation is not labeled a
new ventilation RHS. Both old event code and new driver/stage/boundary hashes are
bound into a new program identity `joint-ventilation-management-program-research-v1`.
No old context/checkpoint type is issued.

Completed actual calls for n steps/e events: input-validation RHS1+n, coupled RHS
and ventilation1+5n+e, management RHS2e, total joint RHS2+6n+3e. Each interval's
endpoint is accepted before management; management's post-event ventilation is
recomputed before committing the event. Failure preserves the prior confirmed
snapshot and selected-output/journal prefixes. A failed event is never journaled
or selected; a same-time step-end may remain confirmed. No partial successful
result or resume checkpoint is returned.

## Acceptance fixed before execution

1. Decimal80 with no app imports independently advances133state/ledger coordinates
   and applies pinned independent retention/removal/capacity equations. Ten32s
   programs cover no events, warm/dark/reverse, initial/final/multiple events,
   signed/zero Uref and zero ventilation. Source programs are referenced by immutable
   case ID/hash; every selected108state/25ledger/6event total/derived value and all
   journal before/after/removal totals match relative5e-12/absolute5e-14; temperature
   and history absolute2e-10 K. Oracle replay reproduces fixture bytes.
2. For three16s-event programs, dt8/4/2 versus independent0.25 yields >8 reduction
   per halving for12 metrics (Tc/Tair/m_v/T24/Tsum/buffer/fruit C/H/LE/E/vent Q/Fv):
  72 ratios. Keep failure/roundoff holds; do not lower criteria.
3. Independently recompute raw stock/event/flux balances and enforce runtime budgets
   plus existing absolute limits: heat/carbohydrate1e-7, number1e-12, water1e-13,
   capacity1e-8 in declared units. Validate actual calls/order/current forcings,
   selection invariance, no-event stage equivalence and zero-flow old-driver equivalence.
4. Check closed input/order/duplicates/bounds/profiles, real and injected step/event/
   global-balance failures, last confirmed prefixes, input immutability and new identities.
   Exercise512outputs/128events and reject bounds without creating field claims.
5. Preserve old calculation/source/fixtures/results, frozen user services/assets and
   original entries; exact owned cleanup/FD and WSL512MiB single/1GiB combined.

Output scope is `software_research_only`,
`synthetic_joint_ventilation_management_program_only`, `G0_G4=not_assessed`.
No UTC, continuation, writer, current-rights API or UI deployment is accepted here.
Those remain required children before user activation. Full-season validity, other
greenhouse/resource/economic boundaries and independent cultivar/farm evidence remain open.
