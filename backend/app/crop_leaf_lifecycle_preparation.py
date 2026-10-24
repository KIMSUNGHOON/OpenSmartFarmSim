"""Bind exact lifecycle initialization to original appearance and stored shoot inputs."""
from copy import deepcopy
from hashlib import sha256
from pathlib import Path

from . import crop_leaf_appearance_preparation as appearance
from . import crop_leaf_lifecycle as lifecycle
from . import crop_leaf_lifecycle_program as program
from .crop_morphology_artifact_io import MorphologyArtifactHold, MorphologyBlobStore, _need
from .crop_morphology_artifact_reader import _canonical, _parse, ROOT_MAX

MODEL_VERSION = 'leaf-lifecycle-program-preparation-research-v1'
SOURCE_PATHS = tuple(dict.fromkeys((*appearance.SOURCE_PATHS, *(f'backend/app/{name}.py' for name in (
    'crop_declared_leaf_removal', 'crop_leaf_removal_timeline', 'crop_leaf_removal_inventory', 'crop_leaf_lifecycle',
    'crop_leaf_lifecycle_program', 'crop_leaf_lifecycle_preparation')))))
MODEL_VERSIONS = {**appearance.MODEL_VERSIONS, 'appearance_preparation': appearance.MODEL_VERSION,
                  'removal_point': lifecycle.point.MODEL_VERSION, 'removal_timeline': lifecycle.single.MODEL_VERSION,
                  'removal_inventory': lifecycle.base.MODEL_VERSION, 'lifecycle': lifecycle.MODEL_VERSION,
                  'preparation': MODEL_VERSION}


class LeafLifecyclePreparationHold(MorphologyArtifactHold):
    pass


def _digest(value):
    return sha256(_canonical(value)).hexdigest()


def _code_pins():
    root = Path(__file__).resolve().parents[2]
    try:
        return {name: sha256((root/name).read_bytes()).hexdigest() for name in SOURCE_PATHS}
    except OSError:
        raise LeafLifecyclePreparationHold('CODE_HOLD: lifecycle preparation sources unavailable') from None


def prepare_leaf_lifecycle_program(stem_directory, access, *, appearance_program_raw, management_raw):
    try:
        m = program.parse_leaf_lifecycle_management_program(program_raw=management_raw)
        p = appearance.program.parse_leaf_appearance_program(program_raw=appearance_program_raw)
        appearance_sha = sha256(appearance_program_raw).hexdigest(); management_sha = sha256(management_raw).hexdigest()
        _need(m['appearance_program_sha256'] == appearance_sha, 'HASH_HOLD: management requires the original appearance program')
        pins = _code_pins()
        with MorphologyBlobStore(stem_directory, access) as store:
            root_raw = store.get(p['stem']['artifact_sha256'], maximum=ROOT_MAX)
            original = appearance.prepare_leaf_appearance_program(stem_directory, access, program_raw=appearance_program_raw)
            _need(original['source_program_sha256'] == appearance_sha
                  and all(pins[name] == digest for name, digest in original['code_sha256'].items()),
                  'CODE_HOLD: original appearance preparation scope changed')
            state = appearance.population.initialize_leaf_population(inputs=original['generated_program']['initialization'])['state']
            _need(_digest(state) == original['initial_state_sha256'], 'HASH_HOLD: original population initialization differs')
            forcing = deepcopy(original['derivation']['leaf_inputs']['segments'])
            lifecycle.point.births._forcing(forcing)
            start = forcing[0]['start_elapsed_seconds_exact']; end = forcing[-1]['end_elapsed_seconds_exact']
            _need(start == state['at_elapsed_seconds_exact'], 'TIME_HOLD: original forcing and initial population differ')
            for declaration in m['removals']:
                _need(lifecycle.single._seconds(start) <= lifecycle.single._seconds(declaration['at_elapsed_seconds_exact'])
                      <= lifecycle.single._seconds(end), 'TIME_HOLD: removal outside stored appearance horizon')
            inputs = {'input_id': _digest({'appearance_program_sha256': appearance_sha,
                       'management_program_sha256': management_sha, 'operation': 'initialize-lifecycle'}),
                      'population_state': state, 'births': deepcopy(original['generated_program']['births']),
                      'removals': deepcopy(m['removals'])}
            initialized = lifecycle.initialize_leaf_lifecycle(inputs=inputs)
            root = _parse(root_raw, ROOT_MAX)
            result = {'model_version': MODEL_VERSION, **appearance.stem.FLAGS, 'model_versions': dict(MODEL_VERSIONS),
                      'input_sha256': _digest({'model_version': MODEL_VERSION, 'appearance_program_sha256': appearance_sha,
                                              'management_program_sha256': management_sha, 'code_sha256': pins}),
                      'appearance_program_sha256': appearance_sha, 'appearance_program_bytes': len(appearance_program_raw),
                      'management_program_sha256': management_sha, 'management_program_bytes': len(management_raw),
                      'management_program_id': m['program_id'], 'appearance_preparation_sha256': _digest(original),
                      'appearance_preparation': original, 'lifecycle_initialization': inputs,
                      'lifecycle_initialization_sha256': _digest(inputs), 'initial_state_sha256': _digest(initialized['state']),
                      'stem': deepcopy(p['stem']), 'time_origin_utc': state['time_origin_utc'],
                      'start_elapsed_seconds_exact': deepcopy(start), 'end_elapsed_seconds_exact': deepcopy(end), 'forcing': forcing,
                      'source_rights': {'appearance': deepcopy(p['rights']), 'management': deepcopy(m['rights']),
                                        'stem': deepcopy(root['program_rights'])},
                      'display_policy': deepcopy(program.DISPLAY_POLICY), 'code_sha256': pins}
            _need(len(_canonical(result)) <= program.MAX, 'CAPACITY_HOLD: lifecycle preparation exceeds 2MiB')
            confirmed = appearance.prepare_leaf_appearance_program(stem_directory, access, program_raw=appearance_program_raw)
            _need(_canonical(confirmed) == _canonical(original), 'HASH_HOLD: original appearance preparation changed before return')
            _need(store.get(p['stem']['artifact_sha256'], maximum=ROOT_MAX) == root_raw, 'HASH_HOLD: original stem root changed')
            _need(_code_pins() == pins, 'CODE_HOLD: lifecycle preparation sources changed before return')
            return result
    except (MorphologyArtifactHold, lifecycle.LeafLifecycleHold, appearance.population.LeafPopulationHold,
            appearance.LeafAppearancePreparationHold, appearance.program.LeafAppearanceProgramHold) as exc:
        raise LeafLifecyclePreparationHold(str(exc)) from None
