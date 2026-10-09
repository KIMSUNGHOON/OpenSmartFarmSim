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

Actual PostgreSQL 16.15 partition four finished: **253 passed, 1,952 deselected,
0 skipped in 1,257.51 s**. Deselected items are assigned to the other five
partitions. Two preexisting Pydantic serializer warnings arise in intentionally
malformed G0 authority fixtures; no warning filter was disabled. The manifest's
full inventory matches the independently checked 2,205-node SHA-256 above.
This does not replace PostgreSQL 18.6 hosted execution. All six hosted partitions, UID content
check, cleanup and aggregate on the new commit must finish before checking
`backend-ci-partition`. The source/farm web task still needs the same newly
registered Run's economic/assessment continuation and visual refinement.
Actual product CLI, independent release and full G1/G4 remain held.

## Hosted checkpoint for the pushed candidate

Commit `0fdecc229109c54b025edfc23f7d499650213fd3` includes the six previous
source/client/web commits and the partition candidate. The draft PR remains
unmerged. [Web run 36826449988](https://github.com/KIMSUNGHOON/OpenSmartFarmSim/actions/runs/36826449988)
passed typecheck, **154 unit tests**, **49 Chromium tests**, build and audit
(zero reported vulnerabilities).
[C0 run 36826449844](https://github.com/KIMSUNGHOON/OpenSmartFarmSim/actions/runs/36826449844)
also passed on this exact commit.

[Authored PostgreSQL run 36826449848](https://github.com/KIMSUNGHOON/OpenSmartFarmSim/actions/runs/36826449848)
finished successfully with all seven suites and their database/password cleanup:

| Suite | Tests passed | Seconds |
| --- | ---: | ---: |
| API, including source and economic selection | 102 | 320.81 |
| Economic inputs/execution | 13 | 615.38 |
| Assessment parents/calculation | 15 | 993.08 |
| Financial selection | 3 | 851.75 |
| Assessment HTTPS | 1 | 388.80 |
| Browser, including two farm registration paths | 4 | 555.16 |
| Financial browser | 1 | 529.30 |

All CLI children and signing authorities are test fixtures. This hosted browser
proof predates the new same-Run financial continuation test; it verifies the
already committed registration/Run/3D and separate financial paths only.
The workflow zip was downloaded once to a private local task directory and
summary lines were extracted; simultaneous `gh run view --log` requests for
the same run produced shared-cache EOF/zip errors and were not used as evidence.

[Broad backend run 36826449924](https://github.com/KIMSUNGHOON/OpenSmartFarmSim/actions/runs/36826449924)
finished **failure**, with all six groups actually executed:

| Partition | Passed | Failed | Deselected | Seconds |
| --- | ---: | ---: | ---: | ---: |
| 0 | 504 | 0 | 1,701 | 2,569.53 |
| 1 | 323 | 0 | 1,882 | 1,455.60 |
| 2 | 414 | 0 | 1,791 | 759.83 |
| 3 | 422 | 0 | 1,783 | 1,320.20 |
| 4 | 253 | 0 | 1,952 | 1,446.81 |
| 5 | 288 | 1 | 1,916 | 813.91 |

All six logs record the identical complete 2,205-node SHA-256 above. There are
**2,204 passed, one failed, zero skipped** across the disjoint groups. Partition
zero additionally passed the four explicit UID service/planning cases in
18.78 s and the content UID boundary. Every database/password cleanup passed.
The stable aggregate correctly failed when partition five failed, despite the
matching inventory hashes; this does not satisfy full-suite acceptance.

The failure was `test_http_request_is_closed_and_preserves_legacy_formula` in
`test_farm_economic_contract.py`. Its old OpenAPI assertion required exactly
two branches, whereas the already implemented [authored economic contract](../contracts/authored-economic-execution-v1.md)
also requires the third closed V3 branch. The corrected assertion checks all
three exact input versions, closed properties and the unchanged formula on
every branch. No application behavior or test exclusion changed. The focused
contract file passed **2 tests in 0.38 s** without a database. A new hosted
commit must verify the correction before the partition task is checked.
The complete log zip was downloaded once into the private local task directory;
only summaries and the failure identity are retained here.

## Hosted acceptance after the OpenAPI correction

Exact commit `5dc63f34ef47ab34a6504404b768f76e7e1404dc`,
[backend run 36835133400](https://github.com/KIMSUNGHOON/OpenSmartFarmSim/actions/runs/36835133400),
completed **success** at 2026-10-01T09:19:34Z. The six disjoint groups passed:

| Partition | Passed | Deselected | Seconds |
| --- | ---: | ---: | ---: |
| 0 | 504 | 1,701 | 1,437.75 |
| 1 | 323 | 1,882 | 1,462.74 |
| 2 | 414 | 1,791 | 782.29 |
| 3 | 422 | 1,783 | 1,548.43 |
| 4 | 253 | 1,952 | 1,421.92 |
| 5 | 289 | 1,916 | 766.42 |

Each actual partition log records its selected count out of 2,205 and the same
complete inventory SHA-256:
`10b67d5c5e84c898a4cb3170e9b1802bbcdf3601a8610da3706e85bf654db86e`.
The extracted counts were checked: all six indices are present, each passed
plus deselected count equals 2,205, and the disjoint passed counts sum to
**2,205 passed, zero failed, zero skipped**. Partition four reports two warnings.
The prior OpenAPI failure is included in partition five and now passes.

Partition zero's four additional explicit UID service/planning cases passed in
13.35 s, and its distinct-UID content access check passed. The UID setup/content
steps are deliberately confined to partition zero; their `skipped` step status
in the other five groups is not a skipped pytest case. Every database/password
cleanup step succeeded. The stable `backend` aggregate received all six exact
inventory outputs, checked each partition and cleanup conclusion and succeeded.
The workflow's finite partitions, concurrency cap, 150-minute per-job limit,
existing test collection and mandatory authored-browser workflow were retained.

This satisfies the CI-partition task's software acceptance at this exact commit.
The [same-new-Run continuation evidence](source-farm-financial-continuation-implementation.md#hosted-verification-of-the-continuation)
also records the successful authored seven-suite, web and C0 workflows for it.
Later composer layout/registration-lock changes need their own hosted checks.
No product model invocation, independent G1 or G4 gate is inferred from green CI.
