# Versioned OpenAPI implementation evidence

On 2026-09-28, existing Codex CLI 0.157.1 session
`01a0e064-b01b-7a22-8ef8-dd4afe0eb7dc` implemented and reviewed the
[OpenAPI candidate contract](../contracts/openapi-v1.md). Its inspected local
turn context at `2026-09-28T10:15:54.920Z` records `gpt-6-sol` / `xhigh`.
No extra agent, recursive CLI/model call, farm data, research model invocation
or agricultural/economic coefficient was used. This is current-session
interface evidence, not independent release or runtime model approval.

Primary sources fetched that day:

- [FastAPI OpenAPI extension](https://fastapi.tiangolo.com/how-to/extending-openapi/)
  describes generation from actual routes, cached schemas and method wrapping.
- [FastAPI operation configuration](https://fastapi.tiangolo.com/advanced/path-operation-advanced-configuration/)
  describes stable operation IDs and merged `openapi_extra` metadata.
- [OpenAPI 3.1.0](https://spec.openapis.org/oas/v3.1.0.html#security-scheme-object)
  defines HTTP Bearer schemes, security requirements and extensions. Although
  3.1 permits non-OAuth role arrays, this contract uses empty Bearer arrays and
  an explicit vendor field for project AND scopes.

The API exposes eight implemented operations with stable IDs and Bearer scheme.
Each route's immutable scope tuple supplies both runtime checks and metadata;
the manifest's extra scope and the hold's three scopes remain required. The
typed Point now rejects extra fields, invalid bounds, strings and booleans;
valid registration response bytes have the same latitude/longitude shape.

The exporter generates actual route schemas using dependencies that refuse
operational access. It does not connect to a database, authenticate, collect or
call a model. The 47,405-byte sorted/pretty JSON snapshot is checked exactly by
the command and test suite. No unavailable future endpoint or credential is
advertised. Existing admission limits, temporal/gate constants, error envelopes
and conditional money strings are preserved. No package, SQL schema/grant or
immutable source/decision/manifest/release record changed.

Initial new tests passed **19 cases in 2.53 s** with locked dependencies.
They verify exact regeneration, FastAPI's OpenAPI structure model, local
reference resolution, Draft 2020-12 component validity, fixed operation sets/
IDs/errors/security, equivalent bad point rejection, all documented mandatory
scopes denied before reads, no exporter authority/store access, changed/missing
file rejection and real credential-free `python -m` check.

The existing real HTTPS API child now compares its authenticated OpenAPI JSON
to the committed snapshot before POST/GET operations. That child still uses
ephemeral synthetic TLS/Bearer, actual local SCRAM/PostgreSQL 16.15 and explicit
unused domain reader doubles. It is transport/schema proof, not a complete
runtime application or actual Codex execution. Combined OpenAPI, HTTPS, identity,
all existing API read/admission and thermal publisher/review checks passed
**166 cases in 54.02 s**, with no skips, using locked pytest and the local
`OSSF_TEST_PG_DSN`. `python -m app.api_openapi --check` passed separately.

API and public schema code now join the closed thermal digest, requiring fresh
independent release review. Snapshot/client compatibility changes must be
reviewed before regeneration. Remaining submissions, full protected operator
assembly, actual CLI, source/independent release, browser/G1 and public G4 are
still incomplete. Whitespace and changed-document local links are checked
separately; hosted exact-head CI is a later receipt.


## Hosted exact-head verification receipt

Commit `c079c53871031b11586f1fc49c4aadbdf5c77295` completed
[backend CI 36409914563](https://github.com/KIMSUNGHOON/OpenSmartFarmSim/actions/runs/36409914563):
**1,530 ordinary tests passed**, two existing Pydantic warnings, 325.89 s;
**4 distinct-UID tests passed**, 18.36 s, and the kernel DAC check passed.
[Compose CI 36409914569](https://github.com/KIMSUNGHOON/OpenSmartFarmSim/actions/runs/36409914569)
passed in 32 s. These receipts cover the OpenAPI commit. Subsequent market-login
changes require their own checks; the receipts do not accept production or G1/G4.
