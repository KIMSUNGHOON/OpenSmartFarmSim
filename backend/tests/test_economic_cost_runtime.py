"""Owned conditional cost runtime rebuild over synthetic assumptions only."""
from datetime import datetime,timezone
from hashlib import sha256
import json

import pytest
from psycopg import Connection

from app.api_runtime import ApiRuntime
from app.economic_batch_calculation import EconomicBatchAuthority
from app.economic_cost_wire import CostArtifactRead
from app.economic_cost_worker import EconomicCostWorker
from app import economic_cost_trace as trace
from app.economic_production_batches import ProductionBatchLedger
from app.http_identity import current_principal
from login_database import login_database,login_scope
from test_api_serve import tls_files
from test_economic_batch_calculation import request
from test_economic_batch_runtime import runtime_inputs,RUNTIME_PROFILE,READ_TOKEN,https
from test_economic_cost_query import no_replay


@pytest.mark.parametrize('login_scope',[RUNTIME_PROFILE],indirect=True)
def test_cost_runtime_HTTPS_rebuild_preserves_original_publication_without_execution(runtime_inputs,monkeypatch,tmp_path):
    values,cfg,deps,scope=runtime_inputs
    jobs,source,holds,contexts,p,s,authority,service=values
    body=request(s,'cost-runtime-rebuild').model_dump(mode='json')
    writes=[];calls=[];listeners=0
    try:
        first=ApiRuntime(cfg,deps)
        bound=first.economic_batch_authority
        assert type(bound)is EconomicBatchAuthority and bound.jobs is first.jobs
        assert bound._holds is first.market_holds and first.market_holds._context_store is first.thermal
        assert first.jobs.principal_provider is current_principal and bound._source._principal_provider is current_principal
        with https(first,cfg)as call:
            listeners+=1
            with monkeypatch.context()as patch:
                no_replay(patch)
                status,accepted,_=call('/v1/economic-cost-calculations',method='POST',body=body)
                assert status==202
                assert call('/v1/economic-cost-calculations',method='POST',body=body)[:2]==(202,accepted)
                job=json.loads(accepted);path='/v1/jobs/'+job['job_id']+'/economic-cost-result'
                assert call(path,token=READ_TOKEN)[0]==404
            with jobs.connect()as conn:
                queued=jobs._locked_job(conn,'tenant-1',job['job_id']);original_input=jobs._verified_input(queued)
            assert queued['state']=='queued'and queued['attempt_count']==0
            assert jobs.get_publication('tenant-1',job['job_id'])is None
            assert json.loads(original_input)['input_version']=='economic-cost-line-calculation-input-v1'
        assert current_principal()is None
        calculate=trace.CostLineLedger.calculate;calculate_base=ProductionBatchLedger.calculate
        with monkeypatch.context()as patch:
            def counted(*a,**k):calls.append('trace');return calculate(*a,**k)
            def counted_base(*a,**k):calls.append('v10');return calculate_base(*a,**k)
            patch.setattr(trace.CostLineLedger,'calculate',counted)
            patch.setattr(ProductionBatchLedger,'calculate',counted_base)
            outcome=EconomicCostWorker(authority,tenant_id='tenant-1').run_once(job['job_id'])
        assert outcome.state=='succeeded'and calls==['trace','v10']
        expected=jobs.read_artifact('tenant-1',job['job_id']);publication=jobs.get_publication('tenant-1',job['job_id'])
        artifact=json.loads(expected)
        assert artifact['result']['trace_id']==outcome.trace_id
        assert artifact['input_sha256']==queued['input_sha256']==sha256(original_input).hexdigest()
        assert artifact['input']==json.loads(original_input)
        fresh=ApiRuntime(cfg,deps)
        assert fresh.jobs is not first.jobs and fresh.economic_batch_authority is not bound
        assert fresh.economic_batch_authority._source is not bound._source
        assert fresh.market_holds is not first.market_holds and fresh.thermal is not first.thermal
        assert fresh.jobs.principal_provider is current_principal
        no_replay(monkeypatch);execute=Connection.execute
        def measured(conn,*a,**k):
            cursor=execute(conn,*a,**k)
            if(cursor.statusmessage or '').split(' ')[0]in {'INSERT','UPDATE','DELETE','MERGE','CREATE','ALTER','DROP','TRUNCATE','GRANT','REVOKE'}:
                writes.append(cursor.statusmessage)
            return cursor
        monkeypatch.setattr(Connection,'execute',measured)
        with https(fresh,cfg)as call:
            listeners+=1
            status,raw,headers=call(path,token=READ_TOKEN)
            assert status==200 and raw==expected and not writes
            assert headers['cache-control']=='no-store'and headers['strict-transport-security']and'server'not in headers
            assert headers['x-ossf-publication-id']==str(publication['publication_id'])
            assert headers['x-ossf-published-at']==publication['published_at'].isoformat()
            CostArtifactRead.model_validate_json(raw)
            assert call(path,token=None)[0]==401
            assert call('/v1/economic-cost-calculations',method='POST',body=body,token=READ_TOKEN)[0]==403
            scope['changed']=True
            status,held,_=call(path,token=READ_TOKEN)
            assert status==422 and json.loads(held)['error']['code']=='economic_cost_hold'
            scope['changed']=False
            status,restored,restored_headers=call(path,token=READ_TOKEN)
            assert status==200 and restored==expected
            assert restored_headers['x-ossf-publication-id']==headers['x-ossf-publication-id']
            assert restored_headers['x-ossf-published-at']==headers['x-ossf-published-at']
            assert not writes and current_principal()is None
        assert jobs.get_publication('tenant-1',job['job_id'])==publication
        with jobs.connect()as conn:
            final=jobs._locked_job(conn,'tenant-1',job['job_id'])
            assert jobs._verified_input(final)==original_input and final['created_at']==queued['created_at']
        assert not writes and listeners==2 and current_principal()is None
    finally:
        scope['changed']=False
        cfg.certificate.unlink(missing_ok=True);cfg.private_key.unlink(missing_ok=True)
    assert not cfg.certificate.exists()and not cfg.private_key.exists()
    proof={'observed_at_UTC':datetime.now(timezone.utc).isoformat(),'job_id':job['job_id'],
        'input_sha256':queued['input_sha256'],'job_created_at':queued['created_at'].isoformat(),
        'artifact_sha256':sha256(expected).hexdigest(),'artifact_bytes':len(expected),
        'publication_id':str(publication['publication_id']),'published_at':publication['published_at'].isoformat(),
        'trace_id':outcome.trace_id,'source_job_id':artifact['input']['base_input']['scenario_source_job_id'],
        'fresh_runtime_objects':2,'verified_TLS_listeners':listeners,'same_process_rebuild':True,
        'first_listener_stopped_before_explicit_worker':True,'actual_trace_calls':calls.count('trace'),
        'actual_v10_calls':calls.count('v10'),'admission_amount_calls':0,'fresh_result_amount_calls':0,
        'fresh_result_runtime_digest_calls':0,'fresh_result_SQL_writes':len(writes),
        'read_execution_scope':False,'current_evidence_hold_and_restore':True,
        'original_input_and_first_publication_preserved':True,'TLS_fixture_material_removed':True,
        'automatic_consumer':False,'production_changes':0,'actual_farm_Runs':0,
        'G0_G4':'not_assessed','R2':'not_approved'}
    (tmp_path/'cost-runtime-result-v1.json').write_bytes(expected)
    (tmp_path/'cost-runtime-receipt-v1.private.json').write_text(json.dumps(proof,indent=2)+'\n')
