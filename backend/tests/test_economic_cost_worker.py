"""Owned SCRAM cost publications over self-authored assumptions, not farm evidence."""
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime,timezone
from decimal import Decimal,localcontext
from hashlib import sha256
import json

import pytest
from psycopg import sql

from app import economic_cost_trace as trace
from app.economic_cost_calculation import EconomicCostCalculationService
from app.economic_cost_worker import EconomicCostWorker,CostCalculationOutcome,ARTIFACT_VERSION
from app.economic_production_batches import ProductionBatchLedger,result_bytes
from login_database import login_database,login_scope
from test_economic_batch_calculation import PROFILE,assembly,request
from test_economic_batch_worker import publication_count,row


def setup(scope):
    jobs,source,holds,contexts,p,s,authority,base=assembly(scope)
    p['scopes'].add('cancel')
    service=EconomicCostCalculationService(authority)
    job=service.submit('tenant-1',request(s))
    worker=EconomicCostWorker(authority,tenant_id='tenant-1')
    return jobs,source,holds,contexts,p,s,authority,service,base,job,worker


def unpublished(jobs,job,state='hold'):
    assert row(jobs,job)['state']==state
    assert publication_count(jobs)==0
    assert jobs.get_publication('tenant-1',job['job_id'])is None
    assert jobs.read_artifact('tenant-1',job['job_id'])is None


@pytest.mark.parametrize('login_scope',[PROFILE],indirect=True)
def test_actual_cost_lease_publishes_complete_trace_once_and_preserves_first_retry(login_scope,monkeypatch,tmp_path):
    jobs,source,holds,contexts,p,s,authority,service,base,job,worker=setup(login_scope)
    calls=[];originals=[];traces=[]
    calculate=trace.CostLineLedger.calculate;calculate_base=ProductionBatchLedger.calculate
    def counted_base(*a,**k):
        result=calculate_base(*a,**k);originals.append(result_bytes(result));calls.append('v10');return result
    def counted(*a,**k):
        result=calculate(*a,**k);traces.append(trace.trace_bytes(result));calls.append('trace');return result
    monkeypatch.setattr(ProductionBatchLedger,'calculate',counted_base)
    monkeypatch.setattr(trace.CostLineLedger,'calculate',counted)
    before=s.model_dump();first_raw=jobs._verified_input(row(jobs,job))
    outcome=worker.run_once(str(job['job_id']))
    assert type(outcome)is CostCalculationOutcome
    assert outcome.state=='succeeded'and outcome.reason_code=='completed'and outcome.attempt==1
    assert calls==['v10','trace']and s.model_dump()==before and not s.harvests and not s.sales
    stored=row(jobs,job);assert stored['state']=='succeeded'and stored['lease_token']is None
    assert stored['created_at']==job['created_at']and jobs._verified_input(stored)==first_raw
    raw=jobs.read_artifact('tenant-1',job['job_id']);artifact=json.loads(raw)
    assert raw==json.dumps(artifact,sort_keys=True,separators=(',',':'),allow_nan=False).encode()
    assert ARTIFACT_VERSION=='economic-cost-line-calculation-result-v1'
    assert artifact['artifact_version']==ARTIFACT_VERSION and artifact['status']=='completed'
    assert artifact['claim_scope']=='conditional_user_assumptions_only'
    assert artifact['job_id']==str(job['job_id'])and artifact['tenant_id']=='tenant-1'and artifact['attempt']==1
    assert artifact['input']==json.loads(first_raw)and artifact['input_sha256']==job['input_sha256']==sha256(first_raw).hexdigest()
    value=artifact['input'];assert value['input_version']=='economic-cost-line-calculation-input-v1'
    assert value['base_input']==base._prepare('tenant-1',request(s)).model_dump(mode='json')
    assert value['base_input']['scenario_source_job_id']==source.get_economic_scenario_pin(s.scenario_id,s.scenario_revision)['immutable_job_input_ref']
    assert value['trace_version']==trace.TRACE_VERSION and value['code_sha256']==trace.CODE_SHA256
    assert value['component_sha256']==trace.COMPONENT_SHA256
    result=artifact['result'];original=result['base_result'];ledger=original['ledger']
    assert result==json.loads(traces[0])and original==json.loads(originals[0])
    assert outcome.trace_id==result['trace_id']and result['trace_version']==trace.TRACE_VERSION
    assert result['code_sha256']==trace.CODE_SHA256 and result['component_sha256']==trace.COMPONENT_SHA256
    assert result['currency']=='KRW'and result['scope']=='conditional_user_assumptions_only'
    with localcontext()as ctx:
        ctx.prec=300
        expected={cost.id:Decimal(cost.quantity.value)*Decimal(cost.unit_cost.value)
            for cost in (*s.variable_costs,*s.fixed_costs)}
        lines=result['lines'];groups={group['category']:group for group in result['groups']}
        assert len(lines)==len(expected)==1
        for line in lines:
            cost=next(cost for cost in (*s.variable_costs,*s.fixed_costs)if cost.id==line['cost']['id'])
            assert line['cost']==cost.model_dump(mode='json')
            assert Decimal(line['incurred'])==expected[cost.id]
            assert Decimal(line['bank_paid_in_period'])==Decimal(cost.payment.value)
            assert Decimal(line['remaining_payable_at_period_end'])==expected[cost.id]-Decimal(cost.payment.value)
        for category in ('variable','fixed'):
            group=groups[category];selected=[line for line in lines if line['category']==category]
            total=sum((Decimal(line['incurred'])for line in selected),Decimal(0))
            assert group['declared']is True and Decimal(group['incurred'])==total==Decimal(ledger[category+'_cost'])
        payable=sum((Decimal(group['remaining_payable_at_period_end'])for group in groups.values()),Decimal(0))
        paid=sum((Decimal(line['bank_paid_in_period'])for line in lines),Decimal(0))
        assert payable==Decimal(ledger['operating_payable_end'])==0
        assert paid==sum((Decimal(month['bank_outflow'])for month in result['months']),Decimal(0))==20
        assert Decimal(original['batch_costs'][0]['variable_incurred'])==expected[s.variable_costs[0].id]==20
        assert Decimal(ledger['operating_cash'])==-paid
    assert result['ledger_payable_reconciliation']=='matched'
    assert ledger['formula_version']=='economic-ledger-v10-declared-production-batches'
    assert ledger['assessment_status']=='hold'and result['G0_G4']==original['G0_G4']=='not_assessed'
    assert result['R2']==original['R2']=='not_approved'
    assert sha256(traces[0]).hexdigest()==artifact['result_sha256']
    assert (artifact['code_sha256'],artifact['environment_sha256'])==worker._digests()
    publication=jobs.get_publication('tenant-1',job['job_id'])
    assert publication_count(jobs)==1 and publication['artifact_sha256']==sha256(raw).hexdigest()
    assert publication['artifact_size']==len(raw)
    assert publication['manifest']=={'schema_version':'1','job_id':str(job['job_id']),
        'stage':'simulation','input_sha256':job['input_sha256'],'attempt':1,'artifact_sha256':sha256(raw).hexdigest()}
    first=publication.copy();retry=service.submit('tenant-1',request(s))
    assert retry['job_id']==job['job_id']and retry['created_at']==job['created_at']
    assert jobs._verified_input(row(jobs,retry))==first_raw
    assert worker.run_once(str(job['job_id']))is None and calls==['v10','trace']
    assert jobs.get_publication('tenant-1',job['job_id'])==first
    assert jobs.read_artifact('tenant-1',job['job_id'])==raw
    (tmp_path/'cost-published-result-v1.json').write_bytes(raw)
    proof={'observed_at_UTC':datetime.now(timezone.utc).isoformat(),'job_id':str(job['job_id']),
        'source_job_id':value['base_input']['scenario_source_job_id'],'input_sha256':job['input_sha256'],
        'artifact_sha256':publication['artifact_sha256'],'artifact_size':len(raw),
        'trace_id':outcome.trace_id,'trace_version':result['trace_version'],
        'result_sha256':artifact['result_sha256'],'code_sha256':artifact['code_sha256'],
        'environment_sha256':artifact['environment_sha256'],'manifest':publication['manifest'],
        'job_created_at':job['created_at'].isoformat(),'published_at':publication['published_at'].isoformat(),
        'actual_trace_calls':calls.count('trace'),'actual_v10_calls':calls.count('v10'),
        'independent_Decimal_precision':300,'expected_variable_cost_KRW':str(expected[s.variable_costs[0].id]),
        'actual_variable_cost_KRW':ledger['variable_cost'],'actual_operating_cash_KRW':ledger['operating_cash'],
        'original_v10_bytes_sha256':sha256(originals[0]).hexdigest(),'same_result_after_retry':True,
        'scope':'self_authored_QA_only','G0_G4':'not_assessed','R2':'not_approved'}
    (tmp_path/'cost-published-proof-v1.json').write_text(json.dumps(proof,indent=2)+'\n')
    for name in ('cost-published-result-v1.json','cost-published-proof-v1.json'):(tmp_path/name).chmod(0o600)


@pytest.mark.parametrize('login_scope',[PROFILE],indirect=True)
def test_other_families_including_original_v10_are_not_claimed(login_scope,monkeypatch):
    jobs,source,holds,contexts,p,s,authority,service,base,job,worker=setup(login_scope)
    old=base.submit('tenant-1',request(s))
    generic=jobs.submit('tenant-1','simulation',{'input_version':'economic-calculation-input-v1'},'other-family')
    def fail(*a,**k):raise AssertionError('cost calculation for another input family')
    monkeypatch.setattr(trace.CostLineLedger,'calculate',fail)
    for other in (old,generic):
        assert worker.run_once(str(other['job_id']))is None
        assert row(jobs,other)['state']=='queued'and row(jobs,other)['attempt_count']==0
    assert row(jobs,job)['attempt_count']==0 and publication_count(jobs)==0


@pytest.mark.parametrize('login_scope',[PROFILE],indirect=True)
def test_malformed_own_input_family_closes_without_arithmetic(login_scope,monkeypatch):
    jobs,source,holds,contexts,p,s,authority,service,base,job,worker=setup(login_scope)
    def fail(*a,**k):raise AssertionError('arithmetic for malformed cost input')
    monkeypatch.setattr(trace.CostLineLedger,'calculate',fail)
    for bad in ('extra','source_uuid','trace_version','component'):
        value=json.loads(jobs._verified_input(row(jobs,job)))
        if bad=='extra':value['unexpected']='field'
        elif bad=='source_uuid':value['base_input']['scenario_source_job_id']='invalid'
        elif bad=='trace_version':value['trace_version']='unsupported'
        else:value['component_sha256']={'invented':'f'*64}
        malformed=jobs.submit('tenant-1','simulation',value,'malformed-cost-'+bad)
        outcome=worker.run_once(str(malformed['job_id']))
        assert outcome.state=='hold'and outcome.reason_code=='economic_cost_input_hold'and outcome.trace_id is None
        unpublished(jobs,malformed)
    assert row(jobs,job)['attempt_count']==0


@pytest.mark.parametrize('login_scope',[PROFILE],indirect=True)
def test_wrong_registered_evidence_is_held_before_arithmetic(login_scope,monkeypatch):
    jobs,source,holds,contexts,p,s,authority,service,base,job,worker=setup(login_scope)
    value=json.loads(jobs._verified_input(row(jobs,job)));value['base_input']['evidence_sha256']='e'*64
    bad=jobs.submit('tenant-1','simulation',value,'incorrect-cost-evidence')
    def fail(*a,**k):raise AssertionError('arithmetic before cost evidence match')
    monkeypatch.setattr(trace.CostLineLedger,'calculate',fail)
    outcome=worker.run_once(str(bad['job_id']))
    assert outcome.state=='hold'and outcome.reason_code=='economic_cost_input_hold'
    unpublished(jobs,bad);assert row(jobs,job)['state']=='queued'


@pytest.mark.parametrize('login_scope',[PROFILE],indirect=True)
def test_every_current_scope_is_required_before_claim(login_scope):
    jobs,source,holds,contexts,p,s,authority,service,base,job,worker=setup(login_scope)
    for scope in ('metadata','artifact','economic_batch_source_read','decision_context_read',
            'market_hold_context_read','simulation_execute'):
        p['scopes'].remove(scope)
        try:
            with pytest.raises(PermissionError):worker.run_once(str(job['job_id']))
        finally:p['scopes'].add(scope)
        assert row(jobs,job)['state']=='queued'and row(jobs,job)['attempt_count']==0
    assert publication_count(jobs)==0


@pytest.mark.parametrize('login_scope',[PROFILE],indirect=True)
def test_late_current_scopes_prevent_publication(login_scope,monkeypatch):
    jobs,source,holds,contexts,p,s,authority,service,base,job,worker=setup(login_scope)
    calculate=trace.CostLineLedger.calculate
    for scope in ('artifact','economic_batch_source_read','decision_context_read',
            'market_hold_context_read','simulation_execute'):
        current=service.submit('tenant-1',request(s,'late-'+scope))
        def revoke(*a,**k):
            result=calculate(*a,**k);p['scopes'].remove(scope);return result
        try:
            with monkeypatch.context()as patch:
                patch.setattr(trace.CostLineLedger,'calculate',revoke)
                outcome=worker.run_once(str(current['job_id']))
        finally:p['scopes'].add(scope)
        assert outcome.state=='hold'and outcome.reason_code=='economic_cost_input_hold'
        unpublished(jobs,current)


@pytest.mark.parametrize('login_scope',[PROFILE],indirect=True)
def test_late_original_reference_change_prevents_publication(login_scope,monkeypatch):
    jobs,source,holds,contexts,p,s,authority,service,base,job,worker=setup(login_scope)
    calculate=trace.CostLineLedger.calculate;pin=source.get_economic_scenario_pin
    def changed(*a,**k):
        result=calculate(*a,**k)
        monkeypatch.setattr(source,'get_economic_scenario_pin',lambda *args:{**pin(*args),'payload_sha256':'f'*64})
        return result
    monkeypatch.setattr(trace.CostLineLedger,'calculate',changed)
    outcome=worker.run_once(str(job['job_id']))
    assert outcome.state=='hold'and outcome.reason_code=='economic_cost_input_hold'
    unpublished(jobs,job)


@pytest.mark.parametrize('login_scope',[PROFILE],indirect=True)
def test_late_trace_program_change_prevents_publication(login_scope,monkeypatch):
    jobs,source,holds,contexts,p,s,authority,service,base,job,worker=setup(login_scope)
    calculate=trace.CostLineLedger.calculate
    def changed(*a,**k):
        result=calculate(*a,**k);monkeypatch.setattr(trace,'CODE_SHA256','f'*64);return result
    monkeypatch.setattr(trace.CostLineLedger,'calculate',changed)
    outcome=worker.run_once(str(job['job_id']))
    assert outcome.state=='hold'and outcome.reason_code=='economic_cost_input_hold'
    unpublished(jobs,job)


@pytest.mark.parametrize('login_scope',[PROFILE],indirect=True)
def test_cancel_after_calculation_prevents_publication(login_scope,monkeypatch):
    jobs,source,holds,contexts,p,s,authority,service,base,job,worker=setup(login_scope)
    calculate=trace.CostLineLedger.calculate
    def cancel(*a,**k):
        result=calculate(*a,**k);assert jobs.cancel('tenant-1',job['job_id']);return result
    monkeypatch.setattr(trace.CostLineLedger,'calculate',cancel)
    outcome=worker.run_once(str(job['job_id']))
    assert outcome.state=='canceled'and outcome.reason_code=='canceled_by_request'and outcome.trace_id is None
    unpublished(jobs,job,'canceled')


@pytest.mark.parametrize('login_scope',[PROFILE],indirect=True)
def test_actual_lease_expiry_after_calculation_prevents_publication(login_scope,monkeypatch):
    jobs,source,holds,contexts,p,s,authority,service,base,job,worker=setup(login_scope)
    calculate=trace.CostLineLedger.calculate
    def expire(*a,**k):
        result=calculate(*a,**k)
        with jobs.connect()as conn:
            conn.execute(sql.SQL("UPDATE {} SET lease_until=clock_timestamp()-interval '1 second' WHERE job_id=%s").format(jobs._table('jobs')),(job['job_id'],))
        return result
    monkeypatch.setattr(trace.CostLineLedger,'calculate',expire)
    outcome=worker.run_once(str(job['job_id']))
    assert outcome.state=='unclosed'and outcome.reason_code=='economic_cost_lease_lost'and outcome.trace_id is None
    assert row(jobs,job)['lease_live']is False and publication_count(jobs)==0
    assert jobs.read_artifact('tenant-1',job['job_id'])is None


@pytest.mark.parametrize('login_scope',[PROFILE],indirect=True)
def test_existing_live_lease_is_not_taken_over(login_scope,monkeypatch):
    jobs,source,holds,contexts,p,s,authority,service,base,job,worker=setup(login_scope)
    lease=jobs.claim(300,allowed_stages=('simulation',),tenant_id='tenant-1',job_id=str(job['job_id']))
    def fail(*a,**k):raise AssertionError('cost calculation under another live lease')
    monkeypatch.setattr(trace.CostLineLedger,'calculate',fail)
    assert worker.run_once(str(job['job_id']))is None
    current=row(jobs,job)
    assert current['lease_token']==lease['lease_token']and current['attempt_count']==1
    assert publication_count(jobs)==0


@pytest.mark.parametrize('login_scope',[PROFILE],indirect=True)
def test_expired_attempt_is_reclaimed_and_old_token_cannot_change_result(login_scope):
    jobs,source,holds,contexts,p,s,authority,service,base,job,worker=setup(login_scope)
    old=jobs.claim(300,allowed_stages=('simulation',),tenant_id='tenant-1',job_id=str(job['job_id']))
    with jobs.connect()as conn:
        conn.execute(sql.SQL("UPDATE {} SET lease_until=clock_timestamp()-interval '1 second' WHERE job_id=%s").format(jobs._table('jobs')),(job['job_id'],))
    outcome=worker.run_once(str(job['job_id']))
    assert outcome.state=='succeeded'and outcome.attempt==2 and publication_count(jobs)==1
    raw=jobs.read_artifact('tenant-1',job['job_id'])
    assert jobs.fail('tenant-1',job['job_id'],old['attempt'],old['lease_token'],'hold','old_token')is False
    assert row(jobs,job)['state']=='succeeded'and row(jobs,job)['attempt_count']==2
    assert jobs.read_artifact('tenant-1',job['job_id'])==raw and jobs.read_artifact('foreign',job['job_id'])is None


@pytest.mark.parametrize('login_scope',[PROFILE],indirect=True)
def test_concurrent_cost_workers_calculate_and_publish_once(login_scope,monkeypatch):
    jobs,source,holds,contexts,p,s,authority,service,base,job,worker=setup(login_scope)
    calls=[];calculate=trace.CostLineLedger.calculate
    def counted(*a,**k):calls.append(1);return calculate(*a,**k)
    monkeypatch.setattr(trace.CostLineLedger,'calculate',counted)
    def run(_):return EconomicCostWorker(authority,tenant_id='tenant-1').run_once(str(job['job_id']))
    with ThreadPoolExecutor(max_workers=2)as pool:outcomes=list(pool.map(run,range(2)))
    assert sum(value is not None and value.state=='succeeded'for value in outcomes)==1
    assert outcomes.count(None)==1 and len(calls)==1 and publication_count(jobs)==1


@pytest.mark.parametrize('login_scope',[PROFILE],indirect=True)
def test_scope_revoke_after_success_event_rolls_back_terminal_and_publication(login_scope,monkeypatch):
    jobs,source,holds,contexts,p,s,authority,service,base,job,worker=setup(login_scope)
    event=jobs._event
    def revoke(conn,tenant,job_id,kind,*a,**k):
        event(conn,tenant,job_id,kind,*a,**k)
        if kind=='succeeded':p['scopes'].remove('simulation_execute')
    monkeypatch.setattr(jobs,'_event',revoke)
    outcome=worker.run_once(str(job['job_id']))
    assert outcome.state=='hold';unpublished(jobs,job)
    with jobs.connect()as conn:
        assert conn.execute(sql.SQL("SELECT count(*) AS n FROM {} WHERE job_id=%s AND kind='succeeded'").format(
            jobs._table('job_events')),(job['job_id'],)).fetchone()['n']==0


@pytest.mark.parametrize('login_scope',[PROFILE],indirect=True)
def test_environment_change_during_final_reference_check_rolls_back(login_scope,monkeypatch):
    jobs,source,holds,contexts,p,s,authority,service,base,job,worker=setup(login_scope)
    original_outcome=jobs._outcome;prepare=EconomicCostCalculationService._prepare
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
    monkeypatch.setattr(EconomicCostCalculationService,'_prepare',changed)
    outcome=worker.run_once(str(job['job_id']))
    assert terminal_written and outcome.state=='hold';unpublished(jobs,job)


@pytest.mark.parametrize('login_scope',[PROFILE],indirect=True)
@pytest.mark.parametrize('index',[0,1])
def test_code_and_environment_guard_faults_are_held(login_scope,monkeypatch,index):
    jobs,source,holds,contexts,p,s,authority,service,base,job,worker=setup(login_scope)
    calculate=trace.CostLineLedger.calculate;changed=list(worker._digests());changed[index]='f'*64
    def replace_digest(*a,**k):
        result=calculate(*a,**k);monkeypatch.setattr(worker,'_digests',lambda:tuple(changed));return result
    monkeypatch.setattr(trace.CostLineLedger,'calculate',replace_digest)
    outcome=worker.run_once(str(job['job_id']))
    assert outcome.state=='hold'and outcome.reason_code=='economic_cost_input_hold';unpublished(jobs,job)


@pytest.mark.parametrize('login_scope',[PROFILE],indirect=True)
def test_durable_write_exception_retains_retry_without_publication(login_scope,monkeypatch):
    jobs,source,holds,contexts,p,s,authority,service,base,job,worker=setup(login_scope)
    def fail(*a,**k):raise OSError('self-authored cost storage failure')
    monkeypatch.setattr(jobs,'_durable_artifact',fail)
    outcome=worker.run_once(str(job['job_id']))
    assert outcome.state=='queued'and outcome.reason_code=='economic_cost_runtime_failure'
    unpublished(jobs,job,'queued')


@pytest.mark.parametrize('login_scope',[PROFILE],indirect=True)
@pytest.mark.parametrize('name',['_insert_publication','_outcome'])
def test_actual_transaction_writes_rollback_after_DB_failure(login_scope,monkeypatch,name):
    jobs,source,holds,contexts,p,s,authority,service,base,job,worker=setup(login_scope)
    original=getattr(jobs,name)
    def fail(*a,**k):
        result=original(*a,**k)
        if name=='_insert_publication'or a[4]=='succeeded':raise RuntimeError('self-authored cost DB failure')
        return result
    monkeypatch.setattr(jobs,name,fail)
    outcome=worker.run_once(str(job['job_id']))
    assert outcome.state=='hold'and outcome.reason_code=='economic_cost_input_hold';unpublished(jobs,job)


@pytest.mark.parametrize('login_scope',[PROFILE],indirect=True)
def test_envelope_capacity_fault_is_held_without_truncation(login_scope,monkeypatch):
    from app import economic_batch_worker as module
    jobs,source,holds,contexts,p,s,authority,service,base,job,worker=setup(login_scope)
    monkeypatch.setattr(module,'MAX_ARTIFACT_BYTES',64)
    outcome=worker.run_once(str(job['job_id']))
    assert outcome.state=='hold'and outcome.reason_code=='economic_cost_input_hold';unpublished(jobs,job)


@pytest.mark.parametrize('login_scope',[PROFILE],indirect=True)
def test_actual_publication_metadata_drift_rolls_back(login_scope,monkeypatch):
    jobs,source,holds,contexts,p,s,authority,service,base,job,worker=setup(login_scope)
    insert=jobs._insert_publication;written=[]
    def changed(conn,tenant,job_id,attempt,decision_id,digest,size,manifest):
        result=insert(conn,tenant,job_id,attempt,decision_id,digest,size,{**manifest,'unexpected':'metadata'})
        written.append(True);return result
    monkeypatch.setattr(jobs,'_insert_publication',changed)
    outcome=worker.run_once(str(job['job_id']))
    assert written and outcome.state=='hold'and outcome.reason_code=='economic_cost_input_hold'
    unpublished(jobs,job)


@pytest.mark.parametrize('login_scope',[PROFILE],indirect=True)
@pytest.mark.parametrize('selector',['_input_version','_artifact_version'])
def test_late_fixed_program_selector_drift_prevents_publication(login_scope,monkeypatch,selector):
    jobs,source,holds,contexts,p,s,authority,service,base,job,worker=setup(login_scope)
    calculate=trace.CostLineLedger.calculate
    def changed(*a,**k):
        result=calculate(*a,**k);monkeypatch.setattr(worker,selector,'unsupported-cost-selector');return result
    monkeypatch.setattr(trace.CostLineLedger,'calculate',changed)
    outcome=worker.run_once(str(job['job_id']))
    assert outcome.state=='hold'and outcome.reason_code=='economic_cost_input_hold';unpublished(jobs,job)


@pytest.mark.parametrize('login_scope',[PROFILE],indirect=True)
def test_late_instance_encoder_and_live_failure_selectors_use_captured_hold(login_scope,monkeypatch):
    jobs,source,holds,contexts,p,s,authority,service,base,job,worker=setup(login_scope)
    calculate=trace.CostLineLedger.calculate;forged_encoder_calls=[]
    def changed(*a,**k):
        result=calculate(*a,**k)
        monkeypatch.setattr(worker,'_encode',lambda *_:forged_encoder_calls.append(True)or b'{}')
        monkeypatch.setattr(worker,'_outcome_type',object)
        monkeypatch.setattr(worker,'_reason_prefix','forged_cost_reason')
        return result
    monkeypatch.setattr(trace.CostLineLedger,'calculate',changed)
    outcome=worker.run_once(str(job['job_id']))
    assert type(outcome)is CostCalculationOutcome
    assert outcome.state=='hold'and outcome.reason_code=='economic_cost_input_hold'and outcome.trace_id is None
    assert forged_encoder_calls==[]
    unpublished(jobs,job)
