# Server planning event and DecisionContext v1

Status: **software candidate**. [`planning_events.py`](../backend/app/planning_events.py)
supplies the event producer and public-key callback missing from the existing
[DecisionContext contract](thermal-g1-publisher-v1.md#trusted-inputs-and-review).
It does not approve a snapshot, release, source, forecast, ranking or deployment.
Actual G1/G4 still require separately controlled roles/keys and the remaining
execution/release evidence.

## Issue and persist

An operator installs a fresh `planning_events` table in a **separate schema**;
the closed runtime role policies and existing project tables are unchanged.
`PlanningEventStore` requires an explicit DSN/schema and trusted principal
provider. `PlanningAuthority` is provisioned with the planning authority ID and
an Ed25519 private key and requires a writer-bound store under
[planning-login-policy-v1](planning-login-policy-v1.md). Its `issue(tenant, snapshot_id, claim_mode=…,
decision_time_kind=…, hypothetical_at=…)` requires authenticated matching-tenant
`planning_event_issue`. Callers cannot supply raw event/context bytes, event ID,
authority, issuance time or a purported actual decision timestamp.

For `actual`, D equals the planning service's PostgreSQL `clock_timestamp()`
observation while processing the request. It is not a claimed browser click
time or a retrospective reconstruction. Supplying `hypothetical_at` is rejected.
For `hypothetical`, an explicit timezone-aware datetime is required and converted
to UTC; the event retains both this hypothetical D and the actual server
observation. This supports a labelled past/future scenario, without claiming
the sources were known at D or that the hypothetical event actually occurred.
`ex_ante` still requires the separate D-time source/vintage/right proof.

A fresh UUID context ID is generated for each issuance. A canonical
`planning-event-v1` binds tenant, snapshot, context, authority, D, kind, mode and
server observation. Its raw SHA-256 enters the unchanged `decision-context-v1`
envelope. A second database clock observation supplies `issued_at_utc`; Ed25519
signs `decision-context-v1` plus a zero byte and the exact canonical context.
The signature is lowercase hexadecimal, 128 characters.

One database transaction stores raw event/context bytes, both hashes, signature
and server-default `recorded_at`. Observed ≤ issued ≤ recorded is required;
clock reversal rolls back issuance, including a previously inserted row.
PostgreSQL checks raw hashes and size bounds, unique tenant/context and
tenant/event-hash identities; UPDATE/DELETE triggers preserve existing rows.
Issuance returns the raw context/signature only after commit. It does not retry
an uncertain commit or replace a previous context. Replaying a known context
uses its stored ID/bytes; a new issuance creates a new observed event.

## Independent read verification

`DecisionContextVerifier` receives only a pinned authority-to-public-key map and
a reader-bound store's exact `read_event` method, not a signing key.
Owner stores, wrong login profiles and arbitrary readers are rejected by default;
explicit `synthetic_smoke=True` enables software test doubles only.
`PlanningEventStore.read_event`
requires authenticated matching-tenant `planning_event_read` and returns no
foreign/unauthorized/unknown row. The verifier validates canonical closed
envelopes, Ed25519, exact stored context/signature/hash, raw event hash, the
tenant/context/snapshot/authority/D/kind/mode bindings and chronology. For an
actual event, D must equal the server observation. Missing, changed, noncanonical
or untrusted evidence returns `None`, preserving the existing context HOLD.
Success returns exactly the four fields required by the existing context reader.

[Planning RPC v1](planning-rpc-v1.md) supplies a bounded Unix-socket issuance
boundary for a separate key-holding process. Its client uses only the reader
login/public verifier and checks the durable event plus exact requested scope.
Issuance has no automatic retry or cross-store transaction guarantee.

The verifier connects directly to `ThermalRunStore.context_verifier`. The same
verified context can bind a signed Market hold; it neither creates a fake
MarketSnapshot nor clears `market_g0_not_evaluated`. The planning module is in
the publisher's closed code-hash inventory; changed code needs a new independent
release, and existing immutable manifests/releases are not rewritten.

## Verification and deployment limits

[Thirty-four focused cases](../backend/tests/test_planning_events.py) use real
PostgreSQL, a generated test Ed25519 key, stored event lookup after object
recreation, the existing thermal context store and Market hold. They cover
actual/hypothetical distinction, timestamp override, authorization/tenant
boundaries, changed signature/hash/record/clock/scope, valid-signature mismatches,
immutable rows, database hash constraints and transaction rollback.

The original contract tests explicitly share an owner credential and test key.
The separate login candidate now authenticates a scoped writer/reader pair,
audits every connection and denies timestamp insertion, mutation and DDL through
SQL grants. Its tests still share one OS UID and key control; they do not install
operating accounts or independently control signing outside this method.
A privileged owner can still alter the schema. Database tenant isolation,
independent private-key custody, clock operations and a product factory remain
unresolved. No real source/field/crop/economic evidence or G1/G4 acceptance follows.
