"""Transient, owned preview namespace probe; never modifies original records."""
import argparse
from collections import Counter
from dataclasses import replace
from hashlib import sha256
import json
import os
from pathlib import Path
import secrets
import sys
from uuid import uuid4


def probe_ventilation(out, policy, dsn, original, original_directory, runtime, requests):
    import importlib.util
    from pytest import MonkeyPatch
    root = Path(__file__).resolve().parents[1]
    sys.path[:0] = [str(root/'backend/tests'), str(original_directory)]
    import joint_prefix_live_operator_v1 as previous_operator
    import test_crop_greenhouse_ventilation_execution_query as query_tests
    from app.crop_greenhouse_ventilation_execution import VentilationExecutionService
    from app.thermal_run_store import _canonical
    raw = runtime.read_bytes()
    config = json.loads(raw)
    operator_source = root/'research/crop-joint-ventilation-live-operator.py'
    operator_copy = out/'ventilation-operator.py'
    operator_copy.write_bytes(operator_source.read_bytes())
    operator_copy.chmod(0o400)
    spec = importlib.util.spec_from_file_location('owned_namespace_ventilation_operator', operator_copy)
    operator = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(operator)
    from dataclasses import asdict
    config = {**config, 'policy': asdict(policy), 'ventilation': {
        **config['ventilation'], 'custody': str(out/'ventilation-custody')}}
    (out/'ventilation-custody').mkdir(mode=0o700)
    prior = {**original, 'dsn': dsn}
    immutable = {runtime: sha256(raw).hexdigest()}
    for item in config['ventilation']['inputs'].values():
        for path in (Path(item['proof']), *Path(item['directory']).rglob('*')):
            if path.is_file():
                immutable[path] = sha256(path.read_bytes()).hexdigest()
    for key in ('rights_file', 'reviews_file'):
        path = Path(config['ventilation'][key])
        immutable[path] = sha256(path.read_bytes()).hexdigest()
    binding_count = 0
    with MonkeyPatch.context() as patch:
        calls = query_tests.forbid(patch)
        farms = operator.farms(config, prior, previous_operator)
        store = operator.ventilation_store(farms, config)
        admission = VentilationExecutionService(store.server.binding, input_resolver=store.server.input_resolver)
        admission._guard('tenant-1')
        for mode in ('completed', 'hold', 'cancel'):
            path = requests/(mode+'.json')
            request_file = path.read_bytes()
            immutable[path] = sha256(request_file).hexdigest()
            request = json.loads(request_file)
            request_raw = _canonical(request)
            directory, proof = admission._resolve('tenant-1', request)
            bound = admission.binding.prepare('tenant-1', request_raw, directory, proof)
            assert admission.binding.current('tenant-1', request_raw, directory, proof, bound) == bound
            assert admission.binding.current('tenant-1', request_raw, directory, proof, bound, write=True) == bound
            assert json.loads(bound)['G0_G4'] == 'not_assessed'
            binding_count += 1
        assert not any(calls.values())
    assert all(sha256(path.read_bytes()).hexdigest() == digest for path, digest in immutable.items())
    return {'new_model_farm_input_bindings_verified': binding_count,
            'native_new_namespace_authority_used': True, 'new_model_calculation_and_write_calls': calls,
            'input_files_proofs_keys_rights_unchanged': True}


def digest_rows(rows):
    return Counter(sha256(json.dumps(row, sort_keys=True, default=str).encode()).hexdigest()
                   for row in rows)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--original-directory', type=Path, required=True)
    parser.add_argument('--output-directory', type=Path, required=True)
    parser.add_argument('--ventilation-runtime', type=Path)
    parser.add_argument('--ventilation-requests', type=Path)
    parser.add_argument('--readmit-market-sources', action='store_true')
    args = parser.parse_args()
    assert bool(args.ventilation_runtime) == bool(args.ventilation_requests)
    assert not args.readmit_market_sources or args.ventilation_runtime
    out = args.output_directory
    out.mkdir(mode=0o700)
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]/'backend'))
    import psycopg
    from psycopg import errors, sql
    from psycopg.conninfo import make_conninfo
    from psycopg.rows import dict_row
    from app.db import install_schema, install_market_hold_schema
    from app.execution_attestation import install_execution_attestation_schema
    from app.thermal_run_store import install_thermal_run_schema
    from app.market_candidate_store import install_market_candidate_schema
    from app.market_result_store import install_market_result_schema
    from app.break_even_store import install_break_even_store_schema
    from app.market_source_store import install_market_source_schema
    from app.thermal_scenario_store import install_thermal_scenario_schema
    from app.crop_cycle_result_schema import install_cycle_crop_result_schema
    from app.crop_climate_joint_result_schema import install_joint_crop_climate_result_schema
    from app.crop_greenhouse_ventilation_result_schema import install_joint_ventilation_result_schema
    from app.runtime_roles import RuntimeLoginPolicy, audit_runtime_roles, install_runtime_roles

    original = json.loads((args.original_directory/'runtime.private.json').read_bytes())
    database = json.loads((args.original_directory/'database.private.json').read_bytes())
    old = RuntimeLoginPolicy(**original['policy'])
    enabled = {'market_calculation', 'break_even_calculation', 'market_source_storage',
               'thermal_scenario_storage', 'crop_cycle_result_storage',
               'crop_climate_joint_result_storage', 'crop_greenhouse_ventilation_result_storage'}
    assert {name for name, value in vars(old).items() if value is True} == enabled-{
        'crop_greenhouse_ventilation_result_storage'}
    suffix = uuid4().hex
    policy = replace(old, schema='model_test_'+suffix, owner='model_owner_'+suffix,
                     prefix='model_'+suffix, crop_greenhouse_ventilation_result_storage=True)
    admin = make_conninfo(host=database['socket'], port=database['port'], dbname=old.database,
                         user='ossf_preview_admin')
    owned_roles = [policy.owner, *policy.roles.values()]
    started = False
    passfiles = []
    checks = {'new_native_SCRAM_logins': 0, 'cross_namespace_denials': 0,
              'runtime_ddl_denials': 0}

    def tables(conn, schema):
        return [row['tablename'] for row in conn.execute(
            'SELECT tablename FROM pg_tables WHERE schemaname=%s ORDER BY tablename',
            (schema,)).fetchall()]

    def rows(conn, schema, names):
        return {name: digest_rows(conn.execute(sql.SQL('SELECT * FROM {}').format(
            sql.Identifier(schema, name))).fetchall()) for name in names}

    def original_catalog(conn):
        return {key: conn.execute(query, params).fetchall() for key, query, params in (
            ('schema', 'SELECT nspowner,nspacl FROM pg_namespace WHERE nspname=%s', (old.schema,)),
            ('relations', 'SELECT c.oid,c.relowner,c.relacl,c.relname FROM pg_class c '
             'JOIN pg_namespace n ON n.oid=c.relnamespace WHERE n.nspname=%s ORDER BY c.oid', (old.schema,)),
            ('columns', 'SELECT a.attrelid,a.attnum,a.attacl FROM pg_attribute a JOIN pg_class c '
             'ON c.oid=a.attrelid JOIN pg_namespace n ON n.oid=c.relnamespace '
             'WHERE n.nspname=%s ORDER BY a.attrelid,a.attnum', (old.schema,)),
            ('roles', 'SELECT oid,rolname,rolsuper,rolinherit,rolcreaterole,rolcreatedb,rolcanlogin,'
             'rolreplication,rolconnlimit,rolvaliduntil,rolbypassrls FROM pg_roles '
             'WHERE rolname=ANY(%s) ORDER BY oid', ([old.owner, *old.roles.values()],)),
            ('defaults', 'SELECT d.* FROM pg_default_acl d JOIN pg_roles r ON r.oid=d.defaclrole '
             'WHERE r.rolname=%s ORDER BY d.oid', (old.owner,)),
        )}

    def denied(conn, statement):
        try:
            with conn.transaction():
                conn.execute(statement)
        except errors.InsufficientPrivilege:
            return
        raise AssertionError('cross-namespace or DDL permission unexpectedly allowed')

    def database_acl(conn):
        return conn.execute("SELECT a.* FROM pg_database d, LATERAL "
            "aclexplode(coalesce(d.datacl,acldefault('d',d.datdba))) a WHERE d.datname=%s "
            "ORDER BY a.grantor,a.grantee,a.privilege_type,a.is_grantable", (old.database,)).fetchall()

    with psycopg.connect(admin, row_factory=dict_row) as conn:
        conn.execute('SET TRANSACTION READ ONLY')
        audit_runtime_roles(conn, old)
        assert not conn.execute("SELECT 1 FROM pg_database d, LATERAL "
            "aclexplode(coalesce(d.datacl,acldefault('d',d.datdba))) a "
            "WHERE d.datname=%s AND a.grantee=0 AND a.privilege_type='CREATE'",
            (old.database,)).fetchone()
        names = tables(conn, old.schema)
        assert len(names) == 27
        before_rows = rows(conn, old.schema, names)
        old_sources = conn.execute(sql.SQL('SELECT * FROM {}').format(
            sql.Identifier(old.schema, 'market_source_records'))).fetchall()
        before_catalog = original_catalog(conn)
        before_database_acl = conn.execute('SELECT datacl FROM pg_database WHERE datname=%s',
                                          (old.database,)).fetchone()
        before_database_privileges = database_acl(conn)
        assert not conn.execute('SELECT 1 FROM pg_roles WHERE rolname=ANY(%s)', (owned_roles,)).fetchone()

    try:
        with psycopg.connect(admin, row_factory=dict_row) as conn:
            conn.execute('SET TRANSACTION ISOLATION LEVEL REPEATABLE READ')
            conn.execute(sql.SQL('CREATE ROLE {} NOLOGIN NOSUPERUSER NOCREATEDB NOCREATEROLE '
                                'NOREPLICATION NOBYPASSRLS').format(sql.Identifier(policy.owner)))
            conn.execute(sql.SQL('CREATE SCHEMA {} AUTHORIZATION {}').format(
                sql.Identifier(policy.schema), sql.Identifier(policy.owner)))
            conn.execute(sql.SQL('SET LOCAL ROLE {}').format(sql.Identifier(policy.owner)))
            for install in (install_schema, install_execution_attestation_schema,
                            install_thermal_run_schema, install_market_hold_schema,
                            install_market_candidate_schema, install_market_result_schema,
                            install_break_even_store_schema, install_market_source_schema,
                            install_thermal_scenario_schema, install_cycle_crop_result_schema,
                            install_joint_crop_climate_result_schema, install_joint_ventilation_result_schema):
                install(conn, policy.schema)
            conn.execute('RESET ROLE')
            assert tables(conn, policy.schema) == names
            dependencies = {name: set() for name in names}
            for row in conn.execute('''SELECT c.relname AS child, p.relname AS parent
                    FROM pg_constraint f JOIN pg_class c ON c.oid=f.conrelid
                    JOIN pg_class p ON p.oid=f.confrelid
                    JOIN pg_namespace n ON n.oid=c.relnamespace
                    WHERE f.contype='f' AND n.nspname=%s''', (policy.schema,)):
                assert row['parent'] in dependencies
                dependencies[row['child']].add(row['parent'])
            copied = set()
            while len(copied) < len(names):
                ready = sorted(name for name in names if name not in copied
                               and dependencies[name] <= copied)
                assert ready, 'foreign key cycle requires an explicit reviewed copy procedure'
                for name in ready:
                    if not (args.readmit_market_sources and name == 'market_source_records'):
                        conn.execute(sql.SQL('INSERT INTO {} SELECT * FROM {}').format(
                            sql.Identifier(policy.schema, name), sql.Identifier(old.schema, name)))
                    copied.add(name)
            exact_names = [name for name in names if not (
                args.readmit_market_sources and name == 'market_source_records')]
            assert rows(conn, policy.schema, exact_names) == {name: before_rows[name] for name in exact_names}
            install_runtime_roles(conn, policy)
            for kind, role in policy.roles.items():
                password = secrets.token_hex(32)
                passfile = out/(kind+'.pgpass')
                with passfile.open('x') as stream:
                    os.fchmod(stream.fileno(), 0o600)
                    stream.write(f'127.0.0.1:{database["port"]}:{old.database}:{role}:{password}\n')
                passfiles.append(passfile)
                conn.execute(sql.SQL('ALTER ROLE {} PASSWORD {}').format(
                    sql.Identifier(role), sql.Literal(password)))
        started = True
        with psycopg.connect(admin, row_factory=dict_row) as conn:
            conn.execute('SET TRANSACTION READ ONLY')
            audit_runtime_roles(conn, policy)
            audit_runtime_roles(conn, old)
            assert original_catalog(conn) == before_catalog
        for kind, role in policy.roles.items():
            with psycopg.connect(host='127.0.0.1', port=database['port'], dbname=old.database,
                    user=role, passfile=str(out/(kind+'.pgpass')), require_auth='scram-sha-256',
                    autocommit=True, row_factory=dict_row) as conn:
                assert conn.pgconn.used_password
                checks['new_native_SCRAM_logins'] += 1
                for statement in (
                    sql.SQL('SELECT tenant_id FROM {} LIMIT 0'),
                    sql.SQL('INSERT INTO {} SELECT * FROM {} WHERE false'),
                    sql.SQL('UPDATE {} SET tenant_id=tenant_id WHERE false'),
                    sql.SQL('DELETE FROM {} WHERE false'),
                ):
                    target = sql.Identifier(old.schema, 'jobs')
                    denied(conn, statement.format(target, target))
                    checks['cross_namespace_denials'] += 1
                denied(conn, sql.SQL('CREATE TABLE {} (value int)').format(
                    sql.Identifier(policy.schema, 'forbidden')))
                denied(conn, sql.SQL('SET ROLE {}').format(sql.Identifier(policy.owner)))
                checks['runtime_ddl_denials'] += 2
                if kind == 'authority':
                    assert rows(conn, policy.schema, exact_names) == {
                        name: before_rows[name] for name in exact_names}
        with psycopg.connect(original['dsn'], require_auth='scram-sha-256',
                autocommit=True, row_factory=dict_row) as conn:
            assert conn.pgconn.used_password
            for statement in (sql.SQL('SELECT * FROM {} LIMIT 0'),
                              sql.SQL('INSERT INTO {} SELECT * FROM {} WHERE false'),
                              sql.SQL('UPDATE {} SET tenant_id=tenant_id WHERE false'),
                              sql.SQL('DELETE FROM {} WHERE false')):
                target = sql.Identifier(policy.schema, 'jobs')
                denied(conn, statement.format(target, target))
                checks['cross_namespace_denials'] += 1
        if args.ventilation_runtime:
            dsn = make_conninfo(host='127.0.0.1', port=database['port'], dbname=old.database,
                user=policy.roles['authority'], passfile=str(out/'authority.pgpass'), require_auth='scram-sha-256')
            if args.readmit_market_sources:
                from app.market_source_store import MarketSourceStore
                principal = {**original['service_principal'], 'scopes': set(original['service_principal']['scopes'])}
                assert 'market_source_write' in principal['scopes']
                source_store = MarketSourceStore(dsn, policy.schema, principal_provider=lambda: principal,
                                                 runtime_identity=(policy, 'authority'))
                for source in old_sources:
                    source_store.adopt_job(source['tenant_id'], source['kind'], str(source['job_id']))
                with source_store.connect() as conn:
                    new_sources = conn.execute(sql.SQL('SELECT * FROM {}').format(
                        sql.Identifier(policy.schema, 'market_source_records'))).fetchall()
                assert len(new_sources) == len(old_sources)
                assert all(row['admitted_by'] == policy.roles['authority'] for row in new_sources)
                payload_columns = set(old_sources[0])-{'admitted_by', 'recorded_at'}
                assert digest_rows([{k: row[k] for k in payload_columns} for row in new_sources]) == digest_rows(
                    [{k: row[k] for k in payload_columns} for row in old_sources])
                with (out/'new-source-admissions.private.json').open('x') as stream:
                    os.fchmod(stream.fileno(), 0o400)
                    json.dump({'original': old_sources, 'new_admissions': new_sources}, stream, default=str)
                checks['readmitted_market_source_records'] = len(new_sources)
                checks['source_payload_job_identity_preserved'] = True
            checks.update(probe_ventilation(out, policy, dsn, original, args.original_directory,
                                           args.ventilation_runtime, args.ventilation_requests))
    finally:
        if started:
            with psycopg.connect(admin, row_factory=dict_row) as conn:
                audit_runtime_roles(conn, policy)
                conn.execute(sql.SQL('DROP SCHEMA {} CASCADE').format(sql.Identifier(policy.schema)))
                for role in owned_roles:
                    conn.execute(sql.SQL('DROP OWNED BY {}').format(sql.Identifier(role)))
                    conn.execute(sql.SQL('DROP ROLE {}').format(sql.Identifier(role)))
        for passfile in passfiles:
            passfile.unlink()
    with psycopg.connect(admin, row_factory=dict_row) as conn:
        conn.execute('SET TRANSACTION READ ONLY')
        audit_runtime_roles(conn, old)
        assert rows(conn, old.schema, names) == before_rows
        assert original_catalog(conn) == before_catalog
        after_database_acl = conn.execute('SELECT datacl FROM pg_database WHERE datname=%s',
                                         (old.database,)).fetchone()
        after_database_privileges = database_acl(conn)
        comparison = {'raw_acl_array_equal': after_database_acl == before_database_acl,
                      'expanded_grantor_grantee_privilege_grantability_equal':
                          after_database_privileges == before_database_privileges,
                      'before_privileges': len(before_database_privileges),
                      'after_privileges': len(after_database_privileges)}
        with (out/'database-acl-comparison.private.json').open('x') as stream:
            os.fchmod(stream.fileno(), 0o400)
            json.dump(comparison, stream, sort_keys=True)
        assert after_database_privileges == before_database_privileges
        assert not conn.execute('SELECT 1 FROM pg_roles WHERE rolname=ANY(%s)', (owned_roles,)).fetchone()
        assert not conn.execute('SELECT 1 FROM pg_namespace WHERE nspname=%s', (policy.schema,)).fetchone()
    assert not any(path.exists() for path in passfiles)
    record = {'schema_version': 'owned-model-namespace-probe-v1', **checks,
              'namespace_tables': len(names), 'source_rows': sum(sum(v.values()) for v in before_rows.values()),
              'exact_copied_tables': len(exact_names), 'all_exact_copied_table_rows_equal': True,
              'original_rows_roles_acl_preserved': True,
              'both_policy_audits_passed': True, 'new_namespace_roles_passfiles_remaining': 0,
              'database_acl_comparison': comparison,
              'new_cluster_started': False, 'original_consumers_paused': False,
              'new_model_user_deployed': False, 'real_farm_runs': 0, 'G0_G4': 'not_assessed'}
    with (out/'acceptance.private.json').open('x') as stream:
        os.fchmod(stream.fileno(), 0o400)
        json.dump(record, stream, sort_keys=True)
        stream.flush()
        os.fsync(stream.fileno())
    print(json.dumps(record, sort_keys=True))


if __name__ == '__main__':
    main()
