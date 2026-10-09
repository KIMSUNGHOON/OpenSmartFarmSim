"""Metadata pagination and authority changes; real signed rows use the native smoke."""
from contextlib import contextmanager
from copy import deepcopy
from datetime import datetime, timedelta, timezone
from types import SimpleNamespace

import pytest

from app import crop_result_catalog as catalog

FARM = {'scenario_id':'owned-farm','scenario_revision':'r1','registration_sha256':'a'*64,'crop_id':'crop-1'}
AT = datetime(2026,10,9,1,0,tzinfo=timezone.utc)


def selection_service(count=1):
    service=object.__new__(catalog.CropResultCatalog)
    crops=tuple(SimpleNamespace(crop_id='crop-'+str(i).zfill(2),batch_id='batch-'+str(i),
        species='방울토마토 시험 의도',variety='등록 품종 · 미검증',profile_status='unavailable',
        provenance=SimpleNamespace(origin='user',evidence_level='assumed'),
        occupancy=SimpleNamespace(start=AT,end=AT+timedelta(days=1))) for i in range(count))
    ref={k:v for k,v in FARM.items() if k!='crop_id'}
    registration={'farm':SimpleNamespace(scenario_id=ref['scenario_id'],scenario_revision=ref['scenario_revision'],
        crops=tuple(reversed(crops))),'scenario_sha256':ref['registration_sha256']}
    state={'registration':registration,'allowed':True,'calls':0}
    def read(tenant,selected):
        state['calls']+=1
        if tenant!='tenant-1' or not state['allowed']:raise PermissionError('private reason')
        assert selected==ref
        return deepcopy(state['registration'])
    service._selection_registration=read
    return service,ref,state


@pytest.mark.parametrize('count',[0,1,32])
def test_registered_crop_selection_preserves_user_labels_and_original_clock(count):
    service,ref,state=selection_service(count)
    with service.open_farm_selection('tenant-1',ref) as value:
        assert value['farm']==ref and len(value['items'])==count
        assert value['version']=='crop-research-farm-selection-v1'
        assert value['scope']=='registered_user_inputs_only'
        assert value['selection_validation_required'] is True and value['rights_or_gate_approval'] is False
        assert [v['crop_id'] for v in value['items']]==sorted(v.crop_id for v in state['registration']['farm'].crops)
        for item in value['items']:
            source=next(v for v in state['registration']['farm'].crops if v.crop_id==item['crop_id'])
            assert (item['species'],item['variety'],item['batch_id'])==(source.species,source.variety,source.batch_id)
            assert item['occupancy']=={'start':catalog._time(AT),'end':catalog._time(AT+timedelta(days=1))}
            assert (item['origin'],item['evidence_level'],item['profile_status'])==('user','assumed','unavailable')
    assert state['calls']==3


@pytest.mark.parametrize('fault',['missing','extra','crop','hash','path','not-object'])
def test_crop_selection_invalid_farm_reference_never_reads_registration(fault):
    service,ref,state=selection_service()
    if fault=='missing':ref.pop('scenario_id')
    elif fault=='extra':ref['approved']=True
    elif fault=='crop':ref['crop_id']='guess'
    elif fault=='hash':ref['registration_sha256']='A'*64
    elif fault=='path':ref['scenario_id']='../guess'
    else:ref=[]
    with pytest.raises(catalog.CropResultCatalogHold):
        with service.open_farm_selection('tenant-1',ref):pytest.fail('invalid reference yielded')
    assert state['calls']==0


@pytest.mark.parametrize('fault',['duplicate','too-many','bytes'])
def test_crop_selection_does_not_truncate_invalid_or_oversized_registration(fault):
    service,ref,state=selection_service(33 if fault=='too-many' else 32)
    crops=state['registration']['farm'].crops
    if fault=='duplicate':crops[-1].crop_id=crops[0].crop_id
    elif fault=='bytes':
        for i,crop in enumerate(crops):
            crop.species='🌱'*200;crop.variety='🍅'*200
            crop.crop_id=str(i).zfill(3)+'c'*197;crop.batch_id='b'*200
    with pytest.raises(catalog.CropResultCatalogHold):
        with service.open_farm_selection('tenant-1',ref):pytest.fail('invalid metadata yielded')


@pytest.mark.parametrize('fault',['foreign','withdrawal','registration-change'])
def test_crop_selection_current_authority_before_and_after_projection(fault):
    service,ref,state=selection_service()
    if fault=='foreign':
        with pytest.raises(PermissionError):
            with service.open_farm_selection('foreign',ref):pytest.fail('foreign metadata yielded')
        return
    with pytest.raises(PermissionError if fault=='withdrawal' else catalog.CropResultCatalogHold):
        with service.open_farm_selection('tenant-1',ref):
            if fault=='withdrawal':state['allowed']=False
            else:state['registration']['farm'].crops[0].variety='changed'


def test_crop_selection_registration_uses_current_shared_binding_and_exact_hash():
    service,ref,state=selection_service();registration=state['registration'];trace=[]
    service._binding=lambda:trace.append('binding')
    def read(*args):trace.append(args);return deepcopy(registration)
    service.calculation=SimpleNamespace(store=SimpleNamespace(server=SimpleNamespace(binding=SimpleNamespace(
        _guard=lambda tenant,write:trace.append((tenant,write)),farms=SimpleNamespace(read_registration=read)))))
    del service._selection_registration
    assert service._selection_registration('tenant-1',ref)==registration
    assert trace==['binding',('tenant-1',False),('tenant-1',ref['scenario_id'],ref['scenario_revision'],ref['registration_sha256']),('tenant-1',False)]
    registration['scenario_sha256']='b'*64
    with pytest.raises(catalog.CropResultCatalogHold):service._selection_registration('tenant-1',ref)


def identifier(kind, n):
    prefix = catalog.calculation.storage.VERSION if kind == catalog.KINDS[0] else catalog.harvest.registry.VERSION
    return prefix+':'+format(n,'064x')


@pytest.mark.parametrize('case', ('kind','farm-list','farm-extra','farm-missing','farm-path','farm-hash',
    'limit-bool','limit-zero','limit-large','cursor-list','cursor-extra','cursor-naive','cursor-string',
    'cursor-id-type','cursor-kind','cursor-hash'))
def test_invalid_filter_or_cursor_rejected_before_lookup(case):
    kind = catalog.KINDS[0];farm = deepcopy(FARM);limit = 10
    before = {'recorded_at':AT,'result_id':identifier(kind,1)}
    if case=='kind':kind='live_run'
    elif case=='farm-list':farm=[]
    elif case=='farm-extra':farm['approved']=True
    elif case=='farm-missing':del farm['crop_id']
    elif case=='farm-path':farm['scenario_id']='../escape'
    elif case=='farm-hash':farm['registration_sha256']='unknown'
    elif case=='limit-bool':limit=True
    elif case=='limit-zero':limit=0
    elif case=='limit-large':limit=21
    elif case=='cursor-list':before=[]
    elif case=='cursor-extra':before['farm']=farm
    elif case=='cursor-naive':before['recorded_at']=AT.replace(tzinfo=None)
    elif case=='cursor-string':before['recorded_at']=AT.isoformat()
    elif case=='cursor-id-type':before['result_id']=1
    elif case=='cursor-kind':before['result_id']=identifier(catalog.KINDS[1],1)
    else:before['result_id']='unknown'
    with pytest.raises(catalog.CropResultCatalogHold):catalog._request(kind,farm,limit,before)


@pytest.mark.parametrize('kind',catalog.KINDS)
def test_keyset_SQL_binds_all_filters_and_tie_breaker(kind):
    calls=[]
    class Connection:
        def execute(self, query, args):
            calls.append((query.as_string(),args))
            return SimpleNamespace(fetchall=lambda:[])
    @contextmanager
    def connection():yield Connection()
    jobs=SimpleNamespace(connect=connection,_table=lambda name:catalog.sql.Identifier('owned',name))
    service=object.__new__(catalog.CropResultCatalog)
    service.calculation=SimpleNamespace(store=SimpleNamespace(jobs=jobs))
    service.harvest=SimpleNamespace(store=SimpleNamespace(_connection=connection,policy=SimpleNamespace(schema='harvest_owned')))
    before={'recorded_at':AT.astimezone(timezone(timedelta(hours=9))),'result_id':identifier(kind,8)}
    assert service._rows('tenant-1',kind,FARM,2,before)==[]
    query,args=calls[0]
    assert args==['tenant-1',*FARM.values(),AT,identifier(kind,8),3]
    assert all(value not in query for value in ('tenant-1','owned-farm','r1','a'*64,'crop-1'))
    assert 'ORDER BY recorded_at DESC,result_id DESC LIMIT %s' in query
    assert '(recorded_at,result_id)<(%s,%s)' in query
    assert ('{binding,request,farm,crop_id}' in query)==(kind==catalog.KINDS[0])


def memory_service(kind, count=3):
    service=object.__new__(catalog.CropResultCatalog);state={'allowed':True}
    rows=[{'result_id':identifier(kind,n),'recorded_at':AT,'value':n} for n in range(count,0,-1)]
    saved={r['result_id']:r for r in rows}
    def guard(tenant,farm):
        if tenant!='tenant-1' or not state['allowed']:raise PermissionError('denied')
        return {'registration':'same'}
    def item(tenant,kind,farm,row,*,registration_checks=None):
        return {'result_id':row['result_id'],'recorded_at':catalog._time(row['recorded_at']),
                'calculation_status':'completed','value':row['value']}
    service._guard=guard;service._item=item
    service._rows=lambda tenant,kind,farm,limit,before:deepcopy(rows)
    store=SimpleNamespace(_find=lambda tenant,result_id:saved.get(result_id))
    service.calculation=SimpleNamespace(store=store);service.harvest=SimpleNamespace(store=store)
    return service,rows,state


@pytest.mark.parametrize('kind',catalog.KINDS)
def test_tied_times_page_lookahead_and_UTC_cursor_preserve_input(kind):
    service,rows,state=memory_service(kind);farm=deepcopy(FARM)
    page=service.read('tenant-1',kind,farm,limit=2)
    assert [r['result_id'] for r in page['items']]==[identifier(kind,3),identifier(kind,2)]
    assert page['next_cursor']=={'recorded_at':'2026-10-09T01:00:00.000000Z','result_id':identifier(kind,2)}
    assert page['scope']=='stored_research_metadata_only'
    assert page['selection_validation_required'] is True and page['rights_or_gate_approval'] is False
    assert farm==FARM and len(rows)==3
    with service.open('tenant-1',kind,farm,limit=2) as mutable:
        mutable['farm'].clear();mutable['items'].clear()
    assert farm==FARM and len(service.read('tenant-1',kind,farm,limit=2)['items'])==2


@pytest.mark.parametrize('kind',catalog.KINDS)
def test_final_page_and_empty_page_still_recheck_authority(kind):
    for count in (0,2):
        service,rows,state=memory_service(kind,count)
        assert service.read('tenant-1',kind,FARM,limit=2)['next_cursor'] is None
        with pytest.raises(PermissionError):
            with service.open('tenant-1',kind,FARM,limit=2):state['allowed']=False


@pytest.mark.parametrize('mutation', ('duplicate','unsorted','too_many','cursor_outside','row_changed','authority_changed'))
def test_unstable_or_modified_metadata_page_is_rejected(mutation):
    kind=catalog.KINDS[0];service,rows,state=memory_service(kind);before=None
    if mutation=='duplicate':rows[1]=deepcopy(rows[0])
    elif mutation=='unsorted':rows.reverse()
    elif mutation=='too_many':rows.append({'result_id':identifier(kind,0),'recorded_at':AT,'value':0})
    elif mutation=='cursor_outside':before={'recorded_at':AT,'result_id':identifier(kind,2)}
    if mutation in ('row_changed','authority_changed'):
        expected=PermissionError if mutation=='authority_changed' else catalog.CropResultCatalogHold
        with pytest.raises(expected):
            with service.open('tenant-1',kind,FARM,limit=2):
                if mutation=='row_changed':rows[0]['value']=100
                else:state['allowed']=False
    else:
        with pytest.raises(catalog.CropResultCatalogHold):service.read('tenant-1',kind,FARM,limit=2,before=before)


def test_unknown_authorities_and_missing_harvest_reader_are_rejected():
    with pytest.raises(catalog.CropResultCatalogHold):catalog.CropResultCatalog(None)
    service,rows,state=memory_service(catalog.KINDS[0],0);service.harvest=None
    with pytest.raises(catalog.CropResultCatalogHold):service.read('tenant-1',catalog.KINDS[1],FARM)


def test_UTC_time_normalization_and_naive_time_rejection():
    assert catalog._time(AT.astimezone(timezone(timedelta(hours=9))))=='2026-10-09T01:00:00.000000Z'
    with pytest.raises(catalog.CropResultCatalogHold):catalog._time(AT.replace(tzinfo=None))


def parent_service():
    calls={'registrations':0,'rights':0,'allowed':True}
    registration={'registered':'owned-farm'}
    packet={'binding':{'request':{'farm':deepcopy(FARM),'rights':{'available_at':'2026-01-01T00:00:00Z'}},
        'input':{'root_sha256':'a'*64,'period':{'start':'2026-02-01T00:00:00Z','end':'2026-02-02T00:00:00Z'}},
        'registration':registration},'policies':{'input_rights_version':'owned-rights',
        'resolver_version':'owned-resolver','notice_sha256':catalog.sha256(b'notice').hexdigest()}}
    def registered(*args):calls['registrations']+=1;return deepcopy(registration)
    def rights(*args):
        calls['rights']+=1
        if not calls['allowed']:raise PermissionError('withdrawn')
    binding=SimpleNamespace(_registration=registered,_rights=rights,
        input_rights=SimpleNamespace(policy_version='owned-rights'),notice_raw=b'notice')
    store=SimpleNamespace(_find=lambda *args,**kwargs:{'result_id':'owned'},
        _row=lambda *args:deepcopy(packet),_guard=lambda *args:None,
        server=SimpleNamespace(binding=binding,input_resolver=SimpleNamespace(version='owned-resolver')))
    service=object.__new__(catalog.CropResultCatalog);service.calculation=SimpleNamespace(store=store)
    return service,packet,calls


def test_same_registration_arguments_share_only_one_pass_check_but_keep_each_rights_check():
    service,packet,calls=parent_service();checks={}
    for n in range(3):
        packet['binding']['request']['study_id']=str(n)
        packet['binding']['input']['root_sha256']=format(n,'064x')
        service._parent('tenant-1','owned',FARM,registration_checks=checks)
    assert calls['registrations']==1 and calls['rights']==3
    service._parent('tenant-1','owned',FARM,registration_checks={})
    assert calls['registrations']==2 and calls['rights']==4
    calls['allowed']=False
    with pytest.raises(PermissionError):service._parent('tenant-1','owned',FARM,registration_checks=checks)
    assert calls['registrations']==2 and calls['rights']==5


@pytest.mark.parametrize('field',('tenant','farm','available_at','start','end'))
def test_different_registration_arguments_are_not_combined(field):
    service,packet,calls=parent_service();checks={};tenant='tenant-1'
    service._parent(tenant,'owned',FARM,registration_checks=checks)
    if field=='tenant':tenant='tenant-2'
    elif field=='farm':packet['binding']['request']['farm']['crop_id']='crop-2'
    elif field=='available_at':packet['binding']['request']['rights'][field]='2026-01-02T00:00:00Z'
    else:packet['binding']['input']['period'][field]='2026-02-01T01:00:00Z'
    service._parent(tenant,'owned',FARM,registration_checks=checks)
    assert calls['registrations']==2 and calls['rights']==2


def test_shared_registration_check_still_rejects_a_changed_original_binding():
    service,packet,calls=parent_service();checks={}
    service._parent('tenant-1','owned',FARM,registration_checks=checks)
    packet['binding']['registration']['registered']='changed'
    with pytest.raises(catalog.CropResultCatalogHold):
        service._parent('tenant-1','owned',FARM,registration_checks=checks)


def test_response_validation_phases_do_not_share_registration_checks():
    service,rows,_=memory_service(catalog.KINDS[0]);original=service._item;phases=[]
    def item(*args,registration_checks=None):
        phases.append(registration_checks)
        return original(*args,registration_checks=registration_checks)
    service._item=item
    service.read('tenant-1',catalog.KINDS[0],FARM,limit=2)
    assert len(phases)==9 and all(type(value) is dict for value in phases)
    assert phases[0] is phases[1] is phases[2]
    assert phases[3] is phases[4] is phases[5]
    assert phases[6] is phases[7] is phases[8]
    assert phases[0] is not phases[3] and phases[3] is not phases[6]


def test_registration_implementation_change_refuses_combined_checks(monkeypatch):
    service=object.__new__(catalog.CropResultCatalog)
    service.calculation=SimpleNamespace(_pointers=lambda:(),_binding=lambda:None);service.harvest=None
    service._fixed=service._pointers()
    service._binding()
    monkeypatch.setattr(catalog,'REGISTRATION_CODE_SHA256','0'*64)
    with pytest.raises(catalog.CropResultCatalogHold):service._binding()
