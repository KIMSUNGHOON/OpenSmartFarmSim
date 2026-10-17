"""API diagnostics expose actual statuses and exception locations, never bodies."""
import json
import os
from pathlib import Path
import subprocess
import sys

TRACE = Path(__file__).resolve().parents[2]/'research/crop-solar-api-response-trace.py'


def command(directory, body):
    target = str(directory/'api.private.py')
    script = ('from pathlib import Path\n__file__='+repr(target)+'\n'
        'exec(compile(Path('+repr(str(TRACE))+').read_text(),'+repr(str(TRACE))+',"exec"))\n'
        'exec(compile('+repr(body)+','+repr(target)+',"exec"))\n')
    return [sys.executable, '-B', '-c', script, str(directory/'pack')]


def read(directory):
    raw = (directory/'api-response-diagnostics.private.json').read_bytes()
    assert len(raw) <= 64*1024 and b'controlled_secret_never_export' not in raw
    return json.loads(raw)


def test_actual_http_status_and_fixed_code_exclude_raw_body(tmp_path):
    body = '''
def request_http():
 return 422, {'error':{'code':'solar_prefix_hold','message':'controlled_secret_never_export'},'private':'controlled_secret_never_export'}
request_http()
'''
    result = subprocess.run(command(tmp_path, body), capture_output=True, timeout=5)
    assert result.returncode == 0, result.stderr.decode()
    value = read(tmp_path)
    assert len(value['responses']) == 1
    assert value['responses'][0]['status'] == 422
    assert value['responses'][0]['code'] == 'solar_prefix_hold'
    assert value['responses'][0]['caller_line'] == 4
    assert value['diagnostic_only'] is True and value['normal_execution_accepted'] is False


def test_actual_threaded_prefix_exception_has_only_type_and_locations(tmp_path):
    body = r'''
import threading
exec(compile("def failed():\n try:raise ValueError('controlled_secret_never_export')\n except ValueError:pass\n", '/owned/app/crop_greenhouse_solar_prefix.py','exec'))
thread=threading.Thread(target=failed);thread.start();thread.join(2)
assert not thread.is_alive()
'''
    result = subprocess.run(command(tmp_path, body), capture_output=True, timeout=5)
    assert result.returncode == 0, result.stderr.decode()
    value = read(tmp_path)
    assert value['responses'] == []
    assert value['exceptions'][0]['exception_type'] == 'ValueError'
    assert value['exceptions'][0]['locations'] == [
        {'file':'crop_greenhouse_solar_prefix.py','line':2,'function':'failed'}]


def test_response_journal_is_bounded_and_unknown_codes_are_omitted(tmp_path):
    body = '''
def request_http():return 503, {'error':{'code':'controlled_secret_never_export'}}
for _ in range(100):request_http()
'''
    result = subprocess.run(command(tmp_path, body), capture_output=True, timeout=5)
    assert result.returncode == 0, result.stderr.decode()
    value = read(tmp_path)
    assert len(value['responses']) == 32 and value['dropped_responses'] == 68
    assert all(row['status'] == 503 and 'code' not in row for row in value['responses'])
    assert (tmp_path/'api-response-diagnostics.private.json').stat().st_mode & 0o777 == 0o600
    assert not list(tmp_path.glob('*.tmp'))
