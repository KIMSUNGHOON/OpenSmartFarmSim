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
The current `CliWorker` does not yet delegate launch to that supervisor and its
default production constructor remains closed. Same-process HMAC and internally
consistent JSONL cannot prove that a separate process ran.

The canonical UTF-8 JSON record includes a version and key ID; tenant, job,
attempt and attempt ID; frozen job input SHA-256 and unique v4 nonce; CLI version,
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
executable/environment digests, final and JSONL hashes, usage, process ID and
chronology against the existing durable JobStore capture. It also calls the
JobStore's raw capture validator before it returns true. A valid-looking
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

G1 remains HOLD until the separately controlled supervisor directly observes
an actual CLI child, signs after durable capture with a private key outside
request/worker control, and production PostgreSQL 18 roles prohibit the
request/worker from writing authoritative invocation, capture, receipt,
decision, publication, and execution-attestation rows. The publisher must
verify that signed record, the separately issued thermal software release,
and a server-authorized planning event. G4 additionally requires per-job
isolation, restricted egress, deployment/account and operating evidence.
