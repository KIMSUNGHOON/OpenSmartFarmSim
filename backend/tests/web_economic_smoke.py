"""Explicit TLS/browser/Decimal/PG software integration, no CLI or data gate."""
from datetime import datetime, timedelta, timezone
import json
import os
from pathlib import Path
import select
import subprocess
import sys
import threading
import time
from uuid import UUID
from psycopg import sql

import pytest

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from app.api_runtime import ApiRuntime
from app.api_economics import project_economic_result
from app.economic_calculation_worker import EconomicCalculationWorker, CALCULATION_SCOPES
from app.http_identity import BearerRegistry, BearerGrant, token_digest
from app.market_source_store import MarketSourceStore
from app.market_result_store import MarketResultStore
from test_api_economic_scenario import economic_api, login_database, login_scope, PROFILE
from test_api_runtime import config, dependencies
from test_api_serve import tls_files
from web_shell_smoke import frontend, WEB

TOKEN=b'synthetic-economic-browser-'+b'e'*32


@pytest.mark.parametrize('login_scope', [{**PROFILE,'break_even_calculation':True}], indirect=True)
def test_browser_real_https_assumption_revision_and_conditional_result(economic_api, tls_files):
    _, jobs, candidates, principal, _, _=economic_api
    principal['scopes'].update(CALCULATION_SCOPES)
    os.close(jobs._content_directory(create=True))
    cert,key,_=tls_files
    now=datetime.now(timezone.utc)
    scopes=frozenset(principal['scopes']|{'market_source_write','market_candidate_write'})
    registry=BearerRegistry((BearerGrant(token_digest(TOKEN),'tenant-1',scopes,
        now-timedelta(seconds=1),now+timedelta(hours=1)),))
    factory=lambda *,principal_provider:MarketSourceStore(jobs._dsn,jobs.schema,
        principal_provider=principal_provider,runtime_identity=jobs.runtime_identity)
    runtime=ApiRuntime(config(policy=jobs.runtime_identity[0],dsn=jobs._dsn,artifact_root=jobs.artifact_root,
        certificate=cert,private_key=key,port=0),dependencies(bearer_registry=registry,
            market_source_factory=factory,market_scope_resolver=candidates._source._holds._scope_resolver))
    results=MarketResultStore(jobs._dsn,jobs.schema,candidates,
        principal_provider=jobs.principal_provider,runtime_identity=jobs.runtime_identity)
    worker=EconomicCalculationWorker(jobs,results,tenant_id='tenant-1')
    server=runtime.service.server();thread=threading.Thread(target=server.run,daemon=True);thread.start()
    browser=None
    try:
        deadline=time.monotonic()+10
        while not server.started and thread.is_alive() and time.monotonic()<deadline:time.sleep(.05)
        assert server.started
        api_port=server.servers[0].sockets[0].getsockname()[1]
        with frontend(f'https://127.0.0.1:{api_port}',cert,key) as (port,_):
            env={name:os.environ[name] for name in ('PATH','HOME','LANG','PLAYWRIGHT_BROWSERS_PATH') if name in os.environ}
            browser=subprocess.Popen(['node','e2e/real-economic-smoke.mjs',f'https://127.0.0.1:{port}'],
                cwd=WEB,env=env,stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True)
            deadline=time.monotonic()+150
            while not select.select([browser.stdout],[],[],30)[0]:
                assert time.monotonic()<deadline, 'browser economic admission timed out'
            line=browser.stdout.readline()
            if not line:
                _,error=browser.communicate(timeout=5);pytest.fail('synthetic browser failed: '+error[-2000:])
            queued=json.loads(line);assert queued['stage']=='queued' and UUID(queued['job_id'])
            print('Actual economic browser admission:',json.dumps(queued['network']))
            sources=factory(principal_provider=jobs.principal_provider)
            saved=sources.get_user_source('tenant-1','economic_input',queued['source_id'],queued['source_revision'])
            assert saved['input']['value']=='9007199254740993.0000000001'
            assert saved['input']['available_at']=='2026-09-29T08:00:00Z'
            outcome=worker.run_once(queued['job_id']);assert outcome.state=='succeeded'
            print('Actual economic worker completed')
            with jobs.connect() as conn:
                job=jobs._locked_job(conn,'tenant-1',UUID(queued['job_id']))
                immutable=json.loads(jobs._verified_input(job))
            stored=results.get_market_result(immutable['scenario_id'],immutable['scenario_revision'])
            projection=project_economic_result(stored).model_dump(mode='json')
            browser.stdin.write(json.dumps(projection)+'\n');browser.stdin.flush()
            deadline=time.monotonic()+150
            while True:
                try:
                    output,error=browser.communicate(timeout=45)
                    break
                except subprocess.TimeoutExpired:
                    assert time.monotonic()<deadline, 'browser economic result verification timed out'
            assert browser.returncode==0,error[-2000:]
            assert json.loads(output)['stage']=='verified'
            assert projection['assessment_status']=='hold' and projection['input_origin']=='user'
            with jobs.connect() as conn:
                count=conn.execute(sql.SQL('SELECT count(*) FROM {} WHERE tenant_id=%s AND stage=%s AND input_sha256=%s')
                    .format(jobs._table('jobs')),('tenant-1','simulation',job['input_sha256'])).fetchone()['count']
                assert count==1
            assert worker.run_once(queued['job_id']) is None
    finally:
        if browser is not None and browser.poll() is None:browser.kill();browser.communicate(timeout=5)
        server.should_exit=True;thread.join(timeout=15);assert not thread.is_alive()
