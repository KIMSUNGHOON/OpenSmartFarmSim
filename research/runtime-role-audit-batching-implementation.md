# Effective runtime privilege audit batching

Date: 2026-09-29. Software performance change; no operating or G0–G4 approval.

## Trigger and implementation

The actual break-even browser path completed its real worker but could not read
the fully revalidated result within the existing 30-second request deadline.
An actual SCRAM profile audit measured 270 SQL statements per audit. Each store
connection runs that audit, and pinned trial validation opens many connections.
This identifies a repeated cost; it does not establish that all latency comes
from the audit or that API replay is an operating-capacity design.

For each of the same four roles, table and column effective privilege checks
now query all inspected relation OIDs together. Every original privilege and
`WITH GRANT OPTION` predicate still runs, including PG17+ `MAINTAIN`, all live
columns, inherited/table/PUBLIC effective rights and extra schema relations.
Sequence/routine checks, role attributes/membership, schema/database ownership,
DDL/security-definer escapes and default ACL checks are unchanged. No identity
check, source replay, permission check, connection, grant or cache was removed.

PostgreSQL's [privilege inquiry documentation](https://www.postgresql.org/docs/18/functions-info.html#FUNCTIONS-INFO-ACCESS-TABLE)
supports role/object OIDs, column attribute numbers and grant-option inquiries.
Its [array documentation](https://www.postgresql.org/docs/18/functions-array.html)
documents `unnest`; the batch uses parameterized OID arrays and a Cartesian
product with the original privilege list. Equivalence to the old checks is an
implementation inference verified against real grant-drift tests.

The existing exact development CLI context at `2026-09-29T11:31:13.535Z`
reports `gpt-6-sol` / `xhigh`, thread
`01a0e064-b01b-7a22-8ef8-dd4afe0eb7dc`. No recursive CLI, subagent or product
model invocation occurred.

## Measurement and security verification

The same new test uses actual local PostgreSQL 16.15 SCRAM authority and the
market/source/break-even policy profile. Three successive audits of a fresh
fixture were measured before and after; there is no permissions cache.

| Variant | SQL statements for each audit | Median of three audits |
| --- | --- | --- |
| Existing per-relation queries | 270, 270, 270 | 0.066718s |
| Batched table/column queries | 94, 94, 94 | 0.031874s |

The deterministic regression budget is at most 120 statements for this profile;
wall-clock timing is recorded rather than used as a flaky test assertion.
The first new test referenced a nonexistent policy property and failed in
1.88s. After that harness correction the original audit reached the intended
budget failure in 2.10s. The final benchmark and existing runtime roles, SCRAM
login and market-runtime suites passed **76 cases in 72.18s**. They cover
forbidden role/table access, missing/extra/grant-option/column/PUBLIC grants,
membership/default ACL drift, wrong login/identity and DDL/definer escapes.

The change is retained for its measured reduction and passing security scope.
The original runtime code digest already includes `runtime_roles.py`; new
calculations therefore record the changed code without relaxing historical
receipt/release boundaries. Full hosted PG18 tests and actual browser latency
are separate verification. Large grids, operating load and G4 remain unproved.

## Column audit follow-up (2026-10-01)

The authored registration/re-read fixture was profiled with actual PostgreSQL
16.15 SCRAM logins. Its unchanged baseline at `bf53a36` took **65.04s** under
`cProfile`; **1,527** fresh role audits accounted for **48.380s** of cumulative
time. This is a synthetic software fixture measurement, not a deployment SLA.

The final column query uses `has_any_column_privilege` for each inspected table
and each original column privilege. The closed table matrix still requires a
whole-table grant wherever a privilege is allowed; that covers every live
column. Any grant on a denied column remains an error, as does any grant option.
The same column query also checks the **current table grant**, so a revocation
between the earlier table query and the column query cannot be disguised by one
remaining column grant. Permissions are neither cached nor assumed from an
earlier query. Extra relations and the other audit predicates remain inspected.
This equivalence within the existing closed matrix is an implementation
inference from PostgreSQL's [privilege inquiry semantics](https://www.postgresql.org/docs/16/functions-info.html#FUNCTIONS-INFO-ACCESS-TABLE)
and the following real grant tests.

A new injected mid-audit revocation test first failed because the intermediate
implementation accepted a remaining `input_bytes` column grant after revoking
the whole-table read. The same-query table check corrected that failure. Added
cases also reject a known-role column grant, column grant option, missing table
grant and unexpected UPDATE grant.

The original audit function from `bf53a36` and the final function were measured
alternately three times against the **same** SCRAM connection and policy; their
returned audit metadata matched. SQL statement counts were unchanged.

| Variant | Three measurements (seconds) | Median | SQL statements |
| --- | --- | --- | --- |
| Baseline | 0.025126, 0.020334, 0.018879 | 0.020334 | 30, 30, 30 |
| Final column inquiry with current table check | 0.013036, 0.011383, 0.012405 | 0.012405 | 30, 30, 30 |

The median decreased by about **39%**, and the three sample ranges did not
overlap. This measures audit cost only; end-user request latency is not inferred
from this small fixture. The tracked runtime-role/login, farm authoring,
round-trip budget, market-runtime and routine-revocation suites plus the
temporary comparison test passed **93 cases in 145.67s**. The standalone tracked
budget test measured 30 statements on each of three audits and a 0.013091s
median. No new wall-clock threshold was added.

### Attempt ledger

| Attempt | Measurement | Decision |
| --- | --- | --- |
| Move the existing full privilege matrices into SQL filters | Same profiled fixture: 65.04s → 65.09s | Reverted; no measured improvement |
| Use any-column inquiries without rechecking table rights in the column query | Same profiled fixture: 46.76s; injected revocation test failed | Replaced; correctness failure |
| Use any-column inquiries and current table rights in the same query | Same-connection median: 0.020334s → 0.012405s; 93 tests passed | Retained |

The final change still requires hosted PostgreSQL 18 CI verification. The
different code digest is recorded for new calculations; historical receipts
and releases are not rewritten. Actual product CLI, independent G1 release,
operating load and G4 remain separate holds.

## All-role query batching follow-up (2026-10-01)

Date: 2026-10-01. Software performance increment; no G1/G4 release.
Development uses the ongoing Codex CLI `gpt-6.1-sol` / `xhigh` session.
No nested model invocation or product model execution is claimed.

### Observed problem and measurement

At exact commit `93e30a7676b335a45d2fbc2b466c715bce583647`,
[authored workflow 36843547162](https://github.com/KIMSUNGHOON/OpenSmartFarmSim/actions/runs/36843547162)
finished with six successful suites and one failed financial-browser suite.
The browser stopped waiting for the new assessment admission, with the UI
showing an unresolved request and its same-request recovery button. The old
harness retained only the tail of the exception, so this evidence cannot
distinguish a deadline from another lost response. Excessive admission latency
is an inference supported by the subsequent profile, not a recovered original
timeout trace. This failed run is not accepted as a passing workflow.

The separate authored-browser suite passed **4 cases in 851.68 s**, including
saved-source selection, new registration, new Run, money/cash, held assessment,
reconnection and the same 3D Run. Its 27 financial bodies completed at client
reader EOF, with a maximum of **26.3284 s** under the unchanged 30-second limit.
The exact commit's web suite passed 154 unit tests and 50 Chromium cases;
C0 also passed. These source-path results do not erase the separate failure.

A bounded cProfile wrapper outside the repository measured the actual
`CalculationAssessmentService.prepare` during the existing HTTPS/browser smoke.
The first preparation performed **451 full grant audits** and **14,763 SQL
execute calls**. Grant audits used 10.036 s of the 14.3178 s preparation.
Admission retains both the initial preparation and its current-input check
inside the commit guard. The observed admission body took **28.1211 s**.

### Change

[The auditor](../backend/app/runtime_roles.py) now queries all four fixed roles
together for CONNECT, schema/database/definer access, sequences, table and column
matrices, and routine execution. It retains the existing `_allowed` policy,
version-selected tables, PostgreSQL 17+ MAINTAIN check, grant-option checks,
ownership/ACL/default/membership checks, and table-level verification alongside
column access. Every real connection still authenticates and runs a fresh full
audit; there is no rights cache, connection reuse or deferred authorization.
No grant, migration, credential, arithmetic, API schema or request deadline changes.

[PostgreSQL 18 privilege inquiry documentation](https://www.postgresql.org/docs/18/functions-info.html#FUNCTIONS-INFO-ACCESS-TABLE)
defines the existing named-role checks and grant-option inquiries. In particular,
any-column privilege can succeed through either whole-table or individual-column
access. Therefore the separate whole-table comparison remains essential; its
existing inter-query revocation test still mutates real permissions and fails closed.

The standalone financial-browser smoke now observes **actual SDK reader EOF**,
successful `no-store` bodies and the 30-second bound. Failed attempts report only
paths/methods/statuses/timing, with the synthetic token redacted before Python
reports an exception. No response body or credentials are exported. A browser
transport-close event is diagnostic, not a substitute for reader completion.

### Verification

One heavy local process at a time, `nice -n 10`, locked Python/backend and
PostgreSQL 16.15; real model smoke flags unset:

- Role audit, role policy, authenticated login and market runtime selections:
  **100 passed, 0 skipped in 61.32 s**. The 20 additional cases exercise each
  request/worker/supervisor/authority role with an unapproved table, column grant
  option, schema, sequence or routine permission. Existing PUBLIC, membership,
  defaults, login laundering and inter-query revocation cases remain included.
- Actual HTTPS/SCRAM/Chromium financial continuation:
  **1 passed, 0 skipped in 419.70 s**. It admits two new jobs, compares server
  money and the complete cash row, executes the deterministic worker and test
  CLI hold, reconnects, recovers the same assessment and draws the same
  **120-point Run**. All **29 actual reader EOF bodies** succeeded with
  `no-store`; the maximum was **24.5048 s**, below the unchanged 30-second limit.
  Zero console/page errors; two recognized GPU readback warnings.
- In the first two admission preparations, the full audit count stayed **451**
  and SQL execute count became **7,998**. Durations were **12.3756/12.0637 s**,
  compared with **14.3178/13.7387 s** before. These are two fixture observations
  with profiler overhead, not a percentile, load test or production guarantee.
- The existing SCRAM round-trip budget and first/last-routine grant/revocation
  cases passed **9 further cases in 4.20 s**, giving **109 distinct policy cases**
  plus the browser case. Three full profile audits each used **15 SQL queries**;
  the observed median was 0.009903 s. The deterministic regression ceiling is
  tightened from 120 to **24 queries**, with headroom for the inspected scope;
  wall-clock timing remains observational rather than a flaky assertion.
- Browser-script syntax and whitespace checks passed. No dependency changed.

Private diagnostic files are `/tmp/ossf-authored-financial-profile-{before,after}-20261001.log`
and `/tmp/ossf-assessment-prepare-{before,after}-*-20261001.prof`.
The first diagnostic run failed a newly added assertion that interpreted browser
transport closure as failed SDK consumption, despite completed reader bodies.
That assertion was removed; the final test retains successful-body/count/deadline
checks and the existing full workflow assertions. The failed diagnostic is not
counted as acceptance. The Python profiling entry point produced one pytest
assert-rewrite warning for already imported anyio; it did not skip a test.
The owned database/browser/Vite/HTTPS children stopped after both runs.
Baseline PostgreSQL and unrelated user services remain running.

### Remaining work

Hosted verification of this new auditor and diagnostic harness is pending.
`runtime_roles.py` is already part of the runtime code manifest. New code-bound
authority/release checks must use this version; historical receipts and releases
are preserved rather than rewritten.
The older six-part backend run remains independent. The 256-point break-even
verification still needs separate asynchronous admission/status/result reading,
current-rights checks and cancellation/retry/load evidence. This query change
does not implement that path or prove its throughput. Product CLI, independent
execution/release/full G1, real source/field/future comparison and G4 stay held.

### Subsequent HTTPS regression verification (2026-10-01)

The still-running backend run [36843547270](https://github.com/KIMSUNGHOON/OpenSmartFarmSim/actions/runs/36843547270)
at the older `93e30a7` revision reported partition 4 as failed: **252 passed,
1 failed in 1506.32 s**. The failed
`test_standard_https_admits_authored_pair_and_reads_persisted_cli_hold`
repeated the assessment POST after the stored hold and raised an actual TLS read
`TimeoutError`. This establishes a read timeout for that test; it does not recover
the original exception from the separate financial-browser failure.

With the all-role auditor from `6748355`, the unchanged focused HTTPS test passed
**1 case in 311.17 s** on local PostgreSQL 16.15. Its existing assertions require
all **10 complete responses below 30 s**, actual admission/idempotent reuse and
the persisted six-item hold. The CLI child and release keys remain synthetic.
No timeout, assertion or request scope was widened. Hosted PostgreSQL 18
verification of the new auditor is pending; other live partitions are not
restarted or canceled merely because this partition failed.
