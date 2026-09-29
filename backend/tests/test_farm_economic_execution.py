"""Actual paired thermal/economic jobs over SCRAM; controlled authorities only."""

from hashlib import sha256
import json
from pathlib import Path
import sys
from uuid import UUID

import pytest
from psycopg import sql

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from app.api import create_app
from app.api_economic_calculation import (EconomicCalculationService, EconomicCalculationHold, ECONOMIC_REQUEST)
from app.economic_calculation_worker import EconomicCalculationWorker, CALCULATION_SCOPES, ECONOMIC_INPUT
from app.farm_economic_execution import FARM_ECONOMIC_SCOPES
from app.jobs import canonical_input_bytes
from app.market_result_store import MarketResultStore
from app.thermal_simulation_worker import ThermalSimulationWorker, SIMULATION_INPUT
from app.thermal_run_submission import RUN_REQUEST
from test_farm_thermal_execution import execution, farm_setup, login_scope, login_database
from test_farm_replay_scenario import call,model
from test_economic_calculation_worker import result_count

pytestmark=pytest.mark.parametrize('login_scope',[{'market_calculation':True,
    'market_source_storage':True,'thermal_scenario_storage':True,'break_even_calculation':True}],indirect=True)


@pytest.fixture
def economic(execution):
    farm,publisher,thermal_submission,_,thermal_request,principal,*_=execution
    principal['scopes'].update(CALCULATION_SCOPES)
    admitted=thermal_submission.submit('tenant-1',
        RUN_REQUEST.validate_python(thermal_request))
    worker=ThermalSimulationWorker(publisher,tenant_id='tenant-1',lease_seconds=300,
        scenario_store=farm.thermal,farm_scenario_service=farm)
    completed=worker.run_once(str(admitted['job_id']))
    assert completed.state=='succeeded'
    selected=farm.read_selection('tenant-1',thermal_request['farm_scenario_id'],
        thermal_request['farm_scenario_revision'],thermal_request['farm_scenario_sha256'])
    chosen=selected['request'].economic
    results=MarketResultStore(farm.jobs._dsn,farm.jobs.schema,farm.candidates,
        principal_provider=farm.jobs.principal_provider,runtime_identity=farm.jobs.runtime_identity)
    service=EconomicCalculationService(farm.jobs,results,farm)
    app=create_app(farm.jobs,farm.thermal.holds,farm.thermal.runs,results,
        principal_provider=farm.jobs.principal_provider,thermal_scenario_store=farm.thermal,
        farm_scenario_service=farm,economic_calculation_service=service)
    body={'input_version':'economic-calculation-input-v2','scenario_id':chosen.scenario_id,
        'scenario_revision':chosen.revision,'scenario_sha256':chosen.sha256,'candidate_id':chosen.candidate_id,
        'formula_version':'economic-ledger-v9-sales-settlement',
        **{key:thermal_request[key] for key in ('farm_scenario_id','farm_scenario_revision','farm_scenario_sha256')},
        'thermal_job_id':str(admitted['job_id']),'idempotency_key':'farm-economic-one'}
    return service,app,body,principal,thermal_request


def test_http_pair_calculation_receipt_and_current_money_cash_reads(economic):
    service,app,body,principal,_=economic
    for scope in FARM_ECONOMIC_SCOPES:
        principal['scopes'].remove(scope)
        assert call(app,body,path='/v1/economic-results')[0]==403
        principal['scopes'].add(scope)
    with pytest.raises(EconomicCalculationHold):
        EconomicCalculationService(service.jobs,service.results).submit('tenant-1',ECONOMIC_REQUEST.validate_python(body))
    assert result_count(service.results)==0
    status,admitted=call(app,body,path='/v1/economic-results')
    assert status==202 and admitted['state']=='queued'
    assert call(app,body,path='/v1/economic-results')==(status,admitted)
    worker=EconomicCalculationWorker(service.jobs,service.results,tenant_id='tenant-1',farm_scenario_service=service.farm_scenario_service)
    outcome=worker.run_once(admitted['job_id'])
    assert outcome.state=='succeeded' and result_count(service.results)==1
    job_id=UUID(admitted['job_id'])
    receipt=json.loads(service.jobs.read_artifact('tenant-1',job_id))
    assert receipt['receipt_version']=='economic-calculation-result-v2'
    assert all(receipt[key]==body[key] for key in ('farm_scenario_id','farm_scenario_revision','farm_scenario_sha256','thermal_job_id'))
    assert receipt['thermal_receipt_sha256']==sha256(service.jobs.read_artifact('tenant-1',body['thermal_job_id'])).hexdigest()
    path=f'/v1/jobs/{job_id}/economic-result'
    status,result=call(app,path=path)
    assert status==200 and result['calculation_status']=='conditional_user_assumption'
    assert result['assessment_status']=='hold' and 'thermal_run_id' not in result
    cash=f'/v1/jobs/{job_id}/economic-cash-flow'
    assert call(app,path=cash)[0]==200
    for target in (path,cash):
        principal['scopes'].remove('farm_scenario_read')
        assert call(app,path=target)[0]==403
        principal['scopes'].add('farm_scenario_read')


def test_late_admission_scope_loss_rolls_back_new_intent(economic,monkeypatch):
    service,_,body,principal,_=economic
    revoked=[]
    original_event=service.jobs._event
    def revoke_at_admission(conn,tenant,job_id,kind,*args,**kwargs):
        original_event(conn,tenant,job_id,kind,*args,**kwargs)
        if kind=='submitted':
            revoked.append(job_id)
            principal['scopes'].remove('thermal_run_read')
    try:
        with monkeypatch.context() as patch:
            patch.setattr(service.jobs,'_event',revoke_at_admission)
            with pytest.raises(PermissionError):
                service.submit('tenant-1',ECONOMIC_REQUEST.validate_python(body))
    finally:
        principal['scopes'].add('thermal_run_read')
    assert len(revoked)==1 and service.jobs.get_job('tenant-1',revoked[0]) is None
    with service.jobs.connect() as conn:
        assert conn.execute(sql.SQL('SELECT count(*) AS n FROM {} WHERE job_id=%s')
            .format(service.jobs._table('job_events')),(revoked[0],)).fetchone()['n']==0
    assert result_count(service.results)==0


def test_other_plan_or_pending_thermal_cannot_authorize_money(economic,execution):
    service,_,body,_,thermal_request=economic
    farm=service.farm_scenario_service
    selected=farm.read_selection('tenant-1',body['farm_scenario_id'],body['farm_scenario_revision'],body['farm_scenario_sha256'])
    other=farm.submit('tenant-1',model(selected['request'].model_dump(mode='json')|{'scenario_revision':'r2'}))
    with pytest.raises(EconomicCalculationHold):
        service.submit('tenant-1',ECONOMIC_REQUEST.validate_python(body|{'farm_scenario_revision':'r2',
            'farm_scenario_sha256':other.scenario_sha256}))
    raw=SIMULATION_INPUT.validate_python({key:item for key,item in thermal_request.items()
        if key not in ('model_version','parameter_set_version','idempotency_key')}).model_dump(mode='json')
    pending=service.jobs.submit('tenant-1','simulation',raw,'pending-thermal')
    with pytest.raises(EconomicCalculationHold):
        service.submit('tenant-1',ECONOMIC_REQUEST.validate_python(body|{'thermal_job_id':str(pending['job_id'])}))
    legacy=service.jobs.submit('tenant-1','simulation',{'input_version':'thermal-simulation-input-v1',
        'snapshot_id':thermal_request['snapshot_id'],'review_job_id':thermal_request['review_job_id']},'legacy-thermal')
    assert ThermalSimulationWorker(execution[1],tenant_id='tenant-1',lease_seconds=300).run_once(
        str(legacy['job_id'])).state=='succeeded'
    with pytest.raises(EconomicCalculationHold):
        service.submit('tenant-1',ECONOMIC_REQUEST.validate_python(body|{'thermal_job_id':str(legacy['job_id'])}))
    missing=service.jobs.submit('tenant-1','simulation',ECONOMIC_INPUT.validate_python(
        {key:item for key,item in body.items() if key!='idempotency_key'}).model_dump(mode='json'),'missing-farm-economic')
    outcome=EconomicCalculationWorker(service.jobs,service.results,tenant_id='tenant-1').run_once(str(missing['job_id']))
    assert outcome.state=='hold' and outcome.reason_code=='economic_farm_scenario_hold'
    assert service.jobs.get_publication('tenant-1',missing['job_id']) is None and result_count(service.results)==0


def test_late_current_farm_access_rolls_back_money_publication(economic,monkeypatch):
    service,_,body,principal,_=economic
    admitted=service.submit('tenant-1',ECONOMIC_REQUEST.validate_python(body))
    original=service.results._pin_in_transaction
    def revoke(*args,**kwargs):
        stored=original(*args,**kwargs)
        principal['scopes'].remove('farm_scenario_read')
        return stored
    monkeypatch.setattr(service.results,'_pin_in_transaction',revoke)
    outcome=EconomicCalculationWorker(service.jobs,service.results,tenant_id='tenant-1',
        farm_scenario_service=service.farm_scenario_service).run_once(str(admitted['job_id']))
    assert outcome.state=='hold' and outcome.reason_code=='economic_input_hold'
    assert result_count(service.results)==0 and service.jobs.get_publication('tenant-1',admitted['job_id']) is None
    assert service.jobs.get_job('tenant-1',admitted['job_id'])['state']=='hold'
