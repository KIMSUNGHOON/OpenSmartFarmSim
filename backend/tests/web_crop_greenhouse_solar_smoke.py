"""Explicit hosted native HTTPS/WebGL check; WSL capacity is a separate hold."""
import ctypes
import importlib.util
import json
import os
from pathlib import Path
import signal
import subprocess
import sys
import tempfile
import time

ROOT = Path(__file__).resolve().parents[2]


def save(path, value):
    with path.open('x') as output:
        os.fchmod(output.fileno(), 0o400)
        json.dump(value, output, sort_keys=True, indent=2)
        output.flush()
        os.fsync(output.fileno())


def exercise(case, evidence):
    sys.path[:0] = [str(ROOT/'backend'), str(ROOT/'backend/tests')]
    import test_api_crop_greenhouse_solar_native as native
    prefix = native.HTTP_READ.split('thread=threading.Thread(')[0]
    needle = 'calls=measured(Patch());'
    assert prefix.count(needle) == 1
    prefix = prefix.replace(needle, 'import subprocess\nowned_transport_Popen=subprocess.Popen\n'
        "with candidates.read_scope('tenant-1'):\n"
        ' assert candidates._scoped_reader.get()[0] is sources._scoped_reader.get()[0]\n'
        ' assert candidates._scoped_references.get()[3] is not None\n'
        'shared_reader_observed=True\n'+needle)
    needle = "farm=p['body']['farm'];result_id=p['result_id'];before=counts(service)"
    assert prefix.count(needle) == 1
    prefix = prefix.replace(needle, needle+"\nwith jobs.connect() as conn:\n"
        " buffer_actual=conn.execute('SHOW shared_buffers').fetchone()['shared_buffers'];assert buffer_actual=='1MB'\n")
    native.HTTP_READ = prefix+(ROOT/'research/crop-greenhouse-solar-browser-read.py').read_text()
    os.environ.update(OSSF_SOLAR_BROWSER_SOURCE_ROOT=str(ROOT),
        OSSF_SOLAR_HTTP_EVIDENCE=str(evidence), OSSF_TEST_PG_SHARED_BUFFERS_MIB='1')
    with tempfile.TemporaryDirectory(prefix='owned-solar-WebGL-') as directory:
        native.exercise(Path(directory), None if case == 'completed' else 'hold')
    result = json.loads((evidence/('native-'+case+'.json')).read_bytes())
    assert result['actual_WebGL_browser'] and result['browser_exit_code'] == 0
    assert result['response_bytes_forwarded_unchanged'] and result['current_rights_scene_removed']
    assert result['reconnect_same_original_result'] and result['FD_before_after'] == [3, 3]
    assert result['actual_crop_Runs'] == 0 and result['G0_G4'] == 'not_assessed'


def supervise(case, evidence):
    spec = importlib.util.spec_from_file_location('owned_scope',
        ROOT/'research/owned-research-process-scope.py')
    scope_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(scope_module)
    assert ctypes.CDLL(None).prctl(36, 1, 0, 0, 0) == 0
    scope = scope_module.OwnedProcessScope()
    before = len(os.listdir('/proc/self/fd'))
    started = time.monotonic()
    one = total = samples = 0
    reason = None
    process = None
    peaks = {}
    try:
        with (evidence/'case.private.log').open('xb') as output:
            os.fchmod(output.fileno(), 0o600)
            process = subprocess.Popen([sys.executable, '-B', str(Path(__file__).resolve()),
                case, str(evidence)], stdin=subprocess.DEVNULL, stdout=output, stderr=subprocess.STDOUT)
            while process.poll() is None:
                rss = scope.sample()
                samples += 1
                one = max(one, max(rss.values(), default=0))
                total = max(total, sum(rss.values()))
                for pid, amount in rss.items():
                    peaks[str(pid)] = max(peaks.get(str(pid), 0), amount)
                if one > 512*1024**2 or total > 1024**3:
                    reason = 'RSS_limit'
                elif time.monotonic()-started > 600:
                    reason = 'wall_limit'
                if reason:
                    break
                time.sleep(.25)
    finally:
        scope.signal_owned(signal.SIGTERM)
        if process is not None and process.poll() is None:
            try:
                process.wait(timeout=15)
            except subprocess.TimeoutExpired:
                scope.signal_owned(signal.SIGKILL)
                process.wait(timeout=5)
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
    result = {'case':case, 'actual_child_exit':process.returncode, 'reason':reason,
        'wall_seconds':time.monotonic()-started, 'single_PID_peak_RSS_bytes':one,
        'combined_peak_RSS_bytes':total, 'sample_interval_seconds':.25, 'RSS_samples':samples,
        'RSS_peaks_by_PID':peaks, 'owned_non_zombie_remaining':remaining,
        'FD_before_after':[before, after], 'hosted_only':True, 'WSL_capacity_accepted':False,
        'actual_crop_Runs':0, 'G0_G4':'not_assessed', 'rights_or_gate_approval':False}
    save(evidence/('resource-'+case+'.json'), result)
    assert process.returncode == 0 and reason is None and not remaining and before == after, result


if __name__ == '__main__':
    assert os.environ.get('GITHUB_ACTIONS') == 'true', 'Hosted check only; use the protected WSL controller locally'
    case, directory = sys.argv[1:]
    evidence = Path(directory).resolve()
    if case == 'all':
        evidence.mkdir(mode=0o700)
        for status in ('completed', 'hold'):
            child = evidence/status
            child.mkdir(mode=0o700)
            supervise(status, child)
    else:
        assert case in ('completed', 'hold') and evidence.is_dir()
        exercise(case, evidence)
