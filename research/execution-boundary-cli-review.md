# Independent CLI execution boundary review

On 2026-09-27 UTC, a local `codex-cli 0.157.1` session reviewed the narrow
execution-attestation problem. It ran from a private temporary directory with
a copied private credential and no repository or source data in the prompt.
The temporary home and JSONL were removed afterward. The CLI invocation used
`codex --ask-for-approval never exec -m gpt-6-sol -c
'model_reasoning_effort="xhigh"' --sandbox read-only --skip-git-repo-check
--ephemeral --ignore-user-config --json --output-last-message <private path>
-C <private path> -`. The prompt summarized the current JobStore/worker and
thermal publisher trust gap and requested a minimal independent observation
boundary and adversarial tests. The terminal `turn.completed` reported 14,073
input, 11,776 cached input, 1,650 output, and 1,034 reasoning output tokens.
These are CLI usage values, not a billed cost.

The final review's conclusions were:

1. A separately controlled supervisor must choose/hash and launch the exact
   CLI binary and arguments, own the output pipes, capture the raw JSONL and
   final bytes, observe exit via process wait, and sign only after durable
   capture. Request handlers and untrusted workers may submit frozen jobs but
   cannot report successful execution.
2. The signed completion record needs version/key ID, tenant/job/attempt and
   frozen request hash, fresh nonce, executable/argv/environment identities,
   process ID and start identity, capture/final hashes, times, exit status,
   and usage. Verification must bind it to the exact stored attempt and reject
   duplicate nonce, altered bytes, failed/incomplete exits and cross-tenant or
   cross-attempt reuse.
3. An authority-owned DB schema must deny direct bridge/attestation writes by
   request and worker roles. A publisher verifies the signature and linked
   capture before a G1 decision. A same-process HMAC or rechecked JSONL does
   not establish independent process observation.
4. An unprivileged host can implement and test the record protocol, signatures,
   grants and rejection cases as a candidate. G1 acceptance still needs an
   actually separate supervisor/key/DB authority, exact CLI execution there,
   and independent thermal release review. The existing local bwrap probe
   does not establish that deployment.

The implementation in [the attestation contract](../contracts/cli-execution-attestation-v1.md)
follows that boundary as a software candidate. This review does not attest
that the separate supervisor has been deployed.

## Follow-up: actual CLI input-byte binding

On 2026-09-27 UTC, a second private temporary `codex-cli 0.157.1` session
used the same `gpt-6-sol`/`xhigh`, read-only, ephemeral command form. Its
narrow prompt disclosed only the record and JobStore field lists and asked
whether unsigned actual stdin and output-schema bytes leave a binding gap.
The terminal usage was 46,913 input tokens (41,600 cached), 1,238 output
tokens (622 reasoning output). The CLI concluded that the separately controlled
observer must hash the bytes actually supplied to the child, sign both
`prompt_sha256` and `schema_sha256`, and the publisher must compare each with
both invocation and launch records. It proposed an adversarial case where the
job store retains prompt A but the child reads prompt B. This was a design
review; the local fake-child regression is not an independently deployed
observer or G1 execution proof.

## Follow-up: worker/supervisor IPC and recovery

On 2026-09-28 UTC, one private ephemeral `codex-cli 0.157.1` session used
the same exact `gpt-6-sol`/`xhigh` command form. The prompt summarized the
proposed bounded Unix socket protocol, configured UID/tenant scope, observer
and signing ownership, DB capture order, and disconnect/retry semantics.
It contained no repository files, farm/source data, credentials, or keys.
The terminal usage was 14,199 input (11,776 cached), 2,924 output, and 2,588
reasoning output tokens. The temporary credential, JSONL, and final file were
removed after extracting the review. These are usage counts, not billed cost.

The review identified five corrections adopted in the software candidate:

1. Check signature/pins/bound IDs while the job is still active; the existing
   thermal verifier separately requires a completed successful review.
2. Recheck cancellation/lease at issuance, including cached replies, and in
   the conditional terminal DB transition.
3. Reserve one authorized tenant/job/attempt before spawning. UID identity
   alone does not assign a job; a configured worker UID has its tenant scope.
4. Cache by the live session and stable request identity. A partial frame or
   broken connection cannot be retried as though the stream remained valid.
5. Require version registration and launch to describe the same pinned binary,
   and bound the serialized reply including base64/JSON overhead.

The resulting [contract](../contracts/cli-execution-attestation-v1.md#local-supervisor-ipc-candidate)
records the protocol and remaining same-UID/key/role/deployment limitations.
This review and the subsequent fake-child tests do not pass G1 or G4.

## Follow-up: closed PostgreSQL runtime grant increment

On 2026-09-28 UTC, a private ephemeral exact `gpt-6-sol`/`xhigh` CLI session
reviewed a narrow grant matrix: fresh non-login request/worker/supervisor/
authority roles, schema ownership outside runtime, no untrusted base-table
writes, restricted issuer reads and validated authority writes. The prompt
explicitly stated that current worker DB mutations still require authority RPC
and that no deployment/G1 claim was proposed. No source/farm data, secrets, or
repository files were supplied. Terminal usage was 14,124 input (11,776 cached),
1,358 output, and 1,034 reasoning output tokens; temporary files were removed.

The CLI accepted the bounded migration increment subject to column ACL cleanup,
global plus schema creator defaults, effective membership/login rights,
database/schema CREATE restrictions, reachable outside-schema definer checks,
and explicit sequence requirements. It required a post-commit catalog/effective
privilege audit, actual negative SQL access checks, positive authority/issuer
flows, stale-installer preservation, and transaction rollback tests. The
[role policy](../contracts/runtime-role-policy-v1.md) implements that candidate
with a dedicated owner and fresh profiles. Real login/service binding and
independent deployment remain unaccepted.
