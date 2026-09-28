"""Real SCRAM logins with local/hosted disposable DB; shared OS UID/test keys."""

import copy
import os
from pathlib import Path
import socket
import struct
import sys
import threading
from uuid import uuid4

import psycopg
from psycopg import sql, errors
from psycopg.conninfo import make_conninfo, conninfo_to_dict
from psycopg.rows import dict_row
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from app.cli_supervisor_service import _SupervisorReads
from app.content_access import ContentAccess
from app.job_store import JobStore
from app.runtime_login import connect_runtime, verify_runtime_identity
from app.runtime_roles import (RuntimeRolePolicy, RuntimeLoginPolicy, RolePolicyHold,
    TABLES, audit_runtime_roles, install_runtime_roles)
from login_database import login_database, login_scope
from test_authority_rpc import running_authority
from test_cli_supervisor_service import approved, running_server
from test_cli_worker import _worker
from test_supervised_cli_worker import decision_input


@pytest.mark.parametrize("kind", ["request", "worker", "supervisor", "authority"])
def test_direct_authenticated_identity_and_idle_connection(login_scope, kind):
    base, policy, dsns = login_scope
    with connect_runtime(dsns[kind], policy, kind) as conn:
        assert conn.info.user == policy.roles[kind] and conn.pgconn.used_password
        assert conn.info.transaction_status == psycopg.pq.TransactionStatus.IDLE
        verify_runtime_identity(conn, policy, kind)
        assert conn.execute("SHOW statement_timeout").fetchone()["statement_timeout"] == (
            "2s" if kind == "supervisor" else "5s")
    with base.connect() as conn:
        assert audit_runtime_roles(conn, policy)["policy_version"] == "runtime-login-policy-v2"
        legacy = RuntimeRolePolicy(policy.schema, policy.owner, policy.prefix)
        with pytest.raises(RolePolicyHold, match="role_attributes"):
            audit_runtime_roles(conn, legacy)


@pytest.mark.parametrize("kind", ["request", "worker"])
def test_authenticated_general_logins_deny_all_base_access_and_role_escalation(login_scope, kind):
    _, policy, dsns = login_scope
    for table in TABLES:
        for operation in ("SELECT", "UPDATE", "INSERT", "DELETE", "TRUNCATE"):
            target = sql.SQL("{}.{}").format(sql.Identifier(policy.schema), sql.Identifier(table))
            query = {
                "SELECT": sql.SQL("SELECT * FROM {} LIMIT 0"),
                "UPDATE": sql.SQL("UPDATE {} SET tenant_id='tenant-a' WHERE false"),
                "INSERT": sql.SQL("INSERT INTO {} (tenant_id) VALUES ('tenant-a')"),
                "DELETE": sql.SQL("DELETE FROM {} WHERE false"),
                "TRUNCATE": sql.SQL("TRUNCATE TABLE {}"),
            }[operation].format(target)
            with connect_runtime(dsns[kind], policy, kind) as conn, pytest.raises(errors.InsufficientPrivilege):
                conn.execute(query)
    for role in (policy.owner, policy.roles["authority"], policy.roles["supervisor"]):
        with connect_runtime(dsns[kind], policy, kind) as conn, pytest.raises(errors.InsufficientPrivilege):
            conn.execute(sql.SQL("SET ROLE {}").format(sql.Identifier(role)))


@pytest.mark.parametrize("fault", ["wrong_password", "missing_password", "user", "database", "nologin"])
def test_runtime_connect_rejects_missing_wrong_or_changed_login(login_scope, tmp_path, fault):
    base, policy, dsns = login_scope
    dsn = dsns["authority"]
    if fault in {"wrong_password", "missing_password"}:
        private = tmp_path / "invalid.pgpass"
        private.write_text("*:*:*:*:incorrect\n" if fault == "wrong_password" else "")
        private.chmod(0o600)
        dsn = make_conninfo(dsn, passfile=str(private))
    elif fault == "user": dsn = make_conninfo(dsn, user=policy.roles["supervisor"])
    elif fault == "database": dsn = make_conninfo(dsn, dbname="different_database")
    else:
        with base.connect() as conn:
            conn.execute(sql.SQL("ALTER ROLE {} NOLOGIN").format(sql.Identifier(policy.roles["authority"])))
    with pytest.raises(RolePolicyHold) as error:
        connect_runtime(dsn, policy, "authority")
    assert str(error.value) == "runtime_login_rejected"


def test_conflicting_dsn_bounds_are_forced_on_job_and_supervisor_paths(login_scope):
    _, policy, dsns = login_scope
    for kind in ("authority", "supervisor"):
        dsn = make_conninfo(dsns[kind], require_auth="none", connect_timeout="0",
            options="-c statement_timeout=0 -c default_transaction_read_only=off")
        store = JobStore(dsn, policy.schema, Path("/tmp/unused"), runtime_identity=(policy, kind))
        reader = _SupervisorReads(store) if kind == "supervisor" else store
        with reader.connect() as conn:
            verify_runtime_identity(conn, policy, kind)
            assert conn.info.get_parameters()["connect_timeout"] == "3"
            assert conn.execute("SHOW statement_timeout").fetchone()["statement_timeout"] == (
                "2s" if kind == "supervisor" else "5s")
            if kind == "supervisor":
                assert conn.execute("SHOW transaction_read_only").fetchone()["transaction_read_only"] == "on"


@pytest.mark.parametrize("authorization", ["ROLE", "SESSION AUTHORIZATION"])
def test_administrator_cannot_launder_login_identity(login_scope, authorization):
    base, policy, _ = login_scope
    with base.connect() as conn:
        conn.execute(sql.SQL("SET {} {}").format(sql.SQL(authorization), sql.Identifier(policy.roles["authority"])))
        with pytest.raises(RolePolicyHold, match="runtime_login_rejected"):
            verify_runtime_identity(conn, policy, "authority")


@pytest.mark.parametrize("drift", ["inherit", "limit", "membership", "grant"])
def test_login_policy_rejects_attributes_membership_and_grant_drift(login_scope, drift):
    base, policy, _ = login_scope
    worker = sql.Identifier(policy.roles["worker"])
    with base.connect() as conn:
        query = {
            "inherit": sql.SQL("ALTER ROLE {} INHERIT").format(worker),
            "limit": sql.SQL("ALTER ROLE {} CONNECTION LIMIT -1").format(worker),
            "membership": sql.SQL("GRANT {} TO {}").format(sql.Identifier(policy.roles["authority"]), worker),
            "grant": sql.SQL("GRANT SELECT ON {}.jobs TO {}").format(sql.Identifier(policy.schema), worker),
        }[drift]
        conn.execute(query)
    with base.connect() as conn, pytest.raises(RolePolicyHold):
        audit_runtime_roles(conn, policy)


def test_repeat_install_keeps_provisioned_password_and_wrong_database_is_rejected(login_scope):
    base, policy, dsns = login_scope
    with base.connect() as conn, pytest.raises(RolePolicyHold, match="already_exist"):
        install_runtime_roles(conn, policy)
    with connect_runtime(dsns["authority"], policy, "authority") as conn:
        verify_runtime_identity(conn, policy, "authority")
    wrong = RuntimeLoginPolicy(policy.schema, policy.owner, policy.prefix, "wrong_database")
    with base.connect() as conn, pytest.raises(RolePolicyHold, match="database_scope"):
        install_runtime_roles(conn, wrong)


@pytest.mark.parametrize("login_scope", [False], indirect=True)
def test_fresh_login_roles_cannot_authenticate_before_separate_provisioning(login_scope):
    base, policy, dsns = login_scope
    with base.connect() as conn:
        assert all(row["rolpassword"] is None for row in conn.execute(
            "SELECT rolpassword FROM pg_authid WHERE rolname=ANY(%s)",
            (list(policy.roles.values()),)).fetchall())
    with pytest.raises(RolePolicyHold, match="runtime_login_rejected"):
        connect_runtime(dsns["authority"], policy, "authority")


@pytest.mark.parametrize("stage", ["research", "collection_review", "assessment"])
@pytest.mark.parametrize("shared_content", [False, True])
def test_three_ai_stages_with_separately_authenticated_services(login_scope, tmp_path, stage, shared_content):
    base, policy, dsns = login_scope
    store, local = _worker(base, tmp_path, mode="valid_slow", authority=approved)
    if shared_content:
        store.content_access = ContentAccess(os.geteuid(), os.getegid())
    job = store.submit("tenant-a", stage, decision_input(stage), uuid4().hex)
    supervisor = copy.copy(store)
    supervisor._dsn, supervisor.runtime_identity = dsns["supervisor"], (policy, "supervisor")
    authority = copy.copy(store)
    authority._dsn, authority.runtime_identity = dsns["authority"], (policy, "authority")
    with running_server(supervisor, local, tmp_path, proceed=True) as server:
        with running_authority(authority, policy, server, proceed=True) as (client, _):
            result = client.run_once()
            assert result.job_id == job["job_id"] and result.state == "succeeded", result
    assert store.get_publication("tenant-a", job["job_id"])["decision_id"] == result.decision_id


def test_authority_credential_holder_can_write_without_rpc(login_scope, tmp_path):
    base, policy, dsns = login_scope
    store, _ = _worker(base, tmp_path)
    job = store.submit("tenant-a", "research", decision_input("research"), uuid4().hex)
    with connect_runtime(dsns["authority"], policy, "authority") as conn:
        assert conn.execute(sql.SQL("UPDATE {}.jobs SET cancel_requested=true WHERE job_id=%s").format(
            sql.Identifier(policy.schema)), (job["job_id"],)).rowcount == 1
    # Authenticated SQL rights do not force credential holders to use server validators.
    with base.connect() as conn:
        assert conn.execute(sql.SQL("SELECT cancel_requested FROM {}.jobs WHERE job_id=%s").format(
            sql.Identifier(policy.schema)), (job["job_id"],)).fetchone()["cancel_requested"]


def test_libpq_rejects_authentication_ok_without_scram_challenge(login_scope):
    _, policy, dsns = login_scope
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as listener:
        listener.bind(("127.0.0.1", 0)); listener.listen(2); listener.settimeout(5)
        failures = []
        def peer():
            try:
                for _ in range(2):
                    conn, _ = listener.accept()
                    with conn:
                        conn.settimeout(5)
                        size = struct.unpack("!I", conn.recv(4, socket.MSG_WAITALL))[0]
                        assert 8 <= size <= 4096
                        conn.recv(size - 4, socket.MSG_WAITALL)
                        def message(kind, payload):
                            return kind + struct.pack("!I", len(payload) + 4) + payload
                        wire = message(b"R", struct.pack("!I", 0))
                        wire += message(b"S", b"server_version\x0018.6\x00")
                        wire += message(b"S", b"client_encoding\x00UTF8\x00")
                        wire += message(b"K", struct.pack("!II", 12345, 1))
                        wire += message(b"Z", b"I")
                        conn.sendall(wire)
                        conn.recv(1)
            except Exception as exc:
                failures.append(type(exc).__name__)
        thread = threading.Thread(target=peer)
        thread.start()
        dsn = make_conninfo(dsns["authority"], host="127.0.0.1", port=listener.getsockname()[1],
                           require_auth="none", sslmode="disable", gssencmode="disable")
        with psycopg.connect(dsn) as control:
            assert not control.pgconn.used_password
        with pytest.raises(RolePolicyHold, match="runtime_login_rejected"):
            connect_runtime(dsn, policy, "authority")
        thread.join(timeout=6)
        assert not thread.is_alive() and not failures
