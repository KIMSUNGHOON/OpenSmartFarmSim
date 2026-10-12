"""Exercise overlapping real validation paths under the unchanged SCRAM limit."""
from concurrent.futures import ThreadPoolExecutor
from concurrent.futures import TimeoutError as FutureTimeout
from contextlib import ExitStack, contextmanager
from dataclasses import replace
import importlib.util
import json
import os
from pathlib import Path
from threading import Barrier, Lock, Event
from types import SimpleNamespace
import time

import psycopg
import pytest

from app.crop_greenhouse_ventilation_execution_query import VentilationExecutionQuery, VentilationExecutionQueryPending
from test_crop_greenhouse_ventilation_result_store import (
    authoring, farm_setup, profiles, login_database, original_login_scope, login_scope)
from test_api_crop_greenhouse_ventilation_replay import database_cleanup
from test_crop_joint_ventilation_runtime import native_pair, mixed_config, tls_files, private_config
from test_crop_greenhouse_ventilation_execution_runtime import served, ventilation_factory
import test_joint_deterministic_work as consumer
from test_crop_joint_ventilation_live_preview import preview
import test_crop_climate_joint_execution_worker as joint
import test_crop_greenhouse_ventilation_execution_worker as ventilation
from test_crop_greenhouse_ventilation_execution_worker import setup as worker_setup, producer_setup

spec = importlib.util.spec_from_file_location('owned_mixed_operator',
    Path(__file__).resolve().parents[2]/'research/crop-joint-ventilation-live-operator.py')
operator = importlib.util.module_from_spec(spec)
spec.loader.exec_module(operator)


@contextmanager
def capacity_consumer(directory):
    with consumer.legacy.process_consumer(directory, 'joint_operator:build') as running:
        try: yield running
        finally: preview.stop_owned_process(running[0], timeout=60)


@ventilation.pytestmark
def test_two_models_and_progress_overlap_within_connection_limit(
        authoring, profiles, database_cleanup, tmp_path, monkeypatch, request):
    seeds = []
    for index, reference in enumerate((joint, ventilation)):
        directory = tmp_path/str(index); directory.mkdir(mode=0o700)
        producer = reference.producer.setup.__wrapped__(authoring, directory, profiles, request, monkeypatch)
        worker, job_id, raw, value = reference.setup.__wrapped__(producer)
        lease = worker.jobs.claim(600, tenant_id='tenant-1', allowed_stages=('simulation',), job_id=job_id)
        assert lease
        seeds.append((worker, job_id, raw, lease))
    jobs = seeds[0][0].jobs
    assert seeds[1][0].jobs is jobs and jobs.runtime_identity[0].connection_limit == 8
    query = VentilationExecutionQuery(seeds[1][0].checkpoints, seeds[1][0].results)
    operator.bind_registration_budget(seeds[0][0].server.binding.farms, tmp_path/'registration-budget.lock')
    original, connections, errors, pending = psycopg.connect, [], [], []
    mutex, barrier, peak = Lock(), Barrier(3), 0
    def measured(*args, **kwargs):
        nonlocal peak
        try: conn = original(*args, **kwargs)
        except psycopg.OperationalError as error:
            errors.append({'connection_limit': 'too many connections for role' in str(error)})
            raise
        if conn.info.user == jobs.runtime_identity[0].roles['authority']:
            with mutex:
                connections.append(conn)
                peak = max(peak, sum(not c.closed for c in connections))
            # A little I/O latency keeps the real nested source reads overlapping.
            time.sleep(.005)
        return conn
    monkeypatch.setattr(psycopg, 'connect', measured)
    def run(index):
        barrier.wait(timeout=10)
        if index < 2:
            worker, _, raw, lease = seeds[index]
            assert worker._before(lease) == raw
        else:
            try:
                assert json.loads(query.read('tenant-1', seeds[1][1]))['job']['state'] == 'simulating'
            except VentilationExecutionQueryPending:
                pending.append('concurrent_lease_renewal')
    with ThreadPoolExecutor(max_workers=3) as pool:
        futures = [pool.submit(run, i) for i in range(3)]
        failures = [type(f.exception()).__name__ for f in futures if f.exception() is not None]
    assert json.loads(query.read('tenant-1', seeds[1][1]))['job']['state'] == 'simulating'
    report = {'peak':peak, 'connection_limit':8, 'errors':errors, 'failures':failures,
              'pending':pending, 'remaining':sum(not c.closed for c in connections), 'G0_G4':'not_assessed'}
    root = os.environ.get('OSSF_JOINT_VENTILATION_RUNTIME_EVIDENCE')
    if root:
        path = Path(root)/'overlap-capacity.json'
        path.write_text(json.dumps(report)); path.chmod(0o400)
    assert not failures and not errors, report
    assert report['remaining'] == 0 and peak <= 8


@ventilation.pytestmark
def test_actual_independent_consumers_with_HTTPS_progress(
        native_pair, authoring, profiles, tmp_path, monkeypatch, request, login_database):
    c = native_pair
    seeds = []
    for index, reference in enumerate((joint, ventilation)):
        directory = tmp_path/('executing-'+str(index)); directory.mkdir(mode=0o700)
        producer = reference.producer.setup.__wrapped__(authoring, directory, profiles, request, monkeypatch)
        server, _, value = producer
        value[1]['revision'] = 'capacity-parallel-v1'
        producer = server, reference.model.results._canonical(value[1]), value
        worker, job_id, raw, value = reference.setup.__wrapped__(producer)
        name = ('joint', 'ventilation')[index]
        assert (value[1]['study_id'], value[1]['revision']) != (
            c.seeds[name].value[1]['study_id'], c.seeds[name].value[1]['revision'])
        seeds.append(SimpleNamespace(worker=worker, job_id=job_id, raw=raw, value=value, directory=directory))
    def factory(seed):
        def build(*, farm_authoring_service):
            old = seed.worker.server
            binding = type(old.binding)(farm_authoring_service, old.binding.input_authority,
                                         input_rights=seed.value[-1])
            server = type(old)(binding, old.directory, input_resolver=old.input_resolver,
                               integrity_key=old.integrity_key)
            return type(seed.worker.results)(server, integrity_key=seed.worker.results.integrity_key)
        return build
    c.options['deps'] = replace(c.deps,
        crop_climate_joint_result_store_factory=factory(seeds[0]),
        crop_greenhouse_ventilation_result_store_factory=factory(seeds[1]))
    from app.crop_greenhouse_ventilation_operator_config import load_ventilation_api_runtime
    runtime = load_ventilation_api_runtime(c.path)
    budget_path = tmp_path/'registration-budget.lock'
    operator.bind_registration_budget(runtime.farm_authoring, budget_path)
    states, prefixes, processes = [], [], []
    with served(runtime, c.config.certificate) as (send, replies):
        with ExitStack() as stack:
            for index, seed in enumerate(seeds):
                model = ('crop-climate-joint', 'crop-greenhouse-ventilation')[index]
                status, raw = send('POST', '/v1/'+model+'-executions', seed.raw)
                assert status == 202 and json.loads(raw)['job_id'] == seed.job_id
                directory = seed.directory/'consumer'; directory.mkdir(mode=0o700)
                builder = consumer.joint_factory if index == 0 else ventilation_factory
                _, file = builder(seed.worker, seed.value, directory)
                source = file.read_text().replace('chunk_budget=128', 'chunk_budget=8').replace('    return loop\n',
                    '    from test_crop_joint_ventilation_connection_capacity import operator as budget_operator\n'
                    f'    budget_operator.bind_registration_budget(worker.server.binding.farms, Path({str(budget_path)!r}))\n'
                    '    budget_operator.bind_worker_custody_wait(worker.server)\n'
                    '    return loop\n')
                source = source.replace("'state':outcome.state,", "'reason_code':outcome.reason_code,'state':outcome.state,", 1)
                assert 'budget_operator.bind_registration_budget' in source
                file.write_text(source)
                (directory/'block').touch(mode=0o600)
                process, events, errors = stack.enter_context(capacity_consumer(directory))
                stack.callback((directory/'block').unlink, missing_ok=True)
                processes.append((process, events, errors, directory))
                consumer.legacy.wait_for(lambda:(directory/'claimed').exists(), process, timeout=20)
            assert len({p.pid for p, *_ in processes}) == 2
            for _, _, _, directory in processes: (directory/'block').unlink()
            deadline = time.monotonic()+240
            terminal = set()
            while len(terminal) < 2:
                assert time.monotonic() < deadline
                assert all(p.poll() is None for p, *_ in processes)
                for index, seed in enumerate(seeds):
                    model = ('crop-climate-joint', 'crop-greenhouse-ventilation')[index]
                    path = '/v1/jobs/'+seed.job_id+'/'+model+'-execution'
                    for suffix in ('', '/prefix'):
                        status, raw = send('GET', path+suffix)
                        assert status in (200, 409, 503), (model, suffix, status)
                        if status == 200:
                            body = json.loads(raw)
                            if suffix: prefixes.append({'model':model,'status':body['prefix_status']})
                            else:
                                states.append({'model':model,'state':body['job']['state']})
                                assert body['job']['state'] not in ('failed', 'hold', 'canceled'), (model, body['job']['state'])
                                if body['job']['state'] == 'succeeded': terminal.add(index)
                time.sleep(.05)
            for index, (process, _, _, directory) in enumerate(processes):
                job = seeds[index].worker.jobs.get_job('tenant-1', seeds[index].job_id)
                consumer.legacy.wait_for(lambda:(directory/('attempt-'+str(job['attempt_count'])+'.private.json')).exists(), process, timeout=20)
                proof = consumer.attempt_proof(directory, job['attempt_count'])
                assert proof['state'] == 'succeeded' and proof['calls']['step'] == 16
        assert all(p.returncode == 0 and errors == [''] for p, _, errors, _ in processes)
        for index, seed in enumerate(seeds):
            model = ('crop-climate-joint', 'crop-greenhouse-ventilation')[index]
            path = '/v1/jobs/'+seed.job_id+'/'+model+'-execution'
            seed.value[-1].allowed = False
            try: assert send('GET', path)[0] == 422
            finally: seed.value[-1].allowed = True
            assert send('GET', path)[0] == 200
    numeric_records = 0
    for index, seed in enumerate(seeds):
        original = json.loads(seed.worker.server.inspect('tenant-1', seed.raw))
        assert original['steps'] == 16 and original['status'] == 'completed'
        assert original['times']['last_confirmed']['at'] == '2026-10-01T00:00:32.123456Z'
        old = c.seeds[('joint', 'ventilation')[index]]
        old_progress = old.store.server.inspect('tenant-1', old.raw)
        current_progress = seed.worker.server.inspect('tenant-1', seed.raw)
        for kind in ('samples', 'events'):
            actual = seed.worker.server.page('tenant-1', seed.raw, current_progress, kind)['records']
            expected = old.store.server.page('tenant-1', old.raw, old_progress, kind)['records']
            assert [(r['value'], r['time']) for r in actual] == [(r['value'], r['time']) for r in expected]
            numeric_records += len(actual)
    role = c.jobs.runtime_identity[0].roles['authority']
    with psycopg.connect(login_database['admin']) as conn:
        assert conn.execute('SELECT count(*) FROM pg_stat_activity WHERE usename=%s', (role,)).fetchone()[0] == 0
        data = Path(conn.execute('SHOW data_directory').fetchone()[0])
        assert 'too many connections for role' not in (data.parent/'server.log').read_text()
    root = os.environ.get('OSSF_JOINT_VENTILATION_RUNTIME_EVIDENCE')
    if root:
        path = Path(root)/'independent-HTTPS-capacity.json'
        path.write_text(json.dumps({'independent_consumers':2,'same_database':True,'connection_limit':8,
            'states':states,'prefixes':prefixes,'exit_codes':[p.returncode for p, *_ in processes],
            'HTTP_status_counts':{status:sum(r['status']==status for r in replies) for status in (200,202,409,422,503)},
            'original_steps_UTC':True,'late_rights_revocation_rejected':True,'remaining_authority_connections':0,
            'all_original_sample_event_values_UTC':True,'original_records_compared':numeric_records,
            'connection_limit_errors':0,'G0_G4':'not_assessed'})); path.chmod(0o400)


def test_registration_budget_releases_after_authority_denial(tmp_path, monkeypatch):
    from app.farm_authoring_storage import FarmAuthoringService
    farms = object.__new__(FarmAuthoringService)
    allowed = False
    def read(self, *_):
        if not allowed: raise PermissionError('current rights denied')
        return 'checked'
    monkeypatch.setattr(FarmAuthoringService, 'read_registration', read)
    before = len(os.listdir('/proc/self/fd'))
    operator.bind_registration_budget(farms, tmp_path/'registration-budget.lock')
    with pytest.raises(PermissionError): farms.read_registration('tenant-1')
    allowed = True
    assert farms.read_registration('tenant-1') == 'checked'
    assert len(os.listdir('/proc/self/fd')) == before
    with pytest.raises(ValueError, match='already bound'):
        operator.bind_registration_budget(farms, tmp_path/'registration-budget.lock')


@pytest.mark.parametrize('unsafe', ['symlink', 'permissions'])
def test_registration_budget_rejects_unsafe_lock_before_authority(tmp_path, monkeypatch, unsafe):
    from app.farm_authoring_storage import FarmAuthoringService
    farms = object.__new__(FarmAuthoringService)
    def denied(*_): pytest.fail('unsafe budget called authority')
    monkeypatch.setattr(FarmAuthoringService, 'read_registration', denied)
    path = tmp_path/'registration-budget.lock'
    if unsafe == 'symlink':
        other = tmp_path/'other'; other.touch(mode=0o600); path.symlink_to(other)
    else: path.touch(mode=0o644)
    operator.bind_registration_budget(farms, path)
    with pytest.raises((ValueError, OSError)): farms.read_registration('tenant-1')


@ventilation.pytestmark
def test_reader_does_not_spend_worker_attempt_before_checkpoint_confirmation(worker_setup, monkeypatch):
    worker, job_id, raw, _ = worker_setup
    lease = worker.jobs.claim(600, tenant_id='tenant-1', allowed_stages=('simulation',), job_id=job_id)
    progress = json.loads(worker.server.advance('tenant-1', raw, budget=8))
    assert progress['steps'] == 7
    files = ventilation.producer.model.files
    original, pending = files._file, Event()
    def measured(*args, **kwargs):
        try: return original(*args, **kwargs)
        except files.CycleCustodyPending:
            pending.set()
            raise
    monkeypatch.setattr(files, '_file', measured)
    operator.bind_worker_custody_wait(worker.server)
    with ThreadPoolExecutor(max_workers=1) as pool:
        with worker.server._open('tenant-1', raw, False):
            future = pool.submit(worker._confirm, lease)
            assert pending.wait(20), 'actual reader/writer contention not reached'
            with pytest.raises(FutureTimeout): future.result(timeout=.2)
        confirmed = future.result(timeout=40)
    assert confirmed['checkpoint']['steps'] == progress['steps']
    job = worker.jobs.get_job('tenant-1', job_id)
    assert job['state'] == 'simulating' and job['attempt_count'] == 1


@pytest.mark.parametrize('server_type,pending_type', [
    (operator.JointServerCustody, operator.JointCustodyPending),
    (operator.VentilationServerCustody, operator.VentilationCustodyPending)])
@pytest.mark.parametrize('mode', ['acquire_busy', 'late_busy', 'denied', 'deadline'])
def test_worker_wait_retries_only_entry_and_keeps_authority_and_deadline(
        server_type, pending_type, mode, monkeypatch):
    calls = []
    @contextmanager
    def opened(self, *_):
        calls.append('enter')
        if mode == 'denied': raise PermissionError('current rights denied')
        if mode == 'deadline' or (mode == 'acquire_busy' and len(calls) == 1):
            raise pending_type('reader busy')
        yield 'checked-session'
        if mode == 'late_busy': raise pending_type('late operation failure')
    monkeypatch.setattr(server_type, '_open', opened)
    server = object.__new__(server_type)
    operator.bind_worker_custody_wait(server)
    if mode == 'deadline':
        clock = iter((0, 31))
        monkeypatch.setattr(operator.time, 'monotonic', lambda:next(clock))
    if mode == 'acquire_busy':
        with server._open(): pass
        assert calls == ['enter', 'enter']
    else:
        with pytest.raises(PermissionError if mode == 'denied' else pending_type):
            with server._open(): pass
        assert calls == ['enter']
    with pytest.raises(ValueError): operator.bind_worker_custody_wait(server)
