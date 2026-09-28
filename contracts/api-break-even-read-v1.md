# Conditional break-even result read v1

Status: software read/authentication candidate; no G1/G3/G4 acceptance.

`GET /v1/break-even-results?plan_id=<URL-encoded identifier>` has stable operation
ID `getBreakEvenResult`. The required service principal scope is `break_even_read`.
Query encoding supports existing Unicode identifiers and embedded slashes; IDs
are 1–200 characters with no surrounding whitespace or control characters.
The store independently binds the HTTP tenant to its authenticated source
principal. Other tenants/missing records receive 404, missing authentication 401,
missing scope 403, invalid/missing ID 422, unavailable dependency/replay failure
503. Error envelopes contain fixed messages only. An absent configured reader
keeps the advertised operation unavailable (503); it does not create a result.

`BreakEvenStore.get_break_even_read(tenant_id, plan_id)` returns a checked request
and result only after checking immutable canonical bytes/hashes, tenant/plan
binding and recalculating the entire pinned market/economic path at every listed
trial. Replay bytes must equal the stored result. Source rights, signed hold,
input versions and unchanged trial bindings remain required. The API checks the
requested plan ID again and projects an explicit public field set.

Public fields identify the plan, market-unavailable hold, decision time, period,
three distinct targets (`oi`, `operating_cash`, `cumulative_equity_cash`), and
variable unit (`kg` or `KRW/kg`). All monetary values are finite decimal strings
in KRW. Grid values/bounds/step/zeroes/bracket endpoints use the indicated variable
unit. Each trial contains its value, target value, minimum cash balance and cash
shortage. Unknown cash remains null; declared zero remains "0". Raw source and
sale/batch/tenant IDs, settlement evidence and internal result/rights hashes are
withheld. Bounded reason codes preserve the existing generic detail withholding.

Statuses retain engine meaning: `zero_on_grid`, `no_zero_on_grid`, `bracket_only`,
`nonmonotone_on_grid`, `hold`. Scope is always `conditional_user_grid_only`, input
origin/evidence `user`/`assumed`, and assessment `hold`. A bracket is not a root;
no grid zero does not prove no continuous solution, and nonmonotonicity provides
no single universal threshold. The route creates no plan/trials, approves no
market source, promises no future margin and supplies no crop ranking.

The [optional runtime profile v4](runtime-break-even-login-policy-v4.md) binds
BreakEvenStore to real SCRAM authority and full effective-grant auditing before
each query. Production sources, plan/trial generation, protected operator
assembly, independent economic/CLI/release proof and full browser/G1/G4 remain
incomplete. Fixtures test software contracts only.
