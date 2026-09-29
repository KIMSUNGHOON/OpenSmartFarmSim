"""Joined completion checks over SCRAM; fixture keys and fake CLI prove no G1."""

from hashlib import sha256
import asyncio
from datetime import timedelta
import json
from pathlib import Path
import sys

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from app.calculation_assessment import CalculationAssessmentService, CalculationAssessmentContract
from app.cli_worker import CliWorker
from app.jobs import canonical_input_bytes
from app.cli_contracts import ProposalHold
from app.calculation_assessment import ADMISSION_SCOPES, INPUT_VERSION, CalculationAssessmentHold
from app.api import create_app
from test_http_identity import request as http_request
from test_api_serve import tls_files
from app.thermal_simulation_worker import ThermalSimulationWorker
from test_api_economic_scenario import economic_api
from test_economic_calculation_worker import calculation_setup
from test_market_source_store import PROFILE
from test_market_hold_store import context_verifier
from test_thermal_publisher import setup as publisher_fixture, input_raws
from test_cli_worker import _fake_cli
from login_database import login_database, login_scope

pytestmark = pytest.mark.parametrize('login_scope', [{**PROFILE, 'break_even_calculation':True}], indirect=True)


@pytest.fixture
def assessment_setup(login_scope, request, monkeypatch):
    import test_market_signed_hold_integration as market_seed
    monkeypatch.setattr(market_seed, 'SNAPSHOT_RAWS', input_raws())
    assembled = economic_api.__wrapped__(login_scope)
    worker, jobs, results, economic_job, _, principal = calculation_setup.__wrapped__(assembled)
    holds = results._candidates._source._holds
    def existing_context(runs, snapshot_id, **_):
        return runs.get_decision_context('tenant-1', snapshot_id, 'context-1')
    publisher, runs, captured, review, snapshot_id, *_ = publisher_fixture.__wrapped__(
        login_scope[0], request, schema_installed=True, tenant='tenant-1',
        context_factory=existing_context, context_verifier=context_verifier)
    runs.runtime_identity = jobs.runtime_identity
    runs.dsn = jobs._dsn
    runs._principal_provider = jobs.principal_provider
    holds._context_store = runs
    principal['scopes'].update({'thermal_snapshot_read', 'thermal_run_read', 'thermal_run_publish',
                               'assessment_create', 'auditor'})
    jobs.decision_validator = captured.decision_validator
    jobs.evidence_policy = captured.evidence_policy
    publisher.job_store = jobs
    thermal_job = jobs.submit('tenant-1', 'simulation', {'input_version':'thermal-simulation-input-v1',
        'snapshot_id':snapshot_id, 'review_job_id':str(review['job_id'])}, 'assessment-thermal')
    assert ThermalSimulationWorker(publisher, tenant_id='tenant-1').run_once(str(thermal_job['job_id'])).state == 'succeeded'
    assert worker.run_once(str(economic_job['job_id'])).state == 'succeeded'
    service = CalculationAssessmentService(jobs, runs, results)
    return service, str(thermal_job['job_id']), str(economic_job['job_id']), principal


def application(service):
    return create_app(service.jobs, service.results._candidates._source._holds, service.runs,
        service.results, principal_provider=service.jobs.principal_provider, assessment_service=service)


def call(app, body, *, raw=None, media=b'application/json', path='/v1/assessments', method='POST'):
    return asyncio.run(http_request(app, path=path, method=method,
        headers=[(b'content-type',media),(b'x-tenant-id',b'foreign')],
        body=json.dumps(body).encode() if raw is None else raw))[:2]


def assessment_count(service):
    from psycopg import sql
    with service.jobs.connect() as conn:
        return conn.execute(sql.SQL("SELECT count(*) AS n FROM {} WHERE stage='assessment'")
            .format(service.jobs._table('jobs'))).fetchone()['n']


def test_completed_calculations_are_pinned_and_fake_cli_retains_hold(assessment_setup, tmp_path):
    service, thermal_job, economic_job, _ = assessment_setup
    app = application(service)
    body = dict(run_job_id=thermal_job, economic_job_id=economic_job, idempotency_key='assessment')
    status, accepted = call(app, body)
    assert status == 202 and accepted['stage'] == 'assessment' and accepted['state'] == 'queued'
    job = service.jobs.get_job('tenant-1', accepted['job_id'])
    assert service.submit('tenant-1', thermal_job, economic_job, 'assessment')['job_id'] == job['job_id']
    with service.jobs.connect() as conn:
        full = service.jobs._locked_job(conn, 'tenant-1', job['job_id'])
    value = json.loads(full['input_bytes'])
    assert value['candidate_ids'] == value['evidence_refs'] == []
    assert value['temporal_provenance'] == 'ex_post_replay' and 'profile_id' not in value
    assert value['run_id'] and value['economic_result_id'] and value['context_sha256']
    contract = CalculationAssessmentContract(service)
    service.jobs.decision_validator = contract
    program = _fake_cli(tmp_path)
    home = tmp_path/'assessment-home'; home.mkdir(mode=0o700)
    cli = CliWorker(service.jobs, contract, cli_path=program, codex_home=home,
        child_env={'CODEX_API_KEY':'synthetic-test-key'}, timeout_seconds=10,
        lease_seconds=300, synthetic_smoke=True)
    result = cli.run_once()
    assert result.job_id == job['job_id'] and result.state == 'hold' and result.decision_id
    report = json.loads(service.jobs.read_hold_report('tenant-1', job['job_id']))
    assert report['missing_evidence'] == list(service.MISSING_EVIDENCE)
    assert service.jobs.get_publication('tenant-1', job['job_id']) is None
    stored = service.jobs.list_decisions('tenant-1', job['job_id'])[0]
    checked = json.loads(service.jobs.read_evidence('tenant-1', job['job_id'], stored['validation_evidence_id']))
    assert checked['passed'] is True and checked['validator_version'] == contract.VERSION
    status, public = call(app, {}, path=f"/v1/jobs/{job['job_id']}/hold-report", method='GET')
    assert status == 200 and public['missing_evidence'] == list(service.MISSING_EVIDENCE)
    assert public['missing_evidence_count'] == 6 and 'context_sha256' not in public
    assert call(app, body)[1]['state'] == 'hold'


def test_http_rejects_missing_authority_and_invalid_bodies_before_admission(assessment_setup, monkeypatch):
    service, thermal, economic, principal = assessment_setup
    app = application(service)
    body = dict(run_job_id=thermal, economic_job_id=economic, idempotency_key='invalid-http')
    for scope in ADMISSION_SCOPES:
        principal['scopes'].remove(scope)
        assert call(app, body, raw=b'{')[0] == 403
        principal['scopes'].add(scope)
    principal['authenticated'] = False
    assert call(app, body, raw=b'{')[0] == 401
    principal['authenticated'] = True
    for change in ({'tenant_id':'foreign'}, {'run_id':'invented'}, {'claims':[]},
                   {'run_job_id':'unknown'}, {'economic_job_id':thermal.upper()}, {'idempotency_key':'한글'}):
        assert call(app, body|change)[0] == 422
    assert call(app, body, raw=b'{"run_job_id":"a","run_job_id":"b"}')[0] == 422
    assert call(app, body, media=b'text/plain')[0] == 415
    assert call(app, body, raw=b' '*4097)[0] == 413
    unconfigured = create_app(service.jobs, service.results._candidates._source._holds,
        service.runs, service.results, principal_provider=service.jobs.principal_provider)
    assert call(unconfigured, body)[0] == 503 and assessment_count(service) == 0
    key = INPUT_VERSION+':'+sha256(body['idempotency_key'].encode()).hexdigest()
    service.jobs.submit('tenant-1','assessment',{'synthetic':'another-intent'},key)
    assert call(app,body)[0] == 409 and assessment_count(service) == 1
    def private_failure(*_):
        raise RuntimeError('synthetic private assessment backend detail')
    monkeypatch.setattr(service,'submit',private_failure)
    status,error = call(app,body)
    assert status == 503 and 'synthetic private' not in json.dumps(error)
    assert assessment_count(service) == 1


def test_incomplete_foreign_or_incompatible_calculations_are_not_admitted(assessment_setup, monkeypatch):
    service, thermal, economic, principal = assessment_setup
    for left,right in ((economic,thermal), (thermal,thermal),
                       ('00000000-0000-0000-0000-000000000000',economic)):
        with pytest.raises(CalculationAssessmentHold): service.submit('tenant-1',left,right,'missing')
    principal['tenant_id'] = 'tenant-2'
    with pytest.raises(CalculationAssessmentHold): service.submit('tenant-2',thermal,economic,'foreign')
    principal['tenant_id'] = 'tenant-1'
    holds = service.results._candidates._source._holds
    original = holds.get_market_hold_report
    monkeypatch.setattr(holds,'get_market_hold_report', lambda identifier:
        original(identifier)|{'decision_context_id':'another-context'})
    with pytest.raises(CalculationAssessmentHold): service.submit('tenant-1',thermal,economic,'context')
    assert assessment_count(service) == 0


def test_commit_guard_rolls_back_revoked_scope_and_changed_store(assessment_setup, monkeypatch):
    service, thermal, economic, principal = assessment_setup
    original = service.jobs._event
    verifier = service.runs._context_verifier
    def revoke(*args, **kwargs):
        original(*args, **kwargs)
        principal['scopes'].remove('assessment_create')
    monkeypatch.setattr(service.jobs, '_event', revoke)
    with pytest.raises(PermissionError): service.submit('tenant-1',thermal,economic,'revoke')
    assert assessment_count(service) == 0
    principal['scopes'].add('assessment_create')
    def replace(*args, **kwargs):
        original(*args, **kwargs)
        service.runs._context_verifier = lambda *_: None
    monkeypatch.setattr(service.jobs, '_event', replace)
    with pytest.raises(RuntimeError): service.submit('tenant-1',thermal,economic,'replace')
    service.runs._context_verifier = verifier
    assert assessment_count(service) == 0


def test_forged_pins_chronology_and_cli_claims_cannot_be_approved(assessment_setup):
    service, thermal, economic, _ = assessment_setup
    submitted = service.submit('tenant-1',thermal,economic,'forged')
    with service.jobs.connect() as conn:
        job = service.jobs._locked_job(conn,'tenant-1',submitted['job_id'])
    value = json.loads(job['input_bytes'])
    contract = CalculationAssessmentContract(service)
    for key in ('run_id','economic_result_id','thermal_report_sha256','economic_result_sha256',
                'context_sha256','market_hold_report_id','temporal_provenance'):
        raw = canonical_input_bytes(value|{key:'forged'})
        with pytest.raises(ProposalHold):
            contract.input_context(job|{'input_bytes':raw,'input_sha256':sha256(raw).hexdigest()})
    with pytest.raises(ProposalHold):
        contract.input_context(job|{'created_at':job['created_at']-timedelta(hours=1)})
    output = {'schema_version':'decision_v1','stage':'assessment','input_sha256':job['input_sha256'],
        'proposed_status':'hold','selected_ids':[],'rejected_ids':[], 'claims':[],
        'missing_evidence':list(service.MISSING_EVIDENCE),'reason':'Synthetic calculations lack validation.',
        **{key:value[key] for key in ('decision_context_id','decision_at_utc','claim_mode','decision_time_kind')}}
    assert contract.plan(job,canonical_input_bytes(output)).disposition == 'hold'
    for change in ({'proposed_status':'proceed'}, {'selected_ids':['invented-crop']},
                   {'missing_evidence':[]}, {'claims':[{'claim':'future margin verified',
                    'evidence_ids':['invented'],'uncertainty':'none'}]}):
        with pytest.raises(ProposalHold): contract.plan(job,canonical_input_bytes(output|change))


def test_fresh_authenticated_runtime_admits_using_actual_shared_stores(assessment_setup, tls_files):
    from datetime import datetime, timezone
    from app.api_runtime import ApiRuntime
    from app.http_identity import BearerRegistry, BearerGrant, token_digest, current_principal
    from app.market_source_store import MarketSourceStore
    from test_api_runtime import config, dependencies
    service, thermal, economic, _ = assessment_setup
    token = b'synthetic-assessment-token-'+b'a'*32
    now = datetime.now(timezone.utc)
    registry = BearerRegistry((BearerGrant(token_digest(token),'tenant-1',frozenset(ADMISSION_SCOPES),
        now-timedelta(seconds=1),now+timedelta(minutes=30)),))
    cert,key,_ = tls_files
    holds = service.results._candidates._source._holds
    factory = lambda *,principal_provider: MarketSourceStore(service.jobs._dsn,service.jobs.schema,
        principal_provider=principal_provider,runtime_identity=service.jobs.runtime_identity)
    runtime = ApiRuntime(config(policy=service.jobs.runtime_identity[0],dsn=service.jobs._dsn,
        artifact_root=service.jobs.artifact_root,certificate=cert,private_key=key,
        thermal_gate_key=service.runs._gate_key), dependencies(bearer_registry=registry,
            market_source_factory=factory,market_scope_resolver=holds._scope_resolver,
            release_verifier=service.runs._release_verifier))
    body = dict(run_job_id=thermal,economic_job_id=economic,idempotency_key='runtime')
    status,accepted,_ = asyncio.run(http_request(runtime.service.app,path='/v1/assessments',method='POST',
        headers=[(b'authorization',b'Bearer '+token),(b'content-type',b'application/json')],
        body=json.dumps(body).encode()))
    assert status == 202 and accepted['stage'] == 'assessment' and current_principal() is None
    assert runtime.assessments.jobs is runtime.jobs and runtime.assessments.runs is runtime.thermal
    assert runtime.assessments.results is runtime.market_results
    assert asyncio.run(http_request(runtime.service.app,path='/v1/assessments',method='POST'))[0] == 401
