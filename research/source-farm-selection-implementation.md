# Source to farm reference selection implementation

Date: 2026-10-01. [Contract](../contracts/source-farm-selection-v1.md),
[task](../tasks/todo.md#지역-원천에서-농장-작성-연결-2026-10-01).

## Judgment and implementation

This work uses the existing development Codex CLI session
`01a0e064-b01b-7a22-8ef8-dd4afe0eb7dc`, verified as `gpt-6.1-sol` / `xhigh` in
the [model migration evidence](cli-model-migration-implementation.md).
The active project configuration remains that exact model/effort. No recursive
product CLI was launched and no new external source or numerical assumption
was adopted. Proposals and this implementation do not issue a claim gate.

The provider shares the exact owned research and collection services, authority
JobStore and immutable registry. It selects an exact pair of completed jobs,
checks the currently registered research scope and signed decision context,
verifies the collection record and its actual research parent, and compares the
collected original weather/thermal bytes against an already stored snapshot.
Two current reads must yield identical closed pins, with final scope/pointer
checks. It returns no source bytes, signature, credentials or agricultural and
economic numeric values. Signed context IDs retain the existing bounded
identifier contract; they are not required to resemble a SHA-256.

Selection keeps software-fixture/hold/not-accepted markers and requires farm
registration to check the references again. Read-only callers do not receive
write scopes, automatic snapshot staging, market hold creation or economic
defaults. The module joins the existing code digest, so release evidence for
older code does not silently authorize this new version.

## Verification

Focused command from `backend`, with `PYTHONPATH` unset, the existing local
PostgreSQL 16.15 administrator socket and registered PostgreSQL binaries:

```text
nice -n 10 .venv/bin/pytest -q -x --tb=short --durations=5 tests/test_source_farm_selection.py
```

Final core run: **4 passed in 19.81 s**. The first 18.90 s run checked the same
four cases; it is not four additional distinct tests. Tests use disposable
SCRAM databases and roles, synthetic source bytes, a fake executable and test
context signatures. They establish software contracts only.

- Missing snapshot produces a hold and no new job/snapshot/context. The existing
  explicit review submission stages the snapshot; selection then succeeds with
  only the five read scopes. Repeated reads preserve storage counts and pins.
- Exact research/collection hashes and snapshot hashes are returned. The closed
  response rejects a false recheck marker, accepted G1 or extra private fields.
  All five missing scopes are denied, and raw/secret/numerical fields are absent.
- Missing, foreign, reversed, mixed and unfinished jobs are rejected; string
  arguments do not substitute for the UUID interface. The original valid pair
  remains selectable after testing other intents.
- Stored snapshot byte mismatch, changed context time, late scope/verifier
  changes, a different second selection and private backend exceptions fail
  closed. Actual test artifact corruption between the two reads is rejected;
  restoring that test-owned record restores the valid selection.

Review covers exact ownership, completed parent lineage, original byte hashes,
current registered authority, closed output, no writes and late changes.
No database role, table, dependency, source coefficient or tariff changed.

## Remaining work

Authenticated HTTP/OpenAPI/runtime assembly, existing matching market hold and
economic candidate discovery, and the general region→farm web path follow this
provider. This core test is not HTTPS/browser evidence. Actual product model
execution, independent custody/release, complete G1 and G0/G2/G3a/G3b/G4 remain
held. No growth, harvest, purchased energy, future margin or crop ranking is
enabled. The entire backend suite and PostgreSQL 18 were not rerun locally.
