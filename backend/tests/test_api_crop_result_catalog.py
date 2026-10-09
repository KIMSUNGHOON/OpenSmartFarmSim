"""Owned Bearer ASGI and closed projection; real SCRAM/HTTPS is a separate smoke."""
import asyncio
from contextlib import contextmanager
from copy import deepcopy
from datetime import datetime
import json
from pathlib import Path
import subprocess
import sys
from types import SimpleNamespace
from urllib.parse import urlencode

from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
import pytest

from app import api_crop_result_catalog as route
from app import crop_result_catalog as catalog
from app.api import create_app, _access, _error
from app.api_openapi import _SchemaOnlyStores
from app.crop_result_store import READ_SCOPES
from app.http_identity import current_principal
from app.runtime_roles import RolePolicyHold
from test_api_crop_cycle_route import protect, TOKEN
from test_http_identity import request

FARM={'scenario_id':'catalog-farm','scenario_revision':'r1','registration_sha256':'a'*64,'crop_id':'crop-1'}
STAMP='2026-10-09T01:00:00.000000Z'


def page(kind='calculation_cycle_v1',count=2):
    items=[]
    for n in range(count,0,-1):
        entry={'recorded_at':STAMP,'calculation_status':'completed'}
        if kind=='calculation_cycle_v1':
            entry.update(result_id=catalog.calculation.storage.VERSION+':'+format(n,'064x'),
                claim_scope='synthetic_crop_math_only',study_id='synthetic-'+str(n),revision='r1',
                period={'start':'2026-10-01T00:00:00Z','end':'2026-10-02T00:00:00Z'},sample_count=3,event_count=3)
        else:
            entry.update(result_id=catalog.harvest.registry.VERSION+':'+format(n,'064x'),
                claim_scope='synthetic_harvest_allocation_math_only',parent_result_id=catalog.calculation.storage.VERSION+':'+'1'*64,row_count=5)
        items.append(entry)
    return {'version':catalog.VERSION,'scope':'stored_research_metadata_only','kind':kind,'farm':deepcopy(FARM),
        'items':items,'next_cursor':None,'selection_validation_required':True,'rights_or_gate_approval':False}


def assembly(monkeypatch,*,kind='calculation_cycle_v1',scopes=READ_SCOPES,disabled=False):
    state={'allowed':True,'page':page(kind),'read_error':None,'exit_error':None,'foreign_after':False}
    trace=[];jobs=_SchemaOnlyStores();jobs.principal_provider=current_principal;farms=object()
    store=object.__new__(catalog.calculation.storage.CalculationCycleCropResultStore)
    store.jobs=jobs;store.server=SimpleNamespace(binding=SimpleNamespace(jobs=jobs,farms=farms))
    query=object.__new__(catalog.calculation.CalculationCurrentCycleQuery);query.store=store
    monkeypatch.setattr(query,'_pointers',lambda:('unit-fixed',));monkeypatch.setattr(query,'_binding',lambda:None)
    harvest=object.__new__(catalog.harvest.HarvestCurrentQuery);harvest.store=SimpleNamespace(query=query)
    harvest._fixed=('unit-harvest',);monkeypatch.setattr(harvest,'_binding',lambda:None)
    @contextmanager
    def opened(service,tenant,actual_kind,farm,*,limit=10,before=None):
        trace.append('open');state['request']=(tenant,actual_kind,farm,limit,before)
        try:
            if state['read_error'] is not None:raise state['read_error']
            if not state['allowed']:raise PermissionError('private source reason')
            yield deepcopy(state['page'])
            trace.append('current')
            if state['exit_error'] is not None:raise state['exit_error']
            if not state['allowed']:raise PermissionError('private withdrawal reason')
        finally:trace.append('close')
    monkeypatch.setattr(catalog.CropResultCatalog,'open',opened)
    def authorized(*required):
        trace.append('account');principal=current_principal()
        if principal is None:return None,_error(401,'unauthenticated','Authentication required')
        if any(s not in principal['scopes'] for s in required):return None,_error(403,'forbidden','Resource access denied')
        return 'foreign' if state['foreign_after'] else principal['tenant_id'],None
    app=FastAPI()
    @app.exception_handler(RequestValidationError)
    async def invalid(*_):return _error(422,'invalid_request','Invalid request')
    kwargs=dict(jobs=jobs,farms=farms,calculation_query=None if disabled else query,
        harvest_query=None if disabled else harvest,principal_provider=current_principal,
        authorized_tenant=authorized,error=_error,access=_access)
    route.install_catalog_routes(app,**kwargs)
    return SimpleNamespace(app=protect(app,scopes=scopes,tenant='tenant-1'),trace=trace,state=state,kwargs=kwargs,base=app)


def get(case,*,query=None,body=b'',headers=None):
    params={'kind':case.state['page']['kind'],**FARM} if query is None else query
    raw=params if isinstance(params,str) else urlencode(params)
    return asyncio.run(request(case.app,path=route.PATH,query=raw.encode(),body=body,
        headers=[(b'authorization',b'Bearer '+TOKEN)] if headers is None else headers))


SELECTION_REF={k:v for k,v in FARM.items() if k!='crop_id'}
SELECTION_PATH='/v1/crop-research-result-catalog/farm-crops'


def selection_case(monkeypatch,**kwargs):
    case=assembly(monkeypatch,**kwargs)
    case.state['selection']={'version':'crop-research-farm-selection-v1','scope':'registered_user_inputs_only',
        'farm':deepcopy(SELECTION_REF),'items':[{'crop_id':'crop-1','batch_id':'batch-1',
            'species':'방울토마토 시험 의도','variety':'등록 품종 · 미검증',
            'occupancy':{'start':'2026-01-01T00:00:00.000000Z','end':'2026-01-02T00:00:00.000000Z'},
            'profile_status':'unavailable','origin':'user','evidence_level':'assumed'}],
        'selection_validation_required':True,'rights_or_gate_approval':False}
    @contextmanager
    def opened(service,tenant,farm):
        case.trace.append('selection-open');case.state['selection_request']=(tenant,farm)
        try:
            if case.state['read_error'] is not None:raise case.state['read_error']
            if not case.state['allowed']:raise PermissionError('private farm rights')
            yield deepcopy(case.state['selection'])
            case.trace.append('selection-current')
            if case.state['exit_error'] is not None:raise case.state['exit_error']
            if not case.state['allowed']:raise PermissionError('private farm rights')
        finally:case.trace.append('selection-close')
    monkeypatch.setattr(catalog.CropResultCatalog,'open_farm_selection',opened)
    return case


def get_selection(case,*,query=None,body=b'',headers=None):
    params=SELECTION_REF if query is None else query
    raw=params if isinstance(params,str) else urlencode(params)
    return asyncio.run(request(case.app,path=SELECTION_PATH,query=raw.encode(),body=body,
        headers=[(b'authorization',b'Bearer '+TOKEN)] if headers is None else headers))


def test_farm_selection_typed_bytes_finish_before_current_context_and_account(monkeypatch):
    case=selection_case(monkeypatch)
    status,value,headers=get_selection(case)
    assert status==200 and value==case.state['selection']
    assert case.state['selection_request']==('tenant-1',SELECTION_REF)
    assert case.trace==['account','selection-open','selection-current','selection-close','account']
    assert headers[b'cache-control']==b'no-store'
    assert headers[b'x-ossf-crop-farm-selection-version']==b'crop-research-farm-selection-v1'
    assert headers[b'x-ossf-crop-catalog-projection-sha256']==route.CODE_SHA256.encode()


@pytest.mark.parametrize('extra',['&extra=1','&crop_id=guess','&kind=harvest_v1','&limit=20',
    '&scenario_id=duplicate','&registration_sha256=bad'])
def test_farm_selection_closed_query_never_reads_registration(monkeypatch,extra):
    case=selection_case(monkeypatch)
    status,value,_=get_selection(case,query=urlencode(SELECTION_REF)+extra)
    assert status==422 and value['error']['code']=='invalid_request' and 'selection-open' not in case.trace


@pytest.mark.parametrize('field',list(SELECTION_REF))
def test_farm_selection_required_fields_are_not_guessed(monkeypatch,field):
    case=selection_case(monkeypatch);params=deepcopy(SELECTION_REF);params.pop(field)
    assert get_selection(case,query=params)[0]==422 and 'selection-open' not in case.trace


def test_farm_selection_requires_auth_empty_body_and_configured_reader(monkeypatch):
    case=selection_case(monkeypatch)
    assert get_selection(case,headers=[])[0]==401
    assert get_selection(case,body=b'{}')[0]==422 and 'selection-open' not in case.trace
    case=selection_case(monkeypatch,scopes=READ_SCOPES[:-1]);assert get_selection(case)[0]==403
    case=selection_case(monkeypatch,disabled=True)
    assert get_selection(case)[0]==503 and get_selection(case,headers=[])[0]==401


@pytest.mark.parametrize('fault',['extra','farm','hash','scope','approval','selection','origin','evidence',
    'profile','species-number','label-control','label-whitespace','label-size','period','duplicate','order','too-many','bytes'])
def test_farm_selection_rejects_unbound_or_invalid_public_metadata(monkeypatch,fault):
    case=selection_case(monkeypatch);v=case.state['selection'];item=v['items'][0]
    if fault=='extra':item['yield_kg']=5
    elif fault=='farm':v['farm']['scenario_id']='foreign'
    elif fault=='hash':v['farm']['registration_sha256']='b'*64
    elif fault=='scope':v['scope']='approved_crop_profile'
    elif fault=='approval':v['rights_or_gate_approval']=1
    elif fault=='selection':v['selection_validation_required']=False
    elif fault=='origin':item['origin']='measured'
    elif fault=='evidence':item['evidence_level']='validated'
    elif fault=='profile':item['profile_status']='approved'
    elif fault=='species-number':item['species']=42
    elif fault=='label-control':item['variety']='bad\nlabel'
    elif fault=='label-whitespace':item['species']=' label '
    elif fault=='label-size':item['species']='x'*201
    elif fault=='period':item['occupancy']['end']=item['occupancy']['start']
    elif fault=='duplicate':v['items']=[item,item]
    elif fault=='order':v['items']=[{**item,'crop_id':'crop-2'},item]
    else:
        v['items']=[{**deepcopy(item),'crop_id':str(i).zfill(3)+'c'*197} for i in range(33 if fault=='too-many' else 32)]
        if fault=='bytes':
            for row in v['items']:row.update(species='🌱'*200,variety='🍅'*200,batch_id='b'*200)
    status,value,_=get_selection(case)
    assert status==422 and value['error']['code']=='crop_catalog_hold'


@pytest.mark.parametrize('count',[0,32])
def test_farm_selection_empty_and_maximum_crop_count_are_metadata_only(monkeypatch,count):
    case=selection_case(monkeypatch);item=case.state['selection']['items'][0]
    case.state['selection']['items']=[{**deepcopy(item),'crop_id':'crop-'+str(i).zfill(2)} for i in range(count)]
    assert get_selection(case)[:2]==(200,case.state['selection'])


@pytest.mark.parametrize('fault',['withdrawal','changed-registration','changed-account'])
def test_farm_selection_late_changes_do_not_publish_prepared_bytes(monkeypatch,fault):
    case=selection_case(monkeypatch);original=route._farm_selection_bytes
    def encoded(*args,**kwargs):
        value=original(*args,**kwargs)
        if fault=='withdrawal':case.state['allowed']=False
        elif fault=='changed-registration':case.state['exit_error']=catalog.CropResultCatalogHold('private replacement')
        else:case.state['foreign_after']=True
        return value
    monkeypatch.setattr(route,'_farm_selection_bytes',encoded)
    status,value,_=get_selection(case)
    assert status==(422 if fault=='changed-registration' else 403)
    assert 'items' not in value and b'private' not in json.dumps(value).encode()


@pytest.mark.parametrize('kind',catalog.KINDS)
def test_complete_typed_page_serializes_inside_current_context(monkeypatch,kind):
    case=assembly(monkeypatch,kind=kind);original=route._public_bytes
    def encoded(*args,**kwargs):case.trace.append('bytes');return original(*args,**kwargs)
    monkeypatch.setattr(route,'_public_bytes',encoded)
    status,value,headers=get(case)
    assert status==200 and value==case.state['page']
    assert case.trace==['account','open','bytes','current','close','account']
    assert headers[b'cache-control']==b'no-store' and headers[b'x-content-type-options']==b'nosniff'
    assert headers[b'x-ossf-crop-catalog-version']==catalog.VERSION.encode()
    assert headers[b'x-ossf-crop-catalog-projection-sha256']==route.CODE_SHA256.encode()


@pytest.mark.parametrize('kind',catalog.KINDS)
def test_empty_and_cursor_pages_keep_UTC_and_kind(monkeypatch,kind):
    case=assembly(monkeypatch,kind=kind);case.state['page']['items']=[]
    ident=page(kind)['items'][0]['result_id'];params={'kind':kind,**FARM,'limit':'20',
        'before_recorded_at':STAMP,'before_result_id':ident}
    assert get(case,query=params)[0]==200
    assert case.state['request'][3:]==(20,{'recorded_at':datetime.fromisoformat(STAMP),'result_id':ident})


@pytest.mark.parametrize('extra', ['&extra=1','&kind=harvest_v1','&limit=0','&limit=21','&limit=01',
    '&limit=+1','&limit=1.0','&limit=true','&limit=','&limit=2&limit=3','&before_recorded_at='+STAMP,
    '&before_result_id=unknown','&before_recorded_at=2026-99-99T00:00:00.000000Z&before_result_id='+catalog.calculation.storage.VERSION+':'+'1'*64,
    '&before_recorded_at='+STAMP+'&before_result_id='+catalog.harvest.registry.VERSION+':'+'1'*64])
def test_invalid_closed_query_does_not_open_catalog(monkeypatch,extra):
    case=assembly(monkeypatch);status,value,_=get(case,query=urlencode({'kind':'calculation_cycle_v1',**FARM})+extra)
    assert status==422 and value['error']['code']=='invalid_request' and 'open' not in case.trace


@pytest.mark.parametrize('field', ['kind',*FARM])
def test_missing_required_query_does_not_open(monkeypatch,field):
    case=assembly(monkeypatch);params={'kind':'calculation_cycle_v1',**FARM};params.pop(field)
    assert get(case,query=params)[0]==422 and 'open' not in case.trace


def test_auth_body_and_disabled_route_are_closed(monkeypatch):
    case=assembly(monkeypatch)
    assert get(case,headers=[])[0]==401 and get(case,body=b'{}')[0]==422 and 'open' not in case.trace
    case=assembly(monkeypatch,scopes=READ_SCOPES[:-1])
    assert get(case)[0]==403 and 'open' not in case.trace
    case=assembly(monkeypatch,disabled=True)
    assert get(case)[0]==503 and get(case,headers=[])[0]==401 and 'open' not in case.trace


@pytest.mark.parametrize('phase', ['read_error','exit_error'])
@pytest.mark.parametrize('fault,status,code', [(PermissionError,403,'forbidden'),
    (catalog.CropResultCatalogHold,422,'crop_catalog_hold'),(RuntimeError,503,'crop_catalog_unavailable'),
    (RolePolicyHold,503,'crop_catalog_unavailable')])
def test_private_errors_on_entry_or_exit_never_publish_prepared_page(monkeypatch,phase,fault,status,code):
    case=assembly(monkeypatch);case.state[phase]=fault('private reason')
    actual,value,_=get(case)
    assert actual==status and value['error']['code']==code and 'private' not in json.dumps(value)
    assert case.trace.count('open')==case.trace.count('close')==1


@pytest.mark.parametrize('mutation', ['unknown','farm','kind','flag0','flag1','count_bool','count_negative',
    'duplicate','order','period','period_fraction','timestamp','cursor','too_many'])
def test_malformed_or_mixed_metadata_is_held(monkeypatch,mutation):
    case=assembly(monkeypatch);value=case.state['page'];item=value['items'][0]
    if mutation=='unknown':value['secret']='private'
    elif mutation=='farm':value['farm']['crop_id']='foreign'
    elif mutation=='kind':value.update(page('harvest_v1'))
    elif mutation=='flag0':value['rights_or_gate_approval']=0
    elif mutation=='flag1':value['selection_validation_required']=1
    elif mutation=='count_bool':item['sample_count']=True
    elif mutation=='count_negative':item['sample_count']=-1
    elif mutation=='duplicate':value['items'][1]=deepcopy(item)
    elif mutation=='order':value['items'].reverse()
    elif mutation=='period':item['period']['end']=item['period']['start']
    elif mutation=='period_fraction':item['period']={'start':'2026-10-01T00:00:00.1Z','end':'2026-10-01T00:00:00Z'}
    elif mutation=='timestamp':item['recorded_at']='2026-10-09T01:00:00Z'
    elif mutation=='cursor':value['next_cursor']={'recorded_at':STAMP,'result_id':item['result_id']}
    else:value['items']=page(count=21)['items']
    # A mixed response must not change the requested kind.
    status,body,_=get(case,query={'kind':'calculation_cycle_v1',**FARM})
    assert status==422 and body['error']['code']=='crop_catalog_hold' and 'items' not in body


@pytest.mark.parametrize('withdraw', ['rights','tenant'])
def test_withdrawal_during_serialization_refuses_success(monkeypatch,withdraw):
    case=assembly(monkeypatch);original=route._public_bytes
    def changed(*args,**kwargs):
        raw=original(*args,**kwargs)
        if withdraw=='rights':case.state['allowed']=False
        else:case.state['foreign_after']=True
        return raw
    monkeypatch.setattr(route,'_public_bytes',changed)
    assert get(case)[0]==403 and case.trace.count('close')==1


@pytest.mark.parametrize('fault',['jobs','farms','principal','query','harvest'])
def test_mixed_runtime_graph_is_rejected(monkeypatch,fault):
    case=assembly(monkeypatch);kwargs=dict(case.kwargs)
    if fault in ('jobs','farms','query'):kwargs['calculation_query' if fault=='query' else fault]=object()
    elif fault=='principal':kwargs['principal_provider']=lambda:None
    else:kwargs['harvest_query']=object()
    with pytest.raises(ValueError,match='trusted crop catalog'):route.install_catalog_routes(FastAPI(),**kwargs)


@pytest.mark.parametrize('module',['app.api','app.api_runtime','app.crop_result_catalog'])
def test_fresh_import_and_schema_export_have_no_connection_side_effect(module):
    root=Path(__file__).resolve().parents[1]
    code='import psycopg,socket\ndef refuse(*a,**k): raise AssertionError("connection during import/schema")\npsycopg.connect=refuse\nsocket.create_connection=refuse\nimport '+module+'\nfrom app.api_openapi import contract_document\nassert "'+route.PATH+'" in contract_document()["paths"]\n'
    result=subprocess.run([sys.executable,'-c',code],cwd=root,capture_output=True,timeout=15)
    assert result.returncode==0,result.stderr.decode()
