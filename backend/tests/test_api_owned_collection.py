"""Actual HTTP admission; owned fixtures and controller-owned keys are synthetic."""

import asyncio
from datetime import datetime, timezone, timedelta
from hashlib import sha256
import json
from pathlib import Path
import sys

import pytest
from psycopg import sql

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from app.api import create_app
from app.owned_fixture_collection import COLLECTION_SCOPES, CollectionWorker
from app.owned_collection_review import REVIEW_SCOPES
from test_owned_collection_review import review_setup
from test_owned_fixture_collection import collection_setup, login_scope, login_database
from test_api_job_status import UnusedMarketResultStore
from test_api_thermal_run import UnusedMarketHoldStore
from test_http_identity import request
from test_api_serve import tls_files

pytestmark = pytest.mark.parametrize('login_scope',
    [{'market_calculation':True, 'break_even_calculation':True}], indirect=True)


@pytest.fixture
def collection_api(review_setup):
    service, collected, principal, _, _ = review_setup
    jobs = service.collection.jobs
    app = create_app(jobs, UnusedMarketHoldStore(), service.runs, UnusedMarketResultStore(),
        principal_provider=jobs.principal_provider, collection_service=service.collection,
        owned_collection_review_service=service)
    record = service.collection.read_record('tenant-a', str(collected['job_id']))
    bodies = {'ingestion':{'research_job_id':record['research_job_id'], 'idempotency_key':'http-owned'},
              'review':{'collection_job_id':str(collected['job_id']), 'idempotency_key':'http-review'}}
    return app, service, principal, bodies


def post(app, kind, body, *, raw=None, media=b'application/json', auth=()):
    path = '/v1/ingestions' if kind=='ingestion' else '/v1/collection-reviews'
    return asyncio.run(request(app, path=path, method='POST',
        headers=[(b'content-type',media),(b'x-tenant-id',b'foreign'),*auth],
        body=json.dumps(body).encode() if raw is None else raw))[:2]


def counts(service):
    with service.collection.jobs.connect() as conn:
        return tuple(conn.execute(sql.SQL('SELECT count(*) AS n FROM {}')
            .format(service.collection.jobs._table(name))).fetchone()['n']
            for name in ('jobs','thermal_input_snapshots','job_publications'))


def test_http_collection_completion_to_review_intent_is_connected(collection_api):
    app, service, _, bodies = collection_api
    before = counts(service)
    status, admitted = post(app,'ingestion',bodies['ingestion'])
    assert status==202 and admitted['stage']=='collection' and admitted['state']=='queued'
    assert post(app,'ingestion',bodies['ingestion']) == (202,admitted)
    assert counts(service)==(before[0]+1,before[1],before[2])
    worker = CollectionWorker(service.collection,tenant_id='tenant-a')
    assert worker.run_once(admitted['job_id']).state=='succeeded'
    assert post(app,'ingestion',bodies['ingestion'])[1]['state']=='succeeded'
    reviewed = bodies['review'] | {'collection_job_id':admitted['job_id']}
    status, job = post(app,'review',reviewed)
    assert status==202 and job['stage']=='collection_review' and job['state']=='queued'
    assert post(app,'review',reviewed)==(202,job)
    assert counts(service)==(before[0]+2,before[1]+1,before[2]+1)
    row = service.collection.jobs.get_job('tenant-a',job['job_id'])
    assert row['tenant_id']=='tenant-a'
    text = json.dumps(job)
    assert 'tenant_id' not in job and 'snapshot_id' not in job and 'raw_utf8' not in text
    record = service.collection.read_record('tenant-a',admitted['job_id'])
    assert record['g0_status']=='not_accepted' and record['assessment_status']=='hold'


def test_closed_body_validation_and_scope_denial_admit_nothing(collection_api):
    app, service, principal, bodies = collection_api
    before = counts(service)
    for kind, scopes in (('ingestion',COLLECTION_SCOPES),('review',REVIEW_SCOPES)):
        body = bodies[kind]
        field = 'research_job_id' if kind=='ingestion' else 'collection_job_id'
        for scope in scopes:
            principal['scopes'].remove(scope)
            assert post(app,kind,body)[0]==403
            principal['scopes'].add(scope)
        for change in ({'tenant_id':'foreign'},{'raw_utf8':'private'}, {'source_url':'https://untrusted.example'},
                {'idempotency_key':''},{'idempotency_key':'한글'},{field:1},{field:'BAD'}, {'approved_g0':True}):
            assert post(app,kind,body | change)[0]==422
        assert post(app,kind,body,raw=b' '*4097)[0]==413
        assert post(app,kind,body,media=b'text/plain')[0]==415
        duplicate = b'{"idempotency_key":"one","idempotency_key":"two"}'
        assert post(app,kind,body,raw=duplicate)[0]==422
    assert counts(service)==before


def test_other_tenant_and_missing_parent_or_context_create_nothing(collection_api, monkeypatch):
    app, service, principal, bodies = collection_api
    before = counts(service)
    principal['tenant_id']='tenant-other'
    for kind,body in bodies.items(): assert post(app,kind,body)[0]==422
    principal['tenant_id']='tenant-a'
    principal['authenticated']=False
    for kind,body in bodies.items(): assert post(app,kind,body)[0]==401
    principal['authenticated']=True
    body = bodies['ingestion'] | {'research_job_id':'00000000-0000-4000-8000-000000000001'}
    assert post(app,'ingestion',body)[0]==422
    monkeypatch.setattr(service.runs,'get_decision_context',lambda *_:None)
    assert post(app,'review',bodies['review'])[0]==422
    assert counts(service)==before


@pytest.mark.parametrize('kind',['ingestion','review'])
def test_conflicting_intent_returns_409_and_rolls_back_snapshot(collection_api,kind):
    app, service, _, bodies = collection_api
    prefix = 'owned-fixture-collection-v1:' if kind=='ingestion' else 'owned-collection-review-v1:'
    key = prefix+sha256(bodies[kind]['idempotency_key'].encode()).hexdigest()
    stage = 'collection' if kind=='ingestion' else 'collection_review'
    service.collection.jobs.submit('tenant-a',stage,{'input_version':'other'},key)
    before = counts(service)
    assert post(app,kind,bodies[kind])[0]==409 and counts(service)==before


@pytest.mark.parametrize('kind',['ingestion','review'])
@pytest.mark.parametrize('fault,status',[('scope',403),('binding',503),('private',503)])
def test_commit_failure_is_private_and_atomic(collection_api,monkeypatch,kind,fault,status):
    app, service, principal, bodies = collection_api
    jobs = service.collection.jobs
    before = counts(service)
    original = jobs._event
    def change(*args,**kwargs):
        original(*args,**kwargs)
        if fault=='scope': principal['scopes'].remove('collection_execute' if kind=='ingestion' else 'collection_review_create')
        if fault=='binding': jobs.artifact_root = jobs.artifact_root.parent/'changed-private-root'
        if fault=='private': raise RuntimeError('synthetic private backend failure')
    monkeypatch.setattr(jobs,'_event',change)
    code, error = post(app,kind,bodies[kind])
    assert code==status and 'private' not in json.dumps(error)
    assert counts(service)==before


def test_missing_service_and_mismatched_assembly_are_rejected(collection_api):
    app, service, _, bodies = collection_api
    jobs = service.collection.jobs
    empty = create_app(jobs,UnusedMarketHoldStore(),service.runs,UnusedMarketResultStore(),
        principal_provider=jobs.principal_provider)
    for kind,body in bodies.items(): assert post(empty,kind,body)[0]==503
    with pytest.raises(ValueError):
        create_app(jobs,UnusedMarketHoldStore(),service.runs,UnusedMarketResultStore(),
            principal_provider=lambda:None,collection_service=service.collection)
    with pytest.raises(ValueError):
        create_app(jobs,UnusedMarketHoldStore(),service.runs,UnusedMarketResultStore(),
            principal_provider=jobs.principal_provider,owned_collection_review_service=service)


def test_real_bearer_runtime_assembles_collection_stores(collection_api,tls_files):
    from app.api_runtime import ApiRuntime
    from app.http_identity import BearerGrant, BearerRegistry, current_principal, token_digest
    from test_api_runtime import config, dependencies
    from test_thermal_run_store import verify_test_context
    _, service, principal, bodies = collection_api
    jobs = service.collection.jobs
    token = b'synthetic-owned-http-bearer-'+b'r'*32
    now = datetime.now(timezone.utc)
    grant = BearerGrant(token_digest(token),'tenant-a',frozenset(principal['scopes']),
        now-timedelta(seconds=1),now+timedelta(hours=1))
    cert,key,_ = tls_files
    runtime = ApiRuntime(config(policy=jobs.runtime_identity[0],dsn=jobs._dsn,
        artifact_root=jobs.artifact_root,certificate=cert,private_key=key,port=0),
        dependencies(owned_fixture_registry=service.collection.registry,
            context_verifier=verify_test_context,bearer_registry=BearerRegistry((grant,))))
    assert runtime.collections.jobs is runtime.jobs
    assert runtime.collection_reviews.collection is runtime.collections
    assert runtime.collection_reviews.runs is runtime.thermal
    assert runtime.jobs.principal_provider is current_principal
    auth = [(b'authorization',b'Bearer '+token)]
    for kind,body in bodies.items():
        status,result = post(runtime.service.app,kind,body,auth=auth)
        assert status==202 and result['state']=='queued' and current_principal() is None
    assert post(runtime.service.app,'ingestion',bodies['ingestion'],auth=[])[0]==401
