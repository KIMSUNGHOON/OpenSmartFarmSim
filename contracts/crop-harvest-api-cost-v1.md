# Preserved harvest: protected API read cost v1

Scope: owned synthetic software research. This does not approve cultivar output,
G0–G4, realtime execution, full WebGL, or deployment capacity.

## Inputs and custody

`research/crop-harvest-api-cost.py` is a stdlib-only import. Before importing any
backend code it selects an explicit frozen source root and storage-helper SHA.
Already loaded `app` modules from another root are rejected. The original storage
manifest is checked by that exact helper, including its absolute dependency paths,
authenticated backup, keys, profiles and original record. No manifest is rebound
to another checkout. Only an owned, separate PostgreSQL restore is used.

The standard `ApiRuntime` assembles the normal current calculation and harvest
factories on the same jobs/farm graph and actual SCRAM database. TLS uses a private,
fresh loopback certificate; bearer secrets and private paths stay outside Git.

## Observation and acceptance

Sequential actual HTTPS GETs read summary, first `min(64, total)` rows and last one
row. There is one active read. Each complete wire response must fit **30 seconds
including TLS and body**, and **2 MiB**. An independent ASGI observer records status,
bytes and SHA; the accepted HTTP reconciliation helper compares those observations
with original record, summary and page hashes. A timeout, size, wire or value
mismatch stops subsequent success probes and records a hold. No limit is widened.

Foreign tenant (404), missing scope (403), and an instance-scoped current display
denial (422) are checked over HTTPS. Restore of that callback must recover the same
original summary. Shared rights/principal files are never modified. Read guards
forbid growth RHS, harvest generation, registration and proof issuance.

Acceptance also requires unchanged original source identity/bytes and DB counts,
closed HTTPS thread, stopped owned PostgreSQL, FD preservation, actual original
command exit 0 and a separate resource/cleanup audit. Diagnostic hold exit 2 is
not API acceptance. The external controller enforces 512 MiB per PID / 1 GiB for
the explicit owned and protected observed trees, not whole WSL capacity.

Focused transport tests establish TLS/boundary/cleanup behavior. A small actual
preserved DB establishes assembly; full-load acceptance additionally requires the
accepted full writer, independent row audit, authenticated backup and fresh read.
Small and full evidence are recorded separately. The existing frontend is unchanged.
