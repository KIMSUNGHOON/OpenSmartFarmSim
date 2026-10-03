# Local Codex CLI schema smoke

Recorded 2026-09-27 UTC. This is an execution check for the planned runtime worker, not a source review or product decision.

- Installed binary: `codex-cli 0.157.1` (`codex --version`).
- Invocation: `codex exec -m gpt-6-sol -c 'model_reasoning_effort="xhigh"' -s read-only --ephemeral --json --output-schema /tmp/ossf_cli_smoke_schema.json -o /tmp/ossf_cli_smoke_final.json --skip-git-repo-check '<prompt>'` from `/tmp`.
- Prompt: `Return exactly the JSON object {"ok":true}. This is a local schema invocation smoke test; do not use tools or inspect files.` SHA-256 `9068bff9770e8ec4faf77338feafa23edc5872e27ec28e3b8720a2e86041e711`.
- Output schema: closed object requiring `ok: true`. Exact schema-file SHA-256 `690fb6ba6d07a51d0b352f48aa270ed0200a3d5a4d11cc8435fa057ec1250245`.
- Process exit: `0`. Last message: `{"ok":true}`; exact output-file SHA-256 `4062edaf750fb8074e7e83e0c9028c94e32468a8b6f1614774328ef045150f93`.
- JSONL event-file SHA-256 `51c32b4f911d6b7a60e754734910830d544d0a3225be022db7dabcb7b5f2d594`; `thread.started` ID `01a0e25d-2d3f-78a1-8378-35422b744f05`; `turn.completed` reports 13,733 input, 0 cached input, 25 output, and 8 reasoning output tokens. These are CLI reported usage counts, not a billing record.

The prompt and result contain no agricultural data. This check shows local CLI availability, exact invocation flags, JSONL events, and schema-shaped output for one trivial request. It does not exercise the three product stages, evidence store, isolation container, tenant authentication, rights, cost controls, or G0–G4 gates. Those remain separate acceptance work.
