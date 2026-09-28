# Planning event implementation evidence

On 2026-09-28, the existing Codex CLI 0.157.1 session
`01a0e064-b01b-7a22-8ef8-dd4afe0eb7dc` implemented the
[planning event candidate](../contracts/planning-event-v1.md). The current local
turn context was inspected and records `gpt-6-sol`, effort `xhigh`. No nested
CLI, independent reviewer/model call, real source collection or farm record was
used. This is current-session implementation/review evidence, not an independent
release or a runtime model invocation.

The implementation keeps the existing canonical DecisionContext envelope and
public verifier callback. It supplies PostgreSQL-observed time, fresh context
identity, immutable event bytes/hash and Ed25519 binding. Explicit hypothetical
D remains distinct from the server observation. It leaves the closed runtime
role policy unchanged by requiring a separately provisioned schema; deployment
writer/read grants, key custody and product assembly remain missing. The new
module is included in the thermal publisher's closed source-byte inventory,
requiring new release evidence before adopting a changed implementation.

Local PostgreSQL 16.15 verification used the existing disposable test-schema
procedures and `uv run --locked --group dev pytest -q` for
`test_planning_events.py`, `test_thermal_publisher.py`,
`test_thermal_review_contract.py`, and `test_thermal_run_store.py`:
**63 passed**, including **34 planning cases**. The checks include durable
replay, the existing context reader, Market hold, signature/record binding,
actual/hypothetical time and clock-reversal transaction rollback. Test signing
keys and shared owner credentials do not prove independent role/key control.
The complete hosted suite is a separate required receipt. No actual CLI/G1,
G0/field/forecast/ranking evidence or deployment G4 is accepted by these checks.

## Authenticated planning grants follow-up — 2026-09-28

The same existing CLI session implemented and reviewed
[planning-login-policy-v1](../contracts/planning-login-policy-v1.md), without a
nested or additional model invocation. The local turn context again records
the exact `gpt-6-sol` / `xhigh` requirement. The writer and reader now use distinct
real SCRAM LOGIN roles and audit their effective privileges on every bound
connection. The default issuer/verifier require the respective bound stores;
the preceding owner/callback tests now explicitly opt into synthetic smoke.
The new grant module enters the publisher code digest; immutable manifests and
past releases remain unchanged, so adoption needs a new independent release.

The [PostgreSQL 18 privileges](https://www.postgresql.org/docs/18/ddl-priv.html)
and [libpq connection](https://www.postgresql.org/docs/18/libpq-connect.html)
documentation were consulted on 2026-09-28 for column INSERT/default and
`require_auth` semantics. No agricultural/economic source data was collected
or approved. Actual SQL behavior was checked against disposable PostgreSQL
16.15 with self-authored test credentials in private temporary passfiles.

Focused planning/previous-event/authenticated-connector/publisher checks:
**108 passed in 39.10 s**. After adding CONNECT/USAGE grant-option drift rejection,
the final planning grant suite passed **35 cases in 4.61 s**. It covers real
writer issuance and reader verification, existing immutable snapshot/context
integration, timestamp insertion, mutation/role escalation with the session's
read-only setting disabled, eleven catalog drift cases, five default-source
guards, reinstall refusal and transactional provisioning rollback.

These credentials and keys share one OS UID; the context storage integration
still uses a test owner. Application tenant checks are not database row
isolation. No operating key custody, product factory, actual runtime CLI,
independent release or G1/G4 claim was demonstrated. The preceding core's
[hosted backend receipt](https://github.com/KIMSUNGHOON/OpenSmartFarmSim/actions/runs/36388752655)
recorded 1264 ordinary tests and three distinct-UID smoke cases; that receipt
does not cover this follow-up. Its new hosted receipt must be checked separately.

The authenticated-login follow-up's exact commit `21550a5` subsequently passed
[backend CI](https://github.com/KIMSUNGHOON/OpenSmartFarmSim/actions/runs/36391103128):
**1299 ordinary tests, 2 warnings**, three distinct-UID service smoke cases and
the content DAC check. Its
[Compose receipt](https://github.com/KIMSUNGHOON/OpenSmartFarmSim/actions/runs/36391103107)
also passed. These receipts do not cover the later RPC candidate below.

## Separate planning issuance RPC — 2026-09-28

The same exact CLI model/effort implemented and reviewed
[planning-rpc-v1](../contracts/planning-rpc-v1.md), using the existing bounded
Linux IPC and authenticated planning profiles. No additional/nested Codex call
or real source collection was used. The server requires a writer-bound planning
authority, fixed tenant/OS peer, protected socket directory and trusted matching
snapshot resolver. The client requires the exact reader-bound verifier and
checks signed durable context bytes against its original request.

The first local suite passed **26 cases in 10.28 s**. After rejecting an
owner-backed smoke verifier and adding live writer-grant drift rejection,
the final RPC/login/publisher/review suite passed **79 cases in 22.49 s**,
including **28 RPC cases**. A fresh spawned Python process issued a context
against a real immutable fixture snapshot; the public reader verified it,
the existing context store persisted it, and JobStore queued the exact
collection review input with its existing intent replay behavior.

Checks cover actual/historical hypothetical requests, unknown/foreign snapshot,
both peer directions, ten malformed wire cases, seven changed reply/signed
scope cases, fixed error output, socket permissions/SIGTERM/preservation,
default owner rejection and privilege drift after listening. An injected lost
success reply left exactly one committed/verifiable event and an unresolved
client result, without retry. Issuance and downstream writes remain separate
transactions; no HTTP intent recovery or automatic safe retry is claimed.

The tests share OS identity, controller credentials and test keys. The spawned
process test is not independent operating custody or an actual runtime model
invocation. Operator service factories, deployment identities/keys, independent
clock/schema/tenant controls, actual CLI execution, release and G1/G4 remain
pending. The module enters the code digest and requires a new independent
release; immutable source manifests and older releases were preserved. This
follow-up's hosted receipt must be verified separately.
