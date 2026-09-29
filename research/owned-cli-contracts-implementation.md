# Shared owned CLI contract assembly

Status: focused software verification passed; not full G1/G4 acceptance.

## Decision evidence

The developer session's actual latest turn context at
2026-09-29T07:20:20.800Z records model `gpt-6-sol`, effort `xhigh`, thread
`01a0e064-b01b-7a22-8ef8-dd4afe0eb7dc`. The already running CLI session made this
architecture judgment; no recursive CLI invocation was launched. Developer
session evidence is not a product invocation or independent release.

The preceding APIs submit three different input contracts. The existing general
router can dispatch them, but protected operator composition still needs to
connect the actual owned services and reject a mixed store/registry assembly.
The new [contract](../contracts/owned-cli-contracts-v1.md) does that using their
existing validators. It supplies no new agricultural coefficients, monetary
rules, source approvals, gate decisions or database grants.

## Verification

The first focused check failed during collection because the assembly module
was not implemented: one ModuleNotFoundError in 0.11 s. A subsequent collection
error exposed an incorrectly applied test profile marker; the marker is now
limited to integration functions that use the login fixture.

The first actual PostgreSQL run completed **4 passed in 425.39s (0:07:05)**,
with no warnings/skips. One shared CliWorker processed actual stored owned
research, deterministic collection and owned review, then kept the separately
completed calculation assessment on hold. Stored validation reports retained
each delegate's original version; an unregistered legacy assessment input
created no model invocation.

Review added different-job/different-run constructor probes and mutation during
authority resolution to the existing binding case. A second locked PostgreSQL
run used test_owned_cli_contracts.py, test_cli_contract_router.py and
test_thermal_publisher.py, excluding the unchanged complete-route case:
**32 passed, 1 deselected in 121.02s (0:02:01)**, no warnings/skips. Three cases
overlap the first run; together these checks cover **33 distinct tests**, not 36.
The changed binding case verifies rejection before delegation and after an
authority callback changes the context verifier, including final validation.

Review checked actual service/store/registry cohesion, current scope checks,
immutable route registration, pre/post binding guards, preserved delegate
versions/holds, no fallback, code-digest coverage and bounded errors. It found
no remaining issue in this slice. The composition guard performs no SQL or
model work; calculation and source-replay behavior remain in existing services.
uv lock --check passed (31 packages); Python compile checks, local links and
staged whitespace checks passed. No local full suite, distinct-UID, browser,
actual model or real-provider request was run for this change. Hosted checks
must cover its exact functional head; earlier CI receipts cover earlier heads.

## Remaining scope

The synthetic fixture completes heat and economic parent calculations before
the shared-route probe. The probe connects owned research to collection/review,
and separately assesses those completed parents; it does not make the new review
the independent authorization for the fixture's preexisting thermal Run. All
keys, review callbacks and model outputs in this probe are synthetic. Actual
product CLI and independent planning/isolation/custody/release, full farm and
economic scenario orchestration, browser/3D, G1 acceptance and later source,
field, future/comparison and operational gates remain unproved. Broad task
checkboxes remain unchanged.
