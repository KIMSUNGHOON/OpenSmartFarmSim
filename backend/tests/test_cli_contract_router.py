"""Mixed durable CLI stages; fake executables and keys do not establish G1."""

from hashlib import sha256
import json
from pathlib import Path
import sys

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.cli_contract_router import CliContractRouter
from app.cli_contracts import AuthoritySnapshot, DecisionContract, ProposalHold
from app.cli_worker import CliWorker
from app.jobs import canonical_input_bytes
from app.owned_collection_review import OwnedCollectionReviewContract
from app.thermal_publisher import collection_review_input, collection_review_proposal
from app.thermal_review_contract import ThermalReviewContract
from test_cli_contracts import encoded, input_for, job_for, proposal, resolver
from test_cli_worker import _fake_cli
from test_owned_collection_review import review_setup
from test_owned_fixture_collection import collection_setup, login_scope, login_database


def generic_routes():
    return {(stage, stage+'_input_v1'): DecisionContract(resolver)
            for stage in ('research', 'collection_review', 'assessment')}


@pytest.mark.parametrize('stage', ['research', 'collection_review', 'assessment'])
def test_router_preserves_each_server_hold_and_validator_version(stage):
    routes = generic_routes()
    router = CliContractRouter(routes)
    job = job_for(stage)
    final = encoded(proposal(job))
    child = routes[(stage, stage+'_input_v1')]
    assert router.input_context(job) == child.input_context(job)
    plan = router.plan(job, final)
    assert plan == child.plan(job, final)
    assert router(job, final, plan.artifact) == child(job, final, plan.artifact)
    assert router(job, final, b'{}')['passed'] is False


@pytest.mark.parametrize('fault', ['version', 'stage', 'hash', 'duplicate', 'not_object'])
def test_unregistered_or_corrupt_input_never_calls_an_authority(fault):
    def forbidden(*_):
        pytest.fail('invalid input reached an authority')
    routes = {(stage, stage+'_input_v1'): DecisionContract(forbidden)
              for stage in ('research', 'collection_review', 'assessment')}
    router = CliContractRouter(routes)
    job = job_for('research')
    value = json.loads(job['input_bytes'])
    if fault == 'version': value['input_version'] = 'research_input_v99'
    if fault == 'stage': job['stage'] = 'simulation'
    raw = canonical_input_bytes(value)
    if fault == 'duplicate': raw = b'{"input_version":"research_input_v1","input_version":"assessment_input_v1"}'
    if fault == 'not_object': raw = b'[]'
    job.update(input_bytes=raw, input_sha256=sha256(raw).hexdigest())
    if fault == 'hash': job['input_sha256'] = '0'*64
    with pytest.raises(ProposalHold): router.input_context(job)
    with pytest.raises(ProposalHold): router.plan(job, b'{}')
    result = router(job, b'{}', b'{}')
    assert result['passed'] is False and result['disposition'] is None


def test_route_registration_is_copied_and_read_only():
    routes = generic_routes()
    router = CliContractRouter(routes)
    routes.clear()
    assert router.plan(job_for('research'), encoded(proposal(job_for('research')))).disposition == 'hold'
    with pytest.raises(TypeError): router._routes[('research', 'research_input_v1')] = None


@pytest.mark.parametrize('fault', ['missing_stage', 'bad_key', 'bad_stage', 'bad_version', 'bad_contract'])
def test_incomplete_or_invalid_server_configuration_is_rejected(fault):
    routes = generic_routes()
    if fault == 'missing_stage': routes.pop(('assessment', 'assessment_input_v1'))
    if fault == 'bad_key': routes['research'] = DecisionContract(resolver)
    if fault == 'bad_stage': routes[('simulation', 'simulation_input_v1')] = DecisionContract(resolver)
    if fault == 'bad_version': routes[('research', '../private\n')] = DecisionContract(resolver)
    if fault == 'bad_contract': routes[('research', 'research_input_v1')] = lambda *_: None
    with pytest.raises(ValueError, match='CLI contract routes rejected'): CliContractRouter(routes)


def test_shared_worker_routes_research_owned_legacy_review_and_assessment(review_setup, tmp_path):
    service, collected, _, snapshot_id, _ = review_setup
    jobs = service.collection.jobs
    def review_authority(job, value):
        fields = (OwnedCollectionReviewContract.BINDING_FIELDS
                  if value['input_version'] == 'owned-collection-review-input-v1'
                  else ThermalReviewContract.BINDING_FIELDS)
        return AuthoritySnapshot(job['tenant_id'], 'collection_review', job['input_sha256'],
            frozenset({snapshot_id}), {}, True, (), {}, frozenset(), False,
            {key:value[key] for key in fields}, value['decision_context_id'],
            value['decision_at_utc'], value['claim_mode'], value['decision_time_kind'])
    routes = generic_routes()
    owned = OwnedCollectionReviewContract(service, review_authority)
    legacy = ThermalReviewContract(service.runs, review_authority)
    routes[('collection_review', 'owned-collection-review-input-v1')] = owned
    routes[('collection_review', 'thermal-g1-collection-review-input-v1')] = legacy
    router = CliContractRouter(routes)
    jobs.decision_validator = router
    research = jobs.submit('tenant-a', 'research', input_for('research'), 'mixed-research')
    reviewed = service.submit('tenant-a', str(collected['job_id']), 'mixed-owned')
    snapshot = service.runs.get_snapshot('tenant-a', snapshot_id)
    record = service.collection.read_record('tenant-a', str(collected['job_id']))
    context = service.runs.get_decision_context('tenant-a', snapshot_id, record['decision_context_id'])
    old = jobs.submit('tenant-a', 'collection_review', collection_review_input(snapshot, context), 'mixed-legacy')
    assessment = jobs.submit('tenant-a', 'assessment', input_for('assessment'), 'mixed-assessment')
    unknown = jobs.submit('tenant-a', 'research', {'input_version':'research_input_v99'}, 'mixed-unknown')
    program = _fake_cli(tmp_path)
    program.write_text(program.read_text().replace("['candidate-a'] if context['server_allows_proceed']",
        "[context['input']['candidate_ids'][0]] if context['server_allows_proceed']"))
    home = tmp_path/'routed-home'; home.mkdir(mode=0o700)
    worker = CliWorker(jobs, router, cli_path=program, codex_home=home,
        child_env={'CODEX_API_KEY':'synthetic-test-key'}, timeout_seconds=10,
        lease_seconds=300, synthetic_smoke=True)
    expected = [(research, 'hold', DecisionContract.VERSION),
                (reviewed, 'succeeded', owned.VERSION), (old, 'succeeded', legacy.VERSION),
                (assessment, 'hold', DecisionContract.VERSION)]
    for submitted, state, version in expected:
        result = worker.run_once()
        assert result.job_id == submitted['job_id'] and result.state == state
        decision = jobs.list_decisions('tenant-a', submitted['job_id'])[0]
        report = json.loads(jobs.read_evidence('tenant-a', submitted['job_id'], decision['validation_evidence_id']))
        assert report['passed'] is True and report['validator_version'] == version
        if state == 'hold':
            assert json.loads(jobs.read_hold_report('tenant-a', submitted['job_id']))['missing_evidence'] == ['real_source_g0']
            assert jobs.get_publication('tenant-a', submitted['job_id']) is None
        else:
            assert json.loads(jobs.read_artifact('tenant-a', submitted['job_id'])) == collection_review_proposal(snapshot, context)
    result = worker.run_once()
    assert result.job_id == unknown['job_id'] and result.state == 'hold'
    assert result.reason_code == 'decision_contract_unregistered'
    assert jobs.get_invocation('tenant-a', unknown['job_id'], 1) is None
    assert worker.run_once() is None
    assert service.collection.read_record('tenant-a', str(collected['job_id']))['g0_status'] == 'not_accepted'
