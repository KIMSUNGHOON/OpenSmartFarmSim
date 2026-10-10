"""Prefix HTTP control flow, actual SCRAM and verified TLS original responses."""
import asyncio
from copy import deepcopy
from datetime import timedelta
from hashlib import sha256
import json
import os
from pathlib import Path
import subprocess
import sys
import threading
from types import SimpleNamespace
from urllib.parse import urlencode
from uuid import uuid4

from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
import pytest

from app import api
from app import api_crop_climate_joint_prefix_routes as route
from app import api_crop_climate_joint_prefix as public
from app import crop_climate_joint_prefix as model
from app.http_identity import current_principal
from app.runtime_roles import RolePolicyHold
from test_api_crop_cycle_route import protect, TOKEN, NOW
from test_http_identity import request
from test_api_crop_climate_joint_execution import (
    native as execution_native, query_setup, worker_setup, producer_setup, farm_setup, profiles,
    login_database, original_login_scope, login_scope, query_cleanup, authoring, base_authoring,
    tls_files, served)
import test_crop_climate_joint_execution_query as reference

JOB = '11111111-1111-4111-8111-111111111111'
PATH = '/v1/jobs/'+JOB+'/crop-climate-joint-execution/prefix'
SELECTOR = {'publication_sequence': 1, 'head_sha256': 'a'*64, 'proof_sha256': 'b'*64}


def save(name, value):
    root = os.environ.get('OSSF_JOINT_PREFIX_HTTP_EVIDENCE')
    if root:
        with (Path(root)/(name+'.json')).open('x') as f:
            os.fchmod(f.fileno(), 0o400); json.dump(value, f, sort_keys=True, indent=2)
            f.flush(); os.fsync(f.fileno())


def authorized(*scopes):
    p = current_principal()
    if p is None: return None, api._error(401, 'unauthenticated', 'Authentication required')
    if any(s not in p['scopes'] for s in scopes): return None, api._error(403, 'forbidden', 'Resource access denied')
    return p['tenant_id'], None


def assembly(monkeypatch, scopes=route.PROGRESS_SCOPES):
    trace = []; clock = {'now': NOW}; state = {'raw': b'{}', 'error': None, 'hook': None, 'missing': False, 'tenant': 'tenant-1'}
    jobs = SimpleNamespace(principal_provider=current_principal); farms = object()
    server = SimpleNamespace(binding=SimpleNamespace(jobs=jobs, farms=farms))
    store = object.__new__(model.execution.storage.JointCropClimateResultStore); store.jobs=jobs;store.server=server
    original = object.__new__(model.execution.JointExecutionQuery); original.jobs=jobs;original.server=server;original.results=store
    query = object.__new__(model.JointExecutionPrefixQuery); query.query=original;query.jobs=jobs;query.server=server
    monkeypatch.setattr(query, '_binding', lambda: None); monkeypatch.setattr(store, '_binding', lambda: None)
    def read(tenant, job_id, **options):
        trace.append((tenant, job_id, options)); assert current_principal()['tenant_id']=='tenant-1'
        if state['hook']: state['hook']()
        if state['error']: raise state['error']
        return None if state['missing'] else object()
    monkeypatch.setattr(query, 'read', read)
    monkeypatch.setattr(public, 'project_prefix', lambda value: value)
    monkeypatch.setattr(public, '_public_bytes', lambda _: state['raw'])
    monkeypatch.setattr(route, '_current_after_projection', lambda *_: None)
    def account(*scopes):
        tenant, denied = authorized(*scopes)
        return (state['tenant'] if tenant else None), denied
    app=FastAPI()
    @app.exception_handler(RequestValidationError)
    async def rejected(*_): return api._error(422, 'invalid_request', 'Invalid request')
    args=dict(jobs=jobs,farms=farms,store=store,query=query,principal_provider=current_principal,
        authorized_tenant=account,error=api._error,access=api._access)
    route.install_joint_prefix_routes(app, **args)
    return SimpleNamespace(app=protect(app, tenant='tenant-1', scopes=scopes, clock=lambda:clock['now']),
        core=app, args=args, state=state, clock=clock, trace=trace)


def call(c, view='summary', *, query=None, body=b'', headers=None, job=JOB):
    suffix='' if view=='summary' else '/'+view
    if query is None: query=b'' if view=='summary' else urlencode(SELECTOR).encode()
    return asyncio.run(request(c.app,path='/v1/jobs/'+job+'/crop-climate-joint-execution/prefix'+suffix,
        query=query,body=body,headers=headers if headers is not None else [(b'authorization',b'Bearer '+TOKEN)]))


@pytest.mark.parametrize('fault', ['query', 'no-query', 'original', 'store', 'jobs', 'farms', 'principal', 'query-jobs',
    'query-server', 'store-jobs', 'store-server', 'binding-jobs', 'binding-farms', 'query-pin', 'store-pin'])
def test_mixed_or_missing_assembly_rejected(monkeypatch, fault):
    c=assembly(monkeypatch);args=c.args.copy();q=args['query'];s=args['store']
    if fault in ('query','store','jobs','farms'):args[fault]=object()
    elif fault=='no-query':args['query']=None
    elif fault=='original':q.query=object()
    elif fault=='principal':args['principal_provider']=lambda:None
    elif fault=='query-jobs':q.jobs=object()
    elif fault=='query-server':q.server=object()
    elif fault=='store-jobs':s.jobs=object()
    elif fault=='store-server':s.server=object()
    elif fault=='binding-jobs':q.server.binding.jobs=object()
    elif fault=='binding-farms':q.server.binding.farms=object()
    else:
        def denied():raise RuntimeError('private diagnostic')
        monkeypatch.setattr(q if fault=='query-pin' else s,'_binding',denied)
    with pytest.raises(ValueError,match='^trusted joint prefix reader required$'):
        route.install_joint_prefix_routes(FastAPI(),**args)


@pytest.mark.parametrize('view',['summary','samples','events'])
@pytest.mark.parametrize('fault',['body','extra','duplicate','id','uppercase'])
def test_invalid_request_never_dispatches(monkeypatch,view,fault):
    c=assembly(monkeypatch);query=b'' if view=='summary' else urlencode(SELECTOR).encode()
    if fault=='extra':query+=b'&private=x' if query else b'private=x'
    if fault=='duplicate':query+=b'&head_sha256='+b'a'*64 if query else b'x=1&x=2'
    job='invalid' if fault=='id' else 'AAAAAAAA-AAAA-4AAA-8AAA-AAAAAAAAAAAA' if fault=='uppercase' else JOB
    assert call(c,view,query=query,job=job,body=b'{}' if fault=='body' else b'')[0]==422 and not c.trace


@pytest.mark.parametrize('view',['samples','events'])
@pytest.mark.parametrize('fault',['missing','zero-sequence','too-large-sequence','noncanonical','float','bool','bad-head','bad-proof',
    'zero-limit','large-limit','bool-offset','large-offset','negative','duplicate'])
def test_page_selector_bounds_before_dispatch(monkeypatch,view,fault):
    c=assembly(monkeypatch);p=SELECTOR.copy()
    if fault=='missing':del p['proof_sha256']
    elif fault=='zero-sequence':p['publication_sequence']=0
    elif fault=='too-large-sequence':p['publication_sequence']=4100
    elif fault=='noncanonical':p['publication_sequence']='01'
    elif fault=='float':p['publication_sequence']='1.0'
    elif fault=='bool':p['publication_sequence']='true'
    elif fault=='bad-head':p['head_sha256']='A'*64
    elif fault=='bad-proof':p['proof_sha256']='b'*63
    elif fault=='zero-limit':p['limit']=0
    elif fault=='large-limit':p['limit']=65 if view=='samples' else 9
    elif fault=='bool-offset':p['start']='true'
    elif fault=='large-offset':p['start']=513 if view=='samples' else 129
    elif fault=='negative':p['start']=-1
    query=urlencode(p).encode()
    if fault=='duplicate':query+=b'&publication_sequence=1'
    assert call(c,view,query=query)[0]==422 and not c.trace


@pytest.mark.parametrize('view',['summary','samples','events'])
@pytest.mark.parametrize('missing',['authentication','metadata','crop_result_read'])
def test_unauthorized_never_dispatches(monkeypatch,view,missing):
    scopes=set(route.PROGRESS_SCOPES)-{missing};c=assembly(monkeypatch,scopes=scopes)
    assert call(c,view,headers=[] if missing=='authentication' else None)[0]==(401 if missing=='authentication' else 403)
    assert not c.trace and current_principal() is None


@pytest.mark.parametrize('view',['summary','samples','events'])
@pytest.mark.parametrize('failure,status',[(PermissionError,403),(model.JointPrefixSelectionConflict,409),
    (model.JointPrefixRequestRejected,422),(model.JointPrefixHold,422),(public.ProjectionHold,422),
    (model.JointPrefixPending,503),(model.custody.farms.JointFarmBindingHold,422),(RolePolicyHold,503),(RuntimeError,503)])
def test_fixed_failures_and_post_account_check(monkeypatch,view,failure,status):
    c=assembly(monkeypatch);c.state['error']=failure('private failure detail')
    response=call(c,view);assert response[0]==status and 'private failure detail' not in json.dumps(response[1])
    assert response[2][b'cache-control']==b'no-store'


@pytest.mark.parametrize('withdraw',['credential','tenant'])
@pytest.mark.parametrize('failure',[False,True])
def test_late_identity_hides_success_and_failure(monkeypatch,withdraw,failure):
    c=assembly(monkeypatch)
    def changed():
        if withdraw=='credential':c.clock['now']+=timedelta(hours=1)
        else:c.state['tenant']='foreign'
        if failure:raise RuntimeError('private failure')
    c.state['hook']=changed
    assert call(c)[0]==(401 if withdraw=='credential' else 403)


def test_missing_response_cap_and_default_page_options(monkeypatch):
    c=assembly(monkeypatch);c.state['missing']=True;assert call(c)[0]==404
    c.state['missing']=False
    for raw in (None,'private',b'',b' '* (public.MAX_RESPONSE_BYTES+1)):
        c.state['raw']=raw;assert call(c)[0]==503
    c.state['raw']=b'{}'
    for view,maximum in [('samples',64),('events',8)]:
        status,_,headers=call(c,view);assert status==200
        assert c.trace[-1]==('tenant-1',JOB,{'selector':SELECTOR,'view':view,'start':0,'limit':maximum})
        assert headers[b'cache-control']==b'no-store' and headers[b'x-ossf-joint-prefix-version']==public.VERSION.encode()


@pytest.mark.parametrize('view',['summary','samples','events'])
def test_body_disconnect_before_dispatch(monkeypatch,view):
    c=assembly(monkeypatch);sent=[];path=PATH+('' if view=='summary' else '/'+view)
    async def receive():return {'type':'http.disconnect'}
    async def send(message):sent.append(message)
    asyncio.run(c.app(dict(type='http',asgi={'version':'3.0'},method='GET',path=path,raw_path=path.encode(),root_path='',
        query_string=b'' if view=='summary' else urlencode(SELECTOR).encode(),headers=[(b'authorization',b'Bearer '+TOKEN)],
        scheme='https',http_version='1.1',server=('test',443),client=('test',1234)),receive,send))
    assert sent[0]['status']==422 and not c.trace and current_principal() is None


@pytest.mark.parametrize('mode',['cancel','send-failure'])
def test_disconnected_request_releases_thread_and_identity(monkeypatch,mode):
    c=assembly(monkeypatch);entered=threading.Event();release=threading.Event();closed=threading.Event();after=[]
    def blocked():
        try:entered.set();assert release.wait(5);after.append(current_principal())
        finally:closed.set()
    c.state['hook']=blocked
    async def exercise():
        async def receive():return dict(type='http.request',body=b'',more_body=False)
        async def send(_):
            if mode=='send-failure':raise RuntimeError('owned disconnected transport')
        task=asyncio.create_task(c.app(dict(type='http',asgi={'version':'3.0'},method='GET',path=PATH,raw_path=PATH.encode(),
            root_path='',query_string=b'',headers=[(b'authorization',b'Bearer '+TOKEN)],scheme='https',http_version='1.1',
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


def test_openapi_explicit_only_and_fresh_module_import(monkeypatch):
    c=assembly(monkeypatch);doc=c.core.openapi()
    for suffix in ('','/samples','/events'):
        op=doc['paths'][route.PREFIX_PATH+suffix]['get'];assert op['x-ossf-required-scopes']==list(route.PROGRESS_SCOPES)
        assert op['security']==[{'ServiceBearer':[]}] and op['x-ossf-max-response-bytes']==2*1024**2
        if suffix:
            p={p['name']:p for p in op['parameters'] if p['in']=='query'}
            assert set(p)=={'publication_sequence','head_sha256','proof_sha256','start','limit'}
            assert all(p[k]['required'] for k in SELECTOR)
    from app.api_openapi import contract_document
    baseline=json.loads((Path(__file__).resolve().parents[2]/'contracts/openapi-v1.json').read_bytes())
    current=contract_document();assert current['paths']==baseline['paths'] and current['components']['schemas']==baseline['components']['schemas']
    script='''import sys,os,socket,psycopg,json
before=len(os.listdir('/proc/self/fd'))
def denied(*a,**kw):raise AssertionError('unexpected connection')
socket.create_connection=denied;psycopg.connect=denied
import app.api_crop_climate_joint_prefix_routes
assert 'app.crop_climate_joint_prefix' not in sys.modules and 'app.api_crop_climate_joint_prefix' not in sys.modules
assert len(os.listdir('/proc/self/fd'))==before
print(json.dumps({'operational_prefix_imports':0,'connections':0,'FD_unchanged':True}))
'''
    child=subprocess.run([sys.executable,'-B','-c',script],capture_output=True,timeout=30)
    assert child.returncode==0,child.stderr.decode();save('schema',{'paths':3,'existing_paths':len(baseline['paths']),
        'existing_schemas':len(baseline['components']['schemas']),'original_default_contract_unchanged':True,'fresh':json.loads(child.stdout)})


@pytest.fixture
def native(execution_native,monkeypatch):
    c=execution_native;c.prefix=model.JointExecutionPrefixQuery(c.query)
    route.install_joint_prefix_routes(c.app,jobs=c.worker.jobs,farms=c.worker.server.binding.farms,store=c.worker.results,
        query=c.prefix,principal_provider=c.worker.jobs.principal_provider,authorized_tenant=authorized,error=api._error,access=api._access)
    c.captured=[];original=public._public_bytes
    def capture(value):
        raw=original(value);c.captured.append(raw);return raw
    monkeypatch.setattr(public,'_public_bytes',capture)
    return c


@reference.reference.pytestmark
def test_actual_running_original_HTTPS_pages_and_selection(native,tls_files,monkeypatch):
    c=native;path='/v1/jobs/'+c.job+'/crop-climate-joint-execution/prefix'
    with served(c,tls_files,scopes=set(route.PROGRESS_SCOPES)) as (http,replies):
        status,raw=http('GET',path);assert status==200 and json.loads(raw)['prefix_status']=='none'
        c.mode['preparing']=True;lease=reference.confirm(c.worker,c.job);progress=json.loads(c.worker.server.advance('tenant-1',c.raw,budget=8))
        accepted=c.worker.checkpoints.confirm('tenant-1',c.job,attempt=1,lease_token=lease['lease_token']);c.mode['preparing']=False
        pin={k:accepted['checkpoint'][k] for k in SELECTOR};before=reference.persisted_digest(c.worker.jobs)
        with monkeypatch.context() as patch:
            calls=reference.forbid(patch)
            for view in ('summary','samples','events'):
                target=path if view=='summary' else path+'/'+view+'?'+urlencode(pin)
                status,raw=http('GET',target);assert status==200 and raw==c.captured[-1]
                value=json.loads(raw);assert value['reference']['selector']==pin
                assert value['reference']['checkpoint']['computed_through_utc']==progress['times']['last_confirmed']['at']
                if view=='samples':assert len(value['page']['records'])==progress['counts']['samples']
            assert http('GET',path+'/samples?'+urlencode(dict(pin,start=progress['counts']['samples'])))[0]==200
            assert http('GET',path+'/samples?'+urlencode(dict(pin,start=512)))[0]==422
            assert http('GET',path+'/samples?'+urlencode(dict(pin,proof_sha256='0'*64)))[0]==409
            assert http('GET','/v1/jobs/'+str(uuid4())+'/crop-climate-joint-execution/prefix')[0]==404
            c.mode['preparing']=True
            with c.worker.server._open('tenant-1',c.raw,False):
                c.mode['preparing']=False
                try:assert http('GET',path)[0]==503
                finally:c.mode['preparing']=True
            c.mode['preparing']=False
            assert all(n==0 for n in calls.values())
        assert reference.persisted_digest(c.worker.jobs)==before
    save('actual-running',{'actual_scram':True,'verified_TLS':True,'same_original_projection_wire':True,
        'read_scopes_only':True,'selector_and_UTC':True,'empty_end_and_ranges':True,'unaccepted_selector_409':True,
        'missing_404':True,'real_lock_503':True,'DB_unchanged':True,'calls':calls,'replies':replies})


@reference.reference.pytestmark
def test_actual_late_rights_and_owner_cancel(native,tls_files,monkeypatch):
    c=native;lease=reference.confirm(c.worker,c.job);c.worker.server.advance('tenant-1',c.raw,budget=2)
    c.worker.checkpoints.confirm('tenant-1',c.job,attempt=1,lease_token=lease['lease_token'])
    path='/v1/jobs/'+c.job+'/crop-climate-joint-execution';original=public._public_bytes
    with served(c,tls_files,scopes=set(route.PROGRESS_SCOPES)) as (http,replies):
        with monkeypatch.context() as patch:
            calls=reference.forbid(patch)
            def revoke(value):
                raw=original(value);c.value[5].allowed=False;return raw
            patch.setattr(public,'_public_bytes',revoke)
            assert http('GET',path+'/prefix')[0]==422 and all(n==0 for n in calls.values())
        c.value[5].allowed=False
    with served(c,tls_files,scopes={'cancel'}) as (http,cancel_replies):
        assert http('GET',path+'/prefix')[0]==403
        status,raw=http('POST',path+'/cancel');assert status==200 and json.loads(raw)['cancel_requested']
    c.value[5].allowed=True
    with served(c,tls_files,scopes=set(route.PROGRESS_SCOPES)) as (http,closed_replies):
        with monkeypatch.context() as patch:
            calls=reference.forbid(patch);status,raw=http('GET',path+'/prefix')
            assert status==200 and json.loads(raw)['prefix_status']=='closed' and json.loads(raw)['reference'] is None
            assert all(n==0 for n in calls.values())
    save('actual-rights-cancel',{'actual_scram':True,'verified_TLS':True,'rights_revoked_after_projection_422':True,
        'owner_cancel_without_read_or_display_rights':True,'cancel_closes_values':True,'calls':calls,'replies':replies+cancel_replies+closed_replies})


@reference.reference.pytestmark
def test_actual_independent_cancel_after_projection_is_pending(native,tls_files,tmp_path,monkeypatch):
    c=native;lease=reference.confirm(c.worker,c.job);c.worker.server.advance('tenant-1',c.raw,budget=2)
    c.worker.checkpoints.confirm('tenant-1',c.job,attempt=1,lease_token=lease['lease_token'])
    pack=reference.reference.producer.fresh_pack(tmp_path,c.value,c.worker.server.inspect('tenant-1',c.raw),c.worker.server)
    value=json.loads(pack.read_bytes());value.update(job_id=c.job,phase='reader');pack.write_text(json.dumps(value))
    script=reference.reference.FRESH_WORKER.split('with MonkeyPatch.context()')[0]+'''
assert jobs.cancel('tenant-1',p['job_id'])
with jobs.connect() as conn:assert conn.pgconn.used_password and conn.info.get_parameters()['require_auth']=='scram-sha-256'
print(json.dumps({'actual_scram':True,'independent_cancel_accepted':True}))
'''
    original=route._current_after_projection;observed=[]
    def changed(*args):
        child=subprocess.run([sys.executable,'-B','-c',script,str(pack)],capture_output=True,stdin=subprocess.DEVNULL,
            timeout=120,env=dict(os.environ,PYTHONPATH=reference.reference.producer.FRESH_PYTHONPATH))
        assert child.returncode==0,child.stderr.decode();observed.append(json.loads(child.stdout));return original(*args)
    try:
        with served(c,tls_files,scopes=set(route.PROGRESS_SCOPES)) as (http,replies):
            with monkeypatch.context() as patch:
                calls=reference.forbid(patch);patch.setattr(route,'_current_after_projection',changed)
                assert http('GET','/v1/jobs/'+c.job+'/crop-climate-joint-execution/prefix')[0]==503
                assert len(observed)==1 and all(n==0 for n in calls.values())
    finally:pack.unlink();(tmp_path/'proof.private.json').unlink()
    save('actual-concurrent-cancel',{'actual_scram':True,'verified_TLS':True,'external_process':observed[0],
        'serialized_values_withheld':True,'reader_calls':calls,'DB_delta_is_external_cancel':True,'replies':replies})


@reference.reference.pytestmark
@pytest.mark.parametrize('producer_setup',['normal','hold'],indirect=True)
def test_actual_terminal_prefix_closed_existing_result(native,tls_files,monkeypatch):
    c=native;c.worker.server.advance('tenant-1',c.raw,budget=128);outcome=c.worker.run_once(c.job)
    path='/v1/jobs/'+c.job+'/crop-climate-joint-execution';before=reference.persisted_digest(c.worker.jobs)
    with served(c,tls_files,scopes=set(route.PROGRESS_SCOPES)) as (http,replies):
        with monkeypatch.context() as patch:
            calls=reference.forbid(patch);status,raw=http('GET',path+'/prefix')
            assert status==200 and json.loads(raw)['prefix_status']=='closed' and json.loads(raw)['reference'] is None
            status,raw=http('GET',path);assert status==200 and json.loads(raw)['result']['result_id']==outcome.result_id
            assert all(n==0 for n in calls.values())
    assert reference.persisted_digest(c.worker.jobs)==before
    save('actual-terminal-'+outcome.state,{'actual_scram':True,'verified_TLS':True,'prefix_closed':True,
        'same_existing_result_ID':True,'DB_unchanged':True,'calls':calls,'replies':replies})
