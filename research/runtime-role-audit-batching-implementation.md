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
