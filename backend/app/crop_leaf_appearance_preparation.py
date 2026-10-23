"""Bind an appearance policy and initial inventory to one original shoot program."""
from copy import deepcopy
from hashlib import sha256
from pathlib import Path

from . import crop_leaf_appearance_program as program
from . import crop_leaf_population as population
from . import crop_leaf_population_artifact_reader as legacy
from . import crop_phytomer_kind as kinds
from . import crop_rational_morphology_artifact_reader as stem
from . import crop_stored_shoot_leaf_birth_inputs as derive
from .crop_morphology_artifact_io import MorphologyArtifactHold, MorphologyBlobStore, _need
from .crop_morphology_artifact_reader import _canonical, _parse, PROGRAM_MAX, RESULT_MAX


MODEL_VERSION = 'leaf-appearance-program-preparation-research-v1'
MODEL_VERSIONS = {**derive.MODEL_VERSIONS, 'birth_inputs': derive.MODEL_VERSION,
    'population': population.MODEL_VERSION, 'preparation': MODEL_VERSION}
SOURCE_PATHS = tuple(dict.fromkeys((*legacy.SOURCE_PATHS, *(f'backend/app/{name}.py' for name in (
    'crop_phytomer_kind', 'crop_stored_shoot_leaf_birth_inputs', 'crop_leaf_appearance_program', 'crop_leaf_appearance_preparation')))))


class LeafAppearancePreparationHold(ValueError):
    pass


def _digest(value):
    return sha256(_canonical(value)).hexdigest()


def _code_pins():
    root = Path(__file__).resolve().parents[2]
    try:
        return {name: sha256((root/name).read_bytes()).hexdigest() for name in SOURCE_PATHS}
    except OSError:
        raise LeafAppearancePreparationHold('CODE_HOLD: appearance preparation source unavailable') from None


def _verify_sample_bytes(store, manifest):
    for descriptor in manifest['samples']:
        raw = store.get(descriptor['result_sha256'], maximum=RESULT_MAX)
        _need(len(raw) == descriptor['result_bytes'], 'HASH_HOLD: original sample bytes differ')


def _initial_bindings(p, original, state):
    timeline = original['initial_state']['timeline_state']; policy = p['policy']
    _need(policy['shoot_id'] == timeline['shoot_id'] and policy['schedule_id'] == timeline['schedule_id'],
          'SCOPE_HOLD: original shoot and initial policy differ')
    _need(state['time_origin_utc'] == timeline['started_at']
          and legacy._exact(state['at_elapsed_seconds_exact'], 's') == legacy._seconds(timeline['at'], timeline['started_at']),
          'TIME_HOLD: initial leaves and original shoot differ')
    nodes = original['initial_state']['internodes']
    typed = kinds.classify_phytomer_sequences(inputs={'input_id': p['program_id'], 'policy': policy,
        'sequences': [n['sequence'] for n in nodes]})
    expected = [n['length_state']['clock_state']['internode_id'] for n, t in zip(nodes, typed['phytomers'], strict=True)
                if t['kind'] == 'vegetative']
    leaves = state['initial_inventory_state']['leaves']
    _need([item['attachment_internode_id'] for item in leaves] == expected,
          'INITIAL_BINDING_HOLD: exactly one ordered leaf per initial vegetative position required')
    by_parent = {item['attachment_internode_id']: item['state']['clock_state'] for item in leaves}
    result = []
    for node, item in zip(nodes, typed['phytomers'], strict=True):
        parent = node['length_state']['clock_state']; leaf = by_parent.get(parent['internode_id'])
        if leaf is not None:
            _need(leaf['emerged_elapsed_seconds_exact'] == parent['emerged_elapsed_seconds_exact'],
                  'INITIAL_BINDING_HOLD: leaf and original phytomer birth differ')
        result.append({'sequence': node['sequence'], 'kind': item['kind'], 'internode_id': parent['internode_id'],
            'birth_age_exact': deepcopy(node['birth_age_exact']),
            'emerged_elapsed_seconds_exact': deepcopy(parent['emerged_elapsed_seconds_exact']),
            'leaf_id': None if leaf is None else leaf['leaf_id']})
    return result


def prepare_leaf_appearance_program(stem_directory, access, *, program_raw):
    try:
        p = program.parse_leaf_appearance_program(program_raw=program_raw); pins = _code_pins()
        source_sha = sha256(program_raw).hexdigest()
        with MorphologyBlobStore(stem_directory, access) as store:
            manifest = stem._load_manifest(store, p['stem']['artifact_sha256'])
            _need(manifest['program_sha256'] == p['stem']['program_sha256'], 'HASH_HOLD: original stem program required')
            _need(all(pins[name] == digest for name, digest in manifest['code_sha256'].items()),
                  'CODE_HOLD: original stem calculation sources differ')
            original = _parse(store.get(manifest['program_sha256'], maximum=PROGRAM_MAX), PROGRAM_MAX)
            _verify_sample_bytes(store, manifest)
            state = population.initialize_leaf_population(inputs=p['initialization'])['state']
            initial = _initial_bindings(p, original, state)
            _need(_code_pins() == pins, 'CODE_HOLD: appearance sources changed before derivation')
            derivation = derive.build_leaf_birth_inputs_from_stored_shoot(stem_directory, access,
                p['stem']['artifact_sha256'], start_index=-1, end_index=len(manifest['samples'])-1,
                inputs={'input_id': _digest({'source_program_sha256': source_sha, 'operation': 'derive-leaf-births'}),
                        'policy': p['policy'], 'leaf_profile': p['leaf_profile']})
            forcing = derivation['leaf_inputs']['segments']
            _need(all(segment['air_temperature']['value'] >= item['state']['clock_state']['base_temperature']['value']
                for item in state['initial_inventory_state']['leaves'] for segment in forcing),
                'THERMAL_DOMAIN_HOLD: future air below initial leaf base unsupported')
            generated = {'schema_version': 'leaf-population-software-program-v1', 'origin': 'synthetic',
                'program_id': p['program_id'], 'rights': deepcopy(p['rights']), 'stem': deepcopy(p['stem']),
                'initialization': deepcopy(p['initialization']), 'births': deepcopy(derivation['leaf_inputs']['births']),
                'display_policy': deepcopy(legacy.POPULATION_DISPLAY_POLICY)}
            legacy._program(generated, original)
            result = {'model_version': MODEL_VERSION, **stem.FLAGS, 'model_versions': dict(MODEL_VERSIONS),
                'input_sha256': _digest({'model_version': MODEL_VERSION, 'source_program_sha256': source_sha, 'code_sha256': pins}),
                'source_program_sha256': source_sha, 'source_program_bytes': len(program_raw),
                'generated_program_sha256': _digest(generated), 'generated_program': generated,
                'initial_state_sha256': _digest(state), 'initial_bindings_sha256': _digest(initial), 'initial_bindings': initial,
                'derivation_sha256': _digest(derivation), 'derivation': derivation,
                'display_policy': deepcopy(p['display_policy']), 'code_sha256': pins}
            _need(len(_canonical(result)) <= program.MAX, 'CAPACITY_HOLD: appearance preparation exceeds 2MiB')
            stem._load_manifest(store, p['stem']['artifact_sha256']); _verify_sample_bytes(store, manifest)
            _need(_code_pins() == pins, 'CODE_HOLD: appearance sources changed before return')
            return result
    except (MorphologyArtifactHold, program.LeafAppearanceProgramHold, derive.LeafBirthInputsHold,
            population.LeafPopulationHold, kinds.PhytomerKindHold) as exc:
        raise LeafAppearancePreparationHold(str(exc)) from None
