# Farm calculation assessment implementation

Date: 2026-09-30 KST. Status: verified software implementation candidate.
This document is not full G1, source adoption, agricultural
validation or production acceptance. Scope:
[farm join contract](../contracts/farm-calculation-assessment-v1.md).

## Development and implementation

The existing development Codex CLI session records `gpt-6-sol`, effort `xhigh`,
in its `turn_context` at `2026-09-29T15:30:20.126Z`, rollout
`rollout-2026-09-27T10-04-50-01a0e064-b01b-7a22-8ef8-dd4afe0eb7dc.jsonl`.
No nested CLI was launched. Integration workers use a fake CLI and test-owned
release/signing keys; they cannot establish actual product model invocation
or independent custody/release acceptance.

The unchanged POST body names the actual completed thermal/economic jobs.
The server infers assessment input v2 only from thermal v3/economic v2 parents.
It requires the economic parent's exact thermal job UUID, then verifies the
same farm ID/revision/input hash and derived bindings. Mixed versions and
another job with the same Run ID cannot downgrade to legacy admission.
The original v1 API idempotency namespace spans both internal input versions.

Existing completion readers retain their public projections and validation.
An internal economic completion carries its verified result, receipt and,
for farm v2, the already verified thermal completion. That thermal completion
retains its accepted stored packet. Assessment consumes these records inside
the same guarded call, instead of fetching/replaying those results again.
There is no caller-supplied proof, reusable cache or validation-skip parameter.
The server still fully re-prepares both pins before commit and at CLI input
parsing/authority lookup. Farm scopes remain required at the final commit guard.

ApiRuntime supplies its exact farm service to assessment admission and exposes
that assessment service. An operator must install its shared CLI router/worker;
the API does not create an operating CLI worker. Router and assessment validator
versions become v2; both assessment input versions remain routed.

All six ordered missing-evidence codes remain. The partial replay selection
does not establish the complete agricultural FarmScenario. No crop is selected,
no forecast or ranking is approved, and a valid hold publishes no recommendation.
Physics, Decimal arithmetic, schemas, roles, dependency locks and the web viewer
are unchanged. Application changes produce a new publisher code digest.

## Verification observed so far

- The initial actual SCRAM fixture completed both farm parents, then failed
  because the assessment constructor did not support the farm service:
  **1 failed in 174.91s**. This established the missing connection before coding.
- OpenAPI initially detected the changed conditional scopes against the old
  JSON snapshot: **3 failed, 36 passed in 18.97s**. After reviewing and generating
  the additive scope diff: **39 passed in 18.78s**. No public schema or operation
  was added. A subsequent locked `--check` passed.
- Exact cash projection tests: **10 passed in 0.55s**.
- Earlier integration runs were deliberately interrupted for review fixes to
  cross-version idempotency and the final conditional-scope guard. Terminal
  tool results were observed before editing publisher source files. Those
  interrupted runs provide no passing integration evidence.

The actual HTTPS/Bearer/SCRAM runtime test failed at the first valid admission:
**1 failed in 213.09s**, request timings `[0.004, 0.004, 0.104, 30.031]` seconds
for missing authentication, missing admission scope, foreign parents and the
valid POST. The valid POST reached the unchanged 30s client timeout. This is a
concrete performance failure, not accepted end-to-end operation. A focused
profile of actual parent preparation recorded **1 passed in 201.61s** including
fixture setup. The profiled prepare took **20.411s**: 338 current role audits
consumed 17.160s and the call executed 34,033 SQL statements. This is an
instrumented trace, not a benchmark or successful HTTP request. The per-routine
privilege loop accounted for 25,688 generator visits and 5.121s cumulatively.
The implemented correction batches each role's current project routine
EXECUTE check into one SQL query, retaining all role/audit predicates and hold
codes. The role/login suite, including eight first/last-routine late grant and
revocation cases across all four roles, passed **65 in 44.81s**. Initial
collection of the new test failed because it omitted the repository's import
path setup; that test harness issue was corrected before this passing run.
The repeated actual HTTPS/Bearer/SCRAM test passed **1 in 278.17s** including
actual farm thermal/economic completion, valid admission/retry, shared fake-CLI
held decision and persisted public job/hold reads. The eight HTTP timings were
`[0.004, 0.004, 0.092, 26.945, 26.337, 0.047, 0.133, 0.043]` seconds. Valid
admission and retry remained below the original 30s timeout. The fixture's
near-limit latencies establish this software case only; they are not production
load/SLO or hardware acceptance. No source, scope, replay or timeout requirement
was relaxed.
Farm join tests passed **3 in 754.64s**. They cover inferred v2 and exact pins,
identical retry, all conditional read scopes, shared fake-CLI hold, altered
farm/hash pins and chronology; pending/foreign/mixed parents and missing
assembly; a different completed thermal job with the same Run ID; cross-version
idempotency conflict; and rollback after revoked scopes, replaced assembly or
scope loss after final preparation. Rolled-back jobs and their events are absent.

Legacy assessment/shared-router and focused public economic/cash/Run completion
regression checks passed **14 in 826.90s**. They preserve v1 inputs, shared CLI
routing, forged-pin/chronology/proceed/selection/claim rejection, current read
revocation and public projections. These two suites ran concurrently over
separate disposable SCRAM schemas; their elapsed times are not request benchmarks.
`git diff --check` and the final locked OpenAPI `--check` passed. The final
documentation check covered **673 local links**, none missing. Task acceptance
checkboxes remain **19 accepted / 20 pending**.

## Review and limits

The final review covered exact parent/farm/version identity, immutable custody
and chronology, current scopes and original service pointers at final commit,
public projection/privacy and legacy compatibility. Internal completions are
constructed by existing verified readers and are not caller-supplied caches.
The routine batching evaluates every catalogued project routine for each role;
no audit result is reused and no role permission is granted by this change.
The focused cases support this software increment. The complete backend suite,
new exact-head hosted CI, production load and independent gate acceptance were
not run as part of these local focused checks. The web implementation was not
changed or retested in this increment.

## Remaining end-to-end requirements

Full farm input authoring, crop/facility/calendar/objective constraints,
physical heat-to-purchased-energy/cost coupling, actual isolated product CLI,
independent G1 custody/release and full browser acceptance remain required.
Rights-backed real G0, independent local G2, future G3a, paired crop G3b and
deployment G4 retain their documented evidence requirements and explicit holds.
