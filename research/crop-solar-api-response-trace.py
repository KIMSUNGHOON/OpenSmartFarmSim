"""Opt-in bounded HTTP/worker-thread cost journal; never acceptance evidence."""
import json as _apiobs_json
import os as _apiobs_os
from pathlib import Path as _apiobs_Path
import sys as _apiobs_sys
import threading as _apiobs_threading
import time as _apiobs_time
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
    'schema_version':'solar-api-response-cost-v2',
    'time_scope':'inclusive nanoseconds; observer overhead included; nested times not additive',
    'server_scope':'protected synchronous execution/prefix body only; client CPU is not server CPU',
    'clocks':{name:{'implementation':_apiobs_time.get_clock_info(name).implementation[:96],
        'resolution_seconds':_apiobs_time.get_clock_info(name).resolution}
        for name in ('monotonic','thread_time')},
    'responses':[], 'server_operations':[], 'exceptions':[],
    'dropped_responses':0, 'dropped_server_operations':0, 'dropped_exceptions':0,
    'dropped_active_operations':0, 'dropped_counters':0}
_apiobs_lock = _apiobs_threading.Lock()
_apiobs_clients, _apiobs_servers = {}, {}
_apiobs_roots = {('api_crop_greenhouse_solar_execution_http.py','checked'):'execution',
    ('api_crop_greenhouse_solar_prefix_routes.py','read'):'prefix'}
_apiobs_counters = {('crop_greenhouse_solar_farm_binding.py','current'):'current_calls',
    ('crop_greenhouse_solar_storage.py','_load'):'storage_loads',
    ('market_source_store.py','_select_with_job'):'source_selects'}


def _apiobs_save():
    _apiobs_state['active_client_requests'] = [v['record'] for v in _apiobs_clients.values()]
    _apiobs_state['active_server_operations'] = [v['record'] for v in _apiobs_servers.values()]
    _apiobs_state['last_saved_monotonic_ns'] = _apiobs_time.monotonic_ns()
    raw = _apiobs_json.dumps(_apiobs_state, separators=(',', ':'), allow_nan=False).encode()
    while len(raw) > 64*1024:
        kind = next(k for k in ('exceptions','server_operations','responses') if _apiobs_state[k])
        del _apiobs_state[kind][0]
        _apiobs_state['dropped_'+kind] += 1
        raw = _apiobs_json.dumps(_apiobs_state, separators=(',', ':'), allow_nan=False).encode()
    temporary = _apiobs_root/('api-response-diagnostics.'+str(_apiobs_os.getpid())+'.tmp')
    fd = _apiobs_os.open(temporary, _apiobs_os.O_WRONLY | _apiobs_os.O_CREAT |
        _apiobs_os.O_EXCL | _apiobs_os.O_NOFOLLOW, 0o600)
    with _apiobs_os.fdopen(fd, 'wb') as output:
        output.write(raw)
    _apiobs_os.replace(temporary, _apiobs_root/'api-response-diagnostics.private.json')


def _apiobs_append(kind, item, maximum):
    rows = _apiobs_state[kind]
    rows.append(item)
    if len(rows) > maximum:
        del rows[0];_apiobs_state['dropped_'+kind] += 1
    _apiobs_save()


def _apiobs_route(frame):
    path = frame.f_locals.get('path')
    if type(path) is not str: return 'other'
    clean = path.partition('?')[0]
    if clean == '/v1/crop-greenhouse-solar-executions': return 'admission'
    if clean.startswith('/v1/jobs/'):
        for suffix, label in (('/crop-greenhouse-solar-execution','progress'),
                ('/crop-greenhouse-solar-execution/prefix','prefix'),
                ('/crop-greenhouse-solar-execution/prefix/samples','samples')):
            if clean.endswith(suffix): return label
    if clean.startswith('/v1/crop-greenhouse-solar-research-results/'): return 'saved_result'
    return 'other'


def _apiobs_begin(record):
    if len(_apiobs_clients) + len(_apiobs_servers) >= 16:
        _apiobs_state['dropped_active_operations'] += 1
        _apiobs_save()
        return None
    record['started_monotonic_ns'] = _apiobs_time.monotonic_ns()
    return {'record':record, 'CPU':_apiobs_time.thread_time_ns()}


def _apiobs_end(active, cpu_key):
    cpu = _apiobs_time.thread_time_ns()
    now = _apiobs_time.monotonic_ns()
    value = active['record']
    value.update(finished_monotonic_ns=now,
        wall_ns=now-value['started_monotonic_ns'])
    value[cpu_key] = cpu-active['CPU']
    return value


def _apiobs_count(record, key):
    if record[key] < 65536: record[key] += 1
    else: _apiobs_state['dropped_counters'] += 1


def _apiobs_trace(frame, event, arg):
    filename = frame.f_code.co_filename.rsplit('/', 1)[-1]
    function = frame.f_code.co_name
    response = filename == _apiobs_script and function == 'request_http'
    root = _apiobs_roots.get((filename,function))
    counter = _apiobs_counters.get((filename,function))
    if (root or counter) and frame.f_globals.get('__name__') != 'app.'+filename[:-3]:
        root = counter = None
    sql = (filename == 'connection.py' and function == 'execute'
        and frame.f_globals.get('__name__') == 'psycopg.connection')
    selected = response or root or filename in _apiobs_modules
    if not selected and not (sql or counter):
        return None
    thread = _apiobs_threading.get_ident()
    if not selected and thread not in _apiobs_servers: return None
    key = id(frame)
    if event == 'call':
        frame.f_trace_lines = False
        with _apiobs_lock:
            if response:
                active = _apiobs_begin({'route':_apiobs_route(frame),
                    'caller_line':frame.f_back.f_lineno if frame.f_back else None})
                if active is None: return None
                _apiobs_clients[key] = active
                _apiobs_save()
            elif root and thread not in _apiobs_servers:
                active = _apiobs_begin({'operation':root, 'SQL_calls':0, 'SQL_wall_ns':0,
                    'SQL_thread_CPU_ns':0, 'current_calls':0, 'storage_loads':0,
                    'source_selects':0, 'exception_events':0})
                if active is None: return None
                active.update(frame=key, SQL={})
                _apiobs_servers[thread] = active
                _apiobs_save()
            else:
                active = _apiobs_servers.get(thread)
                if active is not None:
                    if counter: _apiobs_count(active['record'],counter)
                    if sql:
                        _apiobs_count(active['record'],'SQL_calls')
                        if len(active['SQL']) < 16:
                            active['SQL'][key] = (_apiobs_time.monotonic_ns(),
                                _apiobs_time.thread_time_ns(), not active['SQL'])
                        else: _apiobs_state['dropped_active_operations'] += 1
        return _apiobs_trace if response or root or sql or filename in _apiobs_modules else None
    with _apiobs_lock:
        active = _apiobs_servers.get(thread)
        if event == 'exception':
            if active is not None and active['frame'] == key:
                _apiobs_count(active['record'],'exception_events')
            if filename in _apiobs_modules:
                kind, _, trace = arg
                _apiobs_append('exceptions', {'exception_type':kind.__name__[:96],
                    'locations':[{'file':_apiobs_Path(v.filename).name[:96],
                        'line':v.lineno, 'function':v.name[:96]}
                        for v in _apiobs_tb.extract_tb(trace)[-16:]]}, 16)
        elif event == 'return':
            if sql and active is not None:
                started = active['SQL'].pop(key,None)
                if started is not None and started[2]:
                    cpu = _apiobs_time.thread_time_ns();now = _apiobs_time.monotonic_ns()
                    active['record']['SQL_wall_ns'] += now-started[0]
                    active['record']['SQL_thread_CPU_ns'] += cpu-started[1]
            elif response:
                observed = _apiobs_clients.pop(key,None)
                if observed is not None:
                    item = _apiobs_end(observed,'client_thread_CPU_ns')
                    item['response_returned'] = False
                    if type(arg) is tuple and len(arg) == 2 and type(arg[0]) is int and 100 <= arg[0] <= 599:
                        status, body = arg
                        item.update(status=status,response_returned=True)
                        if type(body) is dict:
                            error = body.get('error')
                            code = error.get('code') if type(error) is dict else None
                            if type(code) is str and code in _apiobs_codes: item['code'] = code
                            prefix = body.get('prefix_status')
                            if type(prefix) is str and prefix in ('none','closed','accepted'):
                                item['prefix_status'] = prefix
                    _apiobs_append('responses',item,32)
            elif active is not None and active['frame'] == key:
                del _apiobs_servers[thread]
                item = _apiobs_end(active,'thread_CPU_ns')
                item['SQL_unfinished_calls'] = len(active['SQL'])
                _apiobs_append('server_operations',item,32)
    return _apiobs_trace


_apiobs_save()
_apiobs_threading.settrace(_apiobs_trace)
_apiobs_sys.settrace(_apiobs_trace)
