"""Real SQL/role contracts for verified result metadata; no crop output adoption."""
from dataclasses import replace
from hashlib import sha256
import json
import os
from pathlib import Path
import secrets
from uuid import uuid4

import psycopg
from psycopg import errors, sql
from psycopg.conninfo import make_conninfo
import pytest

from app.db import install_schema
from app.job_store import JobStore
from app.runtime_login import connect_runtime
from app.runtime_roles import RuntimeLoginPolicy, RolePolicyHold, audit_runtime_roles, install_runtime_roles
from app.thermal_run_store import _canonical
from login_database import login_database, login_scope
from test_jobs import synthetic_principal
from test_runtime_roles import owned_scope
from test_crop_cycle_result_schema import fixture_row, metadata, insert as insert_legacy

FLAG = 'crop_cycle_calculation_result_storage'
TABLE = 'crop_cycle_verified_research_results'
VERSION = 'crop-cycle-verified-result-v1'


def save_reference(name, value):
    directory = os.environ.get('OSSF_CALCULATION_DB_EVIDENCE')
    if directory:
        with (Path(directory) / name).open('x') as handle:
            os.fchmod(handle.fileno(), 0o400)
            json.dump(value, handle, indent=2, sort_keys=True)
            handle.write('\n'); handle.flush(); os.fsync(handle.fileno())


def test_new_storage_policy_is_explicit_and_defaults_to_false():
    policy = RuntimeLoginPolicy('test_schema', 'test_owner', 'test_roles', 'postgres')
    assert getattr(policy, FLAG, None) is False


@pytest.mark.parametrize('value', [None, 0, 1, 'true', [], {}])
def test_new_storage_policy_rejects_non_boolean(value):
    with pytest.raises(RolePolicyHold):
        RuntimeLoginPolicy('test_schema', 'test_owner', 'test_roles', 'postgres', **{FLAG: value})


def install(conn, schema):
    from app.crop_cycle_calculation_result_schema import install_calculation_cycle_crop_result_schema
    install_calculation_cycle_crop_result_schema(conn, schema)


@pytest.mark.parametrize('schema', [None, True, 12, 'bad-name', 'x;DROP SCHEMA public', 'a'*64, 'Mixed', ''])
def test_invalid_identifier_is_rejected_before_sql(schema):
    with pytest.raises(ValueError): install(None, schema)


def target(policy): return sql.Identifier(policy.schema, TABLE)


def owner(conn, policy): conn.execute(sql.SQL('SET LOCAL ROLE {}').format(sql.Identifier(policy.owner)))


def with_payload(row, value=None, raw=None):
    if value is None:
        value = metadata(row); value['schema_version'] = VERSION
    raw = _canonical(value) if raw is None else raw
    return {**row, 'payload_raw': raw, 'payload_sha256': sha256(raw).hexdigest()}


def insert(conn, policy, row):
    conn.execute(sql.SQL('INSERT INTO {} ({}) VALUES ({})').format(target(policy),
        sql.SQL(',').join(map(sql.Identifier, row)),
        sql.SQL(',').join(sql.Placeholder() for _ in row)), tuple(row.values()))


@pytest.fixture(scope='module')
def database_cleanup(login_database):
    yield
    with psycopg.connect(login_database['admin']) as conn:
        schemas = conn.execute("SELECT count(*) FROM pg_namespace WHERE nspname LIKE 'login_test_%'").fetchone()[0]
        roles = conn.execute("SELECT count(*) FROM pg_roles WHERE rolname LIKE 'login_%'").fetchone()[0]
    save_reference('database-cleanup.json', {'schemas_after': schemas, 'roles_after': roles})
    assert schemas == roles == 0


@pytest.fixture(autouse=True)
def forbid_crop_execution(monkeypatch):
    from app import crop_cycle_calculation_context as calculation
    def forbidden(*args, **kwargs): pytest.fail('schema/roles evaluated crop equations')
    monkeypatch.setattr(calculation, 'advance_chunk', forbidden)
    monkeypatch.setattr(calculation.legacy, 'advance_chunk', forbidden)
    monkeypatch.setattr(calculation.short._Evaluator, 'rhs', forbidden)


@pytest.fixture
def calculation_schema(login_database, database_cleanup, tmp_path, request):
    database = login_database; schema = 'login_test_' + uuid4().hex
    base = JobStore(database['admin'], schema, tmp_path/'artifacts', principal_provider=synthetic_principal)
    with base.connect() as conn:
        conn.execute(sql.SQL('CREATE SCHEMA {}').format(sql.Identifier(schema))); install_schema(conn, schema)
    suffix = uuid4().hex
    policy = RuntimeLoginPolicy(schema, 'login_owner_'+suffix, 'login_'+suffix,
        database['database'], crop_cycle_result_storage=True, **{FLAG: getattr(request, 'param', True)})
    passfiles = []
    try:
        with owned_scope(base, policy):
            old = fixture_row(base, policy)
            with base.connect() as conn:
                owner(conn, policy); insert_legacy(conn, policy, old)
                legacy_table = sql.Identifier(schema, 'crop_cycle_research_results')
                before = conn.execute(sql.SQL('SELECT * FROM {}').format(legacy_table)).fetchone()
                install(conn, schema)
                assert conn.execute(sql.SQL('SELECT * FROM {}').format(legacy_table)).fetchone() == before
            with base.connect() as conn: install_runtime_roles(conn, policy)
            dsns = {}
            for kind, role in policy.roles.items():
                password = secrets.token_hex(32); passfile = tmp_path/(kind+'.pgpass'); passfiles.append(passfile)
                passfile.write_text(f"{database['host']}:{database['port']}:{database['database']}:{role}:{password}\n")
                passfile.chmod(0o600)
                with base.connect() as conn:
                    conn.execute("SET LOCAL log_statement='none'")
                    conn.execute("SET LOCAL log_min_duration_statement=-1")
                    conn.execute("SET LOCAL log_min_error_statement='panic'")
                    verifier = conn.pgconn.encrypt_password(password.encode(), role.encode(), b'scram-sha-256')
                    conn.execute(sql.SQL('ALTER ROLE {} PASSWORD {}').format(sql.Identifier(role), sql.Literal(verifier.decode())))
                dsns[kind] = make_conninfo(host=database['host'], port=database['port'], dbname=database['database'],
                    user=role, passfile=str(passfile), sslmode='disable')
            row = with_payload({**old, 'result_id': VERSION+':'+'1'*64,
                'artifact_ref': 'crop-cycle-verified-artifact-v1:' + old['artifact_sha256']})
            yield base, policy, dsns, row, before
    finally:
        for passfile in passfiles: passfile.unlink(missing_ok=True)
        with base.connect() as conn: conn.execute(sql.SQL('DROP SCHEMA {} CASCADE').format(sql.Identifier(schema)))


def test_actual_scram_authority_roundtrip_and_same_intent_legacy_row_preserved(calculation_schema):
    base, policy, dsns, row, before = calculation_schema
    with connect_runtime(dsns['authority'], policy, 'authority') as conn:
        assert conn.pgconn.used_password and conn.info.get_parameters()['require_auth'] == 'scram-sha-256'
        server_version = conn.info.server_version
        insert(conn, policy, row)
        found = conn.execute(sql.SQL('SELECT * FROM {}').format(target(policy))).fetchone()
        assert bytes(found['payload_raw']) == row['payload_raw'] and found['recorded_at'].tzinfo
    with base.connect() as conn:
        assert audit_runtime_roles(conn, policy)['tables'] > 0
        old = conn.execute(sql.SQL('SELECT * FROM {}').format(sql.Identifier(policy.schema, 'crop_cycle_research_results'))).fetchone()
        assert old == before
    save_reference('schema-roundtrip.json', {'actual_scram': True, 'schema_version': VERSION,
        'postgres_server_version': server_version,
        'payload_bytes': len(row['payload_raw']), 'payload_sha256': row['payload_sha256'],
        'original_bytes_hash_time_preserved': True, 'same_tenant_study_revision': True,
        'whole_role_audit_passed': True, 'crop_RHS_calls': 0, 'actual_crop_Runs': 0})


@pytest.mark.parametrize('calculation_schema', [False, True], indirect=True)
def test_actual_four_roles_have_only_explicit_authority_select_insert(calculation_schema):
    _, policy, dsns, _, _ = calculation_schema
    for kind, dsn in dsns.items():
        for permission, query in (
            ('SELECT', sql.SQL('SELECT * FROM {} LIMIT 0').format(target(policy))),
            ('INSERT', sql.SQL('INSERT INTO {} SELECT * FROM {} WHERE false').format(target(policy), target(policy))),
            ('UPDATE', sql.SQL('UPDATE {} SET revision=revision').format(target(policy))),
            ('DELETE', sql.SQL('DELETE FROM {}').format(target(policy))),
            ('TRUNCATE', sql.SQL('TRUNCATE {}').format(target(policy)))):
            with connect_runtime(dsn, policy, kind) as conn:
                assert conn.pgconn.used_password
                if kind == 'supervisor': conn.execute('SET TRANSACTION READ WRITE')
                if getattr(policy, FLAG) and kind == 'authority' and permission in ('SELECT', 'INSERT'):
                    conn.execute(query)
                else:
                    with pytest.raises(errors.InsufficientPrivilege): conn.execute(query)


@pytest.mark.parametrize('path', [(), ('farm',), ('artifact',)])
@pytest.mark.parametrize('change', ['extra', 'missing', 'null'])
def test_sql_rejects_non_closed_metadata(calculation_schema, path, change):
    base, policy, _, row, _ = calculation_schema; value = json.loads(row['payload_raw']); node = value
    for key in path: node = node[key]
    if change == 'extra': node['untrusted'] = True
    elif change == 'missing': node.pop(next(iter(node)))
    elif path: value[path[0]] = None
    else: value = None
    with base.connect() as conn, pytest.raises(errors.CheckViolation):
        owner(conn, policy); insert(conn, policy, with_payload(row, value=value, raw=_canonical(value)))


@pytest.mark.parametrize('changes', [
    {'result_id': 'crop-cycle-result-v1:'+'1'*64},
    {'artifact_ref': 'crop-cycle-artifact-v1:'+'3'*64},
    {'artifact_ref': 'crop-cycle-verified-artifact-v1:'+'0'*64},
    {'steps': -1}, {'planned_steps': 0}, {'steps': 121}, {'planned_steps': 121},
    {'sample_count': -1}, {'event_count': -1}, {'commit_count': 0}, {'storage_bytes': 0}, {'file_count': 0},
    {'artifact_status': 'yielded'}, {'payload_sha256': '0'*64}, {'registration_job_id': str(uuid4())},
    {'tenant_id': 'foreign'}])
def test_sql_rejects_wrong_versions_counts_hash_or_tenant_job(calculation_schema, changes):
    base, policy, _, row, _ = calculation_schema
    changed = with_payload({**row, **changes})
    if 'payload_sha256' in changes: changed['payload_sha256'] = changes['payload_sha256']
    with base.connect() as conn, pytest.raises((errors.CheckViolation, errors.ForeignKeyViolation)):
        owner(conn, policy); insert(conn, policy, changed)


@pytest.mark.parametrize('column', ['sample_count', 'event_count', 'commit_count', 'storage_bytes', 'file_count'])
@pytest.mark.parametrize('edge', ['maximum', 'above'])
def test_upper_boundary_is_inclusive_and_excess_is_rejected(calculation_schema, column, edge):
    from app.crop_cycle_calculation_artifact import LIMITS
    from app.crop_cycle_input_stream import MAX_RECORDS
    base, policy, _, row, _ = calculation_schema
    maximum = {'sample_count': MAX_RECORDS, 'event_count': MAX_RECORDS, 'commit_count': LIMITS['commits'],
        'storage_bytes': LIMITS['directory_bytes'], 'file_count': LIMITS['files']}[column]
    changed = with_payload({**row, column: maximum + (edge == 'above')})
    with base.connect() as conn:
        owner(conn, policy)
        if edge == 'above':
            with pytest.raises(errors.CheckViolation), conn.transaction(): insert(conn, policy, changed)
        else:
            insert(conn, policy, changed)
            assert conn.execute(sql.SQL('SELECT {} FROM {}').format(sql.Identifier(column), target(policy))).fetchone()[column] == maximum


def test_numerical_hold_metadata_retains_partial_steps(calculation_schema):
    base, policy, _, row, _ = calculation_schema
    changed = with_payload({**row, 'artifact_status': 'hold', 'steps': 7})
    with base.connect() as conn:
        owner(conn, policy); insert(conn, policy, changed)
        actual = conn.execute(sql.SQL('SELECT artifact_status,steps,planned_steps FROM {}').format(target(policy))).fetchone()
        assert actual == {'artifact_status': 'hold', 'steps': 7, 'planned_steps': 120}


@pytest.mark.parametrize('kind', ['old-version', 'column-mismatch', 'duplicate', 'nonfinite', 'utf8', 'oversize'])
def test_sql_rejects_rehashed_wrong_json(calculation_schema, kind):
    from app.crop_cycle_calculation_result_schema import MAX_METADATA_BYTES
    base, policy, _, row, _ = calculation_schema; value = json.loads(row['payload_raw']); raw = None
    if kind == 'old-version': value['schema_version'] = 'crop-cycle-result-v1'
    elif kind == 'column-mismatch': value['artifact']['sample_count'] += 1
    elif kind == 'duplicate': raw = row['payload_raw'][:-1]+b',"status":"stored_unpublished_research"}'
    elif kind == 'nonfinite': raw = row['payload_raw'].replace(b'"binding":{}', b'"binding":{"bad":NaN}')
    elif kind == 'utf8': raw = b'\xff'
    else: raw = b' '*(MAX_METADATA_BYTES+1)
    with base.connect() as conn, pytest.raises((errors.CheckViolation, errors.InvalidTextRepresentation,
            errors.CharacterNotInRepertoire, errors.UntranslatableCharacter)):
        owner(conn, policy); insert(conn, policy, with_payload(row, value, raw))


def test_immutable_trigger_duplicates_and_new_revision(calculation_schema):
    base, policy, _, row, _ = calculation_schema
    with base.connect() as conn: owner(conn, policy); insert(conn, policy, row)
    for query in ('UPDATE {} SET revision=revision', 'DELETE FROM {}'):
        with base.connect() as conn, pytest.raises(errors.RaiseException):
            owner(conn, policy); conn.execute(sql.SQL(query).format(target(policy)))
    for changes in ({}, {'revision': 'r2'}, {'result_id': VERSION+':'+'7'*64}):
        with base.connect() as conn, pytest.raises(errors.UniqueViolation):
            owner(conn, policy); insert(conn, policy, with_payload({**row, **changes}))
    with base.connect() as conn:
        owner(conn, policy); insert(conn, policy, with_payload({**row, 'revision': 'r2', 'result_id': VERSION+':'+'7'*64}))
        assert conn.execute(sql.SQL('SELECT count(*) AS n FROM {}').format(target(policy))).fetchone()['n'] == 2


@pytest.mark.parametrize('drift', ['public-select', 'worker-column', 'authority-update', 'authority-grant', 'public-routine'])
def test_extra_table_column_or_routine_rights_fail_whole_audit(calculation_schema, drift):
    base, policy, _, _, _ = calculation_schema
    with base.connect() as conn:
        owner(conn, policy)
        if drift == 'public-routine':
            conn.execute(sql.SQL('GRANT EXECUTE ON FUNCTION {}() TO PUBLIC').format(sql.Identifier(policy.schema, 'reject_verified_cycle_crop_result_change')))
        elif drift == 'public-select': conn.execute(sql.SQL('GRANT SELECT ON {} TO PUBLIC').format(target(policy)))
        elif drift == 'worker-column': conn.execute(sql.SQL('GRANT SELECT (result_id) ON {} TO {}').format(target(policy), sql.Identifier(policy.roles['worker'])))
        elif drift == 'authority-update': conn.execute(sql.SQL('GRANT UPDATE ON {} TO {}').format(target(policy), sql.Identifier(policy.roles['authority'])))
        else: conn.execute(sql.SQL('GRANT SELECT ON {} TO {} WITH GRANT OPTION').format(target(policy), sql.Identifier(policy.roles['authority'])))
    with base.connect() as conn, pytest.raises(RolePolicyHold): audit_runtime_roles(conn, policy)


def test_opt_in_requires_table_and_grants(login_scope):
    base, policy, _ = login_scope; enabled = replace(policy, **{FLAG: True})
    with base.connect() as conn, pytest.raises(RolePolicyHold): audit_runtime_roles(conn, enabled)
    with base.connect() as conn: owner(conn, policy); install(conn, policy.schema)
    with base.connect() as conn: audit_runtime_roles(conn, policy)
    with base.connect() as conn, pytest.raises(RolePolicyHold): audit_runtime_roles(conn, enabled)


def test_fresh_install_rolls_back_without_jobs_and_reinstall_preserves_objects(calculation_schema):
    base, policy, _, row, _ = calculation_schema; extra = 'login_test_' + uuid4().hex
    with base.connect() as conn:
        conn.execute(sql.SQL('CREATE SCHEMA {} AUTHORIZATION {}').format(sql.Identifier(extra), sql.Identifier(policy.owner)))
    try:
        with base.connect() as conn:
            owner(conn, policy)
            with pytest.raises(errors.UndefinedTable): install(conn, extra)
            assert conn.execute('SELECT to_regclass(%s) AS relation', (extra+'.'+TABLE,)).fetchone()['relation'] is None
            assert conn.execute('SELECT count(*) AS n FROM pg_proc p JOIN pg_namespace n ON n.oid=p.pronamespace WHERE n.nspname=%s', (extra,)).fetchone()['n'] == 0
        with base.connect() as conn: owner(conn, policy); insert(conn, policy, row)
        with base.connect() as conn:
            owner(conn, policy)
            with pytest.raises(errors.DuplicateTable): install(conn, policy.schema)
            assert bytes(conn.execute(sql.SQL('SELECT payload_raw FROM {}').format(target(policy))).fetchone()['payload_raw']) == row['payload_raw']
    finally:
        with base.connect() as conn: conn.execute(sql.SQL('DROP SCHEMA {} CASCADE').format(sql.Identifier(extra)))
