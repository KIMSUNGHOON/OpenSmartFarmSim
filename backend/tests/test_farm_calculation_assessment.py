"""Real SCRAM joined parents; fake CLI and test keys establish software only."""
from hashlib import sha256
from datetime import timedelta
import json
from pathlib import Path
import sys

import pytest
from psycopg import sql

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from app.api import create_app
from app.api_economic_calculation import ECONOMIC_REQUEST
from app.calculation_assessment import (CalculationAssessmentService,CalculationAssessmentContract,
    CalculationAssessmentHold,ADMISSION_SCOPES)
from app.economic_calculation_worker import EconomicCalculationWorker
from app.farm_economic_execution import FARM_ECONOMIC_SCOPES
from app.jobs import canonical_input_bytes
from app.owned_cli_contracts import OwnedCliContractRouter
from app.owned_collection_review import INPUT_VERSION as REVIEW_INPUT_VERSION
from app.cli_contracts import ProposalHold
from app.thermal_simulation_worker import ThermalSimulationWorker
from test_farm_economic_execution import economic,execution,farm_setup,login_scope,login_database
from test_farm_replay_scenario import call
from test_calculation_assessment import assessment_count

pytestmark=pytest.mark.parametrize('login_scope',[{'market_calculation':True,
    'market_source_storage':True,'thermal_scenario_storage':True,'break_even_calculation':True}],indirect=True)


@pytest.fixture
def pair(economic,execution):
    previous,_,body,principal,_=economic
    principal['scopes'].update(ADMISSION_SCOPES)
    admitted=previous.submit('tenant-1',ECONOMIC_REQUEST.validate_python(body))
    outcome=EconomicCalculationWorker(previous.jobs,previous.results,tenant_id='tenant-1',
        farm_scenario_service=previous.farm_scenario_service).run_once(str(admitted['job_id']))
    assert outcome.state=='succeeded'
    return previous,str(admitted['job_id']),body,principal,execution[6]


def assembled(previous):
    farm=previous.farm_scenario_service
    service=CalculationAssessmentService(previous.jobs,farm.thermal.runs,previous.results,
        scenario_store=farm.thermal,farm_scenario_service=farm)
    app=create_app(previous.jobs,farm.thermal.holds,farm.thermal.runs,previous.results,
        principal_provider=previous.jobs.principal_provider,thermal_scenario_store=farm.thermal,
        farm_scenario_service=farm,assessment_service=service)
    return service,app


def install_assessment(cli,service):
    original=cli.contract
    router=OwnedCliContractRouter(original.research,original.reviews,service,
        original._routes[('collection_review',REVIEW_INPUT_VERSION)].authority_resolver)
    service.jobs.decision_validator=router
    cli.contract=router
    return router


def test_actual_farm_pair_pins_shared_cli_hold_and_current_read_scopes(pair):
    previous,economic_id,parent,principal,cli=pair
    service,app=assembled(previous)
    body={'run_job_id':parent['thermal_job_id'],'economic_job_id':economic_id,'idempotency_key':'farm-assessment'}
    for scope in FARM_ECONOMIC_SCOPES:
        principal['scopes'].remove(scope)
        assert call(app,body,path='/v1/assessments')[0]==403
        principal['scopes'].add(scope)
    status,admitted=call(app,body,path='/v1/assessments')
    assert status==202 and admitted['state']=='queued'
    assert call(app,body,path='/v1/assessments')==(status,admitted)
    with service.jobs.connect() as conn:
        job=service.jobs._locked_job(conn,'tenant-1',admitted['job_id'])
    value=json.loads(job['input_bytes'])
    assert value['input_version']=='calculation-assessment-input-v2'
    assert all(value[key]==parent[key] for key in ('farm_scenario_id','farm_scenario_revision','farm_scenario_sha256'))
    assert value['candidate_ids']==value['evidence_refs']==[] and 'profile_id' not in value
    farm=previous.farm_scenario_service
    selected=farm.read_selection('tenant-1',parent['farm_scenario_id'],parent['farm_scenario_revision'],parent['farm_scenario_sha256'])
    assert value['farm_bindings_sha256']==sha256(canonical_input_bytes(selected['bindings'])).hexdigest()
    install_assessment(cli,service)
    outcome=cli.run_once()
    assert str(outcome.job_id)==admitted['job_id'] and outcome.state=='hold' and outcome.decision_id
    report=json.loads(service.jobs.read_hold_report('tenant-1',outcome.job_id))
    assert report['missing_evidence']==list(service.MISSING_EVIDENCE)
    assert service.jobs.get_publication('tenant-1',outcome.job_id) is None and assessment_count(service)==1
    contract=CalculationAssessmentContract(service)
    for key in ('farm_scenario_sha256','farm_bindings_sha256'):
        raw=canonical_input_bytes(value|{key:'0'*64})
        with pytest.raises(ProposalHold):contract.input_context(job|{'input_bytes':raw,'input_sha256':sha256(raw).hexdigest()})
    with pytest.raises(ProposalHold):
        contract.input_context(job|{'created_at':job['created_at']-timedelta(hours=1)})


def test_parent_mixing_pending_foreign_and_duplicate_run_job_cannot_admit(pair,execution):
    previous,economic_id,parent,principal,_=pair
    service,app=assembled(previous)
    jobs=service.jobs
    body={'run_job_id':parent['thermal_job_id'],'economic_job_id':economic_id,'idempotency_key':'reject-mixed'}
    with jobs.connect() as conn:
        thermal=jobs._locked_job(conn,'tenant-1',body['run_job_id'])
        economic=jobs._locked_job(conn,'tenant-1',economic_id)
    pending=jobs.submit('tenant-1','simulation',json.loads(thermal['input_bytes']),'pending-farm')
    assert call(app,body|{'run_job_id':str(pending['job_id'])},path='/v1/assessments')[0]==422
    principal['tenant_id']='tenant-other'
    try:
        assert call(app,body,path='/v1/assessments')[0]==422
    finally:principal['tenant_id']='tenant-1'
    unconfigured=CalculationAssessmentService(jobs,service.runs,service.results,service.scenario_store)
    with pytest.raises(CalculationAssessmentHold):
        unconfigured.submit('tenant-1',body['run_job_id'],economic_id,'missing-farm')
    with pytest.raises(ValueError):
        create_app(jobs,service.scenario_store.holds,service.runs,service.results,
            principal_provider=jobs.principal_provider,thermal_scenario_store=service.scenario_store,
            farm_scenario_service=service.farm_scenario_service,assessment_service=unconfigured)
    duplicated=jobs.submit('tenant-1','simulation',json.loads(thermal['input_bytes']),'different-thermal-job')
    result=ThermalSimulationWorker(execution[1],tenant_id='tenant-1',lease_seconds=300,
        scenario_store=service.scenario_store,farm_scenario_service=service.farm_scenario_service).run_once(str(duplicated['job_id']))
    assert result.state=='succeeded'
    original=json.loads(jobs.read_artifact('tenant-1',body['run_job_id']))
    assert result.run_id==original['run_id']
    assert call(app,body|{'run_job_id':str(duplicated['job_id'])},path='/v1/assessments')[0]==422
    legacy_thermal={'input_version':'thermal-simulation-input-v1',
        **{key:json.loads(thermal['input_bytes'])[key] for key in ('snapshot_id','review_job_id')}}
    legacy=jobs.submit('tenant-1','simulation',legacy_thermal,'legacy-assessment-thermal')
    assert ThermalSimulationWorker(execution[1],tenant_id='tenant-1',lease_seconds=300).run_once(str(legacy['job_id'])).state=='succeeded'
    assert call(app,body|{'run_job_id':str(legacy['job_id'])},path='/v1/assessments')[0]==422
    legacy_economic=json.loads(economic['input_bytes'])
    for key in ('farm_scenario_id','farm_scenario_revision','farm_scenario_sha256','thermal_job_id'):
        legacy_economic.pop(key)
    legacy_economic['input_version']='economic-calculation-input-v1'
    old=jobs.submit('tenant-1','simulation',legacy_economic,'legacy-assessment-economic')
    assert EconomicCalculationWorker(jobs,previous.results,tenant_id='tenant-1').run_once(str(old['job_id'])).state=='succeeded'
    assert call(app,body|{'economic_job_id':str(old['job_id'])},path='/v1/assessments')[0]==422
    assert assessment_count(service)==0
    legacy_body=body|{'run_job_id':str(legacy['job_id']),'economic_job_id':str(old['job_id'])}
    assert call(app,legacy_body,path='/v1/assessments')[0]==202
    assert call(app,body,path='/v1/assessments')[0]==409
    assert assessment_count(service)==1


def test_commit_rechecks_farm_access_and_original_assembly_with_full_rollback(pair,monkeypatch):
    previous,economic_id,parent,principal,_=pair
    service,_=assembled(previous)
    jobs=service.jobs
    original=jobs._event
    submitted=[]
    def event(conn,tenant,job_id,kind,*args,**kwargs):
        original(conn,tenant,job_id,kind,*args,**kwargs)
        if kind=='submitted':
            submitted.append(job_id)
            principal['scopes'].remove('farm_scenario_read')
    try:
        with monkeypatch.context() as patch:
            patch.setattr(jobs,'_event',event)
            with pytest.raises(PermissionError):service.submit('tenant-1',parent['thermal_job_id'],economic_id,'late-scope')
    finally:principal['scopes'].add('farm_scenario_read')
    def changed(conn,tenant,job_id,kind,*args,**kwargs):
        original(conn,tenant,job_id,kind,*args,**kwargs)
        if kind=='submitted':
            submitted.append(job_id)
            service.farm_scenario_service=None
    farm=service.farm_scenario_service
    try:
        with monkeypatch.context() as patch:
            patch.setattr(jobs,'_event',changed)
            with pytest.raises(RuntimeError):service.submit('tenant-1',parent['thermal_job_id'],economic_id,'late-assembly')
    finally:service.farm_scenario_service=farm
    original_prepare=service.prepare
    calls=[]
    def late(*args,**kwargs):
        value=original_prepare(*args,**kwargs)
        calls.append(1)
        if len(calls)==2:principal['scopes'].remove('farm_scenario_read')
        return value
    try:
        with monkeypatch.context() as patch:
            patch.setattr(service,'prepare',late)
            with pytest.raises(PermissionError):service.submit('tenant-1',parent['thermal_job_id'],economic_id,'after-prepare')
    finally:principal['scopes'].add('farm_scenario_read')
    assert len(calls)==2 and len(submitted)==2 and assessment_count(service)==0
    for job_id in submitted:
        assert jobs.get_job('tenant-1',job_id) is None
        with jobs.connect() as conn:
            assert conn.execute(sql.SQL('SELECT count(*) AS n FROM {} WHERE job_id=%s')
                .format(jobs._table('job_events')),(job_id,)).fetchone()['n']==0
