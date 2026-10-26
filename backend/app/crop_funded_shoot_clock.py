"""Derive initial shoot/node ages from original stored RK4 indoor-air integrals."""
from copy import deepcopy
from fractions import Fraction
from hashlib import sha256
from math import isfinite
from pathlib import Path

from . import crop_leaf_funded_birth_artifact_reader as leaf
from . import crop_rational_morphology_artifact_reader as stem
from .crop_morphology_artifact_io import MorphologyArtifactHold, MorphologyBlobStore, _need
from .crop_morphology_artifact_reader import _canonical

MODEL_VERSION = 'funded-air-initial-shoot-clock-research-v1'
POLICY = 'stored-rk4-air-integral-signed-no-clip-v1'
CODE_SHA256 = sha256(Path(__file__).read_bytes()).hexdigest()
MAX_BYTES = 2*1024**2


class FundedShootClockHold(MorphologyArtifactHold):
    pass


def _pins():
    root = Path(__file__).resolve().parents[2]
    return {name: sha256((root/name).read_bytes()).hexdigest() for name in stem.SOURCE_PATHS}


def _exact(value):
    result = {'numerator': str(value.numerator), 'denominator': str(value.denominator), 'unit': 'degC_day'}
    stem._age(result)
    return result


def _fence():
    _need(sha256(Path(__file__).read_bytes()).hexdigest() == CODE_SHA256, 'CODE_HOLD: original funded shoot clock required')


def derive_funded_shoot_clock(leaf_directory, stem_directory, access, *, leaf_root_sha256, stem_root_sha256):
    try:
        _fence(); pins = _pins()
        lm = leaf.read_funded_leaf_manifest(leaf_directory, access, leaf_root_sha256)
        sm = stem.read_rational_morphology_manifest(stem_directory, access, stem_root_sha256)
        _need(sm['code_sha256'] == pins, 'CODE_HOLD: original stem source required')
        _need(all(sm['program_rights'][k] is True and lm['source_rights'][k] is True for k in ('use','display')),
              'RIGHTS_HOLD: original source use/display declarations required')
        with MorphologyBlobStore(stem_directory, access) as store:
            raw = store.get(sm['program_sha256'], maximum=stem.PROGRAM_MAX)
            program = stem._parse(raw, stem.PROGRAM_MAX); initial = program['initial_state']; t = initial['timeline_state']
            _need(t['started_at'] == t['at'] == lm['time_origin_utc'], 'TIME_HOLD: common original initial clock required')
            base = t['base_temperature']['value']; initial_age = stem._fraction(t['age_exact'])
            nodes = initial['internodes']; _need(len(nodes) >= 1, 'SCOPE_HOLD: nonempty initial stem required')
            frames = []; frame_bytes = 2; previous_seconds = previous_integral = None
            for index in range(len(lm['samples'])):
                original = leaf.read_funded_leaf_frame(leaf_directory, access, leaf_root_sha256, index=index)
                elapsed = original['at']['elapsed_seconds_exact']; stem._elapsed(elapsed); seconds = stem._fraction(elapsed)
                row = original['integrated_transfers']['indoor_air_temperature_time']; value = row['value']
                _need(row['unit'] == 'degC_s' and type(value) is float and isfinite(value), 'UNIT_HOLD: original finite air integral required')
                if index == 0:
                    _need(seconds == 0 and value == 0., 'TIME_HOLD: original zero air prefix required')
                if seconds == previous_seconds:
                    _need(value == previous_integral, 'TIME_HOLD: no air time advances at a funding point')
                change = (Fraction.from_float(value)-Fraction.from_float(float(base))*seconds)/86400
                clocks = []
                for node in nodes:
                    clock = node['length_state']['clock_state']
                    _need(clock['base_temperature'] == t['base_temperature'], 'BASIS_HOLD: common declared stem base required')
                    clocks.append({'internode_id': clock['internode_id'], 'emerged_elapsed_seconds_exact': deepcopy(clock['emerged_elapsed_seconds_exact']),
                        'age_exact': _exact(stem._fraction(clock['age_exact'])+change)})
                frames.append({**{k: original[k] for k in ('index','step_index','phase','event_sequence','checkpoint_sha256','at')},
                    'air_temperature_integral': deepcopy(row), 'shoot_age_exact': _exact(initial_age+change), 'initial_internodes': clocks})
                frame_bytes += len(_canonical(frames[-1]))+1
                _need(frame_bytes <= MAX_BYTES, 'CAPACITY_HOLD: bounded clock trajectory required')
                previous_seconds, previous_integral = seconds, value
            result = {'model_version': MODEL_VERSION, 'policy': POLICY, 'scope': 'software_research_only', 'G0_G4': 'not_assessed',
                'claim_scope': 'stored_numerical_air_initial_shoot_clock_only', 'leaf_artifact_sha256': leaf_root_sha256,
                'stem_artifact_sha256': stem_root_sha256, 'stem_program_sha256': sm['program_sha256'],
                'stem_initial_state_sha256': sm['initial_state_sha256'], 'code_sha256': CODE_SHA256,
                'stem_code_sha256': pins, 'leaf_code_sha256': lm['code_sha256'],
                'time_origin_utc': lm['time_origin_utc'], 'shoot_id': t['shoot_id'], 'base_temperature': deepcopy(t['base_temperature']),
                'initial_shoot_age_exact': deepcopy(t['age_exact']), 'source_rights': {'leaf': lm['source_rights'], 'stem': sm['program_rights']},
                'stem_pose_after_initial': 'not_bound_to_this_clock', 'new_internode_events': 'not_calculated', 'frames': frames}
            _need(len(_canonical(result)) <= MAX_BYTES, 'CAPACITY_HOLD: bounded clock result required')
            _need(store.get(sm['program_sha256'], maximum=stem.PROGRAM_MAX) == raw, 'HASH_HOLD: original stem program changed')
        _need(leaf.read_funded_leaf_manifest(leaf_directory, access, leaf_root_sha256) == lm
              and stem.read_rational_morphology_manifest(stem_directory, access, stem_root_sha256) == sm,
              'HASH_HOLD: original source changed before return')
        _need(_pins() == pins, 'CODE_HOLD: stem source changed before return'); _fence()
        return deepcopy(result)
    except (OSError, ValueError, TypeError, KeyError, AttributeError, OverflowError, RecursionError) as error:
        raise FundedShootClockHold(str(error)) from None
