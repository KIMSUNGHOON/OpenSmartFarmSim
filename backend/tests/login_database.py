"""Private test credentials and optional local cluster, never production setup."""

from pathlib import Path
import os
import secrets
import shlex
import socket
import subprocess
import tempfile
from uuid import uuid4

import psycopg
from psycopg import sql
from psycopg.conninfo import conninfo_to_dict, make_conninfo
import pytest

from app.db import install_schema
from app.job_store import JobStore
from app.runtime_roles import RuntimeLoginPolicy, install_runtime_roles
from test_jobs import synthetic_principal
from test_runtime_roles import owned_scope


@pytest.fixture(scope="module")
def login_database():
    dsn = os.environ.get("OSSF_TEST_PG_DSN")
    if not dsn:
        pytest.skip("OSSF_TEST_PG_DSN is unset")
    configured = conninfo_to_dict(dsn)
    if configured.get("host", "").startswith("/"):
        binary_path = os.environ.get("OSSF_TEST_PG_BIN")
        if binary_path is None:
            with psycopg.connect(dsn) as conn:
                data_directory = Path(conn.execute("SHOW data_directory").fetchone()[0])
            binary_path = str(Path(shlex.split((data_directory / "postmaster.opts").read_text())[0]).parent)
        binary = Path(binary_path)
        assert (binary / "initdb").is_file() and (binary / "pg_ctl").is_file()
        with tempfile.TemporaryDirectory(prefix="ossf-login-pg-") as directory:
            root = Path(directory); data = root / "data"; sockets = root / "socket"
            sockets.mkdir(mode=0o700)
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as probe:
                probe.bind(("127.0.0.1", 0)); port = probe.getsockname()[1]
            subprocess.run([str(binary / "initdb"), "-D", str(data), "-U", "ossf_login_admin",
                "--auth-local=trust", "--auth-host=scram-sha-256", "--no-locale", "--encoding=UTF8"],
                check=True, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE, timeout=30)
            subprocess.run([str(binary / "pg_ctl"), "-D", str(data), "-l", str(root / "server.log"),
                "-w", "-t", "10", "start", "-o", f"-h 127.0.0.1 -p {port} -k {sockets}"],
                check=True, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE, timeout=20)
            try:
                yield {"admin": make_conninfo(host=str(sockets), port=port, dbname="postgres", user="ossf_login_admin"),
                    "host": "127.0.0.1", "port": port, "database": "postgres"}
            finally:
                subprocess.run([str(binary / "pg_ctl"), "-D", str(data), "-m", "fast", "-w", "-t", "10", "stop"],
                    check=True, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE, timeout=20)
    else:
        # A stale hosted trust setup must fail rather than silently become login proof.
        with psycopg.connect(dsn, require_auth="scram-sha-256") as conn:
            assert conn.pgconn.used_password
        yield {"admin": dsn, "host": configured["host"], "port": configured["port"],
               "database": configured["dbname"]}


@pytest.fixture
def login_scope(login_database, tmp_path, request):
    database = login_database
    schema = "login_test_" + uuid4().hex
    base = JobStore(database["admin"], schema, tmp_path / "artifacts", principal_provider=synthetic_principal)
    with base.connect() as conn:
        conn.execute(sql.SQL("CREATE SCHEMA {}").format(sql.Identifier(schema)))
        install_schema(conn, schema)
    suffix = uuid4().hex
    policy = RuntimeLoginPolicy(schema, "login_owner_" + suffix, "login_" + suffix,
                                database["database"], market_calculation=(
                                    type(getattr(request, "param", None)) is dict and
                                    request.param.get("market_calculation") is True),
                                break_even_calculation=(
                                    type(getattr(request, "param", None)) is dict and
                                    request.param.get("break_even_calculation") is True),
                                market_source_storage=(
                                    type(getattr(request, "param", None)) is dict and
                                    request.param.get("market_source_storage") is True))
    try:
        with owned_scope(base, policy):
            with base.connect() as conn:
                install_runtime_roles(conn, policy)
            dsns = {}
            for kind, role in policy.roles.items():
                password = secrets.token_hex(32)
                passfile = tmp_path / (kind + ".pgpass")
                passfile.write_text(f"{database['host']}:{database['port']}:{database['database']}:{role}:{password}\n")
                passfile.chmod(0o600)
                if getattr(request, "param", True):
                    with base.connect() as conn:
                        # Only this fixture's provisioner sees the verifier; never put plaintext in SQL.
                        conn.execute("SET LOCAL log_statement='none'")
                        conn.execute("SET LOCAL log_min_duration_statement=-1")
                        conn.execute("SET LOCAL log_min_error_statement='panic'")
                        verifier = conn.pgconn.encrypt_password(password.encode(), role.encode(), b"scram-sha-256")
                        conn.execute(sql.SQL("ALTER ROLE {} PASSWORD {}").format(
                            sql.Identifier(role), sql.Literal(verifier.decode())))
                dsns[kind] = make_conninfo(host=database["host"], port=database["port"],
                    dbname=database["database"], user=role, passfile=str(passfile), sslmode="disable")
            yield base, policy, dsns
    finally:
        for kind in policy.roles:
            (tmp_path / (kind + ".pgpass")).unlink(missing_ok=True)
        with base.connect() as conn:
            conn.execute(sql.SQL("DROP SCHEMA {} CASCADE").format(sql.Identifier(schema)))
