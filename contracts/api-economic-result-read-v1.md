# Conditional economic result read v1

Status: implemented software read candidate. Its exact public field set has not
received a separate `gpt-6-sol`/`xhigh` CLI interface review and must be checked
before `api-flow` acceptance.

`GET /v1/economic-results/{economic_result_id}` reads an already pinned, replayed
ledger result. The ID is the 64-character lowercase SHA-256 ID inside the economic
ledger, not the surrounding market scenario result ID. The API resolves it through
the tenant-owned PostgreSQL market result, verifies the immutable stored bytes,
recalculates the whole pinned joint market and ledger path, and compares the replay
bytes before projection. If its signed Market hold, source rights, or candidate
binding no longer replays, the read fails closed with a generic `503`.

The authenticated principal needs `market_result_read`. The HTTP principal's
tenant ID must equal the store principal's tenant ID. Other tenants and absent
results receive `404`; missing authentication receives `401`; missing scope
receives `403`. Malformed IDs receive `422`. Internal store and calculation
details are never returned in errors. Application assembly requires a result
store with `get_economic_result(tenant_id, economic_result_id)`.

The response explicitly identifies `market_context_kind=unavailable` and its
`market_hold_report_id`, `assessment_status=hold`, and either
`calculation_status=conditional_user_assumption` or `hold`. These results use
`input_origin=user`, `evidence_level=assumed`. `sales_totals_status` tells whether
gross sales and recognized kilograms reconcile with inventory or remain only
unverified arithmetic over submitted records. It does not certify realized farm
revenue. Quantity fields end in `_kg`; monetary fields end in `_krw`. Every
finite numeric value is a decimal string, including negative cash. Unknown or
undeclared amounts remain JSON `null`, never zero. Hold reasons are displayed
as bounded codes; sale-specific or unexpected details are withheld. The response
does not include raw user records, rights manifests, settlement events, or the
stored result envelope.

This route does not create a scenario, submit work, publish a forecast, prove a
farm profit, or recommend a crop. Monthly cash schedules, all three conditional
break-even targets, complete input provenance, temporal provenance, real
principal/DB role deployment, and submission/orchestration are later `api-flow`
work. Its current integration test uses a signed Market hold and actual local
PostgreSQL, while baseline, shock, rights, and settlement repositories remain
test data. The route is a software read contract, not a G1 or G3 gate pass.
