# Backend inventory repeatability — 2026-10-03

Status: local software fix accepted; same-head hosted execution pending.

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

## Remaining acceptance

Publish the pending protected-operator configuration together with this fix,
then require all six hosted partitions, the complete matching inventory,
aggregate job, UID checks and resource cleanup at that exact head. Until then,
new discovery/consumer/configuration hosted regression remains unaccepted.
Application images/Compose and real product CLI, independent releases and
G0–G4 evidence remain their existing subsequent work.
