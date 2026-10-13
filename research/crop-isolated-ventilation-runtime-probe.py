"""Exercise an isolated model API/consumer inside the namespace probe lifetime."""
from dataclasses import asdict
from hashlib import sha256
from pathlib import Path
import json
import os
import shutil
import signal
import socket
import ssl
import subprocess
import sys
import time
import urllib.error
import urllib.request
from copy import deepcopy
from urllib.parse import urlencode
from uuid import uuid4


def audited_runtime(config_path, *, bounded_preview=False):
    """Audit actual HTTP query calls in this synthetic probe's API process."""
    from app.crop_greenhouse_ventilation_operator_config import load_ventilation_api_runtime
    from pytest import MonkeyPatch
    from crop_ventilation_query_audit import install, query_calls
    directory = config_path.parent
    runtime = load_ventilation_api_runtime(directory/'api.private.json')
    if bounded_preview:
        from contextlib import asynccontextmanager
        from anyio.to_thread import current_default_thread_limiter
        app = runtime.service.app.app
        previous_lifespan = app.router.lifespan_context
        @asynccontextmanager
        async def lifespan(application):
            async with previous_lifespan(application):
                limiter = current_default_thread_limiter()
                limiter.total_tokens = 1
                with (directory/'capacity.private.json').open('x') as stream:
                    os.fchmod(stream.fileno(), 0o400)
                    json.dump({'synchronous_API_thread_tokens': limiter.total_tokens,
                               'calculation_consumer_separate_process': True}, stream)
                yield
        app.router.lifespan_context = lifespan
    audit_patch = MonkeyPatch()
    install(audit_patch)
    for kind, query in (('progress', runtime.ventilation_execution_query),
                        ('result', runtime.ventilation_crop_query),
                        ('prefix', runtime.ventilation_prefix_query)):
        original = query.read
        def read(*args, _original=original, _kind=kind, _patch=audit_patch, **kwargs):
            with query_calls() as calls:
                try:
                    return _original(*args, **kwargs)
                finally:
                    with (directory/'query-audit.private.jsonl').open('a') as stream:
                        os.fchmod(stream.fileno(), 0o600)
                        stream.write(json.dumps({'kind': _kind, 'calls': calls}, sort_keys=True)+'\n')
                        stream.flush(); os.fsync(stream.fileno())
        query.read = read
    return runtime


def serve_api():
    audited_runtime(Path(os.environ['OSSF_API_CONFIG'])).service.serve()


def calculations(directory, operator, requests, send, children, save, modes):
    from psycopg import sql
    from pytest import MonkeyPatch
    from test_crop_greenhouse_ventilation_execution_query import forbid
    from app.crop_greenhouse_ventilation_execution_query import VentilationExecutionQuery
    from app.crop_greenhouse_ventilation_current_query import VentilationCurrentQuery
    from app.crop_greenhouse_ventilation_result_schema import TABLE
    worker = operator.worker().worker
    progress = VentilationExecutionQuery(worker.checkpoints, worker.results)
    current = VentilationCurrentQuery(worker.results)
    with worker.jobs.connect() as conn:
        assert conn.pgconn.used_password and conn.info.get_parameters()['require_auth'] == 'scram-sha-256'
    def state(job):
        with worker.jobs.connect() as conn:
            conn.execute('SET TRANSACTION READ ONLY')
            return conn.execute(sql.SQL('SELECT state,attempt_count,cancel_requested,lease_until FROM {} '
                'WHERE tenant_id=%s AND job_id=%s').format(worker.jobs._table('jobs')), ('tenant-1', job)).fetchone()
    def wait(job, states):
        deadline = time.monotonic()+240
        while True:
            assert all(child.poll() is None for child in children), 'isolated runtime process exited'
            row = state(job)
            if row['state'] in states: return row
            assert row['state'] not in {'succeeded', 'hold', 'failed', 'canceled'}, 'unexpected terminal state'
            assert time.monotonic() < deadline, 'isolated calculation deadline expired'
            time.sleep(.25)
    cases = {}
    for mode in modes:
        body = json.loads((requests/(mode+'.json')).read_bytes())
        body.update(study_id='isolated-ventilation-'+uuid4().hex, revision=mode+'-v1')
        save(directory/(mode+'.request.private.json'), body)
        status, raw = send('POST', '/v1/crop-greenhouse-ventilation-executions', body)
        assert status == 202, 'isolated HTTP admission rejected'
        job = json.loads(raw)['job_id']
        path = '/v1/jobs/'+job+'/crop-greenhouse-ventilation-execution'
        running = wait(job, {'simulating'})
        assert running['attempt_count'] == 1 and running['lease_until'] is not None
        if mode == 'cancel':
            status, raw = send('POST', path+'/cancel')
            assert status == 200 and json.loads(raw)['cancel_accepted'] is True
            expected_state = 'canceled'
        else:
            expected_state = 'succeeded' if mode == 'completed' else 'hold'
        terminal = wait(job, {expected_state})
        assert terminal['attempt_count'] == 1 and terminal['lease_until'] is None
        status, raw = send('GET', path)
        assert status == 200
        wire = json.loads(raw)
        with MonkeyPatch.context() as patch:
            calls = forbid(patch)
            expected = json.loads(progress.read('tenant-1', job))
            for value in (wire, expected):
                assert value.pop('observed_at').endswith('Z')
            assert wire == expected and wire['G0_G4'] == 'not_assessed'
            if mode == 'cancel':
                assert wire['result'] is None
                with worker.jobs.connect() as conn:
                    count = conn.execute(sql.SQL('SELECT count(*) AS n FROM {} WHERE study_id=%s AND revision=%s').format(
                        sql.Identifier(worker.jobs.schema, TABLE)), (body['study_id'], body['revision'])).fetchone()['n']
                assert count == 0
                sample_count = event_count = 0
            else:
                selected = wire['result']
                assert selected['status'] == mode
                for view in ('summary', 'samples', 'events'):
                    query = {**body['farm'], 'view': view}
                    options = {} if view == 'summary' else {'offset': 0, 'limit': 64 if view == 'samples' else 8}
                    reference = current.read('tenant-1', selected['result_id'], body['farm'], view=view, **options)
                    status, raw = send('GET', '/v1/crop-greenhouse-ventilation-research-results/'+
                        selected['result_id']+'?'+urlencode({**query, **options}))
                    assert status == 200 and raw == reference, 'stored result differs from actual HTTP bytes'
                    if view == 'samples':
                        samples = json.loads(raw)['page']['records']
                        assert all(sample['time']['at'].endswith('Z') for sample in samples)
                        sample_count = len(samples)
                    if view == 'events': event_count = len(json.loads(raw)['page']['records'])
            assert not any(calls.values())
        cases[mode] = {'state': terminal['state'], 'attempt_count': terminal['attempt_count'],
            'running_lease_observed': True, 'actual_HTTP_original_storage_equal': True,
            'samples': sample_count, 'events': event_count, 'read_calculation_and_write_calls': calls,
            'job_id': job, 'result': wire['result'], 'farm': body['farm']}
        save(directory/(mode+'.terminal.private.json'), {'progress': wire, 'case': cases[mode]})
    return cases


def check_rights(directory, operator, cases, send, save):
    from psycopg import sql
    from app.crop_climate_joint_result_schema import TABLE as JOINT_TABLE
    worker = operator.worker().worker
    def snapshot():
        with worker.jobs.connect() as conn:
            conn.execute('SET TRANSACTION ISOLATION LEVEL REPEATABLE READ READ ONLY')
            tables = [row['tablename'] for row in conn.execute(
                'SELECT tablename FROM pg_tables WHERE schemaname=%s ORDER BY tablename', (worker.jobs.schema,))
                if row['tablename'] != JOINT_TABLE]
            return {name: sorted(sha256(json.dumps(row, sort_keys=True, default=str).encode()).hexdigest()
                for row in conn.execute(sql.SQL('SELECT * FROM {}').format(sql.Identifier(worker.jobs.schema, name))))
                for name in tables}
    before = snapshot()
    mode = next(iter(cases))
    case = cases[mode]
    body = json.loads((directory/(mode+'.request.private.json')).read_bytes())
    value, _, _ = operator.load()
    rights = Path(value['ventilation']['rights_file'])
    original = rights.read_bytes()
    changed = json.loads(original)
    changed[body['input']['source_sha256']] = False
    progress_path = '/v1/jobs/'+case['job_id']+'/crop-greenhouse-ventilation-execution'
    result_path = None if case['result'] is None else '/v1/crop-greenhouse-ventilation-research-results/'+\
        case['result']['result_id']+'?'+urlencode(body['farm'])
    denied = []
    try:
        save(rights, changed)
        denied.append(send('GET', progress_path)[0])
        if result_path: denied.append(send('GET', result_path)[0])
        request = deepcopy(body)
        request['revision'] = 'revoked-'+uuid4().hex
        denied.append(send('POST', '/v1/crop-greenhouse-ventilation-executions', request)[0])
        assert all(status == 422 for status in denied), 'current revoked rights were not held'
    finally: save(rights, original, raw=True)
    assert rights.read_bytes() == original
    assert send('GET', progress_path)[0] == 200
    if result_path: assert send('GET', result_path)[0] == 200
    assert snapshot() == before
    record = {'current_rights_revocation_statuses': denied, 'rights_restored_and_reread': True,
        'owned_rights_copy_only_modified': True, 'readable_table_count': len(before),
        'all_readable_rows_unchanged_during_rights_checks': True, 'stored_result_revocation_checked': result_path is not None}
    save(directory/'rights-check.private.json', record)
    return record


def exercise(out, policy, dsn, original, config, requests, original_directory, original_access,
             modes=('cancel', 'completed', 'hold'), check_runtime_rights=False, browser_config=None):
    import importlib.util
    root = Path(__file__).resolve().parents[1]
    spec = importlib.util.spec_from_file_location('isolated_preview_lifecycle',
        root/'research/crop-joint-ventilation-live-preview.py')
    lifecycle = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(lifecycle)
    save = lifecycle.save
    from app.http_identity import token_digest
    token = json.loads(original_access.read_bytes())['token']
    assert token_digest(token.encode()) == original['token_digest']
    directory = out/'runtime'
    directory.mkdir(mode=0o700)
    for name, source in (('isolated_ventilation_support.py', 'crop-joint-ventilation-live-operator.py'),
                         ('isolated_ventilation_operator.py', 'crop-isolated-ventilation-operator.py')):
        save(directory/name, (root/'research'/source).read_bytes(), raw=True)
    artifacts = directory/'artifacts'
    shutil.copytree(original['artifacts'], artifacts)
    legacy, custody = directory/'legacy', directory/'custody'
    legacy.mkdir(mode=0o700); custody.mkdir(mode=0o700)
    owned_sources = {}
    for name in ('rights_file', 'reviews_file'):
        path = directory/(name+'.private.json')
        save(path, Path(config['ventilation'][name]).read_bytes(), raw=True)
        owned_sources[name] = str(path)
    # The local credential copy is removed before the outer namespace is dropped.
    passfile = directory/'authority.pgpass'
    from psycopg.conninfo import conninfo_to_dict, make_conninfo
    authority_dsn = make_conninfo(**{**conninfo_to_dict(dsn), 'passfile': str(passfile),
                                   'options': '-c max_parallel_workers_per_gather=0'})
    value = {**config, 'runtime_version': 'owned-isolated-ventilation-runtime-v1',
        'original_operator': str(original_directory/'joint_prefix_live_operator_v1.py'),
        'original_operator_sha256': sha256((original_directory/'joint_prefix_live_operator_v1.py').read_bytes()).hexdigest(),
        'original_runtime_sha256': sha256((original_directory/'runtime.private.json').read_bytes()).hexdigest(),
        'auth': {name: original[name] for name in ('token_digest', 'issued_at', 'expires_at')},
        'policy': asdict(policy), 'dsn': authority_dsn, 'artifacts': str(artifacts), 'legacy': str(legacy),
        'ventilation': {**config['ventilation'], **owned_sources, 'custody': str(custody)}}
    save(directory/'runtime.private.json', value)
    sys.path.insert(0, str(directory))
    import isolated_ventilation_operator
    checked, _, _ = isolated_ventilation_operator.load()
    assert checked == value
    faults = {
        'old_namespace': {'policy': {**value['policy'], 'schema': original['policy']['schema']}},
        'joint_model_enabled': {'policy': {**value['policy'], 'crop_climate_joint_result_storage': True}},
        'original_artifacts': {'artifacts': original['artifacts']},
        'original_DSN': {'dsn': original['dsn']},
        'stale_original_digest': {'original_runtime_sha256': '0'*64},
        'foreign_auth': {'auth': {**value['auth'], 'token_digest': '0'*64}},
        'chunk_budget': {'worker_chunk_budget': 16},
        'unknown_field': {'extra': True},
    }
    try:
        for fault, changed in faults.items():
            save(directory/'runtime.private.json', {**value, **changed})
            try: isolated_ventilation_operator.load()
            except ValueError: continue
            raise AssertionError('isolated configuration accepted '+fault)
    finally: save(directory/'runtime.private.json', value)
    cert, key = lifecycle.common.certificate(directory, 3600)
    with socket.socket() as probe:
        probe.bind(('127.0.0.1', 0)); port = probe.getsockname()[1]
    from app import crop_greenhouse_ventilation_operator_config as loader
    api = {'config_version': loader.PREFIX_VERSION, 'policy': asdict(policy),
        'artifact_root': str(artifacts), 'certificate': str(cert), 'private_key': str(key),
        'authored_run_gate_key_file': None, 'content_access': None, 'host': '127.0.0.1', 'port': port,
        'dependencies_factory': 'isolated_ventilation_operator:dependencies',
        'crop_greenhouse_ventilation_execution': True, 'crop_greenhouse_ventilation_prefix': True}
    for field, raw in (('dsn_file', authority_dsn.encode()),
                       ('thermal_gate_key_file', bytes.fromhex(original['thermal_key'])),
                       ('market_hold_key_file', bytes.fromhex(original['market_key']))):
        path = directory/field
        save(path, raw, raw=True); api[field] = str(path)
    save(directory/'api.private.json', api)
    env = {**os.environ, 'OSSF_API_CONFIG': str(directory/'api.private.json'),
        'PYTHONPATH': os.pathsep.join(map(str, (directory, root/'backend', root/'backend/tests', original_directory)))}
    logs, children = [], []
    server = thread = None
    checks = {}
    try:
        shutil.copyfile(out/'authority.pgpass', passfile)
        passfile.chmod(0o600)
        commands = (('api', [sys.executable, '-B', str(Path(__file__).resolve()), 'api']),
                ('worker', [sys.executable, '-B', '-m', 'app.deterministic_work',
                            '--factory', 'isolated_ventilation_operator:worker']))
        if browser_config:
            import threading
            server = audited_runtime(directory/'api.private.json', bounded_preview=True).service.server()
            thread = threading.Thread(target=server.run, daemon=True)
            thread.start()
            commands = commands[1:]
        for name, argv in commands:
            log = (directory/(name+'.private.log')).open('xb')
            os.fchmod(log.fileno(), 0o600); logs.append(log)
            children.append(subprocess.Popen(argv, env=env, stdin=subprocess.DEVNULL,
                stdout=log, stderr=subprocess.STDOUT))
        context = ssl.create_default_context(cafile=str(cert))
        readiness_path = '/v1/jobs/'+str(uuid4())+'/crop-greenhouse-ventilation-execution' if browser_config else '/openapi.json'
        readiness_status = 404 if browser_config else 200
        deadline = time.monotonic()+30
        while True:
            assert all(child.poll() is None for child in children), 'isolated runtime process exited'
            assert thread is None or thread.is_alive(), 'isolated API owner thread exited'
            try:
                request = urllib.request.Request(f'https://localhost:{port}'+readiness_path,
                    headers={'Authorization': 'Bearer '+token})
                try: response = urllib.request.urlopen(request, context=context, timeout=3)
                except urllib.error.HTTPError as error: response = error
                with response:
                    assert response.status == readiness_status
                    assert response.headers['Cache-Control'] == 'no-store'
                    response.read()
                break
            except (urllib.error.URLError, TimeoutError):
                assert time.monotonic() < deadline, 'isolated runtime readiness expired'
                time.sleep(.1)
        deadline = time.monotonic()+30
        while True:
            first = (directory/'worker.private.log').read_text().splitlines()
            if first: break
            assert all(child.poll() is None for child in children)
            assert time.monotonic() < deadline, 'isolated consumer readiness expired'
            time.sleep(.1)
        assert first and json.loads(first[0]) == {'version': 1, 'event': 'started'}
        replies = []
        def send(method, path, body=None, *, authenticated=True):
            headers = {'Authorization': 'Bearer '+token} if authenticated else {}
            if body is not None: headers['Content-Type'] = 'application/json'
            request = urllib.request.Request(f'https://localhost:{port}'+path,
                data=None if body is None else json.dumps(body).encode(), headers=headers, method=method)
            try: response = urllib.request.urlopen(request, context=context, timeout=60)
            except urllib.error.HTTPError as exc: response = exc
            with response:
                raw = response.read()
                assert response.headers['Cache-Control'] == 'no-store'
                record = {'method': method, 'status': response.status, 'sha256': sha256(raw).hexdigest()}
                save(directory/('HTTP-'+str(len(replies)+1)+'.private.json'), {'path': path, **record, 'body': raw.decode()})
                replies.append(record)
                return response.status, raw
        assert send('GET', '/openapi.json', authenticated=False)[0] == 401
        if browser_config:
            module = lifecycle.module('isolated_browser_probe', root/'research/crop-isolated-ventilation-browser-probe.py')
            cases = module.exercise(directory, isolated_ventilation_operator, requests, children,
                                    save, modes, browser_config, port, cert, original_access, lifecycle)
        else:
            cases = calculations(directory, isolated_ventilation_operator, requests, send, children, save, modes)
        rights_checks = check_rights(directory, isolated_ventilation_operator, cases, send, save) if check_runtime_rights else {}
        checks = {'actual_TLS_API_started': True, 'independent_unpaused_consumer_started': True,
            'separate_artifact_and_empty_initial_custody_roots': True, 'worker_chunk_budget': 8,
            'original_joint_API_consumer_unchanged': True, 'isolated_joint_factory_enabled': False,
            'API_in_namespace_owner_process': browser_config is not None,
            'API_and_consumer_distinct_processes': True,
            'rejected_configuration_cases': sorted(faults),
            'case_outcomes': {mode: {k: v for k, v in case.items() if k not in ('job_id', 'result', 'farm')}
                for mode, case in cases.items()}, 'HTTP_replies': replies, **rights_checks}
    finally:
        stopped = [lifecycle.stop_owned_process(child, timeout=15) for child in reversed(children)]
        if server is not None:
            server.should_exit = True
            thread.join(15)
            assert not thread.is_alive(), 'isolated API thread did not stop'
        for log in logs: log.close()
        passfile.unlink()
        save(directory/'stopped.private.json', {'children': stopped, 'remaining_children':
            sum(child.poll() is None for child in children), 'passfile_remaining': passfile.exists()})
    # Uvicorn restores and reraises SIGTERM after its graceful shutdown.
    assert not any(item['forced'] for item in stopped)
    assert [item['exit'] for item in stopped] == ([0] if browser_config else [0, -signal.SIGTERM])
    events = [json.loads(line) for line in (directory/'worker.private.log').read_text().splitlines()]
    attempts = [event for event in events if event.get('event') == 'attempt']
    assert events[0]['event'] == 'started' and events[-1]['event'] == 'stopped'
    assert len(attempts) == len(cases) and {event['job_id'] for event in attempts} == {case['job_id'] for case in cases.values()}
    assert all(event['attempt'] == 1 for event in attempts)
    audit = [json.loads(line) for line in (directory/'query-audit.private.jsonl').read_text().splitlines()]
    assert audit and all(not any(item['calls'].values()) for item in audit)
    checks['actual_HTTP_query_audit_count'] = len(audit)
    checks['actual_HTTP_query_calculation_and_write_calls'] = 0
    checks['worker_attempt_events_match_fresh_requests_only'] = True
    checks['actual_API_worker_exit_codes'] = [item['exit'] for item in stopped]
    save(directory/'acceptance.private.json', checks)
    return checks


if __name__ == '__main__':
    assert sys.argv[1:] == ['api']
    serve_api()
