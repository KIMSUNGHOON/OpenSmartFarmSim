# Backend CI partition implementation

Date: 2026-10-01 (Asia/Seoul). This is software CI evidence, not product CLI
execution, source approval, independent release or G0–G4 acceptance.

## Observed failure and change

The broad backend run [36810716327](https://github.com/KIMSUNGHOON/OpenSmartFarmSim/actions/runs/36810716327)
on `7f698e695d2ea5ba346d55f371fb916ed6a5c606` is terminal **cancelled**.
Its `backend` job `110205004881` ran from 03:29:27 to 05:59:53 UTC.
The check annotation says it exceeded 2h30m; this was not a passing result.
The four separate UID service/planning cases passed in 19.08 s. Full-suite
progress reached 66% before cancellation. The later content UID step did not
run; database/password cleanup passed.

The [partition contract](../contracts/backend-ci-partition-v1.md) changes
execution boundaries while keeping the full default pytest inventory and
existing delegated browser test. It uses six file groups, at most two hosted
jobs at a time and the unchanged 150-minute limit. The stable `backend` check
requires all six jobs, their cleanup and identical complete inventory hashes.
UID service/planning and content checks remain on partition zero. No actions,
dependencies, images, account settings or deployment authority are added.

The decisions were made in the ongoing development Codex CLI session with
`gpt-6.1-sol`/`xhigh`. No recursive Codex CLI or real product child was launched.
The contract links the official GitHub and pytest documentation checked for
matrix limits, aggregate dependencies/outputs and collection hook semantics.

## Local focused verification

One local heavy process at a time, `nice -n 10`, Python 3.12. Credentials and
source data were not printed or committed.

- Final focused partition tests: **11 passed in 3.33 s**, including the later
  filter regression assertion. An earlier run exposed inventory emission after
  a collection-filter exception; the fixed collector emits no record on that
  failure or on collection errors. The earlier 11-test passing rerun is not
  counted as additional distinct cases.
- YAML parses; every embedded shell program passes `bash -n`. The matrix,
  fail-fast setting, concurrency cap, aggregate and cleanup conditions are
  checked; no continue-on-error or enlarged timeout is present.
- The actual aggregate shell/Python program was executed with controlled test
  outputs. Matching successful hashes pass. Failure, cancellation, skipped
  results, missing outputs, mismatched inventories and malformed hashes all fail.
- An independent, unpartitioned actual pytest collection and six separate actual
  partition collections agree on **2,205 nodes in 132 collected files**.
  Each group contains 22 files, and their union is exact with zero duplicates.
  Complete inventory SHA-256:
  `10b67d5c5e84c898a4cb3170e9b1802bbcdf3601a8610da3706e85bf654db86e`.

| Partition | Files | Nodes |
| --- | ---: | ---: |
| 0 | 22 | 504 |
| 1 | 22 | 323 |
| 2 | 22 | 414 |
| 3 | 22 | 422 |
| 4 | 22 | 253 |
| 5 | 22 | 289 |

The authored full software path retains its existing separate browser workflow.
The two standalone real CLI smoke modules define tests only in their explicit
opt-in mode and have no collected nodes in either default baseline or partitions.
They were not newly ignored or executed recursively. Hosted inventory summaries
are about 299–330 kB each, below the
[1 MiB per-step summary limit](https://docs.github.com/en/actions/reference/workflows-and-actions/workflow-commands#step-isolation-and-limits).
Local logs and full manifests are under
`/tmp/ossf-backend-ci-partition-20261001/`, outside the repository.

## Remaining verification

An actual PostgreSQL 16.15 partition-four execution is in progress. It does not
replace PostgreSQL 18.6 hosted execution. All six hosted partitions, UID content
check, cleanup and aggregate on the new commit must finish before checking
`backend-ci-partition`. The source/farm web task still needs the same newly
registered Run's economic/assessment continuation and visual refinement.
Actual product CLI, independent release and full G1/G4 remain held.
