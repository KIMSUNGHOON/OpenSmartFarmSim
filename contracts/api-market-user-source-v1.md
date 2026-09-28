# User-assumption HTTP intake v1

Status: software candidate for the unavailable-market path. Registration is
contract_valid_user_assumption; it grants no external data approval, calculation
completion, forecast, ranking or G1/G4 acceptance.

`POST /v1/market-user-sources` / registerMarketUserSource accepts required kind,
input and idempotency_key. The seven existing types/version keys are in
[source storage](market-user-source-store-v1.md). Input is the complete canonical
model JSON except tenant_id; even a matching supplied tenant is rejected. The
server injects the authenticated tenant. User/assumed labels, dates, units,
string money/quantity and references are preserved. Missing default/null fields
or noncanonical model values are rejected, never silently filled or converted.

The body limit is 65536 bytes with streaming, UTF-8, duplicate-key and nonfinite
checks. Existing submissions keep 4096 bytes. OpenAPI has seven closed variants,
complete properties required, tenant removed and definitions inlined. Economic
scenarios admit only unavailable market contexts, matching the actual Store.
AND scopes are market_source_write, market_source_read, metadata. Authorization
and service availability precede body reads. The exact audited authority stores
must share policy/schema/DSN/principal and explicit market_source_storage.

After model validation, JobStore.submit writes an immutable collection intent.
Its new optional admission_action(conn, row) runs after immutable-byte comparison
and before the unchanged zero-argument commit_guard. Trusted server code adopts
the identical source bytes on that actual transaction connection. Current
scope/binding/input/version failures roll back job, submission event and source
row together. Other callers' defaults remain unchanged. Denial/conflict exception
types remain ValueError subtypes for existing Source Store callers.

The bounded internal intent key hashes kind and the public idempotency key;
tenant/stage scoping is unchanged. Identical retries return the same intent;
changed bytes under the same key or an existing source-version conflict return 409. Corrections
need new revisions (new cost_ref for prior_batch_cost). Identical source bytes
under another intent preserve the first source job/time under the Store contract.

`200` returns kind, record_id, revision, payload_sha256, actual first recorded_at,
admission_kind and public intent_job. The intent stays queued. No lease, attempt,
CLI decision, execution completion or result artifact is fabricated. The first
source job pin and current intent are distinct. Registration is available to the
existing readers/calculators, whose decision-time/rights/scope/dependency checks
remain mandatory; complete collection/review/economic workers are subsequent.
Responses omit input, tenant, credentials and arithmetic results.

401/403 are fixed authorization failures; invalid input is 422; conflicts are
409; body/media bounds are 413/415. Missing service or internal binding/failure
is fixed 503. Errors expose no values, identifiers or exception text.

ApiRuntime enables intake only when its existing protected source factory
returns the exact actual MarketSourceStore bound to its JobStore. Custom read
repositories leave it unavailable. No factory, grant, credential default,
migration or automatic profile upgrade is added. Startup still requires the
existing protected artifact root; intake itself creates no artifact.

Synthetic source/key tests with actual SCRAM/Bearer prove software contracts
only. Real CLI, independent source/rights/release/custody, completed workflow,
browser/full G1/G4 and G0/G2/G3 remain unaccepted. New code needs a fresh release.
