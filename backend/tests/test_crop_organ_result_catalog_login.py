"""Actual SCRAM metadata reads of normal synthetic organ producers; no crop claim."""
from copy import deepcopy
from datetime import datetime, timezone
from hashlib import sha256
import json
import os
from pathlib import Path

import pytest

from app.crop_organ_result_catalog import OrganCropResultCatalog, CropResultCatalogHold
from app.crop_result_store import CropResultStore
from test_crop_result_store import (crop_setup,authoring,farm_setup,login_scope,login_database,put,count)

pytestmark=pytest.mark.parametrize('login_scope',[{'market_calculation':True,
    'market_source_storage':True,'thermal_scenario_storage':True,
    'break_even_calculation':True,'crop_result_storage':True}],indirect=True)


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
    assert count(store)==before and calls==[]
    assert {k:store._find('tenant-1',result_id=k) for k in snapshots}==snapshots
    evidence={'scope':'normal synthetic producer / SCRAM metadata only','items':items,
        'first_count':2,'tail_count':1,'rights_entry_and_exit_denied':True,'scope_exit_denied':True,
        'original_rows_and_payloads_unchanged':True,'put_integrate_or_RHS_calls':0,
        'record_SHA256':{k:sha256(v['payload_raw']).hexdigest() for k,v in snapshots.items()},
        'actual_crop_Runs':0,'G0_G4':'not_assessed','API_or_browser_performed':False}
    root=os.environ.get('OSSF_JOINT_PREFIX_RUNTIME_EVIDENCE')
    if root:(Path(root)/'organ-catalog-login.private.json').write_text(json.dumps(evidence,sort_keys=True)+'\n')
