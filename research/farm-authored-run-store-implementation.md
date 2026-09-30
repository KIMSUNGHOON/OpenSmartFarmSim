# Authored Run storage boundary evidence — 2026-09-30

The exact development Codex CLI session `gpt-6-sol`/`xhigh` added an owner-installed `authored_thermal_runs` table and an opt-in v8 SCRAM grant profile. This is an internal [schema contract](../contracts/farm-authored-run-store-v1.md), not Run publication.

With the local PostgreSQL 16.15 test cluster, `uv run --locked --group dev pytest -q tests/test_farm_authored_run_store.py tests/test_farm_authored_release_store.py tests/test_runtime_login.py::test_direct_authenticated_identity_and_idle_connection` passed **7 tests in 5.75 s**. The tests verified v8 effective grants through the audited authority login, confirmed request, worker and supervisor logins cannot select this table, rejected v8 without release custody, and reran v7 packet storage and baseline login identity checks. No Run row, simulation worker, signed gate report or independent release was exercised. All G1 and domain/production gates remain held.
