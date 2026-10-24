"""Read-only tracked area normalization; crop-leaf-canopy-basis-v1.md."""
from copy import deepcopy
from hashlib import sha256
import json
from math import isfinite
from pathlib import Path
import re
from sys import float_info

from . import crop_leaf_lifecycle_artifact_reader as reader
from .crop_morphology_artifact_io import MorphologyArtifactHold

VERSION = 'stored-tracked-leaf-canopy-basis-research-v1'
MAX_BYTES = 128 * 1024
CODE_SHA256 = sha256(Path(__file__).read_bytes()).hexdigest()
READER_CODE_SHA256 = sha256(Path(reader.__file__).read_bytes()).hexdigest()
INPUT_FIELDS = {'schema_version', 'input_id', 'origin', 'evidence_level', 'evidence_id',
                'artifact_sha256', 'index', 'floor_area'}
SOURCE_FIELDS = ('artifact_sha256', 'result_sha256', 'input_sha256', 'appearance_program_sha256',
                 'management_program_sha256', 'preparation_sha256')


class LeafCanopyBasisHold(ValueError):
    pass


def _need(condition, reason):
    if not condition:
        raise LeafCanopyBasisHold(reason)


def _canonical(value):
    try:
        raw = json.dumps(value, sort_keys=True, separators=(',', ':'), ensure_ascii=False, allow_nan=False).encode()
    except (ValueError, TypeError, OverflowError, RecursionError):
        raise LeafCanopyBasisHold('INPUT_HOLD: finite bounded JSON required') from None
    _need(len(raw) <= MAX_BYTES, 'CAPACITY_HOLD: bounded canopy basis required')
    return raw


def _input(inputs):
    _need(type(inputs) is dict and set(inputs) == INPUT_FIELDS, 'INPUT_HOLD: closed canopy basis required')
    _need(inputs['schema_version'] == 'leaf-canopy-basis-input-v1' and inputs['origin'] == 'synthetic'
          and inputs['evidence_level'] == 'assumed', 'INPUT_HOLD: explicit synthetic assumed floor basis required')
    for key in ('input_id', 'evidence_id'):
        _need(type(inputs[key]) is str and re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9_.:/-]{0,199}', inputs[key]),
              'INPUT_HOLD: bounded ASCII basis identifier required')
    _need(type(inputs['artifact_sha256']) is str and re.fullmatch(r'[0-9a-f]{64}', inputs['artifact_sha256']),
          'HASH_HOLD: explicit lifecycle root required')
    _need(type(inputs['index']) is int and 0 <= inputs['index'] < 512, 'INDEX_HOLD: bounded integer index required')
    q = inputs['floor_area']
    _need(type(q) is dict and set(q) == {'value', 'unit'}, 'INPUT_HOLD: closed floor area required')
    _need(q['unit'] == 'm2_floor', 'UNIT_HOLD: model footprint in m2_floor required')
    _need(type(q['value']) in (int, float), 'INPUT_HOLD: explicit numeric floor area required')
    try:
        floor = float(q['value'])
    except OverflowError:
        raise LeafCanopyBasisHold('NUMERIC_HOLD: floor area overflow') from None
    _need(isfinite(floor) and floor >= float_info.min, 'NUMERIC_HOLD: positive normal finite floor area required')
    return floor, _canonical(inputs)


def calculate_stored_leaf_canopy_basis(directory, access, *, inputs):
    floor, raw = _input(inputs)
    captured = json.loads(raw)
    _need(sha256(Path(__file__).read_bytes()).hexdigest() == CODE_SHA256
          and sha256(Path(reader.__file__).read_bytes()).hexdigest() == READER_CODE_SHA256,
          'CODE_HOLD: original canopy basis and reader required')
    try:
        frame = reader.read_leaf_lifecycle_frame(directory, access, captured['artifact_sha256'], index=captured['index'])
    except MorphologyArtifactHold as exc:
        raise LeafCanopyBasisHold(str(exc)) from None
    area = frame['active_leaf_area']['value']
    lai = area / floor
    _need(isfinite(lai) and (area == 0 or lai >= float_info.min),
          'NUMERIC_HOLD: finite normal positive tracked LAI required')
    result = {'schema_version': VERSION, 'scope': 'software_research_only',
              'claim_scope': 'synthetic_tracked_leaf_lai_math_only', 'gates': 'not_assessed',
              'canopy_use': 'tracked_inventory_comparison_only', 'code_sha256': CODE_SHA256,
              'reader_code_sha256': READER_CODE_SHA256, 'inputs': captured,
              'input_sha256': sha256(raw).hexdigest(), 'source': {key: frame[key] for key in SOURCE_FIELDS},
              **{key: deepcopy(frame[key]) for key in ('index', 'at', 'time_origin_utc', 'at_elapsed_seconds_exact',
                 'active_leaf_count', 'removed_leaf_count', 'pending_leaf_count', 'active_leaf_area')},
              **{kind + '_leaf_ids': [row['leaf_id'] for row in frame[kind + '_leaves']]
                 for kind in ('active', 'removed', 'pending')},
              'floor_area': {'value': floor, 'unit': 'm2_floor'},
              'tracked_leaf_area_index': {'value': lai, 'unit': 'm2_leaf/m2_floor'}}
    _canonical(result)
    return result
