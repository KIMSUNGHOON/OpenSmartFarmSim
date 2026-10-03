# Authored Run financial selection v1

Status: internal server prerequisite for web authored economic/assessment parent
selection. This read does not calculate, admit a job or approve a claim.

`GET /v1/jobs/{job_id}/authored-economic-input` resolves an actual completed
authored thermal job through its existing current Run/release/rights checks.
The configured actual economic service and authored store share their existing
authority chain. The current authored farm registration supplies its exact
economic scenario/revision/hash/candidate; clients do not search unrelated
candidates or supply replacement coefficients. The closed response contains
`schema_version=authored-economic-selection-v1`, the existing authored thermal
summary, the closed economic input V3 without an idempotency key, and
`verification=requires_admission_recheck`. The later existing economic POST
still rechecks everything and receives a newly pinned caller key.

`GET /v1/jobs/{job_id}/authored-financial-history` lists that exact parent's
economic V3 and assessment V3 intents in descending `(created_at, job_id)` order.
The limit is 1–50 (default 20); paired `before_created_at` and `before_job_id`
form the cursor. Only the authenticated tenant's actual service namespaces and
matching immutable parent/input pins are included. An assessment item also
links its actual same-tenant economic job, which must have the same V3 input.
Canonical bytes and their stored hashes are checked, and corruption holds the
page rather than silently disappearing. The response contains JobStatus links,
the exact thermal job/Run identity, a cursor and
`verification=requires_current_read`; it contains no arithmetic or private raw
inputs, source text, CLI capture, release packet, rights declaration or token.

The index is recovery metadata. Queued/failed/canceled/held records can appear;
their status does not certify a calculation result or parent compatibility.
Money/cash display uses the existing current verified completion reads. An
assessment uses the existing status/hold reads and cannot become a crop ranking.
Both reads require authored read/release/farm scopes and existing economic job
read scopes. Missing scopes are 403; unknown/foreign/uncompleted/non-authored
parents are 404; invalid path/cursor is 422; missing configured authority or
stale/corrupt current evidence is 503, with fixed public errors.

No new table, role grant, dependency, tariff, arithmetic or claim gate is added.
Bindings and scopes are fenced around current preparation and final projection;
the history also rechecks its prepared parent pins before returning. Acceptance
requires actual SCRAM selection, stable parent identities and pagination,
mixed/foreign/pending/corrupt/rights-revoked refusal, late binding/scope change
refusal, exact OpenAPI and standard HTTPS using the existing 30-second client
limit. Synthetic CLI/reviewer evidence proves software only. The web task,
actual `gpt-6.1-sol`/`xhigh` product CLI and independent G1–G4 remain separate.
