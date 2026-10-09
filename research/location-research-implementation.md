# Location research admission implementation evidence

On 2026-09-28, the existing Codex CLI 0.157.1 session
`01a0e064-b01b-7a22-8ef8-dd4afe0eb7dc` implemented and reviewed
[location research admission](../contracts/api-location-research-v1.md) and the
[CLI temporal precision v2 correction](../contracts/cli-temporal-precision-v2.md).
The latest local turn context inspected at `2026-09-28T08:32:02.110Z` records
`gpt-6-sol` and `xhigh`. No additional/nested model invocation, external data
collection, agricultural/economic coefficient or independent review was used.
This is current-session software evidence, not runtime CLI execution or release.

Actual server-issued signed planning timestamps carry microseconds. The generic
CLI parser previously accepted only whole seconds, rejecting these valid inputs.
The new validator versions retain exact timestamp text and accept at most six
fractional digits; extra precision is rejected instead of truncated. Three CLI
stages accept the real authenticated planning-store context. An evidence instant
one microsecond after D remains late. Existing signed bytes are not rewritten.

The optional HTTP admission requires `location_create` on the API and store,
a real authenticated job authority, a successful grant audit, and a trusted
read-only registered scope resolver. It preserves provider catalog identity in
the exact immutable research input. Initial all-null planning context denotes
preparation only; the response marks spatial support as `pending_research`.
It does not grant coverage, rights, G0, signed D-time knowledge or completion.
Existing tenant/stage/key uniqueness supplies replay and conflict behavior.
No new SQL tables, grants or software dependencies were added.

Local disposable PostgreSQL 16.15 with synthetic catalogs/principals and private
SCRAM credentials checked the new HTTP route: **35 passed in 14.97 s**. Cases
include persisted exact input/hash, public job reads, sequential/concurrent
replay, changed input/catalog conflict, tenant separation, both scope checks,
strict bounded JSON, unsupported/mismatched catalogs and live grant drift.
Temporal correction and generic CLI/review checks initially passed **24 cases**.
The final combined admission, four existing HTTP read paths, intent uniqueness,
temporal/CLI/review and publisher suite passed **88 cases in 29.82 s**, using
`uv run --locked --group dev pytest` and `OSSF_TEST_PG_DSN`. Whitespace checks and
module import checks passed. Full hosted CI is a separate receipt.

`orchestration.py` enters the publisher's closed code-byte inventory. Changed
validator/server bytes require a new independent release; prior source manifests,
released bytes and published records remain immutable. Actual scope/catalog
assembly, request authentication, operating account, isolated CLI invocation,
provider collection, later signed planning, UI and independent release remain
missing. These fixtures do not establish G0, G1 completion, field/forecast/ranking
validation or deployment G4.

The admission/precision changes at exact commit `3fd4f66` subsequently passed
[backend CI](https://github.com/KIMSUNGHOON/OpenSmartFarmSim/actions/runs/36398488128):
**1390 ordinary tests, 2 warnings**, **four distinct-UID cases in 18.53 s** and
content DAC. Its [Compose receipt](https://github.com/KIMSUNGHOON/OpenSmartFarmSim/actions/runs/36398488142)
also passed. Their terminal status and exact head were rechecked on 2026-09-28;
these receipts do not cover the later research registry module.
