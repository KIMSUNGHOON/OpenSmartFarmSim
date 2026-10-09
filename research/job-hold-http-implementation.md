# Validated job hold HTTP implementation evidence

On 2026-09-28, the existing Codex CLI 0.157.1 session
`01a0e064-b01b-7a22-8ef8-dd4afe0eb7dc` implemented and reviewed
[job hold details](../contracts/api-job-hold-v1.md). The latest inspected local
turn context at `2026-09-28T09:02:59.582Z` records `gpt-6-sol` / `xhigh`.
No additional agent, nested CLI/model call, external source research, farm record
or agricultural/economic coefficient was used. This is current-session software
evidence, not independent gate or runtime model evidence.

The new read route joins existing immutable job/report/content accessors and
returns only typed public missing categories/counts, report reason and storage
time. Unknown private missing IDs collapse to `other_evidence`; raw bytes,
arbitrary model text and internal audit references remain private. It requires
metadata/artifact/auditor scopes, exact tenant/job/held-attempt identity and the
existing bounded canonical report plus content SHA/size validation. Queued or
infrastructure-only holds do not acquire fabricated validated AI reports.

The initial local PostgreSQL 16.15 suite had **20 passed, one failed** in 18.91 s.
The test tried changing a terminal held job into an infrastructure hold; the
existing immutability trigger correctly refused. The fixture was corrected to
create a new leased job and use its real failure transition. Combined hold,
status/market/location API and registry checks then passed **95 cases in 36.65 s**.

Review identified a separate raw-reader authorization gap: private hold rows
record `read_scope=auditor`, but the prior accessor checked artifact scope alone.
An explicit RED regression returned bytes to the artifact-only store principal.
The reader now requires both artifact and auditor scope; original rights rows,
`hold_v1` bytes and decisions are preserved. After this correction, hold API,
evidence storage, CLI worker, registry and publisher checks passed **151 cases in
56.61 s**, including **22 new HTTP cases**, with
`uv run --locked --group dev pytest` and the local `OSSF_TEST_PG_DSN`.

Checks cover all three CLI stages, persisted reassembly, no-evidence holds,
private-ID collapse, three API scopes and independent store scope denial,
tenant/missing/queued/infrastructure separation, mismatched record metadata,
unsupported/private/malformed reports and actual same-size canonical content
tampering. Test CLI binaries, evidence policies, keys/credentials and source
facts are synthetic and share one OS UID. They establish software projection
and denial behavior, not actual Codex execution or G0/G1/G4.

Changed JobStore bytes require a new independent release under the existing
closed code digest. No schema, SQL grants, software dependencies, immutable
manifests/releases or published records were changed. Operating authentication
and role assignment, per-job containment, actual runtime CLI, independently
approved source/release and full browser/G1 evidence remain missing. Whitespace
and changed-document links were checked separately; hosted CI is a later receipt.

Exact commit `8b8a4b26d2d2162e78bc871fd6f98b79b445e72d` subsequently passed
[backend CI](https://github.com/KIMSUNGHOON/OpenSmartFarmSim/actions/runs/36402630712):
**1447 ordinary tests, 2 warnings** in 329.50 s, **four distinct-UID cases** in
18.66 s, and content DAC. Its
[Compose receipt](https://github.com/KIMSUNGHOON/OpenSmartFarmSim/actions/runs/36402630689)
also passed. These exact-head receipts were inspected on 2026-09-28 and do not
cover the later HTTP identity changes.
