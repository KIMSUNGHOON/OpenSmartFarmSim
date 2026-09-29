"""Explicit real HTTPS/SCRAM/Chromium replay; synthetic CLI and release keys only."""
from datetime import datetime,timedelta,timezone
import json
import os
from pathlib import Path
import subprocess
import sys
import threading
import time
from uuid import UUID

import pytest

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from app.http_identity import BearerGrant,token_digest
from app.api_thermal import project_thermal_run
from app.thermal_run_submission import RUN_REQUEST
from app.thermal_simulation_worker import ThermalSimulationWorker
from test_farm_thermal_runtime import assemble_farm_runtime,READ_SCOPES,tls_files
from test_farm_thermal_execution import execution,farm_setup,login_scope,login_database
from web_shell_smoke import frontend,WEB

pytestmark=pytest.mark.parametrize('login_scope',[{'market_calculation':True,
    'market_source_storage':True,'thermal_scenario_storage':True,'break_even_calculation':True}],indirect=True)


def test_browser_completed_farm_thermal_run_over_real_https(execution,tls_files,tmp_path):
    farm,publisher,submission,_,value,*_=execution
    admitted=submission.submit('tenant-1',RUN_REQUEST.validate_python(value))
    outcome=ThermalSimulationWorker(publisher,tenant_id='tenant-1',lease_seconds=300,
        scenario_store=farm.thermal,farm_scenario_service=farm).run_once(str(admitted['job_id']))
    assert outcome.state=='succeeded'
    assert UUID(str(admitted['job_id']))
    _,series=project_thermal_run(farm.thermal.runs.get_run('tenant-1',outcome.run_id))
    cert,key,_=tls_files
    now=datetime.now(timezone.utc)
    token=b'synthetic-thermal-replay-browser-'+b'r'*32
    grant=BearerGrant(token_digest(token),'tenant-1',frozenset((*READ_SCOPES,'thermal_run_read')),
        now-timedelta(seconds=1),now+timedelta(minutes=20))
    runtime=assemble_farm_runtime(farm,publisher,tls_files,(grant,))
    server=runtime.service.server();thread=threading.Thread(target=server.run,daemon=True);thread.start()
    browser=None
    try:
        deadline=time.monotonic()+10
        while not server.started:
            assert thread.is_alive() and time.monotonic()<deadline
            time.sleep(.01)
        port=server.servers[0].sockets[0].getsockname()[1]
        with frontend(f'https://127.0.0.1:{port}',cert,key) as (web_port,_):
            env={name:os.environ[name] for name in ('PATH','HOME','LANG','PLAYWRIGHT_BROWSERS_PATH') if name in os.environ}
            browser=subprocess.Popen(['node','e2e/real-thermal-replay-smoke.mjs',f'https://127.0.0.1:{web_port}',str(tmp_path/'screens')],
                cwd=WEB,env=env,stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True)
            browser.stdin.write(json.dumps({'token':token.decode(),'job_id':str(admitted['job_id']),
                'run_id':outcome.run_id,'series':series.model_dump(mode='json')})+'\n')
            browser.stdin.flush()
            output,error=browser.communicate(timeout=90)
            assert browser.returncode==0,error[-2500:]
            report=json.loads(output)
            assert report['stage']=='verified' and report['points']==120
            assert len(report['network'])==4 and all(item['status']==200 for item in report['network'])
            print('thermal_replay_browser='+json.dumps(report))
            print('thermal_replay_screens='+str(tmp_path/'screens'))
    finally:
        if browser is not None and browser.poll() is None:browser.kill();browser.communicate(timeout=5)
        server.should_exit=True;thread.join(timeout=15);assert not thread.is_alive()
