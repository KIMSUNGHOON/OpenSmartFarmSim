# Completed economic job cash flow v1

Status: software candidate for conditional user-assumption monthly cash; no
forecast, farm validation, ranking, whole G1 or operating acceptance.

`GET /v1/jobs/{job_id}/economic-cash-flow?limit=12&after_month=YYYY-MM`
uses the same scopes and completed-job proof as the existing economic-result
read: metadata, artifact, market_source_read, market_candidate_read,
market_result_read, decision_context_read and market_hold_context_read. It
rechecks current authenticated tenant, input/pins, publication/receipt, stored
result and full source/market/ledger replay before projection. Read permission
requires no execution/write scope. The old economic-result DTO is unchanged.

The closed `economic-cash-page-v1` response identifies both result IDs,
scenario/revision, decision/formula, unavailable market-hold context,
calculation status, Assessment hold and user/assumed labels. Its calendar is
`Asia/Seoul`; minimum-balance timestamps are explicitly UTC. Each row contains
month, opening/net/closing/minimum/shortage amounts in KRW as finite decimal
strings and the UTC instant of that month's minimum. No money, interpolation,
forecasts or zero declarations are calculated in the browser.

The first page starts at the first month. limit is 1–24 (default 12). An exact
existing month cursor selects the next page; the next cursor equals the last
returned month only when more months exist. The response echoes limit and
cursor, includes total_months and returns no raw events, tenant or inputs. An
unknown cursor is 422. Pages always revalidate the same immutable completed
result; there is no latest selection. Pagination bounds the response without
truncating an accepted ledger period.

A missing cash series has series_status unavailable, monthly_cash null,
total_months null and no next cursor. It is not an empty series or zero cash.
An available series has a positive total_months and ordered unique month rows;
a cursor at the last month returns an empty terminal page. Other than page
selection, existing versioned Decimal/calendar code supplies every number.

401/403 cover authentication/scope denial; bad UUID/query/cursor is 422;
unfinished/foreign/different-model jobs are 404. Missing service or inconsistent
completed proof, source replay, projection or bindings is fixed 503. No new
source authority, DB role, profile, grant, migration, worker or model invocation
is added. Unknown or broken evidence is never replaced by invented cash.

The web explicitly requests a cash page after reading a completed economic
result, checks exact result/scenario/decision/hold identity, and displays an
accessible table with manual next/first-page controls. Korean month grouping
and UTC minimum times are explained; incomplete cash displays “미확인”.
Full farm/event/settlement inputs, break-even plan/trial UI, actual runtime CLI,
3D/replay and independent gates remain separate required work.
