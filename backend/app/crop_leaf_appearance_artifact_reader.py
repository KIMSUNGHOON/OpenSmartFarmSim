"""Compute-free validation of appearance provenance and stored numeric frames."""
from copy import deepcopy
from datetime import timedelta
from hashlib import sha256

from . import crop_leaf_appearance_program as program
from . import crop_leaf_population_artifact_reader as population
from . import crop_rational_morphology_artifact_reader as stem
from .crop_morphology_artifact_io import MorphologyArtifactHold, MorphologyBlobStore, _need
from .crop_morphology_artifact_reader import FLAGS, _canonical, _closed, _hash, _parse, _utc


MODEL_VERSION = 'leaf-appearance-artifact-reader-research-v1'
BIRTH_VERSION = 'stored-shoot-leaf-birth-inputs-research-v1'
PREPARATION_VERSION = 'leaf-appearance-program-preparation-research-v1'
DERIVATION_MODELS = {'stem': 'morphology-research-artifact-v2', 'timeline': 'shoot-air-phytomer-timeline-research-v1',
    'kind': 'phytomer-kind-research-v1', 'air_adapter': 'whole-second-utc-to-rational-air-segments-research-v1',
    'leaf': 'leaf-rational-air-area-state-research-v1', 'declared_births': 'declared-leaf-births-research-v1'}
PREPARATION_MODELS = {**DERIVATION_MODELS, 'birth_inputs': BIRTH_VERSION,
    'population': population.POPULATION_MODEL_VERSIONS['population'], 'preparation': PREPARATION_VERSION}
PREPARATION_SOURCES = (*population.SOURCE_PATHS, *(f'backend/app/{name}.py' for name in (
    'crop_phytomer_kind', 'crop_stored_shoot_leaf_birth_inputs', 'crop_leaf_appearance_program', 'crop_leaf_appearance_preparation')))
SOURCE_PATHS = (*PREPARATION_SOURCES, 'backend/app/crop_leaf_appearance_artifact_producer.py')
ROOT_CONSTANTS = {**FLAGS, 'schema_version': 'leaf-appearance-research-artifact-v1',
    'status': 'completed_software_fixture', 'time_kind': 'synthetic_model_clock_not_observation',
    'parameter_scope': 'synthetic_software_fixture_only',
    'model_versions': {**PREPARATION_MODELS, 'population_producer': 'leaf-population-artifact-producer-research-v1',
                       'appearance_producer': 'leaf-appearance-artifact-producer-research-v1'},
    'display_policy': program.DISPLAY_POLICY}
ROOT_FIELDS = set(ROOT_CONSTANTS) | {'source_program_sha256', 'source_program_bytes', 'preparation_sha256', 'preparation_bytes',
    'generated_program_sha256', 'generated_program_bytes', 'population_artifact_sha256', 'stem_artifact_sha256',
    'stem_program_sha256', 'program_rights', 'code_sha256', 'time_origin_utc', 'initial_at_elapsed_seconds_exact',
    'initial_state_sha256', 'terminal_state_sha256', 'sample_count'}


class LeafAppearanceReadHold(MorphologyArtifactHold):
    pass


def _digest(value):
    return sha256(_canonical(value)).hexdigest()


def _seconds(value):
    return {'numerator': str(value), 'denominator': '1', 'unit': 's'}


def _kind(sequence, policy):
    first = policy['first_generative_sequence']
    return 'generative' if sequence >= first and (sequence-first) % (policy['vegetative_between_generative']+1) == 0 else 'vegetative'


def _profile(source):
    result = deepcopy(source)
    for quantity in [result['base_temperature'], result['initial_area'], *result['curve']['values'].values()]:
        quantity['value'] = float(quantity['value'])
    return result


def _initial_bindings(p, original):
    leaves = p['initialization']['initial_inventory']['leaves']; policy = p['policy']
    nodes = original['initial_state']['internodes']; timeline = original['initial_state']['timeline_state']
    _need(policy['shoot_id'] == timeline['shoot_id'] and policy['schedule_id'] == timeline['schedule_id'],
          'SCOPE_HOLD: original appearance policy schedule differs')
    expected = [n['length_state']['clock_state']['internode_id'] for n in nodes if _kind(n['sequence'], policy) == 'vegetative']
    _need([leaf['attachment_internode_id'] for leaf in leaves] == expected,
          'INITIAL_BINDING_HOLD: ordered initial vegetative leaves required')
    by_parent = {leaf['attachment_internode_id']: leaf['initialization']['clock_state'] for leaf in leaves}; bindings = []
    for node in nodes:
        parent = node['length_state']['clock_state']; leaf = by_parent.get(parent['internode_id'])
        _need(leaf is None or leaf['emerged_elapsed_seconds_exact'] == parent['emerged_elapsed_seconds_exact'],
              'INITIAL_BINDING_HOLD: original initial leaf birth differs')
        bindings.append({'sequence': node['sequence'], 'kind': _kind(node['sequence'], policy),
            'internode_id': parent['internode_id'], 'birth_age_exact': node['birth_age_exact'],
            'emerged_elapsed_seconds_exact': parent['emerged_elapsed_seconds_exact'], 'leaf_id': None if leaf is None else leaf['leaf_id']})
    return bindings


def _initial_state(first_state, at):
    state = deepcopy(first_state); state['at_elapsed_seconds_exact'] = deepcopy(at)
    state['new_leaves'] = []; state['birth_inventory'] = []
    inventory = state['initial_inventory_state']; inventory['at_elapsed_seconds_exact'] = deepcopy(at)
    for item in inventory['leaves']:
        leaf = item['state']; leaf['clock_state'] = deepcopy(leaf['clock_anchor']); area = leaf['area_state']
        area['age_exact'] = deepcopy(leaf['clock_anchor']['age_exact']); area['area'] = deepcopy(area['anchor']['canonical_area'])
    return state


def _derivation(p, m, original, final_state, parent):
    checkpoint = original['initial_state']['timeline_state']; origin = checkpoint['started_at']
    identifier = _digest({'source_program_sha256': m['source_program_sha256'], 'operation': 'derive-leaf-births'})
    policy_sha = _digest({'model_version': DERIVATION_MODELS['kind'], 'policy': p['policy']})
    profile = _profile(p['leaf_profile']); segments = [{**s, 'air_temperature': {'value': float(s['air_temperature']['value']), 'unit': 'degC'}}
        for s in original['segments']]
    forcing = [{'start_elapsed_seconds_exact': _seconds(population._seconds(s['start_utc'], origin)),
        'end_elapsed_seconds_exact': _seconds(population._seconds(s['end_utc'], origin)), 'air_temperature': s['air_temperature']} for s in segments]
    events = []; declarations = []
    for node in final_state['internodes'][len(original['initial_state']['internodes']):]:
        clock = node['length_state']['clock_state']; birth = clock['emerged_elapsed_seconds_exact']; seconds = stem._fraction(birth)
        kind = _kind(node['sequence'], p['policy']); leaf_id = None
        if kind == 'vegetative':
            leaf_id = 'leaf:'+_digest({'model_version': BIRTH_VERSION, 'stem_program_sha256': parent['program_sha256'],
                'policy_sha256': policy_sha, 'sequence': node['sequence'], 'attachment_internode_id': clock['internode_id']})
            declarations.append({'leaf_id': leaf_id, 'attachment_internode_id': clock['internode_id'],
                'emerged_elapsed_seconds_exact': birth, **deepcopy(profile)})
        utc = None if seconds.denominator != 1 else (_utc(origin)+timedelta(seconds=seconds.numerator)).isoformat().replace('+00:00', 'Z')
        events.append({'sequence': node['sequence'], 'thermal_age_exact': node['birth_age_exact'],
            'elapsed_seconds_exact': birth, 'utc_whole_second': utc, 'kind': kind, 'attachment_internode_id': clock['internode_id'], 'leaf_id': leaf_id})
    inputs = {'input_id': identifier, 'policy': p['policy'], 'leaf_profile': p['leaf_profile']}
    normalized = {**checkpoint, 'base_temperature': {'value': float(checkpoint['base_temperature']['value']), 'unit': 'degC'}}
    return {'model_version': BIRTH_VERSION, **FLAGS, 'model_versions': DERIVATION_MODELS,
        'input_sha256': _digest({'model_version': BIRTH_VERSION, 'model_versions': DERIVATION_MODELS,
            'stem_artifact_sha256': m['stem_artifact_sha256'], 'start_index': -1, 'end_index': len(parent['samples'])-1, 'inputs': inputs}),
        'stem_artifact_sha256': m['stem_artifact_sha256'], 'stem_program_sha256': parent['program_sha256'],
        'start_index': -1, 'end_index': len(parent['samples'])-1, 'start_state_sha256': parent['initial_state_sha256'],
        'end_state_sha256': parent['terminal_state_sha256'], 'policy_sha256': policy_sha,
        'timeline_input_sha256': _digest({'model_version': DERIVATION_MODELS['timeline'],
            'air_segment_version': stem.MODEL_VERSIONS['whole_second_air'], 'emergence_version': stem.MODEL_VERSIONS['emergence'],
            'inputs': {'input_id': identifier, 'state': normalized, 'segments': segments}}),
        'leaf_profile_sha256': _digest({'model_version': BIRTH_VERSION, 'leaf_profile': profile}),
        'policy': p['policy'], 'time_origin_utc': origin, 'timeline_checkpoint': final_state['timeline_state'],
        'start_elapsed_seconds_exact': forcing[0]['start_elapsed_seconds_exact'],
        'end_elapsed_seconds_exact': forcing[-1]['end_elapsed_seconds_exact'], 'events': events,
        'leaf_inputs': {'input_id': identifier, 'origin': 'synthetic', 'time_origin_utc': origin, 'segments': forcing, 'births': declarations}}


def _blob(store, m, field):
    size = m[field+'_bytes']; _need(type(size) is int and 0 < size <= program.MAX, 'CAPACITY_HOLD: bounded original appearance bytes required')
    raw = store.get(m[field+'_sha256'], maximum=program.MAX)
    _need(len(raw) == size, 'HASH_HOLD: appearance byte count differs'); return raw


def _load(directory, access, store, root):
    m = _parse(store.get(root, maximum=program.MAX), program.MAX); _closed(m, ROOT_FIELDS)
    _need(all(_canonical(m[k]) == _canonical(v) for k,v in ROOT_CONSTANTS.items()), 'MODEL_HOLD: supported appearance manifest required')
    pins = m['code_sha256']; _closed(pins, SOURCE_PATHS)
    for value in pins.values(): _hash(value)
    p = program.parse_leaf_appearance_program(program_raw=_blob(store, m, 'source_program'))
    prepared = _parse(_blob(store, m, 'preparation'), program.MAX); generated = _blob(store, m, 'generated_program')
    inner = population.read_leaf_population_manifest(directory, access, m['population_artifact_sha256'])
    _need(_canonical(m['program_rights']) == _canonical(p['rights']) == _canonical(inner['program_rights'])
          and m['stem_artifact_sha256'] == p['stem']['artifact_sha256'] == inner['stem_artifact_sha256']
          and m['stem_program_sha256'] == p['stem']['program_sha256'] == inner['stem_program_sha256']
          and m['generated_program_sha256'] == inner['program_sha256']
          and generated == store.get(inner['program_sha256'], maximum=program.MAX)
          and all(pins[k] == v for k,v in inner['code_sha256'].items()), 'HASH_HOLD: original appearance/population linkage differs')
    for key in ['time_origin_utc', 'initial_at_elapsed_seconds_exact', 'initial_state_sha256', 'terminal_state_sha256']:
        _need(m[key] == inner[key], 'HASH_HOLD: original appearance state/UTC differs')
    _need(type(m['sample_count']) is int and m['sample_count'] == len(inner['samples']), 'FORMAT_HOLD: complete appearance frame count required')
    parent = stem._load_manifest(store, m['stem_artifact_sha256'])
    _need(all(pins[k] == v for k,v in parent['code_sha256'].items()), 'CODE_HOLD: original stem and appearance sources differ')
    original = _parse(store.get(parent['program_sha256'], maximum=program.MAX), program.MAX)
    stem.read_rational_morphology_frame(directory, access, m['stem_artifact_sha256'], index=m['sample_count']-1)
    final_state = _parse(store.get(parent['samples'][-1]['result_sha256'], maximum=program.MAX), program.MAX)['state']
    population.read_leaf_population_frame(directory, access, m['population_artifact_sha256'], index=0)
    first_state = _parse(store.get(inner['samples'][0]['result_sha256'], maximum=program.MAX), program.MAX)['state']
    initial = _digest(_initial_state(first_state, m['initial_at_elapsed_seconds_exact']))
    _need(initial == m['initial_state_sha256'], 'HASH_HOLD: original initial clock/area anchors differ')
    derived = _derivation(p, m, original, final_state, parent); bindings = _initial_bindings(p, original)
    generated_expected = {'schema_version': 'leaf-population-software-program-v1', 'origin': 'synthetic',
        'program_id': p['program_id'], 'rights': p['rights'], 'stem': p['stem'], 'initialization': p['initialization'],
        'births': derived['leaf_inputs']['births'], 'display_policy': population.POPULATION_DISPLAY_POLICY}
    _need(generated == _canonical(generated_expected), 'HASH_HOLD: original generated appearance declarations differ')
    preparation_pins = {key: pins[key] for key in PREPARATION_SOURCES}
    expected = {'model_version': PREPARATION_VERSION, **FLAGS, 'model_versions': PREPARATION_MODELS,
        'input_sha256': _digest({'model_version': PREPARATION_VERSION, 'source_program_sha256': m['source_program_sha256'], 'code_sha256': preparation_pins}),
        'source_program_sha256': m['source_program_sha256'], 'source_program_bytes': m['source_program_bytes'],
        'generated_program_sha256': m['generated_program_sha256'], 'generated_program': generated_expected,
        'initial_state_sha256': initial, 'initial_bindings_sha256': _digest(bindings), 'initial_bindings': bindings,
        'derivation_sha256': _digest(derived), 'derivation': derived, 'display_policy': p['display_policy'], 'code_sha256': preparation_pins}
    _need(_canonical(prepared) == _canonical(expected), 'HASH_HOLD: original appearance preparation evidence differs')
    return m, prepared, inner, parent


def _recheck(store, root, m, inner, parent):
    digests = {root, m['source_program_sha256'], m['preparation_sha256'], m['generated_program_sha256'],
        m['population_artifact_sha256'], m['stem_artifact_sha256'], m['stem_program_sha256']}
    digests.update(d['result_sha256'] for d in parent['samples'])
    digests.update(d[key] for d in inner['samples'] for key in ['result_sha256', 'binding_sha256'])
    for digest in digests: store.get(digest, maximum=program.MAX)


def read_leaf_appearance_manifest(directory, access, root_sha256):
    try:
        with MorphologyBlobStore(directory, access) as store:
            m, _, inner, parent = _load(directory, access, store, root_sha256)
            _recheck(store, root_sha256, m, inner, parent); return m
    except (MorphologyArtifactHold, program.LeafAppearanceProgramHold) as exc:
        raise LeafAppearanceReadHold(str(exc)) from None


def read_leaf_appearance_frame(directory, access, root_sha256, *, index):
    try:
        _need(type(index) is int and index >= 0, 'INDEX_HOLD: explicit integer appearance index required')
        with MorphologyBlobStore(directory, access) as store:
            m, prepared, inner, parent = _load(directory, access, store, root_sha256)
            _need(index < m['sample_count'], 'INDEX_HOLD: bounded appearance frame index required')
            frame = population.read_leaf_population_frame(directory, access, m['population_artifact_sha256'], index=index)
            frame = {**frame, 'schema_version': 'leaf-appearance-replay-frame-v1', 'artifact_sha256': root_sha256,
                'population_artifact_sha256': m['population_artifact_sha256'], 'source_program_sha256': m['source_program_sha256'],
                'preparation_sha256': m['preparation_sha256'], 'policy_sha256': prepared['derivation']['policy_sha256'],
                'leaf_profile_sha256': prepared['derivation']['leaf_profile_sha256'], 'display_policy': m['display_policy']}
            _need(len(_canonical(frame)) <= program.MAX, 'CAPACITY_HOLD: bounded appearance frame required')
            _recheck(store, root_sha256, m, inner, parent); return frame
    except (MorphologyArtifactHold, program.LeafAppearanceProgramHold) as exc:
        raise LeafAppearanceReadHold(str(exc)) from None
