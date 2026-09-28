# Durable thermal simulation authority worker v1

Status: software execution candidate, not actual CLI/G1/G4 acceptance.

`ThermalSimulationWorker.run_once(job_id)` executes one explicit canonical UUID
under a configured tenant, with `simulation_execute`. The strict input is
`{input_version: thermal-simulation-input-v1, snapshot_id, review_job_id}`;
snapshot_id is the existing thermal content ID and review_job_id a canonical UUID.
Neither coefficients, time, raw sources, output, signatures nor gate decisions
are accepted from this job. Existing publisher checks the actual completed review,
signed context, source bytes, execution proof, independent release and physics.

The worker requires exact JobStore/ThermalG1Publisher/ThermalRunStore, identical
schema/DSN/SCRAM authority policy and principal function, and per-connection grants
audit on JobStore. No unbound owner path, CLI/credential default or source/release
mock is provided. The operator supplies and protects the existing dependencies.
This is an authority process; a general worker must not receive its DB credentials.

JobStore.claim adds optional canonical `job_id` scope. Targeted selection and
expired-lease recovery use that same tenant/stage/ID; default callers retain
existing behavior. A thermal worker never scans unrelated simulation jobs.

Publisher.prepare calculates and verifies a signed packet without publishing.
Existing publish still prepares and writes using the same validation path.
The worker prepares a private content-addressed receipt, locks/revalidates its
actual immutable job/input/current scope/live uncanceled attempt, validates and
inserts the Run, then closes the job/publication/event/outcome in one transaction.
The final UPDATE rechecks wall-clock lease expiry; any error rolls the Run back.
Unreferenced private artifact bytes from a rollback are not a public result.

The artifact binds run/snapshot/review job/context/review decision, report and two
trace hashes with synthetic-only thermal replay scope. Simulation is deterministic:
no simulation AI decision/capture is fabricated, and no model call is made. The
review decision remains a distinct referenced AI decision. Immutable source/release
versions and arithmetic are unchanged; new code needs a fresh independent release.

Missing publisher evidence yields an allowlisted fixed hold code, invalid input
a fixed fatal code. Lost leases/cancellation cannot publish. Failure closing a
lease leaves `unclosed` for existing recovery; commit uncertainty is not retried
automatically. An idle/completed/nonmatching target returns None. Retry creates
a new attempt under existing limits and repeats all publisher checks.

Actual process isolation, independent execution/release/custody, orchestrated
review/assessment, HTTP simulation submission, Compose/operator scheduling,
browser/full G1/G4 and external G0/G2/G3 remain pending. Synthetic captures and
controller-owned keys can test atomicity only, never attest real CLI or gates.

## Foreground invocation

`python -m app.simulation_work --factory operator_module:build --job-id UUID`
loads a trusted operator factory returning the exact worker type, then executes
that single target. Arguments are validated before loading. Secrets belong in
protected operator dependencies, not argv or repo defaults. Factory code must
protect its own output and must not launch a model during initialization.
Startup errors return 2 with a fixed JSON code; execution errors/unclosed leases
return 3 without automatic retry. A handled state or idle target returns 0 with
the actual structured result; exit 0 alone is never a gate acceptance claim.
The command accepts no raw input, tenant override, keys or owner provisioning.

The real Python child test uses synthetic protected config/keys/captures and
actual SCRAM, with no Codex credentials/environment or model call. It proves
software process/DB completion, not independent custody or real CLI/G1/G4.
