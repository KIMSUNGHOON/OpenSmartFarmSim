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
