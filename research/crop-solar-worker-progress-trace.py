"""Opt-in synthetic worker observation header; never normal acceptance evidence."""
import json as _obs_json
import os as _obs_os
from pathlib import Path as _obs_Path
import re as _obs_re
import sys as _obs_sys
import time as _obs_time
import traceback as _obs_tb

_obs_root = _obs_Path(_obs_sys.argv[1]).parent
assert _obs_root.is_dir() and not _obs_root.is_symlink()
assert _obs_root.stat().st_uid == _obs_os.getuid()
_obs_started = _obs_time.monotonic()
_obs_worker = 'crop_greenhouse_solar_execution_worker.py'
_obs_detail = _obs_os.environ.get('OSSF_SOLAR_DIAGNOSTIC_DETAIL', 'phases')
assert _obs_detail in ('phases', 'worker')
_obs_phases = {
    _obs_worker: frozenset({'run_once', '_before', '_adopt', '_custody_call', '_confirm', '_finish'}),
    'crop_greenhouse_solar_server_custody.py': frozenset({'advance', '_guard', '_load', 'progress', 'prepare'}),
    'crop_greenhouse_solar_farm_binding.py': frozenset({'current', '_guard', '_input', '_registration'}),
    'crop_greenhouse_solar_input_evidence.py': frozenset({'verify'}),
    'farm_authoring_storage.py': frozenset({'read_registration', '_guard', '_prepare', '_find'}),
    'owned_research.py': frozenset({'authority_snapshot'}),
    'thermal_run_store.py': frozenset({'get_snapshot', 'get_decision_context'}),
    'market_hold_store.py': frozenset({'get_market_hold_report'}),
    'market_scenario.py': frozenset({'validate_pinned'}),
    'farm_input_compiler.py': frozenset({'compile_farm_inputs'}),
    'crop_greenhouse_solar_continuation.py': frozenset({'prepare_context', 'advance_chunk', 'restore_checkpoint'}),
}
_obs_prefixes = {'crop_greenhouse_solar_server_custody.py':'custody',
    'crop_greenhouse_solar_farm_binding.py':'binding', 'crop_greenhouse_solar_input_evidence.py':'evidence',
    'farm_authoring_storage.py':'farm', 'crop_greenhouse_solar_continuation.py':'model',
    'owned_research.py':'research', 'thermal_run_store.py':'thermal',
    'market_hold_store.py':'hold', 'market_scenario.py':'market', 'farm_input_compiler.py':'compiler'}
if _obs_detail == 'worker':
    _obs_phases = {_obs_worker:_obs_phases[_obs_worker]}
_obs_totals, _obs_active, _obs_recent, _obs_errors = {}, {}, [], []
_obs_dropped = 0
_obs_last_confirmed = _obs_last_advanced = _obs_last_adopted = _obs_outcome = None


def _obs_write(name, value):
    raw = _obs_json.dumps(value, separators=(',', ':'), allow_nan=False).encode()
    if len(raw) > 64*1024:
        raise RuntimeError('diagnostic capacity exceeded')
    temporary = _obs_root/(name+'.'+str(_obs_os.getpid())+'.tmp')
    fd = _obs_os.open(temporary, _obs_os.O_WRONLY | _obs_os.O_CREAT | _obs_os.O_EXCL | _obs_os.O_NOFOLLOW, 0o600)
    with _obs_os.fdopen(fd, 'wb') as stream:
        stream.write(raw)
    _obs_os.replace(temporary, _obs_root/name)


def _obs_progress(value):
    if type(value) is bytes and len(value) <= 2*1024**2:
        try: value = _obs_json.loads(value)
        except (ValueError, UnicodeError): return None
    if type(value) is not dict:
        return None
    if not {'steps', 'planned_steps', 'status'} <= value.keys() and 'checkpoint' in value:
        value = value['checkpoint']
    if (type(value) is not dict or type(value.get('steps')) is not int
            or type(value.get('planned_steps')) is not int
            or not 0 <= value['steps'] <= value['planned_steps'] <= 2**63-1
            or value.get('status') not in ('ready', 'yielded', 'completed', 'hold')):
        return None
    record = {key:value[key] for key in ('steps', 'planned_steps', 'status')}
    stamp = value.get('computed_through_utc')
    if 'computed_through_utc' not in value and type(value.get('times')) is dict:
        selected = value['times'].get('last_confirmed')
        if type(selected) is dict:
            stamp = selected.get('at')
    if stamp is None or (type(stamp) is str and _obs_re.fullmatch(
            r'\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d{1,6})?Z', stamp)):
        record['computed_through_utc'] = stamp
    return record


def _obs_dump(now):
    _obs_write('worker-progress-diagnostics.private.json', {
        'version':'solar-worker-progress-observation-v2', 'observation_only':True,
        'detail':_obs_detail,
        'normal_execution_accepted':False, 'G0_G4':'not_assessed',
        'time_scope':'inclusive monotonic seconds; observer overhead included; nested durations overlap',
        'trace_installed_monotonic':_obs_started, 'last_observed_monotonic':now,
        'phase_totals':_obs_totals, 'recent_events':_obs_recent,
        'dropped_recent_events':_obs_dropped,
        'active_phases':[{'phase':v[0], 'started_elapsed_seconds':v[1]-_obs_started}
                         for v in _obs_active.values()],
        'last_confirmed':_obs_last_confirmed, 'last_advanced':_obs_last_advanced,
        'last_adopted':_obs_last_adopted, 'outcome':_obs_outcome})


def _obs_trace(frame, event, arg):
    global _obs_dropped, _obs_last_confirmed, _obs_last_advanced, _obs_last_adopted, _obs_outcome
    filename = frame.f_code.co_filename.rsplit('/', 1)[-1]
    function = frame.f_code.co_name
    selected = function in _obs_phases.get(filename, ())
    if not selected and filename != _obs_worker:
        return None
    phase = ('worker.'+function if filename == _obs_worker
             else _obs_prefixes[filename]+'.'+frame.f_code.co_qualname)
    if event == 'call':
        frame.f_trace_lines = False
    if event == 'exception' and filename == _obs_worker:
        kind, _, trace = arg
        _obs_errors.append({'exception_type':kind.__name__[:96], 'locations':[
            {'file':_obs_Path(v.filename).name[:96], 'line':v.lineno, 'function':v.name[:96]}
            for v in _obs_tb.extract_tb(trace)[-16:]]})
        del _obs_errors[:-16]
        _obs_write('worker-caught-diagnostics.private.json', _obs_errors)
    if not selected or event not in ('call', 'return', 'exception'):
        return _obs_trace
    now = _obs_time.monotonic()
    metrics = _obs_totals.setdefault(phase, {'calls':0, 'returns':0, 'exception_events':0,
        'inclusive_seconds':0.0, 'max_inclusive_seconds':0.0})
    item = {'phase':phase, 'event':event, 'elapsed_seconds':now-_obs_started}
    if event == 'call':
        assert len(_obs_active) < 16
        _obs_active[id(frame)] = (phase, now)
        metrics['calls'] += 1
    elif event == 'exception':
        metrics['exception_events'] += 1
    else:
        started = _obs_active.pop(id(frame), (phase, now))[1]
        duration = now-started
        metrics['returns'] += 1
        metrics['inclusive_seconds'] += duration
        metrics['max_inclusive_seconds'] = max(metrics['max_inclusive_seconds'], duration)
        item['inclusive_seconds'] = duration
        if phase == 'worker._confirm': _obs_last_confirmed = _obs_progress(arg) or _obs_last_confirmed
        if phase == 'custody.SolarServerCustody.advance': _obs_last_advanced = _obs_progress(arg) or _obs_last_advanced
        if phase == 'worker._adopt': _obs_last_adopted = _obs_progress(arg) or _obs_last_adopted
        if phase == 'worker.run_once' and type(arg).__name__ == 'SolarExecutionOutcome':
            if (arg.state in ('queued', 'succeeded', 'failed', 'hold', 'canceled', 'unclosed')
                    and type(arg.attempt) is int and 1 <= arg.attempt <= 3):
                _obs_outcome = {'state':arg.state, 'attempt':arg.attempt}
                if arg.reason_code in ('completed', 'solar_numerical_hold', 'solar_execution_busy',
                        'solar_execution_hold', 'solar_execution_runtime_failure',
                        'canceled_by_request', 'solar_execution_lease_lost'):
                    _obs_outcome['reason_code'] = arg.reason_code
    _obs_recent.append(item)
    if len(_obs_recent) > 32:
        del _obs_recent[0]; _obs_dropped += 1
    _obs_dump(now)
    return _obs_trace


_obs_dump(_obs_started)
_obs_sys.settrace(_obs_trace)
