"""Immutable synthetic appearance provenance wrapped around stored population math."""
from hashlib import sha256
from pathlib import Path

from . import crop_leaf_appearance_preparation as preparation
from . import crop_leaf_appearance_program as program
from . import crop_leaf_population_artifact_producer as population
from . import crop_leaf_population_artifact_reader as reader
from .crop_morphology_artifact_io import MorphologyArtifactHold, MorphologyBlobStore, _need
from .crop_morphology_artifact_reader import _canonical


MODEL_VERSION = 'leaf-appearance-artifact-producer-research-v1'
SOURCE_PATHS = (*preparation.SOURCE_PATHS, 'backend/app/crop_leaf_appearance_artifact_producer.py')
ROOT_CONSTANTS = {
    'schema_version': 'leaf-appearance-research-artifact-v1',
    'status': 'completed_software_fixture', 'scope': 'software_research_only',
    'claim_scope': 'synthetic_crop_math_only', 'gates': 'not_assessed',
    'time_kind': 'synthetic_model_clock_not_observation',
    'parameter_scope': 'synthetic_software_fixture_only',
    'model_versions': {**preparation.MODEL_VERSIONS, 'population_producer': population.MODEL_VERSION,
                       'appearance_producer': MODEL_VERSION},
    'display_policy': program.DISPLAY_POLICY,
}


class LeafAppearanceArtifactHold(MorphologyArtifactHold):
    pass


def _code_pins():
    root = Path(__file__).resolve().parents[2]
    try:
        return {name: sha256((root/name).read_bytes()).hexdigest() for name in SOURCE_PATHS}
    except OSError:
        raise LeafAppearanceArtifactHold('CODE_HOLD: appearance producer source unavailable') from None


def _verified_calculation(directory, access, root, prepared, pins):
    manifest = reader.read_leaf_population_manifest(directory, access, root)
    generated = _canonical(prepared['generated_program'])
    with MorphologyBlobStore(directory, access) as store:
        _need(store.get(manifest['program_sha256'], maximum=program.MAX) == generated
              and manifest['program_sha256'] == prepared['generated_program_sha256']
              and manifest['initial_state_sha256'] == prepared['initial_state_sha256']
              and all(pins[name] == digest for name,digest in manifest['code_sha256'].items()),
              'HASH_HOLD: prepared program and original calculation differ')
    for index in range(len(manifest['samples'])):
        reader.read_leaf_population_frame(directory, access, root, index=index)
    return manifest


def produce_leaf_appearance_artifact(directory, access, *, stem_directory, program_raw):
    try:
        _need(Path(directory).resolve() != Path(stem_directory).resolve(),
              'STORAGE_HOLD: separate appearance directory required')
        p = program.parse_leaf_appearance_program(program_raw=program_raw); pins = _code_pins()
        prepared = preparation.prepare_leaf_appearance_program(stem_directory, access, program_raw=program_raw)
        _need(all(pins[name] == digest for name,digest in prepared['code_sha256'].items())
              and _code_pins() == pins, 'CODE_HOLD: appearance sources changed before calculation')
        generated_raw = _canonical(prepared['generated_program'])
        inner_root = population.produce_leaf_population_artifact(directory, access,
            stem_directory=stem_directory, program_raw=generated_raw)
        prepared_raw = _canonical(prepared)
        with MorphologyBlobStore(directory, access, write=True) as store:
            source_sha = store.put(program_raw, maximum=program.MAX)
            prepared_sha = store.put(prepared_raw, maximum=program.MAX)
            _need(preparation.prepare_leaf_appearance_program(stem_directory, access, program_raw=program_raw) == prepared,
                  'HASH_HOLD: original appearance preparation changed before completion')
            inner = _verified_calculation(directory, access, inner_root, prepared, pins)
            _need(store.get(source_sha, maximum=program.MAX) == program_raw
                  and store.get(prepared_sha, maximum=program.MAX) == prepared_raw,
                  'HASH_HOLD: original appearance evidence changed before completion')
            _need(_code_pins() == pins, 'CODE_HOLD: appearance sources changed before completion')
            manifest = {**ROOT_CONSTANTS, 'source_program_sha256': source_sha, 'source_program_bytes': len(program_raw),
                'preparation_sha256': prepared_sha, 'preparation_bytes': len(prepared_raw),
                'generated_program_sha256': prepared['generated_program_sha256'], 'generated_program_bytes': len(generated_raw),
                'population_artifact_sha256': inner_root, 'stem_artifact_sha256': p['stem']['artifact_sha256'],
                'stem_program_sha256': p['stem']['program_sha256'], 'program_rights': p['rights'], 'code_sha256': pins,
                'time_origin_utc': inner['time_origin_utc'],
                'initial_at_elapsed_seconds_exact': inner['initial_at_elapsed_seconds_exact'],
                'initial_state_sha256': inner['initial_state_sha256'], 'terminal_state_sha256': inner['terminal_state_sha256'],
                'sample_count': len(inner['samples'])}
            return store.put(_canonical(manifest), maximum=program.MAX)
    except (MorphologyArtifactHold, program.LeafAppearanceProgramHold, preparation.LeafAppearancePreparationHold) as exc:
        raise LeafAppearanceArtifactHold(str(exc)) from None
