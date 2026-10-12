"""HTTP control flow and actual SCRAM/verified TLS execution lifecycle."""
import asyncio
from contextlib import contextmanager
from copy import deepcopy
from datetime import timedelta
from hashlib import sha256
import http.client
import json
import logging
import os
from pathlib import Path
import ssl
import subprocess
import sys
import threading
import time
from types import SimpleNamespace
from uuid import uuid4

from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
import pytest

from app import api
from app import api_crop_greenhouse_ventilation_execution as route
from app import crop_greenhouse_ventilation_execution_query as model
from app.api_openapi import _SchemaOnlyStores, contract_document
from app.http_identity import current_principal
from app.https_service import HttpsApiService
from app.runtime_roles import RolePolicyHold
from test_api_crop_cycle_route import protect, TOKEN, NOW
from test_api_serve import tls_files
from test_http_identity import request
from test_api_crop_greenhouse_ventilation_route import authoring, base_authoring, fd_inventory
from test_crop_greenhouse_ventilation_execution_query import (setup as query_setup, worker_setup,
    producer_setup, farm_setup, profiles, login_database, original_login_scope, login_scope, query_cleanup)
import test_crop_greenhouse_ventilation_execution_query as reference

POST = '/v1/crop-greenhouse-ventilation-executions'
JOB = '11111111-1111-4111-8111-111111111111'
PATH = '/v1/jobs/'+JOB+'/crop-greenhouse-ventilation-execution'
SCOPES = set(route.SUBMIT_SCOPES+route.PROGRESS_SCOPES+route.CANCEL_SCOPES)
BODY = {'study_id':'study','revision':'r1',
    'farm':{'scenario_id':'farm','scenario_revision':'r1','registration_sha256':'a'*64,'crop_id':'crop'},
    'input':{'schema_version':route.SOURCE_VERSION,'program_id':'program', **{k:'b'*64 for k in
        ('source_sha256','context_sha256','time_binding_sha256','evidence_sha256')}},
    'rights':{'schema_version':route.RIGHTS_VERSION,'declaration_id':'owned','revision':'r1',
        'input_source_sha256':'b'*64,'available_at':'2026-10-01T00:00:00.123456Z','redistribute':False,
        **{k:True for k in ('ownership_asserted','access','store','transform','use','display')}}}


def call(app, operation='get', *, job_id=JOB, body=None, query=b'', headers=None):
    path = POST if operation=='submit' else '/v1/jobs/'+job_id+'/crop-greenhouse-ventilation-execution'+('/cancel' if operation=='cancel' else '')
    if body is None: body = route._canonical(BODY) if operation=='submit' else b''
    if headers is None:
        headers=[(b'authorization',b'Bearer '+TOKEN)]
        if operation=='submit':headers.append((b'content-type',b'application/json'))
    return asyncio.run(request(app,method='GET' if operation=='get' else 'POST',path=path,body=body,query=query,headers=headers))


def save(name,value):
    root=os.environ.get('OSSF_VENTILATION_EXECUTION_HTTP_EVIDENCE')
    if root:
        with (Path(root)/(name+'.json')).open('x') as f:
            os.fchmod(f.fileno(),0o400);json.dump(value,f,sort_keys=True,indent=2);f.flush();os.fsync(f.fileno())


def assembly(monkeypatch, *, scopes=SCOPES):
    trace=[];clock={'now':NOW};state={'error':None,'raw':b'{}','tenant':'tenant-1','hook':None,'exists':True}
    row={'job_id':JOB,'stage':'simulation','state':'queued','attempt_count':0,'max_attempts':3,
        'created_at':NOW,'updated_at':NOW,'reason':None,'cancel_requested':False,'input_bytes':route._canonical({'input_version':route.INPUT_VERSION})}
    def hook():
        if state['hook']:state['hook']()
        if state['error']:raise state['error']
    jobs=SimpleNamespace(principal_provider=current_principal,_table=lambda _:route.sql.Identifier('unused'),_verified_input=lambda r:r['input_bytes'])
    class Connection:
        def execute(self,statement,args=None):
            if isinstance(statement,str):return SimpleNamespace(fetchone=lambda:{'at':clock['now']})
            return SimpleNamespace(fetchone=lambda:deepcopy(row) if state['exists'] and args==('tenant-1',JOB) else None)
    @contextmanager
    def connect():yield Connection()
    jobs.connect=connect
    def canceled(tenant,job):
        trace.append(('cancel',tenant,job));hook()
        if row['state'] in ('succeeded','hold','failed','canceled'):return False
        if row['state']=='queued':row['state']='canceled';row['reason']={'code':'canceled_by_request'}
        else:row['cancel_requested']=True
        return True
    jobs.cancel=lambda *_:pytest.fail('ventilation route called unscoped cancellation')
    farms=object();binding=SimpleNamespace(farms=farms);server=SimpleNamespace(binding=binding,input_resolver=object())
    store=object.__new__(model.storage.VentilationResultStore);store.server=server
    admission=object.__new__(model.checkpoints.execution.VentilationExecutionService)
    admission.jobs=jobs;admission.binding=binding;admission.input_resolver=server.input_resolver
    monkeypatch.setattr(admission,'_binding',lambda:None)
    def submit(tenant,raw):trace.append(('submit',tenant,raw));hook();return deepcopy(row)
    monkeypatch.setattr(admission,'submit',submit)
    monkeypatch.setattr(admission,'cancel',canceled)
    query=object.__new__(model.VentilationExecutionQuery);query.results=store;query.jobs=jobs;query.server=server;query.checkpoints=SimpleNamespace(admission=admission)
    monkeypatch.setattr(query,'_binding',lambda:None)
    def read(tenant,job):trace.append(('get',tenant,job));hook();return state['raw']
    monkeypatch.setattr(query,'read',read)
    def authorized(*required):
        p=current_principal()
        if p is None:return None,api._error(401,'unauthenticated','Authentication required')
        if any(s not in p['scopes'] for s in required):return None,api._error(403,'forbidden','Resource access denied')
        return state['tenant'],None
    app=FastAPI()
    @app.exception_handler(RequestValidationError)
    async def rejected(*_):return api._error(422,'invalid_request','Invalid request')
    route.install_ventilation_execution_routes(app,jobs=jobs,farms=farms,store=store,admission=admission,query=query,
        principal_provider=current_principal,authorized_tenant=authorized,error=api._error,access=api._access)
    return SimpleNamespace(app=protect(app,tenant='tenant-1',scopes=scopes,clock=lambda:clock['now']),
        jobs=jobs,store=store,admission=admission,query=query,farms=farms,state=state,clock=clock,trace=trace,row=row)


def test_default_and_create_app_forwarding(monkeypatch):
    unused=_SchemaOnlyStores();app=protect(api.create_app(unused,unused,unused,unused,principal_provider=current_principal),scopes=SCOPES)
    for op in ('submit','get','cancel'):
        assert call(app,op)[0]==503 and call(app,op,headers=[])[0]==401
    seen=[];monkeypatch.setattr(api,'install_ventilation_execution_routes',lambda *a,**kw:seen.append(kw))
    admission,query=object(),object()
    api.create_app(unused,unused,unused,unused,principal_provider=current_principal,
        crop_greenhouse_ventilation_execution_service=admission,crop_greenhouse_ventilation_execution_query=query)
    assert len(seen)==1 and seen[0]['admission'] is admission and seen[0]['query'] is query and seen[0]['jobs'] is unused


@pytest.mark.parametrize('fault',['admission','query','no-admission','no-query','query-admission','store','jobs','farms','binding','resolver','principal','admission-pin','query-pin'])
def test_mixed_assembly_rejected(monkeypatch,fault):
    c=assembly(monkeypatch);args=dict(jobs=c.jobs,farms=c.farms,store=c.store,admission=c.admission,query=c.query,principal_provider=current_principal)
    if fault in ('admission','query','store','jobs','farms'):args[fault]=object()
    elif fault=='no-admission':args['admission']=None
    elif fault=='no-query':args['query']=None
    elif fault=='query-admission':c.query.checkpoints.admission=object()
    elif fault=='binding':c.admission.binding=object()
    elif fault=='resolver':c.admission.input_resolver=object()
    elif fault=='principal':args['principal_provider']=lambda:None
    else:
        def denied():raise RuntimeError('private authority detail')
        monkeypatch.setattr(c.admission if fault=='admission-pin' else c.query,'_binding',denied)
    with pytest.raises(ValueError,match='^trusted ventilation execution service required$'):
        route.install_ventilation_execution_routes(FastAPI(),**args,authorized_tenant=lambda *_:None,error=api._error,access=api._access)


@pytest.mark.parametrize('fault',['extra','missing','version','farm-extra','rights-int','rights-false','redistribute','wrong-source','list','duplicate','nested-duplicate','nan','utf8','too-large','media','query'])
def test_invalid_submission_never_dispatches(monkeypatch,fault):
    c=assembly(monkeypatch);body=deepcopy(BODY);headers=None;query=b'';expected=422
    if fault=='extra':body['tenant_id']='foreign'
    elif fault=='missing':del body['rights']
    elif fault=='version':body['input']['schema_version']='future'
    elif fault=='farm-extra':body['farm']['batch_id']='invented'
    elif fault=='rights-int':body['rights']['use']=1
    elif fault=='rights-false':body['rights']['use']=False
    elif fault=='redistribute':body['rights']['redistribute']=True
    elif fault=='wrong-source':body['rights']['input_source_sha256']='c'*64
    elif fault=='list':body=[]
    elif fault=='media':headers=[(b'authorization',b'Bearer '+TOKEN)];expected=415
    elif fault=='query':query=b'tenant_id=foreign'
    raw=route._canonical(body)
    if fault=='duplicate':raw=b'{"study_id":"a","study_id":"b"}'
    elif fault=='nested-duplicate':raw=raw.replace(b'"redistribute":false',b'"redistribute":false,"redistribute":false')
    elif fault=='nan':raw=b'{"x":NaN}'
    elif fault=='utf8':raw=b'\xff'
    elif fault=='too-large':raw=b' '*65537;expected=413
    assert call(c.app,'submit',body=raw,headers=headers,query=query)[0]==expected and not c.trace


@pytest.mark.parametrize('op',['get','cancel'])
@pytest.mark.parametrize('fault',['id','uppercase','extra-query','duplicate-query','body','disconnect'])
def test_invalid_empty_request_never_dispatches(monkeypatch,op,fault):
    c=assembly(monkeypatch)
    if fault=='disconnect':
        async def receive():return {'type':'http.disconnect'}
        sent=[]
        async def send(message):sent.append(message)
        path=PATH+('/cancel' if op=='cancel' else '')
        asyncio.run(c.app(dict(type='http',asgi={'version':'3.0'},method='GET' if op=='get' else 'POST',path=path,raw_path=path.encode(),
            root_path='',query_string=b'',headers=[(b'authorization',b'Bearer '+TOKEN)],scheme='https',http_version='1.1',server=('test',443),client=('test',1234)),receive,send))
        status=sent[0]['status']
    else:
        ident='bad' if fault=='id' else 'AAAAAAAA-AAAA-4AAA-8AAA-AAAAAAAAAAAA' if fault=='uppercase' else JOB
        query=b'x=1&x=2' if fault=='duplicate-query' else b'x=1' if fault=='extra-query' else b''
        status=call(c.app,op,job_id=ident,body=b'{}' if fault=='body' else b'',query=query)[0]
    assert status==422 and not c.trace and current_principal() is None


@pytest.mark.parametrize('op',['submit','get','cancel'])
@pytest.mark.parametrize('fault',['authentication','scope'])
def test_unauthorized_never_dispatches(monkeypatch,op,fault):
    c=assembly(monkeypatch,scopes=() if fault=='scope' else SCOPES)
    assert call(c.app,op,headers=[] if fault=='authentication' else None)[0]==(401 if fault=='authentication' else 403) and not c.trace


@pytest.mark.parametrize('failure,status',[(PermissionError,403),(model.VentilationExecutionQueryHold,422),
    (model.checkpoints.execution.VentilationExecutionHold,422),(model.VentilationExecutionQueryPending,503),
    (model.custody.VentilationCustodyPending,503),(RolePolicyHold,503),(RuntimeError,503),(route.JobIntentConflict,409)])
@pytest.mark.parametrize('op',['submit','get','cancel'])
def test_fixed_failures_and_post_account_check(monkeypatch,op,failure,status):
    c=assembly(monkeypatch);c.state['error']=failure('private detail')
    if op=='cancel':
        @contextmanager
        def broken():raise c.state['error'];yield
        c.jobs.connect=broken
    actual,value,headers=call(c.app,op)
    assert actual==status and 'private' not in json.dumps(value) and headers[b'cache-control']==b'no-store'


@pytest.mark.parametrize('raw,status',[(None,404),('{}',503),(b'',503),(b'x'*16385,503)])
def test_progress_bound_and_missing(monkeypatch,raw,status):
    c=assembly(monkeypatch);c.state['raw']=raw
    assert call(c.app)[0]==status and len(c.trace)==1


@pytest.mark.parametrize('state',['queued','simulating','succeeded','hold','failed','canceled'])
def test_cancellation_acceptance_and_terminal_state(monkeypatch,state):
    c=assembly(monkeypatch,scopes={'cancel'});c.row['state']=state
    status,value,_=call(c.app,'cancel');assert status==200
    assert value['cancel_accepted']==(state in ('queued','simulating'))
    assert value['job']['state']==('canceled' if state=='queued' else state)
    assert value['cancel_requested']==(state=='simulating')
    assert set(value)=={'version','scope','G0_G4','job','cancel_accepted','cancel_requested','observed_at'}


@pytest.mark.parametrize('fault',['missing','stage','version','principal'])
def test_cancel_target_refuses_other_jobs(monkeypatch,fault):
    c=assembly(monkeypatch,scopes={'cancel'})
    if fault=='missing':c.state['exists']=False
    elif fault=='stage':c.row['stage']='collection'
    elif fault=='version':c.row['input_bytes']=b'{"input_version":"future"}'
    else:c.jobs.principal_provider=lambda:None
    assert call(c.app,'cancel')[0]==(503 if fault=='principal' else 404) and not c.trace


@pytest.mark.parametrize('op',['submit','get','cancel'])
@pytest.mark.parametrize('withdraw',['credential','tenant'])
@pytest.mark.parametrize('failure',[False,True])
def test_late_identity_hides_success_and_failure(monkeypatch,op,withdraw,failure):
    c=assembly(monkeypatch)
    def changed():
        if withdraw=='credential':c.clock['now']+=timedelta(hours=1)
        else:c.state['tenant']='foreign'
        if failure:raise RuntimeError('private failure')
    c.state['hook']=changed
    assert call(c.app,op)[0]==(401 if withdraw=='credential' else 403)


def test_submission_same_tenant_raw_and_progress_headers(monkeypatch):
    c=assembly(monkeypatch);status,value,_=call(c.app,'submit')
    assert status==202 and value['job_id']==JOB and c.trace==[('submit','tenant-1',route._canonical(BODY))]
    status,value,headers=call(c.app)
    assert status==200 and value=={} and headers[b'x-ossf-ventilation-execution-query-code-sha256']==model.CODE_SHA256.encode()


@pytest.mark.parametrize('op',['get','submit'])
@pytest.mark.parametrize('mode',['cancel','send-failure'])
def test_disconnected_request_releases_thread_and_identity(monkeypatch,op,mode):
    c=assembly(monkeypatch);entered=threading.Event();release=threading.Event();closed=threading.Event();after=[]
    def blocked():
        try:entered.set();assert release.wait(5);after.append(current_principal())
        finally:closed.set()
    c.state['hook']=blocked
    async def exercise():
        path=POST if op=='submit' else PATH
        async def receive():return dict(type='http.request',body=route._canonical(BODY) if op=='submit' else b'',more_body=False)
        async def send(_):
            if mode=='send-failure':raise RuntimeError('synthetic disconnected transport')
        headers=[(b'authorization',b'Bearer '+TOKEN),(b'content-type',b'application/json')]
        task=asyncio.create_task(c.app(dict(type='http',asgi={'version':'3.0'},method='POST' if op=='submit' else 'GET',
            path=path,raw_path=path.encode(),root_path='',query_string=b'',headers=headers,scheme='https',http_version='1.1',
            server=('test',443),client=('test',1234)),receive,send))
        while not entered.is_set():await asyncio.sleep(.01)
        if mode=='cancel':
            task.cancel()
            with pytest.raises(asyncio.CancelledError):await task
        release.set()
        if mode=='send-failure':
            with pytest.raises(RuntimeError):await task
        while not closed.is_set():await asyncio.sleep(.01)
    asyncio.run(exercise());assert closed.is_set() and len(c.trace)==1 and current_principal() is None
    if mode=='cancel':assert after==[None]


def test_openapi_contract_and_no_operational_imports():
    left=route.VentilationExecutionResultFarm.model_json_schema();right=model.public.Farm.model_json_schema()
    left.pop('title');right.pop('title');assert left==right
    doc=contract_document();old=json.loads((Path(__file__).resolve().parents[2]/'contracts/openapi-v1.json').read_bytes())
    assert all(doc['paths'][p]==v for p,v in old['paths'].items() if p not in (POST,'/v1/jobs/{job_id}/crop-greenhouse-ventilation-execution','/v1/jobs/{job_id}/crop-greenhouse-ventilation-execution/cancel'))
    for p,method,scopes in ((POST,'post',route.SUBMIT_SCOPES),('/v1/jobs/{job_id}/crop-greenhouse-ventilation-execution','get',route.PROGRESS_SCOPES),
            ('/v1/jobs/{job_id}/crop-greenhouse-ventilation-execution/cancel','post',route.CANCEL_SCOPES)):
        op=doc['paths'][p][method];assert op['x-ossf-required-scopes']==list(scopes) and op['security']==[{'ServiceBearer':[]}]
    for name in ('VentilationExecutionRead','VentilationExecutionCheckpoint','VentilationExecutionCancellation'):
        assert doc['components']['schemas'][name]['additionalProperties'] is False
    code='''import socket,psycopg,sys,json,os
before=len(os.listdir('/proc/self/fd'))
def denied(*a,**kw):raise AssertionError('schema performed I/O')
psycopg.connect=denied;socket.create_connection=denied
from app.api_openapi import contract_document
assert '/v1/crop-greenhouse-ventilation-executions' in contract_document()['paths']
assert 'app.crop_greenhouse_ventilation_execution_query' not in sys.modules
assert 'app.crop_greenhouse_ventilation_execution_worker' not in sys.modules
assert len(os.listdir('/proc/self/fd'))==before
print(json.dumps({'operational_imports':0,'connections':0,'FD_unchanged':True}))
'''
    child=subprocess.run([sys.executable,'-B','-c',code],capture_output=True,timeout=30)
    assert child.returncode==0,child.stderr.decode();save('schema-import',json.loads(child.stdout))


@pytest.fixture
def native(query_setup,query_cleanup):
    query,worker,job,raw,value=query_setup;farms=worker.server.binding.farms;replay=farms.replay
    with worker.jobs.connect() as conn:
        assert conn.pgconn.used_password and conn.info.get_parameters()['require_auth']=='scram-sha-256'
    from app.crop_greenhouse_ventilation_current_query import VentilationCurrentQuery
    stored=VentilationCurrentQuery(worker.results);unused=_SchemaOnlyStores()
    app=api.create_app(worker.jobs,replay.thermal.holds,replay.thermal.runs,unused,
        principal_provider=worker.jobs.principal_provider,thermal_scenario_store=replay.thermal,farm_scenario_service=replay,
        farm_authoring_service=farms,crop_greenhouse_ventilation_result_store=worker.results,crop_greenhouse_ventilation_current_query=stored,
        crop_greenhouse_ventilation_execution_service=worker.checkpoints.admission,crop_greenhouse_ventilation_execution_query=query)
    yield SimpleNamespace(query=query,worker=worker,job=job,raw=raw,value=value,app=app,stored=stored,mode=farms._http_test_mode)
    farms._http_test_mode['preparing']=True


@contextmanager
def served(c,tls_files,*,scopes=SCOPES,clock=None):
    c.mode['preparing']=False;cert,key,_=tls_files
    server=HttpsApiService(protect(c.app,tenant='tenant-1',scopes=scopes,clock=clock),cert,key,port=0).server()
    baseline=fd_inventory()
    thread=threading.Thread(target=server.run,daemon=True);thread.start();deadline=time.monotonic()+10
    try:
        while not server.started:
            assert thread.is_alive() and time.monotonic()<deadline;time.sleep(.01)
        port=server.servers[0].sockets[0].getsockname()[1];context=ssl.create_default_context(cafile=str(cert));replies=[]
        def send_request(op,path,body=None):
            connection=http.client.HTTPSConnection('127.0.0.1',port,context=context,timeout=60);start=time.monotonic()
            try:
                headers={'Authorization':'Bearer '+TOKEN.decode()}
                if body is not None:headers['Content-Type']='application/json'
                connection.request(op,path,body=body,headers=headers);response=connection.getresponse();raw=response.read()
                assert response.getheader('Cache-Control')=='no-store'
                replies.append({'status':response.status,'bytes':len(raw),'sha256':sha256(raw).hexdigest(),'seconds':time.monotonic()-start})
                return response.status,raw
            finally:connection.close()
        yield send_request,replies
    finally:
        server.should_exit=True;thread.join(15);assert not thread.is_alive();c.mode['preparing']=True
        assert fd_inventory()==baseline
    assert current_principal() is None


@reference.reference.pytestmark
def test_native_submit_progress_and_running_cancel(native,tls_files,monkeypatch):
    c=native;path='/v1/jobs/'+c.job+'/crop-greenhouse-ventilation-execution';captured=[];original=c.query.read
    def query(*a):raw=original(*a);captured.append(raw);return raw
    monkeypatch.setattr(c.query,'read',query)
    with served(c,tls_files) as (http,replies):
        status,raw=http('POST',POST,c.raw);assert status==202 and json.loads(raw)['job_id']==c.job
        status,raw=http('GET',path);assert status==200 and raw==captured[-1] and json.loads(raw)['checkpoint_status']=='none'
        c.mode['preparing']=True;lease=reference.confirm(c.worker,c.job)
        progress=json.loads(c.worker.server.advance('tenant-1',c.raw,budget=2))
        first=c.worker.checkpoints.confirm('tenant-1',c.job,attempt=lease['attempt'],lease_token=lease['lease_token']);c.mode['preparing']=False
        with monkeypatch.context() as patch:
            calls=reference.forbid(patch);status,raw=http('GET',path);assert status==200 and raw==captured[-1]
            value=json.loads(raw);assert value['checkpoint']['computed_through_utc']==progress['times']['last_confirmed']['at']
            assert value['checkpoint']['checkpoint_recorded_at']==model._utc(first['recorded_at']) and not any(calls.values())
        status,raw=http('POST',path+'/cancel');value=json.loads(raw)
        assert status==200 and value['cancel_accepted'] and value['cancel_requested'] and value['job']['state']=='simulating'
        c.mode['preparing']=True;assert c.worker.jobs.ack_cancel('tenant-1',c.job,lease['attempt'],lease['lease_token']);c.mode['preparing']=False
        status,raw=http('POST',path+'/cancel');assert status==200 and json.loads(raw)['job']['state']=='canceled' and not json.loads(raw)['cancel_accepted']
    with c.worker.jobs.connect() as conn:assert conn.pgconn.used_password and conn.info.get_parameters()['require_auth']=='scram-sha-256'
    save('native-lifecycle',{'actual_scram':True,'verified_TLS':True,'same_job_and_original_progress_wire':True,'worker_ack_required':True,'calls':calls,'replies':replies})


@reference.reference.pytestmark
@pytest.mark.parametrize('producer_setup',['normal','hold'],indirect=True)
def test_native_terminal_result_and_existing_saved_get(native,tls_files,producer_setup,monkeypatch):
    c=native;c.worker.server.advance('tenant-1',c.raw,budget=128);outcome=c.worker.run_once(c.job)
    assert outcome.state in ('succeeded','hold');path='/v1/jobs/'+c.job+'/crop-greenhouse-ventilation-execution'
    captured=[];original=c.query.read
    def query(*a):raw=original(*a);captured.append(raw);return raw
    monkeypatch.setattr(c.query,'read',query)
    original_saved=c.stored.read('tenant-1',outcome.result_id,c.value[1]['farm'])
    with monkeypatch.context() as patch:
        cancel=type(c.worker.jobs).cancel
        calls=reference.forbid(patch)
        patch.setattr(type(c.worker.jobs),'cancel',cancel);del calls['jobs.cancel']
        with served(c,tls_files) as (http,replies):
            status,raw=http('GET',path);assert status==200 and raw==captured[-1]
            value=json.loads(raw);assert value['result']['result_id']==outcome.result_id and value['job']['state']==outcome.state
            assert value['result']['farm']['batch_id'] and value['result']['farm']['zone_id']
            from urllib.parse import urlencode
            status,raw=http('GET','/v1/crop-greenhouse-ventilation-research-results/'+outcome.result_id+'?'+urlencode(c.value[1]['farm']))
            assert status==200 and raw==original_saved
            status,raw=http('POST',path+'/cancel');value=json.loads(raw)
            assert status==200 and not value['cancel_accepted'] and value['job']['state']==outcome.state and not any(calls.values())
    save('native-terminal-'+outcome.state,{'actual_scram':True,'verified_TLS':True,'same_original_progress_wire':True,'existing_saved_GET_unchanged':True,'calls':calls,'replies':replies})


@reference.reference.pytestmark
def test_native_rights_withdrawal_preserves_owner_cancel_without_metadata(native,tls_files,monkeypatch):
    c=native;path='/v1/jobs/'+c.job+'/crop-greenhouse-ventilation-execution';c.value[5].allowed=False
    with served(c,tls_files) as (http,replies):
        assert http('GET',path)[0]==422 and http('POST',POST,c.raw)[0]==422
    with served(c,tls_files,scopes={'cancel'}) as (http,cancel_replies):
        status,raw=http('POST',path+'/cancel');assert status==200 and json.loads(raw)['job']['state']=='canceled'
    c.value[5].allowed=True
    save('native-rights-cancel',{'actual_scram':True,'verified_TLS':True,'source_rights_withdrawn':True,'cancel_only_without_metadata':True,'replies':replies+cancel_replies})
