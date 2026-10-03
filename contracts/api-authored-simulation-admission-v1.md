# Authored thermal simulation HTTP admission v1

Status: internal authenticated admission candidate after an immutable
[review](farm-authored-review-v1.md), independent signed
[release](farm-authored-release-store-v1.md) and exact
[Run preparation](farm-authored-run-preparation-v1.md). HTTP 202 is an intent
job status, not a Run or a G1 acceptance.

`POST /v1/authored-runs` accepts a closed
`authored-thermal-simulation-request-v1` JSON object with canonical review
job UUID, scenario ID/revision, registration SHA-256 and idempotency key.
The server supplies the tenant from the current Bearer principal. It requires
`simulation_create` plus all authored Run read scopes, including current farm,
release and source authority. Duplicate JSON keys, non-JSON media and bodies
over 4,096 bytes are rejected before the service.

The server-owned `AuthoredSimulationService` checks the signed release,
registered farm, final two traces, report and current rights both before and
during durable admission. Equal retries return the same job; a conflicting
stored intent returns 409. A missing, revoked or inconsistent release holds at
422. Authentication/permission failures return 401/403, malformed input
422 and unavailable storage 503. The response is the public `JobStatus` with
stage `simulation`; a separately operated worker must publish the Run and
completion receipt atomically before the existing authenticated read endpoints
or 3D screen can display it.

`ApiRuntime` constructs the service only with an operator-provided exact
`AuthoredRunStore` and its own preparer and job store. The endpoint is
unavailable when that option is absent. Synthetic signed packet and fake CLI
fixtures verify software contracts only. Actual product CLI execution,
independent reviewer release, full G1 and G4 need separate evidence.
