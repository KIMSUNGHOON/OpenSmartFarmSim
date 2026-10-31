"""Actual optional batch assembly alongside the original source family."""
from contextlib import contextmanager
from dataclasses import replace
from datetime import datetime,timezone,timedelta
from hashlib import sha256
import http.client
import json
import os
import socket
import ssl
import threading
import time

import pytest
from psycopg import Connection,sql

from app.api_runtime import ApiRuntime
from app.economic_batch_calculation import EconomicBatchAuthority
from app.economic_batch_source_store import EconomicBatchSourceStore
from app.economic_batch_worker import EconomicBatchWorker
from app.economic_contracts import iter_economic_numbers,OwnedEconomicRecord
from app.economic_production_batches import ProductionBatchLedger,OwnedProductionBatch
from app.economics import EconomicLedger,canonical_scenario_sha256
from app.http_identity import BearerGrant,BearerRegistry,current_principal,token_digest
from app.market_source_store import MarketSourceStore
from login_database import login_database,login_scope
from test_api_runtime import config,dependencies,policy
from test_api_serve import tls_files
from test_economic_batch_calculation import PROFILE,assembly
from test_economic_production_batches import batch_record

RUNTIME_PROFILE={**PROFILE,'break_even_calculation':True}
TOKEN=b'synthetic-batch-runtime-'+b'r'*32
READ_TOKEN=b'synthetic-batch-read-'+b's'*32


def test_invalid_optional_factory_has_fixed_dependency_error():
    with pytest.raises(ValueError,match='^API runtime dependencies rejected$'):
        dependencies(economic_batch_source_factory=object())


@pytest.mark.parametrize('enabled',[False,True])
def test_flag_factory_mismatch_is_rejected_before_factory_or_private_path_access(enabled,monkeypatch):
    import app.api_runtime as runtime_module
    called=[]
    def factory(**kwargs):called.append(True);raise AssertionError('factory before flag check')
    def forbidden_store(*a,**k):called.append('JobStore');raise AssertionError('store before flag check')
    monkeypatch.setattr(runtime_module,'JobStore',forbidden_store)
    p=replace(policy(),market_source_storage=True,economic_batch_source_storage=enabled)
    deps=dependencies(economic_batch_source_factory=None if enabled else factory)
    with pytest.raises(ValueError,match='^API runtime assembly rejected$'):ApiRuntime(config(policy=p),deps)
    assert not called


@pytest.fixture
def runtime_inputs(login_scope,tls_files):
    values=assembly(login_scope);jobs,source,holds,contexts,p,s,authority,service=values
    os.close(jobs._content_directory(create=True))
    cert,key,_=tls_files
    with socket.socket()as sock:sock.bind(('127.0.0.1',0));port=sock.getsockname()[1]
    cfg=config(policy=jobs.runtime_identity[0],dsn=jobs._dsn,artifact_root=jobs.artifact_root,
        certificate=cert,private_key=key,thermal_gate_key=contexts._gate_key,market_hold_key=holds._key,port=port)
    from app.api_economic_batch import SOURCE_WRITE,CALCULATE_SCOPES,RESULT_SCOPES
    scopes=set(SOURCE_WRITE+CALCULATE_SCOPES+RESULT_SCOPES)|{'market_source_read','market_source_write'}
    now=datetime.now(timezone.utc)
    registry=BearerRegistry(tuple(BearerGrant(token_digest(t),'tenant-1',frozenset(v),
        now-timedelta(seconds=1),now+timedelta(minutes=5))for t,v in [(TOKEN,scopes),(READ_TOKEN,set(RESULT_SCOPES))]))
    def legacy_factory(*,principal_provider):
        return MarketSourceStore(jobs._dsn,jobs.schema,principal_provider=principal_provider,runtime_identity=jobs.runtime_identity)
    def batch_factory(*,principal_provider):
        return EconomicBatchSourceStore(jobs._dsn,jobs.schema,principal_provider=principal_provider,runtime_identity=jobs.runtime_identity)
    scope={'changed':False}
    def resolver(*args):
        original=holds._scope_resolver(*args)
        return original|{'sales_end_utc':'2026-11-30T00:00:00Z'}if scope['changed']else original
    deps=dependencies(market_source_factory=legacy_factory,economic_batch_source_factory=batch_factory,
        market_scope_resolver=resolver,context_verifier=contexts._context_verifier,bearer_registry=registry)
    return values,cfg,deps,scope


@pytest.mark.parametrize('login_scope',[RUNTIME_PROFILE],indirect=True)
@pytest.mark.parametrize('fault',['object','legacy','provider','dsn','schema','profile','old_factory'])
def test_wrong_source_factories_are_rejected_without_installing_runtime(runtime_inputs,fault):
    values,cfg,deps,scope=runtime_inputs;jobs,source,holds,contexts,p,s,authority,service=values
    def factory(*,principal_provider):
        if fault=='object':return object()
        cls=MarketSourceStore if fault=='legacy'else EconomicBatchSourceStore
        return cls(jobs._dsn+' application_name=other'if fault=='dsn'else jobs._dsn,
            'different_schema'if fault=='schema'else jobs.schema,
            principal_provider=(lambda:None)if fault=='provider'else principal_provider,
            runtime_identity=(replace(jobs.runtime_identity[0],economic_batch_source_storage=False),'authority')
                if fault=='profile'else jobs.runtime_identity)
    broken=replace(deps,**{'market_source_factory'if fault=='old_factory'else 'economic_batch_source_factory':factory})
    with pytest.raises(ValueError,match='^API runtime assembly rejected$'):ApiRuntime(cfg,broken)


@pytest.mark.parametrize('login_scope',[RUNTIME_PROFILE],indirect=True)
def test_late_source_provider_change_is_rejected_before_HTTP_service(runtime_inputs,monkeypatch):
    import app.api as api
    values,cfg,deps,scope=runtime_inputs;actual=api.create_app
    def changed(*args,**kwargs):
        authority=kwargs['economic_batch_authority'];authority._source._principal_provider=lambda:None
        return actual(*args,**kwargs)
    monkeypatch.setattr(api,'create_app',changed)
    with pytest.raises(ValueError,match='^API runtime assembly rejected$'):ApiRuntime(cfg,deps)


@contextmanager
def https(runtime,cfg):
    # Each assembly owns a bounded ephemeral listener; the certificate is verified by the client.
    port=cfg.port;server=runtime.service.server()
    thread=threading.Thread(target=server.run,daemon=True);thread.start()
    context=ssl.create_default_context(cafile=str(cfg.certificate))
    def call(path,*,method='GET',body=None,token=TOKEN):
        conn=http.client.HTTPSConnection('127.0.0.1',port,context=context,timeout=10)
        try:
            headers={'Content-Type':'application/json','X-Tenant-ID':'foreign'}
            if token is not None:headers['Authorization']='Bearer '+token.decode()
            conn.request(method,path,body=json.dumps(body)if body is not None else None,headers=headers)
            response=conn.getresponse();return response.status,response.read(),dict(response.getheaders())
        finally:conn.close()
    try:
        end=time.monotonic()+10
        while not server.started:
            assert thread.is_alive()and time.monotonic()<end
            time.sleep(.01)
        yield call
    finally:server.should_exit=True;thread.join(timeout=10)
    assert not thread.is_alive()


@pytest.mark.parametrize('login_scope',[RUNTIME_PROFILE],indirect=True)
def test_actual_runtime_HTTPS_preserves_both_source_families_and_fresh_original_result(runtime_inputs,monkeypatch,tmp_path):
    values,cfg,deps,scope=runtime_inputs;jobs,source,holds,contexts,p,s,authority,service=values
    first=ApiRuntime(cfg,deps)
    assert type(first.economic_batch_authority)is EconomicBatchAuthority
    assert first.economic_batch_authority.jobs is first.jobs
    assert first.economic_batch_authority._holds is first.market_holds
    assert first.market_holds._context_store is first.thermal
    with https(first,cfg)as call:
        body={'kind':'production_batch','input':OwnedProductionBatch.model_validate(batch_record(s)).model_dump(
            mode='json',exclude={'tenant_id'}),'idempotency_key':'runtime-batch'}
        status,raw,_=call('/v1/economic-batch-sources',method='POST',body=body)
        assert status==200;record=json.loads(raw)
        assert call('/v1/economic-batch-sources',method='POST',body=body)[1]==raw
        n=next(iter(iter_economic_numbers(s)));number=source.get_economic_input(n.input_id,n.revision)
        legacy={'kind':'economic_input','input':OwnedEconomicRecord.model_validate(number).model_dump(
            mode='json',exclude={'tenant_id'}),'idempotency_key':'runtime-legacy'}
        assert call('/v1/market-user-sources',method='POST',body=legacy)[0]==200
        with jobs.connect()as conn:
            assert conn.execute(sql.SQL('SELECT count(*)AS n FROM {}').format(jobs._table('market_source_records'))).fetchone()['n']==1
        calc={'scenario_id':s.scenario_id,'scenario_revision':s.scenario_revision,
            'scenario_sha256':canonical_scenario_sha256(s),'idempotency_key':'runtime-calc'}
        status,raw,_=call('/v1/economic-batch-calculations',method='POST',body=calc)
        assert status==202;job=json.loads(raw);path='/v1/jobs/'+job['job_id']+'/economic-batch-result'
        assert call(path)[0]==404
        assert EconomicBatchWorker(authority,tenant_id='tenant-1').run_once(job['job_id']).state=='succeeded'
    expected=jobs.read_artifact('tenant-1',job['job_id']);publication=jobs.get_publication('tenant-1',job['job_id'])
    fresh=ApiRuntime(cfg,deps)
    assert fresh.jobs is not first.jobs and fresh.economic_batch_authority is not first.economic_batch_authority
    writes=[];execute=Connection.execute
    def measured(conn,*a,**k):
        cursor=execute(conn,*a,**k)
        if(cursor.statusmessage or '').split(' ')[0]in {'INSERT','UPDATE','DELETE','MERGE','CREATE','ALTER','DROP','TRUNCATE','GRANT','REVOKE'}:writes.append(cursor.statusmessage)
        return cursor
    def fail(*a,**k):raise AssertionError('calculation during fresh runtime read')
    monkeypatch.setattr(Connection,'execute',measured)
    monkeypatch.setattr(ProductionBatchLedger,'calculate',fail)
    monkeypatch.setattr(EconomicLedger,'_calculate_verified',fail)
    with https(fresh,cfg)as call:
        status,raw,headers=call(path,token=READ_TOKEN)
        assert status==200 and raw==expected and not writes
        assert headers['x-ossf-publication-id']==str(publication['publication_id'])
        assert headers['x-ossf-published-at']==publication['published_at'].isoformat()
        assert call(path,token=None)[0]==401
        scope['changed']=True
        assert call(path,token=READ_TOKEN)[0]==422
        scope['changed']=False
        assert call(path,token=READ_TOKEN)[1]==expected
        assert not writes and current_principal()is None
    proof={'artifact_sha256':sha256(expected).hexdigest(),'artifact_bytes':len(expected),
        'publication_id':str(publication['publication_id']),'published_at':publication['published_at'].isoformat(),
        'fresh_runtime_objects':2,'verified_TLS_listeners':2,'original_source_family_preserved':True,
        'SQL_writes_on_fresh_result':0,'amount_calls_on_fresh_result':0,'current_evidence_hold_and_restore':True,
        'automatic_consumer':False,'G0_G4':'not_assessed','R2':'not_approved'}
    (tmp_path/'runtime-result-receipt.private.json').write_text(json.dumps(proof,indent=2))
