# Solar API request cost diagnostics — v1

Local observer accepted with [11 checks on both Python versions and actor hashes](../research/solar-api-request-cost-implementation-20261020.md). The [one actual observation](../research/solar-api-request-cost-observation-20261020.md) is also accepted as diagnostic evidence:24 requests/segments reconciled, whole execution failed at last-confirmed27/64. Normal acceptance remains pending.

Extends the existing [worker/API observer](crop-solar-worker-progress-diagnostics-v1.md).
The [current simultaneous run](../research/solar-current-worker-api-diagnostic-20261020.md)
records statuses and worker phases, but lacks API request latency/CPU/SQL cost.
The [confirm-local reconstruction candidate](../research/solar-confirm-registration-evaluation-20261020.md)
failed its whole-workload cost criterion. Do not repeat that trial or infer the
concurrent failure's cause from isolated worker micro-optimizations.

## Small implementation

Extend `research/crop-solar-api-response-trace.py`; retain its explicit diagnostic
selection and original actor body, calls, assertions, input, polling and budgets.
No product API or always-on tracing is added.

For actual client `request_http` calls, record bounded monotonic start/end and
wall duration, and a fixed route category if safely recognized. Caller-thread
CPU measures only the client thread; never present it as server processing CPU.
Unknown routes get a fixed `other` label. Never emit raw paths or identifiers.

For the existing protected execution `checked` and prefix `read` functions in server threads,
record outermost operation start/end, wall and that thread's CPU, counts of
actual SQL execution/current validation/storage loads, and SQL execution wall
time if attribution can be demonstrated. Match by an explicit bounded internal
thread/frame lifetime, without exporting frame locals, SQL, parameters, body,
query, identity, token, DSN, exception message or unrestricted function names.
Do not double count nested operations or sum nested wall times as exclusive cost.
Retain incomplete entries as incomplete; do not manufacture return status.
Record wall and CPU clocks independently with their implementation/resolution;
do not clamp CPU to wall or require exact nanosecond ordering across clocks.

Use the existing observer and dependencies. Bound active operations to16 and
records to recent32 responses/operations and16 exceptions, with a hard64KiB
total atomic journal and explicit dropped counts. New timestamps/counters must
not break that bound under worst-case allowed location/name lengths. Close
lifetimes after return/exception, including sequential calls on reused threads.
Instrumentation costs are included in this diagnostic and must be reported.

## Acceptance and one actual observation

1. Add focused controlled tests for actual call durations and fixed labels,
   server-thread attribution/nesting, exception/reused-thread cleanup, unknown
   code rejection and no secret/body/path/SQL export. Exercise record and total
   byte limits, dropped counts, owner-only atomic files and no leftover temp.
   Preserve the original response/status/exception tests.
2. Reconstruct and hash the unchanged original API/worker actor bodies after
   removing only the selected observer headers. Keep the original64/chunk1,
   polling/retry360 and RSS/owned cleanup rules. Use the new observer for one
   actual simultaneous diagnostic, not another unchanged normal attempt.
3. Reconcile the immutable run/head/actor/header/resource/artifact identity with
   completed/incomplete client and server timings, current/source/SQL/load
   counts and actual worker-confirmed prefixes. Report missing correlation or
   interrupted spans explicitly. Do not infer server CPU from client waiting.
4. Choose the next product change only from that evidence. An instrumented run
   cannot pass normal64, live WebGL, WSL activation or the product claim gates.

Design judgment is made in the current native Codex CLI `gpt-6.1-sol`/`xhigh`;
no recursive CLI or additional agent is needed.
