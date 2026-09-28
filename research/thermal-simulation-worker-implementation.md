# Targeted durable thermal worker evidence

Status: authenticated deterministic worker software candidate, not real G1/G4.

Active Codex CLI thread 01a0e064-b01b-7a22-8ef8-dd4afe0eb7dc made this
interface/architecture judgment. Actual turn_context selectively inspected at
2026-09-28T12:35:14.700Z records exact gpt-6-sol/xhigh. The reviewable output is
[worker code](../backend/app/thermal_simulation_worker.py) and
[its contract](../contracts/thermal-simulation-worker-v1.md). No recursive CLI,
extra model call or subagent was used. This is not independent gate approval.

The explicit job target prevents this worker consuming other simulation models
or source-record jobs. A closed three-field input references the actual snapshot
and completed collection review. Existing source/context/execution/release and
physics checks remain mandatory. Publisher prepare emits no Run. The job's
actual live uncanceled attempt, input and current scope are checked under a row
lock; Run, publication, successful state/event/outcome commit together. Expiry
is rechecked after insertion and rolls back the transaction. Private orphan
content bytes from rollback are not a published result. No simulation AI decision
is fabricated. The foreground command accepts only a trusted factory and job ID.

## Focused receipts

New targeted claim tests first failed on the absent job_id argument; new prepare
test failed on its absent method; worker/foreground tests failed before their
modules existed. Targeted claim and old jobs/idempotency then passed 25 cases in
4.33 s, prepare/publisher/run store 27 in 8.28 s. Initial worker cases passed 14
before a test read snapshot_id from the wrong projection level; the corrected
success case passed in 3.32 s. Expanded worker/foreground cases passed 26 in
24.28 s; startup plus actual Python child passed 6 in 3.35 s.

Combined focused regression passed 177 cases in 89.43 s with locked Python 3.12
and real local PostgreSQL 16.15/SCRAM. It includes old job evidence, HTTP thermal
reads and runtime login contracts. OpenAPI --check passed unchanged. The final actual process normal/abrupt-exit recovery cases passed **2 in
6.51 s**. The child exits via os._exit(71) after inserting a Run, with no Python
transaction cleanup; actual DB connection loss rolls back both Run and job
publication. After explicit test-clock lease expiration, a fresh child succeeds
in attempt 2. The added unresolved/exception command boundary cases passed
**2 in 0.20 s** without retry. Final source, transaction, changed-link and
whitespace review passed before commit (**115 local links, none broken**).
Manual review inspected target/tenant/stage filtering, strict canonical input,
matching SCRAM bindings, current scope/live attempt checks, late lease guard,
Run/job transaction rollback, safe command errors and absence of fabricated
simulation decisions. Core SQL extraction preserves existing validation and
statement semantics; legacy publish remains guarded before opening a connection. No independent source or farm data was adopted.

## Limits

The child uses protected synthetic operator config, test captures, controller
keys and explicit fixture execution/release verifiers. Actual SCRAM, SQL rollback,
process exit and replay are software evidence only. An injected expired deadline or actual child process failure is controlled
fault testing, not a deployment restart record.
Independent actual Codex execution, release/context/credential custody, protected
operator provisioning, HTTP submission, workflow assessment, Compose/browser/full
G1/G4 remain pending. New modules enter the closed code digest and require a fresh
independent release; existing immutable sources and releases are unchanged.
Full hosted verification follows the implementation commit; whole G1 task
checkboxes remain open. No dependency or economic/physical arithmetic changed.

## Hosted receipt for fc5355b

[Backend run 36426026833](https://github.com/KIMSUNGHOON/OpenSmartFarmSim/actions/runs/36426026833)
completed successfully on exact head fc5355bf042de8bd413e9999c648fd8c0758e922:
PostgreSQL 18.6 ordinary suite **1658 passed, 2 warnings in 908.38 s**;
separate-UID service suite **4 passed in 19.46 s**, followed by successful
distinct-Linux-UID content access and cleanup steps.
[Compose run 36426026865](https://github.com/KIMSUNGHOON/OpenSmartFarmSim/actions/runs/36426026865)
also succeeded on that head. These are hosted software receipts, not G1/G4
approval; the two warnings are existing Pydantic serialization warnings.
