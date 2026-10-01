# Authored thermal/economic parent assessment join

Date: 2026-10-01 (Asia/Seoul). Development follows Codex CLI
`gpt-6.1-sol`/`xhigh` in session
`01a0e064-b01b-7a22-8ef8-dd4afe0eb7dc`; selected actual session metadata is
recorded in [the model migration evidence](cli-model-migration-implementation.md).
This document records software evidence, not another product model invocation.

## Boundary

The [authored assessment contract](../contracts/authored-calculation-assessment-v1.md)
extends the existing closed three-field assessment POST with a server inferred
input V3. Only actual authored thermal V1 and economic V3 completions form this
pair. Its exact job/input/receipt/report/Run, registration, numeric/server
binding, release, snapshot and signed decision-context pins are rechecked.
Both immutable authored traces must match the current registration/context.
Mixed paths cannot silently become generic assessments.

The API and standard runtime share the actual configured authored store.
The owned CLI router selects a distinct `calculation-assessment-server-v3`
validator; prior V1/V2 assessment inputs retain validator V2. Current scopes,
stores, parent completion, source rights and immutable prepared bytes are
checked again before committing the intent and at CLI validation. No table,
dependency, role grant or arithmetic formula is added. The six existing hold
categories, empty crop/evidence selection and refusal of claims/proceed remain.

## Verification

- Pure authored parent binding: 12 passed in 0.58 s; the same cases plus two
  invalid owned-router configuration checks passed in 0.79 s (14 distinct).
- Existing OpenAPI, generic/farm assessment and shared owned-router regression:
  65 passed in 941.17 s against PostgreSQL 16.15/SCRAM.
- New actual SCRAM authored assessment cases (three), standard HTTPS case (one)
  and revised existing assessment browser case (one): **5 passed in 1498.05 s**.
  The V3 pair pins, distinct validator, actual fake-CLI held decision/evidence,
  public hold projection and stable retry passed. Altered pins and chronology,
  proceed/selected-crop/claim/missing-code proposals, mixed versions, pending
  jobs, foreign tenants and missing/mismatched authority were refused.
  Scope, store and source-right changes after submission and altered prepared
  numeric pins rolled back intents/events without a partial assessment.
- Actual standard HTTPS/Bearer/SCRAM V3 admission and persisted CLI hold read:
  **8 responses**, **6 hold categories**, maximum response **25.346 s**, with
  the existing **30-second** client limit. This includes anonymous/denied/foreign
  refusals, admission, identical retry, status/report reads and held retry.
- Corrected stored-authored-Run and existing assessment HTTPS/Chromium selection:
  **2 passed in 185.96 s**. The assessment browser was then repeated in the
  five-case selection with its revised worker barrier: **one POST, five HTTPS
  responses, six hold categories, zero console errors**. Its fake worker took
  **51.484 s** with the existing 300-second lease; HTTP remained limited to 30 s.
- Across these selections **83 distinct focused tests passed**. The two invalid
  router cases are included in the 65-case regression, and the repeated browser
  case is counted once. OpenAPI exact bytes, JavaScript syntax and whitespace
  checks passed. Local Markdown link verification also passed.

## Observed hosted regression and diagnosis

[Hosted run 36795417197](https://github.com/KIMSUNGHOON/OpenSmartFarmSim/actions/runs/36795417197)
on commit `223e926f6b0a868c828bb2429b000e245570f6c2` completed with failure:
95 server tests passed in 992.15 s and the new-authored-job full browser path
passed (120 points, eight HTTPS responses, console errors zero), but two other
browser cases failed. The stored authored Run fixture omitted its actual
completion review/jobs/runs relationships. It now supplies those relationships;
the production binding checks remain. Local actual HTTPS/Chromium then verified
its 120 points, three successful responses and zero console errors.

The assessment browser failed with BrokenPipeError after admission and worker
execution. Its reader had a fixed 60-second offline worker barrier; the hosted
call took 85.08 seconds including admission and worker processing. This suggests
that barrier expired while the worker rechecked evidence. The first local
reproduction passed, so that timing cause is an inference, not a captured
hosted browser stack. Worker timing and redacted exit diagnostics now remain
in the harness. Its offline barrier uses the actual bounded 300-second test
worker lease, while the product HTTP client limit remains 30 seconds. The two
local browser cases passed in 185.96 s before that barrier change; the revised
assessment barrier passed in the five-case selection above. Hosted confirmation
of the corrected commit remains pending.

The prior hosted job used 24 minutes for server and browser setup/checks against
its 25-minute limit. The workflow now separates API, authored economics,
authored assessment, authored assessment HTTPS and browser selections into
isolated matrix jobs with the same 25-minute limit, disposable PostgreSQL 18
and cleanup. Only the browser
selection installs Node/Chromium. Every previously selected test is retained;
the new authored assessment modules are explicit. This is a workflow split,
not evidence that the new hosted selections have passed. Matrix and failure
handling syntax were checked against [GitHub's official matrix
documentation](https://docs.github.com/en/actions/how-tos/write-workflows/choose-what-workflows-do/run-job-variations)
on 2026-10-01; no floating action versions or dependency changes were adopted.

## Review and practical limits

Review covered correctness (whitelisted parent pairs, canonical bytes, context,
chronology and exact pins), cohesion (reuse of actual verified completion and
existing service/router/DTOs), security (current roles/rights, closed input,
private projection and transactional rollback), performance (bounded two-trace
parent reads and the measured HTTP limit) and product semantics (held-only
assessment, no numerical/recommendation claim). Existing validator labels and
caller-key identity remain; no numeric coefficients or money formula changed.

Heavy local checks ran sequentially at `nice -n 10`; test server/browser and
disposable database cleanup completed. The full local backend suite and a new
authored economic/assessment browser orchestration were not run. One local
HTTPS timing observation does not establish a production latency guarantee.

## Holds and remaining work

The SCRAM harness uses a fake CLI executable, test execution/reviewer signatures
and the existing authored economics fixture. That fixture verifies its initial
review/candidate once and freezes them for subsequent setup; actual current
registration, rights, parent jobs and new assessment validation remain active.
These fixtures do not prove independent custody, actual model execution,
agronomic validation or G1 acceptance.

Authored economic/assessment parent selection in the web and the general
region/source/farm orchestration remain subsequent tasks. No new browser UI is
implemented here. Actual product `gpt-6.1-sol`/`xhigh` execution, independent
release and G0/G1/G2/G3a/G3b/G4 evidence remain held. Heat-to-purchased-energy
costs, crop growth, harvest, future margin and ranking are not introduced.
