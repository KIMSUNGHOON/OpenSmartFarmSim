"""Real owned SCRAM admission; no amount calculation or worker execution."""
from copy import copy
from concurrent.futures import ThreadPoolExecutor

import pytest
from psycopg import Connection

from app import economic_cost_trace as trace
from app.economic_cost_calculation import (EconomicCostCalculationInput,
    EconomicCostCalculationService,CostCalculationHold)
from app.economic_production_batches import ProductionBatchLedger
from app.economics import EconomicLedger
from app.job_store import JobIntentConflict
from app.jobs import canonical_input_bytes
from login_database import login_database,login_scope
from test_economic_batch_calculation import PROFILE,assembly,counts,request


def cost_assembly(scope):
    jobs,source,holds,contexts,p,s,authority,base=assembly(scope)
    return jobs,source,holds,contexts,p,s,authority,EconomicCostCalculationService(authority),base


def forbid_calculation(monkeypatch):
    def fail(*a,**k):raise AssertionError('amount calculation during admission')
    for cls,name in [(trace.CostLineLedger,'calculate'),(ProductionBatchLedger,'calculate'),
            (EconomicLedger,'calculate'),(EconomicLedger,'_calculate_verified')]:
        monkeypatch.setattr(cls,name,fail)


def test_contract_rejects_client_program_fields_and_nonactual_authority():
    from test_economic_production_batches import scenario
    body=request(scenario()).model_dump(mode='json')
    for key in ['tenant_id','trace_version','code_sha256','component_sha256','base_input','amount']:
        with pytest.raises(ValueError):type(request(scenario())).model_validate({**body,key:'user-choice'})
    with pytest.raises(ValueError):EconomicCostCalculationService(object())
    with pytest.raises(ValueError):EconomicCostCalculationInput.model_validate({'input_version':'old'})


@pytest.mark.parametrize('login_scope',[PROFILE],indirect=True)
def test_real_retry_preserves_first_bytes_time_and_distinct_old_intent(login_scope,monkeypatch):
    jobs,source,holds,contexts,p,s,authority,service,base=cost_assembly(login_scope)
    forbid_calculation(monkeypatch);before=counts(jobs);writes=[];execute=Connection.execute
    def measure(conn,query,*a,**k):
        cursor=execute(conn,query,*a,**k);tag=(cursor.statusmessage or '').split(' ')[0]
        if tag in {'INSERT','UPDATE','DELETE','MERGE','CREATE','ALTER','DROP','TRUNCATE','GRANT','REVOKE'}:
            statement=query if type(query)is str else query.as_string(conn)
            writes.append((tag,'job_events'if '."job_events"'in statement else'jobs'if '."jobs"'in statement else'other'))
        return cursor
    monkeypatch.setattr(Connection,'execute',measure)
    body=request(s);first=service.submit('tenant-1',body)
    assert service.submit('tenant-1',body)==first
    assert first['state']=='queued'and first['stage']=='simulation'
    assert counts(jobs)==(before[0]+1,before[1]+1,before[2])
    with jobs.connect()as conn:raw=jobs._verified_input(jobs._locked_job(conn,'tenant-1',first['job_id']))
    value=EconomicCostCalculationInput.model_validate_json(raw)
    assert canonical_input_bytes(value.model_dump(mode='json'))==raw
    assert value.base_input==base._prepare('tenant-1',body)
    assert value.input_version=='economic-cost-line-calculation-input-v1'
    assert(value.trace_version,value.code_sha256)==(trace.TRACE_VERSION,trace.CODE_SHA256)
    assert value.component_sha256==trace.COMPONENT_SHA256
    assert value.base_input.scenario_source_job_id==source.get_economic_scenario_pin(s.scenario_id,s.scenario_revision)['immutable_job_input_ref']
    assert jobs.get_publication('tenant-1',first['job_id'])is None
    old=base.submit('tenant-1',body);assert old['job_id']!=first['job_id']and old['state']=='queued'
    assert jobs.get_job('tenant-1',first['job_id'])==first
    assert writes and set(writes)<={('INSERT','jobs'),('INSERT','job_events')}
    assert jobs.get_publication('tenant-1',old['job_id'])is None


@pytest.mark.parametrize('login_scope',[PROFILE],indirect=True)
def test_reference_preparation_is_read_only_without_execute_and_returns_copies(login_scope,monkeypatch):
    jobs,source,holds,contexts,p,s,authority,service,base=cost_assembly(login_scope)
    forbid_calculation(monkeypatch);before=counts(jobs);p['scopes'].remove('simulation_execute')
    value=service._prepare('tenant-1',request(s));assert value.base_input==base._prepare('tenant-1',request(s))
    value.component_sha256.clear()
    assert service._prepare('tenant-1',request(s)).component_sha256==trace.COMPONENT_SHA256
    with pytest.raises(PermissionError):service.submit('tenant-1',request(s))
    assert counts(jobs)==before


@pytest.mark.parametrize('login_scope',[PROFILE],indirect=True)
def test_concurrent_retry_and_different_revision_conflict_preserve_rows(login_scope):
    jobs,source,holds,contexts,p,s,authority,service,base=cost_assembly(login_scope);before=counts(jobs)
    with ThreadPoolExecutor(max_workers=2)as pool:
        rows=list(pool.map(lambda _:service.submit('tenant-1',request(s)),range(2)))
    assert rows[0]==rows[1]and counts(jobs)==(before[0]+1,before[1]+1,before[2])
    other=s.model_copy(update={'scenario_revision':'r2'})
    job=jobs.submit('tenant-1','collection',other.model_dump(mode='json'),'second-revision')
    source.adopt_job('tenant-1','economic_scenario',str(job['job_id']));before=counts(jobs)
    with pytest.raises(JobIntentConflict):service.submit('tenant-1',request(other))
    assert counts(jobs)==before


@pytest.mark.parametrize('login_scope',[PROFILE],indirect=True)
@pytest.mark.parametrize('bad',['sha','missing','tenant'])
def test_wrong_references_and_tenant_create_no_intent(login_scope,bad):
    jobs,source,holds,contexts,p,s,authority,service,base=cost_assembly(login_scope);before=counts(jobs)
    body=request(s);tenant='tenant-1'
    if bad=='sha':body=body.model_copy(update={'scenario_sha256':'f'*64})
    elif bad=='missing':body=body.model_copy(update={'scenario_id':'missing'})
    else:tenant='foreign'
    with pytest.raises(PermissionError if bad=='tenant'else CostCalculationHold):service.submit(tenant,body)
    assert counts(jobs)==before


@pytest.mark.parametrize('login_scope',[PROFILE],indirect=True)
@pytest.mark.parametrize('scope',['metadata','economic_batch_source_read','decision_context_read','market_hold_context_read','simulation_execute'])
@pytest.mark.parametrize('late',[False,True])
def test_every_current_and_commit_scope_is_required(login_scope,monkeypatch,scope,late):
    jobs,source,holds,contexts,p,s,authority,service,base=cost_assembly(login_scope);before=counts(jobs)
    if late:
        event=jobs._event
        def revoke(*a,**k):event(*a,**k);p['scopes'].remove(scope)
        monkeypatch.setattr(jobs,'_event',revoke)
    else:p['scopes'].remove(scope)
    with pytest.raises(PermissionError):service.submit('tenant-1',request(s))
    assert counts(jobs)==before


@pytest.mark.parametrize('login_scope',[PROFILE],indirect=True)
@pytest.mark.parametrize('part',['service','context','code','program'])
def test_commit_time_binding_or_program_change_rolls_back(login_scope,monkeypatch,part):
    jobs,source,holds,contexts,p,s,authority,service,base=cost_assembly(login_scope);before=counts(jobs);event=jobs._event
    def change(*a,**k):
        event(*a,**k)
        if part=='service':service.authority=copy(authority)
        elif part=='context':holds._context_store=copy(contexts)
        elif part=='code':monkeypatch.setattr(trace,'CODE_SHA256','0'*64)
        else:monkeypatch.setattr(trace,'TRACE_VERSION','unsupported-cost-trace')
    monkeypatch.setattr(jobs,'_event',change)
    with pytest.raises((RuntimeError,CostCalculationHold)):service.submit('tenant-1',request(s))
    assert counts(jobs)==before


@pytest.mark.parametrize('login_scope',[PROFILE],indirect=True)
def test_changed_prepared_evidence_and_event_error_roll_back(login_scope,monkeypatch):
    jobs,source,holds,contexts,p,s,authority,service,base=cost_assembly(login_scope);before=counts(jobs)
    original=service._prepare;calls=[]
    def change(*a):
        value=original(*a);calls.append(True)
        if len(calls)>1:value=value.model_copy(update={'base_input':value.base_input.model_copy(update={'evidence_sha256':'f'*64})})
        return value
    with monkeypatch.context()as patch:
        patch.setattr(service,'_prepare',change)
        with pytest.raises(RuntimeError):service.submit('tenant-1',request(s))
    assert len(calls)==2 and counts(jobs)==before
    def fail(*a,**k):raise RuntimeError('self-authored event failure')
    monkeypatch.setattr(jobs,'_event',fail)
    with pytest.raises(RuntimeError):service.submit('tenant-1',request(s))
    assert counts(jobs)==before


@pytest.mark.parametrize('login_scope',[PROFILE],indirect=True)
def test_unicode_source_and_new_service_keep_original_job_bytes(login_scope):
    jobs,source,holds,contexts,p,s,authority,service,base=cost_assembly(login_scope)
    other=s.model_copy(update={'scenario_id':'자체-방울토마토-항목비용'})
    source_job=jobs.submit('tenant-1','collection',other.model_dump(mode='json'),'unicode-source')
    source.adopt_job('tenant-1','economic_scenario',str(source_job['job_id']))
    first=service.submit('tenant-1',request(other))
    assert EconomicCostCalculationService(authority).submit('tenant-1',request(other))==first
    with jobs.connect()as conn:raw=jobs._verified_input(jobs._locked_job(conn,'tenant-1',first['job_id']))
    value=EconomicCostCalculationInput.model_validate_json(raw)
    assert other.scenario_id.encode()in raw and value.base_input.scenario_source_job_id==str(source_job['job_id'])
