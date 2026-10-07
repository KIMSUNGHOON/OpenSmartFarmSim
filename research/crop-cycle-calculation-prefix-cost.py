"""Measure registered synthetic calculations without changing product arithmetic."""
from contextlib import contextmanager
from copy import deepcopy
from datetime import datetime, timezone
from hashlib import sha256
import importlib.util
import json
import os
from pathlib import Path
import resource
from time import perf_counter

from app import crop_cycle_calculation_artifact as artifact
from app import crop_cycle_calculation_context as engine
from app import crop_cycle_calculation_server_custody as custody
from app.crop_cycle_calculation_farm_binding import CalculationFarmBinding
from app.crop_cycle_calculation_result_store import CalculationCycleCropResultStore
from app.crop_cycle_input_evidence import InputEvidenceAuthority

VERSION = 'crop-cycle-calculation-prefix-cost-v1'
_PROFILE_PATH = Path(__file__).with_name('crop-cycle-burden-profile.py')
_SPEC = importlib.util.spec_from_file_location('existing_crop_burden_costs', _PROFILE_PATH)
_PROFILE = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(_PROFILE)
Costs = _PROFILE.Costs


@contextmanager
def observation():
    targets = [(engine, 'open_calculation_context', 'input.context_factory'),
        (engine, 'advance_chunk', 'calculation.advance'),
        (engine, '_canonical', 'json.canonical'), (artifact, '_canonical', 'json.canonical'),
        (InputEvidenceAuthority, 'verify', 'input.proof_verify'),
        (artifact._Files, '_load_prefix', 'artifact.prefix_verify'),
        (artifact, '_validate_delta', 'artifact.delta_qc'),
        (artifact.ArtifactWriter, 'advance', 'artifact.advance'),
        (artifact.ArtifactWriter, '_put', 'artifact.blob_write'),
        (custody._Journal, '__init__', 'journal.open'),
        (custody._Journal, '_progress', 'journal.progress'),
        (custody._Journal, '_selected', 'journal.selected_proof'),
        (custody, '_signed', 'journal.sign'), (custody, '_usage', 'journal.file_usage'),
        (CalculationFarmBinding, 'prepare', 'farm.prepare'),
        (CalculationFarmBinding, 'current', 'farm.current_rights'),
        (CalculationFarmBinding, '_input', 'farm.input_validate'),
        (CalculationFarmBinding, '_registration', 'farm.registration_validate'),
        (CalculationCycleCropResultStore, 'put', 'db.put'),
        (CalculationCycleCropResultStore, '_find', 'db.lookup')]
    costs = Costs()
    with costs.observe(targets):
        yield costs


def _limits(budget, max_advances, wall_budget_seconds):
    _PROFILE._budgets([budget], transitions=128)
    if type(max_advances) is not int or not 1 <= max_advances <= 32:
        raise ValueError('one to thirty-two actual advances required')
    if type(wall_budget_seconds) is not int or not 1 <= wall_budget_seconds <= 1200:
        raise ValueError('one to 1200 seconds observation budget required')


def _checkpoint(server, tenant, raw):
    with server._open(tenant, raw, False) as journal:
        return journal.inspect(), deepcopy(journal.writer._checkpoint)


def _difference(after, before):
    return {name: {key: value-before.get(name, {}).get(key, 0)
        for key, value in metric.items()} for name, metric in after.items()
        if metric['calls'] != before.get(name, {}).get('calls', 0)}


def profile_registered_prefix(server, raw, *, tenant, budget, max_advances=32,
                              wall_budget_seconds=1200, on_advance=None):
    _limits(budget, max_advances, wall_budget_seconds)
    if on_advance is not None and not callable(on_advance):
        raise ValueError('observation sink must be callable')
    if type(server) is not custody.CalculationServerCustody:
        raise ValueError('actual registered calculation service required')
    request = server.binding._request(raw)
    where = server.directory / custody._intent_id(tenant, request)
    if os.path.lexists(where):
        raise ValueError('measurement requires an unused execution intent')
    descriptors = len(os.listdir('/proc/self/fd')); started = perf_counter(); curve = []
    with observation() as costs:
        for _ in range(max_advances):
            if curve and perf_counter()-started >= wall_budget_seconds:
                break
            before = deepcopy(costs.values); tick = perf_counter()
            with costs.measure('server.advance'):
                progress = server.advance(tenant, raw, budget=budget)
            value = json.loads(progress)
            curve.append({key: deepcopy(value[key]) for key in
                ('status', 'steps', 'planned_steps', 'commit_count', 'counts', 'storage_bytes', 'file_count')})
            curve[-1].update(wall_seconds=perf_counter()-tick,
                costs=_difference(costs.values, before), progress_sha256=sha256(progress).hexdigest())
            if on_advance is not None:
                on_advance(deepcopy(curve[-1]))
            if value['status'] != 'yielded':
                break
        rhs_before = costs.values.get('rhs', {}).get('calls', 0)
        with costs.measure('diagnostic.saved_checkpoint'):
            saved_progress, checkpoint = _checkpoint(server, tenant, raw)
        fresh = custody.CalculationServerCustody(server.binding, server.directory,
            input_resolver=server.input_resolver, integrity_key=server.integrity_key)
        with costs.measure('diagnostic.fresh_service_checkpoint'):
            reopened_progress, reopened_checkpoint = _checkpoint(fresh, tenant, raw)
        if progress != saved_progress or progress != reopened_progress or checkpoint != reopened_checkpoint:
            raise AssertionError('current saved prefix changed across service reconstruction')
        read_rhs = costs.values.get('rhs', {}).get('calls', 0)-rhs_before
        if read_rhs:
            raise AssertionError('prefix reopen evaluated crop equations')
    stop = ('terminal' if value['status'] != 'yielded' else
        'advance_limit' if len(curve) == max_advances else 'wall_budget')
    return {'measurement_version': VERSION, 'recorded_at_utc': datetime.now(timezone.utc).isoformat(),
        'measurement_code_sha256': sha256(Path(__file__).read_bytes()).hexdigest(),
        'reused_costs_code_sha256': sha256(_PROFILE_PATH.read_bytes()).hexdigest(),
        'scope': 'owned_synthetic_registered_prefix_cost_only', 'full166day_accepted': False,
        'budget': dict(budget), 'max_advances': max_advances, 'wall_budget_seconds': wall_budget_seconds,
        'last_progress': value, 'growth_curve': curve, 'stop_reason': stop,
        'checkpoint': checkpoint, 'fresh_service_checkpoint_exact': True, 'read_rhs_calls': read_rhs,
        'costs': costs.values, 'wall_seconds': perf_counter()-started,
        'descriptors_before': descriptors, 'descriptors_after': len(os.listdir('/proc/self/fd')),
        'process_peak_rss_bytes': resource.getrusage(resource.RUSAGE_SELF).ru_maxrss*1024,
        'effective_nice': os.getpriority(os.PRIO_PROCESS, 0),
        'measurement_scope': 'serial_process_lifetime_RSS_and_wrapper_overhead_inclusive_costs_not_additive'}


def profile_publication(store, raw, *, tenant):
    if type(store) is not CalculationCycleCropResultStore:
        raise ValueError('actual calculation result store required')
    request = store.server.binding._request(raw)
    descriptors = len(os.listdir('/proc/self/fd')); started = perf_counter()
    with observation() as costs:
        record = store.put(tenant, raw)
        if store.put(tenant, raw) != record or store.get(tenant, record['result_id'], request['farm']) != record:
            raise AssertionError('publication retry or current read changed stored record')
        with costs.measure('db.summary'):
            summary = store.summary(tenant, record['result_id'], request['farm'])
        hashes = {}; counts = {}
        for kind, limit in (('samples', 64), ('events', 8)):
            digest = sha256(); offset = count = 0
            while True:
                with costs.measure('db.page'):
                    page = store.page(tenant, record['result_id'], request['farm'], kind, offset, limit)
                for row in page['records']:
                    digest.update(engine._canonical(row)+b'\n')
                count += len(page['records'])
                if page['next'] == page['total']:
                    break
                if page['next'] <= offset:
                    raise AssertionError('stored page failed to advance')
                offset = page['next']
            hashes[kind] = digest.hexdigest(); counts[kind] = count
        rhs = costs.values.get('rhs', {}).get('calls', 0)
        if rhs:
            raise AssertionError('publication or current read evaluated crop equations')
    return {'result_id': record['result_id'], 'payload_sha256': record['payload_sha256'],
        'status': summary['status'], 'steps': summary['steps'], 'checkpoint': summary['checkpoint'],
        'hold': summary.get('hold'), 'last_confirmed': summary.get('last_confirmed'),
        'row_sha256': hashes, 'counts': counts, 'put_retry_read_rhs_calls': rhs,
        'same_retry_and_get_record': True, 'costs': costs.values, 'wall_seconds': perf_counter()-started,
        'descriptors_before': descriptors, 'descriptors_after': len(os.listdir('/proc/self/fd'))}
