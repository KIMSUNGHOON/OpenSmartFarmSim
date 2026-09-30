# Authored thermal Run HTTP read — 2026-09-30

The exact development Codex CLI `gpt-6-sol`/`xhigh` session added a separate
authenticated read surface for currently verified authored thermal Runs. The
[contract](../contracts/api-authored-thermal-run-v1.md) keeps authored IDs out of
the fixed-fixture routes and projects only bounded 120-point thermal values.
The job discovery route checks the completed simulation job, exact input
digest, publication attempt/manifest and stored Run link. The Run store
rechecks the receipt, gate HMAC, current signed release, farm registration and
rights before projection. The HTTP layer returns generic unavailable errors
without source, signature or CLI capture text.

An existing review verifier required `collection_review_create` even when a
reader was only rechecking completed evidence. `verify_input` now uses farm
read scopes while review admission still requires the create scope. The actual
authored registration test confirms read verification after the create scope
is removed and rejects a new submission. This preserves read-only browser
access without granting review submission authority.

`OSSF_TEST_PG_DSN=<local PostgreSQL 16.15 SCRAM DSN> uv run --locked --group dev
pytest -q tests/test_api_openapi.py tests/test_api_authored_thermal.py
tests/test_farm_authored_simulation_worker.py` passed **51 in 34.58 s**.
After the read-scope change, focused actual registration, signed completion,
synthetic release, API and worker regression passed **13 in 573.61 s**. The
API tests compare job discovery, summary and all 120 stored points; reject
missing/foreign jobs, missing scopes, invalid IDs, a fixed-fixture route and
changed current preparation. The OpenAPI snapshot was regenerated and checked.
After tightening scenario identifiers in the public schema, the final OpenAPI
and authored HTTP regression passed **44 in 24.87 s**, and the locked OpenAPI
`--check` command passed.

The API test uses a fake CLI, constructed reviewer proof and a stubbed authored
preparer. The separate review test exercises a real registered input and
synthetic signed completion; neither is actual product CLI or independent
release evidence. `ApiRuntime` does not yet assemble the authored Run store,
and the web 3D view still uses fixed-fixture endpoints. HTTPS end-to-end
authored replay, real product CLI, G1 and all later scientific/operational
gates remain held.
