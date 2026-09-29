"""Three actual service routes; synthetic keys/executable establish no G1."""

from hashlib import sha256
import json
from pathlib import Path
import sys

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from app.owned_cli_contracts import OwnedCliContractRouter
from app.owned_research import OwnedResearchService
from app.owned_collection_review import OwnedCollectionReviewService, REVIEW_SCOPES
from app.owned_fixture_collection import CollectionService, CollectionWorker
from app.owned_fixture_registry import OwnedFixtureRegistry
from app.orchestration import LocationRequest
from app.research_registry import ResearchRegistry, _scope_key
from app.cli_contracts import AuthoritySnapshot, ProposalHold
from app.cli_worker import CliWorker
from app.jobs import canonical_input_bytes
from test_calculation_assessment import assessment_setup, login_scope, login_database, pytestmark as PROFILE_MARK
from test_cli_worker import _fake_cli


@pytest.fixture
def routed_setup(assessment_setup):
    assessment, thermal_job, economic_job, principal = assessment_setup
    registry = OwnedFixtureRegistry(Path(__file__).resolve().parents[2])
    collection = CollectionService(assessment.jobs, registry)
    review = OwnedCollectionReviewService(collection, assessment.runs)
    context = assessment.prepare('tenant-1', thermal_job, economic_job)[0]
    bundle = registry.read_bundle(context['decision_at_utc'], context['claim_mode'])
    body = LocationRequest(latitude=37.5, longitude=127.0,
        period_start_utc=bundle['start_utc'], period_end_utc=bundle['end_utc'],
        goal_id='owned-fixture-contract-check', idempotency_key='shared-research')
    catalog_raw = canonical_input_bytes({'registry_version':'research-registry-v1', 'registrations':[{
        'tenant_id':'tenant-1', 'point':{'latitude':body.latitude, 'longitude':body.longitude},
        'period_start_utc':body.period_start_utc, 'period_end_utc':body.period_end_utc,
        'goal_id':body.goal_id, 'provider_ids':[registry.provider_id]}]})
    catalog = ResearchRegistry(catalog_raw, sha256(catalog_raw).hexdigest())
    contexts = {_scope_key('tenant-1', (body.latitude, body.longitude), body.period_start_utc,
        body.period_end_utc, body.goal_id):context['decision_context_id']}
    research = OwnedResearchService(assessment.jobs, assessment.runs, catalog, registry, contexts)
    principal['scopes'].update((*REVIEW_SCOPES, 'location_create', 'collection_execute'))
    calls = []
    def review_authority(job, value):
        calls.append(job['job_id'])
        return AuthoritySnapshot(job['tenant_id'], 'collection_review', job['input_sha256'],
            frozenset({value['snapshot_id']}), {}, True, (), {}, frozenset(), False,
            {key:value[key] for key in review_contract_fields()},
            **{key:value[key] for key in ('decision_context_id','decision_at_utc','claim_mode','decision_time_kind')})
    return research, review, assessment, review_authority, body, thermal_job, economic_job, calls


def review_contract_fields():
    from app.owned_collection_review import OwnedCollectionReviewContract
    return OwnedCollectionReviewContract.BINDING_FIELDS


@pytest.mark.parametrize('values', [(None, None, None, None), (object(), None, None, lambda *_:None)])
def test_invalid_configuration_is_bounded(values):
    with pytest.raises(ValueError, match='^owned CLI contract assembly rejected$'):
        OwnedCliContractRouter(*values)


@PROFILE_MARK
def test_one_worker_routes_research_collection_review_and_held_assessment(routed_setup, tmp_path):
    research, review, assessment, authority, body, thermal_job, economic_job, calls = routed_setup
    router = OwnedCliContractRouter(research, review, assessment, authority)
    jobs = assessment.jobs
    jobs.decision_validator = router
    program = _fake_cli(tmp_path)
    program.write_text(program.read_text().replace("['candidate-a'] if context['server_allows_proceed']",
        "[context['input']['candidate_ids'][0]] if context['server_allows_proceed']"))
    home = tmp_path/'shared-home'; home.mkdir(mode=0o700)
    worker = CliWorker(jobs, router, cli_path=program, codex_home=home,
        child_env={'CODEX_API_KEY':'synthetic-test-key'}, timeout_seconds=10,
        lease_seconds=300, synthetic_smoke=True)
    _, _, researched = research.submit('tenant-1', body)
    assert worker.run_once().state == 'succeeded'
    collected = review.collection.submit('tenant-1', str(researched['job_id']), 'shared-collection')
    assert CollectionWorker(review.collection, tenant_id='tenant-1').run_once(str(collected['job_id'])).state == 'succeeded'
    reviewed = review.submit('tenant-1', str(collected['job_id']), 'shared-review')
    assert worker.run_once().state == 'succeeded' and calls
    assessed = assessment.submit('tenant-1', thermal_job, economic_job, 'shared-assessment')
    assert worker.run_once().state == 'hold'
    assert json.loads(jobs.read_hold_report('tenant-1', assessed['job_id']))['missing_evidence'] == list(assessment.MISSING_EVIDENCE)
    assert jobs.get_publication('tenant-1', assessed['job_id']) is None
    for job, version in ((researched, 'decision-server-v2'),
            (reviewed, 'owned-collection-review-server-v1'), (assessed, 'calculation-assessment-server-v1')):
        decision = jobs.list_decisions('tenant-1', job['job_id'])[0]
        report = json.loads(jobs.read_evidence('tenant-1', job['job_id'], decision['validation_evidence_id']))
        assert report['passed'] is True and report['validator_version'] == version
    unknown = jobs.submit('tenant-1', 'assessment', {'input_version':'assessment_input_v1'}, 'unregistered-legacy')
    result = worker.run_once()
    assert result.job_id == unknown['job_id'] and result.reason_code == 'decision_contract_unregistered'
    assert jobs.get_invocation('tenant-1', unknown['job_id'], 1) is None
    assert worker.run_once() is None


@PROFILE_MARK
def test_mixed_or_changed_bindings_never_reach_authority(routed_setup):
    from copy import copy
    research, review, assessment, authority, body, *_ = routed_setup
    foreign = copy(research)
    foreign.registry = OwnedFixtureRegistry(Path(__file__).resolve().parents[2])
    with pytest.raises(ValueError, match='^owned CLI contract assembly rejected$'):
        OwnedCliContractRouter(foreign, review, assessment, authority)
    for name, value in (('store', copy(research.store)), ('runs', copy(research.runs))):
        foreign = copy(research)
        setattr(foreign, name, value)
        with pytest.raises(ValueError, match='^owned CLI contract assembly rejected$'):
            OwnedCliContractRouter(foreign, review, assessment, authority)
    with pytest.raises(ValueError, match='^owned CLI contract assembly rejected$'):
        OwnedCliContractRouter(research, review, assessment, None)
    router = OwnedCliContractRouter(research, review, assessment, authority)
    _, _, admitted = research.submit('tenant-1', body)
    with assessment.jobs.connect() as conn:
        job = assessment.jobs._locked_job(conn, 'tenant-1', admitted['job_id'])
    verifier = research.runs._context_verifier
    research.runs._context_verifier = lambda *_:None
    for operation in (router.input_context, router.binding_fields):
        with pytest.raises(ProposalHold, match='owned_cli_binding_hold'): operation(job)
    result = router(job, b'{}', b'{}')
    assert result == {'passed':False, 'version':router.VERSION, 'code':'owned_cli_binding_hold', 'disposition':None}
    research.runs._context_verifier = verifier
    original = research.authority_snapshot
    def change_during_authority(job, value):
        resolved = original(job, value)
        research.runs._context_verifier = lambda *_:None
        return resolved
    research.authority_snapshot = change_during_authority
    router = OwnedCliContractRouter(research, review, assessment, authority)
    with pytest.raises(ProposalHold, match='owned_cli_binding_hold'): router.input_context(job)
    research.runs._context_verifier = verifier
    from test_cli_contracts import proposal, encoded
    value = json.loads(job['input_bytes'])
    final = proposal(job, status='proceed') | {'selected_ids':[research.registry.provider_id],
        **{key:value[key] for key in ('decision_context_id','decision_at_utc','claim_mode','decision_time_kind')}}
    result = router(job, encoded(final), b'{}')
    assert result['passed'] is False and result['code'] == 'owned_cli_binding_hold'
