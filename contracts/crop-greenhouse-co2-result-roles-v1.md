# CO₂ result opt-in permissions v1

Status: accepted synthetic software permissions contract (2026-10-21 KST). Prerequisite: [CO₂ result schema](crop-greenhouse-co2-result-schema-v1.md).
Reuse the [Solar permission boundary](crop-greenhouse-solar-result-roles-v1.md)
with the current configuration inventory below. Runtime grants do not prove
tenant isolation, signatures/current farm rights, cultivar applicability or G0–G4.

## Explicit current policy

RuntimeLoginPolicy adds keyword-only exact bool `crop_greenhouse_co2_result_storage`,
defaultFalse. Omitted/False grants no new table access; only explicitTrue adds
`crop_greenhouse_co2_research_results` to authority SELECT/INSERT. Request/worker/
supervisor remain denied; UPDATE/DELETE/TRUNCATE/REFERENCES/TRIGGER, MAINTAIN where
supported, grant-option/schema CREATE/routine execute/membership remain denied.
None,0/1,float,string,container/bytes are rejected, never coerced to bool.

Provisioner installs the schema before fresh runtime roles. Keep all existing role
and full effective-grant audits. Missing table/required grant, unexpected table/
column/PUBLIC/routine/grant-option/membership and reinstall fail. Existing5 cycle/
verified-cycle/joint/ventilation/Solar table grants and rows must remain intact.
No existing live-role migration is implied by a fresh scratch-role installation.

## Current configuration inventory and implementation boundary

| Existing loader module | Config versions |
| --- | --- |
| operator_config | basic1 |
| calculation_operator_config | calculation1 |
| crop_climate_joint_operator_config | read/execution/prefix3 |
| crop_greenhouse_ventilation_operator_config | read/execution/prefix/mixed4 |
| crop_greenhouse_solar_operator_config | read/execution/prefix3 |

All12 retain missing/False compatibility and reject True/nonbool before importing
or calling dependency factories. Also test existing Solar opt-in True separately
from the new flag. ApiRuntimeConfig directly rejects new CO₂ True before I/O;
there is no CO₂ API assembly here. Keep explicit per-loader checks in their
existing policy validation; generic JSON/object/file helpers do not gain policy.
Production scope: runtime_roles, the five loaders and api_runtime; short field/
table/false checks, no new orchestration layer. This completes one policy change
across its actual entry points; unrelated config or services are untouched.

## Versioned evidence and acceptance

Common role/operator/API code changes create new dependency/signature identities.
Retain original signed receipts/farm bindings/intents/results and frozen services
at their original code version. Do not adopt, overwrite or re-sign old records.
Issue new test inputs/farm/custody from the current source and verify actual fresh
bytes/checkpoint/UTC and zero read calculations after the shared change.

- Actual SCRAM omitted/False/True matrix, all effective privileges and real SQL,
  exact metadata/progress/UTC, existing5 table grants/rows preserved, missing table/
  fresh atomic install/reinstall and late privilege drift rejected.
- Current12 versions plus existing Solar True variants: missing/False accepted,
  True/nonbool rejected before factories; direct API config rejects new True
  before JobStore/I/O. Exact bool policy and FD behavior checked.
- Focused common role/login and existing config/API/model regressions, then actual
  CO₂ farm/custody fresh/selected checkpoint/UTC/read0; prior captured immutable
  progress remains an old-version SQL fixture, not current authenticated evidence.
- Preserve original2148 entries/five roots/frozen previews and512MiB/PID/combined
  1GiB/600s, FD and owned process/PG/schema/role/passfile cleanup. No whole CI/
  browser/new deployment/field/G0–G4 claim. Next is signed result registration/
  current query, then API/worker/same UTC3D/user acceptance.


## Acceptance evidence — 2026-10-21 KST

[Machine evidence](../research/artifacts/crop-greenhouse-co2-result-roles-20261021.json):
9 new actual-SCRAM tests (6.93s), 363 common role/login/config/API regressions
(81.57s) and 2 current-code farm/custody fresh-process regressions (56.35s).
There are 374 distinct accepted tests. The common group used an owned disposable
PostgreSQL endpoint and guarded main entry. Its earlier teardown failure exposed
2 fake invalid login passfiles; that test now removes its own files in finally.
No rejection assertion, test selection, timeout or resource bound was relaxed.

Each omitted/False/True matrix checked 168 effective table privileges; allowed/
denied SQL was 0/20, 0/20, 2/18 with 6 escalation denials per mode. Fourteen drift
mutations and two False-policy unexpected grants were rejected. Existing five
result tables retained their rows/grants. Fifteen config contexts (12 versions
and 3 existing Solar-True contexts) accepted 30 missing/False combinations and
rejected 105 True/nonbool combinations before factories; direct API True failed
before I/O. FD remained stable.

Fresh farm verification called none of 17 numerical/context/time/CLI entry points.
Current custody resumed 16 remaining intervals/2 events, matching original rows,
UTC and checkpoint; read/page/terminal retry performed no calculations. Existing
signed epochs and the schema fixture were preserved. The largest accepted guard
peak was 1,002,635,264 bytes combined, below the original 1GiB; all five service
roots, original 2,148 entries and owned process/PG/file cleanup were preserved.
Full CI/browser/new deployment and G0–G4 were not assessed in this increment.
