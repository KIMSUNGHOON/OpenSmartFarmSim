# Deterministic job discovery v1

Status: implemented; focused actual SCRAM software acceptance passed.
This is a dependency of the planned foreground consumer, not a
new HTTP route or a replacement for a worker's claim and validation.

## Existing boundary

[EconomicCalculationWorker](../backend/app/economic_calculation_worker.py),
[BreakEvenCalculationWorker](../backend/app/break_even_calculation_worker.py) and
[BreakEvenVerificationWorker](../backend/app/break_even_verification_worker.py)
currently require an exact job UUID. All use the `simulation` stage, but inspect
different immutable `input_version` values before invoking the existing
[JobStore claim](../backend/app/job_store.py). Selecting the oldest simulation
job indiscriminately would repeatedly send unrelated input to the wrong worker.

[`DeterministicJobDiscovery(jobs, *, tenant_id, input_versions)`](../backend/app/deterministic_job_discovery.py) accepts an
exact JobStore with its explicit audited authority login binding and a fixed
operator tenant. The selected versions are a nonempty immutable subset of:

| Input version | Existing worker |
| --- | --- |
| `economic-calculation-input-v1` | EconomicCalculationWorker |
| `economic-calculation-input-v2` | EconomicCalculationWorker with its farm binding |
| `economic-calculation-input-v3` | EconomicCalculationWorker with its authored Run binding |
| `break-even-calculation-input-v1` | BreakEvenCalculationWorker |
| `break-even-verification-input-v1` | BreakEvenVerificationWorker |

The consumer must bind the same jobs, tenant, principal and runtime policy as
its configured worker. Discovery does not create these dependencies, migrate
the database, infer missing farm/release bindings or call any CLI. Worker-specific
scope and dependency checks still occur in that worker immediately before claim
and through calculation/publication.

## Bounded read interface

`page(*, cursor=None, limit=25)` returns a frozen `DiscoveryPage` containing
matching `DiscoveredJob` records, a count of scanned rows and the next cursor.
The scan limit is an exact integer in 1–50 and excludes booleans. Each discovered
record contains only the canonical UUID and the exact input version; it does not
contain input bytes, monetary values, lease tokens, credentials or source data.
The cursor consists of the last scanned row's aware UTC `created_at` and canonical
UUID, using the existing `(created_at, job_id)` ordering.
The concrete cursor is the frozen `DiscoveryCursor(created_at, job_id)`;
database timestamps are normalized to UTC before constructing returned cursors.

The SQL scan is tenant-bound and restricted to simulation jobs. It includes:

- queued records whose `next_attempt_at` has arrived;
- active simulation records whose lease has expired, including canceled or
  exhausted attempts requiring the existing claim recovery to close them.

Live leases, future retries and terminal jobs are excluded. Returned matches
must have a selected version. The cursor advances over scanned unrelated versions
as well as matching ones, so older thermal/other simulation inputs cannot starve
this consumer. A full page supplies its last scanned cursor; a shorter page ends
the scan. The consumer starts a new pass after its configured wait so jobs that
become eligible behind a cursor are reconsidered. No unbounded scan is performed
inside one page call; at most 50 existing 64-KiB inputs are read.

Before choosing a version, each row's immutable input hash/size and canonical
JSON object are checked using the existing job helpers. An integrity failure
rejects the page with a fixed error; it is not interpreted as a supported input,
an empty queue or a successful job. The worker owns full typed input, parent,
source, current rights and domain validation. A syntactically recognizable version
does not approve its schema or contents.

The bound authenticated principal must currently have `metadata` and
`simulation_execute` for the fixed tenant. These checks occur before and after
the read. The actual selected-profile role audit also succeeds before returning
the page. Scope/provider/login/grant drift rejects the page with fixed public
errors and exposes no partial records. Operator-controlled SQL identifiers and
parameterized cursor/version values retain the existing store boundary.

## Claim, recovery and races

Discovery acquires no processing lease and does not write jobs, events,
publications, decisions or artifacts. Two consumers may discover the same UUID.
The existing exact-ID `worker.run_once(uuid)` performs its current access/input
checks and calls `JobStore.claim`; only that existing transaction decides ownership.
An intervening claim, cancellation, completion or schedule change can make
`run_once` return no work. A discovered row is an advisory candidate, not a promise.

Expired canceled/exhausted jobs remain discoverable for their configured input
version so the exact-ID claim can run its existing `_recover_expired` path,
close the old attempt and decline a new lease. Discovery itself does not implement
another recovery state machine. Unknown versions are left to their owning worker
or separately authorized maintenance. Retry and processing limits are unchanged.

## Required acceptance

[`backend/tests/test_deterministic_job_discovery.py`](../backend/tests/test_deterministic_job_discovery.py) must use the
actual disposable SCRAM JobStore and prove:

1. A mixed owned/foreign/stage/version queue returns only selected owned versions,
   skips future retries/live leases/terminal jobs, and advances across pages of
   older unrelated simulation inputs without modifying any persisted record.
2. Hash/canonical-input corruption and current tenant/scope/provider/grant changes
   are refused. Invalid limits/cursors/version selections are closed errors.
   No raw input, key or lease data appears in records, errors or representations.
3. Expired canceled/exhausted owned records reach existing recovery without a new
   processing lease, and two discoveries followed by competing existing claims
   preserve one owner and atomic publication.

The test uses synthetic software inputs and records actual version/hash/cleanup
evidence. It does not establish automatic CLI research, independent releases,
protected maximum throughput, scientific gates or production deployment. The
consumer/process and application Compose tasks supply subsequent evidence.

## Candidate checks (2026-10-02)

In the isolated `feat/deterministic-job-discovery` worktree based on `82ee0cd`,
42 isolated cases passed in 0.76 seconds with the locked backend environment.
They cover page/version/cursor bounds, unknown-version advancement, immutable
record contents, original input hash/canonical/size validation, current scope
and binding drift, and final role-audit ordering. The first collection failed
because the new module did not exist; subsequent functional reproductions
failed for final principal-induced binding drift and non-UTC DB timestamps
(two cases), and for final grant-audit ordering (one case). All passed after
the corresponding implementation changes.

Command: `env -u PYTHONPATH -u OSSF_TEST_PG_DSN nice -n 10 /home/sunghoonk/Workspaces/OpenSmartFarmSim/backend/.venv/bin/python -m pytest -q tests/test_deterministic_job_discovery.py -k 'not scram'`
from the isolated worktree's `backend` directory. I/O is replaced only for these
isolated cases; this is not authentication, SQL, race or publication acceptance.
The main workspace application bytes were kept frozen during the preceding
maximum calculation/verification test. The actual SCRAM cases ran after that
test terminated, using one local heavy execution slot.

## Actual SCRAM software acceptance (2026-10-02)

The full focused file passed **47 cases in 22.11 seconds**, including the five
actual-SCRAM cases and all 42 isolated cases. The locked backend environment
used local PostgreSQL 16.15, the existing disposable SCRAM fixture, explicit
authority login/current role audits and synthetic inputs/keys. No real CLI was
invoked. The following checks passed:

- Owned/foreign/stage/version separation, unrelated-version cursor advancement,
  future retry/live-lease/terminal exclusion and unchanged persisted jobs/events/
  attempts/outcomes/publications through discovery.
- Current tenant/scope/provider/login rejection, and actual grant drift both
  during the final principal refresh and before the next page's connection audit.
- Persisted hash and canonical-JSON corruption rejected the entire page with a
  fixed reason and no mutation. Hash corruption was injected by the administrator
  removing only the hash check in its disposable test schema.
- Two discoveries of the same economic UUID followed by competing existing
  workers produced one successful owner/outcome/result publication. Expired
  canceled/exhausted jobs reached existing claim recovery, closed their old
  attempts and acquired no new lease or publication.

The first actual run had **46 passed and one failed in 13.00 seconds**: the
economic fixture includes more than 25 older unrelated simulation inputs, so
the test incorrectly expected a match in the first page. The test was corrected
to follow the existing cursor, bounded to 250 scanned fixture rows per pass.
Production discovery did not change for this correction. Logs are
`/tmp/ossf-deterministic-job-discovery-scram-20261002.log` (failed expectation) and
`/tmp/ossf-deterministic-job-discovery-scram-v2-20261002.log` (terminal success).

Command: `env -u PYTHONPATH -u OSSF_REAL_CLI_SMOKE -u OSSF_REAL_AUTHORED_FULL_CLI_SMOKE OSSF_TEST_PG_DSN='<local baseline socket DSN>' OSSF_TEST_PG_BIN='<local PostgreSQL binary directory>' nice -n 10 /home/sunghoonk/Workspaces/OpenSmartFarmSim/backend/.venv/bin/python -m pytest -q tests/test_deterministic_job_discovery.py`
from the isolated worktree's `backend` directory. Its disposable cluster,
roles/schema and password files were cleaned by the existing fixtures before
terminal pytest success. This accepts discovery only. The foreground automatic
consumer/application Compose, hosted regression for these added files, real
product CLI/independent G1, scientific gates and G4 remain subsequent work.

The accepted discovery implementation SHA-256 is
`411dff0330ebd98b8d72d91a1ffe5108b0d7995191b3359d92bff8bbb288c884`;
the focused test SHA-256 is
`262f8816c94ab96001277bbf971251d76ad196b8fb8d1cb8aed3b05a9a42d5b8`.
The locked environment digest is
`e73e9ec049e80bfa4ad96afc33bfa25f5fddab60d60771284d6292178241beb3`.
The existing calculation runtime digest covers its enumerated calculation
files; these discovery bytes are recorded separately rather than silently
claiming they are included in that digest.

Self-review in actual Codex CLI session `01a0e064-b01b-7a22-8ef8-dd4afe0eb7dc`
(`gpt-6.1-sol`, `xhigh`; session metadata verified at `2026-10-02T06:15:31.814Z`)
found no remaining required changes in this discovery slice: SQL identifiers
and values use existing safe composition/parameters; the transaction is read
only, its page is bounded, current login/grants/scopes are rechecked, and the
existing canonical-input validator and worker claim/publication own their
respective boundaries. No dependency, arithmetic or deployment change is added.
