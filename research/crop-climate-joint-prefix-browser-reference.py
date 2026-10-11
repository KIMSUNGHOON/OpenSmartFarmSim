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
import ssl
import subprocess
import sys
import threading
import time
import urllib.error
import urllib.request

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
        browser = subprocess.Popen(['nice', '-n', '19', 'node', '--expose-gc', '--max-old-space-size=64',
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


def run_live(args):
    directory = args.directory; directory.mkdir(mode=0o700)
    handoff = json.loads(args.handoff.read_bytes())
    old = handoff['current_joint_execution_user_preview']
    service = Path(old['service_directory'])
    helper = ROOT/'research/owned-research-process-scope.py'
    spec = importlib.util.spec_from_file_location('owned_live_prefix_scope', helper)
    guard = importlib.util.module_from_spec(spec); spec.loader.exec_module(guard)
    assert not guard.live(guard.Identity(**old['controller_identity']))
    protected = tuple(guard.Identity(**v) for v in handoff['resource_protection_required_for_next_turn']['roots'])
    assert all(guard.live(v) for v in protected)
    baseline = json.loads(args.maintenance_before.read_bytes())
    original_runtime = json.loads((service/'runtime.private.json').read_bytes())
    rights = (service/'rights.private.json').read_bytes()
    run_name = 'prefix-p6-'+directory.parent.name
    active = service/run_name
    request = json.loads((service/'requests'/('hold-validation.json' if args.mode == 'live-hold' else 'normal-validation.json')).read_bytes())
    request.update(study_id='p6-prefix-browser', revision=run_name+'-'+args.mode)
    request_file = directory/'request.private.json'; save(request_file, request)
    api_port, web_port = free_port(), free_port()
    assert api_port != web_port
    logs = []; process = browser = None; reason = None; browser_code = None; cleanup = None; cleanup_error = None; http_errors = []
    source = pins(ROOT); start = time.monotonic(); stop = threading.Event()
    for sig in (signal.SIGTERM, signal.SIGINT): signal.signal(sig, lambda *_: stop.set())

    def http(method, path):
        access = json.loads((active/'access.private.json').read_bytes())
        context = ssl.create_default_context(cafile=active/'cert.pem')
        request = urllib.request.Request(f'https://127.0.0.1:{api_port}'+path,
            method=method, headers={'Authorization': 'Bearer '+access['token']})
        deadline = time.monotonic()+60
        while True:
            try:
                with urllib.request.urlopen(request, context=context, timeout=30) as response:
                    raw = response.read(2*1024**2+1); assert len(raw) <= 2*1024**2
                    assert response.headers['Cache-Control'] == 'no-store'
                    return json.loads(raw)
            except urllib.error.HTTPError as error:
                raw = error.read(2*1024**2+1); assert len(raw) <= 2*1024**2
                http_errors.append({'method': method, 'path': path, 'status': error.code,
                    'sha256': sha256(raw).hexdigest(), 'value': json.loads(raw)})
                if error.code != 503 or time.monotonic() >= deadline: raise
                time.sleep(.5)

    try:
        output = (directory/'service.private.log').open('xb'); logs.append(output); os.fchmod(output.fileno(), 0o600)
        env = {**os.environ, 'PYTHONDONTWRITEBYTECODE': '1', 'MALLOC_ARENA_MAX': '2'}
        process = subprocess.Popen([sys.executable, '-B', str(ROOT/'research/crop-climate-joint-live-preview.py'),
            'serve', '--directory', str(service), '--pg-bin', str(args.pg_bin), '--run', run_name,
            '--ttl-seconds', '600', '--api-port', str(api_port), '--web-port', str(web_port),
            '--nginx', str(args.nginx), '--dist', str(args.dist), '--enable-prefix', '--worker-chunk-budget', '8'],
            env=env, stdin=subprocess.DEVNULL, stdout=output, stderr=subprocess.STDOUT)
        deadline = time.monotonic()+30
        while not (active/'ready.private.json').exists():
            assert process.poll() is None and time.monotonic() < deadline and not stop.is_set()
            time.sleep(.1)
        ready = json.loads((active/'ready.private.json').read_bytes())
        assert ready['actual_SCRAM'] and ready['automatic_consumer'] and not ready['test_checkpoint_pause']
        assert ready['prefix_enabled'] and ready['worker_chunk_budget'] == 8
        save(directory/'candidate-ready.private.json', ready)
        from psycopg import connect, sql
        from psycopg.rows import dict_row
        owned = {(value['study_id'], value['revision']) for filename in
            args.directory.parents[1].glob('focused-live-*/native/request.private.json')
            for value in [json.loads(filename.read_bytes())]}
        with connect(original_runtime['dsn'], row_factory=dict_row, require_auth='scram-sha-256') as conn:
            conn.execute('SET TRANSACTION READ ONLY'); assert conn.pgconn.used_password
            rows = conn.execute(sql.SQL('SELECT job_id,input_bytes,input_sha256 FROM {}.jobs WHERE tenant_id=%s')
                .format(sql.Identifier(original_runtime['policy']['schema'])), ('tenant-1',)).fetchall()
        prior_cleanup = []
        for row in rows:
            body = json.loads(row['input_bytes']).get('request', {})
            if (body.get('study_id'), body.get('revision')) not in owned: continue
            assert sha256(row['input_bytes']).hexdigest() == row['input_sha256']
            previous_job = str(row['job_id']); assert previous_job not in baseline['database_rows']['jobs']
            path = '/v1/jobs/'+previous_job+'/crop-climate-joint-execution'
            value = http('POST', path+'/cancel'); deadline = time.monotonic()+90
            while value['job']['state'] in ('queued', 'simulating'):
                assert time.monotonic() < deadline
                time.sleep(.25); value = http('GET', path)
            prior_cleanup.append({'job_id': previous_job, 'state': value['job']['state'], 'cancel_requested': value['cancel_requested']})
        save(directory/'prior-owned-job-cancel.private.json', prior_cleanup)
        context_file = directory/'browser-context.private.json'
        save(context_file, {'origin': f'http://127.0.0.1:{web_port}', 'mode': args.mode,
            'access_file': str(active/'access.private.json'), 'request_file': str(request_file),
            'farm': request['farm'], 'directory': str(directory),
            'playwright': str(ROOT/'web/node_modules/playwright-core/index.mjs')})
        output = (directory/'browser.private.log').open('xb'); logs.append(output); os.fchmod(output.fileno(), 0o600)
        browser = subprocess.Popen(['nice', '-n', '19', 'node', '--expose-gc', '--max-old-space-size=64', '--max-semi-space-size=1',
            str(ROOT/'research/crop-climate-joint-prefix-browser-reference.mjs'), str(context_file)],
            stdin=subprocess.DEVNULL, stdout=output, stderr=subprocess.STDOUT, env=env)
        while browser.poll() is None:
            assert process.poll() is None
            tree = guard._tree(guard.identity(browser.pid))
            browser_soft_limit = max((rss for _, rss in tree.values()), default=0) > 430*1024**2
            if stop.is_set() or browser_soft_limit or time.monotonic()-start > 330:
                reason = 'browser_RSS_soft_limit' if browser_soft_limit else 'requested_stop' if stop.is_set() else 'wall_limit'
                browser.terminate(); break
            time.sleep(.1)
        browser_code = browser.wait(timeout=15)
    finally:
        if browser is not None and browser.poll() is None:
            browser.terminate(); browser.wait(timeout=15)
        if process is not None and process.poll() is None:
            try:
                assert (service/'rights.private.json').read_bytes() == rights
                job_file = directory/'browser-job.private.json'
                if job_file.exists():
                    job = json.loads(job_file.read_bytes())['job_id']
                    path = '/v1/jobs/'+job+'/crop-climate-joint-execution'
                    value = http('POST', path+'/cancel'); deadline = time.monotonic()+90
                    while value['job']['state'] in ('queued', 'simulating'):
                        assert time.monotonic() < deadline
                        time.sleep(.25)
                        try: value = http('GET', path)
                        except urllib.error.HTTPError as error:
                            if error.code != 503: raise
                    cleanup = {'job_id': job, 'state': value['job']['state']}
                sys.path.insert(0, str(service))
                from app.crop_climate_joint_operator_config import load_joint_api_runtime
                from psycopg import sql
                runtime = load_joint_api_runtime(active/'operator.private.json')
                preserved = {}
                owned = {(value['study_id'], value['revision']) for filename in
                    args.directory.parents[1].glob('focused-live-*/native/request.private.json')
                    for value in [json.loads(filename.read_bytes())]}
                with runtime.jobs.connect() as conn:
                    assert conn.pgconn.used_password
                    for table, original in baseline['database_rows'].items():
                        rows = conn.execute(sql.SQL('SELECT * FROM {}').format(runtime.jobs._table(table))).fetchall()
                        actual = {str(row['job_id'])+(':'+str(row['attempt']) if table == 'job_attempts' else
                            ':'+str(row['event_id']) if table == 'job_events' else ''):
                            sha256(json.dumps(row, sort_keys=True, default=str).encode()).hexdigest() for row in rows}
                        preserved[table] = all(actual.get(key) == digest for key, digest in original.items())
                        if table == 'jobs':
                            own_jobs = [str(row['job_id']) for row in rows if
                                str(row['job_id']) not in original and
                                (json.loads(row['input_bytes']).get('request', {}).get('study_id'),
                                 json.loads(row['input_bytes']).get('request', {}).get('revision')) in owned]
                assert all(preserved.values())
                save(directory/'database-preservation.private.json', {'actual_SCRAM': True, 'preexisting_rows': preserved})
                final_own_jobs = []
                for identity in own_jobs:
                    path = '/v1/jobs/'+identity+'/crop-climate-joint-execution'
                    value = http('POST', path+'/cancel'); deadline = time.monotonic()+90
                    while value['job']['state'] in ('queued', 'simulating'):
                        assert time.monotonic() < deadline
                        time.sleep(.25)
                        try: value = http('GET', path)
                        except urllib.error.HTTPError as error:
                            if error.code != 503: raise
                    final_own_jobs.append({'job_id': identity, 'state': value['job']['state']})
                save(directory/'all-owned-jobs-cleanup.private.json', final_own_jobs)
            except Exception as error:
                cleanup_error = type(error).__name__+(':'+str(error.code) if isinstance(error, urllib.error.HTTPError) else '')
            finally:
                process.terminate(); process.wait(timeout=90)
        for output in logs: output.close()
        current = json.loads((service/'runtime.private.json').read_bytes())
        keys = ('input_key', 'custody_key', 'result_key', 'thermal_key', 'market_key', 'dsn', 'inputs')
        inputs_preserved = all(Path(name).is_file() and sha256(Path(name).read_bytes()).hexdigest() == digest
            for name, digest in baseline['data_files'].items())
        record = {'mode': args.mode, 'actual_browser_exit': browser_code,
            'actual_service_exit': process.returncode if process else None, 'reason': reason,
            'wall_seconds': time.monotonic()-start, 'source_preserved': pins(ROOT) == source,
            'preexisting_data_files_preserved': inputs_preserved,
            'signing_keys_DSN_and_inputs_preserved': all(current[k] == original_runtime[k] for k in keys),
            'current_rights_preserved': (service/'rights.private.json').read_bytes() == rights,
            'database_retained': (service/'database').is_dir(),
            'candidate_PG_stopped': not (service/'database/postmaster.pid').exists(),
            'automatic_unpaused_worker_chunk_budget': 8, 'owned_job_cleanup': cleanup, 'cleanup_error': cleanup_error,
            'legacy_protected_live': all(guard.live(v) for v in protected),
            'protected_root_count': len(protected),
            'both_previews_maintenance_window': bool(handoff.get('current_joint_execution_maintenance', {}).get('both_previews_stopped')),
            'candidate_user_port': web_port, 'user_activation': False, 'P6_parent_accepted': False, 'G0_G4': 'not_assessed'}
        save(directory/'terminal.private.json', record); print(json.dumps(record), flush=True)
        save(directory/'cleanup-http-errors.private.json', http_errors)
    assert browser_code == 0 and process.returncode == 0 and reason is None and cleanup_error is None
    assert all(record[k] for k in ('source_preserved', 'preexisting_data_files_preserved',
        'signing_keys_DSN_and_inputs_preserved', 'current_rights_preserved', 'candidate_PG_stopped', 'legacy_protected_live'))


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--directory', type=Path, required=True)
    parser.add_argument('--dist', type=Path, required=True)
    parser.add_argument('--nginx', type=Path, required=True)
    parser.add_argument('--handoff', type=Path, required=True)
    parser.add_argument('--previous-browser', type=Path, required=True)
    parser.add_argument('--pg-bin', type=Path)
    parser.add_argument('--maintenance-before', type=Path)
    parser.add_argument('--mode', choices=['profile', 'live-normal', 'live-hold', 'live-cancel'], default='profile')
    args = parser.parse_args()
    run(args) if args.mode == 'profile' else run_live(args)
