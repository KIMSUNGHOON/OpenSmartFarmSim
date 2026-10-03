# Authored farm real CLI smoke preparation

Date: 2026-09-30. Status: prepared, **not executed**. This is an optional
synthetic software check toward the `end-to-end-g1` dependency; it does not
release a farm snapshot or satisfy G1 on its own.

The existing `scripts/run-cli-smoke.sh` now has `--authored`. In a separate
operator terminal with a protected disposable PostgreSQL SCRAM DSN and private
Codex credential, run from the repository root:

```bash
OSSF_TEST_PG_DSN='<private disposable DSN>' bash scripts/run-cli-smoke.sh --check
OSSF_TEST_PG_DSN='<private disposable DSN>' bash scripts/run-cli-smoke.sh --authored
```

Do not run this from an agent already inside the Codex CLI session. The
wrapper checks the CLI executable/version, credential ownership/mode and
database connection; it copies the credential into a private temporary
`CODEX_HOME` for the attempt and removes that copy afterward. The test builds
one self-authored synthetic farm registration and an immutable review job,
routes it through the existing owned service contract, and invokes actual
Codex CLI `gpt-6-sol` with `xhigh`. It checks the stored invocation, capture
hashes, usage, decision and review artifact. The printed receipt contains IDs,
hashes and token counts, not source bytes or credentials.

Preparation checks performed in the current CLI development session:

```text
bash -n scripts/run-cli-smoke.sh                                        passed
uv run --locked --group dev python -m py_compile
    tests/test_farm_authored_cli_smoke.py                               passed
OSSF_REAL_AUTHORED_CLI_SMOKE=1 uv run --locked --group dev pytest
    --collect-only -q tests/test_farm_authored_cli_smoke.py             1 collected
```

The actual model call, PostgreSQL test, independent execution attestation,
separate reviewer release, authored Run publication and browser replay were
not performed by these preparation checks. A model proposal is not an
approved release; the server and separate reviewer must still validate it.

## Opt-in real CLI to stored 3D path

The authenticated browser registration → new review job → actual Codex CLI
`gpt-6-sol`/`xhigh` review → synthetic observer and reviewer release →
deterministic worker → stored Run HTTPS/Chromium replay is also prepared as
`--authored-full` in the same wrapper. Run it only from a separate operator
terminal after the development CLI session has ended:

```bash
OSSF_TEST_PG_DSN='<private disposable DSN>' bash scripts/run-cli-smoke.sh --check
OSSF_TEST_PG_DSN='<private disposable DSN>' bash scripts/run-cli-smoke.sh --authored-full
```

The wrapper creates a private temporary CLI home and deletes it afterward.
The test records the actual invocation model and effort, attempt, capture and
decision IDs, CLI version and executable/environment digests, JSONL/final
hashes and token usage without printing prompt,
result bytes or credentials. The browser verifies the 120 stored timestamps
against the HTTPS Run. This **has not been executed with actual CLI** in this
session. Its observer and reviewer are still synthetic test authorities and
the source, economic and farm inputs are self-authored fixtures; success would
prove a wider software path, not independent G1 or product deployment.

The default fake-CLI path still passed the complete local PostgreSQL
16.15/SCRAM, HTTPS and Chromium test after this opt-in branch was added:
`1 passed in 240.07s`. That result checks the unchanged default path and
does not execute or validate the real CLI branch.

The opt-in branch was separately rehearsed by deliberately supplying a
test-owned executable that imitates the CLI JSONL protocol, with a dummy
private `auth.json`. PostgreSQL 16.15/SCRAM, HTTPS and Chromium completed with
`1 passed in 236.04s`; the synthetic attempt printed model/effort strings,
digests, one input/output token and a 120-point browser report. This checks
branch wiring and the test-authority receipt only. The executable digest in
that rehearsal is **not** a Codex CLI binary digest, so it is not entered as
actual CLI evidence or used to release G1.
