"""Foreground queue consumption; isolated checks and actual process proofs."""

from datetime import datetime, timezone
from contextlib import contextmanager
from dataclasses import asdict
import json
import os
from pathlib import Path
import select
import signal
import subprocess
import sys
import time
from threading import Event
from types import SimpleNamespace
from uuid import uuid4

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from app.deterministic_work import DeterministicWorkerLoop, LoopHold, main
from app.deterministic_job_discovery import DiscoveryCursor, DiscoveryPage, DiscoveredJob
from app.economic_calculation_worker import EconomicCalculationWorker, EconomicCalculationOutcome
from app.job_store import JobStore
from app.runtime_roles import RuntimeLoginPolicy
from login_database import login_database, login_scope
from test_economic_calculation_worker import calculation_setup, economic_api, PROFILE, result_count
from test_api_break_even_plan import plan_api, post as plan_post

VERSION = 'economic-calculation-input-v1'


@pytest.fixture
def isolated_loop(monkeypatch, tmp_path):
    principal = {'authenticated': True, 'tenant_id': 'tenant-a',
                 'scopes': {'metadata', 'simulation_execute'}}
    policy = RuntimeLoginPolicy('test_jobs', 'test_owner', 'test_runtime', 'postgres')
    jobs = JobStore('dbname=postgres', policy.schema, tmp_path / 'unused',
                    runtime_identity=(policy, 'authority'), audit_runtime_grants=True,
                    principal_provider=lambda: principal)
    # Isolated worker boundary; actual SCRAM/process cases use normal constructors.
    worker = object.__new__(EconomicCalculationWorker)
    worker.jobs, worker.tenant_id = jobs, 'tenant-a'
    worker.farm_scenario_service = worker.authored_run_store = None
    monkeypatch.setattr(worker, '_binding', lambda: None)
    return DeterministicWorkerLoop(worker, input_versions=frozenset({VERSION})), worker, principal


def completed(identity):
    from uuid import UUID
    return EconomicCalculationOutcome(UUID(identity), 1, 'succeeded', 'completed', 'synthetic-result')


def test_follow_unrelated_cursor_and_wait_after_each_page(monkeypatch, isolated_loop):
    loop, worker, _ = isolated_loop
    identity = str(uuid4())
    cursor = DiscoveryCursor(datetime(2026, 10, 2, tzinfo=timezone.utc), str(uuid4()))
    pages = iter([DiscoveryPage((), 25, cursor),
                  DiscoveryPage((DiscoveredJob(identity, VERSION),), 1, None)])
    observed, dispatched, waits, events = [], [], [], []
    def page(*, cursor=None, limit=25):
        observed.append((cursor, limit))
        return next(pages)
    def run_once(target):
        dispatched.append(target)
        return completed(target)
    stop = Event()
    def wait(seconds):
        waits.append(seconds)
        if len(waits) == 2: stop.set()
    monkeypatch.setattr(loop.discovery, 'page', page)
    monkeypatch.setattr(worker, 'run_once', run_once)
    monkeypatch.setattr(stop, 'wait', wait)
    loop.run(stop, emit=events.append)
    assert observed == [(None, 25), (cursor, 25)] and waits == [1, 1]
    assert dispatched == [identity]
    assert events == [{'version': 1, 'event': 'attempt', 'job_id': identity,
                       'attempt': 1, 'state': 'succeeded', 'reason_code': 'completed'}]


def test_stop_during_attempt_prevents_next_dispatch(monkeypatch, isolated_loop):
    loop, worker, _ = isolated_loop
    identities = [str(uuid4()), str(uuid4())]
    monkeypatch.setattr(loop.discovery, 'page', lambda **_: DiscoveryPage(
        tuple(DiscoveredJob(value, VERSION) for value in identities), 2, None))
    stop, calls = Event(), []
    def run_once(identity):
        calls.append(identity)
        stop.set()
        return completed(identity)
    monkeypatch.setattr(worker, 'run_once', run_once)
    monkeypatch.setattr(stop, 'wait', lambda *_: pytest.fail('stopped consumer waited'))
    loop.run(stop, emit=lambda *_: None)
    assert calls == identities[:1]


@pytest.mark.parametrize('field,value', [('poll_seconds', True), ('poll_seconds', 0),
    ('poll_seconds', 61), ('page_size', False), ('page_size', 0), ('page_size', 51)])
def test_poll_and_page_bounds_are_closed(isolated_loop, field, value):
    _, worker, _ = isolated_loop
    with pytest.raises(LoopHold, match='^deterministic_binding_rejected$'):
        DeterministicWorkerLoop(worker, input_versions=frozenset({VERSION}), **{field: value})


@pytest.mark.parametrize('versions', [frozenset({'break-even-calculation-input-v1'}),
    frozenset({'economic-calculation-input-v2'}), frozenset({'economic-calculation-input-v3'})])
def test_selected_versions_require_matching_worker_and_dependencies(isolated_loop, versions):
    _, worker, _ = isolated_loop
    with pytest.raises(LoopHold, match='^deterministic_binding_rejected$'):
        DeterministicWorkerLoop(worker, input_versions=versions)


def test_current_worker_tenant_drift_prevents_dispatch(monkeypatch, isolated_loop):
    loop, worker, _ = isolated_loop
    def page(**_):
        worker.tenant_id = 'tenant-b'
        return DiscoveryPage((DiscoveredJob(str(uuid4()), VERSION),), 1, None)
    monkeypatch.setattr(loop.discovery, 'page', page)
    monkeypatch.setattr(worker, 'run_once', lambda *_: pytest.fail('changed tenant dispatched'))
    with pytest.raises(LoopHold, match='^deterministic_binding_rejected$'):
        loop.run(Event(), emit=lambda *_: None)


@pytest.mark.parametrize('fault', ['job', 'attempt_bool', 'attempt_over', 'state', 'reason', 'type'])
def test_invalid_or_unclosed_outcome_stops_without_emission(monkeypatch, isolated_loop, fault):
    loop, worker, _ = isolated_loop
    identity = str(uuid4())
    value = completed(identity)
    from dataclasses import replace
    if fault == 'job': value = replace(value, job_id=uuid4())
    elif fault == 'attempt_bool': value = replace(value, attempt=True)
    elif fault == 'attempt_over': value = replace(value, attempt=4)
    elif fault == 'state': value = replace(value, state='unclosed')
    elif fault == 'reason': value = replace(value, reason_code='private-test-marker!')
    elif fault == 'type': value = {'state': 'succeeded'}
    monkeypatch.setattr(loop.discovery, 'page', lambda **_: DiscoveryPage(
        (DiscoveredJob(identity, VERSION),), 1, None))
    monkeypatch.setattr(worker, 'run_once', lambda *_: value)
    events = []
    with pytest.raises(LoopHold, match='^deterministic_outcome_rejected$'):
        loop.run(Event(), emit=events.append)
    assert events == []


def test_raced_claim_returns_no_event_and_resets_cursor(monkeypatch, isolated_loop):
    loop, worker, _ = isolated_loop
    cursor = DiscoveryCursor(datetime(2026, 10, 2, tzinfo=timezone.utc), str(uuid4()))
    pages = iter([DiscoveryPage((), 25, cursor),
        DiscoveryPage((DiscoveredJob(str(uuid4()), VERSION),), 1, None), DiscoveryPage((), 0, None)])
    cursors, waits, events = [], [], []
    def page(**kwargs):
        cursors.append(kwargs['cursor'])
        return next(pages)
    stop = Event()
    def wait(seconds):
        waits.append(seconds)
        if len(waits) == 3: stop.set()
    monkeypatch.setattr(loop.discovery, 'page', page)
    monkeypatch.setattr(worker, 'run_once', lambda *_: None)
    monkeypatch.setattr(stop, 'wait', wait)
    loop.run(stop, emit=events.append)
    assert cursors == [None, cursor, None] and events == [] and waits == [1, 1, 1]


@pytest.mark.parametrize('args', [[], ['--factory', 'bad-reference'],
    ['--factory', 'module:build', '--job-id', 'private-test-marker'],
    ['--factory', 'module:build;private-test-marker']])
def test_command_arguments_have_closed_errors(capsys, args):
    import json
    assert main(args) == 2
    captured = capsys.readouterr()
    assert captured.out == ''
    assert json.loads(captured.err) == {'version': 1, 'ok': False, 'code': 'deterministic_startup_rejected'}


def test_help_does_not_load_operator(monkeypatch, capsys):
    monkeypatch.setattr('app.deterministic_work.importlib.import_module', lambda *_: pytest.fail('help imported factory'))
    assert main(['--help']) == 0
    assert '--factory' in capsys.readouterr().out


def test_factory_system_exit_is_rejected_and_handlers_restored(monkeypatch, capsys):
    import json, signal
    before = {sig: signal.getsignal(sig) for sig in (signal.SIGTERM, signal.SIGINT)}
    def build():
        raise SystemExit(0)
    monkeypatch.setattr('app.deterministic_work.importlib.import_module', lambda *_: SimpleNamespace(build=build))
    assert main(['--factory', 'module:build']) == 2
    assert json.loads(capsys.readouterr().err)['code'] == 'deterministic_startup_rejected'
    assert {sig: signal.getsignal(sig) for sig in before} == before


@pytest.mark.parametrize('failure', [False, True])
def test_process_signal_and_fixed_failure_output_restore_handlers(monkeypatch, isolated_loop, capsys, failure):
    import json, signal
    loop, _, _ = isolated_loop
    before = {sig: signal.getsignal(sig) for sig in (signal.SIGTERM, signal.SIGINT)}
    def run(stop, *, emit):
        if failure: raise ValueError('private-test-marker')
        signal.getsignal(signal.SIGTERM)(signal.SIGTERM, None)
        assert stop.is_set()
    monkeypatch.setattr(loop, 'run', run)
    monkeypatch.setattr('app.deterministic_work.importlib.import_module', lambda *_: SimpleNamespace(build=lambda: loop))
    assert main(['--factory', 'module:build']) == (3 if failure else 0)
    captured = capsys.readouterr()
    assert 'private-test-marker' not in captured.out + captured.err
    if failure: assert json.loads(captured.err)['code'] == 'deterministic_execution_unresolved'
    else: assert [json.loads(line)['event'] for line in captured.out.splitlines()] == ['started', 'stopped']
    assert {sig: signal.getsignal(sig) for sig in before} == before


def test_signal_handler_does_not_acquire_event_lock(monkeypatch, isolated_loop):
    loop, _, _ = isolated_loop
    def locked_set(*_):
        raise AssertionError('signal handler acquired Event synchronization')
    monkeypatch.setattr(Event, 'set', locked_set)
    def run(stop, *, emit):
        signal.getsignal(signal.SIGTERM)(signal.SIGTERM, None)
        assert stop.is_set()
    monkeypatch.setattr(loop, 'run', run)
    monkeypatch.setattr('app.deterministic_work.importlib.import_module', lambda *_: SimpleNamespace(build=lambda: loop))
    assert main(['--factory', 'module:build']) == 0


@pytest.mark.parametrize('mode', ['normal', 'factory_failure', 'execution_failure'])
def test_previous_wakeup_fd_is_restored_and_owned_pipe_closed(monkeypatch, isolated_loop, mode):
    from app.deterministic_work import _SignalStop
    loop, _, _ = isolated_loop
    owned = []
    initialize = _SignalStop.__init__
    def capture(self):
        initialize(self)
        owned.extend((self.reader, self.writer))
    monkeypatch.setattr(_SignalStop, '__init__', capture)
    def build():
        if mode == 'factory_failure': raise ValueError('private-test-marker')
        return loop
    def run(stop, *, emit):
        if mode == 'execution_failure': raise ValueError('private-test-marker')
        stop.set()
    monkeypatch.setattr(loop, 'run', run)
    monkeypatch.setattr('app.deterministic_work.importlib.import_module', lambda *_: SimpleNamespace(build=build))
    reader, writer = os.pipe2(os.O_NONBLOCK | os.O_CLOEXEC)
    previous = signal.set_wakeup_fd(writer)
    try:
        assert main(['--factory', 'module:build']) == {'normal':0, 'factory_failure':2, 'execution_failure':3}[mode]
        assert signal.set_wakeup_fd(previous) == writer
        assert len(owned) == 2
        for descriptor in owned:
            with pytest.raises(OSError): os.fstat(descriptor)
    finally:
        signal.set_wakeup_fd(previous)
        os.close(reader); os.close(writer)


def economic_factory(worker, principal, tmp_path):
    directory = tmp_path / 'loop_private'
    directory.mkdir(mode=0o700)
    document = {'dsn': worker.jobs._dsn, 'policy': asdict(worker.jobs.runtime_identity[0]),
        'artifacts': str(worker.jobs.artifact_root),
        'principal': principal | {'scopes': sorted(principal['scopes'])},
        'hold_scope': worker.results._candidates._source._holds._scope_resolver()}
    config = directory / 'loop_operator.json'
    config.write_text(json.dumps(document)); config.chmod(0o600)
    factory = directory / 'loop_operator.py'
    factory.write_text('''import json, time
from pathlib import Path
from app.runtime_roles import RuntimeLoginPolicy
from app.job_store import JobStore
from app.market_source_store import MarketSourceStore
from app.market_candidate_store import MarketCandidateStore
from app.market_result_store import MarketResultStore
from app.market_hold_store import MarketHoldStore
from app.thermal_run_store import ThermalRunStore
from app.api_market_source import _MarketSources
from app.economic_calculation_worker import EconomicCalculationWorker
from app.deterministic_work import DeterministicWorkerLoop
from test_market_hold_store import context_verifier, HOLD_KEY
def build():
    root = Path(__file__).parent
    data = json.loads((root/'loop_operator.json').read_text())
    policy = RuntimeLoginPolicy(**data['policy'])
    provider = lambda: data['principal']
    kwargs = dict(runtime_identity=(policy, 'authority'), principal_provider=provider)
    jobs = JobStore(data['dsn'], policy.schema, Path(data['artifacts']), audit_runtime_grants=True, **kwargs)
    sources = MarketSourceStore(data['dsn'], policy.schema, **kwargs)
    contexts = ThermalRunStore(data['dsn'], policy.schema, gate_key=b'synthetic-gate-key-32-bytes-long!',
        release_verifier=lambda *_: None, context_verifier=context_verifier, **kwargs)
    holds = MarketHoldStore(data['dsn'], policy.schema, context_store=contexts,
        scope_resolver=lambda *_: data['hold_scope'], signing_key=HOLD_KEY, **kwargs)
    candidates = MarketCandidateStore(data['dsn'], policy.schema,
        _MarketSources(sources, holds, principal_provider=provider), **kwargs)
    results = MarketResultStore(data['dsn'], policy.schema, candidates, **kwargs)
    worker = EconomicCalculationWorker(jobs, results, tenant_id=data['principal']['tenant_id'])
    if (root/'block').exists():
        calculate = worker._calculate
        def controlled(value):
            (root/'claimed').write_text('claimed')
            while (root/'block').exists(): time.sleep(0.02)
            return calculate(value)
        worker._calculate = controlled
    loop = DeterministicWorkerLoop(worker, input_versions=frozenset({'economic-calculation-input-v1'}), page_size=50)
    page = loop.discovery.page
    def observed(**kwargs):
        value = page(**kwargs)
        with (root/'pages').open('a') as log: log.write(str(time.monotonic())+'\\n')
        return value
    loop.discovery.page = observed
    return loop
''')
    factory.chmod(0o600)
    return directory


@contextmanager
def process_consumer(directory, reference='loop_operator:build'):
    env = os.environ | {'PYTHONPATH': os.pathsep.join([str(directory),
        str(Path(__file__).parent), str(Path(__file__).parents[1])])}
    process = subprocess.Popen([sys.executable, '-m', 'app.deterministic_work', '--factory', reference],
        env=env, stdin=subprocess.DEVNULL, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    events, errors = [], []
    try:
        ready = select.select([process.stdout], [], [], 10)[0]
        assert ready, 'owned consumer did not report startup'
        first = process.stdout.readline()
        assert first and json.loads(first) == {'version': 1, 'event': 'started'}, 'owned consumer startup rejected'
        events.append(json.loads(first))
        yield process, events, errors
    finally:
        if process.poll() is None: process.terminate()
        try:
            output, error = process.communicate(timeout=10)
        except subprocess.TimeoutExpired:
            process.kill(); process.communicate(timeout=10)
            pytest.fail('owned consumer did not stop after test cleanup')
        assert len(output) + len(error) < 65536, 'consumer output exceeded metadata bound'
        events.extend(json.loads(line) for line in output.splitlines())
        errors.append(error)


def wait_for(check, process, *, timeout=180):
    deadline = time.monotonic() + timeout
    while not check():
        assert process.poll() is None, 'owned consumer ended before expected persisted state'
        assert time.monotonic() < deadline, 'owned consumer did not reach expected state'
        time.sleep(0.05)


def process_cpu_seconds(process):
    fields = Path(f'/proc/{process.pid}/stat').read_text().rsplit(')', 1)[1].split()
    return (int(fields[11]) + int(fields[12])) / os.sysconf('SC_CLK_TCK')


def test_module_entry_accepts_canonical_consumer_type(tmp_path):
    factory = tmp_path/'entry_operator.py'
    factory.write_text('''from pathlib import Path
from app.job_store import JobStore
from app.runtime_roles import RuntimeLoginPolicy
from app.economic_calculation_worker import EconomicCalculationWorker
from app.deterministic_work import DeterministicWorkerLoop
def build():
    policy = RuntimeLoginPolicy('test_jobs', 'test_owner', 'test_runtime', 'postgres')
    jobs = JobStore('dbname=postgres', policy.schema, Path('/unused'),
        runtime_identity=(policy, 'authority'), audit_runtime_grants=True,
        principal_provider=lambda: {'authenticated': True, 'tenant_id': 'tenant-a',
            'scopes': {'metadata', 'simulation_execute'}})
    worker = object.__new__(EconomicCalculationWorker)
    worker.jobs, worker.tenant_id = jobs, 'tenant-a'
    worker.farm_scenario_service = worker.authored_run_store = None
    worker._binding = lambda: None
    loop = DeterministicWorkerLoop(worker, input_versions=frozenset({'economic-calculation-input-v1'}))
    loop.run = lambda stop, *, emit: stop.set()
    return loop
''')
    env = os.environ | {'PYTHONPATH': os.pathsep.join([str(tmp_path), str(Path(__file__).parents[1])])}
    process = subprocess.run([sys.executable, '-m', 'app.deterministic_work', '--factory',
        'entry_operator:build'], env=env, capture_output=True, text=True, timeout=10)
    assert process.returncode == 0
    assert process.stderr == '' and [json.loads(line)['event'] for line in process.stdout.splitlines()] == ['started', 'stopped']


@pytest.mark.parametrize('login_scope', [PROFILE], indirect=True)
def test_scram_idle_polling_cpu_and_sigterm(calculation_setup, tmp_path):
    worker, jobs, results, initial, _, principal = calculation_setup
    assert jobs.cancel('tenant-1', initial['job_id'])
    directory = economic_factory(worker, principal, tmp_path)
    with process_consumer(directory) as (process, events, errors):
        trace = directory/'pages'
        wait_for(lambda: trace.exists(), process, timeout=10)
        before = process_cpu_seconds(process)
        began = time.monotonic()
        time.sleep(2.2)
        elapsed, cpu = time.monotonic()-began, process_cpu_seconds(process)-before
        pages = [float(line) for line in trace.read_text().splitlines()]
        gaps = [b-a for a,b in zip(pages, pages[1:])]
        assert 2 <= len(pages) <= 4 and all(gap >= 1 for gap in gaps) and cpu < 0.5
        stopped = time.monotonic()
        process.terminate(); process.wait(timeout=2)
        stop_seconds = time.monotonic()-stopped
        print('deterministic_idle='+json.dumps({'observation_seconds':elapsed, 'cpu_seconds':cpu,
            'pages':len(pages), 'minimum_page_gap_seconds':min(gaps), 'stop_seconds':stop_seconds}))
    assert process.returncode == 0 and errors == ['']
    assert [event['event'] for event in events] == ['started', 'stopped'] and result_count(results) == 0


@pytest.mark.parametrize('login_scope', [PROFILE], indirect=True)
@pytest.mark.parametrize('cancel', [False, True])
def test_scram_automatic_economic_job_and_signal_during_attempt(calculation_setup, tmp_path, cancel):
    worker, jobs, results, initial, data, principal = calculation_setup
    directory = economic_factory(worker, principal, tmp_path)
    block = directory/'block'; block.touch(mode=0o600)
    following = jobs.submit('tenant-1', 'simulation', data, 'following-job')
    with process_consumer(directory) as (process, events, errors):
        wait_for(lambda: (directory/'claimed').exists(), process)
        assert result_count(results) == 0 and jobs.get_publication('tenant-1', initial['job_id']) is None
        if cancel: assert jobs.cancel('tenant-1', initial['job_id'])
        process.send_signal(signal.SIGTERM)
        assert process.poll() is None
        block.unlink()
        process.wait(timeout=30)
    assert process.returncode == 0 and errors == ['']
    assert [event['event'] for event in events] == ['started', 'attempt', 'stopped']
    attempt = events[1]
    assert attempt['job_id'] == str(initial['job_id']) and attempt['state'] == ('canceled' if cancel else 'succeeded')
    assert set(attempt) == {'version', 'event', 'job_id', 'attempt', 'state', 'reason_code'}
    assert jobs.get_job('tenant-1', following['job_id'])['state'] == 'queued'
    assert jobs.get_job('tenant-1', following['job_id'])['attempt_count'] == 0
    assert result_count(results) == (0 if cancel else 1)
    assert len(jobs.list_attempt_outcomes('tenant-1', initial['job_id'])) == 1
    if not cancel:
        saved = results.get_market_result(data['scenario_id'], data['scenario_revision'])
        assert saved.assessment_status == 'hold' and jobs.get_publication('tenant-1', initial['job_id']) is not None


@pytest.mark.parametrize('login_scope', [PROFILE], indirect=True)
def test_scram_killed_process_and_automatic_expired_lease_recovery(calculation_setup, tmp_path):
    from psycopg import sql
    worker, jobs, results, initial, _, principal = calculation_setup
    directory = economic_factory(worker, principal, tmp_path)
    block = directory/'block'; block.touch(mode=0o600)
    with process_consumer(directory) as (first, _, _):
        wait_for(lambda: (directory/'claimed').exists(), first)
        first.kill(); first.wait(timeout=5)
    assert first.returncode == -signal.SIGKILL and result_count(results) == 0
    assert jobs.get_publication('tenant-1', initial['job_id']) is None
    assert jobs.get_job('tenant-1', initial['job_id'])['state'] == 'simulating'
    assert jobs.list_attempt_outcomes('tenant-1', initial['job_id']) == []
    block.unlink()
    with jobs.connect() as conn:
        conn.execute(sql.SQL("UPDATE {} SET lease_until=clock_timestamp()-interval '1 second' WHERE job_id=%s")
                     .format(jobs._table('jobs')), (initial['job_id'],))
    with process_consumer(directory) as (second, events, errors):
        wait_for(lambda: jobs.get_job('tenant-1', initial['job_id'])['state']=='succeeded', second)
    assert second.returncode == 0 and errors == [''] and result_count(results) == 1
    assert [row['state'] for row in jobs.list_attempt_outcomes('tenant-1', initial['job_id'])] == ['lease_expired', 'succeeded']
    assert jobs.get_publication('tenant-1', initial['job_id']) is not None
    assert [(event['job_id'], event['attempt']) for event in events if event['event']=='attempt'] == [(str(initial['job_id']), 2)]


@pytest.mark.parametrize('login_scope', [{**PROFILE, 'break_even_calculation': True}], indirect=True)
def test_scram_automatic_break_even_calculation_and_verification(plan_api, tmp_path):
    from app.break_even_verification import BreakEvenVerificationService
    from app.break_even_verified_result import BreakEvenVerifiedResultService
    from break_even_maximum_full_smoke import _operator_configuration
    app, service, body, principal = plan_api
    status, accepted = plan_post(app, body)
    assert status == 202
    directory = _operator_configuration(service, principal, tmp_path)
    factory = directory/'loop_operator.py'
    factory.write_text('''from maximum_operator import calculation as calculate, verification as verify
from app.deterministic_work import DeterministicWorkerLoop
def calculation():
    return DeterministicWorkerLoop(calculate(), input_versions=frozenset({'break-even-calculation-input-v1'}))
def verification():
    return DeterministicWorkerLoop(verify(), input_versions=frozenset({'break-even-verification-input-v1'}))
'''); factory.chmod(0o600)
    parent = accepted['intent_job']['job_id']
    with process_consumer(directory, 'loop_operator:calculation') as (process, events, errors):
        wait_for(lambda: service.jobs.get_job('tenant-1', parent)['state']=='succeeded', process)
    assert process.returncode == 0 and errors == [''] and events[1]['job_id'] == parent
    child = BreakEvenVerificationService(service.jobs, service.store).submit('tenant-1', parent)
    identity = str(child.job_id)
    with process_consumer(directory, 'loop_operator:verification') as (process, events, errors):
        wait_for(lambda: service.jobs.get_job('tenant-1', identity)['state']=='succeeded', process)
    assert process.returncode == 0 and errors == [''] and events[1]['job_id'] == identity
    result = BreakEvenVerifiedResultService(service.jobs, service.store).read_job_result('tenant-1', child.job_id)
    assert result.plan_id == accepted['plan_id'] and len(result.trials) == 2 and result.assessment_status == 'hold'
