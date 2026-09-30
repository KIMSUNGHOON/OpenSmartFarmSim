"""Synthetic software chain from an owned farm to an immutable thermal Run.

The CLI executable, observer and reviewer are test authorities. This test
cannot establish an independent G1 review or any agricultural claim.
"""

import json
from pathlib import Path
import sys

from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from psycopg import sql
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.authored_thermal_candidate import calculate_authored_candidate
from app.calculation_assessment import CalculationAssessmentService
from app.cli_worker import CliWorker
from app.execution_attestation import ExecutionAttestationStore
from app.execution_verifier import ExecutionVerifier
from app.farm_authored_release import AuthoredReleaseVerifier, KINDS
from app.farm_authored_release_store import AuthoredReleaseStore
from app.farm_authored_review import FarmAuthoredReviewService
from app.farm_authored_review_completion import AuthoredReviewCompletionVerifier
from app.farm_authored_run import AuthoredRunPreparer
from app.farm_authored_run_store import AuthoredRunStore
from app.farm_authored_simulation import AuthoredSimulationService
from app.farm_authored_simulation_worker import AuthoredSimulationWorker
from app.market_result_store import MarketResultStore
from app.owned_cli_contracts import OwnedCliContractRouter
from app.owned_collection_review import OwnedCollectionReviewService
from app.owned_fixture_collection import CollectionService
from test_cli_worker import _fake_cli
from test_execution_attestation import _signed as signed_execution
from test_farm_authoring_storage import authoring, request
from test_farm_authored_release import _public, _signed as signed_release
from test_farm_authored_review import self_authored_evidence_policy
from test_farm_replay_scenario import farm_setup
from login_database import login_database, login_scope


ROOT = Path(__file__).resolve().parents[2]
PROFILE = {
    'market_calculation': True, 'market_source_storage': True,
    'thermal_scenario_storage': True, 'break_even_calculation': True,
    'authored_release_storage': True, 'authored_run_storage': True,
}


@pytest.mark.parametrize('login_scope', [PROFILE], indirect=True)
def test_owned_farm_review_release_and_worker_publish_one_replayable_run(
        authoring, login_scope, tmp_path, monkeypatch):
    author, body, principal = authoring
    principal['scopes'].update({
        'collection_review_create', 'authored_release_write',
        'authored_release_read', 'simulation_create', 'simulation_execute',
        'authored_run_publish', 'authored_run_read',
    })
    registration = author.submit('tenant-1', request(body))
    review = FarmAuthoredReviewService(author)
    review_job = review.submit('tenant-1', 'farm-1', 'r1',
                               registration.scenario_sha256, 'full-software-review')
    jobs = author.replay.jobs
    runs = author.replay.thermal.runs
    results = MarketResultStore(jobs._dsn, jobs.schema, author.replay.candidates,
        principal_provider=jobs.principal_provider, runtime_identity=jobs.runtime_identity)
    assessment = CalculationAssessmentService(jobs, runs, results,
                                                author.replay.thermal, author.replay)
    owned_review = OwnedCollectionReviewService(
        CollectionService(jobs, author.replay.owned_research.registry), runs)
    router = OwnedCliContractRouter(author.replay.owned_research, owned_review,
                                    assessment, lambda *_: None, review)
    jobs.decision_validator = router
    jobs.evidence_policy = self_authored_evidence_policy

    program = _fake_cli(tmp_path)
    program.write_text(program.read_text().replace(
        "['candidate-a'] if context['server_allows_proceed']",
        "[context['input']['candidate_ids'][0]] if context['server_allows_proceed']"))
    home = tmp_path / 'authored-cli-home'
    home.mkdir(mode=0o700)
    cli_worker = CliWorker(jobs, router, cli_path=program, codex_home=home,
        child_env={'CODEX_API_KEY': 'synthetic-test-key'}, timeout_seconds=10,
        lease_seconds=300, synthetic_smoke=True)
    launch = {}
    original_launch = jobs.record_cli_launch

    def capture_launch(*args, **kwargs):
        launch['argv'] = list(kwargs['argv'])
        return original_launch(*args, **kwargs)

    monkeypatch.setattr(jobs, 'record_cli_launch', capture_launch)
    lease = jobs.claim(300, allowed_stages=('collection_review',),
                       tenant_id='tenant-1', job_id=str(review_job['job_id']))
    reviewed = cli_worker._run_claimed(lease)
    assert reviewed.state == 'succeeded'
    with jobs.connect() as conn:
        rows = {name: conn.execute(sql.SQL(
            'SELECT * FROM {} WHERE tenant_id=%s AND job_id=%s').format(
                jobs._table(name)), ('tenant-1', review_job['job_id'])).fetchone()
            for name in ('jobs', 'attempt_invocations', 'attempt_cli_launches',
                         'attempt_cli_captures')}
    record, attestation_raw, signature, observer_store, _, _ = signed_execution(
        jobs, cli_worker, reviewed, rows, launch['argv'])
    base, _, _ = login_scope
    attestations = ExecutionAttestationStore(base, observer_store.public_keys)
    attestations.put(attestation_raw, signature)
    execution = ExecutionVerifier(attestations,
        executable_sha256=record.executable_sha256,
        environment_sha256=record.environment_sha256)
    completion = AuthoredReviewCompletionVerifier(review, execution)
    proof = completion.verify('tenant-1', review_job['job_id'],
                              registration.scenario_sha256)
    candidate = calculate_authored_candidate(author, 'tenant-1', 'farm-1', 'r1',
                                             registration.scenario_sha256)
    assert candidate.candidate_id == proof.candidate_id
    assert candidate.trace_sha256 == proof.trace_sha256
    # The real completion and candidate were checked above. Pin these immutable
    # outputs while this test exercises the downstream service composition.
    # Dedicated tests cover each service's current-state revalidation.
    monkeypatch.setattr(completion, 'verify', lambda *_: proof)
    monkeypatch.setattr('app.farm_authored_run.calculate_authored_candidate',
                        lambda *_: candidate)

    reviewer = Ed25519PrivateKey.generate()
    artifacts = {f'evidence-{kind}': kind.encode() for kind in KINDS}
    release_verifier = AuthoredReleaseVerifier(completion, ROOT,
        {'reviewer-key': ('separate synthetic reviewer', _public(reviewer))},
        lambda tenant, ref: artifacts.get(ref) if tenant == 'tenant-1' else None)
    release_store = AuthoredReleaseStore(release_verifier)
    signed = signed_release(release_verifier, proof, reviewer)
    release = release_store.put('tenant-1', proof.review_job_id,
                                registration.scenario_sha256, *signed)
    assert release.release_sha256 == release_store.get(
        'tenant-1', proof.review_job_id, registration.scenario_sha256).release_sha256

    preparer = AuthoredRunPreparer(author, release_store)
    run_store = AuthoredRunStore(preparer, b'synthetic-full-path-gate-' + b'0' * 32)
    simulation = AuthoredSimulationService(preparer, run_store)
    job = simulation.submit('tenant-1', proof.review_job_id, 'farm-1', 'r1',
                             registration.scenario_sha256, 'full-software-run')
    worker = AuthoredSimulationWorker(run_store, tenant_id='tenant-1')
    worked = worker.run_once(str(job['job_id']))
    assert worked.state == 'succeeded'
    assert worker.run_once(str(job['job_id'])) is None
    run = run_store.get_run('tenant-1', worked.run_id)
    assert run['run_id'] == worked.run_id
    assert run['report']['review_job_id'] == proof.review_job_id
    assert run['report']['release_sha256'] == release.release_sha256
    traces = [json.loads(raw) for raw in run['trace_raws']]
    assert len(traces) == 2 and all(len(trace['steps']) == 60 for trace in traces)
    assert traces[0]['run_id'] == traces[1]['run_id'] == worked.run_id
    assert traces[0]['interval']['end_utc'] == traces[1]['interval']['start_utc']
    assert jobs.get_job('tenant-1', job['job_id'])['state'] == 'succeeded'
    assert run_store.get_run('tenant-other', worked.run_id) is None
