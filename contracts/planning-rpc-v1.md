# Planning RPC v1

Status: **software candidate**. A separate planning service owns the
[writer login and private key](planning-login-policy-v1.md). Its caller owns
only the socket endpoint, expected service UID, fixed tenant and a public-key
DecisionContextVerifier backed by the reader login. No CLI/model call is made
by this service. It neither approves sources nor opens G1/G4.

`PlanningServer(authority, snapshot_resolver, socket_path=…, caller_uid=…,
tenant_id=…)` accepts one configured OS peer and tenant. The protected socket
directory belongs to the service UID and is not writable by group/others.
The concrete PlanningAuthority must use the writer-bound store; owner/smoke
stores are rejected. Startup and each issuance audit the authenticated login.
The trusted resolver must return the matching immutable tenant/snapshot row
before a new planning event can be issued; this lookup is not G0 approval.

The length-prefixed strict JSON request is at most 4096 bytes:

```json
{"version":1,"op":"issue","snapshot_id":"…","claim_mode":"ex_post_replay","decision_time_kind":"actual","hypothetical_at_utc":null}
```

Fields are closed. Tenant, context/event ID, authority, signature, issuance and
actual D cannot be supplied. A hypothetical request requires an explicit UTC
instant; actual requires null. Success returns exactly `version`, `ok`,
`tenant_id`, UTF-8 `context_raw` and `context_signature`, bounded to 65536 bytes.
The raw canonical context and signature enter the existing verifier unchanged.
Before returning, the client verifies the peer UID, envelope, signature, durable
planning event and request's tenant/snapshot/mode/kind/hypothetical D binding.

Server rejection returns only
`{"version":1,"ok":false,"code":"planning_issue_rejected"}`.
Malformed/lost/rejected replies become the client's fixed
`planning_issue_unresolved` exception, without source or credential details.
The frame deadline is five seconds using the existing Linux Unix-socket IPC.

**Issuance is unsafe to retry.** Each accepted call creates a new event/context;
commit can succeed before the reply is lost. The client makes one attempt and
never retries. A known returned context can be stored/reused with its exact
bytes; HTTP intent/recovery assembly must persist its own initiating intent
before calling this boundary. No idempotency guarantee or request lookup is
invented here. Event commit and downstream context/queue writes are separate
transactions, so unused planning events may remain after downstream failure.

The foreground loop uses restrictive socket permissions and SO_PEERCRED,
counts bounded verification sessions, cleans up only its own socket inode and
supports SIGTERM. Operator-controlled service assembly, independent key/UID
custody, database tenant isolation, full filesystem/clock operations, actual
CLI execution and independent thermal release still need deployment evidence.
Software tests with shared OS identity/test keys do not supply that evidence.
