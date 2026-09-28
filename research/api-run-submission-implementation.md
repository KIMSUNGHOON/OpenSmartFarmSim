# HTTP thermal Run admission implementation evidence

Status: software candidate, not independent CLI/source/release or G1/G4 evidence.

## Judgment environment

The existing Codex CLI root session's turn_context at
2026-09-28T14:54:59.548Z records exact model gpt-6-sol and effort xhigh (thread
01a0e064-b01b-7a22-8ef8-dd4afe0eb7dc). No recursive CLI, additional model or new
subagent was launched. This slice connects the existing documented submission
path to actual records; it introduces no agricultural/economic coefficients,
tariffs, forecast or arithmetic. Controller-owned synthetic captures and keys
remain software test material.

## Implemented boundary

[Admission contract](../contracts/api-run-submission-v1.md) and
[service](../backend/app/thermal_run_submission.py) bind the actual v6 stores,
current reference/scope evidence and existing publisher input checks. Admission
never calculates or publishes. The worker repeats those checks at execution.
The optional operator publisher factory uses the actual ApiRuntime stores;
without it, submission is unavailable. JobStore's optional in-transaction guard
rolls new job/event writes back when current access/binding/reference checks fail.
Existing callers retain prior submission behavior. New code is included in the
closed digest and needs a fresh independent release.

## Verification receipts

The first collection attempt exposed this test file's missing local import-path
setup and was corrected. The actual RED then used a real authenticated SCRAM
fixture and failed because the submission service module did not exist.
Initial HTTP-to-worker/read, immutable idempotency, invalid input/reference,
scope, rollback, fixed error and transport cases passed **23 in 63.05 s**.
The first expanded command referenced a nonexistent test_job_store.py and ran
no tests; the corrected command uses the actual test_jobs/test_job_idempotency.

Expanded submission/legacy scenario-worker/publisher/OpenAPI/runtime/job and
intent regressions passed **156 in 266.44 s**. Manual review found that the
service's saved JobStore pointer also needed rechecking after startup. The
service now compares the exact current publisher/Job/Scenario/Run binding before
queueing and inside the commit guard. A same-policy authenticated replacement
store injected during insertion rolls the original transaction back. Final
submission tests, including that case, passed **28 in 77.82 s**; these overlap
the earlier regression cases and are not an additional 28 unique tests.

Locked OpenAPI regeneration/check passed. Review confirmed the generated diff
adds only the thermal POST operation, preserving existing response schemas and
operation IDs. **109 local link targets, none missing**, and whitespace were
checked. Final review
covered trusted bindings, tenant/scope checks before reads and before commit,
immutable pins/context/release matching, idempotency/rollback, fixed HTTP errors,
no calculation/publication at admission, repeated worker gates and conservative
optional factory behavior. Existing coefficients/arithmetic/source bytes and
release records were not changed. No optional broad rerun was performed after
the final binding guard; its actual rollback path was tested in the final 28.

## Remaining holds

Actual product Codex review/execution, independently issued release/custody,
protected deployed operator factory, full farm/economic Scenario, collection and
assessment workflow, actual browser/full G1/G4 and real G0/G2/G3 evidence remain
unaccepted. ASGI Bearer tests are not real HTTPS/process or browser proof.
No broad task checkbox or fixture/source/release evidence is upgraded here.
