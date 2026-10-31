"""Protected HTTP intake -> real foreground process -> fresh original HTTP read."""
from dataclasses import asdict
from hashlib import sha256
import json
import os
from pathlib import Path
import select
import signal
import subprocess
import sys
import time

import pytest
from psycopg import Connection,sql

from app.api_runtime import ApiRuntime
from app.economic_production_batches import ProductionBatchLedger
from app.economics import EconomicLedger,canonical_scenario_sha256
from login_database import login_database,login_scope
from test_api_serve import tls_files
from test_economic_batch_runtime import runtime_inputs,RUNTIME_PROFILE,READ_TOKEN,https


def lines(path):
    return [json.loads(raw)for raw in path.read_bytes().split(b'\n')[:-1]]if path.exists()else []


@pytest.mark.parametrize('login_scope',[RUNTIME_PROFILE],indirect=True)
def test_actual_HTTPS_intake_separate_process_automatic_completion_and_fresh_read(runtime_inputs,monkeypatch,tmp_path):
    values,cfg,deps,scope=runtime_inputs;jobs,source,holds,contexts,p,s,authority,service=values
    unrelated=[jobs.submit('tenant-1','simulation',{'input_version':
        'economic-calculation-input-v1'if i%2 else 'economic-batch-calculation-input-v2'},'unrelated-'+str(i))for i in range(9)]
    p['tenant_id']='foreign'
    foreign=jobs.submit('foreign','simulation',{'input_version':'economic-batch-calculation-input-v1'},'foreign-queued')
    p['tenant_id']='tenant-1'
    runtime=ApiRuntime(cfg,deps)
    directory=tmp_path/'operator';directory.mkdir(mode=0o700)
    private=directory/'config.private.json'
    private.write_text(json.dumps({'policy':asdict(jobs.runtime_identity[0]),'dsn':jobs._dsn,
        'artifact_root':str(jobs.artifact_root),'gate_key':contexts._gate_key.hex(),
        'hold_key':holds._key.hex(),'hold_scope':holds._scope_resolver()}));private.chmod(0o600)
    root=Path(__file__).resolve().parents[1]
    env={'PATH':os.defpath,'LANG':'C.UTF-8','PYTHONDONTWRITEBYTECODE':'1','MALLOC_ARENA_MAX':'2',
        'PYTHONPATH':os.pathsep.join([str(root),str(root/'tests')]),'OSSF_BATCH_CONSUMER_TEST_CONFIG':str(private)}
    process=None;pending=bytearray();events=[];error=b''
    def event():
        deadline=time.monotonic()+30
        while b'\n'not in pending:
            assert process.poll()is None and time.monotonic()<deadline,'consumer did not report expected event'
            if select.select([process.stdout],[],[],.1)[0]:
                raw=os.read(process.stdout.fileno(),4096);assert raw,'consumer stream ended';pending.extend(raw)
        raw,_,remaining=pending.partition(b'\n');pending[:]=remaining
        value=json.loads(raw);events.append(value);return value
    try:
        with https(runtime,cfg)as call:
            body={'scenario_id':s.scenario_id,'scenario_revision':s.scenario_revision,
                'scenario_sha256':canonical_scenario_sha256(s),'idempotency_key':'http-auto-process'}
            status,raw,_=call('/v1/economic-batch-calculations',method='POST',body=body)
            assert status==202;job=json.loads(raw);path='/v1/jobs/'+job['job_id']+'/economic-batch-result'
            assert call(path,token=READ_TOKEN)[0]==404
            process=subprocess.Popen([sys.executable,'-B','-m','app.deterministic_work',
                '--factory','economic_batch_consumer_factory:build'],cwd=root,env=env,
                stdin=subprocess.DEVNULL,stdout=subprocess.PIPE,stderr=subprocess.PIPE,bufsize=0)
            assert event()=={'version':1,'event':'started'}
            attempt=event()
            assert attempt=={'version':1,'event':'attempt','job_id':job['job_id'],
                'attempt':1,'state':'succeeded','reason_code':'completed'}
            pages_path=directory/'discovery-pages.private.jsonl';deadline=time.monotonic()+20
            while True:
                assert process.poll()is None and time.monotonic()<deadline,'consumer did not finish its post-completion scan'
                pages=lines(pages_path);selected=[i for i,page in enumerate(pages)if page['job_ids']]
                assert len(selected)==1 and pages[selected[0]]['job_ids']==[job['job_id']]
                reset=next((i for i in range(selected[0]+1,len(pages))if pages[i]['cursor_is_none']),None)
                if reset is not None and any(not v['has_next_cursor']for v in pages[reset:]):break
                time.sleep(.05)
            assert all(v['scanned_count']<=2 for v in pages)
            process.send_signal(signal.SIGTERM);out,error=process.communicate(timeout=10)
            events.extend(json.loads(line)for line in(bytes(pending)+out).splitlines());pending.clear()
            assert process.returncode==0 and error==b''and events[-1]=={'version':1,'event':'stopped'}
            assert len(events)==3 and len(lines(directory/'calculation-calls.private.jsonl'))==1
        expected=jobs.read_artifact('tenant-1',job['job_id']);publication=jobs.get_publication('tenant-1',job['job_id'])
        assert len(expected)==10460
        for other in unrelated:assert jobs.get_job('tenant-1',other['job_id'])==other
        with jobs.connect()as conn:
            held=conn.execute(sql.SQL('SELECT state,attempt_count FROM {} WHERE job_id=%s').format(
                jobs._table('jobs')),(foreign['job_id'],)).fetchone()
            assert held['state']=='queued'and held['attempt_count']==0
        fresh=ApiRuntime(cfg,deps);writes=[];execute=Connection.execute
        def measured(conn,*a,**k):
            cursor=execute(conn,*a,**k)
            if(cursor.statusmessage or '').split(' ')[0]in {'INSERT','UPDATE','DELETE','MERGE','CREATE','ALTER','DROP','TRUNCATE','GRANT','REVOKE'}:writes.append(cursor.statusmessage)
            return cursor
        def fail(*a,**k):raise AssertionError('calculation during automatic result read')
        monkeypatch.setattr(Connection,'execute',measured)
        monkeypatch.setattr(ProductionBatchLedger,'calculate',fail)
        monkeypatch.setattr(EconomicLedger,'_calculate_verified',fail)
        with https(fresh,cfg)as call:
            status,raw,headers=call(path,token=READ_TOKEN)
            assert status==200 and raw==expected and not writes
            assert headers['x-ossf-publication-id']==str(publication['publication_id'])
            assert headers['x-ossf-published-at']==publication['published_at'].isoformat()
            scope['changed']=True;assert call(path,token=READ_TOKEN)[0]==422
            scope['changed']=False;assert call(path,token=READ_TOKEN)[1]==expected
            assert not writes
        receipt={'artifact_sha256':sha256(expected).hexdigest(),'artifact_bytes':len(expected),
            'publication_id':str(publication['publication_id']),'published_at':publication['published_at'].isoformat(),
            'verified_TLS_listeners':2,'actual_separate_consumer_process':True,'consumer_exit':process.returncode,
            'actual_v10_calls':1,'unrelated_queued_jobs_preserved':10,'selected_job_count':1,
            'post_completion_full_scan_selected':0,'discovery_page_count':len(pages),'page_size':2,
            'events':events,'fresh_result_amount_calls':0,'fresh_result_SQL_writes':0,
            'read_execution_scope':False,'current_evidence_hold_and_restore':True,
            'private_config_removed':True,'recursive_Codex_CLI':False,'G0_G4':'not_assessed','R2':'not_approved'}
        (tmp_path/'automatic-result-receipt.private.json').write_text(json.dumps(receipt,indent=2))
    finally:
        if process is not None and process.poll()is None:
            process.terminate()
            try:process.communicate(timeout=10)
            except subprocess.TimeoutExpired:process.kill();process.communicate(timeout=10)
        private.unlink(missing_ok=True)
    assert not private.exists()
