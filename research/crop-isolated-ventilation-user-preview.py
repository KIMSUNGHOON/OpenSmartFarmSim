"""Retained local synthetic preview, with an independently owned API and worker."""
import argparse
from datetime import datetime, timezone
from hashlib import sha256
import importlib.util
import json
import os
from pathlib import Path
import signal
import subprocess
import sys
import tempfile
import threading
import time

ROOT = Path(__file__).resolve().parents[1]


def module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    value = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(value)
    return value


def atomic(path, value):
    data = value if isinstance(value, bytes) else (json.dumps(value, sort_keys=True)+'\n').encode()
    fd, temporary = tempfile.mkstemp(prefix='.'+path.name+'.', dir=path.parent)
    try:
        os.fchmod(fd, 0o600)
        with os.fdopen(fd, 'wb') as stream:
            stream.write(data); stream.flush(); os.fsync(stream.fileno())
        os.replace(temporary, path)
        fd = os.open(path.parent, os.O_RDONLY | os.O_DIRECTORY)
        try: os.fsync(fd)
        finally: os.close(fd)
    finally:
        if os.path.exists(temporary): os.unlink(temporary)


def private(path):
    path = Path(path)
    stat = path.lstat()
    assert path.is_file() and not path.is_symlink() and stat.st_uid == os.getuid()
    assert stat.st_mode & 0o777 in (0o400, 0o600) and stat.st_size <= 2*1024**2
    return json.loads(path.read_bytes())


def route_text(original, api):
    marker = '        location ~ ^/(?:v1(?:/|$)|openapi\\.json$) {'
    assert original.count(marker) == 1
    start = original.index(marker)
    end = original.index('\n        location = /development-status.json', start)
    block = original[start:end]
    route = ('        location ~ ^/v1/(?:crop-greenhouse-ventilation-(?:executions|research-results)'
             '(?:/|$)|jobs/[^/]+/crop-greenhouse-ventilation-execution(?:/|$)) {')
    assert block.count('proxy_pass https://127.0.0.1:8446;') == 1
    block = block.replace(marker, route).replace('https://127.0.0.1:8446;',
        'https://127.0.0.1:'+str(api['port'])+';')
    import re
    block, count = re.subn(r'proxy_ssl_trusted_certificate [^;]+;',
        'proxy_ssl_trusted_certificate '+api['certificate']+';', block)
    assert count == 1
    return original[:start]+block+'\n'+original[start:]


def nginx_reload(cfg, processes):
    expected = processes.Identity(**cfg['original_nginx_master'])
    assert processes.live(expected)
    fd = processes._pidfd_open(expected.pid)
    try:
        assert processes.live(expected)
        processes._pidfd_send_signal(fd, signal.SIGHUP)
    finally: os.close(fd)


def switch_route(cfg, run, processes, *, restore=False):
    original = (run/'nginx-before.private.conf').read_bytes()
    candidate = (run/'nginx-candidate.private.conf').read_bytes()
    path = Path(cfg['original_nginx_config'])
    if restore:
        if path.read_bytes() == original: return False
        assert path.read_bytes() == candidate, 'unexpected user proxy configuration'
        atomic(path, original)
    else:
        ready = private(run/'ready.private.json')
        assert all(processes.live(processes.Identity(**ready[k])) for k in ('controller', 'worker'))
        assert private(run/'live.private.json')['reason'] is None
        assert path.read_bytes() == original and sha256(original).hexdigest() == cfg['original_nginx_sha256']
        with (run/'nginx-validation.private.log').open('xb') as log:
            os.fchmod(log.fileno(), 0o600)
            subprocess.run([cfg['nginx'], '-p', str(path.parent), '-c', str(run/'nginx-candidate.private.conf'), '-t'],
                stdin=subprocess.DEVNULL, stdout=log, stderr=subprocess.STDOUT, check=True, timeout=10)
        atomic(path, candidate)
    nginx_reload(cfg, processes)
    atomic(run/('route-restored.private.json' if restore else 'route-applied.private.json'),
        {'original_sha256': sha256(original).hexdigest(), 'candidate_sha256': sha256(candidate).hexdigest(),
         'restored': restore, 'original_nginx_master_preserved': True})
    return True


def browser_batch(cfg, run, command, processes, lifecycle):
    from uuid import uuid4
    import isolated_ventilation_operator as operator
    import ctypes
    import gc
    import re
    assert set(command) == {'action', 'name', 'modes'} and command['action'] == 'browser'
    assert re.fullmatch('[a-z0-9-]{1,64}', command['name'])
    modes = command['modes']
    assert modes and len(set(modes)) == len(modes) and set(modes) <= {'completed', 'hold', 'cancel'}
    assert Path(cfg['original_nginx_config']).read_bytes() == (run/'nginx-candidate.private.conf').read_bytes()
    directory = run/command['name']; directory.mkdir(mode=0o700)
    browser = module('user_browser_owner', ROOT/'research/crop-ventilation-browser-supervisor.py')
    driver = module('user_browser_pipe', ROOT/'research/crop-isolated-ventilation-pipe-reference.py')
    finished = []
    for mode in modes:
        body = private(Path(cfg['requests'])/(mode+'.json'))
        body.update(study_id='user-browser-'+uuid4().hex, revision=mode+'-v1')
        request = directory/(mode+'.request.private.json'); atomic(request, body)
        evidence = browser.BrowserEvidence(directory/('browser-'+mode), request=request,
            access=Path(cfg['access']), rights=Path(operator.load()[0]['ventilation']['rights_file']),
            driver=ROOT/'research/crop-isolated-ventilation-cdp-reference.mjs',
            chromium=Path(cfg['chromium']), mode=mode, origin='http://127.0.0.1:5174')
        gc.collect(); ctypes.CDLL(None).malloc_trim(0)
        terminal = driver.exercise(evidence, processes=processes, supervisor_class=browser.BrowserChild)
        assert terminal['actual_child_exit'] == 0 and terminal['reason'] is None
        assert not terminal['owned_remaining'] and not terminal['forced_kill']
        assert terminal['current_rights_restored'] and terminal['cleanup_error_type'] is None
        finished.append((evidence.directory, body, mode))
    reference = module('user_browser_verification', ROOT/'research/crop-isolated-ventilation-browser-probe.py')
    cases = {mode: reference.verify(path, operator, body, mode, lifecycle.save, lifecycle, ROOT)
             for path, body, mode in finished}
    audit = [json.loads(row) for row in (Path(cfg['runtime'])/'query-audit.private.jsonl').read_text().splitlines()]
    assert audit and all(not any(row['calls'].values()) for row in audit)
    atomic(directory/'acceptance.private.json', {
        'case_outcomes': {mode: {k: v for k, v in case.items() if k not in ('job_id', 'result', 'farm')}
                          for mode, case in cases.items()},
        'same_retained_API_worker_and_namespace': True, 'actual_user_origin_port': 5174,
        'actual_HTTP_query_audit_count': len(audit), 'actual_HTTP_query_calculation_and_write_calls': 0,
        'device_scale_factor': .5, 'real_farm_runs': 0, 'G0_G4': 'not_assessed'})


def serve(cfg, run):
    run.mkdir(mode=0o700)
    processes = module('user_preview_processes', ROOT/'research/owned-research-process-scope.py')
    protected = tuple(processes.Identity(**v) for v in cfg['protected_roots'])
    assert len(protected) == 4 and all(processes.live(v) for v in protected)
    scope = processes.OwnedProcessScope(protected=protected)
    stop = threading.Event()
    for signum in (signal.SIGTERM, signal.SIGINT): signal.signal(signum, lambda *_: stop.set())
    stats = {'reason': None, 'single_PID_peak_RSS_bytes': 0, 'combined_peak_RSS_bytes': 0, 'RSS_samples': 0}
    started = time.monotonic()
    def monitor():
        try:
            while not stop.is_set():
                rss = scope.sample()
                stats['RSS_samples'] += 1
                stats['single_PID_peak_RSS_bytes'] = max(stats['single_PID_peak_RSS_bytes'], max(rss.values(), default=0))
                stats['combined_peak_RSS_bytes'] = max(stats['combined_peak_RSS_bytes'], sum(rss.values()))
                if not all(processes.live(v) for v in protected): stats['reason'] = 'protected_process_lost'
                elif max(rss.values(), default=0) > 512*1024**2 or sum(rss.values()) > 1024**3: stats['reason'] = 'RSS_limit'
                elif time.monotonic() > stats.get('browser_deadline', float('inf')): stats['reason'] = 'browser_wall_limit'
                if stats['RSS_samples'] == 1 or stats['RSS_samples'] % 20 == 0 or stats['reason']:
                    atomic(run/'live.private.json', {**stats, 'wall_seconds': time.monotonic()-started,
                        'controller': processes.identity(os.getpid())._asdict(), 'protected_root_count': 4,
                        'protected_live': all(processes.live(v) for v in protected), 'sample_interval_seconds': .25})
                if stats['reason']:
                    stop.set(); scope.signal_owned(signal.SIGTERM); break
                stop.wait(.25)
        except BaseException:
            stats['reason'] = 'resource_monitor_error'; stop.set(); scope.signal_owned(signal.SIGTERM)
    monitor_thread = threading.Thread(target=monitor, daemon=True); monitor_thread.start()
    directory = Path(cfg['runtime'])
    runtime_config = private(directory/'runtime.private.json')
    paths = list(map(str, (directory, ROOT/'research', ROOT/'backend', ROOT/'backend/tests',
                          Path(runtime_config['original_operator']).parent)))
    sys.path[:0] = paths
    def sources_preserved():
        return all(sha256((ROOT/name).read_bytes()).hexdigest() == digest
                   for name, digest in cfg['source_sha256'].items())
    assert sources_preserved()
    server = api_thread = worker = log = None
    lifecycle = module('user_preview_lifecycle', ROOT/'research/crop-joint-ventilation-live-preview.py')
    try:
        probe = module('user_preview_api', ROOT/'research/crop-isolated-ventilation-runtime-probe.py')
        import isolated_ventilation_operator as operator
        value, _, _ = operator.load()
        expires = datetime.fromisoformat(value['auth']['expires_at'])
        assert (expires-datetime.now(timezone.utc)).total_seconds() > 300
        original = Path(cfg['original_nginx_config']).read_bytes()
        assert sha256(original).hexdigest() == cfg['original_nginx_sha256']
        atomic(run/'nginx-before.private.conf', original)
        api = private(directory/'api.private.json')
        atomic(run/'nginx-candidate.private.conf', route_text(original.decode(), api).encode())
        runtime = probe.audited_runtime(directory/'api.private.json', bounded_preview=True,
            capacity_record=run/'capacity.private.json')
        server = runtime.service.server()
        api_thread = threading.Thread(target=server.run, daemon=True); api_thread.start()
        log = (run/'worker.private.log').open('xb'); os.fchmod(log.fileno(), 0o600)
        env = {**os.environ, 'PYTHONPATH': os.pathsep.join(paths), 'PYTHONDONTWRITEBYTECODE': '1'}
        worker = subprocess.Popen([sys.executable, '-B', '-m', 'app.deterministic_work',
            '--factory', 'isolated_ventilation_operator:worker'], env=env, stdin=subprocess.DEVNULL,
            stdout=log, stderr=subprocess.STDOUT)
        deadline = time.monotonic()+30
        while not server.started or not (run/'worker.private.log').stat().st_size:
            assert worker.poll() is None and api_thread.is_alive() and not stop.is_set()
            assert time.monotonic() < deadline, 'retained service readiness expired'
            time.sleep(.1)
        assert json.loads((run/'worker.private.log').read_text().splitlines()[0]) == {'version': 1, 'event': 'started'}
        atomic(run/'ready.private.json', {'controller': processes.identity(os.getpid())._asdict(),
            'worker': processes.identity(worker.pid)._asdict(), 'API_port': api['port'],
            'expires_at': value['auth']['expires_at'], 'worker_chunk_budget': 8,
            'source_file_count': len(cfg['source_sha256']), 'source_preserved': sources_preserved(),
            'new_model_user_deployed': False, 'real_farm_runs': 0, 'G0_G4': 'not_assessed'})
        while not stop.wait(.25):
            assert worker.poll() is None and api_thread.is_alive(), 'retained service exited'
            command_path = run/'control-request.private.json'
            if command_path.exists():
                command = private(command_path)
                claimed = run/'control-claimed.private.json'
                assert not claimed.exists()
                os.replace(command_path, claimed)
                stats['browser_deadline'] = time.monotonic()+1500
                browser_batch(cfg, run, command, processes, lifecycle)
                stats.pop('browser_deadline')
                assert sources_preserved()
                os.replace(claimed, run/('control-'+command['name']+'.done.private.json'))
            if (expires-datetime.now(timezone.utc)).total_seconds() < 5: break
    except BaseException as error:
        stats['service_error_type'] = type(error).__name__
        raise
    finally:
        stop.set()
        stopped = lifecycle.stop_owned_process(worker, timeout=30) if worker is not None else None
        if server is not None: server.should_exit = True
        if api_thread is not None: api_thread.join(30)
        monitor_thread.join(5)
        restored = switch_route(cfg, run, processes, restore=True) if (run/'nginx-candidate.private.conf').exists() else False
        if log is not None: log.close()
        atomic(run/'stopped.private.json', {**stats, 'worker_stop': stopped,
            'API_stopped': api_thread is None or not api_thread.is_alive(),
            'route_restored': restored, 'namespace_and_results_retained': True,
            'source_preserved': sources_preserved(),
            'protected_live': all(processes.live(v) for v in protected), 'real_farm_runs': 0, 'G0_G4': 'not_assessed'})
    assert stats['reason'] is None and (api_thread is None or not api_thread.is_alive())


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=('serve', 'activate', 'restore', 'stop'))
    parser.add_argument('--config', type=Path, required=True)
    parser.add_argument('--run', type=Path, required=True)
    args = parser.parse_args()
    cfg = private(args.config)
    if args.action == 'serve': serve(cfg, args.run)
    else:
        processes = module('user_preview_processes', ROOT/'research/owned-research-process-scope.py')
        if args.action == 'stop':
            identity = processes.Identity(**private(args.run/'ready.private.json')['controller'])
            assert processes.live(identity)
            fd = processes._pidfd_open(identity.pid)
            try:
                assert processes.live(identity); processes._pidfd_send_signal(fd, signal.SIGTERM)
            finally: os.close(fd)
        else: switch_route(cfg, args.run, processes, restore=args.action == 'restore')
