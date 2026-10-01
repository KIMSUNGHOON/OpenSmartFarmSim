# Authored thermal Run to conditional economic calculation

Date: 2026-10-01 (Asia/Seoul). This development turn follows the mandatory
Codex CLI `gpt-6.1-sol`/`xhigh` policy in current session
`01a0e064-b01b-7a22-8ef8-dd4afe0eb7dc`; selected invocation metadata was recorded
in [the model migration evidence](cli-model-migration-implementation.md).
This is software development evidence, not a new product model invocation.

## Implementation boundary

The [contract](../contracts/authored-economic-execution-v1.md) adds the closed
economic input/receipt V3 for the actual authored thermal Run store. The
existing V1 generic and V2 farm replay paths retain their identity and formula.
The extra authored identity and registration hash cannot be dropped or replaced
with client supplied completion evidence. The existing HTTP endpoints and
deterministic worker use their configured actual store; absent authority holds
V3. The standard HTTPS runtime supplies that same authored store.

Verified authored completion discovery now shares one actual Run read with its
existing display projection and returns internal immutable input/receipt/report
pins. The new economic binding rechecks the actual current owned farm
registration, economic candidate, rights and decision context. It fingerprints
registration/server bindings, numeric input, release and parent job/input/
receipt/report/Run before admission and throughout fenced publication.
Result and monthly cash reads repeat current binding checks and retain the
existing public DTO. Receipt implementation pins include the new binding and
completion helper. No dependency, role grant, table or numeric formula changes.

## Verification

- Existing authored Run HTTP reads: **2 passed in 4.37 s** against PostgreSQL
  16.15/SCRAM. An initial invocation used the wrong test environment variable
  and skipped both cases; the corrected run supplied `OSSF_TEST_PG_DSN` and
  `OSSF_TEST_PG_BIN`. Skips are not counted as acceptance.
- Existing generic/farm replay economic regression: **14 passed** in the first
  604.77-second selection. That selection also had one failed HTTPS fixture:
  its synthetic completion lacked the newly required current reviewer/store
  relationships. The fixture now binds its reviewer, jobs and thermal store;
  the real binding checks were retained.
- Closed authored economic input/request and untrusted store checks: **10
  passed**; the first actual authored-parent HTTP money/cash/retry/current-rights
  case also passed. That 378.50-second selection stopped at a second case's
  fixture `KeyError: input_bytes`: a public submitted job reference does not
  contain raw input. The test now reads verified immutable bytes from the
  actual JobStore before creating its pending parent.
- Corrected remaining selection: **55 passed in 362.25 s**. This includes the
  two remaining real SCRAM authored economic cases, the standard actual HTTPS
  runtime case and 52 OpenAPI checks. Mixed farm/version/candidate, unknown or
  pending parent, foreign tenant and missing authority are rejected. Removing
  an authored read scope at admission rolls back the intent and event; scope
  or numeric binding changes after result insertion roll back result,
  publication and success and close with hold while authority remains.
- In total **82 distinct focused tests passed** across these terminal selections.
  OpenAPI was regenerated through `python -m app.api_openapi --write`; its exact
  byte check, local schema references and conditional V3 scope tests passed.
  No numeric formula or money/quantity coefficient changed.
- The authored PostgreSQL 18 workflow explicitly includes both new test modules.
  Hosted proof for this new commit is pending; the older completed web
  assessment workflow is recorded in its own evidence file. The complete local
  backend suite and a new money/assessment browser flow were not run.

Code review covered the closed version/scopes, matching actual authorities,
current source/release reads, canonical hashes/receipts, no fallback, fenced
rollback and preservation of prior inputs/DTOs. Work is bounded to one parent
and the existing two 60-point traces. Repeated authority checks remain; no
cache or latency improvement is claimed. Local heavy tests ran sequentially
with `nice -n 10`; their disposable clusters were cleaned on termination.

The new SCRAM integration harness runs the actual authored registration,
test executable CLI review, signed test execution/release, authored worker and
stored Run, then tests HTTP admission, stable retry, conditional economic
completion and public money/cash reads. Initial completed review and candidate
are frozen after verification to bound test cost, as in the existing software
chain test. The new registration/source/rights/parent checks remain actual and
are mutated in negative tests. Synthetic signer keys do not provide independent
custody or agricultural evidence.

## Remaining work and holds

Paired authored Assessment, economic web parent selection and the general
region/source/farm flow remain subsequent tasks. Heat-to-purchased-energy/cost
conversion still requires actual efficiency, metering and tariff evidence.
Actual product CLI with the new model, independent release, G1 and subsequent
G0/G2/G3a/G3b/G4 acceptance remain held. No crop growth, harvest, future margin,
ranking or production claim is opened by this software connection.
