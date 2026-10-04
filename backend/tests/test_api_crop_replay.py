"""Saved crop math projection and authenticated TLS/SCRAM research reads."""
import asyncio
from copy import deepcopy
from dataclasses import replace
from datetime import datetime, timedelta, timezone
from hashlib import sha256
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

from app.api import create_app
from app.api_crop_replay import CropResearchReplay, project_crop_result
from app.api_openapi import contract_document
from app.api_runtime import ApiRuntime
from app.crop_growth_integration import _hash as integration_hash
from app.crop_result_store import CropResultStore, CropResultHold, READ_SCOPES
from app.http_identity import BearerGrant, BearerRegistry, current_principal, token_digest
from app.market_source_store import MarketSourceStore
from test_api_job_status import UnusedMarketResultStore
from test_api_runtime import config, dependencies, policy
from test_api_serve import tls_files
from test_crop_result_store import (crop_setup, authoring, farm_setup, login_scope,
    login_database, PROFILE, NOTICE, KEY, raw, put, count)
from test_http_identity import request
from test_market_hold_store import context_verifier

ROOT = Path(__file__).resolve().parents[2]
PATH = '/v1/crop-research-results/{result_id}'
CROP_POLICY = {'market_calculation':True,'market_source_storage':True,
    'thermal_scenario_storage':True,'break_even_calculation':True,'crop_result_storage':True}


@pytest.fixture
def reference_record():
    doc = json.loads((ROOT/'research/artifacts/crop-result-storage-reference-20261004.json').read_bytes())
    return {'result_id':doc['packet']['result_id'],'payload_raw':doc['payload_raw_utf8'].encode(),
        'payload_sha256':doc['payload_sha256'],'recorded_at':datetime.fromisoformat(doc['recorded_at'])}


def test_saved_projection_preserves_every_computed_quantity_and_scope(reference_record):
    packet = json.loads(reference_record['payload_raw'])
    actual = project_crop_result(reference_record).model_dump(mode='json')
    assert actual['result_id'] == packet['result_id']
    assert actual['recorded_at']==reference_record['recorded_at'].astimezone(timezone.utc).isoformat().replace('+00:00','Z')
    assert actual['samples'] == packet['result']['samples']
    assert actual['status'] == 'completed' and actual['hold'] is None
    assert actual['claim_scope'] == 'synthetic_crop_math_only'
    assert actual['gates'] == 'not_assessed'
    assert actual['farm'] == packet['request']['farm']
    assert actual['manifest']['input_sha256'] == packet['result']['manifest']['input_sha256']
    assert actual['manifest']['raw_program_sha256'] == packet['request']['rights']['program_sha256']
    assert actual['manifest']['payload_sha256'] == reference_record['payload_sha256']
    assert len(actual['samples']) == 6
    for event, stored in zip(actual['events'],packet['result']['events'],strict=True):
        assert event == {k:stored[k] for k in ('at','removals','before','after')}
    assert not ({'request','profile_raw_utf8','notice_raw_utf8','rights','tenant_id','integrity_signature'} & actual.keys())
    assert 'forcing_input_id' not in json.dumps(actual) and 'input_ids' not in json.dumps(actual)
    Draft202012Validator(CropResearchReplay.model_json_schema()).validate(actual)


@pytest.mark.parametrize('fault', ['bytes_hash','result_id','raw_duplicate','profile','model',
    'scope','unit','nonfinite','bool','order','missing_sample','extra_sample','hold_samples'])
def test_bad_saved_projection_is_fixed_hold(reference_record,fault):
    doc = json.loads(reference_record['payload_raw'])
    if fault=='bytes_hash': reference_record['payload_sha256']='0'*64
    elif fault=='result_id': reference_record['result_id']='crop-result-v1:'+'0'*64
    elif fault=='raw_duplicate': reference_record['payload_raw']=b'{"private":1,"private":2}'
    else:
        if fault=='profile': doc['result']['manifest']['profile_sha256']='0'*64
        elif fault=='model': doc['result']['manifest']['rate_model_version']='private-wrong-model'
        elif fault=='scope': doc['claim_scope']='real_crop_prediction'
        elif fault=='unit': doc['result']['samples'][0]['state']['fruit']['unit']='kg_fresh'
        elif fault=='nonfinite': doc['result']['samples'][0]['lai']['value']=float('nan')
        elif fault=='bool': doc['result']['samples'][0]['lai']['value']=True
        elif fault=='order': doc['result']['samples'].reverse()
        elif fault=='missing_sample': doc['result']['samples'].pop()
        elif fault=='extra_sample': doc['result']['samples'].append(doc['result']['samples'][0])
        elif fault=='hold_samples': doc['result']['status']='hold'
        if fault!='nonfinite':
            doc['result']['result_sha256']=integration_hash({k:v for k,v in doc['result'].items() if k!='result_sha256'})
            doc['result_id']='crop-result-v1:'+sha256(raw({k:v for k,v in doc.items() if k!='result_id'})).hexdigest()
            reference_record['result_id']=doc['result_id']
            reference_record['payload_raw']=raw(doc)
        else:
            reference_record['payload_raw']=json.dumps(doc,separators=(',',':'),sort_keys=True).encode()
        reference_record['payload_sha256']=sha256(reference_record['payload_raw']).hexdigest()
    with pytest.raises(CropResultHold,match='^crop research display unavailable$') as error:
        project_crop_result(reference_record)
    assert 'private' not in str(error.value)


def test_crop_openapi_closed_units_queries_scopes_and_research_status():
    document = contract_document()
    operation = document['paths'][PATH]['get']
    assert operation['operationId']=='getCropResearchResult'
    assert operation['x-ossf-required-scopes']==list(READ_SCOPES)
    assert operation['responses']['200']['content']['application/json']['schema']=={
        '$ref':'#/components/schemas/CropResearchReplay'}
    assert {p['name'] for p in operation['parameters']}=={
        'result_id','scenario_id','scenario_revision','registration_sha256','crop_id'}
    assert all(p['required'] for p in operation['parameters'])
    for name in ('CropResearchReplay','CropResearchSample','CropResearchState','CropResearchManifest','CropResearchHold'):
        schema=document['components']['schemas'][name]
        assert schema['additionalProperties'] is False
        Draft202012Validator.check_schema(schema)
    schema=document['components']['schemas']['CropResearchReplay']['properties']
    assert schema['gates']['const']=='not_assessed'
    assert schema['claim_scope']['const']=='synthetic_crop_math_only'
    assert schema['samples']['maxItems']==20000


def test_explicit_runtime_crop_options_are_paired_before_connections():
    calls=[]
    for cfg,deps in ((config(),dependencies(crop_result_store_factory=lambda **_:calls.append('called'))),
            (config(policy=replace(policy(),crop_result_storage=True)),dependencies())):
        with pytest.raises(ValueError,match='^API runtime assembly rejected$'):
            ApiRuntime(cfg,deps)
    assert calls==[]


def app_for(store, *, with_store=True):
    replay=store.farms.replay
    return create_app(store.jobs,replay.thermal.holds,replay.thermal.runs,UnusedMarketResultStore(),
        principal_provider=store.jobs.principal_provider,location_research_service=replay.owned_research,
        thermal_scenario_store=replay.thermal,farm_scenario_service=replay,
        farm_authoring_service=store.farms,crop_result_store=store if with_store else None)


def target(record,body,**changes):
    query={**body['farm'],**changes}
    return PATH.format(result_id=record['result_id'])+'?'+urlencode(query)


def get(app,path):
    where=urlsplit(path)
    return asyncio.run(request(app,path=where.path,query=where.query.encode(),method='GET'))[:2]


@pytest.mark.parametrize('login_scope',[CROP_POLICY],indirect=True)
def test_scram_api_current_authority_read_hold_errors_and_no_reintegration(crop_setup,monkeypatch,login_scope):
    store,body,principal,rights=crop_setup
    record=put(store,body)
    held_body=deepcopy(body); held_body['revision']='numeric-hold'
    held_body['program']['initial_state']['values']['buffer']['value']=0
    held_body['program']['segments'][0]['forcing']['values']['par_above_canopy']['value']=0
    held_body['rights']['program_sha256']=sha256(raw(held_body['program'])).hexdigest()
    held=put(store,held_body)
    expected=project_crop_result(record).model_dump(mode='json')
    app=app_for(store); path=target(record,body); before=count(store)
    monkeypatch.setattr('app.crop_result_store.integrate_crop',lambda **_:pytest.fail('read reintegrated'))
    assert get(app,path)==get(app,path)==(200,expected)
    assert get(app_for(store,with_store=False),path)[0]==503
    missing={**record,'result_id':'crop-result-v1:'+'0'*64}
    assert get(app,target(missing,body))[0]==404
    assert get(app,target(record,body,crop_id='other-crop'))[0]==422
    assert get(app,target(record,body,registration_sha256='0'*64))[0]==422
    for invalid in (path+'&tenant_id=spoofed',path+'&crop_id=crop-1',path+'&model=anything',
            path.replace('crop-result-v1:','wrong-v1:'),path.split('?')[0],
            target(record,body,registration_sha256='A'*64),target(record,body,scenario_id='bad space')):
        assert get(app,invalid)[0]==422
    principal['authenticated']=False
    assert get(app,path)[0]==401
    principal['authenticated']=True
    for scope in READ_SCOPES:
        principal['scopes'].remove(scope)
        assert get(app,path)[0]==403
        principal['scopes'].add(scope)
    principal['tenant_id']='foreign-tenant'
    assert get(app,path)[0]==404
    principal['tenant_id']='tenant-1'
    rights.allowed=False
    assert get(app,path)[0]==422
    rights.allowed=True
    held_status,held_value=get(app,target(held,held_body))
    assert held_status==200 and held_value['status']=='hold'
    assert held_value['samples']==held_value['events']==[]
    assert held_value['hold']['reason_code']=='DEPLETED_STATE_HOLD'
    assert held_value['hold']['failed_state']==json.loads(held['payload_raw'])['result']['hold']['failed_state']
    assert held_value['hold']['failed_state']['buffer']['value']==0
    for error,status in ((PermissionError('private'),403),(CropResultHold('private'),422),(RuntimeError('private'),503)):
        with monkeypatch.context() as patch:
            def fail(*_args,**_kwargs):raise error
            patch.setattr(CropResultStore,'get',fail)
            actual,value=get(app,path)
            assert actual==status and 'private' not in json.dumps(value)
    with monkeypatch.context() as patch:
        def revoke_at_projection(record):
            projected=project_crop_result(record)
            principal['scopes'].remove('crop_result_read')
            return projected
        patch.setattr('app.api_crop_replay.project_crop_result',revoke_at_projection)
        assert get(app,path)[0]==403
    principal['scopes'].add('crop_result_read')
    base,policy,_=login_scope
    doc=json.loads(record['payload_raw']);doc['result']['samples'][0]['state']['fruit']['value']+=1
    corrupted=raw(doc)
    with base.connect() as conn:
        conn.execute(sql.SQL('SET LOCAL ROLE {}').format(sql.Identifier(policy.owner)))
        conn.execute(sql.SQL('ALTER TABLE {} DISABLE TRIGGER crop_result_immutable').format(store.jobs._table('crop_research_results')))
        conn.execute(sql.SQL('UPDATE {} SET payload_raw=%s,payload_sha256=%s WHERE tenant_id=%s AND result_id=%s')
            .format(store.jobs._table('crop_research_results')),(corrupted,sha256(corrupted).hexdigest(),'tenant-1',record['result_id']))
        conn.execute(sql.SQL('ALTER TABLE {} ENABLE TRIGGER crop_result_immutable').format(store.jobs._table('crop_research_results')))
    assert get(app,path)[0]==422
    assert count(store)==before


@pytest.mark.parametrize('login_scope',[CROP_POLICY],indirect=True)
def test_standard_runtime_https_same_saved_result_current_rights_and_cleanup(crop_setup,tls_files,monkeypatch):
    store,body,principal,rights=crop_setup
    record=put(store,body); expected=project_crop_result(record).model_dump(mode='json')
    replay=store.farms.replay; research=replay.owned_research; jobs=store.jobs; holds=replay.thermal.holds
    cert,key,_=tls_files; now=datetime.now(timezone.utc)
    subjects=[('owner','tenant-1',set(READ_SCOPES)),('foreign','foreign-tenant',set(READ_SCOPES)),
              ('denied','tenant-1',set(READ_SCOPES)-{'crop_result_read'})]
    tokens={name:('synthetic-crop-'+name+'-'+'c'*32).encode() for name,_,_ in subjects}
    grants=tuple(BearerGrant(token_digest(tokens[name]),tenant,frozenset(scopes),
        now-timedelta(seconds=1),now+timedelta(minutes=10)) for name,tenant,scopes in subjects)
    def source_factory(*,principal_provider):
        return MarketSourceStore(jobs._dsn,jobs.schema,principal_provider=principal_provider,runtime_identity=jobs.runtime_identity)
    def crop_factory(*,farm_authoring_service):
        return CropResultStore(farm_authoring_service,PROFILE,NOTICE,program_rights=rights,integrity_key=KEY)
    cfg=config(policy=jobs.runtime_identity[0],dsn=jobs._dsn,artifact_root=jobs.artifact_root,
        certificate=cert,private_key=key,port=0)
    deps=dependencies(research_registry=research.catalog,bearer_registry=BearerRegistry(grants),
        owned_fixture_registry=research.registry,owned_research_contexts=dict(research._contexts),
        context_verifier=context_verifier,market_scope_resolver=holds._scope_resolver,
        market_source_factory=source_factory,crop_result_store_factory=crop_factory)
    descriptor=jobs._content_directory(create=True)
    os.close(descriptor)
    runtime=ApiRuntime(cfg,deps)
    assert runtime.crop_results.farms is runtime.farm_authoring and runtime.crop_results.jobs is runtime.jobs
    for bad_factory in (None,lambda **_:store,lambda **_:object()):
        with pytest.raises(ValueError,match='^API runtime assembly rejected$'):
            ApiRuntime(cfg,replace(deps,crop_result_store_factory=bad_factory))
    with pytest.raises(ValueError,match='^API runtime dependencies rejected$'):
        replace(deps,crop_result_store_factory=True)
    before=count(store); path=target(record,body); timings=[]; responses=[]
    monkeypatch.setattr('app.crop_result_store.integrate_crop',lambda **_:pytest.fail('GET reintegrated'))
    server=runtime.service.server(); thread=threading.Thread(target=server.run,daemon=True);thread.start()
    try:
        deadline=time.monotonic()+15
        while not server.started:
            assert thread.is_alive() and time.monotonic()<deadline
            time.sleep(.01)
        port=server.servers[0].sockets[0].getsockname()[1]; trust=ssl.create_default_context(cafile=str(cert))
        def call(where=path,bearer='owner'):
            conn=http.client.HTTPSConnection('127.0.0.1',port,timeout=30,context=trust)
            try:
                started=time.monotonic()
                headers={} if bearer is None else {'Authorization':'Bearer '+tokens[bearer].decode()}
                conn.request('GET',where,headers=headers); response=conn.getresponse(); value=json.loads(response.read())
                timings.append(time.monotonic()-started); responses.append({'status':response.status,'value':value})
                assert response.getheader('cache-control')=='no-store'
                return response.status,value
            finally:conn.close()
        assert call(bearer=None)[0]==401
        assert call(bearer='denied')[0]==403
        assert call(bearer='foreign')[0]==404
        assert call()==call()==(200,expected)
        assert call(target(record,body,crop_id='foreign-crop'))[0]==422
        assert call(path+'&tenant_id=spoofed')[0]==422
        rights.allowed=False
        assert call()[0]==422
        rights.allowed=True
        with monkeypatch.context() as patch:
            patch.setattr(runtime.farm_scenarios.candidates._source._source,'get_input_rights',lambda *_:None)
            assert call()[0]==422
        assert call()==(200,expected)
        with jobs.connect() as conn:
            assert conn.pgconn.used_password
            assert conn.execute(sql.SQL('SELECT count(*) AS n FROM {}').format(jobs._table('thermal_g1_runs'))).fetchone()['n']==0
        assert count(store)==before and current_principal() is None
        assert max(timings)<30
        evidence={'scope':'synthetic_crop_math_only','result_id':record['result_id'],
            'actual_tls_scram':True,'responses':responses,'full_response_seconds':timings,'timeout_seconds':30}
    finally:
        server.should_exit=True; thread.join(timeout=15); assert not thread.is_alive()
    evidence['https_server_joined']=True
    Path('/tmp/ossf-crop-api-https-evidence-20261004.json').write_text(json.dumps(evidence,ensure_ascii=False,indent=2)+'\n')
