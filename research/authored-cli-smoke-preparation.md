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
