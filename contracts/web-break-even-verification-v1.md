# Web asynchronous break-even verification v1

Status: internal software candidate. Extends the existing
[conditional workspace](web-break-even-workspace-v1.md) using the
[asynchronous HTTP contract](api-break-even-verification-v1.md).

Calculation and verification are separate simulation Jobs. Refreshing a
calculation reads only its actual status. Once it succeeds, the user deliberately
requests result verification with that pinned calculation UUID. No monetary
result appears before the verification succeeds and its completed result passes
the existing exact plan/context/calendar/target/unit/grid decoder.

Submission sends only `calculation_job_id`. The server determines its immutable
intent, current implementation and verification UUID. The browser rejects a
non-simulation Job or the parent UUID returned as its child. Unknown admission
keeps the exact parent and locks editing/disconnection; confirmation repeats
that same request. It must not replay scenario/plan writes, select a new parent
or invent a verification UUID. Known rejections remain visible and permit
connection correction. No time passage implies admission or completion.

The screen separately labels calculation and verification status/identifiers.
Once the child exists, refresh reads its status and, only on succeeded, its
`break-even-verified-result`. Queued, active, held, failed or canceled children
have no displayed amounts. Every refresh clears old result display before
current reads, so denied/inconsistent evidence cannot retain stale amounts.
The screen never invokes the synchronous full-replay result endpoint.

Existing money/null/hold rendering, navigation lifetime, responsive table and
authenticated 30-second transport/524288-byte result bound remain in force.
The legacy synchronous SDK method remains available to existing callers and
shares the same strict projection decoder. The browser computes no economics.

Focused SDK/admission, Chromium lost-response/queued/error-state and actual
SCRAM/HTTPS/separate Python worker evidence are required. Reload restoration,
automatic workers, actual 256-trial load/cancel/retry/rights withdrawal and
independent product CLI/G1/G4 remain separate acceptance work. Synthetic
fixtures establish software contracts only.
