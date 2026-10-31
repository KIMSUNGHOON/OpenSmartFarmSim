"""Real batch discovery/loop and fail-closed dispatch over owned SCRAM."""
from threading import Event
import time
from uuid import UUID

import pytest

from app.deterministic_work import DeterministicWorkerLoop,LoopHold
from app.deterministic_job_discovery import DiscoveredJob
from app.economic_batch_calculation import EconomicBatchAuthority
from app.economic_batch_source_store import EconomicBatchSourceStore
from app.economic_batch_worker import EconomicBatchWorker,BatchCalculationOutcome
from app.economic_production_batches import ProductionBatchLedger
from login_database import login_database,login_scope
from test_economic_batch_calculation import PROFILE
from test_economic_batch_worker import setup,row,publication_count

VERSION='economic-batch-calculation-input-v1'
pytestmark=pytest.mark.parametrize('login_scope',[PROFILE],indirect=True)


def run_one(loop):
    stop=Event();events=[]
    def emit(value):events.append(value);stop.set()
    loop.run(stop,emit=emit)
    return events


def test_actual_batch_loop_is_registered_with_its_exact_input(login_scope):
    *_,worker=setup(login_scope)
    loop=DeterministicWorkerLoop(worker,input_versions=frozenset({VERSION}))
    assert loop.discovery.input_versions==frozenset({VERSION})


@pytest.mark.parametrize('version',['economic-calculation-input-v1','economic-batch-calculation-input-v2'])
def test_other_versions_cannot_configure_batch_worker(login_scope,version):
    *_,worker=setup(login_scope)
    with pytest.raises(LoopHold):DeterministicWorkerLoop(worker,input_versions=frozenset({version}))


@pytest.mark.parametrize('scope',['metadata','simulation_execute','artifact','economic_batch_source_read',
    'decision_context_read','market_hold_context_read'])
def test_scope_revoked_after_real_discovery_prevents_claim(login_scope,monkeypatch,scope):
    jobs,source,holds,contexts,p,s,authority,service,job,worker=setup(login_scope)
    loop=DeterministicWorkerLoop(worker,input_versions=frozenset({VERSION}));page=loop.discovery.page
    def revoke(**kwargs):
        result=page(**kwargs);p['scopes'].remove(scope);return result
    monkeypatch.setattr(loop.discovery,'page',revoke)
    with pytest.raises(LoopHold):loop.run(Event(),emit=lambda _:pytest.fail('revoked scope emitted'))
    p['scopes'].add(scope)
    assert row(jobs,job)['state']=='queued'and row(jobs,job)['attempt_count']==0 and publication_count(jobs)==0


@pytest.mark.parametrize('part',['source','root'])
def test_late_object_or_root_replacement_prevents_claim(login_scope,monkeypatch,tmp_path,part):
    jobs,source,holds,contexts,p,s,authority,service,job,worker=setup(login_scope)
    loop=DeterministicWorkerLoop(worker,input_versions=frozenset({VERSION}));page=loop.discovery.page
    def replace(**kwargs):
        found=page(**kwargs)
        if part=='root':jobs.artifact_root=tmp_path/'different-root'
        else:authority._source=EconomicBatchSourceStore(source.dsn,source.schema,
            principal_provider=jobs.principal_provider,runtime_identity=jobs.runtime_identity)
        return found
    monkeypatch.setattr(loop.discovery,'page',replace)
    with pytest.raises(LoopHold):loop.run(Event(),emit=lambda _:pytest.fail('changed object emitted'))
    assert row(jobs,job)['state']=='queued'and row(jobs,job)['attempt_count']==0 and publication_count(jobs)==0


def test_actual_loop_cancel_after_calculation_never_publishes(login_scope,monkeypatch):
    jobs,source,holds,contexts,p,s,authority,service,job,worker=setup(login_scope)
    actual=ProductionBatchLedger.calculate;calls=[]
    def cancel(*a,**k):
        calls.append(1);result=actual(*a,**k);assert jobs.cancel('tenant-1',job['job_id']);return result
    monkeypatch.setattr(ProductionBatchLedger,'calculate',cancel)
    events=run_one(DeterministicWorkerLoop(worker,input_versions=frozenset({VERSION})))
    assert len(events)==1 and events[0]['state']=='canceled'and calls==[1]
    assert row(jobs,job)['state']=='canceled'and publication_count(jobs)==0


def test_actual_expired_lease_is_discovered_reclaimed_once_and_old_token_rejected(login_scope):
    jobs,source,holds,contexts,p,s,authority,service,job,worker=setup(login_scope)
    old=jobs.claim(1,allowed_stages=('simulation',),tenant_id='tenant-1',job_id=str(job['job_id']))
    deadline=time.monotonic()+5
    while row(jobs,job)['lease_live']:
        assert time.monotonic()<deadline;time.sleep(.02)
    loop=DeterministicWorkerLoop(worker,input_versions=frozenset({VERSION}));events=run_one(loop)
    assert len(events)==1 and events[0]['state']=='succeeded'and events[0]['attempt']==2
    assert publication_count(jobs)==1 and not loop.discovery.page().jobs
    assert jobs.fail('tenant-1',job['job_id'],old['attempt'],old['lease_token'],'hold','old_token')is False


def test_current_authoritative_evidence_hold_emits_hold_without_amount_calculation(login_scope,monkeypatch):
    jobs,source,holds,contexts,p,s,authority,service,job,worker=setup(login_scope)
    original=holds._scope_resolver
    holds._scope_resolver=lambda *args:original(*args)|{'sales_end_utc':'2026-11-30T00:00:00Z'}
    current=EconomicBatchAuthority(jobs,source,holds)
    worker=EconomicBatchWorker(current,tenant_id='tenant-1')
    monkeypatch.setattr(ProductionBatchLedger,'calculate',lambda *_:pytest.fail('arithmetic after evidence hold'))
    events=run_one(DeterministicWorkerLoop(worker,input_versions=frozenset({VERSION})))
    assert len(events)==1 and events[0]['state']=='hold'and events[0]['reason_code']=='economic_batch_input_hold'
    assert publication_count(jobs)==0


def test_unclosed_lease_result_is_not_an_accepted_loop_event(login_scope):
    jobs,source,holds,contexts,p,s,authority,service,job,worker=setup(login_scope)
    loop=DeterministicWorkerLoop(worker,input_versions=frozenset({VERSION}))
    result=BatchCalculationOutcome(UUID(str(job['job_id'])),1,'unclosed','economic_batch_lease_lost')
    with pytest.raises(LoopHold):loop._event(result,DiscoveredJob(str(job['job_id']),VERSION))
