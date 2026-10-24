"""Instantaneous explicit-LAI probe; crop-explicit-lai-photosynthesis-v1.md."""
from copy import deepcopy
from hashlib import sha256
import json
from math import isfinite
from pathlib import Path
import re

from . import crop_growth_rates as source

MODEL_VERSION = 'explicit-lai-vanthoor-photosynthesis-research-v1'
CODE_SHA256 = sha256(Path(__file__).read_bytes()).hexdigest()
COMPONENT_CODE_SHA256 = sha256(Path(source.__file__).read_bytes()).hexdigest()
UNITS = {'buffer': source.MASS_UNIT, 'leaf_area_index': 'm2_leaf/m2_floor', **source.FORCING_UNITS}


class ExplicitLaiPhotosynthesisHold(ValueError):
    pass


def _need(condition, reason):
    if not condition:
        raise ExplicitLaiPhotosynthesisHold(reason)


def _canonical(value):
    raw = json.dumps(value, sort_keys=True, separators=(',', ':'), ensure_ascii=False, allow_nan=False).encode()
    _need(len(raw) <= 128*1024, 'CAPACITY_HOLD: bounded explicit optical probe required')
    return raw


def calculate_photosynthesis(*, inputs, profile):
    try:
        raw = _canonical(inputs); captured = json.loads(raw)
        _need(type(captured) is dict and set(captured) == {'input_id', 'origin', 'values'},
              'INPUT_HOLD: closed optical probe required')
        _need(type(captured['input_id']) is str and re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9_.:/-]{0,199}', captured['input_id'])
              and captured['origin'] == 'synthetic', 'SCOPE_HOLD: bounded explicitly synthetic optical probe required')
        _need(type(profile) is source.ReferenceParameters, 'PROFILE_HOLD: pinned original reference profile required')
        v, normalized = source._block(captured, UNITS); p = profile.values
        _need(p['tCanMin'] <= v['canopy_temperature'] <= p['tCanMax'] and v['co2'] > 0,
              'INPUT_HOLD: original instantaneous canopy/CO2 domain required')
        photo, diagnostics = source._photosynthesis({'buffer': v['buffer']}, v, p, v['leaf_area_index'])
        _need(all(isfinite(number) for number in (photo, *[x for x in diagnostics.values() if x is not None]))
              and photo >= 0 and diagnostics['electron_transport'] >= 0, 'NUMERIC_HOLD: invalid optical response')
        identity = {'model_version': MODEL_VERSION, 'code_sha256': CODE_SHA256,
                    'component_code_sha256': COMPONENT_CODE_SHA256, 'profile_sha256': profile.sha256,
                    'source_model_version': source.MODEL_VERSION, 'inputs': normalized}
        result = {**identity, 'raw_input_sha256': sha256(raw).hexdigest(),
                  'input_sha256': sha256(_canonical(identity)).hexdigest(),
                  'lai': deepcopy(normalized['values']['leaf_area_index']), 'photosynthesis': source._quantity(photo),
                  'diagnostics': diagnostics, 'diagnostic_units': {'compensation_point_ppm': 'ppm',
                    'electron_transport': 'umol_electrons/m2_floor/s'},
                  'scope': 'software_research_only', 'claim_scope': 'synthetic_explicit_lai_photosynthesis_math_only',
                  'G0_G4': 'not_assessed'}
        _canonical(result)
        return result
    except ExplicitLaiPhotosynthesisHold:
        raise
    except source.CropRateHold as exc:
        raise ExplicitLaiPhotosynthesisHold(str(exc)) from None
    except (TypeError, ValueError, OverflowError, ZeroDivisionError, RecursionError):
        raise ExplicitLaiPhotosynthesisHold('INPUT_HOLD: invalid or unrepresentable optical probe') from None
