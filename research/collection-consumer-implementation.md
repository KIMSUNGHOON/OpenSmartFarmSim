# Automatic owned collection implementation — 2026-10-04

## Implemented boundary

The [contract](../contracts/collection-consumer-v1.md) adds a closed collection
profile to the existing bounded advisory query and a separate foreground
`app.collection_consume` entrypoint. Economic discovery retains its version,
stage and scope boundary. The collection loop freezes its exact worker/service,
registry/store and tenant/lease/poll bindings, rechecks current access and delegates
claims, recovery and record publication to the existing CollectionWorker.
No numeric model, source adoption, approval provider or scientific gate changed.

Self-review in actual Codex CLI session
`01a0e064-b01b-7a22-8ef8-dd4afe0eb7dc`, model `gpt-6.1-sol`, effort `xhigh`
(observed turn metadata `2026-10-04T00:48:34.512Z`) checked correctness, module
boundaries, secrets, bounded polling and current authority. It found a pre-mutated
worker could substitute a fake service before freezing; its regression failed
before the exact CollectionService check and passed after it. No recursive CLI
was launched. The same session is the development reviewer, not an independent
execution/data/release authority.

## Focused actual acceptance

The combined new consumer, unchanged economic discovery tests and original owned
collection tests passed **95 cases in 55.97 seconds**, zero skips, in the locked
backend environment. This comprises **34 new cases**, 47 existing discovery and
14 existing collection cases. Tests used a disposable local PostgreSQL 16.15
SCRAM cluster, fresh scoped logins/roles/schema, synthetic research executable,
source bytes and signing keys. One heavy local slot ran with `nice -n 10`.

Actual separate Python consumers proved:

- Same-tenant due collection/expired-lease discovery excluded unrelated versions,
  simulation/foreign jobs, future retries, live leases and terminal jobs. Keyset
  cursor advanced over unrelated input, and jobs/events/attempts/outcomes/
  publications had the same persisted digest before and after discovery.
- A normal factory completed a queued collection without a UUID argument. It
  preserved the three original sources, one publication/outcome and
  `software_fixture_only`, Assessment hold, G0/G1 not accepted.
- SIGTERM during an active attempt finished or acknowledged current cancellation
  safely and left the following job with zero attempts. Cancellation published
  no collection record.
- SIGKILL left no publication or terminal outcome. After the fixture administrator
  expired its lease, a fresh consumer recovered attempt 2 and published once,
  retaining `lease_expired` and `succeeded` states. Collection completion's
  termination reason is the existing `completed`.
- Destroyed retained parent-output proof held the active collection without a
  publication; actual SELECT revocation stopped idle discovery with fixed exit 3.
- Metadata output excluded record/hash/input/credentials and source bytes.
  Signal handlers/wakeup descriptors were restored and owned pipes closed.
  Owned processes and disposable cluster/roles/schema/passfiles were cleaned
  before terminal success; the existing baseline database was not changed.

Idle observation: 2.2641429549839813 seconds including termination, 0.02 CPU
seconds, minimum page spacing 1.0308333489811048 seconds, SIGTERM exit
0.06378344900440425 seconds. This single local observation demonstrates the
configured wait; it is not a production throughput or availability SLA.

Command from `backend`:
`env -u PYTHONPATH -u OSSF_REAL_CLI_SMOKE -u OSSF_REAL_AUTHORED_FULL_CLI_SMOKE OSSF_TEST_PG_DSN='<baseline socket DSN>' OSSF_TEST_PG_BIN='<PostgreSQL binary directory>' nice -n 10 .venv/bin/pytest -q -s tests/test_collection_consumer.py tests/test_deterministic_job_discovery.py tests/test_owned_fixture_collection.py`.
Actual socket creation required execution outside the restricted workspace
sandbox. The private fixture DSNs/keys were not stored in this report.

Initial RED failed collection because the new class was absent (0.24 seconds).
An isolated run passed 68 and skipped 11 database cases, so it was not SCRAM
acceptance. The first actual run passed 92 and failed one assertion: the test
expected termination reason `succeeded` where the existing collection worker
stores `completed`. Its actual recovery/publication succeeded. The expected
reason was corrected and both state and reason are now checked. That initial
combined log filename was reused for the rerun; the failure is retained in the
CLI tool transcript. Final evidence was copied after terminal exit to immutable
`/tmp/ossf-collection-consumer-final-20261004.log`, SHA-256
`683f417c6303b9a13a3037abd0c6bb12f50aeb4514ed31e1ea254fcf0a60cc98`.
The separate fake-service RED remains
`/tmp/ossf-collection-consumer-service-red-20261004.log` (one failed, 0.78 seconds).

Inventory regressions passed **12 cases in 6.48 seconds**, including independent
whole-repository collection twice; log
`/tmp/ossf-collection-consumer-inventory-20261004.log`. Whitespace and Python
syntax checks also passed. Hosted full regression for these new bytes is pending.

## Byte identity and remaining holds

| File | SHA-256 |
| --- | --- |
| `backend/app/deterministic_job_discovery.py` | `2198952657592b340b5b5d32e58178a2c80d85110502e41e7eed0ace03c07412` |
| `backend/app/collection_consume.py` | `99b7c4cb33da71a9cc5be915edfc3258883c3eb16d0f316b77394c00b4d663f7` |
| `backend/tests/test_collection_consumer.py` | `6eafe9d755b4ffd768b297bbf71b83b913151eedfff7564cb73ffcad26c66651` |
| `backend/uv.lock` | `e73e9ec049e80bfa4ad96afc33bfa25f5fddab60d60771284d6292178241beb3` |

Consumer/discovery bytes are recorded separately from the existing enumerated
calculation digest. Source/CLI Compose, actual product model calls, independent
source/release and credential custody, G0–G4/crop ranking and maximum concurrent
operation require their own evidence. These synthetic records authorize no
agricultural or financial prediction and accept no new dataset.
