# Backend inventory repeatability — 2026-10-03

Status: local fix and exact-head hosted software regression accepted.

## Observed failure

The resumed worktree was clean at `05a5f56`; origin was still
`c9bc689b138a8eee4292a6a041af26252defbc9b`. The existing
[backend run 36978991443](https://github.com/KIMSUNGHOON/OpenSmartFarmSim/actions/runs/36978991443)
is terminal **failure**. GitHub reports all six partition jobs successful and
the final `Require all partitions and identical complete inventories` step failed
with exit 1. `gh run view --log-failed` and the aggregate job log returned empty
output, including a fresh cache read. We do not infer actual pytest counts,
inventory digests or aggregate error wording from those empty responses.

Local reproduction found a sufficient cause for the inventory gate to reject:
four string UUID values were generated at discovery-test collection time.
Pytest included them in the parameter node IDs. Two fresh collections each had
47 cases, with eight differing IDs in their symmetric difference. The gate
hashes the complete sorted node list and therefore cannot accept those as one
identical inventory. The same defect appears when collecting the complete
repository, as shown by the new regression's RED result below.

## Change and review

The six invalid cursor cases now use one explicit canonical synthetic UUID,
its UUID object/uppercase forms, and descriptive fixed parameter IDs. Naive
time, non-UTC time, string time, UUID object, malformed UUID and uppercase UUID
remain rejected. In particular the uppercase case always contains letters;
it cannot occasionally become identical to a lowercase random UUID.

The added repository regression invokes the existing default partition
collector twice in fresh processes and compares full node inventories.
Children run collection only, with no DB/CLI/arithmetic execution, and have
pytest option/plugin overrides, inherited PYTHONPATH, real-CLI smoke switches
and GitHub output/summary destinations removed. A child must not append another
partition's output fields to the current hosted job. The aggregate gate and
partition algorithm retain their existing complete-inventory checks.

Review/implementation used the existing Codex CLI session
`01a0e064-b01b-7a22-8ef8-dd4afe0eb7dc`; turn metadata at
`2026-10-02T23:39:40.439Z` records `gpt-6.1-sol` / `xhigh`. No recursive CLI,
production input, source coefficient, runtime arithmetic or dependency changed.

## Local evidence

- New regression before the fix: **1 failed in 3.76 seconds**, at the generated
  discovery cursor node IDs. Log: `/tmp/ossf-ci-repeatability-red-20261003.log`.
- Existing partition checks plus the new regression and six cursor cases:
  **18 passed in 7.31 seconds**, no skips. Log:
  `/tmp/ossf-ci-repeatability-green-20261003.log`.
- Six independent `scripts/backend-ci-partitions.py INDEX --collect-only`
  processes collected the same **2,436** nodes. Their selected counts are
  `607, 426, 369, 350, 348, 336`. Their union equals the complete inventory
  exactly once. Inventory SHA-256:
  `bc890533260e91178d3b039ba5e5fea7c3a8032260d3bfdd8b194eb77854237a`.
  Manifests/logs are `/tmp/ossf-backend-collection-stable-INDEX-20261003.*`;
  summary: `/tmp/ossf-backend-collection-stable-summary-20261003.json`.

Commands used the locked backend Python 3.12 environment and nice level 10.
Collection follows the existing explicit delegation of
`tests/test_authored_full_software_path.py` to the separate authored workflow.
Outside-default UID and maximum-path smokes remain separate checks.
The 2,436 count is collection evidence, **not** 2,436 completed test executions.

Pinned test SHA-256:

| File | SHA-256 |
| --- | --- |
| `backend/tests/test_deterministic_job_discovery.py` | `6a1790901e17d09753e94b864e835c5f09635d53bae797e4273d72ce863f023d` |
| `backend/tests/test_backend_ci_partitions.py` | `0b58e262c426244883d0e0ffc387b7020dc899def3ea8a5edfde687801101dd4` |

## Hosted acceptance — 2026-10-03

At `4867c1f43b33e60ce7b6cd67f4315f925f77d89c`,
[backend run 37081707992](https://github.com/KIMSUNGHOON/OpenSmartFarmSim/actions/runs/37081707992)
passed all six partitions and the final aggregate. Actual job logs record
`607, 426, 369, 350, 348, 336` passes: **2,436 completed default tests**, no pytest
skips. All six inventories equal the local SHA-256 above. The final aggregate
confirms all partitions passed with the same complete inventory.
Partition 0 additionally passed the four distinct-UID service/planning tests and
the separate content DAC check; each partition's DB/password cleanup completed.
Two existing Pydantic serializer warnings in partition 2 remain visible.

The same head's [web run](https://github.com/KIMSUNGHOON/OpenSmartFarmSim/actions/runs/37081707914)
passed 160 unit and 51 browser tests. The
[authored run](https://github.com/KIMSUNGHOON/OpenSmartFarmSim/actions/runs/37081707927)
passed 141 executions across seven jobs (`104,13,15,3,1,4,1`) and their cleanup.
The [C0 run](https://github.com/KIMSUNGHOON/OpenSmartFarmSim/actions/runs/37081708001)
records actual pinned PostgreSQL 18.6 readiness, new DB container with persisted
sentinel and successful container/volume/password cleanup. These accept the
new discovery/consumer/operator-config software regression, not product CLI or
independent gate evidence.

`gh run view --log` returned empty for some successful runs. Direct GitHub job-log
reads supplied actual evidence; metadata alone was not used as test counts.
Local records are `/tmp/ossf-ci-backend-4867c1f-JOB-20261003.log`, corresponding
web/authored/C0 logs and terminal JSON files. Checked summary:
`/tmp/ossf-ci-4867c1f-and-images-summary-20261003.json`. Historical C9 failure
and its unavailable aggregate log remain recorded above.

## Remaining acceptance

Application images/Compose and real product CLI, independent releases and
G0–G4 evidence remain their existing subsequent work.
