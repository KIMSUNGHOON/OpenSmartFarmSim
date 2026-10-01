# Source-bound economic candidate selection implementation

Date: 2026-10-01 (Asia/Seoul). Development uses the ongoing exact
Codex CLI `gpt-6.1-sol` / `xhigh` session recorded in
[model migration evidence](cli-model-migration-implementation.md). No nested
product CLI invocation was launched. This is synthetic software evidence.

## Implemented provider

The [contract](../contracts/farm-economic-candidate-selection-v1.md) reads saved
economic pins, existing market hold references and evaluation dates for the
exact completed owned research/collection source. The actual shared authority
JobStore, collection registry, signed thermal context, market sources,
candidate store and hold scope/signing pointers are checked again on return.

Catalog metadata filters the owner, snapshot, signed context/hash, decision
time/kind and a Korea calendar that covers the weather interval. Its
`requires_current_selection` marker is deliberate: each metadata row does not
repeat the full economic ledger and rights review. Exact selection revalidates
the original source inputs, current individual rights, immutable hashes and
existing signed hold twice. It returns `requires_registration_recheck` and the
source's software-only/hold/G0/G1 markers. Registration rechecks everything.
No monetary value, crop output, raw input, signature or new approval is returned.

Database `recorded_at` values are explicitly converted to UTC for the closed
response/cursor contract. PostgreSQL can return the connection's local timezone;
the UTC validator remains strict and timestamp precision is preserved.

## Focused acceptance

One `nice -n 10` pytest process, `env -u PYTHONPATH`, Python 3.12 and disposable
PostgreSQL 16.15/SCRAM authority roles: **5 passed in 148.10 s** in
[test_farm_economic_candidate_selection.py](../backend/tests/test_farm_economic_candidate_selection.py).

- With only the eight read scopes, saved catalog/current selection succeeds,
  repeats exactly and leaves job, snapshot, context, hold and candidate/input
  counts unchanged. Each missing scope is rejected. The selected references
  then feed the actual FarmAuthoringService with explicit fixture farm/rights
  declarations, producing a queued `registered_unpublished_inputs` intent.
- Three genuinely registered candidate versions paginate without duplicates,
  including the exact timestamp/ID tie boundary. Invalid paired cursors,
  limits and naive datetimes are rejected. Current individual rights removal
  preserves metadata history but holds exact selection.
- Missing/foreign identifiers and late scope, rights, binding or private
  internal failure cannot return a selection or disclose the private detail.
- A separately signed context on the same snapshot, owner and decision time
  has its own genuinely registered and independently revalidated economic
  candidate. That candidate is excluded from this source's catalog and held
  on exact selection. Neither read creates records.
- Unbound service construction is rejected.

Earlier attempts exposed a fixture parameterization error, a UUID-object lease
argument, local-time response validation and a server-owned `tenant_id` left
in the user source body. They were corrected before the passing selection.
The UTC conversion is the provider correction; the other fixes are fixture
setup corrections. Diagnostic tracing printed only code location/exception
type and validation location/type, never input bodies or credentials.

## Remaining work

Authenticated candidate API and the farm web connection are next; the combined
task remains unchecked until its API acceptance exists. Hosted PostgreSQL 18
has not verified this provider yet. Fake CLI children and test signing keys
exercise contracts only. Actual new-model product execution, independent
release, full G1 and source/field/forecast/comparison/deployment gates remain held.
