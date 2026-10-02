# Deterministic foreground consumer v1

Status: implemented; focused actual process/SCRAM software acceptance passed.
This closes the manual job-UUID delivery gap for the existing deterministic
economic, break-even calculation and break-even verification workers.

## Operator interface

`python -m app.deterministic_work --factory trusted_module:build` loads one
operator-selected callable returning an exact `DeterministicWorkerLoop`.
The module reference is a trusted deployment argument, never an HTTP/job/CLI
proposal field. Its dependencies and credentials remain in protected operator
files; this interface does not provision accounts, install schemas or supply
missing farm/source/release validators. The separate operator-config and
application Compose tasks own deployable configuration and images.

`DeterministicWorkerLoop(worker, *, input_versions, poll_seconds=1, page_size=25)`
accepts exactly one existing EconomicCalculationWorker,
BreakEvenCalculationWorker or BreakEvenVerificationWorker per process. Versions
are an explicit nonempty frozenset accepted by that worker and by
[discovery](deterministic-job-discovery-v1.md). Economic v2 requires its farm
binding; v3 requires both farm and authored Run bindings. No missing dependency
is inferred. Poll seconds is an exact integer in 1–60; page size is an exact
integer in 1–50. Booleans are rejected.

The consumer constructs discovery from the same fixed JobStore, tenant,
versions, authenticated principal and audited authority runtime policy. These
bindings and the worker's existing dependency checks remain current before
discovery and before every dispatch. A version match alone does not validate
input, rights, arithmetic, parent completion or scientific gates.

## Processing and waiting

Each cycle reads one bounded page and invokes the existing exact-ID
`worker.run_once(uuid)` sequentially for its selected records. It follows the
last-scanned cursor even when a full page has no matching version. The end of
a pass resets the cursor, so newly due retries/expired leases behind it are
revisited. A wait occurs after every page, including pages containing only
unrelated versions; the process performs no busy rescan. It uses an interruptible
Event wait, rather than a blocking sleep. There is no second lease/retry/recovery
state machine or recursive Codex invocation.

The existing worker owns current access/input/parent/source checks, the exact-ID
claim, heartbeat, cancellation, attempt closure and atomic result publication.
An advisory candidate may return no work because of a concurrent claim or
state change. A worker's closed transient attempt remains eligible only through
the existing persisted retry schedule. Errors in discovery/binding, malformed
outcomes or `unclosed` outcomes stop the consumer with a fixed failure; they
are not reported as an idle/empty queue or successful calculation.

## Signals and public process output

SIGTERM/SIGINT set the stop event. An idle wait exits promptly. No further job
is dispatched after the event is observed. A job already running finishes
through its existing cancellation/publication fences before graceful exit;
this does not impose a new completion deadline on long maximum calculations.
An external supervisor may force termination. After an actual process crash,
the expired lease and recovery belong to the existing JobStore/worker; a new
consumer discovers the owned expired record and lets that recovery decide.
No partial result is accepted solely because the process exited.

On Linux/WSL2, the process uses a nonblocking wakeup pipe and a main-thread stop
flag; the signal handler acquires no Event lock. The prior signal handlers and
wakeup descriptor are restored, and both owned pipe descriptors are closed on
normal/configuration/execution exits. Python documents the nonblocking wakeup
descriptor's use with `select`, the main-thread restriction and restoration
value ([official signal API](https://docs.python.org/3.12/library/signal.html#signal.set_wakeup_fd)).
The library accepts a regular Event; the process uses its signal-aware wait.

Output is bounded
JSON Lines: version 1 `started`, closed `attempt` metadata (job UUID, attempt,
state and fixed reason code), and `stopped`. No input bytes, lease tokens,
credentials, amounts, source contents or result payloads are emitted. There is
no per-idle-page log. Configuration failures exit 2 with
`deterministic_startup_rejected`; unresolved execution exits 3 with
`deterministic_execution_unresolved`; normal stopped execution exits 0.
`started` describes process startup, not independent deployment readiness.

## Required acceptance

The focused test file must prove bounded sequential page following/waits,
binding/version/outcome rejection, signal restoration and fixed errors. Actual
separate Python processes with the disposable SCRAM fixtures must prove:

1. An economic job completes without passing its UUID to the process; current
   result/publication and assessment hold remain intact.
2. Idle polling/CPU stays bounded and SIGTERM exits promptly; SIGTERM during
   execution finishes the current attempt and dispatches no next job.
3. Current cancellation publishes no result, and a killed process publishes
   no partial result; a restarted consumer reclaims an expired lease and
   publishes once, preserving attempt history.
4. Separate configured break-even calculation and verification consumers both
   discover their own input version and preserve full existing parent/result
   checks. Processes, disposable DB/roles and password files are cleaned.

These are synthetic software proofs. They do not establish actual product CLI,
independent release/G1, maximum concurrency, crop ranking or G4 deployment.

## Software acceptance (2026-10-02)

[`test_deterministic_work.py`](../backend/tests/test_deterministic_work.py)
passed **37 cases in 130.07 seconds**: 32 isolated/process-entry/signal-resource
checks and five actual SCRAM cases. The locked Python environment and existing
PostgreSQL 16.15 disposable login fixture were used; the local heavy slot was
kept sequential. All actual consumers used normal existing worker constructors,
synthetic source/keys and the audited authority login. No Codex CLI was launched
recursively and no agricultural or monetary calculation code was changed.

Actual economic processing required no UUID argument. SIGTERM during a controlled
claimed attempt allowed it to complete safely, or acknowledge a concurrent cancel,
and left the following job queued with zero attempts. A killed owned process
left no result/publication/outcome; after the test administrator expired its
lease, a restarted consumer discovered it and produced exactly one result with
`lease_expired`/`succeeded` attempt history and attempt 2. Separate break-even
calculation and verification consumers completed the same two-trial plan and
the current verified-result reader retained assessment hold. Owned processes,
pipes, disposable cluster/roles/schema and password files were cleaned before
terminal success.

The idle observation measured **2.200106357020559 seconds**, **0.030000000000000027
CPU seconds**, three completed page reads, minimum page spacing
**1.0393643580027856 seconds** and SIGTERM exit **0.11394682701211423 seconds**.
This is one local observation of the configured wait, not a throughput or
production availability SLA. The actual log is
`/tmp/ossf-deterministic-worker-loop-scram-v5-20261002.log`.

Command from `backend`: `env -u PYTHONPATH -u OSSF_REAL_CLI_SMOKE -u OSSF_REAL_AUTHORED_FULL_CLI_SMOKE OSSF_TEST_PG_DSN='<local baseline socket DSN>' OSSF_TEST_PG_BIN='<local PostgreSQL binary directory>' nice -n 10 .venv/bin/pytest -q -s tests/test_deterministic_work.py`

Earlier actual runs exposed the `python -m` class-identity mismatch: factory
imports and the entrypoint used different module namespaces. The entrypoint now
calls the canonical module's main, with a dedicated failing/passing subprocess
regression while preserving exact type checks. A functional factory SystemExit
regression and a signal-handler Event-lock regression also failed before their
fixes. Intermediate remaining failures were incorrect test use of typed
JobStatus/UUID arguments; the existing result reader's identity guard was kept.
Logs v1–v4 under `/tmp/ossf-deterministic-worker-loop-*20261002.log` retain those
failures. The preceding combined v4 selection also passed the unchanged 47
discovery cases, but its one failed consumer test means it is not a fully
passing combined selection. Final acceptance uses the terminal 37-case v5 log.

Implementation SHA-256:
`0898b93fc426477e7388887f1036c8c00abc1eff22b70ae98034ba7cc3b49966`;
test SHA-256:
`b2c395a3178e6b7b7c23f654de1063885e6a91879a3ae52d15ddcefa8d3fdf6b`;
locked environment SHA-256:
`e73e9ec049e80bfa4ad96afc33bfa25f5fddab60d60771284d6292178241beb3`.
Consumer bytes are recorded separately from the existing calculation digest's
enumerated files. Self-review in actual Codex CLI session
`01a0e064-b01b-7a22-8ef8-dd4afe0eb7dc`, `gpt-6.1-sol` / `xhigh`
(metadata `2026-10-02T06:40:39.543Z`), found no remaining required changes:
version/worker bindings are explicit, discovery is bounded/current/read only,
claim/recovery/publication stay in their existing modules, public output has
only closed metadata, and no new dependency or scientific gate is introduced.

The official Python 3.12 signal page was retrieved at
`2026-10-02T07:16:38.611413Z`, its displayed update time was
`2026-10-01T15:25Z`, and raw HTML SHA-256 is
`5cab3107a0a204b6717386b3da1156424cbc2fd6d53a6bcf214173ddec9d2a73`
(`/tmp/ossf-python312-signal-20261002.html`, 108,884 bytes). This is a development
API reference, observed/available at retrieval; agricultural units and dataset
vintages do not apply. Signature/behavior were checked against local Python and
the tests above. The documentation names PSF License v2, with example recipes
under Zero Clause BSD; this repo stores the link/paraphrase, not the raw HTML.
Review: the same exact-model CLI session above. Hosted regression for the added
consumer/discovery files, protected operator config and application Compose,
real product CLI/independent release/G1 and G4 are subsequent acceptance.
