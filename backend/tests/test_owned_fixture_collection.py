"""Owned original bytes and real SCRAM; the research executable and keys are synthetic."""

from dataclasses import replace
from hashlib import sha256
import json
from pathlib import Path
import sys
from uuid import UUID

import pytest
from psycopg import sql

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from app.cli_contracts import DecisionContract
from app.cli_worker import CliWorker
from app.job_store import JobStore
from app.owned_fixture_collection import CollectionService, CollectionWorker
from app.owned_fixture_registry import OwnedFixtureRegistry
from test_cli_contracts import input_for, resolver
from test_cli_worker import _fake_cli
from test_job_evidence import cli_store
from login_database import login_database, login_scope

ROOT = Path(__file__).resolve().parents[2]


@pytest.fixture
def collection_setup(login_scope, tmp_path):
    base, policy, dsns = login_scope
    registry = OwnedFixtureRegistry(ROOT)
    def approved(job, value):
        return replace(resolver(job, value), allow_proceed=True, missing_evidence=(),
            candidate_ids=frozenset({registry.provider_id}))
    contract = DecisionContract(approved)
    principal = {'authenticated': True, 'tenant_id': 'tenant-a',
        'scopes': {'metadata', 'artifact', 'auditor', 'collection_execute', 'cancel'}}
    jobs = JobStore(dsns['authority'], policy.schema, base.artifact_root,
        decision_validator=contract, evidence_policy=cli_store(base).evidence_policy,
        principal_provider=lambda: principal, audit_runtime_grants=True,
        runtime_identity=(policy, 'authority'))
    program = _fake_cli(tmp_path)
    program.write_text(program.read_text().replace('candidate-a', registry.provider_id))
    home = tmp_path/'synthetic-cli-home'
    home.mkdir(mode=0o700)
    research = CliWorker(jobs, contract, cli_path=program, codex_home=home,
        child_env={'CODEX_API_KEY': 'synthetic-test-key'}, timeout_seconds=10,
        lease_seconds=30, synthetic_smoke=True)
    value = input_for('research')
    value.update(candidate_ids=[registry.provider_id], provider_ids=[registry.provider_id],
        period_start_utc='2026-10-15T08:00:00Z', period_end_utc='2026-10-15T10:00:00Z',
        decision_context_id='decision-context-v1:'+'c'*64, decision_at_utc='2026-09-28T00:00:00Z',
        claim_mode='ex_ante', decision_time_kind='hypothetical')
    parent = jobs.submit('tenant-a', 'research', value, 'research-for-collection')
    outcome = research.run_once()
    assert outcome.state == 'succeeded' and outcome.decision_id
    service = CollectionService(jobs, registry)
    return service, CollectionWorker(service, tenant_id='tenant-a'), parent, principal


def test_admission_collection_record_and_atomic_completion(collection_setup):
    service, worker, parent, _ = collection_setup
    job = service.submit('tenant-a', str(parent['job_id']), 'collect-one')
    assert job['state'] == 'queued'
    assert service.submit('tenant-a', str(parent['job_id']), 'collect-one')['job_id'] == job['job_id']
    result = worker.run_once(str(job['job_id']))
    assert result.state == 'succeeded'
    raw = service.jobs.read_artifact('tenant-a', job['job_id'])
    record = json.loads(raw)
    assert record['record_version'] == 'owned-fixture-collection-record-v1'
    assert record['assessment_status'] == 'hold' and record['g0_status'] == 'not_accepted'
    assert record['g1_status'] == 'not_accepted' and record['claim_scope'] == 'software_fixture_only'
    assert record['research_job_id'] == str(parent['job_id'])
    assert len(record['sources']) == 3
    for source in record['sources']:
        original = (ROOT/source['metadata']['source_locator']).read_bytes()
        assert source['raw_utf8'].encode() == original
        assert source['metadata']['sha256'] == sha256(original).hexdigest()
    publication = service.jobs.get_publication('tenant-a', job['job_id'])
    assert publication['decision_id'] is None and publication['artifact_sha256'] == sha256(raw).hexdigest()
    assert len(service.jobs.list_attempt_outcomes('tenant-a', job['job_id'])) == 1
    assert worker.run_once(str(job['job_id'])) is None


def test_parent_or_source_binding_failure_creates_no_intent(collection_setup, monkeypatch):
    service, _, parent, principal = collection_setup
    principal['scopes'].remove('collection_execute')
    with pytest.raises(PermissionError): service.submit('tenant-a', str(parent['job_id']), 'denied')
    principal['scopes'].add('collection_execute')
    with pytest.raises((ValueError, PermissionError)): service.submit('tenant-b', str(parent['job_id']), 'foreign')
    other = service.jobs.submit('tenant-a', 'research', input_for('research'), 'unfinished-parent')
    with pytest.raises(ValueError): service.submit('tenant-a', str(other['job_id']), 'unfinished')
    original = service.registry.read_bundle
    monkeypatch.setattr(service.registry, 'read_bundle', lambda *_: (_ for _ in ()).throw(ValueError('private source')))
    with pytest.raises(ValueError): service.submit('tenant-a', str(parent['job_id']), 'source-failed')
    monkeypatch.setattr(service.registry, 'read_bundle', original)


@pytest.mark.parametrize('fault', ['scope', 'publication'])
def test_publication_failure_rolls_back_completion(collection_setup, monkeypatch, fault):
    service, worker, parent, principal = collection_setup
    job = service.submit('tenant-a', str(parent['job_id']), 'rollback')
    original = service.jobs._insert_publication
    def fail(*args, **kwargs):
        original(*args, **kwargs)
        if fault == 'scope': principal['scopes'].remove('collection_execute')
        else: raise RuntimeError('private publication detail')
    monkeypatch.setattr(service.jobs, '_insert_publication', fail)
    result = worker.run_once(str(job['job_id']))
    assert result.state in ('hold', 'queued') and 'private' not in result.reason_code
    assert service.jobs.get_publication('tenant-a', job['job_id']) is None


def test_cancellation_and_expired_attempt_do_not_publish(collection_setup, monkeypatch):
    service, worker, parent, _ = collection_setup
    job = service.submit('tenant-a', str(parent['job_id']), 'expire')
    original = service.jobs.read_input
    once = []
    def expire(*args):
        raw = original(*args)
        if not once:
            once.append(True)
            with service.jobs.connect() as conn:
                conn.execute(sql.SQL("UPDATE {} SET lease_until=clock_timestamp()-interval '1 second' WHERE job_id=%s")
                    .format(service.jobs._table('jobs')), (job['job_id'],))
        return raw
    monkeypatch.setattr(service.jobs, 'read_input', expire)
    assert worker.run_once(str(job['job_id'])).state == 'unclosed'
    assert service.jobs.get_publication('tenant-a', job['job_id']) is None
    outcome = worker.run_once(str(job['job_id']))
    assert outcome.state == 'succeeded' and outcome.attempt == 2
    canceled = service.submit('tenant-a', str(parent['job_id']), 'cancel')
    assert service.jobs.cancel('tenant-a', canceled['job_id'])
    assert worker.run_once(str(canceled['job_id'])) is None


def test_registry_rejects_changed_original_bytes(tmp_path):
    from shutil import copytree
    copytree(ROOT/'fixtures', tmp_path/'fixtures')
    registry = OwnedFixtureRegistry(tmp_path)
    path = tmp_path/'fixtures'/'synthetic-weather-v1.json'
    path.write_bytes(path.read_bytes()+b' ')
    with pytest.raises(ValueError): registry.read_bundle('2026-09-28T00:00:00Z', 'ex_ante')


def test_forged_intent_is_held_without_record(collection_setup):
    service, worker, parent, _ = collection_setup
    value, _ = service._prepare('tenant-a', str(parent['job_id']))
    data = value.model_dump(mode='json') | {'research_artifact_sha256': 'a'*64}
    job = service.jobs.submit('tenant-a', 'collection', data, 'forged-input')
    outcome = worker.run_once(str(job['job_id']))
    assert outcome.state == 'hold' and outcome.record_sha256 is None
    assert service.jobs.get_publication('tenant-a', job['job_id']) is None


def test_changed_provider_and_binding_roll_back_admission(collection_setup, monkeypatch):
    service, _, parent, _ = collection_setup
    original = service._prepare
    def changed(*args):
        value = original(*args)
        service.registry.provider_id = 'private-rebound-provider'
        return value
    monkeypatch.setattr(service, '_prepare', changed)
    with pytest.raises(RuntimeError): service.submit('tenant-a', str(parent['job_id']), 'rebound')
    with service.jobs.connect() as conn:
        count = conn.execute(sql.SQL("SELECT count(*) AS n FROM {} WHERE stage='collection'")
            .format(service.jobs._table('jobs'))).fetchone()['n']
    assert count == 0


def test_source_available_after_decision_is_rejected():
    with pytest.raises(ValueError):
        OwnedFixtureRegistry(ROOT).read_bundle('2026-01-01T00:00:00Z', 'ex_ante')


def test_actual_foreground_process_collects_original_bytes(collection_setup, tmp_path):
    from dataclasses import asdict
    import os
    import subprocess
    service, _, parent, principal = collection_setup
    job = service.submit('tenant-a', str(parent['job_id']), 'foreground')
    document = {'dsn': service.jobs._dsn, 'policy': asdict(service.jobs.runtime_identity[0]),
        'artifacts': str(service.jobs.artifact_root), 'root': str(ROOT),
        'principal': principal | {'scopes': sorted(principal['scopes'])}}
    config = tmp_path/'collection_operator.json'
    config.write_text(json.dumps(document))
    config.chmod(0o600)
    factory = tmp_path/'collection_operator.py'
    factory.write_text('''import json
from pathlib import Path
from app.runtime_roles import RuntimeLoginPolicy
from app.job_store import JobStore
from app.owned_fixture_registry import OwnedFixtureRegistry
from app.owned_fixture_collection import CollectionService, CollectionWorker
def build():
    data=json.loads(Path(__file__).with_name('collection_operator.json').read_text())
    policy=RuntimeLoginPolicy(**data['policy'])
    jobs=JobStore(data['dsn'],policy.schema,Path(data['artifacts']),audit_runtime_grants=True,
        runtime_identity=(policy,'authority'),principal_provider=lambda:data['principal'])
    return CollectionWorker(CollectionService(jobs,OwnedFixtureRegistry(data['root'])),
        tenant_id=data['principal']['tenant_id'])
''')
    factory.chmod(0o600)
    env = os.environ | {'PYTHONPATH': os.pathsep.join([str(tmp_path), str(Path(__file__).parents[1])])}
    result = subprocess.run([sys.executable, '-m', 'app.collection_work', '--factory',
        'collection_operator:build', '--job-id', str(job['job_id'])], env=env,
        capture_output=True, text=True, timeout=120)
    assert result.returncode == 0, result.stderr
    outcome = json.loads(result.stdout)['result']
    assert outcome['state'] == 'succeeded' and outcome['record_sha256']
    assert 'raw_utf8' not in result.stdout and document['dsn'] not in result.stdout
    record = json.loads(service.jobs.read_artifact('tenant-a', job['job_id']))
    assert record['g0_status'] == 'not_accepted' and len(record['sources']) == 3


def test_retained_parent_proof_corruption_holds_admitted_job(collection_setup):
    service, worker, parent, _ = collection_setup
    job = service.submit('tenant-a', str(parent['job_id']), 'parent-proof-drift')
    decision = service.jobs.list_decisions('tenant-a', parent['job_id'])[0]
    import os
    directory = service.jobs._content_directory('tenant-a')
    try:
        fd = os.open(decision['output_sha256'], os.O_WRONLY | os.O_NOFOLLOW, dir_fd=directory)
        with os.fdopen(fd, 'wb') as stream:
            stream.write(b'corrupted private parent output')
    finally:
        os.close(directory)
    outcome = worker.run_once(str(job['job_id']))
    assert outcome.state == 'hold' and outcome.record_sha256 is None
    assert service.jobs.get_publication('tenant-a', job['job_id']) is None


@pytest.mark.parametrize('arguments', [[], ['--factory', 'private_invalid', '--job-id', 'bad'],
    ['--factory', 'private_module:build', '--job-id', 'private-invalid-id']])
def test_foreground_configuration_failure_is_fixed_before_import(monkeypatch, capsys, arguments):
    from app import collection_work
    def forbidden(*_):
        raise AssertionError('factory must not import for invalid arguments')
    monkeypatch.setattr(collection_work.importlib, 'import_module', forbidden)
    assert collection_work.main(arguments) == 2
    captured = capsys.readouterr()
    assert captured.out == ''
    assert json.loads(captured.err) == {'version': 1, 'ok': False, 'code': 'collection_startup_rejected'}
