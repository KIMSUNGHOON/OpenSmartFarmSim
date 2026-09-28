# Economic calculation HTTP v1

Status: implementation candidate; user-assumption arithmetic only.

`POST /v1/economic-results` (`submitEconomicCalculation`) accepts the closed
EconomicCalculationInput fields plus a bounded ASCII idempotency_key. The input
and formula versions are the worker's existing literals. Tenant comes from the
authenticated server principal. JSON is limited to 4096 bytes. No numbers,
result bytes, decisions or gate proposals can be supplied.

Admission requires all existing CALCULATION_SCOPES and actual audited
Job/Result/Candidate/Source/Hold/Context stores with one policy/schema/DSN/principal.
It verifies candidate/scenario pins and replays the existing ledger before and
at commit, preserving source rights and hold checks. Current scopes and store
identities are checked around replay and at commit. The existing unique intent
constraint atomically handles retries; a namespaced client key with changed
input is 409. Admission writes only the immutable simulation intent and event.
202 returns the existing JobStatus, including its current state on retries.
It does not publish a result, call a model or approve any gate.

`GET /v1/jobs/{job_id}/economic-result` (`getJobEconomicResult`) requires metadata,
artifact, market_source_read, market_candidate_read, market_result_read,
decision_context_read and market_hold_context_read. Write/execution scopes are
not needed. Same-tenant completed economic jobs resolve through verified
immutable input bytes, canonical bounded receipt, publication manifest, attempt,
input/result/artifact hashes and actual replayable result pins. Receipt fields
must exactly match the input and actual result. Original implementation and
environment digests must be well-formed; they are retained historical metadata,
not independent release or G1 evidence. Current scopes and store identities are
checked again after reading/replay. Output is the existing EconomicResultRead.
Other tenants, unfinished jobs and other job models return 404. Missing or
inconsistent completed evidence returns fixed 503. Source values, receipts,
credentials and exception detail are not exposed.

401/403 cover authentication/scope denial; invalid JSON/schema/pins are 422;
oversize/media errors are 413/415; unavailable assembly/internal failure is 503.
The operator ApiRuntime enables both paths only with its actual source store.
Standalone schema/read-only assembly retains fixed 503 for this optional service.

Succeeded denotes calculation procedure completion. Unknown amounts remain
null and the engine's calculation_status and Assessment hold are preserved.
Actual farm performance, forecast, ranking, CLI workflow and G1/G4 remain held.
