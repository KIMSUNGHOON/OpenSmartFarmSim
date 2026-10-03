# Authored farm input HTTP implementation record

Date: 2026-09-30. Scope: internal authenticated intake and read of an existing
immutable, self-authored synthetic farm input. This is software evidence only.

The `FarmAuthoringService` already stores a tenant-owned input version and
rechecks current source, rights and numeric compilation on read. The API now
accepts a bounded, duplicate-free JSON request with its exact Pydantic schema,
then delegates registration to that service under the current Bearer principal.
The GET route returns only digests, version identity and intent job status.
`ApiRuntime` assembles this service only with its owned research and farm replay
authority. The OpenAPI snapshot includes both routes and their scopes.

Local check:

```text
uv run --locked --group dev python -m app.api_openapi --write
uv run --locked --group dev python -m app.api_openapi --check
uv run --locked --group dev pytest -q tests/test_api_openapi.py tests/test_api_runtime.py tests/test_api_farm_authoring.py
75 passed, 11 skipped in 24.85s
```

The skipped local cases need `OSSF_TEST_PG_DSN` and an actual disposable PostgreSQL
SCRAM login. The database test covers authorized intake, exact retry,
conflict, malformed/oversized/wrong-media requests, per-scope denial, foreign
tenant isolation and a current-evidence hold. On exact head `cc181cb`,
[authored API run 36660968888](https://github.com/KIMSUNGHOON/OpenSmartFarmSim/actions/runs/36660968888)
passed **51 tests** against disposable PostgreSQL, including this database
test. No browser authoring form or whole farm Run submission is included.
Product CLI execution,
independent release and G1/G2/G3/G4 remain on hold.
