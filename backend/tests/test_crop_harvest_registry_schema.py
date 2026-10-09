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
from psycopg.rows import dict_row
import pytest

from app import crop_harvest_registry_schema as registry
from app import crop_harvest as harvest
from app.runtime_roles import audit_runtime_roles
from test_crop_harvest import (stored_result, server_setup, bound_setup, counts, login_scope,
    original_login_scope, authoring, farm_setup, login_database, native_cleanup, forbid_calculation, save_native)
from login_database import assert_host_scram


def policy():
    return registry.HarvestRegistryPolicy('harvest_schema','harvest_owner','harvest_publisher','harvest_reader','harvest_database')


@pytest.mark.parametrize('value', [None, True, 1, '', 'bad-name', 'Mixed', 'x;DROP SCHEMA public', 'a'*64, 'pg_reserved'])
def test_invalid_policy_names_are_rejected_before_sql(value):
    with pytest.raises(ValueError):replace(policy(), schema=value)


@pytest.mark.parametrize('field', ['owner','publisher','reader','database'])
def test_policy_names_are_unambiguous_and_roles_distinct(field):
    with pytest.raises(ValueError):replace(policy(), **{field:policy().schema})


@pytest.mark.parametrize('value', [None, {}, object()])
def test_implicit_registry_policy_is_rejected_before_sql(value):
    with pytest.raises(ValueError):registry.install_harvest_registry(None, value)


def fixture_row(original, farm, publisher):
    source = harvest._source(original)
    document = {'schema_version':registry.VERSION, 'status':'stored_unpublished_research',
        'claim_scope':'synthetic_harvest_allocation_math_only','rights_or_gate_approval':False,
        'tenant_id':'tenant-1','result_id':registry.VERSION+':'+'1'*64,'parent_result_id':source['result_id'],
        'farm':dict(farm),'source':source,
        'artifact':{'key':'a'*64,'sha256':'b'*64,'row_count':6,'row_chain_sha256':'c'*64,'writer_code_sha256':'d'*64},
        'parameters':{'mass_sha256':'e'*64,'allocation_sha256':'f'*64},
        'code':{'publication_code_sha256':'0'*64,'registry_schema_code_sha256':'1'*64,'artifact_code_sha256':'2'*64}}
    row = {k:document[k] for k in ('tenant_id','result_id','parent_result_id')}
    row.update(farm)
    row.update(artifact_key='a'*64,artifact_sha256='b'*64,row_count=6,row_chain_sha256='c'*64,
               mass_parameter_sha256='e'*64,allocation_parameter_sha256='f'*64,integrity_signature='0'*64,registered_by=publisher)
    return set_document(row,document)


def set_document(row, document):
    raw = harvest._canonical(document)
    return {**row,'payload_raw':raw,'payload_sha256':sha256(raw).hexdigest()}


def insert(conn, policy, row):
    return conn.execute(sql.SQL('INSERT INTO {} ({}) VALUES ({}) RETURNING recorded_at').format(
        sql.Identifier(policy.schema,registry.TABLE),sql.SQL(',').join(map(sql.Identifier,row)),
        sql.SQL(',').join(sql.Placeholder() for _ in row)),tuple(row.values())).fetchone()[0]


@pytest.mark.parametrize('original_login_scope', [{'market_calculation':True,'market_source_storage':True,
    'thermal_scenario_storage':True,'break_even_calculation':True,'crop_cycle_result_storage':True}], indirect=True)
def test_actual_isolated_registry_SCRAM_SQL_grants_and_existing_parent(stored_result,native_cleanup,login_database,tmp_path,monkeypatch):
    service, record, farm, rights, principal, expected = stored_result
    forbid_calculation(monkeypatch)
    monkeypatch.setattr(type(service.authority),'issue',lambda *a,**k:pytest.fail('schema issued result evidence'))
    before = service.read('tenant-1',record['result_id'],farm);db_before = counts(service.store.server.binding)
    def inventory():
        return {str(p):(sha256(p.read_bytes()).hexdigest(),p.stat().st_mode & 0o777,p.stat().st_ino)
            for d in (service.store.server.directory,service.evidence_resolver.values['input_directory'])
            for p in d.rglob('*') if p.is_file()}
    files_before = inventory();fd_before = len(os.listdir('/proc/self/fd'));suffix = uuid4().hex
    database = login_database
    scope = registry.HarvestRegistryPolicy('harvest_test_'+suffix,'harvest_owner_'+suffix,
        'harvest_pub_'+suffix,'harvest_read_'+suffix,database['database'])
    passfiles = [];dsns = {};installed = False;adversarial = [];rejected = []
    try:
        with psycopg.connect(database['admin']) as conn:
            assert_host_scram(conn)
            with pytest.raises(ValueError):registry.install_harvest_registry(conn,replace(scope,database='wrong_database'))
            initial_role = conn.execute('SELECT current_user').fetchone()[0]
            registry.install_harvest_registry(conn,scope)
            assert conn.execute('SELECT current_user').fetchone()[0] == initial_role
            audit = registry.audit_harvest_registry(conn,scope)
            with pytest.raises(errors.DuplicateObject):
                with conn.transaction():registry.install_harvest_registry(conn,scope)
            for role in (scope.publisher,scope.reader):
                password = secrets.token_hex(32);path = tmp_path/(role+'.pgpass');passfiles.append(path)
                path.write_text(f"{database['host']}:{database['port']}:{database['database']}:{role}:{password}\n");path.chmod(0o600)
                conn.execute("SET LOCAL log_statement='none'");conn.execute("SET LOCAL log_min_duration_statement=-1");conn.execute("SET LOCAL log_min_error_statement='panic'")
                verifier = conn.pgconn.encrypt_password(password.encode(),role.encode(),b'scram-sha-256')
                conn.execute(sql.SQL('ALTER ROLE {} PASSWORD {}').format(sql.Identifier(role),sql.Literal(verifier.decode())))
                dsns[role] = make_conninfo(host=database['host'],port=database['port'],dbname=database['database'],
                    user=role,passfile=str(path),sslmode='disable',require_auth='scram-sha-256')
        installed = True
        row = fixture_row(before,farm,scope.publisher);table = sql.Identifier(scope.schema,registry.TABLE)
        with psycopg.connect(dsns[scope.publisher]) as conn:
            assert conn.pgconn.used_password and conn.info.user == scope.publisher
            first_at = insert(conn,scope,row);conn.commit()
            for change in ('unknown-key','missing-key','wrong-column','bad-hash','wrong-claim','approved','duplicate-key','bool-count','bad-source-hash','bad-code-hash','bad-artifact-key'):
                altered = {**row,'result_id':registry.VERSION+':'+'2'*64}
                doc = json.loads(row['payload_raw']);doc['result_id'] = altered['result_id']
                if change == 'unknown-key':doc['approved'] = True
                elif change == 'missing-key':del doc['source']
                elif change == 'wrong-column':doc['farm']['scenario_revision'] = 'different'
                elif change == 'wrong-claim':doc['claim_scope'] = 'production_forecast'
                elif change == 'approved':doc['rights_or_gate_approval'] = True
                elif change == 'bool-count':doc['artifact']['row_count'] = True
                elif change == 'bad-source-hash':doc['source']['payload_sha256'] = 'unknown'
                elif change == 'bad-code-hash':doc['code']['publication_code_sha256'] = 'unknown'
                elif change == 'bad-artifact-key':doc['artifact']['key'] = '../escape'
                altered = set_document(altered,doc)
                if change == 'bad-hash':altered['payload_sha256'] = '0'*64
                if change == 'duplicate-key':
                    altered['payload_raw'] = altered['payload_raw'][:-1]+b',"tenant_id":"tenant-1"}'
                    altered['payload_sha256'] = sha256(altered['payload_raw']).hexdigest()
                with pytest.raises(errors.CheckViolation):
                    with conn.transaction():insert(conn,scope,altered)
                rejected.append(change)
            for operation in ('UPDATE','DELETE','TRUNCATE'):
                statement = sql.SQL('UPDATE {} SET row_count=row_count').format(table) if operation=='UPDATE' else sql.SQL(operation+' FROM {}').format(table) if operation=='DELETE' else sql.SQL('TRUNCATE {}').format(table)
                with pytest.raises(errors.InsufficientPrivilege):
                    with conn.transaction():conn.execute(statement)
        with psycopg.connect(dsns[scope.reader]) as conn:
            assert conn.pgconn.used_password and conn.info.user == scope.reader
            stored = conn.execute(sql.SQL('SELECT payload_raw,recorded_at FROM {}').format(table)).fetchall()
            assert stored == [(row['payload_raw'],first_at)]
            with pytest.raises(errors.InsufficientPrivilege):
                with conn.transaction():insert(conn,scope,row)
            with pytest.raises(errors.InsufficientPrivilege):
                with conn.transaction():conn.execute(sql.SQL('CREATE TABLE {}.unexpected (x int)').format(sql.Identifier(scope.schema)))
        with psycopg.connect(database['admin'],row_factory=dict_row) as conn:
            # Both connection row factories are supported by the installer audit.
            assert registry.audit_harvest_registry(conn,scope) == audit
        with psycopg.connect(database['admin']) as conn:
            perturbations = [('reader-insert',sql.SQL('GRANT INSERT ON {} TO {}').format(table,sql.Identifier(scope.reader))),
                ('PUBLIC-read',sql.SQL('GRANT SELECT ON {} TO PUBLIC').format(table)),
                ('reader-create',sql.SQL('GRANT CREATE ON SCHEMA {} TO {}').format(sql.Identifier(scope.schema),sql.Identifier(scope.reader))),
                ('membership',sql.SQL('GRANT {} TO {}').format(sql.Identifier(scope.owner),sql.Identifier(scope.publisher))),
                ('privileged-login',sql.SQL('ALTER ROLE {} CREATEDB').format(sql.Identifier(scope.reader))),
                ('routine-execute',sql.SQL('GRANT EXECUTE ON FUNCTION {}.reject_harvest_result_change() TO {}').format(sql.Identifier(scope.schema),sql.Identifier(scope.publisher))),
                ('column-insert',sql.SQL('GRANT INSERT (row_count) ON {} TO {}').format(table,sql.Identifier(scope.reader))),
                ('grant-option',sql.SQL('GRANT SELECT ON {} TO {} WITH GRANT OPTION').format(table,sql.Identifier(scope.publisher))),
                ('disabled-trigger',sql.SQL('ALTER TABLE {} DISABLE TRIGGER harvest_result_immutable').format(table)),
                ('routine-body',sql.SQL('CREATE OR REPLACE FUNCTION {}.reject_harvest_result_change() RETURNS trigger LANGUAGE plpgsql AS $$ BEGIN RETURN NEW; END $$').format(sql.Identifier(scope.schema)))]
            for name,statement in perturbations:
                with conn.transaction(force_rollback=True):
                    conn.execute(statement)
                    with pytest.raises(ValueError):registry.audit_harvest_registry(conn,scope)
                adversarial.append(name)
                assert registry.audit_harvest_registry(conn,scope) == audit
            with pytest.raises(errors.RaiseException):
                with conn.transaction():
                    conn.execute(sql.SQL('SET LOCAL ROLE {}').format(sql.Identifier(scope.owner)))
                    conn.execute(sql.SQL('UPDATE {} SET row_count=row_count').format(table))
        with service.store.jobs.connect() as conn:audit_runtime_roles(conn,service.store.jobs.runtime_identity[0])
        assert service.read('tenant-1',record['result_id'],farm) == before
        assert counts(service.store.server.binding) == db_before and inventory() == files_before
    finally:
        for path in passfiles:path.unlink(missing_ok=True)
        if installed:
            with psycopg.connect(database['admin']) as conn:
                conn.execute(sql.SQL('DROP SCHEMA {} CASCADE').format(sql.Identifier(scope.schema)))
                for role in (scope.publisher,scope.reader):
                    conn.execute(sql.SQL('REVOKE CONNECT ON DATABASE {} FROM {}').format(sql.Identifier(scope.database),sql.Identifier(role)))
                for role in (scope.publisher,scope.reader,scope.owner):conn.execute(sql.SQL('DROP ROLE {}').format(sql.Identifier(role)))
        with psycopg.connect(database['admin']) as conn:
            remaining = conn.execute('SELECT count(*) FROM pg_namespace WHERE nspname=%s',(scope.schema,)).fetchone()[0]
            role_count = conn.execute('SELECT count(*) FROM pg_roles WHERE rolname=ANY(%s)',([scope.owner,scope.publisher,scope.reader],)).fetchone()[0]
        assert remaining == role_count == 0 and not any(path.exists() for path in passfiles)
    assert len(os.listdir('/proc/self/fd')) == fd_before
    save_native('harvest-registry-schema-verified.json',{'actual_SCRAM':True,'separate_schema_and_owner':True,
        'schema_policy':scope.__dict__,'role_audit':audit,
        'SQL_fixture_row':{**{key:value for key,value in row.items() if key!='payload_raw'},'payload_raw_utf8':row['payload_raw'].decode()},
        'rejected_SQL_cases':rejected,'rejected_and_rolled_back_role_cases':adversarial,
        'source_fixture_kind':'SQL_format_only_no_real_harvest_registration','actual_new_harvest_registrations':0,
        'existing_parent_result_id':record['result_id'],'existing_parent_query_and_role_audit_preserved':True,
        'provisioner_current_role_restored':True,'wrong_database_rejected_before_DDL':True,
        'DB_counts_preserved':list(db_before),'input_custody_SHA_mode_inode_preserved':True,'RHS_calls':0,'new_proof_calls':0,
        'FD_before_after':[fd_before,len(os.listdir('/proc/self/fd'))], 'registry_schemas_after':remaining,
        'registry_roles_after':role_count,'registry_passfiles_after':0,'actual_crop_Runs':0,'gates':'not_assessed'})
