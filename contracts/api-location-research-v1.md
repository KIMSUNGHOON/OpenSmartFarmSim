# Location research submission v1

`POST /v1/locations` implements the first registration boundary from
[ARCHITECTURE](../docs/ARCHITECTURE.md). Status: **software candidate**; configured
internal assembly only. A request needs authenticated `location_create` scope:

```json
{"latitude":37.5,"longitude":127.0,"period_start_utc":"2026-01-01T00:00:00Z","period_end_utc":"2026-01-02T00:00:00Z","goal_id":"historical-thermal-replay","idempotency_key":"one-region-intent"}
```

The closed JSON body is at most 4096 bytes. Coordinates must be finite numeric
latitude/longitude; period endpoints must be valid UTC with increasing order.
Goal/key are bounded identifiers. Unknown/duplicate fields, booleans as numbers,
nonfinite values and unsupported media types are rejected. The server-owned
read-only scope resolver must match the exact tenant, coordinates, period and
goal, returning immutable allowed provider IDs and the catalog's raw SHA-256.
Unregistered scope is rejected; valid coordinates alone prove no source coverage,
station representativeness, source right or agricultural suitability.

The concrete [ResearchRegistry](research-registry-v1.md) can supply this lookup
and the initial CLI authority from the same operator-pinned immutable facts.
Later evidence-bearing research needs its own verified context/source authority.

The service uses the existing authenticated job authority and grant audit, then
queues canonical `research_input_v1`. The provider catalog hash is a candidate
reference `research-registry-sha256:<hash>`; provider selection remains restricted
to the returned provider IDs. This reference pins internal catalog identity and
does not grant data rights. Initial preparation has no adopted evidence refs and
uses the existing all-null context quartet. It makes no D-time knowledge claim;
later collection/publication must use independently verified signed context and
source/vintage/right evidence. The authority resolver must independently verify
the catalog reference; an HTTP or CLI value cannot approve it.

`202` returns `location_id`, normalized `point`, `spatial_support="pending_research"`
and public `research_job` status. Location identity hashes tenant and canonical
coordinates; the submitted job preserves the registration's immutable point,
period/goal/catalog input. This v1 adds no location listing/lookup or separate
mutable location row. Job reads use the existing GET route and `metadata` scope.
Queue acceptance is not a completed CLI invocation or data adoption.

Idempotency uses the existing unique tenant/stage/key constraint and exact
canonical job input. Replay returns the same job; different request or catalog
under the same key returns `409` without replacing the original. A source scope
resolver performs only trusted read-only lookup, never signing, collecting or
calling a model. Request-scoped identity must be installed on both API and store.
Database row isolation and actual operating authentication remain deployment work.

Errors have the existing fixed error envelope: `401/403` for authentication/scope,
`413` for size, `415` for media type, `422` for invalid/unsupported request, `409`
for intent conflict and `503` for unconfigured/unavailable trusted assembly.
Raw input, credentials, source details and driver/model messages are not reflected.
Database work runs outside the async HTTP event loop. CLI execution, provider
collection, signed later planning and G0/G1/G4 remain separate requirements.
