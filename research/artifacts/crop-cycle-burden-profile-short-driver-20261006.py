"""Observe existing crop execution costs without replacing its equations."""
from contextlib import contextmanager, ExitStack
from copy import deepcopy
from datetime import datetime, timezone
from functools import wraps
from hashlib import sha256
import os
from pathlib import Path
import platform
import resource
from time import perf_counter, process_time

from app import crop_cycle_input_stream as inputs
from app import crop_cycle_stream_execution as engine
from app import crop_cycle_artifact as artifact

VERSION = 'crop-cycle-burden-profile-v1'


def _metadata():
    return {'measurement_version':VERSION, 'recorded_at_utc':datetime.now(timezone.utc).isoformat(),
        'measurement_code_sha256':sha256(Path(__file__).read_bytes()).hexdigest(),
        'python_version':platform.python_version(), 'effective_nice':os.getpriority(os.PRIO_PROCESS, 0)}


class Costs:
    def __init__(self):
        self.values = {}
        self.stack = []

    @contextmanager
    def measure(self, name):
        item = {'wall':perf_counter(), 'cpu':process_time(), 'children_wall':0.0, 'children_cpu':0.0}
        self.stack.append(item)
        try:
            yield
        finally:
            wall, cpu = perf_counter()-item['wall'], process_time()-item['cpu']
            self.stack.pop()
            value = self.values.setdefault(name, {'calls':0, 'wall_seconds':0.0, 'cpu_seconds':0.0,
                'exclusive_wall_seconds':0.0, 'exclusive_cpu_seconds':0.0})
            value['calls'] += 1; value['wall_seconds'] += wall; value['cpu_seconds'] += cpu
            value['exclusive_wall_seconds'] += max(0.0, wall-item['children_wall'])
            value['exclusive_cpu_seconds'] += max(0.0, cpu-item['children_cpu'])
            if self.stack:
                self.stack[-1]['children_wall'] += wall
                self.stack[-1]['children_cpu'] += cpu

    def wrap(self, function, name):
        @wraps(function)
        def measured(*args, **kwargs):
            with self.measure(name):
                return function(*args, **kwargs)
        return measured

    @contextmanager
    def observe(self, extra=()):
        targets = [(engine.short._Evaluator, 'rhs', 'rhs')]
        targets.extend((module, '_canonical', 'json.canonical') for module in
            (engine, engine.short, engine.physical, engine.physical.legacy)
            if hasattr(module, '_canonical'))
        with ExitStack() as undo:
            seen = set()
            for owner, attribute, name in [*targets, *extra]:
                identity = (id(owner), attribute)
                if identity in seen:raise ValueError('duplicate observation target')
                seen.add(identity); original = getattr(owner, attribute)
                undo.callback(setattr, owner, attribute, original)
                setattr(owner, attribute, self.wrap(original, name))
            yield self


def _budgets(values, *, transitions=10000):
    if type(values) is not list or not values or len(values) > 8:
        raise ValueError('one to eight explicit measurement budgets required')
    for budget in values:
        if (type(budget) is not dict or set(budget) != {'max_steps','max_transitions'}
            or type(budget['max_steps']) is not int or not 1 <= budget['max_steps'] <= 10000
            or type(budget['max_transitions']) is not int or not 1 <= budget['max_transitions'] <= transitions):
            raise ValueError('bounded integer measurement budgets required')


def _semantics(result):
    checkpoint = result['checkpoint']
    return {key:value for key,value in checkpoint.items()
            if key not in {'checkpoint_sha256','parent_sha256'}} if checkpoint else None


def _pure(context, budget, *, observed):
    costs = Costs(); checkpoint = engine.start(context)
    samples, events = sha256(), sha256(); sample_count = event_count = chunks = restores = 0
    started = perf_counter()
    with ExitStack() as stack:
        if observed:stack.enter_context(costs.observe())
        while True:
            if chunks == 16384:raise ValueError('measurement chunk limit exhausted; incomplete')
            with costs.measure('pure.advance'):
                result = engine.advance_chunk(context, checkpoint, budget)
            chunks += 1
            for key,digest in (('samples',samples), ('events',events)):
                for row in result[key]:digest.update(engine._canonical(row)+b'\n')
            sample_count += len(result['samples']); event_count += len(result['events'])
            if result['status'] != 'yielded':break
            if observed:
                with costs.measure('checkpoint.serialize'):
                    raw = engine.checkpoint_bytes(context, result['checkpoint'])
                with costs.measure('checkpoint.restore'):
                    checkpoint = engine.restore_checkpoint(context, raw)
                restores += 1
            else:checkpoint = result['checkpoint']
    semantic = _semantics(result)
    fingerprint = {'status':result['status'], 'steps':result['steps'], 'planned_steps':result['planned_steps'],
        'checkpoint':semantic, 'hold':result.get('hold'), 'last_confirmed':result.get('last_confirmed'),
        'samples_sha256':samples.hexdigest(), 'events_sha256':events.hexdigest()}
    return {'budget':dict(budget), 'instrumented':observed, 'status':result['status'], 'steps':result['steps'],
        'hold':result.get('hold'), 'last_confirmed':result.get('last_confirmed'),
        'sample_count':sample_count, 'event_count':event_count, 'samples_sha256':samples.hexdigest(),
        'events_sha256':events.hexdigest(), 'semantic_checkpoint':semantic,
        'semantic_sha256':sha256(engine._canonical(fingerprint)).hexdigest(),
        'chunks':chunks, 'checkpoint_restores':restores, 'wall_seconds':perf_counter()-started,
        'costs':costs.values}


def profile_pure(directory, program, *, budgets, profiles):
    _budgets(budgets)
    descriptors = len(os.listdir('/proc/self/fd'))
    directory = Path(directory); directory.mkdir(mode=0o700)
    data = deepcopy(program); anchors = data.pop('output_times')
    packet = inputs.write_input_packet(directory/'input', **data, anchors=anchors, outputs=anchors,
        **profiles, program_id='own-cycle-burden-profile-v1')
    with inputs.open_input_packet(directory/'input', packet['root_sha256'], **profiles) as reader:
        context = engine.prepare_context(reader, **profiles)
        runs = [_pure(context, budget, observed=index>0) for index,budget in enumerate(budgets)]
        report = {**_metadata(), 'scope':'own_synthetic_cost_measurement_only', 'full166day_accepted':False,
            'input_root_sha256':packet['root_sha256'], 'planned_steps':context.planned_steps,
            'manifest':context.manifest, 'runs':runs}
    report.update(descriptors_before=descriptors, descriptors_after=len(os.listdir('/proc/self/fd')),
        process_peak_rss_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss*1024,
        measurement_scope='serial_current_process_with_wrapper_overhead_inclusive_costs_not_additive')
    if len({r['semantic_sha256'] for r in runs}) != 1:
        raise AssertionError('observation or quota changed original execution semantics')
    return report


def _artifact(context, directory, budget, notice_raw):
    costs = Costs(); chunks = []; reopens = 0; writer = None
    targets = [(artifact, '_canonical', 'json.canonical'),
        (artifact, 'open_writer', 'artifact.reopen'),
        (artifact._Files, '_load_prefix', 'artifact.verify'),
        (artifact.ArtifactWriter, 'advance', 'artifact.append'),
        (artifact.ArtifactWriter, '_put', 'artifact.blob.write'),
        (artifact.ArtifactWriter, '_usage', 'artifact.file_usage')]
    started = perf_counter()
    with costs.observe(targets):
        try:
            writer = artifact.create_writer(directory, context, notice_raw=notice_raw)
            while True:
                if len(chunks) == artifact.LIMITS['commits']:
                    raise ValueError('measurement commit limit exhausted; incomplete')
                tick = perf_counter(); progress = writer.advance(budget)
                elapsed = perf_counter()-tick
                size, files = writer._usage()
                chunks.append({'commit_count':progress['commit_count'], 'steps':progress['steps'],
                    'advance_wall_seconds':elapsed, 'storage_bytes':size, 'file_count':files})
                if progress['status'] != 'yielded':
                    receipt = writer.finalize()
                    checkpoint = deepcopy(writer._checkpoint)
                    size, files = writer._usage()
                    break
                writer.close()
                writer = artifact.open_writer(directory, progress['head_sha256'], context, notice_raw=notice_raw)
                reopens += 1
        finally:
            if writer is not None:writer.close()
        before_rhs = costs.values.get('rhs', {}).get('calls', 0)
        hashes = {}; counts = {}; max_bytes = 0
        with artifact.open_artifact(directory, receipt['artifact_sha256'], context, notice_raw=notice_raw) as reader:
            summary = reader.summary
            for kind,limit in (('samples',64), ('events',8)):
                digest = sha256(); start = count = 0
                while True:
                    with costs.measure('artifact.page'):
                        page = reader.page(kind, start, limit)
                    max_bytes = max(max_bytes, len(artifact._canonical(page)))
                    for row in page['records']:digest.update(engine._canonical(row)+b'\n')
                    count += len(page['records'])
                    if page['next'] == page['total']:break
                    if page['next'] <= start:raise AssertionError('page did not advance')
                    start = page['next']
                hashes[kind] = digest.hexdigest(); counts[kind] = count
        read_rhs = costs.values.get('rhs', {}).get('calls', 0)-before_rhs
    semantic = _semantics({'checkpoint':checkpoint})
    fingerprint = {'status':summary['status'], 'steps':summary['steps'], 'planned_steps':summary['planned_steps'],
        'checkpoint':semantic, 'hold':summary.get('hold'), 'last_confirmed':summary.get('last_confirmed'),
        'samples_sha256':hashes['samples'], 'events_sha256':hashes['events']}
    return {'budget':dict(budget), 'instrumented':True, 'status':summary['status'], 'steps':summary['steps'],
        'hold':summary.get('hold'), 'last_confirmed':summary.get('last_confirmed'),
        'semantic_sha256':sha256(engine._canonical(fingerprint)).hexdigest(), 'semantic_checkpoint':semantic,
        'sample_count':counts['samples'], 'event_count':counts['events'],
        'samples_sha256':hashes['samples'], 'events_sha256':hashes['events'],
        'artifact_sha256':receipt['artifact_sha256'], 'commit_count':receipt['commit_count'],
        'writer_reopens':reopens, 'growth_curve':chunks, 'storage_bytes':size, 'file_count':files,
        'read_rhs_calls':read_rhs, 'max_page_bytes':max_bytes, 'wall_seconds':perf_counter()-started,
        'costs':costs.values}


def profile_artifact(directory, program, *, budgets, profiles, notice_raw):
    _budgets(budgets, transitions=128)
    descriptors = len(os.listdir('/proc/self/fd'))
    directory = Path(directory); directory.mkdir(mode=0o700)
    data = deepcopy(program); anchors = data.pop('output_times')
    packet = inputs.write_input_packet(directory/'input', **data, anchors=anchors, outputs=anchors,
        **profiles, program_id='own-cycle-burden-profile-v1')
    with inputs.open_input_packet(directory/'input', packet['root_sha256'], **profiles) as reader:
        context = engine.prepare_context(reader, **profiles)
        runs = [_artifact(context, directory/str(index), budget, notice_raw) for index,budget in enumerate(budgets)]
        report = {**_metadata(), 'scope':'own_synthetic_cost_measurement_only', 'full166day_accepted':False,
            'input_root_sha256':packet['root_sha256'], 'planned_steps':context.planned_steps,
            'manifest':context.manifest, 'runs':runs}
    report.update(descriptors_before=descriptors, descriptors_after=len(os.listdir('/proc/self/fd')),
        process_peak_rss_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss*1024,
        measurement_scope='serial_current_process_with_wrapper_overhead_inclusive_costs_not_additive')
    if any(r['read_rhs_calls'] for r in runs):raise AssertionError('artifact read executed RHS')
    if len({r['semantic_sha256'] for r in runs}) != 1:
        raise AssertionError('artifact quota changed original execution semantics')
    return report
