"""Actual SCRAM and owned lineage; fake CLI/release keys prove software only."""

from hashlib import sha256
import json
from pathlib import Path
import sys
from uuid import UUID

import pytest
from psycopg import sql

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from app.api import create_app
from app.api_job_run import read_job_run
from app.calculation_assessment import CalculationAssessmentService
from app.cli_contracts import AuthoritySnapshot
from app.cli_worker import CliWorker
from app.farm_replay_scenario import FarmReplayScenarioService, READ_SCOPES
from app.farm_thermal_execution import FarmThermalHold
from app.jobs import canonical_input_bytes
from app.market_result_store import MarketResultStore
from app.orchestration import LocationRequest
from app.owned_cli_contracts import OwnedCliContractRouter
from app.owned_collection_review import OwnedCollectionReviewService, OwnedCollectionReviewContract, REVIEW_SCOPES
from app.owned_fixture_collection import CollectionService, CollectionWorker
from app.owned_fixture_registry import OwnedFixtureRegistry
from app.owned_research import OwnedResearchService, ADMISSION_SCOPES as OWNED_SCOPES
from app.thermal_publisher import ThermalG1Publisher
from app.thermal_simulation_worker import ThermalSimulationWorker, SIMULATION_INPUT
from app.thermal_run_submission import ThermalRunSubmissionService, RUN_REQUEST, SUBMISSION_SCOPES, FARM_SUBMISSION_SCOPES
from test_farm_replay_scenario import farm_setup, model, call, login_scope, login_database
from test_thermal_publisher import setup as publisher_setup, GATE_KEY
from test_job_evidence import cli_store
from test_cli_worker import _fake_cli

pytestmark=pytest.mark.parametrize('login_scope',[{'market_calculation':True,
    'market_source_storage':True,'thermal_scenario_storage':True,'break_even_calculation':True}],indirect=True)


@pytest.fixture
def execution(farm_setup,login_scope,request,tmp_path):
    previous,body,principal=farm_setup
    jobs,runs=previous.jobs,previous.thermal.runs
    principal['scopes'].update((*OWNED_SCOPES,*REVIEW_SCOPES,*SUBMISSION_SCOPES,
        'cancel','collection_execute','simulation_execute','thermal_run_read','thermal_run_publish','auditor'))
    assert jobs.cancel('tenant-1',UUID(body['research_job_id']))
    context=runs.get_decision_context('tenant-1',previous._references('tenant-1',model(body))['snapshot_id'],'context-1')
    seeded=publisher_setup.__wrapped__(login_scope[0],request,schema_installed=True,tenant='tenant-1',
        context_factory=lambda *_args,**_kwargs:context,context_verifier=runs._context_verifier)
    seed=seeded[0]
    runs._gate_key=GATE_KEY
    runs._release_verifier=seed.release_verifier
    registry=OwnedFixtureRegistry(Path(__file__).resolve().parents[2])
    research=OwnedResearchService(jobs,runs,previous.registry,registry,
        {next(iter(previous.registry._scopes)):'context-1'})
    collection=CollectionService(jobs,registry)
    review=OwnedCollectionReviewService(collection,runs)
    results=MarketResultStore(jobs._dsn,jobs.schema,previous.candidates,
        principal_provider=jobs.principal_provider,runtime_identity=jobs.runtime_identity)
    assessment=CalculationAssessmentService(jobs,runs,results,previous.thermal)
    def authority(job,value):
        return AuthoritySnapshot(job['tenant_id'],'collection_review',job['input_sha256'],
            frozenset({value['snapshot_id']}),{},True,(),{},frozenset(),False,
            {key:value[key] for key in OwnedCollectionReviewContract.BINDING_FIELDS},
            **{key:value[key] for key in ('decision_context_id','decision_at_utc','claim_mode','decision_time_kind')})
    router=OwnedCliContractRouter(research,review,assessment,authority)
    jobs.evidence_policy=cli_store(login_scope[0]).evidence_policy
    jobs.decision_validator=router
    program=_fake_cli(tmp_path)
    program.write_text(program.read_text().replace("['candidate-a'] if context['server_allows_proceed']",
        "[context['input']['candidate_ids'][0]] if context['server_allows_proceed']"))
    home=tmp_path/'farm-cli-home';home.mkdir(mode=0o700)
    cli=CliWorker(jobs,router,cli_path=program,codex_home=home,
        child_env={'CODEX_API_KEY':'synthetic-test-key'},timeout_seconds=10,lease_seconds=300,synthetic_smoke=True)
    scope=next(iter(previous.registry._scopes.values()))
    location=LocationRequest(latitude=35.0,longitude=127.0,
        period_start_utc=scope.period_start_utc,period_end_utc=scope.period_end_utc,
        goal_id='historical-thermal-replay',idempotency_key='farm-owned-root')
    _,_,root=research.submit('tenant-1',location)
    assert cli.run_once().state=='succeeded'
    collected=collection.submit('tenant-1',str(root['job_id']),'farm-owned-collection')
    assert CollectionWorker(collection,tenant_id='tenant-1').run_once(str(collected['job_id'])).state=='succeeded'
    reviewed=review.submit('tenant-1',str(collected['job_id']),'farm-owned-review')
    assert cli.run_once().state=='succeeded'
    farm=FarmReplayScenarioService(jobs,previous.thermal,previous.candidates,previous.registry,research)
    selected=farm.submit('tenant-1',model(body|{'research_job_id':str(root['job_id'])}))
    publisher=ThermalG1Publisher(runs,jobs,seed.release_resolver,root=seed.root,gate_key=GATE_KEY,
        release_verifier=seed.release_verifier,execution_verifier=seed.execution_verifier,collection_review_service=review)
    submission=ThermalRunSubmissionService(publisher,farm.thermal,farm)
    app=create_app(jobs,farm.thermal.holds,runs,results,principal_provider=jobs.principal_provider,
        thermal_scenario_store=farm.thermal,thermal_run_submission_service=submission,farm_scenario_service=farm)
    value={'input_version':'thermal-simulation-input-v3','snapshot_id':context['snapshot_id'],
        'review_job_id':str(reviewed['job_id']),'scenario_id':body['thermal']['scenario_id'],
        'scenario_revision':body['thermal']['revision'],'scenario_sha256':body['thermal']['sha256'],
        'farm_scenario_id':selected.scenario_id,'farm_scenario_revision':selected.scenario_revision,
        'farm_scenario_sha256':selected.scenario_sha256,'model_version':'thermal-v1',
        'parameter_set_version':'synthetic-thermal-parameters-v1','idempotency_key':'farm-thermal-one'}
    return farm,publisher,submission,app,value,principal,cli,location,body


def run_count(farm):
    with farm.jobs.connect() as conn:
        return conn.execute(sql.SQL('SELECT count(*) AS n FROM {}.thermal_g1_runs')
            .format(sql.Identifier(farm.jobs.schema))).fetchone()['n']


def test_owned_selection_http_worker_and_verified_completion(execution):
    farm,publisher,submission,app,value,principal,*_=execution
    for scope in FARM_SUBMISSION_SCOPES:
        principal['scopes'].remove(scope)
        assert call(app,value,path='/v1/runs')[0]==403
        principal['scopes'].add(scope)
    with pytest.raises(FarmThermalHold):
        ThermalRunSubmissionService(publisher,farm.thermal).submit('tenant-1',RUN_REQUEST.validate_python(value))
    status,accepted=call(app,value,path='/v1/runs')
    assert status==202 and accepted['state']=='queued' and run_count(farm)==0
    assert call(app,value,path='/v1/runs')==(status,accepted)
    assert call(app,value|{'farm_scenario_sha256':'b'*64},path='/v1/runs')[0]==422
    job_id=UUID(accepted['job_id'])
    worker=ThermalSimulationWorker(publisher,tenant_id='tenant-1',lease_seconds=300,
        scenario_store=farm.thermal,farm_scenario_service=farm)
    result=worker.run_once(str(job_id))
    assert result.state=='succeeded' and run_count(farm)==1
    receipt=json.loads(farm.jobs.read_artifact('tenant-1',job_id))
    selected=farm.read_selection('tenant-1',value['farm_scenario_id'],value['farm_scenario_revision'],value['farm_scenario_sha256'])
    assert receipt['receipt_version']=='thermal-simulation-result-v3'
    assert receipt['farm_bindings_sha256']==sha256(canonical_input_bytes(selected['bindings'])).hexdigest()
    assert all(receipt[key]==value[key] for key in ('farm_scenario_id','farm_scenario_revision','farm_scenario_sha256'))
    path=f'/v1/jobs/{job_id}/run'
    status,summary=call(app,path=path)
    assert status==200 and summary['run_id']==result.run_id
    assert 'farm_bindings_sha256' not in summary and 'economic' not in summary
    assert read_job_run(farm.jobs,farm.thermal.runs,'tenant-1',job_id,farm.thermal,farm).run_id==result.run_id
    with pytest.raises(FarmThermalHold):read_job_run(farm.jobs,farm.thermal.runs,'tenant-1',job_id,farm.thermal)
    principal['scopes'].remove('farm_scenario_read')
    assert call(app,path=path)[0]==403
    assert call(app,value,path='/v1/runs')[0]==403
    principal['scopes'].add('farm_scenario_read')
    missing=farm.jobs.submit('tenant-1','simulation',SIMULATION_INPUT.validate_python(
        {key:item for key,item in value.items() if key not in ('model_version','parameter_set_version','idempotency_key')}
    ).model_dump(mode='json'),'farm-service-missing')
    hold=ThermalSimulationWorker(publisher,tenant_id='tenant-1',scenario_store=farm.thermal).run_once(str(missing['job_id']))
    assert hold.state=='hold' and hold.reason_code=='thermal_farm_scenario_hold'
    assert farm.jobs.get_publication('tenant-1',missing['job_id']) is None and run_count(farm)==1


def test_other_root_with_identical_snapshot_cannot_substitute(execution):
    farm,_,submission,_,value,_,cli,location,body=execution
    _,_,other=farm.owned_research.submit('tenant-1',location.model_copy(update={'idempotency_key':'another-owned-root'}))
    registered=farm.submit('tenant-1',model(body|{'scenario_revision':'r2','research_job_id':str(other['job_id'])}))
    request=RUN_REQUEST.validate_python(value|{'farm_scenario_revision':'r2',
        'farm_scenario_sha256':registered.scenario_sha256,'idempotency_key':'other-root-run'})
    with pytest.raises(FarmThermalHold):submission.submit('tenant-1',request)
    assert cli.run_once().state=='succeeded'
    with pytest.raises(FarmThermalHold):submission.submit('tenant-1',request)
    assert run_count(farm)==0


def test_current_farm_access_revocation_rolls_back_admission_and_completion(execution,monkeypatch):
    farm,publisher,submission,_,value,principal,*_=execution
    def counts():
        with farm.jobs.connect() as conn:
            return tuple(conn.execute(sql.SQL('SELECT count(*) AS n FROM {}').format(farm.jobs._table(table)))
                .fetchone()['n'] for table in ('jobs','job_events'))
    before=counts()
    event=farm.jobs._event
    def revoke_admission(*args,**kwargs):
        result=event(*args,**kwargs)
        principal['scopes'].remove('collection_review_create')
        return result
    with monkeypatch.context() as changed:
        changed.setattr(farm.jobs,'_event',revoke_admission)
        with pytest.raises(PermissionError):submission.submit('tenant-1',RUN_REQUEST.validate_python(value))
    principal['scopes'].add('collection_review_create')
    assert counts()==before
    admitted=submission.submit('tenant-1',RUN_REQUEST.validate_python(value))
    original=farm.thermal.runs._publish_verified_in_transaction
    def revoked(*args,**kwargs):
        stored=original(*args,**kwargs)
        principal['scopes'].remove('farm_scenario_read')
        return stored
    monkeypatch.setattr(farm.thermal.runs,'_publish_verified_in_transaction',revoked)
    result=ThermalSimulationWorker(publisher,tenant_id='tenant-1',lease_seconds=300,
        scenario_store=farm.thermal,farm_scenario_service=farm).run_once(str(admitted['job_id']))
    assert result.state=='hold' and result.reason_code=='thermal_farm_scenario_hold'
    assert run_count(farm)==0 and farm.jobs.get_publication('tenant-1',admitted['job_id']) is None
    assert farm.jobs.get_job('tenant-1',admitted['job_id'])['state']=='hold'
