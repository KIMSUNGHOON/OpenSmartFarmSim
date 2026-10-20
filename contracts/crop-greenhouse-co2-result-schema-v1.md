# CO₂/Solar result DB schema v1

Status: accepted for synthetic SQL software contracts,8 focused checks on2026-10-21 KST.
Prerequisites: accepted [CO₂ custody](crop-greenhouse-co2-server-custody-v1.md),
[CO₂ immutable files](crop-greenhouse-co2-storage-v1.md) and existing jobs. The
[Solar DB contract](crop-greenhouse-solar-result-schema-v1.md) applies to this
distinct model family, with the following exact new identities.

| Item | Value |
| --- | --- |
| Installer | `install_joint_co2_solar_result_schema(conn,schema)` |
| Table | `crop_greenhouse_co2_research_results` |
| Result schema/ID prefix | `joint-co2-solar-result-v1` |
| Artifact reference prefix | `joint-co2-solar-storage-research-v1` |
| Progress version | `joint-co2-solar-server-custody-v1` |
| Claim/progress scope | `synthetic_joint_co2_solar_math_only` |

## Original bytes and relational checks

Keep separate payload_raw/progress_raw UTF-8 bytea1..131,072bytes each and exact
SHA256, including intentional whitespace. Require JSON objects with unique keys
recursively, including escaped aliases. Metadata's closed top/farm/input/artifact
objects and progress's26 keys match the Solar contract. Every linked hash/string/
counter is checked against its column with original numeric spelling: integer
JSON only, not float/exponent/bool/string/null. IDs/SHA/ref, scalar/container types
and fixed stored_unpublished_research/not_assessed/false claim values are explicit.
The context and custody code SHA columns preserve the CO₂ family identity.

Bounds remain steps0..4096/planned1..4096, sample0..512/event0..128, commit1..4097,
storage1..536,870,912bytes/files1..65,536. Completed steps equal planned; hold may
stop earlier. Original UTC strings have exactly6 fractional digits, valid calendar
and0<end-start<=600s. Planned interval end is separate from hold confirmation time.

Keep PK tenant/study/revision, unique tenant/result and tenant/intent, tenant/job
FK, DB recorded_at and UPDATE/DELETE rejection. Installer is transactional and
fresh-only; reinstall/partial-install conflict fails and rolls back. Revoke PUBLIC
table/routine access. No new runtime grants, default install hook, model/profile
change or result registration/current query is introduced here.

These constraints do not verify full model/profile/state/ledger/unit/UTC-array
semantics, canonical JSON, result content identity, HMAC or current farm/source
rights. Trusted store/query must validate those later. Fixture metadata and hash
agreement do not approve source rights, cultivar applicability or G0–G4.

## Acceptance before implementation

- Actual SCRAM provisioner installs and roundtrips both original bytea at exact
 128KiB and every column/recorded_at; default4 runtime roles deny20 operations.
- Retain original4 cycle/verified-cycle/ventilation/Solar result tables and rows;
  no implicit grants or old table/trigger changes. Actual cleanup confirms owned
  scratch PG/schema/roles/passfiles and original files/five roots/frozen previews.
- Rehashed malformed/mixed-old metadata/progress, every relational pin, raw hash,
  duplicate/escaped JSON keys, types/integer spellings, bounds and UTC reject.
  Exact bounds/600s accept;1µs beyond rejects. Test FK/uniqueness/hold, immutable
  UPDATE/DELETE, reinstall and partial-install rollback against real DB.
- [Captured original CO₂ progress](../fixtures/synthetic-co2-solar-custody-progress-v1.json)
  from accepted9e93cac is canonical serialization of saved final/fresh-equal actual
  synthetic32s output, matching recorded38,513byte wire length, selected HEAD and
  direct checkpoint. Preserve exact38513bytes/SHA without recomputation or a new
  signature. SQL roundtrip must retain both wire/metadata bytes and UTC.
- Schema tests forbid physical/context/UTC/restore/CLI entrypoints; source/fixture
  capture does no model run. Preserve512MiB/PID, combined1GiB,600s, FD and cleanup.
  No full CI/browser/field/new deployment/G0–G4 claim. Next is explicit result
  grants then signed registration/current query→API/worker→same UTC3D.

## Observed acceptance

[Machine evidence](../research/artifacts/crop-greenhouse-co2-result-schema-20261021.json)
records native CLI review and exact current code/test/fixture pins. Final8 checks
passed in6.71s pytest/7.6103s guarded wall. Both raw fields roundtrip exact131,072
bytes with41 supplied columns and DB recorded_at;4 runtime roles deny20 operations.
Seven DB fixtures preserve one original row in each of cycle/verified-cycle/
ventilation/Solar tables. Physical/context/time/restore/CLI17 entrypoints stay0.

114 column-boundary,95 rehashed metadata and74 rehashed progress cases reject;
34 metadata/19 progress column pins are covered. FK/unique/update/delete/reinstall/
partial-install rollback and exact bounds/600s are checked. Independently reused
old Solar schema/scope/progress version values reject after matching other columns
and recomputing raw hashes. The actual captured CO₂ progress roundtrips38,513bytes,
SHA a324a21ff78ea2fe1f1b7b5fe65e1b34cbc9171a723b0aa7046367045aa553e6.

The first preparation incorrectly treated proof-list order as selection order;
selecting the signed finalize action/sequence3 fixed capture before any fixture
was written. No model, original value or prior evidence changed. RED then checked
the absent new module; initial7 checks passed and independent old-Solar boundary
coverage brought the final count to8. Original2148 entries/five roots/frozen
previews, FD4→4 and cleanup are preserved. Final combined735,764,480/single
113,844,224bytes stay within original limits; scratch schemas/roles/passfiles0.
Runtime grants/registration/current rights/API/worker/3D and field gates remain
unaccepted. Next is explicit CO₂ result permissions and existing-config fences.
