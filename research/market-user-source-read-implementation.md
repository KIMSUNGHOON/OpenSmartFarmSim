# Stored user-assumption read implementation

Date: 2026-09-29. Software candidate for the
[owner read contract](../contracts/api-market-user-source-read-v1.md), supporting
the economic input forms in the existing end-to-end plan. It is not whole
`api-flow`, `web-shell`, or gate acceptance.

## Judgment and boundary

The existing HTTP intake requires complete typed, immutable economic records.
The first web shell has no economic input hydration. A scalar profit form that
supplied missing dates, costs, quantities, rights, or context would bypass the
existing contracts. This change supplies owner-scoped discovery and exact
revision reads so the next form can preserve existing inputs and submit explicit
new versions through the existing intake. It does not choose a baseline,
generate defaults, sign context, calculate money, or approve assumptions.

Development occurred in the already-running Codex CLI session
`01a0e064-b01b-7a22-8ef8-dd4afe0eb7dc`. The actual turn context at
`2026-09-29T08:34:12.109Z` records model `gpt-6-sol`, effort `xhigh`. No recursive
CLI or runtime model invocation was made for this change. This development
metadata is not a product execution attestation.

## Implementation

- The actual MarketSourceStore supplies tenant/kind-scoped metadata pages,
  byte-ordered paired cursors, and full exact-version reads. Every returned row
  and pagination lookahead rechecks the canonical input/model, stored hash,
  admitting authority, store version, and original job bytes. Exact reads also
  compare the returned owner/kind/identity/revision with the request.
- The existing intake service enforces read/metadata scopes and the same audited
  JobStore/MarketSourceStore binding before and after reads. A read-only Bearer
  needs no write scope. Missing services return fixed 503, foreign records fixed
  404, and errors contain no record values or internal details.
- The record response's seven closed, discriminated types derive field
  definitions from existing canonical models, remove the owner field, and
  require every field, including nulls. The Store validates the original model
  before projection; derived response types do not replace adoption validators.
  The full stored hash still includes its owner and is not a hash of the
  redacted response. Responses are limited to 131072 UTF-8 bytes.
- OpenAPI adds listMarketUserSources and getMarketUserSource. Comparing the
  generated document to the previous committed document showed exactly these
  two added operations, no removed operations, and **no changed existing
  component schemas**. The snapshot now has 24 operations. New source payload
  and nested definitions account for 40 added schemas.

The derivation follows [Pydantic's documented field-definition pattern](https://pydantic.dev/docs/validation/latest/examples/dynamic_models/)
using `model_fields`, `asdict`, and `create_model`; field objects are not mutated
or copied as a schema shortcut. [FastAPI response models](https://fastapi.tiangolo.com/tutorial/response-model/)
provide the documented output schema and serialization boundary. Both official
sources were consulted on 2026-09-29; locked versions and dependencies are
unchanged.

## Verification

The focused commands use the local PostgreSQL 16.15 admin Unix socket to create
disposable actual SCRAM runtime identities and tables. Inputs, keys, and Bearers
are self-authored synthetic fixtures, not farm or market evidence.

- New reads initially failed with 404 before implementation. The owner-row
  substitution regression then failed with 200 for a valid foreign stored row;
  explicit returned-row identity checks now reject it with fixed 503.
- `pytest -q tests/test_api_market_user_source_read.py tests/test_api_market_user_source.py -x`:
  **54 passed in 76.31s**. This includes seven typed roundtrips, preserved nulls
  and strings, Unicode/slash identifiers, byte-order cursor pages, foreign/missing
  indistinguishability, denied/revoked scopes, binding/corruption failures,
  lookahead rejection, actual read-only Bearer/no-store runtime, a decimal string
  beyond JavaScript's exact integer range, and a legal response larger than
  65536 bytes. No input/job is created by reads.
- After adding revision-substitution and unavailable-service checks,
  `pytest -q tests/test_api_market_user_source_read.py -k 'returned_row or unconfigured'`:
  **3 passed, 32 deselected in 3.97s**. Both returned-owner and returned-revision
  drift are rejected, and unavailable services/authentication publish no fake
  data. The final read test file contains 35 cases.
- `pytest -q tests/test_api_openapi.py`: **35 passed in 16.12s**, including exact
  regeneration, valid local references/schema, all documented scopes before
  reads, and the credential-free CLI schema check.
- `pytest -q tests/test_api_runtime.py -k 'not real_foreground'`:
  **33 passed, 1 deselected in 5.36s**. The expensive existing foreground
  economic/grid process test was not repeated; the new read-only runtime above
  was exercised directly with actual SCRAM and middleware.
- An earlier broader run passed the 22 existing MarketSourceStore cases,
  including signed economic/grid replay, but its initial read test version had
  two test setup/expectation failures (runtime profile and a second rebound
  lookup). Those were corrected and rerun above. That broader run is not cited
  as an overall pass. A run without the admin DSN skipped nine cases; those
  skips are excluded from acceptance evidence.

The full backend suite is delegated to the existing hosted workflow at the
new pushed head and is not a local pass claim. No new dependency, migration,
grant, credential default, record mutation, arithmetic, UI, external adapter,
actual model invocation, independent release/review, G0/G2/G3a/G3b/G4 or whole
G1 evidence is supplied. New code requires fresh release evidence. Existing
task checkboxes and holds remain unchanged.
