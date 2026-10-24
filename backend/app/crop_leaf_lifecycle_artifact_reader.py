"""Typed immutable lifecycle replay without importing growth or preparation code."""
from copy import deepcopy
from math import fsum, isfinite

from . import crop_leaf_appearance_artifact_reader as appearance
from . import crop_leaf_lifecycle_program as program
from .crop_morphology_artifact_io import MorphologyArtifactHold, MorphologyBlobStore, _need
from .crop_morphology_artifact_reader import FLAGS, _canonical, _closed, _hash, _parse, _quantity, PROGRAM_MAX, RESULT_MAX

MAX = RESULT_MAX
PREPARATION_VERSION = 'leaf-lifecycle-program-preparation-research-v1'
LIFECYCLE_VERSION = 'declared-leaf-lifecycle-research-v1'
INVENTORY_VERSION = 'declared-leaf-removal-inventory-research-v1'
PREPARATION_SOURCES = (*appearance.PREPARATION_SOURCES, *(f'backend/app/{name}.py' for name in (
    'crop_declared_leaf_removal', 'crop_leaf_removal_timeline', 'crop_leaf_removal_inventory', 'crop_leaf_lifecycle',
    'crop_leaf_lifecycle_program', 'crop_leaf_lifecycle_preparation')))
SOURCE_PATHS = (*PREPARATION_SOURCES, 'backend/app/crop_leaf_lifecycle_artifact_producer.py',
                'backend/app/crop_leaf_lifecycle_artifact_reader.py')
PREPARATION_MODELS = {**appearance.PREPARATION_MODELS, 'appearance_preparation': appearance.PREPARATION_VERSION,
    'removal_point': 'declared-leaf-removal-point-research-v1', 'removal_timeline': 'declared-leaf-removal-timeline-research-v1',
    'removal_inventory': INVENTORY_VERSION, 'lifecycle': LIFECYCLE_VERSION, 'preparation': PREPARATION_VERSION}
ROOT_CONSTANTS = {**FLAGS, 'schema_version': 'leaf-lifecycle-research-artifact-v1', 'status': 'completed_software_fixture',
    'time_kind': 'synthetic_model_clock_not_observation', 'parameter_scope': 'synthetic_software_fixture_only',
    'model_versions': {**PREPARATION_MODELS, 'producer': 'leaf-lifecycle-artifact-producer-research-v1'},
    'display_policy': program.DISPLAY_POLICY}
ROOT_FIELDS = set(ROOT_CONSTANTS) | {'appearance_program_sha256', 'appearance_program_bytes', 'management_program_sha256',
    'management_program_bytes', 'preparation_sha256', 'preparation_bytes', 'source_rights', 'stem_artifact_sha256',
    'stem_program_sha256', 'code_sha256', 'time_origin_utc', 'initial_at_elapsed_seconds_exact',
    'initial_state_sha256', 'initial_state_bytes', 'terminal_state_sha256', 'samples'}
COUNT_FIELDS = {'declared_leaf_count', 'tracked_leaf_count', 'active_leaf_count', 'removed_leaf_count',
                'scheduled_birth_count', 'emerged_new_leaf_count', 'pending_leaf_count'}
AREA_FIELDS = {'active_leaf_area', 'removed_leaf_area', 'last_tracked_leaf_area'}
RESULT_FIELDS = {'model_version', *FLAGS, 'input_sha256', 'state', 'time_origin_utc', 'at_elapsed_seconds_exact',
                 *COUNT_FIELDS, *AREA_FIELDS, 'active_leaf_ids', 'removed_leaf_ids', 'pending_leaf_ids'}
STATE_FIELDS = {'model_version', 'existing_inventory_state', 'birth_declarations', 'birth_declarations_sha256',
                'removal_declarations', 'removal_declarations_sha256', 'new_leaf_checkpoints'}
EXISTING_FIELDS = {'model_version', 'source_population', 'source_population_sha256', 'removal_declarations',
                   'removal_declarations_sha256', 'at_elapsed_seconds_exact', 'leaf_checkpoints'}
PREPARATION_FIELDS = {'model_version', *FLAGS, 'model_versions', 'input_sha256', 'appearance_program_sha256',
    'appearance_program_bytes', 'management_program_sha256', 'management_program_bytes', 'management_program_id',
    'appearance_preparation_sha256', 'appearance_preparation', 'lifecycle_initialization', 'lifecycle_initialization_sha256',
    'initial_state_sha256', 'stem', 'time_origin_utc', 'start_elapsed_seconds_exact', 'end_elapsed_seconds_exact',
    'forcing', 'source_rights', 'display_policy', 'code_sha256'}
DESCRIPTOR_FIELDS = {'index', 'at', 'result_sha256', 'result_bytes', 'input_state_sha256', 'state_sha256', 'input_sha256', 'stem_result_sha256'}
_digest = appearance._digest
_exact = appearance.population._exact


class LeafLifecycleReadHold(MorphologyArtifactHold):
    pass


def _record(value):
    return {'numerator': str(value.numerator), 'denominator': str(value.denominator), 'unit': 's'}


def _clip(forcing, start, end):
    return [{**s, 'start_elapsed_seconds_exact': _record(max(start, _exact(s['start_elapsed_seconds_exact'], 's'))),
             'end_elapsed_seconds_exact': _record(min(end, _exact(s['end_elapsed_seconds_exact'], 's')))}
            for s in forcing if _exact(s['end_elapsed_seconds_exact'], 's') > start and _exact(s['start_elapsed_seconds_exact'], 's') < end]


def _blob(store, manifest, field):
    size = manifest[field + '_bytes']
    _need(type(size) is int and 0 < size <= MAX, 'CAPACITY_HOLD: bounded lifecycle blob required')
    raw = store.get(manifest[field + '_sha256'], maximum=MAX)
    _need(len(raw) == size, 'HASH_HOLD: lifecycle blob bytes differ')
    return raw


def _source_state(prepared, p):
    inputs = prepared['lifecycle_initialization']; _closed(inputs, {'input_id', 'population_state', 'births', 'removals'})
    state = inputs['population_state']; _closed(state, {'model_version', 'time_origin_utc', 'at_elapsed_seconds_exact',
                                                     'initial_inventory_state', 'new_leaves', 'birth_inventory'})
    source = p['initialization']['initial_inventory']; inventory = state['initial_inventory_state']
    _closed(inventory, {'model_version', 'origin', 'time_origin_utc', 'at_elapsed_seconds_exact', 'initial_inventory', 'leaves'})
    _need(state['model_version'] == appearance.population.POPULATION_MODEL_VERSIONS['population']
          and state['new_leaves'] == [] and state['birth_inventory'] == []
          and state['time_origin_utc'] == inventory['time_origin_utc'] == source['time_origin_utc']
          and state['at_elapsed_seconds_exact'] == inventory['at_elapsed_seconds_exact'] == source['at_elapsed_seconds_exact']
          and inventory['model_version'] == appearance.population.MODEL_VERSIONS['inventory'] and inventory['origin'] == 'synthetic',
          'STATE_HOLD: original initial population required')
    refs = [{'leaf_id': d['initialization']['clock_state']['leaf_id'], 'attachment_internode_id': d['attachment_internode_id']} for d in source['leaves']]
    _need(inventory['initial_inventory'] == {'at_elapsed_seconds_exact': source['at_elapsed_seconds_exact'], 'leaf_attachments': refs}
          and type(inventory['leaves']) is list and len(inventory['leaves']) == len(refs), 'STATE_HOLD: original initial inventory required')
    for item, declaration in zip(inventory['leaves'], source['leaves'], strict=True):
        _closed(item, {'attachment_internode_id', 'state'})
        _need(item['attachment_internode_id'] == declaration['attachment_internode_id'], 'ATTACHMENT_HOLD: initial attachment differs')
        appearance.population._leaf_state(item['state'], declaration['initialization'], source['time_origin_utc'], source['at_elapsed_seconds_exact'])
        _need(item['state']['clock_state'] == item['state']['clock_anchor']
              and item['state']['area_state']['area'] == item['state']['area_state']['anchor']['canonical_area'],
              'STATE_HOLD: original initial leaf checkpoint required')
    return state


def _receipt(declaration, state):
    return {'declaration_sha256': _digest(declaration), 'last_leaf_state_sha256': _digest(state),
            'at_elapsed_seconds_exact': deepcopy(declaration['at_elapsed_seconds_exact']), 'area': deepcopy(state['area_state']['area'])}


def _initial_lifecycle(source, births, removals):
    leaves = source['initial_inventory_state']['leaves']; ids = {x['state']['clock_state']['leaf_id'] for x in leaves}
    existing_removals = [d for d in removals if d['leaf_id'] in ids]; by_leaf = {d['leaf_id']: d for d in existing_removals}
    checkpoints = []
    for item in leaves:
        current = item['state']; declaration = by_leaf.get(current['clock_state']['leaf_id'])
        immediate = declaration is not None and declaration['at_elapsed_seconds_exact'] == source['at_elapsed_seconds_exact']
        checkpoints.append({'state': deepcopy(current), 'removal_receipt': _receipt(declaration, current) if immediate else None})
    existing = {'model_version': INVENTORY_VERSION, 'source_population': deepcopy(source), 'source_population_sha256': _digest(source),
        'removal_declarations': deepcopy(existing_removals), 'removal_declarations_sha256': _digest(existing_removals),
        'at_elapsed_seconds_exact': deepcopy(source['at_elapsed_seconds_exact']), 'leaf_checkpoints': checkpoints}
    return {'model_version': LIFECYCLE_VERSION, 'existing_inventory_state': existing,
        'birth_declarations': deepcopy(births), 'birth_declarations_sha256': _digest(births),
        'removal_declarations': deepcopy(removals), 'removal_declarations_sha256': _digest(removals),
        'new_leaf_checkpoints': [{'state': None, 'removal_receipt': None} for _ in births]}


def _context(directory, access, store, root):
    m = _parse(store.get(root, maximum=MAX), MAX); _closed(m, ROOT_FIELDS)
    _need(all(_canonical(m[k]) == _canonical(v) for k, v in ROOT_CONSTANTS.items()), 'MODEL_HOLD: supported lifecycle manifest required')
    _closed(m['code_sha256'], SOURCE_PATHS)
    for value in m['code_sha256'].values(): _hash(value)
    a_raw = _blob(store, m, 'appearance_program'); mgmt_raw = _blob(store, m, 'management_program')
    p = appearance.program.parse_leaf_appearance_program(program_raw=a_raw)
    management = program.parse_leaf_lifecycle_management_program(program_raw=mgmt_raw)
    prepared = _parse(_blob(store, m, 'preparation'), MAX); _closed(prepared, PREPARATION_FIELDS)
    _need(management['appearance_program_sha256'] == m['appearance_program_sha256'] and p['stem']['artifact_sha256'] == m['stem_artifact_sha256']
          and p['stem']['program_sha256'] == m['stem_program_sha256'], 'HASH_HOLD: lifecycle original program linkage differs')
    parent = appearance.stem._load_manifest(store, m['stem_artifact_sha256'])
    _need(parent['program_sha256'] == m['stem_program_sha256'] and all(m['code_sha256'][k] == v for k, v in parent['code_sha256'].items()),
          'CODE_HOLD: original stem and lifecycle sources differ')
    original = _parse(store.get(parent['program_sha256'], maximum=PROGRAM_MAX), PROGRAM_MAX)
    appearance.stem.read_rational_morphology_frame(directory, access, m['stem_artifact_sha256'], index=len(parent['samples']) - 1)
    final = _parse(store.get(parent['samples'][-1]['result_sha256'], maximum=MAX), MAX)['state']
    old_meta = {'source_program_sha256': m['appearance_program_sha256'], 'stem_artifact_sha256': m['stem_artifact_sha256']}
    derived = appearance._derivation(p, old_meta, original, final, parent); bindings = appearance._initial_bindings(p, original)
    generated = {'schema_version': 'leaf-population-software-program-v1', 'origin': 'synthetic', 'program_id': p['program_id'],
        'rights': p['rights'], 'stem': p['stem'], 'initialization': p['initialization'],
        'births': derived['leaf_inputs']['births'], 'display_policy': appearance.population.POPULATION_DISPLAY_POLICY}
    appearance.population._program(generated, original)
    source = _source_state(prepared, p); old_pins = {k: m['code_sha256'][k] for k in appearance.PREPARATION_SOURCES}
    old_prepared = {'model_version': appearance.PREPARATION_VERSION, **FLAGS, 'model_versions': appearance.PREPARATION_MODELS,
        'input_sha256': _digest({'model_version': appearance.PREPARATION_VERSION, 'source_program_sha256': m['appearance_program_sha256'], 'code_sha256': old_pins}),
        'source_program_sha256': m['appearance_program_sha256'], 'source_program_bytes': len(a_raw),
        'generated_program_sha256': _digest(generated), 'generated_program': generated, 'initial_state_sha256': _digest(source),
        'initial_bindings_sha256': _digest(bindings), 'initial_bindings': bindings,
        'derivation_sha256': _digest(derived), 'derivation': derived, 'display_policy': p['display_policy'], 'code_sha256': old_pins}
    births = generated['births']; removals = management['removals']; forcing = derived['leaf_inputs']['segments']
    start = forcing[0]['start_elapsed_seconds_exact']; end = forcing[-1]['end_elapsed_seconds_exact']
    ids = {d['initialization']['clock_state']['leaf_id']: source['at_elapsed_seconds_exact'] for d in p['initialization']['initial_inventory']['leaves']}
    ids.update({d['leaf_id']: d['emerged_elapsed_seconds_exact'] for d in births})
    for d in removals:
        _need(d['leaf_id'] in ids and d['time_origin_utc'] == source['time_origin_utc'], 'SCOPE_HOLD: original lifecycle removal identity required')
        _need(_exact(ids[d['leaf_id']], 's') <= _exact(d['at_elapsed_seconds_exact'], 's') <= _exact(end, 's'),
              'TIME_HOLD: removal before emergence or beyond original horizon')
    _need(all(s['air_temperature']['value'] >= d['initialization']['clock_state']['base_temperature']['value']
              for d in p['initialization']['initial_inventory']['leaves'] for s in forcing), 'THERMAL_DOMAIN_HOLD: original preparation range required')
    inputs = {'input_id': _digest({'appearance_program_sha256': m['appearance_program_sha256'],
        'management_program_sha256': m['management_program_sha256'], 'operation': 'initialize-lifecycle'}),
        'population_state': source, 'births': births, 'removals': removals}
    initial = _initial_lifecycle(source, births, removals); pins = {k: m['code_sha256'][k] for k in PREPARATION_SOURCES}
    expected = {'model_version': PREPARATION_VERSION, **FLAGS, 'model_versions': PREPARATION_MODELS,
        'input_sha256': _digest({'model_version': PREPARATION_VERSION, 'appearance_program_sha256': m['appearance_program_sha256'],
                               'management_program_sha256': m['management_program_sha256'], 'code_sha256': pins}),
        'appearance_program_sha256': m['appearance_program_sha256'], 'appearance_program_bytes': len(a_raw),
        'management_program_sha256': m['management_program_sha256'], 'management_program_bytes': len(mgmt_raw),
        'management_program_id': management['program_id'], 'appearance_preparation_sha256': _digest(old_prepared),
        'appearance_preparation': old_prepared, 'lifecycle_initialization': inputs, 'lifecycle_initialization_sha256': _digest(inputs),
        'initial_state_sha256': _digest(initial), 'stem': p['stem'], 'time_origin_utc': source['time_origin_utc'],
        'start_elapsed_seconds_exact': start, 'end_elapsed_seconds_exact': end, 'forcing': forcing,
        'source_rights': {'appearance': p['rights'], 'management': management['rights'], 'stem': parent['program_rights']},
        'display_policy': program.DISPLAY_POLICY, 'code_sha256': pins}
    _need(_canonical(prepared) == _canonical(expected), 'HASH_HOLD: original lifecycle preparation evidence differs')
    _need(_blob(store, m, 'initial_state') == _canonical(initial) and m['time_origin_utc'] == source['time_origin_utc']
          and m['initial_at_elapsed_seconds_exact'] == start and _canonical(m['source_rights']) == _canonical(expected['source_rights']),
          'HASH_HOLD: original lifecycle initial state, rights or time differs')
    samples = m['samples']; previous = m['initial_state_sha256']
    _need(type(samples) is list and len(samples) == len(parent['samples']), 'FORMAT_HOLD: complete lifecycle sample chain required')
    for i, (d, original_sample) in enumerate(zip(samples, parent['samples'], strict=True)):
        _closed(d, DESCRIPTOR_FIELDS)
        _need(type(d['index']) is int and d['index'] == i and d['at'] == original_sample['at']
              and d['stem_result_sha256'] == original_sample['result_sha256'] and d['input_state_sha256'] == previous,
              'HASH_HOLD: original lifecycle/stem sample chain differs')
        _need(type(d['result_bytes']) is int and 0 < d['result_bytes'] <= MAX, 'CAPACITY_HOLD: bounded lifecycle result required')
        for k in DESCRIPTOR_FIELDS - {'index', 'at', 'result_bytes'}: _hash(d[k])
        previous = d['state_sha256']
    _need(m['terminal_state_sha256'] == previous, 'HASH_HOLD: lifecycle terminal chain differs')
    return m, prepared, p, parent, initial


def _new_initial(event, origin):
    return {'clock_state': {'origin': 'synthetic', 'age_basis': 'since_leaf_emergence', 'temperature_basis': 'indoor_air_piecewise_constant',
        'leaf_id': event['leaf_id'], 'time_origin_utc': origin, 'emerged_elapsed_seconds_exact': event['emerged_elapsed_seconds_exact'],
        'at_elapsed_seconds_exact': event['emerged_elapsed_seconds_exact'], 'base_temperature': event['base_temperature'],
        'age_exact': {'numerator': '0', 'denominator': '1', 'unit': 'degC_day'}},
        **{k: event[k] for k in ['curve', 'normalization', 'initial_area']}}


def _frame_data(result, prepared, p, stem):
    _closed(result, RESULT_FIELDS)
    _need(result['model_version'] == LIFECYCLE_VERSION and all(result[k] == v for k, v in FLAGS.items()), 'MODEL_HOLD: stored lifecycle result required')
    _hash(result['input_sha256']); state = result['state']; _closed(state, STATE_FIELDS)
    inputs = prepared['lifecycle_initialization']; births = inputs['births']; removals = inputs['removals']; source = inputs['population_state']
    origin = prepared['time_origin_utc']; at = appearance._seconds(appearance.population._seconds(stem['at'], origin)); now = _exact(at, 's')
    _need(result['time_origin_utc'] == stem['time_origin_utc'] == origin and result['at_elapsed_seconds_exact'] == at
          and state['model_version'] == LIFECYCLE_VERSION and state['birth_declarations'] == births
          and state['birth_declarations_sha256'] == _digest(births) and state['removal_declarations'] == removals
          and state['removal_declarations_sha256'] == _digest(removals), 'STATE_HOLD: original lifecycle declarations/time required')
    existing = state['existing_inventory_state']; _closed(existing, EXISTING_FIELDS)
    declared = p['initialization']['initial_inventory']['leaves']; initial_ids = {d['initialization']['clock_state']['leaf_id'] for d in declared}
    existing_removals = [d for d in removals if d['leaf_id'] in initial_ids]
    _need(existing['model_version'] == INVENTORY_VERSION and _canonical(existing['source_population']) == _canonical(source)
          and existing['source_population_sha256'] == _digest(source) and existing['removal_declarations'] == existing_removals
          and existing['removal_declarations_sha256'] == _digest(existing_removals) and existing['at_elapsed_seconds_exact'] == at,
          'STATE_HOLD: original existing-leaf source required')
    _need(type(existing['leaf_checkpoints']) is list and len(existing['leaf_checkpoints']) == len(declared)
          and type(state['new_leaf_checkpoints']) is list and len(state['new_leaf_checkpoints']) == len(births),
          'STATE_HOLD: complete original leaf checkpoint lists required')
    active = []; removed = []; pending = []; tracked = []; by_leaf = {d['leaf_id']: d for d in removals}; parents = {d['internode_id']: d for d in stem['internodes']}
    def append(checkpoint, initial, attachment):
        _closed(checkpoint, {'state', 'removal_receipt'}); identifier = initial['clock_state']['leaf_id']; declaration = by_leaf.get(identifier)
        retired = declaration is not None and _exact(declaration['at_elapsed_seconds_exact'], 's') <= now
        last = declaration['at_elapsed_seconds_exact'] if retired else at
        row = {'attachment_internode_id': attachment, **appearance.population._leaf_state(checkpoint['state'], initial, origin, last)}
        tracked.append(row)
        _need(attachment in parents and _exact(parents[attachment]['emerged_elapsed_seconds_exact'], 's') <= _exact(row['emerged_elapsed_seconds_exact'], 's') <= now,
              'ATTACHMENT_HOLD: original selected stem position required')
        if retired:
            _need(_canonical(checkpoint['removal_receipt']) == _canonical(_receipt(declaration, checkpoint['state'])), 'HASH_HOLD: original removed last-state receipt required')
            removed.append({**row, 'last_at_elapsed_seconds_exact': deepcopy(last), 'removal_declaration': deepcopy(declaration)})
        else:
            _need(checkpoint['removal_receipt'] is None, 'STATE_HOLD: live leaf cannot have removal receipt'); active.append(row)
    for d, checkpoint in zip(declared, existing['leaf_checkpoints'], strict=True): append(checkpoint, d['initialization'], d['attachment_internode_id'])
    emerged = 0
    for d, checkpoint in zip(births, state['new_leaf_checkpoints'], strict=True):
        _closed(checkpoint, {'state', 'removal_receipt'})
        if _exact(d['emerged_elapsed_seconds_exact'], 's') > now:
            _need(checkpoint['state'] is None and checkpoint['removal_receipt'] is None, 'STATE_HOLD: pending leaf has current state')
            pending.append({k: deepcopy(d[k]) for k in ['leaf_id', 'attachment_internode_id', 'emerged_elapsed_seconds_exact']})
        else:
            emerged += 1; append(checkpoint, _new_initial(d, origin), d['attachment_internode_id'])
    counts = {'declared_leaf_count': len(declared) + len(births), 'tracked_leaf_count': len(active) + len(removed),
        'active_leaf_count': len(active), 'removed_leaf_count': len(removed), 'scheduled_birth_count': len(births),
        'emerged_new_leaf_count': emerged, 'pending_leaf_count': len(pending)}
    _need(all(type(result[k]) is int and result[k] == v for k, v in counts.items()), 'STATE_HOLD: stored lifecycle counts differ')
    for name, rows in [('active', active), ('removed', removed), ('pending', pending)]:
        _need(result[name + '_leaf_ids'] == [d['leaf_id'] for d in rows], 'STATE_HOLD: stored lifecycle IDs differ')
    for name, rows in [('active_leaf_area', active), ('removed_leaf_area', removed), ('last_tracked_leaf_area', tracked)]:
        _quantity(result[name], 'm2')
        try: total = fsum(d['area']['value'] for d in rows)
        except OverflowError: raise LeafLifecycleReadHold('NUMERIC_HOLD: stored area sum overflow') from None
        _need(isfinite(total) and result[name]['value'] == total, 'STATE_HOLD: stored lifecycle area sum differs')
    return {**{k: deepcopy(result[k]) for k in COUNT_FIELDS | AREA_FIELDS}, 'at_elapsed_seconds_exact': at,
            'active_leaves': active, 'removed_leaves': removed, 'pending_leaves': pending}


def _recheck(store, root, m, parent):
    for field in ['appearance_program', 'management_program', 'preparation', 'initial_state']: _blob(store, m, field)
    for digest in {root, m['stem_artifact_sha256'], *(d['result_sha256'] for d in parent['samples']), *(d['result_sha256'] for d in m['samples'])}:
        store.get(digest, maximum=MAX)
    store.get(m['stem_program_sha256'], maximum=PROGRAM_MAX)


def read_leaf_lifecycle_manifest(directory, access, root_sha256):
    try:
        with MorphologyBlobStore(directory, access) as store:
            m, _, _, parent, _ = _context(directory, access, store, root_sha256)
            _recheck(store, root_sha256, m, parent); return m
    except (MorphologyArtifactHold, appearance.program.LeafAppearanceProgramHold) as exc:
        raise LeafLifecycleReadHold(str(exc)) from None


def read_leaf_lifecycle_frame(directory, access, root_sha256, *, index):
    try:
        _need(type(index) is int and index >= 0, 'INDEX_HOLD: explicit lifecycle integer index required')
        with MorphologyBlobStore(directory, access) as store:
            m, prepared, p, parent, initial = _context(directory, access, store, root_sha256)
            _need(index < len(m['samples']), 'INDEX_HOLD: bounded lifecycle index required'); d = m['samples'][index]
            raw = _blob(store, d, 'result'); result = _parse(raw, MAX)
            _need(_digest(result.get('state')) == d['state_sha256'] and result.get('input_sha256') == d['input_sha256'], 'HASH_HOLD: original lifecycle result required')
            stem = appearance.stem.read_rational_morphology_frame(directory, access, m['stem_artifact_sha256'], index=index)
            data = _frame_data(result, prepared, p, stem); before = initial
            if index:
                previous = _parse(_blob(store, m['samples'][index - 1], 'result'), MAX)
                previous_stem = appearance.stem.read_rational_morphology_frame(directory, access, m['stem_artifact_sha256'], index=index - 1)
                _frame_data(previous, prepared, p, previous_stem); before = previous['state']
            _need(_digest(before) == d['input_state_sha256'], 'HASH_HOLD: original lifecycle input state differs')
            inputs = {'input_id': _digest({'management_program_sha256': m['management_program_sha256'], 'at': d['at']}), 'state': before,
                'segments': _clip(prepared['forcing'], _exact(before['existing_inventory_state']['at_elapsed_seconds_exact'], 's'), _exact(data['at_elapsed_seconds_exact'], 's'))}
            _need(result['input_sha256'] == _digest({'model_version': LIFECYCLE_VERSION, 'operation': 'advance', 'inputs': inputs}),
                  'HASH_HOLD: original lifecycle advancement input differs')
            frame = {'schema_version': 'leaf-lifecycle-replay-frame-v1', **FLAGS, 'artifact_sha256': root_sha256,
                'result_sha256': d['result_sha256'], 'input_sha256': result['input_sha256'], 'index': index, 'at': d['at'],
                'time_origin_utc': m['time_origin_utc'], **data, 'stem': stem,
                **{k: m[k] for k in ['appearance_program_sha256', 'management_program_sha256', 'preparation_sha256', 'display_policy']}}
            _need(len(_canonical(frame)) <= MAX, 'CAPACITY_HOLD: bounded lifecycle frame required')
            _recheck(store, root_sha256, m, parent); return frame
    except (MorphologyArtifactHold, appearance.program.LeafAppearanceProgramHold) as exc:
        raise LeafLifecycleReadHold(str(exc)) from None
