"""Current stored-result reads over real owned SCRAM; no money replay."""
from dataclasses import replace,asdict
from datetime import datetime,timezone,timedelta
from decimal import Decimal
from hashlib import sha256
import json
from pathlib import Path
import subprocess
import sys

import pytest
from psycopg import Connection

from app.economic_batch_query import EconomicBatchResultQuery,BatchResultHold,decode_stored_batch_result
from app.economic_batch_calculation import EconomicBatchAuthority,EconomicBatchCalculationService
from app.economic_batch_source_store import EconomicBatchSourceStore
from app.economic_production_batches import ProductionBatchLedger,result_bytes
from app.economics import EconomicLedger
from app.economic_batch_worker import MAX_ARTIFACT_BYTES
from app.market_hold_store import MarketHoldStore
from app.thermal_run_store import ThermalRunStore
from login_database import login_database,login_scope
from test_economic_batch_calculation import PROFILE,request
from test_economic_batch_worker import setup as worker_setup
from test_economic_production_batches import scenario,Repository


def ready(scope):
    values=worker_setup(scope);jobs,source,holds,contexts,p,s,authority,service,job,worker=values
    assert worker.run_once(str(job['job_id'])).state=='succeeded'
    provider=jobs.principal_provider;binding=jobs.runtime_identity
    fresh_source=EconomicBatchSourceStore(source.dsn,source.schema,principal_provider=provider,runtime_identity=binding)
    fresh_context=ThermalRunStore(contexts.dsn,contexts.schema,gate_key=contexts._gate_key,
        release_verifier=contexts._release_verifier,context_verifier=contexts._context_verifier,
        principal_provider=provider,runtime_identity=binding)
    fresh_holds=MarketHoldStore(holds.dsn,holds.schema,context_store=fresh_context,
        scope_resolver=holds._scope_resolver,principal_provider=provider,signing_key=holds._key,runtime_identity=binding)
    fresh=EconomicBatchAuthority(jobs,fresh_source,fresh_holds)
    p['scopes'].remove('simulation_execute')
    return values,EconomicBatchResultQuery(fresh)


@pytest.mark.parametrize('login_scope',[PROFILE],indirect=True)
def test_fresh_reader_preserves_raw_first_publication_without_execution_math_or_writes(login_scope,monkeypatch,tmp_path):
    values,query=ready(login_scope);jobs,source,holds,contexts,p,s,authority,service,job,worker=values
    expected=jobs.read_artifact('tenant-1',job['job_id']);publication=jobs.get_publication('tenant-1',job['job_id'])
    def fail(*a,**k):raise AssertionError('money arithmetic or execution during stored query')
    monkeypatch.setattr(ProductionBatchLedger,'calculate',fail)
    monkeypatch.setattr(EconomicLedger,'calculate',fail)
    monkeypatch.setattr(EconomicLedger,'_calculate_verified',fail)
    monkeypatch.setattr(type(worker),'run_once',fail)
    monkeypatch.setattr(type(worker),'_digests',fail)
    writes=[];execute=Connection.execute
    def measured(conn,*a,**k):
        cursor=execute(conn,*a,**k);tag=(cursor.statusmessage or '').split(' ')[0]
        if tag in {'INSERT','UPDATE','DELETE','MERGE','CREATE','ALTER','DROP','TRUNCATE','GRANT','REVOKE'}:writes.append(tag)
        return cursor
    monkeypatch.setattr(Connection,'execute',measured)
    found=query.read('tenant-1',str(job['job_id']))
    assert found.raw==expected and found.published_at==publication['published_at']
    assert found.publication_id==publication['publication_id']and not writes
    assert found.result.ledger.variable_cost==Decimal('20')and found.result.ledger.assessment_status=='hold'
    found.result.component_sha256['forged']='x'
    again=query.read('tenant-1',str(job['job_id']))
    assert again.raw==expected and 'forged'not in again.result.component_sha256 and not writes
    proof={'observed_at_UTC':datetime.now(timezone.utc).isoformat(),'job_id':str(job['job_id']),
        'artifact_sha256':sha256(expected).hexdigest(),'artifact_bytes':len(expected),
        'publication_id':str(again.publication_id),'published_at':again.published_at.isoformat(),
        'same_raw_after_retry':True,'independent_return_values':True,'execution_scope_present':False,
        'amount_arithmetic_calls':0,'SQL_write_commands':len(writes),'scope':'owned_synthetic_QA_only',
        'G0_G4':'not_assessed','R2':'not_approved'}
    (tmp_path/'queried-result-v1.json').write_bytes(again.raw)
    (tmp_path/'query-receipt-v1.json').write_text(json.dumps(proof,indent=2)+'\n')


@pytest.mark.parametrize('login_scope',[PROFILE],indirect=True)
def test_unknown_pending_and_other_family_do_not_read_artifact(login_scope,monkeypatch):
    values=worker_setup(login_scope);jobs,source,holds,contexts,p,s,authority,service,job,worker=values
    query=EconomicBatchResultQuery(authority)
    def fail(*a,**k):raise AssertionError('file read for missing or unfinished result')
    monkeypatch.setattr(query,'_read_raw',fail)
    assert query.read('tenant-1','00000000-0000-0000-0000-000000000000')is None
    assert query.read('tenant-1',str(job['job_id']))is None
    other=jobs.submit('tenant-1','simulation',{'input_version':'economic-calculation-input-v1'},'other-query-family')
    assert query.read('tenant-1',str(other['job_id']))is None


@pytest.mark.parametrize('login_scope',[PROFILE],indirect=True)
@pytest.mark.parametrize('scope',['metadata','artifact','economic_batch_source_read','decision_context_read','market_hold_context_read'])
def test_current_read_scopes_are_required(login_scope,scope):
    values,query=ready(login_scope);jobs,source,holds,contexts,p,s,authority,service,job,worker=values
    p['scopes'].remove(scope)
    with pytest.raises(PermissionError):query.read('tenant-1',str(job['job_id']))


@pytest.mark.parametrize('login_scope',[PROFILE],indirect=True)
def test_foreign_tenant_is_not_returned(login_scope):
    values,query=ready(login_scope);jobs,source,holds,contexts,p,s,authority,service,job,worker=values
    with pytest.raises(PermissionError):query.read('foreign',str(job['job_id']))
    p['tenant_id']='foreign'
    assert query.read('foreign',str(job['job_id']))is None


@pytest.mark.parametrize('login_scope',[PROFILE],indirect=True)
def test_late_source_scope_revocation_blocks_return(login_scope,monkeypatch):
    values,query=ready(login_scope);jobs,source,holds,contexts,p,s,authority,service,job,worker=values
    prepare=EconomicBatchCalculationService._prepare
    def revoked(*a,**k):
        result=prepare(*a,**k);p['scopes'].remove('economic_batch_source_read');return result
    monkeypatch.setattr(EconomicBatchCalculationService,'_prepare',revoked)
    with pytest.raises(PermissionError):query.read('tenant-1',str(job['job_id']))


def test_codec_preserves_null_and_inventory_without_amount_arithmetic():
    s=scenario();base=ProductionBatchLedger(Repository(s)).calculate(s)
    ledger=replace(base.ledger,closing_inventory={('codec-batch','A','direct'):Decimal('1E-9')},
        operating_cash=None,minimum_cash_balance=None)
    result=replace(base,ledger=ledger)
    parsed=decode_stored_batch_result(result_bytes(result))
    assert result_bytes(parsed)==result_bytes(result)and parsed.ledger.operating_cash is None
    assert parsed.ledger.closing_inventory=={('codec-batch','A','direct'):Decimal('1E-9')}


def test_codec_rejects_a_result_timestamp_without_timezone():
    s=scenario();base=ProductionBatchLedger(Repository(s)).calculate(s)
    result=replace(base,ledger=replace(base.ledger,minimum_cash_at=datetime(2026,10,1)))
    with pytest.raises(BatchResultHold):decode_stored_batch_result(result_bytes(result))


@pytest.mark.parametrize('bad',['extra','nonfinite','numeric','gate','model','duplicate_inventory'])
def test_codec_rejects_malformed_or_promoted_results(bad):
    s=scenario();base=ProductionBatchLedger(Repository(s)).calculate(s)
    value=json.loads(result_bytes(base))
    if bad=='extra':value['ledger']['unexpected']='field'
    elif bad=='nonfinite':value['ledger']['variable_cost']='NaN'
    elif bad=='numeric':value['ledger']['variable_cost']=20
    elif bad=='gate':value['G0_G4']='pass'
    elif bad=='model':value['code_sha256']='f'*64
    else:
        entry={'batch_id':'codec-batch','grade':'A','channel':'direct','quantity_kg':'1'}
        value['ledger']['closing_inventory']=[entry,entry]
    raw=json.dumps(value,sort_keys=True,separators=(',',':'),allow_nan=False).encode()
    with pytest.raises(BatchResultHold):decode_stored_batch_result(raw)


@pytest.mark.parametrize('login_scope',[PROFILE],indirect=True)
def test_independent_process_reads_actual_original_without_execution_or_arithmetic(login_scope,tmp_path):
    values,query=ready(login_scope);jobs,source,holds,contexts,p,s,authority,service,job,worker=values
    expected=jobs.read_artifact('tenant-1',job['job_id'])
    report=holds.get_market_hold_report(s.market_context.hold_report_id)
    scope=holds._scope_resolver('tenant-1',report['snapshot_id'],report['decision_context_id'])
    output=tmp_path/'independent-result-v1.json';config=tmp_path/'independent-reader.private.json'
    config.write_text(json.dumps({'dsn':jobs._dsn,'policy':asdict(jobs.runtime_identity[0]),
        'artifact_root':str(jobs.artifact_root),'scope':scope,'job_id':str(job['job_id']),'output':str(output)}))
    config.chmod(0o600)
    try:
        process=subprocess.run([sys.executable,'-B',str(Path(__file__).with_name('economic_batch_query_reader.py')),str(config)],
            capture_output=True,text=True,timeout=30)
        assert process.returncode==0,process.stderr
        proof=json.loads(process.stdout)
        assert output.read_bytes()==expected and proof['artifact_sha256']==sha256(expected).hexdigest()
        assert proof['amount_calls']==proof['SQL_writes']==0
        (tmp_path/'independent-receipt-v1.json').write_text(json.dumps(proof,indent=2)+'\n')
    finally:config.unlink(missing_ok=True)


@pytest.mark.parametrize('login_scope',[PROFILE],indirect=True)
@pytest.mark.parametrize('bad',['missing','corrupt','late_corrupt'])
def test_physical_artifact_loss_and_corruption_block_return(login_scope,monkeypatch,bad):
    values,query=ready(login_scope);jobs,source,holds,contexts,p,s,authority,service,job,worker=values
    publication=jobs.get_publication('tenant-1',job['job_id']);paths=list(jobs.artifact_root.rglob(publication['artifact_sha256']));assert len(paths)==1
    path=paths[0];original=path.read_bytes();mode=path.stat().st_mode&0o777;backup=path.with_name(path.name+'.own-backup')
    def corrupt():path.chmod(0o600);path.write_bytes(original+b' ')
    if bad=='missing':path.rename(backup)
    elif bad=='corrupt':corrupt()
    else:
        prepare=EconomicBatchCalculationService._prepare
        def later(*a,**k):value=prepare(*a,**k);corrupt();return value
        monkeypatch.setattr(EconomicBatchCalculationService,'_prepare',later)
    try:
        with pytest.raises(BatchResultHold):query.read('tenant-1',str(job['job_id']))
    finally:
        if backup.exists():backup.rename(path)
        path.chmod(0o600);path.write_bytes(original);path.chmod(mode)


@pytest.mark.parametrize('login_scope',[PROFILE],indirect=True)
@pytest.mark.parametrize('bad',['size','manifest_boolean','attempt','input_hash'])
def test_metadata_faults_are_rejected_before_file_read(login_scope,monkeypatch,bad):
    values,query=ready(login_scope);jobs,source,holds,contexts,p,s,authority,service,job,worker=values
    execute=Connection.execute
    def measured(conn,statement,*a,**k):
        cursor=execute(conn,statement,*a,**k)
        text=statement if type(statement)is str else statement.as_string(conn)
        target='jobs'if bad=='input_hash'else'job_publications'
        if not text.startswith('SELECT * FROM ')or'."'+target+'"'not in text:return cursor
        class Fault:
            def fetchone(self):
                value=cursor.fetchone()
                if value is not None:
                    value=dict(value)
                    if bad=='size':value['artifact_size']=MAX_ARTIFACT_BYTES+1
                    elif bad=='manifest_boolean':value['manifest']={**value['manifest'],'attempt':True}
                    elif bad=='attempt':value['attempt']+=1
                    else:value['input_sha256']='f'*64
                return value
        return Fault()
    monkeypatch.setattr(Connection,'execute',measured)
    def fail(*a,**k):raise AssertionError('file read before invalid metadata rejection')
    monkeypatch.setattr(query,'_read_raw',fail)
    with pytest.raises(BatchResultHold):query.read('tenant-1',str(job['job_id']))


@pytest.mark.parametrize('login_scope',[PROFILE],indirect=True)
def test_late_root_rebinding_blocks_original_buffer_return(login_scope,monkeypatch,tmp_path):
    values,query=ready(login_scope);jobs,source,holds,contexts,p,s,authority,service,job,worker=values
    read=query._read_raw
    def changed(*a,**k):value=read(*a,**k);jobs.artifact_root=tmp_path/'another-root';return value
    monkeypatch.setattr(query,'_read_raw',changed)
    with pytest.raises(RuntimeError):query.read('tenant-1',str(job['job_id']))


@pytest.mark.parametrize('login_scope',[PROFILE],indirect=True)
def test_actual_unknown_payment_remains_null_in_saved_result(login_scope):
    values=worker_setup(login_scope);jobs,source,holds,contexts,p,s,authority,service,job,worker=values
    cost=s.variable_costs[0].model_copy(update={'paid_at':None,'payment':None})
    partial=s.model_copy(update={'scenario_revision':'payment-unknown','variable_costs':(cost,)})
    source_job=jobs.submit('tenant-1','collection',partial.model_dump(mode='json'),'partial-source')
    source.adopt_job('tenant-1','economic_scenario',str(source_job['job_id']))
    selected=service.submit('tenant-1',request(partial,'partial-result'))
    assert worker.run_once(str(selected['job_id'])).state=='succeeded'
    p['scopes'].remove('simulation_execute')
    found=EconomicBatchResultQuery(authority).read('tenant-1',str(selected['job_id']))
    assert found.raw==jobs.read_artifact('tenant-1',selected['job_id'])
    assert found.result.ledger.operating_cash is None
    assert found.result.batch_costs[0].cash_paid_in_period is None
    assert found.result.ledger.assessment_status=='hold'and found.result.ledger.hold_reasons


@pytest.mark.parametrize('login_scope',[PROFILE],indirect=True)
def test_late_publication_snapshot_change_blocks_return(login_scope,monkeypatch):
    values,query=ready(login_scope);jobs,source,holds,contexts,p,s,authority,service,job,worker=values
    metadata=query._metadata;calls=[]
    def changed(*a,**k):
        value=metadata(*a,**k);calls.append(1)
        if value is not None and len(calls)>1:
            job_row,raw,selected,publication=value
            return job_row,raw,selected,{**publication,'published_at':publication['published_at']+timedelta(seconds=1)}
        return value
    monkeypatch.setattr(query,'_metadata',changed)
    with pytest.raises(BatchResultHold):query.read('tenant-1',str(job['job_id']))


@pytest.mark.parametrize('login_scope',[PROFILE],indirect=True)
def test_changed_authoritative_market_scope_rejects_the_stored_signed_context(login_scope):
    values,query=ready(login_scope);jobs,source,holds,contexts,p,s,authority,service,job,worker=values
    current=query.authority;old=current._holds
    report=old.get_market_hold_report(s.market_context.hold_report_id)
    scope=old._scope_resolver('tenant-1',report['snapshot_id'],report['decision_context_id'])
    class Resolver:
        def __init__(self):self.scope=dict(scope)
        def __call__(self,*_):return dict(self.scope)
    resolver=Resolver()
    changed=MarketHoldStore(old.dsn,old.schema,context_store=old._context_store,
        scope_resolver=resolver,principal_provider=jobs.principal_provider,
        signing_key=old._key,runtime_identity=jobs.runtime_identity)
    reader=EconomicBatchResultQuery(EconomicBatchAuthority(jobs,current._source,changed))
    resolver.scope['scope_version']='changed-current-scope'
    with pytest.raises(BatchResultHold):reader.read('tenant-1',str(job['job_id']))
