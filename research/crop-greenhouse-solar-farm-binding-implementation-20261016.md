# Solar farm/current source rights acceptance — 2026-10-16

Accepted [contract](../contracts/crop-greenhouse-solar-farm-binding-v1.md),
[implementation](../backend/app/crop_greenhouse_solar_farm_binding.py),
[tests](../backend/tests/test_crop_greenhouse_solar_farm_binding.py) and
[machine evidence](artifacts/crop-greenhouse-solar-farm-binding-implementation-20261016.json).
The new version binds authenticated solar inputs to an existing registered farm
and current research permissions. Old models, profiles, keys, result IDs and
deployed services are preserved. Goal remains **active**.

## Scope and evidence

Native parent Codex CLI **gpt-6.1-sol/xhigh**, context2026-10-16T12:47:56.834Z,
performed the design and acceptance review; raw context and actual design/output
hashes are recorded. No recursive CLI, external data adoption, new agricultural
coefficient or physics/money equation was used.

The binding preserves complete authenticated SourceRecord provenance and its
canonical hash, source/context/UTC/evidence/initial-state identity, registered
tenant/farm revision/crop/batch/zone/area/occupancy and registered decision time.
Both source and declared-rights availability must precede or equal that decision.
Later retrieval is represented separately. A source available one microsecond
after the decision and a run ending one microsecond outside occupancy reject.
Synthetic future forcing remains an authored assumption, not future observation.

Current source rights are checked twice, with input/review/registration/scope
rechecks before returning exact immutable binding bytes. This observes current
permissions across separate stores; it is not one global atomic snapshot.
Profile applicability stays `unvalidated_for_registered_crop`,
`rights_or_gate_approval=False`, G0–G4 `not_assessed` and actual farm Runs0.

## Verification

- Original29574:0: **8 new actual SCRAM test groups**,114.66s pytest /
  127.881s guard. Original51546:0: **5 existing ventilation farm-binding tests**
  in a separate guard,78.752s. Total **13 distinct passed**. The existing
  ventilation fresh-exec case was explicitly deselected; new solar fresh exec
  passed. Old input/provenance/UTC suites and full CI were not rerun.
- Normal prepare/current/read/write and a separate fresh Python exec return the
  same 33,113-byte binding. Input verification twice and current rights twice
  are checked. Fresh SCRAM authentication and current review revocation pass.
  All13 numerical/context/UTC/restore/CLI sentinels remain0; job/event counts
  are unchanged and crop-result/Run rows0.
- Closed requests, old source/rights/authority versions, foreign tenant/crop/
  period/registration/source/context/UTC/evidence, current scope/source/review/
  rights revocation, late callback changes and fixed configuration changes reject.
- The database's immutable trigger rejects updates, and its digest constraint
  rejects bytes-only changes. Only the owned scratch fixture administrator
  bypasses the trigger transactionally to inject changed bytes with a matching
  new digest. Current farm binding still rejects that changed registration.
  An actual unexpected DELETE grant rejects; restored data/grants recover the
  identical original binding. No deployed database is used for this injection.
- Final new/regression guards preserve five live roots and dynamic descendants,
  2,148 original entries, frozen sources/assets and HTTP5173. FD4→4, owned
  processes/PG/temp PG directories/passfiles0 and scratch schemas/roles0 pass.
  New peak137,015,296bytes/PID /1,054,896,128bytes combined; regression peak
  143,089,664 /1,061,404,672. Nominal0.25s sampling keeps512MiB/PID and1GiB
  combined limits. User API/worker/services, auth/config/routes and keys were
  not restarted or changed. Edits did not overlap pending focused guards.

Four early fresh-exec guards exceeded combined RSS and stopped only owned tests.
The lean fixture now constructs production services without importing a complete
HTTP app; fresh exec imports production modules directly. Supported scratch PG
shared_buffers16MiB, single numeric thread and released unused Python allocations
keep the same resource caps. An earlier4MiB assignment was overridden by the
existing pytest16MiB setting;16MiB is the actual verified fixture value. A fixture datetime serialization error was fixed
using the existing typed market serializer. The first7/8 test batch exposed the
database's immutable trigger; a later injection exposed its digest constraint.
The final test verifies both protections and the current reader after rehashing.

One private peak log raced with an exiting process's comm label. Its RSS remains
counted, while a missing label is now marked exited. The interrupted scratch PG
was confirmed dead and its four exact owned passfiles removed. Final cleanup0
and original failure hashes are recorded. These failures were not accepted or
removed from the evidence.

## Visible result and next acceptance

The localhost5173/5174 development feed reports this acceptance; current HTTP
publication proof, original34007:0, confirms both200/`no-store`/byte-identical
at2026-10-16 22:10:12KST, SHA
`7f6dad86b2a7a9a18faa9abf285d1123f951315d350fedc026d406f0aeaf1fe8`.
Both frozen HTML entries and2,173 frozen ventilation source files remain equal. Existing simulation
continues on the previously accepted ventilation version. **New solar binding
is not deployed to user API/3D.** Browser DOM/WebGL was not rerun for this data
record update.

Next slice: **signed solar server custody**, using this exact binding/input
authority and existing immutable solar storage. Acceptance requires separately
versioned intent/HEAD/HMAC domains; original108state/41continuous and6event
ledgers/15balances/UTC; normal and held bounded execution; current source/farm/
rights checks before and after calculation and publication; tamper/conflict/lock
rejection; fresh restart from the selected checkpoint without replaying committed
steps/events; read/terminal retry computation0; and preserved original files,
services, owned cleanup and WSL caps. Database result registration/current query,
API/automatic worker, same UTC3D and user normal/hold/cancel/reconnect/restart
acceptance follow as separate increments.

Actual local/future cultivar/farm/optics/facility/spectrum and market evidence
remain external dependencies; none was acquired in this software slice. G0–G4,
whole-season accuracy, real production, purchased energy, future margins/ranking
and final product UI remain unaccepted. Full product date and remaining focused
hours remain unknown until those evidence and integration dependencies resolve.
