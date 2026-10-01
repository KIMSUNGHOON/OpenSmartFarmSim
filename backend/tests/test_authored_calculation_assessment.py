"""Stored authored parents and shared fake CLI; no independent G1 evidence."""

from copy import copy
from datetime import timedelta
from hashlib import sha256
import json
from pathlib import Path
import sys

from psycopg import sql
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.api import create_app
from app.api_economic_calculation import ECONOMIC_REQUEST
from app.authored_calculation_assessment import AUTHORED_FIELDS, AUTHORED_INPUT_VERSION
from app.authored_economic_execution import AUTHORED_ECONOMIC_SCOPES
from app.calculation_assessment import (CalculationAssessmentService, CalculationAssessmentContract,
    AuthoredCalculationAssessmentContract, CalculationAssessmentHold, ADMISSION_SCOPES)
from app.cli_contracts import ProposalHold
from app.cli_worker import CliWorker
from app.jobs import canonical_input_bytes
from app.owned_cli_contracts import OwnedCliContractRouter
from app.owned_collection_review import INPUT_VERSION as REVIEW_INPUT_VERSION
from test_authored_economic_execution import (authored_economic, money_worker, authoring,
    farm_setup, login_database, login_scope, PROFILE)
from test_calculation_assessment import assessment_count
from test_cli_worker import _fake_cli
from test_farm_replay_scenario import call


pytestmark = pytest.mark.parametrize('login_scope', [PROFILE], indirect=True)


@pytest.fixture
def authored_pair(authored_economic):
    economic, _, body, principal, author, completion, thermal = authored_economic
    principal['scopes'].update((*ADMISSION_SCOPES, 'auditor'))
    admitted = economic.submit('tenant-1', ECONOMIC_REQUEST.validate_python(body))
    outcome = money_worker(economic).run_once(str(admitted['job_id']))
    assert outcome.state == 'succeeded', outcome.reason_code
    service = CalculationAssessmentService(economic.jobs, author.replay.thermal.runs, economic.results,
        author.replay.thermal, author.replay, economic.authored_run_store)
    app = create_app(service.jobs, author.replay.thermal.holds, service.runs, service.results,
        principal_provider=service.jobs.principal_provider, thermal_scenario_store=service.scenario_store,
        farm_scenario_service=service.farm_scenario_service, authored_run_store=service.authored_run_store,
        assessment_service=service)
    intent = {'run_job_id': str(thermal['job_id']), 'economic_job_id': str(admitted['job_id']),
        'idempotency_key': 'authored-assessment-one'}
    return service, app, intent, principal, economic, completion


def full_job(jobs, job_id):
    with jobs.connect() as conn:
        row = jobs._locked_job(conn, 'tenant-1', job_id)
        jobs._verified_input(row)
        return row


def assessment_cli(service, tmp_path):
    original = service.jobs.decision_validator
    router = OwnedCliContractRouter(original.research, original.reviews, service,
        original._routes[('collection_review', REVIEW_INPUT_VERSION)].authority_resolver,
        original.authored_review)
    service.jobs.decision_validator = router
    directory = tmp_path / 'assessment-cli'
    directory.mkdir(mode=0o700)
    program = _fake_cli(directory)
    cli_home = directory / 'home'
    cli_home.mkdir(mode=0o700)
    cli = CliWorker(service.jobs, router, cli_path=program, codex_home=cli_home,
        child_env={'CODEX_API_KEY': 'synthetic-test-key'}, timeout_seconds=10,
        lease_seconds=300, synthetic_smoke=True)
    return cli, router


def test_authored_pair_pins_distinct_validator_and_shared_cli_hold(authored_pair, tmp_path):
    service, app, intent, principal, _, _ = authored_pair
    for scope in AUTHORED_ECONOMIC_SCOPES:
        principal['scopes'].remove(scope)
        assert call(app, intent, path='/v1/assessments')[0] == 403
        principal['scopes'].add(scope)
    status, admitted = call(app, intent, path='/v1/assessments')
    assert status == 202 and admitted['state'] == 'queued'
    assert call(app, intent, path='/v1/assessments') == (status, admitted)
    job = full_job(service.jobs, admitted['job_id'])
    value = json.loads(job['input_bytes'])
    assert value['input_version'] == AUTHORED_INPUT_VERSION
    receipt = json.loads(service.jobs.read_artifact('tenant-1', intent['economic_job_id']))
    assert all(value[key] == receipt[key] for key in AUTHORED_FIELDS)
    assert value['run_id'] == receipt['thermal_run_id']
    assert value['thermal_input_sha256'] == receipt['thermal_input_sha256']
    assert value['thermal_receipt_sha256'] == receipt['thermal_receipt_sha256']
    assert value['thermal_report_sha256'] == receipt['thermal_report_sha256']
    assert value['candidate_ids'] == value['evidence_refs'] == []
    contract = AuthoredCalculationAssessmentContract(service)
    with pytest.raises(ProposalHold):
        CalculationAssessmentContract(service).input_context(job)
    for key in ('registration_sha256', 'authored_bindings_sha256', 'numeric_input_sha256', 'release_sha256'):
        raw = canonical_input_bytes(value | {key: '0' * 64})
        with pytest.raises(ProposalHold):
            contract.input_context(job | {'input_bytes': raw, 'input_sha256': sha256(raw).hexdigest()})
    with pytest.raises(ProposalHold):
        contract.input_context(job | {'created_at': job['created_at'] - timedelta(hours=1)})
    output = {'schema_version': 'decision_v1', 'stage': 'assessment', 'input_sha256': job['input_sha256'],
        'proposed_status': 'hold', 'selected_ids': [], 'rejected_ids': [], 'claims': [],
        'missing_evidence': list(service.MISSING_EVIDENCE), 'reason': 'Synthetic parents lack independent evidence.',
        **{key: value[key] for key in ('decision_context_id', 'decision_at_utc', 'claim_mode', 'decision_time_kind')}}
    assert contract.plan(job, canonical_input_bytes(output)).disposition == 'hold'
    for mutation in ({'proposed_status': 'proceed'}, {'selected_ids': ['invented-crop']},
            {'missing_evidence': []}, {'claims': [{'claim': 'future margin verified',
                'evidence_ids': ['invented'], 'uncertainty': 'none'}]}):
        with pytest.raises(ProposalHold):
            contract.plan(job, canonical_input_bytes(output | mutation))
    cli, router = assessment_cli(service, tmp_path)
    lease = service.jobs.claim(300, tenant_id='tenant-1', job_id=admitted['job_id'], allowed_stages=('assessment',))
    outcome = cli._run_claimed(lease)
    assert outcome.state == 'hold' and outcome.decision_id, outcome.reason_code
    report = json.loads(service.jobs.read_hold_report('tenant-1', admitted['job_id']))
    assert report['missing_evidence'] == list(service.MISSING_EVIDENCE)
    decision = service.jobs.list_decisions('tenant-1', admitted['job_id'])[0]
    evidence = json.loads(service.jobs.read_evidence('tenant-1', admitted['job_id'], decision['validation_evidence_id']))
    assert evidence['passed'] is True and evidence['validator_version'] == contract.VERSION
    assert router._routes[('assessment', AUTHORED_INPUT_VERSION)].VERSION == contract.VERSION
    assert service.jobs.get_publication('tenant-1', admitted['job_id']) is None
    status, public = call(app, path=f"/v1/jobs/{admitted['job_id']}/hold-report")
    assert status == 200 and public['missing_evidence_count'] == 6
    assert not any(key in public for key in ('registration_sha256', 'run_id', 'release_sha256', 'point'))
    assert call(app, intent, path='/v1/assessments')[1]['state'] == 'hold'


def test_authored_pair_rejects_mixed_pending_foreign_and_missing_store(authored_pair):
    service, app, intent, principal, economic, _ = authored_pair
    for left, right in ((intent['economic_job_id'], intent['run_job_id']),
            (intent['run_job_id'], intent['run_job_id']),
            ('11111111-1111-4111-8111-111111111111', intent['economic_job_id'])):
        assert call(app, intent | {'run_job_id': left, 'economic_job_id': right}, path='/v1/assessments')[0] == 422
    for field in ('run_job_id', 'economic_job_id'):
        row = full_job(service.jobs, intent[field])
        pending = service.jobs.submit('tenant-1', 'simulation', json.loads(row['input_bytes']), 'pending-' + field)
        assert call(app, intent | {field: str(pending['job_id'])}, path='/v1/assessments')[0] == 422
    principal['tenant_id'] = 'other-tenant'
    assert call(app, intent, path='/v1/assessments')[0] == 422
    principal['tenant_id'] = 'tenant-1'
    unconfigured = CalculationAssessmentService(service.jobs, service.runs, service.results,
        service.scenario_store, service.farm_scenario_service)
    with pytest.raises(CalculationAssessmentHold):
        unconfigured.submit('tenant-1', intent['run_job_id'], intent['economic_job_id'], 'missing-authored-store')
    with pytest.raises(ValueError):
        create_app(service.jobs, service.scenario_store.holds, service.runs, service.results,
            principal_provider=service.jobs.principal_provider, thermal_scenario_store=service.scenario_store,
            farm_scenario_service=service.farm_scenario_service, authored_run_store=copy(service.authored_run_store),
            assessment_service=service)
    raw = json.loads(full_job(service.jobs, intent['economic_job_id'])['input_bytes'])
    for key in ('authored_scenario_id', 'authored_scenario_revision', 'registration_sha256', 'thermal_job_id'):
        raw.pop(key)
    raw['input_version'] = 'economic-calculation-input-v1'
    generic = service.jobs.submit('tenant-1', 'simulation', raw, 'generic-money-for-mixed-assessment')
    assert money_worker(economic).run_once(str(generic['job_id'])).state == 'succeeded'
    assert call(app, intent | {'economic_job_id': str(generic['job_id'])}, path='/v1/assessments')[0] == 422
    assert assessment_count(service) == 0


def test_authored_assessment_commit_rechecks_scope_store_rights_and_pins(authored_pair, monkeypatch):
    service, _, intent, principal, _, _ = authored_pair
    original_event = service.jobs._event
    original_store = service.authored_run_store
    source = service.results._candidates._source._source
    submitted = []
    for mutation in ('scope', 'store', 'rights'):
        def event(conn, tenant, job_id, kind, *args, **kwargs):
            original_event(conn, tenant, job_id, kind, *args, **kwargs)
            if kind == 'submitted':
                submitted.append(job_id)
                if mutation == 'scope':
                    principal['scopes'].remove('authored_run_read')
                elif mutation == 'store':
                    service.authored_run_store = None
                else:
                    patch.setattr(source, 'get_input_rights', lambda *_: None)
        try:
            with monkeypatch.context() as patch:
                patch.setattr(service.jobs, '_event', event)
                with pytest.raises((PermissionError, RuntimeError, CalculationAssessmentHold)):
                    service.submit('tenant-1', intent['run_job_id'], intent['economic_job_id'], 'late-' + mutation)
        finally:
            principal['scopes'].add('authored_run_read')
            service.authored_run_store = original_store
    original_prepare = service.prepare
    calls = []
    def changed(*args, **kwargs):
        value, recorded = original_prepare(*args, **kwargs)
        calls.append(1)
        if len(calls) == 2:
            value = value | {'numeric_input_sha256': '0' * 64}
        return value, recorded
    with monkeypatch.context() as patch:
        patch.setattr(service, 'prepare', changed)
        with pytest.raises(CalculationAssessmentHold):
            service.submit('tenant-1', intent['run_job_id'], intent['economic_job_id'], 'late-pins')
    assert len(calls) == 2 and len(submitted) == 3 and assessment_count(service) == 0
    for job_id in submitted:
        assert service.jobs.get_job('tenant-1', job_id) is None
        with service.jobs.connect() as conn:
            assert conn.execute(sql.SQL('SELECT count(*) AS n FROM {} WHERE job_id=%s')
                .format(service.jobs._table('job_events')), (job_id,)).fetchone()['n'] == 0
