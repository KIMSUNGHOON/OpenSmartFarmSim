"""Observe execution metadata without exporting inputs, locals, or messages."""
import json
import os
from pathlib import Path
import select
import signal
import subprocess
import sys


TRACE = Path(__file__).resolve().parents[2]/'research/crop-solar-worker-progress-trace.py'
TARGET = '/owned/app/crop_greenhouse_solar_execution_worker.py'


def command(directory, body):
    script = ('from pathlib import Path\n'
        + 'exec(compile(Path('+repr(str(TRACE))+').read_text(),'+repr(str(TRACE))+',"exec"))\n'
        + 'exec(compile('+repr(body)+','+repr(TARGET)+',"exec"))\n')
    return [sys.executable, '-B', '-c', script, str(directory/'pack')]


def test_progress_uses_returned_checkpoint_and_excludes_private_values(tmp_path):
    body = '''
def _before():
 private = "controlled_secret_never_export"
 return private.encode()
def _confirm():
 return {'checkpoint': {'steps': 8, 'planned_steps': 64, 'status': 'yielded',
  'computed_through_utc': '2026-10-17T00:00:16Z', 'private': 'controlled_secret_never_export'}}
def caught():
 try:raise ValueError('controlled_secret_never_export')
 except ValueError:pass
_before();_confirm();caught()
'''
    result = subprocess.run(command(tmp_path, body), capture_output=True, timeout=5)
    assert result.returncode == 0, result.stderr.decode()
    raw = (tmp_path/'worker-progress-diagnostics.private.json').read_bytes()
    errors = (tmp_path/'worker-caught-diagnostics.private.json').read_bytes()
    assert b'controlled_secret_never_export' not in raw+errors
    value = json.loads(raw)
    assert value['last_confirmed'] == {'steps':8, 'planned_steps':64, 'status':'yielded',
        'computed_through_utc':'2026-10-17T00:00:16Z'}
    assert value['phase_totals']['worker._confirm']['returns'] == 1
    assert value['observation_only'] and value['normal_execution_accepted'] is False


def test_recent_records_and_file_size_remain_bounded(tmp_path):
    body = 'def _before():return b"private"\nfor _ in range(100):_before()\n'
    result = subprocess.run(command(tmp_path, body), capture_output=True, timeout=5)
    assert result.returncode == 0, result.stderr.decode()
    raw = (tmp_path/'worker-progress-diagnostics.private.json').read_bytes()
    value = json.loads(raw)
    assert len(raw) <= 64*1024 and len(value['recent_events']) <= 32
    assert value['phase_totals']['worker._before']['calls'] == 100
    assert value['phase_totals']['worker._before']['returns'] == 100
    assert value['dropped_recent_events'] > 0


def test_termination_inside_a_phase_preserves_atomic_inflight_evidence(tmp_path):
    body = 'import time\ndef _before():\n print("ready",flush=True);time.sleep(30)\n_before()\n'
    child = subprocess.Popen(command(tmp_path, body), stdin=subprocess.DEVNULL,
        stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    descriptor = os.pidfd_open(child.pid)
    try:
        assert select.select([child.stdout], [], [], 5)[0]
        assert child.stdout.readline() == b'ready\n'
        signal.pidfd_send_signal(descriptor, signal.SIGTERM)
        assert child.wait(timeout=5) == -signal.SIGTERM
    finally:
        if child.poll() is None:
            signal.pidfd_send_signal(descriptor, signal.SIGKILL)
            child.wait(timeout=5)
        os.close(descriptor)
        child.stdout.close();child.stderr.close()
    value = json.loads((tmp_path/'worker-progress-diagnostics.private.json').read_bytes())
    assert value['active_phases'][0]['phase'] == 'worker._before'
    assert value['phase_totals']['worker._before']['calls'] == 1
    assert value['phase_totals']['worker._before']['returns'] == 0
