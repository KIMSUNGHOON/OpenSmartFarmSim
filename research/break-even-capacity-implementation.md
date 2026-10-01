# Break-even result byte capacity correction

Date: 2026-10-01 (Asia/Seoul). Development CLI: `gpt-6.1-sol` / `xhigh`.

Preparing the asynchronous maximum-grid path exposed a serializer mismatch.
A full **256-trial** in-memory synthetic market/ledger replay produced an
**80,912-byte** canonical result. Its plan was **48,020 bytes** and its actual
calculation input **48,801 bytes**, within the unchanged 64 KiB input bound.
The worker sent result bytes through the input codec and rejected this
storage-sized result at 65,536 bytes.

`canonical_result_bytes` now applies the existing **1 MiB result storage bound**
and the same result schema/canonical JSON. Store pinning, replay, worker result
hashing and completed-job comparison use that codec. Small published results
retain exactly the previous canonical bytes. No money formula, input/body bound,
receipt size, schema, dependency, grant or request deadline changed.

## Verification

- The three capacity tests first gave **2 failed, 1 passed in 7.79 s**:
  the 256-trial output was rejected by the input limit, and the oversized
  result reported the wrong bound. After correction: **3 passed in 8.11 s**.
- The final capacity file plus existing atomic calculation completion and
  read-only authenticated ASGI projection gave **6 passed, 0 skipped in
  159.84 s** on local PostgreSQL 16.15, one `nice -n10` process at a time.
  The 256-trial result is pinned into PostgreSQL rows, byte-compares with
  the worker serializer, and survives a new store's complete replay.
  The smaller worker/API cases use actual SCRAM source/candidate/context
  stores and current tenant/scopes. Over-1-MiB output is refused.

The large-grid source provider is synthetic memory; only its plan/result rows
use PostgreSQL. This demonstrates byte capacity and software consistency, not
256-trial SCRAM worker/HTTP throughput, cancellation or production capacity.
The large-grid asynchronous admission/worker/current-rights reader and 30-second
web/load checks remain required. Actual product CLI, independent G1 and the
existing G0/G2/G3a/G3b/G4 holds remain unchanged.
