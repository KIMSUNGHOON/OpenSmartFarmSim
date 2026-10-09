# Authored thermal trajectory candidate implementation

Date: 2026-09-30 KST. Status: internal, unpublished software candidate under
[farm-authoring-storage](../CAPABILITIES-farm-authoring.md) and its
[trajectory contract](../contracts/farm-thermal-candidate-v1.md).

The current development Codex CLI `turn_context` at
`2026-09-29T22:31:28.977Z` in
`rollout-2026-09-27T10-04-50-01a0e064-b01b-7a22-8ef8-dd4afe0eb7dc.jsonl`
records `gpt-6-sol` and `xhigh`. No recursive CLI was launched. This increment
does not make an agricultural, market or economic claim and introduces no
new physical coefficient or tariff.

The calculator accepts the exact owned `FarmAuthoringService`. It reads the
registered version through current scopes and source rights, computes the
authored 120-minute trajectory with the registered `euler_step` and the
original pre-registered residual/convergence limits, then rereads the same
registration. Its two canonical trace byte strings bind registration, farm,
numeric inputs, source snapshot, context binding and code hashes. A fresh
calculation verifies exact trace bytes. A failed step, missing current source,
changed registration or failed recheck returns no partial candidate. The
candidate has no accepted `run_id`, worker job or public projection.

## Focused verification

The RED collection failed because `app.authored_thermal_candidate` was absent.
The first integration attempts exposed only fixture import/type mistakes in
the new test; those were corrected before the following GREEN runs:

- `uv run --locked --group dev pytest -q tests/test_authored_thermal_candidate.py -k 'not actual_registered'`: **3 passed in 0.70 s**. A fixture-equivalent authored farm matches the existing model's temperature, humidity, heat, residual and convergence values at all 120 steps. Changing facility conductance and canopy evaporation changes computed state. Saturation introduced in the second hour holds the complete candidate.
- With `OSSF_TEST_PG_DSN` pointed to the isolated local SCRAM PostgreSQL test database, `uv run --locked --group dev pytest -q tests/test_authored_thermal_candidate.py -k actual_registered`: **1 passed in 58.36 s**. The test registers an owned farm, replays two stored-source hours, rejects a changed trace byte and rejects revoked current input rights.

The tests use self-authored synthetic inputs and synthetic test authorities.
They establish a deterministic software trajectory and current registration
binding only. Independent authored input review and snapshot release, complete
runtime code/environment custody, actual product CLI execution, approved Run
publisher, worker transaction, 3D projection and full G1 remain open. Crop
growth, purchased energy, margin forecasts and ranking remain unavailable.
