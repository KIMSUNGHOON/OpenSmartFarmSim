"""Actual TLS/browser/PG finite user-grid integration; synthetic sources only."""
from datetime import datetime,timedelta,timezone
import json
import os
from pathlib import Path
import select
import subprocess
import sys
import threading
import time
from uuid import UUID

import pytest
from psycopg import sql

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from app.api_runtime import ApiRuntime
from app.api_break_even import project_break_even_result
from app.break_even_calculation_worker import BreakEvenCalculationWorker
from app.break_even import BreakEvenRequest
from app.http_identity import BearerRegistry,BearerGrant,token_digest
from app.market_source_store import MarketSourceStore
from test_api_break_even_plan import plan_api,login_database,login_scope,PROFILE
from test_api_runtime import config,dependencies
from test_api_serve import tls_files
from web_shell_smoke import frontend,WEB

TOKEN=b'synthetic-break-even-browser-'+b'b'*32
pytestmark=pytest.mark.parametrize('login_scope',[{**PROFILE,'break_even_calculation':True}],indirect=True)


@pytest.mark.parametrize('lost_reply',[False,True],ids=['normal','lost_reply'])
def test_browser_real_https_plan_worker_and_grid_result(plan_api,tls_files,lost_reply):
    _,service,expected,principal=plan_api
    jobs=service.jobs;view=service.store._source._source
    principal['scopes'].update({'simulation_execute','break_even_read','break_even_write','market_candidate_write','market_source_write'})
    cert,key,_=tls_files;now=datetime.now(timezone.utc)
    registry=BearerRegistry((BearerGrant(token_digest(TOKEN),'tenant-1',frozenset(principal['scopes']),now-timedelta(seconds=1),now+timedelta(hours=1)),))
    factory=lambda *,principal_provider:MarketSourceStore(jobs._dsn,jobs.schema,principal_provider=principal_provider,runtime_identity=jobs.runtime_identity)
    runtime=ApiRuntime(config(policy=jobs.runtime_identity[0],dsn=jobs._dsn,artifact_root=jobs.artifact_root,certificate=cert,private_key=key,port=0),
        dependencies(bearer_registry=registry,market_source_factory=factory,market_scope_resolver=view._holds._scope_resolver))
    worker=BreakEvenCalculationWorker(jobs,service.store,tenant_id='tenant-1')
    server=runtime.service.server();thread=threading.Thread(target=server.run,daemon=True);thread.start();browser=None
    try:
        deadline=time.monotonic()+10
        while not server.started and thread.is_alive() and time.monotonic()<deadline:time.sleep(.05)
        assert server.started
        api_port=server.servers[0].sockets[0].getsockname()[1]
        with frontend(f'https://127.0.0.1:{api_port}',cert,key) as (port,_):
            env={name:os.environ[name] for name in ('PATH','HOME','LANG','PLAYWRIGHT_BROWSERS_PATH') if name in os.environ}
            command=['node','e2e/real-break-even-smoke.mjs',f'https://127.0.0.1:{port}']
            if lost_reply:command.append('lose-plan-reply')
            browser=subprocess.Popen(command,cwd=WEB,env=env,
                stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True)
            deadline=time.monotonic()+180
            while not select.select([browser.stdout],[],[],30)[0]:assert time.monotonic()<deadline,'browser plan admission timed out'
            line=browser.stdout.readline()
            if not line:
                _,error=browser.communicate(timeout=5);pytest.fail('synthetic browser failed: '+error[-2500:])
            admitted=json.loads(line);assert admitted['stage']=='queued' and UUID(admitted['job_id'])
            print('Actual break-even browser admission:',json.dumps(admitted['network']),flush=True)
            with jobs.connect() as conn:
                job=conn.execute(sql.SQL('SELECT * FROM {} WHERE tenant_id=%s AND job_id=%s')
                    .format(jobs._table('jobs')),('tenant-1',UUID(admitted['job_id']))).fetchone()
            assert job is not None
            actual=json.loads(jobs._verified_input(job))
            assert actual['input_version']=='break-even-calculation-input-v1'
            assert actual['request']==expected['request']|{'plan_id':admitted['plan_id']}
            assert actual['plan']['trials']==[dict(pin,ordinal=index,value=value) for index,(pin,value) in enumerate(zip(expected['trials'],('20','32'),strict=True))]
            outcome=worker.run_once(admitted['job_id']);assert outcome.state=='succeeded'
            request,result=service.store.get_break_even_read('tenant-1',admitted['plan_id'])
            assert type(request) is BreakEvenRequest
            projection=project_break_even_result(request,result).model_dump(mode='json')
            browser.stdin.write(json.dumps(projection)+'\n');browser.stdin.flush()
            deadline=time.monotonic()+180
            while True:
                try:output,error=browser.communicate(timeout=45);break
                except subprocess.TimeoutExpired:assert time.monotonic()<deadline,'browser grid verification timed out'
            assert browser.returncode==0,error[-2500:]
            verified=json.loads(output)
            assert verified['stage']=='verified' and projection['status']=='bracket_only'
            print('Actual break-even browser result:',json.dumps(verified['network']),flush=True)
            with jobs.connect() as conn:
                count=conn.execute(sql.SQL('SELECT count(*) AS n FROM {} WHERE tenant_id=%s AND input_sha256=%s').format(jobs._table('jobs')),
                    ('tenant-1',job['input_sha256'])).fetchone()['n']
                assert count==1
            assert worker.run_once(admitted['job_id']) is None
    finally:
        if browser is not None and browser.poll() is None:browser.kill();browser.communicate(timeout=5)
        server.should_exit=True;thread.join(timeout=15);assert not thread.is_alive()
