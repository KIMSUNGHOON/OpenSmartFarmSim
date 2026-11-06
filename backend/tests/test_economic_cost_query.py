"""Stored conditional cost traces over owned SCRAM; reads never replay money."""
from copy import copy
from dataclasses import asdict,replace
from datetime import datetime,timezone,timedelta
from decimal import Decimal,localcontext
from hashlib import sha256
import json
from pathlib import Path
import subprocess
import sys

import pytest
from psycopg import Connection

from app import economic_cost_trace as trace
from app.economic_cost_query import EconomicCostResultQuery,CostResultHold,decode_stored_cost_result
from app.economic_batch_calculation import EconomicBatchAuthority
from app.economic_cost_calculation import EconomicCostCalculationService
from app.economic_batch_source_store import EconomicBatchSourceStore
from app.economic_batch_worker import EconomicBatchWorker,MAX_ARTIFACT_BYTES
from app.economic_production_batches import ProductionBatchLedger,result_bytes
from app.economics import EconomicLedger
from app.market_hold_store import MarketHoldStore
from app.thermal_run_store import ThermalRunStore
from login_database import login_database,login_scope
from test_economic_batch_calculation import PROFILE,request
from test_economic_cost_worker import setup as worker_setup
from test_economic_production_batches import scenario,Repository


def raw(value):
    return json.dumps(value,sort_keys=True,separators=(',',':'),allow_nan=False).encode()


def ready(scope):
    values=worker_setup(scope)
    jobs,source,holds,contexts,p,s,authority,service,base,job,worker=values
    assert worker.run_once(str(job['job_id'])).state=='succeeded'
    provider=jobs.principal_provider;binding=jobs.runtime_identity
    fresh_source=EconomicBatchSourceStore(source.dsn,source.schema,principal_provider=provider,runtime_identity=binding)
    fresh_context=ThermalRunStore(contexts.dsn,contexts.schema,gate_key=contexts._gate_key,
        release_verifier=contexts._release_verifier,context_verifier=contexts._context_verifier,
        principal_provider=provider,runtime_identity=binding)
    fresh_holds=MarketHoldStore(holds.dsn,holds.schema,context_store=fresh_context,
        scope_resolver=holds._scope_resolver,principal_provider=provider,
        signing_key=holds._key,runtime_identity=binding)
    fresh=EconomicBatchAuthority(jobs,fresh_source,fresh_holds)
    p['scopes'].remove('simulation_execute')
    return values,EconomicCostResultQuery(fresh)


def no_replay(monkeypatch):
    from app import economic_batch_worker,thermal_publisher
    def fail(*a,**k):raise AssertionError('arithmetic, execution or current runtime digest in stored cost reader')
    for cls,name in ((trace.CostLineLedger,'calculate'),(ProductionBatchLedger,'calculate'),
            (EconomicLedger,'calculate'),(EconomicLedger,'_calculate_verified'),
            (EconomicBatchWorker,'run_once'),(EconomicBatchWorker,'_digests')):
        monkeypatch.setattr(cls,name,fail)
    monkeypatch.setattr(economic_batch_worker,'runtime_digests',fail)
    monkeypatch.setattr(thermal_publisher,'runtime_digests',fail)
    for name in ('_line','_groups','_months','_reconcile'):
        monkeypatch.setattr(trace,name,fail)


def reidentify(value):
    value['trace_id']=sha256(raw({key:item for key,item in value.items()if key!='trace_id'})).hexdigest()
    return value


def saved_view(query,monkeypatch,artifact):
    """Inject internally consistent saved bytes; current source checks still use real SCRAM."""
    encoded=raw(artifact);digest=sha256(encoded).hexdigest();metadata=query._metadata
    def changed(*a,**k):
        value=metadata(*a,**k)
        if value is None:return None
        job,raw_input,selected,publication=value
        publication={**publication,'artifact_sha256':digest,'artifact_size':len(encoded),
            'manifest':{**publication['manifest'],'artifact_sha256':digest}}
        return job,raw_input,selected,publication
    monkeypatch.setattr(query,'_metadata',changed)
    monkeypatch.setattr(query,'_read_raw',lambda *_:encoded)
    return encoded


@pytest.mark.parametrize('login_scope',[PROFILE],indirect=True)
def test_fresh_cost_reader_preserves_full_raw_first_publication_without_replay_or_writes(login_scope,monkeypatch,tmp_path):
    values,query=ready(login_scope)
    jobs,source,holds,contexts,p,s,authority,service,base,job,worker=values
    expected=jobs.read_artifact('tenant-1',job['job_id']);publication=jobs.get_publication('tenant-1',job['job_id'])
    envelope=json.loads(expected);no_replay(monkeypatch);writes=[];execute=Connection.execute
    def measured(conn,*a,**k):
        cursor=execute(conn,*a,**k);tag=(cursor.statusmessage or '').split(' ')[0]
        if tag in {'INSERT','UPDATE','DELETE','MERGE','CREATE','ALTER','DROP','TRUNCATE','GRANT','REVOKE'}:writes.append(tag)
        return cursor
    monkeypatch.setattr(Connection,'execute',measured)
    found=query.read('tenant-1',str(job['job_id']))
    assert found.raw==expected==raw(envelope)and found.published_at==publication['published_at']
    assert found.publication_id==publication['publication_id']and not writes
    assert trace.trace_bytes(found.result)==raw(envelope['result'])
    assert result_bytes(found.result.base_result)==raw(envelope['result']['base_result'])
    assert sha256(trace.trace_bytes(found.result)).hexdigest()==envelope['result_sha256']
    assert found.result.trace_id==envelope['result']['trace_id']
    assert found.result.lines[0].cost==s.variable_costs[0]
    assert found.result.lines[0].incurred==found.result.groups[0].incurred==Decimal('20')
    assert found.result.base_result.ledger.variable_cost==Decimal('20')
    assert found.result.G0_G4=='not_assessed'and found.result.R2=='not_approved'
    found.result.component_sha256['forged']='x'
    found.result.base_result.component_sha256['forged']='x'
    again=query.read('tenant-1',str(job['job_id']))
    assert again.raw==expected and 'forged'not in again.result.component_sha256
    assert 'forged'not in again.result.base_result.component_sha256 and not writes
    assert jobs.get_publication('tenant-1',job['job_id'])==publication
    proof={'observed_at_UTC':datetime.now(timezone.utc).isoformat(),'job_id':str(job['job_id']),
        'artifact_sha256':sha256(expected).hexdigest(),'artifact_bytes':len(expected),
        'publication_id':str(again.publication_id),'published_at':again.published_at.isoformat(),
        'trace_id':again.result.trace_id,'result_sha256':envelope['result_sha256'],
        'same_raw_after_retry':True,'independent_return_values':True,'execution_scope_present':False,
        'amount_arithmetic_calls':0,'SQL_write_commands':len(writes),'scope':'owned_synthetic_QA_only',
        'G0_G4':'not_assessed','R2':'not_approved'}
    (tmp_path/'cost-queried-result-v1.json').write_bytes(again.raw)
    (tmp_path/'cost-query-receipt-v1.json').write_text(json.dumps(proof,indent=2)+'\n')


@pytest.mark.parametrize('login_scope',[PROFILE],indirect=True)
def test_unknown_pending_and_completed_old_family_do_not_read_cost_artifact(login_scope,monkeypatch):
    values=worker_setup(login_scope)
    jobs,source,holds,contexts,p,s,authority,service,base,job,worker=values
    old=base.submit('tenant-1',request(s))
    assert EconomicBatchWorker(authority,tenant_id='tenant-1').run_once(str(old['job_id'])).state=='succeeded'
    query=EconomicCostResultQuery(authority);p['scopes'].remove('simulation_execute')
    def fail(*a,**k):raise AssertionError('file read for missing, pending or different-family cost result')
    monkeypatch.setattr(query,'_read_raw',fail)
    for job_id in ('00000000-0000-0000-0000-000000000000',str(job['job_id']),str(old['job_id'])):
        assert query.read('tenant-1',job_id)is None


@pytest.mark.parametrize('login_scope',[PROFILE],indirect=True)
@pytest.mark.parametrize('scope',['metadata','artifact','economic_batch_source_read','decision_context_read','market_hold_context_read'])
def test_every_current_read_scope_is_required(login_scope,scope):
    values,query=ready(login_scope)
    jobs,source,holds,contexts,p,s,authority,service,base,job,worker=values
    p['scopes'].remove(scope)
    with pytest.raises(PermissionError):query.read('tenant-1',str(job['job_id']))


@pytest.mark.parametrize('login_scope',[PROFILE],indirect=True)
def test_foreign_tenant_never_receives_cost_result(login_scope):
    values,query=ready(login_scope)
    jobs,source,holds,contexts,p,s,authority,service,base,job,worker=values
    with pytest.raises(PermissionError):query.read('foreign',str(job['job_id']))
    p['tenant_id']='foreign'
    assert query.read('foreign',str(job['job_id']))is None


@pytest.mark.parametrize('login_scope',[PROFILE],indirect=True)
def test_late_read_scope_revocations_block_original_buffer_return(login_scope,monkeypatch):
    values,query=ready(login_scope)
    jobs,source,holds,contexts,p,s,authority,service,base,job,worker=values
    prepare=EconomicCostCalculationService._prepare
    for scope in ('metadata','artifact','economic_batch_source_read','decision_context_read','market_hold_context_read'):
        def revoked(*a,**k):
            result=prepare(*a,**k);p['scopes'].remove(scope);return result
        try:
            with monkeypatch.context()as patch:
                patch.setattr(EconomicCostCalculationService,'_prepare',revoked)
                with pytest.raises(PermissionError):query.read('tenant-1',str(job['job_id']))
        finally:p['scopes'].add(scope)


def test_codec_preserves_null_decimal_and_tuple_inventory_without_arithmetic(monkeypatch):
    s=scenario();result=trace.CostLineLedger(Repository(s)).calculate(s)
    ledger=replace(result.base_result.ledger,
        closing_inventory={('codec-batch','A','direct'):Decimal('1E-9')},
        operating_cash=None,minimum_cash_balance=None)
    result=replace(result,base_result=replace(result.base_result,ledger=ledger))
    value=reidentify(json.loads(trace.trace_bytes(result)));encoded=raw(value);no_replay(monkeypatch)
    parsed=decode_stored_cost_result(encoded)
    assert trace.trace_bytes(parsed)==encoded and parsed.base_result.ledger.operating_cash is None
    assert parsed.base_result.ledger.closing_inventory=={('codec-batch','A','direct'):Decimal('1E-9')}
    assert parsed.lines[0].incurred==Decimal('20')


@pytest.mark.parametrize('bad',['extra','nonfinite','numeric','gate','version','code','component','trace_id','base_code'])
def test_codec_rejects_malformed_or_promoted_cost_results_without_arithmetic(monkeypatch,bad):
    s=scenario();value=json.loads(trace.trace_bytes(trace.CostLineLedger(Repository(s)).calculate(s)))
    if bad=='extra':value['lines'][0]['unexpected']='field'
    elif bad=='nonfinite':value['lines'][0]['incurred']='NaN'
    elif bad=='numeric':value['lines'][0]['incurred']=20
    elif bad=='gate':value['G0_G4']='pass'
    elif bad=='version':value['trace_version']='unsupported'
    elif bad=='code':value['code_sha256']='f'*64
    elif bad=='component':value['component_sha256']={'invented':'f'*64}
    elif bad=='trace_id':value['trace_id']='f'*64
    else:value['base_result']['code_sha256']='f'*64
    if bad!='trace_id':reidentify(value)
    no_replay(monkeypatch)
    with pytest.raises(CostResultHold):decode_stored_cost_result(raw(value))


def test_codec_rejects_unzoned_nested_result_timestamp():
    s=scenario();value=json.loads(trace.trace_bytes(trace.CostLineLedger(Repository(s)).calculate(s)))
    value['base_result']['ledger']['minimum_cash_at']='2026-10-01T00:00:00'
    with pytest.raises(CostResultHold):decode_stored_cost_result(raw(reidentify(value)))


def test_codec_rejects_oversized_complete_result_without_truncation():
    with pytest.raises(CostResultHold):decode_stored_cost_result(b' '*(MAX_ARTIFACT_BYTES+1))


@pytest.mark.parametrize('login_scope',[PROFILE],indirect=True)
def test_independent_process_reads_actual_cost_result_without_execute_or_replay(login_scope,tmp_path):
    values,query=ready(login_scope)
    jobs,source,holds,contexts,p,s,authority,service,base,job,worker=values
    expected=jobs.read_artifact('tenant-1',job['job_id'])
    report=holds.get_market_hold_report(s.market_context.hold_report_id)
    scope=holds._scope_resolver('tenant-1',report['snapshot_id'],report['decision_context_id'])
    output=tmp_path/'independent-cost-result-v1.json';config=tmp_path/'independent-cost-reader.private.json'
    with config.open('x')as handle:
        config.chmod(0o600)
        json.dump({'dsn':jobs._dsn,'policy':asdict(jobs.runtime_identity[0]),
            'artifact_root':str(jobs.artifact_root),'scope':scope,'job_id':str(job['job_id']),
            'output':str(output)},handle)
    try:
        process=subprocess.run([sys.executable,'-B',str(Path(__file__).with_name('economic_cost_query_reader.py')),str(config)],
            capture_output=True,text=True,timeout=30)
        assert process.returncode==0,'independent cost reader failed; private diagnostics withheld'
        proof=json.loads(process.stdout)
        assert output.read_bytes()==expected and proof['artifact_sha256']==sha256(expected).hexdigest()
        assert proof['amount_calls']==proof['SQL_writes']==proof['runtime_digest_calls']==0
        assert proof['execution_scope_present']is False
        (tmp_path/'independent-cost-receipt-v1.json').write_text(json.dumps(proof,indent=2)+'\n')
    finally:config.unlink(missing_ok=True)


@pytest.mark.parametrize('login_scope',[PROFILE],indirect=True)
@pytest.mark.parametrize('bad',['missing','late_corrupt'])
def test_physical_artifact_loss_and_late_corruption_block_cost_return(login_scope,monkeypatch,bad):
    values,query=ready(login_scope)
    jobs,source,holds,contexts,p,s,authority,service,base,job,worker=values
    publication=jobs.get_publication('tenant-1',job['job_id'])
    paths=list(jobs.artifact_root.rglob(publication['artifact_sha256']));assert len(paths)==1
    path=paths[0];original=path.read_bytes();mode=path.stat().st_mode&0o777;backup=path.with_name(path.name+'.own-backup')
    def corrupt():path.chmod(0o600);path.write_bytes(original+b' ')
    if bad=='missing':path.rename(backup)
    else:
        prepare=EconomicCostCalculationService._prepare
        def changed(*a,**k):value=prepare(*a,**k);corrupt();return value
        monkeypatch.setattr(EconomicCostCalculationService,'_prepare',changed)
    try:
        with pytest.raises(CostResultHold):query.read('tenant-1',str(job['job_id']))
    finally:
        if backup.exists():backup.rename(path)
        path.chmod(0o600);path.write_bytes(original);path.chmod(mode)


@pytest.mark.parametrize('login_scope',[PROFILE],indirect=True)
@pytest.mark.parametrize('bad',['size','manifest_boolean'])
def test_metadata_faults_are_rejected_before_cost_file_read(login_scope,monkeypatch,bad):
    values,query=ready(login_scope)
    jobs,source,holds,contexts,p,s,authority,service,base,job,worker=values
    execute=Connection.execute
    def measured(conn,statement,*a,**k):
        cursor=execute(conn,statement,*a,**k)
        text=statement if type(statement)is str else statement.as_string(conn)
        if not text.startswith('SELECT * FROM ')or'."job_publications"'not in text:return cursor
        class Fault:
            def fetchone(self):
                value=cursor.fetchone()
                if value is not None:
                    value=dict(value)
                    if bad=='size':value['artifact_size']=MAX_ARTIFACT_BYTES+1
                    else:value['manifest']={**value['manifest'],'attempt':True}
                return value
        return Fault()
    monkeypatch.setattr(Connection,'execute',measured)
    def fail(*a,**k):raise AssertionError('file read before invalid cost metadata rejected')
    monkeypatch.setattr(query,'_read_raw',fail)
    with pytest.raises(CostResultHold):query.read('tenant-1',str(job['job_id']))


@pytest.mark.parametrize('login_scope',[PROFILE],indirect=True)
@pytest.mark.parametrize('part',['root','authority'])
def test_late_reader_binding_changes_block_original_cost_buffer(login_scope,monkeypatch,tmp_path,part):
    values,query=ready(login_scope)
    jobs,source,holds,contexts,p,s,authority,service,base,job,worker=values
    read=query._read_raw
    def changed(*a,**k):
        value=read(*a,**k)
        if part=='root':jobs.artifact_root=tmp_path/'another-root'
        else:query.authority=copy(query.authority)
        return value
    monkeypatch.setattr(query,'_read_raw',changed)
    with pytest.raises(RuntimeError):query.read('tenant-1',str(job['job_id']))


@pytest.mark.parametrize('login_scope',[PROFILE],indirect=True)
def test_actual_unknown_cost_payment_stays_null_in_stored_trace(login_scope):
    values=worker_setup(login_scope)
    jobs,source,holds,contexts,p,s,authority,service,base,job,worker=values
    cost=s.variable_costs[0].model_copy(update={'paid_at':None,'payment':None})
    partial=s.model_copy(update={'scenario_revision':'payment-unknown','variable_costs':(cost,)})
    source_job=jobs.submit('tenant-1','collection',partial.model_dump(mode='json'),'partial-cost-source')
    source.adopt_job('tenant-1','economic_scenario',str(source_job['job_id']))
    selected=service.submit('tenant-1',request(partial,'partial-cost-result'))
    assert worker.run_once(str(selected['job_id'])).state=='succeeded'
    p['scopes'].remove('simulation_execute')
    found=EconomicCostResultQuery(authority).read('tenant-1',str(selected['job_id']))
    assert found.raw==jobs.read_artifact('tenant-1',selected['job_id'])
    assert found.result.lines[0].bank_paid_in_period is None
    assert found.result.lines[0].remaining_payable_at_period_end is None
    assert found.result.groups[0].bank_paid_in_period is None
    assert found.result.base_result.ledger.operating_cash is None
    assert found.result.ledger_payable_reconciliation=='unavailable'


@pytest.mark.parametrize('login_scope',[PROFILE],indirect=True)
def test_late_publication_snapshot_change_blocks_cost_return(login_scope,monkeypatch):
    values,query=ready(login_scope)
    jobs,source,holds,contexts,p,s,authority,service,base,job,worker=values
    metadata=query._metadata;calls=[]
    def changed(*a,**k):
        value=metadata(*a,**k);calls.append(1)
        if value is not None and len(calls)>1:
            job_row,raw_input,selected,publication=value
            return job_row,raw_input,selected,{**publication,'published_at':publication['published_at']+timedelta(seconds=1)}
        return value
    monkeypatch.setattr(query,'_metadata',changed)
    with pytest.raises(CostResultHold):query.read('tenant-1',str(job['job_id']))


@pytest.mark.parametrize('login_scope',[PROFILE],indirect=True)
@pytest.mark.parametrize('part',['source','context','code'])
def test_late_current_source_context_or_code_change_blocks_cost_return(login_scope,monkeypatch,part):
    values,query=ready(login_scope)
    jobs,source,holds,contexts,p,s,authority,service,base,job,worker=values
    prepare=EconomicCostCalculationService._prepare
    def changed(*a,**k):
        value=prepare(*a,**k)
        if part=='source':
            selected=query.authority._source;pin=selected.get_economic_scenario_pin
            monkeypatch.setattr(selected,'get_economic_scenario_pin',lambda *args:{**pin(*args),'payload_sha256':'f'*64})
        elif part=='context':query.authority._holds._context_store=copy(query.authority._holds._context_store)
        else:monkeypatch.setattr(trace,'CODE_SHA256','f'*64)
        return value
    monkeypatch.setattr(EconomicCostCalculationService,'_prepare',changed)
    with pytest.raises((CostResultHold,RuntimeError)):query.read('tenant-1',str(job['job_id']))


@pytest.mark.parametrize('login_scope',[PROFILE],indirect=True)
def test_rehashed_saved_cost_identity_still_requires_original_Cost_id_and_category_binding(login_scope,monkeypatch):
    values,query=ready(login_scope)
    jobs,source,holds,contexts,p,s,authority,service,base,job,worker=values
    original=jobs.read_artifact('tenant-1',job['job_id']);no_replay(monkeypatch)
    for bad in ('cost_id','category','duplicate'):
        value=json.loads(original);line=value['result']['lines'][0]
        if bad=='cost_id':line['cost']['id']='unregistered-cost'
        elif bad=='category':line['category']='fixed'
        else:value['result']['lines'].append(dict(line))
        reidentify(value['result']);value['result_sha256']=sha256(raw(value['result'])).hexdigest()
        with monkeypatch.context()as patch:
            saved_view(query,patch,value)
            with pytest.raises(CostResultHold):query.read('tenant-1',str(job['job_id']))


@pytest.mark.parametrize('login_scope',[PROFILE],indirect=True)
def test_historical_outer_code_environment_digests_are_preserved_without_current_runtime_comparison(login_scope,monkeypatch):
    values,query=ready(login_scope)
    jobs,source,holds,contexts,p,s,authority,service,base,job,worker=values
    value=json.loads(jobs.read_artifact('tenant-1',job['job_id']))
    value['code_sha256']='a'*64;value['environment_sha256']='b'*64
    expected=saved_view(query,monkeypatch,value);no_replay(monkeypatch)
    found=query.read('tenant-1',str(job['job_id']))
    assert found.raw==expected and json.loads(found.raw)['environment_sha256']=='b'*64
    assert found.result.code_sha256==trace.CODE_SHA256


@pytest.mark.parametrize('login_scope',[PROFILE],indirect=True)
def test_late_instance_decoder_and_live_hold_stored_selectors_reject_without_replacement_calls(login_scope,monkeypatch):
    values,query=ready(login_scope)
    jobs,source,holds,contexts,p,s,authority,service,base,job,worker=values
    read=query._read_raw;replacement_calls=[];no_replay(monkeypatch)
    def changed(*a,**k):
        original=read(*a,**k)
        monkeypatch.setattr(query,'_decode',lambda *_:replacement_calls.append('decode'))
        monkeypatch.setattr(query,'_hold_type',lambda *_:replacement_calls.append('hold')or CostResultHold('forged'))
        monkeypatch.setattr(query,'_stored_type',lambda *_:replacement_calls.append('stored'))
        return original
    monkeypatch.setattr(query,'_read_raw',changed)
    with pytest.raises(RuntimeError):query.read('tenant-1',str(job['job_id']))
    assert replacement_calls==[]


def test_codec_isolates_nested_amount_serialization_from_caller_decimal_capitals(monkeypatch):
    s=scenario();value=s.model_dump();cost=value['variable_costs'][0]
    cost['quantity']['value']='0.000000001';cost['payment']['value']='0.000000002'
    s=type(s).model_validate(value)
    original=trace.CostLineLedger(Repository(s)).calculate(s);encoded=trace.trace_bytes(original)
    assert b'"variable_cost":"2E-9"'in encoded
    no_replay(monkeypatch)
    with localcontext()as ctx:
        ctx.capitals=0
        parsed=decode_stored_cost_result(encoded)
        assert ctx.capitals==0
        assert trace.trace_bytes(parsed)==encoded
        assert parsed.base_result.ledger.variable_cost==original.base_result.ledger.variable_cost
