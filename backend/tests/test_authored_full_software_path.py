"""Synthetic software chain from an owned farm to an immutable thermal Run.

The CLI executable, observer and reviewer are test authorities. This test
cannot establish an independent G1 review or any agricultural claim.
"""

import json
from datetime import datetime, timedelta, timezone
import os
from pathlib import Path
import subprocess
import sys
import threading
import time

from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from psycopg import sql
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.authored_thermal_candidate import calculate_authored_candidate
from app.api_authored_thermal import AUTHORED_READ_SCOPES, project_authored_run
from app.api_runtime import ApiRuntime
from app.calculation_assessment import CalculationAssessmentService
from app.cli_worker import CliWorker
from app.execution_attestation import ExecutionAttestationStore
from app.execution_verifier import ExecutionVerifier
from app.farm_authored_release import AuthoredReleaseVerifier, KINDS
from app.farm_authored_release_store import AuthoredReleaseStore
from app.farm_authored_review import FarmAuthoredReviewService, REVIEW_SCOPES
from app.farm_authored_review_completion import AuthoredReviewCompletionVerifier
from app.farm_authored_run import AuthoredRunPreparer
from app.farm_authored_run_store import AuthoredRunStore
from app.farm_authored_simulation import AuthoredSimulationService
from app.farm_authored_simulation_worker import AuthoredSimulationWorker
from app.farm_authoring_storage import FarmAuthoringService
from app.http_identity import BearerGrant, BearerRegistry, token_digest
from app.market_source_store import MarketSourceStore
from app.owned_fixture_registry import OwnedFixtureRegistry
from app.market_result_store import MarketResultStore
from app.owned_cli_contracts import OwnedCliContractRouter
from app.owned_collection_review import OwnedCollectionReviewService
from app.owned_fixture_collection import CollectionService
from test_cli_worker import _fake_cli
from test_api_runtime import config, dependencies
from test_api_serve import tls_files
from test_execution_attestation import _signed as signed_execution
from test_farm_authoring_storage import authoring, request
from test_farm_authored_release import _public, _signed as signed_release
from test_farm_authored_review import self_authored_evidence_policy
from test_farm_replay_scenario import farm_setup
from login_database import login_database, login_scope
from web_shell_smoke import WEB, frontend


ROOT = Path(__file__).resolve().parents[2]
REVIEW_BROWSER_UUID = '11111111-1111-4111-8111-111111111111'
RUN_BROWSER_UUID = '22222222-2222-4222-8222-222222222222'
PROFILE = {
    'market_calculation': True, 'market_source_storage': True,
    'thermal_scenario_storage': True, 'break_even_calculation': True,
    'authored_release_storage': True, 'authored_run_storage': True,
}


@pytest.mark.parametrize('login_scope', [PROFILE], indirect=True)
def test_owned_farm_review_release_and_worker_publish_one_replayable_run(
        authoring, login_scope, tls_files, tmp_path, monkeypatch):
    author, body, principal = authoring
    principal['scopes'].update({
        'collection_review_create', 'authored_release_write',
        'authored_release_read', 'simulation_create', 'simulation_execute',
        'authored_run_publish', 'authored_run_read',
    })
    registration = author.submit('tenant-1', request(body))
    review = FarmAuthoredReviewService(author)
    review_job = review.submit('tenant-1', 'farm-1', 'r1',
                               registration.scenario_sha256,
                               'review-' + REVIEW_BROWSER_UUID)
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
                             registration.scenario_sha256,
                             'run-' + RUN_BROWSER_UUID)
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

    # Read the Run produced by this actual registration/review/worker chain
    # through the standard authenticated HTTPS assembly and Chromium viewer.
    _, series = project_authored_run(run)
    cert, key, _ = tls_files
    now = datetime.now(timezone.utc)
    token = b'synthetic-full-path-browser-' + b'x' * 32
    grant = BearerGrant(token_digest(token), 'tenant-1', frozenset((*AUTHORED_READ_SCOPES,
        *REVIEW_SCOPES, 'simulation_create')),
        now - timedelta(seconds=1), now + timedelta(minutes=20))
    source_factory = lambda *, principal_provider: MarketSourceStore(
        jobs._dsn, jobs.schema, principal_provider=principal_provider,
        runtime_identity=jobs.runtime_identity)

    def authored_factory(*, job_store, farm_scenario_service, gate_key):
        preparer.authoring = FarmAuthoringService(farm_scenario_service)
        completion.review = FarmAuthoredReviewService(preparer.authoring)
        completion.jobs = job_store
        preparer.release_store.jobs = job_store
        return AuthoredRunStore(preparer, gate_key)

    runtime = ApiRuntime(config(policy=jobs.runtime_identity[0], dsn=jobs._dsn,
        artifact_root=jobs.artifact_root, certificate=cert, private_key=key,
        port=0, authored_run_gate_key=run_store.gate_key),
        dependencies(research_registry=author.replay.registry,
            bearer_registry=BearerRegistry((grant,)),
            market_source_factory=source_factory,
            market_scope_resolver=author.replay.thermal.holds._scope_resolver,
            owned_fixture_registry=OwnedFixtureRegistry(ROOT),
            owned_research_contexts={next(iter(author.replay.registry._scopes)): 'context-1'},
            authored_run_store_factory=authored_factory))
    server = runtime.service.server()
    thread = threading.Thread(target=server.run, daemon=True)
    thread.start()
    browser = None
    try:
        deadline = time.monotonic() + 15
        while not server.started:
            assert thread.is_alive() and time.monotonic() < deadline
            time.sleep(0.01)
        api_port = server.servers[0].sockets[0].getsockname()[1]
        with frontend(f'https://127.0.0.1:{api_port}', cert, key) as (web_port, _):
            env = {name: os.environ[name] for name in
                ('PATH', 'HOME', 'LANG', 'PLAYWRIGHT_BROWSERS_PATH') if name in os.environ}
            browser = subprocess.Popen(['node', 'e2e/real-thermal-replay-smoke.mjs',
                f'https://127.0.0.1:{web_port}', str(tmp_path / 'full-path-screens')],
                cwd=WEB, env=env, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                stderr=subprocess.PIPE, text=True)
            browser.stdin.write(json.dumps({'kind': 'authored', 'token': token.decode(),
                'job_id': str(job['job_id']), 'run_id': worked.run_id,
                'farm': {'scenario_id': 'farm-1', 'revision': 'r1',
                    'registration_sha256': registration.scenario_sha256},
                'workflow': {'review_uuid': REVIEW_BROWSER_UUID,
                    'run_uuid': RUN_BROWSER_UUID,
                    'review_job_id': proof.review_job_id},
                'series': series.model_dump(mode='json')}) + '\n')
            browser.stdin.flush()
            output, error = browser.communicate(timeout=450)
            assert browser.returncode == 0, error[:1800] + error[-1200:]
            report = json.loads(output)
            assert report['stage'] == 'verified' and report['points'] == 120
            assert len(report['network']) == 8
            assert [item['status'] for item in report['network']].count(202) == 2
            assert all(item['status'] in (200, 202) for item in report['network'])
            print('authored_full_browser=' + json.dumps(report))
            print('authored_full_screens=' + str(tmp_path / 'full-path-screens'))
    finally:
        if browser is not None and browser.poll() is None:
            browser.kill()
            browser.communicate(timeout=5)
        server.should_exit = True
        thread.join(timeout=15)
        assert not thread.is_alive()
