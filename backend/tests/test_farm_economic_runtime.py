"""Actual runtime TLS/Bearer economic completion; synthetic research authorities."""

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
from app.api_economic_calculation import ECONOMIC_JOB_READ_SCOPES
from app.economic_calculation_worker import EconomicCalculationWorker,CALCULATION_SCOPES
from app.farm_economic_execution import FARM_ECONOMIC_SCOPES
from app.http_identity import BearerGrant,token_digest
from test_farm_economic_execution import economic,execution,farm_setup,login_scope,login_database
from test_farm_thermal_runtime import assemble_farm_runtime
from test_api_serve import tls_files

pytestmark=pytest.mark.parametrize('login_scope',[{'market_calculation':True,
    'market_source_storage':True,'thermal_scenario_storage':True,'break_even_calculation':True}],indirect=True)


def test_actual_runtime_economic_pair_money_and_cash_reads(economic,execution,tls_files):
    service,_,body,_,_=economic
    farm,publisher,*_=execution
    now=datetime.now(timezone.utc)
    token=b'synthetic-farm-economic-'+b'e'*32
    reader=b'synthetic-farm-economic-reader-'+b'r'*32
    other=b'synthetic-farm-economic-other-'+b'o'*32
    scopes=set(CALCULATION_SCOPES+FARM_ECONOMIC_SCOPES)
    read_scopes=set(ECONOMIC_JOB_READ_SCOPES+FARM_ECONOMIC_SCOPES)
    grants=tuple(BearerGrant(token_digest(raw),tenant,frozenset(allowed),
        now-timedelta(seconds=1),now+timedelta(minutes=20)) for raw,tenant,allowed in (
            (token,'tenant-1',scopes),(reader,'tenant-1',read_scopes),(other,'tenant-other',scopes)))
    runtime=assemble_farm_runtime(farm,publisher,tls_files,grants)
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
        assert call('/v1/economic-results',payload=body,bearer=None)[0]==401
        assert call('/v1/economic-results',payload=body,bearer=reader)[0]==403
        status,admitted=call('/v1/economic-results',payload=body)
        assert status==202 and admitted['state']=='queued'
        assert call('/v1/economic-results',payload=body)==(status,admitted)
        result=EconomicCalculationWorker(service.jobs,service.results,tenant_id='tenant-1',
            farm_scenario_service=farm).run_once(admitted['job_id'])
        assert result.state=='succeeded'
        path=f"/v1/jobs/{admitted['job_id']}/economic-result"
        status,value=call(path,bearer=reader)
        assert status==200 and value['assessment_status']=='hold'
        assert call(path.replace('economic-result','economic-cash-flow'),bearer=reader)[0]==200
        assert call(path,bearer=other)[0]==404
    finally:
        server.should_exit=True;thread.join(timeout=15)
        assert not thread.is_alive()
        print('farm_economic_https_seconds='+json.dumps(timings))
