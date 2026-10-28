# Actual newborn next-event candidate, research v1

This readonly calculation follows [the accepted post-material continuation](crop-supply-morphology-newborn-resume-v1.md).
It refines the first pending threshold in the actual next interval of a genuine
post-material Context and its evolving newborn CP. It does not adopt a trajectory,
create an organ, consume a schedule item or issue an integrator checkpoint.

## Actual source and numerical event

`crop_supply_morphology_newborn_candidate.calculate_next_event_candidate(context,
raw_checkpoint, expected_sha256=..., time_tolerance_seconds_exact=...)` requires the
actual current owner/CP bytes, trusted SHA and current code/source/profile/rights.
The checkpoint must pass the newborn validator; no older typed handle or older
trajectory candidate is substituted. The tolerance is a closed, canonical positive
rational in seconds, bounded to128 decimal characters per numerator/denominator and
to the actual next original interval. Caller tolerance and original CP bytes must
remain unchanged through return.

Validate the actual current newborn RHS once, then compute the actual next original
shared-stage RK4 interval and its monotone dense shoot-clock polynomial. That
interval must bracket the first pending threshold. The function never searches
later intervals to make a nonbracketing request succeed. Exact bisection retains a
negative lower residual and nonnegative upper residual within the requested time
width, subject to the accepted precision limit. Select the upper bound without
snapping the computed age to the threshold. This is a synthetic numerical clock,
not an observed emergence time or certified ODE/biological error bound.

The same four stages supply the dense full state and partial continuous transfers.
Evaluate the real newborn RHS at that state and require its represented air-integral
age to have crossed the pending threshold. An unresolved precision or represented
rounding failure holds; no age, coefficient, geometry or tolerance is adjusted.

## Same-time diagnostics and exact accounts

At the selected exact time, independently integrate1,2 and4 substeps from the same
actual source CP. Preserve every C/age/area/length/cohort/climate coordinate and its
actual unit/organ identity. Return dense-to-one, one-to-two and two-to-four exact
coordinate differences. These local numerical diagnostics do not guarantee
agronomic accuracy or certify a global error bound.

Partial transfers are binary64 integration outputs. Pending branch totals add the
current CP's binary64 values and partial values as exact fractions; lifetime totals
add the exact current lifetime and those partials. Do not round the sum again or
turn a fractional candidate into an original-grid CP. Preserve point totals,
original/new construction costs, birth baselines and distinct physical-root versus
geometry-branch origins.

Reconstruct current-to-candidate local carbon/stock/age/geometry/heat/vapor equations
with explicit accepted roundoff budgets. Branch and global residuals/budgets must
equal their actual current CP values plus the local values. Physical global
accounts use the original root and actual births; geometry uses the original
supply-law geometry/inflow origins or actual new material seed. Reconcile current
organ clocks, nonnegative branch/lifetime potential deficits and canonical
diagnostics at the same selected time.

## Result, work and failures

The result binds actual source CP/Context, code pins, original interval/stage hashes,
exact root bounds/residuals, selected time, full layout/state, partial and pending
exact transfers, point/local/branch/global accounts, diagnostics and refinements.
It explicitly returns schedule_consumed=false, new_organs_created=false and
integrator_checkpoint=null, with a canonical calculation hash and G0–G4 not_assessed.

One current validation plus33 new RHS evaluations are required:4 original interval,
1 dense state and28 same-time refinement evaluations. Past integration, old biology,
material funding/points, leaf initialization, CP adoption and DB/network/write
operations are excluded. Source-owner preparation is measured separately.

Retain the2MiB result and original512KiB CP/inventory/horizon limits. Current and
late source/profile/code/tolerance failures return no partial candidate. Known
validation/numerical failures raise SupplyCandidateHold; unexpected RuntimeError
propagates. Trusted hashes are not independent farm custody or gate approval.

The next task must use this actual new-owner candidate for an explicit compatible
seed material point, followed by a genuine new owner and separately verified
single-consumption/repeated continuation. Stored-result/3D integration remains
later work, using the actual accepted states.

Evidence: [focused report](../research/crop-supply-morphology-newborn-candidate-20261028.md).
