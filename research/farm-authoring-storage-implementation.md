# Authored farm registration implementation

Date: 2026-09-30 KST. Status: internal custody candidate under
[farm-authoring-storage](../CAPABILITIES-farm-authoring.md), following the
[registration contract](../contracts/farm-authoring-storage-v1.md). The broader
module still needs an independently reviewed authored snapshot/release and its
execution binding. Product CLI, complete G1 and G0/G2/G3/G4 remain open.

## Development boundary

The development Codex CLI `turn_context` at `2026-09-29T16:47:44.857Z` in
`rollout-2026-09-27T10-04-50-01a0e064-b01b-7a22-8ef8-dd4afe0eb7dc.jsonl`
recorded exact model `gpt-6-sol` and effort `xhigh`. No recursive CLI was run.
The module neither invokes a runtime product CLI nor supplies source/crop,
price, coefficient or tariff judgments. Its synthetic rights declarations are
not independent evidence of ownership or a G0 pass.

The service requires the actual `FarmReplayScenarioService` and its installed
`OwnedResearchService`. It resolves the stored owner/root/context/market hold,
the original hash-pinned snapshot and the currently revalidated economic
candidate. It validates the authored farm against the actual economic scenario,
compiles from the stored source bytes, and records one canonical immutable
JobStore intent with numeric bytes/hash, rights declaration/hash, root/registry/
context/candidate bindings, point and pending spatial support. The request is
replayed under current scopes and sources before commit and on every read.

Rights require a user's explicit self-authored assertion with access/store/
transform/use/display and no redistribution. The corresponding weather/law
and economic source rights remain with their own authorities. The input stays
`unpublished_candidate`, with `authored_input_review` and
`authored_snapshot_release` missing. The currently accepted thermal publisher
never receives this numeric artifact. Corrections use a new farm revision.

No new table, grant, package, public HTTP endpoint, registered worker,
approved source or calculation/replay claim was added. The existing collection
stage row is an authoring intent, not a collection result. Only an owner with
the existing read/write scopes can register or reread the internal record.

## Focused verification

The RED run stopped at import because `app.farm_authoring_storage` did not
exist. The first integration attempt exposed a test-fixture discovery issue:
the new test file had to import both the existing `login_scope` and its parent
`login_database` fixtures. After that harness correction:

- Actual isolated SCRAM/PostgreSQL registration, a new service instance's
  read, exact retry, conflicting bytes, a new revision, no publication and a
  private-field-free summary passed **1 in 61.10 s**.
- Missing/altered snapshot, decision context, root, candidate and inadequate
  user rights did not create jobs/events. A valid legacy research row without
  the owned authority binding was also rejected.
- Revoked write scope during the admission/commit path rolled back the job and
  event. A forged returned stored-input byte, replaced owned authority and
  revoked current economic input rights each blocked reads of the registered
  version; no Run was published. The latter two cases passed **2 in 66.69 s**
  after those extra adversarial checks were added.

An internal return key was then clarified to `user_rights_declaration` so a
later worker cannot mistake the assertion for approved source rights. The
affected owned registration/read path passed again: **1 in 56.21 s**. The
application's storage and validation logic did not change in this final edit.

These three focused cases use test-owned source/context/market signatures and
roles. They establish storage and current-reference software behavior only.
No actual product CLI invocation, independent source/parameter review, new
snapshot release, full farm execution/Assessment, browser authoring or
production operating check was run for this increment.

## Next dependency

Define and implement an authored snapshot provenance/review/release contract
that can carry these numeric bytes through the trusted thermal worker while
keeping the original fixture family and publisher pins intact. Then bind the
stored authored version to economic execution and held Assessment before the
complete farm and ledger web authoring flow. The existing G1 and later gate
checks remain open.
