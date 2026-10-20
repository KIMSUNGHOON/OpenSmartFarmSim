"""Bounded discovery of organ metadata; real signed rows have a separate check."""
from copy import deepcopy
from contextlib import contextmanager
from contextvars import ContextVar
from datetime import datetime, timedelta, timezone
from types import SimpleNamespace

import pytest

from app import crop_organ_result_catalog as organ
from app.crop_result_catalog import CropResultCatalogHold
from app.thermal_run_store import _canonical

FARM={'scenario_id':'owned-farm','scenario_revision':'r1','registration_sha256':'a'*64,'crop_id':'crop-1'}
AT=datetime(2026,10,20,tzinfo=timezone.utc)


def identifier(n):return 'crop-result-v1:'+format(n,'064x')


def memory_catalog(count=3):
    service=object.__new__(organ.OrganCropResultCatalog)
    rows=[{'result_id':identifier(n),'recorded_at':AT} for n in range(count,0,-1)]
    records={}
    for row in rows:
        packet={'request':{'farm':deepcopy(FARM),'study_id':'study-'+row['result_id'][-1],'revision':'r1',
            'program':{'segments':[{'start':'2026-10-01T00:00:00Z','end':'2026-10-02T00:00:00Z'}]}},
            'result':{'status':'completed','samples':[{},{}],'events':[]}}
        raw=_canonical(packet)
        records[row['result_id']]={**row,'payload_raw':raw,'payload_sha256':organ.sha256(raw).hexdigest()}
    state={'allowed':True,'registration':{'same':'registration'},'reads':[]}
    def registration(tenant,farm):
        if tenant!='tenant-1' or not state['allowed']:raise PermissionError('private denial')
        assert farm==FARM
        return deepcopy(state['registration'])
    def get(tenant,result_id,farm):
        registration(tenant,farm);state['reads'].append(result_id);return deepcopy(records.get(result_id))
    slot=ContextVar('memory_catalog_registration',default=None)
    @contextmanager
    def read_scope(*args):
        token=slot.set(object())
        try:yield
        finally:slot.reset(token)
    service.store=SimpleNamespace(get=get,farms=SimpleNamespace(
        _registration_read=slot,registration_read_scope=read_scope))
    service._registration=registration
    service._rows=lambda tenant,farm,limit,before:deepcopy(rows)
    return service,rows,records,state


def test_organ_keyset_lookahead_preserves_exact_ids_periods_and_flags():
    service,rows,records,state=memory_catalog()
    with service.open('tenant-1','organ_v1',FARM,limit=2) as page:
        assert [v['result_id'] for v in page['items']]==[identifier(3),identifier(2)]
        assert page['next_cursor']=={'recorded_at':'2026-10-20T00:00:00.000000Z','result_id':identifier(2)}
        assert page['kind']=='organ_v1' and page['selection_validation_required'] is True
        assert page['rights_or_gate_approval'] is False
        assert page['items'][0]['period']=={'start':'2026-10-01T00:00:00Z','end':'2026-10-02T00:00:00Z'}
        assert page['items'][0]['sample_count']==2 and page['items'][0]['event_count']==0
        assert 'payload_raw' not in str(page) and 'samples' not in page['items'][0]
    assert len(state['reads'])==9


@pytest.mark.parametrize('fault',['kind','farm-extra','farm-hash','limit-bool','limit-zero','limit-large',
    'cursor-kind','cursor-naive','cursor-extra'])
def test_organ_invalid_filters_do_not_read_records(fault):
    service,rows,records,state=memory_catalog();farm=deepcopy(FARM);kind='organ_v1';limit=2
    before={'recorded_at':AT+timedelta(seconds=1),'result_id':identifier(9)}
    if fault=='kind':kind='crop_prediction'
    elif fault=='farm-extra':farm['tenant_id']='other'
    elif fault=='farm-hash':farm['registration_sha256']='A'*64
    elif fault=='limit-bool':limit=True
    elif fault=='limit-zero':limit=0
    elif fault=='limit-large':limit=21
    elif fault=='cursor-kind':before['result_id']='crop-result-v2:'+'a'*64
    elif fault=='cursor-naive':before['recorded_at']=AT.replace(tzinfo=None)
    else:before['approved']=True
    with pytest.raises(CropResultCatalogHold):
        with service.open('tenant-1',kind,farm,limit=limit,before=before):pytest.fail('invalid page')
    assert state['reads']==[]


@pytest.mark.parametrize('fault',['rights','registration','record-hash','record-time','missing'])
def test_organ_current_changes_after_projection_refuse_the_page(fault):
    service,rows,records,state=memory_catalog(1)
    with pytest.raises(PermissionError if fault=='rights' else CropResultCatalogHold):
        with service.open('tenant-1','organ_v1',FARM):
            if fault=='rights':state['allowed']=False
            elif fault=='registration':state['registration']['same']='changed'
            elif fault=='record-hash':records[identifier(1)]['payload_sha256']='b'*64
            elif fault=='record-time':records[identifier(1)]['recorded_at']+=timedelta(seconds=1)
            else:records.clear()


def test_organ_empty_page_still_checks_current_registration_and_foreign_tenant():
    service,rows,records,state=memory_catalog(0)
    with service.open('tenant-1','organ_v1',FARM) as page:
        assert page['items']==[] and page['next_cursor'] is None
    with pytest.raises(PermissionError):
        with service.open('foreign','organ_v1',FARM):pytest.fail('foreign empty page')


def test_organ_recorded_time_with_source_offset_preserves_the_exact_UTC_instant():
    service,rows,records,state=memory_catalog(1)
    rows[0]['recorded_at']=AT.astimezone(timezone(timedelta(hours=9)))
    records[identifier(1)]['recorded_at']=rows[0]['recorded_at']
    with service.open('tenant-1','organ_v1',FARM) as page:
        assert page['items'][0]['recorded_at']=='2026-10-20T00:00:00.000000Z'


@pytest.mark.parametrize('fault',['duplicate','order','too-many','cursor-outside','wrong-prefix','wrong-count-type','input-bytes','output-bytes'])
def test_organ_unstable_or_oversized_pages_hold(monkeypatch,fault):
    service,rows,records,state=memory_catalog();before=None
    if fault=='duplicate':rows[1]=deepcopy(rows[0])
    elif fault=='order':rows.reverse()
    elif fault=='too-many':rows.append(deepcopy(rows[0]))
    elif fault=='cursor-outside':before={'recorded_at':AT,'result_id':identifier(2)}
    elif fault=='wrong-prefix':rows[0]['result_id']='crop-result-v2:'+'a'*64
    elif fault=='wrong-count-type':
        import json
        record=records[identifier(3)];packet=json.loads(record['payload_raw']);packet['result']['samples']='bad';record['payload_raw']=_canonical(packet)
        record['payload_sha256']=organ.sha256(record['payload_raw']).hexdigest()
    elif fault=='input-bytes':monkeypatch.setattr(organ.storage,'MAX_PACKET_BYTES',1)
    else:monkeypatch.setattr(organ,'MAX_PAGE_BYTES',1)
    with pytest.raises(CropResultCatalogHold):
        with service.open('tenant-1','organ_v1',FARM,limit=2,before=before):pytest.fail('invalid page')


def test_organ_SQL_is_bounded_and_uses_only_original_farm_filters():
    service,rows,records,state=memory_catalog();calls=[]
    class Connection:
        def execute(self,query,args):calls.append((query.as_string(),args));return SimpleNamespace(fetchall=lambda:[])
        def __enter__(self):return self
        def __exit__(self,*_):pass
    service.store.jobs=SimpleNamespace(connect=Connection,_table=lambda name:organ.sql.Identifier('owned',name))
    del service._rows
    before={'recorded_at':AT.astimezone(timezone(timedelta(hours=9))),'result_id':identifier(2)}
    assert service._rows('tenant-1',FARM,2,before)==[]
    query,args=calls[0]
    assert 'SELECT result_id,recorded_at FROM' in query and 'SELECT *' not in query
    assert "{request,farm,crop_id}" in query and 'ORDER BY recorded_at DESC,result_id DESC LIMIT %s' in query
    assert args==['tenant-1',*FARM.values(),AT,identifier(2),3]
    assert all(value not in query for value in ('tenant-1','owned-farm','a'*64))


@pytest.mark.parametrize('store',[None,object(),SimpleNamespace()])
def test_organ_constructor_rejects_untrusted_stores(store):
    with pytest.raises(CropResultCatalogHold):organ.OrganCropResultCatalog(store)
