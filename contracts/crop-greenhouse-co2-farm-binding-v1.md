# CO₂/Solar current farm binding v1

Status: accepted for synthetic software binding,10 actual SCRAM groups on2026-10-21 KST.
Prerequisites: accepted [CO₂ input evidence](crop-greenhouse-co2-input-evidence-v1.md),
[CO₂ files/UTC](crop-greenhouse-co2-storage-v1.md) and existing registered farms.
Reuse the [Solar farm contract](crop-greenhouse-solar-farm-binding-v1.md) and its
current registered farm/rights service with distinct CO₂ types and versions.
No equations, profiles, old farm bindings, result schemas or services change.

## Boundary and identity

`Co2FarmBinding(farms, input_authority, input_rights=...)` requires exact existing
FarmAuthoringService, exact Co2InputEvidenceAuthority and a current versioned rights
resolver. Authority SCRAM login, complete grant audit, explicit result-storage
permission and current read/write scopes remain mandatory. Server supplies paths,
keys and evidence; request cannot select paths. `prepare` and `current` signatures
and closed request keys follow the Solar contract, each canonical request/result
bounded to128KiB. `current` requires equality to trusted original binding bytes.

Source schema is `joint-co2-solar-input-source-v1`, rights schema
`joint-co2-solar-input-rights-v1`, binding version `joint-co2-solar-farm-binding-v1`.
Require exact VerifiedCo2InputEvidence with no gate approval, current source/context/
UTC/evidence/initial-state identities, complete provenance and SHA, current review,
109-state/44-ledger model/profile/code identity and journal v2. Older Solar/ventilation/
joint/cycle authorities, source/right/binding types cannot be mixed.

Return scope `synthetic_joint_co2_solar_math_only`, `G0_G4=not_assessed`,
`rights_or_gate_approval=False`, and profile applicability
`unvalidated_for_registered_crop`. Registered farm/zone/area/crop/batch bindings
do not make the reference profile valid for that cultivar or create field evidence.

## Currentness and time

Keep existing registration job/revision/hash and source-binding checks, original
microsecond UTC inside both crop occupancy and KST inclusive cultivation dates,
and source provenance/rights declaration each `available_at<=farm.decision_at`.
Retrieval is separate from availability. Current rights callback requires exact
True for research_calculation/research_display on write and research_display on
read; declaration grants/redistribution remain as defined in the Solar contract.
No registered data, calculation Run or crop result is created by prepare/current.

Recheck scopes/configuration, rights and raw evidence/current review/registration
before return. Callback mutation, late withdrawal, source/DB/grant changes hold.
This is repeated current validation, not an atomic snapshot across independent
stores; signed custody must check again around calculation and publication.

## Acceptance before execution

- Actual SCRAM production registration/prepare/current/read/write; original request,
  provenance/model/profile/source/UTC/review/initial identity, farm/crop/batch/zone/
  floor area and unvalidated applicability retained. New Run/result counts stay0.
- Fresh exec reconstructs services from private owned scratch credentials and
  returns identical binding; current review revocation rejects. No physical RHS,
  optical/gas/net/air calculation, context/UTC setup, advance/management/restore or
  CLI during prepare/current/fresh. Synthetic fixtures prove software contracts.
- Reject mixed old types, other tenant/crop/farm/revision, source/context/UTC/evidence,
  malformed/noncanonical/oversize request/expected bytes, non-True rights and changed
  authority/providers/policy/code. Actual scratch DB corruption/grants reject and
  restore to the original bytes; late callbacks cannot introduce new rows.
- UTC outside crop period and authenticated end1µs beyond occupancy reject. Source
  availability before/exactly at decision accepted,1µs after rejected; apply the same
  boundary to declared rights. No rounding of source timestamps.
- Preserve original results/files/five roots/frozen previews,512MiB per process and
  combined1GiB, FD cleanup and all owned PG/schema/roles/passfiles. Full CI/browser/
  field/G0–G4/new deployment are separate. Next is signed CO₂ custody→DB/API/UTC3D.

## Observed acceptance

[Machine evidence](../research/artifacts/crop-greenhouse-co2-farm-binding-20261021.json)
records exact tested source/contract pins, native CLI review, sanitized owned
results and the initial test-helper import failure. The final same-source10
groups passed in133.77s pytest/140.3021s guarded wall. Both normal and maximum
distinct512 forcing/128 events/512 outputs bind in34,687bytes under128KiB;
maximum source850,874/evidence1,038,344bytes retain original input caps.

Actual production registration and SCRAM prepare/current/read/write match farm/
crop/batch/zone/area, provenance/initial/model/UTC and exact fresh bytes. All17
physical/context/time/restore/CLI entrypoints remain0. Jobs/events stay88/88 and
crop/thermal result rows0/0 in the normal fixture; every failure group checks no
new rows. Actual scratch registration corruption/grants reject and restore to
the original binding. Source and declaration availability before/exact decision
accept;1µs after and authenticated end1µs outside occupancy reject.

Combined peak823,685,120bytes/single156,438,528bytes,FD4→4 and five original roots/
2148 entries/frozen previews are preserved. Owned processes, PG directories,
schemas, roles and passfiles are0 after cleanup. Original equations/profiles and
old binding/registration services stay unchanged. Full CI/browser/field/new model
deployment were not run; actual rights/cultivar validity/G0–G4 stay held.
