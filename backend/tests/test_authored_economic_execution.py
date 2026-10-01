"""Actual SCRAM authored parent/economic binding; all review keys are synthetic."""

from hashlib import sha256
import json
from pathlib import Path
import sys
from uuid import UUID

from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from psycopg import sql
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.api import create_app
from app.api_authored_thermal import read_authored_job_completion
from app.api_economic_calculation import ECONOMIC_REQUEST, EconomicCalculationService, EconomicCalculationHold
from app.authored_economic_execution import AUTHORED_ECONOMIC_SCOPES
from app.authored_thermal_candidate import calculate_authored_candidate
from app.calculation_assessment import CalculationAssessmentService
from app.cli_worker import CliWorker
from app.economic_calculation_worker import ECONOMIC_INPUT, EconomicCalculationWorker, CALCULATION_SCOPES
from app.execution_attestation import ExecutionAttestationStore
from app.execution_verifier import ExecutionVerifier
from app.farm_authored_release import AuthoredReleaseVerifier, KINDS
from app.farm_authored_release_store import AuthoredReleaseStore
from app.farm_authored_review import FarmAuthoredReviewService
from app.farm_authored_review_completion import AuthoredReviewCompletionVerifier, AuthoredReviewCompletionHold
from app.farm_authored_run import AuthoredRunPreparer
from app.farm_authored_run_store import AuthoredRunStore
from app.farm_authored_simulation import AuthoredSimulationService
from app.farm_authored_simulation_worker import AuthoredSimulationWorker
from app.jobs import canonical_input_bytes
from app.market_result_store import MarketResultStore
from app.owned_cli_contracts import OwnedCliContractRouter
from app.owned_collection_review import OwnedCollectionReviewService
from app.owned_fixture_collection import CollectionService
from test_cli_worker import _fake_cli
from test_execution_attestation import _signed as signed_execution
from test_farm_authored_release import _public, _signed as signed_release
from test_farm_authored_review import self_authored_evidence_policy
from test_farm_authoring_storage import authoring, request
from test_farm_replay_scenario import farm_setup, call
from test_economic_calculation_worker import result_count
from login_database import login_database, login_scope


ROOT = Path(__file__).resolve().parents[2]
PROFILE = {'market_calculation': True, 'market_source_storage': True,
    'thermal_scenario_storage': True, 'break_even_calculation': True,
    'authored_release_storage': True, 'authored_run_storage': True}
pytestmark = pytest.mark.parametrize('login_scope', [PROFILE], indirect=True)


@pytest.fixture
def authored_economic(authoring, login_scope, tmp_path, monkeypatch):
    author, document, principal = authoring
    principal['scopes'].update((*CALCULATION_SCOPES, *AUTHORED_ECONOMIC_SCOPES,
        'collection_review_create', 'authored_release_write', 'simulation_create',
        'authored_run_publish'))
    registration = author.submit('tenant-1', request(document))
    review = FarmAuthoredReviewService(author)
    jobs = author.replay.jobs
    jobs.artifact_root.mkdir(mode=0o700, exist_ok=True)
    results = MarketResultStore(jobs._dsn, jobs.schema, author.replay.candidates,
        principal_provider=jobs.principal_provider, runtime_identity=jobs.runtime_identity)
    runs = author.replay.thermal.runs
    assessment = CalculationAssessmentService(jobs, runs, results, author.replay.thermal, author.replay)
    owned_review = OwnedCollectionReviewService(CollectionService(jobs, author.replay.owned_research.registry), runs)
    router = OwnedCliContractRouter(author.replay.owned_research, owned_review, assessment, lambda *_: None, review)
    jobs.decision_validator, jobs.evidence_policy = router, self_authored_evidence_policy
    program = _fake_cli(tmp_path)
    program.write_text(program.read_text().replace(
        "['candidate-a'] if context['server_allows_proceed']",
        "[context['input']['candidate_ids'][0]] if context['server_allows_proceed']"))
    cli_home = tmp_path / 'synthetic-cli-home'
    cli_home.mkdir(mode=0o700)
    cli = CliWorker(jobs, router, cli_path=program, codex_home=cli_home,
        child_env={'CODEX_API_KEY': 'synthetic-test-key'}, timeout_seconds=10,
        lease_seconds=300, synthetic_smoke=True)
    launch = {}
    original_launch = jobs.record_cli_launch

    def capture_launch(*args, **kwargs):
        launch['argv'] = list(kwargs['argv'])
        return original_launch(*args, **kwargs)

    monkeypatch.setattr(jobs, 'record_cli_launch', capture_launch)
    review_job = review.submit('tenant-1', 'farm-1', 'r1', registration.scenario_sha256, 'review-money-parent')
    lease = jobs.claim(300, tenant_id='tenant-1', job_id=str(review_job['job_id']), allowed_stages=('collection_review',))
    reviewed = cli._run_claimed(lease)
    assert reviewed.state == 'succeeded', reviewed.reason_code
    with jobs.connect() as conn:
        rows = {name: conn.execute(sql.SQL('SELECT * FROM {} WHERE tenant_id=%s AND job_id=%s')
            .format(jobs._table(name)), ('tenant-1', review_job['job_id'])).fetchone()
            for name in ('jobs', 'attempt_invocations', 'attempt_cli_launches', 'attempt_cli_captures')}
    record, raw, signature, untrusted, _, _ = signed_execution(jobs, cli, reviewed, rows, launch['argv'])
    attestations = ExecutionAttestationStore(login_scope[0], untrusted.public_keys)
    attestations.put(raw, signature)
    execution = ExecutionVerifier(attestations, executable_sha256=record.executable_sha256,
        environment_sha256=record.environment_sha256)
    completed = AuthoredReviewCompletionVerifier(review, execution)
    proof = completed.verify('tenant-1', review_job['job_id'], registration.scenario_sha256)
    candidate = calculate_authored_candidate(author, 'tenant-1', 'farm-1', 'r1', registration.scenario_sha256)
    assert candidate.trace_sha256 == proof.trace_sha256
    # Freeze the initial synthetic review/candidate, while the new binding still
    # reads actual current authored registration, source rights and parent rows.
    monkeypatch.setattr(completed, 'verify', lambda *_: proof)
    monkeypatch.setattr('app.farm_authored_run.calculate_authored_candidate', lambda *_: candidate)
    reviewer = Ed25519PrivateKey.generate()
    artifacts = {f'evidence-{kind}': kind.encode() for kind in KINDS}
    verifier = AuthoredReleaseVerifier(completed, ROOT,
        {'reviewer-key': ('separate synthetic reviewer', _public(reviewer))}, lambda _, ref: artifacts.get(ref))
    releases = AuthoredReleaseStore(verifier)
    releases.put('tenant-1', proof.review_job_id, proof.registration_sha256, *signed_release(verifier, proof, reviewer))
    store = AuthoredRunStore(AuthoredRunPreparer(author, releases), b'synthetic-authored-money-' + b'x' * 32)
    job = AuthoredSimulationService(store.preparer, store).submit('tenant-1', proof.review_job_id,
        'farm-1', 'r1', registration.scenario_sha256, 'money-parent-run')
    outcome = AuthoredSimulationWorker(store, tenant_id='tenant-1').run_once(str(job['job_id']))
    assert outcome.state == 'succeeded', outcome.reason_code
    selected = document['farm']['economic']
    body = {'input_version': 'economic-calculation-input-v3', 'scenario_id': selected['scenario_id'],
        'scenario_revision': selected['revision'], 'scenario_sha256': selected['sha256'],
        'candidate_id': selected['candidate_id'], 'formula_version': 'economic-ledger-v9-sales-settlement',
        'authored_scenario_id': 'farm-1', 'authored_scenario_revision': 'r1',
        'registration_sha256': registration.scenario_sha256, 'thermal_job_id': str(job['job_id']),
        'idempotency_key': 'authored-money-one'}
    service = EconomicCalculationService(jobs, results, author.replay, store)
    app = create_app(jobs, author.replay.thermal.holds, runs, results,
        principal_provider=jobs.principal_provider, thermal_scenario_store=author.replay.thermal,
        farm_scenario_service=author.replay, economic_calculation_service=service, authored_run_store=store)
    return service, app, body, principal, author, completed, job


def money_worker(service, *, configured=True):
    return EconomicCalculationWorker(service.jobs, service.results, tenant_id='tenant-1',
        farm_scenario_service=service.farm_scenario_service,
        authored_run_store=service.authored_run_store if configured else None)


def test_authored_completed_parent_receipt_money_cash_and_current_rights(authored_economic, monkeypatch):
    service, app, body, principal, author, completed, parent = authored_economic
    for scope in AUTHORED_ECONOMIC_SCOPES:
        principal['scopes'].remove(scope)
        assert call(app, body, path='/v1/economic-results')[0] == 403
        principal['scopes'].add(scope)
    status, admitted = call(app, body, path='/v1/economic-results')
    assert status == 202 and admitted['state'] == 'queued'
    assert call(app, body, path='/v1/economic-results') == (status, admitted)
    legacy = {key: item for key, item in body.items() if key not in (
        'authored_scenario_id', 'authored_scenario_revision', 'registration_sha256', 'thermal_job_id')}
    legacy['input_version'] = 'economic-calculation-input-v1'
    assert call(app, legacy, path='/v1/economic-results')[0] == 409
    assert money_worker(service).run_once(admitted['job_id']).state == 'succeeded'
    assert result_count(service.results) == 1
    receipt = json.loads(service.jobs.read_artifact('tenant-1', admitted['job_id']))
    assert receipt['receipt_version'] == 'economic-calculation-result-v3'
    assert all(receipt[key] == body[key] for key in (
        'authored_scenario_id', 'authored_scenario_revision', 'registration_sha256', 'thermal_job_id'))
    thermal = read_authored_job_completion(service.jobs, service.authored_run_store, 'tenant-1', parent['job_id'])
    assert receipt['thermal_run_id'] == thermal.summary['run_id']
    assert receipt['thermal_receipt_sha256'] == sha256(canonical_input_bytes(thermal.receipt)).hexdigest()
    assert receipt['thermal_report_sha256'] == sha256(thermal.stored['report_raw']).hexdigest()
    assert receipt['numeric_input_sha256'] == sha256(author.read_registration('tenant-1', 'farm-1', 'r1',
        body['registration_sha256'])['numeric_input_bytes']).hexdigest()
    paths = [f"/v1/jobs/{admitted['job_id']}/{tail}" for tail in ('economic-result', 'economic-cash-flow')]
    result_status, result = call(app, path=paths[0])
    assert result_status == 200 and result['calculation_status'] == 'conditional_user_assumption'
    assert result['assessment_status'] == 'hold'
    assert not any(key in result for key in ('thermal_run_id', 'crop_growth', 'future_margin', 'rank'))
    assert call(app, path=paths[1])[0] == 200
    completion = service._read_job_completion('tenant-1', UUID(admitted['job_id']))
    assert completion.authored_completion is not None and completion.thermal_completion is None
    principal['scopes'].remove('authored_run_read')
    assert all(call(app, path=path)[0] == 403 for path in paths)
    principal['scopes'].add('authored_run_read')
    with monkeypatch.context() as patch:
        patch.setattr(author.replay.candidates._source._source, 'get_input_rights', lambda *_: None)
        assert all(call(app, path=path)[0] == 503 for path in paths)
        assert call(app, body, path='/v1/economic-results')[0] == 422
    with monkeypatch.context() as patch:
        def revoked(*_):
            raise AuthoredReviewCompletionHold('synthetic review revoked')
        patch.setattr(completed, 'verify', revoked)
        assert all(call(app, path=path)[0] == 503 for path in paths)
    assert call(app, path=paths[0])[0] == 200


def test_mixed_uncompleted_foreign_or_missing_authority_cannot_calculate(authored_economic):
    service, app, body, principal, _, _, parent = authored_economic
    for change in ({'registration_sha256': 'f' * 64}, {'authored_scenario_revision': 'r2'},
            {'authored_scenario_id': 'other-farm'}, {'candidate_id': 'e' * 64},
            {'thermal_job_id': '11111111-1111-4111-8111-111111111111'}):
        assert call(app, body | change, path='/v1/economic-results')[0] == 422
    with service.jobs.connect() as conn:
        row = service.jobs._locked_job(conn, 'tenant-1', parent['job_id'])
        parent_input = json.loads(service.jobs._verified_input(row))
    pending = service.jobs.submit('tenant-1', 'simulation', parent_input, 'pending-authored-money-parent')
    assert call(app, body | {'thermal_job_id': str(pending['job_id'])}, path='/v1/economic-results')[0] == 422
    principal['tenant_id'] = 'foreign-tenant'
    assert call(app, body, path='/v1/economic-results')[0] == 422
    principal['tenant_id'] = 'tenant-1'
    with pytest.raises(EconomicCalculationHold):
        EconomicCalculationService(service.jobs, service.results, service.farm_scenario_service).submit(
            'tenant-1', ECONOMIC_REQUEST.validate_python(body))
    raw = ECONOMIC_INPUT.validate_python({key: item for key, item in body.items() if key != 'idempotency_key'})
    intent = service.jobs.submit('tenant-1', 'simulation', raw.model_dump(mode='json'), 'missing-authored-authority')
    outcome = money_worker(service, configured=False).run_once(str(intent['job_id']))
    assert (outcome.state, outcome.reason_code) == ('hold', 'economic_authored_run_hold')
    assert service.jobs.get_publication('tenant-1', intent['job_id']) is None
    assert result_count(service.results) == 0


def test_late_scope_and_binding_changes_roll_back_intent_and_publication(authored_economic, monkeypatch):
    service, _, body, principal, author, _, _ = authored_economic
    admitted_ids = []
    original_event = service.jobs._event
    def revoke_admission(conn, tenant, job_id, kind, *args, **kwargs):
        original_event(conn, tenant, job_id, kind, *args, **kwargs)
        if kind == 'submitted':
            admitted_ids.append(job_id)
            principal['scopes'].remove('authored_run_read')
    with monkeypatch.context() as patch:
        patch.setattr(service.jobs, '_event', revoke_admission)
        with pytest.raises(PermissionError):
            service.submit('tenant-1', ECONOMIC_REQUEST.validate_python(body))
    principal['scopes'].add('authored_run_read')
    assert len(admitted_ids) == 1 and service.jobs.get_job('tenant-1', admitted_ids[0]) is None
    with service.jobs.connect() as conn:
        assert conn.execute(sql.SQL('SELECT count(*) AS n FROM {} WHERE job_id=%s')
            .format(service.jobs._table('job_events')), (admitted_ids[0],)).fetchone()['n'] == 0
    original_pin = service.results._pin_in_transaction
    for mutation in ('scope', 'binding'):
        intent = service.submit('tenant-1', ECONOMIC_REQUEST.validate_python(body | {'idempotency_key': mutation}))
        with monkeypatch.context() as patch:
            original_read = author.read_registration
            def changed(*args):
                registered = original_read(*args)
                return {**registered, 'numeric_input_bytes': registered['numeric_input_bytes'] + b' '}
            def revoke_after_insert(*args, **kwargs):
                stored = original_pin(*args, **kwargs)
                if mutation == 'scope':
                    principal['scopes'].remove('authored_run_read')
                else:
                    patch.setattr(author, 'read_registration', changed)
                return stored
            patch.setattr(service.results, '_pin_in_transaction', revoke_after_insert)
            outcome = money_worker(service).run_once(str(intent['job_id']))
        principal['scopes'].add('authored_run_read')
        assert outcome.state == 'hold', outcome.reason_code
        assert result_count(service.results) == 0
        assert service.jobs.get_publication('tenant-1', intent['job_id']) is None
