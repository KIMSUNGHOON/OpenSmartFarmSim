# Farm registration connection lifetime — v1 candidate

Status: [core implementation locally accepted by52 focused checks](../research/registration-connection-lifetime-core-20261019.md).
Related worker/query/HTTP regression and independent original64 remain pending;
full integration and deployment are not accepted. The private normal-cost experiment
preserved183 role audits,1,824 ordered source reads,432 transaction ends and
original values/UTC, while reusing one physical connection across144 leases.
Its two advances improved by about26%/23%. This is feasibility evidence only;
the private monkeypatch must not become product code.

## Interface and ownership

`registration_connections(owner, witness)` owns connections only inside the
existing exact `RegistrationRead` lifetime. `read_connection(store)` yields an
actual base Psycopg connection at the six existing read/row-lock call sites.
Outside a supported scope it uses the original `with store.connect()` path.
The existing `.connect()` return type and ordinary callers stay unchanged.

Support the default JobStore/MarketSourceStore/ThermalRunStore cohort only when
their authority policy object, DSN/schema and principal provider agree and job
grant auditing is enabled. Initially unsupported bindings retain the original
path; drift after entry rejects the operation. Bind to the exact owner/witness,
ContextVar token, Task and thread. No cross-request pool or stored permission
result is introduced.

The explicit lease calls the original store `.connect()` and its current role
audit. Only its physical connection factory may borrow an idle owned connection,
through a private ContextVar request active during that call. Existing runtime
identity checks and commits still execute on every lease. A direct `.connect()`
call without that request still creates a fresh connection.

## Transactions and session state

Each original transaction ends at the same read context boundary: commit on
success; rollback and physical close on failure. `FOR UPDATE` ends before the
later authority/thermal/reference work. A busy connection cannot be reused;
distinct simultaneous leases use distinct physical connections. Preserve Read
Committed and the existing market read-only transaction statement.

Check the exact factory arguments, actual connection identity/configuration and
idle status before reuse. Record and recheck server session defaults/settings
inside existing transactions before the original identity commit and before the
data commit, rather than adding a long enclosing transaction. Client adapter/
row-factory/transaction controls must remain unchanged. Session drift, wrong
execution, cancellation, rollback failure or a closed connection poisons the
registration. Close all owned connections and release tokens/references at exit.

## Acceptance

1. Reproduce the missing reuse on actual SCRAM registration reads, then prove
   one physical backend with unchanged original values and a fresh ordinary
   connection outside explicit leases. Verify complete close and re-entry.
2. Compare actual original step2/3 against the product candidate in alternating
   order. Preserve ordered source reads, all183 audits, original transaction
   ends/row-lock release boundaries and values/UTC. Record any added session
   checks separately. Useful consistent actual cost improvement is required.
3. Test actual late grants/revokes and identity/session drift after preparation,
   root/snapshot/source changes, tenant/Task/thread/copied-context isolation,
   nested/busy leases, body/commit/rollback failure, cancellation and cleanup.
   Retain initial unsupported paths and related worker/query/HTTP regressions.
4. Review before adopting. Changed-source original64, subsequent hold/cancel,
   calculating WebGL and user activation remain the existing separate gates.
   Domain claims and G0–G4 follow [PROJECT_SPEC](../docs/PROJECT_SPEC.md).

The current native `gpt-6.1-sol/xhigh` CLI owns this design judgment. No recursive
CLI or subagent is used. WSL resource limits and protected services remain fixed.
