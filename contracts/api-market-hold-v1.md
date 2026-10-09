# Market hold HTTP read v1

Status: internal G1 read-path candidate. The authoritative signed record and public projection are defined in [market-hold-v1](market-hold-v1.md). This endpoint only displays a previously issued report; it cannot issue one or approve a MarketSnapshot.

`GET /v1/market-hold-reports/{report_id}` accepts a UUID. The tenant comes from a trusted server principal, not from the request. The principal needs `market_hold_read`, and the configured `MarketHoldStore.get_public_report` independently checks the same tenant and scope before returning a signed, immutable report's safe projection. A successful response has exactly `hold_report_id`, `status="hold"`, `reasons`, and `missing_evidence`. It excludes raw bytes, signature, signing key, source rights, DecisionContext, snapshot ID, time, candidate scope, and tenant ID. A former scope version remains readable as a historical hold report; it cannot be used as the current MarketContext authority.

The API uses the same `{ "error": { "code": "...", "message": "..." } }` envelope as the job status path: `401` missing authentication, `403` absent display scope, `404` missing or foreign report, `422` malformed UUID, and `503` unavailable/corrupt store. The API does not return exception details. Typed FastAPI/Pydantic response models generate the OpenAPI 3.1 operation; [PostgreSQL tests](../backend/tests/test_api_market_hold.py) verify projection, scope and error behavior.

Request authentication, API service configuration, actual source G0, real CLI/thermal G1, and the full user flow remain held. The report reason `market_g0_not_evaluated` does not mean a source failed quality review or that a crop was evaluated.
