"""One actual HTTPS progress/prefix/samples ABBA on the same original64 prefix."""
from pathlib import Path
from hashlib import sha256
from collections import Counter
from copy import deepcopy
from decimal import Decimal
import gc,json,os,sys,time
import psycopg,pytest
from urllib.parse import urlencode
R=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(R/'backend'),str(R/'backend/tests'),str(R/'research')]
from test_api_crop_greenhouse_solar_execution_http_native import (
 native,authoring,query_setup,worker_setup,producer_setup,profiles,login_database,
 original_login_scope,login_scope,query_cleanup,tls_files,served,pin)
import test_api_crop_greenhouse_solar_execution_http_native as reference
from app import crop_greenhouse_solar_storage as storage
from app import crop_greenhouse_solar_execution_query as query
from app.market_source_store import MarketSourceStore
from app import runtime_roles
import solar_query_scope_candidate as candidate
pytestmark=reference.pytestmark

@pytest.fixture(autouse=True)
def original64_packet(monkeypatch):
 inputs=reference.reference.reference.producer.reference.inputs;original=inputs.packet
 case=deepcopy(inputs.reference.reference.CASES[6])
 case.update(step_count=64,output_steps=list(range(0,65,8)))
 monkeypatch.setattr(inputs,'packet',lambda directory,profiles,origin=None:original(directory,profiles,case,origin))

def journal(row):
 with (Path(os.environ['OSSF_QUERY_SCOPE_EVIDENCE'])/'cost-journal.jsonl').open('a') as f:
  os.fchmod(f.fileno(),0o600);f.write(json.dumps(row,sort_keys=True)+'\n');f.flush();os.fsync(f.fileno())

def stable(raw):
 value=json.loads(raw);assert type(value) is dict and type(value['observed_at']) is str
 value.pop('observed_at')
 return storage._canonical(value)

def test_real_HTTPS_query_current_scope_ABBA(native,tls_files,monkeypatch):
 criteria=json.loads((R/'research/artifacts/solar-query-current-registration-scope-criteria-20261020.json').read_bytes())
 assert sha256((R/'research/solar_query_scope_candidate.py').read_bytes()).hexdigest()==criteria['candidate_SHA256']
 c=native;worker=c.worker;s=storage;continuation=s.continuation
 lease=worker.jobs.claim(600,tenant_id='tenant-1',allowed_stages=('simulation',),job_id=c.job)
 assert lease and worker._before(lease)==c.raw and worker._adopt(c.raw) is None
 journal({'phase':'warmup_started','original_CASE6_64':True,'selected_step':27})
 with worker.server._open('tenant-1',c.raw,True) as (session,prepare):
  binding=prepare();ctx=binding._context;initial=continuation.start(ctx);writer=s.ArtifactWriter(session.path)
  try:
   publish=writer._publish_head;writer._publish_head=lambda h:session._publish(writer,publish,h)
   session._guard();session._reserve('initialize');writer._create(binding,initial)
   while True:
    session._guard();session._reserve('advance');chunk=continuation.advance_chunk(ctx,writer.checkpoint,1)
    session._guard();assert chunk['status']=='yielded'
    writer.append(chunk,expected_chunk_sha256=s.clock.source_chunk_sha256(ctx,chunk))
    if chunk['steps']==27:break
   original_checkpoint=continuation.checkpoint_bytes(ctx,writer.checkpoint)
  finally:writer.close()
 first=worker._confirm(lease);selected=pin(first)
 assert first['checkpoint']['steps']==27 and first['checkpoint']['planned_steps']==64
 assert first['checkpoint']['computed_through_utc']=='2026-10-01T00:00:54.123456Z'
 before=reference.reference.persisted_digest(worker.jobs)
 monitor=sys.monitoring;slot=next(i for i in range(5,-1,-1) if monitor.get_tool(i) is None)
 execute_code=psycopg.Connection.execute.__code__
 connect_code=psycopg.Connection.connect.__func__.__code__
 prepare_code=worker.server.binding.farms._prepare.__func__.__code__
 current_code=type(worker.server.binding).current.__code__
 source_code=MarketSourceStore._select_with_job.__code__
 load_code=storage._Files._load.__code__
 role_code=runtime_roles._database.__code__
 active=False;SQL=Counter();metrics=Counter();sources=[];current=[];loads=[];rows=[]
 def observe(code,offset):
  if not active:return
  frame=sys._getframe(1);parent=frame.f_back
  if code is execute_code:
   if parent.f_code.co_name=='readonly_sql':parent=parent.f_back
   SQL[parent.f_globals.get('__name__','')+'.'+parent.f_code.co_name]+=1
  elif code is connect_code:metrics['physical_connections']+=1
  elif code is prepare_code:metrics['registration_reconstructions']+=1
  elif code is current_code:current.append([parent.f_code.co_name,parent.f_back.f_code.co_name])
  elif code is source_code:
   values=frame.f_locals;sources.append([values[k] for k in ('tenant','kind','identity','revision')])
  elif code is load_code:loads.append([parent.f_globals.get('__name__',''),parent.f_code.co_name])
  elif code is role_code:metrics['role_audits']+=1
 codes=(execute_code,connect_code,prepare_code,current_code,source_code,load_code,role_code)
 monitor.use_tool_id(slot,'actual-HTTPS-query-scope-ABBA')
 expected={};checks=[]
 try:
  monitor.register_callback(slot,monitor.events.PY_START,observe)
  for code in codes:monitor.set_local_events(slot,code,monitor.events.PY_START)
  with served(c,tls_files,scopes=set(reference.route.PROGRESS_SCOPES)) as (http,replies):
   with monkeypatch.context() as readonly:
    forbidden=reference.reference.forbid(readonly)
    for mode in criteria['order']:
     SQL.clear();metrics.clear();sources.clear();current.clear();loads.clear()
     journal({'phase':'sequence_started','mode':mode})
     with monkeypatch.context() as patch:
      if mode=='candidate':candidate.install(patch)
      gc.collect();active=True;start=time.perf_counter_ns();results={}
      try:
       for view,target in [('progress',c.path),('prefix',c.path+'/prefix'),('samples',c.path+'/prefix/samples?'+urlencode(selected))]:
        status,raw=http('GET',target);assert status==200,(view,status)
        result=json.loads(raw)
        if view=='progress':assert result['checkpoint_status']=='current' and result['checkpoint']['steps']==27
        else:assert result['prefix_status']=='accepted' and result['reference']['selector']==selected
        results[view]=stable(raw)
      finally:wall=time.perf_counter_ns()-start;active=False
     if not expected:expected=results
     else:assert expected==results
     assert all(v==0 for v in forbidden.values())
     row={'mode':mode,'wall_ns':wall,'SQL':dict(SQL),'metrics':dict(metrics),'source_count':len(sources),'ordered_sources_SHA256':sha256(json.dumps(sources,separators=(',',':')).encode()).hexdigest(),'full_current_order':list(current),'fresh_storage_load_order':list(loads),'stable_response_SHA256':{k:sha256(v).hexdigest() for k,v in results.items()}}
     rows.append(row);journal({'phase':'sequence_completed','mode':mode,'wall_ns':wall,'SQL_calls':sum(SQL.values()),'metrics':dict(metrics)})
  assert reference.reference.persisted_digest(worker.jobs)==before
 finally:
  active=False
  for code in codes:monitor.set_local_events(slot,code,0)
  monitor.register_callback(slot,monitor.events.PY_START,None);monitor.free_tool_id(slot)
 assert all(r['ordered_sources_SHA256']==rows[0]['ordered_sources_SHA256'] and r['full_current_order']==rows[0]['full_current_order'] and r['fresh_storage_load_order']==rows[0]['fresh_storage_load_order'] for r in rows)
 assert rows[0]['SQL']==rows[3]['SQL'] and rows[1]['SQL']==rows[2]['SQL']
 c.mode['preparing']=True
 current_progress=json.loads(worker.server.inspect('tenant-1',c.raw))
 assert storage._canonical(current_progress['checkpoint']['value'])==original_checkpoint
 paired=[100*(rows[a]['wall_ns']-rows[b]['wall_ns'])/rows[a]['wall_ns'] for a,b in ((0,1),(3,2))]
 mean=100*(rows[0]['wall_ns']+rows[3]['wall_ns']-rows[1]['wall_ns']-rows[2]['wall_ns'])/(rows[0]['wall_ns']+rows[3]['wall_ns'])
 out={'rows':rows,'paired_reduction_pct':paired,'mean_reduction_pct':mean,'cost_criterion_met':mean>=2 and min(paired)>0,'actual_SCRAM_verified_TLS':True,'original_CASE6_64_output0to64_by8_chunk1':True,'same_selected_yielded_step':27,'computed_through_utc':first['checkpoint']['computed_through_utc'],'original_checkpoint_SHA256':sha256(original_checkpoint).hexdigest(),'volatile_fields':['/observed_at (root of each of progress,prefix,samples)'],'all_other_public_fields_values_counts_modelUTC_equal':True,'ordered_fresh_sources_current_and_storage_reads_equal':True,'GET_data_SQL_writes_numerics_CLI':0,'DB_unchanged':True,'one_valid_timing_trial':True,'normal64_accepted':False,'new_Solar_deployed':False,'product_adopted':False}
 reference.reference.save('query-current-scope-actual-HTTPS-ABBA',out)
 journal({'phase':'trial_completed','mean_reduction_pct':mean,'pairs':paired,'cost_criterion_met':out['cost_criterion_met']})
