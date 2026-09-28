# Break-even calculation worker v1

Status: deterministic finite-grid software candidate; no G1/G4 acceptance.

BreakEvenCalculationWorker targets one actual simulation UUID and tenant with
the existing break-even-calculation-input-v1 request/server-plan input. Different
stages/models/tenants and terminal/canceled jobs are not claimed. Actual audited
job/candidate/source/hold/context/break-even stores and PLAN_SUBMISSION_SCOPES
remain required; no grants, migrations or default credentials are added.

The worker verifies canonical leased bytes, rebuilds the server plan from current
actual scenario pins and compares the complete immutable input. Existing
BreakEvenService then recalculates every full market/economic trial. Checkpoints
around trial validation/calculation check scopes, identities, implementation and
environment, renew a live lease and reject cancellation/expiry. Renewals during
the final locked transaction use that same connection, avoiding a second
connection waiting on its own job lock. A single trial exceeding its lease
cannot be revived. Final replay retains existing grid/hold/null semantics.

Request/plan/result rows, fenced succeeded state, publication/event/attempt
outcome commit together. Current lease/input/cancel and full-result replay are
checked before completion. Failure rolls back visible rows/completion; orphan
content has no publication. The canonical receipt contains request/plan/result
hashes, plan ID, actual grid/Assessment statuses, fixed scan/formula versions and
implementation/environment digests. No numbers, source records or CLI decisions
are placed in the receipt. Succeeded means procedure completion, including an
engine hold; Assessment stays hold. No CLI invocation or usage is fabricated.

Fixed input rejection/hold and bounded existing transient retry codes withhold
private exception detail. Lease loss/cancellation cannot publish, and expired
attempts recover through the existing targeted claim path. Final row locking
serializes cancellation with commit; large-grid latency/load/deployment remain
unverified and cannot establish production/G4 acceptance.

The protected operator supplies a factory returning the exact worker and a UUID:

```sh
uv run --locked --group dev python -m app.break_even_work \
  --factory "$OSSF_BREAK_EVEN_FACTORY" --job-id "$OSSF_BREAK_EVEN_JOB_ID"
```

Factory/UUID validation precedes import; startup/execution errors are fixed JSON
with exit 2/3. Exit 0 exposes only job/attempt/state/reason/plan metadata or null.
The command invokes no model. Existing GET break-even results can replay the
completed row. [Verified job-to-result lookup](api-job-break-even-result-v1.md)
connects that completed row to its input/publication/receipt. Protected deployment,
automatic trial assumptions, continuous-interval proof and full CLI/browser/G0–G4
evidence remain subsequent acceptance work. Fixtures prove software contracts only.
