"""Software chain from an owned farm to an immutable thermal Run.

The default CLI is a test executable. Opt-in uses actual Codex CLI, while the
observer and reviewer remain test authorities. Neither mode establishes an
independent G1 review or an agricultural claim.
"""

import json
from datetime import datetime, timedelta, timezone
from hashlib import sha256
import os
from pathlib import Path
import select
import subprocess
import sys
import threading
import time
from uuid import UUID

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
from app.farm_authored_simulation_worker import AuthoredSimulationWorker
from app.farm_authoring_storage import FarmAuthoringService, WRITE_SCOPES
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
from test_farm_authoring_storage import authoring
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
    review = FarmAuthoredReviewService(author)
    jobs = author.replay.jobs
    jobs.artifact_root.mkdir(mode=0o700, exist_ok=True)
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

    real_cli = os.environ.get('OSSF_REAL_AUTHORED_FULL_CLI_SMOKE') == '1'
    if real_cli:
        program = Path(os.environ['OSSF_REAL_CLI_PATH'])
        home = Path(os.environ['OSSF_REAL_CODEX_HOME'])
        child_env = None
    else:
        program = _fake_cli(tmp_path)
        program.write_text(program.read_text().replace(
            "['candidate-a'] if context['server_allows_proceed']",
            "[context['input']['candidate_ids'][0]] if context['server_allows_proceed']"))
        home = tmp_path / 'authored-cli-home'
        home.mkdir(mode=0o700)
        child_env = {'CODEX_API_KEY': 'synthetic-test-key'}
    cli_worker = CliWorker(jobs, router, cli_path=program, codex_home=home,
        child_env=child_env, timeout_seconds=600 if real_cli else 10,
        lease_seconds=660 if real_cli else 300, synthetic_smoke=True)
    launch = {}
    original_launch = jobs.record_cli_launch

    def capture_launch(*args, **kwargs):
        launch['argv'] = list(kwargs['argv'])
        return original_launch(*args, **kwargs)

    monkeypatch.setattr(jobs, 'record_cli_launch', capture_launch)
    base, _, _ = login_scope
    observer = Ed25519PrivateKey.generate()
    attestations = ExecutionAttestationStore(base, {'test-observer-v1': _public(observer)})
    execution = ExecutionVerifier(attestations,
        executable_sha256=sha256(program.read_bytes()).hexdigest(),
        environment_sha256=sha256(b'synthetic-test-environment').hexdigest())
    completion = AuthoredReviewCompletionVerifier(review, execution)
    reviewer = Ed25519PrivateKey.generate()
    artifacts = {f'evidence-{kind}': kind.encode() for kind in KINDS}
    release_verifier = AuthoredReleaseVerifier(completion, ROOT,
        {'reviewer-key': ('separate synthetic reviewer', _public(reviewer))},
        lambda tenant, ref: artifacts.get(ref) if tenant == 'tenant-1' else None)
    release_store = AuthoredReleaseStore(release_verifier)

    preparer = AuthoredRunPreparer(author, release_store)
    run_store = AuthoredRunStore(preparer, b'synthetic-full-path-gate-' + b'0' * 32)

    # Chromium registers the authored farm and creates both jobs. The harness
    # completes the jobs with synthetic
    # reviewer authorities and the actual deterministic simulation worker.
    cert, key, _ = tls_files
    now = datetime.now(timezone.utc)
    token = b'synthetic-full-path-browser-' + b'x' * 32
    grant = BearerGrant(token_digest(token), 'tenant-1', frozenset((*AUTHORED_READ_SCOPES,
        *WRITE_SCOPES, *REVIEW_SCOPES, 'simulation_create')),
        now - timedelta(seconds=1), now + timedelta(minutes=20))
    source_factory = lambda *, principal_provider: MarketSourceStore(
        jobs._dsn, jobs.schema, principal_provider=principal_provider,
        runtime_identity=jobs.runtime_identity)

    api_completion_ref = {}

    def authored_factory(*, job_store, farm_scenario_service, gate_key):
        api_author = FarmAuthoringService(farm_scenario_service)
        api_review = FarmAuthoredReviewService(api_author)
        api_completion = AuthoredReviewCompletionVerifier(api_review, execution)
        api_completion_ref['verifier'] = api_completion
        api_release = AuthoredReleaseStore(AuthoredReleaseVerifier(
            api_completion, ROOT,
            {'reviewer-key': ('separate synthetic reviewer', _public(reviewer))},
            lambda tenant, ref: artifacts.get(ref) if tenant == 'tenant-1' else None))
        return AuthoredRunStore(AuthoredRunPreparer(api_author, api_release), gate_key)

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
                'farm': {'scenario_id': 'farm-1', 'revision': 'r1',
                    'document': body},
                'workflow': {'review_uuid': REVIEW_BROWSER_UUID,
                    'run_uuid': RUN_BROWSER_UUID}}) + '\n')
            browser.stdin.flush()
            def browser_event(expected, *, queued_job=False):
                ready, _, _ = select.select([browser.stdout], [], [], 250)
                assert ready, f'browser did not report {expected}'
                line = browser.stdout.readline()
                if not line:
                    _, browser_error = browser.communicate(timeout=5)
                    pytest.fail(f'browser exited before {expected} '
                                f'(exit {browser.returncode}): '
                                + browser_error.replace(token.decode(), '<redacted>')[-2500:])
                value = json.loads(line)
                assert value['event'] == expected
                if not queued_job:
                    return value
                job_id = value['job_id']
                assert str(UUID(job_id)) == job_id
                assert jobs.get_job('tenant-1', job_id)['state'] == 'queued'
                return job_id

            registered = browser_event('farm_registered')
            registration = author.get('tenant-1', 'farm-1', 'r1')
            assert registration is not None
            assert registered['scenario_sha256'] == registration.scenario_sha256
            assert registration.registration_status == 'registered_unpublished_inputs'
            review_id = browser_event('review_admitted', queued_job=True)
            lease = jobs.claim(cli_worker.lease_seconds, allowed_stages=('collection_review',),
                               tenant_id='tenant-1', job_id=review_id)
            reviewed = cli_worker._run_claimed(lease)
            assert reviewed.state == 'succeeded'
            with jobs.connect() as conn:
                rows = {name: conn.execute(sql.SQL(
                    'SELECT * FROM {} WHERE tenant_id=%s AND job_id=%s').format(
                        jobs._table(name)), ('tenant-1', review_id)).fetchone()
                    for name in ('jobs', 'attempt_invocations', 'attempt_cli_launches',
                                 'attempt_cli_captures')}
            invocation = rows['attempt_invocations']
            assert (invocation['execution_kind'], invocation['model'],
                    invocation['reasoning_effort']) == ('codex_cli', 'gpt-6.1-sol', 'xhigh')
            record, raw, signature, _, _, _ = signed_execution(
                jobs, cli_worker, reviewed, rows, launch['argv'], private=observer,
                observed_hashes=(invocation['prompt_sha256'], invocation['schema_sha256'])
                    if real_cli else None)
            if real_cli:
                capture = rows['attempt_cli_captures']
                assert (capture['exit_code'], capture['termination_reason']) == (0, 'completed')
                assert capture['usage']['input_tokens'] > 0
                print('authored_full_cli_attempt=' + json.dumps({
                    'review_job_id': review_id, 'attempt': reviewed.attempt,
                    'decision_id': str(reviewed.decision_id),
                    'capture_id': str(reviewed.capture_id),
                    'observer_authority': 'synthetic_test_key',
                    'reviewer_authority': 'synthetic_test_key',
                    'cli_version': record.cli_version,
                    'model': invocation['model'],
                    'reasoning_effort': invocation['reasoning_effort'],
                    'executable_sha256': record.executable_sha256,
                    'environment_sha256': record.environment_sha256,
                    'jsonl_sha256': capture['jsonl_sha256'],
                    'final_output_sha256': capture['final_output_sha256'],
                    'usage': capture['usage']}, sort_keys=True))
            attestations.put(raw, signature)
            proof = completion.verify('tenant-1', review_id,
                                      registration.scenario_sha256)
            candidate = calculate_authored_candidate(author, 'tenant-1', 'farm-1', 'r1',
                                                     registration.scenario_sha256)
            assert candidate.candidate_id == proof.candidate_id
            assert candidate.trace_sha256 == proof.trace_sha256
            # A separate test covers changed rights and input. Pin these verified
            # immutable outputs during subsequent API composition.
            monkeypatch.setattr(completion, 'verify', lambda *_: proof)
            monkeypatch.setattr(api_completion_ref['verifier'], 'verify', lambda *_: proof)
            monkeypatch.setattr('app.farm_authored_run.calculate_authored_candidate',
                                lambda *_: candidate)
            signed = signed_release(release_verifier, proof, reviewer)
            release = release_store.put('tenant-1', review_id,
                                        registration.scenario_sha256, *signed)
            assert release.release_sha256 == release_store.get(
                'tenant-1', review_id, registration.scenario_sha256).release_sha256
            assert jobs.get_job('tenant-1', review_id)['state'] == 'succeeded'
            browser.stdin.write(json.dumps({'event': 'review_succeeded',
                'job_id': review_id}) + '\n')
            browser.stdin.flush()
            job_id = browser_event('run_admitted', queued_job=True)
            worker = AuthoredSimulationWorker(run_store, tenant_id='tenant-1')
            worked = worker.run_once(job_id)
            assert worked.state == 'succeeded'
            assert worker.run_once(job_id) is None
            run = run_store.get_run('tenant-1', worked.run_id)
            assert run['run_id'] == worked.run_id
            assert run['report']['review_job_id'] == proof.review_job_id
            assert run['report']['release_sha256'] == release.release_sha256
            traces = [json.loads(raw) for raw in run['trace_raws']]
            assert len(traces) == 2 and all(len(trace['steps']) == 60 for trace in traces)
            assert traces[0]['run_id'] == traces[1]['run_id'] == worked.run_id
            assert traces[0]['interval']['end_utc'] == traces[1]['interval']['start_utc']
            assert jobs.get_job('tenant-1', job_id)['state'] == 'succeeded'
            assert run_store.get_run('tenant-other', worked.run_id) is None
            _, series = project_authored_run(run)
            browser.stdin.write(json.dumps({'event': 'worker_succeeded',
                'job_id': job_id, 'run_id': worked.run_id,
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
