"""Separate authenticated planning logins; test provisioner/key share one OS UID."""

from datetime import datetime, timezone
from hashlib import sha256
import json
from pathlib import Path
import sys
from uuid import uuid4

from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from cryptography.hazmat.primitives.serialization import Encoding, PublicFormat
from psycopg import errors, sql
from psycopg.conninfo import make_conninfo
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from app.planning_events import PlanningEventStore, PlanningAuthority, DecisionContextVerifier, PlanningHold, install_planning_schema
from app.planning_roles import PlanningLoginPolicy, audit_planning_roles, install_planning_roles
from app.runtime_roles import RolePolicyHold
from login_database import login_database
from test_thermal_run_store import run_store, raw_inputs


@pytest.fixture
def scope(login_database, tmp_path):
    suffix = uuid4().hex
    policy = PlanningLoginPolicy("planning_login_" + suffix, "planning_owner_" + suffix,
                                 "plan_" + suffix, login_database["database"])
    principal = {"authenticated": True, "tenant_id": "tenant-a",
                 "scopes": ("planning_event_issue", "planning_event_read")}
    admin = PlanningEventStore(login_database["admin"], policy.schema, principal_provider=lambda: principal)
    with admin.connect() as conn:
        original = conn.execute("SELECT current_user AS name").fetchone()["name"]
        conn.execute(sql.SQL("CREATE SCHEMA {}").format(sql.Identifier(policy.schema)))
        install_planning_schema(conn, policy.schema)
        conn.execute(sql.SQL("CREATE ROLE {} NOLOGIN").format(sql.Identifier(policy.owner)))
        conn.execute(sql.SQL("ALTER SCHEMA {} OWNER TO {}").format(sql.Identifier(policy.schema), sql.Identifier(policy.owner)))
        conn.execute(sql.SQL("ALTER TABLE {}.planning_events OWNER TO {}").format(sql.Identifier(policy.schema), sql.Identifier(policy.owner)))
        conn.execute(sql.SQL("ALTER FUNCTION {}.reject_planning_change() OWNER TO {}").format(sql.Identifier(policy.schema), sql.Identifier(policy.owner)))
    try:
        with admin.connect() as conn:
            install_planning_roles(conn, policy)
        dsns = {}
        for kind, role in policy.roles.items():
            # Self-authored test credential, kept only in a private temporary passfile.
            password = uuid4().hex + uuid4().hex
            passfile = tmp_path / (kind + ".pgpass")
            passfile.write_text(f"{login_database['host']}:{login_database['port']}:{login_database['database']}:{role}:{password}\n")
            passfile.chmod(0o600)
            with admin.connect() as conn:
                conn.execute("SET LOCAL log_statement='none'")
                conn.execute("SET LOCAL log_min_duration_statement=-1")
                conn.execute("SET LOCAL log_min_error_statement='panic'")
                verifier = conn.pgconn.encrypt_password(password.encode(), role.encode(), b"scram-sha-256")
                conn.execute(sql.SQL("ALTER ROLE {} PASSWORD {}").format(sql.Identifier(role), sql.Literal(verifier.decode())))
            dsns[kind] = make_conninfo(host=login_database["host"], port=login_database["port"],
                dbname=login_database["database"], user=role, passfile=str(passfile), sslmode="disable")
        stores = {kind: PlanningEventStore(dsn, policy.schema, principal_provider=lambda: principal,
                    runtime_identity=(policy, kind)) for kind, dsn in dsns.items()}
        yield admin, policy, stores, dsns
    finally:
        with admin.connect() as conn:
            for role in policy.roles.values():
                if conn.execute("SELECT 1 FROM pg_roles WHERE rolname=%s", (role,)).fetchone():
                    conn.execute(sql.SQL("DROP OWNED BY {}").format(sql.Identifier(role)))
                    conn.execute(sql.SQL("DROP ROLE {}").format(sql.Identifier(role)))
            conn.execute(sql.SQL("REASSIGN OWNED BY {} TO {}").format(sql.Identifier(policy.owner), sql.Identifier(original)))
            conn.execute(sql.SQL("DROP OWNED BY {}").format(sql.Identifier(policy.owner)))
            conn.execute(sql.SQL("DROP ROLE {}").format(sql.Identifier(policy.owner)))
            conn.execute(sql.SQL("DROP SCHEMA {} CASCADE").format(sql.Identifier(policy.schema)))


def test_real_writer_and_readonly_login_verify_durable_context(scope):
    _admin, policy, stores, _dsns = scope
    key = Ed25519PrivateKey.generate()
    public = key.public_key().public_bytes(Encoding.Raw, PublicFormat.Raw)
    authority = PlanningAuthority(stores["authority"], "test-planning-v1", key)
    verifier = DecisionContextVerifier({"test-planning-v1": public}, stores["supervisor"].read_event)
    raw, signature = authority.issue("tenant-a", "snapshot-a", claim_mode="ex_post_replay", decision_time_kind="actual")
    assert verifier(raw, signature)["decision_time_kind"] == "actual"
    for kind, store in stores.items():
        with store.connect() as conn:
            assert conn.info.user == policy.roles[kind] and conn.pgconn.used_password
            assert conn.execute("SHOW default_transaction_read_only").fetchone()["default_transaction_read_only"] == (
                "on" if kind == "supervisor" else "off")


def test_authenticated_planning_context_connects_to_existing_snapshot_store(scope, run_store):
    _admin, _policy, stores, _dsns = scope
    key = Ed25519PrivateKey.generate()
    public = key.public_key().public_bytes(Encoding.Raw, PublicFormat.Raw)
    snapshot = run_store.put_snapshot("tenant-a", *raw_inputs())
    authority = PlanningAuthority(stores["authority"], "test-planning-v1", key)
    raw, signature = authority.issue("tenant-a", snapshot, claim_mode="ex_post_replay",
                                    decision_time_kind="actual")
    run_store._context_verifier = DecisionContextVerifier(
        {"test-planning-v1": public}, stores["supervisor"].read_event)
    context_id = run_store.put_decision_context("tenant-a", raw, signature)
    stored = run_store.get_decision_context("tenant-a", snapshot, context_id)
    assert stored["context_sha256"] == sha256(raw).hexdigest()
    assert stored["decision_at_utc"] == json.loads(raw)["decision_at_utc"]


@pytest.mark.parametrize("kind", ["authority", "supervisor"])
def test_logins_cannot_override_server_timestamp(scope, kind):
    _admin, _policy, stores, _dsns = scope
    with stores[kind].connect() as conn, pytest.raises(errors.InsufficientPrivilege):
        conn.execute("SET default_transaction_read_only=off")
        conn.commit()
        conn.execute(sql.SQL("INSERT INTO {}.planning_events (recorded_at) VALUES (%s)").format(
            sql.Identifier(stores[kind].schema)), (datetime(2000, 1, 1, tzinfo=timezone.utc),))


@pytest.mark.parametrize("kind", ["authority", "supervisor"])
@pytest.mark.parametrize("operation", ["UPDATE", "DELETE", "TRUNCATE", "ALTER", "OWNER", "OTHER_LOGIN"])
def test_authenticated_profiles_cannot_mutate_or_escalate(scope, kind, operation):
    _admin, policy, stores, _dsns = scope
    namespace = sql.Identifier(policy.schema)
    other = "supervisor" if kind == "authority" else "authority"
    queries = {
        "UPDATE": sql.SQL("UPDATE {}.planning_events SET context_signature=%s WHERE false").format(namespace),
        "DELETE": sql.SQL("DELETE FROM {}.planning_events WHERE false").format(namespace),
        "TRUNCATE": sql.SQL("TRUNCATE {}.planning_events").format(namespace),
        "ALTER": sql.SQL("ALTER TABLE {}.planning_events DISABLE TRIGGER ALL").format(namespace),
        "OWNER": sql.SQL("SET ROLE {}").format(sql.Identifier(policy.owner)),
        "OTHER_LOGIN": sql.SQL("SET ROLE {}").format(sql.Identifier(policy.roles[other]))}
    with stores[kind].connect() as conn, pytest.raises(errors.InsufficientPrivilege):
        conn.execute("SET default_transaction_read_only=off")
        conn.commit()
        conn.execute(queries[operation], ("0" * 128,) if operation == "UPDATE" else ())


def test_reader_cannot_insert_any_event_columns_even_after_readonly_override(scope):
    _admin, policy, stores, _dsns = scope
    with stores["supervisor"].connect() as conn, pytest.raises(errors.InsufficientPrivilege):
        conn.execute("SET default_transaction_read_only=off")
        conn.commit()
        conn.execute(sql.SQL("INSERT INTO {}.planning_events (tenant_id) VALUES ('tenant-a')").format(
            sql.Identifier(policy.schema)))


@pytest.mark.parametrize("drift", ["timestamp_insert", "table_insert", "public_select", "public_column",
                                  "public_schema", "membership", "superuser", "default_grant", "function",
                                  "connect_grant_option", "usage_grant_option"])
def test_every_bound_connection_rejects_effective_catalog_drift(scope, drift):
    admin, policy, stores, _dsns = scope
    namespace = sql.Identifier(policy.schema)
    writer = sql.Identifier(policy.roles["authority"])
    queries = {
        "timestamp_insert": sql.SQL("GRANT INSERT(recorded_at) ON TABLE {}.planning_events TO {}").format(namespace, writer),
        "table_insert": sql.SQL("GRANT INSERT ON TABLE {}.planning_events TO {}").format(namespace, writer),
        "public_select": sql.SQL("GRANT SELECT ON TABLE {}.planning_events TO PUBLIC").format(namespace),
        "public_column": sql.SQL("GRANT SELECT(context_raw) ON TABLE {}.planning_events TO PUBLIC").format(namespace),
        "public_schema": sql.SQL("GRANT CREATE ON SCHEMA {} TO PUBLIC").format(namespace),
        "connect_grant_option": sql.SQL("GRANT CONNECT ON DATABASE {} TO {} WITH GRANT OPTION").format(
            sql.Identifier(policy.database), writer),
        "usage_grant_option": sql.SQL("GRANT USAGE ON SCHEMA {} TO {} WITH GRANT OPTION").format(namespace, writer),
        "membership": sql.SQL("GRANT {} TO {}").format(sql.Identifier(policy.roles["supervisor"]), writer),
        "superuser": sql.SQL("ALTER ROLE {} SUPERUSER").format(writer),
        "default_grant": sql.SQL("ALTER DEFAULT PRIVILEGES FOR ROLE {} GRANT SELECT ON TABLES TO PUBLIC").format(
            sql.Identifier(policy.owner)),
        "function": sql.SQL("GRANT EXECUTE ON FUNCTION {}.reject_planning_change() TO {}").format(namespace, writer)}
    with admin.connect() as conn:
        conn.execute(queries[drift])
    for store in stores.values():
        with pytest.raises(RolePolicyHold, match="planning_login_or_grants_rejected"):
            store.connect()


def test_reinstallation_preserves_existing_credentials_and_matrix(scope):
    admin, policy, stores, _dsns = scope
    with admin.connect() as conn, pytest.raises(RolePolicyHold, match="planning_logins_already_exist"):
        install_planning_roles(conn, policy)
    for store in stores.values():
        with store.connect() as conn:
            assert audit_planning_roles(conn, policy)["policy_version"] == "planning-login-policy-v1"


def test_failed_postcreation_audit_rolls_back_all_fresh_logins_and_grants(scope):
    admin, policy, _stores, _dsns = scope
    fresh = PlanningLoginPolicy(policy.schema, policy.owner, "rejected_" + uuid4().hex[:24], policy.database)
    with admin.connect() as conn:
        conn.execute(sql.SQL("ALTER DEFAULT PRIVILEGES FOR ROLE {} GRANT SELECT ON TABLES TO {}").format(
            sql.Identifier(policy.owner), sql.Identifier(policy.roles["supervisor"])))
    with admin.connect() as conn, pytest.raises(RolePolicyHold):
        install_planning_roles(conn, fresh)
    with admin.connect() as conn:
        assert conn.execute("SELECT 1 FROM pg_roles WHERE rolname=ANY(%s)", (list(fresh.roles.values()),)).fetchone() is None
        conn.execute(sql.SQL("ALTER DEFAULT PRIVILEGES FOR ROLE {} REVOKE SELECT ON TABLES FROM {}").format(
            sql.Identifier(policy.owner), sql.Identifier(policy.roles["supervisor"])))
        assert audit_planning_roles(conn, policy)["roles"] == policy.roles


@pytest.mark.parametrize("path", ["owner_issuer", "reader_issuer", "owner_verifier", "writer_verifier", "callback_verifier"])
def test_default_authorities_reject_unbound_or_wrong_profile_sources(scope, path):
    admin, _policy, stores, _dsns = scope
    key = Ed25519PrivateKey.generate()
    public = {"test-planning-v1": key.public_key().public_bytes(Encoding.Raw, PublicFormat.Raw)}
    with pytest.raises(PlanningHold, match="planning_(writer|reader)_login_required"):
        if path == "owner_issuer": PlanningAuthority(admin, "test-planning-v1", key)
        elif path == "reader_issuer": PlanningAuthority(stores["supervisor"], "test-planning-v1", key)
        elif path == "owner_verifier": DecisionContextVerifier(public, admin.read_event)
        elif path == "writer_verifier": DecisionContextVerifier(public, stores["authority"].read_event)
        else: DecisionContextVerifier(public, lambda tenant, digest: None)
