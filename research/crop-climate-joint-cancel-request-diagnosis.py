"""Trace an actual cancel after public prefix reads; never trace or pause the worker."""
from hashlib import sha256
from contextlib import contextmanager
import importlib.util
import http.client
import json
import re
from pathlib import Path
import sys
import threading
import time
from urllib.parse import urlencode

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'backend/tests'))
import psycopg
import pytest
from psycopg.rows import dict_row
import test_crop_climate_joint_prefix_runtime as reference

spec = importlib.util.spec_from_file_location('cancel_small_cluster',
    ROOT / 'research/crop-climate-joint-prefix-lease-guard-reference.py')
small = importlib.util.module_from_spec(spec)
spec.loader.exec_module(small)
login_database = small.login_database
pytest_plugins = ['test_crop_climate_joint_prefix_runtime']


@reference.LOGIN
@pytest.mark.parametrize('api_trace', [True, False], ids=['traced', 'untraced'])
def test_diagnose_actual_progress_prefix_cancel_sequence(prefix_native, login_database, tmp_path, monkeypatch, api_trace):
    c = prefix_native
    requests, trace, locks, observer_errors = [], [], [], []
    active = None
    frames = {}
    stopped = threading.Event()
    modules = {'api_crop_climate_joint_execution.py': {'invoke', 'action', 'target', 'after'},
        'job_store.py': {'cancel', '_locked_job', '_has_scope'},
        'crop_climate_joint_execution_query.py': {'_checkpoint', '_current'},
        'crop_climate_joint_result_store.py': {'_session'},
        'crop_climate_joint_server_custody.py': {'_open'}}

    def observe(frame, event, arg):
        module, name = Path(frame.f_code.co_filename).name, frame.f_code.co_name
        if (active is None or '/backend/app/' not in frame.f_code.co_filename
                or name not in modules.get(module, ())):
            return None
        frame.f_trace_lines = False
        try:
            key = id(frame)
            if event == 'call' and key not in frames:
                frames[key] = (active, time.monotonic())
            if key not in frames:
                return observe
            request_id, started = frames[key]
            item = {'request_id': request_id, 'module': module, 'function': name,
                'event': event, 'line': frame.f_lineno, 'at_monotonic': time.monotonic(),
                'at_wall_seconds': time.time()}
            if event == 'exception':
                kind, error, _ = arg
                if kind.__name__ in ('StopIteration', 'GeneratorExit', 'StopAsyncIteration'):
                    return observe
                item.update(exception=kind.__name__, sqlstate=getattr(error, 'sqlstate', None))
            if name == '_locked_job':
                item['PG_backend_pid'] = frame.f_locals['conn'].info.backend_pid
            if event == 'return':
                item['seconds'] = time.monotonic() - started
                if name in ('_open', '_session', '_checkpoint') and type(arg) is tuple:
                    item['event'] = 'yield'
                else:
                    frames.pop(key)
            assert len(trace) < 2000
            trace.append(item)
        except Exception as error:
            observer_errors.append({'module': module, 'function': name, 'error': type(error).__name__})
        return observe

    def monitor():
        try:
            with psycopg.connect(login_database['admin'], autocommit=True, row_factory=dict_row) as conn:
                conn.execute('SET default_transaction_read_only=on')
                previous = None
                while not stopped.is_set():
                    rows = conn.execute("""SELECT pid, state, wait_event_type, wait_event,
                        pg_blocking_pids(pid) AS blockers,
                        CASE WHEN query LIKE '%%FOR UPDATE%%' THEN 'row_lock'
                            WHEN query LIKE '%%INSERT INTO%%' THEN 'insert'
                            WHEN query LIKE '%%UPDATE %%' THEN 'update'
                            ELSE 'other' END AS query_shape,
                        extract(epoch FROM clock_timestamp()-xact_start)::float8 AS transaction_age_seconds
                        FROM pg_stat_activity WHERE datname=current_database()
                            AND pid<>pg_backend_pid() AND backend_type='client backend'
                            AND (wait_event_type='Lock' OR state='idle in transaction')""").fetchall()
                    signature = [(r['pid'], r['state'], r['wait_event_type'], r['wait_event'],
                        r['blockers'], r['query_shape']) for r in rows]
                    if signature != previous:
                        assert len(locks) < 2000
                        locks.append({'at_monotonic': time.monotonic(), 'request_id': active, 'rows': rows})
                        previous = signature
                    stopped.wait(.25)
        except Exception as error:
            observer_errors.append({'monitor_error': type(error).__name__})

    previous_trace = threading.gettrace()
    if api_trace:
        threading.settrace(observe)
    monitor_thread = threading.Thread(target=monitor, daemon=True)
    @contextmanager
    def monitored():
        monitor_thread.start()
        try:
            yield
        finally:
            stopped.set()
            monitor_thread.join(5)
            assert not monitor_thread.is_alive()
    pack, factory = reference.unpaused_consumer(c, tmp_path)
    selected = None
    getresponse = http.client.HTTPConnection.getresponse
    def observed_response(connection):
        response = getresponse(connection)
        if active is not None:
            requests[active].update(HTTP_status=response.status,
                cache_control=response.getheader('Cache-Control'))
        return response
    monkeypatch.setattr(http.client.HTTPConnection, 'getresponse', observed_response)
    try:
        with reference.served(c.prefix_runtime, c.config.certificate) as (send, replies), monitored():
            def request(view, selector=None):
                nonlocal active
                assert active is None
                item = {'request_id': len(requests), 'view': view,
                    'started_monotonic': time.monotonic()}
                requests.append(item)
                active = item['request_id']
                try:
                    endpoint = path if view == 'progress' else path + '/cancel' if view == 'cancel' else (
                        path + '/prefix' + ('' if view == 'summary' else '/' + view + '?' + urlencode(selector)))
                    status, raw = send('POST' if view == 'cancel' else 'GET', endpoint)
                    value = json.loads(raw)
                    item.update(status=status, seconds=time.monotonic()-item['started_monotonic'],
                        wire_sha256=sha256(raw).hexdigest(), wire_utf8=raw.decode())
                    assert status in (200, 409, 422, 503)
                    if status == 200 and selector is not None:
                        assert value['reference']['selector'] == selector
                    return status, value
                finally:
                    active = None

            status, raw = send('POST', reference.POST, c.raw)
            assert status == 202
            job = json.loads(raw)['job_id']
            path = '/v1/jobs/' + job + '/crop-climate-joint-execution'
            with reference.consumer.legacy.process_consumer(tmp_path, 'joint_operator:build') as (process, events, errors):
                deadline = time.monotonic()+240
                with monkeypatch.context() as patch:
                    calls = reference.progress.forbid(patch)
                    while time.monotonic() < deadline and process.poll() is None:
                        status, progress = request('progress')
                        if status == 200 and progress['job']['state'] not in ('queued', 'simulating'):
                            break
                        status, summary = request('summary')
                        if status == 200 and summary['prefix_status'] == 'closed':
                            break
                        if status == 200 and summary['prefix_status'] == 'accepted':
                            selector = summary['reference']['selector']
                            event_status, _ = request('events', selector)
                            sample_status, _ = request('samples', selector) if event_status == 200 else (None, None)
                            if event_status == sample_status == 200:
                                selected = selector
                                break
                        time.sleep(10)
                    assert not any(calls.values())
                cancel_status, cancellation = request('cancel')
                def terminal_attempt():
                    return any(json.loads(file.read_bytes())['state'] in ('canceled', 'succeeded', 'hold', 'failed')
                        for file in tmp_path.glob('attempt-*.private.json'))
                reference.consumer.legacy.wait_for(terminal_attempt, process, timeout=90)
            assert process.returncode == 0 and errors == ['']
            attempts = reference.proofs(tmp_path)
            final = c.worker.jobs.get_job('tenant-1', job)
            assert final['state'] in ('canceled', 'succeeded', 'hold', 'failed')
            busy = []
            for file in sorted(tmp_path.glob('close-*.private.json')):
                detail = json.loads(file.read_bytes())
                busy.append({'kind': detail['kind'], 'reason': detail['reason'],
                    'observed_mtime_seconds': file.stat().st_mtime,
                    'exception_types': re.findall(r'^([A-Za-z_][A-Za-z_0-9.]*):', detail['traceback'], re.M)})
            accepted = cancel_status == 200 and cancellation['cancel_accepted']
            if accepted:
                assert final['state'] == 'canceled'
                reference.consumer.reference.no_published_result(c.worker, job)
            if final['state'] == 'failed':
                assert len(attempts) == len(busy) == 3
                assert all(row['reason'] == 'joint_execution_busy' for row in busy)
                assert final['reason']['code'] == 'attempts_exhausted'
                reference.consumer.reference.no_published_result(c.worker, job)
            with monkeypatch.context() as patch:
                calls = reference.progress.forbid(patch)
                status, raw = send('GET', path+'/prefix')
                closed = json.loads(raw)
                assert status == 200 and closed['prefix_status'] == 'closed'
                assert closed['reference'] is None and closed['page'] is None and not any(calls.values())
        reference.save('cancel-request-diagnosis-'+('traced' if api_trace else 'untraced'), {'actual_SCRAM': True, 'verified_TLS': True,
            'API_tracing_perturbs_timing': api_trace, 'worker_traced': False, 'worker_pause_or_delay': False,
            'browser_run': False, 'P6a_accepted': False, 'same_public_events_samples_before_cancel': selected is not None,
            'cancel_HTTP_status': cancel_status, 'cancel_accepted': accepted, 'final_job_state': final['state'],
            'requests': requests, 'API_trace': trace, 'PG_lock_transitions': locks,
            'observer_errors': observer_errors, 'attempts': attempts, 'worker_exit': process.returncode,
            'worker_busy_outcomes': busy, 'read_calls': calls,
            'reference_sha256': sha256(Path(__file__).read_bytes()).hexdigest()})
        assert requests and any(item['view'] == 'cancel' for item in requests)
        if api_trace:
            assert any(item['request_id'] == requests[-1]['request_id'] for item in trace)
        else:
            assert not trace
        assert not observer_errors
    finally:
        stopped.set()
        if monitor_thread.ident is not None:
            monitor_thread.join(5)
        assert not monitor_thread.is_alive()
        threading.settrace(previous_trace)
        reference.save('cancel-request-partial-'+('traced' if api_trace else 'untraced'), {'requests': requests, 'API_trace': trace,
            'PG_lock_transitions': locks, 'observer_errors': observer_errors,
            'monitor_read_only': True, 'monitor_connection': 'owned_setup_admin_socket',
            'worker_traced': False, 'worker_pause_or_delay': False,
            'reference_sha256': sha256(Path(__file__).read_bytes()).hexdigest()})
        pack.unlink()
        (tmp_path/'proof.private.json').unlink()
