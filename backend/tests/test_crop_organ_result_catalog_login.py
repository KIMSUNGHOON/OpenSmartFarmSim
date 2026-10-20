"""Actual SCRAM metadata reads of normal synthetic organ producers; no crop claim."""
from copy import deepcopy
from datetime import datetime, timezone
from hashlib import sha256
import json
import os
from pathlib import Path
from urllib.parse import urlencode

import pytest

from app.crop_organ_result_catalog import OrganCropResultCatalog, CropResultCatalogHold
from app.crop_result_store import CropResultStore
from app.farm_authoring_storage import FarmAuthoringService
from test_crop_result_store import (crop_setup,authoring,farm_setup,login_scope,login_database,put,count)
from test_api_crop_replay import app_for,get as api_get

pytestmark=pytest.mark.parametrize('login_scope',[{'market_calculation':True,
    'market_source_storage':True,'thermal_scenario_storage':True,
    'break_even_calculation':True,'crop_result_storage':True}],indirect=True)


def test_registration_reconstruction_is_local_to_each_metadata_inspection(crop_setup,monkeypatch):
    store,body,_,_=crop_setup
    for n in range(3):
        request=deepcopy(body);request['study_id']='scope-cost-'+str(n)
        put(store,request)
    original=FarmAuthoringService._read_registration
    reconstructions=[]
    def counted(self,*args):
        reconstructions.append(args)
        return original(self,*args)
    monkeypatch.setattr(FarmAuthoringService,'_read_registration',counted)
    with OrganCropResultCatalog(store).open('tenant-1','organ_v1',body['farm'],limit=3) as page:
        assert len(page['items'])==3
        before_return=len(reconstructions)
    assert [before_return,len(reconstructions)]==[5,8]
    assert store.farms._registration_read.get() is None


@pytest.mark.parametrize('fault',['program-rights','account','farm'])
def test_cached_reconstruction_keeps_each_item_current_and_closes_on_denial(crop_setup,monkeypatch,fault):
    store,body,principal,rights=crop_setup
    records=[]
    for n in range(2):
        request=deepcopy(body);request['study_id']='late-scope-'+str(n)
        records.append(put(store,request))
    before={r['result_id']:store._find('tenant-1',result_id=r['result_id']) for r in records}
    changed={'active':False,'item_calls':0}
    actual_find=FarmAuthoringService._find
    def find(self,*args,**kwargs):
        row=actual_find(self,*args,**kwargs)
        if fault=='farm' and changed['active'] and row is not None:
            row=deepcopy(row);row['input_sha256']='0'*64
        return row
    monkeypatch.setattr(FarmAuthoringService,'_find',find)
    actual_item=OrganCropResultCatalog._item
    def item(self,*args,**kwargs):
        changed['item_calls']+=1
        if changed['item_calls']==2:
            changed['active']=True
            if fault=='program-rights':rights.allowed=False
            elif fault=='account':principal['scopes'].remove('crop_result_read')
        return actual_item(self,*args,**kwargs)
    monkeypatch.setattr(OrganCropResultCatalog,'_item',item)
    try:
        with pytest.raises(PermissionError if fault=='account' else CropResultCatalogHold):
            with OrganCropResultCatalog(store).open('tenant-1','organ_v1',body['farm']):
                pytest.fail('late denial was hidden by registration reuse')
    finally:
        rights.allowed=True;principal['scopes'].add('crop_result_read');changed['active']=False
    assert changed['item_calls']==2 and store.farms._registration_read.get() is None
    assert {k:store._find('tenant-1',result_id=k) for k in before}==before


@pytest.mark.parametrize('withdraw',[False,True])
def test_caller_keeps_ownership_of_an_existing_registration_scope(crop_setup,withdraw):
    store,body,_,rights=crop_setup
    put(store,body)
    farms=store.farms;ref=body['farm']
    with farms.registration_read_scope('tenant-1',ref['scenario_id'],ref['scenario_revision'],ref['registration_sha256']):
        owner=farms._registration_read.get()
        try:
            if withdraw:
                with pytest.raises(CropResultCatalogHold):
                    with OrganCropResultCatalog(store).open('tenant-1','organ_v1',ref):rights.allowed=False
            else:
                with OrganCropResultCatalog(store).open('tenant-1','organ_v1',ref) as page:
                    assert len(page['items'])==1 and farms._registration_read.get() is owner
            assert farms._registration_read.get() is owner
        finally:rights.allowed=True
    assert farms._registration_read.get() is None


def test_organ_signed_rows_keyset_current_rights_and_unchanged_custody(crop_setup,monkeypatch):
    store,body,principal,rights=crop_setup
    saved=[]
    for n in range(3):
        request=deepcopy(body);request['study_id']='organ-catalog-'+str(n)
        record=put(store,request);saved.append(record)
    snapshots={row['result_id']:store._find('tenant-1',result_id=row['result_id']) for row in saved}
    before=count(store)
    service=OrganCropResultCatalog(store)
    calls=[]
    def forbidden(*_,**__):calls.append('forbidden');pytest.fail('catalogue generated or published values')
    monkeypatch.setattr(CropResultStore,'put',forbidden)
    monkeypatch.setattr('app.crop_result_store.integrate_crop',forbidden)
    monkeypatch.setattr('app.crop_growth_integration.rates.calculate_rates',forbidden)
    with store.jobs.connect() as conn:assert conn.pgconn.used_password
    with service.open('tenant-1','organ_v1',body['farm'],limit=2) as first:
        assert len(first['items'])==2 and first['next_cursor'] is not None
    cursor=first['next_cursor']
    with service.open('tenant-1','organ_v1',body['farm'],limit=2,
            before={'recorded_at':datetime.fromisoformat(cursor['recorded_at']),'result_id':cursor['result_id']}) as tail:
        assert len(tail['items'])==1 and tail['next_cursor'] is None
    items=[*first['items'],*tail['items']]
    assert {i['result_id'] for i in items}==set(snapshots)
    for item in items:
        record=next(r for r in saved if r['result_id']==item['result_id']);packet=json.loads(record['payload_raw'])
        assert item['recorded_at']==record['recorded_at'].astimezone(timezone.utc).isoformat(timespec='microseconds').replace('+00:00','Z')
        assert item['sample_count']==len(packet['result']['samples'])
        assert item['event_count']==len(packet['result']['events'])
        assert item['period']=={'start':packet['request']['program']['segments'][0]['start'],
            'end':packet['request']['program']['segments'][-1]['end']}
    for phase in ('entry','after-projection'):
        with pytest.raises(CropResultCatalogHold):
            if phase=='entry':rights.allowed=False
            with service.open('tenant-1','organ_v1',body['farm']):rights.allowed=False
        rights.allowed=True
    with pytest.raises(PermissionError):
        with service.open('tenant-1','organ_v1',body['farm']):principal['scopes'].remove('crop_result_read')
    principal['scopes'].add('crop_result_read')
    with service.open('tenant-1','organ_v1',body['farm'],limit=2) as restored:assert restored==first
    app=app_for(store)
    params={'kind':'organ_v1',**body['farm'],'limit':2}
    path='/v1/crop-research-result-catalog?'+urlencode(params)
    assert api_get(app,path)==(200,first)
    farm_ref={k:v for k,v in body['farm'].items() if k!='crop_id'}
    with service.open_farm_selection('tenant-1',farm_ref) as selection:
        assert api_get(app,'/v1/crop-research-result-catalog/farm-crops?'+urlencode(farm_ref))==(200,selection)
    replay_path='/v1/crop-research-results/'+items[0]['result_id']+'?'+urlencode(body['farm'])
    replay_status,replay=api_get(app,replay_path)
    assert replay_status==200 and replay['result_id']==items[0]['result_id']
    assert len(replay['samples'])==items[0]['sample_count']
    rights.allowed=False
    assert api_get(app,path)[0]==422
    rights.allowed=True
    assert api_get(app,path)==(200,first)
    assert count(store)==before and calls==[]
    assert {k:store._find('tenant-1',result_id=k) for k in snapshots}==snapshots
    evidence={'scope':'normal synthetic producer / SCRAM metadata only','items':items,
        'first_count':2,'tail_count':1,'rights_entry_and_exit_denied':True,'scope_exit_denied':True,
        'original_rows_and_payloads_unchanged':True,'put_integrate_or_RHS_calls':0,
        'record_SHA256':{k:sha256(v['payload_raw']).hexdigest() for k,v in snapshots.items()},
        'actual_crop_Runs':0,'G0_G4':'not_assessed','owned_ASGI_with_actual_SCRAM':True,
        'API_statuses':[200,200,200,422,200],'HTTPS_or_browser_performed':False}
    root=os.environ.get('OSSF_JOINT_PREFIX_RUNTIME_EVIDENCE')
    if root:(Path(root)/'organ-catalog-login.private.json').write_text(json.dumps(evidence,sort_keys=True)+'\n')
