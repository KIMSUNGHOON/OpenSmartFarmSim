"""Owned real leases and publications; self-authored money is not farm evidence."""
from decimal import Decimal,localcontext
from datetime import datetime,timezone
from hashlib import sha256
import json

import pytest
from psycopg import sql

from app.economic_batch_worker import EconomicBatchWorker,ARTIFACT_VERSION
from app.economic_production_batches import ProductionBatchLedger
from login_database import login_database,login_scope
from test_economic_batch_calculation import PROFILE,assembly,request


def setup(scope):
    jobs,source,holds,contexts,p,s,authority,service=assembly(scope)
    p['scopes'].add('cancel')
    job=service.submit('tenant-1',request(s))
    worker=EconomicBatchWorker(authority,tenant_id='tenant-1')
    return jobs,source,holds,contexts,p,s,authority,service,job,worker


def publication_count(jobs):
    with jobs.connect()as conn:
        return conn.execute(sql.SQL('SELECT count(*) AS n FROM {}').format(
            jobs._table('job_publications'))).fetchone()['n']


def row(jobs,job):
    with jobs.connect()as conn:return jobs._locked_job(conn,'tenant-1',job['job_id'])


@pytest.mark.parametrize('login_scope',[PROFILE],indirect=True)
def test_actual_lease_calculates_once_and_stores_full_original_result(login_scope,monkeypatch,tmp_path):
    jobs,source,holds,contexts,p,s,authority,service,job,worker=setup(login_scope)
    calls=[];calculate=ProductionBatchLedger.calculate
    def counted(*a,**k):calls.append(1);return calculate(*a,**k)
    monkeypatch.setattr(ProductionBatchLedger,'calculate',counted)
    before=s.model_dump();outcome=worker.run_once(str(job['job_id']))
    assert outcome.state=='succeeded'and outcome.reason_code=='completed'and outcome.attempt==1
    assert len(calls)==1 and s.model_dump()==before and not s.harvests and not s.sales
    stored=row(jobs,job);assert stored['state']=='succeeded'and stored['lease_token']is None
    assert publication_count(jobs)==1
    raw=jobs.read_artifact('tenant-1',job['job_id']);artifact=json.loads(raw)
    canonical=json.dumps(artifact,sort_keys=True,separators=(',',':'),allow_nan=False).encode()
    assert raw==canonical and artifact['artifact_version']==ARTIFACT_VERSION
    assert artifact['job_id']==str(job['job_id'])and artifact['tenant_id']=='tenant-1'
    assert artifact['input_sha256']==job['input_sha256']and artifact['input']['scenario_sha256']==request(s).scenario_sha256
    result=artifact['result'];ledger=result['ledger']
    with localcontext()as ctx:
        ctx.prec=300
        cost=s.variable_costs[0];expected=Decimal(cost.quantity.value)*Decimal(cost.unit_cost.value)
    assert Decimal(ledger['variable_cost'])==expected==20
    assert Decimal(ledger['operating_cash'])==-expected
    assert ledger['formula_version']=='economic-ledger-v10-declared-production-batches'
    assert ledger['assessment_status']=='hold'and result['G0_G4']=='not_assessed'and result['R2']=='not_approved'
    result_raw=json.dumps(result,sort_keys=True,separators=(',',':'),allow_nan=False).encode()
    assert sha256(result_raw).hexdigest()==artifact['result_sha256']
    publication=jobs.get_publication('tenant-1',job['job_id'])
    assert publication['artifact_sha256']==sha256(raw).hexdigest()and publication['artifact_size']==len(raw)
    assert publication['manifest']=={'schema_version':'1','job_id':str(job['job_id']),
        'stage':'simulation','input_sha256':job['input_sha256'],'attempt':1,'artifact_sha256':sha256(raw).hexdigest()}
    first=publication.copy()
    assert worker.run_once(str(job['job_id']))is None and len(calls)==1
    assert jobs.get_publication('tenant-1',job['job_id'])==first and jobs.read_artifact('tenant-1',job['job_id'])==raw
    (tmp_path/'published-result-v1.json').write_bytes(raw)
    proof={'observed_at_UTC':datetime.now(timezone.utc).isoformat(),'job_id':str(job['job_id']),
        'source_job_id':artifact['input']['scenario_source_job_id'],'input_sha256':job['input_sha256'],
        'artifact_sha256':publication['artifact_sha256'],'artifact_size':len(raw),
        'result_sha256':artifact['result_sha256'],'code_sha256':artifact['code_sha256'],
        'environment_sha256':artifact['environment_sha256'],'manifest':publication['manifest'],
        'job_created_at':job['created_at'].isoformat(),'published_at':publication['published_at'].isoformat(),
        'actual_numeric_calculations':len(calls),'independent_Decimal_precision':300,
        'expected_variable_cost_KRW':str(expected),'actual_variable_cost_KRW':ledger['variable_cost'],
        'actual_operating_cash_KRW':ledger['operating_cash'],'same_result_after_retry':True,
        'scope':'self_authored_QA_only','G0_G4':'not_assessed','R2':'not_approved'}
    (tmp_path/'published-receipt-v1.json').write_text(json.dumps(proof,indent=2)+'\n')
    for name in ['published-result-v1.json','published-receipt-v1.json']:(tmp_path/name).chmod(0o600)


@pytest.mark.parametrize('login_scope',[PROFILE],indirect=True)
def test_other_input_family_and_initial_missing_scope_are_not_claimed(login_scope):
    jobs,source,holds,contexts,p,s,authority,service,job,worker=setup(login_scope)
    other=jobs.submit('tenant-1','simulation',{'input_version':'economic-calculation-input-v1'},'other-family')
    assert worker.run_once(str(other['job_id']))is None
    assert row(jobs,other)['state']=='queued'and row(jobs,other)['attempt_count']==0
    p['scopes'].remove('artifact')
    with pytest.raises(PermissionError):worker.run_once(str(job['job_id']))
    assert row(jobs,job)['state']=='queued'and publication_count(jobs)==0


@pytest.mark.parametrize('login_scope',[PROFILE],indirect=True)
def test_wrong_registered_evidence_is_held_before_arithmetic(login_scope,monkeypatch):
    jobs,source,holds,contexts,p,s,authority,service,job,worker=setup(login_scope)
    value=json.loads(jobs._verified_input(row(jobs,job)));value['evidence_sha256']='e'*64
    bad=jobs.submit('tenant-1','simulation',value,'incorrect-evidence')
    def fail(*a,**k):raise AssertionError('arithmetic before evidence match')
    monkeypatch.setattr(ProductionBatchLedger,'calculate',fail)
    outcome=worker.run_once(str(bad['job_id']))
    assert outcome.state=='hold'and publication_count(jobs)==0
    assert row(jobs,bad)['state']=='hold'and row(jobs,job)['state']=='queued'


@pytest.mark.parametrize('login_scope',[PROFILE],indirect=True)
def test_cancel_after_calculation_prevents_publication(login_scope,monkeypatch):
    jobs,source,holds,contexts,p,s,authority,service,job,worker=setup(login_scope)
    calculate=ProductionBatchLedger.calculate
    def cancel(*a,**k):
        result=calculate(*a,**k);assert jobs.cancel('tenant-1',job['job_id']);return result
    monkeypatch.setattr(ProductionBatchLedger,'calculate',cancel)
    outcome=worker.run_once(str(job['job_id']))
    assert outcome.state=='canceled'and row(jobs,job)['state']=='canceled'
    assert publication_count(jobs)==0 and jobs.read_artifact('tenant-1',job['job_id'])is None


@pytest.mark.parametrize('login_scope',[PROFILE],indirect=True)
def test_real_lease_expiry_after_calculation_prevents_publication(login_scope,monkeypatch):
    jobs,source,holds,contexts,p,s,authority,service,job,worker=setup(login_scope)
    calculate=ProductionBatchLedger.calculate
    def expire(*a,**k):
        result=calculate(*a,**k)
        with jobs.connect()as conn:
            conn.execute(sql.SQL("UPDATE {} SET lease_until=clock_timestamp()-interval '1 second' WHERE job_id=%s").format(jobs._table('jobs')),(job['job_id'],))
        return result
    monkeypatch.setattr(ProductionBatchLedger,'calculate',expire)
    outcome=worker.run_once(str(job['job_id']))
    assert outcome.state=='unclosed'and outcome.reason_code=='economic_batch_lease_lost'
    assert publication_count(jobs)==0 and row(jobs,job)['lease_live']is False


@pytest.mark.parametrize('login_scope',[PROFILE],indirect=True)
def test_scope_revoke_after_success_event_rolls_back_terminal_and_publication(login_scope,monkeypatch):
    jobs,source,holds,contexts,p,s,authority,service,job,worker=setup(login_scope)
    event=jobs._event
    def revoke(conn,tenant,job_id,kind,*a,**k):
        event(conn,tenant,job_id,kind,*a,**k)
        if kind=='succeeded':p['scopes'].remove('simulation_execute')
    monkeypatch.setattr(jobs,'_event',revoke)
    outcome=worker.run_once(str(job['job_id']))
    assert outcome.state=='hold'and row(jobs,job)['state']=='hold'
    assert publication_count(jobs)==0
    with jobs.connect()as conn:
        assert conn.execute(sql.SQL("SELECT count(*) AS n FROM {} WHERE job_id=%s AND kind='succeeded'").format(
            jobs._table('job_events')),(job['job_id'],)).fetchone()['n']==0


@pytest.mark.parametrize('login_scope',[PROFILE],indirect=True)
def test_environment_change_during_final_reference_check_rolls_back(login_scope,monkeypatch):
    from app.economic_batch_calculation import EconomicBatchCalculationService
    jobs,source,holds,contexts,p,s,authority,service,job,worker=setup(login_scope)
    original_outcome=jobs._outcome;prepare=EconomicBatchCalculationService._prepare
    terminal_written=[];digests=worker._digests()
    def recorded(*a,**k):
        result=original_outcome(*a,**k)
        if a[4]=='succeeded':terminal_written.append(True)
        return result
    def changed(*a,**k):
        result=prepare(*a,**k)
        if terminal_written:monkeypatch.setattr(worker,'_digests',lambda:(digests[0],'e'*64))
        return result
    monkeypatch.setattr(jobs,'_outcome',recorded)
    monkeypatch.setattr(EconomicBatchCalculationService,'_prepare',changed)
    outcome=worker.run_once(str(job['job_id']))
    assert terminal_written and outcome.state=='hold'
    assert publication_count(jobs)==0 and row(jobs,job)['state']=='hold'


@pytest.mark.parametrize('login_scope',[PROFILE],indirect=True)
def test_existing_live_lease_is_not_taken_over(login_scope,monkeypatch):
    jobs,source,holds,contexts,p,s,authority,service,job,worker=setup(login_scope)
    lease=jobs.claim(300,allowed_stages=('simulation',),tenant_id='tenant-1',job_id=str(job['job_id']))
    def fail(*a,**k):raise AssertionError('calculation under another live lease')
    monkeypatch.setattr(ProductionBatchLedger,'calculate',fail)
    assert worker.run_once(str(job['job_id']))is None
    current=row(jobs,job)
    assert current['lease_token']==lease['lease_token']and current['attempt_count']==1
    assert publication_count(jobs)==0


@pytest.mark.parametrize('login_scope',[PROFILE],indirect=True)
def test_concurrent_workers_publish_once(login_scope,monkeypatch):
    from concurrent.futures import ThreadPoolExecutor
    jobs,source,holds,contexts,p,s,authority,service,job,worker=setup(login_scope)
    calls=[];calculate=ProductionBatchLedger.calculate
    def counted(*a,**k):calls.append(1);return calculate(*a,**k)
    monkeypatch.setattr(ProductionBatchLedger,'calculate',counted)
    def run(_):return EconomicBatchWorker(authority,tenant_id='tenant-1').run_once(str(job['job_id']))
    with ThreadPoolExecutor(max_workers=2)as pool:outcomes=list(pool.map(run,range(2)))
    assert sum(value is not None and value.state=='succeeded'for value in outcomes)==1
    assert outcomes.count(None)==1 and len(calls)==1 and publication_count(jobs)==1


@pytest.mark.parametrize('login_scope',[PROFILE],indirect=True)
@pytest.mark.parametrize('scope',['artifact','economic_batch_source_read','market_hold_context_read'])
def test_late_current_scope_revoke_is_held_without_publication(login_scope,monkeypatch,scope):
    jobs,source,holds,contexts,p,s,authority,service,job,worker=setup(login_scope)
    calculate=ProductionBatchLedger.calculate
    def revoke(*a,**k):
        result=calculate(*a,**k);p['scopes'].remove(scope);return result
    monkeypatch.setattr(ProductionBatchLedger,'calculate',revoke)
    outcome=worker.run_once(str(job['job_id']))
    assert outcome.state=='hold'and publication_count(jobs)==0 and row(jobs,job)['state']=='hold'


@pytest.mark.parametrize('login_scope',[PROFILE],indirect=True)
@pytest.mark.parametrize('index',[0,1])
def test_code_and_environment_guard_faults_are_held(login_scope,monkeypatch,index):
    jobs,source,holds,contexts,p,s,authority,service,job,worker=setup(login_scope)
    calculate=ProductionBatchLedger.calculate;changed=list(worker._digests());changed[index]='f'*64
    def replace_digest(*a,**k):
        result=calculate(*a,**k);monkeypatch.setattr(worker,'_digests',lambda:tuple(changed));return result
    monkeypatch.setattr(ProductionBatchLedger,'calculate',replace_digest)
    outcome=worker.run_once(str(job['job_id']))
    assert outcome.state=='hold'and row(jobs,job)['state']=='hold'and publication_count(jobs)==0


@pytest.mark.parametrize('login_scope',[PROFILE],indirect=True)
def test_durable_write_exception_retains_retry_and_no_publication(login_scope,monkeypatch):
    jobs,source,holds,contexts,p,s,authority,service,job,worker=setup(login_scope)
    def fail(*a,**k):raise OSError('self-authored storage failure')
    monkeypatch.setattr(jobs,'_durable_artifact',fail)
    outcome=worker.run_once(str(job['job_id']))
    assert outcome.state=='queued'and outcome.reason_code=='economic_batch_runtime_failure'
    assert publication_count(jobs)==0 and row(jobs,job)['state']=='queued'


@pytest.mark.parametrize('login_scope',[PROFILE],indirect=True)
@pytest.mark.parametrize('name',['_insert_publication','_outcome'])
def test_actual_transaction_writes_are_rolled_back_after_injected_DB_failure(login_scope,monkeypatch,name):
    jobs,source,holds,contexts,p,s,authority,service,job,worker=setup(login_scope)
    original=getattr(jobs,name)
    def fail(*a,**k):
        result=original(*a,**k)
        if name=='_insert_publication'or a[4]=='succeeded':raise RuntimeError('self-authored DB failure')
        return result
    monkeypatch.setattr(jobs,name,fail)
    outcome=worker.run_once(str(job['job_id']))
    assert outcome.state=='hold'and publication_count(jobs)==0 and row(jobs,job)['state']=='hold'
    assert jobs.read_artifact('tenant-1',job['job_id'])is None


@pytest.mark.parametrize('login_scope',[PROFILE],indirect=True)
def test_envelope_capacity_fault_is_held_without_truncation(login_scope,monkeypatch):
    from app import economic_batch_worker as module
    jobs,source,holds,contexts,p,s,authority,service,job,worker=setup(login_scope)
    monkeypatch.setattr(module,'MAX_ARTIFACT_BYTES',64)
    outcome=worker.run_once(str(job['job_id']))
    assert outcome.state=='hold'and publication_count(jobs)==0 and row(jobs,job)['state']=='hold'


@pytest.mark.parametrize('login_scope',[PROFILE],indirect=True)
def test_actual_expired_attempt_is_reclaimed_once_and_old_token_cannot_publish(login_scope):
    jobs,source,holds,contexts,p,s,authority,service,job,worker=setup(login_scope)
    old=jobs.claim(300,allowed_stages=('simulation',),tenant_id='tenant-1',job_id=str(job['job_id']))
    with jobs.connect()as conn:
        conn.execute(sql.SQL("UPDATE {} SET lease_until=clock_timestamp()-interval '1 second' WHERE job_id=%s").format(jobs._table('jobs')),(job['job_id'],))
    assert row(jobs,job)['lease_live']is False
    outcome=worker.run_once(str(job['job_id']))
    assert outcome.state=='succeeded'and outcome.attempt==2 and publication_count(jobs)==1
    assert jobs.fail('tenant-1',job['job_id'],old['attempt'],old['lease_token'],'hold','old_token')is False
    assert row(jobs,job)['state']=='succeeded'and row(jobs,job)['attempt_count']==2
    assert jobs.read_artifact('foreign',job['job_id'])is None


@pytest.mark.parametrize('login_scope',[PROFILE],indirect=True)
@pytest.mark.parametrize('part',['root','context'])
def test_late_root_or_context_rebinding_cannot_publish(login_scope,monkeypatch,tmp_path,part):
    from copy import copy
    jobs,source,holds,contexts,p,s,authority,service,job,worker=setup(login_scope)
    calculate=ProductionBatchLedger.calculate
    def rebind(*a,**k):
        result=calculate(*a,**k)
        if part=='root':jobs.artifact_root=tmp_path/'another-root'
        else:holds._context_store=copy(contexts)
        return result
    monkeypatch.setattr(ProductionBatchLedger,'calculate',rebind)
    outcome=worker.run_once(str(job['job_id']))
    assert outcome.state=='hold'and publication_count(jobs)==0 and row(jobs,job)['state']=='hold'
    if part=='root':assert not jobs.artifact_root.exists()


@pytest.mark.parametrize('login_scope',[PROFILE],indirect=True)
@pytest.mark.parametrize('bad',['extra','source_uuid','formula'])
def test_malformed_own_input_family_is_closed_without_arithmetic(login_scope,monkeypatch,bad):
    jobs,source,holds,contexts,p,s,authority,service,job,worker=setup(login_scope)
    value=json.loads(jobs._verified_input(row(jobs,job)))
    if bad=='extra':value['unexpected']='field'
    elif bad=='source_uuid':value['scenario_source_job_id']='invalid'
    else:value['formula_version']='unsupported'
    malformed=jobs.submit('tenant-1','simulation',value,'malformed-'+bad)
    def fail(*a,**k):raise AssertionError('arithmetic for malformed input')
    monkeypatch.setattr(ProductionBatchLedger,'calculate',fail)
    outcome=worker.run_once(str(malformed['job_id']))
    assert outcome.state=='hold'and row(jobs,malformed)['state']=='hold'and publication_count(jobs)==0
