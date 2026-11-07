"""Bounded flat lineage for genuine successive material points and growth."""
from contextlib import contextmanager
from copy import deepcopy
from dataclasses import dataclass, field
from fractions import Fraction
from hashlib import sha256
import json
from pathlib import Path
import sys
from types import SimpleNamespace

from . import crop_supply_material_repeat_proof as proof

point = proof.point
original, base = point.original, point.base
q, x, raw, digest, need = point.q, point.x, point.raw, point.digest, point.need
FLAGS = dict(point.FLAGS)
VERSION = 'supply-material-repeat-owner-research-v1'
CODE_SHA256 = sha256(Path(__file__).read_bytes()).hexdigest()
LIMITS = {'positive_segments': 128, 'repeat_transitions': 256, 'committed_RHS_evaluations': 1024}
_TOKEN = object()
DEFINITION_FIELDS = {'schema_version', *FLAGS, 'model_version','code_sha256','point_code_sha256','proof_code_sha256',
    'dependency_code_sha256','source','forcing_definition_sha256','initial_binding_sha256','original_grid','stop_at','limits_policy','limits'}
BASIS_FIELDS = {'schema_version', *FLAGS, 'model_version','code_sha256','definition_sha256','previous_basis_sha256',
    'source_current_sha256','point_sha256','numeric_basis','origin_records'}
CURRENT_FIELDS = {'schema_version', *FLAGS, 'model_version','code_sha256','definition_sha256','effective_rights','numeric','at',
    'span_index','phase','integration_count','lifetime','output_cursor','output_prefix_sha256'}
CURSOR_FIELDS = {'schema_version', *FLAGS, 'model_version','code_sha256','definition_sha256','basis_sha256','current_sha256',
    'previous_cursor_sha256','history_page_sha256'}
PAGE_FIELDS = {'schema_version','kind','definition_sha256','previous_cursor_sha256','before_current_sha256','after_current_sha256',
    'before_basis_sha256','after_basis_sha256','evidence'}


@dataclass(frozen=True)
class CursorRef:
    sha256: str


@dataclass(frozen=True)
class Workspace:
    original_material_workspace: original.Workspace
    repeat_archive_directory: Path
    access: point.ContentAccess


@dataclass(frozen=True)
class Handle:
    cursor_sha256: str
    _current: bytes = field(repr=False)
    _basis: bytes = field(repr=False)
    _cursor: bytes = field(repr=False)
    _definition: str = field(repr=False)
    _workspace: Workspace = field(repr=False)
    _token: object = field(repr=False)

    @property
    def current(self):
        return json.loads(self._current)

    @property
    def basis(self):
        return json.loads(self._basis)


@dataclass(frozen=True)
class Outcome:
    status: str
    handle: Handle | None
    hold: str | None
    progress: dict
    emitted: list
    pending: dict | None = None
    historical_cursor_sha256: str | None = None
    authority_hold: str | None = None


def _workspace(workspace):
    need(type(workspace) is Workspace and type(workspace.original_material_workspace) is original.Workspace
         and workspace.access is workspace.original_material_workspace.access, 'STORAGE_HOLD: concrete repeat/original workspace required')
    old = workspace.original_material_workspace
    point._workspace_snapshot(old)
    root = old.forcing_workspace.source_workspace
    paths = [Path(p) for p in (root.source_directory, root.archive_directory, old.forcing_workspace.archive_directory,
                               old.archive_directory, workspace.repeat_archive_directory)]
    for path in paths:
        need(path.is_absolute() and '..' not in path.parts and path.resolve() == path,
             'STORAGE_HOLD: fixed nonsymlink absolute archive paths required')
    for i, left in enumerate(paths):
        for right in paths[i+1:]:
            need(left != right and left not in right.parents and right not in left.parents,
                 'STORAGE_HOLD: five separate nonnested archive families required')


def _snapshot(workspace):
    return (id(workspace), tuple(vars(workspace).items()), point._workspace_snapshot(workspace.original_material_workspace),
            point._directory(workspace.repeat_archive_directory))


@contextmanager
def _store(workspace, meter, close_fd=point._ACQUISITION_FIELDS[15]):
    meter.fence(); _workspace(workspace)
    store = point._open_store_v2(workspace.repeat_archive_directory, workspace.access, write=True, meter=meter)
    state = vars(store)
    try:
        meter.fence()
        yield store
        meter.fence()
    finally:
        fd = state['_fd']
        if fd is not None:
            close_fd(fd)
            state['_fd'] = None


def _get(s, reference, maximum=base.PAGE_MAX):
    s.meter.fence()
    result = base._get(s, reference, maximum)
    s.meter.fence()
    return result


def _check(s, canonical_reads=None):
    need(_snapshot(s.workspace) == s.workspace_snapshot, 'SOURCE_HOLD: repeat workspace/policy changed')
    if canonical_reads is None:
        original._check(s.original)
    else:
        point._source_recheck_v3(s.original, canonical_reads)
    need(raw(s.definition) == s.definition_raw and digest(s.definition) == s.definition_ref,
         'SOURCE_HOLD: repeat definition changed')
    for reference, expected in s.archive_witnesses.items():
        info = point.os.stat(reference, dir_fd=s.archive._fd, follow_symlinks=False)
        need(base._metadata(info) == expected, 'STORAGE_HOLD: immutable repeat blob metadata changed')
    s.archive._guard()
    s.archive._usage()


@contextmanager
def _held(store, original_session, workspace, meter, definition):
    s = SimpleNamespace(archive=store, archive_witnesses={}, workspace=workspace, original=original_session,
        origin=original_session.parent.origin, spans=original_session.spans, grid=original_session.grid,
        stop=original_session.stop, profiles=original_session.profiles, meter=meter,
        definition=definition, definition_ref=digest(definition), definition_raw=raw(definition), workspace_snapshot=_snapshot(workspace))
    previous = meter.check
    canonical_reads = point._canonical_reads(original_session)
    meter.check = lambda: _check(s, canonical_reads)
    try:
        meter.fence('source_validation')
        yield s
        meter.fence()
    finally:
        meter.check = previous


def _definition(old_session, old_handle):
    source = point._ref(old_session, old_handle.current, old_handle.cursor_sha256)
    return {**FLAGS, 'schema_version': 'supply-material-repeat-definition-v1', 'model_version': VERSION,
        'code_sha256': CODE_SHA256, 'point_code_sha256': point.CODE_SHA256, 'proof_code_sha256': proof.CODE_SHA256,
        'dependency_code_sha256': dict(point._DEPENDENCY_SHA), 'source': source,
        'forcing_definition_sha256': old_session.definition['source']['definition_sha256'],
        'initial_binding_sha256': old_session.parent.origin.manifest['initial_binding']['sha256'],
        'original_grid': {'time_origin_utc': old_handle.current['at']['time_origin_utc'], 'step_seconds_exact': q(old_session.grid, 's')},
        'stop_at': q(old_session.stop, 's'), 'limits_policy': 'bounded_repeat_material_lineage_v1', 'limits': dict(LIMITS)}


def _definition_head(d):
    base.reader._closed(d, DEFINITION_FIELDS)
    need(d['schema_version'] == 'supply-material-repeat-definition-v1' and d['model_version'] == VERSION
         and all(d[k] == v for k,v in FLAGS.items()) and d['code_sha256'] == CODE_SHA256
         and d['point_code_sha256'] == point.CODE_SHA256 and d['proof_code_sha256'] == proof.CODE_SHA256
         and d['dependency_code_sha256'] == point._DEPENDENCY_SHA and d['limits'] == LIMITS
         and d['limits_policy'] == 'bounded_repeat_material_lineage_v1', 'SCOPE_HOLD: exact repeat definition required')
    base.reader._closed(d['source'], {'owner_version','definition_sha256','cursor_sha256','current_sha256','basis_sha256'})
    need(d['source']['owner_version'] == original.VERSION, 'SOURCE_HOLD: original material bridge required')


@contextmanager
def _session(definition_ref, workspace, meter):
    with _store(workspace, meter) as store:
        temporary = SimpleNamespace(archive=store, archive_witnesses={})
        d = base._get(temporary, definition_ref)
        _definition_head(d)
        with point._material_source_session_v2(d['source']['definition_sha256'], workspace.original_material_workspace, meter) as old_session:
            old_session.origin = old_session.parent.origin
            cursor, current = original._restore(old_session, d['source']['cursor_sha256'])
            handle = original._handle(old_session, d['source']['cursor_sha256'], cursor, current)
            need(raw(_definition(old_session, handle)) == raw(d), 'SOURCE_HOLD: exact genuine bridge definition required')
            with _held(store, old_session, workspace, meter, d) as s:
                s.archive_witnesses.update(temporary.archive_witnesses)
                s.source_cursor, s.source_current = cursor, current
                yield s


def _limits(lifetime):
    base.reader._closed(lifetime, {'positive_segments','repeat_transitions','material_adoptions','forcing_switches','frames','committed_RHS_evaluations'})
    need(all(type(v) is int and v >= 0 for v in lifetime.values())
         and all(lifetime[k] <= maximum for k, maximum in LIMITS.items()), 'CAPACITY_HOLD: inherited lineage limit exhausted')


def _root(s):
    old_session = s.original; d = s.definition; current = deepcopy(s.source_current)
    intervals = switches = 0; selected = d['source']['cursor_sha256']; seen = set()
    while selected is not None:
        need(selected not in seen and len(seen) < 256, 'HISTORY_HOLD: bounded original material history required')
        seen.add(selected)
        cursor = base._get(old_session, selected, base.CURRENT_MAX)
        page = base._get(old_session, cursor['history_page_sha256'])
        intervals += int(page['kind'] == 'interval'); switches += int(page['kind'] == 'forcing_switch')
        selected = cursor['previous_cursor_sha256']
    need(intervals == current['integration_count'], 'HISTORY_HOLD: exact inherited segment count required')
    partial = int(x(old_session.point['at']['elapsed_seconds_exact'], 's') >
                  x(old_session.source_current['at']['elapsed_seconds_exact'], 's'))
    point_work = old_session.point['candidate_RHS_evaluations'] + old_session.point['point_stage_RHS_evaluations']
    lifetime = {'positive_segments': intervals+partial, 'repeat_transitions': 0, 'material_adoptions': 1,
        'forcing_switches': switches, 'frames': 2+intervals+switches, 'committed_RHS_evaluations': point_work+5*intervals+switches}
    _limits(lifetime)
    basis = {**FLAGS, 'schema_version': 'supply-material-repeat-basis-v1', 'model_version': VERSION, 'code_sha256': CODE_SHA256,
        'definition_sha256': s.definition_ref, 'previous_basis_sha256': None,
        'source_current_sha256': digest(current), 'point_sha256': old_session.definition['point_sha256'],
        'numeric_basis': deepcopy(old_session.math_basis), 'origin_records': deepcopy(old_session.origins)}
    current.update(schema_version='supply-material-repeat-current-v1', model_version=VERSION, code_sha256=CODE_SHA256,
        definition_sha256=s.definition_ref, phase='source_anchor', lifetime=lifetime)
    current['numeric'].update(schema_version='supply-material-repeat-numeric-v1', code_sha256=CODE_SHA256)
    return basis, current


def _activate(s, basis, point_value=None):
    base.reader._closed(basis, BASIS_FIELDS)
    need(basis['schema_version'] == 'supply-material-repeat-basis-v1' and basis['model_version'] == VERSION
         and basis['code_sha256'] == CODE_SHA256 and basis['definition_sha256'] == s.definition_ref
         and all(basis[k] == v for k,v in FLAGS.items()), 'BASIS_HOLD: exact repeat basis required')
    s.basis, s.math_basis = basis, basis['numeric_basis']
    s.point = s.original.point if point_value is None else point_value['point_data']
    point.kernel._profiles(s.math_basis, s.profiles)


def _numeric(s, state, totals, derived, steps, at, index):
    value = original._numeric(s, state, totals, derived, steps, at, index)
    value.update(schema_version='supply-material-repeat-numeric-v1', code_sha256=CODE_SHA256)
    return value


def _cursor(s, basis, current, previous=None, page=None):
    return {**FLAGS, 'schema_version': 'supply-material-repeat-cursor-v1', 'model_version': VERSION, 'code_sha256': CODE_SHA256,
        'definition_sha256': s.definition_ref, 'basis_sha256': digest(basis), 'current_sha256': digest(current),
        'previous_cursor_sha256': previous, 'history_page_sha256': page}


def _handle(s, reference, cursor, current):
    return Handle(reference, raw(current, base.CURRENT_MAX), raw(s.basis), raw(cursor, base.CURRENT_MAX), s.definition_ref, s.workspace, _TOKEN)


def _shape(s, current):
    base.reader._closed(current, CURRENT_FIELDS)
    need(current['schema_version'] == 'supply-material-repeat-current-v1' and current['model_version'] == VERSION
         and current['code_sha256'] == CODE_SHA256 and current['definition_sha256'] == s.definition_ref
         and all(current[k] == v for k,v in FLAGS.items()), 'STATE_HOLD: exact repeat current required')
    _limits(current['lifetime']); original.forcing._rights(current['effective_rights'])
    need(current['effective_rights']['use'], 'RIGHTS_HOLD: current material use required')
    n = current['numeric']; index = current['span_index']; at = x(current['at']['elapsed_seconds_exact'], 's')
    need(type(index) is int and 0 <= index < len(s.spans) and type(current['integration_count']) is int
         and 0 <= current['integration_count'] <= 128 and type(n['branch_steps']) is int
         and n['branch_steps'] == current['integration_count'], 'STATE_HOLD: exact branch counters required')
    math = original.proof.math_view(s.math_basis, s.spans[index], s.profiles)
    base.reader._closed(n['branch_integrated_transfers'], set(math.units))
    totals = base._vector([n['branch_integrated_transfers'][k]['value'] for k in math.units], len(math.units))
    state = base._vector(n['last_confirmed']['state'], len(s.math_basis['seed']['initial_sample']['state']))
    derived = n['last_confirmed']['derived']
    base.reader._closed(derived, set(s.math_basis['seed']['initial_sample']['derived']))
    for name, value in derived.items():
        base.reader._closed(value, {'value', 'unit'})
        base._vector([value['value']], 1)
        need(value['unit'] == s.math_basis['seed']['initial_sample']['derived'][name]['unit'],
             'UNIT_HOLD: original derived units required')
    expected = _numeric(s, state, totals, n['last_confirmed']['derived'], n['branch_steps'], at, index)
    need(raw(expected) == raw(n) and current['at'] == n['at'], 'STATE_HOLD: complete original numeric/account projection required')
    need(x(s.spans[index]['start'], 's') <= at <= x(s.spans[index]['end'], 's') and at <= s.stop
         and x(n['schedule']['age_exact'], 'degC_day') < x(n['schedule']['next_threshold_exact'], 'degC_day'), 'TIME_HOLD: covered first-unconsumed current required')
    need(type(current['output_cursor']) is int and current['output_cursor'] >= 0, 'STATE_HOLD: actual output cursor required')
    base.reader._hash(current['output_prefix_sha256'])
    phase = current['phase']
    need(phase == 'source_anchor' or (phase == 'material_after' and at == x(s.point['at']['elapsed_seconds_exact'], 's'))
         or (phase == 'forcing_after' and at == x(s.spans[index]['start'], 's'))
         or (phase == 'forcing_before' and index < len(s.spans)-1 and at == x(s.spans[index]['end'], 's'))
         or (phase == 'declared_end' and index == len(s.spans)-1 and at == s.stop)
         or (phase == 'original_grid_endpoint' and at % s.grid == 0 and at < x(s.spans[index]['end'], 's')),
         'ORDER_HOLD: exact material/forcing/grid phase required')


def _page(s, previous, before, after, before_basis, after_basis, kind, evidence):
    return {'schema_version': 'supply-material-repeat-history-page-v1', 'kind': kind, 'definition_sha256': s.definition_ref,
        'previous_cursor_sha256': previous, 'before_current_sha256': digest(before), 'after_current_sha256': digest(after),
        'before_basis_sha256': digest(before_basis), 'after_basis_sha256': digest(after_basis), 'evidence': evidence}


def _compose(s, before, numeric, index, phase, kind):
    lifetime = deepcopy(before['lifetime']); integrated = kind == 'interval'
    lifetime['positive_segments'] += int(integrated); lifetime['repeat_transitions'] += 1
    lifetime['forcing_switches'] += int(kind == 'forcing_switch'); lifetime['frames'] += 1
    lifetime['committed_RHS_evaluations'] += 5 if integrated else 1
    _limits(lifetime)
    value = {**deepcopy(before), 'numeric': deepcopy(numeric), 'at': deepcopy(numeric['at']), 'span_index': index,
        'phase': phase, 'integration_count': before['integration_count']+int(integrated), 'lifetime': lifetime,
        'output_cursor': before['output_cursor']+1,
        'output_prefix_sha256': digest({'previous': before['output_prefix_sha256'], 'numeric_sha256': digest(numeric),
            'definition_sha256': s.definition_ref, 'phase': phase, 'span_index': index,
            'integration_count': before['integration_count']+int(integrated), 'model_version': VERSION})}
    return value


def _switch(s, before, index, derived):
    n = before['numeric']; math = original.proof.math_view(s.math_basis, s.spans[index], s.profiles)
    numeric = _numeric(s, tuple(n['last_confirmed']['state']), tuple(n['branch_integrated_transfers'][k]['value'] for k in math.units),
        derived, n['branch_steps'], x(n['at']['elapsed_seconds_exact'], 's'), index)
    for key in ('at','schedule','branch_integrated_transfers','lifetime_transfers_exact','point_totals_exact','branch_ledgers',
                'global_ledgers','transfer_origins','geometry_diagnostics'):
        need(raw(numeric[key]) == raw(n[key]), 'BALANCE_HOLD: forcing switch changed ' + key)
    return _compose(s, before, numeric, index, 'forcing_after', 'forcing_switch')


def _frames(receipt):
    data = receipt['point_data']; result = []
    for phase, state, derived in [('material_before', data['before_dense']['state'], data['before_dense']['derived']),
                                   ('material_after', data['after_state'], data['after_derived'])]:
        result.append({'phase': phase, 'at': deepcopy(data['at']), 'point_sha256': digest(receipt),
            'source_current_sha256': receipt['source']['current_sha256'], 'state': deepcopy(state), 'derived': deepcopy(derived)})
    return result


def _adoption(s, before, before_basis, receipt):
    data = receipt['point_data']; event = data['source_event']; seed_basis = deepcopy(s.math_basis); seed = seed_basis['seed']
    for key, value in [('program','after_program'), ('organs','after_organs'), ('costs','after_costs'),
        ('state_layout','after_state_layout'), ('birth_bases','after_birth_baselines'), ('geometry_baselines','after_geometry_baselines'),
        ('global_ledgers','post_point_global_ledgers_preview'), ('lifetime_transfers_exact','post_point_lifetime_transfers_exact_preview'),
        ('point_totals_exact','post_point_point_totals_exact_preview')]:
        seed[key] = deepcopy(data[value])
    seed['initial_sample'] = {'at': deepcopy(data['at']), 'state': deepcopy(data['after_state']), 'derived': deepcopy(data['after_derived'])}
    schedule = deepcopy(before['numeric']['schedule']); spacing = x(point._event_data(s, before)['timeline']['phyllochron_exact'], 'degC_day')
    schedule.update(consumed_event_id=event['source_event_id'], consumed_sequence=event['sequence'],
        consumed_threshold_exact=deepcopy(event['threshold_exact']), next_sequence=event['sequence']+1,
        next_threshold_exact=q(x(event['threshold_exact'], 'degC_day')+spacing, 'degC_day'),
        age_exact=deepcopy(data['before_dense']['shoot_age_exact']), policy='material_repeat_event_once_no_threshold_snap')
    seed['schedule'] = schedule; seed['event_sequence'] = before['numeric']['event_sequence']+1
    records = {kind: {'schema_version': 'supply-material-repeat-'+kind+'-origins-v1',
        'previous_origin_sha256': before['numeric']['transfer_origins'][kind], 'point_sha256': digest(receipt),
        'baselines': deepcopy(seed['birth_bases' if kind == 'physical' else 'geometry_baselines'])} for kind in ('physical','geometry')}
    seed['transfer_origins'] = {k: digest(v) for k,v in records.items()}
    frames = _frames(receipt)
    seed['output_cursor'] = before['output_cursor']+2
    seed['output_prefix_sha256'] = digest({'previous': before['output_prefix_sha256'], 'point_sha256': digest(receipt),
        'before_frame_sha256': digest(frames[0]), 'after_frame_sha256': digest(frames[1]),
        'definition_sha256': s.definition_ref, 'model_version': VERSION})
    at = x(data['at']['elapsed_seconds_exact'], 's'); grid = s.grid
    seed['original_grid_position'] = {'completed_grid_index': int(at//grid), 'at_original_grid': at % grid == 0,
        'next_grid_index': int(at//grid)+1, 'next_grid_elapsed_seconds_exact': q((at//grid+1)*grid, 's'),
        'remaining_to_next_grid_seconds_exact': q((at//grid+1)*grid-at, 's')}
    seed_basis['schema_version'] = 'supply-material-repeat-numeric-basis-v1'
    basis = {**FLAGS, 'schema_version': 'supply-material-repeat-basis-v1', 'model_version': VERSION, 'code_sha256': CODE_SHA256,
        'definition_sha256': s.definition_ref, 'previous_basis_sha256': digest(before_basis), 'source_current_sha256': digest(before),
        'point_sha256': digest(receipt), 'numeric_basis': seed_basis, 'origin_records': records}
    _activate(s, basis, receipt)
    math = original.proof.math_view(s.math_basis, s.spans[before['span_index']], s.profiles)
    numeric = _numeric(s, tuple(seed['initial_sample']['state']), (0.,)*len(math.units), seed['initial_sample']['derived'], 0, at, before['span_index'])
    lifetime = deepcopy(before['lifetime']); lifetime['positive_segments'] += 1; lifetime['repeat_transitions'] += 1
    lifetime['material_adoptions'] += 1; lifetime['frames'] += 2
    lifetime['committed_RHS_evaluations'] += sum(receipt['work'][k] for k in ('interval_replay_RHS_evaluations','dense_state_RHS_evaluations','point_stage_RHS_evaluations'))
    _limits(lifetime)
    current = {**FLAGS, 'schema_version': 'supply-material-repeat-current-v1', 'model_version': VERSION, 'code_sha256': CODE_SHA256,
        'definition_sha256': s.definition_ref, 'effective_rights': deepcopy(receipt['effective_rights']), 'numeric': numeric,
        'at': deepcopy(data['at']), 'span_index': before['span_index'], 'phase': 'material_after', 'integration_count': 0,
        'lifetime': lifetime, 'output_cursor': seed['output_cursor'], 'output_prefix_sha256': seed['output_prefix_sha256']}
    return basis, current, frames


def _restore(s, reference, meter):
    chain = []; seen = set(); selected = reference
    while True:
        need(selected not in seen and len(chain) <= 256, 'HISTORY_HOLD: bounded flat repeat ancestry required')
        seen.add(selected); cursor = _get(s, selected, base.CURRENT_MAX)
        base.reader._closed(cursor, CURSOR_FIELDS)
        if cursor['previous_cursor_sha256'] is None:
            basis, current = _root(s); _activate(s, basis)
            need(raw(cursor) == raw(_cursor(s, basis, current)) and raw(_get(s, cursor['current_sha256'], base.CURRENT_MAX)) == raw(current)
                 and raw(_get(s, cursor['basis_sha256'])) == raw(basis), 'HISTORY_HOLD: exact original-source repeat anchor required')
            break
        chain.append((selected, cursor)); selected = cursor['previous_cursor_sha256']
    previous = selected
    for selected, cursor in reversed(chain):
        meter.fence('history_validation')
        before, before_basis = current, s.basis
        page = _get(s, cursor['history_page_sha256']); base.reader._closed(page, PAGE_FIELDS)
        need(page['schema_version'] == 'supply-material-repeat-history-page-v1' and page['definition_sha256'] == s.definition_ref
             and page['previous_cursor_sha256'] == previous and page['before_current_sha256'] == digest(before)
             and page['before_basis_sha256'] == digest(before_basis), 'HISTORY_HOLD: exact flat before links required')
        saved = _get(s, page['after_current_sha256'], base.CURRENT_MAX); kind, evidence = page['kind'], page['evidence']
        if kind == 'interval':
            base.reader._closed(evidence, {'interval'})
            math = original.proof.math_view(s.math_basis, s.spans[before['span_index']], s.profiles)
            need(original.forcing._switch_index(s, before) is None, 'ORDER_HOLD: switch required before interval')
            right = original.forcing._right(s, before)
            state, totals, schedule = original.proof.trace_values(math, before['numeric'], evidence['interval'], right)
            need(x(schedule['age_exact'], 'degC_day') < x(schedule['next_threshold_exact'], 'degC_day'), 'EVENT_HOLD: cannot skip pending material')
            numeric = _numeric(s, state, totals, saved['numeric']['last_confirmed']['derived'], before['numeric']['branch_steps']+1, right, before['span_index'])
            current = _compose(s, before, numeric, before['span_index'], original.forcing._interval_phase(s, before['span_index'], right), kind)
        elif kind == 'forcing_switch':
            index = original.forcing._switch_index(s, before)
            need(index is not None and evidence == {'span_index': index, 'at': before['at'],
                'state_sha256': digest(before['numeric']['last_confirmed']['state']), 'point_transfers_added': False,
                'producer_code_sha256': CODE_SHA256}, 'ORDER_HOLD: actual unchanged-state switch required')
            current = _switch(s, before, index, saved['numeric']['last_confirmed']['derived'])
        elif kind == 'material_adoption':
            base.reader._closed(evidence, {'source_owner_version','pending_page_sha256','time_tolerance_seconds_exact','input_sha256',
                'point_sha256','point_witness_sha256','before_frame_sha256','after_frame_sha256'})
            witness = _get(s, evidence['point_witness_sha256'])
            bridge = before['phase'] == 'source_anchor'
            actual_s, actual_current = (s.original, s.source_current) if bridge else (s, before)
            actual_s.origin = s.origin
            source = point._ref(actual_s, actual_current, s.definition['source']['cursor_sha256'] if bridge else previous)
            receipt = proof.expand_point_witness(actual_s, actual_current, source, evidence['pending_page_sha256'], witness, meter)
            need(evidence['source_owner_version'] == source['owner_version'] and evidence['input_sha256'] == receipt['input_sha256']
                 and evidence['point_sha256'] == digest(receipt) == witness['public_point_sha256']
                 and evidence['time_tolerance_seconds_exact'] == receipt['candidate']['root_certificate']['time_tolerance_seconds_exact'],
                 'POINT_HOLD: actual source/input/tolerance required')
            basis, current, frames = _adoption(s, before, before_basis, receipt)
            need(evidence['before_frame_sha256'] == digest(frames[0]) and evidence['after_frame_sha256'] == digest(frames[1])
                 and all(raw(_get(s, digest(frame))) == raw(frame) for frame in frames), 'PROOF_HOLD: exact same-time material frames required')
        else:
            need(False, 'HISTORY_HOLD: known repeat transition required')
        need(raw(saved) == raw(current) and page['after_basis_sha256'] == digest(s.basis)
             and raw(_get(s, page['after_basis_sha256'])) == raw(s.basis)
             and raw(cursor) == raw(_cursor(s, s.basis, current, previous, digest(page))),
             'HISTORY_HOLD: exact after basis/current/cursor required')
        _shape(s, current); previous = selected
    _shape(s, current)
    return _get(s, reference, base.CURRENT_MAX), current


def _put_batch(s, values, records, meter):
    meter.reserve(values, records)
    for value, maximum in values:
        meter.fence('publication'); meter.p['CAS_puts_attempted'] += 1
        try:
            s.archive.put(raw(value, maximum), maximum=maximum)
        except point.ERRORS:
            meter.p['failed_put_effect_unknown'] = True
            raise
        meter.p['CAS_puts_completed'] += 1; meter.p['bytes_emitted'] += len(raw(value, maximum))
        meter.fence()
    meter.p['record_units_committed'] += records


def open_material(cursor_ref, definition_sha256, workspace):
    meter = point._Meter()
    need(type(cursor_ref) is CursorRef, 'CONTEXT_HOLD: exact repeat cursor reference required')
    with _session(definition_sha256, workspace, meter) as s:
        cursor, current = _restore(s, cursor_ref.sha256, meter)
        meter.fence('final_source_check')
        return _handle(s, cursor_ref.sha256, cursor, current)


def _adopt_held(s, before, cursor, previous, source_s, source_current, source_ref, pending, tolerance, inputs, expected, meter, anchor):
    before_basis = s.basis
    receipt = point._calculate_point(source_s, source_current, source_ref, pending, tolerance, inputs, meter)
    need(receipt['calculation_sha256'] == expected, 'POINT_HOLD: expected actual successor calculation required')
    witness = proof.pack_point_witness(receipt)
    expanded = proof.expand_point_witness(source_s, source_current, source_ref, pending, witness, meter)
    need(raw(expanded) == raw(receipt) and expanded['calculation_sha256'] == expected,
         'PROOF_HOLD: complete public point roundtrip required before publication')
    need(raw(inputs, point.INPUT_MAX) == raw(receipt['inputs'], point.INPUT_MAX), 'SOURCE_HOLD: caller inputs changed')
    basis, current, frames = _adoption(s, before, before_basis, receipt)
    evidence = {'source_owner_version': source_ref['owner_version'], 'pending_page_sha256': pending,
        'time_tolerance_seconds_exact': q(x(tolerance, 's'), 's'), 'input_sha256': receipt['input_sha256'],
        'point_sha256': digest(receipt), 'point_witness_sha256': digest(witness),
        'before_frame_sha256': digest(frames[0]), 'after_frame_sha256': digest(frames[1])}
    page = _page(s, previous, before, current, before_basis, basis, 'material_adoption', evidence)
    after_cursor = _cursor(s, basis, current, previous, digest(page))
    values = []
    if anchor:
        values.extend([(s.definition, base.PAGE_MAX), (before_basis, base.PAGE_MAX), (before, base.CURRENT_MAX), (cursor, base.CURRENT_MAX)])
    values.extend([(witness, base.PAGE_MAX), (basis, base.PAGE_MAX)])
    values.extend((v, base.PAGE_MAX) for v in basis['origin_records'].values())
    values.extend((v, base.PAGE_MAX) for v in frames)
    values.extend([(current, base.CURRENT_MAX), (page, base.PAGE_MAX), (after_cursor, base.CURRENT_MAX)])
    _put_batch(s, values, 3 if anchor else 2, meter)
    _shape(s, current); meter.fence('final_source_check')
    return Outcome('adopted', _handle(s, digest(after_cursor), after_cursor, current), None, deepcopy(meter.p), frames)


def adopt_successor(handle, pending_page_sha256, time_tolerance_seconds_exact, *, inputs, expected_point_sha256, workspace, cancelled=None, wall_seconds=60):
    meter = point._Meter(cancelled=cancelled, wall_seconds=wall_seconds)
    try:
        base.reader._hash(expected_point_sha256)
        if type(handle) is Handle:
            need(handle._token is _TOKEN and handle._workspace == workspace, 'CONTEXT_HOLD: genuine repeat workspace required')
            with _session(handle._definition, workspace, meter) as s:
                cursor, current = _restore(s, handle.cursor_sha256, meter)
                need(raw(cursor) == handle._cursor and raw(current) == handle._current and raw(s.basis) == handle._basis,
                     'CONTEXT_HOLD: exact repeated source handle required')
                ref = point._ref(s, current, handle.cursor_sha256)
                return _adopt_held(s, current, cursor, handle.cursor_sha256, s, current, ref,
                    pending_page_sha256, time_tolerance_seconds_exact, inputs, expected_point_sha256, meter, False)
        need(type(handle) is original.Handle and handle._token is original._TOKEN
             and handle._workspace == workspace.original_material_workspace, 'CONTEXT_HOLD: genuine original material workspace required')
        with _store(workspace, meter) as store:
            with point._material_source_session_v2(handle._definition, workspace.original_material_workspace, meter) as old_session:
                old_session.origin = old_session.parent.origin
                old_cursor, old_current = original._restore(old_session, handle.cursor_sha256)
                need(raw(old_cursor) == handle._cursor and raw(old_current) == handle._current and raw(old_session.basis) == handle._basis,
                     'CONTEXT_HOLD: exact original material handle required')
                d = _definition(old_session, handle)
                with _held(store, old_session, workspace, meter, d) as s:
                    s.source_current, s.source_cursor = old_current, old_cursor
                    basis, current = _root(s); _activate(s, basis)
                    cursor = _cursor(s, basis, current)
                    source = point._ref(old_session, old_current, handle.cursor_sha256)
                    return _adopt_held(s, current, cursor, digest(cursor), old_session, old_current, source,
                        pending_page_sha256, time_tolerance_seconds_exact, inputs, expected_point_sha256, meter, True)
    except point.ERRORS as error:
        return Outcome('hold', None, base._reason(error), deepcopy(meter.p), [],
            historical_cursor_sha256=handle.cursor_sha256 if type(handle) in (Handle, original.Handle) else None)


def advance(handle, request):
    authority_code, authority_check = point._code, _check
    validated_failure = None
    meter = point._Meter(cancelled=getattr(request, 'cancelled', None), wall_seconds=getattr(request, 'wall_seconds', 60), request=request)
    confirmed = None; emitted = []
    try:
        need(type(handle) is Handle and handle._token is _TOKEN, 'CONTEXT_HOLD: genuine repeat handle required')
        with _session(handle._definition, handle._workspace, meter) as s:
            cursor, current = _restore(s, handle.cursor_sha256, meter)
            need(raw(cursor) == handle._cursor and raw(current) == handle._current and raw(s.basis) == handle._basis,
                 'CONTEXT_HOLD: unchanged repeat handle required')
            confirmed = handle
            try:
                stop = original.forcing._request(s, current, request); status = 'yielded'; pending = None
                while True:
                    meter.fence()
                    if meter.p['record_units_reserved'] >= meter.records:
                        break
                    index = original.forcing._switch_index(s, current)
                    if index is not None:
                        if meter.p['actual_RHS_evaluations'] >= meter.rhs:
                            break
                        math = original.proof.math_view(s.math_basis, s.spans[index], s.profiles)
                        rhs = meter.evaluate(math, tuple(current['numeric']['last_confirmed']['state']), 'pending_replay')
                        new = _switch(s, current, index, rhs['derived']); kind = 'forcing_switch'
                        evidence = {'span_index': index, 'at': deepcopy(current['at']),
                            'state_sha256': digest(current['numeric']['last_confirmed']['state']), 'point_transfers_added': False,
                            'producer_code_sha256': CODE_SHA256}
                    else:
                        at = x(current['at']['elapsed_seconds_exact'], 's')
                        if at >= stop or meter.p['positive_segments_attempted'] >= meter.steps or meter.p['actual_RHS_evaluations']+5 > meter.rhs:
                            break
                        right = original.forcing._right(s, current)
                        need(right <= stop, 'TIME_HOLD: cannot split original canonical remainder')
                        state, totals, derived, trace, schedule = point._interval(s, current, meter)
                        if x(schedule['age_exact'], 'degC_day') >= x(schedule['next_threshold_exact'], 'degC_day'):
                            page = {'schema_version': 'supply-material-repeat-pending-page-v1', 'definition_sha256': s.definition_ref,
                                'previous_cursor_sha256': confirmed.cursor_sha256, 'interval': trace, 'schedule': schedule, 'material_consumed': False}
                            _put_batch(s, [(page, base.PAGE_MAX)], 1, meter)
                            pending = {'page_sha256': digest(page), 'material_consumed': False,
                                'reason': 'EVENT_HOLD: successor material requires a separate explicit point'}
                            status = 'awaiting_material'; break
                        numeric = _numeric(s, state, totals, derived, current['numeric']['branch_steps']+1, right, current['span_index'])
                        new = _compose(s, current, numeric, current['span_index'], original.forcing._interval_phase(s, current['span_index'], right), 'interval')
                        kind = 'interval'; evidence = {'interval': trace}
                    page = _page(s, confirmed.cursor_sha256, current, new, s.basis, s.basis, kind, evidence)
                    proposed = _cursor(s, s.basis, new, confirmed.cursor_sha256, digest(page))
                    _put_batch(s, [(new, base.CURRENT_MAX), (page, base.PAGE_MAX), (proposed, base.CURRENT_MAX)], 1, meter)
                    _shape(s, new)
                    confirmed, cursor, current = _handle(s, digest(proposed), proposed, new), proposed, new
                    emitted.append({'cursor_sha256': confirmed.cursor_sha256, 'current_sha256': digest(new),
                        'at': deepcopy(new['at']), 'phase': new['phase'], 'span_index': new['span_index']})
                if current['phase'] == 'declared_end': status = 'completed'
                meter.fence('final_source_check')
                return Outcome(status, confirmed, None, deepcopy(meter.p), emitted, pending)
            except point.ERRORS as error:
                authority = None
                try:
                    meter.code_metadata = authority_code(metadata=meter.code_metadata)
                    authority_check(s)
                    authority_code(metadata=meter.code_metadata)
                except point.ERRORS as late:
                    authority = base._reason(late)
                    confirmed, emitted = None, []
                validated_failure = (error, Outcome('hold', confirmed, base._reason(error), deepcopy(meter.p), emitted,
                    historical_cursor_sha256=handle.cursor_sha256, authority_hold=authority))
                raise
    except point.ERRORS as error:
        if validated_failure is not None and validated_failure[0] is error:
            return validated_failure[1]
        return Outcome('hold', None, base._reason(error), deepcopy(meter.p), [],
            historical_cursor_sha256=handle.cursor_sha256 if type(handle) is Handle else None)


_SIGNATURE = point._signature(sys.modules[__name__])
