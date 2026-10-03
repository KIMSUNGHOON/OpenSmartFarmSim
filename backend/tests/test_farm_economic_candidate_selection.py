"""Real SCRAM source/candidate selection; CLI, keys and all data are fixtures."""

from copy import deepcopy
from hashlib import sha256
import hmac
from pathlib import Path
import sys
from uuid import UUID, uuid4

import pytest
from psycopg import sql

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from app.api_economic_scenario import EconomicScenarioRequest
from app.api_market_source import MarketUserSourceRequest, MarketUserSourceService
from app.cli_contracts import DecisionContract
from app.cli_worker import CliWorker
from app.farm_economic_candidate_selection import (FarmEconomicCandidateService,
    FarmEconomicCandidateHold, READ_SCOPES)
from app.farm_authoring_storage import FarmAuthoringRequest
from app.jobs import canonical_input_bytes
from app.market_scenario import MarketScenarioService, _json
from app.owned_fixture_collection import CollectionService, CollectionWorker
from app.source_farm_selection import SourceFarmSelectionService
from test_cli_worker import _fake_cli
from test_farm_authoring_storage import authoring, farm_setup, login_scope, login_database
from test_job_evidence import cli_store
from test_market_hold_store import CONTEXT_KEY


PROFILE = {'market_calculation': True, 'market_source_storage': True,
    'thermal_scenario_storage': True, 'break_even_calculation': True}


@pytest.fixture
def candidate_selection(authoring, login_scope, tmp_path):
    farm, body, principal = authoring
    replay = farm.replay
    research = replay.owned_research
    jobs = replay.jobs
    principal['scopes'].update((*READ_SCOPES, 'collection_execute'))
    jobs.evidence_policy = cli_store(login_scope[0]).evidence_policy
    contract = DecisionContract(research.authority_snapshot)
    jobs.decision_validator = contract
    program = _fake_cli(tmp_path)
    program.write_text(program.read_text().replace('candidate-a', research.registry.provider_id))
    home = tmp_path / 'candidate-selection-cli-home'
    home.mkdir(mode=0o700)
    cli = CliWorker(jobs, contract, cli_path=program, codex_home=home,
        child_env={'CODEX_API_KEY': 'synthetic-test-key'}, timeout_seconds=10,
        lease_seconds=300, synthetic_smoke=True)
    root_id = UUID(body['farm']['research_job_id'])
    lease = jobs.claim(300, tenant_id='tenant-1', job_id=str(root_id), allowed_stages=('research',))
    assert lease is not None and cli._run_claimed(lease).state == 'succeeded'
    collection = CollectionService(jobs, research.registry)
    child = collection.submit('tenant-1', str(root_id), 'candidate-selection-source')
    assert CollectionWorker(collection, tenant_id='tenant-1').run_once(str(child['job_id'])).state == 'succeeded'
    source = SourceFarmSelectionService(research, collection)
    service = FarmEconomicCandidateService(source, replay.economic)
    return service, root_id, child['job_id'], body, principal, farm


def counts(service):
    jobs = service.economic.jobs
    with jobs.connect() as conn:
        return tuple(conn.execute(sql.SQL('SELECT count(*) AS n FROM {}').format(jobs._table(name))).fetchone()['n']
            for name in ('jobs', 'thermal_input_snapshots', 'decision_contexts', 'market_hold_reports',
                         'market_candidate_pins', 'market_candidate_inputs'))


def new_candidate(service, body, revision, market_context=None):
    store = service.economic.candidates
    old = store.get_market_candidate(body['farm']['economic']['scenario_id'], body['farm']['economic']['revision'])
    request = deepcopy(old['request'])
    source = store._source._source
    intake = MarketUserSourceService(service.economic.jobs, source)
    if market_context is not None:
        baseline = deepcopy(source.get_economic_scenario(request['baseline']['scenario_id'],
            request['baseline']['revision']))
        baseline.pop('tenant_id')
        baseline['scenario_id'] = 'candidate-test-baseline-' + revision
        baseline['market_context'] = baseline['scenario_market_context'] = market_context
        intake.submit('tenant-1', MarketUserSourceRequest.model_validate_json(_json({
            'kind': 'economic_scenario', 'input': baseline,
            'idempotency_key': 'candidate-test-baseline-' + revision})))
        pin = source.get_economic_scenario_pin(baseline['scenario_id'], baseline['scenario_revision'])
        request['baseline'] = {'scenario_id': baseline['scenario_id'],
            'revision': baseline['scenario_revision'], 'sha256': pin['payload_sha256']}
        request['market_context'] = market_context
    shock = deepcopy(source.get_joint_shock(request['shock']['shock_id'], request['shock']['revision']))
    shock.pop('tenant_id')
    shock['revision'] = revision
    shock['baseline_sha256'] = request['baseline']['sha256']
    intake.submit('tenant-1',
        MarketUserSourceRequest.model_validate_json(_json({'kind': 'joint_shock', 'input': shock,
            'idempotency_key': 'candidate-test-shock-' + revision})))
    request['shock']['revision'] = revision
    request['shock']['sha256'] = source.get_joint_shock_pin(request['shock']['shock_id'], revision)['sha256']
    return service.economic.submit('tenant-1', EconomicScenarioRequest.model_validate_json(_json({
        'request': request, 'idempotency_key': 'candidate-test-economic-' + revision})))


@pytest.mark.parametrize('login_scope', [PROFILE], indirect=True)
def test_current_selection_is_read_only_and_feeds_actual_farm_registration(candidate_selection):
    service, root, child, body, principal, farm = candidate_selection
    original_scopes = set(principal['scopes'])
    principal['scopes'] = set(READ_SCOPES)
    before = counts(service)
    page = service.list('tenant-1', root, child)
    assert page.verification == 'requires_current_selection' and page.next_cursor is None
    assert len(page.items) == 1
    expected = body['farm']['economic']
    assert page.items[0].economic.model_dump(mode='json') == expected
    selected = service.get('tenant-1', root, child, expected['candidate_id'])
    assert selected == service.get('tenant-1', root, child, expected['candidate_id'])
    assert selected.verification == 'requires_registration_recheck'
    assert selected.source == page.source and selected.source.claim_mode == 'ex_post_replay'
    assert selected.source.assessment_status == 'hold' and selected.source.g1_status == 'not_accepted'
    assert selected.market_context.model_dump(mode='json') == body['farm']['market_context']
    assert selected.period_start.isoformat() == body['farm']['period_start']
    assert selected.period_end.isoformat() == body['farm']['period_end']
    assert counts(service) == before
    raw = selected.model_dump_json().encode()
    for hidden in (b'raw_utf8', b'signature', b'CODEX_API_KEY', b'harvest', b'money', b'rights_manifest'):
        assert hidden not in raw
    for scope in READ_SCOPES:
        principal['scopes'].remove(scope)
        with pytest.raises(PermissionError): service.list('tenant-1', root, child)
        with pytest.raises(PermissionError): service.get('tenant-1', root, child, expected['candidate_id'])
        principal['scopes'].add(scope)
    principal['scopes'] = original_scopes
    document = deepcopy(body)
    document['farm'].update(research_job_id=selected.source.research_job_id,
        snapshot_id=selected.source.snapshot_id, decision_context_id=selected.source.decision_context_id,
        decision_at=selected.source.decision_at_utc, market_context=selected.market_context.model_dump(mode='json'),
        economic=selected.economic.model_dump(mode='json'), period_start=selected.period_start.isoformat(),
        period_end=selected.period_end.isoformat())
    accepted = farm.submit('tenant-1', FarmAuthoringRequest.model_validate_json(canonical_input_bytes(document)))
    assert accepted.registration_status == 'registered_unpublished_inputs'
    assert accepted.intent_job.state == 'queued'


@pytest.mark.parametrize('login_scope', [PROFILE], indirect=True)
def test_catalog_pages_use_exact_timestamp_id_and_defer_current_rights(candidate_selection, monkeypatch):
    service, root, child, body, _, _ = candidate_selection
    two = new_candidate(service, body, 'r2')
    three = new_candidate(service, body, 'r3')
    expected = {body['farm']['economic']['candidate_id'], two.candidate_id, three.candidate_id}
    items, cursor = [], None
    for _ in range(3):
        page = service.list('tenant-1', root, child, limit=1,
            **({'before_recorded_at': cursor.recorded_at, 'before_candidate_id': cursor.candidate_id} if cursor else {}))
        assert len(page.items) == 1 and page.verification == 'requires_current_selection'
        items.extend(page.items)
        cursor = page.next_cursor
    assert cursor is None and {item.economic.candidate_id for item in items} == expected
    assert len({item.economic.candidate_id for item in items}) == 3
    first = items[0]
    equal_time = service.list('tenant-1', root, child, before_recorded_at=first.recorded_at,
        before_candidate_id='f' * 64)
    assert equal_time.items[0].economic.candidate_id == first.economic.candidate_id
    excluded = service.list('tenant-1', root, child, before_recorded_at=first.recorded_at,
        before_candidate_id='0' * 64)
    assert first.economic.candidate_id not in {item.economic.candidate_id for item in excluded.items}
    for options in ({'limit': True}, {'limit': 51}, {'before_candidate_id': 'a' * 64},
            {'before_recorded_at': first.recorded_at.replace(tzinfo=None), 'before_candidate_id': 'a' * 64}):
        with pytest.raises(ValueError): service.list('tenant-1', root, child, **options)
    source = service.economic.candidates._source._source
    monkeypatch.setattr(source, 'get_input_rights', lambda *_: None)
    assert len(service.list('tenant-1', root, child).items) == 3
    with pytest.raises(FarmEconomicCandidateHold): service.get('tenant-1', root, child, two.candidate_id)


@pytest.mark.parametrize('login_scope', [PROFILE], indirect=True)
def test_exact_selection_rejects_foreign_missing_and_late_changes(candidate_selection, monkeypatch):
    service, root, child, body, principal, _ = candidate_selection
    candidate = body['farm']['economic']['candidate_id']
    read = lambda: service.get('tenant-1', root, child, candidate)
    assert service.get('tenant-1', uuid4(), child, candidate) is None
    assert service.get('tenant-1', root, child, '0' * 64) is None
    principal['tenant_id'] = 'other-tenant'
    assert service.list('other-tenant', root, child) is None
    assert service.get('other-tenant', root, child, candidate) is None
    principal['tenant_id'] = 'tenant-1'
    with pytest.raises(ValueError): service.get('tenant-1', root, child, 'not-a-digest')
    source_store = service.economic.candidates._source._source
    for fault in ('scope', 'rights', 'binding', 'private'):
        calls = 0
        original = service._current
        def change(*args):
            nonlocal calls
            selected = original(*args)
            calls += 1
            if calls == 1:
                if fault == 'scope': principal['scopes'].remove('market_candidate_read')
                if fault == 'rights': patch.setattr(source_store, 'get_input_rights', lambda *_: None)
                if fault == 'binding': patch.setattr(service.economic.candidates._source._holds,
                    '_scope_resolver', lambda *_: None)
                if fault == 'private': raise RuntimeError('synthetic private candidate backend detail')
            return selected
        with monkeypatch.context() as patch:
            patch.setattr(service, '_current', change)
            with pytest.raises((FarmEconomicCandidateHold, PermissionError)) as failure: read()
            assert 'private' not in str(failure.value)
        principal['scopes'].add('market_candidate_read')
    assert read() is not None


@pytest.mark.parametrize('login_scope', [PROFILE], indirect=True)
def test_valid_same_owner_candidate_in_another_signed_context_is_excluded(candidate_selection):
    service, root, child, body, principal, _ = candidate_selection
    source = service.source.get('tenant-1', root, child)
    holds = service.economic.candidates._source._holds
    runs = holds._context_store
    document = runs.get_decision_context('tenant-1', source.snapshot_id, source.decision_context_id)
    document.pop('context_sha256')
    document.pop('recorded_at')
    document['decision_context_id'] = 'context-other'
    document['planning_event_sha256'] = sha256(b'synthetic other candidate planning event').hexdigest()
    raw = canonical_input_bytes(document)
    signature = hmac.new(CONTEXT_KEY, b'decision-context-v1\0' + raw, sha256).hexdigest()
    principal['scopes'].add('decision_context_write')
    runs.put_decision_context('tenant-1', raw, signature)
    resolver = holds._scope_resolver
    original_scope = resolver('tenant-1', source.snapshot_id, source.decision_context_id)
    holds._scope_resolver = lambda tenant, snapshot, context: (
        dict(original_scope, decision_context_id='context-other') if context == 'context-other'
        else resolver(tenant, snapshot, context))
    report = holds.issue_not_evaluated('tenant-1', source.snapshot_id, 'context-other')
    other = new_candidate(service, body, 'other-context',
        {'kind': 'unavailable', 'hold_report_id': report['hold_report_id']})
    _, valid, record = MarketScenarioService(service.economic.candidates).validate_pinned(
        other.scenario_id, other.scenario_revision, 'tenant-1')
    assert record['candidate_id'] == other.candidate_id and valid.decision_at.isoformat().replace(
        '+00:00', 'Z') == source.decision_at_utc
    before = counts(service)
    page = service.list('tenant-1', root, child)
    assert {item.economic.candidate_id for item in page.items} == {body['farm']['economic']['candidate_id']}
    with pytest.raises(FarmEconomicCandidateHold):
        service.get('tenant-1', root, child, other.candidate_id)
    assert counts(service) == before


def test_candidate_service_rejects_unbound_services():
    with pytest.raises(ValueError, match='^farm economic candidate binding rejected$'):
        FarmEconomicCandidateService(None, None)
