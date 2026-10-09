"""Existing source selection with actual SCRAM; CLI and signed context are fixtures."""

from hashlib import sha256
import os
from pathlib import Path
import sys
from uuid import uuid4

import pytest
from psycopg import sql
from pydantic import ValidationError

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from app.cli_contracts import DecisionContract, _canonical
from app.cli_worker import CliWorker
from app.owned_collection_review import OwnedCollectionReviewService
from app.owned_fixture_collection import CollectionService, CollectionWorker
from app.owned_research import OwnedResearchService
from app.research_registry import ResearchRegistry, _scope_key
from app.source_farm_selection import READ_SCOPES, SourceFarmSelection, SourceFarmSelectionHold, SourceFarmSelectionService
from test_cli_worker import _fake_cli
from test_owned_collection_review import review_setup
from test_owned_fixture_collection import collection_setup, login_scope, login_database
from test_owned_research import research_setup


@pytest.fixture
def source_setup(research_setup, tmp_path):
    old, body, principal, bindings = research_setup
    body = body.model_copy(update={'goal_id': 'historical-thermal-replay'})
    raw = _canonical({'registry_version': 'research-registry-v1', 'registrations': [{
        'tenant_id': 'tenant-a', 'point': {'latitude': body.latitude, 'longitude': body.longitude},
        'period_start_utc': body.period_start_utc, 'period_end_utc': body.period_end_utc,
        'goal_id': body.goal_id, 'provider_ids': [old.registry.provider_id]}]})
    catalog = ResearchRegistry(raw, sha256(raw).hexdigest())
    research = OwnedResearchService(old.store, old.runs, catalog, old.registry, {
        _scope_key('tenant-a', (body.latitude, body.longitude), body.period_start_utc,
            body.period_end_utc, body.goal_id): next(iter(bindings.values()))})
    root = research.submit('tenant-a', body)[2]
    contract = DecisionContract(research.authority_snapshot)
    research.store.decision_validator = contract
    program = _fake_cli(tmp_path)
    program.write_text(program.read_text().replace('candidate-a', research.registry.provider_id))
    home = tmp_path / 'source-farm-cli-home'
    home.mkdir(mode=0o700)
    worker = CliWorker(research.store, contract, cli_path=program, codex_home=home,
        child_env={'CODEX_API_KEY': 'synthetic-test-key'}, timeout_seconds=10,
        lease_seconds=300, synthetic_smoke=True)
    assert worker.run_once().state == 'succeeded'
    collection = CollectionService(research.store, research.registry)
    child = collection.submit('tenant-a', str(root['job_id']), 'source-farm-collection')
    assert CollectionWorker(collection, tenant_id='tenant-a').run_once(str(child['job_id'])).state == 'succeeded'
    return SourceFarmSelectionService(research, collection), root, child, principal, body, worker


def pin_existing_snapshot(service):
    manifest, sources = service.collection.registry._read()
    originals = {item['metadata']['fixture_id']: item['raw_utf8'].encode('utf-8') for item in sources}
    return service.research.runs.put_snapshot('tenant-a', manifest,
        originals['synthetic-weather-v1'], originals['synthetic-thermal-parameters-v1'])


def storage_counts(service):
    jobs, runs = service.research.store, service.research.runs
    with jobs.connect() as conn:
        return tuple(conn.execute(sql.SQL('SELECT count(*) AS n FROM {}').format(table)).fetchone()['n']
            for table in (jobs._table('jobs'), runs._table('thermal_input_snapshots'), runs._table('decision_contexts')))


def test_selection_uses_existing_snapshot_without_writes_and_retains_hold(source_setup):
    service, root, child, principal, _, _ = source_setup
    read = lambda: service.get('tenant-a', root['job_id'], child['job_id'])
    before = storage_counts(service)
    with pytest.raises(SourceFarmSelectionHold, match='^source farm references unavailable$'):
        read()
    assert storage_counts(service) == before
    review = OwnedCollectionReviewService(service.collection, service.research.runs)
    review.submit('tenant-a', str(child['job_id']), 'explicit-source-farm-review')
    principal['scopes'] = set(READ_SCOPES)
    before = storage_counts(service)
    selected = read()
    assert selected == read() and storage_counts(service) == before
    value = selected.model_dump(mode='json')
    assert value['research_job_id'] == str(root['job_id'])
    assert value['collection_job_id'] == str(child['job_id'])
    assert value['collection_input_sha256'] == child['input_sha256']
    assert value['research_input_sha256'] == root['input_sha256']
    assert value['point'] == {'latitude': 37.5, 'longitude': 127.0}
    assert value['goal_id'] == 'historical-thermal-replay'
    assert value['requires_registration_recheck'] is True and value['assessment_status'] == 'hold'
    assert value['g0_status'] == value['g1_status'] == 'not_accepted'
    assert value['claim_scope'] == 'software_fixture_only'
    snapshot = service.research.runs.get_snapshot('tenant-a', value['snapshot_id'])
    assert all(value[key] == snapshot[key] for key in ('manifest_sha256', 'weather_sha256', 'thermal_sha256'))
    raw = _canonical(value)
    for hidden in (b'raw_utf8', b'signature', b'CODEX_API_KEY', b'heater', b'crop', b'tariff'):
        assert hidden not in raw
    for scope in READ_SCOPES:
        principal['scopes'].remove(scope)
        with pytest.raises(PermissionError): read()
        principal['scopes'].add(scope)
    for update in ({'requires_registration_recheck': False}, {'g1_status': 'accepted'}, {'extra': 'private'}):
        with pytest.raises(ValidationError): SourceFarmSelection.model_validate(value | update)


def test_selection_rejects_mixed_unfinished_and_foreign_parents(source_setup):
    service, root, child, principal, body, worker = source_setup
    pin_existing_snapshot(service)
    read = lambda research_id, collection_id: service.get('tenant-a', research_id, collection_id)
    assert read(uuid4(), child['job_id']) is None
    assert read(root['job_id'], uuid4()) is None
    assert read(child['job_id'], root['job_id']) is None
    with pytest.raises(ValueError): read(str(root['job_id']), child['job_id'])
    principal['tenant_id'] = 'other-tenant'
    assert service.get('other-tenant', root['job_id'], child['job_id']) is None
    principal['tenant_id'] = 'tenant-a'
    second = service.research.submit('tenant-a', body.model_copy(update={'idempotency_key': 'source-farm-second'}))[2]
    with pytest.raises(SourceFarmSelectionHold): read(second['job_id'], child['job_id'])
    assert worker.run_once().state == 'succeeded'
    with pytest.raises(SourceFarmSelectionHold): read(second['job_id'], child['job_id'])
    queued = service.collection.submit('tenant-a', str(second['job_id']), 'source-farm-pending-collection')
    with pytest.raises(SourceFarmSelectionHold): read(second['job_id'], queued['job_id'])
    assert read(root['job_id'], child['job_id']) is not None


def test_selection_rechecks_current_inputs_and_late_changes(source_setup, monkeypatch):
    service, root, child, principal, _, _ = source_setup
    pin_existing_snapshot(service)
    read = lambda: service.get('tenant-a', root['job_id'], child['job_id'])
    runs = service.research.runs
    with monkeypatch.context() as patch:
        original = runs.get_snapshot
        patch.setattr(runs, 'get_snapshot', lambda *args: original(*args) | {'weather_raw': b'corrupt fixture'})
        with pytest.raises(SourceFarmSelectionHold): read()
    with monkeypatch.context() as patch:
        original = runs.get_decision_context
        patch.setattr(runs, 'get_decision_context', lambda *args: original(*args) | {
            'decision_at_utc': '2026-09-28T01:00:00Z'})
        with pytest.raises(SourceFarmSelectionHold): read()
    original_read = service._read
    for change in ('scope', 'binding', 'selection', 'private'):
        calls = 0
        def changed(*args):
            nonlocal calls
            value = original_read(*args)
            calls += 1
            if calls == 1:
                if change == 'scope': principal['scopes'].remove('collection_read')
                if change == 'binding': runs._context_verifier = lambda *_: None
                if change == 'private': raise RuntimeError('synthetic private source backend detail')
            if change == 'selection' and calls == 2:
                return value.model_copy(update={'weather_sha256': '0' * 64})
            return value
        old_verifier = runs._context_verifier
        with monkeypatch.context() as patch:
            patch.setattr(service, '_read', changed)
            with pytest.raises((SourceFarmSelectionHold, PermissionError, RuntimeError)) as failure: read()
            assert 'private' not in str(failure.value)
        runs._context_verifier = old_verifier
        principal['scopes'].add('collection_read')
    publication = service.collection.jobs.get_publication('tenant-a', child['job_id'])
    jobs = service.collection.jobs
    raw = jobs.read_artifact('tenant-a', child['job_id'])
    directory = jobs._content_directory()
    def replace_record(data):
        fd = os.open(publication['artifact_sha256'], os.O_WRONLY | os.O_TRUNC | os.O_NOFOLLOW, dir_fd=directory)
        with os.fdopen(fd, 'wb') as stream: stream.write(data)
    calls = 0
    def corrupt_after_first(*args):
        nonlocal calls
        value = original_read(*args)
        calls += 1
        if calls == 1: replace_record(b'corrupt collected fixture')
        return value
    try:
        with monkeypatch.context() as patch:
            patch.setattr(service, '_read', corrupt_after_first)
            with pytest.raises(SourceFarmSelectionHold): read()
    finally:
        replace_record(raw)
        os.close(directory)
    assert read() is not None


def test_selection_requires_actual_bound_services():
    with pytest.raises(ValueError, match='^source farm selection binding rejected$'):
        SourceFarmSelectionService(None, None)
