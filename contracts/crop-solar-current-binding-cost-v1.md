# Solar current binding cost observation — v1

Predecessor: [original native result](../research/runtime-role-matrix-implementation-20261017.md).
The original64-step run remains incomplete. Before changing current validation,
measure the repeated validation cost inside one actual custody advance call.

Use the existing owned Solar worker fixture. Advance one real step, then profile
one further `advance(..., budget=1)` without changing the fixture input, equations,
rights, policy, implementation, stored proofs, or original unpaused programme.
Report before/after steps and UTC, `planned_steps`, call counts and inclusive/self
times for current binding, farm registration, audit and numerical chunk functions.
Function times overlap and include profiling overhead. Export no arguments,
locals, SQL, credentials, private records or unfiltered profile dump.

Acceptance: an actual advancing step and immutable previous proof/head identity;
source/probe hashes; no production Run or gate approval; actual test/guard exit,
all five protected roots/originals/two previews/resource limits and owned cleanup.
This is a component cost observation, not independent worker/API acceptance or
a claim about speed. Set the next implementation boundary from the observed
call graph; do not remove current source/rights checks based on assumed cost.
