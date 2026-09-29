"""Owned planning admission; test context keys and fake CLI establish no G1."""

from hashlib import sha256
import json
from pathlib import Path
import sys

import pytest
from psycopg import sql
from datetime import datetime, timezone, timedelta

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from app.owned_research import OwnedResearchService
from app.orchestration import LocationRequest, ResearchRequestRejected
from app.research_registry import ResearchRegistry, _scope_key
from app.cli_contracts import DecisionContract, _canonical, ProposalHold
from app.cli_worker import CliWorker
from app.owned_fixture_collection import CollectionWorker
from app.api import create_app
from test_owned_collection_review import review_setup
from test_owned_fixture_collection import collection_setup, login_scope, login_database
from test_api_location_research import post
from test_api_job_status import UnusedMarketHoldStore, UnusedMarketResultStore
from test_cli_worker import _fake_cli
from test_api_serve import tls_files


@pytest.fixture
def research_setup(review_setup):
    review, collected, principal, _, _ = review_setup
    principal['scopes'].add('location_create')
    record = review.collection.read_record('tenant-a',str(collected['job_id']))
    body = LocationRequest(latitude=37.5,longitude=127.0,
        period_start_utc='2026-10-15T08:00:00Z',period_end_utc='2026-10-15T10:00:00Z',
        goal_id='owned-fixture-contract-check',idempotency_key='owned-research')
    raw = _canonical({'registry_version':'research-registry-v1','registrations':[{
        'tenant_id':'tenant-a','point':{'latitude':body.latitude,'longitude':body.longitude},
        'period_start_utc':body.period_start_utc,'period_end_utc':body.period_end_utc,
        'goal_id':body.goal_id,'provider_ids':[review.collection.registry.provider_id]}]})
    catalog = ResearchRegistry(raw,sha256(raw).hexdigest())
    bindings = {_scope_key('tenant-a',(body.latitude,body.longitude),body.period_start_utc,
        body.period_end_utc,body.goal_id):record['decision_context_id']}
    service = OwnedResearchService(review.collection.jobs,review.runs,catalog,review.collection.registry,bindings)
    return service,body,principal,bindings


def admitted_jobs(service,body):
    with service.store.connect() as conn:
        return conn.execute(sql.SQL('SELECT count(*) AS n FROM {} WHERE tenant_id=%s AND stage=%s AND idempotency_key=%s')
            .format(service.store._table('jobs')),('tenant-a','research',body.idempotency_key)).fetchone()['n']


def test_http_research_fake_cli_and_actual_collection_are_connected(research_setup,tmp_path):
    service,body,principal,bindings = research_setup
    app = create_app(service.store,UnusedMarketHoldStore(),service.runs,UnusedMarketResultStore(),
        principal_provider=service.store.principal_provider,location_research_service=service)
    for scope in ('metadata','decision_context_read'):
        principal['scopes'].remove(scope)
        assert post(app,body.model_dump(mode='json'),raw=b'{')[0]==403
        principal['scopes'].add(scope)
    status,accepted = post(app,body.model_dump(mode='json'))
    assert status==202 and accepted['research_job']['state']=='queued'
    assert post(app,body.model_dump(mode='json'))==(202,accepted)
    assert accepted['spatial_support']=='pending_research' and 'decision_context_id' not in json.dumps(accepted)
    bindings.clear()
    contract = DecisionContract(service.authority_snapshot)
    service.store.decision_validator=contract
    program = _fake_cli(tmp_path)
    program.write_text(program.read_text().replace('candidate-a',service.registry.provider_id))
    home=tmp_path/'owned-research-home';home.mkdir(mode=0o700)
    worker=CliWorker(service.store,contract,cli_path=program,codex_home=home,
        child_env={'CODEX_API_KEY':'synthetic-test-key'},timeout_seconds=10,lease_seconds=300,synthetic_smoke=True)
    result=worker.run_once()
    assert result.state=='succeeded' and result.decision_id
    reviewed=service.store.get_job('tenant-a',accepted['research_job']['job_id'])
    published=json.loads(service.store.read_artifact('tenant-a',reviewed['job_id']))
    assert published['selected_ids']==[service.registry.provider_id] and published['decision_context_id']
    from app.owned_fixture_collection import CollectionService
    collection=CollectionService(service.store,service.registry)
    job=collection.submit('tenant-a',str(reviewed['job_id']),'collection-after-research')
    assert CollectionWorker(collection,tenant_id='tenant-a').run_once(str(job['job_id'])).state=='succeeded'
    record=collection.read_record('tenant-a',str(job['job_id']))
    assert record['g0_status']=='not_accepted' and record['assessment_status']=='hold'
    assert record['decision_context_id']==published['decision_context_id']


@pytest.mark.parametrize('fault',['context','scope','period','provider'])
def test_missing_or_changed_scope_or_context_admits_no_research(research_setup,monkeypatch,fault):
    service,body,principal,_=research_setup
    if fault=='context': monkeypatch.setattr(service.runs,'get_decision_context',lambda *_:None)
    if fault=='scope': principal['scopes'].remove('decision_context_read')
    if fault=='period': body=body.model_copy(update={'period_end_utc':'2026-10-15T11:00:00Z'})
    if fault=='provider': service.registry.provider_id='other-provider'
    with pytest.raises((PermissionError,ResearchRequestRejected,RuntimeError)):
        service.submit('tenant-a',body)
    assert admitted_jobs(service,body)==0


@pytest.mark.parametrize('fault',['scope','binding','private'])
def test_commit_failure_rolls_back_intent(research_setup,monkeypatch,fault):
    service,body,principal,_=research_setup
    original=service.store._event
    def change(*args,**kwargs):
        original(*args,**kwargs)
        if fault=='scope': principal['scopes'].remove('location_create')
        if fault=='binding': service.runs._context_verifier=lambda *_:None
        if fault=='private': raise RuntimeError('synthetic private planning backend detail')
    monkeypatch.setattr(service.store,'_event',change)
    with pytest.raises((PermissionError,ResearchRequestRejected,RuntimeError)):
        service.submit('tenant-a',body)
    assert admitted_jobs(service,body)==0


def test_unmodified_initial_registry_holds_and_forged_input_is_rejected(research_setup):
    service,body,_,_=research_setup
    _,_,admitted=service.submit('tenant-a',body)
    with service.store.connect() as conn:
        full=service.store._locked_job(conn,'tenant-a',admitted['job_id'])
        raw=service.store._verified_input(full)
    job=dict(full,input_bytes=raw)
    contract=DecisionContract(service.authority_snapshot)
    value,authority=contract.input_context(job)
    assert authority.allow_proceed and authority.approved_claims=={}
    assert service.catalog.authority_snapshot(job,value) is None
    _,context=service.prepare('tenant-a',body)
    with pytest.raises(ProposalHold):
        contract.input_context(dict(job,created_at=context['recorded_at']-timedelta(microseconds=1)))
    forged=value | {'decision_context_id':'other-context'}
    bad=_canonical(forged)
    with pytest.raises(ProposalHold):
        contract.input_context(dict(job,input_bytes=bad,input_sha256=sha256(bad).hexdigest()))


@pytest.mark.parametrize('login_scope',[{'market_calculation':True,'break_even_calculation':True}],indirect=True)
def test_optional_runtime_uses_stored_context_for_bearer_location(research_setup,tls_files):
    import asyncio
    from app.api_runtime import ApiRuntime
    from app.http_identity import BearerGrant, BearerRegistry, current_principal, token_digest
    from test_api_runtime import config, dependencies
    from test_http_identity import request
    from test_thermal_run_store import verify_test_context
    service,body,principal,bindings=research_setup
    now=datetime.now(timezone.utc)
    token=b'synthetic-owned-research-token-'+b'r'*32
    grant=BearerGrant(token_digest(token),'tenant-a',frozenset(principal['scopes']),
        now-timedelta(seconds=1),now+timedelta(hours=1))
    cert,key,_=tls_files
    runtime=ApiRuntime(config(policy=service.store.runtime_identity[0],dsn=service.store._dsn,
        artifact_root=service.store.artifact_root,certificate=cert,private_key=key,port=0),
        dependencies(research_registry=service.catalog,owned_fixture_registry=service.registry,
            owned_research_contexts=bindings,bearer_registry=BearerRegistry((grant,)),context_verifier=verify_test_context))
    assert type(runtime.research) is OwnedResearchService and runtime.research.store is runtime.jobs
    status,accepted,_=asyncio.run(request(runtime.service.app,path='/v1/locations',method='POST',
        headers=[(b'content-type',b'application/json'),(b'authorization',b'Bearer '+token)],
        body=json.dumps(body.model_dump(mode='json')).encode()))
    assert status==202 and accepted['research_job']['state']=='queued' and current_principal() is None
