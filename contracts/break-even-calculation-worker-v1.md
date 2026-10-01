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
environment, renew a live lease and reject cancellation/expiry. Both full
calculations run outside the final Job row lock and must have identical canonical
result bytes. The second replay records fresh lookup descriptors; these are
observations rather than independent release or approval evidence. A single trial
exceeding its lease cannot be revived. Replay retains grid/hold/null semantics.

After pinning the result inside the final transaction, the worker rechecks those
observed dependencies through the actual source/candidate validators on one
fresh audited connection. The plan descriptor uses the just-checked row returned
by the transactional pin, whose uncommitted bytes cannot be read by a separate
connection. Current tenant/scopes/provider bindings, canonical hashes, hold/
context and final role audit remain required; the plan ID and hash must match.
Renewals in this final transaction use its own Job connection. No numeric grid
calculation runs while holding the Job row lock. Cancellation still serializes
with the bounded final publication fence; actual maximum-grid latency is a
separate measurement requirement.

Request/plan/result rows, fenced succeeded state, publication/event/attempt
outcome commit together. Current lease/input/cancel and full-result replay are
checked before completion. Failure rolls back visible rows/completion; orphan
content has no publication. The canonical receipt contains request/plan/result
hashes, plan ID, actual grid/Assessment statuses, fixed scan/formula versions and
implementation/environment digests. No numbers, source records or CLI decisions
are placed in the receipt. Succeeded means procedure completion, including an
engine hold; Assessment stays hold. No CLI invocation or usage is fabricated.

Result encoding uses the existing 1 MiB stored-result bound rather than the
64 KiB job-input codec. Request/input and bounded receipt limits are unchanged;
small result bytes/digests remain identical. The
[capacity correction](../research/break-even-capacity-implementation.md)
includes a 256-trial synthetic result and PostgreSQL row replay, not large-grid
SCRAM worker/HTTP throughput or asynchronous cancellation proof.

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
