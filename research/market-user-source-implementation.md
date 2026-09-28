# User-assumption market source persistence evidence

Status: typed authenticated storage software candidate; no G0/G1/G4 acceptance.

The active Codex CLI thread `01a0e064-b01b-7a22-8ef8-dd4afe0eb7dc` made the
interface/architecture judgment and implemented the reviewable output in
[the source store](../backend/app/market_source_store.py) and
[its contract](../contracts/market-user-source-store-v1.md). Selective inspection
of actual turn_context at `2026-09-28T11:58:48.843Z` records exact gpt-6-sol/xhigh.
There was no recursive CLI, extra model call or new agent. This output is not
independent reviewer, source, execution or release approval.

## Implementation and review

Seven existing strict user-assumption models share one immutable typed record
table, with explicit tenant/kind/ID/revision. Server admission reads actual
collection/simulation job bytes, verifies their hash and canonical model/tenant,
then records the original job, actual authority login, software-validation marker
and DB time. It accepts no caller pins, reviewer or approval flags. Every read
rechecks original job bytes and generates baseline/shock pins from them.
Prior costs have no revision in the existing type and therefore require a new
cost_ref for correction. First binding persists on identical retry; conflicts
roll back. Models, time/money calculations and old immutable data are unchanged.

Explicit v5 adds only source table SELECT/INSERT for authority, no general or
supervisor access, and requires market opt-in. Defaults v1–v4 retain their prior
matrices/version. Store connections require actual SCRAM and full effective
grant audit, with no owner/unbound fallback. Existing API source factory can
supply this reader; its signed hold/context authority remains independently
assembled. Operating provisioning and source write HTTP flow are not implemented.

Review identified the raw-field job filter preventing existing source digest
references. A separate failing test preceded the exact raw_sha256/lowercase
64-digit exception; invalid values/aliases/raw/secret names remain denied.
Typed canonical wire includes default fields: an earlier fixture representation
can have another hash. The persistence integration now uses actual adopted shock
hashes and newly generated candidate refs, preserving the old fixture versions.
Time/use-right failures still reject admission or the subsequent decision path.

## Verification receipts

Initial source tests failed because the module did not exist. After first
implementation, the raw-hash case exposed the job filter; after the targeted
fix, **16 cases passed in 23.06 s** on locked Python 3.12/local PostgreSQL 16.15.
The expanded set initially passed 19 cases before signed fixture preparation
failed; the signed-memory fixture and typed-wire references were corrected.
Separate time/rights cases then passed **2 cases in 17.24 s**.
The first complete memory-removal path reached successful economic/grid replay
and HTTP zero output, then failed its final denied-read assertion (404 expected
by the existing scoped lookup contract, not 503). That expectation was corrected;
an already-running focused invocation was interrupted after 21 passing cases to
avoid repeating the known failure. It is not a completed verification receipt.

Final locked focused run passed **92 cases in 377.91 s**, no skips, covering
**22 new source-store cases** and existing authenticated market/break-even,
runtime role, durable job and intent/idempotency contracts. The canonical
OpenAPI check passed unchanged; **116 changed-document local links** and staged
whitespace passed. Manual review inspected tenant/current-scope binding, exact
actual job/hash/model agreement, fixed errors, atomic conflict/retry, immutable
triggers and default profile preservation. Full hosted CI follows this commit;
original API assembly exact-head receipts are in
[its evidence](api-runtime-assembly-implementation.md).

## Remaining holds

Exact source-store commit 88f467486f9a83cdfe040b714614e1d21b90a0aa passed
[backend CI 36421366549](https://github.com/KIMSUNGHOON/OpenSmartFarmSim/actions/runs/36421366549):
**1620 ordinary tests, 2 existing warnings, 689.91 s**, **4 UID cases in 16.31 s**,
and the distinct Linux UID content-access step. Exact-head
[Compose CI 36421366561](https://github.com/KIMSUNGHOON/OpenSmartFarmSim/actions/runs/36421366561)
passed. These describe that commit, not the following thermal worker code.

All records/keys/credentials are self-authored synthetic fixtures. Immutable job
input proves submission, not completed collection or actual model invocation.
External URL/product/observation/publication/retrieval/vintage/QC/reviewer evidence
and actual rights adoption remain absent. No external source is approved and no
new MarketSnapshot or crop, purchase-energy, future-margin or ranking claim opens.

Protected operator source admission/configuration, actual CLI and independent
custody/releases, accepted assembled thermal Run, remaining API orchestration,
browser/full G1/G4 and load/capacity remain incomplete. Per-read full grant audits
are deliberately preserved; no latency/SLO or service capacity is asserted.
The new module joins the closed thermal digest and needs a fresh independent
release. Whole-task checkboxes remain open. No dependency, raw restricted data or
credentials were added. Changed links and whitespace are checked before commit.
