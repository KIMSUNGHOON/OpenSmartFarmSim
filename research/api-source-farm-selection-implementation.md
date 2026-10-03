# Source to farm reference API implementation

Date: 2026-10-01. [HTTP contract](../contracts/api-source-farm-selection-v1.md),
[provider](source-farm-selection-implementation.md).

The existing `gpt-6.1-sol` / `xhigh` development CLI session documented in the
provider evidence was used. No recursive product CLI or external research was
launched. This change adopts no new data or agricultural/economic coefficients.

## Implementation and review

The authenticated GET binds an exact research/collection pair to the existing
closed source reference provider. `create_app` assembles it only from actual
owned research and collection services sharing one authority JobStore and
registry. Standard `ApiRuntime` uses that assembly without a new dependency,
store, schema, role or write scope. Existing source-history projections stay
unchanged. `contracts/openapi-v1.json` was exported from the implemented app;
all declared fields are required and extras are forbidden.

Review covers current ownership and authority, source/parent hashes, no writes,
closed errors and DTOs, canonical UUID paths, current read scopes and the
unchanged 30 s full-body client deadline. Selection returns fixed hold markers
and requires farm admission to revalidate every reference. No formula, tariff,
numeric default, crop output or approval was added.

The authored API workflow's existing API selection includes the new provider
and HTTP tests. It retains the same pinned images/dependencies and 25 min limit;
no new CI matrix or additional local heavy process was added.

## Verification

Local PostgreSQL **16.15**, disposable SCRAM databases/roles, existing fixture
source bytes, test context signatures and a fake CLI. From `backend`, with
`PYTHONPATH` unset and the existing registered PostgreSQL socket/binaries:

```text
nice -n 10 .venv/bin/pytest -q -s -x --tb=short --durations=8 \
  tests/test_api_source_farm_selection.py tests/test_source_farm_selection.py \
  tests/test_api_openapi.py tests/test_owned_source_history.py \
  tests/test_owned_research.py::test_optional_runtime_uses_stored_context_for_bearer_location
```

Final result: **66 passed in 82.19 s**. Includes seven provider/HTTP cases,
OpenAPI/security/schema cases, unchanged source history/recovery and standard
owned location assembly. Focused reruns are not additional distinct cases.

The actual standard TLS/Bearer/SCRAM case verified **12 full responses**, maximum
**0.582 s** with the existing 30 s limit. It required only five read scopes and
zero write scopes, checked owner equality/repeated reads/no new storage,
401 without authentication, all five missing-scope 403s, foreign/missing 404s,
and changed context 422 followed by restored current selection. Every response
was `no-store`; the request principal and owned server thread were cleaned up.
The independent HTTP contract case also checked absent assembly 503, no staged
snapshot 422, invalid UUID 422, and fixed public envelopes for private backend,
held-input and denied-access exceptions. Provider tests cover late corruption,
scope/pointer changes and mixed or unfinished parents.

`python -m app.api_openapi --check` passes. Workflow YAML and all five embedded
Bash scripts parse, changed local Markdown links resolve and whitespace checks
pass. Owned disposable databases/servers were removed; baseline PostgreSQL and
unrelated WSL processes remain.

## Failed attempts and corrections

The first composed run failed standard runtime assembly: the test provided an
actual `MarketSourceStore` with its storage profile disabled. Existing economic
scenario assembly explicitly rejects that mismatch. The test enables the
existing market source storage profile; server authorization was not relaxed.
The isolated corrected HTTPS case passed in 7.83 s, then the final composition
verified it again.

The next composed run passed the new HTTP/provider cases but failed the shared
OpenAPI missing-scope harness. That harness did not replace the new
`{collection_job_id}` path placeholder, so it sent an invalid UUID and received
422. Adding a canonical collection UUID to the existing path substitutions
restored the intended before-storage 403 checks. The failed runs (2 and 15
passes before failure) are not acceptance or added test counts. The final
66-case run verifies both corrections.

## Holds and publication

The exact earlier web commit `7f698e695d2ea5ba346d55f371fb916ed6a5c606` has
[seven successful authored CI selections](web-authored-economic-assessment-implementation.md#hosted-verification-of-the-web-commit)
and successful web/C0 CI. Its full backend CI was still running at this local
checkpoint. The new source/provider and API changes are committed locally
while that existing full run is allowed to continue. Hosted verification of
these new changes is pending; earlier results are not evidence for their code.

Matching existing market hold/economic candidate discovery and the general
region→farm web flow remain. Actual product CLI invocation, independent
custody/release, complete G1 and G0/G2/G3a/G3b/G4 are held. These tests cannot
authorize crop growth, harvest, purchased energy, future margin or ranking.
The full backend suite and PostgreSQL 18 were not rerun locally.
