# Funded RK4 thermal threshold root, v1

`backend/app/crop_funded_event_time.py` is a research calculation over a rights-checked
immutable funded-leaf graph and its selected original stem state. It returns a numerical
root interval, not an event checkpoint, new organ, biological prediction or G0–G4 decision.
Existing source models, saved graphs, continuation grid and readers remain versioned as before.

## Input and source replay

`locate_funded_shoot_threshold` takes both source directories/root hashes, content access,
the original stored stem index, an explicit bracket index and a positive reduced rational
seconds tolerance no larger than the original step. Indices reject booleans. The original
epoch projection supplies the threshold/sequence, exact source times, two checkpoint hashes
and initial shoot age. The interval must contain exactly one original grid step in the same
population/context. Current use/transform/display grants, complete graph/code/profile hashes,
original curve/anchor/history and late source fences remain required.

From the original left vector and frozen program/profile bytes the calculator evaluates
the same ordered four RK4 stages plus the endpoint (five RHS evaluations). The entire endpoint
sample and every segment/lifetime integrated transfer must match the original canonical
binary64 values. Only this interval is reconstructed; earlier intervals are not reintegrated.
No birth point, DB, CLI, external service or write is needed. The read-only replay API itself
continues to do no ODE work; this is a separate calculation entry point.

## Method and root certificate

Use the explicit classical-RK4 **third-order continuous extension**, equation (28) of
[Izgin-Melnikov, DOI 10.1007/s42967-025-00480-8](https://doi.org/10.1007/s42967-025-00480-8),
with the existing four shared-stage air temperatures as the integral's derivatives.
This adopts the explicit RK formula, not that article's implicit MPRK schemes or positivity claim.
For `theta in [0,1]`, weights are
`theta - 3theta²/2 + 2theta³/3`, `theta² - 2theta³/3` (twice),
and `-theta²/2 + 2theta³/3`. Subtract `Tb * theta * h`, divide by `86400`,
then add the source left shoot age minus its threshold. All coefficients, comparisons,
quadratic derivative minima and bisection arithmetic use exact fractions of original binary64
values. There are no newly selected biological parameters or clipped temperatures.

The derivative's exact minimum over the closed unit interval must be strictly positive.
Checking just the four temperatures is insufficient because one dense weight is negative.
The cubic must strictly precede the threshold on the left and reach it on the right.
This certifies one increasing root of **this polynomial**, including a root at the right endpoint;
it does not establish uniqueness or error bounds for the continuous physical model.

Exact bisection returns lower/upper elapsed seconds, signed thermal residuals, width and
iteration count, bounded by 128 iterations. Width must meet the explicit tolerance.
There is no endpoint linear interpolation, original fixed-22°C event time or arbitrary animation.
The result records four stage hashes/temperatures, source projection hash, original bracket,
method/code versions, and the exact ideal-cubic versus stored-rounded endpoint age difference.
That difference is reported, not corrected by changing the curve; if rounding removes the cubic
bracket the calculation holds. Endpoint replay is exact; the cubic's ideal endpoint need not
equal the rounded cumulative integral.

## Acceptance and remaining dependencies

Require algebraic dense order conditions, nonlinear analytic convergence, strict monotonicity
and endpoint/precision rejection, original stored crossing with all-state/transfer equality,
independent high-precision root/residual checks, code/rights/source/limit fences and no writes.
The time width bounds only numerical root isolation error in this cubic. Discretization,
prior accumulated integration, parameter and measurement errors remain unbounded here.

Next: event-state/transfer balance and domain checks at that time, original-grid remainder,
new numerical checkpoint/cursor/prefix semantics, and step-refinement validation. Those require
a separate version before any transition is adopted. Then bind new internode/leaf IDs, explicit
initial carbon/floor/funding and original stem attachment, store the coupled result, and render
the same state in actual-leaf 3D. Current G0–G4/R2, real cultivar/local independent data,
full cycle/resources/economics/autonomous comparison and final UI remain open.
