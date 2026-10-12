"""Actual unpaused synthetic worker, protected TLS API and product WebGL reference."""
from contextlib import contextmanager
from datetime import datetime, timedelta, timezone
from hashlib import sha256
import http.client
import importlib.util
import ipaddress
import json
import os
from pathlib import Path
import subprocess
import ssl
import sys
import threading
import time
import traceback

import pytest
from pytest import MonkeyPatch
from cryptography import x509
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.x509.oid import NameOID

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'backend/tests'))
import login_database as database_reference
import test_crop_greenhouse_ventilation_prefix_runtime as reference
from test_crop_greenhouse_ventilation_execution_runtime import TOKEN

pytest_plugins = ['test_crop_greenhouse_ventilation_prefix_runtime']
spec = importlib.util.spec_from_file_location('ventilation_browser_observation',
    ROOT/'research/crop-climate-joint-prefix-browser-reference.py')
observation = importlib.util.module_from_spec(spec)
spec.loader.exec_module(observation)


@pytest.fixture
def tls_files(tmp_path):
    directory = tmp_path/'browser-tls'
    directory.mkdir(mode=0o700)
    key = ec.generate_private_key(ec.SECP256R1())
    now = datetime.now(timezone.utc)
    name = x509.Name([x509.NameAttribute(NameOID.COMMON_NAME, 'Synthetic browser API test')])
    certificate = (x509.CertificateBuilder().subject_name(name).issuer_name(name)
        .public_key(key.public_key()).serial_number(x509.random_serial_number())
        .not_valid_before(now-timedelta(minutes=1)).not_valid_after(now+timedelta(minutes=10))
        .add_extension(x509.SubjectAlternativeName([x509.IPAddress(ipaddress.ip_address('127.0.0.1')),
            x509.DNSName('localhost')]), False).sign(key, hashes.SHA256()))
    cert, private = directory/'cert.pem', directory/'key.pem'
    cert.touch(mode=0o600)
    cert.write_bytes(certificate.public_bytes(serialization.Encoding.PEM))
    private.touch(mode=0o600)
    private.write_bytes(key.private_bytes(serialization.Encoding.PEM,
        serialization.PrivateFormat.PKCS8, serialization.NoEncryption()))
    return cert, private, key


@pytest.fixture(scope='module')
def login_database():
    real = subprocess.run
    startup = []
    binary = str(Path(os.environ['OSSF_TEST_PG_BIN'])/'pg_ctl')
    def small_cluster(args, *a, **kw):
        if isinstance(args, list) and args[0] == binary and 'start' in args:
            args = list(args)
            directory = Path(args[args.index('-D')+1])
            assert directory.name == 'data' and directory.parent.name.startswith('ossf-login-pg-')
            args[args.index('-o')+1] += (' -c shared_buffers=16MB -c max_connections=32'
                ' -c work_mem=1MB -c maintenance_work_mem=16MB')
            startup.append(True)
        return real(args, *a, **kw)
    with MonkeyPatch.context() as patch:
        patch.setattr(subprocess, 'run', small_cluster)
        generator = database_reference.login_database.__wrapped__()
        value = next(generator)
        try:
            assert len(startup) == 1
            yield value
        finally:
            try:
                next(generator)
            except StopIteration:
                pass


@contextmanager
def actual_api(runtime, directory):
    server = runtime.service.server()
    inventory = reference.fd_inventory()
    diagnostics = MonkeyPatch()
    diagnostic_mode = os.environ.get('OSSF_LIVE_BROWSER_DIAGNOSTICS')
    if diagnostic_mode in ('1', 'cancel'):
        from app import api_crop_greenhouse_ventilation_execution as wire
        original_pool = wire.run_in_threadpool
        failures = []
        async def observed_pool(action, *args, **kwargs):
            try:
                return await original_pool(action, *args, **kwargs)
            except Exception as error:
                failures.append(True)
                observation.save(directory/('exception-'+str(len(failures))+'.private.json'),
                    {'action': action.__qualname__, 'exception': type(error).__name__,
                     'sqlstate': getattr(error, 'sqlstate', None),
                     'frames': [{'file': Path(f.filename).name, 'line': f.lineno, 'function': f.name}
                        for f in traceback.extract_tb(error.__traceback__)]})
                raise
        def routed_pool(action, *args, **kwargs):
            if diagnostic_mode == 'cancel' and '.cancel.' not in action.__qualname__:
                return original_pool(action, *args, **kwargs)
            return observed_pool(action, *args, **kwargs)
        diagnostics.setattr(wire, 'run_in_threadpool', routed_pool)
    observed = observation.Observe(server.config.app, directory)
    server.config.app = observed
    thread = threading.Thread(target=server.run, daemon=True)
    thread.start()
    try:
        deadline = time.monotonic()+15
        while not server.started:
            assert thread.is_alive() and time.monotonic() < deadline
            time.sleep(.02)
        yield server.servers[0].sockets[0].getsockname()[1], observed
    finally:
        server.should_exit = True
        thread.join(15)
        assert not thread.is_alive()
        diagnostics.undo()
        assert reference.fd_inventory() == inventory


@contextmanager
def frontend(c, api_port, directory):
    nginx = Path(os.environ['OSSF_LIVE_BROWSER_NGINX'])
    assert sha256(nginx.read_bytes()).hexdigest() == '54150b1a96bd5e41b87c2ce87d27db22a6668e22a9f6778f0f9d5e05fd858f4a'
    dist = Path(os.environ['OSSF_LIVE_BROWSER_DIST'])
    port = observation.free_port()
    (directory/'logs').mkdir(mode=0o700)
    template = (ROOT/'web/nginx.conf').read_text()
    changes = {'/tmp/nginx.pid': str(directory/'nginx.pid'),
        '/etc/nginx/mime.types': str(nginx.parents[1]/'conf/mime.types'),
        'listen 8444 ssl;': f'listen 127.0.0.1:{port};',
        '/run/operator/web/cert.pem': str(c.config.certificate),
        '/run/operator/web/key.pem': str(c.config.private_key),
        '/run/operator/web/api-ca.pem': str(c.config.certificate),
        '/usr/share/nginx/html': str(dist),
        'https://127.0.0.1:8443': f'https://127.0.0.1:{api_port}'}
    for name in ('client', 'proxy', 'fastcgi', 'uwsgi', 'scgi'):
        changes['/tmp/'+name+'-temp'] = str(directory/(name+'-temp'))
    for old, new in changes.items():
        assert old in template
        template = template.replace(old, new)
    config = directory/'nginx.conf'
    config.touch(mode=0o600)
    config.write_text(template)
    with (directory/'nginx.private.log').open('xb') as log:
        os.fchmod(log.fileno(), 0o600)
        process = subprocess.Popen([str(nginx), '-p', str(directory)+'/', '-c',
            str(config), '-g', 'daemon off;'], stdin=subprocess.DEVNULL,
            stdout=log, stderr=subprocess.STDOUT)
        try:
            deadline = time.monotonic()+10
            import urllib.request
            while True:
                assert process.poll() is None and time.monotonic() < deadline
                try:
                    with urllib.request.urlopen(f'http://127.0.0.1:{port}/', timeout=1) as reply:
                        assert reply.status == 200
                    break
                except OSError:
                    time.sleep(.05)
            yield f'http://127.0.0.1:{port}'
        finally:
            if process.poll() is None:
                process.terminate()
            process.wait(timeout=10)


def check_frame(frame, record):
    value = record['value']
    assert frame['at'] == record['time']['at'] == frame['scene_at'] == frame['chart_at']
    assert frame['draw_calls'] > 0
    assert abs(frame['leaf_surface_area']-value['derived']['leaf_area_index']['value']) < 1e-8
    assert [q['value'] for q in frame['drawing']['carbon']] == [q['value'] for q in value['cohort_state']['fruit_carbohydrate']]
    assert [q['value'] for q in frame['drawing']['number']] == [q['value'] for q in value['cohort_state']['fruit_number']]
    assert frame['cohorts'] == [[a['value'], b['value']] for a, b in zip(
        value['cohort_state']['fruit_carbohydrate'], value['cohort_state']['fruit_number'], strict=True)]
    assert frame['quantities'] == {**value['plant_state'], **value['climate_state'], **value['derived']}
    assert frame['ventilation'] == value['ventilation']
    assert frame['ledgers'] == value['integrated_transfers'] and len(frame['ledgers']) == 25
    assert frame['residuals'] == value['balance_residuals'] and len(frame['residuals']) == 10


@reference.LOGIN
@pytest.mark.parametrize('setup,mode', [(None, 'completed'), ('hold', 'hold'), (None, 'cancel')], indirect=['setup'])
def test_actual_unpaused_product_browser(prefix_native, tmp_path, monkeypatch, mode):
    c = prefix_native
    directory = Path(os.environ['OSSF_VENTILATION_PREFIX_RUNTIME_EVIDENCE'])/('browser-'+mode)
    directory.mkdir(mode=0o700)
    request = directory/'request.private.json'
    request.touch(mode=0o600)
    request.write_bytes(c.raw)
    pack, factory = reference.unpaused_consumer(c, tmp_path)
    assert factory.exists() and not (tmp_path/'block').exists()
    browser = None
    try:
        with actual_api(c.prefix_runtime, directory) as (port, observed), frontend(c, port, directory) as origin:
            context = directory/'context.private.json'
            observation.save(context, {'origin': origin, 'mode': mode, 'token': TOKEN.decode(),
                'request_file': str(request), 'directory': str(directory),
                'playwright': str(ROOT/'web/node_modules/playwright-core/index.mjs')})
            with reference.consumer.legacy.process_consumer(tmp_path, 'joint_operator:build') as (worker, events, errors):
                with (directory/'browser.private.log').open('xb') as log:
                    os.fchmod(log.fileno(), 0o600)
                    browser = subprocess.Popen(['nice', '-n', '19', 'node', '--expose-gc',
                        '--max-old-space-size=64', '--max-semi-space-size=1',
                        str(ROOT/'research/crop-greenhouse-ventilation-live-browser-reference.mjs'), str(context)],
                        stdin=subprocess.DEVNULL, stdout=log, stderr=subprocess.STDOUT)
                    deadline = time.monotonic()+360
                    while browser.poll() is None:
                        assert worker.poll() is None and time.monotonic() < deadline
                        for name, allowed in (('rights-revoke', False), ('rights-restore', True)):
                            if (directory/name).exists() and not (directory/(name+'-ack')).exists():
                                c.value[5].allowed = allowed
                                (directory/(name+'-ack')).touch(mode=0o600)
                        time.sleep(.1)
                    assert browser.returncode == 0, 'see private browser log'
                reference.consumer.legacy.wait_for(lambda: bool(list(tmp_path.glob('attempt-*.private.json'))), worker, timeout=60)
            assert worker.returncode == 0 and errors == [''] and events[-1]['event'] == 'stopped'
            result = json.loads((directory/'browser-result.private.json').read_bytes())
            assert result['mode'] == mode and result['running_frames'] and not result['pageerrors']
            attempts = reference.proofs(tmp_path)
            assert attempts[-1]['state'] == {'completed': 'succeeded', 'hold': 'hold', 'cancel': 'canceled'}[mode]
            bodies = [(r, json.loads((directory/r['wire_file']).read_bytes())) for r in observed.responses
                if r['status'] == 200 and r['path'].startswith('/v1/')]
            for frame in result['running_frames']:
                sample_pages = [body for wire, body in bodies if wire['path'].endswith('/prefix/samples')
                    and body['reference']['selector'] == frame['reference']['selector']]
                matches = [row for page in sample_pages for row in page['page']['records'] if row['time']['at'] == frame['at']]
                assert matches and any(frame['reference'] == page['reference'] for page in sample_pages)
                assert any(body['prefix_status'] == 'accepted' and body['job']['state'] == 'simulating'
                    and body['reference']['selector'] == frame['reference']['selector']
                    for wire, body in bodies if wire['path'].endswith('/prefix'))
                check_frame(frame, matches[0])
            lookup = {'job_id': result['job_id'], 'farm': json.loads(c.raw)['farm']}
            with monkeypatch.context() as patch:
                calls = reference.progress.forbid(patch)
                connection = http.client.HTTPSConnection('127.0.0.1', port,
                    context=ssl.create_default_context(cafile=str(c.config.certificate)), timeout=60)
                try:
                    connection.request('GET', '/v1/jobs/'+lookup['job_id']+'/crop-greenhouse-ventilation-execution',
                        headers={'Authorization': 'Bearer '+TOKEN.decode()})
                    reply = connection.getresponse()
                    assert reply.status == 200 and reply.getheader('Cache-Control') == 'no-store'
                    outcome = json.loads(reply.read())
                finally:
                    connection.close()
                if mode == 'cancel':
                    assert any(wire['path'].endswith('/cancel') and body.get('cancel_accepted') is True
                        for wire, body in bodies)
                    assert outcome['job']['state'] == 'canceled' and outcome['result'] is None
                    assert result['cancel_accepted'] and result['scene_cleared']
                else:
                    selected = outcome['result']
                    assert selected['status'] == mode and selected['result_id'] == result['result_id']
                    terminal = json.loads(reference.current.VentilationCurrentQuery(c.worker.results).read(
                        'tenant-1', selected['result_id'], lookup['farm'], view='samples', offset=0, limit=64))
                    rows = terminal['page']['records']
                    for frame in result['running_frames']:
                        check_frame(frame, next(row for row in rows if row['time']['at'] == frame['at']))
                    check_frame(result['terminal_frame'], rows[0])
                    check_frame(result['restored_frame'], rows[0])
                    assert result['reconnected'] and result['rights_cleared'] and result['rights_restored']
                assert not any(calls.values())
            observation.save(directory/'acceptance.private.json', {'scope': 'actual_unpaused_synthetic_worker_TLS_API_product_WebGL',
                'mode': mode, 'actual_SCRAM': True, 'verified_TLS_proxy': True, 'test_pause': False,
                'fixture_steps': 64, 'fixture_simulated_seconds': 128, 'chunk_budget': 8,
                'browser': result, 'attempts': attempts, 'events': events, 'responses': observed.responses,
                'read_calculation_calls': calls, 'worker_exit': worker.returncode, 'browser_exit': browser.returncode,
                'real_farm_runs': 0, 'G0_G4': 'not_assessed'})
    finally:
        c.value[5].allowed = True
        if browser is not None and browser.poll() is None:
            browser.terminate()
            browser.wait(timeout=10)
        pack.unlink(missing_ok=True)
        (tmp_path/'proof.private.json').unlink(missing_ok=True)
