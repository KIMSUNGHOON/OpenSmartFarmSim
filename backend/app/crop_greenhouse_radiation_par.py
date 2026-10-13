"""Prescribed solar PAR only; see crop-greenhouse-radiation-par-v1.md.

Equation attribution: crop-par-primary-source-review-20261013.md and
LICENSES/GreenLight-BSD-3-Clause-Clear.txt.
"""
from hashlib import sha256
import json
from math import exp, expm1, fsum, isfinite, ulp
from pathlib import Path

from .crop_growth_rates import ReferenceParameters

VERSION = 'prescribed-solar-par-boundary-research-v1'
CODE_SHA256 = sha256(Path(__file__).read_bytes()).hexdigest()
SOURCE_SHA256 = 'c0fb7a025533f15b80cb6cd60aafdc19be9fe42df6b8183cf97b83fc086138b3'
NOTICE_SHA256 = '96ce8c1f3d7b5473f473417c2785c63b74148edaddc2b9b6d40a6bbe3b7f4b6a'
HEAT = 'W/m2_floor'
PHOTONS = 'umol_photons/m2_floor/s'
INPUT_UNITS = {'outdoor_global_radiation': HEAT, 'leaf_area_index': 'm2_leaf/m2_floor',
    'solar_par_fraction': '1', 'solar_par_photon_conversion': 'umol_photons/J_PAR',
    'cover_par_transmittance': '1', 'cover_par_reflectance': '1',
    'construction_interception_fraction': '1'}
POLICY = {'spectrum': 'solar_PAR_only_explicit_conversion',
    'crop_interface': 'incident_photons_interception_in_unchanged_crop',
    'optics': 'pinned_crop_single_floor_reflection',
    'remainder': 'unresolved_no_further_bounces_or_heat_credit',
    'heat': 'absorbed_PAR_only_no_NIR_or_total_solar_claim', 'balance_ulps': 32}


class RadiationPARHold(ValueError):
    """The prescribed research calculation cannot support this input."""


def _need(condition, reason):
    if not condition:
        raise RadiationPARHold(reason)


def _hash(value):
    return sha256(json.dumps(value, sort_keys=True, separators=(',', ':'), allow_nan=False).encode()).hexdigest()


def _product(*values):
    if 0 in values:
        return 0.0
    result = 1.0
    for value in values:
        result *= value
        _need(isfinite(result) and result > 0, 'NUMERIC_HOLD: product overflow or underflow')
    return result


def _prepare(scenario):
    _need(type(scenario) is dict and set(scenario) == {'input_id', 'origin', 'values'},
          'INPUT_HOLD: closed scenario required')
    _need(type(scenario['input_id']) is str and 1 <= len(scenario['input_id']) <= 200
          and bool(scenario['input_id'].strip()) and type(scenario['origin']) is str
          and scenario['origin'] in ('synthetic', 'reference_calculation'),
          'INPUT_HOLD: explicit research provenance required')
    rows = scenario['values']
    _need(type(rows) is dict and set(rows) == set(INPUT_UNITS), 'INPUT_HOLD: explicit quantities required')
    numbers = {}
    for name, unit in INPUT_UNITS.items():
        row = rows[name]
        _need(type(row) is dict and set(row) == {'value', 'unit'}, 'INPUT_HOLD: closed quantity required')
        _need(type(row['unit']) is str and row['unit'] == unit, 'UNIT_HOLD: ' + name)
        _need(type(row['value']) in (int, float), 'INPUT_HOLD: numeric quantity required')
        try:
            value = float(row['value'])
        except OverflowError as exc:
            raise RadiationPARHold('NUMERIC_HOLD: unrepresentable input') from exc
        _need(isfinite(value) and value >= 0, 'INPUT_HOLD: finite nonnegative quantity required')
        _need(unit != '1' or value <= 1, 'OPTICS_HOLD: fraction outside [0,1]')
        numbers[name] = value
    _need(numbers['solar_par_photon_conversion'] > 0, 'INPUT_HOLD: positive photon conversion required')
    _need(fsum((numbers['cover_par_transmittance'], numbers['cover_par_reflectance'])) <= 1,
          'OPTICS_HOLD: cover transmission plus reflection exceeds one')
    normalized = {**scenario, 'values': {k: {'value': v, 'unit': INPUT_UNITS[k]} for k, v in numbers.items()}}
    return numbers, normalized


def _attenuation(coefficient, lai):
    depth = _product(coefficient, lai)
    transmitted, intercepted = exp(-depth), -expm1(-depth)
    _need(transmitted > 0 and (depth == 0 or intercepted > 0),
          'NUMERIC_HOLD: attenuation or interception underflow')
    return transmitted, intercepted


def calculate_par(*, scenario, profile):
    """Return incident photons, absorbed PAR heat and a bounded optical partition."""
    _need(type(profile) is ReferenceParameters, 'PROFILE_HOLD: pinned crop profile required')
    f, normalized = _prepare(scenario)
    p = profile.values
    t1, a1 = _attenuation(p['k1Par'], f['leaf_area_index'])
    t2, a2 = _attenuation(p['k2Par'], f['leaf_area_index'])
    outside = _product(f['outdoor_global_radiation'], f['solar_par_fraction'])
    transmitted = _product(outside, f['cover_par_transmittance'])
    above = _product(transmitted, 1-f['construction_interception_fraction'])
    down = _product(above, 1-p['rhoCanPar'], a1)
    floor_up = _product(above, t1, p['rhoFlrPar'])
    up = _product(floor_up, 1-p['rhoCanPar'], a2)
    canopy = fsum((down, up))
    floor = _product(above, t1, 1-p['rhoFlrPar'])
    unresolved = fsum((_product(above, p['rhoCanPar'], a1),
                       _product(floor_up, p['rhoCanPar'], a2)))
    upward = _product(floor_up, t2)
    interior = {'canopy_absorbed': canopy, 'floor_absorbed': floor,
        'unresolved_reflected': unresolved, 'upward_transmitted': upward}
    exterior = {'cover_reflected': _product(outside, f['cover_par_reflectance']),
        'cover_absorbed': _product(outside, 1-fsum((f['cover_par_transmittance'], f['cover_par_reflectance']))),
        'construction_intercepted': _product(transmitted, f['construction_interception_fraction']), **interior}
    residuals, budgets = {}, {}
    for name, incoming, partition in (('interior', above, interior), ('exterior_PAR', outside, exterior)):
        residual = fsum((incoming, *(-v for v in partition.values())))
        budget = 32*ulp(max(incoming, *partition.values()))
        _need(all(isfinite(v) and v >= 0 for v in partition.values()) and abs(residual) <= budget,
              'BALANCE_HOLD: unresolved PAR partition')
        residuals[name], budgets[name] = residual, budget
    photon_above = _product(above, f['solar_par_photon_conversion'])
    photon_absorbed = _product(canopy, f['solar_par_photon_conversion'])
    def quantities(values, unit=HEAT):
        return {k: {'value': v, 'unit': unit} for k, v in values.items()}
    policy_hash = _hash(POLICY)
    return {'model_version': VERSION, 'code_sha256': CODE_SHA256, 'policy_sha256': policy_hash,
        'profile_sha256': profile.sha256, 'source_sha256': SOURCE_SHA256, 'notice_sha256': NOTICE_SHA256,
        'input_sha256': _hash({'model_version': VERSION, 'profile_sha256': profile.sha256,
                              'policy_sha256': policy_hash, 'scenario': normalized}),
        'scenario': normalized, 'scope': 'software_research_only',
        'claim_scope': 'synthetic_prescribed_solar_par_math_only', 'G0_G4': 'not_assessed',
        'time_coordinate': 'instantaneous_no_state_advance',
        'crop_forcing': quantities({'par_above_canopy': photon_above}, PHOTONS),
        'absorbed_photons': quantities({'par_absorbed_canopy': photon_absorbed}, PHOTONS),
        'heat_components': quantities({'canopy_absorbed_par': canopy, 'floor_absorbed_par': floor}),
        'diagnostics': quantities({'outdoor_PAR': outside, 'above_canopy_PAR': above,
                                  'canopy_direct_absorbed_PAR': down, 'canopy_floor_absorbed_PAR': up}),
        'interior_partition': quantities(interior), 'exterior_PAR_partition': quantities(exterior),
        'partition_residuals': quantities(residuals), 'partition_budgets': quantities(budgets)}
