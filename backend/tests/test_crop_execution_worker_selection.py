"""Explicit selection boundaries and independent consumption of a mixed queue."""
from hashlib import sha256
import json
import os
from pathlib import Path
from threading import Event
from types import SimpleNamespace

import pytest

from app.crop_execution_worker_selection import select_crop_execution_loop
from app.deterministic_work import DeterministicWorkerLoop, LoopHold
from app.crop_climate_joint_execution_worker import JointExecutionWorker
from app.crop_greenhouse_ventilation_execution_worker import VentilationExecutionWorker
from app.job_store import JobStore
from app.runtime_roles import RuntimeLoginPolicy
from test_crop_greenhouse_ventilation_result_store import (
    authoring, farm_setup, profiles, login_database, original_login_scope, login_scope)
from test_api_crop_greenhouse_ventilation_replay import database_cleanup
import test_crop_climate_joint_execution_worker as joint
import test_crop_greenhouse_ventilation_execution_worker as ventilation
import test_joint_deterministic_work as consumer
from test_crop_greenhouse_ventilation_execution_runtime import ventilation_factory

MODELS = ('crop-climate-joint', 'crop-greenhouse-ventilation')
VERSIONS = ('joint-crop-climate-execution-input-v1', 'joint-ventilation-execution-input-v1')


@pytest.fixture(params=[0, 1])
def isolated(request, monkeypatch, tmp_path):
    index = request.param
    policy = RuntimeLoginPolicy('test_jobs', 'test_owner', 'test_runtime', 'postgres')
    jobs = JobStore('dbname=postgres', policy.schema, tmp_path/'unused',
        runtime_identity=(policy, 'authority'), audit_runtime_grants=True,
        principal_provider=lambda: {'authenticated':True, 'tenant_id':'tenant-a',
                                   'scopes':{'metadata', 'simulation_execute'}})
    worker = object.__new__((JointExecutionWorker, VentilationExecutionWorker)[index])
    worker.jobs, worker.tenant_id = jobs, 'tenant-a'
    monkeypatch.setattr(worker, '_binding', lambda: None)
    loop = DeterministicWorkerLoop(worker, input_versions=frozenset({VERSIONS[index]}))
    calls = []
    def selected(): calls.append(index); return loop
    def other(): pytest.fail('selection called the other model factory')
    factories = dict(zip(('joint_factory', 'ventilation_factory'),
                         (selected, other) if index == 0 else (other, selected)))
    return SimpleNamespace(index=index, loop=loop, worker=worker, factories=factories, calls=calls)


def test_explicit_model_returns_same_bound_loop_without_running(isolated, monkeypatch):
    monkeypatch.setattr(isolated.loop, 'run', lambda *_: pytest.fail('selection started work'))
    monkeypatch.setattr(isolated.loop.discovery, 'page', lambda **_: pytest.fail('selection queried jobs'))
    assert select_crop_execution_loop(MODELS[isolated.index], **isolated.factories) is isolated.loop
    assert isolated.calls == [isolated.index]


def test_default_disabled_calls_neither_factory():
    def forbidden(): pytest.fail('disabled factory was called')
    assert select_crop_execution_loop(joint_factory=forbidden, ventilation_factory=forbidden) is None


@pytest.mark.parametrize('model', ['', 'joint', 'ventilation', True, 1, [], {}, 'crop-climate-joint '])
def test_unknown_model_fails_before_factory(model):
    def forbidden(): pytest.fail('unknown model called a factory')
    with pytest.raises(LoopHold, match='^crop_worker_selection_rejected$'):
        select_crop_execution_loop(model, joint_factory=forbidden, ventilation_factory=forbidden)


@pytest.mark.parametrize('model', MODELS)
def test_missing_selected_factory_is_rejected(model):
    with pytest.raises(LoopHold, match='^crop_worker_selection_rejected$'):
        select_crop_execution_loop(model)


@pytest.mark.parametrize('field', ['joint_factory', 'ventilation_factory'])
@pytest.mark.parametrize('value', [False, 1, 'factory', {}])
def test_non_callable_factory_is_rejected(field, value):
    with pytest.raises(LoopHold, match='^crop_worker_selection_rejected$'):
        select_crop_execution_loop(**{field:value})


@pytest.mark.parametrize('fault', ['object', 'other-model', 'input-version', 'jobs', 'poll', 'failure', 'exit'])
def test_selected_loop_type_versions_binding_and_errors_are_closed(isolated, fault, monkeypatch):
    if fault == 'input-version': isolated.loop.discovery.input_versions = frozenset({VERSIONS[1-isolated.index]})
    elif fault == 'jobs': isolated.worker.jobs = object()
    elif fault == 'poll': isolated.loop.poll_seconds += 1
    factory = isolated.factories['joint_factory' if isolated.index == 0 else 'ventilation_factory']
    if fault == 'object': factory = lambda: object()
    elif fault == 'other-model':
        isolated.loop.worker = object.__new__((VentilationExecutionWorker, JointExecutionWorker)[isolated.index])
    elif fault in ('failure', 'exit'):
        def failed(): raise (ValueError if fault == 'failure' else SystemExit)('private marker')
        factory = failed
    isolated.factories['joint_factory' if isolated.index == 0 else 'ventilation_factory'] = factory
    with pytest.raises(LoopHold, match='^crop_worker_selection_rejected$'):
        select_crop_execution_loop(MODELS[isolated.index], **isolated.factories)


def save(value):
    directory = os.environ.get('OSSF_JOINT_VENTILATION_RUNTIME_EVIDENCE')
    if directory:
        with (Path(directory)/'worker-selection.json').open('x') as stream:
            os.fchmod(stream.fileno(), 0o400); json.dump(value, stream, sort_keys=True)
            stream.flush(); os.fsync(stream.fileno())


def job_snapshot(reference, worker, job_id):
    value = {'job':worker.jobs.get_job('tenant-1', job_id)}
    for table in ('job_events', 'job_attempts', 'attempt_outcomes', 'job_publications'):
        value[table] = sorted(json.dumps(row, sort_keys=True, default=str)
            for row in reference.rows(worker, job_id, table))
    return {name:sha256(json.dumps(rows, sort_keys=True, default=str).encode()).hexdigest()
            for name, rows in value.items()}


@ventilation.pytestmark
def test_actual_independent_selected_consumers_and_current_rights(
        authoring, profiles, database_cleanup, tmp_path, monkeypatch, request):
    seeds = []
    for index, reference in enumerate((joint, ventilation)):
        directory = tmp_path/str(index); directory.mkdir(mode=0o700)
        producer = reference.producer.setup.__wrapped__(authoring, directory, profiles, request, monkeypatch)
        worker, job_id, raw, value = reference.setup.__wrapped__(producer)
        seeds.append(SimpleNamespace(reference=reference, worker=worker, job_id=job_id,
                                     raw=raw, value=value, directory=directory))
    assert seeds[0].worker.jobs is seeds[1].worker.jobs
    for seed in seeds: seed.value[4]['scopes'].discard('simulation_create')
    evidence = []
    for index, seed in enumerate(seeds):
        other = seeds[1-index]
        other_before = job_snapshot(other.reference, other.worker, other.job_id)
        directory = seed.directory/'consumer'; directory.mkdir(mode=0o700)
        factory_builder = consumer.joint_factory if index == 0 else ventilation_factory
        pack, factory = factory_builder(seed.worker, seed.value, directory)
        assert seed.job_id not in pack.read_text()+factory.read_text()
        source = factory.read_text().replace('def build():', 'def configured():', 1)
        chosen = 'joint_factory' if index == 0 else 'ventilation_factory'
        unused = 'ventilation_factory' if index == 0 else 'joint_factory'
        source += ('\ndef build():\n'
            ' from app.crop_execution_worker_selection import select_crop_execution_loop\n'
            ' def unselected(): raise AssertionError("unselected factory")\n'
            f' return select_crop_execution_loop({MODELS[index]!r}, {chosen}=configured, {unused}=unselected)\n')
        factory.write_text(source)
        with consumer.legacy.process_consumer(directory, 'joint_operator:build') as (process, events, errors):
            consumer.legacy.wait_for(lambda: (directory/'attempt-1.private.json').exists(), process, timeout=180)
            assert seed.worker.jobs.get_job('tenant-1', seed.job_id)['state'] == 'succeeded'
        assert process.returncode == 0 and errors == ['']
        assert [event['event'] for event in events] == ['started', 'attempt', 'stopped']
        assert events[1]['job_id'] == seed.job_id and events[1]['state'] == 'succeeded'
        proof = consumer.attempt_proof(directory, 1)
        assert proof['calls']['step'] == 16 and proof['calls']['start'] == 1
        other_after = job_snapshot(other.reference, other.worker, other.job_id)
        assert other_after == other_before
        if index == 0: assert other.worker.jobs.get_job('tenant-1', other.job_id)['state'] == 'queued'
        links = [row for row in seed.reference.rows(seed.worker, seed.job_id, 'job_events')
                 if row['kind'] == seed.reference.model.RESULT_EVENT_KIND]
        assert len(links) == 1
        record = seed.worker.results.get('tenant-1', links[0]['reason']['result_id'], seed.value[1]['farm'])
        progress = json.loads(seed.worker.server.inspect('tenant-1', seed.raw))
        assert json.loads(record['payload_raw'])['policies']['server_progress'] == progress
        assert progress['steps'] == 16 and progress['times']['last_confirmed']['at'] == '2026-10-01T00:00:32.123456Z'
        publications = seed.reference.rows(seed.worker, seed.job_id, 'job_publications')
        assert len(publications) == 1 and publications[0]['manifest'] == links[0]['reason']
        evidence.append({'model':MODELS[index], 'actual_SCRAM':proof['actual_scram'],
            'process_exit':process.returncode, 'step_calls':proof['calls']['step'],
            'other_job_and_history_unchanged':True, 'original_progress_UTC':True,
            'other_snapshot_before':other_before, 'other_snapshot_after':other_after,
            'payload_sha256':record['payload_sha256'], 'events':events})
    for index, seed in enumerate(seeds):
        seed.value[4]['scopes'].add('simulation_create')
        body = json.loads(seed.raw); body['revision'] = 'rights-withdrawn'
        raw = seed.reference.model.results._canonical(body)
        job = seed.worker.checkpoints.admission.submit('tenant-1', raw)
        seed.value[4]['scopes'].discard('simulation_create')
        selected = 'joint_factory' if index == 0 else 'ventilation_factory'
        stop, events = Event(), []
        def emit(value): events.append(value); stop.set()
        seed.value[-1].allowed = False
        try:
            with monkeypatch.context() as patch:
                calls = seed.reference.producer.reference.forbid(patch)
                loop = select_crop_execution_loop(MODELS[index], **{selected:lambda:
                    DeterministicWorkerLoop(seed.worker, input_versions=frozenset({VERSIONS[index]}))})
                loop.run(stop, emit=emit)
                assert not any(calls.values())
        finally: seed.value[-1].allowed = True
        assert len(events) == 1 and events[0]['state'] == 'queued'
        assert events[0]['reason_code'] == ('joint_execution_runtime_failure' if index == 0
                                           else 'ventilation_execution_runtime_failure')
        assert seed.reference.rows(seed.worker, str(job['job_id']), 'job_publications') == []
        assert not any(row['kind'] == seed.reference.model.RESULT_EVENT_KIND
            for row in seed.reference.rows(seed.worker, str(job['job_id']), 'job_events'))
        evidence[index]['current_rights_rejected_before_math_no_publication'] = True
        evidence[index]['rights_rejection_state'] = events[0]['state']
        evidence[index]['rights_rejection_reason'] = events[0]['reason_code']
        assert seed.worker.jobs.cancel('tenant-1', job['job_id'])
    save({'two_selected_independent_consumers':evidence, 'same_database':True,
          'sequential_consumers':True, 'unselected_factory_calls':0,
          'user_server_activated':False, 'G0_G4':'not_assessed'})
