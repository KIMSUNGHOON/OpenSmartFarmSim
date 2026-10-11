"""Request-aligned actual prefix diagnostics; no product or worker changes."""
from copy import deepcopy
from hashlib import sha256
import importlib.util
import json
from pathlib import Path
import sys
import threading
import time
from urllib.parse import urlencode

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'backend/tests'))
import test_crop_climate_joint_prefix_runtime as reference
from app import crop_climate_joint_prefix as prefix
from app import api_crop_climate_joint_prefix_routes as routes

spec = importlib.util.spec_from_file_location('lease_guard_reference',
    ROOT / 'research/crop-climate-joint-prefix-lease-guard-reference.py')
lease_reference = importlib.util.module_from_spec(spec)
spec.loader.exec_module(lease_reference)
login_database = lease_reference.login_database
pytest_plugins = ['test_crop_climate_joint_prefix_runtime']


@reference.LOGIN
def test_actual_request_aligned_progress(prefix_native, tmp_path, monkeypatch):
    c = prefix_native
    requests = []
    active = None
    frames = {}
    previous_bundles = {}
    previous_heads = {}
    modules = {str(Path(module.__file__)): name for name, module in (
        ('prefix', prefix), ('query', prefix.execution), ('routes', routes),
        ('custody', prefix.custody), ('storage', prefix.storage))}
    names = {'read', '_bundle', '_head', '_selected', '_ancestry', '_accepted', '_chosen',
        '_same_bundle', '_unchanged', '_current_after_projection'}

    def append(request_id, value):
        entries = requests[request_id]['trace']
        assert len(entries) < 3000
        entries.append({**value, 'at_monotonic': time.monotonic(),
            'thread_id': threading.get_ident()})

    def differences(before, after):
        if before is None or after is None:
            return {'presence_changed': before is not after}
        row, other = before[0], after[0]
        return {'job_fields': sorted(k for k in row.keys() | other.keys()
                if k not in row or k not in other or not prefix.execution._same(row[k], other[k])),
            'bundle_components': [name for i, name in enumerate(
                ('latest', 'links', 'publications', 'outcomes', 'terminal'), 1)
                if not prefix.execution._same(before[i], after[i])]}

    def observe(frame, event, arg):
        module = modules.get(frame.f_code.co_filename)
        name = frame.f_code.co_name
        if module is None or name not in names:
            return None
        frame.f_trace_lines = False
        key = id(frame)
        if event == 'call':
            if active is None:
                return None
            frames[key] = (active, time.monotonic())
        context = frames.get(key)
        if context is None:
            return None
        request_id, started = context
        common = {'module': module, 'function': name, 'line': frame.f_lineno}
        if event == 'exception':
            kind = arg[0]
            if kind.__name__ not in ('GeneratorExit', 'StopIteration', 'StopAsyncIteration'):
                append(request_id, {**common, 'event': 'exception', 'exception': kind.__name__})
        elif event == 'return':
            entry = {**common, 'event': 'return', 'seconds': time.monotonic() - started}
            if module == 'query' and name == '_bundle' and arg is not None:
                row, latest = arg[:2]
                entry.update(state=row['state'], attempt=row['attempt_count'],
                    cancel_requested=row['cancel_requested'],
                    latest_selector=None if latest is None else {k: latest['reason'][k]
                        for k in ('publication_sequence', 'head_sha256', 'proof_sha256')},
                    difference_from_previous_bundle=differences(previous_bundles.get(request_id), arg))
                previous_bundles[request_id] = deepcopy(arg)
            elif module == 'storage' and name == '_head' and arg is not None:
                head, digest = arg
                entry.update(head_sha256=digest, commit_count=head['commit_count'],
                    terminal_artifact=head['artifact_sha256'] is not None,
                    changed_from_previous_head=request_id in previous_heads and previous_heads[request_id] != digest)
                previous_heads[request_id] = digest
            elif module == 'custody' and name == '_selected' and arg is not None:
                proof, digest = arg
                entry.update(custody_sequence=proof['sequence'],
                    proof_sha256=digest, head_sha256=prefix.custody._head(proof['head']))
            elif module == 'prefix' and name == '_same_bundle':
                entry.update(same_bundle=arg, difference=differences(
                    frame.f_locals['before'], frame.f_locals['after']))
            elif module == 'prefix' and name == '_unchanged':
                entry['unchanged'] = arg
            elif module == 'prefix' and name == '_chosen' and arg is not None:
                entry.update(selected_selector={k: arg['reason'][k]
                        for k in ('publication_sequence', 'head_sha256', 'proof_sha256')},
                    checkpoint_recorded_at=arg['recorded_at'].isoformat(),
                    checkpoint_attempt=arg['attempt'])
            elif module == 'prefix' and name == '_ancestry':
                entry['selected_selector'] = {k: frame.f_locals['selected'][k]
                    for k in ('publication_sequence', 'head_sha256', 'proof_sha256')}
            append(request_id, entry)
            frames.pop(key, None)
        return observe

    previous_trace = threading.gettrace()
    threading.settrace(observe)
    pack, factory = reference.unpaused_consumer(c, tmp_path)
    try:
        with reference.served(c.prefix_runtime, c.config.certificate) as (send, replies):
            status, raw = send('POST', reference.POST, c.raw)
            assert status == 202
            job = json.loads(raw)['job_id']
            path = '/v1/jobs/' + job + '/crop-climate-joint-execution'

            def request(view, selector=None, selector_origin=None):
                nonlocal active
                assert active is None
                request_id = len(requests)
                item = {'request_id': request_id, 'view': view, 'selector': selector,
                    'selector_origin': selector_origin,
                    'started_monotonic': time.monotonic(), 'trace': []}
                requests.append(item)
                active = request_id
                try:
                    endpoint = path + '/prefix' + ('' if view == 'summary' else '/' + view + '?' + urlencode(selector))
                    status, raw = send('GET', endpoint)
                    item.update(status=status, wire_utf8=raw.decode(), wire_sha256=sha256(raw).hexdigest(),
                        seconds=time.monotonic() - item['started_monotonic'])
                    assert status in (200, 409, 422, 503)
                    value = json.loads(raw)
                    if status == 200 and selector is not None:
                        assert value['reference']['selector'] == selector
                    return status, value
                finally:
                    active = None

            with reference.consumer.legacy.process_consumer(tmp_path, 'joint_operator:build') as (process, events, errors):
                deadline = time.monotonic() + 180
                with monkeypatch.context() as patch:
                    calls = reference.progress.forbid(patch)
                    while True:
                        assert time.monotonic() < deadline and process.poll() is None and len(requests) < 80
                        status, value = request('summary')
                        if status == 200 and value['prefix_status'] == 'closed':
                            break
                        if status == 200 and value['prefix_status'] == 'accepted':
                            selector = value['reference']['selector']
                            origin = 'public_accepted_summary'
                        else:
                            selectors = [entry['latest_selector'] for entry in requests[-1]['trace']
                                if entry.get('latest_selector') is not None]
                            selector = selectors[-1] if selectors else None
                            origin = 'actual_readonly_DB_history_diagnostic_only'
                        if selector is not None:
                            request('events', selector, origin)
                            request('samples', selector, origin)
                    assert not any(calls.values())
                reference.consumer.legacy.wait_for(lambda: bool(list(tmp_path.glob('attempt-*.private.json'))), process, timeout=30)
            assert process.returncode == 0 and errors == ['']
            attempts = reference.proofs(tmp_path)
            assert attempts[-1]['state'] == 'succeeded'
            with monkeypatch.context() as patch:
                calls = reference.progress.forbid(patch)
                status, raw = send('GET', path)
                assert status == 200
                outcome = json.loads(raw)
                selected = outcome['result']
                assert selected['status'] == 'completed'
                farm = json.loads(c.raw)['farm']
                expected = reference.current.JointCropClimateCurrentQuery(c.worker.results).read(
                    'tenant-1', selected['result_id'], farm, view='summary')
                status, terminal = send('GET', '/v1/crop-climate-joint-research-results/' + selected['result_id'] + '?' + urlencode(farm))
                assert status == 200 and terminal == expected and not any(calls.values())
            assert events[-1]['event'] == 'stopped'
        assert requests and all(item['trace'] for item in requests)
        reference.save('request-aligned-progress', {'reader_version': prefix.VERSION,
            'actual_SCRAM': True, 'verified_TLS': True, 'API_mocking': False,
            'worker_pause_or_delay': False, 'worker_traced': False, 'worker_chunk_budget': 8,
            'API_thread_only_tracing': True, 'requests': requests, 'read_calls': calls,
            'worker_exit': process.returncode, 'attempts': attempts, 'events': events,
            'terminal_summary_original_wire': terminal.decode(),
            'terminal_summary_sha256': sha256(terminal).hexdigest(),
            'terminal_matches_independent_current_query': True,
            'reference_sha256': sha256(Path(__file__).read_bytes()).hexdigest(),
            'replies': replies})
    finally:
        threading.settrace(previous_trace)
        pack.unlink()
        (tmp_path / 'proof.private.json').unlink()
