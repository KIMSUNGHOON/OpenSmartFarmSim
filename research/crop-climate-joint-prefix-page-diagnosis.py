"""Actual TLS page failure localization; private diagnostic, no production change."""
from pathlib import Path
from hashlib import sha256
import json,os,sys,threading,time
from urllib.parse import urlencode
import pytest
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'backend/tests'))
pytest_plugins=['test_crop_climate_joint_prefix_runtime']
import test_crop_climate_joint_prefix_runtime as reference
from app import crop_climate_joint_prefix as prefix
from app import api_crop_climate_joint_prefix_routes as routes

@reference.LOGIN
def test_actual_page_diagnosis(prefix_native,tmp_path):
    c=prefix_native
    trace=[];calls=[];starts={};rounds=[];snapshots=[];previous_bundle=None;previous_head=None
    files={str(Path(module.__file__)):name for name,module in (
        ('prefix',prefix),('query',prefix.execution),('custody',prefix.custody),('storage',prefix.storage),('routes',routes))}
    def observe(frame,event,arg):
        nonlocal previous_bundle,previous_head
        file=frame.f_code.co_filename
        if file not in files:return None
        frame.f_trace_lines=False
        key=id(frame);name=frame.f_code.co_name
        if event=='call':
            starts[key]=time.monotonic()
            if files[file]=='prefix' and name=='read':previous_bundle=None;previous_head=None
        elif event=='exception':
            kind,error,_=arg
            if kind.__name__ not in ('GeneratorExit','StopIteration'):
                trace.append({'module':files[file],'function':name,'line':frame.f_lineno,'exception':kind.__name__,'at_monotonic':time.monotonic()})
        elif event=='return':
            if files[file]=='query' and name=='_bundle' and arg is not None:
                row=arg[0];changed=[] if previous_bundle is None else sorted(k for k in row if row[k]!=previous_bundle[k])
                snapshots.append({'module':'query','fn':name,'changed_job_fields':changed,'state':row['state'],'attempt':row['attempt_count'],'cancel_requested':row['cancel_requested'],'latest_sequence':arg[1]['reason']['publication_sequence'] if arg[1] else None,'at_monotonic':time.monotonic()});previous_bundle=dict(row)
            if files[file]=='storage' and name=='_head' and arg is not None:
                head,digest=arg;snapshots.append({'module':'storage','fn':name,'head_changed':previous_head is not None and previous_head!=digest,'commits':head['commit_count'],'has_terminal_artifact':head['artifact_sha256'] is not None,'at_monotonic':time.monotonic()});previous_head=digest
            started=starts.pop(key,None)
            if started is not None and name in ('read','_accepted','_current','_load','_guard','_selected'):
                calls.append({'module':files[file],'function':name,'seconds':time.monotonic()-started})
        assert len(trace)<3000 and len(calls)<10000
        return observe
    previous=threading.gettrace();threading.settrace(observe)
    pack,factory=reference.unpaused_consumer(c,tmp_path)
    transient=0;accepted=0;sample_ok=0;event_ok=0
    try:
        with reference.served(c.prefix_runtime,c.config.certificate) as (send,replies):
            status,raw=send('POST',reference.POST,c.raw);assert status==202;job=json.loads(raw)['job_id'];path='/v1/jobs/'+job+'/crop-climate-joint-execution'
            with reference.consumer.legacy.process_consumer(tmp_path,'joint_operator:build') as (process,events,errors):
                end=time.monotonic()+180
                while True:
                    assert time.monotonic()<end and process.poll() is None
                    start=len(trace);started=time.monotonic();status,raw=send('GET',path+'/prefix');value=json.loads(raw)
                    rounds.append({'view':'summary','status':status,'seconds':time.monotonic()-started,'trace_start':start,'trace_end':len(trace),'sha256':sha256(raw).hexdigest(),'prefix_status':value.get('prefix_status')})
                    assert status in (200,503),raw
                    if status==503:transient+=1;continue
                    if value['prefix_status']=='closed':break
                    if value['prefix_status']!='accepted':continue
                    accepted+=1;selector=value['reference']['selector']
                    for view in ('events','samples'):
                        start=len(trace);started=time.monotonic();status,raw=send('GET',path+'/prefix/'+view+'?'+urlencode(selector));value=json.loads(raw)
                        rounds.append({'view':view,'status':status,'seconds':time.monotonic()-started,'trace_start':start,'trace_end':len(trace),'sha256':sha256(raw).hexdigest(),'selector':selector,'records':len(value['page']['records']) if status==200 else None})
                        assert status in (200,409,503),raw
                        if status==503:transient+=1
                        elif status==200:
                            assert value['reference']['selector']==selector
                            if view=='samples':sample_ok+=1
                            else:event_ok+=1
                reference.consumer.legacy.wait_for(lambda:bool(list(tmp_path.glob('attempt-*.private.json'))),process,timeout=30)
            assert process.returncode==0 and errors==['']
            attempts=reference.proofs(tmp_path);assert attempts[-1]['state']=='succeeded'
        assert transient>0 and accepted>0
        reference.save('page-diagnosis-differentials',{'API_mocking':False,'verified_TLS':True,'actual_SCRAM':True,'unpaused_worker':True,'worker_chunk_budget':8,'API_thread_exception_tracing':True,'worker_traced':False,'job_terminal':'succeeded','worker_actual_exit':process.returncode,'accepted_summaries':accepted,'event_pages_200':event_ok,'sample_pages_200':sample_ok,'transient_503':transient,'rounds':rounds,'exceptions':trace,'calls':calls,'snapshots':snapshots,'replies':replies,'attempts':attempts})
    finally:
        threading.settrace(previous);pack.unlink();(tmp_path/'proof.private.json').unlink()
