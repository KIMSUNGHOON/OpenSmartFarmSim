"""Prefix HTTP control flow, actual SCRAM and verified TLS original responses."""
import asyncio
from copy import deepcopy
from dataclasses import replace
from datetime import datetime, timedelta, timezone, tzinfo
from hashlib import sha256
import json
import os
from pathlib import Path
import subprocess
import sys
import threading
from types import SimpleNamespace
from urllib.parse import urlencode
from uuid import uuid4

from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
import pytest

from app import api
from app import api_crop_greenhouse_solar_prefix_routes as route
from app import api_crop_greenhouse_solar_prefix as public
from app import crop_greenhouse_solar_prefix as model
from app.http_identity import current_principal
from app.runtime_roles import RolePolicyHold
from test_api_crop_cycle_route import protect, TOKEN, NOW
from test_http_identity import request
from test_api_crop_greenhouse_solar_execution_http import JOB, TOKEN, NOW


JOB = '11111111-1111-4111-8111-111111111111'
PATH = '/v1/jobs/'+JOB+'/crop-greenhouse-solar-execution/prefix'
SELECTOR = {'publication_sequence': 1, 'head_sha256': 'a'*64, 'proof_sha256': 'b'*64}


def save(name, value):
    root = os.environ.get('OSSF_VENTILATION_PREFIX_HTTP_EVIDENCE')
    if root:
        with (Path(root)/(name+'.json')).open('x') as f:
            os.fchmod(f.fileno(), 0o400); json.dump(value, f, sort_keys=True, indent=2)
            f.flush(); os.fsync(f.fileno())


def authorized(*scopes):
    p = current_principal()
    if p is None: return None, api._error(401, 'unauthenticated', 'Authentication required')
    if any(s not in p['scopes'] for s in scopes): return None, api._error(403, 'forbidden', 'Resource access denied')
    return p['tenant_id'], None


def active_row():
    at = datetime(2026, 10, 11, tzinfo=timezone.utc)
    return {'tenant_id': 'tenant-1', 'job_id': '11111111-1111-4111-8111-111111111111',
        'stage': 'simulation', 'state': 'simulating', 'cancel_requested': False, 'attempt_count': 1,
        'lease_token': 'private-test-lease', 'input_sha256': 'a'*64, 'input_bytes': b'private-input',
        'lease_until': at+timedelta(seconds=600), 'updated_at': at, 'reason': None, 'future_column': {'value': 1}}


@pytest.mark.parametrize('fault', ['token', 'attempt', 'attempt-bool', 'input', 'private-input', 'cancel', 'cancel-int',
    'terminal', 'queued', 'stage', 'reason', 'future-column', 'added-column', 'removed-column',
    'lease-backward', 'updated-backward', 'lease-naive', 'updated-naive', 'lease-null', 'updated-text', 'missing-token'])
def test_lease_refresh_rejects_other_row_changes_and_invalid_timestamps(fault):
    before = active_row(); after = deepcopy(before)
    after['lease_until'] += timedelta(seconds=1); after['updated_at'] += timedelta(seconds=1)
    if fault == 'token': after['lease_token'] = 'other-token'
    elif fault == 'attempt': after['attempt_count'] = 2
    elif fault == 'attempt-bool': after['attempt_count'] = True
    elif fault == 'input': after['input_sha256'] = 'b'*64
    elif fault == 'private-input': after['input_bytes'] = b'other-private-input'
    elif fault == 'cancel': after['cancel_requested'] = True
    elif fault == 'cancel-int': after['cancel_requested'] = 0
    elif fault == 'terminal': after['state'] = 'succeeded'
    elif fault == 'queued': before['state'] = after['state'] = 'queued'
    elif fault == 'stage': after['stage'] = 'research'
    elif fault == 'reason': after['reason'] = {'code': 'changed'}
    elif fault == 'future-column': after['future_column']['value'] = 2
    elif fault == 'added-column': after['unknown'] = None
    elif fault == 'removed-column': del after['future_column']
    elif fault == 'lease-backward': after['lease_until'] = before['lease_until']-timedelta(microseconds=1)
    elif fault == 'updated-backward': after['updated_at'] = before['updated_at']-timedelta(microseconds=1)
    elif fault == 'lease-naive': after['lease_until'] = after['lease_until'].replace(tzinfo=None)
    elif fault == 'updated-naive': after['updated_at'] = after['updated_at'].replace(tzinfo=None)
    elif fault == 'lease-null': before['lease_until'] = after['lease_until'] = None
    elif fault == 'updated-text': before['updated_at'] = after['updated_at'] = '2026-10-11T00:00:00Z'
    else: before['lease_token'] = after['lease_token'] = None
    assert not model._same_job_row(before, after)


@pytest.mark.parametrize('changed', [(), ('lease_until',), ('updated_at',), ('lease_until', 'updated_at')])
def test_lease_refresh_accepts_valid_nondecreasing_times_only(changed):
    before = active_row(); after = deepcopy(before)
    for key in changed: after[key] += timedelta(microseconds=1)
    assert model._same_job_row(before, after)
    before['state'] = after['state'] = 'queued'
    assert model._same_job_row(before, after) is (not changed)


def test_lease_refresh_compares_instants_across_UTC_offsets():
    before = active_row(); after = deepcopy(before)
    for key in ('lease_until', 'updated_at'):
        after[key] = (after[key]+timedelta(microseconds=1)).astimezone(timezone(timedelta(hours=9)))
    assert model._same_job_row(before, after)
    after['updated_at'] -= timedelta(microseconds=2)
    assert not model._same_job_row(before, after)


@pytest.mark.parametrize('field', ['updated_at', 'created_at'])
@pytest.mark.parametrize('state', ['simulating', 'queued'])
def test_job_timestamp_UTC_regression_with_shared_timezone_is_rejected(field, state):
    class FoldOffset(tzinfo):
        def utcoffset(self, value): return timedelta(hours=0 if value is None else value.fold)
        def dst(self, value): return timedelta(0)
    before = active_row(); before['state'] = state
    if state == 'queued': before.update(attempt_count=0, lease_token=None, lease_until=None)
    before[field] = datetime(2026, 10, 11, tzinfo=FoldOffset())
    after = dict(before); after[field] = before[field].replace(fold=1)
    assert after[field] == before[field]
    assert after[field].astimezone(timezone.utc) < before[field].astimezone(timezone.utc)
    assert not model._same_job_row(before, after)


@pytest.mark.parametrize('fault', ['missing', 'owner', 'tenant', 'job', 'digest', 'payload', 'record-digest',
    'token', 'private-input', 'latest', 'links', 'publications', 'outcomes', 'terminal'])
def test_private_witness_rejects_mixed_record_and_bundle(fault):
    query = object.__new__(model.SolarExecutionPrefixQuery); row = active_row()
    bundle = (row, None, [], [], [], []); digest = sha256(b'{}').hexdigest()
    witness = model._ReadWitness(query, row['tenant_id'], row['job_id'], deepcopy(bundle), digest)
    record = model.PrefixRead(b'{}', digest, witness)
    assert query._unchanged(row['tenant_id'], row['job_id'], record, bundle)
    assert 'private-test-lease' not in repr(record) and 'private-input' not in repr(record) and repr(witness) == '_ReadWitness()'
    if fault == 'missing': record = replace(record, _witness=None)
    elif fault == 'owner': record = replace(record, _witness=replace(witness, owner=object()))
    elif fault == 'tenant': record = replace(record, _witness=replace(witness, tenant='foreign'))
    elif fault == 'job': record = replace(record, _witness=replace(witness, job_id='other'))
    elif fault == 'digest': record = replace(record, _witness=replace(witness, payload_sha256='0'*64))
    elif fault == 'payload': record = replace(record, payload_raw=b'{"changed":true}')
    elif fault == 'record-digest': record = replace(record, payload_sha256='0'*64)
    elif fault == 'token': bundle[0]['lease_token'] = 'replaced-lease'
    elif fault == 'private-input': bundle[0]['input_bytes'] = b'replaced-private-input'
    else:
        index = {'latest': 1, 'links': 2, 'publications': 3, 'outcomes': 4, 'terminal': 5}[fault]
        changed = list(bundle); changed[index] = {'changed': True}; bundle = tuple(changed)
    assert not query._unchanged(row['tenant_id'], row['job_id'], record, bundle)


def assembly(monkeypatch, scopes=route.PROGRESS_SCOPES):
    trace = []; clock = {'now': NOW}; state = {'raw': b'{}', 'error': None, 'hook': None, 'missing': False, 'tenant': 'tenant-1'}
    jobs = SimpleNamespace(principal_provider=current_principal); farms = object()
    server = SimpleNamespace(binding=SimpleNamespace(jobs=jobs, farms=farms))
    store = object.__new__(model.execution.storage.SolarResultStore); store.jobs=jobs;store.server=server
    original = object.__new__(model.execution.SolarExecutionQuery); original.jobs=jobs;original.server=server;original.results=store
    query = object.__new__(model.SolarExecutionPrefixQuery); query.query=original;query.jobs=jobs;query.server=server
    monkeypatch.setattr(query, '_binding', lambda: None); monkeypatch.setattr(store, '_binding', lambda: None)
    def read(tenant, job_id, **options):
        trace.append((tenant, job_id, options)); assert current_principal()['tenant_id']=='tenant-1'
        if state['hook']: state['hook']()
        if state['error']: raise state['error']
        return None if state['missing'] else object()
    monkeypatch.setattr(query, 'read', read)
    def read_public(owner,tenant,job_id,**options):
        assert owner is query
        read(tenant,job_id,**options)
        return None if state['missing'] else state['raw']
    monkeypatch.setattr(public, 'project_prefix', lambda value: value)
    monkeypatch.setattr(public, '_public_bytes', lambda _: state['raw'])
    monkeypatch.setattr(public, 'read_prefix', read_public)
    def account(*scopes):
        tenant, denied = authorized(*scopes)
        return (state['tenant'] if tenant else None), denied
    app=FastAPI()
    @app.exception_handler(RequestValidationError)
    async def rejected(*_): return api._error(422, 'invalid_request', 'Invalid request')
    args=dict(jobs=jobs,farms=farms,store=store,query=query,principal_provider=current_principal,
        authorized_tenant=account,error=api._error,access=api._access)
    route.install_solar_prefix_routes(app, **args)
    return SimpleNamespace(app=protect(app, tenant='tenant-1', scopes=scopes, clock=lambda:clock['now']),
        core=app, args=args, state=state, clock=clock, trace=trace)


def call(c, view='summary', *, query=None, body=b'', headers=None, job=JOB):
    suffix='' if view=='summary' else '/'+view
    if query is None: query=b'' if view=='summary' else urlencode(SELECTOR).encode()
    return asyncio.run(request(c.app,path='/v1/jobs/'+job+'/crop-greenhouse-solar-execution/prefix'+suffix,
        query=query,body=body,headers=headers if headers is not None else [(b'authorization',b'Bearer '+TOKEN)]))


def test_explicit_prefix_openapi_contract(monkeypatch):
    c = assembly(monkeypatch); document = c.core.openapi()
    prefix = '/v1/jobs/{job_id}/crop-greenhouse-solar-execution/prefix'
    assert set(document['paths']) == {prefix, prefix+'/samples', prefix+'/events'}
    for suffix, operation in (('', 'getSolarPrefix'), ('/samples', 'getSolarPrefixSamples'), ('/events', 'getSolarPrefixEvents')):
        value = document['paths'][prefix+suffix]['get']
        assert value['operationId'] == operation and value['security'] == [{'ServiceBearer':[]}]
        assert value['x-ossf-required-scopes'] == list(route.PROGRESS_SCOPES)
        assert value['x-ossf-max-response-bytes'] == 2*1024*1024
        parameters = {p['name']:p for p in value['parameters'] if p['in']=='query'}
        assert set(parameters) == (set(SELECTOR)|{'start','limit'} if suffix else set())
        if suffix:
            assert all(parameters[k]['required'] for k in SELECTOR)
            assert parameters['limit']['schema']['maximum'] == (64 if suffix=='/samples' else 8)
        assert all(str(status) in value['responses'] for status in (401,403,404,409,422,503))
    assert c.trace == []


@pytest.mark.parametrize('view', ['summary','samples','events'])
def test_route_code_drift_never_dispatches(monkeypatch, view):
    c = assembly(monkeypatch)
    monkeypatch.setattr(route, 'CODE_SHA256', '0'*64)
    assert call(c, view)[0] == 503 and c.trace == []


@pytest.mark.parametrize('fault', ['query', 'no-query', 'original', 'store', 'jobs', 'farms', 'principal', 'query-jobs',
    'query-server', 'store-jobs', 'store-server', 'binding-jobs', 'binding-farms', 'query-pin', 'store-pin'])
def test_mixed_or_missing_assembly_rejected(monkeypatch, fault):
    c=assembly(monkeypatch);args=c.args.copy();q=args['query'];s=args['store']
    if fault in ('query','store','jobs','farms'):args[fault]=object()
    elif fault=='no-query':args['query']=None
    elif fault=='original':q.query=object()
    elif fault=='principal':args['principal_provider']=lambda:None
    elif fault=='query-jobs':q.jobs=object()
    elif fault=='query-server':q.server=object()
    elif fault=='store-jobs':s.jobs=object()
    elif fault=='store-server':s.server=object()
    elif fault=='binding-jobs':q.server.binding.jobs=object()
    elif fault=='binding-farms':q.server.binding.farms=object()
    else:
        def denied():raise RuntimeError('private diagnostic')
        monkeypatch.setattr(q if fault=='query-pin' else s,'_binding',denied)
    with pytest.raises(ValueError,match='^trusted solar prefix reader required$'):
        route.install_solar_prefix_routes(FastAPI(),**args)


@pytest.mark.parametrize('view',['summary','samples','events'])
@pytest.mark.parametrize('fault',['body','extra','duplicate','id','uppercase'])
def test_invalid_request_never_dispatches(monkeypatch,view,fault):
    c=assembly(monkeypatch);query=b'' if view=='summary' else urlencode(SELECTOR).encode()
    if fault=='extra':query+=b'&private=x' if query else b'private=x'
    if fault=='duplicate':query+=b'&head_sha256='+b'a'*64 if query else b'x=1&x=2'
    job='invalid' if fault=='id' else 'AAAAAAAA-AAAA-4AAA-8AAA-AAAAAAAAAAAA' if fault=='uppercase' else JOB
    assert call(c,view,query=query,job=job,body=b'{}' if fault=='body' else b'')[0]==422 and not c.trace


@pytest.mark.parametrize('view',['samples','events'])
@pytest.mark.parametrize('fault',['missing','zero-sequence','too-large-sequence','noncanonical','float','bool','bad-head','bad-proof',
    'zero-limit','large-limit','bool-offset','large-offset','negative','duplicate'])
def test_page_selector_bounds_before_dispatch(monkeypatch,view,fault):
    c=assembly(monkeypatch);p=SELECTOR.copy()
    if fault=='missing':del p['proof_sha256']
    elif fault=='zero-sequence':p['publication_sequence']=0
    elif fault=='too-large-sequence':p['publication_sequence']=4100
    elif fault=='noncanonical':p['publication_sequence']='01'
    elif fault=='float':p['publication_sequence']='1.0'
    elif fault=='bool':p['publication_sequence']='true'
    elif fault=='bad-head':p['head_sha256']='A'*64
    elif fault=='bad-proof':p['proof_sha256']='b'*63
    elif fault=='zero-limit':p['limit']=0
    elif fault=='large-limit':p['limit']=65 if view=='samples' else 9
    elif fault=='bool-offset':p['start']='true'
    elif fault=='large-offset':p['start']=513 if view=='samples' else 129
    elif fault=='negative':p['start']=-1
    query=urlencode(p).encode()
    if fault=='duplicate':query+=b'&publication_sequence=1'
    assert call(c,view,query=query)[0]==422 and not c.trace


@pytest.mark.parametrize('view',['summary','samples','events'])
@pytest.mark.parametrize('missing',['authentication','metadata','crop_result_read'])
def test_unauthorized_never_dispatches(monkeypatch,view,missing):
    scopes=set(route.PROGRESS_SCOPES)-{missing};c=assembly(monkeypatch,scopes=scopes)
    assert call(c,view,headers=[] if missing=='authentication' else None)[0]==(401 if missing=='authentication' else 403)
    assert not c.trace and current_principal() is None


@pytest.mark.parametrize('view',['summary','samples','events'])
@pytest.mark.parametrize('failure,status',[(PermissionError,403),(model.SolarPrefixSelectionConflict,409),
    (model.SolarPrefixRequestRejected,422),(model.SolarPrefixHold,422),(public.ProjectionHold,422),
    (model.SolarPrefixPending,503),(model.custody.farms.SolarFarmBindingHold,422),(RolePolicyHold,503),(RuntimeError,503)])
def test_fixed_failures_and_post_account_check(monkeypatch,view,failure,status):
    c=assembly(monkeypatch);c.state['error']=failure('private failure detail')
    response=call(c,view);assert response[0]==status and 'private failure detail' not in json.dumps(response[1])
    assert response[2][b'cache-control']==b'no-store'


@pytest.mark.parametrize('withdraw',['credential','tenant'])
@pytest.mark.parametrize('failure',[False,True])
def test_late_identity_hides_success_and_failure(monkeypatch,withdraw,failure):
    c=assembly(monkeypatch)
    def changed():
        if withdraw=='credential':c.clock['now']+=timedelta(hours=1)
        else:c.state['tenant']='foreign'
        if failure:raise RuntimeError('private failure')
    c.state['hook']=changed
    assert call(c)[0]==(401 if withdraw=='credential' else 403)


def test_missing_response_cap_and_default_page_options(monkeypatch):
    c=assembly(monkeypatch);c.state['missing']=True;assert call(c)[0]==404
    c.state['missing']=False
    for raw in (None,'private',b'',b' '* (public.MAX_RESPONSE_BYTES+1)):
        c.state['raw']=raw;assert call(c)[0]==(404 if raw is None else 503)
    c.state['raw']=b'{}'
    for view,maximum in [('samples',64),('events',8)]:
        status,_,headers=call(c,view);assert status==200
        assert c.trace[-1]==('tenant-1',JOB,{'selector':SELECTOR,'view':view,'start':0,'limit':maximum})
        assert headers[b'cache-control']==b'no-store' and headers[b'x-ossf-solar-prefix-version']==public.VERSION.encode()


@pytest.mark.parametrize('view',['summary','samples','events'])
def test_body_disconnect_before_dispatch(monkeypatch,view):
    c=assembly(monkeypatch);sent=[];path=PATH+('' if view=='summary' else '/'+view)
    async def receive():return {'type':'http.disconnect'}
    async def send(message):sent.append(message)
    asyncio.run(c.app(dict(type='http',asgi={'version':'3.0'},method='GET',path=path,raw_path=path.encode(),root_path='',
        query_string=b'' if view=='summary' else urlencode(SELECTOR).encode(),headers=[(b'authorization',b'Bearer '+TOKEN)],
        scheme='https',http_version='1.1',server=('test',443),client=('test',1234)),receive,send))
    assert sent[0]['status']==422 and not c.trace and current_principal() is None


@pytest.mark.parametrize('mode',['cancel','send-failure'])
def test_disconnected_request_releases_thread_and_identity(monkeypatch,mode):
    c=assembly(monkeypatch);entered=threading.Event();release=threading.Event();closed=threading.Event();after=[]
    def blocked():
        try:entered.set();assert release.wait(5);after.append(current_principal())
        finally:closed.set()
    c.state['hook']=blocked
    async def exercise():
        async def receive():return dict(type='http.request',body=b'',more_body=False)
        async def send(_):
            if mode=='send-failure':raise RuntimeError('owned disconnected transport')
        task=asyncio.create_task(c.app(dict(type='http',asgi={'version':'3.0'},method='GET',path=PATH,raw_path=PATH.encode(),
            root_path='',query_string=b'',headers=[(b'authorization',b'Bearer '+TOKEN)],scheme='https',http_version='1.1',
            server=('test',443),client=('test',1234)),receive,send))
        while not entered.is_set():await asyncio.sleep(.01)
        if mode=='cancel':
            task.cancel()
            with pytest.raises(asyncio.CancelledError):await task
        release.set()
        if mode=='send-failure':
            with pytest.raises(RuntimeError):await task
        while not closed.is_set():await asyncio.sleep(.01)
    asyncio.run(exercise());assert closed.is_set() and len(c.trace)==1 and current_principal() is None
    if mode=='cancel':assert after==[None]
