"""Authenticated context/snapshot authority; existing grants are preserved."""

from pathlib import Path
import sys

from psycopg import sql
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from app.thermal_run_store import ThermalRunStore, ThermalStoreHold
from app.runtime_roles import RolePolicyHold
from login_database import login_database, login_scope
from test_thermal_run_store import raw_inputs


def store_for(scope, *, dsn=None, kind="authority"):
    base, policy, dsns = scope
    return ThermalRunStore(dsn or dsns["authority"], base.schema,
        gate_key=b"synthetic-test-store-key-32-bytes-long", release_verifier=lambda *_: None,
        principal_provider=lambda: {"authenticated": True, "tenant_id": "tenant-a",
                                    "scopes": ("thermal_snapshot_write", "thermal_snapshot_read")},
        runtime_identity=(policy, kind))


def test_real_authority_login_stores_and_reads_immutable_snapshot(login_scope):
    store = store_for(login_scope)
    snapshot = store.put_snapshot("tenant-a", *raw_inputs())
    assert store.get_snapshot("tenant-a", snapshot)["snapshot_id"] == snapshot
    with store.connect() as conn:
        assert conn.info.user == login_scope[1].roles["authority"] and conn.pgconn.used_password
        assert conn.execute("SELECT session_user AS name").fetchone()["name"] == conn.info.user


def test_snapshot_store_rejects_wrong_authenticated_login(login_scope):
    store = store_for(login_scope, dsn=login_scope[2]["supervisor"])
    with pytest.raises(RolePolicyHold, match="^runtime_login_rejected$"):
        store.connect()


def test_unsupported_profile_cannot_bind_snapshot_authority(login_scope):
    with pytest.raises(ValueError, match="authority login profile"):
        store_for(login_scope, kind="supervisor")


def test_each_bound_snapshot_connection_rejects_grant_drift(login_scope):
    base, policy, _ = login_scope
    store = store_for(login_scope)
    with base.connect() as conn:
        conn.execute(sql.SQL("GRANT UPDATE ON TABLE {}.thermal_input_snapshots TO {}").format(
            sql.Identifier(policy.schema), sql.Identifier(policy.roles["authority"])))
    with pytest.raises(ThermalStoreHold, match="^LOGIN_HOLD: runtime grants rejected$"):
        store.connect()
