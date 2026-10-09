"""Completed owned bytes to review; fake executable/context keys are not G1."""

from hashlib import sha256
import hmac
import json
from pathlib import Path
import sys

import pytest
from psycopg import sql

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from app.owned_collection_review import OwnedCollectionReviewService, OwnedCollectionReviewContract
from app.thermal_run_store import ThermalRunStore, snapshot_id_for
from app.thermal_publisher import collection_review_proposal
from app.cli_worker import CliWorker
from app.cli_contracts import AuthoritySnapshot, ProposalHold
from test_owned_fixture_collection import collection_setup, login_scope, login_database, ROOT
from test_thermal_run_store import signed_context, canonical, CONTEXT_KEY, verify_test_context
from test_cli_worker import _fake_cli


@pytest.fixture
def review_setup(collection_setup):
    collection, worker, parent, principal = collection_setup
    principal['scopes'].update({'collection_read', 'collection_review_create',
        'thermal_snapshot_write', 'thermal_snapshot_read', 'decision_context_read', 'decision_context_write'})
    job = collection.submit('tenant-a', str(parent['job_id']), 'review-source')
    assert worker.run_once(str(job['job_id'])).state == 'succeeded'
    runs = ThermalRunStore(collection.jobs._dsn, collection.jobs.schema,
        gate_key=b'synthetic-collection-review-gate-key', release_verifier=lambda *_: None,
        principal_provider=collection.jobs.principal_provider,
        runtime_identity=collection.jobs.runtime_identity, context_verifier=verify_test_context)
    raws = tuple((ROOT/'fixtures'/name).read_bytes() for name in
        ('manifest-v2.json', 'synthetic-weather-v1.json', 'synthetic-thermal-parameters-v1.json'))
    snapshot = snapshot_id_for(*raws)
    data, _, _ = signed_context('tenant-a', snapshot, context_id='decision-context-v1:'+'c'*64)
    data['decision_at_utc'] = '2026-09-28T00:00:00Z'
    raw = canonical(data)
    signature = hmac.new(CONTEXT_KEY, b'decision-context-v1\0'+raw, sha256).hexdigest()
    runs.put_decision_context('tenant-a', raw, signature)
    service = OwnedCollectionReviewService(collection, runs)
    return service, job, principal, snapshot, raws


def count_snapshots(service):
    with service.collection.jobs.connect() as conn:
        return conn.execute(sql.SQL('SELECT count(*) AS n FROM {}')
            .format(service.runs._table('thermal_input_snapshots'))).fetchone()['n']


def test_collected_snapshot_and_review_intent_are_atomic(review_setup):
    service, collected, _, snapshot_id, raws = review_setup
    job = service.submit('tenant-a', str(collected['job_id']), 'review-one')
    assert job['stage'] == 'collection_review' and job['state'] == 'queued'
    assert service.submit('tenant-a', str(collected['job_id']), 'review-one')['job_id'] == job['job_id']
    snapshot = service.runs.get_snapshot('tenant-a', snapshot_id)
    assert tuple(snapshot[k] for k in ('manifest_raw', 'weather_raw', 'thermal_raw')) == raws
    with service.collection.jobs.connect() as conn:
        stored = service.collection.jobs._locked_job(conn, 'tenant-a', job['job_id'])
        raw = service.collection.jobs._verified_input(stored)
    assert snapshot['recorded_at'] <= stored['created_at']
    value = json.loads(raw)
    assert value['collection_job_id'] == str(collected['job_id']) and value['collection_record_sha256']
    assert 'raw_utf8' not in raw.decode() and count_snapshots(service) == 1


@pytest.mark.parametrize('allow', [True, False])
def test_actual_fake_cli_review_retains_collection_binding(review_setup, tmp_path, allow):
    service, collected, _, snapshot_id, _ = review_setup
    def authority(job, value):
        return AuthoritySnapshot(job['tenant_id'], 'collection_review', job['input_sha256'],
            frozenset({snapshot_id}), {}, allow, () if allow else ('independent_owned_review',), {}, frozenset(), False,
            {key:value[key] for key in OwnedCollectionReviewContract.BINDING_FIELDS},
            value['decision_context_id'], value['decision_at_utc'], value['claim_mode'], value['decision_time_kind'])
    contract = OwnedCollectionReviewContract(service, authority)
    service.collection.jobs.decision_validator = contract
    job = service.submit('tenant-a', str(collected['job_id']), 'cli-review')
    program = _fake_cli(tmp_path)
    program.write_text(program.read_text().replace('candidate-a', snapshot_id))
    home = tmp_path/'owned-review-home';home.mkdir(mode=0o700)
    worker = CliWorker(service.collection.jobs, contract, cli_path=program, codex_home=home,
        child_env={'CODEX_API_KEY':'synthetic-test-key'}, timeout_seconds=10, lease_seconds=300,
        synthetic_smoke=True)
    result = worker.run_once()
    assert result.state == ('succeeded' if allow else 'hold') and result.decision_id
    record = service.collection.read_record('tenant-a', str(collected['job_id']))
    assert record['g0_status'] == 'not_accepted' and record['assessment_status'] == 'hold'
    if not allow:
        hold = json.loads(service.collection.jobs.read_hold_report('tenant-a', job['job_id']))
        assert hold['missing_evidence'] == ['independent_owned_review']
        assert service.collection.jobs.get_publication('tenant-a', job['job_id']) is None
        return
    proposal = json.loads(service.collection.jobs.read_artifact('tenant-a', job['job_id']))
    context = service.runs.get_decision_context('tenant-a', snapshot_id, record['decision_context_id'])
    assert proposal == collection_review_proposal(service.runs.get_snapshot('tenant-a', snapshot_id), context)
    from app.thermal_publisher import ThermalG1Publisher, ThermalPublishHold
    publisher = ThermalG1Publisher(service.runs, service.collection.jobs, lambda *_:None,
        root=ROOT, gate_key=b'synthetic-collection-review-gate-key')
    with pytest.raises(ThermalPublishHold, match='collection review service unavailable'):
        publisher.prepare('tenant-a', job['job_id'], snapshot_id)
    publisher.collection_review_service = service
    with pytest.raises(ThermalPublishHold, match='no independently observed CLI worker execution'):
        publisher.prepare('tenant-a', job['job_id'], snapshot_id)


@pytest.mark.parametrize('fault', ['missing', 'time', 'scope'])
def test_context_and_access_failure_admit_no_snapshot(review_setup, monkeypatch, fault):
    service, collected, principal, _, _ = review_setup
    original = service.runs.get_decision_context
    def changed(*args):
        result = original(*args)
        if fault == 'missing': return None
        if fault == 'time': return result | {'decision_at_utc':'2026-09-28T01:00:00Z'}
        principal['scopes'].remove('collection_read')
        return result
    monkeypatch.setattr(service.runs, 'get_decision_context', changed)
    with pytest.raises((ValueError, PermissionError)):
        service.submit('tenant-a', str(collected['job_id']), 'bad-context')
    assert count_snapshots(service) == 0


@pytest.mark.parametrize('fault', ['insert', 'scope'])
def test_post_snapshot_fault_rolls_back_snapshot_and_intent(review_setup, monkeypatch, fault):
    service, collected, principal, _, _ = review_setup
    original = service.runs._pin_snapshot_in_transaction
    def fail(*args):
        result = original(*args)
        if fault == 'insert': raise RuntimeError('private snapshot detail')
        principal['scopes'].remove('collection_review_create')
        return result
    monkeypatch.setattr(service.runs, '_pin_snapshot_in_transaction', fail)
    with pytest.raises((ValueError, PermissionError)) as failure:
        service.submit('tenant-a', str(collected['job_id']), 'rollback-snapshot')
    assert 'private' not in str(failure.value) and count_snapshots(service) == 0
    with service.collection.jobs.connect() as conn:
        count = conn.execute(sql.SQL("SELECT count(*) AS n FROM {} WHERE stage='collection_review'")
            .format(service.collection.jobs._table('jobs'))).fetchone()['n']
    assert count == 0


def test_collected_artifact_corruption_blocks_admission(review_setup):
    import os
    service, collected, _, _, _ = review_setup
    publication = service.collection.jobs.get_publication('tenant-a', collected['job_id'])
    directory = service.collection.jobs._content_directory()
    try:
        fd = os.open(publication['artifact_sha256'], os.O_WRONLY | os.O_NOFOLLOW, dir_fd=directory)
        with os.fdopen(fd, 'wb') as stream: stream.write(b'corrupt collected record')
    finally: os.close(directory)
    with pytest.raises(ValueError): service.submit('tenant-a', str(collected['job_id']), 'corrupt-record')
    assert count_snapshots(service) == 0


def test_forged_review_binding_is_rejected_by_server_contract(review_setup):
    service, collected, _, _, _ = review_setup
    job = service.submit('tenant-a', str(collected['job_id']), 'forged-binding')
    with service.collection.jobs.connect() as conn:
        original = service.collection.jobs._locked_job(conn, 'tenant-a', job['job_id'])
    with pytest.raises(ValueError):
        service.verify_input(original | {'input_sha256':'a'*64}, json.loads(original['input_bytes']))
    value = json.loads(original['input_bytes']) | {'collection_record_sha256':'a'*64}
    raw = canonical(value)
    forged = original | {'input_bytes':raw, 'input_sha256':sha256(raw).hexdigest()}
    contract = OwnedCollectionReviewContract(service, lambda *_: None)
    with pytest.raises(ProposalHold): contract.input_context(forged)
