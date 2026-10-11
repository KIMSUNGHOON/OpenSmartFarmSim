"""Prescribed ventilation boundary; crop-greenhouse-ventilation-v1.md defines scope.

Equation attribution: GreenLight Chapter8 at the source hash in the pinned
canopy exchange profile; LICENSES/GreenLight-BSD-3-Clause-Clear.txt.
The vapor mass coordinate and explicit Rv are the project's reduced closure.
"""
from hashlib import sha256
import json
from math import fsum, isfinite
from pathlib import Path

from .crop_canopy_exchange import ReferenceParameters

VERSION = 'prescribed-main-air-ventilation-research-v1'
CODE_SHA256 = sha256(Path(__file__).read_bytes()).hexdigest()
STATE_UNITS = {'air_temperature': 'degC', 'air_vapor_mass': 'kg_water/m2_floor'}
PARAMETER_UNITS = {'air_volume_per_floor_area': 'm3/m2_floor',
    'air_capacity_density': 'kg_air/m3', 'vapor_gas_constant': 'J/kg_water/K'}
FORCING_UNITS = {'outdoor_air_temperature': 'degC', 'outdoor_vapor_pressure': 'Pa',
    'volume_exchange_per_floor_area': 'm3/m2_floor/s'}
POLICY = {'temperature_offset_K': 273.15, 'volume_exchange': 'explicit_nonnegative',
    'vapor_coordinate': 'mass_per_floor_area_explicit_same_Rv',
    'sensible_boundary': 'constant_capacity_density_no_latent_credit',
    'numerics': 'binary64_nonfinite_product_and_quotient_underflow_hold'}


class VentilationHold(ValueError):
    """The explicit instantaneous research boundary is unavailable."""


def _need(condition, reason):
    if not condition:
        raise VentilationHold(reason)


def _hash(value):
    return sha256(json.dumps(value, sort_keys=True, separators=(',', ':'), allow_nan=False).encode()).hexdigest()


def _q(value, unit):
    return {'value': value, 'unit': unit}


def _quantities(block, units):
    _need(type(block) is dict and set(block) == set(units), 'INPUT_HOLD: closed quantity block required')
    result = {}
    for name, unit in units.items():
        row = block[name]
        _need(type(row) is dict and set(row) == {'value', 'unit'}, 'INPUT_HOLD: closed quantity required')
        _need(type(row['unit']) is str and row['unit'] == unit, 'UNIT_HOLD: '+name)
        _need(type(row['value']) in (int, float), 'INPUT_HOLD: explicit numeric value required')
        try:
            value = float(row['value'])
        except OverflowError as exc:
            raise VentilationHold('NUMERIC_HOLD: unrepresentable input') from exc
        _need(isfinite(value), 'INPUT_HOLD: finite quantity required')
        result[name] = value
    return result


def _product(*values):
    if 0 in values:
        return 0.0
    result = 1.0
    for value in values:
        result *= value
        _need(isfinite(result) and result != 0, 'NUMERIC_HOLD: product overflow or underflow')
    return result


def _divide(numerator, denominator):
    value = numerator / denominator
    _need(isfinite(value) and (numerator == 0 or value != 0), 'NUMERIC_HOLD: quotient overflow or underflow')
    return value


def calculate_ventilation(*, scenario, profile):
    """Return signed air forcing contributions, without advancing any state."""
    _need(type(profile) is ReferenceParameters, 'PROFILE_HOLD: pinned canopy exchange profile required')
    _need(type(scenario) is dict and set(scenario) == {'input_id', 'origin', 'state', 'parameters', 'forcing'},
        'INPUT_HOLD: closed scenario required')
    _need(type(scenario['input_id']) is str and 1 <= len(scenario['input_id']) <= 200
        and bool(scenario['input_id'].strip()) and type(scenario['origin']) is str
        and scenario['origin'] in ('synthetic', 'reference_calculation'), 'INPUT_HOLD: explicit research origin required')
    blocks = {name: _quantities(scenario[name], units) for name, units in
        (('state', STATE_UNITS), ('parameters', PARAMETER_UNITS), ('forcing', FORCING_UNITS))}
    s, p, f = (blocks[name] for name in ('state', 'parameters', 'forcing'))
    _need(all(value > 0 for value in p.values()), 'INPUT_HOLD: positive explicit parameters required')
    _need(s['air_vapor_mass'] >= 0 and f['outdoor_vapor_pressure'] >= 0
        and f['volume_exchange_per_floor_area'] >= 0, 'INPUT_HOLD: negative mass, pressure or volume exchange')
    kelvin = [value+273.15 for value in (s['air_temperature'], f['outdoor_air_temperature'])]
    _need(all(isfinite(value) and value > 0 for value in kelvin), 'INPUT_HOLD: positive absolute temperatures required')
    _need(all(k != c for k, c in zip(kelvin, (s['air_temperature'], f['outdoor_air_temperature']))),
        'NUMERIC_HOLD: temperature conversion stagnation')
    indoor = _divide(s['air_vapor_mass'], p['air_volume_per_floor_area'])
    outdoor = _divide(f['outdoor_vapor_pressure'], _product(p['vapor_gas_constant'], kelvin[1]))
    rate = f['volume_exchange_per_floor_area']
    heat = _product(p['air_capacity_density'], profile.values['air_heat_capacity'], rate,
        f['outdoor_air_temperature']-s['air_temperature'])
    vapor = _product(rate, outdoor-indoor)
    latent = _product(profile.values['latent_heat'], vapor)
    try:
        energy = fsum((heat, latent))
    except OverflowError as exc:
        raise VentilationHold('NUMERIC_HOLD: reduced energy overflow') from exc
    _need(isfinite(energy), 'NUMERIC_HOLD: reduced energy overflow')
    normalized = {'input_id': scenario['input_id'], 'origin': scenario['origin'],
        **{name: {key: _q(blocks[name][key], unit) for key, unit in units.items()}
            for name, units in (('state', STATE_UNITS), ('parameters', PARAMETER_UNITS), ('forcing', FORCING_UNITS))}}
    flows = {'sensible_heat': _q(heat, 'W/m2_floor'), 'water_vapor': _q(vapor, 'kg_water/m2_floor/s'),
        'latent_energy': _q(latent, 'W/m2_floor')}
    return {'model_version': VERSION, 'code_sha256': CODE_SHA256, 'profile_sha256': profile.sha256,
        'source_sha256': profile.source_sha256, 'notice_sha256': profile.notice_sha256,
        'policy_sha256': _hash(POLICY), 'input_sha256': _hash(normalized), 'scenario': normalized,
        'derived': {'indoor_vapor_density': _q(indoor, 'kg_water/m3'),
            'outdoor_vapor_density': _q(outdoor, 'kg_water/m3')},
        'forcing_contribution': {'air_external_sensible_heat': flows['sensible_heat'],
            'air_external_vapor': flows['water_vapor']},
        'reduced_energy_to_air': _q(energy, 'W/m2_floor'),
        'local_transfers': {name: {'air': quantity,
            'outdoor': _q(-quantity['value'], quantity['unit'])} for name, quantity in flows.items()},
        'local_transfer_residuals': {name: _q(fsum((q['value'], -q['value'])), q['unit'])
            for name, q in flows.items()},
        'time_coordinate': 'instantaneous_no_state_advance', 'scope': 'software_research_only',
        'claim_scope': 'synthetic_prescribed_ventilation_math_only', 'G0_G4': 'not_assessed'}
