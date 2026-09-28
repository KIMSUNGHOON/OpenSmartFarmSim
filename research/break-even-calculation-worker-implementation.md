# Break-even calculation worker evidence

Status: deterministic finite-grid software candidate; no G1/G4 acceptance.
The active root Codex CLI turn_context at 2026-09-28T21:23:33.806Z records
gpt-6-sol / xhigh in thread 01a0e064-b01b-7a22-8ef8-dd4afe0eb7dc. No recursive
CLI, additional model invocation or subagent is used. Reviewable output is
[the worker](../backend/app/break_even_calculation_worker.py),
[operator command](../backend/app/break_even_work.py),
[contract](../contracts/break-even-calculation-worker-v1.md) and
[actual PostgreSQL tests](../backend/tests/test_break_even_calculation_worker.py).

The worker targets an actual tenant/simulation UUID containing the admitted
server plan. It rebuilds the complete input from current scenario pins and runs
the existing full market/Decimal calculation at each grid point. Scope,
authority identities, source pointers and implementation/environment digests
are checked at lease checkpoints. Existing arithmetic, source validation,
grid/hold/null rules and Assessment hold semantics are preserved; no crop
output, coefficient, price or future margin is supplied by generated prose.

Result/request/plan rows and fenced completion/publication/event/attempt outcome
share the actual JobStore transaction. The full plan and every trial are
replayed again before commit. Lease renewals inside the final locked transaction
use its connection; opening another connection would wait on the same job lock.
Cancellation or an expired lease cannot publish or be revived. Receipt hashes
bind the actual input, plan and result; no CLI decision or usage is fabricated.
The selected implementation digest adds the worker, operator command and
existing economic formula module. A fresh independent release remains needed.

Actual SCRAM RED reached the missing worker module: **1 error, 7 deselected in
42.52 s**. The first development success-path run returned queued while the
selected digest file list was also being edited: **1 failed, 7 deselected in
92.54 s**. Its underlying exception was not captured, so it establishes no
specific root cause. With source files stable and test-only exception surfacing,
the connected completion/replay/receipt/lease-renewal case passed **1 in
203.96 s (3:23)**, 8 cases deselected. Existing break-even engine/store/HTTP and
JobStore renewal/fence/retry/cancel regressions passed **35 in 94.73 s (1:34)**.
The remaining worker boundary and foreground-process checks passed **8 in
1,080.75 s (18:00)**, with the previously verified connected case deselected.
Thus **44 unique cases** passed across three terminal runs: 9 new worker cases
and 35 existing regressions. They cover wrong tenant/stage/model and missing
scope, forged plan, post-insert scope/code/publication faults with rollback,
cancellation, expired-attempt recovery and a fresh Python process completing
an actual queued plan. The foreground factory/configuration is private
temporary test material with synthetic keys, not protected deployment proof.
Hosted CI for this change has not run; broader local backend/distinct-UID gates
were not rerun. All **118 local Markdown targets** in changed/new documents
resolve. The staged whitespace gate remains required before commit.

Review covers the unchanged default checkpoint path and arithmetic, same-
connection lease fence, canonical full-input/result comparisons, actual scope
checks around publication, rollback and fixed error codes. Synthetic sources,
hold/context signing keys and a local operator factory test software contracts
only. The command runs a Python numerical worker, with no recursive Codex CLI.

Verified job-to-result lookup, automatic trial assumptions from a declared
response rule, continuous-interval proof, large-grid latency/load, protected
deployment and full CLI/browser/independent release/isolation/custody remain
pending. Actual G0 rights/data, G2 measurements and G3 future/paired validation
remain missing. No broad task checkbox or gate decision is promoted.

The parent full backend suite took 66:55 under a 75-minute job limit; this
connected worker case alone took 3:23 locally, with eight more actual-source
cases added. The job limit extends to 90 minutes to accommodate them. Full
commands, distinct-UID/content checks and cleanup gates remain unchanged. The
parent receipt is appended in its research document with this functional change.
