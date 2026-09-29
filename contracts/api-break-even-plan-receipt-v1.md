# Stored break-even plan intent receipt v1

GET `/v1/break-even-plans/receipt?plan_id=...&submission_sha256=...` recovers a
lost plan admission reply without repeating source/plan preparation. It requires
current metadata, artifact and break_even_read scopes. It is historical intent
metadata, not current source approval or an execution/result validation.

The exact tenant/stage/namespaced plan-ID key resolves an existing immutable job.
The server verifies stored input bytes/hash and the complete plan-input schema,
request/plan identity, request digest and reconstructed ordered submission digest.
It returns only plan ID, submission digest, `intent_status=stored` and actual
public JobStatus. No raw source, pin list, proposed coefficients or amounts are
exposed. Current scopes/store bindings are rechecked even on failed inspection.

Missing intent is 404, a different submission under the same ID is 409, bad
query is 422, authentication/scope denial is 401/403 and inconsistent/missing
assembly is fixed 503. No new job, write, schema, grant or model invocation is
created. A stored intent can be queued, held or failed; its existence does not
prove the original sources are still usable. The worker and completed-result
reader retain all current source/rights, full calculation and proof checks.

The browser hashes canonical full request plus ordered candidate pins. After an
unknown POST reply, manual recovery reads this receipt. A missing/denied/broken
receipt leaves the original write unresolved, with exact bodies/keys and locks
preserved. It does not automatically repost. If no intent ever exists, safe
resubmission/reload recovery remains separate required work. The 30-second
request deadline is unchanged; no elapsed wait is treated as acknowledgement.
