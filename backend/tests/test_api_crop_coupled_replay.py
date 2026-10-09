"""Typed pages of saved coupled research math; no harvest or gate claims."""
from copy import deepcopy
from datetime import datetime, timedelta, timezone
from hashlib import sha256
import asyncio
from dataclasses import replace
import http.client
import json
import os
from pathlib import Path
import ssl
import threading
import time
from urllib.parse import urlencode, urlsplit

import pytest
from jsonschema import Draft202012Validator
from psycopg import sql

from app.api_crop_coupled_replay import CoupledCropReplay, project_coupled_result
from app import crop_coupled_artifact as artifact
from app import crop_coupled_result_store as storage
from app import crop_result_store as previous
from app.api_openapi import contract_document
from app.api import create_app
from app.api_runtime import ApiRuntime
from app.http_identity import BearerGrant, BearerRegistry, current_principal, token_digest
from app.market_source_store import MarketSourceStore
from app.thermal_run_store import _canonical
from test_crop_coupled_artifact import OPTIONS, rehash
from test_crop_plant_cohort_integration import program
from test_crop_coupled_result_store import (coupled_setup, authoring, farm_setup,
    login_database, login_scope, NOTICE, KEY, PROFILES, put, count, update_rights)
from test_api_job_status import UnusedMarketResultStore
from test_api_runtime import config, dependencies, policy
from test_api_serve import tls_files
from test_http_identity import request
from test_market_hold_store import context_verifier


PATH='/v1/crop-coupled-research-results/{result_id}'
CROP_POLICY={'market_calculation':True,'market_source_storage':True,
    'thermal_scenario_storage':True,'break_even_calculation':True,'crop_coupled_result_storage':True}


def seal(packet):
    packet['artifact_sha256']=sha256(_canonical(packet['artifact'])).hexdigest()
    packet['result_id']='crop-result-v2:'+sha256(_canonical(
        {k:v for k,v in packet.items() if k!='result_id'})).hexdigest()
    raw=_canonical(packet)
    return {'result_id':packet['result_id'],'payload_raw':raw,
        'payload_sha256':sha256(raw).hexdigest(),
        'recorded_at':datetime(2026,10,4,tzinfo=timezone.utc)}


def record_for(candidate):
    doc=json.loads(artifact.calculate_coupled_artifact(_canonical(candidate),**OPTIONS))
    farm={'scenario_id':'scenario-1','scenario_revision':'r1',
          'registration_sha256':'1'*64,'crop_id':'crop-1'}
    return seal({'schema_version':'crop-result-v2','status':'stored_unpublished_research',
        'claim_scope':'synthetic_crop_math_only','tenant_id':'synthetic-tenant',
        'request':{'study_id':'study-1','revision':'r1','farm':farm,'program':candidate,
                  'rights':{'program_sha256':doc['program_sha256']}},
        'binding':{'crop':{'crop_id':'crop-1','batch_id':'batch-1'},'zone_id':'zone-1',
            'farm_sha256':'2'*64,'source_binding_sha256':'3'*64,
            'normalization':'per_m2_floor','profile_applicability':'unvalidated_for_registered_crop'},
        'rights_policy_version':'synthetic-test-only',
        'storage_code_sha256':storage.STORAGE_CODE_SHA256,
        'binding_code_sha256':previous.STORAGE_CODE_SHA256,'artifact':doc})


@pytest.fixture(scope='module')
def saved():
    return record_for(program())


def project(record,**pages):
    return project_coupled_result(record,**OPTIONS,**pages).model_dump(mode='json')


def capacity_program(candidate):
    start=datetime.fromisoformat(candidate['segments'][0]['start'].replace('Z','+00:00'))
    stamp=lambda i:(start+timedelta(seconds=i)).isoformat().replace('+00:00','Z')
    segment=deepcopy(candidate['segments'][0]);segment['end']=stamp(511)
    candidate['segments']=[segment];candidate['output_times']=[stamp(i) for i in range(512)]
    seed=deepcopy(candidate['events'][0]);seed['removals']['values']['leaf']['value']=0.0
    seed['removals']['values']['stem_root']['value']=0.0
    seed['removals']['values']['fruit_fraction']=[{'value':1e-6,'unit':'1'} for _ in range(50)]
    candidate['events']=[]
    for i in range(128):
        event=deepcopy(seed);event['at']=stamp(i);event['removals']['input_id']='management-'+str(i)
        candidate['events'].append(event)
    return candidate


def test_closed_projection_preserves_all_quantities_and_hides_inputs(saved):
    packet=json.loads(saved['payload_raw']);result=packet['artifact']['result'];value=project(saved)
    assert value['samples']==result['samples']
    assert value['events']==[{k:e[k] for k in ('at','before','after','removed')} for e in result['events']]
    assert value['sample_page']=={'offset':0,'limit':64,'total':6,'next_offset':None}
    assert value['event_page']=={'offset':0,'limit':8,'total':3,'next_offset':None}
    assert value['manifest']['artifact_sha256']==packet['artifact_sha256']
    assert value['manifest']['result_sha256']==result['result_sha256']
    assert value['manifest']['raw_program_sha256']==packet['artifact']['program_sha256']
    assert value['claim_scope']=='synthetic_crop_math_only' and value['gates']=='not_assessed'
    assert value['manifest']['research_assumptions']==['leaf_stem_fixed_RGR_from_reference_profile_not_measured']
    assert all(len(s['state']['fruit_number'])==len(s['state']['fruit_carbohydrate'])==50 for s in value['samples'])
    text=json.dumps(value)
    for private in ('tenant_id','program_raw_utf8','profile_raw_utf8','notice_raw_utf8',
                    'forcing_input_id','input_ids','integrity_signature','rights_policy_version'):
        assert private not in text
    Draft202012Validator(CoupledCropReplay.model_json_schema()).validate(value)


def test_capacity_pages_keep_all_original_samples_events_hashes_and_order(monkeypatch):
    saved=record_for(capacity_program(program()))
    result=json.loads(saved['payload_raw'])['artifact']['result'];samples=[];events=[];manifests=[]
    assert result['status']=='completed' and len(result['samples'])==512 and len(result['events'])==128
    monkeypatch.setattr(artifact.integration,'integrate_plant_cohorts',
        lambda **_:pytest.fail('projection reintegrated'))
    for offset in range(0,512,64):
        value=project(saved,sample_offset=offset);samples.extend(value['samples']);manifests.append(value['manifest'])
        assert value['sample_page']['next_offset']==(offset+64 if offset<448 else None)
    for offset in range(0,128,8):
        value=project(saved,event_offset=offset);events.extend(value['events'])
    assert samples==result['samples']
    assert events==[{k:e[k] for k in ('at','before','after','removed')} for e in result['events']]
    assert all(m==manifests[0] for m in manifests)
    last=project(saved,sample_offset=512,event_offset=128)
    assert last['samples']==last['events']==[] and last['sample_page']['next_offset'] is None


@pytest.mark.parametrize('kind',['event','fractional','empty'])
def test_actual_hold_only_shows_confirmed_past_and_separate_diagnostic(kind):
    candidate=program()
    if kind=='event':candidate['events'][1]['removals']['values']['leaf']['value']=1e7
    elif kind=='fractional':
        candidate['events']=[];candidate['solver']['max_step_seconds']=1
        candidate['segments'][0]['removals']['values']['leaf']['value']=1e9
    else:
        candidate['initial_state']['values']['buffer']['value']=0
        candidate['segments'][0]['forcing']['values']['par_above_canopy']['value']=0
    saved=record_for(candidate);result=json.loads(saved['payload_raw'])['artifact']['result'];value=project(saved)
    assert result['status']==value['status']=='hold'
    assert value['samples']==result['samples'] and value['hold']['last_confirmed']==result['last_confirmed']
    at=lambda t:datetime.fromisoformat(t.replace('Z','+00:00'))
    assert all(at(s['at'])<at(value['hold']['at']) for s in value['samples'])
    if kind=='fractional':
        assert value['hold']['at'].endswith('00.500000Z') and len(value['samples'])==1
    if kind=='empty':assert value['samples']==value['events']==[] and value['hold']['last_confirmed'] is None
    assert 'reason' not in value['hold'] and 'failed_state' not in value['hold']


@pytest.mark.parametrize('fault',['bytes','id','storage','binding','profile','model','unit','count','balance','time','scope','duplicate'])
def test_tampered_or_mixed_projection_fails_closed(saved,fault):
    saved=dict(saved);packet=json.loads(saved['payload_raw']);result=packet['artifact']['result']
    if fault=='bytes':saved['payload_sha256']='0'*64
    elif fault=='id':saved['result_id']='crop-result-v2:'+'0'*64
    elif fault=='duplicate':
        saved['payload_raw']=b'{"private":1,"private":2}';saved['payload_sha256']=sha256(saved['payload_raw']).hexdigest()
    else:
        if fault=='storage':packet['storage_code_sha256']='0'*64
        elif fault=='binding':packet['binding_code_sha256']='0'*64
        elif fault=='profile':packet['artifact']['profile_raw_utf8']['cohort_profile']+=' '
        elif fault=='model':result['manifest']['rate_model_version']='private-marker'
        elif fault=='unit':result['samples'][0]['state']['fruit_number'][0]['unit']='kg_fresh'
        elif fault=='count':result['samples'][0]['state']['fruit_carbohydrate'].pop()
        elif fault=='balance':result['samples'][1]['carbon_residual']['value']=100
        elif fault=='time':result['samples'].reverse()
        elif fault=='scope':packet['claim_scope']='real_prediction'
        packet['artifact']=json.loads(rehash(packet['artifact']));saved=seal(packet)
    with pytest.raises(storage.CropResultHold,match='^coupled crop display unavailable$'):
        project(saved)


@pytest.mark.parametrize('pages',[{'sample_offset':7},{'event_offset':4},{'sample_limit':65},
    {'event_limit':9},{'sample_offset':True},{'sample_limit':0},{'sample_offset':-1}])
def test_invalid_pages_are_fixed_hold(saved,pages):
    with pytest.raises(storage.CropResultHold):project(saved,**pages)


def test_openapi_units_closed_arrays_pages_and_scopes():
    doc=contract_document();op=doc['paths'][PATH]['get']
    assert op['operationId']=='getCoupledCropResearchResult'
    assert op['x-ossf-required-scopes']==list(storage.READ_SCOPES)
    assert {p['name'] for p in op['parameters']}=={'result_id','scenario_id','scenario_revision',
        'registration_sha256','crop_id','sample_offset','sample_limit','event_offset','event_limit'}
    for name in ('CoupledCropReplay','CoupledCropState','CoupledCropManifest','CoupledCropSample','CoupledCropHold'):
        assert doc['components']['schemas'][name]['additionalProperties'] is False
        Draft202012Validator.check_schema(doc['components']['schemas'][name])
    state=doc['components']['schemas']['CoupledCropState']['properties']
    assert state['fruit_number']['minItems']==state['fruit_number']['maxItems']==50
    assert state['fruit_carbohydrate']['minItems']==state['fruit_carbohydrate']['maxItems']==50


def test_coupled_runtime_options_are_paired_before_connections():
    calls=[]
    for cfg,deps in ((config(),dependencies(crop_coupled_result_store_factory=lambda **_:calls.append('called'))),
            (config(policy=replace(policy(),crop_coupled_result_storage=True)),dependencies())):
        with pytest.raises(ValueError,match='^API runtime assembly rejected$'):ApiRuntime(cfg,deps)
    with pytest.raises(ValueError,match='^API runtime dependencies rejected$'):
        dependencies(crop_coupled_result_store_factory=True)
    assert calls==[]


def app_for(store,*,with_store=True):
    replay=store.farms.replay
    return create_app(store.jobs,replay.thermal.holds,replay.thermal.runs,UnusedMarketResultStore(),
        principal_provider=store.jobs.principal_provider,location_research_service=replay.owned_research,
        thermal_scenario_store=replay.thermal,farm_scenario_service=replay,
        farm_authoring_service=store.farms,crop_coupled_result_store=store if with_store else None)


def target(record,body,**pages):
    return PATH.format(result_id=record['result_id'])+'?'+urlencode({**body['farm'],**pages})


def get(app,path,body=b''):
    where=urlsplit(path)
    return asyncio.run(request(app,path=where.path,query=where.query.encode(),method='GET',body=body))[:2]


@pytest.mark.parametrize('login_scope',[CROP_POLICY],indirect=True)
def test_scram_current_farm_scope_rights_query_body_caps_and_no_reintegration(coupled_setup,monkeypatch,login_scope):
    store,body,principal,rights=coupled_setup;record=put(store,body)
    expected=project(record);app=app_for(store);path=target(record,body);before=count(store)
    monkeypatch.setattr(artifact.integration,'integrate_plant_cohorts',lambda **_:pytest.fail('GET reintegrated'))
    monkeypatch.setattr(storage,'calculate_coupled_artifact',lambda *a,**k:pytest.fail('GET calculated'))
    assert get(app,path)==get(app,path)==(200,expected)
    assert get(app_for(store,with_store=False),path)[0]==503
    missing={**record,'result_id':'crop-result-v2:'+'0'*64}
    assert get(app,target(missing,body))[0]==404
    for pages in ({'crop_id':'other'},{'registration_sha256':'0'*64},{'sample_offset':7},{'event_offset':4}):
        assert get(app,target(record,body,**pages))[0]==422
    for invalid in (path+'&tenant_id=spoofed',path+'&crop_id=crop-1',path+'&model=x',path+'&sample_limit=65',
            path+'&event_limit=9',path+'&sample_offset=0&sample_offset=0',path.split('?')[0],
            path.replace('crop-result-v2:','wrong-v2:'),
            *(path+'&sample_offset='+v for v in ('00','+1','1.0','1e0','true','-1','','%20','%D9%A1'))):
        assert get(app,invalid)[0]==422,invalid
    assert get(app,path,b'{"program":"not accepted"}')[0]==422
    last=get(app,target(record,body,sample_offset=6,event_offset=3))[1]
    assert last['samples']==last['events']==[]
    principal['authenticated']=False;assert get(app,path)[0]==401;principal['authenticated']=True
    for scope in storage.READ_SCOPES:
        principal['scopes'].remove(scope);assert get(app,path)[0]==403;principal['scopes'].add(scope)
    principal['tenant_id']='foreign';assert get(app,path)[0]==404;principal['tenant_id']='tenant-1'
    rights.allowed=False;assert get(app,path)[0]==422;rights.allowed=True
    import app.api_crop_coupled_replay as module
    for error,status in ((PermissionError('private-marker'),403),(storage.CropResultHold('private-marker'),422),
            (RuntimeError('private-marker'),503)):
        with monkeypatch.context() as patch:
            def fail(*a,**k):raise error
            patch.setattr(storage.CoupledCropResultStore,'get',fail)
            actual,value=get(app,path);assert actual==status and 'private-marker' not in json.dumps(value)
    original=module.project_coupled_result
    for kind in ('program','source','scope','tenant'):
        with monkeypatch.context() as patch:
            def revoke(*a,**k):
                value=original(*a,**k)
                if kind=='program':rights.allowed=False
                elif kind=='source':patch.setattr(store.farms.replay.candidates._source._source,'get_input_rights',lambda *_:None)
                elif kind=='scope':principal['scopes'].remove('crop_result_read')
                else:principal['tenant_id']='foreign'
                return value
            patch.setattr(module,'project_coupled_result',revoke)
            assert get(app,path)[0]==(422 if kind in ('program','source') else 403),kind
        rights.allowed=True;principal['scopes'].add('crop_result_read');principal['tenant_id']='tenant-1'
    with monkeypatch.context() as patch:
        patch.setattr(module,'MAX_RESPONSE_BYTES',1);assert get(app,path)[0]==422
    assert get(app,path)==(200,expected)
    base,policy,_=login_scope;target_table=store.jobs._table('crop_coupled_research_results')
    packet=json.loads(record['payload_raw']);packet['artifact']['result']['samples'][0]['state']['leaf']['value']+=1
    corrupted=_canonical(packet)
    with base.connect() as conn:
        conn.execute(sql.SQL('SET LOCAL ROLE {}').format(sql.Identifier(policy.owner)))
        conn.execute(sql.SQL('ALTER TABLE {} DISABLE TRIGGER crop_coupled_result_immutable').format(target_table))
        conn.execute(sql.SQL('UPDATE {} SET payload_raw=%s,payload_sha256=%s WHERE tenant_id=%s AND result_id=%s')
            .format(target_table),(corrupted,sha256(corrupted).hexdigest(),'tenant-1',record['result_id']))
        conn.execute(sql.SQL('ALTER TABLE {} ENABLE TRIGGER crop_coupled_result_immutable').format(target_table))
    assert get(app,path)[0]==422 and count(store)==before


@pytest.mark.parametrize('login_scope',[CROP_POLICY],indirect=True)
def test_stored_event_and_fractional_hold_pages_keep_past_and_never_append_trial(coupled_setup):
    store,body,_,_=coupled_setup
    body['program']['events'][1]['removals']['values']['leaf']['value']=1e7;update_rights(body)
    record=put(store,body);value=get(app_for(store),target(record,body,sample_limit=2))[1]
    assert value['status']=='hold' and len(value['samples'])==2 and value['sample_page']['total']==3
    assert value['sample_page']['next_offset']==2
    second=get(app_for(store),target(record,body,sample_offset=2))[1]
    result=json.loads(record['payload_raw'])['artifact']['result']
    assert value['samples']+second['samples']==result['samples']
    body['revision']='fractional';body['program']['events']=[]
    body['program']['solver']['max_step_seconds']=1
    body['program']['segments'][0]['removals']['values']['leaf']['value']=1e9;update_rights(body)
    record=put(store,body);status,value=get(app_for(store),target(record,body))
    assert status==200 and value['hold']['at'].endswith('00.500000Z') and len(value['samples'])==1
    assert value['hold']['last_confirmed']['at']==value['samples'][0]['at']


@pytest.mark.parametrize('login_scope',[CROP_POLICY],indirect=True)
def test_standard_https_scram_max_pages_exact_restart_current_rights_and_cleanup(coupled_setup,tls_files,monkeypatch):
    store,body,_,rights=coupled_setup;body['program']=capacity_program(body['program']);update_rights(body)
    record=put(store,body);packet=json.loads(record['payload_raw']);result=packet['artifact']['result']
    assert len(result['samples'])==512 and len(result['events'])==128 and result['status']=='completed'
    expected=project(record);replay=store.farms.replay;research=replay.owned_research;jobs=store.jobs
    cert,key,_=tls_files;now=datetime.now(timezone.utc)
    subjects=[('owner','tenant-1',set(storage.READ_SCOPES)),('foreign','foreign',set(storage.READ_SCOPES)),
        ('denied','tenant-1',set(storage.READ_SCOPES)-{'crop_result_read'})]
    tokens={name:('synthetic-coupled-'+name+'-'+'c'*32).encode() for name,_,_ in subjects}
    grants=tuple(BearerGrant(token_digest(tokens[name]),tenant,frozenset(scopes),
        now-timedelta(seconds=1),now+timedelta(minutes=20)) for name,tenant,scopes in subjects)
    def source_factory(*,principal_provider):
        return MarketSourceStore(jobs._dsn,jobs.schema,principal_provider=principal_provider,runtime_identity=jobs.runtime_identity)
    def crop_factory(*,farm_authoring_service):
        return storage.CoupledCropResultStore(farm_authoring_service,**PROFILES,
            notice_raw=NOTICE,program_rights=rights,integrity_key=KEY)
    cfg=config(policy=jobs.runtime_identity[0],dsn=jobs._dsn,artifact_root=jobs.artifact_root,
        certificate=cert,private_key=key,port=0)
    deps=dependencies(research_registry=research.catalog,bearer_registry=BearerRegistry(grants),
        owned_fixture_registry=research.registry,owned_research_contexts=dict(research._contexts),
        context_verifier=context_verifier,market_scope_resolver=replay.thermal.holds._scope_resolver,
        market_source_factory=source_factory,crop_coupled_result_store_factory=crop_factory)
    descriptor=jobs._content_directory(create=True);os.close(descriptor)
    runtime=ApiRuntime(cfg,deps)
    assert runtime.coupled_crop_results.jobs is runtime.jobs and runtime.coupled_crop_results.farms is runtime.farm_authoring
    for bad in (None,lambda **_:store,lambda **_:object()):
        with pytest.raises(ValueError,match='^API runtime assembly rejected$'):
            ApiRuntime(cfg,replace(deps,crop_coupled_result_store_factory=bad))
    before=count(store);path=target(record,body);timings=[];responses=[];body_sizes=[]
    monkeypatch.setattr(artifact.integration,'integrate_plant_cohorts',lambda **_:pytest.fail('HTTPS reintegrated'))
    monkeypatch.setattr(storage,'calculate_coupled_artifact',lambda *a,**k:pytest.fail('HTTPS calculated'))
    trust=ssl.create_default_context(cafile=str(cert))
    for restart in range(2):
        if restart:runtime=ApiRuntime(cfg,deps)
        server=runtime.service.server();thread=threading.Thread(target=server.run,daemon=True);thread.start()
        try:
            deadline=time.monotonic()+15
            while not server.started:
                assert thread.is_alive() and time.monotonic()<deadline;time.sleep(.01)
            port=server.servers[0].sockets[0].getsockname()[1]
            def call(where=path,bearer='owner'):
                conn=http.client.HTTPSConnection('127.0.0.1',port,timeout=30,context=trust)
                try:
                    started=time.monotonic()
                    headers={} if bearer is None else {'Authorization':'Bearer '+tokens[bearer].decode()}
                    conn.request('GET',where,headers=headers);response=conn.getresponse();raw=response.read()
                    timings.append(time.monotonic()-started);body_sizes.append(len(raw));value=json.loads(raw)
                    assert len(raw)<=2*1024*1024 and response.getheader('cache-control')=='no-store'
                    responses.append({'status':response.status,'value':value})
                    return response.status,value
                finally:conn.close()
            assert call()==(200,expected)
            if not restart:
                assert call(bearer=None)[0]==401 and call(bearer='denied')[0]==403 and call(bearer='foreign')[0]==404
                samples=[]
                for offset in range(0,512,64):
                    status,page=call(target(record,body,sample_offset=offset))
                    assert status==200 and page['manifest']==expected['manifest']
                    samples.extend(page['samples'])
                assert samples==result['samples']
                status,last=call(target(record,body,sample_offset=512,event_offset=128))
                assert status==200 and last['samples']==last['events']==[]
                rights.allowed=False;assert call()[0]==422;rights.allowed=True
                with monkeypatch.context() as patch:
                    patch.setattr(runtime.farm_scenarios.candidates._source._source,'get_input_rights',lambda *_:None)
                    assert call()[0]==422
                assert call(path+'&tenant_id=spoofed')[0]==422
            assert call()==(200,expected)
        finally:
            server.should_exit=True;thread.join(timeout=15);assert not thread.is_alive()
    with jobs.connect() as conn:
        assert conn.pgconn.used_password
        assert conn.execute(sql.SQL('SELECT count(*) AS n FROM {}').format(jobs._table('thermal_g1_runs'))).fetchone()['n']==0
    assert count(store)==before and max(timings)<30 and current_principal() is None
    Path('/tmp/ossf-coupled-api-https-evidence-20261005.json').write_text(json.dumps({
        'scope':'synthetic_crop_math_only','result_id':record['result_id'],'actual_tls_scram':True,
        'responses':responses,'full_response_seconds':timings,'body_bytes':body_sizes,'timeout_seconds':30,
        'original_samples':512,'original_events':128,'https_servers_joined':2},ensure_ascii=False,indent=2)+'\n')
