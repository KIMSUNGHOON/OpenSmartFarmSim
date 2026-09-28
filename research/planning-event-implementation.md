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
