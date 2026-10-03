# Authored calculation assessment join v1

Status: internal implementation candidate after authored economic execution.

[Financial history](authored-financial-selection-v1.md) recovers this exact
authored thermal parent's assessment intents and linked economic jobs. Its
recovery metadata does not replace current assessment/status or result checks.

The existing closed POST `/v1/assessments` still accepts only `run_job_id`,
`economic_job_id` and `idempotency_key`. The server infers
`calculation-assessment-input-v3` exclusively from the actual completed
`authored-thermal-simulation-input-v1` and `economic-calculation-input-v3`
parents. Legacy thermal V1/V2 plus economic V1 and farm replay thermal V3 plus
economic V2 retain their existing assessment inputs. Mixed pairs never degrade
to a generic assessment.

The configured assessment service supplies its actual authored Run store to
economic completion verification. It must share jobs, the current owned farm
service, context store, economic candidates and release authority. The economic
parent must name the exact requested thermal job, canonical input/receipt/
report hashes and Run, even if another job can resolve to an identical Run ID.
Current authored registration, release, source rights, numeric input/server
binding hashes and the exact economic scenario/candidate must still verify.

The authored Run's immutable traces supply the base snapshot and decision time
kind. Both traces must match the current authored farm's snapshot/context and
the release/report; current signed context and market hold must agree with
the economic result. Public report fields are not treated as a substitute for
these actual parent and registration checks.

V3 retains all existing common assessment pins and adds authored scenario ID,
revision, registration hash, server binding hash, numeric input hash and release
hash. These are server derived. Candidate and evidence arrays stay empty.
The existing caller-key namespace is stable across all three internal versions.
Admission, final commit, CLI parsing and authority resolution recheck current
bindings and chronology. The V3 CLI route uses a distinct validator version;
the original V1/V2 validator version remains unchanged.

All six existing ordered missing-evidence categories remain mandatory. The
user-authored agricultural assumptions do not establish admitted crop profiles,
independent local/future/comparison evidence or G0 approval. The CLI proposal
must be hold with no selected crop, claim or missing-code omission. A valid
held decision is immutable evidence and creates no recommendation publication.

V3 adds current authored read/release/farm scopes to existing assessment
read/create requirements. OpenAPI declares these conditional scopes. Error
semantics, JobStatus and bounded public hold reports remain unchanged; raw
inputs, receipts and private bindings are not exposed. The standard HTTPS
runtime and shared owned CLI router supply the actual configured services.

Acceptance requires actual SCRAM paired completions, inferred immutable V3
pins and retry, shared fake-CLI held decision/read, altered pins and forbidden
claims, mixed/foreign/pending/missing-authority refusal, scope/binding changes
at commit with rollback, prior assessment compatibility and actual authenticated
HTTPS admission/read using the existing 30-second client timeout. Synthetic
review keys and executable prove software only. General web orchestration,
actual `gpt-6.1-sol`/`xhigh` product CLI, independent release and G1–G4 evidence
remain subsequent acceptance work.
