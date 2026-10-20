# Actual nested projection cost — 2026-10-20

[CI39380625672](https://github.com/KIMSUNGHOON/OpenSmartFarmSim/actions/runs/39380625672),
source67bd392/attempt1/job118488692429, completed/failure.
[Machine evidence](artifacts/solar-api-projection-cost-observation-20261020.json) ·
[local17/actor verification](solar-api-projection-cost-implementation-20261020.md).

## Acceptance boundary

The diagnostic observation is accepted, original normal64 is not. Original actor
bodies/arguments/CASE6/64/chunk1/poll/retry360/RSS were retained; only selected
observer headers changed. API original ab5a93ae…/instrumented34c40d6e… and worker
original14fe24de…/instrumentedd1a1aac5… matched. Run/source/job/header/artifact
digest/path and ownership/resource cleanup were reconciled once.

Worker's actual last-confirmed record is50/64, model UTC2026-10-01T00:01:40.123456Z.
No normal proof or DB role/schema0 count proof exists; both actors ended with
cleanup−15. The instrumented50 and earlier uninstrumented46 are different
observations, not a throughput comparison or evidence to retry unchanged normal.

## Retention and correlation

The bounded journal retains32 completed clients and32 server records:19 outer
operations and13 nested projection children.19 clients uniquely match an outer
operation;13 older retained clients lack a retained outer span. There are no
ambiguous client matches, orphan retained children or unfinished API spans.
Two responses,24 server records and72 exceptions were dropped from the recent
windows; active/counter drops are0. The raw observation is22,111bytes/64KiB.
Do not describe all retained clients as fully attributed.

All13 complete prefix/sample pairs preserve inclusive parent/child structure.
Successful parent HTTP requests took8.405119–10.179368seconds; each parent
recorded6 current checks,912 sources andSQL5,090/5,091. The nested guard took
2.974239–4.034395seconds,33.2–39.7% of that parent's wall time. Each child
performed2 current checks,304 sources andSQL1,697; child storage loads were1–2.
Across these same13 pairs, parent wall is118.905344seconds and child wall
43.085033seconds (weighted36.23%). Parent CPU76.761937seconds includes child
CPU29.161234seconds. These nested totals are never added to each other.
The existing prefix root already includes serialization and `_after_projection`;
this is a new breakdown, not newly discovered omitted total work.

Worker phase totals include `_before`54 calls/31.224084seconds and `_confirm`51
calls/151.844040seconds. `_custody_call`322.917307seconds includes nested calls;
it must not be added to those totals. One `_custody_call` and `run_once` remained
active at termination. Observer overhead is included; client CPU is not server
CPU. These timings select investigation areas and do not establish production
capacity or an exclusive CPU breakdown.

## Preserved resources

Hosted guard378.200681seconds, peak PID135,081,984bytes/total385,736,704bytes,
FD7→7 and owned/temp remainder0, reasonnull. Local curation3.513988seconds,
peak total935,944,192bytes, FD4→4, original2,148 entries/five roots/two UI
sources/assets preserved and owned/PG/passfile remainder0. Hosted evidence does
not accept WSL combined capacity. Product261 files remain591eff7d….

## Next narrow candidate

Source audit finds custody `_open` already owns a registration scope; the
rejected confirm joining candidate is not revived. No ownership/JSON cache or
permission result cache is proposed. Before changing more query lifetimes,
consider the fresh input JSON duplicate-key loop: a historical isolated worker
profile recorded420,263 `pairs` calls and0.267815seconds exclusive CPU in that
loop. Its source/component hashes still match current code; the sole production
file change since that profile is execution query scope. This historical cost
is a separate diagnostic, not the concurrent request's CPU attribution.

The proposed research-only screen compares the current per-key loop with fresh
native dictionary construction plus duplicate-count validation. It keeps a new
parse for every call, original decoder/constant hooks, key order, errors,
UTF-8/nonfinite/depth/bounds and mutable-result isolation. No cached JSON values,
callee/ownership tables or old retired codec experiment is re-enabled. Controlled
correctness/caller cases and whole original worker quantum costs must support
any adoption; a primitive speedup alone cannot accept a product change.

Native Codex CLI gpt-6.1-sol/xhigh owns this review in the existing session.
Recursive CLI/subagents0. No full backend/browser CI or new DOM/WebGL ran.
New Solar is not deployed, real farm runs0, independent data/G0–G4/whole UI and
completion dates remain open. Normal→hold→HTTP cancel→live WebGL→WSL stays gated.

## User progress publication

[Publication receipt](artifacts/solar-api-projection-cost-final-publication-20261020.json)
verifies the same updated JSON at5173/5174, HTTP200/no-store, original HTML/
2,173 frozen ventilation files, original entries/five roots and owned cleanup.
It explicitly retains original normal46/64 nonacceptance and marks diagnostic
confirm50/64 as diagnostic. No new UI code/DOM/WebGL was run.
