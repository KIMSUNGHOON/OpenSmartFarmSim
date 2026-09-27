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
