"""Authenticated authored farm intake over actual disposable SCRAM stores."""

import asyncio
from copy import deepcopy
import json
from urllib.parse import urlsplit

import pytest

from app.api import create_app
from app.farm_authoring_storage import READ_SCOPES, WRITE_SCOPES, FarmAuthoringHold, FarmAuthoringService
from app.farm_authored_review import FarmAuthoredReviewService, FarmAuthoredReviewHold, REVIEW_SCOPES
from test_api_job_status import UnusedMarketResultStore
from test_farm_authoring_storage import authoring, login_database, login_scope
from test_farm_replay_scenario import farm_setup
from test_http_identity import request as http_request


pytestmark = pytest.mark.parametrize('login_scope', [{'market_calculation':True,
    'market_source_storage':True, 'thermal_scenario_storage':True,
    'break_even_calculation':True}], indirect=True)


def call(app, *, body=None, raw=None, path='/v1/farm-authored-inputs', media=b'application/json'):
    target=urlsplit(path)
    return asyncio.run(http_request(app,path=target.path,query=target.query.encode(),
        method='POST' if body is not None or raw is not None else 'GET',
        headers=[(b'content-type',media),(b'x-tenant-id',b'foreign')],
        body=json.dumps(body).encode() if raw is None else raw))[:2]


def application(service,review=None):
    replay=service.replay
    return create_app(replay.jobs,replay.thermal.holds,replay.thermal.runs,UnusedMarketResultStore(),
        principal_provider=replay.jobs.principal_provider,thermal_scenario_store=replay.thermal,
        farm_scenario_service=replay,farm_authoring_service=service,
        farm_authored_review_service=review)


def test_authored_farm_http_intake_read_scopes_and_revocation(authoring,monkeypatch):
    service,body,principal=authoring
    app=application(service)
    query='/v1/farm-authored-inputs?scenario_id=farm-1&scenario_revision=r1'
    for scope in WRITE_SCOPES:
        principal['scopes'].remove(scope)
        assert call(app,body=body)[0]==403
        principal['scopes'].add(scope)
    principal['authenticated']=False
    assert call(app,body=body)[0]==401
    principal['authenticated']=True
    assert call(app,raw=b'{"farm":{},"farm":{}}')[0]==422
    assert call(app,raw=b' '*65537)[0]==413
    assert call(app,body=body,media=b'text/plain')[0]==415
    invalid=deepcopy(body)
    invalid['rights']['store']=False
    assert call(app,body=invalid)[0]==422
    status,accepted=call(app,body=body)
    assert status==200 and accepted['registration_status']=='registered_unpublished_inputs'
    assert set(accepted)=={'scenario_id','scenario_revision','scenario_sha256','farm_sha256',
        'numeric_input_sha256','rights_sha256','registration_status','intent_job'}
    assert call(app,body=body)==(200,accepted)
    changed=deepcopy(body)
    changed['farm']['facility']['floor_area']['value']='101'
    assert call(app,body=changed)[0]==409
    assert call(app,path=query)==(200,accepted)
    for scope in READ_SCOPES:
        principal['scopes'].remove(scope)
        assert call(app,path=query)[0]==403
        principal['scopes'].add(scope)
    assert call(app,path='/v1/farm-authored-inputs?scenario_id=missing&scenario_revision=r1')[0]==404
    principal['tenant_id']='foreign'
    assert call(app,path=query)[0]==404
    principal['tenant_id']='tenant-1'
    monkeypatch.setattr(service,'_prepare',lambda *_: (_ for _ in ()).throw(FarmAuthoringHold('revoked')))
    assert call(app,path=query)[0]==422
    assert call(app,path=query)[1]=={'error':{'code':'farm_authoring_hold',
        'message':'Farm authoring evidence unavailable'}}


def test_unconfigured_authoring_is_unavailable(authoring):
    service,body,_=authoring
    replay=service.replay
    app=create_app(replay.jobs,replay.thermal.holds,replay.thermal.runs,UnusedMarketResultStore(),
        principal_provider=replay.jobs.principal_provider,thermal_scenario_store=replay.thermal,
        farm_scenario_service=replay)
    assert call(app,body=body)[0]==503


def test_authored_review_http_admission_is_queued_and_bound(authoring,monkeypatch):
    service,body,principal=authoring
    principal['scopes'].add('collection_review_create')
    review=FarmAuthoredReviewService(service)
    app=application(service,review)
    accepted=call(app,body=body)[1]
    request={'schema_version':'farm-authored-review-request-v1',
        'scenario_id':'farm-1','scenario_revision':'r1',
        'registration_sha256':accepted['scenario_sha256'],
        'idempotency_key':'farm-review-http-r1'}
    path='/v1/farm-authored-reviews'
    assert call(application(service),path=path,body=request)[0]==503
    detached=FarmAuthoredReviewService(FarmAuthoringService(service.replay))
    with pytest.raises(ValueError,match='trusted farm authored review service required'):
        application(service,detached)
    for scope in REVIEW_SCOPES:
        principal['scopes'].remove(scope)
        assert call(app,path=path,body=request)[0]==403
        principal['scopes'].add(scope)
    principal['authenticated']=False
    assert call(app,path=path,body=request)[0]==401
    principal['authenticated']=True
    assert call(app,path=path,raw=b'{"scenario_id":"a","scenario_id":"b"}')[0]==422
    assert call(app,path=path,raw=b' '*4097)[0]==413
    assert call(app,path=path,body=request,media=b'text/plain')[0]==415
    assert call(app,path=path,body=request | {'registration_sha256':'a'*64})[0]==422
    status,job=call(app,path=path,body=request)
    assert status==202 and job['state']=='queued' and job['stage']=='collection_review'
    assert call(app,path=path,body=request)==(202,job)
    assert service.replay.jobs.get_publication('tenant-1',job['job_id']) is None
    changed=deepcopy(body)
    changed['farm']['scenario_revision']='r2'
    changed['rights']['scenario_revision']='r2'
    second=call(app,body=changed)[1]
    conflict=request | {'scenario_revision':'r2','registration_sha256':second['scenario_sha256']}
    assert call(app,path=path,body=conflict)[0]==409
    monkeypatch.setattr(review,'prepare',lambda *_args,**_kwargs: (_ for _ in ()).throw(FarmAuthoredReviewHold('revoked')))
    assert call(app,path=path,body=request)[0]==422
    assert call(app,path=path,body=request)[1]=={'error':{'code':'farm_review_hold',
        'message':'Farm review evidence unavailable'}}
