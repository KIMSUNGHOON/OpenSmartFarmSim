"""Diagnostic header: fixed HTTP metadata and prefix exception locations only."""
import json as _apiobs_json
import os as _apiobs_os
from pathlib import Path as _apiobs_Path
import sys as _apiobs_sys
import threading as _apiobs_threading
import traceback as _apiobs_tb

_apiobs_root = _apiobs_Path(_apiobs_sys.argv[1]).parent
assert _apiobs_root.is_dir() and not _apiobs_root.is_symlink()
assert _apiobs_root.stat().st_uid == _apiobs_os.getuid()
_apiobs_script = _apiobs_Path(__file__).name
_apiobs_modules = frozenset({'crop_greenhouse_solar_prefix.py',
    'api_crop_greenhouse_solar_prefix.py', 'api_crop_greenhouse_solar_prefix_routes.py'})
_apiobs_codes = frozenset({'invalid_request', 'solar_prefix_hold',
    'solar_prefix_selection_conflict', 'solar_prefix_unavailable', 'forbidden',
    'not_found', 'unauthorized', 'solar_execution_hold', 'solar_execution_unavailable'})
_apiobs_state = {'diagnostic_only':True, 'normal_execution_accepted':False,
    'responses':[], 'exceptions':[], 'dropped_responses':0, 'dropped_exceptions':0}
_apiobs_lock = _apiobs_threading.Lock()


def _apiobs_save():
    raw = _apiobs_json.dumps(_apiobs_state, separators=(',', ':'), allow_nan=False).encode()
    assert len(raw) <= 64*1024
    temporary = _apiobs_root/('api-response-diagnostics.'+str(_apiobs_os.getpid())+'.tmp')
    fd = _apiobs_os.open(temporary, _apiobs_os.O_WRONLY | _apiobs_os.O_CREAT |
        _apiobs_os.O_EXCL | _apiobs_os.O_NOFOLLOW, 0o600)
    with _apiobs_os.fdopen(fd, 'wb') as output:
        output.write(raw)
    _apiobs_os.replace(temporary, _apiobs_root/'api-response-diagnostics.private.json')


def _apiobs_append(kind, item, maximum):
    with _apiobs_lock:
        rows = _apiobs_state[kind]
        rows.append(item)
        if len(rows) > maximum:
            del rows[0];_apiobs_state['dropped_'+kind] += 1
        _apiobs_save()


def _apiobs_trace(frame, event, arg):
    filename = frame.f_code.co_filename.rsplit('/', 1)[-1]
    response = filename == _apiobs_script and frame.f_code.co_name == 'request_http'
    if not response and filename not in _apiobs_modules:
        return None
    if event == 'call':
        frame.f_trace_lines = False
    if response and event == 'return' and type(arg) is tuple and len(arg) == 2:
        status, body = arg
        if type(status) is int and 100 <= status <= 599:
            item = {'status':status, 'caller_line':frame.f_back.f_lineno if frame.f_back else None}
            if type(body) is dict:
                error = body.get('error')
                code = error.get('code') if type(error) is dict else None
                if type(code) is str and code in _apiobs_codes:
                    item['code'] = code
                prefix = body.get('prefix_status')
                if type(prefix) is str and prefix in ('none', 'closed', 'accepted'):
                    item['prefix_status'] = prefix
            _apiobs_append('responses', item, 32)
    elif event == 'exception' and filename in _apiobs_modules:
        kind, _, trace = arg
        _apiobs_append('exceptions', {'exception_type':kind.__name__[:96],
            'locations':[{'file':_apiobs_Path(v.filename).name[:96],
                'line':v.lineno, 'function':v.name[:96]}
                for v in _apiobs_tb.extract_tb(trace)[-16:]]}, 16)
    return _apiobs_trace


_apiobs_save()
_apiobs_threading.settrace(_apiobs_trace)
_apiobs_sys.settrace(_apiobs_trace)
