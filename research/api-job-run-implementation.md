# Completed thermal job discovery evidence

Status: internal authenticated software read candidate, not actual G1/G4.

The active Codex CLI thread 01a0e064-b01b-7a22-8ef8-dd4afe0eb7dc made this
interface judgment. Selective actual turn_context inspection recorded
2026-09-28T13:21:15.534Z, exact gpt-6-sol and xhigh. Reviewable output is the
[reader](../backend/app/api_job_run.py), [route](../backend/app/api.py),
[contract](../contracts/api-job-run-v1.md) and [tests](../backend/tests/test_api_job_run.py).
No recursive CLI, additional model call or subagent was used. This is developer
evidence, not independent source/release/gate approval.

The completed worker exposed an explicit job ID but clients could not discover
its Run without private artifact handling. The added read uses existing scoped
stores and public ThermalRunSummary. It validates the completion/attempt,
canonical bounded receipt, exact manifest, reconstructed input hash and actual
Run context/review/report/two trace hashes before the existing rights-aware
display projection. No new producer, DB schema, grants, dependency, arithmetic
or mutable source/release is introduced. The reader joins the closed code digest;
changed implementation bytes require a fresh independent release.

## Verification

The initial actual PostgreSQL test failed after worker completion because the
HTTP route was missing (404 instead of 200). After implementation the initial
focused set had 13 passing cases and one invalid fault fixture: the test's own
canonical-input helper rejected its secret-shaped field before exercising the
route. The fixture was corrected to construct controlled corrupt bytes; its
extra field was then changed to an ordinary unknown field to specifically test
the closed receipt contract.

Local PostgreSQL 16.15/SCRAM with locked dependencies:

- API/job Run, OpenAPI, thermal display and runtime assembly: **69 passed in
  95.62 s** (initial 14 discovery cases).
- Final reader/manifest checks plus fresh ApiRuntime/Bearer integration:
  **16 passed in 26.83 s**.
- OpenAPI exact regeneration check passed; the generated diff adds only
  getJobRun with the existing response/error schemas and explicit three scopes.

The tests use actual immutable jobs, atomic worker publication and Run store.
They reject wrong tenant, missing scopes before reads, held/unfinished/other-stage
jobs, attempt/input/typed-manifest mismatch, unknown/noncanonical receipt fields,
wrong review/context and changed report/trace hashes or missing Run. A fresh
assembled API reads the persisted completion under Bearer/current_principal;
spoofed tenant headers do not select the resource, unauthenticated requests are
401 and the successful response is no-store. Additional size-boundary verification
and the corrected ordinary unknown-field case passed **2 in 4.92 s**
(15 deselected). The size case confirms that no artifact read occurs above
4096 bytes. Final changed-file/link and whitespace review passed: **91 local
links, none broken**. Review covered bounded reads, independent store scopes,
canonical manifest type equality (true cannot replace attempt 1), tenant/input/
attempt/Run linkage, immutable read races, fixed error masking and unchanged
existing response schemas. No external data or gate approval was adopted.

## Limits

All captures, review/context/release keys and execution verifiers are controller
owned synthetic test inputs. Fresh API assembly and ASGI/Bearer requests prove
software persistence/identity wiring; this new test does not operate a public
HTTPS service or browser. Actual CLI execution and independent custody/release,
simulation submission, collection/assessment orchestration, Compose application
roles, browser/3D and full G1/G4 remain pending. Actual G0/G2/G3 evidence remains
unavailable. Existing broad task checkboxes stay open. Hosted receipts follow
the implementation commit and must match its exact head.
