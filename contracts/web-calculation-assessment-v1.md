# Web calculation assessment v1

The internal authenticated web workspace connects the existing
[calculation assessment](calculation-assessment-v1.md) and
[farm join](farm-calculation-assessment-v1.md) to a browser request and public
hold read. It adds no new server endpoint, crop profile, scientific claim,
economic calculation or gate authority.

An operator provides the completed thermal calculation job ID and completed
economic calculation job ID. The server verifies the actual same-context
parent results and determines supported legacy/farm input versions. The web
does not infer compatibility from job status or create replacement evidence.
The separate authored thermal Run receipt is not supported by this join yet.
Selecting those parents is an internal operator flow; a general user's regional
research → farm → economics → assessment orchestration remains required.

The API client sends only `run_job_id`, `economic_job_id` and a stable printable
ASCII `idempotency_key` to POST `/v1/assessments`. Its actual server identifier
rule is `[A-Za-z0-9][A-Za-z0-9_.:/-]{0,199}`, which the client validates.
The existing same-origin
Bearer request, 30-second timeout, no stored token, redirect rejection, bounded
JSON decoding and fixed error messages apply. Admission requires HTTP 202 and
assessment JobStatus. Current held-only assessments cannot use `succeeded` or
an unrelated stage as a displayable result.

The browser freezes the two parents and caller key before sending. A lost,
invalid or 5xx response retains that exact intent for retry; it cannot silently
generate a new key. While admission is uncertain or in flight, replacing the
connection or resetting the intent is disabled. A confirmed bounded 4xx refusal
or a valid server job allows a new intent. Two quick submits produce one active
request. The key is not a token and is visible in the operator's request receipt.
Reload loses unconfirmed in-memory intent; saved IDs/key must be resolved by an
operator before submitting a replacement, and automatic reload recovery remains
future work.

Manual refresh reads the exact saved assessment job. A held assessment reads
the existing `/v1/jobs/{id}/hold-report` and shows only its public evidence
categories. Unsupported stages, successful recommendation-shaped status,
mismatched job/hold IDs or report stage are rejected. A refused or unavailable
report is shown as unconfirmed evidence, without fabricating missing data or
approval. No crop ranking, price, future margin or purchase-energy values appear.
Failure of a later GET clears unconfirmed status/report but keeps the already
known job ID for GET retry; it does not turn the confirmed admission into a new
POST or an uncertain-admission connection lock.

An existing assessment job can be reopened by its saved ID after reconnection.
This GET path is not a new POST; it cannot certify the parent linkage or expose
private inputs. Its read authorization is checked by the server. Reconnection
clears old account state, and previous asynchronous responses cannot repaint
the new account's workspace. Auth tokens and result records are not persisted
in browser storage. Existing approved panel/form/status styles are reused.

Acceptance includes exact request/retry bytes, input and response rejection,
HTTP/network error handling, job and report lookup, a held browser flow,
connection/intent locking, reopening, 4xx reset, unexpected positive status,
desktop/phone overflow and console checks. Browser fixtures prove interaction
software only; actual HTTPS/PostgreSQL/CLI integration and independent G1/G4
retain their separate evidence requirements.
