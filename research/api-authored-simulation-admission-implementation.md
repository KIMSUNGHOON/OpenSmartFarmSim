# Authored simulation HTTP admission record

Date: 2026-09-30. Scope: authenticated admission of a signed authored farm
Run intent through the existing immutable `AuthoredSimulationService`. It
does not operate a worker or publish a new Run.

The closed request pins the review job UUID, farm ID/revision, registration
SHA-256 and idempotency key. The API uses the current Bearer principal and
passes the request to a runtime-owned service bound to the exact authored
Run store and preparer. The service checks current release, farm rights,
prepared trace/report identity and durable submission again at commit.
Conflicting stored intent remains a 409; missing or changed evidence is a
422 hold. Equal retries return the stored job status, even if that job has
subsequently completed.

Focused local software checks:

```text
uv run --locked --group dev python -m app.api_openapi --write
uv run --locked --group dev pytest -q tests/test_api_openapi.py tests/test_api_runtime.py tests/test_api_authored_runtime.py tests/test_farm_authored_simulation.py
77 passed, 11 skipped in 25.55s
```

The skipped local cases require disposable PostgreSQL SCRAM. The standard
HTTPS test exercises an exact retry of an already completed synthetic authored
job, scope denial and stale-preparation hold against the actual API and database.
On exact head `cc181cb`, [authored API run 36660968888](https://github.com/KIMSUNGHOON/OpenSmartFarmSim/actions/runs/36660968888)
passed **51 tests** against disposable PostgreSQL, including this HTTPS test.
The fixture uses fake CLI and signed
review authorities. Actual product CLI, independent review/release, a newly
admitted job completed by the runtime worker, G1 and G4 remain unproven.
