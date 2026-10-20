# API nested projection cost observer — 2026-10-20

Status: local observer17 checks accepted; one actual diagnostic remains pending.
[Contract](../contracts/solar-api-request-cost-diagnostics-v1.md#v3-nested-projection-attribution) ·
[machine evidence](artifacts/solar-api-projection-cost-implementation-20261020.json).

## Corrected source interpretation

`api_crop_greenhouse_solar_prefix_routes.read` calls `public.read_prefix`, which
serializes the public record and calls `query._after_projection` before returning.
Thus the v2 observer's prefix root already includes projection-guard time and
counts. The previous note about no separate root is true; interpreting it as
missing total work would be incorrect. This change measures a nested component
and never adds it to its inclusive parent. Execution's existing root is the HTTP
`checked` helper, not just the query object's `read` method.

## Small diagnostic implementation

The opt-in v3 header records the fixed `prefix_projection` operation separately
when that real frame runs. One child per thread retains its parent operation and
monotonic start; original root/SQL/current/storage/source counters remain inclusive.
Other nested roots stay ignored. Exceptions and reused/concurrent threads close
only their own lifetimes. The shared active16/server32/response32/exception16 and
64KiB atomic-file limits are unchanged; dropped child spans are explicit in the
parent. An interrupted parent/child remains incomplete. Frame/thread IDs, raw
path/body/SQL/arguments/locals/identity/credentials/messages are not exported.

A controlled RED observed one inclusive parent with SQL/current2 and no child.
The final17 checks (old11 plus new6) pass on CPython3.12.3 and locked3.12.13;
these executions are not counted as34 distinct tests. Cases cover unchanged
returns, inclusive parent/child counts, exception/reused-thread cleanup, actual
concurrent children, active limit16, root+child window32 and response exclusions,
64KiB/Unicode bounds, private files/no temp and interrupted lifetimes.

The actual API/worker scripts are reconstructed exactly. Removing only the
selected headers restores original full hashes ab5a93ae…/14fe24de…. Worker header/
instrumented worker remain40408e24…/d1a1aac5…. The new API header isd378889d… and
instrumented API34c40d6e…. The product application261 files remains591eff7d….

All three final local guards preserved five live roots,2,148 original entries,
both frozen UI sources/assets and FD4→4, with owned/PG/passfile/temp remainder0.
Peak combined RSS was958,906,368bytes below1GiB; maximum PID145,444,864bytes
below512MiB. No product code/API schema, original actor body, numerical program or source
decision was changed. Native Codex CLI gpt-6.1-sol/xhigh reviewed this in its existing
session (private context reference/output hashes); recursive CLI/subagents0.

## Next actual observation

Use the existing hosted workflow's `unpaused_solar=true`,
`solar_worker_diagnostics=true`, `solar_worker_diagnostics_detail=worker-api`,
`solar_query_scope_cost=false`, `native_solar=false` once. Preserve original
CASE6/64/chunk1/poll/retry360 and supervision600/512MiB/1GiB. Reconcile immutable
run/head/header/actor/artifact identity and retained client/outer/child/worker
records. Window-excluded, ambiguous or interrupted spans must stay explicit;
never pretend the32 combined server records cover every retained client request.
The diagnostic does not repeat the valid ABBA trial or accept original normal64.

Global goal remains active. Original normal39377630664's46/64 stopped metadata
is still a nonacceptance. Independent hold/cancel/live WebGL/WSL activation,
new Solar deployment, external farm/economic data and G0–G4 remain open.
Whole backend/browser CI and new DOM/WebGL are not run in this step.
