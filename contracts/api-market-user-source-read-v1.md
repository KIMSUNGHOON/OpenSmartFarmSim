# Stored user-assumption reads v1

Status: software candidate supporting economic input forms. These owner-only
reads expose existing user assumptions; they approve no data, calculation,
forecast, ranking, or G0–G4 claim. [Intake](api-market-user-source-v1.md) and
[storage](market-user-source-store-v1.md) remain authoritative for adoption.

`GET /v1/market-user-sources` requires `kind` (one of the existing seven types).
Optional `limit` defaults to 20 and ranges from 1 to 50. Paired
`after_record_id` / `after_revision` resume after a returned cursor. Ordering is
the UTF-8 byte order of `(record_id, revision)` within the authenticated tenant
and kind. Pages contain `kind`, `items`, and nullable `next_cursor`; an empty
catalog is 200 with an empty array and null cursor. Each item contains `kind`,
`record_id`, `revision`, `payload_sha256`, `recorded_at`, and
`admission_kind=contract_valid_user_assumption`. No input values appear in a
catalog. There is no total count or immutable catalog snapshot: new insertions
before the cursor require restarting enumeration. An existing revision is never
replaced; the catalog does not pick the latest or most suitable assumption.

`GET /v1/market-user-sources/record` requires `kind`, `record_id`, and `revision`.
It returns the same metadata plus `input`: the complete typed canonical model
JSON without `tenant_id`, suitable for a new submission after explicit edits.
All fields, including null and empty collections, remain present. Money and
quantity remain decimal strings with units; no unknown value becomes zero.
`prior_batch_cost` has the existing synthetic revision key `single`.
OpenAPI discriminates the seven closed record shapes by `kind`.
Each read response is bounded to 131072 UTF-8 JSON bytes, allowing the existing
65536-byte stored input plus its metadata, or up to 50 metadata-only items.

The stored `payload_sha256` pins the full canonical input including the
authenticated owner, not the tenant-redacted response JSON. It is the pin used
by existing scenario/calculation contracts. Read clients must not replace it
with a hash of the redacted response or use it to claim source approval.

Both reads require AND scopes `metadata` and `market_source_read`; write scope
is unnecessary. They use the existing exact audited authority JobStore and
MarketSourceStore binding, with explicit source storage enabled. The server
authenticates each request, verifies current scopes and binding before/after
lookup, and never accepts a tenant selector. Every returned source and the
pagination lookahead rechecks canonical model/identity, stored hash, store
version, admitting role, and identical original job input. Missing and foreign
record versions are the same fixed 404. A corrupt or unavailable store is fixed
503 with no partial page or raw exception. Missing authentication is 401,
missing/revoked scopes 403, malformed query/cursor 422. Errors disclose no
record content. ApiRuntime's protected Bearer middleware supplies no-store
responses; the existing actual source factory enables both reads without new
grants, migrations, defaults, or artifacts.

These private owner reads are for reviewing/editing submitted assumptions.
Rights declarations are preserved as input, not converted into a display,
redistribution, external-source, or calculation approval. Existing calculators
must still check rights, availability at the decision time, scope, inventory,
settlement, and signed context. The catalog may contain incomplete or unusable
assumptions. Frontend economic forms, conditional results, actual CLI and full
G1/G4 remain separate acceptance work.
