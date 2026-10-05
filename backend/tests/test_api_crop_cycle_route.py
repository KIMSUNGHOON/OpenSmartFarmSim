"""ASGI route control flow with real artifacts and stubbed custody; no TLS/DB proof."""
import asyncio
from contextlib import contextmanager
from copy import deepcopy
from datetime import datetime,timedelta,timezone
import json
from pathlib import Path
import subprocess
import sys
from types import SimpleNamespace
from urllib.parse import urlencode

from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
import pytest

from app import api_crop_cycle_replay as public
from app.api import create_app,_access,_error
from app.api_openapi import _SchemaOnlyStores,contract_document
from app import crop_cycle_result_store as storage
from app import crop_cycle_server_custody as server
from app.crop_result_store import READ_SCOPES
from app.http_identity import BearerGrant,BearerRegistry,PrincipalMiddleware,current_principal,token_digest
from app.thermal_run_store import _canonical
from test_api_crop_cycle_replay import saved,program
from test_http_identity import request

PATH='/v1/crop-cycle-research-results/'
TOKEN=b'own-cycle-route-test-'+b'a'*40
NOW=datetime(2026,10,6,tzinfo=timezone.utc)


@pytest.fixture(scope='module')
def original(tmp_path_factory):return saved(tmp_path_factory.mktemp('cycle-route'),program('full-removal-reentry'))


def protect(app,*,scopes=READ_SCOPES,tenant='own-projection-tenant',clock=None):
    grant=BearerGrant(token_digest(TOKEN),tenant,frozenset(scopes),NOW,NOW+timedelta(hours=1))
    return PrincipalMiddleware(app,BearerRegistry((grant,),clock=clock or (lambda:NOW)))


def get(app,record,farm,*,query='',body=b'',headers=None):
    return asyncio.run(request(app,path=PATH+record['result_id'],query=(urlencode(farm)+query).encode(),body=body,
        headers=headers if headers is not None else [(b'authorization',b'Bearer '+TOKEN)]))


def test_default_real_app_has_authenticated_unavailable_cycle_route(original):
    record,_,_=original;farm=json.loads(record['payload_raw'])['binding']['request']['farm']
    unused=_SchemaOnlyStores()
    app=protect(create_app(unused,unused,unused,unused,principal_provider=current_principal))
    assert get(app,record,farm)[0]==503
    assert get(app,record,farm,headers=[])[0]==401


def assembly(original,monkeypatch,*,scopes=READ_SCOPES,tenant='own-projection-tenant',clock=None):
    record,terminal,pages=original;packet=json.loads(record['payload_raw']);farm=packet['binding']['request']['farm']
    trace=[];state={'allowed':True,'exists':True,'read_error':None,'current_error':None}
    jobs=SimpleNamespace(principal_provider=current_principal);farms=object()
    store=object.__new__(storage.CycleCropResultStore)
    store.jobs=jobs;store.server=SimpleNamespace(binding=SimpleNamespace(farms=farms,jobs=jobs))
    monkeypatch.setattr(store,'_binding',lambda:trace.append('binding'))
    journal=SimpleNamespace(writer=SimpleNamespace(_summary={k:deepcopy(v) for k,v in terminal.items() if k!='manifest'}),
        context=SimpleNamespace(manifest=deepcopy(terminal['manifest'])))
    expected=_canonical(packet['policies']['server_progress'])
    def guard():trace.append('guard')
    def progress():trace.append('progress');return expected
    def page(progress_raw,kind,start,limit):
        assert progress_raw==expected;trace.append('page:'+kind)
        p=deepcopy(pages[kind]);p['records']=p['records'][start:start+limit];p['start']=start;p['next']=start+len(p['records'])
        return p
    journal._guard=guard;journal._progress=progress;journal.page=page
    @contextmanager
    def read(who,result_id,farm_ref):
        trace.append('open');assert current_principal()['tenant_id']==who
        try:
            if state['read_error'] is not None:raise state['read_error']
            if not state['allowed']:raise PermissionError('private source reason')
            if farm_ref!=farm:raise server.CycleCustodyHold('private farm mismatch')
            if not state['exists'] or who!=packet['tenant_id']:yield None,None,None
            else:
                assert result_id==record['result_id'];yield record,packet,journal
        finally:trace.append('close')
    monkeypatch.setattr(store,'_read',read)
    def current(who,request_raw,selected,progress_raw,write=False):
        trace.append('current');assert selected is journal and progress_raw==expected and not write
        assert request_raw==_canonical(packet['binding']['request'])
        if state['current_error'] is not None:raise state['current_error']
        if not state['allowed']:raise PermissionError('private withdrawal reason')
    monkeypatch.setattr(store,'_current',current)
    monkeypatch.setattr(store,'get',lambda *_:pytest.fail('nested get'))
    monkeypatch.setattr(store,'page',lambda *_:pytest.fail('nested page'))
    monkeypatch.setattr(store,'summary',lambda *_:pytest.fail('nested summary'))
    def authorized(*required):
        p=current_principal()
        if p is None:return None,_error(401,'unauthenticated','Authentication required')
        if any(s not in p['scopes'] for s in required):return None,_error(403,'forbidden','Resource access denied')
        return p['tenant_id'],None
    app=FastAPI()
    @app.exception_handler(RequestValidationError)
    async def invalid(*_):return _error(422,'invalid_request','Invalid request')
    public.install_cycle_crop_routes(app,jobs=jobs,farms=farms,store=store,principal_provider=current_principal,
        authorized_tenant=authorized,error=_error,access=_access)
    return protect(app,scopes=scopes,tenant=tenant,clock=clock),store,farm,trace,state


@pytest.mark.parametrize('view',['summary','samples','events'])
def test_one_context_original_bytes_and_post_projection_rights(original,monkeypatch,view):
    app,_,farm,trace,_=assembly(original,monkeypatch)
    monkeypatch.setattr(public.engine.short._Evaluator,'rhs',lambda *_:pytest.fail('GET executed RHS'))
    original_bytes=public._public_bytes
    def bytes_checked(value):trace.append('bytes');return original_bytes(value)
    monkeypatch.setattr(public,'_public_bytes',bytes_checked)
    status,value,headers=get(app,original[0],farm,query='' if view=='summary' else '&view='+view)
    assert status==200 and value['result_id']==original[0]['result_id']
    assert trace.count('open')==trace.count('close')==trace.count('current')==1
    assert max(i for i,t in enumerate(trace) if t=='bytes')<trace.index('current')<trace.index('close')
    assert headers[b'cache-control']==b'no-store'
    if view=='summary':assert _canonical(value['summary']['manifest'])==_canonical(original[1]['manifest']) and value['page'] is None
    else:
        expected=original[2][view]['records']
        if view=='events':expected=[{k:e[k] for k in ('at','before','after','removed')} for e in expected]
        assert _canonical(value['page']['records'])==_canonical(expected) and value['summary'] is None


@pytest.mark.parametrize('query',['&tenant_id=foreign','&root=/tmp/private','&view=summary&offset=0','&limit=8',
    '&view=events&limit=9','&view=samples&limit=65','&view=samples&offset=131073','&view=samples&offset=-1',
    '&view=samples&offset=01','&view=samples&limit=+1','&view=events&limit=1.0','&view=samples&offset=true',
    '&view=samples&offset=0&offset=1','&view=samples&view=events','&view=unknown','&crop_id=foreign'])
def test_closed_query_is_denied_before_custody(original,monkeypatch,query):
    app,_,farm,trace,_=assembly(original,monkeypatch)
    assert get(app,original[0],farm,query=query)[0]==422 and 'open' not in trace


def test_body_missing_rights_and_authentication_never_reach_custody(original,monkeypatch):
    app,_,farm,trace,_=assembly(original,monkeypatch)
    assert get(app,original[0],farm,body=b'{}')[0]==422 and 'open' not in trace
    app,_,farm,trace,_=assembly(original,monkeypatch,scopes=READ_SCOPES[:-1])
    assert get(app,original[0],farm)[0]==403 and 'open' not in trace
    assert get(app,original[0],farm,headers=[])[0]==401 and 'open' not in trace


@pytest.mark.parametrize('missing',['exists','tenant'])
def test_missing_or_other_tenant_result_is_closed_not_found(original,monkeypatch,missing):
    app,_,farm,trace,state=assembly(original,monkeypatch,tenant='foreign-tenant' if missing=='tenant' else 'own-projection-tenant')
    if missing=='exists':state['exists']=False
    assert get(app,original[0],farm)[0]==404 and trace.count('open')==trace.count('close')==1 and 'current' not in trace


@pytest.mark.parametrize('position,error,status',[('read_error',PermissionError('private'),403),
    ('read_error',server.CycleCustodyHold('private'),422),('read_error',RuntimeError('private'),503),
    ('current_error',PermissionError('private'),403),('current_error',server.CycleCustodyHold('private'),422),
    ('current_error',RuntimeError('private'),503)])
def test_read_and_final_check_errors_close_context_and_hide_private_reason(original,monkeypatch,position,error,status):
    app,_,farm,trace,state=assembly(original,monkeypatch);state[position]=error
    actual,value,_=get(app,original[0],farm)
    assert actual==status and 'private' not in json.dumps(value) and trace.count('open')==trace.count('close')==1


@pytest.mark.parametrize('withdraw',['source','credential'])
def test_withdrawal_during_projection_does_not_return_stale_bytes(original,monkeypatch,withdraw):
    clock={'now':NOW};app,_,farm,trace,state=assembly(original,monkeypatch,clock=lambda:clock['now'])
    project=public.project_cycle_result
    def changed(*args,**kw):
        value=project(*args,**kw)
        if withdraw=='source':state['allowed']=False
        else:clock['now']=NOW+timedelta(hours=1)
        return value
    monkeypatch.setattr(public,'project_cycle_result',changed)
    assert get(app,original[0],farm)[0]==(403 if withdraw=='source' else 401)
    assert trace.count('close')==1 and 'current' in trace


@pytest.mark.parametrize('fault',['type','jobs','farm','principal'])
def test_install_rejects_mixed_authority_pointers(original,monkeypatch,fault):
    _,store,_,_,_=assembly(original,monkeypatch);jobs=store.jobs;farms=store.server.binding.farms;principal=current_principal
    if fault=='type':store=SimpleNamespace(**store.__dict__)
    elif fault=='jobs':jobs=SimpleNamespace(principal_provider=principal)
    elif fault=='farm':farms=object()
    else:principal=lambda:None
    with pytest.raises(ValueError):public.install_cycle_crop_routes(FastAPI(),jobs=jobs,farms=farms,store=store,
        principal_provider=principal,authorized_tenant=lambda *_:None,error=_error,access=_access)


def test_cycle_openapi_closed_types_paging_and_research_labels():
    doc=contract_document();op=doc['paths'][PATH+'{result_id}']['get']
    assert op['operationId']=='getCycleCropResearchResult' and op['x-ossf-required-scopes']==list(READ_SCOPES)
    params={p['name']:p for p in op['parameters']}
    assert params['offset']['schema']['maximum']==131072 and params['view']['schema']['default']=='summary'
    schemas=doc['components']['schemas'];ref=schemas['CycleCropReference']
    assert ref['additionalProperties'] is False and ref['properties']['steps']['maximum']==40000000
    assert schemas['CycleSamplePage']['properties']['records']['maxItems']==64
    assert schemas['CycleEventPage']['properties']['records']['maxItems']==8
    assert schemas['CycleCropReplay']['additionalProperties'] is False


@pytest.mark.parametrize('first',['app.api','app.crop_cycle_result_store','app.crop_cycle_server_custody'])
def test_fresh_process_import_order_preserves_schema_only_startup(first):
    code="import importlib; importlib.import_module("+repr(first)+"); from app.api_openapi import contract_document; assert '/v1/crop-cycle-research-results/{result_id}' in contract_document()['paths']"
    subprocess.run([sys.executable,'-c',code],cwd=Path(__file__).resolve().parents[1],
        check=True,capture_output=True,timeout=30)


@pytest.mark.parametrize('kind,limit',[('samples',1),('events',2)])
def test_selected_limit_offset_and_empty_last_page_keep_original_positions(original,monkeypatch,kind,limit):
    app,_,farm,trace,_=assembly(original,monkeypatch)
    total=original[2][kind]['total']
    status,value,_=get(app,original[0],farm,query=f'&view={kind}&offset=1&limit={limit}')
    assert status==200 and value['page']['offset']==1 and len(value['page']['records'])==limit
    assert value['page']['next_offset']==(1+limit if 1+limit<total else None)
    status,value,_=get(app,original[0],farm,query=f'&view={kind}&offset={total}&limit={limit}')
    assert status==200 and value['page']['records']==[] and value['page']['next_offset'] is None
    assert trace.count('open')==trace.count('close')==2
