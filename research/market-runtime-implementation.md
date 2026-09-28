# Authenticated market persistence implementation

Status: software authentication/replay candidate; no production or G1/G4 acceptance.

## Decision provenance

The active Codex CLI thread `01a0e064-b01b-7a22-8ef8-dd4afe0eb7dc`
performed this architecture judgment and implementation. Its selectively read
`turn_context` at `2026-09-28T10:49:43.721Z` records exact model `gpt-6-sol`
and effort `xhigh`. No recursive CLI or additional model invocation was made.
The reviewable output is this change, its [v3 contract](../contracts/runtime-market-login-policy-v3.md)
and the test receipt below; it is not approval of source data, a release or a gate.

The existing [v2 login contract](../contracts/runtime-login-policy-v2.md) and
verified SCRAM/effective-grant audit are reused. No external agricultural data,
economic coefficients, tariff, dependency or production credential was adopted.

## Implemented boundary

An explicit keyword-only exact-boolean option adds three existing immutable
market calculation tables to fresh authority SELECT/INSERT grants. The default
v2 matrix/version and v1 NOLOGIN policy remain unchanged. Missing tables,
unexpected ownership, effective table/column rights, grant options and other
existing grant-policy escapes remain rejected. Existing roles/records are not
silently upgraded; owner migration would require separate review.

Bound MarketHoldStore, MarketCandidateStore and MarketResultStore check exact
configured authority/schema/profile at construction. Each connection verifies
actual SCRAM database/login identity and all effective runtime grants before
market data queries. Identity/grant failure closes the connection with a fixed
private error and no owner fallback. Hold can use v2; candidate/result require
v3. Unbound constructors preserve explicit fixture paths and must not enter a
deployed factory. Source/context dependencies retain their own verified authority.

## Focused test receipt

`tests/test_market_runtime.py` passed **18 cases in 40.73 s** with locked Python
3.12 dependencies and actual local PostgreSQL 16.15. It covers the v3 grant
matrix, default-profile downgrade/missing-table rejection, three general login
roles denied market reads, all three stores' actual SCRAM identity and wrong
login rejection, six effective-grant drift cases, exact boolean admission and
signed hold/candidate/result/HTTP replay.

Combined locked pytest over market runtime, runtime login/roles, signed market
hold integration, candidate/result codec/hold stores, economic/market hold API
and thermal publisher tests passed **110 cases in 100.05 s**, no skips. The local
`OSSF_TEST_PG_DSN` points to the existing private socket; temporary SCRAM database,
roles/password files are fixture-created and cleaned up. No existing HBA changed.

The integration binds ThermalRunStore context, signed MarketHoldStore and both
calculation stores to the actual authority login. A fresh result-store instance
replays the original Decimal economics; HTTP preserves string amounts and
`assumed`/`hold`. Foreign-tenant lookup returns no result, identical retry leaves
one immutable record, and changed scope refuses replay. HTTP uses a synthetic
principal injection, not operating Bearer/account proof. Source baselines,
shocks, rights and settlement remain self-authored in-memory fixtures. Test keys
and credentials remain under one local OS UID; the authority credential holder
can still execute permitted SQL directly outside RPC.

The four market modules now join the closed thermal code digest. Fresh independent
release bytes/review are required; existing manifests/releases/decisions are
not rewritten. Changed local document links and staged whitespace are checked
before commit. Hosted exact-head CI will supply a separate receipt.

## Remaining holds

Protected full operator assembly, source repositories/evidence, production
account/credential/key custody, DB TLS/HBA/RLS, actual isolated CLI, independent
thermal release and browser end-to-end flow remain incomplete. These tests do
not authorize a MarketSnapshot, future crop/margin forecast, crop comparison,
energy purchase, deployment or G0–G4 acceptance. Existing task checkboxes remain
open where their complete acceptance evidence is missing.


## Hosted exact-head verification receipt

Commit `082090b37dd75a5a6f2de67817c7c3471deb3a2f` completed
[backend CI 36412355472](https://github.com/KIMSUNGHOON/OpenSmartFarmSim/actions/runs/36412355472):
**1,548 ordinary tests passed**, two existing Pydantic warnings, 377.08 s;
**4 distinct-UID tests passed**, 18.51 s, plus the kernel content DAC check.
[Compose CI 36412355294](https://github.com/KIMSUNGHOON/OpenSmartFarmSim/actions/runs/36412355294)
passed. Both completed runs were rechecked against the exact commit. These
receipts cover v3; later break-even changes require their own verification.
