"""Actual SCRAM and verified TLS for co2 control and confirmed prefix bytes."""
from contextlib import contextmanager
from copy import deepcopy
from dataclasses import replace
from hashlib import sha256
import http.client
import json
import ssl
import threading
import time
import os
from pathlib import Path
from types import SimpleNamespace
from urllib.parse import urlencode
from uuid import uuid4

import pytest

from app import api
from app import api_crop_greenhouse_co2_execution_http as route
from app import api_crop_greenhouse_co2_prefix as public
from app import crop_greenhouse_co2_prefix as prefix
from app.crop_greenhouse_co2_current_query import Co2CurrentQuery
from app.api_openapi import _SchemaOnlyStores
from app.http_identity import current_principal
from app.https_service import HttpsApiService
from test_api_crop_cycle_route import protect, TOKEN
from test_crop_greenhouse_co2_farm_binding import authoring as co2_authoring
from test_crop_greenhouse_co2_execution_query import (
    setup as query_setup, worker_setup, producer_setup, profiles,
    login_database, original_login_scope, login_scope, query_cleanup)
from test_api_crop_greenhouse_co2_prefix_native import producer_setup
import test_crop_greenhouse_co2_execution_query as reference
from test_crop_greenhouse_co2_prefix_concurrent import lightweight_actor
from test_api_serve import tls_files

pytestmark = [reference.reference.pytestmark, pytest.mark.usefixtures('query_cleanup')]
POST = '/v1/crop-greenhouse-co2-executions'


def save(name, value):
    root = os.environ.get('OSSF_CO2_EXECUTION_HTTP_EVIDENCE')
    if root:
        with (Path(root)/(name+'.json')).open('x') as f:
            os.fchmod(f.fileno(), 0o400); json.dump(value, f, sort_keys=True, indent=2)
            f.flush(); os.fsync(f.fileno())


@pytest.fixture
def authoring(login_scope, monkeypatch):
    base = co2_authoring.__wrapped__(login_scope, monkeypatch)
    farms, _, principal = base; replay = farms.replay; mode = {'preparing':True}
    def provider(): return principal if mode['preparing'] else current_principal()
    monkeypatch.setattr(replay.jobs, 'principal_provider', provider)
    for obj in (replay.thermal.runs, replay.thermal.holds, replay.candidates,
            replay.candidates._source, replay.candidates._source._source):
        monkeypatch.setattr(obj, '_principal_provider', provider)
    farms._http_test_mode = mode
    try: yield base
    finally: mode['preparing'] = True


@pytest.fixture
def native(query_setup):
    query, worker, job, raw, value = query_setup
    farms = worker.server.binding.farms; replay = farms.replay
    with worker.jobs.connect() as conn:
        assert conn.pgconn.used_password and conn.info.get_parameters()['require_auth'] == 'scram-sha-256'
    stored = Co2CurrentQuery(worker.results); accepted = prefix.Co2ExecutionPrefixQuery(query)
    app = api.create_app(worker.jobs, replay.thermal.holds, replay.thermal.runs, _SchemaOnlyStores(),
        principal_provider=worker.jobs.principal_provider, thermal_scenario_store=replay.thermal,
        farm_scenario_service=replay, farm_authoring_service=farms,
        crop_greenhouse_co2_result_store=worker.results, crop_greenhouse_co2_current_query=stored,
        crop_greenhouse_co2_execution_service=worker.checkpoints.admission,
        crop_greenhouse_co2_execution_query=query, crop_greenhouse_co2_prefix_query=accepted)
    yield SimpleNamespace(query=query, prefix=accepted, worker=worker, job=job, raw=raw, value=value,
        app=app, stored=stored, mode=farms._http_test_mode,
        path='/v1/jobs/'+job+'/crop-greenhouse-co2-execution')
    farms._http_test_mode['preparing'] = True


def fd_inventory():
    result = {}
    for path in Path('/proc/self/fd').iterdir():
        try:
            info = path.stat(); result[path.name] = (os.readlink(path), info.st_dev, info.st_ino)
        except FileNotFoundError: pass
    return result


@contextmanager
def served(c,tls_files,*,scopes=set(route.SUBMIT_SCOPES+route.PROGRESS_SCOPES+route.CANCEL_SCOPES),clock=None):
    c.mode['preparing']=False;cert,key,_=tls_files
    server=HttpsApiService(protect(c.app,tenant='tenant-1',scopes=scopes,clock=clock),cert,key,port=0).server()
    baseline=fd_inventory()
    thread=threading.Thread(target=server.run,daemon=True);thread.start();deadline=time.monotonic()+10
    try:
        while not server.started:
            assert thread.is_alive() and time.monotonic()<deadline;time.sleep(.01)
        port=server.servers[0].sockets[0].getsockname()[1];context=ssl.create_default_context(cafile=str(cert));replies=[]
        def send_request(op,path,body=None):
            connection=http.client.HTTPSConnection('127.0.0.1',port,context=context,timeout=60);start=time.monotonic()
            try:
                headers={'Authorization':'Bearer '+TOKEN.decode()}
                if body is not None:headers['Content-Type']='application/json'
                connection.request(op,path,body=body,headers=headers);response=connection.getresponse();raw=response.read()
                assert response.getheader('Cache-Control')=='no-store'
                replies.append({'status':response.status,'bytes':len(raw),'sha256':sha256(raw).hexdigest(),'seconds':time.monotonic()-start})
                return response.status,raw
            finally:connection.close()
        yield send_request,replies
    finally:
        server.should_exit=True;thread.join(15);assert not thread.is_alive();c.mode['preparing']=True
        assert fd_inventory()==baseline
    assert current_principal() is None


def running(c, budget=8):
    c.mode['preparing'] = True
    lease = reference.confirm(c.worker, c.job)
    progress = json.loads(c.worker.server.advance('tenant-1', c.raw, budget=budget))
    first = c.worker.checkpoints.confirm('tenant-1', c.job, attempt=lease['attempt'], lease_token=lease['lease_token'])
    return lease, progress, first


def pin(first):
    return {k:first['checkpoint'][k] for k in public.Selector.model_fields}


def test_native_submit_progress_and_running_cancel(native, tls_files, monkeypatch):
    c = native; captured = []; original = c.query.read
    def read(*a):
        raw = original(*a); captured.append(raw); return raw
    monkeypatch.setattr(c.query, 'read', read)
    with served(c, tls_files) as (http, replies):
        for _ in range(2):
            status, raw = http('POST', POST, c.raw)
            assert status == 202 and json.loads(raw)['job_id'] == c.job
        status, raw = http('GET', c.path)
        assert status == 200 and raw == captured[-1] and json.loads(raw)['checkpoint_status'] == 'none'
        lease, progress, first = running(c, 2); c.mode['preparing'] = False
        before = reference.persisted_digest(c.worker.jobs)
        with monkeypatch.context() as patch:
            calls = reference.forbid(patch); status, raw = http('GET', c.path)
            assert status == 200 and raw == captured[-1]
            checkpoint = json.loads(raw)['checkpoint']
            assert checkpoint['computed_through_utc'] == progress['times']['last_confirmed']['at']
            assert checkpoint['checkpoint_recorded_at'] == reference.model._utc(first['recorded_at'])
            assert not any(calls.values())
        assert reference.persisted_digest(c.worker.jobs) == before
        status, raw = http('POST', c.path+'/cancel'); out = json.loads(raw)
        assert status == 200 and out['cancel_accepted'] and out['cancel_requested']
        assert out['job']['state'] == 'simulating' and out['rights_or_gate_approval'] is False
        c.mode['preparing'] = True
        assert c.worker.jobs.ack_cancel('tenant-1', c.job, lease['attempt'], lease['lease_token'])
        c.mode['preparing'] = False
        status, raw = http('POST', c.path+'/cancel')
        assert status == 200 and json.loads(raw)['job']['state'] == 'canceled'
        assert not json.loads(raw)['cancel_accepted']
    save('native-lifecycle', {'actual_scram':True, 'verified_TLS':True, 'same_job_retry':True,
        'original_progress_wire_UTC':True, 'query_DB_unchanged':True, 'worker_ack_required':True, 'calls':calls, 'replies':replies})


@pytest.mark.parametrize('producer_setup', ['normal','hold'], indirect=True)
def test_native_terminal_saved_result_and_closed_prefix(native, tls_files, monkeypatch):
    c = native; c.worker.server.advance('tenant-1', c.raw, budget=128); outcome = c.worker.run_once(c.job)
    assert outcome.state in ('succeeded','hold') and outcome.result_id, (outcome.state, outcome.reason_code)
    expected = c.stored.read('tenant-1', outcome.result_id, c.value[1]['farm'])
    captured = []; original = c.query.read
    def read(*a):
        raw = original(*a); captured.append(raw); return raw
    monkeypatch.setattr(c.query, 'read', read)
    before = reference.persisted_digest(c.worker.jobs)
    with served(c, tls_files) as (http, replies):
        with monkeypatch.context() as patch:
            calls = reference.forbid(patch); status, raw = http('GET', c.path)
            assert status == 200 and raw == captured[-1]
            out = json.loads(raw); assert out['job']['state'] == outcome.state
            assert out['result']['result_id'] == outcome.result_id
            assert out['result']['farm']['batch_id'] and out['result']['farm']['zone_id']
            status, raw = http('GET', '/v1/crop-greenhouse-co2-research-results/'+outcome.result_id+'?'+urlencode(c.value[1]['farm']))
            assert status == 200 and raw == expected
            status, raw = http('GET', c.path+'/prefix'); out = json.loads(raw)
            assert status == 200 and out['prefix_status'] == 'closed'
            assert out['reference'] is out['summary'] is out['page'] is None
            assert not any(calls.values())
        assert reference.persisted_digest(c.worker.jobs) == before
        status, raw = http('POST', c.path+'/cancel')
        assert status == 200 and not json.loads(raw)['cancel_accepted']
    save('native-terminal-'+outcome.state, {'actual_scram':True, 'verified_TLS':True,
        'original_progress_and_existing_saved_wire':True, 'closed_prefix':True, 'query_DB_unchanged':True, 'calls':calls, 'replies':replies})


def test_native_rights_withdrawal_owner_cancel_without_metadata(native, tls_files):
    c = native; c.value[5].allowed = False
    try:
        with served(c, tls_files) as (http, replies):
            assert http('GET', c.path)[0] == 422 and http('GET', c.path+'/prefix')[0] == 422
            assert http('POST', POST, c.raw)[0] == 422
        with served(c, tls_files, scopes={'cancel'}) as (http, cancel_replies):
            assert http('GET', c.path+'/prefix')[0] == 403
            status, raw = http('POST', c.path+'/cancel')
            assert status == 200 and json.loads(raw)['job']['state'] == 'canceled'
    finally:
        c.value[5].allowed = True
    save('native-rights-cancel', {'actual_scram':True, 'verified_TLS':True,
        'source_rights_withdrawn':True, 'cancel_only_without_metadata':True, 'replies':replies+cancel_replies})


@pytest.mark.parametrize('producer_setup', ['normal', 'basis-transition'], indirect=True)
def test_native_original_prefix_views_and_selection(native, tls_files, monkeypatch, request):
    c = native; case = request.node.callspec.params['producer_setup']; pages = {}
    with served(c, tls_files, scopes=set(route.PROGRESS_SCOPES)) as (http, replies):
        status, raw = http('GET', c.path+'/prefix')
        assert status == 200 and json.loads(raw)['prefix_status'] == 'none'
        _, progress, first = running(c, 9 if case == 'basis-transition' else 8); selected = pin(first); c.mode['preparing'] = False
        before = reference.persisted_digest(c.worker.jobs)
        captured = []; serializer = public._public_bytes
        def serialize(value):
            raw = serializer(value); captured.append(raw); return raw
        with monkeypatch.context() as patch:
            calls = reference.forbid(patch); patch.setattr(public, '_public_bytes', serialize)
            for view in ('summary','samples','events'):
                c.mode['preparing'] = True
                try:
                    source_record = c.prefix.read('tenant-1', c.job, selector=selected, view=view)
                    source = json.loads(source_record.payload_raw)
                    program = c.prefix._source_program('tenant-1', c.job, source_record)
                    assert program == c.value[2][2]._context.program
                    bases = public.public._basis_map(program, source['manifest'])
                finally: c.mode['preparing'] = False
                target = c.path+'/prefix'+('' if view=='summary' else '/'+view+'?'+urlencode(selected))
                status, raw = http('GET', target); out = json.loads(raw)
                assert status == 200 and raw == captured[-1] and out['reference']['selector'] == selected
                assert out['reference']['checkpoint']['checkpoint_recorded_at'] == source['selection']['checkpoint_recorded_at']
                assert out['reference']['checkpoint']['computed_through_utc'] == progress['times']['last_confirmed']['at']
                if view in ('samples', 'events'): pages[view] = deepcopy(out['page']['records'])
                if view == 'samples':
                    page = deepcopy(out['page'])
                    for row in page['records']:
                        assert row.pop('co2_basis') == bases[row['value']['forcing_step_index']]
                    assert page == source['page']
                elif view == 'events':
                    assert out['page']['records'] == [public.public._event(r, source['manifest']['identity'], bases) for r in source['page']['records']]
                else: assert out['summary'] == source['summary']
                assert all(k not in raw.decode() for k in ('lease_token','lease_until','_witness','observed_head','dsn'))
            if case == 'basis-transition':
                assert progress['steps'] == 8 and program == c.value[2][2]._context.program
                assert {row['co2_basis'] for row in pages['samples']} == {'wet', 'dry'}
                event = next(row for row in pages['events'] if row['value']['step_index'] == 8)
                sample = next(row for row in pages['samples'] if row['value']['step_index'] == 8)
                assert event['time'] == sample['time'] and event['co2_basis'] == sample['co2_basis'] == 'wet'
                assert event['value']['forcing_step_index'] == sample['value']['forcing_step_index'] == 8
                assert next(row for row in pages['samples'] if row['value']['step_index'] == 4)['co2_basis'] == 'dry'
            for query, status in ((dict(selected,start=progress['counts']['samples']),200),
                    (dict(selected,start=512),422), (dict(selected,proof_sha256='0'*64),409)):
                assert http('GET', c.path+'/prefix/samples?'+urlencode(query))[0] == status
            assert http('GET', '/v1/jobs/'+str(uuid4())+'/crop-greenhouse-co2-execution/prefix')[0] == 404
            assert not any(calls.values())
        assert reference.persisted_digest(c.worker.jobs) == before
    save('native-prefix-views-'+case, {'actual_scram':True, 'verified_TLS':True, 'original_projection_bytes':True,
        'selected_program_equals_original_context':True,
        'same_UTC_new_forcing_before_event_and_output': case == 'basis-transition',
        'original_values_units_UTC_selector_first_time':True, 'query_DB_unchanged':True, 'calls':calls, 'replies':replies})


@pytest.mark.parametrize('fault', ['rights','page','witness','program'])
def test_native_late_prefix_changes_are_withheld(native, tls_files, monkeypatch, fault):
    c = native; _, _, first = running(c); selected = pin(first)
    _, artifact, _ = reference.reference.producer.locations(c.worker.server, c.raw)
    head = json.loads((artifact/'HEAD').read_bytes())
    commit = json.loads((artifact/(head['latest_commit_sha256']+'.json')).read_bytes())
    path = artifact/(commit['pages']['samples'][0]['sha256']+'.json'); source = path.read_bytes(); mode = path.stat().st_mode & 0o777
    program_path = c.value[2][0]/'source.json'; program_original = program_path.read_bytes(); program_mode = program_path.stat().st_mode & 0o777
    serializer = public._public_bytes; serializations = []
    before = reference.persisted_digest(c.worker.jobs)
    try:
        with served(c, tls_files, scopes=set(route.PROGRESS_SCOPES)) as (http, replies):
            with monkeypatch.context() as patch:
                calls = reference.forbid(patch)
                if fault == 'witness':
                    original = c.prefix.read
                    def no_witness(*a, **kw):
                        record = original(*a, **kw); return replace(record, _witness=None)
                    patch.setattr(c.prefix, 'read', no_witness)
                def serialize(value):
                    raw = serializer(value); serializations.append(raw)
                    if len(serializations) == 2:
                        if fault == 'rights': c.value[5].allowed = False
                        elif fault == 'page': path.chmod(0o600); path.write_bytes(source+b' '); path.chmod(mode)
                        elif fault == 'program':
                            changed = json.loads(program_original); block = changed['forcing_program'][0]['co2']
                            block['basis'] = 'dry' if block['basis'] == 'wet' else 'wet'
                            program_path.chmod(0o600); program_path.write_bytes(prefix.storage._canonical(changed)); program_path.chmod(program_mode)
                    return raw
                patch.setattr(public, '_public_bytes', serialize)
                status, raw = http('GET', c.path+'/prefix/samples?'+urlencode(selected))
                assert status == (503 if fault=='witness' else 422)
                assert raw not in serializations and len(serializations) == (0 if fault == 'witness' else 2) and not any(calls.values())
    finally:
        c.value[5].allowed = True; path.chmod(0o600); path.write_bytes(source); path.chmod(mode)
        if fault == 'program':
            program_path.chmod(0o600); program_path.write_bytes(program_original); program_path.chmod(program_mode)
    assert reference.persisted_digest(c.worker.jobs) == before
    save('native-prefix-late-'+fault, {'actual_scram':True, 'verified_TLS':True, 'serialized_values_withheld':True,
        'after_final_serialization_change_rejected': fault != 'witness',
        'missing_witness_denied_before_source': fault == 'witness',
        'query_DB_unchanged':True, 'owned_original_restored':True, 'calls':calls, 'replies':replies})


@pytest.mark.parametrize('action', ['heartbeat','cancel'])
def test_native_independent_change_after_prefix_serialization(native, tls_files, tmp_path, monkeypatch, action):
    c = native; _, _, first = running(c); selected = pin(first)
    serializer = public._public_bytes; serialized = []; observed = []
    with lightweight_actor(c.worker, c.job, tmp_path, action) as change:
        def serialize(value):
            raw = serializer(value); serialized.append(raw)
            if len(serialized) == 2: observed.append(change())
            return raw
        with served(c, tls_files, scopes=set(route.PROGRESS_SCOPES)) as (http, replies):
            with monkeypatch.context() as patch:
                calls = reference.forbid(patch); patch.setattr(public, '_public_bytes', serialize)
                status, raw = http('GET', c.path+'/prefix/samples?'+urlencode(selected))
                assert status == (503 if action=='cancel' else 200)
                if action == 'heartbeat':
                    out = json.loads(raw); assert raw == serialized[-1] and out['reference']['selector'] == selected
                    assert out['reference']['checkpoint']['checkpoint_recorded_at'] == reference.model._utc(first['recorded_at'])
                else: assert raw not in serialized
                assert len(observed) == 1 and len(serialized) == 2 and not any(calls.values())
    save('native-prefix-actor-'+action, {'actual_scram':True, 'verified_TLS':True, 'actor':observed[0],
        'current_change_handled_after_serialization':True, 'actor_SQL_is_intentional_test_control':True, 'calls':calls, 'replies':replies})


@pytest.mark.parametrize('confirmed', [False,True], ids=['private','confirmed'])
def test_native_new_original_HEAD_preserves_selected_HTTP_page(native, tls_files, tmp_path, monkeypatch, confirmed):
    c = native; lease, _, first = running(c, 2); selected = pin(first)
    _, artifact, _ = reference.reference.producer.locations(c.worker.server, c.raw)
    path = artifact/'HEAD'; old = path.read_bytes()
    progress = c.worker.server.advance('tenant-1', c.raw, budget=8)
    new = path.read_bytes(); mode = path.stat().st_mode & 0o777; tail = json.loads(progress)
    assert all(tail['counts'][k] > first['checkpoint']['counts'][k] for k in ('samples','events'))
    with c.worker.server._open('tenant-1', c.raw, False) as (session, _):
        checkpoint, _ = c.worker.checkpoints._snapshot(session, progress, 2, lease['input_sha256'])
    serializer = public._public_bytes; serialized = []; observed = []
    try:
        path.chmod(0o600); path.write_bytes(old); path.chmod(mode)
        expected = json.loads(public.read_prefix(c.prefix, 'tenant-1', c.job, selector=selected, view='samples'))
        with lightweight_actor(c.worker, c.job, tmp_path, 'publish-original', head_path=str(path), head_raw=new.decode(),
                head_mode=mode, checkpoint=checkpoint if confirmed else None, event_kind=prefix.checkpoints.EVENT_KIND) as change:
            def serialize(value):
                raw = serializer(value); serialized.append(raw)
                if len(serialized) == 2: observed.append(change())
                return raw
            with served(c, tls_files, scopes=set(route.PROGRESS_SCOPES)) as (http, replies):
                with monkeypatch.context() as patch:
                    calls = reference.forbid(patch); patch.setattr(public, '_public_bytes', serialize)
                    status, raw = http('GET', c.path+'/prefix/samples?'+urlencode(selected))
                    assert status == 200 and raw == serialized[-1]
                    actual = json.loads(raw); expected['observed_at'] = actual['observed_at']; assert actual == expected
                    assert len(observed) == 1 and len(serialized) == 2 and not any(calls.values())
        assert observed[0]['original_snapshot_event_inserted'] is confirmed
        save('native-prefix-append-'+str(confirmed), {'actual_scram':True, 'verified_TLS':True, 'actor':observed[0],
            'same_original_page_values_UTC_selector_first_time':True, 'precomputed_original_not_new_numerics':True,
            'counts_before_and_after':[first['checkpoint']['counts'],tail['counts']], 'calls':calls, 'replies':replies})
    finally:
        path.chmod(0o600); path.write_bytes(new); path.chmod(mode)
