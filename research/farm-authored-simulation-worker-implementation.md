# Authored simulation worker software evidence — 2026-09-30

The exact development Codex CLI session `gpt-6-sol`/`xhigh` added a targeted deterministic worker and pinned its source in the authored reviewer request. It consumes only `authored-thermal-simulation-input-v1`; other simulation jobs stay queued. The [worker contract](../contracts/farm-authored-simulation-worker-v1.md) requires the current release and owned farm before and inside the Run publication transaction.

`OSSF_TEST_PG_DSN=<local PostgreSQL 16.15 SCRAM test DSN> uv run --locked --group dev pytest -q tests/test_farm_authored_simulation_worker.py` passed **7 tests in 9.27 s**. They cover one actual leased simulation job, exact two-trace Run and receipt on a succeeded job, repeat consumption, unchanged neighboring fixed-fixture job, cancellation after preparation, missing or changing release, exception after insert, lease expiration after insert and malformed authored input. The latter paths leave no Run or job publication. The test runs a fake review CLI and synthetic release key, and replaces the full authoring preparer's method with a synthetic packet. It does not prove product model execution or independent review.

No authenticated authored Run API or authored 3D projection is connected. Whole G1 and the later G0/G2/G3/G4 evidence gates remain held.
