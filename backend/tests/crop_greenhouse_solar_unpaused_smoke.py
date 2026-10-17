"""Explicit hosted normal execution proof; no WSL capacity or deployment claim."""
import ctypes
from hashlib import sha256
import importlib.util
import json
import os
from pathlib import Path
import re
import signal
import subprocess
import sys
import tempfile
import time
import traceback

ROOT = Path(__file__).resolve().parents[2]
PROTOTYPE = ROOT/'research/crop-greenhouse-solar-unpaused-probe.py'
WORKER_TRACE = (ROOT/'research/crop-solar-worker-progress-trace.py').read_text()
API_TRACE = (ROOT/'research/crop-solar-api-response-trace.py').read_text()


def save(path, value):
    with path.open('x') as output:
        os.fchmod(output.fileno(), 0o400)
        json.dump(value, output, sort_keys=True, indent=2)
        output.flush()
        os.fsync(output.fileno())


def failure_locations(raw):
    locations, kinds = [], []
    for line in raw.splitlines():
        location = re.fullmatch(r'\s*File "([^"]+)", line (\d+), in ([\w.<>]+)', line)
        if location:
            locations.append({'file':Path(location[1]).name, 'line':int(location[2]), 'function':location[3]})
        kind = re.match(r'^([A-Za-z_][\w.]*(?:Error|Exception|Hold|Lost|Timeout|Failure|Interrupt))(?::|$)', line)
        if kind:
            kinds.append(kind[1])
    return {'locations':locations[-16:], 'exception_types':kinds[-8:]}


def exercise(evidence):
    sys.path[:0] = [str(ROOT/'backend'), str(ROOT/'backend/tests')]
    spec = importlib.util.spec_from_file_location('original_unpaused', PROTOTYPE)
    prototype = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(prototype)
    diagnostic = os.environ.get('OSSF_SOLAR_TRACE_WORKER') == '1'
    if diagnostic:
        prototype.WORKER = WORKER_TRACE + prototype.WORKER
        if os.environ.get('OSSF_SOLAR_DIAGNOSTIC_DETAIL') == 'worker-api':
            prototype.API = API_TRACE + prototype.API
    os.environ['OSSF_SOLAR_EXECUTION_RUNTIME_EVIDENCE'] = str(evidence)
    original_run, original_popen = subprocess.run, subprocess.Popen
    actors = []
    processes = []
    cleanup_seen = []

    def observe_run(argv, *args, **kwargs):
        if Path(str(argv[0])).name == 'pg_ctl' and 'stop' in argv:
            diagnostics = []
            for process, script in processes:
                log = script.with_suffix('.log')
                diagnostics.append({'role':script.stem.split('.')[0], 'exit_code':process.poll(),
                    'script_sha256':sha256(script.read_bytes()).hexdigest(),
                    'log':failure_locations(log.read_text(errors='replace')) if log.exists() else None,
                    'worker_proof_present':(script.parent/'worker-proof.private.json').exists(),
                    'api_proof_present':(script.parent/'api-proof.private.json').exists(),
                    'client_proof_present':(script.parent/'api-client-proof.private.json').exists()})
            if processes:
                api_trace = processes[0][1].parent/'api-response-diagnostics.private.json'
                if api_trace.exists():
                    assert api_trace.stat().st_size <= 64*1024
                    save(evidence/'api-response-diagnostics.json', {
                        'diagnostic_only':True, 'normal_execution_accepted':False,
                        'source_commit':os.environ['GITHUB_SHA'], 'run_id':os.environ['GITHUB_RUN_ID'],
                        'prototype_sha256':sha256(PROTOTYPE.read_bytes()).hexdigest(),
                        'trace_header_sha256':sha256(API_TRACE.encode()).hexdigest(),
                        'api_script_sha256':sha256(processes[0][1].read_bytes()).hexdigest(),
                        'observations':json.loads(api_trace.read_bytes())})
                caught = processes[-1][1].parent/'worker-caught-diagnostics.private.json'
                if caught.exists():
                    save(evidence/'worker-caught-diagnostics.json', json.loads(caught.read_bytes()))
                progress = processes[-1][1].parent/'worker-progress-diagnostics.private.json'
                if progress.exists():
                    assert progress.stat().st_size <= 64*1024
                    save(evidence/'worker-progress-diagnostics.json', {
                        'diagnostic_only':True, 'normal_execution_accepted':False,
                        'source_commit':os.environ['GITHUB_SHA'], 'run_id':os.environ['GITHUB_RUN_ID'],
                        'prototype_sha256':sha256(PROTOTYPE.read_bytes()).hexdigest(),
                        'trace_header_sha256':sha256(WORKER_TRACE.encode()).hexdigest(),
                        'worker_script_sha256':sha256(processes[-1][1].read_bytes()).hexdigest(),
                        'collected_monotonic':time.monotonic(), 'phases':json.loads(progress.read_bytes())})
            save(evidence/'actor-diagnostics.json', diagnostics)
        result = original_run(argv, *args, **kwargs)
        if len(argv) == 5 and argv[2:4] == ['-c', prototype.CLEANUP]:
            assert result.returncode == 0
            value = json.loads(result.stdout)
            assert value == {'roles': 0, 'schemas': 0}
            cleanup_seen.append(value)
            save(evidence/'database-cleanup.json', value)
        return result

    def observe_popen(argv, *args, **kwargs):
        actor = original_popen(argv, *args, **kwargs)
        if len(argv) == 4 and Path(str(argv[2])).name in ('api.private.py', 'worker.private.py'):
            processes.append((actor, Path(argv[2])))
            actors.append({'role':Path(argv[2]).stem.split('.')[0], 'PID':actor.pid,
                'script_sha256':sha256(Path(argv[2]).read_bytes()).hexdigest()})
        return actor

    subprocess.run, subprocess.Popen = observe_run, observe_popen
    try:
        with tempfile.TemporaryDirectory(prefix='owned-solar-unpaused-') as directory:
            prototype.exercise(Path(directory))
    except Exception as error:
        known = {'owned preparation failed', 'owned API startup failed', 'owned HTTP admission failed',
                 'owned calculation timed out or failed'}
        save(evidence/'failure.json', {'exception_type':type(error).__name__,
            'known_stage':str(error) if str(error) in known else None,
            'locations':[{'file':Path(item.filename).name, 'line':item.lineno, 'function':item.name}
                         for item in traceback.extract_tb(error.__traceback__)[-16:]],
            'original_normal_accepted':False})
        raise
    finally:
        subprocess.run, subprocess.Popen = original_run, original_popen
    proof = json.loads((evidence/'unpaused-normal.private.json').read_bytes())
    assert cleanup_seen == [{'roles': 0, 'schemas': 0}]
    assert [a['role'] for a in actors] == ['api', 'worker']
    assert proof['worker']['PID'] == actors[1]['PID'] != proof['client']['client_PID'] == actors[0]['PID']
    assert proof['worker']['calls']['step'] == 64 and proof['worker']['calls']['start'] == 1
    assert proof['worker']['calls']['CLI'] == 0 and proof['worker']['unpaused']
    assert proof['advancing_prefixes'] >= 2 and proof['original_values_UTC_equal']
    assert proof['api']['FD_unchanged'] and not any(proof['api']['calls'].values())
    save(evidence/'normal.json', {'original_proof':proof, 'actors':actors,
        'prototype_sha256':sha256(PROTOTYPE.read_bytes()).hexdigest(),
        'original_actor_program_and_arguments_unchanged':not diagnostic,
        'diagnostic_observation_only':diagnostic,
        'hosted_only':True, 'WSL_capacity_accepted':False,
        'source_commit':os.environ['GITHUB_SHA'], 'run_id':os.environ['GITHUB_RUN_ID'],
        'actual_crop_Runs':0, 'G0_G4':'not_assessed', 'rights_or_gate_approval':False})


def supervise(evidence):
    spec = importlib.util.spec_from_file_location('owned_scope', ROOT/'research/owned-research-process-scope.py')
    owned = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(owned)
    assert ctypes.CDLL(None).prctl(36, 1, 0, 0, 0) == 0
    scope = owned.OwnedProcessScope()
    before = len(os.listdir('/proc/self/fd'))
    started = time.monotonic()
    peak_one = peak_total = samples = 0
    reason = None
    child = None
    temporary = evidence/'temporary'
    temporary.mkdir(mode=0o700)
    environment = dict(os.environ, TMPDIR=str(temporary))
    try:
        with (evidence/'case.private.log').open('xb') as output:
            os.fchmod(output.fileno(), 0o600)
            child = subprocess.Popen([sys.executable, '-B', str(Path(__file__).resolve()),
                'exercise', str(evidence)], env=environment, stdin=subprocess.DEVNULL,
                stdout=output, stderr=subprocess.STDOUT)
            while child.poll() is None:
                rss = scope.sample()
                samples += 1
                peak_one = max(peak_one, max(rss.values(), default=0))
                peak_total = max(peak_total, sum(rss.values()))
                if peak_one > 512*1024**2 or peak_total > 1024**3:
                    reason = 'RSS_limit'
                elif time.monotonic()-started > 600:
                    reason = 'wall_limit'
                if reason:
                    break
                time.sleep(.25)
    finally:
        scope.signal_owned(signal.SIGTERM)
        if child is not None and child.poll() is None:
            try:
                child.wait(timeout=15)
            except subprocess.TimeoutExpired:
                scope.signal_owned(signal.SIGKILL)
                child.wait(timeout=5)
        deadline = time.monotonic()+10
        while scope.remaining() and time.monotonic() < deadline:
            time.sleep(.1)
        if scope.remaining():
            scope.signal_owned(signal.SIGKILL)
        while True:
            try:
                if os.waitpid(-1, os.WNOHANG)[0] == 0:
                    break
            except ChildProcessError:
                break
    remaining = [i._asdict() for i in scope.remaining()]
    after = len(os.listdir('/proc/self/fd'))
    temporary_entries = sum(1 for _ in temporary.iterdir())
    result = {'actual_child_exit':child.returncode, 'reason':reason,
        'wall_seconds':time.monotonic()-started, 'single_PID_peak_RSS_bytes':peak_one,
        'combined_peak_RSS_bytes':peak_total, 'RSS_samples':samples, 'sample_interval_seconds':.25,
        'FD_before_after':[before, after], 'owned_non_zombie_remaining':remaining,
        'temporary_entries_remaining':temporary_entries,
        'hosted_only':True, 'WSL_capacity_accepted':False, 'local_protected_roots_present':False,
        'actual_crop_Runs':0, 'G0_G4':'not_assessed', 'rights_or_gate_approval':False}
    save(evidence/'resource.json', result)
    assert child.returncode == 0 and reason is None and before == after and not remaining and temporary_entries == 0, result
    assert (evidence/'normal.json').is_file() and (evidence/'database-cleanup.json').is_file()
    assert os.environ.get('OSSF_SOLAR_TRACE_WORKER') != '1', 'Diagnostic observations cannot accept normal execution'


if __name__ == '__main__':
    assert os.environ.get('GITHUB_ACTIONS') == 'true', 'Hosted only; use the protected controller on WSL'
    mode, directory = sys.argv[1:]
    evidence = Path(directory).resolve()
    if mode == 'supervise':
        evidence.mkdir(mode=0o700)
        supervise(evidence)
    else:
        assert mode == 'exercise' and evidence.is_dir()
        exercise(evidence)
