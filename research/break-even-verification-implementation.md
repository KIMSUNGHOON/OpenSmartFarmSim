# Break-even asynchronous verification implementation

Date: 2026-10-01 (Asia/Seoul). Development CLI: `gpt-6.1-sol` / `xhigh`.
Scope: internal service and leased worker preparation for the existing
`economic-break-even` / `api-flow` dependency. The
[contract](../contracts/break-even-verification-v1.md) is the acceptance boundary.

## Implemented behavior

`BreakEvenJobResultService.read_job_completion` resolves the actual completed
calculation's immutable input, attempt, publication, bounded receipt and stored
plan/request/result bytes. It returns closed metadata explicitly requiring
replay, without numeric results. Existing public result reading still runs the
full market/ledger replay before projecting conditional amounts.

`BreakEvenVerificationService` admits an immutable simulation intent for that
actual parent, pins current code/environment and all parent/plan/result hashes,
and rechecks these at admission commit. Its server key deduplicates the same
parent and current implementation. Actual audited stores share the current
tenant/principal/policy/schema/DSN and source-provider pointers. Existing read
scopes and `simulation_execute` are required; `break_even_write` is unnecessary.

The targeted worker claims only the expected input model, renews its live lease
and checks cancellation/current authority during full grid calculation and
reference rechecks. Replay occurs outside the final job-row lock. A final bounded
parent/current-binding recheck and the attempt/token/cancellation fence publish
completion, receipt, event and outcome atomically. No second full grid calculation
is run under that lock. Input changes hold; transient publication failure retries
through the existing queue delay; expired attempts recover with a new fence.

Actual replay evidence uses the existing tenant-private content-addressed store,
at most 1 MiB. The completed receipt is at most 4 KiB, binds evidence hash/size and
the immutable parent/input/result/code versions, and contains no private read
inventory or tenant ID. Failed transactions publish neither receipt nor success;
orphan private content cannot serve as authorized completed evidence. Assessment
remains hold and the receipt describes historical full-grid replay only.

Both new modules are in the runtime code manifest. No dependency, database grant,
schema, money formula, CLI invocation or request deadline changed. The preceding
[256-result codec correction](break-even-capacity-implementation.md) makes stored
results use their existing 1 MiB bound while inputs retain 64 KiB.

## Verification history

One heavy local process at a time, `nice -n10`, PostgreSQL 16.15, actual SCRAM
source/candidate/context/job stores, synthetic inputs and test signing keys.
Real model smoke flags are unset.

- An initial combined run was interrupted after detecting a metadata mismatch;
  its teardown error and partial progress are not accepted as a passing run.
  Identical request fields in a base/subclass Pydantic pair now compare as closed
  JSON contents. The isolated corrected metadata case passed in **63.91 s**.
- An initial admission test wrapped a returned UUID object in `UUID()` again;
  correcting the test to use the existing DTO's UUID gave **1 passed in 53.00 s**.
- The isolated full worker/private-evidence case gave **1 passed in 61.73 s**.
- The first combined verification/completion/existing-result selection stopped
  with **5 passed, 1 failed in 336.62 s**. A transient publication failure correctly
  returned to queued, but the test requested the next attempt before the existing
  one-second retry delay. The test now deterministically places `next_attempt_at`
  in the future, verifies refusal without a new attempt, then advances that row
  past the delay and checks attempt 2. No worker retry policy was changed.
- Final corrected combined selection gave **13 passed, 0 skipped in 726.92 s**:
  new verification 7, completion metadata 1 and existing result API 5. It checks
  immutable/idempotent admission, read-only scopes without replay at admission,
  actual full replay/private receipt, wrong input and forged parent refusal,
  cancellation after the first calculated trial, late rights withdrawal,
  publication rollback/delayed retry and expired attempt recovery. Existing
  completed-result tamper/binding/current-rights refusal, unconfigured assembly
  and actual bearer HTTPS/SCRAM/grant-drift paths also pass. Earlier isolated
  cases are not added to this count.

The final code/environment digests (the same implementation used by that run)
are `1dec4370f78433bad5a82486eda8ae0db8acc090df18476770d18cae314aed0e`
and `e73e9ec049e80bfa4ad96afc33bfa25f5fddab60d60771284d6292178241beb3`.
The official CI collector observes **2,265 nodes in 138 files** with inventory
SHA-256 `fc0500de35d880a54d6a168c97f2651b0b8f602cedd6932a2c1681d2cfe48cc5`.
Its six groups contain **512/375/510/228/278/362** nodes; their exact union equals
the default inventory. The existing delegated authored full path remains in
its separate workflow. Collection is not whole-suite execution or hosted proof.
Local file/anchor checks passed **427 links**, six changed/new Python sources
parsed successfully and `git diff --check` passed. Review checked source/parent
binding, immutable canonical bytes, scope/lease/cancellation fences, bounded
private evidence and transactional rollback. No new public approval path exists.
The owned temporary PostgreSQL cluster stopped after the final local run; the
baseline PostgreSQL and unrelated user services remain running.

## Remaining work

This slice adds no HTTP admission endpoint, public fast result reader, web flow
or protected operator entry point. A subsequent reader must bind the actual
completed verification/input/publication/receipt and tenant-private evidence,
then recheck parent/current rights/provider/code/dependencies before display.
Arbitrary supplied inventories and historical completion cannot authorize results.

The new actual SCRAM fixtures use two trials. Actual 256-trial SCRAM admission,
worker/result-read load and cancel/retry/withdrawal tests under the unchanged
30-second web limit remain required. The earlier 256-trial memory-provider/SQL-row
capacity test is not that proof. Hosted checks for this worker, actual product
CLI, independent G1/release and G0/G2/G3a/G3b/G4 evidence remain pending. No task
or claim gate is promoted by this implementation record.
