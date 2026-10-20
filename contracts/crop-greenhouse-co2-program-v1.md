# CO₂/Solar forcing and management program v1

Status: research software accepted by37 focused tests on2026-10-21 KST. Uses the accepted [109-state short RK](crop-greenhouse-co2-integration-v1.md),
[atomic management](crop-greenhouse-co2-management-v1.md) and existing
[Solar grid limits/order](crop-greenhouse-solar-program-v1.md).

`integrate_events(scenario, forcing_program, events, output_steps, step_seconds,
step_count, four profiles)` runs explicit piecewise constant outdoor boundaries.
Each closed forcing row has `step_index, solar, ventilation, co2`; the three
blocks use the unchanged actual CO₂/Solar RHS contracts. There are1..512 rows,
starting at0, with strictly increasing integer indices through the endpoint.
All origins agree. Geometry, profiles, source non-solar heat/air inputs and other
scenario inputs stay fixed. This is outdoor forcing scheduling; automatic
facility control, variable geometry and a varying internal source program remain
separate. No caller-supplied ppm or coefficients defaulted by the driver.

## Ordering and atomic publication

Existing limits stay1..4096 steps, positive finite dt, at most600s,128 events and
512 selected outputs covering0 and the endpoint. Existing event indices/IDs are
unique and ordered; there is one event per boundary. At a boundary:

1. Confirm the preceding interval using its old forcing, including its RK end
   trial. Intermediate stages never see the following interval's input.
2. Activate that boundary's new forcing, evaluate the actual current109-state
   RHS and confirm it without changing time/stocks or continuous totals.
3. Apply any event with the actual new CO₂/Solar management function; its returned
   `after_rhs` supplies the boundary diagnostic, without another evaluation.
4. Check global balances, then emit a requested output. Outputs show the active
   boundary forcing index and gas/optical diagnostics.

Thus weather and removal at0/interior/endpoint have one deterministic order.
Boundary basis/pressure changes affect derived ppm, never instantly add gas.
The original scenario forcing never becomes already-composed heat/ppm input.
Completed output and identities include all normalized forcing rows, schedule,
selected indices, code/profile/source/notice/policy hashes and payload hashes.

Any failure includes global index/phase, detached last confirmed state, selected
prefix and committed event journal. A failed forcing change retains the same-time
old-forcing endpoint. A failed event retains the same-time active-forcing state,
without committing removal or that boundary's selected output. A failed interval
or global step balance retains the preceding confirmed boundary. Invalid initial
inputs have no confirmed state. A held program is never a completed Run.

## Arithmetic and counts

Retain44 continuous ledgers,6 original instantaneous removal totals and17 global
balances. The combined CO₂/carbohydrate balance includes event leaf/stem/fruit
carbohydrate removal once at the reviewed44/30 source convention. No removed
carbohydrate becomes CO₂ emission. Exact event air invariants remain enforced by
management. Reuse existing crop/energy/number, ventilation and radiation balance
formulas/budgets; no new heat/quantity coefficients or loosened acceptance limits.

With n intervals, e events and b forcing changes after the initial row, actual
coupled RHS/component counts are `1+5*n+2*e+b`: each accepted one-step RK uses5,
each management uses2, each forcing change uses1. No old management/old fixed ppm
RHS is called as a replacement. Output selection cannot change physical totals.
No UTC, checkpoint/resume, custody, storage/API/3D or full crop cycle acceptance.

## Acceptance fixed before execution

- Independent app-free Decimal80 current CO₂ RK plus original removal arithmetic:
  constant/changed forcing, wet/dry, day/night, zero/reverse ventilation,
  signed/zero canopy reference energy and event0/interior/end. Compare selected
 109 states,44 transfers,6 event totals, derived ppm/Tc/LAI/capacity and journal.
  Relative5e-12/absolute5e-14; Tc absolute2e-10K; all17 runtime budgets. Independently
  check mass/carbon/energy1e-7, number1e-12, vapor1e-13, capacity1e-8, radiation
  partitions and explicit piecewise external CO₂ integral.
- At fixed forcing/event times, dt8/4/2 versus independent dt.25 must improve
  every preregistered nondegenerate metric with both ratios>8. No threshold or
  reference adjustment to make a result pass.
- Actual call order/counts; no old management call; source input preservation;
  same-time new forcing before removal; endpoint forcing with zero interval
  credit; no-event versus accepted short integrator; output selection/replay/
  identities. Exercise128 events/512 outputs and512 forcing rows, with immutable
  inputs and meaningful invalid schema/grid/origin/quantity and injected holds.
- Focused WSL guard preserves original models/profiles/results,5healthy roots,
  frozen previews, FD/owned cleanup,512MiB/PID and combined1GiB. No whole CI or
  field/gate/deployment acceptance. Scope `software_research_only`, G0–G4 held.

## Observed acceptance

[Machine evidence](../research/artifacts/crop-greenhouse-co2-program-20261021.json)
records37 passing tests in20.39s. Ten independently generated32s programs provide
36 selected samples and12 events:5,868 selected state/transfer/event/derived
values plus2,688 journal state/removal values. All96 preregistered convergence
ratios exceed8; all17 runtime budgets and independent global balances pass.
The actual three-event/three-change run uses90 new RHS evaluations. The joint
maximum512-forcing/512-output/128-event run uses3,328 evaluations and completes.

Six initial/interval/forcing/event/global-balance failure cases preserve the
correct detached prefix, including a real CO₂ k2 depletion. Thirteen malformed
schedule/limit cases fail without publication. No-event constant forcing matches
the accepted short integrator exactly; changing output selection preserves
physical totals/journal. A test observation initially tried copying immutable
profile objects; its mappingproxy TypeError was corrected by recording only the
input blocks under observation. Product arithmetic and oracle were unchanged.

Generation/RED/GREEN guards preserve original2,148 entries, profiles, five roots,
frozen previews and FD4→4, with zero owned process/PG/temp/credential residue.
GREEN combined RSS769,359,872bytes and single-PID206,598,144bytes remain below the
fixed caps. No broad CI/browser/DB, automatic control, full crop cycle, UTC/
checkpoint, saved109-state3D or farm/gate/deployment claim follows. Next:
immutable continuation with exact program/forcing/event/output cursors.
