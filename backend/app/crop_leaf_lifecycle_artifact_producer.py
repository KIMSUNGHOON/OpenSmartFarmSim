"""Publish one separately versioned lifecycle graph; write completion last."""
from hashlib import sha256
from pathlib import Path

from . import crop_leaf_lifecycle as lifecycle
from . import crop_leaf_lifecycle_preparation as preparation
from . import crop_leaf_lifecycle_artifact_reader as reader
from .crop_morphology_artifact_io import MorphologyArtifactHold, MorphologyBlobStore, _need
from .crop_morphology_artifact_reader import _canonical, _parse, PROGRAM_MAX, ROOT_MAX

MODEL_VERSION = 'leaf-lifecycle-artifact-producer-research-v1'
SOURCE_PATHS = reader.SOURCE_PATHS


class LeafLifecycleArtifactHold(MorphologyArtifactHold):
    pass


def _code_pins():
    root = Path(__file__).resolve().parents[2]
    try: return {name: sha256((root/name).read_bytes()).hexdigest() for name in SOURCE_PATHS}
    except OSError: raise LeafLifecycleArtifactHold('CODE_HOLD: lifecycle producer source unavailable') from None


def produce_leaf_lifecycle_artifact(directory, access, *, stem_directory, appearance_program_raw, management_raw):
    try:
        _need(Path(directory).resolve() != Path(stem_directory).resolve(), 'STORAGE_HOLD: separate lifecycle directory required')
        pins = _code_pins()
        prepared = preparation.prepare_leaf_lifecycle_program(stem_directory, access,
            appearance_program_raw=appearance_program_raw, management_raw=management_raw)
        _need(all(pins[k] == v for k, v in prepared['code_sha256'].items()) and _code_pins() == pins, 'CODE_HOLD: prepared lifecycle sources differ')
        state = lifecycle.initialize_leaf_lifecycle(inputs=prepared['lifecycle_initialization'])['state']
        _need(reader._digest(state) == prepared['initial_state_sha256'], 'HASH_HOLD: lifecycle initialization changed')
        with MorphologyBlobStore(stem_directory, access) as original, MorphologyBlobStore(directory, access, write=True) as store:
            parent = reader.appearance.stem._load_manifest(original, prepared['stem']['artifact_sha256'])
            end = reader.appearance._seconds(reader.appearance.population._seconds(parent['samples'][-1]['at'], prepared['time_origin_utc']))
            _need(end == prepared['end_elapsed_seconds_exact'], 'TIME_HOLD: complete stored lifecycle horizon required')
            source_blobs = [(prepared['stem']['artifact_sha256'], ROOT_MAX), (parent['program_sha256'], PROGRAM_MAX),
                            *((d['result_sha256'], reader.MAX) for d in parent['samples'])]
            for digest, maximum in source_blobs:
                _need(store.put(original.get(digest, maximum=maximum), maximum=maximum) == digest, 'HASH_HOLD: original stem copy differs')
            a_sha = store.put(appearance_program_raw, maximum=reader.MAX); mgmt_sha = store.put(management_raw, maximum=reader.MAX)
            prepared_raw = _canonical(prepared); prepared_sha = store.put(prepared_raw, maximum=reader.MAX)
            initial_raw = _canonical(state); initial_sha = store.put(initial_raw, maximum=reader.MAX); samples = []
            p = preparation.appearance.program.parse_leaf_appearance_program(program_raw=appearance_program_raw)
            for index, descriptor in enumerate(parent['samples']):
                _need(_code_pins() == pins, 'CODE_HOLD: lifecycle source changed during calculation')
                before = reader._digest(state); start = reader._exact(state['existing_inventory_state']['at_elapsed_seconds_exact'], 's')
                stop = reader._exact(reader.appearance._seconds(reader.appearance.population._seconds(descriptor['at'], prepared['time_origin_utc'])), 's')
                result = lifecycle.advance_leaf_lifecycle(inputs={'input_id': reader._digest({'management_program_sha256': mgmt_sha, 'at': descriptor['at']}),
                    'state': state, 'segments': reader._clip(prepared['forcing'], start, stop)})
                stem = reader.appearance.stem.read_rational_morphology_frame(directory, access, prepared['stem']['artifact_sha256'], index=index)
                reader._frame_data(result, prepared, p, stem); state = result['state']; raw = _canonical(result)
                digest = store.put(raw, maximum=reader.MAX)
                samples.append({'index': index, 'at': descriptor['at'], 'result_sha256': digest, 'result_bytes': len(raw),
                    'input_state_sha256': before, 'state_sha256': reader._digest(state), 'input_sha256': result['input_sha256'],
                    'stem_result_sha256': descriptor['result_sha256']})
            _need(result['pending_leaf_count'] == 0, 'STATE_HOLD: complete scheduled lifecycle births required')
            confirmed = preparation.prepare_leaf_lifecycle_program(stem_directory, access,
                appearance_program_raw=appearance_program_raw, management_raw=management_raw)
            _need(_canonical(confirmed) == prepared_raw, 'HASH_HOLD: original lifecycle preparation changed before completion')
            for digest, maximum in source_blobs:
                _need(original.get(digest, maximum=maximum) == store.get(digest, maximum=maximum), 'HASH_HOLD: original stem changed before completion')
            for digest, raw in [(a_sha, appearance_program_raw), (mgmt_sha, management_raw), (prepared_sha, prepared_raw), (initial_sha, initial_raw)]:
                _need(store.get(digest, maximum=reader.MAX) == raw, 'HASH_HOLD: original lifecycle evidence changed before completion')
            for descriptor in samples: reader._blob(store, descriptor, 'result')
            _need(_code_pins() == pins, 'CODE_HOLD: lifecycle sources changed before completion')
            manifest = {**reader.ROOT_CONSTANTS, 'appearance_program_sha256': a_sha, 'appearance_program_bytes': len(appearance_program_raw),
                'management_program_sha256': mgmt_sha, 'management_program_bytes': len(management_raw),
                'preparation_sha256': prepared_sha, 'preparation_bytes': len(prepared_raw), 'source_rights': prepared['source_rights'],
                'stem_artifact_sha256': prepared['stem']['artifact_sha256'], 'stem_program_sha256': parent['program_sha256'],
                'code_sha256': pins, 'time_origin_utc': prepared['time_origin_utc'],
                'initial_at_elapsed_seconds_exact': prepared['start_elapsed_seconds_exact'],
                'initial_state_sha256': initial_sha, 'initial_state_bytes': len(initial_raw),
                'terminal_state_sha256': reader._digest(state), 'samples': samples}
            return store.put(_canonical(manifest), maximum=reader.MAX)
    except (MorphologyArtifactHold, lifecycle.LeafLifecycleHold) as exc:
        raise LeafLifecycleArtifactHold(str(exc)) from None
