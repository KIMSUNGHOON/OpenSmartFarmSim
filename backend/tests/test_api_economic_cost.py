"""Protected cost HTTP over owned synthetic SCRAM evidence; no farm approval."""
from copy import copy,deepcopy
from datetime import datetime,timezone,timedelta
from hashlib import sha256
import json

import pytest
from jsonschema import Draft202012Validator
from psycopg import Connection,sql

from app.api import create_app
from app.economic_cost_wire import CostArtifactRead
from app import economic_cost_trace as trace
from app.economic_batch_calculation import EconomicBatchAuthority
from app.economic_batch_query import EconomicBatchResultQuery
from app.economic_batch_source_store import EconomicBatchSourceStore
from app.economic_cost_calculation import EconomicCostCalculationService
from app.economic_cost_query import EconomicCostResultQuery
from app.economic_cost_worker import EconomicCostWorker
from app.economic_production_batches import ProductionBatchLedger
from app.economics import EconomicLedger
from app.job_store import JobStore
from app.market_hold_store import MarketHoldStore
from app.thermal_run_store import ThermalRunStore
from login_database import login_database,login_scope
from test_api_economic_batch import app_for,call,counts,source_api
from test_api_job_status import UnusedMarketResultStore
from test_api_serve import tls_files
from test_economic_batch_calculation import PROFILE,assembly,request
from test_economic_cost_query import no_replay

POST='/v1/economic-cost-calculations'
RESULT='/v1/jobs/{job_id}/economic-cost-result'
READ=('metadata','economic_batch_source_read','decision_context_read','market_hold_context_read','artifact')
SUBMIT=READ[:-1]+('simulation_execute',)


def api_setup(scope):
    jobs,source,holds,contexts,p,s,authority,base=assembly(scope)
    app=app_for(jobs,holds,contexts,jobs.principal_provider,authority)
    return app,jobs,source,holds,contexts,p,s,authority,base


def ready(scope):
    values=api_setup(scope);app,jobs,source,holds,contexts,p,s,authority,base=values
    status,job,_=call(app,POST,method='POST',body=request(s,'http-cost').model_dump(mode='json'))
    assert status==202
    assert EconomicCostWorker(authority,tenant_id='tenant-1').run_once(job['job_id']).state=='succeeded'
    p['scopes'].remove('simulation_execute')
    return values,job,RESULT.format(job_id=job['job_id'])


def assert_private_error(status,value,expected):
    assert status==expected and set(value)=={'error'}
    assert 'result'not in value and 'input'not in value


@pytest.mark.parametrize('login_scope',[PROFILE],indirect=True)
def test_cost_HTTP_admits_reference_without_math_then_explicit_worker_and_readonly_original_result(login_scope,monkeypatch,tmp_path):
    values=api_setup(login_scope);app,jobs,source,holds,contexts,p,s,authority,base=values
    body=request(s,'cost-http-flow').model_dump(mode='json');before=counts(jobs)
    with monkeypatch.context()as patch:
        no_replay(patch)
        status,job,_=call(app,POST,method='POST',body=body)
        assert status==202 and job['state']=='queued'
        assert call(app,POST,method='POST',body=body)[:2]==(202,job)
        assert counts(jobs)==(before[0]+1,before[1],before[2])
        path=RESULT.format(job_id=job['job_id']);assert call(app,path)[0]==404
    calls=[];calculate=trace.CostLineLedger.calculate;calculate_base=ProductionBatchLedger.calculate
    with monkeypatch.context()as patch:
        def counted(*a,**k):calls.append('trace');return calculate(*a,**k)
        def counted_base(*a,**k):calls.append('v10');return calculate_base(*a,**k)
        patch.setattr(trace.CostLineLedger,'calculate',counted)
        patch.setattr(ProductionBatchLedger,'calculate',counted_base)
        assert EconomicCostWorker(authority,tenant_id='tenant-1').run_once(job['job_id']).state=='succeeded'
    assert calls==['trace','v10']
    expected=jobs.read_artifact('tenant-1',job['job_id']);publication=jobs.get_publication('tenant-1',job['job_id'])
    p['scopes'].remove('simulation_execute');no_replay(monkeypatch);writes=[];execute=Connection.execute
    def measured(conn,*a,**k):
        cursor=execute(conn,*a,**k)
        if(cursor.statusmessage or '').split(' ')[0]in {'INSERT','UPDATE','DELETE','MERGE','CREATE','ALTER','DROP','TRUNCATE','GRANT','REVOKE'}:
            writes.append(cursor.statusmessage)
        return cursor
    monkeypatch.setattr(Connection,'execute',measured)
    status,found,headers=call(app,path)
    assert status==200 and found==json.loads(expected)and not writes
    assert headers[b'cache-control']==b'no-store'
    assert headers[b'x-ossf-publication-id']==str(publication['publication_id']).encode()
    assert headers[b'x-ossf-published-at']==publication['published_at'].isoformat().encode()
    assert call(app,path)[1]==found and jobs.get_publication('tenant-1',job['job_id'])==publication
    CostArtifactRead.model_validate_json(expected)
    Draft202012Validator(CostArtifactRead.model_json_schema()).validate(found)
    proof={'observed_at_UTC':datetime.now(timezone.utc).isoformat(),'job_id':job['job_id'],
        'artifact_sha256':sha256(expected).hexdigest(),'artifact_bytes':len(expected),
        'publication_id':str(publication['publication_id']),'published_at':publication['published_at'].isoformat(),
        'trace_id':found['result']['trace_id'],'actual_trace_calls':1,'actual_v10_calls':1,
        'admission_amount_calls':0,'result_amount_calls':0,'result_SQL_writes':len(writes),
        'result_execution_scope':False,'same_first_publication':True,'synthetic_QA_only':True,
        'G0_G4':'not_assessed','R2':'not_approved'}
    (tmp_path/'cost-http-result-v1.json').write_bytes(expected)
    (tmp_path/'cost-http-receipt-v1.private.json').write_text(json.dumps(proof,indent=2)+'\n')


@pytest.mark.parametrize('login_scope',[PROFILE],indirect=True)
def test_cost_HTTP_retry_conflict_and_original_batch_namespace_preserve_jobs(login_scope):
    values=api_setup(login_scope);app,jobs,source,holds,contexts,p,s,authority,base=values
    body=request(s,'same-cost-http-key').model_dump(mode='json')
    status,first,_=call(app,POST,method='POST',body=body);assert status==202
    assert call(app,POST,method='POST',body=body)[:2]==(202,first)
    other=s.model_copy(update={'scenario_revision':'http-r2'})
    source_job=jobs.submit('tenant-1','collection',other.model_dump(mode='json'),'cost-http-second-source')
    source.adopt_job('tenant-1','economic_scenario',str(source_job['job_id']));before=counts(jobs)
    status,value,_=call(app,POST,method='POST',body=request(other,'same-cost-http-key').model_dump(mode='json'))
    assert_private_error(status,value,409);assert counts(jobs)==before
    status,old,_=call(app,'/v1/economic-batch-calculations',method='POST',body=body)
    assert status==202 and old['job_id']!=first['job_id']
    assert call(app,RESULT.format(job_id=old['job_id']))[0]==404
    assert jobs.get_publication('tenant-1',first['job_id'])is None


@pytest.mark.parametrize('login_scope',[PROFILE],indirect=True)
def test_cost_submission_rejects_nonreferences_unknown_fields_and_metadata_overrides(login_scope,monkeypatch):
    values=api_setup(login_scope);app,jobs,source,holds,contexts,p,s,authority,base=values
    body=request(s).model_dump(mode='json');before=counts(jobs);no_replay(monkeypatch)
    invalid=[{},{'schema_version':'4','variable_costs':[]},body|{'amount':'20'},body|{'tenant_id':'foreign'},
        body|{'trace_version':'economic-cost-line-trace-v1'},body|{'code_sha256':'f'*64},
        body|{'component_sha256':{}},body|{'base_input':{}},body|{'scenario_source_job_id':'user-choice'}]
    for value in invalid:
        status,found,_=call(app,POST,method='POST',body=value);assert_private_error(status,found,422)
    full_scenario=s.model_dump(mode='json')
    assert len(json.dumps(full_scenario,ensure_ascii=False).encode())>4096
    status,found,_=call(app,POST,method='POST',body=full_scenario);assert_private_error(status,found,413)
    assert counts(jobs)==before


@pytest.mark.parametrize('login_scope',[PROFILE],indirect=True)
def test_cost_submission_json_transport_media_and_4096_byte_limit_are_closed(login_scope,monkeypatch):
    values=api_setup(login_scope);app,jobs,source,holds,contexts,p,s,authority,base=values
    before=counts(jobs);no_replay(monkeypatch)
    for value in (b'{"scenario_id":"x","scenario_id":"x"}',b'{"amount":NaN}',
            b'{"amount":Infinity}',b'\xff',b'[]',b'null'):
        status,found,_=call(app,POST,method='POST',raw=value);assert_private_error(status,found,422)
    assert call(app,POST,method='POST',body=request(s).model_dump(mode='json'),media=b'text/plain')[0]==415
    assert call(app,POST,method='POST',raw=b' '*4097)[0]==413
    assert counts(jobs)==before


@pytest.mark.parametrize('login_scope',[PROFILE],indirect=True)
def test_cost_query_parameters_and_canonical_UUID_are_closed_before_result_read(login_scope,monkeypatch):
    values=api_setup(login_scope);app,jobs,source,holds,contexts,p,s,authority,base=values
    def fail(*a,**k):raise AssertionError('result query reached for invalid HTTP parameters')
    monkeypatch.setattr(EconomicCostResultQuery,'read',fail)
    path=RESULT.format(job_id='00000000-0000-0000-0000-000000000000')
    for params in ({'tenant_id':'foreign'},[('view','one'),('view','two')]):
        assert call(app,path,query=params)[0]==422
        assert call(app,POST,method='POST',body=request(s).model_dump(mode='json'),query=params)[0]==422
    for bad in ('invalid','ABCDEFAB-CDEF-ABCD-EFAB-CDEFABCDEFAB'):
        assert call(app,RESULT.format(job_id=bad))[0]==422


@pytest.mark.parametrize('login_scope',[PROFILE],indirect=True)
def test_cost_optin_preserves_default_routes_batch_paths_and_source_eight_schema(source_api):
    app,jobs,source,p,authority,values=source_api
    default=create_app(jobs,authority._holds,authority._holds._context_store,UnusedMarketResultStore(),
        principal_provider=jobs.principal_provider)
    paths=default.openapi()['paths'];assert POST not in paths and RESULT not in paths
    assert len(paths['/v1/market-user-sources']['post']['requestBody']['content']['application/json']['schema']['oneOf'])==7
    spec=app.openapi();assert '/v1/economic-batch-calculations'in spec['paths']
    assert '/v1/jobs/{job_id}/economic-batch-result'in spec['paths']
    variants=spec['paths']['/v1/economic-batch-sources']['post']['requestBody']['content']['application/json']['schema']
    assert len(variants['oneOf'])==8
    Draft202012Validator(variants).validate({'kind':'production_batch','input':values['production_batch'],'idempotency_key':'source-compatible'})
    submit=spec['paths'][POST]['post'];result=spec['paths'][RESULT]['get']
    assert submit['x-ossf-max-body-bytes']==4096 and result['x-ossf-max-response-bytes']==2097152
    assert 'simulation_execute'in submit['x-ossf-required-scopes']
    assert 'simulation_execute'not in result['x-ossf-required-scopes']
    assert set(result['x-ossf-required-scopes'])==set(READ)


@pytest.mark.parametrize('login_scope',[PROFILE],indirect=True)
def test_cost_wire_Pydantic_and_JSONSchema_keep_nested_Decimal_null_inventory_and_closed_gates(login_scope):
    values,job,path=ready(login_scope);app,jobs,source,holds,contexts,p,s,authority,base=values
    value=json.loads(jobs.read_artifact('tenant-1',job['job_id']));validator=Draft202012Validator(CostArtifactRead.model_json_schema())
    def valid(candidate):CostArtifactRead.model_validate_json(json.dumps(candidate));validator.validate(candidate)
    valid(value)
    alternate=deepcopy(value)
    alternate['result']['base_result']['ledger']['operating_cash']=None
    alternate['result']['base_result']['ledger']['closing_inventory']=[{
        'batch_id':'wire-only','grade':'A','channel':'direct','quantity_kg':'1E-9'}]
    alternate['result']['lines'][0]['incurred']='2E-9';valid(alternate)
    for name in ('numeric','nan','extra','gate','trace_id','trace_version','component','base_numeric','inventory_numeric'):
        bad=deepcopy(value)
        if name=='numeric':bad['result']['lines'][0]['incurred']=20
        elif name=='nan':bad['result']['lines'][0]['incurred']='NaN'
        elif name=='extra':bad['result']['lines'][0]['unexpected']='field'
        elif name=='gate':bad['result']['G0_G4']='pass'
        elif name=='trace_id':bad['result']['trace_id']='invalid'
        elif name=='trace_version':bad['result']['trace_version']='unsupported'
        elif name=='component':bad['result']['component_sha256']={'component':'invalid'}
        elif name=='base_numeric':bad['result']['base_result']['ledger']['variable_cost']=20
        else:bad=deepcopy(alternate);bad['result']['base_result']['ledger']['closing_inventory'][0]['quantity_kg']=1
        with pytest.raises(ValueError):CostArtifactRead.model_validate_json(json.dumps(bad))
        assert list(validator.iter_errors(bad))


@pytest.mark.parametrize('login_scope',[PROFILE],indirect=True)
@pytest.mark.parametrize('scope',SUBMIT)
def test_cost_submission_requires_each_current_scope_before_new_intent(login_scope,scope):
    values=api_setup(login_scope);app,jobs,source,holds,contexts,p,s,authority,base=values
    before=counts(jobs);p['scopes'].remove(scope)
    status,value,_=call(app,POST,method='POST',body=request(s).model_dump(mode='json'))
    assert_private_error(status,value,403);assert counts(jobs)==before


@pytest.mark.parametrize('login_scope',[PROFILE],indirect=True)
@pytest.mark.parametrize('scope',READ)
def test_cost_result_requires_each_current_read_scope(login_scope,scope):
    values,job,path=ready(login_scope);app,jobs,source,holds,contexts,p,s,authority,base=values
    p['scopes'].remove(scope);status,value,_=call(app,path);assert_private_error(status,value,403)


@pytest.mark.parametrize('login_scope',[PROFILE],indirect=True)
def test_cost_authentication_and_foreign_tenant_never_return_owned_payload(login_scope):
    values,job,path=ready(login_scope);app,jobs,source,holds,contexts,p,s,authority,base=values
    p['authenticated']=False
    status,value,_=call(app,path);assert_private_error(status,value,401)
    p['authenticated']=True;p['tenant_id']='foreign'
    status,value,_=call(app,path);assert_private_error(status,value,404)


@pytest.mark.parametrize('login_scope',[PROFILE],indirect=True)
def test_late_result_scope_revocations_hide_already_read_cost_buffer(login_scope,monkeypatch):
    values,job,path=ready(login_scope);app,jobs,source,holds,contexts,p,s,authority,base=values
    read=EconomicCostResultQuery.read
    for scope in ('metadata','artifact','economic_batch_source_read'):
        def revoke(*a,**k):value=read(*a,**k);p['scopes'].remove(scope);return value
        try:
            with monkeypatch.context()as patch:
                patch.setattr(EconomicCostResultQuery,'read',revoke)
                status,value,_=call(app,path);assert_private_error(status,value,403)
        finally:p['scopes'].add(scope)


@pytest.mark.parametrize('login_scope',[PROFILE],indirect=True)
@pytest.mark.parametrize('part',['root','authority'])
def test_late_HTTP_binding_changes_hide_already_read_cost_buffer(login_scope,monkeypatch,tmp_path,part):
    values,job,path=ready(login_scope);app,jobs,source,holds,contexts,p,s,authority,base=values
    read=EconomicCostResultQuery.read
    def change(*a,**k):
        value=read(*a,**k)
        if part=='root':jobs.artifact_root=tmp_path/'changed-cost-root'
        else:authority._source=copy(authority._source)
        return value
    monkeypatch.setattr(EconomicCostResultQuery,'read',change)
    status,value,_=call(app,path);assert_private_error(status,value,503)


@pytest.mark.parametrize('login_scope',[PROFILE],indirect=True)
def test_late_HTTP_trace_code_change_hides_already_read_cost_buffer(login_scope,monkeypatch):
    values,job,path=ready(login_scope);app,jobs,source,holds,contexts,p,s,authority,base=values
    read=EconomicCostResultQuery.read
    def change(*a,**k):
        value=read(*a,**k);monkeypatch.setattr(trace,'CODE_SHA256','f'*64);return value
    monkeypatch.setattr(EconomicCostResultQuery,'read',change)
    status,value,_=call(app,path);assert_private_error(status,value,422)
    assert value['error']['code']=='economic_cost_hold'


@pytest.mark.parametrize('login_scope',[PROFILE],indirect=True)
def test_current_source_hold_and_restore_preserve_original_cost_bytes_and_publication(login_scope,monkeypatch):
    values,job,path=ready(login_scope);app,jobs,source,holds,contexts,p,s,authority,base=values
    expected=jobs.read_artifact('tenant-1',job['job_id']);publication=jobs.get_publication('tenant-1',job['job_id'])
    pin=source.get_economic_scenario_pin
    with monkeypatch.context()as patch:
        patch.setattr(source,'get_economic_scenario_pin',lambda *a:{**pin(*a),'payload_sha256':'f'*64})
        status,value,_=call(app,path);assert_private_error(status,value,422)
    assert call(app,path)[:2]==(200,json.loads(expected))
    assert jobs.get_publication('tenant-1',job['job_id'])==publication


@pytest.mark.parametrize('login_scope',[PROFILE],indirect=True)
def test_late_submission_execute_revoke_rolls_back_cost_job_and_event(login_scope,monkeypatch):
    values=api_setup(login_scope);app,jobs,source,holds,contexts,p,s,authority,base=values
    before=counts(jobs);event=jobs._event
    def revoked(*a,**k):value=event(*a,**k);p['scopes'].remove('simulation_execute');return value
    monkeypatch.setattr(jobs,'_event',revoked)
    status,value,_=call(app,POST,method='POST',body=request(s,'late-cost-http').model_dump(mode='json'))
    assert_private_error(status,value,403);assert counts(jobs)==before


@pytest.mark.parametrize('login_scope',[PROFILE],indirect=True)
def test_scaled_64_byte_publication_limit_is_hold_not_full_2MiB_load_proof(login_scope,monkeypatch):
    from app import economic_batch_query
    values,job,path=ready(login_scope);app,jobs,source,holds,contexts,p,s,authority,base=values
    assert app.openapi()['paths'][RESULT]['get']['x-ossf-max-response-bytes']==2097152
    monkeypatch.setattr(economic_batch_query,'MAX_ARTIFACT_BYTES',64)
    status,value,_=call(app,path);assert_private_error(status,value,422)


@pytest.mark.parametrize('login_scope',[PROFILE],indirect=True)
def test_actual_unknown_payment_is_null_on_cost_HTTP_wire(login_scope):
    values=api_setup(login_scope);app,jobs,source,holds,contexts,p,s,authority,base=values
    cost=s.variable_costs[0].model_copy(update={'paid_at':None,'payment':None})
    partial=s.model_copy(update={'scenario_revision':'http-payment-unknown','variable_costs':(cost,)})
    source_job=jobs.submit('tenant-1','collection',partial.model_dump(mode='json'),'http-partial-cost-source')
    source.adopt_job('tenant-1','economic_scenario',str(source_job['job_id']))
    status,job,_=call(app,POST,method='POST',body=request(partial,'http-partial-cost').model_dump(mode='json'))
    assert status==202
    assert EconomicCostWorker(authority,tenant_id='tenant-1').run_once(job['job_id']).state=='succeeded'
    p['scopes'].remove('simulation_execute')
    status,value,_=call(app,RESULT.format(job_id=job['job_id']));assert status==200
    assert value['result']['lines'][0]['bank_paid_in_period']is None
    assert value['result']['base_result']['ledger']['operating_cash']is None
    CostArtifactRead.model_validate_json(json.dumps(value))
    Draft202012Validator(CostArtifactRead.model_json_schema()).validate(value)


@pytest.mark.parametrize('login_scope',[PROFILE],indirect=True)
def test_cost_optin_factory_rejects_nonactual_or_rebound_authority(source_api):
    app,jobs,source,p,authority,values=source_api
    with pytest.raises(ValueError):app_for(jobs,authority._holds,authority._holds._context_store,jobs.principal_provider,object())
    changed=copy(authority);changed.jobs=copy(jobs)
    with pytest.raises(ValueError):app_for(jobs,authority._holds,authority._holds._context_store,jobs.principal_provider,changed)


@pytest.mark.parametrize('login_scope',[PROFILE],indirect=True)
def test_actual_verified_TLS_cost_post_original_raw_read_hold_restore_and_first_timestamp(login_scope,tls_files,monkeypatch,tmp_path):
    import http.client,socket,ssl,threading,time
    from app.http_identity import BearerGrant,BearerRegistry,PrincipalMiddleware,current_principal,token_digest
    from app.https_service import HttpsApiService
    values=api_setup(login_scope);app,jobs,source,holds,contexts,p,s,authority,base=values
    provider=current_principal;binding=jobs.runtime_identity
    fresh_jobs=JobStore(jobs._dsn,jobs.schema,jobs.artifact_root,principal_provider=provider,
        runtime_identity=binding,audit_runtime_grants=True)
    fresh_source=EconomicBatchSourceStore(source.dsn,source.schema,principal_provider=provider,runtime_identity=binding)
    fresh_context=ThermalRunStore(contexts.dsn,contexts.schema,gate_key=contexts._gate_key,
        release_verifier=contexts._release_verifier,context_verifier=contexts._context_verifier,
        principal_provider=provider,runtime_identity=binding)
    fresh_holds=MarketHoldStore(holds.dsn,holds.schema,context_store=fresh_context,
        scope_resolver=holds._scope_resolver,signing_key=holds._key,principal_provider=provider,runtime_identity=binding)
    fresh=EconomicBatchAuthority(fresh_jobs,fresh_source,fresh_holds)
    fresh_app=app_for(fresh_jobs,fresh_holds,fresh_context,provider,fresh)
    now=datetime.now(timezone.utc);clock=[now]
    tokens=[b'synthetic-cost-https-'+bytes([letter])*32 for letter in (97,98,99)]
    grants=tuple(BearerGrant(token_digest(token),tenant,frozenset(scopes),now-timedelta(seconds=1),now+timedelta(minutes=5))
        for token,tenant,scopes in zip(tokens,['tenant-1','tenant-1','foreign'],[set(SUBMIT+READ),set(READ),set(READ)]))
    cert,key,_=tls_files
    with socket.socket()as probe:probe.bind(('127.0.0.1',0));port=probe.getsockname()[1]
    server=HttpsApiService(PrincipalMiddleware(fresh_app,BearerRegistry(grants,clock=lambda:clock[0])),cert,key,port=port).server()
    thread=threading.Thread(target=server.run,daemon=True);thread.start();context=ssl.create_default_context(cafile=str(cert))
    def https(path,*,method='GET',body=None,token=tokens[0]):
        conn=http.client.HTTPSConnection('127.0.0.1',port,timeout=15,context=context)
        try:
            headers={'Content-Type':'application/json','X-Tenant-ID':'foreign','X-Forwarded-Proto':'http'}
            if token is not None:headers['Authorization']='Bearer '+token.decode()
            conn.request(method,path,body=json.dumps(body)if body is not None else None,headers=headers)
            response=conn.getresponse();encoded=response.read()
            return response.status,encoded,{name.lower():value for name,value in response.getheaders()}
        finally:conn.close()
    try:
        deadline=time.monotonic()+10
        while not server.started:
            assert thread.is_alive()and time.monotonic()<deadline
            time.sleep(.01)
        body=request(s,'tls-cost-http').model_dump(mode='json')
        assert https(POST,method='POST',body=body,token=None)[0]==401
        assert https(POST,method='POST',body=body,token=tokens[1])[0]==403
        with monkeypatch.context()as patch:
            no_replay(patch)
            status,encoded,headers=https(POST,method='POST',body=body)
            assert status==202 and headers['cache-control']=='no-store'
            assert https(POST,method='POST',body=body)[1]==encoded
        job=json.loads(encoded);path=RESULT.format(job_id=job['job_id'])
        assert https(path,token=tokens[1])[0]==404
        assert EconomicCostWorker(authority,tenant_id='tenant-1').run_once(job['job_id']).state=='succeeded'
        expected=jobs.read_artifact('tenant-1',job['job_id']);publication=jobs.get_publication('tenant-1',job['job_id'])
        no_replay(monkeypatch);writes=[];execute=Connection.execute
        def measured(conn,*a,**k):
            cursor=execute(conn,*a,**k)
            if(cursor.statusmessage or '').split(' ')[0]in {'INSERT','UPDATE','DELETE','MERGE','CREATE','ALTER','DROP','TRUNCATE','GRANT','REVOKE'}:
                writes.append(cursor.statusmessage)
            return cursor
        monkeypatch.setattr(Connection,'execute',measured)
        status,found,headers=https(path,token=tokens[1])
        assert status==200 and found==expected and not writes
        assert headers['strict-transport-security']and headers['cache-control']=='no-store'and'server'not in headers
        assert headers['x-ossf-publication-id']==str(publication['publication_id'])
        assert headers['x-ossf-published-at']==publication['published_at'].isoformat()
        CostArtifactRead.model_validate_json(found)
        Draft202012Validator(CostArtifactRead.model_json_schema()).validate(json.loads(found))
        pin=fresh_source.get_economic_scenario_pin
        with monkeypatch.context()as patch:
            patch.setattr(fresh_source,'get_economic_scenario_pin',lambda *a:{**pin(*a),'payload_sha256':'f'*64})
            held,hold_raw,hold_headers=https(path,token=tokens[1])
            assert held==422 and json.loads(hold_raw)['error']['code']=='economic_cost_hold'
            assert hold_headers['cache-control']=='no-store'and'server'not in hold_headers
        assert https(path,token=tokens[1])[1]==expected
        assert https(path,token=tokens[2])[0]==404
        assert https(path+'?tenant_id=foreign',token=tokens[1])[0]==422
        clock[0]=now+timedelta(minutes=6)
        assert https(path,token=tokens[1])[0]==401
        assert not writes and current_principal()is None
        proof={'observed_at_UTC':datetime.now(timezone.utc).isoformat(),
            'artifact_sha256':sha256(found).hexdigest(),'artifact_bytes':len(found),
            'publication_id':str(publication['publication_id']),'published_at':publication['published_at'].isoformat(),
            'real_verified_TLS':True,'owned_host_SCRAM':True,'hold_status':held,'restored_same_raw':True,
            'result_SQL_writes':len(writes),'result_amount_calls':0,'result_execution_scope':False,
            'automatic_consumer':False,'G0_G4':'not_assessed','R2':'not_approved'}
        (tmp_path/'cost-https-result-v1.json').write_bytes(found)
        (tmp_path/'cost-https-receipt-v1.private.json').write_text(json.dumps(proof,indent=2)+'\n')
    finally:
        server.should_exit=True;thread.join(timeout=10)
        cert.unlink(missing_ok=True);key.unlink(missing_ok=True)
    assert not thread.is_alive()


@pytest.mark.parametrize('login_scope',[PROFILE],indirect=True)
def test_precommit_HTTP_root_or_check_callback_replacement_rolls_back_actual_job_and_event(login_scope,monkeypatch,tmp_path):
    values=api_setup(login_scope);app,jobs,source,holds,contexts,p,s,authority,base=values
    submit=EconomicCostCalculationService.submit;event=jobs._event;services=[];root=jobs.artifact_root
    def job_events():
        with jobs.connect()as conn:
            return tuple(conn.execute(sql.SQL('SELECT count(*)AS n FROM {}').format(jobs._table(name))).fetchone()['n']
                for name in ('jobs','job_events'))
    def captured(self,*a,**k):services.append(self);return submit(self,*a,**k)
    no_replay(monkeypatch)
    for part in ('root','callback'):
        before=job_events()
        with monkeypatch.context()as patch:
            patch.setattr(EconomicCostCalculationService,'submit',captured)
            def change(*a,**k):
                value=event(*a,**k)
                if part=='root':jobs.artifact_root=tmp_path/'changed-before-cost-commit'
                else:patch.setattr(services[-1],'_http_check',lambda *_:None)
                return value
            patch.setattr(jobs,'_event',change)
            try:
                status,value,_=call(app,POST,method='POST',body=request(s,'precommit-cost-'+part).model_dump(mode='json'))
            finally:jobs.artifact_root=root
            assert_private_error(status,value,503)
            assert job_events()==before


@pytest.mark.parametrize('login_scope',[PROFILE],indirect=True)
def test_postcommit_HTTP_binding_change_suppresses_202_but_retry_preserves_committed_intent(login_scope,monkeypatch,tmp_path):
    values=api_setup(login_scope);app,jobs,source,holds,contexts,p,s,authority,base=values
    submit=EconomicCostCalculationService.submit;committed=[];root=jobs.artifact_root
    body=request(s,'postcommit-cost-http').model_dump(mode='json');before=counts(jobs);no_replay(monkeypatch)
    def changed(self,*a,**k):
        value=submit(self,*a,**k);committed.append(value)
        jobs.artifact_root=tmp_path/'changed-after-cost-commit'
        return value
    with monkeypatch.context()as patch:
        patch.setattr(EconomicCostCalculationService,'submit',changed)
        try:
            status,value,_=call(app,POST,method='POST',body=body)
        finally:jobs.artifact_root=root
        assert_private_error(status,value,503)
    assert len(committed)==1 and counts(jobs)==(before[0]+1,before[1],before[2])
    first=committed[0]
    with jobs.connect()as conn:
        row=jobs._locked_job(conn,'tenant-1',first['job_id']);original_input=jobs._verified_input(row)
        events=conn.execute(sql.SQL('SELECT count(*)AS n FROM {} WHERE job_id=%s').format(jobs._table('job_events')),
            (first['job_id'],)).fetchone()['n']
    assert events==1 and row['created_at']==first['created_at']and row['state']=='queued'
    status,retry,_=call(app,POST,method='POST',body=body)
    assert status==202 and retry['job_id']==str(first['job_id'])
    with jobs.connect()as conn:
        again=jobs._locked_job(conn,'tenant-1',first['job_id'])
        assert jobs._verified_input(again)==original_input and again['created_at']==row['created_at']
        assert conn.execute(sql.SQL('SELECT count(*)AS n FROM {} WHERE job_id=%s').format(jobs._table('job_events')),
            (first['job_id'],)).fetchone()['n']==events
    assert jobs.get_publication('tenant-1',first['job_id'])is None
