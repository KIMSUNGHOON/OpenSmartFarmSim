"""Explicit root controller: fresh planner/caller UIDs and real SCRAM, test keys."""

from dataclasses import asdict
from hashlib import sha256
import json
import os
from pathlib import Path
import pwd
import select
import socket
import sys
import tempfile

from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from cryptography.hazmat.primitives.serialization import Encoding, PrivateFormat, PublicFormat, NoEncryption
from psycopg import sql
from psycopg.conninfo import conninfo_to_dict, make_conninfo
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from app.cli_ipc import receive
from app.thermal_run_store import ThermalRunStore
from test_planning_roles import scope, login_database
from login_database import login_scope
from test_thermal_run_store import raw_inputs
from uid_service_smoke import child, directory, private_file, denied, finished, listening, reap, AUTHORITY, ROGUE


PLANNING, PLANNING_GROUP = 11005, 11013


def test_distinct_uid_planning_command_and_authenticated_context_queue(scope, login_scope):
    assert os.geteuid() == 0, "explicit hosted root controller required"
    for uid in (PLANNING, AUTHORITY, ROGUE):
        with pytest.raises(KeyError): pwd.getpwuid(uid)
    admin, plan_policy, _stores, plan_dsns = scope
    base, job_policy, job_dsns = login_scope
    with tempfile.TemporaryDirectory(prefix="ossf-planning-uid-") as temporary:
        root = Path(temporary)
        root.chmod(0o755)
        service_home = directory(root / "service", PLANNING, PLANNING_GROUP, 0o700)
        caller_home = directory(root / "caller", AUTHORITY, PLANNING_GROUP, 0o700)
        rogue_home = directory(root / "rogue", ROGUE, PLANNING_GROUP, 0o700)
        endpoint = directory(root / "s", PLANNING, PLANNING_GROUP, 0o750) / "rpc"
        def copy_login(dsn, path, uid):
            source = Path(conninfo_to_dict(dsn)["passfile"])
            private_file(path, source.read_bytes(), uid, PLANNING_GROUP)
            return make_conninfo(dsn, passfile=str(path))
        writer = copy_login(plan_dsns["authority"], service_home / "writer.pgpass", PLANNING)
        reader = copy_login(plan_dsns["supervisor"], caller_home / "reader.pgpass", AUTHORITY)
        jobs = copy_login(job_dsns["authority"], caller_home / "jobs.pgpass", AUTHORITY)
        principal = lambda: {"authenticated": True, "tenant_id": "tenant-a",
                            "scopes": ("thermal_snapshot_write", "thermal_snapshot_read")}
        snapshots = ThermalRunStore(base._dsn, base.schema, gate_key=b"unused-synthetic-controller-key-32!",
                                    release_verifier=lambda *_: None, principal_provider=principal)
        snapshot_id = snapshots.put_snapshot("tenant-a", *raw_inputs())
        key = Ed25519PrivateKey.generate()
        key_path = private_file(service_home / "planning-key",
            key.private_bytes(Encoding.Raw, PrivateFormat.Raw, NoEncryption()), PLANNING, PLANNING_GROUP)
        public = key.public_key().public_bytes(Encoding.Raw, PublicFormat.Raw)
        service_config = private_file(service_home / "config.json", json.dumps(dict(
            policy=asdict(plan_policy), dsn=writer, private_key_file=str(key_path), key_id="test-planning-v1",
            snapshot={"tenant_id": "tenant-a", "snapshot_id": snapshot_id},
            settings=dict(socket_path=str(endpoint), caller_uid=AUTHORITY, tenant_id="tenant-a"))).encode(),
            PLANNING, PLANNING_GROUP)
        client_config = private_file(caller_home / "config.json", json.dumps(dict(
            uid=AUTHORITY, tenant_id="tenant-a", planning_policy=asdict(plan_policy), job_policy=asdict(job_policy),
            reader_dsn=reader, job_dsn=jobs, key_id="test-planning-v1", public_key=public.hex(),
            planning_uid=PLANNING, socket_path=str(endpoint), snapshot_id=snapshot_id,
            artifact_root=str(caller_home / "artifacts"),
            denied_paths=[str(key_path), str(service_config), str(service_home / "writer.pgpass")])).encode(),
            AUTHORITY, PLANNING_GROUP)
        application = Path(sys.executable).parents[2] / "code" / "backend"

        def service():
            denied(client_config)
            denied(caller_home / "reader.pgpass")
            denied(caller_home / "jobs.pgpass")
            os.chdir(application)
            os.execve(sys.executable, [sys.executable, "-B", "-m", "app.cli_plan",
                "--factory", "uid_planning_factory:create", "--max-sessions", "3"],
                {"HOME": str(service_home), "PATH": "/usr/bin:/bin", "LANG": "C.UTF-8",
                 "PYTHONPATH": str(application / "tests"), "OSSF_PLANNING_FIXTURE_CONFIG": str(service_config)})

        def caller():
            os.chdir(application)
            os.execve(sys.executable, [sys.executable, "-B", "-m", "uid_planning_client"],
                {"HOME": str(caller_home), "PATH": "/usr/bin:/bin", "LANG": "C.UTF-8",
                 "PYTHONPATH": str(application / "tests"), "OSSF_PLANNING_CLIENT_FIXTURE_CONFIG": str(client_config)})

        def rogue():
            denied(key_path)
            denied(service_home / "writer.pgpass")
            with socket.socket(socket.AF_UNIX) as conn:
                conn.connect(str(endpoint))
                assert receive(conn, 65536) == {"version": 1, "ok": False, "code": "planning_issue_rejected"}

        with child(PLANNING, PLANNING_GROUP, [PLANNING_GROUP], service, home=service_home) as service_handle:
            listening(endpoint, service_handle)
            with child(ROGUE, PLANNING_GROUP, [PLANNING_GROUP], rogue, home=rogue_home) as rogue_handle:
                finished(rogue_handle)
            with admin.connect() as conn:
                assert conn.execute(sql.SQL("SELECT count(*) AS n FROM {}.planning_events").format(
                    sql.Identifier(plan_policy.schema))).fetchone()["n"] == 0
            with child(AUTHORITY, PLANNING_GROUP, [PLANNING_GROUP], caller, home=caller_home) as caller_handle:
                assert select.select([caller_handle[1]], [], [], 15)[0], "planning caller exec deadline"
                assert os.read(caller_handle[1], 128) == b"", "planning caller did not exec"
                assert reap(caller_handle, 15) == 0, "planning caller command failed"
            finished(service_handle, executed=True)
        assert not endpoint.exists()
        with admin.connect() as conn:
            events = conn.execute(sql.SQL("SELECT * FROM {}.planning_events").format(sql.Identifier(plan_policy.schema))).fetchall()
        assert len(events) == 2
        with base.connect() as conn:
            queued = conn.execute(sql.SQL("SELECT * FROM {}.jobs WHERE tenant_id='tenant-a'").format(
                sql.Identifier(job_policy.schema))).fetchall()
            contexts = conn.execute(sql.SQL("SELECT * FROM {}.decision_contexts").format(
                sql.Identifier(job_policy.schema))).fetchall()
        assert len(queued) == len(contexts) == 2
        context_hashes = {row["context_sha256"] for row in contexts}
        assert {json.loads(row["context_raw"])["decision_time_kind"] for row in contexts} == {"actual", "hypothetical"}
        for row in queued:
            value = json.loads(row["input_bytes"])
            assert row["state"] == "queued" and row["stage"] == "collection_review"
            assert sha256(row["input_bytes"]).hexdigest() == row["input_sha256"]
            assert value["context_sha256"] in context_hashes and value["snapshot_id"] == snapshot_id
        print("Planning UID smoke passed: fresh planner/caller exec, separate SCRAM writer/reader/job authority; "
              "private key/credential denials, rogue peer rejection, actual/hypothetical contexts and queued review. "
              "Controller-owned test keys; no actual CLI, independent custody or G1/G4 acceptance.")
