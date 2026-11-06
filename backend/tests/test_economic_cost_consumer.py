"""Owned cost discovery/foreground loop; synthetic inputs are not farm evidence."""
from dataclasses import replace
from hashlib import sha256
import json
from threading import Event
import time
from uuid import UUID

import pytest
from psycopg import Connection,sql

from app.deterministic_job_discovery import DiscoveredJob
from app.deterministic_work import DeterministicWorkerLoop,LoopHold
from app.economic_batch_calculation import EconomicBatchAuthority
from app.economic_batch_source_store import EconomicBatchSourceStore
from app.economic_batch_worker import BatchCalculationOutcome
from app.economic_cost_calculation import EconomicCostCalculationService
from app.economic_cost_worker import EconomicCostWorker,CostCalculationOutcome
from app import economic_cost_trace as trace
from app.economic_production_batches import ProductionBatchLedger
from login_database import login_database,login_scope
from test_economic_batch_calculation import PROFILE,assembly,request
from test_economic_batch_consumer import run_one
from test_economic_batch_worker import row,publication_count
from test_economic_cost_worker import setup

VERSION='economic-cost-line-calculation-input-v1'
pytestmark=pytest.mark.parametrize('login_scope',[PROFILE],indirect=True)


def test_actual_cost_worker_accepts_its_exact_discovery_and_outcome_family(login_scope):
    jobs,source,holds,contexts,p,s,authority,service,base,job,worker=setup(login_scope)
    loop=DeterministicWorkerLoop(worker,input_versions=frozenset({VERSION}))
    assert loop.discovery.input_versions==frozenset({VERSION})
    assert loop.discovery.page().jobs==(DiscoveredJob(str(job['job_id']),VERSION),)
    outcome=CostCalculationOutcome(UUID(str(job['job_id'])),1,'hold','economic_cost_input_hold')
    assert loop._event(outcome,DiscoveredJob(str(job['job_id']),VERSION))=={
        'version':1,'event':'attempt','job_id':str(job['job_id']),
        'attempt':1,'state':'hold','reason_code':'economic_cost_input_hold'}


@pytest.mark.parametrize('version',['economic-calculation-input-v1','economic-batch-calculation-input-v1',
    'economic-cost-line-calculation-input-v2'])
def test_other_families_cannot_configure_cost_consumer(login_scope,version):
    *_,worker=setup(login_scope)
    with pytest.raises(LoopHold):DeterministicWorkerLoop(worker,input_versions=frozenset({version}))


def test_cost_worker_subclass_is_not_an_accepted_exact_consumer_type(login_scope):
    jobs,source,holds,contexts,p,s,authority,service,base,job,worker=setup(login_scope)
    class UnregisteredCostWorker(EconomicCostWorker):
        pass
    with pytest.raises(LoopHold):
        DeterministicWorkerLoop(UnregisteredCostWorker(authority,tenant_id='tenant-1'),input_versions=frozenset({VERSION}))


def test_original_batch_outcome_and_unclosed_cost_outcome_cannot_emit_cost_events(login_scope):
    jobs,source,holds,contexts,p,s,authority,service,base,job,worker=setup(login_scope)
    loop=DeterministicWorkerLoop(worker,input_versions=frozenset({VERSION}))
    selected=DiscoveredJob(str(job['job_id']),VERSION)
    valid=CostCalculationOutcome(UUID(str(job['job_id'])),1,'succeeded','completed','a'*64)
    for outcome in (BatchCalculationOutcome(valid.job_id,1,'succeeded','completed','a'*64),
            replace(valid,state='unclosed',reason_code='economic_cost_lease_lost')):
        with pytest.raises(LoopHold):loop._event(outcome,selected)
    assert 'trace_id'not in loop._event(valid,selected)


def test_actual_cost_keyset_discovery_skips_other_family_tenant_live_and_future_jobs(login_scope,monkeypatch):
    jobs,source,holds,contexts,p,s,authority,base=assembly(login_scope)
    unrelated=[jobs.submit('tenant-1','simulation',{'input_version':version},'cost-discovery-other-'+str(i))
        for i,version in enumerate(['economic-calculation-input-v1','economic-batch-calculation-input-v2',
            'economic-cost-line-calculation-input-v2','unrelated-v1','unrelated-v2'])]
    unrelated.append(base.submit('tenant-1',request(s,'cost-discovery-old-batch')))
    p['tenant_id']='foreign'
    try:foreign=jobs.submit('foreign','simulation',{'input_version':VERSION},'foreign-cost-discovery')
    finally:p['tenant_id']='tenant-1'
    service=EconomicCostCalculationService(authority)
    future=service.submit('tenant-1',request(s,'future-cost-discovery'))
    live=service.submit('tenant-1',request(s,'live-cost-discovery'))
    lease=jobs.claim(300,allowed_stages=('simulation',),tenant_id='tenant-1',job_id=str(live['job_id']))
    with jobs.connect()as conn:
        conn.execute(sql.SQL("UPDATE {} SET next_attempt_at=clock_timestamp()+interval '1 hour' WHERE job_id=%s").format(
            jobs._table('jobs')),(future['job_id'],))
    selected=service.submit('tenant-1',request(s,'due-cost-discovery'))
    loop=DeterministicWorkerLoop(EconomicCostWorker(authority,tenant_id='tenant-1'),input_versions=frozenset({VERSION}),page_size=2)
    writes=[];execute=Connection.execute
    def measured(conn,*a,**k):
        cursor=execute(conn,*a,**k)
        if(cursor.statusmessage or '').split(' ')[0]in {'INSERT','UPDATE','DELETE','MERGE','CREATE','ALTER','DROP','TRUNCATE','GRANT','REVOKE'}:
            writes.append(cursor.statusmessage)
        return cursor
    monkeypatch.setattr(Connection,'execute',measured)
    cursor=None;found=[];pages=[]
    for _ in range(20):
        page=loop.discovery.page(cursor=cursor,limit=2);pages.append(page)
        assert page.scanned_count<=2
        found.extend(page.jobs)
        if page.next_cursor is None:break
        cursor=page.next_cursor
    else:pytest.fail('bounded cost discovery did not finish')
    assert found==[DiscoveredJob(str(selected['job_id']),VERSION)]and len(pages)>1 and not writes
    for other in unrelated:assert jobs.get_job('tenant-1',other['job_id'])==other
    assert row(jobs,live)['lease_token']==lease['lease_token']and row(jobs,live)['attempt_count']==1
    assert row(jobs,future)['state']=='queued'and row(jobs,future)['attempt_count']==0
    with jobs.connect()as conn:
        value=jobs._locked_job(conn,'foreign',foreign['job_id'])
        assert value['state']=='queued'and value['attempt_count']==0
    assert publication_count(jobs)==0


@pytest.mark.parametrize('scope',['metadata','simulation_execute','artifact','economic_batch_source_read',
    'decision_context_read','market_hold_context_read'])
def test_cost_scope_revoked_after_real_discovery_prevents_claim(login_scope,monkeypatch,scope):
    jobs,source,holds,contexts,p,s,authority,service,base,job,worker=setup(login_scope)
    loop=DeterministicWorkerLoop(worker,input_versions=frozenset({VERSION}));page=loop.discovery.page
    def revoke(**kwargs):value=page(**kwargs);p['scopes'].remove(scope);return value
    monkeypatch.setattr(loop.discovery,'page',revoke)
    with pytest.raises(LoopHold):loop.run(Event(),emit=lambda _:pytest.fail('revoked cost scope emitted'))
    p['scopes'].add(scope)
    assert row(jobs,job)['state']=='queued'and row(jobs,job)['attempt_count']==0 and publication_count(jobs)==0


@pytest.mark.parametrize('part',['source','root','provider'])
def test_cost_binding_change_after_real_discovery_prevents_claim(login_scope,monkeypatch,tmp_path,part):
    jobs,source,holds,contexts,p,s,authority,service,base,job,worker=setup(login_scope)
    loop=DeterministicWorkerLoop(worker,input_versions=frozenset({VERSION}));page=loop.discovery.page
    def changed(**kwargs):
        value=page(**kwargs)
        if part=='root':jobs.artifact_root=tmp_path/'changed-cost-consumer-root'
        elif part=='provider':jobs.principal_provider=lambda:p
        else:authority._source=EconomicBatchSourceStore(source.dsn,source.schema,
            principal_provider=jobs.principal_provider,runtime_identity=jobs.runtime_identity)
        return value
    monkeypatch.setattr(loop.discovery,'page',changed)
    with pytest.raises(LoopHold):loop.run(Event(),emit=lambda _:pytest.fail('changed cost binding emitted'))
    assert row(jobs,job)['state']=='queued'and row(jobs,job)['attempt_count']==0 and publication_count(jobs)==0


def test_actual_cost_loop_cancel_after_trace_never_publishes(login_scope,monkeypatch):
    jobs,source,holds,contexts,p,s,authority,service,base,job,worker=setup(login_scope)
    calculate=trace.CostLineLedger.calculate;calls=[]
    def canceled(*a,**k):
        calls.append(1);value=calculate(*a,**k);assert jobs.cancel('tenant-1',job['job_id']);return value
    monkeypatch.setattr(trace.CostLineLedger,'calculate',canceled)
    events=run_one(DeterministicWorkerLoop(worker,input_versions=frozenset({VERSION})))
    assert len(events)==1 and events[0]['state']=='canceled'and events[0]['reason_code']=='canceled_by_request'
    assert calls==[1]and row(jobs,job)['state']=='canceled'and publication_count(jobs)==0


def test_actual_expired_cost_lease_is_reclaimed_once_and_stale_token_is_rejected(login_scope):
    jobs,source,holds,contexts,p,s,authority,service,base,job,worker=setup(login_scope)
    old=jobs.claim(1,allowed_stages=('simulation',),tenant_id='tenant-1',job_id=str(job['job_id']))
    deadline=time.monotonic()+5
    while row(jobs,job)['lease_live']:
        assert time.monotonic()<deadline;time.sleep(.02)
    loop=DeterministicWorkerLoop(worker,input_versions=frozenset({VERSION}));events=run_one(loop)
    assert len(events)==1 and events[0]['state']=='succeeded'and events[0]['attempt']==2
    assert publication_count(jobs)==1 and not loop.discovery.page().jobs
    assert jobs.fail('tenant-1',job['job_id'],old['attempt'],old['lease_token'],'hold','old_token')is False


def test_current_cost_evidence_hold_emits_no_amount_result_or_publication(login_scope,monkeypatch):
    jobs,source,holds,contexts,p,s,authority,service,base,job,worker=setup(login_scope)
    resolver=holds._scope_resolver
    holds._scope_resolver=lambda *args:resolver(*args)|{'sales_end_utc':'2026-11-30T00:00:00Z'}
    current=EconomicBatchAuthority(jobs,source,holds)
    worker=EconomicCostWorker(current,tenant_id='tenant-1')
    monkeypatch.setattr(trace.CostLineLedger,'calculate',lambda *_:pytest.fail('arithmetic after current cost evidence hold'))
    events=run_one(DeterministicWorkerLoop(worker,input_versions=frozenset({VERSION})))
    assert len(events)==1 and events[0]['state']=='hold'and events[0]['reason_code']=='economic_cost_input_hold'
    assert publication_count(jobs)==0 and jobs.read_artifact('tenant-1',job['job_id'])is None


def test_actual_cost_loop_calculates_once_and_preserves_first_publication_after_retry(login_scope,monkeypatch,tmp_path):
    jobs,source,holds,contexts,p,s,authority,service,base,job,worker=setup(login_scope)
    calculate=trace.CostLineLedger.calculate;calculate_base=ProductionBatchLedger.calculate;calls=[]
    def counted(*a,**k):calls.append('trace');return calculate(*a,**k)
    def counted_base(*a,**k):calls.append('v10');return calculate_base(*a,**k)
    monkeypatch.setattr(trace.CostLineLedger,'calculate',counted)
    monkeypatch.setattr(ProductionBatchLedger,'calculate',counted_base)
    loop=DeterministicWorkerLoop(worker,input_versions=frozenset({VERSION}));events=run_one(loop)
    assert calls==['trace','v10']and events==[{'version':1,'event':'attempt','job_id':str(job['job_id']),
        'attempt':1,'state':'succeeded','reason_code':'completed'}]
    raw=jobs.read_artifact('tenant-1',job['job_id']);publication=jobs.get_publication('tenant-1',job['job_id'])
    first=publication.copy();retry=service.submit('tenant-1',request(s))
    assert retry['job_id']==job['job_id']and retry['created_at']==job['created_at']
    assert not loop.discovery.page().jobs and worker.run_once(str(job['job_id']))is None
    assert calls==['trace','v10']and publication_count(jobs)==1
    assert jobs.get_publication('tenant-1',job['job_id'])==first and jobs.read_artifact('tenant-1',job['job_id'])==raw
    proof={'artifact_sha256':sha256(raw).hexdigest(),'artifact_bytes':len(raw),
        'publication_id':str(publication['publication_id']),'published_at':publication['published_at'].isoformat(),
        'trace_id':json.loads(raw)['result']['trace_id'],'actual_trace_calls':calls.count('trace'),
        'actual_v10_calls':calls.count('v10'),'events':events,'completed_reselected':False,
        'same_first_publication_after_retry':True,'G0_G4':'not_assessed','R2':'not_approved'}
    (tmp_path/'cost-consumer-result-v1.json').write_bytes(raw)
    (tmp_path/'cost-consumer-receipt-v1.private.json').write_text(json.dumps(proof,indent=2)+'\n')
