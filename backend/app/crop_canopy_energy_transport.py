"""Represented leaf-capacity inventory; crop-canopy-energy-transport-v1.md.

SLA attribution: crop-growth-reference-parameters-v1.json and the retained
GreenLight BSD notice. Capacity transport is an explicit project closure.
"""
from hashlib import sha256
import json
from math import fsum, isfinite
from pathlib import Path

from .crop_growth_rates import ReferenceParameters

VERSION = 'canopy-capacity-inventory-research-v1'
CODE_SHA256 = sha256(Path(__file__).read_bytes()).hexdigest()
MASS = 'mg_CH2O/m2_floor'
CAPACITY = 'J/m2_floor/K'
CAPACITY_RATE = CAPACITY + '/s'
ENERGY = 'J/m2_floor'
POWER = 'W/m2_floor'
TEMPERATURE_TOLERANCE = 2e-13
BALANCE_RELATIVE_TOLERANCE = 3e-13
TRANSPORT_UNITS = {'leaf_carbohydrate': MASS, 'leaf_allocation': MASS+'/s',
    'leaf_maintenance': MASS+'/s', 'leaf_removal': MASS+'/s',
    'leaf_heat_capacity': 'J/m2_leaf/K', 'canopy_temperature': 'degC',
    'incoming_capacity_temperature': 'degC', 'reference_temperature': 'degC'}
EVENT_UNITS = {'leaf_carbohydrate': MASS, 'leaf_removed': MASS,
    'leaf_heat_capacity': 'J/m2_leaf/K', 'canopy_sensible_energy': ENERGY,
    'reference_temperature': 'degC'}


class CanopyEnergyHold(ValueError):
    """Unsupported input, inventory boundary, or representability."""


def _need(condition, reason):
    if not condition:
        raise CanopyEnergyHold(reason)


def _q(value, unit):
    return {'value': value, 'unit': unit}


def _finite(value):
    _need(isfinite(value), 'NUMERIC_HOLD: nonfinite arithmetic')
    return value


def _sum(*values):
    try:
        return _finite(fsum(values))
    except (OverflowError, ValueError) as exc:
        if isinstance(exc, CanopyEnergyHold):
            raise
        raise CanopyEnergyHold('NUMERIC_HOLD: sum overflow') from exc


def _multiply(a, b):
    value = _finite(a*b)
    _need(a == 0 or b == 0 or value != 0, 'NUMERIC_HOLD: product underflow')
    return value


def _divide(a, b):
    value = _finite(a/b)
    _need(a == 0 or value != 0, 'NUMERIC_HOLD: quotient underflow')
    return value


def _hash(value):
    return sha256(json.dumps(value, sort_keys=True, separators=(',', ':'), allow_nan=False).encode()).hexdigest()


def _prepare(block, units, profile):
    _need(type(profile) is ReferenceParameters, 'PROFILE_HOLD: pinned growth profile required')
    _need(type(block) is dict and set(block) == {'input_id', 'origin', 'values'},
          'INPUT_HOLD: closed research block required')
    _need(type(block['input_id']) is str and 1 <= len(block['input_id']) <= 200
          and bool(block['input_id'].strip()) and type(block['origin']) is str
          and block['origin'] in ('synthetic', 'reference_calculation'),
          'INPUT_HOLD: explicit research origin required')
    records = block['values']
    _need(type(records) is dict and set(records) == set(units), 'INPUT_HOLD: closed quantities required')
    values = {}
    for name, unit in units.items():
        row = records[name]
        _need(type(row) is dict and set(row) == {'value', 'unit'}, 'INPUT_HOLD: closed quantity required')
        _need(type(row['unit']) is str and row['unit'] == unit, 'UNIT_HOLD: '+name)
        _need(type(row['value']) in (int, float), 'INPUT_HOLD: numeric value required')
        try:
            value = float(row['value'])
        except OverflowError as exc:
            raise CanopyEnergyHold('NUMERIC_HOLD: unrepresentable input') from exc
        _need(isfinite(value), 'INPUT_HOLD: finite value required')
        values[name] = value
    _need(values['leaf_carbohydrate'] >= 0, 'INPUT_HOLD: negative leaf inventory')
    _need(values['leaf_carbohydrate'] > 0, 'EMPTY_CANOPY_HOLD: no empty-canopy transition')
    _need(values['leaf_heat_capacity'] > 0, 'INPUT_HOLD: positive explicit capacity required')
    normalized = {'input_id': block['input_id'], 'origin': block['origin'],
        'values': {name: _q(values[name], unit) for name, unit in units.items()}}
    return values, normalized


def _geometry(leaf, cap_leaf, profile):
    lai = _multiply(profile.values['sla'], leaf)
    capacity = _multiply(cap_leaf, lai)
    return lai, capacity


def _temperature(value):
    _need(10 <= value <= 34, 'TEMPERATURE_HOLD: outside 10..34 synthetic window')
    return value


def _offset(temperature, reference):
    offset = _sum(temperature, -reference)
    _need(abs(_sum(reference, offset, -temperature)) <= TEMPERATURE_TOLERANCE,
          'NUMERIC_HOLD: reference temperature resolution')
    return offset


def _balance(residual, terms):
    scale = _sum(*(abs(value) for value in terms))
    _need(abs(residual) <= BALANCE_RELATIVE_TOLERANCE*scale,
          'NUMERIC_HOLD: capacity energy ledger mismatch')


def _identity(normalized, profile, operation):
    identity = {'model_version': VERSION, 'code_sha256': CODE_SHA256,
        'profile_sha256': profile.sha256, 'input_sha256': _hash(normalized), 'operation': operation}
    return {**identity, 'calculation_sha256': _hash(identity), 'input': normalized,
        'scope': 'software_research_only', 'claim_scope': 'synthetic_canopy_capacity_inventory_only',
        'G0_G4': 'not_assessed'}


def calculate_transport(*, forcing, profile):
    """Account for gross represented capacity flows, without advancing a state."""
    v, normalized = _prepare(forcing, TRANSPORT_UNITS, profile)
    names = ('leaf_allocation', 'leaf_maintenance', 'leaf_removal')
    _need(all(v[name] >= 0 for name in names), 'INPUT_HOLD: negative gross leaf rate')
    tc = _temperature(v['canopy_temperature'])
    tin = _temperature(v['incoming_capacity_temperature'])
    ref = v['reference_temperature']
    out_offset, in_offset = _offset(tc, ref), _offset(tin, ref)
    lai, capacity = _geometry(v['leaf_carbohydrate'], v['leaf_heat_capacity'], profile)
    gross = tuple(_multiply(v['leaf_heat_capacity'], _multiply(profile.values['sla'], v[name])) for name in names)
    g, dm, dr = gross
    capacity_rate = _sum(g, -dm, -dr)
    leaf_rate = _sum(v[names[0]], -v[names[1]], -v[names[2]])
    qin, qm, qr = (_multiply(rate, offset) for rate, offset in
        ((g, in_offset), (dm, out_offset), (dr, out_offset)))
    material = _sum(qin, -qm, -qr)
    temperature_rate = _divide(_multiply(g, _sum(tin, -tc)), capacity)
    temperature_part = _multiply(capacity, temperature_rate)
    capacity_part = _multiply(out_offset, capacity_rate)
    chain_rule_rate = _sum(temperature_part, capacity_part)
    residual = _sum(temperature_part, capacity_part, -qin, qm, qr)
    _balance(residual, (temperature_part, capacity_part, qin, qm, qr))
    return {**_identity(normalized, profile, 'continuous_transport'),
        'leaf_area_index': _q(lai, 'm2_leaf/m2_floor'), 'canopy_capacity': _q(capacity, CAPACITY),
        'canopy_sensible_energy': _q(_multiply(capacity, out_offset), ENERGY),
        'leaf_net_rate': _q(leaf_rate, MASS+'/s'),
        'capacity_rates': {name: _q(value, CAPACITY_RATE) for name, value in
            zip(('allocation', 'maintenance', 'removal', 'net'), (*gross, capacity_rate))},
        'energy_flows': {name: _q(value, POWER) for name, value in
            zip(('incoming', 'maintenance_outgoing', 'removal_outgoing', 'net'), (qin, qm, qr, material))},
        'material_temperature_rate': _q(temperature_rate, 'K/s'),
        'storage_rate_from_chain_rule': _q(chain_rule_rate, POWER),
        'balance_residuals': {'material_energy': _q(residual, POWER)}}


def calculate_leaf_removal(*, event, profile):
    """Remove represented capacity at its current temperature, preserving signs."""
    v, normalized = _prepare(event, EVENT_UNITS, profile)
    leaf, removed = v['leaf_carbohydrate'], v['leaf_removed']
    _need(0 <= removed <= leaf, 'EVENT_HOLD: negative or excessive leaf removal')
    _need(removed < leaf, 'EMPTY_CANOPY_HOLD: full removal requires a new transition contract')
    after = _sum(leaf, -removed)
    _need(removed == 0 or after < leaf, 'NUMERIC_HOLD: leaf removal lost to rounding')
    lai_before, c_before = _geometry(leaf, v['leaf_heat_capacity'], profile)
    lai_after, c_after = _geometry(after, v['leaf_heat_capacity'], profile)
    _need(removed == 0 or c_after < c_before, 'NUMERIC_HOLD: capacity removal lost to rounding')
    u_before, ref = v['canopy_sensible_energy'], v['reference_temperature']
    offset_before = _divide(u_before, c_before)
    tc_before = _temperature(_sum(ref, offset_before))
    _need(abs(_sum(_offset(tc_before, ref), -offset_before)) <= TEMPERATURE_TOLERANCE,
          'NUMERIC_HOLD: stored temperature resolution')
    u_after = _multiply(u_before, _divide(c_after, c_before))
    _need(removed == 0 or u_before == 0 or u_after != u_before,
          'NUMERIC_HOLD: energy removal lost to rounding')
    outgoing = _sum(u_before, -u_after)
    tc_after = _temperature(_sum(ref, _divide(u_after, c_after)))
    temperature_residual = _sum(tc_after, -tc_before)
    _need(abs(temperature_residual) <= TEMPERATURE_TOLERANCE,
          'NUMERIC_HOLD: event temperature mismatch')
    expected_outgoing = _multiply(_sum(c_before, -c_after), offset_before)
    energy_residual = _sum(outgoing, -expected_outgoing)
    _balance(energy_residual, (u_before, u_after, outgoing, expected_outgoing))
    return {**_identity(normalized, profile, 'leaf_removal'),
        'before': {'leaf_carbohydrate': _q(leaf, MASS), 'leaf_area_index': _q(lai_before, 'm2_leaf/m2_floor'),
            'canopy_capacity': _q(c_before, CAPACITY), 'canopy_sensible_energy': _q(u_before, ENERGY),
            'canopy_temperature': _q(tc_before, 'degC')},
        'after': {'leaf_carbohydrate': _q(after, MASS), 'leaf_area_index': _q(lai_after, 'm2_leaf/m2_floor'),
            'canopy_capacity': _q(c_after, CAPACITY), 'canopy_sensible_energy': _q(u_after, ENERGY),
            'canopy_temperature': _q(tc_after, 'degC')},
        'outgoing_sensible_energy': _q(outgoing, ENERGY),
        'balance_residuals': {'event_capacity_energy': _q(energy_residual, ENERGY),
            'temperature': _q(temperature_residual, 'K')}}
