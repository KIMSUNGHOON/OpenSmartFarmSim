# Authored farm registration v1

Status: internal storage contract for `farm-authoring-storage` in the
[capability map](../CAPABILITIES-farm-authoring.md). The authored document and
numerical provider are defined by [farm inputs v1](farm-inputs-v1.md).

## Objective and owner

Register an explicit farm plan, its assumption-rights declaration and compiled
numerical inputs as one immutable tenant-owned intent. The authority-owned
`FarmAuthoringService` takes the existing exact `FarmReplayScenarioService` with
its actual SCRAM JobStore, thermal snapshot/DecisionContext, Market hold,
candidate source, ResearchRegistry and `OwnedResearchService`. It rejects an
assembly without the owned research authority. It introduces no independent
fake repository, new public claim, new scientific coefficient or G0 decision.

This module validates custody and current references. It **does not approve**
the authored parameters, release a new thermal snapshot, run a worker, publish
a Run, infer a crop profile or certify a user's rights assertion. Its input
remains `unpublished_candidate`; explicit `authored_input_review` and
`authored_snapshot_release` holds remain after registration. The existing
published thermal family is never given its artifact bytes.

## Input and immutable record

`FarmAuthoringRequest` is a closed `farm-authoring-request-v1` document containing `farm` (`FarmInputs`)
and `rights` (`FarmAssumptionRights`). Rights are an explicit user declaration
for that exact farm id/revision and its self-authored assumptions: `origin=user`,
`evidence_level=assumed`, ownership asserted, access/store/transform/use/display
allowed, redistribution denied, UTC availability no later than the decision,
and a dated scope covering the evaluation calendar. These fields grant no
rights to the owned weather template, NWS law, outside economic records, or
third-party source. A corrected assumption/rights declaration needs a new farm
revision. No personal farm or restricted raw record is put in the public DTO.

The service resolves the canonical research job under lock and validates its
hash-verified input against the current owned authority snapshot and protected
registry. The research location/goal and weather interval must match the
actual signed context, stored original snapshot, and authored plan. The Market
hold report must match the same context/decision. The actual pinned economic
candidate is revalidated through `MarketScenarioService.validate_pinned`,
including its current rights/settlement/source pins, then the farm's
batch/calendar scope is checked against the actual economic scenario. Candidate
status remains conditional and Assessment hold remains mandatory.

The server compiles against **stored** original manifest/weather/parameter bytes
at one recorded UTC review cutoff. The immutable JobStore input includes the
canonical farm request, rights, numerical candidate bytes (as JSON), their
hashes, actual source/context/research/candidate binding hashes, point and
pending spatial support. The existing 64 KiB canonical input bound applies to
the whole record. Stage `collection` stores intent only; the input version is
namespaced and is not a collection completion. No source/job/Run status is
silently upgraded.

The tenant and stage idempotency key derives from farm id and revision. Equal
submissions reuse the original job; changed bytes for the same version are a
conflict. A final commit guard repeats scopes, exact assembly, owned research
authority, source rights, context and economic candidate checks, and recompiles
the same bytes. Any drift rolls back the new job and submission event. Read
revalidates the stored bytes/hash and the current references; revoked current
access or source rights causes hold. Another tenant cannot read the record.

`submit(tenant, request)` and `get(tenant, id, revision)` return only version
ids, full stored-input hash, farm hash, numerical hash, declaration hash,
`registration_status=registered_unpublished_inputs`, and public intent status.
`read_registration(tenant, id, revision, expected_hash)` is a trusted internal
provider for the later worker. Its `user_rights_declaration` field remains the
user's assertion, never an independent approval. No public HTTP route is added
by this module.

## Verification

From `backend/` with an isolated SCRAM test DSN:

```bash
uv run --locked --group dev pytest -q tests/test_farm_authoring_storage.py
```

1. Real owned research/context/snapshot/Market hold and economic candidate,
   exact compiled values and rights declaration persist atomically. A new
   service reads the same immutable version; retry returns one job. Different
   bytes for the same version conflict.
2. Missing/foreign/replaced root, wrong point/period/context/market/candidate,
   denied/late/insufficient user rights, revoked current economic source or
   final scope loss produce no new job/event and no published Run/claim.
3. Current read rechecks references and scope. A forged constructed model,
   mutated stored payload or replaced service dependency cannot authorize the
   numeric candidate. Public summary contains no private coordinate, money,
   species, raw bytes or approved-source statement.

The next module still needs a separately reviewed authored snapshot and
release path before any Run can use these bytes. Product CLI and G1 remain open.
