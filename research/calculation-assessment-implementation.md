# Joined calculation assessment implementation

Status: software candidate; actual product CLI and complete G1/G4 remain pending.

## Decision and scope

This ongoing root Codex CLI session is already `gpt-6-sol` / `xhigh`.
Actual turn metadata was checked at 2026-09-29T06:15:54.721Z in session
`01a0e064-b01b-7a22-8ef8-dd4afe0eb7dc`. No recursive Codex invocation was made.
The [contract](../contracts/calculation-assessment-v1.md) implements the first
synthetic final hold specified in PROJECT_SPEC/IMPLEMENTATION_SLICE. Completed
thermal and conditional economic jobs are joined under the actual same signed
decision context; unrelated calculations cannot be used for that assessment.

The generic assessment schema requires a crop profile, but no admitted crop
profile registry exists. This distinct closed input version preserves actual
completion pins with empty eligible crop/evidence arrays; it creates no fake
profile or approved candidate. The six server-owned hold categories preserve
missing market, common farm/calendar, local, future and paired-comparison
acceptance. Subsequent forecasting/ranking retain their existing dependencies.

## Implementation

CalculationAssessmentService reuses verified thermal job completion lookup and
EconomicCalculationService's full receipt/replay path. It checks actual stored
job input hashes, report/receipt/result hashes, signed context and market hold,
and repeats current scopes/store identity and preparation before commit.
CalculationAssessmentContract rechecks the complete input and requires parent
completion/context/Run timestamps before the assessment intent. The existing
DecisionContract validates the exact hold envelope and refuses selected crops,
claims, edited missing categories, context changes or proceed.

The authenticated 4096-byte POST accepts two UUIDs and an idempotency key.
ApiRuntime exposes the shared assessment service for actual stored sources.
The existing job/hold read paths preserve actual stored decision/hold evidence
and allowlist the six public categories; unknown private identifiers remain
grouped. OpenAPI is regenerated to 22 operations. Both new code modules are
included in the versioned runtime code digest. No dependency, SQL schema,
grant, thermal equation or economic arithmetic was changed.

## Verification

RED: the new test failed collection with ModuleNotFoundError for the missing
assessment module (one error in 0.11s). Initial integration exposed UUID
object/string boundaries in the existing completion/report readers; those
boundaries are converted explicitly. A temporary diagnostic also encountered
an economic worker requeue while versioned code was being edited during its
attempt; final verification uses stable code bytes. No diagnostic trace is
installed in application code or tests.

With OSSF_TEST_PG_DSN configured for the local PostgreSQL 16.15 fixture host,
the seven-file focused run completed with **132 passed in 2,266.96s
(0:37:46)**, no warnings or skips:

```sh
uv run --locked --group dev pytest -q tests/test_calculation_assessment.py tests/test_api_openapi.py tests/test_api_job_hold.py tests/test_api_runtime.py tests/test_thermal_publisher.py tests/test_api_economic_calculation.py tests/test_cli_contract_router.py
```

After final review, the assessment's scenario-v2 conditional scopes were added
to OpenAPI. The existing HTTP case gained actual conflicting-intent `409` and
private backend failure `503` assertions. Those two boundary/schema cases were
rerun: **2 passed, 37 deselected in 88.39s (0:01:28)**, no warnings; these cases
overlap the 132-case total. Six new integration cases cover actual joined
completion/HTTP/fake-CLI hold persistence, auth/body rejection, incompatible
parents, commit rollback, altered pins/chronology/claims and fresh Bearer runtime.
The publisher's default fixture behavior is included in the regression suite.

Locked dependency check resolved 31 packages, regenerated OpenAPI matched, and
508 local Markdown targets resolved. Five-axis review checked exact store/scope
binding, inherited arithmetic/replay, immutable chronology, private error
projection and the bounded metadata-only prompt. Full hosted checks at the new
functional head remain required; earlier head receipts are separate evidence.

All sources, signing keys, planning/release evidence and the executable in
these tests are self-authored synthetic fixtures. Publisher test setup now
accepts an explicit tenant/context reader/verifier so joined tests use the same
actual signed context. Default fixture behavior remains covered by its
existing regression suite.

## Remaining acceptance

Actual CLI execution and independent planning/execution/key custody/release,
complete farm/economic scenario orchestration, UI/3D, complete G1, provider
rights/adoption, local/future/paired validation and public operations are still
required. No broad task or gate checkbox is promoted by this increment.
