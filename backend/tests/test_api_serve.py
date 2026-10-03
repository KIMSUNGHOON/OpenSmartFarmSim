"""Ephemeral synthetic TLS and service accounts; no public deployment or G1 proof."""

from dataclasses import asdict
from datetime import datetime, timezone, timedelta
import http.client
import ipaddress
import json
import logging
import os
import signal
from pathlib import Path
import socket
import ssl
import subprocess
import sys
import time
import types
from uuid import uuid4

from cryptography import x509
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.x509.oid import NameOID
from fastapi import FastAPI
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from app.api_serve import HttpsApiService, main
from app.https_service import _ServiceFormatter
from app.http_identity import BearerGrant, BearerRegistry, PrincipalMiddleware, token_digest
from test_api_location_research import login_database, login_scope, BODY, rows
from test_research_registry import document


TOKEN = b"synthetic-https-service-"+b"t"*32
ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture
def tls_files(tmp_path):
    directory = tmp_path/"private-tls"
    directory.mkdir(mode=0o700)
    key = ec.generate_private_key(ec.SECP256R1())
    now = datetime.now(timezone.utc)
    name = x509.Name([x509.NameAttribute(NameOID.COMMON_NAME, "Synthetic local API test")])
    certificate = (x509.CertificateBuilder().subject_name(name).issuer_name(name)
        .public_key(key.public_key()).serial_number(x509.random_serial_number())
        .not_valid_before(now-timedelta(minutes=1)).not_valid_after(now+timedelta(minutes=10))
        .add_extension(x509.SubjectAlternativeName([x509.IPAddress(ipaddress.ip_address("127.0.0.1"))]), False)
        .sign(key, hashes.SHA256()))
    cert, private = directory/"cert.pem", directory/"key.pem"
    cert.write_bytes(certificate.public_bytes(serialization.Encoding.PEM))
    private.write_bytes(key.private_bytes(serialization.Encoding.PEM, serialization.PrivateFormat.PKCS8,
                                          serialization.NoEncryption()))
    cert.chmod(0o644)
    private.chmod(0o600)
    return cert, private, key


def protected():
    now = datetime.now(timezone.utc)
    grant = BearerGrant(token_digest(TOKEN), "tenant-a", frozenset({"metadata", "location_create"}),
                        now-timedelta(seconds=1), now+timedelta(minutes=5))
    return PrincipalMiddleware(FastAPI(), BearerRegistry((grant,)))


@pytest.mark.parametrize("changes", [{"host": "0.0.0.0"}, {"host": "localhost"},
    {"port": -1}, {"port": 65536}, {"port": True}, {"app": FastAPI()}])
def test_invalid_service_scope_fails_before_loading_tls(tls_files, changes):
    cert, key, _ = tls_files
    values = dict(app=protected(), certificate=cert, private_key=key)
    values.update(changes)
    with pytest.raises(ValueError, match="^API service configuration rejected$"):
        HttpsApiService(**values)


@pytest.mark.parametrize("fault", ["relative", "missing", "directory", "empty", "oversized",
    "key_symlink", "parent_symlink", "parent_mode", "key_mode", "cert_mode", "invalid", "encrypted", "mismatch", "fifo"])
def test_unsafe_or_invalid_tls_material_fails_with_fixed_error(tls_files, tmp_path, fault):
    cert, key, value = tls_files
    if fault == "relative": key = Path("private-key.pem")
    elif fault == "missing": key = key.with_name("missing.pem")
    elif fault == "directory": key.unlink(); key.mkdir()
    elif fault == "fifo": key.unlink(); os.mkfifo(key, 0o600)
    elif fault == "empty": key.write_bytes(b"")
    elif fault == "oversized": key.write_bytes(b"x"*65537)
    elif fault == "key_symlink":
        target = key.with_name("actual.pem"); key.rename(target); key.symlink_to(target)
    elif fault == "parent_symlink":
        alias = tmp_path/"alias"; alias.symlink_to(key.parent, target_is_directory=True); key = alias/key.name
    elif fault == "parent_mode": key.parent.chmod(0o750)
    elif fault == "key_mode": key.chmod(0o640)
    elif fault == "cert_mode": cert.chmod(0o666)
    elif fault == "invalid": key.write_bytes(b"synthetic private invalid PEM")
    elif fault == "encrypted": key.write_bytes(value.private_bytes(serialization.Encoding.PEM,
        serialization.PrivateFormat.PKCS8, serialization.BestAvailableEncryption(b"synthetic-password")))
    elif fault == "mismatch": key.write_bytes(ec.generate_private_key(ec.SECP256R1()).private_bytes(
        serialization.Encoding.PEM, serialization.PrivateFormat.PKCS8, serialization.NoEncryption()))
    with pytest.raises(ValueError, match="^API TLS configuration rejected$"):
        HttpsApiService(protected(), cert, key)


def test_key_path_replacement_after_open_cannot_replace_loaded_bytes(tls_files, monkeypatch):
    cert, key, _ = tls_files
    original = os.open
    changed = []
    def replace_after_open(path, flags, *args, **kwargs):
        descriptor = original(path, flags, *args, **kwargs)
        if path == key.name and "dir_fd" in kwargs:
            key.unlink(); key.write_bytes(b"synthetic replacement invalid PEM"); key.chmod(0o600)
            changed.append(True)
        return descriptor
    monkeypatch.setattr(os, "open", replace_after_open)
    service = HttpsApiService(protected(), cert, key)
    assert changed and service._tls.minimum_version == ssl.TLSVersion.TLSv1_2
    assert "pem" not in repr(service) and "SSLContext" not in repr(service)


def test_private_diagnostics_are_replaced_by_fixed_event():
    record = logging.LogRecord("uvicorn.error", logging.ERROR, "private.py", 1,
        "private token=%s", (TOKEN,), None)
    assert _ServiceFormatter().format(record) == '{"version":1,"ok":false,"code":"api_transport_event"}'


@pytest.mark.parametrize("args", [[], ["--factory", "bad/value:build"], ["--factory", "missing_module:build"],
                                    ["--factory", "x:build", "--password", "private-value"]])
def test_cli_invalid_configuration_has_fixed_error(args, capsys):
    assert main(args) == 2
    captured = capsys.readouterr()
    assert captured.out == "" and json.loads(captured.err)["code"] == "api_startup_rejected"
    assert "private" not in captured.err


@pytest.mark.parametrize("fault,expected", [("type", 2), ("factory", 2), ("factory_exit", 2), ("serve", 3)])
def test_cli_factory_and_transport_errors_are_private(tls_files, monkeypatch, capsys, fault, expected):
    cert, key, _ = tls_files
    service = HttpsApiService(protected(), cert, key)
    def factory():
        if fault == "factory": raise RuntimeError("synthetic private factory credential")
        if fault == "factory_exit": raise SystemExit("synthetic private factory details")
        return object() if fault == "type" else service
    def fail(_): raise SystemExit("synthetic private bind details")
    monkeypatch.setitem(sys.modules, "synthetic_https_factory", types.SimpleNamespace(build=factory))
    monkeypatch.setattr(HttpsApiService, "serve", fail)
    assert main(["--factory", "synthetic_https_factory:build"]) == expected
    captured = capsys.readouterr()
    assert captured.out == "" and "private" not in captured.err


def test_real_cli_https_region_submission_and_job_read_use_real_postgres(login_scope, tls_files, tmp_path):
    base, policy, dsns = login_scope
    cert, key, _ = tls_files
    with socket.socket() as probe:
        probe.bind(("127.0.0.1", 0)); port = probe.getsockname()[1]
    directory = tmp_path/"operator"
    directory.mkdir(mode=0o700)
    config = {"policy": asdict(policy), "dsn": dsns["authority"], "artifacts": str(base.artifact_root),
        "cert": str(cert), "key": str(key), "port": port, "registry": document(), "token": TOKEN.decode()}
    private = directory/"private.json"
    private.write_text(json.dumps(config)); private.chmod(0o600)
    (directory/"synthetic_factory.py").write_text('''from datetime import datetime,timezone,timedelta
from hashlib import sha256
import json
from pathlib import Path
from app.api import create_app
from app.api_serve import HttpsApiService
from app.cli_contracts import _canonical
from app.http_identity import BearerGrant,BearerRegistry,PrincipalMiddleware,current_principal,token_digest
from app.job_store import JobStore
from app.orchestration import LocationResearchService
from app.research_registry import ResearchRegistry
from app.runtime_roles import RuntimeLoginPolicy
from test_api_job_status import UnusedMarketHoldStore,UnusedThermalRunStore,UnusedMarketResultStore
def build():
    value=json.loads(Path(__file__).with_name("private.json").read_text())
    policy=RuntimeLoginPolicy(**value["policy"])
    store=JobStore(value["dsn"],policy.schema,Path(value["artifacts"]),runtime_identity=(policy,"authority"),principal_provider=current_principal)
    raw=_canonical(value["registry"])
    registry=ResearchRegistry(raw,sha256(raw).hexdigest())
    app=create_app(store,UnusedMarketHoldStore(),UnusedThermalRunStore(),UnusedMarketResultStore(),principal_provider=current_principal,location_research_service=LocationResearchService(store,registry.scope_for_location))
    now=datetime.now(timezone.utc)
    grant=BearerGrant(token_digest(value["token"].encode()),"tenant-a",frozenset({"location_create","metadata"}),now-timedelta(seconds=1),now+timedelta(minutes=5))
    return HttpsApiService(PrincipalMiddleware(app,BearerRegistry((grant,))),value["cert"],value["key"],port=value["port"])
''')
    environment = {"PATH": os.defpath, "LANG": "C.UTF-8",
        "PYTHONPATH": os.pathsep.join(map(str, (ROOT, ROOT/"tests", directory)))}
    process = subprocess.Popen([sys.executable, "-m", "app.api_serve", "--factory", "synthetic_factory:build"],
        cwd=ROOT, env=environment, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    context = ssl.create_default_context(cafile=str(cert))
    def call(method="GET", path="/openapi.json", body=None, authenticated=False):
        conn = http.client.HTTPSConnection("127.0.0.1", port, timeout=1, context=context)
        try:
            headers = {"X-Forwarded-Proto": "http", "X-Forwarded-For": "198.51.100.7"}
            if authenticated: headers["Authorization"] = "Bearer "+TOKEN.decode()
            if body is not None: headers["Content-Type"] = "application/json"
            conn.request(method, path, body=json.dumps(body) if body is not None else None, headers=headers)
            response = conn.getresponse()
            return response.status, json.loads(response.read()), dict(response.getheaders())
        finally: conn.close()
    try:
        deadline = time.monotonic()+10
        while True:
            assert process.poll() is None, "synthetic HTTPS service exited early"
            try: first = call(); break
            except OSError:
                assert time.monotonic() < deadline, "synthetic HTTPS service did not become ready"
                time.sleep(0.05)
        assert first[0] == 401 and first[2]["strict-transport-security"] and "server" not in first[2]
        published_contract = call(authenticated=True)
        assert published_contract[0] == 200
        assert published_contract[1] == json.loads((ROOT.parent/"contracts"/"openapi-v1.json").read_bytes())
        accepted = call("POST", "/v1/locations", BODY, True)
        assert accepted[0] == 202
        job = accepted[1]["research_job"]["job_id"]
        assert call(path="/v1/jobs/"+job, authenticated=True)[1] == accepted[1]["research_job"]
        assert call("POST", "/v1/locations", BODY, True)[1] == accepted[1]
        assert call(path="/v1/jobs/"+str(uuid4()), authenticated=True)[0] == 404
        assert len(rows(base)) == 1
        untrusted = http.client.HTTPSConnection("127.0.0.1", port, timeout=1)
        try:
            with pytest.raises(ssl.SSLCertVerificationError): untrusted.request("GET", "/openapi.json")
        finally: untrusted.close()
        plain = http.client.HTTPConnection("127.0.0.1", port, timeout=1)
        try:
            with pytest.raises((OSError, http.client.HTTPException)):
                plain.request("GET", "/openapi.json", headers={"X-Forwarded-Proto": "https"}); plain.getresponse()
        finally: plain.close()
    finally:
        process.terminate()
        try: stdout, stderr = process.communicate(timeout=5)
        except subprocess.TimeoutExpired: process.kill(); stdout, stderr = process.communicate(timeout=5)
    assert process.returncode == -signal.SIGTERM and stdout == b"" and TOKEN not in stderr and b"private.json" not in stderr
