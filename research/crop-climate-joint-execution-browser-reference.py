"""Isolated real SCRAM/TLS/consumer/product-browser execution evidence.

Synthetic test inputs and a bounded checkpoint observation pause are used only
by this reference runner. It does not provide a deployed operator service.
"""
from contextlib import contextmanager
from hashlib import sha256
from pathlib import Path
import json
import gc
import os
import select
import signal
import socket
import ssl
import subprocess
import sys
import threading
import time
import urllib.request
import urllib.error

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT/'backend'), str(ROOT/'backend/tests')]
import pytest
from cryptography import x509
from cryptography.hazmat.primitives import hashes, serialization
from test_api_serve import tls_files as original_tls_files
from test_crop_climate_joint_execution_runtime import (
    native, execution_config, joint_config, private_config, database_cleanup,
    setup, profiles, login_database, original_login_scope, login_scope, authoring, farm_setup)
import test_crop_climate_joint_execution_runtime as r


def save(path, value):
    with path.open('x') as output:
        os.fchmod(output.fileno(), 0o400)
        json.dump(value, output, sort_keys=True); output.flush(); os.fsync(output.fileno())


@pytest.fixture
def tls_files(original_tls_files):
    cert, private, key = original_tls_files
    original = x509.load_pem_x509_certificate(cert.read_bytes())
    names = list(original.extensions.get_extension_for_class(x509.SubjectAlternativeName).value)
    certificate = (x509.CertificateBuilder().subject_name(original.subject).issuer_name(original.issuer)
        .public_key(key.public_key()).serial_number(original.serial_number)
        .not_valid_before(original.not_valid_before_utc).not_valid_after(original.not_valid_after_utc)
        .add_extension(x509.SubjectAlternativeName([*names, x509.DNSName('localhost')]), False)
        .sign(key, hashes.SHA256()))
    cert.write_bytes(certificate.public_bytes(serialization.Encoding.PEM))
    return cert, private, key


@contextmanager
def served(server, root, certificate, private_key):
    thread = threading.Thread(target=server.run, daemon=True); thread.start()
    frontend = log = None
    try:
        deadline = time.monotonic()+10
        while not server.started:
            assert thread.is_alive() and time.monotonic() < deadline; time.sleep(.01)
        api_port = server.servers[0].sockets[0].getsockname()[1]
        prep = json.loads(Path(os.environ['OSSF_VERIFIED_NGINX_PREPARATION']).read_bytes())
        binary = Path(prep['binary'])
        assert prep['official_signature_valid'] and sha256(binary.read_bytes()).hexdigest() == prep['binary_sha256']
        dist = Path(os.environ['OSSF_JOINT_EXECUTION_BROWSER_DIST']); assert (dist/'index.html').is_file()
        directory = root/'frontend'; directory.mkdir(mode=0o700); (directory/'logs').mkdir(mode=0o700)
        with socket.socket() as probe:
            probe.bind(('127.0.0.1', 0)); port = probe.getsockname()[1]
        template = (ROOT/'web/nginx.conf').read_text()
        mapping = {'/tmp/nginx.pid': str(directory/'nginx.pid'), '/etc/nginx/mime.types': str(binary.parents[1]/'conf/mime.types'),
            'listen 8444 ssl;': f'listen 127.0.0.1:{port} ssl;', '/run/operator/web/cert.pem': str(certificate),
            '/run/operator/web/key.pem': str(private_key), '/run/operator/web/api-ca.pem': str(certificate),
            '/usr/share/nginx/html': str(dist), 'https://127.0.0.1:8443': f'https://127.0.0.1:{api_port}'}
        for name in ('client', 'proxy', 'fastcgi', 'uwsgi', 'scgi'):
            mapping['/tmp/'+name+'-temp'] = str(directory/(name+'-temp'))
        for old, new in mapping.items():
            assert old in template; template = template.replace(old, new)
        config = directory/'nginx.conf'; config.write_text(template); config.chmod(0o600)
        log = (root/'nginx.private.log').open('xb'); os.fchmod(log.fileno(), 0o600)
        frontend = subprocess.Popen([str(binary), '-p', str(directory)+'/', '-c', str(config), '-g', 'daemon off;'],
            stdin=subprocess.DEVNULL, stdout=log, stderr=subprocess.STDOUT)
        deadline = time.monotonic()+10
        while True:
            assert frontend.poll() is None and time.monotonic() < deadline
            try:
                with socket.create_connection(('127.0.0.1', port), timeout=.5): break
            except OSError: time.sleep(.05)
        origin = f'https://127.0.0.1:{port}'
        with pytest.raises(urllib.error.URLError) as rejected:
            urllib.request.urlopen(origin+'/', timeout=5)
        assert isinstance(rejected.value.reason, ssl.SSLCertVerificationError)
        with urllib.request.urlopen(origin+'/', context=ssl.create_default_context(cafile=str(certificate)), timeout=5) as response:
            assert response.status == 200 and sha256(response.read()).digest() == sha256((dist/'index.html').read_bytes()).digest()
        yield origin
    finally:
        if frontend is not None:
            frontend.terminate(); frontend.wait(timeout=10)
        if log is not None: log.close()
        server.should_exit = True; thread.join(15)
        assert not thread.is_alive()


def checkpoint_pause(factory):
    source = factory.read_text(); assert source.count('chunk_budget=128') == 1
    source = source.replace('chunk_budget=128', 'chunk_budget=16')
    marker = '    return loop\n'; assert source.endswith(marker)
    extra = '''    confirm=worker._confirm
    def trace(phase,**metadata):
        with (directory/'worker-trace.private.jsonl').open('a') as f:
            __import__('os').fchmod(f.fileno(),0o600)
            f.write(json.dumps({'phase':phase,'steps_called':calls['step'],**metadata})+'\\n');f.flush();__import__('os').fsync(f.fileno())
    original_before=worker._before
    def traced_before(lease):
        trace('before_enter');value=original_before(lease);trace('before_return');return value
    worker._before=traced_before
    original_adopt=worker._adopt
    def traced_adopt(raw):
        trace('adopt_enter');value=original_adopt(raw);trace('adopt_return');return value
    worker._adopt=traced_adopt
    advance=worker.server.advance
    def traced_advance(*args,**kwargs):
        try:return advance(*args,**kwargs)
        except BaseException as error:
            stack=[];frame=error.__traceback__
            while frame is not None:
                stack.append({'file':Path(frame.tb_frame.f_code.co_filename).name,'function':frame.tb_frame.f_code.co_name,'line':frame.tb_lineno})
                frame=frame.tb_next
            trace('advance_exception',exception=type(error).__name__,stack=stack)
            raise
    worker.server.advance=traced_advance
    def observed_confirm(lease):
        trace('confirm_enter')
        value=confirm(lease)
        checkpoint=value['checkpoint'];trace('confirm_return',accepted_steps=checkpoint['steps'],status=checkpoint['status'])
        if checkpoint['steps']>0 and checkpoint['status']=='yielded' and (directory/'progress-block').exists():
            path=directory/'checkpoint-paused'
            with path.open('x') as f:
                __import__('os').fchmod(f.fileno(),0o600)
                json.dump({'steps':checkpoint['steps'],'planned_steps':checkpoint['planned_steps']},f)
            while (directory/'progress-block').exists():
                if stop_flag.is_set():(directory/'stop-observed').touch(mode=0o600)
                time.sleep(.02)
        return value
    worker._confirm=observed_confirm
'''
    factory.write_text(source[:-len(marker)]+extra+marker)


@r.LOGIN
@pytest.mark.parametrize('setup,mode', [(None, 'completed'), ('hold', 'hold'), (None, 'cancel')], indirect=['setup'])
def test_real_execution_browser(native, tmp_path, monkeypatch, mode):
    c = native; root = Path(os.environ['OSSF_JOINT_EXECUTION_BROWSER_EVIDENCE'])
    request_file = root/'request.private.json'
    with request_file.open('xb') as output:
        os.fchmod(output.fileno(), 0o600); output.write(c.raw)
    pack, factory = r.consumer.joint_factory(c.worker, c.value, tmp_path)
    checkpoint_pause(factory)
    (tmp_path/'block').touch(mode=0o600); (tmp_path/'progress-block').touch(mode=0o600)
    factory_sha = sha256(factory.read_bytes()).hexdigest()
    captured = []; original_read = c.runtime.joint_execution_query.read
    def measured_read(*args):
        with monkeypatch.context() as patch:
            counters = r.progress.forbid(patch); start = time.monotonic()
            raw = original_read(*args); assert not any(counters.values())
        captured.append({'raw': raw, 'seconds': time.monotonic()-start, 'calls': counters})
        return raw
    monkeypatch.setattr(c.runtime.joint_execution_query, 'read', measured_read)
    stored = []; original_saved = r.current.JointCropClimateCurrentQuery.read
    def measured_saved(query, *args, **kwargs):
        with monkeypatch.context() as patch:
            counters = r.progress.forbid(patch); start = time.monotonic()
            raw = original_saved(query, *args, **kwargs); assert not any(counters.values())
        stored.append({'raw': raw, 'seconds': time.monotonic()-start, 'calls': counters})
        return raw
    monkeypatch.setattr(r.current.JointCropClimateCurrentQuery, 'read', measured_saved)
    server = c.runtime.service.server()
    browser = errors = None; stages = []; gc.collect(); inventory = r.fd_inventory()
    try:
        with served(server, root, c.config.certificate, c.config.private_key) as origin:
            errors = (root/'browser.private.log').open('xb'); os.fchmod(errors.fileno(), 0o600)
            env = dict(os.environ)
            for key in ('NODE_EXTRA_CA_CERTS', 'NODE_TLS_REJECT_UNAUTHORIZED', 'NODE_OPTIONS'): env.pop(key, None)
            browser = subprocess.Popen(['nice', '-n', '19', 'node', '--max-old-space-size=64', '--max-semi-space-size=2',
                str(ROOT/'research/crop-climate-joint-execution-browser-reference.mjs')], cwd=ROOT/'web', env=env,
                stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=errors, text=True)
            def send(value):
                browser.stdin.write(json.dumps(value)+'\n'); browser.stdin.flush()
            def receive(stage):
                assert select.select([browser.stdout], [], [], 60)[0], 'browser observation timeout: '+stage
                raw = browser.stdout.readline(); assert raw, 'browser ended before: '+stage
                value = json.loads(raw); assert value['stage'] == stage
                stages.append(value); return value
            send({'origin': origin, 'token': r.TOKEN.decode(), 'certificate': str(c.config.certificate),
                'request_file': str(request_file), 'root': str(root), 'mode': mode})
            admitted = receive('admitted'); job = admitted['job_id']
            assert c.worker.jobs.get_job('tenant-1', job)['state'] == 'queued'
            assert job not in pack.read_text()+factory.read_text()
            with r.consumer.legacy.process_consumer(tmp_path, 'joint_operator:build') as (process, events, worker_errors):
                try:
                    r.consumer.legacy.wait_for(lambda: (tmp_path/'claimed').exists(), process, timeout=20)
                    send({'stage': 'claimed'}); receive('running_seen')
                    if mode == 'cancel':
                        c.value[-1].allowed = False; send({'stage': 'rights_revoked'}); receive('cancel_accepted')
                    else:
                        (tmp_path/'block').unlink()
                        r.consumer.legacy.wait_for(lambda: (tmp_path/'checkpoint-paused').exists(), process, timeout=45)
                        checkpoint = json.loads((tmp_path/'checkpoint-paused').read_bytes())
                        send({'stage': 'checkpoint_ready', **checkpoint}); middle = receive('checkpoint_seen')
                        assert any(json.loads(item['raw'])['checkpoint'] == middle['checkpoint'] for item in captured)
                    (tmp_path/('block' if mode == 'cancel' else 'progress-block')).unlink()
                    deadline = time.monotonic()+120
                    expected_state = {'completed': 'succeeded', 'hold': 'hold', 'cancel': 'canceled'}[mode]
                    def attempts():
                        return [json.loads(p.read_bytes()) for p in sorted(tmp_path.glob('attempt-*.private.json'))]
                    while not any(value['state'] == expected_state for value in attempts()):
                        assert process.poll() is None, 'consumer ended before terminal job'
                        assert time.monotonic() < deadline, 'owned consumer finish deadline exceeded'
                        time.sleep(.25)
                    process.send_signal(signal.SIGTERM); process.wait(timeout=5)
                finally:
                    for flag in ('block', 'progress-block'):
                        (tmp_path/flag).unlink(missing_ok=True)
            assert process.returncode == 0 and worker_errors == ['']
            all_attempts = attempts(); attempt = all_attempts[-1]
            assert all(value['actual_scram'] for value in all_attempts)
            assert attempt['state'] == {'completed': 'succeeded', 'hold': 'hold', 'cancel': 'canceled'}[mode], {'state': attempt['state'], 'events': events}
            assert attempt['calls']['step'] == (0 if mode == 'cancel' else 16)
            c.value[-1].allowed = True; send({'stage': 'worker_finished'})
            if mode != 'cancel':
                loaded = receive('saved_loaded')
                for index in range(loaded['samples']):
                    verified = receive('sample_verified'); assert verified['index'] == index
                selected = receive('result_loaded'); assert selected['job_id'] == job
                observed = [p.read_bytes() for p in (root/'browser-wire').glob('*.wire')]
                assert len(stored) == 2 and all(item['raw'] in observed for item in stored)
                send({'stage': 'result_compared'})
            else:
                r.consumer.reference.no_published_result(c.worker, job)
            receive('verified'); output, _ = browser.communicate(timeout=15)
            assert browser.returncode == 0 and not output
            report = json.loads((root/'browser-result.private.json').read_bytes())
            actual_progress = [p.read_bytes() for p in (root/'browser-wire').glob('*.wire')
                if json.loads(p.read_bytes()).get('version') == 'joint-crop-climate-execution-query-v1']
            assert actual_progress and all(raw in [item['raw'] for item in captured] for raw in actual_progress)
            assert report['max_simultaneous_progress_GET'] == 1 and report['no_mocked_routes']
            assert r.TOKEN.decode() not in json.dumps(report)
            save(root/'native-browser-proof.json', {'mode': mode, 'job_id': job, 'actual_SCRAM': attempt['actual_scram'],
                'verified_TLS_negative_CA_test': True, 'automatic_independent_consumer': True, 'consumer_exit': process.returncode,
                'consumer_factory_sha256': factory_sha, 'checkpoint_pause_is_test_instrumentation': True, 'chunk_budget': 16,
                'attempt': attempt, 'all_attempts': all_attempts, 'stages': stages, 'browser_exit': browser.returncode,
                'original_progress_wire_bytes_equal': True, 'read_calls': [item['calls'] for item in captured],
                'query_seconds': [item['seconds'] for item in captured], 'stored_read_calls': [item['calls'] for item in stored],
                'stored_query_seconds': [item['seconds'] for item in stored], 'original_saved_wire_bytes_equal': mode != 'cancel',
                'browser_report_sha256': sha256((root/'browser-result.private.json').read_bytes()).hexdigest(),
                'actual_crop_Runs': 0, 'G0_G4': 'not_assessed'})
    finally:
        c.value[-1].allowed = True
        if browser is not None:
            if browser.poll() is None:
                browser.terminate()
                try: browser.wait(timeout=15)
                except subprocess.TimeoutExpired: browser.kill(); browser.wait(timeout=5)
            for pipe in (browser.stdin, browser.stdout):
                if pipe is not None: pipe.close()
        if errors is not None: errors.close()
        pack.unlink(); (tmp_path/'proof.private.json').unlink(); request_file.unlink()
        gc.collect()
        assert r.fd_inventory() == inventory
