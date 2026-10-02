# Break-even calculation publication fence follow-up

Date: 2026-10-02 (Asia/Seoul). Development remains in the existing exact
`gpt-6.1-sol` / `xhigh` CLI session. No recursive CLI, new source adoption,
independent release or G0–G4 promotion is involved.

## Observed cancellation gap

The calculation worker previously performed its second full-grid calculation
while holding the calculation Job row lock. Actual `JobStore.cancel` needs that
same row lock. A focused two-trial SCRAM barrier test reproduced cancellation
waiting behind this computation: **1 failed in 53.34 s**, specifically the
assertion requiring cancellation to be accepted while replay remained paused.
The barrier is owned by the test and is released in `finally`; the worker and
cancellation threads join. This reproduces a lock ordering gap, not a maximum
grid latency measurement.

## Change

Both complete calculations now run outside the final Job row lock and require
identical canonical result bytes. The second calculation records each freshly
observed lookup through the existing `ReplayReferences`; its immutable descriptor
snapshot performs no recheck and is not a full-grid approval/evidence record.
Existing engine hold/null/grid semantics remain in force.

Inside the final fenced transaction, the actual result row is pinned and checked.
Observed candidate/scenario/numeric/source dependencies are then read with the
same validators on one freshly audited connection; every current principal,
scope, provider, hash and final role audit is retained. Hold/context references
still use their original providers. The plan reference comes from the checked
uncommitted row returned by the transactional pin. Its identity and canonical
hash must match the observed immutable plan; a separate connection cannot read
that uncommitted row.

Lease/input/cancellation and code/environment guards surround final processing,
with renewals on the owning Job connection. Result, succeeded state, publication,
event and attempt outcome still commit together. There is no monetary/grid
calculation under the final Job row lock, no rights cache, no changed formula,
grant, schema, dependency or request deadline. The final dependency comparison
still serializes with publication; its actual maximum-grid duration remains
to be measured.

## Focused verification

The same cancellation regression is GREEN: **1 passed in 34.94 s**. The broader
focused selection completed with **45 passed in 1,178.10 s**, no failures or
skips. It covers calculation atomicity, late scope/provider/result/publication
faults, expiry, protected separate Python process execution, current
completed-result reading and replay contracts. It used PostgreSQL 16.15/SCRAM,
the existing synthetic two-trial fixture and one `nice -n 10` local process.
The shared fixture-builder edit occurred after this process imported the
fixture, so its fresh default-path check is recorded separately below.

An explicit `break_even_maximum_smoke.py` component diagnostic is prepared using
the existing synthetic generator, actual source adoption/candidate stores and
256 integer trial values. It separately measures cold setup and admission work
against the existing 30-second HTTP work budget. It is not default CI collection,
HTTPS body-EOF proof or a passed capacity check. The existing two-trial fixture
now delegates to the shared builder. Its fresh durable/idempotent server-plan
check passed: **1 passed in 43.02 s**, separately from the 45-case selection.
The explicit maximum diagnostic has started; its result remains pending.

### First actual maximum admission result

That invocation is now terminal: **1 failed in 2,297.44 s**. Its actual ASGI
admission returned **202**, with **256 trials**, a queued calculation intent,
and no published result. The failed assertion is specifically the existing
30-second admission work budget: **1,324.4641323270043 s** for the complete
component response. Successful contract admission does not establish usable
HTTP latency or capacity acceptance.

Cold preparation is recorded separately: the synthetic generator finished at
38.67325334799534 s, 1,630 actual source adoptions at 93.33703797099588 s,
and 256 actual candidates at 970.8483542320027 s. These preparation times were
outside the timed admission. The test ran alone at `nice -n 10` on local
PostgreSQL 16.15/SCRAM; no fixtures, grants, numeric rules or request deadlines
were reduced to obtain a pass.

During the long admission, one read-only admin diagnostic against only this
synthetic disposable database observed one client idle in its transaction and
zero backends blocked by another backend. It is an instantaneous diagnostic,
not a proof that no lock wait occurred during the whole request. No query text,
credentials or private numeric inputs were exported or modified.

The next action is targeted profiling of current store connections and
validation during admission, followed by a measured change retaining current
rights, identity, canonical-byte, binding and final checks. The 256-trial
calculation/verification/HTTPS EOF/cancel/retry/withdrawal requirements remain
pending. This failure is not retried unchanged and is not hidden by the broad
CI's passing two-trial software cases.

The official default CI collector reports **2,294 cases in 141 files**, inventory
SHA-256 `68bd8499da3358d28ae5f30ec3ec177454c59fd3b56a5ed2532cb01d8af0979f`.
The explicit maximum diagnostic is not included in that collection. Python AST
parsing passed for the three changed runtime modules and three changed/new test
modules. Collection and parsing are not additional executed test cases.
Changed Markdown's **345 local file/anchor links** resolve. The unstaged diff
whitespace check passes; the staged check is run separately before committing.

Synthetic records/keys and a two-trial cancellation barrier prove software
contracts only. Actual 256-trial calculation/verification/HTTP/reader EOF load,
cancel/retry/rights withdrawal under that load, protected automatic processing,
actual product CLI and independent execution/release/G1/G4 remain outstanding.

Current tested runtime code SHA-256:
`df66ef60dc011ece6cb29c4304661d81e754e24ce74ae761c6764faeadb70844`.
Locked backend environment SHA-256 remains
`e73e9ec049e80bfa4ad96afc33bfa25f5fddab60d60771284d6292178241beb3`.
Later source changes require their own implementation/version evidence; old
publication or review pins are not rewritten.

## Terminal hosted backend at 6a264c6

The [broad backend workflow](https://github.com/KIMSUNGHOON/OpenSmartFarmSim/actions/runs/36946195060)
for exact commit `6a264c6bd20a7202e03bee139de97463410dfc19` completed successfully
on PostgreSQL 18.6. All six partitions and the final aggregate passed with the
same complete default inventory SHA-256:
`68bd8499da3358d28ae5f30ec3ec177454c59fd3b56a5ed2532cb01d8af0979f`.

| Partition | Passed | Suite seconds |
| --- | ---: | ---: |
| 0 | 299 | 850.08 |
| 1 | 277 | 1948.75 |
| 2 | 374 | 1089.25 |
| 3 | 559 | 2271.24 |
| 4 | 306 | 1420.19 |
| 5 | 479 | 1836.40 |

The passing counts sum to **2,294**, with **0 skipped**. Each passing/deselected
pair totals the same full inventory count. Partition 0 has two existing Pydantic
serializer warnings; the other partitions have none. The separate distinct Linux
UID check gave **4 passed in 15.55 seconds**. Every partition's database/password
cleanup completed successfully, including the owned UID runtime cleanup.
The final aggregate explicitly reported all six partitions passing with identical
complete inventories. Local log archive:
`/tmp/ossf-ci-6a264c6-backend-20261002.zip`; parsed count/hash reconciliation:
`/tmp/ossf-ci-6a264c6-backend-summary-20261002.json`.

The same commit's [web/authored follow-up](web-break-even-verification-implementation.md#hosted-web-and-authored-follow-up-at-6a264c6)
passed web 160/51 cases, authored 141 executions across seven selections and C0.
This completes hosted software verification for the committed calculation fence
and web/API connection. It does not cover later uncommitted admission query/
principal changes, nor actual maximum capacity, product CLI or independent gates.
