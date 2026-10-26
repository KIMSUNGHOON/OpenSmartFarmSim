"""Canonical initial-internode lengths at ages derived from stored dynamic air."""
from copy import deepcopy
from hashlib import sha256
from math import fsum, isfinite
from pathlib import Path

from . import crop_funded_shoot_clock as clock
from . import crop_internode_length as point
from . import crop_rational_internode_length as initial
from .crop_morphology_artifact_io import MorphologyArtifactHold, MorphologyBlobStore, _need
from .crop_morphology_artifact_reader import _canonical

MODEL_VERSION = 'funded-air-initial-internode-lengths-research-v1'
CODE_SHA256 = sha256(Path(__file__).read_bytes()).hexdigest()
MAX_BYTES = 2*1024**2


class FundedInternodeLengthsHold(MorphologyArtifactHold):
    pass


def _digest(value): return sha256(_canonical(value)).hexdigest()


def _pins():
    root = Path(__file__).resolve().parents[2]
    names = dict.fromkeys((*clock.stem.SOURCE_PATHS, *clock.leaf.SOURCE_PATHS,
        'backend/app/crop_funded_shoot_clock.py', 'backend/app/crop_funded_internode_lengths.py'))
    return {name: sha256((root/name).read_bytes()).hexdigest() for name in names}


def _fence():
    _need(sha256(Path(__file__).read_bytes()).hexdigest() == CODE_SHA256, 'CODE_HOLD: original funded internode lengths required')


def calculate_funded_initial_internode_lengths(leaf_directory, stem_directory, access, *, leaf_root_sha256, stem_root_sha256):
    try:
        _fence(); pins = _pins()
        ages = clock.derive_funded_shoot_clock(leaf_directory, stem_directory, access,
            leaf_root_sha256=leaf_root_sha256, stem_root_sha256=stem_root_sha256)
        stem = clock.stem.read_rational_morphology_manifest(stem_directory, access, stem_root_sha256)
        leaf = clock.leaf.read_funded_leaf_manifest(leaf_directory, access, leaf_root_sha256)
        _need(ages['stem_program_sha256'] == stem['program_sha256'] and ages['source_rights'] == {
            'leaf': leaf['source_rights'], 'stem': stem['program_rights']}, 'HASH_HOLD: original clock/source declarations required')
        with MorphologyBlobStore(stem_directory, access) as store:
            raw = store.get(stem['program_sha256'], maximum=clock.stem.PROGRAM_MAX)
            program = clock.stem._parse(raw, clock.stem.PROGRAM_MAX); nodes = program['initial_state']['internodes']
            normalized = [initial.normalize_rational_internode_length_state(state=node['length_state']) for node in nodes]
            node_hashes = [_digest(node['length_state']) for node in nodes]
            previous_ages = [clock.stem._fraction(state['clock_state']['age_exact']) for state in normalized]
            frames = []; frame_bytes = 2
            for index, source in enumerate(ages['frames']):
                _need(source['index'] == index and len(source['initial_internodes']) == len(nodes), 'SCOPE_HOLD: complete ordered initial-node clocks required')
                current = []
                for i, (node, age) in enumerate(zip(nodes, source['initial_internodes'], strict=True)):
                    state = node['length_state']; origin = state['clock_state']
                    _need(age['internode_id'] == origin['internode_id'] and age['emerged_elapsed_seconds_exact'] == origin['emerged_elapsed_seconds_exact'],
                          'HASH_HOLD: original initial-node identity required')
                    clock.stem._age(age['age_exact']); value = clock.stem._fraction(age['age_exact'])
                    _need(value >= previous_ages[i], 'AGE_HOLD: reversing initial-node growth unsupported')
                    receipt = point.calculate_internode_length_point(inputs={'input_id': _digest({
                        'model_version': MODEL_VERSION, 'stem_program_sha256': stem['program_sha256'], 'internode_id': age['internode_id']}),
                        'origin': 'synthetic', 'thermal_age_basis': 'since_internode_emergence', 'age_exact': age['age_exact'], 'curve': state['curve']})
                    _need(receipt['curve_sha256'] == state['curve_sha256'], 'HASH_HOLD: original length curve required')
                    if index == 0:
                        _need(age['age_exact'] == origin['age_exact'] and receipt['length'] == state['length'], 'STATE_HOLD: original initial length required')
                    current.append({'sequence': node['sequence'], 'internode_id': age['internode_id'],
                        'emerged_elapsed_seconds_exact': deepcopy(age['emerged_elapsed_seconds_exact']), 'age_exact': deepcopy(age['age_exact']),
                        'curve_sha256': state['curve_sha256'], 'initial_state_sha256': node_hashes[i],
                        'point_input_sha256': receipt['input_sha256'], 'length': receipt['length']})
                    previous_ages[i] = value
                total = fsum(item['length']['value'] for item in current)
                _need(isfinite(total) and total > 0, 'NUMERIC_HOLD: finite positive initial-axis total required')
                frames.append({**{k: v for k, v in source.items() if k != 'initial_internodes'}, 'internodes': current,
                    'tracked_initial_axis_length': {'value': total, 'unit': 'm'}})
                frame_bytes += len(_canonical(frames[-1]))+1
                _need(frame_bytes <= MAX_BYTES, 'CAPACITY_HOLD: bounded initial-length trajectory required')
            result = {'model_version': MODEL_VERSION, 'scope': 'software_research_only', 'G0_G4': 'not_assessed',
                'claim_scope': 'sampled_numerical_air_initial_internode_lengths_only', 'leaf_artifact_sha256': leaf_root_sha256,
                'stem_artifact_sha256': stem_root_sha256, 'stem_program_sha256': stem['program_sha256'],
                'stem_initial_state_sha256': stem['initial_state_sha256'], 'clock_calculation_sha256': _digest(ages),
                'clock_model_version': clock.MODEL_VERSION, 'point_model_version': point.POINT_VERSION,
                'code_sha256': CODE_SHA256, 'source_code_sha256': pins, 'time_origin_utc': ages['time_origin_utc'], 'shoot_id': ages['shoot_id'],
                'source_rights': ages['source_rights'], 'original_internodes': deepcopy(nodes),
                'new_internode_events': 'not_calculated', 'leaf_attachment': 'not_bound', 'spatial_pose': 'not_calculated', 'frames': frames}
            _need(len(_canonical(result)) <= MAX_BYTES, 'CAPACITY_HOLD: bounded initial-length result required')
            _need(store.get(stem['program_sha256'], maximum=clock.stem.PROGRAM_MAX) == raw, 'HASH_HOLD: original initial stem program changed')
        _need(clock.leaf.read_funded_leaf_manifest(leaf_directory, access, leaf_root_sha256) == leaf
              and clock.stem.read_rational_morphology_manifest(stem_directory, access, stem_root_sha256) == stem,
              'HASH_HOLD: original sources changed before return')
        _need(_pins() == pins, 'CODE_HOLD: original calculation sources changed before return'); _fence()
        return deepcopy(result)
    except (OSError, ValueError, TypeError, KeyError, AttributeError, OverflowError, RecursionError) as error:
        raise FundedInternodeLengthsHold(str(error)) from None
