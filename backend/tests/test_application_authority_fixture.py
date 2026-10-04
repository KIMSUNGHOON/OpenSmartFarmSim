"""Actual SCRAM proof of the private Compose registry-hold factory policy."""

from dataclasses import asdict
import json
from pathlib import Path
import runpy
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from app.cli_worker import CliWorker
from app.orchestration import LocationRequest, LocationResearchService
from login_database import login_database, login_scope
from test_cli_worker import _fake_cli

ROOT = Path(__file__).resolve().parents[2]


def test_private_authority_policy_retains_actual_invocation_and_registry_hold(login_scope, tmp_path):
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
    worker = CliWorker(jobs, contract, cli_path=_fake_cli(tmp_path), codex_home=home,
                       child_env={'CODEX_API_KEY': 'synthetic-test-key'},
                       timeout_seconds=10, lease_seconds=30, synthetic_smoke=True)
    result = worker.run_once()
    assert result.job_id == job['job_id']
    assert result.state == 'hold' and result.reason_code == 'validated_hold'
    assert result.capture_id is not None and result.decision_id is not None
    assert jobs.get_job('tenant-1', job['job_id'])['reason'] == {'code': 'ai_validated_hold'}
    assert json.loads(jobs.read_hold_report('tenant-1', job['job_id'])) == {
        'schema_version': 'hold_v1', 'reason_code': 'evidence_missing',
        'missing_evidence': ['research_source_evidence', 'signed_decision_context']}
