"""Owned automatic collection; synthetic research and actual SCRAM/processes."""

from contextlib import contextmanager
from dataclasses import asdict, replace
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import select
import signal
import subprocess
import sys
from threading import Event
import time
from types import SimpleNamespace
from uuid import uuid4

from psycopg import sql
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from app.deterministic_job_discovery import (
    CollectionJobDiscovery, DeterministicJobDiscovery, DiscoveryCursor,
    DiscoveryHold, DiscoveryPage, DiscoveredJob,
)
from app.collection_consume import CollectionWorkerLoop, CollectionLoopHold, main
from app.owned_fixture_collection import CollectionService, CollectionWorker, CollectionOutcome
from app.owned_fixture_registry import OwnedFixtureRegistry
from login_database import login_database, login_scope
from test_owned_fixture_collection import collection_setup
from test_deterministic_job_discovery import isolated_jobs, isolated_page, row, persisted_digest, queue
from test_deterministic_work import process_cpu_seconds

ROOT = Path(__file__).resolve().parents[2]
VERSION = 'owned-fixture-collection-input-v1'


@pytest.fixture
def isolated_collection(isolated_jobs):
    jobs, principal = isolated_jobs
    principal['scopes'] = {'metadata', 'artifact', 'collection_execute'}
    worker = CollectionWorker(CollectionService(jobs, OwnedFixtureRegistry(ROOT)), tenant_id='tenant-a')
    return CollectionWorkerLoop(worker, page_size=2), worker, principal


def test_collection_profile_has_fixed_scopes_and_versions(monkeypatch, isolated_collection):
    loop, worker, principal = isolated_collection
    selected = row(VERSION)
    isolated_page(monkeypatch, worker.service.jobs, [row('economic-calculation-input-v1'), selected])
    page = loop.discovery.page(limit=2)
    assert [(j.job_id, j.input_version) for j in page.jobs] == [(str(selected['job_id']), VERSION)]
    assert page.next_cursor == DiscoveryCursor(selected['created_at'], str(selected['job_id']))
    assert page.scanned_count == 2 and 'input_bytes' not in repr(page)
    with pytest.raises(DiscoveryHold):
        DeterministicJobDiscovery(worker.service.jobs, tenant_id='tenant-a', input_versions=frozenset({VERSION}))
    principal['scopes'].remove('artifact')
    with pytest.raises(DiscoveryHold, match='^discovery_access_rejected$'):
        loop.discovery.page()


def test_sequential_pages_wait_and_reset_after_raced_claim(monkeypatch, isolated_collection):
    loop, worker, _ = isolated_collection
    identity = str(uuid4())
    cursor = DiscoveryCursor(datetime(2026, 10, 4, tzinfo=timezone.utc), str(uuid4()))
    pages = iter([DiscoveryPage((), 2, cursor),
        DiscoveryPage((DiscoveredJob(identity, VERSION),), 1, None), DiscoveryPage((), 0, None)])
    cursors, waits, dispatched, events = [], [], [], []
    def page(**kwargs):
        cursors.append(kwargs['cursor'])
        return next(pages)
    monkeypatch.setattr(loop.discovery, 'page', page)
    monkeypatch.setattr(worker, 'run_once', lambda job: dispatched.append(job))
    stop = Event()
    def wait(seconds):
        waits.append(seconds)
        if len(waits) == 3: stop.set()
    monkeypatch.setattr(stop, 'wait', wait)
    loop.run(stop, emit=events.append)
    assert cursors == [None, cursor, None] and waits == [1, 1, 1]
    assert dispatched == [identity] and events == []


@pytest.mark.parametrize('field,value', [('poll_seconds', True), ('poll_seconds', 0),
    ('poll_seconds', 61), ('page_size', True), ('page_size', 51)])
def test_invalid_bounds_rejected(isolated_collection, field, value):
    _, worker, _ = isolated_collection
    with pytest.raises(CollectionLoopHold, match='^collection_consumer_binding_rejected$'):
        CollectionWorkerLoop(worker, **{field: value})


def test_pre_mutated_worker_cannot_substitute_a_fake_service(isolated_collection):
    _, worker, _ = isolated_collection
    worker.service = SimpleNamespace(jobs=worker.service.jobs, _binding=lambda:None,
        _pointers=lambda:(), _guard=lambda *_:None)
    with pytest.raises(CollectionLoopHold, match='^collection_consumer_binding_rejected$'):
        CollectionWorkerLoop(worker)


@pytest.mark.parametrize('fault', ['tenant', 'lease', 'service', 'registry', 'provider', 'scope', 'boolean_poll'])
def test_current_binding_and_access_drift_stop_before_discovery(monkeypatch, isolated_collection, fault):
    loop, worker, principal = isolated_collection
    if fault == 'tenant': worker.tenant_id = 'tenant-b'
    elif fault == 'lease': worker.lease_seconds = 1
    elif fault == 'service': worker.service = CollectionService(worker.service.jobs, worker.service.registry)
    elif fault == 'registry': worker.service.registry = OwnedFixtureRegistry(ROOT)
    elif fault == 'provider': worker.service.jobs.principal_provider = lambda: principal
    elif fault == 'scope': principal['scopes'].remove('collection_execute')
    else: loop.poll_seconds = True
    monkeypatch.setattr(loop.discovery, 'page', lambda **_: pytest.fail('changed binding read a page'))
    with pytest.raises(CollectionLoopHold, match='^collection_consumer_binding_rejected$'):
        loop.run(Event(), emit=lambda _: None)


@pytest.mark.parametrize('fault', ['foreign_job', 'boolean_attempt', 'unclosed', 'reason', 'type'])
def test_outcomes_do_not_expose_partial_or_unclosed_metadata(monkeypatch, isolated_collection, fault):
    loop, worker, _ = isolated_collection
    identity = uuid4()
    value = CollectionOutcome(identity, 1, 'succeeded', 'completed', 'a'*64)
    if fault == 'foreign_job': value = replace(value, job_id=uuid4())
    elif fault == 'boolean_attempt': value = replace(value, attempt=True)
    elif fault == 'unclosed': value = replace(value, state='unclosed')
    elif fault == 'reason': value = replace(value, reason_code='private-marker!')
    else: value = {'state': 'succeeded'}
    monkeypatch.setattr(loop.discovery, 'page', lambda **_: DiscoveryPage(
        (DiscoveredJob(str(identity), VERSION),), 1, None))
    monkeypatch.setattr(worker, 'run_once', lambda _: value)
    events = []
    with pytest.raises(CollectionLoopHold, match='^collection_consumer_outcome_rejected$'):
        loop.run(Event(), emit=events.append)
    assert events == []


@pytest.mark.parametrize('mode', ['normal', 'factory_failure', 'execution_failure'])
def test_main_restores_signal_resources_and_fixed_errors(monkeypatch, isolated_collection, capsys, mode):
    loop, _, _ = isolated_collection
    from app.process_stop import SignalStop
    descriptors = []
    initialize = SignalStop.__init__
    def capture(self):
        initialize(self)
        descriptors.extend((self.reader, self.writer))
    monkeypatch.setattr(SignalStop, '__init__', capture)
    def build():
        if mode == 'factory_failure': raise SystemExit('private-marker')
        return loop
    def run(stop, *, emit):
        if mode == 'execution_failure': raise ValueError('private-marker')
        signal.getsignal(signal.SIGTERM)(signal.SIGTERM, None)
        assert stop.is_set()
    monkeypatch.setattr(loop, 'run', run)
    monkeypatch.setattr('app.collection_consume.importlib.import_module', lambda *_: SimpleNamespace(build=build))
    before = {s: signal.getsignal(s) for s in (signal.SIGTERM, signal.SIGINT)}
    reader, writer = os.pipe2(os.O_NONBLOCK | os.O_CLOEXEC)
    old = signal.set_wakeup_fd(writer)
    try:
        assert main(['--factory', 'module:build']) == {'normal':0, 'factory_failure':2, 'execution_failure':3}[mode]
        assert signal.set_wakeup_fd(old) == writer
        assert before == {s: signal.getsignal(s) for s in before}
        for fd in descriptors:
            with pytest.raises(OSError): os.fstat(fd)
        assert len(descriptors) == 2
        captured = capsys.readouterr()
        assert 'private-marker' not in captured.out + captured.err
    finally:
        signal.set_wakeup_fd(old)
        os.close(reader); os.close(writer)


@pytest.mark.parametrize('args', [[], ['--factory', 'private-invalid'],
    ['--factory', 'private-module:build'], ['--factory', 'module:build', '--job-id', 'private-id']])
def test_configuration_rejects_before_import(monkeypatch, capsys, args):
    monkeypatch.setattr('app.collection_consume.importlib.import_module', lambda *_: pytest.fail('invalid import'))
    assert main(args) == 2
    output = capsys.readouterr()
    assert output.out == '' and json.loads(output.err) == {
        'version':1, 'ok':False, 'code':'collection_consumer_startup_rejected'}


def test_actual_scram_discovery_filters_mixed_queue_without_mutation(collection_setup, login_scope):
    service, _, parent, principal = collection_setup
    base, policy, _ = login_scope
    assert not {'simulation_execute'} <= principal['scopes']
    queue(base, 'unrelated-v1', stage='collection')
    selected = service.submit('tenant-a', str(parent['job_id']), 'selected')
    queue(base, VERSION, tenant='tenant-b', stage='collection')
    queue(base, VERSION, stage='simulation')
    future = service.submit('tenant-a', str(parent['job_id']), 'future')
    live = service.submit('tenant-a', str(parent['job_id']), 'live')
    expired = service.submit('tenant-a', str(parent['job_id']), 'expired')
    terminal = service.submit('tenant-a', str(parent['job_id']), 'terminal')
    assert service.jobs.cancel('tenant-a', terminal['job_id'])
    for job in (live, expired):
        assert service.jobs.claim(60, tenant_id='tenant-a', allowed_stages=('collection',), job_id=str(job['job_id']))
    with base.connect() as conn:
        conn.execute(sql.SQL("UPDATE {} SET next_attempt_at=clock_timestamp()+interval '2 hours' WHERE job_id=%s")
            .format(base._table('jobs')), (future['job_id'],))
        conn.execute(sql.SQL("UPDATE {} SET lease_until=clock_timestamp()-interval '1 second' WHERE job_id=%s")
            .format(base._table('jobs')), (expired['job_id'],))
    before = persisted_digest(base)
    discovery = CollectionJobDiscovery(service.jobs, tenant_id='tenant-a')
    with service.jobs.connect() as conn:
        assert conn.pgconn.used_password and conn.info.user == policy.roles['authority']
    first = discovery.page(limit=1)
    assert first.jobs == () and first.next_cursor
    second = discovery.page(cursor=first.next_cursor, limit=1)
    third = discovery.page(cursor=second.next_cursor, limit=1)
    last = discovery.page(cursor=third.next_cursor, limit=1)
    assert [j.job_id for p in (second, third) for j in p.jobs] == [str(selected['job_id']), str(expired['job_id'])]
    assert last.jobs == () and last.next_cursor is None
    assert before == persisted_digest(base)


def collection_factory(service, principal, tmp_path):
    directory = tmp_path/'consumer_private'
    directory.mkdir(mode=0o700)
    config = {'dsn':service.jobs._dsn, 'policy':asdict(service.jobs.runtime_identity[0]),
        'artifacts':str(service.jobs.artifact_root), 'root':str(ROOT),
        'principal':principal | {'scopes':sorted(principal['scopes'])}}
    path = directory/'collection_operator.json'
    path.write_text(json.dumps(config)); path.chmod(0o600)
    factory = directory/'collection_operator.py'
    factory.write_text('''import json, time
from pathlib import Path
from app.runtime_roles import RuntimeLoginPolicy
from app.job_store import JobStore
from app.owned_fixture_registry import OwnedFixtureRegistry
from app.owned_fixture_collection import CollectionService, CollectionWorker
from app.collection_consume import CollectionWorkerLoop
def build():
    root = Path(__file__).parent
    data = json.loads((root/'collection_operator.json').read_text())
    policy = RuntimeLoginPolicy(**data['policy'])
    jobs = JobStore(data['dsn'], policy.schema, Path(data['artifacts']), audit_runtime_grants=True,
        runtime_identity=(policy, 'authority'), principal_provider=lambda:data['principal'])
    service = CollectionService(jobs, OwnedFixtureRegistry(data['root']))
    prepare = service._prepare
    def controlled(*args, **kwargs):
        if (root/'block').exists():
            (root/'claimed').write_text('claimed')
            while (root/'block').exists(): time.sleep(0.02)
        return prepare(*args, **kwargs)
    service._prepare = controlled
    loop = CollectionWorkerLoop(CollectionWorker(service, tenant_id=data['principal']['tenant_id']))
    page = loop.discovery.page
    def observed(**kwargs):
        value = page(**kwargs)
        with (root/'pages').open('a') as trace: trace.write(str(time.monotonic())+'\\n')
        return value
    loop.discovery.page = observed
    return loop
''')
    factory.chmod(0o600)
    return directory


@contextmanager
def consumer(directory):
    env = os.environ | {'PYTHONPATH':os.pathsep.join([str(directory), str(ROOT/'backend')])}
    process = subprocess.Popen([sys.executable, '-m', 'app.collection_consume', '--factory', 'collection_operator:build'],
        env=env, stdin=subprocess.DEVNULL, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    events, errors = [], []
    try:
        assert select.select([process.stdout], [], [], 10)[0], 'consumer did not start'
        first = process.stdout.readline()
        assert first and json.loads(first) == {'version':1, 'event':'started'}
        events.append(json.loads(first))
        yield process, events, errors
    finally:
        if process.poll() is None: process.terminate()
        try:
            output, error = process.communicate(timeout=10)
        except subprocess.TimeoutExpired:
            process.kill(); process.communicate(timeout=10)
            pytest.fail('owned consumer did not stop after cleanup')
        assert len(output)+len(error) < 65536
        events.extend(json.loads(line) for line in output.splitlines())
        errors.append(error)


def wait_for(check, process, timeout=30):
    deadline = time.monotonic()+timeout
    while not check():
        assert process.poll() is None, 'owned consumer ended before expected state'
        assert time.monotonic() < deadline, 'consumer deadline exceeded'
        time.sleep(0.05)


def test_actual_automatic_collection_and_idle_sigterm(collection_setup, tmp_path):
    service, _, parent, principal = collection_setup
    job = service.submit('tenant-a', str(parent['job_id']), 'automatic')
    directory = collection_factory(service, principal, tmp_path)
    with consumer(directory) as (process, events, errors):
        wait_for(lambda: service.jobs.get_job('tenant-a', job['job_id'])['state']=='succeeded', process)
        record = json.loads(service.jobs.read_artifact('tenant-a', job['job_id']))
        assert record['claim_scope']=='software_fixture_only' and record['assessment_status']=='hold'
        assert record['g0_status']==record['g1_status']=='not_accepted'
        assert len(record['sources'])==3 and len(service.jobs.list_attempt_outcomes('tenant-a', job['job_id']))==1
        wait_for(lambda: len((directory/'pages').read_text().splitlines())>=2, process)
        before = process_cpu_seconds(process)
        began = time.monotonic(); time.sleep(2.2)
        cpu = process_cpu_seconds(process)-before
        times = [float(line) for line in (directory/'pages').read_text().splitlines()]
        gaps = [b-a for a,b in zip(times,times[1:])]
        assert cpu<0.5 and all(gap>=1 for gap in gaps)
        stopped = time.monotonic(); process.terminate(); process.wait(timeout=2)
        print('collection_idle='+json.dumps({'observation_seconds':time.monotonic()-began,
            'cpu_seconds':cpu,'minimum_page_gap_seconds':min(gaps),'stop_seconds':time.monotonic()-stopped}))
    assert process.returncode==0 and errors==['']
    assert [e['event'] for e in events]==['started','attempt','stopped']
    assert set(events[1])=={'version','event','job_id','attempt','state','reason_code'}
    assert events[1]['job_id']==str(job['job_id']) and events[1]['state']=='succeeded'


@pytest.mark.parametrize('cancel', [False, True])
def test_actual_signal_during_attempt_fences_next_dispatch(collection_setup, tmp_path, cancel):
    service, _, parent, principal = collection_setup
    first = service.submit('tenant-a', str(parent['job_id']), 'first')
    following = service.submit('tenant-a', str(parent['job_id']), 'following')
    directory = collection_factory(service, principal, tmp_path)
    block = directory/'block'; block.touch(mode=0o600)
    try:
        with consumer(directory) as (process, events, errors):
            wait_for(lambda:(directory/'claimed').exists(), process)
            assert service.jobs.get_publication('tenant-a', first['job_id']) is None
            if cancel: assert service.jobs.cancel('tenant-a', first['job_id'])
            process.send_signal(signal.SIGTERM)
            assert process.poll() is None
            block.unlink(); process.wait(timeout=30)
    finally:
        block.unlink(missing_ok=True)
    assert process.returncode==0 and errors==['']
    assert events[1]['state']==('canceled' if cancel else 'succeeded')
    assert [e['event'] for e in events]==['started','attempt','stopped']
    assert service.jobs.get_job('tenant-a', following['job_id'])['attempt_count']==0
    assert (service.jobs.get_publication('tenant-a', first['job_id']) is None)==cancel


def test_actual_kill_then_expired_lease_recovers_once(collection_setup, login_scope, tmp_path):
    service, _, parent, principal = collection_setup
    base, _, _ = login_scope
    job = service.submit('tenant-a', str(parent['job_id']), 'crash')
    directory = collection_factory(service, principal, tmp_path)
    block = directory/'block'; block.touch(mode=0o600)
    with consumer(directory) as (first, _, _):
        wait_for(lambda:(directory/'claimed').exists(), first)
        first.kill(); first.wait(timeout=5)
    assert first.returncode==-signal.SIGKILL
    assert service.jobs.get_publication('tenant-a', job['job_id']) is None
    assert service.jobs.list_attempt_outcomes('tenant-a', job['job_id'])==[]
    block.unlink()
    with base.connect() as conn:
        conn.execute(sql.SQL("UPDATE {} SET lease_until=clock_timestamp()-interval '1 second' WHERE job_id=%s")
            .format(base._table('jobs')), (job['job_id'],))
    with consumer(directory) as (second, events, errors):
        wait_for(lambda:service.jobs.get_job('tenant-a',job['job_id'])['state']=='succeeded',second)
    assert second.returncode==0 and errors==['']
    assert events[1]['attempt']==2 and events[1]['state']=='succeeded'
    outcomes = service.jobs.list_attempt_outcomes('tenant-a',job['job_id'])
    assert len(outcomes)==2 and {o['termination_reason'] for o in outcomes}=={'lease_expired','completed'}
    assert {o['state'] for o in outcomes}=={'lease_expired','succeeded'}


def test_actual_parent_proof_withdrawal_holds_without_publication(collection_setup, tmp_path):
    service, _, parent, principal = collection_setup
    job = service.submit('tenant-a', str(parent['job_id']), 'withdrawal')
    directory = collection_factory(service, principal, tmp_path)
    block = directory/'block'; block.touch(mode=0o600)
    try:
        with consumer(directory) as (process, events, errors):
            wait_for(lambda:(directory/'claimed').exists(), process)
            decision = service.jobs.list_decisions('tenant-a',parent['job_id'])[0]
            content = service.jobs._content_directory('tenant-a')
            try:
                fd = os.open(decision['output_sha256'],os.O_WRONLY|os.O_TRUNC|os.O_NOFOLLOW,dir_fd=content)
                with os.fdopen(fd,'wb') as stream: stream.write(b'private synthetic invalid parent proof')
            finally:
                os.close(content)
            process.send_signal(signal.SIGTERM)
            block.unlink(); process.wait(timeout=30)
    finally:
        block.unlink(missing_ok=True)
    assert process.returncode==0 and errors==['']
    assert events[1]['state']=='hold' and events[1]['reason_code']=='collection_input_hold'
    assert service.jobs.get_publication('tenant-a',job['job_id']) is None
    assert 'private' not in json.dumps(events)


def test_actual_grant_withdrawal_stops_with_fixed_failure(collection_setup, login_scope, tmp_path):
    service, _, _, principal = collection_setup
    base, policy, _ = login_scope
    directory = collection_factory(service,principal,tmp_path)
    with consumer(directory) as (process, events, errors):
        wait_for(lambda:(directory/'pages').exists(),process)
        with base.connect() as conn:
            conn.execute(sql.SQL('REVOKE SELECT ON {} FROM {}').format(
                base._table('jobs'),sql.Identifier(policy.roles['authority'])))
        process.wait(timeout=10)
    assert process.returncode==3
    assert events==[{'version':1,'event':'started'}]
    assert json.loads(errors[0])=={'version':1,'ok':False,'code':'collection_consumer_execution_unresolved'}
