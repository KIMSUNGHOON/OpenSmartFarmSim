# Break-even plan admission v1

Status: software candidate for a finite user grid; no continuous root or G1 claim.

POST /v1/break-even-plans (submitBreakEvenPlan) accepts closed JSON with request
(the existing BreakEvenRequest) and 2–256 ordered scenario/revision/hash pins.
The body is limited to 65536 bytes. No trial values, computed results, tenant,
fixed projections or proposed plan are accepted from the caller.

request.plan_id is the client-owned immutable logical intent and idempotency
identity: distinct plans need distinct IDs. The existing unique JobStore key,
namespaced by the UTF-8 plan ID digest, atomically reuses identical input and
rejects changed input with 409, including a changed trial order. IDs retain the
existing Unicode/query-encoded contract and a 200-character bound.

The server requires metadata, artifact, simulation_execute, break_even_read,
break_even_write, market_source_read, market_candidate_read, decision_context_read
and market_hold_context_read. Actual job/candidate/source/hold/context/break-even
stores share the audited authority policy/schema/DSN/principal. The source and
break-even policy flags are required. No grants or migrations are added.

The existing versioned market path validates each pinned candidate's rights,
baseline, shock, settlement bindings and derived scenario without calculating
money. The server derives exact grid values and fixed input/shock hashes with
the existing break-even functions, checks common scope/calendar/sale/collection
and distinct trials, and assembles BreakEvenPlan. Source identities, current
scopes and the entire prepared input are checked again at commit.

202 returns plan ID, request/plan hashes, trial count, pinned_user_grid_intent and
actual JobStatus. The immutable simulation input contains input_version
break-even-calculation-input-v1, the checked request and server-built plan.
Admission creates only the intent/event. Calculation worker, result publication,
job-result linkage and protected deployment are subsequent steps; no money/root
result, CLI invocation or gate approval is fabricated at admission.

Authentication/scope denial is 401/403, input/pin/scope mismatch 422, body/media
errors 413/415, unavailable assembly/internal source failure fixed 503. Other
tenants cannot admit foreign pins. The optional actual-source ApiRuntime enables
this path; schema-only/read-only assembly returns 503. Existing GET break-even
results remains separate and cannot find these queued plans as completed results.

Trial source records/candidates must already be registered. Automatic generation
of those economic assumptions from a declared response rule remains pending.
The full economics contract's continuous-interval proof, independent domain/CLI
validation, forecast/ranking and farm/G0/G2/G3/G4 evidence remain held.
