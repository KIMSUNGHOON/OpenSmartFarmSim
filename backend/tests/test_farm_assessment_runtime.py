"""Actual TLS admission and persisted fake-CLI hold; no product invocation."""

from datetime import datetime,timedelta,timezone
import http.client
import json
from pathlib import Path
import ssl
import sys
import threading
import time

import pytest

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from app.calculation_assessment import ADMISSION_SCOPES,READ_SCOPES
from app.farm_economic_execution import FARM_ECONOMIC_SCOPES
from app.http_identity import BearerGrant,current_principal,token_digest
from test_farm_calculation_assessment import (pair,economic,execution,farm_setup,
    login_scope,login_database,assembled,install_assessment)
from test_farm_thermal_runtime import assemble_farm_runtime
from test_api_serve import tls_files

pytestmark=pytest.mark.parametrize('login_scope',[{'market_calculation':True,
    'market_source_storage':True,'thermal_scenario_storage':True,'break_even_calculation':True}],indirect=True)


def test_actual_https_runtime_pair_admission_and_immutable_hold(pair,execution,tls_files):
    previous,economic_id,parent,_,cli=pair
    service,_=assembled(previous)
    farm,publisher,*_=execution
    now=datetime.now(timezone.utc)
    token=b'synthetic-farm-assessment-'+b'a'*32
    reader=b'synthetic-farm-assessment-reader-'+b'r'*32
    other=b'synthetic-farm-assessment-other-'+b'o'*32
    all_scopes=set((*ADMISSION_SCOPES,*FARM_ECONOMIC_SCOPES,'auditor'))
    read_scopes=set((*READ_SCOPES,*FARM_ECONOMIC_SCOPES,'auditor'))
    grants=tuple(BearerGrant(token_digest(raw),tenant,frozenset(scopes),
        now-timedelta(seconds=1),now+timedelta(minutes=20)) for raw,tenant,scopes in (
            (token,'tenant-1',all_scopes),(reader,'tenant-1',read_scopes),(other,'tenant-other',all_scopes)))
    runtime=assemble_farm_runtime(farm,publisher,tls_files,grants)
    assert runtime.assessments.farm_scenario_service is runtime.farm_scenarios
    assert runtime.assessments.economic.farm_scenario_service is runtime.farm_scenarios
    assert runtime.assessments.scenario_store is runtime.thermal_scenarios
    body={'run_job_id':parent['thermal_job_id'],'economic_job_id':economic_id,'idempotency_key':'https-farm-assessment'}
    server=runtime.service.server()
    thread=threading.Thread(target=server.run,daemon=True);thread.start()
    timings=[]
    try:
        deadline=time.monotonic()+10
        while not server.started:
            assert thread.is_alive() and time.monotonic()<deadline
            time.sleep(0.01)
        port=server.servers[0].sockets[0].getsockname()[1]
        context=ssl.create_default_context(cafile=str(tls_files[0]))
        def call(path,*,payload=None,bearer=token):
            conn=http.client.HTTPSConnection('127.0.0.1',port,timeout=30,context=context)
            started=time.monotonic()
            try:
                headers={'Content-Type':'application/json','X-Tenant-Id':'foreign'}
                if bearer is not None:headers['Authorization']='Bearer '+bearer.decode()
                conn.request('POST' if payload is not None else 'GET',path,
                    json.dumps(payload) if payload is not None else None,headers)
                response=conn.getresponse()
                assert response.getheader('cache-control')=='no-store'
                return response.status,json.loads(response.read())
            finally:
                timings.append(round(time.monotonic()-started,3));conn.close()
        assert call('/v1/assessments',payload=body,bearer=None)[0]==401
        assert call('/v1/assessments',payload=body,bearer=reader)[0]==403
        assert call('/v1/assessments',payload=body,bearer=other)[0]==422
        status,accepted=call('/v1/assessments',payload=body)
        assert status==202 and accepted['state']=='queued'
        assert call('/v1/assessments',payload=body)==(status,accepted)
        install_assessment(cli,service)
        held=cli.run_once()
        assert str(held.job_id)==accepted['job_id'] and held.state=='hold' and held.decision_id
        assert current_principal() is None
        status,job=call(f"/v1/jobs/{accepted['job_id']}",bearer=reader)
        assert status==200 and job['state']=='hold'
        path=f"/v1/jobs/{accepted['job_id']}/hold-report"
        status,report=call(path,bearer=reader)
        assert status==200 and report['missing_evidence']==list(service.MISSING_EVIDENCE)
        assert call(path,bearer=other)[0]==404
    finally:
        server.should_exit=True;thread.join(timeout=15)
        assert not thread.is_alive()
        print('farm_assessment_https_seconds='+json.dumps(timings))
