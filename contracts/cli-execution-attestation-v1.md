# Signed CLI execution attestation v1

Status: **software candidate only**. An independent `gpt-6-sol`/`xhigh` CLI
review on 2026-09-27 reported 14,073 input and 1,650 output tokens and
identified a separate process observer and database authority as necessary.
Its proposal is reviewable design evidence, not observed production execution.
The earlier [actual CLI thermal smoke](../research/thermal-cli-review-smoke.md)
still used a mocked execution verifier and a test release.

## Trust boundary

A separately controlled supervisor must own the Codex child process, choose
and hash the executable, construct the exact `gpt-6-sol`/`xhigh` argument array,
capture stdout and final bytes, observe exit via the process wait operation,
and sign only after the complete capture is durably stored. Its Ed25519 private
key must be unavailable to the request process, general CLI worker, publisher,
and database owner at runtime. The publisher needs only its pinned public key.
The current `CliWorker` can delegate to the local IPC software candidate; its
default production constructor remains closed. Same-process HMAC and internally
consistent JSONL cannot prove that a separate process ran.

The canonical UTF-8 JSON record includes a version and key ID; tenant, job,
attempt and attempt ID; frozen job input SHA-256, actual stdin prompt and
output-schema file SHA-256, and unique v4 nonce; CLI version,
executable and environment digests, exact argv; launch and capture IDs; JSONL
and final-output digests; PID and a process start token; UTC start/end/signing
times; successful exit, completion reason, and observed usage. Ed25519 signs
`ossf-cli-execution-attestation-v1` followed by a zero byte and those exact
canonical bytes. The verifier rejects duplicate keys, noncanonical JSON,
non-UTC times, changed IDs/digests, invalid signature, unapproved key, or an
argument array differing from the locked worker form. The [upstream Ed25519
documentation](https://cryptography.io/en/latest/hazmat/primitives/asymmetric/ed25519/)
defines the sign/verify API; the implementation pins
[`cryptography 50.0.1`](https://pypi.org/project/cryptography/50.0.1/) in
`backend/uv.lock`.

`execution_attestations` has a tenant/job/attempt primary key, unique nonce,
job-attempt foreign key, raw SHA-256 and immutable trigger. A repeated identical
insert is idempotent; another record for the attempt or a reused nonce fails.
`ExecutionVerifier` checks the signature, job input and snapshot reference,
attempt/launch/capture/decision IDs, exact model and effort, argv hash, pinned
executable/environment digests, actual prompt/schema hashes against both the
invocation and launch rows, final and JSONL hashes, usage, process ID and
chronology against the existing durable JobStore capture. It also calls the
JobStore's raw invocation-input and capture validators before it returns true.
The argv digest uses the existing JobStore JSON encoding, including its
Unicode escaping; the signed record retains canonical UTF-8 JSON.
A valid-looking
JobStore capture without the signed record returns false. The thermal publisher
already accepts this callable verifier interface, but the production supervisor
has not been connected to it.

## Current proof and remaining hold

The local PostgreSQL 16 test uses a **fake CLI process and test Ed25519 key**.
It verifies a valid record and rejects missing signature, changed result,
cross-tenant/snapshot/decision reuse, duplicate nonce, noncanonical JSON,
unapproved binary digest, deletion, and a sample request DB role attempting to
insert an attestation. The sample role is not a deployed grant policy. The
test signer reconstructs evidence after the fake process; it is deliberately
not independent process observation.

A subsequent exact CLI review found a missing binding between the signed
record and bytes actually passed to the CLI. The record now requires the
observer-computed prompt and schema digests. A fake child records the bytes it
read independently of JobStore, and regression tests reject otherwise valid
decisions when JobStore retained different prompt or schema bytes. The fake
child and test signer do not establish the required production supervisor.

`CliProcessSupervisor` now provides a process-observation core: it chooses the
locked read-only CLI argv, copies only private credentials into a temporary
home, owns the child and output files, reads the Linux process start token,
hashes the actual prompt/schema and binary bytes, observes the exit, and
classifies bounded JSONL/final output. The schema bytes come from the pinned
server contract, rather than the caller. Local tests run a fake child and check
success, timeout, late polling, cleanup, and an observer in a separate local
process. The IPC candidate below now connects this core to the durable worker.
It cannot pass G1 by itself.

`ExecutionAttestationIssuer` is the next software candidate. It owns an
unstarted observer and a configured Ed25519 key, reads a live frozen AI-stage
invocation, rederives the exact prompt through the trusted server contract,
and refuses changed prompt/schema bytes or an unpinned executable before
launch. It binds the observer to that tenant/job/attempt and input hash before
the child runs. After completion it rereads the durable raw JSONL/final bytes,
capture, validation receipt, and decision. Only exact matches can be signed.
Signing can precede terminal publication or validated hold closure so that a
failure before signing does not strand an already-completed job. The thermal
public-key verifier still requires the matching successful job state before
publication. Execution evidence by itself does not approve the decision or
close a job. The same completion
returns the same signed bytes on an in-process retry; another capture or
decision cannot reuse the observation. The environment digest is configured
by the intended supervisor deployment; the test digest is not an observed
production image or runtime identity.
The prelaunch hash check alone does not prove that executable bytes cannot
change between checking and execution; deployment identity remains unverified.

PostgreSQL tests use a fake child and a **same-process test key**, then ingest
the result with the public-key store and thermal verifier. They reject signing
before durable capture/decision storage, noncontract input before launch, and plausible stored
PID/JSONL that differ from the observed child. Research, collection review,
assessment, validated hold, and Unicode executable paths are covered. This
proves software issuance checks, not private-key isolation or actual model
execution. Deployed key and role separation have not been accepted.

## Local supervisor IPC candidate

[`SupervisorServer`](../backend/app/cli_supervisor_service.py) is a foreground,
serial Linux Unix socket server with an operator-configured tenant and worker
UID. [`SupervisorClient`](../backend/app/cli_supervisor_client.py) authenticates
the configured supervisor UID and checks the returned tenant/binary/environment
pins. Linux `SO_PEERCRED` exposes the connected peer's identity; it does not
assign a particular job to a process or separate processes sharing a UID
([Linux Unix sockets manual](https://man7.org/linux/man-pages/man7/unix.7.html)).
The directory is supervisor-owned and not writable by group/others; the socket
has mode `0660`, with cross-UID group membership left to deployment. The server
refuses an existing socket instead of unlinking it. The Python socket API
supports the framing and connection timeouts used here
([Python documentation](https://docs.python.org/3/library/socket.html)).

Each connection has one version handshake, one job/attempt, repeated `poll`,
an `issue` request, and `stop`. Requests are version-1 strict JSON with a
four-byte network-order length; duplicate keys, extra fields, arbitrary argv,
prompt, environment, tenant, or key fields are rejected. Requests are limited
to 4096 bytes. Serialized responses, including base64 overhead, are limited
to 16 MiB; raw JSONL/final bytes retain their 10 MiB/1 MiB limits. A whole
frame has a five-second deadline that partial reads cannot reset. The session
deadline is the configured CLI limit plus 30 seconds. Error replies contain
only a fixed code, without child stderr, DB details, paths, or secrets.

The server loads a private owned regular 32-byte Ed25519 key file without
following a final symlink. It chooses the observer settings and checks that
the version handshake and actual launch agree with the pinned binary. It
reserves `(schema, tenant, job, attempt)` with a session PostgreSQL advisory
lock before spawning and rejects an existing launch row. Reservation is
shared across server instances and released when that DB connection closes.
Supervisor DB reads use a connection timeout and statement timeout and request
read-only transactions. These settings do not establish deployed DB grants.
The trusted contract and evidence readers must still be correctly scoped.

A background monitor observes completion/output bounds and checks the same
attempt, input/stage, live lease or valid closed state, and cancellation.
Disconnect, framing errors, normal stop, session expiry, and graceful SIGTERM
close/reap the child and remove temporary credentials. A hard supervisor crash
or SIGKILL still requires an independently tested service/cgroup cleanup policy;
that proof is absent. Observation is kept only in this session. Reconnection
or restart cannot reconstruct it from JobStore or sign a previous capture.
A repeat `issue` must retain capture, decision, and request UUIDs and recheck
the live/closed scope before returning its cached signature. Partial frames
close the client connection; retry on such a stream is not supported.

The supervised `CliWorker` has no CLI executable, home, credential, or signing
key configuration. It claims/recover-expires only its configured tenant, stores
the frozen invocation, records the returned launch, renews its lease, and
persists raw output/capture/validated decision. Before terminal closure it
ingests the signed record and calls `ExecutionVerifier.verify_pending` to
check signature, pins, actual byte/ID binding, validation receipt, live attempt,
lease, and cancellation. The existing conditional JobStore transition checks
lease/cancellation again. The thermal publisher continues to use the separate
completed `collection_review` verifier and its release/planning-event gates.
No thermal G1 publication is authorized by the pending check.

The IPC tests use a **separate local supervisor process with the same OS UID,
fake CLI, test key, synthetic authority, and owner DB access**. They cover all
three AI stages, proceed/hold, child cleanup, wrong peer/tenant/binary metadata,
simultaneous attempt reservation, absent/bad signatures, changed raw JSONL,
and cancellation during cached issuance. This establishes the software path;
it does not establish independent private-key control, least-privilege roles,
immutable binary/image identity, actual model execution, or production service
supervision. The synthetic-only worker guard and G1/G4 holds remain active.

G1 remains HOLD until the separately controlled supervisor directly observes
an actual CLI child, signs after durable capture with a private key outside
request/worker control, and production PostgreSQL 18 roles prohibit the
request/worker from writing authoritative invocation, capture, receipt,
decision, publication, and execution-attestation rows. The publisher must
verify that signed record, the separately issued thermal software release,
and a server-authorized planning event. G4 additionally requires per-job
isolation, restricted egress, deployment/account and operating evidence.

The subsequent [runtime role policy candidate](runtime-role-policy-v1.md)
provides explicit closed request/worker profiles, supervisor reads and authority
writes with effective privilege audits. Its fake-child test uses restricted SQL
identities for durable mutation and issuer reads. The IPC worker's direct
JobStore calls still need a trusted authority RPC before using the worker
profile. Login/UID/key separation and deployment are not established by that
administrator-controlled SQL test.

Local verification on 2026-09-28 used PostgreSQL 16.15 and the locked backend:
`OSSF_TEST_PG_DSN=… uv run --locked --group dev pytest -q` completed with
**1,075 passed, 0 skipped**, including 34 new IPC/service/worker cases, and two
preexisting Pydantic serializer warnings. No actual model invocation was used
in these execution tests. One exact CLI call supplied the narrow architecture
review above; it was not a signed execution or deployment acceptance run.
