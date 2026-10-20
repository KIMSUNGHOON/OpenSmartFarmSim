"""Hosted evaluation of one query scope candidate; no deployment or claim gate."""
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

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT/'backend/tests'), str(ROOT/'research')]
from crop_greenhouse_solar_unpaused_smoke import failure_locations, save


def application_digest():
    return {str(p.relative_to(ROOT)): sha256(p.read_bytes()).hexdigest()
            for p in sorted((ROOT/'backend/app').glob('*.py'))}


def evaluate(directory):
    assert os.environ.get('GITHUB_ACTIONS') == 'true', 'Hosted only; WSL uses its protected controller'
    directory.mkdir(mode=0o700, parents=True)
    spec = importlib.util.spec_from_file_location('owned_scope', ROOT/'research/owned-research-process-scope.py')
    owned = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(owned)
    assert ctypes.CDLL(None).prctl(36, 1, 0, 0, 0) == 0
    scope = owned.OwnedProcessScope()
    before = len(os.listdir('/proc/self/fd'))
    source = application_digest()
    started = time.monotonic()
    peak_one = peak_total = samples = 0
    reason = None
    child = None
    exits = {}
    temporary = tempfile.TemporaryDirectory(prefix='ossf-query-scope-')
    try:
        for phase, name, expected in [('functional', 'cases', 11), ('cost', 'cost', 1)]:
            destination = directory/phase
            destination.mkdir(mode=0o700)
            environment = dict(os.environ, TMPDIR=temporary.name,
                PYTHONPATH=os.pathsep.join(str(ROOT/p) for p in ('backend', 'backend/tests', 'research')),
                OSSF_SOLAR_EXECUTION_QUERY_EVIDENCE=str(destination),
                OSSF_QUERY_SCOPE_EVIDENCE=str(destination), OSSF_TEST_PG_SHARED_BUFFERS_MIB='4',
                PGOPTIONS='-c work_mem=64kB -c jit=off')
            log = destination/'pytest.private.log'
            with log.open('xb') as output:
                os.fchmod(output.fileno(), 0o600)
                child = subprocess.Popen([sys.executable, '-B', '-m', 'pytest',
                    str(ROOT/f'research/solar_query_scope_{name}.py'), '-q', '-rf', '--maxfail=1',
                    '--basetemp', str(destination/'pytest')], cwd=ROOT/'backend', env=environment,
                    stdin=subprocess.DEVNULL, stdout=output, stderr=subprocess.STDOUT)
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
            if reason:
                break
            exits[phase] = child.returncode
            raw = log.read_text(errors='replace')
            if child.returncode != 0 or not re.search(rf'\b{expected} passed\b', raw) or ' skipped' in raw:
                save(directory/'failure.json', {'phase': phase, 'exit_code': child.returncode,
                    'log': failure_locations(raw), 'normal64_accepted': False,
                    'failed_nodes': [line.split(' - ', 1)[0] for line in raw.splitlines() if line.startswith('FAILED ')]})
                break
            assert json.loads((destination/'database-cleanup.json').read_bytes()) == {'schemas': 0, 'roles': 0}
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
        temporary_entries = len(list(Path(temporary.name).iterdir()))
        temporary.cleanup()
        remaining = [i._asdict() for i in scope.remaining()]
        after = len(os.listdir('/proc/self/fd'))
        save(directory/'resource.json', {'phase_exits': exits, 'reason': reason,
            'wall_seconds': time.monotonic()-started, 'single_PID_peak_RSS_bytes': peak_one,
            'combined_peak_RSS_bytes': peak_total, 'RSS_samples': samples, 'sample_interval_seconds': .25,
            'FD_before_after': [before, after], 'owned_non_zombie_remaining': remaining,
            'temporary_entries_before_cleanup': temporary_entries,
            'application_source_preserved': application_digest() == source,
            'hosted_only': True, 'WSL_capacity_accepted': False, 'normal64_accepted': False,
            'product_adopted': False, 'new_Solar_deployed': False, 'G0_G4': 'not_assessed'})
    assert reason is None and exits == {'functional': 0, 'cost': 0}
    assert before == after and not remaining and temporary_entries == 0 and application_digest() == source
    assert (directory/'cost/query-current-scope-actual-HTTPS-ABBA.json').is_file()
    save(directory/'provenance.json', {'source_commit': os.environ['GITHUB_SHA'],
        'run_id': os.environ['GITHUB_RUN_ID'], 'run_attempt': os.environ['GITHUB_RUN_ATTEMPT'],
        'application_source_SHA256': sha256(json.dumps(source, sort_keys=True, separators=(',', ':')).encode()).hexdigest(),
        'evaluation_files': {str(p.relative_to(ROOT)): sha256(p.read_bytes()).hexdigest() for p in
            [ROOT/f'research/solar_query_scope_{n}.py' for n in ('candidate', 'cases', 'cost', 'hosted')]},
        'criteria_SHA256': sha256((ROOT/'research/artifacts/solar-query-current-registration-scope-criteria-20261020.json').read_bytes()).hexdigest(),
        'original_CASE6_64': True, 'normal64_accepted': False, 'product_adopted': False})


if __name__ == '__main__':
    evaluate(Path(sys.argv[1]).resolve())
