# Authored farm review HTTP admission v1

Status: internal authenticated admission candidate. This wraps the existing
[authored review service](farm-authored-review-v1.md) after an immutable
[farm input registration](api-farm-authoring-v1.md). A successful response is a
queued `collection_review` job, not a CLI decision, snapshot release or Run.

`POST /v1/farm-authored-reviews` accepts a closed
`farm-authored-review-request-v1` JSON object with exact `scenario_id`,
`scenario_revision`, `registration_sha256` and caller `idempotency_key`.
Duplicate keys, non-JSON media and bodies over 4,096 bytes are rejected before
the service. The server supplies the tenant from the Bearer principal and
requires the service's current `REVIEW_SCOPES`, including
`collection_review_create`. On acceptance it returns HTTP 202 with the
existing public `JobStatus`, not the private farm or source bytes.

The service rereads current registration, source rights, context and economic
pins, recomputes both complete thermal traces and rechecks them before commit.
Equal repeated intent returns the same job; conflicting intent returns 409.
Invalid input returns 422, unavailable/revoked evidence returns a 422 hold,
missing authorization returns 401/403, and unavailable storage returns 503.
The admitted job needs the separately configured actual Codex CLI worker and
independent reviewer release before authored simulation may publish a Run.

`ApiRuntime` assembles the exact review service from its own farm authoring
service only when owned research is present. The API rejects a review service
bound to a different authoring object. OpenAPI, scope denial, HTTP transport,
idempotency/conflict, current rights hold and actual SCRAM storage need focused
verification. Synthetic fixture checks establish software behavior only.
