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


@pytest.fixture
def role_scope(pg_store):
    suffix = uuid4().hex
    policy = RuntimeRolePolicy(pg_store.schema, "ossf_owner_" + suffix, "ossf_" + suffix)
    with pg_store.connect() as conn:
        original = conn.execute("SELECT current_user AS name").fetchone()["name"]
        conn.execute(sql.SQL("CREATE ROLE {} NOLOGIN").format(sql.Identifier(policy.owner)))
        install_execution_attestation_schema(conn, pg_store.schema)
        install_thermal_run_schema(conn, pg_store.schema)
        install_market_hold_schema(conn, pg_store.schema)
        conn.execute(sql.SQL("ALTER SCHEMA {} OWNER TO {}").format(
            sql.Identifier(policy.schema), sql.Identifier(policy.owner)))
        for table in TABLES:
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


@pytest.mark.parametrize("fault", ["column", "membership", "grant_option", "defaults"])
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
        else:
            conn.execute(sql.SQL("ALTER DEFAULT PRIVILEGES FOR ROLE {} GRANT EXECUTE ON FUNCTIONS TO PUBLIC")
                         .format(sql.Identifier(policy.owner)))
            assert conn.execute("""SELECT 1 FROM pg_default_acl d JOIN pg_roles r ON r.oid=d.defaclrole
                WHERE r.rolname=%s AND d.defaclnamespace=0 AND d.defaclobjtype='f'""",
                (policy.owner,)).fetchone() is None
    with store.connect() as conn, pytest.raises(RolePolicyHold):
        audit_runtime_roles(conn, policy)


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
