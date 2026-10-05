"""Real privilege checks under test identities; no deployed login/UID claim."""

from contextlib import contextmanager
from pathlib import Path
import sys
from uuid import uuid4

import psycopg
from psycopg import errors, sql
from psycopg.rows import dict_row
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from app.execution_attestation import install_execution_attestation_schema
from app.db import install_market_hold_schema
from app.runtime_roles import (RuntimeRolePolicy, RolePolicyHold, TABLES,
                               audit_runtime_roles, install_runtime_roles)
from app.thermal_run_store import install_thermal_run_schema
from test_jobs import pg_store


@contextmanager
def owned_scope(pg_store, policy):
    with pg_store.connect() as conn:
        original = conn.execute("SELECT current_user AS name").fetchone()["name"]
        conn.execute(sql.SQL("CREATE ROLE {} NOLOGIN").format(sql.Identifier(policy.owner)))
        install_execution_attestation_schema(conn, pg_store.schema)
        install_thermal_run_schema(conn, pg_store.schema)
        install_market_hold_schema(conn, pg_store.schema)
        tables = TABLES
        if getattr(policy, "market_calculation", False):
            from app.market_candidate_store import install_market_candidate_schema
            from app.market_result_store import install_market_result_schema
            from app.runtime_roles import MARKET_TABLES
            install_market_candidate_schema(conn, pg_store.schema)
            install_market_result_schema(conn, pg_store.schema)
            tables += MARKET_TABLES
        if getattr(policy, "break_even_calculation", False):
            from app.break_even_store import install_break_even_store_schema
            from app.runtime_roles import BREAK_EVEN_TABLES
            install_break_even_store_schema(conn, pg_store.schema)
            tables += BREAK_EVEN_TABLES
        if getattr(policy, "market_source_storage", False):
            from app.market_source_store import install_market_source_schema
            from app.runtime_roles import MARKET_SOURCE_TABLES
            install_market_source_schema(conn, pg_store.schema)
            tables += MARKET_SOURCE_TABLES
        if getattr(policy, "thermal_scenario_storage", False):
            from app.thermal_scenario_store import install_thermal_scenario_schema
            from app.runtime_roles import THERMAL_SCENARIO_TABLES
            install_thermal_scenario_schema(conn, pg_store.schema)
            tables += THERMAL_SCENARIO_TABLES
        if getattr(policy, "authored_release_storage", False):
            from app.farm_authored_release_store import install_authored_release_schema
            from app.runtime_roles import AUTHORED_RELEASE_TABLES
            install_authored_release_schema(conn, pg_store.schema)
            tables += AUTHORED_RELEASE_TABLES
        if getattr(policy, "authored_run_storage", False):
            from app.farm_authored_run_store import install_authored_run_schema
            from app.runtime_roles import AUTHORED_RUN_TABLES
            install_authored_run_schema(conn, pg_store.schema)
            tables += AUTHORED_RUN_TABLES
        if getattr(policy, "crop_result_storage", False):
            from app.crop_result_store import install_crop_result_schema
            from app.runtime_roles import CROP_RESULT_TABLES
            install_crop_result_schema(conn, pg_store.schema)
            tables += CROP_RESULT_TABLES
        if getattr(policy, "crop_coupled_result_storage", False):
            from app.crop_coupled_result_store import install_coupled_crop_result_schema
            from app.runtime_roles import CROP_COUPLED_RESULT_TABLES
            install_coupled_crop_result_schema(conn, pg_store.schema)
            tables += CROP_COUPLED_RESULT_TABLES
        if getattr(policy, "crop_startup_result_storage", False):
            from app.crop_startup_result_store import install_startup_crop_result_schema
            from app.runtime_roles import CROP_STARTUP_RESULT_TABLES
            install_startup_crop_result_schema(conn, pg_store.schema)
            tables += CROP_STARTUP_RESULT_TABLES
        if getattr(policy, "crop_cycle_result_storage", False):
            from app.crop_cycle_result_schema import install_cycle_crop_result_schema
            from app.runtime_roles import CROP_CYCLE_RESULT_TABLES
            install_cycle_crop_result_schema(conn, pg_store.schema)
            tables += CROP_CYCLE_RESULT_TABLES
        conn.execute(sql.SQL("ALTER SCHEMA {} OWNER TO {}").format(
            sql.Identifier(policy.schema), sql.Identifier(policy.owner)))
        for table in tables:
            conn.execute(sql.SQL("ALTER TABLE {}.{} OWNER TO {}").format(
                sql.Identifier(policy.schema), sql.Identifier(table), sql.Identifier(policy.owner)))
        routines = conn.execute("""SELECT proname FROM pg_proc p JOIN pg_namespace n ON n.oid=p.pronamespace
            WHERE n.nspname=%s""", (policy.schema,)).fetchall()
        for row in routines:
            conn.execute(sql.SQL("ALTER FUNCTION {}.{}() OWNER TO {}").format(
                sql.Identifier(policy.schema), sql.Identifier(row["proname"]), sql.Identifier(policy.owner)))
    try:
        yield pg_store, policy
    finally:
        with pg_store.connect() as conn:
            for role in policy.roles.values():
                if conn.execute("SELECT 1 FROM pg_roles WHERE rolname=%s", (role,)).fetchone():
                    conn.execute(sql.SQL("DROP OWNED BY {}").format(sql.Identifier(role)))
                    conn.execute(sql.SQL("DROP ROLE {}").format(sql.Identifier(role)))
            conn.execute(sql.SQL("REASSIGN OWNED BY {} TO {}").format(
                sql.Identifier(policy.owner), sql.Identifier(original)))
            conn.execute(sql.SQL("DROP OWNED BY {}").format(sql.Identifier(policy.owner)))
            conn.execute(sql.SQL("DROP ROLE {}").format(sql.Identifier(policy.owner)))


@pytest.fixture
def role_scope(pg_store):
    suffix = uuid4().hex
    policy = RuntimeRolePolicy(pg_store.schema, "ossf_owner_" + suffix, "ossf_" + suffix)
    with owned_scope(pg_store, policy) as scope:
        yield scope


def installed(scope):
    store, policy = scope
    with store.connect() as conn:
        install_runtime_roles(conn, policy)
    with store.connect() as conn:
        return audit_runtime_roles(conn, policy)


@contextmanager
def identity(store, role):
    with store.connect() as conn:
        conn.execute(sql.SQL("SET SESSION AUTHORIZATION {}").format(sql.Identifier(role)))
        yield conn


@pytest.mark.parametrize("kind", ["request", "worker"])
@pytest.mark.parametrize("operation", ["INSERT", "UPDATE", "DELETE", "TRUNCATE", "SELECT"])
def test_general_roles_cannot_access_authoritative_tables(role_scope, kind, operation):
    store, policy = role_scope
    installed(role_scope)
    for table in TABLES:
        target = sql.SQL("{}.{}").format(sql.Identifier(policy.schema), sql.Identifier(table))
        queries = {
            "INSERT": sql.SQL("INSERT INTO {} (tenant_id) VALUES ('tenant-a')").format(target),
            "UPDATE": sql.SQL("UPDATE {} SET tenant_id='tenant-a' WHERE false").format(target),
            "DELETE": sql.SQL("DELETE FROM {} WHERE false").format(target),
            "TRUNCATE": sql.SQL("TRUNCATE TABLE {}").format(target),
            "SELECT": sql.SQL("SELECT * FROM {} LIMIT 0").format(target),
        }
        with identity(store, policy.roles[kind]) as conn, pytest.raises(errors.InsufficientPrivilege):
            conn.execute(queries[operation])


def test_installer_removes_public_column_and_global_default_grants(role_scope):
    store, policy = role_scope
    with store.connect() as conn:
        conn.execute(sql.SQL("GRANT SELECT(input_bytes), UPDATE(state) ON TABLE {}.jobs TO PUBLIC")
                     .format(sql.Identifier(policy.schema)))
        conn.execute(sql.SQL("GRANT CREATE ON SCHEMA {} TO PUBLIC").format(sql.Identifier(policy.schema)))
        conn.execute(sql.SQL("ALTER DEFAULT PRIVILEGES FOR ROLE {} GRANT INSERT ON TABLES TO PUBLIC")
                     .format(sql.Identifier(policy.owner)))
    installed(role_scope)
    with store.connect() as conn:
        conn.execute(sql.SQL("SET LOCAL ROLE {}").format(sql.Identifier(policy.owner)))
        conn.execute(sql.SQL("CREATE TABLE {}.future_record (payload text)").format(sql.Identifier(policy.schema)))
        conn.execute(sql.SQL("CREATE FUNCTION {}.future_function() RETURNS int LANGUAGE SQL AS 'SELECT 1'")
                     .format(sql.Identifier(policy.schema)))
    with store.connect() as conn:
        audit_runtime_roles(conn, policy)
    for role in policy.roles.values():
        with identity(store, role) as conn, pytest.raises(errors.InsufficientPrivilege):
            conn.execute(sql.SQL("SELECT payload FROM {}.future_record").format(sql.Identifier(policy.schema)))
        with identity(store, role) as conn, pytest.raises(errors.InsufficientPrivilege):
            conn.execute(sql.SQL("SELECT {}.future_function()").format(sql.Identifier(policy.schema)))


@pytest.mark.parametrize("kind", ["request", "worker", "supervisor", "authority"])
def test_runtime_roles_cannot_create_persistent_objects_or_escalate(role_scope, kind):
    store, policy = role_scope
    installed(role_scope)
    statements = [
        sql.SQL("CREATE TABLE {}.forbidden (value int)").format(sql.Identifier(policy.schema)),
        sql.SQL("ALTER TABLE {}.jobs DISABLE TRIGGER ALL").format(sql.Identifier(policy.schema)),
        sql.SQL("SET ROLE {}").format(sql.Identifier(policy.owner)),
    ]
    if kind != "authority":
        statements.append(sql.SQL("SET ROLE {}").format(sql.Identifier(policy.roles["authority"])))
    for query in statements:
        with identity(store, policy.roles[kind]) as conn, pytest.raises(errors.InsufficientPrivilege):
            conn.execute(query)


def test_rejected_reinstallation_preserves_audited_permissions(role_scope):
    store, policy = role_scope
    before = installed(role_scope)
    with store.connect() as conn, pytest.raises(RolePolicyHold, match="already_exist"):
        install_runtime_roles(conn, policy)
    with store.connect() as conn:
        assert audit_runtime_roles(conn, policy) == before


def test_final_audit_failure_rolls_back_roles_and_acl_changes(role_scope, monkeypatch):
    import app.runtime_roles as module
    store, policy = role_scope
    with store.connect() as conn:
        conn.execute(sql.SQL("GRANT SELECT(input_bytes) ON TABLE {}.jobs TO PUBLIC")
                     .format(sql.Identifier(policy.schema)))
        before = conn.execute("SELECT attacl FROM pg_attribute WHERE attrelid=%s::regclass AND attname='input_bytes'",
                              (policy.schema + ".jobs",)).fetchone()
    def reject(*_args):
        raise RolePolicyHold("test_injected_audit_failure")
    monkeypatch.setattr(module, "audit_runtime_roles", reject)
    with store.connect() as conn, pytest.raises(RolePolicyHold, match="injected"):
        install_runtime_roles(conn, policy)
    with store.connect() as conn:
        assert conn.execute("SELECT 1 FROM pg_roles WHERE rolname=ANY(%s)",
                            (list(policy.roles.values()),)).fetchone() is None
        assert conn.execute("SELECT attacl FROM pg_attribute WHERE attrelid=%s::regclass AND attname='input_bytes'",
                            (policy.schema + ".jobs",)).fetchone() == before


@pytest.mark.parametrize("fault", ["column", "membership", "grant_option", "defaults",
                                 "role_column", "column_grant_option", "missing_table",
                                 "unexpected_update"])
def test_audit_rejects_privilege_drift(role_scope, fault):
    store, policy = role_scope
    installed(role_scope)
    with store.connect() as conn:
        if fault == "column":
            conn.execute(sql.SQL("GRANT SELECT(input_bytes) ON TABLE {}.jobs TO PUBLIC")
                         .format(sql.Identifier(policy.schema)))
        elif fault == "membership":
            conn.execute(sql.SQL("GRANT {} TO {}").format(
                sql.Identifier(policy.roles["authority"]), sql.Identifier(policy.roles["worker"])))
        elif fault == "grant_option":
            conn.execute(sql.SQL("GRANT INSERT ON TABLE {}.ai_decisions TO {} WITH GRANT OPTION")
                .format(sql.Identifier(policy.schema), sql.Identifier(policy.roles["authority"])))
        elif fault == "role_column":
            conn.execute(sql.SQL("GRANT SELECT(input_bytes) ON TABLE {}.jobs TO {}")
                .format(sql.Identifier(policy.schema), sql.Identifier(policy.roles["worker"])))
        elif fault == "column_grant_option":
            conn.execute(sql.SQL("GRANT INSERT(input_bytes) ON TABLE {}.jobs TO {} WITH GRANT OPTION")
                .format(sql.Identifier(policy.schema), sql.Identifier(policy.roles["authority"])))
        elif fault == "missing_table":
            conn.execute(sql.SQL("REVOKE SELECT ON TABLE {}.jobs FROM {}")
                .format(sql.Identifier(policy.schema), sql.Identifier(policy.roles["authority"])))
        elif fault == "unexpected_update":
            conn.execute(sql.SQL("GRANT UPDATE ON TABLE {}.ai_decisions TO {}")
                .format(sql.Identifier(policy.schema), sql.Identifier(policy.roles["authority"])))
        else:
            conn.execute(sql.SQL("ALTER DEFAULT PRIVILEGES FOR ROLE {} GRANT EXECUTE ON FUNCTIONS TO PUBLIC")
                         .format(sql.Identifier(policy.owner)))
            assert conn.execute("""SELECT 1 FROM pg_default_acl d JOIN pg_roles r ON r.oid=d.defaclrole
                WHERE r.rolname=%s AND d.defaclnamespace=0 AND d.defaclobjtype='f'""",
                (policy.owner,)).fetchone() is None
    with store.connect() as conn, pytest.raises(RolePolicyHold):
        audit_runtime_roles(conn, policy)


def test_table_read_revoked_between_table_and_column_checks_is_rejected(role_scope):
    store, policy = role_scope
    installed(role_scope)

    class RevokeBeforeColumns:
        def __init__(self, connection):
            self.connection = connection
            self.changed = False

        def __getattr__(self, name):
            return getattr(self.connection, name)

        def execute(self, query, params=None):
            if (not self.changed and params and policy.roles['authority'] in
                    (params[0] if isinstance(params[0], (list, tuple)) else (params[0],))
                    and ('has_column_privilege' in str(query)
                         or 'has_any_column_privilege' in str(query))):
                self.changed = True
                self.connection.execute(sql.SQL('REVOKE SELECT ON TABLE {}.jobs FROM {}')
                    .format(sql.Identifier(policy.schema), sql.Identifier(policy.roles['authority'])))
                self.connection.execute(sql.SQL('GRANT SELECT(input_bytes) ON TABLE {}.jobs TO {}')
                    .format(sql.Identifier(policy.schema), sql.Identifier(policy.roles['authority'])))
            return self.connection.execute(query, params)

    with store.connect() as conn:
        changed = RevokeBeforeColumns(conn)
        with pytest.raises(RolePolicyHold, match='runtime_column_grant_matrix'):
            audit_runtime_roles(changed, policy)
        assert changed.changed


@pytest.mark.parametrize("name", ["pg_bad", "bad-name", "a" * 64, "x;DROP SCHEMA public"])
def test_policy_rejects_untrusted_identifier_shapes(name):
    with pytest.raises(RolePolicyHold):
        RuntimeRolePolicy(name, "owner_a", "prefix_a")


@pytest.mark.parametrize("stage,proceed", [("research", True), ("collection_review", True), ("assessment", False)])
def test_authority_writes_and_supervisor_issuer_reads_use_only_granted_rights(role_scope, tmp_path, stage, proceed):
    from test_cli_attestation_issuer import _completed_observation
    store, policy = role_scope
    installed(role_scope)

    def connect_as(kind):
        conn = psycopg.connect(store._dsn, row_factory=dict_row)
        conn.execute(sql.SQL("SET SESSION AUTHORIZATION {}").format(sql.Identifier(policy.roles[kind])))
        conn.commit()
        return conn

    data = _completed_observation(store, tmp_path, stage=stage, proceed=proceed,
        sign_before_closure=True, install_attestation=False,
        store_connect=lambda: connect_as("authority"), issuer_connect=lambda: connect_as("supervisor"))
    (trusted_store, observer, issuer, _, _, tenant, job_id, attempt,
     capture_id, decision_id, _, _) = data
    try:
        raw, signature = issuer.issue(capture_id, decision_id)
        assert raw and len(signature) == 64
        assert trusted_store.get_job(tenant, job_id)["state"] == ("succeeded" if proceed else "hold")
        with issuer.job_store.connect() as conn:
            assert conn.execute("SELECT current_user AS name").fetchone()["name"] == policy.roles["supervisor"]
            with pytest.raises(errors.InsufficientPrivilege):
                conn.execute(sql.SQL("INSERT INTO {}.ai_decisions (tenant_id) VALUES ('tenant-a')")
                             .format(sql.Identifier(policy.schema)))
    finally:
        observer.close()


def test_reachable_security_definer_outside_project_rejects_install(role_scope):
    store, policy = role_scope
    outside = policy.prefix + "_outside"
    with store.connect() as conn:
        conn.execute(sql.SQL("CREATE SCHEMA {}").format(sql.Identifier(outside)))
        conn.execute(sql.SQL("GRANT USAGE ON SCHEMA {} TO PUBLIC").format(sql.Identifier(outside)))
        conn.execute(sql.SQL("CREATE FUNCTION {}.escape() RETURNS int LANGUAGE SQL SECURITY DEFINER AS 'SELECT 1'")
                     .format(sql.Identifier(outside)))
    try:
        with store.connect() as conn, pytest.raises(RolePolicyHold, match="definer_escape"):
            install_runtime_roles(conn, policy)
        with store.connect() as conn:
            assert conn.execute("SELECT 1 FROM pg_roles WHERE rolname=ANY(%s)",
                                (list(policy.roles.values()),)).fetchone() is None
    finally:
        with store.connect() as conn:
            conn.execute(sql.SQL("DROP SCHEMA {} CASCADE").format(sql.Identifier(outside)))


@pytest.fixture(scope='module')
def schema_login_database():
    # Local imports avoid a cycle: the shared login fixture provisions owned_scope.
    from login_database import login_database
    yield from login_database.__wrapped__()


@pytest.fixture
def schema_login_scope(schema_login_database, tmp_path, request):
    from login_database import login_scope
    yield from login_scope.__wrapped__(schema_login_database, tmp_path, request)


def test_startup_storage_default_and_explicit_table_selection():
    from dataclasses import replace
    from app.runtime_roles import RuntimeLoginPolicy, _tables
    plain = RuntimeLoginPolicy('test', 'owner', 'runtime', 'postgres')
    assert plain.crop_startup_result_storage is False
    assert _tables(plain)==TABLES
    assert _tables(replace(plain, crop_startup_result_storage=True))==TABLES+('crop_startup_research_results',)
    for value in (0, 1, 'false', None):
        with pytest.raises(RolePolicyHold):replace(plain, crop_startup_result_storage=value)


@pytest.mark.parametrize('schema', ['bad-name', 'x;DROP SCHEMA public', 'a'*64, None])
def test_startup_schema_identifier_rejected_before_sql(schema):
    from app.crop_startup_result_store import install_startup_crop_result_schema
    with pytest.raises(ValueError):install_startup_crop_result_schema(None, schema)


def startup_schema_row(base, policy):
    from hashlib import sha256
    from app.thermal_run_store import _canonical
    job = base.submit('tenant-a', 'research', {'fixture':'synthetic_schema_only'}, uuid4().hex)
    result_id = 'crop-result-v3:'+'1'*64
    raw = _canonical({'schema_version':'crop-result-v3', 'status':'stored_unpublished_research',
        'claim_scope':'synthetic_crop_math_only', 'result_id':result_id, 'fixture_kind':'schema_only'})
    return {'tenant_id':'tenant-a', 'study_id':'schema-study', 'revision':'r1', 'result_id':result_id,
        'scenario_id':'synthetic-schema-farm', 'scenario_revision':'r1', 'registration_job_id':job['job_id'],
        'registration_sha256':'2'*64, 'payload_raw':raw, 'payload_sha256':sha256(raw).hexdigest(),
        'integrity_signature':'3'*64, 'registered_by':policy.roles['authority']}


def insert_startup_schema_row(conn, policy, row):
    columns=list(row)
    conn.execute(sql.SQL('INSERT INTO {}.crop_startup_research_results ({}) VALUES ({})').format(
        sql.Identifier(policy.schema),sql.SQL(',').join(map(sql.Identifier,columns)),
        sql.SQL(',').join(sql.Placeholder() for _ in columns)),tuple(row[k] for k in columns))


@pytest.mark.parametrize('schema_login_scope', [{'crop_startup_result_storage':True}], indirect=True)
def test_startup_schema_actual_scram_select_insert_only_and_immutable_owner(schema_login_scope):
    from app.runtime_login import connect_runtime
    from app.runtime_roles import _tables
    base, policy, dsns = schema_login_scope
    assert policy.crop_startup_result_storage is True
    assert _tables(policy)==TABLES+('crop_startup_research_results',)
    target=sql.SQL('{}.crop_startup_research_results').format(sql.Identifier(policy.schema))
    row=startup_schema_row(base,policy)
    with connect_runtime(dsns['authority'],policy,'authority') as conn:
        assert conn.pgconn.used_password and conn.info.get_parameters()['require_auth']=='scram-sha-256'
        insert_startup_schema_row(conn,policy,row)
        actual=conn.execute(sql.SQL('SELECT * FROM {}').format(target)).fetchone()
        assert all(actual[k]==v for k,v in row.items())
        assert actual['recorded_at'].tzinfo is not None
    for kind in ('request','worker','supervisor'):
        for query in (sql.SQL('SELECT * FROM {} LIMIT 0').format(target),
                      sql.SQL('INSERT INTO {} SELECT * FROM {} WHERE false').format(target,target)):
            with connect_runtime(dsns[kind],policy,kind) as conn,pytest.raises(errors.InsufficientPrivilege):
                if kind=='supervisor':conn.execute('SET TRANSACTION READ WRITE')
                conn.execute(query)
    for query in (sql.SQL('UPDATE {} SET revision=revision').format(target),
                  sql.SQL('DELETE FROM {}').format(target),sql.SQL('TRUNCATE {}').format(target)):
        with connect_runtime(dsns['authority'],policy,'authority') as conn,pytest.raises(errors.InsufficientPrivilege):
            conn.execute(query)
    for query in (sql.SQL('UPDATE {} SET revision=revision').format(target),sql.SQL('DELETE FROM {}').format(target)):
        with base.connect() as conn,pytest.raises(errors.RaiseException,match='immutable'):
            conn.execute(sql.SQL('SET LOCAL ROLE {}').format(sql.Identifier(policy.owner)))
            conn.execute(query)
    with base.connect() as conn:
        assert conn.execute(sql.SQL('SELECT count(*) AS n FROM {}').format(target)).fetchone()['n']==1
        assert audit_runtime_roles(conn,policy)['tables']>=len(TABLES)+1


@pytest.mark.parametrize('schema_login_scope', [{'crop_startup_result_storage':True}], indirect=True)
def test_startup_schema_constraints_and_tenant_parent_cannot_be_bypassed(schema_login_scope):
    from hashlib import sha256
    from app.thermal_run_store import _canonical
    from app.runtime_login import connect_runtime
    import json
    base, policy, dsns = schema_login_scope
    row=startup_schema_row(base,policy);packet=json.loads(row['payload_raw'])
    oversized=_canonical({**packet,'padding':'x'*(20*1024*1024)})
    variants=[({'tenant_id':''},errors.CheckViolation),({'study_id':''},errors.CheckViolation),
        ({'revision':'r'*201},errors.CheckViolation),({'result_id':'crop-result-v2:'+'1'*64},errors.CheckViolation),
        ({'payload_sha256':'0'*64},errors.CheckViolation),
        ({'payload_raw':b''},(errors.CheckViolation,errors.DataError)),
        ({'payload_raw':oversized,'payload_sha256':sha256(oversized).hexdigest()},errors.CheckViolation),
        ({'integrity_signature':'bad'},errors.CheckViolation),
        ({'registration_job_id':uuid4()},errors.ForeignKeyViolation),
        ({'tenant_id':'tenant-other'},errors.ForeignKeyViolation)]
    for changes,error in variants:
        with connect_runtime(dsns['authority'],policy,'authority') as conn,pytest.raises(error):
            insert_startup_schema_row(conn,policy,{**row,**changes})
    for changes in ({'schema_version':'crop-result-v2'}, {'status':'approved'}, {'claim_scope':'prediction'},
                    {'result_id':'crop-result-v3:'+'0'*64}):
        raw=_canonical({**packet,**changes})
        with connect_runtime(dsns['authority'],policy,'authority') as conn,pytest.raises(errors.CheckViolation):
            insert_startup_schema_row(conn,policy,{**row,'payload_raw':raw,'payload_sha256':sha256(raw).hexdigest()})
    with connect_runtime(dsns['authority'],policy,'authority') as conn:
        insert_startup_schema_row(conn,policy,row)
    fresh_id='crop-result-v3:'+'4'*64;fresh_raw=_canonical({**packet,'result_id':fresh_id})
    for changes in ({}, {'revision':'r2'}, {'result_id':fresh_id,'payload_raw':fresh_raw,
                                         'payload_sha256':sha256(fresh_raw).hexdigest()}):
        with connect_runtime(dsns['authority'],policy,'authority') as conn,pytest.raises(errors.UniqueViolation):
            insert_startup_schema_row(conn,policy,{**row,**changes})


@pytest.mark.parametrize('schema_login_scope', [{'crop_startup_result_storage':False}], indirect=True)
def test_startup_storage_false_has_no_grants_even_on_provisioned_table(schema_login_scope):
    from app.crop_startup_result_store import install_startup_crop_result_schema
    from app.runtime_login import connect_runtime
    base,policy,dsns=schema_login_scope
    assert policy.crop_startup_result_storage is False
    with base.connect() as conn:
        conn.execute(sql.SQL('SET LOCAL ROLE {}').format(sql.Identifier(policy.owner)))
        install_startup_crop_result_schema(conn,policy.schema)
    with base.connect() as conn:
        audit_runtime_roles(conn,policy)
    target=sql.SQL('{}.crop_startup_research_results').format(sql.Identifier(policy.schema))
    for kind in policy.roles:
        with connect_runtime(dsns[kind],policy,kind) as conn,pytest.raises(errors.InsufficientPrivilege):
            conn.execute(sql.SQL('SELECT * FROM {} LIMIT 0').format(target))


@pytest.mark.parametrize('schema_login_scope', [{'crop_startup_result_storage':True}], indirect=True)
@pytest.mark.parametrize('drift', ['worker_select','authority_update','public_select','authority_column','authority_missing'])
def test_startup_schema_extra_privileges_fail_current_audit(schema_login_scope,drift):
    base,policy,_=schema_login_scope
    target=sql.SQL('{}.crop_startup_research_results').format(sql.Identifier(policy.schema))
    with base.connect() as conn:
        if drift=='public_select':conn.execute(sql.SQL('GRANT SELECT ON {} TO PUBLIC').format(target))
        elif drift=='authority_missing':
            conn.execute(sql.SQL('REVOKE SELECT ON {} FROM {}').format(target,sql.Identifier(policy.roles['authority'])))
        else:
            privilege={'worker_select':'SELECT','authority_update':'UPDATE','authority_column':'UPDATE (revision)'}[drift]
            kind='worker' if drift=='worker_select' else 'authority'
            conn.execute(sql.SQL('GRANT {} ON {} TO {}').format(sql.SQL(privilege),target,sql.Identifier(policy.roles[kind])))
    with base.connect() as conn,pytest.raises(RolePolicyHold):audit_runtime_roles(conn,policy)


def test_cycle_storage_default_exact_boolean_and_independent_table_selection():
    from dataclasses import replace
    from app.runtime_roles import RuntimeLoginPolicy, _tables
    plain = RuntimeLoginPolicy('test', 'owner', 'runtime', 'postgres')
    assert plain.crop_cycle_result_storage is False
    assert _tables(plain) == TABLES
    assert _tables(replace(plain, crop_cycle_result_storage=True)) == TABLES + ('crop_cycle_research_results',)
    both = replace(plain, crop_startup_result_storage=True, crop_cycle_result_storage=True)
    assert _tables(both) == TABLES + ('crop_startup_research_results', 'crop_cycle_research_results')
    for value in (0, 1, 'false', None, [], {}):
        with pytest.raises(RolePolicyHold):
            replace(plain, crop_cycle_result_storage=value)


def cycle_schema_helpers():
    from test_crop_cycle_result_schema import fixture_row, insert, target, owner
    return fixture_row, insert, target, owner


@pytest.mark.parametrize('schema_login_scope', [{'crop_cycle_result_storage': True}], indirect=True)
def test_cycle_profile_actual_scram_select_insert_only_and_owner_immutability(schema_login_scope, monkeypatch):
    from app import crop_cycle_stream_execution as engine
    from app.runtime_login import connect_runtime
    from app.runtime_roles import _tables
    def forbidden(*args, **kwargs):
        pytest.fail('role provisioning must not execute crop equations')
    monkeypatch.setattr(engine, 'advance_chunk', forbidden)
    monkeypatch.setattr(engine.short._Evaluator, 'rhs', forbidden)
    base, policy, dsns = schema_login_scope
    assert policy.crop_cycle_result_storage is True
    assert _tables(policy) == TABLES + ('crop_cycle_research_results',)
    fixture_row, insert, target, owner = cycle_schema_helpers()
    row = fixture_row(base, policy)
    with connect_runtime(dsns['authority'], policy, 'authority') as conn:
        assert conn.pgconn.used_password and conn.info.get_parameters()['require_auth'] == 'scram-sha-256'
        insert(conn, policy, row)
        actual = conn.execute(sql.SQL('SELECT * FROM {}').format(target(policy))).fetchone()
        assert all((bytes(actual[k]) if k == 'payload_raw' else actual[k]) == v for k, v in row.items())
        assert actual['recorded_at'].tzinfo is not None
    for kind in policy.roles:
        queries = [sql.SQL('UPDATE {} SET revision=revision').format(target(policy)),
                   sql.SQL('DELETE FROM {}').format(target(policy)),
                   sql.SQL('TRUNCATE {}').format(target(policy))]
        if kind != 'authority':
            queries += [sql.SQL('SELECT * FROM {} LIMIT 0').format(target(policy)),
                        sql.SQL('INSERT INTO {} SELECT * FROM {} WHERE false').format(target(policy), target(policy))]
        for query in queries:
            with connect_runtime(dsns[kind], policy, kind) as conn, pytest.raises(errors.InsufficientPrivilege):
                assert conn.pgconn.used_password
                if kind == 'supervisor':
                    conn.execute('SET TRANSACTION READ WRITE')
                conn.execute(query)
    for query in (sql.SQL('UPDATE {} SET revision=revision').format(target(policy)),
                  sql.SQL('DELETE FROM {}').format(target(policy))):
        with base.connect() as conn, pytest.raises(errors.RaiseException, match='immutable'):
            owner(conn, policy)
            conn.execute(query)
    with base.connect() as conn:
        assert bytes(conn.execute(sql.SQL('SELECT payload_raw FROM {}').format(target(policy))).fetchone()['payload_raw']) == row['payload_raw']
        assert audit_runtime_roles(conn, policy)['tables'] >= len(TABLES) + 1
        privileges = ['SELECT', 'INSERT', 'UPDATE', 'DELETE', 'TRUNCATE', 'REFERENCES', 'TRIGGER']
        for kind, role in policy.roles.items():
            for privilege in privileges:
                granted = conn.execute('SELECT has_table_privilege(%s,%s,%s) AS allowed',
                    (role, policy.schema + '.crop_cycle_research_results', privilege)).fetchone()['allowed']
                assert granted is (kind == 'authority' and privilege in {'SELECT', 'INSERT'})
            assert not conn.execute("SELECT has_function_privilege(%s,%s,'EXECUTE') AS allowed",
                (role, policy.schema + '.reject_cycle_crop_result_change()')).fetchone()['allowed']


@pytest.mark.parametrize('schema_login_scope', [True, {'crop_cycle_result_storage': False}],
    ids=['missing', 'false'], indirect=True)
def test_cycle_storage_missing_false_denies_new_table_without_changing_existing_profile(schema_login_scope):
    from app.crop_cycle_result_schema import install_cycle_crop_result_schema
    from app.runtime_login import connect_runtime
    from app.runtime_roles import _tables
    base, policy, dsns = schema_login_scope
    assert policy.crop_cycle_result_storage is False and _tables(policy) == TABLES
    _, _, target, owner = cycle_schema_helpers()
    with base.connect() as conn:
        owner(conn, policy)
        install_cycle_crop_result_schema(conn, policy.schema)
    with base.connect() as conn:
        audit_runtime_roles(conn, policy)
    for kind in policy.roles:
        for query in (sql.SQL('SELECT * FROM {} LIMIT 0').format(target(policy)),
                      sql.SQL('INSERT INTO {} SELECT * FROM {} WHERE false').format(target(policy), target(policy)),
                      sql.SQL('UPDATE {} SET revision=revision').format(target(policy)),
                      sql.SQL('DELETE FROM {}').format(target(policy)), sql.SQL('TRUNCATE {}').format(target(policy))):
            with connect_runtime(dsns[kind], policy, kind) as conn, pytest.raises(errors.InsufficientPrivilege):
                assert conn.pgconn.used_password
                if kind == 'supervisor':
                    conn.execute('SET TRANSACTION READ WRITE')
                conn.execute(query)


@pytest.mark.parametrize('schema_login_scope', [{'crop_cycle_result_storage': True}], indirect=True)
@pytest.mark.parametrize('drift', ['worker_select', 'authority_update', 'public_select',
    'authority_column', 'authority_missing', 'authority_grant_option', 'routine_execute'])
def test_cycle_profile_drift_fails_whole_current_audit(schema_login_scope, drift):
    base, policy, _ = schema_login_scope
    _, _, target, _ = cycle_schema_helpers()
    with base.connect() as conn:
        if drift == 'public_select':
            conn.execute(sql.SQL('GRANT SELECT ON {} TO PUBLIC').format(target(policy)))
        elif drift == 'authority_missing':
            conn.execute(sql.SQL('REVOKE SELECT ON {} FROM {}').format(target(policy), sql.Identifier(policy.roles['authority'])))
        elif drift == 'routine_execute':
            conn.execute(sql.SQL('GRANT EXECUTE ON FUNCTION {}.reject_cycle_crop_result_change() TO {}').format(
                sql.Identifier(policy.schema), sql.Identifier(policy.roles['authority'])))
        else:
            privilege = {'worker_select': 'SELECT', 'authority_update': 'UPDATE',
                         'authority_column': 'UPDATE (revision)', 'authority_grant_option': 'SELECT'}[drift]
            kind = 'worker' if drift == 'worker_select' else 'authority'
            suffix = sql.SQL(' WITH GRANT OPTION') if drift == 'authority_grant_option' else sql.SQL('')
            conn.execute(sql.SQL('GRANT {} ON {} TO {}{}').format(sql.SQL(privilege), target(policy),
                sql.Identifier(policy.roles[kind]), suffix))
    with base.connect() as conn, pytest.raises(RolePolicyHold):
        audit_runtime_roles(conn, policy)


@pytest.mark.parametrize('schema_login_scope', [{'crop_startup_result_storage': True,
    'crop_cycle_result_storage': True}], indirect=True)
def test_cycle_selected_profile_preserves_existing_v3_bytes(schema_login_scope):
    from app.runtime_login import connect_runtime
    base, policy, dsns = schema_login_scope
    fixture_row, insert, target, _ = cycle_schema_helpers()
    old = startup_schema_row(base, policy)
    new = fixture_row(base, policy)
    with connect_runtime(dsns['authority'], policy, 'authority') as conn:
        insert_startup_schema_row(conn, policy, old)
        insert(conn, policy, new)
    for _ in range(2):
        with connect_runtime(dsns['authority'], policy, 'authority') as conn:
            actual = conn.execute(sql.SQL('SELECT payload_raw FROM {}.crop_startup_research_results').format(
                sql.Identifier(policy.schema))).fetchone()
            assert bytes(actual['payload_raw']) == old['payload_raw']
            assert bytes(conn.execute(sql.SQL('SELECT payload_raw FROM {}').format(target(policy))).fetchone()['payload_raw']) == new['payload_raw']
