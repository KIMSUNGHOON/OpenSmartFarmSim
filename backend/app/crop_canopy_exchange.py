"""Pinned instantaneous canopy exchange; crop-canopy-exchange-v1.md defines scope.

Equation attribution: fixtures/crop-canopy-exchange-reference-parameters-v1.json
and LICENSES/GreenLight-BSD-3-Clause-Clear.txt.
"""
from dataclasses import dataclass, field
from hashlib import sha256
import json
from math import exp, fsum, isfinite
from pathlib import Path
from types import MappingProxyType
from typing import Mapping

VERSION = 'greenlight-canopy-exchange-research-v1'
CODE_SHA256 = sha256(Path(__file__).read_bytes()).hexdigest()
PROFILE_SHA256 = '1e032ced2ffdaf8ba713184e89b628cce4173c9e7231f30710afeda8fbf20110'
INPUT_UNITS = {
    'leaf_area_index': 'm2_leaf/m2_floor', 'canopy_temperature': 'degC',
    'air_temperature': 'degC', 'air_vapor_pressure': 'Pa',
    'air_capacity_density': 'kg_air/m3', 'canopy_vapor_resistance': 's/m',
}
WATER_UNIT = 'kg_water/m2_floor/s'
HEAT_UNIT = 'W/m2_floor'


class CanopyExchangeHold(ValueError):
    """The explicit research calculation cannot support this input."""


def _need(condition, reason):
    if not condition:
        raise CanopyExchangeHold(reason)


@dataclass(frozen=True)
class ReferenceParameters:
    raw_bytes: bytes
    values: Mapping[str, float] = field(init=False, repr=False)
    sha256: str = field(init=False)
    source_sha256: str = field(init=False)
    notice_sha256: str = field(init=False)
    temperature_bounds: tuple[float, float] = field(init=False)

    def __post_init__(self):
        _need(type(self.raw_bytes) is bytes and sha256(self.raw_bytes).hexdigest() == PROFILE_SHA256,
              'PROFILE_HOLD: pinned reference bytes required')
        document = json.loads(self.raw_bytes)
        object.__setattr__(self, 'values', MappingProxyType({
            k: float(row['value']) for k, row in document['parameters'].items()}))
        for name, value in (('sha256', PROFILE_SHA256),
                ('source_sha256', document['source_sha256']), ('notice_sha256', document['notice_sha256']),
                ('temperature_bounds', tuple(document['domain']['temperature_degC']))):
            object.__setattr__(self, name, value)


def _forcing(block, bounds):
    _need(type(block) is dict and set(block) == {'input_id', 'origin', 'values'},
          'INPUT_HOLD: closed forcing block required')
    _need(type(block['input_id']) is str and 1 <= len(block['input_id']) <= 200
          and bool(block['input_id'].strip()) and type(block['origin']) is str
          and block['origin'] in ('synthetic', 'reference_calculation'),
          'INPUT_HOLD: explicit research origin required')
    values = block['values']
    _need(type(values) is dict and set(values) == set(INPUT_UNITS),
          'INPUT_HOLD: explicit quantities required')
    numbers = {}
    for name, unit in INPUT_UNITS.items():
        row = values[name]
        _need(type(row) is dict and set(row) == {'value', 'unit'}, 'INPUT_HOLD: closed quantity required')
        _need(type(row['unit']) is str and row['unit'] == unit, 'UNIT_HOLD: ' + name)
        _need(type(row['value']) in (int, float), 'INPUT_HOLD: numeric quantity required')
        try:
            value = float(row['value'])
        except OverflowError as exc:
            raise CanopyExchangeHold('NUMERIC_HOLD: unrepresentable input') from exc
        _need(isfinite(value) and value >= 0, 'INPUT_HOLD: finite nonnegative quantity required')
        numbers[name] = value
    lower, upper = bounds
    _need(all(lower <= numbers[k] <= upper for k in ('canopy_temperature', 'air_temperature')),
          'INPUT_HOLD: outside synthetic temperature window')
    _need(numbers['air_capacity_density'] > 0 and numbers['canopy_vapor_resistance'] > 0,
          'INPUT_HOLD: positive explicit density and resistance required')
    normalized = {'input_id': block['input_id'], 'origin': block['origin'],
        'values': {k: {'value': numbers[k], 'unit': INPUT_UNITS[k]} for k in INPUT_UNITS}}
    return numbers, normalized


def _q(value, unit):
    return {'value': value, 'unit': unit}


def calculate_exchange(*, forcing, profile):
    """Compute signed E/H/LE and their local transfer ledger without state advancement."""
    _need(type(profile) is ReferenceParameters, 'PROFILE_HOLD: reference parameters required')
    f, normalized = _forcing(forcing, profile.temperature_bounds)
    p = profile.values
    try:
        saturation = p['saturation_pressure_coefficient'] * exp(
            p['saturation_exponent_factor'] * f['canopy_temperature'] /
            (f['canopy_temperature'] + p['saturation_denominator_offset']))
        difference = saturation - f['air_vapor_pressure']
        if f['leaf_area_index'] == 0:
            coefficient = vapor = sensible = latent = 0.0
        else:
            numerator = p['leaf_surface_factor'] * f['air_capacity_density'] * p['air_heat_capacity'] * f['leaf_area_index']
            denominator = p['latent_heat'] * p['psychrometric_constant'] * (
                p['boundary_resistance'] + f['canopy_vapor_resistance'])
            _need(isfinite(numerator) and isfinite(denominator) and numerator > 0 and denominator > 0,
                  'NUMERIC_HOLD: vapor coefficient intermediate overflow or underflow')
            coefficient = numerator / denominator
            _need(isfinite(coefficient) and coefficient > 0, 'NUMERIC_HOLD: vapor coefficient underflow')
            vapor = coefficient * difference
            sensible = p['leaf_surface_factor'] * p['leaf_air_heat_transfer'] * f['leaf_area_index'] * (
                f['canopy_temperature'] - f['air_temperature'])
            latent = p['latent_heat'] * vapor
            _need(difference == 0 or vapor != 0, 'NUMERIC_HOLD: vapor flux underflow')
            _need(f['canopy_temperature'] == f['air_temperature'] or sensible != 0,
                  'NUMERIC_HOLD: sensible heat underflow')
        total = fsum((sensible, latent))
    except (OverflowError, ZeroDivisionError, ValueError) as exc:
        if isinstance(exc, CanopyExchangeHold):
            raise
        raise CanopyExchangeHold('NUMERIC_HOLD: equation evaluation failed') from exc
    _need(all(map(isfinite, (saturation, difference, coefficient, vapor, sensible, latent, total))),
          'NUMERIC_HOLD: nonfinite exchange')
    pairs = {'water': {'canopy': _q(-vapor, WATER_UNIT), 'air_vapor': _q(vapor, WATER_UNIT)},
        'sensible': {'canopy': _q(-sensible, HEAT_UNIT), 'air_sensible': _q(sensible, HEAT_UNIT)},
        'latent': {'canopy': _q(-latent, HEAT_UNIT), 'air_vapor_energy': _q(latent, HEAT_UNIT)}}
    raw = json.dumps(normalized, sort_keys=True, separators=(',', ':'), allow_nan=False).encode()
    return {'model_version': VERSION, 'code_sha256': CODE_SHA256, 'profile_sha256': profile.sha256,
        'source_sha256': profile.source_sha256, 'notice_sha256': profile.notice_sha256,
        'input_sha256': sha256(raw).hexdigest(), 'forcing': normalized,
        'scope': 'software_research_only', 'claim_scope': 'synthetic_exchange_math_only', 'G0_G4': 'not_assessed',
        'diagnostics': {'canopy_saturation_pressure': _q(saturation, 'Pa'),
            'canopy_minus_air_vapor_pressure': _q(difference, 'Pa'),
            'vapor_transfer_coefficient': _q(coefficient, 'kg_water/m2_floor/Pa/s')},
        'exchange': {'water_vapor': _q(vapor, WATER_UNIT), 'sensible_heat': _q(sensible, HEAT_UNIT),
            'latent_heat': _q(latent, HEAT_UNIT), 'canopy_total_heat_outflow': _q(total, HEAT_UNIT)},
        'local_transfers': pairs,
        'local_transfer_residuals': {key: _q(fsum(row['value'] for row in pair.values()),
            WATER_UNIT if key == 'water' else HEAT_UNIT) for key, pair in pairs.items()}}
