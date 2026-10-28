# Supply-limited next-event candidate, research v1

This additive internal module extends [the genuine continuation](crop-supply-morphology-continuation-v1.md)
and [the accepted construction policy](crop-supply-limited-morphology-v1.md).
It refines a candidate; it does not adopt a birth or issue a checkpoint.

## Inputs, source and work

`crop_supply_morphology_candidate.calculate_next_event_candidate(context,
raw_checkpoint, expected_sha256=..., time_tolerance_seconds_exact=...)` requires the
actual new supply-limited Context and its bounded canonical checkpoint with a trusted
SHA. An old trajectory/context/checkpoint is not substituted. A closed, canonical,
positive rational tolerance in seconds must fit the actual next original interval;
numerator/denominator strings are limited to128 characters each. The function owns
a copy of that input and rejects a changed caller value before returning.

Current code, exact original source/profile/access, complete140-state/101-channel
inventory in the QA case and the current sample/accounts are validated. Inventory
sizes come from actual source objects. One new current RHS is reused as k1. Four
new stage/endpoint calls build the same original-grid interval and exact shoot-age
certificate as the continuation. A next interval without the first pending threshold
holds; the function does not search farther or skip an event.

## Root and dense state

The exact dense thermal polynomial must have a strictly positive derivative minimum
and bracket the actual first unconsumed threshold. The already accepted pure bisection
helper narrows its negative/positive boundary within the explicit tolerance, with at
most128 bisections. This is a bound on that numerical polynomial, not a certified
ODE time error or observed biological emergence.

Choose the upper rational elapsed time, without snapping age to the threshold.
Use the original four stage derivatives/fluxes and their dense weights for the full
extended state and partial transfers. Validate the actual new RHS at that state.
If the represented air integral has not crossed after rounding, hold rather than
alter state, time, tolerance or threshold. Negative/unsupported intermediate stocks,
invalid thermal domains, lost changes and unresolved balances also hold.

The result binds the original CP, stage hashes, interval certificate, root interval,
upper time, full state/coordinates, explicit phase scope and unchanged source rights.
It does not reinterpret the selected state as a completed interval.

## Partial accounts and diagnostics

`crop_supply_morphology_candidate_books.py` reconstructs all physical and geometry
accounts at the actual selected time. Partial flow values are rounded once from
dense RK4 integration. Pending branch/lifetime transfers add those float values to
the actual current prefix **as exact fractions**; they are not prematurely rounded
back into an integrator CP. Point totals remain unchanged.

The actual current-to-candidate local residuals and arithmetic budgets compose exactly
with the current branch/global residuals and budgets. The root physical equations
are also reconstructed using the genuine original root, actual birth baselines and
unchanged point receipts. Appended ages/lengths are excluded from C sums. Geometry
checks preserve construction/realized/actual-inflow partition, internode stock mapping,
initial clock representation residuals and nonnegative integrated deficits.
Canonical gap and canonical-curve-minus-integrated-potential remain separate diagnostics;
no historical geometry or D0 is corrected to fit the new marginal policy.

Same-time1/2/4 partial-step reintegrations start from the same current state and k1.
They use28 new stage/endpoint calls, expose full states/transfers/accounts and actual
coordinate differences, and remain read-only diagnostics. Refinement states are not
adopted event points or ODE/agronomic error guarantees. Total per candidate:1 new
current +33 new stage/endpoint RHS calls. There is no past/old biological RHS,
material point, initialization, schedule consumption or integrator CP issuance.

## Return, limits and next boundary

Known input/source/code/rights/domain/numerical/account/precision/capacity failures
raise `SupplyCandidateHold` and return no partial candidate. Unexpected `RuntimeError`
propagates. Fences run again before return; caller checkpoint bytes stay immutable.
Existing512KiB checkpoint and2MiB context/result bounds and original research horizon
remain unchanged. This module adds no DB, network, worker, export or UI side effects.

The next material-point task must validate explicit seed C/dimension compatibility,
real parent/IDs, original costs and sensible/capacity transfers once, before issuing
new state or consuming any schedule item. Whole/repeated new-law growth and immutable
stored3D are later acceptance steps. All current outputs are software research only,
G0–G4 not_assessed, with no actual cultivar, farm forecast, margin or ranking claim.

Acceptance evidence: [focused implementation report](../research/crop-supply-morphology-candidate-20261028.md).
