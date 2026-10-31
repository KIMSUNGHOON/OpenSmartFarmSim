"""Actual owned SCRAM sources and signed context; intent admission is not a result."""
from copy import copy
from dataclasses import replace
from datetime import datetime,timezone
from hashlib import sha256
import hmac

import pytest
from psycopg import sql,Connection

from app.economic_batch_calculation import (EconomicBatchAuthority,
    EconomicBatchCalculationService,EconomicBatchCalculationRequest,
    EconomicBatchCalculationInput,BatchCalculationHold)
from app.economic_batch_source_store import EconomicBatchSourceStore
from app.economic_contracts import OwnedEconomicRecord,iter_economic_numbers
from app.economic_production_batches import OwnedProductionBatch,ProductionBatchLedger,ProductionBatchRef
from app.economics import canonical_scenario_sha256,EconomicLedger
from app.job_store import JobStore,JobIntentConflict
from app.jobs import canonical_input_bytes
from app.market_hold_store import MarketHoldStore
from app.thermal_run_store import ThermalRunStore,snapshot_id_for
from login_database import login_database,login_scope
from test_economic_production_batches import scenario,batch_record
from test_market_hold_store import CONTEXT_KEY,HOLD_KEY,SNAPSHOT_RAWS,canonical,context_verifier

PROFILE={'market_calculation':True,'market_source_storage':True,'economic_batch_source_storage':True}


def assembly(scope):
    base,policy,dsns=scope
    p={'authenticated':True,'tenant_id':'tenant-1','scopes':{'metadata','artifact',
        'simulation_execute','economic_batch_source_read','economic_batch_source_write',
        'decision_context_read','decision_context_write','thermal_snapshot_write',
        'market_hold_issue','market_hold_context_read'}}
    provider=lambda:p
    jobs=JobStore(dsns['authority'],policy.schema,base.artifact_root,
        principal_provider=provider,runtime_identity=(policy,'authority'),audit_runtime_grants=True)
    source=EconomicBatchSourceStore(dsns['authority'],policy.schema,
        principal_provider=provider,runtime_identity=jobs.runtime_identity)
    contexts=ThermalRunStore(dsns['authority'],policy.schema,
        gate_key=b'self-authored-gate-test-key-32bytes',release_verifier=lambda *_:None,
        principal_provider=provider,context_verifier=context_verifier,runtime_identity=jobs.runtime_identity)
    snapshot=contexts.put_snapshot('tenant-1',*SNAPSHOT_RAWS);assert snapshot==snapshot_id_for(*SNAPSHOT_RAWS)
    s=scenario()
    doc={'context_version':'decision-context-v1','tenant_id':'tenant-1','snapshot_id':snapshot,
        'decision_context_id':'context-1','decision_at_utc':s.decision_at.isoformat().replace('+00:00','Z'),
        'claim_mode':'ex_post_replay','decision_time_kind':'hypothetical','authority_id':'test-authority',
        'issued_at_utc':datetime.now(timezone.utc).isoformat().replace('+00:00','Z'),
        'planning_event_sha256':sha256(b'self-authored planning fixture').hexdigest()}
    raw=canonical(doc);signature=hmac.new(CONTEXT_KEY,b'decision-context-v1\0'+raw,sha256).hexdigest()
    contexts.put_decision_context('tenant-1',raw,signature)
    bound_scope={'tenant_id':'tenant-1','snapshot_id':snapshot,'decision_context_id':'context-1',
        'candidate_ids':['crop-1'],'sales_start_utc':'2026-10-01T00:00:00Z',
        'sales_end_utc':'2026-12-01T00:00:00Z','scope_version':'v1'}
    holds=MarketHoldStore(dsns['authority'],policy.schema,context_store=contexts,
        scope_resolver=lambda *_:dict(bound_scope),principal_provider=provider,
        signing_key=HOLD_KEY,runtime_identity=jobs.runtime_identity)
    report=holds.issue_not_evaluated('tenant-1',snapshot,'context-1')
    market={'kind':'unavailable','hold_report_id':report['hold_report_id']}
    data=s.model_dump(mode='json');data.update(market_context=market,scenario_market_context=market)
    s=type(s).model_validate_json(canonical_input_bytes(data))
    values=[('production_batch',OwnedProductionBatch.model_validate(batch_record(s))),('economic_scenario',s)]
    values += [('economic_input',OwnedEconomicRecord(**n.model_dump(),tenant_id=s.tenant_id,
        scope_start=s.period_start,scope_end=s.period_end))for n in iter_economic_numbers(s)]
    for kind,model in values:
        job=jobs.submit('tenant-1','collection',model.model_dump(mode='json'),'source-'+kind+'-'+str(len(model.model_dump_json()))+'-'+getattr(model,'input_id','single'))
        source.adopt_job('tenant-1',kind,str(job['job_id']))
    authority=EconomicBatchAuthority(jobs,source,holds)
    return jobs,source,holds,contexts,p,s,authority,EconomicBatchCalculationService(authority)


def request(s,key='same-request'):
    return EconomicBatchCalculationRequest(scenario_id=s.scenario_id,scenario_revision=s.scenario_revision,
        scenario_sha256=canonical_scenario_sha256(s),idempotency_key=key)


def counts(jobs):
    with jobs.connect()as conn:
        return tuple(conn.execute(sql.SQL('SELECT count(*) AS n FROM {}.{}').format(
            sql.Identifier(jobs.schema),sql.Identifier(table))).fetchone()['n']
            for table in ['jobs','job_events','economic_batch_source_records'])


def test_request_rejects_unknown_fields_and_nonreference_input():
    for d in [{},{'scenario_id':'x','scenario_revision':'r1','scenario_sha256':'a'*64,
        'idempotency_key':'request','amount':'100'}]:
        with pytest.raises(ValueError):EconomicBatchCalculationRequest.model_validate(d)
    with pytest.raises(ValueError):EconomicBatchAuthority(object(),object(),object())


@pytest.mark.parametrize('login_scope',[PROFILE],indirect=True)
def test_actual_registered_scenario_retries_keep_job_bytes_time_and_no_calculation(login_scope,monkeypatch):
    jobs,source,holds,contexts,p,s,authority,service=assembly(login_scope)
    def fail(*a,**k):raise AssertionError('arithmetic at admission')
    monkeypatch.setattr(ProductionBatchLedger,'calculate',fail)
    monkeypatch.setattr(EconomicLedger,'calculate',fail)
    monkeypatch.setattr(EconomicLedger,'_calculate_verified',fail)
    writes=[];execute=Connection.execute
    def measured(conn,query,*a,**k):
        cursor=execute(conn,query,*a,**k);tag=(cursor.statusmessage or '').split(' ')[0]
        if tag in {'INSERT','UPDATE','DELETE','MERGE','CREATE','ALTER','DROP','TRUNCATE','GRANT','REVOKE'}:
            statement=query if type(query)is str else query.as_string(conn)
            target='job_events'if '."job_events"'in statement else'jobs'if '."jobs"'in statement else'other'
            writes.append((tag,target))
        return cursor
    monkeypatch.setattr(Connection,'execute',measured)
    before=counts(jobs);body=request(s)
    first=service.submit('tenant-1',body);second=service.submit('tenant-1',body)
    assert first==second and first['state']=='queued'and first['stage']=='simulation'
    assert counts(jobs)==(before[0]+1,before[1]+1,before[2])
    with jobs.connect()as conn:
        row=jobs._locked_job(conn,'tenant-1',first['job_id']);raw=jobs._verified_input(row)
    value=EconomicBatchCalculationInput.model_validate_json(raw)
    assert canonical_input_bytes(value.model_dump(mode='json'))==raw
    assert value.scenario_sha256==body.scenario_sha256
    assert value.scenario_source_job_id==source.get_economic_scenario_pin(s.scenario_id,s.scenario_revision)['immutable_job_input_ref']
    assert value.input_version=='economic-batch-calculation-input-v1'
    assert value.formula_version=='economic-ledger-v10-declared-production-batches'
    assert jobs.get_publication('tenant-1',first['job_id'])is None
    assert ProductionBatchLedger(authority)._context(s)[0]==body.scenario_sha256
    assert writes and set(writes)<={('INSERT','jobs'),('INSERT','job_events')}


@pytest.mark.parametrize('login_scope',[PROFILE],indirect=True)
def test_wrong_sha_missing_and_foreign_do_not_create_intents(login_scope):
    jobs,source,holds,contexts,p,s,authority,service=assembly(login_scope);before=counts(jobs)
    for changes in [{'scenario_sha256':'f'*64},{'scenario_id':'missing'}]:
        with pytest.raises(BatchCalculationHold):service.submit('tenant-1',request(s).model_copy(update=changes))
    with pytest.raises(PermissionError):service.submit('foreign',request(s))
    assert counts(jobs)==before


@pytest.mark.parametrize('login_scope',[PROFILE],indirect=True)
def test_same_key_different_registered_scenario_conflicts_without_partial_rows(login_scope):
    jobs,source,holds,contexts,p,s,authority,service=assembly(login_scope)
    service.submit('tenant-1',request(s));other=s.model_copy(update={'scenario_revision':'r2'})
    job=jobs.submit('tenant-1','collection',other.model_dump(mode='json'),'source-r2')
    source.adopt_job('tenant-1','economic_scenario',str(job['job_id']));before=counts(jobs)
    with pytest.raises(JobIntentConflict):service.submit('tenant-1',request(other))
    assert counts(jobs)==before


@pytest.mark.parametrize('login_scope',[PROFILE],indirect=True)
def test_commit_time_execution_revoke_rolls_back_job_and_event(login_scope,monkeypatch):
    jobs,source,holds,contexts,p,s,authority,service=assembly(login_scope);before=counts(jobs)
    original=jobs._event
    def revoke(*a,**k):
        original(*a,**k);p['scopes'].remove('simulation_execute')
    monkeypatch.setattr(jobs,'_event',revoke)
    with pytest.raises(PermissionError):service.submit('tenant-1',request(s))
    assert counts(jobs)==before


@pytest.mark.parametrize('login_scope',[PROFILE],indirect=True)
def test_changed_context_pointer_is_rejected_even_if_same_configuration(login_scope):
    jobs,source,holds,contexts,p,s,authority,service=assembly(login_scope);before=counts(jobs)
    holds._context_store=copy(contexts)
    with pytest.raises(RuntimeError):service.submit('tenant-1',request(s))
    assert counts(jobs)==before


@pytest.mark.parametrize('login_scope',[PROFILE],indirect=True)
@pytest.mark.parametrize('scope',['metadata','economic_batch_source_read','decision_context_read',
    'market_hold_context_read','simulation_execute'])
def test_each_current_scope_is_required_before_job_insertion(login_scope,scope):
    jobs,source,holds,contexts,p,s,authority,service=assembly(login_scope);before=counts(jobs)
    p['scopes'].remove(scope)
    with pytest.raises(PermissionError):service.submit('tenant-1',request(s))
    assert counts(jobs)==before


@pytest.mark.parametrize('login_scope',[PROFILE],indirect=True)
@pytest.mark.parametrize('scope',['economic_batch_source_read','market_hold_context_read'])
def test_signed_hold_read_cannot_return_after_late_scope_revocation(login_scope,monkeypatch,scope):
    jobs,source,holds,contexts,p,s,authority,service=assembly(login_scope);before=counts(jobs)
    original=holds.get_market_hold_report
    def revoke(*a):
        value=original(*a);p['scopes'].remove(scope);return value
    monkeypatch.setattr(holds,'get_market_hold_report',revoke)
    with pytest.raises(PermissionError):service.submit('tenant-1',request(s))
    assert counts(jobs)==before


@pytest.mark.parametrize('login_scope',[PROFILE],indirect=True)
def test_late_pointer_change_rolls_back_job_and_event(login_scope,monkeypatch):
    jobs,source,holds,contexts,p,s,authority,service=assembly(login_scope);before=counts(jobs)
    original=jobs._event
    def change(*a,**k):
        original(*a,**k);holds._context_store=copy(contexts)
    monkeypatch.setattr(jobs,'_event',change)
    with pytest.raises(RuntimeError):service.submit('tenant-1',request(s))
    assert counts(jobs)==before


@pytest.mark.parametrize('login_scope',[PROFILE],indirect=True)
@pytest.mark.parametrize('bad',['batch_missing','batch_period','input_missing'])
def test_real_registered_but_incomplete_or_wrong_period_sources_are_held(login_scope,bad):
    jobs,source,holds,contexts,p,s,authority,service=assembly(login_scope)
    if bad=='batch_missing':
        changed=s.model_copy(update={'production_batches':(ProductionBatchRef(batch_id='missing',revision='r1'),)})
    elif bad=='batch_period':
        batch=OwnedProductionBatch.model_validate(batch_record(s)).model_copy(update={
            'revision':'r2','scope_end':s.period_start})
        job=jobs.submit('tenant-1','collection',batch.model_dump(mode='json'),'wrong-period-batch')
        source.adopt_job('tenant-1','production_batch',str(job['job_id']))
        changed=s.model_copy(update={'production_batches':(ProductionBatchRef(batch_id='batch-1',revision='r2'),)})
    else:
        cost=s.variable_costs[0]
        cost=cost.model_copy(update={'quantity':cost.quantity.model_copy(update={'revision':'missing'})})
        changed=s.model_copy(update={'variable_costs':(cost,)})
    changed=changed.model_copy(update={'scenario_revision':'invalid-sources'})
    job=jobs.submit('tenant-1','collection',changed.model_dump(mode='json'),'invalid-source-scenario')
    source.adopt_job('tenant-1','economic_scenario',str(job['job_id']));before=counts(jobs)
    with pytest.raises(BatchCalculationHold):service.submit('tenant-1',request(changed))
    assert counts(jobs)==before


@pytest.mark.parametrize('login_scope',[PROFILE],indirect=True)
def test_actual_signed_hold_cannot_be_verified_with_another_key(login_scope):
    jobs,source,holds,contexts,p,s,authority,service=assembly(login_scope)
    holds._key=b'different-self-authored-test-key-32bytes'
    other=EconomicBatchCalculationService(EconomicBatchAuthority(jobs,source,holds));before=counts(jobs)
    with pytest.raises(BatchCalculationHold):other.submit('tenant-1',request(s))
    assert counts(jobs)==before


@pytest.mark.parametrize('login_scope',[PROFILE],indirect=True)
def test_actual_concurrent_requests_create_one_intent_and_first_time(login_scope):
    from concurrent.futures import ThreadPoolExecutor
    jobs,source,holds,contexts,p,s,authority,service=assembly(login_scope);before=counts(jobs)
    with ThreadPoolExecutor(max_workers=2)as pool:
        rows=list(pool.map(lambda _:service.submit('tenant-1',request(s)),range(2)))
    assert rows[0]==rows[1]
    assert counts(jobs)==(before[0]+1,before[1]+1,before[2])


@pytest.mark.parametrize('login_scope',[PROFILE],indirect=True)
def test_exact_store_and_login_binding_rejects_mismatches(login_scope):
    jobs,source,holds,contexts,p,s,authority,service=assembly(login_scope)
    changes=[(source,'dsn','another-database'),(holds,'schema','another-schema'),
        (contexts,'_principal_provider',lambda:p),(jobs,'audit_runtime_grants',False),
        (source,'runtime_identity',(replace(jobs.runtime_identity[0],economic_batch_source_storage=False),'authority'))]
    for obj,name,bad in changes:
        old=getattr(obj,name);setattr(obj,name,bad)
        try:
            with pytest.raises(ValueError):EconomicBatchAuthority(jobs,source,holds)
            with pytest.raises(RuntimeError):authority.require('tenant-1')
        finally:setattr(obj,name,old)
    assert authority.tenant_is_authenticated('tenant-1')is True
    assert authority.tenant_is_authenticated('foreign')is False
    with pytest.raises(AttributeError):authority.adopt_job
    with pytest.raises(PermissionError):authority.get_decision_context('foreign','snapshot','context')


@pytest.mark.parametrize('login_scope',[PROFILE],indirect=True)
def test_fresh_actual_authority_reaches_unchanged_batch_kernel_without_memory_facade(login_scope):
    jobs,source,holds,contexts,p,s,authority,service=assembly(login_scope)
    provider=jobs.principal_provider;binding=jobs.runtime_identity
    fresh_source=EconomicBatchSourceStore(source.dsn,source.schema,principal_provider=provider,runtime_identity=binding)
    fresh_context=ThermalRunStore(contexts.dsn,contexts.schema,gate_key=contexts._gate_key,
        release_verifier=contexts._release_verifier,context_verifier=contexts._context_verifier,
        principal_provider=provider,runtime_identity=binding)
    fresh_holds=MarketHoldStore(holds.dsn,holds.schema,context_store=fresh_context,
        scope_resolver=holds._scope_resolver,principal_provider=provider,
        signing_key=holds._key,runtime_identity=binding)
    fresh=EconomicBatchAuthority(jobs,fresh_source,fresh_holds)
    admitted=service.submit('tenant-1',request(s));before=counts(jobs)
    result=ProductionBatchLedger(fresh).calculate(s)
    assert result.ledger.variable_cost==20 and result.ledger.operating_cash==-20
    assert result.ledger.assessment_status=='hold'and result.G0_G4=='not_assessed'
    assert not s.harvests and not s.sales and counts(jobs)==before
    assert EconomicBatchCalculationService(fresh).submit('tenant-1',request(s))==admitted


@pytest.mark.parametrize('login_scope',[PROFILE],indirect=True)
def test_registered_unicode_scenario_keeps_exact_utf8_source_and_intent_hash(login_scope):
    jobs,source,holds,contexts,p,s,authority,service=assembly(login_scope)
    s=s.model_copy(update={'scenario_id':'자체-방울토마토-생산비'})
    source_job=jobs.submit('tenant-1','collection',s.model_dump(mode='json'),'unicode-source')
    source.adopt_job('tenant-1','economic_scenario',str(source_job['job_id']))
    admitted=service.submit('tenant-1',request(s))
    with jobs.connect()as conn:
        row=jobs._locked_job(conn,'tenant-1',admitted['job_id']);raw=jobs._verified_input(row)
    value=EconomicBatchCalculationInput.model_validate_json(raw)
    assert value.scenario_id==s.scenario_id and s.scenario_id.encode()in raw
    assert value.scenario_sha256==source_job['input_sha256']==canonical_scenario_sha256(s)
    assert value.scenario_source_job_id==str(source_job['job_id'])


@pytest.mark.parametrize('login_scope',[PROFILE],indirect=True)
def test_reference_preparation_remains_read_only_without_execution_permission(login_scope,monkeypatch):
    jobs,source,holds,contexts,p,s,authority,service=assembly(login_scope);before=counts(jobs)
    p['scopes'].remove('simulation_execute')
    def fail(*a,**k):raise AssertionError('arithmetic during reference validation')
    monkeypatch.setattr(ProductionBatchLedger,'calculate',fail)
    monkeypatch.setattr(EconomicLedger,'_calculate_verified',fail)
    value=service._prepare('tenant-1',request(s))
    assert value.scenario_sha256==canonical_scenario_sha256(s)
    with pytest.raises(PermissionError):service.submit('tenant-1',request(s))
    assert counts(jobs)==before
