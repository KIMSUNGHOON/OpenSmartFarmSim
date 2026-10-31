"""Opt-in owned batch HTTP; test identities and inputs do not approve farm data."""
import asyncio
from hashlib import sha256
import json
from urllib.parse import urlencode

import pytest
from psycopg import sql
from jsonschema import Draft202012Validator

from app.api import create_app
from app.api_economic_batch import BatchSourceService,BatchArtifactRead
from app.economic_batch_calculation import EconomicBatchAuthority
from app.economic_batch_source_store import EconomicBatchSourceStore
from app.economic_production_batches import OwnedProductionBatch
from app.economic_batch_worker import EconomicBatchWorker
from app.job_store import JobStore
from app.market_hold_store import MarketHoldStore
from app.thermal_run_store import ThermalRunStore
from login_database import login_database,login_scope
from test_api_job_status import UnusedMarketResultStore
from test_economic_batch_calculation import PROFILE,assembly
from test_economic_production_batches import scenario,batch_record
from test_market_hold_store import HOLD_KEY,context_verifier
from test_market_source_store import record_items
from test_market_scenario import case
from test_economics import TrustedTestRepository,base,opening_lot
from app.economic_contracts import EconomicScenario
from test_http_identity import request
from test_api_serve import tls_files


def app_for(jobs,holds,contexts,provider,authority):
    return create_app(jobs,holds,contexts,UnusedMarketResultStore(),
        principal_provider=provider,economic_batch_authority=authority)


@pytest.fixture
def source_api(login_scope):
    base_store,policy,dsns=login_scope
    p={'authenticated':True,'tenant_id':'tenant-1','scopes':{'metadata','artifact',
        'economic_batch_source_read','economic_batch_source_write','simulation_execute',
        'decision_context_read','market_hold_context_read'}}
    provider=lambda:p;binding=(policy,'authority')
    jobs=JobStore(dsns['authority'],policy.schema,base_store.artifact_root,
        principal_provider=provider,runtime_identity=binding,audit_runtime_grants=True)
    source=EconomicBatchSourceStore(dsns['authority'],policy.schema,
        principal_provider=provider,runtime_identity=binding)
    contexts=ThermalRunStore(dsns['authority'],policy.schema,gate_key=b'self-authored-gate-test-key-32bytes',
        release_verifier=lambda *_:None,context_verifier=context_verifier,
        principal_provider=provider,runtime_identity=binding)
    holds=MarketHoldStore(dsns['authority'],policy.schema,context_store=contexts,
        scope_resolver=lambda *_:{},signing_key=HOLD_KEY,principal_provider=provider,runtime_identity=binding)
    authority=EconomicBatchAuthority(jobs,source,holds)
    legacy,_=case();prior=TrustedTestRepository(EconomicScenario.model_validate(base(opening_inventory=(opening_lot(),))))
    legacy.prior_costs=prior.prior_costs
    values={kind:model.model_dump(mode='json',exclude={'tenant_id'})for kind,model in record_items(legacy)}
    s=scenario();values['economic_scenario']=s.model_dump(mode='json',exclude={'tenant_id'})
    values['production_batch']=OwnedProductionBatch.model_validate(batch_record(s)).model_dump(mode='json',exclude={'tenant_id'})
    return app_for(jobs,holds,contexts,provider,authority),jobs,source,p,authority,values


def call(app,path,*,method='GET',body=None,raw=None,query=None,media=b'application/json'):
    headers=[(b'content-type',media),(b'x-tenant-id',b'foreign')]
    payload=json.dumps(body,ensure_ascii=False).encode()if raw is None and body is not None else raw or b''
    return asyncio.run(request(app,path=path,method=method,headers=headers,body=payload,
        query=urlencode(query or {}).encode()))


def counts(jobs):
    with jobs.connect()as conn:
        return tuple(conn.execute(sql.SQL('SELECT count(*)AS n FROM {}').format(jobs._table(name))).fetchone()['n']
            for name in ['jobs','economic_batch_source_records','market_source_records'])


@pytest.mark.parametrize('login_scope',[PROFILE],indirect=True)
@pytest.mark.parametrize('kind',['economic_scenario','production_batch','economic_input','joint_shock',
    'input_rights','settlement_applicability','settlement_evidence','prior_batch_cost'])
def test_all_eight_sources_register_list_get_and_preserve_first_bytes(source_api,kind):
    app,jobs,source,p,authority,values=source_api
    body={'kind':kind,'input':values[kind],'idempotency_key':'source-http'}
    status,registered,_=call(app,'/v1/economic-batch-sources',method='POST',body=body)
    assert status==200 and registered['kind']==kind and counts(jobs)==(1,1,0)
    assert registered['admission_kind']=='contract_valid_user_assumption'
    assert call(app,'/v1/economic-batch-sources',method='POST',body=body)[:2]==(200,registered)
    status,found,_=call(app,'/v1/economic-batch-sources/record',query={
        'kind':kind,'record_id':registered['record_id'],'revision':registered['revision']})
    assert status==200 and found['input']==values[kind]and 'tenant_id'not in found['input']
    status,page,_=call(app,'/v1/economic-batch-sources',query={'kind':kind,'limit':1})
    assert status==200 and len(page['items'])==1 and page['items'][0]['payload_sha256']==registered['payload_sha256']
    with jobs.connect()as conn:
        saved=conn.execute(sql.SQL('SELECT * FROM {}').format(jobs._table('economic_batch_source_records'))).fetchone()
        intent=jobs._locked_job(conn,'tenant-1',registered['intent_job']['job_id'])
    assert saved['payload_raw']==jobs._verified_input(intent)
    assert saved['payload_sha256']==registered['payload_sha256']==sha256(saved['payload_raw']).hexdigest()


@pytest.mark.parametrize('login_scope',[PROFILE],indirect=True)
def test_calculation_HTTP_connects_registered_intent_explicit_worker_and_current_raw_result(login_scope,monkeypatch):
    from app.economic_batch_calculation import EconomicBatchCalculationRequest
    from app.economics import canonical_scenario_sha256,EconomicLedger
    from app.economic_production_batches import ProductionBatchLedger
    jobs,source,holds,contexts,p,s,authority,service=assembly(login_scope)
    app=app_for(jobs,holds,contexts,jobs.principal_provider,authority)
    body=EconomicBatchCalculationRequest(scenario_id=s.scenario_id,scenario_revision=s.scenario_revision,
        scenario_sha256=canonical_scenario_sha256(s),idempotency_key='http-calculation').model_dump(mode='json')
    status,job,_=call(app,'/v1/economic-batch-calculations',method='POST',body=body)
    assert status==202 and job['state']=='queued'
    path='/v1/jobs/'+job['job_id']+'/economic-batch-result'
    assert call(app,path)[0]==404
    assert EconomicBatchWorker(authority,tenant_id='tenant-1').run_once(job['job_id']).state=='succeeded'
    raw=jobs.read_artifact('tenant-1',job['job_id']);expected=json.loads(raw)
    p['scopes'].remove('simulation_execute')
    def fail(*a,**k):raise AssertionError('calculation in HTTP result lookup')
    monkeypatch.setattr(ProductionBatchLedger,'calculate',fail)
    monkeypatch.setattr(EconomicLedger,'_calculate_verified',fail)
    status,found,headers=call(app,path)
    assert status==200 and found==expected
    assert headers[b'x-ossf-publication-id']==str(jobs.get_publication('tenant-1',job['job_id'])['publication_id']).encode()
    BatchArtifactRead.model_validate_json(raw)
    Draft202012Validator(BatchArtifactRead.model_json_schema()).validate(found)


@pytest.mark.parametrize('login_scope',[PROFILE],indirect=True)
def test_source_rejects_tenant_unknown_fields_and_bad_transport_before_adoption(source_api):
    app,jobs,source,p,authority,values=source_api;before=counts(jobs)
    body={'kind':'production_batch','input':values['production_batch'],'idempotency_key':'invalid-http'}
    for changed in [body|{'unexpected':1},body|{'input':body['input']|{'tenant_id':'foreign'}},
        body|{'kind':'unknown'},body|{'input':body['input']|{'immutable':1}}]:
        assert call(app,'/v1/economic-batch-sources',method='POST',body=changed)[0]==422
    assert call(app,'/v1/economic-batch-sources',method='POST',body=body,media=b'text/plain')[0]==415
    assert call(app,'/v1/economic-batch-sources',method='POST',raw=b' '*65537)[0]==413
    assert counts(jobs)==before


@pytest.mark.parametrize('login_scope',[PROFILE],indirect=True)
def test_default_app_does_not_install_batch_routes_and_preserves_old_seven_variants(source_api):
    app,jobs,source,p,authority,values=source_api
    old=create_app(jobs,authority._holds,authority._holds._context_store,UnusedMarketResultStore(),
        principal_provider=jobs.principal_provider)
    schema=old.openapi()
    assert '/v1/economic-batch-sources'not in schema['paths']
    original=schema['paths']['/v1/market-user-sources']['post']['requestBody']['content']['application/json']['schema']
    assert len(original['oneOf'])==7


@pytest.mark.parametrize('login_scope',[PROFILE],indirect=True)
def test_eight_request_and_read_schemas_match_actual_wire_and_reject_schema3(source_api):
    app,jobs,source,p,authority,values=source_api
    spec=app.openapi();path=spec['paths']['/v1/economic-batch-sources']['post']
    validator=Draft202012Validator(path['requestBody']['content']['application/json']['schema'])
    assert len(validator.schema['oneOf'])==8
    for kind,value in values.items():
        body={'kind':kind,'input':value,'idempotency_key':'schema-'+kind}
        validator.validate(body)
        assert list(validator.iter_errors(body|{'input':value|{'tenant_id':'tenant-1'}}))
    old=values['economic_scenario'].copy();old.pop('production_batches');old['schema_version']='3'
    body={'kind':'economic_scenario','input':old,'idempotency_key':'schema3'}
    assert list(validator.iter_errors(body))
    assert call(app,'/v1/economic-batch-sources',method='POST',body=body)[0]==422
    assert counts(jobs)==(0,0,0)
    result=spec['paths']['/v1/jobs/{job_id}/economic-batch-result']['get']
    assert result['x-ossf-max-response-bytes']==2097152
    assert result['x-ossf-required-scopes'] and 'simulation_execute'not in result['x-ossf-required-scopes']


@pytest.mark.parametrize('login_scope',[PROFILE],indirect=True)
def test_conflict_and_late_revoke_do_not_leave_partial_source_or_intent(source_api,monkeypatch):
    app,jobs,source,p,authority,values=source_api
    body={'kind':'economic_input','input':values['economic_input'],'idempotency_key':'first'}
    _,first,_=call(app,'/v1/economic-batch-sources',method='POST',body=body)
    assert counts(jobs)==(1,1,0)
    changed=body|{'input':body['input']|{'value':'999'},'idempotency_key':'changed'}
    assert call(app,'/v1/economic-batch-sources',method='POST',body=changed)[0]==409
    assert counts(jobs)==(1,1,0)
    same=body|{'idempotency_key':'new-intent'}
    status,later,_=call(app,'/v1/economic-batch-sources',method='POST',body=same)
    assert status==200 and later['recorded_at']==first['recorded_at']
    assert later['intent_job']['job_id']!=first['intent_job']['job_id']
    before=counts(jobs);original=source._verified
    def revoke(*args):
        value=original(*args);p['scopes'].remove('economic_batch_source_write');return value
    monkeypatch.setattr(source,'_verified',revoke)
    assert call(app,'/v1/economic-batch-sources',method='POST',body=body|{'idempotency_key':'revoked'})[0]==403
    assert counts(jobs)==before


@pytest.mark.parametrize('login_scope',[PROFILE],indirect=True)
def test_unicode_cursor_duplicates_and_json_transport_are_closed(source_api):
    app,jobs,source,p,authority,values=source_api
    body={'kind':'production_batch','input':values['production_batch']|{'batch_id':'자체/가정 batch'},
        'idempotency_key':'unicode'}
    status,registered,_=call(app,'/v1/economic-batch-sources',method='POST',body=body)
    assert status==200
    query={'kind':'production_batch','record_id':registered['record_id'],'revision':registered['revision']}
    assert call(app,'/v1/economic-batch-sources/record',query=query)[1]['input']==body['input']
    for params in [[('kind','production_batch'),('kind','economic_input')],{'kind':'production_batch','tenant_id':'foreign'},
        {'kind':'production_batch','after_record_id':'only-one'},{'kind':'production_batch','limit':51}]:
        assert call(app,'/v1/economic-batch-sources',query=params)[0]==422
    path='/v1/economic-batch-sources'
    before=counts(jobs)
    for raw in [b'{"kind":"production_batch","kind":"production_batch"}',
        b'{"input":{"value":NaN}}',b'{"input":{"value":Infinity}}',b'\xff',b'[]']:
        assert call(app,path,method='POST',raw=raw)[0]==422
    assert counts(jobs)==before


@pytest.mark.parametrize('login_scope',[PROFILE],indirect=True)
@pytest.mark.parametrize('scope',['metadata','economic_batch_source_read','economic_batch_source_write'])
def test_source_write_scopes_are_required_before_adoption(source_api,scope):
    app,jobs,source,p,authority,values=source_api;p['scopes'].remove(scope)
    body={'kind':'production_batch','input':values['production_batch'],'idempotency_key':'denied'}
    assert call(app,'/v1/economic-batch-sources',method='POST',body=body)[0]==403
    assert counts(jobs)==(0,0,0)


@pytest.mark.parametrize('login_scope',[PROFILE],indirect=True)
def test_binding_changes_and_late_read_revoke_hide_payload(source_api,monkeypatch):
    app,jobs,source,p,authority,values=source_api
    body={'kind':'production_batch','input':values['production_batch'],'idempotency_key':'read'}
    _,record,_=call(app,'/v1/economic-batch-sources',method='POST',body=body)
    query={'kind':record['kind'],'record_id':record['record_id'],'revision':record['revision']}
    original=source.get_user_source
    def revoke(*a,**k):
        value=original(*a,**k);p['scopes'].remove('economic_batch_source_read');return value
    monkeypatch.setattr(source,'get_user_source',revoke)
    status,value,_=call(app,'/v1/economic-batch-sources/record',query=query)
    assert status==403 and 'input'not in value
    p['scopes'].add('economic_batch_source_read')
    monkeypatch.setattr(source,'get_user_source',original)
    old=authority._source
    authority._source=EconomicBatchSourceStore(old.dsn,old.schema,
        principal_provider=jobs.principal_provider,runtime_identity=jobs.runtime_identity)
    assert call(app,'/v1/economic-batch-sources/record',query=query)[0]==503


@pytest.mark.parametrize('login_scope',[PROFILE],indirect=True)
def test_authority_source_replacement_inside_adoption_rolls_back_both_rows(source_api,monkeypatch):
    app,jobs,source,p,authority,values=source_api
    other=EconomicBatchSourceStore(source.dsn,source.schema,
        principal_provider=jobs.principal_provider,runtime_identity=jobs.runtime_identity)
    original=source._verified
    def replace_source(*a,**k):
        value=original(*a,**k);authority._source=other;return value
    monkeypatch.setattr(source,'_verified',replace_source)
    body={'kind':'production_batch','input':values['production_batch'],'idempotency_key':'late-authority'}
    status,value,_=call(app,'/v1/economic-batch-sources',method='POST',body=body)
    assert status==503 and 'input'not in value
    assert counts(jobs)==(0,0,0)


@pytest.mark.parametrize('login_scope',[PROFILE],indirect=True)
def test_actual_https_source_calculation_and_fresh_result_enforce_current_identity(login_scope,tls_files,monkeypatch,tmp_path):
    from datetime import datetime,timezone,timedelta
    import http.client,socket,ssl,threading,time
    from psycopg import Connection
    from app.api_economic_batch import SOURCE_WRITE,CALCULATE_SCOPES,RESULT_SCOPES
    from app.http_identity import BearerGrant,BearerRegistry,PrincipalMiddleware,current_principal,token_digest
    from app.https_service import HttpsApiService
    from app.economics import canonical_scenario_sha256,EconomicLedger
    from app.economic_production_batches import ProductionBatchLedger
    jobs,source,holds,contexts,p,s,authority,service=assembly(login_scope)
    # New request-bound objects use the same owned database and signed fixture evidence.
    provider=current_principal;binding=jobs.runtime_identity
    fresh_jobs=JobStore(jobs._dsn,jobs.schema,jobs.artifact_root,principal_provider=provider,
        runtime_identity=binding,audit_runtime_grants=True)
    fresh_source=EconomicBatchSourceStore(source.dsn,source.schema,principal_provider=provider,runtime_identity=binding)
    fresh_contexts=ThermalRunStore(contexts.dsn,contexts.schema,gate_key=contexts._gate_key,
        release_verifier=contexts._release_verifier,context_verifier=contexts._context_verifier,
        principal_provider=provider,runtime_identity=binding)
    fresh_holds=MarketHoldStore(holds.dsn,holds.schema,context_store=fresh_contexts,
        scope_resolver=holds._scope_resolver,signing_key=holds._key,principal_provider=provider,runtime_identity=binding)
    fresh=EconomicBatchAuthority(fresh_jobs,fresh_source,fresh_holds)
    app=app_for(fresh_jobs,fresh_holds,fresh_contexts,provider,fresh)
    now=datetime.now(timezone.utc);clock=[now]
    tokens=[b'synthetic-batch-https-'+bytes([letter])*32 for letter in (97,98,99)]
    grants=tuple(BearerGrant(token_digest(token),tenant,frozenset(scopes),now-timedelta(seconds=1),now+timedelta(minutes=5))
        for token,tenant,scopes in zip(tokens,['tenant-1','tenant-1','foreign'],
            [set(SOURCE_WRITE+CALCULATE_SCOPES+RESULT_SCOPES),set(RESULT_SCOPES),set(RESULT_SCOPES)]))
    cert,key,_=tls_files
    with socket.socket()as probe:probe.bind(('127.0.0.1',0));port=probe.getsockname()[1]
    server=HttpsApiService(PrincipalMiddleware(app,BearerRegistry(grants,clock=lambda:clock[0])),cert,key,port=port).server()
    thread=threading.Thread(target=server.run,daemon=True);thread.start()
    context=ssl.create_default_context(cafile=str(cert))
    def https(path,*,method='GET',body=None,token=tokens[0]):
        conn=http.client.HTTPSConnection('127.0.0.1',port,timeout=10,context=context)
        try:
            headers={'Content-Type':'application/json','X-Tenant-ID':'foreign','X-Forwarded-Proto':'http'}
            if token is not None:headers['Authorization']='Bearer '+token.decode()
            conn.request(method,path,body=json.dumps(body)if body is not None else None,headers=headers)
            response=conn.getresponse();raw=response.read()
            return response.status,raw,dict(response.getheaders())
        finally:conn.close()
    try:
        deadline=time.monotonic()+10
        while not server.started:
            assert thread.is_alive()and time.monotonic()<deadline
            time.sleep(.01)
        body={'kind':'economic_scenario','input':s.model_dump(mode='json',exclude={'tenant_id'}),'idempotency_key':'https-source'}
        assert https('/v1/economic-batch-sources',method='POST',body=body,token=None)[0]==401
        assert https('/v1/economic-batch-sources',method='POST',body=body,token=tokens[1])[0]==403
        status,raw,headers=https('/v1/economic-batch-sources',method='POST',body=body)
        assert status==200 and json.loads(raw)['kind']=='economic_scenario'
        assert headers['strict-transport-security']and headers['cache-control']=='no-store'and 'server'not in headers
        calc={'scenario_id':s.scenario_id,'scenario_revision':s.scenario_revision,
            'scenario_sha256':canonical_scenario_sha256(s),'idempotency_key':'https-calculation'}
        status,raw,_=https('/v1/economic-batch-calculations',method='POST',body=calc)
        assert status==202;job=json.loads(raw);path='/v1/jobs/'+job['job_id']+'/economic-batch-result'
        assert https('/v1/economic-batch-calculations',method='POST',body=calc)[1]==raw
        assert https(path)[0]==404
        assert EconomicBatchWorker(authority,tenant_id='tenant-1').run_once(job['job_id']).state=='succeeded'
        expected=jobs.read_artifact('tenant-1',job['job_id']);publication=jobs.get_publication('tenant-1',job['job_id'])
        writes=[];execute=Connection.execute
        def measured(conn,*a,**k):
            cursor=execute(conn,*a,**k)
            if(cursor.statusmessage or '').split(' ')[0]in {'INSERT','UPDATE','DELETE','MERGE','CREATE','ALTER','DROP','TRUNCATE','GRANT','REVOKE'}:writes.append(cursor.statusmessage)
            return cursor
        def fail(*a,**k):raise AssertionError('calculation during HTTPS stored read')
        monkeypatch.setattr(Connection,'execute',measured)
        monkeypatch.setattr(ProductionBatchLedger,'calculate',fail)
        monkeypatch.setattr(EconomicLedger,'_calculate_verified',fail)
        status,found,headers=https(path,token=tokens[1])
        assert status==200 and found==expected and not writes
        assert headers['x-ossf-publication-id']==str(publication['publication_id'])
        assert headers['x-ossf-published-at']==publication['published_at'].isoformat()
        assert https(path,token=tokens[2])[0]==404
        assert https(path+'?tenant_id=foreign',token=tokens[1])[0]==422
        clock[0]=now+timedelta(minutes=6)
        assert https(path,token=tokens[1])[0]==401
        assert not writes and current_principal()is None
        proof={'artifact_sha256':sha256(found).hexdigest(),'artifact_bytes':len(found),
            'publication_id':str(publication['publication_id']),'published_at':publication['published_at'].isoformat(),
            'real_verified_TLS':True,'owned_host_SCRAM':True,'result_SQL_writes':len(writes),
            'result_amount_calls':0,'result_execution_scope':False,'automatic_consumer':False,
            'G0_G4':'not_assessed','R2':'not_approved'}
        (tmp_path/'https-result-receipt.private.json').write_text(json.dumps(proof,indent=2))
    finally:
        server.should_exit=True;thread.join(timeout=10)
    assert not thread.is_alive()
