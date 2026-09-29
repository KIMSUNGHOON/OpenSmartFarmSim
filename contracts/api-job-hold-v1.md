# Validated job hold HTTP details v1

`GET /v1/jobs/{job_id}/hold-report` reads an existing immutable `hold_v1`
artifact for a job with state `hold` and stored reason `ai_validated_hold`.
This complements [job status](api-job-status-v1.md); it is separate from
[Market hold](api-market-hold-v1.md) and does not create a report or a decision.

The trusted principal needs `metadata`, `artifact` and `auditor` for the same
tenant. All three also pass through the JobStore accessors. The
auditor requirement preserves the artifact's stored private/auditor policy.
Operating role assignment and authenticated application assembly remain pending.

The response contains `job_id`, `stage`, `hold_id`, `status="hold"`,
`recorded_at`, `reason_code`, `missing_evidence` and `missing_evidence_count`.
Stage is one of the three CLI stages. Reason is `evidence_missing` or
`decision_held`, taken from the canonical report; it is distinct from job
status's `ai_validated_hold`. Timestamp is report storage time, not planning D.
Recognized public missing codes are `research_source_evidence`,
`signed_decision_context`, `real_source_g0` and the six bounded categories in
[joined calculation assessment](calculation-assessment-v1.md). All other private identifiers
collapse to one `other_evidence` category. The count remains the original total
(0–50); categories preserve first appearance without duplicates. No raw report,
model reason, private identifier, credential, tenant, input/hash, attempt ID,
decision ID or receipt ID is returned.

The server matches requested job ID, tenant, CLI stage, current held attempt and
report metadata, then uses the existing content SHA/size and canonical bounded
report checks. Missing/foreign/unheld reports return `404`; authentication or
scope denial returns `401/403`; malformed UUID returns `422`; corrupt/unsupported
report, inconsistent metadata or store failure returns fixed `503` without raw
error details. The endpoint accepts no replacement report or client tenant.

This is a historical software hold projection. It does not establish actual
CLI execution, source rights/QC, G0, G1 completion, field/forecast/ranking accuracy
or G4. Queued, failed, canceled and infrastructure-only holds still use the
existing job status code; this route does not invent validated AI artifacts.
