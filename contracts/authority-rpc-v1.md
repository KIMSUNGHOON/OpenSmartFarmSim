# Authority dispatcher RPC v1

Status: **synthetic software candidate**. This connects the validated pipeline
to restricted SQL profiles in local process tests. It does not provision logins,
separate operating accounts/keys, attest deployment, or pass G1/G4. The existing
`CliWorker` production constructor guard remains closed.

[`authority_rpc.py`](../backend/app/authority_rpc.py) contains a foreground serial
`AuthorityServer` and a general worker `AuthorityClient`. A trusted provisioner
constructs the server with the existing supervised `CliWorker`, its trusted
DecisionContract/evidence policy, public-key attestation store, fixed tenant,
approved worker UID, and RuntimeRolePolicy. The server rejects a local executable
engine, an absent attestation store, or a mismatched schema/tenant. The trusted
engine is internal to this process: general dispatchers never receive its store,
DSN, frozen input, prompt, lease token, raw output, CLI credentials or signing key.

The authority owns tenant-scoped claims/recovery, exact invocation registration,
capture/decision persistence, signed execution ingestion and pending verification,
and conditional terminal transitions. It uses the existing validators and does
not expose writable JobStore methods through RPC. The separate supervisor owns
actual CLI execution and private-key signing. Source, decision, release and gate
validation rules remain those in the existing contracts.

## Admission and messages

Both ends verify the configured Linux `SO_PEERCRED` UID. The authority socket
parent must be absolute, owned by its operating UID and not group/other writable;
the socket is `0660`. Startup refuses an existing socket. Cleanup removes only
the bound socket inode. Cross-UID group/access provisioning is still unproved.
One server UID/tenant binding is provisioner-controlled; caller data cannot
choose another tenant or a job. A UID shared by several processes cannot establish
their independent control.

Before listening and before each dispatch, a fresh DB connection must have
`current_user` equal to the configured `authority` profile and pass the complete
[effective role audit](runtime-role-policy-v1.md). This is an admission check,
not a guarantee against privileged provisioner changes after that check. Version
1 profiles remain NOLOGIN and reject memberships. With explicit
[RuntimeLoginPolicy v2](runtime-login-policy-v2.md), the server also checks the
original authenticated login, completed SCRAM exchange and current SQL identity.
Real credential/OS UID/key custody remains unaccepted by these local tests.

The optional [content access policy](content-access-v1.md) supports a configured
read-only supervisor group without giving general dispatchers artifact access.
Its focused distinct-UID filesystem probe does not establish complete service,
database-secret or signing-key control for this RPC deployment.

The [explicit hosted service smoke](../research/uid-service-integration-verification.md)
combines these contracts with separate real/effective/saved service UIDs,
existing socket groups and authenticated test DB profiles. It also exercises
peer rejection despite socket group permission. Its fake CLI/test key and
controller forks do not prove independent custody or actual model/deployment
acceptance; ordinary test collection alone is not execution evidence.

Each connection accepts exactly one request:

```json
{"version":1,"op":"run_next"}
```

No job, tenant, stage, lease, input, artifact, argv or environment fields are
accepted. The four-byte network-order length and UTF-8 JSON frame are limited
to 4096 bytes; duplicate keys, non-finite values and extra fields are rejected.
The existing `cli_ipc.receive` imposes an absolute five-second whole-frame
deadline, including silent or partial requests. Sending a reply has the same
time bound. The server is serial; job admission/lease arbitration remains in
JobStore rather than trusting dispatcher-reported state.

A successful exchange returns this shape, with `result: null` for no eligible job:

```json
{"version":1,"ok":true,"tenant_id":"tenant-a","result":{"job_id":"00000000-0000-0000-0000-000000000001","attempt":1,"state":"hold","reason_code":"validated_hold","capture_id":"00000000-0000-0000-0000-000000000002","decision_id":"00000000-0000-0000-0000-000000000003"}}
```

Result fields are limited to canonical UUID references, a positive integer
attempt, the existing six WorkResult states, and a bounded reason identifier.
Capture/decision IDs can be null for failure paths. The client rejects changed
tenant/version, extra fields, invalid UUIDs/types/states/reasons. These are
dispatch status references, not a public assessment or G1 evidence packet.
Rejection returns only `{"version":1,"ok":false,"code":"authority_rejected"}`.
No DB exception, prompt, raw output or secret is returned.

[The general dispatcher command](cli-dispatch-v1.md) exposes this same single
exchange outside test code. It accepts only the trusted endpoint/peer/tenant/wait
configuration and emits a validated status envelope or fixed rejection. An
unresolved exchange never triggers an automatic second request.

## Waiting, cancellation and recovery

The client waits for response readiness separately from reading its frame.
The configured dispatch deadline is at most 660 seconds; once a frame starts,
the five-second frame limit still applies. CLI execution retains its existing
600-second maximum. This is a client wait limit, not an independent hard limit
on every authority DB operation; bounded durable-write/cgroup behavior still
requires deployment work.

An accepted durable job continues if its dispatcher closes the socket or loses
the response. A lost/malformed reply raises `AuthorityDispatchError`; the client
does not retry. The dispatcher must use the existing authorized status/recovery
path to resolve the job outcome rather than infer failure or duplicate a call.
Cancellation is an explicit trusted store/API operation. The supervisor checks
that state and reaps the child; conditional terminal closure checks it again.
Graceful SIGTERM unwinds the supervised execution context and closes the child.
An unclosed lease uses existing expiry/recovery. Hard crashes/SIGKILL and cgroup
cleanup are not deployment-proven by this increment.

Supervisor bounded read connections now preserve provisioner-configured DSN
options before appending forced connection/statement/read-only bounds. This
retains the test SQL role selection; these options do not replace DB grants.
Authority and supervisor configuration is trusted, never caller-supplied.

## Verification scope

[Process tests](../backend/tests/test_authority_rpc.py) run a spawned authority
and supervisor with a fake CLI and test Ed25519 key. Authority connections use
administrator-controlled `SET SESSION AUTHORIZATION`; supervisor connections
use an administrator-controlled `role` option. SQL rights are restricted, but
initial authentication and filesystem/operating UID control remain shared.
There are no new model calls in these process tests.

The cases cover all three AI stages and proceed/hold, foreign-tenant queue
preservation, empty queue, caller-controlled fields and wrong UID, wrong
authority DB identity, pre-dispatch privilege drift, preserved read-only
supervisor role, stalled frames and subsequent dispatch, explicit cancellation,
lost dispatcher connection, graceful termination, concurrent claims, execution
longer than a frame deadline, changed/lost replies and no automatic retry.
Real operating/service accounts, authenticated DB logins, private-key control,
exact CLI execution under that boundary, immutable deployment identity, thermal
release/planning evidence and G4 operating proof remain required.

Local verification on 2026-09-28 used PostgreSQL 16.15 and
`OSSF_TEST_PG_DSN=… uv run --locked --group dev pytest -q`: **1,136 passed,
0 skipped**, including 32 new RPC cases, with two preexisting Pydantic serializer
warnings. `uv lock --check`, staged whitespace and changed local link targets
also passed. These checks do not establish production account or deployment
separation.
