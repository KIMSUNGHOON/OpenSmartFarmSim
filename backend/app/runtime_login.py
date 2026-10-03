"""Authenticated SQL profiles; this does not isolate credential holders by UID."""

import psycopg
from psycopg.conninfo import conninfo_to_dict
from psycopg.rows import dict_row

from .runtime_roles import RuntimeLoginPolicy, RolePolicyHold


def verify_runtime_identity(conn, policy, kind):
    if not isinstance(policy, RuntimeLoginPolicy) or type(kind) is not str or kind not in policy.roles:
        raise RolePolicyHold("runtime_login_rejected")
    role = policy.roles[kind]
    if (conn.info.user != role or conn.info.dbname != policy.database or
            conn.info.get_parameters().get("require_auth") != "scram-sha-256" or
            not conn.pgconn.used_password):
        raise RolePolicyHold("runtime_login_rejected")
    row = conn.execute("SELECT session_user AS authenticated, current_user AS effective, "
                       "current_database() AS database").fetchone()
    if row != {"authenticated": role, "effective": role, "database": policy.database}:
        raise RolePolicyHold("runtime_login_rejected")


def connect_runtime(dsn, policy, kind):
    conn = None
    try:
        if not isinstance(policy, RuntimeLoginPolicy) or type(kind) is not str or kind not in policy.roles:
            raise ValueError("invalid runtime binding")
        configured = conninfo_to_dict(dsn)
        if configured.get("user") != policy.roles[kind] or configured.get("dbname") != policy.database:
            raise ValueError("runtime binding differs")
        readonly = kind == "supervisor"
        options = configured.get("options", "") + (
            " -c statement_timeout=2000 -c default_transaction_read_only=on" if readonly else
            " -c statement_timeout=5000")
        conn = psycopg.connect(dsn, row_factory=dict_row, connect_timeout=3,
            require_auth="scram-sha-256", options=options)
        verify_runtime_identity(conn, policy, kind)
        # Identity inspection must not leave a transaction open (advisory reservations set autocommit).
        conn.commit()
        return conn
    except Exception:
        if conn is not None:
            conn.close()
        raise RolePolicyHold("runtime_login_rejected") from None
