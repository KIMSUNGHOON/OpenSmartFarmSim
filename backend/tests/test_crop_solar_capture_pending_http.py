"""Actual SCRAM/TLS transient capture, permanent denial and scoped access."""
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
import json,os,threading
import pytest
from starlette.concurrency import run_in_threadpool
import test_api_crop_greenhouse_solar_execution_http_native as reference
from test_api_crop_greenhouse_solar_execution_http_native import (
    native,authoring,query_setup,worker_setup,producer_setup,profiles,
    login_database,original_login_scope,login_scope,query_cleanup,tls_files)
custody=reference.reference.model.custody
pytestmark=reference.pytestmark


def test_actual_TLS_capture_change_is_retryable_and_preserves_original_state(native,tls_files,monkeypatch):
    c=native
    _,original,_=reference.running(c,2)
    entered=threading.Event();resume=threading.Event();state=threading.local()
    load=custody._Session._load;current=type(c.worker.server.binding).current
    def loaded(session,*args,**kwargs):
        value=load(session,*args,**kwargs)
        if not session._writable:state.captured=True
        return value
    def validating(binding,*args,**kwargs):
        if getattr(state,'captured',False) and not getattr(state,'blocked',False):
            state.blocked=True;entered.set()
            assert resume.wait(40),'owned actual HTTP current validation not released'
        return current(binding,*args,**kwargs)
    monkeypatch.setattr(custody._Session,'_load',loaded)
    monkeypatch.setattr(type(c.worker.server.binding),'current',validating)
    @c.app.post('/owned-capture-advance',include_in_schema=False)
    async def advance():
        raw=await run_in_threadpool(c.worker.server.advance,'tenant-1',c.raw,budget=1)
        value=json.loads(raw)
        return {'steps':value['steps'],'computed_through_utc':value['times']['last_confirmed']['at']}
    before=reference.reference.persisted_digest(c.worker.jobs)
    with reference.served(c,tls_files) as (http,replies):
        with ThreadPoolExecutor(max_workers=1) as pool:
            future=pool.submit(http,'GET',c.path)
            try:
                assert entered.wait(40),'actual HTTP read did not reach post-capture validation'
                written,body=http('POST','/owned-capture-advance')
                assert written==200
                advanced=json.loads(body);assert advanced['steps']==original['steps']+1
            finally:resume.set()
            status,raw=future.result(timeout=60)
        body=json.loads(raw)
        record={'scope':'one controlled actual SCRAM and verified TLS capture race; not actual CI response',
            'actual_SCRAM':True,'verified_TLS':True,'original_steps':original['steps'],
            'advanced':advanced,'status':status,'code':body.get('error',{}).get('code'),
            'only_error_no_partial_fields':set(body)=={'error'},
            'DB_unchanged':reference.reference.persisted_digest(c.worker.jobs)==before,
            'rights_or_gate_approval':False,'G0_G4':'not_assessed'}
        assert status==503, 'controlled_progress_status_'+str(status)+'_code_'+str(record['code'])
        assert record['code']=='solar_execution_unavailable' and record['only_error_no_partial_fields'] and record['DB_unchanged']
        status,raw=http('GET',c.path)
        assert status==200 and json.loads(raw)['checkpoint_status']=='unavailable'
        assert json.loads(raw)['checkpoint'] is json.loads(raw)['result'] is None
        record['recovered_status']=status
        rights=c.value[5];rights.allowed=False
        try:
            status,raw=http('GET',c.path)
            assert status==422 and json.loads(raw)['error']['code']=='solar_execution_hold'
            record['rights_hold_status']=status
        finally:rights.allowed=True
    with reference.served(c,tls_files,scopes={'metadata'}) as (http,_):
        status,raw=http('GET',c.path)
        assert status==403 and json.loads(raw)['error']['code']=='forbidden'
        record['insufficient_scope_status']=status
    assert reference.reference.persisted_digest(c.worker.jobs)==before
    out=Path(os.environ['OSSF_SOLAR_EXECUTION_HTTP_EVIDENCE'])/'capture-change.json'
    with out.open('x') as f:os.fchmod(f.fileno(),0o400);json.dump(record,f,sort_keys=True);f.flush();os.fsync(f.fileno())
