"""Owned loopback prefix browser reference; reuse a live synthetic store.

The profile action reads an existing completed job. It does not establish
running-prefix acceptance or deploy the candidate to either user preview.
"""
from datetime import datetime, timezone
from hashlib import sha256
from pathlib import Path
import argparse
import importlib.util
import json
import os
import signal
import socket
import subprocess
import sys
import threading
import time

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT/'backend'), str(ROOT/'backend/tests')]


def save(path, value):
    with path.open('x') as output:
        os.fchmod(output.fileno(), 0o600)
        json.dump(value, output, sort_keys=True)
        output.flush(); os.fsync(output.fileno())


def pins(root):
    names = subprocess.check_output(['git', 'ls-files', '-z', '--cached', '--others',
                                     '--exclude-standard'], cwd=root).decode().split('\0')
    return {name: sha256((root/name).read_bytes()).hexdigest()
            for name in set(names) if name and (root/name).is_file()}


def free_port():
    with socket.socket() as probe:
        probe.bind(('127.0.0.1', 0))
        return probe.getsockname()[1]


class Observe:
    def __init__(self, app, directory):
        self.app, self.directory, self.responses = app, directory, []

    async def __call__(self, scope, receive, send):
        if scope['type'] != 'http':
            return await self.app(scope, receive, send)
        captured = bytearray(); status = None; no_store = False
        async def emit(message):
            nonlocal status, no_store
            if message['type'] == 'http.response.start':
                status = message['status']
                no_store = (b'cache-control', b'no-store') in message['headers']
            elif message['type'] == 'http.response.body':
                captured.extend(message.get('body', b''))
                assert len(captured) <= 2*1024**2
                if not message.get('more_body', False):
                    name = f'{len(self.responses):04d}.wire'
                    with (self.directory/name).open('xb') as output:
                        os.fchmod(output.fileno(), 0o400); output.write(captured)
                    self.responses.append({'method': scope['method'], 'path': scope['path'],
                        'query': scope['query_string'].decode(), 'status': status,
                        'bytes': len(captured), 'sha256': sha256(captured).hexdigest(),
                        'no_store': no_store, 'wire_file': name})
            await send(message)
        await self.app(scope, receive, emit)


def run(args):
    directory = args.directory; directory.mkdir(mode=0o700)
    helper = ROOT/'research/owned-research-process-scope.py'
    assert sha256(helper.read_bytes()).hexdigest() == '0337a2878b1d57b39d0e7ef2840c8e0fb41fe6ae4bcdd12812959aacb15f311f'
    spec = importlib.util.spec_from_file_location('owned_prefix_browser_scope', helper)
    guard = importlib.util.module_from_spec(spec); spec.loader.exec_module(guard)
    handoff = json.loads(args.handoff.read_bytes())
    protected = tuple(guard.Identity(**value) for value in
                      handoff['resource_protection_required_for_next_turn']['roots'])
    assert all(guard.live(identity) for identity in protected)
    before = pins(ROOT)
    source = Path(handoff['current_joint_execution_user_preview']['source'])
    old_source = pins(source)
    preview = Path(handoff['current_joint_execution_user_preview']['active_run'])
    service = preview.parent
    sys.path.insert(0, str(service))
    from app.crop_climate_joint_operator_config import load_joint_api_runtime, PREFIX_VERSION
    config = json.loads((preview/'operator.private.json').read_bytes())
    config.update(config_version=PREFIX_VERSION, crop_climate_joint_prefix=True,
                  host='127.0.0.1', port=free_port())
    config_path = directory/'operator.private.json'; save(config_path, config)
    runtime = load_joint_api_runtime(config_path)
    server = runtime.service.server(); observed = Observe(server.config.app, directory)
    server.config.app = observed
    thread = threading.Thread(target=server.run, daemon=True)
    stop = threading.Event()
    for signum in (signal.SIGTERM, signal.SIGINT):
        signal.signal(signum, lambda *_: stop.set())
    scope = guard.OwnedProcessScope(protected=protected)
    nginx = browser = None; single = combined = samples = 0; reason = None
    start = time.monotonic(); logs = []
    try:
        thread.start(); deadline = time.monotonic()+15
        while not server.started:
            assert thread.is_alive() and time.monotonic() < deadline; time.sleep(.05)
        port = free_port(); (directory/'logs').mkdir(mode=0o700)
        template = (ROOT/'web/nginx.conf').read_text()
        changes = {'/tmp/nginx.pid': str(directory/'nginx.pid'),
            '/etc/nginx/mime.types': str(args.nginx.parents[1]/'conf/mime.types'),
            'listen 8444 ssl;': f'listen 127.0.0.1:{port};',
            '/run/operator/web/cert.pem': str(preview/'cert.pem'),
            '/run/operator/web/key.pem': str(preview/'key.pem'),
            '/run/operator/web/api-ca.pem': str(preview/'cert.pem'),
            '/usr/share/nginx/html': str(args.dist),
            'https://127.0.0.1:8443': f'https://127.0.0.1:{config["port"]}'}
        for name in ('client', 'proxy', 'fastcgi', 'uwsgi', 'scgi'):
            changes['/tmp/'+name+'-temp'] = str(directory/(name+'-temp'))
        for old, new in changes.items():
            assert old in template; template = template.replace(old, new)
        nginx_config = directory/'nginx.conf'
        with nginx_config.open('x') as output:
            os.fchmod(output.fileno(), 0o600); output.write(template)
        nginx_log = (directory/'nginx.private.log').open('xb'); logs.append(nginx_log)
        os.fchmod(nginx_log.fileno(), 0o600)
        nginx = subprocess.Popen([str(args.nginx), '-p', str(directory)+'/', '-c',
            str(nginx_config), '-g', 'daemon off;'], stdin=subprocess.DEVNULL,
            stdout=nginx_log, stderr=subprocess.STDOUT)
        old = json.loads((args.previous_browser/'evidence/browser-result.private.json').read_bytes())
        request = json.loads((service/'requests/normal-user.json').read_bytes())
        browser_context = directory/'browser-context.private.json'
        save(browser_context, {'origin': f'http://127.0.0.1:{port}', 'mode': args.mode,
            'access_file': str(preview/'access.private.json'), 'job_id': old['job_id'],
            'farm': request['farm'], 'directory': str(directory),
            'playwright': str(ROOT/'web/node_modules/playwright-core/index.mjs')})
        browser_log = (directory/'browser.private.log').open('xb'); logs.append(browser_log)
        os.fchmod(browser_log.fileno(), 0o600)
        browser = subprocess.Popen(['nice', '-n', '19', 'node', '--max-old-space-size=64',
            '--max-semi-space-size=1', str(ROOT/'research/crop-climate-joint-prefix-browser-reference.mjs'),
            str(browser_context)], stdin=subprocess.DEVNULL, stdout=browser_log,
            stderr=subprocess.STDOUT, env={**os.environ, 'UV_THREADPOOL_SIZE': '1'})
        while browser.poll() is None:
            rss = scope.sample(); samples += 1
            single = max(single, max(rss.values(), default=0)); combined = max(combined, sum(rss.values()))
            if single > 512*1024**2 or combined > 1024**3: reason = 'RSS_limit'
            elif time.monotonic()-start > 180: reason = 'wall_limit'
            elif stop.is_set(): reason = 'requested_stop'
            if reason:
                scope.signal_owned(signal.SIGTERM); break
            assert thread.is_alive() and nginx.poll() is None
            time.sleep(.25)
        code = browser.wait(timeout=10)
    finally:
        if browser is not None and browser.poll() is None:
            browser.terminate(); browser.wait(timeout=10)
        if nginx is not None and nginx.poll() is None:
            nginx.terminate(); nginx.wait(timeout=10)
        server.should_exit = True; thread.join(20)
        for log in logs: log.close()
        scope.signal_owned(signal.SIGTERM)
        for _ in range(30):
            if not scope.remaining(): break
            time.sleep(.1)
        remaining = [identity._asdict() for identity in scope.remaining()]
        save(directory/'server-responses.private.json', observed.responses)
        record = {'mode': args.mode, 'actual_browser_exit': browser.returncode if browser else None,
            'reason': reason, 'single_PID_peak_RSS_bytes': single, 'combined_peak_RSS_bytes': combined,
            'sample_interval_seconds': .25, 'samples': samples, 'wall_seconds': time.monotonic()-start,
            'source_preserved': pins(ROOT) == before, 'user_joint_source_preserved': pins(source) == old_source,
            'protected_live': all(guard.live(identity) for identity in protected),
            'owned_remaining': remaining, 'API_thread_stopped': not thread.is_alive(),
            'existing_automatic_worker_reused': True, 'new_calculation_jobs': 0,
            'actual_live_prefix_acceptance': False, 'user_deployment_changed': False, 'G0_G4': 'not_assessed'}
        save(directory/'terminal.private.json', record)
        print(json.dumps(record), flush=True)
    assert code == 0 and reason is None and record['source_preserved'] and record['protected_live'] and not remaining


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--directory', type=Path, required=True)
    parser.add_argument('--dist', type=Path, required=True)
    parser.add_argument('--nginx', type=Path, required=True)
    parser.add_argument('--handoff', type=Path, required=True)
    parser.add_argument('--previous-browser', type=Path, required=True)
    parser.add_argument('--mode', choices=['profile'], default='profile')
    run(parser.parse_args())
