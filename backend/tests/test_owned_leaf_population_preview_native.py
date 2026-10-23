"""Launch the owned preview executable against actual SCRAM with verified HTTPS."""
from contextlib import contextmanager
from datetime import datetime, timedelta, timezone
from hashlib import sha256
import http.client
import json
import os
from pathlib import Path
import signal
import socket
import ssl
import subprocess
import sys
import time

import pytest

from app import api_crop_leaf_population_execution as leaf_wire
from login_database import login_database, login_scope
from test_api_crop_leaf_population_execution import TOKEN
from test_crop_leaf_population_execution_worker_native import retained_rows
from test_crop_leaf_population_signed_artifact_native import PUBLIC
from test_crop_morphology_signed_artifact_native import final_cleanup
import morphology_farm_factory as factory
import test_crop_leaf_population_farm_binding_native as leaf_factory
from test_owned_leaf_population_preview import preview


ROOT = Path(__file__).resolve().parents[2]
pytestmark = pytest.mark.parametrize('login_scope', [{'market_calculation': True, 'market_source_storage': True,
    'thermal_scenario_storage': True, 'break_even_calculation': True, 'crop_cycle_result_storage': True}], indirect=True)


def write(directory, name, value):
    raw = value if type(value) is bytes else preview.execution.signed.reader._canonical(value)
    return factory.private_file(directory, name, raw)


def replace(path, raw):
    path = Path(path); temporary = path.with_name(path.name+'.pending')
    with temporary.open('xb') as f:
        os.fchmod(f.fileno(), 0o400); f.write(raw); f.flush(); os.fsync(f.fileno())
    os.replace(temporary, path)


@pytest.fixture
def executable(login_scope, tmp_path, monkeypatch):
    monkeypatch.setattr(factory.SyntheticMorphologyRights, 'policy_version', 'owned-morphology-preview-rights-v1')
    values = leaf_factory.registered_leaf_services(login_scope, tmp_path, monkeypatch)
    binding, body, packet, parent_body, parent_packet, review, parent_review, principal, *_ = values
    principal['scopes'].add('simulation_execute')
    directory = tmp_path/'operator'
    previous = factory.fresh_config(binding.farms, principal, parent_body, parent_packet, parent_review, b'', directory)
    p = json.loads(Path(previous).read_bytes())
    p.update(mode='owned_synthetic_morphology_preview_v1', resolver_version='owned-morphology-immutable-input-resolver-v1',
        preview={'label': 'Owned retrospective stem', 'request': parent_body},
        review_file=write(directory, 'stem-review.private', parent_review),
        rights_file=write(directory, 'stem-rights.private', {'schema_version': 'owned-morphology-preview-rights-v1',
            'status': 'allowed_for_software_validation', 'tenant_id': 'tenant-1',
            'declaration': parent_body['rights'], 'source_sha256': parent_body['input']['source_sha256']}))
    parent = binding.parent_authority
    p['signed'] = {'directory': str(parent.directory), 'key_file': write(directory, 'stem-signed-key.private', parent.integrity_key),
        'issuer_id': parent.issuer_id, 'key_id': parent.key_id}
    now = datetime.now(timezone.utc)
    scopes = set(leaf_wire.SUBMIT_SCOPES+leaf_wire.READ_SCOPES+leaf_wire.CANCEL_SCOPES)|{'simulation_execute'}
    p['auth'] = {'token_file': write(directory, 'token.private', TOKEN), 'tenant_id': 'tenant-1', 'scopes': sorted(scopes),
        'not_before': (now-timedelta(minutes=1)).isoformat(), 'expires_at': (now+timedelta(hours=1)).isoformat()}
    cert = directory/'certificate.pem'; key = directory/'TLS-key.pem'
    subprocess.run(['openssl', 'req', '-x509', '-newkey', 'rsa:2048', '-nodes', '-keyout', str(key), '-out', str(cert),
        '-days', '1', '-subj', '/CN=localhost', '-addext', 'subjectAltName=IP:127.0.0.1,DNS:localhost'],
        check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=20)
    key.chmod(0o400); cert.chmod(0o400)
    with socket.socket() as sock:
        sock.bind(('127.0.0.1', 0)); port = sock.getsockname()[1]
    p['TLS'] = {'certificate': str(cert), 'key': str(key), 'port': port}
    p['leaf_population'] = {'schema_version': preview.VERSION, 'request': body, 'label': 'Owned retrospective leaf population',
        'input_key_file': write(directory, 'leaf-input-key.private', binding.input_authority.integrity_key),
        'review_file': write(directory, 'leaf-review.private', review),
        'rights_file': write(directory, 'leaf-rights.private', {'schema_version': preview.RIGHTS_VERSION,
            'status': 'allowed_for_software_validation', 'tenant_id': 'tenant-1',
            'declaration': body['rights'], 'source_sha256': body['input']['source_sha256']}),
        'issuer_id': binding.input_authority.issuer_id, 'key_id': binding.input_authority.key_id,
        'packet_files': {name: write(directory, 'leaf-'+name+'.private', raw) for name,raw in packet.items()},
        'signed': {'directory': str(tmp_path/'new-leaf-signed'),
            'key_file': write(directory, 'leaf-signed-key.private', b'owned-leaf-preview-result-key-32-bytes!'),
            'issuer_id': 'owned-software', 'key_id': 'owned-leaf-preview-result-key-v1'}}
    files = ['research/serve-owned-morphology-preview.py', 'research/owned_leaf_population_preview.py',
        'backend/app/deterministic_work.py', 'backend/app/deterministic_job_discovery.py']
    p['frozen_code_sha256'] = {str(ROOT/name):sha256((ROOT/name).read_bytes()).hexdigest() for name in files}
    config = write(directory, 'runtime.private.json', p)
    return p, config, binding, body


@contextmanager
def server(executable, tmp_path, name, *, stop_signal=signal.SIGTERM):
    p, config, *_ = executable; requests = []; log_path = tmp_path/(name+'.private.log')
    env = {**os.environ, 'PYTHONPATH': str(ROOT/'backend')+':'+str(ROOT/'backend/tests'), 'PYTHONDONTWRITEBYTECODE': '1'}
    process = None
    with log_path.open('xb') as log:
        os.fchmod(log.fileno(), 0o600)
        process = subprocess.Popen([sys.executable, '-B', str(ROOT/'research/serve-owned-morphology-preview.py'),
            '--config', config], cwd=ROOT, env=env, stdin=subprocess.DEVNULL, stdout=log, stderr=subprocess.STDOUT)
        def call(path, method='GET', value=None, *, authenticated=True):
            connection = http.client.HTTPSConnection('127.0.0.1', p['TLS']['port'], timeout=30,
                context=ssl.create_default_context(cafile=p['TLS']['certificate']))
            headers = {'Content-Type': 'application/json'}
            if authenticated: headers['Authorization'] = 'Bearer '+TOKEN.decode()
            started = time.monotonic()
            try:
                connection.request(method, path, body=None if value is None else preview.execution.signed.reader._canonical(value), headers=headers)
                response = connection.getresponse(); raw = response.read(2*1024**2+1)
                elapsed = time.monotonic()-started
                assert len(raw)<=2*1024**2 and elapsed<=30 and response.getheader('Cache-Control')=='no-store'
                requests.append({'path':path, 'status':response.status, 'bytes':len(raw), 'seconds':elapsed})
                return response.status, json.loads(raw)
            finally: connection.close()
        try:
            deadline = time.monotonic()+30
            while True:
                assert process.poll() is None, 'owned preview exited before ready'
                try:
                    assert call('/leaf-preview-input', authenticated=False)[0] == 401
                    break
                except ConnectionRefusedError:
                    assert time.monotonic()<deadline, 'owned preview startup timed out'; time.sleep(.05)
            yield call, requests
        finally:
            if process.poll() is None:
                process.send_signal(stop_signal)
                try: process.wait(timeout=45)
                except subprocess.TimeoutExpired: process.kill(); process.wait(timeout=5)
            assert process.returncode == 0, 'owned preview did not shut down cleanly'
    assert log_path.stat().st_size < 512*1024
    events = []
    for line in log_path.read_text().splitlines():
        try: events.append(json.loads(line))
        except ValueError: pass
    assert not any(v.get('event')=='consumer_hold' for v in events)
    starts = [v for v in events if v.get('event')=='owned_preview_starting']; assert len(starts)==1
    expected = ['leaf-population-execution-input-v1','morphology-execution-input-v1'] if p.get('leaf_population') else ['morphology-execution-input-v1']
    assert starts[0]['consumer_input_versions']==expected
    stopped = [v for v in events if v.get('event')=='owned_preview_stopped']
    assert stopped==[{'event':'owned_preview_stopped','consumers_stopped':True,'consumer_count':len(expected)}]


def wait_terminal(binding, job_id, maximum=240):
    deadline = time.monotonic()+maximum
    while True:
        row = binding.jobs.get_job('tenant-1', job_id)
        if row['state'] in ('succeeded','failed','hold','canceled'): return row
        assert time.monotonic()<deadline, 'automatic owned computation did not finish'; time.sleep(.5)


def test_actual_executable_automatic_leaf_and_same_result_after_cold_restart(executable, login_scope, tmp_path):
    p, _, binding, body = executable; before = retained_rows(login_scope[0]); observations = []
    with server(executable, tmp_path, 'first') as (call, requests):
        status, choice = call('/leaf-preview-input'); assert status==200 and choice['request']==body
        status, job = call('/v1/crop-leaf-population-executions', 'POST', choice['request']); assert status==202
        job_id = job['job_id']; path = '/v1/jobs/'+job_id+'/crop-leaf-population-execution'
        row = wait_terminal(binding, job_id); assert row['state']=='succeeded' and row['attempt_count']==1
        status, result = call(path+'/replay'); assert status==200 and result['job']['state']=='succeeded'
        frames = result['replay']['frames']; assert len(frames)==12 and sum(len(f['leaves']) for f in frames)==52
        for index,frame in enumerate(frames):
            assert preview.execution.signed.reader._canonical(frame)==(PUBLIC/f'frame-{index}.json').read_bytes()
        old = '/v1/jobs/'+body['parent']['job_id']+'/crop-morphology-execution'
        status, parent = call(old); assert status==200 and parent['result']['result_sha256']==body['parent']['result_sha256']
        observations.extend(requests)
    saved_rows = retained_rows(login_scope[0]); assert before==retained_rows(login_scope[0], (job_id,))
    with server(executable, tmp_path, 'cold') as (call, requests):
        status, restored = call(path+'/replay'); assert status==200
        assert restored['result']==result['result'] and restored['replay']==result['replay']
        observations.extend(requests)
    assert saved_rows==retained_rows(login_scope[0])
    factory.save('leaf-preview-executable-normal.json', {'actual_SCRAM':True, 'certificate_verified':True,
        'both_exact_consumers':True, 'one_completed_attempt':True, 'result':result['result'],
        'original_12_frames':True, 'original_52_leaf_areas':sum(len(f['leaves']) for f in frames),
        'same_result_after_cold_restart':True, 'cold_restart_POST_count':0,
        'retained_25_table_rows_sha256':before[0], 'requests':observations, 'user_runtime_deployed':False,
        'actual_farm_Runs':0, 'G0_G4':'not_assessed'})


def test_actual_executable_current_file_holds_cancel_without_publication(executable, login_scope, tmp_path):
    p, _, binding, body = executable; before = retained_rows(login_scope[0]); cfg = p['leaf_population']
    original_rights = Path(cfg['rights_file']).read_bytes(); original_source = Path(cfg['packet_files']['source_raw']).read_bytes()
    with server(executable, tmp_path, 'holds') as (call, requests):
        changed = json.loads(original_rights); changed['status']='revoked'
        replace(cfg['rights_file'], preview.execution.signed.reader._canonical(changed))
        assert call('/leaf-preview-input')[0]==422
        assert call('/v1/crop-leaf-population-executions','POST',body)[0]==422
        replace(cfg['rights_file'], original_rights)
        replace(cfg['packet_files']['source_raw'], original_source+b' ')
        assert call('/leaf-preview-input')[0]==422
        replace(cfg['packet_files']['source_raw'], original_source)
        status, job = call('/v1/crop-leaf-population-executions','POST',body); assert status==202
        job_id=job['job_id']; path='/v1/jobs/'+job_id+'/crop-leaf-population-execution'
        replace(cfg['rights_file'], preview.execution.signed.reader._canonical(changed))
        status, canceled=call(path+'/cancel','POST'); assert status==200 and canceled['cancel_accepted'] is True
        row=wait_terminal(binding,job_id); assert row['state']=='canceled'
        assert binding.jobs.get_publication('tenant-1',job_id) is None
        replace(cfg['rights_file'], original_rights)
        assert call(path)[1]['job']['state']=='canceled'
    assert before==retained_rows(login_scope[0],(job_id,))
    factory.save('leaf-preview-executable-holds.json', {'actual_SCRAM':True, 'certificate_verified':True,
        'current_rights_and_source_file_holds':True,'cancel_after_rights_withdrawal':True,'no_publication':True,
        'retained_25_table_rows_sha256':before[0], 'requests':requests, 'user_runtime_deployed':False})


def test_actual_executable_without_leaf_option_keeps_stem_only_and_handles_SIGINT(executable, login_scope, tmp_path):
    p, _, binding, body = executable; before = retained_rows(login_scope[0])
    p.pop('leaf_population'); config=write(Path(p['review_file']).parent,'runtime-default.private.json',p)
    default=(p,config,binding,body)
    with server(default,tmp_path,'default',stop_signal=signal.SIGINT) as (call,requests):
        status, parent_choice=call('/preview-input'); assert status==200 and parent_choice['request']==p['preview']['request']
        assert call('/leaf-preview-input')[0]==404
        status,parent=call('/v1/jobs/'+body['parent']['job_id']+'/crop-morphology-execution')
        assert status==200 and parent['result']['result_sha256']==body['parent']['result_sha256']
    assert before==retained_rows(login_scope[0])
    factory.save('leaf-preview-executable-default.json', {'actual_SCRAM':True,'certificate_verified':True,
        'one_original_stem_consumer':True,'leaf_option_missing_not_exposed':True,'SIGINT_joined_all_consumers':True,
        'retained_25_table_rows_sha256':before[0],'requests':requests,'user_runtime_deployed':False})
