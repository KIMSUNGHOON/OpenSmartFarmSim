"""Model write-policy cutover with synthetic, immutable invocation history."""

from pathlib import Path
import sys

from psycopg import errors, sql
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.db import downgrade_cli_model_policy, upgrade_cli_model_policy
from test_jobs import pg_store, submit


def _previous_policy(store):
    with store.connect() as conn:
        table = store._table('attempt_invocations')
        conn.execute(sql.SQL('ALTER TABLE {} DROP CONSTRAINT attempt_invocations_cli_policy')
                     .format(table))
        conn.execute(sql.SQL("""
            ALTER TABLE {} ADD CHECK (
                (execution_kind = 'codex_cli'
                 AND cli_version ~ '^codex-cli [0-9]+[.][0-9]+[.][0-9]+$'
                 AND model IS NOT DISTINCT FROM 'gpt-6-sol'
                 AND reasoning_effort IS NOT DISTINCT FROM 'xhigh')
                OR (execution_kind = 'synthetic_fixture'
                    AND cli_version = 'synthetic_fixture'
                    AND model IS NULL AND reasoning_effort IS NULL))
        """).format(table))


def _values(store, key):
    job = submit(store, key=key)
    lease = store.claim(600)
    assert lease['job_id'] == job['job_id']
    evidence = [store.append_evidence('tenant-a', job['job_id'], 1,
        lease['lease_token'], kind=kind, payload=b'synthetic migration input',
        rights_ref='self_authored_fixture') for kind in ('prompt', 'output_schema')]
    return job, lease, dict(tenant_id='tenant-a', job_id=job['job_id'], attempt=1,
        attempt_id=lease['attempt_id'], input_sha256=job['input_sha256'],
        prompt_evidence_id=evidence[0]['evidence_id'], prompt_version='migration-v1',
        prompt_sha256=evidence[0]['sha256'], schema_evidence_id=evidence[1]['evidence_id'],
        schema_version='migration-v1', schema_sha256=evidence[1]['sha256'],
        execution_kind='codex_cli', cli_version='codex-cli 0.157.1',
        model='gpt-6.1-sol', reasoning_effort='xhigh')


def _insert(conn, store, values):
    return conn.execute(sql.SQL('INSERT INTO {} ({}) VALUES ({}) RETURNING *').format(
        store._table('attempt_invocations'),
        sql.SQL(',').join(map(sql.Identifier, values)),
        sql.SQL(',').join(sql.Placeholder() for _ in values)),
        tuple(values.values())).fetchone()


def _policy(conn, store):
    return conn.execute("""
        SELECT conname, convalidated, pg_get_expr(conbin, conrelid) AS expression
        FROM pg_constraint WHERE conrelid = %s::regclass
          AND conname IN ('attempt_invocations_check', 'attempt_invocations_cli_policy')
    """, (f'{store.schema}.attempt_invocations',)).fetchone()


@pytest.mark.parametrize('migrated', [False, True])
def test_new_sql_invocations_require_exact_model_effort_and_version(pg_store, migrated):
    if migrated:
        _previous_policy(pg_store)
        with pg_store.connect() as conn:
            upgrade_cli_model_policy(conn, pg_store.schema)
    else:
        with pg_store.connect() as conn:
            before = _policy(conn, pg_store)
            assert before['convalidated'] is True
            upgrade_cli_model_policy(conn, pg_store.schema)
            assert _policy(conn, pg_store) == before
    _, _, values = _values(pg_store, 'new-policy')
    for override in ({'model': 'gpt-6-sol'}, {'model': 'other'}, {'model': None},
                     {'reasoning_effort': 'high'}, {'reasoning_effort': None},
                     {'cli_version': 'unverified'},
                     {'execution_kind': 'synthetic_fixture', 'cli_version': 'synthetic_fixture'}):
        with pg_store.connect() as conn, pytest.raises(errors.CheckViolation):
            _insert(conn, pg_store, values | override)
    with pg_store.connect() as conn:
        assert _insert(conn, pg_store, values)['model'] == 'gpt-6.1-sol'


def test_upgrade_and_down_preserve_all_immutable_history_and_are_idempotent(pg_store):
    _previous_policy(pg_store)
    old_job, old_lease, values = _values(pg_store, 'previous-model')
    with pg_store.connect() as conn:
        historical = _insert(conn, pg_store, values | {'model': 'gpt-6-sol'})
        assert _policy(conn, pg_store)['conname'] == 'attempt_invocations_check'
        upgrade_cli_model_policy(conn, pg_store.schema)
        upgraded = _policy(conn, pg_store)
        assert upgraded['convalidated'] is False
        upgrade_cli_model_policy(conn, pg_store.schema)
        assert _policy(conn, pg_store) == upgraded
    assert pg_store.get_invocation('tenant-a', old_job['job_id'], 1) == historical
    assert pg_store.fail('tenant-a', old_job['job_id'], 1, old_lease['lease_token'],
                         'hold', 'synthetic_migration_end')
    new_job, new_lease, values = _values(pg_store, 'target-model')
    with pg_store.connect() as conn:
        current = _insert(conn, pg_store, values)
        downgrade_cli_model_policy(conn, pg_store.schema)
        restored = _policy(conn, pg_store)
        downgrade_cli_model_policy(conn, pg_store.schema)
        assert _policy(conn, pg_store) == restored
        assert restored['convalidated'] is False
        assert "'gpt-6-sol'" in restored['expression']
    assert pg_store.get_invocation('tenant-a', old_job['job_id'], 1) == historical
    assert pg_store.get_invocation('tenant-a', new_job['job_id'], 1) == current
    assert pg_store.fail('tenant-a', new_job['job_id'], 1, new_lease['lease_token'],
                         'hold', 'synthetic_migration_end')
    _, _, values = _values(pg_store, 'restored-model')
    with pg_store.connect() as conn, pytest.raises(errors.CheckViolation):
        _insert(conn, pg_store, values)
    with pg_store.connect() as conn:
        _insert(conn, pg_store, values | {'model': 'gpt-6-sol'})
        upgrade_cli_model_policy(conn, pg_store.schema)
    assert pg_store.get_invocation('tenant-a', old_job['job_id'], 1) == historical
    assert pg_store.get_invocation('tenant-a', new_job['job_id'], 1) == current


def test_upgrade_failure_rolls_back_constraint_drop_and_preserves_history(pg_store):
    _previous_policy(pg_store)
    job, _, values = _values(pg_store, 'rollback')
    with pg_store.connect() as conn:
        historical = _insert(conn, pg_store, values | {'model': 'gpt-6-sol'})
        before = _policy(conn, pg_store)

        class InterruptedConnection:
            transaction = conn.transaction

            def execute(self, query, params=None):
                if 'ADD CONSTRAINT attempt_invocations_cli_policy' in str(query):
                    raise RuntimeError('synthetic interruption after DROP')
                return conn.execute(query, params)

        with pytest.raises(RuntimeError, match='synthetic interruption'):
            upgrade_cli_model_policy(InterruptedConnection(), pg_store.schema)
        assert _policy(conn, pg_store) == before
    assert pg_store.get_invocation('tenant-a', job['job_id'], 1) == historical


@pytest.mark.parametrize('drift', ['name', 'expression', 'extra'])
def test_upgrade_rejects_unknown_policy_without_changing_schema(pg_store, drift):
    _previous_policy(pg_store)
    with pg_store.connect() as conn:
        table = pg_store._table('attempt_invocations')
        if drift == 'name':
            conn.execute(sql.SQL('ALTER TABLE {} RENAME CONSTRAINT attempt_invocations_check '
                                 'TO unknown_cli_policy').format(table))
        elif drift == 'expression':
            conn.execute(sql.SQL('ALTER TABLE {} DROP CONSTRAINT attempt_invocations_check')
                         .format(table))
            conn.execute(sql.SQL('ALTER TABLE {} ADD CONSTRAINT attempt_invocations_check '
                                 'CHECK (model IS NOT NULL)').format(table))
        else:
            conn.execute(sql.SQL('ALTER TABLE {} ADD CHECK (model IS NOT NULL)').format(table))
        def checks():
            return conn.execute('SELECT conname, pg_get_expr(conbin, conrelid) AS expression '
                                'FROM pg_constraint WHERE conrelid=%s::regclass '
                                'ORDER BY conname', (f'{pg_store.schema}.attempt_invocations',)).fetchall()
        before = checks()
        with pytest.raises(ValueError, match='known invocation policy'):
            upgrade_cli_model_policy(conn, pg_store.schema)
        assert checks() == before
