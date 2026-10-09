# Authority dispatch foreground loop v1

Status: implemented; [local focused acceptance](../research/cli-dispatch-loop-implementation.md)
passed. Hosted/source-service/actual CLI acceptance remains pending.

This is a separate command/library around the existing AuthorityClient; the
one-request `app.cli_dispatch` contract stays as published. A trusted operator
selects one absolute endpoint, expected peer UID, tenant and existing 1–660
second wait. Poll interval is an exact integer1–60; booleans are invalid. The
loop freezes those values and refuses later binding mutation. It owns no DB,
source/gate/CLI credential, model choice, lease or result approval.

`AuthorityDispatchLoop(client, poll_seconds=1).run(stop_event, emit=callback)`
uses exactly the existing concrete AuthorityClient. Each successful exchange
requests the fixed `run_next` message, receives the existing peer/scope/frame/
result validation and waits after the exchange. Null queues create no per-poll
log. Known queued outcomes may be followed by a fresh dispatch; the authority
owns persisted due times, leases and candidate selection. A lost/malformed reply
or any unresolved exchange ends immediately without another request. An
`unclosed` outcome is recorded as bounded metadata and also ends the loop; it
does not prove completion or permission to blindly retry.

`python -m app.cli_dispatch_loop --socket PATH --authority-uid UID --tenant TENANT`
adds explicit `--wait-seconds` and `--poll-seconds`, never job IDs, DSN, keys or
model/input overrides. Output contains started/stopped events and validated
non-null dispatch metadata only. Startup rejects with a fixed error/exit2;
unresolved execution rejects with `authority_dispatch_unresolved`/exit3.

SIGTERM/SIGINT use the existing nonblocking signal wakeup mechanism moved into
a common process-stop module. Idle waits exit promptly without Event-lock use.
An in-flight RPC retains its existing bounded wait and durable uncertainty
semantics; a dispatcher crash/forced stop does not cancel the authority's job.
No automatic process restart/recovery is added. Prior handlers/wakeup FD are
restored and owned descriptors closed on every command exit.

Acceptance requires fresh Unix-socket subprocess tests for actual repeated
null/non-null dispatch, bounded poll spacing, graceful idle stop, peer/scope/
reply loss rejection with no subsequent request, unclosed stop, fixed errors,
binding mutation and wakeup/descriptor restoration. Re-run the existing
deterministic foreground consumer's focused regression after extracting the
shared signal mechanism. These are software RPC proofs, not actual model calls,
independent operating custody or G1/G4. Actual role/UID/Compose source flow is
the following application-source-consumer acceptance.
