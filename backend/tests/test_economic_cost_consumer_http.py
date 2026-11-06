"""Verified cost HTTPS -> owned foreground process -> fresh original HTTPS read."""
from dataclasses import asdict
from datetime import datetime,timezone
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
from app.economic_cost_wire import CostArtifactRead
from app.http_identity import current_principal
from login_database import login_database,login_scope
from test_api_serve import tls_files
from test_economic_batch_calculation import request
from test_economic_batch_consumer_http import lines
from test_economic_batch_runtime import runtime_inputs,RUNTIME_PROFILE,READ_TOKEN,https
from test_economic_cost_query import no_replay


@pytest.mark.parametrize('login_scope',[RUNTIME_PROFILE],indirect=True)
def test_cost_HTTPS_intake_foreground_process_completion_and_fresh_readonly_result(runtime_inputs,monkeypatch,tmp_path):
    values,cfg,deps,scope=runtime_inputs
    jobs,source,holds,contexts,p,s,authority,base=values
    unrelated=[jobs.submit('tenant-1','simulation',{'input_version':version},'cost-auto-other-'+str(i))
        for i,version in enumerate(['economic-calculation-input-v1','economic-batch-calculation-input-v2',
            'economic-cost-line-calculation-input-v2']*2)]
    unrelated.append(base.submit('tenant-1',request(s,'cost-auto-old-batch')))
    p['tenant_id']='foreign'
    try:foreign=jobs.submit('foreign','simulation',{'input_version':'economic-cost-line-calculation-input-v1'},'cost-auto-foreign')
    finally:p['tenant_id']='tenant-1'
    runtime=ApiRuntime(cfg,deps)
    directory=tmp_path/'cost-operator';directory.mkdir(mode=0o700)
    private=directory/'config.private.json'
    with private.open('x')as handle:
        private.chmod(0o600)
        json.dump({'policy':asdict(jobs.runtime_identity[0]),'dsn':jobs._dsn,
            'artifact_root':str(jobs.artifact_root),'gate_key':contexts._gate_key.hex(),
            'hold_key':holds._key.hex(),'hold_scope':holds._scope_resolver()},handle)
    root=Path(__file__).resolve().parents[1]
    env={'PATH':os.defpath,'LANG':'C.UTF-8','PYTHONDONTWRITEBYTECODE':'1','MALLOC_ARENA_MAX':'2',
        'PYTHONPATH':os.pathsep.join([str(root),str(root/'tests')]),'OSSF_COST_CONSUMER_TEST_CONFIG':str(private)}
    process=None;pending=bytearray();events=[];error=b'';proof=None
    def event():
        deadline=time.monotonic()+45
        while b'\n'not in pending:
            assert process.poll()is None and time.monotonic()<deadline,'cost consumer did not report expected event'
            if select.select([process.stdout],[],[],.1)[0]:
                chunk=os.read(process.stdout.fileno(),4096);assert chunk,'cost consumer stream ended';pending.extend(chunk)
        encoded,_,remaining=pending.partition(b'\n');pending[:]=remaining
        value=json.loads(encoded);events.append(value);return value
    try:
        with https(runtime,cfg)as call:
            body=request(s,'cost-auto-HTTPS').model_dump(mode='json')
            with monkeypatch.context()as patch:
                no_replay(patch)
                status,accepted,_=call('/v1/economic-cost-calculations',method='POST',body=body)
                assert status==202 and call('/v1/economic-cost-calculations',method='POST',body=body)[:2]==(202,accepted)
            job=json.loads(accepted);path='/v1/jobs/'+job['job_id']+'/economic-cost-result'
            assert call(path,token=READ_TOKEN)[0]==404
            with jobs.connect()as conn:
                queued=jobs._locked_job(conn,'tenant-1',job['job_id']);original_input=jobs._verified_input(queued)
            process=subprocess.Popen([sys.executable,'-B','-m','app.deterministic_work',
                '--factory','economic_cost_consumer_factory:build'],cwd=root,env=env,
                stdin=subprocess.DEVNULL,stdout=subprocess.PIPE,stderr=subprocess.PIPE,bufsize=0)
            assert event()=={'version':1,'event':'started'}
            assert event()=={'version':1,'event':'attempt','job_id':job['job_id'],
                'attempt':1,'state':'succeeded','reason_code':'completed'}
            pages_path=directory/'discovery-pages.private.jsonl';deadline=time.monotonic()+30
            while True:
                assert process.poll()is None and time.monotonic()<deadline,'cost consumer post-completion scan did not finish'
                pages=lines(pages_path);selected=[i for i,page in enumerate(pages)if page['job_ids']]
                assert len(selected)==1 and pages[selected[0]]['job_ids']==[job['job_id']]
                reset=next((i for i in range(selected[0]+1,len(pages))if pages[i]['cursor_is_none']),None)
                if reset is not None and any(not page['has_next_cursor']for page in pages[reset:]):break
                time.sleep(.05)
            assert all(page['scanned_count']<=2 for page in pages)
            process.send_signal(signal.SIGTERM);out,error=process.communicate(timeout=10)
            events.extend(json.loads(line)for line in(bytes(pending)+out).splitlines());pending.clear()
            assert process.returncode==0 and error==b''and events[-1]=={'version':1,'event':'stopped'}
            assert len(events)==3 and len(lines(directory/'trace-calls.private.jsonl'))==1
            assert len(lines(directory/'v10-calls.private.jsonl'))==1
            expected=jobs.read_artifact('tenant-1',job['job_id']);publication=jobs.get_publication('tenant-1',job['job_id'])
            with monkeypatch.context()as patch:
                no_replay(patch)
                status,retried,_=call('/v1/economic-cost-calculations',method='POST',body=body)
                assert status==202 and json.loads(retried)['job_id']==job['job_id']
            assert jobs.get_publication('tenant-1',job['job_id'])==publication
        for other in unrelated:assert jobs.get_job('tenant-1',other['job_id'])==other
        with jobs.connect()as conn:
            foreign_row=jobs._locked_job(conn,'foreign',foreign['job_id'])
            assert foreign_row['state']=='queued'and foreign_row['attempt_count']==0
            final=jobs._locked_job(conn,'tenant-1',job['job_id'])
            assert jobs._verified_input(final)==original_input and final['created_at']==queued['created_at']
        fresh=ApiRuntime(cfg,deps);assert fresh.jobs is not runtime.jobs
        no_replay(monkeypatch);writes=[];execute=Connection.execute
        def measured(conn,*a,**k):
            cursor=execute(conn,*a,**k)
            if(cursor.statusmessage or '').split(' ')[0]in {'INSERT','UPDATE','DELETE','MERGE','CREATE','ALTER','DROP','TRUNCATE','GRANT','REVOKE'}:
                writes.append(cursor.statusmessage)
            return cursor
        monkeypatch.setattr(Connection,'execute',measured)
        with https(fresh,cfg)as call:
            status,raw,headers=call(path,token=READ_TOKEN)
            assert status==200 and raw==expected and not writes
            assert headers['cache-control']=='no-store'and headers['strict-transport-security']and'server'not in headers
            assert headers['x-ossf-publication-id']==str(publication['publication_id'])
            assert headers['x-ossf-published-at']==publication['published_at'].isoformat()
            CostArtifactRead.model_validate_json(raw)
            assert call(path,token=None)[0]==401
            scope['changed']=True;assert call(path,token=READ_TOKEN)[0]==422
            scope['changed']=False
            status,restored,restored_headers=call(path,token=READ_TOKEN)
            assert status==200 and restored==expected
            assert restored_headers['x-ossf-published-at']==headers['x-ossf-published-at']
            assert not writes and current_principal()is None
        assert jobs.get_publication('tenant-1',job['job_id'])==publication
        proof={'observed_at_UTC':datetime.now(timezone.utc).isoformat(),'job_id':job['job_id'],
            'input_sha256':queued['input_sha256'],'job_created_at':queued['created_at'].isoformat(),
            'artifact_sha256':sha256(expected).hexdigest(),'artifact_bytes':len(expected),
            'publication_id':str(publication['publication_id']),'published_at':publication['published_at'].isoformat(),
            'trace_id':json.loads(expected)['result']['trace_id'],'verified_TLS_listeners':2,
            'actual_separate_cost_consumer_process':True,'consumer_exit':process.returncode,
            'actual_trace_calls':1,'actual_v10_calls':1,'selected_job_count':1,
            'unrelated_queued_jobs_preserved':len(unrelated)+1,'post_completion_full_scan_selected':0,
            'discovery_page_count':len(pages),'page_size':2,'events':events,
            'admission_amount_calls':0,'fresh_result_amount_calls':0,'fresh_result_runtime_digest_calls':0,
            'fresh_result_SQL_writes':len(writes),'read_execution_scope':False,
            'current_evidence_hold_and_restore':True,'first_publication_preserved':True,
            'recursive_Codex_CLI':False,'actual_farm_Runs':0,'G0_G4':'not_assessed','R2':'not_approved'}
    finally:
        scope['changed']=False
        if process is not None and process.poll()is None:
            process.terminate()
            try:process.communicate(timeout=10)
            except subprocess.TimeoutExpired:process.kill();process.communicate(timeout=10)
        private.unlink(missing_ok=True)
        cfg.certificate.unlink(missing_ok=True);cfg.private_key.unlink(missing_ok=True)
    assert not private.exists()and not cfg.certificate.exists()and not cfg.private_key.exists()
    proof.update(private_config_removed=True,TLS_fixture_material_removed=True)
    (tmp_path/'automatic-cost-result-v1.json').write_bytes(expected)
    (tmp_path/'automatic-cost-receipt-v1.private.json').write_text(json.dumps(proof,indent=2)+'\n')
