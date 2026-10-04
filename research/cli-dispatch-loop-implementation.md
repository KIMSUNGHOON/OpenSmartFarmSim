# Authority dispatch loop — 2026-10-04

Status: local RPC/process software acceptance passed; hosted regression and
application source-consumer assembly pending.

The [contract](../contracts/cli-dispatch-loop-v1.md) adds a separate command
around the existing fixed-peer AuthorityClient. It freezes validated scope,
polls sequentially with bounded waits and emits non-null validated metadata.
Unresolved exchanges and unclosed outcomes stop without a subsequent request.
The authority keeps candidate selection, due-time/lease recovery and durable
publication. No database/model/credential input or gate approval is added.

The existing signal-stop class is moved into `process_stop.py`; deterministic
work imports the same mechanism. The new context manager restores prior signal
handlers/wakeup FD and closes both owned descriptors on normal/error exit.
In-flight RPC wait semantics remain unchanged, including crash uncertainty.

## Evidence and review

- Before implementation, the new test module failed collection because
  `app.cli_dispatch_loop` was absent: `/tmp/ossf-cli-dispatch-loop-red-20261003.log`.
- Restricted-sandbox runs failed at actual Unix socket bind with EPERM, affecting
  existing dispatcher tests as well. They were not treated as software failures
  or passing socket proof. The same focused command ran after explicit sandbox
  escalation; no fixture/provider/protocol guard was weakened.
- Final new19 plus existing17 cases: **36 passed in5.95seconds**, no skips.
  Actual fresh Unix-socket subprocesses prove null→hold polling, minimum0.95-second
  spacing and idle SIGTERM under1second; lost reply, wrong tenant and unclosed
  outcome cause one request only and fixed exit3. Existing tests repeat wrong
  peer/malformed reply and all supported states. Fixed configuration errors,
  live scope mutation, five pre-construction client changes, signal/wakeup and
  descriptor restoration pass. Log: `/tmp/ossf-cli-dispatch-loop-final-20261004.log`.
- After signal extraction, the existing deterministic consumer passed
  **37 cases in126.61seconds**, including actual separate SCRAM/process completion,
  cancellation, killed-process expired-lease recovery and break-even verification.
  Log: `/tmp/ossf-process-stop-deterministic-scram-20261003.log` (retained filename).
  Idle observation:2.200104743s/0.02CPU seconds, minimum page gap1.037331388s,
  stop0.113895171s. This is one local observation, not a production SLA.

The local heavy slot was sequential at nice10; the SCRAM fixture created and
removed its own disposable PostgreSQL16.15 cluster, without modifying the
persistent baseline. No real CLI/model was launched. Review in the existing
`gpt-6.1-sol`/`xhigh` Codex session `01a0e064-b01b-7a22-8ef8-dd4afe0eb7dc` found
a mutable client could already be invalid before loop creation; construction
now reuses the original client validator and five concrete negative cases.
Current values are rechecked before/after dispatch. Reply validation reuses the
existing canonical parser; no second lease/queue/gate mechanism is introduced.
Python compile/whitespace checks passed. Agricultural/money code and locks are
unchanged; these consumer bytes are pinned separately from calculation digests.

| File | SHA-256 |
| --- | --- |
| `backend/app/cli_dispatch_loop.py` | `a234300b487c52df865b629112b3eb5bd3de12776e267389c315fd5ef6124afc` |
| `backend/app/process_stop.py` | `ae866e9fee6162086b44f679ee1d30e77ac43ada629331472be61316a00e6fc1` |
| `backend/app/deterministic_work.py` | `7ac82622e7251f319844a83466052e5c2a778942f48f6aa926703e7c86587f0b` |
| `backend/tests/test_cli_dispatch_loop.py` | `fba8fab88cec6f9e62c5426019970f20e2c046c829371a8bba7e350a0d4f6f6c` |

This is synthetic software RPC evidence with the current local OS UID; it adds
no actual CLI call, independent service custody/release or G1/G4 approval.
Hosted role/UID/source-flow/Compose tests, collection automatic consumption and
actual product research/review/assessment remain subsequent work.
