"""Observe existing crop execution costs without replacing its equations."""
from contextlib import contextmanager, ExitStack
from copy import deepcopy
from datetime import datetime, timedelta, timezone
from functools import wraps
from hashlib import sha256
import os
import multiprocessing
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


def profile_shape(directory, program, *, intervals, interval_seconds, profiles):
    if (type(intervals) is not int or not 1 <= intervals < inputs.MAX_RECORDS
        or type(interval_seconds) is not int or not 1 <= interval_seconds <= 3600):
        raise ValueError('bounded explicit own shape required')
    descriptors = len(os.listdir('/proc/self/fd')); costs = Costs()
    original = deepcopy(program); template = original['segments'][0]
    start = engine.physical._utc(template['start'])
    end = start+timedelta(seconds=intervals*interval_seconds)
    events = [e for e in original['events'] if start <= engine.physical._utc(e['at']) <= end]
    solver = deepcopy(original['solver']); h = solver['max_step_seconds']
    solver['max_steps'] = intervals*((interval_seconds+h-1)//h)+len(events)
    def segments():
        for index in range(intervals):
            segment = deepcopy(template)
            segment['start'] = engine.physical._stamp(start+timedelta(seconds=index*interval_seconds))
            segment['end'] = engine.physical._stamp(start+timedelta(seconds=(index+1)*interval_seconds))
            yield segment
    def anchors():
        for index in range(intervals+1):
            yield engine.physical._stamp(start+timedelta(seconds=index*interval_seconds))
    with costs.observe():
        with costs.measure('input.write_and_preflight'):
            packet = inputs.write_input_packet(directory, initial_state=original['initial_state'],
                segments=segments(), events=iter(events), anchors=anchors(), outputs=anchors(), solver=solver,
                **profiles, program_id='own-uniform-cycle-shape-cost-v1')
        with costs.measure('input.open_and_preflight'):
            reader = inputs.open_input_packet(directory, packet['root_sha256'], **profiles)
        with reader:
            with costs.measure('input.prepare_context'):
                context = engine.prepare_context(reader, **profiles)
            result = {**_metadata(), 'scope':'own_uniform_input_shape_plan_only',
                'full166day_accepted':False, 'actual_rhs_steps':0,
                'source_program_sha256':sha256(engine._canonical(original)).hexdigest(),
                'intervals':intervals, 'interval_seconds':interval_seconds,
                'retained_declared_events':len(events), 'input_root_sha256':packet['root_sha256'],
                'packet_bytes':packet['packet_bytes'], 'plan':reader.plan,
                'index_pages':len(context.index), 'manifest':context.manifest}
    result.update(costs=costs.values, rhs_calls=costs.values.get('rhs',{}).get('calls',0),
        descriptors_before=descriptors, descriptors_after=len(os.listdir('/proc/self/fd')),
        process_peak_rss_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss*1024)
    return result


def _native_targets(server):
    from app import crop_cycle_server_custody as custody
    from app import crop_cycle_result_store as storage
    from app import api_crop_cycle_replay as public
    return [(artifact, '_canonical', 'json.canonical'),
        (engine, 'prepare_context', 'input.prepare_context'),
        (inputs.InputPacket, '_preflight', 'input.preflight'),
        (artifact, 'open_writer', 'artifact.reopen'),
        (artifact._Files, '_load_prefix', 'artifact.verify'),
        (artifact.ArtifactWriter, 'advance', 'artifact.append'),
        (artifact.ArtifactWriter, '_put', 'artifact.blob.write'),
        (custody, '_usage', 'custody.file_usage'),
        (type(server.binding), 'prepare', 'farm.prepare'),
        (type(server.binding), 'current', 'farm.current_rights'),
        (type(server.binding), '_input', 'farm.input_validate'),
        (type(server.binding), '_registration', 'farm.registration_validate'),
        (storage.CycleCropResultStore, 'put', 'db.put'),
        (storage.CycleCropResultStore, '_find', 'db.lookup'),
        (public, '_read_cycle_response', 'public.response'),
        (public, 'project_cycle_result', 'public.projection'),
        (public, '_public_bytes', 'public.bytes')]


def _native_checkpoint(server, tenant, raw):
    with server._open(tenant, raw, False) as journal:
        return deepcopy(journal.writer._checkpoint)


def _native_worker(server, tenant, raw, budget, send, unused):
    unused.close(); descriptors = len(os.listdir('/proc/self/fd'))
    try:
        from app import crop_cycle_server_custody as custody
        fresh = custody.CycleServerCustody(server.binding, server.directory,
            input_resolver=server.input_resolver, integrity_key=server.integrity_key)
        costs = Costs(); growth = []
        with costs.observe(_native_targets(fresh)):
            with costs.measure('diagnostic.checkpoint_open'):
                restored = _native_checkpoint(fresh, tenant, raw)
            while True:
                if len(growth) == artifact.LIMITS['commits']:
                    raise ValueError('worker measurement exhausted; incomplete')
                tick = perf_counter()
                progress = fresh.advance(tenant, raw, budget=budget)
                value = __import__('json').loads(progress)
                growth.append({'steps':value['steps'], 'commit_count':value['commit_count'],
                    'storage_bytes':value['storage_bytes'], 'file_count':value['file_count'],
                    'advance_wall_seconds':perf_counter()-tick})
                if value['status'] != 'yielded':break
            with costs.measure('diagnostic.checkpoint_open'):
                terminal = _native_checkpoint(fresh, tenant, raw)
        response = {'restored_checkpoint':restored, 'terminal_checkpoint':terminal,
            'progress':value, 'growth_curve':growth, 'costs':costs.values,
            'descriptors_before':descriptors, 'descriptors_after':len(os.listdir('/proc/self/fd')),
            'process_peak_rss_bytes':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss*1024}
        send.send(response)
    except Exception as exc:
        send.send({'error_type':type(exc).__name__})
    finally:send.close()


def profile_native(server, raw, *, tenant, first_budget, resume_budget, db_key, worker_timeout,
                   input_rights, principal):
    import json
    from app import crop_cycle_result_store as storage
    from app import crop_cycle_server_custody as custody
    from app import api_crop_cycle_replay as public
    _budgets([first_budget,resume_budget], transitions=128)
    if type(worker_timeout) is not int or not 1 <= worker_timeout <= 900:
        raise ValueError('bounded worker observation timeout required')
    if input_rights is not server.binding.input_rights or input_rights.allowed is not True:
        raise ValueError('explicit own synthetic rights provider required')
    descriptors = len(os.listdir('/proc/self/fd')); started = perf_counter()
    request = json.loads(raw); profiles = server.binding._profiles()
    with server.input_resolver(request['input']['root_sha256'], **profiles) as reader:
        context = engine.prepare_context(reader, **profiles)
        baseline = _pure(context, {'max_steps':10000,'max_transitions':10000}, observed=False)
    costs = Costs()
    with costs.observe(_native_targets(server)):
        with costs.measure('server.initial_advance'):
            initial = json.loads(server.advance(tenant, raw, budget=first_budget))
        if initial['status'] != 'yielded':raise AssertionError('worker requires actual yielded state')
        with costs.measure('diagnostic.checkpoint_open'):
            checkpoint = _native_checkpoint(server, tenant, raw)
    process = multiprocessing.get_context('fork'); receive, send = process.Pipe(duplex=False)
    child = process.Process(target=_native_worker, args=(server,tenant,raw,resume_budget,send,receive))
    try:
        child.start(); send.close()
        if not receive.poll(worker_timeout):raise TimeoutError('native measurement worker incomplete')
        worker = receive.recv(); child.join(5)
        if child.is_alive() or child.exitcode != 0 or 'error_type' in worker:
            raise AssertionError('native measurement worker failed')
        exit_code = child.exitcode
    finally:
        if child.is_alive():child.kill();child.join(5)
        receive.close(); send.close(); child.close()
    if checkpoint != worker['restored_checkpoint']:
        raise AssertionError('actual worker changed saved checkpoint')
    semantic = _semantics({'checkpoint':worker['terminal_checkpoint']})
    if semantic != baseline['semantic_checkpoint']:
        raise AssertionError('native execution changed state, seed, UTC, clock, counters or prefixes')
    pages = []; hashes = {}; public_hashes = {}; counts = {}
    with costs.observe(_native_targets(server)):
        rhs_before = costs.values.get('rhs',{}).get('calls',0)
        store = storage.CycleCropResultStore(server, integrity_key=db_key)
        record = store.put(tenant, raw); farm = request['farm']
        with store.jobs.connect() as connection:
            actual_scram = bool(connection.pgconn.used_password
                and connection.info.get_parameters()['require_auth'] == 'scram-sha-256')
        for kind,limit in (('samples',64),('events',8)):
            digest = sha256(); projected_digest = sha256(); offset = count = 0
            while True:
                with costs.measure('server.raw_page'):
                    page = store.page(tenant, record['result_id'], farm, kind, offset, limit)
                for row in page['records']:
                    digest.update(engine._canonical(row)+b'\n')
                    projected = row if kind == 'samples' else {k:v for k,v in row.items() if k != 'input_id'}
                    projected_digest.update(engine._canonical(projected)+b'\n')
                count += len(page['records'])
                if page['next'] == page['total']:break
                if page['next'] <= offset:raise AssertionError('raw page did not advance')
                offset = page['next']
            hashes[kind] = digest.hexdigest(); public_hashes[kind] = projected_digest.hexdigest(); counts[kind] = count
            if hashes[kind] != baseline[kind+'_sha256']:raise AssertionError('saved original row mismatch')
        for kind,limit in (('summary',None),('samples',64),('events',8)):
            digest = sha256(); offset = count = 0
            while True:
                tick = perf_counter()
                response = public._read_cycle_response(store,tenant,record['result_id'],farm,kind,offset,limit)
                seconds = perf_counter()-tick; value = json.loads(response)
                pages.append({'kind':kind, 'offset':offset, 'bytes':len(response), 'wall_seconds':seconds,
                    'response_sha256':sha256(response).hexdigest()})
                if kind == 'summary':break
                page = value['page']
                for row in page['records']:digest.update(engine._canonical(row)+b'\n')
                count += len(page['records'])
                if page['next_offset'] is None:break
                if page['next_offset'] <= offset:raise AssertionError('public page did not advance')
                offset = page['next_offset']
            if kind != 'summary' and (digest.hexdigest() != public_hashes[kind] or count != counts[kind]):
                raise AssertionError('public original quantities/UTC changed')
        input_rights.allowed = False
        try:
            try:public._read_cycle_response(store,tenant,record['result_id'],farm,'summary',0,None)
            except custody.CycleCustodyHold:withdrawal_denied = True
            else:raise AssertionError('withdrawn input was displayed')
        finally:input_rights.allowed = True
        principal['scopes'].remove('crop_result_read')
        try:
            try:public._read_cycle_response(store,tenant,record['result_id'],farm,'summary',0,None)
            except PermissionError:principal_denied = True
            else:raise AssertionError('withdrawn principal was displayed')
        finally:principal['scopes'].add('crop_result_read')
        read_rhs = costs.values.get('rhs',{}).get('calls',0)-rhs_before
    if read_rhs:raise AssertionError('publication or read executed RHS')
    return {**_metadata(), 'scope':'own_registered_synthetic_worker_and_costs_only',
        'full166day_accepted':False, 'gates':'not_assessed', 'actual_scram':actual_scram,
        'transport_scope':'direct_actual_public_response_function_without_TLS',
        'input_root_sha256':request['input']['root_sha256'], 'baseline':baseline,
        'initial_progress':initial, 'terminal_progress':worker['progress'],
        'worker':worker, 'worker_exit_code':exit_code, 'worker_restore_exact':True,
        'final_semantics_equal':True, 'samples_sha256':hashes['samples'], 'events_sha256':hashes['events'],
        'public_all_original_rows_equal':True, 'public_pages':pages, 'parent_costs':costs.values,
        'put_and_read_rhs_calls':read_rhs, 'current_rights_withdrawal_denied':withdrawal_denied,
        'current_principal_withdrawal_denied':principal_denied,
        'descriptors_before':descriptors, 'descriptors_after':len(os.listdir('/proc/self/fd')),
        'process_peak_rss_bytes':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss*1024,
        'wall_seconds':perf_counter()-started}
