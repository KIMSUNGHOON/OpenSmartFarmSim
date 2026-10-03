# Authored farm thermal candidate v1

Status: internal deterministic trajectory contract for
`farm-authoring-storage`, after [immutable authoring registration](farm-authoring-storage-v1.md).
This prepares the numerical artifact that a future independent reviewer and
publisher must verify. It does not grant G0/G1 or create an accepted Run.

## Provider and calculation

`calculate_authored_candidate(service, tenant, scenario_id, revision,
expected_scenario_sha256)` accepts **only** the exact installed
`FarmAuthoringService`. It calls `read_registration` before and after the
calculation so current tenant scopes, actual owned research, signed context,
source rights, Market hold, economic candidate and immutable input pins remain
valid. A changed byte or reference returns hold, never a partial result. The
output is two canonical, bounded (each ≤ 1 MiB) immutable trace byte strings.

Use the registered compiled numeric document and existing versioned `euler_step`
for exactly 120 one-minute steps across its two original weather intervals.
The first state is the authored initial condition; the second interval starts
from the exact final state of the first. At every step independently compute
one 60-second step and two 30-second steps, then apply the original registered
vapor, energy, state and delivered-heat convergence limits. Reuse the original
registered NWS law, SI conversions, weather, control rule and deterministic
binary64 operation order. A stability, saturation, nonfinite, nonintegral
interval or residual failure holds the entire candidate. No step is clipped,
filled, replaced or reported as crop growth or purchased energy.

Each trace has `candidate_version=authored-thermal-candidate-v1`,
`status=unpublished_candidate`, `claim_scope=synthetic_software_only`, the
exact farm registration/hash, authored numeric hash, original base snapshot,
context/binding hash, code hash, engine/unit versions, an interval and 60
time-stamped kernel steps with residual/convergence quantities. A candidate id
is derived from those immutable input/code bindings. It is **not** a published
`run_id`; there is no accepted trace shape or claim. The code hash covers this
calculator plus the existing physics/unit module and input compiler; the
future publisher must bind a complete runtime code/environment digest as well.

`verify_authored_candidate` recomputes through the same current authority and
requires exact candidate id and trace bytes/hashes. Its success establishes
replay of this registered numeric candidate only. An independent review,
versioned authored snapshot, distinct release authority, publisher proof,
worker transaction and 3D result projection are still required for G1.

## Verification

From `backend/`:

```bash
uv run --locked --group dev pytest -q tests/test_authored_thermal_candidate.py
```

The pure kernel tests compare all 120 results to the original fixture when
authored values equal it, and confirm changed facility/forcing values alter
the trajectory. They reject numerical instability/condensation and tampered
trace bytes. An actual SCRAM test must bind a persisted farm version, then
verify a reproducible two-hour candidate and reject a revoked current right.
These are software checks; no crop accuracy or G1 gate is accepted.
