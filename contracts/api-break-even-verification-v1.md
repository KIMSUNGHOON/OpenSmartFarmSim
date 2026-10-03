# Break-even asynchronous verification HTTP v1

Status: internal implementation candidate. Conditional user-grid replay only;
no source approval, independent release or G0–G4 promotion.

## Admission

`POST /v1/break-even-verifications` (`submitBreakEvenVerification`) accepts a
closed JSON object containing only `calculation_job_id`, a canonical lower-case
UUID for an actual completed calculation. Tenant, hashes, implementation,
trial count and idempotency key are resolved by the server. Maximum request body
is 4 KiB; JSON media type, valid UTF-8, unique keys and finite JSON are required.

The [internal service](break-even-verification-v1.md) requires the existing
completed-result read scopes plus `simulation_execute`. Source/candidate/plan
write scopes are unnecessary. Actual audited stores retain their common current
principal/policy/schema/DSN and original provider chain. The same parent/current
implementation intent reuses its stored Job. `202 JobStatus` may report its
existing state and is not a completed replay or gate approval.

401/403 cover authentication/scope denial. Invalid transport/body is
413/415/422; unavailable or unfinished parent is a fixed 422 hold. Conflicting
immutable intent is 409; unavailable assembly/storage is fixed 503. No raw
input, private evidence, internal exception or credentials are returned.

## Completed result

`GET /v1/jobs/{job_id}/break-even-verified-result`
(`getJobBreakEvenVerifiedResult`) reads the verification Job UUID. It requires
the existing completed-result read scopes; execution/writes are unnecessary.
The [internal completed-evidence reader](break-even-verified-result-v1.md)
checks actual input/publication/receipt, tenant-private evidence, current parent,
source/scope/provider/role and implementation bindings before returning the
existing `BreakEvenRead` projection. It performs no monetary/grid arithmetic.
Conditional user/assumed amounts and Assessment hold remain explicit.

Missing/unfinished/other-model Jobs are 404, invalid UUID is 422,
authentication/scope denial is 401/403, and unavailable or inconsistent evidence
is fixed 503. The standard Bearer HTTPS runtime applies `no-store` to every
complete response and ignores caller tenant headers. Read-only/schema-only
assemblies retain fixed unavailability rather than fabricating results.

`ApiRuntime` enables both services only through the existing actual
`MarketSourceStore` assembly. The explicit `create_app` injection accepts exact
service types bound to the same Job/BreakEven stores. The existing synchronous
result endpoints and their replay semantics remain available.

## Protected worker process

The operator factory returns the exact `BreakEvenVerificationWorker`, with its
private authenticated store assembly and fixed tenant. Factory name/canonical
UUID validation precedes import. Run one targeted leased attempt:

```sh
uv run --locked --group dev python -m app.break_even_verify_work \
  --factory "$OSSF_BREAK_EVEN_VERIFICATION_FACTORY" \
  --job-id "$OSSF_BREAK_EVEN_VERIFICATION_JOB_ID"
```

Exit 2 emits fixed startup rejection, exit 3 fixed execution/lease unresolved.
Exit 0 contains only Job/attempt/state/reason/calculation-parent metadata or null
for no applicable work. No source records, monetary values or model invocation
are printed. The worker retains full replay outside its final publication lock,
lease/cancellation checks, private evidence and atomic completion.

Browser/SDK integration, automatic processing/deployment, actual 256-trial SCRAM
and HTTP/reader EOF load under the unchanged 30-second limit, cancel/retry/rights
withdrawal under that load and independent product CLI/G1/G4 remain required.
Two-trial synthetic checks establish software contracts only.
