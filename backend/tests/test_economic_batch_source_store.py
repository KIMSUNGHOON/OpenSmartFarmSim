"""Owned PostgreSQL inputs for conditional batch costs; no farm-data approval."""
from copy import deepcopy
from dataclasses import replace
from hashlib import sha256

import psycopg
from psycopg import sql
import pytest

from app.economic_contracts import OwnedEconomicRecord
from app.economic_production_batches import BatchEconomicScenario, OwnedProductionBatch
from app.economic_batch_source_store import EconomicBatchSourceStore, VERSION
from app.jobs import canonical_input_bytes
from app.market_source_store import MarketSourceStore, MarketSourceDenied, MarketSourceConflict
from app.runtime_roles import RuntimeLoginPolicy, RolePolicyHold, audit_runtime_roles
from app.runtime_login import connect_runtime
from login_database import login_database, login_scope
from test_economic_production_batches import scenario, batch_record
from test_market_source_store import submit
from test_operator_config import private_config,isolated_assembly,store as write_config

PROFILE={'market_calculation':True,'market_source_storage':True,'economic_batch_source_storage':True}


def principal():
    return {'authenticated':True,'tenant_id':'tenant-1',
            'scopes':{'market_source_read','market_source_write',
                      'economic_batch_source_read','economic_batch_source_write'}}


def store_for(scope,p):
    _,policy,dsns=scope
    return EconomicBatchSourceStore(dsns['authority'],policy.schema,
        runtime_identity=(policy,'authority'),principal_provider=lambda:p)


def test_new_models_are_canonical_and_legacy_model_family_stays_v3():
    s=scenario();raw=canonical_input_bytes(s.model_dump(mode='json'))
    model,i,r=EconomicBatchSourceStore._model('economic_scenario','tenant-1',raw)
    assert type(model)is BatchEconomicScenario and(i,r)==('scenario-1','r1')
    with pytest.raises(ValueError):MarketSourceStore._model('economic_scenario','tenant-1',raw)
    batch=OwnedProductionBatch.model_validate(batch_record(s))
    raw=canonical_input_bytes(batch.model_dump(mode='json'))
    assert EconomicBatchSourceStore._model('production_batch','tenant-1',raw)[0]==batch
    for bad in [raw+b' ',raw.replace(b'"immutable":true',b'"immutable":1'),raw.replace(b'"tenant-1"',b'"foreign"')]:
        with pytest.raises(ValueError):EconomicBatchSourceStore._model('production_batch','tenant-1',bad)


def test_opt_in_policy_is_strict_and_requires_existing_market_source_profile():
    args=('scope','owner','prefix','database')
    assert RuntimeLoginPolicy(*args).economic_batch_source_storage is False
    for bad in [1,'true',None]:
        with pytest.raises(ValueError):RuntimeLoginPolicy(*args,economic_batch_source_storage=bad)
    with pytest.raises(ValueError):RuntimeLoginPolicy(*args,economic_batch_source_storage=True)
    p=RuntimeLoginPolicy(*args,**PROFILE)
    assert p.economic_batch_source_storage
    with pytest.raises(ValueError):EconomicBatchSourceStore('unused',p.schema,
        runtime_identity=(replace(p,economic_batch_source_storage=False),'authority'),principal_provider=principal)


@pytest.mark.parametrize('option',['omit',False,True])
def test_operator_option_preserves_default_and_allows_explicit_flag(option,private_config,monkeypatch):
    from app.operator_config import load_api_runtime
    path,doc=private_config
    doc['policy']['market_source_storage']=True
    if option=='omit':doc['policy'].pop('economic_batch_source_storage',None)
    else:doc['policy']['economic_batch_source_storage']=option
    write_config(path,doc);calls=isolated_assembly(monkeypatch);load_api_runtime(path)
    assert calls[0].policy.economic_batch_source_storage is (option is True)


@pytest.mark.parametrize('option',[0,1,None,'true'])
def test_operator_option_rejects_nonboolean_before_factory(option,private_config,monkeypatch):
    from app.operator_config import load_api_runtime,OperatorConfigHold
    path,doc=private_config;doc['policy']['economic_batch_source_storage']=option
    write_config(path,doc)
    monkeypatch.setattr('app.operator_config.importlib.import_module',lambda *_:pytest.fail('invalid option imported factory'))
    with pytest.raises(OperatorConfigHold):load_api_runtime(path)


@pytest.mark.parametrize('login_scope',[PROFILE],indirect=True)
def test_actual_registration_pin_metadata_and_fresh_reader_preserve_first_bytes(login_scope):
    jobs,policy,_=login_scope;p=principal();store=store_for(login_scope,p);s=scenario()
    b=OwnedProductionBatch.model_validate(batch_record(s))
    values=[('production_batch',b),('economic_scenario',s)]
    for kind,model in values:
        job=submit(jobs,model);job_id=str(job['job_id'])
        assert store.adopt_job('tenant-1',kind,job_id)==model.model_dump(mode='python')
        first=store.get_user_source('tenant-1',kind,
            b.batch_id if kind=='production_batch'else s.scenario_id,'r1')
        assert store.adopt_job('tenant-1',kind,job_id)==model.model_dump(mode='python')
        second=jobs.submit('tenant-1','simulation',model.model_dump(mode='json'),'same-bytes-another-'+kind)
        assert str(second['job_id'])!=job_id
        assert store.adopt_job('tenant-1',kind,str(second['job_id']))==model.model_dump(mode='python')
        assert first==store.get_user_source('tenant-1',kind,first['record_id'],'r1')
        assert first['payload_sha256']==job['input_sha256']
    fresh=store_for(login_scope,p)
    assert fresh.get_production_batch('batch-1','r1')==b.model_dump(mode='python')
    assert fresh.get_economic_scenario('scenario-1','r1')==s.model_dump(mode='python')
    pin=fresh.get_economic_scenario_pin('scenario-1','r1')
    assert pin['immutable_job_input_ref']==job_id
    assert pin['immutable_job_input_sha256']==sha256(canonical_input_bytes(s.model_dump(mode='json'))).hexdigest()
    assert fresh.get_production_batch('missing','r1')is None
    with jobs.connect()as conn:
        assert conn.execute(sql.SQL('SELECT count(*) AS n FROM {}.market_source_records').format(sql.Identifier(policy.schema))).fetchone()['n']==0
        assert conn.execute(sql.SQL('SELECT store_version FROM {}.economic_batch_source_records').format(sql.Identifier(policy.schema))).fetchall()==[{'store_version':VERSION}]*2


@pytest.mark.parametrize('login_scope',[PROFILE],indirect=True)
def test_new_sources_preserve_legacy_registration_and_numeric_input_getters(login_scope):
    jobs,policy,dsns=login_scope;p=principal();store=store_for(login_scope,p)
    old=MarketSourceStore(dsns['authority'],policy.schema,runtime_identity=(policy,'authority'),principal_provider=lambda:p)
    s=scenario();n=s.variable_costs[0].quantity
    owned=OwnedEconomicRecord(**n.model_dump(),tenant_id=s.tenant_id,scope_start=s.period_start,scope_end=s.period_end)
    job=submit(jobs,owned)
    old.adopt_job('tenant-1','economic_input',str(job['job_id']))
    before=old.get_user_source('tenant-1','economic_input',n.input_id,n.revision)
    store.adopt_job('tenant-1','economic_input',str(job['job_id']))
    assert old.get_user_source('tenant-1','economic_input',n.input_id,n.revision)==before
    assert store.get_economic_input(n.input_id,n.revision)==owned.model_dump(mode='python')
    assert old.get_economic_input(n.input_id,n.revision)==owned.model_dump(mode='python')
    with old.connect()as conn:
        assert audit_runtime_roles(conn,policy)['policy_version']=='runtime-economic-batch-source-login-policy-v9'


@pytest.mark.parametrize('login_scope',[PROFILE],indirect=True)
def test_conflicts_rollback_foreign_and_current_scope_revocation(login_scope):
    jobs,policy,_=login_scope;p=principal();store=store_for(login_scope,p)
    b=OwnedProductionBatch.model_validate(batch_record(scenario()))
    job=submit(jobs,b);store.adopt_job('tenant-1','production_batch',str(job['job_id']))
    changed=b.model_copy(update={'source_ref':'different'})
    other=submit(jobs,changed)
    with pytest.raises(MarketSourceConflict):store.adopt_job('tenant-1','production_batch',str(other['job_id']))
    assert store.get_production_batch(b.batch_id,b.revision)==b.model_dump(mode='python')
    p['tenant_id']='foreign'
    assert store.get_production_batch('batch-1','r1')is None
    with pytest.raises(ValueError):store.adopt_job('foreign','production_batch',str(job['job_id']))
    p['tenant_id']='tenant-1';p['scopes'].remove('economic_batch_source_read')
    assert store.get_production_batch('batch-1','r1')is None
    p['scopes'].add('economic_batch_source_read');p['scopes'].remove('economic_batch_source_write')
    with pytest.raises(MarketSourceDenied):store.adopt_job('tenant-1','production_batch',str(job['job_id']))


@pytest.mark.parametrize('login_scope',[PROFILE],indirect=True)
def test_late_reader_revocation_and_immutable_sql_are_rejected(login_scope,monkeypatch):
    jobs,policy,dsns=login_scope;p=principal();store=store_for(login_scope,p)
    b=OwnedProductionBatch.model_validate(batch_record(scenario()))
    job=submit(jobs,b);store.adopt_job('tenant-1','production_batch',str(job['job_id']))
    original=store._verified
    def revoke(*a,**k):
        model=original(*a,**k);p['scopes'].discard('economic_batch_source_read');return model
    monkeypatch.setattr(store,'_verified',revoke)
    with pytest.raises(MarketSourceDenied):store.get_production_batch('batch-1','r1')
    with jobs.connect()as conn:
        with pytest.raises(psycopg.errors.RaiseException):
            conn.execute(sql.SQL("UPDATE {}.economic_batch_source_records SET record_id='changed'").format(sql.Identifier(policy.schema)))
    with connect_runtime(dsns['authority'],policy,'authority')as conn:
        with pytest.raises(psycopg.errors.InsufficientPrivilege):
            conn.execute(sql.SQL('DELETE FROM {}.economic_batch_source_records').format(sql.Identifier(policy.schema)))


@pytest.mark.parametrize('login_scope',[PROFILE],indirect=True)
def test_all_eight_model_families_and_pages_use_the_new_table(login_scope):
    from test_market_source_store import record_items
    from test_market_scenario import case
    from test_economics import TrustedTestRepository,base,opening_lot
    from app.economic_contracts import EconomicScenario
    jobs,policy,_=login_scope;p=principal();store=store_for(login_scope,p);s=scenario()
    source,_=case()
    prior=TrustedTestRepository(EconomicScenario.model_validate(base(opening_inventory=(opening_lot(),))))
    source.prior_costs=prior.prior_costs
    selected={}
    for kind,model in record_items(source):selected.setdefault(kind,model)
    selected['economic_scenario']=s
    selected['production_batch']=OwnedProductionBatch.model_validate(batch_record(s))
    assert len(selected)==8
    for kind,model in selected.items():
        job=submit(jobs,model)
        assert store.adopt_job('tenant-1',kind,str(job['job_id']))==model.model_dump(mode='python')
        page=store.list_user_sources('tenant-1',kind,limit=1)
        assert len(page['items'])==1 and page['next_cursor']is None
        assert page['items'][0]['payload_sha256']==job['input_sha256']
    assert sum(len(store.list_user_sources('tenant-1',k)['items'])for k in selected)==8


@pytest.mark.parametrize('login_scope',[PROFILE],indirect=True)
def test_concurrent_idempotency_and_caller_transaction_rollback(login_scope):
    from concurrent.futures import ThreadPoolExecutor
    jobs,policy,_=login_scope;p=principal();b=OwnedProductionBatch.model_validate(batch_record(scenario()))
    job=submit(jobs,b)
    def adopt(_):return store_for(login_scope,p).adopt_job('tenant-1','production_batch',str(job['job_id']))
    with ThreadPoolExecutor(max_workers=2)as pool:
        assert list(pool.map(adopt,range(2)))==[b.model_dump(mode='python')]*2
    store=store_for(login_scope,p)
    assert len(store.list_user_sources('tenant-1','production_batch')['items'])==1
    other=b.model_copy(update={'batch_id':'rollback-batch'})
    new_job=submit(jobs,other)
    with pytest.raises(RuntimeError,match='abort'):
        with store.connect()as conn:
            store._adopt_in_transaction(conn,'tenant-1','production_batch',str(new_job['job_id']))
            raise RuntimeError('abort')
    assert store.get_production_batch('rollback-batch','r1')is None
    with jobs.connect()as conn:
        assert conn.execute(sql.SQL('SELECT count(*) AS n FROM {}.economic_batch_source_records').format(sql.Identifier(policy.schema))).fetchone()['n']==1


@pytest.mark.parametrize('login_scope',[PROFILE],indirect=True)
def test_read_getters_are_calculation_and_sql_write_free(login_scope,monkeypatch):
    from app.economic_production_batches import ProductionBatchLedger
    from app.economics import EconomicLedger
    jobs,policy,_=login_scope;p=principal();store=store_for(login_scope,p);s=scenario()
    b=OwnedProductionBatch.model_validate(batch_record(s))
    for kind,model in [('production_batch',b),('economic_scenario',s)]:
        job=submit(jobs,model);store.adopt_job('tenant-1',kind,str(job['job_id']))
    def fail(*a,**k):raise AssertionError('calculation during source query')
    monkeypatch.setattr(ProductionBatchLedger,'calculate',fail)
    monkeypatch.setattr(EconomicLedger,'calculate',fail)
    writes=[];tags=[];execute=psycopg.Connection.execute
    def measured(conn,*a,**k):
        cur=execute(conn,*a,**k);tag=(cur.statusmessage or '').split(' ')[0];tags.append(tag)
        if tag in {'INSERT','UPDATE','DELETE','MERGE','CREATE','ALTER','DROP','TRUNCATE','GRANT','REVOKE'}:writes.append(tag)
        return cur
    monkeypatch.setattr(psycopg.Connection,'execute',measured)
    assert store.get_production_batch('batch-1','r1')==b.model_dump(mode='python')
    assert store.get_economic_scenario('scenario-1','r1')==s.model_dump(mode='python')
    assert store.get_economic_scenario_pin('scenario-1','r1')['scenario_id']=='scenario-1'
    assert store.get_user_source('tenant-1','production_batch','batch-1','r1')
    assert store.list_user_sources('tenant-1','production_batch')['items']
    assert tags and not writes


@pytest.mark.parametrize('login_scope',[PROFILE],indirect=True)
def test_late_write_revocation_rolls_back_and_bad_stages_are_not_adopted(login_scope,monkeypatch):
    jobs,policy,_=login_scope;p=principal();store=store_for(login_scope,p)
    b=OwnedProductionBatch.model_validate(batch_record(scenario()));job=submit(jobs,b)
    original=store._verified
    def revoke(*a,**k):
        value=original(*a,**k);p['scopes'].discard('economic_batch_source_write');return value
    monkeypatch.setattr(store,'_verified',revoke)
    with pytest.raises(MarketSourceDenied):store.adopt_job('tenant-1','production_batch',str(job['job_id']))
    p['scopes'].add('economic_batch_source_write');monkeypatch.setattr(store,'_verified',original)
    assert store.get_production_batch('batch-1','r1')is None
    research=submit(jobs,b,stage='research')
    with pytest.raises(ValueError):store.adopt_job('tenant-1','production_batch',str(research['job_id']))


@pytest.mark.parametrize('login_scope',[PROFILE],indirect=True)
def test_optional_table_grants_are_closed_for_other_profiles(login_scope):
    _,policy,dsns=login_scope
    for kind in ['request','worker','supervisor']:
        with connect_runtime(dsns[kind],policy,kind)as conn:
            with pytest.raises(psycopg.errors.InsufficientPrivilege):
                conn.execute(sql.SQL('SELECT * FROM {}.economic_batch_source_records').format(sql.Identifier(policy.schema)))


@pytest.mark.parametrize('login_scope',[PROFILE],indirect=True)
@pytest.mark.parametrize('non_ascii',[False,True])
def test_actual_signed_hold_and_fresh_stored_inputs_reach_batch_ledger(login_scope,non_ascii):
    from app.economic_contracts import iter_economic_numbers
    from app.economic_production_batches import ProductionBatchLedger
    from test_market_signed_hold_integration import signed_market_assembly
    jobs,policy,dsns=login_scope;p=principal();store=store_for(login_scope,p)
    factory,memory,request,_,_=signed_market_assembly(dsns['authority'],policy.schema,
                                                   runtime_identity=(policy,'authority'))
    signed=factory()._source
    d=scenario().model_dump();d['market_context']=d['scenario_market_context']=request['market_context']
    if non_ascii:d['scenario_id']='자체-생산비-계획'
    s=BatchEconomicScenario.model_validate(d)
    b=OwnedProductionBatch.model_validate(batch_record(s))
    records=[('production_batch',b),('economic_scenario',s)]
    records += [('economic_input',OwnedEconomicRecord(**n.model_dump(),tenant_id=s.tenant_id,
                scope_start=s.period_start,scope_end=s.period_end))for n in iter_economic_numbers(s)]
    for kind,model in records:
        job=submit(jobs,model);store.adopt_job('tenant-1',kind,str(job['job_id']))
    memory.records.clear();memory.scenarios.clear();memory.pins.clear()
    fresh=store_for(login_scope,p)
    class Bound:
        def __getattr__(self,name):
            return getattr(signed,name)if name in {'get_market_hold_report','get_decision_context'}else getattr(fresh,name)
    result=ProductionBatchLedger(Bound()).calculate(s)
    assert not s.harvests and not s.sales and result.ledger.variable_cost==20
    assert result.ledger.operating_cash==result.ledger.operating_cash_bridge==-20
    assert result.ledger.assessment_status=='hold' and result.G0_G4=='not_assessed'
    assert len(result.production_batches)==1 and not result.batch_costs[0].harvest_event_declared
