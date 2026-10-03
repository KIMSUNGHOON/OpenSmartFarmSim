# Backend CI partition v1

Status: software candidate; hosted acceptance requires all six partitions,
the existing UID checks, cleanup and the aggregate check on the same commit.

## Collection and execution

[The runner](../scripts/backend-ci-partitions.py) uses the locked pytest's full
default collection from `backend/`. The sole existing exclusion is
`tests/test_authored_full_software_path.py`, which remains mandatory in the
separate [authored browser suite](../.github/workflows/authored-api-smoke.yml).
No slow test is excluded and the 150-minute job limit is unchanged.

Sort the collected file paths and assign each file's index modulo six. All
parameter variants and fixtures from that file stay in one process. Preserve
pytest's original item order within each partition. A file newly discovered
by pytest automatically joins the partition inventory; no hand-maintained list
of test names or discovery patterns substitutes for pytest's collection.

The collector records each item before filtering. Duplicate/empty collections,
empty partitions, another filter's additions or removals, collection failures
and a later change to selected items cannot emit an accepted inventory.
Environment-supplied pytest options/plugins are refused. Normal pytest failure,
collection and interruption exit statuses propagate to the job.

Each partition records `backend-ci-partition-v1` JSON: its index/count, sorted
complete node IDs, selected node IDs and the SHA-256 of the compact ASCII JSON
complete inventory. The local manifest is outside the repository; hosted job
summaries retain the complete record. Each job exposes only its uniquely named
`inventory_N` hash to the aggregate. These are software test inventories, not
agricultural inputs or CLI execution authority.

## Hosted workflow and gate

[Backend tests](../.github/workflows/backend-tests.yml) runs six isolated
PostgreSQL 18.6 jobs, with at most two running concurrently and fail-fast off.
Every job uses the existing pinned actions, uv/Python, image digest, locked
dependencies, loopback port and private random password files. Resource names
include the partition index. Partition zero also runs the two existing explicit
UID service/planning smoke modules and the distinct-UID content check.
Those modules are outside default pytest discovery and are not replaced by the
partitioned collection.

Each job always removes its database, password files and UID runtime; cleanup
failure fails that partition. The stable `backend` job always evaluates all
partition results. It succeeds only when the matrix reports success, all six
unique outputs exist and their valid inventory hashes are identical. Failed,
cancelled, skipped, missing or inconsistent partitions cannot pass this gate.
The separate authored/browser, web and C0 workflows remain required evidence.

## Verification and sources

Focused tests cover actual pytest discovery/parameter variants, complete union
without duplication, file ownership, inventory outputs, failed tests, collection
errors and unwanted filters/options. Compare an independent unpartitioned
collection with the union of six actual partition collections before acceptance.
Hosted results, observed durations and remaining holds are recorded in the
[implementation evidence](../research/backend-ci-partition-implementation.md).

Primary documentation checked on 2026-10-01:
[GitHub matrix concurrency and failure control](https://docs.github.com/en/actions/how-tos/write-workflows/choose-what-workflows-do/run-job-variations),
[job dependencies and unique matrix outputs](https://docs.github.com/en/actions/reference/workflows-and-actions/workflow-syntax),
[pytest collection hooks and deselection](https://docs.pytest.org/en/stable/reference/reference.html).
