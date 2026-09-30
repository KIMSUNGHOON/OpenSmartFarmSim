# Authored simulation worker software evidence — 2026-09-30

The exact development Codex CLI session `gpt-6-sol`/`xhigh` added a targeted deterministic worker and pinned its source in the authored reviewer request. It consumes only `authored-thermal-simulation-input-v1`; other simulation jobs stay queued. The [worker contract](../contracts/farm-authored-simulation-worker-v1.md) requires the current release and owned farm before and inside the Run publication transaction.

`OSSF_TEST_PG_DSN=<local PostgreSQL 16.15 SCRAM test DSN> uv run --locked --group dev pytest -q tests/test_farm_authored_simulation_worker.py` passed **7 tests in 9.27 s**. They cover one actual leased simulation job, exact two-trace Run and receipt on a succeeded job, repeat consumption, unchanged neighboring fixed-fixture job, cancellation after preparation, missing or changing release, exception after insert, lease expiration after insert and malformed authored input. The latter paths leave no Run or job publication. The test runs a fake review CLI and synthetic release key, and replaces the full authoring preparer's method with a synthetic packet. It does not prove product model execution or independent review.

Authenticated authored Run read and browser replay candidates were connected
after this worker's original test. Their separate software evidence does not
establish product CLI execution, independent release or whole G1. The later
G0/G2/G3/G4 evidence gates also remain held.

## Foreground command extension — 2026-09-30

The existing `app.simulation_work` command now accepts an exact
`AuthoredSimulationWorker` from an operator-controlled factory as well as its
existing fixed thermal worker. Its argument, startup and unresolved-execution
handling remain the same. A focused local test supplies one authored worker,
asserts exactly one target call and checks the structured returned Run ID;
existing invalid-factory and unresolved-error cases passed. From `backend/`:

```text
uv run --locked --group dev pytest -q tests/test_simulation_work.py
8 passed in 0.67s
```

This test uses a constructed worker at the command boundary. The earlier
PostgreSQL worker tests cover transaction behavior separately; a protected
operator factory and real external reviewer release were not supplied here.
The authenticated admission, command, Run read and browser path still need
one actual end-to-end execution with product CLI and independent G1 evidence.
