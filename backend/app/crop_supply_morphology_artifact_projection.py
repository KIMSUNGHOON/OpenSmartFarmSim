"""Project recorded quantities and exact clocks without importing crop equations."""
from copy import deepcopy
from fractions import Fraction
from math import isfinite

from .crop_morphology_artifact_io import _need
from .crop_morphology_artifact_reader import _closed, _id, _utc

MASS = 'mg_CH2O/m2_floor'


def q(value, unit):
    value = Fraction(value)
    return {'numerator': str(value.numerator), 'denominator': str(value.denominator), 'unit': unit}


def x(value, unit=None):
    _closed(value, {'numerator', 'denominator', 'unit'})
    _need(type(value['unit']) is str and 1 <= len(value['unit']) <= 64
          and (unit is None or value['unit'] == unit), 'UNIT_HOLD: original stored exact unit required')
    _need(all(type(value[k]) is str and 1 <= len(value[k]) <= 4096
              for k in ('numerator', 'denominator')), 'QUANTITY_HOLD: bounded exact integer strings required')
    try:
        number = Fraction(int(value['numerator']), int(value['denominator']))
    except (ValueError, ZeroDivisionError):
        _need(False, 'QUANTITY_HOLD: canonical nonzero exact denominator required')
    _need(value == q(number, value['unit']), 'QUANTITY_HOLD: canonical stored exact rational required')
    return number


def nonnegative(value):
    _need(type(value) is float and isfinite(value) and value >= 0.,
          'STATE_HOLD: finite nonnegative original binary64 coordinate required')
    return value


def clock(origin, at, air_integral):
    base = origin['base_temperature']
    _closed(base, {'value', 'unit'})
    _need(base['unit'] == 'degC' and type(base['value']) is float and isfinite(base['value']),
          'UNIT_HOLD: original birth base temperature required')
    duration = x(at, 's') - x(origin['at_elapsed_seconds_exact'], 's')
    air = x(air_integral, 'degC_s') - x(origin['air_temperature_integral_exact'], 'degC_s')
    _need(duration >= 0, 'CLOCK_HOLD: stored state cannot precede its birth')
    age = x(origin['thermal_age_exact'], 'degC_day') + (air - Fraction(base['value']) * duration) / 86400
    _need(age >= 0, 'CLOCK_HOLD: nonnegative original birth-relative clock required')
    return q(age, 'degC_day')


def ledgers(value, expected):
    _closed(value, set(expected))
    for name, row in value.items():
        _closed(row, {'residual_exact', 'budget_exact'})
        unit = expected[name]['residual_exact']['unit']
        residual, budget = x(row['residual_exact'], unit), x(row['budget_exact'], unit)
        _need(budget >= 0 and abs(residual) <= budget, 'QC_HOLD: stored global account exceeds recorded budget')
    return deepcopy(value)


def quantity(value, unit):
    _closed(value, {'value', 'unit'})
    _need(value['unit'] == unit, 'UNIT_HOLD: original stored quantity unit required')
    nonnegative(value['value'])
    return deepcopy(value)


def _geometry(value, unit):
    fields = {'potential_exact', 'realized_exact', 'deficit_exact',
              'lifetime_potential_exact', 'lifetime_realized_exact', 'lifetime_deficit_exact',
              'canonical_gap_exact', 'canonical_potential_difference_exact'}
    _closed(value, fields)
    for field in fields:
        x(value[field], unit)
    for prefix in ('', 'lifetime_'):
        potential = x(value[prefix + 'potential_exact'], unit)
        realized = x(value[prefix + 'realized_exact'], unit)
        _need(potential >= realized >= 0 and x(value[prefix + 'deficit_exact'], unit) == potential - realized,
              'QC_HOLD: exact recorded geometry potential/realized/deficit required')
    return deepcopy(value)


def project(seed, snapshot, lifetime, geometry, global_accounts):
    """Name stored coordinates; compose clocks/QC without a growth/curve evaluation."""
    _closed(snapshot, {'at', 'state', 'derived'})
    at = snapshot['at']
    _closed(at, {'time_origin_utc', 'elapsed_seconds_exact'})
    _utc(at['time_origin_utc'])
    x(at['elapsed_seconds_exact'], 's')
    program, organs = seed['program'], seed['organs']
    n, m, h = len(program['leaves']), len(program['stem_root_compartments']), len(organs['internodes'])
    size = 106 + 3 * n + m
    state = snapshot['state']
    _need(1 <= n <= 512 and 1 <= h <= 512 and 1 <= m <= 512
          and type(state) is list and len(state) == size + 2 * h
          and all(type(v) is float and isfinite(v) for v in state), 'STATE_HOLD: complete original finite vector required')
    layout = seed['state_layout']
    leaf_ids = [row['leaf_id'] for row in program['leaves']]
    stem_ids = [row['compartment_id'] for row in program['stem_root_compartments']]
    node_ids = [row['compartment_id'] for row in organs['internodes']]
    _need(len(set(leaf_ids)) == n and len(set(stem_ids)) == m and len(set(node_ids)) == h
          and layout['original_prefix_length'] == size and layout['internode_ids'] == node_ids
          and layout['original']['leaf_ids'] == leaf_ids
          and [row['leaf_id'] for row in organs['leaves']] == leaf_ids,
          'INVENTORY_HOLD: exact ordered original state layout and organ IDs required')
    _closed(geometry, {*(f'leaf_{i}' for i in range(n)), *(f'internode_{i}' for i in range(h))})
    air = lifetime['indoor_air_temperature_time']
    x(air, 'degC_s')
    leaves, internodes = [], []
    for kind, rows, destination in [('leaf', organs['leaves'], leaves), ('internode', organs['internodes'], internodes)]:
        for i, row in enumerate(rows):
            identifier = 'leaf_id' if kind == 'leaf' else 'compartment_id'
            unit = 'm2' if kind == 'leaf' else 'm'
            _id(row[identifier])
            _need(row.get('parent_internode_id') is None or row['parent_internode_id'] in node_ids,
                  'PARENT_HOLD: declared original stored parent required')
            offset = 106 + n + i if kind == 'leaf' else size + h + i
            carbon_offset = 106 + 2 * n + i if kind == 'leaf' else 106 + 3 * n + stem_ids.index(row[identifier])
            age_offset = 106 + i if kind == 'leaf' else size + i
            origin = seed['geometry_baselines']['leaves' if kind == 'leaf' else 'internodes'][i]
            _need(origin[identifier] == row[identifier], 'ORIGIN_HOLD: ordered original geometry origin required')
            quantity(origin['origin_geometry'], unit)
            values = {'id': row[identifier], 'parent_internode_id': row.get('parent_internode_id'),
                      'geometry': {'value': nonnegative(state[offset]), 'unit': unit},
                      'carbon': {'value': nonnegative(state[carbon_offset]), 'unit': MASS},
                      'represented_age': {'value': nonnegative(state[age_offset]), 'unit': 'degC_day'},
                      'clock_exact': clock(row['baseline'], at['elapsed_seconds_exact'], air),
                      'birth': deepcopy(row['baseline']), 'geometry_origin': deepcopy(origin),
                      'geometry_diagnostics': _geometry(geometry[f'{kind}_{i}'], unit),
                      'metadata': deepcopy(row)}
            destination.append(values)
    quantity(program['model_floor_area'], 'm2_floor')
    _need(program['model_floor_area']['value'] > 0, 'BASIS_HOLD: positive original floor required')
    return {'snapshot': deepcopy(snapshot), 'model_floor_area': deepcopy(program['model_floor_area']),
            'state_layout': deepcopy(layout), 'leaves': leaves, 'internodes': internodes,
            'global_ledgers': ledgers(global_accounts, seed['global_ledgers'])}
