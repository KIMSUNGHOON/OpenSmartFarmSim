# CLI model policy migration v1

Effective 2026-10-01, the user's required development and product runtime model
is **Codex CLI `gpt-6.1-sol` with `xhigh`**, replacing `gpt-6-sol` with `xhigh`.
The [official model page](https://developers.openai.com/api/docs/models/gpt-6.1-sol)
documents this model ID and effort support. The
[Codex configuration reference](https://learn.chatgpt.com/docs/config-file/config-reference)
documents trusted project configuration and `model_reasoning_effort`.
The repository's `.codex/config.toml` supplies development defaults. Product
workers still pass explicit `-m gpt-6.1-sol -c 'model_reasoning_effort="xhigh"'`
under `--ignore-user-config`; configuration defaults are not execution proof.

## New execution and historical evidence

Invocation admission, separate supervisor issuance, signed execution verification,
authored review completion and thermal publication require the new exact model.
The thermal independent review method is `codex_cli_gpt-6.1-sol_xhigh`.
Old model rows, raw evidence, hashes, signatures, immutable synthetic fixtures,
past reviews and archived white papers retain their actual recorded model.
They do not certify a new-model invocation. An old argv or invocation cannot
authorize a new publication through the current verifier. Historical records
remain available for audit; release or read paths requiring current verification
can hold until a new review and independent release exist. Code changes also
change current release code pins; do not rewrite or re-sign old evidence.

## Explicit owner migration

Fresh `install_schema` installations use the named
`attempt_invocations_cli_policy` CHECK and accept only the new CLI model/effort,
or the existing explicitly synthetic fixture mode with NULL model/effort.
Existing schemas require `app.db.upgrade_cli_model_policy(conn, schema)`.
Stop admission and drain CLI work before coordinating the application and DB
cutover. Use the schema owner's connection with `psycopg.rows.dict_row`:

```python
import psycopg
from psycopg.rows import dict_row
from app.db import upgrade_cli_model_policy

with psycopg.connect(owner_dsn, row_factory=dict_row) as conn:
    upgrade_cli_model_policy(conn, schema)
```

`owner_dsn` and `schema` come from the operator's existing private configuration;
run with the backend on `PYTHONPATH`. This is not automatic startup migration.
No runtime role receives schema-owner credentials or DDL authority.

The migration locks `attempt_invocations` in its transaction and recognizes
only the exact previous or target CHECK expression under its known names.
Unknown or additional model/effort checks fail closed without removing them.
It atomically replaces the known constraint with the new CHECK **NOT VALID**:
PostgreSQL enforces it for new rows without rejecting historical rows already
stored under the old model ([PostgreSQL ALTER TABLE](https://www.postgresql.org/docs/18/sql-altertable.html)). Audit immutability triggers and all other constraints
stay in place. No row is updated or deleted. Do not validate the new constraint
against mixed-model history or synthesize replacement invocation records.
Repeated calls return without changing a recognized target policy.

For application rollback, stop and drain work again and call
`app.db.downgrade_cli_model_policy(conn, schema)` with the same owner connection.
Then restore the matching previous application version. The inverse CHECK is
also NOT VALID, so later new-model rows remain immutable audit history while
new writes must match the previous policy. A failed cutover transaction restores
the original constraint. Schema owner DDL can alter authority; the runtime
trust boundary still requires separate process observation and current gates.

## Evidence limits

The focused [migration tests](../backend/tests/test_cli_model_migration.py)
exercise fresh and upgraded SQL rejection, unchanged historical rows,
idempotent upgrade/down, current write policy after down, unknown-policy refusal
and interruption after dropping the old constraint. Local evidence uses
PostgreSQL 16.15; PostgreSQL 18 is checked separately by hosted CI.
The [implementation record](../research/cli-model-migration-implementation.md)
distinguishes software tests, current development session and actual product
runtime execution. New-model account cost/access, independent release and
G1/G4 remain subject to their existing evidence requirements.
