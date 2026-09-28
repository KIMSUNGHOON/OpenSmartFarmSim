# Conditional economic scenario HTTP registration v1

Status: implementation contract candidate; no farm profit, forecast, ranking or
gate acceptance. This connects existing user-assumption inputs to the existing
joint market scenario engine, without creating a calculation result.

`POST /v1/economic-scenarios` / registerEconomicScenario accepts a closed object
with required `request` (the existing MarketScenarioRequest) and
`idempotency_key` (the existing bounded ASCII identifier grammar). Request pins
the baseline and joint shock IDs/revisions/hashes, decision_at and unavailable
market context. Tenant is supplied only by the authenticated principal. The
existing 4096-byte JSON/UTF-8/duplicate/nonfinite bounds apply.
The [integration examples](../backend/tests/test_api_economic_scenario.py) build
the request from actual stored fixture pins and check the full response; these
are software examples using synthetic inputs and keys.

AND scopes: metadata, market_source_read, market_candidate_read,
market_candidate_write, decision_context_read, market_hold_context_read.
An exact actual JobStore, MarketCandidateStore and source/hold view must share
the audited authority policy/schema/DSN/principal. Source storage and market
calculation must be explicitly enabled. Custom read repositories do not enable
registration. No new credentials, grants, migration or numeric defaults exist.

The existing engine checks owned immutable baseline/shock inputs, matching
decision time and signed market hold, rights, inventory, settlement applicability
and contract caps. It produces the existing deterministic scenario and revised
numeric manifest. The actual collection intent stores the complete canonical
MarketScenarioRequest. Job/event, candidate and numeric rows are committed in
one transaction. Current scopes, bindings and prepared input content are checked
again before commit; failures roll back the whole admission.

`200` returns candidate_id, scenario_id, scenario_revision, scenario_sha256,
registration_status=pinned_user_assumption, first recorded_at and public
intent_job. No tenant, raw values, numeric output, rights manifest or synthetic
legacy reference is projected. The existing candidate's deterministic
immutable_job_input_ref remains its legacy scenario binding, distinct from the
actual intent UUID. The transaction pairs the intent and registration but does
not promote that legacy field to independent execution evidence.

Same key/request returns the original intent. Changed input under the same key
or conflicting candidate/numeric versions returns 409. Identical candidate bytes
under another intent preserve the first candidate/time. Initial admission leaves
the intent queued; retries project the current original job state without
requeuing. No CLI/lease, execution completion, economic result or Assessment is
fabricated. Subsequent economic work must replay the registered inputs and obey
the existing source, rights, clock, scope and gate contracts.

401/403 are fixed authorization errors; invalid input or an unsupported/
unresolved preparation is fixed 422; conflicts are 409; body/media bounds are
413/415. Missing service/internal binding errors and exceptions from trusted
source lookups use fixed 503, distinct from invalid request/pin mismatches.
Error responses never expose exception text or source values.

Software tests use synthetic inputs/keys with actual PostgreSQL authentication.
Actual CLI, independent source/rights/release/custody and full browser G1/G4,
G0/G2/G3 remain pending. New code requires a fresh independent release.
