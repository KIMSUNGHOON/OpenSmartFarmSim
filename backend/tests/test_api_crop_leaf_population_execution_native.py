"""Actual SCRAM and certificate-verified HTTPS for one owned leaf_population request."""
from contextlib import contextmanager
from copy import deepcopy
from datetime import timedelta
import http.client
import json
import os
from pathlib import Path
import ssl
import subprocess
import threading
import time

from fastapi import FastAPI
import pytest

from app import api_crop_leaf_population_execution as route
from app import crop_leaf_population_execution as execution
from app import crop_leaf_population_execution_query as query
from app.crop_leaf_population_execution_worker import LeafPopulationExecutionWorker
from app.content_access import ContentAccess
from app.http_identity import current_principal
from app.https_service import HttpsApiService
from login_database import login_database, login_scope
from test_crop_leaf_population_execution_native import Resolver
from test_crop_morphology_signed_artifact_native import final_cleanup
from test_api_crop_leaf_population_execution import TOKEN, NOW, error, access, authorized, protect
from test_crop_leaf_population_signed_artifact_native import PUBLIC
from test_crop_morphology_signed_artifact_native import schema_hash
import morphology_farm_factory as factory
import test_crop_leaf_population_farm_binding_native as leaf_factory


pytestmark = pytest.mark.parametrize('login_scope', [{'market_calculation': True, 'market_source_storage': True,
    'thermal_scenario_storage': True, 'break_even_calculation': True, 'crop_cycle_result_storage': True}], indirect=True)


@pytest.fixture
def http_setup(login_scope, tmp_path, monkeypatch):
    def provider_factory(principal):
        return lambda: principal if threading.current_thread() is threading.main_thread() else current_principal()
    create = factory.create_farm
    def with_request_provider(*args, **kwargs):
        return create(*args, **{**kwargs, 'principal_provider_factory': provider_factory})
    with monkeypatch.context() as patch:
        patch.setattr(factory, 'create_farm', with_request_provider)
        values = leaf_factory.registered_leaf_services(login_scope, tmp_path, monkeypatch)
    binding, body, packet, _, _, review, _, principal, rights, _ = values
    principal['scopes'].update(set(route.SUBMIT_SCOPES+route.READ_SCOPES+route.CANCEL_SCOPES))
    authority = execution.signed.LeafPopulationArtifactAuthority(binding, directory=tmp_path/'leaf-signed-http',
        access=ContentAccess(os.getuid(), os.getgid()), integrity_key=b'owned-native-HTTP-leaf-key-32-bytes!',
        issuer_id='owned-native-research', key_id='owned-HTTP-leaf-key')
    service = execution.LeafPopulationExecutionService(authority, input_resolver=Resolver(packet))
    reader = query.LeafPopulationExecutionQuery(service); worker = LeafPopulationExecutionWorker(service, tenant_id='tenant-1')
    from app.api import create_app
    from app.api_openapi import _SchemaOnlyStores
    farms = binding.farms.farms; replay = farms.replay
    app = create_app(service.jobs, replay.thermal.holds, replay.thermal.runs, _SchemaOnlyStores(),
        principal_provider=service.jobs.principal_provider, thermal_scenario_store=replay.thermal,
        farm_scenario_service=replay, farm_authoring_service=farms,
        crop_leaf_population_execution_service=service, crop_leaf_population_execution_query=reader)
    clock = {'now': NOW}; protected = protect(app, set(route.SUBMIT_SCOPES+route.READ_SCOPES+route.CANCEL_SCOPES), clock=lambda: clock['now'])
    return service, reader, worker, body, rights, {'packet': packet, 'review': review,
        'parent_review': values[6]}, protected, clock


@contextmanager
def https(app, directory):
    directory.mkdir(mode=0o700); cert = directory/'certificate.pem'; key = directory/'key.pem'
    subprocess.run(['openssl', 'req', '-x509', '-newkey', 'rsa:2048', '-nodes', '-keyout', str(key), '-out', str(cert),
        '-days', '1', '-subj', '/CN=localhost', '-addext', 'subjectAltName=IP:127.0.0.1,DNS:localhost'],
        check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=20)
    key.chmod(0o600); cert.chmod(0o600)
    server = HttpsApiService(app, cert, key, port=0).server(); thread = threading.Thread(target=server.run, daemon=True); thread.start()
    try:
        end = time.monotonic()+10
        while not server.started and thread.is_alive() and time.monotonic()<end: time.sleep(.02)
        assert server.started
        port = server.servers[0].sockets[0].getsockname()[1]; observations = []
        def call(path, method='GET', value=None, *, authenticated=True):
            headers = {'Content-Type': 'application/json'}
            if authenticated: headers['Authorization'] = 'Bearer '+TOKEN.decode()
            raw = execution.signed.reader._canonical(value) if value is not None else None
            connection = http.client.HTTPSConnection('127.0.0.1', port, context=ssl.create_default_context(cafile=str(cert)), timeout=30)
            started = time.monotonic()
            try:
                connection.request(method, path, body=raw, headers=headers); response = connection.getresponse()
                body = response.read(route.MAX_RESPONSE_BYTES+1); assert len(body)<=route.MAX_RESPONSE_BYTES
                elapsed = time.monotonic()-started
                observations.append({'path': path, 'status': response.status, 'seconds': elapsed, 'bytes': len(body)})
                assert elapsed <= 30.0, 'request exceeded existing client30s budget'
                assert response.getheader('Cache-Control') == 'no-store'
                return response.status, json.loads(body)
            finally: connection.close()
        yield call, observations
    finally:
        server.should_exit = True; thread.join(12); assert not thread.is_alive()


def test_actual_https_admission_worker_and_current_replay_original_values(http_setup, login_scope, tmp_path, monkeypatch):
    service, reader, worker, body, rights, packet, app, _ = http_setup
    with https(app, tmp_path/'tls') as (call, observations):
        assert call('/v1/crop-leaf-population-executions', 'POST', body, authenticated=False)[0] == 401
        status, job = call('/v1/crop-leaf-population-executions', 'POST', body); assert status == 202 and job['state'] == 'queued'
        path = '/v1/jobs/'+job['job_id']+'/crop-leaf-population-execution'
        assert call(path)[1]['job']['state'] == 'queued'
        assert call('/v1/crop-leaf-population-executions', 'POST', body)[1]['job_id'] == job['job_id']
        changed = deepcopy(body); changed['rights']['revision'] = 'r2'
        assert call('/v1/crop-leaf-population-executions', 'POST', changed)[0] == 409
        outcome = worker.run_once(job['job_id']); assert outcome.state == 'succeeded'
        growth = leaf_factory.forbid_growth(monkeypatch); before = schema_hash(login_scope[0])
        status, replay = call(path+'/replay'); assert status == 200
        assert replay['result']['result_sha256'] == outcome.result_sha256
        for index, frame in enumerate(replay['replay']['frames']):
            assert execution.signed.reader._canonical(frame) == (PUBLIC/f'frame-{index}.json').read_bytes()
        status, frame = call(path+'/frames/11'); assert status == 200 and frame['frame']['frame'] == replay['replay']['frames'][11]
        assert call(path+'/manifest')[1]['manifest']['manifest'] == replay['replay']['manifest']['manifest']
        assert call(path)[1]['result']['calculated_at'] == replay['result']['calculated_at']
        rights.allowed = False; assert call(path+'/replay')[0] == 422
        rights.allowed = True; assert schema_hash(login_scope[0]) == before and not any(growth.values())
    factory.save('leaf_population-HTTP-normal.json', {'certificate_verified': True, 'actual_SCRAM': True,
        'same_job_idempotency': True, 'original_12_frames': True, 'result': replay['result'], 'requests': observations,
        'query_growth_CLI_calls': growth, 'database_sha256_before_after': [before, schema_hash(login_scope[0])]})


def test_actual_cancel_after_rights_withdrawal_and_late_http_expiry(http_setup, tmp_path, monkeypatch):
    service, reader, worker, body, rights, _, app, clock = http_setup
    with https(app, tmp_path/'tls') as (call, observations):
        status, job = call('/v1/crop-leaf-population-executions', 'POST', body); assert status == 202
        path = '/v1/jobs/'+job['job_id']+'/crop-leaf-population-execution'
        growth = leaf_factory.forbid_growth(monkeypatch)
        original = reader.read
        def late(*a, **kw):
            value = original(*a, **kw); clock['now'] = NOW+timedelta(hours=2); return value
        with monkeypatch.context() as patch:
            patch.setattr(reader, 'read', late)
            assert call(path)[0] == 401
        clock['now'] = NOW; rights.allowed = False
        assert call(path)[0] == 422
        status, canceled = call(path+'/cancel', 'POST'); assert status == 200
        assert canceled['cancel_accepted'] and canceled['job']['state'] == 'canceled'
        assert service.jobs.get_publication('tenant-1', job['job_id']) is None
        rights.allowed = True; assert call(path)[1]['job']['state'] == 'canceled'
        clock['now'] = NOW+timedelta(hours=2); assert call(path)[0] == 401
        assert not any(growth.values())
    factory.save('leaf_population-HTTP-cancel-expiry.json', {'cancel_after_data_rights_withdrawal': True,
        'canceled_no_result': True, 'expired_registry_denied': True, 'late_HTTP_expiry_denied': True,
        'query_growth_CLI_calls': growth, 'requests': observations})


def test_actual_https_late_input_and_parent_change_reject_payload(http_setup, login_scope, tmp_path, monkeypatch):
    service, reader, _, body, _, packet, app, _ = http_setup
    with https(app, tmp_path/'tls') as (call, observations):
        status, job = call('/v1/crop-leaf-population-executions', 'POST', body); assert status == 202
        path = '/v1/jobs/'+job['job_id']+'/crop-leaf-population-execution'
        before = schema_hash(login_scope[0]); growth = leaf_factory.forbid_growth(monkeypatch)
        original = service.current_input; source = service.input_resolver.packet['source_raw']
        seen = []
        def late_source(*args, **kwargs):
            value = original(*args, **kwargs); seen.append(1)
            if len(seen) == 1: service.input_resolver.packet['source_raw'] += b' '
            return value
        with monkeypatch.context() as patch:
            patch.setattr(service, 'current_input', late_source)
            assert call(path)[0] == 422
        service.input_resolver.packet['source_raw'] = source
        seen.clear(); parent_states = []
        def parent_flag(value):
            status = 'revoked' if value else 'accepted_for_software_validation'
            packet['parent_review']['status'] = status; parent_states.append(status)
        def late_parent(*args, **kwargs):
            value = original(*args, **kwargs); seen.append(1)
            if len(seen) == 1: parent_flag(True)
            return value
        try:
            with monkeypatch.context() as patch:
                patch.setattr(service, 'current_input', late_parent)
                assert call(path)[0] == 422
        finally: parent_flag(False)
        assert parent_states == ['revoked', 'accepted_for_software_validation']
        assert before == schema_hash(login_scope[0]) and not any(growth.values())
        assert service.jobs.get_publication('tenant-1', job['job_id']) is None
    factory.save('leaf_population-HTTP-late-input-parent.json', {'late_resolver_source_rejected': True,
        'late_parent_review_revocation_rejected': True, 'parent_review_restored': True,
        'query_growth_CLI_calls': growth, 'requests': observations,
        'database_sha256_before_after': [before, schema_hash(login_scope[0])]})
