# Source-bound economic candidate API implementation

Date: 2026-10-01 (Asia/Seoul). [HTTP contract](../contracts/api-farm-economic-candidate-selection-v1.md),
[provider acceptance](farm-economic-candidate-selection-implementation.md).
The ongoing development CLI uses exact `gpt-6.1-sol` / `xhigh`; actual product
CLI was not launched recursively. This change adopts no external data, tariff,
crop output or coefficient.

## Implementation and review

Two authenticated GET routes expose the closed provider catalog/current
selection contracts. `create_app` uses existing actual owned research,
collection and economic scenario services sharing the authority JobStore and
signed context. Standard ApiRuntime uses this assembly without a new factory,
store, schema, role or write scope. The eight required scopes are declared in
OpenAPI and checked before storage. Cursor pairs require exact UTC timestamps
and lowercase digests; records with invalid current rights are held on exact
selection. Errors use fixed closed public envelopes.

The catalog retains `requires_current_selection`, the exact selection retains
`requires_registration_recheck`, and both retain the source's software-only,
hold and G0/G1-not-accepted markers. Neither GET issues a hold/approval, writes
inputs or returns ledger numbers, rights bodies, signatures or raw data.

Existing authored API CI now includes the provider and API tests in its same
API selection. Pinned dependencies, PostgreSQL image, seven selection matrix
and 25-minute job limit are unchanged. YAML and all five embedded Bash scripts
parse using the system's existing YAML parser; no dependency was added.

## Focused verification

The local selection used one `nice -n 10` pytest,
`env -u PYTHONPATH`, Python 3.12 and disposable PostgreSQL 16.15/SCRAM roles:

```text
tests/test_api_farm_economic_candidate_selection.py
tests/test_api_openapi.py
tests/test_api_source_farm_selection.py
tests/test_owned_research.py::test_optional_runtime_uses_stored_context_for_bearer_location
```

Final result: **64 passed in 150.71 s**: three new candidate API cases,
57 OpenAPI/schema/before-storage scope cases, three existing source reference
API cases and the existing owned research standard runtime case. The provider's
five cases passed separately; repeated checks are not extra distinct tests.

The new standard HTTPS/Bearer/SCRAM case checked **20 full responses**, maximum
**7.844 s** against the unchanged **30 s** client limit. It uses only eight read
scopes and no write scopes. Two actual registered candidates paginate through
the exact timestamp/digest cursor without duplication; repeat current reads
match the provider. Unauthenticated, all eight missing-scope, foreign/missing
source, invalid-limit and revoked-current-rights responses have the expected
status and `no-store`. After rights restoration exact selection succeeds.
Storage counts stay unchanged, the request principal is cleared and the owned
HTTPS server/thread is stopped. Existing source HTTPS rechecks **12 full
responses**, maximum **0.603 s**.

The separate HTTP case checks missing assembly, missing candidate, non-UTC/
naive/one-sided/malformed cursors, uppercase candidate IDs, authentication and
fixed envelopes for private permission, hold and internal failures on both
operations. Shared OpenAPI checks verify all declared scopes before any storage
read, including the new canonical candidate path substitution. Closed response
schemas preserve required fields and the different verification markers.

The initial composed command used a nonexistent owned-runtime test filename,
so no tests ran. The corrected command selects the existing owned research
runtime node shown above. No server authorization or time limit was changed.
`python -m app.api_openapi --check`, changed Markdown file links and
`git diff --check` pass. The owned disposable PostgreSQL servers and test
processes were removed; baseline PostgreSQL and unrelated WSL processes remain.

## Evidence limits

Hosted PostgreSQL 18 has not verified this candidate API yet. Earlier pushed
commit `7f698e6` has separate successful authored/web/C0 workflows; its broad
backend run was still executing when this slice started. Those results do not
verify these new local commits. No full local backend or browser suite is
claimed for this backend slice. General source→farm web authoring, actual
product CLI, independent release, full G1 and G0/G2/G3a/G3b/G4 remain held.
