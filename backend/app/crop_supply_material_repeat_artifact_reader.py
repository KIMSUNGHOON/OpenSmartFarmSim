"""Validate a selected, changing-basis replay from immutable stored observations."""
from contextlib import contextmanager
from copy import deepcopy
from fractions import Fraction
from hashlib import sha256
from math import isfinite, isclose
from pathlib import Path
from types import SimpleNamespace
import json
import os
import sys

from . import crop_supply_material_artifact_reader as old
from . import crop_supply_material_repeat_owner as owner
from . import crop_supply_material_repeat_point as point
from . import crop_supply_material_repeat_proof as proof
from . import crop_leaf_area_change as area_change
from .content_access import ContentAccess
from .crop_morphology_artifact_io import MorphologyArtifactHold, MorphologyBlobStore

base, original = owner.base, owner.original
raw, digest, q, x = owner.raw, owner.digest, owner.q, owner.x
MAX, TOTAL, FILES, FRAME_MAX, SCALARS = 2097152, 67108864, 4096, 512, 32768
FLAGS = {**owner.FLAGS, 'time_kind': 'synthetic_model_clock_not_observation',
         'claim_scope': 'stored_synthetic_repeat_material_window_only'}
ROOT_FIELDS = frozenset({'schema_version', *FLAGS, 'code_sha256', 'source', 'blob_groups',
                         'transitions', 'frames', 'effective_rights', 'window', 'terminal', 'notice'})
KINDS = ('original', 'base', 'forcing', 'material', 'repeat', 'points', 'frames')
OLD_PATHS = tuple(old.SOURCE_PATHS)
SOURCE_PATHS = tuple(sorted(set(OLD_PATHS) | {'backend/app/job_store.py',
    'backend/app/crop_supply_material_repeat_point.py', 'backend/app/crop_supply_material_repeat_owner.py',
    'backend/app/crop_supply_material_repeat_proof.py',
    'backend/app/crop_supply_material_repeat_artifact_producer.py',
    'backend/app/crop_supply_material_repeat_artifact_reader.py'}))
CODE_SHA256 = sha256(Path(__file__).read_bytes()).hexdigest()


class RepeatArtifactHold(ValueError):
    pass


def need(condition, message):
    if not condition:
        raise RepeatArtifactHold(message)


def closed(value, fields):
    need(type(value) is dict and set(value) == set(fields), 'SCHEMA_HOLD: exact closed artifact fields required')


def reference(data):
    return {'sha256': sha256(data).hexdigest(), 'bytes': len(data)}


def _runtime(metadata=None, code_metadata=None):
    if code_metadata is not None:
        need(_file_metadata() == code_metadata, 'CODE_HOLD: artifact code metadata changed')
    point._code(metadata=metadata)
    need((MAX, TOTAL, FILES, FRAME_MAX, SCALARS) == (2097152, 67108864, 4096, 512, 32768)
         and (OLD_PATHS, SOURCE_PATHS, KINDS) == _SOURCE_FIELDS,
         'CODE_HOLD: fixed artifact limits and source families required')
    need(tuple(old.SOURCE_PATHS) == OLD_PATHS, 'CODE_HOLD: fixed original source inventory required')
    need(point._signature(sys.modules[__name__]) == _SELF_SIGNATURE,
         'CODE_HOLD: unchanged loaded repeat artifact reader required')
    need(_stored_parameters() == _STORED_FIELDS, 'CODE_HOLD: unchanged stored-proof declaration policy required')
    for module, expected in _HELPER_FIELDS:
        need(point._signature(module) == expected, 'CODE_HOLD: unchanged artifact validation dispatch required')
    if code_metadata is not None:
        need(_file_metadata() == code_metadata, 'CODE_HOLD: artifact code changed during validation')


def _pins(*, metadata=None):
    _runtime(metadata)
    before = _file_metadata()
    root = Path(__file__).resolve().parents[2]
    result = {name: sha256((root / name).read_bytes()).hexdigest() for name in SOURCE_PATHS}
    need(_file_metadata() == before, 'CODE_HOLD: artifact code changed during hashing')
    need(result['backend/app/crop_supply_material_repeat_artifact_reader.py'] == CODE_SHA256,
         'CODE_HOLD: exact loaded artifact reader bytes required')
    return result


@contextmanager
def _store(directory, access, *, write, meter, code_metadata=None, close_fd=point._ACQUISITION_FIELDS[15]):
    _runtime(meter.code_metadata, code_metadata)
    store = point._open_store_v2(directory, access, write=write, meter=meter)
    state = object.__getattribute__(store, '__dict__')
    try:
        yield store
    finally:
        fd = state['_fd']
        if fd is not None:
            close_fd(fd)
            state['_fd'] = None


def _store_guard(store, metadata=None, code_metadata=None):
    _runtime(metadata, code_metadata)
    for name, expected in _STORE_FIELDS:
        method = getattr(store, name)
        need(getattr(method, '__self__', None) is store and getattr(method, '__func__', None) is expected,
             'CODE_HOLD: unchanged concrete artifact storage dispatch required')
    store._guard()


def _file_metadata():
    root = Path(__file__).resolve().parents[2]
    result = []
    for name in SOURCE_PATHS:
        info = (root / name).stat(follow_symlinks=False)
        result.append((name, info.st_dev, info.st_ino, info.st_mode, info.st_uid, info.st_gid,
                       info.st_nlink, info.st_size, info.st_mtime_ns, info.st_ctime_ns))
    return tuple(result)


def _fence(store, pins, witnessed, *, complete=False, meter=None, code_metadata=None):
    metadata = None if meter is None else meter.code_metadata
    _store_guard(store, metadata, code_metadata)
    if complete or code_metadata is None:
        need(_pins(metadata=metadata) == pins, 'CODE_HOLD: artifact code changed')
    else:
        need(_file_metadata() == code_metadata, 'CODE_HOLD: artifact code metadata changed')
    if complete:
        store._usage()
    for h, (data, meta) in list(witnessed.items()):
        before = base._metadata(os.stat(h, dir_fd=store._fd, follow_symlinks=False))
        need(before == meta, 'STORAGE_HOLD: selected artifact metadata changed')
        if complete:
            value = store.get(h, maximum=max(MAX, len(data)))
            after = base._metadata(os.stat(h, dir_fd=store._fd, follow_symlinks=False))
            need(type(value) is bytes and value == data and before == after,
                 'HASH_HOLD: selected artifact bytes changed')
    _runtime(metadata, code_metadata)


def _read_blob(store, h, witnessed, maximum=MAX, *, meter=None, code_metadata=None):
    metadata = None if meter is None else meter.code_metadata
    _store_guard(store, metadata, code_metadata)
    old.legacy._hash(h)
    before = base._metadata(os.stat(h, dir_fd=store._fd, follow_symlinks=False))
    data = store.get(h, maximum=maximum)
    after = base._metadata(os.stat(h, dir_fd=store._fd, follow_symlinks=False))
    need(type(data) is bytes and before == after and sha256(data).hexdigest() == h,
         'HASH_HOLD: real immutable artifact bytes required')
    if h in witnessed:
        need(witnessed[h] == (data, before), 'STORAGE_HOLD: immutable artifact witness changed')
    witnessed[h] = (data, before)
    _runtime(metadata, code_metadata)
    return data


def _document(data):
    value = old.legacy._parse(data, MAX)
    need(raw(value) == data, 'INPUT_HOLD: canonical stored artifact document required')
    return value


def _rights(value):
    closed(value, {'use', 'display', 'redistribute'})
    need(all(type(v) is bool for v in value.values()) and value['use'] and value['display'],
         'RIGHTS_HOLD: current use and display grants required')
    return value


def _legacy_sessions(source, obj, stores, manifest, original_frames, witnesses, bases, chains, value):
    """Fixed read-only artifact admission; these are not numerical workspace factories."""
    bd = obj(source['base']['definition_sha256'], 'base')
    fd = obj(source['forcing']['definition_sha256'], 'forcing')
    md = obj(source['material']['definition_sha256'], 'material')
    closed(bd, {'schema_version', 'source', 'code_sha256', 'method', 'stop_at', 'forcing_span', 'rights', *base.FLAGS})
    need(bd['schema_version'] == 'supply-season-definition-v1' and bd['code_sha256'] == base.CODE_SHA256
         and all(bd[k] == v for k, v in base.FLAGS.items()), 'SCOPE_HOLD: original season definition required')
    closed(bd['rights'], {'use', 'display', 'redistribute'})
    need(all(type(v) is bool for v in bd['rights'].values()) and bd['rights']['use'], 'RIGHTS_HOLD: original use grant required')
    index = source['source_frame_index']
    need(type(index) is int and 0 <= index < len(original_frames), 'INDEX_HOLD: actual original frame required')
    frame = original_frames[index]
    need(frame['checkpoint_sha256'] is not None and frame['phase'] == 'original_grid_endpoint',
         'SOURCE_HOLD: actual original-grid source checkpoint required')
    checkpoint = json.loads(witnesses[frame['checkpoint_sha256']][0])
    seed = bases['base']['seed']
    span = bd['forcing_span']; closed(span, {'begin', 'end', 'forcing_and_fruit_entry_sha256'})
    dt = Fraction(seed['original_numerical']['step_seconds'])
    begin, end = x(span['begin'], 's'), x(bd['stop_at'], 's')
    forcing = {k: seed['program']['scenario'][k] for k in ('forcing', 'fruit_entry')}
    need(begin == x(frame['at']['elapsed_seconds_exact'], 's') and begin < end == x(span['end'], 's')
         and dt > 0 and end % dt == begin % dt == 0 and (end-begin)/dt <= base.MAX_HISTORY_STEPS,
         'TIME_HOLD: original bounded forcing grid required')
    need(bd['method'] == seed['original_numerical']['method'] and span['forcing_and_fruit_entry_sha256'] == digest(forcing),
         'FORCING_HOLD: exact original forcing required')
    need(not bd['rights']['redistribute'] or manifest['redistribution_authorized'], 'RIGHTS_HOLD: source grant cannot escalate')
    origin = SimpleNamespace(archive=stores['base'], archive_witnesses={}, source=stores['original'],
        source_witnesses=witnesses, manifest=manifest, definition=bd, definition_ref=source['base']['definition_sha256'],
        original=checkpoint, basis=bases['base'], dt=dt)
    origin.profiles = {name: cls(witnesses[manifest['root_inputs'][name]['sha256']][0]) for name, cls in (
        ('growth_profile', base.growth.ReferenceParameters), ('cohort_profile', base.cohort.ReferenceFruitCohortParameters),
        ('transport_profile', base.transport.ReferenceFruitTransportParameters), ('exchange_profile', base.exchange.ReferenceParameters))}
    indices = {row['compartment_id']: i for i, row in enumerate(seed['program']['stem_root_compartments'])}
    origin.data = {**origin.basis, 'program': seed['program'], 'organs': seed['organs'], 'costs': seed['costs'],
        'profiles': origin.profiles, 'stem_stock_indices': [indices[row['compartment_id']] for row in seed['organs']['internodes']]}
    origin.units = base.books.flux_units(seed['program'], seed['organs'])
    _, current = base._restore(origin, source['base']['cursor_sha256'])
    need(raw(current) == raw(chains['base'][-1][2]), 'SOURCE_HOLD: complete original season restoration required')
    original.forcing._definition_head(fd)
    parent = SimpleNamespace(archive=stores['forcing'], archive_witnesses={}, definition=fd,
        definition_ref=source['forcing']['definition_sha256'], origin=origin, source_current=current,
        math_basis=origin.basis, profiles=origin.profiles, basis=bases['forcing'])
    original.forcing._plan(parent)
    _, current = original.forcing._restore(parent, source['forcing']['cursor_sha256'])
    need(raw(current) == raw(chains['forcing'][-1][2]), 'SOURCE_HOLD: complete forcing restoration required')
    closed(md, {'schema_version', *original.FLAGS, 'code_sha256', 'proof_code_sha256', 'source', 'pending_page_sha256',
                'time_tolerance_seconds_exact', 'inputs', 'expected_point_sha256', 'point_sha256'})
    need(md['schema_version'] == 'supply-material-definition-v1' and md['code_sha256'] == original.CODE_SHA256
         and md['proof_code_sha256'] == original.PROOF_SHA256, 'CODE_HOLD: original material definition required')
    point_source = original.point._source(parent, current)
    need(md['inputs']['cursor_sha256'] == md['source']['cursor_sha256'], 'SOURCE_HOLD: original material input cursor required')
    original.proof.verify(parent, current, point_source, md, value)
    numeric_basis, records = original._derive(parent, current, point_source, value, source['material']['definition_sha256'])
    material = SimpleNamespace(archive=stores['material'], archive_witnesses={}, definition=md,
        definition_ref=source['material']['definition_sha256'], parent=parent, origin=origin, source_current=current,
        point=value, math_basis=numeric_basis, origins=records, profiles=parent.profiles,
        basis=bases['material'], spans=parent.spans, grid=Fraction(numeric_basis['seed']['original_numerical']['step_seconds']),
        stop=parent.stop, rights=deepcopy(value['effective_rights']), basis_raw=raw(bases['material']))
    _, current = original._restore(material, source['material']['cursor_sha256'])
    need(raw(current) == raw(chains['material'][-1][2]), 'SOURCE_HOLD: complete original material restoration required')
    return material, current


def _source_reference(s, current, cursor, *, bridge):
    need(type(bridge) is bool, 'SOURCE_HOLD: explicit validated source role required')
    family = 'supply-material' if bridge else 'supply-material-repeat'
    basis_schema = 'supply-material-owner-basis-v1' if bridge else 'supply-material-repeat-basis-v1'
    need(current['schema_version'] == family+'-current-v1'
         and s.definition['schema_version'] == family+'-definition-v1'
         and s.basis['schema_version'] == basis_schema and digest(s.definition) == s.definition_ref,
         'SOURCE_HOLD: source role must match validated stored family')
    old.legacy._hash(cursor)
    return {'owner_version': original.VERSION if bridge else owner.VERSION,
            'definition_sha256': s.definition_ref, 'cursor_sha256': cursor,
            'current_sha256': digest(current), 'basis_sha256': digest(s.basis)}


def _replay(s, selected, meter):
    """Original flat validation and pure kernels, retaining each verified receipt and frame."""
    ancestry = []; seen = set(); reference = selected
    while True:
        need(reference not in seen and len(ancestry) <= 256, 'HISTORY_HOLD: bounded acyclic repeat ancestry required')
        seen.add(reference); cursor = owner._get(s, reference, base.CURRENT_MAX)
        closed(cursor, owner.CURSOR_FIELDS)
        if cursor['previous_cursor_sha256'] is None:
            basis, current = owner._root(s); owner._activate(s, basis)
            need(raw(cursor) == raw(owner._cursor(s, basis, current))
                 and raw(owner._get(s, cursor['current_sha256'], base.CURRENT_MAX)) == raw(current)
                 and raw(owner._get(s, cursor['basis_sha256'])) == raw(basis), 'HISTORY_HOLD: exact repeat source anchor required')
            break
        ancestry.append((reference, cursor)); reference = cursor['previous_cursor_sha256']
    anchor = (reference, cursor, deepcopy(current), deepcopy(basis)); previous = reference; rows = []
    for reference, cursor in reversed(ancestry):
        meter.fence('history_validation'); before, before_basis = current, s.basis
        page = owner._get(s, cursor['history_page_sha256']); closed(page, owner.PAGE_FIELDS)
        need(page['schema_version'] == 'supply-material-repeat-history-page-v1' and page['definition_sha256'] == s.definition_ref
             and page['previous_cursor_sha256'] == previous and page['before_current_sha256'] == digest(before)
             and page['before_basis_sha256'] == digest(before_basis), 'HISTORY_HOLD: exact repeat before links required')
        saved = owner._get(s, page['after_current_sha256'], base.CURRENT_MAX)
        kind, evidence = page['kind'], page['evidence']; receipt = None; material_frames = None
        if kind == 'interval':
            closed(evidence, {'interval'})
            math = original.proof.math_view(s.math_basis, s.spans[before['span_index']], s.profiles)
            need(original.forcing._switch_index(s, before) is None, 'ORDER_HOLD: forcing switch precedes interval')
            right = original.forcing._right(s, before)
            state, totals, schedule = original.proof.trace_values(math, before['numeric'], evidence['interval'], right)
            need(x(schedule['age_exact'], 'degC_day') < x(schedule['next_threshold_exact'], 'degC_day'),
                 'EVENT_HOLD: cannot skip pending material')
            numeric = owner._numeric(s, state, totals, saved['numeric']['last_confirmed']['derived'],
                                     before['numeric']['branch_steps']+1, right, before['span_index'])
            current = owner._compose(s, before, numeric, before['span_index'],
                                     original.forcing._interval_phase(s, before['span_index'], right), kind)
        elif kind == 'forcing_switch':
            index = original.forcing._switch_index(s, before)
            need(index is not None and evidence == {'span_index': index, 'at': before['at'],
                'state_sha256': digest(before['numeric']['last_confirmed']['state']), 'point_transfers_added': False,
                'producer_code_sha256': owner.CODE_SHA256}, 'ORDER_HOLD: exact stored forcing switch required')
            current = owner._switch(s, before, index, saved['numeric']['last_confirmed']['derived'])
        elif kind == 'material_adoption':
            closed(evidence, {'source_owner_version', 'pending_page_sha256', 'time_tolerance_seconds_exact', 'input_sha256',
                             'point_sha256', 'point_witness_sha256', 'before_frame_sha256', 'after_frame_sha256'})
            witness = owner._get(s, evidence['point_witness_sha256'])
            bridge = before['phase'] == 'source_anchor'
            actual_s, actual_current = (s.original, s.source_current) if bridge else (s, before)
            actual_s.origin = s.origin
            source = _source_reference(actual_s, actual_current,
                s.definition['source']['cursor_sha256'] if bridge else previous, bridge=bridge)
            receipt = proof.expand_point_witness(actual_s, actual_current, source, evidence['pending_page_sha256'], witness, meter)
            need(evidence['source_owner_version'] == source['owner_version'] and evidence['input_sha256'] == receipt['input_sha256']
                 and evidence['point_sha256'] == digest(receipt) == witness['public_point_sha256']
                 and evidence['time_tolerance_seconds_exact'] == receipt['candidate']['root_certificate']['time_tolerance_seconds_exact'],
                 'POINT_HOLD: actual source/input/tolerance and complete receipt required')
            basis, current, material_frames = owner._adoption(s, before, before_basis, receipt)
            need(evidence['before_frame_sha256'] == digest(material_frames[0])
                 and evidence['after_frame_sha256'] == digest(material_frames[1])
                 and all(raw(owner._get(s, digest(f))) == raw(f) for f in material_frames),
                 'PROOF_HOLD: exact stored same-time material frames required')
        else:
            need(False, 'HISTORY_HOLD: known repeat transition required')
        need(raw(saved) == raw(current) and page['after_basis_sha256'] == digest(s.basis)
             and raw(owner._get(s, page['after_basis_sha256'])) == raw(s.basis)
             and raw(cursor) == raw(owner._cursor(s, s.basis, current, previous, digest(page))),
             'HISTORY_HOLD: exact after basis/current/cursor required')
        owner._shape(s, current)
        rows.append((reference, cursor, deepcopy(page), deepcopy(before), deepcopy(before_basis),
                     deepcopy(current), deepcopy(s.basis), receipt, material_frames))
        previous = reference
    owner._shape(s, current)
    need(rows and any(row[2]['kind'] == 'material_adoption' for row in rows),
         'SCOPE_HOLD: at least one committed repeat material adoption required')
    return anchor, rows, cursor, current


def _diagnostics(numeric, before, kind, index, unit):
    key = f'{kind}_{index}'
    if before is None:
        value = old.legacy.projection._geometry(numeric['geometry_diagnostics'][key], unit)
        return {'kind': 'stored_confirmed', 'canonical_status': 'stored', **value}
    value = {'kind': 'dense_stored_transfers', 'canonical_status': 'not_stored_at_dense_boundary',
             'canonical_gap_exact': None, 'canonical_potential_difference_exact': None}
    for prefix, field in (('', 'pending_branch_transfers_exact'), ('lifetime_', 'pending_lifetime_transfers_exact')):
        transfers = before[field]; potential = x(transfers[key+'_potential'], unit); realized = x(transfers[key+'_realized'], unit)
        need(potential >= realized >= 0, 'QC_HOLD: nonnegative stored dense transfers required')
        value.update({prefix+'potential_exact': deepcopy(transfers[key+'_potential']),
                      prefix+'realized_exact': deepcopy(transfers[key+'_realized']), prefix+'deficit_exact': q(potential-realized, unit)})
    return value


def _project(index, transition_index, row, *, dense=False, witness_ref=None):
    reference_sha, cursor, page, before_current, before_basis, current, basis, receipt, material_frames = row
    seed = (before_basis if dense else basis)['numeric_basis']['seed']; numeric = current['numeric']
    data = receipt['point_data'] if receipt is not None else None
    before = data['before_dense'] if dense else None
    if dense:
        snapshot = {'at': deepcopy(data['at']), 'state': deepcopy(before['state']), 'derived': deepcopy(before['derived'])}
        schedule = deepcopy(data['source_schedule']); schedule['age_exact'] = deepcopy(before['shoot_age_exact'])
        accounts = {'event_sequence': before['event_sequence'], 'schedule': schedule,
            'global_ledgers': deepcopy(before['pending_global_ledgers']), 'local_ledgers': deepcopy(before['local_ledgers']),
            'point_totals_exact': deepcopy(before['point_totals_exact']),
            'lifetime_transfers_exact': deepcopy(before['pending_lifetime_transfers_exact']), 'transfer_origins': deepcopy(before['transfer_origins'])}
        phase, binding_kind, checkpoint = 'material_before', 'dense_material_before', None
    else:
        snapshot = deepcopy(numeric['last_confirmed'])
        accounts = {k: deepcopy(numeric[k]) for k in ('event_sequence', 'schedule', 'global_ledgers',
            'point_totals_exact', 'lifetime_transfers_exact', 'transfer_origins')}
        accounts['local_ledgers'] = deepcopy(numeric['branch_ledgers'])
        phase = current['phase']; checkpoint = reference_sha
        binding_kind = 'adopted_material_after' if receipt is not None else 'confirmed_current'
    source = {} if dense else {'current': reference(raw(current))}
    if receipt is not None:
        need(witness_ref is not None, 'SOURCE_HOLD: actual stored witness descriptor required')
        source.update(receipt=reference(raw(receipt)), witness=deepcopy(witness_ref),
                      material_frame=reference(raw(material_frames[0 if dense else 1])))
    binding = {'kind': binding_kind, 'transition_index': transition_index, 'history_page_sha256': digest(page),
        'transition_cursor_sha256': reference_sha, 'active_basis_sha256': digest(before_basis if dense else basis),
        'context_cursor_sha256': page['previous_cursor_sha256'], 'checkpoint_cursor_sha256': checkpoint, 'source': source}
    n, m, h = len(seed['program']['leaves']), len(seed['program']['stem_root_compartments']), len(seed['organs']['internodes'])
    z = 106+3*n+m; state = snapshot['state']; old._vector(state, z+2*h)
    old.legacy._utc(snapshot['at']['time_origin_utc']); x(snapshot['at']['elapsed_seconds_exact'], 's')
    need(type(accounts['event_sequence']) is int and accounts['event_sequence'] >= 0, 'EVENT_HOLD: actual nonnegative source event count required')
    old.legacy.projection.ledgers(accounts['global_ledgers'], seed['global_ledgers'])
    old.legacy.projection.ledgers(accounts['local_ledgers'], seed['global_ledgers'])
    leaf_ids = [v['leaf_id'] for v in seed['program']['leaves']]
    stem_ids = [v['compartment_id'] for v in seed['program']['stem_root_compartments']]
    node_ids = [v['compartment_id'] for v in seed['organs']['internodes']]
    layout = seed['state_layout']
    need(layout['original_prefix_length'] == z and layout['internode_ids'] == node_ids
         and layout['original']['leaf_ids'] == leaf_ids
         and [v['leaf_id'] for v in seed['organs']['leaves']] == leaf_ids,
         'INVENTORY_HOLD: actual per-basis ordered layout required')
    leaves, internodes = [], []
    for kind, name, identifier, unit, target in (('leaf', 'leaves', 'leaf_id', 'm2', leaves),
                                               ('internode', 'internodes', 'compartment_id', 'm', internodes)):
        for i, node in enumerate(seed['organs'][name]):
            old.legacy._id(node[identifier]); parent = node.get('parent_internode_id')
            need(parent is None or parent in node_ids, 'PARENT_HOLD: actual original parent required')
            coordinate = 106+n+i if kind == 'leaf' else z+h+i
            carbon = 106+2*n+i if kind == 'leaf' else 106+3*n+stem_ids.index(node[identifier])
            age = 106+i if kind == 'leaf' else z+i
            quantity = lambda value, u: old.legacy.projection.quantity({'value': value, 'unit': u}, u)
            target.append({'id': node[identifier], 'parent_internode_id': parent, 'source_index': i,
                'geometry': quantity(state[coordinate], unit), 'carbon': quantity(state[carbon], 'mg_CH2O/m2_floor'),
                'represented_age': quantity(state[age], 'degC_day'),
                'clock_exact': old.legacy.projection.clock(node['baseline'], snapshot['at']['elapsed_seconds_exact'],
                                                          accounts['lifetime_transfers_exact']['indoor_air_temperature_time']),
                'birth': deepcopy(node['baseline']), 'geometry_origin': deepcopy(seed['geometry_baselines'][name][i]),
                'metadata': deepcopy(node), 'geometry_diagnostics': _diagnostics(numeric, before, kind, i, unit)})
    floor = old.legacy.projection.quantity(seed['program']['model_floor_area'], 'm2_floor')
    need(floor['value'] > 0, 'BASIS_HOLD: positive original floor required')
    return {**FLAGS, 'schema_version': 'supply-material-repeat-replay-frame-v1', 'index': index, 'phase': phase,
        'at': deepcopy(snapshot['at']), 'binding': binding, 'snapshot': snapshot, 'model_floor_area': floor,
        'state_layout': deepcopy(layout), 'leaves': leaves, 'internodes': internodes, 'accounts': accounts}


def _build(definition_ref, final_ref, stores, fetch, meter, *, admitted=None, pins=None, code_metadata=None):
    if pins is None:
        pins = _pins(metadata=meter.code_metadata)
    _runtime(meter.code_metadata, code_metadata)
    selected = {kind: {} for kind in KINDS}
    def obj(h, kind):
        data = fetch(h, kind, MAX)
        value = _document(data); selected[kind][h] = data
        return value
    definition = obj(definition_ref, 'repeat'); owner._definition_head(definition)
    material_selection = {k: definition['source'][k] for k in ('definition_sha256', 'cursor_sha256')}
    md = obj(material_selection['definition_sha256'], 'material')
    fd = obj(md['source']['definition_sha256'], 'forcing')
    bd = obj(fd['source']['definition_sha256'], 'base')
    original_root = bd['source']['artifact_sha256']
    if admitted is None:
        manifest, original_frames, witnesses = old.legacy._load(stores['original'], original_root)
    else:
        origin = admitted.original.parent.origin
        need(admitted.meter is meter and stores['original'] is origin.source
             and stores['base'] is origin.archive and stores['forcing'] is admitted.original.parent.archive
             and stores['material'] is admitted.original.archive and stores['repeat'] is admitted.archive
             and original_root == origin.definition['source']['artifact_sha256']
             and bd['source'] == origin.definition['source'],
             'SOURCE_HOLD: original admission belongs to this actual held source chain')
        witnesses = dict(origin.source_witnesses)
        root_raw = witnesses[original_root][0]
        need(type(root_raw) is bytes and sha256(root_raw).hexdigest() == original_root
             and raw(origin.manifest) == root_raw,
             'SOURCE_HOLD: unchanged canonical root from actual original admission required')
        manifest = _document(root_raw)
        old.legacy._fence(stores['original'], manifest, witnesses)
        need(witnesses == origin.source_witnesses,
             'SOURCE_HOLD: original admitted source witnesses changed during reuse')
        original_frames = None
    selected['original'] = {h: data for h, (data, _) in witnesses.items()}
    source = {'original_root': reference(selected['original'][original_root]), 'source_frame_index': bd['source']['frame_index'],
        'base': deepcopy(fd['source']), 'forcing': deepcopy(md['source']), 'material': material_selection}
    point_value = obj(md['point_sha256'], 'material')
    chains, bases, _, old_rights = old._graph({'source': source, 'code_sha256': old._pins(),
        'effective_rights': deepcopy(point_value['effective_rights'])}, obj, manifest)
    if admitted is None:
        old_session, source_current = _stored_legacy_sessions(source, obj, stores, manifest, original_frames, witnesses, bases, chains, point_value)
        s = SimpleNamespace(archive=stores['repeat'], archive_witnesses={}, original=old_session, origin=old_session.parent.origin,
            spans=old_session.spans, grid=old_session.grid, stop=old_session.stop, profiles=old_session.profiles,
            meter=meter, definition=definition, definition_ref=definition_ref, definition_raw=raw(definition),
            source_cursor=obj(material_selection['cursor_sha256'], 'material'), source_current=source_current)
    else:
        s = admitted; old_session = s.original; source_current = s.source_current
        need(raw(s.definition) == raw(definition) and raw(source_current) == raw(chains['material'][-1][2]),
             'SOURCE_HOLD: actual held source agrees with selected artifact graph')
    expected_source = {'owner_version': original.VERSION, 'definition_sha256': material_selection['definition_sha256'],
        'cursor_sha256': material_selection['cursor_sha256'], 'current_sha256': digest(source_current), 'basis_sha256': digest(old_session.basis)}
    need(definition['source'] == expected_source and definition['forcing_definition_sha256'] == md['source']['definition_sha256']
         and definition['initial_binding_sha256'] == manifest['initial_binding']['sha256']
         and definition['original_grid'] == {'time_origin_utc': source_current['at']['time_origin_utc'], 'step_seconds_exact': q(old_session.grid, 's')}
         and definition['stop_at'] == q(old_session.stop, 's'), 'SOURCE_HOLD: exact selected original bridge required')
    anchor, rows, cursor, current = (_stored_replay(s, final_ref, meter, point_fetch=lambda h: obj(h, 'points'))
        if admitted is None else _replay(s, final_ref, meter))
    for kind, session in (('base', old_session.parent.origin), ('forcing', old_session.parent), ('material', old_session), ('repeat', s)):
        for h in list(session.archive_witnesses):
            obj(h, kind)
    transitions, frames = [], []
    for i, row in enumerate(rows):
        h, c, page, before, before_basis, after, after_basis, receipt, material_frames = row
        transition = {'index': i, 'kind': page['kind'], 'previous_cursor_sha256': page['previous_cursor_sha256'],
            'cursor': reference(raw(c)), 'history_page': reference(raw(page)), 'before_current': reference(raw(before)),
            'after_current': reference(raw(after)), 'before_basis': reference(raw(before_basis)),
            'after_basis': reference(raw(after_basis)), 'frame_indices': []}
        if receipt is not None:
            data = raw(receipt); selected['points'][digest(receipt)] = data
            witness = fetch(page['evidence']['point_witness_sha256'], 'repeat', MAX)
            transition['point'] = {'witness': reference(witness), 'receipt': reference(data),
                'calculation_sha256': receipt['calculation_sha256'],
                'candidate_calculation_sha256': receipt['candidate']['calculation_sha256'],
                'before_frame': reference(raw(material_frames[0])), 'after_frame': reference(raw(material_frames[1]))}
            for record in after_basis['origin_records'].values():
                need(raw(obj(digest(record), 'repeat')) == raw(record), 'ORIGIN_HOLD: exact physical repeat origin required')
        for dense in ([True, False] if receipt is not None else [False]):
            frame = _project(len(frames), i, row, dense=dense,
                             witness_ref=transition['point']['witness'] if receipt is not None else None)
            data = raw(frame); need(len(data) <= MAX, 'CAPACITY_HOLD: bounded projected frame required')
            selected['frames'][sha256(data).hexdigest()] = data
            transition['frame_indices'].append(len(frames)); frames.append(frame)
        transitions.append(transition)
    need(2 <= len(frames) <= FRAME_MAX and sum(len(f['snapshot']['state']) for f in frames) <= SCALARS,
         'CAPACITY_HOLD: artifact frame and sampled scalar bounds exceeded')
    anchor_ref, anchor_cursor, anchor_current, anchor_basis = anchor
    full_source = {'owner_version': owner.VERSION, 'definition': reference(raw(definition)),
        'anchor': {'cursor': reference(raw(anchor_cursor)), 'current': reference(raw(anchor_current)), 'basis': reference(raw(anchor_basis))},
        'final': {'cursor': reference(raw(cursor)), 'current': reference(raw(current)), 'basis': reference(raw(s.basis))},
        'original_root': source['original_root'], 'original_frame_index': source['source_frame_index'],
        **{kind: {'definition': reference(raw(obj(source[kind]['definition_sha256'], kind))),
                  'cursor': reference(raw(obj(source[kind]['cursor_sha256'], kind)))} for kind in ('base', 'forcing', 'material')}}
    result = {**FLAGS, 'schema_version': 'supply-material-repeat-artifact-v1', 'code_sha256': dict(pins), 'source': full_source,
        'blob_groups': {kind: [reference(data) for h, data in sorted(selected[kind].items())] for kind in KINDS},
        'transitions': transitions, 'frames': [{'index': f['index'], 'transition_index': f['binding']['transition_index'],
            'phase': f['phase'], 'at': deepcopy(f['at']), 'active_basis_sha256': f['binding']['active_basis_sha256'],
            'frame': reference(raw(f)), 'state_scalars': len(f['snapshot']['state'])} for f in frames],
        'effective_rights': deepcopy(_rights(current['effective_rights'])),
        'window': {'first_at': deepcopy(frames[0]['at']), 'last_at': deepcopy(frames[-1]['at']), 'covers_whole_season': False,
                   'selection': 'committed_repeat_material_and_confirmed_remainder'},
        'terminal': {'status': 'completed' if current['phase'] == 'declared_end' else 'confirmed_prefix',
                     'hold': None, 'scope': 'declared_synthetic_forcing_plan_only'}, 'notice': deepcopy(manifest['root_inputs']['license_notice'])}
    need(full_source['anchor']['cursor']['sha256'] == anchor_ref, 'HASH_HOLD: actual repeat anchor required')
    _runtime(meter.code_metadata, code_metadata)
    return result, selected, frames, s


def _load(store, root_sha256, meter, *, pins=None, code_metadata=None):
    if code_metadata is None:
        code_metadata = _file_metadata()
    if pins is None:
        pins = _pins(metadata=meter.code_metadata)
    _runtime(meter.code_metadata, code_metadata)
    witnessed = {}; data = _read_blob(store, root_sha256, witnessed, meter=meter, code_metadata=code_metadata)
    manifest = _document(data); closed(manifest, ROOT_FIELDS)
    need(manifest['schema_version'] == 'supply-material-repeat-artifact-v1'
         and all(manifest[k] == v for k, v in FLAGS.items()) and manifest['code_sha256'] == pins,
         'CODE_HOLD: exact current artifact scope and code map required')
    _rights(manifest['effective_rights']); closed(manifest['blob_groups'], KINDS)
    advertised = {}; unique = {root_sha256: len(data)}
    for kind in KINDS:
        descriptors = manifest['blob_groups'][kind]
        need(type(descriptors) is list and 1 <= len(descriptors) <= FILES, 'CAPACITY_HOLD: nonempty bounded source descriptors required')
        hashes = []
        for desc in descriptors:
            closed(desc, {'sha256', 'bytes'}); old.legacy._hash(desc['sha256'])
            maximum = 16777216 if kind == 'original' else MAX
            need(type(desc['bytes']) is int and 1 <= desc['bytes'] <= maximum, 'CAPACITY_HOLD: actual bounded descriptor size required')
            payload = _read_blob(store, desc['sha256'], witnessed, maximum, meter=meter, code_metadata=code_metadata)
            need(len(payload) == desc['bytes'], 'HASH_HOLD: exact physical descriptor length required')
            unique[desc['sha256']] = len(payload); hashes.append(desc['sha256'])
        need(hashes == sorted(set(hashes)), 'SOURCE_HOLD: unique digest-sorted descriptors required')
        advertised[kind] = set(hashes)
    need(len(unique) <= FILES and sum(unique.values()) <= TOTAL, 'CAPACITY_HOLD: complete physical artifact bound exceeded')
    closed(manifest['source'], {'owner_version', 'definition', 'anchor', 'final', 'original_root', 'original_frame_index', 'base', 'forcing', 'material'})
    previous = meter.check
    meter.check = lambda: _fence(store, pins, witnessed, meter=meter, code_metadata=code_metadata)
    try:
        def fetch(h, kind, maximum):
            need(h in advertised[kind], 'SOURCE_HOLD: reference outside selected group')
            return _read_blob(store, h, witnessed, maximum, meter=meter, code_metadata=code_metadata)
        expected, selected, frames, session = _build(manifest['source']['definition']['sha256'],
            manifest['source']['final']['cursor']['sha256'], {kind: store for kind in KINDS[:5]}, fetch, meter,
            pins=pins, code_metadata=code_metadata)
        need(all(set(selected[k]) == advertised[k] for k in KINDS), 'SOURCE_HOLD: exact used selected closure required')
        for kind in ('points', 'frames'):
            for h, payload in selected[kind].items():
                need(fetch(h, kind, MAX) == payload, 'PROOF_HOLD: complete source-bound projected bytes required')
        need(raw(expected) == data, 'ARTIFACT_HOLD: complete source-derived manifest differs')
        _fence(store, pins, witnessed, complete=True, meter=meter, code_metadata=code_metadata)
        return data, [raw(f) for f in frames], witnessed, pins
    finally:
        meter.check = previous


def _read(directory, access, root_sha256, index):
    try:
        need(type(access) is ContentAccess, 'STORAGE_HOLD: concrete current file policy required')
        if index is not None:
            need(type(index) is int and index >= 0, 'INDEX_HOLD: strict nonnegative frame index required')
        meter = point._Meter()
        meter.fence()
        code_metadata = _file_metadata(); pins = _pins(metadata=meter.code_metadata)
        _runtime(meter.code_metadata, code_metadata)
        with _store(directory, access, write=False, meter=meter, code_metadata=code_metadata) as store:
            store._usage(); data, frames, witnessed, pins = _load(store, root_sha256, meter,
                pins=pins, code_metadata=code_metadata)
            need(index is None or index < len(frames), 'INDEX_HOLD: actual selected frame index required')
            result = data if index is None else frames[index]
            _fence(store, pins, witnessed, complete=True, meter=meter, code_metadata=code_metadata); meter.fence()
            return result
    except RepeatArtifactHold:
        raise
    except (OSError, ValueError, TypeError, KeyError, OverflowError, ZeroDivisionError, RecursionError) as error:
        message = str(error)
        raise RepeatArtifactHold(message if '_HOLD:' in message else 'ARTIFACT_HOLD: invalid or unavailable selected artifact') from None


def read_repeat_material_manifest(directory, access, root_sha256):
    return _read(directory, access, root_sha256, None)


def read_repeat_material_frame(directory, access, root_sha256, *, index):
    need(type(index) is int, 'INDEX_HOLD: strict actual frame index required')
    return _read(directory, access, root_sha256, index)



def _stored_parameters():
    funded = original.point.material.arithmetic
    area = funded.resume.short.old.leaf_area
    return (area.MODEL_VERSION, area.NORMALIZATION, frozenset(area.STATE_KEYS), area_change.RATE_VERSION,
            tuple(sorted(funded.resume.short.old.LEAF_UNITS.items())),
            tuple(sorted(funded.resume.short.STOCK_FIELDS.items())))


def _stored_books(context, data, y, rhs, totals, steps, at, observed):
    books = owner.base.books
    resume, source, base = (books.resume, books.source, books.base)
    F, Q, X, MASS = (books.F, books.Q, books.X, books.MASS)
    flux_units = books.flux_units
    need(type(observed) is dict, 'PROOF_HOLD: selected diagnostic object required')
    seed = data['seed']
    p = seed['program']
    organs = seed['organs']
    initial = seed['initial_sample']
    a0 = initial['state']
    n = len(p['leaves'])
    m = len(p['stem_root_compartments'])
    h = len(organs['internodes'])
    size = seed['state_layout']['original_prefix_length']
    units = flux_units(p, organs)
    t = {k: F(v) for k, v in zip(units, totals, strict=True)}
    lifetime = {k: X(seed['lifetime_transfers_exact'][k]) + v for k, v in t.items()}
    duration = at - X(initial['at']['elapsed_seconds_exact'])
    physical = source.stock.short._flux_units(p)
    latent = data['profiles']['exchange_profile'].values['latent_heat']
    local = source.candidate._local(p, a0[:size], y[:size], tuple((float(t[k]) for k in physical)), initial['derived'], rhs['derived'], duration, latent, steps)
    if steps == 0:
        resume._need(all((X(v['residual_exact']) == 0 for v in local.values())), 'BALANCE_HOLD: exact zero post-material branch required')
        local = {k: {'residual_exact': v['residual_exact'], 'budget_exact': Q(Fraction(0), v['budget_exact']['unit'])} for k, v in local.items()}
    root_p, root_seed = (data['root_program'], data['root_seed'])
    a, b = (tuple(map(F, root_seed['state'])), tuple(map(F, y[:size])))
    first = source.stock.short._view(root_seed['evaluation'])['joint']['derived']
    points = {k: X(v) for k, v in seed['point_totals_exact'].items()}
    rows = source.candidate._physical(p, a, b, lifetime, first, rhs['derived'], latent, len(root_p['leaves']), points)
    for i, birth in enumerate(seed['birth_bases']['leaf']):
        elapsed = at - X(birth['at_elapsed_seconds_exact'])
        rows[f'leaf_age_{i}'] = ((b[106 + i] - X(birth['thermal_age_exact']), -(lifetime['indoor_air_temperature_time'] - X(birth['air_temperature_integral_exact']) - F(birth['base_temperature']['value']) * elapsed) / 86400), Fraction(0), Fraction(0), 'degC_day')
    for kind, start in [('leaf', 106 + 2 * n), ('stem_root', 106 + 3 * n)]:
        for i, birth in enumerate(seed['birth_bases'][kind]):
            rows[f'{kind}_carbon_{i}'] = ((b[start + i] - F(birth['carbon']['value']), -lifetime[f'{kind}_{i}_inflow'], lifetime[f'{kind}_{i}_maintenance'], lifetime[f'{kind}_{i}_removal']), Fraction(0), Fraction(0), MASS)
    rows['stem_root_carbon'] = ((sum(b[106 + 3 * n:]) - sum(a[106 + 3 * len(root_p['leaves']):]), -sum((lifetime[f'stem_root_{i}_inflow'] for i in range(m))), sum((lifetime[f'stem_root_{i}_maintenance'] + lifetime[f'stem_root_{i}_removal'] for i in range(m))), -points['stem_structural_carbon']), Fraction(0), Fraction(0), MASS)
    diagnostics = {}
    floor = F(p['model_floor_area']['value'])
    for kind, meta, offset, unit in [('leaf', organs['leaves'], 106 + n, 'm2'), ('internode', organs['internodes'], size + h, 'm')]:
        origins = seed['geometry_baselines']['leaves' if kind == 'leaf' else 'internodes']
        for i, (node, origin) in enumerate(zip(meta, origins, strict=True)):
            identifier = 'leaf_id' if kind == 'leaf' else 'compartment_id'
            resume._need(node[identifier] == origin[identifier] and origin['origin_geometry']['unit'] == unit and (origin['origin_lifetime_inflow_exact']['unit'] == MASS), 'ORIGIN_HOLD: exact ordered original geometry/inflow origins required')
            key = f'{kind}_{i}'
            start, end = (F(a0[offset + i]), F(y[offset + i]))
            real, potential = (t[key + '_realized'], t[key + '_potential'])
            cost = F(seed['costs']['leaves' if kind == 'leaf' else 'internodes'][i])
            stock_i = i if kind == 'leaf' else data['stem_stock_indices'][i]
            inflow = f'{('leaf' if kind == 'leaf' else 'stem_root')}_{stock_i}_inflow'
            local[key + '_geometry'] = base._row((end - start, -real), start, end, unit, steps)
            local[key + '_partition'] = base._row((t[key + '_extension'], t[key + '_unmapped'], -t[inflow]), Fraction(0), Fraction(0), MASS, steps)
            local[key + '_construction'] = base._row((t[key + '_extension'], -cost * real / floor), Fraction(0), Fraction(0), MASS, steps)
            geometry_origin = F(origin['origin_geometry']['value'])
            physical_origin = X(origin['origin_lifetime_inflow_exact'])
            rows[key + '_geometry'] = ((end - geometry_origin, -lifetime[key + '_realized']), Fraction(0), Fraction(0), unit)
            rows[key + '_partition'] = ((lifetime[key + '_extension'], lifetime[key + '_unmapped'], -lifetime[inflow] + physical_origin), Fraction(0), Fraction(0), MASS)
            rows[key + '_construction'] = ((lifetime[key + '_extension'], -cost * lifetime[key + '_realized'] / floor), Fraction(0), Fraction(0), MASS)
            resume._need(potential >= real >= 0 and lifetime[key + '_potential'] >= lifetime[key + '_realized'] >= 0, 'CONSTRAINT_HOLD: nonnegative branch and lifetime potential deficit required')
            diagnostics[key] = {'potential_exact': Q(potential, unit), 'realized_exact': Q(real, unit), 'deficit_exact': Q(potential - real, unit), 'lifetime_potential_exact': Q(lifetime[key + '_potential'], unit), 'lifetime_realized_exact': Q(lifetime[key + '_realized'], unit), 'lifetime_deficit_exact': Q(lifetime[key + '_potential'] - lifetime[key + '_realized'], unit)}
            if kind == 'internode':
                birth = node['baseline']
                base_temperature = F(birth['base_temperature']['value'])
                local[key + '_age'] = base._row((F(y[size + i]) - F(a0[size + i]), -(t['indoor_air_temperature_time'] - base_temperature * duration) / 86400), F(a0[size + i]), F(y[size + i]), 'degC_day', steps)
                rows[key + '_age'] = ((F(y[size + i]) - X(birth['thermal_age_exact']), -(lifetime['indoor_air_temperature_time'] - X(birth['air_temperature_integral_exact']) - base_temperature * (at - X(birth['at_elapsed_seconds_exact']))) / 86400), Fraction(0), Fraction(0), 'degC_day')
            saved = old.legacy.projection._geometry(observed[key], unit)
            need(all((saved[name] == value for name, value in diagnostics[key].items())), 'PROOF_HOLD: independently recomputed transfer diagnostics differ')
            diagnostics[key].update(canonical_gap_exact=deepcopy(saved['canonical_gap_exact']), canonical_potential_difference_exact=deepcopy(saved['canonical_potential_difference_exact']))
    need(set(observed) == set(diagnostics), 'PROOF_HOLD: exact diagnostic inventory required')
    resume._need(set(rows) == set(seed['global_ledgers']) == set(local), 'BALANCE_HOLD: complete original/new global accounts required')
    global_books = {}
    for name, (terms, _, _, unit) in rows.items():
        residual = sum(terms, Fraction(0))
        expected = X(seed['global_ledgers'][name]['residual_exact']) + X(local[name]['residual_exact'])
        budget = X(seed['global_ledgers'][name]['budget_exact']) + X(local[name]['budget_exact'])
        resume._need(residual == expected and abs(residual) <= budget, 'BALANCE_HOLD: original global plus post-material branch ' + name)
        global_books[name] = {'residual_exact': Q(residual, unit), 'budget_exact': Q(budget, unit)}
    return (local, global_books, diagnostics, lifetime)


def _stored_curve(curve):
    area = original.point.material.arithmetic.resume.short.old.leaf_area
    closed(curve, {'profile_id', 'origin', 'values'})
    area._identifier(curve['profile_id'])
    need(curve['origin'] == 'synthetic', 'INPUT_HOLD: synthetic source curve required')
    supplied = curve['values']
    units = {'maximum_area': 'm2', 'steepness': '1/degC_day', 'inflection_age': 'degC_day'}
    closed(supplied, set(units))
    values = {}
    for name, unit in units.items():
        quantity = supplied[name]
        closed(quantity, {'value', 'unit'})
        need(quantity['unit'] == unit and type(quantity['value']) in (int, float), 'UNIT_HOLD: original declared curve quantity required')
        number = float(quantity['value'])
        need(isfinite(number) and number >= 0 and (name == 'inflection_age' or number > 0), 'INPUT_HOLD: finite nonnegative and positive maximum/steepness required')
        values[name] = {'value': number, 'unit': unit}
    normalized = {**deepcopy(curve), 'values': values}
    curve_hash = area_change._digest({'rate_model_version': area_change.RATE_VERSION, 'curve': normalized})
    return (normalized, curve_hash)


def _stored_leaf(leaf, saved):
    funded = original.point.material.arithmetic
    short = funded.resume.short
    area = short.old.leaf_area
    funded._closed(leaf, {'leaf_id', 'curve', *short.old.LEAF_UNITS, *short.STOCK_FIELDS})
    values = {k: funded._quantity(leaf[k], unit) for k, unit in {**short.old.LEAF_UNITS, **short.STOCK_FIELDS}.items()}
    funded._need(values['thermal_age'] == 0 and values['initial_carbon'] > 0 and (values['sink_weight'] >= 0) and (values['carbon_removal'] >= 0), 'BIRTH_HOLD: zero age, positive carbon and nonnegative sink/removal required')
    area._identifier(leaf['leaf_id'])
    curve, curve_hash = _stored_curve(leaf['curve'])
    closed(saved, {'model_version', 'scope', 'claim_scope', 'gates', 'input_sha256', 'state'})
    state = saved['state']
    closed(state, area.STATE_KEYS)
    canonical = area._quantity(state['area'])
    requested = area._quantity(leaf['initial_area'])
    need(sys.float_info.min <= canonical['value'] <= curve['values']['maximum_area']['value'] and isclose(requested['value'], canonical['value'], rel_tol=1e-12, abs_tol=0), 'INITIAL_AREA_HOLD: actual saved canonical area/tolerance required')
    zero = {'numerator': '0', 'denominator': '1', 'unit': 'degC_day'}
    anchor = {'leaf_id': leaf['leaf_id'], 'age_exact': zero, 'curve_sha256': curve_hash, 'requested_area': requested, 'canonical_area': deepcopy(canonical)}
    expected_state = {'model_version': area.MODEL_VERSION, 'origin': 'synthetic', 'thermal_age_basis': 'since_leaf_emergence', 'normalization': area.NORMALIZATION, 'leaf_id': leaf['leaf_id'], 'curve': curve, 'curve_sha256': curve_hash, 'age_exact': zero, 'area': canonical, 'anchor': anchor}
    receipt = area._envelope(expected_state, {'operation': 'initialize', 'input_id': leaf['leaf_id'], 'state': expected_state})
    need(raw(receipt) == raw(saved), 'PROOF_HOLD: complete saved initialization envelope differs')
    normalized = {'leaf_id': leaf['leaf_id'], 'curve': curve, **{k: funded.numeric._q(v, {**short.old.LEAF_UNITS, **short.STOCK_FIELDS}[k]) for k, v in values.items()}}
    return (normalized, receipt)


def _point_initialization(value, *, repeat):
    data = value['point_data'] if repeat else value
    leaves = data['leaf_receipts']
    need(type(leaves) is list and len(leaves) == int(value['inputs']['leaf'] is not None),
         'PROOF_HOLD: exact physical point leaf initialization inventory required')
    return None if not leaves else leaves[0]['initialization']



def _stored_kernel_books(s, state, totals, derived, steps, at, *, observed):
    return _stored_books(None, s.data, state, {'derived': derived}, totals, steps, at, observed=observed)


def _stored_base_numeric(s, before, state, totals, derived, at, *, observed):
    steps = before['branch_steps'] + 1
    local, global_books, diagnostics, lifetime = _stored_books(None, s.data, state, {'derived': derived}, totals, steps, at, observed=observed)
    result = base.deepcopy(before)
    result.update(at={'time_origin_utc': before['at']['time_origin_utc'], 'elapsed_seconds_exact': base.q(at, 's')}, branch_steps=steps, grid_index=before['grid_index'] + 1, phase='original_grid_endpoint', schedule=base._clock(s, totals, at), output_cursor=before['output_cursor'] + 1, branch_integrated_transfers={k: {'value': v, 'unit': unit} for (k, unit), v in zip(s.units.items(), totals, strict=True)}, lifetime_transfers_exact={k: base.q(v, s.units[k]) for k, v in lifetime.items()}, branch_ledgers=local, global_ledgers=global_books, geometry_diagnostics=diagnostics)
    result['last_confirmed'] = {'at': base.deepcopy(result['at']), 'state': list(state), 'derived': base.deepcopy(derived)}
    result['output_prefix_sha256'] = base._hash({'previous': before['output_prefix_sha256'], 'sample_sha256': base._hash(result['last_confirmed']), 'branch_steps': steps, 'definition_sha256': s.definition_ref, 'model_version': base.VERSION})
    base._raw(result, base.CURRENT_MAX)
    return result


def _stored_base_verify_trace(s, before, current, trace):
    base.reader._closed(trace, {'left_elapsed_seconds_exact', 'right_elapsed_seconds_exact', 'step_seconds_exact', 'stages', 'endpoint', 'flux_order', 'shoot_clock_certificate'})
    left = base.x(before['at']['elapsed_seconds_exact'], 's')
    base._need(trace['left_elapsed_seconds_exact'] == base.q(left, 's') and trace['right_elapsed_seconds_exact'] == base.q(left + s.dt, 's') and (trace['step_seconds_exact'] == base.q(s.dt, 's')), 'TIME_HOLD: contiguous original-grid step required')
    y = tuple(before['last_confirmed']['state'])
    base._need(type(trace['stages']) is list and len(trace['stages']) == 4, 'TRACE_HOLD: four stored RK stages required')
    rates, flows, previous_rates = ([], [], None)
    for name, offset, row in zip(('k1', 'k2', 'k3', 'k4'), (0, s.dt / 2, s.dt / 2, s.dt), trace['stages'], strict=True):
        base.reader._closed(row, {'stage', 'at_elapsed_seconds_exact', 'state', 'rates', 'flux'})
        expected = y if previous_rates is None else base.combine(y, (previous_rates,), (base.Fraction(1),), offset)
        base._need(row['stage'] == name and row['at_elapsed_seconds_exact'] == base.q(left + offset, 's') and (base._vector(row['state'], len(y)) == expected), 'TRACE_HOLD: exact RK stage state/time order required')
        previous_rates = base._vector(row['rates'], len(y))
        rates.append(previous_rates)
        flows.append(base._vector(row['flux'], len(s.units)))
    weights = (base.Fraction(1, 6), base.Fraction(1, 3), base.Fraction(1, 3), base.Fraction(1, 6))
    end = base.combine(y, tuple(rates), weights, s.dt)
    totals = base.combine(tuple((before['branch_integrated_transfers'][k]['value'] for k in s.units)), tuple(flows), weights, s.dt)
    base.reader._closed(trace['endpoint'], {'state', 'rates', 'flux'})
    base._need(base._vector(trace['endpoint']['state'], len(y)) == end, 'TRACE_HOLD: actual shared-stage endpoint required')
    base._vector(trace['endpoint']['rates'], len(y))
    base._vector(trace['endpoint']['flux'], len(s.units))
    base._need(trace['flux_order'] == [{'name': k, 'unit': v} for k, v in s.units.items()], 'UNIT_HOLD: original full flux order required')
    expected = _stored_base_numeric(s, before, end, totals, current['last_confirmed']['derived'], left + s.dt, observed=current['geometry_diagnostics'])
    base._need(current == expected, 'CHECKPOINT_HOLD: exact state/clock/accumulators/accounts/prefix required')
    certificate = base.arithmetic._interval_clock(s.data, before, trace, current['schedule'])
    base._need(trace['shoot_clock_certificate'] == certificate and base.x(current['schedule']['age_exact'], 'degC_day') < base.x(current['schedule']['next_threshold_exact'], 'degC_day'), 'EVENT_HOLD: stored step cannot consume or skip a pending threshold')


def _stored_base_restore(s, cursor_sha):
    selected = selected_current = None
    seen = set()
    while True:
        base._need(cursor_sha not in seen and len(seen) <= base.MAX_HISTORY_STEPS, 'CAPACITY_HOLD: bounded acyclic season history required')
        seen.add(cursor_sha)
        cursor = base._get(s, cursor_sha, base.CURRENT_MAX)
        base.reader._closed(cursor, {'schema_version', *base.FLAGS, 'code_sha256', 'definition_sha256', 'basis_sha256', 'current_sha256', 'previous_cursor_sha256', 'history_page_sha256'})
        base._need(cursor == base._cursor(s, cursor['current_sha256'], base._hash(s.basis), cursor['previous_cursor_sha256'], cursor['history_page_sha256']), 'CONTEXT_HOLD: original code/definition/basis/claim flags required')
        base._need(base._get(s, cursor['basis_sha256']) == s.basis, 'SOURCE_HOLD: actual sufficient basis and origins required')
        current = base._get(s, cursor['current_sha256'], base.CURRENT_MAX)
        base._shape_current(s, current)
        if selected is None:
            selected, selected_current = (cursor, current)
        previous = cursor['previous_cursor_sha256']
        if previous is None:
            base._need(cursor['history_page_sha256'] is None and current == base._initial(s), 'SOURCE_HOLD: actual admitted origin state required')
            break
        parent = base._get(s, previous, base.CURRENT_MAX)
        before = base._get(s, parent['current_sha256'], base.CURRENT_MAX)
        base._shape_current(s, before)
        page = base._get(s, cursor['history_page_sha256'])
        base.reader._closed(page, {'schema_version', 'kind', 'previous_cursor_sha256', 'before_current_sha256', 'after_current_sha256', 'interval'})
        base._need(page['schema_version'] == 'supply-season-history-page-v1' and page['kind'] == 'step' and (page['previous_cursor_sha256'] == previous) and (page['before_current_sha256'] == parent['current_sha256']) and (page['after_current_sha256'] == cursor['current_sha256']), 'HISTORY_HOLD: complete ordered current/history references required')
        _stored_base_verify_trace(s, before, current, page['interval'])
        cursor_sha = previous
    return (selected, selected_current)


def _stored_forcing_numeric(s, before, state, totals, derived, steps, at, index, *, observed):
    m = original.forcing._math(s, index)
    local, global_books, diagnostics, lifetime = _stored_kernel_books(m, state, totals, derived, steps, at, observed=observed)
    position = int(at // s.grid)
    result = {**original.forcing.FLAGS, 'schema_version': 'supply-forcing-interval-state-v1', 'model_version': original.forcing.kernel.VERSION, 'code_sha256': original.forcing.kernel.CODE_SHA256, **{k: original.forcing.deepcopy(before[k]) for k in original.forcing.base.NUMERIC_FIELDS if k not in ('output_cursor', 'output_prefix_sha256')}, 'at': {'time_origin_utc': before['at']['time_origin_utc'], 'elapsed_seconds_exact': original.forcing.q(at, 's')}, 'branch_steps': steps, 'grid_index': position, 'grid_remainder_exact': original.forcing.q(at - position * s.grid, 's'), 'next_grid_endpoint_exact': original.forcing.q((position + 1) * s.grid, 's'), 'active_input_sha256': original.forcing.digest({k: s.spans[index][k] for k in ('forcing', 'fruit_entry')}), 'phase': 'original_grid_endpoint' if at % s.grid == 0 else 'forcing_interval_endpoint', 'schedule': original.forcing.base._clock(m, totals, at), 'branch_integrated_transfers': {k: {'value': v, 'unit': unit} for (k, unit), v in zip(m.units.items(), totals, strict=True)}, 'lifetime_transfers_exact': {k: original.forcing.q(v, m.units[k]) for k, v in lifetime.items()}, 'branch_ledgers': local, 'global_ledgers': global_books, 'geometry_diagnostics': diagnostics}
    result['last_confirmed'] = {'at': original.forcing.deepcopy(result['at']), 'state': list(state), 'derived': original.forcing.deepcopy(derived)}
    original.forcing.raw(result, original.forcing.base.CURRENT_MAX)
    return result


def _stored_forcing_switch(s, before, index, derived, *, observed):
    n = before['numeric']
    m = original.forcing._math(s, index)
    totals = tuple((n['branch_integrated_transfers'][k]['value'] for k in m.units))
    numeric = _stored_forcing_numeric(s, n, tuple(n['last_confirmed']['state']), totals, derived, n['branch_steps'], original.forcing.x(n['at']['elapsed_seconds_exact'], 's'), index, observed=observed)
    for name in ('at', 'branch_steps', 'grid_index', 'event_sequence', 'schedule', 'branch_integrated_transfers', 'lifetime_transfers_exact', 'point_totals_exact', 'branch_ledgers', 'global_ledgers', 'transfer_origins', 'geometry_diagnostics'):
        original.forcing.need(numeric[name] == n[name], 'BALANCE_HOLD: forcing switch cannot change ' + name)
    original.forcing.need(numeric['last_confirmed']['state'] == n['last_confirmed']['state'], 'STATE_HOLD: forcing switch must preserve stocks')
    return original.forcing._compose(s, before, numeric, index, 'forcing_after', False)


def _stored_forcing_verify_interval(s, before, after, evidence):
    original.forcing.need(original.forcing._switch_index(s, before) is None and before['phase'] != 'declared_end', 'ORDER_HOLD: interval must follow an applied forcing')
    trace = evidence['interval']
    left = original.forcing.x(before['at']['elapsed_seconds_exact'], 's')
    right = original.forcing._right(s, before)
    h = right - left
    original.forcing.base.reader._closed(trace, {'left_elapsed_seconds_exact', 'right_elapsed_seconds_exact', 'step_seconds_exact', 'stages', 'endpoint', 'flux_order', 'shoot_clock_certificate'})
    original.forcing.need(trace['left_elapsed_seconds_exact'] == original.forcing.q(left, 's') and trace['right_elapsed_seconds_exact'] == original.forcing.q(right, 's') and (trace['step_seconds_exact'] == original.forcing.q(h, 's')), 'TIME_HOLD: canonical fixed partition required')
    index = before['span_index']
    m = original.forcing._math(s, index)
    n = before['numeric']
    y = tuple(n['last_confirmed']['state'])
    original.forcing.need(type(trace['stages']) is list and len(trace['stages']) == 4, 'TRACE_HOLD: actual four RK4 stages required')
    rates = []
    flows = []
    previous = None
    forced = {'canopy_external': s.spans[index]['forcing']['canopy_external_heat']['value'], 'air_external': s.spans[index]['forcing']['air_external_sensible_heat']['value'], 'external_vapor': s.spans[index]['forcing']['air_external_vapor']['value'], 'entry_number': s.spans[index]['fruit_entry']['fruit_number_inflow']['value']}
    names = list(m.units)
    for label, offset, row in zip(('k1', 'k2', 'k3', 'k4'), (original.forcing.Fraction(0), h / 2, h / 2, h), trace['stages'], strict=True):
        original.forcing.base.reader._closed(row, {'stage', 'at_elapsed_seconds_exact', 'state', 'rates', 'flux'})
        expected = y if previous is None else original.forcing.base.combine(y, (previous,), (original.forcing.Fraction(1),), offset)
        original.forcing.need(row['stage'] == label and row['at_elapsed_seconds_exact'] == original.forcing.q(left + offset, 's') and (original.forcing.base._vector(row['state'], len(y)) == expected), 'TRACE_HOLD: exact stage state/time order required')
        previous = original.forcing.base._vector(row['rates'], len(y))
        rates.append(previous)
        flow = original.forcing.base._vector(row['flux'], len(m.units))
        flows.append(flow)
        original.forcing.need(all((flow[names.index(k)] == v for k, v in forced.items())), 'FORCING_HOLD: stage external/entry flux must use active view')
    weights = (original.forcing.Fraction(1, 6), original.forcing.Fraction(1, 3), original.forcing.Fraction(1, 3), original.forcing.Fraction(1, 6))
    state = original.forcing.base.combine(y, tuple(rates), weights, h)
    totals = original.forcing.base.combine(tuple((n['branch_integrated_transfers'][k]['value'] for k in m.units)), tuple(flows), weights, h)
    original.forcing.base.reader._closed(trace['endpoint'], {'state', 'rates', 'flux'})
    original.forcing.need(original.forcing.base._vector(trace['endpoint']['state'], len(y)) == state and trace['flux_order'] == [{'name': k, 'unit': v} for k, v in m.units.items()], 'TRACE_HOLD: exact endpoint/flux order required')
    original.forcing.base._vector(trace['endpoint']['rates'], len(y))
    original.forcing.base._vector(trace['endpoint']['flux'], len(m.units))
    numeric = _stored_forcing_numeric(s, n, state, totals, after['numeric']['last_confirmed']['derived'], n['branch_steps'] + 1, right, index, observed=after['numeric']['geometry_diagnostics'])
    original.forcing.need(original.forcing.x(numeric['schedule']['age_exact'], 'degC_day') < original.forcing.x(numeric['schedule']['next_threshold_exact'], 'degC_day'), 'EVENT_HOLD: stored interval cannot skip a material threshold')
    certificate = original.forcing.base.arithmetic._interval_clock(m.data, n, trace, numeric['schedule'])
    original.forcing.need(trace['shoot_clock_certificate'] == certificate and evidence == original.forcing._interval_evidence(s, before, trace), 'TRACE_HOLD: exact kernel/code/input/clock evidence required')
    original.forcing.need(after == original.forcing._compose(s, before, numeric, index, original.forcing._interval_phase(s, index, right), True), 'CHECKPOINT_HOLD: exact interval state/accounts/phase/prefix required')


def _stored_forcing_restore(s, cursor_sha):
    selected = selected_current = None
    seen = set()
    while True:
        original.forcing.need(cursor_sha not in seen and len(seen) <= original.forcing.MAX_OPERATIONS, 'CAPACITY_HOLD: bounded acyclic owner history required')
        seen.add(cursor_sha)
        cursor = original.forcing.get(s, cursor_sha, original.forcing.base.CURRENT_MAX)
        original.forcing.base.reader._closed(cursor, {'schema_version', *original.forcing.FLAGS, 'code_sha256', 'definition_sha256', 'basis_sha256', 'current_sha256', 'previous_cursor_sha256', 'history_page_sha256'})
        original.forcing.need(cursor == original.forcing._cursor(s, cursor['current_sha256'], original.forcing.digest(s.basis), cursor['previous_cursor_sha256'], cursor['history_page_sha256']) and original.forcing.get(s, cursor['basis_sha256']) == s.basis, 'SOURCE_HOLD: actual owner source/basis/definition required')
        current = original.forcing.get(s, cursor['current_sha256'], original.forcing.base.CURRENT_MAX)
        original.forcing._shape(s, current)
        if selected is None:
            selected, selected_current = (cursor, current)
        previous = cursor['previous_cursor_sha256']
        if previous is None:
            original.forcing.need(cursor['history_page_sha256'] is None and current == original.forcing._initial(s), 'SOURCE_HOLD: complete actual source origin required')
            break
        parent = original.forcing.get(s, previous, original.forcing.base.CURRENT_MAX)
        before = original.forcing.get(s, parent['current_sha256'], original.forcing.base.CURRENT_MAX)
        original.forcing._shape(s, before)
        page = original.forcing.get(s, cursor['history_page_sha256'])
        original.forcing.base.reader._closed(page, {'schema_version', 'kind', 'previous_cursor_sha256', 'before_current_sha256', 'after_current_sha256', 'evidence'})
        original.forcing.need(page['schema_version'] == 'supply-forcing-history-page-v1' and page['previous_cursor_sha256'] == previous and (page['before_current_sha256'] == parent['current_sha256']) and (page['after_current_sha256'] == cursor['current_sha256']), 'HISTORY_HOLD: actual ordered current/page references required')
        if page['kind'] == 'forcing_switch':
            index = original.forcing._switch_index(s, before)
            original.forcing.need(index is not None and page['evidence'] == original.forcing._switch_evidence(s, before, index) and (current == _stored_forcing_switch(s, before, index, current['numeric']['last_confirmed']['derived'], observed=current['numeric']['geometry_diagnostics'])), 'ORDER_HOLD: exact zero-time forcing switch required')
        else:
            original.forcing.need(page['kind'] == 'interval', 'HISTORY_HOLD: known owner history operation required')
            _stored_forcing_verify_interval(s, before, current, page['evidence'])
        cursor_sha = previous
    return (selected, selected_current)


def _stored_material_numeric(s, state, totals, derived, steps, at, index, *, observed):
    m = original.proof.math_view(s.math_basis, s.spans[index], s.profiles)
    local, global_books, diagnostics, lifetime = _stored_kernel_books(m, state, totals, derived, steps, at, observed=observed)
    if steps == 0:
        original.need(at == original.x(s.point['at']['elapsed_seconds_exact'], 's') and all((original.x(v['residual_exact'], v['residual_exact']['unit']) == 0 for v in local.values())), 'BALANCE_HOLD: exact zero-duration post-point branch required')
        local = {k: {'residual_exact': original.deepcopy(v['residual_exact']), 'budget_exact': original.q(0, v['budget_exact']['unit'])} for k, v in local.items()}
        for k, v in global_books.items():
            original.need(v['residual_exact'] == s.math_basis['seed']['global_ledgers'][k]['residual_exact'], 'BALANCE_HOLD: zero branch must preserve global residual')
        global_books = original.deepcopy(s.math_basis['seed']['global_ledgers'])
    seed = s.math_basis['seed']
    position = int(at // s.grid)
    return {**original.FLAGS, 'schema_version': 'supply-material-numeric-v1', 'code_sha256': original.CODE_SHA256, 'at': {'time_origin_utc': seed['initial_sample']['at']['time_origin_utc'], 'elapsed_seconds_exact': original.q(at, 's')}, 'branch_steps': steps, 'grid_index': position, 'grid_remainder_exact': original.q(at - position * s.grid, 's'), 'next_grid_endpoint_exact': original.q((position + 1) * s.grid, 's'), 'active_input_sha256': original.digest({k: s.spans[index][k] for k in ['forcing', 'fruit_entry']}), 'phase': 'material_after' if steps == 0 else 'original_grid_endpoint' if at % s.grid == 0 else 'forcing_interval_endpoint', 'schedule': original.base._clock(m, totals, at), 'event_sequence': seed['event_sequence'], 'last_confirmed': {'at': original.deepcopy(seed['initial_sample']['at']) if steps == 0 else {'time_origin_utc': seed['initial_sample']['at']['time_origin_utc'], 'elapsed_seconds_exact': original.q(at, 's')}, 'state': list(state), 'derived': original.deepcopy(derived)}, 'branch_integrated_transfers': {k: {'value': v, 'unit': unit} for (k, unit), v in zip(m.units.items(), totals, strict=True)}, 'lifetime_transfers_exact': {k: original.q(v, m.units[k]) for k, v in lifetime.items()}, 'point_totals_exact': original.deepcopy(seed['point_totals_exact']), 'branch_ledgers': local, 'global_ledgers': global_books, 'geometry_diagnostics': diagnostics, 'transfer_origins': original.deepcopy(seed['transfer_origins'])}


def _stored_material_initial(s, *, observed):
    seed = s.math_basis['seed']
    index = s.source_current['span_index']
    m = original.proof.math_view(s.math_basis, s.spans[index], s.profiles)
    sample = seed['initial_sample']
    n = _stored_material_numeric(s, tuple(sample['state']), (0.0,) * len(m.units), sample['derived'], 0, original.x(sample['at']['elapsed_seconds_exact'], 's'), index, observed=observed)
    return {**original.FLAGS, 'schema_version': 'supply-material-current-v1', 'code_sha256': original.CODE_SHA256, 'definition_sha256': s.definition_ref, 'effective_rights': original.deepcopy(s.rights), 'numeric': n, 'at': original.deepcopy(n['at']), 'span_index': index, 'phase': 'material_after', 'integration_count': 0, 'output_cursor': seed['output_cursor'], 'output_prefix_sha256': seed['output_prefix_sha256']}


def _stored_material_shape(s, current):
    original.base.reader._closed(current, {'schema_version', *original.FLAGS, 'code_sha256', 'definition_sha256', 'effective_rights', 'numeric', 'at', 'span_index', 'phase', 'integration_count', 'output_cursor', 'output_prefix_sha256'})
    original.need(current['schema_version'] == 'supply-material-current-v1' and current['code_sha256'] == original.CODE_SHA256 and (current['definition_sha256'] == s.definition_ref) and (current['effective_rights'] == s.rights) and all((current[k] == v for k, v in original.FLAGS.items())), 'CONTEXT_HOLD: exact material current scope/source/rights required')
    n = current['numeric']
    index = current['span_index']
    at = original.x(current['at']['elapsed_seconds_exact'], 's')
    original.need(type(index) is int and s.source_current['span_index'] <= index < len(s.spans) and all((type(current[k]) is int and current[k] >= 0 for k in ['integration_count', 'output_cursor'])) and (current['integration_count'] <= 128) and (type(n['branch_steps']) is int) and (n['branch_steps'] == current['integration_count']), 'STATE_HOLD: actual bounded material counters required')
    m = original.proof.math_view(s.math_basis, s.spans[index], s.profiles)
    original.base.reader._closed(n['branch_integrated_transfers'], set(m.units))
    totals = original.base._vector([n['branch_integrated_transfers'][k]['value'] for k in m.units], len(m.units))
    state = original.base._vector(n['last_confirmed']['state'], len(s.math_basis['seed']['initial_sample']['state']))
    derived = n['last_confirmed']['derived']
    original.base.reader._closed(derived, set(s.math_basis['seed']['initial_sample']['derived']))
    for name, v in derived.items():
        original.base.reader._closed(v, {'value', 'unit'})
        original.base._vector([v['value']], 1)
        original.need(v['unit'] == s.math_basis['seed']['initial_sample']['derived'][name]['unit'], 'UNIT_HOLD: actual derived unit required')
    original.need(current['at'] == n['at'] and original.raw(n) == original.raw(_stored_material_numeric(s, state, totals, derived, n['branch_steps'], at, index, observed=n['geometry_diagnostics'])), 'STATE_HOLD: exact material numeric/account projection required')
    original.need(original.x(s.point['at']['elapsed_seconds_exact'], 's') <= at <= s.stop and original.x(s.spans[index]['start'], 's') <= at <= original.x(s.spans[index]['end'], 's') and (original.x(n['schedule']['age_exact'], 'degC_day') < original.x(n['schedule']['next_threshold_exact'], 'degC_day')), 'TIME_HOLD: covered state before next unconsumed threshold required')
    phase = current['phase']
    original.base.reader._hash(current['output_prefix_sha256'])
    original.need(phase == 'material_after' and current == _stored_material_initial(s, observed=n['geometry_diagnostics']) or (phase == 'forcing_after' and at == original.x(s.spans[index]['start'], 's')) or (phase == 'forcing_before' and index < len(s.spans) - 1 and (at == original.x(s.spans[index]['end'], 's'))) or (phase == 'declared_end' and at == s.stop and (index == len(s.spans) - 1)) or (phase == 'original_grid_endpoint' and at % s.grid == 0 and (at < original.x(s.spans[index]['end'], 's'))), 'ORDER_HOLD: actual material/forcing/grid phase required')


def _stored_material_switch(s, before, index, derived, *, observed):
    n = before['numeric']
    m = original.proof.math_view(s.math_basis, s.spans[index], s.profiles)
    numeric = _stored_material_numeric(s, tuple(n['last_confirmed']['state']), tuple((n['branch_integrated_transfers'][k]['value'] for k in m.units)), derived, n['branch_steps'], original.x(n['at']['elapsed_seconds_exact'], 's'), index, observed=observed)
    for name in ['at', 'schedule', 'branch_integrated_transfers', 'lifetime_transfers_exact', 'point_totals_exact', 'branch_ledgers', 'global_ledgers', 'transfer_origins', 'geometry_diagnostics']:
        original.need(numeric[name] == n[name], 'BALANCE_HOLD: forcing switch must preserve ' + name)
    return original._compose(s, before, numeric, index, 'forcing_after', False)


def _stored_material_verify_interval(s, before, after, trace):
    original.need(original.forcing._switch_index(s, before) is None and before['phase'] != 'declared_end', 'ORDER_HOLD: active forcing interval required')
    index = before['span_index']
    right = original.forcing._right(s, before)
    m = original.proof.math_view(s.math_basis, s.spans[index], s.profiles)
    state, totals, schedule = original.proof.trace_values(m, before['numeric'], trace, right)
    original.need(original.x(schedule['age_exact'], 'degC_day') < original.x(schedule['next_threshold_exact'], 'degC_day'), 'EVENT_HOLD: cannot skip material threshold')
    numeric = _stored_material_numeric(s, state, totals, after['numeric']['last_confirmed']['derived'], before['numeric']['branch_steps'] + 1, right, index, observed=after['numeric']['geometry_diagnostics'])
    original.need(after == original._compose(s, before, numeric, index, original.forcing._interval_phase(s, index, right), True), 'CHECKPOINT_HOLD: exact state/accounts/prefix from saved interval required')


def _stored_material_restore(s, sha):
    selected = selected_current = None
    seen = set()
    while True:
        original.need(sha not in seen and len(seen) < 256, 'CAPACITY_HOLD: bounded acyclic material history required')
        seen.add(sha)
        cursor = original.get(s, sha, original.base.CURRENT_MAX)
        current = original.get(s, cursor['current_sha256'], original.base.CURRENT_MAX)
        original.need(cursor == original._cursor(s, original.digest(current), cursor['previous_cursor_sha256'], cursor['history_page_sha256']) and original.get(s, cursor['basis_sha256']) == s.basis, 'HISTORY_HOLD: exact material cursor and basis required')
        _stored_material_shape(s, current)
        if selected is None:
            selected, selected_current = (cursor, current)
        if cursor['previous_cursor_sha256'] is None:
            original.need(original.raw(current) == original.raw(_stored_material_initial(s, observed=current['numeric']['geometry_diagnostics'])) and original.get(s, cursor['history_page_sha256']) == original._adoption_page(s, original.digest(current)), 'HISTORY_HOLD: complete actual first material adoption required')
            break
        previous = original.get(s, cursor['previous_cursor_sha256'], original.base.CURRENT_MAX)
        before = original.get(s, previous['current_sha256'], original.base.CURRENT_MAX)
        _stored_material_shape(s, before)
        page = original.get(s, cursor['history_page_sha256'])
        kind = page['kind']
        evidence = page['evidence']
        original.need(page == original._page(cursor['previous_cursor_sha256'], previous['current_sha256'], original.digest(current), kind, evidence), 'HISTORY_HOLD: exact linked material history page required')
        if kind == 'forcing_switch':
            index = original.forcing._switch_index(s, before)
            original.need(index is not None and evidence == original._switch_evidence(before, index) and (current == _stored_material_switch(s, before, index, current['numeric']['last_confirmed']['derived'], observed=current['numeric']['geometry_diagnostics'])), 'ORDER_HOLD: exact zero-time forcing switch required')
        else:
            original.need(kind == 'interval', 'HISTORY_HOLD: known material history operation required')
            _stored_material_verify_interval(s, before, current, evidence)
        sha = cursor['previous_cursor_sha256']
    for record in s.origins.values():
        original.need(original.get(s, original.digest(record)) == record, 'ORIGIN_HOLD: exact new origin record required')
    return (selected, selected_current)


def _stored_repeat_numeric(s, state, totals, derived, steps, at, index, *, observed):
    value = _stored_material_numeric(s, state, totals, derived, steps, at, index, observed=observed)
    value.update(schema_version='supply-material-repeat-numeric-v1', code_sha256=owner.CODE_SHA256)
    return value


def _stored_repeat_shape(s, current):
    owner.base.reader._closed(current, owner.CURRENT_FIELDS)
    owner.need(current['schema_version'] == 'supply-material-repeat-current-v1' and current['model_version'] == owner.VERSION and (current['code_sha256'] == owner.CODE_SHA256) and (current['definition_sha256'] == s.definition_ref) and all((current[k] == v for k, v in owner.FLAGS.items())), 'STATE_HOLD: exact repeat current required')
    owner._limits(current['lifetime'])
    owner.original.forcing._rights(current['effective_rights'])
    owner.need(current['effective_rights']['use'], 'RIGHTS_HOLD: current material use required')
    n = current['numeric']
    index = current['span_index']
    at = owner.x(current['at']['elapsed_seconds_exact'], 's')
    owner.need(type(index) is int and 0 <= index < len(s.spans) and (type(current['integration_count']) is int) and (0 <= current['integration_count'] <= 128) and (type(n['branch_steps']) is int) and (n['branch_steps'] == current['integration_count']), 'STATE_HOLD: exact branch counters required')
    math = owner.original.proof.math_view(s.math_basis, s.spans[index], s.profiles)
    owner.base.reader._closed(n['branch_integrated_transfers'], set(math.units))
    totals = owner.base._vector([n['branch_integrated_transfers'][k]['value'] for k in math.units], len(math.units))
    state = owner.base._vector(n['last_confirmed']['state'], len(s.math_basis['seed']['initial_sample']['state']))
    derived = n['last_confirmed']['derived']
    owner.base.reader._closed(derived, set(s.math_basis['seed']['initial_sample']['derived']))
    for name, value in derived.items():
        owner.base.reader._closed(value, {'value', 'unit'})
        owner.base._vector([value['value']], 1)
        owner.need(value['unit'] == s.math_basis['seed']['initial_sample']['derived'][name]['unit'], 'UNIT_HOLD: original derived units required')
    expected = _stored_repeat_numeric(s, state, totals, n['last_confirmed']['derived'], n['branch_steps'], at, index, observed=n['geometry_diagnostics'])
    owner.need(owner.raw(expected) == owner.raw(n) and current['at'] == n['at'], 'STATE_HOLD: complete original numeric/account projection required')
    owner.need(owner.x(s.spans[index]['start'], 's') <= at <= owner.x(s.spans[index]['end'], 's') and at <= s.stop and (owner.x(n['schedule']['age_exact'], 'degC_day') < owner.x(n['schedule']['next_threshold_exact'], 'degC_day')), 'TIME_HOLD: covered first-unconsumed current required')
    owner.need(type(current['output_cursor']) is int and current['output_cursor'] >= 0, 'STATE_HOLD: actual output cursor required')
    owner.base.reader._hash(current['output_prefix_sha256'])
    phase = current['phase']
    owner.need(phase == 'source_anchor' or (phase == 'material_after' and at == owner.x(s.point['at']['elapsed_seconds_exact'], 's')) or (phase == 'forcing_after' and at == owner.x(s.spans[index]['start'], 's')) or (phase == 'forcing_before' and index < len(s.spans) - 1 and (at == owner.x(s.spans[index]['end'], 's'))) or (phase == 'declared_end' and index == len(s.spans) - 1 and (at == s.stop)) or (phase == 'original_grid_endpoint' and at % s.grid == 0 and (at < owner.x(s.spans[index]['end'], 's'))), 'ORDER_HOLD: exact material/forcing/grid phase required')


def _stored_repeat_switch(s, before, index, derived, *, observed):
    n = before['numeric']
    math = owner.original.proof.math_view(s.math_basis, s.spans[index], s.profiles)
    numeric = _stored_repeat_numeric(s, tuple(n['last_confirmed']['state']), tuple((n['branch_integrated_transfers'][k]['value'] for k in math.units)), derived, n['branch_steps'], owner.x(n['at']['elapsed_seconds_exact'], 's'), index, observed=observed)
    for key in ('at', 'schedule', 'branch_integrated_transfers', 'lifetime_transfers_exact', 'point_totals_exact', 'branch_ledgers', 'global_ledgers', 'transfer_origins', 'geometry_diagnostics'):
        owner.need(owner.raw(numeric[key]) == owner.raw(n[key]), 'BALANCE_HOLD: forcing switch changed ' + key)
    return owner._compose(s, before, numeric, index, 'forcing_after', 'forcing_switch')


def _stored_repeat_adoption(s, before, before_basis, receipt, *, observed):
    data = receipt['point_data']
    event = data['source_event']
    seed_basis = owner.deepcopy(s.math_basis)
    seed = seed_basis['seed']
    for key, value in [('program', 'after_program'), ('organs', 'after_organs'), ('costs', 'after_costs'), ('state_layout', 'after_state_layout'), ('birth_bases', 'after_birth_baselines'), ('geometry_baselines', 'after_geometry_baselines'), ('global_ledgers', 'post_point_global_ledgers_preview'), ('lifetime_transfers_exact', 'post_point_lifetime_transfers_exact_preview'), ('point_totals_exact', 'post_point_point_totals_exact_preview')]:
        seed[key] = owner.deepcopy(data[value])
    seed['initial_sample'] = {'at': owner.deepcopy(data['at']), 'state': owner.deepcopy(data['after_state']), 'derived': owner.deepcopy(data['after_derived'])}
    schedule = owner.deepcopy(before['numeric']['schedule'])
    spacing = owner.x(owner.point._event_data(s, before)['timeline']['phyllochron_exact'], 'degC_day')
    schedule.update(consumed_event_id=event['source_event_id'], consumed_sequence=event['sequence'], consumed_threshold_exact=owner.deepcopy(event['threshold_exact']), next_sequence=event['sequence'] + 1, next_threshold_exact=owner.q(owner.x(event['threshold_exact'], 'degC_day') + spacing, 'degC_day'), age_exact=owner.deepcopy(data['before_dense']['shoot_age_exact']), policy='material_repeat_event_once_no_threshold_snap')
    seed['schedule'] = schedule
    seed['event_sequence'] = before['numeric']['event_sequence'] + 1
    records = {kind: {'schema_version': 'supply-material-repeat-' + kind + '-origins-v1', 'previous_origin_sha256': before['numeric']['transfer_origins'][kind], 'point_sha256': owner.digest(receipt), 'baselines': owner.deepcopy(seed['birth_bases' if kind == 'physical' else 'geometry_baselines'])} for kind in ('physical', 'geometry')}
    seed['transfer_origins'] = {k: owner.digest(v) for k, v in records.items()}
    frames = owner._frames(receipt)
    seed['output_cursor'] = before['output_cursor'] + 2
    seed['output_prefix_sha256'] = owner.digest({'previous': before['output_prefix_sha256'], 'point_sha256': owner.digest(receipt), 'before_frame_sha256': owner.digest(frames[0]), 'after_frame_sha256': owner.digest(frames[1]), 'definition_sha256': s.definition_ref, 'model_version': owner.VERSION})
    at = owner.x(data['at']['elapsed_seconds_exact'], 's')
    grid = s.grid
    seed['original_grid_position'] = {'completed_grid_index': int(at // grid), 'at_original_grid': at % grid == 0, 'next_grid_index': int(at // grid) + 1, 'next_grid_elapsed_seconds_exact': owner.q((at // grid + 1) * grid, 's'), 'remaining_to_next_grid_seconds_exact': owner.q((at // grid + 1) * grid - at, 's')}
    seed_basis['schema_version'] = 'supply-material-repeat-numeric-basis-v1'
    basis = {**owner.FLAGS, 'schema_version': 'supply-material-repeat-basis-v1', 'model_version': owner.VERSION, 'code_sha256': owner.CODE_SHA256, 'definition_sha256': s.definition_ref, 'previous_basis_sha256': owner.digest(before_basis), 'source_current_sha256': owner.digest(before), 'point_sha256': owner.digest(receipt), 'numeric_basis': seed_basis, 'origin_records': records}
    owner._activate(s, basis, receipt)
    math = owner.original.proof.math_view(s.math_basis, s.spans[before['span_index']], s.profiles)
    numeric = _stored_repeat_numeric(s, tuple(seed['initial_sample']['state']), (0.0,) * len(math.units), seed['initial_sample']['derived'], 0, at, before['span_index'], observed=observed)
    lifetime = owner.deepcopy(before['lifetime'])
    lifetime['positive_segments'] += 1
    lifetime['repeat_transitions'] += 1
    lifetime['material_adoptions'] += 1
    lifetime['frames'] += 2
    lifetime['committed_RHS_evaluations'] += sum((receipt['work'][k] for k in ('interval_replay_RHS_evaluations', 'dense_state_RHS_evaluations', 'point_stage_RHS_evaluations')))
    owner._limits(lifetime)
    current = {**owner.FLAGS, 'schema_version': 'supply-material-repeat-current-v1', 'model_version': owner.VERSION, 'code_sha256': owner.CODE_SHA256, 'definition_sha256': s.definition_ref, 'effective_rights': owner.deepcopy(receipt['effective_rights']), 'numeric': numeric, 'at': owner.deepcopy(data['at']), 'span_index': before['span_index'], 'phase': 'material_after', 'integration_count': 0, 'lifetime': lifetime, 'output_cursor': seed['output_cursor'], 'output_prefix_sha256': seed['output_prefix_sha256']}
    return (basis, current, frames)


def _stored_seeds(s, source, v, *, stored_initialization):
    event = source['event']
    a = original.point.material.arithmetic
    part = original.point.material.source.stock.short.stock.part
    a._closed(v['internode'], {'declaration', 'initial_length', 'construction_cost'})
    row = v['internode']['declaration']
    stock_fields = original.point.material.source.stock.short.STOCK_FIELDS
    a._closed(row, {'compartment_id', 'kind', *stock_fields})
    part._id(row['compartment_id'])
    original.point.need(row['compartment_id'] == event['internode_id'] and row['kind'] == 'internode', 'EVENT_HOLD: exact new internode ID/kind required')
    numbers = {k: a._quantity(row[k], unit) for k, unit in stock_fields.items()}
    original.point.need(numbers['initial_carbon'] > 0 and numbers['sink_weight'] >= 0 and (numbers['carbon_removal'] == 0), 'SEED_HOLD: positive C/nonnegative sink/zero removal required')
    node = {**original.point.deepcopy(row), **{k: original.point.material.numeric._q(value, stock_fields[k]) for k, value in numbers.items()}}
    length = a._quantity(v['internode']['initial_length'], 'm')
    cost = a._quantity(v['internode']['construction_cost'], 'mg_CH2O/m_internode')
    profile = source['emergence_profile']
    floor = s.math_basis['seed']['program']['model_floor_area']['value']
    original.point.need(0 <= length <= profile['curve']['values']['maximum_length']['value'], 'GEOMETRY_HOLD: bounded explicit seed length required')
    compatibility = {'internode': original.point.material.compatibility(numbers['initial_carbon'], cost, length, floor, 'm')}
    new_leaf = initialization = leaf_cost = temperature = None
    if v['leaf'] is not None:
        packet = v['leaf']
        a._closed(packet, {'declaration', 'incoming_temperature', 'construction_cost'})
        new_leaf, initialization = _stored_leaf(packet['declaration'], saved=stored_initialization)
        original.point.need(new_leaf['leaf_id'] == event['leaf_id'] and new_leaf['carbon_removal']['value'] == 0, 'EVENT_HOLD: exact new leaf ID/zero removal required')
        temperature = a._quantity(packet['incoming_temperature'], 'degC')
        original.point.material.numeric._temperature(temperature)
        leaf_cost = a._quantity(packet['construction_cost'], 'mg_CH2O/m2_leaf')
        compatibility['leaf'] = original.point.material.compatibility(new_leaf['initial_carbon']['value'], leaf_cost, initialization['state']['area']['value'], floor, 'm2')
    return {'node': node, 'length': length, 'cost': cost, 'profile': original.point.deepcopy(profile), 'base_temperature': original.point.deepcopy(source['timeline']['base_temperature']), 'leaf': new_leaf, 'initialization': initialization, 'leaf_cost': leaf_cost, 'temperature': temperature, 'compatibility': compatibility}


def _stored_material_verify(s, current, source, definition, value):
    """Verify saved local producer witnesses without evaluating any past RHS."""
    original.proof.point._head(s, current, source, definition['inputs'], definition['pending_page_sha256'])
    original.proof.need(value['calculation_sha256'] == definition['expected_point_sha256'] and value['calculation_sha256'] == original.proof.digest({k: v for k, v in value.items() if k != 'calculation_sha256'}) and (value['code_sha256'] == original.proof.point.CODE_SHA256) and (value['model_version'] == original.proof.point.VERSION) and (value['status'] == 'point_ready') and (value['inputs'] == definition['inputs']) and (value['source_current_sha256'] == original.proof.digest(current)) and (value['source_schedule'] == current['numeric']['schedule']) and (value['source_transfer_origins'] == current['numeric']['transfer_origins']) and (value['input_sha256'] == original.proof.digest(definition['inputs'])) and (value['cursor_sha256'] == definition['source']['cursor_sha256']) and (value['definition_sha256'] == s.definition_ref) and (value['pending_page_sha256'] == definition['pending_page_sha256']) and (value['initial_binding_sha256'] == source['initial_binding_sha256']) and (value['source_event'] == source['event']) and (value['candidate_sha256'] == definition['inputs']['candidate_sha256']), 'POINT_HOLD: exact locally produced source-bound receipt required')
    original.proof.need(all((value[k] == v for k, v in original.proof.base.FLAGS.items())) and value['checkpoint_issued'] is False and (value['history_committed'] is False) and (value['material_consumed'] is False) and (value['schedule_adoption'] == 'not_performed') and (value['elapsed_seconds_advanced'] == original.proof.q(0, 's')), 'SCOPE_HOLD: original unadopted point scope required')
    n = current['numeric']
    index = current['span_index']
    span = s.spans[index]
    right = original.proof.forcing._right(s, current)
    page = original.proof.forcing.get(s, definition['pending_page_sha256'])
    trace = page['result']['interval']
    m = original.proof.math_view(s.math_basis, span, s.profiles)
    _, _, schedule = original.proof.trace_values(m, n, trace, right)
    original.proof.need(original.proof.x(schedule['age_exact'], 'degC_day') >= original.proof.x(schedule['next_threshold_exact'], 'degC_day'), 'EVENT_HOLD: original pending threshold must be bracketed')
    expected = original.proof.forcing._interval_evidence(s, current, trace)
    expected.update(status='awaiting_material', current=None, pending={'left_at': original.proof.deepcopy(n['at']['elapsed_seconds_exact']), 'right_at': original.proof.q(right, 's'), 'left_age_exact': original.proof.deepcopy(n['schedule']['age_exact']), 'right_age_exact': schedule['age_exact'], 'threshold_exact': schedule['next_threshold_exact'], 'schedule_consumed': False, 'forcing_material_order_resolved': False, 'candidate_or_checkpoint_issued': False})
    reason = 'EVENT_HOLD: refine material threshold before further integration'
    if right == original.proof.x(span['end'], 's') and index < len(s.spans) - 1:
        reason = 'ORDER_HOLD: material bracket reaches forcing edge; refine its order'
    original.proof.need(page == {'schema_version': 'supply-forcing-pending-page-v1', 'definition_sha256': s.definition_ref, 'previous_cursor_sha256': definition['source']['cursor_sha256'], 'result': expected, 'reason': reason}, 'REPLAY_HOLD: exact stored pending page required')
    left = original.proof.x(n['at']['elapsed_seconds_exact'], 's')
    dt = right - left
    threshold = original.proof.x(n['schedule']['next_threshold_exact'], 'degC_day')
    coefficients = original.proof.locator.event._thermal_polynomial(tuple((original.proof.Fraction(row['state'][104]) for row in trace['stages'])), dt, original.proof.Fraction(s.math_basis['shoot_base_temperature']), original.proof.x(n['schedule']['age_exact'], 'degC_day'), threshold)
    progress = {'bisections': 0}
    lo, hi = original.proof.locator._isolate(coefficients, dt, original.proof.x(definition['time_tolerance_seconds_exact'], 's'), lambda: None, progress)
    root = value['root_certificate']
    at = left + hi * dt
    expected_root = {'time_origin_utc': n['at']['time_origin_utc'], 'lower_elapsed_seconds_exact': original.proof.q(left + lo * dt, 's'), 'upper_elapsed_seconds_exact': original.proof.q(at, 's'), 'width_seconds_exact': original.proof.q((hi - lo) * dt, 's'), 'lower_thermal_residual_exact': original.proof.q(original.proof.locator.event._value(coefficients, lo), 'degC_day'), 'upper_thermal_residual_exact': original.proof.q(original.proof.locator.event._value(coefficients, hi), 'degC_day')}
    order = original.proof.locator._order(left, right, original.proof.x(span['start'], 's'), original.proof.x(span['end'], 's') if index < len(s.spans) - 1 else None, coefficients)
    checks = {'root': expected_root, 'order': order, 'status': 'root_located', 'hold': None, 'code_sha256': original.proof.locator.CODE_SHA256, 'owner_code_sha256': original.proof.forcing.CODE_SHA256, 'kernel_code_sha256': original.proof.kernel.CODE_SHA256, 'event_math_code_sha256': original.proof.locator.EVENT_CODE_SHA256, 'definition_sha256': s.definition_ref, 'cursor_sha256': definition['source']['cursor_sha256'], 'pending_page_sha256': definition['pending_page_sha256'], 'numeric_sha256': original.proof.digest(n), 'span_sha256': original.proof.digest(span), 'interval_input_sha256': expected['input_sha256'], 'source_schedule': n['schedule'], 'effective_rights': s.rights, 'time_tolerance_seconds_exact': definition['time_tolerance_seconds_exact'], 'polynomial_residual_coefficients_exact': [original.proof.q(v, 'degC_day') for v in coefficients]}
    checks.update({**original.proof.base.FLAGS, 'schema_version': 'supply-forcing-threshold-location-v1', 'model_version': original.proof.locator.VERSION, 'interval_left_exact': original.proof.q(left, 's'), 'interval_right_exact': original.proof.q(right, 's'), 'minimum_derivative_per_theta_exact': original.proof.q(original.proof.locator.event._minimum_derivative(coefficients), 'degC_day'), 'ideal_cubic_minus_accumulated_endpoint_age_exact': original.proof.q(original.proof.locator.event._value(coefficients, original.proof.Fraction(1)) - (original.proof.x(schedule['age_exact'], 'degC_day') - threshold), 'degC_day'), 'method_reference': original.proof.locator.event.METHOD_REFERENCE, 'method': 'classical_rk4_third_order_continuous_extension_eq28_exact_rational_bisection', 'claim_scope': 'root_isolation_in_this_numerical_polynomial_not_physical_time_or_discretization_error', 'progress': {'stage': 'final_source_check', 'pending_current_validation_RHS_evaluations': 1, 'pending_new_RHS_evaluations': 4, 'RHS_quota_reserved': 5, 'failed_pending_RHS_count_unreported': False, 'bisections': progress['bisections'], 'past_confirmed_intervals_reintegrated': 0}, 'checkpoint_issued': False, 'history_committed': False, 'material_consumed': False})
    original.proof.need(original.proof.raw(root) == original.proof.raw(checks) and order['material_forcing_order_resolved'] and (index == len(s.spans) - 1 or at < original.proof.x(span['end'], 's')), 'ROOT_HOLD: actual root and strict material ordering required')
    original.proof.need(value['at'] == {'time_origin_utc': n['at']['time_origin_utc'], 'elapsed_seconds_exact': original.proof.q(at, 's')} and value['at']['elapsed_seconds_exact'] == definition['inputs']['at_elapsed_seconds_exact'], 'TIME_HOLD: exact chosen material time required')
    weights = original.proof.point.candidate.old._weights(hi)
    state = original.proof.base.combine(tuple(n['last_confirmed']['state']), tuple((tuple(r['rates']) for r in trace['stages'])), weights, dt)
    partial = original.proof.base.combine((0.0,) * len(m.units), tuple((tuple(r['flux']) for r in trace['stages'])), weights, dt)
    dense = original.proof.point.candidate.books.packet(m, n, state, partial, value['before_dense']['derived'], at, 1)
    original.proof.need(original.proof.raw(dense) == original.proof.raw(value['before_dense']) and dense['represented_threshold_status'] == 'crossed', 'STATE_HOLD: exact whole dense state and partial accounts required')
    spacing = original.proof.x(source['timeline']['phyllochron_exact'], 'degC_day')
    original.proof.need(threshold <= original.proof.x(dense['shoot_age_exact'], 'degC_day') < threshold + spacing, 'EVENT_HOLD: only first pending event can be adopted')
    data = m.data
    data['initial'] = {'organs': data['seed']['organs'], 'state_layout': data['seed']['state_layout']}
    numbers = {'dense_candidate': {**original.proof.deepcopy(dense), 'global_ledgers': original.proof.deepcopy(dense['pending_global_ledgers'])}, 'at': original.proof.deepcopy(value['at']), 'source_prefix': {'event_sequence': n['event_sequence']}}
    seeds = _stored_seeds(s, source, definition['inputs'], stored_initialization=_point_initialization(value, repeat=False))
    count = 2 if seeds['leaf'] is not None else 1
    original.proof.need(value['schema_version'] == 'supply-season-material-point-result-v1' and value['hold'] is None and (value['policy'] == original.proof.point.POLICY) and (value['candidate_RHS_evaluations'] == 34) and (value['point_stage_RHS_evaluations'] == count) and (value['point_order'] == (['internode', 'leaf'] if count == 2 else ['internode'])) and (original.proof.raw(value['progress']) == original.proof.raw({'stage': 'final_source_check', 'candidate_RHS_evaluations': 34, 'point_RHS_evaluations': count, 'candidate_failed_RHS_count_unreported': False, 'past_confirmed_intervals_reintegrated': 0})), 'POINT_HOLD: exact original point scope and work witness required')
    for derived in [dense['derived'], value['after_derived']]:
        original.proof.base.reader._closed(derived, set(n['last_confirmed']['derived']))
        for name, v in derived.items():
            original.proof.base.reader._closed(v, {'value', 'unit'})
            original.proof.base._vector([v['value']], 1)
            original.proof.need(v['unit'] == n['last_confirmed']['derived'][name]['unit'], 'UNIT_HOLD: actual source-derived unit required')
    jump = original.proof.point.material.apply(None, data, numbers, definition['inputs'], source['event'], seeds, lambda *a: original.proof.deepcopy(value['after_stage']))
    preview = original.proof.point.point_books.calculate(None, data, numbers, jump)
    layout = {**original.proof.deepcopy(data['seed']['state_layout']), 'original': original.proof.point.material.source.stock.short._layout(jump['program']), 'original_prefix_length': 106 + 3 * len(jump['program']['leaves']) + len(jump['program']['stem_root_compartments']), 'internode_ids': [row['compartment_id'] for row in jump['organs']['internodes']]}
    expected_fields = {**preview, 'after_program': jump['program'], 'after_state': jump['state'], 'after_organs': jump['organs'], 'after_costs': jump['costs'], 'after_state_layout': layout, 'after_rates': jump['evaluation']['rates'], 'after_derived': jump['evaluation']['derived'], 'seed_compatibility': seeds['compatibility'], 'new_birth_baselines': jump['new_birth_baselines'], 'flow_components': jump['components'], 'growth_costs': jump['growth_costs'], 'leaf_receipts': jump['leaf_receipts'], 'effective_rights': {k: s.rights[k] and definition['inputs']['rights'][k] for k in s.rights}}
    original.proof.need(all((original.proof.raw(value[k]) == original.proof.raw(v) for k, v in expected_fields.items())), 'POINT_HOLD: exact source-derived material arithmetic and accounts required')
    original.proof.base._vector(value['after_rates'], len(jump['state']))
    return (jump, preview)


def _stored_point_data(s, current, event, inputs, candidate, evaluate, *, initialization):
    math = point.original.proof.math_view(s.math_basis, s.spans[current['span_index']], s.profiles)
    data = math.data
    data['initial'] = {'organs': data['seed']['organs'], 'state_layout': data['seed']['state_layout']}
    before = point.deepcopy(candidate['dense_candidate'])
    numbers = {'dense_candidate': {**before, 'global_ledgers': point.deepcopy(before['pending_global_ledgers'])}, 'at': point.deepcopy(candidate['at']), 'source_prefix': {'event_sequence': current['numeric']['event_sequence']}}
    seeds = _stored_seeds(s, event, inputs, stored_initialization=initialization)
    jump = point.old.material.apply(None, data, numbers, inputs, event['event'], seeds, evaluate)
    preview = point.old.point_books.calculate(None, data, numbers, jump)
    layout = {**point.deepcopy(data['seed']['state_layout']), 'original': point.old.material.source.stock.short._layout(jump['program']), 'original_prefix_length': 106 + 3 * len(jump['program']['leaves']) + len(jump['program']['stem_root_compartments']), 'internode_ids': [v['compartment_id'] for v in jump['organs']['internodes']]}
    return {'before_dense': before, 'source_event': point.deepcopy(event['event']), 'source_schedule': point.deepcopy(current['numeric']['schedule']), 'source_transfer_origins': point.deepcopy(current['numeric']['transfer_origins']), 'at': point.deepcopy(candidate['at']), 'after_program': jump['program'], 'after_state': jump['state'], 'after_rates': point.deepcopy(jump['evaluation']['rates']), 'after_stage': jump['evaluation'], 'after_derived': point.deepcopy(jump['evaluation']['derived']), 'after_organs': jump['organs'], 'after_costs': jump['costs'], 'after_state_layout': layout, 'seed_compatibility': seeds['compatibility'], 'new_birth_baselines': jump['new_birth_baselines'], 'flow_components': jump['components'], 'growth_costs': jump['growth_costs'], 'leaf_receipts': jump['leaf_receipts'], 'point_order': ['internode', 'leaf'] if inputs['leaf'] is not None else ['internode'], **preview}


def _stored_point_saved(s, current, source, pending, inputs, candidate, after_stage, meter, *, initialization):
    event = proof.point._event_data(s, current)
    proof.point._head(s, current, source, event, inputs, pending)
    snapshot = proof.raw(inputs, proof.point.INPUT_MAX)
    proof.need(inputs['candidate_sha256'] == candidate['calculation_sha256'] and inputs['at_elapsed_seconds_exact'] == candidate['at']['elapsed_seconds_exact'], 'POINT_HOLD: exact saved candidate/input time required')
    age = proof.x(candidate['dense_candidate']['shoot_age_exact'], 'degC_day')
    threshold = proof.x(event['event']['threshold_exact'], 'degC_day')
    proof.need(threshold <= age < threshold + proof.x(event['timeline']['phyllochron_exact'], 'degC_day'), 'EVENT_HOLD: first threshold only')
    data = _stored_point_data(s, current, event, inputs, candidate, lambda *args: proof.deepcopy(after_stage), initialization=initialization)
    proof.base._vector(data['after_rates'], len(data['after_state']))
    work = proof.deepcopy(candidate['work'])
    work['point_stage_RHS_evaluations'] = 2 if inputs['leaf'] is not None else 1
    result = {**proof.point.FLAGS, 'schema_version': 'supply-material-successor-point-result-v1', 'model_version': proof.point.VERSION, 'code_sha256': proof.point.CODE_SHA256, 'status': 'point_ready', 'hold': None, 'policy': proof.point.POLICY, 'source': proof.deepcopy(source), 'pending_page_sha256': pending, 'initial_binding_sha256': event['initial_binding_sha256'], 'input_sha256': proof.sha256(snapshot).hexdigest(), 'inputs': proof.deepcopy(inputs), 'candidate_sha256': candidate['calculation_sha256'], 'candidate': candidate, 'effective_rights': {k: current['effective_rights'][k] and inputs['rights'][k] for k in current['effective_rights']}, 'point_data': data, 'work': work, 'elapsed_seconds_advanced': proof.q(0, 's'), 'schedule_adoption': 'not_performed', 'checkpoint_issued': False, 'history_committed': False, 'material_consumed': False}
    result['calculation_sha256'] = proof.digest(result)
    proof.raw(result)
    proof.need(proof.raw(inputs, proof.point.INPUT_MAX) == snapshot, 'SOURCE_HOLD: saved-stage proof changed inputs')
    meter.fence('history_validation')
    return result


def _stored_expand_point(s, current, source, pending, witness, meter, *, retained):
    """Resolve a real CAS witness to the entire original public receipt, with zero RHS."""
    meter.fence('history_validation')
    proof.base.reader._closed(witness, proof.WITNESS_FIELDS)
    proof.need(witness['schema_version'] == 'supply-material-successor-point-witness-v1' and witness['model_version'] == proof.VERSION and (witness['code_sha256'] == proof.CODE_SHA256) and (witness['producer_model_version'] == proof.point.VERSION) and (witness['producer_code_sha256'] == proof.point.CODE_SHA256) and all((witness[k] == v for k, v in proof.point.FLAGS.items())) and (proof.raw(witness['source']) == proof.raw(source)) and (witness['pending_page_sha256'] == pending), 'PROOF_HOLD: exact source-bound saved-stage witness required')
    for name in ('public_candidate_calculation_sha256', 'public_calculation_sha256', 'public_point_sha256'):
        proof.base.reader._hash(witness[name])
    proof.raw(witness)
    need(raw(proof.pack_point_witness(retained)) == raw(witness), 'PROOF_HOLD: physical complete point and witness observations differ')
    candidate = proof._candidate_saved(s, current, source, pending, witness['time_tolerance_seconds_exact'], witness['dense_derived'], witness['refinements'], meter, inputs=witness['inputs'], after_stage=witness['after_stage'])
    proof.need(candidate['calculation_sha256'] == witness['public_candidate_calculation_sha256'], 'PROOF_HOLD: full public candidate hash differs from actual saved observations')
    result = _stored_point_saved(s, current, source, pending, witness['inputs'], candidate, witness['after_stage'], meter, initialization=_point_initialization(retained, repeat=True))
    proof.need(result['calculation_sha256'] == witness['public_calculation_sha256'] and proof.digest(result) == witness['public_point_sha256'] and (proof.raw(result['work']) == proof.raw(witness['work'])), 'PROOF_HOLD: full public point, inner calculation or work identity differs')
    meter.fence('history_validation')
    need(raw(result) == raw(retained), 'PROOF_HOLD: complete physical public point differs from stored reconstruction')
    return result


def _stored_legacy_sessions(source, obj, stores, manifest, original_frames, witnesses, bases, chains, value):
    """Fixed read-only artifact admission; these are not numerical workspace factories."""
    bd = obj(source['base']['definition_sha256'], 'base')
    fd = obj(source['forcing']['definition_sha256'], 'forcing')
    md = obj(source['material']['definition_sha256'], 'material')
    closed(bd, {'schema_version', 'source', 'code_sha256', 'method', 'stop_at', 'forcing_span', 'rights', *base.FLAGS})
    need(bd['schema_version'] == 'supply-season-definition-v1' and bd['code_sha256'] == base.CODE_SHA256 and all((bd[k] == v for k, v in base.FLAGS.items())), 'SCOPE_HOLD: original season definition required')
    closed(bd['rights'], {'use', 'display', 'redistribute'})
    need(all((type(v) is bool for v in bd['rights'].values())) and bd['rights']['use'], 'RIGHTS_HOLD: original use grant required')
    index = source['source_frame_index']
    need(type(index) is int and 0 <= index < len(original_frames), 'INDEX_HOLD: actual original frame required')
    frame = original_frames[index]
    need(frame['checkpoint_sha256'] is not None and frame['phase'] == 'original_grid_endpoint', 'SOURCE_HOLD: actual original-grid source checkpoint required')
    checkpoint = json.loads(witnesses[frame['checkpoint_sha256']][0])
    seed = bases['base']['seed']
    span = bd['forcing_span']
    closed(span, {'begin', 'end', 'forcing_and_fruit_entry_sha256'})
    dt = Fraction(seed['original_numerical']['step_seconds'])
    begin, end = (x(span['begin'], 's'), x(bd['stop_at'], 's'))
    forcing = {k: seed['program']['scenario'][k] for k in ('forcing', 'fruit_entry')}
    need(begin == x(frame['at']['elapsed_seconds_exact'], 's') and begin < end == x(span['end'], 's') and (dt > 0) and (end % dt == begin % dt == 0) and ((end - begin) / dt <= base.MAX_HISTORY_STEPS), 'TIME_HOLD: original bounded forcing grid required')
    need(bd['method'] == seed['original_numerical']['method'] and span['forcing_and_fruit_entry_sha256'] == digest(forcing), 'FORCING_HOLD: exact original forcing required')
    need(not bd['rights']['redistribute'] or manifest['redistribution_authorized'], 'RIGHTS_HOLD: source grant cannot escalate')
    origin = SimpleNamespace(archive=stores['base'], archive_witnesses={}, source=stores['original'], source_witnesses=witnesses, manifest=manifest, definition=bd, definition_ref=source['base']['definition_sha256'], original=checkpoint, basis=bases['base'], dt=dt)
    origin.profiles = {name: cls(witnesses[manifest['root_inputs'][name]['sha256']][0]) for name, cls in (('growth_profile', base.growth.ReferenceParameters), ('cohort_profile', base.cohort.ReferenceFruitCohortParameters), ('transport_profile', base.transport.ReferenceFruitTransportParameters), ('exchange_profile', base.exchange.ReferenceParameters))}
    indices = {row['compartment_id']: i for i, row in enumerate(seed['program']['stem_root_compartments'])}
    origin.data = {**origin.basis, 'program': seed['program'], 'organs': seed['organs'], 'costs': seed['costs'], 'profiles': origin.profiles, 'stem_stock_indices': [indices[row['compartment_id']] for row in seed['organs']['internodes']]}
    origin.units = base.books.flux_units(seed['program'], seed['organs'])
    _, current = _stored_base_restore(origin, source['base']['cursor_sha256'])
    need(raw(current) == raw(chains['base'][-1][2]), 'SOURCE_HOLD: complete original season restoration required')
    original.forcing._definition_head(fd)
    parent = SimpleNamespace(archive=stores['forcing'], archive_witnesses={}, definition=fd, definition_ref=source['forcing']['definition_sha256'], origin=origin, source_current=current, math_basis=origin.basis, profiles=origin.profiles, basis=bases['forcing'])
    original.forcing._plan(parent)
    _, current = _stored_forcing_restore(parent, source['forcing']['cursor_sha256'])
    need(raw(current) == raw(chains['forcing'][-1][2]), 'SOURCE_HOLD: complete forcing restoration required')
    closed(md, {'schema_version', *original.FLAGS, 'code_sha256', 'proof_code_sha256', 'source', 'pending_page_sha256', 'time_tolerance_seconds_exact', 'inputs', 'expected_point_sha256', 'point_sha256'})
    need(md['schema_version'] == 'supply-material-definition-v1' and md['code_sha256'] == original.CODE_SHA256 and (md['proof_code_sha256'] == original.PROOF_SHA256), 'CODE_HOLD: original material definition required')
    point_source = original.point._source(parent, current)
    need(md['inputs']['cursor_sha256'] == md['source']['cursor_sha256'], 'SOURCE_HOLD: original material input cursor required')
    _stored_material_verify(parent, current, point_source, md, value)
    numeric_basis, records = original._derive(parent, current, point_source, value, source['material']['definition_sha256'])
    material = SimpleNamespace(archive=stores['material'], archive_witnesses={}, definition=md, definition_ref=source['material']['definition_sha256'], parent=parent, origin=origin, source_current=current, point=value, math_basis=numeric_basis, origins=records, profiles=parent.profiles, basis=bases['material'], spans=parent.spans, grid=Fraction(numeric_basis['seed']['original_numerical']['step_seconds']), stop=parent.stop, rights=deepcopy(value['effective_rights']), basis_raw=raw(bases['material']))
    _, current = _stored_material_restore(material, source['material']['cursor_sha256'])
    need(raw(current) == raw(chains['material'][-1][2]), 'SOURCE_HOLD: complete original material restoration required')
    return (material, current)


def _stored_replay(s, selected, meter, *, point_fetch):
    """Original flat validation and pure kernels, retaining each verified receipt and frame."""
    ancestry = []
    seen = set()
    reference = selected
    while True:
        need(reference not in seen and len(ancestry) <= 256, 'HISTORY_HOLD: bounded acyclic repeat ancestry required')
        seen.add(reference)
        cursor = owner._get(s, reference, base.CURRENT_MAX)
        closed(cursor, owner.CURSOR_FIELDS)
        if cursor['previous_cursor_sha256'] is None:
            basis, current = owner._root(s)
            owner._activate(s, basis)
            need(raw(cursor) == raw(owner._cursor(s, basis, current)) and raw(owner._get(s, cursor['current_sha256'], base.CURRENT_MAX)) == raw(current) and (raw(owner._get(s, cursor['basis_sha256'])) == raw(basis)), 'HISTORY_HOLD: exact repeat source anchor required')
            break
        ancestry.append((reference, cursor))
        reference = cursor['previous_cursor_sha256']
    anchor = (reference, cursor, deepcopy(current), deepcopy(basis))
    previous = reference
    rows = []
    for reference, cursor in reversed(ancestry):
        meter.fence('history_validation')
        before, before_basis = (current, s.basis)
        page = owner._get(s, cursor['history_page_sha256'])
        closed(page, owner.PAGE_FIELDS)
        need(page['schema_version'] == 'supply-material-repeat-history-page-v1' and page['definition_sha256'] == s.definition_ref and (page['previous_cursor_sha256'] == previous) and (page['before_current_sha256'] == digest(before)) and (page['before_basis_sha256'] == digest(before_basis)), 'HISTORY_HOLD: exact repeat before links required')
        saved = owner._get(s, page['after_current_sha256'], base.CURRENT_MAX)
        kind, evidence = (page['kind'], page['evidence'])
        receipt = None
        material_frames = None
        if kind == 'interval':
            closed(evidence, {'interval'})
            math = original.proof.math_view(s.math_basis, s.spans[before['span_index']], s.profiles)
            need(original.forcing._switch_index(s, before) is None, 'ORDER_HOLD: forcing switch precedes interval')
            right = original.forcing._right(s, before)
            state, totals, schedule = original.proof.trace_values(math, before['numeric'], evidence['interval'], right)
            need(x(schedule['age_exact'], 'degC_day') < x(schedule['next_threshold_exact'], 'degC_day'), 'EVENT_HOLD: cannot skip pending material')
            numeric = _stored_repeat_numeric(s, state, totals, saved['numeric']['last_confirmed']['derived'], before['numeric']['branch_steps'] + 1, right, before['span_index'], observed=saved['numeric']['geometry_diagnostics'])
            current = owner._compose(s, before, numeric, before['span_index'], original.forcing._interval_phase(s, before['span_index'], right), kind)
        elif kind == 'forcing_switch':
            index = original.forcing._switch_index(s, before)
            need(index is not None and evidence == {'span_index': index, 'at': before['at'], 'state_sha256': digest(before['numeric']['last_confirmed']['state']), 'point_transfers_added': False, 'producer_code_sha256': owner.CODE_SHA256}, 'ORDER_HOLD: exact stored forcing switch required')
            current = _stored_repeat_switch(s, before, index, saved['numeric']['last_confirmed']['derived'], observed=saved['numeric']['geometry_diagnostics'])
        elif kind == 'material_adoption':
            closed(evidence, {'source_owner_version', 'pending_page_sha256', 'time_tolerance_seconds_exact', 'input_sha256', 'point_sha256', 'point_witness_sha256', 'before_frame_sha256', 'after_frame_sha256'})
            witness = owner._get(s, evidence['point_witness_sha256'])
            bridge = before['phase'] == 'source_anchor'
            actual_s, actual_current = (s.original, s.source_current) if bridge else (s, before)
            actual_s.origin = s.origin
            source = _source_reference(actual_s, actual_current, s.definition['source']['cursor_sha256'] if bridge else previous, bridge=bridge)
            receipt = _stored_expand_point(actual_s, actual_current, source, evidence['pending_page_sha256'], witness, meter, retained=point_fetch(evidence['point_sha256']))
            need(evidence['source_owner_version'] == source['owner_version'] and evidence['input_sha256'] == receipt['input_sha256'] and (evidence['point_sha256'] == digest(receipt) == witness['public_point_sha256']) and (evidence['time_tolerance_seconds_exact'] == receipt['candidate']['root_certificate']['time_tolerance_seconds_exact']), 'POINT_HOLD: actual source/input/tolerance and complete receipt required')
            basis, current, material_frames = _stored_repeat_adoption(s, before, before_basis, receipt, observed=saved['numeric']['geometry_diagnostics'])
            need(evidence['before_frame_sha256'] == digest(material_frames[0]) and evidence['after_frame_sha256'] == digest(material_frames[1]) and all((raw(owner._get(s, digest(f))) == raw(f) for f in material_frames)), 'PROOF_HOLD: exact stored same-time material frames required')
        else:
            need(False, 'HISTORY_HOLD: known repeat transition required')
        need(raw(saved) == raw(current) and page['after_basis_sha256'] == digest(s.basis) and (raw(owner._get(s, page['after_basis_sha256'])) == raw(s.basis)) and (raw(cursor) == raw(owner._cursor(s, s.basis, current, previous, digest(page)))), 'HISTORY_HOLD: exact after basis/current/cursor required')
        _stored_repeat_shape(s, current)
        rows.append((reference, cursor, deepcopy(page), deepcopy(before), deepcopy(before_basis), deepcopy(current), deepcopy(s.basis), receipt, material_frames))
        previous = reference
    _stored_repeat_shape(s, current)
    need(rows and any((row[2]['kind'] == 'material_adoption' for row in rows)), 'SCOPE_HOLD: at least one committed repeat material adoption required')
    return (anchor, rows, cursor, current)


_SOURCE_FIELDS = (OLD_PATHS, SOURCE_PATHS, KINDS)
_STORE_FIELDS = tuple((name, getattr(MorphologyBlobStore, name)) for name in ('get', 'put', '_guard', '_usage'))
_HELPER_FIELDS = tuple((module, point._signature(module)) for module in (
    old, old.legacy, old.legacy.projection, owner, proof, base.books, base.books.base,
    base.books.source.candidate, base.books.source.stock.short,
    original.point.material.arithmetic, original.point.material.arithmetic.resume.short.old.leaf_area,
    original.point.material.arithmetic.resume.short, original.point.material.arithmetic.resume.short.old,
    area_change))
_STORED_FIELDS = _stored_parameters()
_SELF_SIGNATURE = point._signature(sys.modules[__name__])
