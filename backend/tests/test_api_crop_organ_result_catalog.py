"""Closed organ catalogue API and an independent legacy-only assembly."""
from contextlib import contextmanager
from copy import deepcopy
import json
from types import SimpleNamespace

from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
import pytest

from app import api_crop_result_catalog as route
from app import crop_organ_result_catalog as organ
from app.crop_result_store import CropResultStore
from app.api import _error
from test_api_crop_result_catalog import assembly,page,get,selection_case,get_selection,FARM,STAMP
from test_api_crop_cycle_route import protect


def organ_page():
    value=page();value['kind']='organ_v1'
    for n,item in enumerate(value['items']):item['result_id']='crop-result-v1:'+format(2-n,'064x')
    return value


def standalone(monkeypatch,*,configured=True,with_calculation=False):
    case=selection_case(monkeypatch,disabled=not with_calculation);case.state['page']=organ_page()
    store=object.__new__(CropResultStore);store.jobs=case.kwargs['jobs'];store.farms=case.kwargs['farms']
    store._pointers=lambda:('owned-organ-unit',)
    monkeypatch.setattr(organ.OrganCropResultCatalog,'_binding',lambda self:None)
    @contextmanager
    def opened(service,tenant,kind,farm,*,limit=10,before=None):
        case.trace.append('organ-open');case.state['request']=(tenant,kind,farm,limit,before)
        if case.state['read_error']:raise case.state['read_error']
        yield deepcopy(case.state['page'])
        case.trace.append('organ-current')
        if case.state['exit_error']:raise case.state['exit_error']
    @contextmanager
    def selection(service,tenant,farm):
        case.trace.append('organ-selection');yield deepcopy(case.state['selection'])
        if case.state['exit_error']:raise case.state['exit_error']
    monkeypatch.setattr(organ.OrganCropResultCatalog,'open',opened)
    monkeypatch.setattr(organ.OrganCropResultCatalog,'open_farm_selection',selection,raising=False)
    app=FastAPI()
    @app.exception_handler(RequestValidationError)
    async def invalid(*_):return _error(422,'invalid_request','Invalid request')
    kwargs={**case.kwargs,'organ_store':store if configured else None}
    route.install_catalog_routes(app,**kwargs)
    return SimpleNamespace(**{**vars(case),'app':protect(app,tenant='tenant-1'),'kwargs':kwargs,'organ_store':store})


def test_organ_typed_metadata_preserves_closed_rows_and_UTC():
    value=organ_page()
    raw=route._public_bytes(value,kind='organ_v1',farm=FARM,limit=10,before=None)
    assert json.loads(raw)==value


def test_organ_only_reader_supports_current_metadata_and_registered_crop_selection(monkeypatch):
    case=standalone(monkeypatch)
    status,value,headers=get(case)
    assert status==200 and value==case.state['page']
    assert case.trace==['account','organ-open','organ-current','account']
    assert headers[b'cache-control']==b'no-store'
    assert headers[b'x-ossf-crop-catalog-code-sha256']==organ.CODE_SHA256.encode()
    assert get_selection(case)[0:2]==(200,case.state['selection'])
    assert 'organ-selection' in case.trace


def test_organ_coexists_with_both_existing_kinds(monkeypatch):
    case=standalone(monkeypatch,with_calculation=True)
    assert get(case)[0]==200
    for kind in ('calculation_cycle_v1','harvest_v1'):
        case.state['page']=page(kind);assert get(case)[0]==200


def test_organ_reader_disabled_after_auth_and_wrong_kind_cursor_are_closed(monkeypatch):
    case=standalone(monkeypatch,configured=False)
    assert get(case)[0]==503 and get(case,headers=[])[0]==401
    case=standalone(monkeypatch)
    params={'kind':'organ_v1',**FARM,'before_recorded_at':STAMP,
        'before_result_id':'crop-result-v2:'+'a'*64}
    assert get(case,query=params)[0]==422
    assert 'organ-open' not in case.trace


@pytest.mark.parametrize('fault',['wrong-ID','wrong-kind','wrong-farm','extra','units','cursor','bool','period'])
def test_organ_malformed_projection_is_held(monkeypatch,fault):
    case=standalone(monkeypatch);value=case.state['page'];item=value['items'][0]
    if fault=='wrong-ID':item['result_id']='crop-result-v2:'+'a'*64
    elif fault=='wrong-kind':value['kind']='calculation_cycle_v1'
    elif fault=='wrong-farm':value['farm']['crop_id']='other'
    elif fault=='extra':item['production_forecast_kg']=3
    elif fault=='units':item['samples']=[{'kg':1}]
    elif fault=='cursor':value['next_cursor']={'recorded_at':STAMP,'result_id':item['result_id']}
    elif fault=='bool':item['sample_count']=True
    else:item['period']['end']=item['period']['start']
    status,body,_=get(case,query={'kind':'organ_v1',**FARM});assert status==422 and body['error']['code']=='crop_catalog_hold'
    assert 'items' not in body


@pytest.mark.parametrize('phase',['read_error','exit_error'])
@pytest.mark.parametrize('error,status',[(PermissionError,403),(organ.CropResultCatalogHold,422),(RuntimeError,503)])
def test_organ_current_or_late_errors_never_publish_private_bytes(monkeypatch,phase,error,status):
    case=standalone(monkeypatch);case.state[phase]=error('private farm reason')
    actual,body,_=get(case);assert actual==status and 'items' not in body
    assert 'private farm reason' not in json.dumps(body)


@pytest.mark.parametrize('fault',['jobs','farms','principal','type'])
def test_organ_mixed_runtime_graph_is_rejected(monkeypatch,fault):
    case=standalone(monkeypatch);kwargs={**case.kwargs}
    if fault=='jobs':case.organ_store.jobs=object()
    elif fault=='farms':case.organ_store.farms=object()
    elif fault=='principal':kwargs['principal_provider']=lambda:None
    else:kwargs['organ_store']=object()
    with pytest.raises(ValueError):route.install_catalog_routes(FastAPI(),**kwargs)


def test_organ_account_change_during_encoding_discards_prepared_bytes(monkeypatch):
    case=standalone(monkeypatch);original=route._public_bytes
    def encoded(*args,**kwargs):
        raw=original(*args,**kwargs);case.state['foreign_after']=True;return raw
    monkeypatch.setattr(route,'_public_bytes',encoded)
    status,body,_=get(case);assert status==403 and 'items' not in body
