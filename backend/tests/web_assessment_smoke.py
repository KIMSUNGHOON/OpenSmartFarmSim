"""Explicit Chromium → HTTPS → actual PG → fake CLI hold integration."""

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

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from app.calculation_assessment import ADMISSION_SCOPES
from app.farm_economic_execution import FARM_ECONOMIC_SCOPES
from app.http_identity import BearerGrant,token_digest
from test_farm_assessment_runtime import (pair,economic,execution,farm_setup,
    login_scope,login_database,assembled,install_assessment,assemble_farm_runtime,tls_files)
from web_shell_smoke import WEB,frontend


@pytest.mark.parametrize('login_scope',[{'market_calculation':True,
    'market_source_storage':True,'thermal_scenario_storage':True,
    'break_even_calculation':True}],indirect=True)
def test_browser_assessment_admission_persisted_hold_and_reopen(pair,execution,tls_files):
    previous,economic_id,parent,_,cli=pair
    service,_=assembled(previous)
    farm,publisher,*_=execution
    now=datetime.now(timezone.utc)
    token=b'synthetic-assessment-browser-'+b'a'*32
    grant=BearerGrant(token_digest(token),'tenant-1',
        frozenset((*ADMISSION_SCOPES,*FARM_ECONOMIC_SCOPES,'auditor')),
        now-timedelta(seconds=1),now+timedelta(minutes=20))
    runtime=assemble_farm_runtime(farm,publisher,tls_files,(grant,))
    assert runtime.assessments.farm_scenario_service is runtime.farm_scenarios
    server=runtime.service.server()
    thread=threading.Thread(target=server.run,daemon=True);thread.start()
    browser=None
    try:
        deadline=time.monotonic()+15
        while not server.started:
            assert thread.is_alive() and time.monotonic()<deadline
            time.sleep(0.01)
        port=server.servers[0].sockets[0].getsockname()[1]
        with frontend(f'https://127.0.0.1:{port}',*tls_files[:2]) as (web_port,_):
            env={name:os.environ[name] for name in
                ('PATH','HOME','LANG','PLAYWRIGHT_BROWSERS_PATH') if name in os.environ}
            browser=subprocess.Popen(['node','e2e/real-assessment-smoke.mjs',
                f'https://127.0.0.1:{web_port}',parent['thermal_job_id'],economic_id],
                cwd=WEB,env=env,stdin=subprocess.PIPE,stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,text=True)
            assert select.select([browser.stdout],[],[],60)[0], 'browser admission observation timed out'
            line=browser.stdout.readline()
            if not line:
                _,error=browser.communicate(timeout=5)
                pytest.fail(f'browser exited before admission (exit {browser.returncode}): '+
                            error.replace(token.decode(),'<redacted>')[-2500:])
            queued=json.loads(line)
            assert queued['event']=='queued' and UUID(queued['job_id'])
            install_assessment(cli,service)
            outcome=cli.run_once()
            assert str(outcome.job_id)==queued['job_id'] and outcome.state=='hold' and outcome.decision_id
            browser.stdin.write('hold-ready\n');browser.stdin.flush()
            output,error=browser.communicate(timeout=100)
            assert browser.returncode==0,error.replace(token.decode(),'<redacted>')[-2500:]
            observed=json.loads(output)
            assert observed=={'event':'verified','hold_count':6,'post_count':1,
                              'https_responses':5,'console_errors':0}
            assert service.jobs.get_publication('tenant-1',outcome.job_id) is None
            print('assessment_browser_https='+json.dumps(observed))
    finally:
        if browser is not None and browser.poll() is None:
            browser.kill();browser.communicate(timeout=5)
        server.should_exit=True;thread.join(timeout=15)
        assert not thread.is_alive()
