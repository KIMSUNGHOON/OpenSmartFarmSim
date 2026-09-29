# Job break-even result HTTP v1

Status: implementation candidate; conditional user-grid arithmetic only.

`GET /v1/jobs/{job_id}/break-even-result` (`getJobBreakEvenResult`) requires
metadata, artifact, break_even_read, market_source_read, market_candidate_read,
decision_context_read and market_hold_context_read. Execution and write scopes
are unnecessary. Tenant comes from the authenticated server principal.

Actual audited Job/BreakEven/Candidate/Source/Hold/Context stores share one
policy/schema/DSN/principal. A completed simulation of the existing break-even
input model resolves through verified canonical input bytes, a bounded canonical
receipt, publication manifest/attempt/input/artifact hashes and the actual stored
plan/request/result. The complete stored plan and request must equal the job
input; the result is replayed through the existing full grid engine and must
match the receipt digest/status. Current scopes, bindings and pointers are
checked after storage/replay, including failed replay. Original code/environment
digests remain historical metadata, not independent release or gate proof.

The response is the existing BreakEvenRead projection with user/assumed origin,
conditional_user_grid_only scope and Assessment hold. Unknown amounts and grid
statuses retain existing semantics. Raw source records, input/receipt bytes,
credentials, internal exceptions and CLI decisions are not exposed.

401/403 cover authentication/scope denial; invalid UUID is 422. Other tenants,
unfinished jobs or different job models return 404. Missing/inconsistent
completed evidence and unavailable assembly return fixed 503. ApiRuntime enables
the service only with its actual source store; schema/read-only assembly keeps
503. No model invocation, source approval or gate promotion occurs here.

Synthetic fixtures verify software contracts only. Automatic trial assumptions,
continuous-interval proof, independent G0–G4 evidence, actual CLI orchestration,
protected deployment and browser completion remain separate acceptance work.

The [stored-trial browser candidate](web-break-even-workspace-v1.md) now connects
this read to explicit baseline/sale/collection/target/range and ordered saved
joint revisions. Its [software verification](../research/web-break-even-workspace-implementation.md)
does not complete the full farm/CLI/replay or gate acceptance above.
