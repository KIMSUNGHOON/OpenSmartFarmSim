"""Opt-in SQL grants under actual SCRAM; schema-only synthetic result metadata."""
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
from app import crop_climate_joint_result_schema as schema
from app.crop_cycle_calculation_result_schema import install_calculation_cycle_crop_result_schema
from app.runtime_login import connect_runtime
from app.runtime_roles import RuntimeLoginPolicy, RolePolicyHold, audit_runtime_roles, install_runtime_roles
from app.thermal_run_store import _canonical
from login_database import login_database
from test_jobs import synthetic_principal
from test_runtime_roles import owned_scope
from test_crop_cycle_result_schema import fixture_row, metadata as old_metadata, insert as old_insert
from test_crop_climate_joint_result_schema import insert, owner, payload, forbid_equations
from test_operator_config import private_config, isolated_assembly, store as store_config

FLAG = 'crop_climate_joint_result_storage'
OLD_TABLES = ('crop_cycle_research_results', 'crop_cycle_verified_research_results')


def save(name, value):
    directory = os.environ.get('OSSF_JOINT_ROLES_EVIDENCE')
    if directory:
        with (Path(directory)/name).open('x') as handle:
            os.fchmod(handle.fileno(), 0o400)
            json.dump(value, handle, sort_keys=True, indent=2); handle.flush(); os.fsync(handle.fileno())


@pytest.fixture(scope='module', autouse=True)
def cleanup(login_database):
    yield
    with psycopg.connect(login_database['admin']) as conn:
        schemas = conn.execute("SELECT count(*) FROM pg_namespace WHERE nspname LIKE 'login_test_%'").fetchone()[0]
        roles = conn.execute("SELECT count(*) FROM pg_roles WHERE rolname LIKE 'login_%'").fetchone()[0]
    save('database-cleanup.json', {'schemas': schemas, 'roles': roles}); assert schemas == roles == 0


@pytest.fixture
def role_schema(login_database, tmp_path, request):
    mode = getattr(request, 'param', 'true'); database = login_database
    name = 'login_test_'+uuid4().hex
    base = JobStore(database['admin'], name, tmp_path/'artifacts', principal_provider=synthetic_principal)
    with base.connect() as conn:
        conn.execute(sql.SQL('CREATE SCHEMA {}').format(sql.Identifier(name))); install_schema(conn, name)
    suffix = uuid4().hex
    options = {} if mode == 'omitted' else {FLAG: mode != 'false'}
    policy = RuntimeLoginPolicy(name, 'login_owner_'+suffix, 'login_'+suffix, database['database'],
        crop_cycle_result_storage=True, crop_cycle_calculation_result_storage=True, **options)
    passfiles = []
    try:
        with owned_scope(base, policy):
            old = fixture_row(base, policy)
            verified = {**old, 'result_id': 'crop-cycle-verified-result-v1:'+'1'*64,
                        'artifact_ref': 'crop-cycle-verified-artifact-v1:'+'3'*64}
            value = old_metadata(verified); value['schema_version'] = 'crop-cycle-verified-result-v1'
            raw = _canonical(value); verified.update(payload_raw=raw, payload_sha256=sha256(raw).hexdigest())
            with base.connect() as conn:
                owner(conn, policy); old_insert(conn, policy, old)
                install_calculation_cycle_crop_result_schema(conn, name); insert(conn, policy, verified, OLD_TABLES[1])
                before = [conn.execute(sql.SQL('SELECT * FROM {}').format(sql.Identifier(name, t))).fetchall() for t in OLD_TABLES]
                if mode != 'uninstalled': schema.install_joint_crop_climate_result_schema(conn, name)
            dsns = {}
            if mode != 'uninstalled':
                with base.connect() as conn: install_runtime_roles(conn, policy)
                for kind, role in policy.roles.items():
                    password = secrets.token_hex(32); passfile = tmp_path/(kind+'.pgpass'); passfiles.append(passfile)
                    passfile.write_text(f"{database['host']}:{database['port']}:{database['database']}:{role}:{password}\n"); passfile.chmod(0o600)
                    with base.connect() as conn:
                        conn.execute("SET LOCAL log_statement='none'"); conn.execute("SET LOCAL log_min_duration_statement=-1")
                        conn.execute("SET LOCAL log_min_error_statement='panic'")
                        verifier = conn.pgconn.encrypt_password(password.encode(), role.encode(), b'scram-sha-256')
                        conn.execute(sql.SQL('ALTER ROLE {} PASSWORD {}').format(sql.Identifier(role), sql.Literal(verifier.decode())))
                    dsns[kind] = make_conninfo(host=database['host'], port=database['port'], dbname=database['database'],
                        user=role, passfile=str(passfile), sslmode='disable')
            row = payload({'tenant_id': old['tenant_id'], 'study_id': 'joint-role-study', 'revision': 'r1',
                'result_id': 'joint-crop-climate-result-v1:'+'1'*64,
                **{k: old[k] for k in ('scenario_id', 'scenario_revision', 'registration_job_id', 'registration_sha256')},
                'crop_id': 'schema-crop', 'batch_id': 'schema-batch', 'zone_id': 'schema-zone', 'program_id': 'schema-program',
                **{k: '2'*64 for k in ('source_sha256', 'context_sha256', 'time_binding_sha256', 'evidence_sha256',
                    'artifact_sha256', 'artifact_header_sha256', 'intent_sha256', 'farm_binding_sha256', 'head_sha256', 'proof_sha256')},
                'integrity_signature': '3'*64, 'artifact_ref': 'joint-crop-climate-storage-research-v1:'+'2'*64,
                'artifact_status': 'completed', 'steps': 16, 'planned_steps': 16, 'sample_count': 3,
                'event_count': 3, 'commit_count': 4, 'storage_bytes': 2048, 'file_count': 12,
                'registered_by': policy.roles['authority'], 'start_utc': '2026-10-01T00:00:00.123456Z',
                'end_utc': '2026-10-01T00:00:32.123456Z'})
            yield base, policy, dsns, row
            with base.connect() as conn:
                after = [conn.execute(sql.SQL('SELECT * FROM {}').format(sql.Identifier(name, t))).fetchall() for t in OLD_TABLES]
            assert after == before
            save(request.node.name+'-preservation.json', {'legacy_tables': list(OLD_TABLES), 'unchanged_rows': [1, 1]})
    finally:
        for passfile in passfiles: passfile.unlink(missing_ok=True)
        with base.connect() as conn: conn.execute(sql.SQL('DROP SCHEMA {} CASCADE').format(sql.Identifier(name)))


def test_flag_is_explicit_exact_boolean_and_defaults_false():
    policy = RuntimeLoginPolicy('test_schema', 'test_owner', 'test_roles', 'postgres')
    assert getattr(policy, FLAG) is False
    bad = (None, 0, 1, 'true', 'false', [], {}, 0.0, 1.0, b'true')
    for value in bad:
        with pytest.raises(RolePolicyHold): replace(policy, **{FLAG: value})
    assert replace(policy, **{FLAG: True}).crop_climate_joint_result_storage is True
    save('policy.json', {'default': False, 'bad_types_rejected': len(bad)})


def test_existing_operator_versions_accept_only_missing_or_false_joint_flag(private_config, monkeypatch):
    from app import operator_config as original
    from app import calculation_operator_config as calculation
    path, document = private_config; calls = isolated_assembly(monkeypatch)
    before = len(os.listdir('/proc/self/fd')); accepted = denied = 0
    for loader, version in ((original.load_api_runtime, 'operator-api-config-v1'),
                            (calculation.load_calculation_api_runtime, calculation.VERSION)):
        for value in ('omitted', False, True, None, 0, 1, 'false', [], {}):
            body = json.loads(json.dumps(document)); body['config_version'] = version
            if version == calculation.VERSION: body['policy']['crop_cycle_calculation_result_storage'] = False
            if value == 'omitted': body['policy'].pop(FLAG, None)
            else: body['policy'][FLAG] = value
            store_config(path, body); previous = len(calls)
            if value == 'omitted' or value is False:
                assert loader(path)[0] == 'assembled' and getattr(calls[-1].policy, FLAG) is False
                assert len(calls) == previous+1; accepted += 1
            else:
                with pytest.raises(original.OperatorConfigHold): loader(path)
                assert len(calls) == previous; denied += 1
    assert len(os.listdir('/proc/self/fd')) == before
    save('operator-compatibility.json', {'accepted_missing_or_false': accepted,
        'rejected_true_or_bad_types_before_factory': denied, 'FD_before_after': [before, before]})


@pytest.mark.parametrize('role_schema', ['omitted', 'false', 'true'], indirect=True)
def test_actual_scram_matrix_roundtrip_and_old_grants_preserved(role_schema, request):
    base, policy, dsns, row = role_schema; target = sql.Identifier(policy.schema, schema.TABLE)
    enabled = getattr(policy, FLAG); allowed = denied = 0
    with base.connect() as conn:
        assert audit_runtime_roles(conn, policy)['tables'] > 0
        privileges = ['SELECT', 'INSERT', 'UPDATE', 'DELETE', 'TRUNCATE', 'REFERENCES', 'TRIGGER']
        if conn.info.server_version >= 170000: privileges.append('MAINTAIN')
        for kind, role in policy.roles.items():
            for table in (*OLD_TABLES, schema.TABLE):
                for privilege in privileges:
                    actual = conn.execute('SELECT has_table_privilege(%s,%s,%s) AS allowed',
                        (role, policy.schema+'.'+table, privilege)).fetchone()['allowed']
                    assert actual == (kind == 'authority' and privilege in ('SELECT', 'INSERT') and (table in OLD_TABLES or enabled))
    for kind, dsn in dsns.items():
        for operation in ('SELECT', 'INSERT', 'UPDATE', 'DELETE', 'TRUNCATE'):
            with connect_runtime(dsn, policy, kind) as conn:
                assert conn.pgconn.used_password and conn.info.get_parameters()['require_auth'] == 'scram-sha-256'
                server_version = conn.info.server_version
                if kind == 'supervisor': conn.execute('SET TRANSACTION READ WRITE')
                if enabled and kind == 'authority' and operation in ('SELECT', 'INSERT'):
                    if operation == 'INSERT': insert(conn, policy, row)
                    else: conn.execute(sql.SQL('SELECT * FROM {} LIMIT 0').format(target))
                    allowed += 1
                else:
                    with pytest.raises(errors.InsufficientPrivilege):
                        if operation == 'INSERT': insert(conn, policy, row)
                        else: conn.execute(sql.SQL({'SELECT': 'SELECT * FROM {} LIMIT 0', 'UPDATE': 'UPDATE {} SET revision=revision',
                            'DELETE': 'DELETE FROM {}', 'TRUNCATE': 'TRUNCATE {}'}[operation]).format(target))
                    denied += 1
    if enabled:
        with connect_runtime(dsns['authority'], policy, 'authority') as conn:
            actual = conn.execute(sql.SQL('SELECT * FROM {}').format(target)).fetchone()
            assert bytes(actual['payload_raw']) == row['payload_raw'] and actual['payload_sha256'] == row['payload_sha256']
            assert (actual['start_utc'], actual['end_utc']) == (row['start_utc'], row['end_utc'])
    else:
        with base.connect() as conn, pytest.raises(RolePolicyHold): audit_runtime_roles(conn, replace(policy, **{FLAG: True}))
    for kind in ('request', 'worker', 'supervisor'):
        for role in (policy.owner, policy.roles['authority']):
            with connect_runtime(dsns[kind], policy, kind) as conn, pytest.raises(errors.InsufficientPrivilege):
                conn.execute(sql.SQL('SET ROLE {}').format(sql.Identifier(role)))
    save('matrix-'+request.node.callspec.params['role_schema']+'.json', {'enabled': enabled,
        'allowed_statements': allowed, 'denied_statements': denied, 'postgres_server_version': server_version,
        'table_privilege_checks': 4*3*len(privileges), 'role_escalations_denied': 6,
        'same_raw_UTC_roundtrip': enabled, 'old_grants_preserved': True, 'equation_calls': 0})


@pytest.mark.parametrize('role_schema', ['uninstalled'], indirect=True)
def test_true_requires_preinstalled_table_and_atomic_fresh_roles(role_schema):
    base, policy, _, _ = role_schema
    for check in (audit_runtime_roles, install_runtime_roles):
        with base.connect() as conn, pytest.raises(RolePolicyHold): check(conn, policy)
    with base.connect() as conn:
        assert conn.execute('SELECT count(*) AS n FROM pg_roles WHERE rolname=ANY(%s)',
                            (list(policy.roles.values()),)).fetchone()['n'] == 0
    save('missing-table.json', {'audit_rejected': True, 'install_rejected': True, 'runtime_roles_created': 0})


def test_new_table_column_routine_grant_option_and_membership_drift_fail_audit(role_schema):
    base, policy, _, _ = role_schema; target = sql.Identifier(policy.schema, schema.TABLE)
    roles = {k: sql.Identifier(v) for k, v in policy.roles.items()}
    statements = [sql.SQL('GRANT SELECT ON {} TO PUBLIC').format(target),
        sql.SQL('GRANT SELECT(result_id) ON {} TO {}').format(target, roles['worker']),
        sql.SQL('GRANT UPDATE ON {} TO {}').format(target, roles['authority']),
        sql.SQL('GRANT SELECT ON {} TO {} WITH GRANT OPTION').format(target, roles['authority']),
        sql.SQL('GRANT EXECUTE ON FUNCTION {}() TO PUBLIC').format(sql.Identifier(policy.schema, 'reject_joint_crop_climate_result_change')),
        sql.SQL('GRANT SELECT ON {} TO {}').format(target, roles['request']),
        sql.SQL('GRANT SELECT ON {} TO {}').format(target, roles['supervisor']),
        sql.SQL('GRANT INSERT ON {} TO {}').format(target, roles['worker']),
        sql.SQL('GRANT UPDATE(result_id) ON {} TO {}').format(target, roles['authority']),
        sql.SQL('GRANT SELECT(result_id) ON {} TO PUBLIC').format(target),
        sql.SQL('GRANT TRUNCATE ON {} TO {}').format(target, roles['authority']),
        sql.SQL('GRANT {} TO {}').format(roles['authority'], roles['worker'])]
    with base.connect() as conn:
        for statement in statements:
            with conn.transaction(force_rollback=True):
                conn.execute(statement)
                with pytest.raises(RolePolicyHold): audit_runtime_roles(conn, policy)
            assert audit_runtime_roles(conn, policy)['tables'] > 0
        with pytest.raises(RolePolicyHold, match='already_exist'): install_runtime_roles(conn, policy)
    save('drift.json', {'rejected_mutations': len(statements), 'baseline_audit_restored_each_time': True,
        'repeat_runtime_install_rejected': True})
