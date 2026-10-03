# Actual CLI synthetic thermal review smoke

Observed locally on 2026-09-27 UTC against the disposable PostgreSQL 16.15 test
schema and `codex-cli 0.157.1`. The command was
`OSSF_TEST_PG_DSN=<private local DSN> bash scripts/run-cli-smoke.sh --thermal`.
The script copied the existing private credential into a temporary Codex home,
ran one opt-in test, then removed that home and the database fixture schema.
The test did not print or retain the credential, prompt, final JSON, or JSONL
payload in this file.

`tests/test_thermal_cli_smoke.py::test_real_cli_synthetic_thermal_review` passed
in 14.01 seconds. A real subprocess invoked `gpt-6-sol` with
`model_reasoning_effort="xhigh"`, the pinned output schema, and the CLI
read-only sandbox. Its `collection_review` response passed the server's
`ThermalReviewContract`, and `JobStore` recorded a succeeded decision. The
publisher then accepted two recarried synthetic thermal traces into one
tenant-scoped Run **using its fixture execution verifier and fixture HMAC
release authority**.

| Evidence item | Observed value |
| --- | --- |
| Job ID | `48c76aa2-581f-4b5f-bda7-51fdeb15ca69` |
| Capture ID | `a6248fb3-1e38-4f7c-b8a4-c1c52fbfe75f` |
| Decision ID | `7ce7a1f1-a7c8-445a-9aad-5f5c4c622827` |
| JSONL SHA-256 | `56c84184871ae9f14263457915ac0746be188f79474f5b8f361e793a7daa001f` |
| Final SHA-256 | `bb0891643941576d2a9097d48adbaba29fa0bc5473c20e2bc258a4b697c7d5fa` |
| Synthetic Run ID | `synthetic-thermal-v1:e486561b28d1e52e25d7c99a41b337178d82c0ec02f349360ecce04757564e26` |
| First accepted trace SHA-256 | `1ffee4a7a95f09e2ba1b56e84e647543fd3aca9ef81fe7727fea867f06f17b0e` |
| Second accepted trace SHA-256 | `7b87b1262c2596ea1cf446b5c78d3a8c58bcfcc226fad128cd2b5973eac1029e` |
| CLI reported usage | 14,538 input; 0 cached input; 435 output; 222 reasoning output tokens |

This is a local integration observation, not the `thermal-g1-publisher` or
`end-to-end-g1` acceptance. The test setup also creates an earlier synthetic
fixture review job; the IDs above belong to the later real CLI review. Its
publisher dependencies use a mocked independent process verifier, arbitrary
planning-event hash, test authority keys, test release evidence, and a schema
owner database role. The CLI ran in the `synthetic_smoke=True` mode, not an
attested per-job product container. The flow did not start the research and
assessment stages, HTTP submission, economic calculation, or browser replay.
No real source G0, independent G1 authority, field G2, crop/economic G3, or
operations G4 claim follows. The reported token counts are not a bill.
