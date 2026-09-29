"""Actual TLS/Bearer/runtime/SCRAM completion; fixture CLI and keys are synthetic."""

from datetime import datetime,timedelta,timezone
import http.client
import json
from pathlib import Path
import ssl
import sys
import threading
import time
from uuid import UUID

import pytest

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from app.api_runtime import ApiRuntime, _MarketSources
from app.calculation_assessment import CalculationAssessmentService
from app.cli_contracts import AuthoritySnapshot
from app.farm_replay_scenario import READ_SCOPES
from app.http_identity import BearerGrant,BearerRegistry,current_principal,token_digest
from app.market_candidate_store import MarketCandidateStore
from app.market_hold_store import MarketHoldStore
from app.market_result_store import MarketResultStore
from app.market_source_store import MarketSourceStore
from app.owned_cli_contracts import OwnedCliContractRouter
from app.owned_collection_review import OwnedCollectionReviewService,OwnedCollectionReviewContract,REVIEW_SCOPES
from app.owned_fixture_collection import CollectionService
from app.owned_research import OwnedResearchService
from app.thermal_publisher import ThermalG1Publisher
from app.thermal_simulation_worker import ThermalSimulationWorker
from app.thermal_run_submission import SUBMISSION_SCOPES
from test_api_runtime import config,dependencies
from test_api_serve import tls_files
from test_farm_thermal_execution import execution,farm_setup,login_scope,login_database
from test_thermal_publisher import GATE_KEY

pytestmark=pytest.mark.parametrize('login_scope',[{'market_calculation':True,
    'market_source_storage':True,'thermal_scenario_storage':True,'break_even_calculation':True}],indirect=True)


def assemble_farm_runtime(farm,publisher,tls_files,grants):
    cert,key,_=tls_files
    jobs=farm.jobs
    registry=farm.owned_research.registry
    contexts={next(iter(farm.registry._scopes)):'context-1'}
    source_factory=lambda *,principal_provider:MarketSourceStore(jobs._dsn,jobs.schema,
        principal_provider=principal_provider,runtime_identity=jobs.runtime_identity)
    def publisher_factory(*,run_store,job_store):
        source=source_factory(principal_provider=current_principal)
        holds=MarketHoldStore(jobs._dsn,jobs.schema,context_store=run_store,
            scope_resolver=farm.thermal.holds._scope_resolver,signing_key=farm.thermal.holds._key,
            principal_provider=current_principal,runtime_identity=jobs.runtime_identity)
        candidates=MarketCandidateStore(jobs._dsn,jobs.schema,_MarketSources(source,holds),
            principal_provider=current_principal,runtime_identity=jobs.runtime_identity)
        results=MarketResultStore(jobs._dsn,jobs.schema,candidates,
            principal_provider=current_principal,runtime_identity=jobs.runtime_identity)
        research=OwnedResearchService(job_store,run_store,farm.registry,registry,contexts)
        review=OwnedCollectionReviewService(CollectionService(job_store,registry),run_store)
        assessment=CalculationAssessmentService(job_store,run_store,results)
        def authority(job,body):
            return AuthoritySnapshot(job['tenant_id'],'collection_review',job['input_sha256'],
                frozenset({body['snapshot_id']}),{},True,(),{},frozenset(),False,
                {field:body[field] for field in OwnedCollectionReviewContract.BINDING_FIELDS},
                **{field:body[field] for field in ('decision_context_id','decision_at_utc','claim_mode','decision_time_kind')})
        job_store.evidence_policy=jobs.evidence_policy
        job_store.decision_validator=OwnedCliContractRouter(research,review,assessment,authority)
        return ThermalG1Publisher(run_store,job_store,publisher.release_resolver,root=publisher.root,
            gate_key=GATE_KEY,release_verifier=publisher.release_verifier,
            execution_verifier=publisher.execution_verifier,collection_review_service=review)
    return ApiRuntime(config(policy=jobs.runtime_identity[0],dsn=jobs._dsn,artifact_root=jobs.artifact_root,
        certificate=cert,private_key=key,port=0,thermal_gate_key=GATE_KEY,
        market_hold_key=farm.thermal.holds._key),dependencies(research_registry=farm.registry,
        bearer_registry=BearerRegistry(grants),context_verifier=farm.thermal.runs._context_verifier,
        release_verifier=publisher.release_verifier,market_scope_resolver=farm.thermal.holds._scope_resolver,
        market_source_factory=source_factory,thermal_publisher_factory=publisher_factory,
        owned_fixture_registry=registry,owned_research_contexts=contexts))


def test_actual_runtime_admits_farm_job_and_reads_atomic_completion(execution,tls_files):
    farm,publisher,_,_,value,principal,*_=execution
    cert,key,_=tls_files
    now=datetime.now(timezone.utc)
    token=b'synthetic-farm-run-'+b'f'*32
    reader=b'synthetic-farm-run-reader-'+b'r'*32
    other=b'synthetic-farm-run-other-'+b'o'*32
    submit_scopes=set(SUBMISSION_SCOPES+READ_SCOPES+REVIEW_SCOPES+('thermal_run_read',))
    grants=tuple(BearerGrant(token_digest(raw),tenant,frozenset(scopes),
        now-timedelta(seconds=1),now+timedelta(minutes=20)) for raw,tenant,scopes in (
            (token,'tenant-1',submit_scopes),
            (reader,'tenant-1',(*READ_SCOPES,'thermal_run_read')),
            (other,'tenant-other',submit_scopes)))
    runtime=assemble_farm_runtime(farm,publisher,tls_files,grants)
    assert runtime.farm_scenarios.owned_research is runtime.research
    server=runtime.service.server()
    thread=threading.Thread(target=server.run,daemon=True);thread.start()
    timings=[]
    try:
        deadline=time.monotonic()+10
        while not server.started:
            assert thread.is_alive() and time.monotonic()<deadline
            time.sleep(0.01)
        port=server.servers[0].sockets[0].getsockname()[1]
        context=ssl.create_default_context(cafile=str(cert))
        def call(path,*,payload=None,bearer=token):
            conn=http.client.HTTPSConnection('127.0.0.1',port,timeout=30,context=context)
            started=time.monotonic()
            try:
                headers={'Content-Type':'application/json','X-Tenant-Id':'foreign'}
                if bearer is not None:headers['Authorization']='Bearer '+bearer.decode()
                conn.request('POST' if payload is not None else 'GET',path,
                    json.dumps(payload) if payload is not None else None,headers)
                response=conn.getresponse()
                assert response.getheader('cache-control')=='no-store'
                return response.status,json.loads(response.read())
            finally:
                timings.append(round(time.monotonic()-started,3));conn.close()
        assert call('/v1/runs',payload=value,bearer=None)[0]==401
        assert call('/v1/runs',payload=value,bearer=reader)[0]==403
        status,accepted=call('/v1/runs',payload=value)
        assert status==202 and accepted['state']=='queued'
        assert call('/v1/runs',payload=value)==(status,accepted)
        worker=ThermalSimulationWorker(publisher,tenant_id='tenant-1',lease_seconds=300,
            scenario_store=farm.thermal,farm_scenario_service=farm)
        result=worker.run_once(accepted['job_id'])
        assert result.state=='succeeded'
        path=f"/v1/jobs/{accepted['job_id']}/run"
        status,summary=call(path,bearer=reader)
        assert status==200 and summary['run_id']==result.run_id
        assert call(path,bearer=other)[0]==404
        receipt=json.loads(farm.jobs.read_artifact('tenant-1',UUID(accepted['job_id'])))
        assert receipt['farm_scenario_sha256']==value['farm_scenario_sha256']
    finally:
        server.should_exit=True;thread.join(timeout=15)
        assert not thread.is_alive()
        print('farm_thermal_https_seconds='+json.dumps(timings))
