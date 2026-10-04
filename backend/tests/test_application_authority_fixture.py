"""Actual SCRAM proof of the private Compose registry-hold factory policy."""

from dataclasses import asdict
from contextlib import redirect_stdout
from hashlib import sha256
import io
import json
import multiprocessing
import os
from pathlib import Path
import runpy
import sys
import tempfile
import time
from types import ModuleType, SimpleNamespace

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from app.cli_worker import CliWorker
from app.cli_supervisor_client import SupervisorClient
from app.cli_supervisor_service import SupervisorServer
from app.execution_attestation import ExecutionAttestationStore
from app.orchestration import LocationRequest, LocationResearchService
from login_database import login_database, login_scope
from test_cli_worker import _fake_cli

ROOT = Path(__file__).resolve().parents[2]


def test_private_authority_policy_retains_actual_invocation_and_registry_hold(login_scope, tmp_path, monkeypatch):
    _, policy, dsns = login_scope
    fixture = runpy.run_path(str(ROOT / 'scripts/application-authority-fixture.py'))
    principal = {'authenticated': True, 'tenant_id': 'tenant-1', 'scopes': set()}

    def private(path, value):
        path.write_bytes(value if type(value) is bytes else value.encode())
        path.chmod(0o600)

    body = fixture['prepare'](tmp_path, login_scope, principal, private=private,
                              command=lambda *args: None)
    root = tmp_path / 'authority'
    private(root / 'authority.dsn', dsns['authority'])
    value = json.loads((root / 'fixture.json').read_bytes())
    # Local software regression substitutes only container filesystem/UID access.
    # Real separate UID/mount/signature acceptance remains the hosted Compose test.
    source = fixture['PLUGIN'].replace("Path('/artifacts')", f'Path({str(tmp_path / "artifacts")!r})')
    source = source.replace('content_access=ContentAccess(owner_uid=11001,reader_gid=11010)',
                            'content_access=None')
    namespace = {}
    exec(compile(source, 'private-authority-fixture', 'exec'), namespace)
    jobs, contract, observed = namespace['store'](value, root, 'authority')
    assert asdict(observed) == asdict(policy)
    jobs.principal_provider = lambda: principal
    principal['scopes'].update({'metadata', 'artifact', 'auditor'})
    registry = contract.authority_resolver
    service = LocationResearchService(jobs, registry.__self__.scope_for_location)
    _, _, job = service.submit('tenant-1', LocationRequest.model_validate(body))
    home = tmp_path / 'local-cli-home'
    home.mkdir(mode=0o700)
    binary = _fake_cli(tmp_path, mode='valid_slow')
    digest = sha256(binary.read_bytes()).hexdigest()
    supervisor_root = tmp_path / 'supervisor'
    private(supervisor_root / 'supervisor.dsn', dsns['supervisor'])
    supervisor_jobs, _, _ = namespace['store'](value, supervisor_root, 'supervisor')
    with tempfile.TemporaryDirectory(prefix='ossf-authority-fixture-rpc-') as directory:
        socket = Path(directory) / 'supervisor.sock'
        server = SupervisorServer(supervisor_jobs, socket_path=socket, worker_uid=os.getuid(),
            tenant_id='tenant-1', key_file=supervisor_root / 'private.key', key_id=value['key_id'],
            cli_path=binary, codex_home=home, executable_sha256=digest,
            environment_sha256=value['environment_sha256'],
            child_env={'CODEX_API_KEY': 'synthetic-test-key'}, timeout_seconds=10)
        process = multiprocessing.get_context('fork').Process(target=server.serve,
                                                               kwargs={'max_sessions': 1})
        process.start()
        try:
            deadline = time.monotonic() + 10
            while not socket.exists():
                assert process.is_alive() and time.monotonic() < deadline
                time.sleep(0.02)
            client = SupervisorClient(socket, supervisor_uid=os.getuid(), tenant_id='tenant-1',
                executable_sha256=digest, environment_sha256=value['environment_sha256'])
            attestations = ExecutionAttestationStore(jobs, {value['key_id']: bytes.fromhex(value['public_key'])})
            worker = CliWorker(jobs, contract, supervisor_client=client, attestation_store=attestations,
                               timeout_seconds=10, lease_seconds=30, synthetic_smoke=True)
            result = worker.run_once()
        finally:
            process.join(timeout=5)
            if process.is_alive():
                process.terminate()
                process.join(timeout=5)
            assert not process.is_alive() and not socket.exists()
    assert result.job_id == job['job_id']
    assert result.state == 'hold' and result.reason_code == 'validated_hold'
    assert result.capture_id is not None and result.decision_id is not None
    assert jobs.get_job('tenant-1', job['job_id'])['reason'] == {'code': 'ai_validated_hold'}
    assert json.loads(jobs.read_hold_report('tenant-1', job['job_id'])) == {
        'schema_version': 'hold_v1', 'reason_code': 'evidence_missing',
        'missing_evidence': ['research_source_evidence', 'signed_decision_context']}
    module = ModuleType('synthetic_authority')
    module.__dict__.update(namespace)
    module.data = lambda: (value, root)
    monkeypatch.setitem(sys.modules, 'synthetic_authority', module)

    def execute_inspection(*args):
        source = args[args.index('-c') + 1]
        monkeypatch.setattr(sys, 'argv', ['inspection', args[-1]])
        output = io.StringIO()
        with redirect_stdout(output):
            exec(compile(source, 'actual-private-inspection', 'exec'), {})
        return SimpleNamespace(stdout=output.getvalue())

    assert fixture['assert_persisted'](str(job['job_id']), command=execute_inspection, compose=('local',)) == {
        'decisions': 1, 'captures': 1, 'signed_executions': 1, 'scope': 'software_fixture_only'}
