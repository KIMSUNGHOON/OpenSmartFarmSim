# Break-even replay reference evidence implementation

Date: 2026-10-01 (Asia/Seoul). Scope: internal software preparation for the
large-grid asynchronous completion path required by `economic-break-even` and
`api-flow`. The current development CLI uses `gpt-6.1-sol` / `xhigh`.

## Implemented behavior

The [contract](../contracts/break-even-replay-evidence-v1.md) defines a closed
reference recorder and `BreakEvenStore.capture_break_even_replay`. The actual
existing engine performs its full grid/market/ledger calculation. Every observed
lookup is fresh; the evidence list alone deduplicates matching method/arguments.
Changed or missing returns and invalid/bounded reference data abort capture.
After any failure that recorder cannot be reused, including after the old value
is restored. Rechecks have caller checkpoints for cancellation/current authority.

Capture compares the actual canonical request/plan/result, checks every planned
candidate was visited, then rechecks the unique references, stored bytes and
current store binding. The final implementation/environment check follows the
last guard. An early engine hold with fewer observations than planned trials
cannot produce full-grid evidence. Existing synchronous readers and Decimal
formulas keep their previous behavior.

The frozen record contains only scoped IDs/revisions and hashes, not raw source
records or numbers. The new module is included in the runtime code inventory.
For the final focused test selection, actual digests are:

- Code: `a3fb38ee950792fe297521a941a7bfb8a5a1c7687523736a3e3e9c930bceb885`.
- Environment: `e73e9ec049e80bfa4ad96afc33bfa25f5fddab60d60771284d6292178241beb3`.

## Focused verification

One local process at a time under `nice -n10`, PostgreSQL 16.15:

```sh
cd backend
env -u PYTHONPATH -u OSSF_REAL_CLI_SMOKE -u OSSF_REAL_AUTHORED_FULL_CLI_SMOKE \
  nice -n10 .venv/bin/pytest -q tests/test_break_even_replay.py \
  tests/test_break_even_replay_runtime.py tests/test_break_even.py
```

The operator's existing private `OSSF_TEST_PG_DSN` and `OSSF_TEST_PG_BIN` were
provided in the environment. Final result: **43 passed, 0 skipped in 333.15 s**:

- **23 reference tests:** fresh repeated lookups, canonical date/time/Unicode,
  exact arity for all 13 methods, 200-character references, invalid values,
  reference budget, sorted/unique/plan-bound manifest shape, changed input,
  lost access, cancellation and permanent failure after an interrupted capture.
- **5 actual SCRAM cases:** an existing completed two-trial calculation is replayed
  through actual source/candidate/hold/context/plan stores. A fresh store instance
  produces the same record; current synchronous read remains compatible.
  Late source-scope withdrawal, candidate-provider replacement, code/environment
  drift and a checkpoint cancellation return no record. The original calculation
  publication remains the sole publication; capture creates no completion.
- **15 existing grid cases:** existing three-target, zero/bracket/nonmonotone,
  fixed-input/shock, persisted-candidate and source/scope behavior.

The unchanged CI partitioner's actual `--collect-only` path includes all **28 new
cases** in **2,253 cases / 135 files**. Its six file-atomic partitions contain
244/321/352/510/331/495 cases and their union equals the complete inventory;
inventory SHA-256 is
`95aa173ab03ce33c46e9012def51a47a214e880236b85324f20636636a56fe7e`.
The existing authored full-path file remains delegated to its separate workflow.
Collection is not execution or hosted PostgreSQL 18 verification. Local file and
anchor checking passed **315 links**, as did `git diff --check`.

The records and signing keys are synthetic. No model child was invoked, no
independent release was issued, and no agricultural or forecast claim follows.

## Review and remaining work

Review checked exact replay/coverage, bounded typed records, current tenant and
provider checks, parameterized SQL, and runtime code pinning. The interrupted
recorder reuse issue was fixed before the final selection. Canonicalization
reuses the existing market serializer; no dependency or schema was added.

This is evidence capture, not a cached approval or an asynchronous job. Sequential
rechecks are not an atomic view of all external state. Full provider-chain and
lease guards, immutable parent/input/attempt/publication binding, a receipt and
current-rights bounded result reader still need implementation. Existing HTTP
reads continue full replay. The 1 MiB/16,384 limits and the two-trial SCRAM fixture
do not prove 256-trial admission, completion, retry/cancel or the 30-second web
deadline. Those load and hosting checks, actual product CLI/independent G1 and
G0/G2/G3a/G3b/G4 evidence remain pending. Parent task checkboxes stay unchecked.
