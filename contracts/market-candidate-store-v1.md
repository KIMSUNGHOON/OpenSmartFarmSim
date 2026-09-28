# First-G1 market candidate pin store v1

Subsequent [HTTP registration](api-economic-scenario-v1.md) uses the actual durable
user-source store and signed hold/context view. The existing public pin method
shares its validation/SQL with `_pin_in_transaction`, allowing the trusted actual
JobStore transaction to include candidate/numeric rows and intent/event. Typed
denial/conflict errors remain ValueError subtypes, and write scope is rechecked
after insertion. The legacy deterministic scenario reference is not an actual
execution UUID; registration keeps it distinct from the queued intent.

Status: synthetic software storage candidate. `MarketScenarioService` remains limited to `MarketContext.kind=unavailable` and user-owned `origin=user`, `evidence_level=assumed` inputs. These records support conditional calculation with Assessment `hold`; they do not authorize a MarketSnapshot, a forecast, a verified farm price, or a crop ranking.

The subsequent [user-assumption source store v1](market-user-source-store-v1.md)
provides typed durable baseline/shock/input/rights/settlement/prior-cost readers,
with actual job bindings and optional authenticated v5. The earlier in-memory
source receipts below describe their original test scope; external sources and
their independent approval remain pending. The later storage candidate does not
make market-scenario accepted or authorize a MarketSnapshot.

`MarketCandidateStore` wraps a trusted source repository and an authenticated tenant principal. The source repository still supplies the baseline scenario and pin, joint shock and pin, input rights, market hold report, settlement applicability/evidence, and prior inventory cost. This store never accepts those authorities from an API request. Reads and writes require separate `market_candidate_read`/`market_candidate_write` scopes and agreement with the source repository's tenant authentication. The production source repository and its immutable evidence remain pending. The explicit [market runtime profile v3](runtime-market-login-policy-v3.md) adds authenticated authority grants and pre-query auditing; operating credential custody remains pending.

After `MarketScenarioService` has checked the baseline, shock, rights, market hold, settlement links, contract caps, and derived scenario, its server-generated `pin_market_candidate` call stores three canonical byte sequences in one PostgreSQL transaction: the candidate record, derived `EconomicScenario`, and a sorted manifest of newly revised numeric inputs. A second table stores those numeric input records by tenant, input ID, and revision. Content hashes, JSON identity checks, unique tenant keys, and UPDATE/DELETE rejecting triggers protect both tables. An identical retry is idempotent; a conflicting scenario or numeric revision rolls back the complete transaction. Candidate writes and reads also recompute the specified candidate ID, derived scenario ID, immutable job input reference, and scenario digest from the pinned request and manifest hashes; a forged digest-shaped ID is insufficient. Reads revalidate every manifest entry and numeric record. `calculate_pinned` then reloads the candidate and recomputes the full market and economic path. The market service canonicalizes its readback comparison so JSON serialization of UTC dates cannot create a false mismatch.

The [PostgreSQL tests](../backend/tests/test_market_candidate_store.py) cover a new store instance reading the same candidate, full market and economic recalculation, identical and concurrent retry, a conflicting numeric revision with no partial candidate, immutable rows, foreign tenant denial, and revoked read/source authentication. A [separate integration test](../backend/tests/test_market_signed_hold_integration.py) uses a synthetic signed DecisionContext and Market hold report through candidate pinning and replay. Baselines, shocks, rights and settlement evidence still come from a self-authored in-memory **source** repository and need durable trusted server storage; A [separate result store](../backend/app/market_result_store.py) now persists replay-checked result bytes and supports the implemented economic read API. This does not make the source repository durable or approved. Database owner permissions are not production role separation. `market-scenario` therefore stays unchecked.
