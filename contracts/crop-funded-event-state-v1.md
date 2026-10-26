# Candidate state and transfers at a funded thermal threshold, v1

`crop_funded_event_state.calculate_funded_threshold_state` accepts the same explicit source
selection/tolerance as the [root locator](crop-funded-event-time-v1.md). It returns a research
candidate and local refinement results, with no checkpoint, new organ or G0–G4 approval.
Capture an isolated input copy and return every source root/index and requested tolerance
in `selection`; caller mutations must not change either the calculation or its recorded inputs.

## State at the selected time

The selected exact elapsed time is the **upper bound** of the certified increasing cubic-root
interval. It is on the crossed side, within the declared root-isolation width; it is not the
exact mathematical root or physical emergence time. Do not snap a shoot/leaf age to a threshold.
The original root certificate, source checkpoint/step/sequence, IDs/layout and all existing
prefix/point ledger blocks remain bound. The source prefix and pending local transfers remain
separate; this API does not compose a replacement global checkpoint or overwrite old bytes.

Reconstruct the original four shared RK4 stage vectors/rates/fluxes and require their hashes
to equal the root certificate. Apply the same [third-order dense weights](crop-funded-event-time-v1.md)
to **every state component and continuous transfer**, using exact fractions of original binary64
inputs and exact source time. Each combination is rounded once to binary64; reject nonfinite,
nonzero underflow or a nonzero state change lost to rounding. This is a new numerical candidate
version, not a bit-equality claim with the original multiply-then-add integrator at arbitrary times.
Evaluate the complete existing RHS at the candidate to enforce its domains and derived quantities.

## Conservation and refinement

At the selected state, check local whole carbohydrate, fruit number, canopy/air sensible energy,
vapor, canopy capacity, reduced energy, and each leaf's age/carbon against all partial transfers.
Use the original balance equations and units with exact rational sums of represented inputs,
including exact duration in age balances. The numerical roundoff budget retains the original
`64*(steps+1)*ULP(scale)` rule; a dense partial interval counts as one interval. No new biological
coefficients, absolute epsilon, area-to-carbon conversion or heat from respiration are introduced.
The original left checkpoint's global/point balances remain source evidence, not newly calculated
global balances. Fractional prefix composition belongs to the next continuation version.

Independently integrate from the same left vector to the **same exact selected time** with
1, 2 and 4 equal classical RK4 substeps. Each shared stage's state updates and transfer quadrature
use exact rational time/coefficient combinations followed by one binary64 rounding. This method
is explicitly versioned and preserves the original source method separately. Each accepted
refinement endpoint must pass the existing RHS domains and the same exact local ledger equations;
each intermediate refinement RHS stage must pass its existing domains. Return every refinement's
state, transfers, ledger budgets/residuals and exact step size. A refined path need not cross the
thermal threshold at the selected dense time. Its difference is a local discretization diagnostic,
not a certified ODE error bound or a new event root. Prior integration/measurement/parameter errors
remain outside this diagnostic. Dense-curve domain validity between the selected samples is not
asserted.

## Bounds and acceptance

Keep original graph/profile/code/rights/selected-stem checks and late leaf/stem/source fences.
The result is at most 2MiB; original leaf/scalar/horizon caps remain. Only the selected interval
and local refinements are calculated. With 1/2/4 substeps: root5 + original stages4 + dense RHS1 +
refinement31 = **41 RHS evaluations**, no past-interval advance/DB/CLI/network/write/birth adoption.
On domain, replay, roundoff, ledger, source or capacity failure, return no candidate/checkpoint.

Acceptance requires original root/funded phase and prefix/ID/time preservation, independent
high-precision dense states/transfers and exact ledger equations, nonlinear analytic convergence
of the new RK4 arithmetic, measured local refinement differences, numeric/dimension/size boundaries,
replay/late-source/rights failures and zero effects. Full fractional-event CP/cursor/prefix/point
application/remainder and split-resume equivalence remain the next implementation task.
Then bind source stem attachments and explicit floor/initial carbon/funding/current review,
store the coupled result, and connect its actual state to realistic leaf meshes.
