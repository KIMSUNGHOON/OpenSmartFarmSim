# Owned collection discovery and foreground consumer v1

Status: implemented; focused actual SCRAM/process software acceptance passed
([evidence](../research/collection-consumer-implementation.md)). Source-consumer
Compose and actual product CLI/G1/G4 acceptance remain subsequent work.

## Fixed discovery boundary

`CollectionJobDiscovery(jobs, *, tenant_id)` uses the existing bounded,
read-only keyset discovery implementation. Its closed profile selects only
`collection` jobs with `owned-fixture-collection-input-v1`: due queued jobs and
expired collecting leases in the configured tenant. Live leases, future retries,
other stages/versions/tenants and terminal jobs are excluded. No public argument
selects a stage, active state or arbitrary input version.

The same immutable cursor/page records, limits (exact integer 1–50), canonical
input/hash verification, last-scanned cursor, current principal and audited
authority login apply. Collection discovery requires current `metadata`,
`artifact` and `collection_execute` scopes. It never claims work, publishes
records, approves sources or changes research decisions. The existing economic
profile retains its exact versions, simulation stage and execution scope.

## Foreground interface

`python -m app.collection_consume --factory trusted_module:build` loads an exact
`CollectionWorkerLoop` from an explicit trusted operator factory. The separate
one-job `app.collection_work` interface remains available. The factory constructs
one exact existing `CollectionWorker`; polling is an exact integer 1–60 seconds
and page size an exact integer 1–50. No job UUID is passed to the process.

The loop freezes worker/service/registry/store/tenant/lease bindings, uses the
same current authority principal, follows bounded discovery pages sequentially
and waits after each page. End-of-pass resets the cursor to revisit newly due
retries and expired leases. A concurrent claim may return no work. The existing
worker owns exact-ID claims, current parent/source/rights/input checks, heartbeat,
cancel/recovery and atomic collection-record publication. No second retry or
approval mechanism and no recursive CLI invocation are introduced.

Discovery/binding exceptions, malformed outcomes and unclosed attempts stop with
a fixed failure. Closed outcomes emit only version 1 `attempt` metadata: UUID,
attempt, state and reason code. Record bytes/hashes, input, credentials, lease
tokens and source contents are not logged. Startup/stopped events have no data
payload and idle pages produce no output.

SIGTERM/SIGINT stop idle polling promptly and prevent the next dispatch after the
signal is observed. An active worker finishes through its existing fences; forced
termination leaves recovery to its persisted lease. The shared signal mechanism
restores handlers/wakeup descriptor and closes owned pipes on all exits. Startup
failure exits 2 with `collection_consumer_startup_rejected`; unresolved execution
exits 3 with `collection_consumer_execution_unresolved`; graceful stop exits 0.

## Acceptance

Focused tests must check immutable profile separation, bounds/cursor following,
current access and binding/outcome rejection. Actual disposable SCRAM and separate
Python processes must demonstrate mixed-queue filtering without mutation,
automatic completion without a UUID argument, safe signals/cancellation, crash
then expired-lease recovery, current grant revocation and complete fixture/process
cleanup. The unchanged economic discovery and original collection worker regressions
must pass after sharing the profile-aware query.

The existing research executable, inputs and keys in these tests are synthetic.
Records retain `software_fixture_only`, Assessment hold and G0/G1 not accepted.
Actual source-consumer Compose, product CLI, independent release/custody, crop
validation/ranking and G4 deployment require their own evidence.
